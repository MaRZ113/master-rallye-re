import json
from pathlib import Path
import unittest


class RuntimeJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((Path(__file__).parent / 'runtime-join.json').read_bytes())

    def test_session_identity_and_generation(self):
        a, b = self.report['frames']['released'], self.report['frames']['held']
        for key in ['exe_sha256', 'proxy_sha256', 'course', 'race_lifecycle_generation', 'owner_lifetime']:
            self.assertEqual(a[key], b[key])
        self.assertTrue(a['live_race_certificate'] and b['live_race_certificate'])

    def test_native_conditional_submission(self):
        a = self.report['frames']['released']['candidates']
        b = self.report['frames']['held']['candidates']
        self.assertEqual([d['arguments'][4] for d in a], [6])
        self.assertEqual([d['arguments'][4] for d in b], [6, 20])
        self.assertEqual([d['fvf'] for d in b], [0x112, 0x112])
        self.assertTrue(all(d['hresult'] == 0 for d in a + b))

    def test_native_glow_keeps_depth_write(self):
        glow = self.report['frames']['held']['candidates'][1]['native_logical_states']
        self.assertEqual((glow['ALPHABLENDENABLE'], glow['SRCBLEND'], glow['DESTBLEND']), (1, 5, 6))
        self.assertEqual(glow['ZWRITEENABLE'], 1)

    def test_shared_geometry_is_not_branch_authority(self):
        source = self.report['source_lamp_records']
        self.assertEqual(source[0]['geometry_sha256'], source[2]['geometry_sha256'])
        self.assertNotEqual(source[0]['slots'], source[2]['slots'])
        for frame in self.report['frames'].values():
            self.assertTrue(all(not d['uploaded_geometry_byte_identity_verified'] for d in frame['candidates']))


if __name__ == '__main__':
    unittest.main()
