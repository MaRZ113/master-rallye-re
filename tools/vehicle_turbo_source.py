"""Original authored test audio, explicitly NOT extracted GT turbo/BOV samples."""
from __future__ import annotations
import argparse,hashlib,json,math,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.addon_sdk.audio_profile import canonical_wav


def synthesize_spool():
    # All oscillators complete integer cycles in one second for seamless looping.
    values=[]
    for i in range(48000):
        t=i/48000
        phase=2*math.pi*2400*t+.07*math.sin(2*math.pi*37*t)
        values.append(round(6500*(math.sin(phase)+.18*math.sin(2*phase)+.07*math.sin(2*math.pi*4011*t))))
    return canonical_wav(values)


def synthesize_bov():
    rng=random.Random(77197);values=[];previous=0.
    for i in range(16800):
        t=i/48000;noise=rng.uniform(-1,1);high=noise-previous;previous=noise
        envelope=min(1,t/.006)*math.exp(-t/.065)*max(0,min(1,(.35-t)/.015))
        values.append(round(6000*high*envelope))
    return canonical_wav(values)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kind',choices=('spool','bov'),required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('output exists')
    raw=synthesize_spool() if a.kind=='spool' else synthesize_bov()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(raw)
    report={'kind':'original_synthetic_test_'+a.kind,'sha256':hashlib.sha256(raw).hexdigest(),'source':'Authored deterministic test sound; no GT/MR sample. Not authentic turbo machinery recording.','sample_rate':48000,'duration_seconds':1 if a.kind=='spool' else .35}
    a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
