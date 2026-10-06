#!/usr/bin/env python3
"""Build exact-hash R5V-G.2 ID26 audio-selector research candidates.

The builder starts from pristine retail, reproduces the committed G.1 Mercedes
profile, then redirects only the CarID value consumed by the per-participant
audio constructor. Physical participant and vehicle identity remain native.
Generated executables belong under ignored research-output directories.
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
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style import for tests
    from tools import patch_vehicle_registry_id26 as registry


RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
G1_SHA256 = "722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7"
TEXT_VIRTUAL_SIZE_ORIGINAL = 0x0028D294
ID26_AUDIO_LOOKUP_CALL_VA = 0x00408FB4
RACE_CAR_ID_GETTER_VA = 0x004AC660
ID26_PHYSICAL_ID = 26
ID26_PROFILE_CODE_CAVE_VA = registry.STUB_VA

DONORS: dict[int, dict[str, Any]] = {
    0: {
        "vehicle": "Landcruiser",
        "class": "T1",
        "class_local_index": 0,
        "sample_family": "vehicles/rev9",
        "primary_sample_scalar_bits": "3fc00000",
        "tuning_field_0x14_bits": "3f733333",
        "curve_table_group": "A",
        "selection_basis": "ordinary stock profile; historical demo Mercedes ID2 shares this constructor branch",
    },
    19: {
        "vehicle": "Mattserati",
        "class": "T3",
        "class_local_index": 5,
        "sample_family": "vehicles/engine9",
        "primary_sample_scalar_bits": "3fc7ae14",
        "tuning_field_0x14_bits": "3f8147ae",
        "curve_table_group": "A",
        "selection_basis": "human-reported bass-heavy buggy oracle; distinct raw tuning from Simmbugghini",
    },
}


class CandidateError(ValueError):
    """The build identity, original bytes, or patch layout was not exact."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _call_rel32(source_va: int, target_va: int) -> bytes:
    displacement = target_va - (source_va + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise CandidateError("audio wrapper is outside CALL rel32 range")
    return b"\xE8" + struct.pack("<i", displacement)


def _file_offset(pe: dict[str, Any], va: int, length: int) -> int:
    try:
        return registry.va_to_file_offset(pe, va, length)
    except Exception as exc:
        raise CandidateError(f"VA 0x{va:08X} is not file-backed: {exc}") from exc


def _operation(name: str, category: str, offset: int, original: bytes,
               replacement: bytes, purpose: str, *, va: int | None = None) -> dict[str, Any]:
    if len(original) != len(replacement):
        raise CandidateError(f"non-size-preserving patch operation: {name}")
    result: dict[str, Any] = {
        "name": name,
        "category": category,
        "file_offset": offset,
        "original_bytes": original.hex(),
        "replacement_bytes": replacement.hex(),
        "semantic_purpose": purpose,
    }
    if va is not None:
        result["virtual_address"] = va
    return result


def audio_wrapper_bytes(donor_id: int, wrapper_va: int) -> bytes:
    """Forward the original slot lookup; substitute only returned CarID 26."""
    if donor_id not in DONORS:
        raise CandidateError(f"unsupported donor CarID: {donor_id}")
    # push [esp+4]; call original thiscall getter; cmp eax,26; jne over mov;
    # mov eax,donor; ret 4. ECX and all non-EAX registers remain untouched.
    body = bytearray(b"\xFF\x74\x24\x04")
    body.extend(_call_rel32(wrapper_va + len(body), RACE_CAR_ID_GETTER_VA))
    body.extend(b"\x83\xF8\x1A\x75\x05\xB8")
    body.extend(struct.pack("<I", donor_id))
    body.extend(b"\xC2\x04\x00")
    if len(body) != 22:
        raise CandidateError("unexpected audio wrapper size")
    return bytes(body)


def resolve_audio_profile_id(car_id: int, donor_id: int) -> int:
    """Model the bounded selector policy for deterministic synthetic tests."""
    if donor_id not in DONORS:
        raise CandidateError(f"unsupported donor CarID: {donor_id}")
    return donor_id if car_id == ID26_PHYSICAL_ID else car_id


def _validate_operations(source: bytes, operations: list[dict[str, Any]]) -> None:
    prior_end = -1
    for operation in sorted(operations, key=lambda item: item["file_offset"]):
        start = operation["file_offset"]
        original = bytes.fromhex(operation["original_bytes"])
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if start < prior_end or start < 0 or start + len(original) > len(source):
            raise CandidateError(f"overlapping or out-of-bounds operation: {operation['name']}")
        if len(original) != len(replacement):
            raise CandidateError(f"size-changing operation: {operation['name']}")
        if source[start:start + len(original)] != original:
            raise CandidateError(f"original byte check failed: {operation['name']}")
        prior_end = start + len(original)


def make_candidate(data: bytes, donor_id: int, *,
                   expected_source_sha256: str = RETAIL_SHA256,
                   expected_g1_sha256: str = G1_SHA256) -> tuple[bytes, dict[str, Any]]:
    source_digest = sha256(data)
    if source_digest != expected_source_sha256.lower():
        raise CandidateError(f"unsupported pristine retail SHA256: {source_digest}")
    if donor_id not in DONORS:
        raise CandidateError(f"unsupported donor CarID: {donor_id}")

    g1_base, g1_manifest = registry.make_candidate(
        data,
        expected_sha256=source_digest,
        id26_profile=registry.ID26_MERCEDES_G1_STOCK_UNLOCK,
    )
    g1_digest = sha256(g1_base)
    if g1_digest != expected_g1_sha256.lower():
        raise CandidateError(f"G.1 reproduction hash mismatch: {g1_digest}")

    # The existing retail parser intentionally rejects any non-pristine text
    # VirtualSize. Reuse its exact source-layout parse, then carry forward the
    # separately hash-verified G.1 section size for this append-only extension.
    pe = registry.parse_pe(data)
    text = next((section for section in pe["sections"] if section["name"] == ".text"), None)
    rdata = next((section for section in pe["sections"] if section["name"] == ".rdata"), None)
    if text is None or rdata is None:
        raise CandidateError("expected .text and .rdata sections are required")
    payload_op = next((op for op in g1_manifest["operations"]
                       if op["name"] == "id26_code_cave_payload"), None)
    size_op = next((op for op in g1_manifest["operations"]
                    if op["name"] == "pe_text_virtual_size"), None)
    if payload_op is None or size_op is None:
        raise CandidateError("G.1 manifest lacks the expected code cave or PE size operation")
    text["virtual_size"] = int(g1_manifest["text_virtual_size"]["patched"])

    g1_payload = bytes.fromhex(payload_op["replacement_bytes"])
    wrapper_va = ID26_PROFILE_CODE_CAVE_VA + len(g1_payload)
    wrapper = audio_wrapper_bytes(donor_id, wrapper_va)
    hook_offset = _file_offset(pe, ID26_AUDIO_LOOKUP_CALL_VA, 5)
    expected_getter_call = _call_rel32(ID26_AUDIO_LOOKUP_CALL_VA, RACE_CAR_ID_GETTER_VA)
    actual_call = g1_base[hook_offset:hook_offset + 5]
    if actual_call != expected_getter_call:
        raise CandidateError(
            f"audio lookup call bytes changed: expected {expected_getter_call.hex()}, got {actual_call.hex()}"
        )

    wrapper_offset = _file_offset(pe, wrapper_va, len(wrapper))
    if g1_base[wrapper_offset:wrapper_offset + len(wrapper)] != bytes(len(wrapper)):
        raise CandidateError("G.1-adjacent audio wrapper range is not zero-filled")
    text_base_va = registry.IMAGE_BASE + text["rva"]
    relative_end = wrapper_va - text_base_va + len(wrapper)
    new_text_virtual_size = max(text["virtual_size"], relative_end)
    if relative_end > text["raw_size"]:
        raise CandidateError("audio wrapper extends past .text raw data")
    if text["rva"] + new_text_virtual_size >= rdata["rva"]:
        raise CandidateError("expanded .text virtual range would overlap .rdata")

    operations = copy.deepcopy(g1_manifest["operations"])
    updated_size_op = next(op for op in operations if op["name"] == "pe_text_virtual_size")
    if bytes.fromhex(updated_size_op["replacement_bytes"]) != struct.pack("<I", text["virtual_size"]):
        raise CandidateError("G.1 .text size bytes do not match parsed PE section")
    updated_size_op["replacement_bytes"] = struct.pack("<I", new_text_virtual_size).hex()
    updated_size_op["semantic_purpose"] = (
        "map the G.1 code cave plus the bounded ID26 audio-profile selector wrapper"
    )

    operations.append(_operation(
        "id26_audio_profile_lookup_call", "audio-profile-selection",
        hook_offset, expected_getter_call,
        _call_rel32(ID26_AUDIO_LOOKUP_CALL_VA, wrapper_va),
        ("intercept only the CarID value returned to gaAiVehicleSound's profile chooser; "
         "preserve the slot argument and original getter for every participant"),
        va=ID26_AUDIO_LOOKUP_CALL_VA,
    ))
    operations.append(_operation(
        "id26_audio_profile_selector_wrapper", "audio-profile-selection",
        wrapper_offset, bytes(len(wrapper)), wrapper,
        (f"forward Race/CarN/CarID unchanged except physical ID 26, whose audio selector "
         f"uses stock donor ID {donor_id}; return convention matches original RET 4"),
        va=wrapper_va,
    ))
    _validate_operations(data, operations)

    result = bytearray(data)
    for operation in operations:
        start = operation["file_offset"]
        result[start:start + len(bytes.fromhex(operation["replacement_bytes"]))] = bytes.fromhex(
            operation["replacement_bytes"]
        )
    candidate = bytes(result)

    # Replay the same operations from the exact pristine input, and assert the
    # two new audio sites plus section bounds as independent postconditions.
    for operation in operations:
        start = operation["file_offset"]
        replacement = bytes.fromhex(operation["replacement_bytes"])
        if candidate[start:start + len(replacement)] != replacement:
            raise CandidateError(f"post-patch range verification failed: {operation['name']}")
    if candidate[hook_offset:hook_offset + 5] != _call_rel32(ID26_AUDIO_LOOKUP_CALL_VA, wrapper_va):
        raise CandidateError("audio hook target verification failed")
    if candidate[wrapper_offset:wrapper_offset + len(wrapper)] != wrapper:
        raise CandidateError("audio wrapper verification failed")

    manifest = copy.deepcopy(g1_manifest)
    manifest.update({
        "phase": "R5V-G.2 bounded physical-ID26 tuned audio identity candidate",
        "profile": f"id26-audio-donor-{donor_id}",
        "g1_base_sha256": g1_digest,
        "donor_id": donor_id,
        "patched_sha256": sha256(candidate),
        "file_size": len(candidate),
        "text_virtual_size": {
            "original": TEXT_VIRTUAL_SIZE_ORIGINAL,
            "g1_patched": text["virtual_size"],
            "patched": new_text_virtual_size,
            "code_cave_va": f"0x{ID26_PROFILE_CODE_CAVE_VA:08X}",
            "g1_payload_size": len(g1_payload),
            "audio_wrapper_va": f"0x{wrapper_va:08X}",
            "audio_wrapper_size": len(wrapper),
            "rdata_rva": f"0x{rdata['rva']:X}",
            "non_overlap_proven": True,
        },
        "structural_self_check": copy.deepcopy(g1_manifest["structural_self_check"]),
        "operations": operations,
        "operation_counts_by_category": dict(Counter(op["category"] for op in operations)),
        "runtime_validation": "STATIC CANDIDATE — WAITING FOR HUMAN AUDIO A/B",
        "audio_identity": {
            "physical_vehicle_id": ID26_PHYSICAL_ID,
            "class": "T1",
            "runtime_family": "Mercedes",
            "lookup_source": "Race/CarN/CarID via FUN_004AC660",
            "consumer": "FUN_00408F20 gaAiVehicleSound constructor",
            "intercept_va": f"0x{ID26_AUDIO_LOOKUP_CALL_VA:08X}",
            "wrapper_va": f"0x{wrapper_va:08X}",
            "donor_id": donor_id,
            "donor": copy.deepcopy(DONORS[donor_id]),
            "physical_identity_changed": False,
            "class_model_wheel_physics_registry_changed": False,
            "warning_behavior": "ID26 takes the selected donor's existing tuned switch branch; warning string/code is not modified",
            "applies_to_any_participant_slot": True,
        },
        "risks": [
            "Static verification proves selector flow and bounded patch ranges, not audible similarity or sound quality.",
            "The donor setting applies wherever a participant's physical CarID is 26; this phase does not add ID26 to AI or event pools.",
            "Campaign audio, replay audio, and non-engine vehicle sound families are not qualified by the short player-car test.",
        ],
    })
    manifest["patched_sha256"] = sha256(candidate)
    _verify_structure(candidate, manifest)
    return candidate, manifest


def _verify_structure(candidate: bytes, manifest: dict[str, Any]) -> None:
    if sha256(candidate) != manifest["patched_sha256"]:
        raise CandidateError("candidate SHA256 does not match manifest")
    if len(candidate) != manifest["file_size"]:
        raise CandidateError("candidate size does not match manifest")
    pe_offset = struct.unpack_from("<I", candidate, 0x3C)[0]
    coff = pe_offset + 4
    if candidate[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise CandidateError("patched PE signature is invalid")
    if struct.unpack_from("<H", candidate, coff)[0] != 0x14C:
        raise CandidateError("patched candidate is not 32-bit x86")
    section_count = struct.unpack_from("<H", candidate, coff + 2)[0]
    optional = coff + 20
    optional_size = struct.unpack_from("<H", candidate, coff + 16)[0]
    section_table = optional + optional_size
    if section_count != 4 or optional_size != 0xE0:
        raise CandidateError("patched candidate section layout differs from retail")
    sections = []
    for index in range(section_count):
        section_header = section_table + index * 40
        name = candidate[section_header:section_header + 8].split(b"\0", 1)[0].decode("ascii")
        values = struct.unpack_from("<IIII", candidate, section_header + 8)
        sections.append({"name": name, "header_offset": section_header,
                         "virtual_size": values[0], "rva": values[1],
                         "raw_size": values[2], "raw_offset": values[3]})
    text = sections[0]
    if ([section["name"] for section in sections] != [".text", ".rdata", ".data", ".rsrc"]
            or text["rva"] != 0x1000 or text["raw_offset"] != 0x1000
            or text["raw_size"] != 0x28E000
            or sections[1]["rva"] != 0x28F000):
        raise CandidateError("patched candidate section layout differs from retail")
    if text["virtual_size"] != manifest["text_virtual_size"]["patched"]:
        raise CandidateError("patched .text VirtualSize does not match manifest")
    if struct.unpack_from("<I", candidate, optional + 28)[0] != 0x400000:
        raise CandidateError("patched candidate image base differs from retail")
    candidate_layout = {"image_base": 0x400000, "sections": sections}
    audio = manifest["audio_identity"]
    wrapper_va = int(audio["wrapper_va"], 16)
    wrapper = audio_wrapper_bytes(audio["donor_id"], wrapper_va)
    hook_offset = registry.va_to_file_offset(candidate_layout, ID26_AUDIO_LOOKUP_CALL_VA, 5)
    wrapper_offset = registry.va_to_file_offset(candidate_layout, wrapper_va, len(wrapper))
    if candidate[hook_offset:hook_offset + 5] != _call_rel32(ID26_AUDIO_LOOKUP_CALL_VA, wrapper_va):
        raise CandidateError("candidate audio call does not target the manifested wrapper")
    if candidate[wrapper_offset:wrapper_offset + len(wrapper)] != wrapper:
        raise CandidateError("candidate wrapper bytes differ from deterministic encoding")
    if audio["physical_identity_changed"] or audio["class_model_wheel_physics_registry_changed"]:
        raise CandidateError("manifest claims a forbidden physical identity change")
    try:
        registry._verify_structural(candidate, manifest)
    except registry.PatchError as exc:
        raise CandidateError(f"G.1 structural regression: {exc}") from exc


def verify_existing(source: Path, output: Path, manifest_path: Path,
                    donor_id: int) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if source == output or os.path.samefile(source, output):
        raise CandidateError("candidate must not overwrite pristine retail")
    expected, manifest = make_candidate(source.read_bytes(), donor_id)
    if output.read_bytes() != expected:
        raise CandidateError("candidate differs from deterministic pristine-to-G.1 rebuild")
    try:
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise CandidateError("invalid candidate manifest") from exc
    if stored != manifest:
        raise CandidateError("stored manifest differs from deterministic rebuild")
    _verify_structure(output.read_bytes(), stored)
    return manifest


def write_candidate(source: Path, output: Path, manifest_path: Path,
                    donor_id: int) -> dict[str, Any]:
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
    candidate, manifest = make_candidate(source.read_bytes(), donor_id)
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
    parser.add_argument("output", type=Path, help="new output path under research-output")
    parser.add_argument("--donor-id", type=int, choices=tuple(DONORS), required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    manifest_path = args.manifest or args.output.with_name(f"{args.output.stem}.manifest.json")
    try:
        if args.verify_existing:
            manifest = verify_existing(args.source, args.output, manifest_path, args.donor_id)
        else:
            manifest = write_candidate(args.source, args.output, manifest_path, args.donor_id)
    except (CandidateError, registry.PatchError, OSError, struct.error) as exc:
        parser.exit(2, f"vehicle audio candidate refused: {exc}\n")
    print(json.dumps({
        "verified_existing": args.verify_existing,
        "source_sha256": manifest["source_sha256"],
        "g1_base_sha256": manifest["g1_base_sha256"],
        "candidate_sha256": manifest["patched_sha256"],
        "size": manifest["file_size"],
        "donor_id": args.donor_id,
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
