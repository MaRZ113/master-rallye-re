from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from master_rallye.vehicle_config_analysis import parse_vehicle_config
from master_rallye.vehicle_family_broker import (
    BROKER_GROUP_PAIRS,
    DIRECT_FAMILY_GROUPS,
    FAMILY_BY_TYPE_ID,
    PLAYER_MODIFICATION_FIELDS,
    analyze_family_identity,
    build_family_config_report,
    family_for_type_id,
    family_type_ids,
    named_vehicle_path,
    player_overlay_path,
    runtime_car_path,
    write_family_config_report,
)


def _write_xml(path: Path, values: list[str]) -> None:
    path.write_text("<Game>" + "".join(values) + "</Game>", encoding="utf-8")


def _value(name: str) -> str:
    return f'<Value Name="{name}" Type="Float" Value="1.0" />'


class RPhys21NamedFamilyTests(unittest.TestCase):
    def test_broker_group_reader_writer_matrix_is_symmetric(self):
        self.assertEqual(len(BROKER_GROUP_PAIRS), 8)
        self.assertEqual(len({pair.group for pair in BROKER_GROUP_PAIRS}), 8)
        self.assertEqual(
            [pair.group for pair in BROKER_GROUP_PAIRS],
            [
                "Dimensions", "Chassis", "Steering", "Engine",
                "Suspension/Front", "Suspension/Rear", "DamageParams", "Modifications",
            ],
        )
        self.assertTrue(all(pair.reader.startswith("FUN_") and pair.writer.startswith("FUN_")
                            for pair in BROKER_GROUP_PAIRS))

    def test_named_family_path_preserves_exact_name_and_rejects_path_injection(self):
        self.assertEqual(named_vehicle_path("Navara"), "Vehicles/Navara")
        self.assertEqual(named_vehicle_path("Newrav"), "Vehicles/Newrav")
        for invalid in ("", " Navara", "Navara ", "A/B", "A\\B", ".", ".."):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                named_vehicle_path(invalid)

    def test_runtime_path_uses_nonnegative_participant_number(self):
        self.assertEqual(runtime_car_path(0), "Vehicles/Car0")
        self.assertEqual(runtime_car_path(1), "Vehicles/Car1")
        self.assertEqual(runtime_car_path(12), "Vehicles/Car12")
        for invalid in (-1, True, "1"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                runtime_car_path(invalid)  # type: ignore[arg-type]

    def test_type_ids_are_separate_from_config_names_and_selectable_slots(self):
        self.assertEqual(len(FAMILY_BY_TYPE_ID), 25)
        self.assertEqual(family_for_type_id(7), "Navara")
        self.assertEqual(family_for_type_id(9), "Jump")
        self.assertIsNone(family_for_type_id(25))
        self.assertEqual(family_type_ids("Trooper"), ())
        self.assertEqual(family_type_ids("forklift"), ())

    def test_family_type_id_and_participant_index_are_distinct_namespaces(self):
        # Navara's family/type ID is 7; the ordinary first participant still
        # writes to Car0 because the race-loop index is passed independently.
        self.assertEqual(family_for_type_id(7), "Navara")
        self.assertEqual(runtime_car_path(0), "Vehicles/Car0")
        self.assertNotEqual(runtime_car_path(7), runtime_car_path(0))

    def test_player_overlay_is_a_distinct_family_subtree(self):
        self.assertEqual(player_overlay_path("Navara", 1), "Vehicles/Navara/Player1")
        self.assertEqual(player_overlay_path("Trooper", 2), "Vehicles/Trooper/Player2")
        for invalid in (3, True, "1"):
            with self.subTest(player_number=invalid), self.assertRaises(ValueError):
                player_overlay_path("Navara", invalid)  # type: ignore[arg-type]

    def test_family_coverage_reports_all_direct_groups_and_player_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vehicle_path = root / "vehicles.xml"
            mods_path = root / "Modifications.xml"
            base_values = [
                _value(f"Vehicles/Trooper/{group}/Test")
                for group in DIRECT_FAMILY_GROUPS
            ]
            mod_values = [
                _value(f"Vehicles/Trooper/Player{player}/Modifications/{field}")
                for player in (1, 2)
                for field in PLAYER_MODIFICATION_FIELDS
            ]
            _write_xml(vehicle_path, base_values)
            _write_xml(mods_path, mod_values)
            vehicle_doc = parse_vehicle_config(vehicle_path, build="fixture")
            mods_doc = parse_vehicle_config(mods_path, build="fixture")
            audit = analyze_family_identity(vehicle_doc, mods_doc, "Trooper")

        self.assertTrue(audit.family_config_present)
        self.assertEqual(audit.missing_base_groups, ())
        self.assertEqual(audit.base_field_count, len(DIRECT_FAMILY_GROUPS))
        self.assertEqual(audit.base_modification_fields, ())
        self.assertEqual(len(audit.base_missing_modification_fields), 13)
        self.assertEqual(audit.player1_missing_modification_fields, ())
        self.assertEqual(audit.player2_missing_modification_fields, ())
        self.assertEqual(len(audit.player1_modification_fields), 13)
        self.assertEqual(len(audit.player2_modification_fields), 13)

    def test_base_family_and_player_modifications_are_not_merged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vehicle_path = root / "vehicles.xml"
            mods_path = root / "Modifications.xml"
            _write_xml(vehicle_path, [_value("Vehicles/Navara/Dimensions/WheelBase")])
            _write_xml(mods_path, [_value("Vehicles/Navara/Player1/Modifications/Engine/BrakeBias")])
            vehicle_doc = parse_vehicle_config(vehicle_path, build="fixture")
            mods_doc = parse_vehicle_config(mods_path, build="fixture")
            audit = analyze_family_identity(vehicle_doc, mods_doc, "Navara")

        self.assertIn("Dimensions/WheelBase", vehicle_doc.families["Navara"])
        self.assertNotIn("Player1/Modifications/Engine/BrakeBias", vehicle_doc.families["Navara"])
        self.assertIn("Player1/Modifications/Engine/BrakeBias", mods_doc.families["Navara"])
        self.assertEqual(audit.player1_modification_fields, ("Engine/BrakeBias",))

    def test_forklift_config_case_does_not_promote_model_or_slot_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vehicle_path = root / "vehicles.xml"
            mods_path = root / "Modifications.xml"
            _write_xml(vehicle_path, [_value("Vehicles/Navara/Dimensions/WheelBase")])
            _write_xml(mods_path, [])
            vehicle_doc = parse_vehicle_config(vehicle_path, build="fixture")
            mods_doc = parse_vehicle_config(mods_path, build="fixture")
            audit = analyze_family_identity(vehicle_doc, mods_doc, "forklift")

        self.assertFalse(audit.family_config_present)
        self.assertEqual(audit.family_type_ids, ())
        self.assertEqual(audit.selectable_slot_status, "UNRESOLVED")

    def test_report_generation_keeps_source_provenance_and_distinct_identity_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vehicle_path = root / "vehicles.xml"
            mods_path = root / "Modifications.xml"
            _write_xml(vehicle_path, [_value("Vehicles/Trooper/Dimensions/WheelBase")])
            _write_xml(mods_path, [])
            vehicle_doc = parse_vehicle_config(vehicle_path, build="fixture")
            mods_doc = parse_vehicle_config(mods_path, build="fixture")
            report = build_family_config_report(vehicle_doc, mods_doc, ("Trooper",))
            json_path, markdown_path = write_family_config_report(report, root / "out")
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(loaded["vehicle_config_source"]["sha256"], vehicle_doc.sha256)
        self.assertEqual(loaded["modifications_config_source"]["sha256"], mods_doc.sha256)
        row = loaded["families"][0]
        self.assertTrue(row["family_config_present"])
        self.assertEqual(row["family_type_ids"], [])
        self.assertEqual(row["selectable_slot_status"], "UNRESOLVED")
        self.assertEqual(row["base_modification_fields"], [])
        self.assertIn("Trooper", markdown)
        self.assertIn("UNRESOLVED", markdown)


CORPORA = Path(r"D:\Game\Master Rallye\corpora")
RETAIL_DATA = CORPORA / "retail" / "Data.sma_unpacked" / "DataGame"
RETAIL_BROKER_INPUTS_AVAILABLE = (
    (RETAIL_DATA / "vehicles.xml").is_file()
    and (RETAIL_DATA / "Modifications.xml").is_file()
)


@unittest.skipUnless(RETAIL_BROKER_INPUTS_AVAILABLE, "requires read-only retail XML corpus")
class RPhys21RetailConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vehicle_config = parse_vehicle_config(RETAIL_DATA / "vehicles.xml", build="retail")
        cls.modifications_config = parse_vehicle_config(RETAIL_DATA / "Modifications.xml", build="retail")

    def test_navara_jump_trooper_completeness_and_forklift_inverse_case(self):
        expected_groups = {
            "Chassis": 16,
            "DamageParams": 25,
            "Dimensions": 8,
            "Engine": 45,
            "Steering": 5,
            "Suspension": 48,
        }
        for family, type_id in (("Navara", 7), ("Jump", 9), ("Trooper", None)):
            with self.subTest(family=family):
                audit = analyze_family_identity(
                    self.vehicle_config, self.modifications_config, family
                )
                self.assertTrue(audit.family_config_present)
                self.assertEqual(audit.base_field_count, 147)
                self.assertEqual(audit.base_group_counts, expected_groups)
                self.assertEqual(audit.missing_base_groups, ())
                self.assertEqual(audit.family_type_ids, () if type_id is None else (type_id,))
                self.assertEqual(audit.base_modification_fields, ())
                self.assertEqual(len(audit.base_missing_modification_fields), 13)
                self.assertEqual(len(audit.player1_modification_fields), 13)
                self.assertEqual(len(audit.player2_modification_fields), 13)
                self.assertEqual(audit.player1_missing_modification_fields, ())
                self.assertEqual(audit.player2_missing_modification_fields, ())

        forklift = analyze_family_identity(
            self.vehicle_config, self.modifications_config, "forklift"
        )
        self.assertFalse(forklift.family_config_present)
        self.assertEqual(forklift.family_type_ids, ())
        self.assertEqual(forklift.base_field_count, 0)
        self.assertEqual(len(forklift.missing_base_groups), len(DIRECT_FAMILY_GROUPS))
        self.assertEqual(forklift.player1_modification_fields, ())
        self.assertEqual(forklift.player2_modification_fields, ())


if __name__ == "__main__":
    unittest.main()
