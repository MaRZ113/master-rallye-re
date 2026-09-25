from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from master_rallye.gxm import (parse_gxm_geometry_prefix_bytes,
                                parse_gxm_prefix_bytes,
                                parse_gxm_triangle_prefix_bytes)
from tools.scanner.r_demo_hull_invariants import validate_pair


def make_gxm(triangles=((0, 1, 2), (3, 4, 5)), point_count=7) -> bytes:
    record_count = len(triangles)
    header = struct.pack("<8I", 0x00020702, 0, 0, 0, record_count * 3, 0,
                         record_count, point_count)
    unit_normal = struct.pack("<3f", 0.0, 0.0, 1.0)
    vector_a = unit_normal * (record_count * 3)
    out = bytearray(header + vector_a + b"\xff" * 12)
    for index, tri in enumerate(triangles):
        out += struct.pack("<10I", 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF,
                           *tri, index * 3, index * 3 + 1, index * 3 + 2)
        if index + 1 < record_count:
            out += b"\xff" * 12
    points = ((0, 0, 0), (1, 0, 0), (0, 1, 0),
              (2, 0, 0), (3, 0, 0), (2, 1, 0), (9, 9, 9))[:point_count]
    for point in points:
        out += struct.pack("<3f", *point)
    return bytes(out)


def update_positions(data: bytes, updates: dict[int, tuple[float, float, float]]) -> bytes:
    out = bytearray(data)
    prefix = parse_gxm_prefix_bytes(data)
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
    for index, point in updates.items():
        struct.pack_into("<3f", out, triangles.vector_c_offset + index * 12, *point)
    return bytes(out)


def translated_first_hull(data: bytes) -> bytes:
    baseline_points = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
    return update_positions(data, {i: (p[0] + 0.4, p[1], p[2])
                                   for i, p in enumerate(baseline_points)})


class HullInvariantHighLevelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.sidecar = Path(self.temp.name) / "car.txt"
        self.sidecar.write_text(
            "moMesh(Name [$chull(Test)] Index 0 Size 1)\n"
            "moMesh(Name [other] Index 1 Size 1)\n", encoding="latin-1")
        self.baseline = make_gxm()

    def tearDown(self):
        self.temp.cleanup()

    def validate(self, candidate, *, sidecar=None):
        return validate_pair(self.baseline, candidate, sidecar or self.sidecar,
                             "$chull(Test)")

    def test_rigid_translation_passes_all_high_level_checks(self):
        report = self.validate(translated_first_hull(self.baseline))
        self.assertEqual(report["status"], "FLAT_GXM_HULL_SOURCE_INVARIANTS_PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertAlmostEqual(report["translation"]["translation_xyz"][0], 0.4)

    def test_topology_change_fails_closed(self):
        candidate = bytearray(translated_first_hull(self.baseline))
        prefix = parse_gxm_prefix_bytes(self.baseline)
        geometry = parse_gxm_geometry_prefix_bytes(self.baseline, prefix)
        layout = parse_gxm_triangle_prefix_bytes(self.baseline, prefix, geometry)
        struct.pack_into("<I", candidate, layout.record_offset + 24, 6)
        report = self.validate(bytes(candidate))
        self.assertFalse(report["checks"]["record_topology_unchanged"])
        self.assertEqual(report["status"], "REJECTED")

    def test_vertex_sharing_conflict_fails_closed(self):
        baseline = make_gxm(((0, 1, 2), (0, 4, 5)))
        self.baseline = baseline
        report = self.validate(translated_first_hull(baseline))
        self.assertFalse(report["checks"]["no_hull_c_positions_shared_with_outside_records"])
        self.assertEqual(report["outside_records_reusing_hull_c_indices"], [1])

    def test_degenerate_candidate_triangle_fails_closed(self):
        candidate = update_positions(self.baseline, {
            0: (0.4, 0.0, 0.0), 1: (1.4, 0.0, 0.0), 2: (0.4, 0.0, 0.0)})
        report = self.validate(candidate)
        self.assertFalse(report["checks"]["all_source_faces_remain_nondegenerate"])

    def test_normal_inconsistency_fails_closed(self):
        candidate = update_positions(self.baseline, {
            0: (0.4, 0.0, 0.0), 1: (1.4, 0.0, 0.0), 2: (0.4, 0.5, 0.5)})
        report = self.validate(candidate)
        self.assertFalse(report["checks"]["triangle_normals_preserved"])
        self.assertFalse(report["checks"]["vector_a_face_alignment_preserved"])

    def test_area_inconsistency_fails_closed(self):
        candidate = update_positions(self.baseline, {
            0: (0.4, 0.0, 0.0), 1: (1.4, 0.0, 0.0), 2: (0.4, 2.0, 0.0)})
        report = self.validate(candidate)
        self.assertFalse(report["checks"]["triangle_areas_preserved_within_float32_noise"])

    def test_unexpected_c_dependency_fails_closed(self):
        candidate = update_positions(translated_first_hull(self.baseline), {6: (10.0, 9.0, 9.0)})
        report = self.validate(candidate)
        self.assertFalse(report["checks"]["all_and_only_hull_c_positions_changed"])
        self.assertFalse(report["checks"]["all_changes_confined_to_hull_vector_c_bytes"])

    def test_count_mismatch_fails_closed(self):
        candidate = bytearray(self.baseline)
        struct.pack_into("<I", candidate, 28, 6)  # candidate claims a different C count
        with self.assertRaisesRegex(ValueError, "layout differs"):
            self.validate(bytes(candidate))

    def test_out_of_range_sidecar_interval_fails_closed(self):
        bad_sidecar = Path(self.temp.name) / "bad.txt"
        bad_sidecar.write_text("moMesh(Name [$chull(Test)] Index 2 Size 1)\n", encoding="latin-1")
        with self.assertRaisesRegex(ValueError, "range outside GXM"):
            self.validate(self.baseline, sidecar=bad_sidecar)


if __name__ == "__main__":
    unittest.main()
