"""Offline validation of a full-course PS2 collision build (W1). Geometry and physical properties are checked separately.

Geometry (against the PS2 BSP):
  * solid/empty at seeded random points in the course box;
  * first contact of vertical columns (fixed grid over the PS2 visible ground, window h + 6 .. h - 12), new tree vs PS2 BSP within 0.05, with the
    retail tree for comparison (columns inside the PS2 solid exterior are included: the shell is ported on purpose).
  * first solid along horizontal rays at car height (0.3 to 1.5 above the PS2 contact of each column, seeded direction, 20 units), new tree vs
    PS2 BSP within 0.05 (vertical columns and random points cannot see thin or vertical solids);
  * contact plane of the engine's nearest-plane fallback (`ps2_fallback`, `pc_fallback`) for a point 0.005 to 0.3 below the PS2 contact of each
    column: the plane the engine uses when the 1-unit trace finds no exit plane, which is the usual case for a wheel under flat ground. A steep
    plane chosen on PC where PS2 chooses a non-steep one is a sideways push (an invisible one-sided wall in the game).
Properties (not implied by the geometry):
  * the plane on which each column's contact happens in the new tree: non-negative code (contact allowed), and how its code was chosen;
  * whether that code equals the retail code at the same column when the retail contact is at the same height (same surface id as PC);
  * surface type under each column: PS2 landscape material vs the new tag1400 record vs the retail tag1400 record.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'track-coll1a'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
sys.path.insert(0, str(HERE.parent / 'course-port'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import bsp_query as q  # noqa: E402
import build_collision as bc  # noqa: E402
import course_config as cc  # noqa: E402
import ps2_bsp  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
import region_validate as rv  # noqa: E402
import surface_grid as sg  # noqa: E402
import tag100_tree as tt  # noqa: E402
import tag1400_io as io  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402
from master_rallye.course_tag1400 import parse_course_tag1400_bytes  # noqa: E402

UP, DOWN, TOL = 6.0, 12.0, 0.05
H_RAY = 20.0
ENGINE_EPS = struct.unpack('<f', bytes.fromhex('17b7d138'))[0]   # 1e-4 as float32, PC 0x6e7b54 and PS2 0x4264a0
FLT_MAX = 3.4028234663852886e38


def _side(pl, p):
    s = pl[0] * p[0] + pl[1] * p[1] + pl[2] * p[2] + pl[3]
    return s, (1 if s >= ENGINE_EPS else -1 if s <= -ENGINE_EPS else 0)


def _negative(code):
    return code is None or code >= 0x80000000


def ps2_fallback(bsp, p):
    """Nearest-plane fallback on the PS2 BSP, transcribed from SLES_509.06: plane node 0x237610 (in front: front link only; on or behind: the node
    plane is a candidate when its code is >= 0 and |n.p + d| is below the best; behind: back link), payload leaf 0x2365e0 (every run plane the
    point is on or behind is a candidate while the current best code is >= 0; the check reads the best, not the plane), other leaves add nothing.
    Start: distance FLT_MAX, code -1. Returns (distance, plane or None, code)."""
    best = (FLT_MAX, None, 0xffffffff)
    i = 0
    while True:
        n = bsp.nodes[i]
        if n.plane is not None:
            s, sd = _side(n.plane, p)
            if sd == 1:
                i = n.sibling
                continue
            if not _negative(n.plane[4]) and abs(s) < best[0]:
                best = (abs(s), tuple(n.plane[:4]), n.plane[4])
            if sd == -1:
                i = n.child
                continue
            return best
        if n.payload is not None:
            start, count = n.payload[0] & 0xffffff, n.payload[1] & 0xff
            for pl in bsp.plane_table[start:start + count]:
                s, sd = _side(pl, p)
                if sd != 1 and not _negative(best[2]) and abs(s) < best[0]:
                    best = (abs(s), tuple(pl[:4]), pl[4])
        return best


def pc_fallback(tree, p):
    """The same query on a PC tag100 tree, transcribed from MRallye.exe 0x61fff0 (called from 0x62f5f0 when 0x636770 finds no exit plane); the
    start values are the static ones written at 0x4e67d0 (distance FLT_MAX, code 0xFFFFFFFF)."""
    best = (FLT_MAX, None, 0xffffffff)
    i = 0
    while tree.plane[i] is not None:
        pl = tree.plane[i]
        s, sd = _side(pl, p)
        if sd == 1:
            i = tree.sib[i]
            continue
        if not _negative(tree.code[i]) and abs(s) < best[0]:
            best = (abs(s), tuple(pl[:4]), tree.code[i])
        if sd == -1:
            i = tree.child[i]
            continue
        break
    return best


def same_plane(a, b):
    if a[1] is None or b[1] is None:
        return a[1] is None and b[1] is None
    return max(abs(a[1][k] - b[1][k]) for k in range(3)) < 1e-3 and abs(a[1][3] - b[1][3]) < 2e-3


def steep(plane):
    return plane is not None and abs(plane[1]) < 0.5


class SurfaceLookup:
    """Triangle under (x, z) in a tag1400 block, via its own cell grid (highest triangle at that point)."""

    def __init__(self, u_bytes):
        self.t = parse_course_tag1400_bytes(u_bytes, 'u')
        self.names = [s.raw_bytes for s in self.t.strings]

    def at(self, x, z):
        t = self.t
        i = math.floor(sg.f32(sg.f32(x - t.vector_a[0]) / t.scalar))
        j = math.floor(sg.f32(sg.f32(z - t.vector_a[2]) / t.scalar))
        if not (0 <= i < t.dimension_0 and 0 <= j < t.dimension_1):
            return None, None
        best = None
        for rid in t.cells[i + j * t.dimension_0].entries:
            v = t.records[rid].float_prefix
            h = _bary_height(v, x, z)
            if h is not None and (best is None or h > best[0]):
                best = (h, rid)
        if best is None:
            return None, None
        return best[0], sg.surface_type(self.names[t.records[best[1]].string_ref_index])


def _bary_height(v, x, z):
    ax, ay, az, bx, by, bz, cx, cy, cz = v
    den = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
    if abs(den) < 1e-12:
        return None
    w1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / den
    w2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / den
    w3 = 1 - w1 - w2
    if min(w1, w2, w3) < -1e-6:
        return None
    return w1 * ay + w2 * by + w3 * cy


def ps2_first_solid_t(bsp, a, b):
    """First solid along a->b in the PS2 BSP with the same thin-interval rule as the PC side (region_validate.MIN_SOLID): a solid interval
    shorter than 1e-4 units is a ray touching a cell edge and is skipped on both trees."""
    length = math.dist(a, b)
    for leaf, t0, t1 in q.ps2_segment_leaves(bsp.nodes, a, b):
        if leaf.payload is None:
            if leaf.field_0 == 0xffffffff and (t1 - t0) * length > rv.MIN_SOLID:
                return t0
            continue
        start, count = leaf.payload[0] & 0xffffff, leaf.payload[1] & 0xff
        lo, hi = t0, t1
        for nx, ny, nz, d, _c in bsp.plane_table[start:start + count]:
            s0 = nx * a[0] + ny * a[1] + nz * a[2] + d
            ds = nx * b[0] + ny * b[1] + nz * b[2] + d - s0
            rhs = -q.PS2_EPS - s0
            if abs(ds) < 1e-12:
                if rhs < 0:
                    lo, hi = 1.0, 0.0
                    break
                continue
            t = rhs / ds
            if ds > 0:
                hi = min(hi, t)
            else:
                lo = max(lo, t)
        if hi > lo and (hi - lo) * length > rv.MIN_SOLID:
            return lo
    return None


def contact_plane(tree, x, y, z):
    """Plane node on the descent path just below the contact point whose plane passes through it (|n.p + d| < 1e-3): (node index or None)."""
    p = (x, y - 1e-3, z)
    i, best = 0, None
    while tree.plane[i] is not None:
        nx, ny, nz, d = tree.plane[i][:4]
        if abs(nx * x + ny * y + nz * z + d) < 2e-3:
            best = i
        i = tree.sib[i] if nx * p[0] + ny * p[1] + nz * p[2] + d >= 0 else tree.child[i]
    return best


def first_contact(tree, x, z, top, bottom):
    t = rv.tree_first_solid_t(tree, (x, top, z), (x, bottom, z))
    return None if t is None else top + (bottom - top) * t


def validate(course, dx, step=6.0, points=100000, seed=20261019):
    bsp = ps2_bsp.parse(cc.read_ps2(course.ps2_bsp))
    new = tt.Tree(extract_tag100_from_dx_bytes(dx, 'new').raw)
    retail_raw = extract_tag100_from_dx_bytes(course.pc_dx.read_bytes(), 'retail').raw
    old = tt.Tree(retail_raw)
    _, _, u_new, _ = io.split_suffix(extract_tag100_from_dx_bytes(dx, 'new').raw)
    _, _, u_old, _ = io.split_suffix(retail_raw)
    s_new, s_old = SurfaceLookup(u_new), SurfaceLookup(u_old)
    scene, _ = bc.ps2_scene(course)
    recs = sg.ps2_records(scene, o.source_triangles)
    xs = [r[0][i] for r in recs for i in (0, 3, 6)]
    ys = [r[0][i] for r in recs for i in (1, 4, 7)]
    zs = [r[0][i] for r in recs for i in (2, 5, 8)]
    lo, hi = (min(xs), min(ys) - 20, min(zs)), (max(xs), max(ys) + 40, max(zs))
    # 1. random points
    g = rv.Lcg(seed)
    mism = []
    for _ in range(points):
        p = tuple(lo[k] + (hi[k] - lo[k]) * g.next() for k in range(3))
        if q.ps2_is_solid(bsp, p) != rv.tree_solid(new, p):
            mism.append(p)
    # 2. columns over the PS2 landscape (heights from the PS2-built surface grid = PS2 visible landscape)
    res = collections.Counter()
    errs_new, errs_old = [], []
    hres, herr = collections.Counter(), []
    fres, ferr = collections.Counter(), []
    rnd = random.Random(seed)
    code_kind = collections.Counter()
    surf = collections.Counter()
    surf_pairs = collections.Counter()
    x = lo[0] + step / 2
    while x < hi[0]:
        z = lo[2] + step / 2
        while z < hi[2]:
            h, st_ps2 = s_new.at(x, z)
            if h is None:
                z += step
                continue
            top, bottom = h + UP, h - DOWN
            t = ps2_first_solid_t(bsp, (x, top, z), (x, bottom, z))
            hp = None if t is None else top + (bottom - top) * t
            hn = first_contact(new, x, z, top, bottom)
            ho = first_contact(old, x, z, top, bottom)
            res['columns'] += 1
            if hp is None and hn is None:
                res['new_agree'] += 1
            elif hp is None or hn is None or abs(hp - hn) > TOL:
                res['new_differs'] += 1
                errs_new.append({'x': x, 'z': z, 'ps2': hp, 'new': hn})
            else:
                res['new_agree'] += 1
            if hp is not None and hp < top - 1e-6:
                # horizontal ray at car height from above the PS2 contact
                y = hp + rnd.uniform(0.3, 1.5)
                ang = rnd.uniform(0.0, 2 * math.pi)
                a, b = (x, y, z), (x + H_RAY * math.cos(ang), y, z + H_RAY * math.sin(ang))
                if not q.ps2_is_solid(bsp, a):
                    tp = ps2_first_solid_t(bsp, a, b)
                    tn = rv.tree_first_solid_t(new, a, b)
                    hres['rays'] += 1
                    if (tp is None) != (tn is None) or (tp is not None and abs(tp - tn) * H_RAY > TOL):
                        hres['new_differs'] += 1
                        herr.append({'a': a, 'b': b, 'ps2': tp and tp * H_RAY, 'new': tn and tn * H_RAY})
                    else:
                        hres['new_agree'] += 1
                # nearest-plane fallback for a point just under the PS2 contact
                pt = (x, hp - rnd.uniform(0.005, 0.3), z)
                fp, fn = ps2_fallback(bsp, pt), pc_fallback(new, pt)
                fres['points'] += 1
                if same_plane(fp, fn):
                    fres['same_plane'] += 1
                else:
                    fres['other_plane'] += 1
                    kind = 'steep_on_new_only' if steep(fn[1]) and not steep(fp[1]) else 'none_on_ps2' if fp[1] is None else 'none_on_new' if fn[1] is None else 'other'
                    fres[kind] += 1
                    if len(ferr) < 20:
                        ferr.append({'point': pt, 'kind': kind, 'ps2': [fp[1], fp[2]], 'new': [fn[1], fn[2]]})
            if (hp is None) == (ho is None) and (hp is None or abs(hp - ho) <= TOL):
                res['retail_agree'] += 1
            else:
                res['retail_differs'] += 1
            if hn is not None and hn < top - 1e-6:
                ci = contact_plane(new, x, hn, z)
                if ci is None:
                    code_kind['contact_plane_not_found'] += 1
                else:
                    c = new.code[ci]
                    code_kind['negative' if c >= 0x80000000 else 'valid'] += 1
                    if ho is not None and abs(ho - hn) <= TOL:
                        co = contact_plane(old, x, ho, z)
                        if co is not None:
                            code_kind['same_code_as_retail' if old.code[co] == c else 'other_code_than_retail'] += 1
            ho_s, st_old = s_old.at(x, z)
            surf['compared'] += 1
            surf['ps2_vs_retail_same' if st_ps2 == st_old else 'ps2_vs_retail_differs'] += 1
            if st_ps2 != st_old:
                surf_pairs[f'{st_old}->{st_ps2}'] += 1
            z += step
        x += step
    return {
        'course': course.name, 'box': [lo, hi],
        'random_points': {'points': points, 'mismatch': len(mism), 'first': mism[:5]},
        'columns': dict(res), 'columns_new_differs_first': errs_new[:10],
        'horizontal_rays': dict(hres), 'horizontal_rays_new_differs_first': herr[:10],
        'fallback_planes': dict(fres), 'fallback_planes_differs_first': ferr,
        'contact_codes': dict(code_kind),
        'surface_types': dict(surf), 'surface_type_changes_retail_to_ps2': dict(surf_pairs.most_common(20)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--course', required=True)
    ap.add_argument('--dx', type=Path, required=True)
    ap.add_argument('--step', type=float, default=6.0)
    ap.add_argument('--points', type=int, default=100000)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    rep = validate(cc.course(a.course), a.dx.read_bytes(), a.step, a.points)
    a.out.write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ('random_points', 'columns', 'horizontal_rays', 'fallback_planes', 'contact_codes', 'surface_types', 'surface_type_changes_retail_to_ps2')}, indent=1))


if __name__ == '__main__':
    main()
