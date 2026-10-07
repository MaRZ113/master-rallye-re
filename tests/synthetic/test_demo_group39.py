from __future__ import annotations

import struct
import sys
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import extract_demo_group39 as extractor


class DemoGroup39Tests(unittest.TestCase):
    def _fixture(self) -> tuple[bytes, dict]:
        data = bytearray(0x240)
        data[0x180:0x193] = b"JOSE MARIA SERCIA\0"
        struct.pack_into("<iiI", data, 0x100, 0x39, 2, 0x401080)
        pe = {
            "image_base": 0x400000,
            "sections": [{"name": ".rdata", "rva": 0x1000,
                          "raw_size": 0x140, "raw_offset": 0x100}],
        }
        return bytes(data), pe

    def test_group_rows_resolve_selector_to_string(self) -> None:
        data, pe = self._fixture()
        rows = extractor.extract_table(data, pe, raw_offset=0x100, row_count=1)
        self.assertEqual(rows[0]["selector"], 2)
        self.assertEqual(rows[0]["text"], "JOSE MARIA SERCIA")
        self.assertEqual(rows[0]["string_raw_offset"], 0x180)

    def test_wrong_group_or_duplicate_selector_refuses_evidence(self) -> None:
        data, pe = self._fixture()
        wrong = bytearray(data)
        struct.pack_into("<i", wrong, 0x100, 0x38)
        with self.assertRaisesRegex(extractor.EvidenceError, "unexpected group"):
            extractor.extract_table(bytes(wrong), pe, raw_offset=0x100, row_count=1)
        dup = bytearray(data)
        struct.pack_into("<iiI", dup, 0x10C, 0x39, 2, 0x401080)
        with self.assertRaisesRegex(extractor.EvidenceError, "duplicate selector"):
            extractor.extract_table(bytes(dup), pe, raw_offset=0x100, row_count=2)

    def test_checked_in_demo_maps_preserve_mercedes_selector_and_classification(self) -> None:
        evidence = json.loads((Path(__file__).resolve().parents[2]
                               / "research/vehicles/ai/demo-group-39.json").read_text(encoding="utf-8"))
        self.assertEqual(len(evidence["builds"]), 2)
        for build in evidence["builds"]:
            with self.subTest(build=build["build"]):
                self.assertEqual(build["physical_mercedes_id2_selector"], 2)
                self.assertEqual(build["physical_mercedes_id2_name"], "JOSE MARIA SERCIA")
                for table in build["tables"]:
                    row = next(row for row in table["rows"] if row["selector"] == 2)
                    self.assertEqual(row["text"], "JOSE MARIA SERCIA")


if __name__ == "__main__":
    unittest.main()
