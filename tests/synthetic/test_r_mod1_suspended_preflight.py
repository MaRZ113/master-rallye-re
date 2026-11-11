from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = Path(os.environ.get(
    "RMOD1_HOTFIX_CANDIDATE",
    ROOT / ".research-output" / "r-mod1" / "first-integrated-candidate-v5",
))
RETAIL_EXE = Path(os.environ.get(
    "RMOD1_RETAIL_EXE",
    r"D:\Game\Master Rallye\corpora\retail\MRallye.exe",
))


@unittest.skipUnless(sys.platform == "win32", "requires real Windows process creation and VirtualQueryEx")
class SuspendedProcessPreflightTests(unittest.TestCase):
    def test_exact_retail_mapping_is_verified_before_resume_or_native_writes(self) -> None:
        if os.environ.get("RMOD1_RUN_WINDOWS_PREFLIGHT") != "1":
            self.skipTest("set RMOD1_RUN_WINDOWS_PREFLIGHT=1 to create and terminate the real suspended retail child")
        launcher = CANDIDATE / "MRallyeRandomizerLauncher.exe"
        if not launcher.is_file() or not RETAIL_EXE.is_file():
            self.skipTest("build first-integrated-candidate-v5 and provide the exact retail executable")
        result = subprocess.run(
            [str(launcher), "--preflight", "--game-dir", str(RETAIL_EXE.parent)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode and "Windows error 623" in result.stderr:
            self.skipTest("host blocks the retail child at CreateProcessW with ERROR_ILLEGAL_DLL_RELOCATION before mapping")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("mapped_image=verified", result.stdout)
        self.assertIn("native_writes=0", result.stdout)
        self.assertIn("child_terminated_before_resume=1", result.stdout)
        self.assertIn("SUSPENDED_PREFLIGHT_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
