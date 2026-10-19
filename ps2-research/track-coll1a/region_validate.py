"""Offline validation of a regional PS2 BSP -> PC tag100 transplant (TRACK-COLL1A).

Three trees are compared against the PS2 BSP: the original PC tree, the current (TRACK-GROUND1) tree and the candidate. Everything is exact leaf
traversal or deterministic sampling (fixed generator, no hidden randomness).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
import bsp_query as q  # noqa: E402
import tag100_tree as tt  # noqa: E402

SOLID = tt.SOLID


def tree_solid(tree, p):
    return tree.f0[tree.classify(p)] == SOLID


def tree_segment_leaves(tree, a, b):
    """Leaves crossed by a->b in order: [(leaf, t0, t1)]. Front half-space = sibling."""
    out = []
    stack = [(0, 0.0, 1.0)]
    while stack:
        i, t0, t1 = stack.pop()
        pl = tree.plane[i]
        if pl is None:
            out.append((i, t0, t1))
            continue
        nx, ny, nz, d = pl[:4]
        s0 = nx * (a[0] + (b[0] - a[0]) * t0) + ny * (a[1] + (b[1] - a[1]) * t0) + nz * (a[2] + (b[2] - a[2]) * t0) + d
        s1 = nx * (a[0] + (b[0] - a[0]) * t1) + ny * (a[1] + (b[1] - a[1]) * t1) + nz * (a[2] + (b[2] - a[2]) * t1) + d
        front, back = tree.sib[i], tree.child[i]
        if s0 >= 0 and s1 >= 0:
            stack.append((front, t0, t1))
        elif s0 < 0 and s1 < 0:
            stack.append((back, t0, t1))
        else:
            tm = t0 + (t1 - t0) * (s0 / (s0 - s1))
            first, second = (front, back) if s0 >= 0 else (back, front)
            stack.append((second, tm, t1))
            stack.append((first, t0, tm))
    return out


MIN_SOLID = 1e-4   # a solid interval shorter than this (units) is a ray touching a cell edge or corner, not a surface


def tree_first_solid_t(tree, a, b):
    length = math.dist(a, b)
    for i, t0, t1 in tree_segment_leaves(tree, a, b):
        if tree.f0[i] == SOLID and (t1 - t0) * length > MIN_SOLID:
            return t0
    return None


def tree_solid_intervals(tree, a, b):
    """Merged solid parameter intervals along a->b."""
    out = []
    length = math.dist(a, b)
    for i, t0, t1 in tree_segment_leaves(tree, a, b):
        if tree.f0[i] == SOLID and (t1 - t0) * length > MIN_SOLID:
            if out and abs(out[-1][1] - t0) < 1e-9:
                out[-1][1] = t1
            else:
                out.append([t0, t1])
    return out


def clip_segment_to_box(a, b, lo, hi):
    t0, t1 = 0.0, 1.0
    for k in range(3):
        da = b[k] - a[k]
        if abs(da) < 1e-12:
            if a[k] < lo[k] or a[k] > hi[k]:
                return None
            continue
        ta, tb = (lo[k] - a[k]) / da, (hi[k] - a[k]) / da
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 >= t1:
            return None
    return t0, t1


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


class Lcg:
    """Deterministic generator for sample points."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF

    def next(self):
        self.s = (1664525 * self.s + 1013904223) & 0xFFFFFFFF
        return self.s / 4294967296.0


def grid_columns(lo, hi, step=2.0, inset=1.0):
    xs, zs = [], []
    x = lo[0] + inset
    while x < hi[0] - 1e-9:
        xs.append(x)
        x += step
    z = lo[2] + inset
    while z < hi[2] - 1e-9:
        zs.append(z)
        z += step
    return [(x, z) for x in xs for z in zs]


