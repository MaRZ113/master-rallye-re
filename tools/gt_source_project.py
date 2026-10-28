"""Create/reopen original-colorway projects without mutating source imports."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.gt_source_project import GTSourceProject
from generate_vehicle_ui_previews import render_sources

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    create=sub.add_parser('create')
    for name in ('source','donor','colour-database','colour-strings','identity','output'):create.add_argument('--'+name,type=Path,required=True)
    inputs=create.add_mutually_exclusive_group(required=True);inputs.add_argument('--profile',type=Path);inputs.add_argument('--inventory',type=Path)
    create.add_argument('--region',choices=['us','eu','jp'],default='us');create.add_argument('--car-key');create.add_argument('--mode',choices=['full','standard'],default='full')
    choose=sub.add_parser('select');choose.add_argument('--project',type=Path,required=True);choose.add_argument('--colour',type=int,required=True)
    for verb in ('undo','redo','restore','inspect'):
        q=sub.add_parser(verb);q.add_argument('--project',type=Path,required=True)
    a=p.parse_args()
    if a.action=='create':
        identity=json.loads(a.identity.read_text())['addon']
        if a.inventory:
            if not a.car_key:p.error('--inventory requires an exact catalog --car-key')
            s=GTSourceProject.create_auto(a.source,a.donor,a.inventory,a.region,a.car_key,a.colour_database,a.colour_strings,identity,a.output,render_ui=render_sources,mode=a.mode)
        else:s=GTSourceProject.create(a.source,a.donor,json.loads(a.profile.read_text()),a.colour_database,a.colour_strings,identity,a.output,render_ui=render_sources)
    else:
        s=GTSourceProject(a.project)
        if a.action=='select':s.choose(a.colour,render_ui=render_sources)
        elif a.action in ('undo','redo'):s.step(a.action=='redo')
        elif a.action=='restore':s.restore()
    print(json.dumps({'selected':s.data['selected'],'colour':s.data['colourways'][s.data['selected']]['latin_name'],'workshop':str(s.current().root),'boundary':s.data['boundary']},indent=2))

if __name__=='__main__':main()
