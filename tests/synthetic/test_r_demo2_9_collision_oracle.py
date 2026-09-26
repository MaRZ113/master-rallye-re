from __future__ import annotations

import unittest
from pathlib import Path

from tools.scanner.r_demo2_9_collision_oracle import analyze_oracle
from master_rallye.collision_oracle_analysis import (
    compare_collision_oracle, compare_secondary_descriptors,
)


ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / ".research-output" / "r-demo2"
CORPUS = Path(r"D:\Game\Master Rallye\corpora\demo-9.3.1")
GXM = CORPUS / "DataGx" / "Vehicles" / "Trooper" / "car.gxm"
SIDECAR = CORPUS / "DataGx" / "Vehicles" / "Trooper" / "Trooper.txt"
CANDIDATE_GXM = SCRATCH / "931-chull-oracle" / "trooper-931-chull-xplus010.gxm"
AUDIT = SCRATCH / "931-chull-oracle" / "trooper-931-chull-xplus010-audit.json"
BASELINE_A = SCRATCH / "931-chull-oracle" / "input" / "car_baseline_A.dx"
BASELINE_B = SCRATCH / "input" / "car_baseline_B.dx"
CANDIDATE_DX = SCRATCH / "input" / "car_chull_xplus010.dx"
REQUIRED = (GXM, SIDECAR, CANDIDATE_GXM, AUDIT, BASELINE_A, BASELINE_B, CANDIDATE_DX)


@unittest.skipUnless(all(path.is_file() for path in REQUIRED),
                     "requires the local ignored 9.3.1 Trooper oracle inputs")
