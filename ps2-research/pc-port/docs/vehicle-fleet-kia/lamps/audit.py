"""Original Kia OFF/ON/glow source and bounded runtime matrix; metadata only."""
from pathlib import Path
import importlib.util,json,struct,hashlib,itertools
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=load('kia_off_corpus',PORT/'docs/full-coverage/vehicles/audit.py');c=load('kia_off_converter',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
 family=next(f for f in json.loads((PORT/'docs/vehicle-continuity2/fleet-car/fleet-car-contracts.json').read_text())['fleet'] if f['pc_family']=='KiaSportage')
 source=next(f for f in json.loads((PORT/'docs/vehicle-crew-port1/fleet/coverage.json').read_text())['fleet'] if f['pc_family']=='KiaSportage')['models']['CAR']
 a.w.verify_inputs(a.PS2);pack,_=a.t.load_pak(a.PS2/'TNG.PAK');entry=next(e for e in pack['entries'] if e.get('path','').upper()==source['resource'].upper());raw,_=a.t.read_payload(entry,a.PS2/'TNG.000');assert a.sha(raw)==family['source_ps2_car_sha256']
 scene=a.r.decode_vehicle(raw);vb=raw[32:32+scene.vertex_count*52];pcpath=a.PC/'KiaSportage/car.dx';assert a.sha(pcpath.read_bytes())==family['source_pc_car_sha256'];pc=a.parse_dx(pcpath)
 result={'schema':1,'ps2_sha256':a.sha(raw),'pc_sha256':a.sha(pcpath.read_bytes()),'meshes':[],'runtime':[]}
 for path,record in [('root.13',16),('root.25.0.0',30),('root.25.1.0',31),('root.25.1.1',32)]:
  m=next(m for m in scene.meshes if m['path']==path);ids,_=c.indices_for_mesh(vb,m)
  pts=[struct.unpack_from('<3f',vb,i*52+36) for i in ids];uv=[struct.unpack_from('<2f',vb,i*52+20) for i in ids]
  policy=next(m for m in family['source_roots'] if m['path']==path)
  if path=='root.13':
   result['meshes'].append({'path':path,'node':m['node_offset'],'material':m['material'],'mode':policy['mode'],'mixed_reflection':policy['mixed_reflection'],'conditional':False,'faces':len(ids)//3,'bounds':{'min':[min(p[k] for p in pts) for k in range(3)],'max':[max(p[k] for p in pts) for k in range(3)]},'note':'Already private unconditional source; native record21 includes additional source geometry, no direct per-record equality asserted.'});continue
  draws=source['pc_compiled_source']['draws']
  d=pc.physical_draws[record];pi=pc.draw_global_indices(d);rem=[[(pc.vertices.positions[i],pc.uv_sets[0].values[i]) for i in pi[k:k+3]] for k in range(0,len(pi),3)];errors=[]
  for k in range(0,len(ids),3):
   found=None
   for n,tri in enumerate(rem):
    for perm in itertools.permutations(tri):
     pe=max(abs(pts[k+j][q]-perm[j][0][q]) for j in range(3) for q in range(3));ue=max(abs(uv[k+j][q]-perm[j][1][q]) for j in range(3) for q in range(2))
     if pe<=.001 and ue<=.000001:found=(n,pe,ue);break
    if found:break
   assert found is not None,(path,k);rem.pop(found[0]);errors.append(found[1:])
  assert not rem
  result['meshes'].append({'path':path,'node':m['node_offset'],'material':m['material'],'mode':policy['mode'],'mixed_reflection':policy['mixed_reflection'],'conditional':policy['conditional'],'pc_record':record,'pc_record_path':draws[record]['record_path'],'faces':len(ids)//3,'vertices':draws[record]['vertices'],'geometry_sha256':a.geometry_signature(a.faces(pc,d)),'position_uv_corner_sha256':a.sha(b''.join(sorted(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in pi))),'max_position_error':max(e[0] for e in errors),'max_uv_error':max(e[1] for e in errors),'bounds':{'min':[min(p[k] for p in pts) for k in range(3)],'max':[max(p[k] for p in pts) for k in range(3)]},'ordered_texture_slots':draws[record]['ordered_texture_slots'],'source_indices':ids if path=='root.25.0.0' else []})
 logs=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')
 for f in (3336,3911,3913):
  path=logs/f'frame-10052-d1-{f:08}.jsonl';row={'frame':f,'file':path.name,'sha256':a.sha(path.read_bytes()),'conditional_shape_candidates':[]};result['runtime'].append(row)
  for line in path.open():
   d=json.loads(line)
   if d.get('type')=='frame_begin':row['proxy_sha256']=d['proxy_sha256']
   if d.get('type')!='draw' or d['caller']['return_rva']!=0x17707e:continue
   ar=d['arguments'];st=d['state']
   if not(ar[4]==12 and ar[2] in (16,20) and st['vertex_shader'] in (0x102,0x152)):continue
   row['conditional_shape_candidates'].append({'sequence_diagnostic_only':d['sequence'],'arguments':ar[:5],'fvf':st['vertex_shader'],'stride':st['streams'][0]['stride'],'object_class':d['object_class'],'reflection_candidate':d['reflection_candidate'],'reason':d['reflection_reason'],'forwarded':d['forwarded'],'texture':st['textures'][:2],'states':st['render_states'],'native_result':d['result']})
 (HERE/'source-runtime.json').write_text(json.dumps(result,indent=2)+'\n');print([(m['path'],m.get('pc_record'),m['mode'],m.get('geometry_sha256'),m.get('position_uv_corner_sha256')) for m in result['meshes']])
if __name__=='__main__':main()
