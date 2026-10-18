import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ps2_bsp as b  # noqa: E402


def plane(nx, ny, nz, d, code):
    return struct.pack('<4fI', nx, ny, nz, d, code)


def tiny():
    """root (plane) with a child leaf (payload run 0..1) and a sibling leaf (no payload)."""
    h = struct.pack('<6I', 1, 0, 0, 1, 1, 1)
    root = struct.pack('<2I', 0, 0) + b'\x01' + plane(1, 0, 0, -5, 0xffffffff) + b'\x00'
    root += b'\x01' + b'\x00\x00'            # child present, selectors
    leaf1 = struct.pack('<2I', 1, 0) + b'\x00' + b'\x01' + struct.pack('<2I', 0, 1)
    leaf1 += b'\x00' + b'\x01' + b'\x00\x00'   # no child; sibling present with selectors
    leaf2 = struct.pack('<2I', 0xffffffff, 0) + b'\x00' + b'\x00' + b'\x00' + b'\x00'
    table = plane(0, 1, 0, 0, 7)
    return h + root + leaf1 + leaf2 + bytes(1) + table  # the root's sibling flag follows its child subtree


class Ps2BspTest(unittest.TestCase):
    def test_tiny_tree(self):
        bsp = b.parse(tiny())
        s = b.summary(bsp)
        self.assertEqual(s['nodes'], 3)
        self.assertEqual(s['nodes_with_plane'], 1)
        self.assertEqual(s['nodes_with_payload'], 1)
        self.assertEqual(s['plane_table'], 1)
        self.assertEqual(s['trailing'], 0)
        self.assertEqual(bsp.nodes[0].child, 1)
        self.assertEqual(bsp.nodes[1].sibling, 2)
        self.assertEqual(bsp.nodes[1].payload, (0, 1))

    def test_truncated_raises(self):
        with self.assertRaises(Exception):
            b.parse(tiny()[:-3])


if __name__ == '__main__':
    unittest.main()
