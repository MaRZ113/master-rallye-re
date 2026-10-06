"""Read-only sampled vehicle identity/material evidence; never infer a new DLL runtime pass."""
import argparse
from collections import Counter,defaultdict
import hashlib,json,math,ntpath
from pathlib import Path
from analyze_vehicle_draws import family,rectangle,reflection_audit
from trace_common import TARGET_SHA,read_jsonl,ROOT

def resource_family(state):
    streams=state.get('streams',[]);index=state.get('indices') or {}
    if not streams or not streams[0]:return 0
    vals=(streams[0].get('last_creation_serial',0),index.get('last_creation_serial',0),streams[0].get('stride',0),state.get('vertex_shader',0))
    if not vals[0] or not vals[1] or not vals[2] or not vals[3]:return 0
    h=14695981039346656037
    for v in vals:
        for shift in range(0,64,8):h=((h^((v>>shift)&255))*1099511628211)&((1<<64)-1)
    return h or 1

def summarize(rows):
    h=rows[0] if rows else {};end=rows[-1] if rows else {}
    draws=[r for r in rows if r.get('type')=='draw']
    exact=h.get('type')=='frame_begin' and h.get('exe_sha256')==TARGET_SHA and end.get('type')=='frame_end' and end.get('complete') is True and end.get('truncated') is False and end.get('dropped_records')==0 and end.get('draw_records')==len(draws)
    summary=next((r for r in rows if r.get('type')=='frame_summary'),{})
    result={'exact_complete':exact,'header':{k:h.get(k) for k in ('proxy_version','proxy_sha256','exe_sha256','device','frame')},'classifier':summary.get('classifier',{}),'fov_culling':summary.get('fov_culling',{}),'groups':[],'structural_candidates':[],'reflection_audit':reflection_audit(rows,exact),'evidence_grade':'RECORDED_RUNTIME_INPUT_NOT_NEW_RUNTIME_PASS'}
    if not exact:return result
    groups={}
    for d in draws:
        caller=d.get('caller',{});s=d.get('state',{});m=s.get('matrices',{}).get('256') or {};w=m.get('values',[])
        if d.get('result')!=0 or d.get('method')!='DrawIndexedPrimitive' or not d.get('race_context') or not d.get('geometry_signature') or caller.get('return_rva')!=0x17707e or ntpath.normcase(caller.get('module') or '')!=ntpath.normcase(h.get('exe_path') or '') or len(w)!=16 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in w):continue
        fvf=s.get('vertex_shader');f=family(d);env=f['stage1']=={'1':18,'2':1,'3':2,'4':4,'5':1,'6':2,'11':f['stage1'].get('11'),'24':2} and isinstance(f['stage1'].get('11'),int) and f['stage1']['11']&0xffff0000==0x10000
        opaque=f['alpha_blend']==0 and f['z_write']==1
        reasons=(64 if env else 0)|(128 if opaque else 0)
        key=tuple(m.get('bits') or w);g=groups.setdefault(key,{'world':w,'track':d.get('transform_track_id',0),'age':d.get('transform_track_age',0),'dynamic':d.get('transform_dynamic',False),'draws':[]})
        g['draws'].append({'signature':d['geometry_signature'],'resource_family':resource_family(s),'fvf':fvf,'reasons':reasons,'triangles':d.get('primitive_count',0)})
    # Only compact body/wheel diagnostic groups; unrelated large scene groups are not copied.
    result['groups']=[g for g in groups.values() if any(d['fvf'] in (0x152,0x112) for d in g['draws']) and len(g['draws'])<=64]
    bodies=[g for g in result['groups'] if sum(d['fvf'] in (0x142,0x152,0x242,0x252) for d in g['draws'])>=4 and any(d['fvf'] in (0x142,0x242) for d in g['draws']) and any(d['fvf']==0x152 and d['reasons']==192 for d in g['draws'])]
    wheels=[g for g in result['groups'] if len(g['draws'])>=2 and all(d['fvf']==0x112 and d['reasons']==192 for d in g['draws'])]
    for b in bodies:
        w=b['world'];near=[]
        for wheel in wheels:
            delta=[wheel['world'][12+k]-w[12+k] for k in range(3)];local=[sum(delta[k]*w[a*4+k] for k in range(3)) for a in range(3)]
            if .35<=abs(local[0])<=2.5 and .5<=abs(local[2])<=4 and -2<=local[1]<=1.5:near.append((wheel,local))
        shared=set.intersection(*(set(d['resource_family'] for d in g['draws']) for g,_ in near)) if near else set()
        error=rectangle([p for _,p in near]) if len(near)==4 else None
        result['structural_candidates'].append({'chassis_track':b['track'],'chassis_dynamic':b['dynamic'],'wheel_tracks':[g['track'] for g,_ in near],'local_centers':[p for _,p in near],'four_wheel_geometry':error is not None and bool(shared-{0}),'symmetry_error':error,'native_temporal_admission':'NOT_REPLAYED_BY_THIS_TOOL'})
    return result

def compare(a,b,track):
    if not a['exact_complete'] or not b['exact_complete']:raise ValueError('Pair must be exact and complete')
    for k in ('proxy_sha256','exe_sha256','device'):
        if a['header'][k]!=b['header'][k]:raise ValueError('Pair provenance mismatch: '+k)
    if a['classifier'].get('epoch')!=b['classifier'].get('epoch'):raise ValueError('Pair crosses classifier epoch')
    ga=[g for g in a['groups'] if g['track']==track];gb=[g for g in b['groups'] if g['track']==track]
    if len(ga)!=1 or len(gb)!=1:raise ValueError('Chassis track must uniquely identify each sampled group')
    sa={d['signature'] for d in ga[0]['draws']};sb={d['signature'] for d in gb[0]['draws']}
    added=[d for d in gb[0]['draws'] if d['signature'] not in sa]
    return {'track':track,'draws_before':len(ga[0]['draws']),'draws_after':len(gb[0]['draws']),'shared_signatures':len(sa&sb),'removed_signatures':len(sa-sb),'added_signatures':len(sb-sa),'new_draw_families':added,'join':'EXPLICIT_HUMAN_CORRELATED_SAMPLES; intervening frames not replayed','brake_semantics':'HUMAN_OBSERVATION; generic mutation in production'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('captures',nargs='+',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
    if a.output:
        out=a.output.resolve()
        if out.suffix!='.json' or not any(out.is_relative_to(ROOT/p) for p in ('research','data','.analysis')):raise ValueError('Output must stay in renderer phase')
    frames=[]
    for p in a.captures:
        r=summarize(read_jsonl(p));r.update(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size);frames.append(r)
    result={'schema_version':1,'frames':frames,'cross_capture_temporal_inference':False,'new_candidate_runtime':'PENDING'}
    text=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8',newline='\n')
    else:print(text,end='')
if __name__=='__main__':main()
