"""Compact source-evidence invariants; no proprietary geometry fixtures."""
import json
from pathlib import Path
import unittest

REPORT = json.loads((Path(__file__).with_name('join-evidence.json')).read_text())


class JoinEvidenceTests(unittest.TestCase):
    def test_correct_alias_has_strong_independent_shape_correspondence(self):
        woodland, exactnamed = REPORT['sources']
        self.assertEqual(woodland['family'], 'WOOLDAND')
        self.assertEqual(sum(d['union_matching_faces'] for d in woodland['draws']), 1814)
        self.assertEqual(sum(d['union_matching_faces'] for d in exactnamed['draws']), 669)
        self.assertEqual(sum(d['triangles'] for d in woodland['draws']), 1845)

    def test_original_source_identity_and_strict_profile(self):
        self.assertEqual(REPORT['sources'][0]['sha256'], '93a2bd9e9ee884ac32a6d7af4b320212156e853fd85b02bc01bdcc783d0d533d')
        self.assertEqual(REPORT['pc_source']['sha256'], '670ef07dc312aefa5628fe24c08aa696ee147043cfecdf2aadaf01e012c8b5fc')
        self.assertEqual(REPORT['tolerance'], .001)

    def test_alias_does_not_certify_entire_body_override(self):
        side = next(d for d in REPORT['sources'][0]['draws'] if d['draw_index'] == 10)
        self.assertEqual((side['triangles'], side['best_matching_faces']), (400, 394))
        self.assertGreater(min(side['unmatched_closest_corner_errors']), .001)
        self.assertNotIn(10, {r['draw_index'] for r in REPORT['registry_candidates']})

    def test_pc_coalesced_rear_materials_preserve_unknown_shader(self):
        rear = next(d for d in REPORT['sources'][0]['draws'] if d['draw_index'] == 9)
        self.assertEqual(rear['union_matching_faces'], 71)
        self.assertEqual(rear['unconditional_nonrubber_carshiny_matching_faces'], 43)
        untyped = next(j for j in rear['matches'] if j['mesh_path'] == 'root.4')
        self.assertEqual(untyped['material'], 'FRear128')
        self.assertIsNone(untyped['contract']['mode'])

    def test_reachable_candidate_source_signatures_are_family_specific(self):
        self.assertEqual({r['draw_index'] for r in REPORT['registry_candidates']}, {2, 7})
        self.assertEqual(REPORT['negative_controls']['files_scanned'], 78)
        self.assertEqual(REPORT['negative_controls']['unsupported'], [])
        for r in REPORT['registry_candidates']:
            self.assertEqual(r['signature_owner_families'], ['Forester'])
            self.assertTrue(r['unique_vehicle_family'])
            self.assertEqual(r['ps2_binding']['pc_matching_faces'], r['triangles'])
            self.assertEqual(r['ps2_binding']['contract']['mode'], 3)
        self.assertEqual(REPORT['runtime_validation'], 'NOT_PERFORMED')


if __name__ == '__main__':
    unittest.main()
