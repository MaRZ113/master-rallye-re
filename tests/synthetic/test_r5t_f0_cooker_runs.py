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

from r5t_f0_cooker_runs import _replace_staged_copy


class R5TF0CookerStageTests(unittest.TestCase):
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
