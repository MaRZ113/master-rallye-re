from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_observatory_research as builder


class ResearchPackageTests(unittest.TestCase):
    def test_allowlist_is_self_contained_and_excludes_game_binaries(self):
        payloads = builder.collect_payloads()
        self.assertIn("tools/runtime/observatory_profile_resolver.py", payloads)
        self.assertIn("tools/research_build_profiles.py", payloads)
        self.assertIn("research/r-observatory-modded-builds/build-profiles.json", payloads)
        self.assertIn("research/r-ai1/vehicle-class-map.json", payloads)
        self.assertIn("MRallye-Observatory-Research.cmd", payloads)
        self.assertNotIn("MRallye.exe", payloads)
        self.assertIn(b'VERSION = "R-OBS3"', payloads["tools/runtime/observatory_version.py"])
        launcher = payloads["MRallye-Observatory-Research.cmd"]
        self.assertIn(b"py -3 -c", launcher)
        self.assertIn(b"python -c", launcher)
        self.assertIn(b"%OBS_PY% tools\\runtime\\mr_observe.py %*", launcher)

    def test_archive_is_deterministic_and_manifest_verified(self):
        payloads = builder.collect_payloads()
        first, manifest = builder.build_archive(payloads)
        second, same_manifest = builder.build_archive(payloads)
        self.assertEqual(first, second)
        self.assertEqual(manifest, same_manifest)
        builder.verify_archive(first, manifest)
        corrupt = bytearray(first)
        corrupt[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "manifest identity"):
            builder.verify_archive(bytes(corrupt), manifest)

    def test_payload_policy_rejects_binary_and_machine_path(self):
        with self.assertRaisesRegex(ValueError, "forbidden"):
            builder.validate_payloads({"MRallye.exe": b"not a real exe"})
        with self.assertRaisesRegex(ValueError, "Local filesystem path"):
            builder.validate_payloads({"README.md": b"private path D:\\Games\\Install"})

    def test_rebuild_preserves_package_local_observatory_data(self):
        payloads = builder.collect_payloads()
        _archive, manifest = builder.build_archive(payloads)
        with tempfile.TemporaryDirectory() as td:
            package = Path(td) / "package"
            builder.write_directory(package, payloads, manifest)
            local_data = package / "research-output" / "captures" / "runtime.json"
            local_data.parent.mkdir(parents=True)
            local_data.write_text("preserve me", encoding="utf-8")
            pycache = package / "tools" / "runtime" / "__pycache__"
            pycache.mkdir(parents=True)
            pyc = pycache / "observatory.cpython-311.pyc"
            pyc.write_bytes(b"generated cache")
            builder.write_directory(package, payloads, manifest)
            self.assertEqual(local_data.read_text(encoding="utf-8"), "preserve me")
            self.assertEqual(pyc.read_bytes(), b"generated cache")


if __name__ == "__main__":
    unittest.main()
