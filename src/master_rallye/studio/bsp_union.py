"""Union of solids before the solid-leaf BSP build.

A solid-leaf BSP built from a polygon soup is only consistent when every
polygon separates solid from empty space. A building sunk into the terrain
breaks that twice: the buried part of its walls lies inside the ground, and
the terrain faces inside the building say "empty above me". Depending on which
plane ends up lower in the tree, the inside of the building becomes empty (the
E2.2 holes under box proxies had the same cause).

:func:`union_polygons` restores the invariant with BSP clipping:

* object faces are clipped against the terrain tree and keep only their parts
  in empty space (buried parts disappear);
* for closed objects (every edge shared by two faces), terrain faces and the
  faces of other overlapping closed objects are clipped against the object's
  own tree and keep only their parts outside it.

Open shells (e.g. collision recovered from a Retail tree) only get the first
step, because an open shell has no defined inside.
"""
from __future__ import annotations

from ..course_bsp import Leaf, Node, Polygon, build_solid_bsp

EPS = 0.01


def _split(points, plane):
    a, b, c, d = plane
    dist = [a * p[0] + b * p[1] + c * p[2] + d for p in points]
    if all(abs(v) <= EPS for v in dist):
        return None, None, 0
    if all(v <= EPS for v in dist):
        return points, None, 1
    if all(v >= -EPS for v in dist):
        return None, points, 2
    back, front = [], []
    n = len(points)
    for i in range(n):
        p, q = points[i], points[(i + 1) % n]
        dp, dq = dist[i], dist[(i + 1) % n]
        if dp <= EPS:
            back.append(p)
        if dp >= -EPS:
            front.append(p)
        if (dp < -EPS and dq > EPS) or (dp > EPS and dq < -EPS):
            t = dp / (dp - dq)
            x = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, p[2] + (q[2] - p[2]) * t)
            back.append(x)
            front.append(x)
    return (back if len(back) >= 3 else None), (front if len(front) >= 3 else None), 3


def clip_outside(root, poly: Polygon, *, keep_coplanar_same: bool) -> list[Polygon]:
    """Fragments of ``poly`` lying in empty space of ``root``.

    Coplanar fragments: kept when the polygon faces the same way as the node
    plane and ``keep_coplanar_same`` (shared boundary kept once), else sent
    to the back side like the game's ``s <= 0`` rule.
    """
    out, stack = [], [(root, poly.points)]
    while stack:
        node, pts = stack.pop()
        if isinstance(node, Leaf):
            if not node.solid:
                out.append(Polygon(list(pts), poly.plane, poly.code))
            continue
        back, front, kind = _split(pts, node.plane)
        if kind == 0:
            same = sum(node.plane[k] * poly.plane[k] for k in range(3)) > 0
            stack.append((node.front if (same and keep_coplanar_same) else node.back, pts))
            continue
        if back is not None:
            stack.append((node.back, back))
        if front is not None:
            stack.append((node.front, front))
    return out


def _bbox(polys):
    xs = [p[0] for poly in polys for p in poly.points]
    ys = [p[1] for poly in polys for p in poly.points]
    zs = [p[2] for poly in polys for p in poly.points]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _overlap(a, b, pad=0.05):
    return all(a[0][k] - pad <= b[1][k] and b[0][k] - pad <= a[1][k] for k in range(3))


def _poly_box(poly):
    xs = [p[0] for p in poly.points]
    ys = [p[1] for p in poly.points]
    zs = [p[2] for p in poly.points]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def components(triangles):
    """Group triangles (each a Polygon) into connected pieces; returns [(polys, closed)]."""
    def key(p):
        return (round(p[0], 3), round(p[1], 3), round(p[2], 3))
    parent = {}

    def find(v):
        while parent.setdefault(v, v) != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    for poly in triangles:
        ks = [key(p) for p in poly.points]
        for k in ks[1:]:
            ra, rb = find(ks[0]), find(k)
            if ra != rb:
                parent[ra] = rb
    groups: dict = {}
    for poly in triangles:
        groups.setdefault(find(key(poly.points[0])), []).append(poly)
    out = []
    for polys in groups.values():
        edges: dict = {}
        for poly in polys:
            ks = [key(p) for p in poly.points]
            for i in range(len(ks)):
                e = frozenset((ks[i], ks[(i + 1) % len(ks)]))
                edges[e] = edges.get(e, 0) + 1
        closed = bool(edges) and all(n == 2 for n in edges.values())
        out.append((polys, closed))
    return out