def first_contact_table(bsp, trees, lo, hi, step=2.0, tol=0.05):
    """First contact (top to bottom) of every grid column in the box for the PS2 BSP and each named tree."""
    top, bottom = hi[1] - 1e-3, lo[1] + 1e-3
    rows, stats = [], {k: {'agree': 0, 'higher': 0, 'lower': 0, 'max_abs': 0.0, 'sum_abs': 0.0, 'compared': 0} for k in trees}
    for x, z in grid_columns(lo, hi, step):
        a, b = (x, top, z), (x, bottom, z)
        t = q.ps2_first_solid_t(bsp, a, b)
        h_ps2 = None if t is None else top + (bottom - top) * t
        row = {'x': x, 'z': z, 'ps2': h_ps2}
        for name, tree in trees.items():
            tt_ = tree_first_solid_t(tree, a, b)
            h = None if tt_ is None else top + (bottom - top) * tt_
            row[name] = h
            s = stats[name]
            if h_ps2 is None and h is None:
                s['agree'] += 1
            elif h_ps2 is None or h is None:
                s['lower' if h is None else 'higher'] += 1
            else:
                e = h - h_ps2
                s['compared'] += 1
                s['max_abs'] = max(s['max_abs'], abs(e))
                s['sum_abs'] += abs(e)
                s['agree' if abs(e) <= tol else ('higher' if e > 0 else 'lower')] += 1
        rows.append(row)
    for s in stats.values():
        s['mean_abs'] = round(s['sum_abs'] / s['compared'], 4) if s['compared'] else None
        s['max_abs'] = round(s['max_abs'], 4)
        del s['sum_abs']
    return rows, stats


def classification_table(bsp, trees, lo, hi, rows, count_random=3000, seed=20261019):
    """Solid/empty agreement with the PS2 BSP at heights around each column's PS2 contact and at seeded random points in the box."""
    offsets = (-6.0, -2.0, -0.5, -0.1, 0.1, 0.5, 2.0, 5.0)
    pts = []
    for r in rows:
        if r['ps2'] is None:
            continue
        for dy in offsets:
            y = r['ps2'] + dy
            if lo[1] < y < hi[1]:
                pts.append((r['x'], y, r['z']))
    g = Lcg(seed)
    for _ in range(count_random):
        pts.append((lo[0] + (hi[0] - lo[0]) * g.next(), lo[1] + (hi[1] - lo[1]) * g.next(), lo[2] + (hi[2] - lo[2]) * g.next()))
    res = {name: {'mismatch': 0, 'ps2_solid_missing': 0, 'ps2_empty_solid': 0} for name in trees}
    for p in pts:
        s = q.ps2_is_solid(bsp, p)
        for name, tree in trees.items():
            c = tree_solid(tree, p)
            if c != s:
                res[name]['mismatch'] += 1
                res[name]['ps2_solid_missing' if s else 'ps2_empty_solid'] += 1
    return len(pts), res


def region_rays(lo, hi, margin=24.0, count=240, seed=7):
    """Deterministic rays crossing the box: horizontal along x and z, and diagonals, at heights through the ground layer, plus rays that start
    inside, end inside, or graze a wall. Every ray starts and ends outside the box expanded by `margin` unless noted."""
    g = Lcg(seed)
    rays = []
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    for k in range(count):
        y = lo[1] + (hi[1] - lo[1]) * g.next()
        kind = k % 4
        if kind == 0:     # along x
            z = lo[2] + (hi[2] - lo[2]) * g.next()
            rays.append(('x', (lo[0] - margin, y, z), (hi[0] + margin, y, z)))
        elif kind == 1:   # along z
            x = lo[0] + (hi[0] - lo[0]) * g.next()
            rays.append(('z', (x, y, lo[2] - margin), (x, y, hi[2] + margin)))
        elif kind == 2:   # diagonal in the horizontal plane
            f = g.next() * 2 - 1
            rays.append(('diag', (lo[0] - margin, y, lo[2] - margin + f * 10), (hi[0] + margin, y + (g.next() - .5) * 6, hi[2] + margin - f * 10)))
        else:             # steep diagonal through the ground layer
            rays.append(('steep', (lo[0] - margin * g.next(), hi[1] + 6, lo[2] - margin * g.next()),
                         (hi[0] + margin * g.next(), lo[1] - 6, hi[2] + margin * g.next())))
    return rays


