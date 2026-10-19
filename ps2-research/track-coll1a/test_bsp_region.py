"""Synthetic and real-data tests for the regional PS2 BSP -> PC tag100 transplant (TRACK-COLL1A)."""
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
import bsp_graft as bg  # noqa: E402
import bsp_region as br  # noqa: E402
import bsp_query as q  # noqa: E402
import ps2_bsp  # noqa: E402
import region_validate as rv  # noqa: E402
import tag100_tree as tt  # noqa: E402

LO, HI = (-10.0, -6.0, -10.0), (10.0, 8.0, 10.0)
BSP_FILE = HERE.parent / 'data/track-bsp/TURKEY3.BSP'
RETAIL_DX = Path('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Course/Turkey3/turkey3.dx')
G1_DX = Path('D:/Game/Master Rallye/research-output/t4-terrain-g1/DataGx/Course/Turkey3/turkey3.dx')


def leaf(f0):
    return struct.pack('<2I4B', f0, 0, 0, 0, 0, 0)


def pc_tree(ground_y=0.0, code=5):
    """PC tag100: plane y = ground_y, back (below) solid, front (above) empty."""
    root = struct.pack('<2IB4fIBB', 0, 0, 1, 0, 1, 0, -ground_y, code, 0, 1) + bytes([1]) + leaf(tt.SOLID) + bytes([1, 1]) + leaf(tt.EMPTY)
    return struct.pack('<6I', 100, 1, 1, 1, 1, 0) + root


def box_planes(x0, x1, y0, y1, z0, z1):
    return [(1, 0, 0, -x1), (-1, 0, 0, x0), (0, 1, 0, -y1), (0, -1, 0, y0), (0, 0, 1, -z1), (0, 0, -1, z0)]


class Builder:
    """Hand made PS2 BSP: plane nodes, solid / empty leaves and payload leaves."""

    def __init__(self):
        self.nodes, self.table = [], []

    def add(self, plane=None, f0=1, payload=None):
        n = ps2_bsp.Node(len(self.nodes), 0, 0, f0, 0, plane, payload, None, None)
        self.nodes.append(n)
        return n.index

    def plane_node(self, plane, back, front):
        i = self.add(plane=plane + (7,), f0=0)
        self.nodes[i].child, self.nodes[i].sibling = back, front
        return i

    def solid(self):
        return self.add(f0=0xFFFFFFFF)

    def empty(self):
        return self.add(f0=1)

    def block(self, box):
        start = len(self.table)
        self.table += [p + (900 + k,) for k, p in enumerate(box_planes(*box))]
        return self.add(f0=0, payload=(start, len(box_planes(*box))))

    def build(self):
        return ps2_bsp.Bsp(header=(0, 0, 0, 0, 0, len(self.table)), nodes=self.nodes, plane_table=self.table)


def ps2_ground(height, blocks=(), split_x=0.0):
    """Root node first. Ground plane y = height (below solid); above it up to two payload blocks separated by the plane x = split_x."""
    b = Builder()
    root = b.plane_node((0.0, 1.0, 0.0, -height), 0, 0)    # placeholders, root must be index 0
    solid = b.solid()
    if not blocks:
        front = b.empty()
    elif len(blocks) == 1:
        front = b.block(blocks[0])
    else:
        a, c = b.block(blocks[0]), b.block(blocks[1])
        front = b.plane_node((1.0, 0.0, 0.0, -split_x), a, c)
    b.nodes[root].child, b.nodes[root].sibling = solid, front
    return b.build()


def solid_pc(tree, p):
    return tree.f0[tree.classify(p)] == tt.SOLID


def solid_ps2(bsp, p):
    return q.ps2_is_solid(bsp, p)


