"""Read a standard Win32 Debug text control without changing the game process.

Windows only. Logs are restricted to ignored .research-output/r-demo/runtime-logs.
No injection, memory access, keyboard automation or EXE modification is used.
"""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import sys
import time
from ctypes import wintypes
from pathlib import Path

WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
SMTO_ABORTIFHUNG = 0x0002
MAX_TEXT_CHARS = 2_000_000
TEXT_CLASSES = ("edit", "richedit", "richtext")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LOG_ROOT = REPOSITORY_ROOT / ".research-output" / "r-demo" / "runtime-logs"


def text_delta(previous: str, current: str) -> tuple[str, bool]:
    """Return appended text and whether a window reset/replaced its buffer."""
    if current.startswith(previous):
        return current[len(previous):], False
    if previous:
        tail = previous[-min(256, len(previous)):]
        position = current.find(tail)
        if position >= 0:
            return current[position + len(tail):], False
    return current, True


class LineAccumulator:
    def __init__(self) -> None:
        self.pending = ""

    def feed(self, fragment: str) -> list[str]:
        self.pending += fragment
        lines = []
        parts = self.pending.splitlines(keepends=True)
        self.pending = ""
        for part in parts:
            if part.endswith(("\r", "\n")):
                lines.append(part.rstrip("\r\n"))
            else:
                self.pending = part
        return lines

    def flush(self) -> str:
        result, self.pending = self.pending, ""
        return result


def user32_api():
    if sys.platform != "win32":
        raise RuntimeError("Win32 Debug window capture requires Windows")
    dll = ctypes.WinDLL("user32", use_last_error=True)
    hwnd = wintypes.HWND
    dll.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
    dll.EnumWindows.restype = wintypes.BOOL
    dll.EnumChildWindows.argtypes = [hwnd, ctypes.c_void_p, wintypes.LPARAM]
    dll.EnumChildWindows.restype = wintypes.BOOL
    dll.GetWindowTextLengthW.argtypes = [hwnd]
    dll.GetWindowTextLengthW.restype = ctypes.c_int
    dll.GetWindowTextW.argtypes = [hwnd, wintypes.LPWSTR, ctypes.c_int]
    dll.GetWindowTextW.restype = ctypes.c_int
    dll.GetClassNameW.argtypes = [hwnd, wintypes.LPWSTR, ctypes.c_int]
    dll.GetClassNameW.restype = ctypes.c_int
    dll.GetWindowThreadProcessId.argtypes = [hwnd, ctypes.POINTER(wintypes.DWORD)]
    dll.GetWindowThreadProcessId.restype = wintypes.DWORD
    dll.IsWindow.argtypes = [hwnd]
    dll.IsWindow.restype = wintypes.BOOL
    dll.SendMessageTimeoutW.argtypes = [hwnd, wintypes.UINT, wintypes.WPARAM,
                                         wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                                         ctypes.POINTER(ctypes.c_size_t)]
    dll.SendMessageTimeoutW.restype = wintypes.LPARAM
    return dll


def enumerate_handles(api, parent: int | None = None) -> list[int]:
    handles: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def collect(hwnd, _param):
        handles.append(int(hwnd))
        return True
    callback = callback_type(collect)
    if parent is None:
        api.EnumWindows(callback, 0)
    else:
        api.EnumChildWindows(parent, callback, 0)
    return handles


