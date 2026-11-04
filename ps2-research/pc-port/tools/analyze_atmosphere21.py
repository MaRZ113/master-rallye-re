"""Read-only exact-DLL runtime evidence for Universal Scene Lighting.

Counts cached draw ranges and submissions, not independently owned game objects.
Does not upgrade offline or incomplete-capture evidence into a runtime pass.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import mean,median

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def analyze(logs,dll):
    sessions=[];pids=set()
    for path in sorted(logs.glob('session-*.jsonl')):
        text=path.read_text(encoding='utf-8')
        if dll not in text:continue
        rows=[json.loads(line) for line in text.splitlines()]
        found=next((r.get('proxy_sha256') for r in rows if r.get('proxy_sha256')),None)
        if found!=dll:continue
        pids.add(path.stem.split('-')[-1])
        config=next((r for r in rows if r.get('type')=='atmosphere_config'),{})
        draws=[r for r in rows if r.get('type')=='atmosphere_resolver_draw']
        cpu=[r for r in rows if r.get('type')=='atmosphere_cpu_window']
        ranges=[r for r in rows if r.get('type')=='atmosphere_resolver_window']
        courses=[]
        for race in sorted({r['race_generation'] for r in draws}):
            current=[r for r in draws if r['race_generation']==race];first=min(r['frame'] for r in current)
            stop=min([r['frame'] for r in rows if r.get('type')=='atmosphere_admission_rejected' and r.get('reason')=='single_camera_race_certificate_missing' and r.get('race_generation')!=race and r['frame']>first]+[10**15])
            windows=[w for w in cpu if w['frame']-w['frames']>=first and w['frame']<stop]
            values=[w['cpu_ms']/w['frames'] for w in windows]
            cached=[w for w in ranges if w['race_generation']==race and first<=w['frame']<stop]
            courses.append({'course':current[0]['course'],'race_generation':race,'owner_lifetimes':sorted({r['owner_lifetime'] for r in current}),
                            'observed_categories':sorted({r['category'] for r in current}),'first_material_events':current,
                            'complete_cpu_windows':len(values),'cpu_ms_per_frame_mean':mean(values) if values else None,'cpu_ms_per_frame_median':median(values) if values else None,
                            'last_cache_window':cached[-1] if cached else None})
        sessions.append({'file':path.name,'sha256':digest(path),'config':config,'universal_resolver_enabled':config.get('scene_resolver')=='Universal','course_lifetimes':courses,
                         'metadata':[r for r in rows if r.get('type')=='atmosphere_resolver_metadata'],
                         'sky':[r for r in rows if r.get('type')=='atmosphere_custom_sky_draw'],
                         'body_prototype':[r for r in rows if r.get('type')=='atmosphere_body_prototype'],
                         'rejections':[r for r in rows if r.get('type')=='atmosphere_admission_rejected'],
                         'ps2_mode':[r for r in rows if r.get('type')=='ps2_port_mode_selected'],
                         'all_window_cpu_ms_per_frame':sum(w['cpu_ms'] for w in cpu)/sum(w['frames'] for w in cpu) if cpu else None})
    captures=[]
    for pid in sorted(pids):
        for path in sorted(logs.glob(f'frame-{pid}-*.jsonl')):
            rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
            begin=next((r for r in rows if r.get('type')=='frame_begin'),{})
            if begin.get('proxy_sha256')!=dll:continue
            end=next((r for r in rows if r.get('type')=='frame_end'),{})
            epoch=next((r for r in rows if r.get('type')=='race_epoch_snapshot'),{})
            overrides=[r for r in rows if r.get('type')=='native_override']
            fog=Counter(hex(r['arguments'][1]) for r in overrides if r.get('slot')==50 and r['arguments'][0]==34 and not r.get('result',0)&0x80000000)
            captures.append({'file':path.name,'sha256':digest(path),'scene':epoch.get('root_job_success',{}).get('scene'),
                             'race_generation':epoch.get('race_lifecycle_generation'),'frame_end':end,
                             'complete':bool(end.get('complete') and not end.get('truncated') and not end.get('dropped_records')),
                             'fog_override_values':dict(fog),'failed_native_writes':sum(bool(r.get('result',0)&0x80000000) for r in overrides),
                             'draw_methods':dict(Counter(r.get('method') for r in rows if r.get('type')=='draw'))})
    return {'schema':1,'evidence':'EXACT_DLL_RUNTIME_LOGS_ONLY','dll_sha256':dll,'session_count':len(sessions),'sessions':sessions,'captures':captures,
            'limits':['Cached ranges / draws are counted; not unique game actors.','QPC hook CPU is not FPS or GPU time.','Only complete windows inside an admitted course lifetime are used for course CPU.','PS2 effect compatibility and visual quality require separate A/B inspection.','No evidence for a case absent from these logs.']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--logs',type=Path,required=True);ap.add_argument('--dll-sha256',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if len(a.dll_sha256)!=64:raise ValueError('exact DLL SHA required')
    report=analyze(a.logs,a.dll_sha256);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"{report['session_count']} exact-DLL sessions, {len(report['captures'])} captures: {a.output}")

if __name__=='__main__':main()
