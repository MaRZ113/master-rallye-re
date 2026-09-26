from __future__ import annotations

import hashlib
import inspect
import json
import math
from pathlib import Path
import unittest

from master_rallye.collision_oracle import gxm_to_demo_xyz
from master_rallye.demo_dx import inspect_demo_dx
from master_rallye.gxm_chull import analyze_gxm_chull
from master_rallye.hull_oracle_compare import (
    analyze_native_rep_b_loop_fan,
    analyze_native_rep_b_loop_order_hypotheses,
    compare_prediction_to_native_rep_b,
)
from master_rallye.native_hull_reconstruction import (
    HullPolicy,
    HullPredictionError,
    build_rep_b_core_from_gxm_chull,
    build_rep_b_core_from_source_points,
)
from master_rallye.sidecar import parse_sidecar


ROOT = Path(__file__).resolve().parents[2]
MASTER_ROOT = ROOT.parent
CORPUS_931 = MASTER_ROOT / "corpora" / "demo-9.3.1"
VEHICLES_931 = CORPUS_931 / "DataGx" / "Vehicles"
SCRATCH = ROOT / ".research-output" / "r-demo2"
FIXTURE = ROOT / "research" / "r-demo2" / "r-demo2.10-golden-fixture.json"
TROOPER_GXM = VEHICLES_931 / "Trooper" / "car.gxm"
TROOPER_SIDECAR = VEHICLES_931 / "Trooper" / "Trooper.txt"
TROOPER_CANDIDATE_GXM = SCRATCH / "931-chull-oracle" / "trooper-931-chull-xplus010.gxm"
BASELINE_A = SCRATCH / "931-chull-oracle" / "input" / "car_baseline_A.dx"
BASELINE_B = SCRATCH / "input" / "car_baseline_B.dx"
CANDIDATE_DX = SCRATCH / "input" / "car_chull_xplus010.dx"
TROOPER_REQUIRED = (TROOPER_GXM, TROOPER_SIDECAR, TROOPER_CANDIDATE_GXM,
                    BASELINE_A, BASELINE_B, CANDIDATE_DX, FIXTURE)

RETAINED_TROOPER_C_INDICES = (
    1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324,
    1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334,
    1335, 1336, 1337, 1338, 1339, 1340,
    1347, 1348, 1349, 1350, 1351, 1352,
)
NOT_RETAINED_TROOPER_C_INDICES = (1325, 1326, 1341, 1342, 1343, 1344, 1345, 1346)
VEHICLE_EXPECTATIONS = {
    "Jump": (26, 48, 37, 61),
    "NewRav": (26, 48, 38, 62),
    "Tata": (18, 32, 24, 40),
    "Trooper": (28, 52, 41, 67),
}


def _cube_source_points():
    return {index: (x, y, z)
            for index, (x, y, z) in enumerate(
                (x, y, z) for x in (-1.0, 1.0)
                for y in (-1.0, 1.0) for z in (-1.0, 1.0))}


