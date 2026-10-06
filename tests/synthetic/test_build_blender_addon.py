from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_blender_addon import FRESHNESS_FILES, build, verify_package_freshness  # noqa: E402


class BlenderAddonPackageFreshnessTests(unittest.TestCase):
    def test_build_checks_current_key_sources_and_reports_zip_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, member in enumerate(FRESHNESS_FILES):
                source = root / "blender" / "master_rallye_io" / Path(member).relative_to("master_rallye_io")
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(f"source-{index}\n".encode("ascii"))
            output = root / "dist" / "addon.zip"
            result = build(output, root)
            self.assertEqual(result["freshness_check"]["status"], "PASS")
            self.assertEqual([entry["member"] for entry in result["freshness_check"]["files"]], list(FRESHNESS_FILES))
            self.assertEqual(len(result["zip_sha256"]), 64)
            self.assertEqual(len(verify_package_freshness(output, root)), len(FRESHNESS_FILES))

            stale_source = root / "blender" / "master_rallye_io" / Path(FRESHNESS_FILES[0]).relative_to("master_rallye_io")
            stale_source.write_bytes(b"changed after package build\n")
            with self.assertRaisesRegex(RuntimeError, "stale add-on ZIP member"):
                verify_package_freshness(output, root)


if __name__ == "__main__":
    unittest.main()
