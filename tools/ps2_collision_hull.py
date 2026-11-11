"""Replace the tag-101 collision hull of a PC car.dx with the hull of the original PS2 CAR.PSM (Roster V4, Forklift).

Both formats store the vehicle hull as the same tag-101 record (base geometry + representations A/B); the PS2 file
ends after it (0xFFFFFFFF), the PC file follows it with a tag-0x53B bounds record:
    u32 0x53B, f32 centre[3], f32 radius, f32 min[3], f32 max[3]
The bounds record describes the visual model (for the Forklift it equals the visual AABB), which this tool does not
change, so it is kept byte-identical; only the tag-101 block is replaced.
Precondition: the PS2 and PC visual models share their model space (equal visual bounds), which is checked.
"""
from __future__ import annotations
import argparse, hashlib, json, math, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "ps2-research/tools"), str(HERE.parent.parent / "master-rallye-re-vehicles/src")]
import reflection_runtime as r                                     # noqa: E402
from master_rallye.collision import parse_collision_sections       # noqa: E402
from master_rallye.dx import parse_dx_bytes                        # noqa: E402

BOUNDS_TAG = 0x53B
BOUNDS = struct.Struct("<I10f")


def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def hull_points(hull):
    out = []
    for g in (hull.base_geometry, hull.representation_a.geometry_a, hull.representation_a.geometry_b,
              hull.representation_b.geometry_a, hull.representation_b.geometry_b):
        out.extend(g.vertices)
    return [p for p in out if all(math.isfinite(c) for c in p)]


def bounds_record(points) -> bytes:
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    centre = [f32((a + b) * 0.5) for a, b in zip(lo, hi)]
    radius = max(math.sqrt(sum((p[i] - centre[i]) ** 2 for i in range(3))) for p in points)
    return BOUNDS.pack(BOUNDS_TAG, *centre, radius, *lo, *hi)


def pc_parts(data: bytes, source: str):
    model = parse_dx_bytes(data, source=source)
    hull = model.collision.convex_hull
    if hull is None:
        raise ValueError(f"{source}: no tag101 hull")
    tail = data[hull.end_offset:]
    if len(tail) != BOUNDS.size or struct.unpack_from("<I", tail)[0] != BOUNDS_TAG:
        raise ValueError(f"{source}: unexpected trailer after tag101 ({len(tail)} bytes)")
    return model, hull, tail


def verify(paths):
    """Reproduce the stored bounds record of finite retail cars from visual + hull points."""
    report = []
    for path in paths:
        data = path.read_bytes()
        model, hull, tail = pc_parts(data, str(path))
        points = list(model.vertices.positions) + hull_points(hull)
        mine = bounds_record(points)
        stored = BOUNDS.unpack(tail)
        computed = BOUNDS.unpack(mine)
        delta = max(abs(a - b) for a, b in zip(stored[1:], computed[1:]))
        report.append({"car": path.parent.name, "exact": mine == tail, "max_abs_delta": delta})
    return report


def transplant(pc_path: Path, psm_path: Path):
    pc = pc_path.read_bytes()
    model, old_hull, _ = pc_parts(pc, str(pc_path))
    psm = psm_path.read_bytes()
    scene = r.decode_vehicle(psm)
    collision = parse_collision_sections(psm[scene.end:], base_offset=scene.end, source=str(psm_path), strict=True)
    if collision.tag_ids != (101,) or collision.errors or psm[collision.end_offset:] != b"\xff\xff\xff\xff":
        raise ValueError("PS2 CAR.PSM: expected exactly one tag101 hull and the 0xFFFFFFFF end")
    new_hull = collision.convex_hull
    ps2_visual = [scene.position(i) for i in range(scene.vertex_count)]
    pc_visual = list(model.vertices.positions)
    for axis in range(3):
        a = (min(p[axis] for p in ps2_visual), max(p[axis] for p in ps2_visual))
        b = (min(p[axis] for p in pc_visual), max(p[axis] for p in pc_visual))
        if max(abs(a[0] - b[0]), abs(a[1] - b[1])) > 1e-3:
            raise ValueError(f"visual models do not share a model space (axis {axis}: PS2 {a} PC {b})")
    block = psm[new_hull.tag_offset:new_hull.end_offset]
    out = pc[:old_hull.tag_offset] + block + pc[old_hull.end_offset:]
    check = parse_dx_bytes(out, source="patched")
    if check.collision.errors or check.collision.convex_hull is None:
        raise ValueError(f"patched car.dx does not parse: {check.collision.errors[:2]}")
    if out[:old_hull.tag_offset] != pc[:old_hull.tag_offset]:
        raise AssertionError("visual part changed")
    hull = check.collision.convex_hull
    return out, {
        "pc_source_sha256": hashlib.sha256(pc).hexdigest(), "ps2_source_sha256": hashlib.sha256(psm).hexdigest(),
        "visual_prefix_bytes_unchanged": old_hull.tag_offset,
        "old_hull": {"bytes": old_hull.end_offset - old_hull.tag_offset, "errors": list(model.collision.errors)[:3]},
        "new_hull": {"bytes": len(block), "sha256": hashlib.sha256(block).hexdigest(),
                     "rep_b_vertices": hull.representation_b.geometry_a.vertex_count, "rep_b_faces": hull.representation_b.face_count},
        "output_sha256": hashlib.sha256(out).hexdigest(), "output_bytes": len(out),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--verify", type=Path, nargs="*", default=[], help="retail car.dx files whose bounds record must be reproduced")
    p.add_argument("--pc", type=Path)
    p.add_argument("--psm", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    result = {}
    if a.verify:
        result["verify"] = verify(a.verify)
        if not all(row["exact"] for row in result["verify"]):
            print(json.dumps(result, indent=1)); sys.exit("bounds formula does not reproduce the retail records")
    if a.pc:
        data, result["transplant"] = transplant(a.pc, a.psm)
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_bytes(data)
    print(json.dumps(result, indent=1))
