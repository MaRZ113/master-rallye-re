"""Facing rules for PS2 triangles, derived from the PC course DX (W2 fix after the first game test).

PS2 draws without back-face culling, so its strip order says nothing about the visible side; PC culls, and its compiler made two-sided materials
by adding a reversed copy of each triangle. For every PS2 directive group this script measures, on the triangles PS2 and PC share (positions):
  * which corner-order rule reproduces the PC order: 'normals' (face normal against the PS2 vertex normals, the PC wire convention) or 'uv'
    (base UV determinant negative in wire order);
  * how many of the PC triangles of that group exist twice with opposite order (two-sided on PC).

    python orientation_map.py --out orientation-map-36.json
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_render as br  # noqa: E402
import course_config as cc  # noqa: E402
import material_map as mm  # noqa: E402
from master_rallye.course_render_writer import CourseRender  # noqa: E402


def uv_det(uv):
    return (uv[1][0] - uv[0][0]) * (uv[2][1] - uv[0][1]) - (uv[1][1] - uv[0][1]) * (uv[2][0] - uv[0][0])


def group_key(mat, textures):
    d = mm.directives(mat)
    d.pop('clamp', None)
    noise = any('noise' in t['name'].lower() for t in textures)
    return json.dumps({**d, 'noise_texture': noise}, sort_keys=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--courses', nargs='*')
    a = ap.parse_args()
    table = collections.defaultdict(collections.Counter)
    for course in cc.courses():
        if a.courses and course.name not in a.courses:
            continue
        r = CourseRender.from_bytes(course.pc_dx.read_bytes(), course.name)
        order = collections.defaultdict(list)
        for d in r.draws():
            for k in range(d.index_start, d.index_start + d.index_count, 3):
                p = [r.positions[d.vertex_base + r.indices[k + j]] for j in range(3)]
                order[mm.key(p)].append(p)
        payload = cc.read_ps2(course.ps2_psm)
        scene = br.o.w.decode_scene(payload)
        for m in scene.meshes:
            g = group_key(m['material'], m['textures'])
            row = table[g]
            for idx in br.ps2_mesh_triangles(scene, m):
                vs = [br.ps2_vertex(payload, i) for i in idx]
                pos = [v[0] for v in vs]
                hits = order.get(mm.key(pos))
                if not hits:
                    continue
                row['shared'] += 1
                fns = [br.cross(br.sub(q[1], q[0]), br.sub(q[2], q[0])) for q in hits]
                if len(hits) >= 2 and any(br.dot(fns[0], f) < 0 for f in fns[1:]):
                    row['pc_two_sided'] += 1
                    continue
                pc_fn = fns[0]
                avg = tuple(sum(v[1][c] for v in vs) for c in range(3))
                fn = br.cross(br.sub(pos[1], pos[0]), br.sub(pos[2], pos[0]))
                normals_order_same = br.dot(fn, avg) < 0          # the normals rule keeps the PS2 order
                uv_order_same = uv_det([v[3] for v in vs]) < 0     # the uv rule keeps the PS2 order
                pc_same = br.dot(fn, pc_fn) > 0
                row['normals_rule_matches_pc'] += normals_order_same == pc_same
                row['uv_rule_matches_pc'] += uv_order_same == pc_same
        print(course.name, flush=True)
    out = {}
    for g, row in sorted(table.items(), key=lambda kv: -kv[1]['shared']):
        single = row['shared'] - row['pc_two_sided']
        out[g] = {'shared': row['shared'], 'pc_two_sided': row['pc_two_sided'],
                  'two_sided_fraction': round(row['pc_two_sided'] / row['shared'], 3) if row['shared'] else None,
                  'single_sided': single,
                  'normals_rule': round(row['normals_rule_matches_pc'] / single, 3) if single else None,
                  'uv_rule': round(row['uv_rule_matches_pc'] / single, 3) if single else None}
    a.out.write_text(json.dumps(out, indent=1))
    for g, v in list(out.items())[:40]:
        print(v, g)


if __name__ == '__main__':
    main()
