from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_r5v_e0_1d_override_bypass as legacy_bypass


class RetiredColourBypassTests(unittest.TestCase):
    def test_legacy_generator_refuses_invalid_abi_output(self):
        with self.assertRaisesRegex(legacy_bypass.PatchError, "retired.*RET 4"):
            legacy_bypass.build_candidate(b"old candidate source")


if __name__ == "__main__":
    unittest.main()
