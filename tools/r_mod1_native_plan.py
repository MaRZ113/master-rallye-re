#!/usr/bin/env python3
"""Generate the exact-retail R-MOD1 in-memory native operation plan.

The plan contains stock-image preimages and a fixed, non-overlapping remote
code/data layout. It never writes a patched executable. Runtime installation
is performed only by the separately built suspended-process launcher.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

import r_ai1_2_randomizer as randomizer
import r_ui1_opponents as opponents_ui
from patch_vehicle_slot25 import parse_pe, va_to_file_offset
from r_ai1_mixed_class import RETAIL_SHA256, RETAIL_SIZE


CODE_BASE = 0x70000000
CODE_ALLOCATION_SIZE = 0x10000
DATA_BASE = CODE_BASE + CODE_ALLOCATION_SIZE
DATA_ALLOCATION_SIZE = 0x10000

CHOICE_GATE = CODE_BASE + 0x0100
LIMIT_GATE = CODE_BASE + 0x0120
SELECTOR_BASE = CODE_BASE + 0x1000
UI_LIST_BASE = CODE_BASE + 0x1500
START_GATE_BASE = CODE_BASE + 0x1700
BOOTSTRAP_BASE = CODE_BASE + 0x1900
MASTER_SELECTOR_BASE = CODE_BASE + 0x2000
CUP_SELECTOR_BASE = CODE_BASE + 0x2400
CHALLENGE_GATE = CODE_BASE + 0x0140
CHALLENGE_PREVIEW_BASE = CODE_BASE + 0x2800
CHALLENGE_RESET_ENTRY_BASE = CODE_BASE + 0x2A00
CHALLENGE_RESET_BACK_BASE = CODE_BASE + 0x2A40
CHALLENGE_CONSUMER_BASE = CODE_BASE + 0x2A80
PLAYER_ENTRY_GATE_BASE = CODE_BASE + 0x2C00
PLAYER_SETUP_GATE_BASE = CODE_BASE + 0x2C40

SLOT_MODULE = DATA_BASE + 0x0000
SLOT_CONFIGURE = DATA_BASE + 0x0004
SLOT_CHOOSE_CLASS = DATA_BASE + 0x0008
SLOT_OPPONENT_LIMIT = DATA_BASE + 0x000C
SLOT_CAN_START = DATA_BASE + 0x0010
SLOT_LOAD_LIBRARY_W = DATA_BASE + 0x0018
SLOT_START_PHASE = DATA_BASE + 0x001C
SLOT_CHALLENGE = DATA_BASE + 0x0020
SLOT_PLAYER_CAR = DATA_BASE + 0x0024
SLOT_REGISTRY_POOL = DATA_BASE + 0x0028
CONFIG_BLOB = DATA_BASE + 0x0100
DLL_PATH = DATA_BASE + 0x1200
KERNEL32_NAME = DATA_BASE + 0x2200
EXPORT_LOAD_LIBRARY_W = DATA_BASE + 0x2210
EXPORT_CONFIGURE = DATA_BASE + 0x2230
EXPORT_CHOOSE_CLASS = DATA_BASE + 0x2250
EXPORT_OPPONENT_LIMIT = DATA_BASE + 0x2270
EXPORT_CAN_START = DATA_BASE + 0x2290
EXPORT_START_PHASE = DATA_BASE + 0x22D0
EXPORT_CHALLENGE = DATA_BASE + 0x22F0
EXPORT_PLAYER_CAR = DATA_BASE + 0x2310
EXPORT_REGISTRY_POOL = DATA_BASE + 0x2330

IAT_VA = {
    "LoadLibraryA": 0x0068F0B8,
    "GetProcAddress": 0x0068F0C0,
    "ExitProcess": 0x0068F114,
}
START_CALL_SITE = 0x0047AD0C
START_CONTINUATION = 0x0047AD11
QUICK_RACE_SETUP = 0x0047B780
OEP = 0x005C4602
OEP_REPLAY = bytes.fromhex("55 8B EC 6A FF")
START_CALL_ORIGINAL = bytes.fromhex("E8 6F 0A 00 00")
UI_LIST_HOOK = opponents_ui.HOOK
UI_LIST_CONTINUE = opponents_ui.CONTINUE
UI_LIST_ORIGINAL = opponents_ui.ORIGINAL
UI_ARROW_SITE = 0x0047A32C
UI_ARROW_ORIGINAL = bytes.fromhex("83 FD 02")

FEATURE_BOOTSTRAP = 4
FEATURE_RANDOMIZER = 1
FEATURE_OPPONENTS = 2


class NativePlanError(ValueError):
    pass


class CodeBuilder(randomizer.Asm):
    """Small rel32 assembler shared with the historical, audited selector."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel32(site_va: int, target_va: int, opcode: int) -> bytes:
    delta = target_va - site_va - 5
    if not -(1 << 31) <= delta < (1 << 31):
        raise NativePlanError(f"relative branch is out of range: {site_va:#x}->{target_va:#x}")
    return bytes((opcode,)) + struct.pack("<i", delta)


def jump(site_va: int, target_va: int, length: int) -> bytes:
    if length < 5:
        raise NativePlanError("native hook is shorter than a near jump")
    return rel32(site_va, target_va, 0xE9) + bytes([0x90]) * (length - 5)


def emit_call_abs_cell(a: CodeBuilder, cell_va: int) -> None:
    a.emit(b"\xff\x15" + struct.pack("<I", cell_va))


def call_gate(gate_va: int, cell_va: int) -> bytes:
    return b"\xff\x15" + struct.pack("<I", cell_va) + b"\xc3"


def stdcall_tail_gate(cell_va: int) -> bytes:
    """Forward a call frame unchanged to a stdcall export via an indirect JMP."""
    return b"\xff\x25" + struct.pack("<I", cell_va)


def make_player_car_gate(base_va: int, phase: int) -> bytes:
    """Replay the native QuickRace/Car0 getter, then consult the cached G2 identity.

    The callsite owns one stack argument and expects a stdcall RET 4. The native
    getter's own RET 4 consumes only the duplicate argument pushed here; the
    runtime callback is stdcall with (current_id, phase) and RET 8.
    """
    if phase not in (0, 1):
        raise NativePlanError("player-car gate phase must be entry=0 or setup=1")
    code = bytearray(b"\xff\x74\x24\x04")  # PUSH [ESP+4], duplicate the callsite's slot arg
    code += rel32(base_va + len(code), 0x004ADFB0, 0xE8)  # original getter, RET 4
    code += bytes((0x6A, phase, 0x50))                    # PUSH phase; PUSH current CarID
    code += b"\xff\x15" + struct.pack("<I", SLOT_PLAYER_CAR) # stdcall callback, RET 8
    code += b"\xc2\x04\x00"                            # match the original getter's RET 4
    return bytes(code)


