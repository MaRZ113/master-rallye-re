"""Bounded source conditional identity audit; no geometry or proprietary images output."""
from pathlib import Path
import importlib.util,json,hashlib,struct
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def run():
 a=load('conditional_source',PORT/'docs/full-coverage/vehicles/audit.py')
 old=json.loads((HERE.parent/'assets/pc-source-map.json').read_text())['car']
 path=a.PC/'Xtrail/car.dx';assert a.sha(path.read_bytes())==old['pc_sha256'];pc=a.parse_dx(path)
 root=a.PS2;pack,_=a.t.load_pak(root/'TNG.PAK');entry=next(e for e in pack['entries'] if e['path'].upper().endswith('XTRAIL\\CAR.PSM'));raw,_=a.t.read_payload(entry,root/'TNG.000');assert a.sha(raw)==old['ps2_sha256'];scene=a.r.decode_vehicle(raw)
 c=load('conditional_converter',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
 meshes=[]
 for m in scene.meshes:
  if m['path'].count('.')<2:continue
  ids,_=c.indices_for_mesh(raw[32:32+scene.vertex_count*52],m)
  # Exact corner-attribute multiset, source f32, preserves duplicated corners.
  attrs=[struct.pack('<3f3f2f',*struct.unpack_from('<3f',raw,32+i*52+36),*struct.unpack_from('<3f',raw,32+i*52),*struct.unpack_from('<2f',raw,32+i*52+20)) for i in ids]
  meshes.append(dict(path=m['path'],node=m['node_offset'],material=m['material'],slots=m['textures'],faces=len(ids)//3,attribute_corner_sha256=a.sha(b''.join(sorted(attrs)))))
 rows=[]
 for row in old['draws']:
  if row['source_draw']<23:continue
  d=pc.physical_draws[row['source_draw']];ids=pc.draw_global_indices(d)
  attrs=[struct.pack('<3f3f2f',*pc.vertices.positions[i],*pc.vertices.normals[i],*pc.uv_sets[0].values[i]) for i in ids]
  rows.append({k:row[k] for k in ('source_draw','vertex_base','vertex_count','index_start','index_count','geometry_sha256','source_uv0_sha256','source_normal_sha256','slots','flags_hex','bindings')}|{'attribute_corner_sha256':a.sha(b''.join(sorted(attrs)))})
 observations=[]
 for frame in (1657,1786,4453):
  f=Path(f'D:/Game/Master Rallye Pristine/MRRRenderer/logs/frame-27136-d1-{frame:08d}.jsonl');records=[json.loads(l) for l in f.read_text().splitlines()];matches=[]
  for q in records:
   if q.get('type')!='draw' or q.get('method')!='DrawIndexedPrimitive':continue
   args=q['arguments'];candidates=[r['source_draw'] for r in rows if r['vertex_count']==args[2] and r['index_count']//3==args[4]]
   if not candidates:continue
   st=q['state'];matches.append(dict(draw=q['draw_index'],sequence=q['sequence'],args=args,candidates=candidates,object_class=q.get('object_class'),native_render_states=st.get('render_states'),texture_stages=st.get('texture_stage_states'),textures=st.get('textures'),world=st.get('matrices',{}).get('256')))
  observations.append(dict(frame=frame,sha256=a.sha(f.read_bytes()),matches=matches))
 out=dict(pc_sha256=old['pc_sha256'],ps2_sha256=old['ps2_sha256'],ps2_meshes=meshes,pc_records=rows,observations=observations,identity_limit='F10 count/range candidates are NOT current upload/resource proof; original source signatures require current owner and generations.')
 (HERE/'registry-candidates.json').write_text(json.dumps(out,indent=2)+'\n');print('conditional records',len(rows),'meshes',len(meshes),'live candidates',[len(o['matches']) for o in observations])
if __name__=='__main__':run()
