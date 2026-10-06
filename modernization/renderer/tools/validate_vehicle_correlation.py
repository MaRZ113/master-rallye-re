"""Offline validation only. Metrics adapted read-only from retired R-GFX2 commit5861ed2. No Broker dependency in runtime."""
import math, re
def matrix(value):
    if isinstance(value, dict): value = value.get('values')
    if isinstance(value, str):
        rows = re.findall(r'\[([^\]]+)\]', value)
        if len(rows) != 4: raise ValueError('Matrix requires four bracketed rows')
        value = [row.split() for row in rows]
    if isinstance(value, list) and len(value) == 4 and all(isinstance(r, list) and len(r) == 4 for r in value):
        value = [x for row in value for x in row]
    if not isinstance(value, list) or len(value) != 16: raise ValueError('Matrix requires 16 elements')
    if any(isinstance(x, bool) for x in value): raise ValueError('Boolean matrix element')
    result = [float(x) for x in value]
    if not all(math.isfinite(x) for x in result): raise ValueError('Non-finite matrix')
    return result

def affine(value):
    m = matrix(value)
    if any(abs(m[i]) > 1e-5 for i in (3,7,11)) or abs(m[15]-1) > 1e-5:
        raise ValueError('WORLD/Broker matrix must be affine row-vector form')
    if any(sum(m[i+j]**2 for j in range(3)) < 1e-12 for i in (0,4,8)):
        raise ValueError('Degenerate transform basis')
    return m

def angle(a,b):
    denominator = math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
    if denominator < 1e-12: raise ValueError('Degenerate basis')
    return math.degrees(math.acos(max(-1., min(1., sum(x*y for x,y in zip(a,b))/denominator))))

def metrics(broker, world, wheel=False):
    b,n = affine(broker),affine(world)
    angles = [angle(b[i:i+3], n[i:i+3]) for i in (0,4,8)]
    return {'translation_error':math.dist(b[12:15], n[12:15]),
            'orientation_error':angles[0] if wheel else max(angles),
            'orientation_metric':'directed_local_X_axle_angle_degrees' if wheel else 'max_basis_angle_degrees',
            'full_basis_orientation_error':max(angles), 'basis_angles_degrees':angles}
import argparse
from collections import defaultdict,Counter
import hashlib,json,ntpath
from pathlib import Path
from trace_common import read_jsonl,TARGET_SHA
from analyze_vehicle_draws import family

def correlate(broker,records,car='Car0'):
    entries={e['path']:e.get('value') for e in broker.get('entries',[]) if e['path'].startswith(f'Physics/{car}/')}
    header=records[0];end=records[-1]
    source=broker.get('source',{})
    if source.get('image_sha256')!=TARGET_SHA or ntpath.normcase(source.get('image_path') or '')!=ntpath.normcase(header.get('exe_path') or ''):raise ValueError('Broker build/module mismatch')
    seen=set()
    for e in broker.get('entries',[]):
        if e['path'].startswith(f'Physics/{car}/'):
            if e['path'] in seen:raise ValueError('Ambiguous Broker transform path')
            seen.add(e['path'])
    if header.get('exe_sha256')!=TARGET_SHA or not end.get('complete') or end.get('truncated'):raise ValueError('Requires complete canonical capture')
    groups=defaultdict(list)
    for d in records:
        if d.get('type')=='draw' and d.get('method')=='DrawIndexedPrimitive' and d.get('result')==0 and d.get('caller',{}).get('return_rva')==0x17707e and ntpath.normcase(d.get('caller',{}).get('module') or '')==ntpath.normcase(header.get('exe_path') or ''):
            w=d['state'].get('matrices',{}).get('256')
            if w:groups[tuple(affine(w))].append(d)
    results=[]
    for path in [f'Physics/{car}/Transform']+[f'Physics/{car}/Wheel{i}/Transform' for i in range(4)]:
        matches=[]
        if path in entries:
            for w,draws in groups.items():
                error=metrics(entries[path],list(w),'/Wheel' in path)
                if error['translation_error']<=.35 and error['orientation_error']<=5:
                    counts=Counter(json.dumps(family(d),sort_keys=True) for d in draws)
                    matches.append({'draws':len(draws),'triangles':sum(d['primitive_count'] for d in draws),'draw_indices':[d['draw_index'] for d in draws],'errors':error,'families':[dict(json.loads(k),draws=v,triangles=sum(d['primitive_count'] for d in draws if json.dumps(family(d),sort_keys=True)==k)) for k,v in counts.items()]})
        results.append({'broker_path':path,'matches':matches,'confidence':'UNIQUE_TRANSFORM_GROUP' if len(matches)==1 else 'AMBIGUOUS' if matches else 'NO_MATCH'})
    return {'objects':results,'same_frame_atomicity':False,'wheel_metric':'directed_X_axle_plus_translation','production_uses_broker':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('broker',type=Path);ap.add_argument('frame',type=Path);a=ap.parse_args()
    b=json.loads(a.broker.read_text(encoding='utf-8-sig'));pid=re.match(r'frame-(\d+)-',a.frame.name)
    if not pid or int(pid.group(1))!=b.get('source',{}).get('process_id'):raise ValueError('Broker/frame process mismatch')
    result=correlate(b,read_jsonl(a.frame));result['inputs']=[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (a.broker,a.frame)];print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':main()
