from __future__ import annotations

import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for item in (ROOT, ROOT / "tools"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from r5t_f0_cooker_runs import _diff_bytes, _replace_staged_copy, _stable_tag_effect


class R5TF0CookerStageTests(unittest.TestCase):
    def test_equal_size_tag_diff_reports_exact_changed_ranges(self):
        diff = _diff_bytes(b"abcde", b"abXde")

        self.assertTrue(diff["same_size"])
        self.assertEqual(diff["changed_bytes"], 1)
        self.assertEqual(diff["changed_ranges"], [{"offset": 2, "length": 1}])
        self.assertEqual(diff["added_tail_bytes"], 0)
        self.assertEqual(diff["removed_tail_bytes"], 0)

    def test_different_size_tag_diff_reports_prefix_and_tail_without_total(self):
        diff = _diff_bytes(b"abcdef", b"abXY")

        self.assertFalse(diff["same_size"])
        self.assertIsNone(diff["changed_bytes"])
        self.assertEqual(diff["common_prefix_bytes_compared"], 4)
        self.assertEqual(diff["changed_bytes_in_common_prefix"], 2)
        self.assertEqual(diff["changed_ranges_in_common_prefix"], [{"offset": 2, "length": 2}])
        self.assertEqual(diff["added_tail_bytes"], 0)
        self.assertEqual(diff["removed_tail_bytes"], 2)
        self.assertEqual(diff["first_length_divergence_offset"], 4)

    def test_stable_tag_effect_handles_different_cohort_lengths(self):
        baseline = (b"baseline-tag",) * 3
        modified = (b"shorter-tag",) * 3
        self.assertTrue(_stable_tag_effect(baseline, modified))
        self.assertFalse(_stable_tag_effect(baseline, (b"x", b"y", b"x")))
        self.assertFalse(_stable_tag_effect((b"x", None, b"x"), modified))

    def test_large_tag_diff_keeps_exact_range_report_bounded(self):
        first = b"\x00\x00" * 3000
        second = b"\x01\x00" * 3000

        diff = _diff_bytes(first, second)

        self.assertEqual(diff["changed_bytes"], 3000)
        self.assertEqual(diff["changed_range_count_in_common_prefix"], 3000)
        self.assertFalse(diff["changed_ranges_complete"])
        self.assertIsNone(diff["changed_ranges_in_common_prefix"])
        self.assertEqual(diff["changed_range_length_histogram"], {"1": 3000})
        self.assertEqual(len(diff["changed_range_samples"]["first"]), 16)
        self.assertEqual(len(diff["changed_range_samples"]["last"]), 16)
        self.assertEqual(len(diff["changed_range_samples"]["largest"]), 16)

    def test_replaces_a_read_only_staged_input_without_touching_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "modified.gxm"
            target = root / "runtime" / "France1.gxm"
            target.parent.mkdir()
            source.write_bytes(b"modified source")
            target.write_bytes(b"baseline source")
            target.chmod(target.stat().st_mode & ~stat.S_IWRITE)

            _replace_staged_copy(target, source)

            self.assertEqual(target.read_bytes(), b"modified source")
            self.assertEqual(source.read_bytes(), b"modified source")


if __name__ == "__main__":
    unittest.main()
