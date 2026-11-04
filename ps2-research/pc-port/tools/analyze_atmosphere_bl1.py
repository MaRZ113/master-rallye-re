"""Read session/F10 JSONL without repairing or hiding malformed input lines."""
from pathlib import Path
import argparse
import collections
import hashlib
import json

def records(path,bad):
    for line,text in enumerate(path.read_text(encoding='utf-8-sig').splitlines(),1):
        try:r=json.loads(text)
        except json.JSONDecodeError as e:
            bad.append({'line':line,'column':e.colno,'error':e.msg});continue
        yield line,r

def analyze(root):
    result={'schema':1,'evidence':'RECORDED_JSONL_NOT_SCREENSHOT_ACCEPTANCE','source':str(root.resolve()),'sessions':[],'captures':[]}
    for path in sorted(root.glob('session-*.jsonl')):
        bad=[];events=[];resources=[];summary=0;types=collections.Counter()
        for line,r in records(path,bad):
            kind=r.get('type');types[kind]+=1
            if kind=='frame_summary':summary=r.get('frame',summary)
            if kind and kind.startswith('atmosphere'):
                events.append({'line':line,'preceding_summary_frame':summary,'record':r})
            if kind=='resource_create' and r.get('method')=='CreateTexture' and r.get('arguments',[0,0])[:2]==[256,256]:
                resources.append({'line':line,'frame':r['frame'],'serial':r['serial'],'format':r['arguments'][4]})
        result['sessions'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'invalid_json':bad,'record_types':dict(types),
            'atmosphere_events':events,'textures_256':resources})
    for path in sorted(root.glob('frame-*.jsonl')):
        bad=[];skies=[];fog=set();epoch=None;end=None
        for _,r in records(path,bad):
            kind=r.get('type')
            if kind=='race_epoch_snapshot':epoch={k:r.get(k) for k in ('race_lifecycle_generation','root_job_success','context','live_certificate_valid')}
            if kind=='frame_end':end=r
            if kind!='draw':continue
            a=r.get('arguments',[]);s=r.get('state',{});rs=s.get('render_states',{})
            if len(a)>=5 and s.get('vertex_shader')==0x102 and (a[2],a[4]) in ((134,196),(114,180)):
                skies.append({'vertices':a[2],'triangles':a[4],'texture':s.get('textures',[None])[0]})
            if rs.get('28')==1 and isinstance(rs.get('34'),int):fog.add(rs['34'])
        result['captures'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'invalid_json':bad,
            'sky_draws':skies,'world_fog_colors':[f'0x{x:08X}' for x in sorted(fog)],'lifecycle':epoch,'end':end})
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--logs',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.logs.resolve()==a.output.resolve() or a.logs.resolve() in a.output.resolve().parents:raise ValueError('keep output outside original logs')
    data=analyze(a.logs);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(f'{len(data["sessions"])} sessions, {len(data["captures"])} captures; malformed lines reported explicitly; {a.output}')
if __name__=='__main__':main()
