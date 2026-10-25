"""V-MESH1: convert a Gran Turismo 3 body OBJ into a donor-draw car.dx candidate.

The output is built with the existing, runtime-confirmed ``rebuild_topology``
path: the donor draw set, material strings, hierarchy and collision bytes are
preserved and only render arrays/indices are replaced.  GT geometry is
assigned to a fixed subset of donor draws; other exterior donor draws are
reduced to a hidden filler triangle; interior/driver draws are kept as-is.

Private input (GT OBJ) must never be committed.  Nothing here reads or writes
the retail executable or archive.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.topology_writer import (  # noqa: E402
    CompiledVertex, DrawGeometry, rebuild_topology, source_geometry)

# Donor (Navara) draw roles, from the audited draw/bbox listings.
PROFILES = {
    "car": {
        "roles": {
            "paint": 3,       # colour-tga / silverpaint-tga body
            "black": 9,       # black-tga trim
            "tail_lamp": 24,  # backlightjnavp-tga / perspex
            "head_lamp": 25,  # headlamp-tga / glass
            "glass": 35,      # screenfront windscreen (tag 7)
        },
        "keep": (0, 1, 2, 16, 17, 18, 19, 20),  # underdash, seat, driver, helmet
    },
    "complete": {
        "roles": {
            "paint": 3,       # colour-tga / silverpaint-tga body
            "black": 9,       # black-tga trim
            "tail_lamp": 16,  # backlightjnavp-tga / perspex
            "head_lamp": 25,  # headlamp-tga / glass
            "glass": 24,      # windscreen32-tga / glass
            # Navara's cab interior reaches y=1.77 (> Impreza roof 1.48), so the GT cabin
            # shell replaces underdash; seat/name-tag draws become fillers.
            "interior": 0,    # underdash-tga (centre texel is black)
        },
        "keep": (20, 21, 22, 23),               # embedded wheels
    },
}
DONOR_ROLES = PROFILES["car"]["roles"]
KEEP_DRAWS = PROFILES["car"]["keep"]
# Donor wheel volumes (hub centres from complete.dx; radius/half-width from wheel.dx).
DONOR_HUBS = tuple((sx * 0.855, 0.401, z) for sx in (-1, 1) for z in (1.495, -1.463))
WHEEL_RADIUS, WHEEL_HALF_WIDTH, ARCH_MARGIN = 0.383, 0.146, 0.03
# All GT texture mapping is discarded: every vertex samples one chosen donor texel.
# Centre texels were checked in the donor DXTs (glass: grey a=133, lens: light grey,
# flat paint/black).  The donor tail-lamp centre is pinkish, so a red texel is used
# (red in either vertical orientation of the stored raster).
ROLE_UV = {"tail_lamp": (10.5 / 32, 24.5 / 32)}
DEFAULT_UV = (0.5, 0.5)
# Navara hub centres measured from complete.dx wheel draws (rendered positions).
DONOR_AXLE_Z = (1.495, -1.463)  # front (+Z), rear
DONOR_FILLER_AT = (0.0, 0.45, 0.0)
FILLER_SIZE = 0.02


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- GT parsing
def parse_gt_obj(path: Path) -> dict:
    """Parse OBJ into per-face records: (obj_name, material, [(v, vt, vn)] * 3)."""
    positions, normals, faces = [], [], []
    obj, material = "", ""
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        parts = line.split()
        if not parts:
            continue
        tag = parts[0]
        if tag == "v":
            positions.append(tuple(float(x) for x in parts[1:4]))
        elif tag == "vn":
            normals.append(tuple(float(x) for x in parts[1:4]))
        elif tag in ("o", "g"):
            obj = parts[1] if len(parts) > 1 else ""
        elif tag == "usemtl":
            material = parts[1]
        elif tag == "f":
            corners = []
            for item in parts[1:]:
                f = item.split("/")
                corners.append((int(f[0]) - 1,
                                int(f[1]) - 1 if len(f) > 1 and f[1] else None,
                                int(f[2]) - 1 if len(f) > 2 and f[2] else None))
            for i in range(1, len(corners) - 1):  # fan; GT dumps are triangles already
                faces.append((obj, material, (corners[0], corners[i], corners[i + 1])))
    return {"positions": positions, "normals": normals, "faces": faces}


def classify(obj: str, material: str) -> str:
    """Map a GT face to a donor role (documented V-MESH1 rules)."""
    if material == "Mat-1_Tex35":
        return "interior"         # GT cabin shell; only used by profiles with an interior role
    if "reflection" in obj or "_tail_lamp_on" in obj or material.startswith("Mat-1"):
        return "exclude"          # env-map shells, lit-lamp duplicate, interior/dup shells
    if material.startswith("Mat4"):
        return "glass"
    if material.startswith("Mat6"):
        if "tail_lamp_off" in obj:
            return "tail_lamp"
        if material.split("_")[1] in ("Tex26", "Tex27", "Tex28"):
            return "head_lamp"
        return "black"
    return "paint"


# ---------------------------------------------------------------- fitting
def measure_axles(positions, faces) -> dict:
    """Estimate GT axle Z from wheel-arch gaps on the +X side (two height bands)."""
    used = {c[0] for _, _, tri in faces for c in tri}
    pts = [positions[i] for i in used]
    centres = []
    for lo, hi in ((0.15, 0.25), (0.35, 0.45)):
        zs = sorted({round(p[2], 2) for p in pts if p[0] > 0.75 and lo <= p[1] <= hi})
        gaps = [(a, b) for a, b in zip(zs, zs[1:]) if 0.4 < b - a < 1.0]
        mids = [(a + b) / 2 for a, b in gaps]
        # one arch per axle: centres must lie in the plausible axle ranges
        centres.append([m for m in mids if 0.9 <= abs(m) <= 1.6])
    if any(len(c) != 2 or c[0] * c[1] >= 0 for c in centres):
        raise ValueError(f"could not find exactly two arch gaps per band: {centres}")
    front = (centres[0][0] + centres[1][0]) / 2   # GT front is -Z
    rear = (centres[0][1] + centres[1][1]) / 2
    return {"bands": centres, "front_z": front, "rear_z": rear,
            "wheelbase": rear - front}


def fit_transform(axles: dict, scale: float | None):
    gt_wb = axles["wheelbase"]
    donor_wb = DONOR_AXLE_Z[0] - DONOR_AXLE_Z[1]
    s = scale if scale is not None else donor_wb / gt_wb
    gt_mid = -(axles["front_z"] + axles["rear_z"]) / 2        # after the 180 deg yaw
    donor_mid = (DONOR_AXLE_Z[0] + DONOR_AXLE_Z[1]) / 2

    def tp(p):                  # yaw 180 about Y (x,z -> -x,-z), uniform scale, align axle midpoint
        return (-p[0] * s, p[1] * s, (-p[2] - gt_mid) * s + donor_mid)

    def tn(n):                  # rotation only (uniform scale)
        return (-n[0], n[1], -n[2])
    return s, tp, tn


def relieve_wheel_volumes(p):
    """Push a body vertex radially out of any (margin-expanded) donor wheel cylinder."""
    for hx, hy, hz in DONOR_HUBS:
        if abs(p[0] - hx) > WHEEL_HALF_WIDTH + ARCH_MARGIN:
            continue
        dy, dz = p[1] - hy, p[2] - hz
        r = math.hypot(dy, dz)
        limit = WHEEL_RADIUS + ARCH_MARGIN
        if r < limit:
            if r < 1e-6:
                dy, dz, r = 1.0, 0.0, 1.0
            f = limit / r
            return (p[0], hy + dy * f, hz + dz * f), True
    return p, False


def _unit(v):
    m = math.sqrt(sum(c * c for c in v))
    return (v[0] / m, v[1] / m, v[2] / m) if m > 1e-12 else None


def face_normal(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    w = [c[i] - a[i] for i in range(3)]
    return _unit((u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]))


def body_extent(buckets) -> dict:
    pts = [v.position for b in buckets.values() for v in b["verts"]]
    ys = sorted(p[1] for p in pts)
    roof = ys[int(len(ys) * 0.99)]          # 99th percentile ignores antenna tips
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return {"min": lo, "max": hi, "roof_y_p99": roof}


# ---------------------------------------------------------------- build
def build_candidate(obj_path: Path, donor_bytes: bytes, scale: float | None = None,
                    axle_obj: Path | None = None, profile: str = "car") -> tuple[bytes, dict]:
    roles_map, keep_draws = PROFILES[profile]["roles"], PROFILES[profile]["keep"]
    gt = parse_gt_obj(obj_path)
    positions, normals, faces = gt["positions"], gt["normals"], gt["faces"]
    ref = parse_gt_obj(axle_obj) if axle_obj else gt  # LOD0 is the finest arch reference
    axles = measure_axles(ref["positions"], [f for f in ref["faces"] if classify(f[0], f[1]) not in ("exclude", "interior")])
    s, tp, tn = fit_transform(axles, scale)

    model = parse_dx_bytes(donor_bytes)
    originals = source_geometry(model)
    donor_color = {}
    for draw in model.physical_draws:
        cols = collections.Counter(v.color for v in originals[draw.draw_index].vertices)
        donor_color[draw.draw_index] = cols.most_common(1)[0][0]

    buckets: dict[str, dict] = {r: {"index": {}, "verts": [], "tris": []} for r in roles_map}
    relieved = 0
    excluded = collections.Counter()
    counts = collections.Counter()
    agree = disagree = 0
    for obj, material, tri in faces:
        role = classify(obj, material)
        if role == "interior" and "interior" not in roles_map:
            role = "exclude_interior"
        counts[role] += 1
        if role in ("exclude", "exclude_interior"):
            why = ("interior_shell" if role == "exclude_interior" else"reflection_shell" if "reflection" in obj else "lit_tail_lamp_overlay" if "_tail_lamp_on" in obj
                   else "untextured_Mat-1_shell")
            excluded[why] += 1
            continue
        pos = []
        for c in tri:
            q, moved = relieve_wheel_volumes(tp(positions[c[0]]))
            relieved += moved
            pos.append(q)
        fn = face_normal(*pos)
        if fn is None:
            counts["degenerate_dropped"] += 1
            continue
        draw_id = roles_map[role]
        bucket = buckets[role]
        local = []
        for corner, p in zip(tri, pos):
            if corner[2] is not None:
                n = tn(normals[corner[2]])
                n = _unit(n) or fn
            else:
                n = fn
            if sum(a * b for a, b in zip(n, fn)) >= 0:
                agree += 1
            else:
                disagree += 1
            key = (corner[0], corner[2] if corner[2] is not None else ("f", tuple(round(x, 5) for x in fn)))
            idx = bucket["index"].get(key)
            if idx is None:
                idx = len(bucket["verts"])
                bucket["index"][key] = idx
                bucket["verts"].append(CompiledVertex(
                    position=tuple(float(x) for x in p), normal=tuple(float(x) for x in n),
                    color=donor_color[draw_id], uvs=(ROLE_UV.get(role, DEFAULT_UV),)))
            local.append(idx)
        bucket["tris"].append(tuple(local))

    edits: dict[int, DrawGeometry] = {}
    for role, bucket in buckets.items():
        if not bucket["tris"]:
            raise ValueError(f"role {role} received no GT geometry")
        edits[roles_map[role]] = DrawGeometry(tuple(bucket["verts"]), tuple(bucket["tris"]))
    replaced = set(edits)
    fillers = []
    for draw in model.physical_draws:
        i = draw.draw_index
        if i in replaced or i in keep_draws:
            continue
        x, y, z = DONOR_FILLER_AT
        col = donor_color[i]
        edits[i] = DrawGeometry(tuple(
            CompiledVertex((x + dx, y, z + dz), (0.0, 1.0, 0.0), col, ((0.5, 0.5),))
            for dx, dz in ((0, 0), (FILLER_SIZE, 0), (0, FILLER_SIZE))), ((0, 1, 2),))
        fillers.append(i)

    rebuilt = rebuild_topology(donor_bytes, edits, bounds_mode="recompute")
    report = {
        "scale": s, "axles_gt": axles,
        "donor_axle_z": list(DONOR_AXLE_Z),
        "gt_face_roles": dict(counts),
        "normal_vs_face_agreement": {"agree": agree, "disagree": disagree},
        "profile": profile, "wheel_relief_vertex_moves": relieved, "exclusion_breakdown": dict(excluded),
        "body_extent": body_extent(buckets),
        "replaced_draws": dict(roles_map),
        "replaced_draw_stats": {str(roles_map[r]): {"vertices": len(b["verts"]), "triangles": len(b["tris"])}
                                for r, b in buckets.items()},
        "filler_draws": fillers, "kept_draws": list(keep_draws),
        "rebuild": rebuilt.to_dict(),
    }
    return rebuilt.data, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--obj", type=Path, required=True)
    ap.add_argument("--donor-car-dx", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True, help="new car.dx path (must not exist)")
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--scale", type=float, default=None)
    ap.add_argument("--profile", choices=sorted(PROFILES), default="car")
    ap.add_argument("--axle-obj", type=Path, default=None, help="OBJ used to measure wheel arches (default: --obj)")
    args = ap.parse_args()
    if args.output.exists() or args.report.exists():
        ap.error("refusing to overwrite an existing output/report")
    donor = args.donor_car_dx.read_bytes()
    data, report = build_candidate(args.obj, donor, args.scale, args.axle_obj, args.profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    report.update({"axle_obj_sha256": sha256(args.axle_obj.read_bytes()) if args.axle_obj else None, "donor_sha256": sha256(donor), "obj_sha256": sha256(args.obj.read_bytes()),
                   "output_sha256": sha256(data)})
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("scale", "output_sha256", "replaced_draw_stats", "filler_draws")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
