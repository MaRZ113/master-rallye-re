"""Regressions for filtered magenta and clipped lamp coverage, no donor data."""
import unittest
from master_rallye.material_derivation import transparent_edge_padding,polygon_pixels,lens_textures


class MaterialDerivationTests(unittest.TestCase):
    def test_filtered_magenta_reproduces_then_disappears_without_alpha_dilation(self):
        raw=bytes((100,100,100,255,255,0,255,0,255,0,255,0))
        # Half-texel sample would pass alpha128 with strong magenta RGB.
        before=tuple((raw[k]+raw[4+k])/2 for k in range(4))
        self.assertGreater(before[0],before[1]);self.assertGreater(before[2],before[1])
        padded,report=transparent_edge_padding(raw,3,1,radius=1)
        after=tuple((padded[k]+padded[4+k])/2 for k in range(4))
        self.assertEqual(after[:3],(100,100,100))
        self.assertEqual(raw[3::4],padded[3::4]);self.assertEqual(raw[:4],padded[:4])
        self.assertEqual(raw[8:],padded[8:]);self.assertEqual(report['changed_zero_alpha_rgb_pixels'],1)

    def test_partial_alpha_is_never_changed_or_used_as_opaque_seed(self):
        raw=bytes((20,30,40,255,250,0,250,128,255,0,255,0))
        padded,_=transparent_edge_padding(raw,3,1,radius=8)
        self.assertEqual(raw,padded)

    def test_deterministic_padding_preserves_opaque_pixels_and_bounds(self):
        raw=bytes((30,40,50,255,255,0,255,0,80,90,100,255))
        a=transparent_edge_padding(raw,3,1);b=transparent_edge_padding(raw,3,1)
        self.assertEqual(a,b);self.assertEqual(a[0][4:7],raw[:3])
        for args in ((raw,4,1),(raw,True,3),(b'',0,1)):
            with self.assertRaises(ValueError):transparent_edge_padding(*args)
        with self.assertRaises(ValueError):transparent_edge_padding(bytes(4),1,1)
        with self.assertRaises(ValueError):transparent_edge_padding(raw,3,1,radius=33)

    def test_full_lens_contour_keeps_highlights_without_glowing_red_body(self):
        # Old red predicate misses a white lens highlight; unrelated red is outside.
        raw=bytes((10,20,200,255,220,220,230,255,10,20,200,255))
        contour=[[(0,0),(2,0),(2,1),(0,1)]]
        lit,glow,coverage=lens_textures(raw,3,1,contour)
        self.assertEqual(coverage,[0,1]);self.assertNotEqual(lit[4:8],raw[4:8])
        self.assertEqual(lit[8:],raw[8:]);self.assertEqual(glow[8:],bytes(4))
        self.assertEqual(lit[3::4],raw[3::4]);self.assertEqual(raw,bytes(raw))

    def test_nonrectangular_coverage_rejects_outside_and_unbounded_work(self):
        self.assertEqual(polygon_pixels([[(0,0),(2,0),(0,2)]],2,2),{0})
        with self.assertRaises(ValueError):polygon_pixels([[(-1,0),(1,0),(0,1)]],2,2)
        with self.assertRaises(ValueError):polygon_pixels([],2,2)
        with self.assertRaises(ValueError):polygon_pixels([[(0,0),(1,0),(0,1)]],100000,100000)
        with self.assertRaisesRegex(ValueError,'work budget'):
            polygon_pixels([[ (0,0),(2048,0),(2048,2048),(0,2048)]]*5,2048,2048)
