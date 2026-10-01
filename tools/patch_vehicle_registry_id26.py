#!/usr/bin/env python3
"""Build a fail-closed retail ID26 / sparse T1 local-7 test executable.

This patcher supports one exact retail image and one bounded profile. It
preserves the confirmed Trooper ID25 record, expands the registry object to
27 VehicleRecords, moves the adjacent 39-row RaceTest table, and initializes
new ID26 by calling the original full initializer with Landcruiser donor
values. It never edits the source executable.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
from typing import Any

try:
    from patch_vehicle_slot25 import (
        IMAGE_BASE,
        SOURCE_SHA256,
        PatchError as BasePatchError,
        parse_pe,
        va_to_file_offset,
    )
except ImportError:  # pragma: no cover - supports package-style import in tests
    from tools.patch_vehicle_slot25 import (
        IMAGE_BASE,
        SOURCE_SHA256,
        PatchError as BasePatchError,
        parse_pe,
        va_to_file_offset,
    )


STUB_VA = 0x68E2A0
TEXT_VIRTUAL_SIZE_OLD = 0x28D294
REGISTRY_HOOK_VA = 0x458D3F
ORIGINAL_SECONDARY_INITIALIZER_VA = 0x4598D0
VEHICLE_INITIALIZER_VA = 0x45A0B0
STRING_CONSTRUCTOR_VA = 0x4D11D0
REGISTRY_ALLOCATOR_IMMEDIATE_VA = 0x45A3E0
OLD_REGISTRY_BYTES = 0xC00
NEW_REGISTRY_BYTES = 0xC34
OLD_RECORD_COUNT = 26
NEW_RECORD_COUNT = 27
RECORD_STRIDE = 0x34
RECORD0_OFFSET = 0x4
RECORD25_OFFSET = 0x518
RECORD26_OFFSET = 0x54C
RACETEST_OFFSET_OLD = 0x54C
RACETEST_OFFSET_NEW = 0x580
RACETEST_COUNT = 39
RACETEST_STRIDE = 0x2C
RACETEST_END_OLD = 0xC00
RACETEST_END_NEW = 0xC34


class PatchError(ValueError):
    """Source identity, byte layout, or requested operation is unsafe."""


@dataclass(frozen=True)
class VehicleRecordProfile:
    profile_id: str
    slot_id: int
    vehicle_class: int
    local_index: int | None
    internal_name: str
    stats: tuple[int, int, int, int]
    smallcarsheet_index: int
    race_colour_rgba_bits: tuple[int, int, int, int]
    donor_id: int


# Preserve the latest human-tested ID25/Trooper presentation profile. Its
# physics/runtime family remains the retail Trooper configuration and assets.
ID25_TROOPER = VehicleRecordProfile(
    profile_id="trooper-smallsheet29",
    slot_id=25,
    vehicle_class=2,
    local_index=11,
    internal_name="Trooper",
    stats=(6, 6, 8, 8),
    smallcarsheet_index=29,
    race_colour_rgba_bits=(0x3D8B1C04, 0x3F092D67, 0x3EF74E40, 0x3F800000),
    donor_id=16,
)

# First physical expansion payload: semantic copy of retail T1 ID0.
ID26_LANDCRUISER = VehicleRecordProfile(
    profile_id="duplicate-t1-id0-landcruiser",
    slot_id=26,
    vehicle_class=0,
    local_index=7,
    internal_name="Landcruiser",
    stats=(4, 2, 4, 6),
    smallcarsheet_index=9,
    race_colour_rgba_bits=(0x3DAA05CC, 0x3ED675DB, 0x3E8172F5, 0x3F800000),
    donor_id=0,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _CodeImage:
    """Tiny x86 rel32 emitter for the bounded code-cave payload."""

    def __init__(self, base_va: int) -> None:
        self.base_va = base_va
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.rel32: list[tuple[int, int, str | int]] = []
        self.imm32: list[tuple[int, str]] = []

    @property
    def va(self) -> int:
        return self.base_va + len(self.code)

    def emit(self, raw: bytes) -> None:
        self.code.extend(raw)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise PatchError(f"duplicate code label: {name}")
        self.labels[name] = len(self.code)

    def align(self, alignment: int = 16) -> None:
        while len(self.code) % alignment:
            self.emit(b"\x90")

    def call(self, target: str | int) -> None:
        self.emit(b"\xE8\x00\x00\x00\x00")
        self.rel32.append((len(self.code) - 4, len(self.code), target))

    def jump(self, target: str | int) -> None:
        self.emit(b"\xE9\x00\x00\x00\x00")
        self.rel32.append((len(self.code) - 4, len(self.code), target))

    def jne(self, target: str) -> None:
        self.emit(b"\x0F\x85\x00\x00\x00\x00")
        self.rel32.append((len(self.code) - 4, len(self.code), target))

    def push_literal(self, label: str) -> None:
        self.emit(b"\x68\x00\x00\x00\x00")
        self.imm32.append((len(self.code) - 4, label))

    def build(self) -> bytes:
        result = bytearray(self.code)
        for imm_offset, name in self.imm32:
            if name not in self.labels:
                raise PatchError(f"unresolved code label: {name}")
            struct.pack_into("<I", result, imm_offset, self.base_va + self.labels[name])
        for rel_offset, next_offset, target in self.rel32:
            target_va = self.base_va + self.labels[target] if isinstance(target, str) else target
            next_va = self.base_va + next_offset
            delta = target_va - next_va
            if not -(1 << 31) <= delta < (1 << 31):
                raise PatchError("code-cave branch out of rel32 range")
            struct.pack_into("<i", result, rel_offset, delta)
        return bytes(result)


def _emit_record_initializer(code: _CodeImage, profile: VehicleRecordProfile,
                             record_offset: int, literal_label: str) -> None:
    code.emit(b"\x83\xEC\x10")  # four tail floats are caller-provided stack values
    for index, bits in enumerate(profile.race_colour_rgba_bits):
        code.emit(b"\xC7\x44\x24" + bytes((index * 4,)) + struct.pack("<I", bits))
    code.emit(b"\x6A\x00\x8B\xCC")  # temporary std::string object, this = ESP
    code.push_literal(literal_label)
    code.call(STRING_CONSTRUCTOR_VA)
    for value in (profile.smallcarsheet_index, *reversed(profile.stats),
                  profile.vehicle_class, profile.slot_id):
        if not 0 <= value <= 0x7F:
            raise PatchError("initializer profile integer does not fit the verified push-imm8 ABI")
        code.emit(b"\x6A" + bytes((value,)))
    code.emit(b"\x8D\x8E" + struct.pack("<I", record_offset))  # ECX = registry + record offset
    code.call(VEHICLE_INITIALIZER_VA)


def build_code_payload() -> tuple[bytes, dict[str, int]]:
    code = _CodeImage(STUB_VA)

    code.label("registry_init")
    code.emit(b"\x56\x8B\xF1")  # preserve ESI; ESI = registry object
    _emit_record_initializer(code, ID25_TROOPER, RECORD25_OFFSET, "trooper_name")
    _emit_record_initializer(code, ID26_LANDCRUISER, RECORD26_OFFSET, "landcruiser_name")
    code.emit(b"\x8B\xCE")
    code.call(ORIGINAL_SECONDARY_INITIALIZER_VA)
    code.emit(b"\x5E\xC3")

    code.align()
    code.label("forward_class_map")
    # Sparse exception: only class T1/local7 is redirected to physical ID26.
    code.emit(b"\x83\x79\x10\x00")  # cmp dword ptr [ecx+10], 0
    code.jne("forward_dense")
    code.emit(b"\x83\x79\x14\x07")  # cmp dword ptr [ecx+14], 7
    code.jne("forward_dense")
    code.emit(b"\xB8\x1A\x00\x00\x00\xC3")
    code.label("forward_dense")
    code.emit(b"\x8B\x41\x10\x83\xE8\x00")  # replay retail MOV/SUB prefix
    code.jump(0x481E26)

    code.align()
    code.label("reverse_class_map")
    code.emit(b"\x81\x7C\x24\x04\x1A\x00\x00\x00")  # arg == 26?
    code.jne("reverse_dense")
    code.emit(b"\x56\x8B\xF1")  # match retail prologue and preserve caller ESI
    code.emit(b"\xC7\x46\x10\x00\x00\x00\x00")  # state.class = T1
    code.emit(b"\xC7\x46\x14\x07\x00\x00\x00")  # state.local = 7
    code.jump(0x481E89)  # shared localization/update tail and original RET 4
    code.label("reverse_dense")
    code.emit(b"\x8B\x44\x24\x04\x56")  # replay retail MOV/PUSH prefix
    code.jump(0x481E55)

    code.align()
    code.label("display_selector")
    code.emit(b"\x8B\xF8\x8B\xDF\x83\xFB\x1A")  # EDI=ID; EBX=ID; cmp EBX,26
    code.jne("display_get_registry")
    code.emit(b"\x31\xDB")  # ID26 only: reuse ID0 localization selector
    code.label("display_get_registry")
    code.call(0x45A3C0)
    code.jump(0x4819C4)

    code.align()
    code.label("id26_unlock")
    code.emit(b"\x51")  # preserve registry-record pointer across original unlock call
    code.call(0x45A150)
    code.emit(b"\x59\x83\x79\x04\x1A")  # restore ECX; test record.ID == 26
    code.jne("unlock_return")
    code.emit(b"\xB0\x01")
    code.label("unlock_return")
    code.emit(b"\xC3")

    code.align(4)
    code.label("trooper_name")
    code.emit(b"Trooper\x00")
    code.label("landcruiser_name")
    code.emit(b"Landcruiser\x00")
    payload = code.build()
    if len(payload) > 0xD60:
        raise PatchError(f"code-cave payload too large: 0x{len(payload):X}")
    return payload, {name: STUB_VA + offset for name, offset in code.labels.items()}


def _operation(name: str, category: str, offset: int, original: bytes,
               replacement: bytes, purpose: str, *, va: int | None = None) -> dict[str, Any]:
    if len(original) != len(replacement):
        raise PatchError(f"operation changes file length: {name}")
    return {
        "name": name,
        "category": category,
        "file_offset": offset,
        "virtual_address": va,
        "rva": None if va is None else va - IMAGE_BASE,
        "original_bytes": original.hex(),
        "replacement_bytes": replacement.hex(),
        "semantic_purpose": purpose,
    }


def _add_va_patch(data: bytes, pe: dict, operations: list[dict[str, Any]], *,
                  name: str, category: str, va: int, original: bytes,
                  replacement: bytes, purpose: str, patch_va: int | None = None) -> None:
    target_va = va if patch_va is None else patch_va
    offset = va_to_file_offset(pe, target_va, len(original))
    actual = data[offset:offset + len(original)]
    if actual != original:
        raise PatchError(
            f"expected original bytes mismatch for {name} at 0x{target_va:X}: "
            f"expected {original.hex()}, got {actual.hex()}"
        )
    operations.append(_operation(name, category, offset, original, replacement,
                                 purpose, va=target_va))


def _rel32_call(call_va: int, target_va: int) -> bytes:
    delta = target_va - (call_va + 5)
    if not -(1 << 31) <= delta < (1 << 31):
        raise PatchError("relative call target out of range")
    return b"\xE8" + struct.pack("<i", delta)


def _rel32_jump(jump_va: int, target_va: int) -> bytes:
    delta = target_va - (jump_va + 5)
    if not -(1 << 31) <= delta < (1 << 31):
        raise PatchError("relative jump target out of range")
    return b"\xE9" + struct.pack("<i", delta)


SECONDARY_INIT_LEAS = (
    (0x4598FA, 0x54C), (0x45992B, 0x578), (0x459959, 0x5A4),
    (0x459987, 0x5D0), (0x4599B5, 0x5FC), (0x4599E3, 0x628),
    (0x459A11, 0x654), (0x459A3F, 0x680), (0x459A6D, 0x6AC),
    (0x459A9B, 0x6D8), (0x459AC9, 0x704), (0x459AF7, 0x730),
    (0x459B25, 0x75C), (0x459B53, 0x788), (0x459B81, 0x7B4),
    (0x459BAF, 0x7E0), (0x459BDD, 0x80C), (0x459C0B, 0x838),
    (0x459C39, 0x864), (0x459C67, 0x890), (0x459C95, 0x8BC),
    (0x459CC3, 0x8E8), (0x459CF1, 0x914), (0x459D1F, 0x940),
    (0x459D4D, 0x96C), (0x459D7B, 0x998), (0x459DA9, 0x9C4),
    (0x459DD7, 0x9F0), (0x459E05, 0xA1C), (0x459E33, 0xA48),
    (0x459E61, 0xA74), (0x459E8F, 0xAA0), (0x459EBD, 0xACC),
    (0x459EEB, 0xAF8), (0x459F19, 0xB24), (0x459F47, 0xB50),
    (0x459F75, 0xB7C), (0x459FA3, 0xBA8), (0x459FD1, 0xBD4),
)

# Each instruction indexes the 39-row secondary array by its original base.
# The independent object at 0x40A6B9 is intentionally absent.
SECONDARY_CONSUMER_DISPS = (
    (0x449CAD, 0x568),
    (0x45003B, 0x570), (0x4500B0, 0x574), (0x45010E, 0x574),
    (0x45EC29, 0x570), (0x45EC35, 0x574),
    (0x47B83D, 0x568),
    (0x47ED43, 0x558), (0x47ED53, 0x550),
    (0x47F155, 0x56C), (0x47F1F2, 0x55C),
)


def build_operations(data: bytes, pe: dict) -> tuple[list[dict[str, Any]], bytes, dict[str, int], int]:
    payload, entrypoints = build_code_payload()
    text = pe["sections"][0]
    text_start_va = IMAGE_BASE + text["rva"]
    relative_end = STUB_VA - text_start_va + len(payload)
    new_virtual_size = max(text["virtual_size"], relative_end)
    if relative_end > text["raw_size"]:
        raise PatchError("code-cave payload extends beyond .text raw data")
    if text["rva"] + new_virtual_size >= pe["sections"][1]["rva"]:
        raise PatchError("expanded .text virtual range would overlap .rdata")
    cave_offset = va_to_file_offset(pe, STUB_VA, len(payload))
    if data[cave_offset:cave_offset + len(payload)] != b"\x00" * len(payload):
        raise PatchError("code-cave region is not entirely zero-filled in clean retail")

    operations: list[dict[str, Any]] = []
    # PE section-header fields are file offsets rather than virtual addresses.
    operations.append(_operation(
        "pe_text_virtual_size", "pe-bookkeeping", text["header_offset"] + 8,
        struct.pack("<I", TEXT_VIRTUAL_SIZE_OLD), struct.pack("<I", new_virtual_size),
        "map the read-only code-cave tail containing ID26 initializers and bounded wrappers"))

    _add_va_patch(data, pe, operations, name="registry_object_allocation", category="registry-allocation",
                  va=REGISTRY_ALLOCATOR_IMMEDIATE_VA, original=struct.pack("<I", OLD_REGISTRY_BYTES),
                  replacement=struct.pack("<I", NEW_REGISTRY_BYTES),
                  purpose="allocate header + 27 VehicleRecords + 39 RaceTest rows")
    _add_va_patch(data, pe, operations, name="construct_vehicle_record_count", category="construction",
                  va=0x458CF4, original=b"\x1A", replacement=b"\x1B",
                  purpose="default-construct 27 records before full initialization")
    _add_va_patch(data, pe, operations, name="construct_racetest_base", category="construction",
                  va=0x458D12, original=struct.pack("<I", RACETEST_OFFSET_OLD),
                  replacement=struct.pack("<I", RACETEST_OFFSET_NEW),
                  purpose="start the adjacent 39-row array after 27 VehicleRecords")
    _add_va_patch(data, pe, operations, name="destroy_racetest_base", category="destruction",
                  va=0x458E2C, original=struct.pack("<I", RACETEST_OFFSET_OLD),
                  replacement=struct.pack("<I", RACETEST_OFFSET_NEW),
                  purpose="destroy the same 39 rows from their relocated base")
    _add_va_patch(data, pe, operations, name="destroy_vehicle_record_count", category="destruction",
                  va=0x458E46, original=b"\x1A", replacement=b"\x1B",
                  purpose="run the VehicleRecord destructor exactly 27 times")
    _add_va_patch(data, pe, operations, name="construction_unwind_record_count", category="exception-unwind",
                  va=0x686796, original=b"\x1A", replacement=b"\x1B",
                  purpose="unwind all constructed VehicleRecords if array construction throws")
    _add_va_patch(data, pe, operations, name="construction_unwind_racetest_base", category="exception-unwind",
                  va=0x6867B3, original=struct.pack("<I", RACETEST_OFFSET_OLD),
                  replacement=struct.pack("<I", RACETEST_OFFSET_NEW),
                  purpose="unwind RaceTest records from their relocated base")

    for index, (va, old_disp) in enumerate(SECONDARY_INIT_LEAS):
        start = va_to_file_offset(pe, va, 6)
        original = data[start:start + 6]
        expected = b"\x8D\x8E" + struct.pack("<I", old_disp)
        if original != expected:
            raise PatchError(f"unexpected secondary initializer LEA #{index} at 0x{va:X}")
        _add_va_patch(data, pe, operations, name=f"racetest_initializer_base_{index:02d}",
                      category="secondary-array-construction", va=va + 2,
                      original=struct.pack("<I", old_disp),
                      replacement=struct.pack("<I", old_disp + RECORD_STRIDE),
                      purpose=f"retarget RaceTest row {index} into the relocated 39-row array")

    for va, old_disp in SECONDARY_CONSUMER_DISPS:
        offset = va_to_file_offset(pe, va, 7)
        instruction = data[offset:offset + 7]
        if instruction[3:7] != struct.pack("<I", old_disp):
            raise PatchError(f"unexpected secondary-array displacement at 0x{va:X}")
        _add_va_patch(data, pe, operations, name=f"racetest_consumer_{va:08x}",
                      category="secondary-array-consumer", va=va + 3,
                      original=struct.pack("<I", old_disp),
                      replacement=struct.pack("<I", old_disp + RECORD_STRIDE),
                      purpose="retarget an indexed RaceTest field after VehicleRecord[26]")

    # P0 class capacity: T1=8, preserve the already-confirmed T3=12 and T2=7.
    _add_va_patch(data, pe, operations, name="frontend_t1_capacity", category="frontend-capacity",
                  va=0x480A4B, original=b"\x07\x00\x00\x00", replacement=b"\x08\x00\x00\x00",
                  purpose="expose eight T1 class-local entries")
    _add_va_patch(data, pe, operations, name="frontend_t3_capacity_id25_compat", category="frontend-capacity",
                  va=0x480A65, original=b"\x0B", replacement=b"\x0C",
                  purpose="retain the E0.2-tested 12-entry T3 capacity and ID25")

    _add_va_patch(data, pe, operations, name="forward_sparse_t1_mapping_hook", category="class-mapping",
                  va=0x481E20,
                  original=bytes.fromhex("8b411083e800"),
                  replacement=_rel32_jump(0x481E20, entrypoints["forward_class_map"]) + b"\x90",
                  purpose="map T1/local7 to physical ID26 and replay original dense mapping otherwise")
    _add_va_patch(data, pe, operations, name="reverse_sparse_t1_mapping_hook", category="class-mapping",
                  va=0x481E50,
                  original=bytes.fromhex("8b44240456"),
                  replacement=_rel32_jump(0x481E50, entrypoints["reverse_class_map"]),
                  purpose="map absolute ID26 to T1/local7 and replay original reverse mapping otherwise")

    _add_va_patch(data, pe, operations, name="id25_test_unlock", category="unlock-policy",
                  va=0x45A282, original=bytes.fromhex("6a0fe887"),
                  replacement=bytes.fromhex("b0015ec3"),
                  purpose="preserve the established test-selectable ID25 Trooper profile")
    _add_va_patch(data, pe, operations, name="id26_narrow_unlock_call", category="unlock-policy",
                  va=0x4819CE, original=_rel32_call(0x4819CE, 0x45A150),
                  replacement=_rel32_call(0x4819CE, entrypoints["id26_unlock"]),
                  purpose="force only selected ID26 unlocked after the original gate")

    _add_va_patch(data, pe, operations, name="display_identity_selector_hook", category="display-localization",
                  va=0x4819BD, original=bytes.fromhex("8bf8e8fc89fdff"),
                  replacement=_rel32_jump(0x4819BD, entrypoints["display_selector"]) + b"\x90\x90",
                  purpose="retain absolute ID26 while selecting donor ID0 localization only")
    _add_va_patch(data, pe, operations, name="display_group_33_selector", category="display-localization",
                  va=0x481A10, original=b"\x57", replacement=b"\x53",
                  purpose="use the donor selector for localization group 0x33")
    _add_va_patch(data, pe, operations, name="display_group_34_selector", category="display-localization",
                  va=0x481A4D, original=b"\x57", replacement=b"\x53",
                  purpose="use the donor selector for localization group 0x34")

    _add_va_patch(data, pe, operations, name="combined_registry_initializer_hook", category="record-initialization",
                  va=REGISTRY_HOOK_VA,
                  original=_rel32_call(REGISTRY_HOOK_VA, ORIGINAL_SECONDARY_INITIALIZER_VA),
                  replacement=_rel32_call(REGISTRY_HOOK_VA, entrypoints["registry_init"]),
                  purpose="full-initialize Trooper ID25 and donor ID26, then run the original secondary initializer")

    section_cave = data[cave_offset:cave_offset + len(payload)]
    operations.append(_operation(
        "id26_code_cave_payload", "record-initialization-and-bounded-wrappers", cave_offset,
        section_cave, payload,
        "owned-string full initializers, sparse maps, display selector, and narrow unlock wrapper",
        va=STUB_VA))
    return operations, payload, entrypoints, new_virtual_size


def validate_operations(data: bytes, operations: list[dict[str, Any]]) -> None:
    prior_end = -1
    for operation in sorted(operations, key=lambda item: item["file_offset"]):
        start = operation["file_offset"]
        original = bytes.fromhex(operation["original_bytes"])
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if start < prior_end or start < 0 or start + len(original) > len(data):
            raise PatchError(f"overlapping or out-of-bounds operation: {operation['name']}")
        if data[start:start + len(original)] != original:
            raise PatchError(f"source byte check failed: {operation['name']} at 0x{start:X}")
        if len(original) != len(replacement):
            raise PatchError(f"operation changes file length: {operation['name']}")
        prior_end = start + len(original)


def make_candidate(data: bytes, *, expected_sha256: str = SOURCE_SHA256) -> tuple[bytes, dict[str, Any]]:
    digest = sha256(data)
    if digest != expected_sha256.lower():
        raise PatchError(f"unsupported retail source SHA256: {digest}")
    try:
        pe = parse_pe(data)
    except (BasePatchError, struct.error) as exc:
        raise PatchError(str(exc)) from exc
    operations, payload, entrypoints, text_virtual_size = build_operations(data, pe)
    validate_operations(data, operations)

    result = bytearray(data)
    for operation in operations:
        start = operation["file_offset"]
        result[start:start + len(bytes.fromhex(operation["replacement_bytes"]))] = bytes.fromhex(
            operation["replacement_bytes"]
        )
    candidate = bytes(result)
    for operation in operations:
        start = operation["file_offset"]
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if candidate[start:start + len(replacement)] != replacement:
            raise PatchError(f"post-patch validation failed: {operation['name']}")

    structural = {
        "registry_capacity": NEW_RECORD_COUNT,
        "registry_object_size": NEW_REGISTRY_BYTES,
        "vehicle_record_stride": RECORD_STRIDE,
        "vehicle_records_offset": RECORD0_OFFSET,
        "record25_offset": RECORD25_OFFSET,
        "record26_offset": RECORD26_OFFSET,
        "record26_end_offset": RECORD26_OFFSET + RECORD_STRIDE,
        "racetest": {
            "count": RACETEST_COUNT,
            "stride": RACETEST_STRIDE,
            "old_base": RACETEST_OFFSET_OLD,
            "new_base": RACETEST_OFFSET_NEW,
            "new_end_exclusive": RACETEST_END_NEW,
            "allocation_end_exclusive": NEW_REGISTRY_BYTES,
        },
        "id25": _profile_manifest(ID25_TROOPER, record_offset=RECORD25_OFFSET,
                                  runtime_family="Trooper"),
        "id26": _profile_manifest(ID26_LANDCRUISER, record_offset=RECORD26_OFFSET,
                                  runtime_family="Landcruiser"),
        "class_mappings": {
            "T1": {"local_0_to_6": "absolute IDs 0..6", "local_7": 26, "capacity": 8},
            "T2": {"local_0_to_6": "absolute IDs 7..13", "capacity": 7},
            "T3": {"local_0_to_11": "absolute IDs 14..25", "capacity": 12},
            "reverse_id26": {"class": 0, "local_index": 7},
        },
        "unlock": {"id25": "test-selectable (existing R5V-E profile)",
                   "id26": "test-selectable at VehicleSelect gate only"},
        "display_selector": {"id26": 0, "scope": "two localization selector pushes only"},
        "code_entrypoints": {name: f"0x{value:08X}" for name, value in entrypoints.items()},
    }
    manifest = {
        "phase": "R5V-F",
        "build": "retail",
        "profile": "duplicate-t1-id0-landcruiser",
        "source_sha256": digest,
        "patched_sha256": sha256(candidate),
        "image_base": IMAGE_BASE,
        "text_virtual_size": {"original": TEXT_VIRTUAL_SIZE_OLD,
                              "patched": text_virtual_size,
                              "code_cave_va": f"0x{STUB_VA:08X}",
                              "payload_size": len(payload)},
        "structural_self_check": structural,
        "operation_counts_by_category": _operation_counts(operations),
        "operations": operations,
        "runtime_validation": "WAITING FOR HUMAN P0",
        "risks": [
            "Campaign/save persistence for ID26 is unproven; use a disposable profile.",
            "Network/multiplayer support for ID26 is unproven; do not test online.",
            "ID26 is a test-only quick-race/practice slot; AI/event pools remain stock-only.",
        ],
    }
    # Run structural self-check against the bytes just generated.
    _verify_structural(candidate, manifest)
    return candidate, manifest


def _profile_manifest(profile: VehicleRecordProfile, *, record_offset: int,
                      runtime_family: str) -> dict[str, Any]:
    return {
        "id": profile.slot_id,
        "class": profile.vehicle_class,
        "class_local_index": profile.local_index,
        "record_offset_from_registry": record_offset,
        "internal_name": profile.internal_name,
        "runtime_family": runtime_family,
        "donor_id": profile.donor_id,
        "frontend_stats": list(profile.stats),
        "smallcarsheet_index": profile.smallcarsheet_index,
        "race_colour_rgba_bits": [f"{value:08x}" for value in profile.race_colour_rgba_bits],
        "initializer_va": f"0x{VEHICLE_INITIALIZER_VA:08X}",
        "owned_name": "temporary deep-copied by the original full initializer",
    }


def _operation_counts(operations: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for operation in operations:
        category = operation["category"]
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def _verify_structural(candidate: bytes, manifest: dict[str, Any]) -> None:
    pe_offset = struct.unpack_from("<I", candidate, 0x3C)[0]
    coff = pe_offset + 4
    optional = coff + 20
    section_count = struct.unpack_from("<H", candidate, coff + 2)[0]
    optional_size = struct.unpack_from("<H", candidate, coff + 16)[0]
    section_table = optional + optional_size
    if section_count < 1 or candidate[section_table:section_table + 8].split(b"\x00", 1)[0] != b".text":
        raise PatchError("structural self-check: missing first .text section")
    text_virtual_size = struct.unpack_from("<I", candidate, section_table + 8)[0]
    if text_virtual_size != manifest["text_virtual_size"]["patched"]:
        raise PatchError("structural self-check: .text VirtualSize mismatch")
    structural = manifest["structural_self_check"]
    if structural["registry_capacity"] != 27 or structural["record26_offset"] != 0x54C:
        raise PatchError("structural self-check: ID26 record layout mismatch")
    if structural["record26_end_offset"] > structural["racetest"]["new_base"]:
        raise PatchError("structural self-check: record26 overlaps RaceTest array")
    if structural["racetest"]["new_end_exclusive"] > structural["racetest"]["allocation_end_exclusive"]:
        raise PatchError("structural self-check: RaceTest array exceeds allocation")
    if structural["class_mappings"]["T1"]["local_7"] != 26:
        raise PatchError("structural self-check: sparse forward map missing")
    if structural["class_mappings"]["reverse_id26"] != {"class": 0, "local_index": 7}:
        raise PatchError("structural self-check: sparse reverse map missing")
    if len(SECONDARY_INIT_LEAS) != RACETEST_COUNT:
        raise PatchError("structural self-check: RaceTest initializer coverage mismatch")
    if len(SECONDARY_CONSUMER_DISPS) != 11:
        raise PatchError("structural self-check: direct consumer coverage mismatch")


def _binary_diff_text(manifest: dict[str, Any]) -> str:
    lines = [
        "R5V-F categorized binary diff",
        f"Source SHA-256: {manifest['source_sha256']}",
        f"Candidate SHA-256: {manifest['patched_sha256']}",
        "",
    ]
    for operation in manifest["operations"]:
        va = operation.get("virtual_address")
        location = f"VA 0x{va:08X}" if isinstance(va, int) else f"file 0x{operation['file_offset']:X}"
        lines.append(
            f"[{operation['category']}] {location} {operation['name']}: "
            f"{operation['original_bytes']} -> {operation['replacement_bytes']}"
        )
        lines.append(f"  {operation['semantic_purpose']}")
    return "\n".join(lines) + "\n"


def write_candidate(source: Path, output: Path, manifest_path: Path,
                    diff_path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    diff_path = diff_path.resolve(strict=False)
    if source == output or (output.exists() and os.path.samefile(source, output)):
        raise PatchError("candidate executable must not overwrite its source")
    if "research-output" not in {part.casefold() for part in output.parts}:
        raise PatchError("candidate output must be inside research-output")
    if output.exists() or (manifest_path.exists() and not dry_run) or (diff_path.exists() and not dry_run):
        raise PatchError("candidate output already exists; choose a new path")
    paths = [source, output, manifest_path, diff_path]
    if len({str(path).casefold() for path in paths}) != len(paths):
        raise PatchError("source, executable, manifest, and diff paths must be distinct")
    source_before = sha256(source.read_bytes())
    candidate, manifest = make_candidate(source.read_bytes())
    if source_before != manifest["source_sha256"]:
        raise PatchError("source changed while building candidate")
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(candidate)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        diff_path.write_text(_binary_diff_text(manifest), encoding="utf-8")
        if sha256(output.read_bytes()) != manifest["patched_sha256"]:
            raise PatchError("written candidate hash mismatch")
    return manifest


def verify_existing(source: Path, output: Path, manifest_path: Path,
                    diff_path: Path) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    diff_path = diff_path.resolve(strict=True)
    if source == output or os.path.samefile(source, output):
        raise PatchError("candidate path must differ from source")
    expected, manifest = make_candidate(source.read_bytes())
    if output.read_bytes() != expected:
        raise PatchError("candidate differs from deterministic clean-retail rebuild")
    try:
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise PatchError("invalid candidate patch manifest") from exc
    if stored != manifest:
        raise PatchError("candidate manifest differs from deterministic rebuild")
    if diff_path.read_text(encoding="utf-8") != _binary_diff_text(manifest):
        raise PatchError("categorical binary diff differs from deterministic rebuild")
    _verify_structural(output.read_bytes(), stored)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Unmodified supported retail MRallye.exe")
    parser.add_argument("output", type=Path, help="New isolated candidate path inside research-output")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--diff", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run and args.verify_existing:
        parser.error("--dry-run and --verify-existing are mutually exclusive")
    manifest_path = args.manifest or args.output.with_name("patch-manifest.json")
    diff_path = args.diff or args.output.with_name("binary-diff.txt")
    try:
        if args.verify_existing:
            manifest = verify_existing(args.source, args.output, manifest_path, diff_path)
        else:
            manifest = write_candidate(args.source, args.output, manifest_path, diff_path,
                                       dry_run=args.dry_run)
    except (PatchError, BasePatchError, OSError, struct.error) as exc:
        parser.exit(2, f"ID26 patch refused: {exc}\n")
    print(json.dumps({
        "dry_run": args.dry_run,
        "verified_existing": args.verify_existing,
        "source_sha256": manifest["source_sha256"],
        "patched_sha256": manifest["patched_sha256"],
        "operations": len(manifest["operations"]),
        "output": str(args.output),
        "runtime_validation": manifest["runtime_validation"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
