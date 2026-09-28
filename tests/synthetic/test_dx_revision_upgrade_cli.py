from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import re
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_dx_revision_upgrade import (
    _rev131_fixture,
    _rev135_reordered_fixture,
    _index_array_range,
)
from master_rallye.dx_revision_upgrade import upgrade_dx_131_to_135


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPOSITORY_ROOT / "tools" / "upgrade_dx_131_to_135.py"
_SPEC = importlib.util.spec_from_file_location("dx_upgrade_cli_test_module", CLI_PATH)
assert _SPEC and _SPEC.loader
CLI_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CLI_MODULE)


class DxRevisionUpgradeCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mr-dx-upgrade-")
        self.root = Path(self.temp.name)
        self.fixture = _rev131_fixture()

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_and_version_are_available_without_repository_import_path(self):
        help_result = self.run_cli("--help")
        version_result = self.run_cli("--version")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--vehicle-dir", help_result.stdout)
        self.assertEqual(version_result.returncode, 0, version_result.stderr)
        self.assertEqual(version_result.stdout.strip(), "Master Rallye DX Upgrader 0.1.0")
        project = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project_section = re.search(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)", project)
        self.assertIsNotNone(project_section)
        declared_version = re.search(r'(?m)^version\s*=\s*"([^\"]+)"\s*$', project_section.group(1))
        self.assertIsNotNone(declared_version)
        self.assertIn(declared_version.group(1), version_result.stdout)

    def test_single_file_writes_valid_dx_and_machine_report(self):
        source = self.root / "input package with spaces" / "car.dx"
        output = self.root / "output package with spaces" / "car.rev135.dx"
        source.parent.mkdir()
        source.write_bytes(self.fixture)

        result = self.run_cli(str(source), "-o", str(output))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("revision 131", result.stdout)
        self.assertIn("revision 135", result.stdout)
        self.assertIn("canonical parser PASS", result.stdout)
        self.assertEqual(source.read_bytes(), self.fixture)
        self.assertEqual(output.read_bytes(), upgrade_dx_131_to_135(self.fixture))
        report_path = Path(str(output) + ".report.json")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["draw_records_transformed"], 2)
        self.assertEqual(report["output_path"], str(output.resolve()))

    def test_existing_outputs_are_not_overwritten_without_force(self):
        source = self.root / "car.dx"
        output = self.root / "car.rev135.dx"
        source.write_bytes(self.fixture)
        output.write_bytes(b"keep this")

        result = self.run_cli(str(source), "-o", str(output))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output already exists", result.stderr)
        self.assertEqual(output.read_bytes(), b"keep this")

    def test_force_replaces_output_but_never_allows_in_place(self):
        source = self.root / "car.dx"
        output = self.root / "car.rev135.dx"
        source.write_bytes(self.fixture)
        output.write_bytes(b"old output")

        result = self.run_cli(str(source), "-o", str(output), "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), upgrade_dx_131_to_135(self.fixture))
        self.assertEqual(source.read_bytes(), self.fixture)

        in_place = self.run_cli(str(source), "-o", str(source), "--force")
        self.assertNotEqual(in_place.returncode, 0)
        self.assertIn("in-place conversion is refused", in_place.stderr)
        self.assertEqual(source.read_bytes(), self.fixture)

    def test_vehicle_directory_processes_only_dx_roles_and_emits_manifest(self):
        source_dir = self.root / "source vehicle"
        output_dir = self.root / "output vehicle"
        source_dir.mkdir()
        (source_dir / "car.dx").write_bytes(self.fixture)
        rev135 = upgrade_dx_131_to_135(self.fixture)
        (source_dir / "complete.dx").write_bytes(rev135)
        (source_dir / "wheel.dx").write_bytes(self.fixture)
        (source_dir / "body.dxt").write_bytes(b"texture bytes stay outside package")
        (source_dir / "unrelated.gxm").write_bytes(b"ignored")
        source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in source_dir.iterdir() if p.is_file()}

        result = self.run_cli("--vehicle-dir", str(source_dir), "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(p.name for p in output_dir.iterdir()),
                         ["car.dx", "complete.dx", "manifest.json", "wheel.dx"])
        self.assertEqual((output_dir / "car.dx").read_bytes(), rev135)
        self.assertEqual((output_dir / "complete.dx").read_bytes(), rev135)
        self.assertEqual((output_dir / "wheel.dx").read_bytes(), rev135)
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["converted_or_copied_dx_count"], 3)
        by_role = {entry["role"]: entry for entry in manifest["dx_files"]}
        self.assertEqual(by_role["car"]["status"], "PASS")
        self.assertEqual(by_role["complete"]["status"], "already_rev135_copied")
        self.assertEqual(by_role["complete"]["source_sha256"], source_hashes["complete.dx"])
        self.assertEqual(
            manifest["runtime_evidence_profile"]["this_package_runtime_status"],
            "NOT_ASSESSED_BY_CONVERTER",
        )
        self.assertFalse((output_dir / "body.dxt").exists())
        self.assertEqual(source_hashes,
                         {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in source_dir.iterdir() if p.is_file()})

    def test_directory_mode_copies_existing_rev135_order_divergence_unchanged(self):
        source_dir = self.root / "source"
        output_dir = self.root / "output"
        source_dir.mkdir()
        original = _rev135_reordered_fixture()
        (source_dir / "car.dx").write_bytes(original)

        result = self.run_cli("--vehicle-dir", str(source_dir), "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((output_dir / "car.dx").read_bytes(), original)
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        entry = manifest["dx_files"][0]
        self.assertEqual(entry["status"], "already_rev135_copied")
        self.assertEqual(
            entry["existing_rev135_validation"]["status"],
            "VALID_WITH_ORDERING_DIVERGENCE",
        )

    def test_directory_mode_refuses_invalid_existing_rev135(self):
        source_dir = self.root / "source"
        output_dir = self.root / "output"
        source_dir.mkdir()
        data = bytearray(_rev135_reordered_fixture())
        index_offset, _ = _index_array_range(data)
        struct.pack_into("<H", data, index_offset, 4)
        (source_dir / "car.dx").write_bytes(data)

        result = self.run_cli("--vehicle-dir", str(source_dir), "--output-dir", str(output_dir))

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output_dir.exists())
        self.assertEqual(list(self.root.glob(".output.staging-*")), [])

    def test_force_report_failure_never_leaves_stale_sidecar(self):
        source = self.root / "input.dx"
        output = self.root / "output.dx"
        report = self.root / "output.dx.report.json"
        source.write_bytes(self.fixture)
        output.write_bytes(b"old output")
        report.write_text('{"status":"OLD"}', encoding="utf-8")
        args = argparse.Namespace(
            input_dx=source,
            output=output,
            vehicle_dir=None,
            output_dir=None,
            report=None,
            force=True,
        )
        parser = argparse.ArgumentParser()
        original_install = CLI_MODULE._install_temp

        def fail_report(temp_path, target_path, *, overwrite):
            if target_path == report:
                raise OSError("synthetic report install failure")
            return original_install(temp_path, target_path, overwrite=overwrite)

        with mock.patch.object(CLI_MODULE, "_install_temp", side_effect=fail_report):
            with self.assertRaisesRegex(OSError, "previous report was removed"):
                CLI_MODULE._single_file(args, parser)

        self.assertFalse(report.exists())
        self.assertEqual(output.read_bytes(), upgrade_dx_131_to_135(self.fixture))
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_directory_conversion_failure_leaves_no_final_or_staging_package(self):
        source_dir = self.root / "source"
        output_dir = self.root / "output"
        source_dir.mkdir()
        (source_dir / "car.dx").write_bytes(self.fixture)
        unsupported = bytearray(self.fixture)
        unsupported[4:8] = (129).to_bytes(4, "little")
        (source_dir / "wheel.dx").write_bytes(unsupported)

        result = self.run_cli("--vehicle-dir", str(source_dir), "--output-dir", str(output_dir))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported DX revision 129", result.stderr)
        self.assertFalse(output_dir.exists())
        self.assertEqual(list(self.root.glob(".output.staging-*")), [])

    def test_directory_mode_refuses_existing_output_directory(self):
        source_dir = self.root / "source"
        output_dir = self.root / "output"
        source_dir.mkdir()
        (source_dir / "car.dx").write_bytes(self.fixture)
        output_dir.mkdir()
        sentinel = output_dir / "keep.txt"
        sentinel.write_text("preserve", encoding="utf-8")

        result = self.run_cli("--vehicle-dir", str(source_dir), "--output-dir", str(output_dir))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output directory already exists", result.stderr)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_directory_mode_rejects_empty_role_set(self):
        source_dir = self.root / "empty"
        output_dir = self.root / "output"
        source_dir.mkdir()
        (source_dir / "readme.txt").write_text("not a DX", encoding="utf-8")

        result = self.run_cli("--vehicle-dir", str(source_dir), "--output-dir", str(output_dir))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contains none of car.dx", result.stderr)
        self.assertFalse(output_dir.exists())

    def test_atomic_write_failure_does_not_leave_partial_output_or_temp_file(self):
        output = self.root / "atomic.dx"
        with mock.patch.object(CLI_MODULE.os, "fsync", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError):
                CLI_MODULE._write_atomic(output, b"complete candidate", overwrite=False)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".atomic.dx.*.tmp")), [])

    def test_failed_no_replace_install_preserves_existing_file(self):
        output = self.root / "existing.dx"
        output.write_bytes(b"original")
        with self.assertRaises(FileExistsError):
            CLI_MODULE._write_atomic(output, b"replacement", overwrite=False)
        self.assertEqual(output.read_bytes(), b"original")
        self.assertEqual(list(self.root.glob(".existing.dx.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
