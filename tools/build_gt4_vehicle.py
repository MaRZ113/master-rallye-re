"""Build private MR inspection resources from a user-supplied qualified GT4 profile.

No GT assets are bundled, no source files modified, no runtime/CarID changes.
The packet writer is shared with other scene sources; all source selection is
explicit profile data. Unsupported source effects remain in the build report.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct,sys,zlib
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.addon_sdk.gt4_assembly import assemble
from master_rallye.addon_sdk.gt4_materials import alpha_compare
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.addon_sdk.texture_addressing import guarded_clamp
from master_rallye.addon_sdk.gt4_mr_materials import environment_pairs,qualified_environment_pairs
from master_rallye.addon_sdk.texture_budget import texture_working_set,require_vehicle_budget
from master_rallye.addon_sdk.wheel_orientation import orient_parts,instance_angle
from master_rallye.addon_sdk.gt4_brakes import source_states,source_key,native_surfaces
from master_rallye.addon_sdk.native_brakes import write_brake_scene
from master_rallye.addon_sdk.gt4_paint import prepare_paint
from master_rallye.addon_sdk.gt4_layered import opaque_layered_surfaces
from master_rallye.addon_sdk.crew import fit_crew
from master_rallye.addon_sdk.visibility_keepout import apply_keepouts,append_source_housings

from master_rallye.source_scene_compile import compile_draws,rotate


def build_model(name,draws,template,assets,*,environment=None,policy=None,brake_source=None,profile=None,stock_glow=None,crew_root=None):
    brakes=None
    if name!='wheel.dx' and profile:
        variant='race' if name=='car.dx' else 'menu';geometry=profile.get('geometry_policy',{}).get(variant,{})
        if set(geometry)-{'visibility_keepouts','source_housings'}:raise ValueError('unsupported geometry policy')
        if geometry.get('visibility_keepouts'):
            draws,_=apply_keepouts(draws,geometry['visibility_keepouts'],profile['body_race_sha256' if variant=='race' else 'body_menu_sha256'])
        if geometry.get('source_housings'):
            draws,_=append_source_housings(draws,geometry['source_housings'],profile['body_race_sha256' if variant=='race' else 'body_menu_sha256'])
    crew,crew_records=fit_crew(crew_root,profile['crew'],'race' if name=='car.dx' else 'menu',assets) if name!='wheel.dx' and profile and profile.get('crew') and crew_root else ([],[])
    if name!='wheel.dx' and profile and profile.get('crew') and crew_root is None:raise ValueError('crew source root is required')
    if name=='car.dx' and profile and profile.get('native_brakes'):
        off,on,provenance=source_states(brake_source,profile);keys={source_key(d) for d in off}
        body=[d for d in draws if source_key(d) not in keys or d.get('component','body')!='body']
        parts,record=compile_draws(body,assets,environment_reference=environment,material_policy=policy)
        unlit,off_records=compile_draws(off,assets,environment_reference=environment,material_policy={k:v for k,v in (policy or {}).items() if not k.startswith('paint_') and k!='layered_opaque_surfaces'})
        source_on,on_records=compile_draws(on,assets)
        # Preserve opaque/cutout source cores and generate the halo only from
        # the actual blended source lens, never its shared off-state atlas.
        opaque_on=[replace(p,diffuse=False) for p in source_on if not p.alpha or p.alpha_test]
        alpha_on=[p for p in source_on if p.alpha and not p.alpha_test]
        lit,glow,lamps=native_surfaces(alpha_on,assets,stock_glow,
            alpha_ref=profile['native_brakes'].get('alpha_ref',32),offset=profile['native_brakes'].get('halo_offset',.001),halo_max_edge=profile['native_brakes'].get('halo_max_edge'))
        data=write_brake_scene(template,parts+crew,unlit,opaque_on+lit,glow)
        brakes={**provenance,**lamps,'off_conversion':off_records,'on_conversion':on_records}
    else:
        parts,record=compile_draws(draws,assets,environment_reference=environment,material_policy=policy)
        if name=='wheel.dx':parts=orient_parts(parts,source_outward_x=1)
        data=write_scene_dx(template,parts+crew)
    return data,record+crew_records,brakes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--crew-source',type=Path,help='optional independent user-supplied stock crew family');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('output exists')
    profile=json.loads(a.profile.read_text());code=profile['model_code'];menu=(a.source_root/'car/menu'/code).read_bytes();race=(a.source_root/'car/lod'/code).read_bytes();spec=a.source_root/'specdb'/profile['spec_folder']
    frontend=assemble(menu,menu,spec,profile);racing=assemble(race,menu,spec,profile,race=True)
    a.output.mkdir(parents=True);assets=a.output/'assets';assets.mkdir();report={'status':'OFFLINE_GT4_MR_CANDIDATE_NOT_RUNTIME_QUALIFIED','profile':profile,'source_reports':{'menu':frontend['report'],'race':racing['report']},'outputs':{},'conversion':{}}
    # MR assembles race wheels independently. Baking the presentation wheels
    # into car.dx would produce a duplicate set once the game attaches wheel.dx.
    race_body=[d for d in racing['draws'] if d.get('component') not in ('rim','tyre')]
    environment=None
    if reference:=profile.get('mr_environment_reference'):
        if Path(reference).name!=reference:raise ValueError('environment reference must be a local donor DXT basename')
        environment=(a.donor/reference).read_bytes();parse_dxt_bytes(environment)
        report['environment_reference']={'file':reference,'sha256':hashlib.sha256(environment).hexdigest(),'policy':'explicit MR helper approximation; only proven GS pairs admitted'}
    for name,scene,draws in [('complete.dx',frontend,frontend['draws']),('car.dx',racing,race_body),('wheel.dx',frontend,frontend['wheel_template'])]:
        policy=profile.get('material_policy',{}).get('race' if name=='car.dx' else 'menu',{}) if name!='wheel.dx' else None
        template=(a.donor/name).read_bytes()
        data,record,brakes=build_model(name,draws,template,assets,environment=environment,policy=policy,brake_source=race,profile=profile,
            stock_glow=(a.donor/'breaklightsonglow-tga.dxt').read_bytes() if profile.get('native_brakes') else None,crew_root=a.crew_source or a.donor)
        if brakes:report['native_brakes']=brakes
        (assets/name).write_bytes(data);model=parse_dx_bytes(data)
        report['outputs'][name]={'sha256':hashlib.sha256(data).hexdigest(),'vertices':model.vertex_count,'triangles':model.triangle_count,'draws':len(model.physical_draws),'validated':model.diagnostics.validated,'template_sha256':hashlib.sha256(template).hexdigest()}
        report['conversion'][name]=record
    report['texture_budget']=require_vehicle_budget(texture_working_set(assets))
    (a.output/'texture-budget.json').write_text(json.dumps(report['texture_budget'],indent=2)+'\n')
    instances=[{'translation':list(rotate(w['hub'])),'rotation_y':instance_angle(-w['side']),
                'scale':[1.,1.,1.]} for w in frontend['report']['rig']['wheels']]
    (a.output/'preview-profile.json').write_text(json.dumps({'race_wheel_instances':instances,
        'provenance':'GT4 original DBT/IDI and traced normal-four wheel constructor rest pose; no MR physics or runtime wheel positions changed'},indent=2)+'\n')
    (assets/'preview-profile.json').write_bytes((a.output/'preview-profile.json').read_bytes())
    report['wheel_orientation']={'source_template_outward_x':1,'mr_template_outward_x':-1,
        'conversion':'proper 180 degree Y rotation, determinant +1; normals follow positions; indices/UVs unchanged',
        'placements':'source and MR physics hubs unchanged; preview instance angles compensate the local basis only'}
    report['limitations']=['GT4 generated reflections/DATE use a source-qualified MR helper approximation, not PS2 renderer parity',
        'source dynamic camber/provider pose remains unresolved; source-supported static hub formula used',
        ('source tail-lamp branches use native blight; original controller CPU-qualified, gameplay confirmation pending' if profile.get('native_brakes') else 'source tail-lamp branches are decoded; selected source day branch retained'),
        'selected no-Z-write window decals use a depth-safe cutout; soft alpha edges quantized, underlying glass remains blended',
        'coverage and environment alpha share one MR channel; cutout reflective regions retain coverage after damage, with approximate reflection fading',
        'baseline donor collision retained explicitly; no physics tuning','no install/CarID allocation attempted; body materials require human MR testing','offline package is private loose research output; do not distribute GT assets']
    (a.output/'conversion-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['outputs'],indent=2))

if __name__=='__main__':main()
