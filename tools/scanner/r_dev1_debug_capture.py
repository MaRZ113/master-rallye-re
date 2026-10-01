"""Capture text from Master Rallye's owner-drawn Debug window.

Uses Python's standard library and Win32 APIs. OCR needs Tesseract, provided
with --tesseract or installed on PATH. This helper only observes windows and
captures pixels; it never sends input to the game.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

user32 = ctypes.windll.user32 if sys.platform == "win32" else None
gdi32 = ctypes.windll.gdi32 if sys.platform == "win32" else None
_configured = False


class BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BitmapInfo(ctypes.Structure):
    _fields_ = [("bmiHeader", BitmapInfoHeader), ("bmiColors", wintypes.DWORD * 3)]


def _ensure_windows() -> None:
    global _configured
    if user32 is None or gdi32 is None:
        raise RuntimeError("This helper requires Windows.")
    if _configured:
        return
    hwnd, hdc, hbitmap, hgdiobj = wintypes.HWND, wintypes.HDC, wintypes.HBITMAP, wintypes.HGDIOBJ
    user32.GetWindowTextLengthW.argtypes = [hwnd]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [hwnd, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetClassNameW.argtypes = [hwnd, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.IsWindowVisible.argtypes = [hwnd]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsWindow.argtypes = [hwnd]
    user32.IsWindow.restype = wintypes.BOOL
    user32.GetWindowRect.argtypes = [hwnd, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, hwnd, wintypes.LPARAM), wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.EnumChildWindows.argtypes = [hwnd, ctypes.WINFUNCTYPE(wintypes.BOOL, hwnd, wintypes.LPARAM), wintypes.LPARAM]
    user32.EnumChildWindows.restype = wintypes.BOOL
    user32.GetWindowDC.argtypes = [hwnd]
    user32.GetWindowDC.restype = hdc
    user32.ReleaseDC.argtypes = [hwnd, hdc]
    user32.ReleaseDC.restype = ctypes.c_int
    user32.PrintWindow.argtypes = [hwnd, hdc, wintypes.UINT]
    user32.PrintWindow.restype = wintypes.BOOL
    gdi32.CreateCompatibleDC.argtypes = [hdc]
    gdi32.CreateCompatibleDC.restype = hdc
    gdi32.CreateCompatibleBitmap.argtypes = [hdc, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = hbitmap
    gdi32.SelectObject.argtypes = [hdc, hgdiobj]
    gdi32.SelectObject.restype = hgdiobj
    gdi32.BitBlt.argtypes = [hdc, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, hdc, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
    gdi32.BitBlt.restype = wintypes.BOOL
    gdi32.GetDIBits.argtypes = [hdc, hbitmap, wintypes.UINT, wintypes.UINT, wintypes.LPVOID, ctypes.POINTER(BitmapInfo), wintypes.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.DeleteObject.argtypes = [hgdiobj]
    gdi32.DeleteObject.restype = wintypes.BOOL
    gdi32.DeleteDC.argtypes = [hdc]
    gdi32.DeleteDC.restype = wintypes.BOOL
    _configured = True


def _window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(max(length + 1, 2))
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value


def _window_class(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(512)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value


def enumerate_windows() -> list[dict[str, object]]:
    _ensure_windows()
    rows: list[dict[str, object]] = []
    enum_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def visit(hwnd: int, _param: int) -> bool:
        children: list[dict[str, object]] = []

        def visit_child(child: int, _child_param: int) -> bool:
            children.append({
                "hwnd": f"0x{int(child):X}", "title": _window_text(child),
                "class": _window_class(child), "visible": bool(user32.IsWindowVisible(child)),
            })
            return True

        user32.EnumChildWindows(hwnd, enum_type(visit_child), 0)
        rows.append({
            "hwnd": f"0x{int(hwnd):X}", "title": _window_text(hwnd),
            "class": _window_class(hwnd), "visible": bool(user32.IsWindowVisible(hwnd)),
            "children": children,
        })
        return True

    user32.EnumWindows(enum_type(visit), 0)
    return rows


def find_debug_window(title: str, class_name: str | None = None) -> int | None:
    for row in enumerate_windows():
        if row["title"] == title and (not class_name or row["class"] == class_name) and row["visible"]:
            return int(str(row["hwnd"]), 16)
    return None


def capture_ppm(hwnd: int) -> bytes:
    _ensure_windows()
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError()
    width, height = rect.right - rect.left, rect.bottom - rect.top
    if width <= 0 or height <= 0:
        raise RuntimeError("Debug window has an empty rectangle.")
    window_dc = user32.GetWindowDC(hwnd)
    if not window_dc:
        raise ctypes.WinError()
    memory_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    if not memory_dc or not bitmap:
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if memory_dc:
            gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)
        raise ctypes.WinError()
    old_bitmap = gdi32.SelectObject(memory_dc, bitmap)
    try:
        ok = user32.PrintWindow(hwnd, memory_dc, 0x00000002)  # PW_RENDERFULLCONTENT
        if not ok:
            ok = gdi32.BitBlt(memory_dc, 0, 0, width, height, window_dc, 0, 0, 0x00CC0020)
        if not ok:
            raise RuntimeError("PrintWindow and BitBlt both failed.")
        # GetDIBits requires the source bitmap to be deselected from the DC.
        gdi32.SelectObject(memory_dc, old_bitmap)
        stride = ((width * 24 + 31) // 32) * 4
        pixels = ctypes.create_string_buffer(stride * height)
        info = BitmapInfo()
        info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 24
        info.bmiHeader.biCompression = 0
        lines = gdi32.GetDIBits(memory_dc, bitmap, 0, height, pixels, ctypes.byref(info), 0)
        if lines != height:
            raise RuntimeError(f"GetDIBits returned {lines} of {height} rows.")
        raw = pixels.raw
        rgb = bytearray(width * height * 3)
        out = 0
        for y in range(height):
            row = y * stride
            for x in range(width):
                pos = row + x * 3
                rgb[out:out + 3] = bytes((raw[pos + 2], raw[pos + 1], raw[pos]))
                out += 3
        return f"P6\n{width} {height}\n255\n".encode("ascii") + rgb
    finally:
        gdi32.SelectObject(memory_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)


def recognize(ppm: bytes, executable: str) -> list[str]:
    result = subprocess.run(
        [executable, "stdin", "stdout", "--psm", "6"], input=ppm,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Tesseract failed ({result.returncode}): {detail}")
    return [line.strip() for line in result.stdout.decode("utf-8", errors="replace").splitlines() if line.strip()]


def new_lines(previous: list[str], current: list[str]) -> list[str]:
    if not current or current == previous:
        return []
    for overlap in range(min(len(previous), len(current)), 0, -1):
        if previous[-overlap:] == current[:overlap]:
            return current[overlap:]
    common = 0
    for before, after in zip(previous, current):
        if before != after:
            break
        common += 1
    return current[common:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list top-level windows and child controls")
    parser.add_argument("--capture", action="store_true", help="OCR the separate Debug window")
    parser.add_argument("--title", default="Debug", help="exact top-level window title")
    parser.add_argument("--class-name", help="optional exact Win32 class")
    parser.add_argument("--interval-ms", type=int, default=1000)
    parser.add_argument("--duration-sec", type=float, default=0, help="0 runs until Ctrl-C")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tesseract", help="executable path; defaults to PATH lookup")
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        parser.error("Win32 window APIs are required.")
    if args.list:
        print(json.dumps(enumerate_windows(), ensure_ascii=False, indent=2))
        return 0
    if not args.capture:
        parser.error("select --list or --capture")
    if args.interval_ms < 100:
        parser.error("--interval-ms must be at least 100")
    ocr = args.tesseract or shutil.which("tesseract")
    if not ocr:
        parser.error("Tesseract not found; use --tesseract PATH or install it on PATH")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = args.output or (Path.home() / "Documents" / f"MasterRallye-Debug-{stamp}.txt")
    output.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + args.duration_sec if args.duration_sec > 0 else None
    previous: list[str] = []
    hwnd: int | None = None
    try:
        while deadline is None or time.monotonic() < deadline:
            if hwnd is None or not user32.IsWindow(hwnd):
                hwnd = find_debug_window(args.title, args.class_name)
            if hwnd is not None:
                lines = recognize(capture_ppm(hwnd), ocr)
                added = new_lines(previous, lines)
                if added:
                    now = datetime.now().astimezone().isoformat(timespec="milliseconds")
                    with output.open("a", encoding="utf-8", newline="\n") as stream:
                        for line in added:
                            stream.write(f"[{now}] {line}\n")
                    print(f"{now} +{len(added)} lines -> {output}")
                previous = lines
            time.sleep(args.interval_ms / 1000)
    except KeyboardInterrupt:
        pass
    print(f"Capture stopped. UTF-8 output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
