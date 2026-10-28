"""SBF/SBZ1 malformed-input tests use fabricated metadata and a one-pixel DDS."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

SPEC = importlib.util.spec_from_file_location('revo_probe', Path(__file__).resolve().parents[2] / 'tools/source_garage_revo_probe.py')
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def dds():
    data = bytearray(132)
    data[:4] = b'DDS '
    struct.pack_into('<7I', data, 4, 124, 0x100f, 1, 1, 4, 0, 1)
    struct.pack_into('<8I', data, 76, 32, 0x41, 0, 32, 0xff0000, 0xff00, 0xff, 0xff000000)
    struct.pack_into('<I', data, 108, 0x1000)
    data[128:] = bytes((0, 0, 255, 255))
    return bytes(data)


def archive(kinds=(1, 4)):
    payloads = [bytes(32) + b'UNDECODED' if kind != 4 else bytes(68) + dds() for kind in kinds]
    result = bytearray(24 + len(kinds) * 8)
    struct.pack_into('<I', result, 0, 4)
    struct.pack_into('<I', result, 20, len(kinds))
    for index, (kind, payload) in enumerate(zip(kinds, payloads)):
        struct.pack_into('<II', result, 24 + index * 8, 0x100 + index, len(result))
        member = bytearray(payload)
        struct.pack_into('<I', member, 0, kind)
        result.extend(member)
    return result


def wrapped(data):
    return b'SBZ1' + struct.pack('<I', len(data)) + zlib.compress(data)


class RevoProbeTests(unittest.TestCase):
    def test_realistic_archive_shape_preserves_offsets_hashes_and_scope(self):
        data = archive()
        result, textures = probe.inspect(data)
        self.assertEqual(result['L0'], 'PASS')
        self.assertEqual(result['L1'], 'NOT TESTED')
        self.assertEqual(result['type_counts'], {'1': 1, '4': 1})
        self.assertEqual(len(textures), 1)
        self.assertEqual(result['members'][1]['dds']['sha256'], probe.digest(dds()))
        self.assertEqual(result['members'][0]['offset'], 40)
        self.assertEqual(result['members'][1]['payload_offset'], result['members'][1]['offset'] + 68)

    def test_bounded_zlib_and_uncompressed_produce_same_expanded_hash(self):
        data = archive()
        direct, _ = probe.inspect(data)
        compressed, _ = probe.inspect(wrapped(data))
        self.assertEqual(direct['expanded_sha256'], compressed['expanded_sha256'])
        self.assertNotEqual(direct['stored_sha256'], compressed['stored_sha256'])

    def test_unsorted_directory_preserves_original_index_and_key(self):
        data = archive()
        first, second = bytes(data[24:32]), bytes(data[32:40])
        data[24:32], data[32:40] = second, first
        result, _ = probe.inspect(data)
        self.assertEqual([member['directory_index'] for member in result['members']], [1, 0])
        self.assertEqual(result['members'][0]['directory_key_hex'], '00000100')

    def test_unknown_member_is_visible_warning_not_fabricated_mesh(self):
        result, textures = probe.inspect(archive((7,)))
        self.assertEqual(result['L0'], 'WARN')
        self.assertEqual(result['members'][0]['meaning'], 'unknown member semantics retained')
        self.assertEqual(textures, [])

    def test_reject_magic_reserved_header_and_truncation(self):
        for data in (b'', b'SBZ1', b'OTHER', archive()[:27]):
            with self.assertRaises(probe.ProbeError): probe.inspect(data)
        data = archive(); data[4] = 1
        with self.assertRaises(probe.ProbeError): probe.inspect(data)

    def test_reject_directory_count_budget_and_missing_table(self):
        for count in (0, probe.MAX_ENTRIES + 1, 900):
            data = archive(); struct.pack_into('<I', data, 20, count)
            with self.assertRaises(probe.ProbeError): probe.inspect(data)

    def test_reject_offset_into_table_beyond_end_and_duplicate(self):
        for offset in (24, 0xffffffff, 40):
            data = archive(); struct.pack_into('<I', data, 36, offset)
            with self.assertRaises(probe.ProbeError): probe.inspect(data)

    def test_reject_overlapping_headers_and_short_texture_header(self):
        data = archive(); struct.pack_into('<I', data, 36, 41)
        with self.assertRaisesRegex(probe.ProbeError, 'overlaps'): probe.inspect(data)
        data = archive((4,))[:70]
        with self.assertRaises(probe.ProbeError): probe.inspect(data)

    def test_reject_advertised_expansion_budget_without_decode(self):
        for size in (0, probe.MAX_EXPANDED + 1):
            with self.assertRaises(probe.ProbeError): probe.expand(b'SBZ1' + struct.pack('<I', size))

    def test_reject_expansion_bomb_underdeclared_and_overdeclared(self):
        data = archive()
        for size in (24, len(data) + 1):
            encoded = b'SBZ1' + struct.pack('<I', size) + zlib.compress(data)
            with self.assertRaises(probe.ProbeError): probe.expand(encoded)

    def test_reject_truncated_corrupt_and_trailing_zlib(self):
        data = wrapped(archive())
        for encoded in (data[:-1], data + b'trailing', data[:8] + b'not-zlib'):
            with self.assertRaises(probe.ProbeError): probe.expand(encoded)

    def test_reject_texture_dimensions_and_header_abuse(self):
        for offset, value in ((4, 0), (76, 0), (12, 0), (16, probe.MAX_DIMENSION + 1), (28, 33)):
            data = bytearray(dds()); struct.pack_into('<I', data, offset, value)
            with self.assertRaises(probe.ProbeError): probe.dds_metadata(data)

    def test_read_only_source_probe_rejects_oversized_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.sbf'; path.write_bytes(archive())
            before = path.read_bytes()
            self.assertEqual(probe.read_source(path), before)
            with patch.object(probe, 'MAX_STORED', 8):
                with self.assertRaises(probe.ProbeError): probe.read_source(path)
            self.assertEqual(path.read_bytes(), before)

    def test_output_inside_source_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source.sbf'; source.write_bytes(archive())
            out = root / 'forbidden'
            config = root / 'config.json'
            config.write_text(json.dumps({'schema': 'source-garage-roots/1', 'base': str(root),
                                          'games': [{'id': 'source', 'path': '.'}]}))
            argv = ['probe', '--config', str(config), '--source-root', str(root), '--input', str(source), '--output', str(out)]
            with patch('sys.argv', argv), patch('builtins.print'):
                self.assertEqual(probe.main(), 2)
            self.assertFalse(out.exists())

    def test_other_title_and_collection_base_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp); base = parent / 'sources'; outside = parent / 'external-title'
            config = parent / 'config.json'
            config.write_text(json.dumps({'schema': 'source-garage-roots/1', 'base': str(base), 'games': [
                {'id': 'one', 'path': 'one'}, {'id': 'external', 'path': str(outside)}]}))
            roots, sha = probe.protected_roots(config, [])
            self.assertEqual(len(sha), 64)
            for destination in (base / 'other-title' / 'output', outside / 'output', parent):
                with self.assertRaisesRegex(probe.ProbeError, 'every configured'):
                    probe.guard_output(destination, roots)
            probe.guard_output(parent / 'research' / 'output', roots)

    def test_extra_tools_root_and_malformed_config_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp); config = parent / 'config.json'; tools = parent / 'tools'
            cfg = {'schema': 'source-garage-roots/1', 'base': str(parent / 'sources'),
                   'games': [{'id': 'one', 'path': 'one'}]}
            config.write_text(json.dumps(cfg))
            roots, _ = probe.protected_roots(config, [tools])
            with self.assertRaises(probe.ProbeError): probe.guard_output(tools / 'output', roots)
            cfg['games'].append({'id': 'one', 'path': 'two'})
            config.write_text(json.dumps(cfg))
            with self.assertRaises(probe.ProbeError): probe.protected_roots(config, [])

    def test_synthetic_dds_decode_if_pillow_available(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow not installed')
        with tempfile.TemporaryDirectory() as tmp:
            result = probe.decode_one_dds([(3, dds())], Path(tmp))
            self.assertEqual(result['status'], 'PASS')
            with Image.open(result['path']) as image:
                self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))


if __name__ == '__main__':
    unittest.main()
