#!/usr/bin/env python3
"""R5T-F.0 read-only spatial report and one pinned France1 source-copy probe."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.course_gxm import (
    CourseGxmNode,
    CourseGxmModelV7,
    parse_course_gxm_model_v7,
    parse_course_gxm_model_v7_bytes,
)
from master_rallye.course_source import parse_course_txt
from master_rallye.course_spatial import (
    MeshSpanRef,
    analyze_source_mesh,
    centroid3,
    distance3,
    gxm_source_to_runtime,
    pair_to_marker_polygon,
    point_to_marker_polygon,
    position_mesh_owners,
    runtime_to_blender,
)
from master_rallye.course_xml import CourseXmlMarkerList, parse_course_xml


EXPECTED_FRANCE1_GXM_SHA256 = "56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2"
PROBE_TARGET = "COLLIDE_finishline03"
PROBE_DELTA_SOURCE = (20.0, 0.0, 0.0)
NAMED_FINISH_MESHES = {
    "COLLIDE_finishline01": (47011, 24),
    "COLLIDE_finishline": (47035, 24),
    "COLLIDE_finishline02": (47059, 24),
    "COLLIDE_finishline03": (47083, 24),
}
START_PAIR = ("COLLIDE_finishline01", "COLLIDE_finishline")
FINISH_PAIR = ("COLLIDE_finishline02", "COLLIDE_finishline03")
SOURCE_GXM = ROOT / "inputs" / "8.4.1_France1" / "France1.gxm"
SOURCE_TXT = ROOT / "inputs" / "8.4.1_France1" / "France1.txt"
RETAIL_FRANCE_XML = ROOT.parent / "corpora" / "retail" / "Data.sma_unpacked" / "DataScene" / "RaceTest" / "France1.xml"
REPORT_PATH = ROOT / "research" / "r5t_f0" / "france1-named-geometry-correlation.json"
PROBE_ROOT = ROOT / "research-output" / "r5t_f0"
MODIFIED_GXM = PROBE_ROOT / "modified-source" / "France1.gxm"
MANIFEST_PATH = ROOT / "research" / "r5t_f0" / "probe-manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _vector_dict(point):
    return {"x": point[0], "y": point[1], "z": point[2]}


def _bounds_dict(bounds):
    if bounds is None:
        return None
    return {"min": list(bounds[0]), "max": list(bounds[1])}


def _node_path(model: CourseGxmModelV7, node: CourseGxmNode) -> tuple[str, ...]:
    by_ordinal = {item.ordinal: item for item in model.object_table.nodes}
    path = [node.name]
    parent_id = node.parent_id
    seen = {node.ordinal}
    while parent_id is not None and parent_id in by_ordinal and parent_id not in seen:
        parent = by_ordinal[parent_id]
        path.append(parent.name)
        seen.add(parent_id)
        parent_id = parent.parent_id
    return tuple(reversed(path))


def _area_record(marker_list: CourseXmlMarkerList) -> dict[str, Any]:
    markers = []
    for marker in marker_list.markers:
        markers.append({
            "ordinal": marker.ordinal,
            "index_in_list": marker.index_in_list,
            "marker_no": marker.marker_no,
            "position_runtime_xml": list(marker.position) if marker.position else None,
            "direction_runtime_xml": list(marker.direction) if marker.direction else None,
            "xml_path": marker.record.xml_path,
        })
    positions = [item["position_runtime_xml"] for item in markers]
    if any(position is None for position in positions):
        raise ValueError(f"{marker_list.name} contains a marker without a parsed position")
    return {
        "name": marker_list.name,
        "ordinal": marker_list.ordinal,
        "xml_path": marker_list.xml_path,
        "evidence": "CONFIRMED_BY_RUNTIME_EDIT" if marker_list.name in {"StartArea", "FinishArea"} else "UNKNOWN",
        "coordinate_space": "RaceTest runtime/XML coordinates",
        "markers": markers,
        "centroid": list(centroid3(positions)),
    }


def _edge_metrics_for_point(point, positions):
    metric = point_to_marker_polygon(point, positions)
    edge_rows = []
    for index, (segment_distance, midpoint_distance) in enumerate(zip(
        metric.edge_segment_distances_xz, metric.edge_midpoint_distances_xz,
    )):
        edge_rows.append({
            "edge_index": index,
            "from_marker_index": index,
            "to_marker_index": (index + 1) % len(positions),
            "segment_distance_xz": segment_distance,
            "midpoint_distance_xz": midpoint_distance,
        })
    nearest = min(edge_rows, key=lambda edge: edge["segment_distance_xz"])
    nearest_marker_index = min(range(len(metric.marker_distances_3d)), key=metric.marker_distances_3d.__getitem__)
    return {
        "marker_distances_3d": list(metric.marker_distances_3d),
        "nearest_marker": {
            "index_in_list": nearest_marker_index,
            "marker_no": str(nearest_marker_index),
            "distance_3d": metric.marker_distances_3d[nearest_marker_index],
        },
        "polygon_centroid_runtime_xml": list(metric.polygon_centroid),
        "distance_to_polygon_centroid_3d": metric.distance_to_polygon_centroid_3d,
        "edge_comparisons_xz": edge_rows,
        "nearest_edge_by_segment_distance": nearest,
    }


def _mesh_record(model, node, areas: dict[str, CourseXmlMarkerList]) -> dict[str, Any]:
    metrics = analyze_source_mesh(model, node)
    if metrics.source_centroid is None or metrics.runtime_centroid is None:
        raise ValueError(f"mesh {node.name!r} has no referenced positions")
    areas_by_name = {}
    for area_name, marker_list in areas.items():
        positions = tuple(marker.position for marker in marker_list.markers)
        if any(position is None for position in positions):
            raise ValueError(f"marker list {area_name!r} contains missing positions")
        areas_by_name[area_name] = _edge_metrics_for_point(
            metrics.runtime_centroid, positions,
        )
    return {
        "literal_source_name": node.name,
        "hierarchy_path": list(_node_path(model, node)),
        "source_ordinal": node.ordinal,
        "Index": node.mesh_index,
        "Size": node.mesh_size,
        "triangle_count": metrics.triangle_count,
        "unique_position_count": len(metrics.unique_position_indices),
        "unique_position_indices": list(metrics.unique_position_indices),
        "source_centroid": list(metrics.source_centroid),
        "runtime_centroid": list(metrics.runtime_centroid),
        "blender_centroid_inferred": list(runtime_to_blender(metrics.runtime_centroid)),
        "source_bounds": _bounds_dict(metrics.source_bounds),
        "runtime_bounds": _bounds_dict(metrics.runtime_bounds),
        "source_dimensions": list(metrics.source_dimensions) if metrics.source_dimensions else None,
        "runtime_dimensions": list(metrics.runtime_dimensions) if metrics.runtime_dimensions else None,
        "vertical_extent_runtime": metrics.runtime_dimensions[1] if metrics.runtime_dimensions else None,
        "unique_edge_count": metrics.unique_edge_count,
        "edge_incidence_histogram": {str(count): edges for count, edges in metrics.edge_incidence_histogram},
        "all_edges_incident_to_two_triangles": metrics.all_edges_incident_to_two_triangles,
        "gameplay_semantics": "UNKNOWN",
        "source_name_only": True,
        "nearest_area_metrics": areas_by_name,
    }


def _pair_record(model, mesh_nodes, area_name, marker_list):
    positions = tuple(marker.position for marker in marker_list.markers)
    if any(position is None for position in positions):
        raise ValueError(f"{area_name} contains missing positions")
    first = analyze_source_mesh(model, mesh_nodes[0]).runtime_centroid
    second = analyze_source_mesh(model, mesh_nodes[1]).runtime_centroid
    if first is None or second is None:
        raise ValueError("pair member has no centroid")
    metrics = pair_to_marker_polygon(first, second, positions)
    edges = []
    for edge in metrics["edge_comparisons"]:
        edges.append({
            "edge_index": edge.edge_index,
            "from_marker_index": edge.start_marker_index,
            "to_marker_index": edge.end_marker_index,
            "angle_difference_acute_degrees": edge.angle_to_pair_degrees,
            "pair_midpoint_distance_to_edge_midpoint_xz": edge.pair_midpoint_distance_xz,
            "pair_midpoint_distance_to_edge_segment_xz": edge.pair_midpoint_segment_distance_xz,
        })
    nearby_parallel = [edge for edge in metrics["edge_comparisons"]
                       if edge.angle_to_pair_degrees is not None and edge.angle_to_pair_degrees <= 3.0]
    best_near_parallel = min(
        nearby_parallel or list(metrics["edge_comparisons"]),
        key=lambda edge: edge.pair_midpoint_segment_distance_xz,
    )
    return {
        "members": [node.name for node in mesh_nodes],
        "area_compared": area_name,
        "pair_separation_3d": metrics["pair_separation_3d"],
        "pair_midpoint_runtime_xml": list(metrics["pair_midpoint"]),
        "pair_direction_xz": list(metrics["pair_direction_xz"]),
        "all_area_edges": edges,
        "smallest_angular_difference_edge": asdict(metrics["smallest_angular_difference_edge"]),
        "nearest_segment_among_edges_within_3_degrees": asdict(best_near_parallel),
        "nearest_edge_segment_to_midpoint": asdict(metrics["nearest_edge_segment_to_midpoint"]),
        "spatial_correlation_status": "STRONG_SPATIAL_CORRELATION" if (
            best_near_parallel.pair_midpoint_segment_distance_xz <= 10.0
            and best_near_parallel.angle_to_pair_degrees <= 3.0
        ) else "MEASURED_NO_STRONG_PAIR_CORRELATION",
        "gameplay_or_physical_semantics": "UNKNOWN",
    }


def build_correlation_report(gxm_path: Path = SOURCE_GXM, txt_path: Path = SOURCE_TXT,
                             xml_path: Path = RETAIL_FRANCE_XML) -> dict[str, Any]:
    model = parse_course_gxm_model_v7(gxm_path, parse_course_txt(txt_path))
    xml = parse_course_xml(xml_path)
    areas = {}
    for name in ("StartArea", "FinishArea"):
        found = tuple(item for item in xml.marker_lists if item.name == name)
        if len(found) != 1:
            raise ValueError(f"expected exactly one {name} MarkerList, found {len(found)}")
        areas[name] = found[0]
    nodes = {name: model.find_mesh(name) for name in NAMED_FINISH_MESHES}
    records = {name: _mesh_record(model, node, areas) for name, node in nodes.items()}
    optional_geometry = {}
    for optional_name in ("_raceline", "$boinds", "_limits"):
        matches = tuple(
            node for node in model.object_table.nodes
            if node.name == optional_name and node.class_name.casefold() == "momesh"
        )
        if len(matches) == 1:
            optional = analyze_source_mesh(model, matches[0])
            optional_geometry[optional_name] = {
                "literal_source_name": optional_name,
                "Index": matches[0].mesh_index,
                "Size": matches[0].mesh_size,
                "triangle_count": optional.triangle_count,
                "unique_position_count": len(optional.unique_position_indices),
                "source_centroid": list(optional.source_centroid) if optional.source_centroid else None,
                "runtime_centroid": list(optional.runtime_centroid) if optional.runtime_centroid else None,
                "source_bounds": _bounds_dict(optional.source_bounds),
                "runtime_bounds": _bounds_dict(optional.runtime_bounds),
                "gameplay_semantics": "UNKNOWN",
            }
        else:
            optional_geometry[optional_name] = {
                "status": "NOT_PRESENT_AS_UNIQUE_moMesh" if not matches else "AMBIGUOUS",
                "gameplay_semantics": "UNKNOWN",
            }
    spans = tuple(
        MeshSpanRef(node.ordinal, node.name, node.mesh_index, node.mesh_size)
        for node in model.object_table.nodes
        if node.class_name.casefold() == "momesh"
        and node.mesh_index is not None and node.mesh_size is not None
    )
    triangle_triplets = tuple(
        model.triangle(index).position_indices for index in range(model.triangles.count)
    )
    position_owners = position_mesh_owners(triangle_triplets, spans)
    exclusivity = {}
    for name, node in nodes.items():
        mesh = records[name]
        shared = []
        exclusive = []
        for position_index in mesh["unique_position_indices"]:
            owners = position_owners[position_index]
            if owners == ((node.ordinal, node.name),):
                exclusive.append(position_index)
            else:
                shared.append({"position_index": position_index, "owners": [
                    {"source_ordinal": ordinal, "literal_name": owner_name}
                    for ordinal, owner_name in owners
                ]})
        exclusivity[name] = {
            "unique_position_indices": list(mesh["unique_position_indices"]),
            "exclusive_position_indices": exclusive,
            "shared_position_references": shared,
            "all_positions_exclusive": len(exclusive) == len(mesh["unique_position_indices"]),
        }

    start_pair = _pair_record(model, [nodes[name] for name in START_PAIR], "StartArea", areas["StartArea"])
    finish_pair = _pair_record(model, [nodes[name] for name in FINISH_PAIR], "FinishArea", areas["FinishArea"])
    return {
        "schema": "r5t-f0-france1-named-geometry-correlation-v1",
        "evidence": ["CONFIRMED_BY_BINARY_STRUCTURE", "CONFIRMED_BY_CORPUS", "CONFIRMED_BY_RUNTIME_EDIT"],
        "source": {
            "build": "Demo 8.4.1 source / original cooker input",
            "gxm": {"path": str(gxm_path), "size_bytes": gxm_path.stat().st_size, "sha256": sha256_path(gxm_path)},
            "txt": {"path": str(txt_path), "size_bytes": txt_path.stat().st_size, "sha256": sha256_path(txt_path)},
            "object_class": model.object_class,
            "version": model.version,
            "coordinate_spaces": {
                "source": "GXM float3 pools in source (x,y,z)",
                "runtime_xml": "(x,z,-y); canonical source-to-runtime transform",
                "blender": "source coordinates map approximately by identity; runtime/XML uses (x,-z,y)",
            },
        },
        "racetest_xml": {
            "path": str(xml_path),
            "size_bytes": xml_path.stat().st_size,
            "sha256": sha256_path(xml_path),
            "status_for_probe": "UNCHANGED",
            "areas": {name: _area_record(item) for name, item in areas.items()},
        },
        "meshes": records,
        "optional_named_mesh_inventory": optional_geometry,
        "ownership": exclusivity,
        "pairs": {"start_pair": start_pair, "finish_pair": finish_pair},
        "interpretation": {
            "literal_mesh_names": "source identity only",
            "spatial_relationship": "quantified geometry; source/runtime semantic linkage not proven",
            "physical_collision_role": "NOT_PROVEN",
            "RaceTest_trigger_role": "NOT_PROVEN",
        },
    }


def _changed_offsets(before: bytes, after: bytes) -> tuple[int, ...]:
    if len(before) != len(after):
        raise ValueError("source probe must preserve file size")
    return tuple(index for index, (a, b) in enumerate(zip(before, after)) if a != b)


def _changed_ranges(offsets: tuple[int, ...]) -> list[dict[str, int]]:
    if not offsets:
        return []
    ranges = []
    start = previous = offsets[0]
    for current in offsets[1:]:
        if current != previous + 1:
            ranges.append({"offset": start, "length": previous - start + 1})
            start = current
        previous = current
    ranges.append({"offset": start, "length": previous - start + 1})
    return ranges


def patch_unique_position_x(
    position_bank_bytes: bytes,
    unique_position_indices: tuple[int, ...],
    delta_x: float,
) -> tuple[bytes, tuple[int, ...]]:
    """Private low-level patch primitive; orchestration pins identity/target/ownership."""
    if not unique_position_indices or len(set(unique_position_indices)) != len(unique_position_indices):
        raise ValueError("target position list must be non-empty and unique")
    if not math.isfinite(delta_x) or delta_x != 20.0:
        raise ValueError("R5T-F.0 probe permits only the reviewed +20.0 source-X delta")
    patched = bytearray(position_bank_bytes)
    allowed = set()
    for position_index in unique_position_indices:
        offset = position_index * 12
        if position_index < 0 or offset + 12 > len(patched):
            raise ValueError(f"position index {position_index} is outside the supplied bank")
        current_x = struct.unpack_from("<f", patched, offset)[0]
        if not math.isfinite(current_x):
            raise ValueError(f"position index {position_index} has non-finite X")
        struct.pack_into("<f", patched, offset, current_x + delta_x)
        allowed.update(range(offset, offset + 4))
    changed = _changed_offsets(position_bank_bytes, bytes(patched))
    if any(offset not in allowed for offset in changed):
        raise AssertionError("position probe changed bytes outside target X components")
    return bytes(patched), changed


def prepare_probe(report: dict[str, Any], *, output_gxm: Path = MODIFIED_GXM,
                  manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    input_path = Path(report["source"]["gxm"]["path"])
    txt_path = Path(report["source"]["txt"]["path"])
    xml_path = Path(report["racetest_xml"]["path"])
    baseline = input_path.read_bytes()
    if sha256_bytes(baseline) != EXPECTED_FRANCE1_GXM_SHA256:
        raise ValueError("R5T-F.0 mutation requires the hash-pinned Demo 8.4.1 France1 GXM")
    model = parse_course_gxm_model_v7(input_path, parse_course_txt(txt_path))
    if model.object_class != 2 or model.version != 7:
        raise ValueError("probe requires class-2 version-7 moModel")
    node = model.find_mesh(PROBE_TARGET)
    expected_span = NAMED_FINISH_MESHES[PROBE_TARGET]
    if (node.mesh_index, node.mesh_size) != expected_span:
        raise ValueError(f"unexpected target span {(node.mesh_index, node.mesh_size)}")
    ownership = report["ownership"][PROBE_TARGET]
    if not ownership["all_positions_exclusive"] or ownership["shared_position_references"]:
        raise ValueError("target source positions are shared; refusing mutation")

    patched_bank, relative_changes = patch_unique_position_x(
        model.positions.raw,
        tuple(ownership["unique_position_indices"]),
        PROBE_DELTA_SOURCE[0],
    )
    modified_array = bytearray(baseline)
    start = model.positions.offset
    modified_array[start:start + len(patched_bank)] = patched_bank
    modified = bytes(modified_array)
    changed = _changed_offsets(baseline, modified)
    expected_allowed = {
        model.positions.offset + index * 12 + byte
        for index in ownership["unique_position_indices"]
        for byte in range(4)
    }
    if any(offset not in expected_allowed for offset in changed):
        raise AssertionError("whole-file change exceeds the exclusive target X fields")

    modified_model = parse_course_gxm_model_v7_bytes(
        modified, parse_course_txt(txt_path), input_path.name + ".modified",
    )
    target_triplets = tuple(model.triangle(index).position_indices for index in model.mesh_triangle_indices(node))
    modified_node = modified_model.find_mesh(PROBE_TARGET)
    modified_triplets = tuple(
        modified_model.triangle(index).position_indices
        for index in modified_model.mesh_triangle_indices(modified_node)
    )
    if target_triplets != modified_triplets:
        raise AssertionError("probe changed target topology/indexing")
    if model.triangles.raw != modified_model.triangles.raw:
        raise AssertionError("probe changed triangle records")
    baseline_table = baseline[model.object_table.table_offset:model.object_table.table_offset + model.object_table.table_size]
    modified_table = modified[modified_model.object_table.table_offset:modified_model.object_table.table_offset + modified_model.object_table.table_size]
    if baseline_table != modified_table:
        raise AssertionError("probe changed source hierarchy bytes")
    for name in ("colors", "materials", "normals", "texcoords"):
        if getattr(model, name).raw != getattr(modified_model, name).raw:
            raise AssertionError(f"probe changed {name} bank")
    target_indices = ownership["unique_position_indices"]
    target_positions = []
    for index in target_indices:
        before = model.position(index)
        after = modified_model.position(index)
        if not math.isclose(after[0] - before[0], 20.0, abs_tol=1e-5) or after[1:] != before[1:]:
            raise AssertionError(f"target position {index} did not receive only source X += 20")
        target_positions.append({"position_index": index, "before": list(before), "after": list(after)})
    target_set = set(target_indices)
    for index in range(model.positions.count):
        if index not in target_set and model.position(index) != modified_model.position(index):
            raise AssertionError(f"non-target position {index} changed")

    offsets = tuple(start + offset for offset in relative_changes)
    if len(offsets) != len(changed):
        raise AssertionError("reported position-bank changes do not match whole-file diff")
    output_gxm = output_gxm.resolve()
    output_root = PROBE_ROOT.resolve()
    if output_root not in output_gxm.parents:
        raise ValueError("modified source output must stay under D: research-output/r5t_f0")
    if output_gxm.exists():
        raise FileExistsError(f"refusing to overwrite probe source: {output_gxm}")
    output_gxm.parent.mkdir(parents=True, exist_ok=True)
    output_gxm.write_bytes(modified)

    source_stats = analyze_source_mesh(model, node)
    old_runtime_bounds = source_stats.runtime_bounds
    new_runtime_centroid = tuple(source_stats.runtime_centroid[axis] + PROBE_DELTA_SOURCE[axis] for axis in range(3))
    new_runtime_bounds = (
        tuple(old_runtime_bounds[0][axis] + PROBE_DELTA_SOURCE[axis] for axis in range(3)),
        tuple(old_runtime_bounds[1][axis] + PROBE_DELTA_SOURCE[axis] for axis in range(3)),
    )
    manifest = {
        "schema": "r5t-f0-probe-manifest-v1",
        "status": "SOURCE_COPY_PREPARED_NOT_COOKED_NOT_RUNTIME_TESTED",
        "baseline": {
            "path": str(input_path),
            "sha256": sha256_bytes(baseline),
            "size_bytes": len(baseline),
            "txt_sha256": sha256_path(txt_path),
        },
        "modified": {
            "path": str(output_gxm),
            "sha256": sha256_bytes(modified),
            "size_bytes": len(modified),
        },
        "race_test_xml": {
            "path": str(xml_path),
            "sha256": sha256_path(xml_path),
            "status": "UNCHANGED; no XML bytes are written by this tool",
            "FinishArea": "UNCHANGED",
        },
        "target": {
            "literal_name": PROBE_TARGET,
            "hierarchy_path": list(_node_path(model, node)),
            "source_ordinal": node.ordinal,
            "Index": node.mesh_index,
            "Size": node.mesh_size,
            "triangle_span_half_open": [node.mesh_index, node.mesh_index + node.mesh_size],
            "triangle_count": source_stats.triangle_count,
            "unique_position_indices": list(target_indices),
            "position_ownership": ownership,
            "all_target_positions_exclusive": True,
        },
        "positions": target_positions,
        "translation": {
            "source_delta": list(PROBE_DELTA_SOURCE),
            "expected_runtime_delta": list(gxm_source_to_runtime(PROBE_DELTA_SOURCE)),
            "old_runtime_centroid": list(source_stats.runtime_centroid),
            "new_runtime_centroid": list(new_runtime_centroid),
            "old_runtime_bounds": _bounds_dict(source_stats.runtime_bounds),
            "new_runtime_bounds": _bounds_dict(new_runtime_bounds),
        },
        "diff": {
            "changed_byte_count": len(changed),
            "changed_byte_offsets": list(offsets),
            "changed_ranges": _changed_ranges(offsets),
            "only_target_source_x_fields_changed": set(changed).issubset(expected_allowed),
            "all_other_position_records_unchanged": True,
            "triangle_bank_identical": True,
            "node_tree_identical": True,
            "attribute_banks_identical": True,
            "target_position_indices_and_topology_unchanged": True,
            "file_size_unchanged": len(baseline) == len(modified),
            "position_bank_changed_byte_count": len(relative_changes),
        },
        "cooking": {"status": "PENDING", "baseline_runs": 0, "modified_runs": 0},
        "evidence": ["CONFIRMED_BY_BINARY_STRUCTURE", "CONTROLLED_SOURCE_COPY_DIFF"],
        "interpretation": {
            "source_name": "literal identity only",
            "gameplay_semantics": "UNKNOWN",
            "physical_role": "NOT_PROVEN",
            "RaceTest_trigger_role": "NOT_PROVEN",
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="rebuild the France1 spatial-correlation report")
    analyze.add_argument("--gxm", type=Path, default=SOURCE_GXM)
    analyze.add_argument("--txt", type=Path, default=SOURCE_TXT)
    analyze.add_argument("--xml", type=Path, default=RETAIL_FRANCE_XML)
    analyze.add_argument("--output", type=Path, default=REPORT_PATH)
    prepare = subparsers.add_parser("prepare-probe", help="prepare the single hash-pinned +20 X source copy")
    prepare.add_argument("--report", type=Path, default=REPORT_PATH)
    prepare.add_argument("--output-gxm", type=Path, default=MODIFIED_GXM)
    prepare.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()

    if args.command == "analyze":
        report = build_correlation_report(args.gxm.resolve(), args.txt.resolve(), args.xml.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(args.output.resolve()), "meshes": len(report["meshes"]), "pairs": {
            name: {"separation": pair["pair_separation_3d"], "status": pair["spatial_correlation_status"]}
            for name, pair in report["pairs"].items()
        }}, indent=2))
    else:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        manifest = prepare_probe(report, output_gxm=args.output_gxm, manifest_path=args.manifest)
        print(json.dumps({
            "target": manifest["target"]["literal_name"],
            "exclusive_positions": len(manifest["target"]["unique_position_indices"]),
            "baseline_sha256": manifest["baseline"]["sha256"],
            "modified_sha256": manifest["modified"]["sha256"],
            "changed_bytes": manifest["diff"]["changed_byte_count"],
            "modified_gxm": manifest["modified"]["path"],
            "manifest": str(args.manifest.resolve()),
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
