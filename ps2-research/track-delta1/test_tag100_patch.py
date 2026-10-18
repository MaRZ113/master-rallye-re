"""Synthetic and retail checks for tag100_patch.insert_brush."""
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tag100_patch as tp  # noqa: E402


def tiny_tree():
    """Root plane y = 0 (n = +y): back (child) solid, front (sibling) empty."""
    root = struct.pack('<2IB4fIBB', 0, 0, 1, 0, 1, 0, 0, 0xFFFFFFFF, 0, 1) + bytes([1]) + tp.leaf_bytes(tp.SOLID) + bytes([1, 1]) + tp.leaf_bytes(tp.EMPTY)
    return struct.pack('<6I', 100, 1, 1, 1, 1, 0) + root


def box(cx, cy, cz, h):
    return [(cx + x * h, cy + y * h, cz + z * h) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]


class BrushTests(unittest.TestCase):
    def test_tiny_tree_is_valid(self):
        nodes, parsed = tp.to_nodes(tiny_tree())
        self.assertEqual(len(nodes), 3)
        self.assertTrue(all(parsed.count_invariants().values()), parsed.count_invariants())

    def test_box_in_empty_space(self):
        raw = tiny_tree()
        new, report = tp.insert_brush(raw, box(0, 5, 0, 1))
        self.assertEqual(report['planes'], 6)
        self.assertEqual(report['leaves_replaced'], 1)
        n2, p2 = tp.to_nodes(new)
        self.assertTrue(all(p2.count_invariants().values()), p2.count_invariants())
        for point, solid in [((0, 5, 0), True), ((0.9, 5.9, -0.9), True), ((2, 5, 0), False), ((0, 7, 0), False), ((0, 4.01, 0.99), True),
                             ((0, 3.9, 0), False), ((0, -3, 0), True), ((0, 1, 0), False)]:
            self.assertEqual(tp.classify(n2, point).field_0 == tp.SOLID, solid, point)

    def test_unchanged_outside(self):
        raw = tiny_tree()
        new, _ = tp.insert_brush(raw, box(0, 5, 0, 1))
        n1, _ = tp.to_nodes(raw)
        n2, _ = tp.to_nodes(new)
        for x in range(-6, 7, 2):
            for y in range(-6, 12, 2):
                for z in range(-6, 7, 2):
                    if abs(x) > 1 or abs(z) > 1 or not 4 <= y <= 6:
                        p = (x + .5, y + .5, z + .5)
                        self.assertEqual(tp.classify(n1, p).field_0, tp.classify(n2, p).field_0, p)

    def test_hull_planes_of_prism(self):
        self.assertEqual(len(tp.hull_planes([(x, y, z) for x in (0, 2) for y in (0, 3) for z in (0, 4)])), 6)

    def test_straddling_brush_hits_two_cells(self):
        # a second plane x = 0 splits the empty half-space into two empty cells; a brush across it is inserted into both
        root = struct.pack('<2IB4fIBB', 0, 0, 1, 0, 1, 0, 0, 0xFFFFFFFF, 0, 1) + bytes([1]) + tp.leaf_bytes(tp.SOLID)
        front = struct.pack('<2IB4fIBB', 0, 0, 1, 1, 0, 0, 0, 0xFFFFFFFF, 0, 1) + bytes([1]) + tp.leaf_bytes(tp.EMPTY) + bytes([1, 1]) + tp.leaf_bytes(tp.EMPTY)
        raw = struct.pack('<6I', 100, 2, 1, 2, 2, 0) + root + bytes([1, 0]) + front
        nodes, parsed = tp.to_nodes(raw)
        self.assertTrue(all(parsed.count_invariants().values()), parsed.count_invariants())
        new, report = tp.insert_brush(raw, box(0, 5, 0, 1))
        self.assertEqual(report['leaves_replaced'], 2)
        n2, p2 = tp.to_nodes(new)
        self.assertTrue(all(p2.count_invariants().values()), p2.count_invariants())
        for point in [(-0.5, 5, 0), (0.5, 5, 0), (0, 5, 0.9)]:
            self.assertEqual(tp.classify(n2, point).field_0, tp.SOLID, point)
        self.assertNotEqual(tp.classify(n2, (3, 5, 0)).field_0, tp.SOLID)


if __name__ == '__main__':
    unittest.main()
