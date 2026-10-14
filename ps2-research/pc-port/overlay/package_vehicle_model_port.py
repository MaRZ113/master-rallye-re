"""Clean committed-source handoff with exact build-byte and archive verification."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
from zipfile import ZipFile

PORT=Path(__file__).resolve().parents[1]
ROOT=PORT.parents[1]

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def extracted_tests(data):
    suites=[('ps2-research/pc-port/tests','test_vehicle_model_port.py',5),
        ('ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights','test_*.py',18),
        ('ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity','test_*.py',12),
        ('ps2-research/pc-port/docs/vehicle-model-port1/race-partitions','test_*.py',5),
        ('ps2-research/pc-port/tests','test_reflection_coverage_fix.py',3),
        ('ps2-research/pc-port/tests','test_course_objects_asset.py',10),
        ('ps2-research/pc-port/tests','test_grass_asset.py',12),
        ('ps2-research/pc-port/tests','test_shrub_asset.py',10)]
    results=[]
    with tempfile.TemporaryDirectory(prefix='mrr-vehicle-model-handoff-') as directory:
        root=Path(directory);archive=root/'review.zip';archive.write_bytes(data)
        with ZipFile(archive) as z:z.extractall(root/'review')
        for folder,pattern,expected in suites:
            args=['-m','unittest','discover','-s',folder,'-p',pattern,'-v']
            result=subprocess.run([sys.executable,*args],cwd=root/'review',capture_output=True,text=True)
            text=result.stdout+result.stderr
            if result.returncode or f'Ran {expected} tests' not in text:
                raise RuntimeError('Extracted suite failed or count changed: '+text)
            results.append({'command':args,'tests':expected,'result':'PASS'})
    return {'result':'PASS','tests':sum(r['tests'] for r in results),'suites':results,
        'game_assets_or_sdk_required':False,'full_dll_rebuild_requires_original_git_objects':True}

def main():
    spec=importlib.util.spec_from_file_location('verified_handoff',PORT/'overlay/package_reflection_handoff.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    report=json.loads((PORT/'dist/current/build-report.json').read_text())
    lock=json.loads((PORT/'overlay/baseline-lock.json').read_text())
    sources=h.verify_build_inputs(report,lock)
    commit=git('rev-parse','HEAD').decode().strip();members={};conversions=[];metadata_eol=[]
    prefix='ps2-research/pc-port/'
    allowed={'.py','.cpp','.hpp','.java','.json','.md','.patch','.x32dbg','.ini','.example','.ps1'}
    for path in git('ls-tree','-r','--name-only',commit,'ps2-research/pc-port').decode().splitlines():
        relative=path.removeprefix(prefix)
        if not (relative.startswith(('renderer/','tests/','tools/','overlay/','docs/')) and Path(path).suffix in allowed or
                relative in ('.gitignore','.gitattributes','PS2Port.ini.example')):continue
        committed=git('show',f'{commit}:{path}');members[path]=committed
        if Path(path).suffix=='.json':
            current=h.read_required(ROOT/path)
            if current!=committed and current.replace(b'\r\n',b'\n')==committed:
                members[path]=current;metadata_eol.append(path)
    for name,path in sources.items():
        key=h.relative_name(path);built=h.read_required(path)
        if key not in members or h.sha256(built)!=report['ps2_source_sha256'][name]:
            raise RuntimeError('Successful build source not committed: '+name)
        if built!=members[key]:
            if built.replace(b'\r\n',b'\n')!=members[key]:raise RuntimeError('Uncommitted build source: '+name)
            conversions.append(name)
        members[key]=built
    for path in git('ls-tree','-r','--name-only',commit,'ps2-research/tools').decode().splitlines():
        if path.endswith('.py'):members[path]=git('show',f'{commit}:{path}')
    for folder in ('rigid1','grass1','grass2','water1','refl1','geom1','cdelta1','ui','ui2'):
        for path in git('ls-tree','-r','--name-only',commit,f'ps2-research/{folder}').decode().splitlines():
            if Path(path).suffix not in {'.json','.md'}:continue
            content=git('show',f'{commit}:{path}')
            if len(content)<1024*1024:members[path]=content
    members['build-report.json']=(PORT/'dist/current/build-report.json').read_bytes()
    members['release-provenance.json']=json.dumps({'source_commit':commit,
        'starting_head':'a6daf3b17d32043c948e3ed9a843b1a5b3258f16',
        'renderer_tree':report['renderer_tree'],'staging_commit':report['baseline_head'],
        'build_report_source_head':report['current_head'],'source_and_patch_hashes_verified':True,
        'git_lf_build_crlf_files':conversions,'git_lf_metadata_crlf_files':metadata_eol,
        'unrelated_dirty_work_excluded':True,'original_assets_packaged':False,
        'frontend_replacement':'BLOCKED_OWNER_JOIN','race_pilot':'IMPLEMENTED_PENDING_USER_RUNTIME'},indent=2).encode()
    for variant in ('baseline','ps2-enabled'):members[f'artifacts/{variant}/d3d8.dll']=h.verified_dll(report,variant)
    key=prefix+'docs/vehicle-model-port1/handoff.md'
    if key not in members:raise RuntimeError('Commit this phase before packaging')
    members['HANDOFF.md']=members[key]
    def serialize():
        members['SHA256SUMS.txt']=''.join(f'{h.sha256(v)}  {k}\n' for k,v in sorted(members.items()) if k!='SHA256SUMS.txt').encode()
        data=h.archive_bytes(members);h.verify_archive(data,members)
        if data!=h.archive_bytes(members):raise RuntimeError('Nondeterministic serialization')
        return data
    validation=extracted_tests(serialize());validation['crc_manifest_repeat_serialization']='PASS'
    members['handoff-validation.json']=json.dumps(validation,indent=2).encode()
    data=serialize();output=PORT/'dist/PS2-VEHICLE-MODEL-PORT1-handoff.zip'
    output.write_bytes(data);h.verify_archive(output.read_bytes(),members)
    output.with_suffix('.zip.sha256').write_text(f'{h.sha256(data)}  {output.name}\n')
    print(json.dumps({'archive':str(output),'sha256':h.sha256(data),'members':len(members),'bytes':len(data),
        'isolated_tests':validation['tests'],'result':'PASS','source_commit':commit,
        'ps2_dll_sha256':report['builds']['ps2-enabled']['dll_sha256']},indent=2))

if __name__=='__main__':main()
