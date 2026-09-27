from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from master_rallye.vehicle_family_broker import PLAYER_MODIFICATION_FIELDS
from master_rallye.vehicle_physics_binding import (
    FamilyCatalogEntry,
    PhysicsBinding,
    RETAIL_FAMILY_CATALOG,
    apply_binding_copy,
    load_binding_config,
    parse_binding_config_text,
    parse_pe32_layout,
    patch_family_initializer,
    restore_binding_copy,
    validate_binding_families,
    validate_binding_request,
)
from master_rallye.vehicle_config_analysis import parse_vehicle_config
from master_rallye.vehicle_config_schema import RETAIL_REQUIRED_FIXED_SCHEMA


TEST_CATALOG = (
    FamilyCatalogEntry(0, "Carrier", 0x00401020, 0x00402080),
    FamilyCatalogEntry(1, "Control", 0x00401030, 0x00402090),
    FamilyCatalogEntry(2, "Other", 0x00401040, 0x004020A0),
)
BASE_GROUPS = {
    "Dimensions": 8,
    "Chassis": 16,
    "Steering": 5,
    "Engine": 45,
    "Suspension": 48,
    "DamageParams": 25,
}


def _section_header(name, virtual_size, virtual_address, raw_size, raw_pointer, characteristics):
    return struct.pack(
        "<8sIIIIIIHHI", name.ljust(8, b"\0"), virtual_size, virtual_address,
        raw_size, raw_pointer, 0, 0, 0, 0, characteristics,
    )


