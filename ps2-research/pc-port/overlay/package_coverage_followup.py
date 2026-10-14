"""Coverage follow-up source/DLL handoff; no proprietary assets or deployment."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
from zipfile import ZipFile

PORT=Path(__file__).resolve().parents[1]
ROOT=PORT.parents[1]


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def isolated_tests(data):
    suites=(
        ('ps2-research/pc-port/tests','test_coverage_followup.py',3),
        ('ps2-research/pc-port/tests','test_reflection_coverage_fix.py',3),
        ('ps2-research/pc-port/docs/coverage-followup/vegetation','test_deployment_inventory.py',2),
        ('ps2-research/pc-port/docs/coverage-followup/frontend','test_audit.py',7),
        ('ps2-research/pc-port/docs/coverage-followup/body-lights','test_audit.py',4),
        ('ps2-research/pc-port/docs/reflection-coverage-fix/source-audit','test_audit.py',5),
        ('ps2-research/pc-port/docs/reflection-coverage-fix/wooldand','test_join.py',5),
        ('ps2-research/pc-port/docs/reflection-coverage-fix','test_modified_materials.py',3),
    )
    results=[]
    with tempfile.TemporaryDirectory(prefix='mrr-coverage-handoff-') as directory:
        archive=Path(directory)/'review.zip';archive.write_bytes(data)
        with ZipFile(archive) as z:z.extractall(Path(directory)/'review')
        for folder,pattern,count in suites:
            args=['-m','unittest','discover','-s',folder,'-p',pattern,'-v']
            result=subprocess.run([sys.executable,*args],cwd=Path(directory)/'review',capture_output=True,text=True)
            results.append({'command':args,'count':count,'returncode':result.returncode,'output':result.stdout+result.stderr})
            if result.returncode:raise RuntimeError(f'Extracted handoff tests failed: {result.stdout}{result.stderr}')
    return {'tests':results,'count':sum(s[2] for s in suites),'result':'PASS','external_game_data_required':False}


def main():
    spec=importlib.util.spec_from_file_location('verified_handoff',PORT/'overlay/package_reflection_handoff.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    report=json.loads((PORT/'dist/current/build-report.json').read_text())
    lock=json.loads((PORT/'overlay/baseline-lock.json').read_text())
    sources=h.verify_build_inputs(report,lock)
    commit=git('rev-parse','HEAD').decode().strip();members={}
    prefix='ps2-research/pc-port/'
    allowed={'.py','.cpp','.hpp','.java','.json','.md','.patch','.x32dbg','.ini','.example'}
    for path in git('ls-tree','-r','--name-only',commit,'ps2-research/pc-port').decode().splitlines():
        relative=path.removeprefix(prefix)
        if relative.startswith(('renderer/','tests/','tools/','overlay/','docs/')) and Path(path).suffix in allowed or relative in ('.gitignore','.gitattributes','PS2Port.ini.example'):
            members[path]=git('show',f'{commit}:{path}')
    conversions=[]
    for name,path in sources.items():
        key=h.relative_name(path);built=h.read_required(path)
        if key not in members or h.sha256(built)!=report['ps2_source_sha256'][name]:
            raise RuntimeError(f'Committed source differs from successful build: {name}')
        if built!=members[key]:
            if built.replace(b'\r\n',b'\n')!=members[key]:raise RuntimeError(f'Uncommitted source content: {name}')
            conversions.append(name)
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
        'source_commit':commit,'starting_head':'22c0ccad5c849f949e7275e9b4afb09da6e75b93',
        'renderer_tree':report['renderer_tree'],'staging_commit':report['baseline_head'],
        'build_report_source_head':report['current_head'],'source_and_patch_hashes_verified':True,
        'git_lf_build_crlf_files':conversions,'source_archive_policy':'EXACT_BUILD_BYTES_COMMITTED_CONTENT_VERIFIED',
        'unrelated_uncommitted_work_excluded':True,'proprietary_assets_packaged':False,
    },indent=2).encode()
    for variant in ('baseline','ps2-enabled'):members[f'artifacts/{variant}/d3d8.dll']=h.verified_dll(report,variant)
    key=prefix+'docs/coverage-followup/handoff.md'
    if key not in members:raise RuntimeError('Commit current handoff documentation before packaging')
    members['HANDOFF.md']=members[key]

    def serialize():
        members['SHA256SUMS.txt']=''.join(f'{h.sha256(v)}  {k}\n' for k,v in sorted(members.items()) if k!='SHA256SUMS.txt').encode()
        data=h.archive_bytes(members);h.verify_archive(data,members)
        if data!=h.archive_bytes(members):raise RuntimeError('Archive serialization is not deterministic')
        return data

    validation=isolated_tests(serialize())
    validation['archive_crc_manifest_repeat_serialization']='PASS'
    members['handoff-validation.json']=json.dumps(validation,indent=2).encode()
    data=serialize();output=PORT/'dist/PS2-VISUAL-COVERAGE-FOLLOWUP-handoff.zip'
    output.write_bytes(data);h.verify_archive(output.read_bytes(),members)
    output.with_suffix('.zip.sha256').write_text(f'{h.sha256(data)}  {output.name}\n')
    print(json.dumps({'archive':str(output),'sha256':h.sha256(data),'bytes':len(data),'members':len(members),
        'isolated_tests':f"{validation['count']}/{validation['count']} PASS",'integrity':'PASS',
        'source_commit':commit,'ps2_dll_sha256':report['builds']['ps2-enabled']['dll_sha256']},indent=2))


if __name__=='__main__':main()
