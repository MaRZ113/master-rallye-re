from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
import sys
import re

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from master_rallye import parse_dx
from master_rallye.version import __version__
import master_rallye
from tools.build_vehicle_composer_release import (
    RELEASE_FILES,
    REQUIRED_MEMBERS,
    TOP_LEVEL,
    build_release,
    validate_member_content,
    validate_member_names,
    validate_release_zip,
)


class VehicleComposerReleaseTests(unittest.TestCase):
    def test_cli_version_matches_project_metadata(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"$', pyproject)
        self.assertIsNotNone(match)
        self.assertEqual(__version__, match.group(1))

    def test_lazy_package_exports_preserve_existing_public_names(self) -> None:
        expected = {
            "BoundsError", "ExportError", "DxWriteError", "CollisionWriteError",
            "FormatError", "MasterRallyeError", "UnknownRecordTagError",
            "DxSpatialBounds1339", "parse_bounds1339", "compute_bounds1339",
            "scale_tag101", "scale_dx_collision", "VehicleProject",
            "validate_vehicle", "build_vehicle_mod", "parse_dx", "parse_dx_bytes",
            "patch_dx_positions", "write_dx_positions", "audit_binary_diff",
            "parse_collision_sections", "serialize_tag101", "replace_dx_tag101",
            "translate_tag101", "patch_dx_collision_translation",
            "write_dx_collision_translation", "SOURCE_IDENTICAL",
            "POSITIONS_ONLY_CHANGED", "UNSUPPORTED_TOPOLOGY_CHANGED",
            "INVALID_PROVENANCE", "provenance_fingerprint",
            "validate_authoring_state", "parse_dxt", "parse_dxt_bytes",
            "decode_rgba_pixels", "encode_dxt_pixels", "replace_dxt_pixels",
            "parse_sidecar", "resolve_sidecar",
        }
        self.assertEqual(set(master_rallye.__all__), expected)
        self.assertTrue(all(hasattr(master_rallye, name) for name in expected))

    def test_required_curated_files_are_in_allowlist(self) -> None:
        self.assertEqual(len(RELEASE_FILES), len(REQUIRED_MEMBERS))
        self.assertIn("README.md", RELEASE_FILES)
        self.assertIn("LICENSE", RELEASE_FILES)
        self.assertIn("tools/vehicle_composer.py", RELEASE_FILES)
        self.assertIn("tools/physics_bind.py", RELEASE_FILES)
        self.assertIn("src/master_rallye/vehicle_composition.py", RELEASE_FILES)
        self.assertNotIn("tests/synthetic/test_vehicle_composer_release.py", RELEASE_FILES)
        self.assertTrue(callable(parse_dx))

    def test_game_assets_and_research_directories_are_rejected(self) -> None:
        base = list(REQUIRED_MEMBERS)
        for relative in (
            "payload.gxm", "payload.dx", "payload.dxt", "payload.exe",
            "Data.sma", "Data.sma.backup", ".research-output/capture.json",
            "corpora/retail.json", ".github/workflows/build.yml",
        ):
            with self.subTest(relative=relative):
                names = base + [f"{TOP_LEVEL}/{relative}"]
                with self.assertRaises(ValueError):
                    validate_member_names(names)

    def test_path_traversal_and_wrong_layout_are_rejected(self) -> None:
        for name in (
            f"{TOP_LEVEL}/../outside.py",
            "../MasterRallye-VehicleComposer-v0.1.0/README.md",
            "C:/temp/file.py",
            f"other-release/README.md",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_member_names(list(REQUIRED_MEMBERS) + [name])

    def test_normal_python_and_docs_content_is_accepted(self) -> None:
        validate_member_names(list(REQUIRED_MEMBERS))
        validate_member_content(f"{TOP_LEVEL}/README.md", b"# Vehicle Composer\n")
        validate_member_content(f"{TOP_LEVEL}/src/example.py", b"print('safe')\n")

    def test_files_outside_positive_allowlist_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the release allowlist"):
            validate_member_names(list(REQUIRED_MEMBERS) + [f"{TOP_LEVEL}/extra.py"])

    def test_suspicious_content_is_rejected(self) -> None:
        for name, content in (
            ("payload.py", b"MZ\x90\x00"),
            ("manifest.json", b'{"path":"D:\\Game\\Master Rallye"}'),
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_member_content(name, content)

    def test_release_build_validates_layout_and_clean_extraction_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            archive_path = Path(temp_name) / "candidate.zip"
            result = build_release(archive_path, smoke_test=True)
            members = validate_release_zip(archive_path)
            self.assertEqual(set(members), REQUIRED_MEMBERS)
            self.assertEqual(result["file_count"], len(REQUIRED_MEMBERS))
            second_path = Path(temp_name) / "candidate-second.zip"
            second = build_release(second_path, smoke_test=False)
            self.assertEqual(result["sha256"], second["sha256"])
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIn(f"{TOP_LEVEL}/README.md", archive.namelist())
                self.assertIn(f"{TOP_LEVEL}/LICENSE", archive.namelist())
                self.assertFalse(any(".gxm" in name.lower() for name in archive.namelist()))


if __name__ == "__main__":
    unittest.main()
