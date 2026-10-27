"""Physics/Camera/Presentation CLI over the same Workshop Core as Windows UI."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path);sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('physics');p.add_argument('--reference')
    p=sub.add_parser('set-physics');p.add_argument('member',choices=['DataGame/vehicles.xml','DataGame/Modifications.xml']);p.add_argument('field');p.add_argument('value',type=json.loads,help='Typed scalar, bool, vector or quoted string')
    p=sub.add_parser('copy-reference');p.add_argument('family');p.add_argument('group')
    sub.add_parser('camera');p=sub.add_parser('set-camera');p.add_argument('half_length',type=float);p.add_argument('height',type=float);p.add_argument('--car-id',type=int)
    for command in ('game-camera','set-camera-mode','export-game-camera'):
        p=sub.add_parser(command);p.add_argument('--mode',type=int,choices=range(5),default=0);p.add_argument('--split',action='store_true')
        if command=='set-camera-mode':p.add_argument('fields',type=json.loads,help='Qualified JSON fields; {} resets selected mode')
        if command=='export-game-camera':p.add_argument('--view',choices=['original','donor','modified'],default='modified')
    p=sub.add_parser('details')
    for k in ('manufacturer','model','combined','display-name','description'):p.add_argument('--'+k)
    p=sub.add_parser('alias');p.add_argument('texture');p.add_argument('label')
    p=sub.add_parser('search-textures');p.add_argument('query',nargs='?',default='')
    p=sub.add_parser('generate-art');p.add_argument('--model',choices=['car.dx','complete.dx'],default='complete.dx');p.add_argument('--role',choices=['vehicle_select_art','smallcarsheet']);p.add_argument('--azimuth',type=float);p.add_argument('--elevation',type=float);p.add_argument('--padding',type=int,default=12)
    p=sub.add_parser('apply-art');p.add_argument('report',type=Path,help='Explicitly accept a reviewed project-owned generation.json')
    p=sub.add_parser('restore');p.add_argument('--section',choices=['physics','camera','details','aliases','art'])
    sub.add_parser('validate');sub.add_parser('undo');sub.add_parser('redo')
    p=sub.add_parser('build');p.add_argument('output',type=Path)
    a=parser.parse_args();project=WorkshopProject(a.project);result=None
    if a.action=='physics':result=project.physics_inspect(a.reference)
    elif a.action=='set-physics':project.physics_update(a.member,a.field,a.value)
    elif a.action=='copy-reference':result=project.physics_copy_reference(a.family,a.group)
    elif a.action=='camera':result=project.camera_inspect()
    elif a.action=='set-camera':project.camera_update(a.half_length,a.height,a.car_id)
    elif a.action=='game-camera':result=project.camera_lab_inspect(mode=a.mode,split=a.split)
    elif a.action=='set-camera-mode':project.camera_mode_update(a.mode,a.fields);result=project.camera_lab_inspect(mode=a.mode,split=a.split)
    elif a.action=='export-game-camera':result=project.camera_lab_export(mode=a.mode,split=a.split,view=a.view)
    elif a.action=='details':
        fields=project.vehicle_state()['details'];updates={k:getattr(a,k) for k in fields if getattr(a,k) is not None}
        if updates:fields.update(updates);project.details_update(fields)
        result=fields
    elif a.action=='alias':project.alias_update(a.texture,a.label)
    elif a.action=='search-textures':result=project.texture_search(a.query)
    elif a.action=='generate-art':result=project.art_generate(model=a.model,role=a.role,azimuth=a.azimuth,elevation=a.elevation,padding=a.padding)
    elif a.action=='apply-art':project.art_apply(json.loads(a.report.read_text(encoding='utf-8')))
    elif a.action=='restore':project.vehicle_reset(a.section)
    elif a.action in ('undo','redo','validate'):result=getattr(project,a.action)()
    elif a.action=='build':result=project.build(a.output,sdk_root=ROOT,log=lambda s:print(s,file=sys.stderr))
    print(json.dumps(result or {'status':'SAVED','project':str(project.root)},indent=2,default=str))
if __name__=='__main__':main()
