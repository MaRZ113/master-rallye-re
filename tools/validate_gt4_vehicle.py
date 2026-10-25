"""Offline reconstruction, deterministic build and private-asset regression audit."""
from __future__ import annotations
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.gt4_assembly import assemble,component
from master_rallye.addon_sdk.gt4_source import modelset,shape_geometry
from master_rallye.addon_sdk.gt4_textures import model_texture_sets
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.scene_dx_writer import write_scene_dx,validate_scene_dx
from build_gt4_vehicle import build_model
from master_rallye.addon_sdk.native_brakes import validate_brake_scene
from prepare_sdk_capacity_probe import verified_base
from master_rallye.addon_sdk.texture_budget import texture_working_set,require_vehicle_budget
from master_rallye.addon_sdk.wheel_orientation import orient_parts


def qualify_embedded_rim(menu,independent):
    """CAR4's explicit rim component owns body assembly; standalone rims may differ.

    Qualify both original structures instead of assuming byte identity across
    separately authored model banks. No substituted wheel or geometry repair.
    """
    embedded,evidence=component(menu,0x20)
    banks={}
    for name,raw in [('embedded',embedded),('independent',independent)]:
        m=modelset(raw);geometries=[shape_geometry(s) for s in m['shapes']]
        for texture_set in model_texture_sets(raw,m['base']):
            for i in range(len(texture_set.registers)):texture_set.texture(i)
        if not geometries or not any(g['triangles'] for g in geometries):raise ValueError('empty qualified rim bank')
        banks[name]={'sha256':hashlib.sha256(raw).hexdigest(),'models':len(m['models']),
                     'shapes':len(geometries),'all_stored_triangles':sum(len(g['triangles']) for g in geometries)}
    return {'byte_equal':embedded==independent,'banks':banks,'component':evidence,
            'assembly_authority':'original CAR4 component pointer at 0x20; independent wheel/menu bank inventoried, never substituted'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--crew-source',type=Path);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--frozen-base',type=Path);a=p.parse_args()
    profile=json.loads(a.profile.read_text());code=profile['model_code'];sources={};inventory={}
    for path in (f'car/menu/{code}',f'car/lod/{code}',f'wheel/menu/{code}',f'wheel/lod/{code}'):
        raw=(a.source_root/path).read_bytes();sources[path]=hashlib.sha256(raw).hexdigest();m=modelset(raw);geoms=[shape_geometry(s) for s in m['shapes']];textures=model_texture_sets(raw,m['base'])
        for t in textures:
            for i in range(len(t.registers)):t.texture(i)
        inventory[path]={'sha256':sources[path],'models':len(m['models']),'shapes':len(geoms),'all_stored_triangles':sum(len(g['triangles']) for g in geoms),
            'textures_per_lod':[len(t.registers) for t in textures],
            'normal_encodings':sorted({v['normal_encoding'] or 'absent' for g in geoms for v in g['vertices']}),
            'scope':'all stored models/LODs, never one merged scene'}
    menu=(a.source_root/f'car/menu/{code}').read_bytes();race=(a.source_root/f'car/lod/{code}').read_bytes();spec=a.source_root/'specdb'/profile['spec_folder']
    rim_evidence=qualify_embedded_rim(menu,(a.source_root/f'wheel/menu/{code}').read_bytes())
    front=assemble(menu,menu,spec,profile);car=assemble(race,menu,spec,profile,race=True);checks={}
    env=(a.donor/profile['mr_environment_reference']).read_bytes() if profile.get('mr_environment_reference') else None
    with tempfile.TemporaryDirectory(prefix='gt4-validation-',dir=a.output.parent) as tmp:
        texture_root=Path(tmp)
        for name,draws in [('complete.dx',front['draws']),('car.dx',[d for d in car['draws'] if d.get('component') not in ('rim','tyre')]),('wheel.dx',front['wheel_template'])]:
            template=(a.donor/name).read_bytes()
            policy=profile.get('material_policy',{}).get('race' if name=='car.dx' else 'menu',{}) if name!='wheel.dx' else None
            rebuilt,records,brakes=build_model(name,draws,template,texture_root,environment=env,policy=policy,brake_source=race,profile=profile,
                stock_glow=(a.donor/'breaklightsonglow-tga.dxt').read_bytes() if profile.get('native_brakes') else None,crew_root=a.crew_source or a.donor)
            actual=(a.candidate/'assets'/name).read_bytes()
            if rebuilt!=actual:raise ValueError('nondeterministic scene: '+name)
            validation=(validate_brake_scene if brakes else validate_scene_dx)(template,actual);m=parse_dx_bytes(actual)
            for d in m.physical_draws:
                for s in d.texture_tuple:
                    if s!='Null':parse_dxt_bytes((a.candidate/'assets'/(s+'.dxt')).read_bytes())
            checks[name]={**validation,'sha256':hashlib.sha256(actual).hexdigest(),'deterministic':True,'missing_texture_references':0,
                'mr_environment_parts':sum(bool(r.get('environment')) for r in records),
                'unsupported':[{k:v for k,v in r.items() if k in ('packet','shape','route','issues','reason')} for r in records if r['route'].startswith(('retained','unsupported'))],
                'frozen_morph_parts':sum(bool(r.get('pose_fallback')) for r in records)}
        for p in texture_root.glob('*.dxt'):
            if p.read_bytes()!=(a.candidate/'assets'/p.name).read_bytes():raise ValueError('nondeterministic texture: '+p.name)
    budget=require_vehicle_budget(texture_working_set(a.candidate/'assets'))
    report={'status':'PASS_OFFLINE_WITH_DOCUMENTED_TRANSLATION_LIMITATIONS','source_inventory':inventory,'checks':checks,'texture_budget':budget,
        'same_source_menu_rim':rim_evidence['byte_equal'],'rim_source_qualification':rim_evidence,'source_rig':front['report']['rig'],
        'human_runtime_confirmed':False,'subaru_regression':'not requested','source_files_unchanged':True}
    for path,h in sources.items():
        if hashlib.sha256((a.source_root/path).read_bytes()).hexdigest()!=h:raise ValueError('source modified')
    if a.frozen_base:
        verified_base(a.frozen_base,(ROOT.parent/'MRallye.exe').read_bytes());report['subaru_regression']='frozen manifest, resource set, immutable asset hashes and native patch reconstruction PASS; user saves excluded'
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'resources':list(checks),'subaru_regression':report['subaru_regression']},indent=2))

if __name__=='__main__':main()
