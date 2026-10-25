"""Deterministic authored whine source and offline independent-loop audition.

This is an explicitly synthetic gearbox approximation. It contains no GT/MR
sample and does not emulate a DirectSound device or establish gameplay parity.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.audio_profile import canonical_wav,decode_pcm
from vehicle_whine_native import response_values

DEFAULT_RESPONSE={'reference_rpm':4000,'pitch_min':.2,'pitch_max':1.8,
                  'gain_drive':.18,'gain_coast':.08,'fade_in_rpm':1000,'mute_neutral':True}


def synthesize_loop():
    """One-second periodic 800 Hz mesh tone with two bounded harmonics.

    Every component completes an integer number of cycles. Reference 4000RPM
    and 12 teeth produce 800Hz by the authored f=RPM/60*teeth relation; these
    are explicit design choices, not measured Lancer transmission constants.
    """
    samples=[]
    for i in range(48000):
        t=i/48000;phase=2*math.pi*800*t+.025*math.sin(2*math.pi*40*t)
        samples.append(round(6000*(math.sin(phase)+.30*math.sin(2*phase)+.08*math.sin(3*phase))))
    return canonical_wav(samples)


def audition_whine(wav,response,rpms,loads=None,gears=None,seconds=1.):
    if not isinstance(rpms,list) or not 1<=len(rpms)<=12 or any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=30000 for x in rpms):raise ValueError('bounded whine RPM sequence required')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not .02<=seconds<=3:raise ValueError('whine segment outside0.02..3 seconds')
    loads=[1.]*len(rpms) if loads is None else loads;gears=[2]*len(rpms) if gears is None else gears
    if len(loads)!=len(rpms) or len(gears)!=len(rpms) or any(type(x) not in (int,float) or not math.isfinite(x) or not -1<=x<=1 for x in loads) or any(type(x) is not int or not 0<=x<=16 for x in gears):raise ValueError('whine load/gear sequence mismatch or bounds')
    values,fmt=decode_pcm(wav)
    if fmt['sample_rate']!=48000 or fmt['channels']!=1 or fmt['bits_per_sample']!=16:raise ValueError('whine audition requires compiled mono16@48000')
    rendered=[];rows=[];phase=0.
    for rpm,load,gear in zip(rpms,loads,gears):
        control=response_values(response,rpm,load*500,500,gear);segment=[]
        for _ in range(round(seconds*48000)):
            q=int(phase);fraction=phase-q
            segment.append(round((values[q%len(values)]*(1-fraction)+values[(q+1)%len(values)]*fraction)*control['gain']))
            phase=(phase+control['pitch'])%len(values)
        rendered+=segment
        rows.append({'inputshaft_rpm':rpm,'signed_crank_torque_over_peak':load,'native_gear_index':gear,**control,
                     'peak_pcm16':max(map(abs,segment)),'rms_pcm16':math.sqrt(sum(x*x for x in segment)/len(segment))})
    return canonical_wav(rendered),{'segments':rows,'resource_sha256':hashlib.sha256(wav).hexdigest(),
        'boundary':'Authored controls and linear loop resampling only; no DirectSound scheduling/spatial attenuation, no original GT gearbox playback, no gameplay qualification.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--synthesize',action='store_true');p.add_argument('--resource',type=Path)
    p.add_argument('--profile',type=Path);p.add_argument('--rpm',type=float,action='append');p.add_argument('--load',type=float,action='append');p.add_argument('--gear',type=int,action='append');p.add_argument('--seconds',type=float,default=1.)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--play',action='store_true');a=p.parse_args()
    if a.output.exists():raise ValueError('output already exists')
    if a.synthesize:
        if a.resource or a.profile or a.rpm:raise ValueError('synthesize takes no resource/profile/RPM sequence')
        data=synthesize_loop();report={'kind':'authored_periodic_mesh_tone','sha256':hashlib.sha256(data).hexdigest(),'reference_rpm':4000,'tooth_count_design_choice':12,'sample_rate':48000,'frames':48000,'default_response':DEFAULT_RESPONSE,'provenance':'Original deterministic synthetic source; no extracted GT/MR audio. 800Hz fundamental, harmonics 0.30/0.08, 40Hz phase modulation0.025rad.'}
    else:
        if not a.resource or not a.rpm:raise ValueError('audition requires resource and RPM sequence')
        response=json.loads(a.profile.read_text())['transmission_whine']['response'] if a.profile else DEFAULT_RESPONSE
        data,report=audition_whine(a.resource.read_bytes(),response,a.rpm,a.load,a.gear,a.seconds)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(data);a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if a.play:
        import winsound
        winsound.PlaySound(str(a.output.resolve()),winsound.SND_FILENAME)
