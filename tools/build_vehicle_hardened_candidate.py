#!/usr/bin/env python3
"""Build fail-closed Mercedes candidates with neutral runtime hardening.

Profiles are intentionally separate:

* ``ordinary-hardened`` carries G.1/G.2 and the neutral Loading/Attract,
  native Dump, and ID26 AI Results-name fixes. It does not force an AI ID and
  contains no opponent randomizer.
* ``forced-id26-ai-hardened`` adds only the already-audited H.0 Car1 proof hook
  before the same hardening/Results fix.

All outputs are derived from the exact pristine retail executable. Generated
executables belong under ignored ``.research-output``.
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
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style import for tests
    from tools import build_vehicle_ai_candidate as ai
    from tools import build_vehicle_audio_candidate as audio
    from tools import patch_vehicle_registry_id26 as registry


RETAIL_SHA256 = audio.RETAIL_SHA256
RETAIL_SIZE = audio.RETAIL_SIZE
G1_SHA256 = audio.G1_SHA256
G2_PROFILE0_SHA256 = ai.G2_PROFILE0_SHA256

PROFILE_ORDINARY = "ordinary-hardened"
PROFILE_FORCED = "forced-id26-ai-hardened"
SUPPORTED_PROFILES = (PROFILE_ORDINARY, PROFILE_FORCED)

# Exact pristine retail sites rechecked against the pinned PE and Ghidra 12.1.4
# listing. The dump guards only add null checks around the stock formatter calls.
LOADING_HOOK_VA = 0x00464F69
LOADING_SKIP_VA = 0x00464F46
LOADING_ORIGINAL = bytes.fromhex("68841f6b00")

STRINGLIST_HOOK_VA = 0x0060201E
STRINGLIST_RESUME_VA = 0x00602024
STRINGLIST_CLEANUP_VA = 0x00602040
STRINGLIST_ORIGINAL = bytes.fromhex("8b7b043b7b08")
STRINGLIST_STUB_VA = 0x0068E6D0

XMLDATA_HOOK_VA = 0x00602153
XMLDATA_RESUME_VA = 0x0060215A
XMLDATA_CLEANUP_VA = 0x0060218E
XMLDATA_ORIGINAL = bytes.fromhex("8b108bc8ff520c")
XMLDATA_STUB_VA = 0x0068E6F0

# FUN_0047C840 constructs RaceResults/NameList. In the AI-name branch it
# currently sends Competitor.CarID (record +8) to localization group 0x39.
# The group has selectors 0..24, while addon CarID 26 is absent. For only that
# physical ID, use the same competitor record's DriverID (record +4) as the
# localized person-name selector. Human branches are handled before this site.
RESULTS_NAME_HOOK_VA = 0x0047CC71
RESULTS_NAME_RESUME_VA = 0x0047CC7C
RESULTS_NAME_ORIGINAL = bytes.fromhex("8b0cae8b108b4908516a39")
RESULTS_NAME_STUB_VA = 0x0068E720
RESULTS_ID26 = 26
RESULTS_DRIVER_GROUP = 0x39

TEXT_BASE_VA = 0x00401000
TEXT_RAW_SIZE = 0x0028E000
RDATA_RVA = 0x0028F000


class CandidateError(ValueError):
    """The source build, original bytes, composition, or output was not exact."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel32(source_va: int, target_va: int, opcode: int = 0xE9) -> bytes:
    displacement = target_va - (source_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise CandidateError("relative branch target is outside x86 rel32 range")
    return bytes((opcode,)) + struct.pack("<i", displacement)


def stringlist_stub_bytes(stub_va: int = STRINGLIST_STUB_VA) -> bytes:
    """Guard the NULL Broker list object, replay retail, and keep cleanup flow."""
    code = bytearray(b"\x85\xDB")  # TEST EBX,EBX
    branch_va = stub_va + len(code)
    code.extend(b"\x0F\x84" + struct.pack("<i", STRINGLIST_CLEANUP_VA - (branch_va + 6)))
    code.extend(STRINGLIST_ORIGINAL)
    code.extend(_rel32(stub_va + len(code), STRINGLIST_RESUME_VA))
    return bytes(code)


def xmldata_stub_bytes(stub_va: int = XMLDATA_STUB_VA) -> bytes:
    """Guard NULL XML data before the stock vtable dereference/call."""
    code = bytearray(b"\x85\xC0")  # TEST EAX,EAX
    branch_va = stub_va + len(code)
    code.extend(b"\x0F\x84" + struct.pack("<i", XMLDATA_CLEANUP_VA - (branch_va + 6)))
    code.extend(XMLDATA_ORIGINAL)
    code.extend(_rel32(stub_va + len(code), XMLDATA_RESUME_VA))
    return bytes(code)


def results_name_stub_bytes(stub_va: int = RESULTS_NAME_STUB_VA) -> bytes:
    """Use DriverID only for ID26 AI result text; leave physical identity intact."""
    code = bytearray()
    code.extend(bytes.fromhex("8B0CAE"))  # mov ecx,[esi+ebp*4] competitor record
    code.extend(bytes.fromhex("8B10"))    # mov edx,[eax] lookup vtable
    code.extend(bytes.fromhex("8B4908"))  # mov ecx,[ecx+8] physical CarID
    code.extend(bytes.fromhex("83F91A"))  # cmp ecx,26
    code.extend(bytes.fromhex("7506"))    # jne past DriverID substitution
    code.extend(bytes.fromhex("8B0CAE"))  # mov ecx,[esi+ebp*4]
    code.extend(bytes.fromhex("8B4904"))  # mov ecx,[ecx+4] AI DriverID
    code.extend(bytes.fromhex("516A39"))  # push selector; push localization group 0x39
    code.extend(_rel32(stub_va + len(code), RESULTS_NAME_RESUME_VA))
    return bytes(code)


def _op(name: str, category: str, va: int, original: bytes, replacement: bytes,
        purpose: str, pe: dict[str, Any]) -> dict[str, Any]:
    if len(original) != len(replacement):
        raise CandidateError(f"patch changes range size: {name}")
    offset = registry.va_to_file_offset(pe, va, len(original))
    return {
        "name": name,
        "category": category,
        "file_offset": offset,
        "virtual_address": va,
        "original_bytes": original.hex(),
        "replacement_bytes": replacement.hex(),
        "semantic_purpose": purpose,
    }


def _base_candidate(data: bytes, profile: str, source_hash: str,
                    g1_hash: str, g2_hash: str) -> tuple[bytes, dict[str, Any]]:
    if profile == PROFILE_ORDINARY:
        return audio.make_candidate(
            data,
            0,
            expected_source_sha256=source_hash,
            expected_g1_sha256=g1_hash,
        )
    if profile == PROFILE_FORCED:
        return ai.make_candidate(
            data,
            mode=ai.AI_PROOF_MODE,
            expected_source_sha256=source_hash,
            expected_g1_sha256=g1_hash,
            expected_g2_sha256=g2_hash,
        )
    raise CandidateError(f"unsupported hardened profile: {profile}")


def make_candidate(data: bytes, profile: str, *,
                   expected_source_sha256: str = RETAIL_SHA256,
                   expected_g1_sha256: str = G1_SHA256,
                   expected_g2_sha256: str = G2_PROFILE0_SHA256
                   ) -> tuple[bytes, dict[str, Any]]:
    """Compose a hardened candidate from the exact supported pristine retail."""
    if profile not in SUPPORTED_PROFILES:
        raise CandidateError(f"unsupported hardened profile: {profile}")
    source_hash = sha256(data)
    if source_hash != expected_source_sha256.lower():
        raise CandidateError(f"unsupported pristine retail SHA256: {source_hash}")
    if source_hash == RETAIL_SHA256 and len(data) != RETAIL_SIZE:
        raise CandidateError(f"unsupported pristine retail size: {len(data)}")

    base, base_manifest = _base_candidate(
        data, profile, source_hash, expected_g1_sha256, expected_g2_sha256
    )
    if profile == PROFILE_ORDINARY and sha256(base) != expected_g2_sha256.lower():
        raise CandidateError("G.2 profile-0 base candidate hash mismatch")
    if (profile == PROFILE_FORCED
            and base_manifest.get("g2_base_sha256") != expected_g2_sha256.lower()):
        raise CandidateError("forced base G.2 provenance hash mismatch")
    if profile == PROFILE_FORCED and base_manifest.get("h_research_mode") != ai.AI_PROOF_MODE:
        raise CandidateError("forced profile is not the exact H.0 proof candidate")

    pe = registry.parse_pe(data)
    text = next((section for section in pe["sections"] if section["name"] == ".text"), None)
    rdata = next((section for section in pe["sections"] if section["name"] == ".rdata"), None)
    if text is None or rdata is None or text["raw_size"] != TEXT_RAW_SIZE or rdata["rva"] != RDATA_RVA:
        raise CandidateError("retail PE text/rdata layout differs from the pinned executable")

    stubs = (
        ("null_stringlist_dump_guard_stub", STRINGLIST_STUB_VA, stringlist_stub_bytes()),
        ("null_xmldata_dump_guard_stub", XMLDATA_STUB_VA, xmldata_stub_bytes()),
        ("id26_results_driver_name_selector_stub", RESULTS_NAME_STUB_VA, results_name_stub_bytes()),
    )
    for name, va, stub in stubs:
        offset = registry.va_to_file_offset(pe, va, len(stub))
        if data[offset:offset + len(stub)] != bytes(len(stub)):
            raise CandidateError(f"{name} is not zero-filled in exact retail")
        if base[offset:offset + len(stub)] != bytes(len(stub)):
            raise CandidateError(f"{name} overlaps the G.1/G.2/base proof composition")

    operations = copy.deepcopy(base_manifest["operations"])
    size_op = next((operation for operation in operations
                    if operation["name"] == "pe_text_virtual_size"), None)
    if size_op is None:
        raise CandidateError("base manifest has no .text VirtualSize operation")
    prior_vsize = int(base_manifest["text_virtual_size"]["patched"])
    furthest_va = max(va + len(stub) for _name, va, stub in stubs)
    new_vsize = max(prior_vsize, furthest_va - TEXT_BASE_VA)
    if new_vsize > text["raw_size"] or text["rva"] + new_vsize >= rdata["rva"]:
        raise CandidateError("hardened code caves exceed .text or overlap .rdata")
    size_op["replacement_bytes"] = struct.pack("<I", new_vsize).hex()
    size_op["semantic_purpose"] = (
        "map the G.1/G.2 base, optional H.0 forced proof, null-safe native Dump guards, "
        "and ID26 Results-name selector stub"
    )

    additions = [
        _op("legacy_loading_attract_skip", "neutral-loading-hardening",
            LOADING_HOOK_VA, LOADING_ORIGINAL,
            _rel32(LOADING_HOOK_VA, LOADING_SKIP_VA),
            "skip the obsolete loading media-check false-trigger path; leave idle-menu Attract owner untouched", pe),
        _op("null_stringlist_dump_guard", "neutral-broker-dump-hardening",
            STRINGLIST_HOOK_VA, STRINGLIST_ORIGINAL,
            _rel32(STRINGLIST_HOOK_VA, STRINGLIST_STUB_VA) + b"\x90",
            "route StringList formatting through a NULL-object check before replaying stock iteration", pe),
        _op("null_xmldata_dump_guard", "neutral-broker-dump-hardening",
            XMLDATA_HOOK_VA, XMLDATA_ORIGINAL,
            _rel32(XMLDATA_HOOK_VA, XMLDATA_STUB_VA) + b"\x90\x90",
            "route XmlData formatting through a NULL-object check before replaying stock vtable call", pe),
        _op("id26_results_driver_name_selector", "id26-results-presentation",
            RESULTS_NAME_HOOK_VA, RESULTS_NAME_ORIGINAL,
            _rel32(RESULTS_NAME_HOOK_VA, RESULTS_NAME_STUB_VA) + b"\x90" * 6,
            "for physical CarID 26 only, use the participant DriverID as group-0x39 AI person-name selector", pe),
    ]
    for name, va, stub in stubs:
        additions.append(_op(
            name,
            "neutral-broker-dump-hardening" if "dump" in name else "id26-results-presentation",
            va,
            bytes(len(stub)),
            stub,
            "bounded executable helper with original control-flow continuations",
            pe,
        ))
    operations.extend(additions)
    operations.sort(key=lambda operation: operation["file_offset"])
    audio._validate_operations(data, operations)

    candidate_bytes = bytearray(data)
    for operation in operations:
        start = operation["file_offset"]
        replacement = bytes.fromhex(operation["replacement_bytes"])
        candidate_bytes[start:start + len(replacement)] = replacement
    candidate = bytes(candidate_bytes)

    # Revert every declared patch in reverse order to prove the manifest is a
    # complete, non-overlapping description of the output.
    inverse = bytearray(candidate)
    for operation in reversed(operations):
        start = operation["file_offset"]
        original = bytes.fromhex(operation["original_bytes"])
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if inverse[start:start + len(replacement)] != replacement:
            raise CandidateError(f"post-patch bytes differ at {operation['name']}")
        inverse[start:start + len(original)] = original
    if bytes(inverse) != data:
        raise CandidateError("declared inverse does not restore exact pristine input")

    base_sha256 = sha256(base)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R5V-H.0.1 hardened research executable composition",
        "profile": profile,
        "source_sha256": source_hash,
        "source_size": len(data),
        "g1_base_sha256": base_manifest.get("g1_base_sha256", base_manifest.get("patched_sha256")),
        "g2_base_sha256": base_manifest.get("patched_sha256") if profile == PROFILE_ORDINARY else base_manifest.get("g2_base_sha256"),
        "pre_hardening_base_sha256": base_sha256,
        "patched_sha256": sha256(candidate),
        "file_size": len(candidate),
        "base_manifest": base_manifest,
        "text_virtual_size": {
            "original": base_manifest["text_virtual_size"]["original"],
            "pre_hardening": prior_vsize,
            "patched": new_vsize,
            "highest_cave_end_exclusive_va": f"0x{furthest_va:08X}",
            "rdata_rva": f"0x{rdata['rva']:X}",
            "non_overlap_proven": True,
        },
        "operations": operations,
        "operation_counts_by_category": dict(Counter(op["category"] for op in operations)),
        "randomizer": {
            "present": False,
            "stock_mixed_diverse_chooser_changed": False,
            "source_note": "The ordinary profile contains no forced AI hook; the forced profile contains only the audited H.0 Car1 proof, not the R-AI1.2 randomizer.",
        },
        "hardening": {
            "loading_false_attract_path_neutralized": True,
            "idle_menu_attract_owner_changed": False,
            "null_stringlist_dump_guard": True,
            "null_xmldata_dump_guard": True,
        },
        "results_identity": {
            "target_physical_car_id": RESULTS_ID26,
            "localization_group": RESULTS_DRIVER_GROUP,
            "selector_for_id26_ai": "participant DriverID at competitor record +4",
            "other_ai_selector": "physical CarID at competitor record +8, unchanged",
            "human_name_branches": "handled before the patched AI lookup and unchanged",
            "physical_car_id_written": False,
            "status": "STATIC_FIX_READY_FOR_HUMAN_RESULTS_AND_DUMP_RETEST",
        },
        "runtime_validation": "candidate composition only; neutral hardening and Results identity require human runtime validation",
    }
    if profile == PROFILE_FORCED:
        manifest["forced_ai_proof"] = {
            "included": True,
            "target": "Car1",
            "requested_class": 0,
            "substituted_car_id": 26,
            "participant_count_changed": False,
            "randomizer_included": False,
        }
    else:
        manifest["forced_ai_proof"] = {"included": False}
    _verify_structure(candidate, manifest)
    return candidate, manifest


