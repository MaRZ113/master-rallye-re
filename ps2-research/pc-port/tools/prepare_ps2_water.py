"""COURSE-WATER1: PS2 water asset for the proxy (PS2Water=1) and the 36-course water inventory.

For every course (cdelta1/course-pairs.json via course-port/course_config.py):
1. PS2 source: the landscape PSM meshes whose $shader is puddle (mode 9), water (10) or waterfall/waterall (19), with their
   authored strip vertices (normal, colour word, UV, position) in strip order (control bit 0 skips a triangle, zero-area
   triangles are dropped: the course-port W2 rule, so the triangle set equals the converted course).
2. PS2 vertex data the shaders derive at load time:
   - puddle RGBA from the 2d4618 ground query (320938, ps2_water_model.puddle_rgba);
   - water UV from 321098 at load phase T0 = 0 (any load phase is a phase shift of the same static pattern).
3. Native draws to replace: every draw of the converted course DX (research-output/course-port-36) and of the retail PC
   course DX whose triangles are all PS2 water triangles (exact float32 positions for the package; 0.001 for retail). The
   runtime recognises such a draw by its triangle count and an order-free SHA-256 of its triangle positions, and draws
   the matched PS2 triangles with the PS2 passes instead (one rendering path per surface).
4. Textures: course water map = the PC 128x128 file when it shows the PS2 image (TRACK-GROUND1 policy), else the PS2 GXI;
   CommonTextures/WATERSURFACE2 (second puddle/water layer) and WATERFALL/WATERFALL2 (both waterfall layers, which the
   PS2 classifier binds instead of the authored maps) come from the PS2 files. Alpha is the PS2 alpha as the GS sees it.

Output (ignored, contains course geometry): .assets/course/PS2Water.ps2wtr; --inventory writes the coordinate-free
inventory committed in docs/course-water1/.

    python ps2-research/pc-port/tools/prepare_ps2_water.py [--inventory docs/course-water1/inventory.json] [--courses Turkey3,...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
sys.path[:0] = [str(PORT / 'tools'), str(RESEARCH / 'course-port'), str(RESEARCH / 'tools'), str(RESEARCH.parent / 'src')]
import course_config as cc  # noqa: E402
import detail_runtime as dr  # noqa: E402
import ps2_mesh  # noqa: E402
import ps2_water_model as wm  # noqa: E402
import water_runtime as wr  # noqa: E402
from master_rallye.course_render_writer import CourseRender  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402

MAGIC = b'PS2WTR01'
VERSION = 1
ASSET = PORT / '.assets' / 'course' / 'PS2Water.ps2wtr'
PACKAGES = Path('D:/Game/Master Rallye/research-output/course-port-36')
HEADER = struct.Struct('<8s7I')       # magic, version, textures, courses, keys, parts, vertices, reserved 0
TEXTURE = struct.Struct('<2I')        # width, height, then w*h D3D A8R8G8B8 words, rows in D3D order (row 0 = v 0)
COURSE = struct.Struct('<48s3I')      # course id, first key, key count, flags (1 = has package keys)
KEY = struct.Struct('<2I32s2I')       # triangle count, source (1 package, 2 retail), order-free position SHA-256, first part, parts
PART = struct.Struct('<6If')          # mode, primary texture, secondary texture, address (bit0 clamp u, bit1 clamp v), first vertex, vertices, waterfall first Y
VERTEX = struct.Struct('<3f3f2f4B4f')  # position, normal, authored UV, PS2 RGBA bytes (R G B A), static water UV (u0 v0 u1 v1)
MODE_NAMES = {9: 'puddle', 10: 'water', 19: 'waterfall'}
COMMON = {'watersurface2': r'\TNG\DATAPSM\COMMONTEXTURES\WATERSURFACE2.GXI',
          'waterfall': r'\TNG\DATAPSM\COMMONTEXTURES\WATERFALL-TGA.GXI',
          'waterfall2': r'\TNG\DATAPSM\COMMONTEXTURES\WATERFALL2-TGA.GXI'}
SAME_IMAGE_LIMIT = 3.0                 # mean absolute 8-bit error after a 2x2 box reduction (TRACK-GROUND1 used the same test)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fixed(text: str, size: int) -> bytes:
    raw = text.encode('ascii')
    if len(raw) >= size:
        raise ValueError(f'name too long: {text}')
    return raw + b'\0' * (size - len(raw))


def f32b(v) -> bytes:
    return struct.pack('<3f', *v)


# ---- textures -------------------------------------------------------------------------------------------------------

def gs_alpha(a: int) -> int:
    """GXI alpha byte -> the D3D byte of the same GS coefficient: the upload stores a >> 1 (128 = 1.0)."""
    return min(255, ((a >> 1) * 255 + 64) // 128)


def gxi_texture(payload: bytes, alpha_one=False):
    w, h = struct.unpack_from('<HH', payload, 4)
    if struct.unpack_from('<I', payload, 0)[0] != 0x13039 or len(payload) != 8 + 4 * w * h:
        raise ValueError('unsupported GXI')
    px = payload[8:]
    words = []
    for y in range(h):                       # D3D row y = GXI row h-1-y (the GS samples t = 0 at the last GXI row)
        row = px[(h - 1 - y) * 4 * w:(h - y) * 4 * w]
        for x in range(w):
            r, g, b, a = row[4 * x:4 * x + 4]
            words.append(((255 if alpha_one else gs_alpha(a)) << 24) | (r << 16) | (g << 8) | b)
    return w, h, words


def pc_texture_if_same(dxt_path: Path, gxi_payload: bytes):
    """PC DXT level 0 (rows as stored = D3D rows) with alpha 255 when it is the PS2 image at twice the size."""
    if not dxt_path.is_file():
        return None, 'pc_file_missing'
    t = parse_dxt_bytes(dxt_path.read_bytes())
    w, h = struct.unpack_from('<HH', gxi_payload, 4)
    if (t.width, t.height) != (2 * w, 2 * h):
        return None, f'pc_size_{t.width}x{t.height}'
    px = gxi_payload[8:]
    err = 0
    for y in range(h):
        for x in range(w):
            s = [0, 0, 0]
            for dy in range(2):
                for dx in range(2):
                    o = ((2 * (h - 1 - y) + dy) * t.width + 2 * x + dx) * 4
                    s = [s[0] + t.bgra[o + 2], s[1] + t.bgra[o + 1], s[2] + t.bgra[o]]
            o = (y * w + x) * 4
            err += sum(abs(s[k] / 4 - px[o + k]) for k in range(3))
    err /= 3 * w * h
    if err > SAME_IMAGE_LIMIT:
        return None, f'pc_image_differs_{err:.2f}'
    words = [(0xff << 24) | (t.bgra[4 * i + 2] << 16) | (t.bgra[4 * i + 1] << 8) | t.bgra[4 * i] for i in range(t.width * t.height)]
    return (t.width, t.height, words), f'pc_same_image_{err:.2f}'


class Textures:
    def __init__(self):
        self.items, self.index, self.provenance = [], {}, []

    def add(self, key, tex, provenance):
        if key not in self.index:
            self.index[key] = len(self.items)
            self.items.append(tex)
            self.provenance.append(provenance)
        return self.index[key]


# ---- PS2 water source -----------------------------------------------------------------------------------------------

def canon(points):
    return b''.join(sorted(f32b(p) for p in points))


def round_key(points, step=1e-3):
    return tuple(sorted(tuple(round(c / step) for c in p) for p in points))


def ps2_water(course, payload):
    scene = wr.decode_scene(payload)
    land = dr.decode_landscape(payload)
    meshes = []
    for mi, mesh in enumerate(scene.meshes):
        mode = mesh['classification']['water_mode']
        if mode is None:
            continue
        cache = {}

        def vert(i):
            if i not in cache:
                pos, nrm, col, uv = ps2_mesh.vertex(payload, i)
                rgba = tuple(col)                       # R G B A as the course render stores the PSM colour word
                if mode == 9:
                    w = wm.puddle_rgba(land, pos)
                    rgba = (w, w, w, w)
                elif mode == 10:
                    rgba = (254, 254, 254, 254)
                cache[i] = dict(pos=pos, nrm=nrm, uv=uv, rgba=rgba)
            return cache[i]
        tris = []
        for idx in ps2_mesh.mesh_triangles(scene, mesh):
            tris.append(tuple(vert(i) for i in idx))
        if mode == 10:                                  # 321098 over the whole mesh (vertex order of its strips)
            order = [i for s in mesh['strips'] for i in range(s['start'], s['start'] + s['count'])]
            uvs = wm.water_mesh_uv([(vert(i)['pos'], vert(i)['nrm']) for i in order], 0.0)
            for i, uv in zip(order, uvs):
                cache[i]['water_uv'] = uv
        first = min(s['start'] for s in mesh['strips']) if mesh['strips'] else 0  # 321838 reads the first vertex of the mesh range (mesh+0x30)
        textures = [t['name'] for t in mesh['textures']]
        material = mesh['material']
        clamp = (1 if '$clamp(u)' in material or '$clamp(uv)' in material else 0) | (2 if '$clamp(v)' in material or '$clamp(uv)' in material else 0)
        meshes.append(dict(index=mi, mode=mode, shader=mesh['classification']['authored_shader'], textures=textures,
                           material=material, triangles=tris, first_y=struct.unpack_from('<3f', payload, 32 + 52 * first + 36)[1],
                           clamp=clamp))
    return scene, meshes


def draw_triangles(cr: CourseRender, d):
    out = []
    for k in range(d.index_start, d.index_start + d.index_count, 3):
        out.append(tuple(cr.positions[d.vertex_base + cr.indices[k + j]] for j in range(3)))
    return out


TOLERANCE = 1e-3                       # the WATER1/GEOM1 correspondence tolerance; shared PC triangles keep PC positions
CELL = 0.05


def _cell(p):
    return tuple(int(c // CELL) for c in p)


def same_triangle(a, b):
    """Every corner of a has a corner of b within TOLERANCE (corner order free)."""
    return all(any(max(abs(x - y) for x, y in zip(p, q)) <= TOLERANCE for q in b) for p in a) and \
        all(any(max(abs(x - y) for x, y in zip(p, q)) <= TOLERANCE for q in a) for p in b)


def match_draws(cr, meshes):
    """Draws whose every triangle is a PS2 water triangle (corners within 0.001); each PS2 triangle instance is claimed
    once. Draws that mix water and other triangles are counted, not claimed: the runtime must replace whole draws."""
    grid = defaultdict(list)
    for m in meshes:
        for t in m['triangles']:
            centroid = tuple(sum(v['pos'][k] for v in t) / 3 for k in range(3))
            grid[_cell(centroid)].append([m, t, False])

    def find(tri):
        c = _cell(tuple(sum(p[k] for p in tri) / 3 for k in range(3)))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for entry in grid.get((c[0] + dx, c[1] + dy, c[2] + dz), ()):
                        if not entry[2] and same_triangle(tri, [v['pos'] for v in entry[1]]):
                            return entry
        return None
    draws, partial = [], []
    for d in cr.draws():
        tris = draw_triangles(cr, d)
        if not tris:
            continue
        found = []
        for t in tris:
            e = find(t)
            if e is not None:
                e[2] = True                              # provisional claim, released below if the draw is not all water
            found.append(e)
        hits = sum(1 for e in found if e is not None)
        if hits == 0:
            continue
        if hits != len(tris):
            for e in found:
                if e is not None:
                    e[2] = False
            partial.append(dict(slots='/'.join(d.texture_tuple), water=hits, triangles=len(tris)))
            continue
        taken = [(e[0], order_corners(e[1], t)) for e, t in zip(found, tris)]
        order_free = sha(b''.join(sorted(canon(t) for t in tris)))
        draws.append(dict(triangles=len(tris), key=order_free, taken=taken, slots=d.texture_tuple,
                          flags=d.flags_0x20.hex(), feature=d.unknown_0x24))
    return draws, partial


def order_corners(ps2_tri, pc_tri):
    """The PS2 vertices in the corner order of the native draw (the replaced draw keeps the PC winding)."""
    out = []
    for p in pc_tri:
        out.append(min(ps2_tri, key=lambda v: max(abs(x - y) for x, y in zip(v['pos'], p))))
    return tuple(out)


def course_package_dx(name):
    root = PACKAGES / name / 'DataGx' / 'Course'
    found = list(root.glob('*/*.dx')) if root.is_dir() else []
    return found[0] if len(found) == 1 else None


def course_texture(course, mesh, pkg_dx, textures):
    """Primary map of a water/puddle mesh (slot 0 course map) or the common waterfall pair (the classifier binds them)."""
    if mesh['mode'] == 19:
        return (textures.add('common:waterfall', gxi_texture(cc.read_ps2(COMMON['waterfall'])), 'PS2 CommonTextures/WATERFALL-TGA.GXI'),
                textures.add('common:waterfall2', gxi_texture(cc.read_ps2(COMMON['waterfall2'])), 'PS2 CommonTextures/WATERFALL2-TGA.GXI'))
    name = mesh['textures'][0] if mesh['textures'] else None
    if not name:
        raise ValueError(f'{course.name}: water mesh without a course map')
    rel = name.replace('/', '\\')                          # e.g. course\france1\water-tga (2fd7d0 adds the root and .gxi)
    gxi_path = '\\TNG\\DATAPSM\\' + rel.upper() + '.GXI'
    gxi = cc.read_ps2(gxi_path)
    stem = rel.split('\\')[-1].lower()
    candidates = []
    if pkg_dx is not None:
        candidates.append(pkg_dx.parent / f'{stem}.dxt')
    candidates.append(course.pc_dx.parent / f'{stem}.dxt')
    tex, why = None, 'pc_file_missing'
    for c in candidates:
        if c.is_file():
            tex, why = pc_texture_if_same(c, gxi)
            if tex:
                key = 'pc:' + sha(c.read_bytes())
                prov = f'PC {c.parent.name}/{c.name} (same image as PS2 {name}.GXI, {why}), alpha 255 (PS2 CT16 alpha bit)'
                break
    if tex is None:
        tex = gxi_texture(gxi, alpha_one=True)
        key = 'ps2:' + sha(gxi)
        prov = f'PS2 {gxi_path} ({why}), alpha 255 (PS2 CT16 alpha bit)'
    primary = textures.add(key, tex, prov)
    secondary = textures.add('common:watersurface2', gxi_texture(cc.read_ps2(COMMON['watersurface2'])),
                             'PS2 CommonTextures/WATERSURFACE2.GXI, GS alpha (a >> 1)')
    return primary, secondary


def build(selected=None):
    textures = Textures()
    courses, inventory = [], []
    for course in cc.courses():
        if selected and course.name not in selected:
            continue
        payload = cc.read_ps2(course.ps2_psm)
        scene, meshes = ps2_water(course, payload)
        row = dict(course=course.name, ps2_landscape=course.ps2_landscape, psm_sha256=sha(payload),
                   meshes={MODE_NAMES[m]: sum(1 for x in meshes if x['mode'] == m) for m in (9, 10, 19)},
                   triangles={MODE_NAMES[m]: sum(len(x['triangles']) for x in meshes if x['mode'] == m) for m in (9, 10, 19)},
                   shaders=sorted({m['shader'] for m in meshes}))
        pkg = course_package_dx(course.name)
        keys = []
        if meshes:
            sources = []
            if pkg is not None:
                sources.append(('package', pkg))
            sources.append(('retail', course.pc_dx))
            covered = {}
            for source, path in sources:
                data = path.read_bytes()
                cr = CourseRender.from_bytes(data, str(path))
                draws, partial = match_draws(cr, meshes)
                ps2_total = sum(len(m['triangles']) for m in meshes)
                claimed = sum(d['triangles'] for d in draws)
                covered[source] = dict(dx_sha256=sha(data), draws=len(draws), triangles=claimed, ps2_triangles=ps2_total,
                                       draws_partly_water=partial,
                                       draw_materials=sorted({'/'.join(d['slots']) + ' flags ' + d['flags'] + ' feature ' + str(d['feature']) for d in draws}))
                for d in draws:
                    if any(k['key'] == d['key'] and k['triangles'] == d['triangles'] for k in keys):
                        continue                         # package and retail draw with identical positions: one key
                    parts = []
                    by_mesh = defaultdict(list)
                    for m, t in d['taken']:
                        by_mesh[m['index']].append((m, t))
                    for mi in sorted(by_mesh):
                        m = by_mesh[mi][0][0]
                        prim, sec = course_texture(course, m, pkg, textures)
                        verts = [v for _, t in by_mesh[mi] for v in t]
                        parts.append(dict(mode=m['mode'], primary=prim, secondary=sec, clamp=m['clamp'], first_y=m['first_y'], vertices=verts))
                    keys.append(dict(source=1 if source == 'package' else 2, triangles=d['triangles'], key=d['key'], parts=parts))
            row['native_draws'] = covered
            row['package_complete'] = bool(pkg) and covered.get('package', {}).get('triangles') == covered.get('package', {}).get('ps2_triangles')
        row['package_dx'] = pkg.name if pkg else None
        inventory.append(row)
        if keys:
            courses.append(dict(id='RaceTest/' + course.name, keys=keys))
    return textures, courses, inventory


def serialize(textures, courses):
    keys = [k for c in courses for k in c['keys']]
    parts = [p for k in keys for p in k['parts']]
    vertices = sum(len(p['vertices']) for p in parts)
    out = bytearray(HEADER.pack(MAGIC, VERSION, len(textures.items), len(courses), len(keys), len(parts), vertices, 0))
    for w, h, words in textures.items:
        out += TEXTURE.pack(w, h) + struct.pack(f'<{len(words)}I', *words)
    first_key = 0
    for c in courses:
        flags = 1 if any(k['source'] == 1 for k in c['keys']) else 0
        out += COURSE.pack(fixed(c['id'], 48), first_key, len(c['keys']), flags)
        first_key += len(c['keys'])
    first_part = 0
    for k in keys:
        out += KEY.pack(k['triangles'], k['source'], bytes.fromhex(k['key']), first_part, len(k['parts']))
        first_part += len(k['parts'])
    first_vertex = 0
    for p in parts:
        out += PART.pack(p['mode'], p['primary'], p['secondary'], p['clamp'], first_vertex, len(p['vertices']), p['first_y'])
        first_vertex += len(p['vertices'])
    for p in parts:
        for v in p['vertices']:
            out += VERTEX.pack(*v['pos'], *v['nrm'], *v['uv'], *v['rgba'], *v.get('water_uv', (0.0, 0.0, 0.0, 0.0)))
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inventory', type=Path)
    ap.add_argument('--courses')
    ap.add_argument('--output', type=Path, default=ASSET)
    args = ap.parse_args()
    selected = set(args.courses.split(',')) if args.courses else None
    textures, courses, inventory = build(selected)
    blob = serialize(textures, courses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    summary = dict(asset=args.output.name, asset_sha256=sha(blob), asset_bytes=len(blob), textures=textures.provenance,
                   courses_with_keys=len(courses), keys=sum(len(c['keys']) for c in courses),
                   courses=inventory)
    if args.inventory:
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('asset', 'asset_sha256', 'asset_bytes', 'courses_with_keys', 'keys')}))


if __name__ == '__main__':
    main()
