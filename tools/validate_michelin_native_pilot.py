"""Reproducible owner-local native conservation checks, without launching MR."""
import argparse
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as uvs
from master_rallye.michelin_native_pilot import profile as pilot_profile,semantic_parts,enhance as _enhance,SCENES,FAMILY,PANES,LAMP_IDS,lamp_maps
SCENE_SHA256=SCENES["Car25A.PDO"]
from master_rallye.universal_scene_bridge import compile_scene
from master_rallye.scene_dx_writer import write_scene_dx
from master_rallye.addon_sdk.wheel_orientation import orient_parts
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.workshop.service import WorkshopProject


def inventory(root):
    return {p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':uvs.sha(p.read_bytes())}for p in sorted(root.rglob('*'))if p.is_file()}


def validate(pilot,donor,output):
    pilot=Path(pilot).absolute();donor=Path(donor).absolute();output=Path(output).absolute()
    uvs.unlinked(output)
    if output.exists()or output.is_relative_to(pilot)or pilot.is_relative_to(output):raise ValueError('Fresh validation output outside pilot required')
    scene_path=pilot/'inputs/source-scene/scene.json';scene=uvs.load_scene(scene_path)
    uvs.output_directory(output,[pilot,donor,Path(scene['source']['root']),*scene['source'].get('protected_roots',[])])
    before=inventory(pilot/'inputs/source-scene');profile=pilot_profile(scene_path)
    result=compile_scene(scene_path,profile);second=compile_scene(scene_path,profile)
    assert result==second
    assert uvs.sha(scene_path.read_bytes())==SCENE_SHA256
    output.mkdir();assets=output/'assets';assets.mkdir()
    deterministic={}
    for name,raw in result['textures'].items():
        assert raw==(pilot/'source-baseline/assets'/name).read_bytes();(assets/name).write_bytes(raw);deterministic[name]=uvs.sha(raw)
    for name,parts in [('car.dx',result['body_parts']),('complete.dx',result['complete_parts']),('wheel.dx',result['wheel_parts'])]:
        raw=write_scene_dx((donor/name).read_bytes(),parts)
        assert raw==(pilot/'source-baseline/assets'/name).read_bytes();(assets/name).write_bytes(raw);deterministic['baseline/'+name]=uvs.sha(raw)
    adaptations=_enhance(assets,result,donor,output)
    for name in ('car.dx','complete.dx','mr-michelin-rav4-cracks-tga.dxt','mr-michelin-rav4-stop-lit-tga.dxt','mr-michelin-rav4-stop-glow-tga.dxt'):
        raw=(assets/name).read_bytes();assert raw==(pilot/'converted/assets'/name).read_bytes();deterministic['adapted/'+name]=uvs.sha(raw)
    # Native resource rotation +X=pi / -X=0 must reconstruct the exact source
    # hub-local vertices, normals, UVs and triangle winding, not donor wheels.
    wheels={}
    for i,slot in enumerate(('front_left','front_right','rear_left','rear_right')):
        parts=result['wheel_parts_by_slot'][slot]
        expected=orient_parts(parts,source_outward_x=1,target_outward_x=-1)if slot.endswith('left')else parts
        raw=write_scene_dx((donor/'wheel.dx').read_bytes(),expected)
        assert raw==(pilot/'converted/assets'/('wheel-source'+str(i)+'.dx')).read_bytes()
        model=parse_dx_bytes(raw);geometries=source_geometry(model)
        max_error=0.;radius=0.
        for draw,source in zip(geometries.values(),parts):
            assert draw.triangles==source.geometry.triangles
            for actual,original in zip(draw.vertices,source.geometry.vertices):
                turn=lambda p:(-p[0],p[1],-p[2])if slot.endswith('left')else p
                position=turn(actual.position);normal=turn(actual.normal)
                max_error=max(max_error,*[abs(position[k]-original.position[k])for k in range(3)],*[abs(normal[k]-original.normal[k])for k in range(3)])
                assert all(abs(actual.uvs[0][k]-original.uvs[0][k])<1e-6 for k in range(2))
                radius=max(radius,math.hypot(position[1],position[2]))
        assert max_error<1e-6
        wheels[slot]={'resource_sha256':uvs.sha(raw),'max_rest_pose_vertex_normal_error':max_error,'geometry_radius':radius,'hub':result['report']['hubs'][slot]}
    textures={t['id']:t for t in scene['textures']};texture_checks={}
    for material in result['report']['materials'].values():
        tex=textures[material['source_texture_id']];rgba=(scene_path.parent/tex['rgba_path']).read_bytes()
        name=material['native_textures'][0]+'.dxt';native=parse_dxt_bytes(result['textures'][name])
        recovered=b''.join(bytes((b[2],b[1],b[0],b[3]))for b in (native.bgra[i:i+4]for i in range(0,len(native.bgra),4)))
        assert recovered==rgba
        texture_checks[tex['id']]={'rgba_sha256':uvs.sha(recovered),'dxt_sha256':uvs.sha(result['textures'][name]),'channels':'all original RGBA samples exact, stored rows preserved'}
    # Round-trip every source corner through the explicit inverse, including
    # determinant-aware winding, with no UV or damage-target substitution.
    source_meshes={m['id']:m for m in scene['meshes']};geometry_errors=[]
    for mapping,part in zip(result['report']['body_draws'],result['body_parts']):
        mesh=source_meshes[mapping['mesh_id']]
        for v,source_id in zip(part.geometry.vertices,mapping['source_vertex_ids']):
            restored=uvs.transform_point(mapping['mr_to_source'],v.position)
            geometry_errors.extend(abs(restored[k]-mesh['positions'][source_id][k])for k in range(3))
            assert list(v.uvs[0])==mesh['uvs'][source_id]
            assert v.color==bytes(mesh['preview_colors_bgra'][source_id])
    assert max(geometry_errors)<1e-6
    split,panes,lamp,core=semantic_parts(result)
    assert sum(len(p.geometry.triangles)for p in split)==652
    assert sum(len(ids)for ids in PANES.values())==34
    assert len({i for ids in PANES.values()for i in ids})==34
    for label,index in panes.items():
        assert split[index].alpha and not split[index].alpha_test
        assert all(v.color[3]==96 for v in split[index].geometry.vertices)
    original_rear=parse_dxt_bytes(result['textures'][split[lamp].textures[0]+'.dxt'])
    lit,glow,allowed=lamp_maps(original_rear);lit=parse_dxt_bytes(lit);glow=parse_dxt_bytes(glow)
    allowed=set(allowed)
    for i in range(original_rear.width*original_rear.height):
        if i not in allowed:
            assert lit.bgra[4*i:4*i+4]==original_rear.bgra[4*i:4*i+4]
            assert glow.bgra[4*i:4*i+4]==bytes(4)
    work=WorkshopProject(pilot/'workshop');work.verify_inputs();work.validate()
    native=work.native_model_resources()
    # The SDK collision adaptation changes only collision bytes/bounds; render
    # arrays and semantic controllers remain the qualified authored baseline.
    converted=parse_dx_bytes((pilot/'converted/assets/car.dx').read_bytes());built=parse_dx_bytes(native['car.dx'])
    assert converted.vertices==built.vertices and converted.uv_sets==built.uv_sets
    assert converted.physical_draws==built.physical_draws
    runtime=pilot/'builds/source-fidelity/candidate/runtime';base=json.loads((pilot/'roster/roster-config.json').read_text())
    original=inventory(Path(base['base_runtime'])/'resource-root');current=inventory(runtime/'resource-root')
    differences=[{'resource':name,'before':original.get(name),'after':current.get(name)}for name in sorted(original.keys()|current.keys())if original.get(name)!=current.get(name)]
    # No stock model namespace is replaced by this cross-game authoring.
    changed_original_models=[r['resource']for r in differences if r['before'] and r['resource'].lower().startswith('datagx/vehicles/')]
    assert not changed_original_models,changed_original_models
    assert len([r for r in base['projects']if r['physical_id']==29])==1
    assert base['wheel_profiles'][-1]['runtime_family']==FAMILY
    assert inventory(pilot/'inputs/source-scene')==before
    report={'schema':'michelin-native-conservation/1','status':'PASS_STATIC_OWNER_LOCAL','source_scene_sha256':SCENE_SHA256,
        'deterministic_resources':deterministic,'original_rgba_checks':texture_checks,'wheels':wheels,
        'source_scene_immutable':True,'native_render_arrays_unchanged_by_collision_fit':True,
        'native_state_preservation':adaptations['native_states'],'max_source_roundtrip_error':max(geometry_errors),'bounded_glass_triangles':34,'bounded_rear_lens_pixels':len(allowed),'exact_resource_differences':differences,
        'all_resource_root_files':len(current),'sealed_resources':len(current)-int('DataGame/PlayerState.xml'in current),'car_id':29,'roster_limit':30,
        'stock_model_replacements':changed_original_models,'gameplay':'NOT TESTED'}
    (output/'validation.json').write_bytes(uvs.canonical(report));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('pilot','donor','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();r=validate(args.pilot,args.donor,args.output)
    print(json.dumps({k:v for k,v in r.items()if k not in ('exact_resource_differences','wheels','original_rgba_checks','deterministic_resources')},indent=2))
