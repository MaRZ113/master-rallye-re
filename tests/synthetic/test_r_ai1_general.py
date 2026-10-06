import copy
import itertools
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import r_ai1_mixed_class as ai
import r_ai1_observe as observe


def capture(plan=(2, 1, 0), label="mixed-random-race-1"):
    ids = [0, *({0: 1, 1: 7, 2: 14}[cls] for cls in plan)]
    for n in range(1, 4):
        while ids[n] in ids[:n]:
            ids[n] += 1
    values = {"Race/NumCars": 4, "Race/NumPlayers": 1, "Race/Type": 2,
              "Race/NumNetworkPlayers": 0, "Race/NetworkSyncActive": False,
              "Race/AttractMode": False, "Frontend/Active": True,
              "Frontend/QuickRace/Car0": 0, "Frontend/QuickRace/Mode": 2,
              "Frontend/QuickRace/NumOpponents": 3, "Frontend/QuickRace/Ghost": 0,
              "Frontend/QuickRace/Track": 10}
    table = json.loads((ai.REPOSITORY / "research/r-ai1-1/vehicle-physics-canaries.json").read_text())
    families = ai.stock_map()
    for n, vehicle_id in enumerate(ids):
        for key, value in {"CarID": vehicle_id, "CarClass": ai.stock_class_local(vehicle_id)[0],
                           "DriverID": 30 if n == 0 else n, "PlayerType": 1 if n == 0 else 2,
                           "CarType": families[vehicle_id]["family"],
                           "WheelType": families[vehicle_id]["family"]}.items():
            values[f"Race/Car{n}/{key}"] = value
        for key, value in table["vehicles"][vehicle_id]["values"].items():
            values[f"Vehicles/Car{n}/{key}"] = value
    return {"kind": "master-rallye-broker-dump-snapshot", "schema_version": 1,
            "source": {"image_sha256": ai.GENERAL_SHA256, "label": label,
                       "freshness": "post_baseline_complete_dump_proven"},
            "entries": [{"path": path, "value": value} for path, value in values.items()]}


