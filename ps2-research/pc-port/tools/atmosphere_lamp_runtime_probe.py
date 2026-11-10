"""Exercise LPA1 attachments using independent native-compiler index streams.

The authoring parser returns source-DX corner order. This probe deliberately
reads the stored native local index stream instead, so it reproduces the 6.18
winding regression instead of sharing the author's assumption.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,argparse
PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
p=argparse.ArgumentParser(description=__doc__)
for name in ('asset-report','ini','output','parser-root'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();OUT=a.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(a.parser_root))
from master_rallye.dx import parse_dx
source_report=a.asset_report.resolve();data=json.loads(source_report.read_text());sidecar=source_report.parent/'lamp_attachments.lpa'
with (OUT/'fixture.txt').open('w') as f:
 f.write('8\n')
 for mode in ('off','on'):
  selected={}
  for row in data['selected']:
   if mode in row['modes']:selected[row['car'],row['record']]=row
  for mutation in range(4):
   f.write(f'{int(mode=="on")} {mutation} {len(selected)}\n')
   for (car,record),row in selected.items():
    model=parse_dx(Path(data['source_root'])/car/'car.dx');draw=next(d for d in model.physical_draws if str(d.record_path)==record);indices=tuple(i+draw.vertex_base for i in model.local_indices[draw.index_start:draw.index_start+draw.index_count])
    f.write(f'{car} {row["texture_identities"][0]} {row["uv_sha256"]} {int(row["role"]=="main")} {len(model.vertices.positions)} {len(indices)}\n')
    for p,uv in zip(model.vertices.positions,model.uv_sets[0].values):f.write(' '.join(map(str,(*p,*uv)))+'\n')
    f.write(' '.join(map(str,indices))+'\n')
compiler='C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'
includes=[PORT/'.staging/baseline/modernization/renderer/include',PORT/'.staging/baseline/modernization/renderer/vendor/d3d8',PORT/'renderer']
source=PORT/'tests/lamp_attachment_runtime_probe.cpp';exe=OUT/'runtime_probe.exe'
cmd='@call "'+compiler+'" x64_x86 >nul\n@cl /nologo /std:c++17 /EHsc /O2 /MT /fp:strict '+' '.join('/I"'+str(p)+'"' for p in includes)+' "'+str(source)+'" /Fe:"'+str(exe)+'" /Fo:"'+str(OUT/'runtime_probe.obj')+'" "'+str(PORT/'.build/baseline/Release/proxy_core.lib')+'" bcrypt.lib user32.lib\n@exit /b %errorlevel%\n'
(OUT/'compile.cmd').write_text(cmd);subprocess.run(['cmd','/d','/c',str(OUT/'compile.cmd')],check=True)
subprocess.run([str(exe),str(a.ini.resolve()),str(sidecar),str(OUT/'fixture.txt'),str(OUT/'results.json')],check=True)
report=json.loads((OUT/'results.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[PORT/'renderer/atmosphere.hpp',PORT/'renderer/atmosphere_lamp_attachments.hpp',PORT/'renderer/atmosphere_lamp_surface.hpp',PORT/'renderer/atmosphere_body_general.hpp',source,Path(__file__),sidecar,OUT/'fixture.txt']
report.update(status='NATIVE_COMPILER_ORDER_RUNTIME_CODE_OFFLINE_NOT_GAMEPLAY',index_source='Stored raw local triangle stream, independent of authoring parser draw_global_indices',source_model_boundary=data['models_validated'],original_models_available=data['original_models_available'],rig_sha256=data['rig_sha256'],sha256={str(p):sha(p) for p in paths})
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
