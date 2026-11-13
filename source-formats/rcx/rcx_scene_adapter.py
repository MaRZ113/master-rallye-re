"""Astra RCX to SDK universal scene; source only and bounded to a fresh output."""
import argparse,hashlib,math,struct,sys
from pathlib import Path
from qto_inspect import parse
from tex_decode import decode
HERE=Path(__file__).resolve().parent
SRC=HERE/'astra_extracted'
PARTS=['body','bonnet','bumper back','bumper front','headlamp l','headlamp r','brakelight l','brakelight r','mirror l','mirror r','wing','windows','wheelfront l','wheelfront r','wheelback l','wheelback r']
WHEELS={'front_left':'wheelfront l','front_right':'wheelfront r','rear_left':'wheelback l','rear_right':'wheelback r'}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def build(sdk,output):
 sys.dont_write_bytecode=True;sys.path.insert(0,str(sdk/'src'))
 from master_rallye import universal_vehicle_scene as u
 output=output.resolve()
 if output==HERE or not output.is_relative_to(HERE):raise ValueError('output outside research root')
 raw=(SRC/'Astra.msh').read_bytes();magic,count=struct.unpack_from('<II',raw)
 if magic!=0xb00b10ad or len(raw)!=8+count*136:raise ValueError('unknown MSH')
 records={}
 for i in range(count):
  p=8+i*136;name=raw[p:p+32].split(b'\0')[0].decode('ascii');bounds=struct.unpack_from('<6f',raw,p+36);m=struct.unpack_from('<16f',raw,p+72)
  if name in records or not all(math.isfinite(x) for x in (*bounds,*m)):raise ValueError('bad MSH')
  records[name]=(bounds,m,i)
 meshes=[];nodes=[];materials=[];textures=[];assets={};texture_map={};anchor={}
 for i,name in enumerate(PARTS):
  path=SRC/(name+'.qto');source=path.read_bytes();d=parse(path);bounds,m,source_msh_index=records[name]
  matrix=[m[0],m[4],m[8],m[12],m[1],m[5],m[9],m[13],m[2],m[6],m[10],m[14],0,0,0,1]
  points=[u.transform_point(matrix,list(x[0])) for x in d['vertices']]
  actual=[min(v[a] for v in points) for a in range(3)]+[max(v[a] for v in points) for a in range(3)]
  if max(abs(a-b) for a,b in zip(actual,bounds))>.02:raise ValueError('MSH/QTO bounds mismatch '+name)
  mid=[]
  for j,g in enumerate(d['groups']):
   if g['texture_index'] is None:raise ValueError('untextured group is not qualified')
   texname=d['textures'][g['texture_index']].replace('\\','/').split('/')[-1]
   key=texname.lower()
   if key not in texture_map:
    tf=SRC/texname; traw=tf.read_bytes();tex=decode(traw); pixels=tex['mips'][0]['rgba'];tid=f'tex-{len(textures):03d}'; side=f'textures/{tid}.rgba';assets[side]=pixels;texture_map[key]=tid
    textures.append({'id':tid,'width':tex['width'],'height':tex['height'],'rgba_path':side,'rgba_sha256':digest(pixels),'source_channels':{'format':tex['format'],'original_tex_sha256':digest(traw),'orientation':'stored top mip rows; no source-runtime parity claim'}})
   mat=f'material-{i:03d}-{j:02d}';mesh=f'mesh-{i:03d}-{j:02d}';mid.append(mesh)
   materials.append({'id':mat,'diffuse_texture_id':texture_map[key],'raw_fields':[{'qto_group_hex':g['raw_hex'],'texture_index':g['texture_index'],'material_flags_raw':g['material_flags_raw']}],'unsupported':['RCX render flags, blending, reflection and lighting not decoded']})
   indices=d['indices'];tri=[list(indices[k:k+3]) for k in range(g['start'],g['end'],3)]
   meshes.append({'id':mesh,'material_id':mat,'positions':[list(v[0]) for v in d['vertices']],'normals':[list(v[1]) for v in d['vertices']],'uvs':[list(v[2]) for v in d['vertices']],'triangles':tri,'source':{'qto_file':path.name,'qto_sha256':digest(source),'draw_index':j,'texture_index':g['texture_index'],'group_raw_hex':g['raw_hex']}})
  node=f'node-{i:03d}';nodes.append({'id':node,'name':name,'role':'wheel' if name in WHEELS.values() else 'body','parent_id':None,'mesh_ids':mid,'visible':True,'source_visible':True,'local_transform':matrix,'source_local_transform':matrix,'transform_evidence':'MSH 4x4 row matrix transposed; transformed QTO bounds match MSH within 0.02 source units','source_transform_record':{'msh_index':source_msh_index,'matrix_raw':list(m),'bbox':list(bounds)}})
  if name in WHEELS.values():anchor[next(k for k,v in WHEELS.items() if v==name)]=node
 scene={'schema':'universal-vehicle-scene/1','source':{'root':str(SRC),'protected_roots':[str(sdk)],'format':'RCX v4/QTO v7.2','msh_sha256':digest(raw)},'metadata':{'vehicle':'Astra','source_scope':'minimal static body and four wheels'},'unknown_semantics':[{'id':'render','status':'UNSUPPORTED','meaning':'native materials, lighting, alpha, animation and damage remain unknown'},{'id':'units','status':'INFERRED','meaning':'source dimensions consistent with metres, not engine-qualified'}],'coordinate_system':{'source_to_normalized':[-1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1],'interpretation_status':'INFERRED static basis','evidence':['MSH matrices and bounds','readable original texture text in diagnostic images; native render unverified']},'nodes':nodes,'meshes':meshes,'materials':materials,'textures':textures,'wheel_anchors':anchor}
 result=u.save_scene(scene,output,assets,protected_roots=[sdk]);print(result);return output/'scene.json'
def main():
 p=argparse.ArgumentParser();p.add_argument('--sdk',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();build(a.sdk,a.output)
if __name__=='__main__':main()
