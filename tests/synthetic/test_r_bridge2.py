from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from master_rallye.bridge2_analysis import (
    RAW_DX_COMPATIBILITY_MATRIX,
    analyze_complete_wheel_geometry,
    analyze_complete_wheel_file,
    audit_vehicle_config_roots,
    compare_dx_assets,
    parse_vehicle_properties,
    validate_compatibility_matrix,
    validate_transfer_provenance,
    wheel_dimension_properties,
)
from master_rallye.errors import FormatError


def _node(name: str, start: int, count: int, *, node_type: int = 1) -> bytes:
    encoded = name.encode("ascii")
    return struct.pack("<BBHIIH", node_type, 1, 0, start, count, len(encoded)) + encoded


def _complete_gxm(*, node_type: int = 1) -> bytes:
    record_count = 8
    points_dx = (
        (-1.0, 0.0, 2.0), (1.0, 0.0, 2.0),
        (-1.0, 0.0, -2.0), (1.0, 0.0, -2.0),
    )
    c_points = []
    triangle_indices = []
    for center_x, center_y, center_z in points_dx:
        corner_points = (
            (center_x - 0.5, center_y, center_z),
            (center_x + 0.5, center_y, center_z),
            (center_x, center_y + 0.5, center_z),
        )
        first = len(c_points)
        # inverse of the observed DX transform (x, z, -y)
        c_points.extend((x, -z, y) for x, y, z in corner_points)
        triangle_indices.append((first, first + 1, first + 2))

    vector_a_count = record_count * 3
    vectors_a = b"".join(struct.pack("<3f", *axis) for axis in (
        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    ) for _ in range(record_count))
    header = struct.pack("<8I", 0x20702, 0, 0, 0, vector_a_count, 0,
                         record_count, len(c_points))
    records = bytearray()
    for index in range(record_count):
        wheel = index // 2
        c_indices = triangle_indices[wheel]
        records.extend(struct.pack("<10I", 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF,
                                   0xFFFFFFFF, *c_indices, 0, 1, 2))
        if index < record_count - 1:
            records.extend(b"\xff" * 12)
    vectors_c = b"".join(struct.pack("<3f", *point) for point in c_points)
    hierarchy = struct.pack("<H", 5) + b"Model"
    for wheel in range(4):
        hierarchy += _node(f"wheel $cylinder_fixture{wheel}", wheel * 2, 2,
                           node_type=node_type)
    return header + vectors_a + b"\xff" * 12 + bytes(records) + vectors_c + hierarchy


