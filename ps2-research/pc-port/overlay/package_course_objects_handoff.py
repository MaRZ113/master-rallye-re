#!/usr/bin/env python3
"""Compact verified object-layer handoff; excludes original meshes/textures."""
import importlib.util
import json
from pathlib import Path

PORT=Path(__file__).resolve().parents[1]
ROOT=PORT.parents[1]
DOCS=PORT/'docs/course-objects1'
OUTPUT=PORT/'dist/PS2-COURSE-OBJECTS1-handoff.zip'
spec=importlib.util.spec_from_file_location('verified_handoff',PORT/'overlay/package_reflection_handoff.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)

def main():
    report=json.loads(pack.read_required(DOCS/'build-report.json'))
    lock=json.loads(pack.read_required(PORT/'overlay/baseline-lock.json'))
    sources=pack.verify_build_inputs(report,lock)
    for name in ('final-report.md','validation.md','design.md','runtime-ab.md','command-log.md','source-contract.json'):
        pack.read_required(DOCS/name)
    paths=list(sources.values())
    paths += [PORT/name for name in ('.gitignore','README.md','PS2Port.ini.example','overlay/README.md',
        'overlay/build_overlay.py','overlay/baseline-lock.json','overlay/package_reflection_handoff.py',
        'overlay/package_course_objects_handoff.py','overlay/patches/0001-renderer-integration.patch',
        'overlay/patches/0002-interface-generator.patch','tools/prepare_course_objects.py','tools/prepare_reflection_pilot.py')]
    paths += [p for p in DOCS.rglob('*') if p.is_file() and p.suffix in {'.md','.json'}]
    # Existing focused reflection tests depend on this compact source witness.
    paths += [PORT/'docs/reflection-port1/material-source-contract.json']
    paths += [ROOT/'ps2-research/tools'/name for name in pack.RESEARCH_TOOLS]
    for phase,names in [('water1',('final-report.md','turkey3-delta.md','texture-binding.md','render-contract.json','uv-and-animation.md')),
                        ('geom1',('turkey3-case-study.md','source-and-coordinate-contract.md'))]:
        paths += [ROOT/'ps2-research'/phase/name for name in names]
    members={pack.relative_name(p):pack.read_required(p) for p in sorted(set(paths))}
    for variant in ('baseline','ps2-enabled'):members[f'artifacts/{variant}/d3d8.dll']=pack.verified_dll(report,variant)
    members['HANDOFF.md']=f'''# PS2-COURSE-OBJECTS1 — Turkey3 additive layer

Start with ps2-research/pc-port/docs/course-objects1/final-report.md and runtime-ab.md.
The frozen renderer source is absent; rebuilding requires the external Git checkout
with pinned commit {report['baseline_head']} and tree {report['renderer_tree']},
Python, CMake and the existing Visual Studio Win32 toolchain. Exact overlay patches,
PS2 sources/tests and both independently built proxy DLLs are included.

Stock defaults are CourseObjectsMode=0, FoliageMode=0, PixelProbe=0, ReflectionMode=0.
Mode1 is original-source geometry/static-texture inspection, not complete PS2 water.
Manual installation only. The original .ps2obj mesh/image is excluded: prepare it
locally from the canonical PS2 corpus using tools/prepare_course_objects.py.

Python tree-lock/synthetic artifact tests need Python/Git only. Full Python integration
requires verified external staging (set MRR_PC_PORT_RENDERER_ROOT). Native tests need
the staged frozen renderer headers and Windows toolchain. The optional original-image
cases additionally need MRR_COURSE_OBJECT_TEST_ASSET / MRR_REFLECTION_TEST_GXI;
they explicitly report NOT_PERFORMED without inputs. Both ran and passed here.
No Course SDK or Blender is needed for this Turkey3 package preparation.

Actual commands/results and runtime limits are in command-log.md and validation.md.
SHA256SUMS.txt covers all members except itself; the ZIP has a checksum sidecar.
Baseline DLL: {report['builds']['baseline']['dll_sha256']}
PS2 DLL: {report['builds']['ps2-enabled']['dll_sha256']}
Neither original geometry/textures nor canonical game executables are included.
'''.encode()
    members['SHA256SUMS.txt']=''.join(f'{pack.sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    archive=pack.archive_bytes(members)
    if archive!=pack.archive_bytes(members):raise RuntimeError('Non-deterministic archive')
    pack.verify_archive(archive,members)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_bytes(archive)
    pack.verify_archive(OUTPUT.read_bytes(),members)
    digest=pack.sha256(archive);OUTPUT.with_suffix('.zip.sha256').write_text(f'{digest}  {OUTPUT.name}\n')
    print(json.dumps({'archive':str(OUTPUT),'sha256':digest,'members':len(members),'bytes':len(archive),
        'manifest_round_trip':'PASS','deterministic_serialization':'PASS','proprietary_assets_included':False},indent=2))

if __name__=='__main__':main()