def make_ui_list_code() -> bytes:
    a = CodeBuilder(UI_LIST_BASE)
    # Preserve native flags/registers. Keep the configured upper bound at
    # [ESP] and reserve a distinct enString object at [ESP+4]. The native
    # enString constructor is thiscall/RET 4: its stack argument is consumed
    # by the callee, so both local addresses remain stable after construction.
    a.emit("9c6083ec088bf3")
    a.call(LIMIT_GATE)
    a.emit("890424bf03000000")
    a.label("loop")
    a.emit("3b3c24")
    a.branch("0f83", "done")  # unsigned EDI >= MROpponentLimitV1()
    a.call(0x00485CF0)
    a.emit("576a408bc88b10ff520c")
    a.emit("508d4c2408")
    a.call(0x004D11D0)
    a.emit("8d442404506a01ff76088bce")
    a.call(0x00407B30)
    a.emit("ff742404")
    a.call(0x005B4C00)
    a.emit("83c40447")
    a.branch("e9", "loop")
    a.label("done")
    a.emit("83c408619d")
    a.emit(UI_LIST_ORIGINAL)
    a.branch("e9", UI_LIST_CONTINUE)
    return a.finish()[0]


def make_start_gate_code() -> bytes:
    a = CodeBuilder(START_GATE_BASE)
    a.emit("9c60")
    emit_call_abs_cell(a, SLOT_CAN_START)
    a.emit("85c0")
    a.branch("0f84", "blocked")
    a.emit("619d")
    # The callback only records a phase when diagnostics are enabled. Preserve
    # the exact caller state around it so native setup receives the original
    # ECX/flags and its stack shape remains the stock call-site shape.
    a.emit("9c606a04")
    emit_call_abs_cell(a, SLOT_START_PHASE)
    a.emit("619d")
    # Preserve the original native setup call and its caller state. Race
    # Broker values are not an authoritative roster oracle until the game has
    # entered the race-scene initialization path.
    a.call(QUICK_RACE_SETUP)
    a.emit("9c606a05")
    emit_call_abs_cell(a, SLOT_START_PHASE)
    a.emit("619d")
    a.branch("e9", START_CONTINUATION)
    a.label("blocked")
    a.emit("619d")
    a.emit("5e83c430c20400")  # parent epilogue: POP ESI; ADD ESP,30; RET 4
    return a.finish()[0]


def make_oep_bootstrap(checkpoint: str = "v13",registry_pool=False) -> bytes:
    a = CodeBuilder(BOOTSTRAP_BASE)
    a.emit("9c60")  # Preserve retail entry registers/flags until OEP replay.
    # Resolve LoadLibraryW using the already-resolved retail imports. The
    # launcher writes a UTF-16 path, so a Unicode install directory is safe.
    a.emit(b"\x68" + struct.pack("<I", KERNEL32_NAME))
    emit_call_abs_cell(a, IAT_VA["LoadLibraryA"])
    a.emit("85c0")
    a.branch("0f84", "fail")
    a.emit(b"\xa3" + struct.pack("<I", SLOT_MODULE))
    a.emit(b"\x68" + struct.pack("<I", EXPORT_LOAD_LIBRARY_W))
    a.emit(b"\xff\x35" + struct.pack("<I", SLOT_MODULE))
    emit_call_abs_cell(a, IAT_VA["GetProcAddress"])
    a.emit("85c0")
    a.branch("0f84", "fail")
    a.emit(b"\xa3" + struct.pack("<I", SLOT_LOAD_LIBRARY_W))
    a.emit(b"\x68" + struct.pack("<I", DLL_PATH))
    emit_call_abs_cell(a, SLOT_LOAD_LIBRARY_W)
    a.emit("85c0")
    a.branch("0f84", "fail")
    a.emit(b"\xa3" + struct.pack("<I", SLOT_MODULE))

    exports = [
        (EXPORT_CONFIGURE, SLOT_CONFIGURE, "MRConfigureBlobV1"),
        (EXPORT_CHOOSE_CLASS, SLOT_CHOOSE_CLASS, "MRChooseClassV1"),
        (EXPORT_OPPONENT_LIMIT, SLOT_OPPONENT_LIMIT, "MROpponentLimitV1"),
        (EXPORT_CAN_START, SLOT_CAN_START, "MRCanStartQuickRaceV1"),
        (EXPORT_START_PHASE, SLOT_START_PHASE, "MRSetStartPhaseV1"),
    ]
    if checkpoint in {"f3", "g1", "g2"}:
        exports.append((EXPORT_CHALLENGE, SLOT_CHALLENGE, "MRChallengeV1"))
    if checkpoint == "g2":
        exports.append((EXPORT_PLAYER_CAR, SLOT_PLAYER_CAR, "MRQuickRacePlayerCarV1"))
    if registry_pool:exports.append((EXPORT_REGISTRY_POOL,SLOT_REGISTRY_POOL,'MRFilterAiPoolV1'))
    for name_va, function_slot, _name in exports:
        a.emit(b"\x68" + struct.pack("<I", name_va))
        a.emit(b"\xff\x35" + struct.pack("<I", SLOT_MODULE))
        emit_call_abs_cell(a, IAT_VA["GetProcAddress"])
        a.emit("85c0")
        a.branch("0f84", "fail")
        a.emit(b"\xa3" + struct.pack("<I", function_slot))

    a.emit(b"\x68" + struct.pack("<I", CONFIG_BLOB))
    emit_call_abs_cell(a, SLOT_CONFIGURE)
    a.emit("85c0")
    a.branch("0f84", "fail")
    a.emit("619d")
    a.emit(OEP_REPLAY)
    a.branch("e9", OEP + len(OEP_REPLAY))
    a.label("fail")
    a.emit("619d")
    a.emit(b"\x68\x11\xe0\x00\x00")
    emit_call_abs_cell(a, IAT_VA["ExitProcess"])
    a.emit("0f0b")  # fail-closed trap if ExitProcess unexpectedly returns
    return a.finish()[0]


