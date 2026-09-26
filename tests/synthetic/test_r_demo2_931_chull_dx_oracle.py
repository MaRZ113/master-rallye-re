from __future__ import annotations

import struct
import unittest

from tools.scanner.r_demo2_931_chull_dx_oracle import (
    byte_diff_summary,
    compare_pair,
    vector_delta_summary,
)


def dx_fixture(position_x: float = 1.0, *, draw_word: int = 22) -> bytes:
    return (struct.pack("<4I", 0xD00D, 131, 1337, 1)
            + struct.pack("<3f", position_x, 0, 0)
            + struct.pack("<3f", 0, 0, 1)
            + bytes((255, 128, 0, 255))
            + struct.pack("<I", 0)
            + struct.pack("<I3H", 3, 0, 0, 0)
            + struct.pack("<2I", 1, draw_word)
            + struct.pack("<5I", 1, 3, 0, 0, 0))


class Demo931ChullDxOracleTests(unittest.TestCase):
    def test_expected_coordinate_translation_and_float_noise_are_distinct(self):
        translated = vector_delta_summary(((0.0, 2.0, 3.0),), ((0.1, 2.0, 3.0),),
                                          expected=(0.1, 0.0, 0.0))
        noise = vector_delta_summary(((1.0, 2.0, 3.0),),
                                     ((1.000001, 2.0, 3.0),), expected=(0.0, 0.0, 0.0))
        self.assertEqual(translated["classification"], "INTENTIONAL_TRANSLATION")
        self.assertEqual(noise["classification"], "SEMANTIC_FLOAT_NOISE")

    def test_byte_diff_ranges_are_exact_and_parser_fields_remain_structured(self):
        first = dx_fixture()
        same = byte_diff_summary(first, first)
        self.assertTrue(same["byte_identical"])
        self.assertEqual(same["changed_byte_count"], 0)

        changed = dx_fixture(draw_word=23)
        report = compare_pair(first, changed, first_source="baseline A",
                              second_source="baseline B", role="baseline")
        self.assertFalse(report["byte_diff"]["byte_identical"])
        self.assertTrue(report["byte_diff"]["changed_byte_offsets"])
        self.assertFalse(report["render"]["draw_material_raw"]["byte_identical"])
        self.assertEqual(report["classification"]["topology"], "NOT_PARSED")

    def test_candidate_role_flags_render_change_as_unexpected_without_tag101(self):
        report = compare_pair(dx_fixture(), dx_fixture(position_x=1.25),
                              first_source="baseline", second_source="candidate",
                              role="candidate")
        self.assertTrue(report["classification"]["unexpected_change"])
        self.assertFalse(report["classification"]["intentional_translation"])
        self.assertIn("tag101 is absent or incomplete", report["unexpected_changes"])


if __name__ == "__main__":
    unittest.main()
