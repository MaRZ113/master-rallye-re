from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import addon_runtime
import build_runtime_launcher


class AddonRuntimeCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retail = addon_runtime.DEFAULT_RETAIL_EXE
        if not cls.retail.is_file():
            raise unittest.SkipTest("exact retail PE fixture is unavailable")
        cls.source = cls.retail.read_bytes()
        cls.plan, _ = addon_runtime._reference_plan(
            addon_runtime.DEFAULT_MANIFESTS, addon_runtime.DEFAULT_CAPABILITIES)
        cls.manifest, cls.rvp, cls.reference_image = addon_runtime._native_patch_artifacts(
            cls.source, cls.plan)

    def test_reference_plan_remains_j0_byte_identical(self) -> None:
        manifests, _ = addon_runtime.load_manifests(addon_runtime.DEFAULT_MANIFESTS)
        capabilities, _ = addon_runtime.load_capabilities(addon_runtime.DEFAULT_CAPABILITIES)
        artifacts = addon_runtime.build_artifacts(manifests, capabilities)
        self.assertEqual(artifacts["addon-plan.json"], addon_runtime.canonical_json(self.plan))
        self.assertEqual(addon_runtime.sha256(artifacts["addon-plan.json"]),
                         addon_runtime.REFERENCE_PLAN_SHA256)

    def test_id27_registry_marker_uses_manifest_magenta_not_body_art(self) -> None:
        addon = next(row for row in self.plan["addons"] if row["physical_id"] == 27)
        self.assertEqual(addon["race_colour_rgba"], [1.0, 0.0, 1.0, 1.0])
        _candidate, build_manifest = addon_runtime._build_reference_candidate(self.source)
        self.assertEqual(build_manifest["profiles"][1]["race_colour_rgba_bits"], [
            "3f800000", "00000000", "3f800000", "3f800000",
        ])

    def test_retail_relative_operations_reproduce_only_the_reference_file_bytes(self) -> None:
        self.assertEqual(addon_runtime.sha256(self.source), addon_runtime.RETAIL_SHA256)
        self.assertEqual(addon_runtime.sha256(self.reference_image),
                         "dd03adbd9f45c679e59d09e0a9f09337bd99c787d81f4ce018edb654c1cec881")
        self.assertEqual(len(self.reference_image), len(self.source))
        self.assertNotEqual(self.reference_image, self.source)
        self.assertFalse(self.manifest["reference_image"]["written_to_disk"])
        self.assertTrue(self.manifest["operations"])
        self.assertTrue(all(row.get("semantic_provenance") for row in self.manifest["operations"]))

    def test_rvp_counts_memory_header_and_inert_canary_separately(self) -> None:
        fields = addon_runtime.RVP_HEADER.unpack_from(self.rvp)
        self.assertEqual(fields[0], b"MRVP")
        self.assertEqual(fields[6], 246)
        operations = []
        cursor = addon_runtime.RVP_HEADER.size
        for _ in range(fields[6]):
            file_offset, rva, length, flags, page_class = addon_runtime.RVP_OPERATION.unpack_from(self.rvp, cursor)
            cursor += addon_runtime.RVP_OPERATION.size
            before = self.rvp[cursor:cursor + length]
            cursor += length
            after = self.rvp[cursor:cursor + length]
            cursor += length
            operations.append((file_offset, rva, flags, page_class, before, after))
        self.assertEqual(cursor, len(self.rvp))
        self.assertEqual(sum(row[2] == 1 for row in operations), 1)
        self.assertEqual(sum(row[2] == 2 for row in operations), 1)
        self.assertEqual(sum(row[2] == 0 for row in operations), 244)
        canary = next(row for row in operations if row[2] == 2)
        self.assertEqual(canary[:4], (addon_runtime.CANARY_FILE_OFFSET,
                                      addon_runtime.CANARY_FILE_OFFSET, 2, 2))
        self.assertEqual(canary[4], addon_runtime.CANARY_BYTES)
        self.assertEqual(canary[4], canary[5])
        self.assertEqual(self.manifest["non_mutating_canary"]["effect"].startswith("no semantic image change"), True)

    def test_file_range_mapping_is_section_bounded(self) -> None:
        pe, sections = addon_runtime._pe_sections(self.source)
        self.assertEqual(pe["machine"], addon_runtime.MACHINE_I386)
        rva, section = addon_runtime._file_range_to_rva(sections, addon_runtime.CANARY_FILE_OFFSET, 4)
        self.assertEqual((rva, section), (addon_runtime.CANARY_FILE_OFFSET, ".rdata"))
        with self.assertRaises(addon_runtime.RuntimeIntegrationError):
            addon_runtime._file_range_to_rva(sections, len(self.source) - 2, 8)

    def test_unknown_retail_build_fails_before_operation_generation(self) -> None:
        with self.assertRaisesRegex(addon_runtime.RuntimeIntegrationError, "exact pristine retail image"):
            addon_runtime._native_patch_artifacts(b"not the retail image", self.plan)

    def test_resource_index_is_sorted_and_rejects_traversal_and_case_collision(self) -> None:
        rows = [
            {"path": "DataGx/Vehicles/B/car.dx", "size": 4, "sha256": "b" * 64},
            {"path": "DataGx/Vehicles/A/car.dx", "size": 3, "sha256": "a" * 64},
        ]
        first = addon_runtime._resource_index(rows)
        self.assertEqual(first, addon_runtime._resource_index(list(reversed(rows))))
        self.assertIn(b"DataGx/Vehicles/A/car.dx", first.splitlines()[0])
        bad = dict(rows[0], path="../MRallye.exe")
        with self.assertRaisesRegex(addon_runtime.RuntimeIntegrationError, "unsafe"):
            addon_runtime._resource_index([bad])
        duplicate = [rows[0], dict(rows[1], path="datagx/vehicles/b/CAR.DX")]
        with self.assertRaisesRegex(addon_runtime.RuntimeIntegrationError, "collision"):
            addon_runtime._resource_index(duplicate)

    def test_i1_projection_deduplicates_scene_path_and_rejects_case_aliases(self) -> None:
        scene_path = "DataScene/FrontendScreens/VehicleSelect.xml"
        self.assertEqual(addon_runtime._unique_package_paths([
            "DataGx/Vehicles/R5VQualifier/car.dx", scene_path, scene_path,
        ]), ["DataGx/Vehicles/R5VQualifier/car.dx", scene_path])
        with self.assertRaisesRegex(addon_runtime.RuntimeIntegrationError, "case-insensitive path collision"):
            addon_runtime._unique_package_paths([scene_path, scene_path.lower()])

    def test_runtime_save_files_are_separate_from_the_pinned_resource_inventory(self) -> None:
        expected = {"Data.sma", "DataGame/vehicles.xml"}
        actual = expected | {"DataGame/PlayerState.xml", "DataGame/PlayerState.xml#",
                             "DataGame/options.xml#"}
        addon_runtime._validate_runtime_resource_set(expected, actual)
        with self.assertRaisesRegex(addon_runtime.RuntimeIntegrationError, "file set"):
            addon_runtime._validate_runtime_resource_set(expected, actual | {"DataGame/unexpected.xml"})
        with self.assertRaisesRegex(addon_runtime.RuntimeIntegrationError, "file set"):
            addon_runtime._validate_runtime_resource_set(expected, {"Data.sma"})

    def test_launcher_trust_header_pins_exact_bundle_artifacts(self) -> None:
        profile = {
            "retail_exe": {"sha256": addon_runtime.RETAIL_SHA256},
            "addon_plan_sha256": addon_runtime.REFERENCE_PLAN_SHA256,
            "native_patch_manifest_sha256": "1" * 64,
            "native_patch_operations_sha256": addon_runtime.sha256(self.rvp),
            "resource_manifest_sha256": "2" * 64,
            "resource_index_sha256": "3" * 64,
            "reconstructed_reference_file_sha256": addon_runtime.sha256(self.reference_image),
            "resource_count": 243,
        }
        header = build_runtime_launcher._header(profile, self.manifest)
        self.assertIn(b'#define MR_RETAIL_SHA256 "' + addon_runtime.RETAIL_SHA256.encode() + b'"', header)
        self.assertIn(b"#define MR_PATCH_OPERATION_COUNT 246u", header)
        self.assertIn(b"#define MR_RESOURCE_COUNT 243u", header)
        profile["resource_index_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(build_runtime_launcher.LauncherBuildError, "trusted-profile"):
            build_runtime_launcher._header(profile, self.manifest)

    def test_native_launcher_is_separate_from_offline_j0_installable_flag(self) -> None:
        source = (ROOT / "runtime_launcher/src/main.cpp").read_text(encoding="utf-8")
        self.assertIn("CREATE_SUSPENDED", source)
        self.assertIn("ProcessImageBase32", source)
        self.assertIn("TerminateSuspended", source)
        self.assertIn("if (!TerminateProcess", source)
        self.assertIn("wait == WAIT_OBJECT_0", source)
        self.assertIn("--integrated", source)
        self.assertIn("--canary-only", source)
        self.assertFalse(self.manifest.get("runtime_installable", False))


if __name__ == "__main__":
    unittest.main()
