import struct
import unittest
from tools.scanner.r_demo2_6_hull_diff import compare
from master_rallye.errors import BoundsError


def fixture(*, dx=0.0, bad_section=False):
    header = struct.pack('<8I', 0x20702, 0, 0, 0, 3, 0, 1, 3)
    normals = struct.pack('<9f', 1, 0, 0, 0, 1, 0, 0, 0, 1)
    separator = b'\xff' * 12
    record = struct.pack('<10I', *([0xffffffff] * 4), 0, 1, 2, 0, 1, 2)
    points = b''.join(struct.pack('<3f', x + dx, y, z)
                      for x, y, z in ((0, 0, 0), (1, 0, 0), (0, 1, 0)))
    name = b'$chull'
    tail = (struct.pack('<H', 5) + b'Model' +
            struct.pack('<BBHIIH', 1, 1, 0, 0, 1, len(name)) + name)
    data = bytearray(header + normals + separator + record + points + tail)
    if bad_section:
        data[33] ^= 1
    return bytes(data)


class HullDiffTests(unittest.TestCase):
    expected = ('$chull', 0, 1, range(3), 1, 1)

    def test_pure_translation_preserves_topology_and_changes_plane_offset(self):
        result = compare(fixture(), fixture(dx=.4), expected=self.expected)
        self.assertEqual(result['changed_indices'], [0, 1, 2])
        self.assertTrue(result['topology_unchanged'])
        self.assertTrue(result['non_hull_bytes_unchanged'])
        self.assertEqual(result['record_count'], 1)
        self.assertAlmostEqual(result['source_centroid_after'][0] -
                               result['source_centroid_before'][0], .4, places=6)
        self.assertLess(result['plane_d_predicted_translation_max_residual'], 1e-6)

    def test_rejects_non_hull_byte_edit(self):
        with self.assertRaisesRegex(ValueError, 'non-hull-X edit'):
            compare(fixture(), fixture(dx=.4, bad_section=True), expected=self.expected)

    def test_rejects_wrong_shift_and_identical_pair(self):
        with self.assertRaisesRegex(ValueError, 'translation differs'):
            compare(fixture(), fixture(dx=.3), expected=self.expected)
        with self.assertRaisesRegex(ValueError, 'identical'):
            compare(fixture(), fixture(), expected=self.expected)

    def test_rejects_malformed_layout(self):
        with self.assertRaises(BoundsError):
            compare(fixture()[:-1], fixture(dx=.4)[:-1], expected=self.expected)


if __name__ == '__main__':
    unittest.main()
