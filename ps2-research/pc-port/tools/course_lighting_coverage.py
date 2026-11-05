"""Join opt-in A/B admission ledger to real successful F10 draws; pixel diff is secondary."""
from pathlib import Path
import argparse,collections,html,json,struct,zlib

def read_jsonl(path,limit=128*1024*1024):
    if path.stat().st_size>limit:raise ValueError('diagnostic file exceeds limit')
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def draw_key(row):
    s=row['state'];args=row['arguments'];vb=s['streams'][0] or {};ib=s['indices'] or {}
    return (args[1],args[2],args[3],args[4],s['vertex_shader'],vb.get('last_creation_serial',0),ib.get('last_creation_serial',0))

def ledger_key(row):return tuple(row[k] for k in ['min_index','vertices','start_index','triangles','fvf','vertex_generation','index_generation'])

def join_admissions(admissions,trace):
    by_key=collections.defaultdict(collections.deque)
    for r in trace:
        if r.get('type')=='draw' and r.get('method')=='DrawIndexedPrimitive' and r.get('caller',{}).get('return_rva')==0x17707e:by_key[draw_key(r)].append(r)
    result=[]
    for row in admissions:
        candidates=by_key[ledger_key(row)];draw=candidates.popleft() if candidates else None
        verdict='Unconfirmed' if draw is None else 'Draw failed' if draw['result']!=0 else 'Lit' if row['admission']=='Lit candidate' else row['admission']
        result.append(dict(row,runtime_verdict=verdict,draw_hresult=draw['result'] if draw else None))
    return result

def rgb_png(path):
    data=path.read_bytes()
    if len(data)>64*1024*1024:raise ValueError('PNG file limit')
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('not PNG')
    at=8;payload=b'';w=h=0
    while at<len(data):
        n=struct.unpack_from('>I',data,at)[0];kind=data[at+4:at+8];body=data[at+8:at+8+n]
        if len(body)!=n or zlib.crc32(kind+body)&0xffffffff!=struct.unpack_from('>I',data,at+8+n)[0]:raise ValueError('PNG chunk integrity')
        if kind==b'IHDR':
            w,h,depth,color,compression,filter_method,interlace=struct.unpack('>IIBBBBB',body)
            if depth!=8 or color!=2 or interlace or not 0<w*h<=4194304:raise ValueError('expected bounded native RGB8 capture')
        if kind==b'IDAT':payload+=body
        at+=12+n
        if kind==b'IEND':break
    expected=h*(1+w*3);decoder=zlib.decompressobj();raw=decoder.decompress(payload,expected+1)
    if len(raw)!=expected or not decoder.eof:raise ValueError('PNG decompression size')
    rows=[]
    for y in range(h):
        row=raw[y*(1+w*3):(y+1)*(1+w*3)]
        if row[0]!=0:raise ValueError('expected native filter-0 diagnostic PNG')
        rows.append(row[1:])
    return w,h,b''.join(rows)

def write_rgb(path,w,h,rgb):
    def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
    raw=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))

