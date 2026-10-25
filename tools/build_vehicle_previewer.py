"""Build the asset-independent Windows fixed-function Vehicle Previewer."""
import argparse,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.research-output/vehicles/previewer/build');p.add_argument('--generator');a=p.parse_args()
    command=['cmake','-S',str(ROOT/'vehicle_previewer'),'-B',str(a.output.resolve()),'-A','x64']
    if a.generator:command+=['-G',a.generator]
    subprocess.run(command,check=True);subprocess.run(['cmake','--build',str(a.output.resolve()),'--config','Release'],check=True)
    print(a.output.resolve()/'Release/mr-vehicle-previewer.exe')
