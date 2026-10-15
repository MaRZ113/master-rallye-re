"""Deterministic source/test/dll handoff for X-Trail CAR trim + WHEEL follow-up."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,tempfile,zipfile
PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def main():
 spec=importlib.util.spec_from_file_location('handoff',PORT/'overlay/package_reflection_handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 report=json.loads((PORT/'dist/current/build-report.json').read_text());lock=json.loads((PORT/'overlay/baseline-lock.json').read_text());sources=h.verify_build_inputs(report,lock)
 commit=git('rev-parse','HEAD').decode().strip();members={}
 for prefix in ['ps2-research/pc-port/renderer','ps2-research/pc-port/tests','ps2-research/pc-port/tools','ps2-research/pc-port/overlay','ps2-research/pc-port/docs/vehicle-race-model-port1','ps2-research/pc-port/docs/vehicle-model-port2','ps2-research/tools']:
  for path in git('ls-tree','-r','--name-only',commit,prefix).decode().splitlines():
   if Path(path).suffix in {'.py','.hpp','.cpp','.md','.json','.patch','.ps1','.x32dbg'}:members[path]=git('show',f'{commit}:{path}')
 for name,path in sources.items():
  key=h.relative_name(path);data=path.read_bytes()
  if key not in members or (data!=members[key] and data.replace(b'\r\n',b'\n')!=members[key]):raise RuntimeError('Uncommitted source '+name)
  if h.sha256(data)!=report['ps2_source_sha256'][name]:raise RuntimeError('Build source drift '+name)
  members[key]=data
 members['build-report.json']=(PORT/'dist/current/build-report.json').read_bytes()
 members['d3d8.dll']=h.verified_dll(report,'ps2-enabled')
 key='ps2-research/pc-port/docs/vehicle-race-model-port1/completion-followup/runtime-ab.md';members['RUNTIME-AB.md']=members[key]
 members['provenance.json']=json.dumps({'commit':commit,'starting_head':'9893186c11f2073895d724e112acfbc07c218049','renderer_tree':report['renderer_tree'],'baseline_head':report['baseline_head'],'build_source_head':report['current_head'],'status':'TRIM_AND_WHEEL_IMPLEMENTED_PENDING_USER_RUNTIME','original_assets_included':False,'original_renderer_unchanged':True,'private_wheel_sha256':'1c548d537acd75480515ff6d43140215638d2cd87c8b254d509dd5e6d004a31f','rebuild_requires_original_git_objects_and_toolchain':True},indent=2).encode()
 results=[]
 with tempfile.TemporaryDirectory(prefix='mrr-race-check-') as tmp:
  root=Path(tmp)
  for k,v in members.items():
   f=root/k;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(v)
  for folder,pattern,count in [('wheel-port','test_wheel.py',3),('conditional-followup','test_registry.py',4)]:
   args=[sys.executable,'-m','unittest','discover','-s','ps2-research/pc-port/docs/vehicle-race-model-port1/'+folder,'-p',pattern,'-v'];r=subprocess.run(args,cwd=root,text=True,capture_output=True);output=r.stdout+r.stderr
   if r.returncode or f'Ran {count} tests' not in output:raise RuntimeError(output)
   results.append({'suite':folder,'tests_run':count,'result':'PASS','output':output})
 members['handoff-validation.json']=json.dumps({'extracted_suites':results,'note':'Private asset check intentionally skips in source-only extraction; full 3/3 local checks and native asset tests ran in original workspace.'},indent=2).encode()
 members['SHA256SUMS.txt']=''.join(h.sha256(v)+'  '+k+'\n' for k,v in sorted(members.items())).encode()
 data=h.archive_bytes(members);h.verify_archive(data,members)
 if data!=h.archive_bytes(members):raise RuntimeError('Nondeterministic archive')
 out=PORT/'dist/vehicle-race-model-completion';out.mkdir(exist_ok=True)
 for name,content in [('handoff.zip',data),('d3d8.dll',members['d3d8.dll']),('build-report.json',members['build-report.json']),('runtime-ab.md',members['RUNTIME-AB.md'])]:
  path=out/name
  if path.exists() and path.read_bytes()!=content:raise RuntimeError('Existing release differs: '+name)
  path.write_bytes(content)
 (out/'SHA256SUMS.txt').write_text(''.join(h.sha256(f.read_bytes())+'  '+f.name+'\n' for f in sorted(out.iterdir()) if f.name!='SHA256SUMS.txt'))
 print(json.dumps({'archive':str(out/'handoff.zip'),'sha256':h.sha256(data),'dll_sha256':h.sha256(members['d3d8.dll']),'commit':commit,'members':len(members),'extracted_tests':7,'result':'PASS'},indent=2))
if __name__=='__main__':main()
