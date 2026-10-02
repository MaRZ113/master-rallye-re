from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/runtime"))
import broker_observatory as core
import mr_observe as observe
from test_broker_observatory import dump, row, parse_rows


class DiscoveryTests(unittest.TestCase):
    def candidate(self, pid):
        return observe.ProcessCandidate(pid, Path("MRallye.exe"), core.RETAIL_SHA256)

    def test_zero_and_one(self):
        self.assertIsNone(observe.select_process([]))
        candidate = self.candidate(7)
        self.assertIs(observe.select_process([candidate]), candidate)

    def test_multiple_never_silent(self):
        candidates = [self.candidate(1), self.candidate(2)]
        with self.assertRaises(core.ObservatoryError):
            observe.select_process(candidates)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(observe.select_process(candidates, input_fn=lambda _: "2").pid, 2)
            self.assertIsNone(observe.select_process(candidates, input_fn=lambda _: "0"))
            with self.assertRaises(core.ObservatoryError):
                observe.select_process(candidates, input_fn=lambda _: "3")

    def test_pid_override_must_be_supported(self):
        with self.assertRaises(core.ObservatoryError):
            observe.select_process([self.candidate(1)], pid=2)

    def test_wrong_executable_hash_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "MRallye.exe"
            path.write_bytes(b"synthetic")
            with patch.object(core, "RETAIL_SIZE", path.stat().st_size):
                with self.assertRaises(core.ObservatoryError):
                    observe.verify_executable(path)


class CaptureStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = dump([row("Synthetic/Value", "1")])
        self.now = datetime(2026, 10, 2, 22, 15, 30)

    def test_name_and_label_sanitizing(self):
        self.assertEqual(observe.capture_name(" race : grid / test ", self.now),
                         ("2026-10-02", "20261002-221530_race-grid-test"))
        self.assertEqual(observe.capture_name("...", self.now)[1], "20261002-221530_snapshot")
        self.assertNotIn("\\", observe.capture_name("a\\b", self.now)[1])

    def store(self, label="snapshot"):
        return observe.store_capture(self.root, self.raw, {"capture_kind": "synthetic"}, label, self.now)

    def test_pair_and_preserved_label(self):
        path = self.store(" race / sample ")
        snapshot = core.load_snapshot(path)
        self.assertEqual(path.parent.name, "2026-10-02")
        self.assertEqual(snapshot["source"]["label"], " race / sample ")
        self.assertEqual(path.with_suffix(".dump.bin").read_bytes(), self.raw)
        self.assertEqual(observe.capture_history(self.root), [path])

    def test_same_second_does_not_overwrite(self):
        before = self.store()
        original = before.read_bytes()
        after = self.store()
        self.assertNotEqual(before, after)
        self.assertEqual(before.read_bytes(), original)
        self.assertEqual(observe.last_two(self.root), (before, after))

    def test_zero_or_one_latest_diff_refused(self):
        with self.assertRaises(core.ObservatoryError):
            observe.last_two(self.root)
        self.store()
        with self.assertRaises(core.ObservatoryError):
            observe.last_two(self.root)

    def test_previous_uses_second_latest_and_requires_two(self):
        args = observe.build_parser().parse_args(["show", "--previous"])
        self.store()
        with self.assertRaises(core.ObservatoryError):
            observe.execute(args, self.root, {})
        expected = observe.capture_history(self.root)[0]
        self.store()
        with patch.object(observe, "show_capture") as show:
            observe.execute(args, self.root, {})
        show.assert_called_once_with(expected)

    def test_partial_corrupt_or_pending_not_latest(self):
        good = self.store()
        second = self.store()
        second.with_suffix(".dump.bin").write_bytes(b"broken")
        self.assertEqual(observe.capture_history(self.root), [good])
        good.with_suffix(".pending").touch()
        self.assertEqual(observe.capture_history(self.root), [])

    def test_original_flat_capture_is_indexed_without_rewriting(self):
        path = self.store()
        flat = self.root / path.name
        raw = path.with_suffix(".dump.bin")
        raw.rename(self.root / raw.name)
        path.rename(flat)
        original = flat.read_bytes()
        self.assertEqual(observe.capture_history(self.root), [flat])
        self.assertEqual(flat.read_bytes(), original)

    def test_interrupted_publish_cleans_pair(self):
        publish = observe._publish_new
        calls = 0
        def fail_second(temp, final):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return publish(temp, final)
        with patch.object(observe, "_publish_new", fail_second):
            with self.assertRaises(KeyboardInterrupt):
                self.store()
        self.assertEqual([p for p in self.root.rglob("*") if p.is_file()], [])

    def test_parse_failure_has_no_output(self):
        with self.assertRaises(core.ObservatoryError):
            observe.store_capture(self.root, b"incomplete", {}, "fail", self.now)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_cli_last_and_offline_status(self):
        self.store("before")
        self.store("after")
        args = observe.build_parser().parse_args(["diff", "--last", "--ignore-revision-only"])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(observe.execute(args, self.root, {}), 0)
            observe.status(self.root, None)
        self.assertIn("before", out.getvalue())
        self.assertIn("Captures: 2", out.getvalue())


