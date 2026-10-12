#!/usr/bin/env python3
"""Verify original ELF mapping, frozen TREEBLEND1 words, and fresh Ghidra rows.

This uses Rabbitizer's explicit R5900 instruction category. It does not emulate
the CPU, interpret VU microcode, or turn static code into runtime evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any

EXPECTED_ELF_SHA256 = "b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2"
INS_RE = re.compile(r"^INS\t(0x)?([0-9a-fA-F]+)\t([0-9a-fA-F]+)\t(.*)$")
HEADER_KEYS = {
    "LANGUAGE": "r5900:LE:32:default",
    "COMPILER": "default",
    "BYTE_ORDER": "LE",
    "IMAGE_BASE": "00100000",
}
PROBE_RANGES = [
    ("treeblend_handler", 0x003AE618, 0x003AE670),
    ("tree_handler", 0x003AE710, 0x003AE760),
    ("treeblend_registration", 0x003A7468, 0x003A74D0),
    ("tree_registration", 0x003A75B8, 0x003A7624),
    ("treeblend_gs_template", 0x00313270, 0x003134BC),
    ("tree_initial_test_and_shared_tail", 0x003139BC, 0x00313A4C),
    ("tree_shared_test_zbuf_tail", 0x0031679C, 0x003167D4),
    ("gs_context_register_identity", 0x003411E0, 0x00341260),
    ("source_rgba_unpack", 0x003A7F60, 0x003A7F88),
    ("source_channel_clamp", 0x003401F0, 0x0034022C),
    ("cached_rgba_half_scale", 0x0031F844, 0x0031F9A8),
    ("queue_bucket_outer_setup", 0x0031CE68, 0x0031CEB0),
    ("queue_bucket_increment_and_branch", 0x0031D074, 0x0031D0E0),
    ("queue_insert_setup", 0x0031D250, 0x0031D2C4),
    ("r5900_mult_stride", 0x0031D700, 0x0031D718),
    ("route_a_to_dispatcher", 0x0032FF28, 0x0032FF60),
    ("route_b_to_dispatcher", 0x003301C8, 0x00330200),
    ("dispatcher_to_visitor", 0x003302B8, 0x00330310),
    ("visitor_indirect_drain_call", 0x00330CF4, 0x00330D0C),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_elf32_le(data: bytes) -> dict[str, Any]:
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file or truncated ELF header")
    if data[4] != 1 or data[5] != 1:
        raise ValueError("expected ELF32 little-endian input")
    (etype, machine, version, entry, phoff, _shoff, flags, _ehsize,
     phentsize, phnum, _shentsize, _shnum, _shstrndx) = struct.unpack_from(
        "<HHIIIIIHHHHHH", data, 16
    )
    if phentsize < 32 or phoff + phentsize * phnum > len(data):
        raise ValueError("invalid ELF program-header table")
    loads: list[dict[str, int]] = []
    for idx in range(phnum):
        p = phoff + idx * phentsize
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from(
            "<IIIIIIII", data, p
        )
        if p_type == 1:
            if p_offset + p_filesz > len(data):
                raise ValueError(f"PT_LOAD[{idx}] file range is outside the ELF")
            loads.append({
                "index": idx, "file_offset": p_offset, "virtual_address": p_vaddr,
                "physical_address": p_paddr, "file_size": p_filesz,
                "memory_size": p_memsz, "flags": p_flags, "alignment": p_align,
            })
    if not loads:
        raise ValueError("ELF has no PT_LOAD")
    return {
        "class": 32, "endianness": "little", "type": etype,
        "machine": machine, "version": version, "entry": entry,
        "flags": flags, "program_header_count": phnum, "load_segments": loads,
    }


def va_to_offset(va: int, size: int, loads: list[dict[str, int]]) -> int:
    found = [s for s in loads if s["virtual_address"] <= va
             and va + size <= s["virtual_address"] + s["file_size"]]
    if len(found) != 1:
        raise ValueError(f"VA 0x{va:08x}+0x{size:x} maps to {len(found)} file-backed PT_LOADs")
    seg = found[0]
    return seg["file_offset"] + va - seg["virtual_address"]


def verify_frozen_evidence(data: bytes, header: dict[str, Any], path: Path, rabbitizer: Any) -> dict[str, Any]:
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("canonical_elf_sha256") != EXPECTED_ELF_SHA256:
        raise ValueError("TREEBLEND1 evidence does not name the canonical ELF")
    checked = 0
    invalid: list[dict[str, Any]] = []
    for window in evidence.get("cpu_windows", []):
        for item in window.get("instructions", []):
            if "original_word" not in item:
                continue
            va = int(item.get("address", item.get("va")), 16)
            expected = int(str(item["original_word"]), 16)
            actual = struct.unpack_from("<I", data, va_to_offset(va, 4, header["load_segments"]))[0]
            if actual != expected:
                raise ValueError(f"frozen instruction word differs from ELF at 0x{va:08x}")
            decoded = rabbitizer.Instruction(actual, va, rabbitizer.InstrCategory.R5900)
            if not decoded.isValid():
                invalid.append({"va": f"0x{va:08x}", "word": f"0x{actual:08x}"})
            checked += 1
    if invalid:
        raise ValueError(f"Rabbitizer rejected {len(invalid)} frozen R5900 words")
    return {"word_count": checked, "byte_mismatches": 0, "invalid_r5900_words": 0}


def verify_ghidra_output(data: bytes, header: dict[str, Any], path: Path, rabbitizer: Any) -> dict[str, Any]:
    checked = 0
    byte_mismatches: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    mnemonic_differences: list[dict[str, str]] = []
    addresses: set[int] = set()
    header_values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            key, value = line.split("\t", 1)
            if key in HEADER_KEYS:
                header_values[key] = value
        match = INS_RE.match(line)
        if not match:
            continue
        va = int(match.group(2), 16)
        listed = bytes.fromhex(match.group(3))
        ghidra_text = match.group(4).strip()
        if not listed:
            continue
        offset = va_to_offset(va, len(listed), header["load_segments"])
        actual_bytes = data[offset:offset + len(listed)]
        if actual_bytes != listed:
            byte_mismatches.append({"va": f"0x{va:08x}", "listed": listed.hex(), "actual": actual_bytes.hex()})
            continue
        if len(listed) % 4:
            raise ValueError(f"Ghidra row at 0x{va:08x} is not whole R5900 words")
        for word_index in range(0, len(listed), 4):
            word_va = va + word_index
            word = int.from_bytes(listed[word_index:word_index + 4], "little")
            ins = rabbitizer.Instruction(word, word_va, rabbitizer.InstrCategory.R5900)
            if not ins.isValid():
                invalid.append({"va": f"0x{word_va:08x}", "word": f"0x{word:08x}"})
                continue
            # Ghidra may print a mnemonic alias. Preserve exact spellings, count
            # the differences, and leave semantic adjudication to the byte probe.
            ghidra_mnemonic = ghidra_text.split()[0].lower() if ghidra_text else ""
            rabbitizer_mnemonic = str(ins).split()[0].lower()
            if ghidra_mnemonic and ghidra_mnemonic != rabbitizer_mnemonic:
                mnemonic_differences.append({
                    "va": f"0x{word_va:08x}", "word": f"0x{word:08x}",
                    "ghidra": ghidra_mnemonic, "rabbitizer": rabbitizer_mnemonic,
                })
            addresses.add(word_va)
            checked += 1
    if byte_mismatches:
        raise ValueError(f"{len(byte_mismatches)} Ghidra instruction rows do not match source bytes")
    if invalid:
        raise ValueError(f"Rabbitizer rejected {len(invalid)} fresh R5900 words")
    if header_values != HEADER_KEYS:
        raise ValueError(f"Ghidra program contract differs: expected {HEADER_KEYS}, got {header_values}")
    return {
        "program_contract": header_values,
        "instruction_word_count": checked,
        "unique_instruction_addresses": len(addresses),
        "source_byte_mismatches": 0,
        "invalid_r5900_words": 0,
        "mnemonic_spelling_differences": len(mnemonic_differences),
        "mnemonic_difference_samples": mnemonic_differences[:40],
    }


def parse_listing(path: Path) -> dict[int, tuple[bytes, str]]:
    rows: dict[int, tuple[bytes, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = INS_RE.match(line)
        if match:
            rows[int(match.group(2), 16)] = (bytes.fromhex(match.group(3)), match.group(4).strip())
    return rows


def build_instruction_probes(data: bytes, header: dict[str, Any], listing_path: Path, rabbitizer: Any) -> dict[str, Any]:
    listing = parse_listing(listing_path)
    windows: list[dict[str, Any]] = []
    total = 0
    for name, start, end in PROBE_RANGES:
        instructions = []
        for va in range(start, end, 4):
            offset = va_to_offset(va, 4, header["load_segments"])
            word = struct.unpack_from("<I", data, offset)[0]
            ins = rabbitizer.Instruction(word, va, rabbitizer.InstrCategory.R5900)
            if not ins.isValid():
                raise ValueError(f"Rabbitizer rejected probe word at 0x{va:08x}")
            raw, ghidra_text = listing.get(va, (b"", ""))
            if raw and raw[:4] != data[offset:offset + 4]:
                raise ValueError(f"Ghidra bytes disagree with the ELF at 0x{va:08x}")
            instructions.append({
                "va": f"0x{va:08x}",
                "file_offset": f"0x{offset:x}",
                "word": f"0x{word:08x}",
                "rabbitizer_r5900": str(ins),
                "ghidra_listing": ghidra_text or None,
            })
            total += 1
        windows.append({"name": name, "start_va": f"0x{start:08x}", "end_va_exclusive": f"0x{end:08x}", "instructions": instructions})
    return {
        "schema": "ps2-r5900-revalidation2-instruction-probes-v1",
        "canonical_elf_sha256": EXPECTED_ELF_SHA256,
        "decoder": "Rabbitizer 1.16.2 InstrCategory.R5900",
        "instruction_count": total,
        "windows": windows,
        "scope_note": "Compact byte-backed CPU instruction probes only; no VU microinstruction semantics or runtime execution implied.",
    }


def verify_instruction_probes(data: bytes, header: dict[str, Any], path: Path, rabbitizer: Any) -> dict[str, int]:
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("canonical_elf_sha256") != EXPECTED_ELF_SHA256:
        raise ValueError("instruction probes do not name the canonical ELF")
    checked = 0
    for window in evidence.get("windows", []):
        for item in window.get("instructions", []):
            va = int(item["va"], 16)
            offset = va_to_offset(va, 4, header["load_segments"])
            actual = struct.unpack_from("<I", data, offset)[0]
            expected = int(item["word"], 16)
            if actual != expected:
                raise ValueError(f"instruction probe word differs at 0x{va:08x}")
            ins = rabbitizer.Instruction(actual, va, rabbitizer.InstrCategory.R5900)
            if not ins.isValid():
                raise ValueError(f"invalid R5900 instruction in probe at 0x{va:08x}")
            if str(ins) != item["rabbitizer_r5900"]:
                raise ValueError(f"Rabbitizer decode changed at 0x{va:08x}")
            checked += 1
    if checked != evidence.get("instruction_count"):
        raise ValueError("instruction probe count does not match its metadata")
    return {"instruction_count": checked, "byte_mismatches": 0, "invalid_r5900_words": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, required=True)
    parser.add_argument("--ghidra-output", type=Path, required=True)
    parser.add_argument("--frozen-evidence", type=Path, default=Path(__file__).resolve().parents[2] / "treeblend1" / "instruction-evidence.json")
    parser.add_argument("--instruction-probes", type=Path, default=Path(__file__).resolve().parent / "instruction-probes.json")
    parser.add_argument("--emit-instruction-probes", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    elf = args.elf.read_bytes()
    digest = sha256(elf)
    if digest != EXPECTED_ELF_SHA256:
        raise ValueError(f"canonical ELF SHA-256 mismatch: {digest}")
    header = parse_elf32_le(elf)
    if (header["type"], header["machine"], header["entry"], header["flags"]) != (2, 8, 0x00100008, 0x20924001):
        raise ValueError("canonical ELF header differs from the expected R5900 contract")
    loads = header["load_segments"]
    if len(loads) != 1 or loads[0] != {
        "index": 0, "file_offset": 0x1000, "virtual_address": 0x00100000,
        "physical_address": 0x00100000, "file_size": 0x38D490,
        "memory_size": 0x3D9978, "flags": 7, "alignment": 0x1000,
    }:
        raise ValueError("canonical ELF PT_LOAD differs from the established source map")

    rabbitizer_version = importlib.metadata.version("rabbitizer")
    if rabbitizer_version != "1.16.2":
        raise ValueError(f"expected Rabbitizer 1.16.2, found {rabbitizer_version}")
    import rabbitizer

    frozen = verify_frozen_evidence(elf, header, args.frozen_evidence, rabbitizer)
    ghidra = verify_ghidra_output(elf, header, args.ghidra_output, rabbitizer)
    probes = build_instruction_probes(elf, header, args.ghidra_output, rabbitizer)
    if args.emit_instruction_probes:
        args.emit_instruction_probes.parent.mkdir(parents=True, exist_ok=True)
        args.emit_instruction_probes.write_text(json.dumps(probes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    probe_result = verify_instruction_probes(elf, header, args.instruction_probes, rabbitizer) if args.instruction_probes.is_file() else None
    if args.instruction_probes.is_file() and args.emit_instruction_probes:
        probe_result = verify_instruction_probes(elf, header, args.emit_instruction_probes, rabbitizer)
    if not args.instruction_probes.is_file() and not args.emit_instruction_probes:
        raise ValueError("instruction probes are missing; use --emit-instruction-probes once to create the frozen compact probe")
    report = {
        "schema": "ps2-r5900-revalidation2-byte-check-v1",
        "canonical_elf": {"basename": args.elf.name, "size": len(elf), "sha256": digest, "format": "ELF32 LE ET_EXEC EM_MIPS R5900"},
        "elf_header": header,
        "va_to_file": "unique file-backed PT_LOAD only: p_offset + VA - p_vaddr",
        "r5900_decoder": {"name": "Rabbitizer", "version": rabbitizer_version, "category": "InstrCategory.R5900"},
        "frozen_treeblend": frozen,
        "fresh_ghidra_listing": ghidra,
        "fresh_instruction_probes": probe_result or {"instruction_count": probes["instruction_count"], "generated": True},
        "scope_note": "Checks source byte mapping and supported R5900 decoding; no execution or live graphics state is implied.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS", "elf_sha256": digest,
        "frozen_words": frozen["word_count"],
        "ghidra_words": ghidra["instruction_word_count"],
        "ghidra_byte_mismatches": ghidra["source_byte_mismatches"],
        "rabbitizer_valid": True,
        "mnemonic_spelling_differences": ghidra["mnemonic_spelling_differences"],
        "phase_probe_words": probe_result["instruction_count"] if probe_result else probes["instruction_count"],
        "report": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, struct.error, json.JSONDecodeError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
