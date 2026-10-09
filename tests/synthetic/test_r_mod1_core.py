from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests" / "rmod1" / "core_tests.cpp"
OUTPUT = ROOT / ".research-output" / "r-mod1" / "core-tests.exe"


class RMod1SharedCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        compiler = shutil.which("g++") or r"C:\msys64\ucrt64\bin\g++.exe"
        if not Path(compiler).exists():
            raise unittest.SkipTest("MinGW g++ is required to compile the portable R-MOD1 core fixture")
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        built = subprocess.run(
            [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", str(HARNESS), "-o", str(OUTPUT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if built.returncode:
            raise AssertionError(f"R-MOD1 C++ core test compilation failed:\n{built.stdout}\n{built.stderr}")

    def test_shared_core_semantics_and_fail_closed_guards(self) -> None:
        completed = subprocess.run([str(OUTPUT)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("failures=0", completed.stdout)
        self.assertIn("checks=", completed.stdout)


if __name__ == "__main__":
    unittest.main()
