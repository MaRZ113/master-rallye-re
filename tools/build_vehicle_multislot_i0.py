#!/usr/bin/env python3
"""Build the fail-closed R5V-I.0 two-addon-slot diagnostic candidate.

The builder composes the exact H.2 result from pristine retail, then expands
the VehicleRecord/RaceTest boundary from 27 to 28 records and adds one sparse
T2/local7 diagnostic slot at physical ID27. ID27 deliberately reuses the
stock Navara runtime family and is not a second real vehicle qualification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
from typing import Any

try:
    import build_vehicle_audio_candidate as audio
    import build_vehicle_mode_ai_candidate as h2
    import build_vehicle_natural_t1_candidate as natural
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style imports for tests
    from tools import build_vehicle_audio_candidate as audio
    from tools import build_vehicle_mode_ai_candidate as h2
    from tools import build_vehicle_natural_t1_candidate as natural
    from tools import patch_vehicle_registry_id26 as registry


RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
RETAIL_SIZE = 3_121_214
H2_SHA256 = "de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9"
PROFILE = "i0-two-addon-slots-id27-t2-diagnostic"
CODE_CAVE_VA = 0x0068E800
CODE_CAVE_SIZE = 0x800
TEXT_BASE_VA = 0x00401000
RDATA_RVA = 0x0028F000
RACETEST_COUNT = 39
RACETEST_STRIDE = 0x2C
RECORD_STRIDE = 0x34
REGISTRY_HEADER_SIZE = 4
LEGACY_RECORD_COUNT = 26  # physical records 0..25, including the Trooper slot

REGISTRY_ALLOCATOR_VA = 0x0045A3E0
CONSTRUCT_RECORD_COUNT_VA = 0x00458CF4
CONSTRUCT_RACETEST_BASE_VA = 0x00458D12
DESTRUCT_RACETEST_BASE_VA = 0x00458E2C
DESTRUCT_RECORD_COUNT_VA = 0x00458E46
UNWIND_RECORD_COUNT_VA = 0x00686796
UNWIND_RACETEST_BASE_VA = 0x006867B3
REGISTRY_INITIALIZER_CALL_VA = 0x00458D3F
FORWARD_CLASS_HOOK_VA = 0x00481E20
REVERSE_CLASS_HOOK_VA = 0x00481E50
UNLOCK_CALL_VA = 0x004819CE
LOCKED_REASON_HOOK_VA = 0x00481ACF
CAPACITY_T2_IMMEDIATE_VA = 0x0068E63F
AUDIO_PROFILE_CALL_VA = audio.ID26_AUDIO_LOOKUP_CALL_VA

QUICKRACE_T2_HOOK_VA = 0x004581B4
QUICKRACE_T2_REENTRY_VA = 0x0045817F
QUICKRACE_T2_EXIT_VA = 0x004582D5
CUP_T2_HOOK_VA = 0x0045AD53
CUP_T2_REENTRY_VA = 0x0045AD1E
CUP_T2_EXIT_VA = 0x0045AE66
MASTER_T2_HOOK_VA = 0x00451F18
MASTER_T2_REENTRY_VA = 0x00451EE3
MASTER_T2_EXIT_VA = 0x0045202B

T1_PHYSICAL_IDS = tuple(range(7)) + (26,)
T2_PHYSICAL_IDS = tuple(range(7, 14)) + (27,)
T3_BASE_PHYSICAL_IDS = tuple(range(14, 21))
RESULTS_ID27 = "ID27 SLOT PROOF"
DISPLAY_ID27_MANUFACTURER = "SLOT PROOF"
DISPLAY_ID27_MODEL = "NAVARA DONOR"
DISPLAY_ID27_COMBINED = "SLOT PROOF NAVARA"


class CandidateError(ValueError):
    """Unsupported input, unexpected bytes, or unsafe composed layout."""


ID27_RECORD = replace(
    registry.ID26_MERCEDES_G1_STOCK_UNLOCK,
    profile_id="i0-id27-navara-donor-slot-proof",
    slot_id=27,
    vehicle_class=1,
    local_index=7,
    internal_name="Navara",
    stats=(7, 6, 6, 5),
    smallcarsheet_index=13,
    race_colour_rgba_bits=(0x00000000, 0x3F800000, 0x3F800000, 0x3F800000),
    donor_id=7,
    runtime_family="Navara",
    vehicle_select_icon_frame=23,
    display_selector_by_group=(),
    unlock_policy="mirror-stock-vehicle-id-10",
    race_colour_role="cyan physical-ID27 slot canary; not authentic addon art",
    display_manufacturer=DISPLAY_ID27_MANUFACTURER,
    display_model=DISPLAY_ID27_MODEL,
    display_quickrace=DISPLAY_ID27_COMBINED,
    asset_package="retail Data.sma / DataGx/Vehicles/Navara",
    model_family="Navara",
    wheel_family="Navara",
    physics_family="Vehicles/Navara",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel32(source_va: int, target_va: int, opcode: int = 0xE9) -> bytes:
    delta = target_va - (source_va + 5)
    if not -(1 << 31) <= delta < (1 << 31):
        raise CandidateError("relative branch target is outside x86 rel32 range")
    return bytes((opcode,)) + struct.pack("<i", delta)


def _call_rel32(call_va: int, target_va: int) -> bytes:
    return _rel32(call_va, target_va, 0xE8)


def registry_layout(highest_physical_id: int) -> dict[str, int]:
    if type(highest_physical_id) is not int or highest_physical_id < LEGACY_RECORD_COUNT - 1:
        raise CandidateError("highest physical ID must include the 26 stock records")
    record_count = highest_physical_id + 1
    racetest_base = REGISTRY_HEADER_SIZE + record_count * RECORD_STRIDE
    allocation_size = racetest_base + RACETEST_COUNT * RACETEST_STRIDE
    return {
        "highest_physical_id": highest_physical_id,
        "record_count": record_count,
        "record25_offset": REGISTRY_HEADER_SIZE + 25 * RECORD_STRIDE,
        "record26_offset": REGISTRY_HEADER_SIZE + 26 * RECORD_STRIDE,
        "record27_offset": REGISTRY_HEADER_SIZE + 27 * RECORD_STRIDE,
        "racetest_base": racetest_base,
        "racetest_count": RACETEST_COUNT,
        "racetest_stride": RACETEST_STRIDE,
        "allocation_size": allocation_size,
    }


def class_local_to_physical(class_id: int, local_index: int) -> int:
    if type(class_id) is not int or type(local_index) is not int:
        raise CandidateError("class and local index must be integers")
    if class_id == 0 and local_index == 7:
        return 26
    if class_id == 1 and local_index == 7:
        return 27
    if class_id == 0 and 0 <= local_index < 7:
        return local_index
    if class_id == 1 and 0 <= local_index < 7:
        return 7 + local_index
    if class_id == 2 and 0 <= local_index < 12:
        return 14 + local_index
    raise CandidateError(f"invalid vehicle class/local pair: {class_id}/{local_index}")


def physical_to_class_local(physical_id: int) -> tuple[int, int]:
    if type(physical_id) is not int or not 0 <= physical_id <= 27:
        raise CandidateError(f"invalid physical vehicle ID: {physical_id!r}")
    if physical_id == 26:
        return (0, 7)
    if physical_id == 27:
        return (1, 7)
    if physical_id < 7:
        return (0, physical_id)
    if physical_id < 14:
        return (1, physical_id - 7)
    if physical_id < 25:
        return (2, physical_id - 14)
    return (2, 11)  # physical ID25 is the existing Trooper record


def unlock_oracle(physical_id: int) -> int:
    if physical_id == 26:
        return 3
    if physical_id == 27:
        return 10
    return physical_id


def locked_reason_selector(physical_id: int) -> int | None:
    # Stock group-6 selector mapping from FUN_004819B0. ID26's existing
    # qualified mirror remains ID3/selector9; ID27 reuses ID10/selector12.
    return {26: 9, 27: 12}.get(physical_id)


def audio_profile_for(physical_id: int) -> int:
    if physical_id == 26:
        return 0
    if physical_id == 27:
        return 7
    return physical_id


def pool_for_mode(mode: str, class_id: int,
                  excluded_ids: tuple[int, ...] | list[int] = ()) -> list[int]:
    if mode not in {"quickrace", "rallye_cup", "master_rallye"}:
        raise CandidateError(f"I.0 does not add ID27 to mode {mode!r}")
    if len(excluded_ids) > 2 or any(type(item) is not int for item in excluded_ids):
        raise CandidateError("native roster supports at most two integer exclusions")
    if class_id == 0:
        source = list(T1_PHYSICAL_IDS)
    elif class_id == 1:
        source = list(T2_PHYSICAL_IDS)
    elif class_id in (2, 4):
        source = list(T3_BASE_PHYSICAL_IDS)
    else:
        raise CandidateError(f"unsupported stock class selector: {class_id}")
    excluded = {item for item in excluded_ids if item >= 0}
    result = [item for item in source if item not in excluded]
    if class_id == 0 and 7 in result:
        raise CandidateError("physical ID7 is T2 and may not enter the T1 pool")
    if class_id == 1 and 14 in result:
        raise CandidateError("physical ID14 is T3 and may not enter the T2 pool")
    return result


def _operation(name: str, category: str, offset: int, original: bytes,
               replacement: bytes, purpose: str, *, va: int | None = None) -> dict[str, Any]:
    if len(original) != len(replacement):
        raise CandidateError(f"size-changing operation is not allowed: {name}")
    return {
        "name": name,
        "category": category,
        "file_offset": offset,
        "virtual_address": va,
        "original_bytes": original.hex(),
        "replacement_bytes": replacement.hex(),
        "semantic_purpose": purpose,
    }


def _add_va_operation(base: bytes, pe: dict[str, Any], operations: list[dict[str, Any]], *,
                      name: str, category: str, va: int, replacement: bytes,
                      purpose: str, expected: bytes | None = None) -> None:
    offset = registry.va_to_file_offset(pe, va, len(replacement))
    original = base[offset:offset + len(replacement)]
    if expected is not None and original != expected:
        raise CandidateError(
            f"H.2 intermediate byte mismatch for {name} at 0x{va:08X}: "
            f"expected {expected.hex()}, got {original.hex()}"
        )
    operations.append(_operation(name, category, offset, original, replacement,
                                  purpose, va=va))


def _validate_operations(base: bytes, operations: list[dict[str, Any]]) -> None:
    prior_end = -1
    for op in sorted(operations, key=lambda item: item["file_offset"]):
        start = op["file_offset"]
        original = bytes.fromhex(op["original_bytes"])
        replacement = bytes.fromhex(op["replacement_bytes"])
        if start < prior_end or start < 0 or start + len(original) > len(base):
            raise CandidateError(f"overlapping or out-of-bounds patch operation: {op['name']}")
        if len(original) != len(replacement):
            raise CandidateError(f"non-size-preserving patch operation: {op['name']}")
        if base[start:start + len(original)] != original:
            raise CandidateError(f"H.2 original bytes changed at {op['name']}")
        prior_end = start + len(original)


def _apply_layer(base: bytes, operations: list[dict[str, Any]]) -> bytes:
    _validate_operations(base, operations)
    result = bytearray(base)
    for op in operations:
        start = op["file_offset"]
        result[start:start + len(bytes.fromhex(op["replacement_bytes"]))] = bytes.fromhex(
            op["replacement_bytes"]
        )
    candidate = bytes(result)
    inverse = bytearray(candidate)
    for op in reversed(operations):
        start = op["file_offset"]
        original = bytes.fromhex(op["original_bytes"])
        replacement = bytes.fromhex(op["replacement_bytes"])
        if inverse[start:start + len(replacement)] != replacement:
            raise CandidateError(f"post-patch range differs at {op['name']}")
        inverse[start:start + len(original)] = original
    if bytes(inverse) != base:
        raise CandidateError("I.0 operation inverse does not restore exact H.2 intermediate")
    return candidate


def _comparison_bytes(code: registry._CodeImage, register: str, immediate: int) -> None:
    if register == "eax":
        code.emit(b"\x3D" + struct.pack("<I", immediate))
    elif register == "ecx":
        code.emit(b"\x81\xF9" + struct.pack("<I", immediate))
    elif register == "edi":
        code.emit(b"\x81\xFF" + struct.pack("<I", immediate))
    elif register == "esi":
        code.emit(b"\x81\xFE" + struct.pack("<I", immediate))
    else:  # pragma: no cover - internal constant guard
        raise CandidateError(f"unsupported x86 comparison register: {register}")


def _emit_id27_display_bridge(code: registry._CodeImage, *, label: str,
                              register: str, old_helper: int, text_label: str,
                              resume_va: int) -> None:
    code.label(label)
    _comparison_bytes(code, register, 27)
    code.jne(label + "_stock")
    code.mov_eax_literal(text_label)
    code.jump(resume_va)
    code.label(label + "_stock")
    code.jump(old_helper)


def t2_append_stub_bytes(stub_va: int, reentry_va: int,
                         common_exit_va: int) -> bytes:
    """Append sparse ID27 through the native human/duplicate exclusion and append body."""
    code = bytearray(bytes.fromhex("83FE1C740A"))  # ESI=28 means second visit
    code.extend(b"\xBE" + struct.pack("<I", 27))  # ESI=physical ID27
    code.extend(_rel32(stub_va + len(code), reentry_va))
    code.extend(b"\xBE" + struct.pack("<I", 14))  # restore stock T2 end sentinel
    code.extend(_rel32(stub_va + len(code), common_exit_va))
    if len(code) != 25:
        raise CandidateError("unexpected T2 append-stub size")
    return bytes(code)


def build_code_payload(h2_manifest: dict[str, Any]) -> tuple[bytes, dict[str, int]]:
    prior = h2_manifest.get("base_manifest", {})
    structural = prior.get("structural_self_check", {})
    old_entries = structural.get("code_entrypoints", {})
    if not isinstance(old_entries, dict):
        raise CandidateError("H.2 manifest has no audited code-entrypoint map")

    code = registry._CodeImage(CODE_CAVE_VA)

    # Keep the original G.1/H.2 initialization intact, then initialize ID27
    # before the native constructor returns. H.2's secondary initializer now
    # addresses RaceTest at 0x5B4, so it cannot overwrite record27 [0x580,0x5B4).
    code.label("multi_addon_registry_init")
    code.emit(b"\x56\x8B\xF1\x8B\xCE")  # save ESI; ESI/ECX = registry
    code.call(int(old_entries["registry_init"], 16))
    registry._emit_record_initializer(code, ID27_RECORD, 0x580, "id27_internal_name")
    # FUN_00458CD0 returns its registry pointer in EAX; keep that ABI after
    # adding the extra record initializer.
    code.emit(b"\x8B\xC6\x5E\xC3")

    code.align()
    code.label("forward_class_map_multi_addon")
    code.emit(b"\x83\x79\x10\x01")  # [ECX+10] == T2
    code.jne("forward_class_map_id26_stock")
    code.emit(b"\x83\x79\x18\x07")  # T2 local index is [ECX+0x18]
    code.jne("forward_class_map_id26_stock")
    code.emit(b"\xB8\x1B\x00\x00\x00\xC3")  # EAX=27; return
    code.label("forward_class_map_id26_stock")
    code.jump(int(old_entries["forward_class_map"], 16))

    code.align()
    code.label("reverse_class_map_multi_addon")
    code.emit(b"\x83\x7C\x24\x04\x1B")  # [ESP+4] == physical ID27
    code.jne("reverse_class_map_id26_stock")
    code.emit(b"\x56\x8B\xF1")
    code.emit(b"\xC7\x46\x10\x01\x00\x00\x00")  # class T2
    code.emit(b"\xC7\x46\x14\x07\x00\x00\x00")  # local7
    code.jump(0x00481E89)
    code.label("reverse_class_map_id26_stock")
    code.jump(int(old_entries["reverse_class_map"], 16))

    code.align()
    _emit_id27_display_bridge(
        code, label="vehicle_select_manufacturer_id27", register="edi",
        old_helper=int(old_entries["vehicle_select_manufacturer_lookup"], 16),
        text_label="id27_manufacturer_text", resume_va=0x00481A18)
    code.align()
    _emit_id27_display_bridge(
        code, label="vehicle_select_model_id27", register="edi",
        old_helper=int(old_entries["vehicle_select_model_lookup"], 16),
        text_label="id27_model_text", resume_va=0x00481A55)

    quick_calls = registry.QUICKRACE_LOCALIZATION_CALLS
    for index, call_va in enumerate(quick_calls):
        code.align()
        _emit_id27_display_bridge(
            code, label=f"quickrace_name_id27_{index}", register="eax",
            old_helper=int(old_entries[f"quickrace_name_lookup_{index}"], 16),
            text_label="id27_combined_text", resume_va=call_va + 8)

    for suffix, group, label, text_label, resume in (
        ("manufacturer", 0x33, "race_options_manufacturer_lookup", "id27_manufacturer_text", 0x0047A669),
        ("model", 0x34, "race_options_model_lookup", "id27_model_text", 0x0047A6CE),
    ):
        _ = group, suffix
        code.align()
        _emit_id27_display_bridge(
            code, label=f"{label}_id27", register="esi",
            old_helper=int(old_entries[label], 16), text_label=text_label,
            resume_va=resume)

    for _hook, _slot, label, _group, call_va, resume_va in registry.RACE_DETAILS_LOCALIZATION_CALLS:
        code.align()
        old_label = f"race_details_name_lookup_{label}"
        _emit_id27_display_bridge(
            code, label=f"{old_label}_id27", register="eax",
            old_helper=int(old_entries[old_label], 16),
            text_label="id27_combined_text", resume_va=resume_va)

    code.align()
    _emit_id27_display_bridge(
        code, label="vehicle_setup_name_lookup_id27", register="edi",
        old_helper=int(old_entries["vehicle_setup_name_lookup"], 16),
        text_label="id27_combined_text", resume_va=0x0044FA33)

    code.align()
    code.label("results_name_id27_bridge")
    old_results_prefix = natural.results_name_stub_bytes()[:8]
    code.emit(old_results_prefix)
    code.emit(b"\x83\xF9\x1B")  # extracted participant CarID == 27
    code.jne("results_name_id26_native")
    code.mov_eax_literal("id27_results_text")
    code.jump(natural.RESULTS_AFTER_LOOKUP_VA)
    code.label("results_name_id26_native")
    code.jump(natural.RESULTS_NAME_STUB_VA)

    code.align()
    code.label("multi_addon_unlock")
    code.emit(b"\x51\x83\x79\x04\x1B")  # save ECX; record physical ID == 27
    code.jne("unlock_id26_and_stock")
    code.emit(b"\x83\xEC\x08")
    code.emit(b"\xC7\x04\x24\x00\x00\x00\x00")
    code.emit(b"\xC7\x44\x24\x04\x0A\x00\x00\x00")  # oracle ID10
    code.emit(b"\x8D\x0C\x24")
    code.call(0x0045A150)
    code.emit(b"\x83\xC4\x08\x59\xC3")
    code.label("unlock_id26_and_stock")
    code.emit(b"\x59")
    code.jump(int(old_entries["id26_unlock"], 16))

    code.align()
    code.label("locked_reason_id27_bridge")
    # The native switch receives physical ID - 3 in EAX; ID27 therefore
    # arrives as 24. Stock ID10's group-6 selector is 12 in EBX.
    code.emit(b"\x83\xF8\x18")
    code.jne("locked_reason_id26_native")
    code.emit(b"\xBB\x0C\x00\x00\x00")
    code.jump(0x00481B49)
    code.label("locked_reason_id26_native")
    code.jump(int(old_entries["id26_locked_reason_lookup"], 16))

    code.align()
    code.label("multi_addon_audio_profile")
    code.emit(b"\xFF\x74\x24\x04")  # copy original slot parameter
    code.call(audio.RACE_CAR_ID_GETTER_VA)
    code.emit(b"\x83\xF8\x1B")
    code.je("audio_profile_id27")
    code.emit(b"\x83\xF8\x1A")
    code.je("audio_profile_id26")
    code.emit(b"\xC2\x04\x00")  # stock IDs returned unchanged
    code.label("audio_profile_id26")
    code.emit(b"\x31\xC0\xC2\x04\x00")  # ID26 -> profile0
    code.label("audio_profile_id27")
    code.emit(b"\xB8\x07\x00\x00\x00\xC2\x04\x00")  # ID27 -> profile7

    for name, reentry, exit_va in (
        ("quickrace_t2_id27_append", QUICKRACE_T2_REENTRY_VA, QUICKRACE_T2_EXIT_VA),
        ("rallyecup_t2_id27_append", CUP_T2_REENTRY_VA, CUP_T2_EXIT_VA),
        ("masterrallye_t2_id27_append", MASTER_T2_REENTRY_VA, MASTER_T2_EXIT_VA),
    ):
        code.align(4)
        code.label(name)
        stub = t2_append_stub_bytes(code.va, reentry, exit_va)
        code.emit(stub)

    code.align(4)
    code.label("id27_internal_name")
    code.emit(b"Navara\x00")
    code.label("id27_manufacturer_text")
    code.emit(DISPLAY_ID27_MANUFACTURER.encode("ascii") + b"\x00")
    code.label("id27_model_text")
    code.emit(DISPLAY_ID27_MODEL.encode("ascii") + b"\x00")
    code.label("id27_combined_text")
    code.emit(DISPLAY_ID27_COMBINED.encode("ascii") + b"\x00")
    code.label("id27_results_text")
    code.emit(RESULTS_ID27.encode("ascii") + b"\x00")

    payload = code.build()
    if len(payload) > CODE_CAVE_SIZE:
        raise CandidateError(f"I.0 code-cave payload exceeds audited fresh range: 0x{len(payload):X}")
    return payload, {name: code.base_va + offset for name, offset in code.labels.items()}


def make_candidate(data: bytes) -> tuple[bytes, dict[str, Any]]:
    source_hash = sha256(data)
    if source_hash != RETAIL_SHA256 or len(data) != RETAIL_SIZE:
        raise CandidateError(f"unsupported pristine retail image: SHA256={source_hash}, size={len(data)}")
    try:
        parent, parent_manifest = h2.make_candidate(data)
    except (h2.CandidateError, audio.CandidateError, registry.PatchError, ValueError) as exc:
        raise CandidateError(f"could not reproduce the exact H.2 parent: {exc}") from exc
    parent_hash = sha256(parent)
    if parent_hash != H2_SHA256:
        raise CandidateError(f"exact H.2 intermediate mismatch: {parent_hash}")

    pe = registry.parse_pe(data)
    layout = registry_layout(27)
    expected_layout = {
        "record_count": 28, "record25_offset": 0x518,
        "record26_offset": 0x54C, "record27_offset": 0x580,
        "racetest_base": 0x5B4, "allocation_size": 0xC68,
    }
    for key, expected in expected_layout.items():
        if layout[key] != expected:
            raise CandidateError(f"internal two-addon layout error for {key}: {layout[key]:#x}")

    payload, entrypoints = build_code_payload(parent_manifest)
    cave_offset = registry.va_to_file_offset(pe, CODE_CAVE_VA, len(payload))
    if parent[cave_offset:cave_offset + len(payload)] != bytes(len(payload)):
        raise CandidateError("fresh I.0 code cave is not zero-filled in the exact H.2 parent")

    text = pe["sections"][0]
    rdata = next(section for section in pe["sections"] if section["name"] == ".rdata")
    current_vsize = struct.unpack_from("<I", parent, text["header_offset"] + 8)[0]
    if current_vsize != parent_manifest["text_virtual_size"]["patched"]:
        raise CandidateError("H.2 .text VirtualSize does not match its verified manifest")
    highest_end_va = CODE_CAVE_VA + len(payload)
    new_vsize = max(current_vsize, highest_end_va - (registry.IMAGE_BASE + text["rva"]))
    if highest_end_va >= registry.IMAGE_BASE + rdata["rva"]:
        raise CandidateError("I.0 cave reaches or overlaps .rdata")
    if new_vsize > text["raw_size"] or text["rva"] + new_vsize >= rdata["rva"]:
        raise CandidateError("I.0 .text VirtualSize would overlap .rdata or file-backed data")

    operations: list[dict[str, Any]] = []
    _add_va_operation(parent, pe, operations, name="registry_allocate_28_records",
                      category="registry-layout", va=REGISTRY_ALLOCATOR_VA,
                      replacement=struct.pack("<I", layout["allocation_size"]),
                      expected=struct.pack("<I", 0xC34),
                      purpose="allocate 4-byte header + 28 VehicleRecords + 39 RaceTest rows")
    for name, va in (("construct_vehicle_record_count_28", CONSTRUCT_RECORD_COUNT_VA),
                     ("destroy_vehicle_record_count_28", DESTRUCT_RECORD_COUNT_VA),
                     ("unwind_vehicle_record_count_28", UNWIND_RECORD_COUNT_VA)):
        _add_va_operation(parent, pe, operations, name=name, category="registry-lifecycle",
                          va=va, replacement=b"\x1C", expected=b"\x1B",
                          purpose="construct, destroy, or unwind all 28 physical record slots")
    for name, va in (("construct_racetest_base_0x5b4", CONSTRUCT_RACETEST_BASE_VA),
                     ("destroy_racetest_base_0x5b4", DESTRUCT_RACETEST_BASE_VA),
                     ("unwind_racetest_base_0x5b4", UNWIND_RACETEST_BASE_VA)):
        _add_va_operation(parent, pe, operations, name=name, category="secondary-array-layout",
                          va=va, replacement=struct.pack("<I", layout["racetest_base"]),
                          expected=struct.pack("<I", 0x580),
                          purpose="move RaceTest start from H.2 27-record base 0x580 to 28-record base 0x5B4")

    # Re-audited H.2 displacement sets from the native 39-row initializer and
    # its indexed consumers. Each is shifted once more by one 0x34-byte record.
    for index, (va, retail_disp) in enumerate(registry.SECONDARY_INIT_LEAS):
        _add_va_operation(parent, pe, operations,
                          name=f"racetest_initializer_{index:02d}_0x{retail_disp + 0x68:03x}",
                          category="secondary-array-construction", va=va + 2,
                          replacement=struct.pack("<I", retail_disp + 0x68),
                          expected=struct.pack("<I", retail_disp + 0x34),
                          purpose=f"retarget native RaceTest initializer row {index} after two addon records")
    for va, retail_disp in registry.SECONDARY_CONSUMER_DISPS:
        _add_va_operation(parent, pe, operations,
                          name=f"racetest_consumer_{va:08x}_0x{retail_disp + 0x68:03x}",
                          category="secondary-array-consumer", va=va + 3,
                          replacement=struct.pack("<I", retail_disp + 0x68),
                          expected=struct.pack("<I", retail_disp + 0x34),
                          purpose="retarget an indexed RaceTest consumer after VehicleRecord[27]")

    # PE header, .text-size extension, and the new ID27 full initializer.
    section_size_offset = text["header_offset"] + 8
    operations.append(_operation(
        "pe_text_virtual_size_i0_payload", "pe-bookkeeping", section_size_offset,
        struct.pack("<I", current_vsize), struct.pack("<I", new_vsize),
        "map the fresh ID27/multi-addon wrapper code cave without overlapping .rdata"))
    operations.append(_operation(
        "i0_multi_addon_code_payload", "multi-addon-code-cave", cave_offset,
        bytes(len(payload)), payload,
        "initialize physical ID27 and implement sparse mapping, display, unlock, audio, Results, and native T2 pool bridges",
        va=CODE_CAVE_VA))

    def hook(name: str, va: int, replacement: bytes, purpose: str) -> None:
        _add_va_operation(parent, pe, operations, name=name, category="multi-addon-bridge",
                          va=va, replacement=replacement, purpose=purpose)

    hook("registry_initializer_id27_wrapper_call", REGISTRY_INITIALIZER_CALL_VA,
         _call_rel32(REGISTRY_INITIALIZER_CALL_VA, entrypoints["multi_addon_registry_init"]),
         "run the exact H.2 ID25/ID26 initializer, then full-initialize ID27 before returning")
    hook("forward_sparse_t2_local7_id27", FORWARD_CLASS_HOOK_VA,
         _rel32(FORWARD_CLASS_HOOK_VA, entrypoints["forward_class_map_multi_addon"]) + b"\x90",
         "map T2/local7 to physical ID27 before stock dense mapping; leave ID26 helper as fallback")
    hook("reverse_sparse_id27_t2_local7", REVERSE_CLASS_HOOK_VA,
         _rel32(REVERSE_CLASS_HOOK_VA, entrypoints["reverse_class_map_multi_addon"]),
         "map physical ID27 back to T2/local7; leave H.2 ID26 and stock paths intact")
    hook("unlock_id27_oracle_id10", UNLOCK_CALL_VA,
         _call_rel32(UNLOCK_CALL_VA, entrypoints["multi_addon_unlock"]),
         "evaluate ID27 with native physical-ID10/T2CupCar1 gate; preserve physical ID27")
    hook("locked_reason_id27_oracle_id10", LOCKED_REASON_HOOK_VA,
         _rel32(LOCKED_REASON_HOOK_VA, entrypoints["locked_reason_id27_bridge"]),
         "route only physical ID27 through the native ID10 group-6 selector path")
    hook("audio_profile_lookup_multi_addon", AUDIO_PROFILE_CALL_VA,
         _call_rel32(AUDIO_PROFILE_CALL_VA, entrypoints["multi_addon_audio_profile"]),
         "preserve physical IDs; map ID26 to profile0 and ID27 to tuned stock profile7")

    display_hooks: list[tuple[str, int, str, str]] = [
        ("vehicle_select_manufacturer_id27", 0x00481A0E, "vehicle_select_manufacturer_id27", "group0x33 NISSAN-compatible slot label"),
        ("vehicle_select_model_id27", 0x00481A4B, "vehicle_select_model_id27", "group0x34 T2 donor slot label"),
    ]
    for index, call_va in enumerate(registry.QUICKRACE_LOCALIZATION_CALLS):
        display_hooks.append((f"quickrace_name_id27_{index}", call_va,
                              f"quickrace_name_id27_{index}", "group0x35 combined ID27 display"))
    for _call_va, _group, label, _string, _resume in registry.RACE_OPTIONS_LOCALIZATION_CALLS:
        display_hooks.append((f"{label}_id27", _call_va,
                              f"{label}_id27", "Race Options ID27 split manufacturer/model display"))
    for hook_va, _slot, label, _group_va, _call_va, _resume in registry.RACE_DETAILS_LOCALIZATION_CALLS:
        display_hooks.append((f"race_details_name_id27_{label}", hook_va,
                              f"race_details_name_lookup_{label}_id27", "Race Details ID27 display"))
    display_hooks.append(("vehicle_setup_name_id27", 0x0044FA29,
                          "vehicle_setup_name_lookup_id27", "Vehicle Setup ID27 combined display"))
    for name, va, entry_name, purpose in display_hooks:
        hook(name, va, _rel32(va, entrypoints[entry_name]), purpose)

    hook("results_name_id27_fixed_diagnostic", natural.RESULTS_NAME_HOOK_VA,
         _rel32(natural.RESULTS_NAME_HOOK_VA, entrypoints["results_name_id27_bridge"]),
         "display a fixed I.0-only ID27 label; preserve native DriverID and ID26 Strugo behavior")

    capacity_original = parent[registry.va_to_file_offset(pe, CAPACITY_T2_IMMEDIATE_VA, 1)]
    if capacity_original != 7:
        raise CandidateError("H.2 T2 capacity immediate is not the audited value 7")
    _add_va_operation(parent, pe, operations, name="frontend_t2_capacity_8",
                      category="frontend-capacity", va=CAPACITY_T2_IMMEDIATE_VA,
                      replacement=b"\x08", expected=b"\x07",
                      purpose="set T2 capacity to eight independently; preserve T1=8 and T3=12")

    pool_hooks = (
        ("quickrace_t2_pool_exit_id27", QUICKRACE_T2_HOOK_VA,
         QUICKRACE_T2_REENTRY_VA, QUICKRACE_T2_EXIT_VA),
        ("rallyecup_t2_pool_exit_id27", CUP_T2_HOOK_VA,
         CUP_T2_REENTRY_VA, CUP_T2_EXIT_VA),
        ("masterrallye_t2_pool_exit_id27", MASTER_T2_HOOK_VA,
         MASTER_T2_REENTRY_VA, MASTER_T2_EXIT_VA),
    )
    stub_entry_by_hook = {
        "quickrace_t2_pool_exit_id27": "quickrace_t2_id27_append",
        "rallyecup_t2_pool_exit_id27": "rallyecup_t2_id27_append",
        "masterrallye_t2_pool_exit_id27": "masterrallye_t2_id27_append",
    }
    for name, va, reentry, exit_va in pool_hooks:
        _ = reentry, exit_va
        stub_entry = entrypoints[stub_entry_by_hook[name]]
        hook(name, va, _rel32(va, stub_entry),
             "append sparse physical ID27 through the native T2 exclusion/append body exactly once")

    operations.sort(key=lambda item: item["file_offset"])
    candidate = _apply_layer(parent, operations)
    parent_manifest_bytes = (json.dumps(parent_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R5V-I.0 two-addon-slot / T2 local7 diagnostic candidate",
        "profile": PROFILE,
        "status": "READY_FOR_HUMAN_RUNTIME",
        "source_sha256": source_hash,
        "source_size": len(data),
        "parent_candidate": {
            "phase": "R5V-H.2 mode-aware physical-ID26 AI eligibility",
            "sha256": parent_hash,
            "manifest_sha256_utf8": sha256(parent_manifest_bytes),
            "profile": parent_manifest["profile"],
        },
        "patched_sha256": sha256(candidate),
        "file_size": len(candidate),
        "layout": layout,
        "profiles": [
            {
                "physical_id": 26, "class": 0, "local_index": 7,
                "name": "Mercedes", "runtime_family": "Mercedes",
                "model_family": "Mercedes", "wheel_family": "Mercedes",
                "physics_family": "Vehicles/Mercedes", "stats": [4, 3, 6, 5],
                "smallcarsheet_index": 9, "race_colour_rgba_bits": ["3f800000", "00000000", "00000000", "3f800000"],
                "unlock_oracle_id": 3, "audio_profile_id": 0,
                "ai_pools": ["quickrace:T1", "rallye_cup:new-roster:T1", "master_rallye:new-roster:T1"],
                "results_display": "JEAN-PIERRE STRUGO",
                "native_driver_id_changed": False,
            },
            {
                "physical_id": 27, "class": 1, "local_index": 7,
                "profile_role": "SLOT PROOF / DONOR; NOT A REAL SECOND ADDON",
                "name": "Navara", "donor_physical_id": 7,
                "runtime_family": "Navara", "model_family": "Navara",
                "wheel_family": "Navara", "physics_family": "Vehicles/Navara",
                "stats": [7, 6, 6, 5], "smallcarsheet_index": 13,
                "vehicle_select_frame": 23,
                "race_colour_rgba_bits": ["00000000", "3f800000", "3f800000", "3f800000"],
                "display": {"manufacturer": DISPLAY_ID27_MANUFACTURER,
                            "model": DISPLAY_ID27_MODEL,
                            "combined": DISPLAY_ID27_COMBINED,
                            "results": RESULTS_ID27},
                "unlock_oracle_id": 10,
                "unlock_path": "Progress/UnlockedCars/T2CupCar1",
                "audio_profile_id": 7,
                "ai_pools": ["quickrace:T2", "rallye_cup:new-roster:T2", "master_rallye:new-roster:T2"],
                "native_driver_id_changed": False,
                "donor_frontend_art": True,
                "id7_record_overwritten": False,
            },
        ],
        "class_mapping": {
            "T1_local0_to6": list(range(7)), "T1_local7": 26,
            "T2_local0_to6": list(range(7, 14)), "T2_local7": 27,
            "T3_local0_to11": list(range(14, 26)),
            "T2_local7_never_maps_to_ID14": True,
            "stock_reverse_mappings_unchanged": True,
        },
        "capacity": {"T1": 8, "T2": 8, "T3": 12},
        "registry_arrays": {
            "vehicle_record_stride": RECORD_STRIDE,
            "secondary_racetest_displacement_from_retail": 0x68,
            "secondary_initializer_lea_count": len(registry.SECONDARY_INIT_LEAS),
            "secondary_consumer_count": len(registry.SECONDARY_CONSUMER_DISPS),
            "racetest_array_count": RACETEST_COUNT,
            "physical_allocation_changed_other_than_vehicle_registry_and_adjacent_racetest": False,
        },
        "unlock": {
            "id26_oracle_id": 3, "id26_path": "Progress/UnlockedCars/T1CupCar1",
            "id27_oracle_id": 10, "id27_path": "Progress/UnlockedCars/T2CupCar1",
            "t2_class_reachability_independent": True,
            "native_gate_va": "0x0045A150", "vehicle_select_call_va": "0x004819CE",
            "id27_group6_requirement_selector": 12,
        },
        "audio": {
            "physical_id26_profile": 0, "physical_id27_profile": 7,
            "id27_profile_record": "tuned-07 / Navara donor",
            "physical_car_id_rewritten": False,
            "stock_ids_0_to25_native": True,
        },
        "ai_pools": {
            "quickrace_t1": list(T1_PHYSICAL_IDS),
            "quickrace_t2": list(T2_PHYSICAL_IDS),
            "rallye_cup_t2_new_roster_only": list(T2_PHYSICAL_IDS),
            "master_rallye_t2_new_competition_only": list(T2_PHYSICAL_IDS),
            "invitation_id27": "NOT_APPLICABLE; normal tested mode uses T3 ordinary IDs14..20",
            "challenge": "authored roster unchanged",
            "id27_forced_participant": False,
            "native_exclusion_shuffle_driver_and_publication": "preserved through original T2 loop body",
            "existing_competition_rosters_mutated": False,
        },
        "runtime_architecture": {
            "randomizer_present": False,
            "participant_count_changed": False,
            "save_load_or_stage_reuse_changed": False,
            "physical_car_id_aliasing": False,
            "id25_trooper_id26_mercedes_preserved": True,
        },
        "text_virtual_size": {
            "h2": current_vsize,
            "i0": new_vsize,
            "code_cave_va": f"0x{CODE_CAVE_VA:08X}",
            "payload_size": len(payload),
            "payload_end_exclusive_va": f"0x{highest_end_va:08X}",
            "rdata_va": f"0x{registry.IMAGE_BASE + rdata['rva']:08X}",
            "zero_fill_verified_in_h2": True,
            "non_overlap_proven": True,
        },
        "code_entrypoints": {key: f"0x{value:08X}" for key, value in entrypoints.items()},
        "operations": operations,
        "operation_counts_by_category": dict(sorted(Counter(op["category"] for op in operations).items())),
        "inverse": {
            "i0_layer_restores_exact_h2_bytes": True,
            "h2_parent_is_reproducibly_built_from_exact_retail": True,
            "source_exe_modified": False,
        },
        "higher_phase_boundary": {
            "i0_slot_architecture": "STATIC_PASS / READY_FOR_HUMAN_RUNTIME",
            "i1_real_t2_payload": "REAL_T2_PAYLOAD_REQUIRED",
            "r5v_i_full_pass": False,
        },
    }
    _verify_structure(candidate, manifest)
    return candidate, manifest


def _verify_structure(candidate: bytes, manifest: dict[str, Any]) -> None:
    if sha256(candidate) != manifest.get("patched_sha256"):
        raise CandidateError("candidate SHA256 differs from manifest")
    if len(candidate) != RETAIL_SIZE or manifest.get("file_size") != RETAIL_SIZE:
        raise CandidateError("I.0 candidate must retain the exact retail file size")
    if manifest.get("profile") != PROFILE or manifest.get("layout", {}).get("record_count") != 28:
        raise CandidateError("candidate profile or 28-record target is invalid")
    if manifest.get("capacity") != {"T1": 8, "T2": 8, "T3": 12}:
        raise CandidateError("candidate class capacities differ from the I.0 target")
    if manifest.get("class_mapping", {}).get("T2_local7") != 27:
        raise CandidateError("T2 local7 must map to physical ID27")
    if class_local_to_physical(1, 7) == 14:
        raise CandidateError("T2/local7 has dense T3 contamination")
    if manifest.get("runtime_architecture", {}).get("randomizer_present") is not False:
        raise CandidateError("I.0 candidate may not contain the old/general randomizer")
    if manifest.get("runtime_architecture", {}).get("participant_count_changed") is not False:
        raise CandidateError("I.0 candidate may not change participant count")
    expected_layout = registry_layout(27)
    if manifest.get("layout") != expected_layout:
        raise CandidateError("manifest registry layout does not match the derived 28-record formula")
    entrypoints = {key: int(value, 16) for key, value in manifest.get("code_entrypoints", {}).items()}
    cave_va = int(manifest["text_virtual_size"]["code_cave_va"], 16)
    payload_op = next((op for op in manifest["operations"]
                       if op["name"] == "i0_multi_addon_code_payload"), None)
    if payload_op is None or payload_op.get("virtual_address") != cave_va:
        raise CandidateError("candidate manifest is missing the audited I.0 code-cave operation")
    payload = bytes.fromhex(payload_op["replacement_bytes"])
    if not payload or len(payload) > CODE_CAVE_SIZE:
        raise CandidateError("candidate code payload is empty or exceeds the audited cave")
    cave_end_va = cave_va + len(payload)
    rdata_va = int(manifest["text_virtual_size"]["rdata_va"], 16)
    text_vsize_i0 = manifest["text_virtual_size"].get("i0")
    text_end_va = TEXT_BASE_VA + text_vsize_i0
    if cave_end_va > rdata_va or text_end_va < cave_end_va:
        raise CandidateError("candidate code payload is not fully mapped before .rdata")
    if payload_op["file_offset"] < 0 or candidate[
            payload_op["file_offset"]:payload_op["file_offset"] + len(payload)] != payload:
        raise CandidateError("candidate does not carry the manifested code cave")
    for name, address in entrypoints.items():
        if not cave_va <= address < cave_end_va:
            raise CandidateError(f"code entrypoint {name} falls outside the I.0 payload")
    for operation in manifest["operations"]:
        start = operation["file_offset"]
        original = bytes.fromhex(operation["original_bytes"])
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if len(original) != len(replacement) or start < 0 or start + len(replacement) > len(candidate):
            raise CandidateError(f"candidate operation has invalid bounds or size: {operation['name']}")
        if candidate[start:start + len(replacement)] != replacement:
            raise CandidateError(f"candidate patch bytes differ at {operation['name']}")
    inverse = bytearray(candidate)
    for operation in reversed(manifest["operations"]):
        start = operation["file_offset"]
        original = bytes.fromhex(operation["original_bytes"])
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if inverse[start:start + len(replacement)] != replacement:
            raise CandidateError(f"candidate inverse range differs at {operation['name']}")
        inverse[start:start + len(original)] = original
    if sha256(bytes(inverse)) != manifest.get("parent_candidate", {}).get("sha256"):
        raise CandidateError("I.0 inverse does not restore the pinned H.2 parent")
    for key in ("quickrace_t2_id27_append", "rallyecup_t2_id27_append", "masterrallye_t2_id27_append"):
        if key not in entrypoints:
            raise CandidateError(f"candidate is missing the T2 append entrypoint {key}")
    if manifest.get("profiles", [])[0].get("physical_id") != 26 or manifest.get("profiles", [])[1].get("physical_id") != 27:
        raise CandidateError("ID26/ID27 profile order or identity changed")
    if manifest["profiles"][0].get("name") != "Mercedes" or manifest["profiles"][1].get("name") != "Navara":
        raise CandidateError("I.0 must preserve Mercedes and use a clearly labeled Navara donor")


def verify_existing(source: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if source == output or os.path.samefile(source, output):
        raise CandidateError("candidate must not overwrite the pristine executable")
    expected_bytes, expected_manifest = make_candidate(source.read_bytes())
    if output.read_bytes() != expected_bytes:
        raise CandidateError("existing I.0 candidate differs from deterministic retail rebuild")
    expected_manifest_bytes = (json.dumps(expected_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if manifest_path.read_bytes() != expected_manifest_bytes:
        raise CandidateError("existing I.0 patch manifest differs from deterministic rebuild")
    _verify_structure(expected_bytes, expected_manifest)
    return expected_manifest


def write_candidate(source: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    if source == output or output.exists() or manifest_path.exists():
        raise CandidateError("refusing to overwrite source, candidate, or manifest")
    if not registry._is_research_output(output) or not registry._is_research_output(manifest_path):
        raise CandidateError("candidate and manifest must be under ignored research-output")
    before = sha256(source.read_bytes())
    candidate, manifest = make_candidate(source.read_bytes())
    if before != manifest["source_sha256"]:
        raise CandidateError("retail source changed during I.0 build")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    # Keep the signed/hashed research manifest byte-stable across platforms.
    # Path.write_text() translates LF to CRLF on Windows unless newline is set.
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if sha256(output.read_bytes()) != manifest["patched_sha256"]:
        raise CandidateError("written candidate failed its output SHA256 check")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("source", type=Path, help="exact pristine retail MRallye.exe")
    build.add_argument("output", type=Path, help="new candidate path under research-output")
    build.add_argument("--manifest", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("source", type=Path)
    verify.add_argument("candidate", type=Path)
    verify.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    manifest_path = args.manifest or (args.output if args.command == "build" else args.candidate).with_suffix(".manifest.json")
    try:
        if args.command == "build":
            manifest = write_candidate(args.source, args.output, manifest_path)
        else:
            manifest = verify_existing(args.source, args.candidate, manifest_path)
    except (CandidateError, h2.CandidateError, audio.CandidateError,
            natural.CandidateError, registry.PatchError, OSError, ValueError,
            struct.error, KeyError, TypeError) as exc:
        parser.exit(2, f"R5V-I.0 candidate refused: {exc}\n")
    print(json.dumps({
        "status": "VERIFIED" if args.command == "verify" else manifest["status"],
        "profile": manifest["profile"],
        "source_sha256": manifest["source_sha256"],
        "h2_sha256": manifest["parent_candidate"]["sha256"],
        "candidate_sha256": manifest["patched_sha256"],
        "size": manifest["file_size"],
        "id27": manifest["profiles"][1],
        "output": str(args.candidate if args.command == "verify" else args.output),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
