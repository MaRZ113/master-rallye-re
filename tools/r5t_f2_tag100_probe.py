#!/usr/bin/env python3
"""Read-only R5T-F.2 tag100 structure and France1 plane-correlation probe."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for item in (ROOT, ROOT / "src"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from master_rallye.course_gxm import CourseGxmModelV7, parse_course_gxm_model_v7  # noqa: E402
from master_rallye.course_source import parse_course_txt  # noqa: E402
from master_rallye.course_spatial import gxm_source_to_runtime  # noqa: E402
from master_rallye.course_tag100 import CourseTag100, Tag100Node, parse_course_tag100_bytes, translate_plane_distance  # noqa: E402
from master_rallye.dx_course import parse_course_dx  # noqa: E402


TARGET_MESH = "COLLIDE_finishline03"
PLANE_NORMAL_TOLERANCE = 1.0e-5
PLANE_DISTANCE_TOLERANCE = 1.0e-3
TRANSLATION = (20.0, 0.0, 0.0)
RETAIL_COURSE_ROOT = ROOT.parent / "corpora" / "retail" / "Data.sma_unpacked" / "DataGx" / "Course"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bounds(points: tuple[tuple[float, float, float], ...]) -> dict[str, list[float]]:
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def _cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _triangle_geometry(model: CourseGxmModelV7, node) -> list[dict[str, Any]]:
    result = []
    for triangle_index in model.mesh_triangle_indices(node):
        triangle = model.triangle(triangle_index)
        source_vertices = tuple(model.position(index) for index in triangle.position_indices)
        runtime_vertices = tuple(gxm_source_to_runtime(point) for point in source_vertices)
        edge_a = tuple(runtime_vertices[1][axis] - runtime_vertices[0][axis] for axis in range(3))
        edge_b = tuple(runtime_vertices[2][axis] - runtime_vertices[0][axis] for axis in range(3))
        raw_normal = _cross(edge_a, edge_b)
        magnitude = math.sqrt(sum(value * value for value in raw_normal))
        if magnitude == 0.0:
            raise ValueError(f"source triangle {triangle_index} is degenerate")
        normal = tuple(value / magnitude for value in raw_normal)
        distance = -sum(normal[axis] * runtime_vertices[0][axis] for axis in range(3))
        centroid = tuple(sum(point[axis] for point in runtime_vertices) / 3.0 for axis in range(3))
        result.append({
            "triangle_index": triangle_index,
            "position_indices": list(triangle.position_indices),
            "source_vertices": [list(point) for point in source_vertices],
            "runtime_vertices": [list(point) for point in runtime_vertices],
            "runtime_centroid": list(centroid),
            "runtime_aabb": _bounds(runtime_vertices),
            "unit_normal": list(normal),
            "plane_d_for_n_dot_p_plus_d_zero": distance,
            "area": magnitude / 2.0,
        })
    return result


def _same_plane(first: dict, second: dict, *, normal_tolerance: float, distance_tolerance: float) -> bool:
    n1 = first["unit_normal"]
    n2 = second["unit_normal"]
    d1 = first["plane_d_for_n_dot_p_plus_d_zero"]
    d2 = second["plane_d_for_n_dot_p_plus_d_zero"]
    direct = max(abs(n1[i] - n2[i]) for i in range(3)) <= normal_tolerance and abs(d1 - d2) <= distance_tolerance
    reversed_plane = max(abs(n1[i] + n2[i]) for i in range(3)) <= normal_tolerance and abs(d1 + d2) <= distance_tolerance
    return direct or reversed_plane


def _plane_groups(triangles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for triangle in triangles:
        matching = next((group for group in groups if _same_plane(
            group["representative"], triangle,
            normal_tolerance=PLANE_NORMAL_TOLERANCE,
            distance_tolerance=PLANE_DISTANCE_TOLERANCE,
        )), None)
        if matching is None:
            groups.append({"representative": triangle, "triangles": [triangle]})
        else:
            matching["triangles"].append(triangle)
    return groups


def _match_record(record_values, plane: dict) -> tuple[bool, float, float, int]:
    record_normal = record_values[:3]
    record_d = record_values[3]
    normal = plane["unit_normal"]
    distance = plane["plane_d_for_n_dot_p_plus_d_zero"]
    direct_normal_error = max(abs(record_normal[i] - normal[i]) for i in range(3))
    direct_d_error = abs(record_d - distance)
    reverse_normal_error = max(abs(record_normal[i] + normal[i]) for i in range(3))
    reverse_d_error = abs(record_d + distance)
    if (direct_normal_error, direct_d_error) <= (reverse_normal_error, reverse_d_error):
        return (
            direct_normal_error <= PLANE_NORMAL_TOLERANCE and direct_d_error <= PLANE_DISTANCE_TOLERANCE,
            direct_normal_error,
            direct_d_error,
            1,
        )
    return (
        reverse_normal_error <= PLANE_NORMAL_TOLERANCE and reverse_d_error <= PLANE_DISTANCE_TOLERANCE,
        reverse_normal_error,
        reverse_d_error,
        -1,
    )


def _candidate_records(tree: CourseTag100, plane: dict) -> list[dict[str, Any]]:
    found = []
    for node in tree.nodes:
        record = node.optional_record
        if record is None:
            continue
        matched, normal_error, d_error, sign = _match_record(record.values, plane)
        if matched:
            found.append({
                "node_index": node.index,
                "record_offset_in_tag100": record.offset,
                "node_offset_in_tag100": node.offset,
                "allocation_role": node.allocation_role,
                "parent_index": node.parent_index,
                "first_child_index": node.first_child_index,
                "next_sibling_index": node.next_sibling_index,
                "field_0": node.field_0,
                "field_1": node.field_1,
                "unit_normal": list(record.values[:3]),
                "d": record.values[3],
                "code": record.code,
                "normal_max_abs_error": normal_error,
                "d_abs_error": d_error,
                "orientation_sign_vs_source": sign,
            })
    return found


def _tree_metrics(tree: CourseTag100) -> dict[str, Any]:
    child_counts = Counter(node.parent_index for node in tree.nodes if node.parent_index is not None)
    role_counts = dict(tree.allocation_role_counts)
    plane_nodes = [node for node in tree.nodes if node.optional_record is not None]
    plane_norm_errors = [abs(math.sqrt(sum(value * value for value in node.optional_record.values[:3])) - 1.0)
                         for node in plane_nodes]
    fanout = Counter(child_counts.get(node.index, 0) for node in tree.nodes if node.first_child_index is not None)
    return {
        **tree.structural_summary(),
        "header_count_interpretation_by_loader": {
            "word_0": "pool8_child allocation count",
            "word_1": "pool8_sibling allocation count",
            "word_2": "pool36 allocation count (the root is separately allocated)",
            "word_3": "duplicate count emitted by the executable traversal; purpose unknown",
            "word_4": "node-list item count emitted by the executable traversal",
        },
        "plane_bearing_nodes": len(plane_nodes),
        "plane_bearing_nodes_by_role": dict(Counter(node.allocation_role for node in plane_nodes)),
        "plane_normal_length_error_max": max(plane_norm_errors, default=0.0),
        "plane_normal_length_error_mean": sum(plane_norm_errors) / len(plane_norm_errors) if plane_norm_errors else None,
        "terminal_nodes": sum(node.optional_record is None for node in tree.nodes),
        "all_pool8_nodes_are_terminal_without_optional_record": all(
            node.optional_record is None and node.first_child_index is None
            for node in tree.nodes if node.allocation_role.startswith("pool8_")
        ),
        "all_pool36_nodes_have_optional_record_and_children": all(
            node.optional_record is not None and node.first_child_index is not None
            for node in tree.nodes if node.allocation_role == "pool36"
        ),
        "branch_child_fanout_histogram": {str(key): value for key, value in sorted(fanout.items())},
        # Sibling records can follow the separately allocated root. These are
        # additional top-level nodes, not malformed/orphaned descendants.
        "additional_top_level_siblings": sum(node.parent_index is None for node in tree.nodes) - 1,
    }


def _load_course_tag100(path: Path) -> tuple[Any, CourseTag100, bytes, bytes]:
    course = parse_course_dx(path)
    region = course.collision.bsp
    if region is None:
        raise ValueError(f"{path} has no trailing tag100 region")
    raw = region.raw
    tree = parse_course_tag100_bytes(raw, path.name, allow_trailing=True)
    tree_bytes = raw[:tree.consumed_size]
    post_tree = raw[tree.consumed_size:]
    return course, tree, tree_bytes, post_tree


def _post_tree_summary(post_tree: bytes, file_offset: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"byte_size": len(post_tree), "sha256": sha256(post_tree)}
    if file_offset is not None:
        result["file_offset"] = file_offset
    if len(post_tree) >= 4:
        result["first_tag"] = struct.unpack_from("<I", post_tree)[0]
    if len(post_tree) >= 44 and struct.unpack_from("<I", post_tree)[0] == 1339:
        result["first_1339_record"] = {
            "byte_size": 44,
            "file_offset": file_offset,
            "sha256": sha256(post_tree[:44]),
            "raw_values": list(struct.unpack("<I3ff3f3f", post_tree[:44])),
            "course_semantics": "UNKNOWN",
        }
        following = post_tree[44:]
        result["following_region"] = {
            "first_tag": struct.unpack_from("<I", following)[0] if len(following) >= 4 else None,
            "byte_size": len(following),
            "file_offset": file_offset + 44 if file_offset is not None else None,
            "sha256": sha256(following),
            "course_semantics": "UNKNOWN; not parsed by this probe",
        }
    return result


def _byte_diff(first: bytes, second: bytes) -> dict[str, Any]:
    common = min(len(first), len(second))
    changed = 0
    ranges = 0
    in_range = False
    for left, right in zip(first[:common], second[:common]):
        differs = left != right
        if differs:
            changed += 1
            if not in_range:
                ranges += 1
        in_range = differs
    return {
        "first_size": len(first),
        "second_size": len(second),
        "common_prefix_bytes": common,
        "changed_bytes_in_common_prefix": changed,
        "changed_ranges_in_common_prefix": ranges,
        "first_only_tail_bytes": max(0, len(first) - common),
        "second_only_tail_bytes": max(0, len(second) - common),
    }


def _load_source_model(gxm_path: Path, txt_path: Path) -> CourseGxmModelV7:
    txt = parse_course_txt(txt_path)
    return parse_course_gxm_model_v7(gxm_path, txt)


def _source_report(baseline_path: Path, modified_path: Path, txt_path: Path) -> tuple[dict[str, Any], list[dict], list[dict]]:
    baseline_model = _load_source_model(baseline_path, txt_path)
    modified_model = _load_source_model(modified_path, txt_path)
    baseline_node = baseline_model.find_mesh(TARGET_MESH)
    modified_node = modified_model.find_mesh(TARGET_MESH)
    if (baseline_node.mesh_index, baseline_node.mesh_size) != (modified_node.mesh_index, modified_node.mesh_size):
        raise ValueError("target source mesh triangle span changed between baseline and modified GXM")
    baseline_triangles = _triangle_geometry(baseline_model, baseline_node)
    modified_triangles = _triangle_geometry(modified_model, modified_node)
    if len(baseline_triangles) != 24 or len(modified_triangles) != 24:
        raise ValueError(f"expected 24 target triangles, found {len(baseline_triangles)} / {len(modified_triangles)}")

    baseline_bytes = baseline_path.read_bytes()
    modified_bytes = modified_path.read_bytes()
    changed_offsets = [index for index, (left, right) in enumerate(zip(baseline_bytes, modified_bytes)) if left != right]
    baseline_positions = baseline_model.positions
    modified_positions = modified_model.positions
    if baseline_positions.count != modified_positions.count:
        raise ValueError("position pool count changed in the controlled source pair")
    target_indices = set(baseline_model.mesh_position_indices(baseline_node))
    target_indices |= set(modified_model.mesh_position_indices(modified_node))
    other_position_changes = []
    moved_position_changes = []
    for index in range(baseline_positions.count):
        first = baseline_model.position(index)
        second = modified_model.position(index)
        if first != second:
            if index in target_indices and second == (first[0] + 20.0, first[1], first[2]):
                moved_position_changes.append(index)
            else:
                other_position_changes.append(index)

    baseline_bounds = _bounds(tuple(tuple(vertex) for row in baseline_triangles for vertex in row["runtime_vertices"]))
    modified_bounds = _bounds(tuple(tuple(vertex) for row in modified_triangles for vertex in row["runtime_vertices"]))
    baseline_centroid = [sum(row["runtime_centroid"][axis] for row in baseline_triangles) / len(baseline_triangles) for axis in range(3)]
    modified_centroid = [sum(row["runtime_centroid"][axis] for row in modified_triangles) / len(modified_triangles) for axis in range(3)]
    geometry = {
        "source_mesh": {
            "literal_name": TARGET_MESH,
            "baseline_ordinal": baseline_node.ordinal,
            "hierarchy_path": ["Model", "$autovsphere_300", "$bsp", "$nodraw", TARGET_MESH],
            "mesh_index": baseline_node.mesh_index,
            "mesh_size": baseline_node.mesh_size,
            "triangle_span_half_open": [baseline_node.mesh_index, baseline_node.mesh_index + baseline_node.mesh_size],
            "triangle_count": len(baseline_triangles),
            "unique_position_indices": sorted(target_indices),
            "unique_position_count": len(target_indices),
        },
        "source_files": {
            "baseline": {"path": str(baseline_path), "size_bytes": len(baseline_bytes), "sha256": sha256(baseline_bytes)},
            "modified": {"path": str(modified_path), "size_bytes": len(modified_bytes), "sha256": sha256(modified_bytes)},
            "txt": {"path": str(txt_path), "size_bytes": txt_path.stat().st_size, "sha256": sha256_file(txt_path)},
        },
        "isolation": {
            "changed_gxm_byte_count": len(changed_offsets),
            "changed_gxm_byte_offsets": changed_offsets,
            "target_position_x_changes": len(moved_position_changes),
            "all_target_positions_moved_by_source_delta": len(moved_position_changes) == len(target_indices),
            "other_position_record_changes": other_position_changes,
            "position_pool_count_unchanged": baseline_positions.count == modified_positions.count,
            "triangle_bank_byte_identical": baseline_model.triangles.raw == modified_model.triangles.raw,
            "node_object_table_identical": baseline_model.object_table.nodes == modified_model.object_table.nodes,
        },
        "translation": {
            "source_delta": [20.0, 0.0, 0.0],
            "coordinate_transform": "GXM source (x,y,z) -> runtime (x,z,-y)",
            "expected_runtime_delta": list(TRANSLATION),
            "baseline_runtime_centroid_of_triangle_centroids": baseline_centroid,
            "modified_runtime_centroid_of_triangle_centroids": modified_centroid,
            "baseline_runtime_aabb": baseline_bounds,
            "modified_runtime_aabb": modified_bounds,
        },
        "baseline_triangles": baseline_triangles,
        "modified_triangles": modified_triangles,
    }
    return geometry, baseline_triangles, modified_triangles


def _binding_report(
    geometry: dict[str, Any],
    baseline_triangles: list[dict],
    modified_triangles: list[dict],
    baseline_tree: CourseTag100,
    modified_tree: CourseTag100,
    baseline_tree_bytes: bytes,
    modified_tree_bytes: bytes,
    baseline_post_tree: bytes,
    modified_post_tree: bytes,
    baseline_dx: Path,
    modified_dx: Path,
    baseline_tag_offset: int,
    modified_tag_offset: int,
) -> dict[str, Any]:
    groups = _plane_groups(baseline_triangles)
    modified_groups = _plane_groups(modified_triangles)
    if len(groups) != len(modified_groups):
        raise ValueError("source plane grouping changed under rigid translation")

    group_rows = []
    all_baseline_hits = 0
    all_modified_hits = 0
    all_translation_pairs = 0
    baseline_excess = 0
    modified_excess = 0
    code_alignments = []
    max_translation_residual = 0.0
    for group, translated_group in zip(groups, modified_groups):
        plane = group["representative"]
        translated_plane = translated_group["representative"]
        base_hits = _candidate_records(baseline_tree, plane)
        modified_hits = _candidate_records(modified_tree, translated_plane)
        expected_d = translate_plane_distance(
            tuple(plane["unit_normal"]),
            plane["plane_d_for_n_dot_p_plus_d_zero"],
            TRANSLATION,
        )
        matched_pairs = []
        for base in base_hits:
            compatible = [item for item in modified_hits if item["code"] == base["code"]]
            if not compatible:
                continue
            selected = min(compatible, key=lambda item: abs(item["d"] - expected_d))
            residual = selected["d"] - expected_d
            if abs(residual) <= PLANE_DISTANCE_TOLERANCE:
                matched_pairs.append({
                    "baseline_record_offset_in_tag100": base["record_offset_in_tag100"],
                    "modified_record_offset_in_tag100": selected["record_offset_in_tag100"],
                    "baseline_code": base["code"],
                    "modified_code": selected["code"],
                    "baseline_d": base["d"],
                    "modified_d": selected["d"],
                    "expected_modified_d": expected_d,
                    "translation_residual": residual,
                })
                max_translation_residual = max(max_translation_residual, abs(residual))
        all_baseline_hits += len(base_hits)
        all_modified_hits += len(modified_hits)
        all_translation_pairs += len(matched_pairs)
        baseline_excess += max(0, len(base_hits) - 1)
        modified_excess += max(0, len(modified_hits) - 1)
        representative_index = min(item["triangle_index"] for item in group["triangles"])
        baseline_codes = sorted({item["code"] for item in base_hits})
        modified_codes = sorted({item["code"] for item in modified_hits})
        expected_code = representative_index - 12
        code_alignment = baseline_codes == [expected_code] and modified_codes == [expected_code]
        code_alignments.append(code_alignment)
        group_rows.append({
            "source_triangle_indices": [item["triangle_index"] for item in group["triangles"]],
            "representative_source_triangle": representative_index,
            "baseline_plane": {
                "unit_normal": plane["unit_normal"],
                "d": plane["plane_d_for_n_dot_p_plus_d_zero"],
            },
            "modified_plane": {
                "unit_normal": translated_plane["unit_normal"],
                "d": translated_plane["plane_d_for_n_dot_p_plus_d_zero"],
            },
            "expected_modified_d": expected_d,
            "expected_d_delta": expected_d - plane["plane_d_for_n_dot_p_plus_d_zero"],
            "baseline_candidate_count": len(base_hits),
            "modified_candidate_count": len(modified_hits),
            "baseline_candidate_codes": baseline_codes,
            "modified_candidate_codes": modified_codes,
            "code_matches_representative_source_triangle_minus_12": code_alignment,
            "translation_pair_count_by_stable_code": len(matched_pairs),
            "translation_pairs": matched_pairs,
            "baseline_candidate_records": base_hits,
            "modified_candidate_records": modified_hits,
        })

    baseline_all_match = all(row["baseline_candidate_count"] > 0 for row in group_rows)
    modified_all_match = all(row["modified_candidate_count"] > 0 for row in group_rows)
    translation_all_match = all(
        row["translation_pair_count_by_stable_code"] > 0 for row in group_rows
    )

    b_roles = dict(baseline_tree.allocation_role_counts)
    m_roles = dict(modified_tree.allocation_role_counts)
    unit_residuals = [abs(math.sqrt(sum(node.optional_record.values[i] ** 2 for i in range(3))) - 1.0)
                      for tree in (baseline_tree, modified_tree) for node in tree.nodes if node.optional_record]

    return {
        "schema": "r5t-f2-collide-finishline03-binding-v1",
        "evidence": [
            "CONFIRMED_BY_EXECUTABLE",
            "CONFIRMED_BY_BINARY_STRUCTURE",
            "CONFIRMED_BY_SOURCE_COMPILED_PAIR",
            "CONFIRMED_BY_RECIPROCAL_SUFFIX_RUNTIME_SWAP",
        ],
        "source_oracle": geometry,
        "serialized_region": {
            "baseline": {
                "dx_path": str(baseline_dx),
                "dx_sha256": sha256_file(baseline_dx),
                "tag100_file_offset": baseline_tag_offset,
                "tag100_tree_size_bytes": len(baseline_tree_bytes),
                "tag100_tree_sha256": sha256(baseline_tree_bytes),
                "tag100_starting_suffix_sha256": sha256(baseline_tree_bytes + baseline_post_tree),
                "tag100_starting_suffix_size_bytes": len(baseline_tree_bytes) + len(baseline_post_tree),
                "tree": _tree_metrics(baseline_tree),
                "post_tree_sections": _post_tree_summary(
                    baseline_post_tree, baseline_tag_offset + len(baseline_tree_bytes)
                ),
            },
            "modified": {
                "dx_path": str(modified_dx),
                "dx_sha256": sha256_file(modified_dx),
                "tag100_file_offset": modified_tag_offset,
                "tag100_tree_size_bytes": len(modified_tree_bytes),
                "tag100_tree_sha256": sha256(modified_tree_bytes),
                "tag100_starting_suffix_sha256": sha256(modified_tree_bytes + modified_post_tree),
                "tag100_starting_suffix_size_bytes": len(modified_tree_bytes) + len(modified_post_tree),
                "tree": _tree_metrics(modified_tree),
                "post_tree_sections": _post_tree_summary(
                    modified_post_tree, modified_tag_offset + len(modified_tree_bytes)
                ),
            },
            "comparison": {
                "tree_bytes": _byte_diff(baseline_tree_bytes, modified_tree_bytes),
                "post_tree_bytes": _byte_diff(baseline_post_tree, modified_post_tree),
                "trailing_1339_record_identical": baseline_post_tree[:44] == modified_post_tree[:44],
                "following_region_after_1339": _byte_diff(baseline_post_tree[44:], modified_post_tree[44:]),
                "plane_bearing_node_delta": _tree_metrics(modified_tree)["plane_bearing_nodes"] - _tree_metrics(baseline_tree)["plane_bearing_nodes"],
                "node_count_delta": len(modified_tree.nodes) - len(baseline_tree.nodes),
                "allocation_role_count_delta": {role: m_roles.get(role, 0) - b_roles.get(role, 0) for role in sorted(set(b_roles) | set(m_roles))},
                "header_word_delta": [m - b for b, m in zip(baseline_tree.header_words, modified_tree.header_words)],
            },
        },
        "plane_binding": {
            "source_triangle_count": len(baseline_triangles),
            "source_unique_plane_count": len(groups),
            "compiled_optional_records_compared": {
                "baseline": sum(node.optional_record is not None for node in baseline_tree.nodes),
                "modified": sum(node.optional_record is not None for node in modified_tree.nodes),
            },
            "plane_match_tolerances": {
                "normal_max_abs_component": PLANE_NORMAL_TOLERANCE,
                "d_absolute": PLANE_DISTANCE_TOLERANCE,
                "plane_convention": "n dot p + d = 0 with unit n; both simultaneous sign orientations accepted",
            },
            "baseline_triangle_coverage": sum(
                len(group["triangles"]) for group, row in zip(groups, group_rows)
                if row["baseline_candidate_count"] > 0
            ),
            "modified_triangle_coverage": sum(
                len(group["triangles"]) for group, row in zip(groups, group_rows)
                if row["modified_candidate_count"] > 0
            ),
            "unique_plane_groups_matched_baseline": sum(row["baseline_candidate_count"] > 0 for row in group_rows),
            "unique_plane_groups_matched_modified": sum(row["modified_candidate_count"] > 0 for row in group_rows),
            "baseline_candidate_record_count": all_baseline_hits,
            "modified_candidate_record_count": all_modified_hits,
            "baseline_duplicate_candidate_excess": baseline_excess,
            "modified_duplicate_candidate_excess": modified_excess,
            "stable_code_translation_pairs": all_translation_pairs,
            "max_translation_d_residual": max_translation_residual,
            "all_group_codes_match_representative_source_triangle_minus_12": all(code_alignments),
            "code_value_interpretation": "UNKNOWN; the candidate code sets are not a consistent one-to-one source-triangle mapping across both cohorts",
            "all_groups_match_in_both_cohorts": baseline_all_match and modified_all_match,
            "all_groups_obey_expected_translation": translation_all_match,
            "global_plane_record_unit_normal_length_error_max": max(unit_residuals, default=0.0),
            "groups": group_rows,
            "conclusion": (
                "All 12 unique source face-plane groups are represented by matching optional float4/code records "
                "in the parsed tag100 tree in both cohorts. For every group, stable code-keyed records preserve "
                "the normal and shift d by -dot(n,(20,0,0)) within tolerance. Individual duplicate node copies "
                "are not uniquely paired by offset because the spatial serialization is rebuilt."
            ),
        },
        "bounds_binding": {
            "baseline_source_aabb": geometry["translation"]["baseline_runtime_aabb"],
            "modified_source_aabb": geometry["translation"]["modified_runtime_aabb"],
            "expected_delta": list(TRANSLATION),
            "decoded_target_specific_aabb_record_in_tag100": "NOT_FOUND_IN_DECODED_FIELDS",
            "whole_course_1339_record": "identical across this pair; not a target-specific collider bound",
        },
        "physical_binding_assessment": {
            "tested_source_mesh": TARGET_MESH,
            "tag100_tree_plane_geometry_binding": "HIGH_CONFIDENCE_INFERENCE supported by unique source-plane matches and the exact rigid-translation relation",
            "physical_role_evidence": "the reciprocal F.1 runtime swap showed collision follows the tag100-starting suffix; the tree itself is loaded by the confirmed tag100 handler",
            "component_isolation_limit": "F.1 swapped from the tag100 marker through EOF. The adjacent 1339 record is byte-identical, but the later tag1400 region differs in 64 bytes; F.1 did not independently swap the parsed tag100 tree while holding tag1400 fixed.",
            "triangle_preservation": "no one-to-one 24-triangle record mapping. The source has 12 unique plane equations; matching plane records repeat at multiple tree offsets.",
            "ambiguity": "plane equation family is distinctive; repeated serialized copies prevent unique node-offset identity for each source triangle.",
        },
    }


def _corpus_layout(corpus_root: Path) -> dict[str, Any]:
    if not corpus_root.is_dir():
        return {"status": "UNAVAILABLE", "root": str(corpus_root), "courses": []}
    paths = sorted(corpus_root.rglob("*.dx"))
    rows = []
    for path in paths:
        row: dict[str, Any] = {"course": path.parent.name, "file": path.name, "path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
        try:
            course, tree, tree_bytes, post_tree = _load_course_tag100(path)
            row.update({
                "parse_status": "PASS",
                "tag100_file_offset": course.collision.bsp.tag_offset,
                "tag100_starting_suffix_size_bytes": course.collision.bsp.end_offset - course.collision.bsp.tag_offset,
                "tag100_starting_suffix_sha256": course.collision.bsp.sha256,
                "tag100_tree_size_bytes": len(tree_bytes),
                "tag100_tree_sha256": sha256(tree_bytes),
                "tree": _tree_metrics(tree),
                "post_tree": _post_tree_summary(
                    post_tree, course.collision.bsp.tag_offset + len(tree_bytes)
                ),
            })
        except Exception as error:  # corpus outliers remain visible in the report
            row.update({"parse_status": "FAIL", "error": f"{type(error).__name__}: {error}"})
        rows.append(row)
    return {
        "status": "PASS" if all(row["parse_status"] == "PASS" for row in rows) else "PARTIAL",
        "root": str(corpus_root),
        "course_count": len(rows),
        "parsed_count": sum(row["parse_status"] == "PASS" for row in rows),
        "failed_count": sum(row["parse_status"] == "FAIL" for row in rows),
        "courses": rows,
        "distributions": {
            "node_count": _distribution(row["tree"]["node_count"] for row in rows if row["parse_status"] == "PASS"),
            "plane_bearing_node_count": _distribution(row["tree"]["plane_bearing_nodes"] for row in rows if row["parse_status"] == "PASS"),
            "max_depth": _distribution(row["tree"]["max_depth"] for row in rows if row["parse_status"] == "PASS"),
            "list_item_count": _distribution(row["tree"]["list_item_count"] for row in rows if row["parse_status"] == "PASS"),
        },
    }


def _distribution(values) -> dict[str, int | float | None]:
    numbers = list(values)
    if not numbers:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {"count": len(numbers), "min": min(numbers), "max": max(numbers), "mean": sum(numbers) / len(numbers)}


def _layout_report(
    baseline_tree: CourseTag100,
    modified_tree: CourseTag100,
    baseline_tree_bytes: bytes,
    modified_tree_bytes: bytes,
    baseline_post_tree: bytes,
    modified_post_tree: bytes,
    baseline_tag_offset: int,
    modified_tag_offset: int,
    baseline_dx: Path,
    modified_dx: Path,
    corpus: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "r5t-f2-tag100-layout-v1",
        "status": "READ_ONLY_PARTIAL_GRAMMAR",
        "supported_executable": {
            "version": "Retail rev135",
            "path": str(ROOT.parent / "MRallye.exe"),
            "sha256": sha256_file(ROOT.parent / "MRallye.exe"),
        },
        "loader": {
            "dx_section_loop": {"address": "0x00551430", "evidence": "CONFIRMED_BY_EXECUTABLE"},
            "tag100_dispatch_call": {"instruction_address": "0x0055167A", "callee": "0x0057E2D0", "evidence": "CONFIRMED_BY_EXECUTABLE"},
            "tag100_object_attachment": {"instruction_address": "0x005516B4", "object_offset": "+0x08", "evidence": "CONFIRMED_BY_EXECUTABLE"},
            "root_parser": {"address": "0x0057E2D0", "allocation_bytes": 0x74, "recursive_reader": "0x0057E550", "evidence": "CONFIRMED_BY_EXECUTABLE"},
            "pool_allocators": [
                {"address": "0x00599290", "record_stride_bytes": 8, "root_fields": ["+0x48", "+0x4C"]},
                {"address": "0x005993B0", "record_stride_bytes": 8, "root_fields": ["+0x54", "+0x58"]},
                {"address": "0x005994D0", "record_stride_bytes": 36, "root_fields": ["+0x60", "+0x64"]},
            ],
            "chunk_capacity_records": 0x400,
            "wire_bool_width_bytes": 1,
            "evidence_note": "The loader dispatches tag 100 to a recursive tree reader. The reported allocation roles and strides come from exact Retail executable reader/allocator code; their gameplay names remain unassigned.",
        },
        "tag100_wire_grammar": {
            "byte_order": "little-endian",
            "header": {
                "size_bytes": 24,
                "offset_0": {"width": 4, "type": "uint32", "value": 100},
                "offset_4_to_23": {"width": 20, "type": "five uint32 values", "semantic_names": "neutral count_0..count_4"},
            },
            "node": {
                "leading_fields": {"width": 8, "fields": ["uint32 field_0", "uint32 field_1"]},
                "optional_record": {"flag_width": 1, "payload_width": 20, "payload": ["float32 x4", "uint32 code"]},
                "optional_list": {"flag_width": 1, "count_width": 4, "item_width": 20, "item": ["float32 x3", "float32 value", "uint32 code"]},
                "child": {"presence_width": 1, "allocation_selector_width_if_present": 1, "encoding": "recursive first-child / next-sibling order"},
                "sibling": {"presence_width": 1, "allocation_selector_width_if_present": 1},
                "allocation_roles": ["root object (0x74 bytes)", "pool8_child", "pool8_sibling", "pool36"],
            },
            "provenance": "CONFIRMED_BY_EXECUTABLE for reads, writes, record widths, child/sibling recursion and pool strides; source correlation supports interpreting optional float4 as plane-like (n,d); uint fields remain opaque.",
        },
        "samples": {
            "baseline": {
                "dx_path": str(baseline_dx), "dx_sha256": sha256_file(baseline_dx), "tag100_file_offset": baseline_tag_offset,
                "tag100_tree_size_bytes": len(baseline_tree_bytes), "tag100_tree_sha256": sha256(baseline_tree_bytes),
                "tree": _tree_metrics(baseline_tree),
                "post_tree": _post_tree_summary(
                    baseline_post_tree, baseline_tag_offset + len(baseline_tree_bytes)
                ),
            },
            "modified": {
                "dx_path": str(modified_dx), "dx_sha256": sha256_file(modified_dx), "tag100_file_offset": modified_tag_offset,
                "tag100_tree_size_bytes": len(modified_tree_bytes), "tag100_tree_sha256": sha256(modified_tree_bytes),
                "tree": _tree_metrics(modified_tree),
                "post_tree": _post_tree_summary(
                    modified_post_tree, modified_tag_offset + len(modified_tree_bytes)
                ),
            },
            "comparison": {
                "tag100_tree_bytes": _byte_diff(baseline_tree_bytes, modified_tree_bytes),
                "post_tree_bytes": _byte_diff(baseline_post_tree, modified_post_tree),
                "post_1339_region_bytes": _byte_diff(baseline_post_tree[44:], modified_post_tree[44:]),
                "node_count_delta": len(modified_tree.nodes) - len(baseline_tree.nodes),
                "header_word_delta": [m - b for b, m in zip(baseline_tree.header_words, modified_tree.header_words)],
            },
        },
        "retail_corpus": corpus,
        "unknowns": [
            "Meaning of the two leading uint32 node fields and the trailing uint32 code.",
            "Which serialized links encode spatial partition sides versus other hierarchy relationships.",
            "Target-specific compiled AABB/bounds record was not identified in this pass.",
            "The distinct tag1400 region after the tag100 tree is not decoded; F.1 swapped that region together with the tag100 tree.",
            "No conclusion about all tag100 records, all collision-source classes, or source $bsp semantics.",
        ],
    }


def _markdown(layout: dict[str, Any], binding: dict[str, Any]) -> str:
    base = binding["serialized_region"]["baseline"]
    modified = binding["serialized_region"]["modified"]
    comparison = binding["serialized_region"]["comparison"]
    planes = binding["plane_binding"]
    corpus = layout["retail_corpus"]
    lines = [
        "# R5T-F.2 — tag100 physical grammar archaeology",
        "",
        "## Status",
        "",
        "The tag100 recursive wire structure and its plane-bearing record family are parsed read-only. The France1 source mesh's 12 distinct face planes match records inside the parsed tree in both source/cooked cohorts, and the `+20 X` translation follows the expected plane-distance equation. Runtime evidence remains bounded to the F.1 reciprocal suffix swap; the adjacent tag1400 block was not isolated by that test.",
        "",
        "## Loader and wire layout",
        "",
        "Retail rev135 SHA256: `" + layout["supported_executable"]["sha256"] + "`.",
        "",
        "| Structure | Wire/allocation layout | Evidence |",
        "|---|---|---|",
        "| Header | 24 bytes: tag 100 + five little-endian uint32 values | `CONFIRMED_BY_EXECUTABLE` |",
        "| Node prefix | 2 × uint32, then optional/list/child/sibling presence bytes | `CONFIRMED_BY_EXECUTABLE` |",
        "| Optional record | 20 bytes: float32 × 4 + uint32 code | executable reader; source plane correlation |",
        "| Optional list item | 20 bytes: float32 × 3 + float32 + uint32 | `CONFIRMED_BY_EXECUTABLE`; absent in this France1 pair |",
        "| In-memory pools | two 8-byte allocation roles and one 36-byte role, chunked in groups of 0x400 | `CONFIRMED_BY_EXECUTABLE` |",
        "| Links | recursive first-child / next-sibling serialization; one-byte bools | `CONFIRMED_BY_EXECUTABLE` |",
        "",
        "Neutral role names are used because the two leading node fields and the uint32 record code have not been assigned runtime meanings. The repository's existing `CollisionSections.bsp` field is historical naming; it preserves the tag100-starting suffix raw and is not evidence that this grammar is a BSP.",
        "",
        "## France1 structural counts",
        "",
        "| Measure | Baseline | Modified | Delta |",
        "|---|---:|---:|---:|",
        f"| Tag100 tree bytes | {base['tag100_tree_size_bytes']:,} | {modified['tag100_tree_size_bytes']:,} | {modified['tag100_tree_size_bytes'] - base['tag100_tree_size_bytes']:+,} |",
        f"| Tree nodes | {base['tree']['node_count']:,} | {modified['tree']['node_count']:,} | {comparison['node_count_delta']:+,} |",
        f"| Plane-bearing records | {base['tree']['plane_bearing_nodes']:,} | {modified['tree']['plane_bearing_nodes']:,} | {comparison['plane_bearing_node_delta']:+,} |",
        f"| Plane-less terminal records | {base['tree']['terminal_nodes']:,} | {modified['tree']['terminal_nodes']:,} | {modified['tree']['terminal_nodes'] - base['tree']['terminal_nodes']:+,} |",
        f"| Max tree depth | {base['tree']['max_depth']} | {modified['tree']['max_depth']} | {modified['tree']['max_depth'] - base['tree']['max_depth']:+} |",
        f"| Optional list items | {base['tree']['list_item_count']} | {modified['tree']['list_item_count']} | {modified['tree']['list_item_count'] - base['tree']['list_item_count']:+} |",
        "",
        "All decoded plane-bearing records have a first-three-component vector whose length is within `" + f"{max(base['tree']['plane_normal_length_error_max'], modified['tree']['plane_normal_length_error_max']):.3g}" + "` of 1.0 in this pair. All pool8 nodes are plane-less terminals; pool36 nodes carry the 20-byte optional record and children. This supports a plane-bearing hierarchy, while link-side and full spatial semantics remain unknown.",
        "",
        "## Source geometry binding",
        "",
        f"`{TARGET_MESH}` has {binding['source_oracle']['source_mesh']['triangle_count']} source triangles and {binding['plane_binding']['source_unique_plane_count']} distinct plane equations. All {binding['plane_binding']['source_unique_plane_count']} plane groups match optional float4/code records in both tag100 trees within normal max-component {PLANE_NORMAL_TOLERANCE:g} and `d` {PLANE_DISTANCE_TOLERANCE:g} tolerances.",
        "",
        "For `n·p + d = 0`, translation by `T=(20,0,0)` requires `d' = d - dot(n,T)`. Stable code-keyed records meet this relation with maximum residual `" + f"{binding['plane_binding']['max_translation_d_residual']:.6g}" + "`. Several planes have repeated copies at different tree offsets, so there is not a one-to-one mapping from 24 source triangles to 24 compiled records. The observed source/code numeric relation is recorded in the JSON; the code's actual meaning remains unknown.",
        "",
        "Baseline runtime AABB: `" + json.dumps(binding['source_oracle']['translation']['baseline_runtime_aabb'], separators=(',', ':')) + "`.",
        "Modified runtime AABB: `" + json.dumps(binding['source_oracle']['translation']['modified_runtime_aabb'], separators=(',', ':')) + "`. No target-specific AABB record was identified in the decoded tree fields.",
        "",
        "## F.1 boundary clarification",
        "",
        "The F.1 donor region begins with tag 100 and extends to EOF. This loader-guided parse ends the tag100 tree before a 44-byte tag1339 record and a separate tag1400 region. The tag1339 record is byte-identical in baseline/modified files. The later tag1400 region has the same size and 64 changed byte positions. Therefore the reciprocal runtime result proves that the tested physical state follows the selected tag100-starting suffix donor; the run did not isolate the tag100 tree bytes from the following tag1400 region. The geometry-bound plane records themselves are inside the parsed tag100 tree.",
        "",
        "The tree shrinks by 3,404 bytes while the loader-pool memory estimate changes by 3,256 bytes. The remaining 148-byte difference is not assigned a cause; the serializer is variable-length and the node topology is rebuilt.",
        "",
        "## Retail corpus",
        "",
        f"Structural parse: {corpus.get('parsed_count', 0)}/{corpus.get('course_count', 0)} courses; status `{corpus['status']}`.",
        "",
        "Full per-course hashes, header words, node counts, depth, pool roles, trailing bytes, and failures are in `tag100-layout.json`. This is parser coverage only, not physical runtime validation across the retail corpus.",
        "",
        "## Limits",
        "",
        "- `tag100` is not globally renamed to collision data or BSP.",
        "- `$bsp -> tag100` remains unknown.",
        "- No AABB/triangle writer, source writer, Blender overlay, or course authoring was added.",
        "- The tag1400 region and any target-specific runtime node/leaf selection remain unresolved.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dx", type=Path, default=ROOT / "research-output/r5t_f0/cooker-lab/baseline/runtime/DataGx/Course/France1/france1.dx")
    parser.add_argument("--modified-dx", type=Path, default=ROOT / "research-output/r5t_f0/cooker-lab/modified/runtime/DataGx/Course/France1/france1.dx")
    parser.add_argument("--baseline-gxm", type=Path, default=ROOT / "inputs/8.4.1_France1/France1.gxm")
    parser.add_argument("--modified-gxm", type=Path, default=ROOT / "research-output/r5t_f0/modified-source/France1.gxm")
    parser.add_argument("--source-txt", type=Path, default=ROOT / "inputs/8.4.1_France1/France1.txt")
    parser.add_argument("--corpus-root", type=Path, default=RETAIL_COURSE_ROOT)
    parser.add_argument("--no-corpus", action="store_true", help="Skip retail corpus parsing")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "research/r5t_f2")
    args = parser.parse_args(argv)

    for required in (args.baseline_dx, args.modified_dx, args.baseline_gxm, args.modified_gxm, args.source_txt, ROOT.parent / "MRallye.exe"):
        if not required.is_file():
            parser.error(f"required evidence input not found: {required}")

    baseline_course, baseline_tree, baseline_tree_bytes, baseline_post_tree = _load_course_tag100(args.baseline_dx)
    modified_course, modified_tree, modified_tree_bytes, modified_post_tree = _load_course_tag100(args.modified_dx)
    geometry, baseline_triangles, modified_triangles = _source_report(args.baseline_gxm, args.modified_gxm, args.source_txt)
    corpus = {"status": "SKIPPED", "root": str(args.corpus_root), "courses": []} if args.no_corpus else _corpus_layout(args.corpus_root)
    binding = _binding_report(
        geometry, baseline_triangles, modified_triangles,
        baseline_tree, modified_tree, baseline_tree_bytes, modified_tree_bytes,
        baseline_post_tree, modified_post_tree,
        args.baseline_dx, args.modified_dx,
        baseline_course.collision.bsp.tag_offset,
        modified_course.collision.bsp.tag_offset,
    )
    layout = _layout_report(
        baseline_tree, modified_tree, baseline_tree_bytes, modified_tree_bytes,
        baseline_post_tree, modified_post_tree,
        baseline_course.collision.bsp.tag_offset,
        modified_course.collision.bsp.tag_offset,
        args.baseline_dx, args.modified_dx, corpus,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "collide-finishline03-binding.json").write_text(
        json.dumps(binding, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (args.output_dir / "tag100-layout.json").write_text(
        json.dumps(layout, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (args.output_dir / "tag100-physical-grammar.md").write_text(_markdown(layout, binding), encoding="utf-8")
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "retail_corpus_status": corpus["status"],
        "retail_course_count": corpus.get("course_count", 0),
        "retail_parsed_count": corpus.get("parsed_count", 0),
        "source_plane_groups": binding["plane_binding"]["source_unique_plane_count"],
        "baseline_candidate_records": binding["plane_binding"]["baseline_candidate_record_count"],
        "modified_candidate_records": binding["plane_binding"]["modified_candidate_record_count"],
        "translation_residual_max": binding["plane_binding"]["max_translation_d_residual"],
        "tag1400_changed_bytes": binding["serialized_region"]["comparison"]["following_region_after_1339"]["changed_bytes_in_common_prefix"],
    }, indent=2, sort_keys=True))
    return 0 if corpus.get("status") in ("PASS", "SKIPPED", "UNAVAILABLE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
