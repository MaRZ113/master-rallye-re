"""Read-only common preflight; source fidelity, compiler and gameplay stay separate."""
from pathlib import Path
from copy import deepcopy
import math
from . import universal_vehicle_scene as u
from . import scene_semantics as semantic


def conservation(scene,compiled):
    meshes={m['id']:m for m in scene['meshes']};maximum=0.;normal_error=0.;triangles=0;unchanged_uv=True
    if len(compiled['report']['complete_draws'])!=len(compiled['complete_parts']):raise ValueError('unaccounted native draw')
    for record,part in zip(compiled['report']['complete_draws'],compiled['complete_parts']):
        mesh=meshes[record['mesh_id']];inverse=record['mr_to_source']
        if len(part.geometry.vertices)!=len(record['source_vertex_ids']):raise ValueError('unaccounted native vertex')
        for vertex,index in zip(part.geometry.vertices,record['source_vertex_ids']):
            source=u.transform_point(inverse,vertex.position)
            maximum=max(maximum,*[abs(source[k]-mesh['positions'][index][k])for k in range(3)])
            unchanged_uv=unchanged_uv and record['source_uvs_preserved']
            uv=list(vertex.uvs[0])
            if record['derived_uv_v_policy']=='flip':uv[1]=1.-uv[1]
            if any(abs(uv[k]-mesh['uvs'][index][k])>1e-6 for k in range(2)):raise ValueError('source UV conservation failure')
            if not all(math.isfinite(x)for x in (*vertex.position,*vertex.normal)):raise ValueError('nonfinite native geometry')
            forward=record['source_to_mr']
            restored=[sum(forward[4*k+j]*vertex.normal[k]for k in range(3))for j in range(3)]
            length=math.hypot(*restored);original=mesh['normals'][index];source_length=math.hypot(*original)
            if min(length,source_length)<1e-12:raise ValueError('unqualified zero native/source normal')
            normal_error=max(normal_error,*[abs(restored[j]/length-original[j]/source_length)for j in range(3)])
        expected=mesh['triangles'];actual=part.geometry.triangles
        used=record['source_vertex_ids'];remap={old:new for new,old in enumerate(used)}
        corners=(0,2,1)if record['winding_reversed']else(0,1,2)
        if actual!=tuple(tuple(remap[face[k]]for k in corners)for face in expected):raise ValueError('source triangle conservation failure')
        triangles+=len(actual)
    if maximum>1e-6:raise ValueError('source inverse geometry error exceeds tolerance')
    if normal_error>1e-6:raise ValueError('inverse transpose normal conservation failed')
    return {'max_source_roundtrip_error':maximum,'max_source_normal_error':normal_error,'instanced_triangles':triangles,'uvs_preserved':unchanged_uv,'uv_conversion_reversible':True,'determinant_winding_verified':True}


def preflight(path,*,profile=None,semantics=None):
    """Return evidence, never a fabricated source/gameplay readiness score."""
    path=Path(path);scene=u.load_scene(path);digest=u.sha(u.read_bounded(path,u.MAX_JSON_BYTES))
    rows=semantic.features(scene);issues=[]
    for row in rows:issues.append({**row,'severity':'P1','status':'BLOCKED','reason':'Native disposition required; original data is retained'})
    result={'schema':'source-garage-preflight/1','source_scene_sha256':digest,
        'source_game':scene['source'].get('game'),'catalog':scene['source'].get('catalog'),
        'levels':{'L0':'PASS','L1':'PASS','L2':'WARN','L3':'BLOCKED','L4':'NOT TESTED'},
        'counts':u.validate_scene(scene),'source_unknowns':scene['unknown_semantics'],
        'material_unknowns':{m['id']:m['unsupported']for m in scene['materials']if m['unsupported']},
        'source_features':rows,'issues':issues,'native_entry_allowed':False,'native_geometry_compiler_allowed':False,'original_scene_mutated':False}
    if semantics is not None:result['semantic_ownership']=semantic.validate(scene,semantics,digest)
    if profile is None:
        issues.append({'id':'native-policy','severity':'P1','status':'BLOCKED','reason':'No qualified geometry/wheel/material/physics authoring policy selected'})
        return result
    from .universal_scene_bridge import compile_scene
    try:
        if semantics is not None:
            profile=deepcopy(profile);profile['semantics']=semantics
        compiled=compile_scene(path,profile);repeated=compile_scene(path,profile)
        if compiled!=repeated:raise ValueError('nondeterministic native compilation')
        result['conservation']=conservation(scene,compiled)
        if semantics is not None:
            parts,bindings=semantic.partition(compiled,scene,semantics)
            result['semantic_partition']={'parts':len(parts),'triangles':sum(len(p.geometry.triangles)for p in parts),
                'source_bindings':bindings,'material_flags_changed':False,'native_controllers_created':False}
        result['native_texture_sha256']={k:u.sha(v)for k,v in sorted(compiled['textures'].items())}
        result['hubs']=compiled['report']['hubs']
        dispositions=compiled['report'].get('source_feature_dispositions',[])
        by_id={r['id']:r for r in dispositions}
        result['issues']=[{**row,'status':by_id[row['id']]['status'],
                           'reason':by_id[row['id']].get('impact',by_id[row['id']]['disposition'])}if row['id']in by_id else
                         {**row,'status':'NOT TESTED','severity':'P2','reason':'Feature belongs to an explicitly unselected source mesh/material; retained, not compiled'}for row in issues]
        result['levels']['L3']='WARN'
        result['native_geometry_compiler_allowed']=True
        if set(profile['wheel_slots'])!={'front_left','front_right','rear_left','rear_right'}:
            result['native_geometry_compiler_allowed']=False;result['levels']['L3']='BLOCKED'
            result['issues'].append({'id':'native-wheel-controller','severity':'P1','status':'BLOCKED','reason':'Existing native authoring requires four explicit FL/FR/RL/RR slots; geometric instances alone do not qualify more/different controllers'})
        result['native_boundary']='Deterministic geometry/material compiler only; native controllers, wheel motion, collision/physics and live D3D8 require separate qualification'
        result['source_feature_dispositions']=dispositions
    except ValueError as error:
        result['issues'].append({'id':'native-compile','severity':'P1','status':'BLOCKED','reason':str(error)})
    if u.sha(u.read_bounded(path,u.MAX_JSON_BYTES))!=digest:raise ValueError('source scene changed during preflight')
    return result
