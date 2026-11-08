from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RMod1RuntimeLogTests(unittest.TestCase):
    def test_append_only_access_and_record_serialization_are_explicit(self) -> None:
        header = (ROOT / "src" / "native" / "rmod1" / "runtime_log.hpp").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "native" / "rmod1" / "runtime_core.cpp").read_text(encoding="utf-8")
        harness = (ROOT / "tests" / "rmod1" / "runtime_log_harness.cpp").read_text(encoding="utf-8")

        self.assertIn("CreateFileA(path, FILE_APPEND_DATA | FILE_READ_ATTRIBUTES,", header)
        self.assertNotIn("FILE_APPEND_DATA | GENERIC_WRITE", header)
        self.assertIn("RuntimeLogGuard guard", header)
        self.assertIn("WriteFile(file, record, record_size, &written, nullptr)", header)
        self.assertIn("MoveFileExA(path, rotated_path", header)
        self.assertIn("append_runtime_log_record_to_path(path, line)", runtime)
        self.assertIn('"CONFIG randomizer=1"', harness)
        self.assertIn('"START ADMITTED requested_ai=4"', harness)
        self.assertIn('"ROSTER OBSERVED race_numcars=5"', harness)
        self.assertIn("actual != expected", harness)


if __name__ == "__main__":
    unittest.main()