def class_name(api, handle: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    api.GetClassNameW(handle, buffer, len(buffer))
    return buffer.value


def title_text(api, handle: int) -> str:
    length = min(api.GetWindowTextLengthW(handle), 4096)
    buffer = ctypes.create_unicode_buffer(length + 1)
    api.GetWindowTextW(handle, buffer, len(buffer))
    return buffer.value


def process_id(api, handle: int) -> int:
    pid = wintypes.DWORD()
    api.GetWindowThreadProcessId(handle, ctypes.byref(pid))
    return int(pid.value)


def send_text_message(api, handle: int, message: int, wparam: int, lparam: int) -> int | None:
    result = ctypes.c_size_t()
    ok = api.SendMessageTimeoutW(handle, message, wparam, lparam,
                                 SMTO_ABORTIFHUNG, 200, ctypes.byref(result))
    return int(result.value) if ok else None


def control_text(api, handle: int) -> str | None:
    length = send_text_message(api, handle, WM_GETTEXTLENGTH, 0, 0)
    if length is None or length < 0 or length > MAX_TEXT_CHARS:
        return None
    buffer = ctypes.create_unicode_buffer(length + 1)
    copied = send_text_message(api, handle, WM_GETTEXT, length + 1, ctypes.addressof(buffer))
    return buffer.value if copied is not None else None


def matching_windows(api, title_fragment: str, pid: int | None) -> list[dict]:
    rows = []
    for handle in enumerate_handles(api):
        title = title_text(api, handle)
        if title_fragment.casefold() not in title.casefold():
            continue
        actual_pid = process_id(api, handle)
        if pid is not None and actual_pid != pid:
            continue
        children = []
        for child in enumerate_handles(api, handle):
            kind = class_name(api, child)
            readable = any(kind.casefold().startswith(prefix) for prefix in TEXT_CLASSES)
            text = control_text(api, child) if readable else None
            children.append({"hwnd": child, "class": kind,
                             "readable_text_chars": len(text) if text is not None else None})
        rows.append({"hwnd": handle, "title": title, "class": class_name(api, handle),
                     "pid": actual_pid, "children": children})
    return rows


def timestamp() -> str:
    return dt.datetime.now().astimezone().strftime("%H:%M:%S.%f")[:-3]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window-title", default="Debug", help="case-insensitive title fragment")
    ap.add_argument("--pid", type=int, help="optional demo process ID")
    ap.add_argument("--output", type=Path, help="UTF-8 log under ignored runtime-logs")
    ap.add_argument("--poll-ms", type=int, default=250)
    ap.add_argument("--wait-seconds", type=int, default=120)
    ap.add_argument("--list-windows", action="store_true")
    args = ap.parse_args()
    if not 50 <= args.poll_ms <= 5000:
        ap.error("--poll-ms must be 50..5000")
    if args.wait_seconds < 0:
        ap.error("--wait-seconds must be nonnegative")
    api = user32_api()
    if args.list_windows:
        print(json.dumps(matching_windows(api, args.window_title, args.pid),
                         ensure_ascii=False, indent=2))
        return
    if args.output is None:
        ap.error("--output is required unless --list-windows is used")
    output = args.output.resolve()
    root = LOG_ROOT.resolve()
    if root not in output.parents or output.suffix.lower() not in {".log", ".txt"}:
        ap.error("--output must be a .log or .txt under .research-output/r-demo/runtime-logs")
    deadline = time.monotonic() + args.wait_seconds
    chosen = None
    while time.monotonic() <= deadline:
        windows = matching_windows(api, args.window_title, args.pid)
        for window in windows:
            controls = [child for child in window["children"]
                        if child["readable_text_chars"] is not None]
            if controls:
                chosen = max(controls, key=lambda row: row["readable_text_chars"])["hwnd"]
                print(json.dumps({"window": window["title"], "pid": window["pid"],
                                  "control_hwnd": chosen}))
                break
        if chosen is not None:
            break
        time.sleep(args.poll_ms / 1000)
    if chosen is None:
        raise SystemExit("no readable standard text control found; use --list-windows and fallback capture methods")
    output.parent.mkdir(parents=True, exist_ok=True)
    previous = ""
    accumulator = LineAccumulator()
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        try:
            while api.IsWindow(chosen):
                current = control_text(api, chosen)
                if current is None:
                    print("WM_GETTEXT failed or timed out; capture stopped", file=sys.stderr)
                    break
                added, reset = text_delta(previous, current)
                if reset:
                    old_tail = accumulator.flush()
                    if old_tail:
                        stream.write(f"{timestamp()} | {old_tail}\n")
                    stream.write(f"{timestamp()} | [window text reset]\n")
                for line in accumulator.feed(added):
                    stream.write(f"{timestamp()} | {line}\n")
                stream.flush()
                previous = current
                time.sleep(args.poll_ms / 1000)
        except KeyboardInterrupt:
            pass
        remaining = accumulator.flush()
        if remaining:
            stream.write(f"{timestamp()} | {remaining}\n")
    print(f"saved {output}")


if __name__ == "__main__":
    main()
