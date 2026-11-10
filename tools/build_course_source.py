"""Build one cookable GXM v7 course source from several Retail stages (R5T-INV E2).

The multi-landscape scenes proved that only the first landscape collides.
This tool merges the stages a route uses into ONE source model that the
game's own cooker turns into a single DX (render draws, tag100 collision,
tag1400 land database):

* render triangles of every stage DX, exact duplicates removed across stages
  (oriented positions + texture tuple), start/finish dressing of foreign
  stage areas and near-duplicate billboards dropped;
* triangles that also occur in the stage's land database (tag1400) go to
  ``$autovsphere_300/$bsp/$draw/$landdb`` with the land database's surface
  string as material name (``$surfacetype(...) $shader(ground)...``,
  ``walls $shader(object)``); water surfaces go to ``Water $water $landdb``;
* other ground-shader triangles join ``$landdb``; opaque ``$shader(object)``
  triangles (buildings, tyres, posts, fences) go to ``$bsp/$draw/solid
  objects`` so they collide (Retail used invisible ``$nodraw`` proxies, which
  compiled DX does not keep); trees, sprites and signs/banners go to
  ``$objects`` render-only, like Retail;
* textures: DXT -> GXI (top-down RGBA) next to the model; material slots
  reference them by absolute path with ``(present, HasAlpha, UsesAlpha)``
  controls from the stage TXT sidecars.

Coordinates: source = (dx.x, -dx.z, dx.y); colours BGRA bytes -> RGBA floats;
texcoord third component 0.5 (AI_Track source/compiled pair).
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from master_rallye.course_atlas import (  # noqa: E402
    START_DRESSING_TEXTURES, clear_route_end, read_marker_list, resample_route, snap_route_end)
from master_rallye.course_bsp import close_land  # noqa: E402
from master_rallye.course_entry import build_entry_racetest, replace_limit_lists, validated_limits  # noqa: E402
from master_rallye.course_gxm_writer import (  # noqa: E402
    GxmBuilder, GxmCorner, GxmGroup, GxmMaterial, GxmTextureSlot)
from master_rallye.course_sfl_field import grid_for_route, synthesize_pursuit_field  # noqa: E402
from master_rallye.course_tag1400 import parse_course_tag1400_bytes  # noqa: E402
from master_rallye.dx_course import parse_course_dx  # noqa: E402
from master_rallye.sidecar import normalize_texture_value, parse_sidecar  # noqa: E402

import invitation_concept as concept  # noqa: E402

STAGE_FOLDERS = {stem: folder for country in concept.COUNTRIES.values() for stem, folder in country.items()}


def land_database(dx_bytes: bytes):
    i = dx_bytes.rfind(struct.pack("<I", 1339))
    while i > 0 and struct.unpack_from("<I", dx_bytes, i + 44)[0] != 1400:
        i = dx_bytes.rfind(struct.pack("<I", 1339), 0, i)
    if i <= 0:
        raise ValueError("tag1339/tag1400 not found")
    return parse_course_tag1400_bytes(dx_bytes[i + 44:], allow_trailing=True)


def _k(p):
    return (round(p[0], 2), round(p[1], 2), round(p[2], 2))


def _oriented(keys):
    i = min(range(3), key=lambda j: keys[j])
    return keys[i:] + keys[:i]


def dxt_to_gxi(dxt: bytes) -> bytes:
    magic, version, crc, width, height = struct.unpack_from("<5I", dxt, 0)
    payload = dxt[20:]
    if len(payload) != width * height * 4:
        raise ValueError("unexpected DXT payload size")
    rows = [payload[r * width * 4:(r + 1) * width * 4] for r in range(height)]
    out = bytearray(struct.pack("<IHH", 0x00013039, width, height))
    for row in reversed(rows):  # DXT rows are bottom-up BGRA; GXI is top-down RGBA
        px = bytearray(row)
        px[0::4], px[2::4] = row[2::4], row[0::4]
        out += px
    return bytes(out)


def gantry_centres(racetest: Path, stems):
    """XZ centres of the StartArea/FinishArea lists of Retail stages."""
    out = []
    for stem in stems:
        root = ET.parse(racetest / f"{stem}.xml").getroot()
        for name in ("FinishArea", "StartArea"):
            pts = [tuple(map(float, v.get("Value").split())) for lst in root.iter("List") if lst.get("Name") == name
                   for v in lst.iter("Value") if v.get("Name") == "Marker Pos"]
            if pts:
                out.append((sum(p[0] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts)))
    return out


# Start/finish dressing of the Retail stages: removed around old start/finish
# areas the new route does not use (gantries, banner lines, tyre walls, service
# park). Buildings, palms, trees, fences and road guides stay.
DRESSING_PREFIXES = ("checks", "stpf", "masterlogo", "go-tga", "burago", "tent", "mrtruck", "tsidew", "tfront",
                     "top-tga", "drum", "crate", "ctyre", "wheel", "i2a_planks2", "yaught", "sweede boat")


def is_dressing(texture: str, material_name: str) -> bool:
    if texture.startswith(DRESSING_PREFIXES):
        return True
    return "$shader(sign)" in material_name and not texture.startswith("road guides")


def is_vegetation(texture: str, material_name: str) -> bool:
    if texture.startswith("fencegate"):
        return False
    return "$shader(tree)" in material_name or material_name.startswith(("trunk", "palm"))


def stage_zones(racetest: Path, stems, route, radius=100.0, keep=200.0):
    zones, ends = [], (route[0], route[-1])
    for stem in stems:
        root = ET.parse(racetest / f"{stem}.xml").getroot()
        for name in ("StartArea", "FinishArea"):
            pts = [tuple(map(float, v.get("Value").split())) for lst in root.iter("List") if lst.get("Name") == name
                   for v in lst.iter("Value") if v.get("Name") == "Marker Pos"]
            if pts:
                cx, cz = sum(p[0] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts)
                if all(math.hypot(cx - e[0], cz - e[2]) > keep for e in ends):
                    zones.append((cx, cz, radius))
    return zones


def merge_land_surfaces(stage_lands, cell: float = 10.0, owner=None, tolerance: float = 1e9,
                        steep_tolerance: float = 1e9):
    """One non-overlapping collision surface from per-stage land databases.

    Stages are corridors of one master map: interior triangles are mostly
    bit-identical, but each stage re-triangulated its cut border and some areas
    differ between stages by several units of height (SpainW vs the other Spain
    stages near (2633, -187): 1.5-4 units). A plain union overlaps along every
    seam and stacks layers. Triangles are taken by priority: first those whose
    centroid lies in the area ``owner(x, z)`` assigns to their stage (the stage
    the new route drives there), then the rest in stage order. A triangle is
    dropped when its centroid or a shrunk corner lies on an already accepted
    triangle of another stage within ``tolerance`` units of height (steep
    faces: ``steep_tolerance``). Returns {key: (triangle, name, stage)}
    and the keys that were dropped as overlaps.
    """
    accepted: dict = {}
    order: list = []
    grid: dict = {}
    dropped: set = set()

    def height_on(px, pz, t):
        (ax, _, az), (bx, _, bz), (cx, _, cz) = t
        d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        if abs(d) < 1e-9:
            return None
        l1 = ((bz - cz) * (px - cx) + (cx - bx) * (pz - cz)) / d
        l2 = ((cz - az) * (px - cx) + (ax - cx) * (pz - cz)) / d
        l3 = 1 - l1 - l2
        if min(l1, l2, l3) < -1e-4:
            return None
        return l1 * t[0][1] + l2 * t[1][1] + l3 * t[2][1]

    queue = []
    for rank, (stage, triangles) in enumerate(stage_lands):
        for t, name in triangles:
            c = [sum(p[i] for p in t) / 3 for i in range(3)]
            owned = owner is not None and owner(c[0], c[2]) == stage
            queue.append((0 if owned else 1, rank, t, name, stage))
    queue.sort(key=lambda item: (item[0], item[1]))
    for _, _, t, name, stage in queue:
        key = frozenset(t)
        if key in accepted:
            continue
        ux, uy, uz = (t[1][i] - t[0][i] for i in range(3))
        vx, vy, vz = (t[2][i] - t[0][i] for i in range(3))
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        hit = False
        # Steep faces (cliffs) of a stage whose terrain differs from the one
        # already accepted there would stand inside that terrain: test them
        # too, with a wider height window.
        window = tolerance if abs(ny / length) >= 0.2 else steep_tolerance
        c = [sum(p[i] for p in t) / 3 for i in range(3)]
        for q in [c] + [[c[i] + 0.9 * (p[i] - c[i]) for i in range(3)] for p in t]:
            for j in grid.get((int(q[0] // cell), int(q[2] // cell)), ()):
                if order[j][2] == stage:
                    continue  # a stage is never overlap-tested against itself
                h = height_on(q[0], q[2], order[j][0])
                if h is not None and abs(h - q[1]) < window:
                    hit = True
                    break
            if hit:
                break
        if hit:
            dropped.add(key)
            continue
        item = (t, name, stage)
        accepted[key] = item
        order.append(item)
        xs, zs = [p[0] for p in t], [p[2] for p in t]
        for gx in range(int(min(xs) // cell), int(max(xs) // cell) + 1):
            for gz in range(int(min(zs) // cell), int(max(zs) // cell) + 1):
                grid.setdefault((gx, gz), []).append(len(order) - 1)
    return accepted, dropped - set(accepted)


def route_owner(route, legs, racelines, *, near: float = 10.0, radius: float = 150.0, cell: float = 25.0):
    """owner(x, z): the stage whose leg the route drives nearest to (x, z).

    Route samples are walked in order; the current leg advances to the next
    leg's stage once the route leaves the current stage's RaceLine while it is
    on the next one's.
    """
    def near_line(p, line):
        return min(math.hypot(p[0] - q[0], p[2] - q[2]) for q in line) <= near

    dense = {stage: resample_route(line, 5.0) for stage, line in racelines.items()}
    current, owners = 0, []
    for p in route:
        while (current + 1 < len(legs) and near_line(p, dense[legs[current + 1]])
               and not near_line(p, dense[legs[current]])):
            current += 1
        owners.append(legs[current])
    grid: dict = {}
    for p, stage in zip(route, owners):
        grid.setdefault((int(p[0] // cell), int(p[2] // cell)), []).append((p, stage))
    reach = int(radius // cell) + 1

    def owner(x, z):
        best, found = radius, None
        gx, gz = int(x // cell), int(z // cell)
        for i in range(gx - reach, gx + reach + 1):
            for k in range(gz - reach, gz + reach + 1):
                for p, stage in grid.get((i, k), ()):
                    d = math.hypot(p[0] - x, p[2] - z)
                    if d < best:
                        best, found = d, stage
        return found

    return owner, owners


def _hull_2d(points):
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def min_area_rect(points):
    """(centre_x, centre_z, axis_angle, half_u, half_v) of the smallest XZ rectangle."""
    hull = _hull_2d(points)
    if len(hull) < 2:
        x, z = hull[0]
        return x, z, 0.0, 0.0, 0.0
    best = None
    for i in range(len(hull)):
        (x0, z0), (x1, z1) = hull[i], hull[(i + 1) % len(hull)]
        angle = math.atan2(z1 - z0, x1 - x0)
        ca, sa = math.cos(angle), math.sin(angle)
        us = [x * ca + z * sa for x, z in hull]
        vs = [-x * sa + z * ca for x, z in hull]
        area = (max(us) - min(us)) * (max(vs) - min(vs))
        if best is None or area < best[0]:
            cu, cv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
            best = (area, cu * ca - cv * sa, cu * sa + cv * ca, angle,
                    (max(us) - min(us)) / 2, (max(vs) - min(vs)) / 2)
    return best[1:]


def surface_samples(tri, spacing: float = 0.75):
    """Points covering a DX-space triangle about every ``spacing`` units."""
    a, b, c = tri
    longest = max(math.dist(a, b), math.dist(b, c), math.dist(c, a))
    steps = max(1, math.ceil(longest / spacing))
    out = []
    for i in range(steps + 1):
        for j in range(steps + 1 - i):
            u, v = i / steps, j / steps
            w = 1.0 - u - v
            out.append(tuple(a[k] * w + b[k] * u + c[k] * v for k in range(3)))
    return out


def _components(triangles):
    parent: dict = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for tri in triangles:
        keys = [_k(p) for p in tri]
        for other in keys[1:]:
            ra, rb = find(keys[0]), find(other)
            if ra != rb:
                parent[ra] = rb
    groups: dict = {}
    for index, tri in enumerate(triangles):
        groups.setdefault(find(_k(tri[0])), []).append(index)
    return list(groups.values())


def clear_road(triangles, route, ground, *, corridor: float = 3.5, clearance: float = 2.0,
               gap: float = 0.5, max_cluster: float = 40.0, protect: set | None = None):
    """Indices of object triangles standing ON the new route (old start/finish dressing).

    Objects are connected components, clustered with neighbours whose bounding
    boxes touch (a truck = body, wheels, tent). A cluster is removed when any of
    its surface points lies within ``corridor`` of the route centreline and lower
    than ``clearance`` above the ground there; overhead banners and gantries stay.
    Clusters longer than ``max_cluster`` (fence lines) are judged per component.
    """
    protect = protect or set()
    comps = [c for c in _components(triangles) if not any(i in protect for i in c)]
    boxes = []
    for comp in comps:
        pts = [p for i in comp for p in triangles[i]]
        boxes.append((min(p[0] for p in pts) - gap, max(p[0] for p in pts) + gap,
                      min(p[2] for p in pts) - gap, max(p[2] for p in pts) + gap))
    parent = list(range(len(comps)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    cell = 10.0
    cells: dict = {}
    for index, (x0, x1, z0, z1) in enumerate(boxes):
        for gx in range(int(x0 // cell), int(x1 // cell) + 1):
            for gz in range(int(z0 // cell), int(z1 // cell) + 1):
                for other in cells.get((gx, gz), ()):
                    o = boxes[other]
                    if x0 <= o[1] and o[0] <= x1 and z0 <= o[3] and o[2] <= z1:
                        ra, rb = find(index), find(other)
                        if ra != rb:
                            parent[ra] = rb
                cells.setdefault((gx, gz), []).append(index)
    clusters: dict = {}
    for index in range(len(comps)):
        clusters.setdefault(find(index), []).append(index)
    units = []
    for members in clusters.values():
        x0, x1 = min(boxes[m][0] for m in members), max(boxes[m][1] for m in members)
        z0, z1 = min(boxes[m][2] for m in members), max(boxes[m][3] for m in members)
        if max(x1 - x0, z1 - z0) > max_cluster:
            units += [[m] for m in members]
        else:
            units.append(members)
    rcell = 20.0
    route_grid: dict = {}
    for q in route:
        route_grid.setdefault((int(q[0] // rcell), int(q[2] // rcell)), []).append(q)

    def on_road(p):
        for gx in (int(p[0] // rcell) - 1, int(p[0] // rcell), int(p[0] // rcell) + 1):
            for gz in (int(p[2] // rcell) - 1, int(p[2] // rcell), int(p[2] // rcell) + 1):
                for q in route_grid.get((gx, gz), ()):
                    if math.hypot(p[0] - q[0], p[2] - q[2]) <= corridor:
                        h = ground(p[0], p[2], p[1] + 1.0)
                        return p[1] < (h if h is not None else q[1]) + clearance
        return False

    dropped: set = set()
    for members in units:
        if any(on_road(p) for m in members for i in comps[m] for p in surface_samples(triangles[i], 1.0)):
            dropped.update(i for m in members for i in comps[m])
    return dropped


def _touching_clusters(groups, gap: float = 0.3):
    """Join components whose bounding boxes touch (fence rails + posts, tyre stacks)."""
    boxes = []
    for tris in groups:
        pts = [p for tri in tris for p in tri]
        boxes.append((min(p[0] for p in pts) - gap, max(p[0] for p in pts) + gap,
                      min(p[2] for p in pts) - gap, max(p[2] for p in pts) + gap))
    parent = list(range(len(groups)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    cell, cells = 10.0, {}
    for index, (x0, x1, z0, z1) in enumerate(boxes):
        for gx in range(int(x0 // cell), int(x1 // cell) + 1):
            for gz in range(int(z0 // cell), int(z1 // cell) + 1):
                for other in cells.get((gx, gz), ()):
                    o = boxes[other]
                    if x0 <= o[1] and o[0] <= x1 and z0 <= o[3] and o[2] <= z1:
                        ra, rb = find(index), find(other)
                        if ra != rb:
                            parent[ra] = rb
                cells.setdefault((gx, gz), []).append(index)
    out: dict = {}
    for index, tris in enumerate(groups):
        out.setdefault(find(index), []).extend(tris)
    return list(out.values())


def _tile_boxes(tris, ground, tile, min_half, skipped, route_grid, cell, road_clear):
    """Boxes standing ON the land, one per world tile, shaped by what a car can hit.

    * a box reaching below the land leaves its planes underground (pockets under
      posts and tyres), so every box starts 0.1 above the highest land under it;
    * only object surface within 3 units above the land counts (palm crowns over
      the road made walls); the box top is the highest surface in the tile;
    * each tile's box has its own orientation (a curved fence becomes a chain of
      thin boxes) and is stretched to the tile border where the object goes on,
      so neighbouring boxes meet instead of leaving gaps that snag the car.
    """
    samples = [q for tri in tris for q in surface_samples(tri, 0.5)]
    cells: dict = {}
    for q in samples:
        key = (int(q[0] // tile), int(q[2] // tile))
        entry = cells.setdefault(key, [[], -math.inf])
        entry[1] = max(entry[1], q[1])
        h = ground(q[0], q[2], q[1] + 1.0)
        if h is not None and q[1] <= h + 3.0:
            entry[0].append((q[0], q[2]))
    out = []
    for (ix, iz), (low, top) in cells.items():
        if len(low) < 2:
            continue
        x0, z0 = ix * tile, iz * tile
        bx, bz, angle, bu, bv = min_area_rect([(round(x, 3), round(z, 3)) for x, z in low])
        if bv > bu:
            angle, bu, bv = angle + math.pi / 2, bv, bu
        ca, sa = math.cos(angle), math.sin(angle)
        # extend the long axis to the tile border where the object continues
        limits = []
        for d, o, lo, hi in ((ca, bx, x0, x0 + tile), (sa, bz, z0, z0 + tile)):
            if abs(d) < 1e-9:
                continue
            t1, t2 = (lo - o) / d, (hi - o) / d
            limits.append((min(t1, t2), max(t1, t2)))
        t_lo = max(l[0] for l in limits) if limits else -bu
        t_hi = min(l[1] for l in limits) if limits else bu
        lo_end, hi_end = -bu, bu
        if t_hi - bu < 0.9:
            hi_end = max(bu, t_hi)
        if -bu - t_lo < 0.9:
            lo_end = min(-bu, t_lo)
        mid = (lo_end + hi_end) / 2
        bx, bz = bx + mid * ca, bz + mid * sa
        bu = max((hi_end - lo_end) / 2, min_half)
        bv = max(bv + 0.1, min_half)
        corners = [(bx + su * bu * ca - sv * bv * sa, bz + su * bu * sa + sv * bv * ca)
                   for su in (-1, -0.5, 0, 0.5, 1) for sv in (-1, 0, 1)]
        hs = [h for h in (ground(x, z, top) for x, z in corners) if h is not None]
        if not hs:
            continue
        bottom = max(hs) + 0.1
        if top - bottom < 0.3:
            skipped["low"] += 1
            continue
        blocked = False
        reach = bu + road_clear
        for gx in range(int((bx - reach) // cell), int((bx + reach) // cell) + 1):
            for gz in range(int((bz - reach) // cell), int((bz + reach) // cell) + 1):
                for p in route_grid.get((gx, gz), ()):
                    du = (p[0] - bx) * ca + (p[2] - bz) * sa
                    dv = -(p[0] - bx) * sa + (p[2] - bz) * ca
                    if abs(du) <= bu + road_clear and abs(dv) <= bv + road_clear and bottom - 3 <= p[1] <= top + 3:
                        blocked = True
        if blocked:
            skipped["over_road_tiles"] += 1  # gantries, banners and bridges over the road
            continue
        out.append((bx, bz, angle, bu, bv, bottom, top))
    return out


def collision_boxes(triangles, route, *, max_size=40.0, min_height=0.5, min_half=0.15, road_clear=2.5,
                    ground=None, tile=3.0):
    """Closed box proxies for opaque objects (Retail used 12-triangle $nodraw boxes).

    ``triangles`` are DX-space corner triples. Connected components (shared
    positions) get one oriented box each; boxes longer than ``max_size``, lower
    than ``min_height`` or reaching within ``road_clear`` of the route centreline
    at drivable height (gantries, banners, bridges) are skipped.
    """
    parent: dict = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for tri in triangles:
        keys = [_k(p) for p in tri]
        for other in keys[1:]:
            ra, rb = find(keys[0]), find(other)
            if ra != rb:
                parent[ra] = rb
    groups: dict = {}
    for tri in triangles:
        groups.setdefault(find(_k(tri[0])), []).append(tri)
    cell = 20.0
    route_grid: dict = {}
    for p in route:
        route_grid.setdefault((int(p[0] // cell), int(p[2] // cell)), []).append(p)
    boxes, skipped, tiled = [], Counter(), []
    for tris in groups.values():
        pts = [p for tri in tris for p in tri]
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        if ground is None and y1 - y0 < min_height:
            skipped["flat"] += 1
            continue
        cx, cz, angle, hu, hv = min_area_rect([(round(p[0], 3), round(p[2], 3)) for p in pts])
        if ground is None and 2 * max(hu, hv) > max_size:
            skipped["large"] += 1  # untiled boxes only; tiles follow the object's shape
            continue
        hu, hv = max(hu, min_half), max(hv, min_half)
        ca, sa = math.cos(angle), math.sin(angle)

        def over_road(bx, bz, bu, bv, lo, hi, ca=ca, sa=sa):
            reach = max(bu, bv) + road_clear
            for gx in range(int((bx - reach) // cell), int((bx + reach) // cell) + 1):
                for gz in range(int((bz - reach) // cell), int((bz + reach) // cell) + 1):
                    for p in route_grid.get((gx, gz), ()):
                        du = (p[0] - bx) * ca + (p[2] - bz) * sa
                        dv = -(p[0] - bx) * sa + (p[2] - bz) * ca
                        if abs(du) <= bu + road_clear and abs(dv) <= bv + road_clear and lo - 3 <= p[1] <= hi + 3:
                            return True
            return False

        if ground is None:
            if over_road(cx, cz, hu, hv, y0, y1):
                skipped["over_road"] += 1
            else:
                boxes.append((cx, cz, angle, hu, hv, y0, y1))
            continue
        tiled.append(tris)
    if ground is not None:
        for tris in _touching_clusters(tiled):
            boxes += _tile_boxes(tris, ground, tile, min_half, skipped, route_grid, cell, road_clear)
    return boxes, dict(skipped)


def ground_sampler(triangles, cell: float = 10.0):
    """height(x, z, below) of the highest DX-space surface triangle under ``below + 1``."""
    grid: dict = {}
    for j, t in enumerate(triangles):
        xs, zs = [p[0] for p in t], [p[2] for p in t]
        for gx in range(int(min(xs) // cell), int(max(xs) // cell) + 1):
            for gz in range(int(min(zs) // cell), int(max(zs) // cell) + 1):
                grid.setdefault((gx, gz), []).append(j)

    def height(x, z, below):
        best = None
        for j in grid.get((int(x // cell), int(z // cell)), ()):
            (ax, ay, az), (bx, by, bz), (qx, qy, qz) = triangles[j]
            d = (bz - qz) * (ax - qx) + (qx - bx) * (az - qz)
            if abs(d) < 1e-9:
                continue
            l1 = ((bz - qz) * (x - qx) + (qx - bx) * (z - qz)) / d
            l2 = ((qz - az) * (x - qx) + (ax - qx) * (z - qz)) / d
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) < -1e-6:
                continue
            h = l1 * ay + l2 * by + l3 * qy
            if h <= below + 1.0 and (best is None or h > best):
                best = h
        return best

    return height


def box_triangles(box):
    """12 source-space triangles with outward normals by the right-hand rule (Retail Mesh07)."""
    cx, cz, angle, hu, hv, y0, y1 = box
    ca, sa = math.cos(angle), math.sin(angle)
    ring = [(cx + su * hu * ca - sv * hv * sa, cz + su * hu * sa + sv * hv * ca)
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lo = [(x, -z, y0) for x, z in ring]  # source space = (dx.x, -dx.z, dx.y)
    hi = [(x, -z, y1) for x, z in ring]
    if (lo[1][0] - lo[0][0]) * (lo[2][1] - lo[0][1]) - (lo[1][1] - lo[0][1]) * (lo[2][0] - lo[0][0]) < 0:
        lo.reverse()
        hi.reverse()  # make the ring counter-clockwise seen from +Z (up)
    faces = [(lo[0], lo[2], lo[1]), (lo[0], lo[3], lo[2]), (hi[0], hi[1], hi[2]), (hi[0], hi[2], hi[3])]
    for i in range(4):
        j = (i + 1) % 4
        faces += [(lo[i], lo[j], hi[j]), (lo[i], hi[j], hi[i])]
    return faces


def _face_normal(tri):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    ux, uy, uz, vx, vy, vz = bx - ax, by - ay, bz - az, cx - ax, cy - ay, cz - az
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    length = math.sqrt(sum(c * c for c in n)) or 1.0
    return tuple(c / length for c in n)


def write_scene(scene_root: Path, entry: str, name: str, route, saved, racetest: Path, textures) -> dict:
    """RaceTest XML/HNT and SFL for a single-landscape entry on the cooked model."""
    legs = saved["route"]["legs"]
    model = "course\\{0}\\{0}".format(name)
    xml, report = build_entry_racetest(racetest / f"{legs[0]['stage']}.xml", entry_name=entry, model_name=model,
                                       route=route, source_xmls=[racetest / f"{leg['stage']}.xml" for leg in legs])
    samples = resample_route(route, 20.0)
    limits, report["limits"] = validated_limits(samples, [(racetest / f"{leg['stage']}.xml", bool(leg["reversed"]))
                                                          for leg in legs])
    (scene_root / "RaceTest").mkdir(parents=True, exist_ok=True)
    (scene_root / "ICont").mkdir(parents=True, exist_ok=True)
    (scene_root / "RaceTest" / f"{entry}.xml").write_bytes(replace_limit_lists(xml, limits))
    lines = [f"Model\t[{model}]"] + [f"Texture\t[course\\{name}\\{t}]" for t in textures]
    (scene_root / "RaceTest" / f"{entry}.hnt").write_bytes(("\r\n".join(lines) + "\r\n").encode("latin-1"))
    (scene_root / "ICont" / f"{entry.lower()}.sfl").write_bytes(synthesize_pursuit_field(samples, grid_for_route(samples), lookahead=12.0))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--country", default="Spain")
    parser.add_argument("--name", default=None, help="course folder/model name (default inv<country>gx)")
    parser.add_argument("--retail", type=Path, default=ROOT.parent / "corpora/retail/Data.sma_unpacked")
    parser.add_argument("--concept", type=Path, default=ROOT / "research-output/invitation_concept")
    parser.add_argument("--output", type=Path, default=ROOT / "research-output/invitation_concept/source")
    parser.add_argument("--install-root", default="D:/Game/Master Rallye",
                        help="game root the GXI references point at (absolute authoring paths)")
    args = parser.parse_args()
    name = (args.name or f"inv{args.country.lower()}gx").lower()
    entry = f"Inv{args.country}"
    course_root = args.retail / "DataGx/Course"
    racetest = args.retail / "DataScene/RaceTest"
    saved = json.loads((args.concept / entry / f"{entry}_route.json").read_text(encoding="utf-8"))
    route = clear_route_end([tuple(p) for p in saved["samples"]])  # finish away from earlier route
    route = snap_route_end(route, gantry_centres(racetest, list(dict.fromkeys(
        leg["stage"] for leg in saved["route"]["legs"]))))  # finish at a visible Retail finish line
    legs = list(dict.fromkeys(leg["stage"] for leg in saved["route"]["legs"]))
    out_dir = args.output / "DataGx/Course" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    zones = stage_zones(racetest, legs, route)

    materials: list[GxmMaterial] = []
    material_index: dict[tuple, int] = {}
    textures: dict[str, Path] = {}
    seen: set = set()
    seen_near: set = set()
    buckets = {"landdb": [], "water": [], "solid": [], "terrain": [], "objects": []}
    stats = {"stages": {}, "dropped_dressing": 0, "dropped_duplicates": 0, "dropped_near": 0,
             "dropped_overlap_render": 0}
    solid_dx: list = []
    objects_dx: list = []
    solid_veg: list = []
    objects_veg: list = []
    terrain_dx: list = []

    def material_for(name_text: str, draw, sidecar_material):
        slots = []
        flags = {t.slot: t for t in (sidecar_material.textures if sidecar_material else [])}
        for slot_index, slot in enumerate(draw.texture_slots[:3]):
            stem = normalize_texture_value(slot.value)
            if stem == "null":
                slots.append(GxmTextureSlot())
                continue
            src = folder_dxt.get(stem)
            textures.setdefault(stem, src)
            info = flags.get(slot_index)
            slots.append(GxmTextureSlot(f"{args.install_root}/DataGx/Course/{name}/{stem}.gxi",
                                        bool(info and info.has_alpha), bool(info and info.uses_alpha),
                                        bool(info and info.is_noise)))
        while len(slots) < 3:
            slots.append(GxmTextureSlot())
        key = (name_text, tuple((s.reference, s.has_alpha, s.uses_alpha) for s in slots))
        if key not in material_index:
            material_index[key] = len(materials)
            materials.append(GxmMaterial(name_text, slots))
        return material_index[key]

    stage_lands = []
    for stem in legs:
        land = land_database(next((course_root / STAGE_FOLDERS[stem]).glob("*.dx")).read_bytes())
        land_names = [s.raw_bytes.decode("latin-1") for s in land.strings]
        stage_lands.append((stem, [((_k(r.float_prefix[0:3]), _k(r.float_prefix[3:6]), _k(r.float_prefix[6:9])),
                                    land_names[r.string_ref_index]) for r in land.records]))
    racelines = {stem: read_marker_list(racetest / f"{stem}.xml", "RaceLine") for stem in legs}
    owner, owners = route_owner(resample_route(route, 10.0), [leg["stage"] for leg in saved["route"]["legs"]],
                                racelines)
    stats["route_owners"] = {stem: owners.count(stem) for stem in legs}
    surface, overlap = merge_land_surfaces(stage_lands, owner=owner)
    emitted: set = set()
    print(f"collision surface {len(surface)} triangles, {len(overlap)} seam overlaps dropped", flush=True)

    for stem in legs:
        folder = STAGE_FOLDERS[stem]
        dx_path = next((course_root / folder).glob("*.dx"))
        model = parse_course_dx(dx_path)
        folder_dxt = {p.stem.lower(): p for p in (course_root / folder).glob("*.dxt")}
        sidecar = parse_sidecar(next((course_root / folder).glob("*.txt")))
        land = next(triangles for name, triangles in stage_lands if name == stem)
        positions, normals, colors = model.vertices.positions, model.vertices.normals, model.vertices.colors
        uv0 = model.uv_sets[0].values if model.uv_sets else None
        kept = 0
        own, own_near = set(), set()
        for draw in model.physical_draws:
            actual = tuple(normalize_texture_value(s.value) for s in draw.texture_slots)
            candidates = []
            for material in sidecar.materials:
                v = ["null"] * len(actual)
                for t in material.textures:
                    if t.slot < len(actual):
                        v[t.slot] = t.resource_stem
                if tuple(v) == actual:
                    candidates.append(material)
            texture = actual[0] if actual else "null"
            indices = model.draw_global_indices(draw)
            for t in range(0, len(indices) - 2, 3):
                face = indices[t:t + 3]
                keys = tuple(_k(positions[i]) for i in face)
                key = (_oriented(keys), actual)
                centroid = tuple(sum(positions[i][c] for i in face) / 3 for c in range(3))
                near_key = (texture, round(centroid[0] * 2), round(centroid[1] * 2), round(centroid[2] * 2))
                if key in seen:
                    stats["dropped_duplicates"] += 1
                    continue
                if near_key in seen_near:
                    stats["dropped_near"] += 1
                    continue
                face_material = candidates[0].name if candidates else ""
                if (texture in START_DRESSING_TEXTURES or is_dressing(texture, face_material)) and any(
                        (centroid[0] - x) ** 2 + (centroid[2] - z) ** 2 <= r * r for x, z, r in zones):
                    stats["dropped_dressing"] += 1
                    continue
                own.add(key)
                own_near.add(near_key)
                land_key = frozenset(keys)
                if land_key in overlap or (land_key in surface and land_key in emitted):
                    stats["dropped_overlap_render"] += 1  # seam overlap: neither collide nor draw it
                    continue
                land_name = surface[land_key][1] if land_key in surface else None
                if land_name is not None:
                    emitted.add(land_key)
                    match = next((m for m in candidates if m.name == land_name), candidates[0] if candidates else None)
                    mat = material_for(land_name, draw, match)
                    bucket = "water" if "$shader(water)" in land_name or "surfacetype(water)" in land_name else "landdb"
                else:
                    match = candidates[0] if candidates else None
                    material_name = match.name if match else "untextured $shader(object)"
                    mat = material_for(material_name, draw, match)
                    if "$shader(ground)" in material_name:
                        bucket = "terrain"  # ground outside the land database: render-only
                        terrain_dx.append((centroid, _face_normal([positions[i] for i in face])))
                    elif ((any(f"$shader({kind})" in material_name for kind in ("object", "metal", "sign"))
                           and "$alphatest" not in material_name) or texture.startswith("fencegate")):
                        # opaque objects, metal (trucks), signs (banners, arrows) and
                        # fence gates: render-only, collide through box proxies
                        bucket = "solid"
                        solid_dx.append(tuple(positions[i] for i in face))
                        solid_veg.append(is_vegetation(texture, material_name))
                    else:
                        bucket = "objects"  # trees, sprites: render-only
                        objects_dx.append(tuple(positions[i] for i in face))
                        objects_veg.append(is_vegetation(texture, material_name))
                corners = []
                for i in face:
                    p, n = positions[i], normals[i]
                    b, g, r, a = colors[i * 4:i * 4 + 4]
                    uv = uv0[i] if uv0 else None
                    corners.append(GxmCorner((p[0], -p[2], p[1]), (n[0], -n[2], n[1]),
                                             (uv[0], uv[1], 0.5) if uv else None,
                                             (r / 255.0, g / 255.0, b / 255.0, a / 255.0)))
                if land_name is not None and _oriented(keys) == _oriented(surface[land_key][0]):
                    # Land records wind opposite to the source surface (cooker convention);
                    # a render triangle wound like its record would face down in $bsp.
                    corners.reverse()
                    stats["flipped_land"] = stats.get("flipped_land", 0) + 1
                buckets[bucket].append((mat, corners))
                kept += 1
        seen |= own
        seen_near |= own_near
        stats["stages"][stem] = {"kept_triangles": kept, "render_triangles": model.triangle_count,
                                 "land_records": len(land)}
        print(f"[{stem}] kept {kept}/{model.triangle_count}", flush=True)

    # Collision-only parts: land records without a render triangle, and box proxies.
    fill = []
    for land_key, (t, land_name, _stage) in surface.items():
        if land_key in emitted or "surfacetype(water)" in land_name or "$shader(water" in land_name:
            continue
        if abs(_face_normal(t)[1]) < 0.7:
            # Undrawn steep land records are the invisible blockers that close a
            # Retail stage's road at its ends; on a merged route they stand across
            # the road (owner's one-sided "invisible-coll-wall").
            stats["dropped_stage_blockers"] = stats.get("dropped_stage_blockers", 0) + 1
            continue
        # Draw it with a textured material of the same land name (planar UVs),
        # an undrawn piece shows as a hole in the ground ("triangle-tears").
        drawn = next((i for (name, slots), i in material_index.items()
                      if name == land_name and slots[0][0] != "Null"), None)
        if drawn is None:
            drawn = material_index.setdefault((land_name, (("Null", False, False),) * 3), len(materials))
            if drawn == len(materials):
                materials.append(GxmMaterial(land_name, [GxmTextureSlot(), GxmTextureSlot(), GxmTextureSlot()]))
        src = [(q[0], -q[2], q[1]) for q in reversed(t)]  # record winding is reversed
        n = _face_normal(src)
        fill.append((drawn, [GxmCorner(q, n, (q[0] / 16.0, q[1] / 16.0, 0.5), (1.0, 1.0, 1.0, 1.0)) for q in src]))
    route_dense = resample_route(route, 2.0)
    ground = ground_sampler([t for t, name, _ in surface.values() if not name.startswith(("roof", "walls"))])
    # Render-only ground pieces that no longer sit on the merged land (platforms
    # of old service parks, other stages' terrain versions) float or clip.
    floating = set()
    detail = Counter()
    for i, (c, n) in enumerate(terrain_dx):
        h = ground(c[0], c[2], c[1] + 50.0)
        detail[("steep" if abs(n[1]) < 0.5 else "flat", "none" if h is None else min(int(abs(h - c[1])), 5))] += 1
        # Non-land ground elsewhere is rock/cliff detail (sea rocks stand 1-4
        # units above the seabed): keep it.
        if any((c[0] - x) ** 2 + (c[2] - z) ** 2 <= r * r for x, z, r in zones):
            floating.add(i)  # ramps/platforms of an old start or finish area
    stats["terrain_detail"] = {f"{a}/{b}": v for (a, b), v in sorted(detail.items(), key=str)}
    buckets["terrain"] = [e for i, e in enumerate(buckets["terrain"]) if i not in floating]
    stats["dropped_floating_terrain"] = len(floating)
    # Old start/finish dressing standing on the new route (trucks, tyre stacks);
    # trees and palms next to the road stay.
    on_road = clear_road(solid_dx + objects_dx, route_dense, ground, protect=set(
        i for i, veg in enumerate(solid_veg + objects_veg) if veg))
    split = len(solid_dx)
    buckets["solid"] = [e for i, e in enumerate(buckets["solid"]) if i not in on_road]
    solid_dx = [t for i, t in enumerate(solid_dx) if i not in on_road]
    buckets["objects"] = [e for i, e in enumerate(buckets["objects"]) if i + split not in on_road]
    stats["road_cleared_triangles"] = len(on_road)
    boxes, box_skips = collision_boxes(solid_dx, route_dense, ground=ground)
    collide_key = ("collide $shader(object)", (("Null", False, False),) * 3)
    if collide_key not in material_index:
        material_index[collide_key] = len(materials)
        materials.append(GxmMaterial(collide_key[0], [GxmTextureSlot(), GxmTextureSlot(), GxmTextureSlot()]))
    proxy = [(material_index[collide_key], [GxmCorner(q, _face_normal(tri), (0.0, 0.0, 0.5), (1.0, 1.0, 1.0, 1.0)) for q in tri])
             for box in boxes for tri in box_triangles(box)]
    stats["collision"] = {"surface": len(surface), "seam_overlaps": len(overlap), "fill_triangles": len(fill),
                          "boxes": len(boxes), "box_skips": box_skips}

    # Small holes in the merged land (dropped faces at stage seams): close them
    # with a fan, reusing the neighbouring triangle's material and corners.
    land_entries = buckets["landdb"] + fill
    land_dx = [[(c.position[0], c.position[2], -c.position[1]) for c in corners] for _, corners in land_entries]
    patches = []
    for pts, _normal, index in close_land(land_dx)[0]:
        if len(pts) != 3:
            continue  # skirt walls and step faces are collision-only (course_bsp_patch)
        mat, corners = land_entries[index]
        by_pos = {_k((c.position[0], c.position[2], -c.position[1])): c for c in corners}
        made = []
        for q in pts:
            c = by_pos.get(_k(q))
            made.append(c if c is not None else None)
        known = [c for c in made if c is not None]
        avg_uv = tuple(sum(c.texcoord[k] for c in known) / len(known) for k in range(3)) if known and all(
            c.texcoord for c in known) else None
        n = _face_normal([(q[0], -q[2], q[1]) for q in pts])
        patches.append((mat, [c if c is not None else GxmCorner((q[0], -q[2], q[1]), n, avg_uv, (1.0, 1.0, 1.0, 1.0))
                              for c, q in zip(made, pts)]))
    stats["collision"]["hole_patches"] = len(patches)

    builder = GxmBuilder()
    landdb = builder.mesh("$landdb", land_entries + patches)
    fill_mesh = builder.mesh("$landdb fill", [])
    proxies = builder.mesh("COLLIDEobjects", proxy)
    solid = builder.mesh("solid objects", buckets["solid"])
    terrain = builder.mesh("terrain", buckets["terrain"])
    water = builder.mesh("Water $water $landdb", buckets["water"])
    objects = builder.mesh("objects $objects(intrasort)", buckets["objects"])
    nodraw = [m for m in (fill_mesh, proxies) if m.count]
    tree = [GxmGroup("$autovsphere_300", [
        GxmGroup("$bsp", [GxmGroup("$draw", [landdb]), *([GxmGroup("$nodraw", nodraw)] if nodraw else [])]),
        GxmGroup("$objects", [m for m in (solid, terrain, objects) if m.count]),
        *([water] if water.count else []),
    ])]
    data, txt = builder.encode(materials, "Model", tree)
    (out_dir / f"{name}.gxm").write_bytes(data)
    (out_dir / f"{name}.txt").write_text(txt, encoding="latin-1", newline="")
    for stem, src in textures.items():
        if src is None:
            continue
        dxt = src.read_bytes()
        (out_dir / f"{stem}.gxi").write_bytes(dxt_to_gxi(dxt))
        (out_dir / f"{stem}.dxt").write_bytes(dxt)  # the cooked DX names textures by stem
    stats["scene"] = write_scene(args.output / "DataScene", f"{entry}GX", name, route, saved, racetest,
                                 sorted(stem for stem, src in textures.items() if src is not None))
    stats.update({"name": name, "legs": legs, "materials": len(materials), "textures": len(textures),
                  "missing_textures": sorted(k for k, v in textures.items() if v is None),
                  "triangles": {k: len(v) for k, v in buckets.items()}, "gxm_bytes": len(data),
                  "banks": {"colors": len(builder.colors), "normals": len(builder.normals),
                            "texcoords": len(builder.texcoords), "positions": len(builder.positions)}})
    (out_dir.parent.parent.parent / f"{name}-source-report.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "stages"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
