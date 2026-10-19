"""Offline model of the OFF COURSE border on PS2 and PC (W4 behaviour, separate from the XML data port).

Both classifiers are transcribed from the decompiled code, with the full-list search (the games search a window of +-12 (PS2) / +-24 (PC) markers
around the cached index and the full list every 15 ticks; for a car that moves continuously this gives the same nearest marker).

PS2 `gaLimitsAI` update `FUN_001a6098`, nearest `FUN_001a6758` (lists LeftOuterLimit2 / RightOuterLimit2 only):
  i = argmin X/Z distance; if 0 < i < n-1 and the car lies behind the bisector at marker i, i -= 1; clamp to [0, n-3];
  outside if cross(L[i]->L[i+1], car) < 0 (left) or cross(R[i]->R[i+1], car) > 0 (right); LimitState 2 at once, else 1.
PC `gaLimitsAI` update `0x004CD9B0`, nearest `0x004CE140` (four lists):
  i = argmin 3D distance; if 0 < i < n-1 and |P[i+1]-P[i]|^2 < |P[i+1]-car|^2 (3D), i -= 1; clamp to [0, n-3];
  left outside if both segments i->i+1 and i+1->i+2 have the car on the outer side (same for right); inner lists first (inside -> state 0),
  then outer lists (inside -> 1, outside -> counter, state 2 from the 8th consecutive sample).

The car height is taken from the nearest RaceLine marker (the PC step-back test is 3D, so marker Y matters there). Variants: retail PC
lists, PS2 markers only (Y 0), and the default `build_logic.py` lists (PS2 polyline densified to 10 units, Y 0). Agreement = share of
grid points within 320 units of the RaceLine where PC state 2 equals PS2 outside.

    python limit_sim.py --out limit-sim-36.json [--course Turkey3]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402
import build_logic as bl  # noqa: E402
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402


def cross(a, b, p):
    """(z1 - z0)(x1 - px) - (x1 - x0)(z1 - pz), the form both games use (a, b, p are (x, y, z))."""
    return (b[2] - a[2]) * (b[0] - p[0]) - (b[0] - a[0]) * (b[2] - p[2])


def ps2_index(pts, p):
    n = len(pts)
    i = min(range(n), key=lambda k: (p[0] - pts[k][0]) ** 2 + (p[2] - pts[k][2]) ** 2)
    if 0 < i < n - 1:
        def perp(a, b):
            v = (b[2] - a[2], -(b[0] - a[0]))
            L = math.hypot(*v)
            return (0.0, 0.0) if L <= 1.1920929e-07 ** 0.5 else (v[0] / L, v[1] / L)
        u, w = perp(pts[i - 1], pts[i]), perp(pts[i], pts[i + 1])
        e = (u[0] + w[0], u[1] + w[1])
        L = math.hypot(*e)
        e = (0.0, 0.0) if L <= 1.1920929e-07 ** 0.5 else (e[0] / L, e[1] / L)
        x, z = pts[i][0], pts[i][2]
        if e[1] * ((x + e[0]) - p[0]) - e[0] * ((z + e[1]) - p[2]) < 0.0:
            i -= 1
    if i >= n - 2:
        i = n - 3
    return max(i, 0)


def ps2_outside(L, R, p):
    i, j = ps2_index(L, p), ps2_index(R, p)
    return cross(L[i], L[i + 1], p) < 0.0 or cross(R[j], R[j + 1], p) > 0.0


def pc_index(pts, p):
    n = len(pts)
    i = min(range(n), key=lambda k: math.dist(p, pts[k]))
    if 0 < i < n - 1:
        if math.dist(pts[i + 1], pts[i]) ** 2 < math.dist(pts[i + 1], p) ** 2:
            i -= 1
    if i >= n - 2:
        i = n - 3
    return max(i, 0)


def pc_outside_pair(L, R, p):
    i, j = pc_index(L, p), pc_index(R, p)
    left = cross(L[i], L[i + 1], p) < 0.0 and cross(L[i + 1], L[i + 2], p) < 0.0
    right = cross(R[j], R[j + 1], p) > 0.0 and cross(R[j + 1], R[j + 2], p) > 0.0
    return left or right


def pc_state(lists, p):
    if not pc_outside_pair(lists['LeftInnerLimit'], lists['RightInnerLimit'], p):
        return 0
    return 1 if not pc_outside_pair(lists['LeftOuterLimit'], lists['RightOuterLimit'], p) else 2


def positions(doc, name):
    ml = doc.marker_list(name)
    return None if ml is None else [m.position for m in ml.markers]


def simulate(course, step=6.0, reach=320.0):
    ps2 = parse_course_xml_bytes(cc.read_ps2(course.ps2_xml), 'ps2')
    pc = parse_course_xml_bytes(course.pc_xml.read_bytes(), 'pc')
    cand = parse_course_xml_bytes(bl.build(course, cameras=False, splits=False, sounds=False)[0], 'cand')
    plain = parse_course_xml_bytes(bl.build(course, cameras=False, splits=False, sounds=False, limit_step=None)[0], 'plain')
    route = positions(ps2, 'RaceLine')
    L2, R2 = positions(ps2, 'LeftOuterLimit2'), positions(ps2, 'RightOuterLimit2')
    names = ('LeftInnerLimit', 'RightInnerLimit', 'LeftOuterLimit', 'RightOuterLimit')
    retail = {n: positions(pc, n) for n in names}
    dense = {n: positions(cand, n) for n in names}
    ps2_markers = {n: positions(plain, n) for n in names}
    xs, zs = [r[0] for r in route], [r[2] for r in route]
    cells = {}
    for r in route:
        cells.setdefault((int(r[0] // reach), int(r[2] // reach)), []).append(r)
    cnt = {'points': 0, 'ps2_outside': 0}
    variants = (('retail', retail), ('ps2_markers', ps2_markers), ('dense', dense))
    for k, _ in variants:
        cnt[k + '_differs_from_ps2'] = 0
    x = min(xs) - reach
    while x <= max(xs) + reach:
        z = min(zs) - reach
        while z <= max(zs) + reach:
            near = [r for dx in (-1, 0, 1) for dz in (-1, 0, 1) for r in cells.get((int(x // reach) + dx, int(z // reach) + dz), ())]
            if near:
                r = min(near, key=lambda q: (q[0] - x) ** 2 + (q[2] - z) ** 2)
                if (r[0] - x) ** 2 + (r[2] - z) ** 2 <= reach * reach:
                    p = (x, r[1], z)
                    cnt['points'] += 1
                    o = ps2_outside(L2, R2, p)
                    cnt['ps2_outside'] += o
                    for k, lists in variants:
                        if (pc_state(lists, p) == 2) != o:
                            cnt[k + '_differs_from_ps2'] += 1
            z += step
        x += step
    route_ok = {'ps2_route_inside': sum(not ps2_outside(L2, R2, r) for r in route) / len(route),
                'dense_route_state0': sum(pc_state(dense, r) == 0 for r in route) / len(route)}
    out = {k: v for k, v in cnt.items()}
    for k, _ in variants:
        out[k + '_agreement'] = round(1 - cnt[k + '_differs_from_ps2'] / cnt['points'], 4)
    out.update({k: round(v, 4) for k, v in route_ok.items()})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--course')
    ap.add_argument('--out', type=Path)
    ap.add_argument('--step', type=float, default=6.0)
    a = ap.parse_args()
    res = {}
    for c in ([cc.course(a.course)] if a.course else cc.courses()):
        res[c.name] = simulate(c, a.step)
        r = res[c.name]
        print(c.name, {k: v for k, v in r.items() if 'agreement' in k or 'route' in k}, flush=True)
    if a.out:
        a.out.write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
