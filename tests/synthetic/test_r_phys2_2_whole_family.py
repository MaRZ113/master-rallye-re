from __future__ import annotations

import unittest
from pathlib import Path

from master_rallye.vehicle_config_analysis import compare_vehicle_configs, parse_vehicle_config
from master_rallye.vehicle_family_broker import analyze_family_identity
from master_rallye.vehicle_family_redirect import (
    BASE_FAMILY_READER_ENTRY,
    BASE_READER_RETURN,
    CAR_WRITER_RETURN_BREAKPOINT,
    FAMILY_CATALOG_ENTRY_SIZE,
    FAMILY_CATALOG_NAME_FIELD_BASE_OFFSET,
    FAMILY_CATALOG_POINTER_READ_BREAKPOINT,
    HUMAN_NAVARA_BROKER_OBSERVATION,
    HUMAN_TROOPER_WHOLE_FAMILY_OBSERVATION,
    HUMAN_RUNTIME_EVIDENCE_STATUS,
    MANAGED_FAMILY_STRING_CAPACITY_OFFSET,
    MANAGED_FAMILY_STRING_DATA_POINTER_OFFSET,
    MANAGED_FAMILY_STRING_LENGTH_OFFSET,
    MANAGED_FAMILY_STRING_SIZE,
    OVERLAY_READER_ENTRY,
    OVERLAY_READER_RETURN,
    REDIRECT_PLAN_STATUS,
    RUNTIME_EXPERIMENT_STATUS,
    build_whole_family_redirect_plan,
)


CORPORA = Path(r"D:\Game\Master Rallye\corpora")
RETAIL_DATA = CORPORA / "retail" / "Data.sma_unpacked" / "DataGame"
RETAIL_BROKER_INPUTS_AVAILABLE = (
    (RETAIL_DATA / "vehicles.xml").is_file()
    and (RETAIL_DATA / "Modifications.xml").is_file()
)


