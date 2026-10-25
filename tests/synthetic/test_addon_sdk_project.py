from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_library import footer56, simple_record, synthetic_dx
from master_rallye.addon_sdk import (
    AddonValidationError, build_project, initialize_project, validate_project, verify_build,
)
from tools.mrtool import _author_facing_diagnostic, build_parser


CAPABILITIES = ROOT / "research/vehicles/sdk/capabilities/retail-2001.json"


def _dx_fixture() -> bytes:
    positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    record = simple_record(0, 2, 0, 3, ("Null",))
    return synthetic_dx(positions, [0, 1, 2], [record], [(0, 0, 3)], trailing=footer56(positions))


def _data_game_fixture() -> tuple[bytes, bytes]:
    vehicles = (
        b'<?xml version="1.0" encoding="utf-8"?>\r\n'
        b'<Broker>\r\n'
        b'  <Value Name="Vehicles/Navara/Engine" Type="Float" Value="1"/>\r\n'
        b'  <Value Name="Vehicles/Landcruiser/Engine" Type="Float" Value="2"/>\r\n'
        b'</Broker>\r\n'
    )
    modifications = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<Broker>\n'
        b'  <Value Name="Vehicles/Navara/Suspension" Type="Float" Value="3"/>\n'
        b'</Broker>\n'
    )
    return vehicles, modifications


