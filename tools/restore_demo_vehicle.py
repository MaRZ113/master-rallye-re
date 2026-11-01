"""Restore one manifest-qualified Demo vehicle through Heritage/Workshop/CMD."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.demo_restoration import prepare

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','roots','roster-config','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--author-only',action='store_true');a=p.parse_args()
    prepare(json.loads(a.manifest.read_text()),json.loads(a.roots.read_text()),a.roster_config,a.output,sdk_root=ROOT,build=not a.author_only)
