"""Where does object collision live, per course (W1 check that a full BSP replacement loses nothing silently).

1. Egg models referenced by the RaceTest XML (PS2 and PC, from cdelta1/course-pairs.json): does the model file carry its own collision section
   (tag101 convex hull / tag102 cylinder)? Such collision belongs to the Egg, not to the course tree, and is unaffected by replacing tag100. It is lost only
   if the Egg itself is dropped or replaced (W4 decides the Egg list).
2. Static meshes inside the PS2 landscape PSM that are not ground (shader other than ground, or no $surfacetype): sample points 0.05 behind each
   triangle (against its normal) and ask whether they are solid in the PS2 BSP and in the retail PC tree. A mesh solid in the retail tree but not in
   the PS2 BSP is a collision the PS2 version does not have; the reverse is a PS2 collision the converted tree now brings.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'course-port'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
sys.path.insert(0, str(HERE.parent / 'track-coll1a'))
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import bsp_query as q  # noqa: E402
import course_config as cc  # noqa: E402
import ps2_bsp  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
import region_validate as rv  # noqa: E402
import tag100_tree as tt  # noqa: E402
from master_rallye.collision import parse_collision_sections  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402

PAIRS = json.loads((HERE.parent / 'cdelta1/course-pairs.json').read_text())


def ps2_model_collision(model):
    path = '\\TNG\\DATAPSM\\' + model.upper() + '.PSM'
    if path not in cc.manifest():
        return 'missing'
    payload = cc.read_ps2(path)
    try:
        scene = o.w.decode_scene(payload, terminator=101)
        col = parse_collision_sections(payload[scene.end:], base_offset=scene.end, source=path, strict=False)
        tags = list(col.tag_ids)
    except Exception as e:  # noqa: BLE001 - report, do not guess
        return f'unparsed: {type(e).__name__}'
    return 'tags ' + ','.join(map(str, tags)) if tags else 'none'


def pc_model_collision(model):
    try:
        p = cc._ci(cc.PC_ROOT, 'DataGx/' + model.replace('\\', '/') + '.dx')
    except FileNotFoundError:
        return 'missing'
    try:
        m = parse_dx_bytes(p.read_bytes(), p.name)
        tags = list(m.collision.tag_ids)
    except Exception as e:  # noqa: BLE001
        return f'unparsed: {type(e).__name__}'
    return 'tags ' + ','.join(map(str, tags)) if tags else 'none'


def normal(t):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
    u, w = (bx - ax, by - ay, bz - az), (cx - ax, cy - ay, cz - az)
    n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
    ln = (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** .5
    return None if ln == 0 else (n[0] / ln, n[1] / ln, n[2] / ln)


def static_meshes(course, bsp, pc):
    scene = o.w.decode_scene(cc.read_ps2(course.ps2_psm))
    rows = collections.defaultdict(lambda: collections.Counter())
    for m in scene.meshes:
        mat = m['material']
        if '$shader(ground)' in mat.lower() or '$surfacetype' in mat:
            continue
        c = rows[mat]
        for pos, _, _ in o.source_triangles(scene, m):
            n = normal(pos)
            if n is None:
                continue
            cen = tuple(sum(p[k] for p in pos) / 3 for k in range(3))
            for s in (1, -1):    # both sides: the winding of PS2 object meshes is not reliable
                p = tuple(cen[k] - s * 0.05 * n[k] for k in range(3))
                c['samples'] += 1
                c['ps2_solid'] += q.ps2_is_solid(bsp, p)
                c['pc_solid'] += rv.tree_solid(pc, p)
            c['triangles'] += 1
    out = []
    for mat, c in rows.items():
        ps2f, pcf = c['ps2_solid'] / c['samples'], c['pc_solid'] / c['samples']
        # a solid object has about half of its two-sided samples inside; thin or open meshes less
        kind = ('both' if ps2f >= .25 and pcf >= .25 else 'ps2_only' if ps2f >= .25 else 'pc_only' if pcf >= .25 else 'neither')
        out.append({'material': mat, 'triangles': c['triangles'], 'ps2_solid_fraction': round(ps2f, 3), 'pc_solid_fraction': round(pcf, 3), 'collision': kind})
    return sorted(out, key=lambda r: -r['triangles'])


def main(out_path, only=None):
    result = {}
    for course in cc.courses():
        if only and course.name.lower() != only.lower():
            continue
        pair = next(p for p in PAIRS if Path(p['pc']).stem == course.name)
        land = {course.ps2_landscape.lower(), course.pc_landscape.lower()}
        eggs = []
        for side, fn in (('ps2', ps2_model_collision), ('pc', pc_model_collision)):
            for model, n in pair['model_counts'][side].items():
                if model.lower() in land:
                    continue
                eggs.append({'side': side, 'model': model, 'instances': n, 'collision': fn(model)})
        bsp = ps2_bsp.parse(cc.read_ps2(course.ps2_bsp))
        pc = tt.Tree(extract_tag100_from_dx_bytes(course.pc_dx.read_bytes(), 'pc').raw)
        st = static_meshes(course, bsp, pc)
        result[course.name] = {'egg_models': eggs, 'static_landscape_objects': st,
                               'summary': dict(collections.Counter(r['collision'] for r in st))}
        print(course.name, result[course.name]['summary'], [e for e in eggs if e['collision'] not in ('none', 'missing')])
    Path(out_path).write_text(json.dumps(result, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
