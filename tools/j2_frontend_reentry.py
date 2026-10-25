#!/usr/bin/env python3
"""Build/verify the bounded J.2 Vehicle Select re-entry runtime bundle.

This is a derivative of the independently verified J.1 bundle. It leaves the
J.1 bundle, launcher source, retail executable and stock resources untouched.
The J.2 composite corrects one faulty ID27 reverse-map field displacement,
then republishes the final scene object's class/local coordinates to the
existing XYButton Broker paths after native saved-vehicle restoration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import addon_runtime  # noqa: E402


RETAIL_EXE = addon_runtime.DEFAULT_RETAIL_EXE
J1_BUNDLE = addon_runtime.DEFAULT_OUTPUT
J1_PACKAGE = addon_runtime.DEFAULT_I1_PACKAGE
J2_BUNDLE = PROJECT_ROOT / ".research-output/vehicles/sdk/j2-reentry/repaired-candidate"
J2_PROFILE = "r5v-j2-vehicle-select-reentry-two-addon-retail-2001"

# Exact-build native owner and audited constructor convergence.
IMAGE_BASE = 0x00400000
HOOK_VA = 0x00481152
HOOK_RVA = HOOK_VA - IMAGE_BASE
CONTINUATION_VA = 0x00481157
STUB_VA = 0x0068EB40
STUB_RVA = STUB_VA - IMAGE_BASE
EXPECTED_HOOK = bytes.fromhex("68f8746b00")  # PUSH "Frontend/VehicleSelect/VehicleList"
YVALUE_PATH_VA = 0x006B4184  # UI/XYButton/YValue
XVALUE_PATH_VA = 0x006B4198  # UI/XYButton/XValue
VEHICLE_LIST_PATH_VA = 0x006B74F8
BROKER_PATH_INIT_VA = 0x004D0580
BROKER_VALUE_GET_VA = 0x004D8EC0
BROKER_VALUE_SET_VA = 0x004D8000
STUB_ORIGINAL_FILL = 0x00
BROKER_PATH_INIT_STACK_CLEANUP = 4  # 0x004D0580 ends in RET 4
BROKER_VALUE_GET_STACK_CLEANUP = 0  # 0x004D8EC0 ends in RET
BROKER_VALUE_SET_STACK_CLEANUP = 8  # 0x004D8000 ends in RET 8
BROKER_PATH_OBJECT_OFFSET = 0x14  # native constructor LEA at 0x00481130
ID27_REVERSE_MAP_VA = 0x0068E880
ID27_REVERSE_MAP_STOCK_FALLBACK_VA = 0x0068E8A1
ID27_REVERSE_LOCAL_STORE_VA = 0x0068E895
ID27_REVERSE_LOCAL_STORE_FILE_OFFSET = ID27_REVERSE_LOCAL_STORE_VA - IMAGE_BASE
ID27_REVERSE_LOCAL_STORE_EXPECTED = bytes.fromhex("c7461407")
ID27_REVERSE_LOCAL_STORE_FIXED = bytes.fromhex("c7461807")

RVP_HEADER = addon_runtime.RVP_HEADER
RVP_OPERATION = addon_runtime.RVP_OPERATION
PAGE_CODE = 1
PAGE_DATA = 2
FLAG_PROCESS = 0
FLAG_FILE_ONLY = 1
FLAG_NOOP = 2
PHYSICAL_TO_CLASS_LOCAL = {
    **{car_id: (0, car_id) for car_id in range(7)},
    **{car_id: (1, car_id - 7) for car_id in range(7, 14)},
    **{car_id: (2, car_id - 14) for car_id in range(14, 26)},
    26: (0, 7),
    27: (1, 7),
}


class ReentryBundleError(ValueError):
    """The retail image, J.1 parent or derived J.2 candidate is unsafe."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel32(opcode: int, target: int, instruction_va: int) -> bytes:
    displacement = target - (instruction_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise ReentryBundleError("relative branch target is out of x86 rel32 range")
    return bytes((opcode,)) + struct.pack("<i", displacement)


def _decode_republish_stub(stub: bytes, *, stub_va: int = STUB_VA) -> list[tuple[str, int | None, int]]:
    """Decode only the audited instruction forms emitted by the J.2 stub."""
    decoded: list[tuple[str, int | None, int]] = []
    cursor = 0
    while cursor < len(stub):
        start = cursor
        opcode = stub[cursor]
        if opcode in (0x9C, 0x9D):
            decoded.append(("pushfd" if opcode == 0x9C else "popfd", None, start))
            cursor += 1
        elif opcode == 0x68 and cursor + 5 <= len(stub):
            decoded.append(("push_imm", struct.unpack_from("<I", stub, cursor + 1)[0], start))
            cursor += 5
        elif stub[cursor:cursor + 3] == b"\x8d\x4c\x24" and cursor + 4 <= len(stub):
            decoded.append(("lea_ecx_esp", stub[cursor + 3], start))
            cursor += 4
        elif opcode in (0xE8, 0xE9) and cursor + 5 <= len(stub):
            displacement = struct.unpack_from("<i", stub, cursor + 1)[0]
            target = stub_va + cursor + 5 + displacement
            decoded.append(("call" if opcode == 0xE8 else "jmp", target, start))
            cursor += 5
        elif stub[cursor:cursor + 3] == b"\x8b\x47\x10":
            decoded.append(("mov_eax_class", None, start))
            cursor += 3
        elif stub[cursor:cursor + 3] == b"\x8b\x57\x10":
            decoded.append(("mov_edx_class", None, start))
            cursor += 3
        elif stub[cursor:cursor + 4] == b"\x8b\x44\x97\x14":
            decoded.append(("mov_eax_local", None, start))
            cursor += 4
        elif stub[cursor:cursor + 2] == b"\x8b\xc8":
            decoded.append(("mov_ecx_eax", None, start))
            cursor += 2
        elif opcode == 0x50:
            decoded.append(("push_eax", None, start))
            cursor += 1
        elif opcode == 0x51:
            decoded.append(("push_ecx", None, start))
            cursor += 1
        else:
            raise ReentryBundleError(
                f"unsupported J.2 stub instruction at +0x{cursor:x}: {stub[cursor:cursor + 8].hex()}")
    return decoded


def verify_republish_stub(stub: bytes, *, stub_va: int = STUB_VA) -> dict[str, Any]:
    """Symbolically execute actual emitted bytes under the audited native ABIs."""
    instructions = _decode_republish_stub(stub, stub_va=stub_va)
    expected_shape = [
        ("pushfd", None),
        ("push_imm", YVALUE_PATH_VA), ("lea_ecx_esp", 0x1C), ("call", BROKER_PATH_INIT_VA),
        ("mov_eax_class", None), ("lea_ecx_esp", 0x18), ("push_eax", None), ("push_ecx", None),
        ("call", BROKER_VALUE_GET_VA), ("mov_ecx_eax", None), ("call", BROKER_VALUE_SET_VA),
        ("push_imm", XVALUE_PATH_VA), ("lea_ecx_esp", 0x1C), ("call", BROKER_PATH_INIT_VA),
        ("mov_edx_class", None), ("lea_ecx_esp", 0x18), ("mov_eax_local", None),
        ("push_eax", None), ("push_ecx", None), ("call", BROKER_VALUE_GET_VA),
        ("mov_ecx_eax", None), ("call", BROKER_VALUE_SET_VA), ("popfd", None),
        ("push_imm", VEHICLE_LIST_PATH_VA), ("jmp", CONTINUATION_VA),
    ]
    if [(mnemonic, operand) for mnemonic, operand, _ in instructions] != expected_shape:
        raise ReentryBundleError("stub instruction order or operands differ from the audited ABI template")
    esp = 0  # entry ESP = S
    stack: dict[int, Any] = {}
    eax: Any = None
    ecx: Any = None
    edx: Any = None
    flags_saved = False
    initialized: list[tuple[int, int]] = []
    calls: list[int] = []
    pushed_writes: list[int] = []
    sequence = 0
    pending_path: int | None = None
    pending_value: Any = None
    saw_replay_push = False
    saw_jump = False

    def push(value: Any) -> None:
        nonlocal esp
        esp -= 4
        stack[esp] = value
        pushed_writes.append(esp)

    def emulate_call(target: int, cleanup: int) -> None:
        nonlocal esp
        esp -= 4
        stack[esp] = ("return", target)
        # RET consumes the return address; RET n then consumes n argument bytes.
        esp += 4
        stack.pop(esp - 4, None)
        for _ in range(cleanup // 4):
            stack.pop(esp, None)
            esp += 4

    for mnemonic, operand, offset in instructions:
        if saw_jump:
            raise ReentryBundleError("instructions follow the stub continuation jump")
        if mnemonic == "pushfd":
            if flags_saved:
                raise ReentryBundleError("nested PUSHFD is not part of the audited stub")
            push(("saved-flags",))
            flags_saved = True
        elif mnemonic == "popfd":
            if not flags_saved or stack.get(esp) != ("saved-flags",):
                raise ReentryBundleError("POPFD is not balanced with the entry flags")
            stack.pop(esp, None)
            esp += 4
            flags_saved = False
        elif mnemonic == "push_imm":
            assert operand is not None
            if operand == VEHICLE_LIST_PATH_VA:
                if flags_saved or sequence != 2 or esp != 0:
                    raise ReentryBundleError("displaced VehicleList PUSH is not replayed with the original stack")
                saw_replay_push = True
            push(operand)
            if operand in (YVALUE_PATH_VA, XVALUE_PATH_VA):
                pending_path = operand
                sequence += 1
        elif mnemonic == "lea_ecx_esp":
            assert operand is not None
            ecx = esp + operand
        elif mnemonic == "mov_eax_class":
            eax = ("class",)
        elif mnemonic == "mov_edx_class":
            edx = ("class",)
        elif mnemonic == "mov_eax_local":
            if edx != ("class",):
                raise ReentryBundleError("local ordinal load is not indexed by the restored class")
            eax = ("local",)
        elif mnemonic == "push_eax":
            push(eax)
            pending_value = eax
        elif mnemonic == "push_ecx":
            push(ecx)
        elif mnemonic == "mov_ecx_eax":
            ecx = eax
        elif mnemonic == "call":
            assert operand is not None
            calls.append(operand)
            if operand == BROKER_PATH_INIT_VA:
                if pending_path is None or stack.get(esp) != pending_path:
                    raise ReentryBundleError("Broker path initializer argument does not match the pending path")
                if ecx != BROKER_PATH_OBJECT_OFFSET:
                    got = ecx if isinstance(ecx, int) else -1
                    raise ReentryBundleError(
                        f"path initializer object is S+0x{got:x}, expected S+0x{BROKER_PATH_OBJECT_OFFSET:x}")
                initialized.append((pending_path, ecx))
                emulate_call(operand, BROKER_PATH_INIT_STACK_CLEANUP)
            elif operand == BROKER_VALUE_GET_VA:
                # The native helper ends in RET; its path argument and staged
                # value remain for the following RET 8 setter call.
                if pending_path is None or stack.get(esp) != BROKER_PATH_OBJECT_OFFSET:
                    raise ReentryBundleError("Broker value-get argument is not the initialized path object")
                if stack.get(esp + 4) != pending_value:
                    raise ReentryBundleError("Broker setter value is not staged below the getter path argument")
                emulate_call(operand, BROKER_VALUE_GET_STACK_CLEANUP)
                eax = ("broker-container",)
            elif operand == BROKER_VALUE_SET_VA:
                if ecx != ("broker-container",):
                    raise ReentryBundleError("Broker setter does not receive its native container in ECX")
                if stack.get(esp) != BROKER_PATH_OBJECT_OFFSET or stack.get(esp + 4) != pending_value:
                    raise ReentryBundleError("Broker setter arguments do not match path-object/value order")
                emulate_call(operand, BROKER_VALUE_SET_STACK_CLEANUP)
                if esp != -4:
                    raise ReentryBundleError("native setter did not return to the post-PUSHFD stack")
                pending_path = None
                pending_value = None
            else:
                raise ReentryBundleError(f"unexpected call target 0x{operand:08x}")
        elif mnemonic == "jmp":
            assert operand is not None
            if operand != CONTINUATION_VA or esp != -4 or flags_saved or not saw_replay_push:
                raise ReentryBundleError("stub continuation, stack, flags, or replayed PUSH is invalid")
            if stack.get(esp) != VEHICLE_LIST_PATH_VA:
                raise ReentryBundleError("continuation stack lacks the exact displaced VehicleList PUSH")
            saw_jump = True
        else:
            raise ReentryBundleError(f"unhandled decoded instruction {mnemonic} at +0x{offset:x}")

    expected_calls = [
        BROKER_PATH_INIT_VA, BROKER_VALUE_GET_VA, BROKER_VALUE_SET_VA,
        BROKER_PATH_INIT_VA, BROKER_VALUE_GET_VA, BROKER_VALUE_SET_VA,
    ]
    if (not saw_jump or calls != expected_calls or len(initialized) != 2
            or [path for path, _ in initialized] != [YVALUE_PATH_VA, XVALUE_PATH_VA]
            or [address for _, address in initialized] != [BROKER_PATH_OBJECT_OFFSET] * 2
            or flags_saved or esp != -4 or pushed_writes != [-4, -8, -8, -12, -8, -8, -12, -4]):
        raise ReentryBundleError("stub does not satisfy the audited two-field publication lifecycle")
    if any(address >= 0 for address in pushed_writes):
        raise ReentryBundleError("stub stack pushes overwrite constructor locals")
    return {
        "status": "PASS_SYMBOLIC_STUB_ABI",
        "entry_esp_before_replayed_push": 0,
        "continuation_esp": esp,
        "initialized_paths": ["UI/XYButton/YValue", "UI/XYButton/XValue"],
        "broker_path_object_offsets": [address for _, address in initialized],
        "path_init_ret_cleanup": BROKER_PATH_INIT_STACK_CLEANUP,
        "value_get_ret_cleanup": BROKER_VALUE_GET_STACK_CLEANUP,
        "value_set_ret_cleanup": BROKER_VALUE_SET_STACK_CLEANUP,
        "calls": [f"0x{target:08x}" for target in calls],
        "replayed_push": f"PUSH 0x{VEHICLE_LIST_PATH_VA:08x}",
        "continuation": f"0x{CONTINUATION_VA:08x}",
    }


def make_republish_stub(*, stub_va: int = STUB_VA) -> bytes:
    """Emit a stack-balanced x86 stub using the constructor's native locals.

    The constructor has already restored the correct physical ID through its
    player-specific source and sparse reverse mapper at this point. At entry
    ESP is S; PUSHFD and the path push put ESP at S-8. The native Broker path
    object is at S+0x14, so initialization uses [ESP+0x1c]. FUN_004D0580
    returns with RET 4, leaving ESP at S-4; its object address is then
    [ESP+0x18]. The emitted bytes are symbolically checked against those ABIs.
    """
    code = bytearray()

    def emit(raw: bytes) -> None:
        code.extend(raw)

    def push_imm(value: int) -> None:
        emit(b"\x68" + struct.pack("<I", value))

    def call(target: int) -> None:
        emit(_rel32(0xE8, target, stub_va + len(code)))

    emit(b"\x9c")  # pushfd: preserve the constructor's incoming flags

    # YValue = the constructor's final class index [this+0x10].
    push_imm(YVALUE_PATH_VA)
    emit(b"\x8d\x4c\x24\x1c")  # lea ecx,[esp+0x1c]
    call(BROKER_PATH_INIT_VA)
    emit(b"\x8b\x47\x10")  # mov eax,[edi+0x10]
    emit(b"\x8d\x4c\x24\x18")  # lea ecx,[esp+0x18] -> S+0x14 after RET 4
    emit(b"\x50\x51")  # push eax; push ecx
    call(BROKER_VALUE_GET_VA)
    emit(b"\x8b\xc8")  # mov ecx,eax
    call(BROKER_VALUE_SET_VA)

    # XValue = the local ordinal for that final class [this+0x14+class*4].
    push_imm(XVALUE_PATH_VA)
    emit(b"\x8d\x4c\x24\x1c")
    call(BROKER_PATH_INIT_VA)
    emit(b"\x8b\x57\x10")  # mov edx,[edi+0x10]
    emit(b"\x8d\x4c\x24\x18")
    emit(b"\x8b\x44\x97\x14")  # mov eax,[edi+edx*4+0x14]
    emit(b"\x50\x51")
    call(BROKER_VALUE_GET_VA)
    emit(b"\x8b\xc8")
    call(BROKER_VALUE_SET_VA)

    emit(b"\x9d")  # popfd
    push_imm(VEHICLE_LIST_PATH_VA)  # replay displaced original instruction
    emit(_rel32(0xE9, CONTINUATION_VA, stub_va + len(code)))
    result = bytes(code)
    verify_republish_stub(result, stub_va=stub_va)
    return result


def _find_republish_stub_va(source: bytes, parent_image: bytes,
                            parent_rows: list[dict[str, Any]]) -> int:
    """Choose a zero-filled .text cave in the already-qualified J.2 page.

    The original J.2 address remains preferred and therefore byte-identical
    for its reference collection. Longer authored identity payloads may occupy
    that address, so a deterministic scan uses only the same executable PE
    page and requires an exact zero preimage in both retail and the composed
    parent image, with no overlap against any parent file/RVA operation.
    """
    stub_size = len(make_republish_stub())
    _pe, sections = addon_runtime._pe_sections(source)
    text = next((row for row in sections if row.get("name") == ".text"), None)
    if text is None:
        raise ReentryBundleError("retail image has no executable .text section")
    page_start_va = STUB_VA & ~0xFFF
    page_end_va = page_start_va + 0x1000
    raw_start_va = IMAGE_BASE + text["rva"]
    raw_end_va = raw_start_va + text["raw_size"]
    scan_end_va = min(page_end_va, raw_end_va)
    candidates = [STUB_VA]
    last = (scan_end_va - stub_size) & ~0xF
    candidates.extend(range(last, page_start_va - 1, -16))
    file_ranges = [(row["file_offset"], row["file_offset"] + row["length"])
                   for row in parent_rows]
    memory_ranges = [(row["rva"], row["rva"] + row["length"])
                     for row in parent_rows if row.get("flags") != FLAG_FILE_ONLY]
    for candidate_va in dict.fromkeys(candidates):
        if candidate_va & ~0xFFF != page_start_va or candidate_va < raw_start_va:
            continue
        rva = candidate_va - IMAGE_BASE
        try:
            file_offset, section = _rva_to_file_offset(sections, rva, stub_size)
        except ReentryBundleError:
            continue
        if section != ".text" or file_offset + stub_size > len(source):
            continue
        if any(source[file_offset:file_offset + stub_size]) or any(parent_image[file_offset:file_offset + stub_size]):
            continue
        if any(candidate_start < file_offset + stub_size and file_offset < candidate_end
               for candidate_start, candidate_end in file_ranges):
            continue
        if any(candidate_start < rva + stub_size and rva < candidate_end
               for candidate_start, candidate_end in memory_ranges):
            continue
        return candidate_va
    raise ReentryBundleError("no zero-filled, non-overlapping J.2 executable code cave exists in the audited .text page")


def expected_xy_for_physical_id(physical_id: int) -> tuple[int, int]:
    """Reference oracle for the native sparse physical->class/local mapping."""
    try:
        return PHYSICAL_TO_CLASS_LOCAL[physical_id]
    except KeyError as exc:
        raise ReentryBundleError(f"physical vehicle ID is not in the qualified catalog: {physical_id}") from exc


def _rva_to_file_offset(sections: list[dict[str, Any]], rva: int, length: int) -> tuple[int, str]:
    for section in sections:
        start = section["rva"]
        if start <= rva and rva + length <= start + section["raw_size"]:
            return section["raw_offset"] + rva - start, section["name"]
    raise ReentryBundleError(f"RVA 0x{rva:X}+0x{length:X} is not wholly inside a file-backed PE section")


def _parse_and_reconstruct(source: bytes, rvp: bytes) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    if len(rvp) < RVP_HEADER.size:
        raise ReentryBundleError("truncated MRVP operation header")
    fields = RVP_HEADER.unpack_from(rvp)
    magic, version, machine, image_base, source_size, result_size, count = fields[:7]
    if (magic != b"MRVP" or version != 1 or machine != addon_runtime.MACHINE_I386
            or image_base != IMAGE_BASE or source_size != len(source)
            or result_size != len(source) or count > 512):
        raise ReentryBundleError("J.1 parent MRVP identity/header mismatch")
    if fields[7] != bytes.fromhex(_sha(source)):
        raise ReentryBundleError("MRVP source identity differs from the pristine retail file")
    cursor = RVP_HEADER.size
    _pe, sections = addon_runtime._pe_sections(source)
    reconstructed = bytearray(source)
    file_ranges: list[tuple[int, int, str]] = []
    rva_ranges: list[tuple[int, int, str]] = []
    rows: list[dict[str, Any]] = []
    for index in range(count):
        if cursor + RVP_OPERATION.size > len(rvp):
            raise ReentryBundleError("truncated MRVP operation row")
        file_offset, rva, length, flags, page_class = RVP_OPERATION.unpack_from(rvp, cursor)
        cursor += RVP_OPERATION.size
        if length == 0 or length > 8192 or cursor + length * 2 > len(rvp):
            raise ReentryBundleError("invalid MRVP operation length")
        before = rvp[cursor:cursor + length]
        cursor += length
        after = rvp[cursor:cursor + length]
        cursor += length
        if file_offset + length > len(source) or source[file_offset:file_offset + length] != before:
            raise ReentryBundleError(f"MRVP preimage mismatch at operation {index}")
        for start, end, name in file_ranges:
            if file_offset < end and start < file_offset + length:
                raise ReentryBundleError(f"MRVP file-operation overlap with {name}")
        file_ranges.append((file_offset, file_offset + length, f"parent operation {index}"))
        if flags == FLAG_FILE_ONLY:
            if rva != 0xFFFFFFFF or page_class != 0:
                raise ReentryBundleError("invalid file-only parent operation")
        elif flags in (FLAG_PROCESS, FLAG_NOOP):
            expected_rva, section = addon_runtime._file_range_to_rva(sections, file_offset, length)
            if expected_rva != rva:
                raise ReentryBundleError(f"MRVP RVA/file mapping mismatch at operation {index}")
            expected_page = PAGE_CODE if section == ".text" else PAGE_DATA
            if page_class != expected_page:
                raise ReentryBundleError(f"MRVP page class mismatch at operation {index}")
            for start, end, name in rva_ranges:
                if rva < end and start < rva + length:
                    raise ReentryBundleError(f"MRVP memory-operation overlap with {name}")
            rva_ranges.append((rva, rva + length, f"parent operation {index}"))
        else:
            raise ReentryBundleError(f"unknown MRVP operation flags: {flags}")
        reconstructed[file_offset:file_offset + length] = after
        rows.append({"file_offset": file_offset, "rva": rva, "length": length,
                     "flags": flags, "page_class": page_class,
                     "before": before, "after": after})
    if cursor != len(rvp):
        raise ReentryBundleError("MRVP contains trailing bytes")
    if _sha(bytes(reconstructed)) != fields[8].hex():
        raise ReentryBundleError("J.1 MRVP operations do not reproduce their pinned reference image")
    return {"fields": fields, "count": count, "source_sha256": fields[7].hex(),
            "reference_sha256": fields[8].hex(), "plan_sha256": fields[9].hex()}, bytes(reconstructed), rows


def _verify_id27_reverse_mapper(image: bytes) -> dict[str, Any]:
    """Decode the emitted ID27 reverse-map branch and emulate its object writes.

    This deliberately reads the effective reconstructed code bytes. The
    class-local layout is class at +0x10 followed by three local ordinals at
    +0x14/+0x18/+0x1c, as also encoded by the stock mapper and forward hook.
    """
    _pe, sections = addon_runtime._pe_sections(image)
    code_offset, section = _rva_to_file_offset(
        sections, ID27_REVERSE_MAP_VA - IMAGE_BASE, 0x40)
    if section != ".text":
        raise ReentryBundleError("ID27 reverse mapper is not in the audited executable section")
    code = image[code_offset:code_offset + 0x40]
    prefix = bytes.fromhex("837c24041b0f8516000000568bf1")
    if not code.startswith(prefix):
        raise ReentryBundleError("ID27 reverse mapper no longer checks the physical ID argument safely")
    cursor = len(prefix)

    def decode_store(expected_field: int, expected_value: int, label: str) -> tuple[int, int]:
        nonlocal cursor
        if code[cursor:cursor + 2] != b"\xc7\x46":
            raise ReentryBundleError(f"ID27 reverse mapper is missing its {label} object write")
        field = code[cursor + 2]
        value = struct.unpack_from("<I", code, cursor + 3)[0]
        cursor += 7
        if (field, value) != (expected_field, expected_value):
            raise ReentryBundleError(
                f"ID27 reverse mapper {label} write is [{field:#x}]={value}, "
                f"expected [{expected_field:#x}]={expected_value}")
        return field, value

    class_field, class_value = decode_store(0x10, 1, "T2 class")
    local_field, local_value = decode_store(0x18, 7, "T2 local ordinal")
    if code[cursor] != 0xE9:
        raise ReentryBundleError("ID27 reverse mapper does not jump to the native common tail")
    tail = ID27_REVERSE_MAP_VA + cursor + 5
    tail += struct.unpack_from("<i", code, cursor + 1)[0]
    cursor += 5
    if tail != 0x00481E89:
        raise ReentryBundleError(f"ID27 reverse mapper tail changed unexpectedly: {tail:#x}")
    class_local_field = 0x14 + class_value * 4
    if local_field != class_local_field:
        raise ReentryBundleError("ID27 reverse mapper writes its local ordinal into another class's slot")

    # Symbolically execute the two stores against the native object layout and
    # then follow the same field selection used by the constructor/J.2 stub.
    scene = bytearray(0x20)
    struct.pack_into("<I", scene, class_field, class_value)
    struct.pack_into("<I", scene, local_field, local_value)
    restored_class = struct.unpack_from("<I", scene, 0x10)[0]
    restored_local = struct.unpack_from("<I", scene, 0x14 + restored_class * 4)[0]
    if (restored_class, restored_local) != (1, 7):
        raise ReentryBundleError("ID27 reverse mapper does not restore T2/local7 in the scene object")

    # Verify the matching forward hook consumes T2's local slot and resolves
    # it back to physical 27, rather than relying on the Python catalog map.
    forward_va = 0x0068E860
    forward_offset, forward_section = _rva_to_file_offset(
        sections, forward_va - IMAGE_BASE, 0x20)
    forward = image[forward_offset:forward_offset + 0x20]
    expected_forward = bytes.fromhex("837910010f8510000000837918070f8506000000b81b000000c3")
    if forward_section != ".text" or forward[:len(expected_forward)] != expected_forward:
        raise ReentryBundleError("ID27 forward mapper does not consume T2/local7 and return physical ID27")
    if forward[0x14] != 0xB8 or forward[0x19] != 0xC3:
        raise ReentryBundleError("ID27 forward mapper return sequence changed unexpectedly")
    mapped_id = struct.unpack_from("<I", forward, 0x15)[0]
    if mapped_id != 27:
        raise ReentryBundleError("ID27 forward sparse mapping changed unexpectedly")
    return {
        "status": "PASS_ID27_NATIVE_REVERSE_FORWARD_MAP",
        "reverse_entry_va": f"0x{ID27_REVERSE_MAP_VA:08X}",
        "reverse_local_store_va": f"0x{ID27_REVERSE_LOCAL_STORE_VA:08X}",
        "class_field_offset": class_field,
        "class_value": class_value,
        "local_field_offset": local_field,
        "local_value": local_value,
        "class_local_field_expected": class_local_field,
        "restored_state": {"CarClass": restored_class, "local_ordinal": restored_local},
        "forward_physical_id": mapped_id,
        "native_common_tail": f"0x{tail:08X}",
    }


def _repair_id27_reverse_mapper_parent(base_manifest: dict[str, Any],
                                       parent_rows: list[dict[str, Any]],
                                       base_image: bytes) -> tuple[dict[str, Any], list[dict[str, Any]], bytes, dict[str, Any]]:
    """Derive a one-byte J.2 fix over the unchanged, verified 246-op J.1 parent."""
    target_offset = ID27_REVERSE_LOCAL_STORE_FILE_OFFSET
    matches = [i for i, row in enumerate(parent_rows)
               if row["file_offset"] <= target_offset < row["file_offset"] + row["length"]]
    if len(matches) != 1:
        raise ReentryBundleError("J.1 parent does not have one exact ID27 reverse-map code operation")
    row_index = matches[0]
    row = dict(parent_rows[row_index])
    within = target_offset - row["file_offset"]
    if (row["rva"] != target_offset or row["length"] != len(ID27_REVERSE_LOCAL_STORE_EXPECTED)
            or within != 0 or row["after"] != ID27_REVERSE_LOCAL_STORE_EXPECTED
            or row["before"] != bytes(row["length"])):
        raise ReentryBundleError("J.1 reverse-map bytes differ from the audited faulty ID27 T1-slot write")
    original_after = row["after"]
    repaired_after = bytearray(original_after)
    repaired_after[within + 2] = ID27_REVERSE_LOCAL_STORE_FIXED[2]
    row["after"] = bytes(repaired_after)
    repaired_rows = list(parent_rows)
    repaired_rows[row_index] = row

    patched_manifest = json.loads(json.dumps(base_manifest))
    manifest_matches = [op for op in patched_manifest["operations"]
                        if op.get("file_offset") == row["file_offset"]
                        and op.get("replacement_bytes") == ID27_REVERSE_LOCAL_STORE_EXPECTED.hex()]
    if len(manifest_matches) != 1:
        raise ReentryBundleError("J.1 manifest does not uniquely identify the reverse-map code bytes")
    operation = manifest_matches[0]
    operation["replacement_bytes"] = row["after"].hex()
    operation["replacement_sha256"] = _sha(row["after"])
    operation.setdefault("semantic_provenance", []).append({
        "layer": "J.2 ID27 Vehicle Select re-entry root-cause fix",
        "name": "id27_reverse_map_t2_local_ordinal_slot",
        "category": "class-mapping",
        "semantic_purpose": "write T2/local7 to scene field +0x18 (T2 ordinal) instead of +0x14 (T1 ordinal); preserve physical ID27 and the stock/H.2 fallback mapper",
    })

    repaired_image = bytearray(base_image)
    repaired_image[row["file_offset"]:row["file_offset"] + row["length"]] = row["after"]
    audit = _verify_id27_reverse_mapper(bytes(repaired_image))
    audit.update({
        "parent_operation_index": row_index,
        "parent_operation_file_offset": f"0x{row['file_offset']:X}",
        "parent_operation_before": original_after.hex(),
        "parent_operation_after": row["after"].hex(),
        "changed_instruction": f"MOV [ESI+0x18],7 at 0x{ID27_REVERSE_LOCAL_STORE_VA:08X}",
        "physical_id_written": False,
    })
    return patched_manifest, repaired_rows, bytes(repaired_image), audit


def _serialize_rvp_rows(rows: list[dict[str, Any]]) -> bytes:
    body = bytearray()
    for row in rows:
        body.extend(RVP_OPERATION.pack(row["file_offset"], row["rva"], row["length"],
                                       row["flags"], row["page_class"]))
        body.extend(row["before"])
        body.extend(row["after"])
    return bytes(body)


def _j2_artifacts(source: bytes, base_bundle: Path, *,
                  expected_plan_sha256: str = addon_runtime.REFERENCE_PLAN_SHA256,
                  profile_name: str = J2_PROFILE,
                  allow_generic_collection: bool = False,
                  stub_va: int | None = None) -> tuple[dict[str, Any], bytes, bytes, dict[str, Any], bytes]:
    if len(source) != addon_runtime.RETAIL_SIZE or _sha(source) != addon_runtime.RETAIL_SHA256:
        raise ReentryBundleError("source is not the exact pristine retail executable")
    base_manifest = json.loads((base_bundle / "native-patch-manifest.json").read_text(encoding="utf-8"))
    base_rvp = (base_bundle / "native-patch-ops.rvp").read_bytes()
    base_profile = json.loads((base_bundle / "runtime-profile.json").read_text(encoding="utf-8"))
    parent, base_image, parent_rows = _parse_and_reconstruct(source, base_rvp)
    profile_matches = (base_manifest.get("profile") == "r5v-j1-two-addon-retail-2001-reference"
                       if not allow_generic_collection
                       else isinstance(base_manifest.get("profile"), str)
                       and base_manifest.get("profile", "").startswith("r5v-j3b-collection-parent-"))
    if (not profile_matches
            or base_manifest.get("source", {}).get("sha256") != addon_runtime.RETAIL_SHA256
            or base_manifest.get("reference_image", {}).get("sha256") != parent["reference_sha256"]
            or base_profile.get("native_patch_operations_sha256") != _sha(base_rvp)
            or base_profile.get("native_patch_manifest_sha256") != _sha(addon_runtime.canonical_json(base_manifest))
            or base_profile.get("addon_plan_sha256") != expected_plan_sha256
            or parent["plan_sha256"] != expected_plan_sha256):
        raise ReentryBundleError("native patch parent does not match its verified addon collection")

    # The verified J.1 bundle remains byte-for-byte untouched. J.2 derives a
    # corrected composite plan by changing the one faulty displacement inside
    # its inherited code-cave operation, then adds the two re-entry publication
    # operations below. This preserves the 246-operation parent shape without
    # overlapping an extra patch into the parent's code-cave range.
    base_manifest, parent_rows, base_image, reverse_map_audit = (
        _repair_id27_reverse_mapper_parent(base_manifest, parent_rows, base_image))

    selected_stub_va = stub_va if stub_va is not None else _find_republish_stub_va(source, base_image, parent_rows)
    if (selected_stub_va & ~0xFFF) != (STUB_VA & ~0xFFF):
        raise ReentryBundleError("re-entry stub must remain on the already-qualified executable .text page")

    pe, sections = addon_runtime._pe_sections(source)
    hook_offset, hook_section = _rva_to_file_offset(sections, HOOK_RVA, len(EXPECTED_HOOK))
    stub = make_republish_stub(stub_va=selected_stub_va)
    stub_rva = selected_stub_va - IMAGE_BASE
    stub_offset, stub_section = _rva_to_file_offset(sections, stub_rva, len(stub))
    if hook_section != ".text" or stub_section != ".text":
        raise ReentryBundleError("re-entry hook and trampoline must be in the audited executable .text section")
    if (base_image[hook_offset:hook_offset + len(EXPECTED_HOOK)] != EXPECTED_HOOK
            or source[hook_offset:hook_offset + len(EXPECTED_HOOK)] != EXPECTED_HOOK):
        raise ReentryBundleError("constructor convergence preimage differs from the audited stock PUSH")
    if source[stub_offset:stub_offset + len(stub)] != bytes((STUB_ORIGINAL_FILL,)) * len(stub):
        raise ReentryBundleError("the proposed post-I.1 code cave is not entirely zero-filled")
    if stub_rva + len(stub) > pe["size_image"]:
        raise ReentryBundleError("re-entry stub exceeds the mapped PE SizeOfImage")

    new_hook = _rel32(0xE9, selected_stub_va, HOOK_VA)
    additions = [
        {"name": "vehicle_select_republish_final_class_local_xy", "file_offset": hook_offset,
         "rva": HOOK_RVA, "section": ".text", "before": EXPECTED_HOOK,
         "after": new_hook, "va": HOOK_VA,
         "semantic_purpose": "After native mode/player-specific physical-ID restoration and sparse class/local mapping, branch to the republisher; do not alter saved or committed vehicle identity."},
        {"name": "vehicle_select_republish_stub", "file_offset": stub_offset,
         "rva": stub_rva, "section": ".text", "before": source[stub_offset:stub_offset + len(stub)],
         "after": stub, "va": selected_stub_va,
         "semantic_purpose": "Publish the constructor's final class and per-class local ordinal through the existing XYButton Broker setters, then replay the displaced VehicleList path setup."},
    ]
    all_file_ranges = [(row["file_offset"], row["file_offset"] + row["length"], f"parent {i}")
                       for i, row in enumerate(parent_rows)]
    all_rva_ranges = [(row["rva"], row["rva"] + row["length"], f"parent {i}")
                      for i, row in enumerate(parent_rows) if row["flags"] != FLAG_FILE_ONLY]
    for addition in additions:
        start = addition["file_offset"]
        end = start + len(addition["before"])
        for prior_start, prior_end, name in all_file_ranges:
            if start < prior_end and prior_start < end:
                raise ReentryBundleError(f"new file range overlaps {name}")
        rva = addition["rva"]
        for prior_start, prior_end, name in all_rva_ranges:
            if rva < prior_end and prior_start < rva + len(addition["before"]):
                raise ReentryBundleError(f"new memory range overlaps {name}")
        all_file_ranges.append((start, end, addition["name"]))
        all_rva_ranges.append((rva, rva + len(addition["before"]), addition["name"]))

    result_image = bytearray(base_image)
    for addition in additions:
        start = addition["file_offset"]
        result_image[start:start + len(addition["after"])] = addition["after"]
    result_image_bytes = bytes(result_image)
    result_sha = _sha(result_image_bytes)
    if result_sha == parent["reference_sha256"]:
        raise ReentryBundleError("J.2 image hash did not change after adding the re-entry operation")

    patch_manifest = json.loads(json.dumps(base_manifest))
    patch_manifest["profile"] = profile_name
    patch_manifest["status"] = "STATICALLY_VERIFIED_READY_FOR_HUMAN_RUNTIME"
    patch_manifest["reference_image"].update({
        "sha256": result_sha,
        "written_to_disk": False,
        "derivation": "unchanged verified J.1 parent bundle with one J.2 correction to ID27's T2-local field displacement, plus the constructor-local Vehicle Select XY publication hook and stub; no executable file is emitted",
        "hash_semantics": "SHA256 of deterministic retail-file reconstruction including the parent PE-header-only operation and the J.2 in-memory operations; never written to the retail executable path",
    })
    manifest_ops = patch_manifest["operations"]
    for addition in additions:
        manifest_ops.append({
            "name": addition["name"], "target_module": "MRallye.exe",
            "file_offset": addition["file_offset"], "rva": addition["rva"],
            "preferred_va": addition["va"], "section": addition["section"],
            "expected_original_bytes": addition["before"].hex(),
            "expected_original_sha256": _sha(addition["before"]),
            "replacement_bytes": addition["after"].hex(),
            "replacement_sha256": _sha(addition["after"]),
            "required_initialization_phase": "after-native-vehicle-selection-restoration-before-primary-thread-first-resume",
            "page_class": "EXECUTE_READWRITE",
            "dependencies": ["exact_retail_file_identity", "mapped_image_identity", "all_preimages_validated",
                             "FUN_00480B60_saved_physical_id_restoration", "FUN_00481E50_sparse_physical_to_class_local_mapping"],
            "semantic_provenance": [{
                "layer": "J.2 bounded frontend re-entry correction",
                "name": addition["name"],
                "category": "Vehicle Select constructor final-state publication",
                "semantic_purpose": addition["semantic_purpose"],
            }],
        })
    patch_manifest["process_memory_operation_count"] += len(additions)
    patch_manifest["vehicle_select_reentry"] = {
        "constructor_va": 0x00480B60,
        "restoration_join_va": HOOK_VA,
        "hook_continuation_va": CONTINUATION_VA,
        "stub_va": selected_stub_va,
        "saved_selection_source": "PlayerID selects its stored physical Quick Race car; constructor passes that ID to the sparse reverse mapper before XY publication",
        "published_fields": ["UI/XYButton/YValue", "UI/XYButton/XValue"],
        "source_values": ["this+0x10 class", "this+0x14 + class*4 local ordinal"],
        "native_reverse_mapping_fix": "ID27 writes T2/local7 at this+0x18; ID26 remains T1/local7 at this+0x14",
        "physical_car_id_or_commit_state_written": False,
        "global_xy_override": False,
        "replays_displaced_instruction": "PUSH Frontend/VehicleSelect/VehicleList",
        "stub_abi_audit": verify_republish_stub(stub, stub_va=selected_stub_va),
        "evidence_boundary": "STATIC_PATCH_PLAN_READY_FOR_HUMAN_RUNTIME",
    }
    patch_manifest["id27_reverse_mapping_correction"] = reverse_map_audit
    patch_manifest["evidence_boundary"] = "STATIC_J2_REENTRY_CANDIDATE_NOT_HUMAN_RUNTIME_QUALIFIED"
    manifest_bytes = addon_runtime.canonical_json(patch_manifest)

    rvp_header = RVP_HEADER.pack(
        b"MRVP", 1, addon_runtime.MACHINE_I386, IMAGE_BASE, len(source), len(source),
        parent["count"] + len(additions), bytes.fromhex(_sha(source)),
        bytes.fromhex(result_sha), bytes.fromhex(parent["plan_sha256"]),
    )
    binary = bytearray(rvp_header)
    # The parent operations are already validated. Keep their exact serialized
    # body byte-for-byte, changing only the trusted count/image identity header.
    binary.extend(_serialize_rvp_rows(parent_rows))
    for addition in additions:
        binary.extend(RVP_OPERATION.pack(addition["file_offset"], addition["rva"],
                                         len(addition["before"]), FLAG_PROCESS, PAGE_CODE))
        binary.extend(addition["before"])
        binary.extend(addition["after"])

    profile = json.loads(json.dumps(base_profile))
    profile.update({
        "profile": profile_name,
        "status": "READY_FOR_HUMAN_RUNTIME",
        "runtime_level": "STATICALLY_VERIFIED_EXTERNAL_LAUNCHER_CANDIDATE_WITH_REENTRY_FIX",
        "native_patch_manifest_sha256": _sha(manifest_bytes),
        "native_patch_operations_sha256": _sha(bytes(binary)),
        "reconstructed_reference_file_sha256": result_sha,
        "reference_executable_written_to_disk": False,
        "runtime_installable": False,
        "runtime_qualified": False,
        "j1_parent_profile": base_profile["profile"],
        "j1_parent_manifest_sha256": base_profile["native_patch_manifest_sha256"],
        "j1_parent_operations_sha256": base_profile["native_patch_operations_sha256"],
        "j2_reentry_hook_va": HOOK_VA,
        "j2_reentry_stub_va": selected_stub_va,
        "id27_reverse_mapping_correction": reverse_map_audit,
        "unresolved_runtime_gates": [
            "human confirmation of same-PlayerID Quick Race ID27 return/reopen selection",
            "human confirmation of ID26, stock ID7 and SplitScreen player-state regression",
            "locked ID27 interaction regression must remain blocked",
        ],
    })
    return patch_manifest, bytes(binary), profile, result_image_bytes, manifest_bytes


def _verify_base(*, base_bundle: Path, retail_exe: Path, package: Path,
                 capabilities: Path) -> dict[str, Any]:
    result = addon_runtime.verify_bundle(base_bundle, retail_exe=retail_exe,
                                         package=package, capabilities_path=capabilities)
    if result.get("status") != "PASS_STATIC_RUNTIME_BUNDLE":
        raise ReentryBundleError("exact J.1 parent bundle failed deterministic verification")
    return result


def prepare_candidate(*, output: Path = J2_BUNDLE, base_bundle: Path = J1_BUNDLE,
                      retail_exe: Path = RETAIL_EXE, package: Path = J1_PACKAGE,
                      capabilities: Path = addon_runtime.DEFAULT_CAPABILITIES) -> dict[str, Any]:
    output = addon_runtime._under_research_output(Path(output))
    base_bundle = Path(base_bundle)
    _verify_base(base_bundle=base_bundle, retail_exe=retail_exe,
                 package=package, capabilities=capabilities)
    source = Path(retail_exe).read_bytes()
    patch_manifest, binary, profile, _reference_image, manifest_bytes = _j2_artifacts(source, base_bundle)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        shutil.copytree(base_bundle, stage / "bundle", dirs_exist_ok=True)
        target = stage / "bundle"
        (target / "native-patch-manifest.json").write_bytes(manifest_bytes)
        (target / "native-patch-ops.rvp").write_bytes(binary)
        (target / "runtime-profile.json").write_bytes(addon_runtime.canonical_json(profile))
        # Add a small evidence file to make the custom operation discoverable.
        (target / "vehicle-select-reentry.json").write_bytes(addon_runtime.canonical_json(
            patch_manifest["vehicle_select_reentry"]))
        verified = verify_candidate(target, base_bundle=base_bundle,
                                    retail_exe=retail_exe, package=package,
                                    capabilities=capabilities)
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return verified


def verify_candidate(bundle: Path = J2_BUNDLE / "bundle", *, base_bundle: Path = J1_BUNDLE,
                     retail_exe: Path = RETAIL_EXE, package: Path = J1_PACKAGE,
                     capabilities: Path = addon_runtime.DEFAULT_CAPABILITIES) -> dict[str, Any]:
    _verify_base(base_bundle=base_bundle, retail_exe=retail_exe,
                 package=package, capabilities=capabilities)
    bundle = Path(bundle)
    if not bundle.is_dir() or bundle.is_symlink():
        raise ReentryBundleError("J.2 bundle is missing or link-backed")
    source = Path(retail_exe).read_bytes()
    expected_manifest, expected_ops, expected_profile, ref_image, manifest_bytes = _j2_artifacts(source, Path(base_bundle))
    for relative, expected in (
        ("native-patch-manifest.json", manifest_bytes),
        ("native-patch-ops.rvp", expected_ops),
        ("runtime-profile.json", addon_runtime.canonical_json(expected_profile)),
        ("vehicle-select-reentry.json", addon_runtime.canonical_json(expected_manifest["vehicle_select_reentry"])),
    ):
        path = bundle / relative
        if not path.is_file() or path.read_bytes() != expected:
            raise ReentryBundleError(f"J.2 deterministic artifact mismatch: {relative}")
    base_bundle = Path(base_bundle)
    for relative in ("addon-plan.json", "frontend-overlay.plan.json", "resource-inventory.json",
                     "resource-index.tsv", "resource-manifest.json"):
        if (bundle / relative).read_bytes() != (base_bundle / relative).read_bytes():
            raise ReentryBundleError(f"J.2 changed the accepted J.1 addon/resource artifact: {relative}")
    resource_manifest = json.loads((bundle / "resource-manifest.json").read_text(encoding="utf-8"))
    resource_rows = resource_manifest.get("resources")
    if not isinstance(resource_rows, list):
        raise ReentryBundleError("J.2 resource manifest has no resource inventory")
    resource_root = bundle / "resource-root"
    if not resource_root.is_dir() or resource_root.is_symlink() or getattr(resource_root, "is_junction", lambda: False)():
        raise ReentryBundleError("J.2 resource root is missing or linked")
    expected_paths = {str(row.get("path", "")).replace("\\", "/").casefold() for row in resource_rows}
    actual_paths: set[str] = set()
    for current, directories, files in os.walk(resource_root, followlinks=False):
        for name in directories:
            path = Path(current) / name
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ReentryBundleError(f"J.2 resource root contains a linked directory: {path}")
        for name in files:
            path = Path(current) / name
            if path.is_symlink():
                raise ReentryBundleError(f"J.2 resource root contains a linked file: {path}")
            actual_paths.add(path.relative_to(resource_root).as_posix().casefold())
    try:
        addon_runtime._validate_runtime_resource_set(expected_paths, actual_paths)
    except addon_runtime.RuntimeIntegrationError as exc:
        raise ReentryBundleError(f"J.2 resource-root path inventory is invalid: {exc}") from exc
    for row in resource_rows:
        relative = str(row["path"])
        path = addon_runtime._inside(resource_root, relative)
        if path.stat().st_size != row["size"] or addon_runtime.sha256_file(path) != row["sha256"]:
            raise ReentryBundleError(f"J.2 resource-root hash/size mismatch: {relative}")
    if _sha(ref_image) != expected_profile["reconstructed_reference_file_sha256"]:
        raise ReentryBundleError("J.2 reference reconstruction hash mismatch")
    return {
        "status": "PASS_STATIC_J2_REENTRY_BUNDLE",
        "runtime_qualified": False,
        "profile": J2_PROFILE,
        "retail_exe_sha256": addon_runtime.RETAIL_SHA256,
        "retail_exe_size": addon_runtime.RETAIL_SIZE,
        "addon_plan_sha256": expected_profile["addon_plan_sha256"],
        "native_patch_manifest_sha256": expected_profile["native_patch_manifest_sha256"],
        "native_patch_operations_sha256": expected_profile["native_patch_operations_sha256"],
        "native_operation_count": len(expected_manifest["operations"]),
        "j2_added_operations": ["vehicle_select_republish_final_class_local_xy", "vehicle_select_republish_stub"],
        "id27_reverse_mapping_correction": expected_manifest["id27_reverse_mapping_correction"],
        "stub_size": len(make_republish_stub()),
        "stub_sha256": _sha(make_republish_stub()),
        "stub_abi_audit": verify_republish_stub(make_republish_stub()),
        "stub_va": STUB_VA,
        "hook_va": HOOK_VA,
        "reference_reconstruction_sha256": expected_profile["reconstructed_reference_file_sha256"],
        "original_executable_written": False,
        "physical_ids_or_commit_state_changed_by_reentry_hook": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare/verify a minimal J.2 native re-entry candidate")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--output", type=Path, default=J2_BUNDLE)
    prepare.add_argument("--base-bundle", type=Path, default=J1_BUNDLE)
    prepare.add_argument("--retail-exe", type=Path, default=RETAIL_EXE)
    prepare.add_argument("--i1-package", type=Path, default=J1_PACKAGE)
    prepare.add_argument("--capabilities", type=Path, default=addon_runtime.DEFAULT_CAPABILITIES)
    verify = sub.add_parser("verify")
    verify.add_argument("bundle", type=Path, nargs="?", default=J2_BUNDLE / "bundle")
    verify.add_argument("--base-bundle", type=Path, default=J1_BUNDLE)
    verify.add_argument("--retail-exe", type=Path, default=RETAIL_EXE)
    verify.add_argument("--i1-package", type=Path, default=J1_PACKAGE)
    verify.add_argument("--capabilities", type=Path, default=addon_runtime.DEFAULT_CAPABILITIES)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_candidate(output=args.output, base_bundle=args.base_bundle,
                                       retail_exe=args.retail_exe, package=args.i1_package,
                                       capabilities=args.capabilities)
        else:
            result = verify_candidate(args.bundle, base_bundle=args.base_bundle,
                                      retail_exe=args.retail_exe, package=args.i1_package,
                                      capabilities=args.capabilities)
    except (ReentryBundleError, addon_runtime.RuntimeIntegrationError, OSError,
            ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
