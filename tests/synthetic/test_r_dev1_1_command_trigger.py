from __future__ import annotations

import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "tools" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

import dev_command_trigger as trigger


class DeveloperCommandTriggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target = trigger.TargetWindow(
            pid=123,
            hwnd=0x123456,
            image_path=Path("C:/disposable/MRallye.exe"),
            sha256=trigger.RETAIL_SHA256,
            title="Master Rallye",
        )

    def test_tool_allowlist_contains_only_the_two_reviewed_openers(self):
        self.assertEqual(
            trigger.TOOL_COMMANDS,
            {"flow-builder": 0x30, "broker-editor": 0x27},
        )
        self.assertNotIn("build-data", trigger.TOOL_COMMANDS)

    def test_main_window_signature_accepts_recovered_menu_tree(self):
        class FakeUser32:
            labels = {(10, 0): "&Game", (20, 0): "&Reset...", (20, 2): "E&xit"}

            def GetMenu(self, _hwnd):
                return 10

            def GetMenuItemCount(self, menu):
                return 1 if menu == 10 else 3

            def GetSubMenu(self, _menu, _position):
                return 20

            def GetMenuStringW(self, menu, position, buffer, _length, _flags):
                buffer.value = self.labels.get((menu, position), "")
                return len(buffer.value)

        self.assertTrue(trigger._has_expected_main_menu(FakeUser32(), 0x123456))

    def test_main_window_signature_rejects_an_editor_menu(self):
        class FakeUser32:
            labels = {(10, 0): "&File", (20, 0): "&Close", (20, 2): "&Help"}

            def GetMenu(self, _hwnd):
                return 10

            def GetMenuItemCount(self, menu):
                return 1 if menu == 10 else 3

            def GetSubMenu(self, _menu, _position):
                return 20

            def GetMenuStringW(self, menu, position, buffer, _length, _flags):
                buffer.value = self.labels.get((menu, position), "")
                return len(buffer.value)

        self.assertFalse(trigger._has_expected_main_menu(FakeUser32(), 0x123456))

    def test_dump_requires_exact_broker_menu_and_local_id(self):
        class FakeUser32:
            command = 2

            def GetMenu(self, hwnd):
                return 10

            def GetMenuItemCount(self, menu):
                return 6 if menu == 10 else 1

            def GetSubMenu(self, menu, position):
                return 20 if position == 4 else 0

            def GetMenuStringW(self, menu, position, buffer, length, flags):
                buffer.value = ["&File", "&Edit", "&Branch", "&View", "&Debug", "&Help"][position] if menu == 10 else "&Dump"
                return len(buffer.value)

            def GetMenuItemID(self, menu, position):
                return self.command

        user = FakeUser32()
        self.assertTrue(trigger._has_broker_menu(user, 123))
        user.command = 3
        self.assertFalse(trigger._has_broker_menu(user, 123))

    def test_dump_rejects_changed_or_ambiguous_window_before_send(self):
        for windows in ([], [self.target, self.target]):
            with patch.object(trigger, "find_tool_windows", return_value=windows), \
                 self.assertRaises(RuntimeError):
                trigger.send_broker_dump(self.target)

    def test_verified_dump_sends_only_local_command_two(self):
        fake = Mock()
        fake.SendMessageTimeoutW.return_value = 1
        with patch.object(trigger, "find_tool_windows", return_value=[self.target]), \
             patch("ctypes.WinDLL", return_value=fake, create=True), \
             patch.object(trigger, "_configure_user32"):
            trigger.send_broker_dump(self.target)
        self.assertEqual(fake.SendMessageTimeoutW.call_args.args[:4],
                         (self.target.hwnd, trigger.WM_COMMAND, 2, 0))
        self.assertEqual(fake.SendMessageTimeoutW.call_count, 1)

    def test_dump_timeout_is_not_retried(self):
        fake = Mock()
        fake.SendMessageTimeoutW.return_value = 0
        with patch.object(trigger, "find_tool_windows", return_value=[self.target]), \
             patch("ctypes.WinDLL", return_value=fake, create=True), \
             patch.object(trigger, "_configure_user32"), self.assertRaises(RuntimeError):
            trigger.send_broker_dump(self.target)
        self.assertEqual(fake.SendMessageTimeoutW.call_count, 1)

    def test_unsupported_tool_is_rejected_by_argument_parser(self):
        with self.assertRaises(SystemExit):
            trigger.main(["--tool", "build-data"], find_targets=lambda: [])

    def test_default_is_dry_run_and_sends_nothing(self):
        sent = []
        result = trigger.main(
            ["--tool", "flow-builder"],
            find_targets=lambda: [self.target],
            send_command=lambda target, tool: sent.append((target, tool)),
        )
        self.assertEqual(result, 0)
        self.assertEqual(sent, [])

    def test_nonmatching_typed_confirmation_sends_nothing(self):
        sent = []
        result = trigger.main(
            ["--tool", "flow-builder", "--confirm"],
            find_targets=lambda: [self.target],
            send_command=lambda target, tool: sent.append((target, tool)),
            input_fn=lambda _prompt: "yes",
        )
        self.assertEqual(result, 3)
        self.assertEqual(sent, [])

    def test_exact_confirmation_sends_only_the_allowlisted_target(self):
        sent = []
        result = trigger.main(
            ["--tool", "flow-builder", "--confirm"],
            find_targets=lambda: [self.target],
            send_command=lambda target, tool: sent.append((target, tool)),
            input_fn=lambda _prompt: trigger.CONFIRM_PHRASE,
        )
        self.assertEqual(result, 0)
        self.assertEqual(sent, [(self.target, "flow-builder")])

    def test_broker_editor_requires_its_stronger_confirmation(self):
        sent = []
        result = trigger.main(
            ["--tool", "broker-editor", "--confirm"],
            find_targets=lambda: [self.target],
            send_command=lambda target, tool: sent.append((target, tool)),
            input_fn=lambda _prompt: trigger.CONFIRM_PHRASE,
        )
        self.assertEqual(result, 3)
        self.assertEqual(sent, [])

    def test_broker_editor_exact_confirmation_sends_only_its_allowlisted_command(self):
        sent = []
        result = trigger.main(
            ["--tool", "broker-editor", "--confirm"],
            find_targets=lambda: [self.target],
            send_command=lambda target, tool: sent.append((target, tool)),
            input_fn=lambda _prompt: trigger.CONFIRM_PHRASES["broker-editor"],
        )
        self.assertEqual(result, 0)
        self.assertEqual(sent, [(self.target, "broker-editor")])

    def test_ambiguous_targets_refuse_to_send(self):
        sent = []
        result = trigger.main(
            ["--tool", "flow-builder", "--confirm"],
            find_targets=lambda: [self.target, self.target],
            send_command=lambda target, tool: sent.append((target, tool)),
            input_fn=lambda _prompt: trigger.CONFIRM_PHRASE,
        )
        self.assertEqual(result, 2)
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
