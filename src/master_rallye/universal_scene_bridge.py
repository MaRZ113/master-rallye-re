"""Qualified neutral scene -> common MR SceneParts, independent of source games.

This bridge does not parse donor formats, write native controllers, choose a
physics donor or allocate a roster. The caller uses the existing scene DX writer
and SDK authoring services. Original scene arrays and sidecars remain immutable.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path
import struct
import zlib

from . import universal_vehicle_scene as uvs
from .dxt import parse_dxt_bytes
from .scene_dx_writer import ScenePart
from .topology_writer import CompiledVertex, DrawGeometry

SCHEMA='universal-scene-mr-profile/1'
MAX_DRAWS=8192
MAX_VERTICES=1000000
MAX_TRIANGLES=2000000
MAX_TEXTURE_BYTES=64*1024*1024


def inverse_affine(matrix):
    """Inverse of the evidenced row-major affine transform; no guessed basis."""
    uvs.matrix(matrix)
    a=matrix;d=uvs.determinant(a)
    inv=[(a[5]*a[10]-a[6]*a[9])/d,(a[2]*a[9]-a[1]*a[10])/d,(a[1]*a[6]-a[2]*a[5])/d,0.,
         (a[6]*a[8]-a[4]*a[10])/d,(a[0]*a[10]-a[2]*a[8])/d,(a[2]*a[4]-a[0]*a[6])/d,0.,
         (a[4]*a[9]-a[5]*a[8])/d,(a[1]*a[8]-a[0]*a[9])/d,(a[0]*a[5]-a[1]*a[4])/d,0.,0.,0.,0.,1.]
    for r in range(3):inv[4*r+3]=-sum(inv[4*r+k]*a[4*k+3]for k in range(3))
    uvs.matrix(inv)
    return inv


def _normal(inverse,normal):
    transformed=[sum(inverse[4*k+r]*normal[k]for k in range(3))for r in range(3)]
    length=math.hypot(*transformed)
    if not math.isfinite(length)or length<1e-12:raise ValueError('source normal cannot be transformed')
    return tuple(v/length for v in transformed)


def _nonempty(value,label):
    if not isinstance(value,str)or not value.strip():raise ValueError(label+' evidence required')


def _rgba(value,label):
    if not isinstance(value,list)or len(value)!=4 or any(type(v)is not int or not 0<=v<=255 for v in value):
        raise ValueError('invalid '+label+' RGBA')
    return value


def _profile(profile,scene,scene_hash):
    required={'schema','source_scene_sha256','normalized_to_mr','authoring_transform','transform_evidence',
              'body_node_ids','wheel_slots','canonical_wheel_slot','materials','texture_row_policy','uv_v_policy'}
    optional={'hub_overrides','hub_evidence'}
    if not isinstance(profile,dict)or set(profile)-required-optional or not required<=set(profile)or profile['schema']!=SCHEMA:
        raise ValueError('unsupported neutral scene MR profile')
    if profile['source_scene_sha256']!=scene_hash:raise ValueError('immutable source scene/profile hash mismatch')
    uvs.matrix(profile['normalized_to_mr']);uvs.matrix(profile['authoring_transform'])
    _nonempty(profile['transform_evidence'],'basis/authoring transform')
    if profile['texture_row_policy']not in ('preserve','flip_vertical')or profile['uv_v_policy']not in ('preserve','flip'):
        raise ValueError('explicit texture-row and UV-V policies required')
    nodes={node['id']:node for node in scene['nodes']}
    body=profile['body_node_ids'];wheels=profile['wheel_slots']
    if not isinstance(body,list)or not body or any(not isinstance(k,str)or k not in nodes for k in body)or len(set(body))!=len(body):
        raise ValueError('explicit unique body node selection required')
    if not isinstance(wheels,dict)or not 1<=len(wheels)<=16 or any(not isinstance(k,str)or not k or not isinstance(v,str)or v not in nodes for k,v in wheels.items()):
        raise ValueError('explicit wheel node instances required')
    if len(set(wheels.values()))!=len(wheels)or set(body)&set(wheels.values()):raise ValueError('body/wheel source instances overlap')
    if profile['canonical_wheel_slot']not in wheels:raise ValueError('explicit canonical wheel slot required')
    overrides=profile.get('hub_overrides',{})
    if not isinstance(overrides,dict):raise ValueError('explicit derived hub override map required')
    for slot,point in overrides.items():
        if slot not in wheels:raise ValueError('hub override has no selected source wheel')
        uvs.vector(point,3);_nonempty(profile.get('hub_evidence'),'derived hub fit')
    mats=profile['materials']
    if not isinstance(mats,dict):raise ValueError('explicit material approvals required')
    source_materials={row['id']for row in scene['materials']}
    for key,rule in mats.items():
        if key not in source_materials or not isinstance(rule,dict):raise ValueError('unknown source material approval')
        keys={'mode','interpretation','role','evidence','vertex_rgba','alpha_override','allow_alpha_flatten','alpha_ref','environment_reference'}
        if set(rule)-keys or rule.get('mode')not in ('opaque','alpha_blend','alpha_test')or rule.get('interpretation')not in ('mr_authoring','source_qualified'):
            raise ValueError('unsupported MR material interpretation')
        _nonempty(rule.get('role'),'material role');_nonempty(rule.get('evidence'),'material')
        _rgba(rule.get('vertex_rgba',[255]*4),'vertex')
        if 'allow_alpha_flatten'in rule and type(rule['allow_alpha_flatten'])is not bool:raise ValueError('alpha flatten policy must be boolean')
        if 'alpha_override'in rule:
            if rule['interpretation']!='mr_authoring'or type(rule['alpha_override'])is not int or not 0<=rule['alpha_override']<=255:
                raise ValueError('alpha override requires explicit MR authoring interpretation')
            if rule['mode']=='opaque'and rule['alpha_override']!=255:raise ValueError('opaque mode conflicts with alpha override')
        if rule['mode']=='alpha_test':
            if type(rule.get('alpha_ref'))is not int or not 0<=rule['alpha_ref']<=255:raise ValueError('explicit source cutout reference required')
        elif 'alpha_ref'in rule:raise ValueError('alpha reference requires cutout mode')
    return nodes


def _texture(tex,rule,root):
    raw=uvs.read_bounded(root/tex['rgba_path'],tex['width']*tex['height']*4)
    if uvs.sha(raw)!=tex['rgba_sha256']:raise ValueError('source texture changed during compilation')
    pixels=bytearray(raw)
    mode=rule['mode']
    if mode=='opaque'and any(v!=255 for v in pixels[3::4])and not rule.get('allow_alpha_flatten',False):
        raise ValueError('opaque conversion would discard unapproved source alpha')
    if 'alpha_override'in rule:pixels[3::4]=bytes([rule['alpha_override']])*(len(pixels)//4)
    if mode=='opaque':pixels[3::4]=b'\xff'*(len(pixels)//4)
    elif mode=='alpha_test':pixels[3::4]=bytes(255 if v>=rule['alpha_ref']else 0 for v in pixels[3::4])
    return pixels


def _dxt(width,height,rgba,row_policy):
    stride=width*4
    rows=range(height)if row_policy=='preserve'else reversed(range(height))
    raw=bytearray()
    for row in rows:
        for k in range(row*stride,(row+1)*stride,4):
            r,g,b,a=rgba[k:k+4];raw.extend((b,g,r,a))
    data=struct.pack('<5I',0xfeed,1,zlib.crc32(raw)&0xffffffff,width,height)+raw
    parse_dxt_bytes(data)
    return data


def compile_scene(scene_path,profile,*,references=None):
    """Return common writer inputs and provenance; perform no filesystem writes.

    wheel_parts_by_slot preserves each selected source instance's exact local
    geometry. A canonical selection alone does not establish that MR's shared
    runtime wheel template reproduces the other source wheel variants.
    """
    path=Path(scene_path);raw=uvs.read_bounded(path,uvs.MAX_JSON_BYTES)
    scene=uvs.load_scene(path);source_hash=uvs.sha(raw)
    if uvs.canonical(scene)!=raw:raise ValueError('canonical immutable scene serialization required')
    nodes=_profile(profile,scene,source_hash)
    meshes={row['id']:row for row in scene['meshes']};materials={row['id']:row for row in scene['materials']}
    textures={row['id']:row for row in scene['textures']};references=references or {}
    world={};visibility={}
    def node_world(key):
        if key in world:return world[key]
        node=nodes[key];parent=node['parent_id'];matrix=node['local_transform'][:]
        if parent is not None:matrix=uvs.multiply(node_world(parent),matrix)
        world[key]=matrix;visibility[key]=node['visible']and(parent is None or visibility[parent])
        return matrix
    for key in nodes:node_world(key)
    basis=uvs.multiply(profile['normalized_to_mr'],scene['coordinate_system']['source_to_normalized'])
    fit_basis=uvs.multiply(profile['authoring_transform'],basis)
    inverse_affine(fit_basis)
    output_textures={};texture_cache={};material_audit={};total_texture=0
    def material(key):
        nonlocal total_texture
        if key in texture_cache:return texture_cache[key]
        if key not in profile['materials']:raise ValueError('selected source material lacks explicit MR approval: '+key)
        rule=profile['materials'][key];source=materials[key];tex=textures[source['diffuse_texture_id']]
        pixels=_texture(tex,rule,path.parent)
        data=_dxt(tex['width'],tex['height'],pixels,profile['texture_row_policy'])
        name='uvs-'+uvs.sha(data)[:24]+'-tga';filename=name+'.dxt'
        if filename not in output_textures:output_textures[filename]=data;total_texture+=len(data)
        helper='Null'
        if rule.get('environment_reference')is not None:
            ref=rule['environment_reference']
            if not isinstance(ref,dict)or set(ref)!={'key','sha256'}or not isinstance(ref.get('key'),str):raise ValueError('pinned native environment reference required')
            blob=references.get(ref['key'])
            if not isinstance(blob,bytes)or uvs.sha(blob)!=ref['sha256']:raise ValueError('native environment reference hash mismatch')
            parse_dxt_bytes(blob);helper='uvs-env-'+uvs.sha(blob)[:24]+'-tga'
            if helper+'.dxt'not in output_textures:output_textures[helper+'.dxt']=blob;total_texture+=len(blob)
        if total_texture>MAX_TEXTURE_BYTES:raise ValueError('derived MR texture budget')
        texture_cache[key]=(name,helper,'Null')
        material_audit[key]={'source_material_id':key,'source_texture_id':tex['id'],'source_rgba_sha256':tex['rgba_sha256'],
                             'source_raw_fields':copy.deepcopy(source['raw_fields']),'source_unsupported':copy.deepcopy(source['unsupported']),
                             'approval':copy.deepcopy(rule),'native_textures':list(texture_cache[key]),'native_dxt_sha256':uvs.sha(data),
                             'source_channel_metadata':copy.deepcopy(tex['source_channels']),
                             'bump_mapping':'UNSUPPORTED; original binding retained in source scene'if source.get('bump_texture_id')else'not declared',
                             'boundary':'MR authoring interpretation; no source shader/rendering parity claim'}
        return texture_cache[key]
    emitted_vertices=emitted_triangles=0
    def parts_for(key,matrix,kind,slot=None):
        nonlocal emitted_vertices,emitted_triangles
        node=nodes[key]
        if not visibility[key]:raise ValueError('explicit selection contains a hidden source node: '+key)
        inverse=inverse_affine(matrix);mirrored=uvs.determinant(matrix)<0;parts=[];maps=[]
        for mesh_id in node['mesh_ids']:
            mesh=meshes[mesh_id];triangles=mesh['triangles']
            if not triangles:raise ValueError('selected source mesh has no triangles')
            used=sorted({i for face in triangles for i in face});remap={source:target for target,source in enumerate(used)}
            emitted_vertices+=len(used);emitted_triangles+=len(triangles)
            if len(used)>65536 or emitted_vertices>MAX_VERTICES or emitted_triangles>MAX_TRIANGLES:
                raise ValueError('instanced native geometry budget')
            native_texture=material(mesh['material_id']);rule=profile['materials'][mesh['material_id']]
            rgba=rule.get('vertex_rgba',[255]*4);r,g,b,a=rgba;compiled=[]
            for source_index in used:
                position=tuple(uvs.transform_point(matrix,mesh['positions'][source_index]))
                normal=_normal(inverse,mesh['normals'][source_index]);uv=mesh['uvs'][source_index]
                target_uv=(uv[0],1.-uv[1]if profile['uv_v_policy']=='flip'else uv[1])
                # Scene writer stores float32; reject overflow before caller writes.
                try:struct.pack('<8f',*position,*normal,*target_uv)
                except (OverflowError,struct.error)as error:raise ValueError('native float32 geometry overflow')from error
                compiled.append(CompiledVertex(position,normal,bytes((b,g,r,a)),(target_uv,),parent_source_vertex_id=source_index))
            faces=tuple(tuple(remap[face[i]]for i in ((0,2,1)if mirrored else(0,1,2)))for face in triangles)
            part=ScenePart(DrawGeometry(tuple(compiled),faces),native_texture,
                           alpha=rule['mode']in('alpha_blend','alpha_test'),alpha_test=rule['mode']=='alpha_test',
                           environment=native_texture[1]!='Null')
            parts.append(part)
            maps.append({'node_id':key,'mesh_id':mesh_id,'material_id':mesh['material_id'],'kind':kind,'wheel_slot':slot,
                         'source_geometry':copy.deepcopy(mesh['source']),'source_vertex_ids':used,'source_triangle_ids':list(range(len(triangles))),
                         'source_uvs_preserved':profile['uv_v_policy']=='preserve','derived_uv_v_policy':profile['uv_v_policy'],
                         'source_to_mr':matrix[:],'mr_to_source':inverse,'transform_determinant':uvs.determinant(matrix),
                         'winding_reversed':mirrored,'normal_policy':'inverse transpose, then unit normalization; original normal array unchanged',
                         'vertices':len(used),'triangles':len(triangles)})
        return parts,maps
    body_parts=[];body_maps=[]
    for key in profile['body_node_ids']:
        parts,maps=parts_for(key,uvs.multiply(fit_basis,world[key]),'body');body_parts.extend(parts);body_maps.extend(maps)
    complete_parts=list(body_parts);complete_maps=copy.deepcopy(body_maps)
    wheel_parts_by_slot={};wheel_maps={};hub_report={}
    for slot,key in profile['wheel_slots'].items():
        original_matrix=uvs.multiply(fit_basis,world[key]);source_hub=uvs.transform_point(original_matrix,[0.,0.,0.])
        fitted_hub=profile.get('hub_overrides',{}).get(slot,source_hub)
        matrix=original_matrix[:]
        for axis in range(3):matrix[4*axis+3]+=fitted_hub[axis]-source_hub[axis]
        parts,maps=parts_for(key,matrix,'wheel_instance',slot);complete_parts.extend(parts);complete_maps.extend(maps)
        local=matrix[:]
        for axis in range(3):local[4*axis+3]-=fitted_hub[axis]
        parts,maps=parts_for(key,local,'wheel_template',slot)
        wheel_parts_by_slot[slot]=parts;wheel_maps[slot]=maps
        hub_report[slot]={'source_node_id':key,'source_world_transform':world[key][:],
                          'source_to_mr_before_hub_fit':original_matrix,'source_hub_mr':source_hub,'derived_hub_mr':list(fitted_hub),
                          'fit_delta_mr':[fitted_hub[i]-source_hub[i]for i in range(3)],
                          'source_transform_record':copy.deepcopy(nodes[key].get('source_transform_record')),
                          'source_local_transform':copy.deepcopy(nodes[key].get('source_local_transform'))}
    if not body_parts or not complete_parts or len(complete_parts)>MAX_DRAWS:raise ValueError('native draw count budget/empty body')
    for records in (body_maps,complete_maps,*wheel_maps.values()):
        for index,record in enumerate(records):record['draw_index']=index
    selected={*profile['body_node_ids'],*profile['wheel_slots'].values()}
    report={'schema':'universal-scene-mr-bridge-report/1','source_scene_sha256':source_hash,'profile_sha256':uvs.sha(uvs.canonical(profile)),
            'implementation_sha256':uvs.sha(uvs.read_bounded(Path(__file__),1024*1024)),
            'source_to_normalized':scene['coordinate_system']['source_to_normalized'][:],
            'normalized_to_mr':profile['normalized_to_mr'][:],'authoring_transform':profile['authoring_transform'][:],
            'texture_row_policy':profile['texture_row_policy'],'uv_v_policy':profile['uv_v_policy'],
            'transform_evidence':profile['transform_evidence'],'body_draws':body_maps,'complete_draws':complete_maps,
            'wheel_template_draws':wheel_maps,'hubs':hub_report,'materials':material_audit,
            'selection_exclusions':[{'node_id':key,'visible':visibility[key],'mesh_ids':nodes[key]['mesh_ids']}for key in nodes if key not in selected],
            'unknown_semantics':copy.deepcopy(scene['unknown_semantics']),
            'canonical_wheel_slot':profile['canonical_wheel_slot'],'runtime_single_wheel_safe':False,
            'wheel_boundary':'All selected exact source wheel instances retained separately. A canonical wheel alone does not qualify shared native wheel instancing.',
            'source_scene_changed':False,'runtime_qualified':False,
            'limitations':['native render/physics/dynamics not inferred','source bump/reflection semantics remain explicit unknowns',
                           'native controllers, damage, shadows and collision are authored by existing SDK services',
                           'source animation frames retained in immutable neutral scene; selected static positions compiled']}
    if uvs.sha(uvs.read_bounded(path,uvs.MAX_JSON_BYTES))!=source_hash:raise ValueError('immutable scene changed during compilation')
    canonical=profile['canonical_wheel_slot']
    return {'body_parts':body_parts,'complete_parts':complete_parts,'wheel_parts_by_slot':wheel_parts_by_slot,
            'wheel_parts':wheel_parts_by_slot[canonical],'textures':output_textures,'report':report}