def make_rmod1_selector(spec: dict[str, Any]) -> tuple[bytes, dict[str, int]]:
    """Reuse the historical policy assembler without changing its source."""
    original_loader = randomizer.LOADER
    try:
        randomizer.LOADER = CHOICE_GATE
        blob,labels=randomizer.selection_code(spec)
        if spec.get('registry_pool',False):
            # Only an active policy rebuild (-1/-2 marker) is filtered. Native
            # Stock pass-through never calls the provider. Preserve every
            # register/flag and the existing participant-exclusion machinery.
            a=CodeBuilder(spec['base']+len(blob));a.emit('9c')
            a.emit(bytes((0x83,0x7c,0x24,spec['marker']+4,0xff)));a.branch('0f84','filter')
            a.emit(bytes((0x83,0x7c,0x24,spec['marker']+4,0xfe)));a.branch('0f85','done')
            a.label('filter');a.emit('60')
            a.emit(bytes((0x8d,0x44,0x24,spec['primary']+36))+b'\x50')
            a.emit(b'\xff\xb4\x24'+struct.pack('<I',spec['cls']+40))
            a.emit(bytes((0x6a,spec['hint'])))
            a.emit(b'\xff\x15'+struct.pack('<I',SLOT_REGISTRY_POOL));a.emit('61')
            a.label('done');a.emit('9d');a.branch('e9',labels['pool_end'])
            wrapper=a.finish()[0];labels['unfiltered_pool_end']=labels['pool_end'];labels['pool_end']=spec['base']+len(blob)
            blob+=wrapper
        return blob,labels
    finally:
        randomizer.LOADER = original_loader


def make_challenge_preview_code() -> bytes:
    a = CodeBuilder(CHALLENGE_PREVIEW_BASE)
    # Replay the authored absolute CarID load before saving the native frame.
    # The selected ID replaces only saved EDI, which is consumed by both the
    # native localized-name and preview-model publications at 45ECBE..45ED41.
    a.emit("8bbc38740500009c60")
    a.emit("57538b461083c064506a01")  # authored opponent, human, event+100, hint=1
    a.call(CHALLENGE_GATE)
    a.emit("83f818")
    a.branch("0f87", "stock")  # invalid/-1 preserves the authored EDI
    a.emit("89442400")           # saved EDI in PUSHAD frame = absolute physical CarID
    a.label("stock")
    a.emit("619d")
    a.branch("e9", 0x0045EC3C)
    return a.finish()[0]


def make_challenge_reset_code(base: int, continuation: int) -> bytes:
    a = CodeBuilder(base)
    a.emit("9c60")
    a.emit("6a006a00")
    a.emit(b"\x68" + struct.pack("<I", 0xFFFFFF9C))  # first=-100 invalidates cache
    a.emit("6a01")
    a.call(CHALLENGE_GATE)
    a.emit("619d")
    a.branch("e9", continuation)
    return a.finish()[0]


def make_challenge_consumer_code() -> bytes:
    a = CodeBuilder(CHALLENGE_CONSUMER_BASE)
    # The native authored CarID load always runs, then the same prepared ID
    # consumed by the preview replaces only the saved EDI value.
    a.emit("8bbc38740500009c60")
    a.emit("6a016a016a016a01")
    a.call(CHALLENGE_GATE)
    a.emit("83f818")
    a.branch("0f87", "stock")
    a.emit("89442400")
    a.label("stock")
    a.emit("619d")
    a.branch("e9", 0x00450115)
    return a.finish()[0]