class Demo210HullControlUnitTests(unittest.TestCase):
    def test_builder_api_has_only_source_side_inputs(self):
        parameters = tuple(inspect.signature(build_rep_b_core_from_gxm_chull).parameters)
        self.assertEqual(parameters, ("gxm_data", "sidecar_path", "directive", "policy"))
        source = inspect.getsource(build_rep_b_core_from_gxm_chull)
        self.assertNotIn("native_rep", source)
        self.assertNotIn("target_dx", source)

    def test_source_prediction_module_has_no_dx_dependency(self):
        import master_rallye.native_hull_reconstruction as source_module

        source = inspect.getsource(source_module)
        self.assertNotIn("demo_dx", source)
        self.assertNotIn("ConvexHullRepresentation", source)

    def test_oracle_comparator_is_a_separate_api(self):
        parameters = tuple(inspect.signature(compare_prediction_to_native_rep_b).parameters)
        self.assertEqual(parameters[:2], ("prediction", "native"))

    def test_gxm_axis_transform(self):
        self.assertEqual(gxm_to_demo_xyz((1.25, -2.0, 3.5)), (1.25, 3.5, 2.0))

    def test_tetrahedron_builds_four_supporting_faces(self):
        points = {0: (0.0, 0.0, 0.0), 1: (1.0, 0.0, 0.0),
                  2: (0.0, 1.0, 0.0), 3: (0.0, 0.0, 1.0)}
        prediction = build_rep_b_core_from_source_points(points, tuple(points))
        self.assertEqual(len(prediction.vertex_source_c_indices), 4)
        self.assertEqual(len(prediction.polygon_faces), 4)
        self.assertEqual(len(prediction.edges_source_c_indices), 6)
        self.assertEqual(len(prediction.triangles_source_c_indices), 4)
        self.assertTrue(prediction.valid)

    def test_cube_face_deduplication_and_shell_counts(self):
        points = _cube_source_points()
        prediction = build_rep_b_core_from_source_points(points, tuple(points))
        self.assertEqual(len(prediction.polygon_faces), 6)
        self.assertEqual(len(prediction.edges_source_c_indices), 12)
        self.assertEqual(len(prediction.triangles_source_c_indices), 12)
        self.assertEqual(prediction.summary()["plane_disposition_counts"]["INSERTED_SUPPORTING_PLANE"], 6)
        self.assertGreater(prediction.summary()["plane_disposition_counts"][
            "DEDUPLICATED_BY_COPLANAR_SOURCE_SET"], 0)

    def test_polygon_loops_are_closed_and_use_known_edges(self):
        prediction = build_rep_b_core_from_source_points(
            _cube_source_points(), tuple(_cube_source_points()))
        edges = set(prediction.edges_source_c_indices)
        for face in prediction.polygon_faces:
            self.assertGreaterEqual(len(face.source_c_indices), 3)
            self.assertEqual(len(set(face.source_c_indices)), len(face.source_c_indices))
            for index, source_id in enumerate(face.source_c_indices):
                other = face.source_c_indices[(index + 1) % len(face.source_c_indices)]
                self.assertIn(tuple(sorted((source_id, other))), edges)

    def test_each_cube_edge_has_two_incident_faces(self):
        prediction = build_rep_b_core_from_source_points(
            _cube_source_points(), tuple(_cube_source_points()))
        self.assertEqual(len(prediction.edge_face_adjacency), 12)
        self.assertTrue(all(len(pair) == 2 and pair[0] != pair[1]
                            for pair in prediction.edge_face_adjacency))

    def test_reversing_source_enumeration_preserves_geometric_shell(self):
        points = _cube_source_points()
        first = build_rep_b_core_from_source_points(points, tuple(points))
        second = build_rep_b_core_from_source_points(points, tuple(reversed(points)))
        self.assertEqual(set(first.vertex_source_c_indices), set(second.vertex_source_c_indices))
        self.assertEqual({frozenset(face.source_c_indices) for face in first.polygon_faces},
                         {frozenset(face.source_c_indices) for face in second.polygon_faces})
        self.assertEqual(set(first.edges_source_c_indices), set(second.edges_source_c_indices))

    def test_coplanar_interior_source_point_is_not_a_hull_vertex(self):
        points = _cube_source_points()
        points[8] = (0.0, 0.0, -1.0)
        prediction = build_rep_b_core_from_source_points(points, tuple(points))
        self.assertEqual(len(prediction.vertex_source_c_indices), 8)
        self.assertNotIn(8, prediction.vertex_source_c_indices)
        self.assertEqual(len(prediction.polygon_faces), 6)

    def test_collinear_source_geometry_fails_closed(self):
        points = {index: (float(index), 0.0, 0.0) for index in range(4)}
        with self.assertRaises(HullPredictionError) as caught:
            build_rep_b_core_from_source_points(points, tuple(points))
        self.assertEqual(caught.exception.code, "INSUFFICIENT_SUPPORTING_PLANES")

    def test_duplicate_source_positions_fail_closed(self):
        points = {0: (0.0, 0.0, 0.0), 1: (0.0, 0.0, 0.0),
                  2: (1.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0), 4: (0.0, 0.0, 1.0)}
        with self.assertRaises(HullPredictionError) as caught:
            build_rep_b_core_from_source_points(points, tuple(points))
        self.assertEqual(caught.exception.code, "DUPLICATE_SOURCE_POSITION")

    def test_nonfinite_source_position_fails_closed(self):
        points = {0: (0.0, 0.0, 0.0), 1: (1.0, 0.0, 0.0),
                  2: (0.0, 1.0, 0.0), 3: (0.0, 0.0, math.inf)}
        with self.assertRaises(HullPredictionError) as caught:
            build_rep_b_core_from_source_points(points, tuple(points))
        self.assertEqual(caught.exception.code, "INVALID_SOURCE_POINT")

    def test_source_id_order_mismatch_fails_closed(self):
        points = {0: (0.0, 0.0, 0.0), 1: (1.0, 0.0, 0.0),
                  2: (0.0, 1.0, 0.0), 3: (0.0, 0.0, 1.0)}
        with self.assertRaises(HullPredictionError) as caught:
            build_rep_b_core_from_source_points(points, (0, 1, 2))
        self.assertEqual(caught.exception.code, "SOURCE_ID_MISMATCH")

    def test_invalid_geometric_policy_fails_closed(self):
        points = {0: (0.0, 0.0, 0.0), 1: (1.0, 0.0, 0.0),
                  2: (0.0, 1.0, 0.0), 3: (0.0, 0.0, 1.0)}
        with self.assertRaises(HullPredictionError) as caught:
            build_rep_b_core_from_source_points(
                points, tuple(points), policy=HullPolicy(support_tolerance=-1.0))
        self.assertEqual(caught.exception.code, "INVALID_POLICY")

    def test_insufficiently_resolved_tolerance_does_not_fabricate_hull(self):
        points = _cube_source_points()
        with self.assertRaises(HullPredictionError):
            build_rep_b_core_from_source_points(
                points, tuple(points), policy=HullPolicy(support_tolerance=100.0))


