"""Object collision tree for many disjoint convex solids (used by build_track.py around Course Studio's build).

Course Studio (master-rallye-re-course src/master_rallye/course_bsp.py build_solid_bsp) splits a cell with more than 64
polygons on an axis plane and gives a polygon-free sub-cell the side state of that axis split (back = solid). That is
intended for terrain; for a set of separate objects it turns the empty space between them into solid (the 300 Evo 2
rock/fence proxies of Deadman's Gulch made phantom solid 50-190 m away and blocked the AI line). A single object of up
to 64 faces is exact.

Here the object polygons are grouped by their source solid (to_course.py records the proxy triangle range of every
solid in project.extras["evo2_solids"]; Course Studio's provenance keeps the source triangle of every polygon), the
groups are separated by axis planes that pass *between* them (kd split: empty stays empty) and every solid gets its
own exact BSP built from its *complete* hull: Course Studio drops proxy faces that lie entirely under the terrain
(collision_faces_buried), which left grounded convex solids open and leaking solid space tens of metres away.
Terrain polygons still go to the original builder.
"""
from __future__ import annotations

import bisect

import master_rallye.studio.collision as collision
from master_rallye.course_bsp import AXIS_CODE, Node

_original = collision.build_solid_bsp
_original_polygons = collision.collision_polygons
_state = {"provenance": None, "ranges": {}, "solids": {}}


def _bounds(polys):
    pts = [p for poly in polys for p in poly.points]
    return [min(q[k] for q in pts) for k in range(3)], [max(q[k] for q in pts) for k in range(3)]


def _kd(items):
    """items: [(polys, lo, hi)] of pairwise disjoint solids."""
    if len(items) == 1:
        return _original(items[0][0], axis_threshold=10 ** 9)
    for axis in sorted((0, 2, 1), key=lambda k: -(max(i[2][k] for i in items) - min(i[1][k] for i in items))):
        order = sorted(items, key=lambda i: (i[1][axis] + i[2][axis]) / 2)
        best = None
        for cut in range(1, len(order)):
            hi_left = max(i[2][axis] for i in order[:cut])
            lo_right = min(i[1][axis] for i in order[cut:])
            if hi_left < lo_right - 1e-4:
                balance = abs(2 * cut - len(order))
                if best is None or balance < best[0]:
                    best = (balance, cut, (hi_left + lo_right) / 2)
        if best:
            _b, cut, c = best
            plane = tuple(-c if k == 3 else (1.0 if k == axis else 0.0) for k in range(4))
            return Node(plane, AXIS_CODE, _kd(order[:cut]), _kd(order[cut:]))
    # bounds interleave on every axis: one exact polygon BSP of these solids (no axis splits)
    return _original([p for i in items for p in i[0]], axis_threshold=10 ** 9)


def _solid_of(poly):
    prov = _state["provenance"]
    if prov is None or poly.code >= len(prov):
        return None
    src = prov[poly.code]
    if src.get("kind") != "AUTHORED_OBJECT":
        return None
    ranges = _state["ranges"].get(src.get("mesh"))
    if not ranges:
        return None
    t = src.get("triangle", -1)
    starts = [r[0] for r in ranges]
    k = bisect.bisect_right(starts, t) - 1
    if k >= 0 and ranges[k][0] <= t < ranges[k][1]:
        return (src["mesh"], k)
    return None


def build_solid_bsp_objects(polys, **kw):
    groups = {}
    for poly in polys:
        key = _solid_of(poly)
        if key is None:
            return _original(polys, **kw)
        groups.setdefault(key, []).append(poly)
    if not groups:
        return _original(polys, **kw)
    from master_rallye.course_bsp import polygon
    from master_rallye.studio.dx_build import triangle_normal
    items = []
    for key, g in groups.items():
        code = g[0].code
        full = [polygon(list(t), triangle_normal(*t), code) for t in _state["solids"][key]]
        full = [q for q in full if q is not None]
        items.append((full, *_bounds(full)))
    return _kd(items)


def collision_polygons_recorded(*a, **kw):
    polys, provenance, stats = _original_polygons(*a, **kw)
    _state["provenance"] = provenance
    return polys, provenance, stats


def install(project):
    _state["ranges"] = {mesh: sorted(r) for mesh, r in project.extras.get("evo2_solids", {}).items()}
    meshes = {m.id: m for m in project.meshes}
    for mesh_id, ranges in _state["ranges"].items():
        mesh = meshes[mesh_id]
        for k, (a, b) in enumerate(ranges):
            _state["solids"][(mesh_id, k)] = [tuple(tuple(mesh.positions[3 * mesh.triangles[3 * t + j]:3 * mesh.triangles[3 * t + j] + 3])
                                                    for j in range(3)) for t in range(a, b)]
    collision.build_solid_bsp = build_solid_bsp_objects
    collision.collision_polygons = collision_polygons_recorded
