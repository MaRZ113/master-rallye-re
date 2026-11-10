"""Country atlas: union of Retail stage corridors sharing one world frame.

Retail stages of one country are corridors cut from a common master landscape:
their DX vertex positions coincide exactly where the corridors overlap, and
their RaceLines share road segments. This module composes those read-only
facts into concept data for new combined courses:

* a deduplicated union render mesh (triangles keyed by rounded positions and
  primary texture basename) with per-triangle stage coverage;
* a stitched route that chains stage RaceLines (optionally reversed) through
  their shared roads;
* corridor cropping and size budgets for a candidate compiled course.

Nothing here writes compiled DX/tag100 or claims runtime behavior. The outputs
are Blender/GXM-source inputs for the cooker path documented in
``docs/course-new-entries.md``.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .dx_course import CourseDxModel, parse_course_dx

Vec3 = tuple[float, float, float]
POSITION_KEY_DECIMALS = 2


def read_marker_list(xml_path: Path, list_name: str) -> list[Vec3]:
    root = ET.parse(xml_path).getroot()
    for marker_list in root.iter("List"):
        if marker_list.get("Name") != list_name:
            continue
        return [
            tuple(float(part) for part in value.get("Value", "").split()[:3])
            for value in marker_list.iter("Value")
            if value.get("Name") == "Marker Pos"
        ]
    return []


def route_length(route: Sequence[Vec3]) -> float:
    return sum(math.dist(a, b) for a, b in zip(route, route[1:]))


@dataclass
class AtlasStage:
    name: str
    dx_path: Path
    xml_path: Path | None
    raceline: list[Vec3] = field(default_factory=list)


@dataclass
class AtlasTriangle:
    positions: tuple[Vec3, Vec3, Vec3]
    uvs: tuple[tuple[float, float], ...] | None
    texture: str
    stages: set[str]


@dataclass
class CountryAtlas:
    country: str
    stages: list[AtlasStage]
    triangles: list[AtlasTriangle]
    source_triangle_count: int
    texture_sources: dict[str, Path]

    @property
    def unique_positions(self) -> int:
        return len({p for tri in self.triangles for p in tri.positions})

    def summary(self) -> dict:
        per_stage = {stage.name: 0 for stage in self.stages}
        exclusive = {stage.name: 0 for stage in self.stages}
        for tri in self.triangles:
            for name in tri.stages:
                per_stage[name] += 1
            if len(tri.stages) == 1:
                exclusive[next(iter(tri.stages))] += 1
        return {
            "country": self.country,
            "stages": [stage.name for stage in self.stages],
            "source_triangles": self.source_triangle_count,
            "union_triangles": len(self.triangles),
            "union_ratio": round(len(self.triangles) / max(1, self.source_triangle_count), 4),
            "union_unique_positions": self.unique_positions,
            "textures": len(self.texture_sources),
            "triangles_per_stage": per_stage,
            "exclusive_triangles_per_stage": exclusive,
            "raceline_length_per_stage": {s.name: round(route_length(s.raceline), 1) for s in self.stages},
        }


def _texture_basename(value: str) -> str:
    return value.replace("/", "\\").split("\\")[-1].lower()


def _pos_key(p: Sequence[float]) -> Vec3:
    return tuple(round(float(c), POSITION_KEY_DECIMALS) for c in p[:3])  # type: ignore[return-value]


def build_country_atlas(country: str, stages: Iterable[AtlasStage]) -> CountryAtlas:
    """Union the render triangles of every supplied stage DX."""
    stage_list = list(stages)
    by_key: dict[tuple, AtlasTriangle] = {}
    order: list[tuple] = []
    textures: dict[str, Path] = {}
    total = 0
    for stage in stage_list:
        model: CourseDxModel = parse_course_dx(stage.dx_path)
        if stage.xml_path is not None and not stage.raceline:
            stage.raceline = read_marker_list(stage.xml_path, "RaceLine")
        positions = model.vertices.positions
        uv0 = model.uv_sets[0].values if model.uv_sets else None
        for draw in model.physical_draws:
            primary = next((slot.value for slot in draw.texture_slots if slot.value.lower() != "null"), "null")
            texture = _texture_basename(primary)
            if texture != "null" and texture not in textures:
                candidate = stage.dx_path.parent / f"{texture}.dxt"
                if candidate.exists():
                    textures[texture] = candidate
            indices = model.draw_global_indices(draw)
            for at in range(0, len(indices) - 2, 3):
                face = indices[at:at + 3]
                total += 1
                pos = tuple(_pos_key(positions[i]) for i in face)
                key = (frozenset(pos), texture)
                hit = by_key.get(key)
                if hit is not None:
                    hit.stages.add(stage.name)
                    continue
                uvs = tuple((float(uv0[i][0]), float(uv0[i][1])) for i in face) if uv0 else None
                by_key[key] = AtlasTriangle(pos, uvs, texture, {stage.name})  # type: ignore[arg-type]
                order.append(key)
    return CountryAtlas(country, stage_list, [by_key[k] for k in order], total, textures)


# --------------------------------------------------------------------------- routes


@dataclass(frozen=True)
class RouteLeg:
    stage: str
    reversed: bool
    start_index: int
    end_index: int
    join_gap: float
    new_length: float


@dataclass
class StitchedRoute:
    name: str
    samples: list[Vec3]
    legs: list[RouteLeg]

    @property
    def length(self) -> float:
        return route_length(self.samples)

    @property
    def max_join_gap(self) -> float:
        return max((leg.join_gap for leg in self.legs[1:]), default=0.0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "samples": len(self.samples),
            "length": round(self.length, 1),
            "max_join_gap": round(self.max_join_gap, 2),
            "self_overlap_length": round(self_overlap_length(self.samples), 1),
            "legs": [leg.__dict__ for leg in self.legs],
        }


class _CoverageIndex:
    """Grid hash of driven route samples (with route index) for new-road accounting."""

    def __init__(self, cell: float = 8.0) -> None:
        self.cell = cell
        self.cells: dict[tuple[int, int], list[tuple[float, float, int]]] = {}
        self.count = 0

    def add(self, p: Vec3) -> None:
        key = (math.floor(p[0] / self.cell), math.floor(p[2] / self.cell))
        self.cells.setdefault(key, []).append((p[0], p[2], self.count))
        self.count += 1

    def truncate(self, keep: int) -> None:
        """Forget samples whose route index is >= ``keep``."""
        for key, items in list(self.cells.items()):
            items[:] = [item for item in items if item[2] < keep]
        self.count = keep

    def covered(self, p: Vec3, radius: float = 8.0, below: int | None = None) -> bool:
        cx, cz = math.floor(p[0] / self.cell), math.floor(p[2] / self.cell)
        reach = int(math.ceil(radius / self.cell))
        limit = self.count if below is None else below
        for dx in range(-reach, reach + 1):
            for dz in range(-reach, reach + 1):
                for x, z, k in self.cells.get((cx + dx, cz + dz), ()):
                    if k < limit and (x - p[0]) ** 2 + (z - p[2]) ** 2 <= radius * radius:
                        return True
        return False


def _new_length(route: Sequence[Vec3], coverage: _CoverageIndex, below: int | None = None) -> float:
    return sum(math.dist(a, b) for a, b in zip(route, route[1:]) if not coverage.covered(b, below=below))


def _clip_to_new_road(
    piece: Sequence[Vec3], coverage: _CoverageIndex, *, below: int | None = None, lead_in: float = 60.0,
    keep_clear: float = 10.0, clear_skip: int = 15,
) -> list[Vec3]:
    """Drop covered road after the join (beyond ``lead_in``) and stop at the
    first return onto already-driven road, so the route never revisits itself.

    With ``keep_clear`` above 10 the piece also stops where it comes within
    that distance of earlier road (ignoring the ``clear_skip`` samples before
    the join): gaLimitsAI re-selects the globally nearest limit marker, so
    near-passes of the route classify a centred car as outside.
    """
    out: list[Vec3] = []
    travelled = 0.0
    seen_new = False
    for k, p in enumerate(piece):
        if k:
            travelled += math.dist(piece[k - 1], p)
        covered = coverage.covered(p, 10.0, below=below)
        if covered and seen_new:
            break
        if keep_clear > 10.0 and seen_new and travelled > lead_in and coverage.covered(
                p, keep_clear, below=None if below is None else max(0, below - clear_skip)):
            break
        if covered and travelled > lead_in:
            return []
        seen_new = seen_new or not covered
        out.append(p)
    return out if seen_new else []


def self_overlap_length(route: Sequence[Vec3], radius: float = 12.0, min_index_gap: int = 15) -> float:
    """Route length lying within ``radius`` of a non-neighbouring route sample."""
    index: dict[tuple[int, int], list[int]] = {}
    cell = radius
    for k, p in enumerate(route):
        index.setdefault((math.floor(p[0] / cell), math.floor(p[2] / cell)), []).append(k)
    total = 0.0
    for k in range(1, len(route)):
        p = route[k]
        cx, cz = math.floor(p[0] / cell), math.floor(p[2] / cell)
        hit = False
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for other in index.get((cx + dx, cz + dz), ()):
                    if abs(other - k) >= min_index_gap and math.dist((p[0], p[2]), (route[other][0], route[other][2])) <= radius:
                        hit = True
                        break
        if hit:
            total += math.dist(route[k - 1], p)
    return total


def _xz_dir(a: Vec3, b: Vec3) -> tuple[float, float]:
    dx, dz = b[0] - a[0], b[2] - a[2]
    n = math.hypot(dx, dz) or 1.0
    return dx / n, dz / n


def _best_join(
    tail: Sequence[Vec3], head: Sequence[Vec3], max_turn_degrees: float = 120.0
) -> tuple[int, int, float]:
    """Join tail's last 35% to head's first 65% at the closest sample pair.

    Pairs whose travel directions differ by more than ``max_turn_degrees`` are
    rejected so a reversed leg cannot U-turn back along the road just driven.
    """
    tail_from = max(1, int(len(tail) * 0.65))
    head_to = max(2, int(len(head) * 0.65))
    min_dot = math.cos(math.radians(max_turn_degrees))
    best = (len(tail) - 1, 0, math.inf)
    for i in range(tail_from, len(tail)):
        incoming = _xz_dir(tail[i - 1], tail[i])
        for j in range(0, min(head_to, len(head) - 1)):
            d = math.dist(tail[i], head[j])
            if d >= best[2]:
                continue
            outgoing = _xz_dir(head[j], head[j + 1])
            if incoming[0] * outgoing[0] + incoming[1] * outgoing[1] < min_dot:
                continue
            best = (i, j, d)
    return best


def stitch_routes(
    name: str,
    stages: Sequence[AtlasStage],
    *,
    first: str | None = None,
    allow_reverse: bool = True,
    max_join_gap: float = 40.0,
    min_new_length: float = 500.0,
    keep_clear: float = 10.0,
) -> StitchedRoute:
    """Greedily chain stage RaceLines into one longer route.

    Each step picks the stage (forward or reversed) that joins the current
    route end within ``max_join_gap`` without a U-turn and adds the most
    not-yet-driven road. Each leg is clipped where it would rejoin driven road,
    because RaceLine progress and the SFL heading field are single-valued.
    """
    pool = {s.name: s.raceline for s in stages if len(s.raceline) >= 2}
    if not pool:
        raise ValueError("no stage RaceLines")
    start_name = first or max(pool, key=lambda n: route_length(pool[n]))
    samples = list(pool.pop(start_name))
    coverage = _CoverageIndex()
    for p in samples:
        coverage.add(p)
    legs = [RouteLeg(start_name, False, 0, len(samples) - 1, 0.0, round(route_length(samples), 1))]
    while pool:
        best = None
        for stage_name, line in pool.items():
            options = [(False, line)] + ([(True, list(reversed(line)))] if allow_reverse else [])
            for is_reversed, candidate in options:
                i, j, gap = _best_join(samples, candidate)
                if gap > max_join_gap:
                    continue
                piece = _clip_to_new_road(candidate[j:], coverage, below=i + 1, keep_clear=keep_clear)
                added = _new_length(piece, coverage, below=i + 1)
                if best is None or added > best[0]:
                    best = (added, stage_name, is_reversed, piece, i, j, gap)
        if best is None or best[0] < min_new_length:
            break
        added, stage_name, is_reversed, piece, i, j, gap = best
        del samples[i + 1:]
        coverage.truncate(len(samples))
        if piece and math.dist(samples[-1], piece[0]) < 1e-6:
            piece = piece[1:]
        samples.extend(piece)
        for p in piece:
            coverage.add(p)
        pool.pop(stage_name)
        legs.append(RouteLeg(stage_name, is_reversed, j, j + len(piece), round(gap, 2), round(added, 1)))
    return StitchedRoute(name, samples, legs)


def resample_route(route: Sequence[Vec3], spacing: float = 20.0) -> list[Vec3]:
    """Uniform arc-length resampling (Retail median spacing is about 20)."""
    if len(route) < 2:
        return list(route)
    out = [route[0]]
    carry = 0.0
    for a, b in zip(route, route[1:]):
        seg = math.dist(a, b)
        if seg <= 1e-9:
            continue
        t = spacing - carry
        while t <= seg:
            f = t / seg
            out.append(tuple(a[k] + (b[k] - a[k]) * f for k in range(3)))  # type: ignore[arg-type]
            t += spacing
        carry = seg - (t - spacing)
    if math.dist(out[-1], route[-1]) > spacing * 0.25:
        out.append(route[-1])
    return out


def clear_route_end(route: Sequence[Vec3], *, clearance: float = 200.0, gap: float = 500.0,
                    tail: float = 120.0, max_trim: float = 0.3) -> list[Vec3]:
    """Shorten a route until its finish is away from every earlier part of it.

    The game counts a finish when the car enters the FinishArea while the route
    progress picks the last markers; a stitched route that passes within ~50
    units of its own finish earlier (InvSpain at 3.6 km) finished there. The
    last ``tail`` units must stay ``clearance`` (XZ) away from route points more
    than ``gap`` units of arc length earlier. At most ``max_trim`` of the length
    is removed; the full route is returned unchanged when that is not enough.
    """
    pts = list(route)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    limit = cum[-1] * (1.0 - max_trim)

    def clear(i: int) -> bool:
        return all(math.hypot(pts[i][0] - pts[j][0], pts[i][2] - pts[j][2]) >= clearance
                   for j in range(i) if cum[i] - cum[j] > gap)

    ok = [clear(i) for i in range(len(pts))]
    for end in range(len(pts) - 1, 0, -1):
        if cum[end] < limit:
            break
        if all(ok[i] for i in range(end + 1) if cum[end] - cum[i] <= tail):
            return pts[:end + 1]
    return pts


def snap_route_end(route: Sequence[Vec3], anchors: Sequence[tuple[float, float]], *, max_back: float = 400.0,
                   max_offset: float = 30.0, clearance: float = 200.0, gap: float = 500.0) -> list[Vec3]:
    """End the route at a Retail start/finish gantry it drives through near its end.

    ``anchors`` are XZ centres of Retail StartArea/FinishArea lists. The latest
    anchor within ``max_offset`` of the route and at most ``max_back`` before
    its end, whose position is ``clearance`` away from route parts more than
    ``gap`` earlier, becomes the new end (projected onto the route), so the
    FinishArea sits at the visible finish line. Without one the route is kept.
    """
    pts = list(route)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    best = None
    for ax, az in anchors:
        k = min(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - ax, pts[i][2] - az))
        if math.hypot(pts[k][0] - ax, pts[k][2] - az) > max_offset or cum[-1] - cum[k] > max_back or k < 2:
            continue
        if any(math.hypot(pts[k][0] - pts[j][0], pts[k][2] - pts[j][2]) < clearance
               for j in range(k) if cum[k] - cum[j] > gap):
            continue
        if best is None or k > best:
            best = k
    return pts if best is None else pts[:best + 1]


# --------------------------------------------------------------------------- crop / export


def crop_to_corridor(atlas: CountryAtlas, route: Sequence[Vec3], radius: float) -> list[AtlasTriangle]:
    """Keep triangles whose X/Z centroid lies within ``radius`` of the route."""
    index = _CoverageIndex(cell=max(8.0, radius / 2.0))
    for p in resample_route(route, spacing=max(4.0, radius / 4.0)):
        index.add(p)
    kept = []
    for tri in atlas.triangles:
        c = tuple(sum(p[k] for p in tri.positions) / 3.0 for k in range(3))
        if index.covered(c, radius):  # type: ignore[arg-type]
            kept.append(tri)
    return kept


def translate_route(route: Sequence[Vec3], offset: Vec3, yaw_degrees: float = 0.0, pivot: Vec3 = (0.0, 0.0, 0.0)) -> list[Vec3]:
    c, s = math.cos(math.radians(yaw_degrees)), math.sin(math.radians(yaw_degrees))
    out = []
    for x, y, z in route:
        rx, rz = x - pivot[0], z - pivot[2]
        out.append((pivot[0] + rx * c - rz * s + offset[0], y + offset[1], pivot[2] + rx * s + rz * c + offset[2]))
    return out


def write_atlas_obj(
    triangles: Sequence[AtlasTriangle],
    output_dir: Path,
    *,
    stem: str,
    textures: dict[str, Path] | None = None,
    decode_textures: bool = False,
    offset: Vec3 = (0.0, 0.0, 0.0),
) -> Path:
    """Write a Blender-friendly OBJ/MTL grouped by texture.

    Coordinates stay in DX/course space; Blender's default OBJ import axes
    (forward -Z, up Y) produce the repository's established ``(X, -Z, Y)``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    obj_path = output_dir / f"{stem}.obj"
    mtl_path = output_dir / f"{stem}.mtl"
    by_texture: dict[str, list[AtlasTriangle]] = {}
    for tri in triangles:
        by_texture.setdefault(tri.texture, []).append(tri)
    png_for: dict[str, str] = {}
    if decode_textures and textures:
        from .dxt import PNG_ROWS_FLIP_VERTICAL, parse_dxt, write_png

        tex_dir = output_dir / "textures"
        tex_dir.mkdir(exist_ok=True)
        for name in by_texture:
            source = textures.get(name)
            if source is None:
                continue
            png = tex_dir / f"{name}.png"
            if not png.exists():
                write_png(parse_dxt(source), png, row_policy=PNG_ROWS_FLIP_VERTICAL)
            png_for[name] = f"textures/{name}.png"
    with mtl_path.open("w", encoding="utf-8", newline="\n") as mtl:
        for name in by_texture:
            mtl.write(f"newmtl {name}\nKd 1 1 1\n")
            if name in png_for:
                mtl.write(f"map_Kd {png_for[name]}\n")
            mtl.write("\n")
    with obj_path.open("w", encoding="utf-8", newline="\n") as obj:
        obj.write(f"# Master Rallye course atlas concept: {stem}\nmtllib {mtl_path.name}\n")
        v = 1
        for name, tris in by_texture.items():
            obj.write(f"g {stem}_{name}\nusemtl {name}\n")
            for tri in tris:
                for p in tri.positions:
                    obj.write(f"v {p[0] + offset[0]:.3f} {p[1] + offset[1]:.3f} {p[2] + offset[2]:.3f}\n")
                if tri.uvs:
                    for u, w in tri.uvs:
                        obj.write(f"vt {u:.6f} {w:.6f}\n")
                    obj.write(f"f {v}/{v} {v + 1}/{v + 1} {v + 2}/{v + 2}\n")
                else:
                    obj.write(f"f {v} {v + 1} {v + 2}\n")
                v += 3
    return obj_path


