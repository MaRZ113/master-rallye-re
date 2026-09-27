from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from master_rallye.vehicle_config_analysis import (
    VehicleConfigDocument,
    parse_vehicle_config_bytes,
)
from master_rallye.errors import FormatError
from master_rallye.vehicle_family_binder import (
    InstallInventory,
    _choose_output_path,
    _default_output_name,
    discover_binding_manifests,
    load_install_inventory,
    run_interactive_wizard,
    run_restore_menu,
    run_status_view,
)
from master_rallye.vehicle_model_inventory import (
    build_vehicle_family_inventory,
    inventory_vehicle_model_packages,
    select_family_row,
    select_retail_carrier,
)
from master_rallye.vehicle_packaging import (
    index_sma_members,
    normalize_sma_member_name,
    read_sma_member,
)
from master_rallye.vehicle_physics_binding import RETAIL_REQUIRED_BASE_SCHEMA_SHA256
from tools.physics_bind import build_parser


def _doc(families: dict[str, dict[str, dict[str, str]]], source: str) -> VehicleConfigDocument:
    return VehicleConfigDocument(
        build="synthetic",
        source=source,
        sha256=hashlib.sha256(source.encode()).hexdigest(),
        file_size=0,
        families=families,
        excluded_families={},
    )


def _family_row(
    family: str = "Trooper",
    *,
    model_status: str = "COMPLETE",
    provenance: str = "DATA_SMA",
) -> dict:
    return {
        "family": family,
        "identity_kind": "CONFIG_ONLY" if model_status == "MISSING" else "CONFIG_AND_MODEL",
        "type_ids": [],
        "base_config": {
            "status": "COMPLETE", "field_count": 147,
            "expected_field_count": 147, "group_counts": {}, "missing_groups": [],
            "schema_sha256": RETAIL_REQUIRED_BASE_SCHEMA_SHA256,
        },
        "player1_modifications": {
            "status": "COMPLETE", "field_count": 13,
            "expected_field_count": 13, "missing_fields": [],
            "unexpected_fields": [], "wrong_type_fields": [],
        },
        "model": {
            "family_names": [family], "provenance": provenance,
            "status": model_status, "wheelless_by_design": False,
            "required_resources": ["car.dx", "complete.dx", "wheel.dx"],
            "missing_resources": ([] if model_status == "COMPLETE" else ["car.dx"]),
            "ambiguous_resources": [],
            "resources": {
                name: {"source": provenance if model_status == "COMPLETE" else "MISSING",
                       "present": model_status == "COMPLETE"}
                for name in ("car.dx", "complete.dx", "wheel.dx")
            },
            "archive_file_count": 3 if provenance in {"DATA_SMA", "DATA_SMA+LOOSE"} else 0,
            "loose_file_count": 3 if provenance in {"LOOSE_OVERRIDE", "DATA_SMA+LOOSE"} else 0,
        },
    }


def _synthetic_install(root: Path, *, model_status: str = "COMPLETE") -> InstallInventory:
    exe = root / "MRallye.exe"
    exe.write_bytes(b"synthetic executable input")
    xml = b"<Config><Values /></Config>"
    vehicle = parse_vehicle_config_bytes(xml, build="synthetic", source="vehicles.xml")
    modifications = parse_vehicle_config_bytes(xml, build="synthetic", source="Modifications.xml")
    row = _family_row(
        model_status=model_status,
        provenance="MISSING" if model_status == "MISSING" else "DATA_SMA",
    )
    return InstallInventory(
        root=root,
        executable=exe,
        executable_sha256="synthetic-hash",
        data_sma=None,
        archive_members=(),
        vehicles_xml_bytes=xml,
        modifications_xml_bytes=xml,
        vehicle_config=vehicle,
        modifications_config=modifications,
        model_packages={"trooper": row["model"]},
        families=[row],
        config_sources={"vehicles.xml": "test", "Modifications.xml": "test"},
    )


