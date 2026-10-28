"""Bounded representative source qualification, distinct from playable imports."""
import collections,json
from pathlib import Path
from .gt3_vehicle import digest
from .gt3_source import inspect_car
from .addon_sdk.gt3_scene import reconstruct
from .addon_sdk.texture_budget import texture_working_set,require_vehicle_budget
from .dx import parse_dx_bytes

def qualify(case):
    if set(case)-{'name','source','engine_sha256','model','lod','colour','callbacks','candidate','captures'}:raise ValueError('Unknown qualification case field')
    path=Path(case['source']);report={'name':case['name'],'source':str(path.resolve()),'L0':'NOT TESTED','L1':'NOT TESTED','L2':'NOT TESTED','owner_gameplay':'NOT TESTED','issues':[]}
    if not path.is_file():return {**report,'L0':'MISSING INPUT','issues':['source_missing']}
    if not 0<path.stat().st_size<=16*1024*1024:raise ValueError('Source qualification file budget')
    raw=path.read_bytes();report['source_sha256']=digest(raw)
    try:
        structure=inspect_car(raw);report['L0']='PASS'
        scene=reconstruct(raw,engine_sha256=case['engine_sha256'],model_index=case.get('model',0),lod=case.get('lod',0),colour=case.get('colour',0),callbacks=case.get('callbacks',{'0':0,'7':0}),strict_textures=False)
        counts=collections.Counter(issue for d in scene['draws']for issue in d['issues'])
        report['source_geometry']=scene['report'];report['source_issue_counts']=dict(counts)
        report['source_texture_records']=sum(t['textures']for t in structure['body']['texture_sets'])
        report['issues']=['source_palette_unsupported'if issue.startswith('unsupported source texture')else 'source_render_effect_untranslated'for issue in counts]
        report['L1']='UNSUPPORTED'if any(k.startswith('unsupported source texture')for k in counts)else'NOT TESTED'
        report['conversion_boundary']='Selected source geometry decoded, including explicit unsupported material records. No full MR conversion is inferred from source coverage.'
    except (ValueError,IndexError)as e:
        report['L1']='UNSUPPORTED';report['reason']=str(e);report['issues'].append('source_decode_or_state_unsupported');return report
    if case.get('candidate'):
        root=Path(case['candidate']);build=json.loads((root/'conversion-report.json').read_text())
        if build['profile']['source_sha256']!=report['source_sha256']or build['colourway']['source_index']!=case.get('colour',0):raise ValueError('Qualification candidate/source selection mismatch')
        assets=root/'assets'
        for name,record in build['outputs'].items():
            data=(assets/name).read_bytes()
            if digest(data)!=record['sha256']or not parse_dx_bytes(data).diagnostics.validated:raise ValueError('Qualification candidate changed: '+name)
        budget=require_vehicle_budget(texture_working_set(assets))
        report['L1']='WARN';report['mr_outputs']=build['outputs'];report['texture_budget']=budget['cache_bytes']
        report['conversion_boundary']='PASS structural DX/DXT resources with explicit lighting/effect/assembly approximations; WARN source semantics/rig not fully reconstructed. No gameplay claim.'
    captures=[]
    for name in case.get('captures',[]):
        p=Path(name)
        if not p.is_file()or p.stat().st_size>32*1024*1024:raise ValueError('Missing/oversized L2 capture')
        captures.append({'path':str(p.resolve()),'sha256':digest(p.read_bytes())})
    if captures:report['L2']='CAPTURED';report['captures']=captures;report['visual_boundary']='Fixed D3D9 inspection artifacts available; successful capture alone is not visual acceptance or PS2/D3D8 parity.'
    report['issues']=sorted(set(report['issues']));return report

def batch(cases):
    if not isinstance(cases,list)or not 0<len(cases)<=64:raise ValueError('Qualification batch must contain 1..64 explicit cases')
    reports=[qualify(c)for c in cases];groups=collections.defaultdict(list)
    for r in reports:
        for issue in r['issues']:groups[issue].append(r['name'])
    return {'schema':'gt-garage-qualification/1','cases':reports,'issue_clusters':dict(groups),'boundary':'Selected representative source/structural evidence only. L0, L1, D3D9 capture and owner gameplay remain independent.'}
