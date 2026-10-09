"""RIGID1 read-only authored, shape and explicit-state physics diagnostics.

No contact simulator, asset writer or PC implementation. Numeric inputs are
synthetic/captured state, never a claim about a live PS2 body. PackFS, PSM and
collision parsing are delegated to the established tools/read-only Course SDK.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

import spline_runtime as s
import tngtool as t
import water_runtime as w
import geometry_delta as g
import course_delta as c

ROOT, Error = s.ROOT, s.ContractError
f32, add, sub, mul, div = s.f32, s.add, s.sub, s.mul, s.div
SCHEMA = 'ps2-rigid-contract-v1'
HAY = (r'\TNG\DATAPSM\MISC\HAYBALE\HAYBALE.PSM',
       r'\TNG\DATAPSM\MISC\OBJECTS\HAYBALES\HAYBALE.PSM')
TUMBLE = r'\TNG\DATAPSM\MISC\OBJECTS\TUMBLEWEED\TUMBLWEED.PSM'
DT_HALF = mul(struct.unpack('<f', bytes.fromhex('8988083d'))[0], .5)
GRAVITY = struct.unpack('<f', bytes.fromhex('c3f51c41'))[0]


def local_output(path):
    path = Path(path).resolve()
    if not path.is_relative_to((ROOT/'data/rigid1').resolve()) or path == ROOT/'data/rigid1':
        raise Error('Diagnostics must stay under ignored data/rigid1')
    if path.exists(): raise Error('Existing output preserved; select a new filename')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def vector(values, count=3):
    try: result = tuple(f32(float(v)) for v in values)
    except (TypeError, ValueError) as exc: raise Error('Finite numeric vector required') from exc
    if len(result) != count: raise Error('Incorrect vector length')
    return result


def resolve_properties(rows):
    """19fe98: first correctly typed property, original constructor defaults.

    Raw unknown/duplicate properties survive the inventory. Unusual finite
    Mass/MOI values are retained; only numerical evaluation rejects division
    by zero. This diagnostic does not fix the original game configuration.
    """
    def scalar(name, default):
        try: return f32(float(s.value(rows, name, 'Float', str(default))))
        except (TypeError, ValueError) as exc: raise Error('Invalid '+name) from exc
    shadow = s.value(rows, 'Casts Shadow', 'Bool', 'False')
    if shadow not in ('True', 'False'): raise Error('Unsupported lexical Bool')
    return dict(mass=scalar('Mass', 500), moi=s.vector(s.value(rows, 'MOI', 'Vector3', '100 100 100')),
                trigger_distance=scalar('Trigger Distance', 5), casts_shadow=shadow == 'True')


def parse_authored(payload, source):
    if not 0 < len(payload) <= 16*1024*1024 or any(x in payload.upper() for x in (b'<!DOCTYPE', b'<!ENTITY')):
        raise Error('Unsupported XML size/declarations')
    try: tree = ET.fromstring(payload)
    except ET.ParseError as exc: raise Error('Malformed scene XML') from exc
    if tree.tag != 'Scene' or tree.find('EggLists_Version4') is None:
        raise Error('Expected Scene/EggLists_Version4')
    records = []
    for li, group in enumerate(tree.findall('EggLists_Version4/List')):
        for ei, egg in enumerate(group.findall('Egg')):
            for ai_index, ai in enumerate(egg.findall('AI_List/AI')):
                if s.value(s.properties(ai), 'AI Name', 'String') != 'gaAiRigidBody': continue
                config = ai.find('gaAiRigidBody')
                if config is None: raise Error('Missing gaAiRigidBody configuration')
                props, params = s.properties(egg), s.properties(config)
                model = s.value(props, 'en3d Model Name', 'String')
                if model is None: raise Error('Missing en3d model name')
                matrices = [x for x in props if x.get('Name') == 'en3d Matrix' and x.get('Type') == 'Matrix']
                if not matrices: raise Error('Missing authored en3d Matrix')
                matrix = [vector(matrices[0].get('Row%d'%i, '').split(), 4) for i in range(4)]
                normalized = model.replace('/', '\\').lower()
                family = 'haybale' if normalized in ('misc\\haybale\\haybale', 'misc\\objects\\haybales\\haybale') else (
                         'tumbleweed' if normalized == 'misc\\objects\\tumbleweed\\tumblweed' else 'UNKNOWN')
                records.append(dict(source_id='%s:list:%d:egg:%d:ai:%d'%(source,li,ei,ai_index),
                    list_name=group.get('Name'), list_index=li, egg_index=ei, ai_index=ai_index,
                    egg=egg.get('Name'), model=model, family=family, parameters=params,
                    resolved=resolve_properties(params), matrix=matrix,
                    matrix_sha256=t.sha(struct.pack('<16f',*(v for row in matrix for v in row))),
                    evidence_grade='CONFIRMED_BY_BYTES', live_instance='UNKNOWN'))
    return dict(source=source, decoded_sha256=t.sha(payload), records=records)


def compact_authored(case):
    result = {k:v for k,v in case.items() if k != 'records'}
    result['records'] = [{k:v for k,v in row.items() if k != 'matrix'} for row in case['records']]
    result['counts'] = dict(authored_eggs=len(case['records']),
        distinct_matrix_hashes=len({r['matrix_sha256'] for r in case['records']}),
        families=dict(sorted(Counter(r['family'] for r in case['records']).items())))
    return result


def corpus_inventory(directory):
    corpus = s.Corpus(directory)
    pairs = json.loads((ROOT/'cdelta1/course-pairs.json').read_text())
    courses = []
    for pair in pairs:
        matches = [e for e in corpus.manifest['entries'] if e['path'] == pair['ps2']]
        if len(matches) != 1: raise Error('Missing/ambiguous paired resource')
        payload, report = t.read_payload(matches[0], corpus.directory/'TNG.000')
        case = compact_authored(parse_authored(payload, pair['ps2']))
        case.update(course=Path(pair['ps2'].replace('\\','/')).stem, pc_source=pair['pc'], packfs=report)
        courses.append(case)
    return dict(schema=SCHEMA, canonical_inputs=corpus.provenance, courses=courses,
        totals=dict(course_pairs=len(courses), rigid_courses=sum(bool(c['records']) for c in courses),
                    authored_eggs=sum(c['counts']['authored_eggs'] for c in courses),
                    families=dict(sorted(Counter(r['family'] for c0 in courses for r in c0['records']).items()))),
        evidence_grade='CONFIRMED_BY_BYTES', runtime_validation='NOT_PERFORMED')


def shape_summary(hull):
    def geometry(block):
        return dict(offset=block.offset,end_offset=block.end_offset,vertices=block.vertex_count,
                    triangles=block.triangle_count,bounds=g.bounds(block.vertices),
                    xyz_f32_sha256=t.sha(b''.join(struct.pack('<3f',*p) for p in block.vertices)),
                    index_u32_sha256=t.sha(b''.join(struct.pack('<3I',*p) for p in block.triangles)))
    def representation(rep):
        return dict(offset=rep.offset,end_offset=rep.end_offset,geometry_a=geometry(rep.geometry_a),
                    geometry_b=geometry(rep.geometry_b),referenced_vertices=len(rep.referenced_vertex_indices),
                    edges=len(rep.edges),faces=rep.face_count)
    return dict(tag=101,offset=hull.tag_offset,end_offset=hull.end_offset,sha256=hull.sha256,
                base_geometry=geometry(hull.base_geometry),base_scalar=hull.base_scalar,
                representation_a=representation(hull.representation_a),representation_b=representation(hull.representation_b))


def inspect_model(payload, source, sdk):
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        c.sdk_modules(Path(sdk))
        from master_rallye.collision import parse_collision_sections
        scene = w.decode_scene(payload, terminator=101)
        collision = parse_collision_sections(payload[scene.end:], base_offset=scene.end, source=source, strict=True)
    finally: sys.dont_write_bytecode = old
    if collision.convex_hull is None or collision.errors or collision.tag_ids != (101,):
        raise Error('Selected prop requires one proved tag101 convex hull')
    if payload[collision.end_offset:] != b'\xff\xff\xff\xff':
        raise Error('Unsupported prop trailer; refuse guessed extra records')
    return dict(source=source,size=len(payload),sha256=t.sha(payload),visual=dict(
        vertex_records=scene.vertex_count,start=scene.start,end=scene.end,node_counts=scene.node_counts,
        mesh_records=len(scene.meshes),materials=[m['material'] for m in scene.meshes],
        texture_references=[m['textures'] for m in scene.meshes],
        bounds=g.bounds(scene.position(i) for i in range(scene.vertex_count)),
        strips=sum(len(m['strips']) for m in scene.meshes),
        nonsuppressed_nondegenerate_triangles=sum(len(w.mesh_triangles(scene,m)[0]) for m in scene.meshes)),
        collision=shape_summary(collision.convex_hull),evidence_grade='CONFIRMED_BY_BOTH',
        live_shape_selection='UNKNOWN; static shape/body registration proved, frame not captured')


def shapes(directory, sdk):
    corpus = s.Corpus(directory)
    rows=[]
    for path in (*HAY,TUMBLE):
        entries=[e for e in corpus.manifest['entries'] if e['path']==path]
        if len(entries)!=1: raise Error('Missing/ambiguous prop resource')
        payload, report=t.read_payload(entries[0],corpus.directory/'TNG.000')
        row=inspect_model(payload,path,sdk);row['packfs']=report;rows.append(row)
    return dict(schema=SCHEMA,models=rows,canonical_inputs=corpus.provenance)


def near_gate(position, views):
    """1a0258: at most first two registry entries; explicit 200550 results."""
    p = vector(position)
    diagnostics=[]
    for i, view in enumerate(views[:2]):
        if type(view.get('predicate_200550')) is not bool: raise Error('Explicit view predicate Bool required')
        d=tuple(sub(a,b) for a,b in zip(vector(view['position']),p))
        distance2=s.dot(d,d)
        near=distance2<=f32(10000.) and view['predicate_200550']
        diagnostics.append(dict(entry=i,distance_squared=distance2,eligible=near))
        if near: return dict(near=True,selected=i,checks=diagnostics,authored_trigger_used=False)
    return dict(near=False,selected=None,checks=diagnostics,authored_trigger_used=False)


@dataclass(frozen=True)
class Activation:
    paused: bool = True       # body+0
    acknowledged: bool = False  # owner+2c
    settled: bool = True      # owner+34
    far_decay: bool = False   # owner+38
    timer: int = 0            # owner+30, invocation count


def activation_step(state, near):
    if type(near) is not bool or any(type(getattr(state,k)) is not bool for k in
            ('paused','acknowledged','settled','far_decay')) or type(state.timer) is not int or not 0<=state.timer<=60:
        raise Error('Unsupported explicit activation state')
    p,a,z,d,n=state.paused,state.acknowledged,state.settled,state.far_decay,state.timer
    branch='RETAIN'
    if near:
        if d: p,a,z,d,n=False,True,False,False,0;branch='RESUME_FAR_BODY'
        elif p and a: a,z,d,n=False,True,False,0;branch='ACKNOWLEDGE_PHYSICS_SLEEP'
        elif not p and not a: a,z,d,n=True,False,False,0;branch='ACKNOWLEDGE_CONTACT_WAKE'
    elif not p: p,a,z,d,n=True,False,False,True,60;branch='PAUSE_AND_DECAY'
    elif not d: a,z,d,n=False,True,False,0;branch='RETAIN_SETTLED'
    decay='NONE'
    if d and n:
        decay='ZERO_MOMENTA_AND_VELOCITIES' if n==1 else 'MULTIPLY_BY_FLOAT32_ONE_OVER_60_THEN_RECOMPUTE_MOMENTA'
        n-=1
    return dict(state=asdict(Activation(p,a,z,d,n)),branch=branch,decay=decay,
                decay_factor=DT_HALF if decay!='NONE' else None,precision='FLOAT32_RECONSTRUCTION')


def body_parameters(mass, moi):
    mass=f32(mass);moi=vector(moi)
    if mass<=0 or any(v<=0 for v in moi):
        raise Error('Diagnostic inversion requires positive mass/inertia; source inventory retains unusual values')
    return dict(mass=mass,inverse_mass=div(1.,mass),body_inertia_diagonal=moi,
                inverse_body_inertia_diagonal=tuple(div(1.,v) for v in moi),
                precision='MATHEMATICALLY_EQUIVALENT; inverse diagonal only, not bit-exact 203358 matrix inversion')


def derivative(quaternion, velocity, omega, force, torque, extra_force=(0,0,0),extra_torque=(0,0,0)):
    """266e20 derivative order: position, wxyz quaternion, P, L."""
    qw,qx,qy,qz=vector(quaternion,4);ox,oy,oz=vector(omega)
    qdot=(mul(sub(sub(sub(mul(qw,0.),mul(ox,qx)),mul(oy,qy)),mul(oz,qz)),.5),
          mul(sub(add(add(mul(qx,0.),mul(ox,qw)),mul(oy,qz)),mul(oz,qy)),.5),
          mul(sub(add(add(mul(qy,0.),mul(oy,qw)),mul(oz,qx)),mul(ox,qz)),.5),
          mul(sub(add(add(mul(qz,0.),mul(oz,qw)),mul(ox,qy)),mul(oy,qx)),.5))
    return tuple(vector(velocity))+qdot+tuple(add(a,b) for a,b in zip(vector(force),vector(extra_force)))+tuple(
        add(a,b) for a,b in zip(vector(torque),vector(extra_torque)))


def linear_step(position, momentum, mass, dt, extra_force=(0,0,0), paused=False):
    """Isolated linear RK4 portion of 269968 mode1 + 27d060 gravity.

    Constant explicit force, no contacts/rotation/sleep/activation; not a complete
    prop simulation. Weighted stages follow the original repeated-add contract.
    """
    mass=f32(mass);dt=f32(dt)
    if mass<=0 or dt<0 or type(paused) is not bool: raise Error('Unsupported linear diagnostic input')
    x,p=vector(position),vector(momentum)
    if paused:return dict(position=x,momentum=p,paused=True)
    force=list(vector(extra_force));force[1]=add(mul(-GRAVITY,mass),force[1]);force=tuple(force)
    state=x+p
    def rhs(v):return tuple(div(u,mass) for u in v[3:])+force
    def shifted(v,k,half):
        return tuple(add(a,mul(mul(b,.5) if half else b,dt)) for a,b in zip(v,k))
    k1=rhs(state);k2=rhs(shifted(state,k1,True));k3=rhs(shifted(state,k2,True));k4=rhs(shifted(state,k3,False))
    result=[]
    for i in range(6):
        total=add(add(add(add(add(k1[i],k2[i]),k2[i]),k3[i]),k3[i]),k4[i])
        result.append(add(state[i],div(mul(dt,total),6.)))
    return dict(position=result[:3],momentum=result[3:],force=force,dt=dt,paused=False,
                precision='FLOAT32_RECONSTRUCTION', scope='ISOLATED_CONSTANT_FORCE_LINEAR_RK4; NO_CONTACTS')


def visual_pose(position, rotation_rows, local_com, right, up, forward):
    """267f60: explicit body basis and COM -> row-major en3d matrix.

    Basis inputs are actual body ec/e0/f8 vectors, not invented unit globals.
    Rotation_rows are body bc..dc; source coordinates are never converted here.
    """
    if len(rotation_rows)!=3: raise Error('Three rotation rows required')
    rows=[vector(row) for row in rotation_rows];p,com=vector(position),vector(local_com)
    translation=tuple(sub(p[i],s.dot(rows[i],com)) for i in range(3))
    return [list(vector(axis)) + [0.] for axis in (right,up,forward)]+[list(translation)+[1.]]


def quaternion_rotation(quaternion):
    """2661e0 + 205580, wxyz input and row-major body rotation.

    The startup initializer 21cec0 writes identity quaternion and XYZ basis.
    sqrt/div use finite host IEEE32, not an exact PS2 FPU implementation.
    """
    q=vector(quaternion,4)
    length=f32(math.sqrt(add(add(add(mul(q[0],q[0]),mul(q[1],q[1])),mul(q[2],q[2])),mul(q[3],q[3]))))
    q=(1.,0.,0.,0.) if length<f32(.001) else tuple(mul(v,div(1.,length)) for v in q)
    qw,qx,qy,qz=q;y2=add(qy,qy);z2=add(qz,qz);xx=mul(add(qx,qx),qx);xw=mul(add(qx,qx),qw)
    rows=((sub(1.,add(mul(y2,qy),mul(z2,qz))),sub(mul(y2,qx),mul(z2,qw)),add(mul(z2,qx),mul(y2,qw))),
          (add(mul(y2,qx),mul(z2,qw)),sub(1.,add(xx,mul(z2,qz))),sub(mul(z2,qy),xw)),
          (sub(mul(z2,qx),mul(y2,qw)),add(mul(z2,qy),xw),sub(1.,add(xx,mul(y2,qy)))))
    return q,rows


def quaternion_pose(position, quaternion, local_com):
    q,rows=quaternion_rotation(quaternion)
    basis=[tuple(s.dot(row,axis) for row in rows) for axis in ((1,0,0),(0,1,0),(0,0,1))]
    return dict(normalized_quaternion=q,body_rotation_rows=rows,
                en3d_matrix=visual_pose(position,rows,local_com,*basis),precision='FLOAT32_RECONSTRUCTION')


def pc_counterparts(pcroot, sdk, ps2root):
    """Bounded source scan + independently decoded standalone/cooked hay evidence.

    TXT names are leads. Texture-selected compiled draws are not object counts.
    No source TXT span is promoted to a DX face ID or safely removable instance.
    """
    pcroot=Path(pcroot);corpus=s.Corpus(ps2root)
    old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
    try:
        c.sdk_modules(Path(sdk))
        from master_rallye.dx import parse_dx
        from master_rallye.dx_course import parse_course_dx
        from master_rallye.course_source import parse_course_txt
        path=pcroot/'DataGx/Misc/Haybale/haybaletest.dx';model=parse_dx(path)
        if model.collision.convex_hull is None:raise Error('PC standalone has no validated hull')
        pcshape=shape_summary(model.collision.convex_hull)
        entries=[e for e in corpus.manifest['entries'] if e['path']==HAY[0]]
        if len(entries)!=1:raise Error('Missing canonical hay model')
        payload,_=t.read_payload(entries[0],corpus.directory/'TNG.000')
        from master_rallye.collision import parse_collision_sections
        scene=w.decode_scene(payload,terminator=101)
        ps2shape=parse_collision_sections(payload[scene.end:],base_offset=scene.end,strict=True).convex_hull
        agreement={}
        for label in ('representation_a','representation_b'):
            a=getattr(ps2shape,label).geometry_a;b=getattr(model.collision.convex_hull,label).geometry_a
            agreement[label]=dict(positions=g.vertex_agreement(a.vertices,b.vertices,.0001),
                                 identical_triangle_indices=a.triangles==b.triangles,
                                 tolerance=.0001,coordinate_system='MODEL_LOCAL_IDENTITY')
        sources=[]
        for folder in ('Italy_S1','Italy2'):
            dx=pcroot/'DataGx/Course'/folder/(folder+'.dx');txt=dx.with_suffix('.txt')
            course=parse_course_dx(dx);doc=parse_course_txt(txt)
            if not course.course_render_validated:raise Error('PC complete draw coverage not validated')
            leads=[n for n in doc.nodes if 'haybal' in n.name.lower()]
            draws=[d for d in course.physical_draws if any('hay' in n.lower() for n in d.texture_tuple)]
            sources.append(dict(course=folder,dx_sha256=t.file_hash(dx),txt_sha256=t.file_hash(txt),
                compiled_draws=len(course.physical_draws),vertices=course.vertex_count,triangles=course.triangle_count,
                hay_name_leads=len(leads),lead_classes=dict(sorted(Counter(n.class_name for n in leads).items())),
                texture_candidate_draws=[dict(draw_index=d.draw_index,textures=list(d.texture_tuple),
                    triangles=len(course.draw_global_indices(d))//3,
                    bounds=g.bounds(course.vertices.positions[i] for i in course.draw_global_indices(d))) for d in draws],
                lead_samples=[dict(node_id=n.node_id,name=n.name,parent_id=n.parent_id,
                                   source_index=n.mesh_index,source_size=n.mesh_size) for n in leads[:8]],
                instance_correspondence='UNKNOWN; TXT spans are not compiled DX face indices',
                risk='COURSE_INSTANCE_MAPPING_REQUIRED; no whole-draw deletion approved'))
    finally:sys.dont_write_bytecode=old
    files=sorted(p for p in pcroot.rglob('*') if p.is_file())
    names=[p.relative_to(pcroot).as_posix() for p in files]
    xmls=[p for p in files if p.suffix.lower()=='.xml']
    textfiles=[p for p in files if p.suffix.lower() in ('.xml','.txt')]
    hits={term:[] for term in ('tumbleweed','tumblweed','gaairigidbody','haybale')}
    for path in textfiles:
        data=path.read_bytes().lower()
        for term in hits:
            if term.encode() in data:hits[term].append(path.relative_to(pcroot).as_posix())
    return dict(schema=SCHEMA,pc_root=str(pcroot),scan=dict(files=len(files),xml_files=len(xmls),
        xml_txt_files=len(textfiles),ordered_filename_sha256=t.sha('\n'.join(names).encode()),
        name_tumble_hits=[n for n in names if 'tumble' in n.lower() or 'tumbl' in n.lower()],
        text_hits=hits,absence_grade='NOT_FOUND_IN_SCANNED_PC_CORPUS'),
        hay_standalone=dict(path='DataGx/Misc/Haybale/haybaletest.dx',
            sha256=t.file_hash(pcroot/'DataGx/Misc/Haybale/haybaletest.dx'),vertices=len(model.vertices.positions),
            triangles=len(model.local_indices)//3,collision=pcshape,ps2_collision_agreement=agreement),
        baked_hay_candidates=sources,live_behavior='UNKNOWN; static model existence is not runtime physics')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['inventory','shapes','pc','contract','evaluate'])
    parser.add_argument('--ps2',type=Path);parser.add_argument('--sdk',type=Path);parser.add_argument('--pc',type=Path)
    parser.add_argument('--input',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.mode in ('inventory','shapes','pc') and args.ps2 is None:parser.error('--ps2 required')
    if args.mode in ('shapes','pc') and args.sdk is None:parser.error('--sdk required')
    if args.mode=='inventory':result=corpus_inventory(args.ps2)
    elif args.mode=='shapes':result=shapes(args.ps2,args.sdk)
    elif args.mode=='pc':
        if args.pc is None:parser.error('--pc required')
        result=pc_counterparts(args.pc,args.sdk,args.ps2)
    elif args.mode=='contract':result=json.loads((ROOT/'rigid1/rigid-physics-contract.json').read_text())
    else:
        if args.input is None:parser.error('evaluate requires explicit --input JSON')
        data=json.loads(args.input.read_text())
        if data.get('input_provenance') not in ('SYNTHETIC','CAPTURED_EXPLICIT_INPUT'):
            raise Error('Explicit synthetic/captured input provenance required')
        result=dict(schema=SCHEMA,input_provenance=data['input_provenance'],runtime_validation='NOT_PERFORMED')
        if 'gate' in data:result['gate']=near_gate(**data['gate'])
        if 'activation' in data:result['activation']=activation_step(Activation(**data['activation']['state']),data['activation']['near'])
        if 'linear' in data:result['linear']=linear_step(**data['linear'])
        if 'derivative' in data:result['derivative']=derivative(**data['derivative'])
        if 'pose' in data:result['pose']=visual_pose(**data['pose'])
        if 'quaternion_pose' in data:result['quaternion_pose']=quaternion_pose(**data['quaternion_pose'])
        if len(result)==3:raise Error('No supported diagnostic operation supplied')
    text=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if args.output:local_output(args.output).write_text(text,encoding='utf-8',newline='\n')
    else:print(text,end='')


if __name__=='__main__':main()
