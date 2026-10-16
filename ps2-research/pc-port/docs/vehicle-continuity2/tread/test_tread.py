from pathlib import Path
import json
import unittest

HERE = Path(__file__).resolve().parent


class CompleteTread(unittest.TestCase):
    def test_xtrail_source_policy(self):
        rows = json.loads((HERE / 'complete-tread-policy.json').read_text())
        for filename in ('XTRAIL-COMPLETE.ps2model', 'XTRAIL-COMPLETE-FLEET.ps2model'):
            row = next(r for r in rows if r['filename'] == filename)
            self.assertEqual(row['tread_u_wrap_mask'], 1 << 19)
            self.assertEqual(len(row['treads']), 1)
            tread = row['treads'][0]
            self.assertEqual(tread['faces'], 528)
            self.assertEqual(tread['mode'], 3)
            self.assertLess(tread['u_range'][0], -1)
            self.assertGreater(tread['u_range'][1], 2)
            self.assertGreater(tread['v_range'][0], 0)
            self.assertLess(tread['v_range'][1], 1)

    def test_every_admitted_tread_mask_is_source_bounded(self):
        rows = json.loads((HERE / 'complete-tread-policy.json').read_text())
        for row in rows:
            self.assertEqual(len(row['asset_sha256']), 64)
            expected = 0
            for tread in row['treads']:
                self.assertIn('tread', tread['source_primary'].lower())
                self.assertIn('rubber', '|'.join(tread['source_secondary']).lower())
                self.assertGreaterEqual(tread['mesh'], 0)
                self.assertLess(tread['mesh'], row['meshes'])
                self.assertGreaterEqual(tread['v_range'][0], 0)
                self.assertLessEqual(tread['v_range'][1], 1)
                if tread['u_range'][0] < 0 or tread['u_range'][1] > 1:
                    expected |= 1 << tread['mesh']
            self.assertEqual(expected, row['tread_u_wrap_mask'])


if __name__ == '__main__':
    unittest.main()