class AddonSdkProjectTests(unittest.TestCase):
    def test_project_cli_uses_public_name_option_and_actionable_machine_diagnostic(self) -> None:
        args = build_parser().parse_args([
            "addon", "init", "--name", "My Rally Car", "--class", "T2",
            "--donor", "Navara", "--output", "MyRallyCar",
        ])
        self.assertEqual((args.addon_command, args.name, args.vehicle_class),
                         ("init", "My Rally Car", "T2"))
        diagnostic = _author_facing_diagnostic(ValueError("T2 class-local capacity exceeded"))
        self.assertEqual(diagnostic["code"], "ADDON_CLASS_SLOT_UNAVAILABLE")
        self.assertEqual(diagnostic["field"], "/vehicle_class")
        self.assertIn("ID26/T1 and ID27/T2", diagnostic["suggested_action"])

    def test_asset_free_example_project_matches_independent_manifest(self) -> None:
        example = ROOT / "research/vehicles/sdk/examples/glacier-sprint-t2-project"
        manifest = json.loads((example / "addon.json").read_text(encoding="utf-8"))
        standalone = json.loads((ROOT / "research/vehicles/sdk/examples/glacier-sprint-t2.json")
                               .read_text(encoding="utf-8"))
        self.assertEqual(manifest, standalone)
        vehicle_project = json.loads((example / "vehicle-project.json").read_text(encoding="utf-8"))
        self.assertEqual(vehicle_project["source_vehicle_dir"], "assets/source/Navara")
        self.assertFalse((example / "assets").exists())

    def test_generated_physics_overlays_are_exact_donor_clones_and_verifiable(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            root = Path(temporary)
            vehicles, modifications = _data_game_fixture()
            data_sma = root / "Data.sma"
            with zipfile.ZipFile(data_sma, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("DataGame/vehicles.xml", vehicles)
                archive.writestr("DataGame/Modifications.xml", modifications)
            data_root = root / "unpacked"
            (data_root / "DataGame").mkdir(parents=True)
            (data_root / "DataGame/vehicles.xml").write_bytes(vehicles)
            (data_root / "DataGame/Modifications.xml").write_bytes(modifications)

            capabilities = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
            archive_bytes = data_sma.read_bytes()
            capabilities["retail_data_sma_sha256"] = hashlib.sha256(archive_bytes).hexdigest()
            capabilities["retail_data_sma_size"] = len(archive_bytes)
            capabilities_path = root / "capabilities.json"
            capabilities_path.write_text(json.dumps(capabilities), encoding="utf-8")

            project = root / "glacier-project"
            initialize_project(name="Glacier Sprint", vehicle_class="T2", donor="Navara",
                               family="GlacierSprint", output=project)
            donor = project / "assets/source/Navara"
            for role in ("car.dx", "complete.dx", "wheel.dx"):
                (donor / role).write_bytes(_dx_fixture())

            validation = validate_project(project, capabilities_path,
                                           retail_data_sma=data_sma, retail_data_root=data_root)
            self.assertEqual(validation["status"], "PASS", validation)
            self.assertTrue(validation["physics_family_resources"]["runtime_overlay_ready"])
            self.assertFalse(validation["runtime_installable"])

            output = root / "build"
            build_project(project, capabilities_path, output,
                          retail_data_sma=data_sma, retail_data_root=data_root)
            self.assertEqual(verify_build(output)["status"], "PASS")
            generated_vehicles = (output / "DataGame/vehicles.xml").read_bytes()
            generated_modifications = (output / "DataGame/Modifications.xml").read_bytes()
            self.assertIn(b'Name="Vehicles/GlacierSprint/Engine"', generated_vehicles)
            self.assertIn(b'Name="Vehicles/GlacierSprint/Suspension"', generated_modifications)
            self.assertEqual(generated_vehicles.count(b'Name="Vehicles/Navara/'), 1)
            self.assertEqual(generated_modifications.count(b'Name="Vehicles/Navara/'), 1)
            inventory = json.loads((output / "resource-inventory.json").read_text(encoding="utf-8"))
            generated_rows = [row for row in inventory["resources"]
                              if row.get("status") == "GENERATED_AND_HASHED"]
            self.assertEqual({row["path"] for row in generated_rows},
                             {"DataGame/vehicles.xml", "DataGame/Modifications.xml"})

    def test_wrong_archive_and_unpaired_retail_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            root = Path(temporary)
            vehicles, modifications = _data_game_fixture()
            data_sma = root / "Data.sma"
            with zipfile.ZipFile(data_sma, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("DataGame/vehicles.xml", vehicles)
                archive.writestr("DataGame/Modifications.xml", modifications)
            data_root = root / "unpacked"
            (data_root / "DataGame").mkdir(parents=True)
            (data_root / "DataGame/vehicles.xml").write_bytes(vehicles)
            (data_root / "DataGame/Modifications.xml").write_bytes(modifications)
            project = root / "project"
            initialize_project(name="Glacier Sprint", vehicle_class="T2", donor="Navara",
                               family="GlacierSprint", output=project)
            donor = project / "assets/source/Navara"
            for role in ("car.dx", "complete.dx", "wheel.dx"):
                (donor / role).write_bytes(_dx_fixture())
            with self.assertRaisesRegex(AddonValidationError, "must be supplied together"):
                validate_project(project, CAPABILITIES, retail_data_sma=data_sma)
            with self.assertRaisesRegex(AddonValidationError, "does not match"):
                build_project(project, CAPABILITIES, root / "out",
                              retail_data_sma=data_sma, retail_data_root=data_root)

    def test_physics_clone_rejects_non_native_xml_shapes_and_target_collisions(self) -> None:
        from master_rallye.addon_sdk.physics import clone_vehicle_family_xml

        with self.assertRaisesRegex(AddonValidationError, "self-closing Value format"):
            clone_vehicle_family_xml(
                b'<Broker>\n<Value Name="Vehicles/Navara/Engine"></Value>\n</Broker>',
                donor_family="Navara", runtime_family="GlacierSprint", source_label="fixture")
        with self.assertRaisesRegex(AddonValidationError, "already contains target family"):
            clone_vehicle_family_xml(
                b'<Broker>\n<Value Name="Vehicles/Navara/Engine"/>\n'
                b'<Value Name="Vehicles/GlacierSprint/Engine"/>\n</Broker>',
                donor_family="Navara", runtime_family="GlacierSprint", source_label="fixture")


if __name__ == "__main__":
    unittest.main()
