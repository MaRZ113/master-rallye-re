"""Regional PS2 BSP -> PC tag100 collision transplant (TRACK-COLL1A).

Independent of the renderer. Inputs are a parsed PS2 BSP (`ps2_bsp.Bsp`) and a `tag100_tree.Tree`; the module has three parts.

1. `ConvexCell` : convex polyhedron kept as faces (polygon + the plane equation it came from). Clipping by a half-space never recomputes the
   plane equations, so every output plane is exactly one of the float32 planes of the PS2 file or one of the region walls.
2. `solid_volumes(bsp, box)` : exact traversal of the PS2 BSP restricted to a box. Every leaf cell is the box cut by the planes on the path
   (front = sibling = n.p + d >= 0, back = child). A plain solid leaf contributes its whole cell, a plain empty leaf nothing, a payload leaf its
   cell cut by the run planes (solid where n.p + d <= -eps for every run plane, the rule of the original leaf class; an empty run is solid).
3. `transplant(tree, bsp, box)` : carve the box in the PC tree (solid -> empty, outside untouched), then fill every PS2 solid polytope
   (empty -> solid) with `Tree.apply_prepared`. Plane normals point from the solid to the empty side. Fill chains use a valid non-negative
   plane code taken from the PC descent path (never 0xFFFFFFFF, which generates no contacts).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
import tag100_tree as tt  # noqa: E402

PS2_EPS = 9.999999747378752e-05   # n.p + d <= -PS2_EPS is "behind" in the original payload test
EPS = 1e-7
MIN_VOLUME = 1e-4                 # polytopes below this volume (units^3) are slivers and reported, not transplanted


def _dot(n, p):
    return n[0] * p[0] + n[1] * p[1] + n[2] * p[2]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


class ConvexCell:
    """Convex polyhedron: faces = [(plane (nx, ny, nz, d), [vertices])], interior is n.p + d <= 0 for every face (outward normals)."""

    def __init__(self, faces):
        self.faces = faces

    @classmethod
    def box(cls, lo, hi):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        v = lambda x, y, z: (x, y, z)
        return cls([
            ((1.0, 0.0, 0.0, -x1), [v(x1, y0, z0), v(x1, y1, z0), v(x1, y1, z1), v(x1, y0, z1)]),
            ((-1.0, 0.0, 0.0, x0), [v(x0, y0, z0), v(x0, y0, z1), v(x0, y1, z1), v(x0, y1, z0)]),
            ((0.0, 1.0, 0.0, -y1), [v(x0, y1, z0), v(x0, y1, z1), v(x1, y1, z1), v(x1, y1, z0)]),
            ((0.0, -1.0, 0.0, y0), [v(x0, y0, z0), v(x1, y0, z0), v(x1, y0, z1), v(x0, y0, z1)]),
            ((0.0, 0.0, 1.0, -z1), [v(x0, y0, z1), v(x1, y0, z1), v(x1, y1, z1), v(x0, y1, z1)]),
            ((0.0, 0.0, -1.0, z0), [v(x0, y0, z0), v(x0, y1, z0), v(x1, y1, z0), v(x1, y0, z0)]),
        ])

    def clip(self, plane):
        """Intersect with {p : n.p + d <= 0}. Returns a new ConvexCell, or None when the result has no volume."""
        n, d = plane[:3], plane[3]
        new_faces, has_cap = [], False
        for fp, poly in self.faces:
            s = [_dot(n, p) + d for p in poly]
            if max(s) <= EPS:
                new_faces.append((fp, poly))
                has_cap = has_cap or all(abs(x) <= 1e-5 for x in s)
                continue
            if min(s) >= -EPS:
                continue                      # whole face outside (or only touching the plane)
            out = []
            m = len(poly)
            for i in range(m):
                a, b = poly[i], poly[(i + 1) % m]
                sa, sb = s[i], s[(i + 1) % m]
                if sa <= EPS:
                    out.append(a)
                if (sa < -EPS and sb > EPS) or (sa > EPS and sb < -EPS):
                    t = sa / (sa - sb)
                    out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t))
            if len(out) >= 3:
                new_faces.append((fp, out))
        if not has_cap:
            on_plane = []
            for _, poly in new_faces:
                for p in poly:
                    if abs(_dot(n, p) + d) <= 1e-5 and not any(abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6 and abs(p[2] - q[2]) < 1e-6 for q in on_plane):
                        on_plane.append(p)
            if len(on_plane) >= 3:
                c = tuple(sum(p[i] for p in on_plane) / len(on_plane) for i in range(3))
                ax = max(range(3), key=lambda i: abs(n[i]))
                u = _cross(n, (1.0, 0.0, 0.0) if ax != 0 else (0.0, 1.0, 0.0))
                ul = math.sqrt(_dot(u, u))
                u = tuple(x / ul for x in u)
                w = _cross(n, u)
                on_plane.sort(key=lambda p: math.atan2(_dot(w, _sub(p, c)), _dot(u, _sub(p, c))))
                new_faces.append((tuple(plane), on_plane))
        cell = ConvexCell(new_faces)
        return cell if len(new_faces) >= 4 and cell.volume() > 1e-9 else None

    def vertices(self):
        out = []
        for _, poly in self.faces:
            for p in poly:
                if not any(abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6 and abs(p[2] - q[2]) < 1e-6 for q in out):
                    out.append(p)
        return out

    def volume(self):
        if not self.faces:
            return 0.0
        c = self.vertices()
        if not c:
            return 0.0
        o = tuple(sum(p[i] for p in c) / len(c) for i in range(3))
        v = 0.0
        for _, poly in self.faces:
            for i in range(1, len(poly) - 1):
                a, b, e = _sub(poly[0], o), _sub(poly[i], o), _sub(poly[i + 1], o)
                v += abs(_dot(a, _cross(b, e))) / 6.0
        return v

    def halfspaces(self):
        """Distinct face planes [((nx, ny, nz), d)] of faces with area."""
        out = []
        for fp, poly in self.faces:
            area = 0.0
            for i in range(1, len(poly) - 1):
                cr = _cross(_sub(poly[i], poly[0]), _sub(poly[i + 1], poly[0]))
                area += math.sqrt(_dot(cr, cr)) / 2
            if area < 1e-8:
                continue
            h = ((fp[0], fp[1], fp[2]), fp[3])
            if not any(max(abs(h[0][i] - k[0][i]) for i in range(3)) < 1e-6 and abs(h[1] - k[1]) < 1e-5 for k in out):
                out.append(h)
        return out


def solid_volumes(bsp, box_lo, box_hi):
    """Disjoint convex polytopes (ConvexCell) whose union is the PS2 solid inside the box, in depth-first back-before-front order.

    Returns (cells, stats). stats counts visited leaves and dropped sliver cells."""
    nodes = bsp.nodes
    cells, stats = [], {'leaves_visited': 0, 'solid_leaves': 0, 'payload_leaves': 0, 'empty_leaves': 0, 'sliver_cells_dropped': 0, 'sliver_volume': 0.0}
    stack = [(0, ConvexCell.box(box_lo, box_hi))]
    while stack:
        idx, cell = stack.pop()
        n = nodes[idx]
        if n.plane is None:
            stats['leaves_visited'] += 1
            if n.payload is None:
                if n.field_0 == 0xFFFFFFFF:
                    stats['solid_leaves'] += 1
                    out = cell
                else:
                    stats['empty_leaves'] += 1
                    continue
            else:
                stats['payload_leaves'] += 1
                start, count = n.payload[0] & 0xFFFFFF, n.payload[1] & 0xFF
                out = cell
                for nx, ny, nz, d, _code in bsp.plane_table[start:start + count]:
                    out = out.clip((nx, ny, nz, d + PS2_EPS))   # n.p + d <= -eps
                    if out is None:
                        break
                if out is None:
                    continue
            if out.volume() < MIN_VOLUME:
                stats['sliver_cells_dropped'] += 1
                stats['sliver_volume'] += out.volume()
                continue
            cells.append(out)
            continue
        nx, ny, nz, d = n.plane[:4]
        back = cell.clip((nx, ny, nz, d))                  # n.p + d <= 0
        front = cell.clip((-nx, -ny, -nz, -d))             # n.p + d >= 0
        # push front first so the back subtree is processed first
        if front is not None and n.sibling is not None:
            stack.append((n.sibling, front))
        if back is not None and n.child is not None:
            stack.append((n.child, back))
    return cells, stats


def box_halfspaces(lo, hi):
    return [((1, 0, 0), -hi[0]), ((-1, 0, 0), lo[0]), ((0, 1, 0), -hi[1]), ((0, -1, 0), lo[1]), ((0, 0, 1), -hi[2]), ((0, 0, -1), lo[2])]


class Snapshot:
    """Rollback point for a Tree: all lists only grow, existing nodes change only their links."""

    def __init__(self, tree):
        self.n = len(tree.plane)
        self.child, self.sib = list(tree.child), list(tree.sib)

    def restore(self, tree):
        for name in ('plane', 'code', 'f0', 'f1'):
            del getattr(tree, name)[self.n:]
        tree.child[:] = self.child
        tree.sib[:] = self.sib
        del tree.child[self.n:]
        del tree.sib[self.n:]


def transplant_brush(tree, bsp, box_lo, box_hi, code=None):
    """Reference method: carve the box, then fill every PS2 polytope with the brush API. Exact, but every fragmented PC leaf in the box gets a chain
    (Turkey3 rank 1: +134k nodes), so `bsp_graft.transplant` is the default. Mutates `tree`; raises (after restoring it) on any failure.

    Returns a report dict."""
    snap = Snapshot(tree)
    n0 = len(tree.plane)
    try:
        cells, stats = solid_volumes(bsp, box_lo, box_hi)
        if code is None:
            mid = ((box_lo[0] + box_hi[0]) / 2, (box_lo[1] + box_hi[1]) / 2, (box_lo[2] + box_hi[2]) / 2)
            code = tree.reference_code(mid)
            if code is None:
                raise ValueError('no valid plane code on the PC descent path at the region centre')
        if code >= 0x80000000:
            raise ValueError('plane code must be a non-negative int32')
        carved = tree.apply_brush(box_halfspaces(box_lo, box_hi), code, 'carve')
        nodes_after_carve = len(tree.plane)
        filled = 0
        planes_used = 0
        for cell in cells:
            hs = cell.halfspaces()
            planes_used += len(hs)
            filled += tree.apply_prepared(cell.vertices(), hs, code, 'fill')
        if not tree.counts_ok():
            raise ValueError('tag100 count invariants failed')
    except Exception:
        snap.restore(tree)
        raise
    return {'code': code, 'ps2_polytopes': len(cells), 'ps2_stats': stats, 'polytope_planes': planes_used,
            'carved_leaves': carved, 'filled_leaves': filled, 'nodes_before': n0, 'nodes_after_carve': nodes_after_carve,
            'nodes_after': len(tree.plane), 'nodes_added': len(tree.plane) - n0, 'polytope_volume': round(sum(c.volume() for c in cells), 3)}
