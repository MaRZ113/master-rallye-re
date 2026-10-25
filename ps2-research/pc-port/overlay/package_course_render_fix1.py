"""COURSE-RENDER-FIX1 in-game kit: the verified PS2-enabled DLL, ini snippets for the reflection A/B and the race-cycle run,
the analyzers, the 14-entry race-cycle plan and the recorded offline evidence. Never deploys, no game assets inside.

    python ps2-research/pc-port/overlay/package_course_render_fix1.py

Output: ps2-research/pc-port/dist/course-render-fix1/ (ignored): d3d8.dll, PS2Port.A-reflection-diag.ini,
PS2Port.B-race-cycles.ini, PS2Port.C-inframe-control.ini (snippets), tools/, race-cycle-plan.{md,json}, evidence/,
README.md, RUNTIME-AB.md, SHA256SUMS.txt.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
OUT = PORT / 'dist' / 'course-render-fix1'
DOCS = PORT / 'docs' / 'course-render-fix1'
TOOLS = ('analyze_race_lifecycle.py', 'race_cycle_plan.py', 'reflection_evidence.py')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    report = json.loads((PORT / 'dist' / 'current' / 'build-report.json').read_text(encoding='utf-8'))
    dll = (PORT / 'dist' / 'current' / 'ps2-enabled' / 'd3d8.dll').read_bytes()
    if sha(dll) != report['builds']['ps2-enabled']['dll_sha256']:
        raise ValueError('dist/current DLL does not match its build report')
    if OUT.exists():
        shutil.rmtree(OUT)
    a = ('; A: reflection check on SpainS2 (and the stock control Italy3). Add to [PS2Port] in PS2Port.ini.\n'
         'Reflection=4\nReflectionCoverage=1\nReflectionTargetPrecision=1\nReflectionDebug=2\n'
         'ReflectionCaptureTiming=auto\nReflectionStageDiag=1\nDiagnostics=1\n')
    b = ('; B: 14 race cycles (race-cycle-plan.md). Add to [PS2Port] in PS2Port.ini, keep your own effect keys.\n'
         'Reflection=4\nReflectionDebug=0\nReflectionCaptureTiming=auto\nReflectionStageDiag=0\nDiagnostics=1\nPS2PerfTiming=0\n')
    c = ('; C: control = the behaviour of every earlier build (capture at the first car draw, no probe, no readback).\n'
         'ReflectionCaptureTiming=inframe\nReflectionStageDiag=0\n')
    files = {
        'd3d8.dll': dll,
        'PS2Port.A-reflection-diag.ini': a.encode(), 'PS2Port.B-race-cycles.ini': b.encode(), 'PS2Port.C-inframe-control.ini': c.encode(),
        'README.md': (DOCS / 'README.md').read_bytes(), 'RUNTIME-AB.md': (DOCS / 'runtime-ab.md').read_bytes(),
        'race-cycle-plan.md': (DOCS / 'race-cycle-plan.md').read_bytes(), 'race-cycle-plan.json': (DOCS / 'race-cycle-plan.json').read_bytes(),
    }
    for name in TOOLS:
        files['tools/' + name] = (PORT / 'tools' / name).read_bytes()
    for p in sorted((DOCS / 'evidence').iterdir()):
        files['evidence/' + p.name] = p.read_bytes()
    for name, data in files.items():
        target = OUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (OUT / 'SHA256SUMS.txt').write_text(''.join(f'{sha(d)}  {n}\n' for n, d in sorted(files.items())), encoding='utf-8')
    print(json.dumps({'output': str(OUT), 'dll_sha256': sha(dll), 'files': len(files), 'head': report.get('current_head')}, indent=1))


if __name__ == '__main__':
    main()
