"""Narrow, confirmation-gated opener for two retail developer tools.

The CLI sends one allowlisted opener WM_COMMAND to a verified retail main
window. The reusable Broker Dump helper sends only the original local command
2 to a separately verified Broker window. No arbitrary IDs, memory writes,
injection, editing or persistence commands are exposed.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence
from observatory_build_profiles import RETAIL_PRISTINE, profile_for_file


RETAIL_SHA256 = RETAIL_PRISTINE.sha256  # backwards-compatible constant
TOOL_COMMANDS = {"flow-builder": 0x30, "broker-editor": 0x27}
SAFETY = {
    "flow-builder": "SAFE_OPEN_CANDIDATE (open only), medium-high confidence",
    "broker-editor": (
        "LOW_RISK_BUT_METADATA_MUTATION (open only); registers two reserved "
        "SaveFile names in shared in-memory metadata"
    ),
}
CONFIRM_PHRASES = {
    "flow-builder": "OPEN FLOW BUILDER",
    "broker-editor": "OPEN BROKER EDITOR WITH METADATA REGISTRATION",
}
# Kept as a compatibility name for existing Flow Builder-only callers/tests.
CONFIRM_PHRASE = CONFIRM_PHRASES["flow-builder"]
WM_COMMAND = 0x0111
SMTO_ABORTIFHUNG = 0x0002
ERROR_TIMEOUT = 1460
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
MF_BYPOSITION = 0x0400


@dataclass(frozen=True)
class TargetWindow:
    pid: int
    hwnd: int
    image_path: Path
    sha256: str
    title: str
    profile: object | None = None


class DumpDispatchOutcome(str, Enum):
    COMPLETED_SYNCHRONOUSLY = "completed_synchronously"
    TIMEOUT_COMPLETION_UNCERTAIN = "send_timeout_completion_uncertain"


class OpenOutcome(str, Enum):
    COMPLETED = "OPEN_COMPLETED"
    UNCERTAIN = "OPEN_TIMEOUT_COMPLETION_UNKNOWN"
    FAILED = "OPEN_FAILED"
    LATE = "OPENED_LATE"
    INVALIDATED = "TARGET_INVALIDATED"


@dataclass(frozen=True)
class OpenDispatch:
    completed: bool
    win32_error: int
    elapsed_ms: float


@dataclass(frozen=True)
class OpenReport:
    outcome: OpenOutcome
    command: int
    pid: int
    hwnd: int
    win32_error: int
    elapsed_ms: float
    process_alive: bool | None
    broker_hwnd: int | None
    reason: str
    command_count: int = 1
    dump_sent: bool = False

    def json(self) -> str:
        from dataclasses import asdict
        return json.dumps(asdict(self), sort_keys=True)


class ToolOpenError(RuntimeError):
    def __init__(self, report: OpenReport):
        self.report = report
        if report.outcome == OpenOutcome.UNCERTAIN:
            detail = "Broker Editor open timed out; native command completion is uncertain; no retry was sent."
        else:
            detail = f"Tool open: {report.outcome.value}; {report.reason}; no retry was sent."
        super().__init__(f"{detail} PID={report.pid}, HWND=0x{report.hwnd:X}, "
                         f"WM_COMMAND=0x{report.command:X}, Win32={report.win32_error}, "
                         f"elapsed={report.elapsed_ms:.0f}ms, alive={report.process_alive}, "
                         f"Broker HWND={report.broker_hwnd}. Dump was not sent.")


def target_status(target: TargetWindow) -> tuple[bool | None, bool]:
    """Bounded kernel/user queries only; never sends a message to the target."""
    import ctypes
    from ctypes import wintypes
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    _configure_user32(user, ctypes)
    _configure_kernel32(kernel, ctypes)
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, target.pid)
    alive = None
    if handle:
        try:
            code = wintypes.DWORD()
            if kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                alive = code.value == 259
        finally:
            kernel.CloseHandle(handle)
    pid = wintypes.DWORD()
    title = ctypes.create_unicode_buffer(512)
    valid = bool(user.IsWindow(target.hwnd))
    if valid:
        user.GetWindowThreadProcessId(target.hwnd, ctypes.byref(pid))
        user.GetWindowTextW(target.hwnd, title, len(title))
        valid = pid.value == target.pid and title.value == target.title == "Master Rallye"
    return alive, valid


def open_tool_once(target: TargetWindow, tool: str, *, grace: float = 3.0,
                   dispatch=None, discover=None, status=None, clock=None, sleep=None):
    """One allowlisted dispatch, then bounded discovery; never sends Dump or retries."""
    if tool not in TOOL_COMMANDS or not math.isfinite(grace) or not 0 <= grace <= 5:
        raise ValueError("Invalid opener or discovery grace")
    dispatch = dispatch or send_tool_command
    discover = discover or find_tool_windows
    status = status or target_status
    clock = clock or time.monotonic
    sleep = sleep or time.sleep
    started = clock()
    sent = dispatch(target, tool)
    alive, valid = status(target)
    def report(outcome, window=None, reason=""):
        return OpenReport(outcome, TOOL_COMMANDS[tool], target.pid, target.hwnd,
                          sent.win32_error, max(sent.elapsed_ms, (clock()-started)*1000), alive,
                          window.hwnd if window else None, reason)
    if not valid or alive is False:
        return report(OpenOutcome.INVALIDATED, reason="process_exited_or_main_identity_changed"), None
    if not sent.completed and sent.win32_error not in (0, ERROR_TIMEOUT):
        return report(OpenOutcome.FAILED, reason="dispatch_failed"), None
    deadline = clock()+grace
    for _ in range(52):
        alive, valid = status(target)
        if not valid or alive is False:
            return report(OpenOutcome.INVALIDATED, reason="process_exited_or_main_identity_changed"), None
        try:
            windows = discover(target.pid, tool, target.profile)
        except (OSError, RuntimeError) as exc:
            alive, valid = status(target)
            return report(OpenOutcome.INVALIDATED if alive is False or not valid else OpenOutcome.FAILED,
                          reason=f"tool_discovery_failed: {exc}"), None
        if len(windows) > 1:
            return report(OpenOutcome.FAILED, reason="ambiguous_tool_windows"), None
        if windows:
            window = windows[0]
            if window.pid != target.pid or window.sha256 != target.sha256:
                return report(OpenOutcome.INVALIDATED, reason="tool_owner_changed"), None
            return report(OpenOutcome.COMPLETED if sent.completed else OpenOutcome.LATE,
                          window, "verified_tool_window_found"), window
        if clock() >= deadline:
            break
        sleep(min(.1, max(0, deadline-clock())))
    return report(OpenOutcome.FAILED if sent.completed else OpenOutcome.UNCERTAIN,
                  reason="no_verified_tool_window_after_bounded_discovery"), None


def validate_retail_main_owner(read, base: int, hwnd: int) -> bool:
    """Exact retail singleton ownership, independent of renderer menu removal."""
    import struct
    def word(address):
        if not 0x10000 <= address <= 0x7ffffffb:
            raise ValueError("Invalid owner address")
        return struct.unpack('<I', read(address, 4))[0]
    try:
        if base != 0x400000 or not hwnd:
            return False
        renderer, owner = word(base+0x2f9cf0), word(base+0x2f9d80)
        return (word(renderer+0x20) == owner and word(owner) == base+0x29228c
                and word(owner+0x5c) == hwnd)
    except (ValueError, OSError, RuntimeError, struct.error):
        return False


def _verified_menu_less_main(pid: int, hwnd: int, profile) -> bool:
    if profile.sha256 != RETAIL_SHA256 or not profile.supports("open_broker_editor"):
        return False
    import ctypes
    import broker_observatory as core
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    core._configure_win32(kernel, ctypes)
    process, image = core._process_image_path(kernel, pid, ctypes)
    try:
        evidence = core._verify_live_capability_open(kernel, process, pid, image,
                                                    profile, "open_broker_editor", ctypes)
        return validate_retail_main_owner(
            lambda address, count: core._read_remote(kernel, process, address, count, ctypes),
            evidence['module_base'], hwnd)
    finally:
        kernel.CloseHandle(process)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run by default. The only supported actions are opening the "
            "retail Flow Builder or Broker Editor after strict identity checks."
        )
    )
    parser.add_argument("--tool", required=True, choices=sorted(TOOL_COMMANDS))
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="ask for the exact confirmation phrase and send the allowlisted command",
    )
    return parser


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified_profile(path: Path | None, expected_profile: object | None = None):
    if path is None or path.name.casefold() != "mrallye.exe":
        raise RuntimeError("Tool owner is not a known MRallye.exe build.")
    if expected_profile is not None:
        if (not path.is_file() or sha256_file(path) != expected_profile.sha256
                or path.stat().st_size != expected_profile.file_size):
            raise RuntimeError("Tool owner changed after the resolved profile was selected.")
        return expected_profile
    try:
        return profile_for_file(path)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc


def _menu_text(user32: object, menu: int, position: int) -> str:
    from ctypes import create_unicode_buffer

    buffer = create_unicode_buffer(256)
    user32.GetMenuStringW(menu, position, buffer, len(buffer), MF_BYPOSITION)
    return buffer.value.strip()


def _configure_user32(user32: object, ctypes: object) -> None:
    from ctypes import wintypes

    user32.GetMenu.argtypes = [wintypes.HWND]
    user32.GetMenu.restype = wintypes.HMENU
    user32.GetMenuItemCount.argtypes = [wintypes.HMENU]
    user32.GetMenuItemCount.restype = ctypes.c_int
    user32.GetSubMenu.argtypes = [wintypes.HMENU, ctypes.c_int]
    user32.GetSubMenu.restype = wintypes.HMENU
    user32.GetMenuStringW.argtypes = [
        wintypes.HMENU,
        wintypes.UINT,
        wintypes.LPWSTR,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.GetMenuStringW.restype = wintypes.UINT
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.SendMessageTimeoutW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    user32.SendMessageTimeoutW.restype = ctypes.c_ssize_t


def _configure_kernel32(kernel32: object, ctypes: object) -> None:
    from ctypes import wintypes

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL


def _has_expected_main_menu(user32: object, hwnd: int) -> bool:
    """Require the recovered Game → Reset / Exit menu signature."""
    menu = user32.GetMenu(hwnd)
    if not menu or user32.GetMenuItemCount(menu) < 1:
        return False
    root_text = _menu_text(user32, menu, 0).replace("&", "").strip().casefold()
    if root_text != "game":
        return False
    submenu = user32.GetSubMenu(menu, 0)
    if not submenu or user32.GetMenuItemCount(submenu) != 3:
        return False
    first = _menu_text(user32, submenu, 0).replace("&", "").casefold()
    last = _menu_text(user32, submenu, 2).replace("&", "").strip().casefold()
    return first.startswith("reset") and last == "exit"


def _image_for_pid(kernel32: object, pid: int) -> Path | None:
    from ctypes import byref, create_unicode_buffer
    from ctypes import wintypes

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        length = wintypes.DWORD(32768)
        buffer = create_unicode_buffer(length.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, byref(length)):
            return None
        return Path(buffer.value)
    finally:
        kernel32.CloseHandle(handle)


def find_retail_main_windows(profile_by_pid: dict[int, object] | None = None) -> list[TargetWindow]:
    """Enumerate visible windows with the verified retail main-menu signature."""
    if os.name != "nt":
        raise RuntimeError("This helper is Windows-only.")

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _configure_user32(user32, ctypes)
    _configure_kernel32(kernel32, ctypes)
    candidates: list[TargetWindow] = []

    enum_proc_type = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )

    @enum_proc_type
    def callback(hwnd: int, _lparam: int) -> bool:
        hwnd_value = int(hwnd)
        if not user32.IsWindowVisible(hwnd_value):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd_value, ctypes.byref(pid))
        image_path = _image_for_pid(kernel32, int(pid.value))
        if image_path is None:
            return True
        try:
            profile = verified_profile(image_path, (profile_by_pid or {}).get(int(pid.value)))
            image_hash = profile.sha256
        except (OSError, ValueError, RuntimeError):
            return True
        title_buffer = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd_value, title_buffer, len(title_buffer))
        if title_buffer.value != "Master Rallye":
            return True
        if not _has_expected_main_menu(user32, hwnd_value):
            try:
                if not _verified_menu_less_main(int(pid.value), hwnd_value, profile):
                    return True
            except (OSError, ValueError, RuntimeError):
                return True
        candidates.append(
            TargetWindow(
                pid=int(pid.value),
                hwnd=hwnd_value,
                image_path=image_path,
                sha256=image_hash,
                title=title_buffer.value,
                profile=profile,
            )
        )
        return True

    user32.EnumWindows(callback, 0)
    return candidates


def send_tool_command(target: TargetWindow, tool: str) -> OpenDispatch:
    """Revalidate the target and send one CLI-allowlisted tool command."""
    if os.name != "nt":
        raise RuntimeError("This helper is Windows-only.")
    if tool not in TOOL_COMMANDS:
        raise ValueError(f"Unsupported developer tool: {tool!r}")

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _configure_user32(user32, ctypes)
    _configure_kernel32(kernel32, ctypes)
    pid = wintypes.DWORD()
    if not user32.IsWindow(target.hwnd):
        raise RuntimeError("Target HWND no longer exists.")
    user32.GetWindowThreadProcessId(target.hwnd, ctypes.byref(pid))
    if int(pid.value) != target.pid:
        raise RuntimeError("Target HWND changed process identity.")
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(target.hwnd, title, len(title))
    if title.value != target.title or title.value != "Master Rallye":
        raise RuntimeError("Target main-window title changed identity.")
    image_path = _image_for_pid(kernel32, target.pid)
    profile = verified_profile(image_path, target.profile)
    capability = {"broker-editor": "open_broker_editor", "flow-builder": "flow_builder"}[tool]
    if profile.sha256 != target.sha256 or not profile.supports(capability):
        raise RuntimeError("Target identity changed or tool is not verified for this build.")
    if profile.runtime_anchors:
        from broker_observatory import verify_live_capability
        verify_live_capability(target.pid, profile, capability)
    if not user32.IsWindowVisible(target.hwnd) or not (
        _has_expected_main_menu(user32, target.hwnd)
        or _verified_menu_less_main(target.pid, target.hwnd, profile)
    ):
        raise RuntimeError("Target no longer has the verified Game → Reset / Exit menu.")

    result = ctypes.c_size_t()
    started = time.monotonic()
    ctypes.set_last_error(0)
    sent = user32.SendMessageTimeoutW(
        target.hwnd,
        WM_COMMAND,
        TOOL_COMMANDS[tool],
        0,
        SMTO_ABORTIFHUNG,
        3000,
        ctypes.byref(result),
    )
    error = 0 if sent else ctypes.get_last_error()
    return OpenDispatch(bool(sent), error, (time.monotonic()-started)*1000)


def find_tool_windows(pid: int, tool: str, resolved_profile: object | None = None) -> list[TargetWindow]:
    """Find a verified process's existing tool windows, without activating them.

    Broker identity additionally requires its recovered File and Debug menus;
    Flow Builder's title is status evidence only (no local actions are sent).
    """
    if os.name != "nt" or tool not in TOOL_COMMANDS:
        raise RuntimeError("Supported tool discovery requires Windows.")
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _configure_user32(user32, ctypes)
    _configure_kernel32(kernel32, ctypes)
    user32.GetMenuItemID.argtypes = [wintypes.HMENU, ctypes.c_int]
    user32.GetMenuItemID.restype = wintypes.UINT
    image = _image_for_pid(kernel32, pid)
    profile = verified_profile(image, resolved_profile)
    allowed = ((profile.supports("open_broker_editor") or profile.supports("native_dump"))
               if tool == "broker-editor" else profile.supports("flow_builder"))
    if not allowed:
        raise RuntimeError("Tool is not statically verified for this build.")
    result: list[TargetWindow] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(hwnd, _lparam):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value != pid:
            return True
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, len(title))
        expected = "Broker Editor" if tool == "broker-editor" else "Flow Builder"
        if title.value != expected:
            return True
        if tool == "broker-editor" and not _has_broker_menu(user32, hwnd):
            return True
        result.append(TargetWindow(pid, int(hwnd), image, profile.sha256, title.value, profile))
        return True

    user32.EnumWindows(callback, 0)
    return result


def _has_broker_menu(user32: object, hwnd: int) -> bool:
    menu = user32.GetMenu(hwnd)
    if not menu or user32.GetMenuItemCount(menu) != 6:
        return False
    titles = [_menu_text(user32, menu, i).replace("&", "").casefold() for i in range(6)]
    if titles != ["file", "edit", "branch", "view", "debug", "help"]:
        return False
    debug = user32.GetSubMenu(menu, 4)
    return bool(debug and user32.GetMenuItemCount(debug) == 1
                and _menu_text(user32, debug, 0).replace("&", "").casefold() == "dump"
                and user32.GetMenuItemID(debug, 0) == 2)


def send_broker_dump(target: TargetWindow) -> DumpDispatchOutcome:
    """Only Broker Editor local WM_COMMAND 2: original observational Dump.

    The recipient is freshly rediscovered by PID, exact title and menu layout.
    The main-window command ID 2 is never used. ERROR_TIMEOUT is not proof of
    failure: the window procedure may still append the original Dump. Return
    that uncertainty to the capture coordinator without retrying the message.
    """
    profile = target.profile or RETAIL_PRISTINE
    if not profile.supports("native_dump"):
        raise RuntimeError("Native Broker Dump request is disabled for this resolved build.")
    if profile.runtime_anchors:
        from broker_observatory import verify_live_capability
        verify_live_capability(target.pid, profile, "native_dump")
    matches = find_tool_windows(target.pid, "broker-editor", profile)
    if (len(matches) != 1 or matches[0].hwnd != target.hwnd
            or matches[0].sha256 != target.sha256 or matches[0].image_path != target.image_path
            or (matches[0].profile is not None and matches[0].profile.audit_fingerprint != profile.audit_fingerprint)):
        raise RuntimeError("Broker Editor identity changed or is ambiguous.")
    import ctypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    _configure_user32(user32, ctypes)
    result = ctypes.c_size_t()
    # SendMessageTimeout does not always set LastError on failure. Clear the
    # ctypes thread-local error copy before the use_last_error=True API call.
    ctypes.set_last_error(0)
    if not user32.SendMessageTimeoutW(target.hwnd, WM_COMMAND, 2, 0,
                                     SMTO_ABORTIFHUNG, 10000, ctypes.byref(result)):
        error = ctypes.get_last_error()
        if error == ERROR_TIMEOUT:
            return DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN
        if error:
            raise ctypes.WinError(error)
        raise RuntimeError("Broker Dump dispatch failed without Win32 error information; no retry was sent.")
    return DumpDispatchOutcome.COMPLETED_SYNCHRONOUSLY


def main(
    argv: Sequence[str] | None = None,
    *,
    find_targets: Callable[[], list[TargetWindow]] = find_retail_main_windows,
    send_command: Callable[[TargetWindow, str], None] = send_tool_command,
    input_fn: Callable[[str], str] = input,
) -> int:
    args = build_parser().parse_args(argv)
    command_id = TOOL_COMMANDS[args.tool]
    print("Build: exact known profile required (unknown EXEs rejected)")
    print(f"Tool: {args.tool}; command ID: 0x{command_id:02X}")
    print(f"Safety: {SAFETY[args.tool]}")

    targets = find_targets()
    if len(targets) != 1:
        print(
            f"Refusing: expected exactly one verified main window, found {len(targets)}.",
            file=sys.stderr,
        )
        return 2
    target = targets[0]
    print(f"Target HWND: 0x{target.hwnd:X}; PID: {target.pid}; title: {target.title!r}")
    print(f"Image: {target.image_path}; SHA256: {target.sha256}")

    if not args.confirm:
        print("Dry run only. No command was sent. Add --confirm to continue.")
        return 0
    confirm_phrase = CONFIRM_PHRASES[args.tool]
    if input_fn(f'Type exactly "{confirm_phrase}" to send: ') != confirm_phrase:
        print("Confirmation did not match; no command was sent.", file=sys.stderr)
        return 3

    outcome = send_command(target, args.tool)
    if isinstance(outcome, OpenDispatch) and not outcome.completed:
        alive, valid = target_status(target)
        report = OpenReport(OpenOutcome.UNCERTAIN if outcome.win32_error in (0, ERROR_TIMEOUT)
                            else OpenOutcome.FAILED, command_id, target.pid, target.hwnd,
                            outcome.win32_error, outcome.elapsed_ms, alive, None,
                            "command_return_uncertain" if valid else "target_changed")
        print(str(ToolOpenError(report)), file=sys.stderr)
        return 4
    print(f"Sent WM_COMMAND 0x{command_id:02X} to the verified retail main window.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
