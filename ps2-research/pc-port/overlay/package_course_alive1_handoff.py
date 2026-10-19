"""COURSE-ALIVE1 handoff archive (deterministic zip; never deploys).

    python ps2-research/pc-port/overlay/package_course_alive1_handoff.py

Output: ps2-research/pc-port/dist/course-alive1-handoff/
- course-alive1-handoff.zip: phase sources (portable controller, pilot, native seam, tests, tools), overlay lock and
  patches, docs/course-alive1, the touched course-port docs, the AMBIENT1 reference tool, build report, PS2-enabled DLL,
  provenance.json and SHA256SUMS.txt;
- course-alive1-runtime-kit.zip: d3d8.dll, PS2Grass/PS2SplineObjects.ps2spl, INI snippets, README, RUNTIME-AB
  (the PS2 course packages stay in research-output/course-port-36 and are not repacked here).
Private PS2 route coordinates are only inside the asset; the source archive has none.
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
ROOT = PORT.parents[1]
OUT = PORT / 'dist' / 'course-alive1-handoff'
KIT = PORT / 'dist' / 'course-alive1'
SOURCES = [
    'ps2-research/pc-port/renderer/ps2_spline_motion.hpp', 'ps2-research/pc-port/renderer/spline_objects.hpp',
    'ps2-research/pc-port/renderer/spline_objects.cpp', 'ps2-research/pc-port/renderer/spline_objects_native_integration.hpp',
    'ps2-research/pc-port/renderer/course_object_transaction.hpp', 'ps2-research/pc-port/renderer/ps2_config.hpp',
    'ps2-research/pc-port/renderer/ps2_port_extension.hpp', 'ps2-research/pc-port/renderer/ps2_port_extension.cpp',
    'ps2-research/pc-port/tests/spline_objects_tests.cpp', 'ps2-research/pc-port/tests/test_spline_objects.py',
    'ps2-research/pc-port/tests/test_build_roots.py', 'ps2-research/pc-port/tests/test_coverage_followup.py',
    'ps2-research/pc-port/tools/prepare_spline_objects.py', 'ps2-research/pc-port/tools/verify_spline_objects.py',
    'ps2-research/pc-port/overlay/baseline-lock.json', 'ps2-research/pc-port/overlay/patches/0001-renderer-integration.patch',
    'ps2-research/pc-port/overlay/patches/0002-interface-generator.patch', 'ps2-research/pc-port/overlay/package_course_alive1.py',
    'ps2-research/pc-port/overlay/package_course_alive1_handoff.py', 'ps2-research/pc-port/PS2Port.ini.example',
    'ps2-research/course-port/STATUS.md', 'ps2-research/course-port/AMBIENT-PROPS.md', 'ps2-research/course-port/build_objects.py',
    'ps2-research/tools/spline_runtime.py',
]
DOCS = 'ps2-research/pc-port/docs/course-alive1'
STAMP = (2026, 10, 20, 0, 0, 0)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def archive(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, members[name])
    return buf.getvalue()


def verify(blob, members):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if sorted(z.namelist()) != sorted(members) or any(z.read(n) != members[n] for n in members):
            raise ValueError('archive content mismatch')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    if git('status', '--porcelain', '--', 'ps2-research/pc-port/renderer', 'ps2-research/pc-port/tests', 'ps2-research/pc-port/overlay/patches'):
        raise ValueError('phase sources have uncommitted changes; commit first')
    report_bytes = (PORT / 'dist' / 'current' / 'build-report.json').read_bytes()
    report = json.loads(report_bytes)
    dll = (PORT / 'dist' / 'current' / 'ps2-enabled' / 'd3d8.dll').read_bytes()
    if sha(dll) != report['builds']['ps2-enabled']['dll_sha256']:
        raise ValueError('dist/current DLL does not match its build report')
    # The build report must describe exactly these sources.
    for rel, digest in report['ps2_source_sha256'].items():
        p = PORT / rel
        if p.exists() and p.suffix in ('.hpp', '.cpp') and sha(p.read_bytes()) != digest:
            raise ValueError(f'source changed after the build: {rel}')
    asset = (PORT / '.assets' / 'course' / 'PS2SplineObjects.ps2spl').read_bytes()
    verification = json.loads((ROOT / DOCS / 'verification.json').read_text(encoding='utf-8'))
    if verification['overall'] != 'PASS' or verification['asset_sha256'] != sha(asset):
        raise ValueError('verification is not PASS for this asset')
    members = {rel: (ROOT / rel).read_bytes() for rel in SOURCES}
    for p in sorted((ROOT / DOCS).rglob('*')):
        if p.is_file():
            members[p.relative_to(ROOT).as_posix()] = p.read_bytes()
    members['build-report.json'] = report_bytes
    members['d3d8.dll'] = dll
    members['provenance.json'] = json.dumps({
        'phase': 'COURSE-ALIVE1', 'head': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
        'build_head': report.get('current_head'), 'baseline_head': report.get('baseline_head'), 'renderer_tree': report.get('renderer_tree'),
        'ps2_enabled_dll_sha256': sha(dll), 'asset_sha256': sha(asset), 'verification': verification['overall'],
        'invocations_compared': verification['checks']['cpp_equals_ambient1_reference'].get('invocations_compared'),
        'runtime': 'CONFIRMED_BY_USER_GAME_TEST 2026-10-20 (kit courses FranceM, SpainS2, ItalyW2): loads, draws, PS2 speed',
        'feature_default': 'SplineObjects=0 (Stock)', 'route_coordinates_in_source_archive': False,
        'lock_adoption': 'probe_baseline_adoption: c357e8b (probe teleport, crash log)'}, indent=1).encode()
    members['SHA256SUMS.txt'] = ''.join(f'{sha(v)}  {k}\n' for k, v in sorted(members.items())).encode()
    handoff = archive(members)
    verify(handoff, members)
    if handoff != archive(members):
        raise ValueError('nondeterministic archive')
    kit = {'d3d8.dll': dll, 'PS2Grass/PS2SplineObjects.ps2spl': asset}
    for name in ('PS2Port.snippet.ini', 'ProbeTeleport.snippet.ini', 'README.md', 'RUNTIME-AB.md'):
        kit[name] = (KIT / name).read_bytes()
    kit['SHA256SUMS.txt'] = ''.join(f'{sha(v)}  {k}\n' for k, v in sorted(kit.items())).encode()
    kit_zip = archive(kit)
    verify(kit_zip, kit)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'course-alive1-handoff.zip').write_bytes(handoff)
    (OUT / 'course-alive1-runtime-kit.zip').write_bytes(kit_zip)
    (OUT / 'SHA256SUMS.txt').write_text(f'{sha(handoff)}  course-alive1-handoff.zip\n{sha(kit_zip)}  course-alive1-runtime-kit.zip\n', encoding='utf-8')
    print(json.dumps({'output': str(OUT), 'handoff_sha256': sha(handoff), 'handoff_bytes': len(handoff), 'members': len(members),
                      'runtime_kit_sha256': sha(kit_zip), 'runtime_kit_bytes': len(kit_zip), 'dll_sha256': sha(dll)}, indent=1))


if __name__ == '__main__':
    main()
