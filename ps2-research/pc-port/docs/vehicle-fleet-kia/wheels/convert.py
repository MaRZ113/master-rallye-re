"""Whole original Kia WHEEL; no guessed per-record geometry mapping or fitting."""
from pathlib import Path
import importlib.util,json,struct,hashlib
HERE=Path(__file__).resolve().parent;PORT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('wheel_reference',PORT/'docs/vehicle-race-model-port1/wheel-port/convert_wheel.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
spec=importlib.util.spec_from_file_location('fleet_reference',PORT/'docs/vehicle-continuity2/fleet-car/prepare_contracts.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def bounds(points):return [[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)]
def convert():
 f=next(x for x in json.loads((PORT/'docs/vehicle-continuity2/fleet-car/fleet-car-contracts.json').read_text())['fleet'] if x.get('pc_family')=='KiaSportage');wc=f['wheel_contract']
 p.r.w.verify_inputs(p.PS2);pack,_=p.t.load_pak(p.PS2/'TNG.PAK');entries={p.t.logical_path(e['path']).upper():e for e in pack['entries'] if e['kind']=='file'}
 resource='\\TNG\\DATAPSM\\VEHICLES\\KIASPORTAGE\\WHEEL.PSM';raw,prov=p.t.read_payload(entries[resource],p.PS2/'TNG.000')
 if p.sha(raw)!=wc['source_ps2_sha256']:raise ValueError('Original PS2 drift')
 scene,trailer=p.wheel_reader.decode_complete(raw);verts=raw[32:32+scene.vertex_count*52];points=[struct.unpack_from('<3f',verts,i*52+36) for i in range(scene.vertex_count)]
 pcpath=p.PC/'KiaSportage/wheel.dx'
 if p.sha(pcpath.read_bytes())!=wc['source_pc_sha256']:raise ValueError('Original PC drift')
 pc=p.parse_dx(pcpath);textures=[];texture_rows=[];mapping={};indices=[];meshes=[];rows=[]
 for m in scene.meshes:
  slots=[w.c.NONE]*3
  for s in m['textures']:
   key=p.t.logical_path('\\TNG\\DATAPSM\\'+s['name']+'.GXI').upper()
   if key not in mapping:
    gxi,gprov=p.t.read_payload(entries[key],p.PS2/'TNG.000');info,pixels=w.c.texture(gxi);mapping[key]=len(textures);textures.append(struct.pack('<3I',info['width'],info['height'],len(pixels))+pixels);texture_rows.append(dict(path=key,sha256=p.sha(gxi),argb_sha256=p.sha(pixels),width=info['width'],height=info['height']))
   slots[s['slot']]=mapping[key]
  contract=p.r.material_contract(m['material'],next((s['name'] for s in m['textures'] if s['slot']==1),''))
  if contract['mode']!=3:raise ValueError('Unsupported original wheel material')
  ids,diag=w.c.indices_for_mesh(verts,m);us=[struct.unpack_from('<f',verts,i*52+20)[0] for i in ids];vs=[struct.unpack_from('<f',verts,i*52+24)[0] for i in ids]
  meshes.append(w.c.MESH.pack(m['node_offset'],3,*slots,len(indices),len(ids)));rows.append(dict(path=m['path'],node_offset=m['node_offset'],mode=3,texture_indices=slots,first_index=len(indices),index_count=len(ids),faces=len(ids)//3,contract=contract,mixed_reflection=contract['effective_secondary'].lower().endswith('rendertarget64x64'),u_range=[min(us),max(us)],v_range=[min(vs),max(vs)],primary_u_wrap='tread' in m['textures'][0]['name'].lower(),source_texture_slots=m['textures'],**diag));indices+=ids
 meta=dict(schema_version=2,role='FLEET_WHOLE_SEPARATE_WHEEL',family='KiaSportage',source_sha256=p.sha(raw),pc_source_sha256=wc['source_pc_sha256'],meshes=rows,texture_upload=texture_rows,coordinates='ORIGINAL_WHEEL_LOCAL_NO_RESCALE_NO_PIVOT_TRANSLATION; CURRENT_INDEPENDENT_NATIVE_WHEEL_WORLD',primary_orientation='RAW_SOURCE_UV_RUNTIME_V_EQUALS_1_MINUS_V',suppression='ALL_FOUR_CURRENT_OWNED_PC_WHEEL_SOURCES_ATOMICALLY; WHOLE_PRIVATE_WHEEL_ONCE',original_post_tree_auxiliary=trailer)
 text=json.dumps(meta,sort_keys=True,separators=(',',':')).encode();binary=w.c.HEADER.pack(w.c.MAGIC,2,len(text),len(meshes),scene.vertex_count,len(indices),len(textures),bytes.fromhex(p.sha(raw)))+text+b''.join(meshes)+b''.join(w.c.vertex(verts,i) for i in range(scene.vertex_count))+struct.pack('<'+'I'*len(indices),*indices)+b''.join(textures)
 out=w.c.private_output(PORT/'.assets/vehicles/KIASPORTAGE-WHEEL-FLEET.ps2model')
 if out.exists() and out.read_bytes()!=binary:raise ValueError('Private candidate drift')
 out.write_bytes(binary)
 report=dict(**meta,filename=out.name,sha256=p.sha(binary),bytes=len(binary),vertices=scene.vertex_count,indices=len(indices),textures=len(textures),native_sources=wc['native_sources'],ps2_bounds=bounds(points),pc_bounds=bounds(pc.vertices.positions),runtime_grant='CURRENT_OWNER_TRANSFORM_AND_SOURCE_PREFLIGHT_STILL_REQUIRED')
 (HERE/'contract.json').write_text(json.dumps(report,indent=2)+'\n');print(out.name,report['sha256'],report['ps2_bounds'],report['pc_bounds'])
 lines=['#pragma once','#include "race_fleet_registry.hpp"','namespace gfx2::ps2port {','inline constexpr FleetRaceSource kKiaWheelSources[]={']
 for s in wc['native_sources']:
  lines.append(' {"%s","%s","%s","%s",%du,%du,false},'%(s['geometry_sha256'],s['ordered_position_sha256'],s['uv_topology_sha256'],s['native_uv_winding_sha256'],s['vertices'],s['faces']))
 lines+=['};','inline constexpr bool kKiaWheelMixed[]={'+','.join('true' if m['mixed_reflection'] else 'false' for m in rows)+'};','inline constexpr bool kKiaWheelWrapU[]={'+','.join('true' if m['primary_u_wrap'] else 'false' for m in rows)+'};', 'inline constexpr FleetRaceProfile kKiaWheelProfile={"KiaSportage","KIASPORTAGE","%s","%s",%du,%du,%du,%du,%du,4u,4u,kKiaWheelSources,kKiaWheelMixed,kKiaWheelWrapU};'%(out.name,p.sha(binary),len(binary),scene.vertex_count,len(indices),len(textures),len(rows)),'}']
 (HERE/'kia_wheel_registry.hpp').write_text('\n'.join(lines)+'\n')
 fixture=b'PS2KWH01'+struct.pack('<I',4)
 for d in pc.physical_draws:
  count=d.local_vertex_max+1;first=d.vertex_base
  vb=b''.join(struct.pack('<3fI2f',*pc.vertices.positions[i],0xffffffff,*pc.uv_sets[0].values[i]) for i in range(first,first+count))
  ids=[i-first for i in pc.draw_global_indices(d)]
  for k in range(0,len(ids),3):ids[k],ids[k+1]=ids[k+1],ids[k]
  ib=struct.pack('<'+'I'*len(ids),*ids)
  fixture+=struct.pack('<6I',0x142,24,count,len(ids)//3,len(vb),len(ib))+vb+ib
 fixture_path=PORT/'.assets/vehicles/kia-wheel-fixtures.bin';fixture_path.write_bytes(fixture)
 (HERE/'fixture-manifest.json').write_text(json.dumps(dict(filename=fixture_path.name,sha256=p.sha(fixture),bytes=len(fixture),format='PS2KWH01 + u32 source_count + 4 * (6xu32 fvf,stride,vertices,triangles,vbytes,ibytes; vb; normalized u32 ib)',provenance='ORIGINAL_PC_XYZ_UV_WITH_SYNTHETIC_WHITE_DIFFUSE; EXACT_NATIVE_WINDING',source_pc_sha256=wc['source_pc_sha256']),indent=2)+'\n')
if __name__=='__main__':convert()
