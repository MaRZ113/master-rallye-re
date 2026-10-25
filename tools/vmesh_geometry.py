"""V-MESH3/V-MESH4 reusable GT3 -> donor-draw geometry pipeline (frame-aware, wheel-anchored).

V-MESH4 (``BuildOptions`` defaults) replaces texture-alpha arch carving by an analytic wheel-house cut with a
continuous liner (``vmesh_arch.py``), lifts the body to a rally ride height, routes translucent GT glazing
materials to the donor glass draw and keeps the cabin shell inside the paint shell.  ``BuildOptions.v3()``
reproduces the V-MESH3 behaviour.

Differences from the V-MESH2 converter (``vmesh_gt3_to_dx.py``, untouched and kept for
reproducing ``exp-001``):

* **Vehicle frames.** Master Rallye stores ``car.dx`` (race) and ``complete.dx`` (frontend)
  in different vertical frames: in every stock donor ``complete.dx`` is ``car.dx`` translated by a
  constant ``dy`` (Navara 0.393 m, dx = dz = 0).  The body is generated once in the
  frontend frame and shifted by ``-dy`` for ``car.dx``.
* **Wheel anchoring.** The GT body is aligned to the donor's wheel hubs in all three axes (axle
  mid-point, track-independent wheelbase scale, GT hub height -> donor hub height) instead of
  "ground at y = 0".
* **Wheel size.** Uniform scale comes from the wheelbase; the visual wheels (``wheel.dx`` and the
  wheels embedded in ``complete.dx``) are scaled about their hubs by ``k = s * r_gt / r_donor`` so
  the donor tyre fits the GT arch the way the GT tyre did.  The physical tyre radius (physics XML)
  is not changed, see scale-and-risks.
* **Donor leftovers.** The donor cab (``underdash``) is replaced by the GT cabin shell in both
  files; donor crew draws are translated, not distorted, to sit under the GT roof.

No GT data is stored here; private input is read from a user-supplied OBJ.
"""
from __future__ import annotations

import collections
import dataclasses
import math
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.texture_authoring import decode_rgba_png  # noqa: E402
from master_rallye.topology_writer import (  # noqa: E402
    CompiledVertex, DrawGeometry, rebuild_topology, source_geometry)
import vmesh_arch  # noqa: E402
from vmesh_diagnose import donor_hubs_complete, frame_offset, wheel_extent  # noqa: E402
from vmesh_gt3_to_dx import (  # noqa: E402
    DEFAULT_UV, FILLER_SIZE, ROLE_UV, _unit, classify, face_normal, measure_axles, parse_gt_obj, sha256)

# Navara donor draw roles (audited listings, see docs).  ``crew`` draws are translated,
# ``wheels`` draws are scaled about their hubs, everything else becomes a hidden filler.
PROFILES = {
    "car": {
        "roles": {"paint": 3, "black": 9, "tail_lamp": 24, "head_lamp": 25, "glass": 35, "interior": 0},
        "crew": (1, 2, 16, 17, 18, 19, 20),   # seat, name tag, suit, arms, helmet
        "wheels": (),
    },
    "complete": {
        "roles": {"paint": 3, "black": 9, "tail_lamp": 16, "head_lamp": 25, "glass": 24, "interior": 0},
        "crew": (),
        "wheels": (20, 21, 22, 23),            # embedded wheels
    },
}
DEFAULT_GT_WHEEL_RADIUS = 0.29     # m; from the GT3 reference side view (see docs), cross-checked with arch top ~0.6 m
ARCH_MARGIN = 0.02                 # m clearance kept between tyre and relieved body vertices
ARCH_LIP_MARGIN = 0.03             # m between tyre and the snapped arch lip (outer fender plane)
CREW_HEADROOM = 0.08               # m between helmet top and GT cabin roof
ARCH_GAP = 0.06                    # m tyre -> arch lip (V-MESH4 cut mode; donor Navara arch gaps are 0.04-0.08 m)
ARCH_SIDES = 24                    # N of the circumscribed prism that defines the opening
ARCH_INBOARD = 0.06                # m inboard of the tyre's inner face where the wheel-house wall stands
ARCH_CUT_ROLES = ("paint", "black")
INTERIOR_INSET = 0.03              # m the cabin shell is shrunk so it cannot poke through the paint shell
GLAZING_MAX_MEAN_ALPHA = 245


@dataclass(frozen=True)
class DonorContext:
    frame_dy: float
    hubs_complete: tuple           # four (x, y, z) hubs in the complete.dx frame
    wheel_radius: float            # visual radius of the donor wheel.dx
    wheel_half_width: float

    @property
    def hub_y(self) -> float:
        return sum(h[1] for h in self.hubs_complete) / 4

    @property
    def axle_z(self) -> tuple[float, float]:
        front = [h[2] for h in self.hubs_complete if h[2] > 0]
        rear = [h[2] for h in self.hubs_complete if h[2] < 0]
        return sum(front) / len(front), sum(rear) / len(rear)


