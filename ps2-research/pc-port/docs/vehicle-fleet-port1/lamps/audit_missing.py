"""Read original authored lamp branches. Metadata only, no assets or renderer edits."""
from pathlib import Path
import importlib.util,json,struct,itertools,hashlib
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=load('fleet_lamp_source',PORT/'docs/full-coverage/vehicles/audit.py')
 c=load('fleet_lamp_converter',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
 old=json.loads((PORT/'docs/vehicle-crew-port1/lamps/source-registry.json').read_text())
 fleet={f['ps2_family']:f for f in json.loads((PORT/'docs/vehicle-crew-port1/fleet/coverage.json').read_text())['fleet']}
 a.w.verify_inputs(a.PS2);pack,_=a.t.load_pak(a.PS2/'TNG.PAK');entries={e['path'].upper():e for e in pack['entries'] if e['kind']=='file'}
 inventory=json.loads((PORT/'docs/coverage-followup/body-lights/source-joins.json').read_text())['brake_family_inventory']
 result={'schema':1,'evidence':'ORIGINAL_SOURCE_ONLY_NOT_RUNTIME','families':[]}
 for family in ('FRONTERA','JUMP','MATTSERATI','RMONSTER','TATA'):
  src=next(f for f in inventory if f['family']==family);raw,_=a.t.read_payload(entries[src['source'].upper()],a.PS2/'TNG.000');assert a.sha(raw)==src['sha256']
  scene=a.r.decode_vehicle(raw);verts=raw[32:32+scene.vertex_count*52]
  pcpath=next(p for p in a.PC.iterdir() if p.name.upper()==family)/'car.dx'
  assert a.sha(pcpath.read_bytes())==fleet[family]['models']['CAR']['pc_compiled_source']['sha256']
  pc=a.parse_dx(pcpath)
  row={'family':family,'ps2_sha256':a.sha(raw),'pc_sha256':a.sha(pcpath.read_bytes()),'meshes':[]};result['families'].append(row)
  for meta in src['light_meshes']:
   mesh=next(m for m in scene.meshes if m['path']==meta['path']);ids,_=c.indices_for_mesh(verts,mesh)
   ps=[struct.unpack_from('<3f',verts,i*52+36) for i in ids];uv=[struct.unpack_from('<2f',verts,i*52+20) for i in ids]
   uv_tri=lambda values:sorted(b''.join(sorted(struct.pack('<2f',*v) for v in values[n:n+3])) for n in range(0,len(values),3))
   out={'path':meta['path'],'mode':meta['final_mode_in_loader'],'slots':meta['texture_slots'],'faces':len(ids)//3,'vertex_count':len(set(ids)),'pc_candidates':[]};row['meshes'].append(out)
   out['ps2_uv_triangle_sha256']=a.sha(b''.join(uv_tri(uv)))
   for n,d in enumerate(pc.physical_draws):
    di=pc.draw_global_indices(d)
    if len(di)!=len(ids):continue
    remaining=[[(pc.vertices.positions[i],pc.uv_sets[0].values[i]) for i in di[k:k+3]] for k in range(0,len(di),3)]
    errors=[]
    for k in range(0,len(ids),3):
     best=None
     for ri,tri in enumerate(remaining):
      for p in itertools.permutations(tri):
       pe=max(abs(ps[k+j][q]-p[j][0][q]) for j in range(3) for q in range(3))
       ue=max(abs(uv[k+j][q]-p[j][1][q]) for j in range(3) for q in range(2))
       score=(pe,ue,ri)
       if best is None or score<best:best=score
     if best is None:break
     errors.append(best[:2]);remaining.pop(best[2])
    if remaining or not errors:continue
    pcmeta=fleet[family]['models']['CAR']['pc_compiled_source']['draws'][n]
    uvhash=a.sha(b''.join(uv_tri([pc.uv_sets[0].values[i] for i in di])))
    out['pc_candidates'].append({'record':n,'vertices':len(set(di)),'max_position_error':max(e[0] for e in errors),'max_uv_error':max(e[1] for e in errors),'geometry_sha256':a.geometry_signature(a.faces(pc,d)),'position_uv_corner_sha256':a.sha(b''.join(sorted(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in di))),'uv_triangle_sha256':uvhash,'exact_uv_triangle_multiset':uvhash==out['ps2_uv_triangle_sha256'],'record_path':pcmeta['record_path'],'ordered_texture_slots':pcmeta['ordered_texture_slots']})
   out['pc_candidates'].sort(key=lambda r:(r['max_position_error'],r['max_uv_error']))
 (HERE/'missing-source-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 for f in result['families']:
  print(f['family'],[(m['path'],m['mode'],m['faces'],m['pc_candidates'][:2]) for m in f['meshes']])
if __name__=='__main__':main()
