"""All pinned CAR source-only damage indices; no original vertex bytes emitted."""
from pathlib import Path
import collections, hashlib, itertools, json, struct, sys
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]; ROOT=PORT.parents[1]
sys.path.insert(0,str(ROOT.parent/'master-rallye-re-course/src'))
def digest(b): return hashlib.sha256(b).hexdigest()
def asset_data(blob):
 _,_,meta,meshes,nv,ni,_,_=struct.unpack_from('<8s6I32s',blob);at=64+meta
 rows=[struct.unpack_from('<7I',blob,at+i*28) for i in range(meshes)];at+=meshes*28
 raw=[blob[at+i*36:at+(i+1)*36] for i in range(nv)];at+=nv*36
 return rows,raw,struct.unpack_from('<'+'I'*ni,blob,at)
def components(raw,indices):
 parent={i:i for i in set(indices)}
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def join(a,b):parent[find(a)]=find(b)
 points={}
 for i in parent:
  key=tuple(0. if x==0 else x for x in struct.unpack_from('<3f',raw[i]))
  if key in points:join(i,points[key])
  else:points[key]=i
 for at in range(0,len(indices),3):join(indices[at],indices[at+1]);join(indices[at],indices[at+2])
 groups=collections.defaultdict(list)
 for at in range(0,len(indices),3):groups[find(indices[at])].append(indices[at:at+3])
 return list(groups.values())
def component_signature(raw,faces):
 used=sorted({i for tri in faces for i in tri}); origin=struct.unpack_from('<3f',raw[used[0]])
 def corner(i):
  xyz=struct.unpack_from('<3f',raw[i]);return (tuple(round((xyz[j]-origin[j])/1e-5) for j in range(3)),raw[i][12:])
 triangles=[]
 for face in faces:
  c=[corner(i) for i in face];triangles.append(min(tuple(c[i:]+c[:i]) for i in range(3)))
 return tuple(sorted(triangles))
