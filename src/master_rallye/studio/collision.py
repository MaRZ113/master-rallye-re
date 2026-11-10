"""Collision tree build, validation probes, differences and exact native extraction.

The game resolves collision against the tag100 solid-leaf BSP: ``s = n.p + d``,
``s <= 0`` continues in the back (child) subtree; back leaves are solid, front
leaves are empty. :func:`classify` reproduces that query exactly, so every
probe below reports what the game itself would answer for the same point.

:func:`extract_native_collision` turns a Retail tree back into editable
geometry: the course box is clipped down the tree into convex cells; for every
solid cell, faces lying on non-ground planes are clipped against the whole
tree and only fragments whose outside is empty space are kept. The result is
exactly the boundary between solid and empty space that the game uses, not a
guess; faces coplanar with land-database records are left to the terrain.
"""
from __future__ import annotations

import math
import struct
import time
from dataclasses import dataclass, field

from ..course_bsp import AXIS_CODE, Leaf, Node, build_solid_bsp
from .dx_build import collision_polygons, triangle_area, triangle_normal, tree_stats
from .model import ROLE_COLLISION, ROLE_TERRAIN, ROLE_WATER, CourseProject, Mesh, new_uid

EPS = 1e-4
BOX_CODE = -2          # faces of the extraction box (outer, unbounded regions of the tree)


def classify(root, p) -> bool:
    node = root
    while isinstance(node, Node):
        a, b, c, d = node.plane
        node = node.back if a * p[0] + b * p[1] + c * p[2] + d <= 0 else node.front
    return node.solid


def native_state(project: CourseProject):
    """(mesh, unchanged) of the collision recovered from a Retail tree, or (None, False)."""
    info = project.extras.get("native_collision")
    mesh = next((m for m in project.meshes if m.role == ROLE_COLLISION and m.source.startswith("retail-bsp")), None)
    if not info or mesh is None or "native_objects" not in project.blobs:
        return mesh, False
    from .native_graft import mesh_digest
    return mesh, mesh_digest(mesh) == info.get("digest")


def build_tree(project: CourseProject, *, progress=None):
    """The collision tree the build writes (see :mod:`.native_graft` for edited Retail courses)."""
    native, unchanged = native_state(project)
    exclude = {native.id} if (native is not None and unchanged) else set()
    polys, provenance, stats = collision_polygons(project, skirt=project.build.collision_skirt, exclude=exclude)
    t0 = time.time()
    tree = build_solid_bsp(polys) if polys else Leaf(False)
    if exclude:
        from ..course_bsp import tree_from_parsed
        from ..course_tag100 import parse_course_tag100_bytes
        from .native_graft import graft
        objects = tree_from_parsed(parse_course_tag100_bytes(project.blobs["native_objects"], "native", allow_trailing=True))
        info = project.extras["native_collision"]
        xs = [p[k] for poly in polys for p in poly.points for k in (0,)] or [0.0]
        lo = [min(info["lo"][k], min(p[k] for poly in polys for p in poly.points)) for k in range(3)]
        hi = [max(info["hi"][k], max(p[k] for poly in polys for p in poly.points)) for k in range(3)]
        tree, gstats = graft(objects, polys, tree, lo, hi)
        stats["native_graft"] = gstats
    elif native is not None:
        stats["native_graft"] = "native collision edited: rebuilt by solid union of its cells"
    stats["build_seconds"] = round(time.time() - t0, 2)
    stats.update(tree_stats(tree))
    return tree, provenance, stats


