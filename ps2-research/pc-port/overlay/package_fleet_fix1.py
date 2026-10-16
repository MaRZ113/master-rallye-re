"""Clean source handoff plus separate local runtime assets; never deploys."""
from pathlib import Path
import importlib.util,json,subprocess,sys,hashlib,tempfile
PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
def main():
 spec=importlib.util.spec_from_file_location('handoff',PORT/'overlay/package_reflection_handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 report=json.loads((PORT/'dist/current/build-report.json').read_text());lock=json.loads((PORT/'overlay/baseline-lock.json').read_text());sources=h.verify_build_inputs(report,lock)
 out=PORT/'dist/vehicle-fleet-port1-fix1';out.mkdir(exist_ok=True);members={}
 for prefix in ['renderer','tests','tools','overlay','docs/vehicle-crew-port1','docs/vehicle-model-port2/assets','docs/vehicle-damage-fix1','docs/vehicle-continuity2','docs/vehicle-fleet-port1','docs/vehicle-fleet-port1-fix1']:
  directory=PORT/prefix
  for name in subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','--',directory.relative_to(ROOT).as_posix()],cwd=ROOT).decode().splitlines():
   p=ROOT/name
   if p.is_file() and p.suffix in {'.py','.hpp','.cpp','.md','.json','.patch','.ps1','.x32dbg','.txt'}:members[name]=p.read_bytes()
 for name,p in sources.items():members[h.relative_name(p)]=p.read_bytes()
 for name in subprocess.check_output(['git','ls-files','--','ps2-research/tools'],cwd=ROOT).decode().splitlines():
  p=ROOT/name
  if p.suffix in {'.py','.md','.json'}:members[name]=p.read_bytes()
 members['d3d8.dll']=h.verified_dll(report,'ps2-enabled');members['build-report.json']=(PORT/'dist/current/build-report.json').read_bytes();members['RUNTIME-AB.md']=(PORT/'docs/vehicle-fleet-port1-fix1/runtime-ab.md').read_bytes();members['PS2Port.ini.example']=(PORT/'PS2Port.ini.example').read_bytes()
 validation=[]
 with tempfile.TemporaryDirectory(prefix='mrr-fleet-source-') as tmp:
  root=Path(tmp)
  for name,data in members.items():p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  for folder,pattern,count in [('vehicle-fleet-port1/admission','test_source_contracts.py',5),('vehicle-fleet-port1/wheels-damage','test_contracts.py',5),('vehicle-fleet-port1/lamps','test_lamp_inventory.py',4),('vehicle-continuity2/fleet-car','test_contracts.py',6),('vehicle-continuity2/frontend','test_frontend_continuity2.py',5),('vehicle-continuity2/tread','test_tread.py',2),('vehicle-continuity2/damage-parts','test_front_lamp_evidence.py',3)]:
   r=subprocess.run([sys.executable,'-m','unittest','discover','-s','ps2-research/pc-port/docs/'+folder,'-p',pattern,'-v'],cwd=root,text=True,capture_output=True);output=r.stdout+r.stderr
   if r.returncode or f'Ran {count} tests' not in output:raise RuntimeError(output)
   validation.append({'suite':folder,'tests':count,'output':output})
 members['handoff-validation.json']=json.dumps({'extracted_focused_tests':validation,'result':'PASS'},indent=2).encode()
 profiles=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/race-profiles.json').read_text())['profiles'];assets={};manifest=[]
 for p in profiles:
  data=(PORT/'.assets/vehicles'/p['filename']).read_bytes()
  if h.sha256(data)!=p['sha256'] or len(data)!=p['bytes']:raise ValueError('CAR asset changed')
  assets[p['filename']]=data;manifest.append({'family':p['family'],'file':p['filename'],'bytes':len(data),'sha256':h.sha256(data),'runtime_render_confirmed_this_phase':False})
 for name,sha in [('XTRAIL-CAR.ps2model','a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac'),('XTRAIL-WHEEL-DRAW.ps2model','1c548d537acd75480515ff6d43140215638d2cd87c8b254d509dd5e6d004a31f')]:
  data=(PORT/'.assets/vehicles'/name).read_bytes()
  if h.sha256(data)!=sha:raise ValueError('Accepted X-Trail asset changed')
  assets[name]=data
 members['asset-manifest.json']=json.dumps({'schema':1,'local_runtime_assets':manifest,'accepted_xtrail_dependencies_included':True,'assets_separate_from_source_handoff':True},indent=2).encode()
 members['provenance.json']=json.dumps({'phase':'PS2-VEHICLE-FLEET-PORT1-FIX1','snapshot':'verified current working source; no unrelated changes staged or committed','head':report['current_head'],'baseline_commit':report['baseline_head'],'renderer_tree':report['renderer_tree'],'new_runtime_render_acceptance':'HEALTHY_KIA_GATE2_UNRESOLVED; FIX1_PERFORMANCE_AND_COMPACT_GLOW_RUNTIME_PENDING','builds':report['builds'],'new_build_trees':False,'new_integration_patches':False,'original_assets_in_source_zip':False},indent=2).encode()
 members['SHA256SUMS.txt']=''.join(h.sha256(v)+'  '+k+'\n' for k,v in sorted(members.items())).encode();archive=h.archive_bytes(members);h.verify_archive(archive,members)
 if archive!=h.archive_bytes(members):raise ValueError('Nondeterministic handoff')
 for name,data in [('handoff.zip',archive),('d3d8.dll',members['d3d8.dll']),('build-report.json',members['build-report.json']),('runtime-ab.md',members['RUNTIME-AB.md']),('asset-manifest.json',members['asset-manifest.json'])]:
  p=out/name
  if p.exists() and p.read_bytes()!=data and (out/'SHA256SUMS.txt').exists():raise ValueError('Refusing to replace different finalized release artifact: '+name)
  p.write_bytes(data)
 asset_dir=out/'assets';asset_dir.mkdir(exist_ok=True)
 for name,data in assets.items():
  p=asset_dir/name
  if p.exists() and p.read_bytes()!=data:raise ValueError('Existing different asset')
  p.write_bytes(data)
 runtime={'d3d8.dll':members['d3d8.dll'],'RUNTIME-AB.md':members['RUNTIME-AB.md'],'asset-manifest.json':members['asset-manifest.json'],**{'PS2Vehicles/'+n:d for n,d in assets.items()}}
 runtime['SHA256SUMS.txt']=''.join(h.sha256(v)+'  '+k+'\n' for k,v in sorted(runtime.items())).encode()
 runtime_zip=h.archive_bytes(runtime);h.verify_archive(runtime_zip,runtime);(out/'runtime-kit.zip').write_bytes(runtime_zip)
 (out/'SHA256SUMS.txt').write_text(''.join(h.sha256(p.read_bytes())+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'))
 print(json.dumps({'dll_sha256':h.sha256(members['d3d8.dll']),'handoff_sha256':h.sha256(archive),'runtime_kit_sha256':h.sha256(runtime_zip),'local_asset_count':len(assets),'extracted_focused_tests':sum(v['tests'] for v in validation),'members':len(members),'output':str(out)},indent=2))
if __name__=='__main__':main()
