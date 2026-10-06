"""Read R-GFX2 and additive R-GFX3 traces; no game execution or visual-pass claim."""
import argparse
import copy
import json
import math
from pathlib import Path
from trace_common import read_jsonl,guarded_output


def effective_state(draw):
    state=copy.deepcopy(draw.get('state',{}));overlay=draw.get('effective_state')
    if overlay is None:return state
    if overlay.get('inherits_logical') is not True:raise ValueError('Unknown effective-state overlay convention')
    stage0=overlay.get('stage0',{})
    if stage0:
        if not state.get('texture_stage_states'):raise ValueError('Overlay without logical texture stages')
        state['texture_stage_states'][0].update(stage0)
    if 'projection' in overlay:state.setdefault('matrices',{})['3']=overlay['projection']
    return state


def projection(value):
    if not value or not isinstance(value,dict):return None
    m=value.get('values')
    if not isinstance(m,list) or len(m)!=16 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in m):return None
    if m[11]==1 and m[15]==0 and m[0]>0 and m[5]>0:
        return {'kind':'perspective','vfov':math.degrees(2*math.atan(1/m[5])),'aspect':m[5]/m[0],'z_coefficients':[m[10],m[11],m[14],m[15]]}
    if m[15]==1 and m[11]==0 and m[0] and m[5]:return {'kind':'orthographic','logical_width':abs(2/m[0]),'logical_height':abs(2/m[5])}
    return {'kind':'unsupported'}


def summarize(records):
    end=next((r for r in records if r.get('type')=='frame_end'),{})
    draws=[r for r in records if r.get('type')=='draw'];modified=[]
    for d in draws:
        logical=d.get('state',{});native=effective_state(d)
        differences={}
        lt=logical.get('texture_stage_states') or [];et=native.get('texture_stage_states') or []
        if lt and et:
            for i in range(min(len(lt),len(et))):
                for key in set(lt[i])|set(et[i]):
                    if lt[i].get(key)!=et[i].get(key):differences[f'stage{i}.{key}']={'requested':lt[i].get(key),'effective':et[i].get(key)}
        lm=logical.get('matrices',{}).get('3');em=native.get('matrices',{}).get('3')
        if lm!=em:differences['projection']={'requested':projection(lm),'effective':projection(em)}
        if differences or d.get('forwarded') is False:
            modified.append({'draw_index':d.get('draw_index'),'method':d.get('method'),'caller':d.get('caller'),
                'forwarded':d.get('forwarded',True),'feature_mask':d.get('feature_mask',0),'differences':differences})
    return {'schema_version':1,'identity':records[0] if records else {},
        'complete':bool(end.get('complete') and not end.get('truncated')),'draws':len(draws),
        'suppressed_draws':sum(d.get('forwarded') is False for d in draws),
        'native_extra_writes':sum(bool(r.get('native_only')) for r in records),
        'modified_draws':modified,'visual_runtime_pass':'PENDING_HUMAN'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('--output',type=guarded_output,required=True);a=ap.parse_args()
    a.output.write_text(json.dumps(summarize(read_jsonl(a.input)),indent=2,allow_nan=False)+'\n',encoding='utf-8')

if __name__=='__main__':main()
