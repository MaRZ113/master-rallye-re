from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import addon_runtime


class TwoAddonRuntimeCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan, cls.artifacts = addon_runtime._reference_plan(
            addon_runtime.DEFAULT_MANIFESTS,
            addon_runtime.DEFAULT_CAPABILITIES,
        )
        cls.addons = {row["physical_id"]: row for row in cls.plan["addons"]}

    def test_one_manifest_collection_composes_both_independent_addons(self) -> None:
        self.assertEqual(set(self.addons), {26, 27})
        self.assertEqual(self.plan["registry_layout"], {
            "record_count": 28,
            "vehicle_record_base": 4,
            "vehicle_record_stride": 0x34,
            "race_test_base": 0x5B4,
            "race_test_count": 39,
            "race_test_stride": 0x2C,
            "allocation_size": 0xC68,
        })
        self.assertEqual(self.plan["class_mapping"]["class_to_physical_ids"]["T1"],
                         [0, 1, 2, 3, 4, 5, 6, 26])
        self.assertEqual(self.plan["class_mapping"]["class_to_physical_ids"]["T2"],
                         [7, 8, 9, 10, 11, 12, 13, 27])
        self.assertEqual(self.plan["class_mapping"]["class_to_physical_ids"]["T3"],
                         list(range(14, 26)))
        self.assertEqual(self.plan["class_mapping"]["physical_id_to_class_local"]["14"],
                         {"vehicle_class": "T3", "class_local_index": 0})
        self.assertEqual(self.plan["class_mapping"]["physical_id_to_class_local"]["25"],
                         {"vehicle_class": "T3", "class_local_index": 11})

    def test_each_profile_keeps_its_physical_family_and_resource_roots(self) -> None:
        merc, qualifier = self.addons[26], self.addons[27]
        self.assertEqual((merc["vehicle_class"], merc["class_local_index"]), ("T1", 7))
        self.assertEqual((qualifier["vehicle_class"], qualifier["class_local_index"]), ("T2", 7))
        self.assertEqual(merc["identity"]["runtime_family"], "Mercedes")
        self.assertEqual(qualifier["identity"]["runtime_family"], "R5VQualifier")
        self.assertEqual(merc["identity"]["physics_family"], "Vehicles/Mercedes")
        self.assertEqual(qualifier["identity"]["physics_family"], "Vehicles/R5VQualifier")
        self.assertEqual(merc["assets"]["model_package_root"], "DataGx/Vehicles/Mercedes")
        self.assertEqual(qualifier["assets"]["model_package_root"],
                         "DataGx/Vehicles/R5VQualifier")
        self.assertNotEqual(merc["identity"]["runtime_family"],
                            qualifier["identity"]["runtime_family"])
        self.assertNotEqual(merc["assets"]["model_package_root"],
                            qualifier["assets"]["model_package_root"])

    def test_two_addon_policies_compose_without_changing_native_driver_policy(self) -> None:
        merc, qualifier = self.addons[26], self.addons[27]
        self.assertEqual(merc["audio"]["stock_audio_profile_id"], 0)
        self.assertEqual(qualifier["audio"]["stock_audio_profile_id"], 7)
        self.assertEqual(merc["race_colour_rgba"], [1.0, 0.0, 0.0, 1.0])
        self.assertEqual(qualifier["race_colour_rgba"], [1.0, 0.0, 1.0, 1.0])
        self.assertEqual(merc["unlock"]["stock_vehicle_id"], 3)
        self.assertEqual(qualifier["unlock"]["stock_vehicle_id"], 10)
        self.assertEqual(merc["results"]["display_name"], "JEAN-PIERRE STRUGO")
        self.assertEqual(qualifier["results"]["display_name"], "R5V TEST DRIVER")
        for addon in (merc, qualifier):
            for mode in ("quick_race", "rallye_cup", "master_rallye"):
                self.assertTrue(addon["ai_eligibility"][mode]["enabled"])
            self.assertFalse(addon["ai_eligibility"]["challenge"]["enabled"])
            self.assertNotIn("driver_id", addon["results"])

    def test_composition_artifacts_are_order_independent_and_keep_j0_hash(self) -> None:
        forward, _ = addon_runtime._reference_plan(
            addon_runtime.DEFAULT_MANIFESTS,
            addon_runtime.DEFAULT_CAPABILITIES,
        )
        reverse, reverse_artifacts = addon_runtime._reference_plan(
            list(reversed(addon_runtime.DEFAULT_MANIFESTS)),
            addon_runtime.DEFAULT_CAPABILITIES,
        )
        self.assertEqual(addon_runtime.canonical_json(forward),
                         addon_runtime.canonical_json(reverse))
        self.assertEqual(addon_runtime.sha256(self.artifacts["addon-plan.json"]),
                         addon_runtime.REFERENCE_PLAN_SHA256)
        self.assertEqual(self.artifacts, reverse_artifacts)
        overlay = json.loads(self.artifacts["frontend-overlay.plan.json"])
        self.assertEqual(len(overlay["vehicle_select_entries"]), 2)
        self.assertEqual({row["physical_id"] for row in overlay["vehicle_select_entries"]}, {26, 27})


if __name__ == "__main__":
    unittest.main()
