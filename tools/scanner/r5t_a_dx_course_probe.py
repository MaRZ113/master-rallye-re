"""Probe the vehicle DX parser and the bounded R5T-A course DX reader."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import struct
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from master_rallye.dx import parse_dx, parse_dx_common_prefix  # noqa: E402
from master_rallye.dx_course import parse_course_dx  # noqa: E402
from master_rallye.sidecar import parse_sidecar  # noqa: E402


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def error_offset(message: str) -> int | None:
    match = re.search(r"\bat 0x([0-9A-Fa-f]+)", message)
    return int(match.group(1), 16) if match else None


def probe(path: Path, data_root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    record: dict[str, Any] = {
        "resource": path.relative_to(data_root).as_posix(),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "magic": f"0x{struct.unpack_from('<I', data, 0)[0]:08X}" if len(data) >= 4 else None,
        "revision": struct.unpack_from("<I", data, 4)[0] if len(data) >= 8 else None,
        "first_16_hex": data[:16].hex(" "),
    }
    try:
        prefix = parse_dx_common_prefix(data, path.name)
        record["common_prefix"] = {
            "status": "parsed",
            "vertex_count": len(prefix.vertices.positions),
            "normal_count": len(prefix.vertices.normals),
            "color_bytes": len(prefix.vertices.colors),
            "uv_set_count": len(prefix.uv_sets),
            "local_index_count": len(prefix.local_indices),
            "local_triangle_count": len(prefix.local_indices) // 3,
            "draw_table_offset": prefix.draw_table_offset,
            "draw_table_offset_hex": f"0x{prefix.draw_table_offset:X}",
            "draw_envelope_hex": data[prefix.draw_table_offset:prefix.draw_table_offset + 32].hex(" "),
        }
    except Exception as error:
        record["common_prefix"] = {
            "status": "failed",
            "error_type": type(error).__name__,
            "error": str(error),
        }
        record["vehicle_parser"] = {"status": "not-reached"}
        record["course_parser"] = {"status": "not-reached"}
        return record

    try:
        vehicle = parse_dx(path)
        record["vehicle_parser"] = {
            "status": "parsed",
            "draw_count": len(vehicle.physical_draws),
            "triangle_count": vehicle.triangle_count,
            "validation_errors": list(vehicle.diagnostics.errors),
            "trailing_offset": vehicle.trailing.offset,
            "trailing_size": len(vehicle.trailing.data),
            "trailing_family": vehicle.trailing.layout_family,
            "collision_tags": list(vehicle.collision.tag_ids),
        }
    except Exception as error:
        offset = error_offset(str(error))
        record["vehicle_parser"] = {
            "status": "unsupported",
            "error_type": type(error).__name__,
            "error": str(error),
            "first_divergence_offset": offset,
            "first_divergence_offset_hex": f"0x{offset:X}" if offset is not None else None,
            "expected_at_first_divergence": "vehicle draw record tag in {2, 7, 8}",
            "observed_at_first_divergence": (
                struct.unpack_from("<I", data, offset)[0] if offset is not None and offset + 4 <= len(data) else None
            ),
        }

    try:
        course = parse_course_dx(path)
        sidecar_path = path.with_suffix(".txt")
        sidecar = parse_sidecar(sidecar_path) if sidecar_path.is_file() else None
        texture_refs = sorted({
            slot.value
            for draw in course.physical_draws
            for slot in draw.texture_slots
            if slot.value.casefold() != "null"
        })
        record["course_parser"] = {
            "status": "parsed" if course.course_render_validated else "invalid",
            "grammar": "revision-135 root records and sequential draw batches; shared tag-2/7/8 draws; raw course wrappers 1/4/5/6",
            "wrapper": {
                "present": course.course_wrapper is not None,
                "offset": course.course_wrapper.offset if course.course_wrapper else None,
                "tag": course.course_wrapper.tag if course.course_wrapper else None,
                "control_words": list(course.course_wrapper.control_words) if course.course_wrapper else [],
                "parsed_child_count": course.course_wrapper.child_count if course.course_wrapper else None,
                "direct_root_record_count": len(course.course_root_records),
            },
            "vertex_count": course.vertex_count,
            "uv_set_count": len(course.uv_sets),
            "local_index_count": len(course.local_indices),
            "triangle_count": course.triangle_count,
            "draw_count": len(course.physical_draws),
            "draw_record_tag_counts": dict(Counter(draw.tag for draw in course.physical_draws)),
            "batch_count": len(course.course_batches),
            "batch_record_counts": [batch.record_count for batch in course.course_batches],
            "texture_slot_reference_count": sum(len(draw.texture_slots) for draw in course.physical_draws),
            "unique_texture_references": texture_refs,
            "sidecar": {
                "present": sidecar is not None,
                "declared_material_count": sidecar.declared_material_count if sidecar else None,
                "material_count": len(sidecar.materials) if sidecar else 0,
                "mesh_count": len(sidecar.meshes) if sidecar else 0,
                "mesh_span": sidecar.mesh_span if sidecar else 0,
            },
            "trailing": {
                "offset": course.trailing.offset,
                "size": len(course.trailing.data),
                "layout_family": course.trailing.layout_family,
            },
            "collision": {
                "structurally_detected_tags": list(course.collision.tag_ids),
                "tag100": (
                    {
                        "offset": course.collision.bsp.tag_offset,
                        "end_offset": course.collision.bsp.end_offset,
                        "status": course.collision.bsp.status,
                        "sha256": course.collision.bsp.sha256,
                    }
                    if course.collision.bsp else None
                ),
                "tag101": course.collision.convex_hull is not None,
                "tag102": course.collision.cylinder is not None,
            },
            "render_validation": {
                "passed": course.course_render_validated,
                "index_coverage": course.diagnostics.index_coverage,
                "vertex_coverage": course.diagnostics.vertex_coverage,
                "errors": list(course.diagnostics.errors),
                "warnings": list(course.diagnostics.warnings),
            },
        }
    except Exception as error:
        offset = error_offset(str(error))
        record["course_parser"] = {
            "status": "unsupported",
            "error_type": type(error).__name__,
            "error": str(error),
            "first_unsupported_offset": offset,
            "first_unsupported_offset_hex": f"0x{offset:X}" if offset is not None else None,
            "draw_envelope_hex": record["common_prefix"]["draw_envelope_hex"],
            "collision_tag_status": "not-structurally-reached",
        }
    return record


def markdown_report(report: dict[str, Any]) -> str:
    records = report["resources"]
    course_status = Counter(item["course_parser"]["status"] for item in records)
    vehicle_status = Counter(item["vehicle_parser"]["status"] for item in records)
    lines = [
        "# R5T-A course DX parser probe",
        "",
        "The current vehicle parser was run unchanged against every retail `DataGx/Course/*/*.dx` resource. The additive course reader reuses the shared DX arrays and draw-record parser, then follows the observed revision-135 root records, repeated draw batches, and course wrapper records.",
        "",
        f"- Retail course DX files: **{len(records)}**",
        f"- Shared common-prefix success: **{sum(item['common_prefix']['status'] == 'parsed' for item in records)}**",
        f"- Current vehicle-parser status: **{dict(vehicle_status)}**",
        f"- Course-parser status: **{dict(course_status)}**",
        "- Every course parse requires complete, disjoint local-index and vertex-range coverage; course tails are handed to the shared optional-section boundary reader.",
        "",
        "| Resource | Revision | Vertices | Local triangles | Vehicle parser | First divergence | Course parser | Draws |",
        "|---|---:|---:|---:|---|---|---|---:|",
    ]
    for item in records:
        prefix = item["common_prefix"]
        course = item["course_parser"]
        vehicle = item["vehicle_parser"]
        lines.append(
            f"| `{item['resource']}` | {item.get('revision')} | "
            f"{prefix.get('vertex_count', '—')} | {prefix.get('local_triangle_count', '—')} | "
            f"{vehicle['status']} | {vehicle.get('first_divergence_offset_hex', '—')} | "
            f"{course['status']} | {course.get('draw_count', '—')} |"
        )
    lines.extend([
        "",
        "## Unsupported structures",
        "",
    ])
    unsupported = [item for item in records if item["course_parser"]["status"] != "parsed"]
    if not unsupported:
        lines.append("None.")
    for item in unsupported:
        course = item["course_parser"]
        lines.append(
            f"- `{item['resource']}`: `{course['error_type']}` at "
            f"{course.get('first_unsupported_offset_hex') or 'unknown offset'}: {course['error']}"
        )
        lines.append(f"  Draw envelope: `{course.get('draw_envelope_hex', '')}`")
    lines.extend([
        "",
        "A `tag100`/`tag101`/`tag102` result is listed only when reached through the parsed course tail. Raw byte coincidences are not counted as tags.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT.parent / "corpora" / "retail" / "Data.sma_unpacked")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "research" / "r5t_a")
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    course_root = data_root / "DataGx" / "Course"
    paths = sorted(course_root.glob("*/*.dx"), key=lambda item: item.as_posix().casefold())
    report = {
        "schema": "r5t-a-dx-course-probe-v1",
        "corpus_label": "corpora/retail/Data.sma_unpacked",
        "resource_count": len(paths),
        "resources": [probe(path, data_root) for path in paths],
    }
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "dx-course-probe.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "dx-course-probe.md").write_text(markdown_report(report), encoding="utf-8", newline="\n")
    print(json.dumps({
        "resource_count": len(paths),
        "common_prefix_success": sum(item["common_prefix"]["status"] == "parsed" for item in report["resources"]),
        "course_parse_success": sum(item["course_parser"]["status"] == "parsed" for item in report["resources"]),
        "vehicle_parser_success": sum(item["vehicle_parser"]["status"] == "parsed" for item in report["resources"]),
        "json": str(json_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
