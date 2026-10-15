"""Pinned original WHEEL conversion; exact PC face partition, no fitted transforms."""
from pathlib import Path
import sys, json, struct, importlib.util, collections
PORT=Path(__file__).resolve().parents[3];ROOT=PORT.parents[1]
sys.path[:0]=[str(ROOT/'ps2-research/tools'),str(PORT/'tools'),str(ROOT.parent/'master-rallye-re-course/src')]
import tngtool as t, reflection_runtime as r
from master_rallye.dx import parse_dx
from prepare_reflection_pilot import geometry_signature
spec=importlib.util.spec_from_file_location('complete_conversion',PORT/'docs/vehicle-model-port2/assets/convert_complete.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
SOURCE='d53360eab52761fdadf1a4d5a2c87196be7674fbbb603c41cd4726a4b303773c'
PCSHA='f05ac990b6ea2312f2a2d552ec886aded4c68a8d8fac027f99e1fc7b0826779c'
def key(face):
 return tuple(sorted(tuple(struct.pack('<f',0.0 if v==0 else v) for v in p) for p in face))
def convert(root,split=True):
 root=Path(root);r.w.verify_inputs(root);pack,_=t.load_pak(root/'TNG.PAK')
 entries={t.logical_path(e['path']).upper():e for e in pack['entries'] if e['kind']=='file'}
 resource='\\TNG\\DATAPSM\\VEHICLES\\XTRAIL\\WHEEL.PSM';raw,prov=t.read_payload(entries[resource],root/'TNG.000')
 if t.sha(raw)!=SOURCE:raise ValueError('Original WHEEL source drift')
 spec=importlib.util.spec_from_file_location('reader',PORT/'docs/vehicle-model-port1/ps2-format-lights/complete_reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
 scene,trailer=reader.decode_complete(raw)
 if scene.vertex_count!=300 or [m['path'] for m in scene.meshes]!=['root.0','root.1','root.2']:raise ValueError('Wheel hierarchy drift')
 verts=raw[32:32+300*52];points=[struct.unpack_from('<3f',verts,i*52+36) for i in range(300)]
 textures=[];tmeta=[];mapping={};sources=[]
 for mesh in scene.meshes:
  slots=[c.NONE]*3
  for s in mesh['textures']:
   name=t.logical_path('\\TNG\\DATAPSM\\'+s['name']+'.GXI').upper()
   if name not in mapping:
    gxi,gprov=t.read_payload(entries[name],root/'TNG.000');info,pixels=c.texture(gxi);mapping[name]=len(textures)
    textures.append(struct.pack('<3I',info['width'],info['height'],len(pixels))+pixels);tmeta.append({'path':name,'sha256':t.sha(gxi),'argb_sha256':t.sha(pixels),'width':info['width'],'height':info['height'],'provenance':gprov})
   slots[s['slot']]=mapping[name]
  contract=r.material_contract(mesh['material'],next((s['name'] for s in mesh['textures'] if s['slot']==1),''))
  if contract['mode']!=3:raise ValueError('Wheel material drift')
  ids,diag=c.indices_for_mesh(verts,mesh);sources.append((mesh,slots,contract,[ids[i:i+3] for i in range(0,len(ids),3)],diag))
 pcpath=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/wheel.dx'
 if t.sha(pcpath.read_bytes())!=PCSHA:raise ValueError('PC wheel source drift')
 pc=parse_dx(pcpath);records=[];groups=[]
 for d in pc.physical_draws:
  ids=pc.draw_global_indices(d);faces=[tuple(pc.vertices.positions[i] for i in ids[j:j+3]) for j in range(0,len(ids),3)]
  records.append({'record':d.draw_index,'path':d.record_path,'vertex_base':d.vertex_base,'vertices':d.local_vertex_max+1,'index_start':d.index_start,'faces':len(faces),'signature':geometry_signature(faces),'slots':[s.value for s in d.texture_slots]})
  source_index=[0,1,0,2][d.draw_index];source=sources[source_index];wanted=collections.Counter(key(f) for f in faces);chosen=[]
  for tri in source[3]:
   k=key([points[i] for i in tri])
   if wanted[k]:chosen.append(tri);wanted[k]-=1
  if any(wanted.values()) or len(chosen)!=len(faces):raise ValueError('Exact face partition not proved')
  groups.append((source,chosen,d.draw_index))
 if [len(g[1]) for g in groups]!=[72,36,54,90]:raise ValueError('PC record face counts drift')
 if collections.Counter(tuple(v) for g in groups for v in g[1])!=collections.Counter(tuple(v) for s in sources for v in s[3]):raise ValueError('Partition not exhaustive/disjoint')
 if not split:groups=[(s,s[3],None) for s in sources]
 indices=[];meshes=[];rows=[]
 for source,tris,record in groups:
  mesh,slots,contract,_,diag=source;ids=[i for tri in tris for i in tri]
  meshes.append(c.MESH.pack(mesh['node_offset'],3,*slots,len(indices),len(ids)))
  rows.append({**mesh,'mode':3,'texture_indices':slots,'contract':contract,'first_index':len(indices),'index_count':len(ids),'faces':len(tris),'pc_record':record,'signature':geometry_signature([tuple(points[i] for i in tri) for tri in tris]),**diag});indices+=ids
 metadata={'schema_version':2,'role':'RACE_SEPARATE_WHEEL','source_resource':resource,'source_sha256':SOURCE,'source_provenance':prov,'meshes':rows,'texture_upload':tmeta,'pc_source_sha256':PCSHA,'pc_records':records,'coordinates':'RAW_WHEEL_LOCAL_CURRENT_NATIVE_WHEEL_WORLD_REQUIRED','primary_orientation':'RAW_UV_RUNTIME_V_EQUALS_1_MINUS_V_AS_CONFIRMED_COMPLETE','alpha':'ORIGINAL_STORED_ALPHA_NO_REMAP','winding':'ORDERED_SOURCE_TRIPLES_CULL_NONE_REQUIRED','partition':'BIT_EXACT_FLOAT32_UNSIGNED_FACE_MULTISET_EXHAUSTIVE_DISJOINT' if split else 'ORIGINAL_THREE_MESHES'}
 text=json.dumps(metadata,sort_keys=True,separators=(',',':')).encode();binary=c.HEADER.pack(c.MAGIC,2,len(text),len(meshes),300,len(indices),len(textures),bytes.fromhex(SOURCE))+text+b''.join(meshes)+b''.join(c.vertex(verts,i) for i in range(300))+struct.pack('<%dI'%len(indices),*indices)+b''.join(textures)
 return binary,{**metadata,'asset_sha256':t.sha(binary),'bytes':len(binary),'vertices':300,'mesh_count':len(meshes),'faces':len(indices)//3,'texture_count':len(textures)}
if __name__=='__main__':
 for split,name in [(False,'XTRAIL-WHEEL.ps2model'),(True,'XTRAIL-WHEEL-DRAW.ps2model')]:
  binary,report=convert('D:/Game/Master Rallye PS2',split);out=c.private_output(PORT/'.assets/vehicles'/name)
  if out.exists() and out.read_bytes()!=binary:raise ValueError('Existing private output differs')
  out.write_bytes(binary);Path(__file__).with_name('draw-evidence.json' if split else 'conversion-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
  print(name,report['bytes'],report['asset_sha256'])
