from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from master_rallye.vehicle_config_analysis import VehicleConfigDocument, parse_vehicle_config
from master_rallye.vehicle_config_schema import (
    RETAIL_ENGINE_COUNT_SCHEMA,
    RETAIL_REQUIRED_FIXED_SCHEMA,
    analyze_vehicle_base_schema,
    fixed_schema_fingerprint,
)
from master_rallye.vehicle_family_binder import (
    InstallInventory,
    run_interactive_wizard,
)
from master_rallye.vehicle_composition import VehicleComposition
from master_rallye.vehicle_family_broker import PLAYER_MODIFICATION_FIELDS
from master_rallye.vehicle_model_inventory import build_vehicle_family_inventory
from master_rallye.vehicle_physics_binding import (
    FamilyCatalogEntry,
    PhysicsBinding,
    validate_binding_families,
    validate_vehicle_family_config,
)


def _fields(gears: int = 7, torque: int = 6) -> dict[str, dict[str, str]]:
    fields = {
        path: {"type": value_type, "value": "1"}
        for path, value_type in RETAIL_REQUIRED_FIXED_SCHEMA.items()
    }
    fields["Engine/Gears"]["value"] = str(gears)
    fields["Engine/TorqueEntries"]["value"] = str(torque)
    for prefix in ("Gear", "ChangeUpRevs", "ChangeDownRevs"):
        for index in range(gears):
            fields[f"Engine/{prefix}{index}"] = {"type": "Float", "value": "1"}
    for index in range(torque):
        fields[f"Engine/TorqueEntry{index}"] = {"type": "Vector2", "value": "0,0"}
    return fields


def _document(
    families: dict[str, dict[str, dict[str, str]]], source: str = "synthetic"
) -> VehicleConfigDocument:
    return VehicleConfigDocument(
        build="synthetic",
        source=source,
        sha256=hashlib.sha256(source.encode("utf-8")).hexdigest(),
        file_size=0,
        families=families,
        excluded_families={},
    )


def _mods() -> VehicleConfigDocument:
    return _document({"Probe": {
        f"Player1/Modifications/{name}": {"type": "Float", "value": "1"}
        for name in PLAYER_MODIFICATION_FIELDS
    }}, "synthetic-modifications")