class Demo29CollisionOracleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze_oracle(GXM, CANDIDATE_GXM, SIDECAR, BASELINE_A,
                                   BASELINE_B, CANDIDATE_DX, AUDIT, CORPUS)

    def test_baseline_a_and_b_are_exactly_identical(self):
        self.assertTrue(self.report["baseline_ab"]["byte_identical"])
        self.assertEqual(self.report["input_hashes"]["baseline_a"]["sha256"],
                         self.report["input_hashes"]["baseline_b"]["sha256"])
        self.assertEqual(self.report["input_hashes"]["baseline_a"]["size"], 124568)

    def test_chull_source_counts_and_identity_mapping_are_stable(self):
        source = self.report["source_chull"]
        mapping = self.report["source_to_rep_b"]
        self.assertEqual(source["triangle_record_count"], 68)
        self.assertEqual(source["unique_source_c_count"], 36)
        self.assertEqual(len(mapping["retained_source_c_indices"]), 28)
        self.assertEqual(len(mapping["not_retained_as_distinct_final_vertices"]), 8)
        self.assertEqual(mapping["rep_b_vertices"], 28)
        self.assertEqual(mapping["rep_b_triangles"], 52)
        self.assertTrue(mapping["all_mapping_identities_preserved"])
        self.assertEqual(mapping["retained_source_c_indices"], mapping["candidate_extreme_indices"])
        self.assertLessEqual(mapping["baseline_mapping_max_residual"], 1e-5)
        self.assertLessEqual(mapping["candidate_mapping_max_residual"], 1e-5)

    def test_rep_b_is_translated_with_core_topology_preserved(self):
        result = self.report["rep_b_translation"]
        self.assertEqual(result["core_topology"]["classification"], "CORE_TOPOLOGY_EQUAL")
        self.assertTrue(result["triangles_equal"])
        self.assertTrue(result["edges_equal"])
        self.assertTrue(result["edge_face_adjacency_equal"])
        self.assertTrue(result["face_loops_equal"])
        self.assertTrue(result["geometry"]["within_float32_tolerance"])
        self.assertAlmostEqual(result["geometry"]["delta_mean_xyz"][0], 0.10, places=7)
        self.assertEqual(result["geometry"]["delta_mean_xyz"][1:], [0.0, 0.0])

    def test_rep_a_is_aabb_corner_set_and_core_topology_is_preserved(self):
        result = self.report["rep_a"]
        self.assertEqual(result["core_topology"]["classification"], "CORE_TOPOLOGY_EQUAL")
        self.assertEqual(result["aabb"]["classification"],
                         "REP_A_VERTICES_EQUAL_REP_B_AABB_CORNERS_IN_CONTROLLED_PAIR")
        for pair in (result["aabb"]["baseline"], result["aabb"]["candidate"]):
            self.assertTrue(pair["all_eight_matched"])
            self.assertEqual(pair["maximum_corner_error"], 0.0)
        self.assertTrue(result["aabb"]["triangles_equal"])
        self.assertTrue(result["triangles_equal"])
        self.assertEqual(result["baseline_triangle_count"], 12)
        self.assertEqual(result["baseline_triangles"], result["candidate_triangles"])

    def test_auxiliary_secondary_difference_does_not_change_core_topology(self):
        comparison = self.report["dx_comparisons"]["baseline_A_vs_candidate"]
        self.assertEqual(comparison["classification"]["topology"], "CORE_TOPOLOGY_EQUAL")
        self.assertEqual(comparison["classification"]["auxiliary_secondary_descriptors"],
                         "AUXILIARY_SECONDARY_DESCRIPTORS_DIFFER")
        self.assertEqual(comparison["classification"]["auxiliary_secondary_descriptor_semantics"],
                         "UNRESOLVED")
        changes = {item["representation"]: item for item in comparison["unresolved_auxiliary_changes"]}
        self.assertEqual(len(changes["representation_a"]["changed_faces"]), 2)
        self.assertEqual(len(changes["representation_b"]["changed_faces"]), 13)
        self.assertFalse(all(row["per_face_multiset_equal"]
                             for row in changes["representation_a"]["changed_faces"]))
        self.assertTrue(all(row["per_face_multiset_equal"]
                            for row in changes["representation_b"]["changed_faces"]))
        self.assertFalse(comparison["classification"]["unexpected_change"])
        self.assertTrue(comparison["classification"]["intentional_translation"])

    def test_secondary_tuple_comparison_preserves_permutations_and_multiplicity(self):
        class Face:
            def __init__(self, indices):
                self.secondary_indices = tuple(indices)

        result = compare_secondary_descriptors((Face((1, 2, 2)),), (Face((2, 1, 2)),))
        self.assertEqual(result["classification"], "AUXILIARY_SECONDARY_DESCRIPTORS_DIFFER")
        self.assertEqual(result["semantics"], "UNRESOLVED")
        self.assertTrue(result["per_face_multisets_equal"])
        self.assertEqual(result["pure_permutation_face_indices"], [0])
        changed_multiplicity = compare_secondary_descriptors((Face((1, 2, 2)),), (Face((1, 2)),))
        self.assertFalse(changed_multiplicity["per_face_multisets_equal"])

    def test_reusable_collision_comparator_separates_core_and_auxiliary(self):
        report = compare_collision_oracle(BASELINE_A.read_bytes(), CANDIDATE_DX.read_bytes())
        self.assertEqual(report["core_topology"], "CORE_TOPOLOGY_EQUAL")
        self.assertEqual(report["secondary_descriptor_semantics"], "UNRESOLVED")
        self.assertEqual(report["parser_verdict"], "UNRESOLVED")
        self.assertEqual(len(report["representations"]["representation_b"]["secondary_descriptors"]["pure_permutation_face_indices"]), 13)

    def test_base_scalar_is_bit_identical_under_translation(self):
        scalar = self.report["tag101_base_scalar"]
        self.assertEqual(scalar["baseline_value"], scalar["candidate_value"])
        self.assertEqual(scalar["baseline_bytes_hex"], "a4b02640")
        self.assertEqual(scalar["candidate_bytes_hex"], "a4b02640")
        self.assertTrue(scalar["bit_identical"])
        self.assertEqual(scalar["classification"], "TRANSLATION_INVARIANT_IN_CONTROLLED_ORACLE")
        self.assertTrue(scalar["baseline_rep_a_radius_relation"]["stored_matches_float32_radius"])
        self.assertTrue(scalar["candidate_rep_a_radius_relation"]["stored_matches_float32_radius"])
        self.assertTrue(all(item["stored_matches_float32_radius"]
                            for item in scalar["additional_corpus_relations"].values()))

    def test_marker_1339_union_center_radius_formulas(self):
        for label in ("controlled_baseline", "controlled_candidate"):
            formula = self.report["marker_1339"][label]
            self.assertLessEqual(formula["hypothesis_a_render_union_rep_b"]["max_minimum_error"], 1e-7)
            self.assertLessEqual(formula["hypothesis_a_render_union_rep_b"]["max_maximum_error"], 1.3e-7)
            self.assertLessEqual(formula["hypothesis_b_center_from_extrema"]["maximum_error"], 6e-8)
            self.assertLessEqual(formula["hypothesis_c_radius_from_union"]["nearest_float32_error"], 2.5e-7)
        controls = self.report["marker_1339"]["additional_corpus_controls"]
        self.assertEqual(set(controls), {"Jump", "NewRav", "Tata"})
        for control in controls.values():
            formula = control["formula"]
            self.assertEqual(formula["hypothesis_a_render_union_rep_b"]["max_minimum_error"], 0.0)
            self.assertEqual(formula["hypothesis_a_render_union_rep_b"]["max_maximum_error"], 0.0)
            self.assertEqual(formula["hypothesis_b_center_from_extrema"]["maximum_error"], 0.0)
            self.assertLessEqual(formula["hypothesis_c_radius_from_union"]["nearest_float32_error"], 2.5e-7)

    def test_face_scalars_track_polygon_area_with_small_recomputation_drift(self):
        for rep in self.report["face_scalars"].values():
            self.assertLess(rep["scalar_area_error_max_both_runs"], 1e-6)
            self.assertLess(rep["recomputed_area_max_abs_delta"], 4e-7)
            self.assertLess(rep["scalar_max_abs_delta"], 1e-6)

    def test_all_changed_bytes_are_accounted_for(self):
        accounting = self.report["byte_accounting"]
        self.assertEqual(accounting["total_changed_bytes"], 182)
        self.assertEqual(accounting["explained_changed_bytes"], 182)
        self.assertTrue(accounting["complete"])
        self.assertEqual(accounting["unexplained"], [])
        self.assertEqual(sum(len(item["ranges"]) for item in accounting["categories"].values()), 89)


if __name__ == "__main__":
    unittest.main()
