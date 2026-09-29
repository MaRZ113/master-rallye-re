#!/usr/bin/env python3
"""Read-only R5T-B.1 GXM point-pool and old-DX correlation report."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from master_rallye.course_gxm import parse_course_gxm_bytes, parse_course_gxm_float3_pool_bytes, parse_course_gxm_object_table_bytes
from master_rallye.course_source import parse_course_txt
from master_rallye.course_xml import parse_course_xml
from master_rallye.dx import parse_dx_common_prefix


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: Path) -> str:
    """Keep committed reports portable across checkout locations."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return Path(os.path.relpath(resolved, ROOT.resolve())).as_posix()


def bounds(points: tuple[tuple[float, float, float], ...]) -> list[list[float]]:
    if not points:
        return []
    return [[min(point[axis] for point in points), max(point[axis] for point in points)] for axis in range(3)]


def transform_name(permutation: tuple[int, int, int], signs: tuple[int, int, int]) -> str:
    names = ("x", "y", "z")
    return "(" + ", ".join(("-" if sign < 0 else "") + names[permutation[index]] for index, sign in enumerate(signs)) + ")"


def coordinate_scores(source: tuple[tuple[float, float, float], ...], target: list[tuple[float, float, float]]) -> dict[str, Any]:
    target_exact = set(target)
    target_int = {tuple(round(value) for value in point) for point in target}
    target_tenth = {tuple(round(value * 10) for value in point) for point in target}
    candidates = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            mapped = [tuple(signs[a] * point[permutation[a]] for a in range(3)) for point in source]
            candidates.append({
                "transform": transform_name(permutation, signs),
                "exact": sum(point in target_exact for point in mapped),
                "rounded_1": sum(tuple(round(value) for value in point) in target_int for point in mapped),
                "rounded_0_1": sum(tuple(round(value * 10) for value in point) in target_tenth for point in mapped),
            })
    candidates.sort(key=lambda item: (item["rounded_0_1"], item["rounded_1"], item["exact"]), reverse=True)
    return {
        "candidate_transform_count": len(candidates),
        "best": candidates[0],
        "runner_up": candidates[1],
        "source_point_count": len(source),
        "dx_vertex_count": len(target),
        "match_fraction_rounded_0_1": round(candidates[0]["rounded_0_1"] / max(1, len(source)), 6),
        "evidence": "HIGH_CONFIDENCE_INFERENCE" if candidates[0]["rounded_0_1"] > 20 * candidates[1]["rounded_0_1"] else "PLAUSIBLE",
    }


def point_cluster(points: tuple[tuple[float, float, float], ...]) -> dict[str, Any]:
    box = bounds(points)
    corners = {(x, y, z) for x in (box[0][0], box[0][1]) for y in (box[1][0], box[1][1]) for z in (box[2][0], box[2][1])} if points else set()
    unique = set(points)
    return {
        "count": len(points),
        "unique_count": len(unique),
        "bounds_xyz": box,
        "eight_corners_of_axis_aligned_box": len(points) == 8 and unique == corners,
    }


def helper_nodes(nodes, pool) -> list[dict[str, Any]]:
    records = {
        node.ordinal: {
            "ordinal": node.ordinal,
            "name": node.name,
            "class": node.class_name,
            "parent_id": node.parent_id,
            "mesh_index": node.mesh_index,
            "mesh_size": node.mesh_size,
            "child_count": node.child_count,
            "record_offset": node.record_offset,
            "record_size": node.record_size,
        }
        for node in nodes
    }
    selected = []
    for node in nodes:
        name = node.name.casefold()
        if not any(token in name for token in ("start", "finish", "split", "bsp", "raceline", "boinds", "limits", "landdb", "grnd")):
            continue
        item = dict(records[node.ordinal])
        item["evidence"] = "CONFIRMED_BY_BINARY for node name/hierarchy/span; behavior unknown"
        if name == "startpoint" and node.mesh_index == 0 and node.mesh_size == 12:
            item["first_eight_points"] = point_cluster(pool.points[:8])
            item["first_eight_points"]["candidate_pool_index_range_inclusive"] = [0, 7]
            item["first_eight_points"]["node_link"] = "HIGH_CONFIDENCE_INFERENCE; triangle connectivity not decoded"
        if name == "$bsp":
            descendants = []
            for other in nodes:
                parent = other.parent_id
                while parent is not None:
                    if parent == node.ordinal:
                        descendants.append(other)
                        break
                    parent = records[parent]["parent_id"] if parent in records else None
            meshes = [child for child in descendants if child.class_name.casefold() == "momesh"]
            item["subtree_node_count"] = len(descendants)
            item["subtree_mesh_count"] = len(meshes)
            item["subtree_mesh_size_sum"] = sum(child.mesh_size or 0 for child in meshes)
            item["point_pool_mapping"] = "UNKNOWN"
        selected.append(item)
    return selected