def _verify_structure(candidate: bytes, manifest: dict[str, Any]) -> None:
    if sha256(candidate) != manifest.get("patched_sha256"):
        raise CandidateError("candidate SHA256 differs from its manifest")
    if len(candidate) != manifest.get("file_size"):
        raise CandidateError("candidate size differs from its manifest")
    if manifest.get("profile") not in SUPPORTED_PROFILES:
        raise CandidateError("unsupported profile in candidate manifest")
    if manifest.get("randomizer", {}).get("present") is not False:
        raise CandidateError("candidate manifest enables an opponent randomizer")
    if manifest.get("results_identity", {}).get("physical_car_id_written") is not False:
        raise CandidateError("Results presentation patch may not change physical CarID")
    for operation in manifest.get("operations", []):
        offset = operation["file_offset"]
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if candidate[offset:offset + len(replacement)] != replacement:
            raise CandidateError(f"manifested output range mismatch: {operation['name']}")
    expected_caves = {
        STRINGLIST_STUB_VA: stringlist_stub_bytes(),
        XMLDATA_STUB_VA: xmldata_stub_bytes(),
        RESULTS_NAME_STUB_VA: results_name_stub_bytes(),
    }
    pe = ai._parse_candidate_pe(candidate)
    for va, stub in expected_caves.items():
        offset = registry.va_to_file_offset(pe, va, len(stub))
        if candidate[offset:offset + len(stub)] != stub:
            raise CandidateError(f"candidate helper bytes differ at 0x{va:08X}")
    text = next(section for section in pe["sections"] if section["name"] == ".text")
    rdata = next(section for section in pe["sections"] if section["name"] == ".rdata")
    if text["virtual_size"] != manifest["text_virtual_size"]["patched"]:
        raise CandidateError("candidate .text VirtualSize differs from manifest")
    if text["rva"] + text["virtual_size"] >= rdata["rva"]:
        raise CandidateError("candidate .text overlaps .rdata")


