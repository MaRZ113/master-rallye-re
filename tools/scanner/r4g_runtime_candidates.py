#!/usr/bin/env python3
"""Generate ignored isolated R4G Astero B1/C1/P1/W1 runtime probes."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.collision_scale import scale_dx_collision
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, rebuild_topology, source_geometry

EXPECTED = {
    "car.dx": "b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90",
    "complete.dx": "853a1e7e76b00c1b4c0747e19ec6a4c110bda7923a974bc807c7f5907645331f",
    "wheel.dx": "17edbf252c31bf671e19786c25694cc1cfad8599a39d881189e75971eb79aef6",
}
DEFAULT_SOURCE = Path("D:/Game/Master Rallye/backup/Data.sma_unpacked/DataGx/Vehicles/Astero")
DEFAULT_OUTPUT = ROOT / ".research-output/r4g/runtime-tests"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original(source: Path, role: str) -> bytes:
    path = source / role
    data = path.read_bytes()
    if path.parent.name.casefold() != "astero" or sha(data) != EXPECTED[role]:
        raise ValueError(f"{role}: protected original hash mismatch")
    return data


def triangle_candidate(data: bytes, draw_id: int, triangle_id: int, axis: int, delta: float):
    model = parse_dx_bytes(data)
    draw = model.physical_draws[draw_id]
    geometry = source_geometry(model)[draw_id]
    corners = geometry.triangles[triangle_id]
    new = []
    for local_id in corners:
        parent = geometry.vertices[local_id]
        position = tuple(parent.position[i] + (delta if i == axis else 0) for i in range(3))
        new.append(CompiledVertex(position, parent.normal, parent.color, parent.uvs,
                                  parent_source_vertex_id=parent.source_vertex_id))
    start = len(geometry.vertices)
    edited = DrawGeometry(geometry.vertices + tuple(new),
                          geometry.triangles + ((start, start + 1, start + 2),))
    rebuilt = rebuild_topology(data, {draw_id: edited}, bounds_mode="recompute")
    out = rebuilt.output_model
    if rebuilt.changed_draws != (draw_id,) or out.vertex_count != model.vertex_count + 3 or out.triangle_count != model.triangle_count + 1:
        raise ValueError("topology candidate changed unexpected draws or counts")
    if out.collision.convex_hull and model.collision.convex_hull and out.collision.convex_hull.raw != model.collision.convex_hull.raw:
        raise ValueError("topology candidate changed collision")
    if out.collision.cylinder and model.collision.cylinder and out.collision.cylinder.raw != model.collision.cylinder.raw:
        raise ValueError("topology candidate changed tag102")
    return rebuilt, {"draw_id": draw_id, "texture_slots": list(draw.texture_tuple),
                     "source_triangle": triangle_id, "source_global_vertices": [draw.vertex_base + x for x in corners],
                     "axis": axis, "offset": delta, "new_vertices": 3, "new_triangles": 1,
                     "old_bounds": model.collision.spatial_bounds_1339.to_dict(),
                     "new_bounds": out.collision.spatial_bounds_1339.to_dict(),
                     "collision_byte_identical": True, "unexpected_diff_count": rebuilt.external_diff_count}


def save(folder: Path, role: str, data: bytes, validation: dict, instructions: str):
    folder.mkdir(parents=True, exist_ok=True)
    asset = folder / role
    if asset.exists() and sha(asset.read_bytes()) != sha(data):
        raise ValueError(f"refusing to overwrite different candidate: {asset}")
    asset.write_bytes(data)
    (folder / "validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    (folder / "TEST_INSTRUCTIONS.txt").write_text(instructions, encoding="utf-8")
    return str(asset)


def generate(source: Path, output: Path):
    sources = {role: original(source, role) for role in EXPECTED}
    results = {}
    probes = (
        ("B1_out_of_bounds", "car.dx", 7, 5, 1, 0.12,
         "Package only this Astero car.dx. Check game/car load, raised roof/body triangle above old bounds visible, no clipping, normal collision, damage/glass, artifacts. Runtime status: WAITING FOR HUMAN.\n"),
        ("P1_complete_topology", "complete.dx", 2, 27, 1, 0.04,
         "Package only this Astero complete.dx. Inspect presentation/menu car: added hood/body triangle visible, textures/shading correct, model otherwise normal. Runtime status: WAITING FOR HUMAN.\n"),
        ("W1_wheel_topology", "wheel.dx", 2, 37, 0, 0.04,
         "Package only this Astero wheel.dx. Check race loads, protruding wheel triangle visible on all four wheel instances, steering/suspension normal, wheel physics unchanged, artifacts. Runtime status: WAITING FOR HUMAN.\n"),
    )
    for label, role, draw, tri, axis, delta, instructions in probes:
        rebuilt, extra = triangle_candidate(sources[role], draw, tri, axis, delta)
        if label.startswith("B1") and not extra["new_bounds"]["maximum"][1] > extra["old_bounds"]["maximum"][1]:
            raise ValueError("B1 failed to exceed donor Y maximum")
        validation = {"phase": "R4G", "candidate": label, "resource": f"Astero/{role}",
                      "source_sha256": sha(sources[role]), "candidate_sha256": sha(rebuilt.data),
                      "runtime_status": "WAITING_FOR_HUMAN", **rebuilt.to_dict(), **extra}
        results[label] = save(output / label, role, rebuilt.data, validation, instructions)
    scaled = scale_dx_collision(sources["car.dx"], (1.2, 1.0, 1.0))
    validation = {k:v for k,v in scaled.items() if k != "data"}
    validation.update(phase="R4G", candidate="C1_collision_scale", resource="Astero/car.dx",
                      runtime_status="WAITING_FOR_HUMAN", render_byte_identical=True,
                      scale_axis="source X lateral", source_sha256=sha(sources["car.dx"]))
    results["C1_collision_scale"] = save(
        output / "C1_collision_scale", "car.dx", scaled["data"], validation,
        "Package only this Astero car.dx. Body render is stock; tag101 collision is widened 20% on source X. Check game/car load, earlier side-wall contact than visible body, collision present, usable handling, damage, artifacts. Runtime status: WAITING FOR HUMAN.\n")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(generate(args.source.resolve(), args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