class FreshDumpTests(unittest.TestCase):
    def test_already_open_editor_sends_no_open_command(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        target = observe.commands.TargetWindow(3, 123, process.image_path, process.sha256, "Broker Editor")
        with patch.object(observe.commands, "find_tool_windows", return_value=[target]), \
             patch.object(observe.commands, "send_tool_command") as send:
            self.assertEqual(observe.ensure_tool(process, "broker-editor"), target)
            send.assert_not_called()

    def test_dump_timeout_has_no_retry_or_output(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        with patch.object(observe.time, "sleep"), self.assertRaises(core.ObservatoryError):
            observe.capture_fresh(process, timeout=0, read_fn=lambda _: (b"old", {}),
                                  ensure_fn=lambda *_: "broker", dump_fn=lambda _: None)
    def test_old_dump_cannot_be_captured_as_fresh(self):
        raw = dump([row("Test/X", "1")])
        with self.assertRaises(core.ObservatoryError):
            observe.fresh_dump_snapshot(raw, raw + b"other log\n", {})

    def test_identical_new_dump_is_fresh(self):
        old = dump([row("Test/X", "1")])
        new = observe.fresh_dump_snapshot(old, old + old, {})
        self.assertEqual(new["source"]["selected_block_offset"], len(old))

    def test_reset_rejected_and_incomplete_new_rejected(self):
        old = b"baseline log\n"
        new = dump([row("Test/X", "1")])
        with self.assertRaises(core.ObservatoryError):
            observe.fresh_dump_snapshot(old, new, {})
        with self.assertRaises(core.ObservatoryError):
            observe.fresh_dump_snapshot(old, old + new[:-10], {})

    def test_capture_coordinator_calls_dump_once(self):
        old = b"synthetic baseline\n"
        new = old + dump([row("Test/X", "1")])
        reads = iter([(old, {}), (new, {})])
        sent = []
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        raw, source = observe.capture_fresh(process, read_fn=lambda _: next(reads),
                                           ensure_fn=lambda *_: "broker", dump_fn=sent.append)
        self.assertEqual(sent, ["broker"])
        self.assertEqual(raw, new)
        self.assertEqual(source["baseline_byte_length"], len(old))


class OfflineAnalysisTests(unittest.TestCase):
    def test_revision_only_is_semantic_and_opt_in(self):
        before = parse_rows([row("Arbitrary/Path", "1", revision=1)])
        after = parse_rows([row("Arbitrary/Path", "1", revision=2)])
        self.assertEqual(len(core.diff_snapshots(before, after)["events"]), 1)
        self.assertEqual(core.diff_snapshots(before, after, ignore_revision_only=True)["events"], [])
        after["entries"][0]["value_raw"] = "2"
        self.assertEqual(len(core.diff_snapshots(before, after, ignore_revision_only=True)["events"]), 1)

    def test_presets_filter_paths_not_claims(self):
        a = parse_rows([row("Car12", "1"), row("Carpet", "1"), row("Race/Car1/X", "1"), row("UI/X", "1")])
        b = parse_rows([row("Car12", "2"), row("Carpet", "2"), row("Race/Car1/X", "2"), row("UI/X", "2")])
        result = observe.filtered_diff(a, b, preset="race")
        self.assertEqual([e["path"] for e in result["events"]], ["Car12", "Race/Car1/X"])
        self.assertEqual(observe.filtered_diff(a, b, preset="persistence")["events"], [])
        b["entries"][0]["save_file"] = "OtherFile"
        report = observe.filtered_diff(a, b, preset="persistence")
        self.assertEqual(report["summary"], {"CHANGED": 1, "SAVE_FILE_CHANGED": 1})

    def test_persistence_duplicates_case_scope_and_special_names(self):
        snapshot = parse_rows([
            row("Same/X", "1", s=True, save_file="Vehicles"),
            row("Same/X", "2", o=True, scope="SCENE", save_file="vehicles"),
            row("Transient/X", "3", save_file="__NO_SAVE"),
            row("Sentinel/X", "4", ps=True, save_file="__NO_CHANGE", scope="USER 2"),
            row("Ignored/X", '"opaque"', type_name="XmlFilename", save_file="__IGNORE"),
            row("Data/X", "[Synthetic]", type_name="xmlData", continuation=("<Synthetic/>",)),
        ])
        report = core.persistence_report(snapshot)
        self.assertEqual(report["entry_count"], 6)
        names = [g["save_file"] for g in report["groups"]]
        self.assertIn("Vehicles", names)
        self.assertIn("vehicles", names)
        self.assertEqual(core.persistence_report(snapshot, save_file="Vehicles")["entry_count"], 1)
        self.assertEqual(core.persistence_report(snapshot, save_mode="playerstate", scope="USER")["entry_count"], 1)
        self.assertEqual(core.persistence_report(snapshot, save_mode="game")["entry_count"], 1)

    def test_report_accepts_unknown_type_metadata_without_relabeling(self):
        snapshot = parse_rows([row("Test/X", "1")])
        snapshot["entries"][0]["type"] = "UNKNOWN_TYPE"
        report = core.persistence_report(snapshot)
        self.assertEqual(report["groups"][0]["types"], {"UNKNOWN_TYPE": 1})
        self.assertIn("0x0C", report["limitation"])

    def test_config_missing_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            self.assertEqual(observe.load_config(path), {})
            path.write_text(json.dumps({"retail_exe": "local/MRallye.exe"}), encoding="utf-8")
            self.assertIn("retail_exe", observe.load_config(path))
            for text in ("[]", '{"unknown": "x"}', '{"retail_exe": 3}', "malformed"):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(core.ObservatoryError):
                    observe.load_config(path)

    def test_capture_root_bounded_and_no_writer_commands(self):
        args = observe.build_parser().parse_args(["status"])
        self.assertEqual(observe.capture_root_for(args, {}), observe.DEFAULT_CAPTURE_ROOT.resolve())
        args.capture_root = Path(tempfile.gettempdir())
        with self.assertRaises(core.ObservatoryError):
            observe.capture_root_for(args, {})
        for name in ("save-game", "save-options", "save-playerstate", "commit"):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                observe.build_parser().parse_args([name])

    def test_launcher_is_new_file_only_with_real_crlf(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(observe, "REPO", Path(folder)):
            path = Path(folder) / "research-output/launcher.cmd"
            with contextlib.redirect_stdout(io.StringIO()):
                observe.setup_launcher(path, None)
            raw = path.read_bytes()
            self.assertIn(b'\r\nsetlocal\r\n', raw)
            self.assertNotIn(b'\\r\\n', raw)
            self.assertIn(b'exit /b %observe_exit%', raw)
            with self.assertRaises(FileExistsError):
                observe.setup_launcher(path, None)

    def test_launcher_rejects_shell_expansion_paths(self):
        for value in ('path%VARIABLE%', 'path!VARIABLE!', 'path"quoted', 'path\nnext'):
            with self.assertRaises(core.ObservatoryError):
                observe._cmd_literal(value)


if __name__ == "__main__":
    unittest.main()
