from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for item in (ROOT, ROOT / "src", ROOT / "tests" / "synthetic", ROOT / "tools"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from master_rallye.course_gxm import parse_course_gxm_model_v7_bytes
from master_rallye.course_source import parse_course_txt_bytes
from master_rallye.course_spatial import (
    MeshSpanRef,
    acute_xz_angle_degrees,
    analyze_source_mesh,
    gxm_source_to_runtime,
    pair_to_marker_polygon,
    point_to_marker_polygon,
    point_to_segment_distance_xz,
    position_mesh_owners,
    runtime_to_blender,
)
from test_r5t_e1_gxm_topology import make_v7_gxm
from r5t_f0_course_probe import patch_unique_position_x


class R5TF0SpatialTests(unittest.TestCase):
    def setUp(self):
        data, txt = make_v7_gxm()
        document = parse_course_txt_bytes(txt, "synthetic.txt")
        self.model = parse_course_gxm_model_v7_bytes(data, document, "synthetic.gxm")
        self.node = self.model.find_mesh("startpoint")

    def test_canonical_source_runtime_and_blender_transforms(self):
        self.assertEqual(gxm_source_to_runtime((1, 2, 3)), (1, 3, -2))
        self.assertEqual(runtime_to_blender((1, 3, -2)), (1, 2, 3))

    def test_mesh_centroid_bounds_and_transform(self):
        metrics = analyze_source_mesh(self.model, self.node)
        self.assertEqual(metrics.triangle_count, 12)
        self.assertEqual(metrics.unique_position_indices, tuple(range(8)))
        self.assertEqual(metrics.source_centroid, (0.0, 0.0, 0.0))
        self.assertEqual(metrics.runtime_centroid, (0.0, 0.0, -0.0))
        self.assertEqual(metrics.source_dimensions, (10.0, 10.0, 10.0))
        self.assertEqual(metrics.edge_incidence_histogram, ((2, 18),))

    def test_point_to_segment_xz_clamps_to_segment(self):
        self.assertEqual(point_to_segment_distance_xz((2, 100, 3), (0, 0, 0), (4, 0, 0)), 3.0)
        self.assertEqual(point_to_segment_distance_xz((-1, 0, 0), (0, 0, 0), (4, 0, 0)), 1.0)

    def test_marker_polygon_reports_every_marker_and_edge(self):
        markers = ((0, 0, 0), (10, 1, 0), (10, 2, 10), (0, 1, 10))
        result = point_to_marker_polygon((4, 2, -2), markers)
        self.assertEqual(len(result.marker_distances_3d), 4)
        self.assertEqual(len(result.edge_segment_distances_xz), 4)
        self.assertEqual(result.nearest_edge_index, 0)

    def test_pair_metrics_compare_all_edges_and_use_acute_orientation(self):
        markers = ((0, 0, 0), (10, 0, 0), (10, 0, 10), (0, 0, 10))
        result = pair_to_marker_polygon((2, 0, -2), (8, 0, -2), markers)
        self.assertEqual(len(result["edge_comparisons"]), 4)
        edges = result["edge_comparisons"]
        self.assertAlmostEqual(edges[0].angle_to_pair_degrees, 0.0)
        self.assertAlmostEqual(acute_xz_angle_degrees((-1, 0, 0), (1, 0, 0)), 0.0)
        self.assertEqual(result["nearest_edge_segment_to_midpoint"].edge_index, 0)

    def test_position_ownership_marks_shared_and_exclusive_vertices(self):
        triangles = ((0, 1, 2), (2, 3, 4))
        owners = position_mesh_owners(triangles, (
            MeshSpanRef(1, "first", 0, 1),
            MeshSpanRef(2, "second", 1, 1),
        ))
        self.assertEqual(owners[2], ((1, "first"), (2, "second")))
        self.assertEqual(owners[0], ((1, "first"),))

    def test_exclusive_mesh_positions_are_eligible(self):
        triangles = ((0, 1, 2), (2, 3, 4))
        owners = position_mesh_owners(triangles, (MeshSpanRef(1, "only", 0, 2),))
        self.assertTrue(all(owner == ((1, "only"),) for owner in owners.values()))

    def test_ownership_rejects_shared_or_incomplete_triangle_spans(self):
        with self.assertRaisesRegex(ValueError, "overlapping"):
            position_mesh_owners(((0, 1, 2),), (
                MeshSpanRef(1, "first", 0, 1), MeshSpanRef(2, "second", 0, 1),
            ))
        with self.assertRaisesRegex(ValueError, "unowned"):
            position_mesh_owners(((0, 1, 2), (3, 4, 5)), (MeshSpanRef(1, "first", 0, 1),))

    def test_one_off_x_translation_changes_only_selected_float_components(self):
        bank = self.model.positions
        original = bytearray(self.model.positions.raw)
        patched, changed_offsets = patch_unique_position_x(bytes(original), (0, 3), 20.0)
        self.assertEqual(len(patched), len(original))
        self.assertEqual(len(changed_offsets), sum(
            original[index] != patched[index] for index in range(len(original))
        ))
        self.assertEqual(len(changed_offsets), len(set(changed_offsets)))
        for position_index in (0, 3):
            old = self.model.position(position_index)
            import struct
            new = struct.unpack_from("<3f", patched, position_index * 12)
            self.assertEqual(new, (old[0] + 20.0, old[1], old[2]))
        untouched = bytearray(original)
        allowed = {index for position_index in (0, 3) for index in range(position_index * 12, position_index * 12 + 4)}
        self.assertTrue(all(original[index] == patched[index] for index in range(len(original)) if index not in allowed))


if __name__ == "__main__":
    unittest.main()
