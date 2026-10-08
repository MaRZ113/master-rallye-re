from __future__ import annotations

import hashlib
import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import build_vehicle_multislot_i0 as i0
import build_vehicle_multislot_i1 as i1
import vehicle_multislot_i1_runtime_package as package


class VehicleMultiSlotI1ProfileTests(unittest.TestCase):
    def test_id27_is_a_distinct_authored_family_without_physical_aliasing(self) -> None:
        profile = i1.ID27_RECORD
        self.assertEqual((profile.slot_id, profile.vehicle_class, profile.local_index), (27, 1, 7))
        self.assertEqual(i0.class_local_to_physical(1, 7), 27)
        self.assertEqual(i0.physical_to_class_local(27), (1, 7))
        self.assertNotEqual(i0.class_local_to_physical(1, 7), 7)
        self.assertNotEqual(i0.class_local_to_physical(1, 7), 14)
        self.assertEqual(profile.internal_name, "R5VQualifier")
        self.assertEqual(profile.runtime_family, "R5VQualifier")
        self.assertEqual(profile.model_family, "R5VQualifier")
        self.assertEqual(profile.wheel_family, "R5VQualifier")
        self.assertEqual(profile.physics_family, "Vehicles/R5VQualifier")
        self.assertEqual(profile.asset_package, "DataGx/Vehicles/R5VQualifier")
        self.assertEqual(profile.donor_id, 7)
        self.assertNotEqual(profile.runtime_family, "Navara")

    def test_qualifier_keeps_i0_unlock_audio_ai_and_neighbor_identities(self) -> None:
        self.assertEqual(i1.ID27_RECORD.unlock_policy, i0.ID27_RECORD.unlock_policy)
        self.assertEqual(i1.ID27_RECORD.unlock_policy, "mirror-stock-vehicle-id-10")
        self.assertEqual(i0.unlock_oracle(27), 10)
        self.assertEqual(i0.audio_profile_for(27), 7)
        self.assertEqual(i0.RESULTS_ID27, "ID27 SLOT PROOF")
        self.assertEqual(i1.RESULTS_LABEL, "R5V TEST DRIVER")
        self.assertEqual(i1.DISPLAY_MANUFACTURER, "R5V")
        self.assertEqual(i1.DISPLAY_MODEL, "T2 QUALIFIER")
        self.assertEqual(i1.DISPLAY_COMBINED, "R5V T2 QUALIFIER")

        self.assertEqual(i0.T1_PHYSICAL_IDS, (*range(7), 26))
        self.assertEqual(i0.T2_PHYSICAL_IDS, (*range(7, 14), 27))
        self.assertEqual(i0.T3_BASE_PHYSICAL_IDS, tuple(range(14, 21)))
        for mode in ("quickrace", "rallye_cup", "master_rallye"):
            with self.subTest(mode=mode):
                self.assertEqual(i0.pool_for_mode(mode, 1), [7, 8, 9, 10, 11, 12, 13, 27])
                self.assertEqual(i0.pool_for_mode(mode, 1).count(27), 1)
                self.assertNotIn(14, i0.pool_for_mode(mode, 1))

        self.assertEqual(i0.physical_to_class_local(26), (0, 7))
        self.assertEqual(i0.physical_to_class_local(25), (2, 11))
        self.assertEqual(i0.audio_profile_for(26), 0)
        self.assertEqual(i1.PROFILE, "i1-id27-r5v-qualifier-independent-t2-family")

    def test_family_xml_overlay_clones_only_into_the_independent_namespace(self) -> None:
        source = (
            b'<?xml version="1.0"?>\n'
            b'<Game>\n<Broker>\n'
            b'<Value Name="Vehicles/Navara/Dimensions/WheelBase" Type="Float" Value="2.75"/>\n'
            b'<Value Name="Vehicles/Astero/Dimensions/WheelBase" Type="Float" Value="2.50"/>\n'
            b'</Broker>\n</Game>\n'
        )
        output, count = package._family_xml_overlay(source, source_label="synthetic vehicles.xml")
        self.assertEqual(count, 1)
        root = ET.fromstring(output)
        values = {node.get("Name"): node.get("Value") for node in root.iter("Value")}
        self.assertEqual(values["Vehicles/Navara/Dimensions/WheelBase"], "2.75")
        self.assertEqual(values["Vehicles/R5VQualifier/Dimensions/WheelBase"], "2.75")
        self.assertEqual(values["Vehicles/Astero/Dimensions/WheelBase"], "2.50")
        self.assertEqual(sum(name.startswith("Vehicles/R5VQualifier/") for name in values), 1)
        with self.assertRaises(package.PackageError):
            package._family_xml_overlay(output, source_label="already extended XML")

    def test_independent_asset_payload_and_physics_paths(self) -> None:
        h2_root = package.DEFAULT_H2_ROOT
        retail_data = package.DEFAULT_RETAIL_DATA
        data_sma = h2_root / "Data.sma"
        if not h2_root.is_dir() or not retail_data.is_dir() or not data_sma.is_file():
            self.skipTest("retail/H.2 runtime asset fixtures are not packaged")
        payloads, metadata = package._build_payloads(data_sma=data_sma,
                                                      retail_data_root=retail_data)
        self.assertIn("DataGx/Vehicles/R5VQualifier/car.dx", payloads)
        self.assertIn("DataGx/Vehicles/R5VQualifier/complete.dx", payloads)
        self.assertIn("DataGx/Vehicles/R5VQualifier/wheel.dx", payloads)
        self.assertIn("DataGx/Vehicles/R5VQualifier/paintjeep-tga.dxt", payloads)
        self.assertNotIn("DataGx/Vehicles/Navara/car.dx", payloads)
        self.assertNotIn("DataGx/Vehicles/Navara/wheel.dx", payloads)
        self.assertEqual(metadata["asset_file_count"], 98)
        self.assertEqual(metadata["physics"]["family_path_prefix"],
                         "Vehicles/R5VQualifier/")
        self.assertEqual(metadata["physics"]["values_cloned"], 147)
        self.assertFalse(metadata["physics"]["semantic_delta"])
        self.assertEqual(metadata["player_modifications"]["family_path_prefix"],
                         "Vehicles/R5VQualifier/")
        canary = payloads["DataGx/Vehicles/R5VQualifier/paintjeep-tga.dxt"]
        self.assertEqual(hashlib.sha256(canary).hexdigest(),
                         "76e3e81a7bf9dd32c7d96a1131d3343e4586459bbbc0d52af7f783c3a1e6d44d")
        decoded = package.decode_rgba_pixels(package.parse_dxt_bytes(canary, "qualifier canary"))
        self.assertEqual(decoded, bytes((255, 64, 210, 255)) * 256)

    def test_manifest_declares_exact_i1_boundary_and_preserved_i0_identities(self) -> None:
        source_path = i1.DEFAULT_SOURCE
        if not source_path.is_file():
            self.skipTest("pristine retail executable fixture is not packaged")
        candidate, manifest = i1.make_candidate(source_path.read_bytes())
        self.assertEqual(hashlib.sha256(candidate).hexdigest(),
                         "90abfbf9825f1cc7acebb3a1a2811a179e6474f2406433854e1ffdbc60bdd955")
        self.assertEqual(len(candidate), i0.RETAIL_SIZE)
        self.assertEqual(manifest["status"], "READY_FOR_HUMAN_RUNTIME")
        self.assertEqual(manifest["layout"]["record_count"], 28)
        self.assertEqual(manifest["class_mapping"]["T2_local7"], 27)
        self.assertEqual(manifest["profiles"][0]["physical_id"], 26)
        self.assertEqual(manifest["profiles"][0]["runtime_family"], "Mercedes")
        self.assertEqual(manifest["profiles"][0]["results_display"], "JEAN-PIERRE STRUGO")
        self.assertEqual(manifest["profiles"][1]["runtime_family"], "R5VQualifier")
        self.assertEqual(manifest["profiles"][1]["results_display"], "R5V TEST DRIVER")
        self.assertEqual(manifest["ai_pools"]["quickrace_t2"], [7, 8, 9, 10, 11, 12, 13, 27])
        self.assertFalse(manifest["runtime_architecture"]["randomizer_present"])
        self.assertFalse(manifest["runtime_architecture"]["participant_count_changed"])
        self.assertTrue(manifest["runtime_architecture"]["id27_independent_family_qualification"])
        self.assertFalse(manifest["runtime_architecture"]["id27_is_real_independent_t2_payload"])
        self.assertTrue(manifest["runtime_architecture"]["id27_model_and_physics_content_are_navara_derived"])
        self.assertFalse(manifest["higher_phase_boundary"]["r5v_i_full_pass"])
        self.assertFalse(manifest["higher_phase_boundary"]["r5v_j_started"])
        self.assertEqual(manifest["higher_phase_boundary"]["i0_slot_architecture"],
                         "CONFIRMED_BY_RUNTIME / FULL PASS / CLOSED")
        self.assertEqual(manifest["higher_phase_boundary"]["i1_real_t2_payload"],
                         "AUTHORED_R5VQUALIFIER_FAMILY; NAVARA_DERIVED; NOT_HISTORICAL_CONTENT")

        derived_path = REPO / "research/vehicles/multislot/i1-candidate-manifest.json"
        derived = json.loads(derived_path.read_text(encoding="utf-8"))
        serialized = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        self.assertEqual(derived["source_patch_manifest_sha256"], hashlib.sha256(serialized).hexdigest())
        self.assertFalse(derived["raw_patch_bytes_included"])
        self.assertEqual(derived["candidate"]["sha256"], hashlib.sha256(candidate).hexdigest())
        self.assertEqual(len(derived["patch_operations"]), len(manifest["operations"]))
        for recorded, operation in zip(derived["patch_operations"], manifest["operations"]):
            before = bytes.fromhex(operation["original_bytes"])
            after = bytes.fromhex(operation["replacement_bytes"])
            self.assertEqual(recorded["name"], operation["name"])
            self.assertEqual(recorded["category"], operation["category"])
            self.assertEqual(recorded["file_offset"], operation["file_offset"])
            self.assertEqual(recorded["original_length"], len(before))
            self.assertEqual(recorded["replacement_length"], len(after))
            self.assertEqual(recorded["original_sha256"], hashlib.sha256(before).hexdigest())
            self.assertEqual(recorded["replacement_sha256"], hashlib.sha256(after).hexdigest())
            self.assertNotIn("original_bytes", recorded)
            self.assertNotIn("replacement_bytes", recorded)

        restored = bytearray(candidate)
        for operation in reversed(manifest["operations"]):
            start = operation["file_offset"]
            before = bytes.fromhex(operation["original_bytes"])
            after = bytes.fromhex(operation["replacement_bytes"])
            self.assertEqual(restored[start:start + len(after)], after)
            restored[start:start + len(before)] = before
        self.assertEqual(hashlib.sha256(restored).hexdigest(), i0.H2_SHA256)
        self.assertEqual(manifest["parent_candidate"]["sha256"], i0.H2_SHA256)


if __name__ == "__main__":
    unittest.main()