@unittest.skipUnless(all(path.is_file() for path in TROOPER_REQUIRED),
                     "requires the local ignored DEMO 9.3.1 Trooper oracle inputs")
class Demo210TrooperOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.baseline_data = TROOPER_GXM.read_bytes()
        cls.candidate_data = TROOPER_CANDIDATE_GXM.read_bytes()
        cls.baseline_source = analyze_gxm_chull(
            cls.baseline_data, TROOPER_SIDECAR, "$chull(Trooper)")
        cls.baseline = build_rep_b_core_from_gxm_chull(
            cls.baseline_data, TROOPER_SIDECAR, "$chull(Trooper)")
        cls.candidate = build_rep_b_core_from_gxm_chull(
            cls.candidate_data, TROOPER_SIDECAR, "$chull(Trooper)")
        cls.baseline_a = BASELINE_A.read_bytes()
        cls.baseline_b = BASELINE_B.read_bytes()
        cls.candidate_dx = CANDIDATE_DX.read_bytes()
        cls.native_baseline = inspect_demo_dx(cls.baseline_a, "Trooper baseline A").collision.convex_hull.representation_b
        cls.native_candidate = inspect_demo_dx(cls.candidate_dx, "Trooper +0.10 X candidate").collision.convex_hull.representation_b
        cls.baseline_comparison = compare_prediction_to_native_rep_b(cls.baseline, cls.native_baseline)
        cls.candidate_comparison = compare_prediction_to_native_rep_b(cls.candidate, cls.native_candidate)

    def test_fixture_hashes_and_baseline_determinism(self):
        hashes = self.fixture["input_sha256"]
        self.assertEqual(hashlib.sha256(self.baseline_data).hexdigest(), hashes["original_gxm"])
        self.assertEqual(hashlib.sha256(self.candidate_data).hexdigest(), hashes["xplus010_gxm"])
        self.assertEqual(hashlib.sha256(self.baseline_a).hexdigest(), hashes["baseline_a_dx"])
        self.assertEqual(hashlib.sha256(self.baseline_b).hexdigest(), hashes["baseline_b_dx"])
        self.assertEqual(hashlib.sha256(self.candidate_dx).hexdigest(), hashes["xplus010_dx"])
        self.assertEqual(self.baseline_a, self.baseline_b)

    def test_source_directive_and_triangle_range_counts(self):
        expected = self.fixture["source_chull"]
        self.assertEqual(self.baseline_source["directive"], "$chull(Trooper)")
        self.assertEqual(self.baseline_source["record_range_half_open"], expected["record_range_half_open"])
        self.assertEqual(len(self.baseline_source["records"]), expected["triangle_records"])
        self.assertEqual(len(self.baseline_source["source_c_indices"]), expected["unique_source_c_count"])

    def test_source_only_predictor_selects_the_exact_oracle_vertex_set(self):
        self.assertEqual(set(self.baseline.vertex_source_c_indices),
                         set(RETAINED_TROOPER_C_INDICES))
        self.assertEqual(len(self.baseline.vertex_source_c_indices), 28)
        self.assertEqual(set(self.baseline.source_c_indices)
                         - set(self.baseline.vertex_source_c_indices),
                         set(NOT_RETAINED_TROOPER_C_INDICES))

    def test_source_to_dx_transform_maps_all_predicted_vertices(self):
        source_points = self.baseline_source["source_c_points"]
        by_id = dict(zip(self.baseline.vertex_source_c_indices, self.baseline.vertices))
        for source_id in self.baseline.vertex_source_c_indices:
            self.assertEqual(by_id[source_id], gxm_to_demo_xyz(source_points[source_id]))

    def test_supporting_plane_trace_is_complete_and_deduplicated(self):
        counts = self.baseline.summary()["plane_disposition_counts"]
        self.assertEqual(len(self.baseline.plane_trace), math.comb(36, 3))
        self.assertEqual(counts["INSERTED_SUPPORTING_PLANE"], 41)
        self.assertEqual(counts["DEDUPLICATED_BY_COPLANAR_SOURCE_SET"], 33)
        self.assertEqual(sum(counts.values()), math.comb(36, 3))

    def test_source_triangle_first_occurrence_order_does_not_change_geometric_core(self):
        reversed_order = build_rep_b_core_from_source_points(
            self.baseline_source["source_c_points"],
            tuple(reversed(self.baseline.source_point_order)),
            directive=self.baseline.directive,
            source_record_range=self.baseline.source_record_range,
            source_triangle_record_count=self.baseline.source_triangle_record_count,
            policy=self.baseline.policy,
        )
        self.assertEqual(set(self.baseline.vertex_source_c_indices),
                         set(reversed_order.vertex_source_c_indices))
        self.assertEqual({frozenset(face.source_c_indices)
                          for face in self.baseline.polygon_faces},
                         {frozenset(face.source_c_indices)
                          for face in reversed_order.polygon_faces})
        self.assertEqual(set(self.baseline.edges_source_c_indices),
                         set(reversed_order.edges_source_c_indices))

    def test_polygon_faces_edges_adjacency_and_triangles_match_oracle_counts(self):
        counts = self.fixture["native_rep_b_counts"]
        self.assertEqual(len(self.baseline.polygon_faces), counts["polygon_faces"])
        self.assertEqual(len(self.baseline.edges_source_c_indices), counts["edges"])
        self.assertEqual(len(self.baseline.edge_face_adjacency), counts["edges"])
        self.assertEqual(len(self.baseline.triangles_source_c_indices), counts["triangles"])

    def test_predicted_vertices_and_max_residual_match_native(self):
        result = self.baseline_comparison["vertex_membership"]
        self.assertTrue(result["exact_source_id_set_match"])
        self.assertEqual(result["matched_count"], 28)
        self.assertLessEqual(result["max_position_error"], 1e-5)
        self.assertEqual(result["missing_source_c_indices"], [])
        self.assertEqual(result["extra_source_c_indices"], [])

    def test_polygon_face_vertex_sets_match_native(self):
        faces = self.baseline_comparison["polygon_faces"]
        self.assertTrue(faces["same_per_face_vertex_sets"])
        self.assertTrue(faces["same_cycles_up_to_rotation_and_winding"])
        self.assertEqual(faces["native_face_count"], 41)

    def test_native_loop_winding_is_separate_from_face_geometry(self):
        counts = self.baseline_comparison["polygon_faces"]["ordered_cycle_classification_counts"]
        self.assertEqual(counts["SAME_ORIENTATION_UP_TO_ROTATION"], 21)
        self.assertEqual(counts["REVERSED_UP_TO_ROTATION"], 20)
        self.assertEqual(counts["ORDER_DIFFERENT"], 0)

    def test_predicted_edges_and_edge_face_adjacency_match_native(self):
        self.assertTrue(self.baseline_comparison["edges"]["same_undirected_edge_set"])
        self.assertTrue(self.baseline_comparison["edge_face_adjacency"]["same_after_face_identity_mapping"])

    def test_triangulation_difference_is_classified_separately(self):
        result = self.baseline_comparison["triangulation"]
        self.assertEqual(result["classification"], "SAME_POLYGON_DIFFERENT_TRIANGULATION")
        self.assertFalse(result["same_unoriented_triangle_partition"])
        self.assertEqual(len(result["predicted_only_unoriented_triangles"]), 10)
        self.assertEqual(len(result["native_only_unoriented_triangles"]), 10)

    def test_native_triangles_are_fan_from_second_stored_loop_vertex(self):
        result = analyze_native_rep_b_loop_fan(self.native_baseline)
        self.assertEqual(result["face_count"], 41)
        self.assertTrue(result["fan_from_loop_vertex_1_matches_all_faces"])
        self.assertFalse(result["fan_from_loop_vertex_0_matches_all_faces"])
        recorded = self.fixture["comparison_after_prediction"]["native_triangle_rule"]
        self.assertEqual(result["fan_from_loop_vertex_1_match_count"],
                         recorded["trooper_baseline_matching_faces"])

    def test_native_loop_start_hypotheses_are_reported_after_prediction(self):
        result = analyze_native_rep_b_loop_order_hypotheses(
            self.baseline, self.native_baseline)
        self.assertEqual(result["matched_face_count"], 41)
        self.assertTrue(result["native_face_order_matches_prediction"])

    def test_native_vertex_face_and_edge_ordering_is_reported_separately(self):
        result = self.baseline_comparison["native_ordering"]
        self.assertFalse(result["vertex_order_matches_prediction"])
        self.assertTrue(result["face_order_matches_prediction"])
        self.assertFalse(result["edge_order_matches_prediction"])

    def test_plus010_candidate_preserves_source_only_topology(self):
        self.assertEqual(self.baseline.vertex_source_c_indices,
                         self.candidate.vertex_source_c_indices)
        self.assertEqual([face.source_c_indices for face in self.baseline.polygon_faces],
                         [face.source_c_indices for face in self.candidate.polygon_faces])
        self.assertEqual(self.baseline.edges_source_c_indices,
                         self.candidate.edges_source_c_indices)
        self.assertEqual(self.baseline.triangles_source_c_indices,
                         self.candidate.triangles_source_c_indices)
        for before, after in zip(self.baseline.vertices, self.candidate.vertices):
            self.assertAlmostEqual(after[0] - before[0], 0.10, delta=1e-7)
            self.assertAlmostEqual(after[1] - before[1], 0.0, delta=1e-7)
            self.assertAlmostEqual(after[2] - before[2], 0.0, delta=1e-7)

    def test_plus010_native_oracle_retains_polygon_shell_core(self):
        self.assertTrue(self.candidate_comparison["vertex_membership"]["exact_source_id_set_match"])
        self.assertTrue(self.candidate_comparison["polygon_faces"]["same_per_face_vertex_sets"])
        self.assertTrue(self.candidate_comparison["edges"]["same_undirected_edge_set"])
        self.assertTrue(self.candidate_comparison["edge_face_adjacency"]["same_after_face_identity_mapping"])
        self.assertEqual(self.candidate_comparison["triangulation"]["classification"],
                         "SAME_POLYGON_DIFFERENT_TRIANGULATION")
        fan = analyze_native_rep_b_loop_fan(self.native_candidate)
        self.assertTrue(fan["fan_from_loop_vertex_1_matches_all_faces"])
        self.assertEqual(fan["fan_from_loop_vertex_1_match_count"],
                         self.fixture["comparison_after_prediction"][
                             "native_triangle_rule"]["trooper_candidate_matching_faces"])


