"""Narrow, confirmation-gated opener for two retail developer tools.

This helper sends one allowlisted WM_COMMAND to a verified Master Rallye retail
main window. It does not accept arbitrary command IDs, write process memory,
inject code, or perform any tool action after opening.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
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
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
MF_BYPOSITION = 0x0400


@dataclass(frozen=True)
class TargetWindow:
    pid: int
    hwnd: int
    image_path: Path
    sha256: str
    title: str


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


def find_retail_main_windows() -> list[TargetWindow]:
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
        if not user32.IsWindowVisible(hwnd_value) or not _has_expected_main_menu(
            user32, hwnd_value
        ):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd_value, ctypes.byref(pid))
        image_path = _image_for_pid(kernel32, int(pid.value))
        if image_path is None:
            return True
        try:
            image_hash = sha256_file(image_path)
        except OSError:
            return True
        if image_hash != RETAIL_SHA256:
            return True
        title_buffer = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd_value, title_buffer, len(title_buffer))
        candidates.append(
            TargetWindow(
                pid=int(pid.value),
                hwnd=hwnd_value,
                image_path=image_path,
                sha256=image_hash,
                title=title_buffer.value,
            )
        )
        return True

    user32.EnumWindows(callback, 0)
    return candidates


def send_tool_command(target: TargetWindow, tool: str) -> None:
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
    image_path = _image_for_pid(kernel32, target.pid)
    if image_path is None or sha256_file(image_path) != RETAIL_SHA256:
        raise RuntimeError("Target process no longer matches the verified retail EXE.")
    if not user32.IsWindowVisible(target.hwnd) or not _has_expected_main_menu(
        user32, target.hwnd
    ):
        raise RuntimeError("Target no longer has the verified Game → Reset / Exit menu.")

    result = ctypes.c_size_t()
    sent = user32.SendMessageTimeoutW(
        target.hwnd,
        WM_COMMAND,
        TOOL_COMMANDS[tool],
        0,
        SMTO_ABORTIFHUNG,
        3000,
        ctypes.byref(result),
    )
    if not sent:
        raise ctypes.WinError(ctypes.get_last_error())


def find_tool_windows(pid: int, tool: str) -> list[TargetWindow]:
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
    if image is None or sha256_file(image) != RETAIL_SHA256:
        raise RuntimeError("Tool owner is not verified retail.")
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
        result.append(TargetWindow(pid, int(hwnd), image, RETAIL_SHA256, title.value))
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


def send_broker_dump(target: TargetWindow) -> None:
    """Only Broker Editor local WM_COMMAND 2: original observational Dump.

    The recipient is freshly rediscovered by PID, exact title and menu layout.
    The main-window command ID 2 is never used.
    """
    matches = find_tool_windows(target.pid, "broker-editor")
    if len(matches) != 1 or matches[0].hwnd != target.hwnd:
        raise RuntimeError("Broker Editor identity changed or is ambiguous.")
    import ctypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    _configure_user32(user32, ctypes)
    result = ctypes.c_size_t()
    if not user32.SendMessageTimeoutW(target.hwnd, WM_COMMAND, 2, 0,
                                     SMTO_ABORTIFHUNG, 10000, ctypes.byref(result)):
        raise RuntimeError("Broker Dump command timed out; it may still run. No retry was sent.")


def main(
    argv: Sequence[str] | None = None,
    *,
    find_targets: Callable[[], list[TargetWindow]] = find_retail_main_windows,
    send_command: Callable[[TargetWindow, str], None] = send_tool_command,
    input_fn: Callable[[str], str] = input,
) -> int:
    args = build_parser().parse_args(argv)
    command_id = TOOL_COMMANDS[args.tool]
    print(f"Build: retail; required EXE SHA256: {RETAIL_SHA256}")
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

    send_command(target, args.tool)
    print(f"Sent WM_COMMAND 0x{command_id:02X} to the verified retail main window.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
