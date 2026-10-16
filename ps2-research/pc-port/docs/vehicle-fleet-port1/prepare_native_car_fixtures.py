"""Reproduce native-layout source certificates from immutable retail DX (not runtime evidence)."""
from pathlib import Path
import importlib.util,json,struct,hashlib
HERE=Path(__file__).resolve().parent;PORT=HERE.parents[1]
s=importlib.util.spec_from_file_location('original_car_sources',PORT/'docs/vehicle-continuity2/fleet-car/prepare_contracts.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
 profiles=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/race-profiles.json').read_text())['profiles'];cases=[]
 for fi,p in enumerate(profiles):
  path=m.PC/p['family']/'car.dx';raw=path.read_bytes()
  if m.sha(raw)!=p['original_pc_source_sha256']:raise ValueError('Original PC source changed')
  model=m.parse_dx(path);draws={d.record_path:d for d in model.physical_draws}
  for si,source in enumerate(p['pc_sources']):
   d=draws[source['record_path']];n=source['vertices'];ids=model.draw_global_indices(d);faces=[ids[i:i+3] for i in range(0,len(ids),3)]
   vb=b''.join(struct.pack('<3fI2f',*model.vertices.positions[d.vertex_base+i],0xffffffff,*model.uv_sets[0].values[d.vertex_base+i]) for i in range(n))
   # Original native compiler reverses the first two corners; do not change UV order.
   ib=b''.join(struct.pack('<3I',f[1]-d.vertex_base,f[0]-d.vertex_base,f[2]-d.vertex_base) for f in faces)
   cases.append(struct.pack('<4I',fi,si,n,len(faces))+vb+ib)
 data=b'FLEETPC1'+struct.pack('<I',len(cases))+b''.join(cases);out=PORT/'.assets/vehicles/fleet-port1-native-car.bin';out.write_bytes(data)
 (HERE/'native-car-fixtures.json').write_text(json.dumps({'schema':1,'bytes':len(data),'sha256':m.sha(data),'families':25,'cases':len(cases),'native_layout':'FVF142,stride24,IDX32,source-local,compiler-swapped winding','runtime_evidence':False},indent=2)+'\n');print(m.sha(data),len(cases))
if __name__=='__main__':main()
