"""Offline layered audition; native engine input, authored loop/BOV controls.

No DirectSound spatial mix or native-device fidelity is claimed.
"""
import hashlib,math
from master_rallye.addon_sdk.audio_profile import decode_pcm,canonical_wav
from master_rallye.addon_sdk.audio_response import SpoolState,step
from vehicle_whine_native import response_values
from vehicle_sfx_gain import sfx_near_amplitude,sfx_volume_hundredth_db

DEFAULT_SPOOL={'reference_rpm':4000,'pitch_min':.35,'pitch_max':1.8,'gain':.3,'fade_in_rpm':1500,
    'load_threshold':.15,'spool_up_seconds':.35,'spool_down_seconds':.55,'mute_neutral':True}

def mix_layers(engine,resources,report,rpm,load,gear,enabled,*,lift=False):
    samples,fmt=decode_pcm(engine)
    if (fmt['sample_rate'],fmt['channels'],fmt['bits_per_sample'])!=(48000,1,16):raise ValueError('canonical engine required')
    if not all(math.isfinite(v) for v in (rpm,load)) or not 0<=rpm<=30000 or not -1<=load<=1 or type(gear) is not int or not 0<=gear<=16:raise ValueError('invalid audition controls')
    names=('engine','transmission_whine','turbo_spool','bov_release')
    if set(enabled)-set(names):raise ValueError('unknown audition layer')
    output=[x if enabled.get('engine',True) else 0 for x in samples];tracks={};positions={};stats={};events=[]
    for name in names[1:]:
        if name not in report or not enabled.get(name,False):continue
        detail=report[name];wav=resources[detail['resource_path']];track,form=decode_pcm(wav)
        if (form['sample_rate'],form['channels'],form['bits_per_sample'])!=(48000,1,16):raise ValueError('canonical layer required')
        tracks[name]=track;positions[name]=0.;stats[name]={'resource':detail['resource_path'],'sha256':hashlib.sha256(wav).hexdigest(),'peak':0,'sum_squares':0,'active_frames':0}
    spool=report.get('turbo_spool',{}).get('response',DEFAULT_SPOOL);bov=report.get('bov_release',{}).get('response')
    duration=len(tracks.get('bov_release',[]))/48000 if 'bov_release' in tracks else .35
    state=SpoolState();bov_control=None;bov_index=None;amplitudes={}
    # Optional scripted lift is preceded by sustained load, clearly distinct
    # from reading a live throttle or proving native playback.
    if lift:
        for _ in range(300):step(state,rpm,load,gear,.01,spool,bov,duration=duration)
    for i in range(len(samples)):
        current=0. if lift and i>=len(samples)//2 else load
        if i%480==0:
            control=step(state,rpm,current,gear,.01,spool,bov,duration=duration)
            whine=response_values(report['transmission_whine']['response'],rpm,current*500,500,gear) if 'transmission_whine' in tracks else None
            if control['bov'] and 'bov_release' in tracks:
                bov_control=control['bov'];bov_index=0.;events.append({'time_seconds':i/48000,**bov_control})
            for name,c in (('transmission_whine',whine),('turbo_spool',control),('bov_release',bov_control)):
                if name in tracks and c is not None:
                    amplitudes[name]=sfx_near_amplitude(c['gain'])
                    stats[name]['native_volume_hundredth_db']=sfx_volume_hundredth_db(c['gain'])
        for name,track in tracks.items():
            c=whine if name=='transmission_whine' else control if name=='turbo_spool' else bov_control
            if c is None or (name=='bov_release' and bov_index is None):continue
            q=bov_index if name=='bov_release' else positions[name];index=int(q);fraction=q-index
            if name=='bov_release' and index>=len(track):bov_index=None;continue
            next_index=min(index+1,len(track)-1) if name=='bov_release' else (index+1)%len(track)
            value=round((track[index%len(track)]*(1-fraction)+track[next_index]*fraction)*amplitudes[name])
            output[i]+=value;d=stats[name];d['peak']=max(d['peak'],abs(value));d['sum_squares']+=value*value;d['active_frames']+=bool(value)
            if name=='bov_release':bov_index+=c['pitch']
            else:positions[name]=(q+c['pitch'])%len(track)
    clipped=sum(not -32768<=x<=32767 for x in output)
    for d in stats.values():d['rms']=math.sqrt(d.pop('sum_squares')/len(samples))
    return canonical_wav([max(-32768,min(32767,x)) for x in output]),{'layers':stats,'bov_events':events,'clipped_samples':clipped,
        'mode':'scripted sustained-load/lift' if lift else 'constant controls','boundary':'Original engine DSP plus authored supplemental controls and verified native near-listener SFX gain curve; no spatial attenuation, native device/thread mixing or gameplay confirmation'}