@unittest.skipUnless(all((VEHICLES_931 / name / "car.gxm").is_file()
                         and (VEHICLES_931 / name / "car.txt").is_file()
                         and (VEHICLES_931 / name / "car.dx").is_file()
                         for name in ("Jump", "NewRav", "Tata")),
                     "requires local same-build DEMO 9.3.1 source/DX controls")
class Demo210CrossCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_source_only_shell_matches_three_additional_shipped_controls(self):
        for vehicle, expected in VEHICLE_EXPECTATIONS.items():
            with self.subTest(vehicle=vehicle):
                directory = VEHICLES_931 / vehicle
                source_path = directory / "car.gxm"
                sidecar_path = directory / "car.txt"
                target_path = directory / "car.dx"
                sidecar = parse_sidecar(sidecar_path)
                directives = [mesh.name for mesh in sidecar.meshes if "chull" in mesh.name.casefold()]
                self.assertEqual(len(directives), 1)
                prediction = build_rep_b_core_from_gxm_chull(
                    source_path.read_bytes(), sidecar_path, directives[0])
                target = inspect_demo_dx(target_path.read_bytes(), f"9.3.1 shipped {vehicle}")
                native = target.collision.convex_hull.representation_b
                result = compare_prediction_to_native_rep_b(prediction, native)
                native_fan = analyze_native_rep_b_loop_fan(native)
                self.assertEqual((len(prediction.vertex_source_c_indices),
                                  len(prediction.triangles_source_c_indices),
                                  len(prediction.polygon_faces),
                                  len(prediction.edges_source_c_indices)), expected)
                self.assertTrue(result["vertex_membership"]["exact_source_id_set_match"])
                self.assertTrue(result["polygon_faces"]["same_per_face_vertex_sets"])
                self.assertTrue(result["edges"]["same_undirected_edge_set"])
                self.assertTrue(result["edge_face_adjacency"]["same_after_face_identity_mapping"])
                self.assertTrue(result["native_ordering"]["face_order_matches_prediction"])
                self.assertTrue(self.fixture["additional_same_build_shipped_controls"][
                    vehicle]["face_order_matches_prediction"])
                self.assertEqual(result["triangulation"]["classification"],
                                 "SAME_POLYGON_DIFFERENT_TRIANGULATION")
                self.assertTrue(native_fan["fan_from_loop_vertex_1_matches_all_faces"])
                self.assertEqual(native_fan["fan_from_loop_vertex_1_match_count"],
                                 expected[2])


