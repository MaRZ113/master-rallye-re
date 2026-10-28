"""Source-free failure/budget and deterministic Michelin structural tests."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from master_rallye.source_adapters import michelin_research as m
from master_rallye.universal_vehicle_scene import canonical


def pdi(payload=b'private', name='unknown.bin'):
    slots = 2; start = 34; cdi = start + slots * 68
    data = bytearray(cdi + 12 + len(payload))
    data[:4] = b'PDI1'
    struct.pack_into('<6I', data, 4, slots, 1, 30, start, cdi, 12 + len(payload))
    struct.pack_into('<H', data, start, 24)
    struct.pack_into('<2I', data, start + 12, 0, 12 + len(payload))
    data[start + 20:start + 20 + len(name)] = name.encode('ascii')
    data[cdi:cdi + 4] = b'CDI1'
    struct.pack_into('<IHH', data, cdi + 4, len(payload), 0, 16)
    data[cdi + 12:] = payload
    return data


def xobj():
    triangle_at = 76; vertex_at = 184; normal_at = 220; texture_at = 256
    name = b'tex.tga\0\0'
    data = bytearray(texture_at + len(name)); data[:4] = b'XOBJ'
    struct.pack_into('<12I', data, 28, 1, triangle_at, 108, 3, vertex_at, 36,
                     3, normal_at, 36, 1, texture_at, len(name))
    struct.pack_into('<3f', data, triangle_at + 4, 0, 0, 1)
    struct.pack_into('<3I', data, triangle_at + 24, 0, 1, 2)
    struct.pack_into('<3I', data, triangle_at + 36, 0, 1, 2)
    struct.pack_into('<I', data, triangle_at + 80, 1)
    struct.pack_into('<6f', data, triangle_at + 84, 0, 0, 1, 0, 0, 1)
    struct.pack_into('<9f', data, vertex_at, 0, 0, 0, 1, 0, 0, 0, 1, 0)
    struct.pack_into('<9f', data, normal_at, 0, 0, 1, 0, 0, 1, 0, 0, 1)
    data[texture_at:] = name
    return data


def tga():
    # Unknown attribute bits do not turn a BGR24 palette into alpha.
    data = bytearray(18)
    struct.pack_into('<3B2HB4H2B', data, 0, 0, 1, 1, 0, 2, 24, 0, 0, 2, 1, 8, 40)
    return data + bytes([0, 1, 2, 252, 253, 254, 0, 1])


class MichelinResearchTests(unittest.TestCase):
    def test_standard_tea_known_zero_vector_and_short_tail(self):
        # Standard TEA zero key/plaintext vector: words41EA3A0A,94BAA940.
        ciphertext = struct.pack('<2I', 0x41EA3A0A, 0x94BAA940)
        self.assertEqual(m.tea_decode(ciphertext, bytes(16)), bytes(8))
        for length in range(8):
            tail = bytes(range(length))
            self.assertEqual(m.tea_decode(ciphertext + tail, bytes(16)), bytes(8) + tail)
        with self.assertRaises(ValueError): m.tea_decode(b'', b'bad')

    def test_lzss_literal_overlapping_ring_reference(self):
        self.assertEqual(m.lzss_decode(bytes([1, 65, 0xee, 0xf2]), 6), b'AAAAAA')
        self.assertEqual(m.lzss_decode(bytes([0, 0, 0]), 3), bytes(3))

    def test_lzss_truncation_overrun_trailing_bytes_and_budget(self):
        for data, count in ((b'', 1), (b'\1', 1), (b'\0', 3), (b'\0\0', 3),
                            (b'\0\0\1', 3), (b'\1ab', 1), (b'\1a', m.MAX_DECODED + 1)):
            with self.subTest(data=data, count=count), self.assertRaises(ValueError):
                m.lzss_decode(data, count)

    def test_pdi_exact_selected_payload_proof(self):
        raw = pdi(); original = bytes(raw)
        report, files = m.inspect_archive(raw)
        self.assertEqual(files['decoded/unknown.bin'], b'private')
        self.assertEqual(report['entries'][0]['decoded_bytes'], 7)
        self.assertEqual(bytes(raw), original)

    def test_malformed_table_signature_counts_offsets_flags_sizes(self):
        for offset, value in ((4, m.MAX_MEMBERS + 1), (8, 3), (16, 0), (20, 1), (24, 1),
                              (34 + 12, 99999), (34 + 16, 99999), (170 + 4, m.MAX_DECODED + 1)):
            raw = pdi(); struct.pack_into('<I', raw, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError): m.directory(raw)
        raw = pdi(); struct.pack_into('<H', raw, 180, 1)
        with self.assertRaises(ValueError): m.directory(raw)
        with self.assertRaises(ValueError): m.directory(pdi()[:-1])
        with self.assertRaises(ValueError): m.directory(b'BAD!' + pdi()[4:])

    def test_unsafe_case_alias_and_aggregate_budget_rejected_before_decode(self):
        for name in ('../bad', 'CON', 'foo/bar', 'bad:stream'):
            with self.subTest(name=name), self.assertRaises(ValueError): m.directory(pdi(name=name))
        raw = pdi()
        with patch.object(m, 'MAX_DECODED', 6), self.assertRaises(ValueError): m.directory(raw)

    def test_decode_size_mismatch_unknown_encoding_and_bad_span(self):
        raw = pdi(); row = m.directory(raw)['entries'][0]
        for changes in ({'decoded_bytes': 6}, {'flags': 2}, {'encoded_span': [100000, 1]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                m.decode_member(raw, {**row, **changes})

    def test_xobj_preserves_indices_uv_normals_unknowns_and_winding(self):
        raw = xobj(); original = bytes(raw); scene = m.xobj_structure(raw)
        self.assertEqual(scene['triangles'][0]['vertex_indices'], [0, 1, 2])
        self.assertEqual(scene['triangles'][0]['uv'], [[0, 0], [1, 0], [0, 1]])
        self.assertEqual(scene['cross_dot_face_normal_signs'], {'positive': 1})
        self.assertTrue(scene['unknown_semantics'])
        self.assertEqual(canonical(scene), canonical(m.xobj_structure(raw)))
        self.assertEqual(bytes(raw), original)

    def test_xobj_invalid_indices_uv_nan_texture_stride_and_budget(self):
        mutations = ((76 + 24, '<I', 3), (76 + 36, '<I', 3), (76 + 80, '<I', 2),
                     (76 + 84, '<f', float('nan')), (28, '<I', m.MAX_GEOMETRY + 1),
                     (36, '<I', 107), (44, '<I', 183))
        for offset, fmt, value in mutations:
            raw = xobj(); struct.pack_into(fmt, raw, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError): m.xobj_structure(raw)
        with self.assertRaises(ValueError): m.xobj_structure(xobj()[:-1])

    def test_indexed_texture_preserves_palette_channels_and_unknown_attributes(self):
        raw = tga(); info = m.indexed_tga(raw)
        self.assertEqual(info['palette_bits'], 24)
        self.assertEqual(info['declared_attribute_bits'], 8)
        self.assertIn('UNRESOLVED', info['alpha_status'])
        self.assertEqual(info['pixels_sha256'], m.sha(b'\0\1'))
        self.assertEqual(info['palette_sha256'], m.sha(bytes([0, 1, 2, 252, 253, 254])))

    def test_texture_malformed_palette_dimensions_truncation_and_trailer(self):
        for offset, fmt, value in ((7, '<B', 32), (12, '<H', 4097), (16, '<B', 24), (5, '<H', 0)):
            raw = tga(); struct.pack_into(fmt, raw, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError): m.indexed_tga(raw)
        raw = tga(); raw[-1] = 2
        with self.assertRaises(ValueError): m.indexed_tga(raw)
        with self.assertRaises(ValueError): m.indexed_tga(tga()[:-1])
        with self.assertRaises(ValueError): m.indexed_tga(tga() + b'extra')

    def test_safe_output_freshness_source_immutability_and_determinism(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); root = base / 'source'; objects = root / 'Data' / 'Objects'
            objects.mkdir(parents=True); source = objects / 'Car25A.PDO'; source.write_bytes(pdi())
            before = source.stat(); original = source.read_bytes()
            for destination in (root / 'out', base):
                with self.assertRaises(ValueError): m.run(root, destination, targets=('Car25A.PDO',))
            first = m.run(root, base / 'one', targets=('Car25A.PDO',))
            second = m.run(root, base / 'two', targets=('Car25A.PDO',))
            self.assertEqual(first['manifest_sha256'], second['manifest_sha256'])
            self.assertEqual((base / 'one/report.json').read_bytes(), (base / 'two/report.json').read_bytes())
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(source.stat().st_mtime_ns, before.st_mtime_ns)
            with self.assertRaises(ValueError): m.run(root, base / 'one', targets=('Car25A.PDO',))
            with self.assertRaises(ValueError): m.run(root, base / 'bad', targets=('../Car25A.PDO',))
            with patch.object(m, 'MAX_DECODED', 10), self.assertRaises(ValueError):
                m.run(root, base / 'budget', targets=('Car25A.PDO',))
            self.assertFalse((base / 'budget').exists())


if __name__ == '__main__':
    unittest.main()