def _generic_pe_rva_to_offset(binary: bytes, rva: int, size: int = 1) -> int:
    pe_offset = struct.unpack_from("<I", binary, 0x3C)[0]
    if binary[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise NativePlanError("runtime bridge DLL has an invalid PE signature")
    machine, section_count = struct.unpack_from("<HH", binary, pe_offset + 4)
    optional_size = struct.unpack_from("<H", binary, pe_offset + 20)[0]
    optional = pe_offset + 24
    if machine != 0x014C or struct.unpack_from("<H", binary, optional)[0] != 0x10B:
        raise NativePlanError("runtime bridge DLL must be PE32/I386")
    table = optional + optional_size
    for index in range(section_count):
        at = table + index * 40
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from("<IIII", binary, at + 8)
        if virtual_address <= rva and rva + size <= virtual_address + raw_size:
            offset = raw_offset + rva - virtual_address
            if offset + size <= len(binary):
                return offset
    raise NativePlanError(f"runtime bridge RVA is not file-backed: {rva:#x}")


def _module_exports(binary: bytes) -> set[str]:
    """Read the PE32 export-name table and require the exact bridge ABI."""
    # Parse the bridge DLL independently because the retail-only repository PE
    # helper intentionally enforces the game's four-section image shape.
    pe_offset = struct.unpack_from("<I", binary, 0x3C)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", binary, optional)[0] != 0x10B:
        raise NativePlanError("runtime bridge DLL is not PE32")
    export_rva, export_size = struct.unpack_from("<II", binary, optional + 96)
    if not export_rva or not export_size:
        raise NativePlanError("runtime bridge DLL has no export directory")
    export_offset = _generic_pe_rva_to_offset(binary, export_rva, 40)
    name_count = struct.unpack_from("<I", binary, export_offset + 24)[0]
    names_rva = struct.unpack_from("<I", binary, export_offset + 32)[0]
    names_offset = _generic_pe_rva_to_offset(binary, names_rva, name_count * 4)
    names: set[str] = set()
    for index in range(name_count):
        name_rva = struct.unpack_from("<I", binary, names_offset + index * 4)[0]
        name_offset = _generic_pe_rva_to_offset(binary, name_rva, 1)
        end = binary.find(b"\0", name_offset)
        if end < 0:
            raise NativePlanError("unterminated runtime export name")
        names.add(binary[name_offset:end].decode("ascii", "strict"))
    return names


def _verify_import_table(source: bytes) -> dict[str, int]:
    pe = parse_pe(source)
    pe_offset = struct.unpack_from("<I", source, 0x3C)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", source, optional)[0] != 0x10B:
        raise NativePlanError("retail image is not PE32")
    import_rva, import_size = struct.unpack_from("<II", source, optional + 96 + 8)
    if not import_rva or not import_size:
        raise NativePlanError("retail image has no normal import table")
    import_offset = va_to_file_offset(pe, import_rva + 0x400000, import_size)
    found: dict[str, int] = {}
    cursor = import_offset
    while cursor + 20 <= import_offset + import_size:
        original_thunk, _timestamp, _forwarder, name_rva, iat_rva = struct.unpack_from("<IIIII", source, cursor)
        if not any((original_thunk, name_rva, iat_rva)):
            break
        module_offset = va_to_file_offset(pe, name_rva + 0x400000, 1)
        module_end = source.find(b"\0", module_offset)
        module = source[module_offset:module_end].decode("ascii", "strict").casefold()
        thunk_rva = original_thunk or iat_rva
        index = 0
        while True:
            thunk_offset = va_to_file_offset(pe, thunk_rva + index * 4 + 0x400000, 4)
            thunk = struct.unpack_from("<I", source, thunk_offset)[0]
            if not thunk:
                break
            if thunk & 0x80000000:
                name = f"ordinal:{thunk & 0xFFFF}"
            else:
                hint_name_offset = va_to_file_offset(pe, thunk + 0x400000, 3)
                end = source.find(b"\0", hint_name_offset + 2)
                name = source[hint_name_offset + 2:end].decode("ascii", "strict")
            if module == "kernel32.dll" and name in IAT_VA:
                found[name] = 0x400000 + iat_rva + index * 4
            index += 1
        cursor += 20
    if found != IAT_VA:
        raise NativePlanError(f"retail Kernel32 import locations changed: {found!r}")
    return found


def _patch_op(source: bytes, pe: Any, operation_id: str, owner: str,
              feature: int, va: int, expected: bytes, replacement: bytes,
              purpose: str) -> dict[str, Any]:
    if not expected or len(expected) != len(replacement):
        raise NativePlanError(f"invalid operation length for {operation_id}")
    file_offset = va_to_file_offset(pe, va, len(expected))
    actual = source[file_offset:file_offset + len(expected)]
    if actual != expected:
        raise NativePlanError(f"retail preimage mismatch for {operation_id} at {va:#x}")
    return {
        "id": operation_id,
        "owner": owner,
        "feature_mask": feature,
        "va": va,
        "rva": va - 0x400000,
        "file_offset": file_offset,
        "expected_original_hex": expected.hex(),
        "replacement_hex": replacement.hex(),
        "purpose": purpose,
    }


def build_plan(source: bytes, runtime_dll: bytes, checkpoint: str = "v13") -> dict[str, Any]:
    if checkpoint not in {"v13", "f1", "f2", "f3", "g1", "g2"}:
        raise NativePlanError("unknown R-MOD native-plan checkpoint")
    has_challenge = checkpoint in {"f3", "g1", "g2"}
    has_mode_owners = checkpoint in {"f2", "f3", "g1", "g2"}
    is_g1 = checkpoint in {"g1", "g2"}
    is_g2 = checkpoint == "g2"
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise NativePlanError("require the exact pristine supported retail executable")
    pe = parse_pe(source)
    if _verify_import_table(source) != IAT_VA:
        raise NativePlanError("retail bootstrap import map mismatch")
    exports = _module_exports(runtime_dll)
    registry_pool=is_g1 and 'MRFilterAiPoolV1' in exports
    required_exports = {
        "MRConfigureBlobV1", "MRChooseClassV1", "MROpponentLimitV1",
        "MRCanStartQuickRaceV1", "MRSetStartPhaseV1",
    }
    if has_challenge:
        required_exports.add("MRChallengeV1")
    if is_g2:
        required_exports.add("MRQuickRacePlayerCarV1")
    if registry_pool:required_exports.add('MRFilterAiPoolV1')
    if not required_exports.issubset(exports):
        raise NativePlanError(f"runtime DLL is missing ABI exports: {sorted(required_exports - exports)}")

    selector_spec = dict(randomizer.SPECS[0])
    selector_spec["base"] = SELECTOR_BASE
    if is_g1:
        selector_spec["duplicate_repeat_fallback"] = True
    # Keep the historical R-AI1.2 source read-only. Its assembler reads the
    # loader target from a module constant, so scope the R-MOD1 call-gate
    # substitution to this deterministic build invocation and restore it even
    # if code generation fails.
    selector_specs = [selector_spec]
    if has_mode_owners:
        for original_spec, base in ((randomizer.SPECS[1], MASTER_SELECTOR_BASE),
                                    (randomizer.SPECS[2], CUP_SELECTOR_BASE)):
            mode_spec = dict(original_spec)
            mode_spec["base"] = base
            selector_specs.append(mode_spec)
    selectors: dict[str, tuple[dict[str, Any], bytes, dict[str, int]]] = {}
    for spec in selector_specs:
        spec['registry_pool']=registry_pool
        code_bytes, labels = make_rmod1_selector(spec)
        if len(code_bytes) > 0x300:
            raise NativePlanError(f"{spec['name']} selector exceeds its assigned remote code interval")
        selectors[spec["name"]] = (spec, code_bytes, labels)

    code = bytearray(CODE_ALLOCATION_SIZE)
    data = bytearray(DATA_ALLOCATION_SIZE)
    choice_gate = stdcall_tail_gate(SLOT_CHOOSE_CLASS)
    limit_gate = call_gate(LIMIT_GATE, SLOT_OPPONENT_LIMIT)
    code_objects = [
        (CHOICE_GATE - CODE_BASE, choice_gate),
        (LIMIT_GATE - CODE_BASE, limit_gate),
        (UI_LIST_BASE - CODE_BASE, make_ui_list_code()),
        (START_GATE_BASE - CODE_BASE, make_start_gate_code()),
        (BOOTSTRAP_BASE - CODE_BASE, make_oep_bootstrap(checkpoint,registry_pool)),
    ]
    if has_challenge:
        code_objects.append((CHALLENGE_GATE - CODE_BASE, stdcall_tail_gate(SLOT_CHALLENGE)))
    for _name, (spec, selector_code, _labels) in selectors.items():
        code_objects.append((spec["base"] - CODE_BASE, selector_code))
    challenge_objects: list[tuple[int, bytes]] = []
    if has_challenge:
        challenge_objects = [
            (CHALLENGE_PREVIEW_BASE - CODE_BASE, make_challenge_preview_code()),
            (CHALLENGE_RESET_ENTRY_BASE - CODE_BASE,
             make_challenge_reset_code(CHALLENGE_RESET_ENTRY_BASE, 0x004E3DD0)),
            (CHALLENGE_RESET_BACK_BASE - CODE_BASE,
             make_challenge_reset_code(CHALLENGE_RESET_BACK_BASE, 0x0045D910)),
            (CHALLENGE_CONSUMER_BASE - CODE_BASE, make_challenge_consumer_code()),
        ]
        code_objects.extend(challenge_objects)
    if is_g2:
        code_objects.extend((
            (PLAYER_ENTRY_GATE_BASE - CODE_BASE, make_player_car_gate(PLAYER_ENTRY_GATE_BASE, 0)),
            (PLAYER_SETUP_GATE_BASE - CODE_BASE, make_player_car_gate(PLAYER_SETUP_GATE_BASE, 1)),
        ))
    for at, blob in code_objects:
        if at < 0 or at + len(blob) > len(code):
            raise NativePlanError("generated remote code exceeds the fixed code allocation")
        code[at:at + len(blob)] = blob
    export_strings = [
        (KERNEL32_NAME - DATA_BASE, b"kernel32.dll\0"),
        (EXPORT_LOAD_LIBRARY_W - DATA_BASE, b"LoadLibraryW\0"),
        (EXPORT_CONFIGURE - DATA_BASE, b"MRConfigureBlobV1\0"),
        (EXPORT_CHOOSE_CLASS - DATA_BASE, b"MRChooseClassV1\0"),
        (EXPORT_OPPONENT_LIMIT - DATA_BASE, b"MROpponentLimitV1\0"),
        (EXPORT_CAN_START - DATA_BASE, b"MRCanStartQuickRaceV1\0"),
        (EXPORT_START_PHASE - DATA_BASE, b"MRSetStartPhaseV1\0"),
    ]
    if has_challenge:
        export_strings.append((EXPORT_CHALLENGE - DATA_BASE, b"MRChallengeV1\0"))
    if is_g2:
        export_strings.append((EXPORT_PLAYER_CAR - DATA_BASE, b"MRQuickRacePlayerCarV1\0"))
    if registry_pool:export_strings.append((EXPORT_REGISTRY_POOL-DATA_BASE,b'MRFilterAiPoolV1\0'))
    for at, value in export_strings:
        data[at:at + len(value)] = value

    operations: list[dict[str, Any]] = []
    operations.append(_patch_op(
        source, pe, "oep-bootstrap", "shared-runtime-bootstrap", FEATURE_BOOTSTRAP,
        OEP, OEP_REPLAY, jump(OEP, BOOTSTRAP_BASE, len(OEP_REPLAY)),
        "Load the exact adjacent runtime core and configure it before retail CRT/game constructors.",
    ))
    for name, (spec, _selector_code, labels) in selectors.items():
        prefix = {"QuickRace": "quickrace", "MasterRallye": "masterrallye",
                  "RallyeCup/Invitation": "cup-invitation"}[name]
        for site_name, label in (("init", "init"), ("loop", "loop"), ("end", "pool_end")):
            va, original_hex = spec[site_name]
            expected = bytes.fromhex(original_hex)
            operations.append(_patch_op(
                source, pe, prefix + "-selector-" + site_name,
                prefix + "-class-selection", FEATURE_RANDOMIZER, va, expected,
                # Asm.label() returns an absolute virtual address. Adding the
                # selector base here a second time creates an out-of-range,
                # invalid target (and would corrupt every native mode hook).
                jump(va, labels[label], len(expected)),
                ("R-MOD3-G1 Quick Race selector: remove prior physical IDs while unique eligible choices remain; on exhaustion preserve only the human exclusion and let the native refill repeat a valid CarID."
                 if is_g1 and name == "QuickRace" else
                 "R-AI1.2 Quick Race T1/T2/T3 class seam; native game keeps physical CarID and DriverID selection."
                 if checkpoint == "v13" else
                 f"{name} native generation boundary; policy selects a class while native code owns physical CarID and DriverID."),
            ))
    operations.append(_patch_op(
        source, pe, "opponent-list-append", "quickrace-opponent-selector",
        FEATURE_OPPONENTS, UI_LIST_HOOK, UI_LIST_ORIGINAL,
        jump(UI_LIST_HOOK, UI_LIST_BASE, len(UI_LIST_ORIGINAL)),
        "Append localized number-bank entries up to the configured native AI count.",
    ))
    operations.append(_patch_op(
        source, pe, "opponent-arrow-bound", "quickrace-opponent-selector",
        FEATURE_OPPONENTS, UI_ARROW_SITE, UI_ARROW_ORIGINAL,
        bytes.fromhex("83fd06"),
        "Allow native right-arrow navigation through index six; launcher materializes max_opponents-1.",
    ))
    start_gate = make_start_gate_code()
    operations.append(_patch_op(
        source, pe, "quickrace-start-guard", "quickrace-opponent-safety-gate",
        FEATURE_OPPONENTS, START_CALL_SITE, START_CALL_ORIGINAL,
        jump(START_CALL_SITE, START_GATE_BASE, len(START_CALL_ORIGINAL)),
        "Apply pre-start capability checks, call native Quick Race setup once, then preserve the stock state-10 transition without a pre-scene Race-counter veto.",
    ))
    if has_challenge:
        operations.extend((
            _patch_op(source, pe, "challenge-preview-identity", "challenge-preview-cache",
                      FEATURE_RANDOMIZER, 0x0045EC35, bytes.fromhex("8bbc3874050000"),
                      jump(0x0045EC35, CHALLENGE_PREVIEW_BASE, 7),
                      "Prepare/reuse the exact physical opponent ID consumed by native Challenge name and model publication."),
            _patch_op(source, pe, "challenge-screen-entry-reset", "challenge-preview-cache",
                      FEATURE_RANDOMIZER, 0x0045E511,
                      rel32(0x0045E511, 0x004E3DD0, 0xE8),
                      rel32(0x0045E511, CHALLENGE_RESET_ENTRY_BASE, 0xE8),
                      "Invalidate a prior Challenge preview before native screen initialization."),
            _patch_op(source, pe, "challenge-back-reset", "challenge-preview-cache",
                      FEATURE_RANDOMIZER, 0x0045EA9A,
                      rel32(0x0045EA9A, 0x0045D910, 0xE8),
                      rel32(0x0045EA9A, CHALLENGE_RESET_BACK_BASE, 0xE8),
                      "Invalidate preview on Back, then tail-call the original frontend transition."),
            _patch_op(source, pe, "challenge-race-consume", "challenge-preview-cache",
                      FEATURE_RANDOMIZER, 0x0045010E, bytes.fromhex("8bbc3874050000"),
                      jump(0x0045010E, CHALLENGE_CONSUMER_BASE, 7),
                      "Consume the already prepared absolute ID; Stock and missing cache preserve authored identity."),
        ))
    if is_g2:
        operations.extend((
            _patch_op(source, pe, "quickrace-player-select-entry", "quickrace-player-vehicle",
                      FEATURE_RANDOMIZER, 0x0047AC50, bytes.fromhex("E8 5B 33 03 00"),
                      rel32(0x0047AC50, PLAYER_ENTRY_GATE_BASE, 0xE8),
                      "Prepare one player CarID at the Quick Race Vehicle Select constructor entry before VehicleSelect/CarModel is published."),
            _patch_op(source, pe, "quickrace-player-setup-consume", "quickrace-player-vehicle",
                      FEATURE_RANDOMIZER, 0x0047B78A, bytes.fromhex("E8 21 28 03 00"),
                      rel32(0x0047B78A, PLAYER_SETUP_GATE_BASE, 0xE8),
                      "Consume the cached player CarID at native Quick Race setup before Race/Car0 identity is published."),
        ))
    ranges = sorted((int(op["rva"]), int(op["rva"]) + len(bytes.fromhex(op["replacement_hex"])), op["id"])
                    for op in operations)
    for current, following in zip(ranges, ranges[1:]):
        if current[1] > following[0]:
            raise NativePlanError(f"image patch operations overlap: {current[2]} / {following[2]}")
    code_ranges = sorted((CODE_BASE + at, CODE_BASE + at + len(blob), f"object@{at:#x}")
                         for at, blob in code_objects)
    for begin, end, label in code_ranges:
        if not CODE_BASE <= begin < end <= CODE_BASE + CODE_ALLOCATION_SIZE:
            raise NativePlanError(f"remote {label} lies outside the verified code allocation")
    for current, following in zip(code_ranges, code_ranges[1:]):
        if current[1] > following[0]:
            raise NativePlanError(f"remote code ranges overlap: {current[2]} / {following[2]}")

    reserved_data = [(CONFIG_BLOB - DATA_BASE, CONFIG_BLOB - DATA_BASE + 4 + 4096, "INI blob"),
                     (DLL_PATH - DATA_BASE, DLL_PATH - DATA_BASE + 0x1000, "UTF-16 runtime DLL path")]
    data_ranges = sorted([(at, at + len(value), f"string {at:#x}") for at, value in export_strings] + reserved_data)
    for current, following in zip(data_ranges, data_ranges[1:]):
        if current[1] > following[0]:
            raise NativePlanError(f"remote data ranges overlap: {current[2]} / {following[2]}")
    if data_ranges[-1][1] > DATA_ALLOCATION_SIZE:
        raise NativePlanError("remote data objects exceed the verified data allocation")

    code_used = max(end - CODE_BASE for _begin, end, _label in code_ranges)
    data_used = max(at + len(value) for at, value in export_strings)
    _quick_spec, _quick_code, quick_labels = selectors["QuickRace"]
    if checkpoint == "v13":
        code_symbols = {"choice_gate": CHOICE_GATE, "limit_gate": LIMIT_GATE,
                        "selector": SELECTOR_BASE,
                        # Retain the historical v13 metadata shape exactly;
                        # emitted hook bytes below have always targeted the
                        # actual 0x70001000 selector allocation.
                        "selector_labels": {label: SELECTOR_BASE + address
                                            for label, address in quick_labels.items()},
                        "ui_list": UI_LIST_BASE, "start_gate": START_GATE_BASE,
                        "bootstrap": BOOTSTRAP_BASE}
    elif checkpoint == "f1":
        code_symbols = {"choice_gate": CHOICE_GATE, "limit_gate": LIMIT_GATE,
                        "selector": SELECTOR_BASE,
                        "selector_labels": dict(quick_labels),
                        "ui_list": UI_LIST_BASE, "start_gate": START_GATE_BASE,
                        "bootstrap": BOOTSTRAP_BASE}
    else:
        code_symbols = {"choice_gate": CHOICE_GATE,
                        "challenge_gate": CHALLENGE_GATE if has_challenge else None,
                        "limit_gate": LIMIT_GATE, "selector": SELECTOR_BASE,
                        "selectors": {name: {"base": spec["base"], "labels": dict(labels)}
                                      for name, (spec, _selector_code, labels) in selectors.items()},
                        "ui_list": UI_LIST_BASE, "start_gate": START_GATE_BASE,
                        "challenge_preview": CHALLENGE_PREVIEW_BASE if has_challenge else None,
                        "challenge_reset_entry": CHALLENGE_RESET_ENTRY_BASE if has_challenge else None,
                        "challenge_reset_back": CHALLENGE_RESET_BACK_BASE if has_challenge else None,
                        "challenge_consumer": CHALLENGE_CONSUMER_BASE if has_challenge else None,
                        "bootstrap": BOOTSTRAP_BASE}
    if is_g2:
        code_symbols["quickrace_player_entry"] = PLAYER_ENTRY_GATE_BASE
        code_symbols["quickrace_player_setup_consume"] = PLAYER_SETUP_GATE_BASE
    data_symbols = {"module": SLOT_MODULE, "configure_fn": SLOT_CONFIGURE,
                    "choose_class_fn": SLOT_CHOOSE_CLASS, "opponent_limit_fn": SLOT_OPPONENT_LIMIT,
                    "can_start_fn": SLOT_CAN_START,
                    "set_start_phase_fn": SLOT_START_PHASE,
                    "load_library_w_fn": SLOT_LOAD_LIBRARY_W,
                    "config_blob": CONFIG_BLOB, "dll_path_utf16": DLL_PATH,
                    "exports": {"MRConfigureBlobV1": EXPORT_CONFIGURE,
                                "MRChooseClassV1": EXPORT_CHOOSE_CLASS,
                                "MROpponentLimitV1": EXPORT_OPPONENT_LIMIT,
                                "MRCanStartQuickRaceV1": EXPORT_CAN_START,
                                "MRSetStartPhaseV1": EXPORT_START_PHASE}}
    if has_challenge:
        data_symbols["challenge_fn"] = SLOT_CHALLENGE
        data_symbols["exports"]["MRChallengeV1"] = EXPORT_CHALLENGE
    if is_g2:
        data_symbols["player_car_fn"] = SLOT_PLAYER_CAR
        data_symbols["exports"]["MRQuickRacePlayerCarV1"] = EXPORT_PLAYER_CAR
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R-MOD1-D" if checkpoint == "v13" else "R-MOD3-G2" if is_g2 else "R-MOD3-G1" if is_g1 else "R-MOD1-F",
        **({"checkpoint": checkpoint} if checkpoint != "v13" else {}),
        **({'registry_ai_pool':True} if registry_pool else {}),
        "status": "STATICALLY_VERIFIED_RUNTIME_PLAN_TEMPLATE",
        "runtime_qualified": False,
        "source_executable": {"sha256": RETAIL_SHA256, "size": RETAIL_SIZE,
                               "machine": "I386", "image_base": 0x400000},
        "runtime_core": {"sha256": sha256(runtime_dll), "size": len(runtime_dll),
                          "required_exports": sorted(required_exports)},
        "startup": {"method": "external suspended-process launcher + OEP trampoline",
                    "entry_va": OEP, "replayed_original_hex": OEP_REPLAY.hex(),
                    "iat_va": IAT_VA, "dll_init_work_under_loader_lock": False,
                    "retail_constructors_start_after_configure": True},
        "remote_allocations": [
            {"name": "rmod1-code", "base": CODE_BASE, "size": CODE_ALLOCATION_SIZE,
             "final_protection": "PAGE_EXECUTE_READ", "used_size": code_used,
             "template_sha256": sha256(bytes(code[:code_used]))},
            {"name": "rmod1-data", "base": DATA_BASE, "size": DATA_ALLOCATION_SIZE,
             "final_protection": "PAGE_READWRITE", "used_size": data_used,
             "template_sha256": sha256(bytes(data[:data_used]))},
        ],
        "code_symbols": code_symbols,
        "data_symbols": data_symbols,
        "operations": operations,
        "feature_selection": {"randomizer_bit": FEATURE_RANDOMIZER,
                              "opponent_extender_bit": FEATURE_OPPONENTS,
                              "bootstrap_bit": FEATURE_BOOTSTRAP},
        "limits": {"native_ai_maximum": 3, "ui_ai_maximum": 7,
                   "static_extended_ai_minimum": 4, "static_extended_ai_maximum": 7,
                   "runtime_qualified_extended_ai": 4,
                   "runtime_qualified_total_participants": 5,
                   "higher_count_runtime": "PENDING_HUMAN_QUALIFICATION",
                   "maximum_total_participants": 8,
                   "raw_frontend_split_authoritative": False,
                   "actual_human_topology_source": "RACE_NUMPLAYERS_AND_PARTICIPANT_PLAYERTYPE_AFTER_SETUP",
                   "one_human_qualification_oracle": "experimental_extended_roster_matches",
                   "post_setup_start_veto": "NONE; no observer hook installed"},
        **({"duplicate_support": {
            "status": "CONFIRMED_BY_RUNTIME" if is_g2 else "STATICALLY_VERIFIED_HUMAN_RUNTIME_PENDING",
            "quick_race_selection": "unique eligible physical IDs first; after exhaustion retain the human-car exclusion and allow native source-pool refill",
            "participant_identity": "native per-CarN CarID/Class/DriverID publication and participant construction remain unchanged",
            "duplicates_never": "pre-start Quick Race capacity refusal only when the selected roster exceeds the distinct eligible pool",
            "start_scope": "mode-2 Quick Race only; all other modes keep native Start passthrough",
        }} if is_g1 else {}),
        **({"mode_generation_owners": {
            "QuickRace": {
                "race_type": 2,
                "generation_owner": 0x0047B780,
                "native_selector": 0x00458090,
                "selection_sites": [0x0045810B, 0x00458379, 0x004582D5],
                "existing_roster": "restart reuses current native roster",
            },
            "RallyeCup": ({
                "race_type": 6,
                "generation_owner": 0x0045BE10,
                "native_selector": 0x0045ABC0,
                "selection_sites": [0x0045AC79, 0x0045AF0F, 0x0045AE66],
                "existing_roster": "native RaceData/CompetitorN reused across stages",
            } if has_mode_owners else {"checkpoint_status": "STOCK_OWNER_NOT_HOOKED"}),
            "Invitation": ({
                "race_type": 8,
                "shared_builder": "RallyeCup",
                "pool_rule": "ordinary T3 IDs 14..20; no bonus/progression T3 additions",
                "existing_roster": "native event roster reused across stages",
            } if has_mode_owners else {"checkpoint_status": "STOCK_OWNER_NOT_HOOKED"}),
            "MasterRallye": ({
                "race_type": 5,
                "generation_owner": 0x00452590,
                "native_selector": 0x00451DD0,
                "selection_sites": [0x00451E90, 0x004520D2, 0x0045202D],
                "existing_roster": "native save/load reuse",
                "mutation_boundary": "new competition generation only",
            } if has_mode_owners else {"checkpoint_status": "STOCK_OWNER_NOT_HOOKED"}),
            "Challenge": ({
                "race_type": 7,
                "screen_init": 0x0045E4F0,
                "preview_owner": 0x0045EB30,
                "preview_car_id": 0x0045EC35,
                "preview_name": "Frontend/Challenge/Car2Text",
                "preview_model": "Frontend/Challenge/OpponentCar",
                "race_constructor": 0x0044FEC0,
                "race_consume_car_id": 0x0045010E,
                "lifetime": "ChallengePreviewCache keyed by event and authored human/opponent; Back/reentry resets; Start consumes same CarID; Retry reuses native attempt",
            } if has_challenge else {"checkpoint_status": "AUTHORED_STOCK_MATCHUP_NOT_HOOKED"}),
        }} if has_mode_owners else {}),
        "executable_image_modification": False,
        "resource_overlay_required": False,
        "renderer_proxy_modified": False,
    }
    if is_g2:
        payload["g1_runtime_baseline"] = {
            "status": "OWNER_CONFIRMED_RUNTIME_AND_BROKER_EVIDENCE",
            "num_cars": 8,
            "num_players": 1,
            "ai_participants": 7,
            "duplicate_vehicle_id": 8,
            "duplicate_slots": [3, 7],
            "separate_driver_ids": [6, 5],
            "all_finished": True,
            "results_count": 8,
            "candidate_sha256_supplied": False,
            "raw_snapshots_present_in_checkout": False,
            "post_results_dump_crash": "separate Observatory unsafe post-results dump investigation",
        }
        payload["player_vehicle"] = {
            "scope": "Quick Race player zero only",
            "entry_owner": 0x0047AB30,
            "entry_publish_site": 0x0047AC50,
            "setup_owner": 0x0047B780,
            "setup_publish_site": 0x0047B78A,
            "native_getter": 0x004ADFB0,
            "native_setter": 0x004ADF50,
            "selection_lifetime": "one callback preparation per Vehicle Select constructor entry; setup consumes cached identity",
            "navigation": "native browse/commit handlers are outside this integration and require human qualification",
            "physical_car_aliasing": False,
        }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    payload["plan_template_sha256"] = sha256(canonical)
    # These exact bytes are inputs to the native launcher-header generator;
    # they are not a modified executable or a file patch candidate.
    payload["_code_template_hex"] = bytes(code[:code_used]).hex()
    payload["_data_template_hex"] = bytes(data[:data_used]).hex()
    return payload


