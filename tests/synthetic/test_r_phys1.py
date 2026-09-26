from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from master_rallye.errors import FormatError
from master_rallye.vehicle_config_analysis import (
    STATIC_RUNTIME_READERS,
    WHEEL_SOURCE_LINKAGE_EVIDENCE,
    WHEEL_SOURCE_LINKAGE_STATUS,
    build_vehicle_schema,
    classify_config_families_against_directories,
    compare_vehicle_configs,
    family_value_rows,
    inventory_vehicle_directories,
    parse_vehicle_config,
    wheel_spline_playback_local_offset,
)


def _xml(contents: str) -> bytes:
    return ("<Game><Broker>" + contents + "</Broker></Game>").encode("utf-8")


def _value(name: str, value: str, value_type: str = "Float") -> str:
    return f'<Value Name="{name}" Type="{value_type}" Value="{value}" />'


class VehicleConfigAnalysisTests(unittest.TestCase):
    def test_parser_keeps_exact_families_and_separates_global_and_numeric_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "vehicles.xml"
            path.write_bytes(_xml(
                _value("Vehicles/Trooper/Dimensions/WheelBase", "2.40000")
                + _value("Vehicles/NewRav/Dimensions/WheelBase", "2.50000")
                + _value("Vehicles/Tyres/tarmac0/PeakMu", "1.1")
                + _value("Vehicles/Car0/Dimensions/WheelBase", "2.8")
            ))
            parsed = parse_vehicle_config(path, build="fixture-a")
        self.assertEqual(set(parsed.families), {"Trooper", "NewRav"})
        self.assertIn("Tyres", parsed.excluded_families)
        self.assertIn("Car0", parsed.excluded_families)
        self.assertEqual(parsed.source, str(path))
        self.assertEqual(parsed.build, "fixture-a")
        self.assertEqual(len(parsed.sha256), 64)

    def test_malformed_path_or_missing_attributes_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.xml"
            path.write_bytes(_xml(_value("Vehicles/Trooper", "2.4")))
            with self.assertRaises(FormatError):
                parse_vehicle_config(path, build="fixture")
            path.write_bytes(b'<Game><Value Name="Vehicles/Trooper/Dimensions/WheelBase" Value="2.4"/></Game>')
            with self.assertRaises(FormatError):
                parse_vehicle_config(path, build="fixture")
            path.write_bytes(b"<Game>")
            with self.assertRaises(FormatError):
                parse_vehicle_config(path, build="fixture")

    def test_directory_inventory_preserves_exact_names_and_resource_roles(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vehicle = root / "CaseSensitiveCar"
            vehicle.mkdir()
            for name in ("car.dx", "complete.dx", "wheel.dx", "paint-tga.dxt", "car.txt", "collision.gxm"):
                (vehicle / name).write_bytes(b"fixture")
            inventory = inventory_vehicle_directories(root)
        self.assertEqual(inventory[0]["name"], "CaseSensitiveCar")
        self.assertTrue(inventory[0]["car_dx"])
        self.assertTrue(inventory[0]["complete_dx"])
        self.assertTrue(inventory[0]["wheel_dx"])
        self.assertEqual(inventory[0]["texture_files_dxt"], ["paint-tga.dxt"])
        self.assertEqual(inventory[0]["other_local_files"], ["car.txt"])
        self.assertIn("collision.gxm", inventory[0]["files"])

    def test_classification_is_case_sensitive_and_never_equates_alias_names(self):
        result = classify_config_families_against_directories(
            ["Trooper", "NewRav", "Rav4", "Bowler", "Tyres"],
            ["Trooper", "newrav", "BowlerAlpha"],
            possible_aliases={"Bowler": ("BowlerAlpha",)},
        )
        by_name = {row["config_family"]: row for row in result}
        self.assertEqual(by_name["Trooper"]["status"], "MATCHED_EXACT")
        self.assertEqual(by_name["NewRav"]["status"], "DIRECTORY_NAME_MISMATCH")
        self.assertEqual(by_name["NewRav"]["case_insensitive_directory_matches"], ["newrav"])
        self.assertEqual(by_name["Rav4"]["status"], "EXACT_CONFIG_ONLY")
        self.assertEqual(by_name["Bowler"]["status"], "POSSIBLE_ALIAS")
        self.assertEqual(by_name["Tyres"]["status"], "NON-VEHICLE_CONFIG_FAMILY")

    def test_config_comparison_reports_presence_type_text_and_numeric_deltas(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.xml"
            b = root / "b.xml"
            a.write_bytes(_xml(
                _value("Vehicles/Trooper/Dimensions/WheelBase", "2.4000")
                + _value("Vehicles/Trooper/Dimensions/Length", "4.0")
                + _value("Vehicles/Trooper/Dimensions/Count", "1", "Int")
            ))
            b.write_bytes(_xml(
                _value("Vehicles/Trooper/Dimensions/WheelBase", "2.4")
                + _value("Vehicles/Trooper/Dimensions/Length", "4.2")
                + _value("Vehicles/Trooper/Dimensions/Count", "1", "Float")
                + _value("Vehicles/Trooper/Dimensions/Width", "1.8")
            ))
            compared = compare_vehicle_configs(
                parse_vehicle_config(a, build="A"), "Trooper",
                parse_vehicle_config(b, build="B"), "Trooper",
            )
        rows = {row["path"]: row for row in compared["fields"]}
        self.assertEqual(rows["Dimensions/WheelBase"]["status"],
                         "NUMERIC_EQUAL_TEXT_DIFFERENT")
        self.assertEqual(rows["Dimensions/Length"]["numeric_delta_b_minus_a"], "0.2")
        self.assertEqual(rows["Dimensions/Count"]["status"], "TYPE_CHANGED")
        self.assertEqual(rows["Dimensions/Width"]["status"], "ADDED_IN_B")
        self.assertEqual(rows["Dimensions/WheelBase"]["runtime_reader_status"], "READ_BY_RETAIL_SPLINE_AI_PATH")

    def test_schema_coverage_retains_build_values_without_merging_family_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = root / "old.xml"
            new = root / "new.xml"
            old.write_bytes(_xml(_value("Vehicles/NewRav/Dimensions/WheelBase", "2.5")))
            new.write_bytes(_xml(_value("Vehicles/Rav4/Dimensions/WheelBase", "2.5")))
            schema = build_vehicle_schema([
                parse_vehicle_config(old, build="demo"),
                parse_vehicle_config(new, build="retail"),
            ])
        self.assertEqual({item["family"] for item in schema}, {"NewRav", "Rav4"})
        self.assertEqual({tuple(item["build_coverage"]) for item in schema}, {("demo",), ("retail",)})
        self.assertEqual(len(schema), 2)

    def test_wheel_spline_playback_offset_order_and_axis_components(self):
        offsets = [wheel_spline_playback_local_offset(
            index,
            wheel_base=2.4,
            track_width_front=1.65,
            track_width_rear=1.70,
            ride_height_front=0.05,
            ride_height_rear=0.08,
            front_max_droop=0.10,
            dynamic_vertical_sample=-0.20,
        ) for index in range(4)]
        self.assertEqual([(item["axle"], item["lateral_side"]) for item in offsets], [
            ("front", "negative"), ("front", "positive"),
            ("rear", "negative"), ("rear", "positive"),
        ])
        self.assertEqual([item["local_longitudinal"] for item in offsets], [1.2, 1.2, -1.2, -1.2])
        self.assertAlmostEqual(offsets[0]["local_lateral"], -0.825)
        self.assertAlmostEqual(offsets[1]["local_lateral"], 0.825)
        self.assertAlmostEqual(offsets[2]["local_lateral"], -0.85)
        self.assertAlmostEqual(offsets[3]["local_lateral"], 0.85)
        self.assertAlmostEqual(offsets[0]["local_vertical_component"], -0.15)
        self.assertAlmostEqual(offsets[2]["local_vertical_component"], -0.18)

    def test_wheel_index_bounds_and_physical_linkage_fail_closed(self):
        with self.assertRaises(ValueError):
            wheel_spline_playback_local_offset(
                4, wheel_base=2.4, track_width_front=1.6, track_width_rear=1.6,
                ride_height_front=0, ride_height_rear=0, front_max_droop=0.1,
                dynamic_vertical_sample=0,
            )
        self.assertEqual(WHEEL_SOURCE_LINKAGE_STATUS, "UNRESOLVED")
        self.assertIn("established", WHEEL_SOURCE_LINKAGE_EVIDENCE["physical_contact_path"])
        self.assertIn("spline", STATIC_RUNTIME_READERS["Dimensions/WheelBase"]["evidence"])


CORPORA = Path(r"D:\Game\Master Rallye\corpora")
CORPUS_AVAILABLE = (CORPORA / "retail" / "Data.sma_unpacked" / "DataGame" / "vehicles.xml").is_file()


@unittest.skipUnless(CORPUS_AVAILABLE, "requires read-only demo and retail corpora")
class VehicleConfigCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.scanner.r_phys1 import collect_analysis, corpus_paths

        cls.paths = corpus_paths(CORPORA)
        cls.analysis = collect_analysis(CORPORA)
        cls.docs = {
            build: parse_vehicle_config(cls.paths[build]["xml"], build=build)
            for build in ("8.4.1", "9.3.1", "9.10.0", "retail")
        }

    def test_retail_model_folder_inventory_exact_names_and_completeness(self):
        retail = self.analysis["retail"]
        names = retail["model_directory_names"]
        self.assertEqual(len(names), 26)
        self.assertEqual(set(names), {
            "Astero", "Bruno", "ChevyBlazer", "Forester", "forklift", "Frontera",
            "IceCream", "Jump", "Kamaz", "Kangoo", "KiaSportage", "LandCruiser",
            "Mattserati", "megane", "Navara", "NewRav", "Pajero", "Patrol",
            "RMonster", "SeatBuggy", "Simmbugghini", "Tata", "Terrano", "Ufo",
            "WildCat", "Xtrail",
        })
        folders = {entry["name"]: entry for entry in self.analysis["builds"]["retail"]["model_directory_inventory"]}
        self.assertTrue(all(folders[name]["car_dx"] and folders[name]["complete_dx"]
                            for name in names))
        self.assertFalse(folders["Ufo"]["wheel_dx"])
        self.assertGreater(folders["Navara"]["texture_count_dxt"], 0)
        self.assertIn("car.txt", folders["Navara"]["other_local_files"])

    def test_exact_retail_named_config_families_and_nonvehicle_namespace(self):
        families = self.analysis["retail"]["vehicle_family_names"]
        self.assertEqual(len(families), 35)
        self.assertIn("Trooper", families)
        self.assertIn("Navarabig", families)
        self.assertIn("Pajerostripe", families)
        self.assertNotIn("Tyres", families)
        self.assertEqual(self.analysis["retail"]["excluded_config_families"], ["Tyres"])

    def test_all_config_only_and_possible_alias_retail_families_are_reported(self):
        entries = self.analysis["retail"]["config_only_or_possible_aliases"]
        by_name = {entry["config_family"]: entry for entry in entries}
        expected = {
            "Bowler", "Cherokee", "Citroen", "Custom", "Megane2", "Mercedes",
            "Navarabig", "Pajerostripe", "Terios", "Trooper",
        }
        self.assertEqual(set(by_name), expected)
        self.assertEqual(by_name["Navarabig"]["status"], "POSSIBLE_ALIAS")
        self.assertEqual(by_name["Navarabig"]["possible_aliases"], ["Navara"])
        self.assertFalse(by_name["Navarabig"]["demo_corpus_matches"]["9.10.0"]["model_assets_present"])
        self.assertEqual(by_name["Trooper"]["demo_corpus_matches"]["8.4.1"]["matching_model_directories_case_insensitive"], ["Trooper"])
        self.assertEqual(by_name["Trooper"]["demo_corpus_matches"]["9.3.1"]["matching_model_directories_case_insensitive"], ["Trooper"])
        self.assertEqual(by_name["Mercedes"]["demo_corpus_matches"]["8.4.1"]["matching_model_directories_case_insensitive"], ["Mercedes"])
        self.assertEqual(by_name["Bowler"]["demo_corpus_matches"]["9.10.0"]["matching_model_directories_case_insensitive"], [])

    def test_case_only_directory_name_mismatches_are_separate_from_orphans(self):
        rows = self.analysis["retail"]["family_directory_classification"]
        mismatches = {row["config_family"]: row["case_insensitive_directory_matches"]
                      for row in rows if row["status"] == "DIRECTORY_NAME_MISMATCH"}
        self.assertEqual(mismatches, {
            "Chevyblazer": ["ChevyBlazer"], "Icecream": ["IceCream"],
            "Kiasportage": ["KiaSportage"], "Landcruiser": ["LandCruiser"],
            "Megane": ["megane"], "Newrav": ["NewRav"],
            "Rmonster": ["RMonster"], "Wildcat": ["WildCat"],
        })

    def test_trooper_known_wheel_config_matches_across_all_four_builds(self):
        fields = (
            "Dimensions/WheelBase", "Dimensions/TrackWidthFront", "Dimensions/TrackWidthRear",
            "Dimensions/WheelRadiusFront", "Dimensions/WheelRadiusRear",
            "Suspension/Front/RideHeight", "Suspension/Rear/RideHeight",
            "Suspension/Front/MaxDroop", "Suspension/Rear/MaxDroop",
        )
        expected = {
            "Dimensions/WheelBase": "2.4",
            "Dimensions/TrackWidthFront": "1.65",
            "Dimensions/TrackWidthRear": "1.65",
            "Dimensions/WheelRadiusFront": "0.38",
            "Dimensions/WheelRadiusRear": "0.38",
            "Suspension/Front/RideHeight": "0.05",
            "Suspension/Rear/RideHeight": "0.05",
            "Suspension/Front/MaxDroop": "0.1",
            "Suspension/Rear/MaxDroop": "0.1",
        }
        for build, document in self.docs.items():
            rows = {row["path"]: row["value"] for row in family_value_rows(document, "Trooper")}
            for field in fields:
                self.assertEqual(float(rows[field]), float(expected[field]), f"{build} {field}")
        counts = {build: len(self.docs[build].families["Trooper"]) for build in self.docs}
        self.assertEqual(counts, {"8.4.1": 121, "9.3.1": 150, "9.10.0": 147, "retail": 147})

    def test_trooper_full_config_diff_preserves_presence_and_changed_fields(self):
        result = compare_vehicle_configs(self.docs["9.3.1"], "Trooper", self.docs["retail"], "Trooper")
        self.assertEqual(result["field_count"], 160)
        self.assertEqual(result["status_counts"]["ADDED_IN_B"], 10)
        self.assertEqual(result["status_counts"]["REMOVED_IN_B"], 13)
        self.assertEqual(result["status_counts"]["VALUE_CHANGED"], 28)
        self.assertIn("Chassis/TotalMass", {row["path"] for row in result["fields"]})
        self.assertEqual(next(row for row in result["fields"] if row["path"] == "Chassis/TotalMass")["runtime_reader_status"],
                         "PRESENT_BUT_USAGE_UNRESOLVED")

    def test_jump_build_evolution_and_navara_retail_control(self):
        jump = {build: {row["path"]: row["value"] for row in family_value_rows(doc, "Jump")}
                for build, doc in self.docs.items() if "Jump" in doc.families}
        self.assertEqual(float(jump["8.4.1"]["Dimensions/WheelBase"]), 2.5)
        self.assertEqual(float(jump["9.3.1"]["Dimensions/TrackWidthFront"]), 1.7)
        self.assertEqual(float(jump["9.10.0"]["Dimensions/TrackWidthFront"]), 1.6)
        self.assertEqual(float(jump["9.10.0"]["Suspension/Front/RideHeight"]), 0.08)
        self.assertEqual(float(jump["retail"]["Dimensions/TrackWidthRear"]), 1.6)
        navara_910 = {row["path"]: row["value"] for row in family_value_rows(self.docs["9.10.0"], "Navara")}
        navara_retail = {row["path"]: row["value"] for row in family_value_rows(self.docs["retail"], "Navara")}
        self.assertEqual(float(navara_910["Dimensions/WheelBase"]), 2.6)
        self.assertEqual(float(navara_retail["Dimensions/WheelBase"]), 2.8)
        self.assertEqual(float(navara_910["Dimensions/TrackWidthFront"]), 1.7)
        self.assertEqual(float(navara_retail["Dimensions/TrackWidthFront"]), 1.7)
        self.assertEqual(float(navara_910["Suspension/Front/RideHeight"]), 0.05)
        self.assertEqual(float(navara_retail["Suspension/Front/RideHeight"]), 0.05)

    def test_rav4_and_newrav_are_kept_as_separate_config_names(self):
        self.assertNotIn("Rav4", self.docs["retail"].families)
        self.assertIn("Newrav", self.docs["retail"].families)
        self.assertNotIn("Rav4", self.docs["9.3.1"].families)
        self.assertIn("Rav4", self.analysis["builds"]["9.3.1"]["model_directory_names"])
        self.assertIn("Rav4", self.docs["8.4.1"].families)
        self.assertIn("Newrav", self.docs["9.3.1"].families)

    def test_full_schema_and_runtime_reader_classification_are_provenance_bounded(self):
        schema = build_vehicle_schema(list(self.docs.values()))
        trooper_mass = next(row for row in schema if row["full_path"] == "Vehicles/Trooper/Chassis/TotalMass")
        self.assertEqual(trooper_mass["build_coverage"], ["8.4.1", "9.3.1", "9.10.0", "retail"])
        self.assertEqual(trooper_mass["runtime_reader_status"], "PRESENT_BUT_USAGE_UNRESOLVED")
        wheel_keys = {
            "Dimensions/WheelBase", "Dimensions/TrackWidthFront", "Dimensions/TrackWidthRear",
            "Suspension/Front/RideHeight", "Suspension/Rear/RideHeight", "Suspension/Front/MaxDroop",
        }
        self.assertEqual(set(STATIC_RUNTIME_READERS), wheel_keys)
        self.assertEqual(WHEEL_SOURCE_LINKAGE_STATUS, "UNRESOLVED")
        for build, document in self.docs.items():
            car_roots = [name for name in document.excluded_families if name.casefold().startswith("car")]
            self.assertEqual(car_roots, [], f"{build} has no literal Vehicles/CarN XML family root")

    def test_complete_model_wheel_geometry_oracle_keeps_vehicle_and_build_provenance(self):
        from master_rallye.bridge2_analysis import analyze_complete_wheel_file

        fixtures = {
            "Trooper": self.paths["9.3.1"]["vehicle_dirs"] / "Trooper" / "complete.gxm",
            "Rav4": self.paths["9.3.1"]["vehicle_dirs"] / "Rav4" / "complete.gxm",
            "Jump": self.paths["9.3.1"]["vehicle_dirs"] / "Jump" / "complete.gxm",
            "Navara": self.paths["9.10.0"]["vehicle_dirs"] / "Navara" / "complete.gxm",
        }
        parsed = {name: analyze_complete_wheel_file(path, path.with_suffix(".txt"))
                  for name, path in fixtures.items()}
        self.assertEqual({len(value.meshes) for value in parsed.values()}, {4})
        trooper_centers = [mesh.dx_aabb_center for mesh in parsed["Trooper"].meshes]
        x_values = sorted({round(point[0], 6) for point in trooper_centers})
        z_values = sorted({round(point[2], 6) for point in trooper_centers})
        self.assertEqual(len(x_values), 3)  # the two left centers differ by ~1.2e-7
        self.assertAlmostEqual(x_values[0], -0.752512, places=5)
        self.assertAlmostEqual(x_values[-1], 0.752617, places=5)
        self.assertEqual(z_values, [-1.183466, 1.211832])
        self.assertEqual(parsed["Navara"].meshes[0].span_source, "sidecar")


if __name__ == "__main__":
    unittest.main()