class RPhys22RedirectPlanTests(unittest.TestCase):
    def test_human_runtime_observation_records_only_observed_claims(self):
        evidence = HUMAN_NAVARA_BROKER_OBSERVATION
        self.assertEqual(evidence.executable_sha256,
                         "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4")
        self.assertEqual(evidence.breakpoint_eip, 0x00493E30)
        self.assertEqual(evidence.caller_return_address, 0x0044F0D2)
        self.assertEqual(evidence.ebp_at_hit, 0)
        self.assertEqual(evidence.family_object_address, 0x001AF838)
        self.assertEqual(evidence.family_name, "Navara")
        self.assertEqual(evidence.overlay_text_visible_on_stack, "Navara/Player1")
        self.assertFalse(evidence.overlay_reader_call_confirmed_in_capture)
        self.assertEqual(evidence.evidence_status, HUMAN_RUNTIME_EVIDENCE_STATUS)

    def test_successful_trooper_redirect_records_runtime_result_without_reusing_heap_addresses(self):
        evidence = HUMAN_TROOPER_WHOLE_FAMILY_OBSERVATION
        self.assertEqual(evidence.executable_sha256,
                         "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4")
        self.assertEqual(evidence.breakpoint_eip, 0x0044EE69)
        self.assertEqual(evidence.participant_index, 0)
        self.assertEqual(evidence.carrier_type_id, 7)
        self.assertEqual(evidence.catalog_pointer_slot_address_for_this_run, 0x03488A78)
        self.assertEqual(evidence.original_name_pointer_address_for_this_run, 0x03489640)
        self.assertEqual((evidence.original_family, evidence.redirected_family),
                         ("Navara", "Trooper"))
        self.assertEqual(evidence.base_reader_entry, BASE_FAMILY_READER_ENTRY)
        self.assertEqual(evidence.base_reader_caller_return, BASE_READER_RETURN)
        self.assertEqual(evidence.overlay_family, "Trooper/Player1")
        self.assertEqual(evidence.overlay_reader_entry, OVERLAY_READER_ENTRY)
        self.assertEqual(evidence.runtime_writer, 0x004938C0)
        self.assertTrue(evidence.race_started)
        self.assertTrue(evidence.wheel_placement_corrected)
        self.assertTrue(evidence.handling_changed_from_carrier)
        self.assertEqual(evidence.evidence_status, HUMAN_RUNTIME_EVIDENCE_STATUS)
        self.assertEqual(RUNTIME_EXPERIMENT_STATUS, HUMAN_RUNTIME_EVIDENCE_STATUS)

    def test_managed_string_offsets_match_fixed_build_reader_accesses(self):
        base = HUMAN_NAVARA_BROKER_OBSERVATION.family_object_address
        self.assertEqual(MANAGED_FAMILY_STRING_SIZE, 0x10)
        self.assertEqual(base + MANAGED_FAMILY_STRING_DATA_POINTER_OFFSET, 0x001AF83C)
        self.assertEqual(base + MANAGED_FAMILY_STRING_LENGTH_OFFSET, 0x001AF840)
        self.assertEqual(base + MANAGED_FAMILY_STRING_CAPACITY_OFFSET, 0x001AF844)

    def test_catalog_pointer_plan_redirects_base_and_overlay_together(self):
        plan = build_whole_family_redirect_plan("Navara", "Trooper", 0)
        self.assertEqual(plan["source_type_id"], 7)
        self.assertEqual(plan["target_type_ids_in_initialized_catalog"], ())
        self.assertEqual(
            plan["catalog_name_pointer_slot_offset"],
            FAMILY_CATALOG_NAME_FIELD_BASE_OFFSET + 7 * FAMILY_CATALOG_ENTRY_SIZE,
        )
        self.assertEqual(plan["source_pointer_read_breakpoint"], FAMILY_CATALOG_POINTER_READ_BREAKPOINT)
        self.assertEqual(plan["base_reader_entry"], BASE_FAMILY_READER_ENTRY)
        self.assertEqual(plan["base_reader_return"], BASE_READER_RETURN)
        self.assertEqual(plan["overlay_reader_entry"], OVERLAY_READER_ENTRY)
        self.assertEqual(plan["overlay_reader_return"], OVERLAY_READER_RETURN)
        self.assertEqual(plan["overlay_text_checkpoint"], 0x0044EE25)
        self.assertEqual(plan["runtime_car_path"], "Vehicles/Car0")
        self.assertEqual(plan["overlay_player_number"], 1)
        self.assertEqual(plan["replacement_c_string"], "Trooper")
        self.assertEqual(plan["replacement_c_string_bytes_with_nul"], 8)
        self.assertEqual(plan["restore_after_family_strings_created_breakpoint"], 0x0044EE25)
        self.assertEqual(plan["car_writer_return_breakpoint"], CAR_WRITER_RETURN_BREAKPOINT)
        self.assertEqual(plan["status"], REDIRECT_PLAN_STATUS)
        self.assertEqual(RUNTIME_EXPERIMENT_STATUS, HUMAN_RUNTIME_EVIDENCE_STATUS)

    def test_nonzero_participant_keeps_source_type_separate_from_runtime_car_index(self):
        plan = build_whole_family_redirect_plan("Navara", "Trooper", 1)
        self.assertEqual(plan["source_type_id"], 7)
        self.assertEqual(plan["runtime_car_path"], "Vehicles/Car1")
        self.assertEqual(plan["overlay_player_number"], 2)

    def test_plan_rejects_uninitialized_source_type_without_creating_target_id(self):
        with self.assertRaises(ValueError):
            build_whole_family_redirect_plan("Trooper", "Navara", 0)
        with self.assertRaises(ValueError):
            build_whole_family_redirect_plan("Navara", "Trooper", -1)


@unittest.skipUnless(RETAIL_BROKER_INPUTS_AVAILABLE,
                     "requires read-only retail XML corpus")
