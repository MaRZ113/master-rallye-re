"""Build an optional audio-profile project using the shared sealed SDK builder.

The project must contain audio-profile.json and its private/custom WAV input.
Existing project physics are preserved unless an explicit profile is supplied.
No game is launched and no original executable is written.
"""
import argparse,json
from pathlib import Path
from build_vehicle_physics_candidate import build,ROOT

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True);p.add_argument('--physics-profile',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--retail-data-sma',type=Path,default=ROOT.parent/'corpora/retail/Data.sma')
    p.add_argument('--retail-data-root',type=Path,default=ROOT.parent/'corpora/retail/Data.sma_unpacked')
    p.add_argument('--retail-exe',type=Path,default=ROOT.parent/'MRallye.exe')
    a=p.parse_args()
    if not (a.project/'audio-profile.json').is_file():p.error('project requires explicit audio-profile.json')
    r=build(a.project,a.physics_profile,a.output,retail_data_sma=a.retail_data_sma,retail_data_root=a.retail_data_root,retail_exe=a.retail_exe)
    launch=a.output/'Launch-Audio.cmd';launch.write_bytes((a.output/'Launch-Physics.cmd').read_bytes())
    r.update(status='READY_FOR_HUMAN_AUDIO_TEST',scope='independent source waveform; native MR synthesis and stock tuning retained')
    (a.output/'audio-candidate.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])

if __name__=='__main__':main()
