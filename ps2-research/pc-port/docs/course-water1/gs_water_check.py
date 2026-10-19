"""COURSE-WATER1 runtime check of the PS2 water contract against PCSX2 GS dumps (decompressed *.gs files).

Reader: ps2-research/course-light1/gsdump.py (GIF replay of register state). Reference: tools/ps2_water_model.py.
For every dump:
  1. the water strips: a GS context 0 run (course map, ALPHA 0x44, Z write) followed by a context 1 run on the same vertices
     (WATERSURFACE2, ALPHA 0x44 or 0x3800000068, ZMSK 1);
  2. puddles: the per-vertex alpha sequence of each run is looked up among the 320938 weights // 2 of every course's
     puddle strips (identifies the course and checks the load-time colour bit for bit);
with --uv on one dump of a course: the phase T and the camera rows are solved from the UVs of the identified puddle strips
and every vertex is compared with 320c78; the water strips are matched by their secondary V and the load phase T0 is
solved and every vertex compared with 321098.

    python gs_water_check.py <dir with *.gs> --out gs-validation.json [--uv Turkey2:<dump name>]
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[1]
RESEARCH = PORT.parent
sys.path[:0] = [str(PORT / 'tools'), str(RESEARCH / 'tools'), str(RESEARCH / 'course-port'), str(RESEARCH / 'course-light1')]
import course_config as cc  # noqa: E402
import detail_runtime as dr  # noqa: E402
import gsdump  # noqa: E402
import ps2_water_model as wm  # noqa: E402
import water_runtime as wr  # noqa: E402


class GS(gsdump.GS):
    def kick(self, x, y, z, f):
        ptype, attr = self.prim_attr()
        c = (attr >> 9) & 1
        key = (ptype, attr & 0x7f8, c, self.r[0x06 + c] & ((1 << 62) - 1), self.r[0x42 + c], self.r[0x47 + c], self.r[0x4e + c])
        rgba = self.r[0x01]
        st = self.r[0x02]
        s = struct.unpack('<f', (st & 0xffffffff).to_bytes(4, 'little'))[0]
        t = struct.unpack('<f', ((st >> 32) & 0xffffffff).to_bytes(4, 'little'))[0]
        self.kicks.append((key, (rgba & 0xff, (rgba >> 8) & 0xff, (rgba >> 16) & 0xff, (rgba >> 24) & 0xff), (x, y, z), s, t, self.q))


def runs(path):
    _, _, _, _, packets = gsdump.read_dump(path)
    gs = GS()
    for p in packets:
        if p[0] == 'xfer':
            gs.gif(p[2])
    out, cur = [], None
    for k in gs.kicks:
        if cur and cur[0] == k[0]:
            cur[1].append(k)
        else:
            cur = [k[0], [k]]
            out.append(cur)
    return out


def tex0(v):
    return dict(TBP=v & 0x3fff, PSM=(v >> 20) & 0x3f, TW=(v >> 26) & 0xf, TH=(v >> 30) & 0xf, TCC=(v >> 34) & 1, TFX=(v >> 35) & 3)


def water_pairs(path):
    """(kind, primary run, secondary run, state summary) of every water/puddle strip."""
    rs = runs(path)
    out = []
    for prev, cur in zip(rs, rs[1:]):
        k = cur[0]
        t = tex0(k[3])
        if not (k[2] == 1 and t['TW'] == 6 and t['TH'] == 6 and t['PSM'] == 0 and (k[4] & 0xff) in (0x44, 0x68)):
            continue
        p = prev[0]
        if p[2] != 0 or (p[4] & 0xff) != 0x44 or len(prev[1]) != len(cur[1]):
            continue
        if any(a[2] != b[2] or a[1] != b[1] for a, b in zip(prev[1], cur[1])):
            continue
        kind = 'puddle' if (k[4] & 0xff) == 0x68 else 'water'
        state = dict(primary=dict(ctx=0, alpha='%x' % p[4], test='%x' % p[5], zbuf='%x' % p[6], tex0=tex0(p[3]), fge=(p[1] >> 5) & 1),
                     secondary=dict(ctx=1, alpha='%x' % k[4], test='%x' % k[5], zbuf='%x' % k[6], tex0=t, fge=(k[1] >> 5) & 1))
        out.append((kind, prev[1], cur[1], state))
    return out


def course_strips(course, mode):
    payload = cc.read_ps2(course.ps2_psm)
    scene = wr.decode_scene(payload)
    out = []
    for m in scene.meshes:
        if m['classification']['water_mode'] == mode:
            for s in m['strips']:
                out.append(list(range(s['start'], s['start'] + s['count'])))
    return payload, out


def puddle_fingerprints():
    table = {}
    for course in cc.courses():
        payload, strips = course_strips(course, 9)
        if not strips:
            continue
        land = dr.decode_landscape(payload)
        seqs = {}
        for idx in strips:
            seq = tuple(wm.puddle_rgba(land, struct.unpack_from('<3f', payload, 32 + 52 * i + 36)) // 2 for i in idx)
            seqs.setdefault(seq, []).append(idx)
        table[course.name] = (payload, seqs)
    return table


def frac(v):
    return (v + 0.5) % 1 - 0.5


def solve_phase(obs, frequency, tmax, step=0.002):
    """T values where the observed wave terms A, B of the first vertices fit the model (double precision scan)."""
    sin, cos = math.sin, math.cos
    (x0, z0, a0, b0), rest = obs[0], obs[1:12]
    found, t = [], 0.0
    while t < tmax:
        a, b = x0 + 1.61368 * t, z0 + t
        if abs(sin(1.13 * a) - cos(1.78 * b) - a0) < 0.02 and abs(cos(2.19 * a) + sin(2.93 * b) - b0) < 0.02:
            if all(abs(sin(1.13 * (x + 1.61368 * t)) - cos(1.78 * (z + t)) - ao) < 0.03 and
                   abs(cos(2.19 * (x + 1.61368 * t)) + sin(2.93 * (z + t)) - bo) < 0.03 for x, z, ao, bo in rest):
                found.append(t)
        t += step
    return found


def refine(t0, error):
    best = None
    for k in range(-3000, 3001):
        t = wm.f32(t0 + k * 1e-6)
        e = error(t)
        if best is None or e < best[0]:
            best = (e, t)
    return best[1]


def check_puddle_uv(payload, groups, tmax):
    P = lambda i: struct.unpack_from('<3f', payload, 32 + 52 * i + 36)  # noqa: E731
    N = lambda i: struct.unpack_from('<3f', payload, 32 + 52 * i)  # noqa: E731
    rows = [(P(i), N(i), p, s) for idx, prim, sec in groups for i, p, s in zip(idx, prim, sec)]
    obs = [(p[0] * .1, p[2] * .1, frac(pr[3] / pr[5] - 0.05 * p[0]) / 0.05, frac(pr[4] / pr[5] - 0.05 * p[2]) / 0.05)
           for p, n, pr, se in rows[:30]]
    cands = solve_phase(obs, 0.1, tmax)
    if not cands:
        return dict(status='NO_PHASE')
    t = refine(cands[len(cands) // 2], lambda tt: sum(abs(frac(pr[3] / pr[5] - wm.puddle_uv(p, n, tt, wm.WATER_BASIS)[0])) +
                                                      abs(frac(pr[4] / pr[5] - wm.puddle_uv(p, n, tt, wm.WATER_BASIS)[1]))
                                                      for p, n, pr, se in rows[:40]))
    primary = max(max(abs(frac(pr[3] / pr[5] - wm.puddle_uv(p, n, t, wm.WATER_BASIS)[0])),
                      abs(frac(pr[4] / pr[5] - wm.puddle_uv(p, n, t, wm.WATER_BASIS)[1]))) for p, n, pr, se in rows)
    # Camera columns from in-strip differences (the packet integer and the constant normal term cancel).
    cols = []
    for comp, sign, coord in ((3, 1, 0), (4, -1, 2)):
        M, r, consts = [], [], []
        for idx, prim, sec in groups:
            base = None
            for i, se in zip(idx, sec):
                p, n = P(i), N(i)
                A, B = wm.waves(p[0], p[2], t, 0.1)
                m = (0.5 * (n[0] + 0.6 * A), 0.5 * (n[2] + 0.6 * B))
                v = sign * (se[comp] / se[5] - 0.5 - 0.02 * p[coord])
                consts.append((m, 0.5 * n[1], v))
                if base is None:
                    base = (m, v)
                    continue
                M.append((m[0] - base[0][0], m[1] - base[0][1]))
                r.append(v - base[1])
        a11 = sum(x[0] * x[0] for x in M); a12 = sum(x[0] * x[1] for x in M); a22 = sum(x[1] * x[1] for x in M)  # noqa: E702
        b1 = sum(x[0] * y for x, y in zip(M, r)); b2 = sum(x[1] * y for x, y in zip(M, r))  # noqa: E702
        det = a11 * a22 - a12 * a12
        cx, cz = (b1 * a22 - b2 * a12) / det, (a11 * b2 - a12 * b1) / det
        mids = [(((v - (m[0] * cx + m[1] * cz)) / ny) + 1) % 2 - 1 for m, ny, v in consts]
        cy = sum(mids) / len(mids)
        resid = max(abs(y - (x[0] * cx + x[1] * cz)) for x, y in zip(M, r))
        cols.append(dict(column=[round(cx, 5), round(cy, 5), round(cz, 5)], norm=round(math.sqrt(cx * cx + cy * cy + cz * cz), 5),
                         spread_of_normal_term=round(max(mids) - min(mids), 5), max_difference_residual=round(resid, 5)))
    dot = sum(a * b for a, b in zip(cols[0]['column'], cols[1]['column']))
    return dict(status='SOLVED', vertices=len(rows), phase=t, counter=round(t * 150, 3), primary_max_residual=primary,
                camera_x_column=cols[0], camera_y_down_column=cols[1], columns_dot=round(dot, 5))


def check_water_uv(course, pairs, tmax):
    payload, strips = course_strips(course, 10)
    P = lambda i: struct.unpack_from('<3f', payload, 32 + 52 * i + 36)  # noqa: E731
    N = lambda i: struct.unpack_from('<3f', payload, 32 + 52 * i)  # noqa: E731
    matched = []
    for kind, prim, sec, _ in pairs:
        if kind != 'water':
            continue
        cands = []
        for idx in strips:
            if len(idx) != len(sec):
                continue
            vals = [frac(e[4] / e[5] - (-0.5 * N(i)[1] + 0.5 + 0.02 * P(i)[2])) for i, e in zip(idx, sec)]
            if max(vals) - min(vals) < 0.01:
                cands.append(idx)
        if len(cands) == 1:
            matched.append((cands[0], prim, sec))
    if not matched:
        return dict(status='NO_WATER_RUNS')
    obs = [(P(i)[0] * .05, P(i)[2] * .05, frac(e[3] / e[5] - 0.01 * P(i)[0]) / 0.05, frac(e[4] / e[5] - 0.01 * P(i)[2]) / 0.05)
           for idx, prim, sec in matched[:40] for i, e in list(zip(idx, prim))[:3]]
    cands = solve_phase(obs, 0.05, tmax)
    if not cands:
        return dict(status='NO_PHASE', runs=len(matched))
    t = refine(cands[len(cands) // 2], lambda tt: sum(abs(frac(e[3] / e[5] - wm.water_uv(P(i), N(i), tt)[0])) +
                                                      abs(frac(e[4] / e[5] - wm.water_uv(P(i), N(i), tt)[1]))
                                                      for idx, prim, sec in matched[:20] for i, e in zip(idx, prim)))
    mp = ms = 0.0
    n = 0
    for idx, prim, sec in matched:
        for i, p, s in zip(idx, prim, sec):
            u0, v0, u1, v1 = wm.water_uv(P(i), N(i), t)
            n += 1
            mp = max(mp, abs(frac(p[3] / p[5] - u0)), abs(frac(p[4] / p[5] - v0)))
            ms = max(ms, abs(frac(s[3] / s[5] - u1)), abs(frac(s[4] / s[5] - v1)))
    return dict(status='SOLVED', runs=len(matched), vertices=n, load_phase=t, load_counter=round(t * 150, 3),
                primary_max_residual=mp, secondary_max_residual=ms)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dumps', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--uv', action='append', default=[], help='Course:dumpname for the UV solve')
    ap.add_argument('--tmax', type=float, default=60000.0)
    args = ap.parse_args()
    table = puddle_fingerprints()
    result = dict(method=__doc__.strip().splitlines()[0], dumps={})
    cache = {}
    for path in sorted(args.dumps.glob('*.gs')):
        pairs = water_pairs(path)
        cache[path.name] = pairs
        states = Counter(json.dumps(st, sort_keys=True) for _, _, _, st in pairs)
        puddles = [tuple(e[1][3] for e in prim) for kind, prim, _, _ in pairs if kind == 'puddle']
        scores = sorted(((sum(1 for r in puddles if r in seqs), name) for name, (_, seqs) in table.items()), reverse=True)
        best = scores[0] if puddles else (0, None)
        result['dumps'][path.name] = dict(water_strips=sum(1 for k, *_ in pairs if k == 'water'), puddle_strips=len(puddles),
                                          course=best[1], puddle_strips_matching_320938=best[0],
                                          states=[dict(json.loads(s), runs=n) for s, n in states.most_common()])
        print(path.name, result['dumps'][path.name]['course'], best[0], '/', len(puddles), flush=True)
    for spec in args.uv:
        name, dump = spec.split(':')
        course = cc.course(name)
        payload, seqs = table[name]
        groups = []
        for kind, prim, sec, _ in cache[dump]:
            if kind != 'puddle':
                continue
            hit = seqs.get(tuple(e[1][3] for e in prim), [])
            if len(hit) == 1:
                groups.append((hit[0], prim, sec))
        result.setdefault('uv', {})[spec] = dict(puddle=check_puddle_uv(payload, groups, args.tmax),
                                                 water=check_water_uv(course, cache[dump], args.tmax))
        print(spec, json.dumps(result['uv'][spec]), flush=True)
    args.out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