def write_route_obj(routes: dict[str, Sequence[Vec3]], path: Path) -> Path:
    """Polylines (OBJ ``l`` records) for Blender route inspection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as obj:
        v = 1
        for name, route in routes.items():
            obj.write(f"o {name}\n")
            for x, y, z in route:
                obj.write(f"v {x:.3f} {y + 1.0:.3f} {z:.3f}\n")
            obj.write("l " + " ".join(str(v + k) for k in range(len(route))) + "\n")
            v += len(route)
    return path


START_DRESSING_TEXTURES = frozenset({"checks-tga", "stpf-tga", "masterlogo-tga", "go-tga"})


def degenerate_shared_triangles(
    dx_paths: Sequence[Path],
    *,
    hide_zones: Sequence[tuple[float, float, float]] = (),
    hide_textures: frozenset = START_DRESSING_TEXTURES,
) -> dict:
    """Hide render triangles in place by giving them zero area.

    * exact duplicates: a triangle whose rounded positions and primary texture
      match an earlier model's triangle (stages share bit-identical geometry);
    * near duplicates: same texture, centroid within 0.5 units and similar
      area as an earlier model's triangle (billboard trees that differ by a
      re-cook, which showed as doubled trees);
    * start/finish dressing: triangles with ``hide_textures`` whose centroid
      lies in one of ``hide_zones`` ``(x, z, radius)``, i.e. the start gantry
      and banners of a Retail stage start/finish the new route drives through.

    A hidden triangle gets its first uint16 local index three times: same file
    size, collision (tag100) and land database untouched. Duplicates inside one
    model (double-sided faces) are kept.
    """
    import struct

    seen: set = set()
    seen_near: set = set()
    report = {}
    for path in dx_paths:
        data = bytearray(path.read_bytes())
        model = parse_course_dx(path)
        positions = model.vertices.positions
        base = model.local_index_offset
        hidden = near_hidden = dressing = total = 0
        own: set = set()
        own_near: set = set()
        for draw in model.physical_draws:
            primary = next((slot.value for slot in draw.texture_slots if slot.value.lower() != "null"), "null")
            texture = _texture_basename(primary)
            global_indices = model.draw_global_indices(draw)
            for t in range(0, draw.index_count - 2, 3):
                total += 1
                face = global_indices[t:t + 3]
                pts = [positions[i] for i in face]
                key = (frozenset(_pos_key(q) for q in pts), texture)
                centroid = tuple(sum(q[k] for q in pts) / 3.0 for k in range(3))
                ux, uy, uz = (pts[1][k] - pts[0][k] for k in range(3))
                vx, vy, vz = (pts[2][k] - pts[0][k] for k in range(3))
                area = 0.5 * math.sqrt((uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2)
                near_key = (texture, round(centroid[0] * 2), round(centroid[1] * 2), round(centroid[2] * 2),
                            round(area * 2))
                reason = None
                if key in seen:
                    reason = "exact"
                elif near_key in seen_near:
                    reason = "near"
                elif texture in hide_textures and any(
                        (centroid[0] - x) ** 2 + (centroid[2] - z) ** 2 <= r * r for x, z, r in hide_zones):
                    reason = "dressing"
                if reason:
                    at = base + 2 * (draw.index_start + t)
                    first = struct.unpack_from("<H", data, at)[0]
                    struct.pack_into("<3H", data, at, first, first, first)
                    hidden += reason == "exact"
                    near_hidden += reason == "near"
                    dressing += reason == "dressing"
                else:
                    own.add(key)
                    own_near.add(near_key)
        seen |= own
        seen_near |= own_near
        path.write_bytes(bytes(data))
        report[path.name] = {"triangles": total, "hidden": hidden, "near_hidden": near_hidden,
                             "dressing_hidden": dressing}
    return report
