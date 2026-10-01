#!/usr/bin/env python3
"""Read-only PE fingerprint collector for the Master Rallye R-EXE1 corpus.

Uses only the Python standard library. It records derived metadata, never copies
or writes to the source executables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any


EXPECTED = {
    "8.4.1": "bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be",
    "9.3.1": "931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680",
    "9.10.0": "13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78",
    "retail": "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",
}
BUILD_DIRS = {
    "8.4.1": "demo-8.4.1",
    "9.3.1": "demo-9.3.1",
    "9.10.0": "demo-9.10.0",
    "retail": "retail",
}
MACHINE = {0x014C: "i386", 0x8664: "amd64", 0x01C0: "ARM", 0x01C4: "ARMNT"}
SUBSYSTEM = {1: "native", 2: "Windows GUI", 3: "Windows CUI", 9: "Windows CE GUI"}
SECTION_FLAGS = {
    0x00000020: "CODE", 0x00000040: "INITIALIZED_DATA",
    0x00000080: "UNINITIALIZED_DATA", 0x02000000: "DISCARDABLE",
    0x20000000: "EXECUTE", 0x40000000: "READ", 0x80000000: "WRITE",
}


def u16(buf: bytes, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]


def u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def cstr(buf: bytes, off: int, limit: int = 4096) -> str:
    if off < 0 or off >= len(buf):
        return ""
    end = buf.find(b"\0", off, min(len(buf), off + limit))
    if end < 0:
        end = min(len(buf), off + limit)
    return buf[off:end].decode("ascii", "replace")


def parse_pe(path: Path, root: Path, build: str) -> dict[str, Any]:
    data = path.read_bytes()
    if data[:2] != b"MZ":
        raise ValueError(f"{path} has no MZ header")
    nt = u32(data, 0x3C)
    if data[nt:nt + 4] != b"PE\0\0":
        raise ValueError(f"{path} has no PE signature at e_lfanew")
    coff = nt + 4
    machine, section_count, timestamp, _, _, opt_size, characteristics = struct.unpack_from("<HHIIIHH", data, coff)
    opt = coff + 20
    magic = u16(data, opt)
    if magic == 0x10B:
        pe_kind, ptr_width, image_base_off, dir_count_off, dirs_off = "PE32", 4, 28, 92, 96
    elif magic == 0x20B:
        pe_kind, ptr_width, image_base_off, dir_count_off, dirs_off = "PE32+", 8, 24, 108, 112
    else:
        raise ValueError(f"Unsupported optional-header magic: 0x{magic:04x}")
    image_base = struct.unpack_from("<Q" if ptr_width == 8 else "<I", data, opt + image_base_off)[0]
    entry_rva = u32(data, opt + 16)
    section_alignment, file_alignment = u32(data, opt + 32), u32(data, opt + 36)
    size_image, size_headers = u32(data, opt + 56), u32(data, opt + 60)
    subsystem, dll_chars = u16(data, opt + 68), u16(data, opt + 70)
    linker_major, linker_minor = data[opt + 2], data[opt + 3]
    num_dirs = min(u32(data, opt + dir_count_off), 16)
    dirs = []
    for i in range(num_dirs):
        off = opt + dirs_off + i * 8
        if off + 8 > opt + opt_size:
            break
        rva, size = struct.unpack_from("<II", data, off)
        dirs.append((rva, size))

    section_table = opt + opt_size
    sections = []
    for i in range(section_count):
        off = section_table + i * 40
        name, vsize, va, raw_size, raw_ptr, _, _, _, _, flags = struct.unpack_from("<8sIIIIIIHHI", data, off)
        decoded_flags = [label for bit, label in SECTION_FLAGS.items() if flags & bit]
        sections.append({
            "name": name.rstrip(b"\0").decode("ascii", "replace"),
            "virtual_address": f"0x{va:08X}", "virtual_size": vsize,
            "raw_offset": f"0x{raw_ptr:08X}", "raw_size": raw_size,
            "characteristics": f"0x{flags:08X}", "flags": decoded_flags,
        })

    def rva_to_off(rva: int) -> int | None:
        if rva < size_headers:
            return rva if rva < len(data) else None
        for sec in sections:
            va = int(sec["virtual_address"], 16)
            raw = int(sec["raw_offset"], 16)
            raw_size = int(sec["raw_size"])
            vsize = int(sec["virtual_size"])
            if va <= rva < va + max(raw_size, vsize):
                off = raw + (rva - va)
                return off if off < len(data) else None
        return None

    imports = []
    if len(dirs) > 1 and dirs[1][0]:
        off = rva_to_off(dirs[1][0])
        if off is not None:
            for _ in range(8192):
                if off + 20 > len(data):
                    break
                oft, stamp, chain, name_rva, first = struct.unpack_from("<IIIII", data, off)
                if not (oft or stamp or chain or name_rva or first):
                    break
                noff = rva_to_off(name_rva)
                dll = cstr(data, noff or 0).lower()
                thunk_rva = oft or first
                thunk_off = rva_to_off(thunk_rva)
                names = []
                if thunk_off is not None:
                    for j in range(65536):
                        p_off = thunk_off + j * ptr_width
                        if p_off + ptr_width > len(data):
                            break
                        thunk = struct.unpack_from("<Q" if ptr_width == 8 else "<I", data, p_off)[0]
                        if thunk == 0:
                            break
                        ordinal_bit = 1 << (ptr_width * 8 - 1)
                        if thunk & ordinal_bit:
                            names.append({"ordinal": int(thunk & 0xFFFF)})
                        else:
                            iat = rva_to_off(int(thunk))
                            names.append({"name": cstr(data, (iat + 2) if iat is not None else 0)})
                imports.append({"dll": dll, "symbols": names})
                off += 20

    exports = []
    if dirs and dirs[0][0]:
        off = rva_to_off(dirs[0][0])
        if off is not None and off + 40 <= len(data):
            base, nfunc, nname, funcs_rva, names_rva, ords_rva = struct.unpack_from("<IIIIII", data, off + 16)
            fn_off, name_off, ord_off = map(rva_to_off, (funcs_rva, names_rva, ords_rva))
            name_by_index = {}
            if name_off is not None and ord_off is not None:
                for i in range(min(nname, 100000)):
                    nrva = u32(data, name_off + 4 * i)
                    ix = u16(data, ord_off + 2 * i)
                    no = rva_to_off(nrva)
                    name_by_index[ix] = cstr(data, no or 0)
            if fn_off is not None:
                for i in range(min(nfunc, 100000)):
                    frva = u32(data, fn_off + 4 * i)
                    if frva:
                        exports.append({"ordinal": base + i, "name": name_by_index.get(i), "rva": f"0x{frva:08X}"})

    debug_records = []
    if len(dirs) > 6 and dirs[6][0]:
        off = rva_to_off(dirs[6][0])
        if off is not None:
            for i in range(min(dirs[6][1] // 28, 1024)):
                row = off + i * 28
                if row + 28 > len(data):
                    break
                _, ts, major, minor, typ, size, addr, ptr = struct.unpack_from("<IIHHIIII", data, row)
                item = {"type": typ, "timestamp": ts, "version": f"{major}.{minor}", "size": size}
                if typ == 2 and ptr + size <= len(data):
                    blob = data[ptr:ptr + size]
                    if blob.startswith(b"RSDS") and len(blob) >= 24:
                        guid = blob[4:20]
                        age = u32(blob, 20)
                        pdb = blob[24:].split(b"\0", 1)[0].decode("utf-8", "replace")
                        item.update({"format": "RSDS", "guid_hex": guid.hex(), "age": age, "pdb_path": pdb})
                    elif blob.startswith(b"NB10"):
                        item.update({"format": "NB10", "pdb_path": cstr(blob, 16)})
                debug_records.append(item)

    # The Rich header is a useful toolchain clue, but its absence is not proof
    # of a non-Microsoft toolchain.
    rich = []
    rich_pos = data.find(b"Rich", 0, nt)
    if rich_pos >= 0 and rich_pos + 8 <= len(data):
        key = u32(data, rich_pos + 4)
        dans_sig = struct.pack("<I", 0x536E6144 ^ key)
        dans_pos = data.rfind(dans_sig, 0, rich_pos)
        if dans_pos >= 0:
            pos = dans_pos + 16
            while pos + 8 <= rich_pos:
                comp_xor, count_xor = struct.unpack_from("<II", data, pos)
                comp_id, count = comp_xor ^ key, count_xor ^ key
                if comp_id or count:
                    rich.append({"product_id": comp_id >> 16, "build_id": comp_id & 0xFFFF, "count": count})
                pos += 8

    # Scan only strings that can anchor RTTI or debug/toolchain analysis.
    ascii_runs = [m.group().decode("ascii", "replace") for m in re.finditer(rb"[\x20-\x7e]{4,}", data)]
    rtti_markers = sorted({s for s in ascii_runs if re.search(r"(?:\.?\?_R0|\.?AV|\.?AU|__RTTI|type_info)", s)})
    pdb_strings = sorted({s for s in ascii_runs if s.lower().endswith(".pdb")})

    dlls = [item["dll"] for item in imports]
    directx = [dll for dll in dlls if re.match(r"(?:d3d|ddraw|dinput|dsound|dxguid|d3dx)", dll)]
    crt = [dll for dll in dlls if re.match(r"(?:msvcr|msvcp|ucrt|api-ms-win-crt)", dll)]
    if crt:
        crt_fingerprint = "dynamic CRT imports: " + ", ".join(crt)
    elif any(s.startswith("__") for s in ascii_runs):
        crt_fingerprint = "no recognizable dynamic MSVC CRT import; static/runtime model unresolved"
    else:
        crt_fingerprint = "CRT/runtime linkage unresolved from imports"

    expected = EXPECTED[build]
    sha = hashlib.sha256(data).hexdigest()
    return {
        "build": build,
        "source_relative_path": str(path.relative_to(root)).replace("\\", "/"),
        "size_bytes": len(data), "sha256": sha,
        "expected_sha256": expected,
        "expected_hash_match": sha == expected,
        "pe": {
            "kind": pe_kind, "machine": MACHINE.get(machine, f"0x{machine:04X}"),
            "machine_value": f"0x{machine:04X}", "timestamp_unix": timestamp,
            "timestamp_utc": __import__("datetime").datetime.fromtimestamp(timestamp, __import__("datetime").timezone.utc).isoformat(),
            "characteristics": f"0x{characteristics:04X}",
            "image_base": f"0x{image_base:08X}", "entry_point_rva": f"0x{entry_rva:08X}",
            "entry_point_va": f"0x{image_base + entry_rva:08X}",
            "section_alignment": section_alignment, "file_alignment": file_alignment,
            "size_of_image": size_image, "size_of_headers": size_headers,
            "subsystem": SUBSYSTEM.get(subsystem, f"0x{subsystem:04X}"),
            "dll_characteristics": f"0x{dll_chars:04X}",
            "linker_version": f"{linker_major}.{linker_minor}",
            "sections": sections,
        },
        "imports": imports, "imported_dlls": dlls,
        "exports": exports,
        "debug_directory": debug_records,
        "debug_information_present": bool(debug_records),
        "pdb_path_strings": pdb_strings,
        "rtti_indicators": rtti_markers[:100],
        "rich_header_records": rich,
        "toolchain_fingerprints": {
            "rich_header_present": bool(rich), "linker_version": f"{linker_major}.{linker_minor}",
            "crt": crt_fingerprint, "directx_imports": directx,
            "rtti_marker_count": len(rtti_markers),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", type=Path, help="Corpus root; defaults to ../corpora relative to repository")
    ap.add_argument("--output-dir", type=Path, help="Output directory; defaults to research/r-exe1")
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    corpus = (args.corpora or (repo.parent / "corpora")).resolve()
    out_dir = (args.output_dir or (repo / "research" / "r-exe1")).resolve()
    records = []
    for build, subdir in BUILD_DIRS.items():
        path = corpus / subdir / "MRallye.exe"
        if not path.is_file():
            raise SystemExit(f"Missing corpus executable: {path}")
        records.append(parse_pe(path, corpus, build))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "build-fingerprints.json").write_text(json.dumps({"schema_version": 1, "builds": records}, indent=2) + "\n", encoding="utf-8")
    lines = ["# R-EXE1 executable build fingerprints", "", "All four corpus executables were read in place. No binary was copied or modified.", "", "## Summary", "", "| Build | Size | SHA-256 | PE | Image base | Entry point | Timestamp (UTC) | Hash gate |", "|---|---:|---|---|---:|---:|---|---|"]
    for r in records:
        p = r["pe"]
        lines.append(f"| {r['build']} | {r['size_bytes']:,} | `{r['sha256']}` | {p['kind']} {p['machine']} | `{p['image_base']}` | `{p['entry_point_va']}` | {p['timestamp_utc']} | {'PASS' if r['expected_hash_match'] else 'MISMATCH'} |")
    for r in records:
        p = r["pe"]
        lines += ["", f"## {r['build']}", "", f"- Source: `{r['source_relative_path']}`", f"- Expected hash match: **{r['expected_hash_match']}**", f"- Subsystem: {p['subsystem']}; linker field: {p['linker_version']}; file/section alignment: {p['file_alignment']}/{p['section_alignment']}", f"- Toolchain clues: {r['toolchain_fingerprints']['crt']}; Rich header records={len(r['rich_header_records'])}; debug directory entries={len(r['debug_directory'])}; RTTI-like string candidates={r['toolchain_fingerprints']['rtti_marker_count']}.", f"- DirectX-related imported DLLs: {', '.join(r['toolchain_fingerprints']['directx_imports']) or 'none observed'}.", f"- Imported DLLs: {', '.join(r['imported_dlls']) or 'none'}", f"- Exports: {len(r['exports'])}; debug information present: {r['debug_information_present']}.", "", "### Sections", "", "| Name | RVA | Virtual size | Raw offset | Raw size | Flags |", "|---|---:|---:|---:|---:|---|"]
        for s in p["sections"]:
            lines.append(f"| `{s['name']}` | `{s['virtual_address']}` | {s['virtual_size']:,} | `{s['raw_offset']}` | {s['raw_size']:,} | {', '.join(s['flags'])} |")
        if r["debug_directory"]:
            lines += ["", "### Debug directory", ""]
            for d in r["debug_directory"]:
                lines.append(f"- `{json.dumps(d, sort_keys=True)}`")
        if r["rich_header_records"]:
            lines += ["", "### Rich header records", "", "Record IDs are raw Microsoft Rich-header product/build identifiers; they require cross-build interpretation before assigning compiler names.", ""]
            lines.append("```json")
            lines.append(json.dumps(r["rich_header_records"], indent=2))
            lines.append("```")
    lines += ["", "## Cross-build interpretation", "", "PE timestamps, linker version fields, import sets, section geometry, debug records, Rich headers, and RTTI markers are fingerprints, not stand-alone proof of a compiler release. DirectX generation is reported only from imports and executable evidence; missing imports do not establish absence of dynamically loaded APIs.", ""]
    (out_dir / "build-fingerprints.md").write_text("\n".join(lines), encoding="utf-8")
    if not all(r["expected_hash_match"] for r in records):
        raise SystemExit("At least one executable hash differs from the recorded expected hash")
    print(f"Fingerprinted {len(records)} executables; all expected SHA-256 values match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
