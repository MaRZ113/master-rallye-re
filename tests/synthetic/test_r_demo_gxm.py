from __future__ import annotations

import struct
import unittest

from master_rallye.errors import BoundsError, FormatError
from master_rallye.gxm import (
    parse_gxm_prefix_bytes, parse_gxm_geometry_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)


class GxmPrefixTests(unittest.TestCase):
    def make_sample(self):
        header = struct.pack("<8I", 0x00020702, 0, 0, 1, 6, 2, 2, 1)
        material = (struct.pack("<H", 5) + b"glass" + b"\x02" +
                    b"\x01\x00\x00" + struct.pack("<H", 9) + b"a-tga.gxi" +
                    b"\x00\x00\x00" + struct.pack("<H", 4) + b"Null")
        return header + material + b"opaque-tail"

    def test_prefix_materials_and_opaque_tail(self):
        sample = self.make_sample()
        parsed = parse_gxm_prefix_bytes(sample)
        self.assertEqual(parsed.header_words[3], 1)
        self.assertEqual(parsed.materials[0].name, "glass")
        self.assertEqual(parsed.materials[0].slots[0].reference, "a-tga.gxi")
        self.assertEqual(parsed.materials[0].slots[0].flags3, b"\x01\0\0")
        self.assertEqual(sample[parsed.tail_offset:], b"opaque-tail")

    def test_fail_closed(self):
        sample = self.make_sample()
        with self.assertRaises(BoundsError):
            parse_gxm_prefix_bytes(sample[:31])
        with self.assertRaises(FormatError):
            parse_gxm_prefix_bytes(b"\0\0\0\0" + sample[4:])
        with self.assertRaises(BoundsError):
            parse_gxm_prefix_bytes(sample[:48])

    def test_zero_material_and_empty_vector_b(self):
        header = struct.pack("<8I", 0x00070702, 0, 0, 0, 3, 0, 1, 3)
        vector_a = struct.pack("<9f", 1, 0, 0, 0, 1, 0, 0, 0, 1)
        record = struct.pack("<10I", *(0xFFFFFFFF,) * 4, 0, 1, 2, 0, 1, 2)
        vector_c = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
        sample = header + vector_a + b"\xff" * 12 + record + vector_c + b"tail"
        prefix = parse_gxm_prefix_bytes(sample)
        geometry = parse_gxm_geometry_prefix_bytes(sample, prefix)
        triangles = parse_gxm_triangle_prefix_bytes(sample, prefix, geometry)
        self.assertEqual(prefix.prefix_kind, "material_table")
        self.assertEqual(geometry.vector_b_bounds, ())
        self.assertEqual(triangles.no_material_record_count, 1)
        self.assertEqual(triangles.no_vector_b_record_count, 1)
        self.assertEqual(sample[triangles.hierarchy_offset:], b"tail")

    def test_indexed_vector_sections(self):
        header = struct.pack("<8I", 0x00020702, 0, 0, 1, 3, 3, 1, 3)
        material = struct.pack("<H", 3) + b"mat" + b"\x01\x01\x00\x00" + struct.pack("<H", 5) + b"x.gxi"
        vector_a = struct.pack("<9f", 1, 0, 0, 0, 1, 0, 0, 0, 1)
        vector_b = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
        record = struct.pack("<10I", 0, 0, 1, 2, 0, 1, 2, 0, 1, 2)
        sample = header + material + vector_a + vector_b + b"\xff" * 12 + record + vector_b + b"tail"
        prefix = parse_gxm_prefix_bytes(sample)
        geometry = parse_gxm_geometry_prefix_bytes(sample, prefix)
        triangles = parse_gxm_triangle_prefix_bytes(sample, prefix, geometry)
        self.assertEqual(triangles.record_count, 1)
        self.assertEqual(sample[triangles.hierarchy_offset:], b"tail")
        bad = bytearray(sample)
        struct.pack_into("<I", bad, triangles.record_offset + 4, 3)
        with self.assertRaises(FormatError):
            parse_gxm_triangle_prefix_bytes(bytes(bad), prefix, geometry)

if __name__ == "__main__":
    unittest.main()
