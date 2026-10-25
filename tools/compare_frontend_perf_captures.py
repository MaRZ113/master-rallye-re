"""Compare manually labelled native frontend captures without inventing FPS."""
import argparse,hashlib,json,math
from pathlib import Path
from vehicle_frontend_perf_native import RETAIL_SHA256,STAGES


def load(path):
    raw=path.read_bytes();data=json.loads(raw)
    if data.get('status')!='CAPTURED_NATIVE_FRONTEND_COUNTERS' or data.get('exe_sha256')!=RETAIL_SHA256:raise ValueError('unqualified native capture: '+str(path))
    stages=data.get('interval_summary',[])
    if [r['stage'] for r in stages]!=[r[0] for r in STAGES]:raise ValueError('incompatible timing stages')
    for row in stages:
        if type(row['calls']) is not int or row['calls']<0 or not math.isfinite(row['total_ms']) or row['total_ms']<0:raise ValueError('invalid native timing interval')
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'data':data}


def compare(before,after):
    a,b=load(before),load(after);rows=[]
    if a['data'].get('label','').casefold()!=b['data'].get('label','').casefold():raise ValueError('capture labels differ; compare the same vehicle/action')
    for old,new in zip(a['data']['interval_summary'],b['data']['interval_summary']):
        count_same=old['calls']==new['calls'];old_mean=old['total_ms']/old['calls'] if old['calls'] else None;new_mean=new['total_ms']/new['calls'] if new['calls'] else None
        rows.append({'stage':old['stage'],'before_calls':old['calls'],'after_calls':new['calls'],'equal_call_counts':count_same,'before_total_ms':old['total_ms'],'after_total_ms':new['total_ms'],
            'before_average_ms':old_mean,'after_average_ms':new_mean,'interval_time_ratio_after_before':new['total_ms']/old['total_ms'] if old['total_ms'] else None,
            'average_call_ratio_after_before':new_mean/old_mean if old_mean and new_mean is not None else None,
            'comparison_caution':None if count_same else 'different call counts; interval total is not an isolated like-for-like load latency'})
    return {'status':'COMPARED_NATIVE_TIMING_WINDOWS','label':a['data']['label'],'before':{k:v for k,v in a.items() if k!='data'},'after':{k:v for k,v in b.items() if k!='data'},'stages':rows,
        'decoder_identity':{'before':a['data'].get('decoder_path',{'verified':False,'mode':'not_recorded'}),'after':b['data'].get('decoder_path',{'verified':False,'mode':'not_recorded'}),
            'both_observed':bool(a['data'].get('decoder_path',{}).get('verified') and b['data'].get('decoder_path',{}).get('verified')),
            'caution':None if a['data'].get('decoder_path',{}).get('verified') and b['data'].get('decoder_path',{}).get('verified') else 'older capture omitted direct decoder-hook identity; profiler prefix alone does not distinguish scalar and bulk modes'},
        'boundary':'user-labelled native synchronous timing windows; no automatic CarID/texture mix/settings equality proof; nested inclusive stages must not be added; not FPS or GPU completion time'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=compare(a.before,a.after);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['stages'],indent=2))
