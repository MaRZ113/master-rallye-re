"""PS2 material -> PC course draw fields, derived from triangles both versions share (W3 groundwork for W2).

For every course: each PC course draw contributes its triangles (positions rounded to 1e-3) with its fields (texture tuple, flag bytes at +0x20,
words +0x14 / +0x18 / +0x24, whether it sits under a tag-5/6 sort container); each PS2 landscape mesh contributes its triangles with the material
name and texture names. Triangles present in both give pairs. The table groups them by the PS2 material directives ($shader, $alphatest, $alphablend,
$clamp, presence of a noise texture, $surfacetype) and counts the PC field combinations seen for each group, plus the vertex alpha bytes of shared
vertices (PS2 colour word byte 0 vs PC colour byte 3).

    python material_map.py --out material-map.json [--courses Turkey3 France1 ...]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'course-port'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
from master_rallye.course_render_writer import Container, CourseRender  # noqa: E402

TOKEN = re.compile(r'\$(shader|alphatest|alphablend|clamp|surfacetype|detail|nodraw|draw|grnd\w*)\(([^)]*)\)?')


def directives(material):
    d = {}
    for name, arg in TOKEN.findall(material):
        if name.startswith('grnd'):
            continue
        if name in ('surfacetype', 'detail'):
            d[name] = 'yes' if name == 'surfacetype' else None
            continue
        d[name] = arg
    return {k: v for k, v in d.items() if v is not None}


def ps2_triangles_with_alpha(scene, mesh):
    """Same strip rule as ps2_obj_to_dx.source_triangles_ext, plus the PS2 vertex byte at +16 (A of the colour word)."""
    out = []
    for strip in mesh['strips']:
        for newest in range(strip['start'] + 2, strip['start'] + strip['count']):
            if scene.control(newest) & 1:
                continue
            idx = (newest - 2, newest - 1, newest)
            pos = tuple(scene.position(i) for i in idx)
            if o.w.area_normal(pos)[0] <= 1e-7:
                continue
            out.append((pos, tuple(scene.payload[32 + i * 52 + 16] for i in idx)))
    return out


def key(points):
    return frozenset(tuple(round(c, 3) for c in p) for p in points)


def pc_triangles(render):
    out = {}
    alpha = {}

    def walk(rec, sorted_):
        if isinstance(rec, Container):
            for c in rec.children:
                walk(c, sorted_ or rec.tag in (5, 6))
            return
        fields = {'textures': rec.texture_tuple, 'flags': rec.flags_0x20.hex(), 'w14': rec.unknown_0x14, 'w18': rec.unknown_0x18,
                  'w24': rec.unknown_0x24, 'f1c': struct.unpack('<f', rec.raw_0x1c)[0], 'sorted': sorted_}
        for k in range(rec.index_start, rec.index_start + rec.index_count, 3):
            vids = [rec.vertex_base + render.indices[k + j] for j in range(3)]
            pts = [render.positions[v] for v in vids]
            out[key(pts)] = (fields, vids)
    for b in render.batches:
        for r in b:
            walk(r, False)
    for r in render.roots:
        walk(r, False)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--courses', nargs='*')
    a = ap.parse_args()
    table = collections.defaultdict(lambda: {'pairs': 0, 'pc_fields': collections.Counter(), 'alpha': collections.Counter(), 'ps2_alpha': collections.Counter(), 'ps2_alpha_all': collections.Counter(), 'examples': set()})
    stats = {}
    for course in cc.courses():
        if a.courses and course.name not in a.courses:
            continue
        render = CourseRender.from_bytes(course.pc_dx.read_bytes(), course.name)
        pc = pc_triangles(render)
        payload = cc.read_ps2(course.ps2_psm)
        scene = o.w.decode_scene(payload)
        shared = ps2_total = 0
        for m in scene.meshes:
            mat = m['material']
            dirs = directives(mat)
            noise = any('noise' in t['name'].lower() for t in m['textures'])
            gkey = json.dumps({**dirs, 'noise_texture': noise}, sort_keys=True)
            for pos, ps2a in ps2_triangles_with_alpha(scene, m):
                ps2_total += 1
                for v in ps2a:
                    table[gkey]['ps2_alpha_all'][v] += 1
                hit = pc.get(key(pos))
                if not hit:
                    continue
                shared += 1
                fields, vids = hit
                row = table[gkey]
                row['pairs'] += 1
                row['pc_fields'][json.dumps({k: fields[k] for k in ('flags', 'w14', 'w18', 'w24', 'sorted')} | {'slots': len(fields['textures']),
                                                                                                                'slot2': fields['textures'][2] if len(fields['textures']) > 2 else None,
                                                                                                                'slot1': fields['textures'][1] if len(fields['textures']) > 1 else None},
                                                sort_keys=True)] += 1
                for v in vids:
                    row['alpha'][render.colors[4 * v + 3]] += 1
                for v in ps2a:
                    row['ps2_alpha'][v] += 1
                if len(row['examples']) < 4:
                    row['examples'].add(mat)
        stats[course.name] = {'ps2_triangles': ps2_total, 'shared_with_pc': shared, 'pc_triangles': len(pc)}
        print(course.name, stats[course.name], flush=True)
    out = {'courses': stats, 'groups': {}}
    for g, row in sorted(table.items(), key=lambda kv: -kv[1]['pairs']):
        out['groups'][g] = {'pairs': row['pairs'], 'pc_fields': dict(row['pc_fields'].most_common(6)),
                            'pc_vertex_alpha': dict(row['alpha'].most_common(4)), 'ps2_vertex_alpha_shared': dict(row['ps2_alpha'].most_common(6)),
                            'ps2_vertex_alpha_all': dict(row['ps2_alpha_all'].most_common(6)), 'examples': sorted(row['examples'])}
    a.out.write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
