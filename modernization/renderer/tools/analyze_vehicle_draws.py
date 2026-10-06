"""Summarize D3D-boundary material families; no single frame proves a vehicle."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import ntpath
from pathlib import Path
from trace_common import read_jsonl,TARGET_SHA

# Values and coordinate-size encoding verified against pinned vendor/d3d8/d3d8types.h.
def decode_fvf(fvf):
    if not isinstance(fvf,int) or fvf not in (0x102,0x112,0x142,0x152,0x242,0x252):return {'fvf':fvf,'known_layout':False}
    normals=bool(fvf&0x10);diffuse=bool(fvf&0x40);uv=(fvf&0xf00)>>8
    return {'fvf':f'0x{fvf:03X}','known_layout':True,'position':'XYZ','normal':normals,'diffuse':diffuse,'uv_count':uv,'stride':12+12*normals+4*diffuse+8*uv,'uv_dimensions':[2]*uv}

def family(draw):
    s=draw.get('state',{});st=s.get('texture_stage_states') or [{},{}];rs=s.get('render_states',{})
    return {'layout':decode_fvf(s.get('vertex_shader')),'stage0':{k:st[0].get(k) for k in ('1','2','3','4','5','6','11','24')},
            'stage1':{k:st[1].get(k) for k in ('1','2','3','4','5','6','11','24')},
            'alpha_test':rs.get('15'),'alpha_blend':rs.get('27'),'z_write':rs.get('14'),'lighting':rs.get('137')}

def analyze(records):
    header=records[0] if records else {};end=records[-1] if records else {}
    complete=header.get('type')=='frame_begin' and end.get('type')=='frame_end' and end.get('complete') is True and end.get('truncated') is False
    known=header.get('exe_sha256')==TARGET_SHA and complete
    families={};groups=defaultdict(lambda:{'draws':0,'triangles':0,'tracks':set(),'dynamic':False});classifications=Counter();reflections=0
    for d in records:
        if d.get('type')!='draw':continue
        classifications[d.get('object_classification','UNAVAILABLE_LEGACY')]+=1
        reflections+=d.get('reflection_feature','Stock')!='Stock'
        caller=d.get('caller',{})
        if not known or d.get('result')!=0 or d.get('method')!='DrawIndexedPrimitive' or caller.get('return_rva')!=0x17707e or ntpath.normcase(caller.get('module') or '')!=ntpath.normcase(header.get('exe_path') or ''):continue
        f=family(d);key=json.dumps(f,sort_keys=True);item=families.setdefault(key,dict(f,draws=0,triangles=0,texture_generations=set()))
        item['draws']+=1;item['triangles']+=d['primitive_count'] if d.get('primitive_type') in (4,5,6) else 0
        item['texture_generations'].add(tuple(t.get('last_creation_serial',0) for t in d['state'].get('textures',[])[:2]))
        world=d['state'].get('matrices',{}).get('256')
        if world:
            key=tuple(world.get('bits') or world.get('values',[]));g=groups[key];g['draws']+=1;g['triangles']+=d['primitive_count'] if d.get('primitive_type') in (4,5,6) else 0;g['tracks'].add(d.get('transform_track_id',0));g['dynamic']|=d.get('transform_dynamic',False)
    for v in families.values():v['texture_generations']=sorted(v['texture_generations'])
    for v in groups.values():v['tracks']=sorted(v['tracks'])
    return {'exact_build_and_complete':known,'header':{k:header.get(k) for k in ('exe_sha256','proxy_sha256','device','frame')},'families':list(families.values()),'transform_groups':list(groups.values()),'classification_counts':dict(classifications),'reflection_modified_draws':reflections,'vehicle_semantics':'UNPROVEN_UNLESS_SEPARATELY_CORRELATED','legacy_temporal_status':'UNAVAILABLE' if not any('transform_dynamic' in d for d in records) else 'RECORDED_RUNTIME_TRACKER'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('captures',type=Path,nargs='+');a=ap.parse_args()
    results=[]
    for p in a.captures:
        result=analyze(read_jsonl(p));result['file']=p.name;result['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();results.append(result)
    # No identities are joined across sessions or independently sampled F10 frames.
    print(json.dumps({'captures':results,'cross_capture_temporal_inference':False},indent=2,allow_nan=False))
if __name__=='__main__':main()
