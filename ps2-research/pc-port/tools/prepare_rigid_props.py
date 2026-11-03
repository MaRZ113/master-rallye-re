"""COURSE-ALIVE3: private asset and inventory of the 83 PS2 gaAiRigidBody props (58 hay bales, 25 tumbleweeds, 9 courses).

Inputs (read only):
- PS2 RaceTest XML of each course (TNG.PAK/TNG.000): every gaAiRigidBody Egg with its en3d Matrix, model and the four
  typed properties (Mass, MOI, Trigger Distance, Casts Shadow), parsed by the RIGID1 reference
  `ps2-research/tools/rigid_runtime.py` (`parse_authored`: first correctly typed property, original defaults);
- the prop PSM of each family: tag101 convex hull, representation B geometry_a (hay 16 vertices / 28 triangles,
  tumbleweed 26 / 48; rigid1/collision-shapes.md), read with the strict SDK collision reader (`inspect`-equivalent);
- the PC visual models of course-port W5 (`course-port/build_objects.py convert()`): hay = the W5 hay bale, tumbleweed =
  the same conversion with its own PS2 texture `shrubtrig2-tga` (PC file of the same name), retail loader winding,
  two-sided copies;
- the retail PC course DX of each course (only its SHA-256, so the runtime can refuse a stock PC course).

Output: `.assets/course/PS2RigidProps.ps2rgd` (ignored; contains PS2 coordinates) and
`.assets/course/rigid-inventory-full.json` (ignored). `--inventory <path>` writes the coordinate-free inventory that is
committed in docs/course-alive3/.

    python ps2-research/pc-port/tools/prepare_rigid_props.py [--inventory docs/course-alive3/inventory.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
sys.path[:0] = [str(RESEARCH / 'course-port'), str(RESEARCH / 'tools'), str(RESEARCH / 'track-delta1'), str(RESEARCH.parent / 'src')]
sys.dont_write_bytecode = True
import build_objects  # noqa: E402
import course_config as cc  # noqa: E402
import rigid_runtime as rr  # noqa: E402
import water_runtime as wr  # noqa: E402
from master_rallye.collision import parse_collision_sections  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402

MAGIC = b'PS2RGD02'
VERSION = 2
ASSET = PORT / '.assets' / 'course' / 'PS2RigidProps.ps2rgd'
FULL_INVENTORY = PORT / '.assets' / 'course' / 'rigid-inventory-full.json'
HEADER = struct.Struct('<8s9I')            # magic, version, textures, models, vertices, hull points, hull planes, courses, props,
                                           # shadow texture (Misc\Shadow\shadow, 332628)
TEXTURE = struct.Struct('<2I')             # width, height, then w*h BGRA (stored DXT rows, as the PC game uploads them)
MODEL = struct.Struct('<16s2I6If4Ifi6f')   # name, material, draws, (texture, first, count) x2, visual radius,
                                           # hull first point, points, first plane, planes, hull radius,
                                           # env texture (-1 none), model AABB min xyz, max xyz (332628 shadow box)
VERTEX = struct.Struct('<3fI2f')           # ps2port::ObjectVertex: x y z, D3DCOLOR, u v
NORMAL = struct.Struct('<3f')              # per vertex, model space (PS2 normals; reversed copies negated)
POINT = struct.Struct('<3f')
PLANE = struct.Struct('<4f')               # outward unit normal n, d: n.p + d <= 0 inside
COURSE = struct.Struct('<48s64s32s2I')     # course id, PC course DX path, retail PC DX SHA-256, first prop, count
PROP = struct.Struct('<32s2I5f12f')        # egg, model, flags (bit0 Casts Shadow), mass, MOI xyz, Trigger Distance, matrix rows 0..3 xyz

MATERIAL_OBJECT, MATERIAL_TREEBLEND = 0, 1
# PS2 model (lower case, backslashes) -> family. The two hay paths are byte-identical (rigid1/collision-shapes.md).
FAMILIES = {
    r'misc\haybale\haybale': 'haybale',
    r'misc\objects\haybales\haybale': 'haybale',
    r'misc\objects\tumbleweed\tumblweed': 'tumblweed',
}
MODEL_SPECS = {
    # $shader(dull) (setup 3aeb50): mode 3, auxiliary 328000 whose vertex callback 322400 overwrites every vertex colour
    # with (0x72, 0x72, 0x72, 0xFE) (cached x0.5 -> 57/128 on the GS), secondary CommonTextures/dull added through the
    # mode-3 normal-coordinate environment pass (REFL1 environment-coordinate-math.md).
    'haybale': {'psm': rr.HAY[0], 'w5': r'misc\haybale\haybale', 'spec': build_objects.MODELS[r'misc\haybale\haybale'],
                'material': MATERIAL_OBJECT, 'vertex_color': 0xFE727272, 'env': r'\TNG\DATAPSM\COMMONTEXTURES\DULL.GXI'},
    # W5 left the tumbleweed out only for want of a loose-model alpha template; the runtime draws it with its own
    # treeblend state, so the same conversion is used with the hay template slot (texture name aliased).
    'tumblweed': {'psm': rr.TUMBLE, 'w5': r'misc\objects\tumbleweed\tumblweed', 'spec': {'name': 'tumblweed', 'draws': ['shrubtrig2-tga']},
                  'material': MATERIAL_TREEBLEND},
}
SHADOW_GXI = r'\TNG\DATAPSM\MISC\SHADOW\SHADOW.GXI'   # 'Misc\Shadow\shadow' (0x485948), black RGB, alpha blob


def gxi(path):
    """Uncompressed 32-bit GXI (magic 0x13039, u16 width/height, RGBA bytes) -> (w, h, BGRA bytes)."""
    payload = cc.read_ps2(path)
    magic, w, h = struct.unpack_from('<IHH', payload, 0)
    if magic != 0x13039 or len(payload) != 8 + 4 * w * h or w & (w - 1) or h & (h - 1):
        raise ValueError(f'{path}: unsupported GXI')
    px = payload[8:]
    out = bytearray(len(px))
    out[0::4], out[1::4], out[2::4], out[3::4] = px[2::4], px[1::4], px[0::4], px[3::4]
    return (w, h, bytes(out)), sha(payload)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fixed(text, size):
    raw = text.encode('ascii')
    if len(raw) >= size:
        raise ValueError(f'name too long for {size} bytes: {text}')
    return raw + b'\0' * (size - len(raw))


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def hull_planes(points, triangles, tolerance=1e-4):
    """Outward face planes of the convex representation: one plane per triangle (oriented away from the centroid),
    coplanar duplicates merged. Every point must lie on or inside every plane (convexity check)."""
    c = [sum(p[k] for p in points) / len(points) for k in range(3)]
    planes = []
    for a, b, d in triangles:
        pa, pb, pd = points[a], points[b], points[d]
        u = [pb[k] - pa[k] for k in range(3)]
        v = [pd[k] - pa[k] for k in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        length = math.sqrt(sum(x * x for x in n))
        if length < 1e-9:
            continue
        n = [x / length for x in n]
        dist = -sum(n[k] * pa[k] for k in range(3))
        if sum(n[k] * c[k] for k in range(3)) + dist > 0:
            n, dist = [-x for x in n], -dist
        if any(abs(n[0] - q[0]) < 1e-4 and abs(n[1] - q[1]) < 1e-4 and abs(n[2] - q[2]) < 1e-4 and abs(dist - q[3]) < 1e-4 for q in planes):
            continue
        planes.append((n[0], n[1], n[2], dist))
    for n0, n1, n2, dist in planes:
        for p in points:
            if n0 * p[0] + n1 * p[1] + n2 * p[2] + dist > tolerance:
                raise ValueError('convex representation is not convex at tolerance')
    return planes


def hull(psm_path):
    payload = cc.read_ps2(psm_path)
    scene = wr.decode_scene(payload, terminator=101)
    col = parse_collision_sections(payload[scene.end:], base_offset=scene.end, source=psm_path, strict=True)
    if col.convex_hull is None or col.errors or col.tag_ids != (101,) or payload[col.end_offset:] != b'\xff\xff\xff\xff':
        raise ValueError(f'{psm_path}: one proved tag101 convex hull required')
    h = col.convex_hull
    rep = h.representation_b.geometry_a
    points = [tuple(f32(x) for x in p) for p in rep.vertices]
    planes = hull_planes(points, rep.triangles)
    centre = h.base_geometry.vertices[0]
    if max(abs(x) for x in centre) > 1e-3:
        raise ValueError(f'{psm_path}: base centre is not the model origin; the body centre of mass would need it')
    radius = max(math.sqrt(sum(x * x for x in p)) for p in points)
    return {'psm': psm_path, 'psm_sha256': sha(payload), 'tag101_sha256': h.sha256, 'points': points, 'planes': planes,
            'radius': radius, 'base_scalar': h.base_scalar, 'triangles': len(rep.triangles),
            'representation_a_vertices': h.representation_a.geometry_a.vertex_count}


def visual(family):
    s = MODEL_SPECS[family]
    files, rep = build_objects.convert(s['w5'], s['spec'])
    m = parse_dx_bytes(files[s['spec']['name'] + '.dx'])
    uv = m.uv_sets[0].values
    pos, col = m.vertices.positions, m.vertices.colors
    draws = []
    for d, tex in zip(m.physical_draws, rep['textures']):
        idx = m.draw_global_indices(d)
        color = s.get('vertex_color')
        verts = [(*pos[i], color if color is not None else struct.unpack_from('<I', col, 4 * i)[0], uv[i][0], uv[i][1]) for i in idx]
        normals = [tuple(m.vertices.normals[i]) for i in idx]
        t = parse_dxt_bytes(files[tex['file']])
        draws.append({'texture_file': tex['file'], 'texture': (t.width, t.height, bytes(t.bgra)), 'vertices': verts, 'normals': normals})
    aabb = [min(p[k] for p in pos) for k in range(3)] + [max(p[k] for p in pos) for k in range(3)]
    env = gxi(s['env']) if s.get('env') else None
    radius = max(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) for p in pos)
    return {'draws': draws, 'radius': radius, 'aabb': aabb, 'env': env[0] if env else None, 'env_source': (s.get('env'), env[1]) if env else None,
            'vertex_color': s.get('vertex_color'), 'ps2_triangles': rep['ps2_triangles'], 'dx_triangles': rep['dx_triangles_per_draw'],
            'two_sided_copies': rep['two_sided_copies'], 'textures': rep['textures'],
            'sources': {name: sha(blob) for name, blob in sorted(files.items())}}


def collect():
    models = {}
    for family, s in MODEL_SPECS.items():
        models[family] = {'name': family, 'material': s['material'], **visual(family), 'hull': hull(s['psm'])}
    courses = []
    for c in cc.courses():
        payload = cc.read_ps2(c.ps2_xml)
        case = rr.parse_authored(payload, c.ps2_xml)
        if not case['records']:
            continue
        props = []
        for r in case['records']:
            model = r['model'].replace('/', '\\').lower()
            if model not in FAMILIES:
                raise ValueError(f'{c.name}/{r["egg"]}: unknown prop model {model}')
            m = r['matrix']
            for row in m[:3]:
                if abs(math.sqrt(sum(x * x for x in row[:3])) - 1) > 2e-2:  # XML stores 2 decimals (Italy2 0.69/0.73)
                    raise ValueError(f'{c.name}/{r["egg"]}: authored basis is not a rotation')
            if [round(x, 6) for x in (m[0][3], m[1][3], m[2][3], m[3][3])] != [0, 0, 0, 1]:
                raise ValueError(f'{c.name}/{r["egg"]}: authored matrix is not affine')
            res = r['resolved']
            if not (res['mass'] > 0 and all(x > 0 for x in res['moi'])):
                raise ValueError(f'{c.name}/{r["egg"]}: mass and MOI must be positive')
            props.append({'egg': r['egg'], 'source_id': r['source_id'], 'family': FAMILIES[model], 'model': r['model'],
                          'mass': res['mass'], 'moi': list(res['moi']), 'trigger_distance': res['trigger_distance'],
                          'casts_shadow': res['casts_shadow'], 'matrix': [list(row[:3]) for row in m], 'matrix_sha256': r['matrix_sha256']})
        pc_dx = c.pc_dx.read_bytes()
        courses.append({'name': c.name, 'id': 'RaceTest/' + c.name, 'ps2_xml': c.ps2_xml, 'ps2_xml_sha256': case['decoded_sha256'],
                        'pc_dx_path': c.pc_dx.relative_to(cc.PC_ROOT).as_posix(), 'retail_pc_dx_sha256': sha(pc_dx), 'props': props})
    return models, courses


def build_asset(models, courses):
    textures, tex_index = [], {}
    order = sorted(models)
    vertex_blob, normal_blob, model_blob, point_blob, plane_blob = bytearray(), bytearray(), bytearray(), bytearray(), bytearray()
    def texture_index(t):
        key = sha(t[2])
        if key not in tex_index:
            tex_index[key] = len(textures)
            textures.append(t)
        return tex_index[key]
    total = points = planes = 0
    for name in order:
        m = models[name]
        draws = []
        for d in m['draws']:
            key = sha(d['texture'][2])
            if key not in tex_index:
                tex_index[key] = len(textures)
                textures.append(d['texture'])
            for v, n in zip(d['vertices'], d['normals']):
                vertex_blob += VERTEX.pack(*v)
                normal_blob += NORMAL.pack(*n)
            draws.append((tex_index[key], total, len(d['vertices'])))
            total += len(d['vertices'])
        if not 1 <= len(draws) <= 2:
            raise ValueError(name)
        h = m['hull']
        for p in h['points']:
            point_blob += POINT.pack(*p)
        for q in h['planes']:
            plane_blob += PLANE.pack(*q)
        flat = [x for dr in draws for x in dr] + [0, 0, 0] * (2 - len(draws))
        env = texture_index(m['env']) if m['env'] else -1
        model_blob += MODEL.pack(fixed(m['name'], 16), m['material'], len(draws), *flat, m['radius'],
                                 points, len(h['points']), planes, len(h['planes']), h['radius'], env, *m['aabb'])
        points += len(h['points'])
        planes += len(h['planes'])
    shadow = texture_index(gxi(SHADOW_GXI)[0])
    nprops = sum(len(c['props']) for c in courses)
    out = bytearray(HEADER.pack(MAGIC, VERSION, len(textures), len(models), total, points, planes, len(courses), nprops, shadow))
    for w, h, bgra in textures:
        if len(bgra) != w * h * 4:
            raise ValueError('texture size')
        out += TEXTURE.pack(w, h) + bgra
    out += model_blob + vertex_blob + normal_blob + point_blob + plane_blob
    first = 0
    for c in courses:
        out += COURSE.pack(fixed(c['id'], 48), fixed(c['pc_dx_path'], 64), bytes.fromhex(c['retail_pc_dx_sha256']), first, len(c['props']))
        first += len(c['props'])
    for c in courses:
        for p in c['props']:
            out += PROP.pack(fixed(p['egg'], 32), order.index(p['family']), 1 if p['casts_shadow'] else 0, p['mass'], *p['moi'],
                             p['trigger_distance'], *(x for row in p['matrix'] for x in row))
    return bytes(out)


def inventory(models, courses, asset_sha, coordinates):
    rows = []
    for c in courses:
        props = []
        for p in c['props']:
            row = {k: p[k] for k in ('egg', 'source_id', 'family', 'model', 'mass', 'moi', 'trigger_distance', 'casts_shadow', 'matrix_sha256')}
            if coordinates:
                row['matrix'] = p['matrix']
            props.append(row)
        rows.append({'course': c['name'], 'course_id': c['id'], 'ps2_xml': c['ps2_xml'], 'ps2_xml_sha256': c['ps2_xml_sha256'],
                     'pc_dx_path': c['pc_dx_path'], 'retail_pc_dx_sha256': c['retail_pc_dx_sha256'], 'props': props})
    mods = {}
    for name, m in sorted(models.items()):
        h = m['hull']
        mods[name] = {'material': 'treeblend (source alpha blend, no depth write)' if m['material'] else 'object (opaque)',
                      'ps2_triangles': m['ps2_triangles'], 'dx_triangles_per_draw': m['dx_triangles'], 'two_sided_copies': m['two_sided_copies'],
                      'visual_radius': round(m['radius'], 4),
                      'textures': [{'file': t['file'], 'ps2_texture': t['ps2_texture'], 'pc_source': t['pc_source']} for t in m['textures']],
                      'hull': {'psm': h['psm'], 'psm_sha256': h['psm_sha256'], 'tag101_sha256': h['tag101_sha256'],
                               'representation': 'B geometry_a', 'points': len(h['points']), 'triangles': h['triangles'],
                               'planes': len(h['planes']), 'radius': round(h['radius'], 4), 'base_scalar': h['base_scalar'],
                               'representation_a_vertices': h['representation_a_vertices']},
                      'source_sha256': m['sources']}
    return {'schema_version': 1, 'phase': 'COURSE-ALIVE3', 'asset': ASSET.name, 'asset_sha256': asset_sha,
            'courses': len(rows), 'props': sum(len(r['props']) for r in rows), 'models': mods, 'by_course': rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--inventory', type=Path, help='also write the coordinate-free inventory here')
    ap.add_argument('--output', type=Path, default=ASSET)
    a = ap.parse_args()
    models, courses = collect()
    blob = build_asset(models, courses)
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
                      'props': sum(len(c['props']) for c in courses),
                      'models': {n: {'hull_points': len(m['hull']['points']), 'hull_planes': len(m['hull']['planes'])} for n, m in models.items()}}))


if __name__ == '__main__':
    main()
