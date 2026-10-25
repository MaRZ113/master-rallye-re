"""Authored spool/BOV controls, never a claim of native boost pressure.

Inputs are caller-supplied verified RPM and signed crank torque / peak torque.
Release is a load proxy until a genuine throttle signal is qualified. Callers
must provide elapsed seconds, not assume a fixed frame rate. The runtime uses
the original millisecond clock with a bounded timestep.
"""
from dataclasses import dataclass
import math

@dataclass
class SpoolState:
    pressure:float=0.
    previous_load:float=0.
    cooldown:float=0.
    active_remaining:float=0.
    events:int=0


def step(state,rpm,load,gear,dt,spool,bov=None,*,duration=.2,finished=False):
    if not all(math.isfinite(x) for x in (rpm,load,dt,duration)) or not .0001<=dt<=.25 or not .02<=duration<=4:
        raise ValueError('bounded finite audio control inputs required')
    load=max(0.,min(1.,load));rpm=abs(rpm)
    old=state.pressure;state.cooldown=max(0.,state.cooldown-dt);state.active_remaining=max(0.,state.active_remaining-dt)
    target=max(0.,min(1.,(load-spool['load_threshold'])/(1-spool['load_threshold'])))
    target*=min(1.,rpm/spool['fade_in_rpm'])
    if finished or (gear==1 and spool['mute_neutral']):target=0.
    event=None
    if (bov and not finished and (gear!=1 or not bov.get('mute_neutral',True)) and rpm>=bov['min_rpm'] and old>=bov['boost_threshold']
        and (state.previous_load-load)/dt>=bov['release_rate_threshold']
        and state.cooldown==0 and state.active_remaining==0):
        state.events+=1
        # Stable bounded variation, reproducible for diagnostics.
        variation=((state.events*1664525+1013904223)&0xffff)/65535*2-1
        pitch=1+variation*bov['pitch_variation']
        event={'gain':bov['gain']*old,'pitch':pitch,'event':state.events}
        state.cooldown=bov['retrigger_seconds'];state.active_remaining=duration/pitch
    tau=spool['spool_up_seconds'] if target>old else (bov['release_decay_seconds'] if bov and state.active_remaining else spool['spool_down_seconds'])
    state.pressure=max(0.,min(1.,old+(target-old)*dt/(tau+dt)));state.previous_load=load
    pitch=max(spool['pitch_min'],min(spool['pitch_max'],rpm/spool['reference_rpm']))
    return {'pitch':pitch,'gain':spool['gain']*state.pressure if not finished else 0.,'estimated_spool':state.pressure,'bov':event,
        'boundary':'Authored estimated spool and load-release proxy; no physical boost signal'}
