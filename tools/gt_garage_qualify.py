"""Qualify explicit private representative GT3 cases, without mass installation."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.gt3_qualification import batch
from master_rallye.workshop.service import write_json

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Qualification output exists')
    if a.cases.stat().st_size>1024*1024:raise ValueError('Qualification case-file budget')
    report=batch(json.loads(a.cases.read_text(encoding='utf-8')));write_json(a.output,report)
    print(json.dumps([{k:c[k]for k in ('name','L0','L1','L2')}for c in report['cases']],indent=2))
