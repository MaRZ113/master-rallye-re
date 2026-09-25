"""Emit explicit same-build GXM $chull -> demo DX tag101 comparison JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from master_rallye.collision_oracle import (
    compare_triangle_topology, edge_loop_vertices, exact_vertex_bijection, face_normal_metrics,
    gxm_to_demo_xyz,
)
from master_rallye.demo_dx import inspect_demo_dx
from master_rallye.bounds import compute_bounds1339
from master_rallye.gxm import (parse_gxm_geometry_prefix_bytes,
                                parse_gxm_prefix_bytes,
                                parse_gxm_triangle_prefix_bytes)
from master_rallye.sidecar import parse_sidecar
from r_demo_collision_compare import hull_vertex_ids


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def analyze(gxm: bytes, sidecar_path: Path, dx: bytes, directive: str, dx_provenance: str, mapping_tolerance: float) -> dict:
    prefix = parse_gxm_prefix_bytes(gxm, "same-build source GXM")
    geometry = parse_gxm_geometry_prefix_bytes(gxm, prefix)
    layout = parse_gxm_triangle_prefix_bytes(gxm, prefix, geometry)
    sidecar = parse_sidecar(sidecar_path)
    meshes = [mesh for mesh in sidecar.meshes if mesh.name == directive]
    if len(meshes) != 1 or sidecar.mesh_span != layout.record_count:
        raise ValueError("sidecar must contain one exact directive and match GXM record span")
    mesh = meshes[0]
    start, stop = mesh.index, mesh.index + mesh.size
    if mesh.size <= 0 or start < 0 or stop > layout.record_count:
        raise ValueError("sidecar hull record range outside GXM")

    records = [struct.unpack_from("<10I", gxm, layout.record_offset + index * 52)
               for index in range(start, stop)]
    source_ids = sorted({index for row in records for index in row[4:7]})
    source_points = {index: struct.unpack_from("<3f", gxm, layout.vector_c_offset + index * 12)
                     for index in source_ids}
    source_normals = [struct.unpack_from("<3f", gxm, geometry.vector_a_offset + index * 12)
                      for index in range(geometry.vector_a_count)]
    transformed = [gxm_to_demo_xyz(source_points[index]) for index in source_ids]
    extreme_local = hull_vertex_ids(transformed)
    extreme_ids = [source_ids[index] for index in sorted(extreme_local)]
    extreme_points = {index: source_points[index] for index in extreme_ids}

    parsed = inspect_demo_dx(dx, "same-build generated demo DX")
    tag = parsed.collision.convex_hull
    if tag is None:
        raise ValueError("generated demo DX has no parsed tag101")
    rep_b = tag.representation_b.geometry_a
    vertex_map = exact_vertex_bijection(extreme_points, rep_b.vertices, tolerance=mapping_tolerance)
    if not vertex_map["bijective"]:
        raise ValueError(f"$chull vertex mapping rejected: {vertex_map}")
    target_to_source = {row["target_index"]: row["source_c_index"]
                        for row in vertex_map["rows"]}
    face_report = compare_triangle_topology(
        [tuple(row[4:7]) for row in records], rep_b.triangles, target_to_source)
    polygon_rows = []
    polygon_area_errors = []
    source_record_assignments = []
    for face_index, edge_loop in enumerate(tag.representation_b.face_loop_indices):
        loop = edge_loop_vertices(tag.representation_b.edges, edge_loop)
        source_loop = [target_to_source[index] for index in loop]
        source_loop_set = set(source_loop)
        matching_records = [start + local_index for local_index, row in enumerate(records)
                            if set(row[4:7]).issubset(source_loop_set)]
        source_record_assignments.extend(matching_records)
        points = [rep_b.vertices[index] for index in loop]
        area = 0.0
        for index in range(1, len(points) - 1):
            a = tuple(points[index][axis] - points[0][axis] for axis in range(3))
            b = tuple(points[index + 1][axis] - points[0][axis] for axis in range(3))
            cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
                     a[0] * b[1] - a[1] * b[0])
            area += 0.5 * sum(value * value for value in cross) ** 0.5
        stored_area = tag.representation_b.face_scalars[face_index]
        area_error = abs(area - stored_area)
        polygon_area_errors.append(area_error)
        polygon_rows.append({"compiled_face_index": face_index,
                             "target_edge_loop": list(edge_loop),
                             "target_vertex_loop": list(loop),
                             "mapped_source_c_loop": source_loop,
                             "source_record_indices_by_vertex_subset": matching_records,
                             "computed_polygon_area": area,
                             "stored_face_scalar": stored_area,
                             "area_abs_error": area_error})

    vector_b_sentinel_records = sum(row[1:4] == (0xFFFFFFFF,) * 3 for row in records)
    material_counts = {}
    for row in records:
        material_key = "FFFFFFFF" if row[0] == 0xFFFFFFFF else str(row[0])
        material_counts[material_key] = material_counts.get(material_key, 0) + 1
    source_face_sets = [tuple(sorted(row[4:7])) for row in records]
    source_duplicate_face_records = len(source_face_sets) - len(set(source_face_sets))
    vector_a_record_rows = []
    for local_index, row in enumerate(records):
        face = tuple(row[4:7])
        a_indices = tuple(row[7:10])
        vector_a_record_rows.append(face_normal_metrics(source_points, face, a_indices,
                                                        source_normals))
    valid_normals = [row for row in vector_a_record_rows if not row.get("degenerate", True)]
    all_angles = [angle for row in valid_normals for angle in row["angles_degrees"]]
    a_spreads = [row["max_pairwise_normal_distance"] for row in valid_normals]

    rep_a = tag.representation_a.geometry_a.vertices
    bounds = lambda points: [[min(p[axis] for p in points), max(p[axis] for p in points)]
                             for axis in range(3)]
    rep_a_bounds = bounds(rep_a)
    source_extreme_bounds = bounds([gxm_to_demo_xyz(point) for point in extreme_points.values()])
    rep_b_bounds = bounds(rep_b.vertices)
    base_center = tag.base_geometry.vertices[0]
    corner_radius = max((sum((base_center[i] - point[i]) ** 2 for i in range(3)) ** 0.5
                         for point in rep_a), default=0.0)
    distance = abs(tag.base_scalar - corner_radius)

    marker = parsed.collision.spatial_bounds_1339
    marker_candidates = {}
    if marker is not None:
        candidate_sets = {
            "render_only": list(parsed.positions),
            "rep_b_only": list(rep_b.vertices),
            "render_plus_rep_b": list(parsed.positions) + list(rep_b.vertices),
        }
        for label, candidate_points in candidate_sets.items():
            candidate = compute_bounds1339(candidate_points)
            marker_candidates[label] = {
                "exact_44_byte_match": candidate.raw == marker.raw,
                "center_abs_error": max(abs(a - b) for a, b in zip(candidate.center, marker.center)),
                "radius_abs_error": abs(candidate.radius - marker.radius),
                "minimum_abs_error": max(abs(a - b) for a, b in zip(candidate.minimum, marker.minimum)),
                "maximum_abs_error": max(abs(a - b) for a, b in zip(candidate.maximum, marker.maximum)),
            }

    return {
        "evidence": ("CONFIRMED_BY_BYTES same-build regenerated source/compiled pair; runtime mutation safety not established" if dx_provenance == "runtime-regenerated" else "CONFIRMED_BY_CORPUS same-build shipped source/compiled association; regeneration not established"),
        "compiled_dx_provenance": dx_provenance,
        "source_sha256": sha256(gxm), "sidecar_sha256": sha256(sidecar_path.read_bytes()),
        "compiled_dx_sha256": sha256(dx), "directive": directive,
        "record_range_half_open": [start, stop], "source_record_count": len(records),
        "vector_c_referenced_indices": source_ids,
        "vector_c_extreme_indices": extreme_ids,
        "vector_b_all_sentinel": vector_b_sentinel_records == len(records),
        "vector_b_sentinel_record_count": vector_b_sentinel_records,
        "source_record_material_field_counts": material_counts,
        "source_duplicate_unordered_face_records": source_duplicate_face_records,
        "coordinate_transform": "(x,y,z) -> (x,z,-y)",
        "mapping_tolerance": mapping_tolerance,
        "vector_c_to_rep_b": vertex_map,
        "source_record_to_rep_b_faces": face_report,
        "source_records_matched_to_compiled_polygon_faces": len(source_record_assignments),
        "source_records_reused_across_polygon_subset_groups": len(source_record_assignments) - len(set(source_record_assignments)),
        "compiled_polygon_face_area_max_abs_error": max(polygon_area_errors, default=0.0),
        "compiled_polygon_faces": polygon_rows,
        "vector_a": {
            "records_tested": len(records), "nondegenerate_records": len(valid_normals),
            "degenerate_records": len(records) - len(valid_normals),
            "all_referenced_values_by_record": vector_a_record_rows,
            "angle_degrees_min": min(all_angles, default=None),
            "angle_degrees_max": max(all_angles, default=None),
            "max_intra_record_normal_spread": max(a_spreads, default=None),
            "interpretation": "per-record normal candidates; source triangle mapping and axis transform tested",
        },
        "tag101": {"rep_b_vertex_count": len(rep_b.vertices),
                   "rep_b_triangle_count": len(rep_b.triangles),
                   "rep_b_edge_count": len(tag.representation_b.edges),
                   "rep_b_face_descriptor_count": tag.representation_b.face_count,
                   "rep_b_edge_face_adjacency_count": len(tag.representation_b.edge_face_adjacency),
                   "rep_b_face_loop_count": len(tag.representation_b.face_loop_indices),
                   "rep_b_face_scalar_count": len(tag.representation_b.face_scalars),
                   "rep_a_vertex_count": len(rep_a),
                   "rep_a_bounds_xyz": rep_a_bounds,
                   "source_hull_extreme_bounds_xyz": source_extreme_bounds,
                   "rep_b_bounds_xyz": rep_b_bounds,
                   "base_scalar": tag.base_scalar,
                   "base_geometry_center": base_center,
                   "rep_a_corner_radius_from_center": corner_radius,
                   "base_scalar_radius_abs_error": distance},
        "marker_1339": {"present": marker is not None,
                         "stored": marker.to_dict() if marker is not None else None,
                         "candidate_set_comparisons": marker_candidates},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gxm", type=Path, required=True)
    ap.add_argument("--sidecar", type=Path, required=True)
    ap.add_argument("--compiled-dx", type=Path, required=True)
    ap.add_argument("--dx-provenance", choices=("runtime-regenerated", "corpus-shipped"), required=True)
    ap.add_argument("--mapping-tolerance", type=float, required=True,
                    help="maximum accepted source-to-target distance in demo coordinates")
    ap.add_argument("--directive", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    gxm = args.gxm.resolve(strict=True)
    sidecar = args.sidecar.resolve(strict=True)
    dx = args.compiled_dx.resolve(strict=True)
    output = args.output.resolve()
    if gxm.parent != sidecar.parent:
        ap.error("source GXM and sidecar must be siblings")
    output_root = Path(__file__).resolve().parents[2] / ".research-output" / "r-demo2"
    if output_root.resolve() not in output.parents or output.suffix.lower() != ".json":
        ap.error("output must be JSON under ignored .research-output/r-demo2")
    report = analyze(gxm.read_bytes(), sidecar, dx.read_bytes(), args.directive, args.dx_provenance, args.mapping_tolerance)
    report.update({"source_gxm": str(gxm), "source_sidecar": str(sidecar),
                   "compiled_dx": str(dx)})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_records": report["source_record_count"],
                      "source_extremes": len(report["vector_c_extreme_indices"]),
                      "target_vertices": report["tag101"]["rep_b_vertex_count"],
                      "exact_vertex_matches": report["vector_c_to_rep_b"]["exact_float_match_count"],
                      "mapped_faces": report["source_record_to_rep_b_faces"]["target_faces_matching_source_unordered"],
                      "target_faces": report["tag101"]["rep_b_triangle_count"]}))


if __name__ == "__main__":
    main()