def analyze(pair_dir,logs,output,batch=None):
    if output.exists():raise ValueError('fresh output required')
    output.mkdir(parents=True);pair=json.loads((pair_dir/'pair.json').read_text());result={'status':'UNCONFIRMED','pixel_diff_is_secondary':True,'pair':pair,'draws':[],'materials':[]}
    try:
        if pair['status']!='CAPTURED_MATCHED_CAMERA_RUNTIME_TRACE_JOIN_REQUIRED' or pair.get('camera_equal_by_bits') is not True:raise ValueError('pair incomplete or aborted')
        ledger=read_jsonl(pair_dir/'admissions.jsonl',32*1024*1024)
        cameras=[]
        for label in ['lit','native']:
            frame=pair[label+'_frame'];trace=read_jsonl(logs/f"frame-{pair['pid']}-d{pair['device']}-{frame:08}.jsonl")
            begin=next(r for r in trace if r['type']=='frame_begin');end=next(r for r in trace if r['type']=='frame_end');summary=next(r for r in trace if r['type']=='frame_summary')
            if not end.get('complete') or end.get('truncated') or not summary.get('complete_interval') or summary.get('present_hresult')!=0:raise ValueError('incomplete or failed F10 interval')
            if begin['proxy_sha256']!=pair.get('proxy_sha256'):raise ValueError('pair/F10 DLL identity missing or mismatched')
            states={tuple(r['state']['matrices']['2']['bits']+r['state']['matrices']['3']['bits']) for r in trace if r.get('type')=='draw' and r.get('caller',{}).get('return_rva')==0x17707e and r['state']['vertex_shader'] in [0x142,0x242,0x152] and r['state']['render_states'].get('7')==1 and r['state']['render_states'].get('28')==1}
            cameras.append(states)
            result['draws']+=join_admissions([r for r in ledger if r['frame']==frame],trace)
        if not cameras[0] or cameras[0]!=cameras[1]:raise ValueError('F10 camera/projection changed')
        result['status']='RUNTIME_DRAW_TRACE_JOINED_NOT_OWNER_ACCEPTANCE'
    except (OSError,ValueError,KeyError,StopIteration,json.JSONDecodeError) as e:
        result['error']=str(e)
        for row in result['draws']:row['candidate_verdict']=row['runtime_verdict'];row['runtime_verdict']='Unconfirmed'
    grouped=collections.defaultdict(list)
    for row in result['draws']:grouped[(row['material'],row['texture_sha256'])].append(row)
    for (name,texture),rows in sorted(grouped.items()):result['materials'].append({'material':name,'texture_sha256':texture,'verdicts':dict(collections.Counter(r['runtime_verdict'] for r in rows)),'draw_count':len(rows)})
    try:
        w,h,a=rgb_png(pair_dir/'lit.png');bw,bh,b=rgb_png(pair_dir/'native.png')
        if (w,h)!=(bw,bh):raise ValueError('image dimensions changed')
        delta=bytes(min(255,abs(x-y)*4) for x,y in zip(a,b));write_rgb(output/'difference.png',w,h,delta)
        result['pixel_diff']={'status':'SECONDARY_DYNAMIC_LAYERS_MAY_DIFFER','mean_absolute_rgb_delta':sum(abs(x-y) for x,y in zip(a,b))/len(a),'width':w,'height':h}
    except (OSError,ValueError,struct.error,zlib.error) as e:result['pixel_diff']={'status':'UNAVAILABLE','reason':str(e)}
    if batch:
        candidates=list((batch/'reports').glob('*/report.json'))
        course=str(pair.get('course','')).casefold().removeprefix('racetest/')
        folders=[course]
        scene_manifest=batch/'scene-bindings.json'
        if scene_manifest.is_file():
            binding=next((b for b in json.loads(scene_manifest.read_text())['bindings'] if b['scene'].casefold()==course),None)
            if binding:folders=[f.casefold() for f in binding['folders']]
        for source in candidates:
            if source.parent.name.casefold() not in folders:continue
            inventory=json.loads(source.read_text(encoding='utf-8'))
            for row in result['materials']:
                material=next((m for m in inventory['materials'] if row['texture_sha256'] in m.get('texture_identities',[])),None)
                if material and material.get('thumbnail'):
                    src=source.parent/material['thumbnail'];target=output/'textures'/src.name
                    target.parent.mkdir(exist_ok=True);target.write_bytes(src.read_bytes());row['thumbnail']='textures/'+src.name
    result['counts']=dict(collections.Counter(r['runtime_verdict'] for r in result['draws']))
    (output/'coverage.json').write_text(json.dumps(result,indent=2)+'\n')
    # A material coverage map, not a falsely attributed pixel mask.
    cells=[]
    for n,row in enumerate(result['materials']):
        verdicts=row['verdicts'];color='#4b9' if verdicts.get('Lit') else '#778' if verdicts.get('Excluded') else '#c85'
        x=(n%4)*280;y=(n//4)*65;label=html.escape((row['material'] or '(unknown)')[:34]);counts=html.escape(str(verdicts))
        cells.append(f'<g><rect x="{x}" y="{y}" width="272" height="58" fill="{color}"/><text x="{x+6}" y="{y+20}">{label}</text><title>{label}: {counts}</title></g>')
    (output/'coverage.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{max(65,((len(cells)+3)//4)*65)}" font-family="sans-serif" font-size="13">'+''.join(cells)+'</svg>')
    rows=''.join('<tr><td>'+('<img width=64 src="'+r['thumbnail']+'">' if r.get('thumbnail') else 'MISSING')+'</td><td>'+html.escape(r['material'] or '(unknown)')+'</td><td>'+html.escape(str(r['verdicts']))+'</td></tr>' for r in result['materials'])
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><h1>Runtime course coverage</h1><p>'+html.escape(result['status'])+'</p><p>'+html.escape(result.get('error',''))+'</p><p>Draw-call ledger is ground truth. Difference image is secondary; water, grass and reflections can animate.</p><img src="coverage.svg"><table>'+rows+'</table><h2>Difference ×4</h2><img width="960" src="difference.png">',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pair',type=Path,required=True);p.add_argument('--logs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--batch',type=Path);a=p.parse_args();r=analyze(a.pair,a.logs,a.output,a.batch);print(r['status'],r['counts'])
