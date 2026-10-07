#!/usr/bin/env python3
"""Build the fail-closed R5V-H.2 mode-aware physical-ID26 AI candidate.

The build composes the frozen, runtime-confirmed H.1 candidate from exact
pristine retail, then extends only the existing T1 source-pool exits used by
the shared Rallye Cup/Invitation generator and the new Master Rallye roster
generator. Existing native exclusions, class selection, shuffle, driver
selection, roster storage, save/load, and stage reuse remain in place.
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
    import build_vehicle_audio_candidate as audio
    import build_vehicle_natural_t1_candidate as natural
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style import for tests
    from tools import build_vehicle_ai_candidate as ai
    from tools import build_vehicle_audio_candidate as audio
    from tools import build_vehicle_natural_t1_candidate as natural
    from tools import patch_vehicle_registry_id26 as registry


RETAIL_SHA256 = audio.RETAIL_SHA256
RETAIL_SIZE = audio.RETAIL_SIZE
H1_SHA256 = "e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a"
H1_MANIFEST_LF_SHA256 = "13305165f5683ee6546460745b82b7d9cca4244263ded119b59e0fd0f3b4f587"
PROFILE = "mode-aware-natural-t1-id26"
TEXT_BASE_VA = natural.TEXT_BASE_VA

T1_STOCK_IDS = tuple(range(7))
T1_ADDON_ID = 26
T1_SOURCE_IDS = (*T1_STOCK_IDS, T1_ADDON_ID)
T2_SOURCE_IDS = tuple(range(7, 14))
T3_BASE_IDS = tuple(range(14, 21))

# FUN_0045abc0: shared Cup/Invitation dynamic pool. T1 exits after the stock
# exclusion-and-append loop; the body starts at 0x0045ACEF and common exit is
# 0x0045AE66. Retail and H.1 both use this five-byte exit instruction.
CUP_T1_HOOK_VA = 0x0045AD14
CUP_T1_HOOK_ORIGINAL = bytes.fromhex("E94D010000")
CUP_T1_BOUND_VA = 0x0045AD0E
CUP_T1_REENTRY_VA = 0x0045ACEF
CUP_T1_COMMON_EXIT_VA = 0x0045AE66
CUP_T1_REENTRY_BYTES = bytes.fromhex(
    "8B4C24288D84248C000000506A01518D4C242C89B42498000000"
)
CUP_T1_BOUND_BYTES = bytes.fromhex("4683FE077CCEE94D010000")
CUP_T1_STUB_VA = 0x0068E7A0

# FUN_00451dd0: new Master Rallye roster pool. Its persisted load/resume path
# is FUN_00452FE0 and does not call this generator. The native T1 append body
# performs the same participant-CarID exclusions before inserting the ID.
MASTER_T1_HOOK_VA = 0x00451ED9
MASTER_T1_HOOK_ORIGINAL = bytes.fromhex("E94D010000")
MASTER_T1_BOUND_VA = 0x00451ED3
MASTER_T1_REENTRY_VA = 0x00451EB4
MASTER_T1_COMMON_EXIT_VA = 0x0045202B
MASTER_T1_REENTRY_BYTES = bytes.fromhex(
    "8B4C242C8D842490000000506A01518D4C243089B4249C000000"
)
MASTER_T1_BOUND_BYTES = bytes.fromhex("4683FE077CCEE94D010000")
MASTER_T1_STUB_VA = 0x0068E7C0


class CandidateError(ValueError):
    """Raised when the exact H.1 base or H.2 patch layout does not match."""


def dynamic_t1_mode_pools() -> dict[str, dict[str, Any]]:
    """Return the machine-readable scope of H.2's native dynamic pool owners."""
    return {
        "quickrace": {
            "source_ids": list(T1_SOURCE_IDS),
            "owner_va": "0x00458090",
            "status": "PRESERVED_FROM_H1_CONFIRMED_BY_RUNTIME",
        },
        "rallye_cup": {
            "source_ids": list(T1_SOURCE_IDS),
            "owner_va": "0x0045ABC0",
            "new_roster_entry_va": "0x0045BE10",
            "status": "STATIC_PATCH_READY_FOR_HUMAN_RUNTIME",
        },
        "invitation": {
            "source_ids": list(T1_SOURCE_IDS),
            "owner_va": "0x0045ABC0",
            "shared_mode_dispatch_race_type": 8,
            "status": "STATIC_PATCH_READY_FOR_HUMAN_RUNTIME",
        },
        "master_rallye": {
            "source_ids": list(T1_SOURCE_IDS),
            "new_roster_owner_va": "0x00452590",
            "pool_owner_va": "0x00451DD0",
            "status": "STATIC_PATCH_READY_FOR_HUMAN_RUNTIME",
        },
    }


