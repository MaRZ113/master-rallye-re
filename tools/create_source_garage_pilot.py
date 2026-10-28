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
    parser.add_argument('--mr-visual-kit',action='store_true',help='Rejected legacy option; retained only to explain the D3D8 quality gate')
    parser.add_argument('--upper-brake-lamp',action='store_true',help='Independent upper brake strip test variant; new D3D8 owner testing required')
    args=parser.parse_args()
    if args.mr_visual_kit:parser.error('Visual Polish kit rejected by owner D3D8 review; build Stable with all five options off.')
    report=create_pilot(args.scene,args.donor,args.retail_sma,args.output,
        retail_root=args.retail_root,base_roster=args.base_roster,build=not args.author_only,
        upper_brake_lamp=args.upper_brake_lamp)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