class RPhys22RetailConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vehicle_config = parse_vehicle_config(RETAIL_DATA / "vehicles.xml", build="retail")
        cls.modifications_config = parse_vehicle_config(
            RETAIL_DATA / "Modifications.xml", build="retail"
        )

    def test_trooper_has_complete_reader_groups_and_matching_navara_shape(self):
        navara = self.vehicle_config.families["Navara"]
        trooper = self.vehicle_config.families["Trooper"]
        self.assertEqual(len(navara), 147)
        self.assertEqual(len(trooper), 147)
        self.assertEqual(set(navara), set(trooper))
        self.assertEqual({path: row["type"] for path, row in navara.items()},
                         {path: row["type"] for path, row in trooper.items()})

        expected_groups = {
            "Chassis": 16,
            "DamageParams": 25,
            "Dimensions": 8,
            "Engine": 45,
            "Steering": 5,
            "Suspension": 48,
        }
        audit = analyze_family_identity(
            self.vehicle_config, self.modifications_config, "Trooper"
        )
        self.assertEqual(audit.base_group_counts, expected_groups)
        self.assertEqual(audit.missing_base_groups, ())
        self.assertEqual(audit.base_modification_fields, ())
        self.assertEqual(len(audit.base_missing_modification_fields), 13)
        self.assertEqual(len(audit.player1_modification_fields), 13)
        self.assertEqual(audit.player1_missing_modification_fields, ())
        self.assertEqual(len(audit.player2_modification_fields), 13)
        self.assertEqual(audit.player2_missing_modification_fields, ())

    def test_retained_trooper_overlay_is_complete_and_not_a_navara_hybrid(self):
        for player in (1, 2):
            prefix = f"Player{player}/Modifications/"
            navara = {
                path[len(prefix):]: value
                for path, value in self.modifications_config.families["Navara"].items()
                if path.startswith(prefix)
            }
            trooper = {
                path[len(prefix):]: value
                for path, value in self.modifications_config.families["Trooper"].items()
                if path.startswith(prefix)
            }
            with self.subTest(player=player):
                self.assertEqual(len(navara), 13)
                self.assertEqual(len(trooper), 13)
                self.assertEqual(set(navara), set(trooper))
                self.assertEqual(navara, trooper)

    def test_navara_trooper_distinguishing_values_are_repeatable(self):
        navara = self.vehicle_config.families["Navara"]
        trooper = self.vehicle_config.families["Trooper"]
        comparison = compare_vehicle_configs(
            self.vehicle_config, "Navara", self.vehicle_config, "Trooper"
        )
        self.assertEqual(comparison["status_counts"], {
            "EXACT_EQUAL": 105,
            "VALUE_CHANGED": 42,
        })
        changed_by_group = {}
        for row in comparison["fields"]:
            if row["status"] == "VALUE_CHANGED":
                changed_by_group[row["subsystem"]] = changed_by_group.get(row["subsystem"], 0) + 1
        self.assertEqual(changed_by_group, {
            "Chassis": 4,
            "DamageParams": 17,
            "Dimensions": 3,
            "Engine": 6,
            "Suspension": 12,
        })
        expected = {
            "Dimensions/WheelBase": ("2.80000", "2.40000"),
            "Dimensions/TrackWidthFront": ("1.70000", "1.65000"),
            "Dimensions/TrackWidthRear": ("1.70000", "1.65000"),
            "Chassis/TotalMass": ("1320.00000", "1350.00000"),
            "Engine/PeakTorque": ("275.00000", "340.00000"),
            "Engine/GearRatioDiff": ("3.92000", "3.82000"),
            "Suspension/Front/AuxRollStiffness": ("3000.00000", "7000.00000"),
            "Suspension/Rear/AuxRollStiffness": ("3000.00000", "7000.00000"),
            "Suspension/Front/RideHeight": ("0.05000", "0.05000"),
            "Suspension/Rear/RideHeight": ("0.05000", "0.05000"),
        }
        for path, values in expected.items():
            with self.subTest(path=path):
                self.assertEqual((navara[path]["value"], trooper[path]["value"]), values)

        self.assertTrue(all(navara[path] == trooper[path]
                            for path in navara if path.startswith("Steering/")))


if __name__ == "__main__":
    unittest.main()