def eligibility_lifecycle_manifest() -> dict[str, bool]:
    """Describe the creation-only boundary; native roster persistence is untouched."""
    return {
        "id26_appended_only_at_new_dynamic_roster_generation": True,
        "native_cup_invitation_roster_storage_changed": False,
        "masterrallye_car_n_storage_changed": False,
        "master_save_or_load_changed": False,
        "existing_rosters_mutated": False,
        "stage_reroll_added": False,
        "class_randomization_added": False,
    }


def id26_identity_manifest() -> dict[str, Any]:
    """Keep physical vehicle, native driver, Results display, and audio separate."""
    return {
        "physical_car_id": 26,
        "class": 0,
        "native_driver_id_selection_changed": False,
        "results_display": "JEAN-PIERRE STRUGO",
        "audio_profile": 0,
        "runtime_car_id_aliased": False,
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel32(source_va: int, target_va: int, opcode: int = 0xE9) -> bytes:
    displacement = target_va - (source_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise CandidateError("relative branch target is outside x86 rel32 range")
    return bytes((opcode,)) + struct.pack("<i", displacement)


def t1_append_stub_bytes(stub_va: int, reentry_va: int,
                         common_exit_va: int) -> bytes:
    """Append physical ID26 through a native class-0 exclusion body once."""
    code = bytearray(bytes.fromhex("83FE1B740A"))  # cmp esi,27; je restore
    code.extend(b"\xBE" + struct.pack("<I", T1_ADDON_ID))
    code.extend(_rel32(stub_va + len(code), reentry_va))
    code.extend(b"\xBE" + struct.pack("<I", 7))  # restore stock end index
    code.extend(_rel32(stub_va + len(code), common_exit_va))
    return bytes(code)


def pool_for_mode(mode: str, class_code: int,
                  excluded_ids: tuple[int, ...] | list[int] = ()) -> list[int]:
    """Model the audited source vectors and native physical-ID exclusions."""
    if mode not in {"quickrace", "rallye_cup", "invitation", "master_rallye"}:
        raise CandidateError(f"mode has no dynamic vehicle pool in H.2: {mode}")
    if len(excluded_ids) > 2 or any(type(value) is not int for value in excluded_ids):
        raise CandidateError("native roster pool accepts at most two integer exclusions")
    if class_code == 0:
        source = list(T1_SOURCE_IDS)
    elif class_code == 1:
        source = list(T2_SOURCE_IDS)
    elif class_code in (2, 4):
        source = list(T3_BASE_IDS)
    else:
        raise CandidateError(f"unsupported stock vehicle class selector: {class_code}")
    excluded = {value for value in excluded_ids if value >= 0}
    result = [vehicle_id for vehicle_id in source if vehicle_id not in excluded]
    if class_code == 0 and 7 in result:
        raise CandidateError("physical ID7 is T2 and cannot enter the T1 pool")
    return result


def _operation(name: str, pe: dict[str, Any], va: int,
               original: bytes, replacement: bytes, purpose: str) -> dict[str, Any]:
    if len(original) != len(replacement):
        raise CandidateError(f"patch operation changes range size: {name}")
    return {
        "name": name,
        "category": "mode-aware-dynamic-t1-pool",
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
        replacement = bytes.fromhex(operation["replacement_bytes"])
        result[start:start + len(replacement)] = replacement
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
        raise CandidateError("declared H.2 inverse does not restore exact retail input")
    return candidate


def make_candidate(data: bytes) -> tuple[bytes, dict[str, Any]]:
    """Build H.2 from exact pristine retail through the frozen H.1 composition."""
    source_hash = sha256(data)
    if source_hash != RETAIL_SHA256:
        raise CandidateError(f"unsupported pristine retail SHA256: {source_hash}")
    if len(data) != RETAIL_SIZE:
        raise CandidateError(f"unsupported pristine retail size: {len(data)}")

    h1_candidate, h1_manifest = natural.make_candidate(data)
    if sha256(h1_candidate) != H1_SHA256:
        raise CandidateError("frozen H.1 candidate bytes differ from the runtime-confirmed build")
    h1_manifest_bytes = (json.dumps(h1_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if sha256(h1_manifest_bytes) != H1_MANIFEST_LF_SHA256:
        raise CandidateError("frozen H.1 manifest differs from its pinned evidence")

    pe = registry.parse_pe(data)
    checks = (
        (CUP_T1_HOOK_VA, CUP_T1_HOOK_ORIGINAL, "Cup/Invitation T1 pool exit"),
        (CUP_T1_BOUND_VA, CUP_T1_BOUND_BYTES,
         "Cup/Invitation T1 loop bound and exit"),
        (CUP_T1_REENTRY_VA, CUP_T1_REENTRY_BYTES, "Cup/Invitation native T1 exclusion body"),
        (MASTER_T1_HOOK_VA, MASTER_T1_HOOK_ORIGINAL, "Master Rallye new-roster T1 pool exit"),
        (MASTER_T1_BOUND_VA, MASTER_T1_BOUND_BYTES,
         "Master Rallye T1 loop bound and exit"),
        (MASTER_T1_REENTRY_VA, MASTER_T1_REENTRY_BYTES, "Master Rallye native T1 exclusion body"),
    )
    for va, expected, purpose in checks:
        if _read_va(data, pe, va, len(expected)) != expected:
            raise CandidateError(f"{purpose} differs from exact retail at 0x{va:08X}")

    cup_stub = t1_append_stub_bytes(CUP_T1_STUB_VA, CUP_T1_REENTRY_VA,
                                    CUP_T1_COMMON_EXIT_VA)
    master_stub = t1_append_stub_bytes(MASTER_T1_STUB_VA, MASTER_T1_REENTRY_VA,
                                       MASTER_T1_COMMON_EXIT_VA)
    for label, va, code in (("Cup/Invitation", CUP_T1_STUB_VA, cup_stub),
                            ("Master Rallye", MASTER_T1_STUB_VA, master_stub)):
        offset = registry.va_to_file_offset(pe, va, len(code))
        if data[offset:offset + len(code)] != bytes(len(code)):
            raise CandidateError(f"{label} H.2 cave is not zero-filled in retail")
        if h1_candidate[offset:offset + len(code)] != bytes(len(code)):
            raise CandidateError(f"{label} H.2 cave overlaps the frozen H.1 composition")

    operations = copy.deepcopy(h1_manifest["operations"])
    size_op = next((op for op in operations if op["name"] == "pe_text_virtual_size"), None)
    if size_op is None:
        raise CandidateError("frozen H.1 manifest lacks its PE text-size operation")
    text = next((section for section in pe["sections"] if section["name"] == ".text"), None)
    rdata = next((section for section in pe["sections"] if section["name"] == ".rdata"), None)
    if text is None or rdata is None or text["raw_size"] != natural.hardened.TEXT_RAW_SIZE:
        raise CandidateError("exact retail .text/.rdata layout differs from pinned executable")

    new_ops = [
        _operation(
            "rallyecup_invitation_t1_pool_exit_hook", pe, CUP_T1_HOOK_VA,
            CUP_T1_HOOK_ORIGINAL, _rel32(CUP_T1_HOOK_VA, CUP_T1_STUB_VA),
            "extend the shared dynamic Cup/Invitation T1 source pool without changing roster creation or persistence",
        ),
        _operation(
            "rallyecup_invitation_t1_id26_append_stub", pe, CUP_T1_STUB_VA,
            bytes(len(cup_stub)), cup_stub,
            "re-enter the stock physical-ID exclusion and append body once for ID26, restore ESI=7, then exit the class arm",
        ),
        _operation(
            "master_rallye_new_roster_t1_pool_exit_hook", pe, MASTER_T1_HOOK_VA,
            MASTER_T1_HOOK_ORIGINAL, _rel32(MASTER_T1_HOOK_VA, MASTER_T1_STUB_VA),
            "extend only the new Master Rallye T1 roster source; saved-roster load/resume remains unmodified",
        ),
        _operation(
            "master_rallye_new_roster_t1_id26_append_stub", pe, MASTER_T1_STUB_VA,
            bytes(len(master_stub)), master_stub,
            "re-enter the stock physical-ID exclusion and append body once for ID26, restore ESI=7, then exit the class arm",
        ),
    ]
    operations.extend(new_ops)

    highest_end = max(
        CUP_T1_STUB_VA + len(cup_stub),
        MASTER_T1_STUB_VA + len(master_stub),
        int(h1_manifest["text_virtual_size"]["highest_cave_end_exclusive_va"], 16),
    )
    patched_vsize = max(int(h1_manifest["text_virtual_size"]["patched"]),
                        highest_end - TEXT_BASE_VA)
    if patched_vsize > text["raw_size"] or text["rva"] + patched_vsize >= rdata["rva"]:
        raise CandidateError("H.2 payload extends past .text or overlaps .rdata")
    size_op["replacement_bytes"] = struct.pack("<I", patched_vsize).hex()
    size_op["semantic_purpose"] = (
        "map the frozen H.1 runtime implementation plus shared Cup/Invitation and new Master Rallye T1 append shims"
    )
    operations.sort(key=lambda op: op["file_offset"])
    candidate = _apply_operations(data, operations)

    publication = registry.va_to_file_offset(pe, ai.AI_PUBLICATION_HOOK_VA,
                                             len(ai.EXPECTED_PUBLICATION_BYTES))
    if candidate[publication:publication + len(ai.EXPECTED_PUBLICATION_BYTES)] != ai.EXPECTED_PUBLICATION_BYTES:
        raise CandidateError("H.2 must preserve the H.1 native CarID publication path")
    forced = registry.va_to_file_offset(pe, ai.AI_PROOF_STUB_VA, 64)
    if candidate[forced:forced + 64] != bytes(64):
        raise CandidateError("H.2 candidate unexpectedly contains the forced H.0 proof")

    manifest = copy.deepcopy(h1_manifest)
    manifest.update({
        "schema_version": 1,
        "phase": "R5V-H.2 mode-aware addon AI eligibility",
        "profile": PROFILE,
        "patched_sha256": sha256(candidate),
        "file_size": len(candidate),
        "parent_candidate": {
            "phase": "R5V-H.1 natural T1 AI pool inclusion",
            "sha256": H1_SHA256,
            "manifest_sha256_lf_normalized": H1_MANIFEST_LF_SHA256,
            "runtime_status": "CONFIRMED_BY_RUNTIME",
        },
        "text_virtual_size": {
            "original": h1_manifest["text_virtual_size"]["original"],
            "h1_patched": h1_manifest["text_virtual_size"]["patched"],
            "patched": patched_vsize,
            "highest_cave_end_exclusive_va": f"0x{highest_end:08X}",
            "rdata_rva": f"0x{rdata['rva']:X}",
            "non_overlap_proven": True,
        },
        "operations": operations,
        "operation_counts_by_category": dict(Counter(op["category"] for op in operations)),
        "dynamic_t1_mode_pools": dynamic_t1_mode_pools(),
        "eligibility_lifecycle": eligibility_lifecycle_manifest(),
        "id26_identity": id26_identity_manifest(),
        "challenge_auto_injection": False,
        "practice_ai_pool": "NOT_APPLICABLE_NO_SEPARATE_STOCK_AI_ROSTER_OWNER_FOUND",
        "participant_count_changed": False,
        "randomizer": {"present": False},
        "status": "READY_FOR_HUMAN_RUNTIME",
    })
    _verify_structure(candidate, manifest)
    return candidate, manifest


def _verify_structure(candidate: bytes, manifest: dict[str, Any]) -> None:
    if sha256(candidate) != manifest.get("patched_sha256"):
        raise CandidateError("candidate SHA256 differs from manifest")
    if manifest.get("profile") != PROFILE or len(candidate) != RETAIL_SIZE:
        raise CandidateError("candidate profile or size differs from the exact retail family")
    if manifest.get("participant_count_changed") is not False:
        raise CandidateError("H.2 must not change participant count")
    if manifest.get("randomizer", {}).get("present") is not False:
        raise CandidateError("H.2 must not include the general randomizer")
    if manifest.get("challenge_auto_injection") is not False:
        raise CandidateError("authored Challenge rosters must remain unchanged")
    if manifest.get("id26_identity", {}).get("physical_car_id") != 26:
        raise CandidateError("H.2 must preserve physical ID26")

    pe = ai._parse_candidate_pe(candidate)
    cup_stub = t1_append_stub_bytes(CUP_T1_STUB_VA, CUP_T1_REENTRY_VA, CUP_T1_COMMON_EXIT_VA)
    master_stub = t1_append_stub_bytes(MASTER_T1_STUB_VA, MASTER_T1_REENTRY_VA,
                                       MASTER_T1_COMMON_EXIT_VA)
    for va, expected in ((CUP_T1_STUB_VA, cup_stub), (MASTER_T1_STUB_VA, master_stub)):
        offset = registry.va_to_file_offset(pe, va, len(expected))
        if candidate[offset:offset + len(expected)] != expected:
            raise CandidateError(f"mode-specific append stub differs at 0x{va:08X}")
    for va, target in ((CUP_T1_HOOK_VA, CUP_T1_STUB_VA),
                       (MASTER_T1_HOOK_VA, MASTER_T1_STUB_VA)):
        offset = registry.va_to_file_offset(pe, va, 5)
        if candidate[offset:offset + 5] != _rel32(va, target):
            raise CandidateError(f"mode-specific T1 exit does not target its stub at 0x{va:08X}")

    # H.1 remains represented by the pinned parent operation set, its T1 and
    # Results hooks, and the exact helper bytes generated by H.1's builder.
    h1_ranges = (
        (natural.T1_EXIT_HOOK_VA, _rel32(natural.T1_EXIT_HOOK_VA, natural.T1_POOL_STUB_VA)),
        (natural.RESULTS_NAME_HOOK_VA,
         _rel32(natural.RESULTS_NAME_HOOK_VA, natural.RESULTS_NAME_STUB_VA)),
        (natural.T1_POOL_STUB_VA, natural.natural_t1_exit_stub_bytes()),
        (natural.RESULTS_NAME_STUB_VA, natural.results_name_stub_bytes()),
    )
    for va, expected in h1_ranges:
        offset = registry.va_to_file_offset(pe, va, len(expected))
        if candidate[offset:offset + len(expected)] != expected:
            raise CandidateError(f"H.1 closed behavior changed at 0x{va:08X}")
    publication = registry.va_to_file_offset(pe, ai.AI_PUBLICATION_HOOK_VA,
                                             len(ai.EXPECTED_PUBLICATION_BYTES))
    if candidate[publication:publication + 5] != ai.EXPECTED_PUBLICATION_BYTES:
        raise CandidateError("native CarID/CarClass/DriverID publication must remain H.1 stock")
    forced = registry.va_to_file_offset(pe, ai.AI_PROOF_STUB_VA, 64)
    if candidate[forced:forced + 64] != bytes(64):
        raise CandidateError("forced H.0 proof stub must remain absent")
    text = next(section for section in pe["sections"] if section["name"] == ".text")
    rdata = next(section for section in pe["sections"] if section["name"] == ".rdata")
    if text["virtual_size"] != manifest["text_virtual_size"]["patched"]:
        raise CandidateError("candidate .text VirtualSize differs from manifest")
    if text["rva"] + text["virtual_size"] >= rdata["rva"]:
        raise CandidateError("candidate .text overlaps .rdata")


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
    parser.add_argument("output", type=Path, help="new H.2 candidate under .research-output")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    manifest_path = args.manifest or args.output.with_name(f"{args.output.stem}.manifest.json")
    try:
        manifest = (verify_existing(args.source, args.output, manifest_path) if args.verify_existing
                    else write_candidate(args.source, args.output, manifest_path))
    except (CandidateError, natural.CandidateError, audio.CandidateError,
            ai.CandidateError, registry.PatchError, OSError, struct.error) as exc:
        parser.exit(2, f"mode-aware candidate refused: {exc}\n")
    print(json.dumps({
        "verified_existing": args.verify_existing,
        "profile": manifest["profile"],
        "source_sha256": manifest["source_sha256"],
        "h1_parent_sha256": manifest["parent_candidate"]["sha256"],
        "candidate_sha256": manifest["patched_sha256"],
        "size": manifest["file_size"],
        "modes": ["Quick Race (preserved)", "Rallye Cup", "Invitation", "Master Rallye"],
        "participant_count_changed": manifest["participant_count_changed"],
        "randomizer": manifest["randomizer"]["present"],
        "output": str(args.output),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
