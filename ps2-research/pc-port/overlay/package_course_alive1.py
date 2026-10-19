"""COURSE-ALIVE1 in-game candidate: verified PS2-enabled DLL, the spline asset and three PS2 course packages
(FranceM airship; SpainS2 two triggered banking dinghies; ItalyW2 a dinghy that moves from the start). Never deploys.

    python ps2-research/pc-port/overlay/package_course_alive1.py

Output: ps2-research/pc-port/dist/course-alive1/ (ignored): d3d8.dll, PS2Grass/PS2SplineObjects.ps2spl,
courses/<Course>/{DataGx,DataScene}/..., PS2Port.snippet.ini, ProbeTeleport.snippet.ini, RUNTIME-AB.md, SHA256SUMS.txt.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import sys
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
ROOT = PORT.parents[1]
OUT = PORT / 'dist' / 'course-alive1'
PACKAGES = Path('D:/Game/Master Rallye/research-output/course-port-36')
COURSES = ('FranceM', 'SpainS2', 'ItalyW2')
sys.path.insert(0, str(ROOT / 'src'))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pinned_asset_sha():
    text = (PORT / 'renderer' / 'spline_objects.hpp').read_text(encoding='utf-8')
    return re.search(r'kSplineObjectsArtifactSha\[\]="([0-9a-f]{64})"', text).group(1)


def teleport_points(inventory):
    """Up to 9 points 25 units beside the race line where it passes closest to each route (Ctrl+Alt+1..9)."""
    from master_rallye.course_xml import parse_course_xml_bytes
    lines = ['[ProbeTeleport]', 'Enabled=1']
    n = 0
    for c in inventory['by_course']:
        if c['course'] not in COURSES:
            continue
        xml = parse_course_xml_bytes((PACKAGES / c['course'] / 'DataScene' / 'RaceTest' / f'{c["course"]}.xml').read_bytes(), 'pkg')
        rl = [m.position for m in xml.marker_list('RaceLine').markers]
        for o in c['objects']:
            i = min(range(len(rl)), key=lambda k: min(math.dist((rl[k][0], rl[k][2]), (q[0], q[2])) for q in o['points']))
            n += 1
            p = rl[i]
            lines.append(f'; {c["course"]} {o["egg"]} ({o["pc_model"]}): race line marker {i}, closest to its route')
            lines.append(f'Point{n}={p[0]:.1f},{p[1] + 1.5:.1f},{p[2]:.1f},0')
    return '\n'.join(lines) + '\n'


def main():
    report = json.loads((PORT / 'dist' / 'current' / 'build-report.json').read_text(encoding='utf-8'))
    dll = (PORT / 'dist' / 'current' / 'ps2-enabled' / 'd3d8.dll').read_bytes()
    if sha(dll) != report['builds']['ps2-enabled']['dll_sha256']:
        raise ValueError('dist/current DLL does not match its build report')
    asset = (PORT / '.assets' / 'course' / 'PS2SplineObjects.ps2spl').read_bytes()
    if sha(asset) != pinned_asset_sha():
        raise ValueError('spline asset does not match the pinned digest')
    verification = json.loads((PORT / 'docs' / 'course-alive1' / 'verification.json').read_text(encoding='utf-8'))
    if verification['overall'] != 'PASS' or verification['asset_sha256'] != sha(asset):
        raise ValueError('automatic verification is not PASS for this asset')
    inventory = json.loads((PORT / '.assets' / 'course' / 'spline-inventory-full.json').read_text(encoding='utf-8'))
    if OUT.exists():
        shutil.rmtree(OUT)
    files = {'d3d8.dll': dll, 'PS2Grass/PS2SplineObjects.ps2spl': asset,
             'RUNTIME-AB.md': (PORT / 'docs' / 'course-alive1' / 'runtime-ab.md').read_bytes(),
             'README.md': (PORT / 'docs' / 'course-alive1' / 'README.md').read_bytes(),
             'PS2Port.snippet.ini': b'; add to [PS2Port] in PS2Port.ini\nSplineObjects=1\nDiagnostics=1\n',
             'ProbeTeleport.snippet.ini': teleport_points(inventory).encode()}
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
    print(json.dumps({'output': str(OUT), 'dll_sha256': sha(dll), 'asset_sha256': sha(asset), 'courses': COURSES,
                      'files': len(files), 'head': report.get('current_head')}, indent=1))


if __name__ == '__main__':
    main()
