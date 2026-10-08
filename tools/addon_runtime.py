#!/usr/bin/env python3
"""Prepare and verify the bounded R5V-J.1 in-memory runtime profile.

This tool derives operations from the audited I.1 builder. It never writes a
replacement MRallye.exe. The native launcher consumes the sealed RVP1 operation
table only after independently checking the retail image and staged resources.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import sys
import tempfile
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.addon_sdk import (  # noqa: E402
    AddonValidationError,
    build_artifacts,
    load_capabilities,
    load_manifests,
    verify_retail_executable,
)

try:  # Script and namespace-package test invocation are both supported.
    import build_vehicle_multislot_i1 as i1  # type: ignore[import-not-found]
    import vehicle_multislot_i1_runtime_package as i1_package  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - package-style test import
    from tools import build_vehicle_multislot_i1 as i1
    from tools import vehicle_multislot_i1_runtime_package as i1_package


RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
RETAIL_SIZE = 3_121_214
REFERENCE_PLAN_SHA256 = "357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989"
RUNTIME_ROOT_PROFILE = "i1-id27-r5v-qualifier-independent-t2-family"
DEFAULT_RETAIL_EXE = PROJECT_ROOT.parent / "corpora/retail/MRallye.exe"
DEFAULT_CAPABILITIES = PROJECT_ROOT / "research/vehicles/sdk/capabilities/retail-2001.json"
DEFAULT_I1_PACKAGE = PROJECT_ROOT / ".research-output/vehicles/multislot/i1/runtime-package"
DEFAULT_OUTPUT = PROJECT_ROOT / ".research-output/vehicles/sdk/j1/reference-runtime-final"
DEFAULT_MANIFESTS = [
    PROJECT_ROOT / "research/vehicles/sdk/examples/mercedes-ml320.json",
    PROJECT_ROOT / "research/vehicles/sdk/examples/r5v-qualifier-t2.json",
]
RVP_HEADER = struct.Struct("<4sHHIIII32s32s32s")
RVP_OPERATION = struct.Struct("<IIHBB")
RVP_MAGIC = b"MRVP"
RVP_VERSION = 1
IMAGE_BASE = 0x00400000
MACHINE_I386 = 0x014C
MAGENTA_RGBA_BITS = (0x3F800000, 0x00000000, 0x3F800000, 0x3F800000)
EXCLUDED_FILE_OPERATION = "pe_text_virtual_size_i1_payload"
CANARY_FILE_OFFSET = 0x2AC7AE
CANARY_BYTES = b"File"
RUNTIME_STATE_PATHS = frozenset({
    "datagame/playerstate.xml",
    "datagame/playerstate.xml#",
    "datagame/options.xml#",
})


class RuntimeIntegrationError(ValueError):
    """Unsupported build, incomplete runtime root, or unsafe patch plan."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _under_research_output(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    output_root = (PROJECT_ROOT / ".research-output").resolve()
    resolved_parent = absolute.parent.resolve()
    try:
        resolved_parent.relative_to(output_root)
    except ValueError as exc:
        raise RuntimeIntegrationError("runtime output must be under ignored .research-output") from exc
    if absolute.exists() or absolute.is_symlink() or getattr(absolute, "is_junction", lambda: False)():
        raise RuntimeIntegrationError(f"refusing to overwrite or follow runtime output: {absolute}")
    return absolute


def _inside(root: Path, relative: str) -> Path:
    normalized = relative.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (not normalized or pure.is_absolute() or ":" in normalized
            or any(part in {"", ".", ".."} for part in normalized.split("/"))
            or "\t" in normalized or "|" in normalized or "\n" in normalized):
        raise RuntimeIntegrationError(f"unsafe resource path: {relative!r}")
    path = root
    for part in pure.parts:
        path = path / part
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise RuntimeIntegrationError(f"resource path traverses a link: {relative}")
    if not path.is_file():
        raise RuntimeIntegrationError(f"resource file is missing: {relative}")
    return path


def _pe_sections(data: bytes) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise RuntimeIntegrationError("source is not a PE image")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\0\0":
        raise RuntimeIntegrationError("malformed PE signature")
    machine, count = struct.unpack_from("<HH", data, pe + 4)
    optional_size = struct.unpack_from("<H", data, pe + 20)[0]
    characteristics = struct.unpack_from("<H", data, pe + 22)[0]
    optional = pe + 24
    if optional + optional_size > len(data) or struct.unpack_from("<H", data, optional)[0] != 0x10B:
        raise RuntimeIntegrationError("only PE32 optional headers are supported")
    image_base = struct.unpack_from("<I", data, optional + 28)[0]
    size_image, size_headers = struct.unpack_from("<II", data, optional + 56)
    sections: list[dict[str, Any]] = []
    table = optional + optional_size
    for index in range(count):
        offset = table + index * 40
        if offset + 40 > len(data):
            raise RuntimeIntegrationError("truncated PE section table")
        name = data[offset:offset + 8].split(b"\0", 1)[0].decode("ascii", "strict")
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", data, offset + 8)
        sections.append({"name": name, "virtual_size": virtual_size, "rva": rva,
                         "raw_size": raw_size, "raw_offset": raw_offset})
    return ({"pe_offset": pe, "machine": machine, "image_base": image_base,
             "size_image": size_image, "size_headers": size_headers,
             "relocations_stripped": bool(characteristics & 0x0001)}, sections)


