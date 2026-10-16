"""Focused metadata assertions; these do not establish live damage identity."""
from pathlib import Path
import json
import unittest

HERE = Path(__file__).resolve().parent


class DamageEvidence(unittest.TestCase):
    def test_actual_replacement_fallback(self):
        evidence = json.loads((HERE / 'runtime-comparison.json').read_text())
        healthy, damaged = evidence['23999'], evidence['32683']
        self.assertEqual(healthy['draw_records'], 790)
        self.assertEqual(damaged['draw_records'], 606)
        self.assertEqual(healthy['body_private_faces'], 1980)
        self.assertEqual(damaged['body_private_faces'], 14)
        self.assertEqual(healthy['malformed_lines'], 0)
        self.assertEqual(damaged['malformed_lines'], 0)
        for vertices, faces in ((362, 265), (244, 209), (158, 155),
                                (117, 77), (130, 144), (76, 62), (6, 4),
                                (49, 34), (50, 50), (201, 166),
                                (20, 14), (145, 110), (80, 140)):
            h = [r for r in healthy['original_records']
                 if (r['vertices'], r['faces']) == (vertices, faces)]
            d = [r for r in damaged['original_records']
                 if (r['vertices'], r['faces']) == (vertices, faces)]
            self.assertEqual(len(h), 1)
            self.assertEqual(len(d), 1)
            self.assertFalse(h[0]['forwarded'])
            self.assertTrue(d[0]['forwarded'])
            self.assertNotEqual(h[0]['vertex_generation'], d[0]['vertex_generation'])
            self.assertNotEqual(h[0]['index_generation'], d[0]['index_generation'])
            self.assertEqual(h[0]['native_primary_generation'], d[0]['native_primary_generation'])

    def test_static_uv_certificates_are_family_bounded(self):
        evidence = json.loads((HERE / 'source-uv-topology.json').read_text())
        self.assertEqual(len(evidence['rows']), 13)
        digests = set()
        for row in evidence['rows']:
            digest = row['ordered_uv_normalized_topology_sha256']
            self.assertEqual(len(digest), 64)
            self.assertNotIn(digest, digests)
            digests.add(digest)
            self.assertTrue(row['negative_search_matches'])
            self.assertTrue(all(r['path'].split('/')[0] == 'Xtrail'
                                for r in row['negative_search_matches']))

    def test_new_damage_trio_exact_gate_and_stable_certificate(self):
        trio = json.loads((HERE / 'trio-analysis.json').read_text())
        self.assertEqual(len(trio), 3)
        for frame, capture in zip((1869, 2684, 4497), trio):
            self.assertIn('f' + str(frame), capture['capture'])
            self.assertTrue(capture['captured_source_rows'])
            for row in capture['captured_source_rows']:
                self.assertTrue(row['uv_topology_matches_original'])
                self.assertEqual(row['owner_context'], frame == 1869)
                self.assertEqual(row['context_gate'], 7 if frame == 1869 else 5)
        self.assertTrue(all(row['ordered_uv_winding_matches'] for row in
                            json.loads((HERE / 'trio-ordered-certificates.json').read_text())))

    def test_compiled_candidate_delta_agreement(self):
        rows = json.loads((HERE / 'trio-compiled-map-agreement.json').read_text())
        self.assertTrue(rows)
        self.assertTrue(all(row['maximum_all_whitelisted_candidate_delta_disagreement'] == 0
                            for row in rows))
        bumper = [row for row in rows if row['ps2_root'] == 17]
        self.assertEqual(len(bumper), 2)
        self.assertTrue(all(row['private_vertices_moved'] == 30 for row in bumper))

    def test_draft_index_only_and_unmapped_explicit(self):
        summary = json.loads((HERE / 'deformation-correspondence-summary.json').read_text())
        self.assertEqual(len(summary['profiles']), 13)
        self.assertEqual(len(summary['profiles'][0]['unmapped_private_vertices']), 8)
        self.assertEqual(len(summary['profiles'][5]['unmapped_private_vertices']), 4)
        for row in summary['profiles']:
            self.assertEqual(len(row['ordered_original_position_sha256']), 64)
            self.assertEqual(len(row['ordered_uv_winding_topology_sha256']), 64)
        draft = HERE / 'generated/xtrail_damage_source_draft.hpp'
        if draft.exists():
            source = draft.read_text()
            self.assertNotIn('struct XYZ', source)
            self.assertNotIn('constexpr XYZ', source)


if __name__ == '__main__':
    unittest.main()
