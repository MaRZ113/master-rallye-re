"""Build a machine-readable R-DEMO2.9 source-to-cooker oracle analysis."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.collision_oracle import gxm_to_demo_xyz  # noqa: E402
from master_rallye.collision_oracle_analysis import (  # noqa: E402
    analyze_face_scalars, analyze_gxm_chull, analyze_tag101_rep_a,
    compare_core_topology, map_gxm_chull_to_rep_b, recompute_marker1339,
)
from master_rallye.demo_dx import inspect_demo_dx  # noqa: E402
from tools.scanner.r_demo_collision_compare import hull_vertex_ids  # noqa: E402
from tools.scanner.r_demo2_931_chull_dx_oracle import (  # noqa: E402
    byte_diff_summary, categorized_byte_accounting, compare_pair,
)

MAPPING_TOLERANCE = 1e-5
EXPECTED_SHIFT = (0.10, 0.0, 0.0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _source_hull(raw: bytes, sidecar_path: Path, directive: str) -> dict:
    return analyze_gxm_chull(raw, sidecar_path, directive)


def _source_to_b_map(points: dict[int, tuple[float, float, float]], target_vertices) -> dict:
    transformed = {index: gxm_to_demo_xyz(point) for index, point in points.items()}
    point_list = [transformed[index] for index in sorted(transformed)]
    hull_local = hull_vertex_ids(point_list)
    extreme_ids = [sorted(transformed)[i] for i in sorted(hull_local)]
    result = map_gxm_chull_to_rep_b(points, target_vertices, extreme_ids,
                                    tolerance=MAPPING_TOLERANCE)
    result = result["mapping"]
    if not result["bijective"]:
        raise ValueError(f"$chull extreme-to-Rep-B mapping failed: {result['status']}")
    target_to_source = {row["target_index"]: row["source_c_index"] for row in result["rows"]}
    source_to_target = {row["source_c_index"]: row for row in result["rows"]}
    return {"extreme_source_indices": extreme_ids, "mapping": result,
            "source_to_target": source_to_target,
            "target_to_source": target_to_source,
            "non_extreme_source_indices": sorted(set(points) - set(extreme_ids))}


def _bounds(points) -> dict:
    return {"minimum": [min(point[axis] for point in points) for axis in range(3)],
            "maximum": [max(point[axis] for point in points) for axis in range(3)]}


def _mean(values) -> float | None:
    return sum(values) / len(values) if values else None


def _translation(first, second, expected=EXPECTED_SHIFT) -> dict:
    if len(first) != len(second):
        return {"same_count": False, "first_count": len(first), "second_count": len(second)}
    deltas = [[float(b[axis]) - float(a[axis]) for axis in range(3)]
              for a, b in zip(first, second)]
    residuals = [[delta[axis] - expected[axis] for axis in range(3)] for delta in deltas]
    absolute = [abs(value) for row in residuals for value in row]
    return {"same_count": True, "count": len(deltas),
            "delta_min_xyz": [min(row[axis] for row in deltas) for axis in range(3)],
            "delta_max_xyz": [max(row[axis] for row in deltas) for axis in range(3)],
            "delta_mean_xyz": [_mean([row[axis] for row in deltas]) for axis in range(3)],
            "expected_translation_xyz": list(expected),
            "residual_min_xyz": [min(row[axis] for row in residuals) for axis in range(3)],
            "residual_max_xyz": [max(row[axis] for row in residuals) for axis in range(3)],
            "residual_mean_xyz": [_mean([row[axis] for row in residuals]) for axis in range(3)],
            "max_abs_translation_error": max(absolute, default=0.0),
            "within_float32_tolerance": max(absolute, default=0.0) <= 2e-7}


def _marker_formula(view) -> dict:
    stored = view.collision.spatial_bounds_1339
    hull = view.collision.convex_hull
    if stored is None or hull is None:
        return {"status": "NOT_PARSED"}
    render = list(view.positions)
    collision = list(hull.representation_b.geometry_a.vertices)
    points = render + collision
    expected = _bounds(points)
    center = tuple(_f32((expected["minimum"][axis] + expected["maximum"][axis]) / 2)
                   for axis in range(3))
    raw_radius = _f32(max(math.dist(center, point) for point in points))
    safe_recomputed = recompute_marker1339(render, collision, offset=stored.offset)
    point_extrema = []
    for axis in range(3):
        point_extrema.append({
            "axis": "xyz"[axis],
            "minimum_render": min(p[axis] for p in render),
            "minimum_rep_b": min(p[axis] for p in collision),
            "minimum_union": expected["minimum"][axis],
            "minimum_dominated_by": "render" if min(p[axis] for p in render) < min(p[axis] for p in collision) else "rep_b",
            "maximum_render": max(p[axis] for p in render),
            "maximum_rep_b": max(p[axis] for p in collision),
            "maximum_union": expected["maximum"][axis],
            "maximum_dominated_by": "render" if max(p[axis] for p in render) > max(p[axis] for p in collision) else "rep_b",
        })
    center_errors = [abs(stored.center[axis] - center[axis]) for axis in range(3)]
    min_errors = [abs(stored.minimum[axis] - expected["minimum"][axis]) for axis in range(3)]
    max_errors = [abs(stored.maximum[axis] - expected["maximum"][axis]) for axis in range(3)]
    return {"stored": stored.to_dict(), "expected_minimum": expected["minimum"],
            "expected_maximum": expected["maximum"], "expected_center_f32": list(center),
            "expected_radius_f32_nearest": raw_radius,
            "expected_radius_safe_enclosing": safe_recomputed.radius,
            "hypothesis_a_render_union_rep_b": {
                "max_minimum_error": max(min_errors, default=0.0),
                "max_maximum_error": max(max_errors, default=0.0)},
            "hypothesis_b_center_from_extrema": {
                "component_errors": center_errors,
                "maximum_error": max(center_errors, default=0.0)},
            "hypothesis_c_radius_from_union": {
                "nearest_float32_error": abs(stored.radius - raw_radius),
                "safe_enclosing_error": abs(stored.radius - safe_recomputed.radius),
                "unrounded_distance": max(math.dist(center, point) for point in points)},
            "extrema_dominance": point_extrema}


def _reference_points(view, rep_b_bounds) -> dict:
    hull = view.collision.convex_hull
    if hull is None:
        return {}
    center = tuple((rep_b_bounds["minimum"][axis] + rep_b_bounds["maximum"][axis]) / 2
                   for axis in range(3))
    points = {
        "tag101_base_geometry": hull.base_geometry.vertices,
        "rep_a_geometry_b": hull.representation_a.geometry_b.vertices,
        "rep_b_geometry_b": hull.representation_b.geometry_b.vertices,
    }
    result = {}
    for label, values in points.items():
        rows = []
        for point in values:
            rows.append({"xyz": list(point), "delta_from_rep_b_aabb_center": [point[i] - center[i] for i in range(3)],
                         "distance_to_rep_b_aabb_center": math.dist(point, center)})
        result[label] = rows
    return {"rep_b_aabb_center": list(center), "points": result}


def _base_scalar_relation(view) -> dict:
    hull = view.collision.convex_hull
    if hull is None or not hull.base_geometry.vertices:
        return {"status": "NOT_PARSED"}
    center = hull.base_geometry.vertices[0]
    corners = hull.representation_a.geometry_a.vertices
    distance = max(math.dist(center, point) for point in corners)
    rounded = _f32(distance)
    return {"base_geometry_point": list(center), "maximum_distance_to_rep_a_vertex": distance,
            "float32_nearest": rounded, "stored_scalar": hull.base_scalar,
            "stored_matches_float32_radius": rounded == hull.base_scalar,
            "absolute_error_before_float32_rounding": abs(distance - hull.base_scalar),
            "absolute_error_after_float32_rounding": abs(rounded - hull.base_scalar)}


def _face_scalar_pair(before_rep, after_rep) -> dict:
    before = analyze_face_scalars(before_rep)
    after = analyze_face_scalars(after_rep)
    scalar_deltas = [b - a for a, b in zip(before_rep.face_scalars, after_rep.face_scalars)]
    area_deltas = [b["computed_polygon_area"] - a["computed_polygon_area"]
                   for a, b in zip(before["rows"], after["rows"])]
    errors = [row["absolute_error"] for row in before["rows"] + after["rows"]]
    relative = [abs(delta) / max(abs(value), 1e-30)
                for delta, value in zip(scalar_deltas, before_rep.face_scalars)]
    return {"baseline": {"count": before["face_count"], "max_area_error": before["max_abs_area_error"],
                         "mean_area_error": before["mean_abs_area_error"]},
            "candidate": {"count": after["face_count"], "max_area_error": after["max_abs_area_error"],
                          "mean_area_error": after["mean_abs_area_error"]},
            "face_identity_basis": "same face index; core topology and edge loops compare equal",
            "scalar_delta_min": min(scalar_deltas, default=0.0),
            "scalar_delta_max": max(scalar_deltas, default=0.0),
            "scalar_delta_mean": _mean(scalar_deltas),
            "scalar_max_abs_delta": max((abs(value) for value in scalar_deltas), default=0.0),
            "scalar_max_relative_delta": max(relative, default=0.0),
            "recomputed_area_max_abs_delta": max((abs(value) for value in area_deltas), default=0.0),
            "scalar_area_error_max_both_runs": max(errors, default=0.0)}


def analyze_oracle(gxm_path: Path, candidate_gxm_path: Path, sidecar_path: Path,
                   baseline_a_path: Path, baseline_b_path: Path, candidate_dx_path: Path,
                   audit_path: Path, corpus_root: Path) -> dict:
    original_raw = gxm_path.read_bytes()
    candidate_gxm_raw = candidate_gxm_path.read_bytes()
    sidecar_raw = sidecar_path.read_bytes()
    original = _source_hull(original_raw, sidecar_path, "$chull(Trooper)")
    candidate_source = _source_hull(candidate_gxm_raw, sidecar_path, "$chull(Trooper)")
    if original["source_c_indices"] != candidate_source["source_c_indices"] or original["record_count"] != candidate_source["record_count"]:
        raise ValueError("candidate GXM changed the identified $chull index set or record count")

    dx_raws = [baseline_a_path.read_bytes(), baseline_b_path.read_bytes(), candidate_dx_path.read_bytes()]
    if dx_raws[0] != dx_raws[1]:
        raise ValueError("baseline A/B are not byte-identical; candidate comparison stopped")
    views = [inspect_demo_dx(raw, str(path)) for raw, path in zip(
        dx_raws, (baseline_a_path, baseline_b_path, candidate_dx_path))]
    hulls = [view.collision.convex_hull for view in views]
    if any(hull is None for hull in hulls):
        raise ValueError("one or more DX files do not have parsed tag101")
    base_hull, baseline_b_hull, candidate_hull = hulls

    map_a = _source_to_b_map(original["source_c_points"], base_hull.representation_b.geometry_a.vertices)
    map_b = _source_to_b_map(original["source_c_points"], baseline_b_hull.representation_b.geometry_a.vertices)
    map_c = _source_to_b_map(candidate_source["source_c_points"], candidate_hull.representation_b.geometry_a.vertices)
    if map_a["target_to_source"] != map_b["target_to_source"]:
        raise ValueError("baseline A/B source-to-Rep-B vertex identities differ")
    source_mapping_rows = []
    for index in original["source_c_indices"]:
        row_a = map_a["source_to_target"].get(index)
        row_c = map_c["source_to_target"].get(index)
        p0 = original["source_c_points"][index]
        p1 = candidate_source["source_c_points"][index]
        source_mapping_rows.append({
            "source_c_index": index,
            "baseline_source_xyz": list(p0),
            "baseline_expected_dx_xyz": list(gxm_to_demo_xyz(p0)),
            "baseline_rep_b_vertex_index": row_a["target_index"] if row_a else None,
            "baseline_residual": row_a["distance"] if row_a else None,
            "candidate_source_xyz": list(p1),
            "candidate_expected_dx_xyz": list(gxm_to_demo_xyz(p1)),
            "candidate_rep_b_vertex_index": row_c["target_index"] if row_c else None,
            "candidate_residual": row_c["distance"] if row_c else None,
            "mapping_identity_preserved": (row_a is None and row_c is None) or (
                row_a is not None and row_c is not None and row_a["target_index"] == row_c["target_index"]),
        })

    delta = _translation(base_hull.representation_b.geometry_a.vertices,
                         candidate_hull.representation_b.geometry_a.vertices)
    rep_b_core = compare_core_topology(base_hull.representation_b, candidate_hull.representation_b)
    rep_a_core = compare_core_topology(base_hull.representation_a, candidate_hull.representation_a)
    rep_b_bounds = {"baseline": _bounds(base_hull.representation_b.geometry_a.vertices),
                    "candidate": _bounds(candidate_hull.representation_b.geometry_a.vertices)}
    rep_a_aabb = {
        "baseline": analyze_tag101_rep_a(base_hull.representation_a,
                                         base_hull.representation_b)["aabb_corners"],
        "candidate": analyze_tag101_rep_a(candidate_hull.representation_a,
                                          candidate_hull.representation_b)["aabb_corners"],
        "vertex_order_delta": _translation(base_hull.representation_a.geometry_a.vertices,
                                           candidate_hull.representation_a.geometry_a.vertices),
        "triangles_equal": base_hull.representation_a.geometry_a.triangles == candidate_hull.representation_a.geometry_a.triangles,
        "classification": "REP_A_VERTICES_EQUAL_REP_B_AABB_CORNERS_IN_CONTROLLED_PAIR",
    }
    for label in ("baseline", "candidate"):
        if not rep_a_aabb[label]["all_eight_matched"] or rep_a_aabb[label]["maximum_corner_error"] is None:
            rep_a_aabb["classification"] = "REP_A_AABB_RELATION_NOT_PROVEN"

    scalar_bytes = [raw[base_hull.base_scalar_offset:base_hull.base_scalar_offset + 4]
                    for raw in dx_raws[::2]]
    scalar = {"baseline_value": base_hull.base_scalar, "candidate_value": candidate_hull.base_scalar,
              "baseline_bytes_hex": scalar_bytes[0].hex(), "candidate_bytes_hex": scalar_bytes[1].hex(),
              "bit_identical": scalar_bytes[0] == scalar_bytes[1],
              "classification": "TRANSLATION_INVARIANT_IN_CONTROLLED_ORACLE"}
    references = {"baseline": _reference_points(views[0], rep_b_bounds["baseline"]),
                  "candidate": _reference_points(views[2], rep_b_bounds["candidate"])}
    reference_deltas = {}
    for label in references["baseline"]["points"]:
        first_points = references["baseline"]["points"][label]
        second_points = references["candidate"]["points"][label]
        reference_deltas[label] = [
            {"point_index": index,
             "delta_xyz": [second["xyz"][axis] - first["xyz"][axis] for axis in range(3)]}
            for index, (first, second) in enumerate(zip(first_points, second_points))
        ]

    markers = {"baseline": _marker_formula(views[0]), "candidate": _marker_formula(views[2])}
    marker_corpus = {}
    for name in ("Jump", "NewRav", "Tata"):
        path = corpus_root / "DataGx" / "Vehicles" / name / "car.dx"
        if path.is_file():
            view = inspect_demo_dx(path.read_bytes(), str(path))
            marker_corpus[name] = {"sha256": view.sha256, "formula": _marker_formula(view),
                                   "tag101_base_scalar_relation": _base_scalar_relation(view),
                                   "provenance": "same-build corpus-shipped control"}

    comparisons = {
        "baseline_A_vs_baseline_B": compare_pair(dx_raws[0], dx_raws[1],
            first_source=str(baseline_a_path), second_source=str(baseline_b_path), role="baseline"),
        "baseline_A_vs_candidate": compare_pair(dx_raws[0], dx_raws[2],
            first_source=str(baseline_a_path), second_source=str(candidate_dx_path), role="candidate"),
    }
    byte_accounting = categorized_byte_accounting(dx_raws[0], dx_raws[2])
    if not byte_accounting["complete"]:
        raise ValueError("not all baseline-to-candidate changed bytes are classified")
    face_scalars = {
        "representation_a": _face_scalar_pair(base_hull.representation_a, candidate_hull.representation_a),
        "representation_b": _face_scalar_pair(base_hull.representation_b, candidate_hull.representation_b),
    }

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("candidate_sha256") != sha256(candidate_gxm_raw):
        raise ValueError("candidate GXM does not match its byte audit SHA256")
    if audit.get("source_sha256") != sha256(original_raw):
        raise ValueError("source GXM does not match its candidate audit SHA256")
    if audit.get("translation_source_xyz") != [0.1, 0.0, 0.0]:
        raise ValueError("candidate audit does not describe +0.10 X")

    return {
        "schema": "r-demo2.9-collision-cooker-oracle-v1",
        "status": "CONTROLLED_ORACLE_ANALYSIS_COMPLETE",
        "input_hashes": {
            "source_gxm": {"path": str(gxm_path), "size": len(original_raw), "sha256": sha256(original_raw)},
            "candidate_gxm": {"path": str(candidate_gxm_path), "size": len(candidate_gxm_raw), "sha256": sha256(candidate_gxm_raw)},
            "sidecar": {"path": str(sidecar_path), "size": len(sidecar_raw), "sha256": sha256(sidecar_raw)},
            "baseline_a": {"path": str(baseline_a_path), "size": len(dx_raws[0]), "sha256": sha256(dx_raws[0])},
            "baseline_b": {"path": str(baseline_b_path), "size": len(dx_raws[1]), "sha256": sha256(dx_raws[1])},
            "candidate_dx": {"path": str(candidate_dx_path), "size": len(dx_raws[2]), "sha256": sha256(dx_raws[2])},
        },
        "baseline_ab": {"byte_identical": dx_raws[0] == dx_raws[1],
                        "difference": byte_diff_summary(dx_raws[0], dx_raws[1])},
        "source_chull": {"directive": "$chull(Trooper)",
                         "header_words": list(original["header_words"]),
                         "parsed_counts": {"materials": original["material_count"],
                                           "vector_a": original["geometry_prefix"].vector_a_count,
                                           "vector_b": original["geometry_prefix"].vector_b_count,
                                           "triangle_records": original["triangle_prefix"].record_count,
                                           "vector_c": original["triangle_prefix"].vector_c_count},
                         "record_range_half_open": [original["record_start"], original["record_start"] + original["record_count"]],
                         "triangle_record_count": original["record_count"],
                         "unique_source_c_count": len(original["source_c_indices"]),
                         "source_c_indices": original["source_c_indices"],
                         "candidate_source_translation_xyz": list(EXPECTED_SHIFT),
                         "candidate_source_index_set_equal": original["source_c_indices"] == candidate_source["source_c_indices"]},
        "source_to_rep_b": {"coordinate_transform": "GXM (x,y,z) -> DX (x,z,-y)",
                            "mapping_tolerance": MAPPING_TOLERANCE,
                            "baseline_extreme_indices": map_a["extreme_source_indices"],
                            "candidate_extreme_indices": map_c["extreme_source_indices"],
                            "retained_source_c_indices": sorted(map_a["source_to_target"]),
                            "not_retained_as_distinct_final_vertices": map_a["non_extreme_source_indices"],
                            "baseline_mapping_max_residual": map_a["mapping"]["max_matched_distance"],
                            "candidate_mapping_max_residual": map_c["mapping"]["max_matched_distance"],
                            "mapping_table": source_mapping_rows,
                            "all_mapping_identities_preserved": all(row["mapping_identity_preserved"] for row in source_mapping_rows),
                            "rep_b_vertices": len(base_hull.representation_b.geometry_a.vertices),
                            "rep_b_triangles": len(base_hull.representation_b.geometry_a.triangles)},
        "rep_b_translation": {"geometry": delta, "core_topology": rep_b_core,
                              "triangles_equal": base_hull.representation_b.geometry_a.triangles == candidate_hull.representation_b.geometry_a.triangles,
                              "edges_equal": base_hull.representation_b.edges == candidate_hull.representation_b.edges,
                              "edge_face_adjacency_equal": base_hull.representation_b.edge_face_adjacency == candidate_hull.representation_b.edge_face_adjacency,
                              "face_loops_equal": base_hull.representation_b.face_loop_indices == candidate_hull.representation_b.face_loop_indices},
        "rep_a": {"core_topology": rep_a_core, "aabb": rep_a_aabb,
                  "baseline_triangle_count": len(base_hull.representation_a.geometry_a.triangles),
                  "baseline_triangles": [list(face) for face in base_hull.representation_a.geometry_a.triangles],
                  "candidate_triangles": [list(face) for face in candidate_hull.representation_a.geometry_a.triangles],
                  "triangles_equal": base_hull.representation_a.geometry_a.triangles == candidate_hull.representation_a.geometry_a.triangles},
        "tag101_base_and_auxiliary_points": {**references, "translation_deltas": reference_deltas},
        "tag101_base_scalar": {**scalar,
                               "baseline_rep_a_radius_relation": _base_scalar_relation(views[0]),
                               "candidate_rep_a_radius_relation": _base_scalar_relation(views[2]),
                               "additional_corpus_relations": {
                                   name: item["tag101_base_scalar_relation"]
                                   for name, item in marker_corpus.items()}},
        "face_scalars": face_scalars,
        "marker_1339": {"controlled_baseline": markers["baseline"],
                         "controlled_candidate": markers["candidate"],
                         "additional_corpus_controls": marker_corpus},
        "byte_accounting": byte_accounting,
        "dx_comparisons": comparisons,
        "source_candidate_byte_audit": {
            key: audit[key] for key in (
                "modified_vector_count", "changed_byte_count", "changed_byte_ranges_end_exclusive",
                "non_target_bytes_identical", "vector_a_b_material_triangle_hierarchy_bytes_unchanged",
                "file_size_unchanged", "masked_source_sha256", "masked_candidate_sha256",
                "native_plane_replay") if key in audit
        },
        "classification_notes": {
            "existing_parser_verdict": comparisons["baseline_A_vs_candidate"]["semantic_verdict_from_existing_demo_dx_parser"],
            "core_topology": comparisons["baseline_A_vs_candidate"]["classification"]["topology"],
            "secondary_descriptor_semantics": "UNRESOLVED",
            "runtime": "human supplied original-cooker outputs; no local game launch performed",
        },
    }


def render_markdown(report: dict) -> str:
    hashes = report["input_hashes"]
    source = report["source_chull"]
    mapping = report["source_to_rep_b"]
    byte = report["byte_accounting"]
    lines = [
        "# R-DEMO2.9 machine analysis",
        "",
        f"Baseline A/B exact identity: **{report['baseline_ab']['byte_identical']}**.",
        "",
        "| Input | Size | SHA256 |",
        "|---|---:|---|",
    ]
    for name, item in hashes.items():
        lines.append(f"| `{name}` | {item['size']} | `{item['sha256']}` |")
    lines.extend(["", "## Source C to Rep B mapping", "",
                  f"`{source['directive']}` records `{source['record_range_half_open']}` contain {source['triangle_record_count']} triangles and reference {source['unique_source_c_count']} unique C positions. Rep B has {mapping['rep_b_vertices']} vertices and {mapping['rep_b_triangles']} triangles; {len(mapping['retained_source_c_indices'])} C positions map bijectively to Rep B and {len(mapping['not_retained_as_distinct_final_vertices'])} are not retained as distinct final vertices.",
                  "", "| C index | Source XYZ | Expected baseline DX XYZ | Baseline B index / error | Expected candidate DX XYZ | Candidate B index / error | Same identity |",
                  "|---:|---|---|---|---|---|---|"])
    for row in mapping["mapping_table"]:
        base_match = "—" if row["baseline_rep_b_vertex_index"] is None else f"{row['baseline_rep_b_vertex_index']} / {row['baseline_residual']:.3g}"
        cand_match = "—" if row["candidate_rep_b_vertex_index"] is None else f"{row['candidate_rep_b_vertex_index']} / {row['candidate_residual']:.3g}"
        lines.append(f"| {row['source_c_index']} | `{row['baseline_source_xyz']}` | `{row['baseline_expected_dx_xyz']}` | {base_match} | `{row['candidate_expected_dx_xyz']}` | {cand_match} | {row['mapping_identity_preserved']} |")
    lines.extend(["", "## Changed-byte accounting", "",
                  f"{byte['explained_changed_bytes']} of {byte['total_changed_bytes']} changed bytes are assigned to parsed fields; complete: **{byte['complete']}**.",
                  "", "| Category | Changed bytes | Ranges |", "|---|---:|---:|"])
    for label, item in byte["categories"].items():
        lines.append(f"| `{label}` | {item['changed_byte_count']} | {len(item['ranges'])} |")
    lines.extend(["", "Full offsets, old/new bytes, computed errors, secondary descriptor tuples, and marker formula checks are preserved in the adjacent JSON machine report."])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gxm", type=Path, required=True)
    parser.add_argument("--candidate-gxm", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--baseline-a", type=Path, required=True)
    parser.add_argument("--baseline-b", type=Path, required=True)
    parser.add_argument("--candidate-dx", type=Path, required=True)
    parser.add_argument("--candidate-audit", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="new JSON output below ignored .research-output/r-demo2")
    args = parser.parse_args()
    output = args.output.resolve()
    scratch = (ROOT / ".research-output" / "r-demo2").resolve()
    if scratch not in output.parents or output.suffix.lower() != ".json":
        parser.error("output must be a JSON file below ignored .research-output/r-demo2")
    try:
        report = analyze_oracle(args.gxm.resolve(strict=True), args.candidate_gxm.resolve(strict=True),
                                args.sidecar.resolve(strict=True), args.baseline_a.resolve(strict=True),
                                args.baseline_b.resolve(strict=True), args.candidate_dx.resolve(strict=True),
                                args.candidate_audit.resolve(strict=True), args.corpus_root.resolve(strict=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    report["output_path"] = str(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path = output.with_suffix(".md")
    if output.exists() or report_path.exists():
        parser.error("refusing to overwrite an existing analysis output")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "changed_bytes": report["byte_accounting"]["total_changed_bytes"],
                      "explained_bytes": report["byte_accounting"]["explained_changed_bytes"],
                      "source_c": report["source_chull"]["unique_source_c_count"],
                      "rep_b_vertices": report["source_to_rep_b"]["rep_b_vertices"],
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
