import copy
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import r_ai2_capacity as c


def capture(results=False):
    entries = []
    def put(path, value, kind=None):
        entries.append({"path": path, "value": value, "type": kind or ("Bool" if type(value) is bool else "Int" if type(value) is int else "Float" if type(value) is float else "String")})
    for path, value in {"Race/NumCars": 5, "Race/NumPlayers": 1, "Race/NumNetworkPlayers": 0,
                        "Race/Type": 2, "Race/FinishingType": 0, "Race/AttractMode": False,
                        "Race/NetworkSyncActive": False, "Race/GhostPlayback": False,
                        "Frontend/QuickRace/Track": 10, "Frontend/QuickRace/Ghost": 0}.items():
        put(path, value)
    vehicles = c.stock_map()
    for n in range(5):
        for key, value in {"CarID": n, "CarClass": 0, "PlayerType": 1 if n == 0 else 2,
                           "DriverID": 30 if n == 0 else n - 1,
                           "CarType": vehicles[n]["family"], "WheelType": vehicles[n]["family"]}.items():
            put(f"Race/Car{n}/{key}", value)
    canaries = json.loads((c.REPOSITORY / "research/r-ai1-1/vehicle-physics-canaries.json").read_text())
    for suffix, value in canaries["vehicles"][4]["values"].items(): put("Vehicles/Car4/" + suffix, value)
    if results:
        for suffix, values in {"PositionList": [f'"{n}"' for n in range(1, 6)],
                               "NameList": [f'"driver{n}"' for n in range(5)],
                               "TimeList": ['"00:01:00"'] * 5}.items():
            put("Frontend/RaceResults/" + suffix, values, "StringList")
        for n, image in enumerate((9, 17, 22, 15, 1, 12, 12, 12)): put(f"Frontend/RaceResults/Car{n}", image)
    return {"kind": "master-rallye-broker-dump-snapshot", "schema_version": 1, "entries": entries,
            "source": {"image_sha256": c.CANDIDATE_SHA256, "build_profile": c.PROFILE,
                       "broker_dump_variant": "native_hardened", "label": "five-results" if results else "five-race",
                       "freshness": "post_baseline_complete_dump_proven"}}


def change(snapshot, path, value):
    next(row for row in snapshot["entries"] if row["path"] == path)["value"] = value


