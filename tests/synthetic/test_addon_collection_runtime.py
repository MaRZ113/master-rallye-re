from __future__ import annotations

import json
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import addon_collection_runtime as collection
import addon_runtime
import j2_frontend_reentry as reentry
from master_rallye.addon_sdk.compiler import build_artifacts
from master_rallye.addon_sdk.manifest import load_capabilities, load_manifests


class AddonCollectionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        examples = ROOT / "research/vehicles/sdk/examples"
        cls.mercedes = examples / "mercedes-ml320.json"
        cls.glacier = examples / "glacier-sprint-t2.json"
        cls.capabilities = ROOT / "research/vehicles/sdk/capabilities/retail-2001.json"

    def _plan(self, paths: list[Path]) -> dict:
        manifests, _ = load_manifests(paths)
        capabilities, _ = load_capabilities(self.capabilities)
        return json.loads(build_artifacts(manifests, capabilities)["addon-plan.json"])

    def test_collection_resolves_only_the_qualified_sparse_pair(self) -> None:
        plan = self._plan([self.mercedes, self.glacier])
        row26, row27 = collection._assert_exact_stock_pair(plan, self.capabilities)
        self.assertEqual((row26["physical_id"], row26["vehicle_class"], row26["class_local_index"]), (26, "T1", 7))
        self.assertEqual((row27["physical_id"], row27["vehicle_class"], row27["class_local_index"]), (27, "T2", 7))
        self.assertEqual(row27["identity"]["runtime_family"], "GlacierSprint")
        self.assertEqual(row27["identity"]["physics_family"], "Vehicles/GlacierSprint")

    def test_t2_only_collection_fails_instead_of_injecting_mercedes(self) -> None:
        plan = self._plan([self.glacier])
        with self.assertRaisesRegex(collection.CollectionRuntimeError, "ID27-only is blocked"):
            collection._assert_exact_stock_pair(plan, self.capabilities)
        self.assertEqual([row["physical_id"] for row in plan["addons"]], [27])

    def test_t1_only_collection_is_not_misreported_as_a_runtime_bundle(self) -> None:
        plan = self._plan([self.mercedes])
        with self.assertRaisesRegex(collection.CollectionRuntimeError,
                                    "requires exactly ID26/T1 and ID27/T2"):
            collection._assert_exact_stock_pair(plan, self.capabilities)
        self.assertEqual([row["physical_id"] for row in plan["addons"]], [26])

    def test_custom_native_identity_comes_from_manifest_without_stale_reference_family(self) -> None:
        plan = self._plan([self.mercedes, self.glacier])
        row27 = next(row for row in plan["addons"] if row["physical_id"] == 27)
        record = collection._record_for_id27(row27, "test-profile")
        native_identity = collection.runtime_family_bytes(row27)
        self.assertEqual(record.internal_name, "GlacierSprint")
        self.assertIn(b"GlacierSprint", native_identity)
        self.assertNotIn(b"R5VQualifier", native_identity)

    def test_manifest_marker_bytes_are_written_to_physical_id27_record(self) -> None:
        plan = self._plan([self.mercedes, self.glacier])
        row27 = next(row for row in plan["addons"] if row["physical_id"] == 27)
        record = collection._record_for_id27(row27, "test-profile")
        self.assertEqual((record.slot_id, record.vehicle_class, record.local_index), (27, 1, 7))
        self.assertEqual(record.internal_name, "GlacierSprint")
        self.assertEqual(record.race_colour_rgba_bits,
                         struct.unpack("<4I", bytes.fromhex(row27["race_colour_rgba_f32le_hex"])))
        self.assertEqual(record.race_colour_rgba_bits,
                         tuple(struct.unpack("<I", struct.pack("<f", value))[0]
                               for value in (0.1, 0.75, 0.35, 1.0)))

    def test_physics_composition_replaces_only_id27_family_and_preserves_mercedes(self) -> None:
        source = (
            b'<Broker>\n'
            b'<Value Name="Vehicles/Navara/Engine" Value="donor" />\n'
            b'<Value Name="Vehicles/R5VQualifier/Engine" Value="donor" />\n'
            b'<Value Name="Vehicles/Mercedes/Engine" Value="stock-addon" />\n'
            b'</Broker>\n'
        )
        result, report = collection._compose_family_xml(
            source, base_family="R5VQualifier", addon_family="GlacierSprint",
            donor_family="Navara", expected_project_data=None,
            source_label="DataGame/vehicles.xml")
        values = collection._family_value_map(result, "GlacierSprint", "test output")
        self.assertEqual(values, {"Vehicles/GlacierSprint/Engine":
                                  {"Name": "Vehicles/GlacierSprint/Engine", "Value": "donor"}})
        self.assertFalse(collection._family_value_map(result, "R5VQualifier", "test output"))
        self.assertEqual(collection._family_value_map(result, "Mercedes", "test output"),
                         {"Vehicles/Mercedes/Engine":
                          {"Name": "Vehicles/Mercedes/Engine", "Value": "stock-addon"}})
        self.assertTrue(report["id26_mercedes_rows_preserved"])

    def test_vehicle_select_generator_changes_only_id27_art_and_keeps_lock_control(self) -> None:
        scene = b'''<Scene>
  <Egg Name="Existing"><Value Name="en2d Image Bank Index" Value="23" /></Egg>
  <Egg Name="Other"><Value Name="en2d Image Bank Index" Value="5" /></Egg>
  <Egg Name="T2_Car8">
    <Value Name="en2d Image Bank Index" Value="23" />
    <Value Name="True Value" Value="23" />
    <AI_List>
      <AI No="0">
        <Value Name="AI Name" Value="gaFrontendDisablerAI" />
        <gaFrontendDisablerAI>
          <Value Name="False Value" Value="15" />
          <Value Name="Broker Value1*" Value="Progress/UnlockedCars/T2CupCar1" />
        </gaFrontendDisablerAI>
      </AI>
      <AI No="2">
        <Value Name="AI Name" Value="gaFrontendXYButtonAI" />
        <gaFrontendXYButtonAI>
          <Value Name="X ID" Value="7" />
          <Value Name="Y ID" Value="1" />
          <Value Name="XPos*" Value="Frontend/VehicleSelect/Button7XPos" />
        </gaFrontendXYButtonAI>
      </AI>
    </AI_List>
  </Egg>
</Scene>
'''
        result, report = collection._build_scene(scene, frame=5)
        expected = scene.replace(
            b'<Value Name="en2d Image Bank Index" Value="23" />\n    <Value Name="True Value" Value="23" />',
            b'<Value Name="en2d Image Bank Index" Value="5" />\n    <Value Name="True Value" Value="5" />',
        )
        self.assertEqual(result, expected)
        root = collection.vehicle_select.g1._parse_xml(result.decode("utf-8"))
        slot = next(egg for egg in root.iter("Egg") if egg.get("Name") == "T2_Car8")
        self.assertEqual(collection.vehicle_select.g1._direct_value(slot, "en2d Image Bank Index").get("Value"), "5")
        self.assertEqual(collection.vehicle_select.g1._direct_value(slot, "True Value").get("Value"), "5")
        _node, disabler = collection.vehicle_select.g1._ai_node(slot, "0", "gaFrontendDisablerAI")
        self.assertEqual(collection.vehicle_select.g1._body_values(disabler)["False Value"], "15")
        self.assertEqual(collection.vehicle_select.g1._body_values(disabler)["Broker Value1*"],
                         "Progress/UnlockedCars/T2CupCar1")
        self.assertEqual(report["physical_id"], 27)
        self.assertTrue(report["stock_slot_and_unlock_controls_preserved"])

    def test_reentry_cave_selection_is_deterministic_and_keeps_stub_abi(self) -> None:
        image = bytes(0x300000)
        sections = [{"name": ".text", "rva": 0, "raw_size": len(image), "raw_offset": 0}]
        with mock.patch.object(addon_runtime, "_pe_sections", return_value=({}, sections)):
            preferred = reentry._find_republish_stub_va(image, image, [])
            self.assertEqual(preferred, reentry.STUB_VA)
            self.assertEqual(reentry.verify_republish_stub(
                reentry.make_republish_stub(stub_va=preferred), stub_va=preferred)["status"],
                "PASS_SYMBOLIC_STUB_ABI")

            occupied_offset = reentry.STUB_VA - reentry.IMAGE_BASE
            row = {"file_offset": occupied_offset, "rva": occupied_offset,
                   "length": len(reentry.make_republish_stub()), "flags": reentry.FLAG_PROCESS}
            relocated = reentry._find_republish_stub_va(image, image, [row])
            self.assertNotEqual(relocated, reentry.STUB_VA)
            self.assertEqual(relocated & ~0xFFF, reentry.STUB_VA & ~0xFFF)
            self.assertEqual(reentry.verify_republish_stub(
                reentry.make_republish_stub(stub_va=relocated), stub_va=relocated)["status"],
                "PASS_SYMBOLIC_STUB_ABI")

            page_start_rva = (reentry.STUB_VA & ~0xFFF) - reentry.IMAGE_BASE
            full_page = {"file_offset": page_start_rva, "rva": page_start_rva,
                         "length": 0x1000, "flags": reentry.FLAG_PROCESS}
            with self.assertRaisesRegex(reentry.ReentryBundleError, "no zero-filled"):
                reentry._find_republish_stub_va(image, image, [full_page])

    def test_mrtool_exposes_separate_runtime_compiler_commands(self) -> None:
        import mrtool

        for subcommand in ("runtime-prepare", "runtime-verify", "runtime-launcher-build"):
            with self.subTest(subcommand=subcommand):
                parsed = mrtool.build_parser().parse_args([
                    "addon", subcommand,
                    "--manifest", str(self.mercedes),
                    "--manifest", str(self.glacier),
                ] + (["bundle"] if subcommand != "runtime-prepare" else ["--output", "bundle"]) +
                    (["--launcher-output", "launcher"] if subcommand == "runtime-launcher-build" else []))
                self.assertEqual(parsed.addon_command, subcommand)


if __name__ == "__main__":
    unittest.main()
