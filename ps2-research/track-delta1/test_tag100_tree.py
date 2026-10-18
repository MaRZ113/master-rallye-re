"""Checks for tag100_tree: exact round trip, fill and carve brushes."""
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tag100_tree as tt  # noqa: E402
import tag100_patch as tp  # noqa: E402

RETAIL_DX = Path('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Course/Turkey3/turkey3.dx')


def leaf(f0):
    return struct.pack('<2I4B', f0, 0, 0, 0, 0, 0)


def tiny_tree():
    """Plane y = 0 (normal +y, code 5): back (child) solid below, front (sibling) empty above."""
    root = struct.pack('<2IB4fIBB', 0, 0, 1, 0, 1, 0, 0, 5, 0, 1) + bytes([1]) + leaf(tt.SOLID) + bytes([1, 1]) + leaf(tt.EMPTY)
    return struct.pack('<6I', 100, 1, 1, 1, 1, 0) + root


def slab(x0, x1, z0, z1, y0, y1):
    return [((1, 0, 0), -x1), ((-1, 0, 0), x0), ((0, 0, 1), -z1), ((0, 0, -1), z0), ((0, 1, 0), -y1), ((0, -1, 0), y0)]


class TreeTests(unittest.TestCase):
    def test_round_trip_tiny(self):
        raw = tiny_tree()
        self.assertEqual(tt.Tree(raw).serialize(), raw)

    def test_fill_above_ground(self):
        tree = tt.Tree(tiny_tree())
        self.assertEqual(tree.apply_brush(slab(-2, 2, -2, 2, 0, 3), 7, 'fill'), 1)
        self.assertTrue(tree.counts_ok())
        for point, solid in [((0, 1, 0), True), ((0, 2.9, 1.9), True), ((0, 3.1, 0), False), ((3, 1, 0), False), ((0, -1, 0), True)]:
            self.assertEqual(tree.f0[tree.classify(point)] == tt.SOLID, solid, point)

    def test_carve_into_ground(self):
        tree = tt.Tree(tiny_tree())
        self.assertEqual(tree.apply_brush(slab(-2, 2, -2, 2, -3, 0), 7, 'carve'), 1)
        self.assertTrue(tree.counts_ok())
        for point, solid in [((0, -1, 0), False), ((0, -2.9, 1.9), False), ((0, -3.1, 0), True), ((3, -1, 0), True), ((0, 1, 0), False)]:
            self.assertEqual(tree.f0[tree.classify(point)] == tt.SOLID, solid, point)

    def test_carve_contact_plane_points_to_empty(self):
        tree = tt.Tree(tiny_tree())
        tree.apply_brush(slab(-2, 2, -2, 2, -3, 0), 7, 'carve')
        # walk down from above the carve: the plane that finally separates empty (above) from solid (below) must have its normal pointing up
        i, last_up = 0, None
        point = (0, -2.5, 0)
        while tree.plane[i] is not None:
            nx, ny, nz, d = tree.plane[i][:4]
            front = nx * point[0] + ny * point[1] + nz * point[2] + d >= 0
            if abs(ny) > .9:
                last_up = (ny, front)
            i = tree.sib[i] if front else tree.child[i]
        self.assertEqual(tree.f0[i], tt.EMPTY)
        ny, front = last_up
        self.assertTrue(front)  # the chain bottom face is the last plane crossed; the point is on its front side
        self.assertGreater(ny, 0)

    @unittest.skipUnless(RETAIL_DX.exists(), 'retail corpus not available')
    def test_round_trip_retail(self):
        sys.path.insert(0, str(HERE.parent.parent / 'src'))
        from master_rallye.tag100_diff import extract_tag100_from_dx
        raw = extract_tag100_from_dx(RETAIL_DX).raw
        self.assertEqual(tt.Tree(raw).serialize(), raw)


if __name__ == '__main__':
    unittest.main()
