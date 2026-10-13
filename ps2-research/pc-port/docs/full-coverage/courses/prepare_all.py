"""Exact-source full-course vegetation registry; original assets stay ignored.

Delegates PackFS, PSM spatial decoding, float32 placement and artifact layout.
Only source triangles matching validated PC compiled geometry at .001 are used.
The larger bounded artifact budget does not thin or alter any source sample.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import time

PORT = Path(__file__).resolve().parents[3]
RESEARCH = PORT.parent
sys.path[:0] = [str(RESEARCH/'tools'), str(PORT/'tools')]
import detail_runtime as detail
import geometry_delta as geometry
import tngtool
import water_runtime as water
import course_delta
import prepare_grass_pilot as grass

def pair_for_source(source,pairs):
    resource=source['resource'].replace('\\','/').split('/')
    identity=course_delta.normalize('course/'+resource[-2]+'/'+Path(resource[-1]).stem)
    candidates=[r for r in pairs if r['landscape']==identity]
    if len(candidates)!=1:raise ValueError('Missing/ambiguous original course pair')
    return candidates[0]

def prove_alignment(ps2,pc,sdk,pair,entries):
    xml,_=course_delta.sdk_modules(sdk)
    a_bytes,_=tngtool.read_payload(entries[tngtool.logical_path(pair['ps2'])],ps2/'TNG.000')
    b_bytes=(pc/pair['pc']).read_bytes()
    a,_=course_delta.parse_scene(a_bytes,pair['ps2'],xml)
    b,_=course_delta.parse_scene(b_bytes,pair['pc'],xml)
    residual=course_delta.route_alignment(a['_route_points'],b['_route_points'])
    if pair['confidence'] not in ('STRONG','EXACT') or residual is None or residual['within_one_world_unit']<.95:
        raise ValueError('Original route/identity correspondence insufficient')
    if a['landscape']!=pair['landscape'] or b['landscape']!=pair['pc_landscape']:
        raise ValueError('Original landscape ownership changed')
    matrices=[]
    for raw in (a_bytes,b_bytes):
        document=xml.parse_course_xml_bytes(raw)
        eggs=[e for e in document.eggs if e.list_name=='landscape' and e.model_name]
        if len(eggs)!=1 or eggs[0].matrix() is None:raise ValueError('Missing landscape transform')
        matrix=eggs[0].matrix().rows
        geometry.require_identity_transform(matrix);matrices.append(matrix)
    return {'transform':'IDENTITY_IN_SOURCE_FRAME; NO_FIT','independent_anchor':'ORDERED_RACELINE',
            'route_residual':residual,'authored_landscape_matrices':matrices,
            'ps2_route_sha256':hashlib.sha256(a_bytes).hexdigest(),'pc_route_sha256':hashlib.sha256(b_bytes).hexdigest(),
            'runtime_transform':'UNKNOWN','evidence_grade':'CONFIRMED_BY_BYTES'}

def exact_matches(source, target, epsilon=.001):
    grid=defaultdict(list)
    for points in target:
        if water.area_normal(points)[0] > geometry.AREA_EPSILON:
            grid[water._cell(water.centroid(points),100*epsilon)].append(points)
    result=[]
    for triangle,points in source:
        if water.area_normal(points)[0] <= geometry.AREA_EPSILON:continue
        hits=[water.corner_error(points, candidate)
              for key in water._neighbors(water._cell(water.centroid(points),100*epsilon))
              for candidate in grid.get(key,())]
        if hits and min(hits)<=epsilon:result.append(triangle)
    return result

def publish(data,filename):
    root=PORT/'.assets/grass'
    for part in (root.parent,root):
        if part.is_symlink() or getattr(part,'is_junction',lambda:False)():raise ValueError('Linked private root')
    destination=root/filename
    if destination.exists():
        if destination.is_symlink() or destination.stat().st_nlink!=1 or destination.read_bytes()!=data:
            raise ValueError('Refusing to replace different/linked artifact '+filename)
        return 'EXISTING_BYTES_REPRODUCED'
    root.mkdir(exist_ok=True)
    with destination.open('xb') as f:f.write(data)
    return 'PRIVATE_IGNORED_ASSET_CREATED'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ps2',type=Path,required=True);p.add_argument('--pc',type=Path,required=True)
    p.add_argument('--sdk',type=Path,required=True);p.add_argument('--publish',action='store_true')
    p.add_argument('--course',action='append');p.add_argument('--budget',type=int,default=300000)
    args=p.parse_args()
    if not 250000<=args.budget<=1000000:raise ValueError('Unsupported explicit artifact budget')
    grass.MAX_POINTS=args.budget
    water.verify_inputs(args.ps2)
    manifest,_=tngtool.load_pak(args.ps2/'TNG.PAK')
    entries={tngtool.logical_path(e['path']):e for e in manifest['entries'] if e['kind']=='file'}
    inventory=json.loads((PORT/'docs/grass-port3/course-inventory.json').read_text())
    pairs=json.loads((RESEARCH/'cdelta1/course-pairs.json').read_text())
    course_delta.sdk_modules(args.sdk)
    from master_rallye.dx_course import parse_course_dx
    jitter,_=detail.jitter_table()
    textures={}
    for category in ('grass','shrubs'):
        entry=next(x for x in inventory['textures'] if x['category']==category)
        data,_=tngtool.read_payload(entries[tngtool.logical_path(entry['resource'])],args.ps2/'TNG.000')
        if hashlib.sha256(data).hexdigest()!=entry['sha256'] or len(data)!=4104:raise ValueError('Texture mismatch')
        textures[category]=(entry,data)
    out=Path(__file__).parent
    rows=[]
    if args.course:
        old=out/'coverage-registry.json'
        if old.exists():rows=[row for row in json.loads(old.read_text())['courses'] if row['course'] not in args.course]
    for source in inventory['courses']:
        if args.course and source['course'] not in args.course:continue
        start=time.monotonic();course=source['course']
        row={'course':course,'psm_resource':source['resource'],'psm_sha256':source['psm_sha256'],
             'categories':{},'evidence_grade':'CONFIRMED_BY_BYTES','runtime_validation':'NOT_PERFORMED'}
        try:
            pair=pair_for_source(source,pairs)
            stem=Path(pair['pc']).stem
            folder=args.pc/'DataGx'/Path(pair['pc_landscape'].replace('\\','/')).parent
            # PC spelling differs for special stages; use source-owned folder identity.
            available=[x for x in (args.pc/'DataGx'/'Course').iterdir()
                       if course_delta.normalize(x.name)==pair['pc_landscape'].split('\\')[1]]
            if len(available)!=1:raise ValueError('Missing/ambiguous PC course directory')
            dxs=sorted(available[0].glob('*.dx'));txts=sorted(available[0].glob('*.txt'))
            if len(dxs)!=1 or len(txts)!=1:raise ValueError('Missing/ambiguous compiled DX/TXT')
            target=parse_course_dx(dxs[0])
            if not target.course_render_validated:raise ValueError('PC compiled geometry not complete-disjoint validated')
            alignment=prove_alignment(args.ps2,args.pc,args.sdk,pair,entries)
            row.update(native_certificate_id='RaceTest/'+stem,asset_stem=stem,
                       pc_scene=pair['pc'],pc_scene_sha256=tngtool.file_hash(args.pc/pair['pc']),
                       pc_dx_path=str(dxs[0].relative_to(args.pc)),pc_dx_sha256=tngtool.file_hash(dxs[0]),
                       pc_txt_sha256=tngtool.file_hash(txts[0]),alignment=alignment,
                       pc_triangles=target.triangle_count,pc_draws=len(target.physical_draws))
            data,_=tngtool.read_payload(entries[tngtool.logical_path(source['resource'])],args.ps2/'TNG.000')
            if hashlib.sha256(data).hexdigest()!=source['psm_sha256']:raise ValueError('Frozen PSM hash mismatch')
            model=detail.decode_landscape(data)
            faces=[]
            for draw in target.physical_draws:
                ids=target.draw_global_indices(draw)
                faces.extend(tuple(target.vertices.positions[j] for j in ids[i:i+3]) for i in range(0,len(ids),3))
            for category in ('grass','shrubs'):
                chosen=[(i,model.surface(i)) for i,m in sorted(model.bindings.items())
                        if detail.directive_contract(model.materials[m])['detail_category']==category
                        and detail.eligibility(model.surface(i),category)['eligible']]
                matched=exact_matches(chosen,faces)
                points=[];digest=hashlib.sha256();max_hash=0.
                for triangle in matched:
                    polygon=list(reversed(model.surface(triangle)))
                    generated=detail.scan_polygon(polygon,detail.plane_coefficients(polygon),category,jitter,'nearest_even')
                    for sample in generated:
                        x,z=sample['grid_x'],sample['grid_z']
                        h=detail.add(detail.add(detail.mul(x,detail.f32(21.123102)),detail.mul(z,detail.f32(-34.923172))),detail.mul(detail.mul(x,-z),detail.f32(184.12938)))
                        if not -2**31<=h<2**31:raise ValueError('Unrecovered R5900 hash CVT.W.S overflow')
                        max_hash=max(max_hash,abs(h));point=tuple(sample['position'])
                        digest.update(struct.pack('<3f',*point));points.append(point)
                item={'eligible_triangles':len(chosen),'strict_matched_triangles':len(matched),
                      'excluded_nonexact_triangles':len(chosen)-len(matched),'point_count':len(points),
                      'generated_xyz_sha256':digest.hexdigest(),'maximum_abs_hash':max_hash}
                row['categories'][category]=item
                if not points: item['status']='NO_VERIFIED_PLACEMENT';continue
                if len(points)>args.budget:item['status']='POINT_BUDGET_EXCEEDED_NO_THINNING';continue
                texture,gxi=textures[category]
                artifact=grass.serialize_artifact(points,gxi[8:],source['psm_sha256'],texture['sha256'],row['pc_dx_sha256'])
                item.update(artifact=grass.validate_artifact(artifact),filename=stem+('Grass' if category=='grass' else 'Shrubs')+'.ps2grass',
                            status='VERIFIED_PRIVATE_ASSET',gxi_sha256=texture['sha256'])
                if args.publish:print(item['filename'],publish(artifact,item['filename']),flush=True)
                print(course,category,len(chosen),len(matched),len(points),flush=True)
            row['status']='VERIFIED_PAIR'
        except (ValueError,tngtool.FormatError,StopIteration) as error:
            row.update(status='BLOCKED',blocker=str(error));print(course,'BLOCKED',str(error),flush=True)
        print(course,'elapsed_seconds',round(time.monotonic()-start,3),flush=True)
        rows.append(row)
        (out/(course.lower()+'-placement.json')).write_text(json.dumps(row,indent=2,allow_nan=False)+'\n',encoding='utf8')
        summary={'schema_version':1,'courses':sorted(rows,key=lambda r:r['course']),'matching_tolerance':.001,'artifact_point_budget':args.budget,
                 'coordinate_frame':'GAME_SOURCE','placement_precision':'FLOAT32_RECONSTRUCTION',
                 'generation':'FULL_SOURCE_TRIANGLE_ACTIVATION_NOT_ORIGINAL_RUNTIME_HISTORY',
                 'runtime_validation':'NOT_PERFORMED'}
        (out/'coverage-registry.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf8')

if __name__=='__main__':main()
