from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from master_rallye.vehicle_runtime_identity import (
    HUMAN_CONTEXT,
    build_identity_layers,
    scan_corpus_metadata,
    summarize_ghidra_xrefs,
    trooper_survival_profile,
)


def _comparison(family: str, changed: set[str], total: int = 147) -> dict:
    fields = [
        {"path": path, "status": "VALUE_CHANGED", "value_a": "1", "value_b": "2"}
        for path in sorted(changed)
    ]
    fields.extend(
        {"path": f"Stable/{family}/{index}", "status": "EXACT_EQUAL"}
        for index in range(total - len(fields))
    )
    from collections import Counter
    counts = Counter(row["status"] for row in fields)
    return {
        "family_a": family, "build_a": "9.10.0", "build_b": "retail",
        "field_count": len(fields), "status_counts": dict(counts), "fields": fields,
    }


class VehicleRuntimeIdentityTests(unittest.TestCase):
    def test_text_and_compiled_metadata_scan_ascii_and_utf16le_with_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data_game = root / "retail" / "Data.sma_unpacked" / "DataGame"
            data_gx = root / "retail" / "Data.sma_unpacked" / "DataGx"
            data_scene = root / "retail" / "Data.sma_unpacked" / "DataScene"
            data_game.mkdir(parents=True)
            data_gx.mkdir(parents=True)
            data_scene.mkdir(parents=True)
            xml = data_game / "frontend.xml"
            xml.write_text(
                '<Value Name="Frontend/QuickRace/Car0" Value="16" />\n'
                '<Value Name="Race/Car3/CarType" Type="String" Value="Trooper" />',
                encoding="utf-8",
            )
            (data_scene / "DefaultVehicleParamBrokerRegistration.xml").write_text(
                '<Value Name="CarModelDataFile" Value="RMonster" />', encoding="utf-8"
            )
            binary = data_gx / "compiled.dx"
            binary.write_bytes("Vehicles/Car%d/Dimensions/WheelBase\0CarType".encode("utf-16le"))

            scan = scan_corpus_metadata(root)

        self.assertEqual(scan["text_file_count"], 2)
        self.assertEqual(scan["compiled_metadata_file_count"], 1)
        self.assertGreaterEqual(scan["hit_file_count"], 2)
        self.assertTrue(any(row["category"] == "frontend_car_slot" for row in scan["text_hits"]))
        self.assertTrue(any(row["category"] == "numeric_race_path" for row in scan["text_hits"]))
        self.assertTrue(any(row["category"] == "car_model_data_file" for row in scan["text_hits"]))
        assignments = [row for row in scan["text_hits"]
                       if row["category"] == "scene_race_car_type_assignment"]
        self.assertEqual(assignments[0]["participant_index"], 3)
        self.assertEqual(assignments[0]["value_type"], "String")
        self.assertEqual(assignments[0]["value"], "Trooper")
        wide = [row for row in scan["compiled_metadata_hits"]
                if row["encoding_detection"] == "UTF16LE_CANDIDATE"]
        self.assertTrue(any(row["category"] == "numeric_vehicle_path" for row in wide))
        self.assertTrue(all(len(row["source_sha256"]) == 64 for row in scan["text_hits"] + wide))

    def test_trooper_delta_separates_control_shared_from_trooper_only(self):
        trooper = {"Chassis/MomentOfInertia", "DamageParams/MaxEngineDamage", "Suspension/Front/ToeIn"}
        jump = {"Chassis/MomentOfInertia", "DamageParams/MaxEngineDamage"}
        navara = {"Chassis/MomentOfInertia", "DamageParams/MaxEngineDamage"}
        analysis = {"config_comparisons": [
            _comparison("Trooper", trooper), _comparison("Jump", jump), _comparison("Navara", navara),
        ]}
        result = trooper_survival_profile(analysis)
        self.assertEqual(result["trooper_value_changed_path_count"], 3)
        self.assertEqual(result["control_shared_path_count"], 2)
        self.assertEqual(result["trooper_only_control_paths"], ["Suspension/Front/ToeIn"])
        self.assertEqual(result["runtime_consumption_status"], "UNRESOLVED_FOR_NAMED_FAMILY_FIELDS")

    def test_identity_map_keeps_config_folder_ui_race_and_human_evidence_separate(self):
        rphys1 = {"builds": {
            "retail": {
                "family_names": ["Trooper", "Ufo"],
                "model_directory_inventory": [
                    {"name": "Ufo", "car_dx": True, "complete_dx": True, "wheel_dx": False},
                    {"name": "forklift", "car_dx": True, "complete_dx": True, "wheel_dx": True},
                ],
            },
        }}
        scan = {"text_hits": [
            {"category": "frontend_car_slot", "match": "Frontend/QuickRace/Car0"},
            {"category": "scene_race_car_type_assignment", "build": "retail",
             "path": "retail/DataScene/fixture.xml", "participant_index": 0,
             "value_type": "String", "value": "Trooper", "match": "Race/Car0/CarType"},
        ]}
        ghidra = {"relevant_strings": [{"value": "Race/Car%d/CarType", "address": "006e6f18"}]}
        result = build_identity_layers(rphys1, scan, ghidra)
        retail = result["builds"]["retail"]
        self.assertTrue(retail["Trooper"]["config_family_present_casefold"])
        self.assertFalse(retail["Trooper"]["model_directory_casefold_names"])
        self.assertTrue(retail["forklift"]["model_directory_exact_names"])
        self.assertFalse(retail["forklift"]["config_family_present_casefold"])
        self.assertFalse(retail["Ufo"]["model_file_roles"]["wheel_dx"])
        self.assertEqual(result["runtime_physics_object"]["status"], "NOT_BOUND_TO_NAMED_FAMILY")
        self.assertEqual(result["frontend_saved_or_default_selections"]["interpretation"].split(";")[0], "UI/save namespace only")
        self.assertEqual(
            result["race_participant_namespace"]["scene_car_type_summary"]["retail"][
                "values_matching_named_config_families_casefold"
            ],
            {"Trooper": 1},
        )
        self.assertTrue(all("user-supplied" in row["source"] for row in result["human_context"]))
        self.assertEqual(len(HUMAN_CONTEXT), 2)

    def test_xref_summary_preserves_sites_without_claiming_read_or_write_semantics(self):
        payload = {
            "program": "MRallye.exe", "image_base": "00400000", "string_count": 3,
            "strings": [
                {"address": "006e4598", "value": "Vehicles/Car", "xref_count": 1,
                 "xrefs": [{"from": "00493633", "type": "READ", "function": "FUN_00493600", "read": True, "write": False}]},
                {"address": "006e6f18", "value": "Race/Car%d/CarType", "xref_count": 1,
                 "xrefs": [{"from": "004c0b7d", "type": "DATA", "function": "FUN_004c0b20", "read": False, "write": False}]},
                {"address": "006e4450", "value": "CarModelDataFile", "xref_count": 1, "xrefs": []},
            ],
        }
        result = summarize_ghidra_xrefs(payload)
        self.assertEqual(result["status"], "GHIDRA_STATIC_STRING_XREFS")
        self.assertEqual(len(result["relevant_strings"]), 3)
        self.assertEqual(result["relevant_strings"][1]["value"], "Race/Car%d/CarType")
        self.assertEqual(result["relevant_strings"][1]["xrefs"][0]["write"], False)


if __name__ == "__main__":
    unittest.main()
