"""Bridge an imported GT4 scene candidate into the existing Vehicle SDK.

Creates a fresh private donor authoring tree and editable addon project. Does
not install, allocate new engine capacity, launch the game, or copy GT assets
into the repository's tracked source directories.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.project import initialize_project
from master_rallye.addon_sdk.ui_assets import BANKS
from master_rallye.scene_dx_writer import validate_scene_dx
from generate_vehicle_ui_previews import render_sources


def prepare(candidate,donor,profile,output,*,ui_from=None):
    if output.exists():raise ValueError('output exists')
    identity=json.loads(profile.read_text())['addon']
    if donor.name!='Navara':raise ValueError('this bridge currently admits the existing verified Navara T2 physics baseline only')
    source=output/'source'/donor.name;source.mkdir(parents=True)
    # No original donor resource is changed. Imported textures must use distinct
    # names; conflicts are rejected instead of replacing an unrelated resource.
    for p in donor.iterdir():
        if p.is_file() and p.suffix.lower() in ('.dx','.dxt'):shutil.copyfile(p,source/p.name)
    for p in (candidate/'assets').glob('*.dxt'):
        target=source/p.name
        if target.exists() and target.read_bytes()!=p.read_bytes():raise ValueError('imported texture collides with donor: '+p.name)
        shutil.copyfile(p,target)
    initialize_project(name=identity['name'],vehicle_class='T2',donor='Navara',family=identity['family'],output=output/'project',donor_source=source)
    project=output/'project';spec=json.loads((project/'vehicle-project.json').read_text())
    for role in ('car.dx','complete.dx','wheel.dx'):
        before=(donor/role).read_bytes();after=(candidate/'assets'/role).read_bytes()
        native=role=='car.dx' and json.loads(profile.read_text()).get('native_brakes')
        if native:
            from master_rallye.addon_sdk.native_brakes import validate_brake_scene
            validate_brake_scene(before,after)
        else:validate_scene_dx(before,after)
        spec['resources'][role]={'source_sha256':hashlib.sha256(before).hexdigest(),
            'native_brake_scene_candidate' if native else 'scene_candidate':str((candidate/'assets'/role).resolve())}
    (project/'vehicle-project.json').write_text(json.dumps(spec,indent=2)+'\n')
    manifest=json.loads((project/'addon.json').read_text());manifest['frontend'].update(manufacturer=identity['manufacturer'],model=identity['model'],combined=identity['name'].upper())
    manifest['description']='Private GT4 source reconstruction; existing T2/ID27 integration, unchanged donor physics, no new capacity qualification.'
    for role,(_,count,_,_) in BANKS.items():manifest['frontend'][role]={'policy':'project_frame','frame':count}
    (project/'addon.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if ui_from:
        ui=json.loads((ui_from/'ui-assets.json').read_text());(project/'ui').mkdir(exist_ok=True)
        for role in BANKS:
            item=ui['icons'][role];source_icon=ui_from/item['png']
            if not source_icon.resolve().is_relative_to(ui_from.resolve()) or hashlib.sha256(source_icon.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('UI reference changed or escapes project')
            target=project/item['png'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source_icon,target)
        shutil.copyfile(ui_from/'ui-assets.json',project/'ui-assets.json');render={'policy':'byte-identical user-selected qualified UI project','source':str(ui_from)}
        icons=ui['icons']
    else:render=render_sources(candidate/'assets',project/'ui');icons={}
    if not ui_from:
        for role in BANKS:
            path=project/'ui'/(role+'.png');icons[role]={'png':'ui/'+path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'presentation':'mr-native-v1'}
        (project/'ui-assets.json').write_text(json.dumps({'version':1,'icons':icons},indent=2)+'\n')
    (output/'bridge-report.json').write_text(json.dumps({'project':str(project.resolve()),'source_candidate':str(candidate.resolve()),
        'donor':str(donor.resolve()),'physics':'byte-identical Navara profile; wheel positions not tuned','ui_render':render,
        'integration':'existing ID26/T1 + ID27/T2 path; separate Lancer bundle, not simultaneous Subaru+Lancer/new-capacity qualification'},indent=2)+'\n')
    return project


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ui-from',type=Path);a=p.parse_args()
    print(prepare(a.candidate.resolve(),a.donor.resolve(),a.profile.resolve(),a.output.resolve(),ui_from=a.ui_from.resolve() if a.ui_from else None))
