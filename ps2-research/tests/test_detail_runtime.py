"""Recovered GRASS1 contracts; synthetic fixtures are never runtime evidence."""
import hashlib
import math
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import detail_runtime as d
import tngtool as t


def fixture(names=None):
    names = names or ['$surfacetype(harddirt) $detail(grass)', '$surfacetype(harddirt) $detail(none)']
    points = [(10., 2., 20.), (10., 2., 25.), (15., 2., 20.)]
    b = bytearray(struct.pack('<3I4fI', 0xd00d, 2, 0x539, 0, 0, 0, 100, 3))
    for p in points:
        b.extend(struct.pack('<4fI4f4f', 0, 1, 0, 0, 0x80808080, 0, 0, 0, 0, *p, 1))
    b.extend(b'OPAQUE_VISUAL_TREE')
    proxy = len(b)
    b.extend(struct.pack('<5I9f', 103, 2, 2, 1, 1, 32, 0, 0, 0, 0, 0, 64, 10, 64))
    b.extend(struct.pack('<3I', 2, 0, 0x00010001))
    b.extend(struct.pack('<I', 2))
    for name in names:
        text = name.encode('ascii')
        b.extend(struct.pack('<IH', len(text), len(text)))
        b.extend(text)
    b.extend(struct.pack('<I6I', 2, 0, 1, 2, 0, 1, 2))
    b.extend(struct.pack('<I', 104))
    return bytes(b), proxy


class DirectiveTests(unittest.TestCase):
    def test_pool_order_is_not_string_order(self):
        self.assertEqual(d.directive_contract('$detail(grass)')['point_pool_index'], 1)
        self.assertEqual(d.directive_contract('$detail(shrubs)')['point_pool_index'], 0)

    def test_none_stones_and_singular_are_excluded_differently(self):
        for token, category in [('none', 'none'), ('stones', 'stones'), ('shrub', 'unrecognized')]:
            result = d.directive_contract('$detail('+token+')')
            self.assertEqual(result['detail_category'], category)
            self.assertEqual(result['point_pool_index'], -1)
            self.assertFalse(result['default_applied'])

    def test_first_token_case_sensitive_search_then_interner_fold(self):
        self.assertEqual(d.directive_contract('$detail(GRASS) $detail(none)')['detail_category'], 'grass')
        self.assertEqual(d.directive_contract('$DETAIL(grass)')['detail_category'], 'none')
        self.assertEqual(d.directive_contract('$detail(shrub) $detail(shrubs)')['detail_category'], 'unrecognized')
        self.assertEqual(d.directive_contract('$detailExtra(grass)')['detail_category'], 'unrecognized')

    def test_missing_or_unclosed_defaults_and_grass_off_is_not_override(self):
        for text in ['', '$detail(', '$surfacetype(grass)']:
            self.assertTrue(d.directive_contract(text)['default_applied'])
        result = d.directive_contract('$detail(grass) $grass(off)')
        self.assertEqual(result['detail_category'], 'grass')
        self.assertTrue(result['grass_off_present'])


class SpatialTests(unittest.TestCase):
    def test_positive_and_negative_share_actual_source_geometry(self):
        data, offset = fixture()
        model = d.decode_landscape(data)
        self.assertEqual(model.proxy_offset, offset)
        self.assertEqual(model.bindings, {0: 0, 1: 1})
        self.assertEqual(model.surface(0), model.surface(1))
        report = d.metadata_report(model, 'SYNTHETIC', 'SYNTHETIC')
        self.assertEqual([m['slope_passing_triangles_float32'] for m in report['materials']], [1, 1])
        self.assertEqual([m['eligible_triangles_float32'] for m in report['materials']], [1, 0])

    def test_spatial_order_and_triangle_deduplication(self):
        model = d.decode_landscape(fixture()[0])
        self.assertEqual(d.spatial_query(model, 10, 20, 30), [(0, 0), (1, 1)])
        # Original query clamps to an edge cell; it does not reject outside-grid centers.
        self.assertEqual(d.spatial_query(model, -1000, -1000, 30), [(0, 0), (1, 1)])

    def test_malformed_bounds_and_identity_fail_closed(self):
        original, proxy = fixture()
        for offset, value in [(0, 0), (4, 3), (28, 0xffffffff), (proxy+4, 99), (proxy+12, 0), (proxy+60, 0xffff)]:
            data = bytearray(original)
            struct.pack_into('<I', data, offset, value)
            with self.subTest(offset=offset), self.assertRaises(t.FormatError):
                d.decode_landscape(data)
        with self.assertRaises(t.FormatError):
            d.decode_landscape(original[:proxy+30])

    def test_serialized_material_lengths_must_agree(self):
        data, _ = fixture()
        data = bytearray(data)
        offset = data.index(b'$surfacetype')
        struct.pack_into('<H', data, offset-2, 1)
        with self.assertRaises(t.FormatError):
            d.decode_landscape(data)

    def test_spatial_material_need_not_have_surface_type(self):
        model = d.decode_landscape(fixture(['$detail(grass)', '$detail(none)'])[0])
        self.assertEqual(model.bindings, {0: 0, 1: 1})
        self.assertEqual(d.directive_contract(model.materials[1])['detail_category'], 'none')


