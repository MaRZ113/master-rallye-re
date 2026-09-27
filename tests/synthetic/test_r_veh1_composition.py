from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from master_rallye.vehicle_composition import (
    VehicleComposition,
    apply_vehicle_composition,
    build_vehicle_composition_plan,
    choose_composition_manifest_path,
    discover_vehicle_composition_manifests,
    resolve_effective_model_package,
    restore_vehicle_composition,
)
from master_rallye.vehicle_config_analysis import parse_vehicle_config
from master_rallye.vehicle_family_broker import PLAYER_MODIFICATION_FIELDS
from master_rallye.vehicle_model_inventory import (
    available_model_donors,
    build_vehicle_family_inventory,
    inventory_vehicle_model_packages,
    select_family_row,
    select_model_donor,
)
from master_rallye.vehicle_packaging import index_sma_members
from master_rallye.vehicle_physics_binding import (
    PhysicsBinding,
    RETAIL_FAMILY_CATALOG,
    parse_binding_config_text,
)
from tests.synthetic.test_library import simple_record, synthetic_dx
from tests.synthetic.test_r_phys3_family_binding import TEST_CATALOG, make_synthetic_pe32
from tools.physics_bind import main as physics_bind_main


def _synthetic_dx(texture: str = "body-tga") -> bytes:
    points = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)]
    return synthetic_dx(
        points,
        [0, 1, 2],
        [simple_record(0, 2, 0, 3, (texture, "Null"))],
        [(0, 0, 3)],
    )


def _write_configs(root: Path, families: tuple[str, ...]) -> tuple[Path, Path]:
    from master_rallye.vehicle_config_schema import RETAIL_REQUIRED_FIXED_SCHEMA

    base_rows = []
    mod_rows = []
    for family in families:
        fields = dict(RETAIL_REQUIRED_FIXED_SCHEMA)
        for path, value_type in fields.items():
            value = "7" if path == "Engine/Gears" else "6" if path == "Engine/TorqueEntries" else "1"
            base_rows.append(
                f'<Value Name="Vehicles/{family}/{path}" Type="{value_type}" Value="{value}" />'
            )
        for prefix in ("Gear", "ChangeUpRevs", "ChangeDownRevs"):
            for index in range(7):
                base_rows.append(
                    f'<Value Name="Vehicles/{family}/Engine/{prefix}{index}" Type="Float" Value="1" />'
                )
        for index in range(6):
            base_rows.append(
                f'<Value Name="Vehicles/{family}/Engine/TorqueEntry{index}" Type="Vector2" Value="0,0" />'
            )
        for field in PLAYER_MODIFICATION_FIELDS:
            mod_rows.append(
                f'<Value Name="Vehicles/{family}/Player1/Modifications/{field}" '
                'Type="Float" Value="1" />'
            )
    vehicles = root / "vehicles.xml"
    modifications = root / "Modifications.xml"
    vehicles.write_text("<Config><Values>" + "".join(base_rows) + "</Values></Config>", encoding="utf-8")
    modifications.write_text(
        "<Config><Values>" + "".join(mod_rows) + "</Values></Config>", encoding="utf-8"
    )
    return vehicles, modifications


