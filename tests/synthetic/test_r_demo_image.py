from __future__ import annotations

import struct
import unittest

from master_rallye.errors import BoundsError, FormatError
from master_rallye.gxi import parse_gxi_bytes
from master_rallye.gxb import parse_gxb_bytes
from master_rallye.gxp import gxp_tile_bgra, parse_gxp_bytes


class GxImageTests(unittest.TestCase):
    def test_exact_structure_and_extension_identity(self):
        data = struct.pack("<IHH", 0x00013039, 2, 1) + bytes((1, 2, 3, 4, 5, 6, 7, 8))
        for parse, kind in ((parse_gxi_bytes, "GXI"), (parse_gxb_bytes, "GXB"), (parse_gxp_bytes, "GXP")):
            image = parse(data)
            self.assertEqual((image.kind, image.width, image.height), (kind, 2, 1))
            self.assertEqual(image.rgba, data[8:])
            self.assertEqual(image.header, data[:8])

    def test_gxp_tile_padding_and_channel_order(self):
        pixels = bytes(range(1, 25))
        image = parse_gxp_bytes(struct.pack("<IHH", 0x00013039, 3, 2) + pixels)
        result = gxp_tile_bgra(image, 1, 0, 4, 4)
        expected = (bytes((19, 18, 17, 20, 23, 22, 21, 24)) + b"\0" * 8 +
                    bytes((7, 6, 5, 8, 11, 10, 9, 12)) + b"\0" * 8 +
                    b"\0" * 32)
        self.assertEqual(result, expected)
        with self.assertRaises(ValueError):
            gxp_tile_bgra(image, 3, 0, 4, 4)
        with self.assertRaises(ValueError):
            gxp_tile_bgra(image, 0, 0, 0, 4)
        with self.assertRaises(ValueError):
            gxp_tile_bgra(parse_gxi_bytes(struct.pack("<IHH", 0x00013039, 3, 2) + pixels), 0, 0, 4, 4)

    def test_invalid_headers_and_sizes(self):
        good = struct.pack("<IHH", 0x00013039, 1, 1) + b"\x01\x02\x03\x04"
        for parse in (parse_gxi_bytes, parse_gxb_bytes, parse_gxp_bytes):
            with self.assertRaises(BoundsError):
                parse(good[:7])
            with self.assertRaises(FormatError):
                parse(b"BAD!" + good[4:])
            with self.assertRaises(FormatError):
                parse(struct.pack("<IHH", 0x00013039, 0, 1))
            with self.assertRaises(BoundsError):
                parse(good[:-1])
            with self.assertRaises(BoundsError):
                parse(good + b"\0")


if __name__ == "__main__":
    unittest.main()
