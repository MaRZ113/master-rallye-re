"""Bounded original lamp corpus join; compact identities only, no assets emitted."""
from pathlib import Path
import importlib.util, json, itertools, struct
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=load('lamp_corpus_source',PORT/'docs/full-coverage/vehicles/audit.py')
 c=load('lamp_converter',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
 old=json.loads((PORT/'docs/coverage-followup/body-lights/source-joins.json').read_text())['brake_family_inventory']
 a.w.verify_inputs(a.PS2);pack,_=a.t.load_pak(a.PS2/'TNG.PAK');entries={e['path'].upper():e for e in pack['entries'] if e['kind']=='file'}
 pcdirs={p.name.upper():p for p in a.PC.iterdir() if p.is_dir()}
 result={'schema':1,'runtime':'SOURCE_CANDIDATES_NOT_RUNTIME_ADMISSION','families':[]}
 for source in old:
  raw,_=a.t.read_payload(entries[source['source'].upper()],a.PS2/'TNG.000');assert a.sha(raw)==source['sha256']
  scene=a.r.decode_vehicle(raw);verts=raw[32:32+scene.vertex_count*52]
  family=source['family'];pcdir=None if family=='FORESTER' else pcdirs.get('FORESTER' if family=='WOOLDAND' else family)
  row={'ps2_family':family,'ps2_sha256':source['sha256'],'pc_family':pcdir.name if pcdir else None,'meshes':[]};result['families'].append(row)
  pc=a.parse_dx(pcdir/'car.dx') if pcdir and (pcdir/'car.dx').exists() else None
  if pc:row['pc_sha256']=a.sha((pcdir/'car.dx').read_bytes())
  metas=list(source['light_meshes'])
  if family=='XTRAIL':
   for extra in ('root.20.0.0','root.5','root.11'):
    m=next(m for m in scene.meshes if m['path']==extra)
    metas.append({'path':extra,'node_offset':m['node_offset'],'final_mode_in_loader':3,'texture_slots':[t['name'] for t in m['textures']],'conditional_named_child':extra.count('.')>1})
  for meta in metas:
   mesh=next(m for m in scene.meshes if m['path']==meta['path']);ids,_=c.indices_for_mesh(verts,mesh)
   mode=meta['final_mode_in_loader'];out={'path':meta['path'],'node':meta['node_offset'],'mode':mode,'faces':len(ids)//3,'slots':meta['texture_slots'],'conditional':meta['conditional_named_child'],'pc_candidates':[]};row['meshes'].append(out)
   positions=[struct.unpack_from('<3f',verts,i*52+36) for i in ids];uv=[struct.unpack_from('<2f',verts,i*52+20) for i in ids]
   out['bounds']={'min':[min(p[k] for p in positions) for k in range(3)],'max':[max(p[k] for p in positions) for k in range(3)]}
   if not pc:continue
   triangles=[list(zip(positions[n:n+3],uv[n:n+3])) for n in range(0,len(ids),3)]
   for draw in pc.physical_draws:
    pids=pc.draw_global_indices(draw)
    if len(pids)!=len(ids):continue
    pfaces=[[(pc.vertices.positions[i],pc.uv_sets[0].values[i]) for i in pids[n:n+3]] for n in range(0,len(pids),3)]
    remaining=list(pfaces);errors=[]
    for tri in triangles:
     found=None
     for index,pface in enumerate(remaining):
      for perm in itertools.permutations(pface):
       pe=max(abs(tri[i][0][k]-perm[i][0][k]) for i in range(3) for k in range(3));ue=max(abs(tri[i][1][k]-perm[i][1][k]) for i in range(3) for k in range(2))
       if pe<=.001 and ue<=.000001:found=(index,pe,ue);break
      if found:break
     if found is None:break
     remaining.pop(found[0]);errors.append(found[1:])
    if remaining:continue
    attrs=[struct.pack('<3f3f2f',*pc.vertices.positions[i],*pc.vertices.normals[i],*pc.uv_sets[0].values[i]) for i in pids]
    out['pc_candidates'].append({'record':list(pc.physical_draws).index(draw),'vertex_count':len(set(pids)),'index_count':len(pids),'attribute_sha256':a.sha(b''.join(sorted(attrs))),'position_uv_corner_sha256':a.sha(b''.join(sorted(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in pids))),'max_position_error':max(e[0] for e in errors),'max_uv_error':max(e[1] for e in errors)})
   if family=='XTRAIL':out['source_indices']=ids
 (HERE/'source-registry.json').write_text(json.dumps(result,indent=2)+'\n')
 print('families',len(result['families']),'meshes',sum(len(f['meshes']) for f in result['families']))
if __name__=='__main__':main()
