from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_rmod2_public_release as release


class PublicReleasePreparationTests(unittest.TestCase):
    def test_release_ini_is_ascii_version_two_with_requested_defaults(self):
        report = release.audit_release_ini(ROOT / "research/r-mod1/MRallyeRandomizer.release.ini")
        self.assertTrue(report["ascii"])
        self.assertLessEqual(report["bytes"], 4096)
        self.assertEqual(report["max_opponents"], 5)
        self.assertTrue(all(value == 4 for value in report["policy_values"].values()))
        text = (ROOT / "research/r-mod1/MRallyeRandomizer.release.ini").read_text(encoding="ascii")
        for value, name in enumerate(("Stock", "T1", "T2", "T3", "Full", "Mixed", "Diverse")):
            self.assertIn(f"; {value} = {name}\n", text)

    def test_release_ini_rejects_legacy_hidden_v2_switches(self):
        import tempfile
        source = ROOT / "research/r-mod1/MRallyeRandomizer.release.ini"
        with tempfile.TemporaryDirectory() as temp:
            invalid = Path(temp) / "invalid.ini"
            invalid.write_bytes(source.read_bytes() + b"\n[Experimental]\nExtendedAI = 1\n")
            with self.assertRaises(release.ReleaseError):
                release.audit_release_ini(invalid)

    def test_archive_writer_is_deterministic(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "src"
            root.mkdir()
            (root / "a.txt").write_text("alpha\n", encoding="ascii")
            (root / "b.txt").write_text("beta\n", encoding="ascii")
            first, second = Path(temp) / "one.zip", Path(temp) / "two.zip"
            release.create_zip(root, first, ["b.txt", "a.txt"])
            release.create_zip(root, second, ["a.txt", "b.txt"])
            self.assertEqual(release.sha256(first), release.sha256(second))

    def test_release_package_has_only_two_project_dlls(self):
        builder = (ROOT / "tools/build_rmod2_public_release.py").read_text(encoding="utf-8")
        self.assertIn('"dinput8.dll", "MRallyeRandomizerRuntime.dll"', builder)
        self.assertIn('"graphical_d3d8_proxy_included_or_modified": False', builder)
        self.assertIn("prohibited = (\".exe\"", builder)


if __name__ == "__main__":
    unittest.main()
