from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_vehicle_ai_runtime as checker


EXPECTED_SHA = "a" * 64
EXPECTED_IMAGE = r"D:\verified-h\runtime-package\MRallye.exe"
EXPECTED_ROOT = r"D:\verified-h\runtime-package"


def capture_fixture() -> dict:
    entries = [
        {"path": "Race/NumCars", "type": "Int", "value": 4},
        {"path": "Race/NumPlayers", "type": "Int", "value": 1},
    ]
    rows = [
        {"PlayerType": 44, "DriverID": 30, "CarID": 0, "CarClass": 0,
         "CarType": "Landcruiser", "WheelType": "Landcruiser", "RaceState": 1},
        {"PlayerType": 9, "DriverID": 4, "CarID": 26, "CarClass": 0,
         "CarType": "Mercedes", "WheelType": "Mercedes", "RaceState": 1},
        {"PlayerType": 9, "DriverID": 0, "CarID": 3, "CarClass": 0,
         "CarType": "Terrano", "WheelType": "Terrano", "RaceState": 1},
        {"PlayerType": 9, "DriverID": 8, "CarID": 6, "CarClass": 0,
         "CarType": "Frontera", "WheelType": "Frontera", "RaceState": 1},
    ]
    for index, row in enumerate(rows):
        entries.extend({"path": f"Race/Car{index}/{field}", "type": "Int" if type(value) is int else "String", "value": value}
                       for field, value in row.items())
    return {
        "source": {
            "image_sha256": EXPECTED_SHA,
            "image_path": EXPECTED_IMAGE,
            "active_root": EXPECTED_ROOT,
        },
        "entries": entries,
    }


def check(capture: dict) -> dict:
    return checker.summarize_capture(
        capture,
        expected_exe_sha256=EXPECTED_SHA,
        expected_image_path=EXPECTED_IMAGE,
        expected_active_root=EXPECTED_ROOT,
    )


