"""Compact source registry checks; no private geometry or live-runtime claims."""
from pathlib import Path
import configparser
import json
import unittest

PORT = Path(__file__).resolve().parents[1]


class FullCoverageTests(unittest.TestCase):
    def test_vehicle_registry_is_exact_and_unique(self):
        rows = json.loads((PORT/'docs/full-coverage/vehicles/registry-candidates.json').read_text())
        header = (PORT/'renderer/reflection_pilot.hpp').read_text()
        self.assertEqual(len(rows), 174)
        self.assertEqual(len({r['geometry_sha256'] for r in rows}), 174)
        self.assertEqual(len({r['vehicle'] for r in rows}), 24)
        for r in rows:
            with self.subTest(vehicle=r['vehicle'], record=r['draw_index']):
                self.assertIn(r['geometry_sha256'], header)
                self.assertTrue(r['unique_vehicle_family'])
                self.assertEqual(r['signature_owner_families'], [r['vehicle']])
                self.assertEqual(r['ps2_binding']['pc_matching_faces'], r['triangles'])
                self.assertEqual(r['ps2_binding']['shader'], 'carshiny')
                self.assertEqual(r['flags_hex'], '00000101')

    def test_every_course_has_independent_exact_source_and_artifact(self):
        report = json.loads((PORT/'docs/full-coverage/courses/coverage-registry.json').read_text())
        rows = report['courses']
        header = (PORT/'renderer/grass_pilot.hpp').read_text()
        self.assertEqual(len(rows), 36)
        self.assertEqual(len({r['native_certificate_id'] for r in rows}), 36)
        for r in rows:
            with self.subTest(course=r['course']):
                self.assertIn(r['native_certificate_id'], header)
                self.assertIn(r['psm_sha256'], header)
                self.assertIn(r['pc_dx_sha256'], header)
                for category in ('grass', 'shrubs'):
                    a = r['categories'][category]['artifact']
                    self.assertIn(a['sha256'], header)
                    self.assertLessEqual(a['point_count'], 300000)
                    self.assertEqual(a['psm_sha256'], r['psm_sha256'])
                    self.assertEqual(a['pc_dx_sha256'], r['pc_dx_sha256'])

    def test_stock_defaults_remain_stock(self):
        ini = configparser.ConfigParser()
        ini.read(PORT/'PS2Port.ini.example')
        for key in ('Reflection', 'Grass', 'Shrubs', 'Foliage', 'RaceFleet'):
            self.assertEqual(ini.getint('PS2Port', key), 0)

    def test_cache_generation_and_no_frame_io(self):
        reflection = (PORT/'renderer/reflection_pilot.cpp').read_text()
        for key in ('g.vertex_revision', 'g.index_revision', 'g.primitive_count', 'g.reset_generation'):
            self.assertIn(key, reflection)
        grass = (PORT/'renderer/grass_pilot.cpp').read_text()
        frame_path = grass[grass.index('bool GrassPilot::build_vertices'):]
        self.assertNotIn('ifstream', frame_path)
        self.assertIn('kGrassSources.size()', grass)
        self.assertIn('f[1]>300000', grass)

    def test_msaa_driver_gate_preserves_non_msaa_and_has_no_cpu_readback(self):
        source = (PORT/'renderer/reflection_capture.cpp').read_text()
        for token in ('D3DMULTISAMPLE_2_SAMPLES', 'D3DMULTISAMPLE_4_SAMPLES',
                      'multisample_copy_unsupported_padded_dimensions',
                      'native_msaa_resolve_unsupported', 'multisampled?nullptr:&source'):
            self.assertIn(token, source)
        self.assertEqual(source.count('native.CopyRects('), 1)
        for forbidden in ('GetFrontBuffer(', 'LockRect(', 'Reset(', 'StretchRect('):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