def make_context(donor_car: bytes, donor_complete: bytes, donor_wheel: bytes) -> DonorContext:
    car, comp, wheel = parse_dx_bytes(donor_car), parse_dx_bytes(donor_complete), parse_dx_bytes(donor_wheel)
    off = frame_offset(car, comp)
    if off["dx_abs_max"] > 1e-3 or off["dz_abs_max"] > 1e-3 or off["dy_max"] - off["dy_min"] > 1e-3:
        raise ValueError(f"donor car/complete are not a pure vertical translation: {off}")
    r, hw = wheel_extent(wheel)
    return DonorContext(off["dy"], tuple(donor_hubs_complete(comp)), r, hw)


@dataclass(frozen=True)
class FitPlan:
    scale: float
    wheel_scale: float
    gt_wheel_radius: float
    gt_mid_z: float                 # GT axle mid-point after the 180 degree yaw
    axles: dict
    lift: float = 0.0               # m; body (not wheels) is raised by this amount (ride height)

    def hub_y(self, ctx: DonorContext, profile: str) -> float:
        return ctx.hub_y - (ctx.frame_dy if profile == "car" else 0.0)

    def transform(self, ctx: DonorContext, profile: str):
        s, mid = self.scale, sum(ctx.axle_z) / 2
        hy, r = self.hub_y(ctx, profile), self.gt_wheel_radius

        def tp(p):   # yaw 180 about Y, uniform scale, align axle mid-point and hub height
            return (-p[0] * s, s * (p[1] - r) + hy + self.lift, (-p[2] - self.gt_mid_z) * s + mid)

        def tn(n):
            return (-n[0], n[1], -n[2])
        return tp, tn


def plan_fit(ctx: DonorContext, axles: dict, gt_wheel_radius: float = DEFAULT_GT_WHEEL_RADIUS,
             scale: float | None = None, wheel_scale: float | None = None, lift: float = 0.0) -> FitPlan:
    donor_wb = ctx.axle_z[0] - ctx.axle_z[1]
    s = scale if scale is not None else donor_wb / axles["wheelbase"]
    k = wheel_scale if wheel_scale is not None else s * gt_wheel_radius / ctx.wheel_radius
    return FitPlan(s, k, gt_wheel_radius, -(axles["front_z"] + axles["rear_z"]) / 2, axles, lift)


def hubs_in_frame(ctx: DonorContext, profile: str) -> list[tuple[float, float, float]]:
    dy = ctx.frame_dy if profile == "car" else 0.0
    return [(x, y - dy, z) for x, y, z in ctx.hubs_complete]


def relieve(p, hubs, radius, half_width, outer: bool = False):
    """Push a point radially out of any tyre cylinder (radius/half-width already include margins).

    ``outer=True`` applies the disc on the whole outer-fender side (|x| > |hub x| - 0.2) instead of the
    tyre slab; used to round the serrated edge left by alpha-cutout carving.
    """
    for hx, hy, hz in hubs:
        if (abs(p[0]) <= abs(hx) - 0.2) if outer else (abs(p[0] - hx) > half_width):
            continue
        dy, dz = p[1] - hy, p[2] - hz
        r = math.hypot(dy, dz)
        if r < radius:
            if r < 1e-6:
                dy, dz, r = 1.0, 0.0, 1.0
            f = radius / r
            return (p[0], hy + dy * f, hz + dz * f), True
    return p, False


def scale_about_hub(p, hubs, k):
    """Scale a wheel vertex about the nearest hub (quadrant by sign of x and z)."""
    hub = min(hubs, key=lambda h: (h[0] - p[0]) ** 2 + (h[2] - p[2]) ** 2)
    return tuple(hub[i] + k * (p[i] - hub[i]) for i in range(3))


# ------------------------------------------------------------------ alpha cutouts
ALPHA_OPAQUE = 128            # texels with alpha >= this are solid
OVERLAY_TRANSPARENT_FRACTION = 0.5   # materials mostly transparent are livery/shadow overlays -> dropped
CARVE_MIN_TRANSPARENT_FRACTION = 0.01
CARVE_DEPTH = 3               # adaptive 4-way subdivision depth (cell = triangle edge / 8); budget-neutral vs donor
KEEPOUT_EXTRA = 0.30          # m beyond the visual tyre radius where cutout holes are true openings


class AlphaTexture:
    """GT PNG alpha plane; GT3 body panels use alpha for wheel-arch and grille openings."""

    def __init__(self, png: bytes):
        self.w, self.h, rgba = decode_rgba_png(png)
        self.alpha = bytes(rgba[3::4])
        n = self.w * self.h
        self.transparent_fraction = sum(1 for a in self.alpha if a < ALPHA_OPAQUE) / n

    @property
    def policy(self) -> str:
        if self.transparent_fraction >= OVERLAY_TRANSPARENT_FRACTION:
            return "drop"
        return "carve" if self.transparent_fraction >= CARVE_MIN_TRANSPARENT_FRACTION else "opaque"

    def at(self, u: float, v: float, v_flip: bool) -> int:
        x = int(math.floor(u * self.w)) % self.w
        y = int(math.floor((1.0 - v if v_flip else v) * self.h)) % self.h
        return self.alpha[y * self.w + x]


