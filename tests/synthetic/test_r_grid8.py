import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import grid8_audit as audit
import r_grid8_candidate as candidate
import r_ai2_1_capacity as capacity
import research_build_profiles as profiles


class Grid8GuardTests(unittest.TestCase):
    def test_only_registered_scene_ids_are_accepted(self):
        self.assertEqual(candidate.TRACK_IDS, tuple(range(39)))
        self.assertTrue(all(candidate.track_guard(value) for value in range(39)))
        for value in (-1, 39, 100, 0.0, True, "10"):
            self.assertFalse(candidate.track_guard(value))

    def test_only_track_guard_condition_changes(self):
        rows = candidate.ranges()
        self.assertEqual({row["va"] for row in rows if row["va"] is not None},
                         candidate.KEEP_VAS)
        count = next(row for row in rows if row["va"] == 0x68E300)
        self.assertEqual(count["replacement"].count(candidate.TRACK_GUARD_REPLACEMENT), 1)
        self.assertNotIn(candidate.TRACK_GUARD_ORIGINAL, count["replacement"])
        self.assertEqual(candidate.TRACK_GUARD_ORIGINAL.hex(), "83f80a0f851e000000")
        self.assertEqual(candidate.TRACK_GUARD_REPLACEMENT.hex(), "83f8260f871e000000")

    def test_candidate_scope_and_deterministic_roster(self):
        manifest = candidate.manifest(candidate.EXPECTED_CANDIDATE_SHA256)
        self.assertEqual(manifest["participants"], 8)
        self.assertEqual(manifest["effective_ai_count"], 7)
        self.assertEqual(manifest["guard"]["quick_race_mode"], 2)
        self.assertEqual(manifest["guard"]["visible_opponents_choice"], 3)
        self.assertFalse(manifest["guard"]["split_screen"])
        self.assertEqual(manifest["guard"]["ghost"], 0)
        self.assertEqual(manifest["guard"]["player_id"], 0)
        self.assertNotIn("race_type", manifest["guard"])
        self.assertEqual(manifest["guard"]["accepted_registered_scene_ids"], list(range(39)))
        self.assertEqual([row["CarID"] for row in manifest["roster"]], list(capacity.ROSTER))
        self.assertEqual([row["CarClass"] for row in manifest["roster"]],
                         [0, 0, 1, 2, 0, 1, 2, 2])
        self.assertEqual([row["DriverID"] for row in manifest["roster"]],
                         [30, 0, 1, 2, 3, 4, 5, 6])
        self.assertTrue(manifest["changes"]["legacy_loading_to_false_attract_hardening_retained"])
        self.assertFalse(manifest["changes"]["native_broker_dump_hardening"])
        self.assertFalse(manifest["changes"]["ui_changes"])
        self.assertFalse(manifest["changes"]["randomizer_dependency"])
        self.assertFalse(manifest["changes"]["vehicle_registry_expansion"])
        self.assertFalse(manifest["changes"]["course_assets_modified"])
        self.assertFalse(manifest["changes"]["global_grid_formula_modified"])
        self.assertFalse(manifest["changes"]["physical_participant_storage_expanded"])

    def test_audit_row_requires_consistent_status_slots_and_issue_tags(self):
        audit.validate_result_fields("PASS_CLEAR", [], [])
        audit.validate_result_fields("PHYSICS_UNSTABLE", ["Car0"],
                                     ["STATIC_GEOMETRY_CONTACT"])
        audit.validate_result_fields("PASS_TIGHT", ["Car7"], [])
        for status, slots, tags in (
            ("PASS_CLEAR", ["Car0"], []),
            ("PASS_CLEAR", [], ["STATIC_GEOMETRY_CONTACT"]),
            ("NOT_TESTED", ["Car1"], []),
            ("PHYSICS_UNSTABLE", [], []),
            ("INVALID_POSITION", ["Car8"], []),
            ("CAR_OVERLAP", ["Car3"], ["PASS_CLEAR"]),
        ):
            with self.subTest(status=status, slots=slots, tags=tags), self.assertRaises(ValueError):
                audit.validate_result_fields(status, slots, tags)

    def test_builder_rejects_non_pristine_source(self):
        for source in (b"", bytes(candidate.RETAIL_SIZE), bytes(candidate.RETAIL_SIZE - 1)):
            with self.assertRaises(ValueError):
                candidate.build(source)

