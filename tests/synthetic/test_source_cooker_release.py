from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "tools" / "build_source_cooker_release.py"
SPEC = importlib.util.spec_from_file_location("source_cooker_release_builder", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class SourceCookerReleaseValidationTests(unittest.TestCase):
    def test_positive_allowlist_and_expected_layout(self):
        members = sorted(f"{builder.TOP_LEVEL}/{name}" for name in builder.RELEASE_FILES)
        builder.validate_member_names(members)
        for unsafe in (
            f"{builder.TOP_LEVEL}/../escape.py",
            f"{builder.TOP_LEVEL}/DataGx/car.dx",
            f"{builder.TOP_LEVEL}/model.dxt",
            f"{builder.TOP_LEVEL}/model.gxm",
            f"{builder.TOP_LEVEL}/MRallye.exe",
            f"{builder.TOP_LEVEL}/Data.sma",
            f"{builder.TOP_LEVEL}/research-output/dump.json",
            "C:/absolute.py",
        ):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                builder.validate_member_names(members + [unsafe])

    def test_content_rejects_executable_and_local_path_leaks(self):
        for name, data in (
            (f"{builder.TOP_LEVEL}/README.md", b"MZ executable"),
            (f"{builder.TOP_LEVEL}/docs/notes.md", b"local path C:\\Users\\person\\Desktop"),
            (f"{builder.TOP_LEVEL}/docs/notes.md", b"/home/person/private"),
        ):
            with self.subTest(name=name, data=data), self.assertRaises(ValueError):
                builder.validate_member_content(name, data)

    def test_release_build_is_deterministic_and_clean_extraction_smokes(self):
        with tempfile.TemporaryDirectory(prefix="source cooker release tests ") as temporary:
            root = Path(temporary)
            first = builder.build_release(root / "first.zip", smoke_test=False)
            second = builder.build_release(root / "second.zip", smoke_test=False)
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first["file_count"], len(builder.RELEASE_FILES))
            self.assertEqual(set(first["members"]), set(
                f"{builder.TOP_LEVEL}/{name}" for name in builder.RELEASE_FILES
            ))
            result = builder.smoke_test_release(root / "first.zip")
            self.assertEqual(result, {
                "help": "PASS", "version": "PASS", "compileall": "PASS",
                "synthetic_offline_conversion": "PASS",
            })


if __name__ == "__main__":
    unittest.main()
