"""Replace the cooked tag100 collision tree of a course DX with an exact BSP (R5T-INV E2.4).

usage: course_bsp_patch.py <source.gxm> <cooked.dx> [-o patched.dx]

The tree is built from the GXM's ``$bsp`` meshes (``$landdb``, ``$landdb fill``,
``COLLIDEobjects``) plus a rebuilt ``$skirt`` on the open edge of the land, with
spanning polygons clipped (see master_rallye.course_bsp).
Everything else in the cooked DX (render data, tag1339, land database, tag1500)
is kept byte for byte. The output keeps a newer timestamp than the GXM so the
game uses it instead of re-cooking.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.course_bsp import build_solid_bsp, close_land, encode_tag100, polygon  # noqa: E402
from master_rallye.course_gxm import _float3_at, parse_course_gxm_model_v7  # noqa: E402
from master_rallye.course_gxm_writer import decode_materials  # noqa: E402
from master_rallye.course_tag100 import parse_course_tag100_bytes  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402


BSP_MESHES = ("$landdb", "$landdb fill", "COLLIDEobjects")


def collision_polygons(gxm: Path):
    model = parse_course_gxm_model_v7(gxm)
    names = [m.name for m in decode_materials(model.materials.raw, model.materials.count)]
    tris, counts = [], {}
    for node in model.object_table.nodes:
        if node.mesh_index is None or node.name not in BSP_MESHES:
            continue
        counts[node.name] = node.mesh_size
        for index in range(node.mesh_index, node.mesh_index + node.mesh_size):
            tri = model.triangle(index)
            src = [_float3_at(model.positions, j) for j in tri.position_indices]
            u = [src[1][k] - src[0][k] for k in range(3)]
            v = [src[2][k] - src[0][k] for k in range(3)]
            n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            length = math.sqrt(sum(c * c for c in n)) or 1.0
            # source (x, y, z-up) -> DX (x, z, -y); outward normal from the source winding
            tris.append((index, node.name, names[tri.material_index],
                         [(p[0], p[2], -p[1]) for p in src], (n[0] / length, n[2] / length, -n[1] / length)))
    polys = []
    for index, mesh, name, pts, n in tris:
        poly = polygon(pts, n, index)
        if poly is not None:
            polys.append(poly)
    # Retail closes the land corridor with $nodraw $skirt walls; compiled DX
    # does not keep them: rebuild them on the map edge and patch small holes.
    land = [(index, pts) for index, mesh, name, pts, n in tris if mesh != "COLLIDEobjects"]
    walls, counts["closure"] = close_land([pts for _, pts in land])
    for quad, normal, local in walls:
        poly = polygon(quad, normal, land[local][0])  # code: the land triangle under the wall
        if poly is not None:
            polys.append(poly)
    return polys, counts


def patch(gxm: Path, dx: Path, out: Path) -> dict:
    raw = dx.read_bytes()
    model = parse_course_dx_bytes(raw, dx.name, dx)
    region = model.collision.bsp
    old = parse_course_tag100_bytes(region.raw, dx.name, allow_trailing=True)
    start = region.tag_offset
    polys, counts = collision_polygons(gxm)
    began = time.time()
    tree = build_solid_bsp(polys)
    tag100 = encode_tag100(tree)
    patched = raw[:start] + tag100 + raw[start + old.consumed_size:]
    check = parse_course_dx_bytes(patched, out.name, out)
    new = parse_course_tag100_bytes(check.collision.bsp.raw, out.name, allow_trailing=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_bytes(patched)
    tmp.replace(out)  # fails while the game holds the file; callers retry
    marker = out.with_suffix(".bsp.json")
    report = {"polygons": counts, "seconds": round(time.time() - began, 1),
            "old_header": list(old.header_words), "new_header": list(new.header_words),
            "old_bytes": old.consumed_size, "new_bytes": new.consumed_size, "output": str(out)}
    marker.write_text(json.dumps({"tag100_bytes": new.consumed_size, "dx_size": len(patched)}), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("gxm", type=Path)
    parser.add_argument("dx", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None, help="default: overwrite the DX in place")
    args = parser.parse_args()
    out = args.output or args.dx
    print(json.dumps(patch(args.gxm, args.dx, out), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
