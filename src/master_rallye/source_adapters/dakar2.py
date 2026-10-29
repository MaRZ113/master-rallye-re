"""Qualified original Xbox Dakar2 → immutable Universal Vehicle Scene v1.

No MR compiler, physics, CarID or roster dependency. Source material/rendering
and dynamic pose unknowns survive reconstruction explicitly.
"""
from pathlib import Path
import hashlib
import struct
from .. import universal_vehicle_scene as uvs
from .dakar2_disc import FileReader,xdvdfs
from .dakar2_formats import RBB,sbb_entries,hierarchy,xmd_meshes,xtx_texture,digest

VERSION='dakar2-xbox-source/1'
PINS={'default.xbe':'715db4e407b38c0a6d14ea0ee9d08ebc524b9ece92ceeaa70b5fb81a5ec32378',
      'ALL.RBB':'c82744f12b8322a2bde93d19bc270f6e365523d22c38235b12253fb7673b889a',
      'ALL.SBB':'df98579418da0ed2b0b0bc79a7c6e1558a7b356c84abbbbe086a19cb3a2d62e9'}
VEHICLES={'PAJERO':{'vehicle_resource':6,'hierarchy_resource':48,'prefix':'PAJ_'},
          'NISSAN':{'vehicle_resource':9,'hierarchy_resource':54,'prefix':None},
          'HINO':{'vehicle_resource':18,'hierarchy_resource':72,'prefix':'HINO_'}}
NORMALIZATION=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,-1.,0.,0.,0.,0.,1.]

