"""4x4 Evolution 2 race -> Master Rallye Course Studio project (master_rallye.studio.CourseProject).

Universal for every Evo 2 race SIT (and the same TRI engine format family): nothing here is specific to one track.

Mapping (docs/evo2-tracks/EVO2_TRACKS.md):
  frame     Evo 2 is left-handed (TRK wheels: +X right, +Z front, +Y up); Master Rallye's world is right-handed (+X left:
            captured gameplay VIEW det = -1 with an LH projection, renderer menu-grass-fix1; vehicle SDK "MR +X left"). Every
            output point is mirrored X -> -X (feet -> metres) and every triangle is re-wound, so the layout is not mirrored.
  terrain   256x256 height grid, 32 ft cells -> metres. Cells near the race (corridor) are ROLE_TERRAIN (drawn, solid,
            surface database) with their own 64x64 Evo ground tile (baked shadow tile when SDW has one) packed into
            1024x1024 atlas pages; the rest of the map is ROLE_VISUAL with one baked overview texture (4 px / cell).
  surface   TEX terrain class (value // 100) -> MR Surface.xml row (MR_SURFACE).
  water     LVL waterHeight -> flat ROLE_WATER over cells that dip below it.
  objects   SIT boxes with SMF models: CCollide / CNonCollide drawn; CCollide collisionType 0 and CCollisionBox -> oriented
            box proxies, collisionType 1 (docks, bridges, ramps, cliffs) -> convex hull of the model (drivable top; the
            model itself as land polygons with overhangs inflated the layered BSP to millions of planes).
  race      start = SIT vehicle 1 (position, heading); AI route = SIT Course straights joined by Hermite arcs; gates =
            CCheckpoint boxes ordered along the route; circuit races end FINISH_GAP before the start line (one lap).
"""
from __future__ import annotations

import json
import math
import struct
import sys
import zlib
from pathlib import Path

from evo2_track import (FT, GRID, CELL_FT, MR_SURFACE, Track, load_texture, parse_smf, load_track)

from master_rallye.studio.model import (ROLE_COLLISION, ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER, Area, Checkpoint,
                                        CourseProject, Material, Mesh, Texture, new_uid, safe_key)
from master_rallye.studio.templates import new_project

TILE = 64                                    # largest ground tile; smaller when the corridor needs more tiles
TILE_CHOICES = (64, 48, 40, 32, 24)
GROUND_PAGES = 2                             # ground atlas page budget (Evo maps have ~1000 unique ground tiles)
PAD = 2
PAGE = 1024
OVERVIEW_PX = 2                              # per cell -> 512 for the 256-cell map
OBJECT_MAX_TILE = 128
# MR keeps course textures (A8R8G8B8 + full mip chain, D3D managed pool) in the model cache together with the course
# DX, collision pools and every car. Over budget the cache evicts and re-creates textures every frame (in-race
# 0x5589D0 CreateTexture storm, 100+ per frame in host-evo-tracks-01 on Pikes Peak). Stay well under it.
TEXTURE_BUDGET_BYTES = 24 << 20
FINISH_GAP_M = 150.0
ROUTE_STEP_M = 10.0


# ----------------------------------------------------------------------------------------------- small helpers
from PIL import Image


def write_png(path: Path, w: int, h: int, rgba):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.frombytes("RGBA", (w, h), bytes(rgba)).save(path, compress_level=6)


def resize_nearest(w, h, rgba, nw, nh):
    return Image.frombytes("RGBA", (w, h), bytes(rgba)).resize((nw, nh), Image.NEAREST).tobytes()


def box_mean(w, h, rgba, nw, nh):
    """Area-average downscale (for the overview texture)."""
    return Image.frombytes("RGBA", (w, h), bytes(rgba)).resize((nw, nh), Image.BOX).tobytes()


def padded(w, h, rgba, pad):
    """Tile with its edge pixels repeated `pad` times on every side (atlas gutter against mip/filter bleeding)."""
    tile = Image.frombytes("RGBA", (w, h), bytes(rgba))
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad))
    out.paste(tile, (pad, pad))
    out.paste(tile.crop((0, 0, w, 1)).resize((w, pad)), (pad, 0))
    out.paste(tile.crop((0, h - 1, w, h)).resize((w, pad)), (pad, h + pad))
    left = out.crop((pad, 0, pad + 1, h + 2 * pad)).resize((pad, h + 2 * pad))
    right = out.crop((w + pad - 1, 0, w + pad, h + 2 * pad)).resize((pad, h + 2 * pad))
    out.paste(left, (0, 0))
    out.paste(right, (w + pad, 0))
    return out


def euler_pbh(p, b, h):
    """CMatrix::genMatrix (4x4.elf) with v0=pitch, v1=heading, v2=bank; world = M . body (row-major 3x3)."""
    sp, cp = math.sin(p), math.cos(p)
    sh, ch = math.sin(h), math.cos(h)
    sb, cb = math.sin(b), math.cos(b)
    return (ch * cb + sb * sh * sp, -ch * sb + cb * sh * sp, sh * cp,
            sb * cp, cb * cp, -sp,
            -sh * cb + sb * ch * sp, sb * sh + cb * ch * sp, ch * cp)


def xform(m, v):
    return (m[0] * v[0] + m[1] * v[1] + m[2] * v[2], m[3] * v[0] + m[4] * v[1] + m[5] * v[2],
            m[6] * v[0] + m[7] * v[1] + m[8] * v[2])


