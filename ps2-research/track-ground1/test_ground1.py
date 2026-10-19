"""Regression tests for the TRACK-GROUND1 components (texture choice, DXT headers, ground triangle refinement, noise factor)."""
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TD1 = HERE.parent / 'track-delta1'
sys.path.insert(0, str(TD1))
sys.path.insert(0, str(TD1.parent / 'tools'))
sys.path.insert(0, str(TD1.parent.parent / 'src'))
import ps2_terrain as terrain  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402

RETAIL = Path('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Course/Turkey3')
HEADER = struct.pack('<5I', 0x0000FEED, 1, 0, 0, 0)  # only bytes 0..7 are used as a template
BS = chr(92)


def gradient_rgba(w, h, seed=0):
    """Asymmetric top-down RGBA image: red grows to the right, green grows downward, blue is a diagonal."""
    out = bytearray()
    for y in range(h):
        for x in range(w):
            out += bytes([(x * 255 // max(1, w - 1)) ^ seed, (y * 255 // max(1, h - 1)), ((x + y) * 255 // max(1, w + h - 2)), 255])
    return bytes(out)


def pc_dxt_from_rgba(rgba, w, h, scale):
    """PC style file (bottom-up BGRA rows) of the same picture enlarged by `scale`."""
    rows = []
    for y in range(h * scale):
        src_y = y // scale
        row = bytearray()
        for x in range(w * scale):
            i = (src_y * w + x // scale) * 4
            row += bytes([rgba[i + 2], rgba[i + 1], rgba[i], 255])
        rows.append(bytes(row))
    payload = b''.join(reversed(rows))  # bottom-up
    return terrain.make_dxt(payload, w * scale, h * scale, HEADER)


class TextureTests(unittest.TestCase):
    def test_make_dxt_header_is_payload_crc(self):
        data = terrain.make_dxt(bytes(range(64)) * 4, 8, 8, HEADER)
        magic, w4, w8, w, h = struct.unpack_from('<5I', data)
        self.assertEqual((w, h), (8, 8))
        self.assertEqual(w8, zlib.crc32(data[20:]) & 0xFFFFFFFF)
        parse_dxt_bytes(data)
        with self.assertRaises(ValueError):
            terrain.make_dxt(b'abc', 8, 8, HEADER)

    @unittest.skipUnless(RETAIL.exists(), 'retail corpus not available')
    def test_retail_dxt_headers_are_payload_crc(self):
        for f in sorted(RETAIL.glob('*.dxt'))[:20]:
            data = f.read_bytes()
            self.assertEqual(struct.unpack_from('<I', data, 8)[0], zlib.crc32(data[20:]) & 0xFFFFFFFF, f.name)

    def test_orientation_expected_is_best(self):
        rgba = gradient_rgba(16, 16)
        pc = parse_dxt_bytes(pc_dxt_from_rgba(rgba, 16, 16, 2))
        good = terrain.texture_difference(pc, rgba, 16, 16)
        self.assertLess(good, 1.0)
        for kw in (dict(flip_rows=False), dict(flip_rows=True, flip_cols=True), dict(flip_rows=False, flip_cols=True)):
            self.assertGreater(terrain.texture_difference(pc, rgba, 16, 16, **kw), good + 10)

    def test_choose_pc_same_name(self):
        rgba = gradient_rgba(16, 16)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'rock-tga.dxt').write_bytes(pc_dxt_from_rgba(rgba, 16, 16, 2))
            data, size, source = terrain.choose_texture('rock-tga', rgba, 16, 16, HEADER, d)
            self.assertEqual((size, source), ((32, 32), 'pc'))

    def test_different_artwork_keeps_ps2(self):
        ps2 = gradient_rgba(16, 16)
        other = gradient_rgba(16, 16, seed=0x55)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'rock-tga.dxt').write_bytes(pc_dxt_from_rgba(other, 16, 16, 2))
            data, size, source = terrain.choose_texture('rock-tga', ps2, 16, 16, HEADER, d)
            self.assertEqual((size, source), ((16, 16), 'ps2'))
            self.assertEqual(struct.unpack_from('<I', data, 8)[0], zlib.crc32(data[20:]) & 0xFFFFFFFF)

    def test_renamed_pc_texture_is_found(self):
        ps2 = gradient_rgba(16, 16)
        other = gradient_rgba(16, 16, seed=0x55)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'plating-tga.dxt').write_bytes(pc_dxt_from_rgba(other, 16, 16, 2))   # same name, other art
            (Path(d) / 'tanky-tga.dxt').write_bytes(pc_dxt_from_rgba(ps2, 16, 16, 2))        # PS2 art under another name
            _, size, source = terrain.choose_texture('plating-tga', ps2, 16, 16, HEADER, d)
            self.assertEqual((size, source), ((32, 32), 'pc_renamed:tanky-tga'))

    def test_missing_pc_file_and_unreadable_ps2(self):
        rgba = gradient_rgba(8, 8)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(terrain.choose_texture('nothing-tga', rgba, 8, 8, HEADER, d)[2], 'ps2')
            self.assertIsNone(terrain.choose_texture('nothing-tga', None, None, None, HEADER, d))
            (Path(d) / 'only-tga.dxt').write_bytes(pc_dxt_from_rgba(rgba, 8, 8, 2))
            self.assertEqual(terrain.choose_texture('only-tga', None, None, None, HEADER, d)[2], 'pc_unchecked')

    @unittest.skipUnless(RETAIL.exists(), 'retail corpus not available')
    def test_noise_mean_factor_retail(self):
        self.assertAlmostEqual(terrain.noise_mean_factor(RETAIL), 0.9537, places=3)


def tri(points, tex, uv, color=(200, 200, 200, 255)):
    return {'p': tuple(points), 'tex': 'Course' + BS + 'turkey3' + BS + tex, 'uv': tuple(uv), 'col': (color,) * 3, 'ground': True, 'mesh': 'm'}


def pc_tri(points, tex, uv, draw=0, first=0):
    return {'p': tuple(points), 'tex': tex, 'uv': tuple(uv), 'ground': True, 'draw': draw, 'first_index': first}


class RefineTests(unittest.TestCase):
    A = ((0.0, 5.0, 0.0), (10.0, 5.0, 0.0), (0.0, 5.0, 10.0))
    UV = ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))

    def run_refine(self, ps2, pc):
        return terrain.refine([ps2], [pc], [pc])

    def test_integer_uv_offset_is_equivalent(self):
        uv = tuple((u + 3.0, v - 5.0) for u, v in self.UV)
        replace, candidates, stats = self.run_refine(tri(self.A, 'rock-tga', uv), pc_tri(self.A, 'rock-tga', self.UV))
        self.assertEqual((len(replace), len(candidates)), (0, 0))
        self.assertEqual(stats['equivalent_integer_uv_offset'], 1)

    def test_height_texture_and_uv_differences_replace(self):
        high = tuple((x, y + 0.5, z) for x, y, z in self.A)
        r, c, s = self.run_refine(tri(high, 'rock-tga', self.UV), pc_tri(self.A, 'rock-tga', self.UV))
        self.assertEqual((len(r), len(c), s['geometry_differs']), (1, 1, 1))
        r, c, s = self.run_refine(tri(self.A, 'mud-tga', self.UV), pc_tri(self.A, 'rock-tga', self.UV))
        self.assertEqual((len(r), len(c), s['base_texture_differs']), (1, 1, 1))
        other_uv = ((0.0, 0.0), (2.0, 0.0), (0.0, 1.0))
        r, c, s = self.run_refine(tri(self.A, 'rock-tga', other_uv), pc_tri(self.A, 'rock-tga', self.UV))
        self.assertEqual((len(r), len(c), s['uv_mapping_differs']), (1, 1, 1))
        mixed = ((1.0, 0.0), (1.0, 0.0), (0.0, 1.0))  # offsets differ per vertex: not one mapping
        r, c, s = self.run_refine(tri(self.A, 'rock-tga', mixed), pc_tri(self.A, 'rock-tga', self.UV))
        self.assertEqual(s['uv_mapping_differs'], 1)

    def test_no_pc_footprint_replaces(self):
        far = tuple((x + 100, y, z) for x, y, z in self.A)
        r, c, s = terrain.refine([tri(far, 'rock-tga', self.UV)], [], [pc_tri(self.A, 'rock-tga', self.UV)])
        self.assertEqual((len(r), s['no_pc_footprint']), (1, 1))


if __name__ == '__main__':
    unittest.main()