class Bridge2GeometryTests(unittest.TestCase):
    def test_named_wheel_meshes_use_exact_spans_and_coordinate_transform(self):
        parsed = analyze_complete_wheel_geometry(_complete_gxm(), source="fixture complete.gxm")
        self.assertEqual(parsed.hierarchy_status, "ACCEPTED")
        self.assertEqual(parsed.triangle_record_count, 8)
        self.assertEqual(len(parsed.meshes), 4)
        self.assertEqual([mesh.record_count for mesh in parsed.meshes], [2, 2, 2, 2])
        self.assertEqual(parsed.meshes[0].dx_aabb_center, (-1.0, 0.25, 2.0))
        self.assertEqual(parsed.meshes[1].dx_aabb_center, (1.0, 0.25, 2.0))
        self.assertEqual(parsed.meshes[2].dx_aabb_center, (-1.0, 0.25, -2.0))
        self.assertEqual(parsed.meshes[3].dx_aabb_center, (1.0, 0.25, -2.0))
        self.assertTrue(all(len(mesh.unique_vector_c_indices) == 3 for mesh in parsed.meshes))

    def test_unsupported_hierarchy_uses_only_explicit_sidecar_spans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gxm = root / "complete.gxm"
            gxm.write_bytes(_complete_gxm(node_type=3))
            sidecar = root / "complete.txt"
            sidecar.write_text("\n".join(
                f"moMesh(Name [wheel $cylinder_fixture{i}] Index {i * 2} Size 2)"
                for i in range(4)
            ), encoding="latin-1")
            parsed = analyze_complete_wheel_file(gxm, sidecar)
        self.assertEqual(parsed.hierarchy_status, "UNSUPPORTED_OR_REJECTED")
        self.assertIn("unsupported GXM node type/version 3/1", parsed.hierarchy_error)
        self.assertTrue(all(mesh.span_source == "sidecar" for mesh in parsed.meshes))

    def test_unsupported_hierarchy_without_sidecar_fails_closed(self):
        with self.assertRaisesRegex(FormatError, "no sidecar fallback"):
            analyze_complete_wheel_geometry(_complete_gxm(node_type=3), source="unknown hierarchy")

    def test_vehicle_xml_reader_keeps_exact_property_names_and_values(self):
        xml = (
            '<Game><Broker>'
            '<Value Name="Vehicles/Navara/Dimensions/TrackWidthFront" Type="Float" Value="1.70000"/>'
            '<Value Name="Vehicles/Navara/Dimensions/TrackWidthRear" Type="Float" Value="1.70000"/>'
            '<Value Name="Vehicles/Navara/Suspension/Front/RideHeight" Type="Float" Value="0.05000"/>'
            '<Value Name="Vehicles/Other/Dimensions/TrackWidthFront" Type="Float" Value="9.0"/>'
            '</Broker></Game>'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vehicles.xml"
            path.write_text(xml, encoding="utf-8")
            properties = parse_vehicle_properties(path, "Navara")
        self.assertEqual(properties["Dimensions/TrackWidthFront"],
                         {"type": "Float", "value": "1.70000"})
        self.assertEqual(wheel_dimension_properties(properties), {
            "Dimensions/TrackWidthFront": "1.70000",
            "Dimensions/TrackWidthRear": "1.70000",
            "Suspension/Front/RideHeight": "0.05000",
        })

    def test_vehicle_root_audit_does_not_guess_car_index_aliases(self):
        xml = (
            '<Game><Value Name="Vehicles/Navara/Dimensions/WheelBase" Type="Float" Value="2.8"/>'
            '<Value Name="Vehicles/Trooper/Dimensions/WheelBase" Type="Float" Value="2.4"/>'
            '</Game>'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vehicles.xml"
            path.write_text(xml, encoding="utf-8")
            audit = audit_vehicle_config_roots(path)
        self.assertEqual(audit["status"], "NO_NUMERIC_CAR_ROOTS_FOUND")
        self.assertEqual(audit["named_vehicle_roots"], ["Navara", "Trooper"])
        self.assertEqual(audit["alias_resolution"], "UNRESOLVED")


class Bridge2EvidenceRecordTests(unittest.TestCase):
    def test_raw_dx_compatibility_matrix_is_complete_and_uses_known_statuses(self):
        validate_compatibility_matrix(RAW_DX_COMPATIBILITY_MATRIX)
        self.assertEqual(RAW_DX_COMPATIBILITY_MATRIX["8.4.1"]["retail"], "REJECTED_BY_STATIC")
        self.assertEqual(RAW_DX_COMPATIBILITY_MATRIX["9.3.1"]["retail"], "REJECTED_BY_STATIC")
        self.assertEqual(RAW_DX_COMPATIBILITY_MATRIX["9.10.0"]["retail"], "CONFIRMED_BY_RUNTIME")
        self.assertEqual(RAW_DX_COMPATIBILITY_MATRIX["8.4.1"]["9.10.0"], "UNKNOWN")
        self.assertEqual(RAW_DX_COMPATIBILITY_MATRIX["9.3.1"]["9.10.0"], "UNKNOWN")

    def test_transfer_record_does_not_invent_missing_file_provenance(self):
        record = {
            "vehicle": "Trooper",
            "evidence": "HUMAN_RUNTIME_CONFIRMED",
            "source_build": "UNKNOWN_FROM_USER_REPORT",
            "source_hashes": None,
            "cooker_build": "9.10.0",
            "generated_hashes": None,
            "target_build": "retail",
            "target_slot": "Navara",
        }
        status = validate_transfer_provenance(record)
        self.assertTrue(status["valid"])
        self.assertFalse(status["source_hashes_verified"])
        self.assertFalse(status["generated_hashes_verified"])
        self.assertFalse(status["source_build_identified"])
        self.assertTrue(status["target_slot_identified"])

    def test_transfer_record_rejects_malformed_hashes(self):
        record = {"evidence": "HUMAN_RUNTIME_CONFIRMED", "source_hashes": ["0" * 63]}
        with self.assertRaisesRegex(ValueError, "malformed SHA-256"):
            validate_transfer_provenance(record)

    def test_transfer_record_keeps_unreported_target_slot_unknown(self):
        record = {
            "evidence": "HUMAN_RUNTIME_CONFIRMED",
            "source_build": "UNKNOWN_FROM_USER_REPORT",
            "target_slot": "UNKNOWN_FROM_USER_REPORT",
            "source_hashes": None,
            "generated_hashes": None,
        }
        status = validate_transfer_provenance(record)
        self.assertFalse(status["target_slot_identified"])


CORPORA = Path(r"D:\Game\Master Rallye\corpora")
DEMO_841 = CORPORA / "demo-8.4.1" / "DataGx" / "Vehicles"
DEMO_931 = CORPORA / "demo-9.3.1" / "DataGx" / "Vehicles"
DEMO_910 = CORPORA / "demo-9.10.0" / "DataGx" / "Vehicles"
RETAIL = CORPORA / "retail" / "Data.sma_unpacked" / "DataGx" / "Vehicles"


@unittest.skipUnless((DEMO_841 / "Jump" / "wheel.dx").is_file()
                     and (DEMO_931 / "Jump" / "wheel.dx").is_file()
                     and (DEMO_910 / "Jump" / "wheel.dx").is_file()
                     and (RETAIL / "Jump" / "wheel.dx").is_file(),
                     "requires read-only demo and retail vehicle corpora")
class Bridge2CorpusTests(unittest.TestCase):
    def test_910_vehicle_models_emit_retail_revision_and_parse(self):
        from master_rallye.dx import parse_dx_bytes

        dx_files = sorted(DEMO_910.rglob("*.dx"))
        self.assertEqual(len(dx_files), 18)
        for path in dx_files:
            data = path.read_bytes()
            self.assertEqual(struct.unpack_from("<I", data, 4)[0], 135, str(path))
            parse_dx_bytes(data, str(path))

    def test_jump_wheel_four_generation_format_evolution(self):
        from master_rallye.bridge2_analysis import compare_dx_assets

        p841 = DEMO_841 / "Jump" / "wheel.dx"
        p931 = DEMO_931 / "Jump" / "wheel.dx"
        p910 = DEMO_910 / "Jump" / "wheel.dx"
        pretail = RETAIL / "Jump" / "wheel.dx"
        first = compare_dx_assets(p841.read_bytes(), p931.read_bytes())
        self.assertEqual(first["byte_diff"]["changed_byte_count"], 1)
        self.assertTrue(first["render"]["local_indices_equal"])
        self.assertTrue(first["draw_material_raw"]["exact_equal"])
        self.assertTrue(first["collision_raw"]["exact_equal"])

        late = compare_dx_assets(p910.read_bytes(), pretail.read_bytes())
        self.assertEqual(late["first"]["header"][1], 135)
        self.assertEqual(late["second"]["header"][1], 135)
        self.assertTrue(late["render"]["local_indices_equal"])
        self.assertTrue(late["render"]["global_indices_equal"])
        self.assertTrue(late["draw_material_raw"]["exact_equal"])
        self.assertTrue(late["collision_raw"]["exact_equal"])
        self.assertEqual(late["first"]["retail_parser"]["status"], "ACCEPTED")

    def test_navara_wheel_dx_is_byte_identical_demo910_to_retail(self):
        demo = (DEMO_910 / "Navara" / "wheel.dx").read_bytes()
        retail = (RETAIL / "Navara" / "wheel.dx").read_bytes()
        self.assertEqual(demo, retail)

    def test_complete_jump_wheel_longitudinal_and_lateral_centers_are_stable_but_height_changes(self):
        for vehicle in ("Jump",):
            paths = [root / vehicle / "complete.gxm" for root in (DEMO_841, DEMO_931, DEMO_910)]
            parsed = [analyze_complete_wheel_file(path, path.with_suffix(".txt")) for path in paths]
            centers = [sorted(mesh.dx_aabb_center for mesh in item.meshes) for item in parsed]
            for old, middle, late in zip(*centers):
                self.assertAlmostEqual(old[0], middle[0], places=6)
                self.assertAlmostEqual(middle[0], late[0], places=6)
                self.assertAlmostEqual(old[2], middle[2], places=6)
                self.assertAlmostEqual(middle[2], late[2], places=6)
                self.assertAlmostEqual(middle[1] - old[1], 0.0, places=6)
                self.assertAlmostEqual(late[1] - middle[1], 0.451111, places=5)

    def test_jump_910_to_retail_wheel_byte_changes_are_fully_in_position_and_normal_arrays(self):
        first = (DEMO_910 / "Jump" / "wheel.dx").read_bytes()
        second = (RETAIL / "Jump" / "wheel.dx").read_bytes()
        comparison = compare_dx_assets(first, second)
        regions = comparison["byte_diff"]["same_layout_regions"]
        self.assertIsNotNone(regions)
        self.assertTrue(regions["valid_partition"])
        self.assertEqual(comparison["byte_diff"]["changed_byte_count"], 485)
        self.assertEqual(regions["changed_byte_count"], 485)
        self.assertEqual(regions["unexplained_changed_byte_count"], 0)
        self.assertEqual(regions["regions"]["positions"], 260)
        self.assertEqual(regions["regions"]["normals"], 225)
        for name, count in regions["regions"].items():
            if name not in ("positions", "normals"):
                self.assertEqual(count, 0, name)

    def test_navara_910_vs_retail_only_wheel_is_exactly_identical(self):
        for role in ("car", "complete"):
            first = (DEMO_910 / "Navara" / f"{role}.dx").read_bytes()
            second = (RETAIL / "Navara" / f"{role}.dx").read_bytes()
            self.assertFalse(compare_dx_assets(first, second)["byte_diff"]["exact_equal"])
        wheel_first = (DEMO_910 / "Navara" / "wheel.dx").read_bytes()
        wheel_second = (RETAIL / "Navara" / "wheel.dx").read_bytes()
        self.assertTrue(compare_dx_assets(wheel_first, wheel_second)["byte_diff"]["exact_equal"])

    def test_vehicle_config_exposes_track_width_fields_but_not_hardpoint_vectors(self):
        from master_rallye.bridge2_analysis import parse_vehicle_properties, wheel_dimension_properties

        xml = CORPORA / "retail" / "Data.sma_unpacked" / "DataGame" / "vehicles.xml"
        props = wheel_dimension_properties(parse_vehicle_properties(xml, "Navara"))
        self.assertEqual(props["Dimensions/TrackWidthFront"], "1.70000")
        self.assertEqual(props["Dimensions/TrackWidthRear"], "1.70000")
        self.assertEqual(props["Dimensions/WheelBase"], "2.80000")
        self.assertFalse(any("Hardpoint" in name for name in props))
        audit = audit_vehicle_config_roots(xml)
        self.assertEqual(audit["status"], "NO_NUMERIC_CAR_ROOTS_FOUND")
        self.assertIn("Navara", audit["named_vehicle_roots"])
        self.assertEqual(len(audit["numeric_car_roots"]), 0)


if __name__ == "__main__":
    unittest.main()
