"""Summarize observed resource pools and Reset boundaries; no lifetime guessing."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from trace_common import read_jsonl,TARGET_SHA
POOL_INDEX={'CreateTexture':5,'CreateVolumeTexture':6,'CreateCubeTexture':4,'CreateVertexBuffer':3,'CreateIndexBuffer':3}
POOL_NAMES={0:'DEFAULT',1:'MANAGED',2:'SYSTEMMEM',3:'SCRATCH'}
def analyze(records):
    if not records or records[0].get('exe_sha256')!=TARGET_SHA:return {'exact_build':False,'segments':[]}
    segments=[];counts=Counter();resets=[];before=0
    for r in records:
        if r.get('type')=='resource_create':
            method=r['method'];a=r.get('arguments',[])
            pool=a[POOL_INDEX[method]] if method in POOL_INDEX and len(a)>POOL_INDEX[method] else 2 if method=='CreateImageSurface' else 0 if method in ('CreateRenderTarget','CreateDepthStencilSurface') else -1
            counts[f'{method}:{POOL_NAMES.get(pool,"UNKNOWN")}']+=1
        elif r.get('type')=='reset':
            segments.append({'after_successful_reset':before,'resource_creations':dict(sorted(counts.items())),'ending_reset_hresult':r.get('hresult')});counts.clear()
            resets.append({'hresult':r.get('hresult'),'parameters_before':r.get('parameters_before'),'parameters_after':r.get('parameters_after')})
            before+=r.get('hresult')==0
    segments.append({'after_successful_reset':before,'resource_creations':dict(sorted(counts.items()))})
    return {'exact_build':True,'segments':segments,'resets':resets,'resource_release_observed':False}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('session',type=Path);a=ap.parse_args();r=analyze(read_jsonl(a.session));r['source']={'path':str(a.session),'sha256':hashlib.sha256(a.session.read_bytes()).hexdigest()};print(json.dumps(r,indent=2,allow_nan=False))
if __name__=='__main__':main()