def parse_gt_full(path: Path) -> dict:
    """OBJ + MTL parse that keeps texture coordinates and material->PNG paths (private input)."""
    positions, normals, uvs, faces, textures = [], [], [], [], {}
    obj, material, name = "", "", None
    mtl = path.with_suffix(".mtl")
    for line in (mtl.read_text(encoding="utf-8").splitlines() if mtl.exists() else []):
        parts = line.split()
        if parts and parts[0] == "newmtl":
            name = parts[1]
        elif parts and parts[0] == "map_Kd" and name:
            textures[name] = path.parent / parts[1]
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts:
            continue
        tag = parts[0]
        if tag == "v":
            positions.append(tuple(float(x) for x in parts[1:4]))
        elif tag == "vn":
            normals.append(tuple(float(x) for x in parts[1:4]))
        elif tag == "vt":
            uvs.append((float(parts[1]), float(parts[2])))
        elif tag in ("o", "g"):
            obj = parts[1] if len(parts) > 1 else ""
        elif tag == "usemtl":
            material = parts[1]
        elif tag == "f":
            corners = []
            for item in parts[1:]:
                f = item.split("/")
                vi = int(f[0]) - 1
                ti = int(f[1]) - 1 if len(f) > 1 and f[1] else None
                ni = int(f[2]) - 1 if len(f) > 2 and f[2] else None
                corners.append((positions[vi], normals[ni] if ni is not None else None, (vi, ni),
                                uvs[ti] if ti is not None else None))
            for i in range(1, len(corners) - 1):
                faces.append((obj, material, (corners[0], corners[i], corners[i + 1])))
    return {"faces": faces, "textures": textures}


def _mid(a, b):
    pos = tuple((a[0][i] + b[0][i]) / 2 for i in range(3))
    nrm = None
    if a[1] is not None and b[1] is not None:
        nrm = _unit(tuple((a[1][i] + b[1][i]) / 2 for i in range(3)))
    uv = None if a[3] is None or b[3] is None else tuple((a[3][i] + b[3][i]) / 2 for i in range(2))
    return (pos, nrm, ("m", tuple(round(c, 5) for c in pos), None if nrm is None else tuple(round(c, 4) for c in nrm)), uv)


def carve_triangle(tri, tex: AlphaTexture, v_flip: bool, depth: int = CARVE_DEPTH, zone=None):
    """Split a triangle by the texture alpha: returns (solid_triangles, hole_triangles).

    ``zone(gt_position) -> bool`` restricts where transparency counts (outside it the texture is treated
    as solid), which keeps the subdivision confined to the wheel openings.
    """
    a, b, c = tri
    pts = [a, b, c, _mid(a, b), _mid(b, c), _mid(c, a)]
    cen_pos = tuple(sum(p[0][i] for p in (a, b, c)) / 3 for i in range(3))
    cen_uv = tuple(sum(p[3][i] for p in (a, b, c)) / 3 for i in range(2))
    probes = [(p[0], p[3]) for p in pts] + [(cen_pos, cen_uv)]
    solid_flags = [(tex.at(uv[0], uv[1], v_flip) >= ALPHA_OPAQUE) or (zone is not None and not zone(pos)) for pos, uv in probes]
    if all(solid_flags):
        return [tri], []
    if not any(solid_flags) or depth == 0:
        return ([tri], []) if solid_flags[-1] else ([], [tri])
    ab, bc, ca = pts[3], pts[4], pts[5]
    solid, hole = [], []
    for sub in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)):
        s_, h_ = carve_triangle(sub, tex, v_flip, depth - 1, zone)
        solid += s_
        hole += h_
    return solid, hole


def _tri_area(tri) -> float:
    a, b, c = (p[0] for p in tri)
    u = [b[i] - a[i] for i in range(3)]
    w = [c[i] - a[i] for i in range(3)]
    return 0.5 * math.sqrt((u[1] * w[2] - u[2] * w[1]) ** 2 + (u[2] * w[0] - u[0] * w[2]) ** 2 + (u[0] * w[1] - u[1] * w[0]) ** 2)


def in_wheel_zone(p, hubs, keepout_r) -> bool:
    """Point (in the target frame) lies in the side-view disc around a hub, on the outer/hub side."""
    return any(math.hypot(p[1] - h[1], p[2] - h[2]) < keepout_r and abs(p[0]) > abs(h[0]) - 0.2 for h in hubs)