class _Grid:
    def __init__(self, cell: float = 24.0):
        self.cell, self.items = cell, {}

    def keys(self, box):
        c = self.cell
        for gx in range(int(box[0][0] // c), int(box[1][0] // c) + 1):
            for gz in range(int(box[0][2] // c), int(box[1][2] // c) + 1):
                yield gx, gz

    def add(self, box, value):
        for k in self.keys(box):
            self.items.setdefault(k, []).append(value)

    def query(self, box):
        seen, out = set(), []
        for k in self.keys(box):
            for v in self.items.get(k, ()):
                if v not in seen:
                    seen.add(v)
                    out.append(v)
        return out


def union_polygons(terrain, extra_land, objects, *, heights=None, progress=None):
    """Return (polygons for the final build, stats).

    ``objects``: list of ``(polygons, closed[, cuts_terrain])`` components; ``extra_land``: skirt/closure faces
    (never clipped). Native cells recovered from a Retail tree pass ``cuts_terrain=False``: they sit on the
    ground they were cut from, and removing the shared face from both sides opens seams.
    """
    stats = {"objects": len(objects), "closed_objects": sum(1 for o in objects if o[1]),
             "object_faces_clipped": 0, "terrain_faces_clipped": 0}
    if not objects:
        return terrain + extra_land, stats
    land_tree = build_solid_bsp(terrain + extra_land) if terrain else Leaf(False)
    solids, grid = [], _Grid()
    terrain_grid = _Grid()
    for index, item in enumerate(objects):
        polys, closed = item[0], item[1]
        cuts_terrain = item[2] if len(item) > 2 else True
        box = _bbox(polys)
        tree = build_solid_bsp(list(polys)) if closed else None
        solids.append((box, tree, polys))
        if tree is not None:
            grid.add(box, index)
            if cuts_terrain:
                terrain_grid.add(box, index)
    kept_objects = []
    for index, (box, tree, polys) in enumerate(solids):
        if progress and index % 2000 == 0:
            progress("union", index / max(1, len(solids)))
        neighbours = [j for j in grid.query(box) if j != index and _overlap(box, solids[j][0])]
        for poly in polys:
            pb = _poly_box(poly)
            buried = True
            if heights is not None:
                low = min(p[1] for p in poly.points)
                ground = max((h for h in (heights(p[0], p[2]) for p in poly.points) if h is not None), default=None)
                buried = ground is None or low <= ground + 0.5
            frags = clip_outside(land_tree, poly, keep_coplanar_same=False) if buried else [poly]
            if buried and (len(frags) != 1 or frags[0].points != poly.points):
                stats["object_faces_clipped"] += 1
            for j in neighbours:
                obox, otree, _ = solids[j]
                if not frags or not _overlap(pb, obox):
                    continue
                nxt = []
                for frag in frags:
                    nxt.extend(clip_outside(otree, frag, keep_coplanar_same=j > index))
                frags = nxt
            kept_objects.extend(frags)
    kept_terrain = []
    for poly in terrain:
        pb = _poly_box(poly)
        frags = [poly]
        for j in terrain_grid.query(pb):
            box, tree, _ = solids[j]
            if not frags or not _overlap(pb, box):
                continue
            nxt = []
            for frag in frags:
                nxt.extend(clip_outside(tree, frag, keep_coplanar_same=False))
            frags = nxt
        if len(frags) != 1 or frags[0] is not poly:
            stats["terrain_faces_clipped"] += 1
        kept_terrain.extend(frags)
    return kept_terrain + extra_land + kept_objects, stats
