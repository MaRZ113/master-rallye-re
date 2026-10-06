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


if __name__ == "__main__":
    unittest.main()
