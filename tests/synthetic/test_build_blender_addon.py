from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_blender_addon import build, source_files, verify_package_freshness  # noqa: E402


class BlenderAddonPackageFreshnessTests(unittest.TestCase):
    def _write_source(self, root: Path, relative: str, content: bytes) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_build_checks_all_addon_and_vendored_python_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_source(root, "blender/master_rallye_io/blender_materials.py", b"material-source\n")
            self._write_source(root, "blender/master_rallye_io/operators/import_course_xml.py", b"course-source\n")
            self._write_source(root, "src/master_rallye/material_semantics.py", b"semantics-source\n")
            output = root / "dist" / "addon.zip"

            result = build(output, root)
            source_members = {member for _path, member in source_files(root)}
            checked_members = {entry["member"] for entry in result["freshness_check"]["files"]}
            self.assertEqual(result["freshness_check"]["status"], "PASS")
            self.assertEqual(checked_members, source_members | {"master_rallye_io/vendor/__init__.py"})
            self.assertEqual(result["freshness_check"]["python_source_members_checked"], 4)
            self.assertEqual(len(result["zip_sha256"]), 64)
            self.assertEqual(len(verify_package_freshness(output, root)), 4)

            addon_material = root / "blender/master_rallye_io/blender_materials.py"
            addon_material.write_bytes(b"changed after package build\n")
            with self.assertRaisesRegex(RuntimeError, "stale add-on ZIP member master_rallye_io/blender_materials.py"):
                verify_package_freshness(output, root)

            result = build(output, root)
            self.assertEqual(result["freshness_check"]["status"], "PASS")
            vendored_material = root / "src/master_rallye/material_semantics.py"
            vendored_material.write_bytes(b"changed vendored semantics\n")
            with self.assertRaisesRegex(
                RuntimeError,
                "stale add-on ZIP member master_rallye_io/vendor/master_rallye/material_semantics.py",
            ):
                verify_package_freshness(output, root)

    def test_missing_and_unexpected_python_members_fail_freshness(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_source(root, "blender/master_rallye_io/ui.py", b"ui\n")
            output = root / "dist" / "addon.zip"
            build(output, root)

            with zipfile.ZipFile(output, "r") as archive:
                entries = [(name, archive.read(name)) for name in archive.namelist()
                           if name != "master_rallye_io/ui.py"]
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, payload in entries:
                    archive.writestr(name, payload)
            with self.assertRaisesRegex(RuntimeError, "missing Python source members"):
                verify_package_freshness(output, root)

            build(output, root)
            with zipfile.ZipFile(output, "a", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("master_rallye_io/old_material_preview.py", b"stale\n")
            with self.assertRaisesRegex(RuntimeError, "unexpected Python source members"):
                verify_package_freshness(output, root)


if __name__ == "__main__":
    unittest.main()