class RPhys32SemanticSchemaTests(unittest.TestCase):
    def test_retail_fixed_schema_is_descriptive_and_separates_count_headers(self):
        self.assertEqual(len(RETAIL_REQUIRED_FIXED_SCHEMA), 120)
        self.assertEqual(len(RETAIL_REQUIRED_FIXED_SCHEMA) - len(RETAIL_ENGINE_COUNT_SCHEMA), 118)
        self.assertEqual(RETAIL_ENGINE_COUNT_SCHEMA, {
            "Engine/Gears": "Int",
            "Engine/TorqueEntries": "Int",
        })
        self.assertEqual(len(fixed_schema_fingerprint()), 64)

    def test_count_driven_valid_shapes_do_not_require_a_universal_field_total(self):
        for gears, torque in ((7, 6), (7, 5), (6, 6), (7, 8), (10, 8)):
            with self.subTest(gears=gears, torque=torque):
                audit = analyze_vehicle_base_schema(_fields(gears, torque))
                self.assertEqual(audit.compatibility_class, "COMPATIBLE")
                self.assertTrue(audit.fixed_schema_ok)
                self.assertTrue(audit.dynamic_shape_ok)
                self.assertEqual(audit.expected_total_fields, 120 + 3 * gears + torque)
                self.assertEqual(audit.total_fields, audit.expected_total_fields)
                self.assertEqual(audit.gear_fields_present, {
                    "Gear": gears,
                    "ChangeUpRevs": gears,
                    "ChangeDownRevs": gears,
                })
                self.assertEqual(audit.torque_fields_present, torque)

    def test_semantic_validation_matrix_distinguishes_incomplete_unverified_and_types(self):
        cases = []

        fields = _fields(7, 6)
        del fields["Engine/Gear6"]
        cases.append(("missing gear", fields, "INCOMPLETE"))

        fields = _fields(6, 6)
        for prefix in ("Gear", "ChangeUpRevs", "ChangeDownRevs"):
            fields[f"Engine/{prefix}6"] = {"type": "Float", "value": "1"}
        cases.append(("extra gear above declared count", fields, "UNVERIFIED_SCHEMA"))

        fields = _fields(7, 8)
        del fields["Engine/TorqueEntry7"]
        cases.append(("missing torque entry", fields, "INCOMPLETE"))

        fields = _fields(7, 5)
        fields["Engine/TorqueEntry5"] = {"type": "Vector2", "value": "0,0"}
        cases.append(("extra torque entry above declared count", fields, "UNVERIFIED_SCHEMA"))

        fields = _fields(7, 6)
        fields["Engine/Gear2"]["type"] = "Int"
        cases.append(("wrong indexed float type", fields, "TYPE_MISMATCH"))

        fields = _fields(7, 6)
        fields["Engine/TorqueEntry2"]["type"] = "Float"
        cases.append(("wrong indexed vector type", fields, "TYPE_MISMATCH"))

        fields = _fields(7, 6)
        del fields["Dimensions/Length"]
        cases.append(("missing fixed field", fields, "INCOMPLETE"))

        fields = _fields(7, 6)
        fields["Engine/UnrecognizedReaderPath"] = {"type": "Float", "value": "1"}
        cases.append(("unexplained path", fields, "UNVERIFIED_SCHEMA"))

        fields = _fields(7, 6)
        fields["Engine/Gears"]["type"] = "Float"
        cases.append(("wrong count header type", fields, "TYPE_MISMATCH"))

        fields = _fields(7, 6)
        fields["Engine/Gears"]["value"] = "-1"
        cases.append(("negative count", fields, "UNVERIFIED_SCHEMA"))

        fields = _fields(7, 6)
        fields["Engine/TorqueEntries"]["value"] = "six"
        cases.append(("non-decimal count", fields, "UNVERIFIED_SCHEMA"))

        fields = _fields(7, 6)
        del fields["Engine/ChangeDownRevs3"]
        fields["Engine/ChangeDownRevs03"] = {"type": "Float", "value": "1"}
        cases.append(("non-canonical index spelling", fields, "INCOMPLETE"))

        for name, fields, expected in cases:
            with self.subTest(case=name):
                audit = analyze_vehicle_base_schema(fields)
                self.assertEqual(audit.compatibility_class, expected)

    def test_audit_reports_exact_missing_unexpected_and_type_paths(self):
        fields = _fields(7, 6)
        del fields["Engine/Gear6"]
        fields["Engine/Gear7"] = {"type": "Float", "value": "1"}
        fields["Engine/TorqueEntry0"]["type"] = "Float"
        audit = analyze_vehicle_base_schema(fields)
        self.assertIn("Engine/Gear6", audit.missing_paths)
        self.assertIn("Engine/Gear7", audit.unexpected_paths)
        self.assertIn(
            ("Engine/TorqueEntry0", "Vector2", "Float"), audit.type_mismatches
        )
        self.assertFalse(audit.dynamic_shape_ok)

    def test_unverified_override_is_narrow_and_never_waives_missing_or_bad_types(self):
        fields = _fields()
        fields["Engine/ReaderExtension"] = {"type": "Float", "value": "1"}
        vehicle = _document({"Probe": fields})
        modifications = _mods()
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_SCHEMA"):
            validate_vehicle_family_config("Probe", vehicle, modifications)
        allowed = validate_vehicle_family_config(
            "Probe", vehicle, modifications, allow_unverified_schema=True
        )
        self.assertTrue(allowed.schema_override_used)
        self.assertEqual(allowed.config_schema.compatibility_class, "UNVERIFIED_SCHEMA")

        for mutate, expected in (
            (lambda f: f.pop("Dimensions/Length"), "INCOMPLETE"),
            (lambda f: f["Engine/Gear0"].update(type="Int"), "TYPE_MISMATCH"),
        ):
            changed = _fields()
            mutate(changed)
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                validate_vehicle_family_config(
                    "Probe", _document({"Probe": changed}), modifications,
                    allow_unverified_schema=True,
                )

    def test_binding_backend_uses_the_same_override_and_records_its_audit(self):
        fields = _fields()
        fields["Engine/ReaderExtension"] = {"type": "Float", "value": "1"}
        vehicle = _document({"Probe": fields})
        catalog = (FamilyCatalogEntry(0, "Carrier", 0x401020, 0x402080),)
        binding = (PhysicsBinding("Carrier", "Probe"),)
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_SCHEMA"):
            validate_binding_families(binding, vehicle, _mods(), catalog=catalog)
        result = validate_binding_families(
            binding, vehicle, _mods(), catalog=catalog, allow_unverified_schema=True
        )
        self.assertTrue(result[0].schema_override_used)
        self.assertEqual(
            result[0].config_schema.compatibility_class, "UNVERIFIED_SCHEMA"
        )

    def test_inventory_exposes_semantic_audit_without_making_field_count_a_gate(self):
        fields = _fields(6, 6)
        vehicle = _document({"Probe": fields})
        rows = build_vehicle_family_inventory(vehicle, _document({}), {})
        row = rows[0]
        self.assertEqual(row["base_config"]["status"], "COMPATIBLE")
        self.assertEqual(row["base_config"]["field_count"], 144)
        self.assertEqual(row["base_config"]["schema_audit"]["gears_count"], 6)
        self.assertEqual(row["base_config"]["schema_audit"]["torque_entries_count"], 6)
        self.assertNotIn("schema_sha256", row["base_config"])


