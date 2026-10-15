"""Pinned original XTRAIL CAR unconditional roots only; no COMPLETE reuse."""
from pathlib import Path
import sys, json, struct, importlib.util
PORT=Path(__file__).resolve().parents[3];ROOT=PORT.parents[1]
sys.path[:0]=[str(ROOT/'ps2-research/tools'),str(PORT/'tools')]
import tngtool as t, reflection_runtime as r, psbtool as p, prepare_vehicle_models as src
spec=importlib.util.spec_from_file_location('complete_conversion',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
SOURCE='af57572e92ce47d810666779fb60c8c178f1979feb203416131a3acc81449326'
def convert(root):
 root=Path(root);r.w.verify_inputs(root);pack,_=t.load_pak(root/'TNG.PAK')
 entries={t.logical_path(e['path']).upper():e for e in pack['entries'] if e['kind']=='file'}
 key='\\TNG\\DATAPSM\\VEHICLES\\XTRAIL\\CAR.PSM';raw,prov=t.read_payload(entries[key],root/'TNG.000')
 if t.sha(raw)!=SOURCE:raise ValueError('Original CAR source drift')
 scene=r.decode_vehicle(raw); selected=[m for m in scene.meshes if m['path'] in ['root.'+str(i) for i in range(20)]]
 if len(selected)!=20 or scene.vertex_count!=3292:raise ValueError('Original CAR hierarchy drift')
 textures=[];tmeta=[];mapping={};rows=[];meshes=[];indices=[]
 def tx(name):
  k=t.logical_path(name).upper()
  if k not in mapping:
   gxi,gprov=t.read_payload(entries[k],root/'TNG.000');info,pixels=c.texture(gxi)
   mapping[k]=len(textures);textures.append(struct.pack('<3I',info['width'],info['height'],len(pixels))+pixels)
   tmeta.append({'path':k,'sha256':t.sha(gxi),'argb_sha256':t.sha(pixels),'width':info['width'],'height':info['height'],'provenance':gprov})
  return mapping[k]
 verts=raw[32:32+scene.vertex_count*52]
 for mesh in selected:
  slots=[c.NONE]*3
  for slot in mesh['textures']:slots[slot['slot']]=tx('\\TNG\\DATAPSM\\'+slot['name']+'.GXI')
  secondary=next((s['name'] for s in mesh['textures'] if s['slot']==1),'');contract=r.material_contract(mesh['material'],secondary)
  mode=contract['mode']
  if mesh['path']=='root.18':
   if mesh['material']!='shit' or slots[0]!=c.NONE:raise ValueError('Default material drift')
   slots=[tx('\\TNG\\DEFAULT.GXI'),c.NONE,c.NONE];mode=0
   contract={**contract,'mode':0,'effective_primary':'ORIGINAL_DEFAULT_GXI','effective_secondary':None}
  if mode not in (0,1,3,20):raise ValueError('Unsupported unconditional CAR mode')
  ids,diag=c.indices_for_mesh(verts,mesh)
  meshes.append(c.MESH.pack(mesh['node_offset'],mode,*slots,len(indices),len(ids)))
  rows.append({**mesh,'mode':mode,'texture_indices':slots,'contract':contract,'first_index':len(indices),'index_count':len(ids),'faces':len(ids)//3,**diag});indices+=ids
 metadata={'schema_version':2,'role':'RACE_UNCONDITIONAL_CHASSIS','source_resource':key,'source_sha256':SOURCE,'source_provenance':prov,'meshes':rows,'texture_upload':tmeta,'excluded_conditional_meshes':[m['path'] for m in scene.meshes if m not in selected],'named_wrappers':scene.extra_nodes,'wheels':'SEPARATE_WHEEL_PSM_NOT_INCLUDED','coordinates':'RAW_CAR_MODEL_LOCAL_NATIVE_WORLD_REQUIRED','alpha':'ORIGINAL_STORED_ALPHA_NO_REMAP','winding':'ORDERED_SOURCE_TRIPLES_CULL_NONE_REQUIRED','primary_orientation':'RAW_UV_RUNTIME_V_EQUALS_1_MINUS_V_AS_CONFIRMED_COMPLETE'}
 text=json.dumps(metadata,sort_keys=True,separators=(',',':')).encode()
 binary=c.HEADER.pack(c.MAGIC,2,len(text),len(meshes),scene.vertex_count,len(indices),len(textures),bytes.fromhex(SOURCE))+text+b''.join(meshes)+b''.join(c.vertex(verts,i) for i in range(scene.vertex_count))+struct.pack('<%dI'%len(indices),*indices)+b''.join(textures)
 report={**metadata,'asset_sha256':t.sha(binary),'bytes':len(binary),'vertices':scene.vertex_count,'mesh_count':len(meshes),'index_count':len(indices),'faces':len(indices)//3,'texture_count':len(textures)}
 return binary,report
if __name__=='__main__':
 binary,report=convert('D:/Game/Master Rallye PS2');out=c.private_output(PORT/'.assets/vehicles/XTRAIL-CAR.ps2model')
 if out.exists() and out.read_bytes()!=binary:raise ValueError('Existing private output differs')
 out.write_bytes(binary);Path(__file__).with_name('conversion-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ('asset_sha256','bytes','vertices','mesh_count','faces','texture_count')}))