def analyze_pair(label: str, gxm: Path, txt: Path, dx: Path, race_xml: Path | None = None) -> dict[str, Any]:
    raw = gxm.read_bytes()
    prefix = parse_course_gxm_bytes(raw, gxm.name)
    document = parse_course_txt(txt)
    table = parse_course_gxm_object_table_bytes(raw, document, gxm.name)
    pool = parse_course_gxm_float3_pool_bytes(raw, table, gxm.name)
    compiled = parse_dx_common_prefix(dx.read_bytes(), dx.name)
    scores = coordinate_scores(pool.points, [tuple(point) for point in compiled.vertices.positions])
    meshes = [node for node in table.nodes if node.mesh_size is not None]
    marker_correlation = None
    startpoint_node = next((node for node in table.nodes if node.name.casefold() == "startpoint"), None)
    if race_xml and race_xml.is_file() and startpoint_node and startpoint_node.mesh_index == 0 and startpoint_node.mesh_size == 12:
        first_eight = pool.points[:8]
        if len(set(first_eight)) == 8:
            source_bounds = bounds(first_eight)
            source_center = tuple((axis[0] + axis[1]) / 2 for axis in source_bounds)
            dx_center = (source_center[0], source_center[2], -source_center[1])
            xml = parse_course_xml(race_xml)
            positioned = [marker for marker in xml.markers if marker.position is not None]
            nearest = min(positioned, key=lambda marker: math.dist(dx_center, marker.position)) if positioned else None
            marker_correlation = {
                "race_test_xml": display_path(race_xml),
                "source_cluster_center_xyz": list(source_center),
                "mapped_dx_center_xyz": list(dx_center),
                "nearest_marker": None if nearest is None else {
                    "ordinal": nearest.ordinal,
                    "marker_no": nearest.marker_no,
                    "marker_type": nearest.marker_type,
                    "position_xyz": list(nearest.position),
                    "distance": math.dist(dx_center, nearest.position),
                },
                "evidence": "HIGH_CONFIDENCE_INFERENCE; spatial proximity only, no XML helper binding is asserted",
            }
    return {
        "label": label,
        "source": {
            "gxm": {"path": display_path(gxm), "bytes": len(raw), "sha256": sha256(raw)},
            "txt": {"path": display_path(txt), "bytes": txt.stat().st_size, "sha256": sha256(txt.read_bytes())},
            "header_words_u32": list(prefix.header_words),
            "node_table": {"offset": table.table_offset, "bytes": table.table_size, "node_count": len(table.nodes)},
            "float3_pool": {
                "status": "bounded and finite; per-node association UNKNOWN",
                "offset": pool.offset,
                "count": pool.count,
                "bytes": pool.byte_size,
                "sha256": sha256(pool.raw),
                "bounds_xyz": bounds(pool.points),
                "finite_point_count": len(pool.points),
            },
            "header_crosschecks": {
                "word4_equals_3_times_word6": prefix.header_words[4] == 3 * prefix.header_words[6],
                "word6_equals_sum_mesh_size": prefix.header_words[6] == sum(node.mesh_size or 0 for node in meshes),
            },
            "helper_nodes": helper_nodes(table.nodes, pool),
        },
        "compiled_dx": {
            "path": display_path(dx),
            "bytes": dx.stat().st_size,
            "sha256": sha256(dx.read_bytes()),
            "revision": compiled.word_0x04,
            "vertex_count": len(compiled.vertices.positions),
        },
        "source_to_dx": scores,
        "source_to_blender": {
            "transform": "identity (x, y, z)",
            "evidence": "HIGH_CONFIDENCE_INFERENCE: best source-to-DX transform (x, z, -y) composes with proven DX-to-Blender (x, -z, y)",
        },
        "startpoint_xml_spatial_correlation": marker_correlation,
    }


