import json
import hashlib
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


class KiaSourceCorrespondenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((HERE / 'kia-source-correspondence.json').read_text())

    def test_healthy_native_exact_certificates(self):
        self.assertEqual(len(self.data['source_profiles']), 26)
        for p in self.data['source_profiles']:
            for key in ('ordered_position_sha256', 'native_uv_winding_sha256', 'geometry_sha256'):
                self.assertEqual(len(p[key]), 64)
        self.assertFalse(self.data['runtime_grant'])

    def test_every_private_vertex_has_explicit_policy(self):
        self.assertEqual(self.data['referenced_vertices'], 3411)
        self.assertEqual(self.data['asset_vertex_count'], 3559)
        self.assertEqual(self.data['unused_asset_vertices'], list(range(3411, 3559)))
        self.assertEqual(self.data['mapped_vertices'], 2440)
        self.assertEqual(self.data['topology_proved_additional_vertices'], 15)
        static = set(self.data['static_unmatched_crew_interior_vertices'])
        self.assertEqual(len(static), 956)
        self.assertEqual(self.data['static_unmatched_roots'], [17, 18, 19])
        self.assertFalse(self.data['unresolved_body_vertices'])
        mapping = self.data['mapping']
        self.assertEqual(len({p['vertex'] for p in mapping}), 3411)
        self.assertEqual([p['vertex'] for p in mapping], list(range(3411)))
        for m in mapping:
            self.assertEqual(not m['candidates'], m['vertex'] in static)
            for slot, vertex in m['candidates']:
                self.assertLess(slot, 26)
                self.assertLess(vertex, self.data['source_profiles'][slot]['vertices'])

    def test_topology_revision_not_nearest_neighbor(self):
        mapping = {p['vertex']: p for p in self.data['mapping']}
        for d in self.data['body_unmatched_diagnostics']:
            proofs = d['adjacent_triangle_proofs']
            self.assertTrue(proofs)
            expected = sorted({(p['native_source_slot'], p['candidate_vertex']) for p in proofs})
            self.assertEqual([list(p) for p in expected], mapping[d['vertex']]['candidates'])
            self.assertEqual(mapping[d['vertex']]['source_rule'],
                             'TWO_VERIFIED_NEIGHBORS_IDENTIFY_ORIGINAL_NATIVE_TRIANGLE')
            self.assertFalse(d['mapping_authorized'])  # no runtime delta proof yet
        # The closest original point is explicitly NOT the source topology join.
        d = next(p for p in self.data['body_unmatched_diagnostics'] if p['vertex'] == 34)
        self.assertEqual(d['nearest_native_vertex_for_diagnosis_only'], 389)
        self.assertEqual(mapping[34]['candidates'], [[0, 437]])

    def test_original_clone_retains_material_vector(self):
        evidence = json.loads((HERE / 'leaf-clone-evidence.json').read_text())
        self.assertEqual(evidence['subject']['digest']['sha256'],
                         'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4')
        self.assertIn('0x5767a0: MOV EAX, dword ptr [EBX + 0x38]', evidence['assembly'])
        self.assertIn('0x5767a3: MOV dword ptr [EBP + 0x38], EAX', evidence['assembly'])
        windows = json.loads((HERE / 'leaf-clone-original-bytes.json').read_text())
        for row in windows['windows']:
            raw = bytes.fromhex(row['bytes_hex'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
        self.assertEqual(bytes.fromhex(windows['windows'][0]['bytes_hex'])[4:],
                         bytes.fromhex('30665700'))  # original vtable slot +4


if __name__ == '__main__':
    unittest.main()
