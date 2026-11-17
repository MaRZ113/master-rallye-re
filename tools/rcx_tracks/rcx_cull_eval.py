"""RCX-PERF1: offline estimate of the course draws the renderer submits per frame.

Course Studio courses have no Retail sector visibility, so without culling the game submits every draw record of the
course DX every frame. With the renderer course culling (PS2Port.ini [CourseCull]) a record is drawn only when its
world box is inside the view frustum and (FogCull) not deeper than the linear fog end. This tool replays that test at
chase-camera positions along the course route (the same plane extraction as renderer/course_cull.hpp) and reports
draws and vertices per frame.

    py -3 tools/rcx_tracks/rcx_cull_eval.py --dx A.dx [--dx B.dx ...] --project project.json [--fog 600 --fog 0]

PYTHONPATH must contain master-rallye-re-course/src (DX reader).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path


def records(dx: Path):
    from master_rallye.dx_course import parse_course_dx
    m = parse_course_dx(dx)
    P = m.vertices.positions
    out = []
    for r in m.physical_draws:
        lo, hi = r.vertex_base, r.vertex_base + r.local_vertex_max + 1
        xs = [P[i][0] for i in range(lo, hi)]
        ys = [P[i][1] for i in range(lo, hi)]
        zs = [P[i][2] for i in range(lo, hi)]
        out.append(((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)), hi - lo, r.index_count // 3))
    return out


def planes(eye, forward, vfov_deg, aspect, zfar):
    """Inward-facing normalised planes (n, d) with n.p + d >= 0 inside; plane 4 = near (measures depth)."""
    f = forward
    right = (f[2], 0.0, -f[0])
    rl = math.hypot(right[0], right[2]) or 1.0
    right = (right[0] / rl, 0.0, right[2] / rl)
    up = (f[1] * right[2] - f[2] * right[1], f[2] * right[0] - f[0] * right[2], f[0] * right[1] - f[1] * right[0])
    ty = math.tan(math.radians(vfov_deg) / 2)
    tx = ty * aspect

    def plane(n):
        L = math.sqrt(sum(c * c for c in n))
        n = tuple(c / L for c in n)
        return n, -sum(n[i] * eye[i] for i in range(3))
    side = lambda a, t: tuple(f[i] - t * a[i] for i in range(3))
    out = [plane(tuple(f[i] + tx * right[i] for i in range(3))),     # left
           plane(tuple(f[i] - tx * right[i] for i in range(3))),     # right
           plane(tuple(f[i] + ty * up[i] for i in range(3))),        # bottom
           plane(tuple(f[i] - ty * up[i] for i in range(3))),        # top
           plane(f)]                                                 # near (depth)
    n, d = plane(tuple(-c for c in f))
    out.append((n, d + zfar))                                        # far
    return out


def outside(pl, lo, hi, margin):
    for k, (n, d) in enumerate(pl):
        p = tuple(hi[i] if n[i] >= 0 else lo[i] for i in range(3))
        if sum(n[i] * p[i] for i in range(3)) + d < -margin:
            return True
    return False


def min_depth(pl, lo, hi):
    n, d = pl[4]
    p = tuple(lo[i] if n[i] >= 0 else hi[i] for i in range(3))
    return sum(n[i] * p[i] for i in range(3)) + d


def cameras(route, step=6, back=6.0, height=2.5):
    cams = []
    for i in range(0, len(route) - 2, step):
        a, b = route[i], route[i + 2]
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        f = (dx / L, dy / L * 0.3 - 0.05, dz / L)
        fl = math.sqrt(sum(c * c for c in f))
        f = tuple(c / fl for c in f)
        eye = (a[0] - f[0] * back, a[1] + height, a[2] - f[2] * back)
        cams.append((eye, f))
    return cams


def evaluate(recs, cams, *, vfov, aspect, zfar, fog, margin=2.0, cull=True):
    draws, verts, tris = [], [], []
    for eye, f in cams:
        pl = planes(eye, f, vfov, aspect, zfar)
        nd = nv = nt = 0
        for lo, hi, v, t in recs:
            if cull and (outside(pl, lo, hi, margin) or (fog > 0 and min_depth(pl, lo, hi) > fog + margin)):
                continue
            nd += 1; nv += v; nt += t
        draws.append(nd); verts.append(nv); tris.append(nt)
    q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))]
    return {"draws_mean": round(statistics.mean(draws), 1), "draws_p95": q(draws, .95),
            "vertices_mean_k": round(statistics.mean(verts) / 1000, 1), "vertices_p95_k": round(q(verts, .95) / 1000, 1),
            "triangles_mean_k": round(statistics.mean(tris) / 1000, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dx", type=Path, action="append", required=True)
    ap.add_argument("--project", type=Path, required=True, help="Course Studio project.json (route)")
    ap.add_argument("--fog", type=float, action="append", help="linear fog end, m (0 = no fog cull); repeatable")
    ap.add_argument("--vfov", type=float, default=55.0)
    ap.add_argument("--aspect", type=float, default=16 / 9)
    ap.add_argument("--zfar", type=float, default=5000.0)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    route = json.loads(a.project.read_text())["route"]["points"]
    cams = cameras(route)
    report = {"cameras": len(cams), "vfov": a.vfov, "aspect": round(a.aspect, 3), "zfar": a.zfar, "courses": []}
    for dx in a.dx:
        recs = records(dx)
        row = {"dx": str(dx), "records": len(recs), "vertices_k": round(sum(r[2] for r in recs) / 1000, 1),
               "no_cull": evaluate(recs, cams, vfov=a.vfov, aspect=a.aspect, zfar=a.zfar, fog=0, cull=False)}
        for fog in a.fog or [0.0]:
            row[f"cull_fog{int(fog)}"] = evaluate(recs, cams, vfov=a.vfov, aspect=a.aspect, zfar=a.zfar, fog=fog)
        report["courses"].append(row)
        print(json.dumps(row), flush=True)
    if a.json:
        a.json.write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
