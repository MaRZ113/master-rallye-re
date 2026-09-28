"""Reproducible corpus accounting for vehicle DX revision 131 -> 135.

The scanner reads DX/GXM files under a supplied root and emits derived
metadata only. It never writes game assets and never infers a source pairing
from output names alone: direct oracle status requires matching GXM SHA256.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any

from .cooker_diff import compare_cooker_dx
from .demo_dx import inspect_demo_dx
from .dx import parse_dx_bytes
from .dx_revision_upgrade import (
    REVISION_131,
    REVISION_135,
    DxRevisionUpgradeError,
    upgrade_dx_131_to_135_with_report,
    validate_existing_rev135,
)

_VERSION_DIR = re.compile(r"^(9\.3\.1|9\.10\.0)_(.+)$", re.IGNORECASE)
_ROLES = {"car", "complete", "wheel"}
_RUNTIME_REPORTS = (
    Path("research/r-cooker1_1/prototype-results.json"),
    Path("research/r-cooker1_2/prototype-results.json"),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _portable_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _generation_family(path: Path) -> tuple[str | None, str | None]:
    match = _VERSION_DIR.match(path.parent.name)
    if not match:
        return None, None
    generation, family = match.groups()
    if family.casefold().startswith("dx"):
        family = family[2:]
    return generation, family


def _source_gxm(path: Path, role: str, root: Path) -> dict[str, Any]:
    names = [f"{role}.gxm"]
    if role.casefold() == "complete":
        names.append("comlplete.gxm")
    found: list[Path] = []
    for name in names:
        found = sorted(
            (item for item in path.parent.iterdir()
             if item.is_file() and item.name.casefold() == name.casefold()),
            key=lambda item: item.name.casefold(),
        )
        if found:
            break
    if not found:
        return {"status": "MISSING", "path": None, "sha256": None, "size": None}
    if len(found) != 1:
        return {
            "status": "AMBIGUOUS",
            "path": [_portable_path(item, root) for item in found],
            "sha256": None,
            "size": None,
        }
    source = found[0]
    data = source.read_bytes()
    return {
        "status": "FOUND",
        "path": _portable_path(source, root),
        "sha256": _sha256(data),
        "size": len(data),
        "filename_role_normalization": (
            "comlplete.gxm treated as complete.gxm source"
            if source.name.casefold() == "comlplete.gxm" else None
        ),
    }


def _runtime_candidate_hashes(repository_root: Path) -> set[str]:
    """Read only candidate hashes whose owning result records runtime PASS."""
    result: set[str] = set()
    first_path, second_path = (repository_root / path for path in _RUNTIME_REPORTS)
    if first_path.is_file():
        try:
            report = json.loads(first_path.read_text(encoding="utf-8"))
            if (report.get("runtime_status") == "PASS"
                    and report.get("runtime_evidence_status") == "CONFIRMED_BY_RUNTIME"):
                for resource in report.get("resources", {}).values():
                    candidate = resource.get("candidate", {})
                    digest = candidate.get("sha256") if isinstance(candidate, dict) else None
                    if isinstance(digest, str):
                        result.add(digest.lower())
        except (OSError, ValueError, AttributeError):
            pass
    if second_path.is_file():
        try:
            report = json.loads(second_path.read_text(encoding="utf-8"))
            forester = report.get("forester", {})
            if (forester.get("runtime_status") == "PASS"
                    and forester.get("runtime_evidence") == "CONFIRMED_BY_RUNTIME"):
                for pair in forester.get("output_pairs", {}).values():
                    candidate = pair.get("candidate", {})
                    digest = candidate.get("sha256") if isinstance(candidate, dict) else None
                    if isinstance(digest, str):
                        result.add(digest.lower())
        except (OSError, ValueError, AttributeError):
            pass
    return result


def _triangle_multiset_equal(first, second) -> bool:
    if len(first.physical_draws) != len(second.physical_draws):
        return False
    for left, right in zip(first.physical_draws, second.physical_draws):
        if (left.vertex_base, left.index_start, left.index_count) != (
                right.vertex_base, right.index_start, right.index_count):
            return False
        a = first.local_indices[left.index_start:left.index_start + left.index_count]
        b = second.local_indices[right.index_start:right.index_start + right.index_count]
        if len(a) != len(b) or len(a) % 3:
            return False
        triangles_a = Counter(
            tuple(a[index + corner] + left.vertex_base for corner in range(3))
            for index in range(0, len(a), 3)
        )
        triangles_b = Counter(
            tuple(b[index + corner] + right.vertex_base for corner in range(3))
            for index in range(0, len(b), 3)
        )
        if triangles_a != triangles_b:
            return False
    return True


def _changed_ranges(first: bytes, second: bytes) -> list[list[int]]:
    if len(first) != len(second):
        common = min(len(first), len(second))
        result = _changed_ranges(first[:common], second[:common])
        if len(first) != common or len(second) != common:
            result.append([common, max(len(first), len(second))])
        return result
    result: list[list[int]] = []
    start: int | None = None
    for offset, (a, b) in enumerate(zip(first, second)):
        if a != b and start is None:
            start = offset
        elif a == b and start is not None:
            result.append([start, offset])
            start = None
    if start is not None:
        result.append([start, len(first)])
    return result


def _candidate_comparison(candidate: bytes, official: bytes, source: str) -> dict[str, Any]:
    candidate_model = parse_dx_bytes(candidate, f"{source} [generated rev135]")
    official_model = parse_dx_bytes(official, f"{source} [official rev135]")
    candidate_view = inspect_demo_dx(candidate, f"{source} [generated rev135]")
    official_view = inspect_demo_dx(official, f"{source} [official rev135]")
    candidate_existing_validation = validate_existing_rev135(
        candidate, f"{source} [generated rev135 as external]"
    )
    official_validation = validate_existing_rev135(official, f"{source} [official rev135]")

    same_size = len(candidate) == len(official)
    same_index_range = (
        candidate_model.local_index_offset == official_model.local_index_offset
        and len(candidate_model.local_indices) == len(official_model.local_indices)
    )
    local_equal = candidate_model.local_indices == official_model.local_indices
    if same_index_range:
        index_start = candidate_model.local_index_offset
        index_end = index_start + len(candidate_model.local_indices) * 2
        non_index_bytes_equal = (
            candidate[:index_start] == official[:index_start]
            and candidate[index_end:] == official[index_end:]
        )
        outside_differences = [
            offset for offset, (left, right) in enumerate(zip(candidate, official))
            if left != right and not index_start <= offset < index_end
        ]
    else:
        index_start = index_end = None
        non_index_bytes_equal = False
        outside_differences = []

    same_triangles = _triangle_multiset_equal(candidate_model, official_model)
    if not same_size:
        status = "SIZE_DIFFERENCE"
    elif candidate == official:
        status = "BYTE_IDENTICAL"
    elif non_index_bytes_equal and same_triangles:
        status = "ONLY_LOCAL_INDEX_ORDER" if not local_equal else "INDEX_ENCODING_DIFFERENCE"
    else:
        status = "ADDITIONAL_DIFFERENCES"
    ranges = _changed_ranges(candidate, official)
    return {
        "status": status,
        "candidate_sha256": _sha256(candidate),
        "official_sha256": _sha256(official),
        "candidate_size": len(candidate),
        "official_size": len(official),
        "same_size": same_size,
        "changed_byte_count": (
            sum(left != right for left, right in zip(candidate, official))
            + abs(len(candidate) - len(official))
        ),
        "changed_byte_range_count": len(ranges),
        "changed_byte_ranges_first_32": ranges[:32],
        "changed_byte_ranges_truncated": len(ranges) > 32,
        "non_index_bytes_equal": non_index_bytes_equal,
        "non_index_changed_offsets": outside_differences[:32],
        "non_index_changed_offset_count": len(outside_differences),
        "local_index_array_range": [index_start, index_end] if same_index_range else None,
        "local_indices_equal": local_equal,
        "changed_local_index_values": sum(
            left != right for left, right in zip(
                candidate_model.local_indices, official_model.local_indices
            )
        ),
        "per_draw_oriented_triangle_multisets_equal": same_triangles,
        "draw_region_equal": candidate_view.draw_raw == official_view.draw_raw,
        "geometry_attributes_equal": (
            candidate_view.positions == official_view.positions
            and candidate_view.normals == official_view.normals
            and candidate_view.colors == official_view.colors
            and candidate_view.uv_sets == official_view.uv_sets
        ),
        "global_index_table_equal": candidate_view.global_indices == official_view.global_indices,
        "collision_and_tail_equal": (
            candidate_view.data[candidate_view.collision.offset:]
            == official_view.data[official_view.collision.offset:]
        ),
        "candidate_existing_policy_status": candidate_existing_validation["status"],
        "official_existing_policy_status": official_validation["status"],
    }


def _pattern(record: dict[str, Any]) -> tuple[int, int, int, int, int]:
    flags = record["flags_before"]
    return (int(flags[0]), int(flags[1]), int(flags[2]),
            int(record["preserved_x"]), int(record["texture_slot_count"]))


def _direct_prefix_oracle(first: bytes, second: bytes, source: str,
                          first_gxm_sha: str, second_gxm_sha: str) -> dict[str, Any]:
    try:
        comparison = compare_cooker_dx(
            first,
            second,
            first_source=f"{source} rev131",
            second_source=f"{source} rev135",
            source_hashes=(first_gxm_sha, second_gxm_sha),
        )
        draw_result = comparison["draws"]
        if (comparison.get("source_identity", {}).get("status") != "CONFIRMED_BY_BYTES"
                or draw_result.get("record_alignment_status") != "VERIFIED"):
            return {
                "status": "UNRESOLVED",
                "draw_records_checked": 0,
                "matches": 0,
                "mismatches": [],
                "reason": "same-source identity or draw alignment was not confirmed",
            }
        mismatches: list[dict[str, Any]] = []
        records = draw_result.get("records", [])
        if not records:
            return {
                "status": "UNRESOLVED",
                "draw_records_checked": 0,
                "matches": 0,
                "mismatches": [],
                "reason": "verified pair has no aligned draw records",
            }
        for record in records:
            old = bytes.fromhex(record["legacy_opaque_prefix"])
            new = bytes.fromhex(record["rev135_parsed_prefix"])
            if len(old) != 11 or len(new) != 24:
                mismatch = {
                    "draw_index": record["draw_index"],
                    "reason": "unexpected prefix lengths",
                    "rev131_prefix": old.hex(),
                    "rev135_prefix": new.hex(),
                }
            else:
                a, b, c = old[:3]
                x, slots = struct.unpack_from("<II", old, 3)
                expected = struct.pack(
                    "<IIf4sII", 1, 0, 1.0, bytes((a, 0, b, c)), x, slots
                )
                mismatch = None if expected == new else {
                    "draw_index": record["draw_index"],
                    "reason": "prefix bytes differ from deterministic transform",
                    "rev131_prefix": old.hex(),
                    "expected_rev135_prefix": expected.hex(),
                    "observed_rev135_prefix": new.hex(),
                }
            if mismatch is not None:
                mismatches.append(mismatch)
        return {
            "status": "PASS" if not mismatches else "MISMATCH",
            "draw_records_checked": len(records),
            "matches": len(records) - len(mismatches),
            "mismatches": mismatches[:16],
            "mismatch_count": len(mismatches),
            "topology_status": draw_result.get("topology_status"),
            "geometry_equivalence": comparison.get(
                "geometry_equivalence", {}
            ).get("classification"),
        }
    except Exception as exc:
        return {
            "status": "UNRESOLVED",
            "draw_records_checked": 0,
            "matches": 0,
            "mismatches": [],
            "reason": f"{type(exc).__name__}: {exc}",
        }


def _relative_message(error: Exception, absolute_root: Path) -> str:
    message = str(error)
    return message.replace(str(absolute_root), "<inputs>").replace(
        str(absolute_root).replace("\\", "/"), "<inputs>"
    )


def scan_dx_corpus(root: Path | str, *, repository_root: Path | str | None = None) -> dict[str, Any]:
    """Scan a supplied corpus and return deterministic, path-portable metadata."""
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"DX corpus root is not a directory: {root}")
    repository = Path(repository_root).resolve() if repository_root else Path(__file__).resolve().parents[2]
    runtime_hashes = _runtime_candidate_hashes(repository)

    instances: list[dict[str, Any]] = []
    paths = sorted(
        (item for item in root.rglob("*") if item.is_file() and item.suffix.casefold() == ".dx"),
        key=lambda item: item.relative_to(root).as_posix().casefold(),
    )
    for path in paths:
        rel = _portable_path(path, root)
        try:
            data = path.read_bytes()
            digest = _sha256(data)
            magic, revision = struct.unpack_from("<2I", data) if len(data) >= 8 else (None, None)
            if magic != 0xD00D:
                revision = None
        except (OSError, struct.error) as exc:
            instances.append({
                "path": rel, "size": None, "sha256": None, "revision": None,
                "generation": None, "family": None, "role": path.stem.casefold(),
                "status": "READ_ERROR", "error": _relative_message(exc, root),
                "source_gxm": {"status": "NOT_CHECKED"},
            })
            continue
        generation, family = _generation_family(path)
        role = path.stem.casefold()
        if family and generation:
            try:
                source = _source_gxm(path, role, root)
            except OSError as exc:
                source = {
                    "status": "READ_ERROR", "path": None, "sha256": None,
                    "size": None, "error": _relative_message(exc, root),
                }
        else:
            source = {
                "status": "NOT_FOUND_FOR_UNCLASSIFIED_PATH",
                "path": None, "sha256": None, "size": None,
            }
        instances.append({
            "path": rel, "size": len(data), "sha256": digest, "revision": revision,
            "generation": generation, "family": family, "role": role,
            "status": "OK", "source_gxm": source,
        })

    all_by_sha: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_sha: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in instances:
        if item["sha256"] is not None:
            all_by_sha[item["sha256"]].append(item)
            if item["revision"] in (REVISION_131, REVISION_135):
                by_sha[item["sha256"]].append(item)

    unique_payloads: dict[str, dict[str, Any]] = {}
    for digest, files in sorted(all_by_sha.items()):
        sample = min(files, key=lambda entry: entry["path"].casefold())
        unique_payloads[digest] = {
            "sha256": digest,
            "revision": sample["revision"],
            "size": sample["size"],
            "file_instance_count": len(files),
            "paths": sorted((item["path"] for item in files), key=str.casefold),
            "families": sorted(
                {item["family"] for item in files if item["family"]}, key=str.casefold
            ),
        }
    conversions: dict[str, dict[str, Any]] = {}
    conversion_bytes: dict[str, bytes] = {}
    existing_validation: dict[str, dict[str, Any]] = {}
    for digest in sorted(by_sha):
        files = by_sha[digest]
        sample = min(files, key=lambda entry: entry["path"].casefold())
        payload = (root / Path(sample["path"])).read_bytes()
        revision = sample["revision"]
        if revision == REVISION_131:
            try:
                candidate, report = upgrade_dx_131_to_135_with_report(payload, sample["path"])
                conversion_bytes[digest] = candidate
                conversions[digest] = {
                    "status": "PASS",
                    "source_path": sample["path"],
                    "source_sha256": digest,
                    "output_sha256": report["output_sha256"],
                    "output_size": report["output_size"],
                    "output_revision": report["output_revision"],
                    "draw_records": report["draw_records_transformed"],
                    "vertex_count": report["parser_validation"]["vertex_count"],
                    "triangle_count": report["parser_validation"]["triangle_count"],
                    "generated_validation": {
                        "status": report["parser_validation"]["status"],
                        "policy": report["parser_validation"]["policy"],
                        "revision": report["parser_validation"]["revision"],
                        "draw_count": report["parser_validation"]["draw_count"],
                        "vertex_count": report["parser_validation"]["vertex_count"],
                        "triangle_count": report["parser_validation"]["triangle_count"],
                        "collision_tags": report["parser_validation"]["collision_tags"],
                        "parser_warnings": report["parser_validation"]["parser_warnings"],
                        "collision_errors": report["parser_validation"]["collision_errors"],
                        "collision_warnings": report["parser_validation"]["collision_warnings"],
                        "global_index_sequence_equal": (
                            report["parser_validation"]["global_index_validation"]["sequence_equal"]
                        ),
                    },
                    "runtime_evidence": (
                        "CONFIRMED_BY_RUNTIME" if report["output_sha256"] in runtime_hashes
                        else "STRUCTURALLY_SUPPORTED"
                    ),
                    "preservation_checks": report["preservation_checks"],
                    "draw_prefix_patterns": [
                        list(_pattern(record)) for record in report["records"]
                    ],
                }
            except (DxRevisionUpgradeError, OSError, ValueError, struct.error) as exc:
                conversions[digest] = {
                    "status": "REJECTED",
                    "source_path": sample["path"],
                    "source_sha256": digest,
                    "error_type": type(exc).__name__,
                    "error": _relative_message(exc, root),
                }
        elif revision == REVISION_135:
            try:
                validation = validate_existing_rev135(payload, sample["path"])
                existing_validation[digest] = {
                    "status": validation["status"],
                    "path": sample["path"],
                    "sha256": digest,
                    "draw_count": validation["draw_count"],
                    "vertex_count": validation["vertex_count"],
                    "triangle_count": validation["triangle_count"],
                    "ordering_divergence": validation["global_index_validation"]["ordering_divergence"],
                    "parser_errors": validation["parser_errors"],
                }
            except (DxRevisionUpgradeError, OSError, ValueError, struct.error) as exc:
                existing_validation[digest] = {
                    "status": "REJECTED",
                    "path": sample["path"],
                    "sha256": digest,
                    "error_type": type(exc).__name__,
                    "error": _relative_message(exc, root),
                }

    pair_groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for item in instances:
        if item["status"] == "OK" and item["generation"] and item["family"]:
            if item["role"] in _ROLES:
                pair_groups[(item["family"].casefold(), item["role"])][item["generation"]].append(item)

    pairs: list[dict[str, Any]] = []
    direct_formula_records = 0
    direct_formula_matches = 0
    direct_formula_mismatches = 0
    direct_unresolved = 0
    direct_pattern_counts: Counter[tuple[int, int, int, int, int]] = Counter()
    unpaired: list[str] = []
    unverified_count = 0
    ambiguous_count = 0
    for (family_key, role), generations in sorted(pair_groups.items()):
        old_files = generations.get("9.3.1", [])
        new_files = generations.get("9.10.0", [])
        if not old_files or not new_files:
            unpaired.extend(item["path"] for item in old_files + new_files)
            continue
        family_display = old_files[0]["family"] or new_files[0]["family"] or family_key
        if len(old_files) != 1 or len(new_files) != 1:
            pairs.append({
                "family": family_display, "role": role,
                "status": "AMBIGUOUS_OUTPUT_INSTANCES",
                "rev131_paths": sorted((item["path"] for item in old_files), key=str.casefold),
                "rev135_paths": sorted((item["path"] for item in new_files), key=str.casefold),
            })
            ambiguous_count += 1
            continue
        old, new = old_files[0], new_files[0]
        same_gxm = (
            old["source_gxm"].get("status") == "FOUND"
            and new["source_gxm"].get("status") == "FOUND"
            and old["source_gxm"].get("sha256") == new["source_gxm"].get("sha256")
        )
        record: dict[str, Any] = {
            "family": family_display, "role": role,
            "rev131_path": old["path"], "rev131_sha256": old["sha256"],
            "rev135_path": new["path"], "rev135_sha256": new["sha256"],
            "source_gxm_9_3_1": old["source_gxm"],
            "source_gxm_9_10_0": new["source_gxm"],
            "source_gxm_byte_identical": bool(same_gxm),
        }
        if not same_gxm:
            record["status"] = "UNVERIFIED_SOURCE_PAIR"
            record["reason"] = (
                "source GXM is missing/ambiguous or SHA256 differs; filename pairing is not direct oracle evidence"
            )
            unverified_count += 1
            pairs.append(record)
            continue
        record["status"] = "VERIFIED_SAME_SOURCE"
        direct = _direct_prefix_oracle(
            (root / Path(old["path"])).read_bytes(),
            (root / Path(new["path"])).read_bytes(),
            f"{family_display}/{role}",
            old["source_gxm"]["sha256"],
            new["source_gxm"]["sha256"],
        )
        record["direct_draw_prefix_oracle"] = direct
        direct_formula_records += direct["draw_records_checked"]
        direct_formula_matches += direct["matches"]
        direct_formula_mismatches += direct.get("mismatch_count", len(direct.get("mismatches", [])))
        if direct["status"] == "UNRESOLVED":
            direct_unresolved += 1
        if direct["status"] == "PASS":
            converted = conversions.get(old["sha256"], {})
            for pattern in converted.get("draw_prefix_patterns", []):
                direct_pattern_counts[tuple(pattern)] += 1
        if old["sha256"] in conversion_bytes:
            try:
                record["minimal_candidate_vs_official_rev135"] = _candidate_comparison(
                    conversion_bytes[old["sha256"]],
                    (root / Path(new["path"])).read_bytes(),
                    f"{family_display}/{role}",
                )
            except Exception as exc:
                record["minimal_candidate_vs_official_rev135"] = {
                    "status": "UNRESOLVED",
                    "error_type": type(exc).__name__,
                    "error": _relative_message(exc, root),
                }
        else:
            record["minimal_candidate_vs_official_rev135"] = {
                "status": "NOT_AVAILABLE",
                "reason": "the unique rev131 payload did not convert successfully",
            }
        pairs.append(record)

    instance_pattern_counts: Counter[tuple[int, int, int, int, int]] = Counter()
    unique_pattern_counts: Counter[tuple[int, int, int, int, int]] = Counter()
    for item in instances:
        if item["revision"] == REVISION_131 and item["sha256"] in conversions:
            for pattern in conversions[item["sha256"]].get("draw_prefix_patterns", []):
                instance_pattern_counts[tuple(pattern)] += 1
    for conversion in conversions.values():
        if conversion["status"] == "PASS":
            for pattern in conversion["draw_prefix_patterns"]:
                unique_pattern_counts[tuple(pattern)] += 1
    all_patterns = sorted(set(instance_pattern_counts) | set(unique_pattern_counts))
    pattern_rows = []
    for pattern in all_patterns:
        direct_count = direct_pattern_counts[pattern]
        pattern_rows.append({
            "A_B_C": list(pattern[:3]),
            "X": pattern[3],
            "texture_slot_count": pattern[4],
            "file_instance_frequency": instance_pattern_counts[pattern],
            "unique_payload_frequency": unique_pattern_counts[pattern],
            "direct_oracle_occurrences": direct_count,
            "evidence_class": "DIRECTLY_ORACLED" if direct_count else "STRUCTURALLY_SUPPORTED_ONLY",
        })

    rev131_instances = [item for item in instances if item["revision"] == REVISION_131]
    rev135_instances = [item for item in instances if item["revision"] == REVISION_135]
    rev131_unique = [item for item in unique_payloads.values() if item["revision"] == REVISION_131]
    rev135_unique = [item for item in unique_payloads.values() if item["revision"] == REVISION_135]
    family_names = sorted(
        {item["family"] for item in instances if item["family"]}, key=str.casefold
    )
    all_draw_instances = sum(
        conversions[item["sha256"]].get("draw_records", 0)
        for item in rev131_instances
        if conversions.get(item["sha256"], {}).get("status") == "PASS"
    )
    unique_draw_records = sum(
        item.get("draw_records", 0)
        for item in conversions.values()
        if item.get("status") == "PASS"
    )
    conversion_rows = [conversions[key] for key in sorted(conversions)]
    successful = [item for item in conversion_rows if item["status"] == "PASS"]
    rejected = [item for item in conversion_rows if item["status"] != "PASS"]
    existing_rows = [existing_validation[key] for key in sorted(existing_validation)]
    unexpected_pair_diffs = [
        {
            "family": pair["family"], "role": pair["role"],
            "comparison": pair["minimal_candidate_vs_official_rev135"],
        }
        for pair in pairs
        if pair.get("status") == "VERIFIED_SAME_SOURCE"
        and pair.get("minimal_candidate_vs_official_rev135", {}).get("status")
        not in ("ONLY_LOCAL_INDEX_ORDER", "BYTE_IDENTICAL", "NOT_AVAILABLE")
    ]
    verified_pair_count = sum(pair.get("status") == "VERIFIED_SAME_SOURCE" for pair in pairs)
    return {
        "schema_version": 2,
        "phase": "R-COOKER2.1",
        "scan_root": root.name,
        "evidence_policy": {
            "runtime": "CONFIRMED_BY_RUNTIME only when generated SHA matches a runtime-tested Trooper or Forester candidate",
            "direct_bytes": "CONFIRMED_BY_BYTES only for a same-source GXM SHA pair with a verified draw alignment",
            "structural": "STRUCTURALLY_SUPPORTED for unique rev131 payloads converted and strictly revalidated without a direct pair",
        },
        "summary": {
            "vehicle_family_count": len(family_names),
            "vehicle_families": family_names,
            "dx_file_instances": len(instances),
            "unique_dx_payloads": len(unique_payloads),
            "rev131_file_instances": len(rev131_instances),
            "unique_rev131_payloads": len(rev131_unique),
            "rev135_file_instances": len(rev135_instances),
            "unique_rev135_payloads": len(rev135_unique),
            "unrecognized_or_invalid_dx_files": sum(
                item["status"] != "OK" or item["revision"] not in (131, 135)
                or item["family"] is None or item["generation"] is None
                for item in instances
            ),
            "unclassified_paths": sorted(
                (item["path"] for item in instances
                 if item["family"] is None or item["generation"] is None),
                key=str.casefold,
            ),
            "rev131_draw_record_instances": all_draw_instances,
            "rev131_draw_records_across_unique_payloads": unique_draw_records,
        },
        "file_instances": sorted(instances, key=lambda item: item["path"].casefold()),
        "unique_payloads": [unique_payloads[key] for key in sorted(unique_payloads)],
        "verified_same_source_pairs": [pair for pair in pairs if pair.get("status") == "VERIFIED_SAME_SOURCE"],
        "unverified_pairs": [pair for pair in pairs if pair.get("status") == "UNVERIFIED_SOURCE_PAIR"],
        "ambiguous_pairs": [pair for pair in pairs if pair.get("status") == "AMBIGUOUS_OUTPUT_INSTANCES"],
        "unpaired_files": sorted(unpaired, key=str.casefold),
        "pairing_summary": {
            "potential_unique_role_pairs": len(pairs),
            "verified_same_source_pairs": verified_pair_count,
            "unverified_pairs": unverified_count,
            "ambiguous_pairs": ambiguous_count,
            "draw_records_checked": direct_formula_records,
            "formula_matches": direct_formula_matches,
            "formula_mismatches": direct_formula_mismatches,
            "unresolved_direct_pairs": direct_unresolved,
            "pairs": pairs,
        },
        "draw_prefix_patterns": {
            "unique_abc_patterns": len({tuple(row["A_B_C"]) for row in pattern_rows}),
            "unique_X_values": len({row["X"] for row in pattern_rows}),
            "unique_texture_slot_counts": len({row["texture_slot_count"] for row in pattern_rows}),
            "unique_full_tuples": len(pattern_rows),
            "directly_oracled_unique_patterns": sum(
                row["evidence_class"] == "DIRECTLY_ORACLED" for row in pattern_rows
            ),
            "structurally_supported_only_unique_patterns": sum(
                row["evidence_class"] == "STRUCTURALLY_SUPPORTED_ONLY" for row in pattern_rows
            ),
            "patterns": pattern_rows,
        },
        "conversion_regression": {
            "unique_rev131_payloads_attempted": len(rev131_unique),
            "converted": sum(item["status"] == "PASS" for item in conversion_rows),
            "rejected": len(rejected),
            "failures": rejected,
            "unique_payload_results": conversion_rows,
            "runtime_confirmed_generated_payloads": sum(
                item.get("runtime_evidence") == "CONFIRMED_BY_RUNTIME" for item in successful
            ),
        },
        "existing_rev135_validation": {
            "unique_rev135_payloads_checked": len(rev135_unique),
            "accepted": sum(item["status"] in ("VALID", "VALID_WITH_ORDERING_DIVERGENCE") for item in existing_rows),
            "ordering_divergence": sum(item.get("ordering_divergence") is True for item in existing_rows),
            "rejected": [item for item in existing_rows if item["status"] == "REJECTED"],
            "unique_payload_results": existing_rows,
        },
        "official_rev135_comparison": {
            "verified_pairs_compared": sum(
                pair.get("minimal_candidate_vs_official_rev135", {}).get("status") != "NOT_AVAILABLE"
                for pair in pairs if pair.get("status") == "VERIFIED_SAME_SOURCE"
            ),
            "only_known_local_index_order": sum(
                pair.get("minimal_candidate_vs_official_rev135", {}).get("status") == "ONLY_LOCAL_INDEX_ORDER"
                for pair in pairs
            ),
            "byte_identical": sum(
                pair.get("minimal_candidate_vs_official_rev135", {}).get("status") == "BYTE_IDENTICAL"
                for pair in pairs
            ),
            "additional_or_unresolved_differences": unexpected_pair_diffs,
        },
        "dxt_policy": {
            "converted": False,
            "directory_mode": "DXT is not included or rewritten by the DX upgrader; package DXT resources remain outside the conversion output.",
            "prior_control": "R-COOKER1.1 and R-COOKER1.2 report their paired black-tga.dxt control byte-identical; no new DXT analysis is performed here.",
        },
    }


def render_corpus_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    pairing = report["pairing_summary"]
    patterns = report["draw_prefix_patterns"]
    conversion = report["conversion_regression"]
    official = report["official_rev135_comparison"]
    lines = [
        "# R-COOKER2.1 DX Corpus Coverage",
        "",
        "Generated deterministically from the ignored DX/GXM corpus. Paths are relative to the scan root.",
        "",
        "Regenerate with:",
        "",
        "~~~powershell",
        "python tools/scan_dx_131_135_corpus.py inputs --json research/r-cooker2/corpus-coverage.json --markdown research/r-cooker2/corpus-coverage.md",
        "~~~",
        "",
        "## Inventory",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Vehicle families | {summary['vehicle_family_count']} |",
        f"| DX file instances | {summary['dx_file_instances']} |",
        f"| Unique DX payloads | {summary['unique_dx_payloads']} |",
        f"| rev131 file instances | {summary['rev131_file_instances']} |",
        f"| Unique rev131 payloads | {summary['unique_rev131_payloads']} |",
        f"| rev135 file instances | {summary['rev135_file_instances']} |",
        f"| Unique rev135 payloads | {summary['unique_rev135_payloads']} |",
        f"| rev131 draw-record instances | {summary['rev131_draw_record_instances']} |",
        f"| Draw records across unique rev131 payloads | {summary['rev131_draw_records_across_unique_payloads']} |",
        "",
        "Families: " + ", ".join(summary["vehicle_families"]),
        "",
        "## Source-verified pairs",
        "",
        f"Verified same-GXM pairs: {pairing['verified_same_source_pairs']}; unverified filename pairs: {pairing['unverified_pairs']}; unpaired outputs: {len(report['unpaired_files'])}.",
        "",
        f"Direct paired draw records: {pairing['draw_records_checked']}; formula matches: {pairing['formula_matches']}; mismatches: {pairing['formula_mismatches']}.",
        "",
        "| Family | Role | rev131 source SHA256 | rev135 source SHA256 | Pair status | Direct records | Formula | Minimal candidate vs official |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for pair in report["pairing_summary"]["pairs"]:
        old_source = pair.get("source_gxm_9_3_1", {})
        new_source = pair.get("source_gxm_9_10_0", {})
        direct = pair.get("direct_draw_prefix_oracle", {})
        comparison = pair.get("minimal_candidate_vs_official_rev135", {})
        lines.append(
            f"| {pair['family']} | {pair['role']} | {old_source.get('sha256') or '—'} | "
            f"{new_source.get('sha256') or '—'} | {pair['status']} | "
            f"{direct.get('draw_records_checked', 0)} | {direct.get('status', '—')} | "
            f"{comparison.get('status', '—')} |"
        )
    lines += [
        "",
        "## Draw-prefix pattern coverage",
        "",
        f"Unique ABC: {patterns['unique_abc_patterns']}; unique X values: {patterns['unique_X_values']}; "
        f"unique slot counts: {patterns['unique_texture_slot_counts']}; unique full tuples: {patterns['unique_full_tuples']}.",
        "",
        "| A,B,C | X | Slots | File instances | Unique payloads | Direct oracle occurrences | Evidence |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in patterns["patterns"]:
        lines.append(
            f"| {','.join(str(value) for value in row['A_B_C'])} | {row['X']} | "
            f"{row['texture_slot_count']} | {row['file_instance_frequency']} | "
            f"{row['unique_payload_frequency']} | {row['direct_oracle_occurrences']} | "
            f"{row['evidence_class']} |"
        )
    lines += [
        "",
        "## Conversion regression",
        "",
        f"Unique rev131 payloads attempted: {conversion['unique_rev131_payloads_attempted']}; "
        f"converted: {conversion['converted']}; rejected: {conversion['rejected']}.",
        "",
        "Every successful unique payload was generated with the production converter and its strict generated-rev135 checks. Runtime confirmation is limited to generated hashes matching the Trooper or Forester runtime candidates.",
        "",
        "## Existing rev135 policy",
        "",
        f"Unique rev135 payloads checked: {report['existing_rev135_validation']['unique_rev135_payloads_checked']}; "
        f"accepted: {report['existing_rev135_validation']['accepted']}; "
        f"valid ordering divergences: {report['existing_rev135_validation']['ordering_divergence']}; "
        f"rejected: {len(report['existing_rev135_validation']['rejected'])}.",
        "",
        "The existing-input contract permits only the known local/global ordering divergence when each draw retains the same oriented triangle multiset. Generated output remains subject to exact local/global sequence agreement.",
        "",
        "## Minimal candidate vs official rev135",
        "",
        f"Verified pairs compared: {official['verified_pairs_compared']}; only local index order differs: "
        f"{official['only_known_local_index_order']}; byte-identical: {official['byte_identical']}; "
        f"additional/unresolved differences: {len(official['additional_or_unresolved_differences'])}.",
        "",
        "## Evidence scope",
        "",
        "- Trooper and Forester candidate hashes are runtime-confirmed.",
        "- Same-source draw-prefix mappings require byte-identical GXM source hashes.",
        "- Other accepted rev131 payloads are structurally supported only.",
        "- DXT is not converted by this tool.",
        "",
        "The JSON companion contains per-file hashes, source provenance, per-payload preservation checks, and pairwise comparison details.",
        "",
    ]
    return "\n".join(lines)


def write_corpus_reports(report: dict[str, Any], json_path: Path | str,
                         markdown_path: Path | str) -> None:
    """Write deterministic JSON and Markdown outputs."""
    json_path = Path(json_path)
    markdown_path = Path(markdown_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    # Write explicit UTF-8/LF bytes. Text-mode newline translation differs by
    # platform (notably Windows), which would otherwise make regeneration
    # byte-different despite identical report data.
    json_path.write_bytes(
        (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        .encode("utf-8")
    )
    markdown_path.write_bytes(render_corpus_markdown(report).encode("utf-8"))
