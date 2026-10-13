#!/usr/bin/env python3
"""Verified reflection iteration handoff; original images/meshes stay private."""
import importlib.util
import json
from pathlib import Path

PORT=Path(__file__).resolve().parents[1]
ROOT=PORT.parents[1]
DOCS=PORT/'docs/reflection-port1.1'
OUTPUT=PORT/'dist/PS2-REFLECTION-PORT1.1-handoff.zip'
spec=importlib.util.spec_from_file_location('verified_pack',PORT/'overlay/package_reflection_handoff.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)

def main():
    report=json.loads(pack.read_required(DOCS/'build-report.json'))
    lock=json.loads(pack.read_required(PORT/'overlay/baseline-lock.json'))
    sources=pack.verify_build_inputs(report,lock)
    for name in ('final-report.md','validation.md','command-log.md','runtime-ab.md','runtime-audit.md','source-contract.md','classifier-provenance.json','body-panel-components.json'):
        pack.read_required(DOCS/name)
    paths=list(sources.values())
    paths += [PORT/name for name in ('.gitignore','README.md','PS2Port.ini.example','overlay/README.md',
        'overlay/build_overlay.py','overlay/baseline-lock.json','overlay/package_reflection_handoff.py',
        'overlay/package_reflection11_handoff.py','overlay/patches/0001-renderer-integration.patch',
        'overlay/patches/0002-interface-generator.patch','tools/prepare_reflection_pilot.py','tools/prepare_course_objects.py')]
    paths += [p for p in DOCS.rglob('*') if p.is_file() and p.suffix in {'.md','.json'}]
    # Small witnesses required by the retained focused source/integration tests.
    paths += [PORT/'docs/reflection-port1/material-source-contract.json',PORT/'docs/course-objects1/source-contract.json']
    paths += [ROOT/'ps2-research/tools'/name for name in pack.RESEARCH_TOOLS]
    paths += [ROOT/'ps2-research/refl1'/name for name in ('environment-target-lifecycle.md','environment-coordinate-math.md','body-reflection.md','render-contract.json','pc-comparison.md','provenance.json')]
    members={pack.relative_name(p):pack.read_required(p) for p in sorted(set(paths))}
    for variant in ('baseline','ps2-enabled'): members[f'artifacts/{variant}/d3d8.dll']=pack.verified_dll(report,variant)
    members['HANDOFF.md']=f'''# PS2-REFLECTION-PORT1.1 — bounded mixed framebuffer pilot

Read ps2-research/pc-port/docs/reflection-port1.1/final-report.md and runtime-ab.md.
This source/test handoff contains exact staged overlay patches and two independently
built Win32 Release D3D8 proxies. It excludes original game executables, private GXI,
full vehicle/course meshes, screenshots, raw logs and a copied renderer.

Frozen source commit: {report['baseline_head']}
Frozen renderer tree: {report['renderer_tree']}
Baseline DLL SHA256: {report['builds']['baseline']['dll_sha256']}
PS2-enabled DLL SHA256: {report['builds']['ps2-enabled']['dll_sha256']}

Mode0 Stock defaults. Modes1/2/3 isolate old static source and COLOROP behavior.
Mode4 implements a bounded live PC framebuffer contribution in a private64 target;
native driver support and visual behavior are pending the next user test.
Native coordinate generation, PS2 timing, GS PSMCT16 and body-base processing are
not claimed equivalent. No automatic deployment, no proxy chain.

Manual test: FoliageMode=0, PixelProbe=0, CourseObjectsMode=0; existing vehicle
reflection policy Stock. Start with the same Tata and Free Camera bookmark;
restart game for each ReflectionMode. Mode4 requires MSAA off and non-MSAA32bit
main backbuffer. If native CopyRects fails, it retains the original material.
Original canonical GXI is supplied locally only for modes1/2/4. Mode3 needs noGXI.

Rebuilding requires an external Git checkout containing the locked frozenrenderer,
Python/Git/CMake/VisualStudio18 2026 Win32. Run overlay/build_overlay.py fromrepo
root; it verifies Git objects/patch hashes and builds serially (--parallel1).
Focused native tests need staged baseline headers and MSVC, not game corpus.
Tree-lock/synthetic Python tests use temporary localGit and generatedmockfixtures;
integration tests inspect verified staging (MRR_PC_PORT_RENDERER_ROOT).
The two compact historical JSON witnesses needed by included tests are included.
Private-image Reset cases use MRR_REFLECTION_TEST_GXI and
MRR_COURSE_OBJECT_TEST_ASSET; unavailable inputs explicitly report NOT_PERFORMED.
Asset preparation additionally needs the original PS2 corpus and, for the first
reflection source witness, the read-only CourseSDK/protected retailPC corpus.
No Blender dependency. Actual commands/results are in command-log.md; examples
and pending human steps are clearly separated from executed checks.

SHA256SUMS.txt covers every other member. ZIP.sha256 hashes the completearchive.
'''.encode()
    members['SHA256SUMS.txt']=''.join(f'{pack.sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    archive=pack.archive_bytes(members)
    if archive!=pack.archive_bytes(members): raise RuntimeError('Non-deterministic serialization')
    pack.verify_archive(archive,members)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_bytes(archive)
    pack.verify_archive(OUTPUT.read_bytes(),members)
    digest=pack.sha256(archive);OUTPUT.with_suffix('.zip.sha256').write_text(f'{digest}  {OUTPUT.name}\n')
    print(json.dumps({'archive':str(OUTPUT),'sha256':digest,'members':len(members),'bytes':len(archive),
        'manifest_round_trip':'PASS','deterministic_serialization':'PASS','original_assets_included':False},indent=2))

if __name__=='__main__': main()
