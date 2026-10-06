#!/usr/bin/env python3
"""Build the gated R5V-H forced-ID26 AI materialization proof candidate.

This first-stage tool composes pristine retail -> G.1 Mercedes -> G.2 audio
profile 0, then substitutes the final selected CarID at one guarded Quick Race
publication seam. It deliberately does not alter the AI pool; natural T1 pool
membership is a later stage that requires a human pass of this candidate.
Generated executables belong under ignored research-output.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
from typing import Any

try:
    import build_vehicle_audio_candidate as audio
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style import for tests
    from tools import build_vehicle_audio_candidate as audio
    from tools import patch_vehicle_registry_id26 as registry


RETAIL_SHA256 = audio.RETAIL_SHA256
RETAIL_SIZE = audio.RETAIL_SIZE
G1_SHA256 = audio.G1_SHA256
G2_PROFILE0_SHA256 = "636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f"
G2_PROFILE0_ID = 0

AI_POOL_FUNCTION_VA = 0x00458090
QUICK_RACE_SETUP_FUNCTION_VA = 0x0047B780
SPLIT_SCREEN_CALL_VA = 0x0047B93D
SINGLE_PLAYER_CALL_VA = 0x0047B96E
SINGLE_PLAYER_RETURN_VA = SINGLE_PLAYER_CALL_VA + 5

AI_PUBLICATION_HOOK_VA = 0x00458428
AI_PUBLICATION_RESUME_VA = 0x0045842D
AI_PROOF_STUB_VA = 0x0068E690
AI_PROOF_SLOT = 1
AI_PROOF_END_SLOT = 4
AI_PROOF_CLASS = 0
AI_PROOF_PLAYER_CAR_ID = 0
AI_PROOF_SECOND_EXCLUDED_CAR_ID = -1
AI_PROOF_PHYSICAL_CAR_ID = 26

# FUN_00458090 entry frame is 0x80 bytes below its incoming return address at
# the publication hook. These parameter offsets were rechecked against the
# current retail Ghidra export and raw retail instruction bytes.
STACK_RETURN_ADDRESS = 0x80
STACK_CLASS_ARGUMENT = 0x8C
STACK_PLAYER_CAR_ID_ARGUMENT = 0x90
STACK_SECOND_CAR_ID_ARGUMENT = 0x94
STACK_SELECTED_CAR_ID = 0x14

EXPECTED_PUBLICATION_BYTES = bytes.fromhex("8B44241450")
AI_PROOF_MODE = "forced-id26-proof"


class CandidateError(ValueError):
    """The build identity, original bytes, or patch layout was not exact."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_jump(source_va: int, target_va: int) -> bytes:
    displacement = target_va - (source_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise CandidateError("relative JMP target is outside x86 rel32 range")
    return b"\xE9" + struct.pack("<i", displacement)


def _cmp_stack_imm8(offset: int, value: int) -> bytes:
    if not 0 <= offset <= 0xFFFFFFFF or not -128 <= value <= 127:
        raise CandidateError("stack comparison is outside the supported x86 encoding")
    return b"\x83\xBC\x24" + struct.pack("<I", offset) + struct.pack("b", value)


def forced_proof_stub_bytes(stub_va: int = AI_PROOF_STUB_VA) -> bytes:
    """Encode a fail-closed exact-single-player-Car1 publication guard.

    Every failed comparison branches to the replayed retail instructions. Only
    the normal Quick Race one-human call at 0x0047B96E with T1 class, Car0=ID0,
    three AI slots, and current slot Car1 substitutes stack local CarID=26.
    """
    code = bytearray()
    conditional_fixups: list[int] = []

    def jne_restore() -> None:
        code.extend(b"\x0F\x85")  # JNE rel32
        conditional_fixups.append(len(code))
        code.extend(bytes(4))

    # The caller-return guard makes the one-human Quick Race path explicit and
    # excludes the split-screen call site even if its arguments later overlap.
    code.extend(b"\x81\xBC\x24")
    code.extend(struct.pack("<I", STACK_RETURN_ADDRESS))
    code.extend(struct.pack("<I", SINGLE_PLAYER_RETURN_VA))
    jne_restore()

    code.extend(bytes.fromhex("83FE01"))  # cmp esi, Car1
    jne_restore()
    code.extend(bytes.fromhex("83FD04"))  # cmp ebp, end slot Car4 (3 AI)
    jne_restore()
    code.extend(_cmp_stack_imm8(STACK_CLASS_ARGUMENT, AI_PROOF_CLASS))
    jne_restore()
    code.extend(_cmp_stack_imm8(STACK_PLAYER_CAR_ID_ARGUMENT, AI_PROOF_PLAYER_CAR_ID))
    jne_restore()
    code.extend(_cmp_stack_imm8(
        STACK_SECOND_CAR_ID_ARGUMENT, AI_PROOF_SECOND_EXCLUDED_CAR_ID
    ))
    jne_restore()

    code.extend(b"\xC7\x44\x24")
    code.extend(struct.pack("B", STACK_SELECTED_CAR_ID))
    code.extend(struct.pack("<I", AI_PROOF_PHYSICAL_CAR_ID))

    restore_offset = len(code)
    restore_va = stub_va + restore_offset
    for fixup_offset in conditional_fixups:
        displacement = restore_va - (stub_va + fixup_offset + 4)
        code[fixup_offset:fixup_offset + 4] = struct.pack("<i", displacement)

    # Replay both displaced instructions exactly, then return to the original
    # next instruction at 0x0045842D. The chooser's stack and driver state stay
    # intact; downstream retail code publishes CarID and derives CarClass.
    code.extend(bytes.fromhex("8B44241450"))
    jump_va = stub_va + len(code)
    code.extend(_relative_jump(jump_va, AI_PUBLICATION_RESUME_VA))
    return bytes(code)


def _patch_operation(name: str, category: str, offset: int, original: bytes,
                     replacement: bytes, purpose: str, *, va: int) -> dict[str, Any]:
    if len(original) != len(replacement):
        raise CandidateError(f"patch operation changes size: {name}")
    return {
        "name": name,
        "category": category,
        "file_offset": offset,
        "virtual_address": va,
        "original_bytes": original.hex(),
        "replacement_bytes": replacement.hex(),
        "semantic_purpose": purpose,
    }


def _parse_candidate_pe(candidate: bytes) -> dict[str, Any]:
    pe_offset = struct.unpack_from("<I", candidate, 0x3C)[0]
    if candidate[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise CandidateError("candidate PE signature is invalid")
    coff = pe_offset + 4
    if struct.unpack_from("<H", candidate, coff)[0] != 0x14C:
        raise CandidateError("candidate is not 32-bit x86")
    section_count = struct.unpack_from("<H", candidate, coff + 2)[0]
    optional_size = struct.unpack_from("<H", candidate, coff + 16)[0]
    if section_count != 4 or optional_size != 0xE0:
        raise CandidateError("candidate section layout differs from supported retail")
    section_table = coff + 20 + optional_size
    sections: list[dict[str, Any]] = []
    for index in range(section_count):
        header = section_table + index * 40
        name = candidate[header:header + 8].split(b"\0", 1)[0].decode("ascii")
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", candidate, header + 8)
        sections.append({
            "name": name,
            "header_offset": header,
            "virtual_size": virtual_size,
            "rva": rva,
            "raw_size": raw_size,
            "raw_offset": raw_offset,
        })
    return {
        "image_base": struct.unpack_from("<I", candidate, coff + 20 + 28)[0],
        "sections": sections,
    }


def make_candidate(data: bytes, *, mode: str = AI_PROOF_MODE,
                   expected_source_sha256: str = RETAIL_SHA256,
                   expected_g1_sha256: str = G1_SHA256,
                   expected_g2_sha256: str = G2_PROFILE0_SHA256) -> tuple[bytes, dict[str, Any]]:
    """Build the one gated forced-ID26 proof from exact pristine retail."""
    if mode != AI_PROOF_MODE:
        raise CandidateError(
            "natural-t1-pool mode is intentionally unavailable until the forced AI runtime gate passes"
        )
    source_digest = sha256(data)
    if source_digest != expected_source_sha256.lower():
        raise CandidateError(f"unsupported pristine retail SHA256: {source_digest}")
    if source_digest == RETAIL_SHA256 and len(data) != RETAIL_SIZE:
        raise CandidateError(f"unsupported pristine retail size: {len(data)}")

    g2_candidate, g2_manifest = audio.make_candidate(
        data,
        G2_PROFILE0_ID,
        expected_source_sha256=source_digest,
        expected_g1_sha256=expected_g1_sha256,
    )
    g2_digest = sha256(g2_candidate)
    if g2_digest != expected_g2_sha256.lower():
        raise CandidateError(f"G.2 profile-0 reproduction hash mismatch: {g2_digest}")

    pe = registry.parse_pe(data)
    hook_offset = registry.va_to_file_offset(pe, AI_PUBLICATION_HOOK_VA,
                                             len(EXPECTED_PUBLICATION_BYTES))
    if data[hook_offset:hook_offset + len(EXPECTED_PUBLICATION_BYTES)] != EXPECTED_PUBLICATION_BYTES:
        raise CandidateError("AI publication hook bytes differ from expected retail MOV/PUSH")

    # These exact CALL encodings prove the known parent and return address.
    for call_va in (SPLIT_SCREEN_CALL_VA, SINGLE_PLAYER_CALL_VA):
        call_offset = registry.va_to_file_offset(pe, call_va, 5)
        expected_call = audio._call_rel32(call_va, AI_POOL_FUNCTION_VA)
        if data[call_offset:call_offset + 5] != expected_call:
            raise CandidateError(f"Quick Race chooser call changed at 0x{call_va:08X}")

    stub = forced_proof_stub_bytes()
    stub_offset = registry.va_to_file_offset(pe, AI_PROOF_STUB_VA, len(stub))
    if data[stub_offset:stub_offset + len(stub)] != bytes(len(stub)):
        raise CandidateError("H proof code-cave range is not zero-filled in pristine retail")
    if g2_candidate[stub_offset:stub_offset + len(stub)] != bytes(len(stub)):
        raise CandidateError("H proof code-cave range overlaps the composed G.1/G.2 payload")

    operations = copy.deepcopy(g2_manifest["operations"])
    size_op = next((op for op in operations if op["name"] == "pe_text_virtual_size"), None)
    if size_op is None:
        raise CandidateError("composed G.2 manifest has no .text VirtualSize operation")
    text = next((section for section in pe["sections"] if section["name"] == ".text"), None)
    rdata = next((section for section in pe["sections"] if section["name"] == ".rdata"), None)
    if text is None or rdata is None:
        raise CandidateError("expected retail .text and .rdata sections")

    g1_vsize = int(g2_manifest["text_virtual_size"]["g1_patched"])
    g2_vsize = int(g2_manifest["text_virtual_size"]["patched"])
    text_base_va = registry.IMAGE_BASE + text["rva"]
    relative_end = AI_PROOF_STUB_VA - text_base_va + len(stub)
    if relative_end > text["raw_size"]:
        raise CandidateError("H proof stub extends past .text raw data")
    new_text_virtual_size = max(g2_vsize, relative_end)
    if text["rva"] + new_text_virtual_size >= rdata["rva"]:
        raise CandidateError("expanded .text virtual range would overlap .rdata")

    size_op["replacement_bytes"] = struct.pack("<I", new_text_virtual_size).hex()
    size_op["semantic_purpose"] = (
        "map the G.1 registry/display payload, G.2 audio selector, and bounded R5V-H proof stub"
    )

    operations.append(_patch_operation(
        "id26_ai_proof_publication_jump",
        "forced-ai-materialization-proof",
        hook_offset,
        EXPECTED_PUBLICATION_BYTES,
        _relative_jump(AI_PUBLICATION_HOOK_VA, AI_PROOF_STUB_VA),
        ("route only the final selected absolute CarID through a narrow guarded proof; "
         "the displaced retail MOV/PUSH is replayed before resuming at 0x0045842D"),
        va=AI_PUBLICATION_HOOK_VA,
    ))
    operations.append(_patch_operation(
        "id26_ai_proof_guarded_stub",
        "forced-ai-materialization-proof",
        stub_offset,
        bytes(len(stub)),
        stub,
        ("substitute final local CarID with physical ID26 only for the exact "
         "single-player Quick Race call, Car1, T1, Car0 ID0, and three-AI setup"),
        va=AI_PROOF_STUB_VA,
    ))
    operations.sort(key=lambda op: op["file_offset"])
    audio._validate_operations(data, operations)

    result = bytearray(data)
    for operation in operations:
        start = operation["file_offset"]
        replacement = bytes.fromhex(operation["replacement_bytes"])
        result[start:start + len(replacement)] = replacement
    candidate = bytes(result)

    manifest = copy.deepcopy(g2_manifest)
    manifest.update({
        "phase": "R5V-H forced physical-ID26 AI materialization proof",
        "profile": "id26-stock-audio-profile-0",
        "h_research_mode": mode,
        "g2_base_sha256": g2_digest,
        "patched_sha256": sha256(candidate),
        "file_size": len(candidate),
        "text_virtual_size": {
            "original": g2_manifest["text_virtual_size"]["original"],
            "g1_patched": g1_vsize,
            "g2_patched": g2_vsize,
            "patched": new_text_virtual_size,
            "code_cave_va": g2_manifest["text_virtual_size"]["code_cave_va"],
            "g1_payload_size": g2_manifest["text_virtual_size"]["g1_payload_size"],
            "audio_wrapper_va": g2_manifest["text_virtual_size"]["audio_wrapper_va"],
            "audio_wrapper_size": g2_manifest["text_virtual_size"]["audio_wrapper_size"],
            "ai_proof_stub_va": f"0x{AI_PROOF_STUB_VA:08X}",
            "ai_proof_stub_size": len(stub),
            "ai_proof_stub_end_exclusive": f"0x{AI_PROOF_STUB_VA + len(stub):08X}",
            "rdata_rva": f"0x{rdata['rva']:X}",
            "non_overlap_proven": True,
        },
        "operations": operations,
        "operation_counts_by_category": dict(Counter(op["category"] for op in operations)),
        "ai_proof": {
            "status": "READY_FOR_HUMAN_RUNTIME",
            "mode": mode,
            "quick_race_pool_function": f"0x{AI_POOL_FUNCTION_VA:08X}",
            "single_player_call_site": f"0x{SINGLE_PLAYER_CALL_VA:08X}",
            "single_player_return_guard": f"0x{SINGLE_PLAYER_RETURN_VA:08X}",
            "publication_hook": f"0x{AI_PUBLICATION_HOOK_VA:08X}",
            "resume_va": f"0x{AI_PUBLICATION_RESUME_VA:08X}",
            "stub_va": f"0x{AI_PROOF_STUB_VA:08X}",
            "guard": {
                "return_address": SINGLE_PLAYER_RETURN_VA,
                "current_slot_esi": AI_PROOF_SLOT,
                "end_slot_ebp": AI_PROOF_END_SLOT,
                "class_argument": AI_PROOF_CLASS,
                "player_car_id_argument": AI_PROOF_PLAYER_CAR_ID,
                "second_excluded_car_id_argument": AI_PROOF_SECOND_EXCLUDED_CAR_ID,
            },
            "substituted_selected_absolute_car_id": AI_PROOF_PHYSICAL_CAR_ID,
            "participant_count_changed": False,
            "CarClass_written_by_H": False,
            "driver_selection_changed": False,
            "ai_pool_membership_changed": False,
            "g2_audio_profile_id": G2_PROFILE0_ID,
            "runtime_validation": "NOT_TESTED",
            "next_gate": "Do not build natural T1 pool inclusion until a human passes this forced AI proof.",
        },
        "runtime_validation": (
            "Static candidate only. Forced Car1=ID26 must pass the human AI materialization gate "
            "before natural T1 pool membership is implemented."
        ),
        "risks": list(g2_manifest.get("risks", [])) + [
            "The H proof guard is limited to the exact one-human, three-AI, T1 Quick Race call with Car0 ID0.",
            "The forced proof does not add ID26 to the natural AI pool and does not establish natural eligibility.",
            "Broker state and static bytes cannot prove a visible model, AI driving, collision, damage, or race completion.",
        ],
    })
    manifest["patched_sha256"] = sha256(candidate)
    _verify_structure(candidate, manifest)
    return candidate, manifest


def _verify_structure(candidate: bytes, manifest: dict[str, Any]) -> None:
    if sha256(candidate) != manifest.get("patched_sha256"):
        raise CandidateError("candidate SHA256 does not match manifest")
    if len(candidate) != manifest.get("file_size"):
        raise CandidateError("candidate size does not match manifest")
    audio._verify_structure(candidate, manifest)
    layout = _parse_candidate_pe(candidate)
    hook_offset = registry.va_to_file_offset(layout, AI_PUBLICATION_HOOK_VA,
                                             len(EXPECTED_PUBLICATION_BYTES))
    expected_hook = _relative_jump(AI_PUBLICATION_HOOK_VA, AI_PROOF_STUB_VA)
    if candidate[hook_offset:hook_offset + 5] != expected_hook:
        raise CandidateError("candidate AI proof hook does not target the bounded stub")
    stub = forced_proof_stub_bytes()
    stub_offset = registry.va_to_file_offset(layout, AI_PROOF_STUB_VA, len(stub))
    if candidate[stub_offset:stub_offset + len(stub)] != stub:
        raise CandidateError("candidate AI proof stub differs from deterministic encoding")
    text = next(section for section in layout["sections"] if section["name"] == ".text")
    rdata = next(section for section in layout["sections"] if section["name"] == ".rdata")
    if text["virtual_size"] != manifest["text_virtual_size"]["patched"]:
        raise CandidateError("candidate .text VirtualSize does not match manifest")
    if text["rva"] + text["virtual_size"] >= rdata["rva"]:
        raise CandidateError("candidate .text overlaps .rdata")
    if manifest.get("h_research_mode") != AI_PROOF_MODE:
        raise CandidateError("candidate manifest does not identify forced proof mode")
    proof = manifest.get("ai_proof")
    if not isinstance(proof, dict) or proof.get("participant_count_changed") is not False:
        raise CandidateError("candidate manifest does not preserve participant count")
    if proof.get("CarClass_written_by_H") is not False or proof.get("driver_selection_changed") is not False:
        raise CandidateError("candidate manifest claims a forbidden participant-field change")


def verify_existing(source: Path, output: Path, manifest_path: Path, *,
                    mode: str = AI_PROOF_MODE) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if source == output or os.path.samefile(source, output):
        raise CandidateError("candidate must not overwrite pristine retail")
    expected, manifest = make_candidate(source.read_bytes(), mode=mode)
    if output.read_bytes() != expected:
        raise CandidateError("candidate differs from deterministic pristine-to-G.2-to-H rebuild")
    try:
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise CandidateError("invalid candidate manifest") from exc
    if stored != manifest:
        raise CandidateError("stored manifest differs from deterministic candidate rebuild")
    _verify_structure(output.read_bytes(), manifest)
    return manifest


def write_candidate(source: Path, output: Path, manifest_path: Path, *,
                    mode: str = AI_PROOF_MODE) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    if source == output or (output.exists() and os.path.samefile(source, output)):
        raise CandidateError("candidate executable must not overwrite pristine retail")
    if not registry._is_research_output(output):
        raise CandidateError("candidate must be under research-output")
    if output.exists() or manifest_path.exists():
        raise CandidateError("output already exists; choose a new path")
    if len({str(source).casefold(), str(output).casefold(), str(manifest_path).casefold()}) != 3:
        raise CandidateError("source, candidate, and manifest paths must be distinct")
    source_before = sha256(source.read_bytes())
    candidate, manifest = make_candidate(source.read_bytes(), mode=mode)
    if source_before != manifest["source_sha256"]:
        raise CandidateError("source changed during candidate build")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if sha256(output.read_bytes()) != manifest["patched_sha256"]:
        raise CandidateError("written candidate SHA256 mismatch")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="exact supported pristine retail MRallye.exe")
    parser.add_argument("output", type=Path, help="new candidate output under research-output")
    parser.add_argument("--mode", choices=(AI_PROOF_MODE,), required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    manifest_path = args.manifest or args.output.with_name(f"{args.output.stem}.manifest.json")
    try:
        if args.verify_existing:
            manifest = verify_existing(args.source, args.output, manifest_path, mode=args.mode)
        else:
            manifest = write_candidate(args.source, args.output, manifest_path, mode=args.mode)
    except (CandidateError, audio.CandidateError, registry.PatchError, OSError, struct.error) as exc:
        parser.exit(2, f"vehicle AI candidate refused: {exc}\n")
    print(json.dumps({
        "verified_existing": args.verify_existing,
        "mode": args.mode,
        "source_sha256": manifest["source_sha256"],
        "g1_base_sha256": manifest["g1_base_sha256"],
        "g2_base_sha256": manifest["g2_base_sha256"],
        "candidate_sha256": manifest["patched_sha256"],
        "size": manifest["file_size"],
        "participant_count_changed": manifest["ai_proof"]["participant_count_changed"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
