"""Metadata-only malformed-input/qualification checks; no original game fixtures."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('priority_probe', Path(__file__).resolve().parents[2] / 'tools/source_garage_priority_probe.py')
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def pdi(names=('test.bin',), directory=34):
    slots = len(names) + 1; cdi = directory + slots * 68
    data = bytearray(cdi + len(names) * 16)
    data[:4] = b'PDI1'
    struct.pack_into('<6I', data, 4, slots, len(names), 30, directory, cdi, len(names) * 16)
    data[cdi:cdi + 4] = b'CDI1'
    for index, name in enumerate(names):
        at = directory + index * 68
        struct.pack_into('<H', data, at, 25)
        struct.pack_into('<II', data, at + 12, index * 16, 16)
        data[at + 20:at + 20 + len(name)] = name.encode('ascii')
        struct.pack_into('<IHH', data, cdi + index * 16 + 4, 4, 0, 17)
    return data


def pssg(duplicates=False):
    def number(value): return struct.pack('>I', value)
    def text(value): return number(len(value)) + value
    dictionary = number(1) + text(b'SYNTHETIC') + number(2)
    dictionary += number(1) + text(b'width') + number(1 if duplicates else 2) + text(b'height')
    data = b'PSSG' + number(len(dictionary) + 8) + number(2) + number(1) + dictionary
    return bytearray(data)


class PriorityProbeTests(unittest.TestCase):
    def test_pdi_variable_directory_offset_and_wrapper_are_bounded_without_decode(self):
        for offset in (34, 50, 162):
            result = probe.pdi_directory(pdi(directory=offset))
            self.assertEqual(result['directory_offset'], offset)
            entry = result['entries'][0]
            self.assertIn('UNSUPPORTED', entry['payload_status'])
            self.assertEqual(entry['encoded_payload_span'][1], 4)

    def test_pdi_rejects_offsets_count_truncation_and_bad_magic(self):
        for field, value in ((4, 200001), (8, 4), (16, 0), (20, 0), (24, 0)):
            data = pdi(); struct.pack_into('<I', data, field, value)
            with self.assertRaises(ValueError): probe.pdi_directory(data)
        with self.assertRaises(ValueError): probe.pdi_directory(pdi()[:-1])
        with self.assertRaises(ValueError): probe.pdi_directory(b'PDI1')

    def test_pdi_rejects_unsafe_name_overlapping_spans_and_unsupported_flags(self):
        with self.assertRaises(ValueError): probe.pdi_directory(pdi(('../bad',)))
        data = pdi(('one', 'two'))
        struct.pack_into('<I', data, 34 + 68 + 12, 0)
        with self.assertRaisesRegex(ValueError, 'overlapping'): probe.pdi_directory(data)
        data = pdi(); cdi = struct.unpack_from('<I', data, 20)[0]
        struct.pack_into('<H', data, cdi + 10, 7)
        with self.assertRaises(ValueError): probe.pdi_directory(data)

    def test_pdi_rejects_declared_decompression_budget_before_any_decode(self):
        data = pdi(); cdi = struct.unpack_from('<I', data, 20)[0]
        struct.pack_into('<I', data, cdi + 4, probe.MAX_FILE + 1)
        with self.assertRaises(ValueError): probe.pdi_directory(data)

    def test_pssg_preserves_duplicate_ids_as_warning_instead_of_overwriting(self):
        ordinary = probe.pssg_dictionary(pssg())
        duplicate = probe.pssg_dictionary(pssg(True))
        self.assertEqual(ordinary['status'], 'PASS')
        self.assertEqual(duplicate['status'], 'WARN')
        self.assertEqual([a['name'] for a in duplicate['nodes'][0]['attributes']], ['width', 'height'])
        self.assertEqual(duplicate['mesh_status'], 'NOT TESTED')

    def test_pssg_rejects_byte_order_size_string_and_count_abuse(self):
        for offset, value in ((4, 0), (8, 32769), (12, 4097), (20, 257)):
            data = pssg(); struct.pack_into('>I', data, offset, value)
            with self.assertRaises(ValueError): probe.pssg_dictionary(data)
        with self.assertRaises(ValueError): probe.pssg_dictionary(pssg()[:-1])

    def test_literal_markers_do_not_promote_vehicle_or_mesh_identity(self):
        result = probe.opaque_markers(b'x' * 8 + b'RallyCar 1.00\0ArchList')
        self.assertEqual(result['markers']['RallyCar 1.00'], [8])
        self.assertEqual(result['mesh_status'], 'UNSUPPORTED')
        self.assertIn('no V60/V20', result['identity'])

    def test_missing_inputs_stay_missing_and_probe_does_not_write_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'original'; source.write_bytes(b'original')
            before = source.stat()
            report = probe.run(root)
            self.assertTrue(all(row.get('status') == 'MISSING INPUT' for row in report['files'].values()))
            self.assertEqual(source.read_bytes(), b'original')
            self.assertEqual(source.stat().st_mtime_ns, before.st_mtime_ns)

    def test_output_inside_source_and_source_read_budget_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source'; source.write_bytes(b'12345')
            with self.assertRaises(ValueError): probe.validate_output(root, root / 'report.json')
            with self.assertRaises(ValueError): probe.read_source(source, 4)
            self.assertEqual(probe.read_source(source, 5), b'12345')
            sources = root / 'sources'; sources.mkdir()
            with self.assertRaises(ValueError): probe.validate_output(sources, root)
            existing = root / 'existing.json'; existing.write_text('{}')
            with self.assertRaises(ValueError): probe.validate_output(sources, existing)
            link = root / 'link'
            try: link.symlink_to(root / 'elsewhere', target_is_directory=True)
            except OSError: return
            # A dangling output link must also fail; resolve() must not hide it.
            with self.assertRaises(ValueError): probe.validate_output(sources, link / 'report.json')

    def test_catalog_unqualified_size_and_duplicate_ids_reject(self):
        with self.assertRaises(ValueError): probe.car_catalog(b'not a catalog')
        data = bytearray(24 * 1608)
        for index in range(24):
            struct.pack_into('<I', data, index * 1608 + 28, index + 1)
            data[index * 1608 + 32:index * 1608 + 36] = b'Test'
        self.assertEqual(len(probe.car_catalog(data)['records']), 24)
        struct.pack_into('<I', data, 1608 + 28, 1)
        with self.assertRaises(ValueError): probe.car_catalog(data)


if __name__ == '__main__':
    unittest.main()
