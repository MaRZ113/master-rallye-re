from __future__ import annotations

import contextlib
import io
import itertools
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/runtime"))
import broker_observatory as core
import mr_observe as observe
from observatory_build_profiles import ObservatoryBuildProfile
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

    def test_process_candidate_retains_locally_audited_profile_without_exact_sha_lookup(self):
        profile=replace(core.RETAIL_PRISTINE,sha256="a"*64,profile_origin="locally_audited",
                        exact_profile_id=None,compatibility_family="retail-broker-v1")
        process=observe.ProcessCandidate(9,Path("MRallye.exe"),profile.sha256,profile)
        self.assertIs(process.profile,profile)
        self.assertEqual(process.profile.profile_origin,"locally_audited")

    def test_internal_verifier_uses_family_resolver(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"MRallye.exe";path.write_bytes(b"family fixture")
            expected=replace(core.RETAIL_PRISTINE,sha256="a"*64,profile_origin="locally_audited",
                             exact_profile_id=None)
            with patch.object(observe,"PORTABLE",False), \
                 patch.object(observe,"resolve_executable_profile",return_value=expected) as resolve:
                self.assertIs(observe.verify_executable(path),expected)
            resolve.assert_called_once()

    def test_exe_option_binds_live_process_to_same_resolved_profile_and_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"MRallye.exe";path.write_bytes(b"family fixture")
            profile=replace(core.RETAIL_PRISTINE,sha256="a"*64,profile_origin="locally_audited",
                            exact_profile_id=None)
            matching=observe.ProcessCandidate(1,path,profile.sha256)
            other=observe.ProcessCandidate(2,Path(folder)/"other"/"MRallye.exe",profile.sha256)
            args=observe.build_parser().parse_args(["--exe",str(path),"status"])
            with patch.object(observe,"verify_executable",return_value=profile), \
                 patch.object(observe,"discover_processes",return_value=([matching,other],[])), \
                 patch.object(observe,"status") as show:
                self.assertEqual(observe.execute(args,Path(folder),{}),0)
            selected=show.call_args.args[1]
            self.assertEqual(selected.pid,1)
            self.assertIs(selected.profile,profile)

    def test_exe_option_binds_live_process_to_same_resolved_profile_and_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"MRallye.exe";path.write_bytes(b"family fixture")
            profile=replace(core.RETAIL_PRISTINE,sha256="a"*64,profile_origin="locally_audited",
                            exact_profile_id=None)
            matching=observe.ProcessCandidate(1,path,profile.sha256)
            other=observe.ProcessCandidate(2,Path(folder)/"other"/"MRallye.exe",profile.sha256)
            args=observe.build_parser().parse_args(["--exe",str(path),"status"])
            with patch.object(observe,"verify_executable",return_value=profile), \
                 patch.object(observe,"discover_processes",return_value=([matching,other],[])), \
                 patch.object(observe,"status") as show:
                self.assertEqual(observe.execute(args,Path(folder),{}),0)
            selected=show.call_args.args[1]
            self.assertEqual(selected.pid,1)
            self.assertIs(selected.profile,profile)

    def test_degraded_process_can_recover_but_cannot_request_native_dump(self):
        profile=replace(core.RETAIL_PRISTINE,sha256="a"*64,profile_origin="locally_audited",
                        exact_profile_id=None,capabilities={"broker_read":True,"native_dump":False,
                        "open_broker_editor":False,"post_results_native_dump_safe":None})
        process=observe.ProcessCandidate(9,Path("MRallye.exe"),profile.sha256,profile)
        raw=dump([row("Existing/Value","1")])
        recovered,source=observe.capture_recovery(process,read_fn=lambda _pid:(raw,{}))
        self.assertEqual(recovered,raw)
        self.assertEqual(source["dump_dispatch"],"not_sent")
        ensure=Mock();dispatch=Mock()
        with self.assertRaisesRegex(core.ObservatoryError,"Native Dump request is disabled"):
            observe.capture_fresh(process,ensure_fn=ensure,dump_fn=dispatch,read_fn=lambda _pid:(raw,{}))
        ensure.assert_not_called();dispatch.assert_not_called()

    def test_status_reports_independent_capabilities(self):
        profile=replace(core.RETAIL_PRISTINE,sha256="a"*64,profile_origin="locally_audited",
                        exact_profile_id=None,capabilities={"broker_read":True,"native_dump":False,
                        "open_broker_editor":False,"flow_builder":False,
                        "post_results_native_dump_safe":None,"legacy_loading_attract_present":False})
        process=observe.ProcessCandidate(9,Path("MRallye.exe"),profile.sha256,profile)
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(observe.core,"capture_debug_buffer",return_value=(b"",{"debug_buffer_used_bytes":0,"debug_buffer_capacity_bytes":1})) as read, \
             contextlib.redirect_stdout(io.StringIO()) as out:
            observe.status(Path(folder),process)
        rendered=out.getvalue()
        self.assertIn("Broker read          YES",rendered)
        self.assertIn("Native Dump          NO",rendered)
        self.assertIn("Legacy Attract      NEUTRALIZED",rendered)
        read.assert_called_once_with(process.pid,profile)


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

    def test_zero_post_dispatch_wait_has_no_retry(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        send = Mock(return_value=observe.commands.DumpDispatchOutcome.COMPLETED_SYNCHRONOUSLY)
        with patch.object(observe.time, "sleep"), self.assertRaises(core.ObservatoryError):
            observe.capture_fresh(process, timeout=0, read_fn=lambda _: (b"old", {}),
                                  ensure_fn=lambda *_: "broker", dump_fn=send)
        send.assert_called_once_with("broker")

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
        sent = Mock(return_value=observe.commands.DumpDispatchOutcome.COMPLETED_SYNCHRONOUSLY)
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        raw, source = observe.capture_fresh(process, read_fn=lambda _: next(reads),
                                           ensure_fn=lambda *_: "broker", dump_fn=sent)
        sent.assert_called_once_with("broker")
        self.assertEqual(raw, new)
        self.assertEqual(source["baseline_byte_length"], len(old))
        self.assertEqual(source["dump_dispatch"], "completed_synchronously")
        with tempfile.TemporaryDirectory() as folder:
            path = observe.store_capture(Path(folder), raw, source, "synchronous")
            self.assertEqual(core.load_snapshot(path)["source"]["dump_dispatch"], "completed_synchronously")
            self.assertEqual(observe.capture_history(Path(folder)), [path])

    def test_timeout_then_late_fresh_complete_dump_succeeds_once(self):
        old = b"synthetic baseline\n"
        new = old + dump([row("Test/X", "1")])
        reads = Mock(side_effect=[(old, {}), (old, {}), (new, {})])
        send = Mock(return_value=observe.commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN)
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        with patch.object(observe.time, "sleep"), \
             patch.object(observe.time, "monotonic", side_effect=itertools.count(step=0.25)), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            raw, source = observe.capture_fresh(process, timeout=1, read_fn=reads,
                                               ensure_fn=lambda *_: "broker", dump_fn=send)
        send.assert_called_once_with("broker")
        self.assertEqual(reads.call_count, 3)
        self.assertEqual(raw, new)
        self.assertIn("Broker Dump is still processing...", out.getvalue())
        self.assertIn("Fresh Broker Dump captured.", out.getvalue())
        self.assertNotIn("ERROR_TIMEOUT", out.getvalue())
        self.assertEqual(source["dump_dispatch"], "send_timeout_then_fresh_dump_observed")

    def test_timeout_then_incomplete_then_complete_publishes_provenance(self):
        old = dump([row("Test/X", "1")])
        new_dump = dump([row("Test/X", "2")])
        new = old + new_dump
        reads = Mock(side_effect=[(old, {}), (old + new_dump[:-10], {}), (new, {})])
        send = Mock(return_value=observe.commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN)
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        with tempfile.TemporaryDirectory() as folder, patch.object(observe.time, "sleep"), \
             patch.object(observe.time, "monotonic", side_effect=itertools.count(step=0.25)), \
             contextlib.redirect_stdout(io.StringIO()):
            raw, source = observe.capture_fresh(process, timeout=1, read_fn=reads,
                                               ensure_fn=lambda *_: "broker", dump_fn=send)
            path = observe.store_capture(Path(folder), raw, source, "timeout-recovery")
            snapshot = core.load_snapshot(path)
            self.assertEqual(path.with_suffix(".dump.bin").read_bytes(), new)
            self.assertEqual(snapshot["source"]["dump_dispatch"], "send_timeout_then_fresh_dump_observed")
            self.assertEqual(snapshot["source"]["dump_dispatch_win32_error"], 1460)
            self.assertEqual(snapshot["source"]["freshness"], "post_baseline_complete_dump_proven")
            self.assertEqual(snapshot["source"]["selected_block_offset"], len(old))
            self.assertEqual(observe.capture_history(Path(folder)), [path])
        send.assert_called_once_with("broker")
        self.assertEqual(reads.call_count, 3)

    def test_timeout_without_fresh_complete_dump_publishes_nothing(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        old = dump([row("Test/X", "1")])
        reads = Mock(side_effect=[(old, {})] + [(old + b"incomplete log\n", {})] * 3)
        send = Mock(return_value=observe.commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN)
        coordinator = observe.capture_fresh
        args = observe.build_parser().parse_args(["capture", "must-not-publish"])
        with tempfile.TemporaryDirectory() as folder, patch.object(observe.time, "sleep"), \
             patch.object(observe.time, "monotonic", side_effect=itertools.count(step=0.25)), \
             patch.object(observe, "discover_processes", return_value=([process], [])), \
             patch.object(observe, "capture_fresh", side_effect=lambda *a, **k: coordinator(
                 process, timeout=1, read_fn=reads, ensure_fn=lambda *_: "broker", dump_fn=send)), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(core.ObservatoryError, "timed out"):
            try:
                observe.execute(args, Path(folder), {})
            finally:
                self.assertEqual(list(Path(folder).iterdir()), [])
        send.assert_called_once_with("broker")
        self.assertEqual(reads.call_count, 4)

    def test_non_timeout_dispatch_error_aborts_before_polling_or_publication(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        reads = Mock(return_value=(b"baseline", {}))
        send = Mock(side_effect=PermissionError("Access denied"))
        coordinator = observe.capture_fresh
        args = observe.build_parser().parse_args(["capture", "error"])
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(observe, "discover_processes", return_value=([process], [])), \
             patch.object(observe, "capture_fresh", side_effect=lambda *a, **k: coordinator(
                 process, read_fn=reads, ensure_fn=lambda *_: "broker", dump_fn=send)), \
             self.assertRaises(PermissionError):
            try:
                observe.execute(args, Path(folder), {})
            finally:
                self.assertEqual(list(Path(folder).iterdir()), [])
        send.assert_called_once_with("broker")
        reads.assert_called_once_with(process.pid)  # Baseline only.

    def test_manual_dump_has_no_automatic_dispatch(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        old = b"baseline\n"
        new = old + dump([row("Test/X", "1")])
        reads = Mock(side_effect=[(old, {}), (new, {})])
        send = Mock()
        raw, source = observe.capture_fresh(process, manual=True, input_fn=lambda _: "",
                                           read_fn=reads, ensure_fn=lambda *_: "broker", dump_fn=send)
        send.assert_not_called()
        self.assertEqual(source["dump_dispatch"], "manual_original_menu")
        self.assertEqual(raw, new)


class PassiveRecoveryTests(unittest.TestCase):
    def test_recover_publishes_latest_complete_dump_and_full_buffer_without_commands(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        first = dump([row("Test/X", "1")])
        second = dump([row("Test/X", "2")])
        raw = b"earlier logs\n" + first + second + second[:-10]
        reader = Mock(return_value=(raw, {}))
        recovery = observe.capture_recovery
        args = observe.build_parser().parse_args(["recover", "salvaged-session"])
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(observe, "discover_processes", return_value=([process], [])), \
             patch.object(observe, "capture_recovery", side_effect=lambda p: recovery(p, read_fn=reader)), \
             patch.object(observe, "capture_fresh") as fresh, \
             patch.object(observe, "ensure_tool") as ensure, \
             patch.object(observe.commands, "send_tool_command") as opener, \
             patch.object(observe.commands, "send_broker_dump") as send, \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(observe.execute(args, Path(folder), {}), 0)
            history = observe.capture_history(Path(folder))
            self.assertEqual(len(history), 1)
            snapshot = core.load_snapshot(history[0])
            self.assertEqual(history[0].with_suffix(".dump.bin").read_bytes(), raw)
            self.assertEqual(snapshot["source"]["selected_block_offset"], len(b"earlier logs\n") + len(first))
            self.assertEqual(snapshot["entries"][0]["value_raw"], "2")
            self.assertEqual(snapshot["source"]["freshness"], "not_command_proven")
            self.assertEqual(snapshot["source"]["dump_dispatch"], "not_sent")
            self.assertEqual(snapshot["source"]["label"], "salvaged-session")
        self.assertIn("NOT command-proven", out.getvalue())
        reader.assert_called_once_with(process.pid)
        for operation in (fresh, ensure, opener, send):
            operation.assert_not_called()

    def test_recovery_without_complete_dump_publishes_nothing(self):
        process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)
        reader = Mock(return_value=(dump([row("Test/X", "1")])[:-10], {}))
        recovery = observe.capture_recovery
        args = observe.build_parser().parse_args(["recover"])
        self.assertEqual(args.label, "recovered")
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(observe, "discover_processes", return_value=([process], [])), \
             patch.object(observe, "capture_recovery", side_effect=lambda p: recovery(p, read_fn=reader)), \
             patch.object(observe.commands, "send_broker_dump") as send, \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(core.ObservatoryError):
            try:
                observe.execute(args, Path(folder), {})
            finally:
                self.assertEqual(list(Path(folder).iterdir()), [])
        send.assert_not_called()


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
