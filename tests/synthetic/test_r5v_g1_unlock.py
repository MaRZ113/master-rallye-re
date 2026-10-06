from __future__ import annotations

import struct
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import patch_vehicle_registry_id26 as patcher
from r5v_g1_unlock import (
    UNLOCK_PATH_BY_ID,
    id26_stock_mirror_gate,
    quickrace_reachable_classes,
    stock_vehicle_gate,
    summarize_capture,
)
from test_vehicle_registry_id26_patcher import retail_layout_fixture


class R5vG1UnlockModelTests(unittest.TestCase):
    def test_stock_t1_oracle_false_and_true_follow_named_progress_flag(self) -> None:
        self.assertFalse(stock_vehicle_gate(
            3, {"T1CupCar1": False}, {"UnlockAll": False, "UnlockCars": False}))
        self.assertTrue(stock_vehicle_gate(
            3, {"T1CupCar1": True}, {"UnlockAll": False, "UnlockCars": False}))

    def test_stock_default_and_special_id25_predicates_remain_distinct(self) -> None:
        self.assertTrue(stock_vehicle_gate(0, {}, {}))
        self.assertFalse(stock_vehicle_gate(
            25, {"Bonus2": False}, {"UnlockAll": False, "UnlockCars": False}))
        self.assertTrue(stock_vehicle_gate(
            25, {"Bonus2": True}, {"UnlockAll": False, "UnlockCars": False}))
        self.assertTrue(stock_vehicle_gate(26, {}, {}))  # pristine native default only

    def test_global_car_cheats_bypass_stock_vehicle_predicates(self) -> None:
        self.assertTrue(stock_vehicle_gate(
            3, {"T1CupCar1": False}, {"UnlockAll": False, "UnlockCars": True}))
        self.assertTrue(stock_vehicle_gate(
            3, {"T1CupCar1": False}, {"UnlockAll": True, "UnlockCars": False}))

    def test_g1_profile_mirrors_id3_only_and_retains_physical_id26(self) -> None:
        unlocked = {"T1CupCar1": False}
        cheats = {"UnlockAll": False, "UnlockCars": False}
        self.assertFalse(id26_stock_mirror_gate(26, unlocked, cheats))
        self.assertTrue(id26_stock_mirror_gate(
            26, {"T1CupCar1": True}, cheats))
        self.assertTrue(id26_stock_mirror_gate(0, unlocked, cheats))
        self.assertFalse(id26_stock_mirror_gate(3, unlocked, cheats))

    def test_missing_progress_is_unknown_not_locked(self) -> None:
        self.assertIsNone(stock_vehicle_gate(3, {}, {}))

    def test_quickrace_class_gate_is_independent_from_vehicle_gate(self) -> None:
        self.assertEqual(quickrace_reachable_classes({
            "T2Cup": False, "T3Cup": False, "UnlockCups": False, "UnlockAll": False,
        }), ["T1"])
        self.assertEqual(quickrace_reachable_classes({
            "T2Cup": True, "T3Cup": False, "UnlockCups": False, "UnlockAll": False,
        }), ["T1", "T2"])
        self.assertEqual(quickrace_reachable_classes({
            "T2Cup": False, "T3Cup": True, "UnlockCups": False, "UnlockAll": False,
        }), ["T1", "T2", "T3"])
        self.assertIsNone(quickrace_reachable_classes({"T3Cup": False}))

    def test_machine_matrix_covers_every_native_slot_0_through_25(self) -> None:
        root = Path(__file__).resolve().parents[2]
        matrix = json.loads((root / "research/r5v_g1/stock-unlock-matrix.json").read_text(
            encoding="utf-8"))
        vehicles = matrix["vehicles"]
        self.assertEqual([entry["id"] for entry in vehicles], list(range(26)))
        for entry in vehicles:
            vehicle_id = entry["id"]
            if vehicle_id in UNLOCK_PATH_BY_ID:
                self.assertEqual(entry["predicate"], UNLOCK_PATH_BY_ID[vehicle_id])
            else:
                self.assertEqual(entry["predicate"], "unconditional")
        self.assertFalse(vehicles[25]["stock_record_initialized"])

    def test_matrix_and_candidate_profile_keep_physical_id26_separate(self) -> None:
        root = Path(__file__).resolve().parents[2]
        profile = json.loads((root / "research/r5v_g1/id26-unlock-profile.json").read_text(
            encoding="utf-8"))
        self.assertEqual(profile["physical_vehicle"]["id"], 26)
        self.assertTrue(profile["physical_vehicle"]["preserve_physical_id"])
        self.assertEqual(profile["unlock_policy"]["stock_oracle_id"], 3)
        self.assertFalse(profile["unlock_policy"]["registry_id_or_class_substituted"])