class Demo210841NegativeReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = MASTER_ROOT / "corpora" / "demo-8.4.1" / "DataGx" / "Vehicles" / "Trooper" / "car.gxm"
        cls.candidate = SCRATCH / "exact-841-rebuild" / "candidate.gxm"

    @unittest.skipUnless((MASTER_ROOT / "corpora" / "demo-8.4.1" / "DataGx" / "Vehicles" / "Trooper" / "car.gxm").is_file()
                     and (SCRATCH / "exact-841-rebuild" / "candidate.gxm").is_file(),
                     "requires pinned DEMO 8.4.1 +0.4 X source pair")
    def test_existing_841_replay_preserves_stock_and_override_threshold_control(self):
        from tools.scanner.r_demo2_7_hull_divergence import _replay

        stock = 0.0005000000237487257
        override = 0.00052
        baseline_data = self.baseline.read_bytes()
        candidate_data = self.candidate.read_bytes()
        self.assertEqual(len(_replay(baseline_data, stock)["faces"]), 37)
        self.assertEqual(len(_replay(candidate_data, stock)["faces"]), 38)
        self.assertEqual(len(_replay(baseline_data, override)["faces"]), 37)
        self.assertEqual(len(_replay(candidate_data, override)["faces"]), 37)


if __name__ == "__main__":
    unittest.main()