class NumericalTests(unittest.TestCase):
    def test_original_inline_floor_signed_and_boundary_inputs(self):
        for value in [0, -0., .5, -.75, 1, -1, 1.9999, -1.9999, 4000.125, -4000.125, 2**-40]:
            self.assertEqual(d.ee_floor(value), math.floor(d.f32(value)))
        # Original 356c40/356c70 use only the explicit 23 mantissa bits;
        # 356c84 cancels the sign correction when those bits are zero.
        for value in [-.5, -.25, -2**-40]:
            self.assertEqual(d.ee_floor(value), 0)
        for value in [math.inf, math.nan, 2**31]:
            with self.assertRaises(t.FormatError): d.ee_floor(value)

    def test_winding_slope_and_degenerate_controls(self):
        up = [(10, 2, 20), (10, 2, 25), (15, 2, 20)]
        self.assertTrue(d.eligibility(up, 'grass')['eligible'])
        self.assertFalse(d.eligibility(list(reversed(up)), 'grass')['eligible'])
        steep = [(10, 2, 20), (10, 12, 25), (15, 2, 20)]
        self.assertFalse(d.eligibility(steep, 'grass')['slope_pass'])
        self.assertTrue(d.eligibility([up[0]]*3, 'grass')['degenerate'])
        self.assertFalse(d.eligibility(up, 'stones')['category_pass'])

    def test_scanline_lattice_not_barycentric_sampling(self):
        polygon = [(15., 2., 20.), (10., 2., 25.), (10., 2., 20.)]
        coefficients = d.plane_coefficients(polygon)
        self.assertEqual(coefficients, (2., 0., 0.))
        points = d.scan_polygon(polygon, coefficients, 'grass', [(0., 0., 0.)]*1024)
        self.assertEqual(len(points), 9)  # Three half-open rows with 4 + 3 + 2 points.
        self.assertLess(points[0]['position'][0], 10.)
        self.assertLess(points[0]['position'][2], 20.)
        self.assertEqual(points[0]['position'][1], d.add(2., d.LIFT['grass']))
        self.assertEqual(d.scan_polygon(polygon, coefficients, 'none', [(0., 0., 0.)]*1024), [])
        with self.assertRaises(t.FormatError):
            d.scan_polygon(polygon, coefficients, 'grass', [(0., 0., 0.)]*1024, limit=1)

    def test_height_plane_against_independent_affine_surface(self):
        vertices = [(10., 4., 20.), (10., 5., 25.), (15., 4.5, 20.)]
        c, x, z = d.plane_coefficients(vertices)
        for vx, vy, vz in vertices:
            self.assertAlmostEqual(c+x*vx+z*vz, vy, places=5)
        with self.assertRaises(t.FormatError):
            d.plane_coefficients([(0, 0, 0), (1, 0, 0), (0, 0, 1)])

    def test_fixed_seed_jitter_and_unit_ball_invariant(self):
        table, provenance = d.jitter_table()
        again, repeated = d.jitter_table()
        self.assertEqual(table, again)
        self.assertEqual(provenance, repeated)
        self.assertEqual(provenance['seed'], 0x30ff)
        self.assertTrue(all(sum(x*x for x in v) <= 1.000001 for v in table))
        changed, _ = d.jitter_table(1)
        self.assertNotEqual(table, changed)

    def test_input_record_alpha_cull_and_resource_mapping(self):
        record = d.primitive_record((1, 2, 3), 'grass', (1, 3), 64, 1)
        self.assertEqual(record['rgba_float'], [128., 128., 128., 128.])
        self.assertEqual(record['record_bytes'], 64)
        self.assertEqual(record['size_xy'], [d.mul(d.LIFT['grass'], 3)]*2)
        self.assertTrue(record['resource'].endswith('GRASS1.GXI'))
        self.assertTrue(d.primitive_record((1, 2, 3), 'shrubs', (1, 3), 64, 1)['resource'].endswith('BUSH1.GXI'))
        self.assertIsNone(d.primitive_record((100, 0, 0), 'grass', (0, 0), 64, 1))
        self.assertIsNone(d.primitive_record((1, 2, 3), 'stones', (1, 3), 64, 1))
        for scale, factor in [(0, 1), (64, math.nan), (-1, 1)]:
            with self.assertRaises(t.FormatError):
                d.primitive_record((1, 2, 3), 'grass', (1, 3), scale, factor)


class OptionalCanonicalTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MASTER_RALLYE_PS2_INPUT'), 'Canonical proprietary corpus not configured')
    def test_canonical_elf_instruction_anchors(self):
        elf = (Path(os.environ['MASTER_RALLYE_PS2_INPUT'])/'SLES_509.06').read_bytes()
        self.assertEqual(hashlib.sha256(elf).hexdigest(),
                         'b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2')
        # Original bytes, independent of Ghidra's temporary analysis surrogates.
        for address, word in {0x356c40: 0x00a82824, 0x356c70: 0x00052a00,
                              0x356c84: 0x00691823, 0x3b78cc: 0x240430ff,
                              0x3f9714: 0x00641818, 0x3f9718: 0x24633039,
                              0x341204: 0x24190047, 0x341280: 0xfc590028,
                              0x4443e8: 0x800c06bc, 0x444744: 0x01804a5f,
                              0x444760: 0x2400003f, 0x444050: 0x800046fc}.items():
            self.assertEqual(struct.unpack_from('<I', elf, address-0xff000)[0], word)
        self.assertEqual(struct.unpack_from('<I', elf, 0x4850c0+11*4-0xff000)[0], 0x312dc8)
        # Independent VIF stream addressing: fifth MPG uploads pc400..4c8.
        self.assertEqual(struct.unpack_from('<I', elf, 0x44419c-0xff000)[0], 0x4ac90400)
        self.assertEqual(struct.unpack_from('<I', elf, 0x442170-0xff000)[0], 0x60000267)


class EmbeddedSpriteTests(unittest.TestCase):
    def test_projected_two_corner_stq_and_integer_contract(self):
        # Independently specified arithmetic example; all vectors are synthetic.
        sprite = d.vu_sprite([4, 8], [128, 128, 128, 12.9], [200, 100, 600, 2], [.5, -.5, 1, 2])
        self.assertEqual(sprite['corners_xyz'], [[102., 54., 300.], [98., 46., 300.]])
        self.assertEqual(sprite['xyz_ftoi4'], [[1632, 864, 4800], [1568, 736, 4800]])
        self.assertEqual(sprite['stq'], [[0., 0., .5], [.5, .5, .5]])
        self.assertEqual(sprite['rgba_ftoi0'], [128, 128, 128, 12])
        self.assertEqual(sprite['second_xyzf2_w_mask'], 0)
        self.assertEqual(sprite['resident_microcode_provenance'], 'UNKNOWN_UPLOAD_LINK')

    def test_size_cap_and_center_clip_are_distinct(self):
        capped = d.vu_sprite([300, 160], [128]*4, [200, 100, 600, 2], [0, 0, 1, 2])
        self.assertEqual(capped['half_size_xy'], [56., 56.])
        self.assertEqual(capped['corners_xyz'][0][0]-capped['corners_xyz'][1][0], 112.)
        rejected = d.vu_sprite([4, 8], [128]*4, [200, 100, 600, 2], [3, 0, 1, 2])
        self.assertEqual(rejected['second_xyzf2_w_mask'], 0xc000)
        boundary = d.vu_sprite([4, 8], [128]*4, [200, 100, 600, 2], [2.5, 0, 1, 2])
        self.assertEqual(boundary['second_xyzf2_w_mask'], 0)

    def test_unsupported_vu_inputs_remain_explicit(self):
        for projected, clip in [([0, 0, 0, 0], [0, 0, 1, 1]),
                                ([0, 0, 0, -1], [0, 0, 1, 1]),
                                ([0, 0, math.nan, 1], [0, 0, 1, 1]),
                                ([0, 0, 0, 1], [0, 0, 1, 0])]:
            with self.assertRaises(t.FormatError):
                d.vu_sprite([4, 8], [128]*4, projected, clip)

class OptionalSpatialCanonicalTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MASTER_RALLYE_PS2_INPUT'), 'Canonical proprietary corpus not configured')
    def test_original_spatial_binding_and_spelling(self):
        source = Path(os.environ['MASTER_RALLYE_PS2_INPUT'])
        self.assertEqual(t.file_hash(source/'TNG.PAK'), t.PAK_SHA)
        manifest, _ = t.load_pak(source/'TNG.PAK')
        for course, count, digest in [
            ('FRANCE1', 23064, 'd0b9845218ddd1ff4f12b3b16e77eff43aa182ac73992b5cbea8d81be04f935d'),
            ('TURKEY_S1', 18768, 'e431d2c3e64cf9e803013b4faf1f116bd2bce9e4d9a55140b74c42f2b8ca2198')]:
            logical = '\\TNG\\DATAPSM\\COURSE\\'+course+'\\'+course+'.PSM'
            entry = next(r for r in manifest['entries'] if r['path'].upper() == logical)
            payload, _ = t.read_payload(entry, source/'TNG.000')
            self.assertEqual(hashlib.sha256(payload).hexdigest(), digest)
            model = d.decode_landscape(payload)
            self.assertEqual(len(model.bindings), count)
            if course == 'TURKEY_S1':
                singular = [i for i,s in enumerate(model.materials) if '$detail(shrub)' in s]
                self.assertEqual(singular, [11])
                self.assertGreater(sum(v == 11 for v in model.bindings.values()), 0)


if __name__ == '__main__': unittest.main()
