#!/usr/bin/env python3
"""Verified grass source/test handoff; original point/image asset stays local."""
import importlib.util
import json
from pathlib import Path
PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
DOCS=PORT/'docs/grass-port1';OUTPUT=PORT/'dist/PS2-GRASS-PORT1-handoff.zip'
spec=importlib.util.spec_from_file_location('verified_pack',PORT/'overlay/package_reflection_handoff.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)

def main():
    report=json.loads(pack.read_required(DOCS/'build-report.json'))
    lock=json.loads(pack.read_required(PORT/'overlay/baseline-lock.json'))
    sources=pack.verify_build_inputs(report,lock)
    for name in ('final-report.md','validation.md','command-log.md','runtime-ab.md','visual-comparison.md','source-contract.json'):
        pack.read_required(DOCS/name)
    paths=list(sources.values())
    paths += [PORT/name for name in ('.gitignore','README.md','PS2Port.ini.example','overlay/README.md',
        'overlay/build_overlay.py','overlay/baseline-lock.json','overlay/package_reflection_handoff.py',
        'overlay/package_grass_handoff.py','overlay/patches/0001-renderer-integration.patch',
        'overlay/patches/0002-interface-generator.patch','tools/prepare_grass_pilot.py',
        'tools/prepare_reflection_pilot.py','tools/prepare_course_objects.py')]
    paths += [p for p in DOCS.rglob('*') if p.is_file() and p.suffix in {'.md','.json'}]
    paths += [PORT/'docs/reflection-port1/material-source-contract.json',PORT/'docs/course-objects1/source-contract.json',
              PORT/'docs/reflection-port1.1/classifier-provenance.json']
    paths += [ROOT/'ps2-research/tools'/name for name in pack.RESEARCH_TOOLS+('geometry_delta.py',)]
    paths += [ROOT/'ps2-research/grass1'/name for name in ('final-report.md','material-directive-contract.md',
        'placement-and-density.md','surface-eligibility.md','randomness.md','primitive-geometry.md','culling-and-animation.md','vu-contract.json')]
    members={pack.relative_name(p):pack.read_required(p) for p in sorted(set(paths))}
    for variant in ('baseline','ps2-enabled'):members[f'artifacts/{variant}/d3d8.dll']=pack.verified_dll(report,variant)
    members['HANDOFF.md']=f'''# PS2-GRASS-PORT1 — Turkey3 grass preview

Start with ps2-research/pc-port/docs/grass-port1/final-report.md and runtime-ab.md.
This archive includes source/tests/exact overlays/compact research and independently
built Win32 Release baseline and PS2 proxies. It excludes original PS2/PC files,
images, full coordinates, screenshots, raw logs and a renderer copy.

Frozen renderer Git commit: {report['baseline_head']}
Frozen renderer tree: {report['renderer_tree']}
Baseline DLL SHA256: {report['builds']['baseline']['dll_sha256']}
PS2 DLL SHA256: {report['builds']['ps2-enabled']['dll_sha256']}

Stock defaults: GrassMode0, FoliageMode0, PixelProbe0, ReflectionMode0,
CourseObjectsMode0. Enable only GrassMode1 for the first Turkey3 A/B.
The private .ps2grass asset is already local in the original research checkout,
or must be regenerated from the canonical PS2 corpus/protected PC DX/TXT using
the read-only CourseSDK and prepare_grass_pilot.py. It is NOT in this archive.
No Blender dependency; no automatic DLL deployment or asset installation.

Full native rebuild requires the external Git checkout with locked renderer,
Python/Git/CMake/VisualStudio18 2026 Win32. Run overlay/build_overlay.py;
it stages verified immutable Git objects, applies exact patches, repeats the
generator and serially builds both variants (--parallel1).
Synthetic Python asset/tree-lock tests need no game corpus. Source/integration
tests require verified staging (MRR_PC_PORT_RENDERER_ROOT); necessary small
historical JSON witnesses are included. Native tests need baseline headers
and MSVC. Optional original-asset subcases use MRR_GRASS_TEST_ASSET,
MRR_COURSE_OBJECT_TEST_ASSET and MRR_REFLECTION_TEST_GXI; absent inputs explicitly
print NOT_PERFORMED. All three were supplied and passed in the original build.

64,900 reconstructed sourcepoints do not mean64,900 simultaneously visible
plants. Region/radial selection and native clipping/depth/alpha act at runtime.
Full-triangle activation, PC size/UV/projection/alpha/batch and chosen FCSR
rounding are explicit preview boundaries. Actual gameplay and PS2 parity pending.

SHA256SUMS.txt hashes every other member; ZIP.sha256 hashes the archive.
Executed commands and pending human recipe are distinguished in command-log.md.
'''.encode()
    members['SHA256SUMS.txt']=''.join(f'{pack.sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    data=pack.archive_bytes(members)
    if data!=pack.archive_bytes(members):raise RuntimeError('Non-deterministic ZIP')
    pack.verify_archive(data,members);OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_bytes(data)
    pack.verify_archive(OUTPUT.read_bytes(),members)
    digest=pack.sha256(data);OUTPUT.with_suffix('.zip.sha256').write_text(f'{digest}  {OUTPUT.name}\n')
    print(json.dumps({'archive':str(OUTPUT),'sha256':digest,'members':len(members),'bytes':len(data),
        'manifest_round_trip':'PASS','deterministic_serialization':'PASS','original_geometry_images_included':False},indent=2))

if __name__=='__main__':main()
