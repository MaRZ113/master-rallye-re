"""Compatibility snapshot of an existing qualified native family into UVS.

This is an editable migration of already converted/Classic MR assets, not a new
GT decoder or a claim to recover original GT shader/mesh identities. Existing
GT projects and compilers remain untouched. Wheel transforms must be proven by
the existing exact frontend/race correspondence service; no guessed hub fitting.
"""
from pathlib import Path
from . import universal_vehicle_scene as u
from .dx import parse_dx_bytes
from .dxt import parse_dxt_bytes
from .topology_writer import source_geometry
from .preview_scene import presentation_wheels


def snapshot(root,output):
    root=Path(root).absolute();u.unlinked(root)
    blobs={};models={};input_bytes=0
    for name in('car.dx','complete.dx','wheel.dx'):
        raw=u.read_bounded(root/name,64*1024*1024);input_bytes+=len(raw)
        if input_bytes>u.MAX_OUTPUT_BYTES:raise ValueError('Native migration input byte budget')
        model=parse_dx_bytes(raw)
        if not model.diagnostics.validated:raise ValueError('Invalid native family geometry')
        if any(d.tag!=2 or len(d.texture_tuple)!=3 for d in model.physical_draws):raise ValueError('Flattening existing native controllers is not an editable migration')
        if (len(model.physical_draws)>1024 or sum(d.local_vertex_max+1 for d in model.physical_draws)>u.MAX_VERTICES or
                sum(d.triangle_count for d in model.physical_draws)>u.MAX_TRIANGLES):raise ValueError('Native migration geometry allocation budget')
        blobs[name]=raw;models[name]=model
    profile=root/'preview-profile.json';profile_blob=None
    if profile.is_file():
        profile_blob=u.read_bounded(profile,1024*1024);doc=u.load_json(profile_blob)
        instances=doc.get('race_wheel_instances')
        if not isinstance(instances,list)or len(instances)!=4 or not doc.get('provenance'):raise ValueError('Explicit native preview profile needs four wheel instances and provenance')
        from .preview_scene import preview_transform
        for instance in instances:preview_transform(instance)
        transforms={'race_wheel_instances':instances,'provenance':'Existing explicit MR preview-profile authoring reference sha256='+u.sha(profile_blob)+'; not newly recovered donor hubs'}
    else:transforms=presentation_wheels(models['car.dx'],models['complete.dx'],models['wheel.dx'])
    assets={};resources=[];textures={};materials=[];meshes=[];body=[];wheel=[];stored_bytes=0;decoded_bytes=0
    def original(name,raw):
        nonlocal stored_bytes
        stored_bytes+=len(raw)
        if stored_bytes>u.MAX_OUTPUT_BYTES:raise ValueError('Native snapshot byte budget')
        path='original/'+name;assets[path]=raw
        resources.append({'member':name,'snapshot_path':path,'bytes':len(raw),'sha256':u.sha(raw)})
    for name,raw in blobs.items():original(name,raw)
    if profile_blob is not None:original('preview-profile.json',profile_blob)
    for filename in('car.dx','wheel.dx'):
        model=models[filename];geometry=source_geometry(model)
        for index,draw in enumerate(model.physical_draws):
            if draw.triangle_count==0:continue
            diffuse=draw.texture_tuple[0]
            if diffuse=='Null':raise ValueError('Native untextured draw needs an explicit authored texture, not an invented donor atlas')
            if Path(diffuse).name!=diffuse or '/'in diffuse or '\\'in diffuse or ':'in diffuse:raise ValueError('Unsafe native texture binding')
            if diffuse not in textures:
                raw=u.read_bounded(root/(diffuse+'.dxt'),u.MAX_TEXTURE_BYTES);texture=parse_dxt_bytes(raw);original(diffuse+'.dxt',raw)
                decoded_bytes+=len(texture.bgra);stored_bytes+=len(texture.bgra)
                if decoded_bytes>u.MAX_TEXTURE_BYTES or stored_bytes>u.MAX_OUTPUT_BYTES or len(textures)>=256:raise ValueError('Native texture migration allocation budget')
                rgba=bytearray(texture.bgra);rgba[0::4],rgba[2::4]=rgba[2::4],rgba[0::4];path='textures/'+diffuse+'.rgba';assets[path]=bytes(rgba)
                textures[diffuse]={'id':diffuse,'width':texture.width,'height':texture.height,'rgba_path':path,'rgba_sha256':u.sha(rgba),
                                   'source_channels':{'mode':'Native MR BGRA converted losslessly to RGBA; stored rows preserved'}}
            key=filename+'-draw-'+str(index);g=geometry[index]
            materials.append({'id':key,'diffuse_texture_id':diffuse,'raw_fields':[{'native_draw':index,'native_textures':list(draw.texture_tuple)}],
                              'flags':{'transparent_raw':str(int(bool(draw.flags_0x20[0]))),'reflective_raw':str(int(bool(draw.unknown_0x24&4)))},
                              'unsupported':['Native reference reflection/controller behavior requires explicit derived material assignment']})
            meshes.append({'id':key,'name':key,'material_id':key,'positions':[list(v.position)for v in g.vertices],
                           'normals':[list(v.normal)for v in g.vertices],'uvs':[list(v.uvs[0])for v in g.vertices],
                           'preview_colors_bgra':[list(v.color)for v in g.vertices],'triangles':[list(t)for t in g.triangles],
                           'source':{'member':filename,'member_sha256':u.sha(blobs[filename]),'native_draw':index}})
            (body if filename=='car.dx'else wheel).append(key)
    nodes=[{'id':'body','name':'Native family body','mesh_ids':body,'parent_id':None,'local_transform':u.IDENTITY[:],
            'source_local_transform':u.IDENTITY[:],'visible':True,'source_visible':True,'role':'body','transform_evidence':'Existing native race coordinate frame'}]
    for i,transform in enumerate(transforms['race_wheel_instances']):
        from .preview_scene import preview_transform
        vector,_=preview_transform(transform)
        matrix=u.IDENTITY[:]
        for axis in range(3):
            basis=[int(k==axis)for k in range(3)];point=vector(basis,True)
            for row in range(3):matrix[row*4+axis]=point[row]-transform['translation'][row]
        for axis in range(3):matrix[axis*4+3]=transform['translation'][axis]
        nodes.append({'id':'wheel-'+str(i),'name':'Native rest wheel '+str(i),'mesh_ids':wheel[:],'parent_id':None,
                      'local_transform':matrix,'source_local_transform':matrix[:],'visible':True,'source_visible':True,'role':'wheel',
                      'transform_evidence':transforms['provenance']})
    scene={'schema':u.SCHEMA,'metadata':{'adapter':'native-family-editable-compatibility/1','display_name':root.parent.name+' — native baseline snapshot',
             'identity_boundary':'Existing MR-converted geometry; this snapshot does not claim original GT mesh identity'},
           'source':{'root':str(root),'catalog':'native-family','resources':resources},
           'coordinate_system':{'source_to_normalized':u.IDENTITY[:],'interpretation_status':'Existing native MR coordinates','evidence':[transforms['provenance']]},
           'unknown_semantics':[{'id':'migration','status':'WARN','meaning':'Static native baseline; no original GT renderer or new runtime-controller equivalence'}],
           'textures':list(textures.values()),'materials':materials,'meshes':meshes,'nodes':nodes}
    return u.save_scene(scene,Path(output),assets,protected_roots=[root])
