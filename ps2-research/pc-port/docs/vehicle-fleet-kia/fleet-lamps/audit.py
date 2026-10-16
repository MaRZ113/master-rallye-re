"""Source-only exact conditional OFF lamp inventory; no renderer edits."""
from pathlib import Path
import importlib.util,json,struct,itertools,hashlib
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=load('fleet_off_source',PORT/'docs/full-coverage/vehicles/audit.py');c=load('fleet_off_converter',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
 contracts=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/fleet-car-contracts.json').read_text())['fleet'];corpus={f['ps2_family']:f for f in json.loads((PORT/'docs/vehicle-crew-port1/fleet/coverage.json').read_text())['fleet']}
 a.w.verify_inputs(a.PS2);pack,_=a.t.load_pak(a.PS2/'TNG.PAK');entries={e['path'].upper():e for e in pack['entries'] if e['kind']=='file'}
 result={'schema':1,'runtime_validation':'SOURCE_ONLY; UNKNOWN_OR_DEFORMED_UPLOADS_STOCK','families':[]}
 for f in contracts:
  if 'source_roots' not in f:continue
  cr=corpus[f['ps2_family']]['models']['CAR'];raw,_=a.t.read_payload(entries[cr['resource'].upper()],a.PS2/'TNG.000');assert a.sha(raw)==f['source_ps2_car_sha256'];scene=a.r.decode_vehicle(raw);vb=raw[32:32+scene.vertex_count*52]
  pcpath=a.PC/f['pc_family']/'car.dx';assert a.sha(pcpath.read_bytes())==f['source_pc_car_sha256'];pc=a.parse_dx(pcpath);draws=cr['pc_compiled_source']['draws']
  # Original blight owner label identifies the native conditional family, never a draw ordinal.
  native=[(n,d) for n,d in enumerate(draws) if d['group_label']=='blight']
  row={'family':f['pc_family'],'ps2_family':f['ps2_family'],'pc_sha256':a.sha(pcpath.read_bytes()),'ps2_sha256':a.sha(raw),'candidates':[]};result['families'].append(row)
  glow_parents={m['path'].rsplit('.',2)[0] for m in scene.meshes if any('breaklightsonglow' in t['name'].lower() for t in m['textures']) and m['path'].count('.')>=3}
  for policy in f['source_roots']:
   path=policy['path']
   if not(policy['conditional'] and policy['mode']==3 and policy['mixed_reflection'] and path.rsplit('.',2)[0] in glow_parents):continue
   mesh=next(m for m in scene.meshes if m['path']==path);ids,_=c.indices_for_mesh(vb,mesh);pts=[struct.unpack_from('<3f',vb,i*52+36) for i in ids];uv=[struct.unpack_from('<2f',vb,i*52+20) for i in ids]
   out={'ps2_path':path,'ps2_node':mesh['node_offset'],'mode':3,'material':mesh['material'],'faces':len(ids)//3,'candidates':[],'uv_exclusions':[]};row['candidates'].append(out)
   for n,meta in native:
    # Some authorings put OFF in child1 and ON at the group root.
    options=[(n,meta)]+[(j,d) for j,d in enumerate(draws) if d['record_path'].startswith(meta['record_path']+'.')]
    for record,dm in options:
     d=pc.physical_draws[record];pi=pc.draw_global_indices(d)
     if len(pi)!=len(ids):continue
     remaining=[[(pc.vertices.positions[i],pc.uv_sets[0].values[i]) for i in pi[k:k+3]] for k in range(0,len(pi),3)];errors=[]
     for k in range(0,len(ids),3):
      best=None
      for ri,tri in enumerate(remaining):
       for perm in itertools.permutations(tri):
        pe=max(abs(pts[k+j][q]-perm[j][0][q]) for j in range(3) for q in range(3));ue=max(abs(uv[k+j][q]-perm[j][1][q]) for j in range(3) for q in range(2))
        if ue>.000001:continue
        if best is None or (pe,ri)<(best[0],best[1]):best=(pe,ri,ue)
      if best is None:break
      errors.append((best[0],best[2]));remaining.pop(best[1])
     if remaining or len(errors)!=len(ids)//3:
      # Explain rejected matching authored primary without admitting by its name.
      primary=mesh['textures'][0]['name'].replace('\\','/').rsplit('/',1)[-1]
      if dm['ordered_texture_slots'][0].lower()==primary.lower():
       rest=[[(pc.vertices.positions[i],pc.uv_sets[0].values[i]) for i in pi[k:k+3]] for k in range(0,len(pi),3)];uv_errors=[]
       for k in range(0,len(ids),3):
        best=None
        for ri,tri in enumerate(rest):
         for perm in itertools.permutations(tri):
          pe=max(abs(pts[k+j][q]-perm[j][0][q]) for j in range(3) for q in range(3));ue=max(abs(uv[k+j][q]-perm[j][1][q]) for j in range(3) for q in range(2))
          if pe<=.001 and (best is None or ue<best[0]):best=(ue,ri)
        if best is None:break
        uv_errors.append(best[0]);rest.pop(best[1])
       if not rest:out['uv_exclusions'].append({'record':record,'max_uv_residual_with_exact_geometry':max(uv_errors)})
      continue
     out['candidates'].append({'record':record,'record_path':dm['record_path'],'vertices':dm['vertices'],'faces':dm['faces'],'ordered_texture_slots':dm['ordered_texture_slots'],'geometry':a.geometry_signature(a.faces(pc,d)),'positionUv':a.sha(b''.join(sorted(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in pi))),'max_position_error':max(e[0] for e in errors),'max_uv_error':max(e[1] for e in errors),'runtime_guard_exact':True})
  admitted=[(m,m['candidates'][0]) for m in row['candidates'] if len(m['candidates'])==1 and m['candidates'][0]['max_position_error']<=.001]
  row['status']='SOURCE_ADMITTED' if len(admitted)==1 else 'BLOCKED_NO_EXACT_OFF_PAIR'
  if len(admitted)==1:row['profile']=dict(admitted[0][1],ps2_path=admitted[0][0]['ps2_path'])
  elif row['candidates']:row['blocker']='Original XYZ revision exceeds .001 or source pair ambiguous; no tolerance relaxation.'
  else:row['blocker']='No independently verified conditional OFF carshiny/mixed source.'
  # All other sources, including ON and glow, remain explicit hash negatives.
  row['negative_sources']=[]
  for n,d in enumerate(draws):
   if row.get('profile',{}).get('record')==n:continue
   corners=sorted(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in pc.draw_global_indices(pc.physical_draws[n]))
   row['negative_sources'].append({'record':n,'geometry':d['geometry_sha256'],'positionUv':a.sha(b''.join(corners))})
 (HERE/'source-registry.json').write_text(json.dumps(result,indent=2)+'\n');print([(f['family'],f['status'],[(m['ps2_path'],[(x['record'],x['max_position_error']) for x in m['candidates']]) for m in f['candidates']]) for f in result['families']])
if __name__=='__main__':main()
