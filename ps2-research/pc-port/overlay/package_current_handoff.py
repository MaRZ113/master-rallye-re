#!/usr/bin/env python3
"""Compact current release handoff, exact provenance, no full renderer copy."""
import argparse,importlib.util,json,subprocess
from pathlib import Path
PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
pack=load('current_handoff_helpers',PORT/'overlay/package_reflection_handoff.py')
b=load('current_build_verifier',PORT/'overlay/build_overlay.py')

def verify(report,lock,approved_exception=False):
    def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
    if not approved_exception:b.verify_baseline(lock)
    else:
        # Packaging-only explicit switch; it cannot build or permit changed
        # native sources. Exactly the previously authorized files/hashes only.
        exception=report.get('one_off_worktree_exception',{})
        if exception.get('working_sources_used') is not False:raise RuntimeError('Missing verified immutable-object exception')
        expected=exception.get('excluded_worktree_sha256',{})
        allowed={'modernization/renderer/'+p for p in ('docs/global-hud-hide/implementation.md',
            'include/hud_visibility.hpp','src/visual_wrappers.cpp','tests/hud_visibility_tests.cpp')}
        if set(expected)!=allowed:raise RuntimeError('Wrong approved worktree file set')
        dirty=set(git('diff','--name-only','HEAD','--','modernization/renderer').splitlines())
        if not dirty.issubset(allowed):raise RuntimeError('Unapproved baseline working changes')
        if git('ls-files','--others','--exclude-standard','--','modernization/renderer'):raise RuntimeError('Untracked original renderer files')
        for p,digest in expected.items():
            if b.file_sha(ROOT/p)!=digest:raise RuntimeError('Approved worktree file changed: '+p)
    if git('branch','--show-current')!=lock['baseline_branch']:raise RuntimeError('Branch drift')
    for revision in ('HEAD',lock['baseline_head']):
        if git('rev-parse',revision+':modernization/renderer')!=lock['renderer_tree']:raise RuntimeError('Frozen renderer tree drift')
    for field in ('baseline_head','renderer_tree','branch'):
        expected=lock['baseline_branch'] if field=='branch' else lock[field]
        if report[field]!=expected:raise RuntimeError('Build identity mismatch: '+field)
    for relative,expected in lock['files'].items():
        original=subprocess.check_output(['git','show',lock['baseline_head']+':'+relative],cwd=ROOT)
        if pack.sha256(original)!=expected['sha256']:raise RuntimeError('Immutable source mismatch')
    if set(report['patch_sha256'])!=set(b.PATCH_PATHS) or set(lock['patches'])!=set(b.PATCH_PATHS):raise RuntimeError('Patch set mismatch')
    for name in b.PATCH_PATHS:
        if b.file_sha(PORT/'overlay/patches'/name)!=lock['patches'][name]['sha256'] or report['patch_sha256'][name]!=lock['patches'][name]['sha256']:raise RuntimeError('Patch mismatch')
    sources=pack.current_ps2_sources()
    if set(sources)!=set(report['ps2_source_sha256']):raise RuntimeError('Source set drift')
    for name,path in sources.items():
        digest=report['ps2_source_sha256'][name]
        if b.file_sha(path)!=digest or b.file_sha(PORT/'.staging/ps2-enabled/ps2-research/pc-port'/name)!=digest:raise RuntimeError('Source drift: '+name)
    for variant in ('baseline','ps2-enabled'):
        if any(report['builds'][variant][k]!='PASS' for k in ('build','ctest','proxy_verification')):raise RuntimeError('Build/test failure')
        if not report['generator'][variant]['deterministic'] or b.generated_hashes(PORT/'.staging'/variant/'modernization/renderer')!=lock['generated_outputs'][variant]:raise RuntimeError('Generator drift')
    if report['ps2_port_tests']!='PASS':raise RuntimeError('Python tests not verified')
    return sources

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--approved-worktree-report',action='store_true',
        help='Package only the explicitly approved four-file worktree exception already recorded by the completed build')
    parser.add_argument('--phase',choices=('grass2','rigid-hud'),default='rigid-hud',
        help='Choose the current handoff; old GRASS2 archive is preserved by the default new phase')
    args=parser.parse_args();report=json.loads(pack.read_required(PORT/'dist/current/build-report.json'))
    lock=json.loads(pack.read_required(PORT/'overlay/baseline-lock.json'));sources=verify(report,lock,args.approved_worktree_report)
    if args.phase=='rigid-hud':
        validation=json.loads(pack.read_required(PORT/'docs/rigid-port1/validation.json'))
        if b.file_sha(PORT/'dist/current/build-report.json')!=validation['build_report_sha256']:
            raise RuntimeError('Rigid validation refers to a different completed build')
        for name,digest in validation['tool_sha256'].items():
            if pack.sha256(pack.read_required(PORT/name))!=digest:
                raise RuntimeError('Rigid source/test differs from verified focused tests: '+name)
    paths=list(sources.values())+[PORT/p for p in ('README.md','PS2Port.ini.example','.gitignore')]
    paths += [p for p in (PORT/'overlay').rglob('*') if p.is_file() and p.suffix in ('.py','.ps1','.patch','.json','.md') and p.name!='build-report.json']
    paths += [p for folder in ('docs/build-policy','docs/menu-grass-fix1','docs/grass-port2','docs/rigid-port1','docs/hud-port0') for p in (PORT/folder).rglob('*') if p.is_file() and (p.suffix in ('.json','.md','.patch','.x32dbg','.py') or p.name in ('SHA256SUMS','SHA256SUMS.txt'))]
    paths += [PORT/p for p in ('docs/reflection-port1/material-source-contract.json',
        'docs/course-objects1/source-contract.json','docs/grass-port1/source-contract.json',
        'docs/reflection-port1.1/classifier-provenance.json')]
    paths += [ROOT/'ps2-research/tools'/p for p in pack.RESEARCH_TOOLS+('geometry_delta.py','rigid_runtime.py','spline_runtime.py','elf_query.py')]
    paths += [PORT/'tools'/p for p in ('prepare_grass_pilot.py','prepare_shrub_pilot.py','prepare_course_objects.py','prepare_reflection_pilot.py','prepare_tumbleweed_contract.py','rigid_lifecycle_probe.py')]
    paths += [ROOT/'ps2-research/revalidation2/tools/verify_r5900_revalidation2.py']
    members={pack.relative_name(p):pack.read_required(p) for p in sorted(set(paths))}
    members['build-report.json']=pack.read_required(PORT/'dist/current/build-report.json')
    for v in ('baseline','ps2-enabled'):members['artifacts/'+v+'/d3d8.dll']=pack.verified_dll(report,v)
    grass_handoff=('''# PS2-GRASS2 — Turkey3 second vegetation category and rigid-port boundary

Start with ps2-research/pc-port/docs/grass-port2/final-report.md and
runtime-ab.md; build policy/inventory in docs/build-policy. Two independent
Win32 Release proxies, one per build, no proxy chain. No automatic deployment.
Sources/tests/exact patches/compact metadata included. Original game files,
private .ps2grass/.ps2obj/GXI inputs, meshes, screenshots, raw logs and the full
renderer are excluded. All modes default0. Manual installation only.

Full native rebuild requires the external repository with frozen renderer,
Git/Python/CMake/MSVC Win32; public builder requires a clean locked renderer.
This release uses the newly committed, unchanged HUD baseline. Adoption from
the previous frozen tree was separately verified byte-for-byte; compact audit
fixtures and retired patch evidence are included. Only two active exact patches.

Corpus-independent Python tests for assets/tree lock/build roots/policies can
run from this archive. Source integration tests require immutable renderer
staging: MRR_PC_PORT_RENDERER_ROOT must point to that verified stage. Full88
tests were executed in the original checkout; native24/30 CTest also executed.
Private corpus test cases need MRR_GRASS_TEST_ASSET/MRR_SHRUB_TEST_ASSET/
MRR_COURSE_OBJECT_TEST_ASSET/MRR_REFLECTION_TEST_GXI. No Blender needed.
First grass and frontend/HUD freezes were confirmed by the user. New shrubs
remain pending user A/B; no PS2 pixel parity is claimed. Private shrub/grass
point/image packs are not included. Set the verified local ShrubsAsset path
in PS2Port.ini per runtime-ab.md; GrassMode/ShrubsMode are independent opt-in.
The originalPC native rigidprop path is identified, but safe private convex
resource, Egg owner and physics-thread lifetime still block the physical port.
No fake physics or original-course modification is enabled.

Canonical source location .staging, two CMake configurations .build/baseline
and .build/ps2-enabled; final outputs dist/current. Four approved legacy roots
were fully archived/verified then removed, reclaiming ~702MiB net. The ignored
complete cleanup-preservation archive stays local and is not this handoff.
SHA256SUMS.txt covers every other member. No auto-installation or push.
''')
    rigid_handoff='''# PS2-RIGID-PORT1 + HUD-PORT0 — resource/lifecycle checkpoint

Start with ps2-research/pc-port/docs/rigid-port1/final-report.md, then
runtime-control.md and docs/hud-port0/final-report.md. The physical object is
NOT ENABLED. Native cache invalidation is proved and original convex wire is
byte-compatible; private native stream/resource registration, owner lifetime,
thread admission, contact and restart/exit remain the implementation gate.
HUD is research/design only: proposed static tachometer plate; exact live
SpeedDial semantic mapping still missing. No fake physics or HUD override.

Accepted GRASS2 implementation is unchanged and runtime draw/visibility
evidence is adopted in compact grass2-runtime-review.json. Both DLLs have the
same hashes as that accepted release. All example modes default0. Do not
reinstall merely to use the new external read-only probe. No automatic deploy.

Included: tools/tests, two exact overlay patches, frozen renderer lock,
compact original instruction/format/source evidence, HUD source matrix,
bounded x32dbg recipe, build report and two existing Win32 Release DLLs.
Excluded: original binaries/PSM/DX/XML/GXI/hull bytes/complete meshes, raw
logs/screenshots, private .ps2grass/.ps2obj assets and full renderer copies.
SHA256SUMS.txt covers every other member; no proxy chain or game EXE patch.

Full rebuild requires the external repository at the locked renderer tree,
Git/Python/CMake/MSVC Win32. Command actually executed in that checkout:
  python ps2-research/pc-port/overlay/build_overlay.py
It reuses .build/baseline and .build/ps2-enabled and .staging, builds serially,
checks exact patches/generator twice, native24/30 CTest and port107 Python tests.
Original renderer is not bundled and must not be approximated with another copy.

Without game data: observer10 tests; synthetic grass/shrub/asset/policy/tree-lock
tests run independently. Standalone examples from extracted archive root:
  python -m unittest discover -s ps2-research/pc-port/tests -p test_rigid_lifecycle_probe.py -v
  python -m unittest discover -s ps2-research/pc-port/tests -p test_tumbleweed_contract.py -v
The second command has2 self-contained identity/storage tests;5 synthetic
wire tests need the external read-only Course SDK collision reader/serializer,
and2 original-source tests also need canonical PS2 PackFS corpus. Missing
declared SDK/corpus causes explicit dependency skips; it is not a physical pass.
PS2_COURSE_SDK_ROOT and PS2_TUMBLEWEED_CORPUS select those external roots.
Source-integration test suites need MRR_PC_PORT_RENDERER_ROOT pointing to a
verified immutable PS2-enabled renderer staging tree. Missing-stage failures
must not be silently counted as test passes. No manual earlier handoff needed
for small fixtures: required research JSON/scripts are included here.

HUD source audit requires original PS2 corpus, protected PC Retail corpus,
read-only SDK, existing Rabbitizer1.16.2 and named F10 captures. Source scripts
and short evidence included; no Ghidra project/disassembly dump. The selected
PS2 revalidation helper needs the original ELF plus installed EER/Rabbitizer
for re-execution. Neither REA nor Blender is needed for bundle-only tests.

Native sampler and debugger recipe are opt-in USER EXAMPLES, not runtime
tests performed by Codex. Explicit PID, exact EXE hash/PE32/base/backend gates,
max60seconds/16instances/64KiB-per-sample. Snapshots aren't atomic and do not
certify course ownership/thread/contact/destruction. x32dbg INT3 logpoints
are separately capped16 hits each and change timing. No engine getter calls.
Use one original native control on cold Turkey3 load, restart and exit before
designing a private owner/cache bridge. Checkpoint/HUD implementation deferred.

No original asset or frozen renderer source changed; no deployment or push.
Existing uncommitted port work preserved. DLLs are local handoff artifacts.
'''
    members['HANDOFF.md']=((rigid_handoff if args.phase=='rigid-hud' else grass_handoff)+
        f'\nBaseline commit: {report["baseline_head"]}\nRenderer tree: {report["renderer_tree"]}\n'+
        ''.join(f'{v} DLL SHA256: {report["builds"][v]["dll_sha256"]}\n' for v in ('baseline','ps2-enabled'))).encode()
    members['SHA256SUMS.txt']=''.join(f'{pack.sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    data=pack.archive_bytes(members)
    if data!=pack.archive_bytes(members):raise RuntimeError('Nondeterministic archive')
    pack.verify_archive(data,members)
    filename='PS2-RIGID-PORT1-HUD-PORT0-handoff.zip' if args.phase=='rigid-hud' else 'PS2-GRASS2-handoff.zip'
    output=PORT/'dist'/filename;output.write_bytes(data)
    pack.verify_archive(output.read_bytes(),members)
    output.with_suffix('.zip.sha256').write_text(f'{pack.sha256(data)}  {output.name}\n')
    print(json.dumps({'archive':str(output),'sha256':pack.sha256(data),'members':len(members),'bytes':len(data),
        'manifest_round_trip':'PASS','deterministic_serialization':'PASS'},indent=2))
if __name__=='__main__':main()
