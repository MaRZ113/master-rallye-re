from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for item in (ROOT, ROOT / "src"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from master_rallye.course_tag1400 import CourseTag1400, parse_course_tag1400_bytes
from master_rallye.errors import BoundsError, FormatError


def _tag1400(*, dims=(2, 1), cells=((7, 8), ()), strings=(b"a", b"bc"), records=()):
    output = bytearray(struct.pack("<IfII3f3f", 1400, 2.5, *dims, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0))
    for entries in cells:
        output += struct.pack("<I", len(entries))
        output += struct.pack(f"<{len(entries)}I", *entries) if entries else b""
    output += struct.pack("<I", len(strings))
    for item in strings:
        output += struct.pack("<I", len(item)) + item
    output += struct.pack("<I", len(records))
    for prefix, ref, suffix in records:
        output += struct.pack("<9fI4f", *prefix, ref, *suffix)
    return bytes(output)


class R5TF21CourseTag1400Tests(unittest.TestCase):
    def test_parses_header_dimensioned_cell_lists_strings_and_records(self):
        raw = _tag1400(records=[(tuple(float(i) for i in range(9)), 1, (9.0, 10.0, 11.0, 12.0))])
        parsed = parse_course_tag1400_bytes(raw, "synthetic")
        self.assertEqual(parsed.scalar, 2.5)
        self.assertEqual((parsed.dimension_0, parsed.dimension_1), (2, 1))
        self.assertEqual(parsed.vector_a, (1.0, 2.0, 3.0))
        self.assertEqual(parsed.vector_b, (4.0, 5.0, 6.0))
        self.assertEqual([cell.entries for cell in parsed.cells], [(7, 8), ()])
        self.assertEqual([item.raw_bytes for item in parsed.strings], [b"a", b"bc"])
        self.assertEqual(parsed.records[0].float_prefix, tuple(float(i) for i in range(9)))
        self.assertEqual(parsed.records[0].string_ref_index, 1)
        self.assertEqual(parsed.records[0].float_suffix, (9.0, 10.0, 11.0, 12.0))
        self.assertEqual(parsed.consumed_size, len(raw))
        self.assertTrue(parsed.complete)

    def test_preserves_section_boundary_when_later_region_is_allowed(self):
        raw = _tag1400() + struct.pack("<I", 1500) + b"later"
        parsed = parse_course_tag1400_bytes(raw, allow_trailing=True)
        self.assertEqual(parsed.consumed_size, len(_tag1400()))
        self.assertEqual(parsed.trailing_size, 9)

    def test_rejects_wrong_tag_and_strict_trailing_bytes(self):
        raw = bytearray(_tag1400())
        struct.pack_into("<I", raw, 0, 100)
        with self.assertRaises(FormatError):
            parse_course_tag1400_bytes(bytes(raw))
        with self.assertRaisesRegex(FormatError, "trailing bytes"):
            parse_course_tag1400_bytes(_tag1400() + b"x")

    def test_rejects_dimensions_that_exceed_bounded_product(self):
        raw = bytearray(struct.pack("<IfII3f3f", 1400, 1.0, 4_000_000, 2, *(0.0,) * 6))
        with self.assertRaisesRegex(FormatError, "cell count"):
            parse_course_tag1400_bytes(bytes(raw), allow_trailing=True)

    def test_rejects_truncated_cell_list_and_record_region(self):
        raw = _tag1400()
        with self.assertRaises(BoundsError):
            parse_course_tag1400_bytes(raw[:-2])
        with self.assertRaises(BoundsError):
            parse_course_tag1400_bytes(raw[:-1])

    def test_rejects_record_string_reference_outside_table(self):
        raw = _tag1400(records=[((0.0,) * 9, 2, (0.0,) * 4)])
        with self.assertRaisesRegex(FormatError, "references string"):
            parse_course_tag1400_bytes(raw)

    def test_model_has_no_writer_api(self):
        self.assertFalse(hasattr(CourseTag1400, "write"))
        self.assertFalse(hasattr(CourseTag1400, "edit"))
        self.assertFalse(hasattr(CourseTag1400, "rebuild"))


if __name__ == "__main__":
    unittest.main()
