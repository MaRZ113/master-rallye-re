"""Revalidate original lamp bytes and emit metadata/ignored native fixtures only."""
from pathlib import Path
import importlib.util,json,struct
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=load('port3_lamp_source',PORT/'docs/full-coverage/vehicles/audit.py')
 converter=load('port3_lamp_converter',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
 old=json.loads((PORT/'docs/vehicle-crew-port1/lamps/source-registry.json').read_text())['families']
 extra=json.loads((PORT/'docs/vehicle-fleet-port1/lamps/missing-source-comparison.json').read_text())['families']
 contracts=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/fleet-car-contracts.json').read_text())['fleet']
 inventory={f['family']:f for f in json.loads((PORT/'docs/coverage-followup/body-lights/source-joins.json').read_text())['brake_family_inventory']}
 off={f['family']:f for f in json.loads((PORT/'docs/vehicle-fleet-kia/fleet-lamps/source-registry.json').read_text())['families']}
 a.w.verify_inputs(a.PS2);pack,_=a.t.load_pak(a.PS2/'TNG.PAK');entries={e['path'].upper():e for e in pack['entries'] if e['kind']=='file'}
 result={'schema':1,'runtime':'SOURCE_ONLY_NOT_RUNTIME_AUTHORIZATION','families':[]};fixtures=[];manifest=[];cpp=[]
 for contract in contracts:
  if 'source_roots' not in contract:continue
  family=contract['pc_family'];ps2=contract['ps2_family'];meta=inventory[ps2]
  raw,_=a.t.read_payload(entries[meta['source'].upper()],a.PS2/'TNG.000');assert a.sha(raw)==contract['source_ps2_car_sha256']==meta['sha256']
  scene=a.r.decode_vehicle(raw);source_vb=raw[32:32+scene.vertex_count*52]
  pcpath=a.PC/family/'car.dx';assert a.sha(pcpath.read_bytes())==contract['source_pc_car_sha256'];pc=a.parse_dx(pcpath)
  prior=next((f for f in extra if f['family']==ps2),None) or next(f for f in old if f['ps2_family']==ps2)
  row={'family':family,'ps2_family':ps2,'pc_sha256':a.sha(pcpath.read_bytes()),'ps2_sha256':a.sha(raw),'off_status':off[family]['status'],'on':[],'glow':[],'damaged_runtime':'Kia USER_CONFIRMED; other families REQUIRE_CURRENT_OWNER_HEALTHY_REFERENCE_AND_CLONE_PROOF'};result['families'].append(row)
  selected=set()
  for m in meta['light_meshes']:
   slots=m['texture_slots'];kind='on' if slots and slots[0].lower()=='breaklightson-tga' else 'glow' if slots and slots[0].lower()=='breaklightsonglow-tga' else None
   if kind is None:continue
   prior_mesh=next(x for x in prior['meshes'] if x['path']==m['path']);cs=prior_mesh['pc_candidates']
   if 'vertex_count' in (cs[0] if cs else {}):candidates=[c for c in cs if c['max_uv_error']==0 and c['max_position_error']<=.001]
   else:candidates=[c for c in cs if c['exact_uv_triangle_multiset'] and c['max_uv_error']==0 and c['ordered_texture_slots'][0].lower()==slots[0].lower()]
   item={'path':m['path'],'mode':m['final_mode_in_loader'],'material':m['material'],'ordered_slots':m['texture_records'],'loader_contract':m['contract'],'resources':[],'status':'SOURCE_ADMITTED' if len(candidates)==1 else 'BLOCKED_AMBIGUOUS_SOURCE'};row[kind].append(item)
   source_mesh=next(x for x in scene.meshes if x['path']==m['path']);source_ids,_=converter.indices_for_mesh(source_vb,source_mesh)
   item['original_vertex_rgba_words']=sorted({struct.unpack_from('<I',source_vb,i*52+16)[0] for i in source_ids})
   for t in m['texture_records']:
    key=a.t.logical_path('\\TNG\\DATAPSM\\'+t['name']+'.GXI').upper();entry=entries.get(key)
    if entry:
     data,_=a.t.read_payload(entry,a.PS2/'TNG.000');item['resources'].append({'slot':t['slot'],'resource':entry['path'],'sha256':a.sha(data),'bytes':len(data)})
   if len(candidates)!=1:continue
   c=candidates[0];n=c['record'];d=pc.physical_draws[n];ids=pc.draw_global_indices(d);first=min(ids);count=max(ids)-first+1
   item.update(record=n,vertices=count,triangles=len(ids)//3,geometry=a.geometry_signature(a.faces(pc,d)),positionUv=a.sha(b''.join(sorted(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in ids))),max_source_xyz_difference=c['max_position_error'],native_ordered_slots=contract.get('native_sources',[])[n]['ordered_texture_slots'] if n<len(contract.get('native_sources',[])) else None)
   item['source_uv_index_topology']=a.sha(b''.join(struct.pack('<2f',*pc.uv_sets[0].values[i]) for i in range(first,first+count))+struct.pack('<%dI'%len(ids),*(i-first for i in ids)))
   selected.add(n)
   if kind=='on':cpp.append(' {"%s",%du,%du,"%s","%s"},'%(family,count,len(ids)//3,item['geometry'],item['positionUv']))
  on_records={m['record'] for m in row['on'] if m['status']=='SOURCE_ADMITTED'}
  glow_records={m['record'] for m in row['glow'] if m['status']=='SOURCE_ADMITTED'}
  for n,d in enumerate(pc.physical_draws):
   ids=pc.draw_global_indices(d);first=min(ids);count=max(ids)-first+1
   # Compact102 is explicit adapter fixture, not a claim about a live family upload.
   vb=b''.join(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in range(first,first+count));ib=struct.pack('<%dI'%len(ids),*(i-first for i in ids))
   kind=1 if n in on_records else 2 if n in glow_records else 3
   fixtures.append(struct.pack('<4I',kind,count,len(ids)//3,20)+vb+ib);manifest.append({'family':family,'record':n,'kind':kind})
 binary=b'PS2LMP01'+struct.pack('<I',len(fixtures))+b''.join(fixtures);out=PORT/'.assets/vehicles/port3-lamps-compact.bin';out.write_bytes(binary)
 (HERE/'source-registry.json').write_text(json.dumps(result,indent=2)+'\n')
 (HERE/'fixture-manifest.json').write_text(json.dumps({'path':str(out),'bytes':len(binary),'sha256':a.sha(binary),'format':'PS2LMP01 stride20/FVF102 INDEX32; kind1 ONpositive kind2 glowpositive kind3 negative','live_upload':False,'cases':manifest},indent=2)+'\n')
 (HERE/'fleet_on_registry_draft.hpp').write_text('#pragma once\nnamespace gfx2::ps2port {\nstruct FleetOnProfile {const char* family;unsigned vertices,triangles;const char* geometry;const char* positionUv;};\ninline constexpr FleetOnProfile kFleetOnProfiles[]={\n'+'\n'.join(cpp)+'\n};\n}\n')
 print([(r['family'],[(m['mode'],m['status']) for m in r['on']],r['off_status']) for r in result['families']]);print('ON',len(cpp),'fixtures',len(fixtures))
if __name__=='__main__':main()
