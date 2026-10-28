"""Paris-Dakar qualified source scenes. Never calls the native MR bridge."""
from __future__ import annotations
from pathlib import Path
import re
from .. import universal_vehicle_scene as uvs
from . import paris_dakar_formats as fmt

VERSION='paris-dakar-source/1'
QUALIFIED={
    'PajeroRED.tc':'38b1d5ba438b3b384e029ab4feb395907ea7f6436e27dc40efa0ed0e53964d7d',
    'PajeroSilver.tc':'fe5b111f88309fa8167d9df8a996a8d478c912a2a189126d5534bad3f14a82ae',
    'NissanPatrol.tc':'acdb8fc6ae19e6c4dce83e60b35bc86885389f4d3cf89812dce609c40801b765',
}
NORMALIZATION=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,-1.,0.,0.,0.,0.,1.]


def inspect(data,keys):
    tc=fmt.container(data,keys)
    models={};textures={};vertices=triangles=texture_bytes=0
    for entry in tc['entries']:
        b=data[entry['offset']:entry['offset']+entry['bytes']]
        if b[:4]==b'Gex#':
            model=fmt.gex(b);vertices+=model['vertices'];triangles+=model['triangles']
            if vertices>uvs.MAX_VERTICES or triangles>uvs.MAX_TRIANGLES:raise ValueError('TC aggregate geometry budget')
            models[entry['name']]=model
        elif b[:4]==b'\x10\0\0\0':
            meta=fmt.tim(b)[0];texture_bytes+=meta['width']*meta['height']*4
            if texture_bytes>uvs.MAX_TEXTURE_BYTES or len(textures)>=255:raise ValueError('TC aggregate texture budget')
            textures[entry['name']]=meta
    by={e['name'].casefold():e for e in tc['entries']}
    row=by.get('description')
    if row is None:raise ValueError('missing original vehicle Description')
    desc=fmt.description(data[row['offset']:row['offset']+row['bytes']])
    for key in ('Body','BodyShadow','FrontWheel','RearWheel','FrontWheelShadow','RearWheelShadow'):
        value=desc['references'].get(key,{}).get('value','NULL')
        if value!='NULL' and value not in models:raise ValueError('missing/mismatched assembly resource: '+value)
    for obj in desc['objects']:
        if obj['member'] not in ('None','NULL') and obj['member'] not in models:
            raise ValueError('missing original detachable object: '+obj['member'])
    for model in models.values():
        for tex in model['textures']:
            if Path(tex).suffix.lower()!='.3df' or tex[:-4] not in textures:
                raise ValueError('missing original material texture: '+tex)
    return tc,desc,models,textures


