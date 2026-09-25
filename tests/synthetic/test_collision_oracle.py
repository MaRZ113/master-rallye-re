from __future__ import annotations

import unittest

from master_rallye.collision_oracle import (
    compare_triangle_topology,
    edge_loop_vertices,
    exact_vertex_bijection,
    face_normal_metrics,
    gxm_to_demo_xyz,
    rigid_translation_metrics,
)


class CollisionOracleTests(unittest.TestCase):
    def test_axis_map_is_rigid_and_preserves_distances(self):
        a = (1.25, -2.0, 3.5)
        b = (-0.5, 4.0, 0.25)
        self.assertEqual(gxm_to_demo_xyz(a), (1.25, 3.5, 2.0))
        self.assertAlmostEqual(sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5,
                               sum((gxm_to_demo_xyz(a)[i] - gxm_to_demo_xyz(b)[i]) ** 2
                                   for i in range(3)) ** 0.5)

    def test_vertex_mapping_exact_and_rejects_reuse(self):
        source = {7: (0.0, 0.0, 0.0), 8: (1.0, 0.0, 0.0), 9: (0.0, 1.0, 0.0)}
        target = [gxm_to_demo_xyz(source[index]) for index in (9, 7, 8)]
        result = exact_vertex_bijection(source, target, tolerance=0.0)
        self.assertTrue(result["bijective"])
        self.assertTrue(result["all_source_points_used"])
        self.assertEqual(result["exact_float_match_count"], 3)
        self.assertEqual([row["source_c_index"] for row in result["rows"]], [9, 7, 8])
        reused = exact_vertex_bijection(source, [target[0], target[0]], tolerance=0.0)
        self.assertFalse(reused["bijective"])
        self.assertEqual(reused["rejected_points"][0]["reason"], "outside_tolerance")

    def test_vertex_mapping_rejects_empty_sets(self):
        with self.assertRaisesRegex(ValueError, "nonempty"):
            exact_vertex_bijection({}, [], tolerance=0.0)

    def test_vertex_mapping_float_epsilon_within_tolerance(self):
        result = exact_vertex_bijection({4: (0.0, 0.0, 0.0)}, [(1e-7, 0.0, 0.0)],
                                        tolerance=1e-6)
        self.assertEqual(result["status"], "BIJECTION_WITHIN_TOLERANCE")
        self.assertAlmostEqual(result["max_matched_distance"], 1e-7)

    def test_vertex_mapping_rejects_out_of_tolerance(self):
        result = exact_vertex_bijection({4: (0.0, 0.0, 0.0)}, [(0.1, 0.0, 0.0)],
                                        tolerance=1e-4)
        self.assertFalse(result["bijective"])
        self.assertEqual(result["unmatched_target_indices"], [0])
        self.assertEqual(result["status"], "OUT_OF_TOLERANCE")
        self.assertEqual(result["max_matched_distance"], None)

    def test_vertex_mapping_reports_ambiguous_near_duplicates(self):
        source = {1: (0.0, 0.0, 0.0), 2: (0.0, 0.0, 1e-10)}
        result = exact_vertex_bijection(source, [(0.0, 5e-11, 0.0)], tolerance=1e-6,
                                        ambiguity_epsilon=1e-12)
        self.assertFalse(result["bijective"])
        self.assertEqual(result["status"], "AMBIGUOUS")
        self.assertEqual(result["ambiguous_pairs"][0]["source_indices"], [1, 2])

    def test_vertex_mapping_reports_unequal_counts_without_forcing(self):
        source = {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0)}
        result = exact_vertex_bijection(source, [gxm_to_demo_xyz(source[1])], tolerance=0.0)
        self.assertFalse(result["bijective"])
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["unused_source_indices"], [2])

    def test_face_set_and_winding_mapping(self):
        source = [(4, 5, 6), (4, 6, 7)]
        mapping = {0: 4, 1: 5, 2: 6, 3: 7}
        report = compare_triangle_topology(source, [(0, 1, 2), (0, 3, 2)], mapping)
        self.assertEqual(report["target_faces_matching_source_unordered"], 2)
        self.assertEqual(report["target_faces_matching_source_oriented"], 1)
        self.assertEqual(report["target_faces_matching_source_reversed"], 1)

    def test_edge_loop_resolves_vertices_and_rejects_open_loop(self):
        edges = [(0, 1), (2, 1), (2, 3), (0, 3)]
        self.assertEqual(set(edge_loop_vertices(edges, (0, 1, 2, 3))), {0, 1, 2, 3})
        with self.assertRaisesRegex(ValueError, "closed polygon"):
            edge_loop_vertices(edges, (0, 2, 3))

    def test_rigid_translation_metrics_and_rejection(self):
        before = {0: (0.0, 0.0, 0.0), 1: (1.0, 2.0, 3.0)}
        after = {index: (point[0] + 0.4, point[1], point[2])
                 for index, point in before.items()}
        result = rigid_translation_metrics(before, after)
        self.assertAlmostEqual(result["translation_xyz"][0], 0.4)
        self.assertTrue(result["rigid_within_tolerance"])
        after[1] = (1.5, 2.0, 3.0)
        with self.assertRaisesRegex(ValueError, "not a rigid translation"):
            rigid_translation_metrics(before, after)

    def test_transformed_face_normal_matches_vector_a(self):
        points = {0: (0.0, 0.0, 0.0), 1: (1.0, 0.0, 0.0), 2: (0.0, 1.0, 0.0)}
        source_normal = (0.0, 0.0, 1.0)  # maps to demo +Y
        result = face_normal_metrics(points, (0, 1, 2), (0, 0, 0), [source_normal])
        self.assertFalse(result["degenerate"])
        self.assertAlmostEqual(result["signed_dot_products"][0], 1.0)
        self.assertAlmostEqual(result["angles_degrees"][0], 0.0)


if __name__ == "__main__":
    unittest.main()
