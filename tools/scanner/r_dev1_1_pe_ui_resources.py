"""Inventory PE UI resources and dialog control IDs for R-DEV1.1.

The script reads an EXE only. ``pefile`` is loaded lazily so the pure dialog
template parser can be tested without the optional PE dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


RT_DIALOG = 5
DS_SETFONT = 0x00000040
CONTROL_ID_MIN = 0x26
CONTROL_ID_MAX = 0x58


def _u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _align4(offset: int) -> int:
    return (offset + 3) & ~3


def _skip_var_field(data: bytes, offset: int) -> int:
    """Skip a menu/class/title field encoded as empty, ordinal, or UTF-16."""
    if offset + 2 > len(data):
        raise ValueError("variable field extends beyond dialog template")
    value = _u16(data, offset)
    offset += 2
    if value == 0:
        return offset
    if value == 0xFFFF:
        if offset + 2 > len(data):
            raise ValueError("ordinal field extends beyond dialog template")
        return offset + 2
    while offset + 2 <= len(data):
        if _u16(data, offset) == 0:
            return offset + 2
        offset += 2
    raise ValueError("unterminated UTF-16 field in dialog template")


def parse_dialog_template(data: bytes) -> list[int]:
    """Return control IDs from a standard DLGTEMPLATE or DIALOGEX template."""
    if len(data) < 18:
        raise ValueError("dialog template is shorter than its standard header")

    extended = len(data) >= 26 and _u16(data, 0) == 1 and _u16(data, 2) == 0xFFFF
    if extended:
        style = _u32(data, 12)
        control_count = _u16(data, 16)
        offset = 26
    else:
        style = _u32(data, 0)
        control_count = _u16(data, 8)
        offset = 18

    for _ in range(3):
        offset = _skip_var_field(data, offset)
    if style & DS_SETFONT:
        offset += 6 if extended else 2
        offset = _skip_var_field(data, offset)

    control_ids: list[int] = []
    for _ in range(control_count):
        offset = _align4(offset)
        if extended:
            offset += 20
            if offset + 4 > len(data):
                raise ValueError("extended control header extends beyond template")
            control_ids.append(_u32(data, offset))
            offset += 4
        else:
            offset += 16
            if offset + 2 > len(data):
                raise ValueError("control header extends beyond template")
            control_ids.append(_u16(data, offset))
            offset += 2

        offset = _skip_var_field(data, offset)
        offset = _skip_var_field(data, offset)
        if offset + 2 > len(data):
            raise ValueError("control creation-data count extends beyond template")
        creation_data_size = _u16(data, offset)
        offset += 2 + creation_data_size
        if offset > len(data):
            raise ValueError("control creation data extends beyond template")

    return control_ids


def _resource_name(entry: Any) -> str:
    if entry.name is not None:
        return entry.name.string.decode("utf-8", errors="replace")
    return str(entry.struct.Id)


def inspect_exe(path: Path, build: str) -> dict[str, Any]:
    try:
        import pefile
    except ImportError as exc:
        raise RuntimeError("PE inspection requires the already-used 'pefile' package") from exc

    pe = pefile.PE(str(path), fast_load=False)
    resource_types = [_resource_name(entry) for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries]
    dialog_type = next(
        (
            entry
            for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries
            if entry.name is None and entry.struct.Id == RT_DIALOG
        ),
        None,
    )
    if dialog_type is None:
        dialogs = []
    else:
        dialogs = []
        for name_entry in dialog_type.directory.entries:
            language_entry = name_entry.directory.entries[0]
            resource = language_entry.data.struct
            payload = pe.get_data(resource.OffsetToData, resource.Size)
            dialogs.append(
                {
                    "id": _resource_name(name_entry),
                    "control_ids": parse_dialog_template(payload),
                }
            )

    all_control_ids = [item for dialog in dialogs for item in dialog["control_ids"]]
    tested_matches = sorted(
        {
            control_id
            for control_id in all_control_ids
            if CONTROL_ID_MIN <= control_id <= CONTROL_ID_MAX
        }
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "build": build,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": digest,
        "resource_type_ids": resource_types,
        "dialog_count": len(dialogs),
        "dialog_control_count": len(all_control_ids),
        "dialog_resource_ids": [dialog["id"] for dialog in dialogs],
        "dialog_control_id_range_checked_inclusive": [CONTROL_ID_MIN, CONTROL_ID_MAX],
        "control_ids_in_tested_range": [f"0x{item:X}" for item in tested_matches],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, help="Human-readable build name")
    parser.add_argument("exe", type=Path, help="Read-only EXE path")
    args = parser.parse_args(argv)
    print(json.dumps(inspect_exe(args.exe, args.build), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