def make_synthetic_pe32() -> bytes:
    """Build a small hand-authored PE32 image; no retail executable bytes."""
    data = bytearray(0x800)
    data[0:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    coff = 0x84
    struct.pack_into("<HHIIIHH", data, coff, 0x014C, 2, 0, 0, 0, 0xE0, 0x010F)
    optional = coff + 20
    struct.pack_into("<H", data, optional, 0x010B)
    struct.pack_into("<I", data, optional + 8, 0x200)
    struct.pack_into("<I", data, optional + 28, 0x00400000)
    struct.pack_into("<II", data, optional + 32, 0x1000, 0x200)
    struct.pack_into("<I", data, optional + 56, 0x3000)
    struct.pack_into("<I", data, optional + 60, 0x400)
    struct.pack_into("<H", data, optional + 70, 0)
    section_table = optional + 0xE0
    data[section_table:section_table + 40] = _section_header(
        b".text", 0x200, 0x1000, 0x200, 0x400, 0x60000020
    )
    data[section_table + 40:section_table + 80] = _section_header(
        b".data", 0x200, 0x2000, 0x200, 0x600, 0xC0000040
    )
    # `PUSH original_literal_va` instructions at the two synthetic call sites.
    struct.pack_into("<BI", data, 0x420, 0x68, TEST_CATALOG[0].literal_va)
    struct.pack_into("<BI", data, 0x430, 0x68, TEST_CATALOG[1].literal_va)
    struct.pack_into("<BI", data, 0x440, 0x68, TEST_CATALOG[2].literal_va)
    data[0x680:0x688] = b"Carrier\0"
    data[0x690:0x698] = b"Control\0"
    data[0x6A0:0x6A6] = b"Other\0"
    return bytes(data)


def make_configs(root: Path, *, target: str = "LongTargetFamily", include_overlay: bool = True,
                 missing_base_group: str | None = None) -> tuple[Path, Path]:
    vehicle_path = root / "vehicles.xml"
    mods_path = root / "Modifications.xml"
    fields = {
        path: {"type": value_type, "value": "1"}
        for path, value_type in RETAIL_REQUIRED_FIXED_SCHEMA.items()
    }
    fields["Engine/Gears"]["value"] = "7"
    fields["Engine/TorqueEntries"]["value"] = "6"
    for prefix in ("Gear", "ChangeUpRevs", "ChangeDownRevs"):
        for index in range(7):
            fields[f"Engine/{prefix}{index}"] = {"type": "Float", "value": "1"}
    for index in range(6):
        fields[f"Engine/TorqueEntry{index}"] = {"type": "Vector2", "value": "0,0"}
    if missing_base_group is not None:
        missing_path = next(path for path in fields if path.startswith(missing_base_group + "/"))
        del fields[missing_path]
    value_rows = [
        f'<Value Name="Vehicles/{target}/{path}" Type="{row["type"]}" Value="{row["value"]}" />'
        for path, row in sorted(fields.items())
    ]
    vehicle_path.write_text(
        "<Config><Values>" + "".join(value_rows) + "</Values></Config>", encoding="utf-8"
    )
    overlay_rows = []
    if include_overlay:
        for field in PLAYER_MODIFICATION_FIELDS:
            overlay_rows.append(
                f'<Value Name="Vehicles/{target}/Player1/Modifications/{field}" '
                'Type="Float" Value="1" />'
            )
    mods_path.write_text(
        "<Config><Values>" + "".join(overlay_rows) + "</Values></Config>", encoding="utf-8"
    )
    return vehicle_path, mods_path


class RPhys3BindingConfigTests(unittest.TestCase):
    def test_binding_config_keeps_carrier_and_physics_family_distinct(self):
        bindings = parse_binding_config_text(
            '{"schema_version":1,"bindings":['
            '{"carrier_type":"Navara","physics_family":"Trooper"}]}'
        )
        self.assertEqual(bindings, (PhysicsBinding("Navara", "Trooper"),))

    def test_binding_config_rejects_model_identity_and_duplicate_carriers(self):
        with self.assertRaisesRegex(ValueError, "model/resource identity is separate"):
            parse_binding_config_text(
                '{"schema_version":1,"bindings":[{"carrier_type":"Navara",'
                '"physics_family":"Trooper","model_package":"Trooper"}]}'
            )
        with self.assertRaisesRegex(ValueError, "bound more than once"):
            parse_binding_config_text(
                '{"schema_version":1,"bindings":[{"carrier_type":"Navara",'
                '"physics_family":"Trooper"},{"carrier_type":"navara",'
                '"physics_family":"Jump"}]}'
            )
        with self.assertRaisesRegex(ValueError, "schema_version"):
            parse_binding_config_text(
                '{"schema_version":true,"bindings":[{"carrier_type":"Navara",'
                '"physics_family":"Trooper"}]}'
            )

    def test_config_validation_accepts_complete_base_and_player1_overlay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vehicle_path, mods_path = make_configs(root)
            vehicle = parse_vehicle_config(vehicle_path, build="synthetic")
            mods = parse_vehicle_config(mods_path, build="synthetic")
            result = validate_binding_families(
                (PhysicsBinding("Carrier", "LongTargetFamily"),), vehicle, mods,
                catalog=TEST_CATALOG,
            )
        self.assertEqual(result[0].type_id, 0)
        self.assertEqual(result[0].base_group_counts, BASE_GROUPS)
        self.assertEqual(result[0].player1_overlay_count, 13)
        self.assertEqual(result[0].pointer_source,
                         "new read-only .rphys3 executable-section string")

    def test_config_validation_fails_closed_for_unknown_carrier_or_family(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vehicle_path, mods_path = make_configs(root)
            vehicle = parse_vehicle_config(vehicle_path, build="synthetic")
            mods = parse_vehicle_config(mods_path, build="synthetic")
            with self.assertRaisesRegex(ValueError, "not initialized"):
                validate_binding_families(
                    (PhysicsBinding("Hidden", "LongTargetFamily"),), vehicle, mods,
                    catalog=TEST_CATALOG,
                )
            with self.assertRaisesRegex(ValueError, "absent from vehicles.xml"):
                validate_binding_families(
                    (PhysicsBinding("Carrier", "Missing"),), vehicle, mods,
                    catalog=TEST_CATALOG,
                )

    def test_config_validation_fails_for_incomplete_reader_groups_or_overlay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vehicle_path, mods_path = make_configs(root, missing_base_group="Engine")
            vehicle = parse_vehicle_config(vehicle_path, build="synthetic")
            mods = parse_vehicle_config(mods_path, build="synthetic")
            with self.assertRaisesRegex(ValueError, "config schema is INCOMPLETE"):
                validate_binding_families(
                    (PhysicsBinding("Carrier", "LongTargetFamily"),), vehicle, mods,
                    catalog=TEST_CATALOG,
                )
            vehicle_path, mods_path = make_configs(root, include_overlay=False)
            vehicle = parse_vehicle_config(vehicle_path, build="synthetic")
            mods = parse_vehicle_config(mods_path, build="synthetic")
            with self.assertRaisesRegex(ValueError, "Player1 overlay misses"):
                validate_binding_families(
                    (PhysicsBinding("Carrier", "LongTargetFamily"),), vehicle, mods,
                    catalog=TEST_CATALOG,
                )

    def test_config_validation_rejects_changed_base_path_type_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vehicle_path, mods_path = make_configs(root)
            source_text = vehicle_path.read_text(encoding="utf-8")
            vehicle_path.write_text(source_text.replace("/Dimensions/Length\"", "/Dimensions/Renamed\""),
                                    encoding="utf-8")
            vehicle = parse_vehicle_config(vehicle_path, build="synthetic")
            mods = parse_vehicle_config(mods_path, build="synthetic")
            with self.assertRaisesRegex(ValueError, "config schema is INCOMPLETE"):
                validate_binding_families(
                    (PhysicsBinding("Carrier", "LongTargetFamily"),), vehicle, mods,
                    catalog=TEST_CATALOG,
                )

    def test_config_validation_rejects_non_float_player1_overlay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vehicle_path, mods_path = make_configs(root)
            source_text = mods_path.read_text(encoding="utf-8")
            mods_path.write_text(source_text.replace('Type="Float"', 'Type="Integer"', 1),
                                 encoding="utf-8")
            vehicle = parse_vehicle_config(vehicle_path, build="synthetic")
            mods = parse_vehicle_config(mods_path, build="synthetic")
            with self.assertRaisesRegex(ValueError, "non-Float fields"):
                validate_binding_families(
                    (PhysicsBinding("Carrier", "LongTargetFamily"),), vehicle, mods,
                    catalog=TEST_CATALOG,
                )


class RPhys3PEPatchTests(unittest.TestCase):
    def test_catalog_has_25_static_initializer_entries_with_unique_sites(self):
        self.assertEqual(len(RETAIL_FAMILY_CATALOG), 25)
        self.assertEqual([entry.type_id for entry in RETAIL_FAMILY_CATALOG], list(range(25)))
        self.assertEqual(len({entry.push_instruction_va for entry in RETAIL_FAMILY_CATALOG}), 25)
        self.assertEqual(len({entry.literal_va for entry in RETAIL_FAMILY_CATALOG}), 25)

    def test_variable_length_string_and_multiple_bindings_patch_copy_only(self):
        source = make_synthetic_pe32()
        long_family = "LongTargetFamily_Name_With_Several_Bytes"
        bindings = (
            PhysicsBinding("Carrier", long_family),
            PhysicsBinding("Control", "Carrier"),
            PhysicsBinding("Other", long_family),
        )
        result = patch_family_initializer(source, bindings, catalog=TEST_CATALOG)
        self.assertNotEqual(result.data, source)
        self.assertEqual(result.source_sha256, hashlib.sha256(source).hexdigest())
        self.assertEqual(len(result.patches), 3)
        self.assertTrue(all(item.changed for item in result.patches))
        self.assertTrue(result.added_section)
        self.assertTrue(result.changed_ranges)

        layout = parse_pe32_layout(result.data)
        section = next(item for item in layout.sections if item.name == b".rphys3")
        self.assertGreater(section.virtual_address, 0x2000)
        pointer_va = result.patches[0].new_pointer_va
        offset = layout.va_to_file_offset(pointer_va, length=len(long_family) + 1)
        self.assertEqual(result.data[offset:offset + len(long_family) + 1],
                         long_family.encode("ascii") + b"\0")
        self.assertEqual(result.patches[0].new_pointer_va, result.patches[2].new_pointer_va)
        self.assertEqual(section.virtual_size, len(long_family) + 1)
        carrier_push = layout.va_to_file_offset(TEST_CATALOG[0].push_instruction_va, length=5)
        self.assertEqual(result.data[carrier_push], 0x68)
        self.assertEqual(struct.unpack_from("<I", result.data, carrier_push + 1)[0], pointer_va)
        control_push = layout.va_to_file_offset(TEST_CATALOG[1].push_instruction_va, length=5)
        self.assertEqual(struct.unpack_from("<I", result.data, control_push + 1)[0],
                         TEST_CATALOG[0].literal_va)
        self.assertEqual(source, make_synthetic_pe32())

    def test_native_identity_is_a_noop_without_added_section(self):
        source = make_synthetic_pe32()
        result = patch_family_initializer(
            source, (PhysicsBinding("Carrier", "Carrier"),), catalog=TEST_CATALOG
        )
        self.assertEqual(result.data, source)
        self.assertFalse(result.added_section)
        self.assertFalse(result.patches[0].changed)
        self.assertEqual(result.changed_ranges, ())

    def test_initializer_signature_mismatch_fails_closed(self):
        source = bytearray(make_synthetic_pe32())
        source[0x420] = 0x90
        with self.assertRaisesRegex(ValueError, "signature mismatch"):
            patch_family_initializer(
                bytes(source), (PhysicsBinding("Carrier", "LongTargetFamily"),),
                catalog=TEST_CATALOG,
            )


class RPhys3CopyLifecycleTests(unittest.TestCase):
    def test_validate_is_a_read_only_dry_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "MRallye.exe"
            source_data = make_synthetic_pe32()
            source.write_bytes(source_data)
            original_sha = hashlib.sha256(source_data).hexdigest()
            vehicle, mods = make_configs(root)
            before = {item.name for item in root.iterdir()}
            report = validate_binding_request(
                source,
                (PhysicsBinding("Carrier", "LongTargetFamily"),),
                vehicle,
                mods,
                expected_exe_sha256=original_sha,
                catalog=TEST_CATALOG,
            )
            self.assertEqual(report["status"], "VALID")
            self.assertEqual(report["mode"], "DRY_RUN_NO_FILES_WRITTEN")
            self.assertFalse(report["source_executable_modified"])
            self.assertTrue(report["output_copy_required"])
            self.assertNotEqual(report["planned_executable_sha256"], original_sha)
            self.assertTrue(report["planned_changed_ranges"])
            self.assertEqual({item.name for item in root.iterdir()}, before)

    def test_wrong_executable_hash_is_rejected_before_any_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "MRallye.exe"
            source.write_bytes(make_synthetic_pe32())
            vehicle, mods = make_configs(root)
            output = root / "MRallye_bound.exe"
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                apply_binding_copy(
                    source, output, (PhysicsBinding("Carrier", "LongTargetFamily"),),
                    vehicle, mods, catalog=TEST_CATALOG,
                )
            self.assertFalse(output.exists())
            self.assertFalse(source.with_name(output.name + ".original").exists())

    def test_apply_is_idempotent_and_restore_returns_copy_to_exact_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "MRallye.exe"
            original = make_synthetic_pe32()
            source.write_bytes(original)
            original_sha = hashlib.sha256(original).hexdigest()
            vehicle, mods = make_configs(root)
            output = root / "MRallye_bound.exe"
            bindings = (PhysicsBinding("Carrier", "LongTargetFamily"),)

            first = apply_binding_copy(
                source, output, bindings, vehicle, mods,
                expected_exe_sha256=original_sha, catalog=TEST_CATALOG,
            )
            self.assertEqual(first["status"], "APPLIED_TO_COPY")
            self.assertNotEqual(output.read_bytes(), original)
            self.assertEqual(source.read_bytes(), original)
            backup = output.with_name(output.name + ".original")
            manifest_path = output.with_name(output.name + ".physics-bind.json")
            self.assertEqual(backup.read_bytes(), original)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_sha256"], original_sha)
            self.assertEqual(manifest["status"], "applied")
            self.assertEqual(manifest["bindings"], [{
                "carrier_type": "Carrier", "physics_family": "LongTargetFamily"
            }])

            second = apply_binding_copy(
                source, output, bindings, vehicle, mods,
                expected_exe_sha256=original_sha, catalog=TEST_CATALOG,
            )
            self.assertEqual(second["status"], "ALREADY_APPLIED")
            self.assertEqual(restore_binding_copy(
                output, expected_source_sha256=original_sha
            )["status"], "RESTORED_COPY")
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(restore_binding_copy(
                output, expected_source_sha256=original_sha
            )["status"], "ALREADY_RESTORED")
            self.assertEqual(source.read_bytes(), original)

    def test_apply_refuses_source_overwrite_and_restore_refuses_tampered_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "MRallye.exe"
            original = make_synthetic_pe32()
            source.write_bytes(original)
            original_sha = hashlib.sha256(original).hexdigest()
            vehicle, mods = make_configs(root)
            binding = (PhysicsBinding("Carrier", "LongTargetFamily"),)
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                apply_binding_copy(
                    source, source, binding, vehicle, mods,
                    expected_exe_sha256=original_sha, catalog=TEST_CATALOG,
                )
            output = root / "MRallye_bound.exe"
            apply_binding_copy(
                source, output, binding, vehicle, mods,
                expected_exe_sha256=original_sha, catalog=TEST_CATALOG,
            )
            with self.assertRaisesRegex(ValueError, "expected retail executable build"):
                restore_binding_copy(output)
            tampered = bytearray(output.read_bytes())
            tampered[-1] ^= 0x01
            output.write_bytes(tampered)
            with self.assertRaisesRegex(ValueError, "changed since apply"):
                restore_binding_copy(output, expected_source_sha256=original_sha)


if __name__ == "__main__":
    unittest.main()
