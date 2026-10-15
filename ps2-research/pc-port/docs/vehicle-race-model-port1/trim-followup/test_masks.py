import json,unittest
from pathlib import Path
import masks

class TrimMasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads(Path(__file__).with_name('masks.json').read_text())
    def test_full_source_coverage(self):
        for root,total in [('2',50),('15',8),('18',2)]:
            ids=[i for rows in self.report['ps2_masks'][root].values() for i in rows]
            self.assertEqual(sorted(ids),list(range(total)))
    def test_pc17_keeps_native_38(self):
        r=self.report['records']['17'];self.assertEqual(r['categories'],{'KEEP_NATIVE':38,'PS2_ROOT_15':2,'PS2_ROOT_18':2})
        self.assertEqual([r['category'] for r in r['faces'][:38]],['KEEP_NATIVE']*38)
    def test_runtime_reorder(self):
        r=self.report['records']['17'];fs=list(reversed(r['faces']))
        self.assertEqual(masks.runtime_categories(r['runtime_hash_categories'],[f['hash'] for f in fs]),[f['category'] for f in fs])
    def test_runtime_missing_extra_wrong_rejected(self):
        r=self.report['records']['17'];h=[f['hash'] for f in r['faces']]
        for changed in (h[:-1],h+[h[0]],['0'*64]+h[1:]):self.assertIsNone(masks.runtime_categories(r['runtime_hash_categories'],changed))
    def test_tolerance_not_rounding(self):
        a=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
        self.assertTrue(masks.matches(a,tuple(reversed(a))))
        self.assertFalse(masks.matches(a,((.0011,0.,0.),a[1],a[2])))
    def test_reproduce_from_pinned_originals(self):self.assertEqual(json.loads(json.dumps(masks.generate())),self.report)

if __name__=='__main__':unittest.main()
