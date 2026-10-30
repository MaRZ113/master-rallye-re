"""Evidence-bound part ownership and explicit losses at the UVS/native boundary.

These are optional, external authoring contracts: original UVS values are never
rewritten to fit native capabilities. Unknown source effects are not successes.
"""
from __future__ import annotations
from . import universal_vehicle_scene as u

SCHEMA='universal-vehicle-semantics/1'
ROLES={'opaque_body','glass','frame','lamp_off','lamp_on','reflective_paint',
       'mirror_body','mirror_inset','tyre','rim','wheel_interior','equipment',
       'damage_eligible','cabin_crew'}
OVERLAYS={'reflective_paint','damage_eligible'}


def text(value,label):
    if not isinstance(value,str)or not value.strip()or len(value)>8192:
        raise ValueError(label+' evidence required')


def features(scene,selected_meshes=None):
    """Inventory unsupported native inputs even in old scenes with raw UV1 only."""
    rows=[];selected=set(selected_meshes)if selected_meshes is not None else {m['id']for m in scene['meshes']}
    used_materials=set()
    for mesh in scene['meshes']:
        if mesh['id']not in selected:continue
        used_materials.add(mesh['material_id'])
        channels=set(mesh.get('uv_channels',{}))
        if '10'in mesh['source'].get('streams',{}):channels.add('1')
        for channel in sorted(channels):
            rows.append({'id':'mesh:'+mesh['id']+':uv'+channel,'scope':mesh['id'],'kind':'secondary_uv',
                         'native_support':'UNSUPPORTED','source_preserved':True})
    for mat in scene['materials']:
        if mat['id']not in used_materials:continue
        stages={}
        for raw in mat['raw_fields']:
            if isinstance(raw,dict):
                bindings=raw.get('texture_bindings',[])
                if isinstance(bindings,list):
                    for slot,binding in enumerate(bindings[1:],1):
                        if binding is not None:stages[slot]=True
                fourth=raw.get('native_four_texture_resource_ids',[])
                if isinstance(fourth,list)and len(fourth)>3 and fourth[3]is not None:stages[3]=True
        for stage in sorted(stages):
            rows.append({'id':'material:'+mat['id']+':stage'+str(stage),'scope':mat['id'],'kind':'secondary_texture',
                         'native_support':'UNSUPPORTED','source_preserved':True})
        if mat.get('bump_texture_id'):
            rows.append({'id':'material:'+mat['id']+':bump','scope':mat['id'],'kind':'bump',
                         'native_support':'UNSUPPORTED','source_preserved':True})
    return rows


def feature_policy(scene,policy,selected_meshes=None,*,require_bump=False):
    """No implicit loss of secondary UV/stages. Omission remains an explicit WARN."""
    rows=features(scene,selected_meshes);known={r['id']for r in rows}
    if not isinstance(policy,dict)or set(policy)-known:raise ValueError('unknown source feature approval')
    result=[]
    for row in rows:
        approval=policy.get(row['id'])
        if approval is None:
            if row['kind']=='bump'and not require_bump:
                result.append({**row,'disposition':'legacy_diffuse_only','status':'WARN'});continue
            raise ValueError('unapproved native feature loss: '+row['id'])
        if not isinstance(approval,dict)or set(approval)!={'disposition','evidence','impact'}:
            raise ValueError('source feature disposition/evidence/impact required')
        text(approval['evidence'],'source feature');text(approval['impact'],'source fidelity impact')
        if approval['disposition']=='alias_uv0':
            mesh=next((m for m in scene['meshes']if m['id']==row['scope']),None)
            channel=row['id'].rsplit(':uv',1)[-1]
            values=mesh.get('uv_channels',{}).get(channel,{}).get('values')if mesh else None
            streams=mesh['source'].get('streams',{})if mesh else {}
            same_raw=channel=='1'and all(k in streams for k in ('9','10'))and streams['9']['sha256']==streams['10']['sha256']and streams['9']['stride']==streams['10']['stride']==8
            if row['kind']!='secondary_uv'or not(values==mesh['uvs']if values is not None else same_raw):
                raise ValueError('secondary UV alias is not identical to UV0')
            result.append({**row,**approval,'status':'PASS'});continue
        if approval['disposition']!='omit_for_mr':raise ValueError('unsupported source feature must block or explicitly omit for MR')
        result.append({**row,**approval,'status':'WARN'})
    return result