class VehicleAIRuntimeCheckerTests(unittest.TestCase):
    def test_forced_id26_capture_is_only_a_broker_state_match(self) -> None:
        result = check(capture_fixture())
        self.assertEqual(result["status"], "HUMAN_AI_CONFIRMATION_REQUIRED")
        self.assertEqual(result["forced_id26_classification"], "FORCED_ID26_BROKER_MATCH")
        self.assertEqual(result["candidate_identity"]["status"], "MATCH")
        self.assertEqual(result["classifications"], {
            "ID26_AI_PRESENT": "PASS",
            "ID26_IS_PHYSICAL_26": "PASS",
            "ID26_CLASS_IS_T1": "PASS",
            "ID26_MERCEDES_FAMILY": "PASS",
            "PLAYER_UNCHANGED": "PASS",
            "STOCK_CONTROLS_PRESENT": "PASS",
            "PLAYER_TYPE_MATCHES_AI_CONTROLS": "PASS",
            "NUM_CARS_IS_FOUR": "PASS",
            "NUM_PLAYERS_IS_ONE": "PASS",
        })
        self.assertEqual(result["ai_control_type_comparison"]["numeric_enum_assumed"], False)
        self.assertEqual(result["ai_vehicle_ids"], [26, 3, 6])
        self.assertIn("cannot prove model rendering", result["evidence_limit"])

    def test_player_type_enum_is_not_hardcoded(self) -> None:
        capture = capture_fixture()
        for entry in capture["entries"]:
            if entry["path"].endswith("/PlayerType"):
                entry["value"] = 100 if entry["path"].endswith("Car0/PlayerType") else 7
        result = check(capture)
        self.assertEqual(result["classifications"]["PLAYER_TYPE_MATCHES_AI_CONTROLS"], "PASS")
        self.assertEqual(result["ai_control_type_comparison"]["player_raw_value"], 100)
        self.assertEqual(result["ai_control_type_comparison"]["target_raw_value"], 7)

    def test_wrong_candidate_hash_is_not_hidden_by_matching_broker_state(self) -> None:
        result = checker.summarize_capture(
            capture_fixture(), expected_exe_sha256="b" * 64,
            expected_image_path=EXPECTED_IMAGE, expected_active_root=EXPECTED_ROOT,
        )
        self.assertEqual(result["status"], "RUNTIME_PACKAGE_MISMATCH")
        self.assertEqual(result["candidate_identity"]["status"], "MISMATCH")

    def test_expected_candidate_hash_requires_capture_identity(self) -> None:
        capture = capture_fixture()
        del capture["source"]["image_sha256"]
        result = check(capture)
        self.assertEqual(result["candidate_identity"]["status"], "INCOMPLETE")
        self.assertEqual(result["status"], "RUNTIME_PACKAGE_MISMATCH")

    def test_wrong_runtime_image_path_or_root_is_rejected(self) -> None:
        for key, value in (("image_path", r"D:\wrong\MRallye.exe"),
                           ("active_root", r"D:\wrong")):
            with self.subTest(key=key):
                capture = capture_fixture()
                capture["source"][key] = value
                result = check(capture)
                self.assertEqual(result["status"], "RUNTIME_PACKAGE_MISMATCH")
                self.assertEqual(result["candidate_identity"]["status"], "MISMATCH")

    def test_wrong_id_or_count_is_a_state_mismatch(self) -> None:
        capture = capture_fixture()
        for entry in capture["entries"]:
            if entry["path"] == "Race/Car1/CarID":
                entry["value"] = 7
        result = check(capture)
        self.assertEqual(result["status"], "FORCED_ID26_NOT_OBSERVED")
        self.assertEqual(result["classifications"]["ID26_IS_PHYSICAL_26"], "FAIL")
        self.assertEqual(result["classifications"]["ID26_AI_PRESENT"], "FAIL")

    def test_ambiguous_broker_paths_remain_unknown(self) -> None:
        capture = capture_fixture()
        capture["entries"].append({"path": "Race/Car1/CarID", "type": "Int", "value": 26})
        result = check(capture)
        self.assertEqual(result["participants"][1]["CarID"]["status"], "AMBIGUOUS")
        self.assertEqual(result["classifications"]["ID26_IS_PHYSICAL_26"], "UNKNOWN")

    def test_missing_player_type_is_unknown_not_a_false_player_failure(self) -> None:
        capture = capture_fixture()
        capture["entries"] = [
            entry for entry in capture["entries"]
            if entry["path"] != "Race/Car0/PlayerType"
        ]
        result = check(capture)
        self.assertEqual(result["classifications"]["PLAYER_UNCHANGED"], "UNKNOWN")
        self.assertEqual(result["classifications"]["PLAYER_TYPE_MATCHES_AI_CONTROLS"], "UNKNOWN")

    def test_missing_player_car_id_is_unknown_for_stock_controls(self) -> None:
        capture = capture_fixture()
        capture["entries"] = [
            entry for entry in capture["entries"]
            if entry["path"] != "Race/Car0/CarID"
        ]
        result = check(capture)
        self.assertEqual(result["classifications"]["STOCK_CONTROLS_PRESENT"], "UNKNOWN")

    def test_missing_capture_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "entries array"):
            checker.summarize_capture(
                {"paths": []}, expected_exe_sha256=EXPECTED_SHA,
                expected_image_path=EXPECTED_IMAGE, expected_active_root=EXPECTED_ROOT,
            )

    def test_natural_t1_capture_allows_valid_absent_id26_sample(self) -> None:
        result = self._check_natural(self._natural_capture([1, 3, 5]))
        self.assertEqual(result["status"], "NATURAL_T1_POOL_CAPTURE")
        self.assertEqual(result["classifications"]["ID26_AI_ABSENT_VALID_SAMPLE"], "PASS")
        self.assertEqual(result["classifications"]["ID26_AI_PRESENT"], "NOT_OBSERVED")
        self.assertEqual(result["classifications"]["ID7_T1_CONTAMINATION"], "PASS")
        self.assertTrue(result["valid_id26_absent_sample"])

    def test_natural_t1_capture_recognizes_id26_with_mercedes_locked_player(self) -> None:
        result = self._check_natural(self._natural_capture([26, 2, 4]))
        self.assertEqual(result["status"], "NATURAL_T1_POOL_CAPTURE")
        self.assertEqual(result["id26_ai_slots"], [1])
        self.assertEqual(result["classifications"]["PHYSICAL_ID26_OK"], "PASS")
        self.assertEqual(result["classifications"]["MERCEDES_FAMILY_OK"], "PASS")
        self.assertEqual(result["classifications"]["PLAYER_MERCEDES_LOCKED_IF_OBSERVED"], "PASS")
        self.assertEqual(result["classifications"]["FORCED_HOOK_EXPECTED_FALSE"], "PASS")

    def test_natural_t1_rejects_id7_contamination_and_forced_manifest(self) -> None:
        result = self._check_natural(self._natural_capture([7, 2, 4]))
        self.assertEqual(result["status"], "BROKER_STATE_INCOMPLETE_OR_MISMATCH")
        self.assertEqual(result["classifications"]["ID7_T1_CONTAMINATION"], "FAIL")
        bad_manifest = self._natural_manifest()
        bad_manifest["forced_ai_proof"]["included"] = True
        refused = checker.summarize_natural_capture(
            self._natural_capture([1, 2, 4]),
            expected_exe_sha256=EXPECTED_SHA,
            expected_image_path=EXPECTED_IMAGE,
            expected_active_root=EXPECTED_ROOT,
            candidate_manifest=bad_manifest,
        )
        self.assertEqual(refused["classifications"]["FORCED_HOOK_EXPECTED_FALSE"], "FAIL")
        wrong_candidate_manifest = self._natural_manifest()
        wrong_candidate_manifest["patched_sha256"] = "b" * 64
        wrong_candidate = checker.summarize_natural_capture(
            self._natural_capture([1, 2, 4]),
            expected_exe_sha256=EXPECTED_SHA,
            expected_image_path=EXPECTED_IMAGE,
            expected_active_root=EXPECTED_ROOT,
            candidate_manifest=wrong_candidate_manifest,
        )
        self.assertEqual(wrong_candidate["candidate_identity"]["manifest_status"], "FAIL")

    def test_natural_aggregator_reports_rosters_without_probability(self) -> None:
        result = checker.aggregate_natural_captures([
            {"ai_ids": [1, 2, 3], "id26_ai_slots": []},
            {"ai_ids": [26, 4, 5], "id26_ai_slots": [1]},
        ])
        self.assertTrue(result["id26_ever_seen"])
        self.assertEqual(result["id26_slots_by_race"], [{"race": 2, "slots": [1]}])
        self.assertEqual(result["stock_ids_observed"], [1, 2, 3, 4, 5])
        self.assertEqual(result["probability_claim"], "none")

    @staticmethod
    def _check_natural(capture: dict) -> dict:
        return checker.summarize_natural_capture(
            capture,
            expected_exe_sha256=EXPECTED_SHA,
            expected_image_path=EXPECTED_IMAGE,
            expected_active_root=EXPECTED_ROOT,
            candidate_manifest=VehicleAIRuntimeCheckerTests._natural_manifest(),
        )

    @staticmethod
    def _natural_manifest() -> dict:
        return {
            "profile": "natural-t1-id26",
            "patched_sha256": EXPECTED_SHA,
            "forced_ai_proof": {"included": False},
            "randomizer": {"present": False},
            "participant_count_changed": False,
            "natural_t1_id26_pool": {
                "included": True,
                "source_ids": [0, 1, 2, 3, 4, 5, 6, 26],
                "id7_forbidden": True,
            },
            "results_identity": {
                "target_physical_car_id": 26,
                "policy": "fixed_display_name",
                "display_name": "JEAN-PIERRE STRUGO",
                "classification": "REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER",
                "exact_ml320_pairing": "unproven",
                "native_driver_id_selection_changed": False,
                "native_driver_id_written": False,
            },
        }

    @staticmethod
    def _natural_capture(ai_ids: list[int]) -> dict:
        entries = [
            {"path": "Race/NumCars", "value": 4},
            {"path": "Race/NumPlayers", "value": 1},
            {"path": "Race/Type", "value": 2},
            {"path": "Race/AttractMode", "value": False},
            {"path": "Progress/UnlockedCars/T1CupCar1", "value": False},
        ]
        participants = [
            (0, 30, 0, "Landcruiser", "Landcruiser"),
            (1, 4, ai_ids[0], "Mercedes" if ai_ids[0] == 26 else "T1Car", "Mercedes" if ai_ids[0] == 26 else "T1Car"),
            (2, 0, ai_ids[1], "Mercedes" if ai_ids[1] == 26 else "T1Car", "Mercedes" if ai_ids[1] == 26 else "T1Car"),
            (3, 8, ai_ids[2], "Mercedes" if ai_ids[2] == 26 else "T1Car", "Mercedes" if ai_ids[2] == 26 else "T1Car"),
        ]
        for slot, driver_id, car_id, car_type, wheel_type in participants:
            values = {
                "PlayerType": 1 if slot == 0 else 2,
                "DriverID": driver_id,
                "CarID": car_id,
                "CarClass": 0,
                "CarType": car_type,
                "WheelType": wheel_type,
                "RaceState": 1,
            }
            entries.extend({"path": f"Race/Car{slot}/{field}", "value": value}
                           for field, value in values.items())
        return {
            "entries": entries,
            "source": {
                "image_sha256": EXPECTED_SHA,
                "image_path": EXPECTED_IMAGE,
                "active_root": EXPECTED_ROOT,
            },
        }


if __name__ == "__main__":
    unittest.main()
