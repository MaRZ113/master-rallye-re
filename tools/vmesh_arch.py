"""V-MESH4 wheel-arch construction: analytic cut + continuous liner (no texture-alpha carving).

A vehicle body generated from a donor-agnostic source mesh has to give the (differently sized) donor
wheels room.  V-MESH3 carved the source's alpha cutouts and pushed vertices out of the tyre, which left
stair-stepped, distorted arch edges.  Here the opening is a clean geometric cut:

* every body triangle that reaches the *wheel house* of a hub (the cylinder around the hub axis, radius
  ``R`` = visual tyre radius + gap, for ``|x|`` beyond ``x_in``) is clipped against a regular N-gon prism
  that circumscribes the cylinder (so the opening is never smaller than ``R``);
* the new boundary edges are *the lip* of the arch; a tube is built from them towards the car centre
  (``x_in``) and closed with a flat inboard wall, so the opening reads as a proper wheel house instead of
  a hole through a thin sheet.

Everything works on plain tuples; corners are ``(position, normal, key, uv)`` as used by
``vmesh_geometry`` (``uv`` is dropped for generated vertices).  No source data lives here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

EPS = 1e-7
MIN_AREA = 1e-9


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(v):
    n = math.sqrt(_dot(v, v))
    return (v[0] / n, v[1] / n, v[2] / n) if n > 1e-12 else None


def _gen_key(pos, nrm):
    return ("g", tuple(round(c, 5) for c in pos), None if nrm is None else tuple(round(c, 3) for c in nrm))


def lerp_corner(a, b, t):
    """Interpolate two corners; the result is a *generated* vertex (stable key from its attributes)."""
    pos = tuple(a[0][i] + (b[0][i] - a[0][i]) * t for i in range(3))
    nrm = None
    if a[1] is not None and b[1] is not None:
        nrm = _norm(tuple(a[1][i] + (b[1][i] - a[1][i]) * t for i in range(3)))
    return (pos, nrm, _gen_key(pos, nrm), None)


def split_polygon(poly, normal, offset):
    """Split a convex polygon by the plane ``normal . p = offset``.

    Returns ``(inside, outside)`` polygons (lists of corners; ``None`` when empty) where *inside* has
    ``normal . p <= offset``.  Corner order (winding) is preserved.
    """
    inside, outside = [], []
    n = len(poly)
    d = [_dot(normal, c[0]) - offset for c in poly]
    for i in range(n):
        a, b, da, db = poly[i], poly[(i + 1) % n], d[i], d[(i + 1) % n]
        if da <= EPS:
            inside.append(a)
        if da >= -EPS:
            outside.append(a)
        if (da < -EPS and db > EPS) or (da > EPS and db < -EPS):
            t = da / (da - db)
            c = lerp_corner(a, b, t)
            inside.append(c)
            outside.append(c)
    return (inside if len(inside) >= 3 else None), (outside if len(outside) >= 3 else None)


def _area(poly) -> float:
    total = 0.0
    for i in range(1, len(poly) - 1):
        c = _cross(_sub(poly[i][0], poly[0][0]), _sub(poly[i + 1][0], poly[0][0]))
        total += math.sqrt(_dot(c, c)) / 2
    return total


def fan(poly):
    """Triangulate a convex polygon (dropping zero-area slivers)."""
    out = []
    for i in range(1, len(poly) - 1):
        tri = (poly[0], poly[i], poly[i + 1])
        if _area(list(tri)) > MIN_AREA:
            out.append(tri)
    return out


@dataclass(frozen=True)
class WheelHouse:
    """One wheel's cutter: hub (x, y, z), arch radius (side view), inboard wall ``x_in`` (absolute value)."""

    hub: tuple
    radius: float
    x_in: float
    sides: int = 32

    @property
    def sx(self) -> float:
        return 1.0 if self.hub[0] > 0 else -1.0

    def planes(self):
        """N-gon prism planes ``(normal, offset)``; outside = ``normal . p > offset`` (apothem = radius)."""
        out = []
        for k in range(self.sides):
            th = 2 * math.pi * (k + 0.5) / self.sides
            n = (0.0, math.cos(th), math.sin(th))
            out.append((n, n[1] * self.hub[1] + n[2] * self.hub[2] + self.radius))
        return out