class GeneralClassTests(unittest.TestCase):
    def test_stock_policy_preserves_every_player_class(self):
        for cls in range(3):
            self.assertEqual(ai.class_plan("stock", cls), (cls,) * 3)

    def test_diverse_plan_independent_of_player(self):
        for cls in range(3):
            self.assertEqual(ai.class_plan("diverse", cls), (2, 1, 0))

    def test_all_mixed_class_inputs_and_slot_independence(self):
        for plan in itertools.product(range(3), repeat=3):
            for player in range(3):
                self.assertEqual(ai.class_plan("mixed", player, plan), plan)
                changed = ((plan[0] + 1) % 3, *plan[1:])
                self.assertEqual(ai.class_plan("mixed", player, changed)[1:], plan[1:])

    def test_invalid_policy_and_ranges_fail_closed(self):
        for policy, player, draws in (("unknown", 0, (0, 1, 2)), ("stock", True, (0, 1, 2)),
                                      ("mixed", 0, (0, 1)), ("mixed", 0, (0, 1, 3)),
                                      ("mixed", 0, (0, True, 2))):
            with self.assertRaises(ValueError):
                ai.class_plan(policy, player, draws)
        with self.assertRaises(ValueError):
            ai.general_code("stock")

    def test_general_patch_deterministic_and_confined(self):
        ranges = ai.general_ranges()
        source = bytearray(ai.GENERAL_BASE - 0x400000 + len(ai.general_code()[0]))
        for row in ranges:
            source[row["offset"]:row["offset"] + len(row["original"])] = row["original"]
        source = bytes(source)
        result = ai.apply_ranges(source, ranges, ai.sha256(source))
        self.assertEqual(result, ai.apply_ranges(source, ai.general_ranges(), ai.sha256(source)))
        approved = {n for row in ranges for n in range(row["offset"], row["offset"] + len(row["original"]))}
        self.assertTrue(all(n in approved for n, (a, b) in enumerate(zip(source, result)) if a != b))
        self.assertEqual(len(result), len(source))
        new_size = struct.unpack("<I", ranges[0]["replacement"])[0]
        self.assertEqual((new_size + 4095) // 4096, (ai.ORIGINAL_TEXT_SIZE + 4095) // 4096)
        self.assertEqual(len(ranges), 5)

    def test_patch_hash_and_original_bytes_are_separate_gates(self):
        for policy in ("stock", "mixed", "diverse"):
            with self.assertRaises(ValueError):
                ai.build_general(bytes(ai.RETAIL_SIZE), policy)
        with self.assertRaises(ValueError):
            ai.verify_general(bytes(ai.RETAIL_SIZE))
        with self.assertRaisesRegex(ValueError, "original bytes"):
            ai.apply_ranges(b"abc", [{"offset": 0, "original": b"Z", "replacement": b"Y"}], ai.sha256(b"abc"))

    def test_every_plan_uses_valid_stock_identity_and_state_only_verdict(self):
        for plan in itertools.product(range(3), repeat=3):
            report = ai.check_general_snapshot(capture(plan), ai.GENERAL_SHA256)
            self.assertFalse(report["runtime_full_pass"])
            self.assertEqual(report["status"], "BROKER_STATE_MATCH_ONLY")
            self.assertEqual(tuple(row["CarClass"] for row in report["participants"][1:]), plan)
            self.assertEqual(len(report["participants"]), 4)

    def test_oracle_rejects_wrong_setup_identity_physics_or_network(self):
        for path, value in (("Race/NumCars", 5), ("Race/NumPlayers", 2), ("Race/Type", 14),
                            ("Race/AttractMode", True), ("Race/NumNetworkPlayers", 1),
                            ("Race/NetworkSyncActive", True), ("Frontend/QuickRace/Ghost", 1),
                            ("Race/Car0/CarID", 1), ("Race/Car1/CarClass", 0),
                            ("Race/Car1/CarID", 22), ("Race/Car2/DriverID", 1),
                            ("Race/Car3/PlayerType", True), ("Race/Car1/WheelType", "Landcruiser"),
                            ("Vehicles/Car2/Engine/GearRatioDiff", 123)):
            snapshot = capture()
            next(row for row in snapshot["entries"] if row["path"] == path)["value"] = value
            with self.assertRaises(ValueError, msg=path):
                ai.check_general_snapshot(snapshot, ai.GENERAL_SHA256)

    def test_capture_freshness_hash_and_label_rejection(self):
        for key, value in (("label", "mixed-random-race-0"), ("label", "mixed-return"),
                            ("freshness", "recovery"), ("image_sha256", ai.CANDIDATE_SHA256)):
            snapshot = capture()
            snapshot["source"][key] = value
            with self.assertRaises(ValueError):
                ai.check_general_snapshot(snapshot, ai.GENERAL_SHA256)

    def test_ambiguous_missing_and_aliased_paths_reject(self):
        snapshot = capture()
        snapshot["entries"].append(dict(snapshot["entries"][0]))
        with self.assertRaises(ValueError):
            ai.check_general_snapshot(snapshot, ai.GENERAL_SHA256)
        snapshot = capture()
        snapshot["entries"] = [row for row in snapshot["entries"] if row["path"] != "Race/Car2/CarID"]
        with self.assertRaises(ValueError):
            ai.check_general_snapshot(snapshot, ai.GENERAL_SHA256)
        snapshot = capture((0, 0, 0))
        for row in snapshot["entries"]:
            if row["path"] == "Race/Car3/CarID":
                row["value"] = 2
        with self.assertRaises(ValueError):
            ai.check_general_snapshot(snapshot, ai.GENERAL_SHA256)

    def test_five_sample_summary_variation_and_no_full_pass(self):
        reports = [ai.check_general_snapshot(capture(plan, f"mixed-random-race-{n}"), ai.GENERAL_SHA256)
                   for n, plan in enumerate(((2, 1, 0), (0, 0, 0), (1, 2, 1), (2, 2, 0), (0, 1, 2)), 1)]
        result = ai.summarize_general(reports)
        self.assertEqual(result["status"], "BROKER_SAMPLING_MATCH_ONLY")
        self.assertFalse(result["runtime_full_pass"])
        with self.assertRaises(ValueError):
            ai.summarize_general(reports[:4])
        duplicated = copy.deepcopy(reports)
        duplicated[-1]["label"] = duplicated[0]["label"]
        with self.assertRaises(ValueError):
            ai.summarize_general(duplicated)
        changed_course = copy.deepcopy(reports)
        changed_course[-1]["course"] = 11
        with self.assertRaises(ValueError):
            ai.summarize_general(changed_course)

    def test_fixed_or_all_player_class_samples_do_not_pass_randomization(self):
        reports = [ai.check_general_snapshot(capture((0, 0, 0), f"mixed-random-race-{n}"), ai.GENERAL_SHA256)
                   for n in range(1, 6)]
        self.assertEqual(ai.summarize_general(reports)["status"], "MORE_SAMPLES_NEEDED")

    def test_external_implementation_and_unknown_images_reject(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            for filename in observe.OBSERVATORY_FILES:
                (directory / filename).write_bytes(b"unreviewed implementation")
            with self.assertRaisesRegex(ValueError, "implementation changed"):
                observe.verify_distribution(directory)
            candidate = directory / "MRallye.exe"
            candidate.write_bytes(b"unknown executable")
            with self.assertRaisesRegex(ValueError, "Unknown research image"):
                observe.load_profile(directory, candidate)

    def test_physics_canary_source_and_registry_consistency(self):
        table = json.loads((ai.REPOSITORY / "research/r-ai1-1/vehicle-physics-canaries.json").read_text())
        self.assertEqual(table["source_sha256"], ai.VEHICLES_SHA256)
        self.assertEqual(len(table["vehicles"]), 25)
        for canary, stock in zip(table["vehicles"], ai.stock_map()):
            self.assertEqual((canary["id"], canary["family"]), (stock["id"], stock["family"]))
        self.assertEqual(table["vehicles"][14]["values"]["Dimensions/WheelBase"], 2.77)
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "vehicles.xml"
            path.write_bytes(b"not retail")
            with self.assertRaises(ValueError):
                ai.physics_canary_table(path)


if __name__ == "__main__":
    unittest.main()