def create_scene(source_root: Path, output: Path, catalog='PajeroRED.tc'):
    root=Path(source_root).absolute();output=Path(output).absolute()
    if catalog not in QUALIFIED:raise ValueError('unqualified vehicle selection')
    # All owner sources and tool caches protected, including sibling games.
    protected=[root,root.parent,root.parent.parent/'tools',Path(__file__).resolve().parents[3]/'tools']
    uvs.output_directory(output,protected)
    exe=uvs.read_bounded(root/'dakar.exe',4*1024*1024);keys=fmt.executable_keys(exe)
    path=root/'Data'/catalog;data=uvs.read_bounded(path,fmt.MAX_FILE)
    if uvs.sha(data)!=QUALIFIED[catalog]:raise ValueError('qualified source TC hash mismatch')
    tc,desc,models,texmeta=inspect(data,keys)
    entries={row['name']:row for row in tc['entries']}
    assets={'original/'+catalog:data};resources=[]
    for e in tc['entries']:
        b=data[e['offset']:e['offset']+e['bytes']]
        snapshot='resources/r%04d.bin'%e['index'];assets[snapshot]=b
        resources.append({'member':e['name'],'offset':e['offset'],'bytes':e['bytes'],'sha256':e['sha256'],
                          'snapshot_path':snapshot,'tc_sha256':uvs.sha(data),'directory_index':e['index']})
    recs={r['member']:r for r in resources};textures=[];texture_ids={}
    for texname,meta in texmeta.items():
        entry=entries[texname];tid='tex-%04d'%entry['index'];b=data[entry['offset']:entry['offset']+entry['bytes']]
        meta,rgba,samples,palette=fmt.tim(b)
        p='textures/'+tid;assets[p+'.rgba']=rgba;assets[p+'.indices']=samples;assets[p+'.palette']=palette
        meta['source_channels'].update(raw_samples_path=p+'.indices',palette_path=p+'.palette')
        textures.append({'id':tid,'name':texname,**meta,'rgba_path':p+'.rgba','rgba_sha256':uvs.sha(rgba),'source':recs[texname]})
        texture_ids[texname]=tid
    # White neutral fallback is used only for original UNTEXTURED shadow geometry.
    fallback=b'\xff'*4;assets['textures/neutral-white.rgba']=fallback
    textures.append({'id':'neutral-white','width':1,'height':1,'rgba_path':'textures/neutral-white.rgba',
                     'rgba_sha256':uvs.sha(fallback),'source_channels':{'status':'DERIVED neutral untextured visualization, not donor image'}})
    materials=[];meshes=[];model_ids={};source_report={}
    for modelname,model in models.items():
        e=entries[modelname];prefix='r%04d'%e['index'];ids=[]
        used={b['material_index']for b in model['batches']}
        for mi in sorted(used):
            mat=model['materials'][mi];ti=mat['texture_index']
            if ti!=32000 and ti>=len(model['textures']):raise ValueError('invalid material texture index')
            texname=model['textures'][ti][:-4] if ti!=32000 else None
            tid=texture_ids[texname] if texname else 'neutral-white'
            # Bit8 of original texture flags is alpha-bearing in original loader.
            alpha=bool(texname and texmeta[texname]['flags_raw']&8)
            token=mat['name'].split('_',1)[0]
            suffix=re.search(r'([0-9A-Fa-f]{8})([0-9A-Fa-f]{3})$',token)
            material={'id':prefix+'-mat-%02d'%mi,'name':mat['name'],'diffuse_texture_id':tid,
                      'raw_fields':mat['raw_fields'],'source':{'member':modelname,'offset':mat['offset'],
                                                               'member_sha256':e['sha256']},
                      'flags':{'transparent_raw':str(int(alpha)), 'source_texture_alpha_bit':int(alpha)},
                      'decoded_name_fields':{'flags_hex':suffix[1],'type_hex':suffix[2]} if suffix else None,
                      'unsupported':['original material dispatch, lighting, reflections and damage transitions'],
                      'preview':{'opacity':1.0,'policy':'source RGBA palette; neutral blend when original texture bit8 set'}}
            materials.append(material)
            # Material groups preserve batch/vertex order and provenance; no weld.
            positions=[];normals=[];uv=[];tri=[];batches=[]
            for batch in model['batches']:
                if batch['material_index']!=mi:continue
                base=len(positions);positions.extend(batch['positions']);normals.extend(batch['normals']);uv.extend(batch['uvs'])
                tri.extend([[base+i for i in face]for face in batch['triangles']])
                batches.append({'offset':batch['offset'],'bytes':batch['bytes'],'first_vertex':base,'vertices':len(batch['positions'])})
            mid=prefix+'-mat-%02d'%mi;ids.append(mid)
            meshes.append({'id':mid,'name':modelname+'/'+mat['name'],'positions':positions,'normals':normals,
                           'uvs':uv,'triangles':tri,'material_id':material['id'],
                           'source':{'member':modelname,'member_sha256':e['sha256'],'batches':batches,
                                     'original_mesh_id':prefix,'material_index':mi,
                                     'vertex_layout':'px py pz nz u v nx ny; IEEE754 LE',
                                     'winding':'original ordered triangle list; index bytes divided by3'}})
        model_ids[modelname]=ids
        source_report[modelname]={k:v for k,v in model.items()if k!='batches'}
        source_report[modelname]['batch_spans']=[{k:v for k,v in b.items()if k in ('offset','bytes','material_index','header_hex')}for b in model['batches']]
    nodes=[]
    def instance(id_,member,position,*,role='body',side=0,visible=True,evidence=None):
        if member=='NULL':return
        mat=uvs.IDENTITY[:];mat[3],mat[7],mat[11]=position
        if side:mat[0]=mat[10]=-1.
        nodes.append({'id':id_,'name':member,'parent_id':None,'mesh_ids':model_ids[member],
                      'local_transform':mat,'source_local_transform':None,'role':role,
                      'visible':visible,'source_visible':visible,
                      'source_transform_record':{'translation':position,'rotation_y_radians':3.141592653589793 if side else 0.,
                                                 'rotation_evidence':'0051a160 side argument0/1 from004f7ed3; Y rotation0/pi'},
                      'transform_evidence':evidence or 'Description object-space position, original part geometry; derived grouping'})
    refs=desc['references'];body=refs['Body']['value'];instance('body',body,[0.,0.,0.])
    instance('body-shadow',refs['BodyShadow']['value'],[0.,0.,0.],role='shadow',visible=False)
    seen=set()
    for obj in desc['objects']:
        member=obj['member']
        if member in ('None','NULL'):continue
        if member in seen or 'position'not in obj:raise ValueError('ambiguous detachable object placement')
        seen.add(member);instance('part-r%04d'%entries[member]['index'],member,obj['position'],evidence=obj)
    for i,wheel in enumerate(desc['wheels']):
        member=refs['FrontWheel'if i<2 or refs['RearWheel']['value']=='NULL'else'RearWheel']['value']
        instance('wheel-%d'%i,member,wheel['attach_point'],role='wheel',side=i%2,
                 evidence={'description_offset':wheel['offset'],'datum':'ORIGINAL_ATTACH_POINT static inspection, not gravity-settled hub',
                           'native_evidence':'004f7ed3 shares FrontWheel when RearWheel NULL;0051a160 side rotation'})
    positions=[]
    bymesh={m['id']:m for m in meshes}
    for node in nodes:
        if node['visible']:
            for mid in node['mesh_ids']:positions.extend(uvs.transform_point(node['local_transform'],p)for p in bymesh[mid]['positions'])
    lo=[min(p[k]for p in positions)for k in range(3)];hi=[max(p[k]for p in positions)for k in range(3)]
    wheels=desc['wheels'];hub=[w['attach_point']for w in wheels]
    measurements={'assembly_source_bounds':[lo,hi],'assembly_source_size':[b-a for a,b in zip(lo,hi)],
                  'wheelbase_attach':(hub[0][2]+hub[1][2]-hub[2][2]-hub[3][2])/2,
                  'front_track_attach':hub[1][0]-hub[0][0],'rear_track_attach':hub[3][0]-hub[2][0],
                  'suspension_original':wheels,'wheel_geometry_bounds':models[refs['FrontWheel']['value']]['bounds_original'],
                  'units':'original numerical units; metre interpretation plausible, physical scale not independently qualified',
                  'pose':'static original attach datum; suspension solver/options/gravity settling NOT TESTED'}
    assets['inspection/container.json']=uvs.canonical(tc)
    assets['inspection/models.json']=uvs.canonical(source_report)
    scene={'schema':uvs.SCHEMA,'metadata':{'adapter':VERSION,'display_name':'Paris-Dakar '+catalog[:-3],
            'neutral_preview':{'cull':'cw','evidence':'original triangle/normal alignment; original D3D FVF112 loader; paired CW/CCW neutral diagnostics'},
            'implementation_sha256':{Path(p).name:uvs.sha(Path(p).read_bytes())for p in (__file__,fmt.__file__)},
            'qualification':'L1 source reconstruction, neutral static pose; no native import'},
           'source':{'game':'Paris-Dakar Rally (2001)','root':str(root),'protected_roots':list(map(str,protected)),
                     'catalog':'Data/'+catalog,'container_sha256':uvs.sha(data),'executable_sha256':uvs.sha(exe),
                     'resources':resources,'description_original':desc,
                     'authenticity':'owner-local Windows installation; exact edition/region publisher authenticity not independently established'},
           'coordinate_system':{'source':{'up_axis':[0,1,0],'forward_axis':[0,0,1],'right_axis':[1,0,0],'units':'source units'},
                                'normalized':{'up_axis':[0,1,0],'forward_axis':[0,0,-1],'right_axis':[1,0,0],'units':'source units'},
                                'source_to_normalized':NORMALIZATION[:],
                                'interpretation_status':'static source-backed axes; reversible mirrorZ, no physical rescale',
                                'evidence':['Description FrontWheel/suspension order0,1 versus2,3; positiveY body/roof',
                                            '0051a160 original0/pi side rotation;00491cf0 vertex reorder; geometric face/normal agreement']},
           'meshes':meshes,'materials':materials,'textures':textures,'nodes':nodes,'measurements':measurements,
           'selection':{'body_texture_references':'original resource names, no livery remap','wheel_pose':'attach datum, zero steer/spin',
                        'shadow_pass':'recovered geometry retained, disabled in neutral body pass'},
           'unknown_semantics':[{'id':'suspension','status':'NOT TESTED','meaning':'attach datum is not gravity-settled running pose; native options alter suspension'},
                                {'id':'material','status':'WARN','meaning':'original flags/name tokens/palettes retained; native specular/reflection/blend dispatch not reproduced'},
                                {'id':'variants','status':'WARN','meaning':'all original texture variants preserved; runtime damage/livery selection not implemented'},
                                {'id':'hierarchy','status':'WARN','meaning':'flat resources plus Description assembly links; derived nodes are not invented source parent transforms'},
                                {'id':'scale','status':'WARN','meaning':'axis signs source-backed; physical metre interpretation not independently qualified'},
                                {'id':'runtime','status':'NOT TESTED','meaning':'no original donor renderer parity, MR compilation or gameplay'}]}
    result=uvs.save_scene(scene,output,assets,protected_roots=protected)
    if uvs.sha(uvs.read_bounded(path,fmt.MAX_FILE))!=QUALIFIED[catalog]:raise ValueError('source changed during extraction')
    return {**result,'measurements':measurements,'catalog':catalog,'source_unchanged':True}
