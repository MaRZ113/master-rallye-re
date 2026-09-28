from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from build_dx_upgrader_release import (
    ARCHIVE_NAME,
    REQUIRED_MEMBERS,
    RUNTIME_MODULES,
    TOP_LEVEL,
    build_release,
    validate_member_content,
    validate_member_names,
    validate_release_zip,
)


class DxUpgraderReleaseTests(unittest.TestCase):
    def test_positive_allowlist_contains_only_runtime_and_user_docs(self):
        self.assertEqual(len(REQUIRED_MEMBERS), 19)
        self.assertIn(f"{TOP_LEVEL}/README.md", REQUIRED_MEMBERS)
        self.assertIn(f"{TOP_LEVEL}/LICENSE", REQUIRED_MEMBERS)
        self.assertIn(f"{TOP_LEVEL}/tools/upgrade_dx_131_to_135.py", REQUIRED_MEMBERS)
        self.assertIn("version.py", RUNTIME_MODULES)
        self.assertNotIn(f"{TOP_LEVEL}/research/corpus-coverage.json", REQUIRED_MEMBERS)
        self.assertTrue(all(not name.endswith((".dx", ".dxt", ".gxm", ".gxi", ".exe", ".sma"))
                            for name in REQUIRED_MEMBERS))

    def test_forbidden_game_assets_and_research_paths_are_rejected(self):
        for relative in (
            "car.dx", "texture.dxt", "source.gxm", "image.gxi", "data.gxb",
            "MRallye.exe", "Data.sma", "Data.sma.backup",
            ".research-output/capture.json", "inputs/vehicle.json", ".git/config",
            "research/private.md", "Ghidra/project.rep",
        ):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                validate_member_names(sorted(REQUIRED_MEMBERS) + [f"{TOP_LEVEL}/{relative}"])

    def test_path_traversal_absolute_paths_and_wrong_top_level_are_rejected(self):
        for name in (
            f"{TOP_LEVEL}/../outside.py",
            "../MasterRallye-DX-Upgrader-v0.1.0/README.md",
            "C:/local/file.py",
            f"{TOP_LEVEL}/C:/local/file.py",
            f"{TOP_LEVEL}/docs//extra.md",
            "other-release/README.md",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_member_names(sorted(REQUIRED_MEMBERS) + [name])

    def test_machine_paths_and_executable_signatures_are_rejected(self):
        for name, content in (
            (f"{TOP_LEVEL}/README.md", b"Local path D:\\Game\\Master Rallye"),
            (f"{TOP_LEVEL}/README.md", b"User path C:\\Users\\MaRZ\\Desktop"),
            (f"{TOP_LEVEL}/tools/tool.py", b"MZ\\x90\\x00"),
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_member_content(name, content)

    def test_validator_rejects_symlink_members_and_unexpected_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "bad.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for member in sorted(REQUIRED_MEMBERS):
                    info = zipfile.ZipInfo(member)
                    info.external_attr = (0o120777 << 16) if member.endswith("/LICENSE") else (0o100644 << 16)
                    archive.writestr(info, b"text")
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                validate_release_zip(archive_path)

    def test_build_is_deterministic_and_clean_extraction_smokes_readme_commands(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_path = root / ARCHIVE_NAME
            first = build_release(first_path, smoke_test=True)
            self.assertEqual(set(validate_release_zip(first_path)), REQUIRED_MEMBERS)
            self.assertEqual(first["file_count"], len(REQUIRED_MEMBERS))
            self.assertEqual(first["sha256"], hashlib.sha256(first_path.read_bytes()).hexdigest())
            self.assertTrue(Path(first["checksum_path"]).is_file())

            second_path = root / "second.zip"
            second = build_release(second_path, smoke_test=False)
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
