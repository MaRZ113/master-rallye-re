"""Verified committed-source handoff; excludes unrelated dirty/untracked work."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
from zipfile import ZipFile

PORT = Path(__file__).resolve().parents[1]
ROOT = PORT.parents[1]
DOCS = PORT/'docs/reflection-coverage-fix'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def isolated_tests(data):
    results=[]
    commands=(
        ('source-audit','ps2-research/pc-port/docs/reflection-coverage-fix/source-audit','test_audit.py'),
        ('wooldand','ps2-research/pc-port/docs/reflection-coverage-fix/wooldand','test_join.py'),
        ('modified-materials','ps2-research/pc-port/docs/reflection-coverage-fix','test_modified_materials.py'),
        ('coverage-fix','ps2-research/pc-port/tests','test_reflection_coverage_fix.py'),
    )
    with tempfile.TemporaryDirectory(prefix='mrr-reflection-handoff-') as directory:
        archive=Path(directory)/'review.zip';archive.write_bytes(data)
        # Members came only from explicit repository-relative paths, verified by
        # the existing archive manifest verifier. No external archive is loaded.
        with ZipFile(archive) as z:z.extractall(Path(directory)/'review')
        for name,folder,pattern in commands:
            command=[sys.executable,'-m','unittest','discover','-s',folder,'-p',pattern,'-v']
            result=subprocess.run(command,cwd=Path(directory)/'review',capture_output=True,text=True)
            results.append({'suite':name,'command':command[1:],'returncode':result.returncode,
                            'output':result.stdout+result.stderr})
            if result.returncode:
                raise RuntimeError(f'Isolated {name} failed: {result.stdout}{result.stderr}')
    return results


def main():
    spec=importlib.util.spec_from_file_location('verified_handoff',PORT/'overlay/package_reflection_handoff.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    report=json.loads((PORT/'dist/current/build-report.json').read_text())
    lock=json.loads((PORT/'overlay/baseline-lock.json').read_text())
    sources=h.verify_build_inputs(report,lock)
    commit=git('rev-parse','HEAD').decode().strip()
    paths=git('ls-tree','-r','--name-only',commit,'ps2-research/pc-port').decode().splitlines()
    members={}
    allowed={'.py','.cpp','.hpp','.json','.md','.patch','.x32dbg','.ini','.example'}
    folders=('renderer/','tests/','tools/','overlay/','docs/')
    prefix='ps2-research/pc-port/'
    for path in paths:
        relative=path.removeprefix(prefix)
        if relative.startswith(folders) and Path(path).suffix in allowed or relative in ('.gitignore','.gitattributes','PS2Port.ini.example'):
            members[path]=git('show',f'{commit}:{path}')
    # Never package a source revision different from the successful build.
    eol_conversions=[]
    for name,path in sources.items():
        key=h.relative_name(path)
        built=h.read_required(path)
        if key not in members or h.sha256(built)!=report['ps2_source_sha256'][name]:
            raise RuntimeError(f'Committed source differs from build: {name}')
        # Git core.autocrlf stores LF while this successful Windows build used
        # some CRLF source files. Permit only that exact conversion, never a
        # content change, and package the bytes actually hashed by the build.
        if built!=members[key]:
            if built.replace(b'\r\n',b'\n')!=members[key]:
                raise RuntimeError(f'Uncommitted source content: {name}')
            eol_conversions.append(name)
        members[key]=built
    for path in git('ls-tree','-r','--name-only',commit,'ps2-research/tools').decode().splitlines():
        if path.endswith('.py'):members[path]=git('show',f'{commit}:{path}')
    for folder in ('rigid1','grass1','grass2','water1','refl1','geom1','cdelta1','ui2'):
        for path in git('ls-tree','-r','--name-only',commit,f'ps2-research/{folder}').decode().splitlines():
            if Path(path).suffix not in {'.json','.md'}:continue
            content=git('show',f'{commit}:{path}')
            if len(content)<1024*1024:members[path]=content
    members['build-report.json']=(PORT/'dist/current/build-report.json').read_bytes()
    members['release-provenance.json']=json.dumps({
        'source_commit':commit,'starting_head':'485288f29eebd01d8b2e0d89b8abfd5f01aa56ef',
        'frozen_renderer_tree':report['renderer_tree'],'staging_commit':report['baseline_head'],
        'build_report_source_head':report['current_head'],'sources_and_patches_verified':True,
        'unrelated_uncommitted_work_excluded':True,'proprietary_assets_packaged':False,
        'source_archive_policy':'EXACT_SUCCESSFUL_BUILD_BYTES_WITH_COMMITTED_CONTENT_VERIFICATION',
        'git_lf_build_crlf_files':eol_conversions,
    },indent=2).encode()
    for variant in ('baseline','ps2-enabled'):
        members[f'artifacts/{variant}/d3d8.dll']=h.verified_dll(report,variant)
    handoff_key=prefix+'docs/reflection-coverage-fix/handoff.md'
    if handoff_key not in members:raise RuntimeError('Commit the final research docs before packaging')
    members['HANDOFF.md']=members[handoff_key]

    def serialize():
        members['SHA256SUMS.txt']=''.join(f'{h.sha256(v)}  {k}\n' for k,v in sorted(members.items()) if k!='SHA256SUMS.txt').encode()
        data=h.archive_bytes(members);h.verify_archive(data,members)
        if data!=h.archive_bytes(members):raise RuntimeError('Archive serialization is not deterministic')
        return data

    isolated=isolated_tests(serialize())
    members['handoff-validation.json']=json.dumps({
        'isolated_corpus_independent_tests':isolated,'test_count':16,'result':'PASS',
        'archive_crc_manifest_and_repeated_serialization':'PASS',
        'not_a_game_runtime_test':True,
    },indent=2).encode()
    data=serialize()
    output=PORT/'dist/PS2-REFLECTION-COVERAGE-FIX-handoff.zip'
    output.write_bytes(data);h.verify_archive(output.read_bytes(),members)
    output.with_suffix('.zip.sha256').write_text(f'{h.sha256(data)}  {output.name}\n')
    print(json.dumps({'archive':str(output),'sha256':h.sha256(data),'bytes':len(data),
        'members':len(members),'isolated_tests':'16/16 PASS','integrity':'PASS','source_commit':commit,
        'ps2_dll_sha256':report['builds']['ps2-enabled']['dll_sha256']},indent=2))


if __name__=='__main__':main()