def mirror(p):
    """Evo (left-handed, feet already converted) -> MR world (right-handed): X -> -X."""
    return (-p[0], p[1], p[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# ----------------------------------------------------------------------------------------------- route
def hermite(p0, t0, p1, t1, n):
    out = []
    for i in range(1, n):
        s = i / n
        h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        out.append(tuple(h00 * p0[k] + h10 * t0[k] + h01 * p1[k] + h11 * t1[k] for k in (0, 1)))
    return out


def route_polyline(track: Track):
    """(x, z) feet polyline through the SIT Course straights, joined with tangent-continuous arcs."""
    segs = [((a[0], a[2]), (b[0], b[2])) for a, b, _w in track.sit.course]
    if not segs:
        # no AI course: chain the checkpoints in SIT order
        pts = [(b.pos[0], b.pos[2]) for b in track.checkpoints()]
        return pts, False
    pts = []
    for i, (a, b) in enumerate(segs):
        if pts:
            pa, pb = segs[i - 1]
            gap = math.dist(pb, a)
            if gap > 1.0:
                d0 = (pb[0] - pa[0], pb[1] - pa[1]); l0 = math.hypot(*d0) or 1
                d1 = (b[0] - a[0], b[1] - a[1]); l1 = math.hypot(*d1) or 1
                t0 = (d0[0] / l0 * gap, d0[1] / l0 * gap); t1 = (d1[0] / l1 * gap, d1[1] / l1 * gap)
                pts += hermite(pb, t0, a, t1, max(2, int(gap / 30)))
        pts += [a, b]
    closed = math.dist(segs[-1][1], segs[0][0]) < 2000.0
    if closed:
        pa, pb = segs[-1]; a, b = segs[0]
        gap = math.dist(pb, a)
        d0 = (pb[0] - pa[0], pb[1] - pa[1]); l0 = math.hypot(*d0) or 1
        d1 = (b[0] - a[0], b[1] - a[1]); l1 = math.hypot(*d1) or 1
        pts += hermite(pb, (d0[0] / l0 * gap, d0[1] / l0 * gap), a, (d1[0] / l1 * gap, d1[1] / l1 * gap), max(2, int(gap / 30)))
    return pts, closed


def resample(pts, step, closed):
    if closed:
        pts = pts + [pts[0]]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    total = cum[-1]
    out, j = [], 0
    s = 0.0
    while s <= total:
        while j < len(cum) - 2 and cum[j + 1] < s:
            j += 1
        seg = cum[j + 1] - cum[j] or 1
        f = (s - cum[j]) / seg
        a, b = pts[j], pts[j + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        s += step
    return out, total


def project_param(route, p):
    best, bi = 1e18, 0
    for i, q in enumerate(route):
        d = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
        if d < best:
            best, bi = d, i
    return bi, math.sqrt(best)


# ----------------------------------------------------------------------------------------------- atlases
class Atlas:
    def __init__(self, prefix, out_dir: Path, tile: int = TILE):
        self.prefix, self.out_dir, self.tile = prefix, out_dir, tile
        self.per_row = PAGE // (tile + 2 * PAD)
        self.per_page = self.per_row * self.per_row
        self.pages: list[bytearray] = []
        self.slots: dict = {}

    @staticmethod
    def tile_for(count: int, pages: int = GROUND_PAGES) -> int:
        for t in TILE_CHOICES:
            if count <= pages * (PAGE // (t + 2 * PAD)) ** 2:
                return t
        return TILE_CHOICES[-1]

    def add(self, key, w, h, rgba):
        if key in self.slots:
            return self.slots[key]
        t = self.tile
        if (w, h) != (t, t):
            rgba = box_mean(w, h, rgba, t, t) if w >= t and h >= t else resize_nearest(w, h, rgba, t, t)
        n = len(self.slots)
        page, idx = divmod(n, self.per_page)
        while len(self.pages) <= page:
            self.pages.append(Image.new("RGBA", (PAGE, PAGE)))
        ox, oy = (idx % self.per_row) * (t + 2 * PAD), (idx // self.per_row) * (t + 2 * PAD)
        self.pages[page].paste(padded(t, t, rgba, PAD), (ox, oy))
        u0, v0 = (ox + PAD) / PAGE, (oy + PAD) / PAGE
        self.slots[key] = (page, u0, v0, t / PAGE)
        return self.slots[key]

    def texture_key(self, page):
        return f"{self.prefix}{page}-tga"

    def save(self, project: CourseProject):
        for i, im in enumerate(self.pages):
            rel = f"textures/{self.texture_key(i)}.png"
            (self.out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            im.save(self.out_dir / rel, compress_level=6)
            project.textures[self.texture_key(i)] = Texture(key=self.texture_key(i), source=rel, width=PAGE, height=PAGE)


class ShelfAtlas:
    """Object textures: shelf-packed pages, used only for models whose UVs stay inside [0, 1]."""

    def __init__(self, prefix, out_dir: Path, max_tile=OBJECT_MAX_TILE):
        self.prefix, self.out_dir, self.max_tile = prefix, out_dir, max_tile
        self.pages, self.slots, self.cursor = [], {}, None

    def add(self, key, w, h, rgba):
        if key in self.slots:
            return self.slots[key]
        while w > self.max_tile or h > self.max_tile:
            rgba = box_mean(w, h, rgba, max(1, w // 2), max(1, h // 2)) if w % 2 == 0 and h % 2 == 0 else resize_nearest(w, h, rgba, max(1, w // 2), max(1, h // 2))
            w, h = max(1, w // 2), max(1, h // 2)
        pw, ph = w + 2 * PAD, h + 2 * PAD
        if self.cursor is None or self.cursor[0] + pw > PAGE:
            if self.cursor is not None and self.cursor[1] + self.cursor[2] + ph <= PAGE:
                self.cursor = [0, self.cursor[1] + self.cursor[2], 0]
            else:
                self.pages.append(Image.new("RGBA", (PAGE, PAGE)))
                self.cursor = [0, 0, 0]
        x0, y0, row_h = self.cursor
        if y0 + ph > PAGE:
            self.pages.append(Image.new("RGBA", (PAGE, PAGE)))
            x0, y0, row_h = 0, 0, 0
        self.pages[-1].paste(padded(w, h, rgba, PAD), (x0, y0))
        self.cursor = [x0 + pw, y0, max(row_h, ph)]
        self.slots[key] = (len(self.pages) - 1, (x0 + PAD) / PAGE, (y0 + PAD) / PAGE, w / PAGE, h / PAGE)
        return self.slots[key]

    def texture_key(self, page):
        return f"{self.prefix}{page}-tga"

    def save(self, project):
        for i, im in enumerate(self.pages):
            rel = f"textures/{self.texture_key(i)}.png"
            (self.out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            im.save(self.out_dir / rel, compress_level=6)
            project.textures[self.texture_key(i)] = Texture(key=self.texture_key(i), source=rel, width=PAGE, height=PAGE, has_alpha=True)


# ----------------------------------------------------------------------------------------------- environment
ENVIRONMENTS = {  # Evo level art prefix / name keywords -> MR Retail scene supplying sky, physics, cameras, HUD
    "desert": "Turkey1", "egypt": "Turkey2", "zona": "Turkey1", "baja": "Spain1", "tibet": "Italy1",
    "arctic": "ItalyW1", "yukon": "FranceW", "alaska": "FranceW", "peak": "Italy2", "thai": "France2",
    "costa": "France2", "island": "Spain2", "autumn": "France1", "aspen": "Italy1",
}


def environment_for(track: Track) -> str:
    text = (track.key + " " + track.sit.name).lower()
    for k, v in ENVIRONMENTS.items():
        if k in text:
            return v
    return "France1"


# ----------------------------------------------------------------------------------------------- conversion
def build_project(track: Track, out_dir: Path, *, corridor_m: float = 190.0, limits_m=(45.0, 75.0), title: str | None = None,
                  course_key: str | None = None, objects: bool = True, object_collision: str = "all",
                  collision_radius_m: float = 40.0, grounded: bool = True, log=print) -> CourseProject:
    out_dir = Path(out_dir)
    key = course_key or safe_key("Evo2" + track.key.capitalize())
    project = new_project(key, title=title or track.sit.name, template=environment_for(track))
    project.materials.clear()
    project.textures.clear()
    project.provenance.kind = "imported"
    project.provenance.notes.append(f"4x4 Evolution 2 {track.pod.path.name} WORLD/{track.key}.SIT '{track.sit.name}'")
    report = {"track": track.key, "name": track.sit.name, "race_type": track.sit.race_type}
    mm = FT  # feet -> metres

    def ground_m(x_m, z_m):
        return track.height(x_m / mm, z_m / mm) * mm

    # ---- route and race layout (feet in, metres out)
    poly, closed = route_polyline(track)
    route_ft, total_ft = resample(poly, ROUTE_STEP_M / mm, closed)
    start_pos, start_or, _trk = track.sit.vehicles[0]
    sx, sz = start_pos[0], start_pos[2]
    heading = start_or[2]                         # vehicles: (pitch, bank, heading) - heading in radians, 0 = +Z
    i0, dist0 = project_param(route_ft, (sx, sz))
    fwd = (math.sin(heading), math.cos(heading))
    ahead = route_ft[(i0 + 3) % len(route_ft)]
    behind = route_ft[(i0 - 3) % len(route_ft)]
    if (ahead[0] - behind[0]) * fwd[0] + (ahead[1] - behind[1]) * fwd[1] < 0:
        route_ft = route_ft[::-1]
        i0 = len(route_ft) - 1 - i0
    if closed:
        route_ft = route_ft[i0:] + route_ft[:i0]
        end_index = max(10, len(route_ft) - int(FINISH_GAP_M / ROUTE_STEP_M))
        lap = route_ft[:end_index]
    else:
        lap = route_ft[i0:]
    # gates ordered along the lap; a gate on the start line is the finish line of a circuit, dropped for one lap
    gates = []
    for b in track.checkpoints():
        k, d = project_param(lap, (b.pos[0], b.pos[2]))
        if closed and (k < int(60 / ROUTE_STEP_M) or k > len(lap) - 3):
            continue
        gates.append((k, b))
    gates.sort(key=lambda t: t[0])
    if not closed and gates:
        lap = lap[:gates[-1][0] + 1]
        gates = gates[:-1]
    route_m = [mirror((x * mm, ground_m(x * mm, z * mm) + 0.3, z * mm)) for x, z in lap]
    # Course Studio draws the RaceLine as straight chords between markers: lift markers so that every chord stays
    # 0.3 m above the terrain surface over crests (else "route leaves the terrain" / AI line inside a hill).
    for _ in range(3):
        lifted = False
        for i in range(len(route_m) - 1):
            a, b = route_m[i], route_m[i + 1]
            deficit = 0.0
            for k in range(1, 10):
                f = k / 10
                x, z = a[0] + (b[0] - a[0]) * f, a[2] + (b[2] - a[2]) * f
                deficit = max(deficit, ground_m(-x, z) + 0.3 - (a[1] + (b[1] - a[1]) * f))
            if deficit > 0.01:
                route_m[i] = (a[0], a[1] + deficit, a[2])
                route_m[i + 1] = (b[0], b[1] + deficit, b[2])
                lifted = True
        if not lifted:
            break
    project.route.points = route_m
    project.route.spacing = ROUTE_STEP_M           # RaceLine markers = these points (chords checked above)

    def head_deg(i):
        a, b = route_m[max(0, i - 1)], route_m[min(len(route_m) - 1, i + 1)]
        return math.degrees(math.atan2(b[0] - a[0], b[2] - a[2]))

    project.start = Area(center=route_m[1], heading=head_deg(1), width=24.0, depth=12.0)
    project.finish = Area(center=route_m[-2], heading=head_deg(len(route_m) - 2), width=36.0, depth=14.0)
    prev, prev_k = 0, 0
    for n, (k, b) in enumerate(gates):
        width = min(max(b.size[0] * mm / 2, 18.0), 40.0)
        seg_len = (k - prev_k) * ROUTE_STEP_M
        extra = round(min(240.0, 25.0 + seg_len / 11.0), 0)            # ~40 km/h through rough off-road + margin
        c = route_m[k]
        gate = mirror((b.pos[0] * mm, ground_m(b.pos[0] * mm, b.pos[2] * mm), b.pos[2] * mm))
        off = math.hypot(gate[0] - c[0], gate[2] - c[2])
        # The trigger must catch the AI line too (Course Studio: centre within max(radius, 25 m) of the route): the
        # radius covers the gate offset; gates further out than 37 m move towards the line.
        if off + 8.0 > 45.0:
            f = 37.0 / off
            gx, gz = c[0] + (gate[0] - c[0]) * f, c[2] + (gate[2] - c[2]) * f
            gate = (gx, ground_m(-gx, gz), gz)
            off = 37.0
        width = min(max(width, off + 8.0), 45.0)
        project.checkpoints.append(Checkpoint(uid=new_uid("cp_"), center=gate,
                                              radius=width, extra_time=extra, heading=head_deg(k),
                                              board_spacing=min(width * 2, 60.0), name=f"Gate {n + 1}",
                                              # the Evo gate models (banner, towers) are the visible gate; Course Studio
                                              # boards sit at the gate centre height (under a slope) and turned 90 deg
                                              boards=False))
        prev_k = k
    first_len = (gates[0][0] if gates else len(route_m)) * ROUTE_STEP_M
    project.environment.time_to_first_checkpoint = round(min(300.0, 30.0 + first_len / 11.0), 0)
    # gaLimitsAI reset lines (see safe_limits): Retail-sized targets, clamped where the route bends or passes itself.
    project.limits.mode = "manual"
    project.limits.inner, project.limits.outer = limits_m
    project.limits.lists, limit_stats = safe_limits(project, *limits_m)
    report["limits"] = limit_stats
    project.build.pacenotes = "auto"
    report.update(closed=closed, route_m=round(len(route_m) * ROUTE_STEP_M), gates=len(gates),
                  start_offset_m=round(dist0 * mm, 1), evo_track_length_m=round(track.sit.track_length_ft * mm))

    # ---- corridor mask (cells), stamped from the route and the gates
    corridor = [False] * (GRID * GRID)
    r_cells = int(math.ceil(corridor_m / (CELL_FT * mm)))
    stamp = [(x / CELL_FT, z / CELL_FT) for x, z in lap[::2]] + [(b.pos[0] / CELL_FT, b.pos[2] / CELL_FT) for b in track.checkpoints()]
    stamp.append((sx / CELL_FT, sz / CELL_FT))
    for cx, cz in stamp:
        for j in range(max(0, int(cz) - r_cells), min(GRID, int(cz) + r_cells + 1)):
            for i in range(max(0, int(cx) - r_cells), min(GRID, int(cx) + r_cells + 1)):
                if (i + 0.5 - cx) ** 2 + (j + 0.5 - cz) ** 2 <= r_cells * r_cells:
                    corridor[j * GRID + i] = True

    # ---- textures: ground tiles
    tile_cache = {}

    def tile(index):
        if index not in tile_cache:
            t = load_texture(track.pod, track.tex[index].name)
            tile_cache[index] = t or (TILE, TILE, bytes((128, 128, 128, 255)) * TILE * TILE)
        return tile_cache[index]

    ground_keys = {track.cell_shadow[c] if track.cell_shadow[c] >= 0 else track.cell_tex[c]
                   for c in range(GRID * GRID) if corridor[c]}
    atlas = Atlas(f"evo_{key.lower()}_g", out_dir, Atlas.tile_for(len(ground_keys)))
    ov_side = GRID * OVERVIEW_PX
    overview = Image.new("RGBA", (ov_side, ov_side))
    small_cache = {}
    for j in range(GRID):
        for i in range(GRID):
            c = j * GRID + i
            idx = track.cell_shadow[c] if track.cell_shadow[c] >= 0 else track.cell_tex[c]
            if idx not in small_cache:
                w, h, rgba = tile(idx)
                small_cache[idx] = Image.frombytes("RGBA", (w, h), rgba).resize((OVERVIEW_PX, OVERVIEW_PX), Image.BOX).transpose(Image.FLIP_TOP_BOTTOM)
            overview.paste(small_cache[idx], (i * OVERVIEW_PX, j * OVERVIEW_PX))
    ov_key = f"evo_{key.lower()}_ov-tga"
    (out_dir / "textures").mkdir(parents=True, exist_ok=True)
    overview.save(out_dir / f"textures/{ov_key}.png")
    project.textures[ov_key] = Texture(key=ov_key, source=f"textures/{ov_key}.png", width=ov_side, height=ov_side)
    project.materials["evo_far"] = Material("evo_far", "Evo far terrain", shader="ground", surface="grass",
                                            textures=[ov_key, None, None], noise=True)

    # ---- terrain meshes
    def vid(i, j):
        return j * (GRID + 1) + i

    def vpos(i, j):
        ii, jj = min(i, GRID - 1), min(j, GRID - 1)            # edge row repeats the last height (map edge)
        return mirror((i * CELL_FT * mm, track.heights_ft[jj * GRID + ii] * mm, j * CELL_FT * mm))

    positions = []
    for j in range(GRID + 1):
        for i in range(GRID + 1):
            positions.extend(vpos(i, j))
    near = Mesh(id=new_uid("mesh_"), name="Evo terrain (race corridor)", role=ROLE_TERRAIN, source="evo2:" + track.key,
                group="Terrain")
    far = Mesh(id=new_uid("mesh_"), name="Evo terrain (horizon)", role=ROLE_VISUAL, source="evo2:" + track.key,
               group="Terrain", materials=["evo_far"])
    near.positions, far.positions = list(positions), list(positions)
    near.uv, far.uv = [], []
    mat_index = {}

    def material_for(page, surface):
        mkey = f"evo_g{page}_{surface}"
        if mkey not in project.materials:
            project.materials[mkey] = Material(mkey, f"Evo ground {page} {surface}", shader="ground", surface=surface,
                                               textures=[atlas.texture_key(page), None, None], noise=True)
        if mkey not in mat_index:
            mat_index[mkey] = len(near.materials)
            near.materials.append(mkey)
        return mat_index[mkey]

    corridor_cells = 0
    for j in range(GRID):
        for i in range(GRID):
            c = j * GRID + i
            quad = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            tris = ((quad[0], quad[2], quad[3]), (quad[0], quad[1], quad[2]))      # mirrored frame: re-wound
            if corridor[c]:
                corridor_cells += 1
                idx = track.cell_shadow[c] if track.cell_shadow[c] >= 0 else track.cell_tex[c]
                w, h, rgba = tile(idx)
                page, u0, v0, span = atlas.add(idx, w, h, rgba)
                surface = MR_SURFACE[track.tex[track.cell_tex[c]].terrain_class]
                m = material_for(page, surface)
                for tri in tris:
                    near.triangles.extend(vid(*q) for q in tri)
                    near.tri_material.append(m)
                    for q in tri:
                        near.uv.extend((u0 + (q[0] - i) * span, v0 + (j + 1 - q[1]) * span))   # tile top at +Z
    # Far terrain (drawn only): 2x2-cell blocks where all four cells are far, single cells next to the corridor; a block
    # edge that meets single cells gets a skirt dropping below the finer edge (no T-junction cracks against the sky).
    def far_quad(i0, j0, s):
        quad = ((i0, j0), (i0 + s, j0), (i0 + s, j0 + s), (i0, j0 + s))
        for tri in ((quad[0], quad[2], quad[3]), (quad[0], quad[1], quad[2])):
            far.triangles.extend(vid(*q) for q in tri)
            far.tri_material.append(0)
            for q in tri:
                far.uv.extend((q[0] / GRID, q[1] / GRID))

    coarse = set()
    for bj in range(0, GRID, 2):
        for bi in range(0, GRID, 2):
            if all(not corridor[(bj + dj) * GRID + bi + di] for dj in (0, 1) for di in (0, 1)):
                coarse.add((bi, bj))
    for j in range(GRID):
        for i in range(GRID):
            if corridor[j * GRID + i]:
                continue
            if (i - i % 2, j - j % 2) in coarse:
                if i % 2 == 0 and j % 2 == 0:
                    far_quad(i, j, 2)
            else:
                far_quad(i, j, 1)
    skirt_drop = 2.0
    for (bi, bj) in coarse:
        for (ni, nj), edge in (((bi - 2, bj), ((bi, bj), (bi, bj + 2))), ((bi + 2, bj), ((bi + 2, bj + 2), (bi + 2, bj))),
                               ((bi, bj - 2), ((bi + 2, bj), (bi, bj))), ((bi, bj + 2), ((bi, bj + 2), (bi + 2, bj + 2)))):
            if (ni, nj) in coarse or not (0 <= ni < GRID and 0 <= nj < GRID):
                continue
            (ai, aj), (ci, cj) = edge
            a, c = vpos(ai, aj), vpos(ci, cj)
            base = len(far.positions) // 3
            far.positions.extend(a); far.positions.extend(c)
            far.positions.extend((a[0], a[1] - skirt_drop, a[2])); far.positions.extend((c[0], c[1] - skirt_drop, c[2]))
            for tri in ((0, 1, 3), (0, 3, 2), (0, 3, 1), (0, 2, 3)):         # both sides
                far.triangles.extend(base + k for k in tri)
                far.tri_material.append(0)
                for k in tri:
                    gi, gj = (ai, aj) if k in (0, 2) else (ci, cj)
                    far.uv.extend((gi / GRID, gj / GRID))
    atlas.save(project)
    project.meshes.append(near)
    if far.triangles:
        project.meshes.append(far)
    report.update(corridor_cells=corridor_cells, ground_tiles=len(atlas.slots), ground_pages=len(atlas.pages))

    # ---- water
    wl = track.level.water_height_ft
    if wl > -1e8:
        water = Mesh(id=new_uid("mesh_"), name="Evo water", role=ROLE_WATER, source="evo2:" + track.key, group="Water",
                     materials=["evo_water"])
        water.uv = []
        wv = {}
        def wvid(i, j):
            if (i, j) not in wv:
                wv[(i, j)] = len(water.positions) // 3
                water.positions.extend(mirror((i * CELL_FT * mm, wl * mm, j * CELL_FT * mm)))
            return wv[(i, j)]
        for j in range(GRID - 1):
            for i in range(GRID - 1):
                lo = min(track.heights_ft[(j + dj) * GRID + i + di] for dj in (0, 1) for di in (0, 1))
                if lo < wl:
                    quad = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                    for tri in ((quad[0], quad[2], quad[3]), (quad[0], quad[1], quad[2])):
                        water.triangles.extend(wvid(*q) for q in tri)
                        water.tri_material.append(0)
                        for q in tri:
                            water.uv.extend((q[0] / 4.0, q[1] / 4.0))
        if water.triangles:
            r, g, b, a = (list(track.level.water_rgba) + [255] * 4)[:4]
            wt = load_texture(track.pod, "waterx00.RAW")
            if wt:
                ww, wh, wr = wt
                wr = bytes(v if k % 4 != 3 else max(96, min(220, a)) for k, v in enumerate(wr))
            else:
                ww = wh = 8
                wr = bytes((r, g, b, max(96, min(220, a)))) * 64
            write_png(out_dir / "textures/evo_water-tga.png", ww, wh, wr)
            project.textures["evo_water-tga"] = Texture(key="evo_water-tga", source="textures/evo_water-tga.png",
                                                        width=ww, height=wh, has_alpha=True)
            project.materials["evo_water"] = Material("evo_water", "Evo water", shader="water", surface="water",
                                                      textures=["evo_water-tga", None, None], noise=False, alpha="blend")
            project.meshes.append(water)
            report["water_triangles"] = len(water.tri_material)

    # ---- objects (collision only near the AI line and the gates: the solids the cars actually reach)
    near = [False] * (GRID * GRID)
    rc = collision_radius_m / (CELL_FT * mm)
    for cx, cz in [(x / CELL_FT, z / CELL_FT) for x, z in lap] + [(b.pos[0] / CELL_FT, b.pos[2] / CELL_FT) for b in track.checkpoints()]:
        for j in range(max(0, int(cz - rc) - 1), min(GRID, int(cz + rc) + 2)):
            for i in range(max(0, int(cx - rc) - 1), min(GRID, int(cx + rc) + 2)):
                if (i + 0.5 - cx) ** 2 + (j + 0.5 - cz) ** 2 <= rc * rc:
                    near[j * GRID + i] = True
    if objects:
        report.update(add_objects(track, project, out_dir, key, near, log, object_collision, grounded, route_m))
    # Course Studio UVs follow the FEED texture rows (stored bottom-up, uploaded as-is): v = 0 is the bottom row of
    # the PNG. Evo UVs and every atlas rectangle above are top-origin, so v is flipped once for every mesh here.
    for mesh in project.meshes:
        if mesh.uv:
            mesh.uv[1::2] = [1.0 - v for v in mesh.uv[1::2]]
    report["texture_bytes"] = texture_bytes(project, out_dir)
    report["ground_tile_px"] = atlas.tile
    if report["texture_bytes"] > TEXTURE_BUDGET_BYTES:
        raise ValueError(f"course textures need {report['texture_bytes'] / 2**20:.1f} MB with mips "
                         f"(budget {TEXTURE_BUDGET_BYTES >> 20} MB): the race would thrash the MR model cache")
    project.extras["evo2"] = report
    return project


def safe_limits(project, inner: float, outer: float, minimum: float = 12.0, step: float = 5.0):
    """Four gaLimitsAI lists that never fold over the AI line.

    gaLimitsAI (0x4CD9B0, research/g1/limits-executable.md) takes the nearest marker of each list separately and
    tests the car against the region built between them. Constant offsets of 90/140 m (batch-03, Course Studio
    "auto") crossed to the wrong side of the line on the inside of tight Evo turns and lay next to other parts of
    the route, so the nearest "left" marker could sit on the right or at another progress: cars were reset on the
    road. Here each station gets the largest offset (<= target) whose point is still nearest to its own part of the
    route and on its own side; offsets are then smoothed (running minimum, then mean) and outer >= inner + 10 m.
    """
    import numpy as np
    from master_rallye.course_entry import RouteFrame
    from master_rallye.studio.ai import raceline
    line = raceline(project)
    frame = RouteFrame(line)
    xz = np.array([(q[0], q[2]) for q in line])
    ys = np.array([q[1] for q in line])
    cum = np.array(frame.cum)
    spacing = max(5.0, project.route.spacing)
    count = max(2, int(frame.total / spacing) + 1)
    stations = [frame.total * k / (count - 1) for k in range(count)]
    closed_loop = math.dist(line[0], line[-1]) < 250.0

    def ok(s, side, d):
        p, yaw = frame.place(s, side * d, 0.0)
        # 3-D like gaLimitsAI's nearest marker: a bridge over another leg does not narrow the limits
        dd = ((xz[:, 0] - p[0]) ** 2 + (xz[:, 1] - p[2]) ** 2 + (ys - p[1]) ** 2)
        n = int(dd.argmin())
        gap = abs(cum[n] - s)
        if closed_loop:
            gap = min(gap, frame.total - gap)             # circuit: the line's end lies next to its start
        if gap > 1.5 * d + 20.0 or math.sqrt(dd[n]) < 0.6 * d:
            return False                                  # closer to another part of the route, or folded inwards
        fx, fz = frame.forward(min(n, len(line) - 2))
        return (fx * (p[2] - xz[n, 1]) - fz * (p[0] - xz[n, 0])) * side > 0

    def widest(s, side, target):
        d = target
        while d > minimum and not ok(s, side, d):
            d -= step
        return max(d, minimum)

    def smooth(v, w=3):
        v = np.array(v)
        m = np.array([v[max(0, i - w):i + w + 1].min() for i in range(len(v))])
        return np.array([m[max(0, i - w):i + w + 1].mean() for i in range(len(m))])

    lists, stats = {}, {}
    for side, prefix in ((-1, "Left"), (1, "Right")):
        o = smooth([widest(s, side, outer) for s in stations])
        i = smooth([widest(s, side, inner) for s in stations])
        i = np.minimum(i, np.maximum(o - 10.0, minimum * 0.5))
        lists[prefix + "InnerLimit"] = [frame.place(s, side * d, 0.0)[0] for s, d in zip(stations, i)]
        lists[prefix + "OuterLimit"] = [frame.place(s, side * d, 0.0)[0] for s, d in zip(stations, o)]
        stats[prefix.lower()] = {"inner_min": round(float(i.min()), 1), "inner_median": round(float(np.median(i)), 1),
                                 "outer_min": round(float(o.min()), 1), "outer_median": round(float(np.median(o)), 1)}
    return lists, stats


def texture_bytes(project, out_dir: Path) -> int:
    """A8R8G8B8 with a full mip chain, as MR creates course textures."""
    total = 0
    for t in project.textures.values():
        w, h = t.width, t.height
        while True:
            total += w * h * 4
            if w == 1 and h == 1:
                break
            w, h = max(1, w // 2), max(1, h // 2)
    return total


def _directions(n=162):
    """Roughly uniform unit vectors (golden spiral)."""
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - y * y))
        a = i * math.pi * (3 - math.sqrt(5))
        out.append((math.cos(a) * r, y, math.sin(a) * r))
    return out


DIRECTIONS = _directions(32)


def support_points(points, limit=32):
    """Hull-preserving reduction: the extreme point in each of 32 directions (exact when already small). Keeps every
    hull at most 60 faces: Course Studio builds an object of up to 64 faces without axis splits (object_bsp.py)."""
    pts = sorted(set(points))
    if len(pts) <= limit:
        return pts
    keep = {max(pts, key=lambda q: q[0] * d[0] + q[1] * d[1] + q[2] * d[2]) for d in DIRECTIONS}
    return sorted(keep)


def _box_tris(center, size, m):
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    corners = [(sx * hx, sy * hy, sz * hz) for sy in (-1, 1) for sz in (-1, 1) for sx in (-1, 1)]
    v = [mirror(tuple(center[k] + xform(m, c)[k] for k in range(3))) for c in corners]
    center = mirror(center)
    # indices: bottom 0..3 (z-,x-),(z-,x+),(z+,x-),(z+,x+); top 4..7
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    tris = []
    for q in quads:
        for t in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
            a, b, c = v[t[0]], v[t[1]], v[t[2]]
            n = cross(sub(b, a), sub(c, a))
            ctr = tuple((a[k] + b[k] + c[k]) / 3 - center[k] for k in range(3))
            tris.append((a, c, b) if dot(n, ctr) < 0 else (a, b, c))
    return tris


def add_objects(track: Track, project: CourseProject, out_dir: Path, key: str, corridor, log, collision: str = "all",
                grounded: bool = True, route_samples=()) -> dict:
    mm = FT
    shelf = ShelfAtlas(f"evo_{key.lower()}_o", out_dir)
    loose = {}                       # texture name -> project texture key (tiling UVs)
    smf_cache, tex_cache = {}, {}
    visual = Mesh(id=new_uid("mesh_"), name="Evo objects", role=ROLE_VISUAL, source="evo2:" + track.key, group="Objects")
    visual.uv = []
    visual.normals = []
    proxies = Mesh(id=new_uid("mesh_"), name="Evo object collision", role=ROLE_COLLISION, source="evo2:" + track.key,
                   group="Objects", materials=["evo_collision"])
    drive = Mesh(id=new_uid("mesh_"), name="Evo drivable objects", role=ROLE_TERRAIN, source="evo2:" + track.key,
                 group="Objects")
    drive.uv = []
    project.materials["evo_collision"] = Material("evo_collision", "Evo collision", shader="object", surface="rock",
                                                  noise=False)
    mat_slots = {visual.id: {}, drive.id: {}}
    stats = {"objects": 0, "object_missing_models": [], "box_proxies": 0, "drivable_objects": 0, "skipped_far": 0}

    def ground_mr(x, z):
        return track.height(-x / mm, z / mm) * mm          # MR (mirrored) metres -> Evo feet -> ground metres

    solids = []                      # point sets of convex proxies; merged where they overlap, emitted at the end

    def add_grounded(points, depth=0.5):
        """Convex collision proxy whose underside sits `depth` below the ground (Course Studio rule: solids that reach
        deep under the terrain break the solid-leaf union and leave phantom solid / holes). False when buried."""
        if not grounded:
            floor = min(q[1] for q in points)
        else:
            floor = min(ground_mr(q[0], q[2]) for q in points) - depth
        if grounded and max(q[1] for q in points) <= floor + depth + 0.05:
            return False
        solids.append(support_points([(q[0], max(q[1], floor), q[2]) for q in points]))
        return True

    def texture(name):
        if name in tex_cache:
            return tex_cache[name]
        tex_cache[name] = load_texture(track.pod, name)
        return tex_cache[name]

    def mesh_material(mesh, tex_name, alpha, tiling, drivable):
        t = texture(tex_name)
        if t is None:
            mkey = "evo_obj_plain"
            if mkey not in project.materials:
                project.materials[mkey] = Material(mkey, "Evo object", shader="object", surface=None, noise=False)
            transform = None
        elif tiling:
            tkey = loose.get(tex_name.casefold())
            if tkey is None:
                tkey = safe_key("evo_" + tex_name.rsplit(".", 1)[0]).lower() + "-tga"
                w, h, rgba = t
                while w > OBJECT_MAX_TILE or h > OBJECT_MAX_TILE:
                    nw, nh = max(1, w // 2), max(1, h // 2)
                    rgba = box_mean(w, h, rgba, nw, nh)
                    w, h = nw, nh
                write_png(out_dir / f"textures/{tkey}.png", w, h, rgba)
                project.textures[tkey] = Texture(key=tkey, source=f"textures/{tkey}.png", width=w, height=h, has_alpha=alpha)
                loose[tex_name.casefold()] = tkey
            mkey = f"evo_t_{tkey}"
            transform = None
        else:
            w, h, rgba = t
            page, u0, v0, us, vs = shelf.add(tex_name.casefold(), w, h, rgba)
            tkey = shelf.texture_key(page)
            mkey = f"evo_o{page}{'_a' if alpha else ''}{'_d' if drivable else ''}"
            transform = (u0, v0, us, vs)
        if mkey not in project.materials:
            if t is None:
                pass
            elif drivable:
                project.materials[mkey] = Material(mkey, "Evo drivable", shader="ground", surface="harddirt",
                                                   textures=[tkey, None, None], noise=False)
            else:
                project.materials[mkey] = Material(mkey, "Evo object", shader="tree" if alpha else "object", surface=None,
                                                   textures=[tkey, None, None], noise=False,
                                                   alpha="cutout" if alpha else "opaque")
        slots = mat_slots[mesh.id]
        if mkey not in slots:
            slots[mkey] = len(mesh.materials)
            mesh.materials.append(mkey)
        return slots[mkey], transform

    for b in track.sit.boxes:
        cell_i, cell_j = int(b.pos[0] / CELL_FT), int(b.pos[2] / CELL_FT)
        in_corridor = 0 <= cell_i < GRID and 0 <= cell_j < GRID and corridor[cell_j * GRID + cell_i]
        m = euler_pbh(b.orient[0], b.orient[1], b.orient[2]) if len(b.orient) == 3 else euler_pbh(0, 0, 0)
        center = (b.pos[0] * mm, b.pos[1] * mm, b.pos[2] * mm)
        if collision in ("all", "boxes") and (b.kind == "CCollisionBox" or (b.kind == "CCollide" and b.fields.get("collisionType", "0") == "0")):
            if in_corridor and all(s > 0 for s in b.size):
                size = tuple(max(s * mm, 0.4) for s in b.size)         # fences/decks: >= 0.4 m (no sliver faces)
                corners = sorted({p for tri in _box_tris(center, size, m) for p in tri})
                if add_grounded(corners):
                    stats["box_proxies"] += 1
                else:
                    stats["buried_boxes"] = stats.get("buried_boxes", 0) + 1
        if b.kind not in ("CCollide", "CNonCollide", "CNonCollideFacing") or not b.model:
            continue
        drivable = collision in ("all", "drivable") and b.kind == "CCollide" and b.fields.get("collisionType", "0") == "1" and in_corridor
        name = b.model
        if name.casefold() not in smf_cache:
            member = track.pod.find(name, ("MODELS", "ART", "DATA"))
            smf_cache[name.casefold()] = parse_smf(track.pod.read(member)) if member else None
        smf = smf_cache[name.casefold()]
        if smf is None:
            stats["object_missing_models"].append(name)
            continue
        target = visual
        hull_points = []
        for obj in smf["objects"]:
            if not obj["visible"] or not obj["faces"]:
                continue
            verts = obj["vertices_by_frame"][0]
            uvs = [(v[6], v[7]) for v in verts]
            tiling = any(u < -0.01 or u > 1.01 or v < -0.01 or v > 1.01 for u, v in uvs)
            t = texture(obj["texture"])
            alpha = bool(t) and any(t[2][k] < 250 for k in range(3, len(t[2]), 4))
            mi, tr = mesh_material(target, obj["texture"], alpha, tiling, False)
            world = [mirror(tuple(center[k] + xform(m, (v[0] * mm, v[1] * mm, v[2] * mm))[k] for k in range(3))) for v in verts]
            normals = [mirror(xform(m, (v[3], v[4], v[5]))) for v in verts]
            if drivable:
                hull_points.extend(world)
            base = len(target.positions) // 3
            for p in world:
                target.positions.extend(p)
            for f in obj["faces"]:
                a, bb, c = f
                n = cross(sub(world[bb], world[a]), sub(world[c], world[a]))
                vn = tuple(normals[a][k] + normals[bb][k] + normals[c][k] for k in range(3))
                order = (a, bb, c) if dot(n, vn) >= 0 else (a, c, bb)
                target.triangles.extend(base + i for i in order)
                target.tri_material.append(mi)
                for i in order:
                    u, v = uvs[i]
                    if tr:
                        u0, v0, us, vs = tr
                        u, v = u0 + min(max(u, 0.0), 1.0) * us, v0 + min(max(v, 0.0), 1.0) * vs
                    target.uv.extend((u, v))
                    if target is visual:
                        target.normals.extend(normals[i])
        stats["objects"] += 1
        if drivable and hull_points and add_grounded(hull_points):
            stats["drivable_objects"] += 1
    # Course Studio compiles all collision objects into one solid BSP: overlapping closed solids break its solid-leaf
    # classification (whole regions became solid). Proxies whose convex hulls really intersect (face-normal separating
    # axis test, conservative) are merged into the hull of their union until none overlap; a solid that would block the
    # AI line between 0.5 and 2.4 m above the ground is dropped (the Evo AI line is the drivable race line).
    from master_rallye.studio.collision import convex_hull

    def hull(pts):
        tris = convex_hull(pts)
        planes = []
        for a, b, c in tris:
            n = cross(sub(b, a), sub(c, a))
            ln = math.sqrt(dot(n, n))
            if ln < 1e-4:                      # a face Course Studio would drop: the solid would leak
                tris = []
                break
            n = (n[0] / ln, n[1] / ln, n[2] / ln)
            planes.append((n, dot(n, a)))
        lo = [min(q[k] for q in pts) for k in range(3)]
        hi = [max(q[k] for q in pts) for k in range(3)]
        return {"pts": pts, "tris": tris, "planes": planes, "lo": lo, "hi": hi}

    def separated(a, b):
        for h, other in ((a, b), (b, a)):
            for n, d in h["planes"]:
                if all(dot(n, q) - d > 1e-3 for q in other["pts"]):
                    return True
        return False

    hulls = [h for h in (hull(pts) for pts in solids) if h["tris"]]
    changed = True
    while changed:
        changed = False
        hulls.sort(key=lambda h: h["lo"][0])
        for i in range(len(hulls)):
            a = hulls[i]
            for j in range(i + 1, len(hulls)):
                b = hulls[j]
                if b["lo"][0] > a["hi"][0]:
                    break
                if all(a["lo"][k] < b["hi"][k] and b["lo"][k] < a["hi"][k] for k in range(3)) and not separated(a, b):
                    merged = hull(support_points(a["pts"] + b["pts"]))
                    hulls = [h for k, h in enumerate(hulls) if k not in (i, j)] + ([merged] if merged["tris"] else [])
                    changed = True
                    break
            if changed:
                break
    # the Course Studio route sweep: +-1 m beside the AI line, 0.35..2.2 m above the ground (with margin)
    samples = []
    rs = list(route_samples)
    for i in range(len(rs) - 1):
        a, b = rs[i], rs[i + 1]
        dx, dz = b[0] - a[0], b[2] - a[2]
        ln = math.hypot(dx, dz) or 1.0
        for f in (0.0, 0.25, 0.5, 0.75):
            x, y, z = a[0] + dx * f, a[1] + (b[1] - a[1]) * f - 0.3, a[2] + dz * f
            for off in (-1.5, 0.0, 1.5):
                for dy in (0.3, 0.7, 1.5, 2.4):
                    samples.append((x - dz / ln * off, y + dy, z + dx / ln * off))

    def blocks(h):
        for q in samples:
            if all(h["lo"][k] - 0.01 <= q[k] <= h["hi"][k] + 0.01 for k in range(3)) and all(dot(n, q) - d <= 0 for n, d in h["planes"]):
                return True
        return False
    stats["collision_solids"] = 0
    stats["route_blocking_solids_dropped"] = 0
    for h in hulls:
        if blocks(h):
            stats["route_blocking_solids_dropped"] += 1
            continue
        stats["collision_solids"] += 1
        first = len(proxies.tri_material)
        project.extras.setdefault("evo2_solids", {}).setdefault(proxies.id, []).append([first, first + len(h["tris"])])
        for tri in h["tris"]:
            for q in tri:
                proxies.triangles.append(len(proxies.positions) // 3)
                proxies.positions.extend(q)
            proxies.tri_material.append(0)
    shelf.save(project)
    for mesh in (visual, proxies, drive):
        if mesh.triangles:
            if mesh is visual and len(mesh.normals) != len(mesh.triangles) * 3:
                mesh.normals = None
            project.meshes.append(mesh)
    stats["object_pages"] = len(shelf.pages)
    stats["tiling_textures"] = len(loose)
    stats["object_missing_models"] = sorted(set(stats["object_missing_models"]))
    return stats


def main(argv=None):
    import argparse
    from master_rallye.studio.model import save_project
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pod", type=Path)
    ap.add_argument("--sit", help="WORLD/<name>.SIT stem (default: first)")
    ap.add_argument("--out", type=Path, required=True, help="Course Studio project folder to create")
    ap.add_argument("--corridor", type=float, default=190.0)
    ap.add_argument("--no-objects", action="store_true")
    ap.add_argument("--key")
    ap.add_argument("--title")
    a = ap.parse_args(argv)
    track = load_track(a.pod, a.sit)
    project = build_project(track, a.out, corridor_m=a.corridor, objects=not a.no_objects, course_key=a.key, title=a.title)
    save_project(project, a.out)
    print(json.dumps(project.extras["evo2"], indent=1))


if __name__ == "__main__":
    main()
