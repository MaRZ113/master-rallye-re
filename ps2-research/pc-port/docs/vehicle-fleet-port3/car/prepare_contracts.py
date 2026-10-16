"""All pinned CAR source-only damage indices; no original vertex bytes emitted."""
from pathlib import Path
import collections, hashlib, itertools, json, math, struct, sys
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
TRANSFER_LIMIT=.05  # DAMAGE2 option A: metres from the healthy PC surface
MIXED_LIMIT=.08  # components that also contain exact vertices (their own PC surface patch)
def _sub(a,b):return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _dot(a,b):return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def closest_on_triangle(p,a,b,c):
 ab,ac,ap=_sub(b,a),_sub(c,a),_sub(p,a);d1,d2=_dot(ab,ap),_dot(ac,ap)
 if d1<=0 and d2<=0:w=(1.,0.,0.)
 else:
  bp=_sub(p,b);d3,d4=_dot(ab,bp),_dot(ac,bp);cp=_sub(p,c);d5,d6=_dot(ab,cp),_dot(ac,cp)
  vc,vb,va=d1*d4-d3*d2,d5*d2-d1*d6,d3*d6-d5*d4
  if d3>=0 and d4<=d3:w=(0.,1.,0.)
  elif d6>=0 and d5<=d6:w=(0.,0.,1.)
  elif vc<=0 and d1>=0 and d3<=0:t=d1/(d1-d3);w=(1-t,t,0.)
  elif vb<=0 and d2>=0 and d6<=0:t=d2/(d2-d6);w=(1-t,0.,t)
  elif va<=0 and d4-d3>=0 and d5-d6>=0:t=(d4-d3)/((d4-d3)+(d5-d6));w=(0.,1-t,t)
  else:den=1./(va+vb+vc);v,x=vb*den,vc*den;w=(1-v-x,v,x)
 q=tuple(w[0]*a[j]+w[1]*b[j]+w[2]*c[j] for j in range(3));return math.dist(p,q),w
class SurfaceIndex:
 """Healthy PC source triangles of one family for nearest-surface transfer."""
 CELL=.25
 def __init__(self,slot_tris,originals):
  self.tris=[];self.grid=collections.defaultdict(list)
  for slot,tris in enumerate(slot_tris):
   for a,b,c in tris:
    A,B,C=originals[slot][a],originals[slot][b],originals[slot][c];u,v=_sub(B,A),_sub(C,A);n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    if _dot(n,n)<=1e-24:continue  # degenerate triangles carry no surface
    t=len(self.tris);self.tris.append((slot,a,b,c,A,B,C))
    lo=[math.floor(min(A[j],B[j],C[j])/self.CELL) for j in range(3)];hi=[math.floor(max(A[j],B[j],C[j])/self.CELL) for j in range(3)]
    for x in range(lo[0],hi[0]+1):
     for y in range(lo[1],hi[1]+1):
      for z in range(lo[2],hi[2]+1):self.grid[(x,y,z)].append(t)
 def nearest(self,p):
  c0=[math.floor(p[j]/self.CELL) for j in range(3)];best=(math.inf,None,None)
  for r in (1,2,4,8):
   seen=set()
   for x in range(c0[0]-r,c0[0]+r+1):
    for y in range(c0[1]-r,c0[1]+r+1):
     for z in range(c0[2]-r,c0[2]+r+1):
      for t in self.grid.get((x,y,z),()):
       if t in seen:continue
       seen.add(t);d,w=closest_on_triangle(p,*self.tris[t][4:])
       if d<best[0] or (d==best[0] and t<best[1]):best=(d,t,w)
   if best[0]<=r*self.CELL:break
  d,t,w=best;slot,a,b,c=self.tris[t][:4];return d,slot,a,b,c,w
