#!/usr/bin/env python3
"""Generate one ignored Astero +3-vertex/+1-triangle F1 game probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, rebuild_topology, source_geometry

SOURCE_SHA256 = "b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90"
DRAW_ID = 7
DRAW_TRIANGLE = 27
OFFSET = 0.05


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(source_path: Path, output: Path) -> dict:
    source_path = source_path.resolve()
    output = output.resolve()
    if source_path.parent.name.casefold() != "astero" or source_path.name.casefold() != "car.dx":
        raise ValueError("F1 requires original Astero/car.dx")
    data = source_path.read_bytes()
    if _sha(data) != SOURCE_SHA256:
        raise ValueError("Astero DX does not match protected original R4E/R4E.1 provenance")
    if output.exists():
        raise ValueError("F1 output already exists")
    model = parse_dx_bytes(data)
    draw = model.physical_draws[DRAW_ID]
    if draw.texture_tuple != ("acamo64b-tga", "whitepaint-tga", "Null") or draw.tag != 2:
        raise ValueError("Astero body draw identity changed")
    original = source_geometry(model)[DRAW_ID]
    corner_ids = original.triangles[DRAW_TRIANGLE]
    global_ids = tuple(draw.vertex_base + index for index in corner_ids)
    if global_ids != (1227, 1228, 1229):
        raise ValueError("selected hood-side triangle identity changed")
    a, b, c = (original.vertices[index].position for index in corner_ids)
    u = tuple(b[k] - a[k] for k in range(3))
    v = tuple(c[k] - a[k] for k in range(3))
    cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    magnitude = math.sqrt(sum(x*x for x in cross))
    if magnitude < 1e-6:
        raise ValueError("selected triangle is degenerate")
    outward = tuple(x/magnitude for x in cross)
    if outward[1] < 0.9:
        raise ValueError("selected triangle is no longer upward-facing")
    footer = model.collision.unparsed_data
    minimum = struct.unpack_from("<3f", footer, 20)
    maximum = struct.unpack_from("<3f", footer, 32)
    render_minimum = tuple(min(point[axis] for point in model.vertices.positions) for axis in range(3))
    render_maximum = tuple(max(point[axis] for point in model.vertices.positions) for axis in range(3))
    generated = []
    margins = []
    for index in corner_ids:
        parent = original.vertices[index]
        position = tuple(parent.position[axis] + OFFSET*outward[axis] for axis in range(3))
        if any(not minimum[axis] < position[axis] < maximum[axis] for axis in range(3)):
            raise ValueError("raised vertex exceeds original combined bounds")
        if any(not render_minimum[axis] < position[axis] < render_maximum[axis] for axis in range(3)):
            raise ValueError("raised vertex exceeds original render-only bounds")
        margins.append([min(position[axis]-minimum[axis], maximum[axis]-position[axis]) for axis in range(3)])
        generated.append(CompiledVertex(position, parent.normal, parent.color, parent.uvs,
                                        source_vertex_id=None, parent_source_vertex_id=parent.source_vertex_id))
    start = len(original.vertices)
    altered = DrawGeometry(original.vertices + tuple(generated), original.triangles + ((start, start+1, start+2),))
    result = rebuild_topology(data, {DRAW_ID: altered})
    rebuilt = result.output_model
    if (result.output_vertex_count, result.output_triangle_count) != (model.vertex_count+3, model.triangle_count+1):
        raise ValueError("F1 did not add exactly 3 vertices and 1 triangle")
    if result.changed_draws != (DRAW_ID,) or result.external_diff_count:
        raise ValueError("F1 changed unrelated draw or external region")
    new_draw = rebuilt.physical_draws[DRAW_ID]
    new_triangle = rebuilt.draw_global_indices(new_draw)[-3:]
    expected_new_triangle = tuple(new_draw.vertex_base + i for i in (start,start+1,start+2))
    if new_triangle != expected_new_triangle:
        raise ValueError("new local/global triangle mismatch")
    for new_id, parent_id in zip(new_triangle, global_ids):
        if rebuilt.vertices.normals[new_id] != model.vertices.normals[parent_id]:
            raise ValueError("new normal differs from source corner")
        if rebuilt.vertices.colors[new_id*4:new_id*4+4] != model.vertices.colors[parent_id*4:parent_id*4+4]:
            raise ValueError("new color differs from source corner")
        for index in range(len(model.uv_sets)):
            if rebuilt.uv_sets[index].values[new_id] != model.uv_sets[index].values[parent_id]:
                raise ValueError("new UV differs from source corner")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result.data)
    validation = {
        **result.to_dict(),
        "phase": "R4F F1 topology runtime candidate",
        "runtime_status": "WAITING_FOR_HUMAN",
        "source_resource": "Astero/car.dx",
        "source_draw_id": DRAW_ID,
        "source_draw_slots": list(draw.texture_tuple),
        "source_triangle_within_draw": DRAW_TRIANGLE,
        "source_triangle_global_vertices": list(global_ids),
        "new_vertices": 3,
        "new_triangles": 1,
        "offset_source_units": OFFSET,
        "geometric_outward_normal": list(outward),
        "minimum_new_vertex_bound_margins": [min(row[axis] for row in margins) for axis in range(3)],
        "original_render_bounds": {"minimum": list(render_minimum), "maximum": list(render_maximum)},
        "new_vertices_strictly_inside_original_render_bounds": True,
        "changed_render_core_source_range": [12, model.trailing.offset],
        "changed_render_core_output_range": [12, rebuilt.trailing.offset],
        "collision_byte_identical": result.data[rebuilt.collision.offset:rebuilt.collision.end_offset] == data[model.collision.offset:model.collision.end_offset],
        "suffix_byte_identical": result.data[rebuilt.trailing.offset:] == data[model.trailing.offset:],
        "unexpected_external_diffs": 0,
        "candidate_path": str(output),
        "candidate_sha256": _sha(output.read_bytes()),
    }
    (output.parent/"validation.json").write_text(json.dumps(validation,indent=2)+"\n",encoding="utf-8")
    (output.parent/"TEST_INSTRUCTIONS.txt").write_text(
        "R4F F1 — ASTERO RACE car.dx ONLY\n"
        "Package this candidate alone through the full-tree Python Data.sma workflow. Compare against original Astero.\n"
        "Look at the right-side hood region (source body draw 7); one raised duplicate triangle should be visible.\n"
        "Record: game loads? Astero loads? extra triangle visible? new texture and shading correct? body otherwise normal? collision normal? ordinary damage still works? breakable glass still works? wheels normal? any artifacts?\n"
        "Avoid extreme-speed crashes. This is a visual-only topology edit; collision bytes are unchanged.\n"
        "RUNTIME STATUS: WAITING FOR HUMAN. Do not treat reparse/corpus validation as game proof.\n",
        encoding="utf-8",
    )
    if _sha(source_path.read_bytes()) != SOURCE_SHA256:
        raise ValueError("original source changed during F1 generation")
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.source, args.output)
    print(json.dumps({key: result[key] for key in (
        "source_resource", "source_draw_id", "source_triangle_within_draw", "new_vertices", "new_triangles",
        "offset_source_units", "source_vertex_count", "output_vertex_count", "source_triangle_count",
        "output_triangle_count", "unexpected_external_diffs", "candidate_sha256", "candidate_path",
    )}, indent=2))


if __name__ == "__main__":
    main()
