#!/usr/bin/env python3
"""Audit read-only vehicle DX corpora across supported source revisions."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _role(path: Path) -> str:
    return {
        "car.dx": "RACE BODY",
        "complete.dx": "PRESENTATION",
        "wheel.dx": "WHEEL TEMPLATE",
    }.get(path.name.casefold(), "AUXILIARY")


def _source_provenance(label: str, relative: Path, revision: int | None) -> str:
    first = relative.parts[0] if relative.parts else ""
    lowered = first.casefold()
    if label.casefold() == "retail":
        return "retail corpus path"
    if lowered.startswith(("8.4.1", "9.3.1", "9.10.0")):
        return f"directory-tagged {first}; cooker identity not independently encoded"
    if lowered == "!other_research" and len(relative.parts) > 1:
        return f"research directory {relative.parts[1]}; cooker identity not independently encoded"
    return f"{label} input; build family UNKNOWN for revision {revision}"


def _directory_group(label: str, relative: Path) -> str:
    """Return an input-path group without inferring a cooker identity."""
    parts = relative.parts
    if not parts:
        return "(root)"
    if label.casefold() == "retail":
        return parts[0]
    if parts[0].casefold() == "!other_research" and len(parts) > 1:
        return parts[1]
    return parts[0]


def _scan_root(label: str, root: Path) -> list[dict]:
    if not root.is_dir():
        raise ValueError(f"source root is not a directory: {root}")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from master_rallye.dx import analyze_global_index_consistency, parse_dx

    rows = []
    for path in sorted(root.rglob("*.dx"), key=lambda value: value.relative_to(root).as_posix().casefold()):
        relative = path.relative_to(root)
        revision = None
        try:
            header = path.open("rb")
            try:
                header_bytes = header.read(8)
            finally:
                header.close()
            if len(header_bytes) == 8:
                revision = int.from_bytes(header_bytes[4:8], "little")
            model = parse_dx(path)
            consistency = analyze_global_index_consistency(model)
            texture_names = list(dict.fromkeys(
                slot.value for draw in model.physical_draws for slot in draw.texture_slots
            ))
            rows.append({
                "source_set": label,
                "source": relative.as_posix(),
                "directory_group": _directory_group(label, relative),
                "provenance": _source_provenance(label, relative, model.dx_revision),
                "build_family": "UNKNOWN",
                "revision": model.dx_revision,
                "role": _role(path),
                "parse_status": "PASS",
                "vertices": model.vertex_count,
                "triangles": model.triangle_count,
                "draws": len(model.physical_draws),
                "uv_sets": len(model.uv_sets),
                "texture_slots": texture_names,
                "texture_slot_count": len(texture_names),
                "index_sequence_equal": consistency["index_sequence_equal"],
                "oriented_triangle_sets_equal": consistency[
                    "oriented_triangle_sets_equal_per_draw"
                ],
                "mismatch_positions": consistency["mismatch_position_count"],
                "first_mismatch_position": consistency["first_mismatch_position"],
                "index_coverage": consistency["index_coverage"],
                "vertex_coverage": consistency["vertex_coverage"],
                "structural_import_valid": consistency["structural_import_valid"],
                "exact_generated_valid": consistency["exact_generated_valid"],
                "validation_profile": consistency["validation_profile"],
                "collision_tags": list(model.collision.tag_ids),
                "collision_validated": model.collision.validated,
                "collision_warnings": list(model.collision.warnings),
                "collision_errors": list(model.collision.errors),
                "warnings": list(model.diagnostics.warnings),
                "errors": list(model.diagnostics.errors),
            })
        except Exception as error:
            rows.append({
                "source_set": label,
                "source": relative.as_posix(),
                "directory_group": _directory_group(label, relative),
                "provenance": _source_provenance(label, relative, revision),
                "build_family": "UNKNOWN",
                "revision": revision,
                "role": _role(path),
                "parse_status": "FAIL",
                "error": f"{type(error).__name__}: {error}",
            })
    return rows


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _rev135_markdown(rows: list[dict], summary: dict) -> str:
    lines = [
        "# Revision 135 vehicle DX index-ordering audit",
        "",
        "This report separates exact local/global sequence equality from per-draw oriented topology equivalence.",
        "Build family is not inferred from revision. Directory provenance is retained as a label.",
        "",
        "## Summary",
        "",
        f"- Revision 135 resources parsed: {summary['resource_count']}",
        f"- Exact sequence: {summary['exact_sequence_count']}",
        f"- Structurally valid ordering divergence: {summary['ordering_divergence_count']}",
        f"- Structural failures: {summary['structural_failure_count']}",
        "",
        "## By source set",
        "",
        "| Source set | Files | Exact | Order-equivalent | Structural failures |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in sorted(summary["by_source_set"]):
        item = summary["by_source_set"][label]
        lines.append(
            f"| {label} | {item['files']} | {item['exact']} | "
            f"{item['ordering_divergence']} | {item['structural_failures']} |"
        )
    lines.extend([
        "",
        "## By directory group",
        "",
        "Directory labels organize the supplied files; they do not prove which cooker produced them.",
        "",
        "| Source set | Directory group | Files | Exact | Order-equivalent | Structural failures |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for key, item in sorted(summary["by_directory_group"].items()):
        source_set, directory_group = key.split("/", 1)
        lines.append(
            f"| {source_set} | `{directory_group}` | {item['files']} | {item['exact']} | "
            f"{item['ordering_divergence']} | {item['structural_failures']} |"
        )
    lines.extend([
        "",
        "## Resources",
        "",
        "| Source set | Directory group | Resource | Role | Vertices | Triangles | Draws | Sequence | Topology | Mismatches | First | Index coverage | Collision |",
        "|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---|---|",
    ])
    for row in rows:
        sequence = "exact" if row["index_sequence_equal"] else "diverged"
        topology = "equal" if row["oriented_triangle_sets_equal"] else "different"
        collision = ", ".join(map(str, row["collision_tags"])) or "none"
        first = "—" if row["first_mismatch_position"] is None else f"0x{row['first_mismatch_position']:X}"
        lines.append(
            f"| {row['source_set']} | `{row['directory_group']}` | `{row['source']}` | {row['role']} | {row['vertices']} | "
            f"{row['triangles']} | {row['draws']} | {sequence} | {topology} | "
            f"{row['mismatch_positions']} | {first} | {row['index_coverage']} | {collision} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Only resources with complete disjoint draw coverage and matching per-draw oriented triangle multisets are classified as `VALID_WITH_INDEX_ORDERING_DIVERGENCE`.",
        "A row with a topology mismatch, invalid range, or coverage failure remains structurally invalid.",
        "The cooker identity is not encoded in the revision field; source directory names are evidence labels only.",
        "",
    ])
    return "\n".join(lines)


def _matrix_markdown(rows: list[dict], summary: dict) -> str:
    lines = [
        "# Multi-revision vehicle DX corpus matrix",
        "",
        "Read-only parse inventory. Revision is a file fact; build family remains UNKNOWN unless the input path independently labels it.",
        "",
        "| Source set | Directory group | Resource | Revision | Role | Parse | Vertices | Triangles | Draws | UV | Texture refs | Index profile | Collision tags | Warnings |",
        "|---|---|---|---:|---|---|---:|---:|---:|---:|---:|---|---|---:|",
    ]
    for row in rows:
        if row["parse_status"] == "PASS":
            warnings = len(row["warnings"]) + len(row["collision_warnings"])
            textures = ", ".join(f"`{name}`" for name in row["texture_slots"])
            lines.append(
                f"| {row['source_set']} | `{row['directory_group']}` | `{row['source']}` | {row['revision']} | {row['role']} | PASS | "
                f"{row['vertices']} | {row['triangles']} | {row['draws']} | {row['uv_sets']} | {textures} | "
                f"{row['validation_profile']} | {', '.join(map(str, row['collision_tags'])) or 'none'} | {warnings} |"
            )
        else:
            lines.append(
                f"| {row['source_set']} | `{row['directory_group']}` | `{row['source']}` | {row['revision'] or 'unknown'} | "
                f"{row['role']} | FAIL | — | — | — | — | — | — | — | — |"
            )
    lines.extend([
        "",
        "## Summary",
        "",
        f"- Resources: {summary['resource_count']}",
        f"- Parsed: {summary['parsed_count']}",
        f"- Unsupported or malformed: {summary['parse_failure_count']}",
        "",
    ])
    for revision in sorted(summary["by_revision"], key=lambda value: (value is None, value or 0)):
        label = "unknown" if revision is None else str(revision)
        lines.append(f"- Revision {label}: {summary['by_revision'][revision]}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", action="append", required=True, metavar="LABEL=PATH",
        help="read-only vehicle root; repeat to audit multiple source sets",
    )
    parser.add_argument("--revision135-json", type=Path, required=True)
    parser.add_argument("--revision135-md", type=Path, required=True)
    parser.add_argument("--matrix-json", type=Path, required=True)
    parser.add_argument("--matrix-md", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    for item in args.source:
        if "=" not in item:
            parser.error(f"source must be LABEL=PATH: {item}")
        label, raw_path = item.split("=", 1)
        if not label:
            parser.error(f"empty source label: {item}")
        rows.extend(_scan_root(label, Path(raw_path).resolve()))

    by_revision = Counter(row["revision"] for row in rows)
    parse_failures = [row for row in rows if row["parse_status"] != "PASS"]
    matrix_summary = {
        "resource_count": len(rows),
        "parsed_count": len(rows) - len(parse_failures),
        "parse_failure_count": len(parse_failures),
        "by_revision": dict(by_revision),
    }
    directory_counts = defaultdict(Counter)
    for row in rows:
        counts = directory_counts[(row["source_set"], row["directory_group"])]
        counts["files"] += 1
        if row["parse_status"] == "PASS":
            counts["parsed"] += 1
            counts[f"revision_{row['revision']}"] += 1
            counts[row["validation_profile"]] += 1
        else:
            counts["parse_failures"] += 1
    matrix_summary["by_directory_group"] = {
        f"{source_set}/{directory_group}": dict(counts)
        for (source_set, directory_group), counts in sorted(directory_counts.items())
    }
    matrix_payload = {
        "schema_version": 1,
        "sources": [item.split("=", 1)[0] for item in args.source],
        "summary": matrix_summary,
        "resources": rows,
    }

    rev135_rows = [
        row for row in rows
        if row["parse_status"] == "PASS" and row["revision"] == 135
    ]
    by_source = defaultdict(lambda: Counter())
    by_directory_group = defaultdict(lambda: Counter())
    for row in rev135_rows:
        for counts in (
            by_source[row["source_set"]],
            by_directory_group[(row["source_set"], row["directory_group"])],
        ):
            counts["files"] += 1
            if row["index_sequence_equal"]:
                counts["exact"] += 1
            elif row["structural_import_valid"] and row["oriented_triangle_sets_equal"]:
                counts["ordering_divergence"] += 1
            else:
                counts["structural_failures"] += 1
    rev135_summary = {
        "resource_count": len(rev135_rows),
        "exact_sequence_count": sum(row["index_sequence_equal"] for row in rev135_rows),
        "ordering_divergence_count": sum(
            not row["index_sequence_equal"]
            and row["structural_import_valid"]
            and row["oriented_triangle_sets_equal"]
            for row in rev135_rows
        ),
        "structural_failure_count": sum(
            not row["structural_import_valid"] for row in rev135_rows
        ),
        "by_source_set": {
            label: {key: counts.get(key, 0) for key in (
                "files", "exact", "ordering_divergence", "structural_failures"
            )}
            for label, counts in sorted(by_source.items())
        },
        "by_directory_group": {
            f"{source_set}/{directory_group}": {
                key: counts.get(key, 0)
                for key in ("files", "exact", "ordering_divergence", "structural_failures")
            }
            for (source_set, directory_group), counts in sorted(by_directory_group.items())
        },
    }
    rev135_payload = {
        "schema_version": 1,
        "validation_model": {
            "exact": "EXACT_SEQUENCE",
            "structural_import": "STRUCTURALLY_EQUIVALENT_ORDERING",
            "triangle_comparison": "per-draw oriented multiset; cyclic rotations accepted; reverse winding rejected",
        },
        "summary": rev135_summary,
        "resources": rev135_rows,
    }

    _write_json(args.matrix_json, matrix_payload)
    _write_json(args.revision135_json, rev135_payload)
    args.matrix_md.parent.mkdir(parents=True, exist_ok=True)
    args.matrix_md.write_bytes(_matrix_markdown(rows, matrix_summary).encode("utf-8"))
    args.revision135_md.parent.mkdir(parents=True, exist_ok=True)
    args.revision135_md.write_bytes(_rev135_markdown(rev135_rows, rev135_summary).encode("utf-8"))
    print(json.dumps({"matrix": matrix_summary, "revision135": rev135_summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