def verify_existing(source: Path, output: Path, manifest_path: Path,
                    profile: str) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if source == output or os.path.samefile(source, output):
        raise CandidateError("candidate may not overwrite pristine retail")
    expected, manifest = make_candidate(source.read_bytes(), profile)
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


def write_candidate(source: Path, output: Path, manifest_path: Path,
                    profile: str) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    manifest_path = manifest_path.resolve(strict=False)
    if source == output or (output.exists() and os.path.samefile(source, output)):
        raise CandidateError("candidate may not overwrite pristine retail")
    if not registry._is_research_output(output):
        raise CandidateError("candidate output must stay under .research-output")
    if output.exists() or manifest_path.exists():
        raise CandidateError("refusing to overwrite an existing candidate or manifest")
    if output == manifest_path or str(output).casefold() == str(manifest_path).casefold():
        raise CandidateError("candidate and manifest paths must be distinct")
    source_before = sha256(source.read_bytes())
    candidate, manifest = make_candidate(source.read_bytes(), profile)
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
    parser.add_argument("output", type=Path, help="new candidate under .research-output")
    parser.add_argument("--profile", choices=SUPPORTED_PROFILES, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    manifest_path = args.manifest or args.output.with_name(f"{args.output.stem}.manifest.json")
    try:
        if args.verify_existing:
            manifest = verify_existing(args.source, args.output, manifest_path, args.profile)
        else:
            manifest = write_candidate(args.source, args.output, manifest_path, args.profile)
    except (CandidateError, audio.CandidateError, ai.CandidateError,
            registry.PatchError, OSError, struct.error) as exc:
        parser.exit(2, f"hardened vehicle candidate refused: {exc}\n")
    print(json.dumps({
        "verified_existing": args.verify_existing,
        "profile": manifest["profile"],
        "source_sha256": manifest["source_sha256"],
        "candidate_sha256": manifest["patched_sha256"],
        "size": manifest["file_size"],
        "forced_ai_proof": manifest["forced_ai_proof"]["included"],
        "randomizer": manifest["randomizer"]["present"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
