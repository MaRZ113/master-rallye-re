"""Three pinned source PS2 conditional OFF meshes; no runtime authorization.

Original PC triangle correspondence is explicit, not a runtime tolerance.
Runtime must retain exact healthy PC signature and owner-bound clone topology.
"""
from pathlib import Path
import importlib.util,json,struct,itertools
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=load('off_followup_audit',PORT/'docs/full-coverage/vehicles/audit.py')
 c=load('off_followup_convert',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
 src=json.loads((PORT/'docs/vehicle-fleet-kia/fleet-lamps/source-registry.json').read_text())['families']
 inventory=json.loads((PORT/'docs/vehicle-crew-port1/fleet/coverage.json').read_text())['fleet']
 a.w.verify_inputs(a.PS2);pack,_=a.t.load_pak(a.PS2/'TNG.PAK');entries={e['path'].upper():e for e in pack['entries'] if e['kind']=='file'}
 result={'schema':1,'runtime':'SOURCE_ONLY_OWNER_REQUIRED','families':[]};hpp=['#pragma once','namespace gfx2::ps2port::off_followup {','struct Mapping { unsigned first,count; };']
 for family,record,xyz_limit,uv_limit in [('NewRav',34,.001,.000001),('Bruno',20,.001,.0002),('Mattserati',25,.0081,.000001)]:
  row=next(x for x in src if x['family']==family);ps2=row['ps2_family'];meta=next(x for x in inventory if x['ps2_family']==ps2)['models']['CAR']
  raw,_=a.t.read_payload(entries[meta['resource'].upper()],a.PS2/'TNG.000');assert a.sha(raw)==row['ps2_sha256']
  pcpath=a.PC/family/'car.dx';assert a.sha(pcpath.read_bytes())==row['pc_sha256'];pc=a.parse_dx(pcpath);draw=pc.physical_draws[record];pi=pc.draw_global_indices(draw);first=min(pi);native_count=max(pi)-first+1
  scene=a.r.decode_vehicle(raw);mesh=next(m for m in scene.meshes if m['path']==row['candidates'][0]['ps2_path']);assert mesh['material']=='$shader(carshiny)'
  vb=raw[32:32+scene.vertex_count*52];ids,diag=c.indices_for_mesh(vb,mesh);assert len(pi)==len(ids)
  pos=lambda i:struct.unpack_from('<3f',vb,i*52+36)
  uv=lambda i:struct.unpack_from('<2f',vb,i*52+20)
  unique=sorted(set(ids));remap={v:i for i,v in enumerate(unique)};links={v:set() for v in unique};remaining=[tuple(pi[k:k+3]) for k in range(0,len(pi),3)];residual=[]
  for k in range(0,len(ids),3):
   tri=ids[k:k+3];options=[]
   for j,pctri in enumerate(remaining):
    for perm in itertools.permutations(pctri):
     pe=max(abs(pos(tri[n])[q]-pc.vertices.positions[perm[n]][q]) for n in range(3) for q in range(3));ue=max(abs(uv(tri[n])[q]-pc.uv_sets[0].values[perm[n]][q]) for n in range(3) for q in range(2))
     if pe<=xyz_limit and ue<=uv_limit:options.append((pe,ue,j,perm))
   assert options,(family,k);pe,ue,j,matched=min(options);remaining.pop(j);residual.append((pe,ue))
   for n,v in enumerate(tri):links[v].add(matched[n]-first)
  assert not remaining
  candidates=[];maps=[]
  for v in unique:
   cand=sorted(links[v]);assert cand;maps.append((len(candidates),len(cand)));candidates+=cand
  texture_data=[];texture_meta=[];slots=[c.NONE]*3
  for t in mesh['textures']:
   key=a.t.logical_path('\\TNG\\DATAPSM\\'+t['name']+'.GXI').upper();entry=entries[key];gxi,_=a.t.read_payload(entry,a.PS2/'TNG.000');info,pixels=c.texture(gxi);slots[t['slot']]=len(texture_data);texture_data.append(struct.pack('<3I',info['width'],info['height'],len(pixels))+pixels);texture_meta.append({'slot':t['slot'],'resource':entry['path'],'sha256':a.sha(gxi)})
  assert slots[0]!=c.NONE
  native_geometry=a.geometry_signature(a.faces(pc,draw));native_puv=a.sha(b''.join(sorted(struct.pack('<3f2f',*pc.vertices.positions[i],*pc.uv_sets[0].values[i]) for i in pi)))
  ordered_xyz=a.sha(b''.join(struct.pack('<3f',*pc.vertices.positions[i]) for i in range(first,first+native_count)))
  topology=a.sha(b''.join(struct.pack('<2f',*pc.uv_sets[0].values[i]) for i in range(first,first+native_count))+struct.pack('<%dI'%len(pi),*(i-first for i in pi)))
  report={'family':family,'ps2_family':ps2,'source_pc_sha256':row['pc_sha256'],'source_ps2_sha256':row['ps2_sha256'],'source_path':mesh['path'],'node':mesh['node_offset'],'native_source_record':record,'native_vertices':native_count,'native_triangles':len(pi)//3,'native_geometry':native_geometry,'native_position_uv':native_puv,'native_ordered_xyz':ordered_xyz,'native_ordered_uv_indices':topology,'native_first_source_vertex':first,'vertices':len(unique),'indices':len(ids),'textures':texture_meta,'material':mesh['material'],'mode':3,'max_xyz_revision':max(x[0] for x in residual),'max_uv_revision':max(x[1] for x in residual),'mapping':maps,'candidates':candidates,'source_vertex_ids':unique,'runtime_damage':'Requires retained exact healthy native reference, unchanged owner/material/texture and native UV/index clone topology; all mapped candidate deltas must agree <=1e-6. No captured damage proof yet.','diagnostics':diag}
  text=json.dumps(report,sort_keys=True,separators=(',',':')).encode();binary=c.HEADER.pack(c.MAGIC,2,len(text),1,len(unique),len(ids),len(texture_data),bytes.fromhex(row['ps2_sha256']))+text+c.MESH.pack(mesh['node_offset'],3,*slots,0,len(ids))+b''.join(c.vertex(vb,i) for i in unique)+struct.pack('<%dI'%len(ids),*(remap[i] for i in ids))+b''.join(texture_data)
  path=c.private_output(PORT/'.assets/vehicles'/('port3-'+ps2+'-OFF.ps2model'));path.write_bytes(binary);report.update(asset=path.name,size=len(binary),sha256=a.sha(binary));result['families'].append(report)
  hpp+=['inline constexpr unsigned '+ps2+'_candidates[]={'+','.join(str(i)+'u' for i in candidates)+'};','inline constexpr Mapping '+ps2+'_mapping[]={'+','.join('{%du,%du}'%m for m in maps)+'};']
 hpp+=['struct Profile { const char* family; unsigned nativeVertices,triangles; const char *geometry,*positionUv,*orderedXyz,*uvIndices; const Mapping* mapping; const unsigned* candidates; unsigned mappingCount,candidateCount; FleetProfile loader; };','inline constexpr Profile profiles[]={']
 for r in result['families']:
  ps2=r['ps2_family'];hpp.append(' {"%s",%du,%du,"%s","%s","%s","%s",%s_mapping,%s_candidates,%du,%du,{"%s","%s","%s","%s",%du,%du,%du,%du,1u,0u,nullptr,nullptr,nullptr}},'%(r['family'],r['native_vertices'],r['native_triangles'],r['native_geometry'],r['native_position_uv'],r['native_ordered_xyz'],r['native_ordered_uv_indices'],ps2,ps2,len(r['mapping']),len(r['candidates']),r['family'],ps2,r['asset'],r['sha256'],r['size'],r['vertices'],r['indices'],len(r['textures'])))
 hpp+=['};','}'];(HERE/'off_mapping.hpp').write_text('\n'.join(hpp)+'\n');(HERE/'contracts.json').write_text(json.dumps(result,indent=2)+'\n');print([(x['family'],x['vertices'],x['native_vertices'],x['max_xyz_revision'],x['max_uv_revision'],x['sha256']) for x in result['families']])
if __name__=='__main__':main()
