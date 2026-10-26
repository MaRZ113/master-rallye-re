"""Qualified addon Shadow Studio commands over the same Workshop Core."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.workshop.service import WorkshopProject
from master_rallye.workshop.shadow import CONTROLS


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',type=Path)
    p.add_argument('action',choices=['inspect','original','auto','custom','donor','preview'])
    for key,default in CONTROLS.items():p.add_argument('--'+key.replace('_','-'),type=int if key=='alpha_threshold' else float,default=default)
    a=p.parse_args();project=WorkshopProject(a.project)
    if a.action=='inspect':result=project.shadow_calculate()
    elif a.action=='preview':scene,report=project.shadow_preview_export();result={'scene':str(scene),'report':report}
    else:result=project.shadow_update(a.action,**({k:getattr(a,k) for k in CONTROLS}if a.action=='custom'else{}))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
