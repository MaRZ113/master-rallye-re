"""Compatibility CLI for the accepted Forester restoration manifest.

Vehicle values, original bindings and resource mappings live in the manifest.
Use restore_demo_vehicle.py for new restorations. Accepted outputs are never
rewritten; this command requires a fresh private destination.
"""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.demo_restoration import localized_records,prepare as restore


def prepare(demo,rebaked,retail_sma,ps2,roster_config,output,*,retail_corrections=False,mini_icon=None):
    manifest=json.loads((ROOT/'research/vehicles/sdk/restorations/forester-931.json').read_text())
    roots={'demo':str(Path(demo).absolute()),'pcg':str(Path(rebaked).absolute().parent),
           'retail':str(Path(retail_sma).absolute().parent),'ps2':str(Path(ps2).absolute().parent),
           'legacy':str(Path(demo).absolute().parent/'demo-8.4.1'),
           'later':str(Path(mini_icon).absolute().parents[3]if mini_icon else Path(demo).absolute().parent/'demo-9.10.0')}
    # Both legacy flag forms now select the CURRENT owner-approved reference.
    # Historical first-delivery physics remains in Git and V-DEF1 reports.
    result=restore(manifest,roots,roster_config,output,sdk_root=ROOT)
    output=Path(output);(output/'Open-Forester-Workshop.cmd').write_bytes((output/'Open-Restoration-Workshop.cmd').read_bytes())
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('demo','rebaked','retail-sma','ps2','roster-config','output'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--retail-corrections',action='store_true',help='Compatibility flag; current manifest always uses the owner-approved policy')
    p.add_argument('--mini-icon',type=Path);a=p.parse_args()
    prepare(a.demo,a.rebaked,a.retail_sma,a.ps2,a.roster_config,a.output,retail_corrections=a.retail_corrections,mini_icon=a.mini_icon)
