"""COLLISION-DEBUG1: CourseCollision.mrcoll, the collision surface of every retail course, for CollisionDebug=1.

The retail course DX files live inside Data.sma, which the proxy does not read, so their collision surface is extracted
here. Loose course DX files (converted PS2 courses, new courses) are parsed by the proxy itself (collision_debug.hpp).

Source: the tag1400 section of each course DX, delimited by the loader-guided bounded parsers of R5T-F.2.1
(render prefix -> tag100 tree -> tag1339 -> tag1400 -> tag1500, `tools/r5t_f21_prepare.split_tag100_suffix`).
Record meaning (COLLISION-DEBUG1, checked here on every record): 9 floats = triangle v0,v1,v2; uint32 = index into the
tag1400 string table (material, "$surfacetype(<type>) ..."); 4 floats = plane n,d with |n| = 1, n.v + d = 0 for the three
vertices and n along cross(v1-v0, v2-v0). The race -> course mapping is the landscape "course\\<dir>\\<name>" of each
retail race XML (DataScene/RaceTest/*.xml), the same rule the proxy applies to a loose race XML.

Layout (little endian), decoded by colldebug::decode_asset_index / decode_asset_mesh:
  "MRCOLL01" u32 version=1 u32 entries
  entry[160]: race_id[48] dx_path[64] dx_sha256[32] u32 offset u32 size u32 reserved[2]
  blob: f32 cell u32 dim0 u32 dim1 f32 min[3] f32 max[3]
        u32 materials {u16 length, bytes} u32 vertices {f32 xyz} u32 triangles {u32 i0,i1,i2} {u16 material} {f32 plane[4]}
Vertices are welded bit-exactly in first-use order (the proxy's order for loose files).

    python ps2-research/pc-port/tools/prepare_collision_debug.py [--retail <Data.sma_unpacked>] [--out <asset>]
        [--verify <collision_debug_tests.exe>] [--loose-root <game folder>]

--verify runs the C++ contract binary on every retail DX (raw-byte tag1400 search) and on the written asset, and
requires the same digest as this loader-guided parse for every course; --loose-root adds the loose course DX of a game
folder (C++ only, reported).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
REPO = PORT.parents[1]
for item in (REPO, REPO / 'src', REPO / 'tools'):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

import r5t_f21_prepare as f21  # noqa: E402

RETAIL = REPO.parent / 'corpora/retail/Data.sma_unpacked'
OUT = PORT / '.assets/debug/CourseCollision.mrcoll'
REPORT = PORT / 'docs/collision-debug1/corpus.json'
LANDSCAPE = re.compile(rb'(?<![A-Za-z])course\\([A-Za-z0-9_\-]+)\\([A-Za-z0-9_\-]+)')
SURFACE = re.compile(rb'\$surfacetype\(([^)]*)\)')


def ci_path(root: Path, rel: str) -> Path | None:
    cur = root
    for part in rel.split('/'):
        hits = [p for p in cur.iterdir() if p.name.lower() == part.lower()] if cur.is_dir() else []
        if len(hits) != 1:
            return None
        cur = hits[0]
    return cur


def plane_ok(v, n) -> bool:
    if not all(math.isfinite(x) for x in (*v, *n)):
        return False
    if abs(math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) - 1.0) > 1e-3:
        return False
    for k in range(3):
        r = n[0] * v[k * 3] + n[1] * v[k * 3 + 1] + n[2] * v[k * 3 + 2] + n[3]
        if not abs(r) <= 0.05 + 1e-5 * abs(n[3]):
            return False
    return True


def winding(v, n) -> tuple[bool, float]:
    """(n along cross(v1-v0, v2-v0), doubled triangle area)."""
    a = [v[3] - v[0], v[4] - v[1], v[5] - v[2]]
    b = [v[6] - v[0], v[7] - v[1], v[8] - v[2]]
    c = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    return c[0] * n[0] + c[1] * n[1] + c[2] * n[2] > 0, math.sqrt(c[0] ** 2 + c[1] ** 2 + c[2] ** 2)


def f32(x: float) -> float:
    return struct.unpack('<f', struct.pack('<f', x))[0]


def course_mesh(path: Path) -> dict:
    parts = f21._parse_dx_parts(path)
    t = parts.tag1400
    records = t.records
    corners, planes, mats, bad, reversed_, degenerate = [], [], [], 0, [], []
    for r in records:
        v = [f32(x) for x in r.float_prefix]
        n = [f32(x) for x in r.float_suffix]
        along, area2 = winding(v, n)
        if all(math.isnan(x) for x in n) and area2 <= 1e-3:
            degenerate.append({'record': len(corners), 'doubled_area': area2})
        elif r.string_ref_index >= len(t.strings) or not plane_ok(v, n):
            bad += 1
        elif not along:
            reversed_.append({'record': len(corners), 'doubled_area': area2})
        corners.append(v)
        planes.append(n)
        mats.append(r.string_ref_index)
    weld, positions, indices = {}, [], []
    for v in corners:
        for k in range(3):
            key = struct.pack('<3f', *v[k * 3:k * 3 + 3])
            if key not in weld:
                weld[key] = len(positions)
                positions.append(key)
            indices.append(weld[key])
    names = [s.raw_bytes for s in t.strings]
    return {'path': path, 'raw': parts.raw, 'tag1400_offset': parts.ranges['U'][0], 'cell': t.scalar,
            'dims': (t.dimension_0, t.dimension_1), 'min': t.vector_a, 'max': t.vector_b, 'materials': names,
            'positions': positions, 'indices': indices, 'planes': planes, 'material': mats, 'corners': corners,
            'bad_records': bad, 'reversed': reversed_, 'degenerate': degenerate}


QNAN = struct.pack('<I', 0x7fc00000)


def pack_plane(n) -> bytes:
    """Plane floats; NaN as the canonical quiet NaN 0x7fc00000 (asset and digests)."""
    return b''.join(QNAN if math.isnan(x) else struct.pack('<f', x) for x in n)


def digest(m: dict) -> str:
    """Same bytes as digest() of tests/collision_debug_tests.cpp."""
    out = bytearray()
    for t, v in enumerate(m['corners']):
        out += struct.pack('<9f', *v) + pack_plane(m['planes'][t]) + struct.pack('<H', m['material'][t])
    for s in m['materials']:
        out += struct.pack('<I', len(s)) + s
    return hashlib.sha256(out).hexdigest()


def blob(m: dict) -> bytes:
    out = bytearray(struct.pack('<f2I3f3f', m['cell'], *m['dims'], *m['min'], *m['max']))
    out += struct.pack('<I', len(m['materials']))
    for s in m['materials']:
        out += struct.pack('<H', len(s)) + s
    out += struct.pack('<I', len(m['positions'])) + b''.join(m['positions'])
    out += struct.pack('<I', len(m['material']))
    out += struct.pack(f'<{len(m["indices"])}I', *m['indices'])
    out += struct.pack(f'<{len(m["material"])}H', *m['material'])
    out += b''.join(pack_plane(p) for p in m['planes'])
    return bytes(out)


def fixed(text: str, size: int) -> bytes:
    raw = text.encode('ascii')
    if len(raw) >= size:
        raise SystemExit(f'{text!r} does not fit {size} bytes')
    return raw + b'\0' * (size - len(raw))


def races(retail: Path) -> list[tuple[str, str]]:
    out = []
    for xml in sorted((retail / 'DataScene/RaceTest').glob('*.xml')):
        m = LANDSCAPE.search(xml.read_bytes())
        if not m:
            continue
        rel = f'DataGx/Course/{m.group(1).decode()}/{m.group(2).decode()}.dx'
        if ci_path(retail, rel):
            out.append((f'RaceTest/{xml.stem}', rel))
    return out


def surface_counts(m: dict) -> dict:
    kinds = []
    for s in m['materials']:
        hit = SURFACE.search(s)
        kinds.append(hit.group(1).decode('ascii', 'replace').lower() if hit else 'none')
    c = Counter(kinds[i] for i in m['material'])
    return dict(sorted(c.items()))


def run_cpp(exe: Path, args: list[str]) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'dump.jsonl'
        r = subprocess.run([str(exe), *args, str(out)], capture_output=True, text=True)
        rows = [json.loads(line) for line in out.read_text().splitlines()] if out.exists() else []
        if r.returncode not in (0, 1):
            raise SystemExit(f'{exe} {args} failed: {r.returncode} {r.stderr}')
        return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--retail', type=Path, default=RETAIL)
    ap.add_argument('--out', type=Path, default=OUT)
    ap.add_argument('--report', type=Path, default=REPORT)
    ap.add_argument('--verify', type=Path)
    ap.add_argument('--loose-root', type=Path)
    a = ap.parse_args()

    mapping = races(a.retail)
    meshes: dict[str, dict] = {}
    for _, rel in mapping:
        key = rel.lower()
        if key not in meshes:
            meshes[key] = course_mesh(ci_path(a.retail, rel))
    bad = {k: m['bad_records'] for k, m in meshes.items() if m['bad_records']}
    if bad:
        raise SystemExit(f'records outside the triangle contract: {bad}')

    blobs: dict[str, tuple[int, int]] = {}
    table = 16 + 160 * len(mapping)
    data = bytearray()
    for key, m in meshes.items():
        b = blob(m)
        blobs[key] = (table + len(data), len(b))
        data += b
    head = bytearray(b'MRCOLL01' + struct.pack('<2I', 1, len(mapping)))
    for race, rel in mapping:
        m = meshes[rel.lower()]
        off, size = blobs[rel.lower()]
        head += fixed(race, 48) + fixed(rel, 64) + hashlib.sha256(m['raw']).digest() + struct.pack('<4I', off, size, 0, 0)
    asset = bytes(head + data)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(asset)
    asset_sha = hashlib.sha256(asset).hexdigest()

    rows = []
    for race, rel in mapping:
        m = meshes[rel.lower()]
        rows.append({'race_id': race, 'dx_path': rel, 'dx_sha256': hashlib.sha256(m['raw']).hexdigest(),
                     'tag1400_offset': m['tag1400_offset'], 'triangles': len(m['material']),
                     'vertices': len(m['positions']), 'materials': len(m['materials']),
                     'cell': m['cell'], 'grid': list(m['dims']), 'surface_triangles': surface_counts(m),
                     'reversed_winding_records': m['reversed'], 'degenerate_nan_plane_records': m['degenerate'],
                     'digest': digest(m)})
    reversed_total = sum(len(m['reversed']) for m in meshes.values())
    degenerate_total = sum(len(m['degenerate']) for m in meshes.values())
    report = {'schema': 'collision-debug1-corpus-v1', 'asset': a.out.name, 'asset_sha256': asset_sha,
              'asset_bytes': len(asset), 'races': len(mapping), 'course_dx': len(meshes),
              'triangles_total': sum(len(m['material']) for m in meshes.values()),
              'record_contract': 'every record: |n|=1, n.v+d=0 (<=0.05) and material index in range, or a degenerate triangle '
                                 f'(doubled area <= 1e-3) with an all-NaN plane ({degenerate_total} records, not drawn)',
              'winding': f'n along cross(v1-v0,v2-v0) except {reversed_total} records (listed per course)',
              'courses': rows}

    if a.verify:
        cpp = {}
        for key, m in meshes.items():
            for row in run_cpp(a.verify, ['--dump', m['path'].as_posix()]):
                cpp[key] = row
        mismatch = [k for k, m in meshes.items()
                    if cpp.get(k, {}).get('digest') != digest(m) or cpp[k]['tag1400_offset'] != m['tag1400_offset']]
        asset_rows = run_cpp(a.verify, ['--dump-asset', a.out.as_posix()])
        by_race = {r['race_id']: r for r in asset_rows}
        asset_mismatch = [race for race, rel in mapping if by_race.get(race, {}).get('digest') != digest(meshes[rel.lower()])]
        report['verify'] = {'cpp_raw_search_equal': len(meshes) - len(mismatch), 'cpp_raw_search_mismatch': mismatch,
                            'cpp_asset_equal': len(mapping) - len(asset_mismatch), 'cpp_asset_mismatch': asset_mismatch}
        if a.loose_root:
            loose = []
            for dx in sorted((a.loose_root / 'DataGx/Course').glob('*/*.dx')):
                for row in run_cpp(a.verify, ['--dump', dx.as_posix()]):
                    row['path'] = dx.relative_to(a.loose_root).as_posix()
                    loose.append(row)
            report['verify']['loose_course_dx'] = loose
        if mismatch or asset_mismatch:
            print(json.dumps(report['verify'], indent=2))
            raise SystemExit('C++ parse differs from the loader-guided parse')

    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'{a.out} {len(asset)} bytes sha256 {asset_sha}; {len(mapping)} races, {len(meshes)} course DX, '
          f'{report["triangles_total"]} triangles')
    if 'verify' in report:
        v = report['verify']
        print(f'verify: raw search {v["cpp_raw_search_equal"]}/{len(meshes)}, asset {v["cpp_asset_equal"]}/{len(mapping)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