class R5vG1CandidateTests(unittest.TestCase):
    def test_candidate_uses_id3_gate_without_test_unlocking_id25(self) -> None:
        source = retail_layout_fixture()
        candidate, manifest = patcher.make_candidate(
            source,
            expected_sha256=patcher.sha256(source),
            id26_profile=patcher.ID26_MERCEDES_G1_STOCK_UNLOCK,
        )
        self.assertEqual(manifest["phase"], "R5V-G.1 Mercedes stock-like T1 unlock candidate")
        self.assertIn("READY FOR HUMAN RUNTIME", manifest["runtime_validation"])
        operations = {item["name"]: item for item in manifest["operations"]}
        self.assertNotIn("id25_test_unlock", operations)
        self.assertIn("id26_narrow_unlock_call", operations)
        offset = patcher.va_to_file_offset(patcher.parse_pe(source), 0x45A282, 4)
        self.assertEqual(candidate[offset:offset + 4], bytes.fromhex("6a0fe887"))
        unlock = manifest["structural_self_check"]["unlock"]
        self.assertEqual(unlock["id25"], "native Progress/UnlockedCars/Bonus2 predicate retained")
        self.assertEqual(unlock["id26"]["oracle_id"], 3)
        self.assertEqual(unlock["id26"]["progress_path"], "Progress/UnlockedCars/T1CupCar1")
        self.assertEqual(unlock["id26"]["physical_record_id_preserved"], 26)

        structural = manifest["structural_self_check"]
        payload = bytes.fromhex(next(item["replacement_bytes"] for item in manifest["operations"]
                                     if item["name"] == "id26_code_cave_payload"))
        entry = int(structural["code_entrypoints"]["id26_unlock"], 16)
        helper = payload[entry - patcher.STUB_VA:]
        self.assertEqual(helper[:5], bytes.fromhex("518379041a"))
        self.assertEqual(helper[5:7], b"\x0f\x85")
        branch = struct.unpack_from("<i", helper, 7)[0]
        stock_entry = int(structural["code_entrypoints"]["id26_unlock_stock"], 16)
        self.assertEqual(entry + 11 + branch, stock_entry)
        self.assertEqual(helper[11:32], bytes.fromhex(
            "83ec08c7042400000000c7442404030000008d0c24"))
        self.assertEqual(helper[32], 0xE8)
        mirror_call_delta = struct.unpack_from("<i", helper, 33)[0]
        self.assertEqual(entry + 37 + mirror_call_delta, 0x45A150)
        self.assertEqual(helper[37:42], bytes.fromhex("83c40859c3"))
        stock_offset = stock_entry - entry
        self.assertEqual(helper[stock_offset], 0xE8)
        stock_call_delta = struct.unpack_from("<i", helper, stock_offset + 1)[0]
        self.assertEqual(entry + stock_offset + 5 + stock_call_delta, 0x45A150)
        self.assertEqual(helper[stock_offset + 5:stock_offset + 7], b"\x59\xC3")
        self.assertEqual(structural["id26"]["id"], 26)
        self.assertEqual(structural["id26"]["class"], 0)
        self.assertEqual(structural["id26"]["class_local_index"], 7)

    def test_g1_candidate_retains_f2f_frontend_string_hooks(self) -> None:
        _candidate, manifest = patcher.make_candidate(
            retail_layout_fixture(),
            expected_sha256=patcher.sha256(retail_layout_fixture()),
            id26_profile=patcher.ID26_MERCEDES_G1_STOCK_UNLOCK,
        )
        names = {item["name"] for item in manifest["operations"]}
        self.assertIn("race_options_manufacturer_lookup_id26_string_override", names)
        self.assertIn("race_options_model_lookup_id26_string_override", names)
        self.assertIn("quickrace_name_string_override_0", names)


class R5vG1CaptureSummaryTests(unittest.TestCase):
    def test_capture_summarizes_known_fresh_gate_state_without_claiming_visibility(self) -> None:
        values = {
            "Progress/UnlockedCars/T1CupCar1": False,
            "Progress/OpenedModes/T2Cup": False,
            "Progress/OpenedModes/T3Cup": False,
            "Progress/Cheats/UnlockCups": False,
            "Progress/Cheats/UnlockAll": False,
            "Progress/Cheats/UnlockCars": False,
            "Frontend/VehicleSelect/CarModel": 26,
        }
        capture = {
            "source": {"label": "test-fresh", "build": "retail", "image_sha256": "abc"},
            "entries": [{"path": path, "value": value} for path, value in values.items()],
        }
        result = summarize_capture(capture)
        self.assertEqual(result["status"], "UNLOCK_STATE_SUMMARY_ONLY")
        self.assertEqual(result["quickrace_reachable_classes"], ["T1"])
        self.assertFalse(result["stock_vehicle_id3_gate_expected"])
        self.assertEqual(result["observed_state"]["vehicle_select_car_model"],
                         {"status": "OBSERVED", "value": 26})
        self.assertIn("does not prove rendered visibility", result["evidence_limit"])

    def test_capture_reports_unknown_for_missing_unlock_and_class_inputs(self) -> None:
        result = summarize_capture({"entries": []})
        self.assertEqual(result["quickrace_reachable_classes"], "UNKNOWN")
        self.assertEqual(result["stock_vehicle_id3_gate_expected"], "UNKNOWN")
        self.assertEqual(result["progress"]["T1CupCar1"]["status"], "UNKNOWN")
        self.assertEqual(result["observed_state"]["vehicle_select_car_model"]["status"], "UNKNOWN")

    def test_duplicate_capture_paths_are_ambiguous(self) -> None:
        capture = {"entries": [
            {"path": "Progress/UnlockedCars/T1CupCar1", "value": False},
            {"path": "progress/unlockedcars/t1cupcar1", "value": True},
        ]}
        result = summarize_capture(capture)
        self.assertEqual(result["progress"]["T1CupCar1"]["status"], "AMBIGUOUS")
        self.assertEqual(result["stock_vehicle_id3_gate_expected"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
