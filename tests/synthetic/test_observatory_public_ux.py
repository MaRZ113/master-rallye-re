from __future__ import annotations
import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/runtime"))
import mr_observe as observe
import broker_observatory as core
from observatory_version import VERSION, TOOL_NAME
from test_broker_observatory import dump, row, parse_rows


class PublicUXTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(observe, "VERBOSE", False).start()
        patch.object(observe, "DEBUG", False).start()
        self.process = observe.ProcessCandidate(3, Path("MRallye.exe"), core.RETAIL_SHA256)

    def test_normal_timeout_has_no_error_code_but_keeps_provenance(self):
        self.check_timeout(False)

    def test_verbose_timeout_includes_details(self):
        self.check_timeout(True)

    def test_debug_enables_timeout_details(self):
        args = observe.build_parser().parse_args(["--debug", "capture"])
        self.assertTrue(args.debug)
        with patch.object(observe, "capture_root_for", side_effect=RuntimeError("synthetic failure")), \
             contextlib.redirect_stderr(io.StringIO()) as out:
            self.assertEqual(observe.main(["--debug", "capture"]), 2)
        self.assertIn("Traceback", out.getvalue())
        self.assertTrue(observe.VERBOSE)

    def check_timeout(self, verbose):
        old = b"baseline\n"
        new = old + dump([row("Test/X", "1")])
        reads = iter([(old, {}), (new, {})])
        send = Mock(return_value=observe.commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN)
        with patch.object(observe, "VERBOSE", verbose), contextlib.redirect_stdout(io.StringIO()) as out:
            raw, source = observe.capture_fresh(self.process, read_fn=lambda _: next(reads),
                ensure_fn=lambda *_: "broker", dump_fn=send)
        self.assertIn("Broker Dump is still processing...", out.getvalue())
        self.assertIn("Waiting for a fresh complete dump.", out.getvalue())
        self.assertIn("Fresh Broker Dump captured.", out.getvalue())
        self.assertEqual("1460" in out.getvalue(), verbose)
        self.assertEqual("ERROR_TIMEOUT" in out.getvalue(), verbose)
        self.assertEqual(source["dump_dispatch_win32_error"], 1460)
        self.assertEqual(raw, new)
        send.assert_called_once_with("broker")

    def test_unsupported_exe_message_and_detailed_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "MRallye.exe"
            path.write_bytes(b"synthetic unsupported exe")
            with self.assertRaises(observe.UserError) as caught:
                observe.verify_executable(path)
        with contextlib.redirect_stderr(io.StringIO()) as out:
            observe.report_error(caught.exception)
        self.assertIn("Unsupported Master Rallye executable", out.getvalue())
        self.assertIn(f"Observatory {VERSION} currently supports pristine retail only", out.getvalue())
        self.assertNotIn(core.RETAIL_SHA256, out.getvalue())
        with patch.object(observe, "VERBOSE", True), contextlib.redirect_stderr(io.StringIO()) as detail:
            observe.report_error(caught.exception)
        self.assertIn(core.RETAIL_SHA256, detail.getvalue())

    def test_version_without_process_access(self):
        with patch.object(observe, "discover_processes") as discover, \
             contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit) as exit:
            observe.main(["--version"])
        self.assertEqual(exit.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), f"{TOOL_NAME} {VERSION}")
        discover.assert_not_called()

    def test_first_run_shows_three_simple_choices(self):
        args = observe.build_parser().parse_args([])
        with patch.object(observe, "discover_processes", return_value=([], [])), \
             patch("builtins.input", return_value="0"), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertFalse(observe.first_run(args, {}))
        for text in ("Master Rallye was not found", "1. Select Master Rallye installation",
                     "2. Wait for manually launched game", "0. Exit"):
            self.assertIn(text, out.getvalue())

    def test_config_change_clear_and_show_without_manual_json(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(observe, "REPO", Path(folder)), \
             patch.object(observe, "verify_executable"), contextlib.redirect_stdout(io.StringIO()):
            path = Path(folder) / "research-output/config.json"
            config = {}
            exe = Path(folder) / "game/MRallye.exe"
            observe.configure_install(path, config, exe)
            self.assertEqual(observe.load_config(path)["retail_exe"], str(exe.resolve()))
            args = observe.build_parser().parse_args(["config", "clear"])
            args.config = path
            observe.config_action(args, config)
            self.assertEqual(observe.load_config(path), {})
            self.assertEqual(config, {})

    def test_corrupt_config_cli_refuses_without_traceback_and_offers_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "broken.json"
            path.write_text("broken")
            with contextlib.redirect_stderr(io.StringIO()) as out:
                self.assertEqual(observe.main(["--config", str(path), "show", "--last"]), 2)
            self.assertIn("config reset", out.getvalue())
            self.assertNotIn("Traceback", out.getvalue())

    def test_corrupt_config_interactive_reset_then_exit(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(observe, "REPO", Path(folder)), \
             patch.object(observe, "discover_processes", return_value=([], [])):
            path = Path(folder) / "research-output/config.json"
            path.parent.mkdir()
            path.write_text("broken")
            with patch("builtins.input", side_effect=["r", "0"]), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(observe.main(["--config", str(path), "--capture-root", str(path.parent / "captures")]), 0)
            self.assertEqual(json.loads(path.read_text()), {})
            self.assertIn("Local configuration is corrupt", out.getvalue())

    def test_explicit_config_reset_can_handle_corruption(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(observe, "REPO", Path(folder)), \
             contextlib.redirect_stdout(io.StringIO()):
            path = Path(folder) / "research-output/config.json"
            path.parent.mkdir()
            path.write_text("broken")
            self.assertEqual(observe.main(["--config", str(path), "config", "reset"]), 0)
            self.assertEqual(json.loads(path.read_text()), {})

    def test_compact_status_hides_hash_and_detailed_status_shows_it(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(observe.commands, "find_tool_windows", return_value=[]), \
             patch.object(core, "capture_debug_buffer", return_value=(b"", {
                 "debug_buffer_used_bytes": 5_000_000, "debug_buffer_capacity_bytes": 8_000_000})):
            with contextlib.redirect_stdout(io.StringIO()) as normal:
                observe.status(Path(folder), self.process)
            self.assertIn("Retail verified", normal.getvalue())
            self.assertNotIn(core.RETAIL_SHA256, normal.getvalue())
            with contextlib.redirect_stdout(io.StringIO()) as detail:
                observe.status(Path(folder), self.process, detailed=True)
            self.assertIn(core.RETAIL_SHA256, detail.getvalue())

    def test_diff_labels_times_and_counts(self):
        left = parse_rows([row("Test/X", "1", revision=1)])
        right = parse_rows([row("Test/X", "1", revision=2)])
        left["source"]["label"], right["source"]["label"] = "before", "after"
        with contextlib.redirect_stdout(io.StringIO()) as out:
            observe.print_diff(observe.filtered_diff(left, right), left, right)
        self.assertIn("Snapshot A: before", out.getvalue())
        self.assertIn("Snapshot B: after", out.getvalue())
        self.assertIn("Revision-only: 1", out.getvalue())

    def test_tool_version_added_but_legacy_schema_still_loads(self):
        snapshot = parse_rows([row("Test/X", "1")])
        self.assertEqual(snapshot["tool_version"], VERSION)
        del snapshot["tool_version"]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "legacy.json"
            core.write_json(path, snapshot)
            self.assertEqual(core.load_snapshot(path)["schema_version"], 1)

    def test_same_second_capture_order_does_not_depend_on_label(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(core, "datetime") as clock:
            clock.now.side_effect = [datetime(2026, 10, 3, 0, 0, 0, 100, timezone.utc),
                                     datetime(2026, 10, 3, 0, 0, 0, 200, timezone.utc)]
            first = observe.store_capture(Path(folder), dump([row("Test/X", "1")]), {}, "z-before")
            second = observe.store_capture(Path(folder), dump([row("Test/X", "2")]), {}, "a-after")
            self.assertEqual(observe.capture_history(Path(folder)), [first, second])

    def test_corrupt_pair_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = observe.store_capture(Path(folder), dump([row("Test/X", "1")]), {}, "pair")
            path.with_suffix(".dump.bin").write_bytes(b"corrupt")
            with self.assertRaises(observe.UserError):
                observe.checked_snapshot(path)
            self.assertEqual(observe.capture_history(Path(folder)), [])

    def test_expected_error_has_action_no_traceback(self):
        with contextlib.redirect_stderr(io.StringIO()) as out:
            observe.report_error(PermissionError("synthetic denied"))
        self.assertIn("writable", out.getvalue())
        self.assertNotIn("Traceback", out.getvalue())
