"""Create a private Dakar 2 Xbox MR Classic project (see dakar2_classic_pilot)."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dakar2_classic_pilot import create_pilot
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--scene',required=True);p.add_argument('--vehicle',default='PAJERO')
p.add_argument('--retail-sma',required=True);p.add_argument('--retail-root',required=True);p.add_argument('--output',required=True)
a=p.parse_args()
r=create_pilot(a.scene,a.vehicle,a.retail_sma,a.retail_root,a.output)
print(json.dumps({k:r[k] for k in ('output','author','workshop','dimensions','collision_core_draws')},indent=1))
