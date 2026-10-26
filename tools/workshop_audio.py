"""Audio Studio CLI using the same project authoring service as Windows GUI."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject
from master_rallye.workshop.audio import LAYERS

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',type=Path)
    sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('inspect');sub.add_parser('restore')
    q=sub.add_parser('import');q.add_argument('layer',choices=LAYERS);q.add_argument('wav',type=Path);q.add_argument('--gain-db',type=float,default=0);q.add_argument('--trim',type=int,nargs=2);q.add_argument('--crossfade',type=int,default=0)
    q=sub.add_parser('apply');q.add_argument('layer',choices=LAYERS);q.add_argument('json',type=Path,help='audio_update keyword arguments (source/response/enabled/stock_profile)')
    for action in ('save-preset','load-preset'):
        q=sub.add_parser(action);q.add_argument('name')
    q=sub.add_parser('import-preset');q.add_argument('donor',type=Path);q.add_argument('name')
    q=sub.add_parser('audition');q.add_argument('output',type=Path);q.add_argument('--exe',type=Path,default=ROOT.parent/'MRallye.exe');q.add_argument('--solo',choices=LAYERS);q.add_argument('--rpm',type=float,nargs='+',default=[900,2000,4000,6000,3000,900]);q.add_argument('--load',type=float,default=1.);q.add_argument('--gear',type=int,default=2);q.add_argument('--rev-limit',type=float,default=7000)
    a=p.parse_args();project=WorkshopProject(a.project);result=None
    if a.action=='inspect':result=project.audio_inspect()
    elif a.action=='restore':project.audio_reset()
    elif a.action=='import':result=project.audio_import(a.layer,a.wav,gain_db=a.gain_db,trim=a.trim,crossfade=a.crossfade)
    elif a.action=='apply':project.audio_update(a.layer,**json.loads(a.json.read_text()))
    elif a.action=='save-preset':project.audio_save_preset(a.name)
    elif a.action=='load-preset':project.audio_load_preset(a.name)
    elif a.action=='import-preset':project.audio_transfer(WorkshopProject(a.donor),a.name)
    elif a.action=='audition':result=project.audio_audition(a.exe,a.output,rpms=a.rpm,load=a.load,gear=a.gear,rev_limit=a.rev_limit,enabled={k:a.solo is None or k==a.solo for k in LAYERS})
    print(json.dumps(result or {'status':'SAVED','project':str(project.root)},indent=2))

if __name__=='__main__':main()