def create_scene(image,output,vehicle='PAJERO',*,partition=0x18300000):
    if vehicle not in VEHICLES:raise ValueError('unqualified Dakar2 source vehicle')
    image=Path(image).absolute();uvs.unlinked(image);output=Path(output).absolute()
    protected=[image.parent,image.parent.parent]
    uvs.output_directory(output,protected)
    if output.exists():raise ValueError('Fresh source output required')
    reader=FileReader(image);files=xdvdfs(reader,partition);lookup={r['path'].lower():r for r in files}
    if reader.size>16*1024*1024*1024:raise ValueError('source image audit budget')
    image_hash=hashlib.sha256()
    before=image.stat()
    with image.open('rb')as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):image_hash.update(chunk)
    after=image.stat()
    if(before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('source image changed during hash')
    original={};sources={}
    for name,key in [('default.xbe','default.xbe'),('ALL.RBB','all.vsr/rbb/xbox/all.rbb'),('ALL.SBB','all.vsr/rbb/xbox/all.sbb')]:
        row=lookup.get(key)
        if row is None:raise ValueError('missing qualified Xbox source '+key)
        data=reader.read(row['offset'],row['bytes'])
        if digest(data)!=PINS[name]:raise ValueError('unqualified Xbox resource revision '+name)
        original[name]=data;sources[name]={**row,'sha256':digest(data)}
    main=RBB(original['ALL.RBB']);catalog=sbb_entries(original['ALL.SBB']);selection=VEHICLES[vehicle]
    vehicle_row=main.resources[selection['vehicle_resource']]
    if vehicle_row['type']!='VEH' or main.reference(vehicle_row['offset']+4)['id']!=selection['hierarchy_resource']:
        raise ValueError('VEH→HIR ownership mismatch')
    bones=hierarchy(main,selection['hierarchy_resource'])
    if selection['prefix']and not all(n['name'].startswith(selection['prefix'])for n in bones):raise ValueError('unexpected source hierarchy identity')
    member=next((r for r in catalog if r['name']==vehicle+'_HI_0_0.LOD'),None)
    if member is None:raise ValueError('missing original HI_0_0 resource')
    block=RBB(original['ALL.SBB'][member['offset']:member['offset']+member['stored_bytes']])
    root=block.resources[0]
    if root['type']!='LOD'or block.u(root['offset'])!=len(bones):raise ValueError('LOD→HIR node count mismatch')
    materials=[];meshes=[];nodes=[];textures=[];assets={};texture_ids={}
    resources=[]
    for name,data in [('ALL.RBB',main.data),(member['name'],block.data)]:
        path='original/'+name;assets[path]=data
        resources.append({'member':name,'snapshot_path':path,'bytes':len(data),'sha256':digest(data)})
    member_pin=resources[1]
    def texture(index):
        if index in texture_ids:return texture_ids[index]
        decoded=xtx_texture(block,index);key='xtx-%03d'%index;rgba=decoded['rgba'];raw=decoded['original']
        assets['textures/'+key+'.rgba']=rgba;assets['textures/'+key+'.bcn']=raw
        textures.append({'id':key,'width':decoded['width'],'height':decoded['height'],'rgba_path':'textures/'+key+'.rgba',
            'rgba_sha256':digest(rgba),'source_channels':{'mode':'BC1_RGBA'if decoded['format']==12 else'BC3_RGBA',
                'xbox_format':decoded['format'],'compressed_path':'textures/'+key+'.bcn','compressed_sha256':digest(raw),
                'mips':decoded['mips'],'alpha':'decoded original BC samples; runtime shader/coverage interpretation unqualified'},
            'source':{**member_pin,'resource_id':index,'offset':decoded['offset']}})
        texture_ids[index]=key;return key
    for bone in bones:
        ordinal=bone['id'];pair_at=root['offset']+12+ordinal*8;model=block.reference(pair_at);mesh_ids=[]
        if model['type']!='XMD':raise ValueError('LOD node mesh reference')
        for sub in xmd_meshes(block,model['id']):
            key='node-%03d-sub-%02d'%(ordinal,sub['submesh']);mesh_ids.append(key)
            refs=[texture(i)if i is not None else None for i in sub['texture_resource_ids']]
            materials.append({'id':key,'diffuse_texture_id':refs[0],
                'raw_fields':[{'texture_resource_ids':sub['texture_resource_ids'],'texture_bindings':refs,'flags':sub['raw_flags'],'model_flags':sub['model_flags'],
                               'declaration':sub['declaration'],'index_primitive':6,'source_offset':sub['offset']}],
                'unsupported':['secondary texture/lightmap/environment shader roles','alpha-test/blend/cull/lighting runtime state'],
                'flags':{'transparent_raw':'1'if sub['declaration']in(0x13,0x51a13)else'0',
                    'evidence':'Exact XBE declaration table1940b8 and native8b360: mode3 enables SRC_ALPHA/ONE_MINUS_SRC_ALPHA; mode0 disables blending. No name heuristic.'},
                'preview':{'opacity':1.,'policy':'Original BC alpha and native blend classification. Secondary shader stages and original cull state are not reproduced.'}})
            stream_records={}
            for slot,s in sub['streams'].items():
                path='streams/'+key+'-%02d.bin'%slot;assets[path]=s['raw'];stream_records[str(slot)]={k:v for k,v in s.items()if k!='raw'};stream_records[str(slot)]['path']=path
            meshes.append({'id':key,'material_id':key,'positions':sub['positions'],'normals':sub['normals'],'uvs':sub['uvs'],
                'triangles':sub['triangles'],'source':{'member':member['name'],'member_sha256':member['sha256'],'resource_id':model['id'],
                    'source_node':ordinal,'original_index_strip':sub['original_indices'],'indices_offset':sub['indices_offset'],
                    'streams':stream_records,'normal_encoding':'signed11/11/10 compressed vector; original words retained',
                    'color_policy':'original BGRA stream retained; vertex lighting/color multiplication not applied by neutral preview',
                    'secondary_uv':'original stream10 retained, not discarded or substituted for UV0'}})
        matrix=uvs.IDENTITY[:]
        for k,value in enumerate(bone['translation']):matrix[k*4+3]=value
        is_wheel=bone['name'].endswith('_WHEEL')
        nodes.append({'id':'node-%03d'%ordinal,'name':bone['name'],'parent_id':None if bone['parent']==-1 else'node-%03d'%bone['parent'],
            'mesh_ids':mesh_ids,'visible':True,'source_visible':True,'role':'wheel'if is_wheel else'body',
            'local_transform':matrix,'source_local_transform':matrix[:],'source_transform_record':bone,
            'transform_evidence':'Original HIR 0xd4 records, parent/sibling/child links and identity rest bases; local XYZ translations retained. Equipment/runtime visibility unresolved.'})
    scene={'schema':uvs.SCHEMA,'metadata':{'adapter':VERSION,'display_name':'Dakar 2 Xbox '+vehicle,
        'qualification':'L1 structural recovery; L2 WARN: mixed source strip facing/culling unresolved; original local rest assembly, runtime equipment not qualified',
        'neutral_preview':{'cull':'cw','evidence':'CW is a bounded exterior inspection policy, not source cull qualification. Source index strips retained exactly; paired CW/CCW and explicit two-sided diagnostics required.'},
        'implementation_sha256':{Path(p).name:digest(Path(p).read_bytes())for p in(__file__,Path(__file__).with_name('dakar2_formats.py'),Path(__file__).with_name('dakar2_disc.py'))}},
        'source':{'game':"Dakar 2: The World's Ultimate Rally (2003)",'platform':'Xbox','root':str(image.parent),'protected_roots':list(map(str,protected)),
                  'disc':str(image),'disc_bytes':reader.size,'disc_sha256':image_hash.hexdigest(),
                  'partition_offset':partition,'resources':resources,'container_resources':sources,'catalog':member['name'],'catalog_record':member,
                  'vehicle_resource':vehicle_row,'hierarchy_resource':main.resources[selection['hierarchy_resource']],
                  'related_members':[r for r in catalog if r['name'].startswith(vehicle+'_')],
                  'authenticity':'exact owner-local source; certificate/title/region audited separately, publisher dump authenticity not independently certified'},
        'coordinate_system':{'source_to_normalized':NORMALIZATION[:],'source':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,1],'units':'source units'},
            'normalized':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,-1],'units':'source units'},
            'interpretation_status':'front/back and left/right HIR node names qualify signs; +Y roof/body geometry; physical units not qualified',
            'evidence':['original FL/FR/BL/BR axle,hub,wheel hierarchy','native XMD Xbox stream/declaration loader','identity source rest bases, no scale fit']},
        'meshes':meshes,'materials':materials,'textures':textures,'nodes':nodes,
        'selection':{'member':member['name'],'pose':'HIR original local rest pose; no suspension settlement or wheel guessing','visibility':'all retained source nodes; runtime part visibility/equipment selection NOT TESTED'},
        'unknown_semantics':[{'id':k,'status':'NOT TESTED','meaning':v}for k,v in {
            'renderer':'secondary texture stages, vertex colors, lights, culling and full shader parity not reproduced; original standard blend classification is recovered',
            'culling':'CW and CCW reveal mixed-facing source strips; exact runtime cull handling unresolved. Two-sided diagnostic is not an automatic repair or L2 parity pass.',
            'pose':'source rest matrices recovered; animation, gravity-settled suspension and steering not evaluated',
            'variants':'all named LOD/member slots enumerated, numeric tuple runtime selector meaning unresolved',
            'units':'no source physical-unit conversion or MR fit applied',
            'identity':'NISSAN original label Pickup; D22 generation needs additional source confirmation',
            'integration':'no Master Rallye compiler, candidate, CarID or gameplay in this phase'}.items()]}
    world={};by_node={n['id']:n for n in nodes}
    def world_matrix(key):
        if key not in world:
            node=by_node[key];parent=node['parent_id'];local=node['local_transform']
            world[key]=uvs.multiply(world_matrix(parent),local)if parent is not None else local[:]
        return world[key]
    for node in nodes:world_matrix(node['id'])
    by_mesh={m['id']:m for m in meshes};points=[];wheels={}
    for node in nodes:
        points.extend(uvs.transform_point(world[node['id']],p)for mid in node['mesh_ids']for p in by_mesh[mid]['positions'])
        if node['role']=='wheel':wheels[node['name']]=uvs.transform_point(world[node['id']],[0.,0.,0.])
    scene['measurements']={'source_bounds':[[min(p[k]for p in points)for k in range(3)],[max(p[k]for p in points)for k in range(3)]],
        'original_rest_wheel_origins':wheels,'units':'unscaled original numerical units'}
    assets['inspection/sbb-catalog.json']=uvs.canonical(catalog)
    result=uvs.save_scene(scene,output,assets,protected_roots=protected)
    return {**result,'vehicle':vehicle,'source_unchanged':True,'measurements':scene['measurements']}
