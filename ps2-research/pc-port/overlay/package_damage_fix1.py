"""Verified working-source snapshot; no raw captures or original game assets."""
from pathlib import Path
import importlib.util,json,subprocess,sys,tempfile
PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
def main():
 spec=importlib.util.spec_from_file_location('handoff',PORT/'overlay/package_reflection_handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 report=json.loads((PORT/'dist/current/build-report.json').read_text());lock=json.loads((PORT/'overlay/baseline-lock.json').read_text());sources=h.verify_build_inputs(report,lock)
 members={}
 prefixes=['renderer','tests','tools','overlay','docs/vehicle-crew-port1','docs/vehicle-model-port2/assets','docs/vehicle-damage-fix1']
 for prefix in prefixes:
  directory=PORT/prefix
  listed=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','--',directory.relative_to(ROOT).as_posix()],cwd=ROOT).decode().splitlines()
  for name in listed:
   p=ROOT/name
   if p.is_file() and p.suffix in {'.py','.hpp','.cpp','.md','.json','.patch','.ps1','.x32dbg','.txt'}:members[name]=p.read_bytes()
 for name,p in sources.items():members[h.relative_name(p)]=p.read_bytes()
 for name in subprocess.check_output(['git','ls-files','--','ps2-research/tools'],cwd=ROOT).decode().splitlines():
  p=ROOT/name
  if p.suffix in {'.py','.md','.json'}:members[name]=p.read_bytes()
 members['d3d8.dll']=h.verified_dll(report,'ps2-enabled');members['build-report.json']=(PORT/'dist/current/build-report.json').read_bytes()
 members['RUNTIME-AB.md']=(PORT/'docs/vehicle-damage-fix1/runtime-ab.md').read_bytes()
 members['PS2Port.ini.example']=(PORT/'PS2Port.ini.example').read_bytes()
 members['provenance.json']=json.dumps({'snapshot':'verified uncommitted working source, not HEAD-only archive','starting_head':'cf969a189097cab94281a9b7e7e9771eff97751d','renderer_tree':report['renderer_tree'],'baseline_head':report['baseline_head'],'status':'DAMAGE_CONTINUITY_USER_CONFIRMED; IMPACT_FLICKER_OPEN; TRANSITION_DIAGNOSTIC_PENDING','original_assets_or_raw_captures_included':False,'rebuild_requires_original_git_objects_and_local_proprietary_assets':True},indent=2).encode()
 results=[]
 with tempfile.TemporaryDirectory(prefix='mrr-damage-handoff-') as tmp:
  root=Path(tmp)
  for name,data in members.items():
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  for folder,pattern,count in [('damage','test_evidence.py',5),('frontend','test_frontend_evidence.py',3),('frontend','test_fix1_profiles.py',4)]:
   args=[sys.executable,'-m','unittest','discover','-s','ps2-research/pc-port/docs/vehicle-damage-fix1/'+folder,'-p',pattern,'-v'];r=subprocess.run(args,cwd=root,text=True,capture_output=True);output=r.stdout+r.stderr
   if r.returncode or f'Ran {count} tests' not in output:raise RuntimeError(output)
   results.append({'suite':pattern,'count':count,'output':output})
 members['handoff-validation.json']=json.dumps({'extracted_focused_tests':results,'result':'PASS','private_assets_not_in_source_archive':True},indent=2).encode()
 members['SHA256SUMS.txt']=''.join(h.sha256(v)+'  '+k+'\n' for k,v in sorted(members.items())).encode()
 data=h.archive_bytes(members);h.verify_archive(data,members)
 if data!=h.archive_bytes(members):raise RuntimeError('Nondeterministic ZIP')
 out=PORT/'dist/vehicle-damage-fix1-transition';out.mkdir(exist_ok=True)
 for name,content in [('handoff.zip',data),('d3d8.dll',members['d3d8.dll']),('build-report.json',members['build-report.json']),('runtime-ab.md',members['RUNTIME-AB.md'])]:
  p=out/name
  if p.exists() and p.read_bytes()!=content:raise RuntimeError('Existing different artifact '+name)
  p.write_bytes(content)
 (out/'SHA256SUMS.txt').write_text(''.join(h.sha256(p.read_bytes())+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.name!='SHA256SUMS.txt'))
 print(json.dumps({'archive':str(out/'handoff.zip'),'archive_sha256':h.sha256(data),'dll_sha256':h.sha256(members['d3d8.dll']),'focused_extracted_tests':12,'members':len(members)},indent=2))
if __name__=='__main__':main()