def detect_uv_flip(faces, textures: dict, tp, hubs, keepout_r) -> tuple[bool, dict]:
    """Choose the V orientation whose cutouts concentrate in the wheel zones (measured, not assumed).

    Only materials whose cutouts are predominantly wheel openings under at least one orientation vote
    (other cutouts, e.g. grilles, say nothing about V orientation).
    """
    cache = {}
    per = collections.defaultdict(lambda: {True: [0.0, 0.0], False: [0.0, 0.0]})    # material -> flip -> [near, total]
    for obj, material, tri in faces:
        if classify(obj, material) != "paint" or material not in textures or any(c[3] is None for c in tri):
            continue
        tex = cache.setdefault(material, AlphaTexture(textures[material].read_bytes()))
        if tex.policy != "carve":
            continue
        for flip in (True, False):
            for hole in carve_triangle(tri, tex, flip, 4)[1]:
                area = _tri_area(hole)
                per[material][flip][1] += area
                if in_wheel_zone(tp(tuple(sum(c[0][i] for c in hole) / 3 for i in range(3))), hubs, keepout_r):
                    per[material][flip][0] += area
    frac = lambda v: v[0] / v[1] if v[1] else 0.0
    voters = [m for m, d in per.items() if max(frac(d[True]), frac(d[False])) >= 0.8]
    score = {f: sum(per[m][f][0] for m in voters) / max(sum(per[m][f][1] for m in voters), 1e-9) for f in (True, False)}
    evidence = {"voting_materials": sorted(voters),
                "cutout_area_in_wheel_zones_fraction_v_flipped": round(score[True], 4),
                "cutout_area_in_wheel_zones_fraction_v_direct": round(score[False], 4),
                "cutout_area_m2_v_flipped": round(sum(per[m][True][1] for m in voters), 3),
                "cutout_area_m2_v_direct": round(sum(per[m][False][1] for m in voters), 3)}
    return score[True] >= score[False], evidence


def _filler(point, color):
    x, y, z = point
    return DrawGeometry(tuple(CompiledVertex((x + dx, y, z + dz), (0.0, 1.0, 0.0), color, ((0.5, 0.5),))
                              for dx, dz in ((0, 0), (FILLER_SIZE, 0), (0, FILLER_SIZE))), ((0, 1, 2),))


@dataclass(frozen=True)
class BuildOptions:
    """Geometry style switches.  Defaults = V-MESH4; ``BuildOptions.v3()`` = V-MESH3 behaviour."""

    arch: str = "cut"                  # "cut" (analytic wheel house + liner) | "alpha" (V-MESH3 carving + relief)
    arch_gap: float = ARCH_GAP         # m between visual tyre and the arch lip (cut mode)
    arch_sides: int = ARCH_SIDES       # N of the circumscribed prism
    arch_inboard: float = ARCH_INBOARD  # m inboard of the tyre's inner face where the liner wall stands
    glazing: bool = True               # translucent GT glazing materials -> donor glass draw; GT 'glass' strips -> trim
    interior_inset: float = INTERIOR_INSET   # m the cabin shell is shrunk so it stays inside the paint shell
    crew_headroom: float = CREW_HEADROOM
    alpha_cutouts: bool = True         # alpha mode only: bake wheel-opening cutouts

    @classmethod
    def v3(cls, **kw) -> "BuildOptions":
        return cls(arch="alpha", glazing=False, interior_inset=0.0, **kw)


def find_glazing_materials(faces, textures: dict) -> dict:
    """GT trim-class (Mat6) materials whose texture is uniformly translucent *and* mostly dark are window panes.

    Measured on the texture alpha plane only (no names): minimum alpha >= ALPHA_OPAQUE (nothing is cut out),
    mean alpha <= GLAZING_MAX_MEAN_ALPHA (not a plain opaque trim) and mean colour luminance <= 80.
    """
    out, seen = {}, set()
    for obj, material, tri in faces:
        if material in seen or not material.startswith("Mat6") or material not in textures:
            continue
        seen.add(material)
        w, h, rgba = decode_rgba_png(textures[material].read_bytes())
        alpha = rgba[3::4]
        lum = sum(0.3 * rgba[i] + 0.59 * rgba[i + 1] + 0.11 * rgba[i + 2] for i in range(0, len(rgba), 4)) / (w * h)
        mean_a = sum(alpha) / len(alpha)
        if min(alpha) >= ALPHA_OPAQUE and mean_a <= GLAZING_MAX_MEAN_ALPHA and lum <= 80:
            out[material] = {"mean_alpha": round(mean_a, 1), "min_alpha": min(alpha), "mean_luminance": round(lum, 1)}
    return out