class RVeh1Fixture:
    def __init__(self, root: Path, *, include_ufo: bool = True):
        self.root = root.resolve()
        self.exe = self.root / "MRallye.exe"
        self.exe_bytes = make_synthetic_pe32()
        self.exe.write_bytes(self.exe_bytes)
        self.exe_sha256 = hashlib.sha256(self.exe_bytes).hexdigest()
        self.sma = self.root / "Data.sma"
        self.loose_root = self.root / "DataGx" / "Vehicles"
        self.loose_root.mkdir(parents=True)
        dx = _synthetic_dx()
        families = {
            "Carrier": {
                "car.dx": dx,
                "complete.dx": dx,
                "wheel.dx": dx,
                "body-tga.dxt": b"carrier texture",
                "nested/extra.bin": b"carrier extra",
                "destination-only.dxt": b"unreferenced archive fallback",
            },
            "LongTargetFamily": {
                "car.dx": dx,
                "complete.dx": dx,
                "wheel.dx": dx,
                "body-tga.dxt": b"target texture",
                "target-only.dxt": b"unreferenced target texture",
            },
            "Donor": {
                "car.dx": dx,
                "complete.dx": dx,
                "wheel.dx": dx,
                "body-tga.dxt": b"donor texture",
                "nested/extra.bin": b"donor extra",
                "donor.txt": b"sidecar",
            },
            "forklift": {
                "car.dx": dx,
                "complete.dx": dx,
                "wheel.dx": dx,
                "body-tga.dxt": b"forklift texture",
                "nested/fork.bin": b"forklift aux",
            },
        }
        if include_ufo:
            families["Ufo"] = {
                "car.dx": dx,
                "complete.dx": dx,
                "body-tga.dxt": b"ufo texture",
            }
        with zipfile.ZipFile(self.sma, "w") as archive:
            for family, files in families.items():
                for relative, data in files.items():
                    archive.writestr(f"DataGx/Vehicles/{family}/{relative}", data)
        self.archive_members = index_sma_members(self.sma)
        self.vehicles_xml, self.modifications_xml = _write_configs(
            self.root, ("Carrier", "LongTargetFamily")
        )
        self.vehicle_config = parse_vehicle_config(self.vehicles_xml, build="synthetic")
        self.modifications_config = parse_vehicle_config(self.modifications_xml, build="synthetic")
        self.model_packages = inventory_vehicle_model_packages(
            self.archive_members, self.loose_root
        )

    def plan(
        self,
        carrier: str,
        physics: str,
        donor: str,
        *,
        output: Path | None = None,
        catalog=TEST_CATALOG,
        allow_incomplete_model: bool = False,
    ):
        composition = VehicleComposition(carrier, physics, donor)
        return build_vehicle_composition_plan(
            self.exe,
            self.root,
            composition,
            self.vehicle_config,
            self.modifications_config,
            self.sma,
            self.archive_members,
            self.loose_root,
            model_packages=self.model_packages,
            allow_incomplete_model=allow_incomplete_model,
            output_exe=output,
            expected_exe_sha256=self.exe_sha256,
            catalog=catalog,
        )


