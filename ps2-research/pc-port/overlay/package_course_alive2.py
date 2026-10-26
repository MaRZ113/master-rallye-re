"""COURSE-ALIVE2 in-game kit: verified PS2-enabled DLL, the bird asset and three PS2 course packages with an open PS2
bird gate (France1, SpainS2, ItalyS4). Never deploys.

    python ps2-research/pc-port/overlay/package_course_alive2.py

Output: ps2-research/pc-port/dist/course-alive2/ (ignored): d3d8.dll, PS2Grass/PS2Birds.ps2bird, courses/<Course>/...,
PS2Port.snippet.ini, ProbeTeleport.snippet.ini, README.md, RUNTIME-AB.md, SHA256SUMS.txt, course-alive2-handoff.zip
(sources, patches, lock, docs, generators, tests, build report, DLL).
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
ROOT = PORT.parents[1]
OUT = PORT / 'dist' / 'course-alive2'
PACKAGES = Path('D:/Game/Master Rallye/research-output/course-port-36')
COURSES = ('France1', 'SpainS2', 'ItalyS4')
STAMP = (2026, 10, 26, 0, 0, 0)
sys.path.insert(0, str(ROOT / 'src'))
SOURCES = ['renderer/ps2_birds.hpp', 'renderer/ps2_birds_pilot.hpp', 'renderer/ps2_birds_pilot.cpp', 'renderer/ps2_birds_native_integration.hpp',
           'renderer/ps2_diag.hpp', 'renderer/ps2_config.hpp', 'renderer/ps2_port_extension.hpp', 'renderer/ps2_port_extension.cpp',
           'tests/ps2_birds_tests.cpp', 'tests/test_ps2_birds.py', 'tools/prepare_ps2_birds.py', 'tools/ps2_bird_model.py',
           'tools/verify_ps2_birds.py', 'overlay/baseline-lock.json', 'overlay/patches/0001-renderer-integration.patch',
           'overlay/patches/0002-interface-generator.patch', 'overlay/package_course_alive2.py', 'PS2Port.ini.example']


def sha(b):
    return hashlib.sha256(b).hexdigest()


def archive(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, STAMP); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o644 << 16
            z.writestr(info, members[name])
    data = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if any(z.read(n) != members[n] for n in members):
            raise ValueError('archive mismatch')
    return data


def teleport_points(inventory):
    from master_rallye.course_xml import parse_course_xml_bytes
    lines = ['[ProbeTeleport]', 'Enabled=1']
    n = 0
    for c in inventory['courses']:
        if c['name'] not in COURSES:
            continue
        xml = parse_course_xml_bytes((PACKAGES / c['name'] / 'DataScene' / 'RaceTest' / f'{c["name"]}.xml').read_bytes(), 'pkg')
        rl = [m.position for m in xml.marker_list('RaceLine').markers]
        pts = c['flight_xyz']
        def d(p):
            return min(math.dist((p[0], p[2]), (q[0], q[2])) for q in pts)
        cand = [i for i, p in enumerate(rl) if c['min_fly'] + 50 < d(p) < 600]
        picks = [cand[len(cand) * k // 3] for k in range(3)] if len(cand) >= 3 else cand
        for i in picks:
            n += 1
            p = rl[i]
            lines.append(f'; {c["name"]}: race line marker {i}, {d(p):.0f} units from the nearest FlightList origin')
            lines.append(f'Point{n}={p[0]:.1f},{p[1] + 1.5:.1f},{p[2]:.1f},0')
    return '\n'.join(lines[:2 + 2 * 9]) + '\n'


def main():
    if subprocess.run(['git', 'status', '--porcelain', '--', 'ps2-research/pc-port/renderer', 'ps2-research/pc-port/overlay/patches'],
                      cwd=ROOT, capture_output=True, text=True).stdout.strip():
        raise ValueError('commit the phase sources first')
    report_bytes = (PORT / 'dist' / 'current' / 'build-report.json').read_bytes()
    report = json.loads(report_bytes)
    dll = (PORT / 'dist' / 'current' / 'ps2-enabled' / 'd3d8.dll').read_bytes()
    if sha(dll) != report['builds']['ps2-enabled']['dll_sha256']:
        raise ValueError('dist/current DLL does not match its build report')
    for rel, digest in report['ps2_source_sha256'].items():
        p = PORT / rel
        if p.exists() and p.suffix in ('.hpp', '.cpp') and sha(p.read_bytes()) != digest:
            raise ValueError(f'source changed after the build: {rel}')
    asset = (PORT / '.assets' / 'course' / 'PS2Birds.ps2bird').read_bytes()
    pinned = re.search(r'kPS2BirdsArtifactSha\[\]="([0-9a-f]{64})"', (PORT / 'renderer' / 'ps2_birds_pilot.hpp').read_text(encoding='utf-8')).group(1)
    verification = json.loads((PORT / 'docs' / 'course-alive2' / 'verification.json').read_text(encoding='utf-8'))
    if sha(asset) != pinned or verification['overall'] != 'PASS' or verification['asset_sha256'] != pinned:
        raise ValueError('asset / verification not PASS')
    inventory = json.loads((PORT / '.assets' / 'course' / 'birds-inventory-full.json').read_text(encoding='utf-8'))
    if OUT.exists():
        shutil.rmtree(OUT)
    files = {'d3d8.dll': dll, 'PS2Grass/PS2Birds.ps2bird': asset,
             'README.md': (PORT / 'docs/course-alive2/README.md').read_bytes(), 'RUNTIME-AB.md': (PORT / 'docs/course-alive2/runtime-ab.md').read_bytes(),
             'PS2Port.snippet.ini': b'; add to [PS2Port] in PS2Port.ini\nPS2Birds=1\nDiagnostics=1\n',
             'ProbeTeleport.snippet.ini': teleport_points(inventory).encode()}
    for course in COURSES:
        src = PACKAGES / course
        for p in sorted(src.rglob('*')):
            if p.is_file() and p.relative_to(src).parts[0] in ('DataGx', 'DataScene'):
                files[f'courses/{course}/' + p.relative_to(src).as_posix()] = p.read_bytes()
    members = {'ps2-research/pc-port/' + rel: (PORT / rel).read_bytes() for rel in SOURCES}
    for p in sorted((PORT / 'docs' / 'course-alive2').glob('*')):
        members['ps2-research/pc-port/docs/course-alive2/' + p.name] = p.read_bytes()
    for rel in ('ps2-research/tools/bird_runtime.py', 'ps2-research/course-port/STATUS.md', 'ps2-research/course-port/AMBIENT-PROPS.md'):
        members[rel] = (ROOT / rel).read_bytes()
    members['build-report.json'] = report_bytes
    members['d3d8.dll'] = dll
    members['provenance.json'] = json.dumps({'phase': 'COURSE-ALIVE2', 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                                             'ps2_enabled_dll_sha256': sha(dll), 'asset_sha256': pinned, 'verification': verification['overall'],
                                             'route_or_texture_data_in_source_archive': False, 'runtime': 'PENDING_USER'}, indent=1).encode()
    members['SHA256SUMS.txt'] = ''.join(f'{sha(v)}  {k}\n' for k, v in sorted(members.items())).encode()
    files['course-alive2-handoff.zip'] = archive(members)
    for name, data in files.items():
        t = OUT / name; t.parent.mkdir(parents=True, exist_ok=True); t.write_bytes(data)
    (OUT / 'SHA256SUMS.txt').write_text(''.join(f'{sha(d)}  {n}\n' for n, d in sorted(files.items())), encoding='utf-8')
    print(json.dumps({'output': str(OUT), 'dll_sha256': sha(dll), 'asset_sha256': pinned, 'handoff_sha256': sha(files['course-alive2-handoff.zip']),
                      'files': len(files), 'courses': COURSES}, indent=1))


if __name__ == '__main__':
    main()
