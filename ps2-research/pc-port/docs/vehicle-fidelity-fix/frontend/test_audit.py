import json
import unittest
from pathlib import Path


class FrontendEvidence(unittest.TestCase):
    def setUp(self):
        self.report = json.loads((Path(__file__).parent / 'runtime-evidence.json').read_text())

    def test_complete_source_coverage(self):
        self.assertEqual([f['frame'] for f in self.report['frames']], [1040, 2051])
        for frame in self.report['frames']:
            self.assertEqual(frame['indices'], list(range(24)))
            self.assertEqual(frame['triangles'], 2487)
            self.assertEqual(len({r['source_geometry_sha256'] for r in frame['records']}), 24)

    def test_current_matrices_and_rotating_model(self):
        first, second = self.report['frames']
        self.assertNotEqual(first['world_matrices'], second['world_matrices'])
        self.assertEqual(first['view_matrices'], second['view_matrices'])
        self.assertEqual(first['projection_matrices'], second['projection_matrices'])
        for frame in self.report['frames']:
            self.assertEqual(len(frame['world_matrices']), 1)
            for record in frame['records']:
                self.assertTrue(record['world_view_projection_current'])
                self.assertEqual(record['matrix_hresults'], [0, 0, 0])
                self.assertGreater(record['vertex_generation'], 0)
                self.assertGreater(record['index_generation'], 0)

    def test_no_false_owner_claim(self):
        self.assertEqual(self.report['owner_cache_join'], 'UNKNOWN')
        self.assertFalse(self.report['replacement_enabled'])
        for frame in self.report['frames']:
            for record in frame['records']:
                self.assertFalse(record['model_owner_join_verified'])
                self.assertFalse(record['replacement_enabled'])
        self.assertEqual(self.report['malformed_session_lines'], [649, 664, 679, 1305])


if __name__ == '__main__':
    unittest.main()
