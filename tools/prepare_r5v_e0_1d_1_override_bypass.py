"""Build the ABI-correct, slot-0-only colour-override diagnostic executable.

The only supported input is the tested E0 Trooper/SmallCarSheet29 baseline
executable (the XML-red archive is paired separately). The retail executable
is never an input or output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


BASELINE_SHA256 = "e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df"
XML_RED_DATA_SHA256 = "10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072"
IMAGE_BASE = 0x400000
HOOK_VA = 0x4A7661
EXISTS_GETTER_VA = 0x4D7470
HELPER_VA = 0x68E300
TEXT_VIRTUAL_SIZE_OLD = 0x28D300
TEXT_VIRTUAL_SIZE_NEW = 0x28D310
TEXT_RAW_SIZE = 0x28E000
TEXT_RVA = 0x1000
RDATA_RVA = 0x28F000
CALL_SITE_ORIGINAL = bytes.fromhex(
    "52 E8 61 18 03 00 8B C8 E8 0A FE 02 00 84 C0 74 36"
)
HOOK_ORIGINAL = bytes.fromhex("E8 0A FE 02 00")
STUB_PREFIX = bytes.fromhex("83 7E 18 00 75 05 33 C0 C2 04 00 E9")
STUB_SIZE = len(STUB_PREFIX) + 4
OUTPUT_ROOT = (Path(__file__).resolve().parents[1]
               / "research-output" / "r5v_e0_1d_1" / "override-bypass")
OUTPUT_NAME = "MRallye_slot25_trooper_smallsheet29_xmlred_colour-bypass-abi-safe.exe"


class PatchError(ValueError):
    """The input does not match the reviewed E0 baseline or a safety check failed."""


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
            or text["rva"] != TEXT_RVA or text["raw_offset"] != 0x1000
            or text["raw_size"] != TEXT_RAW_SIZE
            or text["characteristics"] != 0x60000020
            or rdata["rva"] != RDATA_RVA):
        raise PatchError("Unexpected E0 baseline PE section layout")
    if text["rva"] + text["virtual_size"] != HELPER_VA - IMAGE_BASE:
        raise PatchError("The helper must begin at the original .text virtual end")
    if text["rva"] + TEXT_VIRTUAL_SIZE_NEW >= rdata["rva"]:
        raise PatchError("Extended .text would overlap .rdata")
    if HELPER_VA - IMAGE_BASE + STUB_SIZE > text["rva"] + TEXT_VIRTUAL_SIZE_NEW:
        raise PatchError("The helper bytes would exceed the extended .text virtual size")
    if HELPER_VA - IMAGE_BASE + STUB_SIZE > text["rva"] + text["raw_size"]:
        raise PatchError("The helper bytes are not fully backed by .text raw data")
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


def _relative_instruction(opcode: int, instruction_va: int, target_va: int) -> bytes:
    displacement = target_va - (instruction_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise PatchError("Relative branch target is out of range")
    return bytes((opcode,)) + struct.pack("<i", displacement)


def build_stub(helper_va: int = HELPER_VA,
               target_va: int = EXISTS_GETTER_VA) -> bytes:
    """Encode compare; JNE tail-jump; XOR EAX; RET 4; JMP original getter."""
    jmp_va = helper_va + len(STUB_PREFIX) - 1
    stub = STUB_PREFIX + _relative_instruction(0xE9, jmp_va, target_va)[1:]
    if len(stub) != STUB_SIZE:
        raise AssertionError("Internal stub-size mismatch")
    branch_target = helper_va + 6 + struct.unpack("b", stub[5:6])[0]
    if branch_target != jmp_va:
        raise AssertionError("JNE does not land on the original-function tail jump")
    return stub


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


def validate_paths(source_path: Path, output_path: Path,
                   manifest_path: Path, diff_path: Path) -> None:
    resolved = [source_path.resolve(), output_path.resolve(),
                manifest_path.resolve(), diff_path.resolve()]
    if len(set(resolved)) != len(resolved):
        raise PatchError("source, output, manifest, and diff must use distinct paths")
    output_root = OUTPUT_ROOT.resolve()
    for path in resolved[1:]:
        if not path.is_relative_to(output_root):
            raise PatchError(f"outputs must remain under {output_root}")


def build_candidate(source: bytes) -> tuple[bytes, list[dict]]:
    if sha256(source) != BASELINE_SHA256:
        raise PatchError("Input SHA-256 does not match the tested E0 baseline candidate")
    pe = parse_pe(source)
    callsite_offset = va_to_file_offset(pe, 0x4A7659, len(CALL_SITE_ORIGINAL))
    if source[callsite_offset:callsite_offset + len(CALL_SITE_ORIGINAL)] != CALL_SITE_ORIGINAL:
        raise PatchError("Consumer call-site ABI bytes do not match retail evidence")
    hook_offset = va_to_file_offset(pe, HOOK_VA, len(HOOK_ORIGINAL))
    if source[hook_offset:hook_offset + len(HOOK_ORIGINAL)] != HOOK_ORIGINAL:
        raise PatchError("Colour consumer call bytes do not match retail evidence")
    stub_offset = va_to_file_offset(pe, HELPER_VA, STUB_SIZE)
    if source[stub_offset:stub_offset + STUB_SIZE] != bytes(STUB_SIZE):
        raise PatchError("Expected zero-filled 16-byte .text tail at the helper address")

    text = pe["sections"][0]
    virtual_size_offset = text["header"] + 8
    if _u32(source, virtual_size_offset) != TEXT_VIRTUAL_SIZE_OLD:
        raise PatchError("Unexpected .text VirtualSize field")

    stub = build_stub()
    result = bytearray(source)
    result[hook_offset:hook_offset + len(HOOK_ORIGINAL)] = _relative_instruction(0xE8, HOOK_VA, HELPER_VA)
    result[stub_offset:stub_offset + STUB_SIZE] = stub
    struct.pack_into("<I", result, virtual_size_offset, TEXT_VIRTUAL_SIZE_NEW)
    candidate = bytes(result)

    callsite_offset = va_to_file_offset(pe, 0x4A7659, len(CALL_SITE_ORIGINAL))
    if candidate[callsite_offset:callsite_offset + len(CALL_SITE_ORIGINAL)] != (
            CALL_SITE_ORIGINAL[:HOOK_VA - 0x4A7659]
            + _relative_instruction(0xE8, HOOK_VA, HELPER_VA)
            + CALL_SITE_ORIGINAL[HOOK_VA - 0x4A7659 + len(HOOK_ORIGINAL):]):
        raise PatchError("Unexpected change to the surrounding consumer call sequence")

    allowed = (set(range(hook_offset, hook_offset + len(HOOK_ORIGINAL)))
               | set(range(stub_offset, stub_offset + STUB_SIZE))
               | set(range(virtual_size_offset, virtual_size_offset + 4)))
    changed = {index for index, pair in enumerate(zip(source, candidate)) if pair[0] != pair[1]}
    if not changed <= allowed:
        raise PatchError("Candidate contains a change outside the approved hook, helper, and section-size ranges")
    return candidate, _changed_ranges(source, candidate)


def make_manifest(source_path: Path, output_path: Path, before: bytes,
                  after: bytes, changed_ranges: list[dict]) -> dict:
    pe = parse_pe(before)
    text = pe["sections"][0]
    return {
        "phase": "R5V-E0.1d.1",
        "purpose": "ABI-correct diagnostic bypass of Race/Car0/Colour existence override",
        "source_path": str(source_path),
        "source_sha256": sha256(before),
        "output_path": str(output_path),
        "output_sha256": sha256(after),
        "source_bytes": len(before),
        "output_bytes": len(after),
        "paired_xml_red_data_sha256": XML_RED_DATA_SHA256,
        "runtime_status": "NOT RUN; await owner test in isolated game copy",
        "abi_contract": {
            "consumer_stack_argument": "PUSH EDX at 0x004A7659; remains at [ESP+4] when FUN_004D7470 is entered",
            "property_lookup": "FUN_004D8EC0 returns with plain RET and leaves the pushed argument for the next call",
            "exists_getter": "FUN_004D7470 receives ECX object pointer, reads [ESP+4], returns AL and executes RET 4",
            "slot_zero": "XOR EAX,EAX; RET 4 cleans the original stack argument and returns false",
            "other_slots": "JMP 0x004D7470 preserves ECX and the original stack layout; no nested CALL",
        },
        "operations": [
            {
                "va": f"0x{HOOK_VA:08X}",
                "file_offset": f"0x{va_to_file_offset(pe, HOOK_VA, 5):X}",
                "original": HOOK_ORIGINAL.hex(" "),
                "replacement": _relative_instruction(0xE8, HOOK_VA, HELPER_VA).hex(" "),
                "scope": "Redirect the exists query through the display-slot test; continuation remains 0x004A7666.",
            },
            {
                "va": f"0x{HELPER_VA:08X}",
                "file_offset": f"0x{va_to_file_offset(pe, HELPER_VA, STUB_SIZE):X}",
                "original": bytes(STUB_SIZE).hex(" "),
                "replacement": build_stub().hex(" "),
                "scope": "Slot 0 returns false with RET 4; nonzero slots tail-jump to the original getter.",
            },
            {
                "location": "PE section header .text.VirtualSize",
                "file_offset": f"0x{text['header'] + 8:X}",
                "original": f"0x{text['virtual_size']:08X}",
                "replacement": f"0x{TEXT_VIRTUAL_SIZE_NEW:08X}",
                "scope": "Expose exactly 16 existing file-backed tail bytes; section remains before .rdata.",
            },
        ],
        "changed_byte_ranges": changed_ranges,
    }


def format_binary_diff(manifest: dict) -> str:
    lines = [
        "R5V-E0.1d.1 corrected colour bypass binary diff",
        f"Source SHA-256: {manifest['source_sha256']}",
        f"Candidate SHA-256: {manifest['output_sha256']}",
        "Only the exists-query call, the new helper, and .text.VirtualSize change.",
        "",
    ]
    labels = {
        "0x004A7661": "redirect consumer exists-query call to diagnostic helper",
        "0x0068E300": "ABI-correct helper bytes in previously zero-filled .text tail",
        "PE section header .text.VirtualSize": "expose 16 helper bytes without overlapping .rdata",
    }
    operations = manifest["operations"]
    for operation in operations:
        if "va" in operation:
            key = operation["va"]
            label = labels[key]
        else:
            label = labels[operation["location"]]
        lines.append(f"{operation.get('va', operation.get('location'))} ({operation['file_offset']}): {label}")
        lines.append(f"  {operation['original']} -> {operation['replacement']}")
    lines.extend(("", "Exact byte ranges:"))
    for item in manifest["changed_byte_ranges"]:
        lines.append(f"  file 0x{item['offset']:X}, length 0x{item['length']:X}: {item['before']} -> {item['after']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--diff", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    source_path = args.source.resolve()
    output_path = args.output.resolve()
    manifest_path = args.manifest.resolve()
    diff_path = args.diff.resolve()
    try:
        validate_paths(source_path, output_path, manifest_path, diff_path)
    except PatchError as exc:
        parser.error(str(exc))
    if not source_path.is_file():
        parser.error(f"source file does not exist: {source_path}")
    if not args.dry_run and any(path.exists() for path in (output_path, manifest_path, diff_path)):
        parser.error("refusing to overwrite an existing output, manifest, or diff")

    before = source_path.read_bytes()
    after, ranges = build_candidate(before)
    manifest = make_manifest(source_path, output_path, before, after, ranges)
    diff = format_binary_diff(manifest)
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        print(diff)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(after)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    diff_path.write_text(diff, encoding="utf-8")
    if sha256(source_path.read_bytes()) != BASELINE_SHA256:
        for generated in (output_path, manifest_path, diff_path):
            generated.unlink(missing_ok=True)
        raise PatchError("Source changed during candidate creation; generated outputs removed")
    print(json.dumps(manifest, indent=2))
    print(diff)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
