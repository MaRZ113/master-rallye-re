from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for item in (ROOT, ROOT / "src"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from master_rallye.course_tag100 import CourseTag100, parse_course_tag100_bytes, translate_plane_distance
from master_rallye.errors import BoundsError, FormatError


def _node(field_0, field_1, *, optional=None, items=(), child=None, sibling=None):
    output = bytearray(struct.pack("<2I", field_0, field_1))
    output += struct.pack("<B", optional is not None)
    if optional is not None:
        output += struct.pack("<4fI", *optional)
    output += struct.pack("<B", bool(items))
    if items:
        output += struct.pack("<I", len(items))
        for item in items:
            output += struct.pack("<4fI", *item)
    output += struct.pack("<B", child is not None)
    if child is not None:
        child_role, child_bytes = child
        output += struct.pack("<B", child_role)
        output += child_bytes
    output += struct.pack("<B", sibling is not None)
    if sibling is not None:
        sibling_role, sibling_bytes = sibling
        output += struct.pack("<B", sibling_role)
        output += sibling_bytes
    return bytes(output)


def _tag100(words, root):
    return struct.pack("<I5I", 100, *words) + root


class R5TF2CourseTag100Tests(unittest.TestCase):
    def test_parses_header_optional_record_list_and_child_sibling_roles(self):
        sibling = _node(5, 6)
        child = _node(3, 4, sibling=(0, sibling))
        root = _node(
            1,
            2,
            optional=(0.0, 1.0, 0.0, -3.0, 9),
            items=((1.0, 2.0, 3.0, 4.0, 7),),
            child=(1, child),
        )
        parsed = parse_course_tag100_bytes(_tag100((1, 0, 1, 1, 1), root), "synthetic")
        self.assertEqual(parsed.header_words, (1, 0, 1, 1, 1))
        self.assertEqual(parsed.tree_offset, 24)
        self.assertEqual(len(parsed.nodes), 3)
        self.assertEqual(parsed.allocation_role_counts, (
            ("root", 1), ("pool8_child", 1), ("pool8_sibling", 0), ("pool36", 1),
        ))
        self.assertEqual(parsed.nodes[0].first_child_index, 1)
        self.assertEqual(parsed.nodes[1].next_sibling_index, 2)
        self.assertEqual(parsed.nodes[2].parent_index, 0)
        self.assertEqual(parsed.nodes[0].optional_record.values, (0.0, 1.0, 0.0, -3.0))
        self.assertEqual(parsed.nodes[0].optional_record.code, 9)
        self.assertEqual(parsed.nodes[0].list_items[0].vector, (1.0, 2.0, 3.0))
        self.assertEqual(parsed.nodes[0].list_items[0].value, 4.0)
        self.assertEqual(parsed.nodes[0].list_items[0].code, 7)
        self.assertTrue(parsed.complete)

    def test_accepts_empty_root_with_five_header_words(self):
        parsed = parse_course_tag100_bytes(_tag100((0, 0, 0, 0, 0), _node(0, 0)))
        self.assertEqual(parsed.structural_summary()["node_count"], 1)
        self.assertEqual(parsed.structural_summary()["optional_record_count"], 0)

    def test_preserves_top_level_root_sibling_chain(self):
        second_root = _node(3, 4)
        first_root = _node(1, 2, sibling=(1, second_root))
        parsed = parse_course_tag100_bytes(_tag100((0, 1, 0, 1, 0), first_root))
        self.assertEqual(len(parsed.nodes), 2)
        self.assertIsNone(parsed.nodes[1].parent_index)
        self.assertEqual(parsed.nodes[0].next_sibling_index, 1)
        self.assertEqual(parsed.nodes[1].allocation_role, "pool8_sibling")

    def test_rejects_wrong_tag_and_non_boolean_flags(self):
        with self.assertRaises(FormatError):
            parse_course_tag100_bytes(struct.pack("<I5I", 101, 0, 0, 0, 0, 0) + _node(0, 0))
        malformed = bytearray(_tag100((0, 0, 0, 0, 0), _node(0, 0)))
        malformed[32] = 2
        with self.assertRaisesRegex(FormatError, "non-boolean"):
            parse_course_tag100_bytes(bytes(malformed))

    def test_rejects_truncated_payload_and_nonzero_trailing_data(self):
        raw = _tag100((0, 0, 0, 0, 0), _node(0, 0))
        with self.assertRaises(BoundsError):
            parse_course_tag100_bytes(raw[:-1])
        with self.assertRaisesRegex(FormatError, "trailing bytes"):
            parse_course_tag100_bytes(raw + b"\x00")

    def test_rejects_pool_or_list_counts_exceeding_header(self):
        child = _node(1, 1)
        root = _node(0, 0, child=(1, child))
        with self.assertRaisesRegex(FormatError, "exceeds declared counts"):
            parse_course_tag100_bytes(_tag100((0, 0, 0, 0, 0), root))
        root_with_list = _node(0, 0, items=((1.0, 2.0, 3.0, 4.0, 5),))
        with self.assertRaisesRegex(FormatError, "exceeds header count"):
            parse_course_tag100_bytes(_tag100((0, 0, 0, 0, 0), root_with_list))

    def test_plane_translation_uses_n_dot_translation(self):
        normal = (0.6, 0.0, 0.8)
        baseline_d = -12.5
        shifted = translate_plane_distance(normal, baseline_d, (20.0, 0.0, 0.0))
        self.assertAlmostEqual(shifted, baseline_d - 20.0 * normal[0])
        self.assertAlmostEqual(translate_plane_distance((0.0, 1.0, 0.0), 4.0, (20.0, 0.0, 0.0)), 4.0)

    def test_course_tag100_model_exposes_no_writer_or_rebuild_api(self):
        self.assertFalse(hasattr(CourseTag100, "write"))
        self.assertFalse(hasattr(CourseTag100, "edit"))
        self.assertFalse(hasattr(CourseTag100, "rebuild"))


if __name__ == "__main__":
    unittest.main()