def build_candidate(obj_path: Path, donor_bytes: bytes, ctx: DonorContext, plan: FitPlan, profile: str,
                    options: BuildOptions | None = None, *, crew_headroom: float | None = None,
                    alpha_cutouts: bool | None = None, classifier=None, overlay_keep=None,
                    source_map: list | None = None, dropped_map: list | None = None, material_plan=None) -> tuple[bytes, dict]:
    """Build one donor-draw DX from a GT OBJ.

    V-MESH4.1 hooks (all optional, defaults keep V-MESH3/4 behaviour byte-for-byte): ``classifier(obj, material)``
    returns the final role or ``"exclude"`` (content-driven LOD0 classification); ``overlay_keep(tri)`` decides
    whether a triangle of a mostly-transparent overlay material is kept (unsupported surfaces) or dropped (decals);
    ``source_map`` (a list) receives one record per emitted triangle with its source object/material/face/UVs.
    """
    opt = options or BuildOptions()
    if crew_headroom is not None or alpha_cutouts is not None:     # V-MESH3 call signature
        opt = dataclasses.replace(opt, crew_headroom=opt.crew_headroom if crew_headroom is None else crew_headroom,
                                  alpha_cutouts=opt.alpha_cutouts if alpha_cutouts is None else alpha_cutouts)
    cut_mode = opt.arch == "cut"
    native = opt.arch == "native"          # source arches are used as they are: no cut, no relief, no carving
    alpha_cutouts = opt.alpha_cutouts and opt.arch == "alpha"
    spec = PROFILES[profile]
    roles_map = dict(spec["roles"])
    if material_plan is not None:           # V-MESH4.2: pool draws that carry packed GT textures
        roles_map.update(material_plan.role_draws(profile))
    gt = parse_gt_full(obj_path)
    faces, textures = gt["faces"], gt["textures"]
    tp, tn = plan.transform(ctx, profile)
    hubs = hubs_in_frame(ctx, profile)
    vis_r, vis_hw = plan.wheel_scale * ctx.wheel_radius, plan.wheel_scale * ctx.wheel_half_width
    relief_r, relief_hw = vis_r + ARCH_MARGIN, vis_hw + ARCH_MARGIN
    keepout_r = vis_r + KEEPOUT_EXTRA
    houses = [vmesh_arch.WheelHouse(h, vis_r + opt.arch_gap, abs(h[0]) - vis_hw - opt.arch_inboard, opt.arch_sides) for h in hubs]
    house_planes = [h.planes() for h in houses]
    glazing = find_glazing_materials(faces, textures) if (opt.glazing and classifier is None) else {}
    glazing_active = bool(glazing)          # without a translucent pane material the V-MESH3 role mapping stays in force

    model = parse_dx_bytes(donor_bytes)
    originals = source_geometry(model)
    donor_color = {d.draw_index: collections.Counter(v.color for v in originals[d.draw_index].vertices).most_common(1)[0][0]
                   for d in model.physical_draws}
    buckets = {r: {"index": {}, "verts": [], "tris": []} for r in roles_map}
    counts, excluded, alpha_stats = collections.Counter(), collections.Counter(), collections.Counter()
    arch_stats = collections.Counter()
    moved = {}
    agree = disagree = 0
    textures_cache: dict[str, AlphaTexture] = {}
    v_flip, flip_evidence = True, {"note": "alpha cutouts disabled"}
    if alpha_cutouts:
        v_flip, flip_evidence = detect_uv_flip(faces, textures, tp, hubs, keepout_r)
    lip_edges = [[] for _ in houses]
    pending = collections.defaultdict(list)       # cut mode: clipped triangles, flushed after T-junction repair

    def emit_world(role, corners):
        """Add one already-transformed triangle (corners = (pos, normal|None, key, uv)) to its role's draw."""
        nonlocal agree, disagree
        pos = []
        for c in corners:
            q, did = c[0], False
            if opt.arch == "alpha":
                q, did = relieve(c[0], hubs, relief_r, relief_hw)
                if not did and alpha_cutouts:
                    q, did = relieve(c[0], hubs, vis_r + ARCH_LIP_MARGIN, 0.0, outer=True)   # round the carved arch edge
            if did:
                moved[c[2]] = max(moved.get(c[2], 0.0), math.dist(c[0], q))
            pos.append(q)
        fn = face_normal(*pos)
        if fn is None:
            counts["degenerate_dropped"] += 1
            return
        bucket, draw_id, local = buckets[role], roles_map[role], []
        for c, p in zip(corners, pos):
            n = (_unit(c[1]) if c[1] is not None else None) or fn
            agree, disagree = (agree + 1, disagree) if sum(a_ * b_ for a_, b_ in zip(n, fn)) >= 0 else (agree, disagree + 1)
            key = (c[2], ("f", tuple(round(x, 5) for x in fn)) if c[1] is None else None)
            if material_plan is not None:
                key = key + (tuple(round(x, 6) for x in c[3]),)
            idx = bucket["index"].get(key)
            if idx is None:
                idx = len(bucket["verts"])
                bucket["index"][key] = idx
                if material_plan is not None:
                    vert_uv, vert_color = tuple(c[3]), material_plan.vertex_color(role)
                else:
                    vert_uv, vert_color = ROLE_UV.get(role, DEFAULT_UV), donor_color[draw_id]
                bucket["verts"].append(CompiledVertex(tuple(float(x) for x in p), tuple(float(x) for x in n), vert_color, (vert_uv,)))
                if cur_interior:
                    interior_refs.append((role, idx))
            if cur_interior:
                interior_points.append(p)
            local.append(idx)
        bucket["tris"].append(tuple(local))
        if source_map is not None and cur_src:
            source_map.append({"role": role, "draw": draw_id, "tri": len(bucket["tris"]) - 1, **cur_src})

    cur_src: dict = {}
    interior_refs: list = []
    interior_points: list = []
    cur_interior = False

    def emit(role, corners, uvs=None):
        """Transform one GT (sub)triangle to the target frame; in cut mode clip it against the wheel houses."""
        world = tuple((tp(c[0]), (_unit(tn(c[1])) if c[1] is not None else None), c[2], (uvs[i] if uvs is not None else c[3]))
                      for i, c in enumerate(corners))
        if source_map is not None:
            cur_src.clear()
            cur_src.update(face=face_no, obj=cur_face[0], material=cur_face[1], source_role=cur_face[2],
                           corners=[{"v": c[2][0], "n": c[2][1], "uv": None if c[3] is None else [c[3][0], c[3][1]]} for c in corners],
                           dx_uv=None if uvs is None else [[u[0], u[1]] for u in uvs])
        if cut_mode and role in ARCH_CUT_ROLES:
            kept, lips, removed = vmesh_arch.cut_wheel_houses([world], houses, house_planes)
            for i, edges in enumerate(lips):
                lip_edges[i] += edges
            arch_stats["area_removed_m2_x1e6"] += int(1e6 * removed)
            arch_stats["tris_untouched" if (len(kept) == 1 and kept[0] is world) else "tris_clipped"] += 1
            pending[role] += kept
        else:
            emit_world(role, world)

    cur_face = ("", "", None)
    face_no = -1
    for obj, material, tri in faces:
        face_no += 1
        cur_face = (obj, material, None)
        role = classifier(obj, material) if classifier is not None else classify(obj, material)
        if classifier is not None:
            pass
        elif glazing_active and role == "black" and material in glazing:
            role = "glass"                                   # window panes -> alpha-blended donor glass draw
            arch_stats["glazing_tris"] += 1
        elif glazing_active and role == "glass":
            role = "black"                                   # thin GT glass strips = window seals/frames -> opaque trim
            arch_stats["glass_strip_tris_to_trim"] += 1
        counts[role] += 1
        if role == "exclude":
            excluded["reflection_shell" if "reflection" in obj else "lit_tail_lamp_overlay" if "_tail_lamp_on" in obj
                     else "untextured_Mat-1_shell"] += 1
            continue
        routed_uvs = None
        cur_interior = role == "interior"
        cur_face = (obj, material, role)
        if material_plan is not None:
            routed = material_plan.route(face_no, tri, role)
            if routed is not None:
                if routed[0] == "drop":
                    alpha_stats["tris_dropped_clear"] += 1
                    if dropped_map is not None:
                        dropped_map.append({"face": face_no, "obj": obj, "material": material, "reason": "alpha_clear_footprint",
                                            "corners": [{"v": c[2][0], "n": c[2][1], "uv": None if c[3] is None else [c[3][0], c[3][1]]} for c in tri]})
                    continue
                role, routed_uvs = routed
        if material_plan is None and role in ("paint", "black") and material in textures and all(c[3] is not None for c in tri):
            tex = textures_cache.setdefault(material, AlphaTexture(textures[material].read_bytes()))
            if tex.policy == "drop":
                if overlay_keep is not None and overlay_keep(tri):
                    alpha_stats["overlay_tris_kept_unsupported_surface"] += 1
                else:
                    alpha_stats["tris_dropped_overlay_or_invisible"] += 1
                    if dropped_map is not None:
                        dropped_map.append({"face": face_no, "obj": obj, "material": material, "reason": "supported_overlay_or_invisible",
                                            "corners": [{"v": c[2][0], "n": c[2][1], "uv": None if c[3] is None else [c[3][0], c[3][1]]} for c in tri]})
                    continue
            if alpha_cutouts and tex.policy == "carve":
                solid, holes = carve_triangle(tri, tex, v_flip, CARVE_DEPTH, lambda q: in_wheel_zone(tp(q), hubs, keepout_r))
                if holes:
                    alpha_stats["tris_carved_at_wheel_openings"] += 1
                    alpha_stats["wheel_opening_subtris_removed"] += len(holes)
                    alpha_stats["wheel_opening_area_removed_m2_x1000"] += int(1000 * sum(_tri_area(h) for h in holes) * plan.scale ** 2)
                    for sub in solid:
                        emit(role, sub)
                    continue
        emit(role, tri, routed_uvs)

    liner = {"tube_tris": 0, "wall_tris": 0, "lip_edges": [len(e) for e in lip_edges]}
    if cut_mode:
        for house, edges in zip(houses, lip_edges):
            tube, wall = vmesh_arch.build_liner(edges, house)
            pending["black"] += tube + wall
            liner["tube_tris"] += len(tube)
            liner["wall_tris"] += len(wall)
        for role, tris in pending.items():
            generated = [c for t in tris for c in t if c[2] and c[2][0] == "g"]
            before = len(tris)
            tris = vmesh_arch.split_tjunctions(tris, generated)
            arch_stats["tjunction_splits"] += len(tris) - before
            for t in tris:
                emit_world(role, t)

    if material_plan is not None and opt.interior_inset > 0 and interior_points:
        centre = [(min(p[i] for p in interior_points) + max(p[i] for p in interior_points)) / 2 for i in range(3)]
        half = [(max(p[i] for p in interior_points) - min(p[i] for p in interior_points)) / 2 for i in range(3)]
        k = [max(0.0, 1.0 - opt.interior_inset / h) if h > 1e-6 else 1.0 for h in half]
        for r_, idx in interior_refs:
            v = buckets[r_]["verts"][idx]
            buckets[r_]["verts"][idx] = CompiledVertex(tuple(centre[i] + (v.position[i] - centre[i]) * k[i] for i in range(3)),
                                                       v.normal, v.color, v.uvs)
        interior_points[:] = [tuple(centre[i] + (p[i] - centre[i]) * k[i] for i in range(3)) for p in interior_points]
    elif opt.interior_inset > 0 and buckets["interior"]["verts"]:
        ip = [v.position for v in buckets["interior"]["verts"]]
        centre = [(min(p[i] for p in ip) + max(p[i] for p in ip)) / 2 for i in range(3)]
        half = [(max(p[i] for p in ip) - min(p[i] for p in ip)) / 2 for i in range(3)]
        k = [max(0.0, 1.0 - opt.interior_inset / h) if h > 1e-6 else 1.0 for h in half]
        buckets["interior"]["verts"] = [CompiledVertex(tuple(centre[i] + (v.position[i] - centre[i]) * k[i] for i in range(3)),
                                                       v.normal, v.color, v.uvs) for v in buckets["interior"]["verts"]]

    edits: dict[int, DrawGeometry] = {}
    for role, bucket in buckets.items():
        if not bucket["tris"]:
            if material_plan is not None and role in material_plan.optional_roles:
                continue                                      # the draw becomes a hidden filler like any unused donor draw
            raise ValueError(f"role {role} received no GT geometry")
        edits[roles_map[role]] = DrawGeometry(tuple(bucket["verts"]), tuple(bucket["tris"]))
    cab = interior_points if material_plan is not None else [v.position for v in buckets["interior"]["verts"]]
    cab_floor, cab_roof = min(p[1] for p in cab), max(p[1] for p in cab)
    cab_z = sum(p[2] for p in cab) / len(cab)

    crew_dy = 0.0
    if spec["crew"]:
        donor_top = max(v.position[1] for d in spec["crew"] for v in originals[d].vertices)
        crew_dy = (cab_roof - opt.crew_headroom) - donor_top
        for d in spec["crew"]:
            edits[d] = DrawGeometry(tuple(
                CompiledVertex((v.position[0], v.position[1] + crew_dy, v.position[2]), v.normal, v.color, v.uvs,
                               source_vertex_id=v.source_vertex_id) for v in originals[d].vertices), originals[d].triangles)
    for d in spec["wheels"]:
        edits[d] = DrawGeometry(tuple(
            CompiledVertex(scale_about_hub(v.position, hubs, plan.wheel_scale), v.normal, v.color, v.uvs,
                           source_vertex_id=v.source_vertex_id) for v in originals[d].vertices), originals[d].triangles)
    fillers = []
    spot = (0.0, cab_floor + 0.15, cab_z)
    for draw in model.physical_draws:
        i = draw.draw_index
        if i in edits:
            continue
        edits[i] = _filler(spot, donor_color[i])
        fillers.append(i)

    rebuilt = rebuild_topology(donor_bytes, edits, bounds_mode="recompute")
    body = [v.position for r, b in buckets.items() if r != "interior" for v in b["verts"]]
    ys = sorted(p[1] for p in body)
    crew_pts = [(v.position[0], v.position[1] + crew_dy, v.position[2]) for d in spec["crew"] for v in originals[d].vertices]
    report = {
        "profile": profile, "options": dataclasses.asdict(opt), "scale": plan.scale, "wheel_scale": plan.wheel_scale,
        "gt_wheel_radius": plan.gt_wheel_radius, "lift_m": plan.lift,
        "axles_gt": plan.axles, "frame_dy": ctx.frame_dy, "frame_shift_applied": -ctx.frame_dy if profile == "car" else 0.0,
        "hub_y_frame": plan.hub_y(ctx, profile), "hubs_frame": [list(h) for h in hubs],
        "visual_tyre_radius": vis_r, "visual_tyre_half_width": vis_hw, "physical_tyre_radius_hint": ctx.wheel_radius,
        "tyre_hover_if_physical_radius_is_donor_m": ctx.wheel_radius - vis_r,
        "gt_face_roles": dict(counts), "exclusion_breakdown": dict(excluded),
        "alpha_cutouts": {"enabled": alpha_cutouts, "v_flip": v_flip, "evidence": flip_evidence, **dict(alpha_stats),
                          "material_policy": {m: t.policy for m, t in sorted(textures_cache.items())}},
        "arch": ({"mode": "native", "source_arches_used_as_is": True, "cut": False, "relief": False, "subdivision": False,
                  "visual_tyre_radius": vis_r, **dict(arch_stats)} if native else
                 {"mode": opt.arch, "radius": vis_r + opt.arch_gap, "gap": opt.arch_gap, "sides": opt.arch_sides,
                  "inboard_wall_abs_x": [h.x_in for h in houses], **dict(arch_stats), **liner}),
        "glazing": {"materials": glazing, "enabled": opt.glazing, "active": glazing_active},
        "normal_vs_face_agreement": {"agree": agree, "disagree": disagree},
        "relief": {"margin": ARCH_MARGIN, "gt_vertices_moved": len(moved),
                   "max_displacement_m": max(moved.values(), default=0.0),
                   "mean_displacement_m": (sum(moved.values()) / len(moved)) if moved else 0.0},
        "cabin": {"floor_y": cab_floor, "roof_y": cab_roof, "centre_z": cab_z, "inset": opt.interior_inset},
        "crew": {"draws": list(spec["crew"]), "dy": crew_dy, "headroom_requested": opt.crew_headroom,
                 "bbox": ([[min(p[i] for p in crew_pts) for i in range(3)], [max(p[i] for p in crew_pts) for i in range(3)]]
                          if crew_pts else None)},
        "body_extent": {"min": [min(p[i] for p in body) for i in range(3)], "max": [max(p[i] for p in body) for i in range(3)],
                        "roof_y_p99": ys[int(len(ys) * 0.99)]},
        "replaced_draws": dict(roles_map), "wheel_draws_scaled": list(spec["wheels"]),
        "replaced_draw_stats": {str(roles_map[r]): {"vertices": len(b["verts"]), "triangles": len(b["tris"])} for r, b in buckets.items()},
        "filler_draws": fillers, "filler_point": list(spot), "rebuild": rebuilt.to_dict(),
    }
    return rebuilt.data, report


