from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "tools" / "scanner"
if str(SCANNER) not in sys.path:
    sys.path.insert(0, str(SCANNER))

from r_dev1_debug_capture import new_lines


class DebugCaptureDeltaTests(unittest.TestCase):
    def test_appended_lines_after_overlapping_scroll_window(self):
        self.assertEqual(
            new_lines(["one", "two", "three"], ["two", "three", "four"]),
            ["four"],
        )

    def test_identical_snapshot_has_no_delta(self):
        self.assertEqual(new_lines(["same"], ["same"]), [])

    def test_changed_line_after_common_header_is_appended(self):
        self.assertEqual(new_lines(["header", "old"], ["header", "new"]), ["new"])


if __name__ == "__main__":
    unittest.main()