# ---------------------------------------------------------------------- height lookup
class HeightField:
    """Spatial hash of terrain triangles for vertical ray queries (game space, Y up)."""

    def __init__(self, triangles, cell: float = 10.0):
        self.cell = cell
        self.tris = triangles
        self.grid: dict = {}
        for i, (a, b, c) in enumerate(triangles):
            for gx in range(int(min(a[0], b[0], c[0]) // cell), int(max(a[0], b[0], c[0]) // cell) + 1):
                for gz in range(int(min(a[2], b[2], c[2]) // cell), int(max(a[2], b[2], c[2]) // cell) + 1):
                    self.grid.setdefault((gx, gz), []).append(i)

    def heights(self, x: float, z: float) -> list[float]:
        out = []
        for i in self.grid.get((int(x // self.cell), int(z // self.cell)), ()):
            (ax, ay, az), (bx, by, bz), (qx, qy, qz) = self.tris[i]
            det = (bz - qz) * (ax - qx) + (qx - bx) * (az - qz)
            if abs(det) < 1e-12:
                continue
            l1 = ((bz - qz) * (x - qx) + (qx - bx) * (z - qz)) / det
            l2 = ((qz - az) * (x - qx) + (ax - qx) * (z - qz)) / det
            l3 = 1.0 - l1 - l2
            if l1 >= -1e-7 and l2 >= -1e-7 and l3 >= -1e-7:
                out.append(l1 * ay + l2 * by + l3 * qy)
        return out

    def ground(self, x: float, z: float, below: float | None = None) -> float | None:
        hs = self.heights(x, z)
        if below is not None:
            hs = [h for h in hs if h <= below]
        return max(hs) if hs else None


def terrain_triangles(project: CourseProject, roles=(ROLE_TERRAIN,)):
    out = []
    for mesh in project.meshes_with(*roles):
        for t in range(mesh.triangle_count):
            pts = mesh.triangle_points(t)
            if triangle_area(*pts) > 1e-7:
                out.append(pts)
    return out


# ---------------------------------------------------------------------- probes
@dataclass
class CollisionIssue:
    kind: str          # hole | phantom | route_blocked | open_mesh | no_ground
    position: tuple
    detail: str
    severity: str = "warning"


@dataclass
class CollisionReport:
    samples: int = 0
    holes: int = 0
    route_holes: int = 0
    phantoms: int = 0
    route_samples: int = 0
    route_blocked: int = 0
    route_steps: int = 0
    issues: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def summary(self) -> dict:
        return {"samples": self.samples, "holes": self.holes, "route_holes": self.route_holes, "phantoms": self.phantoms,
                "route_samples": self.route_samples, "route_blocked": self.route_blocked, "route_steps": self.route_steps,
                "issues": len(self.issues), **self.stats}


def validate_tree(project: CourseProject, tree, *, spacing: float = 6.0, offset: float = 0.3,
                  max_issues: int = 5000, route_clearance: float = 2.2, route_radius: float = 15.0) -> CollisionReport:
    """Probe the tree the way the game queries it.

    * terrain: on a ``spacing`` grid, 0.3 below the top drivable surface must be
      solid (else a car falls through: *hole*) and 0.3 above it empty (else an
      invisible bump: *phantom*);
    * route: every RaceLine sample needs empty space from 0.5 to ``route_clearance``
      above the ground (else the AI/players hit an invisible or solid wall);
    * collision meshes: the outside of each face must be empty.
    """
    report = CollisionReport()
    tris = terrain_triangles(project)
    if not tris:
        report.issues.append(CollisionIssue("no_ground", (0, 0, 0), "project has no terrain", "error"))
        return report
    hf = HeightField(tris)
    xs = [p[0] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    route_grid: dict = {}
    rpts = project.route.points
    for i in range(len(rpts) - 1):
        a, b = rpts[i], rpts[i + 1]
        steps = max(1, int(math.dist(a, b) // 4.0))
        for k in range(steps + 1):
            px, pz = a[0] + (b[0] - a[0]) * k / steps, a[2] + (b[2] - a[2]) * k / steps
            route_grid.setdefault((int(px // 20), int(pz // 20)), []).append((px, pz))

    def near_route(x, z, radius=route_radius):
        for gx in (int(x // 20) - 1, int(x // 20), int(x // 20) + 1):
            for gz in (int(z // 20) - 1, int(z // 20), int(z // 20) + 1):
                for px, pz in route_grid.get((gx, gz), ()):
                    if (px - x) ** 2 + (pz - z) ** 2 <= radius * radius:
                        return True
        return False

    def add(issue):
        if len(report.issues) < max_issues:
            report.issues.append(issue)
    x = x0 + spacing / 2
    while x < x1:
        z = z0 + spacing / 2
        while z < z1:
            hs = sorted(hf.heights(x, z), reverse=True)
            if hs:
                top = hs[0]
                gap_below = (hs[0] - hs[1]) if len(hs) > 1 else 1e9
                report.samples += 1
                if gap_below > 2 * offset + 0.05:
                    if not classify(tree, (x, top - offset, z)):
                        report.holes += 1
                        near = near_route(x, z)
                        report.route_holes += near
                        add(CollisionIssue("hole", (x, top, z), "empty space just under the terrain surface"
                                           + (" next to the AI route" if near else " (off the route)"),
                                           "error" if near else "warning"))
                if classify(tree, (x, top + offset, z)):
                    report.phantoms += 1
                    add(CollisionIssue("phantom", (x, top, z), "solid space just above the terrain surface"))
            z += spacing
        x += spacing
    # route clearance
    pts = project.route.points
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        steps = max(1, int(math.dist(a, b) // 2.0))
        for s in range(steps):
            t = s / steps
            px, pz = a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t
            py = a[1] + (b[1] - a[1]) * t
            ground = hf.ground(px, pz, below=py + 3.0)
            report.route_samples += 1
            if ground is None:
                report.route_blocked += 1
                add(CollisionIssue("route_blocked", (px, py, pz), "route leaves the terrain (no ground below)", "error"))
                continue
            wall = next((h for h in (1.2, route_clearance) if classify(tree, (px, ground + h, pz))), None)
            if wall is not None:
                report.route_blocked += 1
                add(CollisionIssue("route_blocked", (px, ground + wall, pz),
                                   f"solid collision {wall:.1f} m above the road on the AI route (wall)", "error"))
            elif classify(tree, (px, ground + 0.5, pz)):
                report.route_steps += 1
                add(CollisionIssue("route_step", (px, ground + 0.5, pz),
                                   "solid collision 0.5 m above the road surface on the AI route (step or bump)"))
    # collision meshes: outside must be empty
    open_faces = 0
    for mesh in project.meshes_with(ROLE_COLLISION):
        for t in range(mesh.triangle_count):
            a, b, c = mesh.triangle_points(t)
            n = triangle_normal(a, b, c)
            length = math.sqrt(sum(v * v for v in n))
            if length < 1e-9:
                continue
            n = tuple(v / length for v in n)
            cen = tuple((a[k] + b[k] + c[k]) / 3 for k in range(3))
            if classify(tree, tuple(cen[k] + 0.05 * n[k] for k in range(3))):
                open_faces += 1
    report.stats["collision_faces_buried"] = open_faces
    return report


def tree_difference(old, new, project: CourseProject, *, spacing: float = 4.0, heights=(-0.5, 0.5, 1.5, 3.0),
                    limit: int = 20000) -> list[tuple]:
    """Points (x, y, z, was_solid, now_solid) where two trees disagree, sampled over the terrain."""
    tris = terrain_triangles(project)
    if not tris:
        return []
    hf = HeightField(tris)
    xs = [p[0] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    out = []
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    x = x0
    while x <= x1 and len(out) < limit:
        z = z0
        while z <= z1 and len(out) < limit:
            g = hf.ground(x, z)
            if g is not None:
                for h in heights:
                    p = (x, g + h, z)
                    a, b = classify(old, p), classify(new, p)
                    if a != b:
                        out.append((x, g + h, z, a, b))
            z += spacing
        x += spacing
    return out


# ---------------------------------------------------------------------- native extraction
def _split_poly(points, plane):
    a, b, c, d = plane
    dist = [a * p[0] + b * p[1] + c * p[2] + d for p in points]
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
    return (back if len(back) >= 3 else None), (front if len(front) >= 3 else None), dist


def _order_on_plane(points, normal):
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    cz = sum(p[2] for p in points) / len(points)
    ax = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = (normal[1] * ax[2] - normal[2] * ax[1], normal[2] * ax[0] - normal[0] * ax[2], normal[0] * ax[1] - normal[1] * ax[0])
    ul = math.sqrt(sum(v * v for v in u)) or 1.0
    u = tuple(v / ul for v in u)
    v = (normal[1] * u[2] - normal[2] * u[1], normal[2] * u[0] - normal[0] * u[2], normal[0] * u[1] - normal[1] * u[0])
    uniq = []
    for p in points:
        if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > 1e-5 for q in uniq):
            uniq.append(p)
    uniq.sort(key=lambda p: math.atan2((p[0] - cx) * v[0] + (p[1] - cy) * v[1] + (p[2] - cz) * v[2],
                                       (p[0] - cx) * u[0] + (p[1] - cy) * u[1] + (p[2] - cz) * u[2]))
    return uniq


def _hull_on_plane(points, normal):
    """2-D convex hull (monotone chain) of coplanar points, returned in 3-D."""
    ax = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = (normal[1] * ax[2] - normal[2] * ax[1], normal[2] * ax[0] - normal[0] * ax[2], normal[0] * ax[1] - normal[1] * ax[0])
    ul = math.sqrt(sum(v * v for v in u)) or 1.0
    u = tuple(v / ul for v in u)
    v = (normal[1] * u[2] - normal[2] * u[1], normal[2] * u[0] - normal[0] * u[2], normal[0] * u[1] - normal[1] * u[0])
    flat = sorted({(round(p[0] * u[0] + p[1] * u[1] + p[2] * u[2], 4), round(p[0] * v[0] + p[1] * v[1] + p[2] * v[2], 4)): p
                   for p in points}.items())
    if len(flat) < 3:
        return []
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for item in flat:
        while len(lower) >= 2 and cross(lower[-2][0], lower[-1][0], item[0]) <= 1e-9:
            lower.pop()
        lower.append(item)
    for item in reversed(flat):
        while len(upper) >= 2 and cross(upper[-2][0], upper[-1][0], item[0]) <= 1e-9:
            upper.pop()
        upper.append(item)
    return [p for _, p in lower[:-1] + upper[:-1]]


def _split_cell(faces, plane, code):
    """Split a convex cell (faces = [(points, outward normal, code)]) by ``plane``."""
    back, front, cut = [], [], []
    for points, normal, fcode in faces:
        b, f, dist = _split_poly(points, plane)
        if b is not None and f is not None:
            back.append((b, normal, fcode)); front.append((f, normal, fcode))
        elif b is not None and all(v <= EPS for v in dist):
            back.append((points, normal, fcode))
        elif f is not None:
            front.append((points, normal, fcode))
        for p, dv in zip(points, dist):
            if abs(dv) <= EPS:
                cut.append(p)
        n = len(points)
        for i in range(n):
            dp, dq = dist[i], dist[(i + 1) % n]
            if (dp < -EPS and dq > EPS) or (dp > EPS and dq < -EPS):
                t = dp / (dp - dq)
                p, q = points[i], points[(i + 1) % n]
                cut.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, p[2] + (q[2] - p[2]) * t))
    n3 = plane[:3]
    if len(cut) >= 3:
        ring = _order_on_plane(cut, n3)
        if len(ring) >= 3:
            back.append((ring, n3, code))                          # back cell: outward = +normal
            front.append((list(reversed(ring)), (-n3[0], -n3[1], -n3[2]), code))
    return (back if len(back) >= 4 else None), (front if len(front) >= 4 else None)


def _box(lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    return [
        ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1.0, 0.0, 0.0), BOX_CODE),
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1.0, 0.0, 0.0), BOX_CODE),
        ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0.0, -1.0, 0.0), BOX_CODE),
        ([(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], (0.0, 1.0, 0.0), BOX_CODE),
        ([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], (0.0, 0.0, -1.0), BOX_CODE),
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0.0, 0.0, 1.0), BOX_CODE),
    ]


def _clip_to_empty(root, points, normal, offset=0.02):
    """Fragments of a polygon whose outside (``offset`` along ``normal``) is empty space."""
    shifted = [(p[0] + normal[0] * offset, p[1] + normal[1] * offset, p[2] + normal[2] * offset) for p in points]
    out, stack = [], [(root, shifted)]
    while stack:
        node, poly = stack.pop()
        if isinstance(node, Leaf):
            if not node.solid:
                out.append([(p[0] - normal[0] * offset, p[1] - normal[1] * offset, p[2] - normal[2] * offset) for p in poly])
            continue
        b, f, dist = _split_poly(poly, node.plane)
        if all(abs(v) <= EPS for v in dist):
            # coplanar: the game decides s <= 0 -> back
            stack.append((node.back, poly))
            continue
        if b is not None and not all(v >= -EPS for v in dist):
            stack.append((node.back, b))
        if f is not None and not all(v <= EPS for v in dist):
            stack.append((node.front, f))
    return out


def extract_native_collision(root, lo, hi, *, ground_planes=(), progress=None, max_cells: int = 2_000_000):
    """Return ``(triangles, stats)``: solid/empty boundary faces not coplanar with ``ground_planes``.

    ``ground_planes`` is an iterable of ``(nx, ny, nz, d)`` land-record planes;
    their faces belong to the terrain and are skipped.
    """
    ground = {}
    for n0, n1, n2, d in ground_planes:
        if any(math.isnan(v) for v in (n0, n1, n2, d)):
            continue
        key = (round(n0, 2), round(n1, 2), round(n2, 2), round(d, 1))
        ground[key] = True
        ground[(round(-n0, 2), round(-n1, 2), round(-n2, 2), round(-d, 1))] = True

    def is_ground(normal, points):
        d = -(normal[0] * points[0][0] + normal[1] * points[0][1] + normal[2] * points[0][2])
        for dd in (0.0, 0.05, -0.05):
            if (round(normal[0], 2), round(normal[1], 2), round(normal[2], 2), round(d + dd, 1)) in ground:
                return True
        return False

    pad = 5.0
    lo = (lo[0] - pad, lo[1] - pad, lo[2] - pad)
    hi = (hi[0] + pad, hi[1] + pad, hi[2] + pad)
    faces_out, stats = [], {"cells": 0, "solid_cells": 0, "candidate_faces": 0, "ground_faces": 0, "kept_fragments": 0}
    stack = [(root, _box(lo, hi))]
    started = time.time()
    while stack:
        node, cell = stack.pop()
        stats["cells"] += 1
        if stats["cells"] > max_cells:
            raise RuntimeError("native collision extraction exceeded its cell budget")
        if progress and stats["cells"] % 20000 == 0:
            progress("extract", stats["cells"])
        if isinstance(node, Leaf):
            if not node.solid:
                continue
            stats["solid_cells"] += 1
            for points, normal, code in cell:
                if code in (AXIS_CODE, BOX_CODE):
                    continue
                stats["candidate_faces"] += 1
                if is_ground(normal, points):
                    stats["ground_faces"] += 1
                    continue
                for frag in _clip_to_empty(root, points, normal):
                    if len(frag) >= 3:
                        faces_out.append((frag, normal, code))
                        stats["kept_fragments"] += 1
            continue
        back, front = _split_cell(cell, node.plane, node.code)
        if back is not None:
            stack.append((node.back, back))
        if front is not None:
            stack.append((node.front, front))
    # Plane code = source triangle index (Retail cooker): the fragments of one code are pieces of one
    # source polygon. Their convex hull on the plane restores that polygon (its buried parts are inside
    # solid space anyway), so the editable mesh has source-sized faces instead of cell fragments.
    by_code: dict = {}
    for frag, normal, code in faces_out:
        by_code.setdefault((code, round(normal[0], 3), round(normal[1], 3), round(normal[2], 3)),
                           (normal, []))[1].append(frag)
    triangles = []
    merged = 0

    def fan(ring, normal):
        for k in range(1, len(ring) - 1):
            tri = (ring[0], ring[k], ring[k + 1])
            n = triangle_normal(*tri)
            if n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] < 0:
                tri = (ring[0], ring[k + 1], ring[k])
            if triangle_area(*tri) > 1e-5:
                triangles.append(tri)

    def area(ring):
        return sum(triangle_area(ring[0], ring[k], ring[k + 1]) for k in range(1, len(ring) - 1))
    for (code, *_), (normal, frags) in by_code.items():
        ring = _hull_on_plane([p for f in frags for p in f], normal) if len(frags) > 1 else frags[0]
        # The hull replaces the fragments only when it covers exactly their area (a convex union):
        # then it is the source polygon's visible part; otherwise the exact fragments are kept.
        if len(frags) > 1 and ring and abs(area(ring) - sum(area(f) for f in frags)) <= 1e-3 * max(1.0, area(ring)):
            fan(ring, normal)
            merged += 1
        else:
            for f in frags:
                fan(f, normal)
    stats["merged_polygons"] = merged
    stats["source_polygons"] = len(by_code)
    stats["triangles"] = len(triangles)
    stats["seconds"] = round(time.time() - started, 1)
    return triangles, stats


def triangles_to_mesh(triangles, *, name: str, role: str, material: str, source: str) -> Mesh:
    mesh = Mesh(id=new_uid("mesh_"), name=name, role=role, materials=[material], source=source)
    lookup = {}
    for tri in triangles:
        for p in tri:
            key = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
            if key not in lookup:
                lookup[key] = len(mesh.positions) // 3
                mesh.positions.extend(p)
            mesh.triangles.append(lookup[key])
        mesh.tri_material.append(0)
    return mesh


# ---------------------------------------------------------------------- authoring helpers
def box_proxy(lo, hi, *, yaw: float = 0.0, center=None):
    """Closed box (12 triangles, outward winding) in game space; ``yaw`` degrees about Y."""
    cx, cz = center if center is not None else ((lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2)
    hx, hz = (hi[0] - lo[0]) / 2, (hi[2] - lo[2]) / 2
    y0, y1 = lo[1], hi[1]
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    def pt(sx, y, sz):
        x, z = sx * hx, sz * hz
        return (cx + x * ca + z * sa, y, cz - x * sa + z * ca)
    v = [pt(-1, y0, -1), pt(1, y0, -1), pt(1, y0, 1), pt(-1, y0, 1),
         pt(-1, y1, -1), pt(1, y1, -1), pt(1, y1, 1), pt(-1, y1, 1)]
    quads = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    tris = []
    centre = (cx, (y0 + y1) / 2, cz)
    for q in quads:
        for tri in ((v[q[0]], v[q[1]], v[q[2]]), (v[q[0]], v[q[2]], v[q[3]])):
            n = triangle_normal(*tri)
            c = tuple(sum(p[k] for p in tri) / 3 for k in range(3))
            if sum(n[k] * (c[k] - centre[k]) for k in range(3)) < 0:
                tri = (tri[0], tri[2], tri[1])
            tris.append(tri)
    return tris


def convex_hull(points):
    """3-D convex hull (gift-wrapping-free incremental) returning outward triangles."""
    pts = []
    for p in points:
        if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > 1e-4 for q in pts):
            pts.append(tuple(p))
        if len(pts) > 600:
            break
    if len(pts) < 4:
        return []
    def plane_of(a, b, c):
        n = triangle_normal(pts[a], pts[b], pts[c])
        return n, -(n[0] * pts[a][0] + n[1] * pts[a][1] + n[2] * pts[a][2])
    # initial tetrahedron
    i0 = 0
    i1 = max(range(len(pts)), key=lambda i: sum((pts[i][k] - pts[i0][k]) ** 2 for k in range(3)))
    def line_dist(i):
        u = [pts[i1][k] - pts[i0][k] for k in range(3)]
        w = [pts[i][k] - pts[i0][k] for k in range(3)]
        c = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        return sum(v * v for v in c)
    i2 = max(range(len(pts)), key=line_dist)
    n, d = plane_of(i0, i1, i2)
    i3 = max(range(len(pts)), key=lambda i: abs(n[0] * pts[i][0] + n[1] * pts[i][1] + n[2] * pts[i][2] + d))
    if abs(n[0] * pts[i3][0] + n[1] * pts[i3][1] + n[2] * pts[i3][2] + d) < 1e-6:
        return []
    centre = tuple(sum(pts[i][k] for i in (i0, i1, i2, i3)) / 4 for k in range(3))
    faces = []
    for f in ((i0, i1, i2), (i0, i1, i3), (i0, i2, i3), (i1, i2, i3)):
        n, d = plane_of(*f)
        if n[0] * centre[0] + n[1] * centre[1] + n[2] * centre[2] + d > 0:
            f = (f[0], f[2], f[1])
        faces.append(f)
    for i in range(len(pts)):
        if i in (i0, i1, i2, i3):
            continue
        p = pts[i]
        visible = []
        for f in faces:
            n, d = plane_of(*f)
            if n[0] * p[0] + n[1] * p[1] + n[2] * p[2] + d > 1e-7:
                visible.append(f)
        if not visible:
            continue
        edges = {}
        for f in visible:
            for e in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
                if (e[1], e[0]) in edges:
                    del edges[(e[1], e[0])]
                else:
                    edges[e] = True
        faces = [f for f in faces if f not in visible] + [(a, b, i) for a, b in edges]
    return [(pts[a], pts[b], pts[c]) for a, b, c in faces]


def grounded_proxy(mesh_points, heightfield: HeightField | None, *, kind: str = "hull", depth: float = 0.5):
    """Collision proxy for a static object: convex hull or box, extended ``depth`` below the ground."""
    pts = list(mesh_points)
    if not pts:
        return []
    if heightfield is not None:
        ground = [heightfield.ground(p[0], p[2], below=p[1] + 0.5) for p in pts]
        floor = min((g for g in ground if g is not None), default=min(p[1] for p in pts)) - depth
        pts = pts + [(p[0], floor, p[2]) for p in pts if p[1] - floor < 2.0 * depth + 0.5]
    if kind == "box":
        lo = tuple(min(p[k] for p in pts) for k in range(3))
        hi = tuple(max(p[k] for p in pts) for k in range(3))
        return box_proxy(lo, hi)
    return convex_hull(pts)


def visualise_tree_surface(root, project: CourseProject, *, spacing: float = 4.0):
    """Sample of the solid/empty boundary over the terrain: points where the game ground is (for viewing)."""
    tris = terrain_triangles(project, roles=(ROLE_TERRAIN, ROLE_WATER))
    hf = HeightField(tris)
    out = []
    xs = [p[0] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    x = x0
    while x <= x1:
        z = z0
        while z <= z1:
            g = hf.ground(x, z)
            if g is not None:
                lo, hi = g - 4.0, g + 4.0
                if classify(root, (x, lo, z)) and not classify(root, (x, hi, z)):
                    for _ in range(18):
                        mid = (lo + hi) / 2
                        if classify(root, (x, mid, z)):
                            lo = mid
                        else:
                            hi = mid
                    out.append((x, (lo + hi) / 2, z))
            z += spacing
        x += spacing
    return out


def extract_native_solids(root, lo, hi, *, heights=None, ground_planes=(), min_lift: float = 0.3,
                          max_span: float = 150.0, progress=None, max_cells: int = 2_000_000):
    """Closed convex solids of a native tree that stand above the ground (objects, walls, proxies).

    Every solid leaf of a BSP is a convex cell; the cells above the terrain are exactly the game's
    object collision. A cell is kept when part of it rises ``min_lift`` above the ground under it and it
    has a face towards empty space that is not ground (thin slabs of cooker artefacts on the ground and
    the ground itself stay with the terrain). Each returned solid is a list of outward faces.
    """
    ground = set()
    for n0, n1, n2, d in ground_planes:
        if not any(math.isnan(v) for v in (n0, n1, n2, d)):
            ground.add((round(n0, 2), round(n1, 2), round(n2, 2), round(d, 1)))
            ground.add((round(-n0, 2), round(-n1, 2), round(-n2, 2), round(-d, 1)))

    def is_ground(normal, points):
        d = -(normal[0] * points[0][0] + normal[1] * points[0][1] + normal[2] * points[0][2])
        return any((round(normal[0], 2), round(normal[1], 2), round(normal[2], 2), round(d + dd, 1)) in ground
                   for dd in (0.0, 0.05, -0.05))
    pad = 5.0
    stack = [(root, _box((lo[0] - pad, lo[1] - pad, lo[2] - pad), (hi[0] + pad, hi[1] + pad, hi[2] + pad)))]
    solids, stats = [], {"cells": 0, "solid_cells": 0, "object_cells": 0}
    while stack:
        node, cell = stack.pop()
        stats["cells"] += 1
        if stats["cells"] > max_cells:
            raise RuntimeError("native collision extraction exceeded its cell budget")
        if progress and stats["cells"] % 20000 == 0:
            progress("extract", stats["cells"])
        if isinstance(node, Leaf):
            if not node.solid:
                continue
            stats["solid_cells"] += 1
            pts = [p for face, _, _ in cell for p in face]
            # Outer solid regions (Retail corridors are closed by $skirt walls: everything outside is solid)
            # touch the extraction box or are huge; the Studio build closes the map edge itself.
            span = max(max(p[k] for p in pts) - min(p[k] for p in pts) for k in (0, 2))
            if any(code == BOX_CODE for _, _, code in cell) or span > max_span:
                stats["outer_cells"] = stats.get("outer_cells", 0) + 1
                continue
            if heights is not None:
                lift = 0.0
                for p in pts:
                    g = heights(p[0], p[2])
                    lift = max(lift, p[1] - g if g is not None else 0.0)
                if lift < min_lift:
                    continue
            boundary = False
            for face, normal, code in cell:
                if code in (AXIS_CODE, BOX_CODE) or is_ground(normal, face):
                    continue
                cen = tuple(sum(p[k] for p in face) / len(face) for k in range(3))
                if not classify(root, tuple(cen[k] + 0.02 * normal[k] for k in range(3))):
                    boundary = True
                    break
            if boundary:
                solids.append([(face, normal) for face, normal, _ in cell])
                stats["object_cells"] += 1
            continue
        back, front = _split_cell(cell, node.plane, node.code)
        if back is not None:
            stack.append((node.back, back))
        if front is not None:
            stack.append((node.front, front))
    return solids, stats


def solids_to_mesh(solids, *, name: str, material: str, source: str) -> Mesh:
    """One mesh, each solid its own closed vertex island (no welding across solids)."""
    mesh = Mesh(id=new_uid("mesh_"), name=name, role=ROLE_COLLISION, materials=[material], source=source)
    for solid in solids:
        lookup = {}
        for face, normal in solid:
            ring = []
            for p in face:
                key = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
                if key not in lookup:
                    lookup[key] = len(mesh.positions) // 3
                    mesh.positions.extend(p)
                if not ring or ring[-1] != lookup[key]:
                    ring.append(lookup[key])
            if len(ring) > 1 and ring[0] == ring[-1]:
                ring.pop()
            for k in range(1, len(ring) - 1):
                tri = (ring[0], ring[k], ring[k + 1])
                pts = [mesh.vertex(i) for i in tri]
                n = triangle_normal(*pts)
                if triangle_area(*pts) < 1e-6:
                    continue
                if n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] < 0:
                    tri = (tri[0], tri[2], tri[1])
                mesh.triangles.extend(tri)
                mesh.tri_material.append(0)
    return mesh
