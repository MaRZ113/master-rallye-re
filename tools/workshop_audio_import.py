"""Optional GT source selection and ordinary media import over shared SDK Core."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',type=Path);sub=p.add_subparsers(dest='action',required=True)
    q=sub.add_parser('prepare');q.add_argument('audio',type=Path);q.add_argument('--trim',type=int,nargs=2);q.add_argument('--gain-db',type=float,default=-3);q.add_argument('--crossfade',type=int,default=0);q.add_argument('--source-loop',action='store_true');q.add_argument('--evidence',type=Path)
    q=sub.add_parser('apply');q.add_argument('report',type=Path);q.add_argument('layer',choices=['engine','transmission_whine','turbo_spool','bov_release'])
    q=sub.add_parser('gt-source');q.add_argument('--game',choices=['gt3','gt4'],required=True);q.add_argument('--source',required=True);q.add_argument('--catalog');q.add_argument('--core')
    q=sub.add_parser('find');q.add_argument('--game',choices=['gt3','gt4'],required=True);q.add_argument('selector')
    q=sub.add_parser('inspect-bank');q.add_argument('--game',choices=['gt3','gt4'],required=True);q.add_argument('bank')
    q=sub.add_parser('event');q.add_argument('--game',choices=['gt3','gt4'],required=True);q.add_argument('name')
    q=sub.add_parser('export');q.add_argument('--game',choices=['gt3','gt4'],required=True);q.add_argument('bank');q.add_argument('entry');q.add_argument('--vehicle');q.add_argument('--event');q.add_argument('--rate',type=int,default=24000);q.add_argument('--rate-mode',choices=['nominal','native'],default='nominal')
    a=p.parse_args();project=WorkshopProject(a.project)
    if a.action=='prepare':result=project.audio_prepare_import(a.audio,trim=a.trim,crossfade=a.crossfade,gain_db=a.gain_db,use_source_loop=a.source_loop,source_evidence=json.loads(a.evidence.read_text()) if a.evidence else None)
    elif a.action=='apply':result=project.audio_apply_import(json.loads(a.report.read_text()),a.layer)
    elif a.action=='gt-source':result=project.gt_audio_configure({k:getattr(a,k) for k in ('game','source','catalog','core') if getattr(a,k)})
    elif a.action=='find':result=project.gt_audio_adapter(a.game).find_vehicle(a.selector)
    elif a.action=='inspect-bank':result=project.gt_audio_adapter(a.game).inspect(a.bank)
    elif a.action=='event':result=project.gt_audio_adapter(a.game).event_selection(a.name)
    else:result=project.gt_audio_export(a.game,a.bank,a.entry,selector=a.vehicle,rate=a.rate,rate_mode=a.rate_mode,event_name=a.event)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
