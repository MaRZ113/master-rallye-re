"""COURSE-ALIVE2: private asset and inventory of the PS2 bird system (gaAnimals_BirdManager) for all 36 courses.

Inputs (read only, canonical PS2 corpus through PackFS):
- the 36 RaceTest XML: the BirdManager properties (typed first-match reader of AMBIENT2 `bird_runtime.parse_authored`)
  and the named FlightList / MillList marker lists;
- MISC/ANIMALS/BURDYBROWN.PSB (four images, two triangles each) and BURDYBROWN_000.GXI (64x64 RGBA). The White bank is
  never selected (1af0b0 writes the "Bird Brown" property instead of reading it, so +94 keeps its constructor value 1);
- the retail PC course DX of each course (SHA-256 only, for the stock-course guard).

Texture: the GXI rows are stored top-down and the PS2 uploads them so that VRAM row r = file row 63-r (the PSB UVs
v=0.75..1.0 address the sprite band that is file rows 0..15). Each 16x16 frame cell is written as its own texture in
VRAM row order, so the D3D draw can use CLAMP exactly like the PS2 REGION_CLAMP of the atlas rectangle (CLAMP WMS/WMT=2).
Alpha: GXI 0/255 -> the PS2 loader halves it (resident NOISE.GXI 128 -> 64 in the owner's GS dumps), i.e. 0 / 1.0.

Output: `.assets/course/PS2Birds.ps2bird` and `.assets/course/birds-inventory-full.json` (ignored, contain PS2
coordinates); `--inventory <path>` writes the coordinate-free inventory committed in docs/course-alive2/.

    python ps2-research/pc-port/tools/prepare_ps2_birds.py [--inventory docs/course-alive2/inventory.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
RESEARCH = PORT.parent
sys.path[:0] = [str(RESEARCH / 'course-port'), str(RESEARCH / 'tools'), str(PORT / 'tools')]
import course_config as cc  # noqa: E402
import bird_runtime as br  # noqa: E402
import psbtool  # noqa: E402

MAGIC = b'PS2BRD01'
VERSION = 1
ASSET = PORT / '.assets' / 'course' / 'PS2Birds.ps2bird'
FULL = PORT / '.assets' / 'course' / 'birds-inventory-full.json'
HEADER = struct.Struct('<8s4I')            # magic, version, frames, courses, points
CELL = 16
FRAME = struct.Struct('<I6f6f')            # cell; 3 x (local x, local y) raw PSB ints as float; then 3 x (u, v) ... per triangle
COURSE = struct.Struct('<48s64s32s4f2i2B2x2I')  # id, PC DX path, retail SHA, minfly maxfly minmil maxmil, rndfly rndmil,
#                                                   flight_present, mill_present, first point, point count
POINT = struct.Struct('<3f')
B = chr(92)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fixed(text, size):
    raw = text.encode('ascii')
    if len(raw) >= size:
        raise ValueError(text)
    return raw + b'\0' * (size - len(raw))


def resource(suffix):
    hits = [p for p in cc.manifest() if p.endswith(suffix)]
    if len(hits) != 1:
        raise ValueError(f'{suffix}: {len(hits)} matches')
    return hits[0], cc.read_ps2(hits[0])


def bank():
    psb_path, psb = resource(B + 'MISC' + B + 'ANIMALS' + B + 'BURDYBROWN.PSB')
    gxi_path, gxi = resource(B + 'MISC' + B + 'ANIMALS' + B + 'BURDYBROWN_000.GXI')
    doc = psbtool.parse_psb(psb)
    if doc['unknown_ranges'] or doc['texture_references'] != ['burdybrown_000']:
        raise ValueError('unexpected Burdy bank')
    info = psbtool.parse_gxi(gxi)
    if (info['width'], info['height']) != (64, 64) or info['alpha_min'] != 0 or info['alpha_max'] != 255:
        raise ValueError('unexpected Burdy atlas')
    px = gxi[8:]
    frames = []
    for mapping, image in zip(doc['mappings'], doc['images']):
        if mapping['key_u32'] != image['image_index'] or image['triangle_count'] != 2:
            raise ValueError('unexpected Burdy frame mapping')
        tris = []
        us = [u for t in image['triangles'] for u, _ in t['uv_pairs']]
        vs = [v for t in image['triangles'] for _, v in t['uv_pairs']]
        u0, v0 = min(us), min(vs)
        if max(us) - u0 != .25 or max(vs) - v0 != .25 or v0 != .75:
            raise ValueError('frame UV rectangle is not one 16x16 cell of the sprite band')
        for t in image['triangles']:
            tris.append({'xy': [tuple(map(float, p)) for p in t['vertices_xy']], 'uv': [tuple(p) for p in t['uv_pairs']]})
        frames.append({'key': mapping['key_u32'], 'cell': int(u0 * 4), 'u0': u0, 'v0': v0, 'triangles': tris,
                       'local_bounds': image['local_bounds_xyxy']})
    # Cell c in VRAM orientation: VRAM row r = file row 63-r; the band v 0.75..1.0 = VRAM rows 48..63.
    cells = []
    for c in range(4):
        out = bytearray()
        for r in range(CELL):
            file_row = 63 - (48 + r)
            for x in range(c * CELL, (c + 1) * CELL):
                rr, gg, bb, aa = px[(file_row * 64 + x) * 4:(file_row * 64 + x) * 4 + 4]
                out += bytes((bb, gg, rr, 255 if aa else 0))   # BGRA; PS2 alpha is binary (0 / 1.0 after halving)
        cells.append(bytes(out))
    return {'psb': psb_path, 'psb_sha256': sha(psb), 'gxi': gxi_path, 'gxi_sha256': sha(gxi), 'frames': frames, 'cells': cells,
            'gxi_alpha_nonzero': info['alpha_nonzero_pixels']}


def courses():
    rows = []
    for c in cc.courses():
        payload = cc.read_ps2(c.ps2_xml)
        doc = br.parse_authored(payload, c.ps2_xml)
        if len(doc['managers']) != 1:
            raise ValueError(f'{c.name}: {len(doc["managers"])} BirdManagers')
        m = doc['managers'][0]
        props = {r.get('Name') for r in m['parameters']}
        for need in ('Milling MarkerList', 'Flight MarkerList', 'Min Fly Dist', 'Max Fly Dist', 'Min Mil Dist', 'Max Mil Dist', 'Rnd Fly', 'Rnd Mil'):
            if need not in props:
                raise ValueError(f'{c.name}: property {need} missing (config would write 0)')
        k = m['resolved_config']
        flight = m['lists']['flight']
        mill = m['lists']['milling']
        rows.append({'name': c.name, 'id': 'RaceTest/' + c.name, 'ps2_xml': c.ps2_xml, 'ps2_xml_sha256': sha(payload),
                     'pc_dx_path': c.pc_dx.relative_to(cc.PC_ROOT).as_posix(), 'retail_pc_dx_sha256': sha(c.pc_dx.read_bytes()),
                     'min_fly': k['Min Fly Dist'], 'max_fly': k['Max Fly Dist'], 'min_mil': k['Min Mil Dist'], 'max_mil': k['Max Mil Dist'],
                     'rnd_fly': k['Rnd Fly'], 'rnd_mil': k['Rnd Mil'], 'references': m['references'],
                     'flight_present': flight is not None, 'mill_present': mill is not None,
                     'flight_points': [list(x['position']) for x in flight] if flight else [],
                     'mill_points': len(mill) if mill else 0,
                     'bird_brown_authored': m['bird_brown_authored'], 'egg': m['egg']})
    return rows


def build(bank_data, rows):
    out = bytearray(HEADER.pack(MAGIC, VERSION, len(bank_data['frames']), len(rows), sum(len(r['flight_points']) for r in rows)))
    for cell in bank_data['cells']:
        out += cell
    for f in bank_data['frames']:
        for t in f['triangles']:
            out += FRAME.pack(f['cell'], *[v for p in t['xy'] for v in p], *[v for p in t['uv'] for v in p])
    first = 0
    for r in rows:
        out += COURSE.pack(fixed(r['id'], 48), fixed(r['pc_dx_path'], 64), bytes.fromhex(r['retail_pc_dx_sha256']),
                           r['min_fly'], r['max_fly'], r['min_mil'], r['max_mil'], r['rnd_fly'], r['rnd_mil'],
                           int(r['flight_present']), int(r['mill_present']), first, len(r['flight_points']))
        first += len(r['flight_points'])
    for r in rows:
        for p in r['flight_points']:
            out += POINT.pack(*p)
    return bytes(out)


def inventory(bank_data, rows, digest, coordinates):
    courses_out = []
    for r in rows:
        gate = r['flight_present'] and r['mill_present']
        row = {k: r[k] for k in ('name', 'id', 'ps2_xml', 'ps2_xml_sha256', 'pc_dx_path', 'retail_pc_dx_sha256', 'min_fly', 'max_fly',
                                 'min_mil', 'max_mil', 'rnd_fly', 'rnd_mil', 'references', 'flight_present', 'mill_present',
                                 'mill_points', 'bird_brown_authored', 'egg')}
        row.update(flight_points=len(r['flight_points']), update_gate='OPEN' if gate else 'CLOSED_NO_LOCAL_MILLLIST' if r['flight_present'] else 'CLOSED',
                   ps2_birds='flying birds spawn' if gate and r['flight_points'] else 'no birds (manager update never passes its list gate)')
        if coordinates:
            row['flight_xyz'] = r['flight_points']
        courses_out.append(row)
    return {'schema_version': 1, 'phase': 'COURSE-ALIVE2', 'asset': 'PS2Birds.ps2bird', 'asset_sha256': digest,
            'bank': {'psb': bank_data['psb'], 'psb_sha256': bank_data['psb_sha256'], 'gxi': bank_data['gxi'], 'gxi_sha256': bank_data['gxi_sha256'],
                     'frames': [{k: f[k] for k in ('key', 'cell', 'u0', 'v0', 'local_bounds')} for f in bank_data['frames']],
                     'gxi_alpha_nonzero_pixels': bank_data['gxi_alpha_nonzero']},
            'courses_total': len(rows), 'courses_with_open_gate': sum(1 for c in courses_out if c['update_gate'] == 'OPEN'),
            'courses': courses_out}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--inventory', type=Path)
    ap.add_argument('--output', type=Path, default=ASSET)
    a = ap.parse_args()
    bank_data, rows = bank(), courses()
    blob = build(bank_data, rows)
    if a.output.is_symlink() or a.output.parent.is_symlink():
        raise ValueError('private output link rejected')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(blob)
    digest = sha(blob)
    FULL.write_text(json.dumps(inventory(bank_data, rows, digest, True), indent=1), encoding='utf-8')
    if a.inventory:
        a.inventory.parent.mkdir(parents=True, exist_ok=True)
        a.inventory.write_text(json.dumps(inventory(bank_data, rows, digest, False), indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'asset': str(a.output), 'bytes': len(blob), 'sha256': digest, 'courses': len(rows),
                      'open_gate': sum(1 for r in rows if r['flight_present'] and r['mill_present'])}))


if __name__ == '__main__':
    main()
