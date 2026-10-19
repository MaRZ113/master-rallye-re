"""COURSE-ALIVE1: private asset and inventory of the 24 PS2 gaEntitySpline objects (17 courses).

Inputs (read only):
- PS2 RaceTest XML of each course (TNG.PAK/TNG.000): Egg, model, the eleven gaEntitySpline properties and the named
  MarkerList, parsed by the AMBIENT1 reference `ps2-research/tools/spline_runtime.py` (`parse_case`, first typed match);
- the PC models of course-port W5 (`course-port/build_objects.py convert()`, the same bytes as
  `DataGx/Misc/PS2Port/<model>/`): vertices, colours, UV, the retail loader winding (b,a,c) and their DXT textures;
- the retail PC course DX of each course (only its SHA-256, so the runtime can refuse a stock PC course).

Output: `.assets/course/PS2SplineObjects.ps2spl` (ignored; contains PS2 route coordinates) and
`.assets/course/spline-inventory-full.json` (ignored, with coordinates). `--inventory <path>` also writes the
coordinate-free inventory that is committed in docs/course-alive1/.

    python ps2-research/pc-port/tools/prepare_spline_objects.py [--inventory docs/course-alive1/inventory.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
sys.path[:0] = [str(RESEARCH / 'course-port'), str(RESEARCH / 'tools'), str(RESEARCH / 'track-delta1'), str(RESEARCH.parent / 'src')]
import build_objects  # noqa: E402
import course_config as cc  # noqa: E402
import spline_runtime as sr  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402

MAGIC = b'PS2SPL01'
VERSION = 1
ASSET = PORT / '.assets' / 'course' / 'PS2SplineObjects.ps2spl'
FULL_INVENTORY = PORT / '.assets' / 'course' / 'spline-inventory-full.json'
HEADER = struct.Struct('<8s6I')            # magic, version, textures, models, vertices, courses, objects
TEXTURE = struct.Struct('<2I')             # width, height, then w*h BGRA (stored DXT rows, as the PC game uploads them)
MODEL = struct.Struct('<16sI6If')          # name, draws, (texture, first, count) x2, bounding radius
VERTEX = struct.Struct('<3fI2f')           # ps2port::ObjectVertex: x y z, D3DCOLOR, u v
COURSE = struct.Struct('<48s64s32s2I')     # course id, PC course DX path, retail PC DX SHA-256, first object, count
OBJECT = struct.Struct('<32s3I4B4f2i')     # egg, model, first point, points, const/loop/trigger/rest, speed on off banking, rest ticks, samples
POINT = struct.Struct('<3f')
MAX_POINTS_PER_OBJECT = 64


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fixed(text, size):
    raw = text.encode('ascii')
    if len(raw) >= size:
        raise ValueError(f'name too long for {size} bytes: {text}')
    return raw + b'\0' * (size - len(raw))


def spline_eggs(payload):
    """(Egg name, occurrence) of every gaEntitySpline AI, in source order (the same scan as spline_runtime.parse_case)."""
    tree = ET.fromstring(payload)
    out, seen = [], {}
    for egg in tree.findall('./EggLists_Version4/List/Egg'):
        for ai in egg.findall('AI_List/AI'):
            if sr.value(sr.properties(ai), 'AI Name', 'String') == 'gaEntitySpline':
                name = egg.get('Name')
                out.append((name, seen.get(name, 0)))
                seen[name] = seen.get(name, 0) + 1
    return out


def model_geometry(model):
    """The W5 PC model of a PS2 model name as triangle-list vertices per draw (the order the retail loader submits)."""
    spec = build_objects.MODELS[model]
    files, rep = build_objects.convert(model, spec)
    dx_name = spec['name'] + '.dx'
    m = parse_dx_bytes(files[dx_name])
    uv = m.uv_sets[0].values
    pos, col = m.vertices.positions, m.vertices.colors
    draws = []
    for d, tex in zip(m.physical_draws, rep['textures']):
        idx = m.draw_global_indices(d)  # (b, a, c) per triangle: retail PC loader winding
        verts = [(*pos[i], struct.unpack_from('<I', col, 4 * i)[0], uv[i][0], uv[i][1]) for i in idx]
        t = parse_dxt_bytes(files[tex['file']])
        draws.append({'texture_file': tex['file'], 'texture': (t.width, t.height, bytes(t.bgra)), 'vertices': verts})
    radius = max(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) for p in pos)
    sources = {name: sha(blob) for name, blob in sorted(files.items())}
    return {'name': spec['name'], 'ps2_model': model, 'draws': draws, 'radius': radius, 'sources': sources,
            'ps2_triangles': rep['ps2_triangles'], 'dx_triangles': rep['dx_triangles_per_draw'],
            'two_sided_copies': rep['two_sided_copies'], 'textures': rep['textures']}


def collect():
    models, courses = {}, []
    for c in cc.courses():
        payload = cc.read_ps2(c.ps2_xml)
        eggs = spline_eggs(payload)
        if not eggs:
            continue
        objects = []
        for egg, occurrence in eggs:
            identity, points, config = sr.parse_case(payload, c.ps2_xml, egg, occurrence)
            model = (identity['model'] or '').lower()
            if model not in build_objects.MODELS:
                raise ValueError(f'{c.name}/{egg}: model {model} has no W5 PC conversion')
            if model not in models:
                models[model] = model_geometry(model)
            path = sr.PathState(points, config)  # the AMBIENT1 contract checks (finite, >=4 points, no duplicates)
            ctrl = sr.Controller(path, 0)
            if not 4 <= len(points) <= MAX_POINTS_PER_OBJECT:
                raise ValueError(f'{c.name}/{egg}: unsupported route size {len(points)}')
            chords = [math.dist(a, b) for a, b in zip(points, points[1:])]
            objects.append({
                'egg': egg, 'occurrence': occurrence, 'model': model, 'pc_model': models[model]['name'],
                'marker_list': identity['marker_list'], 'route_sha256': identity['route_sha256'],
                'points': [list(p) for p in points], 'config': config,
                'knots': path.knots, 'closing_time': path.closing_time, 'duration': path.duration,
                'open_route_length': sum(chords), 'closing_chord': math.dist(points[-1], points[0]),
                'start': list(ctrl.position), 'start_forward': list(ctrl.direction),
                'authored_matrix_identity': _identity_matrix(identity['egg_properties']),
                'egg_flags': {n: _egg_flag(identity['egg_properties'], n) for n in
                              ('Freezable', 'Hitable', 'en3d Interpolated', 'en3d Visible', 'en3d ZBuffered')},
            })
        pc_dx = c.pc_dx.read_bytes()
        courses.append({'name': c.name, 'id': 'RaceTest/' + c.name, 'ps2_xml': c.ps2_xml, 'ps2_xml_sha256': sha(payload),
                        'pc_dx_path': c.pc_dx.relative_to(cc.PC_ROOT).as_posix(), 'retail_pc_dx_sha256': sha(pc_dx),
                        'objects': objects})
    return models, courses


def _identity_matrix(rows):
    """True when the authored en3d Matrix has an identity basis. The spline owner overwrites the whole matrix
    (AMBIENT1 transform-pipeline.md), so neither basis nor translation is composed with the route."""
    for r in rows:
        if r.get('Name') == 'en3d Matrix' and r.get('Type') == 'Matrix':
            basis = [[float(x) for x in r.get(f'Row{i}', '').split()][:3] for i in range(3)]
            return basis == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    return None


def _egg_flag(rows, name):
    return sr.value(rows, name, 'Bool')


def build_asset(models, courses):
    textures, tex_index = [], {}
    model_order = sorted(models)
    vertex_blob, model_blob = bytearray(), bytearray()
    total = 0
    for name in model_order:
        m = models[name]
        draws = []
        for d in m['draws']:
            key = sha(d['texture'][2])
            if key not in tex_index:
                tex_index[key] = len(textures)
                textures.append(d['texture'])
            for v in d['vertices']:
                vertex_blob += VERTEX.pack(*v)
            draws.append((tex_index[key], total, len(d['vertices'])))
            total += len(d['vertices'])
        if not 1 <= len(draws) <= 2:
            raise ValueError(name)
        flat = [x for dr in draws for x in dr] + [0, 0, 0] * (2 - len(draws))
        model_blob += MODEL.pack(fixed(m['name'], 16), len(draws), *flat, m['radius'])
    out = bytearray(HEADER.pack(MAGIC, VERSION, len(textures), len(models), total, len(courses),
                                sum(len(c['objects']) for c in courses)))
    for w, h, bgra in textures:
        if len(bgra) != w * h * 4:
            raise ValueError('texture size')
        out += TEXTURE.pack(w, h) + bgra
    out += model_blob + vertex_blob
    first = 0
    for c in courses:
        out += COURSE.pack(fixed(c['id'], 48), fixed(c['pc_dx_path'], 64), bytes.fromhex(c['retail_pc_dx_sha256']), first, len(c['objects']))
        first += len(c['objects'])
    point_first = 0
    for c in courses:
        for o in c['objects']:
            k = o['config']
            out += OBJECT.pack(fixed(o['egg'], 32), model_order.index(o['model']), point_first, len(o['points']),
                               k.const_speed, k.loop, k.trigger, k.rest, k.speed, k.on, k.off, k.banking, k.rest_ticks, k.samples)
            point_first += len(o['points'])
    for c in courses:
        for o in c['objects']:
            for p in o['points']:
                out += POINT.pack(*p)
    return bytes(out), model_order


def inventory(models, courses, asset_sha, coordinates):
    def cfg(k):
        return {'use_const_speed': k.const_speed, 'use_closed_loop': k.loop, 'use_trigger_system': k.trigger,
                'max_speed_const_speed': k.speed, 'trigger_dist_on': k.on, 'trigger_dist_off': k.off,
                'use_rest_on_nonloop': k.rest, 'rest_ticks': k.rest_ticks, 'banking': k.banking, 'number_of_samples': k.samples}
    rows = []
    for c in courses:
        objs = []
        for o in c['objects']:
            k = o['config']
            ticks = o['duration'] * 30.0
            row = {'egg': o['egg'], 'occurrence': o['occurrence'], 'ps2_model': o['model'], 'pc_model': o['pc_model'],
                   'marker_list': o['marker_list'], 'route_sha256': o['route_sha256'], 'route_points': len(o['points']),
                   'config': cfg(k), 'open_route_length': round(o['open_route_length'], 3),
                   'closing_chord': round(o['closing_chord'], 3), 'closing_time': o['closing_time'], 'duration_nominal_s': o['duration'],
                   'cycle_ticks': math.floor(ticks) + 1, 'cycle_seconds_at_50hz': round((math.floor(ticks) + 1) / 50.0, 2),
                   'route_y_constant': len({p[1] for p in o['points']}) == 1,
                   'behaviour': _behaviour(o, k), 'authored_matrix_identity_basis': o['authored_matrix_identity'],
                   'egg_flags': o['egg_flags']}
            if coordinates:
                row.update({'points': o['points'], 'knots': o['knots'], 'start': o['start'], 'start_forward': o['start_forward']})
            objs.append(row)
        rows.append({'course': c['name'], 'course_id': c['id'], 'ps2_xml': c['ps2_xml'], 'ps2_xml_sha256': c['ps2_xml_sha256'],
                     'pc_dx_path': c['pc_dx_path'], 'retail_pc_dx_sha256': c['retail_pc_dx_sha256'], 'objects': objs})
    mods = {}
    for name, m in sorted(models.items()):
        mods[m['name']] = {'ps2_model': name, 'ps2_triangles': m['ps2_triangles'], 'dx_triangles_per_draw': m['dx_triangles'],
                           'two_sided_copies': m['two_sided_copies'], 'bounding_radius': round(m['radius'], 3),
                           'textures': [{'file': t['file'], 'ps2_texture': t['ps2_texture'], 'pc_source': t['pc_source']} for t in m['textures']],
                           'source_sha256': m['sources']}
    return {'schema_version': 1, 'phase': 'COURSE-ALIVE1', 'asset': 'PS2SplineObjects.ps2spl', 'asset_sha256': asset_sha,
            'tick_contract': {'nominal_increment_s': '1/30 (float32 0x3d088889) per controller invocation',
                              'invocations_per_second': 50, 'evidence': 'EE main loop 3ed9e0 -> 2a13e0 -> 2a2300 -> 21f088 once per rendered frame; PS2 PAL frame 50 Hz (diag-reflection2 GS dumps)'},
            'courses': len(rows), 'objects': sum(len(r['objects']) for r in rows), 'models': mods, 'by_course': rows}


def _behaviour(o, k):
    parts = ['closed loop' if k.loop else 'open route']
    parts.append('chord/speed knot times' if k.const_speed else 'equal knot times')
    if k.trigger:
        parts.append(f'trigger on<{k.on:g} off>{k.off:g} (Car0 XZ)')
    if not k.loop and k.const_speed:
        parts.append(f'endpoint hold {o["closing_time"]:.2f} nominal s')
    if not k.loop and not k.rest:
        parts.append('stays at the last marker')
    if not k.loop and k.rest:
        parts.append(f'rest {k.rest_ticks} ticks then restart')
    if k.loop and k.rest:
        parts.append('authored rest ignored (closed branch)')
    if k.banking:
        parts.append(f'banking {k.banking:g} over {k.samples} samples')
    return ', '.join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--inventory', type=Path, help='also write the coordinate-free inventory here')
    ap.add_argument('--output', type=Path, default=ASSET)
    a = ap.parse_args()
    models, courses = collect()
    blob, _ = build_asset(models, courses)
    out = a.output
    if out.is_symlink() or out.parent.is_symlink():
        raise ValueError('private output link rejected')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    digest = sha(blob)
    FULL_INVENTORY.write_text(json.dumps(inventory(models, courses, digest, True), indent=1), encoding='utf-8')
    if a.inventory:
        a.inventory.parent.mkdir(parents=True, exist_ok=True)
        a.inventory.write_text(json.dumps(inventory(models, courses, digest, False), indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'asset': str(out), 'bytes': len(blob), 'sha256': digest, 'courses': len(courses),
                      'objects': sum(len(c['objects']) for c in courses), 'models': sorted(m['name'] for m in models.values())}))


if __name__ == '__main__':
    main()