class NativeGridPredictionTests(unittest.TestCase):
    def test_eight_slots_follow_three_column_row_formula(self):
        result = audit.native_grid([(0.0, 0.0, 0.0), (18.0, 0.0, 0.0)])
        self.assertEqual(result["participant_count"], 8)
        self.assertEqual(result["longitudinal_cells_per_row"], 3)
        transforms = result["transforms"]
        self.assertEqual([row["slot"] for row in transforms], list(range(7, -1, -1)))
        self.assertEqual([(row["row"], row["column"]) for row in transforms],
                         [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)])
        self.assertEqual(transforms[0]["position_xyz"], [9.0, 0.0, 0.0])
        self.assertEqual(transforms[1]["position_xyz"], [3.0, 0.0, 0.0])
        self.assertEqual(transforms[3]["position_xyz"], [9.0, 0.0, -8.0])
        self.assertEqual(transforms[-1]["slot"], 0)
        self.assertEqual(transforms[0]["orientation_basis"]["forward_xzy"], [1.0, 0.0, 0.0])
        self.assertEqual(transforms[0]["orientation_basis"]["side_xzy"], [0.0, 0.0, 1.0])
        self.assertEqual(result["clearance"], "UNKNOWN_NOT_PHYSICALLY_TESTED")

    def test_grid_formula_uses_fallback_two_columns_for_short_edge(self):
        result = audit.native_grid([(0.0, 0.0, 0.0), (3.0, 0.0, 0.0)])
        self.assertEqual(result["longitudinal_cells_per_row"], 2)
        self.assertEqual(len(result["transforms"]), 8)

    def test_transform_model_rejects_non_eight_count_and_degenerate_edge(self):
        with self.assertRaises(ValueError):
            audit.native_grid([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)], count=7)
        with self.assertRaises(ValueError):
            audit.native_grid([(1.0, 0.0, 1.0), (1.0, 0.0, 1.0)])

class Grid8CaptureOracleTests(unittest.TestCase):
    @staticmethod
    def make_snapshot():
        entries = []

        def put(path, value):
            entries.append({"path": path, "value": value})

        for path, value in {
            "Race/NumCars": 8,
            "Race/NumPlayers": 1,
            "Race/Type": 2,
            "Race/FinishingType": 0,
            "Race/AttractMode": False,
            "Race/NumNetworkPlayers": 0,
            "Race/NetworkSyncActive": False,
            "Race/GhostPlayback": False,
            "Frontend/QuickRace/Ghost": 0,
            "Frontend/QuickRace/Track": 0,
        }.items():
            put(path, value)
        for slot, car_id in enumerate(capacity.ROSTER):
            stock = profiles.vehicle("retail-pristine", car_id)
            for key, value in {
                "CarID": car_id,
                "CarClass": stock["class"],
                "PlayerType": 1 if slot == 0 else 2,
                "DriverID": 30 if slot == 0 else slot - 1,
                "CarType": stock["CarType"],
                "WheelType": stock["WheelType"],
            }.items():
                put(f"Race/Car{slot}/{key}", value)
            put(f"Vehicles/Car{slot}/Dimensions/WheelBase", 2.0)
            put(f"Physics/Car{slot}/Mass", 1000.0)
            put(f"Controller/Car{slot}/Mode", "AI" if slot else "Human")
            put(f"Network/Car{slot}/Finished", False)
        return {
            "kind": "master-rallye-broker-dump-snapshot",
            "schema_version": 1,
            "source": {
                "label": "grid8-france1",
                "freshness": "post_baseline_complete_dump_proven",
                "broker_dump_variant": "native_stock",
            },
            "entries": entries,
        }

    def test_eight_car_race_capture_matches_exact_roster_and_scene(self):
        row = {"canonical_course": "France1", "frontend_scene_ids": [0]}
        profile = {"profile_origin": "locally_audited",
                   "compatibility_family": "retail-broker-v1",
                   "vehicle_registry_profile": "unknown"}
        result = audit.validate_snapshot_state(self.make_snapshot(), row, profile)
        self.assertEqual(result["status"], "GRID8_BROKER_STATE_MATCH_ONLY")
        self.assertFalse(result["runtime_full_pass"])
        self.assertFalse(result["human_actor_visibility_proven"])
        self.assertEqual(result["race_num_cars"], 8)
        self.assertEqual([p["CarID"] for p in result["participants"]], list(capacity.ROSTER))
        self.assertEqual(result["subsystem_path_counts_not_actor_proof"]["Physics/Car7"], 1)

    def test_capture_oracle_rejects_count_scene_roster_and_missing_physics(self):
        row = {"canonical_course": "France1", "frontend_scene_ids": [0]}
        profile = {"profile_origin": "locally_audited",
                   "compatibility_family": "retail-broker-v1",
                   "vehicle_registry_profile": "unknown"}
        mutations = (
            ("Race/NumCars", 7),
            ("Frontend/QuickRace/Track", 1),
            ("Race/Car7/CarID", 16),
            ("Race/Car7/DriverID", 5),
        )
        for path, value in mutations:
            snapshot = self.make_snapshot()
            next(entry for entry in snapshot["entries"] if entry["path"] == path)["value"] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                audit.validate_snapshot_state(snapshot, row, profile)
        snapshot = self.make_snapshot()
        snapshot["entries"] = [entry for entry in snapshot["entries"]
                               if entry["path"] != "Physics/Car7/Mass"]
        with self.assertRaisesRegex(ValueError, "Physics/Car7"):
            audit.validate_snapshot_state(snapshot, row, profile)


if __name__ == "__main__":
    unittest.main()
