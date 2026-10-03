"""Fail-closed Windows Junction operations for source-cooker jobs.

Only the Junction node is removed. The target directory is never traversed or
deleted. The policy helpers are platform-independent so safety decisions can
be exercised by synthetic tests on non-Windows hosts.
"""
from __future__ import annotations

import ctypes
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class JunctionError(RuntimeError):
    """A Junction could not be inspected or acted on safely."""


@dataclass(frozen=True)
class JunctionInspection:
    kind: str
    target: str | None = None
    detail: str | None = None


def normalize_windows_path(value: str | os.PathLike[str]) -> str:
    """Normalize a Windows path for equality without resolving its target."""
    import ntpath

    text = os.fspath(value).replace("/", "\\")
    if text.startswith("\\??\\"):
        text = text[4:]
    if text.startswith("UNC\\"):
        text = "\\\\" + text[4:]
    return ntpath.normcase(ntpath.normpath(text)).rstrip("\\")


def classify_junction_policy(
    inspection: JunctionInspection,
    *,
    expected_target: str,
    owned_by_job: bool,
    ownership_state: str | None,
) -> str:
    """Return CREATE, OWNED, REUSE, ABSENT, or STOP for one path."""
    if inspection.kind == "ABSENT":
        return "ABSENT" if ownership_state in {"created", "removed"} else "CREATE"
    if inspection.kind != "JUNCTION" or not inspection.target:
        return "STOP"
    if normalize_windows_path(inspection.target) != normalize_windows_path(expected_target):
        return "STOP"
    if not owned_by_job or ownership_state not in {"created", "reused"}:
        return "STOP"
    return "OWNED" if ownership_state == "created" else "REUSE"


def _win_error(operation: str, path: Path) -> JunctionError:
    error = ctypes.get_last_error()
    return JunctionError(f"{operation} failed for {path}: {ctypes.FormatError(error).strip()}")


