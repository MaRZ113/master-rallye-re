"""Owner-local Windows source open/stage/render/cache benchmark, no game launch."""
from pathlib import Path
import argparse
import copy
import json
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.workshop.preview_cache import PreviewCache,SceneMemory,stage,render,Task,Cancelled
from master_rallye.source_scene_preview import preview_cull


def run(paths,viewer,output):
    paths=[Path(p).absolute()for p in paths];loaded=[u.load_scene(p)for p in paths]
    output=u.output_directory(Path(output),[p.parent for p in paths]);output.mkdir()
    memory=SceneMemory();cache=PreviewCache(output/'cache');rows=[]
    def timed(label,fn):
        t=time.perf_counter();cpu=time.process_time();value=fn();rows.append({'stage':label,'seconds':time.perf_counter()-t,'cpu_seconds':time.process_time()-cpu});return value
    def preview(scene,path,label,view='isometric',use_cache=cache):
        prepared,report,hit=timed(label+' stage',lambda:stage(use_cache,scene,{'scene_root':path.parent}))
        image,image_hit=timed(label+' render',lambda:render(use_cache,viewer,prepared,report,view=view,cull=preview_cull(scene)))
        rows[-2]['hit']=hit;rows[-1]['hit']=image_hit;return prepared,image
    for i,path in enumerate(paths):
        scene,hit=timed(f'{i} source cold',lambda:memory.load(path));assert not hit
        scene,hit=timed(f'{i} source warm',lambda:memory.load(path));assert hit
        preview(scene,path,str(i)+' cold');preview(scene,path,str(i)+' warm')
        # A different camera reuses staged arrays, a new process-like cache
        # object reuses persistent artifacts without any memory-cache admission.
        preview(scene,path,str(i)+' camera',view='rear')
        preview(scene,path,str(i)+' persistent',use_cache=PreviewCache(output/'cache'))
        edited=copy.deepcopy(scene);edited['meshes'][0]['positions'][0][0]+=.001
        preview(edited,path,str(i)+' geometry-edit')
    # The source-free tests exercise corruption/cancellation and ensure partial
    # output is never committed. Here also measure a real pre-staging cancel.
    task=Task();task.cancelled.set()
    try:stage(cache,loaded[0],{'scene_root':paths[0].parent},task=task)
    except Cancelled:cancel=True
    else:cancel=False
    if not cancel:raise AssertionError('Cancelled task emitted preview')
    result={'schema':'workshop-performance/1','rows':rows,'cache_stats':cache.stats,'safe_cancel':cancel,
            'scope':'Actual owner-local UVS integrity, prepared MRPV and D3D9 processes on Windows; no D3D8 or entire-installation hash',
            'process_cpu_boundary':'Python CPU only; viewer wall includes process launch, GPU render and capture together'}
    (output/'timings.json').write_bytes(u.canonical(result));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scene',action='append',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run(a.scene,a.viewer,a.output);print(json.dumps(result,indent=2))
