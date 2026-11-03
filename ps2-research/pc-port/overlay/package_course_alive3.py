"""COURSE-ALIVE3 in-game kit: verified PS2-enabled DLL, the rigid prop asset and the PS2 course packages of the prop
courses. Never deploys.

    python ps2-research/pc-port/overlay/package_course_alive3.py [--courses ItalyS1 Turkey1 ...]

Output: ps2-research/pc-port/dist/course-alive3/ (ignored): d3d8.dll, PS2Grass/PS2RigidProps.ps2rgd,
courses/<Course>/..., PS2Port.snippet.ini, README.md, RUNTIME-AB.md, SHA256SUMS.txt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
OUT = PORT / 'dist' / 'course-alive3'
PACKAGES = Path('D:/Game/Master Rallye/research-output/course-port-36')
PROP_COURSES = ('ItalyS1', 'Italy2', 'ItalyS4', 'ItalyW1', 'ItalyW2', 'Turkey1', 'Turkey3', 'TurkeyM', 'TurkeyS2Flip')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--courses', nargs='*', default=list(PROP_COURSES))
    a = ap.parse_args()
    report = json.loads((PORT / 'dist' / 'current' / 'build-report.json').read_bytes())
    dll = (PORT / 'dist' / 'current' / 'ps2-enabled' / 'd3d8.dll').read_bytes()
    if sha(dll) != report['builds']['ps2-enabled']['dll_sha256']:
        raise ValueError('dist/current DLL does not match its build report')
    for rel, digest in report['ps2_source_sha256'].items():
        p = PORT / rel
        if p.exists() and p.suffix in ('.hpp', '.cpp') and sha(p.read_bytes()) != digest:
            raise ValueError(f'source changed after the build: {rel}')
    if 'renderer/rigid_props.cpp' not in report['ps2_source_sha256']:
        raise ValueError('the published build does not contain COURSE-ALIVE3')
    asset = (PORT / '.assets' / 'course' / 'PS2RigidProps.ps2rgd').read_bytes()
    pinned = re.search(r'kRigidPropsArtifactSha\[\]="([0-9a-f]{64})"', (PORT / 'renderer' / 'rigid_props.hpp').read_text(encoding='utf-8')).group(1)
    if sha(asset) != pinned:
        raise ValueError('asset does not match the pinned digest')
    if OUT.exists():
        shutil.rmtree(OUT)
    files = {'d3d8.dll': dll, 'PS2Grass/PS2RigidProps.ps2rgd': asset,
             'README.md': (PORT / 'docs/course-alive3/README.md').read_bytes(),
             'RUNTIME-AB.md': (PORT / 'docs/course-alive3/runtime-ab.md').read_bytes(),
             'PS2Port.snippet.ini': b'; add to [PS2Port] in PS2Port.ini\nRigidProps=1\nRigidPropsDiagnostics=1\nDiagnostics=1\n'}
    for course in a.courses:
        if course not in PROP_COURSES:
            raise ValueError(f'{course} has no PS2 rigid props')
        src = PACKAGES / course
        for p in sorted(src.rglob('*')):
            if p.is_file() and p.relative_to(src).parts[0] in ('DataGx', 'DataScene'):
                files[f'courses/{course}/' + p.relative_to(src).as_posix()] = p.read_bytes()
    for name, data in files.items():
        t = OUT / name
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(data)
    (OUT / 'SHA256SUMS.txt').write_text(''.join(f'{sha(d)}  {n}\n' for n, d in sorted(files.items())), encoding='utf-8')
    print(json.dumps({'out': str(OUT), 'dll_sha256': sha(dll), 'asset_sha256': pinned, 'courses': a.courses, 'files': len(files)}))


if __name__ == '__main__':
    main()
