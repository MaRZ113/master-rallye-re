"""Build optional visual/shadow/audio sidecars without changing project physics.

Uses the shared project, collection, damage and sealed launcher builders. All
source assets remain user supplied. No game launch or original EXE disk write.
"""
import argparse,json
from pathlib import Path
from build_vehicle_physics_candidate import build,ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--retail-data-sma',type=Path,default=ROOT.parent/'corpora/retail/Data.sma')
    p.add_argument('--retail-data-root',type=Path,default=ROOT.parent/'corpora/retail/Data.sma_unpacked')
    p.add_argument('--retail-exe',type=Path,default=ROOT.parent/'MRallye.exe')
    p.add_argument('--base-manifest',type=Path,action='append');a=p.parse_args()
    report=build(a.project,None,a.output,retail_data_sma=a.retail_data_sma,
        retail_data_root=a.retail_data_root,retail_exe=a.retail_exe,base_manifests=a.base_manifest)
    (a.output/'Launch-Vehicle.cmd').write_bytes((a.output/'Launch-Physics.cmd').read_bytes())
    report.update(status='READY_FOR_HUMAN_VEHICLE_EXTENSION_TEST',
        scope='Optional source-pinned mechanical fitment, shadow and additive audio; existing project physics preserved')
    (a.output/'vehicle-candidate.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'])


if __name__=='__main__':main()
