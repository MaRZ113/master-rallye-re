"""COURSE-WATER1 in-game A/B kit: verified PS2-enabled DLL, the PS2 water asset (and the COURSE-ALIVE1 spline asset for the
France1 boats) and three PS2 course packages: Turkey3 (PS2-only puddles, river ford), Turkey2 (river water plus PS2 extra
puddles), France1 (puddles, water, two waterfalls, two moving dinghies). Never deploys.

    python ps2-research/pc-port/overlay/package_course_water1.py

Output: ps2-research/pc-port/dist/course-water1/ (ignored): d3d8.dll, PS2Grass/PS2Water.ps2wtr, PS2Grass/PS2SplineObjects.ps2spl,
courses/<Course>/{DataGx,DataScene}/..., PS2Port.A-stock-water.ini, PS2Port.B-ps2-water.ini (snippets), ProbeTeleport.snippet.ini,
RUNTIME-AB.md, README.md, SHA256SUMS.txt.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import struct
import sys
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
ROOT = PORT.parents[1]
OUT = PORT / 'dist' / 'course-water1'
PACKAGES = Path('D:/Game/Master Rallye/research-output/course-port-36')
COURSES = ('Turkey3', 'Turkey2', 'France1')
sys.path.insert(0, str(ROOT / 'src'))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pinned(header, name):
    text = (PORT / 'renderer' / header).read_text(encoding='utf-8')
    return re.search(name + r'\[\]="([0-9a-f]{64})"', text).group(1)


def water_points(asset):
    """Race-line markers closest to the largest water surface of each mode per kit course (Ctrl+Alt+1..9)."""
    from master_rallye.course_xml import parse_course_xml_bytes
    magic, version, ntex, ncourse, nkey, npart, nvert, _ = struct.unpack_from('<8s7I', asset, 0)
    at = 36
    for _ in range(ntex):
        w, h = struct.unpack_from('<2I', asset, at)
        at += 8 + 4 * w * h
    courses = []
    for i in range(ncourse):
        cid = asset[at:at + 48].split(b'\0')[0].decode()
        first, count, _ = struct.unpack_from('<3I', asset, at + 48)
        courses.append((cid, first, count))
        at += 60
    keys = [struct.unpack_from('<2I32s2I', asset, at + 48 * i) for i in range(nkey)]
    at += 48 * nkey
    parts = [struct.unpack_from('<6If', asset, at + 28 * i) for i in range(npart)]
    at += 28 * npart
    pos = lambda v: struct.unpack_from('<3f', asset, at + 52 * v)  # noqa: E731
    lines, n = ['[ProbeTeleport]', 'Enabled=1'], 0
    for cid, first, count in courses:
        name = cid.split('/')[-1]
        if name not in COURSES:
            continue
        xml = parse_course_xml_bytes((PACKAGES / name / 'DataScene' / 'RaceTest' / f'{name}.xml').read_bytes(), 'pkg')
        rl = [m.position for m in xml.marker_list('RaceLine').markers]
        best = {}
        for k in keys[first:first + count]:
            if k[1] != 1:
                continue
            for pi in range(k[3], k[3] + k[4]):
                mode, _, _, _, fv, cv, _ = parts[pi]
                if cv > best.get(mode, (0, None))[0]:
                    c = [sum(pos(v)[j] for v in range(fv, fv + cv)) / cv for j in range(3)]
                    best[mode] = (cv, c)
        for mode, (_, c) in sorted(best.items()):
            i = min(range(len(rl)), key=lambda q: math.dist((rl[q][0], rl[q][2]), (c[0], c[2])))
            n += 1
            p = rl[i]
            label = {9: 'puddle', 10: 'water', 19: 'waterfall'}[mode]
            lines.append(f'; {name}: race line marker {i}, closest to the largest PS2 {label} surface '
                         f'({math.dist((p[0], p[2]), (c[0], c[2])):.0f} units away)')
            lines.append(f'Point{n}={p[0]:.1f},{p[1] + 1.5:.1f},{p[2]:.1f},0')
    return '\n'.join(lines) + '\n'


def main():
    report = json.loads((PORT / 'dist' / 'current' / 'build-report.json').read_text(encoding='utf-8'))
    dll = (PORT / 'dist' / 'current' / 'ps2-enabled' / 'd3d8.dll').read_bytes()
    if sha(dll) != report['builds']['ps2-enabled']['dll_sha256']:
        raise ValueError('dist/current DLL does not match its build report')
    water = (PORT / '.assets' / 'course' / 'PS2Water.ps2wtr').read_bytes()
    if sha(water) != pinned('ps2_water_pilot.hpp', 'kPS2WaterArtifactSha'):
        raise ValueError('water asset does not match the pinned digest')
    splines = (PORT / '.assets' / 'course' / 'PS2SplineObjects.ps2spl').read_bytes()
    if sha(splines) != pinned('spline_objects.hpp', 'kSplineObjectsArtifactSha'):
        raise ValueError('spline asset does not match the pinned digest')
    if OUT.exists():
        shutil.rmtree(OUT)
    common = 'SplineObjects=1\nGroundDetail=0\nCourseObjects=0\nDiagnostics=1\n'
    files = {'d3d8.dll': dll, 'PS2Grass/PS2Water.ps2wtr': water, 'PS2Grass/PS2SplineObjects.ps2spl': splines,
             'RUNTIME-AB.md': (PORT / 'docs' / 'course-water1' / 'runtime-ab.md').read_bytes(),
             'README.md': (PORT / 'docs' / 'course-water1' / 'README.md').read_bytes(),
             'PS2Port.A-stock-water.ini': ('; A: PC water (Stock). Add to [PS2Port] in PS2Port.ini.\nPS2Water=0\n' + common).encode(),
             'PS2Port.B-ps2-water.ini': ('; B: PS2 water. Add to [PS2Port] in PS2Port.ini.\nPS2Water=1\n' + common).encode(),
             'ProbeTeleport.snippet.ini': water_points(water).encode()}
    for course in COURSES:
        src = PACKAGES / course
        for p in sorted(src.rglob('*')):
            if p.is_file() and p.relative_to(src).parts[0] in ('DataGx', 'DataScene'):
                files[f'courses/{course}/' + p.relative_to(src).as_posix()] = p.read_bytes()
    for name, data in files.items():
        target = OUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    sums = ''.join(f'{sha(d)}  {n}\n' for n, d in sorted(files.items()))
    (OUT / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8')
    print(json.dumps({'output': str(OUT), 'dll_sha256': sha(dll), 'water_asset_sha256': sha(water), 'courses': COURSES,
                      'files': len(files), 'head': report.get('current_head')}, indent=1))


if __name__ == '__main__':
    main()