@dataclass
class ArchResult:
    kept: list = field(default_factory=list)          # triangles (corner tuples) that survive
    removed_area: float = 0.0
    lip_edges: list = field(default_factory=list)     # (corner_a, corner_b) on the prism, outside the tyre


def _on_plane(corner, normal, offset) -> bool:
    return abs(_dot(normal, corner[0]) - offset) < 1e-5


def _point_on_segment(p, a, b, tol=1e-6):
    ab = _sub(b, a)
    den = _dot(ab, ab)
    if den < 1e-18:
        return None
    t = _dot(_sub(p, a), ab) / den
    if t <= 1e-6 or t >= 1 - 1e-6:
        return None
    q = tuple(a[i] + ab[i] * t for i in range(3))
    return t if math.dist(q, p) < tol else None


def split_tjunctions(tris, candidates, tol=1e-6, _depth=0):
    """Remove T-junctions: split triangles whose edge passes through a candidate vertex (generated by clipping).

    ``tris`` are corner-tuple triangles, ``candidates`` corner tuples.  A triangle (a, b, c) with candidate h on
    edge a-b becomes (a, h, c) + (h, b, c); recursion handles several hits.  Only vertices that exist in the
    candidate list are ever inserted, so the surface is unchanged.
    """
    if not candidates:
        return list(tris)
    grid = {}
    cell = 0.25
    for c in candidates:
        grid.setdefault((math.floor(c[0][0] / cell), math.floor(c[0][2] / cell)), []).append(c)

    def near(a, b):
        lo = [min(a[i], b[i]) - tol for i in (0, 2)]
        hi = [max(a[i], b[i]) + tol for i in (0, 2)]
        for gx in range(math.floor(lo[0] / cell), math.floor(hi[0] / cell) + 1):
            for gz in range(math.floor(lo[1] / cell), math.floor(hi[1] / cell) + 1):
                yield from grid.get((gx, gz), ())

    def process(tri, depth):
        if depth > 40:
            return [tri]
        for i in range(3):
            a, b, c = tri[i], tri[(i + 1) % 3], tri[(i + 2) % 3]
            best = None
            for h in near(a[0], b[0]):
                if h[0] == a[0] or h[0] == b[0]:
                    continue
                t = _point_on_segment(h[0], a[0], b[0], tol)
                if t is not None:
                    best = h
                    break
            if best is not None:
                return process((a, best, c), depth + 1) + process((best, b, c), depth + 1)
        return [tri]

    out = []
    for tri in tris:
        out += process(tri, 0)
    return [t for t in out if _area(list(t)) > MIN_AREA]


def cut_triangle(tri, house: WheelHouse, planes=None) -> ArchResult:
    """Clip one triangle against one wheel house; returns kept sub-triangles and the lip edges."""
    planes = planes or house.planes()
    res = ArchResult()
    poly = [tri[0], tri[1], tri[2]]
    sx, x_in = house.sx, house.x_in
    # inboard of the wall: untouched
    inboard, outboard = split_polygon(poly, (sx, 0.0, 0.0), x_in)
    if outboard is None:
        res.kept = [tri]
        return res
    pieces = [inboard] if inboard is not None else []
    remain = outboard
    for k, (n, off) in enumerate(planes):
        remain_in, out_k = split_polygon(remain, n, off)
        if out_k is not None:
            pieces.append(out_k)
        remain = remain_in
        if remain is None:
            break
    if remain is not None:
        pieces.append(remain)                                   # last entry = the removed part
    repaired = list(pieces)
    if remain is not None:
        removed = repaired.pop()
        res.removed_area = _area(removed)
        wall = (sx, 0.0, 0.0)
        m = len(removed)
        for i in range(m):
            a, b = removed[i], removed[(i + 1) % m]
            if abs(_dot(wall, a[0]) - x_in) < 1e-5 and abs(_dot(wall, b[0]) - x_in) < 1e-5:
                continue                                        # lies on the inboard wall plane, not a lip
            if any(_on_plane(a, n, off) and _on_plane(b, n, off) for n, off in planes):
                res.lip_edges.append((a, b))
    for piece in repaired:
        res.kept += fan(piece)
    return res


