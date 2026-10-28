"""Shared donor-based imported-scene authoring bridge; no runtime allocation.

UI rendering is supplied by the existing qualified source renderer. The GUI and
CLI reuse this service; no alternate mesh writer or UI atlas code is embedded.
"""
import hashlib,json,shutil
from .project import initialize_project
from .ui_assets import BANKS
from ..scene_dx_writer import validate_scene_dx

def prepare(candidate,donor,profile,output,*,ui_from=None,render_ui,source_format="GT4",vehicle_class="T2"):
    if output.exists():raise ValueError('output exists')
    identity=json.loads(profile.read_text())['addon']
    # Any retail family may donate physics/templates; Navara/T2 remains the
    # runtime-qualified baseline, other donors need owner gameplay checks.
    if vehicle_class not in ('T1','T2'):raise ValueError('vehicle class must be T1 or T2')
    source=output/'source'/donor.name;source.mkdir(parents=True)
    # No original donor resource is changed. Imported textures must use distinct
    # names; conflicts are rejected instead of replacing an unrelated resource.
    for p in donor.iterdir():
        if p.is_file() and p.suffix.lower() in ('.dx','.dxt'):shutil.copyfile(p,source/p.name)
    for p in (candidate/'assets').glob('*.dxt'):
        target=source/p.name
        if target.exists() and target.read_bytes()!=p.read_bytes():raise ValueError('imported texture collides with donor: '+p.name)
        shutil.copyfile(p,target)
    initialize_project(name=identity['name'],vehicle_class=vehicle_class,donor=donor.name,family=identity['family'],output=output/'project',donor_source=source)
    project=output/'project';spec=json.loads((project/'vehicle-project.json').read_text())
    for role in ('car.dx','complete.dx','wheel.dx'):
        before=(donor/role).read_bytes();after=(candidate/'assets'/role).read_bytes()
        native=role=='car.dx' and json.loads(profile.read_text()).get('native_brakes')
        from master_rallye.dx import parse_dx_bytes
        states=role=='car.dx' and not native and any(d.tag!=2 for d in parse_dx_bytes(after).physical_draws)
        if native:
            from master_rallye.addon_sdk.native_brakes import validate_brake_scene
            validate_brake_scene(before,after);key='native_brake_scene_candidate'
        elif states:
            from master_rallye.addon_sdk.native_states import validate_state_scene
            validate_state_scene(before,after);key='native_state_scene_candidate'
        else:validate_scene_dx(before,after);key='scene_candidate'
        spec['resources'][role]={'source_sha256':hashlib.sha256(before).hexdigest(),key:str((candidate/'assets'/role).resolve())}
    (project/'vehicle-project.json').write_text(json.dumps(spec,indent=2)+'\n')
    manifest=json.loads((project/'addon.json').read_text());manifest['frontend'].update(manufacturer=identity['manufacturer'],model=identity['model'],combined=identity['name'].upper())
    manifest['description']=('Private GT4 source reconstruction; existing T2/ID27 integration, unchanged donor physics, no new capacity qualification.' if source_format=='GT4' else 'Private '+source_format+' reconstruction; independent addon identity, donor-derived initial physics, no new capacity qualification.')
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
    else:render=render_ui(candidate/'assets',project/'ui');icons={}
    if not ui_from:
        for role in BANKS:
            path=project/'ui'/(role+'.png');icons[role]={'png':'ui/'+path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'presentation':'mr-native-v1'}
        (project/'ui-assets.json').write_text(json.dumps({'version':1,'icons':icons},indent=2)+'\n')
    (output/'bridge-report.json').write_text(json.dumps({'project':str(project.resolve()),'source_candidate':str(candidate.resolve()),
        'donor':str(donor.resolve()),'physics':'byte-identical '+donor.name+' donor profile; wheel positions not tuned','ui_render':render,
        'integration':('existing ID26/T1 + ID27/T2 path; separate Lancer bundle, not simultaneous Subaru+Lancer/new-capacity qualification' if source_format=='GT4' else 'Authoring project only; allocation and simultaneous roster require existing qualified roster builder'), 'source_format':source_format},indent=2)+'\n')
    return project

