"""Frontend resource complexity and existing renderer upload-event diagnostics.

Python timings describe this offline reader, never native cold/warm timings.
"""
import argparse,collections,hashlib,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes


def analyze_model(path):
    start=time.perf_counter_ns();raw=path.read_bytes();read_ms=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();model=parse_dx_bytes(raw);parse_ms=(time.perf_counter_ns()-start)/1e6
    stems=sorted({s for d in model.physical_draws for s in d.texture_tuple if s!='Null'})
    textures=[];duplicate=collections.defaultdict(list)
    for stem in stems:
        if Path(stem).name!=stem or '/' in stem or '\\' in stem:raise ValueError('frontend textures must be family-local')
        texture_path=path.parent/(stem+'.dxt');start=time.perf_counter_ns();data=texture_path.read_bytes();io=(time.perf_counter_ns()-start)/1e6
        start=time.perf_counter_ns();texture=parse_dxt_bytes(data);decode=(time.perf_counter_ns()-start)/1e6;digest=hashlib.sha256(data).hexdigest();duplicate[digest].append(stem)
        textures.append({'stem':stem,'width':texture.width,'height':texture.height,'bytes':len(data),'native_source_charge_bytes':texture.width*texture.height*4,'sha256':digest,'offline_read_ms':io,'offline_parse_ms':decode})
    return {'model':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'vertices':model.vertex_count,'physical_draws':len(model.physical_draws),'unique_textures':len(stems),
        'native_source_charge_bytes':sum(t['native_source_charge_bytes'] for t in textures),'lossless_duplicate_groups':[v for v in duplicate.values() if len(v)>1],
        'offline_model_read_ms':read_ms,'offline_model_parse_ms':parse_ms,'textures':textures,
        'boundary':'measured Python file reads/parser on current OS cache; not original native DX/DXT decode, GPU upload, cold disk, cache lifecycle or gameplay time'}


def analyze_renderer_log(path):
    events=collections.Counter();frames={};session=None;malformed=0
    with path.open(encoding='utf-8') as source:
        for line in source:
            try:row=json.loads(line)
            except ValueError:malformed+=1;continue
            events[row.get('type')]+=1
            if row.get('type')=='session':session=row
            if row.get('type')!='resource_create':continue
            frame=row.get('frame');entry=frames.setdefault(frame,{'frame':frame,'methods':collections.Counter(),'texture_source_bytes':0,'creation_callers':collections.Counter()});entry['methods'][row.get('method')]+=1
            entry['creation_callers'][hex(row.get('creation_caller',{}).get('address',0))]+=1
            args=row.get('arguments',[])
            if row.get('method')=='CreateTexture' and len(args)>=2:entry['texture_source_bytes']+=args[0]*args[1]*4
    ordered=sorted(frames.values(),key=lambda r:r['frame'])
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'session':session,'events':dict(events),'malformed_lines':malformed,'resource_frames':ordered,
        'peak_texture_creation_frames':sorted(ordered,key=lambda r:r['methods'].get('CreateTexture',0),reverse=True)[:20],
        'boundary':'existing successful resource creation events only; no elapsed-stage time, resource destruction, vehicle identity or cache hit/miss proof'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',type=Path,action='append',default=[]);p.add_argument('--renderer-log',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result={'models':[analyze_model(path) for path in a.model]}
    if a.renderer_log:result['renderer_log']=analyze_renderer_log(a.renderer_log)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ('model','vertices','physical_draws','unique_textures','native_source_charge_bytes')} for r in result['models']],indent=2))
