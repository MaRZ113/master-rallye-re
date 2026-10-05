"""Summarize an observed frame/session, preserving unknowns and incomplete frames."""
import argparse
from collections import Counter
import json
from pathlib import Path
from trace_common import annotate, read_jsonl, guarded_output, DEFAULT_MAP

def frequency(values):
    counter=Counter(json.dumps(x,sort_keys=True,allow_nan=False) for x in values)
    return [{'value':json.loads(k),'count':v} for k,v in counter.most_common()]

def summarize(records):
    header=next((r for r in records if r.get('type') in ('session','frame_begin')), {})
    draws=[r for r in records if r.get('type')=='draw']
    events=[r for r in records if r.get('type') in ('event','draw')]
    end=next((r for r in records if r.get('type')=='frame_end'),None)
    viewport=[]
    for r in events:
        if r.get('method')=='SetViewport':viewport.append({'sequence':r['sequence'],'result':r['result'],'payload_bits':r.get('payload_bits')})
    counts=Counter(r.get('method') for r in events)
    complete=bool(end and end.get('complete') and not end.get('truncated'))
    creation=[r for r in records if r.get('type') in ('create_device','resource_create','reset')]
    return {'identity':header,'complete_frame':complete,'frame_end':end,'draw_records':len(draws),
        'primitive_total_observed':sum(r.get('primitive_count',0) for r in draws),
        'method_counts_in_records':dict(counts),'device_and_resource_creation':creation,
        'unique_callers':frequency(r.get('caller') for r in draws),
        'top_owners':frequency(r.get('annotation',{}) for r in draws),
        'viewport_writes':viewport,'view_projection_writes':[r for r in events if r.get('method')=='SetTransform' and r['arguments'][0] in (2,3)],
        'fvf_stride':frequency({'vertex_shader':r.get('state',{}).get('vertex_shader'),
            'stream0':(r.get('state',{}).get('streams') or [None])[0]} for r in draws),
        'texture_stage_signatures':frequency(r.get('state',{}).get('texture_stage_states') for r in draws),
        'alpha_blend_signatures':frequency({k:r.get('state',{}).get('render_states',{}).get(k) for k in ('15','24','25','27','19','20','14')} for r in draws),
        'lighting_shader_calls':{k:(counts[k] if complete else None) for k in ('SetMaterial','SetLight','LightEnable','SetPixelShader','CreatePixelShader','CreateVertexShader')},
        'fog_observations':frequency({k:r.get('state',{}).get('render_states',{}).get(k) for k in ('28','34','35','140','36','37','38')} for r in draws),
        'categories':dict(Counter(r.get('annotation',{}).get('category','UNKNOWN') for r in draws)),
        'periodic_frame_summaries':[r for r in records if r.get('type')=='frame_summary'],
        'runtime_parity':'NOT_DETERMINED_BY_TRACE_TOOL'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path)
    ap.add_argument('--session',type=Path);ap.add_argument('--callmap',type=Path,default=DEFAULT_MAP)
    ap.add_argument('--output',type=guarded_output);a=ap.parse_args()
    records=annotate(read_jsonl(a.input),json.loads(a.callmap.read_text()))
    result=summarize(records)
    if a.session:
        session=read_jsonl(a.session);identity=next((r for r in session if r.get('type')=='session'),{})
        for key in ('exe_sha256','exe_path','proxy_sha256'):
            if key in result['identity'] and result['identity'][key]!=identity.get(key):raise ValueError('Session/frame provenance mismatch: '+key)
        result['session']=summarize(session)
        result['resource_metadata']= {str(r['device'])+':'+str(r['serial']):r for r in session if r.get('type')=='resource_create'}
    text=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    else:print(text,end='')

if __name__=='__main__':main()