def _win_api():
    if os.name != "nt":
        raise JunctionError("native authoring Junctions are available only on Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
    kernel32.GetFileAttributesW.restype = ctypes.c_uint32
    kernel32.CreateDirectoryW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
    kernel32.CreateDirectoryW.restype = ctypes.c_int
    kernel32.RemoveDirectoryW.argtypes = [ctypes.c_wchar_p]
    kernel32.RemoveDirectoryW.restype = ctypes.c_int
    kernel32.CreateFileW.argtypes = [
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.DeviceIoControl.argtypes = [
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p,
    ]
    kernel32.DeviceIoControl.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    return kernel32


def _nt_target(path: Path) -> str:
    raw = os.path.abspath(os.fspath(path)).replace("/", "\\")
    if raw.startswith("\\\\"):
        return "\\??\\UNC\\" + raw.lstrip("\\")
    return "\\??\\" + raw


def _open_reparse_handle(kernel32: Any, path: Path, access: int) -> int:
    invalid = ctypes.c_void_p(-1).value
    handle = kernel32.CreateFileW(
        str(path), access, 0x1 | 0x2 | 0x4, None, 3,
        0x00200000 | 0x02000000, None,
    )
    if handle == invalid or handle is None:
        raise _win_error("open reparse point", path)
    return handle


def _decode_mount_target(buffer: bytes) -> str:
    if len(buffer) < 16:
        raise JunctionError("reparse-point data is truncated")
    tag, data_length, _reserved = struct.unpack_from("<IHH", buffer, 0)
    if tag != 0xA0000003:
        return ""
    if data_length + 8 > len(buffer):
        raise JunctionError("Junction reparse-point data length is invalid")
    substitute_offset, substitute_length, _print_offset, _print_length = struct.unpack_from(
        "<HHHH", buffer, 8
    )
    start = 16 + substitute_offset
    end = start + substitute_length
    if end > data_length + 8:
        raise JunctionError("Junction target range is invalid")
    value = buffer[start:end].decode("utf-16-le").rstrip("\0")
    if value.startswith("\\??\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\??\\"):
        value = value[4:]
    return value


def inspect_junction(path: str | os.PathLike[str]) -> JunctionInspection:
    """Inspect a path without following a reparse point."""
    item = Path(path)
    if os.name != "nt":
        if not os.path.lexists(item):
            return JunctionInspection("ABSENT")
        if item.is_symlink():
            return JunctionInspection("SYMLINK", os.readlink(item))
        return JunctionInspection("DIRECTORY" if item.is_dir() else "FILE")

    kernel32 = _win_api()
    attributes = kernel32.GetFileAttributesW(str(item))
    if attributes == 0xFFFFFFFF:
        error = ctypes.get_last_error()
        if error in (2, 3):
            return JunctionInspection("ABSENT")
        raise _win_error("inspect path", item)
    is_reparse = bool(attributes & 0x400)
    is_directory = bool(attributes & 0x10)
    if not is_reparse:
        return JunctionInspection("DIRECTORY" if is_directory else "FILE")

    handle = _open_reparse_handle(kernel32, item, 0x80000000)
    try:
        output = ctypes.create_string_buffer(16 * 1024)
        returned = ctypes.c_uint32()
        ok = kernel32.DeviceIoControl(
            handle, 0x000900A8, None, 0, output, len(output), ctypes.byref(returned), None
        )
        if not ok:
            raise _win_error("read reparse data", item)
        raw = output.raw[:returned.value]
        if len(raw) < 4:
            raise JunctionError(f"reparse data is truncated for {item}")
        tag = struct.unpack_from("<I", raw, 0)[0]
        if tag != 0xA0000003:
            kind = "SYMLINK" if tag == 0xA000000C else "OTHER_REPARSE"
            return JunctionInspection(kind, detail=f"reparse tag 0x{tag:08X}")
        return JunctionInspection("JUNCTION", _decode_mount_target(raw))
    finally:
        kernel32.CloseHandle(handle)


def create_junction(link_path: str | os.PathLike[str], target_path: str | os.PathLike[str]) -> None:
    """Create and verify a Junction; never create missing parents."""
    link = Path(os.path.abspath(os.fspath(link_path)))
    target = Path(os.path.abspath(os.fspath(target_path)))
    if os.name != "nt":
        raise JunctionError("native authoring Junctions are available only on Windows")
    if not target.is_dir():
        raise JunctionError(f"Junction target directory is missing: {target}")
    if not link.parent.is_dir():
        raise JunctionError(f"historical parent directory is missing; refusing to create it: {link.parent}")
    kernel32 = _win_api()
    if not kernel32.CreateDirectoryW(str(link), None):
        raise _win_error("create Junction placeholder", link)
    handle = None
    try:
        handle = _open_reparse_handle(kernel32, link, 0x40000000)
        substitute = _nt_target(target)
        printable = str(target).replace("/", "\\")
        sub_bytes = substitute.encode("utf-16-le")
        print_bytes = printable.encode("utf-16-le")
        path_buffer = sub_bytes + b"\0\0" + print_bytes + b"\0\0"
        data_length = 8 + len(path_buffer)
        payload = struct.pack(
            "<IHHHHHH", 0xA0000003, data_length, 0,
            0, len(sub_bytes), len(sub_bytes) + 2, len(print_bytes),
        ) + path_buffer
        input_buffer = ctypes.create_string_buffer(payload)
        returned = ctypes.c_uint32()
        if not kernel32.DeviceIoControl(
            handle, 0x000900A4, input_buffer, len(payload), None, 0,
            ctypes.byref(returned), None,
        ):
            raise _win_error("set Junction target", link)
    except Exception:
        if handle:
            kernel32.CloseHandle(handle)
            handle = None
        # The placeholder was created by this call, and is safe to remove only
        # if it remains an ordinary empty directory.
        current = inspect_junction(link)
        if current.kind == "DIRECTORY":
            kernel32.RemoveDirectoryW(str(link))
        raise
    finally:
        if handle:
            kernel32.CloseHandle(handle)
    current = inspect_junction(link)
    if current.kind != "JUNCTION" or not current.target or normalize_windows_path(current.target) != normalize_windows_path(target):
        raise JunctionError(f"post-create target verification failed for {link}: {current}")


def remove_owned_junction(
    link_path: str | os.PathLike[str],
    expected_target: str | os.PathLike[str],
    *,
    owned_by_job: bool,
    ownership_state: str | None,
) -> str:
    """Remove only an exact job-owned Junction node; return removed/absent."""
    link = Path(os.path.abspath(os.fspath(link_path)))
    inspection = inspect_junction(link)
    if inspection.kind == "ABSENT":
        return "absent"
    action = classify_junction_policy(
        inspection,
        expected_target=os.fspath(expected_target),
        owned_by_job=owned_by_job,
        ownership_state=ownership_state,
    )
    if action == "ABSENT":
        return "absent"
    if action != "OWNED":
        raise JunctionError(
            f"refusing Junction cleanup for {link}: kind={inspection.kind}, "
            f"target={inspection.target!r}, ownership_state={ownership_state!r}"
        )
    if os.name != "nt":
        raise JunctionError("native Junction cleanup is available only on Windows")
    kernel32 = _win_api()
    if not kernel32.RemoveDirectoryW(str(link)):
        raise _win_error("remove verified Junction node", link)
    if inspect_junction(link).kind != "ABSENT":
        raise JunctionError(f"Junction remains after cleanup: {link}")
    return "removed"
