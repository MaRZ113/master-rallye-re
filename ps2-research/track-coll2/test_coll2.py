"""Tests for the full-course collision conversion (W1)."""
import math
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'track-coll1a'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
sys.path.insert(0, str(HERE.parent / 'course-port'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import bsp_query as q  # noqa: E402
import ps2_to_tag100 as conv  # noqa: E402
import surface_grid as sg  # noqa: E402
import tag100_tree as tt  # noqa: E402
import tag1400_io as io  # noqa: E402
from test_bsp_region import Builder, pc_tree, ps2_ground  # noqa: E402
from master_rallye.course_tag1400 import parse_course_tag1400_bytes  # noqa: E402

RETAIL_DX = Path('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Course/Turkey3/turkey3.dx')


def solid(tree, p):
    return tree.f0[tree.classify(p)] == tt.SOLID


def stats_splitters(bsp):
    return sum(1 for n in bsp.nodes if n.plane is not None and n.plane[4] == conv.PS2_SPLITTER)


def ground_with_splitter():
    """Ground y = 0 (code 7) with a vertical PS2 splitter x = 0 (code 0xFFFFFFFF) inside the solid below it."""
    b = Builder()
    root = b.plane_node((0.0, 1.0, 0.0, 0.0), 0, 0)
    b.nodes[root].sibling = b.empty()
    split = b.add(plane=(1.0, 0.0, 0.0, 0.0, conv.PS2_SPLITTER), f0=0)
    b.nodes[split].child, b.nodes[split].sibling = b.solid(), b.solid()
    b.nodes[root].child = split
    return b.build()


class ConvertTests(unittest.TestCase):
    def codes(self):
        return conv.PlaneCodes(tt.Tree(pc_tree(0.0, code=5)), (0, 10, 0))

    def grid(self):
        return [(x, y, z) for x in (-9.5, -6.1, -3.3, 0.7, 4.9, 6.1, 9.4) for z in (-9.2, -1.1, 0.5, 4.4) for y in (-5, -1, 0.5, 1.5, 2.9, 4.5, 6)]

    def check(self, bsp, prune=True):
        tree, stats = conv.convert(bsp, self.codes(), prune=prune)
        self.assertTrue(tree.counts_ok())
        for p in self.grid():
            self.assertEqual(solid(tree, p), q.ps2_is_solid(bsp, p), p)
        # negative (no contact) codes only where the PS2 tree plane is a splitter coded 0xFFFFFFFF
        self.assertEqual(sum(1 for c in tree.code if c is not None and c >= 0x80000000), stats_splitters(bsp))
        raw = tree.serialize()
        self.assertEqual(tt.Tree(raw).serialize(), raw)
        return tree, stats

    def test_ground_and_blocks(self):
        for prune in (True, False):
            self.check(ps2_ground(1.0, blocks=[(-8, -4, 1, 3, -2, 2), (4, 8, 1, 5, -2, 2)]), prune)

    def test_empty_run_payload_is_solid(self):
        b = Builder()
        root = b.plane_node((1.0, 0.0, 0.0, 0.0), 0, 0)
        b.nodes[root].child = b.add(f0=0, payload=(0, 0))
        b.nodes[root].sibling = b.empty()
        tree, _ = self.check(b.build())
        self.assertTrue(solid(tree, (-1, 0, 0)))
        self.assertFalse(solid(tree, (1, 0, 0)))

    def test_thin_cell_keeps_the_ps2_epsilon(self):
        # cell 0 <= y < 0.0005 is a payload leaf whose run plane is y = 0.00012: PS2 solid only where y <= 0.00002
        b = Builder()
        root = b.plane_node((0.0, 1.0, 0.0, -0.0005), 0, 0)
        b.nodes[root].sibling = b.empty()
        low = b.plane_node((0.0, 1.0, 0.0, 0.0), 0, 0)
        b.nodes[root].child = low
        b.nodes[low].child = b.solid()
        b.table.append((0.0, 1.0, 0.0, -0.00012, 1))
        b.nodes[low].sibling = b.add(f0=0, payload=(0, 1))
        bsp = b.build()
        tree, _ = conv.convert(bsp, self.codes())
        for y in (0.0001, 0.0003, 0.00001, -0.1):
            self.assertEqual(solid(tree, (0, y, 0)), q.ps2_is_solid(bsp, (0, y, 0)), y)
        self.assertGreaterEqual(conv.inset_d(-0.00012), -0.00012 + conv.PS2_EPS)
        self.assertGreaterEqual(conv.inset_d(-2500.123), -2500.123 + conv.PS2_EPS)

    def test_ps2_splitter_keeps_no_contact_code(self):
        # the engine's nearest-plane fallback must pick the ground under the surface, not the splitter 0.01 away (Turkey2 one-sided wall)
        import validate_collision as vc
        bsp = ground_with_splitter()
        tree, stats = self.check(bsp)
        p = (-0.01, -0.05, 0.0)
        self.assertEqual(vc.ps2_fallback(bsp, p)[1], (0.0, 1.0, 0.0, 0.0))
        self.assertEqual(vc.pc_fallback(tree, p)[1], (0.0, 1.0, 0.0, 0.0))
        old, _ = conv.convert(bsp, self.codes(), keep_splitters=False)
        self.assertEqual(vc.pc_fallback(old, p)[1], (1.0, 0.0, 0.0, 0.0))      # the earlier build: the splitter becomes the contact plane

    def test_same_plane_code_is_taken_from_pc(self):
        bsp = ps2_ground(0.0)          # the PS2 ground plane equals the PC plane y = 0 (code 5)
        codes = self.codes()
        tree, _ = conv.convert(bsp, codes)
        self.assertEqual(tree.code[0], 5)
        self.assertEqual(codes.provenance['pc_same_plane'], 1)

    def test_other_plane_gets_path_code(self):
        codes = self.codes()
        conv.convert(ps2_ground(2.0), codes)
        self.assertEqual(codes.provenance['pc_same_plane'], 0)
        self.assertEqual(codes.provenance['pc_ground_path'] + codes.provenance['default'], 1)


class Tag1400Tests(unittest.TestCase):
    def test_build_rule_on_synthetic_triangles(self):
        tris = [((0, 0, 0, 30, 0, 0, 0, 0, 30), b'$surfacetype(grass) $shader(ground)'),
                ((45, 1, 45, 50, 1, 45, 45, 1, 50), b'$surfacetype(gravel) $shader(ground)'),
                ((5, 0, 5, 5, 0, 5, 6, 0, 6), b'$surfacetype(grass) $shader(ground)')]   # degenerate
        raw, rep = sg.build(tris)
        t = parse_course_tag1400_bytes(raw, 'x')
        self.assertEqual((t.dimension_0, t.dimension_1), (3, 3))     # extent 50 / 20 -> 3 cells
        self.assertEqual(t.vector_a, (0.0, 0.0, 0.0))
        self.assertEqual(list(t.cells[0].entries), [0, 2])           # cell (0,0) holds the big triangle and the degenerate one
        self.assertEqual(list(t.cells[1].entries), [0])
        self.assertEqual(list(t.cells[8].entries), [1])
        self.assertEqual(len(t.strings), 2)
        self.assertEqual(rep['degenerate_nan_plane'], 1)
        self.assertTrue(math.isnan(t.records[2].float_suffix[0]))
        n = t.records[0].float_suffix
        self.assertAlmostEqual(n[1], -1.0)                          # (b-a) x (c-a) for this winding points down, as in retail

    def test_detail_tokens_are_removed(self):
        self.assertEqual(sg.DETAIL.sub('', '$surfacetype(grass) $shader(ground) $detail(shrubs)$grnd:grass_hardNoise Pass'),
                         '$surfacetype(grass) $shader(ground)$grnd:grass_hardNoise Pass')
        self.assertEqual(sg.surface_type(b'$surfacetype(gravel) $shader(ground)'), 'gravel')

    @unittest.skipUnless(RETAIL_DX.exists(), 'retail data not available')
    def test_retail_turkey3_round_trip_and_rule(self):
        from master_rallye.tag100_diff import extract_tag100_from_dx_bytes
        raw = extract_tag100_from_dx_bytes(RETAIL_DX.read_bytes(), 't').raw
        tree, b1339, u, rest = io.split_suffix(raw)
        self.assertEqual(tree + b1339 + u + rest, raw)
        t = parse_course_tag1400_bytes(u, 't')
        self.assertEqual(io.from_parsed(t), u)
        self.assertEqual(sg.rebuild_from_parsed(t), u)


@unittest.skipUnless(RETAIL_DX.exists(), 'retail data not available')
class CourseConfigTests(unittest.TestCase):
    def test_36_courses(self):
        import course_config as cc
        cs = cc.courses()
        self.assertEqual(len(cs), 36)
        self.assertEqual(len({c.pc_dx for c in cs}), 36)
        self.assertEqual(cc.course('Italy1').pc_landscape, 'course\\italy1\\track01')


if __name__ == '__main__':
    unittest.main()
