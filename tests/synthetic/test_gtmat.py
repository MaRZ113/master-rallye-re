"""Tests for the reusable GT texture primitives (tools/gtmat.py)."""
import unittest

from tools import gtmat
from master_rallye.texture_authoring import decode_rgba_png
from tests.synthetic.test_vmesh_geometry import _png


class TextureTests(unittest.TestCase):
    def test_ps2_alpha_is_normalised_but_translucency_is_kept(self):
        tex = gtmat.GtTexture(_png(4, 1, lambda x, y: (10, 20, 30, (249, 255, 65, 0)[x])))
        self.assertEqual(list(tex.alpha), [255, 255, 65, 0])

    def test_wrap_sampling_and_v_up(self):
        tex = gtmat.GtTexture(_png(2, 2, lambda x, y: (255 if y == 0 else 0, 0, 0, 255)))     # top row red
        self.assertEqual(tex.at_uv(0.25, 0.75)[0], 255)        # v up -> top row
        self.assertEqual(tex.at_uv(0.25, 0.25)[0], 0)
        self.assertEqual(tex.at_uv(1.25, 0.75)[0], 255)        # wraps

    def test_png_round_trip(self):
        px = bytes((i * 7) % 256 for i in range(3 * 2 * 4))
        w, h, back = decode_rgba_png(gtmat.png_from_rgba(3, 2, px))
        self.assertEqual((w, h, bytes(back)), (3, 2, px))


class AlphaClassTests(unittest.TestCase):
    def tex(self, fn):
        return gtmat.GtTexture(_png(16, 16, fn))

    def tri(self, u0, u1):
        return [(u0, 0.1), (u1, 0.1), (u0, 0.9)]

    def test_footprint_not_whole_texture_decides(self):
        tex = self.tex(lambda x, y: (1, 2, 3, 255 if x < 8 else 0))      # right half cleared
        left = gtmat.classify_alpha(gtmat.triangle_alpha_stats(tex, self.tri(0.05, 0.45)))
        right = gtmat.classify_alpha(gtmat.triangle_alpha_stats(tex, [(0.55, 0.1), (0.95, 0.1), (0.55, 0.9)]))
        straddle = gtmat.classify_alpha(gtmat.triangle_alpha_stats(tex, self.tri(0.05, 0.95)))
        self.assertEqual((left, right, straddle), ("opaque", "clear", "cutout"))

    def test_translucent_and_mixed(self):
        translucent = self.tex(lambda x, y: (1, 2, 3, 65))
        self.assertEqual(gtmat.classify_alpha(gtmat.triangle_alpha_stats(translucent, self.tri(0.1, 0.9))), "translucent")
        mixed = self.tex(lambda x, y: (1, 2, 3, (255, 65, 0, 65)[x % 4]))
        self.assertEqual(gtmat.classify_alpha(gtmat.triangle_alpha_stats(mixed, self.tri(0.05, 0.95))), "mixed")

    def test_pass_routing(self):
        self.assertEqual([gtmat.pass_of(c) for c in ("opaque", "clear", "cutout", "translucent", "mixed")],
                         ["opaque", None, "cutout", "blend", "blend"])


