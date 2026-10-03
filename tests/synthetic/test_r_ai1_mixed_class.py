import copy
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import r_ai1_mixed_class as ai


def stock_participants():
    return [{"CarID": 14 + n, "CarClass": 2, "PlayerType": 1 if n == 0 else 2,
             "DriverID": 30 if n == 0 else n + 1, "sentinel": f"untouched-{n}"}
            for n in range(4)]


def synthetic_capture():
    participants = ai.mixed_plan(stock_participants(), 4)
    families = ai.stock_map()
    entries = [{"path": path, "value": value} for path, value in
               {"Race/NumCars": 4, "Race/NumPlayers": 1, "Race/Type": 2,
                "Race/Networked": False, "Frontend/Active": True,
                "Frontend/QuickRace/Track": 10}.items()]
    for n, participant in enumerate(participants):
        for key in ("CarID", "CarClass", "DriverID", "PlayerType"):
            entries.append({"path": f"Race/Car{n}/{key}", "value": participant[key]})
        for key in ("CarType", "WheelType"):
            entries.append({"path": f"Race/Car{n}/{key}", "value": families[participant["CarID"]]["family"]})
    for suffix, value in {"Dimensions/WheelBase": 2.45, "Dimensions/TrackWidthFront": 1.5,
                          "Engine/GearRatioDiff": 3.95}.items():
        entries.append({"path": "Vehicles/Car1/" + suffix, "value": value})
    return {"kind": "master-rallye-broker-dump-snapshot", "schema_version": 1,
            "source": {"image_sha256": ai.CANDIDATE_SHA256, "label": "mixed-race",
                       "freshness": "post_baseline_complete_dump_proven"}, "entries": entries}


