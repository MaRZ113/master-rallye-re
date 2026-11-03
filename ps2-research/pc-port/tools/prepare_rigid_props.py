"""COURSE-ALIVE3: private asset and inventory of the 83 PS2 gaAiRigidBody props (58 hay bales, 25 tumbleweeds, 9 courses)
and (COURSE-ALIVE4) the 432 PS2 checkpoint barrels of the 36 courses.

Inputs (read only):
- PS2 RaceTest XML of each course (TNG.PAK/TNG.000): every gaAiRigidBody Egg with its en3d Matrix, model and the four
  typed properties (Mass, MOI, Trigger Distance, Casts Shadow), parsed by the RIGID1 reference
  `ps2-research/tools/rigid_runtime.py` (`parse_authored`: first correctly typed property, original defaults);
- the prop PSM of each family: tag101 convex hull, representation B geometry_a (hay 16 vertices / 28 triangles,
  tumbleweed 26 / 48; rigid1/collision-shapes.md), read with the strict SDK collision reader (`inspect`-equivalent);
- the PC visual models of course-port W5 (`course-port/build_objects.py convert()`): hay = the W5 hay bale, tumbleweed =
  the same conversion with its own PS2 texture `shrubtrig2-tga` (PC file of the same name), retail loader winding,
  two-sided copies;
- the retail PC course DX of each course (only its SHA-256, so the runtime can refuse a stock PC course);
- COURSE-ALIVE4 checkpoint barrels: no authored owner. The first update of every gaRaceSplitTimeAI (181988 -> 1822c0,
  pending flag +24 set by the init 181dd0) looks up the Eggs "%s-%d" (0x46fc10) of its own Egg name for 0..3, gives each
  found Egg a new gaAiRigidBody (19fcd0) with Casts Shadow 1, Mass 500, Trigger Distance 5, MOI (487.5, 900, 487.5),
  sets its model to misc\\objects\\checkpoints\\checkpoint (262f88, also where the Egg authored another model: SpainWFlip
  SplitTime1-3 = nessie) and attaches the owner to AI slot 0 (21e620). Barrel = that PSM: meshes drum/top
  $shader(metal) (3aeb00: mode 3 like dull, no vertex colour auxiliary, secondary = the mesh's second texture
  aluminium), textures from the PS2 GXI (c-point-tga has no PC file), tag101 representation B hull.

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
import ps2_mesh  # noqa: E402
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

MATERIAL_OBJECT, MATERIAL_TREEBLEND, MATERIAL_METAL = 0, 1, 2
FLAG_SHADOW, FLAG_CHECKPOINT = 1, 2
# PS2 model (lower case, backslashes) -> family. The two hay paths are byte-identical (rigid1/collision-shapes.md).
FAMILIES = {
    r'misc\haybale\haybale': 'haybale',
    r'misc\objects\haybales\haybale': 'haybale',
    r'misc\objects\tumbleweed\tumblweed': 'tumblweed',
}
CHECKPOINT_PSM = r'\TNG\DATAPSM\MISC\OBJECTS\CHECKPOINTS\CHECKPOINT.PSM'
CHECKPOINT_MODEL = r'misc\objects\checkpoints\checkpoint'
# 1822c0 constants (lui/ori words at 1822c0..1823d8): +10 = 1, +14 = 0x43fa0000, +18 = 0x40a00000, MOI = (0x43f3c001,
# 0x44610000, 0x43f3c001).
CHECKPOINT_BODY = {'casts_shadow': True, 'mass': struct.unpack('<f', struct.pack('<I', 0x43fa0000))[0],
                   'trigger_distance': struct.unpack('<f', struct.pack('<I', 0x40a00000))[0],
                   'moi': [struct.unpack('<f', struct.pack('<I', w))[0] for w in (0x43f3c001, 0x44610000, 0x43f3c001)]}
CHECKPOINT_TEXTURES = {'c-point-tga': r'\TNG\DATAPSM\COMMONTEXTURES\C-POINT-TGA.GXI',
                       'top-tga': r'\TNG\DATAPSM\COMMONTEXTURES\TOP-TGA.GXI',
                       'aluminium-tga': r'\TNG\DATAPSM\COMMONTEXTURES\ALUMINIUM-TGA.GXI'}
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


def gxi_dxt_rows(path):
    """GXI -> BGRA rows in the PC DXT order (bottom-up), as the PC game uploads its course textures; the PS2 UV is then
    used as is (ps2_mesh.convert_gxi_rows; aluminium-tga: PC DXT rows == flipped GXI rows, exact)."""
    payload = cc.read_ps2(path)
    magic, w, h = struct.unpack_from('<IHH', payload, 0)
    if magic != 0x13039 or len(payload) != 8 + 4 * w * h or w & (w - 1) or h & (h - 1):
        raise ValueError(f'{path}: unsupported GXI')
    return (w, h, ps2_mesh.convert_gxi_rows(payload[8:], w, h)), sha(payload)


def tex_name(t):
    return t['name'].replace('\\', '/').split('/')[-1].lower()


def checkpoint_visual():
    """The PS2 barrel PSM drawn directly: one draw per primary texture (drum c-point, top), PS2 strip triangles in PC
    corner order, every triangle also reversed (objects without back-face culling), PSM prelight colours (metal has no
    vertex colour auxiliary), PS2 UV; secondary aluminium = the environment layer of the model."""
    payload = cc.read_ps2(CHECKPOINT_PSM)
    scene = wr.decode_scene(payload, terminator=101)
    draws, textures, tris = [], [], 0
    for primary in ('c-point-tga', 'top-tga'):
        meshes = [m for m in scene.meshes if m['textures'] and tex_name(m['textures'][0]) == primary]
        if len(meshes) != 1 or '$shader(metal)' not in meshes[0]['material'].lower():
            raise ValueError(f'checkpoint: one metal mesh with {primary} expected')
        second = [tex_name(t) for t in meshes[0]['textures'][1:]]
        if second != ['aluminium-tga']:
            raise ValueError(f'checkpoint: secondary of {primary} is {second}')
        verts, normals = [], []
        for idx in ps2_mesh.mesh_triangles(scene, meshes[0]):
            vs = [ps2_mesh.vertex(payload, i) for i in ps2_mesh.pc_order(payload, idx)]
            tris += 1
            for rev in (False, True):
                for pos, nrm, col, uv in (reversed(vs) if rev else vs):
                    verts.append((*pos, struct.unpack('<I', col)[0], uv[0], uv[1]))
                    normals.append(tuple(-x for x in nrm) if rev else tuple(nrm))
        tex, tex_sha = gxi_dxt_rows(CHECKPOINT_TEXTURES[primary])
        draws.append({'texture_file': primary, 'texture': tex, 'vertices': verts, 'normals': normals})
        textures.append({'file': primary, 'ps2_texture': primary, 'pc_source': f'PS2 {CHECKPOINT_TEXTURES[primary]} (sha256 {tex_sha})'})
    if sum(len(m['strips']) > 0 for m in scene.meshes) != 2:
        raise ValueError('checkpoint: unexpected extra meshes')
    pos = [scene.position(i) for i in range(scene.vertex_count)]
    env, env_sha = gxi_dxt_rows(CHECKPOINT_TEXTURES['aluminium-tga'])
    return {'draws': draws, 'radius': max(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) for p in pos),
            'aabb': [min(p[k] for p in pos) for k in range(3)] + [max(p[k] for p in pos) for k in range(3)],
            'env': env, 'env_source': (CHECKPOINT_TEXTURES['aluminium-tga'], env_sha), 'vertex_color': None,
            'ps2_triangles': tris, 'dx_triangles': [len(d['vertices']) // 3 for d in draws], 'two_sided_copies': True,
            'textures': textures, 'sources': {'CHECKPOINT.PSM': sha(payload)}}


def checkpoint_barrels(payload, source):
    """1822c0: the Eggs "<split Egg>-0".."-3" of every gaRaceSplitTimeAI Egg, in scene order (21e9c0 finds by name)."""
    import xml.etree.ElementTree as ET
    import spline_runtime as srt
    tree = ET.fromstring(payload)
    eggs, splits = {}, []
    for li, group in enumerate(tree.findall('EggLists_Version4/List')):
        for ei, egg in enumerate(group.findall('Egg')):
            eggs.setdefault(egg.get('Name'), (li, ei, egg))
            if any(srt.value(srt.properties(ai), 'AI Name', 'String') == 'gaRaceSplitTimeAI' for ai in egg.findall('AI_List/AI')):
                splits.append(egg.get('Name'))
    out = []
    for name in splits:
        for i in range(4):
            hit = eggs.get(f'{name}-{i}')
            if hit is None:
                continue                      # 3f9698 "Splitpoint marker %s not found": no barrel
            li, ei, egg = hit
            props = srt.properties(egg)
            matrices = [x for x in props if x.get('Name') == 'en3d Matrix' and x.get('Type') == 'Matrix']
            if not matrices:
                raise ValueError(f'{source}/{name}-{i}: no en3d Matrix')
            matrix = [rr.vector(matrices[0].get('Row%d' % k, '').split(), 4) for k in range(4)]
            authored = srt.value(props, 'en3d Model Name', 'String')
            out.append({'egg': f'{name}-{i}', 'source_id': f'{source}:list:{li}:egg:{ei}:split:{name}', 'family': 'checkpoint',
                        'model': CHECKPOINT_MODEL, 'authored_model': authored, **CHECKPOINT_BODY, 'matrix': matrix,
                        'matrix_sha256': sha(struct.pack('<16f', *(v for row in matrix for v in row)))})
    return out


def hull(psm_path, centre_tolerance=1e-3):
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
    if max(abs(x) for x in centre) > centre_tolerance:
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
    # Barrel tag101 base centre (0, 0.0091, 0): 9 mm; the body centre stays the model origin as for the other families.
    models['checkpoint'] = {'name': 'checkpoint', 'material': MATERIAL_METAL, **checkpoint_visual(), 'hull': hull(CHECKPOINT_PSM, 0.02)}
    courses = []
    for c in cc.courses():
        payload = cc.read_ps2(c.ps2_xml)
        case = rr.parse_authored(payload, c.ps2_xml)
        barrels = checkpoint_barrels(payload, c.ps2_xml)
        if not case['records'] and not barrels:
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
        for b in barrels:
            m = b['matrix']
            for row in m[:3]:
                if abs(math.sqrt(sum(x * x for x in row[:3])) - 1) > 2e-2:
                    raise ValueError(f'{c.name}/{b["egg"]}: authored basis is not a rotation')
            if [round(x, 6) for x in (m[0][3], m[1][3], m[2][3], m[3][3])] != [0, 0, 0, 1]:
                raise ValueError(f'{c.name}/{b["egg"]}: authored matrix is not affine')
            props.append({**b, 'matrix': [list(row[:3]) for row in m]})
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
            flags = (FLAG_SHADOW if p['casts_shadow'] else 0) | (FLAG_CHECKPOINT if p['family'] == 'checkpoint' else 0)
            out += PROP.pack(fixed(p['egg'], 32), order.index(p['family']), flags, p['mass'], *p['moi'],
                             p['trigger_distance'], *(x for row in p['matrix'] for x in row))
    return bytes(out)


def inventory(models, courses, asset_sha, coordinates):
    rows = []
    for c in courses:
        props = []
        for p in c['props']:
            row = {k: p[k] for k in ('egg', 'source_id', 'family', 'model', 'mass', 'moi', 'trigger_distance', 'casts_shadow', 'matrix_sha256')}
            if p.get('authored_model') and p['authored_model'].replace('/', '\\').lower() != CHECKPOINT_MODEL:
                row['authored_model'] = p['authored_model']
            if coordinates:
                row['matrix'] = p['matrix']
            props.append(row)
        rows.append({'course': c['name'], 'course_id': c['id'], 'ps2_xml': c['ps2_xml'], 'ps2_xml_sha256': c['ps2_xml_sha256'],
                     'pc_dx_path': c['pc_dx_path'], 'retail_pc_dx_sha256': c['retail_pc_dx_sha256'], 'props': props})
    mods = {}
    for name, m in sorted(models.items()):
        h = m['hull']
        mods[name] = {'material': {MATERIAL_OBJECT: 'object (opaque)', MATERIAL_TREEBLEND: 'treeblend (source alpha blend, no depth write)',
                                   MATERIAL_METAL: 'metal (opaque, mode-3 aluminium environment added)'}[m['material']],
                      'ps2_triangles': m['ps2_triangles'], 'dx_triangles_per_draw': m['dx_triangles'], 'two_sided_copies': m['two_sided_copies'],
                      'visual_radius': round(m['radius'], 4),
                      'textures': [{'file': t['file'], 'ps2_texture': t['ps2_texture'], 'pc_source': t['pc_source']} for t in m['textures']],
                      'hull': {'psm': h['psm'], 'psm_sha256': h['psm_sha256'], 'tag101_sha256': h['tag101_sha256'],
                               'representation': 'B geometry_a', 'points': len(h['points']), 'triangles': h['triangles'],
                               'planes': len(h['planes']), 'radius': round(h['radius'], 4), 'base_scalar': h['base_scalar'],
                               'representation_a_vertices': h['representation_a_vertices']},
                      'source_sha256': m['sources']}
    return {'schema_version': 2, 'phase': 'COURSE-ALIVE3 + COURSE-ALIVE4', 'asset': ASSET.name, 'asset_sha256': asset_sha,
            'courses': len(rows), 'props': sum(len(r['props']) for r in rows),
            'checkpoint_barrels': sum(p['family'] == 'checkpoint' for r in rows for p in r['props']), 'models': mods, 'by_course': rows}


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
