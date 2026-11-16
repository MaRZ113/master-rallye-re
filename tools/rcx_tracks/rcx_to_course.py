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
OVERLAY_PASS_FLAG = 0x400             # .map group render flag: not drawn as plain geometry (see build_project)
DRAW_ONLY_TEXTURES = ('barrier', 'rail')  # bridge barriers and rails: open soup along the deck edges
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
                  corridor_m: float = 45.0, min_up: float = -0.05, barriers: bool = False, demote=()):
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
            meshes[role] = Mesh(id=new_uid("mesh_"), name=f"RCX {role}", role=role, source="rcx:" + name, group=role)
            meshes[role].uv = []
            meshes[role]._index = {}
            meshes[role]._mat = {}
        return meshes[role]

    used_textures = {}
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
    dists = []
    for g, tri in smap.triangles():
        surface = SURFACES[g.surface] if g.surface < len(SURFACES) else 'Unknown'
        if g.texture < 0 or g.flags & OVERLAY_PASS_FLAG or surface == 'Water' or surface in DRAW_ONLY | SOLID_PROPS:
            continue
        ps = [to_mr(v[:3]) for v in tri]
        dists.append(near(sum(q[0] for q in ps) / 3, sum(q[2] for q in ps) / 3))
    dists.sort()
    if len(dists) > TERRAIN_FACE_BUDGET and dists[TERRAIN_FACE_BUDGET] < corridor_m:
        corridor_m = max(CORRIDOR_MIN_M, dists[TERRAIN_FACE_BUDGET])
    report["corridor_m"] = round(corridor_m, 1)
    drawn = set()
    for g, tri in smap.triangles():
        surface = SURFACES[g.surface] if g.surface < len(SURFACES) else 'Unknown'
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
        elif surface in DRAW_ONLY or surface in SOLID_PROPS or any(k in smap.textures[g.texture].lower() for k in DRAW_ONLY_TEXTURES):
            role = ROLE_VISUAL
        else:
            ps = [to_mr(v[:3]) for v in tri]
            cx, cz = sum(q[0] for q in ps) / 3, sum(q[2] for q in ps) / 3
            up = up_normal(*ps)
            solid = (up >= min_up and near(cx, cz) <= corridor_m
                     and not (surface in STRUCTURES and (up < 0.7 or not on_line(ps)))
                     and not any((cx - dx) ** 2 + (cz - dz) ** 2 <= dr * dr for dx, dz, dr in demote))
            role = ROLE_TERRAIN if solid else ROLE_VISUAL
        m = mesh(role)
        tex = smap.textures[g.texture] if g.texture >= 0 else None
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
        m.triangles.extend((base, base + 1, base + 2))
        m.tri_material.append(m._mat[mkey])
        tri_counts[role] = tri_counts.get(role, 0) + 1
        if role == ROLE_TERRAIN and surface in STRUCTURES:
            # deck slab: every deck top face gets its own downward face DECK_SLAB_M lower (the RCX underside, drawn
            # only, is narrower than the top: the overhanging deck edges had no support under them)
            for v in reversed(tri):
                x, y, z = to_mr(v[:3])
                m.positions.extend((x, y - DECK_SLAB_M, z))
                m.uv.extend((v[4], 1.0 - v[5]))
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
        tkey = safe_key("rcx_" + low.rsplit(".", 1)[0]).lower()[:40] + "-tga"
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
                    if role == ROLE_WATER:
                        project.materials[mk] = Material(mk, "RCX water", shader="water", surface="water",
                                                         textures=[tkey, None, None], noise=False, alpha="blend")
                    elif role == ROLE_TERRAIN:
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

    # ---- ground queries on the drivable surface (Course Studio height field, MR frame)
    from master_rallye.studio.collision import HeightField, terrain_triangles
    hf = HeightField(terrain_triangles(project))

    def ground(x, z, hint=None):
        hs = hf.heights(x, z)
        if not hs:
            return hint if hint is not None else 0.0
        return min(hs, key=lambda h: abs(h - hint)) if hint is not None else max(hs)

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
    route = route[i0:i1 + 1]
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
    project.finish = Area(center=route[-2], heading=heading_deg(route, len(route) - 2), width=36.0, depth=14.0)

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
                                              name=gname, boards=True))
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
    a = ap.parse_args(argv)
    from master_rallye.studio.model import save_project
    from master_rallye.studio.build import build_course
    import object_bsp
    import render_batches
    render_batches.install()
    t0 = time.time()
    pdir = a.work / "projects" / a.stage.name
    demote, history = [], []
    for npass in range(a.passes + 1):
        project = build_project(a.stage, pdir, title=a.title, corridor_m=a.corridor, min_up=a.min_up,
                                barriers=a.barriers, demote=demote)
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
        near = corridor_distance(project.route.points)
        spots = [(e["position"][0], e["position"][2]) for e in errors
                 if e.get("position") and e["category"] == "collision"]
        fixable, radius = [(x, z) for x, z in spots if near(x, z) > a.keep_m], 4.0
        if not fixable:
            # second stage: spots beside the road (rock faces, verges 4-10 m out), smaller discs; the 4 m the
            # cars use around the line are never touched
            fixable, radius = [(x, z) for x, z in spots if near(x, z) > NEAR_KEEP_M and (x, z, 2.0) not in demote], 2.0
            if not fixable:
                # the same spots again after their 2 m discs: wider discs that still end NEAR_KEEP_M from the route
                fixable = [(x, z) for x, z in spots if near(x, z) - NEAR_KEEP_M > 2.0]
                radius = min(4.0, min((near(x, z) - NEAR_KEEP_M for x, z in fixable), default=2.0))
        history.append({"pass": npass, "errors": len(errors), "spots": len(spots), "demoted": len(fixable), "radius": radius})
        print(f"  pass {npass}: ok={result.ok} errors={len(errors)} spots fixed={len(fixable)}/{len(spots)} r={radius}", flush=True)
        if result.ok or not fixable:
            break
        demote += [(x, z, radius) for x, z in fixable]
    summary = {"ok": result.ok, "output": str(result.output), "stages": marks, "passes": history,
               "demoted": demote, "errors": errors[:40], "model_cache": result.report.get("model_cache")}
    (a.work / f"build-{a.stage.name}.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: summary[k] for k in ("ok", "output", "passes")}, indent=1, default=str))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