def run():
 from master_rallye.dx import parse_dx
 profiles=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/race-profiles.json').read_text())['profiles']
 kia=next(p for p in profiles if p['family']=='KiaSportage');kb=(PORT/'.assets/vehicles'/kia['filename']).read_bytes(); kr,kv,ki=asset_data(kb)
 static_templates=set()
 for mesh in (17,18,19):
  r=kr[mesh]
  for faces in components(kv,ki[r[5]:r[5]+r[6]]):static_templates.add(component_signature(kv,faces))
 output=[]; headers=['#pragma once','#include <cstdint>','#include <cstddef>','namespace gfx2::ps2port::fleet_damage_draft {','struct Candidate { uint16_t slot,vertex; };','struct Mapping { uint32_t vertex,first,count; };','// Surface-bound transfer: displacement = wa*d(a)+wb*d(b)+wc*d(c) of one healthy PC source triangle (DAMAGE2 option A).','struct Transfer { uint32_t vertex; uint16_t slot,a,b,c; float wa,wb,wc; };','struct Profile { const char *family,*ps2Family; uint32_t assetVertexCount,sourceCount; const Candidate *candidates; size_t candidateCount; const Mapping *mapping; size_t mappingCount; const uint32_t *staticVertices; size_t staticCount; bool eligible; const Transfer *transfers; size_t transferCount; float maxTransferDistance; };']
 for p in profiles:
  pcpath=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles'/p['family']/'car.dx'
  blob=(PORT/'.assets/vehicles'/p['filename']).read_bytes()
  assert digest(blob)==p['sha256'] and digest(pcpath.read_bytes())==p['original_pc_source_sha256']
  pc=parse_dx(pcpath); bypath={d.record_path:d for d in pc.physical_draws}; originals=[]; buckets=collections.defaultdict(list); edges=collections.defaultdict(list)
  slot_tris=[]
  for slot,s in enumerate(p['pc_sources']):
   d=bypath[s['record_path']]; points=pc.vertices.positions[d.vertex_base:d.vertex_base+s['vertices']]
   assert digest(b''.join(struct.pack('<3f',*v) for v in points))==s['ordered_position_sha256']
   originals.append(points)
   for i,v in enumerate(points): buckets[tuple(round(x/1e-5) for x in v)].append((slot,i))
   ids=[i-d.vertex_base for i in pc.draw_global_indices(d)];slot_tris.append([tuple(ids[k:k+3]) for k in range(0,len(ids),3)])
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
  exact_unresolved=unresolved;transfer={};rigid=set();blocked=[];rigid_components=[];widened=set();widened_components=[]
  if unresolved and p['family'] not in ('Xtrail','KiaSportage'):
   # Option A: a component with an exact source vertex may only add surface-bound vertices (<=TRANSFER_LIMIT);
   # a PS2-only component (no exact vertex) is wholly surface-bound or wholly rigid; anything else blocks the family.
   surface=SurfaceIndex(slot_tris,originals);pending=set(unresolved)
   for mesh,r in enumerate(rows):
    for faces in components(raw_vertices,ids[r[5]:r[5]+r[6]]):
     verts={i for tri in faces for i in tri};todo=sorted(verts&pending)
     if not todo:continue
     near={v:surface.nearest(positions[v]) for v in todo};inside=all(near[v][0]<=TRANSFER_LIMIT for v in todo);ps2_only=not any(mapping[v] for v in verts)
     if inside:transfer.update(near)
     elif ps2_only:rigid.update(todo);rigid_components.append(dict(mesh=mesh,path=metadata['meshes'][mesh]['path'],vertices=len(todo),beyond_limit=sum(near[v][0]>TRANSFER_LIMIT for v in todo),max_distance=max(near[v][0] for v in todo),center=[sum(positions[v][j] for v in todo)/len(todo) for j in range(3)]))
     else:
      # Mixed component (has exact vertices): surface-bound transfer up to MIXED_LIMIT so the piece follows its own
      # PC surface; the tighter TRANSFER_LIMIT keeps PS2-only crew rigid. Beyond MIXED_LIMIT the family fails closed.
      if all(near[v][0]<=MIXED_LIMIT for v in todo):
       transfer.update(near);widened.update(v for v in todo if near[v][0]>TRANSFER_LIMIT)
       if any(near[v][0]>TRANSFER_LIMIT for v in todo):widened_components.append(dict(mesh=mesh,component_vertices=len(verts),unresolved=len(todo),beyond_transfer_limit=sum(near[v][0]>TRANSFER_LIMIT for v in todo),max_distance=max(near[v][0] for v in todo)))
      else:blocked.append(dict(mesh=mesh,component_vertices=len(verts),unresolved=len(todo),beyond_limit=sum(near[v][0]>MIXED_LIMIT for v in todo),max_distance=max(near[v][0] for v in todo)))
   rigid-=set(transfer);unresolved=sorted(v for v in unresolved if v not in transfer and v not in rigid)
  diagnostics=[]
  if p['family']=='Forester':
   for v in exact_unresolved:
    distance,slot,native_vertex=min((max(abs(point[j]-positions[v][j]) for j in range(3)),slot,i) for slot,values in enumerate(originals) for i,point in enumerate(values))
    diagnostics.append(dict(vertex=v,nearest_distance_diagnostic_only=distance,source_slot_diagnostic_only=slot,native_vertex_diagnostic_only=native_vertex,mapping_authorized=False))
  used=[{'mesh':i,'path':metadata['meshes'][i]['path'],'unmapped':sum(not mapping[v] and v not in static for v in set(ids[r[5]:r[5]+r[6]]))} for i,r in enumerate(rows)]
  signatures=collections.defaultdict(list);uv=collections.defaultdict(list)
  for i,s in enumerate(p['pc_sources']):
   signatures[(s['vertices'],s['faces'],s['ordered_position_sha256'],s['native_uv_winding_sha256'])].append(i)
   uv[(s['vertices'],s['faces'],s['native_uv_winding_sha256'])].append(i)
  duplicate=[v for v in signatures.values() if len(v)>1]; ambiguous=[v for v in uv.values() if len(v)>1]
  eligible=not unresolved and not blocked and not duplicate and p['family']!='Xtrail'
  flat=[];maprows=[]
  for v in range(vertices):maprows.append((v,len(flat),len(mapping.get(v,[]))));flat.extend(mapping.get(v,[]))
  runtime_static=sorted(set(static)|rigid);max_transfer=max((t[0] for t in transfer.values()),default=0.)
  name=p['ps2_family'];headers += [f'inline constexpr Candidate {name}_candidates[]={{'+(','.join('{%du,%du}'%c for c in flat) or '{0u,0u}')+'};',f'inline constexpr Mapping {name}_mapping[]={{'+','.join('{%du,%du,%du}'%r for r in maprows)+'};',f'inline constexpr uint32_t {name}_static[]={{'+(','.join(str(v)+'u' for v in runtime_static) or '0u')+'};',f'inline constexpr Transfer {name}_transfers[]={{'+(','.join('{%du,%du,%du,%du,%du,%sf,%sf,%sf}'%(v,t[1],t[2],t[3],t[4],repr(float(t[5][0])),repr(float(t[5][1])),repr(float(t[5][2]))) for v,t in sorted(transfer.items())) or '{0u,0u,0u,0u,0u,0.f,0.f,0.f}')+'};']
  output.append(dict(family=p['family'],ps2_family=name,asset_sha256=p['sha256'],source_count=len(p['pc_sources']),asset_vertices=vertices,referenced_vertices=len(referenced),mapped_vertices=sum(bool(mapping[v]) for v in referenced),topology_proved_vertices=len(topology),static_vertices=len(static),rigid_component_vertices=len(rigid),transfer_vertices=len(transfer),max_transfer_distance=max_transfer,transfer_limit=TRANSFER_LIMIT,transfer_blocked_components=blocked,mixed_limit=MIXED_LIMIT,widened_vertices=len(widened),widened_components=widened_components,rigid_components=rigid_components,exact_unresolved_vertices=len(exact_unresolved),unresolved_vertices=unresolved,unresolved_meshes=[m for m in used if m['unmapped']],unresolved_diagnostics=diagnostics,duplicate_healthy_sources=duplicate,private_uv_ambiguity_groups=ambiguous,eligible=eligible,candidate_count=len(flat),runtime_grant=False,native_owner_required=True,static_component_proofs=static_proofs,static_rigid_relative_position_quantization=1e-5,meshes=used))
  print(p['family'],len(referenced)-len(unresolved),'/',len(referenced),'eligible',eligible,flush=True)
 runtime_headers=[line for line in headers if not line.startswith('inline constexpr') or any((' '+p['ps2_family']+'_') in line for p in output if p['eligible'])]
 headers.append('inline constexpr Profile profiles[]={')
 for p in output:
  n=p['ps2_family'];headers.append('{"%s","%s",%du,%du,%s_candidates,%du,%s_mapping,%du,%s_static,%du,%s,%s_transfers,%du,%sf},'%(p['family'],n,p['asset_vertices'],p['source_count'],n,p['candidate_count'],n,p['asset_vertices'],n,p['static_vertices']+p['rigid_component_vertices'],str(p['eligible']).lower(),n,p['transfer_vertices'],repr(float(p['max_transfer_distance']))))
 runtime_headers.append('inline constexpr Profile profiles[]={')
 for p in output:
  n=p['ps2_family']
  if p['eligible']:runtime_headers.append('{"%s","%s",%du,%du,%s_candidates,%du,%s_mapping,%du,%s_static,%du,true,%s_transfers,%du,%sf},'%(p['family'],n,p['asset_vertices'],p['source_count'],n,p['candidate_count'],n,p['asset_vertices'],n,p['static_vertices']+p['rigid_component_vertices'],n,p['transfer_vertices'],repr(float(p['max_transfer_distance']))))
  else:runtime_headers.append('{"%s","%s",%du,%du,nullptr,0,nullptr,0,nullptr,0,false,nullptr,0,0.f},'%(p['family'],n,p['asset_vertices'],p['source_count']))
 runtime_headers+=['};','}'];(HERE/'runtime_damage_registry.hpp').write_text('\n'.join(runtime_headers)+'\n')
 headers+=['};','}'];(HERE/'fleet_damage_draft.hpp').write_text('\n'.join(headers)+'\n')
 (HERE/'contracts.json').write_text(json.dumps(dict(schema=1,profiles=output,policy='SOURCE_ONLY; EXACT_HEALTHY_OWNER_REQUIRED; UV_MATERIAL_AMBIGUITY_REQUIRES_UNCHANGED_UNIQUE_XYZ; ALL_CANDIDATE_DELTAS_CONSENSUS; DAMAGE2_A_SURFACE_BARYCENTRIC_TRANSFER_LE_0.05M_PS2_ONLY_LE_0.08M_MIXED; PS2_ONLY_COMPONENTS_WHOLLY_TRANSFERRED_OR_RIGID; MIXED_COMPONENT_BEYOND_LIMIT_FAIL_CLOSED'),indent=2)+'\n')
if __name__=='__main__':run()
