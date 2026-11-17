"""Rally Championship Xtreme (PC) stage -> Master Rallye Course Studio project.

Input: one extracted stage archive folder (Data/Levels/<stage>.rcx: <stage>.map, config.cfg, *.tex).

Mapping (docs/rcx/RCX_TRACKS.md):
  frame     RCX world is right-handed with +Y down (road face normals by winding point to -Y, like the car
            meshes); MR's world is right-handed with +Y up. Points map (x, y, z) -> (-x, -y, z), a rotation:
            triangle winding is kept and the layout is not mirrored. Units are metres in both.
  geometry  every .map group becomes triangles of one Course Studio mesh by the Rally.exe surface:
            ground within --corridor (45 m) of the driving line -> ROLE_TERRAIN (drawn, collides, MR surface);
            ground beyond it, NO_COLLIDE / Forest / Bushy / Corona, Fence, bridge barriers and rails ->
            ROLE_VISUAL; Water -> ROLE_WATER; untextured groups (RCX invisible barrier walls) are dropped
            (--barriers keeps them as ROLE_COLLISION). The whole RCX soup as terrain needed 52 MB of native
            collision pools (32 MB model cache) and its open walls made phantom solids over the road.
  bridges   Wood / Metal faces: only deck tops the driving line runs on (8 m, +-2 m) stay solid, each with its own
            downward face 0.4 m lower (an exact land slab; the RCX underside is narrower than the top and left the
            deck edges unsupported); piers, beams and undersides are drawn only. Underpasses stay open.
  repair    the build repeats (--passes): terrain within 4 m of every off-road collision spot Course Studio
            reports (hole / phantom farther than --keep-m from the route) becomes drawn only.
  textures  RCX TEX (DXT1/DXT3/ARGB) -> PNG; halved until the course stays within the MR model-cache budget.
            UVs are top-origin in RCX, bottom-origin in Course Studio (v flipped once).
  race      route = config.cfg spline "driving line" (oriented from STRT to the last CHKP gate), resampled
            every 10 m and kept 0.3 m above the drivable surface; start = STRT position and heading;
            finish = last CHKP gate; the gates between become the three native splits.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "evo2_tracks"))
from rcx_map import SURFACES, read_config, read_map  # noqa: E402
from rcx_tex import decode_tex  # noqa: E402
from to_course import (FINISH_GAP_M, SPLITS, TEXTURE_BUDGET_BYTES, box_mean, safe_limits, start_area,  # noqa: E402
                       texture_bytes, write_png)

from master_rallye.studio.model import (ROLE_COLLISION, ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER, Area, Checkpoint,  # noqa: E402
                                        Material, Mesh, Texture, new_uid, safe_key)
from master_rallye.studio.templates import new_project  # noqa: E402

ROUTE_STEP_M = 10.0
SURFACE_MR = {'Tarmac': 'tarmac', 'Rough tarmac': 'tarmac', 'Cattle Grid': 'metal', 'THS': 'tarmac',
              'Gravel': 'gravel', 'Rough gravel': 'gravel', 'Dust': 'harddirt', 'Rough': 'harddirt',
              'Mud': 'mud', 'Snow': 'gravel', 'Ice': 'harddirt', 'Grass': 'grass', 'Soft grass': 'grass',
              'Rough grass': 'grass', 'Rock': 'rock', 'Fence': 'metal', 'Wood': 'harddirt', 'Metal': 'metal',
              'No Drive': 'rock', 'Unknown': 'rock', 'Water': 'water'}
DRAW_ONLY = {'NO_COLLIDE', 'Forest', 'Bushy', 'Corona'}
STRUCTURES = {'Wood', 'Metal'}  # bridges: deck tops the line runs on become exact slabs, underside/piers/beams drawn only
DECK_SLAB_M = 0.4
TERRAIN_FACE_BUDGET, CORRIDOR_MIN_M = 30000, 20.0
NEAR_KEEP_M = 4.0                     # repair never demotes terrain closer than this to the route
UNSTACK_M = 3.0                       # last repair: discs where only the top of stacked ground layers stays solid
EDGE_KEEP_M = 3.5                     # ... except the last-stage 1 m discs, which end this far out
OVERLAY_PASS_FLAG = 0x400             # .map group render flag: not drawn as plain geometry (see build_project)
DRAW_ONLY_TEXTURES = ('barrier', 'rail')  # bridge barriers and rails: open soup along the deck edges
# Blend layers (.map group flag 0x8, rcx_map.BLEND_FLAG): RCX blends texture -> texture2 by the vertex alpha (0 =
# texture, 255 = texture2; checked against the neighbouring plain groups on Clashin Darroch). MR draws the first
# texture opaque and texture2 as a second, alpha-blended layer BLEND_LIFT_M above it (the native shader multiplies
# texture alpha by the vertex alpha when the material's vertex-lighting byte is set: Rally.exe-independent, MR
# 0x57FED5). Without it only the first texture was drawn: patches and hard stripes on grass / gravel / tarmac.
BLEND_LIFT_M = 0.02
OVERLAY_SUFFIX = "#ovl"
# Props that collide in RCX (owner 2026-11-16/17: trees, woodpiles and 2D fences are solid there, passable in MR).
# RCX's own collision for trees, woodpiles and buildings is the untextured render-flag-0x2404 geometry ("hulls": a
# 0.9 m pyramid on every tree trunk, closed boxes on each woodpile); the drawn trees are NO_COLLIDE star planes.
# Each hull component becomes one closed oriented box (ROLE_COLLISION); Fence-surface panels (RCX collides with them
# directly) become continuous thin slabs. The open hull soup itself made phantom solids in MR's BSP.
PROP_REACH_M = 35.0                   # props farther from the driving line than this get no collision
HULL_MAX_H = 4.0                      # pyramid hulls reach 20+ m up: boxes stop this far above their base
HULL_BOX_MAX_M = 12.0                 # bigger / non-boxy hull components: thin slabs along their vertical faces
FENCE_THICK_M, FENCE_MAX_H = 0.15, 1.6
PROP_BURY_M = 0.5                     # Course Studio rule: solids reach 0.5 m under the ground, no deeper
PROP_ROUTE_CLEAR_M = 3.5              # no prop closer than this to the driving line (Course Studio route sweep +-3 m)
PROP_BOX_BUDGET = 2400                # closed boxes kept nearest the route first (35.7 MB pools at 4170 boxes > 32 MB cache)
FENCE_PIECE_M = 3.0                   # fence runs: abutting slabs of at most this length (long thin solids broke the BSP union)
FENCE_JOINT_M = 0.1                   # gap between abutting slabs of one run (0.02: near-coplanar BSP slivers, phantom cells)
PROP_ROAD_DROP_M = 15.0               # ... and road spots (phantom cells over the route) this far
PROP_DROP_M = 3.0                     # repair: props within this of a reported collision spot get no box
# Lighting: RCX vertex RGB is its baked light (slopes, tree shadows; shared corners, so smooth). MR draws it as the
# vertex colour of every layer, scaled so the 90th percentile of the ground reaches LIGHT_TOP. Course Studio's own bake
# lit each unwelded RCX face by its face normal: faceted ground, and the blend layer (unnormalised normal) differed.
LIGHT_TOP = 245
SOLID_PROPS = {'Fence'}    # thin walls: open soup, drawn only (BSP would leak solid); rock/wood/metal can be road
TEMPLATES = {'kenya': 'Turkey1', 'arctic': 'ItalyW1', 'manx': 'France2', 'scottish': 'Italy1', 'usa': 'Spain1',
             'welsh': 'France1'}


def to_mr(p):
    return (-p[0], -p[1], p[2])


def resample3(pts, step):
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    out, j, s = [], 0, 0.0
    while s <= cum[-1]:
        while j < len(cum) - 2 and cum[j + 1] < s:
            j += 1
        f = (s - cum[j]) / ((cum[j + 1] - cum[j]) or 1)
        out.append(tuple(pts[j][k] + (pts[j + 1][k] - pts[j][k]) * f for k in range(3)))
        s += step
    if math.dist(out[-1], pts[-1]) > 1.0:
        out.append(tuple(pts[-1]))
    return out, cum[-1]


def nearest(route, p):
    return min(range(len(route)), key=lambda i: (route[i][0] - p[0]) ** 2 + (route[i][2] - p[2]) ** 2)


def heading_deg(route, i):
    a, b = route[max(0, i - 1)], route[min(len(route) - 1, i + 1)]
    return math.degrees(math.atan2(b[0] - a[0], b[2] - a[2]))


def corridor_distance(line, cell=50.0):
    """XZ distance from a point to the nearest driving-line sample (grid hash; MR frame)."""
    grid = {}
    for p in line:
        grid.setdefault((int(p[0] // cell), int(p[2] // cell)), []).append(p)

    def dist(x, z, reach=2):
        gi, gj, best = int(x // cell), int(z // cell), float("inf")
        for di in range(-reach, reach + 1):
            for dj in range(-reach, reach + 1):
                for p in grid.get((gi + di, gj + dj), ()):
                    best = min(best, (p[0] - x) ** 2 + (p[2] - z) ** 2)
        return math.sqrt(best)
    return dist


def up_normal(a, b, c):
    u = [b[k] - a[k] for k in range(3)]; w = [c[k] - a[k] for k in range(3)]
    n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
    ln = math.sqrt(sum(x * x for x in n))
    return n[1] / ln if ln else 0.0


def build_project(stage_dir: Path, out_dir: Path, *, key: str | None = None, title: str | None = None, log=print,
                  corridor_m: float = 45.0, min_up: float = -0.05, barriers: bool = False, demote=(), drop_props=()):
    """demote: [(x, z, radius)] MR-frame discs whose terrain triangles become drawn-only (collision repair passes)."""
    stage_dir, out_dir = Path(stage_dir), Path(out_dir)
    name = stage_dir.name
    smap = read_map((stage_dir / f"{name}.map").read_bytes())
    cfg = read_config((stage_dir / "config.cfg").read_bytes())
    template = next((v for k, v in TEMPLATES.items() if name.lower().startswith(k)), "France1")
    key = key or safe_key("Rcx" + name.capitalize())
    project = new_project(key, title=title or name, template=template)
    project.materials.clear(); project.textures.clear()
    project.provenance.kind = "imported"
    project.provenance.notes.append(f"Rally Championship Xtreme (PC) Data/Levels/{name}.rcx")
    report = {"stage": name, "template": template, "groups": len(smap.groups)}

    # ---- geometry by role
    meshes = {}

    def mesh(role):
        if role not in meshes:
            real = ROLE_VISUAL if role == "blend" else role
            meshes[role] = Mesh(id=new_uid("mesh_"), name=f"RCX {role}", role=real, source="rcx:" + name, group=role)
            meshes[role].uv = []
            if role != ROLE_COLLISION:
                meshes[role].colors = []
            meshes[role]._index = {}
            meshes[role]._mat = {}
        return meshes[role]

    used_textures = {}
    blend_lows = set()
    tri_counts = {}
    near = corridor_distance([to_mr(p) for p in cfg.splines["driving line"]])
    line_mr = [to_mr(p) for p in cfg.splines["driving line"]]

    def on_line(ps, reach=8.0, rise=2.0):
        """A structure face the driving line runs on (a bridge deck, not its beams or the deck over an underpass)."""
        return any(math.dist((q[0], q[2]), (l[0], l[2])) <= reach and abs(q[1] - l[1]) <= rise
                   for q in ps for l in line_mr if abs(q[0] - l[0]) <= reach and abs(q[2] - l[2]) <= reach)

    # Collision corridor within the native pool budget: Fire Rock, 32 k terrain faces in 45 m, needed 20 MB of the
    # 32 MB model cache; Mountain Descent (41 MB) and Twin Bridges (46 MB) are denser. The corridor shrinks (not
    # below CORRIDOR_MIN_M) until the ground faces in it fit TERRAIN_FACE_BUDGET.
    unstack = [(x, z, -r) for x, z, r in demote if r < 0]
    protect = [(x, z) for x, z, r in demote if r == 0]
    demote = [d for d in demote if d[2] > 0]
    stacked_low = set()                        # ground faces under another ground face in an unstack disc
    stack_faces = []
    dists, lums = [], []
    for g, tri in smap.triangles():
        surface = SURFACES[g.surface] if g.surface < len(SURFACES) else 'Unknown'
        if g.texture < 0 or g.flags & OVERLAY_PASS_FLAG or surface == 'Water' or surface in DRAW_ONLY | SOLID_PROPS:
            continue
        ps = [to_mr(v[:3]) for v in tri]
        dists.append(near(sum(q[0] for q in ps) / 3, sum(q[2] for q in ps) / 3))
        lums.extend(max((v[3] >> 16) & 255, (v[3] >> 8) & 255, v[3] & 255) for v in tri)
        if unstack:
            cx, cz = sum(q[0] for q in ps) / 3, sum(q[2] for q in ps) / 3
            if any((cx - ux) ** 2 + (cz - uz) ** 2 <= ur * ur for ux, uz, ur in unstack):
                stack_faces.append(ps)
    def y_on(t, x, z):
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = t
        d = (z1 - z2) * (x0 - x2) + (x2 - x1) * (z0 - z2)
        if abs(d) < 1e-9:
            return None
        l0 = ((z1 - z2) * (x - x2) + (x2 - x1) * (z - z2)) / d
        l1 = ((z2 - z0) * (x - x2) + (x0 - x2) * (z - z2)) / d
        l2 = 1 - l0 - l1
        return l0 * y0 + l1 * y1 + l2 * y2 if min(l0, l1, l2) >= -1e-6 else None
    for t in stack_faces:
        cx, cy, cz = (sum(q[k] for q in t) / 3 for k in range(3))
        for o in stack_faces:
            if o is not t:
                y = y_on(o, cx, cz)
                if y is not None and y > cy + 0.05:
                    stacked_low.add(tuple(round(c, 3) for c in (cx, cy, cz)))
                    break
    report["unstacked"] = len(stacked_low)
    dists.sort()
    lums.sort()
    light_scale = LIGHT_TOP / max(1, lums[int(len(lums) * 0.9)] if lums else 128)
    report["light_scale"] = round(light_scale, 3)

    def rgb_of(v):
        c = v[3]
        return tuple(min(255, int(((c >> sh) & 255) * light_scale)) for sh in (16, 8, 0))
    if len(dists) > TERRAIN_FACE_BUDGET and dists[TERRAIN_FACE_BUDGET] < corridor_m:
        corridor_m = max(CORRIDOR_MIN_M, dists[TERRAIN_FACE_BUDGET])
    report["corridor_m"] = round(corridor_m, 1)
    drawn = set()
    hull_tris, fence_tris, struct_tris = [], [], []            # MR-frame props for the collision boxes (after the ground exists)
    for g, tri in smap.triangles():
        surface = SURFACES[g.surface] if g.surface < len(SURFACES) else 'Unknown'
        tex_index, blend_index = g.texture, -1
        if g.texture >= 0 and g.texture2 >= 0:
            alphas = [v[3] >> 24 for v in tri]
            if min(alphas) >= 250:
                tex_index = g.texture2            # fully texture2: one opaque layer
            elif max(alphas) > 5:
                blend_index = g.texture2          # mixed: texture opaque + texture2 blended by the vertex alpha
        if g.texture < 0 or (surface == 'Unknown' and g.flags & OVERLAY_PASS_FLAG):
            # untextured 0x2404 and textured 0x2506 / 0x2406 groups of the Unknown surface: RCX collision hulls
            # (tree pyramids, woodpile boxes, telegraph poles, advert boxes)
            hull_tris.append([to_mr(v[:3]) for v in tri])
        elif not g.flags & OVERLAY_PASS_FLAG and surface == "Fence":
            fence_tris.append([to_mr(v[:3]) for v in tri])
        if g.texture >= 0:
            # Render flag 0x400 marks groups RCX does not draw as plain geometry: the invisible barriers (0x2404,
            # untextured) and the envmap reflection pass over buildings (0x2406, envmap.tex on the same faces as
            # the house texture: as a second opaque layer it flickered black / white in MR, owner test 2026-11-16).
            if g.flags & OVERLAY_PASS_FLAG:
                tri_counts["dropped_overlay_pass"] = tri_counts.get("dropped_overlay_pass", 0) + 1
                continue
            k = [tuple(round(c, 3) for c in v[:3]) for v in tri]
            k = min(tuple(k[i:] + k[:i]) for i in range(3))     # same face, same winding: drawn once
            if k in drawn:
                tri_counts["dropped_duplicate"] = tri_counts.get("dropped_duplicate", 0) + 1
                continue
            drawn.add(k)
        if g.texture < 0:
            if not barriers:
                tri_counts["dropped_barrier"] = tri_counts.get("dropped_barrier", 0) + 1
                continue
            role = ROLE_COLLISION
        elif surface == 'Water':
            role = ROLE_WATER
        elif surface in DRAW_ONLY or surface in SOLID_PROPS or any(k in smap.textures[tex_index].lower() for k in DRAW_ONLY_TEXTURES):
            role = ROLE_VISUAL
        else:
            ps = [to_mr(v[:3]) for v in tri]
            cx, cz = sum(q[0] for q in ps) / 3, sum(q[2] for q in ps) / 3
            up = up_normal(*ps)
            solid = (up >= min_up and near(cx, cz) <= corridor_m
                     and not (surface in STRUCTURES and (up < 0.7 or not on_line(ps)))
                     and (not any((cx - dx) ** 2 + (cz - dz) ** 2 <= dr * dr for dx, dz, dr in demote)
                          or any(y_on(ps, px, pz) is not None for px, pz in protect))
                     and not (stacked_low and tuple(round(c, 3) for c in
                                                    (cx, sum(q[1] for q in ps) / 3, cz)) in stacked_low))
            role = ROLE_TERRAIN if solid else ROLE_VISUAL
        if role == ROLE_VISUAL and surface in STRUCTURES:
            struct_tris.append([to_mr(v[:3]) for v in tri])   # woodpiles, sheds, bridge piers: solid in RCX
        m = mesh(role)
        tex = smap.textures[tex_index] if tex_index >= 0 else None
        mr_surface = SURFACE_MR.get(surface, 'harddirt') if role in (ROLE_TERRAIN, ROLE_WATER) else None
        if role == ROLE_VISUAL and g.surface < len(SURFACES) and surface not in DRAW_ONLY | SOLID_PROPS | STRUCTURES                 and not any(k in (tex or "").lower() for k in DRAW_ONLY_TEXTURES):
            mr_surface = "far"                 # ground outside the collision corridor: ground shader, no surface
        mkey = (tex, mr_surface)
        if mkey not in m._mat:
            m._mat[mkey] = len(m.materials)
            m.materials.append(mkey)          # replaced by the material key below
            if tex:
                used_textures[tex.lower()] = tex
        base = len(m.positions) // 3
        for v in tri:
            m.positions.extend(to_mr(v[:3]))
            m.uv.extend((v[4], 1.0 - v[5]))
            if m.colors is not None:
                m.colors.extend(rgb_of(v) + (255,))
        m.triangles.extend((base, base + 1, base + 2))
        m.tri_material.append(m._mat[mkey])
        tri_counts[role] = tri_counts.get(role, 0) + 1
        if blend_index >= 0:
            # second layer: same corners BLEND_LIFT_M higher, texture2, vertex alpha = RCX alpha; RGB = the bake
            # Course Studio gives the opaque layer (unwelded corners: the face normal), so both layers match
            bm = mesh("blend")
            btex = smap.textures[blend_index]
            # its own texture: a horizontally mirrored copy sampled at -u (identical look, distinct texture hash), so
            # Atmosphere can give the blended layer its own lighting record (blended draws need category 3 / 4 with
            # AlphaTest; the opaque ground under it is terrain / road)
            bkey = (btex + OVERLAY_SUFFIX, "blend")
            if bkey not in bm._mat:
                bm._mat[bkey] = len(bm.materials)
                bm.materials.append(bkey)
                used_textures[btex.lower()] = btex
                blend_lows.add(btex.lower())
            pts = [to_mr(v[:3]) for v in tri]
            bb = len(bm.positions) // 3
            for v, q in zip(tri, pts):
                bm.positions.extend((q[0], q[1] + BLEND_LIFT_M, q[2]))
                bm.uv.extend((-v[4], 1.0 - v[5]))
                bm.colors.extend(rgb_of(v) + (v[3] >> 24,))
            bm.triangles.extend((bb, bb + 1, bb + 2))
            bm.tri_material.append(bm._mat[bkey])
            tri_counts["blend_layer"] = tri_counts.get("blend_layer", 0) + 1
        if role == ROLE_TERRAIN and surface in STRUCTURES:
            # deck slab: every deck top face gets its own downward face DECK_SLAB_M lower (the RCX underside, drawn
            # only, is narrower than the top: the overhanging deck edges had no support under them)
            for v in reversed(tri):
                x, y, z = to_mr(v[:3])
                m.positions.extend((x, y - DECK_SLAB_M, z))
                m.uv.extend((v[4], 1.0 - v[5]))
                m.colors.extend(rgb_of(v) + (255,))
            m.triangles.extend((base + 3, base + 4, base + 5))
            m.tri_material.append(m._mat[mkey])
            tri_counts["deck_slab"] = tri_counts.get("deck_slab", 0) + 1
    report["triangles"] = tri_counts

    # ---- textures (shared PNGs; halved until the model-cache budget holds)
    decoded = {}
    for low, tex in used_textures.items():
        path = stage_dir / tex
        # .tan = texture animation (manx3 lake0000.tan lists lake0000..0031.TEX): its first frame, static for now
        want = low.rsplit(".", 1)[0] + ".tex" if low.endswith(".tan") else low
        if not path.is_file() or low.endswith(".tan"):
            alt = [p for p in stage_dir.iterdir() if p.name.lower() == want]
            path = alt[0] if alt else None
        if path is None:
            log(f"  missing texture {tex}")
            continue
        d = decode_tex(path.read_bytes())
        decoded[low] = [d["width"], d["height"], d["rgba"]]
    for low in blend_lows:
        if low in decoded:
            w, h, rgba = decoded[low]
            rgba = bytes(rgba)
            decoded[low + OVERLAY_SUFFIX] = [w, h, b"".join(
                b"".join(rgba[(y * w + x) * 4:(y * w + x) * 4 + 4] for x in range(w - 1, -1, -1)) for y in range(h))]

    def budget():
        return sum(int(w * h * 4 * 4 / 3) for w, h, _ in decoded.values())
    halvings = 0
    while budget() > TEXTURE_BUDGET_BYTES * 0.9:
        big = max(decoded.values(), key=lambda t: t[0] * t[1])
        w, h, rgba = big
        big[:] = [max(1, w // 2), max(1, h // 2), box_mean(w, h, rgba, max(1, w // 2), max(1, h // 2))]
        halvings += 1
    report["texture_halvings"] = halvings
    tex_keys = {}
    for low, (w, h, rgba) in decoded.items():
        base_low = low.removesuffix(OVERLAY_SUFFIX)
        tkey = safe_key("rcx_" + base_low.rsplit(".", 1)[0]).lower()[:40] + ("_ovl" if low != base_low else "") + "-tga"
        alpha = any(a < 250 for a in rgba[3::4])
        write_png(out_dir / f"textures/{tkey}.png", w, h, rgba)
        project.textures[tkey] = Texture(key=tkey, source=f"textures/{tkey}.png", width=w, height=h, has_alpha=alpha)
        tex_keys[low] = (tkey, alpha)

    # ---- materials
    for role, m in meshes.items():
        keys = []
        for tex, surf in m.materials:
            t = tex_keys.get(tex.lower()) if tex else None
            if role == ROLE_COLLISION or t is None:
                mk = "rcx_collision" if role == ROLE_COLLISION else "rcx_plain"
                if mk not in project.materials:
                    project.materials[mk] = Material(mk, "RCX " + mk, shader="object", surface=None, noise=False)
            else:
                tkey, alpha = t
                mk = f"rcx_{role[0]}_{tkey}" + (f"_{surf}" if surf else "")
                if mk not in project.materials:
                    if surf == "blend":
                        project.materials[mk] = Material(mk, "RCX blend layer", shader="ground", surface=None,
                                                         textures=[tkey, None, None], noise=False, alpha="blend")
                    elif role == ROLE_WATER:
                        # plain blended ground, not Course Studio's water shader: its second (reflection) stage
                        # missed the PC-water contract and Atmosphere dropped the draw unlit (day-bright at
                        # night); RCX water is a plain blended texture anyway. Surface stays water (ROLE_WATER).
                        project.materials[mk] = Material(mk, "RCX water", shader="ground", surface="water",
                                                         textures=[tkey, None, None], noise=False, alpha="blend")
                    elif role == ROLE_TERRAIN:
                        # noise=False: Atmosphere would light opaque noise ground as "automatic ground" but leave the
                        # blend layers, steep batches (< 75 % faces up), trees and objects native; mixed lit / native
                        # ground showed as patches (owner 2026-11-16). RCX courses stay native until they get a
                        # lighting package with explicit roles.
                        project.materials[mk] = Material(mk, "RCX " + (surf or ""), shader="ground", surface=surf,
                                                         textures=[tkey, None, None], noise=False,
                                                         alpha="cutout" if alpha else "opaque")
                    elif surf == "far":
                        project.materials[mk] = Material(mk, "RCX far ground", shader="ground", surface=None,
                                                         textures=[tkey, None, None], noise=False,
                                                         alpha="cutout" if alpha else "opaque")
                    else:
                        project.materials[mk] = Material(mk, "RCX object", shader="tree" if alpha else "object",
                                                         surface=None, textures=[tkey, None, None], noise=False,
                                                         alpha="cutout" if alpha else "opaque")
            keys.append(mk)
        # merge duplicate material keys
        uniq, remap = [], {}
        for i, k in enumerate(keys):
            if k not in uniq:
                uniq.append(k)
            remap[i] = uniq.index(k)
        m.materials = uniq
        m.tri_material = [remap[i] for i in m.tri_material]
        del m._index, m._mat
        project.meshes.append(m)

    # ---- Atmosphere: smooth ground normals and explicit lighting roles
    # The lighting package takes its normals from the DX vertex normals; Course Studio would give every unwelded RCX
    # face its own (faceted light). Ground faces (terrain, far ground, blend layer) get area-weighted normals welded
    # by position across meshes; objects keep face normals.
    def is_ground(role, mk):
        return role in (ROLE_TERRAIN, "blend") or mk.endswith("_far")
    acc = {}
    CREASE_COS = 0.5                          # weld only faces within 60 deg (culvert pipe walls kept their own)

    def wkey(q, lift):
        return (round(q[0], 2), round(q[1] - lift, 2), round(q[2], 2))
    for role, m in meshes.items():
        if role == ROLE_COLLISION:
            continue
        lift = BLEND_LIFT_M if role == "blend" else 0.0
        for t in range(len(m.triangles) // 3):
            if not is_ground(role, m.materials[m.tri_material[t]]):
                continue
            q = [tuple(m.positions[3 * m.triangles[3 * t + k] + c] for c in range(3)) for k in range(3)]
            u = [q[1][c] - q[0][c] for c in range(3)]; w = [q[2][c] - q[0][c] for c in range(3)]
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            for p in q:
                acc.setdefault(wkey(p, lift), []).append(n)

    def unit(v):
        ln = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        return (v[0] / ln, v[1] / ln, v[2] / ln) if ln > 1e-12 else (0.0, 1.0, 0.0)
    for role, m in meshes.items():
        if role == ROLE_COLLISION:
            continue
        lift = BLEND_LIFT_M if role == "blend" else 0.0
        m.normals = []
        for t in range(len(m.triangles) // 3):
            q = [tuple(m.positions[3 * m.triangles[3 * t + k] + c] for c in range(3)) for k in range(3)]
            if is_ground(role, m.materials[m.tri_material[t]]):
                u = [q[1][c] - q[0][c] for c in range(3)]; w = [q[2][c] - q[0][c] for c in range(3)]
                own = unit((u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]))
                for p in q:
                    s = [0.0, 0.0, 0.0]
                    for n in acc[wkey(p, lift)]:
                        un = unit(n)
                        if un[0] * own[0] + un[1] * own[1] + un[2] * own[2] >= CREASE_COS:
                            s[0] += n[0]; s[1] += n[1]; s[2] += n[2]
                    m.normals.extend(unit(s) if any(s) else own)
            else:
                u = [q[1][c] - q[0][c] for c in range(3)]; w = [q[2][c] - q[0][c] for c in range(3)]
                n = unit((u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]))
                m.normals.extend(n * 3)
    # roles by texture label (course_lighting.material_role): road / terrain ground, vegetation for cutout objects,
    # static for opaque objects. "static_alpha" (rcx_lighting.py: static + AlphaTest) for the blend layer, cutout
    # ground and water: blended / alpha-tested draws are lit only as category 3 or 4 with AlphaTest, and category 3
    # (vegetation) gets no normal hints and turns its normals to the sun / moon: the blend layer lit apart from the
    # ground under it, hard edges in the headlights (owner 2026-11-17); cutout ground and water stayed native.
    rank = {"road": 0, "terrain": 1, "static_alpha": 2, "static": 3, "vegetation": 4, "exclude": 5}
    roles = {}
    for mk, mat in project.materials.items():
        if not mat.textures or not mat.textures[0]:
            continue
        label = mat.textures[0]
        if mat.shader == "water" or mat.alpha == "blend" or (mat.shader == "ground" and mat.alpha == "cutout"):
            role = "static_alpha"
        elif mat.shader == "ground":
            role = "road" if mat.surface in ("tarmac", "gravel") else "terrain"
        else:
            role = "vegetation" if mat.alpha == "cutout" else "static"
        if label not in roles or rank[role] < rank[roles[label]]:
            roles[label] = role
    report["lighting_roles"] = roles

    # ---- ground queries on the drivable surface (Course Studio height field, MR frame)
    from master_rallye.studio.collision import HeightField, terrain_triangles
    hf = HeightField(terrain_triangles(project))

    def ground(x, z, hint=None):
        hs = hf.heights(x, z)
        if not hs:
            return hint if hint is not None else 0.0
        return min(hs, key=lambda h: abs(h - hint)) if hint is not None else max(hs)

    # ---- solid props: RCX hulls (trees, woodpiles, buildings) and Fence panels near the driving line
    from master_rallye.studio.collision import box_proxy
    dense, _len = resample3(line_mr, 2.0)
    near_dense = corridor_distance(dense, cell=10.0)
    candidates = []                                   # (route distance, kind, cx, cz, ux, uz, half_len, half_wid, y0, y1)

    def obb(points):
        """Minimum-area oriented rectangle of xz points: (cx, cz, ux, uz, half_len, half_wid), u along the length."""
        pts = sorted(set((round(q[0], 3), round(q[2], 3)) for q in points))
        if len(pts) < 3:
            (x0, z0), (x1, z1) = pts[0], pts[-1]
            ln = math.dist(pts[0], pts[-1]) or 1e-3
            return ((x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / ln, (z1 - z0) / ln, ln / 2, 0.0)

        def cross(o, a1, b1):
            return (a1[0] - o[0]) * (b1[1] - o[1]) - (a1[1] - o[1]) * (b1[0] - o[0])
        lower, upper = [], []
        for q in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
                lower.pop()
            lower.append(q)
        for q in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
                upper.pop()
            upper.append(q)
        hull = lower[:-1] + upper[:-1]
        best = None
        for i in range(len(hull)):
            (x0, z0), (x1, z1) = hull[i], hull[(i + 1) % len(hull)]
            ln = math.hypot(x1 - x0, z1 - z0)
            if ln < 1e-6:
                continue
            ux, uz = (x1 - x0) / ln, (z1 - z0) / ln
            us = [q[0] * ux + q[1] * uz for q in hull]
            vs = [-q[0] * uz + q[1] * ux for q in hull]
            area = (max(us) - min(us)) * (max(vs) - min(vs))
            if best is None or area < best[0]:
                mu, mv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
                best = (area, (mu * ux - mv * uz, mu * uz + mv * ux, ux, uz,
                               (max(us) - min(us)) / 2, (max(vs) - min(vs)) / 2))
        if best is None:
            return obb(pts[:1] + pts[-1:])
        o = best[1]
        return o if o[4] >= o[5] else (o[0], o[1], -o[3], o[2], o[5], o[4])

    def corners(c):
        _d, _k, cx, cz, ux, uz, hl, hw = c[:8]
        return [(cx + sl * hl * ux - sw * hw * uz, cz + sl * hl * uz + sw * hw * ux)
                for sl, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    def route_gap(cx, cz, ux, uz, hl, hw):
        # nearest driving-line distance over the rectangle outline (every <= 1 m along the long edges)
        steps = max(1, int(math.ceil(2 * hl)))
        pts = [(cx + (-hl + 2 * hl * i / steps) * ux - sw * hw * uz, cz + (-hl + 2 * hl * i / steps) * uz + sw * hw * ux)
               for i in range(steps + 1) for sw in (-1, 1)]
        return min(near_dense(x, z) for x, z in pts + [(cx, cz)])

    def add(kind, cx, cz, ux, uz, hl, hw, y0, y1):
        if near(cx, cz) - hl > PROP_REACH_M or route_gap(cx, cz, ux, uz, hl, hw) <= PROP_ROUTE_CLEAR_M:
            return
        candidates.append((near(cx, cz), kind, cx, cz, ux, uz, hl, hw, y0, y1))

    # hulls: connected components of the untextured soup (shared corners)
    parent = {}

    def find(k):
        while parent.setdefault(k, k) != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    # Wood / Metal faces off the driving line (woodpiles, sheds, piers) are solid in RCX without a hull: their own
    # components, keyed apart from the hulls ("s" prefix) so a woodpile and its neighbouring hull stay two boxes
    for tag, tris in (("h", hull_tris), ("s", struct_tris)):
        for t in tris:
            ks = [(tag,) + tuple(round(c, 2) for c in q) for q in t]
            for k in ks[1:]:
                parent[find(ks[0])] = find(k)
    components = {}
    for tag, tris in (("h", hull_tris), ("s", struct_tris)):
        for t in tris:
            components.setdefault(find((tag,) + tuple(round(c, 2) for c in t[0])), []).append(t)
    hull_slabs = []
    for comp in components.values():
        P = [q for t in comp for q in t]
        cx, cz, ux, uz, hl, hw = obb(P)
        y0, y1 = min(q[1] for q in P), max(q[1] for q in P)
        if 2 * hl <= HULL_BOX_MAX_M and hw >= 0.05:
            add("hull", cx, cz, ux, uz, max(hl, 0.25), max(hw, 0.25), y0, min(y1, y0 + HULL_MAX_H))
        else:
            hull_slabs += [t for t in comp if abs(up_normal(*t)) <= 0.35]   # long walls / buildings: their faces
    # fence panels (and big hulls): vertical faces -> xz segments, de-duplicated (both sides, rails at two heights)
    segs = {}
    for t in fence_tris + hull_slabs:
        if abs(up_normal(*t)) > 0.35:
            continue
        a1, b1 = max(((p1, q1) for i, p1 in enumerate(t) for q1 in t[i + 1:]),
                     key=lambda pq: math.dist((pq[0][0], pq[0][2]), (pq[1][0], pq[1][2])))
        if math.dist((a1[0], a1[2]), (b1[0], b1[2])) < 0.3:
            continue
        ka, kb = (round(a1[0] * 4), round(a1[2] * 4)), (round(b1[0] * 4), round(b1[2] * 4))
        key = (ka, kb) if ka <= kb else (kb, ka)
        lo, hi = min(q[1] for q in t), max(q[1] for q in t)
        if key in segs:
            s0 = segs[key]
            segs[key] = (s0[0], s0[1], min(s0[2], lo), max(s0[3], hi))
        else:
            segs[key] = (a1, b1, lo, hi)
    for a1, b1, lo, hi in segs.values():
        ln = math.dist((a1[0], a1[2]), (b1[0], b1[2]))
        ux, uz = (b1[0] - a1[0]) / ln, (b1[2] - a1[2]) / ln
        run = ln - 2 * FENCE_THICK_M                  # ends stay clear of the neighbouring segment at the joints
        if run < 0.2:
            continue
        pieces = max(1, math.ceil(run / FENCE_PIECE_M))
        piece = run / pieces
        for i in range(pieces):
            f = FENCE_THICK_M + piece * (i + 0.5)
            add("fence", a1[0] + ux * f, a1[2] + uz * f, ux, uz, piece / 2 - FENCE_JOINT_M / 2, FENCE_THICK_M / 2, lo, hi)

    # nearest first, no overlaps (overlapping closed solids left unexplained BSP cells), within the pool budget
    def separated(c1, c2):
        for c in (c1, c2):
            for ax, az in ((c[4], c[5]), (-c[5], c[4])):
                p1 = [x * ax + z * az for x, z in corners(c1)]
                p2 = [x * ax + z * az for x, z in corners(c2)]
                if max(p1) <= min(p2) or max(p2) <= min(p1):
                    return True
        return False

    cells, boxes, prop_boxes = {}, [], []
    kinds = {"hull": 0, "fence": 0}
    for c in sorted(candidates, key=lambda c: c[0]):
        if len(boxes) >= PROP_BOX_BUDGET:
            break
        _d, kind, cx, cz, ux, uz, hl, hw, y0, y1 = c
        r = math.hypot(hl, hw)
        if any(math.hypot(cx - dx, cz - dz) - r <= dr for dx, dz, dr in drop_props):
            continue
        k0 = (int(cx // 8), int(cz // 8))
        others = [o for i in (-2, -1, 0, 1, 2) for j in (-2, -1, 0, 1, 2) for o in cells.get((k0[0] + i, k0[1] + j), ())]
        if any(math.hypot(cx - o[2], cz - o[3]) < r + math.hypot(o[6], o[7]) and not separated(c, o) for o in others):
            continue
        g0 = ground(cx, cz, y0)
        bottom = min(y0, g0) - PROP_BURY_M
        top = y1 if kind == "hull" else min(y1, g0 + FENCE_MAX_H)
        if top - max(bottom, g0) < 0.3:
            top = max(bottom, g0) + 0.3 if kind == "hull" else g0 + max(0.4, min(FENCE_MAX_H, y1 - g0))
        cells.setdefault(k0, []).append(c)
        prop_boxes.append((round(cx, 2), round(cz, 2), round(r, 2)))
        kinds[kind] += 1
        boxes.append(box_proxy((cx - hl, bottom, cz - hw), (cx + hl, top, cz + hw),
                               yaw=math.degrees(math.atan2(-uz, ux)), center=(cx, cz)))
    if boxes:
        props = Mesh(id=new_uid("mesh_"), name="RCX prop collision", role=ROLE_COLLISION, source="rcx:" + name,
                     group="Props", materials=["rcx_prop_collision"])
        project.materials["rcx_prop_collision"] = Material("rcx_prop_collision", "RCX prop collision", shader="object",
                                                           surface="rock", noise=False)
        for box in boxes:
            for tri3 in box:
                b0 = len(props.positions) // 3
                for q in tri3:
                    props.positions.extend(q)
                props.triangles.extend((b0, b0 + 1, b0 + 2))
                props.tri_material.append(0)
        project.meshes.append(props)
    report["solid_props"] = {"hull_components": len(components), "fence_segments": len(segs),
                             "candidates": len(candidates), "boxes": len(boxes), **kinds, "dropped_spots": len(drop_props)}
    report["prop_boxes"] = prop_boxes

    # ---- route
    line = [to_mr(p) for p in cfg.splines["driving line"]]
    start_pos = to_mr(cfg.start[0])
    gates = [(n, to_mr(a), to_mr(b)) for n, a, b in sorted(cfg.checkpoints, key=lambda c: c[0])]
    if math.dist(line[0], start_pos) > math.dist(line[-1], start_pos):
        line.reverse()
    route, total = resample3(line, ROUTE_STEP_M)
    i0 = nearest(route, start_pos)
    finish_gate = gates[-1]
    fmid = tuple((finish_gate[1][k] + finish_gate[2][k]) / 2 for k in range(3))
    i1 = nearest(route, fmid)
    route = route[i0:min(len(route), i1 + 3)]           # two samples past the gate: the finish is not the route end
    # finish = the gate centre projected on the route (route[-2] was a 10 m sample, up to 15 m before the gate)
    best = None
    for i in range(len(route) - 1):
        a, b = route[i], route[i + 1]
        dx, dz = b[0] - a[0], b[2] - a[2]
        f = max(0.0, min(1.0, ((fmid[0] - a[0]) * dx + (fmid[2] - a[2]) * dz) / ((dx * dx + dz * dz) or 1)))
        q = (a[0] + dx * f, a[1] + (b[1] - a[1]) * f, a[2] + dz * f)
        d = math.hypot(q[0] - fmid[0], q[2] - fmid[2])
        if best is None or d < best[0]:
            best = (d, i, q)
    finish_i, finish_pt = best[1], best[2]
    route = [(x, ground(x, z, y) + 0.3, z) for x, y, z in route]
    for _ in range(3):                                   # chords stay above the surface over crests
        lifted = False
        for i in range(len(route) - 1):
            a, b = route[i], route[i + 1]
            deficit = 0.0
            for k in range(1, 10):
                f = k / 10
                x, z = a[0] + (b[0] - a[0]) * f, a[2] + (b[2] - a[2]) * f
                y = a[1] + (b[1] - a[1]) * f
                deficit = max(deficit, ground(x, z, y) + 0.3 - y)
            if deficit > 0.01:
                route[i] = (a[0], a[1] + deficit, a[2]); route[i + 1] = (b[0], b[1] + deficit, b[2]); lifted = True
        if not lifted:
            break
    project.route.points = route
    project.route.spacing = ROUTE_STEP_M
    project.start = start_area(route, heading_deg(route, 1), lambda x, z: ground(x, z, route[1][1]))
    finish_pt = (finish_pt[0], ground(finish_pt[0], finish_pt[2], finish_pt[1]), finish_pt[2])
    project.finish = Area(center=finish_pt, heading=heading_deg(route, finish_i), width=36.0, depth=14.0)

    # ---- splits: the RCX gates between start and finish nearest 1/4, 1/2, 3/4 of the route
    inner = []
    for n, a, b in gates[1:-1]:
        mid = tuple((a[k] + b[k]) / 2 for k in range(3))
        inner.append((nearest(route, mid), n, a, b, mid))
    inner.sort()
    chosen = []
    for f in [(i + 1) / (SPLITS + 1) for i in range(SPLITS)]:
        cand = [g for g in inner if g not in chosen]
        if cand:
            chosen.append(min(cand, key=lambda g: abs(g[0] - f * len(route))))
    chosen.sort()
    for n, (k, gname, a, b, mid) in enumerate(chosen):
        next_k = chosen[n + 1][0] if n + 1 < len(chosen) else len(route) - 1
        extra = round(min(300.0, 25.0 + (next_k - k) * ROUTE_STEP_M / 14.0), 0)
        width = min(max(math.dist(a, b) / 2 + 6.0, 18.0), 40.0)
        centre = (route[k][0], route[k][1] - 0.3, route[k][2])
        project.checkpoints.append(Checkpoint(uid=new_uid("cp_"), center=centre, radius=width, extra_time=extra,
                                              heading=heading_deg(route, k), board_spacing=min(width * 2, 60.0),
                                              # RCX gates are in the course model; Course Studio boards stood off the
                                              # road, above the ground and turned 90 deg (owner 2026-11-17, Evo too)
                                              name=gname, boards=False))
    first_len = (chosen[0][0] if chosen else len(route)) * ROUTE_STEP_M
    project.environment.time_to_first_checkpoint = round(min(300.0, 30.0 + first_len / 14.0), 0)
    project.limits.mode = "manual"
    project.limits.inner, project.limits.outer = 45.0, 75.0
    project.limits.lists, report["limits"] = safe_limits(project, 45.0, 75.0)
    project.build.pacenotes = "auto"
    report.update(route_m=round((len(route) - 1) * ROUTE_STEP_M), driving_line_m=round(total), gates=len(gates),
                  splits=[c[1] for c in chosen], texture_bytes=texture_bytes(project, out_dir))
    project.extras["rcx"] = report
    return project


def main(argv=None):
    import argparse
    import time
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", type=Path, required=True, help="extracted Levels/<stage>.rcx folder")
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--resource-root", type=Path, required=True, help="retail data tree (Data.sma_unpacked)")
    ap.add_argument("--title")
    ap.add_argument("--project-only", action="store_true")
    ap.add_argument("--passes", type=int, default=7, help="collision repair passes (off-road holes -> drawn only)")
    ap.add_argument("--keep-m", type=float, default=10.0, help="never demote terrain this close to the driving line")
    ap.add_argument("--corridor", type=float, default=45.0, help="collision corridor around the driving line, m")
    ap.add_argument("--min-up", type=float, default=-0.05, help="solid ground faces need normal Y >= this (overhangs drawn only)")
    ap.add_argument("--barriers", action="store_true", help="keep the untextured RCX barrier walls as collision")
    ap.add_argument("--seed", type=Path, help="start from a previous build-<stage>.json (its repair discs and dropped props)")
    ap.add_argument("--authoring-order", action="store_true",
                    help="chunk draw records in authoring order (before RCX-PERF1: records spanned the whole stage)")
    a = ap.parse_args(argv)
    from master_rallye.studio.model import save_project
    from master_rallye.studio.build import build_course
    import object_bsp
    import render_batches
    render_batches.install(spatial=not a.authoring_order)   # RCX-PERF1: compact records for view culling
    t0 = time.time()
    pdir = a.work / "projects" / a.stage.name
    demote, drop_props, history = [], [], []
    if a.seed:
        prev = json.loads(a.seed.read_text())
        demote = [tuple(d) for d in prev.get("demoted", [])]
        drop_props = [tuple(d) for d in prev.get("dropped_props", [])]
    for npass in range(a.passes + 1):
        project = build_project(a.stage, pdir, title=a.title, corridor_m=a.corridor, min_up=a.min_up,
                                barriers=a.barriers, demote=demote, drop_props=drop_props)
        save_project(project, pdir)
        object_bsp.install(project)
        print(json.dumps(project.extras["rcx"]), flush=True)
        if a.project_only:
            return 0
        marks = {}

        def say(stage, fraction=None):
            if stage not in marks:
                marks[stage] = round(time.time() - t0, 1)
                print(f"  [{stage}] t={marks[stage]}s", flush=True)
        result = build_course(project, project_dir=pdir, resource_root=a.resource_root, output=a.work / "builds",
                              progress=say)
        errors = [f.to_dict() for f in result.findings if f.severity == "error"]
        # dense line (2 m): route points are 10 m apart, a spot between two of them looked farther from the road
        # than it is and its repair disc removed road ground (Clashin Darroch x -86 z -1778)
        near = corridor_distance(resample3(project.route.points, 2.0)[0], cell=10.0)
        spots = [(e["position"][0], e["position"][2]) for e in errors
                 if e.get("position") and e["category"] == "collision"]
        # props first: a spot within PROP_DROP_M of a prop box drops the props there (solid union of thin boxes can
        # leave unexplained cells next to them); terrain is demoted only where no prop is near
        boxes_here = project.extras["rcx"].get("prop_boxes", [])
        prop_spots = [(x, z, PROP_DROP_M) for x, z in spots
                      if any(math.hypot(x - bx, z - bz) - bh <= PROP_DROP_M for bx, bz, bh in boxes_here)]
        # on the road no terrain may go: a phantom BSP cell there (set by boxes farther away) drops props up to
        # PROP_ROAD_DROP_M around it (Fire Rock x 374 z 629: nearest box 9.5 m)
        prop_spots += [(x, z, PROP_ROAD_DROP_M) for x, z in spots if near(x, z) <= NEAR_KEEP_M
                       and (x, z, PROP_ROAD_DROP_M) not in drop_props
                       and not any(math.hypot(x - bx, z - bz) - bh <= PROP_DROP_M for bx, bz, bh in boxes_here)
                       and any(math.hypot(x - bx, z - bz) - bh <= PROP_ROAD_DROP_M for bx, bz, bh in boxes_here)]
        if prop_spots:
            drop_props += prop_spots
            history.append({"pass": npass, "errors": len(errors), "spots": len(spots), "dropped_props_at": len(prop_spots)})
            print(f"  pass {npass}: ok={result.ok} errors={len(errors)} props dropped at {len(prop_spots)} spots", flush=True)
            continue
        fixable, radius = [(x, z) for x, z in spots if near(x, z) > a.keep_m], 4.0
        if not fixable:
            # second stage: spots beside the road (rock faces, verges 4-10 m out), smaller discs; the 4 m the
            # cars use around the line are never touched
            fixable, radius = [(x, z) for x, z in spots if near(x, z) > NEAR_KEEP_M and (x, z, 2.0) not in demote], 2.0
            if not fixable:
                # the same spots again after their 2 m discs: wider discs that still end NEAR_KEEP_M from the route
                fixable = [(x, z) for x, z in spots if near(x, z) - NEAR_KEEP_M > 2.0]
                radius = min(4.0, min((near(x, z) - NEAR_KEEP_M for x, z in fixable), default=2.0))
                if not fixable:
                    # last: verge spots 4.5-6 m out (stream banks with stacked ground layers): 1 m discs that end
                    # EDGE_KEEP_M from the route
                    fixable = [(x, z) for x, z in spots if near(x, z) - EDGE_KEEP_M >= 1.0 and (x, z, 1.0) not in demote]
                    radius = 1.0
                    if not fixable:
                        # on the road edge (fords: road, bed and bank stacked within 1 m): keep only the top ground
                        # layer solid in a disc (negative radius = unstack, see build_project)
                        fixable = [(x, z) for x, z in spots if (x, z, -UNSTACK_M) not in demote]
                        radius = -UNSTACK_M
                        if not fixable:
                            # still there: a hole the repair discs opened (cliff edge, BSP leaks solid into it):
                            # the ground face over the spot is solid again, whatever disc covers it (radius 0)
                            fixable = [(x, z) for x, z in spots if (x, z, 0.0) not in demote]
                            radius = 0.0
        history.append({"pass": npass, "errors": len(errors), "spots": len(spots), "demoted": len(fixable), "radius": radius})
        print(f"  pass {npass}: ok={result.ok} errors={len(errors)} spots fixed={len(fixable)}/{len(spots)} r={radius}", flush=True)
        if result.ok or not fixable:
            break
        demote += [(x, z, radius) for x, z in fixable]
    summary = {"ok": result.ok, "output": str(result.output), "stages": marks, "passes": history,
               "demoted": demote, "dropped_props": drop_props, "errors": errors[:40], "model_cache": result.report.get("model_cache")}
    (a.work / f"build-{a.stage.name}.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: summary[k] for k in ("ok", "output", "passes")}, indent=1, default=str))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
