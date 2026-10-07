#!/usr/bin/env python3
"""Build the fail-closed natural T1 pool candidate with physical ID26.

The candidate is composed from pristine retail through the existing G.1/G.2
and neutral hardened base, then changes only the T1 source-pool exit and the
ID26 Results display branch. Native DriverID selection is left untouched; the
Results presentation for physical ID26 is the fixed historical Mercedes name
selected for H.1 after auditing demo group 0x39.
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
from typing import Any

try:
    import build_vehicle_ai_candidate as ai
    import build_vehicle_hardened_candidate as hardened
    import build_vehicle_audio_candidate as audio
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style import for tests
    from tools import build_vehicle_ai_candidate as ai
    from tools import build_vehicle_hardened_candidate as hardened
    from tools import build_vehicle_audio_candidate as audio
    from tools import patch_vehicle_registry_id26 as registry


RETAIL_SHA256 = audio.RETAIL_SHA256
RETAIL_SIZE = audio.RETAIL_SIZE
NEUTRAL_BASE_SHA256 = "391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819"
PROFILE = "natural-t1-id26"

T1_SOURCE_POOL = (0, 1, 2, 3, 4, 5, 6, 26)
T2_SOURCE_POOL = tuple(range(7, 14))
T3_BASE_POOL = tuple(range(14, 21))
T3_PROGRESS_POOL = (21, 22, 23, 24)

T1_EXIT_HOOK_VA = 0x00458167
T1_EXIT_ORIGINAL = bytes.fromhex("E969010000")
T1_REENTRY_VA = 0x00458137
T1_COMMON_EXIT_VA = 0x004582D5
T1_REENTRY_BYTES = bytes.fromhex("3BF574263BF7750583FFFF751D8B5424288D8C2494000000")
T1_BOUND_BYTES = bytes.fromhex("83FE077CD0E969010000")
T1_POOL_STUB_VA = 0x0068E780
T1_APPEND_ID = 26
T1_STOCK_END = 7
T1_FINISHED_END = 27

RESULTS_NAME_HOOK_VA = hardened.RESULTS_NAME_HOOK_VA
RESULTS_NAME_STUB_VA = hardened.RESULTS_NAME_STUB_VA
RESULTS_NAME_ORIGINAL = hardened.RESULTS_NAME_ORIGINAL
RESULTS_LOOKUP_CONTINUATION_VA = 0x0047CC7C
RESULTS_AFTER_LOOKUP_VA = 0x0047CC81
RESULTS_LOOKUP_AND_PUSH_BYTES = bytes.fromhex("8BC8FF520C50")
RESULTS_ID26 = 26
RESULTS_FIXED_DISPLAY_NAME = "JEAN-PIERRE STRUGO"
RESULTS_FIXED_DISPLAY_CLASSIFICATION = "REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER"
RESULTS_FIXED_DISPLAY_CAVE = RESULTS_NAME_STUB_VA

TEXT_BASE_VA = hardened.TEXT_BASE_VA


class CandidateError(ValueError):
    """Raised when a source build, layout, or patch does not match evidence."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel32(source_va: int, target_va: int, opcode: int = 0xE9) -> bytes:
    displacement = target_va - (source_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise CandidateError("relative branch target is outside x86 rel32 range")
    return bytes((opcode,)) + struct.pack("<i", displacement)


def results_name_stub_bytes(stub_va: int = RESULTS_NAME_STUB_VA) -> bytes:
    """Use a fixed Results display only for CarID26, preserving native DriverID.

    All other AI rows replay the retail group-0x39 lookup with physical CarID.
    For ID26 the code places a pointer to the literal name in EAX and resumes
    after the gaLocal call, at the stock string consumer. No participant field
    is read for driver selection or written by this display helper.
    """
    code = bytearray(bytes.fromhex("8B0CAE8B108B4908"))  # record, vtable, CarID
    code.extend(bytes.fromhex("83F91A"))  # cmp ecx,26
    jne_va = stub_va + len(code)
    code.extend(b"\x0F\x85\x00\x00\x00\x00")

    code.extend(b"\xB8\x00\x00\x00\x00")  # mov eax, literal VA
    fixed_jump_va = stub_va + len(code)
    code.extend(_rel32(fixed_jump_va, RESULTS_AFTER_LOOKUP_VA))

    non_id_offset = len(code)
    non_id_va = stub_va + non_id_offset
    code[jne_va - stub_va + 2:jne_va - stub_va + 6] = struct.pack(
        "<i", non_id_va - (jne_va + 6)
    )
    code.extend(bytes.fromhex("8B0CAE8B4908516A39"))  # stock CarID selector, group 39
    code.extend(_rel32(stub_va + len(code), RESULTS_LOOKUP_CONTINUATION_VA))

    string_va = stub_va + len(code)
    name = RESULTS_FIXED_DISPLAY_NAME.encode("ascii") + b"\x00"
    code[18:22] = struct.pack("<I", string_va)
    code.extend(name)
    return bytes(code)


def natural_t1_exit_stub_bytes(stub_va: int = T1_POOL_STUB_VA) -> bytes:
    """Append ID26 by re-entering the stock exclusion/appending loop once."""
    code = bytearray(bytes.fromhex("83FE1B740A"))  # cmp esi,27; je done
    code.extend(b"\xBE" + struct.pack("<I", T1_APPEND_ID))  # mov esi,26
    code.extend(_rel32(stub_va + len(code), T1_REENTRY_VA))
    code.extend(b"\xBE" + struct.pack("<I", T1_STOCK_END))  # restore ESI=7
    code.extend(_rel32(stub_va + len(code), T1_COMMON_EXIT_VA))
    return bytes(code)


def source_pool_after_exclusions(excluded_ids: tuple[int, ...] | list[int] = ()) -> list[int]:
    """Model the exact H.1 T1 source vector plus stock physical-ID exclusions."""
    if len(excluded_ids) > 2:
        raise CandidateError("native T1 pool supports at most two human exclusions")
    if any(type(vehicle_id) is not int for vehicle_id in excluded_ids):
        raise CandidateError("human exclusion IDs must be integers")
    excluded = {vehicle_id for vehicle_id in excluded_ids if vehicle_id >= 0}
    return [vehicle_id for vehicle_id in T1_SOURCE_POOL if vehicle_id not in excluded]


def select_without_repeat(pool: list[int], order: list[int], count: int) -> list[int]:
    """Model stock remove-after-selection for a supplied shuffled ordering."""
    if count < 0 or count > len(pool) or len(order) != len(pool) or set(order) != set(pool):
        raise CandidateError("selection order must be a permutation of the source pool")
    working = list(order)
    selected: list[int] = []
    for _ in range(count):
        vehicle_id = working.pop(0)
        selected.append(vehicle_id)
    return selected


def _operation(name: str, category: str, pe: dict[str, Any], va: int,
               original: bytes, replacement: bytes, purpose: str) -> dict[str, Any]:
    if len(original) != len(replacement):
        raise CandidateError(f"patch operation changes range size: {name}")
    return {
        "name": name,
        "category": category,
        "file_offset": registry.va_to_file_offset(pe, va, len(original)),
        "virtual_address": va,
        "original_bytes": original.hex(),
        "replacement_bytes": replacement.hex(),
        "semantic_purpose": purpose,
    }


def _read_va(data: bytes, pe: dict[str, Any], va: int, length: int) -> bytes:
    offset = registry.va_to_file_offset(pe, va, length)
    return data[offset:offset + length]


def _apply_operations(source: bytes, operations: list[dict[str, Any]]) -> bytes:
    audio._validate_operations(source, operations)
    result = bytearray(source)
    for operation in operations:
        start = operation["file_offset"]
        result[start:start + len(bytes.fromhex(operation["replacement_bytes"]))] = bytes.fromhex(
            operation["replacement_bytes"]
        )
    candidate = bytes(result)
    inverse = bytearray(candidate)
    for operation in reversed(operations):
        start = operation["file_offset"]
        replacement = bytes.fromhex(operation["replacement_bytes"])
        original = bytes.fromhex(operation["original_bytes"])
        if inverse[start:start + len(replacement)] != replacement:
            raise CandidateError(f"post-patch bytes differ at {operation['name']}")
        inverse[start:start + len(original)] = original
    if bytes(inverse) != source:
        raise CandidateError("declared inverse does not restore exact pristine input")
    return candidate


def make_candidate(data: bytes, *,
                   expected_source_sha256: str = RETAIL_SHA256,
                   expected_neutral_base_sha256: str = NEUTRAL_BASE_SHA256,
                   expected_g1_sha256: str = hardened.G1_SHA256,
                   expected_g2_sha256: str = hardened.G2_PROFILE0_SHA256
                   ) -> tuple[bytes, dict[str, Any]]:
    """Build a natural T1-ID26 candidate from exact pristine retail."""
    source_hash = sha256(data)
    if source_hash != expected_source_sha256.lower():
        raise CandidateError(f"unsupported pristine retail SHA256: {source_hash}")
    if source_hash == RETAIL_SHA256 and len(data) != RETAIL_SIZE:
        raise CandidateError(f"unsupported pristine retail size: {len(data)}")

    pe = registry.parse_pe(data)
    checks = (
        (RESULTS_LOOKUP_CONTINUATION_VA, RESULTS_LOOKUP_AND_PUSH_BYTES,
         "stock Results gaLocal and string-stack continuation"),
        (T1_REENTRY_VA, T1_REENTRY_BYTES, "native T1 exclusion and append body"),
        (T1_EXIT_HOOK_VA, T1_EXIT_ORIGINAL, "native T1 source-pool exit"),
        (T1_EXIT_HOOK_VA - 5, T1_BOUND_BYTES, "native T1 0..6 loop bound and exit"),
    )
    for va, expected, purpose in checks:
        if _read_va(data, pe, va, len(expected)) != expected:
            raise CandidateError(f"{purpose} differs from exact retail at 0x{va:08X}")

    neutral_base, base_manifest = hardened.make_candidate(
        data,
        hardened.PROFILE_ORDINARY,
        expected_source_sha256=source_hash,
        expected_g1_sha256=expected_g1_sha256,
        expected_g2_sha256=expected_g2_sha256,
    )
    neutral_hash = sha256(neutral_base)
    if neutral_hash != expected_neutral_base_sha256.lower():
        raise CandidateError(f"neutral hardened base hash mismatch: {neutral_hash}")

    results_stub = results_name_stub_bytes()
    pool_stub = natural_t1_exit_stub_bytes()
    results_offset = registry.va_to_file_offset(pe, RESULTS_FIXED_DISPLAY_CAVE, len(results_stub))
    pool_offset = registry.va_to_file_offset(pe, T1_POOL_STUB_VA, len(pool_stub))
    old_results_stub = hardened.results_name_stub_bytes()
    if neutral_base[results_offset:results_offset + len(old_results_stub)] != old_results_stub:
        raise CandidateError("neutral base Results helper differs from the audited H.0.1 helper")
    if data[results_offset:results_offset + len(results_stub)] != bytes(len(results_stub)):
        raise CandidateError("fixed ID26 Results helper range is not zero-filled in retail")
    if neutral_base[pool_offset:pool_offset + len(pool_stub)] != bytes(len(pool_stub)):
        raise CandidateError("natural T1 code cave overlaps the neutral hardened composition")

    operations = copy.deepcopy(base_manifest["operations"])
    result_stub_op = next((op for op in operations
                           if op["name"] == "id26_results_driver_name_selector_stub"), None)
    size_op = next((op for op in operations if op["name"] == "pe_text_virtual_size"), None)
    if result_stub_op is None or size_op is None:
        raise CandidateError("neutral manifest lacks Results helper or PE size operation")
    result_stub_op["original_bytes"] = bytes(len(results_stub)).hex()
    result_stub_op["replacement_bytes"] = results_stub.hex()
    result_stub_op["semantic_purpose"] = (
        "for physical CarID26 only, return the fixed historical Mercedes Results name; "
        "leave the native DriverID untouched and keep all other group-0x39 lookups stock"
    )

    t1_hook = _operation(
        "natural_t1_pool_exit_hook", "natural-t1-source-pool", pe,
        T1_EXIT_HOOK_VA, T1_EXIT_ORIGINAL,
        _rel32(T1_EXIT_HOOK_VA, T1_POOL_STUB_VA),
        "intercept the native T1 loop exit to append physical ID26 through the same exclusion/appending body",
    )
    t1_stub_op = _operation(
        "natural_t1_pool_id26_append_stub", "natural-t1-source-pool", pe,
        T1_POOL_STUB_VA, bytes(len(pool_stub)), pool_stub,
        "re-enter native pool body for ID26 once, then restore ESI=7 and resume the shared class exit",
    )
    operations.extend((t1_hook, t1_stub_op))

    text = next((section for section in pe["sections"] if section["name"] == ".text"), None)
    rdata = next((section for section in pe["sections"] if section["name"] == ".rdata"), None)
    if text is None or rdata is None or text["raw_size"] != hardened.TEXT_RAW_SIZE:
        raise CandidateError("exact retail .text/.rdata layout differs from the pinned executable")
    highest_end = max(
        RESULTS_FIXED_DISPLAY_CAVE + len(results_stub),
        T1_POOL_STUB_VA + len(pool_stub),
    )
    patched_vsize = max(
        int(base_manifest["text_virtual_size"]["patched"]),
        highest_end - TEXT_BASE_VA,
    )
    if patched_vsize > text["raw_size"] or text["rva"] + patched_vsize >= rdata["rva"]:
        raise CandidateError("H.1 payload extends past .text or overlaps .rdata")
    size_op["replacement_bytes"] = struct.pack("<I", patched_vsize).hex()
    size_op["semantic_purpose"] = (
        "map the G.1/G.2/neutral-hardening payload, fixed ID26 Results name, and natural T1 pool append stub"
    )
    operations.sort(key=lambda op: op["file_offset"])
    candidate = _apply_operations(data, operations)

    # Ensure the natural candidate preserves neutral identity/audio/hardening
    # and has no forced publication hook or randomizer.
    publication_offset = registry.va_to_file_offset(pe, ai.AI_PUBLICATION_HOOK_VA,
                                                    len(ai.EXPECTED_PUBLICATION_BYTES))
    if candidate[publication_offset:publication_offset + len(ai.EXPECTED_PUBLICATION_BYTES)] != ai.EXPECTED_PUBLICATION_BYTES:
        raise CandidateError("H.1 candidate unexpectedly changes the publication hook")
    forced_stub_offset = registry.va_to_file_offset(pe, ai.AI_PROOF_STUB_VA, 64)
    if candidate[forced_stub_offset:forced_stub_offset + 64] != bytes(64):
        raise CandidateError("H.1 candidate contains an H.0 forced-proof stub")

    manifest = copy.deepcopy(base_manifest)
    manifest.update({
        "schema_version": 1,
        "phase": "R5V-H.1 natural T1 AI pool inclusion",
        "profile": PROFILE,
        "patched_sha256": sha256(candidate),
        "file_size": len(candidate),
        "neutral_hardened_base_sha256": neutral_hash,
        "text_virtual_size": {
            "original": base_manifest["text_virtual_size"]["original"],
            "pre_hardening": base_manifest["text_virtual_size"]["pre_hardening"],
            "neutral_hardened": base_manifest["text_virtual_size"]["patched"],
            "patched": patched_vsize,
            "highest_cave_end_exclusive_va": f"0x{highest_end:08X}",
            "rdata_rva": f"0x{rdata['rva']:X}",
            "non_overlap_proven": True,
        },
        "operations": operations,
        "operation_counts_by_category": dict(Counter(op["category"] for op in operations)),
        "natural_t1_id26_pool": {
            "included": True,
            "source_ids": list(T1_SOURCE_POOL),
            "stock_ids_preserved": list(range(7)),
            "id7_forbidden": True,
            "human_exclusion": "native body applies both physical-ID exclusions before append",
            "shuffle_remove_selection": "native unchanged",
            "slot_specific_force": False,
            "unlock_predicate_consulted": False,
        },
        "forced_ai_proof": {"included": False},
        "randomizer": {
            "present": False,
            "stock_mixed_diverse_chooser_changed": False,
            "source_note": "No mixed-class/randomizer code is composed into H.1.",
        },
        "participant_count_changed": False,
        "results_identity": {
            "target_physical_car_id": RESULTS_ID26,
            "policy": "fixed_display_name",
            "display_name": RESULTS_FIXED_DISPLAY_NAME,
            "classification": RESULTS_FIXED_DISPLAY_CLASSIFICATION,
            "exact_ml320_pairing": "unproven",
            "native_driver_id_selection_changed": False,
            "native_driver_id_written": False,
            "other_ai_selector": "physical CarID through original group-0x39 lookup",
            "human_name_branches": "unchanged",
            "physical_car_id_written": False,
            "status": "STATIC_FIX_READY_FOR_HUMAN_RUNTIME",
        },
        "demo_group_0x39": {
            "demo_8_4_1_sha256": "2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a",
            "demo_9_3_1_sha256": "611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728",
            "physical_mercedes_id": 2,
            "selector": 2,
            "mapped_name": "JOSE MARIA SERCIA",
            "classification": "DEVELOPER_PLACEHOLDER_FOR_MERCEDES_ASSOCIATION",
        },
    })
    _verify_structure(candidate, manifest)
    return candidate, manifest


def _verify_structure(candidate: bytes, manifest: dict[str, Any]) -> None:
    if sha256(candidate) != manifest.get("patched_sha256"):
        raise CandidateError("candidate SHA256 differs from manifest")
    if manifest.get("profile") != PROFILE or len(candidate) != manifest.get("file_size"):
        raise CandidateError("candidate profile or size differs from manifest")
    if manifest.get("forced_ai_proof", {}).get("included") is not False:
        raise CandidateError("natural candidate must not contain forced CarN proof")
    if manifest.get("randomizer", {}).get("present") is not False:
        raise CandidateError("natural candidate must not contain a randomizer")
    if manifest.get("participant_count_changed") is not False:
        raise CandidateError("natural candidate may not change participant count")
    if manifest.get("natural_t1_id26_pool", {}).get("source_ids") != list(T1_SOURCE_POOL):
        raise CandidateError("manifest does not declare the exact natural T1 pool")
    identity = manifest.get("results_identity", {})
    if (identity.get("display_name") != RESULTS_FIXED_DISPLAY_NAME
            or identity.get("native_driver_id_selection_changed") is not False
            or identity.get("physical_car_id_written") is not False):
        raise CandidateError("ID26 Results display policy or physical identity is invalid")

    pe = ai._parse_candidate_pe(candidate)
    pool_stub = natural_t1_exit_stub_bytes()
    results_stub = results_name_stub_bytes()
    for va, expected in ((T1_POOL_STUB_VA, pool_stub), (RESULTS_NAME_STUB_VA, results_stub)):
        offset = registry.va_to_file_offset(pe, va, len(expected))
        if candidate[offset:offset + len(expected)] != expected:
            raise CandidateError(f"H.1 helper bytes differ at 0x{va:08X}")
    hook = registry.va_to_file_offset(pe, T1_EXIT_HOOK_VA, len(T1_EXIT_ORIGINAL))
    if candidate[hook:hook + 5] != _rel32(T1_EXIT_HOOK_VA, T1_POOL_STUB_VA):
        raise CandidateError("natural T1 exit does not target the append stub")
    publication = registry.va_to_file_offset(pe, ai.AI_PUBLICATION_HOOK_VA,
                                             len(ai.EXPECTED_PUBLICATION_BYTES))
    if candidate[publication:publication + 5] != ai.EXPECTED_PUBLICATION_BYTES:
        raise CandidateError("H.0 forced publication hook must be absent")
    forced = registry.va_to_file_offset(pe, ai.AI_PROOF_STUB_VA, 64)
    if candidate[forced:forced + 64] != bytes(64):
        raise CandidateError("H.0 forced-proof cave must remain unused")
    text = next(section for section in pe["sections"] if section["name"] == ".text")
    rdata = next(section for section in pe["sections"] if section["name"] == ".rdata")
    if text["virtual_size"] != manifest["text_virtual_size"]["patched"]:
        raise CandidateError("candidate .text VirtualSize differs from manifest")
    if text["rva"] + text["virtual_size"] >= rdata["rva"]:
        raise CandidateError("candidate .text overlaps .rdata")
    if RESULTS_FIXED_DISPLAY_NAME.encode("ascii") + b"\x00" not in results_stub:
        raise CandidateError("fixed ID26 Results literal is missing")


def verify_existing(source: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if source == output or os.path.samefile(source, output):
        raise CandidateError("candidate may not overwrite pristine retail")
    expected, manifest = make_candidate(source.read_bytes())
    if output.read_bytes() != expected:
        raise CandidateError("candidate differs from deterministic exact-retail rebuild")
    try:
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateError("candidate manifest is invalid") from exc
    if stored != manifest:
        raise CandidateError("stored manifest differs from deterministic rebuilt manifest")
    _verify_structure(output.read_bytes(), manifest)
    return manifest


def write_candidate(source: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    if source == output or (output.exists() and os.path.samefile(source, output)):
        raise CandidateError("candidate may not overwrite pristine retail")
    if not registry._is_research_output(output):
        raise CandidateError("candidate output must stay under .research-output")
    if output.exists() or manifest_path.exists():
        raise CandidateError("refusing to overwrite an existing candidate or manifest")
    source_hash = sha256(source.read_bytes())
    candidate, manifest = make_candidate(source.read_bytes())
    if source_hash != manifest["source_sha256"]:
        raise CandidateError("source changed during candidate build")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if sha256(output.read_bytes()) != manifest["patched_sha256"]:
        raise CandidateError("written candidate SHA256 mismatch")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="exact supported pristine retail MRallye.exe")
    parser.add_argument("output", type=Path, help="new H.1 candidate under .research-output")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    manifest_path = args.manifest or args.output.with_name(f"{args.output.stem}.manifest.json")
    try:
        if args.verify_existing:
            manifest = verify_existing(args.source, args.output, manifest_path)
        else:
            manifest = write_candidate(args.source, args.output, manifest_path)
    except (CandidateError, hardened.CandidateError, audio.CandidateError,
            ai.CandidateError, registry.PatchError, OSError, struct.error) as exc:
        parser.exit(2, f"natural T1 candidate refused: {exc}\n")
    print(json.dumps({
        "verified_existing": args.verify_existing,
        "profile": manifest["profile"],
        "source_sha256": manifest["source_sha256"],
        "neutral_hardened_base_sha256": manifest["neutral_hardened_base_sha256"],
        "candidate_sha256": manifest["patched_sha256"],
        "size": manifest["file_size"],
        "natural_t1_source_ids": manifest["natural_t1_id26_pool"]["source_ids"],
        "fixed_results_name": manifest["results_identity"]["display_name"],
        "forced_ai_proof": manifest["forced_ai_proof"]["included"],
        "randomizer": manifest["randomizer"]["present"],
        "output": str(args.output),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
