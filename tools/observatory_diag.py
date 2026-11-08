#!/usr/bin/env python3
"""Explain why Observatory 0.3.0 does (not) accept a running Master Rallye window.

Run with the game open:  python tools/observatory_diag.py --observatory "<Observatory-0.3.0-beta folder>"
Read-only: enumerates windows, reads menus/titles and re-runs Observatory's own profile and
live-anchor checks; never sends window messages or writes process memory.
"""
from __future__ import annotations

import argparse
import ctypes
import sys
import traceback
from ctypes import wintypes
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--observatory", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.observatory))
    import dev_command_trigger as dct
    import broker_observatory as core
    from observatory_profile_resolver import resolve_executable_profile

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    dct._configure_user32(user32, ctypes)
    dct._configure_kernel32(kernel32, ctypes)
    user32.GetMenuItemID.argtypes = [wintypes.HMENU, ctypes.c_int]
    user32.GetMenuItemID.restype = wintypes.UINT
    rows = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        image = dct._image_for_pid(kernel32, int(pid.value))
        if image is None or not image.name.lower().startswith("mrallye"):
            return True
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, 512)
        rows.append((int(hwnd), int(pid.value), image, title.value, bool(user32.IsWindowVisible(hwnd))))
        return True

    user32.EnumWindows(cb, 0)
    if not rows:
        print("No MRallye* process windows found. Start the game first.")
        return 1
    for hwnd, pid, image, title, visible in rows:
        print(f"\n== hwnd {hwnd:#x} pid {pid} visible={visible} title={title!r}\n   image {image}")
        try:
            profile = resolve_executable_profile(image, cache_root=Path(a.observatory) / "observatory-data" / "build-profiles")
            print(f"   profile {profile.id} sha {profile.sha256[:16]} caps open_broker_editor="
                  f"{profile.supports('open_broker_editor')} native_dump={profile.supports('native_dump')}")
        except Exception as exc:  # noqa: BLE001 - diagnostic output
            print(f"   PROFILE FAILED: {exc}")
            continue
        menu = user32.GetMenu(hwnd)
        ids = sorted(dct._menu_command_ids(user32, menu)) if menu else []
        print(f"   menu handle {menu} ids {[hex(i) for i in ids][:40]}")
        print(f"   title prefix ok: {title.startswith(dct.MAIN_TITLE_PREFIX)}")
        print(f"   has Game Reset/Exit menu: {dct._has_expected_main_menu(user32, hwnd)}")
        try:
            print(f"   menu-less main accepted: {dct._verified_menu_less_main(pid, hwnd, profile)}")
        except Exception as exc:  # noqa: BLE001
            print(f"   menu-less main check raised: {type(exc).__name__}: {exc}")
        for cap in ("open_broker_editor", "native_dump", "broker_read"):
            try:
                core.verify_live_capability(pid, profile, cap)
                print(f"   live anchors for {cap}: OK")
            except Exception as exc:  # noqa: BLE001
                print(f"   live anchors for {cap}: FAILED {type(exc).__name__}: {exc}")
        try:
            print(f"   find_retail_main_windows -> {[hex(w.hwnd) for w in dct.find_retail_main_windows({pid: profile}) if w.pid == pid]}")
        except Exception:  # noqa: BLE001
            traceback.print_exc()
    return 0


if __name__ == "__main__":
    sys.exit(main())