class IslandPackingTests(unittest.TestCase):
    def isl(self, key, boxes):
        items = [(key[0], key[1], i, [(b[0], b[2]), (b[1], b[2]), (b[0], b[3])], 1.0) for i, b in enumerate(boxes)]
        return gtmat.build_islands(items)

    def test_overlapping_uv_boxes_merge_and_passes_stay_separate(self):
        a = self.isl(("m", "opaque"), [(0, 0.4, 0, 0.4), (0.3, 0.7, 0.3, 0.7), (0.9, 1.0, 0.9, 1.0)])
        self.assertEqual(sorted(len(i.tris) for i in a), [1, 2])
        both = gtmat.build_islands([("m", "opaque", 0, [(0, 0), (1, 0), (0, 1)], 1.0), ("m", "blend", 1, [(0, 0), (1, 0), (0, 1)], 1.0)])
        self.assertEqual(len(both), 2)

    def test_packing_fits_inside_and_never_overlaps(self):
        islands = self.isl(("m", "opaque"), [(i * 0.1, i * 0.1 + 0.08, 0, 0.5) for i in range(9)])
        pool = gtmat.Pool("p", 64, 64, "opaque")
        density, packed, rejected = gtmat.pack_pool(pool, islands, {"m": (256, 256)})
        self.assertEqual((len(packed), len(rejected)), (9, 0))
        rects = [(x, y, w, h) for _, x, y, w, h in pool.placements]
        for x, y, w, h in rects:
            self.assertTrue(x >= gtmat.GUTTER and y >= gtmat.GUTTER and x + w <= 64 - gtmat.GUTTER + 0 and y + h <= 64)
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                self.assertTrue(a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])

    def test_small_pool_lowers_density_not_correctness(self):
        islands = self.isl(("m", "opaque"), [(0, 1, 0, 1)])
        big, small = gtmat.Pool("b", 128, 128, "opaque"), gtmat.Pool("s", 32, 32, "opaque")
        d_big = gtmat.pack_pool(big, islands, {"m": (512, 512)})[0]
        d_small = gtmat.pack_pool(small, islands, {"m": (512, 512)})[0]
        self.assertGreater(d_big, d_small)

    def test_remap_maps_island_corners_to_the_rectangle_with_v_up(self):
        isl = self.isl(("m", "opaque"), [(0.25, 0.75, 0.25, 0.75)])[0]
        pool = gtmat.Pool("p", 100, 100, "opaque")
        rect = (10, 20, 40, 30)
        u, v = gtmat.remap_uv(pool, isl, rect, (0.25, 0.75))          # island top-left
        self.assertAlmostEqual(u, 10 / 100)
        self.assertAlmostEqual(v, 1 - 20 / 100)
        u, v = gtmat.remap_uv(pool, isl, rect, (0.75, 0.25))          # island bottom-right
        self.assertAlmostEqual(u, 50 / 100)
        self.assertAlmostEqual(v, 1 - 50 / 100)

    def test_render_reproduces_source_colours_and_alpha_scale(self):
        tex = gtmat.GtTexture(_png(8, 8, lambda x, y: ((200, 0, 0, 255) if x < 4 else (0, 0, 200, 255))))
        isl = self.isl(("m", "opaque"), [(0, 1, 0, 1)])[0]
        pool = gtmat.Pool("p", 16, 16, "opaque", alpha_scale=0.5)
        gtmat.pack_pool(pool, [isl], {"m": (8, 8)})
        px = gtmat.render_pool(pool, {"m": tex})
        _, x, y, w, h = pool.placements[0]
        left = px[((y + h // 2) * 16 + x + 1) * 4:][:4]
        right = px[((y + h // 2) * 16 + x + w - 2) * 4:][:4]
        self.assertEqual((left[0], left[2]), (200, 0))
        self.assertEqual((right[0], right[2]), (0, 200))
        self.assertEqual(left[3], 128)                                   # alpha scaled by 0.5

    def test_footprint_mean_and_dilation(self):
        tex = gtmat.GtTexture(_png(8, 8, lambda x, y: (100, 150, 200, 255)))
        rgb, a = gtmat.footprint_mean(bytes(tex.rgba), 8, 8, [(0.1, 0.1), (0.9, 0.1), (0.1, 0.9)])
        self.assertEqual((round(rgb[0]), round(rgb[1]), round(rgb[2]), round(a)), (100, 150, 200, 255))
        px = bytearray(bytes((50, 60, 70, 255)) + bytes(4) * 3)          # 2x2: one visible, three transparent black
        gtmat.dilate_color(px, 2, 2)
        self.assertEqual(tuple(px[4:7]), (50, 60, 70))
        self.assertEqual(px[7], 0)                                       # alpha untouched


if __name__ == "__main__":
    unittest.main()
