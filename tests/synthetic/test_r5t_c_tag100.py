from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "src", ROOT / "tests" / "synthetic"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.errors import FormatError
from master_rallye.tag100_diff import (
    Tag100Slice,
    analyze_tag100_diff,
    changed_ranges,
    extract_tag100_from_dx_bytes,
    plane_residual,
    translated_plane_d,
)


class R5TCTag100DiffTests(unittest.TestCase):
    def test_contiguous_ranges_are_exact_and_end_exclusive(self):
        before = bytes(range(32))
        after = bytearray(before)
        after[2] ^= 1
        after[3] ^= 1
        after[9] ^= 1
        self.assertEqual(changed_ranges(before, bytes(after)), [
            {"start": 2, "end_exclusive": 4, "length": 2},
            {"start": 9, "end_exclusive": 10, "length": 1},
        ])

    def test_changed_tail_is_reported_without_claiming_alignment(self):
        self.assertEqual(changed_ranges(b"abcd", b"abXYmore"), [
            {"start": 2, "end_exclusive": 8, "length": 6},
        ])

    def test_candidate_float4_normal_and_neighbor_records(self):
        baseline = bytearray(struct.pack("<I", 100) + bytes(12))
        modified = bytearray(baseline)
        baseline += struct.pack("<4f", 1.0, 0.0, 0.0, -2.0)
        baseline += struct.pack("<4f", 0.0, 1.0, 0.0, -4.0)
        modified += struct.pack("<4f", 1.0, 0.0, 0.0, -3.0)
        modified += struct.pack("<4f", 0.0, 1.0, 0.0, -4.0)
        left = Tag100Slice("base", 120, bytes(baseline), True)
        right = Tag100Slice("edit", 240, bytes(modified), True)
        report = analyze_tag100_diff(left, right)
        self.assertEqual(report["summary"]["changed_byte_count"], 1)
        self.assertEqual(report["summary"]["unit_normal_like_changed_float4_window_count"], 1)
        candidate = report["unit_normal_like_float4_candidates"][0]
        self.assertEqual(candidate["offset"], 16)
        self.assertAlmostEqual(candidate["d_delta"], -1.0)
        self.assertEqual(candidate["changed_components"], [3])
        self.assertTrue(candidate["neighboring_float4_windows"]["next"]["changed"] is False)
        self.assertEqual(report["changed_range_clusters"][0]["maximum_join_gap"], 65536)

    def test_rejects_bad_markers_and_different_region_sizes(self):
        with self.assertRaises(FormatError):
            analyze_tag100_diff(
                Tag100Slice("base", 0, b"bad!", True),
                Tag100Slice("edit", 0, b"bad!", True),
            )
        with self.assertRaisesRegex(FormatError, "sizes differ"):
            analyze_tag100_diff(
                Tag100Slice("base", 0, struct.pack("<I", 100) + b"x", True),
                Tag100Slice("edit", 0, struct.pack("<I", 100) + b"xy", True),
            )

    def test_extract_uses_parser_boundary_and_preserves_exact_suffix(self):
        from test_r5t_a import synthetic_course_dx

        source = synthetic_course_dx()
        section = extract_tag100_from_dx_bytes(source, "synthetic-course.dx")
        self.assertTrue(section.render_validated)
        self.assertEqual(section.raw, struct.pack("<I", 100) + b"synthetic BSP bytes")
        self.assertEqual(source[section.tag_offset:], section.raw)
        with self.assertRaisesRegex(FormatError, "no structurally detected tag100"):
            extract_tag100_from_dx_bytes(source[:section.tag_offset], "without-tag100.dx")

    def test_plane_residual_and_translation_law_keep_conventions_explicit(self):
        normal = (1.0, 0.0, 0.0)
        point = (2.0, 3.0, 4.0)
        self.assertEqual(plane_residual(normal, -2.0, point, convention="dot_plus_d_zero"), 0.0)
        self.assertEqual(plane_residual(normal, 2.0, point, convention="dot_equals_d"), 0.0)
        translation = (3.0, 0.0, 0.0)
        self.assertEqual(
            translated_plane_d(normal, -2.0, translation, convention="dot_plus_d_zero"), -5.0
        )
        self.assertEqual(
            translated_plane_d(normal, 2.0, translation, convention="dot_equals_d"), 5.0
        )
        with self.assertRaises(ValueError):
            plane_residual(normal, 0.0, point, convention="guessed")


if __name__ == "__main__":
    unittest.main()