class MixedClassTests(unittest.TestCase):
    def test_all_stock_class_local_roundtrips(self):
        for vehicle_id in range(25):
            cls, local = ai.stock_class_local(vehicle_id)
            self.assertEqual(ai.stock_absolute(cls, local), vehicle_id)
        rows = ai.stock_map()
        self.assertEqual([sum(row["class"] == cls for row in rows) for cls in range(3)], [7, 7, 11])
        self.assertEqual((rows[0]["family"], rows[14]["family"]), ("Landcruiser", "Wildcat"))

    def test_stock_bounds_exclude_uninitialized_and_expansion_ids(self):
        for value in (-1, 25, 26, True, 1.5):
            with self.assertRaises(ValueError):
                ai.stock_class_local(value)
        for cls, local in ((0, 7), (1, 7), (2, 11), (3, 0), (2, -1), (False, 0)):
            with self.assertRaises(ValueError):
                ai.stock_absolute(cls, local)

    def test_exactly_one_ai_changes_player_controls_driver_untouched(self):
        source = stock_participants()
        saved = copy.deepcopy(source)
        result = ai.mixed_plan(source, 4)
        self.assertEqual(source, saved)
        self.assertEqual(len(result), 4)
        for n in (0, 2, 3):
            self.assertEqual(result[n], source[n])
        self.assertEqual(result[1], {**source[1], "CarID": 0, "CarClass": 0})
        self.assertEqual(sum(row["CarClass"] != result[0]["CarClass"] for row in result), 1)

    def test_plan_rejects_capacity_or_player_changes(self):
        for count in (3, 5, True):
            with self.assertRaises(ValueError):
                ai.mixed_plan(stock_participants(), count)
        for key, value in (("CarID", 16), ("PlayerType", 2), ("CarClass", 0)):
            rows = stock_participants()
            rows[0][key] = value
            with self.assertRaises(ValueError):
                ai.mixed_plan(rows, 4)

    def test_plan_rejects_invalid_ai_or_aliased_ids(self):
        for key, value in (("DriverID", 10), ("PlayerType", 1), ("CarID", 16), ("CarClass", 0)):
            rows = stock_participants()
            rows[1][key] = value
            with self.assertRaises(ValueError):
                ai.mixed_plan(rows, 4)

    def test_hash_and_original_byte_gates_independently(self):
        ranges = [{"offset": 1, "original": b"bc", "replacement": b"XY"}]
        with self.assertRaisesRegex(ValueError, "SHA256"):
            ai.apply_ranges(b"abcd", ranges, "0" * 64)
        with self.assertRaisesRegex(ValueError, "original bytes"):
            ai.apply_ranges(b"aZcd", ranges, ai.sha256(b"aZcd"))
        with self.assertRaisesRegex(ValueError, "pristine retail"):
            ai.build_candidate(b"abcd")

    def test_range_overlap_size_and_bounds_fail_closed(self):
        invalid = [
            [{"offset": 1, "original": b"bc", "replacement": b"X"}],
            [{"offset": 4, "original": b"e", "replacement": b"X"}],
            [{"offset": -1, "original": b"", "replacement": b""}],
            [{"offset": 1, "original": b"bc", "replacement": b"XY"},
             {"offset": 2, "original": b"c", "replacement": b"Z"}],
        ]
        for ranges in invalid:
            with self.assertRaises(ValueError):
                ai.apply_ranges(b"abcd", ranges, ai.sha256(b"abcd"))

    def test_deterministic_patch_and_manifest_on_synthetic_bytes(self):
        source = bytearray(ai.SELECTOR - 0x400000 + len(ai.selector_code()))
        for patch in ai.patch_ranges():
            start = patch["offset"]
            source[start:start + len(patch["original"])] = patch["original"]
        source = bytes(source)
        a = ai.apply_ranges(source, ai.patch_ranges(), ai.sha256(source))
        b = ai.apply_ranges(source, ai.patch_ranges(), ai.sha256(source))
        self.assertEqual(a, b)
        manifest = ai.patch_manifest(ai.sha256(a))
        self.assertEqual(json.loads(json.dumps(manifest)), manifest)
        self.assertFalse(manifest["num_cars_changed"])
        self.assertFalse(manifest["driver_id_changed"])
        allowed = set()
        for patch in ai.patch_ranges():
            allowed.update(range(patch["offset"], patch["offset"] + len(patch["original"])))
        self.assertTrue(all(index in allowed for index, (old, new) in enumerate(zip(source, a)) if old != new))
        self.assertEqual(len(a), len(source))

    def test_candidate_verify_rejects_size_and_unknown_images(self):
        for data in (b"", bytes(ai.RETAIL_SIZE)):
            with self.assertRaises(ValueError):
                ai.verify_candidate(data)

    def test_no_header_image_growth(self):
        patch = ai.patch_ranges()[0]
        size = struct.unpack("<I", patch["replacement"])[0]
        self.assertEqual((size + 4095) // 4096, (ai.ORIGINAL_TEXT_SIZE + 4095) // 4096)
        self.assertLess(size, 0x28E000)

    def test_oracle_state_is_not_a_runtime_full_pass(self):
        result = ai.check_snapshot(synthetic_capture(), ai.CANDIDATE_SHA256)
        self.assertEqual(result["status"], "BROKER_STATE_MATCH_ONLY")
        self.assertFalse(result["runtime_full_pass"])
        self.assertEqual(len(result["participants"]), 4)

    def test_oracle_rejects_stale_frontend_recovery_or_unknown_build(self):
        for key, value in (("label", "mixed-front"), ("freshness", "NOT command-proven"),
                           ("image_sha256", ai.RETAIL_SHA256)):
            snapshot = synthetic_capture()
            snapshot["source"][key] = value
            with self.assertRaises(ValueError):
                ai.check_snapshot(snapshot, ai.CANDIDATE_SHA256)

    def test_oracle_rejects_count_identity_physics_and_controller_errors(self):
        for path, value in (("Race/NumCars", 5), ("Race/Car1/CarID", 15),
                            ("Race/Car1/CarClass", 2), ("Race/Car1/DriverID", 10),
                            ("Race/Car1/PlayerType", 1), ("Race/Car1/WheelType", "Wildcat"),
                            ("Race/Car0/PlayerType", True),
                            ("Race/Car0/DriverID", 0), ("Race/Car3/DriverID", 2),
                            ("Vehicles/Car1/Dimensions/WheelBase", 2.77),
                            ("Frontend/QuickRace/Track", 8),
                            ("Frontend/Active", False)):
            snapshot = synthetic_capture()
            next(row for row in snapshot["entries"] if row["path"] == path)["value"] = value
            with self.assertRaises(ValueError):
                ai.check_snapshot(snapshot, ai.CANDIDATE_SHA256)

    def test_oracle_rejects_missing_ambiguous_or_aliased_controls(self):
        snapshot = synthetic_capture()
        snapshot["entries"].append(dict(snapshot["entries"][0]))
        with self.assertRaises(ValueError):
            ai.check_snapshot(snapshot, ai.CANDIDATE_SHA256)
        snapshot = synthetic_capture()
        snapshot["entries"] = [row for row in snapshot["entries"] if row["path"] != "Race/Car2/DriverID"]
        with self.assertRaises(ValueError):
            ai.check_snapshot(snapshot, ai.CANDIDATE_SHA256)
        snapshot = synthetic_capture()
        for row in snapshot["entries"]:
            if row["path"] == "Race/Car3/CarID":
                row["value"] = 16
            elif row["path"] in ("Race/Car3/CarType", "Race/Car3/WheelType"):
                row["value"] = "Astero"
        with self.assertRaises(ValueError):
            ai.check_snapshot(snapshot, ai.CANDIDATE_SHA256)

    def test_raw_dump_binding_rejects_json_edits_and_block_selection(self):
        raw = b"synthetic complete dump"
        parsed = {"source": {"selected_block_offset": 0, "selected_block_length": len(raw),
                             "selected_block_sha256": ai.sha256(raw)},
                  "entries": [{"path": "Race/NumCars", "value": 4}], "dump": {"count": 1}}
        snapshot = copy.deepcopy(parsed)
        snapshot["source"]["raw_sha256"] = ai.sha256(raw)
        ai.verify_capture(snapshot, raw, lambda data: parsed)
        for section, key, value in (("source", "selected_block_offset", 1),
                                    ("source", "raw_sha256", "0" * 64),
                                    ("dump", "count", 2)):
            edited = copy.deepcopy(snapshot)
            edited[section][key] = value
            with self.assertRaises(ValueError):
                ai.verify_capture(edited, raw, lambda data: parsed)
        snapshot["entries"][0]["value"] = 5
        with self.assertRaises(ValueError):
            ai.verify_capture(snapshot, raw, lambda data: parsed)


if __name__ == "__main__":
    unittest.main()