def build_wheel_candidate(donor_wheel: bytes, wheel_scale: float, *, lateral_scale: float | None = None) -> tuple[bytes, dict]:
    """Uniformly scale wheel.dx about its origin (the hub) through the confirmed topology writer.

    The writer recomputes the 1339 bounds footer (a position-only patch would leave a footer the parser
    warns about).  The project must declare this resource as ``topology_candidate``.
    """
    lateral_scale = wheel_scale if lateral_scale is None else lateral_scale
    if not all(math.isfinite(x) and x > 0 for x in (wheel_scale, lateral_scale)):
        raise ValueError("wheel scales must be finite and positive")
    model = parse_dx_bytes(donor_wheel)
    edits = {d: DrawGeometry(tuple(
        CompiledVertex((v.position[0] * lateral_scale, v.position[1] * wheel_scale, v.position[2] * wheel_scale),
                       v.normal if lateral_scale == wheel_scale else _unit((v.normal[0] / lateral_scale, v.normal[1] / wheel_scale, v.normal[2] / wheel_scale)),
                       v.color, v.uvs, source_vertex_id=v.source_vertex_id)
        for v in g.vertices), g.triangles) for d, g in source_geometry(model).items()}
    rebuilt = rebuild_topology(donor_wheel, edits, bounds_mode="recompute")
    return rebuilt.data, {"wheel_scale": wheel_scale, "lateral_scale": lateral_scale,
                          "path": "rebuild_topology(recompute bounds)",
                          "rebuild": rebuilt.to_dict(), "output_sha256": sha256(rebuilt.data)}