def ray_check(bsp, tree_ref, tree_new, lo, hi, rays, tol=0.05):
    """For each ray: (a) inside the box the first solid distance of the candidate equals the PS2 one within `tol` (or both none);
    (b) outside the box the solid intervals of the candidate equal the reference (current) tree exactly."""
    inside_bad, outside_bad, n_inside = [], [], 0
    for kind, a, b in rays:
        length = math.dist(a, b)
        clip = clip_segment_to_box(a, b, lo, hi)
        if clip:
            n_inside += 1
            t0, t1 = clip
            pa, pb = lerp(a, b, t0), lerp(a, b, t1)
            tp_ = q.ps2_first_solid_t(bsp, pa, pb)
            tn = tree_first_solid_t(tree_new, pa, pb)
            seg = math.dist(pa, pb)
            if (tp_ is None) != (tn is None) or (tp_ is not None and abs(tp_ - tn) * seg > tol):
                inside_bad.append({'kind': kind, 'a': a, 'b': b, 'ps2_t': tp_, 'new_t': tn, 'segment': seg})
        # outside: remove the box part from both interval lists
        def outside(ints):
            res = []
            for i0, i1 in ints:
                if clip:
                    c0, c1 = clip
                    parts = [(i0, min(i1, c0)), (max(i0, c1), i1)]
                else:
                    parts = [(i0, i1)]
                res += [(p0, p1) for p0, p1 in parts if p1 - p0 > 1e-9]
            return res
        ia, ib = outside(tree_solid_intervals(tree_ref, a, b)), outside(tree_solid_intervals(tree_new, a, b))
        if len(ia) != len(ib) or any(abs(x[0] - y[0]) * length > 1e-3 or abs(x[1] - y[1]) * length > 1e-3 for x, y in zip(ia, ib)):
            outside_bad.append({'kind': kind, 'a': a, 'b': b})
    return {'rays': len(rays), 'rays_crossing_box': n_inside, 'inside_mismatch': inside_bad, 'outside_mismatch': outside_bad}


def outside_sample_check(tree_ref, tree_new, lo, hi, extent=80.0, step=3.0, seed=11, random_points=20000):
    """Classification of the candidate vs the reference tree at points outside the box: a regular grid over box +- extent (all y of the box range
    +- 20) and seeded random points; the points inside the box are skipped. Returns the number compared and the differences."""
    diffs, n = [], 0
    ylo, yhi = lo[1] - 20, hi[1] + 20

    def inside(p):
        return all(lo[k] <= p[k] <= hi[k] for k in range(3))
    x = lo[0] - extent
    while x <= hi[0] + extent:
        z = lo[2] - extent
        while z <= hi[2] + extent:
            y = ylo
            while y <= yhi:
                p = (x, y, z)
                if not inside(p):
                    n += 1
                    if tree_solid(tree_ref, p) != tree_solid(tree_new, p):
                        diffs.append(p)
                y += step * 2
            z += step
        x += step
    g = Lcg(seed)
    for _ in range(random_points):
        p = (lo[0] - extent + (hi[0] - lo[0] + 2 * extent) * g.next(), ylo + (yhi - ylo) * g.next(), lo[2] - extent + (hi[2] - lo[2] + 2 * extent) * g.next())
        if not inside(p):
            n += 1
            if tree_solid(tree_ref, p) != tree_solid(tree_new, p):
                diffs.append(p)
    return n, diffs


def boundary_ring_check(tree_ref, tree_new, lo, hi, step=0.5, offsets=(1e-3, 0.05, 0.25, 1.0)):
    """Points on shells just outside the box (distance `offset` from each face): the candidate must equal the reference exactly."""
    diffs, n = [], 0
    for off in offsets:
        for k in range(3):
            for side in (lo[k] - off, hi[k] + off):
                o1, o2 = [i for i in range(3) if i != k]
                u = lo[o1] - off
                while u <= hi[o1] + off:
                    v = lo[o2] - off
                    while v <= hi[o2] + off:
                        p = [0, 0, 0]
                        p[k], p[o1], p[o2] = side, u, v
                        n += 1
                        if tree_solid(tree_ref, tuple(p)) != tree_solid(tree_new, tuple(p)):
                            diffs.append(tuple(p))
                        v += step
                    u += step
    return n, diffs


def changed_links(tree, snap_child, snap_sib, n0):
    """Existing nodes whose links changed: [(node, 'child' | 'sib')]."""
    out = []
    for i in range(n0):
        if tree.child[i] != snap_child[i]:
            out.append((i, 'child'))
        if tree.sib[i] != snap_sib[i]:
            out.append((i, 'sib'))
    return out


def reachable_near_box(tree_ref, lo, hi):
    """Plane nodes the box-guided descent of the reference tree visits (a link may only change below these)."""
    verts = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    seen, stack = set(), [0]
    while stack:
        i = stack.pop()
        seen.add(i)
        nx, ny, nz, d = tree_ref.plane[i][:4]
        s = [nx * x + ny * y + nz * z + d for x, y, z in verts]
        nxt = []
        if min(s) >= -tt.EPS:
            nxt.append(tree_ref.sib[i])
        elif max(s) <= tt.EPS:
            nxt.append(tree_ref.child[i])
        else:
            nxt += [tree_ref.sib[i], tree_ref.child[i]]
        stack += [t for t in nxt if tree_ref.plane[t] is not None]
    return seen