class RPhys32WizardSchemaOverrideTests(unittest.TestCase):
    def _inventory(self, root: Path) -> InstallInventory:
        exe = root / "MRallye.exe"
        exe.write_bytes(b"synthetic executable")
        fields = _fields()
        fields["Engine/ReaderExtension"] = {"type": "Float", "value": "1"}
        vehicle = _document({"Probe": fields})
        modifications = _mods()
        audit = analyze_vehicle_base_schema(fields).to_dict()
        model = {
            "family_names": ["Probe"], "provenance": "DATA_SMA", "status": "COMPLETE",
            "wheelless_by_design": False,
            "required_resources": ["car.dx", "complete.dx", "wheel.dx"],
            "missing_resources": [], "ambiguous_resources": [],
            "resources": {
                name: {"source": "DATA_SMA", "present": True}
                for name in ("car.dx", "complete.dx", "wheel.dx")
            },
            "archive_file_count": 3, "loose_file_count": 0,
        }
        row = {
            "family": "Probe", "identity_kind": "CONFIG_AND_MODEL", "type_ids": [],
            "base_config": {
                "status": "UNVERIFIED_SCHEMA", "field_count": audit["total_fields"],
                "group_counts": audit["group_counts"], "missing_groups": [],
                "fixed_fields_expected": 120, "fixed_fields_present": 120,
                "compatibility_class": "UNVERIFIED_SCHEMA", "schema_audit": audit,
            },
            "player1_modifications": {
                "status": "COMPLETE", "field_count": 13,
                "expected_field_count": 13, "missing_fields": [],
                "unexpected_fields": [], "wrong_type_fields": [],
            },
            "model": model,
        }
        return InstallInventory(
            root=root, executable=exe, executable_sha256="synthetic", data_sma=None,
            archive_members=(), vehicles_xml_bytes=b"<Config><Values /></Config>",
            modifications_xml_bytes=b"<Config><Values /></Config>",
            vehicle_config=vehicle, modifications_config=modifications,
            model_packages={"probe": model}, families=[row],
            config_sources={"vehicles.xml": "synthetic", "Modifications.xml": "synthetic"},
        )

    @staticmethod
    def _fake_plan(root: Path, composition: VehicleComposition):
        return SimpleNamespace(
            composition=composition,
            type_id=7,
            config_validation=SimpleNamespace(
                config_schema=SimpleNamespace(compatibility_class="UNVERIFIED_SCHEMA"),
                player1_overlay_count=13,
                schema_override_used=True,
            ),
            exe_patch_required=True,
            model_overlay_required=False,
            donor_package={
                "family": composition.model_donor,
                "provenance": "DATA_SMA",
                "file_count": 3,
            },
            overlay_writes=[], overlay_removals=[], archive_fallbacks=[],
            destination_directory=root / "DataGx" / "Vehicles" / composition.physics_family,
            output_exe=root / "bound.exe",
        )

    def test_exact_schema_phrase_is_required_and_forwarded_to_shared_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory = self._inventory(root)
            with mock.patch(
                "master_rallye.vehicle_family_binder.build_vehicle_composition_plan",
                side_effect=lambda _exe, _root, composition, *_args, **_kwargs:
                    self._fake_plan(root, composition),
            ) as build_plan, mock.patch(
                "master_rallye.vehicle_family_binder.load_install_inventory",
                return_value=inventory,
            ):
                answers = iter(["7", "Probe", "ALLOW UNVERIFIED SCHEMA", "1"])
                output: list[str] = []
                status = run_interactive_wizard(
                    root, dry_run=True, input_fn=lambda _prompt: next(answers),
                    output_fn=output.append,
                )
        self.assertEqual(status, 0)
        self.assertTrue(any("unverified schema" in line.lower() for line in output))
        self.assertTrue(build_plan.call_args.kwargs["allow_unverified_schema"])

    def test_wrong_schema_phrase_stops_before_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory = self._inventory(root)
            with mock.patch(
                "master_rallye.vehicle_family_binder.load_install_inventory",
                return_value=inventory,
            ), mock.patch(
                "master_rallye.vehicle_family_binder.build_vehicle_composition_plan"
            ) as build_plan:
                answers = iter(["7", "Probe", "allow unverified schema"])
                status = run_interactive_wizard(
                    root, dry_run=True, input_fn=lambda _prompt: next(answers),
                    output_fn=lambda _line: None,
                )
        self.assertEqual(status, 2)
        build_plan.assert_not_called()

