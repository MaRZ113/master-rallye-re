"""Tests for the W4 XML writer and the limit model (need the PS2 and PC corpora; skipped without them)."""
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402

HAVE = cc.PS2_ROOT.exists() and cc.PC_ROOT.exists()


@unittest.skipUnless(HAVE, 'PS2/PC corpora not present')
class LogicTest(unittest.TestCase):
    def test_turkey3_xml(self):
        import build_logic as bl
        from master_rallye.course_xml import parse_course_xml_bytes
        data, rep = bl.build(cc.course('Turkey3'))
        self.assertTrue(rep['checks']['pass'], rep['checks'])
        doc = parse_course_xml_bytes(data, 'cand')
        self.assertNotIn('Copy of SplitTime1', [e.name for e in doc.split_time_eggs])
        for name in ('LeftOuterLimit', 'RightOuterLimit', 'LeftInnerLimit', 'RightInnerLimit'):
            pts = [m.position for m in doc.marker_list(name).markers]
            self.assertEqual({p[1] for p in pts}, {0.0})
            self.assertLessEqual(max(math.dist((a[0], a[2]), (b[0], b[2])) for a, b in zip(pts, pts[1:])), bl.LIMIT_STEP + 0.02)

    def test_italym1_split_values(self):
        import build_logic as bl
        _, rep = bl.build(cc.course('ItalyM1'))
        fields = {(c.get('split') or c.get('egg'), c.get('field')): c.get('ps2') for c in rep['changes'] if 'field' in c}
        self.assertEqual(fields[('SplitTime0', 'ExtraTime')], 77.5)
        self.assertEqual(fields[('StartSplitTime', 'TimeToFirstCheckpoint')], 62.5)

    def test_densify_keeps_polyline(self):
        import build_logic as bl
        pts = [(0.0, 0.0, 0.0), (25.0, 0.0, 0.0), (25.0, 0.0, 7.0)]
        d = bl.densify(pts, 10.0)
        self.assertEqual(d[0], pts[0])
        self.assertIn(pts[1], d)
        self.assertEqual(d[-1], pts[-1])
        self.assertTrue(bl.on_polyline([(p[0], p[2]) for p in d], [(p[0], p[2]) for p in pts]))

    def test_classifiers_agree_on_square(self):
        import limit_sim as ls
        # road along +x; in the games' cross form the left border of travel direction +x lies at negative z
        L = [(x, 0.0, -10.0) for x in range(0, 101, 10)]
        R = [(x, 0.0, 10.0) for x in range(0, 101, 10)]
        lists = {'LeftInnerLimit': L, 'RightInnerLimit': R, 'LeftOuterLimit': L, 'RightOuterLimit': R}
        for z, out in ((0.0, False), (15.0, True), (-15.0, True)):
            p = (50.0, 0.0, z)
            self.assertEqual(ls.ps2_outside(L, R, p), out)
            self.assertEqual(ls.pc_state(lists, p) == 2, out)


if __name__ == '__main__':
    unittest.main()
