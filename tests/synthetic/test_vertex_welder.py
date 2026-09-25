from __future__ import annotations
import copy
import math
import struct
import unittest

from master_rallye.collision_oracle import exact_vertex_bijection
from master_rallye.vertex_welder import (
    TOLERANCE, f32, loader_positions, proximity_pairs, isolation_proof,
    emit_triangles, stream_metrics, compare_streams, classify, early_hull_probe,
)


class VertexWelderTests(unittest.TestCase):
    points = ((0.,0.,0.), (1.,0.,0.), (0.,1.,0.), (0.,0.,1.))
    faces = ((0,2,1), (0,1,3), (0,3,2), (1,2,3))

    def moved(self):
        return tuple((f32(x+.4),y,z) for x,y,z in self.points)

    def compare(self, after=None, indices=None, **kwargs):
        after = self.moved() if after is None else after
        indices = self.faces if indices is None else indices
        return compare_streams(self.points, after, self.faces, indices,
                               isolation_proof(self.points, range(4)),
                               isolation_proof(after, range(4)),
                               pre_hull_stages_excluded=True, source_scope_validated=True, **kwargs)

    def test_exact_and_tolerance_bijection_statuses_preserved(self):
        self.assertEqual(exact_vertex_bijection({0:(0.,0.,0.)}, [(0.,0.,0.)], tolerance=0.)["status"], "EXACT_BIJECTION")
        self.assertEqual(exact_vertex_bijection({0:(0.,0.,0.)}, [(1e-7,0.,0.)], tolerance=1e-6)["status"],
                         "BIJECTION_WITHIN_TOLERANCE")

    def test_tolerance_is_actual_binary32(self):
        self.assertEqual(struct.pack("<f",TOLERANCE).hex(), "0ad7233c")

    def test_strict_boundary_and_next_binary32_values(self):
        bits = struct.unpack("<I",struct.pack("<f",TOLERANCE))[0]
        below = struct.unpack("<f",struct.pack("<I",bits-1))[0]
        above = struct.unpack("<f",struct.pack("<I",bits+1))[0]
        self.assertEqual(len(proximity_pairs([(0.,0.,0.),(below,0.,0.)])),1)
        self.assertFalse(proximity_pairs([(0.,0.,0.),(TOLERANCE,0.,0.)]))
        self.assertFalse(proximity_pairs([(0.,0.,0.),(above,0.,0.)]))

    def test_distance_is_sphere_not_axis_box(self):
        self.assertFalse(proximity_pairs([(0.,0.,0.),(f32(.008),f32(.008),0.)]))

    def test_proximity_is_not_transitive_equivalence(self):
        p=[(0.,0.,0.),(f32(.007),0.,0.),(f32(.014),0.,0.)]
        self.assertEqual([(a,b) for a,b,_ in proximity_pairs(p)], [(0,1),(1,2)])
        self.assertFalse(isolation_proof(p,[0])["complete"])

    def test_singleton_classes_and_identity_index_map(self):
        proof=isolation_proof(self.points,[3,1,0,2,1])
        self.assertEqual(proof["welded_classes"],[[0],[1],[2],[3]])
        self.assertEqual(proof["representatives"],{0:0,1:1,2:2,3:3})
        self.assertEqual(proof["maximum_merge_distance"],0.)

    def test_deterministic_selection_without_sort_axis_guess(self):
        self.assertEqual(isolation_proof(self.points,[2,1,0]),isolation_proof(self.points,[0,2,1]))

    def test_external_near_representative_fails_closed(self):
        proof=isolation_proof(self.points+((f32(.005),0.,0.),),range(4))
        self.assertEqual(proof["status"],"UNRESOLVED")
        self.assertIsNone(proof["representatives"])
        self.assertIsNone(proof["welded_classes"])
        self.assertTrue(any(p["other"]==4 for p in proof["near_dependencies"]))

    def test_near_boundary_is_not_promoted_to_proven(self):
        self.assertFalse(isolation_proof([(0.,0.,0.),(TOLERANCE,0.,0.)],[0])["complete"])

    def test_non_hull_pairs_do_not_invalidate_isolated_hull(self):
        points=self.points+((5.,5.,5.),(f32(5.005),5.,5.))
        self.assertTrue(proximity_pairs(points))
        self.assertTrue(isolation_proof(points,range(4))["complete"])

    def test_invalid_positions_indices_and_margin_rejected(self):
        for points in [[],[(math.nan,0.,0.)],[(0.,0.)],[(.1,0.,0.)]]:
            with self.subTest(points=points), self.assertRaises(ValueError):
                isolation_proof(points,[0])
        for selected in [[],[-1],[4]]:
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                isolation_proof(self.points,selected)
        with self.assertRaises(ValueError):
            isolation_proof(self.points,[0],margin=-1)

    def test_loader_x_translation_is_mode_independent(self):
        for single in [False,True]:
            a=loader_positions(self.points,single_precision=single)
            b=loader_positions(self.moved(),single_precision=single)
            self.assertEqual([p[1:] for p in a],[p[1:] for p in b])
            self.assertAlmostEqual(b[1][0]-a[1][0],.4,places=6)

    def test_stream_preserves_record_and_corner_order(self):
        self.assertEqual(emit_triangles(self.points,[(3,1,2)])[0],
                         (self.points[3],self.points[1],self.points[2]))
        with self.assertRaises(ValueError):
            emit_triangles(self.points,[(0,1,4)])

    def test_path_b_uniform_translation(self):
        report=self.compare()
        self.assertEqual(report["decision"],"B")
        self.assertTrue(report["passed"])
        self.assertLess(report["maximum_rigid_residual"],1e-6)

    def test_nonrigid_complete_stream_path_a(self):
        points=list(self.moved());points[1]=(2.,0.,0.)
        self.assertEqual(self.compare(tuple(points))["decision"],"A")

    def test_changed_winding_rejected(self):
        faces=list(self.faces);faces[0]=tuple(reversed(faces[0]))
        result=self.compare(indices=faces)
        self.assertFalse(result["checks"]["same_indices_topology_winding_adjacency"])
        self.assertEqual(result["decision"],"A")

    def test_new_degenerate_triangle_detected(self):
        faces=list(self.faces);faces[0]=(0,0,1)
        result=self.compare(indices=faces)
        self.assertEqual(result["candidate"]["degenerate_triangles"],[0])
        self.assertFalse(result["passed"])

    def test_duplicate_triangles_detected(self):
        report=stream_metrics(self.points,[(0,1,2),(1,2,0)])
        self.assertEqual(report["duplicate_triangles"],1)

    def test_changed_representatives_are_path_a_only_if_complete(self):
        a=isolation_proof(self.points,range(4)); b=copy.deepcopy(a)
        b["representatives"][0]=4
        # Explicit completed input maps exercise classification independently of the no-op oracle.
        r=compare_streams(self.points,self.moved(),self.faces,self.faces,a,b,
                          pre_hull_stages_excluded=True,source_scope_validated=True)
        self.assertEqual(r["decision"],"A")
        b["complete"]=False
        r=compare_streams(self.points,self.moved(),self.faces,self.faces,a,b,
                          pre_hull_stages_excluded=True,source_scope_validated=True)
        self.assertEqual(r["decision"],"U")

    def test_missing_pre_hull_or_source_gate_is_unresolved(self):
        proof=isolation_proof(self.points,range(4))
        report=compare_streams(self.points,self.moved(),self.faces,self.faces,proof,proof)
        self.assertEqual(report["decision"],"U")

    def test_nonfinite_checker_tolerance_rejected(self):
        for value in [math.inf, math.nan, 0., -1.]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.compare(tolerance=value)

    def test_classifier_never_forces_a_or_b_from_unknown(self):
        self.assertEqual(classify(False,True,True),"U")
        self.assertEqual(classify(True,False,False),"U")
        self.assertEqual(classify(True,True,False),"A")
        self.assertEqual(classify(True,False,True),"B")

    def test_early_hull_math_translation_and_first_occurrence(self):
        a=early_hull_probe(self.points,self.faces)
        b=early_hull_probe(self.moved(),self.faces)
        self.assertEqual(a["unique_count"],4)
        self.assertEqual(a["representative_corner_ids"],[0,1,2,5])
        self.assertEqual(a["signatures"],b["signatures"])
        self.assertAlmostEqual(b["center"][0]-a["center"][0],.4,places=6)
        self.assertAlmostEqual(a["twice_centered_radius"],b["twice_centered_radius"],places=6)


if __name__ == "__main__":
    unittest.main()