CORPORA = Path(r"D:\Game\Master Rallye\corpora")
VEHICLE_XMLS = {
    "demo-8.4.1": CORPORA / "demo-8.4.1" / "DataGame" / "vehicles.xml",
    "demo-9.3.1": CORPORA / "demo-9.3.1" / "DataGame" / "vehicles.xml",
    "demo-9.10.0": CORPORA / "demo-9.10.0" / "DataGame" / "vehicles.xml",
    "retail": CORPORA / "retail" / "Data.sma_unpacked" / "DataGame" / "vehicles.xml",
}
CORPORA_AVAILABLE = all(path.is_file() for path in VEHICLE_XMLS.values())


@unittest.skipUnless(CORPORA_AVAILABLE, "requires the read-only vehicle XML corpora")
class RPhys32CorpusRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {
            build: parse_vehicle_config(path, build=build)
            for build, path in VEHICLE_XMLS.items()
        }

    def _audit(self, build: str, family: str):
        return analyze_vehicle_base_schema(self.documents[build].families[family])

    def test_retail_candidate_families_match_reader_counts_not_one_total(self):
        expected = {
            "Navara": (7, 6, 147),
            "Kamaz": (7, 5, 146),
            "Pajero": (6, 6, 144),
            "Mercedes": (6, 6, 144),
            "Bowler": (7, 8, 149),
            "Custom": (7, 8, 149),
            "Trooper": (7, 6, 147),
        }
        retail = self.documents["retail"]
        for family, (gears, torque, count) in expected.items():
            with self.subTest(family=family):
                audit = analyze_vehicle_base_schema(retail.families[family])
                self.assertEqual(audit.compatibility_class, "COMPATIBLE")
                self.assertEqual((audit.gears_count, audit.torque_entries_count), (gears, torque))
                self.assertEqual(audit.total_fields, count)

    def test_every_named_retail_config_family_matches_reader_schema(self):
        retail = self.documents["retail"]
        self.assertEqual(len(retail.families), 35)
        statuses = {
            family: analyze_vehicle_base_schema(fields).compatibility_class
            for family, fields in retail.families.items()
        }
        self.assertEqual(set(statuses.values()), {"COMPATIBLE"})

    def test_demo_cross_builds_preserve_array_cardinality_evidence(self):
        cases = (
            ("demo-8.4.1", "Trooper", 7, 8),
            ("demo-9.3.1", "Bowler", 7, 8),
            ("demo-9.3.1", "Custom", 7, 8),
            ("demo-9.10.0", "Bowler", 7, 8),
            ("demo-9.10.0", "Custom", 7, 8),
            ("demo-9.10.0", "Kamaz", 10, 8),
        )
        for build, family, gears, torque in cases:
            with self.subTest(build=build, family=family):
                audit = self._audit(build, family)
                self.assertEqual((audit.gears_count, audit.torque_entries_count), (gears, torque))
                self.assertEqual(audit.gear_fields_present, {
                    "Gear": gears,
                    "ChangeUpRevs": gears,
                    "ChangeDownRevs": gears,
                })
                self.assertEqual(audit.torque_fields_present, torque)
                self.assertTrue(audit.dynamic_shape_ok)

    def test_cross_build_paths_outside_retail_fixed_schema_stay_unverified_or_incomplete(self):
        for build in ("demo-8.4.1", "demo-9.3.1"):
            with self.subTest(build=build):
                audit = self._audit(build, "Trooper")
                self.assertNotEqual(audit.compatibility_class, "COMPATIBLE")
                self.assertGreater(audit.missing_path_count + len(audit.unexpected_paths), 0)


if __name__ == "__main__":
    unittest.main()