def developer_oracles(corpora: Path) -> dict[str, Any]:
    base = corpora / "demo-8.4.1" / "DataGx" / "Test"
    stems = {
        "gordonTrack/flatTrack": base / "gordonTrack" / "flatTrack",
        "gordonTrack/track": base / "gordonTrack" / "track",
        "RussiaTurkey1/RussiaTurkey1": base / "RussiaTurkey1" / "RussiaTurkey1",
        "boinds/track01": base / "boinds" / "track01",
        "collisiontests/crack": base / "collisiontests" / "crack",
        "collisiontests/crack2": base / "collisiontests" / "crack2",
    }
    result = {}
    for label, stem in stems.items():
        gxi = sorted(stem.parent.glob("*.gxi"))
        result[label] = {
            suffix: {"exists": stem.with_suffix(suffix).is_file(), "bytes": stem.with_suffix(suffix).stat().st_size if stem.with_suffix(suffix).is_file() else None}
            for suffix in (".gxm", ".txt", ".dx")
        }
        result[label]["gxi"] = {"count_in_folder": len(gxi)}
    return result


def build_report(inputs: Path, corpora: Path) -> dict[str, Any]:
    pairs = [
        ("Demo 8.4.1 France1", inputs / "8.4.1_France1" / "France1.gxm", inputs / "8.4.1_France1" / "France1.txt", corpora / "demo-8.4.1" / "DataGx" / "Course" / "France1" / "france1.dx", corpora / "demo-9.10.0" / "DataScene" / "RaceTest" / "France1.xml"),
        ("Demo 8.4.1 Italy1", inputs / "8.4.1_Italy1" / "track01.gxm", inputs / "8.4.1_Italy1" / "track01.txt", corpora / "demo-8.4.1" / "DataGx" / "Course" / "Italy1" / "track01.dx", corpora / "demo-9.10.0" / "DataScene" / "RaceTest" / "Italy1.xml"),
        ("Demo 8.4.1 developer Boinds", corpora / "demo-8.4.1" / "DataGx" / "Test" / "boinds" / "track01.gxm", corpora / "demo-8.4.1" / "DataGx" / "Test" / "boinds" / "track01.txt", corpora / "demo-8.4.1" / "DataGx" / "Test" / "boinds" / "track01.dx", None),
    ]
    missing = [display_path(path) for _, *paths in pairs for path in paths if path is not None and not path.is_file()]
    analyzed = [analyze_pair(label, gxm, txt, dx, race_xml) for label, gxm, txt, dx, race_xml in pairs if all(path.is_file() for path in (gxm, txt, dx))]
    return {
        "schema": "r5t-b1-gxm-geometry-probe-v1",
        "evidence_labels": ["CONFIRMED_BY_BINARY", "CONFIRMED_BY_SOURCE_COMPILED_PAIR", "HIGH_CONFIDENCE_INFERENCE", "UNKNOWN"],
        "source_compiled_pairs": analyzed,
        "missing_required_pair_files": missing,
        "small_developer_oracles": developer_oracles(corpora),
        "conclusions": {
            "float3_pool": "Header word 7 bounds a finite trailing float3 bank immediately before the TXT-validated node table. The full pool correlates with old compiled DX vertices in the three measured source/cooked pairs.",
            "node_mesh_link": "UNKNOWN. TXT/GXM mesh Index/Size spans validate, but their mapping to the float3 pool and raw index streams is not proven.",
            "startpoint": "HIGH_CONFIDENCE_INFERENCE: France1 has a startpoint node at Index 0 / Size 12 and the first eight pool points are eight corners of a 10-unit axis-aligned box. Face connectivity and exact pool-to-node indices are still unknown.",
            "startpoint_xml": "The mapped center of that France1 point cluster is within the reported distance of Demo 9.10 France1 XML Marker 0; this is spatial correlation, not a direct XML-to-GXM binding.",
            "source_to_dx": "HIGH_CONFIDENCE_INFERENCE: (x, z, -y) is the strongest match among all 48 signed axis permutations in France1, Italy1, and Boinds.",
            "source_to_blender": "HIGH_CONFIDENCE_INFERENCE: identity, composed from source-to-DX (x, z, -y) and the established DX-to-Blender (x, -z, y).",
            "bsp": "UNKNOWN. France1's $bsp hierarchy and mesh spans are inventoried, but the source point pool has not been mapped to individual BSP meshes.",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R5T-B.1 GXM geometry probe",
        "",
        "Status: **partial**. The float3 pool is bounded and spatially correlated. Node-to-point topology is not decoded.",
        "",
        "## Source to compiled comparisons",
        "",
        "| Pair | Nodes | Points | DX rev | Exact | 1-unit | 0.1-unit | Best transform | Runner-up 0.1-unit |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for item in report["source_compiled_pairs"]:
        source = item["source"]
        score = item["source_to_dx"]
        lines.append(
            f"| {item['label']} | {source['node_table']['node_count']} | {source['float3_pool']['count']} | "
            f"{item['compiled_dx']['revision']} | {score['best']['exact']} | {score['best']['rounded_1']} | "
            f"{score['best']['rounded_0_1']} | {score['best']['transform']} | {score['runner_up']['rounded_0_1']} |"
        )
    lines.extend(["", "Counts are source points matching the compiled DX position set. All 48 signed axis permutations were evaluated. This validates a coordinate relation, not per-node geometry.", "", "## Current conclusions", ""])
    for name, result in report["conclusions"].items():
        lines.append(f"- **{name}:** {result}")
    france = next((item for item in report["source_compiled_pairs"] if "France1" in item["label"]), None)
    if france and france["startpoint_xml_spatial_correlation"]:
        marker = france["startpoint_xml_spatial_correlation"]["nearest_marker"]
        lines.extend(["", "## France1 startpoint and XML marker", "", f"The candidate startpoint box center maps to DX `{france['startpoint_xml_spatial_correlation']['mapped_dx_center_xyz']}`. Nearest Demo 9.10 XML marker: ordinal `{marker['ordinal']}`, no `{marker['marker_no']}`, distance `{marker['distance']:.3f}` source units. Spatial proximity only; no record binding is claimed."])
    lines.extend(["", "## Small developer oracle files", "", "| Oracle | GXM | TXT | DX | GXI files in folder |", "|---|---|---|---|---:|"])
    for name, files in report["small_developer_oracles"].items():
        lines.append(f"| {name} | {files['.gxm']['exists']} | {files['.txt']['exists']} | {files['.dx']['exists']} | {files['gxi']['count_in_folder']} |")
    lines.extend(["", "Only Boinds currently has the complete small source/TXT/cooked-DX pair. Missing companions are not synthesized.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-root", type=Path, default=ROOT / "inputs")
    parser.add_argument("--corpora-root", type=Path, default=ROOT.parent / "corpora")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "research" / "r5t_b1")
    args = parser.parse_args()
    report = build_report(args.inputs_root.resolve(), args.corpora_root.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "gxm-geometry.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output_dir / "gxm-geometry.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"output_dir": str(args.output_dir.resolve()), "pairs": len(report["source_compiled_pairs"]), "missing_pair_files": len(report["missing_required_pair_files"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
