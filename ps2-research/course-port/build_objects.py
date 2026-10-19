"""W5/W6 assets: PS2 moving and physical course objects as loose PC models, plus an optional static placement of the moving ones.

The PS2 classes that drive these objects (`gaEntitySpline` boats, barges and airships, `gaAiRigidBody` hay bales and tumbleweeds,
`gaAnimals_BirdManager`) do not exist in the PC executable, so their behaviour needs native code (STATUS.md, W5/W6). This script prepares the
data that such code (or a static stand-in) needs:

- one PC DX per PS2 model under `DataGx/Misc/PS2Port/<name>/`, built on a retail template with the same draw count (`haybaletest.dx` for one
  texture, `checkpoint.dx` for two). Geometry = the PS2 model triangles (ps2_mesh strip rule) in PC corner order with the PS2 normals, colours and
  raw UV, each triangle also stored reversed (PS2 draws objects without back-face culling, the v4 object rule of the course render).
  Textures: the PC 128x128 file of the same name (TRACK-GROUND1 policy), copied next to the model under a name of the template slot length
  (the template slot strings are patched in place, their length must not change).
- `--static-splines`: each `gaEntitySpline` Egg as a plain Egg (no AI) at the PS2 start pose of its route: position = first marker (the
  Catmull-Rom curve passes through its knots), forward = direction to the second marker (the PS2 owner uses the secant, `1a9e08`), up =
  (0, 1, 0) (banking off at rest), right = (G.z, G.y, -G.x) (`1aa2e0`). The object then stands still; this is a stand-in, not the PS2
  behaviour.

    python build_objects.py --out <dir> [--static-splines --xml-dir <dir with build_logic XML>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402
import ps2_mesh  # noqa: E402
import water_runtime as w  # noqa: E402
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, rebuild_topology  # noqa: E402

DATAGX = cc.PC_ROOT / 'DataGx'
TEMPLATES = {1: 'Misc/Haybale/haybaletest.dx', 2: 'Misc/Checkpoints/checkpoint.dx'}

# PS2 model -> PC folder name and, per template draw, the PS2 texture of the meshes that go there.
MODELS = {
    r'misc\objects\dinghys\bluedinghy': {'name': 'bluedinghy', 'draws': ['dinghy-tga']},
    r'misc\objects\dinghys\reddinghy': {'name': 'reddinghy', 'draws': ['dinghy-tga']},
    r'misc\airship\airship': {'name': 'airship', 'draws': ['stamp_01-tga']},
    r'misc\barge\barge': {'name': 'barge', 'draws': ['basegravel-tga', 'plating2-tga']},
    r'misc\haybale\haybale': {'name': 'haybale', 'draws': ['hay-tga']},
}
NOT_CONVERTED = {
    r'misc\objects\haybales\haybale': 'byte-identical alias of misc\\haybale\\haybale (rigid1/collision-shapes.md), uses the same PC model',
    r'misc\objects\tumbleweed\tumblweed': 'treeblend (alpha) material: no alpha template for loose models yet',
}


def decode(payload):
    for term in (101, 100, 0xFFFFFFFF):
        try:
            return w.decode_scene(payload, terminator=term)
        except Exception:  # noqa: BLE001 - try the other terminator
            continue
    raise ValueError('PSM does not decode')


def pc_texture(name):
    """First PC DXT of that name (all copies of a common texture are the same image; the first course folder in sorted order)."""
    hits = sorted(p for p in DATAGX.rglob(name + '.dxt'))
    if not hits:
        hits = sorted(p for p in DATAGX.rglob('*.dxt') if p.stem.lower() == name.lower())
    return hits[0] if hits else None


def alias(name, length, used):
    """A texture file name of exactly `length` characters ending in -tga, derived from name, not in used."""
    stem = re.sub(r'[^a-z0-9_]', '', name.lower().replace('-tga', ''))
    for k in range(100):
        base = (stem + str(k) if k else stem)
        cand = (base[:length - 4] if len(base) >= length - 4 else base + 'x' * (length - 4 - len(base))) + '-tga'
        if len(cand) == length and cand not in used:
            used.add(cand)
            return cand
    raise ValueError('no alias')


def white_dxt(size=8):
    """Uncompressed BGRA DXT in the layout of the retail hay-tga.dxt header (as ps2_obj_to_dx: word 0x08 = CRC32 of the pixels)."""
    import struct
    import zlib
    hay = parse_dxt_bytes((DATAGX / 'Misc/Haybale/hay-tga.dxt').read_bytes())
    px = bytes([255]) * (size * size * 4)
    return hay.header[:8] + struct.pack('<3I', zlib.crc32(px) & 0xFFFFFFFF, size, size) + px


def geometry(payload, scene, meshes):
    verts, faces = [], []
    for mesh in meshes:
        for idx in ps2_mesh.mesh_triangles(scene, mesh):
            order = ps2_mesh.pc_order(payload, idx)
            vs = [ps2_mesh.vertex(payload, i) for i in order]
            for rev in (False, True):
                base = len(verts)
                for pos, nrm, col, uv in (reversed(vs) if rev else vs):
                    n = tuple(-x for x in nrm) if rev else nrm
                    verts.append(CompiledVertex(tuple(pos), tuple(n), bytes(col), ((uv[0], uv[1]),)))
                faces.append((base, base + 1, base + 2))
    return DrawGeometry(tuple(verts), tuple(faces))


def convert(model, spec):
    payload = cc.read_ps2('\\TNG\\DATAPSM\\' + model.upper() + '.PSM')
    scene = decode(payload)
    n = len(spec['draws'])
    template = (DATAGX / TEMPLATES[n]).read_bytes()
    groups = []
    for tex in spec['draws']:
        ms = [m for m in scene.meshes if m['textures'] and m['textures'][0]['name'].replace('\\', '/').split('/')[-1].lower() == tex]
        groups.append(ms)
    if sum(len(g) for g in groups) != len(scene.meshes):
        raise ValueError(f'{model}: meshes not covered by the draw list')
    edits = {i: geometry(payload, scene, g) for i, g in enumerate(groups)}
    rebuilt = rebuild_topology(template, edits, bounds_mode='recompute')
    dx = bytearray(rebuilt.data)
    files, used, rep_tex = {}, set(), []
    for draw, tex in zip(rebuilt.output_model.physical_draws, spec['draws']):
        slot = next(s for s in draw.texture_slots if s.slot == 0)
        length = int.from_bytes(dx[slot.data_offset - 4:slot.data_offset], 'little')
        old = bytes(dx[slot.data_offset:slot.data_offset + length])
        if not old.endswith(b'-tga'):
            raise ValueError(f'{model}: unexpected template slot {old!r}')
        notex = all('$shader(notexture)' in m['material'].lower() for m in groups[draw.draw_index])
        src = None if notex else pc_texture(tex)
        if src is None and not notex:
            raise ValueError(f'{model}: PC texture {tex} not found')
        name = tex if len(tex) == length and tex not in used and not notex else alias('white' if notex else tex, length, used)
        used.add(name)
        dx[slot.data_offset:slot.data_offset + length] = name.encode()
        blob = white_dxt() if notex else src.read_bytes()
        parse_dxt_bytes(blob)
        files[name + '.dxt'] = blob
        rep_tex.append({'draw': draw.draw_index, 'ps2_texture': tex, 'file': name + '.dxt',
                        'pc_source': 'white 8x8 ($shader(notexture): vertex colour only, read from the shader name)' if notex else str(src.relative_to(cc.PC_ROOT))})
    parsed = parse_dx_bytes(bytes(dx))
    tri = [len(e.triangles) for e in edits.values()]
    files[spec['name'] + '.dx'] = bytes(dx)
    src_tris = sum(len(ps2_mesh.mesh_triangles(scene, m)) for m in scene.meshes)
    rep = {'ps2_model': model, 'pc_model': f'misc\\ps2port\\{spec["name"]}\\{spec["name"]}', 'template': TEMPLATES[n], 'ps2_triangles': src_tris,
           'dx_triangles_per_draw': tri, 'two_sided_copies': sum(tri) == 2 * src_tris, 'parses': len(parsed.physical_draws) == n,
           'textures': rep_tex}
    return files, rep


def egg_block(name, model, pos, fwd, eol):
    import ps2_obj_to_dx as o
    g = fwd
    rows = ((g[2], g[1], -g[0]), (0.0, 1.0, 0.0), g)
    blk = o.egg_xml(name, model, pos, rows)
    return blk if eol == b'\r\n' else blk.replace(b'\r\n', b'\n')


def static_splines(course, xml, eol):
    """Plain Eggs at the PS2 start pose of each gaEntitySpline Egg, appended to the IContManager list."""
    ps2 = parse_course_xml_bytes(cc.read_ps2(course.ps2_xml), 'ps2')
    out = []
    for e in ps2.eggs:
        comp = next(iter(e.components('gaEntitySpline')), None)
        if comp is None:
            continue
        vals = {v.name: v.value for v in comp.values}
        ml = ps2.marker_list(vals.get('MarkerList Name'))
        model = (e.model_name or '').lower()
        if ml is None or len(ml.markers) < 2 or model not in MODELS:
            out.append({'egg': e.name, 'skipped': 'route or model missing'})
            continue
        p0, p1 = ml.markers[0].position, ml.markers[1].position
        d = [p1[i] - p0[i] for i in range(3)]
        L = math.sqrt(sum(x * x for x in d)) or 1.0
        fwd = tuple(x / L for x in d)
        name = MODELS[model]['name']
        out.append({'egg': 'ps2_' + e.name, 'model': name, 'pos': p0, 'forward': fwd, 'route': ml.name, 'route_markers': len(ml.markers),
                    'params': vals, 'route_points': [m.position for m in ml.markers],
                    'block': egg_block('ps2_' + e.name, f'misc\\ps2port\\{name}\\{name}', p0, fwd, eol)})
    blocks = b''.join(r.pop('block') for r in out if 'block' in r)
    if blocks:
        m = re.search(rb'<List Name="(IContManager|IConManager)">', xml)
        start = m.start()
        end = xml.index(b'</List>', start)
        end = xml.rindex(b'\n', 0, end) + 1
        xml = xml[:end] + blocks + xml[end:]
        parse_course_xml_bytes(xml, 'with static splines')
    return xml, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True, help='package root; models go to <out>/DataGx/Misc/PS2Port')
    ap.add_argument('--static-splines', action='store_true')
    ap.add_argument('--xml-dir', type=Path, help='per-course package root (<xml-dir>/<Course>/DataScene/RaceTest/<Course>.xml) to extend')
    a = ap.parse_args()
    report = {'models': {}, 'not_converted': NOT_CONVERTED, 'static_splines': {}}
    for model, spec in MODELS.items():
        files, rep = convert(model, spec)
        d = a.out / 'DataGx' / 'Misc' / 'PS2Port' / spec['name']
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob('*'):           # only files this script wrote earlier
            if old.suffix.lower() in ('.dx', '.dxt'):
                old.unlink()
        for fn, blob in files.items():
            (d / fn).write_bytes(blob)
        rep['files'] = {fn: hashlib.sha256(b).hexdigest()[:16] for fn, b in files.items()}
        report['models'][spec['name']] = rep
        print(spec['name'], rep['ps2_triangles'], 'triangles', 'ok' if rep['parses'] and rep['two_sided_copies'] else rep, flush=True)
    if a.static_splines:
        if a.xml_dir is None:
            raise SystemExit('--static-splines needs --xml-dir')
        for c in cc.courses():
            p = a.xml_dir / c.name / c.pc_xml.relative_to(cc.PC_ROOT)
            if not p.exists():
                continue
            xml = p.read_bytes()
            new, rows = static_splines(c, xml, b'\r\n' if b'\r\n' in xml[:200] else b'\n')
            if rows:
                (a.out / c.name / c.pc_xml.relative_to(cc.PC_ROOT)).parent.mkdir(parents=True, exist_ok=True)
                (a.out / c.name / c.pc_xml.relative_to(cc.PC_ROOT)).write_bytes(new)
                report['static_splines'][c.name] = rows
                print(c.name, [r.get('egg') for r in rows], flush=True)
    (a.out / 'objects-report.json').write_text(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
