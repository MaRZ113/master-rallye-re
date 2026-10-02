from __future__ import annotations

import sys
import unittest
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "tools" / "scanner"
if str(SCANNER) not in sys.path:
    sys.path.insert(0, str(SCANNER))

from r_dev1_1_pe_ui_resources import parse_dialog_template


def make_standard_dialog(control_id: int) -> bytes:
    header = struct.pack("<IIHhhhh", 0, 0, 1, 0, 0, 20, 10)
    empty_fields = struct.pack("<HHH", 0, 0, 0)
    control = struct.pack("<IIhhhhH", 0, 0, 0, 0, 10, 10, control_id)
    return header + empty_fields + control + struct.pack("<HHH", 0, 0, 0)


def make_extended_dialog(control_id: int) -> bytes:
    header = struct.pack("<HHIIIHhhhh", 1, 0xFFFF, 0, 0, 0, 1, 0, 0, 20, 10)
    empty_fields = struct.pack("<HHH", 0, 0, 0)
    control = struct.pack("<IIIhhhhI", 0, 0, 0, 0, 0, 10, 10, control_id)
    return header + empty_fields + control + struct.pack("<HHH", 0, 0, 0)


class DialogResourceParserTests(unittest.TestCase):
    def test_reads_standard_dialog_control_id(self):
        self.assertEqual(parse_dialog_template(make_standard_dialog(0x30)), [0x30])

    def test_reads_extended_dialog_control_id(self):
        self.assertEqual(parse_dialog_template(make_extended_dialog(0x58)), [0x58])

    def test_rejects_truncated_template(self):
        with self.assertRaises(ValueError):
            parse_dialog_template(b"\x00\x00")


if __name__ == "__main__":
    unittest.main()