class ConvexCellTests(unittest.TestCase):
    def test_volume_and_clip(self):
        c = br.ConvexCell.box((0, 0, 0), (2, 2, 2))
        self.assertAlmostEqual(c.volume(), 8.0)
        self.assertAlmostEqual(c.clip((1, 1, 0, -2)).volume(), 4.0)
        self.assertAlmostEqual(c.clip((1, 1, 0, -2)).clip((0, -1, 0, 0.5)).volume(), 2.25)
        self.assertIsNone(c.clip((1, 0, 0, 0.0)))               # x <= 0 touches only the face
        self.assertIsNone(c.clip((1, 0, 0, 1.0)))               # x <= -1 is outside
        self.assertAlmostEqual(c.clip((1, 0, 0, -5)).volume(), 8.0)  # x <= 5 keeps everything

    def test_halfspaces_are_original_planes(self):
        c = br.ConvexCell.box((0, 0, 0), (2, 2, 2)).clip((1, 1, 0, -2))
        hs = c.halfspaces()
        self.assertEqual(len(hs), 5)
        self.assertIn(((1, 1, 0), -2), hs)


class SolidVolumeTests(unittest.TestCase):
    def test_ground_only(self):
        bsp = ps2_ground(2.0)
        cells, stats = br.solid_volumes(bsp, LO, HI)
        self.assertEqual(len(cells), 1)
        self.assertAlmostEqual(cells[0].volume(), 20 * 8 * 20)   # y -6 .. 2
        self.assertEqual(stats['solid_leaves'], 1)

    def test_payload_blocks_are_disconnected(self):
        bsp = ps2_ground(0.0, blocks=[(-8, -4, 0, 3, -2, 2), (4, 8, 0, 5, -2, 2)])
        cells, _ = br.solid_volumes(bsp, LO, HI)
        vols = sorted(c.volume() for c in cells)
        for got, want in zip(vols, sorted([6 * 20 * 20, 4 * 3 * 4, 4 * 5 * 4])):
            self.assertAlmostEqual(got, want, delta=want * 1e-3)   # payload planes are inset by the original 1e-4 epsilon
        self.assertEqual(len(vols), 3)

    def test_empty_run_payload_is_whole_cell(self):
        b = Builder()
        root = b.plane_node((1.0, 0.0, 0.0, 0.0), 0, 0)
        b.nodes[root].child = b.add(f0=0, payload=(0, 0))
        b.nodes[root].sibling = b.empty()
        cells, _ = br.solid_volumes(b.build(), LO, HI)
        self.assertEqual(len(cells), 1)
        self.assertAlmostEqual(cells[0].volume(), 10 * 14 * 20)