def public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in plan.items() if not key.startswith("_")}


def render_cpp_header(plan: dict[str, Any]) -> str:
    """Render deterministic, source-only launcher constants from a verified plan."""
    def byte_array(hex_text: str) -> str:
        raw = bytes.fromhex(hex_text)
        return ",".join(f"0x{value:02x}" for value in raw)

    operations = []
    for operation in plan["operations"]:
        operations.append(
            "    {\"%s\", %du, 0x%08xu, \"%s\", \"%s\"}" % (
                operation["id"], operation["feature_mask"], operation["rva"],
                operation["expected_original_hex"], operation["replacement_hex"],
            )
        )
    code = plan["_code_template_hex"]
    data = plan["_data_template_hex"]
    lines = [
        "#pragma once",
        "#include <cstddef>",
        "#include <cstdint>",
        "namespace rmod1_plan {",
        "struct ImageOperation { const char* id; std::uint32_t feature; std::uint32_t rva; const char* expected_hex; const char* replacement_hex; };",
        f"inline constexpr char kRetailSha256[] = \"{plan['source_executable']['sha256']}\";",
        f"inline constexpr std::uint32_t kRetailSize = {plan['source_executable']['size']}u;",
        f"inline constexpr std::uint32_t kImageBase = 0x{plan['source_executable']['image_base']:08x}u;",
        "inline constexpr std::uint32_t kImageSize = 0x00311000u;",
        f"inline constexpr char kRuntimeCoreSha256[] = \"{plan['runtime_core']['sha256']}\";",
        f"inline constexpr char kPlanSha256[] = \"{plan['plan_template_sha256']}\";",
        f"inline constexpr std::uint32_t kCodeBase = 0x{CODE_BASE:08x}u;",
        f"inline constexpr std::uint32_t kCodeSize = 0x{CODE_ALLOCATION_SIZE:x}u;",
        f"inline constexpr std::uint32_t kDataBase = 0x{DATA_BASE:08x}u;",
        f"inline constexpr std::uint32_t kDataSize = 0x{DATA_ALLOCATION_SIZE:x}u;",
        f"inline constexpr bool kRegistryAiPool = {'true' if plan.get('registry_ai_pool',False) else 'false'};",
        f"inline constexpr std::uint32_t kSlotRegistryAiPool = 0x{SLOT_REGISTRY_POOL:08x}u;",
        f"inline constexpr std::uint32_t kSlotModule = 0x{SLOT_MODULE:08x}u;",
        f"inline constexpr std::uint32_t kSlotConfigure = 0x{SLOT_CONFIGURE:08x}u;",
        f"inline constexpr std::uint32_t kSlotChooseClass = 0x{SLOT_CHOOSE_CLASS:08x}u;",
        f"inline constexpr std::uint32_t kSlotOpponentLimit = 0x{SLOT_OPPONENT_LIMIT:08x}u;",
        f"inline constexpr std::uint32_t kSlotCanStart = 0x{SLOT_CAN_START:08x}u;",
        f"inline constexpr std::uint32_t kSlotLoadLibraryW = 0x{SLOT_LOAD_LIBRARY_W:08x}u;",
        f"inline constexpr std::uint32_t kSlotStartPhase = 0x{SLOT_START_PHASE:08x}u;",
        f"inline constexpr std::uint32_t kSlotChallenge = 0x{SLOT_CHALLENGE:08x}u;",
        *([f"inline constexpr std::uint32_t kSlotPlayerCar = 0x{SLOT_PLAYER_CAR:08x}u;"]
          if plan.get("checkpoint") == "g2" else []),
        f"inline constexpr std::uint32_t kDllPathOffset = 0x{DLL_PATH - DATA_BASE:x}u;",
        f"inline constexpr std::uint32_t kConfigOffset = 0x{CONFIG_BLOB - DATA_BASE:x}u;",
        f"inline constexpr std::uint32_t kMaxOpponents = {plan['limits']['ui_ai_maximum']}u;",
        f"inline constexpr std::uint32_t kFeatureBootstrap = {FEATURE_BOOTSTRAP}u;",
        f"inline constexpr std::uint32_t kFeatureRandomizer = {FEATURE_RANDOMIZER}u;",
        f"inline constexpr std::uint32_t kFeatureOpponents = {FEATURE_OPPONENTS}u;",
        f"inline constexpr std::size_t kCodeUsed = {plan['remote_allocations'][0]['used_size']}u;",
        f"inline constexpr std::size_t kDataUsed = {plan['remote_allocations'][1]['used_size']}u;",
        f"inline constexpr char kCodeTemplateSha256[] = \"{plan['remote_allocations'][0]['template_sha256']}\";",
        f"inline constexpr char kDataTemplateSha256[] = \"{plan['remote_allocations'][1]['template_sha256']}\";",
        f"inline constexpr std::size_t kCodeTemplateSize = {len(code) // 2}u;",
        f"inline constexpr std::uint8_t kCodeTemplate[] = {{{byte_array(code)}}};",
        f"inline constexpr std::size_t kDataTemplateSize = {len(data) // 2}u;",
        f"inline constexpr std::uint8_t kDataTemplate[] = {{{byte_array(data)}}};",
        f"inline constexpr std::size_t kOperationCount = {len(operations)}u;",
        "inline constexpr ImageOperation kOperations[] = {",
        ",\n".join(operations),
        "};",
        "}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("retail_exe", type=Path)
    parser.add_argument("runtime_dll", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--header-output", type=Path)
    parser.add_argument("--checkpoint", choices=("v13", "f1", "f2", "f3", "g1", "g2"), default="v13")
    args = parser.parse_args()
    plan = build_plan(args.retail_exe.read_bytes(), args.runtime_dll.read_bytes(), checkpoint=args.checkpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(public_plan(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.header_output:
        args.header_output.parent.mkdir(parents=True, exist_ok=True)
        args.header_output.write_text(render_cpp_header(plan), encoding="ascii", newline="\n")
    print(json.dumps({"status": plan["status"], "runtime_qualified": False,
                      "plan_template_sha256": plan["plan_template_sha256"],
                      "operation_count": len(plan["operations"]),
                      "code_template_sha256": plan["remote_allocations"][0]["template_sha256"],
                      "runtime_core_sha256": plan["runtime_core"]["sha256"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
