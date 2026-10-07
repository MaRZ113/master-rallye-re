#!/usr/bin/env python3
"""Extract hash-pinned demo localization group 0x39 selector rows.

This narrow evidence tool supports only the two audited demo executables. It
reads their known contiguous 12-byte localization rows and resolves string
pointers through the PE sections; other hashes/layouts fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_841 = REPO_ROOT.parent / "corpora" / "demo-8.4.1" / "MRallye.exe"
DEFAULT_DEMO_931 = REPO_ROOT.parent / "corpora" / "demo-9.3.1" / "MRallye.exe"
BUILDS = {
    "demo-8.4.1": {
        "sha256": "2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a",
        "size": 2084926,
        "group_0x39_tables": [{"raw_offset": 0x1E8F30, "row_count": 12}],
    },
    "demo-9.3.1": {
        "sha256": "611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728",
        "size": 2637886,
        "group_0x39_tables": [
            {"raw_offset": 0x2677CC, "row_count": 20},
            {"raw_offset": 0x269CBC, "row_count": 20},
        ],
    },
}


class EvidenceError(ValueError):
    """Raised for an unsupported executable or malformed localization rows."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_pe(data: bytes) -> dict[str, Any]:
    if len(data) < 0x40:
        raise EvidenceError("input is too short for a PE header")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise EvidenceError("invalid PE signature")
    coff = pe_offset + 4
    if struct.unpack_from("<H", data, coff)[0] != 0x14C:
        raise EvidenceError("only the audited 32-bit x86 builds are supported")
    section_count = struct.unpack_from("<H", data, coff + 2)[0]
    optional_size = struct.unpack_from("<H", data, coff + 16)[0]
    optional = coff + 20
    if struct.unpack_from("<H", data, optional)[0] != 0x10B:
        raise EvidenceError("only PE32 images are supported")
    image_base = struct.unpack_from("<I", data, optional + 28)[0]
    section_table = optional + optional_size
    sections: list[dict[str, int | str]] = []
    for index in range(section_count):
        offset = section_table + 40 * index
        name = data[offset:offset + 8].split(b"\0", 1)[0].decode("ascii", errors="strict")
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", data, offset + 8)
        if raw_offset + raw_size > len(data):
            raise EvidenceError(f"PE section {name} exceeds file bounds")
        sections.append({"name": name, "virtual_size": virtual_size, "rva": rva,
                         "raw_size": raw_size, "raw_offset": raw_offset})
    return {"image_base": image_base, "sections": sections}


def _read_c_string(data: bytes, pe: dict[str, Any], pointer: int) -> tuple[str, int]:
    image_base = int(pe["image_base"])
    for section in pe["sections"]:
        start_va = image_base + int(section["rva"])
        end_va = start_va + int(section["raw_size"])
        if start_va <= pointer < end_va:
            raw = int(section["raw_offset"]) + pointer - start_va
            end = data.find(b"\0", raw, min(raw + 256, len(data)))
            if end < 0:
                raise EvidenceError(f"unterminated localization text pointer 0x{pointer:08X}")
            try:
                return data[raw:end].decode("ascii"), raw
            except UnicodeDecodeError as exc:
                raise EvidenceError(f"non-ASCII localization string at 0x{pointer:08X}") from exc
    raise EvidenceError(f"localization pointer 0x{pointer:08X} is not file-backed")


def extract_table(data: bytes, pe: dict[str, Any], *, raw_offset: int,
                  row_count: int) -> list[dict[str, Any]]:
    if raw_offset < 0 or raw_offset + row_count * 12 > len(data):
        raise EvidenceError("pinned group table lies outside the executable")
    rows: list[dict[str, Any]] = []
    selectors: set[int] = set()
    for index in range(row_count):
        row_offset = raw_offset + index * 12
        group, selector, pointer = struct.unpack_from("<iiI", data, row_offset)
        if group != 0x39:
            raise EvidenceError(f"group-0x39 row {index} has unexpected group {group}")
        if selector in selectors:
            raise EvidenceError(f"duplicate selector {selector} in pinned table")
        selectors.add(selector)
        text, text_raw = _read_c_string(data, pe, pointer)
        rows.append({
            "row_index": index,
            "raw_offset": row_offset,
            "selector": selector,
            "string_pointer_va": pointer,
            "string_raw_offset": text_raw,
            "text": text,
        })
    return rows


def extract_build(path: Path, name: str) -> dict[str, Any]:
    if name not in BUILDS:
        raise EvidenceError(f"unsupported demo build: {name}")
    path = path.resolve(strict=True)
    data = path.read_bytes()
    pin = BUILDS[name]
    digest = sha256(data)
    if digest != pin["sha256"] or len(data) != pin["size"]:
        raise EvidenceError(f"{name} hash/size mismatch: {digest} / {len(data)}")
    pe = parse_pe(data)
    tables = []
    for table in pin["group_0x39_tables"]:
        tables.append({
            "raw_offset": table["raw_offset"],
            "table_va": int(pe["image_base"]) + table["raw_offset"],
            "rows": extract_table(data, pe, **table),
        })
    selectors = [{"selector": row["selector"], "text": row["text"]}
                 for row in tables[0]["rows"]]
    for table in tables[1:]:
        if [{"selector": row["selector"], "text": row["text"]}
                for row in table["rows"]] != selectors:
            raise EvidenceError(f"{name} duplicate group-0x39 tables differ")
    row2 = next((row for row in tables[0]["rows"] if row["selector"] == 2), None)
    if row2 is None or row2["text"] != "JOSE MARIA SERCIA":
        raise EvidenceError(f"{name} selector 2 differs from the audited ID2 result")
    return {
        "build": name,
        "corpus_relative_path": path.relative_to(REPO_ROOT.parent).as_posix(),
        "sha256": digest,
        "size": len(data),
        "image_base": pe["image_base"],
        "group": 0x39,
        "tables": tables,
        "physical_mercedes_id2_selector": 2,
        "physical_mercedes_id2_name": row2["text"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-8-4-1", type=Path, default=DEFAULT_DEMO_841)
    parser.add_argument("--demo-9-3-1", type=Path, default=DEFAULT_DEMO_931)
    parser.add_argument("--output", type=Path, help="optional derived JSON evidence under research/")
    args = parser.parse_args(argv)
    try:
        result = {
            "schema_version": 1,
            "evidence": "CONFIRMED_BY_EXE",
            "extraction_method": "exact-hash-pinned PE localization rows, 12-byte entries",
            "builds": [
                extract_build(args.demo_8_4_1, "demo-8.4.1"),
                extract_build(args.demo_9_3_1, "demo-9.3.1"),
            ],
        }
        encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            output = args.output.resolve(strict=False)
            research = (REPO_ROOT / "research").resolve()
            if research not in output.parents:
                raise EvidenceError("derived evidence output must be inside this checkout's research directory")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(encoded, encoding="utf-8")
        print(encoded, end="")
    except (OSError, EvidenceError, struct.error) as exc:
        parser.exit(2, f"demo group-0x39 extraction refused: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
