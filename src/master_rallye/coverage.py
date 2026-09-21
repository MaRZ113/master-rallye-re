"""Vehicle-only corpus scanner for the R1 extraction grammar."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .assets import AssetResolver
from .dx import parse_dx
from .errors import UnknownRecordTagError
from .sidecar import apply_material_candidates, parse_sidecar


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _winding_alignment(model) -> dict[str, int]:
    positive = negative = near_zero = 0
    positions = model.vertices.positions
    normals = model.vertices.normals
    for draw in model.physical_draws:
        indices = model.draw_global_indices(draw)
        for offset in range(0, len(indices), 3):
            ia, ib, ic = indices[offset:offset + 3]
            a, b, c = positions[ia], positions[ib], positions[ic]
            edge1 = tuple(b[axis] - a[axis] for axis in range(3))
            edge2 = tuple(c[axis] - a[axis] for axis in range(3))
            face = (
                edge1[1] * edge2[2] - edge1[2] * edge2[1],
                edge1[2] * edge2[0] - edge1[0] * edge2[2],
                edge1[0] * edge2[1] - edge1[1] * edge2[0],
            )
            average = tuple((normals[ia][axis] + normals[ib][axis] + normals[ic][axis]) / 3 for axis in range(3))
            dot = sum(face[axis] * average[axis] for axis in range(3))
            if dot > 1e-8:
                positive += 1
            elif dot < -1e-8:
                negative += 1
            else:
                near_zero += 1
    return {"aligned": positive, "opposed": negative, "near_zero": near_zero}


def _unknown_record(error: UnknownRecordTagError, relative_path: str) -> dict[str, Any]:
    evidence = error.evidence
    return {
        "file": relative_path,
        "offset": f"0x{evidence.offset:X}",
        "tag": evidence.tag,
        "context_start": f"0x{evidence.context_start:X}",
        "surrounding_bytes": evidence.context_hex,
        "context": "draw-table physical record stream",
        "nearest_preceding_known_structure": evidence.preceding_context,
        "nearest_following_known_structure": "unknown; parsing stopped without guessing",
    }


def scan_vehicle_corpus(vehicle_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = vehicle_root.resolve()
    files = sorted(root.rglob("*.dx"), key=lambda path: path.as_posix().lower())
    records: list[dict[str, Any]] = []
    unknown_records: list[dict[str, Any]] = []

    for path in files:
        relative = _relative(path, root)
        sidecar_path = path.with_suffix(".txt")
        try:
            model = parse_dx(path)
            sidecar = parse_sidecar(sidecar_path) if sidecar_path.exists() else None
            apply_material_candidates(model.physical_draws, sidecar)
            resolver = AssetResolver(path.parent)

            unique_matches = 0
            ambiguous: list[dict[str, Any]] = []
            unmatched: list[int] = []
            missing_textures: list[dict[str, Any]] = []
            slot_counts = Counter()
            for draw in model.physical_draws:
                candidates = draw.material_candidates
                if len(candidates) == 1:
                    unique_matches += 1
                elif len(candidates) > 1:
                    ambiguous.append({
                        "draw_index": draw.draw_index,
                        "record_path": draw.record_path,
                        "candidates": [
                            {"number": item.number, "name": item.name} for item in candidates
                        ],
                    })
                else:
                    unmatched.append(draw.draw_index if draw.draw_index is not None else -1)
                slot_counts[len(draw.texture_slots)] += 1
                for slot in draw.texture_slots:
                    if slot.value.lower() != "null" and resolver.resolve_texture(slot.value) is None:
                        missing_textures.append({
                            "draw_index": draw.draw_index,
                            "slot": slot.slot,
                            "value": slot.value,
                        })

            warnings = list(model.diagnostics.warnings)
            if model.trailing.layout_family == "opaque":
                warnings.append(f"opaque trailing data: {len(model.trailing.data)} bytes")
            validated = model.diagnostics.validated
            fully_accounted = validated and model.trailing.layout_family in {"none", "footer56-bounds"}
            accounting = "FULLY_ACCOUNTED" if fully_accounted else "PARTIALLY_ACCOUNTED"
            stages = ["PARSED"]
            if validated:
                stages.append("VALIDATED")
            stages.append(accounting)
            trailing = {
                "byte_count": len(model.trailing.data),
                "layout_family": model.trailing.layout_family,
                "sha256": model.trailing.sha256,
                "recognized_footer": model.trailing.bounding is not None,
            }
            if model.trailing.bounding is not None:
                bounding = model.trailing.bounding
                trailing["bounding"] = {
                    "unknown_0x00_u32": bounding.unknown_0x00_u32,
                    "unknown_0x04_float": bounding.unknown_0x04_float,
                    "unknown_0x08_float": bounding.unknown_0x08_float,
                    "unknown_0x0C_u32": bounding.unknown_0x0c_u32,
                    "midpoint": list(bounding.midpoint),
                    "unknown_0x1C_float": bounding.unknown_0x1c_float,
                    "minimum": list(bounding.minimum),
                    "maximum": list(bounding.maximum),
                    "matches_positions": bounding.matches_positions,
                }
            records.append({
                "path": relative,
                "resource_type": path.stem.lower(),
                "byte_size": model.byte_size,
                "status": accounting,
                "stages": stages,
                "parsed": True,
                "validated": validated,
                "fully_accounted": fully_accounted,
                "vertex_count": model.vertex_count,
                "uv_set_count": len(model.uv_sets),
                "local_index_count": len(model.local_indices),
                "triangle_count": model.triangle_count,
                "declared_top_level_record_count": model.declared_top_level_record_count,
                "reconstructed_root_count": len(model.draw_groups),
                "physical_draw_count": len(model.physical_draws),
                "record_tags": model.record_tags,
                "group_labels": model.group_labels,
                "texture_slot_counts": {str(key): value for key, value in sorted(slot_counts.items())},
                "stored_global_indices": model.global_index_table is not None,
                "stored_global_index_count": model.global_index_table.count if model.global_index_table else None,
                "reconstructed_indices_exact_match": (
                    model.global_index_table.reconstructed_match if model.global_index_table else False
                ),
                "compared_global_index_count": (
                    model.global_index_table.compared_index_count if model.global_index_table else 0
                ),
                "local_index_coverage": model.diagnostics.index_coverage,
                "vertex_range_coverage": model.diagnostics.vertex_coverage,
                "uncovered_index_count": model.diagnostics.uncovered_index_count,
                "overlapping_index_count": model.diagnostics.overlapping_index_count,
                "unused_vertex_count": model.diagnostics.unused_vertex_count,
                "shared_vertex_count": model.diagnostics.shared_vertex_count,
                "sidecar_present": sidecar is not None,
                "sidecar_material_count": sidecar.declared_material_count if sidecar else None,
                "material_match_count": unique_matches + len(ambiguous),
                "unique_material_match_count": unique_matches,
                "ambiguous_material_matches": ambiguous,
                "unmatched_draw_records": unmatched,
                "missing_texture_references": missing_textures,
                "winding_against_vertex_normals": _winding_alignment(model),
                "trailing": trailing,
                "parser_warnings": warnings,
                "parser_failure": None,
            })
        except UnknownRecordTagError as error:
            unknown_records.append(_unknown_record(error, relative))
            records.append({
                "path": relative,
                "resource_type": path.stem.lower(),
                "byte_size": path.stat().st_size,
                "status": "FAILED",
                "stages": ["FAILED"],
                "parsed": False,
                "validated": False,
                "fully_accounted": False,
                "sidecar_present": sidecar_path.exists(),
                "parser_warnings": [],
                "parser_failure": {"type": type(error).__name__, "message": str(error)},
            })
        except Exception as error:
            records.append({
                "path": relative,
                "resource_type": path.stem.lower(),
                "byte_size": path.stat().st_size,
                "status": "FAILED",
                "stages": ["FAILED"],
                "parsed": False,
                "validated": False,
                "fully_accounted": False,
                "sidecar_present": sidecar_path.exists(),
                "parser_warnings": [],
                "parser_failure": {"type": type(error).__name__, "message": str(error)},
            })

    status_counts = Counter(record["status"] for record in records)
    tag_frequency = Counter()
    trailing_by_type: dict[str, Counter] = defaultdict(Counter)
    trailing_sizes = Counter()
    for record in records:
        for tag in record.get("record_tags", []):
            tag_frequency[tag] += 1
        trailing = record.get("trailing")
        if trailing:
            trailing_by_type[record["resource_type"]][trailing["layout_family"]] += 1
            trailing_sizes[trailing["byte_count"]] += 1

    summary = {
        "total_dx": len(records),
        "parsed": sum(record["parsed"] for record in records),
        "validated": sum(record["validated"] for record in records),
        "fully_accounted": status_counts["FULLY_ACCOUNTED"],
        "partially_accounted": status_counts["PARTIALLY_ACCOUNTED"],
        "failed": status_counts["FAILED"],
        "sidecar_present": sum(record.get("sidecar_present", False) for record in records),
        "stored_global_indices": sum(record.get("stored_global_indices", False) for record in records),
        "exact_global_matches": sum(record.get("reconstructed_indices_exact_match", False) for record in records),
        "record_tag_file_frequency": {str(key): value for key, value in sorted(tag_frequency.items())},
        "trailing_layout_by_resource_type": {
            resource_type: dict(sorted(counter.items()))
            for resource_type, counter in sorted(trailing_by_type.items())
        },
        "trailing_byte_count_frequency": {
            str(key): value for key, value in sorted(trailing_sizes.items())
        },
        "ambiguous_draws": sum(len(record.get("ambiguous_material_matches", [])) for record in records),
        "unmatched_draws": sum(len(record.get("unmatched_draw_records", [])) for record in records),
        "missing_texture_references": sum(len(record.get("missing_texture_references", [])) for record in records),
        "unknown_record_count": len(unknown_records),
        "winding_against_vertex_normals": {
            key: sum(record.get("winding_against_vertex_normals", {}).get(key, 0) for record in records)
            for key in ("aligned", "opposed", "near_zero")
        },
        "declared_root_count_mismatches": sum(
            record.get("declared_top_level_record_count") != record.get("reconstructed_root_count")
            for record in records if record.get("parsed")
        ),
    }
    generated = datetime.now(timezone.utc).isoformat()
    report = {
        "schema_version": 1,
        "generated_utc": generated,
        "source_descriptor": "external DataGx/Vehicles root (path intentionally omitted)",
        "status_definitions": {
            "PARSED": "known structural sections reached a valid stopping point",
            "VALIDATED": "draw geometry is internally consistent and stored global indices match",
            "FULLY_ACCOUNTED": "validated geometry plus no opaque trailing section",
            "PARTIALLY_ACCOUNTED": "validated known geometry with opaque trailing data",
            "FAILED": "structural parser could not safely continue",
        },
        "summary": summary,
        "files": records,
    }
    unknown = {
        "schema_version": 1,
        "generated_utc": generated,
        "record_count": len(unknown_records),
        "records": unknown_records,
    }
    return report, unknown


def coverage_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# R1 vehicle corpus coverage",
        "",
        "All paths are relative to the external `DataGx/Vehicles` tree.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Total DX | {summary['total_dx']} |",
        f"| Parsed | {summary['parsed']} |",
        f"| Validated | {summary['validated']} |",
        f"| Fully accounted | {summary['fully_accounted']} |",
        f"| Partially accounted | {summary['partially_accounted']} |",
        f"| Failed | {summary['failed']} |",
        f"| Exact stored-global matches | {summary['exact_global_matches']} |",
        f"| Unknown record tags | {summary['unknown_record_count']} |",
        f"| Declared/root count mismatches | {summary['declared_root_count_mismatches']} |",
        "",
        "## Record variants",
        "",
        "File frequency by encountered tag: "
        + ", ".join(f"tag {tag}: {count}" for tag, count in summary["record_tag_file_frequency"].items())
        + ".",
        "",
        "## Trailing layouts",
        "",
        "| Resource type | footer56-bounds | opaque |",
        "|---|---:|---:|",
    ]
    for resource_type, counts in summary["trailing_layout_by_resource_type"].items():
        lines.append(
            f"| `{resource_type}` | {counts.get('footer56-bounds', 0)} | {counts.get('opaque', 0)} |"
        )
    lines.extend([
        "",
        "Opaque byte-count frequency: "
        + ", ".join(f"{size}: {count}" for size, count in summary["trailing_byte_count_frequency"].items() if size != "56")
        + ".",
        "",
        "## Material diagnostics",
        "",
        f"- Ambiguous draw matches: {summary['ambiguous_draws']}.",
        f"- Unmatched draws: {summary['unmatched_draws']}.",
        f"- Missing referenced texture resources: {summary['missing_texture_references']}.",
        "- Matching uses normalized ordered texture tuples padded with `Null` to the binary tuple width.",
        "",
        "## Interpretation",
        "",
        "`FULLY_ACCOUNTED` is intentionally stricter than parser success. Opaque trailing data makes a file",
        "`PARTIALLY_ACCOUNTED` even when every draw and stored global index validates exactly.",
        "",
        "Reconstructed winding versus stored vertex normals: "
        + ", ".join(
            f"{key} {value}" for key, value in summary["winding_against_vertex_normals"].items()
        )
        + ".",
    ])
    return "\n".join(lines) + "\n"


def write_coverage_reports(
    vehicle_root: Path,
    json_path: Path,
    markdown_path: Path,
    unknown_path: Path,
) -> dict[str, Any]:
    report, unknown = scan_vehicle_corpus(vehicle_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(coverage_markdown(report), encoding="utf-8")
    unknown_path.write_text(json.dumps(unknown, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
