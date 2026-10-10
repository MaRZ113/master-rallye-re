from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/runtime"))
import build_observatory_release as release


class ObservatoryReleaseTests(unittest.TestCase):
    def payload(self):
        return release.collect_files(ROOT)

    def test_explicit_allowlist_and_standalone_files(self):
        payload = self.payload()
        self.assertEqual(set(payload), set(release.FILES))
        self.assertIn("observatory_compatibility.py", payload)
        self.assertIn("data/broker-families.json", payload)
        self.assertIn("data/registry-profiles.json", payload)
        self.assertIn("LICENSE", payload)
        for data in payload.values():
            self.assertFalse(release.LOCAL_PATH_PATTERNS[0].search(data.decode("utf-8")))
        release.validate_import_closure(payload)

    def test_prohibited_paths_and_files_fail_closed(self):
        for name in (
            "MRallye.exe", "MRallye_research.exe", "Data.sma", "vehicles/car.dx",
            "research-output/config.json", "research/feature.json", "captures/state.json",
            "assets/car.png", "local-profile.json", "bundle.zip",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                release.reject_forbidden((name,))
        with self.assertRaisesRegex(ValueError, "Executable signature"):
            payload = self.payload()
            payload["README.md"] = b"MZ"
            release.validate_payloads(payload)

    def test_developer_machine_paths_and_research_imports_rejected(self):
        payload = self.payload()
        payload["README.md"] += b"\nD:\\Game\\Master Rallye\\MRallye.exe\n"
        with self.assertRaisesRegex(ValueError, "Developer-machine absolute path"):
            release.validate_payloads(payload)
        payload = self.payload()
        payload["README.md"] += b"\nC:\\Users\\MaRZ\\private\\file.json\n"
        with self.assertRaisesRegex(ValueError, "Developer-machine absolute path"):
            release.validate_payloads(payload)
        payload = self.payload()
        payload["mr_observe.py"] += b"\nimport research_build_profiles\n"
        with self.assertRaisesRegex(ValueError, "Repository-only research import"):
            release.validate_payloads(payload)

    def test_nonstdlib_unbundled_import_rejected(self):
        payload = self.payload()
        payload["mr_observe.py"] += b"\nimport unsupported_third_party_package\n"
        with self.assertRaisesRegex(ValueError, "Unpackaged or non-stdlib import"):
            release.validate_payloads(payload)

    def test_archive_is_deterministic_and_manifest_verified(self):
        payload = self.payload()
        first, manifest = release.build_bytes(payload, "a" * 40)
        second, same_manifest = release.build_bytes(payload, "a" * 40)
        self.assertEqual(first, second)
        self.assertEqual(manifest, same_manifest)
        self.assertEqual(manifest["archive_sha256"], hashlib.sha256(first).hexdigest())
        self.assertEqual(manifest["version"], "0.2.3-beta")
        self.assertEqual(manifest["game_executables"], 0)
        self.assertEqual(manifest["game_assets"], 0)
        self.assertEqual(manifest["absolute_repo_dependencies"], 0)
        release.validate_release(first, manifest)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(set(archive.namelist()), set(payload))
            self.assertNotIn("MRallye.exe", archive.namelist())
            self.assertEqual(archive.read("observatory_version.py"), payload["observatory_version.py"])

    def test_unallowlisted_member_rejected(self):
        payload = self.payload()
        payload["MRallye.exe"] = b"not a game"
        with self.assertRaises(ValueError):
            release.build_bytes(payload, "a" * 40)

    def test_manifest_tamper_rejected(self):
        raw, manifest = release.build_bytes(self.payload(), "a" * 40)
        manifest["game_executables"] = 1
        with self.assertRaisesRegex(ValueError, "manifest"):
            release.validate_release(raw, manifest)

    def test_clean_extraction_runs_isolated_entrypoints_and_launcher(self):
        raw, _manifest = release.build_bytes(self.payload(), "a" * 40)
        with tempfile.TemporaryDirectory(prefix="mr-observatory-test-") as folder:
            root = Path(folder)
            self.assertFalse(root.resolve().is_relative_to(ROOT.resolve().parent))
            release._clean_extraction_smoke(raw, root)
            self.assertTrue((root / "observatory-data/config.json").is_file())


if __name__ == "__main__":
    unittest.main()
