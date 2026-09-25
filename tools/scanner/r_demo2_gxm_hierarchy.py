"""Reconstruct the supported demo 9.3.1 typed GXM hierarchy tail as JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.gxm import (  # noqa: E402
    parse_gxm_geometry_prefix_bytes,
    parse_gxm_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)
from master_rallye.sidecar import parse_sidecar  # noqa: E402
from master_rallye.gxm_hierarchy import (GxmNode, parse_gxm_hierarchy_tail, walk_depth_first,
                                             runtime_node_bindings, serialized_c_triangle_stream)  # noqa: E402


def node_json(node: GxmNode, record_count: int) -> dict:
    end = node.mesh_start + node.mesh_count
    return {
        "name": node.name,
        "type": node.node_type,
        "version": node.version,
        "child_count": node.child_count,
        "mesh_start": node.mesh_start,
        "mesh_count": node.mesh_count,
        "mesh_end_exclusive": end,
        "range_in_bounds": end <= record_count,
        "record_offset": node.record_offset,
        "name_offset": node.name_offset,
        "children": [node_json(child, record_count) for child in node.children],
    }


def build_report(path: Path, sidecar_path: Path) -> dict:
    data = path.read_bytes()
    prefix = parse_gxm_prefix_bytes(data, str(path))
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
    hierarchy = parse_gxm_hierarchy_tail(data, triangles.hierarchy_offset)
    sidecar = parse_sidecar(sidecar_path)
    nodes = tuple(walk_depth_first(hierarchy.roots))
    bindings = runtime_node_bindings(hierarchy.roots)
    hulls = [node for node in nodes if node.name.startswith("$chull")]
    sidecar_spans = [(mesh.name, mesh.index, mesh.size) for mesh in sidecar.meshes]
    serialized_spans = [(node.name, node.mesh_start, node.mesh_count) for node in nodes]
    hull_stream = (serialized_c_triangle_stream(data, triangles.record_offset, triangles.record_count,
                                                  hulls[0].mesh_start, hulls[0].mesh_count)
                   if len(hulls) == 1 and hulls[0].mesh_start + hulls[0].mesh_count <= triangles.record_count
                   else ())
    return {
        "schema": "r-demo2-gxm-hierarchy-v2",
        "evidence": "CONFIRMED_BY_BYTES",
        "runtime_mapping_evidence": "CONFIRMED_BY_EXE for node layout/links and type-2/version-7 root child count; bounded tail consumption checked separately",
        "source_path": str(path),
        "source_size": len(data),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "sidecar_path": str(sidecar_path),
        "sidecar_sha256": hashlib.sha256(sidecar_path.read_bytes()).hexdigest(),
        "sidecar_mesh_count": len(sidecar.meshes),
        "serialized_name_span_order_matches_sidecar": serialized_spans == sidecar_spans,
        "prefix_kind": prefix.prefix_kind,
        "triangle_record_count": triangles.record_count,
        "hierarchy_tail_offset": hierarchy.tail_offset,
        "hierarchy_tail_size": hierarchy.tail_size,
        "hierarchy_consumed_size": hierarchy.consumed_size,
        "root_name": hierarchy.root_name,
        "top_level_node_count": len(hierarchy.roots),
        "header_root_child_count": prefix.header_words[0] >> 16,
        "header_root_count_matches": len(hierarchy.roots) == prefix.header_words[0] >> 16,
        "node_count": hierarchy.node_count,
        "all_ranges_in_bounds": all(node.mesh_start + node.mesh_count <= triangles.record_count for node in nodes),
        "depth_first_serialized_ranges": [
            {"name": node.name, "start": node.mesh_start, "count": node.mesh_count,
             "end_exclusive": node.mesh_start + node.mesh_count}
            for node in nodes
        ],
        "runtime_link_mapping": [
            {"name": entry.node.name, "record_offset": entry.node.record_offset,
             "parent_name": entry.parent_name, "previous_sibling_name": entry.previous_sibling_name,
             "next_sibling_name": entry.next_sibling_name, "child_offset": entry.child_pointer_offset,
             "sibling_offset": entry.sibling_pointer_offset, "parent_offset": entry.parent_pointer_offset,
             "name_offset": entry.name_pointer_offset, "mesh_start_offset": entry.mesh_start_offset,
             "mesh_count_offset": entry.mesh_count_offset}
            for entry in bindings
        ],
        "nodes": [node_json(node, triangles.record_count) for node in hierarchy.roots],
        "chull_matches": [node_json(node, triangles.record_count) for node in hulls],
        "serialized_hull_record_ids": (
            list(range(hulls[0].mesh_start, hulls[0].mesh_start + hulls[0].mesh_count))
            if len(hulls) == 1 and hulls[0].mesh_start + hulls[0].mesh_count <= triangles.record_count else None
        ),
        "serialized_hull_triangle_count": len(hull_stream),
        "serialized_hull_unique_c_indices": sorted({index for triangle in hull_stream for index in triangle.c_indices}),
        "serialized_hull_triangle_stream": [
            {"record_index": triangle.record_index, "c_indices": list(triangle.c_indices)}
            for triangle in hull_stream
        ],
        "runtime_triangle_stream": "SERIALIZED_ONLY: this hierarchy report does not run welding. Use r_demo_vertex_weld_oracle.py; pinned Trooper pair has Path B in vertex-welder.json. FUN_005c9990/FUN_005ca370 run after hull",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gxm", required=True, type=Path, help="read-only 9.3.1 GXM file")
    parser.add_argument("--sidecar", required=True, type=Path, help="matching read-only TXT sidecar")
    parser.add_argument("--output", required=True, type=Path, help="JSON destination")
    args = parser.parse_args()
    report = build_report(args.gxm, args.sidecar)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "source_sha256", "sidecar_sha256", "sidecar_mesh_count",
        "serialized_name_span_order_matches_sidecar", "triangle_record_count",
        "hierarchy_tail_offset", "hierarchy_tail_size",
        "top_level_node_count", "node_count", "all_ranges_in_bounds", "chull_matches",
        "serialized_hull_triangle_count", "serialized_hull_unique_c_indices",
        "runtime_triangle_stream")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
