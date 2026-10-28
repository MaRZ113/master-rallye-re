"""Create the approved isolated Evo2 4Runner Source Fidelity author/candidate."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.source_garage_pilot import create_pilot
from master_rallye.fourrunner_visual_kit import OPTIONS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('scene','donor','retail-sma','retail-root','base-roster','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--author-only',action='store_true',help='Configure Workshop build settings but stop before runtime candidate compilation')
    parser.add_argument('--mr-visual-kit',action='store_true',help='Optional MR paint/mirrors/cabin/rear-glazing/body-frame presentation; original source baseline remains immutable')
    args=parser.parse_args()
    report=create_pilot(args.scene,args.donor,args.retail_sma,args.output,
        retail_root=args.retail_root,base_roster=args.base_roster,build=not args.author_only,
        visual_options=dict.fromkeys(OPTIONS,True)if args.mr_visual_kit else None)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
