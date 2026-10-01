"""Build a slot-0-only Race/CarN/Colour bypass diagnostic executable.

The only supported input is the human-tested R5V-E0 baseline candidate with
SHA-256 BASELINE_SHA256. The retail executable is never an input or output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


BASELINE_SHA256 = "e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df"
IMAGE_BASE = 0x400000
HOOK_VA = 0x4A7661
EXISTS_GETTER_VA = 0x4D7470
HELPER_VA = 0x68E300
TEXT_VIRTUAL_SIZE_OLD = 0x28D300
TEXT_VIRTUAL_SIZE_NEW = 0x28D310
HOOK_ORIGINAL = bytes.fromhex("E8 0A FE 02 00")
STUB_PREFIX = bytes.fromhex("83 7E 18 00 75 03 33 C0 C3")
STUB_SUFFIX = b"\xC3"
STUB_SIZE = len(STUB_PREFIX) + 5 + len(STUB_SUFFIX)
OUTPUT_ROOT = (Path(__file__).resolve().parents[1]
               / "research-output" / "r5v_e0_1d" / "override-bypass")


class PatchError(ValueError):
    """The input is not the expected E0 baseline or a safety check failed."""


def _u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_pe(data: bytes) -> dict:
    if len(data) < 0x400 or data[:2] != b"MZ":
        raise PatchError("Missing DOS/PE header")
    pe_offset = _u32(data, 0x3C)
    if pe_offset + 0x108 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise PatchError("Missing PE signature")
    coff = pe_offset + 4
    if _u16(data, coff) != 0x14C or _u16(data, coff + 2) != 4:
        raise PatchError("Expected 32-bit x86 PE with four sections")
    optional = coff + 20
    optional_size = _u16(data, coff + 16)
    if optional_size != 0xE0 or _u16(data, optional) != 0x10B:
        raise PatchError("Unexpected PE32 optional header")
    if _u32(data, optional + 28) != IMAGE_BASE:
        raise PatchError("Unexpected image base")
    if (_u32(data, optional + 32) != 0x1000
            or _u32(data, optional + 36) != 0x1000
            or _u32(data, optional + 56) != 0x311000):
        raise PatchError("Unexpected section alignment or image size")

    section_table = optional + optional_size
    sections = []
    for index in range(4):
        header = section_table + index * 40
        sections.append({
            "name": data[header:header + 8].split(b"\0", 1)[0].decode("ascii"),
            "header": header,
            "virtual_size": _u32(data, header + 8),
            "rva": _u32(data, header + 12),
            "raw_size": _u32(data, header + 16),
            "raw_offset": _u32(data, header + 20),
            "characteristics": _u32(data, header + 36),
        })
    text, rdata, data_section, resources = sections
    if ([item["name"] for item in sections] != [".text", ".rdata", ".data", ".rsrc"]
            or text["virtual_size"] != TEXT_VIRTUAL_SIZE_OLD
            or text["rva"] != 0x1000 or text["raw_offset"] != 0x1000
            or text["raw_size"] != 0x28E000
            or text["characteristics"] != 0x60000020
            or rdata["rva"] != 0x28F000):
        raise PatchError("Unexpected E0 baseline PE section layout")
    if text["rva"] + TEXT_VIRTUAL_SIZE_NEW >= rdata["rva"]:
        raise PatchError("Extended .text would overlap .rdata")
    return {"image_base": IMAGE_BASE, "sections": sections}


def va_to_file_offset(pe: dict, va: int, size: int = 1) -> int:
    rva = va - pe["image_base"]
    if size < 1 or rva < 0:
        raise PatchError("Invalid virtual address")
    for section in pe["sections"]:
        start = section["rva"]
        if start <= rva and rva + size <= start + section["raw_size"]:
            offset = section["raw_offset"] + rva - start
            if offset + size <= section["raw_offset"] + section["raw_size"]:
                return offset
    raise PatchError(f"VA 0x{va:X} is not backed by section bytes")


def _rel32_call(call_va: int, target_va: int) -> bytes:
    displacement = target_va - (call_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise PatchError("Relative call target is out of range")
    return b"\xE8" + struct.pack("<i", displacement)


def _changed_ranges(before: bytes, after: bytes) -> list[dict]:
    offsets = [index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1]]
    ranges: list[dict] = []
    for offset in offsets:
        if not ranges or offset != ranges[-1]["offset"] + ranges[-1]["length"]:
            ranges.append({"offset": offset, "length": 1})
        else:
            ranges[-1]["length"] += 1
    for item in ranges:
        offset = item["offset"]
        length = item["length"]
        item["before"] = before[offset:offset + length].hex(" ")
        item["after"] = after[offset:offset + length].hex(" ")
    return ranges


def validate_paths(source_path: Path, output_path: Path, manifest_path: Path) -> None:
    if source_path == output_path or source_path == manifest_path or output_path == manifest_path:
        raise PatchError("source, output, and manifest must use distinct paths")
    output_root = OUTPUT_ROOT.resolve()
    if not output_path.is_relative_to(output_root) or not manifest_path.is_relative_to(output_root):
        raise PatchError(f"outputs must remain under {output_root}")


def build_candidate(source: bytes) -> tuple[bytes, list[dict]]:
    if sha256(source) != BASELINE_SHA256:
        raise PatchError("Input SHA-256 does not match the tested E0 baseline candidate")
    pe = parse_pe(source)
    hook_offset = va_to_file_offset(pe, HOOK_VA, len(HOOK_ORIGINAL))
    if source[hook_offset:hook_offset + len(HOOK_ORIGINAL)] != HOOK_ORIGINAL:
        raise PatchError("Colour consumer call bytes do not match retail evidence")
    stub_offset = va_to_file_offset(pe, HELPER_VA, STUB_SIZE)
    if source[stub_offset:stub_offset + STUB_SIZE] != bytes(STUB_SIZE):
        raise PatchError("Expected zero-filled .text tail at the helper address")

    text = pe["sections"][0]
    virtual_size_offset = text["header"] + 8
    if _u32(source, virtual_size_offset) != TEXT_VIRTUAL_SIZE_OLD:
        raise PatchError("Unexpected .text VirtualSize field")

    stub_call_va = HELPER_VA + len(STUB_PREFIX)
    stub = STUB_PREFIX + _rel32_call(stub_call_va, EXISTS_GETTER_VA) + STUB_SUFFIX
    if len(stub) != STUB_SIZE:
        raise AssertionError("Internal stub-size mismatch")
    result = bytearray(source)
    result[hook_offset:hook_offset + len(HOOK_ORIGINAL)] = _rel32_call(HOOK_VA, HELPER_VA)
    result[stub_offset:stub_offset + len(stub)] = stub
    struct.pack_into("<I", result, virtual_size_offset, TEXT_VIRTUAL_SIZE_NEW)
    candidate = bytes(result)

    allowed = (set(range(hook_offset, hook_offset + len(HOOK_ORIGINAL)))
               | set(range(stub_offset, stub_offset + STUB_SIZE))
               | set(range(virtual_size_offset, virtual_size_offset + 4)))
    changed = {index for index, pair in enumerate(zip(source, candidate)) if pair[0] != pair[1]}
    if not changed <= allowed:
        raise PatchError("Candidate contains a change outside the three approved patch ranges")
    return candidate, _changed_ranges(source, candidate)


def make_manifest(source_path: Path, output_path: Path, before: bytes,
                  after: bytes, changed_ranges: list[dict]) -> dict:
    pe = parse_pe(before)
    text = pe["sections"][0]
    return {
        "phase": "R5V-E0.1d",
        "purpose": "Diagnostic bypass of Race/Car%d/Colour existence override for HUD display slot 0",
        "source_path": str(source_path),
        "source_sha256": sha256(before),
        "output_path": str(output_path),
        "output_sha256": sha256(after),
        "source_bytes": len(before),
        "output_bytes": len(after),
        "runtime_status": "NOT RUN; owner runtime result required",
        "operations": [
            {
                "va": f"0x{HOOK_VA:08X}",
                "file_offset": f"0x{va_to_file_offset(pe, HOOK_VA, 5):X}",
                "original": HOOK_ORIGINAL.hex(" "),
                "replacement": _rel32_call(HOOK_VA, HELPER_VA).hex(" "),
                "scope": "Redirects the colour-property-exists query through the slot test.",
            },
            {
                "va": f"0x{HELPER_VA:08X}",
                "file_offset": f"0x{va_to_file_offset(pe, HELPER_VA, STUB_SIZE):X}",
                "original": bytes(STUB_SIZE).hex(" "),
                "replacement": (STUB_PREFIX + _rel32_call(HELPER_VA + len(STUB_PREFIX), EXISTS_GETTER_VA)
                               + STUB_SUFFIX).hex(" "),
                "scope": "If [ESI+0x18] is 0 return false; otherwise call original getter and preserve its result.",
            },
            {
                "location": "PE section header .text.VirtualSize",
                "file_offset": f"0x{text['header'] + 8:X}",
                "original": f"0x{text['virtual_size']:08X}",
                "replacement": f"0x{TEXT_VIRTUAL_SIZE_NEW:08X}",
                "scope": "Expose 16 bytes of the existing file-backed .text tail; no section overlap.",
            },
        ],
        "changed_byte_ranges": changed_ranges,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    source_path = args.source.resolve()
    output_path = args.output.resolve()
    manifest_path = args.manifest.resolve()
    try:
        validate_paths(source_path, output_path, manifest_path)
    except PatchError as exc:
        parser.error(str(exc))
    if not source_path.is_file():
        parser.error(f"source file does not exist: {source_path}")
    if not args.dry_run and (output_path.exists() or manifest_path.exists()):
        parser.error("refusing to overwrite an existing output or manifest")

    before = source_path.read_bytes()
    after, ranges = build_candidate(before)
    manifest = make_manifest(source_path, output_path, before, after, ranges)
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(after)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if sha256(source_path.read_bytes()) != BASELINE_SHA256:
        output_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise PatchError("Source changed during candidate creation; generated outputs removed")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
