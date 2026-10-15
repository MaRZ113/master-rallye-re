import json
from pathlib import Path
import struct
import unittest
import convert_complete as c


class ConversionTests(unittest.TestCase):
    def test_vertex_exact_attributes(self):
        raw = bytearray(52)
        struct.pack_into('<3f', raw, 0, .25, .5, .75)
        struct.pack_into('<I', raw, 16, 0x12345678)
        struct.pack_into('<2f', raw, 20, .125, .875)
        struct.pack_into('<3f', raw, 36, 1, 2, 3)
        values = c.VERTEX.unpack(c.vertex(raw, 0))
        self.assertEqual(values, (1, 2, 3, .25, .5, .75, 0x78123456, .125, .875))

    def test_adc_keeps_source_triples_not_guessed_parity(self):
        raw = bytearray(52 * 5)
        for i, xyz in enumerate(((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (2, 0, 0))):
            struct.pack_into('<3f', raw, i * 52 + 36, *xyz)
        struct.pack_into('<I', raw, 3 * 52 + 12, 1)
        ids, diagnostics = c.indices_for_mesh(raw, {'strips': [{'start': 0, 'count': 5, 'flag': True}]})
        self.assertEqual(ids, [0, 1, 2, 2, 3, 4])
        self.assertEqual(diagnostics['adc_suppressed'], 1)

    def test_gxi_channel_order_preserves_zero_alpha(self):
        info, pixels = c.texture(struct.pack('<IHH', 0x13039, 1, 1) + bytes((1, 2, 3, 0)))
        self.assertEqual(pixels, bytes((3, 2, 1, 0)))
        self.assertEqual(info['alpha_max'], 0)

    def test_malformed_gxi_fails_closed(self):
        with self.assertRaises(Exception):
            c.texture(struct.pack('<IHH', 0x13039, 2, 2) + b'abcd')

    def test_source_artifact_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'source artifact drift'):
            c.convert(b'PS2VEH01' + bytes(80))

    def test_original_default_material_branches(self):
        report = json.loads((Path(__file__).parent / 'default-material-evidence.json').read_text())
        words = {row['va']: row['original_word'] for row in report['instructions']}
        self.assertEqual(words['0x3916dc'], '0xac400028')
        self.assertEqual(words['0x39177c'], '0x1060005f')
        self.assertEqual(words['0x391b68'], '0x1840001a')
        self.assertEqual(report['root17_static_mode'], 0)
        self.assertEqual(report['default_texture_original_pixels'], 'CANONICAL_DEFAULT_GXI_8x8_RGBA_0_0_0_255')

    def test_source_metadata_contract(self):
        report = json.loads((Path(__file__).parent / 'conversion-evidence.json').read_text())
        self.assertEqual((report['vertices'], report['faces'], report['meshes'], report['textures']), (6606, 4636, 24, 28))
        self.assertEqual(report['unknown_materials'], [])
        self.assertFalse(report['transforms_applied'])
        wheels = report['meshes_detail'][19:23]
        self.assertEqual([m['faces'] for m in wheels], [m['index_count'] // 3 for m in wheels])
        self.assertEqual([m['contract']['rubber_substring_preserved'] for m in wheels], [True, True, False, True])

    def test_resolved_default_asset_if_original_available(self):
        path = c.PORT / '.assets/vehicles/XTRAIL-COMPLETE.ps2vehicle'
        default = c.PORT / '.assets/vehicles/XTRAIL-default.gxi'
        if not path.exists() or not default.exists():
            self.skipTest('Original private sources unavailable')
        binary, report = c.convert(path.read_bytes(), default.read_bytes())
        self.assertEqual(c.sha(binary), 'ba1cee9a21c2a2ae2935158136ae80b587eca7dc9a6701afc573e069818d772b')
        self.assertEqual(c.HEADER.unpack_from(binary)[6], 28)
        self.assertEqual(report['meshes_detail'][17]['contract']['mode'], 0)
        self.assertEqual(report['meshes_detail'][17]['contract']['effective_secondary'], None)
        self.assertEqual(report['textures_detail'][-1]['average_rgba'], [0.0, 0.0, 0.0, 255.0])

    def test_private_determinism_if_original_available(self):
        path = c.PORT / '.assets/vehicles/XTRAIL-COMPLETE.ps2vehicle'
        if not path.exists():
            self.skipTest('Original private source unavailable')
        a, ra = c.convert(path.read_bytes())
        b, rb = c.convert(path.read_bytes())
        self.assertEqual(a, b)
        self.assertEqual(ra, rb)
        self.assertEqual(c.HEADER.unpack_from(a)[0], c.MAGIC)
        self.assertEqual(c.sha(a), '641406d6ff45e028bb26d38bf69ea53dd48afd3d0fe420284e8055ca5f5809cc')


if __name__ == '__main__':
    unittest.main()
