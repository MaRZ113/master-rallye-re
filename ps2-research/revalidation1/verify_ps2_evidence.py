#!/usr/bin/env python3
"""Recheck frozen TREEBLEND1 instruction/data words against canonical ELF bytes.

This validates target identity, ELF32 little-endian MIPS metadata, PT_LOAD VA
mapping, and stored word/anchor bytes. It does not decode MIPS/R5900 semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "treeblend1" / "instruction-evidence.json"
DEFAULT_OUTPUT = ROOT / "revalidation1" / "ps2-elf-byte-recheck.json"
EXPECTED_ELF_SHA256 = "b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_elf(data: bytes) -> dict:
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file or truncated ELF32 header")
    ident = data[:16]
    if ident[4] != 1 or ident[5] != 1:
        raise ValueError("expected ELF32 little-endian input")
    fields = struct.unpack_from("<HHIIIIIHHHHHH", data, 16)
    (etype, machine, version, entry, phoff, shoff, flags, ehsize, phentsize,
     phnum, shentsize, shnum, shstrndx) = fields
    if phentsize < 32 or phoff + phentsize * phnum > len(data):
        raise ValueError("invalid ELF program-header table bounds")
    loads = []
    for index in range(phnum):
        offset = phoff + index * phentsize
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from(
            "<IIIIIIII", data, offset
        )
        if p_type == 1:
            if p_offset + p_filesz > len(data):
                raise ValueError(f"PT_LOAD[{index}] exceeds file bounds")
            loads.append({
                "index": index,
                "file_offset": p_offset,
                "virtual_address": p_vaddr,
                "physical_address": p_paddr,
                "file_size": p_filesz,
                "memory_size": p_memsz,
                "flags": p_flags,
                "alignment": p_align,
            })
    if not loads:
        raise ValueError("ELF contains no PT_LOAD segment")
    return {
        "class": ident[4], "data_encoding": ident[5], "type": etype,
        "machine": machine, "version": version, "entry": entry,
        "flags": flags, "program_header_count": phnum, "load_segments": loads,
    }


def va_to_offset(va: int, loads: list[dict], size: int) -> int:
    matches = [segment for segment in loads
               if segment["virtual_address"] <= va
               and va + size <= segment["virtual_address"] + segment["file_size"]]
    if len(matches) != 1:
        raise ValueError(f"VA 0x{va:08x} maps to {len(matches)} file-backed PT_LOAD ranges")
    segment = matches[0]
    return segment["file_offset"] + va - segment["virtual_address"]


def flatten_windows(value) -> list[dict]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    raise ValueError("unexpected cpu_windows structure")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, help="canonical SLES_509.06 path")
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = args.elf
    if source is None:
        root = os.environ.get("MASTER_RALLYE_PS2_INPUT")
        if not root:
            parser.error("pass --elf or set MASTER_RALLYE_PS2_INPUT")
        source = Path(root) / "SLES_509.06"
    elf_bytes = source.read_bytes()
    elf_hash = digest(elf_bytes)
    if elf_hash != EXPECTED_ELF_SHA256:
        raise SystemExit(f"canonical ELF hash mismatch: {elf_hash}")
    header = parse_elf(elf_bytes)
    if header["type"] != 2 or header["machine"] != 8:
        raise SystemExit("unexpected ELF type or machine for canonical target")

    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    if evidence.get("canonical_elf_sha256") != elf_hash:
        raise SystemExit("evidence file is not bound to the canonical ELF hash")

    verified = 0
    windows = []
    for window in flatten_windows(evidence.get("cpu_windows")):
        instructions = window.get("instructions", [])
        addresses = []
        for instruction in instructions:
            if "original_word" not in instruction:
                continue
            address = int(instruction.get("address", instruction.get("va")), 16)
            expected = int(str(instruction["original_word"]), 16)
            file_offset = va_to_offset(address, header["load_segments"], 4)
            actual = struct.unpack_from("<I", elf_bytes, file_offset)[0]
            if actual != expected:
                raise SystemExit(
                    f"word mismatch at VA 0x{address:08x}: evidence={expected:08x}, file={actual:08x}"
                )
            addresses.append((address, file_offset))
            verified += 1
        if addresses:
            start = min(address for address, _ in addresses)
            end = max(address for address, _ in addresses) + 4
            start_off = va_to_offset(start, header["load_segments"], end - start)
            span = elf_bytes[start_off:start_off + end - start]
            windows.append({
                "role": window.get("role", "UNKNOWN"),
                "va_start": f"0x{start:08x}",
                "va_end_exclusive": f"0x{end:08x}",
                "file_offset": f"0x{start_off:x}",
                "instruction_words_verified": len(addresses),
                "byte_span_sha256": digest(span),
            })

    anchors = []
    for item in evidence.get("data_anchors", []):
        address = int(item["address"], 16)
        expected = bytes.fromhex(item["raw_hex"])
        file_offset = va_to_offset(address, header["load_segments"], len(expected))
        actual = elf_bytes[file_offset:file_offset + len(expected)]
        if actual != expected:
            raise SystemExit(f"data-anchor mismatch at VA 0x{address:08x}")
        anchors.append({
            "role": item.get("role", "UNKNOWN"),
            "va": f"0x{address:08x}",
            "file_offset": f"0x{file_offset:x}",
            "length": len(expected),
            "sha256": digest(actual),
        })

    result = {
        "schema": "ps2-elf-byte-recheck-v1",
        "elf_path_basename": source.name,
        "elf_size": len(elf_bytes),
        "elf_sha256": elf_hash,
        "header": header,
        "va_to_file_mapping": "PT_LOAD file_offset + VA - virtual_address; uniquely file-backed range required",
        "instruction_words_verified": verified,
        "windows": windows,
        "data_anchors_verified": len(anchors),
        "data_anchors": anchors,
        "mismatches": 0,
        "semantic_decode": "NOT_PERFORMED; this is byte/mapping verification only",
        "rea_ps2_analysis": "CAPABILITY_UNAVAILABLE",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "elf_sha256": elf_hash,
        "machine": header["machine"],
        "flags": f"0x{header['flags']:08x}",
        "instruction_words_verified": verified,
        "data_anchors_verified": len(anchors),
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, struct.error, json.JSONDecodeError) as exc:
        print(f"verification error: {exc}", file=sys.stderr)
        raise SystemExit(2)