def _file_range_to_rva(sections: list[dict[str, Any]], file_offset: int, length: int) -> tuple[int, str]:
    for section in sections:
        start = section["raw_offset"]
        end = start + section["raw_size"]
        if start <= file_offset and file_offset + length <= end:
            return section["rva"] + file_offset - start, section["name"]
    raise RuntimeIntegrationError(f"file range 0x{file_offset:X}+0x{length:X} is not in one PE section")


def _reference_plan(manifest_paths: list[Path], capabilities_path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    manifests, _provenance = load_manifests(manifest_paths)
    capabilities, _capability_sha = load_capabilities(capabilities_path)
    artifacts = build_artifacts(manifests, capabilities)
    plan_bytes = artifacts["addon-plan.json"]
    if sha256(plan_bytes) != REFERENCE_PLAN_SHA256:
        raise RuntimeIntegrationError("J.0 reference addon-plan SHA256 differs from the accepted output")
    plan = json.loads(plan_bytes)
    expected = {
        26: ("T1", 7, "Mercedes", 0, [1.0, 0.0, 0.0, 1.0]),
        27: ("T2", 7, "R5VQualifier", 7, [1.0, 0.0, 1.0, 1.0]),
    }
    rows = {row.get("physical_id"): row for row in plan.get("addons", [])}
    if set(rows) != set(expected):
        raise RuntimeIntegrationError("reference plan must contain exactly physical IDs 26 and 27")
    for physical_id, (vehicle_class, local, family, audio, colour) in expected.items():
        row = rows[physical_id]
        if (row.get("vehicle_class"), row.get("class_local_index"),
                row.get("identity", {}).get("runtime_family"),
                row.get("audio", {}).get("stock_audio_profile_id"),
                row.get("race_colour_rgba")) != (vehicle_class, local, family, audio, colour):
            raise RuntimeIntegrationError(f"reference addon semantics differ for physical ID{physical_id}")
    return plan, artifacts


def _build_reference_candidate(source: bytes) -> tuple[bytes, dict[str, Any]]:
    original_record = i1.ID27_RECORD
    try:
        i1.ID27_RECORD = replace(
            original_record,
            race_colour_rgba_bits=MAGENTA_RGBA_BITS,
            race_colour_role="SDK manifest race/progress marker magenta; independent of body paint",
        )
        candidate, build_manifest = i1.make_candidate(source)
    finally:
        i1.ID27_RECORD = original_record
    profiles = build_manifest.get("profiles", [])
    if len(profiles) != 2 or profiles[1].get("race_colour_rgba_bits") != [f"{v:08x}" for v in MAGENTA_RGBA_BITS]:
        raise RuntimeIntegrationError("runtime candidate did not honor the ID27 manifest marker colour")
    return candidate, build_manifest


def _native_patch_artifacts(source: bytes, plan: dict[str, Any]) -> tuple[dict[str, Any], bytes, bytes]:
    digest = sha256(source)
    if digest != RETAIL_SHA256 or len(source) != RETAIL_SIZE:
        raise RuntimeIntegrationError("native runtime patch source is not the exact pristine retail image")
    pe, sections = _pe_sections(source)
    if (pe["machine"] != MACHINE_I386 or pe["image_base"] != IMAGE_BASE
            or not pe["relocations_stripped"]):
        raise RuntimeIntegrationError("retail PE architecture/base/relocation profile changed")
    candidate, build_manifest = _build_reference_candidate(source)
    expected_candidate_sha = build_manifest.get("patched_sha256")
    if (build_manifest.get("source_sha256") != RETAIL_SHA256
            or sha256(candidate) != expected_candidate_sha
            or len(candidate) != RETAIL_SIZE):
        raise RuntimeIntegrationError("audited I.1 builder failed its deterministic output self-check")
    # I.1's patch list is incremental from its H.2 parent, not a retail-relative
    # list. Rebuild both audited layers, validate each original byte range at its
    # layer boundary, then derive exact retail->final spans for suspended-image
    # installation. The derived spans retain every intersecting semantic owner.
    h2_candidate, h2_manifest = i1.i0.h2.make_candidate(source)
    if sha256(h2_candidate) != i1.i0.H2_SHA256:
        raise RuntimeIntegrationError("audited H.2 parent no longer reproduces its pinned image")
    h2_operations = h2_manifest.get("operations")
    i1_operations = build_manifest.get("operations")
    if not isinstance(h2_operations, list) or not isinstance(i1_operations, list):
        raise RuntimeIntegrationError("audited patch layer lacks an operation list")

    owners: list[dict[str, Any]] = []
    for layer_name, layer_base, layer_output, layer_ops in (
        ("H.2", source, h2_candidate, h2_operations),
        ("I.1", h2_candidate, candidate, i1_operations),
    ):
        rebuilt_layer = bytearray(layer_base)
        layer_ranges: list[tuple[int, int, str]] = []
        for operation in layer_ops:
            name = operation.get("name")
            offset = operation.get("file_offset")
            original_hex = operation.get("original_bytes")
            replacement_hex = operation.get("replacement_bytes")
            if (not isinstance(name, str) or type(offset) is not int
                    or not isinstance(original_hex, str) or not isinstance(replacement_hex, str)):
                raise RuntimeIntegrationError(f"{layer_name} builder returned a malformed operation")
            try:
                original = bytes.fromhex(original_hex)
                replacement = bytes.fromhex(replacement_hex)
            except ValueError as exc:
                raise RuntimeIntegrationError(f"{layer_name} builder returned invalid bytes: {name}") from exc
            if (not original or len(original) != len(replacement)
                    or offset < 0 or offset + len(original) > len(layer_base)):
                raise RuntimeIntegrationError(f"{layer_name} builder returned a malformed range: {name}")
            if layer_base[offset:offset + len(original)] != original:
                raise RuntimeIntegrationError(f"{layer_name} preimage mismatch: {name}")
            for start, end, prior_name in layer_ranges:
                if offset < end and start < offset + len(original):
                    raise RuntimeIntegrationError(f"overlapping {layer_name} operations: {prior_name}, {name}")
            layer_ranges.append((offset, offset + len(original), name))
            rebuilt_layer[offset:offset + len(original)] = replacement
            owners.append({
                "layer": layer_name,
                "name": name,
                "category": operation.get("category"),
                "semantic_purpose": operation.get("semantic_purpose"),
                "start": offset,
                "end": offset + len(original),
            })
        if bytes(rebuilt_layer) != layer_output:
            raise RuntimeIntegrationError(f"{layer_name} operation table does not reproduce its audited image")

    changed = [left != right for left, right in zip(source, candidate)]
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(changed):
        if not changed[index]:
            index += 1
            continue
        start = index
        while index < len(changed) and changed[index]:
            index += 1
        spans.append((start, index))

    manifest_operations: list[dict[str, Any]] = []
    rvp_operations: list[tuple[int, int, int, bytes, bytes]] = []
    excluded: list[dict[str, Any]] = []
    memory_ranges: list[tuple[int, int, str]] = []
    covered_changed_bytes: set[int] = set()
    for number, (offset, end) in enumerate(spans):
        original = source[offset:end]
        replacement = candidate[offset:end]
        provenance = [owner for owner in owners if offset < owner["end"] and owner["start"] < end]
        if not provenance:
            raise RuntimeIntegrationError(f"changed retail bytes at 0x{offset:X} have no audited semantic owner")
        for byte_offset in range(offset, end):
            covered_changed_bytes.add(byte_offset)
        name = f"retail_delta_{number:03d}"
        owner_rows = [{"layer": row["layer"], "name": row["name"],
                       "category": row["category"], "semantic_purpose": row["semantic_purpose"]}
                      for row in provenance]
        if offset >= 0x218 and end <= 0x21C:
            if offset != 0x218:
                raise RuntimeIntegrationError("unexpected PE header delta outside the audited text VirtualSize field")
            excluded.append({
                "name": name, "file_offset": offset,
                "expected_original_bytes": original.hex(), "replacement_bytes": replacement.hex(),
                "semantic_provenance": owner_rows,
                "reason": "PE .text VirtualSize is consumed during image mapping. The launcher cannot retroactively remap the process; it instead validates the code-cave page in the already mapped raw section before use.",
            })
            manifest_operations.append({
                "name": name, "semantic_provenance": owner_rows,
                "file_offset": offset, "rva": None, "section": "PE headers",
                "expected_original_bytes": original.hex(), "replacement_bytes": replacement.hex(),
                "installation": "FILE_IMAGE_RECONSTRUCTION_ONLY_NOT_WRITTEN_TO_PROCESS",
            })
            rvp_operations.append((offset, 0xFFFFFFFF, 1, original, replacement))
            continue
        rva, section_name = _file_range_to_rva(sections, offset, len(original))
        if rva + len(original) > pe["size_image"]:
            raise RuntimeIntegrationError(f"derived operation at 0x{offset:X} exceeds SizeOfImage")
        for start, prior_end, prior_name in memory_ranges:
            if rva < prior_end and start < rva + len(original):
                raise RuntimeIntegrationError(f"overlapping derived memory operations: {prior_name}, {name}")
        memory_ranges.append((rva, rva + len(original), name))
        manifest_operations.append({
            "name": name,
            "semantic_provenance": owner_rows,
            "target_module": "MRallye.exe",
            "file_offset": offset,
            "rva": rva,
            "preferred_va": IMAGE_BASE + rva,
            "section": section_name,
            "expected_original_bytes": original.hex(),
            "expected_original_sha256": sha256(original),
            "replacement_bytes": replacement.hex(),
            "replacement_sha256": sha256(replacement),
            "required_initialization_phase": "before_primary_thread_first_resume",
            "page_class": "EXECUTE_READWRITE" if section_name == ".text" else "READWRITE",
            "dependencies": ["exact_retail_file_identity", "mapped_image_identity", "all_preimages_validated"],
        })
        rvp_operations.append((offset, rva, 0, original, replacement))

    if len(covered_changed_bytes) != sum(changed):
        raise RuntimeIntegrationError("derived operation spans do not cover all reference image changes")
    if len(excluded) != 1 or not rvp_operations:
        raise RuntimeIntegrationError("runtime operation inventory is incomplete")
    canary_rva, canary_section = _file_range_to_rva(sections, CANARY_FILE_OFFSET, len(CANARY_BYTES))
    if source[CANARY_FILE_OFFSET:CANARY_FILE_OFFSET + len(CANARY_BYTES)] != CANARY_BYTES or canary_section != ".rdata":
        raise RuntimeIntegrationError("audited inert .rdata canary bytes changed in the supported retail build")
    if any(canary_rva < end and start < canary_rva + len(CANARY_BYTES)
           for start, end, _name in memory_ranges):
        raise RuntimeIntegrationError("inert canary overlaps a native integration patch")
    canary_owner = {
        "name": "inert_rdata_write_canary",
        "layer": "J.1 launcher validation",
        "category": "no-op memory integration canary",
        "semantic_purpose": "write the exact same four bytes of an import-name string in the mapped read-only .rdata section, verify, and restore page protection before resume",
    }
    manifest_operations.append({
        "name": "inert_rdata_write_canary",
        "semantic_provenance": [canary_owner],
        "target_module": "MRallye.exe",
        "file_offset": CANARY_FILE_OFFSET,
        "rva": canary_rva,
        "preferred_va": IMAGE_BASE + canary_rva,
        "section": canary_section,
        "expected_original_bytes": CANARY_BYTES.hex(),
        "expected_original_sha256": sha256(CANARY_BYTES),
        "replacement_bytes": CANARY_BYTES.hex(),
        "replacement_sha256": sha256(CANARY_BYTES),
        "required_initialization_phase": "before_primary_thread_first_resume",
        "page_class": "READWRITE_TEMPORARY_NOOP",
        "dependencies": ["exact_retail_file_identity", "mapped_image_identity", "all_preimages_validated"],
        "runtime_semantic_effect": "none; preserves exact string bytes and restores the original page protection",
    })
    rvp_operations.append((CANARY_FILE_OFFSET, canary_rva, 2, CANARY_BYTES, CANARY_BYTES))
    plan_sha = sha256(canonical_json(plan))
    if plan_sha != REFERENCE_PLAN_SHA256:
        raise RuntimeIntegrationError("canonical runtime plan SHA changed")
    patch_manifest = {
        "schema_version": 1,
        "artifact_kind": "native in-memory patch manifest",
        "profile": "r5v-j1-two-addon-retail-2001-reference",
        "status": "STATICALLY_VERIFIED_READY_FOR_BOOTSTRAP_TEST",
        "source": {"file_name": "MRallye.exe", "sha256": digest, "size": len(source)},
        "addon_plan_sha256": plan_sha,
        "reference_image": {
            "sha256": expected_candidate_sha,
            "size": len(candidate),
            "written_to_disk": False,
            "derivation": "deterministic audited I.1 retail-relative reference reconstruction; no executable file is emitted",
            "hash_semantics": "SHA256 of deterministic retail-file reconstruction, including the file-only PE-header operation; not a hash of the mapped process address space",
        },
        "pe": {"machine": "I386", "machine_value": MACHINE_I386,
               "optional_header": "PE32", "preferred_image_base": IMAGE_BASE,
               "size_of_image": pe["size_image"], "relocations": "STRIPPED_FIXED_BASE",
               "runtime_base_policy": "mapped image must equal 0x00400000"},
        "operations": manifest_operations,
        "file_only_operations": excluded,
        "process_memory_operation_count": len(rvp_operations) - len(excluded),
        "atomic_installation": {
            "create_suspended": True,
            "verify_every_preimage_before_first_write": True,
            "write_before_primary_thread_resume": True,
            "partial_failure": "terminate suspended child; never resume; no unsafe rollback",
        },
        "non_mutating_canary": {
            "name": "inert_rdata_write_canary",
            "file_offset": CANARY_FILE_OFFSET,
            "rva": canary_rva,
            "section": canary_section,
            "expected_bytes_hex": CANARY_BYTES.hex(),
            "replacement_bytes_hex": CANARY_BYTES.hex(),
            "effect": "no semantic image change; exercises exact targeting, temporary protection change, remote write/readback and protection restoration",
        },
        "evidence_boundary": "STATIC_PLAN_ONLY_NOT_RUNTIME_QUALIFIED",
    }
    header = RVP_HEADER.pack(
        RVP_MAGIC, RVP_VERSION, MACHINE_I386, IMAGE_BASE, len(source), len(candidate),
        len(rvp_operations), bytes.fromhex(digest), bytes.fromhex(expected_candidate_sha),
        bytes.fromhex(plan_sha),
    )
    binary = bytearray(header)
    for file_offset, rva, flags, original, replacement in rvp_operations:
        section_kind = 0 if flags == 1 else (1 if _file_range_to_rva(sections, file_offset, len(original))[1] == ".text" else 2)
        binary.extend(RVP_OPERATION.pack(file_offset, rva, len(original), flags, section_kind))
        binary.extend(original)
        binary.extend(replacement)
    return patch_manifest, bytes(binary), candidate


def _resource_index(rows: list[dict[str, Any]]) -> bytes:
    ordered = sorted(rows, key=lambda row: row["path"].casefold())
    if len({row["path"].casefold() for row in ordered}) != len(ordered):
        raise RuntimeIntegrationError("resource inventory contains a case-insensitive path collision")
    lines = []
    for row in ordered:
        path = row.get("path")
        size = row.get("size")
        digest = row.get("sha256")
        if not isinstance(path, str) or type(size) is not int or not isinstance(digest, str):
            raise RuntimeIntegrationError("malformed resource inventory row")
        normalized = path.replace("\\", "/")
        pure = PurePosixPath(normalized)
        if (pure.is_absolute() or ":" in normalized or any(part in {"", ".", ".."} for part in normalized.split("/"))
                or any(char in normalized for char in "\t|\r\n")):
            raise RuntimeIntegrationError(f"unsafe resource path in inventory: {path!r}")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise RuntimeIntegrationError(f"invalid SHA256 in resource inventory: {path}")
        lines.append(f"{digest}\t{size}\t{normalized}\n")
    return "".join(lines).encode("utf-8")


def _validate_runtime_resource_set(expected: set[str], actual: set[str]) -> None:
    expected_folded = {path.replace("\\", "/").casefold() for path in expected}
    actual_folded = {path.replace("\\", "/").casefold() for path in actual}
    resource_files = actual_folded - RUNTIME_STATE_PATHS
    unexpected = actual_folded - expected_folded - RUNTIME_STATE_PATHS
    if resource_files != expected_folded or unexpected:
        raise RuntimeIntegrationError("resource-root file set differs from the qualified package inventory")


def _unique_package_paths(paths: list[str]) -> list[str]:
    unique: list[str] = []
    seen: dict[str, str] = {}
    for path in paths:
        normalized = path.replace("\\", "/")
        key = normalized.casefold()
        prior = seen.get(key)
        if prior is not None:
            if prior != normalized:
                raise RuntimeIntegrationError("I.1 package contains a case-insensitive path collision")
            continue
        seen[key] = normalized
        unique.append(path)
    return unique


def _expected_resources(package: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    package = Path(package)
    if package.is_symlink() or getattr(package, "is_junction", lambda: False)():
        raise RuntimeIntegrationError("qualified I.1 resource package root is linked")
    package = package.resolve()
    if not package.is_dir():
        raise RuntimeIntegrationError("qualified I.1 resource package root is missing or linked")
    try:
        package_manifest = json.loads((package / i1_package.RUNTIME_MANIFEST_NAME).read_text(encoding="utf-8"))
        rows = package_manifest.get("resource_inventory")
        if not isinstance(rows, list):
            raise RuntimeIntegrationError("I.1 resource inventory is missing")
        candidate = package_manifest.get("candidate", {})
        scene = package_manifest.get("vehicle_select_scene", {})
        allowed = [row.get("path") for row in rows]
        allowed.extend((candidate.get("path"), candidate.get("patch_manifest_path"),
                        scene.get("path"), scene.get("manifest_path"),
                        i1_package.RUNTIME_MANIFEST_NAME))
        if any(not isinstance(path, str) or not path for path in allowed):
            raise RuntimeIntegrationError("I.1 package manifest contains an invalid allowlisted path")
        allowed = _unique_package_paths(allowed)
        # The old runtime package directory was used as a game CWD and now
        # contains user-generated PlayerState save files. Verify an exact
        # manifest projection made only from allowlisted build artifacts;
        # keep those unrelated files untouched and out of the runtime root.
        with tempfile.TemporaryDirectory(prefix=".j1-i1-verify-", dir=package.parent) as temp:
            projection = Path(temp)
            for relative in allowed:
                source_path = i1_package._inside(package, relative)
                target_path = projection.joinpath(*Path(relative.replace("\\", "/")).parts)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.link(source_path, target_path)
                except FileExistsError as exc:
                    raise RuntimeIntegrationError(
                        f"duplicate I.1 staging target: {relative}") from exc
                except OSError:
                    # Some managed Windows filesystems deny hardlinks. A
                    # temporary byte-for-byte projection is still safe and is
                    # removed automatically; the source package is read-only.
                    shutil.copyfile(source_path, target_path)
            verified = i1_package.verify_package(projection)
    except (i1_package.PackageError, OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeIntegrationError(f"qualified I.1 resource package verification failed: {exc}") from exc
    if (verified.get("status") != "VERIFIED"
            or package_manifest.get("profile") != RUNTIME_ROOT_PROFILE
            or package_manifest.get("candidate", {}).get("sha256") != "90abfbf9825f1cc7acebb3a1a2811a179e6474f2406433854e1ffdbc60bdd955"):
        raise RuntimeIntegrationError("resource input is not the exact qualified I.1 package")
    if not isinstance(rows, list) or len(rows) != 243:
        raise RuntimeIntegrationError("I.1 resource inventory changed from the qualified 243-file package")
    return package_manifest, rows


def _copy_resource_root(package: Path, rows: list[dict[str, Any]], destination: Path) -> None:
    for row in rows:
        relative = row["path"]
        source = _inside(package, relative)
        target = destination.joinpath(*PurePosixPath(relative.replace("\\", "/")).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        data_hash = sha256_file(target)
        if target.stat().st_size != row["size"] or data_hash != row["sha256"]:
            raise RuntimeIntegrationError(f"resource copy verification failed: {relative}")


def prepare_bundle(*, retail_exe: Path = DEFAULT_RETAIL_EXE,
                   capabilities_path: Path = DEFAULT_CAPABILITIES,
                   package: Path = DEFAULT_I1_PACKAGE,
                   output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output = _under_research_output(output)
    retail_exe = Path(retail_exe)
    capabilities, _ = load_capabilities(capabilities_path)
    exe_check = verify_retail_executable(retail_exe, capabilities)
    if exe_check["sha256"] != RETAIL_SHA256 or exe_check["size"] != RETAIL_SIZE:
        raise RuntimeIntegrationError("selected build profile is not the fixed R5V-J.1 retail build")
    plan, artifacts = _reference_plan(DEFAULT_MANIFESTS, capabilities_path)
    package_manifest, rows = _expected_resources(Path(package))
    source = retail_exe.read_bytes()
    patch_manifest, binary_operations, runtime_candidate = _native_patch_artifacts(source, plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        (stage / "addon-plan.json").write_bytes(artifacts["addon-plan.json"])
        (stage / "frontend-overlay.plan.json").write_bytes(artifacts["frontend-overlay.plan.json"])
        (stage / "resource-inventory.json").write_bytes(artifacts["resource-inventory.json"])
        patch_bytes = canonical_json(patch_manifest)
        (stage / "native-patch-manifest.json").write_bytes(patch_bytes)
        (stage / "native-patch-ops.rvp").write_bytes(binary_operations)
        resource_root = stage / "resource-root"
        resource_root.mkdir()
        _copy_resource_root(Path(package), rows, resource_root)
        index_bytes = _resource_index(rows)
        (stage / "resource-index.tsv").write_bytes(index_bytes)
        resource_manifest = {
            "schema_version": 1,
            "artifact_kind": "verified external loose-resource root inventory",
            "status": "STAGED_UNQUALIFIED_RESOURCE_ROOT",
            "source_profile": RUNTIME_ROOT_PROFILE,
            "source_package_manifest_sha256": sha256_file(Path(package) / i1_package.RUNTIME_MANIFEST_NAME),
            "resource_count": len(rows),
            "data_sma": next((dict(row) for row in rows if row["path"].casefold() == "data.sma"), None),
            "index_sha256": sha256(index_bytes),
            "runtime_state_paths": sorted(RUNTIME_STATE_PATHS),
            "runtime_state_hashing": "excluded from resource inventory and preserved as user state",
            "resources": sorted(rows, key=lambda row: row["path"].casefold()),
            "root_resolution": {
                "intended_process_current_directory": "resource-root",
                "co-location_with_executable": False,
                "evidence": "I.1 human runtime package co-located MRallye.exe and loose resources; current-directory-only lookup is a J.1 runtime validation item.",
            },
            "original_installation_files_modified": False,
            "stock_resource_archive_modified": False,
        }
        resource_manifest_bytes = canonical_json(resource_manifest)
        (stage / "resource-manifest.json").write_bytes(resource_manifest_bytes)
        profile = {
            "schema_version": 1,
            "profile": "r5v-j1-two-addon-retail-2001-reference",
            "status": "READY_FOR_HUMAN_RUNTIME",
            "runtime_level": "STATICALLY_VERIFIED_EXTERNAL_LAUNCHER_CANDIDATE",
            "retail_exe": {"sha256": RETAIL_SHA256, "size": RETAIL_SIZE, "machine": "I386", "image_base": IMAGE_BASE, "relocations": "STRIPPED"},
            "addon_plan_sha256": sha256(artifacts["addon-plan.json"]),
            "native_patch_manifest_sha256": sha256(patch_bytes),
            "native_patch_operations_sha256": sha256(binary_operations),
            "resource_manifest_sha256": sha256(resource_manifest_bytes),
            "resource_index_sha256": sha256(index_bytes),
            "resource_count": len(rows),
            "resource_root": "resource-root",
            "reconstructed_reference_file_sha256": sha256(runtime_candidate),
            "reconstructed_reference_file_size": len(runtime_candidate),
            "reference_executable_written_to_disk": False,
            "runtime_installable": False,
            "unresolved_runtime_gates": [
                "bootstrap-only original EXE startup has not received human visual confirmation",
                "current-directory resource-root resolution is not distinguished from executable-directory resolution by prior I.1 captures",
                "the available canary is a no-op memory-write exercise, not a game-visible semantic integration",
                "same-process and graphics-wrapper compatibility remain unqualified",
            ],
        }
        (stage / "runtime-profile.json").write_bytes(canonical_json(profile))
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return verify_bundle(output, retail_exe=retail_exe, package=Path(package))


def verify_bundle(bundle: Path, *, retail_exe: Path = DEFAULT_RETAIL_EXE,
                   package: Path = DEFAULT_I1_PACKAGE,
                   capabilities_path: Path = DEFAULT_CAPABILITIES) -> dict[str, Any]:
    bundle = Path(bundle)
    if bundle.is_symlink() or getattr(bundle, "is_junction", lambda: False)():
        raise RuntimeIntegrationError("runtime bundle root is link-backed")
    bundle = bundle.resolve()
    if not bundle.is_dir():
        raise RuntimeIntegrationError("runtime bundle root is missing or link-backed")
    capabilities, _ = load_capabilities(capabilities_path)
    exe_check = verify_retail_executable(retail_exe, capabilities)
    plan, artifacts = _reference_plan(DEFAULT_MANIFESTS, capabilities_path)
    patch_manifest, binary_operations, runtime_candidate = _native_patch_artifacts(Path(retail_exe).read_bytes(), plan)
    package_manifest, rows = _expected_resources(Path(package))
    expected_root_files = {row["path"].replace("\\", "/").casefold() for row in rows}
    root = bundle / "resource-root"
    if not root.is_dir() or root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise RuntimeIntegrationError("resource-root is missing")
    actual_root_files: set[str] = set()
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            p = Path(current) / name
            if p.is_symlink() or getattr(p, "is_junction", lambda: False)():
                raise RuntimeIntegrationError(f"resource root contains a linked directory: {p}")
        for name in files:
            p = Path(current) / name
            if p.is_symlink():
                raise RuntimeIntegrationError(f"resource root contains a symlink: {p}")
            actual_root_files.add(p.relative_to(root).as_posix().casefold())
    _validate_runtime_resource_set(expected_root_files, actual_root_files)
    for row in rows:
        path = _inside(root, row["path"])
        if path.stat().st_size != row["size"] or sha256_file(path) != row["sha256"]:
            raise RuntimeIntegrationError(f"resource-root hash/size mismatch: {row['path']}")
    index_bytes = _resource_index(rows)
    resource_manifest = {
        "schema_version": 1,
        "artifact_kind": "verified external loose-resource root inventory",
        "status": "STAGED_UNQUALIFIED_RESOURCE_ROOT",
        "source_profile": RUNTIME_ROOT_PROFILE,
        "source_package_manifest_sha256": sha256_file(Path(package) / i1_package.RUNTIME_MANIFEST_NAME),
        "resource_count": len(rows),
        "data_sma": next((dict(row) for row in rows if row["path"].casefold() == "data.sma"), None),
        "index_sha256": sha256(index_bytes),
        "runtime_state_paths": sorted(RUNTIME_STATE_PATHS),
        "runtime_state_hashing": "excluded from resource inventory and preserved as user state",
        "resources": sorted(rows, key=lambda row: row["path"].casefold()),
        "root_resolution": {
            "intended_process_current_directory": "resource-root",
            "co-location_with_executable": False,
            "evidence": "I.1 human runtime package co-located MRallye.exe and loose resources; current-directory-only lookup is a J.1 runtime validation item.",
        },
        "original_installation_files_modified": False,
        "stock_resource_archive_modified": False,
    }
    expected_files = {
        "addon-plan.json": artifacts["addon-plan.json"],
        "frontend-overlay.plan.json": artifacts["frontend-overlay.plan.json"],
        "resource-inventory.json": artifacts["resource-inventory.json"],
        "native-patch-manifest.json": canonical_json(patch_manifest),
        "native-patch-ops.rvp": binary_operations,
        "resource-index.tsv": index_bytes,
        "resource-manifest.json": canonical_json(resource_manifest),
    }
    for relative, expected in expected_files.items():
        path = bundle / relative
        if not path.is_file() or path.read_bytes() != expected:
            raise RuntimeIntegrationError(f"runtime bundle artifact differs from deterministic rebuild: {relative}")
    profile = json.loads((bundle / "runtime-profile.json").read_text(encoding="utf-8"))
    expected_profile = {
        "schema_version": 1,
        "profile": "r5v-j1-two-addon-retail-2001-reference",
        "status": "READY_FOR_HUMAN_RUNTIME",
        "runtime_level": "STATICALLY_VERIFIED_EXTERNAL_LAUNCHER_CANDIDATE",
        "retail_exe": {"sha256": RETAIL_SHA256, "size": RETAIL_SIZE, "machine": "I386", "image_base": IMAGE_BASE, "relocations": "STRIPPED"},
        "addon_plan_sha256": sha256(artifacts["addon-plan.json"]),
        "native_patch_manifest_sha256": sha256(canonical_json(patch_manifest)),
        "native_patch_operations_sha256": sha256(binary_operations),
        "resource_manifest_sha256": sha256(canonical_json(resource_manifest)),
        "resource_index_sha256": sha256(index_bytes),
        "resource_count": len(rows),
        "resource_root": "resource-root",
        "reconstructed_reference_file_sha256": sha256(runtime_candidate),
        "reconstructed_reference_file_size": len(runtime_candidate),
        "reference_executable_written_to_disk": False,
        "runtime_installable": False,
        "unresolved_runtime_gates": [
            "bootstrap-only original EXE startup has not received human visual confirmation",
            "current-directory resource-root resolution is not distinguished from executable-directory resolution by prior I.1 captures",
            "the available canary is a no-op memory-write exercise, not a game-visible semantic integration",
            "same-process and graphics-wrapper compatibility remain unqualified",
        ],
    }
    if profile != expected_profile:
        raise RuntimeIntegrationError("runtime profile differs from deterministic reference")
    top_expected = set(expected_files) | {"runtime-profile.json", "resource-root"}
    actual_top = {p.name for p in bundle.iterdir()}
    if actual_top != top_expected:
        raise RuntimeIntegrationError("runtime bundle has an unexpected top-level file set")
    if (bundle / "resource-root" / "MRallye.exe").exists():
        raise RuntimeIntegrationError("resource root must not contain a replacement or copied executable")
    return {
        "status": "PASS_STATIC_RUNTIME_BUNDLE",
        "retail_exe": exe_check,
        "addon_plan_sha256": sha256(artifacts["addon-plan.json"]),
        "patch_operation_count": len(patch_manifest["operations"]),
        "process_memory_operation_count": patch_manifest["process_memory_operation_count"],
        "file_only_operation_count": len(patch_manifest["file_only_operations"]),
        "patch_manifest_sha256": sha256(canonical_json(patch_manifest)),
        "patch_ops_sha256": sha256(binary_operations),
        "resource_count": len(rows),
        "resource_index_sha256": sha256(index_bytes),
        "reconstructed_reference_file_sha256": sha256(runtime_candidate),
        "patched_executable_written": False,
        "runtime_qualified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or verify the R5V-J.1 exact-build external runtime bundle")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="stage the exact two-addon in-memory runtime reference")
    prepare.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL_EXE)
    prepare.add_argument("--capabilities", type=Path, default=DEFAULT_CAPABILITIES)
    prepare.add_argument("--i1-package", type=Path, default=DEFAULT_I1_PACKAGE)
    prepare.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    verify = commands.add_parser("verify", help="rebuild and verify all bundle plans, hashes and resources")
    verify.add_argument("bundle", type=Path, nargs="?", default=DEFAULT_OUTPUT)
    verify.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL_EXE)
    verify.add_argument("--capabilities", type=Path, default=DEFAULT_CAPABILITIES)
    verify.add_argument("--i1-package", type=Path, default=DEFAULT_I1_PACKAGE)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_bundle(retail_exe=args.retail_exe, capabilities_path=args.capabilities,
                                    package=args.i1_package, output=args.output)
        else:
            result = verify_bundle(args.bundle, retail_exe=args.retail_exe, package=args.i1_package,
                                   capabilities_path=args.capabilities)
    except (RuntimeIntegrationError, AddonValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