def run():
 from master_rallye.dx import parse_dx
 profiles=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/race-profiles.json').read_text())['profiles']
 kia=next(p for p in profiles if p['family']=='KiaSportage');kb=(PORT/'.assets/vehicles'/kia['filename']).read_bytes(); kr,kv,ki=asset_data(kb)
 static_templates=set()
 for mesh in (17,18,19):
  r=kr[mesh]
  for faces in components(kv,ki[r[5]:r[5]+r[6]]):static_templates.add(component_signature(kv,faces))
 output=[]; headers=['#pragma once','#include <cstdint>','#include <cstddef>','namespace gfx2::ps2port::fleet_damage_draft {','struct Candidate { uint16_t slot,vertex; };','struct Mapping { uint32_t vertex,first,count; };','struct Profile { const char *family,*ps2Family; uint32_t assetVertexCount,sourceCount; const Candidate *candidates; size_t candidateCount; const Mapping *mapping; size_t mappingCount; const uint32_t *staticVertices; size_t staticCount; bool eligible; };']
 for p in profiles:
  pcpath=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles'/p['family']/'car.dx'
  blob=(PORT/'.assets/vehicles'/p['filename']).read_bytes()
  assert digest(blob)==p['sha256'] and digest(pcpath.read_bytes())==p['original_pc_source_sha256']
  pc=parse_dx(pcpath); bypath={d.record_path:d for d in pc.physical_draws}; originals=[]; buckets=collections.defaultdict(list); edges=collections.defaultdict(list)
  for slot,s in enumerate(p['pc_sources']):
   d=bypath[s['record_path']]; points=pc.vertices.positions[d.vertex_base:d.vertex_base+s['vertices']]
   assert digest(b''.join(struct.pack('<3f',*v) for v in points))==s['ordered_position_sha256']
   originals.append(points)
   for i,v in enumerate(points): buckets[tuple(round(x/1e-5) for x in v)].append((slot,i))
   ids=[i-d.vertex_base for i in pc.draw_global_indices(d)]
   for at in range(0,len(ids),3):
    tri=ids[at:at+3]
    for c in range(3): edges[(slot,*sorted((tri[(c+1)%3],tri[(c+2)%3])))].append(tri[c])
  _,version,meta,meshes,vertices,indices,textures,_=struct.unpack_from('<8s6I32s',blob); assert version==2
  metadata=json.loads(blob[64:64+meta]); at=64+meta; rows=[struct.unpack_from('<7I',blob,at+i*28) for i in range(meshes)];at+=meshes*28
  positions=[struct.unpack_from('<3f',blob,at+i*36) for i in range(vertices)];at+=vertices*36; ids=struct.unpack_from('<'+'I'*indices,blob,at); referenced=set(ids)
  mapping={}; rules={}
  for v in referenced:
   point=positions[v];cell=tuple(round(x/1e-5) for x in point); choices=[]
   for off in itertools.product((-1,0,1),repeat=3):
    for slot,i in buckets.get(tuple(cell[j]+off[j] for j in range(3)),[]):
     if max(abs(originals[slot][i][j]-point[j]) for j in range(3))<=1e-5: choices.append((slot,i))
   mapping[v]=sorted(set(choices))
  # Match authored revision corners only via two already-proven neighbors.
  topology=collections.defaultdict(set)
  for at in range(0,len(ids),3):
   tri=ids[at:at+3]
   for c,v in enumerate(tri):
    if mapping[v] or tri.count(v)!=1: continue
    for a in mapping[tri[(c+1)%3]]:
     for b in mapping[tri[(c+2)%3]]:
      if a[0]!=b[0]:continue
      for i in edges.get((a[0],*sorted((a[1],b[1]))),[]):
       if max(abs(originals[a[0]][i][j]-positions[v][j]) for j in range(3))<=.005:topology[v].add((a[0],i))
  for v,candidates in topology.items():mapping[v]=sorted(candidates);rules[v]='TWO_PROVEN_NEIGHBORS_ORIGINAL_TRIANGLE'
  static=[]
  _,raw_vertices,_=asset_data(blob); static_proofs=[]
  for mesh,r in enumerate(rows):
   for faces in components(raw_vertices,ids[r[5]:r[5]+r[6]]):
    signature=component_signature(raw_vertices,faces)
    if signature in static_templates:
     vertices_in_component={i for tri in faces for i in tri};static.extend(v for v in vertices_in_component if not mapping[v])
     static_proofs.append(dict(mesh=mesh,faces=len(faces),vertices=len(vertices_in_component),rule='KIA_VERIFIED_STATIC_COMPONENT_RIGID_TRANSLATION_FULL_NORMAL_COLOR_UV_TOPOLOGY'))
  static=sorted(set(static))
  if p['family']=='KiaSportage':
   proven=json.loads((PORT/'docs/vehicle-fleet-kia/damage/kia-source-correspondence.json').read_text());static=proven['static_unmatched_crew_interior_vertices']
  unresolved=sorted(v for v in referenced if not mapping[v] and v not in static)
  diagnostics=[]
  if p['family']=='Forester':
   for v in unresolved:
    distance,slot,native_vertex=min((max(abs(point[j]-positions[v][j]) for j in range(3)),slot,i) for slot,values in enumerate(originals) for i,point in enumerate(values))
    diagnostics.append(dict(vertex=v,nearest_distance_diagnostic_only=distance,source_slot_diagnostic_only=slot,native_vertex_diagnostic_only=native_vertex,mapping_authorized=False))
  used=[{'mesh':i,'path':metadata['meshes'][i]['path'],'unmapped':sum(not mapping[v] and v not in static for v in set(ids[r[5]:r[5]+r[6]]))} for i,r in enumerate(rows)]
  signatures=collections.defaultdict(list);uv=collections.defaultdict(list)
  for i,s in enumerate(p['pc_sources']):
   signatures[(s['vertices'],s['faces'],s['ordered_position_sha256'],s['native_uv_winding_sha256'])].append(i)
   uv[(s['vertices'],s['faces'],s['native_uv_winding_sha256'])].append(i)
  duplicate=[v for v in signatures.values() if len(v)>1]; ambiguous=[v for v in uv.values() if len(v)>1]
  eligible=not unresolved and not duplicate and p['family']!='Xtrail'
  flat=[];maprows=[]
  for v in range(vertices):maprows.append((v,len(flat),len(mapping.get(v,[]))));flat.extend(mapping.get(v,[]))
  name=p['ps2_family'];headers += [f'inline constexpr Candidate {name}_candidates[]={{'+(','.join('{%du,%du}'%c for c in flat) or '{0u,0u}')+'};',f'inline constexpr Mapping {name}_mapping[]={{'+','.join('{%du,%du,%du}'%r for r in maprows)+'};',f'inline constexpr uint32_t {name}_static[]={{'+(','.join(str(v)+'u' for v in static) or '0u')+'};']
  output.append(dict(family=p['family'],ps2_family=name,asset_sha256=p['sha256'],source_count=len(p['pc_sources']),asset_vertices=vertices,referenced_vertices=len(referenced),mapped_vertices=sum(bool(mapping[v]) for v in referenced),topology_proved_vertices=len(topology),static_vertices=len(static),unresolved_vertices=unresolved,unresolved_meshes=[m for m in used if m['unmapped']],unresolved_diagnostics=diagnostics,duplicate_healthy_sources=duplicate,private_uv_ambiguity_groups=ambiguous,eligible=eligible,candidate_count=len(flat),runtime_grant=False,native_owner_required=True,static_component_proofs=static_proofs,static_rigid_relative_position_quantization=1e-5,meshes=used))
  print(p['family'],len(referenced)-len(unresolved),'/',len(referenced),'eligible',eligible,flush=True)
 runtime_headers=[line for line in headers if not line.startswith('inline constexpr') or any((' '+p['ps2_family']+'_') in line for p in output if p['eligible'])]
 headers.append('inline constexpr Profile profiles[]={')
 for p in output:
  n=p['ps2_family'];headers.append('{"%s","%s",%du,%du,%s_candidates,%du,%s_mapping,%du,%s_static,%du,%s},'%(p['family'],n,p['asset_vertices'],p['source_count'],n,p['candidate_count'],n,p['asset_vertices'],n,p['static_vertices'],str(p['eligible']).lower()))
 runtime_headers.append('inline constexpr Profile profiles[]={')
 for p in output:
  n=p['ps2_family']
  if p['eligible']:runtime_headers.append('{"%s","%s",%du,%du,%s_candidates,%du,%s_mapping,%du,%s_static,%du,true},'%(p['family'],n,p['asset_vertices'],p['source_count'],n,p['candidate_count'],n,p['asset_vertices'],n,p['static_vertices']))
  else:runtime_headers.append('{"%s","%s",%du,%du,nullptr,0,nullptr,0,nullptr,0,false},'%(p['family'],n,p['asset_vertices'],p['source_count']))
 runtime_headers+=['};','}'];(HERE/'runtime_damage_registry.hpp').write_text('\n'.join(runtime_headers)+'\n')
 headers+=['};','}'];(HERE/'fleet_damage_draft.hpp').write_text('\n'.join(headers)+'\n')
 (HERE/'contracts.json').write_text(json.dumps(dict(schema=1,profiles=output,policy='SOURCE_ONLY; EXACT_HEALTHY_OWNER_REQUIRED; UV_MATERIAL_AMBIGUITY_REQUIRES_UNCHANGED_UNIQUE_XYZ; ALL_CANDIDATE_DELTAS_CONSENSUS; UNMAPPED_FAIL_CLOSED'),indent=2)+'\n')
if __name__=='__main__':run()
