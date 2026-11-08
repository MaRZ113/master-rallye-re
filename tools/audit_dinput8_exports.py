#!/usr/bin/env python3
"""Audit the PE32 DirectInput8 export names and ordinal assignments."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


EXPECTED = {
    "DirectInput8Create": 1,
    "DllCanUnloadNow": 2,
    "DllGetClassObject": 3,
    "DllRegisterServer": 4,
    "DllUnregisterServer": 5,
    "GetdfDIJoystick": 6,
}


class ExportAuditError(ValueError):
    pass


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise ExportAuditError("truncated PE uint16")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ExportAuditError("truncated PE uint32")
    return struct.unpack_from("<I", data, offset)[0]


def exports(data: bytes) -> dict[str, int]:
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ExportAuditError("missing DOS header")
    pe = _u32(data, 0x3C)
    if data[pe:pe + 4] != b"PE\0\0":
        raise ExportAuditError("missing PE signature")
    coff = pe + 4
    machine = _u16(data, coff)
    count_sections = _u16(data, coff + 2)
    optional_size = _u16(data, coff + 16)
    optional = coff + 20
    if machine != 0x14C or _u16(data, optional) != 0x10B:
        raise ExportAuditError("expected PE32/I386 system DirectInput DLL")
    if _u32(data, optional + 92) < 1:
        raise ExportAuditError("PE32 image has no export directory")
    export_rva = _u32(data, optional + 96)
    sections_at = optional + optional_size
    sections: list[tuple[int, int, int, int]] = []
    for index in range(count_sections):
        at = sections_at + 40 * index
        virtual_size = _u32(data, at + 8)
        virtual_address = _u32(data, at + 12)
        raw_size = _u32(data, at + 16)
        raw_offset = _u32(data, at + 20)
        sections.append((virtual_address, max(virtual_size, raw_size), raw_offset, raw_size))

    def file_offset(rva: int, amount: int = 1) -> int:
        for va, extent, raw, raw_size in sections:
            if va <= rva and rva + amount <= va + extent:
                offset = raw + rva - va
                if rva - va + amount <= raw_size and offset + amount <= len(data):
                    return offset
        raise ExportAuditError(f"export RVA 0x{rva:x} is not file-backed")

    directory = file_offset(export_rva, 40)
    ordinal_base = _u32(data, directory + 16)
    function_count = _u32(data, directory + 20)
    name_count = _u32(data, directory + 24)
    functions_rva = _u32(data, directory + 28)
    names_rva = _u32(data, directory + 32)
    ordinals_rva = _u32(data, directory + 36)
    function_table = file_offset(functions_rva, function_count * 4)
    names_table = file_offset(names_rva, name_count * 4)
    ordinals_table = file_offset(ordinals_rva, name_count * 2)
    result: dict[str, int] = {}
    for index in range(name_count):
        name_rva = _u32(data, names_table + index * 4)
        name_at = file_offset(name_rva)
        end = data.find(b"\0", name_at)
        if end < 0:
            raise ExportAuditError("unterminated export name")
        try:
            name = data[name_at:end].decode("ascii")
        except UnicodeDecodeError as exc:
            raise ExportAuditError("non-ASCII export name") from exc
        function_index = _u16(data, ordinals_table + index * 2)
        if function_index >= function_count:
            raise ExportAuditError("export name ordinal index exceeds function table")
        function_rva = _u32(data, function_table + function_index * 4)
        if not function_rva:
            raise ExportAuditError(f"export {name} points to an empty function slot")
        result[name] = ordinal_base + function_index
    return result


def audit(path: Path) -> dict:
    found = exports(path.read_bytes())
    missing = {name: ordinal for name, ordinal in EXPECTED.items()
               if found.get(name) != ordinal}
    if missing:
        raise ExportAuditError(f"required name/ordinal map differs: {missing}")
    return {"path": str(path), "required": EXPECTED, "observed": found,
            "required_match": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dll", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.dll)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