def validate(scene,document,scene_sha256):
    if not isinstance(document,dict)or set(document)!={'schema','source_scene_sha256','claims'}or document['schema']!=SCHEMA:
        raise ValueError('unsupported vehicle semantics contract')
    if document['source_scene_sha256']!=scene_sha256:raise ValueError('semantic source scene hash mismatch')
    claims=document['claims'];meshes={m['id']:m for m in scene['meshes']}
    if not isinstance(claims,list)or len(claims)>8192:raise ValueError('semantic claim budget')
    ownership={};role_faces={};total=0
    for claim in claims:
        if not isinstance(claim,dict)or set(claim)!={'mesh_id','material_id','triangles','role','interpretation','evidence'}:
            raise ValueError('exact semantic ownership fields required')
        if any(not isinstance(claim[k],str)for k in ('mesh_id','material_id','role','interpretation')):
            raise ValueError('semantic identity and role must be text')
        mesh=meshes.get(claim['mesh_id']);role=claim['role']
        if mesh is None or claim['material_id']!=mesh['material_id']:raise ValueError('semantic mesh/material ownership mismatch')
        if role not in ROLES or claim['interpretation']not in ('source_qualified','mr_authoring'):
            raise ValueError('unsupported semantic role/interpretation')
        text(claim['evidence'],'part role')
        ids=claim['triangles'];count=len(mesh['triangles'])
        if ids=='all':ids=range(count)
        elif not isinstance(ids,list)or not ids:raise ValueError('explicit semantic triangles required')
        total+=len(ids)
        if total>u.MAX_TRIANGLES*2:raise ValueError('semantic triangle allocation budget')
        if any(type(i)is not int or not 0<=i<count for i in ids)or len(set(ids))!=len(ids):
            raise ValueError('semantic triangle index/duplicate')
        key=(mesh['id'],role)
        if key in role_faces and role_faces[key].intersection(ids):raise ValueError('duplicate semantic claim')
        role_faces.setdefault(key,set()).update(ids)
        if role not in OVERLAYS:
            used=ownership.setdefault(mesh['id'],set())
            if used.intersection(ids):raise ValueError('conflicting opaque/glass/lamp/frame ownership')
            used.update(ids)
    # Reflection authoring must cover each complete original material group.
    reflected={meshes[mid]['material_id']for mid,role in role_faces if role=='reflective_paint'}
    for material in reflected:
        for mesh in scene['meshes']:
            if mesh['material_id']==material and len(role_faces.get((mesh['id'],'reflective_paint'),set()))!=len(mesh['triangles']):
                raise ValueError('fragmented reflection material ownership')
    return {'schema':SCHEMA,'source_scene_sha256':scene_sha256,'claims':len(claims),
            'roles':{role:sum(len(ids)for (mid,r),ids in role_faces.items()if r==role)for role in sorted(ROLES)},
            'unclassified_triangles':sum(len(m['triangles'])-len(ownership.get(m['id'],set()))for m in scene['meshes']),
            'source_mutated':False}


def native_roles(scene,profile,document):
    """An evidenced transparent/reflection rule cannot contradict part ownership."""
    claims=document['claims']
    for material,rule in profile['materials'].items():
        selected=[m for m in scene['meshes']if m['material_id']==material]
        if rule['mode']=='alpha_blend':
            for mesh in selected:
                allowed=set()
                for claim in claims:
                    if claim['mesh_id']==mesh['id']and claim['role']in('glass','lamp_on','mirror_inset'):
                        allowed.update(range(len(mesh['triangles']))if claim['triangles']=='all'else claim['triangles'])
                if len(allowed)!=len(mesh['triangles']):raise ValueError('alpha blend includes unqualified body/frame triangles')
        if rule.get('environment_reference')is not None:
            for mesh in selected:
                if not any(c['mesh_id']==mesh['id']and c['role']=='reflective_paint'and(c['triangles']=='all'or len(c['triangles'])==len(mesh['triangles']))for c in claims):
                    raise ValueError('native reflection lacks complete material ownership')


def partition(compiled,scene,document):
    """Partition existing compiled geometry by claims, without invented rendering.

    Returns ordinary SceneParts and exact source-face bindings for existing MR
    glass/lamp/damage services. Overlays annotate ownership, never add duplicate
    reflection/deformation polygons. Unclassified faces remain visible/unknown.
    """
    from dataclasses import replace
    from .glass_authoring import subset
    validate(scene,document,compiled['report']['source_scene_sha256'])
    assignments={}
    for claim_index,claim in enumerate(document['claims']):
        if claim['role']in OVERLAYS:continue
        mesh=next(m for m in scene['meshes']if m['id']==claim['mesh_id'])
        ids=range(len(mesh['triangles']))if claim['triangles']=='all'else claim['triangles']
        for index in ids:assignments[(mesh['id'],index)]=(claim_index,claim['role'])
    records=compiled['report']['complete_draws'];parts=compiled['complete_parts']
    if len(records)!=len(parts):raise ValueError('semantic partition draw mismatch')
    output=[];bindings=[]
    for record,part in zip(records,parts):
        ids=record['source_triangle_ids']
        if len(ids)!=len(part.geometry.triangles):raise ValueError('semantic partition triangle mismatch')
        groups={}
        for local,source in enumerate(ids):groups.setdefault(assignments.get((record['mesh_id'],source),(-1,'unknown')),[]).append(local)
        for (claim_index,role),local_ids in groups.items():
            if len(output)>=8192:raise ValueError('semantic partition draw budget')
            output.append(replace(part,geometry=subset(part.geometry,local_ids)))
            bindings.append({'part':len(output)-1,'node_id':record['node_id'],'mesh_id':record['mesh_id'],
                'material_id':record['material_id'],'role':role,'claim_index':claim_index,'source_triangle_ids':[ids[i]for i in local_ids],
                'interpretation':'ownership only; material/controller authoring remains explicit'})
    if sum(len(p.geometry.triangles)for p in output)!=sum(len(p.geometry.triangles)for p in parts):
        raise ValueError('semantic partition lost or duplicated triangles')
    return output,bindings
