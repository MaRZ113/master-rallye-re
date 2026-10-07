from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import build_vehicle_hardened_candidate as candidate
import vehicle_hardened_runtime_package as package


class VehicleHardenedRuntimePackageTests(unittest.TestCase):
    def test_package_paths_reject_traversal_and_absolute_roots(self) -> None:
        with self.assertRaisesRegex(package.RuntimePackageError, "unsafe package-relative path"):
            package._safe_path(Path("C:/runtime"), "../MRallye.exe")
        with self.assertRaisesRegex(package.RuntimePackageError, "unsafe package-relative path"):
            package._safe_path(Path("C:/runtime"), "D:/other/MRallye.exe")

    def test_ordinary_and_forced_package_manifests_distinguish_forcing_not_randomizer(self) -> None:
        base = {
            "patched_sha256": "a" * 64,
            "file_size": 3121214,
            "patch_manifest_sha256": "b" * 64,
        }
        profile = {"profile": "pinned-g1"}
        for name, forced in (
            (candidate.PROFILE_ORDINARY, False),
            (candidate.PROFILE_FORCED, True),
        ):
            with self.subTest(profile=name):
                manifest = package._expected_manifest(
                    profile=profile,
                    profile_sha256="c" * 64,
                    candidate={**base, "profile": name},
                    rows=[],
                )
                self.assertEqual(manifest["forced_ai_proof"], forced)
                self.assertEqual(manifest["randomizer"], "not present")
                self.assertEqual(manifest["candidate"]["sha256"], "a" * 64)
                self.assertIn("PlayerState.xml", manifest["fresh_profile_policy"])


if __name__ == "__main__":
    unittest.main()
