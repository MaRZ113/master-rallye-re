"""Solid-leaf BSP writer for the cooked course tag100 tree (R5T-INV E2.4).

Decoded runtime contract (probe-verified against Retail SpainW/Spain2/SpainM):

* plane node: ``(a, b, c, d)`` with ``s = a*x + b*y + c*z + d``; ``s <= 0``
  continues in the node's *child* (back), otherwise in its *sibling* (front);
  the float4 record carries a ``code`` = source GXM triangle index of the
  splitting polygon (0xFFFFFFFF for axis-aligned splits);
* leaves: a back leaf (child slot, pool8_child) has ``field_0`` 0xFFFFFFFF =
  solid; a front leaf (sibling slot, pool8_sibling) has ``field_0`` 1 = empty;
* wire order is depth first: node record, ``child`` flag (+ selector, back
  subtree), then the node's ``sibling`` flag (+ selector, front subtree).

The game's own cooker assigns polygons that span a splitting plane without
cutting them, which leaves wrong cells (solid slabs above beaches, pockets
under the road) wherever a large triangle is crossed. ``build_solid_bsp``
clips spanning polygons, so every cell is bounded by real surface fragments.
"""
from __future__ import annotations

import math
import struct
import sys
from dataclasses import dataclass
from typing import Sequence

AXIS_CODE = 0xFFFFFFFF
SOLID = 0xFFFFFFFF
EMPTY = 1
EPS = 0.01

Vec3 = tuple[float, float, float]


@dataclass
class Leaf:
    solid: bool


@dataclass
class Node:
    plane: tuple[float, float, float, float]
    code: int
    back: "Node | Leaf"
    front: "Node | Leaf"


@dataclass
class Polygon:
    points: list[Vec3]
    plane: tuple[float, float, float, float]
    code: int


def polygon(points: Sequence[Vec3], normal: Vec3, code: int) -> Polygon | None:
    """Polygon with an outward ``normal`` (towards empty space); None if degenerate."""
    length = math.sqrt(sum(c * c for c in normal))
    if length < 1e-9:
        return None
    n = tuple(c / length for c in normal)
    d = -sum(n[k] * points[0][k] for k in range(3))
    return Polygon(list(points), (n[0], n[1], n[2], d), code)


def _side(plane, p) -> float:
    return plane[0] * p[0] + plane[1] * p[1] + plane[2] * p[2] + plane[3]


def _split(poly: Polygon, plane) -> tuple[Polygon | None, Polygon | None, int]:
    """(back part, front part, kind) — kind 0 coplanar, 1 back, 2 front, 3 spanning."""
    dists = [_side(plane, p) for p in poly.points]
    if all(abs(v) <= EPS for v in dists):
        return None, None, 0
    if all(v <= EPS for v in dists):
        return poly, None, 1
    if all(v >= -EPS for v in dists):
        return None, poly, 2
    back, front = [], []
    pts = poly.points
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        dp, dq = dists[i], dists[(i + 1) % len(pts)]
        if dp <= EPS:
            back.append(p)
        if dp >= -EPS:
            front.append(p)
        if (dp < -EPS and dq > EPS) or (dp > EPS and dq < -EPS):
            t = dp / (dp - dq)
            x = tuple(p[k] + (q[k] - p[k]) * t for k in range(3))
            back.append(x)
            front.append(x)
    bp = Polygon(back, poly.plane, poly.code) if len(back) >= 3 else None
    fp = Polygon(front, poly.plane, poly.code) if len(front) >= 3 else None
    return bp, fp, 3


def _partition(polys, plane, splitter_normal=None):
    back, front, coplanar_dropped = [], [], 0
    for poly in polys:
        b, f, kind = _split(poly, plane)
        if kind == 0:
            same = splitter_normal is not None and sum(
                poly.plane[k] * splitter_normal[k] for k in range(3)) > 0
            if same:
                coplanar_dropped += 1  # lies on the node; represented by it
            else:
                front.append(poly)     # back-to-back face: belongs to the other solid
            continue
        if b is not None:
            back.append(b)
        if f is not None:
            front.append(f)
    return back, front


def _centroid(poly: Polygon) -> Vec3:
    n = len(poly.points)
    return tuple(sum(p[k] for p in poly.points) / n for k in range(3))


