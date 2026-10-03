from __future__ import annotations
import hashlib
import ast
import io
import json
import subprocess
import sys
import tempfile
import unittest
import contextlib
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/runtime"))
import build_observatory_release as release
import mr_observe as observe
from test_broker_observatory import dump, row


class ObservatoryReleaseTests(unittest.TestCase):
    def test_unsupported_python_stops_before_runtime_imports(self):
        script = ROOT / "tools/runtime/mr_observe.py"
        ast.parse(script.read_text(encoding="utf-8"), feature_version=(3, 6))
        for version in ((3, 6), (3, 10)):
            result = subprocess.run([sys.executable, "-c",
                "import sys,runpy; sys.version_info=" + repr(version)
                + "; runpy.run_path(sys.argv[1], run_name='__main__')", str(script)],
                text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stderr.strip(),
                             "Master Rallye Observatory requires Python 3.11 or newer.")
            self.assertNotIn("Traceback", result.stderr)

    def test_launcher_checks_python_before_frontend(self):
        launcher = (ROOT / "tools/runtime/MRallye-Observatory.cmd").read_text()
        self.assertLess(launcher.index("sys.version_info >= (3, 11)"),
                        launcher.index("py -3 mr_observe.py"))

    def test_publication_stages_directly_in_output_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            files = {"release.zip": b"archive", "release.manifest.json": b"{}"}
            original_open = Path.open
            staged_parents = []
            def tracked_open(path, mode="r", *args, **kwargs):
                if mode == "xb":
                    staged_parents.append(path.parent)
                return original_open(path, mode, *args, **kwargs)
            with patch.object(Path, "open", tracked_open):
                release.publish_files(output, files)
            self.assertEqual(staged_parents, [output, output])
            self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, files)
            release.publish_files(output, {"release.zip": b"replacement"})
            self.assertEqual((output / "release.zip").read_bytes(), b"replacement")

    def test_publication_failure_cleans_staging_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            (output / "release.zip").write_bytes(b"existing")
            with patch.object(release.os, "fsync", side_effect=OSError("write failed")):
                with self.assertRaises(OSError):
                    release.publish_files(output, {"release.zip": b"new"})
            self.assertEqual(list(output.iterdir()), [output / "release.zip"])
            self.assertEqual((output / "release.zip").read_bytes(), b"existing")

    def payload(self):
        return release.collect_files(ROOT)

    def test_exact_allowlist_and_no_forbidden_contents(self):
        payload = self.payload()
        self.assertEqual(set(payload), set(release.FILES) | ({"LICENSE"} if (ROOT / "LICENSE").exists() else set()))
        release.reject_forbidden(payload)
        for data in payload.values():
            self.assertFalse(release.LOCAL_PATH.search(data.decode("utf-8")))

    def test_reject_forbidden_staged_file_classes(self):
        for name in ("MRallye.exe", "Data.sma", "DataGame/dev.xml", "capture.dump.bin",
                     "research-output/config.json", "personal/runtime-config.json", "scratch.gpr", "bundle.zip"):
            with self.assertRaises(ValueError):
                release.reject_forbidden([name])

    def test_unallowlisted_file_is_rejected_even_if_text(self):
        payload = self.payload()
        payload["extra.txt"] = b"unexpected"
        with self.assertRaises(ValueError):
            release.build_bytes(payload, "a" * 40)

    def test_archive_manifest_and_deterministic_bytes(self):
        payload = self.payload()
        raw, manifest = release.build_bytes(payload, "a" * 40)
        again, second = release.build_bytes(payload, "a" * 40)
        self.assertEqual(raw, again)
        self.assertEqual(manifest, second)
        self.assertEqual(manifest["archive_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(manifest["build_commit"], "a" * 40)
        self.assertEqual(manifest["python_requirement"], ">=3.11")
        self.assertEqual(json.loads(json.dumps(manifest)), manifest)
        self.assertFalse(release.LOCAL_PATH.search(json.dumps(manifest)))
        release.validate_release(raw, manifest)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            self.assertEqual(set(archive.namelist()), set(payload))
            for name in payload:
                self.assertEqual(archive.read(name), payload[name])

    def test_manifest_tamper_rejected(self):
        raw, manifest = release.build_bytes(self.payload(), "a" * 40)
        manifest["archive_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            release.validate_release(raw, manifest)

    def test_absolute_machine_path_rejected(self):
        payload = self.payload()
        payload["README.md"] += b"\nC:\\Users\\private\\config.json"
        with self.assertRaises(ValueError):
            release.build_bytes(payload, "a" * 40)

    def test_cli_refuses_forbidden_staged_file_before_collecting(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(release, "REPO", Path(folder)), \
             patch.object(release.subprocess, "check_output", return_value="MRallye.exe\n"), \
             patch.object(release, "collect_files") as collect, contextlib.redirect_stderr(io.StringIO()) as out:
            self.assertEqual(release.main([]), 2)
            self.assertIn("Forbidden", out.getvalue())
            collect.assert_not_called()
            self.assertFalse((Path(folder) / "dist").exists())

    def test_cli_refuses_dirty_release_inputs(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(release, "REPO", Path(folder)), \
             patch.object(release.subprocess, "check_output", side_effect=["", " M tools/runtime/mr_observe.py"]), \
             patch.object(release, "collect_files") as collect, contextlib.redirect_stderr(io.StringIO()) as out:
            self.assertEqual(release.main([]), 2)
            self.assertIn("Commit release inputs", out.getvalue())
            collect.assert_not_called()

    def test_portable_outside_repository_version_and_offline_history(self):
        raw, manifest = release.build_bytes(self.payload(), "a" * 40)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                archive.extractall(root)  # Names already checked against flat allowlist.
            captures = root / "observatory-data/captures"
            observe.store_capture(captures, dump([row("Test/X", "1")]), {}, "portable-before")
            observe.store_capture(captures, dump([row("Test/X", "2")]), {}, "portable-after")
            def run(*args):
                result = subprocess.run([sys.executable, str(root / "mr_observe.py"), *args],
                                        cwd=root, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout
            self.assertIn(release.VERSION, run("--version"))
            shown = run("show", "--last")
            self.assertIn("portable-after", shown)
            self.assertNotIn(str(root), shown)
            diff = run("diff", "--last")
            self.assertIn("portable-before", diff)
            self.assertIn("Value changed: 1", diff)
            self.assertIn("not selected", run("config", "show"))
