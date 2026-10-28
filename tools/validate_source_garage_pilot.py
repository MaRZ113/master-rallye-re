"""Owner-local SDK/Studio smoke; creates a fresh disposable authoring copy.

No game executable is launched and no source/accepted project is modified.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.universal_vehicle_scene import sha,canonical,unlinked,output_directory,load_scene
from master_rallye.workshop.service import WorkshopProject


def validate(source,output):
    source=Path(source).absolute();output=Path(output).absolute();unlinked(output)
    if output.exists()or output.is_relative_to(source):raise ValueError('Fresh validation output outside input required')
    original=WorkshopProject(source);original.verify_inputs()
    scene=load_scene(Path(original.data['universal_source']['scene_path']))
    settings=original.data['build_settings']
    output_directory(output,[source,Path(original.data['source']),original.baseline,
        scene['source']['root'],*scene['source'].get('protected_roots',[]),
        Path(settings['retail_root']),Path(settings['retail_sma']).parent])
    immutable={str(p):(sha(p.read_bytes()),p.stat().st_mtime_ns)for folder in (original.baseline,Path(original.data['source']))for p in folder.rglob('*')if p.is_file()}
    project=WorkshopProject.create(Path(original.data['source']),output/'workshop',kind='addon',car_id=29)
    project.data['universal_source']=copy.deepcopy(original.data['universal_source'])
    project.data['source_baseline']=copy.deepcopy(original.data['source_baseline']);project.save()
    project.configure_build(copy.deepcopy(original.data['build_settings']))
    project.register_crew_models({name:copy.deepcopy(value['definition'])for name,value in original.data['crew'].items()})
    def resources():return {p.name:sha(p.read_bytes())for p in project.assets.iterdir()if p.is_file()}
    initial=resources();project.shadow_update('auto')
    body_before=(project.assets/'car.dx').read_bytes()
    project.edit_surface('car.dx',0,rgb=[.8,1.,1.])
    tinted=(project.assets/'car.dx').read_bytes();assert tinted!=body_before
    fitted_before=project.native_model_resources()['car.dx'];project.shadow_calculate();project.frontend_auto_frame()
    project.undo();assert(project.assets/'car.dx').read_bytes()==body_before
    project.redo();assert(project.assets/'car.dx').read_bytes()==tinted
    placement={'lateral':.02,'vertical':0.,'longitudinal':0.,'yaw_degrees':0.}
    crew=project.fit_crew('car.dx','driver',placement)
    moved=(project.assets/'car.dx').read_bytes();assert moved!=tinted
    project.native_model_resources();project.shadow_calculate();project.frontend_auto_frame()
    project.undo();assert(project.assets/'car.dx').read_bytes()==tinted
    project.redo();assert(project.assets/'car.dx').read_bytes()==moved
    project.marker_update('#204080');project.results_name_update('TOYOTA 4RUNNER TEST')
    project.camera_mode_update(2,{'FOV':75.})
    project.camera_mode_update(2,{})
    project.shadow_reset('original');project.shadow_update('auto')
    project.save();reopened=WorkshopProject(project.root)
    assert reopened.data['crew']['car.dx']['placements']['driver']==placement
    assert reopened.vehicle_state()['details']['display_name']=='TOYOTA 4RUNNER TEST'
    assert reopened.vehicle_state()['race_marker'][:3]==[32/255,64/255,128/255]
    reopened.verify_inputs();reopened.validate()
    project=reopened;project.restore();assert resources()==initial
    project.undo();assert(project.assets/'car.dx').read_bytes()==moved
    project.redo();assert resources()==initial
    project.verify_inputs()
    for name,expected in immutable.items():
        p=Path(name);assert(sha(p.read_bytes()),p.stat().st_mtime_ns)==expected
    result={'status':'PASS_OWNER_LOCAL_STUDIO_SMOKE','project':str(project.root),'checks':[
        'surface edit + exact Undo/Redo','crew rigid edit + exact Undo/Redo','collision-fit source rebase',
        'Shadow AutoFit + Original reset','frontend AutoFrame after overlays','Results and marker persistence',
        'GameplayCamera2 override reset','reopen and validation','Restore exact baseline resources + Undo/Redo',
        'original author/baseline hashes and mtimes unchanged'],
        'crew_reports':crew,'source_original_file_count':len(immutable),'gameplay':'NOT TESTED'}
    (output/'validation.json').write_bytes(canonical(result));return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workshop',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(validate(args.workshop,args.output),indent=2))


if __name__=='__main__':main()