def _choose_polygon(polys: list[Polygon], candidates: int = 12) -> Polygon:
    if len(polys) <= candidates:
        pool = polys
    else:
        step = len(polys) / candidates
        pool = [polys[int(i * step)] for i in range(candidates)]
    best, best_score = pool[0], None
    for cand in pool:
        b = f = s = 0
        for poly in polys:
            if poly is cand:
                continue
            dists = [_side(cand.plane, p) for p in poly.points]
            lo, hi = min(dists), max(dists)
            if lo < -EPS and hi > EPS:
                s += 1
            elif hi <= EPS and lo < -EPS:
                b += 1
            elif lo >= -EPS and hi > EPS:
                f += 1
        score = 8 * s + abs(f - b)
        if best_score is None or score < best_score:
            best, best_score = cand, score
    return best


def build_solid_bsp(polys: list[Polygon], *, axis_threshold: int = 64) -> Node | Leaf:
    """Solid-leaf BSP; axis splits (median centroid) while a cell is crowded."""
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, 20000))
    try:
        return _build(polys, axis_threshold, side_solid=True, depth=0)
    finally:
        sys.setrecursionlimit(old_limit)


def _build(polys, axis_threshold, side_solid, depth):
    if not polys:
        return Leaf(side_solid)
    if len(polys) > axis_threshold and depth < 200:
        cents = [_centroid(p) for p in polys]
        spans = [max(c[k] for c in cents) - min(c[k] for c in cents) for k in (0, 2)]
        axis = 0 if spans[0] >= spans[1] else 2
        values = sorted(c[axis] for c in cents)
        cut = values[len(values) // 2]
        plane = (1.0, 0.0, 0.0, -cut) if axis == 0 else (0.0, 0.0, 1.0, -cut)
        back, front = _partition(polys, plane)
        if back and front and len(back) < len(polys) and len(front) < len(polys):
            return Node(plane, AXIS_CODE, _build(back, axis_threshold, True, depth + 1),
                        _build(front, axis_threshold, False, depth + 1))
    splitter = _choose_polygon(polys)
    back, front = _partition(polys, splitter.plane, splitter.plane[:3])
    return Node(splitter.plane, splitter.code, _build(back, axis_threshold, True, depth + 1),
                _build(front, axis_threshold, False, depth + 1))


def orient_terrain(triangles: Sequence[Sequence[Vec3]], normals: Sequence[Vec3], *, cell: float = 10.0,
                   steep: float = 0.5, probe: float = 2.0) -> tuple[list[Vec3], dict]:
    """Outward normals for a terrain soup whose stored winding is unreliable.

    * gentle faces (|ny| >= ``steep``) face up, except a down-facing face with
      another surface more than 1 unit below it (bridge/overhang underside);
    * steep faces face the side whose ground is lower ``probe`` units away
      (cliff faces look into the open), when the two sides differ by > 1.
    Heights come from the gentle faces themselves.
    """
    grid: dict = {}
    gentle = [i for i, n in enumerate(normals) if abs(n[1]) >= steep]
    for i in gentle:
        t = triangles[i]
        xs, zs = [p[0] for p in t], [p[2] for p in t]
        for gx in range(int(min(xs) // cell), int(max(xs) // cell) + 1):
            for gz in range(int(min(zs) // cell), int(max(zs) // cell) + 1):
                grid.setdefault((gx, gz), []).append(i)

    def heights(x, z):
        out = []
        for j in grid.get((int(x // cell), int(z // cell)), ()):
            (ax, ay, az), (bx, by, bz), (qx, qy, qz) = triangles[j]
            d = (bz - qz) * (ax - qx) + (qx - bx) * (az - qz)
            if abs(d) < 1e-9:
                continue
            l1 = ((bz - qz) * (x - qx) + (qx - bx) * (z - qz)) / d
            l2 = ((qz - az) * (x - qx) + (ax - qx) * (z - qz)) / d
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) >= -1e-6:
                out.append(l1 * ay + l2 * by + l3 * qy)
        return out

    def ground_below(x, z, y):
        hs = [h for h in heights(x, z) if h <= y + 0.5]
        return max(hs) if hs else None

    result, stats = [], {"gentle_up": 0, "underside_kept": 0, "steep_turned": 0}
    for t, n in zip(triangles, normals):
        c = [sum(p[k] for p in t) / 3 for k in range(3)]
        if abs(n[1]) >= steep:
            if n[1] < 0:
                below = [h for h in heights(c[0], c[2]) if h < c[1] - 1.0]
                if below:
                    stats["underside_kept"] += 1
                else:
                    n = (-n[0], -n[1], -n[2])
                    stats["gentle_up"] += 1
        else:
            hl = math.hypot(n[0], n[2]) or 1.0
            hf = ground_below(c[0] + probe * n[0] / hl, c[2] + probe * n[2] / hl, c[1] + 50)
            hb = ground_below(c[0] - probe * n[0] / hl, c[2] - probe * n[2] / hl, c[1] + 50)
            if hf is not None and hb is not None and hf > hb + 1.0:
                n = (-n[0], -n[1], -n[2])
                stats["steep_turned"] += 1
        result.append(n)
    return result, stats


def boundary_skirt(triangles: Sequence[Sequence[Vec3]], *, top: float | None = None, seam_probe: float = 0.75,
                   seam_height: float = 1e9, cell: float = 10.0) -> tuple[list[tuple[list[Vec3], Vec3, int]], dict]:
    """Retail ``$skirt``: walls rising from the open edge of the land surface.

    Retail stages are corridors; the cooker closes the space above the land
    with ``$nodraw $skirt`` walls (Italy1: 1108 triangles from every boundary
    edge up to a constant height). Without them a solid-leaf BSP classifies
    cells through the open sides arbitrarily. Only edges with no land at all
    within 8 units beyond them (the real map edge) get a wall.
    Returns ``[(quad points, inward normal, index of the edge's triangle)]``.
    """
    def key(p):
        return (round(p[0], 2), round(p[1], 2), round(p[2], 2))

    edges: dict = {}
    for index, t in enumerate(triangles):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = frozenset((key(t[a]), key(t[b])))
            edges.setdefault(e, []).append((index, a, b))
    grid: dict = {}
    for index, t in enumerate(triangles):
        xs, zs = [p[0] for p in t], [p[2] for p in t]
        for gx in range(int(min(xs) // cell), int(max(xs) // cell) + 1):
            for gz in range(int(min(zs) // cell), int(max(zs) // cell) + 1):
                grid.setdefault((gx, gz), []).append(index)

    def surface_near(x, z, y, skip):
        for j in grid.get((int(x // cell), int(z // cell)), ()):
            if j == skip:
                continue
            (ax, ay, az), (bx, by, bz), (qx, qy, qz) = triangles[j]
            d = (bz - qz) * (ax - qx) + (qx - bx) * (az - qz)
            if abs(d) < 1e-9:
                continue
            l1 = ((bz - qz) * (x - qx) + (qx - bx) * (z - qz)) / d
            l2 = ((qz - az) * (x - qx) + (ax - qx) * (z - qz)) / d
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) >= -1e-6 and abs(l1 * ay + l2 * by + l3 * qy - y) < seam_height:
                return True
        return False

    ceiling = top if top is not None else max(p[1] for t in triangles for p in t) + 300.0
    walls, seams = [], 0
    for uses in edges.values():
        if len(uses) != 1:
            continue
        index, a, b = uses[0]
        t = triangles[index]
        pa, pb, pc = t[a], t[b], t[3 - a - b]
        ex, ez = pb[0] - pa[0], pb[2] - pa[2]
        length = math.hypot(ex, ez)
        if length < 1e-6:
            continue
        nx, nz = -ez / length, ex / length            # horizontal edge normal
        mx, mz = (pa[0] + pb[0]) / 2, (pa[2] + pb[2]) / 2
        if (pc[0] - mx) * nx + (pc[2] - mz) * nz < 0:  # make it point into the triangle
            nx, nz = -nx, -nz
        my = (pa[1] + pb[1]) / 2
        # Any land just beyond the edge, at any height, means the edge is inside
        # the map (a seam, a cliff gap): a wall there would block the course.
        if any(surface_near(mx - nx * dist, mz - nz * dist, my, index) for dist in (seam_probe, 3.0, 8.0)):
            seams += 1
            continue
        quad = [pa, pb, (pb[0], ceiling, pb[2]), (pa[0], ceiling, pa[2])]
        walls.append((quad, (nx, 0.0, nz), index))
    return walls, {"walls": len(walls), "seam_edges": seams, "ceiling": round(ceiling, 1)}


def close_land(triangles: Sequence[Sequence[Vec3]], *, top: float | None = None, fill_extent: float = 200.0,
               cell: float = 10.0) -> tuple[list[tuple[list[Vec3], Vec3, int]], dict]:
    """Close the open edges of a merged land surface for a solid-leaf BSP.

    ``triangles`` are DX-space points in source winding (outward normal =
    right-hand cross product). Open edges are grouped into boundary loops:

    * crack loops (most edges have land within 0.75 units beyond them: stage
      seams, T-junctions) stay open, except where the neighbouring stage's
      terrain is lower: a vertical step face closes that seam;
    * small loops (extent below ``fill_extent``, most edges with land again
      within the loop's extent beyond them) are holes left by dropped faces: closed with a fan from the
      loop centre, wound to match the surrounding surface;
    * the rest is the map edge (also the gaps between stage corridors): Retail
      ``$skirt`` walls rising to a ceiling, skipping edges that have land just
      beyond them.

    Returns ``[(points, outward normal, index of the edge's triangle)]``.
    """
    def key(p):
        return (round(p[0], 2), round(p[1], 2), round(p[2], 2))

    edges: dict = {}
    for index, t in enumerate(triangles):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edges.setdefault(frozenset((key(t[a]), key(t[b]))), []).append((index, a, b))
    grid: dict = {}
    for index, t in enumerate(triangles):
        xs, zs = [p[0] for p in t], [p[2] for p in t]
        for gx in range(int(min(xs) // cell), int(max(xs) // cell) + 1):
            for gz in range(int(min(zs) // cell), int(max(zs) // cell) + 1):
                grid.setdefault((gx, gz), []).append(index)

    def heights_at(x, z, skip):
        out = []
        for j in grid.get((int(x // cell), int(z // cell)), ()):
            if j == skip:
                continue
            (ax, ay, az), (bx, by, bz), (qx, qy, qz) = triangles[j]
            d = (bz - qz) * (ax - qx) + (qx - bx) * (az - qz)
            if abs(d) < 1e-9:
                continue
            l1 = ((bz - qz) * (x - qx) + (qx - bx) * (z - qz)) / d
            l2 = ((qz - az) * (x - qx) + (ax - qx) * (z - qz)) / d
            if min(l1, l2, 1 - l1 - l2) >= -1e-6:
                out.append(l1 * ay + l2 * by + (1 - l1 - l2) * qy)
        return out

    def land_at(x, z, skip):
        return bool(heights_at(x, z, skip))

    open_edges = []
    for uses in edges.values():
        if len(uses) != 1:
            continue
        index, a, b = uses[0]
        t = triangles[index]
        pa, pb, pc = t[a], t[b], t[3 - a - b]
        ex, ez = pb[0] - pa[0], pb[2] - pa[2]
        length = math.hypot(ex, ez)
        nx, nz = (-ez / length, ex / length) if length > 1e-6 else (0.0, 0.0)
        mx, mz = (pa[0] + pb[0]) / 2, (pa[2] + pb[2]) / 2
        if (pc[0] - mx) * nx + (pc[2] - mz) * nz < 0:
            nx, nz = -nx, -nz                          # horizontal normal into the triangle
        seam = length > 1e-6 and land_at(mx - nx * 0.75, mz - nz * 0.75, index)
        near = seam or (length > 1e-6 and any(land_at(mx - nx * d, mz - nz * d, index) for d in (3.0, 8.0)))
        open_edges.append((index, pa, pb, (nx, nz), seam, near))

    parent: dict = {}

    def find(v):
        while parent.setdefault(v, v) != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for _, pa, pb, *_ in open_edges:
        ra, rb = find(key(pa)), find(key(pb))
        if ra != rb:
            parent[ra] = rb
    loops: dict = {}
    for edge in open_edges:
        loops.setdefault(find(key(edge[1])), []).append(edge)

    ceiling = top if top is not None else max(p[1] for t in triangles for p in t) + 300.0
    out, stats = [], {"loops": len(loops), "crack_loops": 0, "filled_loops": 0, "fill_triangles": 0,
                      "skirt_walls": 0, "step_curtains": 0, "ceiling": round(ceiling, 1)}

    def curtain(index, pa, pb, nx, nz):
        """Seam between stage terrains at different heights: from the higher
        edge a vertical face down to the neighbour surface, facing outward."""
        drops = []
        for p in (pa, pb):
            hs = [h for h in heights_at(p[0] - nx * 0.75, p[2] - nz * 0.75, index) if h < p[1] + 0.05]
            if not hs:
                return
            drops.append(max(hs))
        if max(pa[1] - drops[0], pb[1] - drops[1]) < 0.05:
            return
        out.append(([pa, pb, (pb[0], min(drops[1], pb[1]), pb[2]), (pa[0], min(drops[0], pa[1]), pa[2])],
                    (-nx, 0.0, -nz), index))
        stats["step_curtains"] += 1

    for loop in loops.values():
        pts = [p for e in loop for p in (e[1], e[2])]
        extent = math.hypot(max(p[0] for p in pts) - min(p[0] for p in pts),
                            max(p[2] for p in pts) - min(p[2] for p in pts))
        seams = sum(e[4] for e in loop) / len(loop)
        nears = sum(e[5] for e in loop) / len(loop)
        stats.setdefault("detail", []).append((len(loop), round(extent), round(seams, 2), round(nears, 2),
                                               round(min(p[0] for p in pts)), round(min(p[2] for p in pts))))
        if seams > 0.5:
            stats["crack_loops"] += 1
            for index, pa, pb, (nx, nz), seam, _ in loop:
                if seam:
                    curtain(index, pa, pb, nx, nz)
            continue
        if extent < fill_extent:
            # across a hole there is land again within the hole's own extent
            reach = [d for d in (3.0, 8.0, 16.0, 32.0, 64.0, 128.0) if d <= extent] + [extent]
            nears = sum(e[5] or any(land_at(((e[1][0] + e[2][0]) / 2) - e[3][0] * d,
                                            ((e[1][2] + e[2][2]) / 2) - e[3][1] * d, e[0]) for d in reach)
                        for e in loop) / len(loop)
        if extent < fill_extent and nears > 0.5:
            centre = tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))
            for index, pa, pb, *_ in loop:
                tri = [pb, pa, centre]               # reversed edge: continues the surface winding
                u = [tri[1][k] - tri[0][k] for k in range(3)]
                v = [tri[2][k] - tri[0][k] for k in range(3)]
                n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                out.append((tri, n, index))
                stats["fill_triangles"] += 1
            stats["filled_loops"] += 1
            continue
        for index, pa, pb, (nx, nz), seam, _ in loop:
            if seam:
                curtain(index, pa, pb, nx, nz)
                continue
            out.append(([pa, pb, (pb[0], ceiling, pb[2]), (pa[0], ceiling, pa[2])], (nx, 0.0, nz), index))
            stats["skirt_walls"] += 1
    return out, stats


# ----------------------------------------------------------------------------- wire format

def encode_tag100(root: Node | Leaf) -> bytes:
    """Serialise a tree in the revision-135 tag100 grammar."""
    out = bytearray()
    counts = {"child_leaf": 0, "sibling_leaf": 0, "planes": 0}

    def record(node, slot):
        if isinstance(node, Leaf):
            if slot == "child":
                counts["child_leaf"] += 1
                if not node.solid:
                    raise ValueError("a back (child) leaf must be solid")
            elif slot == "sibling":
                counts["sibling_leaf"] += 1
                if node.solid:
                    raise ValueError("a front (sibling) leaf must be empty")
            out.extend(struct.pack("<2I", SOLID if node.solid else EMPTY, 0))
            out.extend(b"\x00\x00")  # no plane record, no list
        else:
            counts["planes"] += 1
            out.extend(struct.pack("<2I", 0, 0))
            out.append(1)
            out.extend(struct.pack("<4fI", *node.plane, node.code))
            out.append(0)  # no list

    # iterative depth-first: (node, slot, phase)
    stack = [(root, "root", 0)]
    while stack:
        node, slot, phase = stack.pop()
        if phase == 0:
            record(node, slot)
            if isinstance(node, Leaf):
                out.append(0)  # no child
                out.append(0)  # no sibling
                continue
            out.append(1)  # child present
            out.append(1 if isinstance(node.back, Leaf) else 0)
            stack.append((node, slot, 1))
            stack.append((node.back, "child", 0))
        else:
            out.append(1)  # sibling present
            out.append(1 if isinstance(node.front, Leaf) else 0)
            stack.append((node.front, "sibling", 0))
    header = struct.pack("<I5I", 100, counts["child_leaf"], counts["sibling_leaf"], counts["planes"],
                         counts["planes"], 0)
    return header + bytes(out)


def tree_from_parsed(parsed) -> Node | Leaf:
    """Binary tree from ``course_tag100.parse_course_tag100_bytes`` output (for round trips)."""
    nodes = parsed.nodes

    def make(index):
        n = nodes[index]
        if n.optional_record is None:
            return Leaf(n.field_0 == SOLID)
        return Node(tuple(n.optional_record.values), n.optional_record.code,
                    make(n.first_child_index), make(n.next_sibling_index))

    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 50000))
    try:
        return make(0)
    finally:
        sys.setrecursionlimit(old)


def classify(root: Node | Leaf, p: Vec3) -> bool:
    """True when ``p`` is in solid space."""
    node = root
    while isinstance(node, Node):
        node = node.back if _side(node.plane, p) <= 0 else node.front
    return node.solid