def build_liner(lip_edges, house: WheelHouse):
    """Tube (lip -> inboard wall) and closing wall for one wheel house.

    Returns ``(tube_tris, wall_tris)`` as corner-tuple triangles; the tube faces the wheel axis, the wall
    faces outboard.  Normals are radial for the tube and +/-x for the wall.
    """
    hx, hy, hz = house.hub
    sx = house.sx
    x_wall = sx * house.x_in

    def radial(p):
        dy, dz = p[1] - hy, p[2] - hz
        r = math.hypot(dy, dz) or 1.0
        return (0.0, -dy / r, -dz / r)

    def corner(p, nrm):
        return (p, nrm, _gen_key(p, nrm), None)

    tube, wall = [], []
    centre = (x_wall, hy, hz)
    for a, b in lip_edges:
        pa, pb = a[0], b[0]
        pa_in, pb_in = (x_wall, pa[1], pa[2]), (x_wall, pb[1], pb[2])
        for quad in ((pa, pb, pb_in), (pa, pb_in, pa_in)):
            n = _cross(_sub(quad[1], quad[0]), _sub(quad[2], quad[0]))
            mid = tuple(sum(q[i] for q in quad) / 3 for i in range(3))
            toward_axis = (0.0, hy - mid[1], hz - mid[2])
            tri = quad if _dot(n, toward_axis) > 0 else (quad[0], quad[2], quad[1])
            if _area([corner(p, None) for p in tri]) > MIN_AREA:
                tube.append(tuple(corner(p, radial(p)) for p in tri))
        tri = (centre, pb_in, pa_in)
        n = _cross(_sub(tri[1], tri[0]), _sub(tri[2], tri[0]))
        if _dot(n, (sx, 0.0, 0.0)) < 0:
            tri = (tri[0], tri[2], tri[1])
        if _area([corner(p, None) for p in tri]) > MIN_AREA:
            wall.append(tuple(corner(p, (sx, 0.0, 0.0)) for p in tri))
    return tube, wall


def cut_wheel_houses(triangles, houses, sides_planes=None):
    """Clip a list of corner-tuple triangles against every wheel house.

    Returns ``(kept_triangles, lip_edges_by_house_index, removed_area)``.
    """
    planes = sides_planes or [h.planes() for h in houses]
    lips = [[] for _ in houses]
    removed = 0.0
    work = list(triangles)
    for hi, house in enumerate(houses):
        nxt = []
        for tri in work:
            xs = [c[0][0] for c in tri]
            if max(house.sx * x for x in xs) <= house.x_in:     # entirely inboard of the wall
                nxt.append(tri)
                continue
            ys = [c[0][1] for c in tri]
            zs = [c[0][2] for c in tri]
            if (min(ys) > house.hub[1] + house.radius + 0.01 or max(ys) < house.hub[1] - house.radius - 0.01
                    or min(zs) > house.hub[2] + house.radius + 0.01 or max(zs) < house.hub[2] - house.radius - 0.01):
                nxt.append(tri)
                continue
            r = cut_triangle(tri, house, planes[hi])
            nxt += r.kept
            lips[hi] += r.lip_edges
            removed += r.removed_area
        work = nxt
    return work, lips, removed