def wheel_scale_from_clearance(donor_radius: float, current_scale: float, minimum_arch_gap: float,
                               clearance_margin: float = 0.005) -> dict:
    """Choose a race-wheel scale bounded by both the donor physics radius and measured arch clearance.

    The measurement is the minimum visible arch-lip gap at ``donor_radius * current_scale``. The target keeps
    ``clearance_margin`` at the lip and never exceeds the donor radius. This is a reusable fitment heuristic;
    callers still validate the output against body samples and the in-game suspension.
    """
    values = (donor_radius, current_scale, minimum_arch_gap, clearance_margin)
    if not all(math.isfinite(v) for v in values) or donor_radius <= 0 or current_scale <= 0 or clearance_margin < 0:
        raise ValueError("wheel fitment values must be finite; radius/scale positive and margin non-negative")
    current_radius = donor_radius * current_scale
    target_radius = min(donor_radius, max(current_radius, current_radius + minimum_arch_gap - clearance_margin))
    return {"scale": target_radius / donor_radius, "current_scale": current_scale,
            "current_radius_m": current_radius, "target_radius_m": target_radius,
            "minimum_arch_gap_m": minimum_arch_gap, "clearance_margin_m": clearance_margin,
            "method": "physics radius capped by measured arch-lip gap"}
