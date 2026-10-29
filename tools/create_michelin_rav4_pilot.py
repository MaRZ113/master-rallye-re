"""Create only the qualified private Michelin RAV4 alternative roster pilot."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.michelin_native_pilot import create


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('scene','donor','retail-sma','retail-root','base-roster','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--author-only',action='store_true');a=p.parse_args()
    print(json.dumps(create(a.scene,a.donor,a.retail_sma,a.output,retail_root=a.retail_root,base_roster=a.base_roster,build=not a.author_only),indent=2))