class RVeh1IdentityAndConfigTests(unittest.TestCase):
    def test_schema_v1_defaults_model_donor_to_physics_and_v2_is_explicit(self):
        legacy = parse_binding_config_text(
            '{"schema_version":1,"bindings":[{"carrier_type":"Navara",'
            '"physics_family":"Trooper"}]}'
        )[0]
        self.assertIsNone(legacy.model_donor)
        self.assertEqual(legacy.effective_model_donor, "Trooper")
        explicit = parse_binding_config_text(
            '{"schema_version":2,"bindings":[{"carrier_type":"Navara",'
            '"physics_family":"Trooper","model_donor":"forklift"}]}'
        )[0]
        self.assertEqual(explicit, PhysicsBinding("Navara", "Trooper", "forklift"))
        with self.assertRaisesRegex(ValueError, "model_donor"):
            parse_binding_config_text(
                '{"schema_version":2,"bindings":[{"carrier_type":"Navara",'
                '"physics_family":"Trooper"}]}'
            )

    def test_forklift_is_an_independent_model_donor_without_physics_family(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            donor = select_model_donor(fixture.model_packages, "forklift")
            self.assertEqual(donor["family"], "forklift")
            self.assertEqual(donor["model"]["status"], "COMPLETE")
            rows = build_vehicle_family_inventory(
                fixture.vehicle_config, fixture.modifications_config, fixture.model_packages
            )
            forklift = select_family_row(rows, "forklift")
            self.assertEqual(forklift["identity_kind"], "MODEL_ONLY")
            self.assertEqual(forklift["base_config"]["status"], "MISSING")
            with self.assertRaisesRegex(ValueError, "absent from vehicles.xml"):
                fixture.plan("Carrier", "forklift", "forklift", output=fixture.root / "bound.exe")

    def test_model_donor_list_includes_all_installed_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            names = {row["family"].casefold() for row in available_model_donors(fixture.model_packages)}
            self.assertEqual(names, {"carrier", "longtargetfamily", "donor", "forklift", "ufo"})

    def test_ufo_is_complete_without_a_wheel_resource(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            ufo = fixture.model_packages["ufo"]
            self.assertEqual(ufo["status"], "COMPLETE_WHEELLESS")
            package = resolve_effective_model_package(
                fixture.sma, fixture.archive_members, fixture.loose_root, "Ufo",
                model_packages=fixture.model_packages,
            )
            self.assertNotIn("wheel.dx", package["files"])


class RVeh1ModelPackageTests(unittest.TestCase):
    def test_data_sma_loose_merge_is_filewise_and_preserves_source_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            donor_dir = fixture.loose_root / "Donor"
            donor_dir.mkdir()
            (donor_dir / "body-tga.dxt").write_bytes(b"loose override")
            (donor_dir / "nested").mkdir()
            (donor_dir / "nested" / "loose-only.bin").write_bytes(b"loose-only")
            packages = inventory_vehicle_model_packages(fixture.archive_members, fixture.loose_root)
            package = resolve_effective_model_package(
                fixture.sma, fixture.archive_members, fixture.loose_root, "Donor",
                model_packages=packages,
            )
            self.assertEqual(package["provenance"], "DATA_SMA+LOOSE")
            self.assertEqual(package["files"]["body-tga.dxt"]["data"], b"loose override")
            self.assertEqual(package["files"]["body-tga.dxt"]["source_provenance"], "LOOSE_OVERRIDE")
            self.assertEqual(package["files"]["car.dx"]["source_provenance"], "DATA_SMA")
            self.assertIn("nested/extra.bin", package["files"])
            self.assertIn("nested/loose-only.bin", package["files"])

    def test_loose_only_model_donor_is_materializable(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            loose_only = fixture.loose_root / "LooseOnly"
            loose_only.mkdir()
            for name, data in (
                ("car.dx", _synthetic_dx()),
                ("complete.dx", _synthetic_dx()),
                ("wheel.dx", _synthetic_dx()),
                ("body-tga.dxt", b"texture"),
            ):
                (loose_only / name).write_bytes(data)
            packages = inventory_vehicle_model_packages(fixture.archive_members, fixture.loose_root)
            resolved = resolve_effective_model_package(
                fixture.sma, fixture.archive_members, fixture.loose_root, "LooseOnly",
                model_packages=packages,
            )
            self.assertEqual(resolved["provenance"], "LOOSE_OVERRIDE")
            self.assertTrue(all(row["source_provenance"] == "LOOSE_OVERRIDE" for row in resolved["files"].values()))

    def test_case_colliding_nested_paths_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            donor = fixture.loose_root / "Donor"
            donor.mkdir()
            (donor / "car.dx").write_bytes(_synthetic_dx())
            packages = inventory_vehicle_model_packages(
                fixture.archive_members + ("DataGx/Vehicles/Donor/CAR.DX",),
                fixture.loose_root,
            )
            self.assertEqual(packages["donor"]["status"], "AMBIGUOUS_CASE_COLLISION")
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                resolve_effective_model_package(
                    fixture.sma, fixture.archive_members, fixture.loose_root, "Donor",
                    model_packages=packages,
                )


class RVeh1CompositionPlanTests(unittest.TestCase):
    def test_full_family_regression_uses_natural_package_without_overlay(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            plan = fixture.plan("Carrier", "LongTargetFamily", "LongTargetFamily", output=fixture.root / "bound.exe")
            self.assertTrue(plan.exe_patch_required)
            self.assertFalse(plan.model_overlay_required)
            self.assertEqual(plan.donor_package["file_count"], 5)
            self.assertEqual(plan.planned_exe_sha256, plan.preview()["planned_exe_sha256"])

    def test_independent_carrier_model_and_physics_composition_is_three_way(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            plan = fixture.plan("Carrier", "LongTargetFamily", "Carrier", output=fixture.root / "bound.exe")
            self.assertEqual(plan.composition.to_dict(), {
                "carrier_type": "Carrier", "physics_family": "LongTargetFamily",
                "model_donor": "Carrier", "runtime_family": "LongTargetFamily",
            })
            self.assertTrue(plan.exe_patch_required)
            self.assertTrue(plan.model_overlay_required)
            self.assertIn("nested/extra.bin", {row["donor_relative_path"] for row in plan.overlay_writes})
            provenance = {row["donor_relative_path"]: row["source_provenance"] for row in plan.overlay_writes}
            self.assertEqual(provenance["car.dx"], "DATA_SMA")

    def test_carrier_physics_and_model_can_all_be_different(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            plan = fixture.plan(
                "Carrier", "LongTargetFamily", "Donor",
                output=fixture.root / "three-way.exe",
            )
            self.assertEqual(
                plan.composition,
                VehicleComposition("Carrier", "LongTargetFamily", "Donor"),
            )
            self.assertTrue(plan.exe_patch_required)
            self.assertTrue(plan.model_overlay_required)
            self.assertGreater(len(plan.overlay_writes), 0)

    def test_pure_model_swap_elides_exe_patch_and_uses_full_forklift_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            vehicle, mods = _write_configs(fixture.root, ("Carrier", "LongTargetFamily"))
            fixture.vehicle_config = parse_vehicle_config(vehicle, build="synthetic")
            fixture.modifications_config = parse_vehicle_config(mods, build="synthetic")
            plan = fixture.plan("Carrier", "Carrier", "forklift")
            self.assertFalse(plan.exe_patch_required)
            self.assertIsNone(plan.output_exe)
            self.assertTrue(plan.model_overlay_required)
            self.assertIn("nested/fork.bin", {row["donor_relative_path"] for row in plan.overlay_writes})
            self.assertEqual(len(plan.overlay_writes), 5)
            self.assertIn("destination-only.dxt", plan.archive_fallbacks)

    def test_all_equal_composition_is_a_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            vehicle, mods = _write_configs(fixture.root, ("Carrier", "LongTargetFamily"))
            fixture.vehicle_config = parse_vehicle_config(vehicle, build="synthetic")
            fixture.modifications_config = parse_vehicle_config(mods, build="synthetic")
            plan = fixture.plan("Carrier", "Carrier", "Carrier")
            self.assertFalse(plan.exe_patch_required)
            self.assertFalse(plan.model_overlay_required)
            manifest = choose_composition_manifest_path(fixture.root, plan.composition)
            result = apply_vehicle_composition(plan, manifest_path=manifest)
            self.assertEqual(result["status"], "NO_CHANGES")
            self.assertFalse(manifest.exists())

    def test_referenced_destination_archive_fallback_cannot_silently_mix(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            # A donor DX refers to a texture absent from its package. The runtime
            # family archive has that path, so a loose overlay would mix sources.
            donor = fixture.loose_root / "Donor"
            donor.mkdir()
            dx = _synthetic_dx("target-only")
            for name in ("car.dx", "complete.dx", "wheel.dx"):
                (donor / name).write_bytes(dx)
            (donor / "body-tga.dxt").write_bytes(b"donor body")
            fixture.model_packages = inventory_vehicle_model_packages(
                fixture.archive_members, fixture.loose_root
            )
            with self.assertRaisesRegex(ValueError, "unresolved DX texture dependencies"):
                fixture.plan("Carrier", "LongTargetFamily", "Donor", output=fixture.root / "bound.exe")

    def test_wheel_less_donor_cannot_reveal_archived_target_wheel(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            with self.assertRaisesRegex(ValueError, "cannot be masked: wheel.dx"):
                fixture.plan("Carrier", "LongTargetFamily", "Ufo", output=fixture.root / "bound.exe")

    def test_preview_is_deterministic_and_source_model_is_read_before_destination_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            (fixture.loose_root / "Carrier").mkdir()
            source_loose = fixture.loose_root / "Carrier" / "body-tga.dxt"
            source_loose.write_bytes(b"source override snapshot")
            fixture.model_packages = inventory_vehicle_model_packages(
                fixture.archive_members, fixture.loose_root
            )
            first = fixture.plan("Carrier", "LongTargetFamily", "Carrier", output=fixture.root / "bound.exe")
            second = fixture.plan("Carrier", "LongTargetFamily", "Carrier", output=fixture.root / "bound.exe")
            self.assertEqual(first.preview(), second.preview())
            donor = first.donor_package["files"]["body-tga.dxt"]
            self.assertEqual(donor["data"], b"source override snapshot")
            self.assertEqual(source_loose.read_bytes(), b"source override snapshot")


class RVeh1TransactionTests(unittest.TestCase):
    def _model_swap_plan(self, fixture: RVeh1Fixture, *, patch_exe: bool = False):
        carrier = "Carrier"
        physics = "LongTargetFamily" if patch_exe else "Carrier"
        vehicle, mods = _write_configs(fixture.root, ("Carrier", "LongTargetFamily"))
        fixture.vehicle_config = parse_vehicle_config(vehicle, build="synthetic")
        fixture.modifications_config = parse_vehicle_config(mods, build="synthetic")
        return fixture.plan(
            carrier, physics, "Donor",
            output=(fixture.root / "bound.exe") if patch_exe else None,
        )

    def test_apply_and_restore_new_replaced_stale_and_unrelated_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            destination = fixture.loose_root / "Carrier"
            destination.mkdir()
            (destination / "body-tga.dxt").write_bytes(b"old body")
            (destination / "stale-loose.bin").write_bytes(b"stale")
            plan = self._model_swap_plan(fixture)
            original_exe = fixture.exe.read_bytes()
            manifest = choose_composition_manifest_path(fixture.root, plan.composition)
            result = apply_vehicle_composition(plan, manifest_path=manifest)
            self.assertEqual(result["status"], "APPLIED_COMPOSITION")
            self.assertEqual((destination / "body-tga.dxt").read_bytes(), b"donor texture")
            self.assertFalse((destination / "stale-loose.bin").exists())
            self.assertEqual((destination / "nested" / "extra.bin").read_bytes(), b"donor extra")
            (destination / "created-later.bin").write_bytes(b"game/user file")
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["composition"]["model_donor"], "Donor")
            donor_rows = [row for row in data["model_overlay_changes"] if row["operation"] == "WRITE_DONOR_FILE"]
            self.assertIn("DATA_SMA", {row["source_provenance"] for row in donor_rows})
            body_row = next(row for row in donor_rows if row["donor_relative_path"] == "body-tga.dxt")
            self.assertTrue(body_row["existed_before"])
            self.assertTrue(body_row["backup_relative_path"])
            self.assertTrue(any(row["operation"] == "REMOVE_STALE_LOOSE" for row in data["model_overlay_changes"]))
            self.assertEqual(fixture.exe.read_bytes(), original_exe)

            restored = restore_vehicle_composition(
                manifest, expected_exe_sha256=fixture.exe_sha256
            )
            self.assertEqual(restored["status"], "RESTORED_COMPOSITION")
            self.assertEqual((destination / "body-tga.dxt").read_bytes(), b"old body")
            self.assertEqual((destination / "stale-loose.bin").read_bytes(), b"stale")
            self.assertFalse((destination / "nested" / "extra.bin").exists())
            self.assertEqual((destination / "created-later.bin").read_bytes(), b"game/user file")
            self.assertEqual(fixture.exe.read_bytes(), original_exe)
            self.assertEqual(
                restore_vehicle_composition(manifest, expected_exe_sha256=fixture.exe_sha256)["status"],
                "ALREADY_RESTORED",
            )

    def test_restore_conflict_refuses_without_touching_other_overlay_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            destination = fixture.loose_root / "Carrier"
            destination.mkdir()
            (destination / "body-tga.dxt").write_bytes(b"pre-apply")
            plan = self._model_swap_plan(fixture)
            manifest = choose_composition_manifest_path(fixture.root, plan.composition)
            apply_vehicle_composition(plan, manifest_path=manifest)
            (destination / "body-tga.dxt").write_bytes(b"user changed")
            donor_file = destination / "donor.txt"
            self.assertEqual(donor_file.read_bytes(), b"sidecar")
            with self.assertRaisesRegex(ValueError, "no files were restored"):
                restore_vehicle_composition(manifest, expected_exe_sha256=fixture.exe_sha256)
            self.assertEqual((destination / "body-tga.dxt").read_bytes(), b"user changed")
            self.assertEqual(donor_file.read_bytes(), b"sidecar")

    def test_restore_does_not_remove_empty_destination_directory_created_after_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            plan = fixture.plan(
                "Carrier", "LongTargetFamily", "Donor",
                output=fixture.root / "bound.exe",
            )
            destination = fixture.loose_root / "LongTargetFamily"
            self.assertIn(
                "DataGx/Vehicles/LongTargetFamily", plan.created_directories
            )
            # Simulate the user creating the empty destination after preview.
            destination.mkdir()
            manifest = choose_composition_manifest_path(
                fixture.root, plan.composition, output_exe=plan.output_exe
            )
            apply_vehicle_composition(plan, manifest_path=manifest)
            applied_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertNotIn(
                "DataGx/Vehicles/LongTargetFamily",
                applied_manifest["created_directories"],
            )
            restore_vehicle_composition(
                manifest, expected_exe_sha256=fixture.exe_sha256
            )
            self.assertTrue(destination.is_dir())
            self.assertEqual(list(destination.iterdir()), [])

    def test_restore_removes_only_empty_directories_created_by_composer(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            (fixture.root / "DataGx" / "Vehicles").rmdir()
            (fixture.root / "DataGx").rmdir()
            plan = fixture.plan(
                "Carrier", "LongTargetFamily", "Donor",
                output=fixture.root / "bound.exe",
            )
            self.assertEqual(
                set(plan.created_directories),
                {
                    "DataGx", "DataGx/Vehicles",
                    "DataGx/Vehicles/LongTargetFamily",
                    "DataGx/Vehicles/LongTargetFamily/nested",
                },
            )
            manifest = choose_composition_manifest_path(
                fixture.root, plan.composition, output_exe=plan.output_exe
            )
            apply_vehicle_composition(plan, manifest_path=manifest)
            applied_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                set(applied_manifest["created_directories"]),
                {
                    "DataGx", "DataGx/Vehicles",
                    "DataGx/Vehicles/LongTargetFamily",
                    "DataGx/Vehicles/LongTargetFamily/nested",
                },
            )
            restore_vehicle_composition(
                manifest, expected_exe_sha256=fixture.exe_sha256
            )
            self.assertFalse((fixture.root / "DataGx").exists())

    def test_restore_rejects_manifest_destination_outside_runtime_model_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            plan = self._model_swap_plan(fixture)
            manifest = choose_composition_manifest_path(fixture.root, plan.composition)
            apply_vehicle_composition(plan, manifest_path=manifest)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["model_overlay_changes"][0]["destination_relative_path"] = "MRallye.exe"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            before = fixture.exe.read_bytes()
            with self.assertRaisesRegex(ValueError, "outside its runtime-family directory"):
                restore_vehicle_composition(manifest, expected_exe_sha256=fixture.exe_sha256)
            self.assertEqual(fixture.exe.read_bytes(), before)

    def test_corrupt_executable_backup_is_not_tolerated_as_interrupted_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            plan = self._model_swap_plan(fixture, patch_exe=True)
            output = plan.output_exe
            manifest = choose_composition_manifest_path(
                fixture.root, plan.composition, output_exe=output
            )
            apply_vehicle_composition(plan, manifest_path=manifest)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["status"] = "applying"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            backup = output.with_name(output.name + ".original")
            backup.write_bytes(b"wrong original backup")
            patched = output.read_bytes()
            with self.assertRaisesRegex(ValueError, "backup is missing or changed"):
                restore_vehicle_composition(manifest, expected_exe_sha256=fixture.exe_sha256)
            self.assertEqual(output.read_bytes(), patched)

    def test_patched_exe_and_model_overlay_restore_as_one_composition(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            plan = self._model_swap_plan(fixture, patch_exe=True)
            output = plan.output_exe
            self.assertIsNotNone(output)
            manifest = choose_composition_manifest_path(fixture.root, plan.composition, output_exe=output)
            original = fixture.exe.read_bytes()
            result = apply_vehicle_composition(plan, manifest_path=manifest)
            self.assertTrue(output.is_file())
            self.assertNotEqual(output.read_bytes(), original)
            self.assertFalse(fixture.exe.read_bytes() != original)
            self.assertTrue((fixture.loose_root / "LongTargetFamily" / "nested" / "extra.bin").exists())
            self.assertEqual(discover_vehicle_composition_manifests(
                fixture.root, expected_exe_sha256=fixture.exe_sha256
            )[0]["status"], "applied")
            restored = restore_vehicle_composition(
                manifest, expected_exe_sha256=fixture.exe_sha256
            )
            self.assertEqual(restored["status"], "RESTORED_COMPOSITION")
            self.assertEqual(output.read_bytes(), original)
            self.assertFalse((fixture.loose_root / "LongTargetFamily" / "nested" / "extra.bin").exists())

    def test_failed_preparation_does_not_change_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            destination = fixture.loose_root / "Carrier"
            destination.mkdir()
            old = destination / "old.bin"
            old.write_bytes(b"old")
            incomplete = fixture.loose_root / "Incomplete"
            incomplete.mkdir()
            (incomplete / "car.dx").write_bytes(_synthetic_dx())
            fixture.model_packages = inventory_vehicle_model_packages(
                fixture.archive_members, fixture.loose_root
            )
            with self.assertRaisesRegex(ValueError, "incomplete"):
                fixture.plan("Carrier", "Carrier", "Incomplete")
            self.assertEqual(old.read_bytes(), b"old")
            self.assertFalse((destination / "car.dx").exists())

    def test_destination_modified_after_preview_is_refused_before_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RVeh1Fixture(Path(temporary))
            destination = fixture.loose_root / "Carrier"
            destination.mkdir()
            old = destination / "body-tga.dxt"
            old.write_bytes(b"preview bytes")
            plan = self._model_swap_plan(fixture)
            old.write_bytes(b"changed after preview")
            manifest = choose_composition_manifest_path(fixture.root, plan.composition)
            with self.assertRaisesRegex(ValueError, "changed after preview"):
                apply_vehicle_composition(plan, manifest_path=manifest)
            self.assertEqual(old.read_bytes(), b"changed after preview")
            self.assertFalse(manifest.exists())


class RVeh1BatchCliTests(unittest.TestCase):
    def _inventory(self, root: Path):
        return SimpleNamespace(
            executable=root / "MRallye.exe",
            data_sma=None,
            archive_members=(),
            model_packages={},
            vehicle_config=object(),
            modifications_config=object(),
        )

    def test_schema_v2_apply_routes_independent_model_donor_through_composer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "composition.json"
            config.write_text(
                json.dumps({
                    "schema_version": 2,
                    "bindings": [{
                        "carrier_type": "Navara",
                        "physics_family": "Navara",
                        "model_donor": "forklift",
                    }],
                }),
                encoding="utf-8",
            )
            inventory = self._inventory(root)
            plan = SimpleNamespace(preview=lambda: {"exe_patch_required": False})
            output = io.StringIO()
            with (
                mock.patch("tools.physics_bind.load_install_inventory", return_value=inventory),
                mock.patch("tools.physics_bind.build_vehicle_composition_plan", return_value=plan) as build,
                mock.patch("tools.physics_bind.apply_vehicle_composition", return_value={
                    "status": "APPLIED_COMPOSITION",
                }) as apply,
                redirect_stdout(output),
            ):
                status = physics_bind_main([
                    "apply", "--install-root", str(root), "--config", str(config),
                ])
        self.assertEqual(status, 0)
        self.assertIn('"status": "APPLIED_COMPOSITION"', output.getvalue())
        composition = build.call_args.args[2]
        self.assertEqual(composition, VehicleComposition("Navara", "Navara", "forklift"))
        self.assertIsNone(build.call_args.kwargs["output_exe"])
        apply.assert_called_once()

    def test_schema_v1_batch_validate_and_apply_keep_legacy_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "binding-v1.json"
            config.write_text(
                '{"schema_version":1,"bindings":[{"carrier_type":"Navara",'
                '"physics_family":"Trooper"}]}',
                encoding="utf-8",
            )
            inventory = mock.patch("tools.physics_bind.load_install_inventory")
            output = io.StringIO()
            with (
                inventory as load_inventory,
                mock.patch("tools.physics_bind.validate_binding_request", return_value={"status": "VALID"}) as validate,
                mock.patch("tools.physics_bind.apply_binding_copy", return_value={"status": "APPLIED_TO_COPY"}) as apply,
                redirect_stdout(output),
            ):
                validate_status = physics_bind_main([
                    "validate", "--install-root", str(root), "--config", str(config),
                ])
                apply_status = physics_bind_main([
                    "apply", "--install-root", str(root), "--config", str(config),
                ])
        self.assertEqual(validate_status, 0)
        self.assertEqual(apply_status, 0)
        load_inventory.assert_not_called()
        validate.assert_called_once()
        apply.assert_called_once()

    def test_explicit_manifest_restore_routes_to_composition_restore(self):
        manifest = Path("test-manifest.vehicle-compose.json")
        output = io.StringIO()
        with (
            mock.patch("tools.physics_bind.restore_vehicle_composition", return_value={
                "status": "RESTORED_COMPOSITION",
            }) as restore,
            redirect_stdout(output),
        ):
            status = physics_bind_main(["restore", "--manifest", str(manifest)])
        self.assertEqual(status, 0)
        restore.assert_called_once_with(manifest, install_root=None)
        self.assertIn('"status": "RESTORED_COMPOSITION"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
