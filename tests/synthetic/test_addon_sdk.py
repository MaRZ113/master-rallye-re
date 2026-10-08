from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_library import simple_record, synthetic_dx
from master_rallye.addon_sdk import (
    AddonValidationError, build_to_directory, inspect_frontend_capture,
    load_capabilities, load_manifests, validate_manifests, verify_build,
    verify_retail_executable,
)


CAPABILITIES_PATH = ROOT / "research/vehicles/sdk/capabilities/retail-2001.json"
EXAMPLE_DIR = ROOT / "research/vehicles/sdk/examples"


def example_paths() -> list[Path]:
    return [EXAMPLE_DIR / "mercedes-ml320.json", EXAMPLE_DIR / "r5v-qualifier-t2.json"]


def load_example_values() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in example_paths()]


class AddonSdkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capabilities, self.capability_sha = load_capabilities(CAPABILITIES_PATH)
        self.manifests = load_example_values()

    def test_examples_resolve_sparse_physical_and_local_maps_both_directions(self) -> None:
        plan = validate_manifests(self.manifests, self.capabilities)
        self.assertEqual([(row["physical_id"], row["vehicle_class"], row["class_local_index"])
                          for row in plan["addons"]], [(26, "T1", 7), (27, "T2", 7)])
        self.assertEqual(plan["class_mapping"]["class_to_physical_ids"]["T1"], list(range(7)) + [26])
        self.assertEqual(plan["class_mapping"]["class_to_physical_ids"]["T2"], list(range(7, 14)) + [27])
        self.assertEqual(plan["class_mapping"]["physical_id_to_class_local"]["26"],
                         {"vehicle_class": "T1", "class_local_index": 7})
        self.assertEqual(plan["class_mapping"]["physical_id_to_class_local"]["27"],
                         {"vehicle_class": "T2", "class_local_index": 7})
        self.assertEqual(plan["registry_layout"], {
            "record_count": 28, "vehicle_record_base": 4, "vehicle_record_stride": 0x34,
            "race_test_base": 0x5B4, "race_test_count": 39, "race_test_stride": 0x2C,
            "allocation_size": 0xC68,
        })

    def test_auto_id_resolution_is_stable_and_reads_capability_pool(self) -> None:
        manifests = load_example_values()
        for manifest in manifests:
            manifest["physical_id"] = {"policy": "auto", "value": None}
        a = validate_manifests(manifests, self.capabilities)
        b = validate_manifests(list(reversed(manifests)), self.capabilities)
        mapping_a = {row["addon_id"]: row["physical_id"] for row in a["addons"]}
        mapping_b = {row["addon_id"]: row["physical_id"] for row in b["addons"]}
        self.assertEqual(mapping_a, {"mercedes-ml320": 26, "r5v-qualifier-t2": 27})
        self.assertEqual(mapping_a, mapping_b)

    def test_rejects_reserved_duplicate_and_unqualified_physical_ids(self) -> None:
        for bad_id in (3, 25, 28, 100):
            with self.subTest(physical_id=bad_id):
                manifest = copy.deepcopy(self.manifests[0])
                manifest["physical_id"]["value"] = bad_id
                with self.assertRaises(AddonValidationError):
                    validate_manifests([manifest], self.capabilities)
        duplicate = load_example_values()
        duplicate[1]["physical_id"]["value"] = 26
        with self.assertRaisesRegex(AddonValidationError, "collision"):
            validate_manifests(duplicate, self.capabilities)

    def test_class_slot_overflow_is_rejected_instead_of_assuming_more_capacity(self) -> None:
        manifests = load_example_values()
        for manifest in manifests:
            manifest["vehicle_class"] = "T1"
            manifest["physical_id"] = {"policy": "auto", "value": None}
        with self.assertRaisesRegex(AddonValidationError, "class-local capacity"):
            validate_manifests(manifests, self.capabilities)

    def test_rejects_family_or_resource_name_collision(self) -> None:
        manifests = load_example_values()
        manifests[1]["identity"]["runtime_family"] = manifests[0]["identity"]["runtime_family"]
        with self.assertRaisesRegex(AddonValidationError, "runtime_family collision"):
            validate_manifests(manifests, self.capabilities)

    def test_policy_validation_keeps_unlock_audio_ai_and_results_independent(self) -> None:
        plan = validate_manifests(self.manifests, self.capabilities)
        mercedes, qualifier = plan["addons"]
        self.assertEqual(mercedes["unlock"], {"policy": "mirror_stock_unlock", "stock_vehicle_id": 3})
        self.assertEqual(qualifier["unlock"]["stock_vehicle_id"], 10)
        self.assertEqual((mercedes["audio"]["stock_audio_profile_id"],
                          qualifier["audio"]["stock_audio_profile_id"]), (0, 7))
        self.assertFalse(mercedes["ai_eligibility"]["invitation"]["enabled"])
        self.assertFalse(qualifier["ai_eligibility"]["challenge"]["enabled"])
        self.assertEqual(mercedes["results"]["display_name"], "JEAN-PIERRE STRUGO")
        self.assertEqual(qualifier["results"]["display_name"], "R5V TEST DRIVER")
        self.assertEqual(qualifier["race_colour_rgba_f32le_hex"], "0000803f000000000000803f0000803f")
        self.assertNotIn("driver_id", qualifier)

    def test_unsupported_audio_challenge_randomization_and_unsafe_paths_fail(self) -> None:
        invalid = copy.deepcopy(self.manifests[0])
        invalid["audio"]["stock_audio_profile_id"] = 25
        with self.assertRaisesRegex(AddonValidationError, "0..24"):
            validate_manifests([invalid], self.capabilities)
        invalid = copy.deepcopy(self.manifests[0])
        invalid["ai_eligibility"]["challenge"] = {
            "enabled": True, "boundary": "event", "pool": "dynamic_class"
        }
        with self.assertRaises(AddonValidationError):
            validate_manifests([invalid], self.capabilities)
        invalid = copy.deepcopy(self.manifests[0])
        invalid["identity"]["model_family"] = "../Navara"
        invalid["assets"]["model_package_root"] = "DataGx/Vehicles/../Navara"
        with self.assertRaises(AddonValidationError):
            validate_manifests([invalid], self.capabilities)

    def test_offline_build_is_deterministic_and_verifier_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            root = Path(temporary)
            paths = example_paths()
            out_a = root / "a"
            out_b = root / "b"
            build_to_directory(paths, CAPABILITIES_PATH, out_a)
            build_to_directory(list(reversed(paths)), CAPABILITIES_PATH, out_b)
            self.assertEqual(verify_build(out_a)["status"], "PASS")
            files_a = {p.relative_to(out_a).as_posix(): p.read_bytes()
                       for p in out_a.rglob("*") if p.is_file()}
            files_b = {p.relative_to(out_b).as_posix(): p.read_bytes()
                       for p in out_b.rglob("*") if p.is_file()}
            self.assertEqual(files_a, files_b)
            self.assertFalse(json.loads((out_a / "build-manifest.json").read_text())["runtime_installable"])
            (out_a / "addon-plan.json").write_bytes(b"tampered")
            with self.assertRaisesRegex(AddonValidationError, "SHA256 mismatch"):
                verify_build(out_a)

    def test_external_asset_dependency_closure_is_validated_and_staged(self) -> None:
        positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        record = simple_record(0, 2, 0, 3, ("Null",))
        dx = synthetic_dx(positions, [0, 1, 2], [record], [(0, 0, 3)])
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            root = Path(temporary)
            assets = root / "assets"
            for family in ("Mercedes", "R5VQualifier"):
                folder = assets / "DataGx" / "Vehicles" / family
                folder.mkdir(parents=True)
                for role in ("car.dx", "complete.dx", "wheel.dx"):
                    (folder / role).write_bytes(dx)
            output = root / "compiled"
            build_to_directory(example_paths(), CAPABILITIES_PATH, output, assets_root=assets)
            self.assertEqual(verify_build(output)["status"], "PASS")
            inventory = json.loads((output / "resource-inventory.json").read_text())
            self.assertEqual(inventory["status"], "REQUIRED_ASSETS_VALIDATED")
            self.assertEqual(len(inventory["resources"]), 6)
            self.assertEqual(len(list((output / "DataGx" / "Vehicles").rglob("*.dx"))), 6)

    def test_missing_or_invalid_asset_dependency_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            root = Path(temporary)
            folder = root / "DataGx" / "Vehicles" / "Mercedes"
            folder.mkdir(parents=True)
            (folder / "car.dx").write_bytes(b"not a DX")
            (folder / "complete.dx").write_bytes(b"not a DX")
            (folder / "wheel.dx").write_bytes(b"not a DX")
            with self.assertRaises(AddonValidationError):
                build_to_directory([example_paths()[0]], CAPABILITIES_PATH, root / "out", assets_root=root)

    def test_wrong_retail_executable_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "MRallye.exe"
            path.write_bytes(b"wrong build")
            with self.assertRaisesRegex(AddonValidationError, "SHA256"):
                verify_retail_executable(path, self.capabilities)

    def test_capture_a_reports_scene_divergence_without_claiming_id_loss(self) -> None:
        fixture = json.loads((ROOT / "research/vehicles/sdk/fixtures/frontend-reentry.json").read_text())
        self.assertEqual(fixture["changed_broker_path_count"], 21)
        for key in ("capture_a", "capture_b"):
            state = fixture[key]["state"]
            capture = {
                "source": {"label": fixture[key]["label"], "image_sha256": fixture["candidate_exe_sha256"], "process_id": 14300},
                "entries": [{"path": path, "value": value, "ordinal": index}
                            for index, (path, value) in enumerate(state.items())],
            }
            with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
                path = Path(temporary) / "capture.json"
                path.write_text(json.dumps(capture), encoding="utf-8")
                result = inspect_frontend_capture(path, expected_exe_sha256=fixture["candidate_exe_sha256"])
            self.assertEqual(result["stored_quickrace_car_id"], 27)
            self.assertEqual(result["expected_class_from_stored_id"], "T2")
            self.assertEqual(result["expected_local_from_stored_id"], 7)
            self.assertIs(result["physical_vehicle_record_loss"], "NOT_INFERRED_FROM_THIS_FRONTEND_CAPTURE")
            if key == "capture_a":
                self.assertEqual(result["status"], "FRONTEND_SELECTION_DIVERGENCE_STORED_ID_RETAINED")
                self.assertEqual(result["xybutton_local_ordinal"], 0)
                self.assertEqual(result["displayed_car_model"], 7)
            else:
                self.assertEqual(result["status"], "FRONTEND_SELECTION_CONSISTENT")
                self.assertEqual(result["xybutton_local_ordinal"], 7)
                self.assertEqual(result["displayed_car_model"], 27)

    def test_later_navara_state_is_not_misclassified_as_automatic_commit(self) -> None:
        fixture = json.loads((ROOT / "research/vehicles/sdk/fixtures/frontend-reentry.json").read_text())
        state = fixture["capture_c"]["state"]
        capture = {
            "source": {"label": fixture["capture_c"]["label"], "image_sha256": fixture["candidate_exe_sha256"], "process_id": 14300},
            "entries": [{"path": path, "value": value, "ordinal": index}
                        for index, (path, value) in enumerate(state.items())],
        }
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "capture.json"
            path.write_text(json.dumps(capture), encoding="utf-8")
            result = inspect_frontend_capture(path)
        self.assertEqual(result["stored_quickrace_car_id"], 7)
        self.assertEqual(result["selected_car_highlight_or_current_identity"], 7)
        self.assertEqual(result["vehicle_class"], "T2")
        self.assertNotIn("committed_car_id", result)
        self.assertEqual(result["physical_vehicle_record_loss"], "NOT_INFERRED_FROM_THIS_FRONTEND_CAPTURE")

    def test_schema_and_evidence_files_are_machine_readable(self) -> None:
        schema = json.loads((ROOT / "research/vehicles/sdk/schema/addon-manifest-v1.schema.json").read_text())
        evidence = json.loads((ROOT / "research/vehicles/multislot/i1-runtime-evidence.json").read_text())
        self.assertEqual(schema["properties"]["manifest_version"]["const"], 1)
        self.assertTrue(evidence["all_six_capture_pairs_raw_sha_verified"])
        ai_capture = next(row for row in evidence["captures"] if row["status"] == "NATURAL_AI_MATERIALIZATION")
        self.assertEqual(ai_capture["evidence"]["Race/Car3/CarID"], 27)


if __name__ == "__main__":
    unittest.main()
