import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_menu_backdrops import texture_identity, bank_references, extension_layout


class MenuBackdropTests(unittest.TestCase):
    def test_exact_content_identity(self):
        data = struct.pack('<5I', 0xFEED, 1, 0, 1, 1) + bytes([2, 3, 4, 255])
        identity = texture_identity(data)
        self.assertEqual(identity['alpha_values'], [255])
        changed = bytearray(data)
        changed[20] ^= 1
        self.assertNotEqual(identity['upload_bgra_sha256'], texture_identity(changed)['upload_bgra_sha256'])
        for bad in [data[:19], data[:-1], bytes(20), data + b'\x00']:
            with self.assertRaises(ValueError):
                texture_identity(bad)

    def test_bank_identity_only(self):
        data = struct.pack('<2I', 0xF001, 125) + b'bg_quickrace_000_000\0' * 2 + b'font_000_001\0'
        self.assertEqual(len(bank_references(data)), 2)
        with self.assertRaises(ValueError):
            bank_references(b'unknown')

    def test_layout_central_composition(self):
        for aspect in [4 / 3, 16 / 9, 16 / 10, 21 / 9]:
            result = extension_layout(aspect)
            self.assertEqual(result['central_art'], [0, 0, 640, 480])
            self.assertEqual(result['central_scale'], [1, 1])
            self.assertAlmostEqual(result['canvas'][2] - result['canvas'][0], 480 * aspect)
        self.assertFalse(extension_layout(4 / 3)['requires_extension'])
        with self.assertRaises(ValueError):
            extension_layout(99)


if __name__ == '__main__':
    unittest.main()