class CapacityTests(unittest.TestCase):
    def test_exact_five_policy_and_each_guard(self):
        state = dict(opponents=3, mode=2, split=False, ghost=0, player=0, track=10)
        self.assertEqual(c.effective_opponents(**state) + 1, 5)
        for key, value in (("opponents", 0), ("opponents", 1), ("opponents", 2), ("opponents", 4),
                           ("mode", 1), ("mode", 3), ("split", True), ("ghost", 1), ("player", 1),
                           ("player", 7), ("track", 9)):
            row = {**state, key: value}
            self.assertEqual(c.effective_opponents(**row), row["opponents"])
        with self.assertRaises(ValueError): c.effective_opponents(True, 2, False, 0, 0, 10)

    def test_t1_pool_has_four_distinct_stock_choices(self):
        pool = [row for row in c.stock_map() if row["id"] in range(1, 7)]
        self.assertEqual(len(pool), 6)
        self.assertTrue(all(row["class"] == 0 and row["family"] for row in pool))
        self.assertEqual(c.stock_map()[0]["family"], "Landcruiser")

    def test_unknown_hash_size_and_candidate_rejected(self):
        for source in (b"", bytes(c.RETAIL_SIZE), bytes(c.RETAIL_SIZE - 1)):
            with self.assertRaises(ValueError): c.build(source)
            with self.assertRaises(ValueError): c.verify(source)

    def test_original_bytes_fail_closed(self):
        for row in c.ranges():
            source = bytearray(row["offset"] + len(row["original"]))
            source[row["offset"]:] = row["original"]
            source[row["offset"]] ^= 1
            with self.assertRaisesRegex(ValueError, "original bytes"):
                c.apply_ranges(bytes(source), [row], c.sha256(source))

    def test_determinism_inverse_and_range_confinement(self):
        rows = c.ranges(); source = bytearray(c.RETAIL_SIZE)
        for row in rows: source[row["offset"]:row["offset"] + len(row["original"])] = row["original"]
        source = bytes(source); patched = c.apply_ranges(source, rows, c.sha256(source))
        self.assertEqual(patched, c.apply_ranges(source, c.ranges(), c.sha256(source)))
        inverse = [{**row, "original": row["replacement"], "replacement": row["original"]} for row in rows]
        self.assertEqual(c.apply_ranges(patched, inverse, c.sha256(patched)), source)
        allowed = {n for row in rows for n in range(row["offset"], row["offset"] + len(row["original"]))}
        self.assertTrue(all(n in allowed for n, (a, b) in enumerate(zip(source, patched)) if a != b))

    def test_no_loop_or_registry_patch_and_no_range_overlap(self):
        rows = c.ranges()
        self.assertEqual(len(rows), 9)
        self.assertEqual([r["va"] for r in c.capacity_ranges()[1:]], [*c.SITES, c.CAVE])
        self.assertTrue(all(a["offset"] + len(a["original"]) <= b["offset"] for a, b in zip(rows, rows[1:])))
        size = struct.unpack("<I", rows[0]["replacement"])[0]
        self.assertEqual((size + 4095) // 4096, (c.ORIGINAL_TEXT_SIZE + 4095) // 4096)

    def test_shim_original_getter_and_all_rejection_joins(self):
        code = c.shim()
        self.assertEqual(c.CAVE + 5 + struct.unpack("<i", code[1:5])[0], 0x4AE150)
        self.assertEqual(code[-3:], bytes.fromhex("619dc3"))
        targets = [i + 6 + struct.unpack("<i", code[i + 2:i + 6])[0]
                   for i in range(len(code) - 5) if code[i:i + 2] == b"\x0f\x85"]
        self.assertEqual(targets, [len(code) - 3] * 6)

    def test_manifest_exact_scope_and_hashes(self):
        report = c.manifest(c.CANDIDATE_SHA256)
        self.assertEqual(report["active_indices"], [0, 1, 2, 3, 4])
        self.assertFalse(report["mixed_class_chooser"])
        self.assertFalse(report["arrays_relocated"])
        self.assertEqual(len(report["ranges"]), 9)
        self.assertEqual(len(report["output_sha256"]), 64)
        self.assertEqual(report["status"], "PREPARED_RUNTIME_UNTESTED")

    def test_five_race_oracle_is_broker_only(self):
        report = c.check_snapshot(capture())
        self.assertEqual(len(report["participants"]), 5)
        self.assertEqual(report["participants"][4]["CarID"], 4)
        self.assertFalse(report["runtime_full_pass"])
        self.assertEqual(report["status"], "BROKER_STATE_MATCH_ONLY")

    def test_alias_wrong_count_or_slot_rejected(self):
        for path, value in (("Race/NumCars", 4), ("Race/NumCars", True), ("Race/NumPlayers", 2),
                            ("Race/Car4/CarID", 0), ("Race/Car4/CarID", 3), ("Race/Car4/CarClass", 2),
                            ("Race/Car4/PlayerType", 1), ("Race/Car4/DriverID", 0)):
            d = capture(); change(d, path, value)
            with self.assertRaises(ValueError): c.check_snapshot(d)

    def test_capture_provenance_and_duplicate_path_rejected(self):
        for key, value in (("image_sha256", "0" * 64), ("build_profile", "unknown"),
                           ("broker_dump_variant", "native"), ("freshness", "recovered"), ("label", "five-front")):
            d = capture(); d["source"][key] = value
            with self.assertRaises(ValueError): c.check_snapshot(d)
        d = capture(); d["entries"].append(copy.deepcopy(d["entries"][0]))
        with self.assertRaises(ValueError): c.check_snapshot(d)

    def test_car4_physics_and_family_follow_own_id(self):
        for path, value in (("Vehicles/Car4/Dimensions/WheelBase", 0.0), ("Race/Car4/CarType", "Landcruiser"),
                            ("Race/Car4/WheelType", "Pajero")):
            d = capture(); change(d, path, value)
            with self.assertRaises(ValueError): c.check_snapshot(d)

    def test_five_result_lists_icons_and_blank_tail(self):
        report = c.check_snapshot(capture(True), results=True)
        self.assertEqual(len(report["result_lists"]["TimeList"]), 5)
        self.assertFalse(report["runtime_full_pass"])
        for path, value in (("Frontend/RaceResults/NameList", ["x"] * 4),
                            ("Frontend/RaceResults/PositionList", ["1"] * 5),
                            ("Frontend/RaceResults/PositionList", [str(n) for n in range(1, 6)]),
                            ("Frontend/RaceResults/Car4", 12), ("Frontend/RaceResults/Car5", 9)):
            d = capture(True); change(d, path, value)
            with self.assertRaises(ValueError): c.check_snapshot(d, results=True)

    def test_capacity_matrix_keeps_storage_and_runtime_separate(self):
        data = json.loads((c.REPOSITORY / "research/r-ai2/capacity-map.json").read_text())
        self.assertEqual(len(data["subsystems"]), 13)
        self.assertFalse(data["five_car_runtime_confirmed"])
        for row in data["subsystems"]:
            self.assertIn("storage", row); self.assertIn("active_bound", row); self.assertTrue(row["evidence"])
        self.assertEqual(data["proof_target"], 5)


if __name__ == "__main__": unittest.main()
