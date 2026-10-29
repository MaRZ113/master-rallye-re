"""Create only the exact approved private Paris-Dakar Silver source candidate."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from master_rallye.paris_dakar_silver_pilot import create_pilot

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('scene','donor','retail-sma','retail-root','base-roster','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--author-only',action='store_true')
    args=parser.parse_args()
    print(json.dumps(create_pilot(args.scene,args.donor,args.retail_sma,args.output,retail_root=args.retail_root,base_roster=args.base_roster,build=not args.author_only),indent=2))

if __name__=='__main__':main()
