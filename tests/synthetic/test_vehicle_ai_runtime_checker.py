from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_vehicle_ai_runtime as checker


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
    return {"source": {"image_sha256": "a" * 64}, "entries": entries}


class VehicleAIRuntimeCheckerTests(unittest.TestCase):
    def test_forced_id26_capture_is_only_a_broker_state_match(self) -> None:
        result = checker.summarize_capture(
            capture_fixture(), expected_exe_sha256="a" * 64
        )
        self.assertEqual(result["status"], "BROKER_STATE_MATCH_ONLY")
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
        result = checker.summarize_capture(capture)
        self.assertEqual(result["classifications"]["PLAYER_TYPE_MATCHES_AI_CONTROLS"], "PASS")
        self.assertEqual(result["ai_control_type_comparison"]["player_raw_value"], 100)
        self.assertEqual(result["ai_control_type_comparison"]["target_raw_value"], 7)

    def test_wrong_candidate_hash_is_not_hidden_by_matching_broker_state(self) -> None:
        result = checker.summarize_capture(
            capture_fixture(), expected_exe_sha256="b" * 64
        )
        self.assertEqual(result["status"], "CANDIDATE_IDENTITY_MISMATCH")
        self.assertEqual(result["candidate_identity"]["status"], "MISMATCH")

    def test_expected_candidate_hash_requires_capture_identity(self) -> None:
        capture = capture_fixture()
        del capture["source"]["image_sha256"]
        result = checker.summarize_capture(
            capture, expected_exe_sha256="a" * 64
        )
        self.assertEqual(result["candidate_identity"]["status"], "UNKNOWN")
        self.assertEqual(result["status"], "BROKER_STATE_INCOMPLETE_OR_MISMATCH")

    def test_wrong_id_or_count_is_a_state_mismatch(self) -> None:
        capture = capture_fixture()
        for entry in capture["entries"]:
            if entry["path"] == "Race/Car1/CarID":
                entry["value"] = 7
        result = checker.summarize_capture(capture)
        self.assertEqual(result["status"], "BROKER_STATE_INCOMPLETE_OR_MISMATCH")
        self.assertEqual(result["classifications"]["ID26_IS_PHYSICAL_26"], "FAIL")
        self.assertEqual(result["classifications"]["ID26_AI_PRESENT"], "FAIL")

    def test_ambiguous_broker_paths_remain_unknown(self) -> None:
        capture = capture_fixture()
        capture["entries"].append({"path": "Race/Car1/CarID", "type": "Int", "value": 26})
        result = checker.summarize_capture(capture)
        self.assertEqual(result["participants"][1]["CarID"]["status"], "AMBIGUOUS")
        self.assertEqual(result["classifications"]["ID26_IS_PHYSICAL_26"], "UNKNOWN")

    def test_missing_player_type_is_unknown_not_a_false_player_failure(self) -> None:
        capture = capture_fixture()
        capture["entries"] = [
            entry for entry in capture["entries"]
            if entry["path"] != "Race/Car0/PlayerType"
        ]
        result = checker.summarize_capture(capture)
        self.assertEqual(result["classifications"]["PLAYER_UNCHANGED"], "UNKNOWN")
        self.assertEqual(result["classifications"]["PLAYER_TYPE_MATCHES_AI_CONTROLS"], "UNKNOWN")

    def test_missing_player_car_id_is_unknown_for_stock_controls(self) -> None:
        capture = capture_fixture()
        capture["entries"] = [
            entry for entry in capture["entries"]
            if entry["path"] != "Race/Car0/CarID"
        ]
        result = checker.summarize_capture(capture)
        self.assertEqual(result["classifications"]["STOCK_CONTROLS_PRESENT"], "UNKNOWN")

    def test_missing_capture_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "entries array"):
            checker.summarize_capture({"paths": []})


if __name__ == "__main__":
    unittest.main()
