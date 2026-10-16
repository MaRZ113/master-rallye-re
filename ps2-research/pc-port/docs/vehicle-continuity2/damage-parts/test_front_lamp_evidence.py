import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent

class FrontLampEvidenceTests(unittest.TestCase):
    def test_original_correspondence_is_complete(self):
        profiles = json.loads((HERE / 'front-lamp-mappings.json').read_text())['profiles']
        self.assertEqual([(p['ps2_root'], p['pc_record']) for p in profiles], [(5, 21), (11, 22)])
        for profile in profiles:
            self.assertEqual(profile['unmapped'], [])
            self.assertTrue(all(m['candidates'] for m in profile['mappings']))
            self.assertEqual(profile['tolerance'], 0.00001)

    def test_observed_duplicate_deltas_agree(self):
        rows = json.loads((HERE / 'front-lamp-runtime-13624.json').read_text())
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row['candidate_delta_conflicts'], [])
            self.assertTrue(row['owner_context'])
            self.assertEqual(row['context_gate'], 7)
        changed = [r for r in rows if r['frame'] == 10314]
        self.assertEqual([r['changed_native_vertices'] for r in changed], [3, 1])

    def test_screen_branch_is_not_a_front_reflection_profile(self):
        profiles = json.loads((HERE / 'front-lamp-mappings.json').read_text())['profiles']
        self.assertNotIn('e3f1adc5c0a294e29be66eef22aa73028a614b41992504c50b87ceb0862cce9b',
                         [p['original_geometry_sha256'] for p in profiles])

if __name__ == '__main__':
    unittest.main()
