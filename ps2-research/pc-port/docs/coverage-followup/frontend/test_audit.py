"""Corpus-independent metadata and fail-closed format tests.

Synthetic decoder tests reuse the included PS2 readers. Metadata checks need
only the committed JSON; the external SDK is required for corpus regeneration.
"""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE = Path(__file__).parent


class FrontendMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((HERE / 'source-evidence.json').read_text(encoding='utf8'))

    def test_inventory_unique_and_hashed(self):
        rows = self.report['inventory']
        self.assertEqual(len(rows), 29)
        self.assertEqual(len({row['resource'] for row in rows}), 29)
        self.assertTrue(all(len(row['sha256']) == 64 for row in rows))
        self.assertEqual(len(self.report['pc_complete_sources']), 26)

    def test_unknown_terminal_is_not_geometry(self):
        blocked = [row for row in self.report['inventory'] if row['decoder'] == 'UNSUPPORTED_FAIL_CLOSED']
        self.assertEqual(len(blocked), 25)
        for row in blocked:
            self.assertNotIn('source_triangles', row)
            self.assertEqual(row['terminal_bytes_hex'], '66000000cdcccc3ecdcc4c3effffffff')

    def test_wooldand_menu_source_is_distinct(self):
        case = next(c for c in self.report['cases'] if c['ps2_family'] == 'WOOLDAND')
        self.assertEqual(case['pc_family'], 'Forester')
        menu = next(c for c in case['comparisons'] if c['pc_model'] == 'complete')
        self.assertEqual(menu['pc_triangles'], 2271)
        self.assertEqual(menu['ps2_complete_matching_pc_faces'], 978)
        self.assertEqual(menu['ps2_car_matching_pc_faces'], 0)
        self.assertEqual(self.report['runtime_validation'], 'NOT_PERFORMED')

    def test_tata_terminal_blocker_preserved(self):
        case = next(c for c in self.report['cases'] if c['ps2_family'] == 'TATA')
        menu = next(c for c in case['comparisons'] if c['pc_model'] == 'complete')
        self.assertIsNone(menu['ps2_complete_matching_pc_faces'])
        self.assertEqual(menu['pc_triangles'], 2470)


class SyntheticFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('frontend_audit', HERE / 'audit.py')
        cls.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.audit)

    def source(self, terminal, trailer=b''):
        header = struct.pack('<8I', 0xd00d, 2, 0x539, 0, 0, 0, 0, 1)
        return header + bytes(52) + struct.pack('<3I', 1, 0, terminal) + trailer

    def test_known_sentinel_exact_eof_only(self):
        scene = self.audit.decode_menu(self.source(0xffffffff))
        self.assertEqual(scene.end, 92)
        with self.assertRaises(self.audit.existing.t.FormatError):
            self.audit.decode_menu(self.source(0xffffffff, b'unknown'))

    def test_new_menu_terminal_is_rejected(self):
        with self.assertRaises(self.audit.existing.t.FormatError):
            self.audit.decode_menu(self.source(102, struct.pack('<2fI', .4, .2, 0xffffffff)))

    def test_ambiguous_resource_fails_closed(self):
        entries = [{'path': '\\TNG\\A.PSM'}, {'path': '\\TNG\\A.PSM'}]
        with self.assertRaises(ValueError):
            self.audit.unique_resource(entries, '\\TNG\\A.PSM')


if __name__ == '__main__':
    unittest.main()