class RPhys31SmaInventoryTests(unittest.TestCase):
    def test_archive_xml_parse_errors_keep_the_member_source(self):
        with self.assertRaisesRegex(FormatError, "Data.sma!DataGame/vehicles.xml"):
            parse_vehicle_config_bytes(
                b'<Config><Value Name="Vehicles//broken" Type="Float" Value="1" /></Config>',
                build="synthetic",
                source="Data.sma!DataGame/vehicles.xml",
            )

    def test_data_sma_member_index_enumerates_without_extraction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "Data.sma"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("DataGx/Vehicles/Trooper/car.dx", b"car")
                archive.writestr("DataGame/vehicles.xml", b"<Config />")
            members = index_sma_members(archive_path)
            self.assertEqual(set(members), {
                "DataGx/Vehicles/Trooper/car.dx", "DataGame/vehicles.xml"
            })
            self.assertFalse((root / "DataGx").exists())
            self.assertEqual(read_sma_member(archive_path, "datagx/vehicles/trooper/CAR.dx"), b"car")

    def test_retail_sma_end_marker_is_indexed_without_rewriting_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "retail.Data.sma"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("DataGx/Vehicles/Test/car.dx", b"car")
                archive.writestr("DataGame/vehicles.xml", b"xml")
            original = archive_path.read_bytes()
            marker = original.rfind(b"PK\x05\x06")
            self.assertGreaterEqual(marker, 0)
            archive_path.write_bytes(original[:marker] + b"SM" + original[marker + 2:])
            before = archive_path.read_bytes()
            names = index_sma_members(archive_path)
            car = read_sma_member(archive_path, "DataGx/Vehicles/Test/car.dx")
            after = archive_path.read_bytes()
        self.assertIn("DataGx/Vehicles/Test/car.dx", names)
        self.assertEqual(car, b"car")
        self.assertEqual(before, after)

    def test_data_sma_index_rejects_unsafe_member_paths(self):
        for name in (
            "../escape", "DataGx/../escape", "DataGx\\Vehicles\\Trooper\\car.dx",
            "C:/outside", "/absolute", "DataGx//empty",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                normalize_sma_member_name(name)

    def test_loose_override_merges_with_archive_and_reports_per_file_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            loose = Path(temporary) / "DataGx" / "Vehicles"
            family = loose / "Trooper"
            family.mkdir(parents=True)
            (family / "Complete.DX").write_bytes(b"loose complete")
            (family / "custom.txt").write_text("loose", encoding="utf-8")
            packages = inventory_vehicle_model_packages(
                (
                    "DataGx/Vehicles/Trooper/car.dx",
                    "DataGx/Vehicles/Trooper/complete.dx",
                    "DataGx/Vehicles/Trooper/wheel.dx",
                ),
                loose,
            )
        model = packages["trooper"]
        self.assertEqual(model["provenance"], "DATA_SMA+LOOSE")
        self.assertEqual(model["status"], "COMPLETE")
        self.assertEqual(model["resources"]["car.dx"]["source"], "DATA_SMA")
        self.assertEqual(model["resources"]["complete.dx"]["source"], "LOOSE_OVERRIDE")
        self.assertEqual(model["resources"]["wheel.dx"]["source"], "DATA_SMA")

    def test_ufo_missing_wheel_is_complete_by_design(self):
        with tempfile.TemporaryDirectory() as temporary:
            packages = inventory_vehicle_model_packages(
                ("DataGx/Vehicles/Ufo/car.dx", "DataGx/Vehicles/Ufo/complete.dx"),
                Path(temporary) / "no-loose-files",
            )
        self.assertEqual(packages["ufo"]["status"], "COMPLETE_WHEELLESS")
        self.assertTrue(packages["ufo"]["wheelless_by_design"])
        self.assertNotIn("wheel.dx", packages["ufo"]["missing_resources"])

    def test_archive_only_and_loose_only_have_distinct_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            loose_root = Path(temporary) / "DataGx" / "Vehicles"
            loose_family = loose_root / "LooseOnly"
            loose_family.mkdir(parents=True)
            for filename in ("car.dx", "complete.dx", "wheel.dx"):
                (loose_family / filename).write_bytes(b"dx")
            packages = inventory_vehicle_model_packages(
                tuple(f"DataGx/Vehicles/ArchiveOnly/{name}" for name in ("car.dx", "complete.dx", "wheel.dx")),
                loose_root,
            )
        self.assertEqual(packages["archiveonly"]["provenance"], "DATA_SMA")
        self.assertEqual(packages["looseonly"]["provenance"], "LOOSE_OVERRIDE")
        self.assertEqual(packages["archiveonly"]["status"], "COMPLETE")
        self.assertEqual(packages["looseonly"]["status"], "COMPLETE")

    def test_model_only_forklift_and_config_only_trooper_are_both_preserved(self):
        vehicle = _doc({"Trooper": {"Dimensions/WheelBase": {"type": "Float", "value": "1"}}}, "vehicles")
        modifications = _doc({}, "mods")
        with tempfile.TemporaryDirectory() as temporary:
            packages = inventory_vehicle_model_packages(
                (
                    "DataGx/Vehicles/forklift/car.dx",
                    "DataGx/Vehicles/forklift/complete.dx",
                    "DataGx/Vehicles/forklift/wheel.dx",
                ),
                Path(temporary) / "loose",
            )
            rows = build_vehicle_family_inventory(vehicle, modifications, packages)
        forklift = next(row for row in rows if row["family"] == "forklift")
        trooper = next(row for row in rows if row["family"] == "Trooper")
        self.assertEqual(forklift["identity_kind"], "MODEL_ONLY")
        self.assertEqual(forklift["base_config"]["status"], "MISSING")
        self.assertEqual(forklift["model"]["status"], "COMPLETE")
        self.assertEqual(trooper["identity_kind"], "CONFIG_ONLY")
        self.assertEqual(trooper["model"]["status"], "MISSING")

    def test_config_names_are_merged_with_model_only_directories(self):
        vehicle = _doc({"Navara": {"Dimensions/WheelBase": {"type": "Float", "value": "1"}}}, "vehicles")
        modifications = _doc({}, "mods")
        with tempfile.TemporaryDirectory() as temporary:
            packages = inventory_vehicle_model_packages(
                ("DataGx/Vehicles/forklift/car.dx",), Path(temporary) / "loose"
            )
            rows = build_vehicle_family_inventory(vehicle, modifications, packages)
        self.assertEqual({row["family"] for row in rows}, {"Navara", "forklift"})

    def test_case_colliding_config_roots_are_both_visible_and_refused(self):
        values = {"Dimensions/WheelBase": {"type": "Float", "value": "1"}}
        vehicle = _doc({"Family": values, "family": values}, "vehicles")
        modifications = _doc({}, "mods")
        rows = build_vehicle_family_inventory(vehicle, modifications, {})
        self.assertEqual([row["family"] for row in rows], ["Family", "family"])
        self.assertTrue(all(row["identity_kind"] == "CONFIG_CASE_COLLISION" for row in rows))
        self.assertTrue(all(row["base_config"]["status"] == "AMBIGUOUS_CASE_COLLISION" for row in rows))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            select_family_row(rows, "FAMILY")


class RPhys31SelectionTests(unittest.TestCase):
    def test_no_command_and_legacy_batch_restore_modes_remain_available(self):
        parser = build_parser()
        self.assertIsNone(parser.parse_args([]).command)
        wizard = parser.parse_args(["--install-root", r"D:\Game\Master Rallye", "--dry-run"])
        self.assertIsNone(wizard.command)
        self.assertTrue(wizard.dry_run)
        restore = parser.parse_args(["restore", "--output-exe", r"D:\Game\Master Rallye\copy.exe"])
        self.assertEqual(restore.command, "restore")
        self.assertEqual(restore.output_exe, Path(r"D:\Game\Master Rallye\copy.exe"))
        menu = parser.parse_args(["restore"])
        self.assertIsNone(menu.output_exe)

    def test_family_selection_accepts_name_and_displayed_ordinal(self):
        rows = [_family_row("Navara"), _family_row("Trooper")]
        self.assertEqual(select_family_row(rows, "Trooper")["family"], "Trooper")
        self.assertEqual(select_family_row(rows, "1")["family"], "Navara")

    def test_invalid_family_and_carrier_selections_are_rejected(self):
        rows = [_family_row("Trooper")]
        for value in ("", "0", "2", "forklift", "unknown"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_family_row(rows, value)
        self.assertEqual(select_retail_carrier("7").family, "Navara")
        self.assertEqual(select_retail_carrier("jump").type_id, 9)
        for value in ("Trooper", "forklift", "25", "-1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_retail_carrier(value)

    def test_config_only_trooper_and_release_family_can_be_selected_as_source(self):
        rows = [_family_row("Navara"), _family_row("Trooper", model_status="MISSING", provenance="MISSING")]
        self.assertEqual(select_family_row(rows, "Trooper")["identity_kind"], "CONFIG_ONLY")
        self.assertEqual(select_family_row(rows, "Navara")["family"], "Navara")

    def test_default_output_name_and_collision_avoidance_support_paths_with_spaces(self):
        self.assertEqual(_default_output_name("Navara", "Trooper"), "MRallye_Navara-to-Trooper.exe")
        self.assertEqual(_default_output_name("Forester", "Forester"), "MRallye_Forester.exe")
        with tempfile.TemporaryDirectory(prefix="MR Install With Spaces ") as temporary:
            root = Path(temporary)
            (root / "MRallye_Navara-to-Trooper.exe").write_bytes(b"existing")
            self.assertEqual(
                _choose_output_path(root, "Navara", "Trooper").name,
                "MRallye_Navara-to-Trooper-2.exe",
            )


class RPhys31WizardTests(unittest.TestCase):
    def test_quoted_windows_install_path_with_spaces_is_accepted(self):
        with tempfile.TemporaryDirectory(prefix="MR Install With Spaces ") as temporary:
            root = Path(temporary)
            (root / "MRallye.exe").write_bytes(b"synthetic")
            inventory = _synthetic_install(root)
            with mock.patch(
                "master_rallye.vehicle_family_binder.load_install_inventory",
                return_value=inventory,
            ), mock.patch(
                "master_rallye.vehicle_family_binder.detect_install_root", return_value=None
            ):
                from master_rallye.vehicle_family_binder import choose_install_root
                chosen = choose_install_root(None, input_fn=lambda _prompt: f'"{root}"', output_fn=lambda _line: None)
            self.assertEqual(chosen, root.resolve())

    def test_wizard_selects_family_before_retail_carrier_and_uses_shared_backend(self):
        with tempfile.TemporaryDirectory(prefix="MR Install With Spaces ") as temporary:
            root = Path(temporary)
            inventory = _synthetic_install(root)
            answers = iter(["Trooper", "7", ""])
            prompts: list[str] = []
            output: list[str] = []

            def input_fn(prompt: str) -> str:
                prompts.append(prompt)
                return next(answers)

            with (
                mock.patch("master_rallye.vehicle_family_binder.load_install_inventory", return_value=inventory),
                mock.patch("master_rallye.vehicle_family_binder._validate_selected_family"),
                mock.patch("master_rallye.vehicle_family_binder.validate_binding_request", return_value={
                    "planned_executable_sha256": "planned-hash"
                }) as validate,
                mock.patch("master_rallye.vehicle_family_binder.apply_binding_copy", return_value={
                    "status": "APPLIED_TO_COPY", "output_exe": str(root / "bound.exe"),
                    "backup": str(root / "bound.exe.original"),
                    "manifest": str(root / "bound.exe.physics-bind.json"),
                }) as apply,
            ):
                status = run_interactive_wizard(
                    root, input_fn=input_fn, output_fn=output.append
                )
        self.assertEqual(status, 0)
        self.assertLess(
            prompts.index("Select vehicle family to activate (number or name): "),
            prompts.index("Carrier type ID or name: "),
        )
        self.assertEqual(validate.call_count, 1)
        self.assertEqual(apply.call_count, 1)
        self.assertEqual(apply.call_args.args[2][0].carrier_type, "Navara")
        self.assertEqual(apply.call_args.args[2][0].physics_family, "Trooper")
        self.assertTrue(any("both model/resource lookup" in line for line in output))

    def test_no_final_confirmation_means_no_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory = _synthetic_install(root)
            answers = iter(["Trooper", "7", "n"])
            with (
                mock.patch("master_rallye.vehicle_family_binder.load_install_inventory", return_value=inventory),
                mock.patch("master_rallye.vehicle_family_binder._validate_selected_family"),
                mock.patch("master_rallye.vehicle_family_binder.validate_binding_request", return_value={
                    "planned_executable_sha256": "planned-hash"
                }),
                mock.patch("master_rallye.vehicle_family_binder.apply_binding_copy") as apply,
            ):
                status = run_interactive_wizard(root, input_fn=lambda _prompt: next(answers), output_fn=lambda _line: None)
        self.assertEqual(status, 0)
        apply.assert_not_called()

    def test_missing_model_package_refuses_before_carrier_selection_without_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory = _synthetic_install(root, model_status="MISSING")
            answers = iter(["Trooper", ""])
            output: list[str] = []
            prompts: list[str] = []

            def input_fn(prompt: str) -> str:
                prompts.append(prompt)
                return next(answers)

            with (
                mock.patch("master_rallye.vehicle_family_binder.load_install_inventory", return_value=inventory),
                mock.patch("master_rallye.vehicle_family_binder._validate_selected_family"),
                mock.patch("master_rallye.vehicle_family_binder.validate_binding_request") as validate,
            ):
                status = run_interactive_wizard(root, input_fn=input_fn, output_fn=output.append)
        self.assertEqual(status, 2)
        self.assertTrue(any("no model package was found" in line for line in output), output)
        self.assertTrue(any("ALLOW MISSING MODEL" in prompt for prompt in prompts))
        validate.assert_not_called()

    def test_explicit_advanced_missing_model_override_is_required_and_previewable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory = _synthetic_install(root, model_status="MISSING")
            answers = iter(["Trooper", "ALLOW MISSING MODEL", "7"])
            output: list[str] = []
            prompts: list[str] = []

            def input_fn(prompt: str) -> str:
                prompts.append(prompt)
                return next(answers)

            with (
                mock.patch("master_rallye.vehicle_family_binder.load_install_inventory", return_value=inventory),
                mock.patch("master_rallye.vehicle_family_binder._validate_selected_family"),
                mock.patch("master_rallye.vehicle_family_binder.validate_binding_request", return_value={
                    "planned_executable_sha256": "planned-hash"
                }) as validate,
            ):
                status = run_interactive_wizard(
                    root, dry_run=True, input_fn=input_fn, output_fn=output.append
                )
        self.assertEqual(status, 0)
        self.assertEqual(validate.call_count, 1)
        self.assertTrue(any("ALLOW MISSING MODEL" in prompt for prompt in prompts))


class RPhys31RestoreDiscoveryTests(unittest.TestCase):
    def test_restore_manifest_discovery_checks_artifacts_and_reads_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "MRallye_Navara-to-Trooper.exe"
            backup = output.with_name(output.name + ".original")
            manifest = output.with_name(output.name + ".physics-bind.json")
            output.write_bytes(b"patched")
            backup.write_bytes(b"retail")
            manifest.write_text(json.dumps({
                "build": "retail-2001-verified", "status": "applied",
                "source_sha256": "retail-hash", "patched_sha256": "patched-hash",
                "output_exe_name": output.name, "backup_name": backup.name,
                "bindings": [{"carrier_type": "Navara", "physics_family": "Trooper"}],
            }), encoding="utf-8")
            def fake_sha(data: bytes):
                value = b"retail-hash" if data == b"retail" else b"patched-hash"
                return SimpleNamespace(hexdigest=lambda: value.decode())
            with mock.patch("master_rallye.vehicle_family_binder.hashlib.sha256", side_effect=fake_sha), \
                 mock.patch("master_rallye.vehicle_family_binder.RETAIL_EXE_SHA256", "retail-hash"):
                rows = discover_binding_manifests(root)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["valid"])
        self.assertEqual(rows[0]["status"], "applied")
        self.assertEqual(rows[0]["bindings"][0]["physics_family"], "Trooper")

    def test_restore_menu_requires_selection_and_confirmation_then_calls_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "MRallye.exe").write_bytes(b"synthetic")
            fake_entry = {
                "manifest": root / "copy.physics-bind.json",
                "output_exe": root / "copy.exe",
                "backup": root / "copy.exe.original",
                "manifest_data": {}, "valid": True, "status": "applied",
                "bindings": [{"carrier_type": "Navara", "physics_family": "Trooper"}],
            }
            answers = iter(["1", "y"])
            with (
                mock.patch("master_rallye.vehicle_family_binder.discover_binding_manifests", return_value=[fake_entry]),
                mock.patch("master_rallye.vehicle_family_binder.restore_binding_copy", return_value={
                    "status": "RESTORED_COPY", "output_exe": str(fake_entry["output_exe"])
                }) as restore,
            ):
                status = run_restore_menu(root, input_fn=lambda _prompt: next(answers), output_fn=lambda _line: None)
        self.assertEqual(status, 0)
        restore.assert_called_once_with(fake_entry["output_exe"])

    def test_status_view_shows_binding_model_source_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory = _synthetic_install(root)
            fake_entry = {
                "manifest": root / "copy.physics-bind.json",
                "output_exe": root / "copy.exe",
                "backup": root / "copy.exe.original",
                "manifest_data": {"patched_sha256": "patched-hash"},
                "valid": True, "status": "applied",
                "bindings": [{"carrier_type": "Navara", "physics_family": "Trooper"}],
            }
            output: list[str] = []
            with (
                mock.patch("master_rallye.vehicle_family_binder.load_install_inventory", return_value=inventory),
                mock.patch("master_rallye.vehicle_family_binder.discover_binding_manifests", return_value=[fake_entry]),
            ):
                status = run_status_view(root, output_fn=output.append)
        self.assertEqual(status, 0)
        self.assertTrue(any("type 7 Navara -> Trooper" in line for line in output))
        self.assertTrue(any("COMPLETE / Data.sma" in line for line in output))
        self.assertTrue(any("patched-hash" in line for line in output))


RETAIL_CORPUS = Path(r"D:\Game\Master Rallye\corpora\retail")
RETAIL_CORPUS_INPUTS_AVAILABLE = (
    (RETAIL_CORPUS / "MRallye.exe").is_file()
    and (RETAIL_CORPUS / "Data.sma").is_file()
)


@unittest.skipUnless(RETAIL_CORPUS_INPUTS_AVAILABLE, "requires the read-only retail corpus")
class RPhys31RetailCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = load_install_inventory(RETAIL_CORPUS)
        cls.rows = {row["family"].casefold(): row for row in cls.inventory.families}

    def test_trooper_required_config_is_complete_but_retail_model_is_config_only(self):
        trooper = self.rows["trooper"]
        self.assertEqual(trooper["base_config"]["status"], "COMPLETE")
        self.assertEqual(trooper["base_config"]["field_count"], 147)
        self.assertEqual(trooper["player1_modifications"]["status"], "COMPLETE")
        self.assertEqual(trooper["player1_modifications"]["field_count"], 13)
        self.assertEqual(trooper["identity_kind"], "CONFIG_ONLY")
        self.assertEqual(trooper["model"]["status"], "MISSING")
        self.assertEqual(trooper["base_config"]["schema_sha256"], RETAIL_REQUIRED_BASE_SCHEMA_SHA256)

    def test_retail_forklift_is_model_only_and_ufo_is_wheel_less(self):
        forklift = self.rows["forklift"]
        self.assertEqual(forklift["identity_kind"], "MODEL_ONLY")
        self.assertEqual(forklift["base_config"]["status"], "MISSING")
        self.assertEqual(forklift["model"]["status"], "COMPLETE")
        ufo = self.rows["ufo"]
        self.assertEqual(ufo["model"]["status"], "COMPLETE_WHEELLESS")
        self.assertTrue(ufo["model"]["wheelless_by_design"])

    def test_retail_inventory_keeps_release_and_config_only_identity_separate(self):
        self.assertEqual(self.rows["navara"]["type_ids"], [7])
        self.assertEqual(self.rows["trooper"]["type_ids"], [])
        self.assertTrue(self.rows["trooper"]["base_config"]["status"] == "COMPLETE")


if __name__ == "__main__":
    unittest.main()