class TransplantTests(unittest.TestCase):
    def check_against_ps2(self, tree, bsp, points):
        for p in points:
            self.assertEqual(solid_pc(tree, p), solid_ps2(bsp, p), p)

    def grid(self, ys):
        return [(x, y, z) for x in (-9.5, -3.3, 0.7, 6.1, 9.4) for z in (-9.2, -1.1, 4.4, 9.8) for y in ys]

    def test_raised_terrain(self):
        bsp = ps2_ground(2.0)
        tree = tt.Tree(pc_tree(0.0))
        rep = bg.transplant(tree, bsp, LO, HI)
        self.assertTrue(tree.counts_ok())
        self.check_against_ps2(tree, bsp, self.grid([-5.5, -1, 0.5, 1.9, 2.1, 3, 7.9]))
        self.assertFalse(solid_pc(tree, (30, 1.0, 0)))          # outside the box: still the old ground at y = 0
        self.assertTrue(solid_pc(tree, (30, -1.0, 0)))
        self.assertEqual(rep['method'], 'graft')

    def test_lowered_terrain(self):
        bsp = ps2_ground(-2.0)
        tree = tt.Tree(pc_tree(0.0))
        bg.transplant(tree, bsp, LO, HI)
        self.check_against_ps2(tree, bsp, self.grid([-5.5, -3, -2.1, -1.9, -1, 0.5, 3]))
        self.assertTrue(solid_pc(tree, (30, -0.5, 0)))
        self.assertFalse(solid_pc(tree, (0, -0.5, 0)))          # PS2 is empty there
        self.assertFalse(solid_pc(tree, (11, 5.0, 0)))

    def test_disconnected_solids(self):
        bsp = ps2_ground(0.0, blocks=[(-8, -4, 0, 3, -2, 2), (4, 8, 0, 5, -2, 2)])
        tree = tt.Tree(pc_tree(0.0))
        bg.transplant(tree, bsp, LO, HI)
        for p, s in [((-6, 1, 0), True), ((6, 4, 0), True), ((0, 1, 0), False), ((-6, 4, 0), False), ((6, 6, 0), False), ((-6, 1, 5), False)]:
            self.assertEqual(solid_pc(tree, p), s, p)
        self.check_against_ps2(tree, bsp, self.grid([-5, -1, 0.5, 2.9, 4.5, 6]))

    def test_solid_larger_than_the_region_is_clipped(self):
        bsp = ps2_ground(0.0, blocks=[(-30, -4, 0, 6, -2, 2)])   # block continues far outside the box on the -x side
        tree = tt.Tree(pc_tree(0.0))
        bg.transplant(tree, bsp, LO, HI)
        self.assertTrue(solid_pc(tree, (-9, 3, 0)))
        self.assertFalse(solid_pc(tree, (-12, 3, 0)))            # outside the box: the PC tree has no such block
        self.assertFalse(solid_pc(tree, (-10.01, 3, 0)))
        self.assertTrue(solid_pc(tree, (-9.99, 3, 0)))

    def test_fragmented_pc_tree_with_cells_inside_and_across_the_box(self):
        tree = tt.Tree(pc_tree(0.0))
        # invisible PC bumps: one inside the box, one crossing the +x wall, one outside
        tree.apply_brush([((1, 0, 0), -2), ((-1, 0, 0), -2), ((0, 1, 0), -3), ((0, -1, 0), 0), ((0, 0, 1), -2), ((0, 0, -1), -2)], 11, 'fill')
        tree.apply_brush([((1, 0, 0), -14), ((-1, 0, 0), 6), ((0, 1, 0), -2), ((0, -1, 0), 0), ((0, 0, 1), -1), ((0, 0, -1), -1)], 11, 'fill')
        tree.apply_brush([((1, 0, 0), -50), ((-1, 0, 0), 40), ((0, 1, 0), -2), ((0, -1, 0), 0), ((0, 0, 1), -1), ((0, 0, -1), -1)], 11, 'fill')
        before = tt.Tree(tree.serialize())
        bsp = ps2_ground(0.0)
        bg.transplant(tree, bsp, LO, HI)
        self.assertTrue(tree.counts_ok())
        self.assertFalse(solid_pc(tree, (0, 1.5, 0)))            # the inside bump is gone
        self.assertFalse(solid_pc(tree, (8, 1.0, 0)))            # the part of the straddling bump inside the box is gone
        self.assertTrue(solid_pc(tree, (12, 1.0, 0)))            # the part outside the box stays
        self.assertTrue(solid_pc(tree, (45, 1.0, 0)))
        # nothing outside the box changed
        n, diffs = rv.outside_sample_check(before, tree, LO, HI, extent=30.0, step=1.7)
        self.assertGreater(n, 1000)
        self.assertEqual(diffs, [])
        n, diffs = rv.boundary_ring_check(before, tree, LO, HI, step=1.0)
        self.assertEqual(diffs, [])

    def test_matches_brush_method(self):
        bsp = ps2_ground(1.0, blocks=[(-8, -4, 1, 3, -2, 2), (4, 8, 1, 5, -2, 2)])
        a, b = tt.Tree(pc_tree(0.0)), tt.Tree(pc_tree(0.0))
        bg.transplant(a, bsp, LO, HI)
        br.transplant_brush(b, bsp, LO, HI)
        pts = self.grid([-5, -1, 0.5, 1.5, 2.9, 4.5, 6, 7.5]) + [(40, 0.5, 0), (40, -0.5, 0)]
        for p in pts:
            self.assertEqual(solid_pc(a, p), solid_pc(b, p), p)

    def test_codes_and_orientation(self):
        bsp = ps2_ground(2.0, blocks=[(-8, -4, 2, 3, -2, 2)])
        tree = tt.Tree(pc_tree(0.0, code=5))
        n0 = len(tree.plane)
        bg.transplant(tree, bsp, LO, HI)
        new_codes = [c for c in tree.code[n0:] if c is not None]
        self.assertTrue(new_codes)
        self.assertTrue(all(c < 0x80000000 for c in new_codes))
        self.assertTrue(solid_pc(tree, (-6, 2.5, 0)))           # block: solid behind its planes
        self.assertFalse(solid_pc(tree, (-6, 3.5, 0)))          # empty in front of the top plane (normals point toward the empty side)

    def test_rollback_restores_the_tree(self):
        raw = pc_tree(0.0)
        tree = tt.Tree(raw)
        n0 = len(tree.plane)
        with self.assertRaises(ValueError):
            bg.transplant(tree, ps2_ground(2.0), LO, HI, code=0xFFFFFFFF)
        self.assertEqual(tree.serialize(), raw)
        self.assertEqual(len(tree.plane), n0)
        # a failure in the middle of the walk (a PS2 BSP without nodes) is rolled back as well
        with self.assertRaises(Exception):
            bg.transplant(tree, ps2_bsp.Bsp(header=(0,) * 6, nodes=[], plane_table=[]), LO, HI)
        self.assertEqual(tree.serialize(), raw)
        self.assertEqual(len(tree.plane), n0)
        self.assertEqual(len(tree.child), n0)

    def test_deterministic(self):
        bsp = ps2_ground(2.0, blocks=[(-8, -4, 2, 3, -2, 2)])
        out = []
        for _ in range(2):
            tree = tt.Tree(pc_tree(0.0))
            bg.transplant(tree, bsp, LO, HI)
            out.append(tree.serialize())
        self.assertEqual(out[0], out[1])

    def test_round_trip_after_transplant(self):
        bsp = ps2_ground(-2.0, blocks=[(-8, -4, -2, 3, -2, 2)])
        tree = tt.Tree(pc_tree(0.0))
        bg.transplant(tree, bsp, LO, HI)
        raw = tree.serialize()
        self.assertEqual(tt.Tree(raw).serialize(), raw)

    def test_ray_and_grid_validation_helpers(self):
        bsp = ps2_ground(2.0)
        tree = tt.Tree(pc_tree(0.0))
        ref = tt.Tree(pc_tree(0.0))
        bg.transplant(tree, bsp, LO, HI)
        rows, stats = rv.first_contact_table(bsp, {'candidate': tree, 'original': ref}, LO, HI)
        self.assertEqual(stats['candidate']['agree'], len(rows))
        self.assertEqual(stats['original']['agree'], 0)
        res = rv.ray_check(bsp, ref, tree, LO, HI, rv.region_rays(LO, HI, margin=10, count=40))
        self.assertEqual(res['inside_mismatch'], [])
        self.assertEqual(res['outside_mismatch'], [])


@unittest.skipUnless(BSP_FILE.exists() and RETAIL_DX.exists() and G1_DX.exists(), 'Turkey3 data not available')
class Turkey3Rank1(unittest.TestCase):
    def test_rank1_from_retail_and_from_ground1(self):
        import region_transplant as rt
        bsp = ps2_bsp.parse(BSP_FILE.read_bytes())
        lo, hi = (2142.5, 6.0, -4.27), (2202.5, 27.0, 31.73)
        retail, g1 = RETAIL_DX.read_bytes(), G1_DX.read_bytes()
        for base in (retail, g1):
            new_dx, rep, trees = rt.build(retail, base, bsp, lo, hi, 'turkey3.dx')
            rt.validate(bsp, lo, hi, trees, rep)
            checks = rt.passed(rep)
            self.assertTrue(all(checks.values()), checks)
            self.assertLess(abs(rep['structure']['node_growth_percent']), 1.0)
            again, _, _ = rt.build(retail, base, bsp, lo, hi, 'turkey3.dx')
            self.assertEqual(new_dx, again)


if __name__ == '__main__':
    unittest.main()
