"""Read-only corpus and geometry analysis for DX collision sections."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collision import CollisionGeometryBlock, ConvexHullRepresentation
from .dx import parse_dx
from .sidecar import parse_sidecar


def _aabb(vertices):
    if not vertices:
        return None
    return {
        "minimum": [min(value[axis] for value in vertices) for axis in range(3)],
        "maximum": [max(value[axis] for value in vertices) for axis in range(3)],
    }


def _distance(left, right) -> float:
    return math.sqrt(sum((left[index] - right[index]) ** 2 for index in range(3)))


def _triangle_edges(triangles):
    counts: dict[tuple[int, int], int] = {}
    for triangle in triangles:
        for left, right in ((triangle[0], triangle[1]), (triangle[1], triangle[2]), (triangle[2], triangle[0])):
            edge = tuple(sorted((left, right)))
            counts[edge] = counts.get(edge, 0) + 1
    return counts


def _closed_geometry(geometry: CollisionGeometryBlock) -> dict[str, Any]:
    edges = _triangle_edges(geometry.triangles)
    closed = bool(edges) and all(count == 2 for count in edges.values())
    euler = geometry.vertex_count - len(edges) + geometry.triangle_count
    convex = True
    # Float32 hull construction leaves one measured Frontera supporting-plane
    # deviation at 2.98e-5 source units; 5e-5 remains tiny relative to the
    # 2-5 unit vehicle hulls and classifies the whole non-empty corpus.
    tolerance = 5e-5
    for triangle in geometry.triangles:
        a, b, c = (geometry.vertices[index] for index in triangle)
        ab = tuple(b[index] - a[index] for index in range(3))
        ac = tuple(c[index] - a[index] for index in range(3))
        normal = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        magnitude = math.sqrt(sum(value * value for value in normal))
        if magnitude <= tolerance:
            convex = False
            break
        distances = [
            sum(normal[axis] * (vertex[axis] - a[axis]) for axis in range(3)) / magnitude
            for vertex in geometry.vertices
        ]
        if min(distances) < -tolerance and max(distances) > tolerance:
            convex = False
            break
    return {
        "unique_edge_count": len(edges),
        "all_triangle_edges_incident_twice": closed,
        "euler_characteristic": euler,
        "convex_supporting_planes": convex if geometry.triangles else None,
    }


def _polygon_area(vertices, indices) -> float:
    if len(indices) < 3:
        return 0.0
    origin = vertices[indices[0]]
    cross_sum = [0.0, 0.0, 0.0]
    for index in range(1, len(indices) - 1):
        left = vertices[indices[index]]
        right = vertices[indices[index + 1]]
        a = tuple(left[axis] - origin[axis] for axis in range(3))
        b = tuple(right[axis] - origin[axis] for axis in range(3))
        cross_sum[0] += a[1] * b[2] - a[2] * b[1]
        cross_sum[1] += a[2] * b[0] - a[0] * b[2]
        cross_sum[2] += a[0] * b[1] - a[1] * b[0]
    return math.sqrt(sum(value * value for value in cross_sum)) * 0.5


def _representation(rep: ConvexHullRepresentation) -> dict[str, Any]:
    areas = [
        _polygon_area(rep.geometry_a.vertices, descriptor.primary_indices)
        for descriptor in rep.face_descriptors
    ]
    errors = [abs(observed - expected) for observed, expected in zip(rep.face_scalars, areas)]
    return {
        "offset": rep.offset,
        "end_offset": rep.end_offset,
        "byte_size": rep.end_offset - rep.offset,
        "geometry_a": {
            "vertex_count": rep.geometry_a.vertex_count,
            "triangle_count": rep.geometry_a.triangle_count,
            "offset": rep.geometry_a.offset,
            "end_offset": rep.geometry_a.end_offset,
            "aabb": _aabb(rep.geometry_a.vertices),
            "topology": _closed_geometry(rep.geometry_a),
        },
        "geometry_b": {
            "vertex_count": rep.geometry_b.vertex_count,
            "triangle_count": rep.geometry_b.triangle_count,
            "offset": rep.geometry_b.offset,
            "end_offset": rep.geometry_b.end_offset,
            "aabb": _aabb(rep.geometry_b.vertices),
        },
        "referenced_vertex_count": len(rep.referenced_vertex_indices),
        "edge_count": len(rep.edges),
        "face_count": rep.face_count,
        "descriptor_primary_lengths": sorted({len(item.primary_indices) for item in rep.face_descriptors}),
        "descriptor_secondary_lengths": sorted({len(item.secondary_indices) for item in rep.face_descriptors}),
        "face_loop_lengths": sorted({len(item) for item in rep.face_loop_indices}),
        "face_scalar_area_max_abs_error": max(errors, default=0.0),
        "face_scalars_match_polygon_area": all(error <= 2e-4 for error in errors),
    }


def _is_axis_aligned_box(geometry: CollisionGeometryBlock) -> bool:
    if geometry.vertex_count != 8 or geometry.triangle_count != 12:
        return False
    bounds = _aabb(geometry.vertices)
    assert bounds is not None
    minimum, maximum = bounds["minimum"], bounds["maximum"]
    corners = {
        tuple(minimum[axis] if mask & (1 << axis) == 0 else maximum[axis] for axis in range(3))
        for mask in range(8)
    }
    observed = {tuple(vertex) for vertex in geometry.vertices}
    return observed == corners


def _source_chull_candidates(directory: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(directory.glob("*.txt"), key=lambda item: item.name.casefold()):
        try:
            sidecar = parse_sidecar(path)
        except Exception:
            continue
        matches = [mesh for mesh in sidecar.meshes if "$chull" in mesh.name.casefold()]
        if matches:
            result.append({
                "sidecar": path.name,
                "meshes": [
                    {"name": mesh.name, "index": mesh.index, "triangle_count": mesh.size}
                    for mesh in matches
                ],
            })
    return result


def analyze_collision_corpus(vehicle_root: Path) -> dict[str, Any]:
    root = vehicle_root.resolve()
    records = []
    failures = []
    for path in sorted(root.glob("*/*.dx"), key=lambda item: str(item).casefold()):
        relative = f"{path.parent.name}/{path.name}"
        try:
            model = parse_dx(path)
            collision = model.collision
            record: dict[str, Any] = {
                "resource": relative,
                "evidence_class": (
                    "STATIC_FORMAT_ONLY_OUTLIER" if path.parent.name.casefold() == "forklift"
                    else "PC_VEHICLE_CORPUS"
                ),
                "tag100_present": collision.bsp is not None,
                "tag101_present": collision.convex_hull is not None,
                "tag102_present": collision.cylinder is not None,
                "collision_tags": list(collision.tag_ids),
                "collision_prefix_offset": collision.offset,
                "collision_prefix_end_offset": collision.end_offset,
                "unparsed_trailing_offset": collision.unparsed_offset,
                "unparsed_trailing_byte_count": len(collision.unparsed_data),
                "status": "FAILED" if collision.errors else "VALIDATED",
                "warnings": list(collision.warnings),
                "errors": list(collision.errors),
            }
            if collision.bsp is not None and not collision.errors:
                record["status"] = "PARTIAL"
                record["warnings"].append("tag100 BSP payload length is unresolved in R4B")
            if collision.cylinder is not None:
                record["tag102"] = {
                    "tag_offset": collision.cylinder.tag_offset,
                    "end_offset": collision.cylinder.end_offset,
                    "value_0": collision.cylinder.value_0,
                    "value_1": collision.cylinder.value_1,
                    "sha256": collision.cylinder.sha256,
                }
            hull = collision.convex_hull
            if hull is not None:
                center = hull.base_geometry.vertices[0] if hull.base_geometry.vertex_count == 1 else None
                box_geometry = hull.representation_a.geometry_a
                box_bounds = _aabb(box_geometry.vertices)
                box_center = tuple(
                    (box_bounds["minimum"][axis] + box_bounds["maximum"][axis]) * 0.5
                    for axis in range(3)
                ) if box_bounds else None
                maximum_distance = max((_distance(center, value) for value in box_geometry.vertices), default=None) if center else None
                record["tag101"] = {
                    "tag_offset": hull.tag_offset,
                    "payload_offset": hull.payload_offset,
                    "end_offset": hull.end_offset,
                    "payload_size": hull.payload_size,
                    "total_size_with_tag": hull.end_offset - hull.tag_offset,
                    "sha256": hull.sha256,
                    "base_geometry": {
                        "vertex_count": hull.base_geometry.vertex_count,
                        "triangle_count": hull.base_geometry.triangle_count,
                        "offset": hull.base_geometry.offset,
                        "end_offset": hull.base_geometry.end_offset,
                        "vertices": [list(value) for value in hull.base_geometry.vertices],
                    },
                    "base_scalar": hull.base_scalar,
                    "base_scalar_offset": hull.base_scalar_offset,
                    "base_center_to_representation_a_aabb_center": _distance(center, box_center) if center and box_center else None,
                    "base_center_to_representation_a_max_corner": maximum_distance,
                    "base_scalar_radius_abs_error": abs(hull.base_scalar - maximum_distance) if maximum_distance is not None else None,
                    "representation_a_axis_aligned_box": _is_axis_aligned_box(box_geometry),
                    "representation_a": _representation(hull.representation_a),
                    "representation_b": _representation(hull.representation_b),
                    "source_chull_candidates": _source_chull_candidates(path.parent),
                }
            records.append(record)
        except Exception as error:
            failures.append({"resource": relative, "type": type(error).__name__, "message": str(error)})

    tag101 = [record for record in records if record["tag101_present"]]
    nonempty = [record for record in tag101 if record["status"] == "VALIDATED" and record["tag101"]["representation_a"]["geometry_a"]["vertex_count"]]
    summary = {
        "dx_resource_count": len(records) + len(failures),
        "parsed_resource_count": len(records),
        "failed_resource_count": len(failures),
        "tag100_count": sum(record["tag100_present"] for record in records),
        "tag101_count": len(tag101),
        "tag101_validated_count": sum(record["status"] == "VALIDATED" for record in tag101),
        "tag101_failed_count": sum(record["status"] == "FAILED" for record in tag101),
        "tag102_count": sum(record["tag102_present"] for record in records),
        "tag101_nonempty_count": len(nonempty),
        "base_1v_0t_count": sum(record["tag101"]["base_geometry"]["vertex_count"] == 1 and record["tag101"]["base_geometry"]["triangle_count"] == 0 for record in tag101),
        "representation_a_box_count": sum(record["tag101"]["representation_a_axis_aligned_box"] for record in tag101),
        "base_scalar_radius_match_count": sum((record["tag101"]["base_scalar_radius_abs_error"] or 0.0) <= 1e-5 and record["tag101"]["representation_a_axis_aligned_box"] for record in nonempty),
        "representation_b_closed_count": sum(record["tag101"]["representation_b"]["geometry_a"]["topology"]["all_triangle_edges_incident_twice"] for record in nonempty),
        "representation_b_euler2_count": sum(record["tag101"]["representation_b"]["geometry_a"]["topology"]["euler_characteristic"] == 2 for record in nonempty),
        "representation_b_convex_count": sum(record["tag101"]["representation_b"]["geometry_a"]["topology"]["convex_supporting_planes"] is True for record in nonempty),
        "face_scalar_area_match_a_count": sum(record["tag101"]["representation_a"]["face_scalars_match_polygon_area"] for record in nonempty),
        "face_scalar_area_match_b_count": sum(record["tag101"]["representation_b"]["face_scalars_match_polygon_area"] for record in nonempty),
    }
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_descriptor": "external read-only DataGx/Vehicles root (path omitted)",
        "summary": summary,
        "resources": records,
        "failures": failures,
    }


def collision_corpus_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# R4B tag-101 vehicle corpus",
        "",
        "Generated from the canonical bounds-checked parser over external read-only vehicle assets.",
        "",
        "## Summary",
        "",
        f"- DX resources: **{summary['dx_resource_count']}**; parsed: **{summary['parsed_resource_count']}**; failed: **{summary['failed_resource_count']}**.",
        f"- Tag 100 / 101 / 102: **{summary['tag100_count']} / {summary['tag101_count']} / {summary['tag102_count']}**.",
        f"- Tag-101 validated / validation-failed: **{summary['tag101_validated_count']} / {summary['tag101_failed_count']}**; non-empty PC-style hulls: **{summary['tag101_nonempty_count']}**.",
        f"- Base 1v/0t: **{summary['base_1v_0t_count']}**; representation-A AABB: **{summary['representation_a_box_count']}**.",
        f"- Base scalar equals center-to-AABB-corner radius: **{summary['base_scalar_radius_match_count']}/{summary['tag101_nonempty_count']}**.",
        f"- Representation-B closed / Euler=2 / convex: **{summary['representation_b_closed_count']} / {summary['representation_b_euler2_count']} / {summary['representation_b_convex_count']}**.",
        f"- Face scalar equals polygon area, A/B: **{summary['face_scalar_area_match_a_count']} / {summary['face_scalar_area_match_b_count']}**.",
        "",
        "Forklift is retained as `STATIC_FORMAT_ONLY_OUTLIER`, not PC runtime evidence. Its tag-101 boundary parses exactly, but nine stored coordinate components are non-finite, so it is the one validation-failed tag-101 resource.",
        "",
        "## Tag-101 resources",
        "",
        "| Resource | Bytes | Base | Scalar | A V/T/E/F | B V/T/E/F | Remaining | Evidence |",
        "|---|---:|---|---:|---|---|---:|---|",
    ]
    for record in report["resources"]:
        if not record["tag101_present"]:
            continue
        hull = record["tag101"]
        a = hull["representation_a"]
        b = hull["representation_b"]
        lines.append(
            f"| `{record['resource']}` | {hull['total_size_with_tag']} | "
            f"{hull['base_geometry']['vertex_count']}/{hull['base_geometry']['triangle_count']} | "
            f"{hull['base_scalar']:.6g} | "
            f"{a['geometry_a']['vertex_count']}/{a['geometry_a']['triangle_count']}/{a['edge_count']}/{a['face_count']} | "
            f"{b['geometry_a']['vertex_count']}/{b['geometry_a']['triangle_count']}/{b['edge_count']}/{b['face_count']} | "
            f"{record['unparsed_trailing_byte_count']} | {record['evidence_class']} |"
        )
    lines.extend([
        "",
        "`Bytes` includes the four-byte tag. Parsing stops structurally before optional tag 102 and the preserved non-collision remainder; no signature search or resynchronization is used.",
    ])
    return "\n".join(lines) + "\n"


def write_collision_corpus_reports(vehicle_root: Path, json_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = analyze_collision_corpus(vehicle_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(collision_corpus_markdown(report), encoding="utf-8")
    return report
