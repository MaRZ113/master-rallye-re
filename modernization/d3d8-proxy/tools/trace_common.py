"""Bounded JSONL reading and exact-build call-site joins, without game memory."""
import json
import ntpath
from pathlib import Path

TARGET_SHA='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_MAP=ROOT.parent/'renderer-recon/data/d3d8-callmap.json'

def read_jsonl(path):
    if path.stat().st_size>64*1024*1024:raise ValueError('Trace exceeds documented 64 MiB bound')
    records=[]
    with path.open(encoding='utf-8') as f:
        for i,line in enumerate(f,1):
            if len(line)>1024*1024:raise ValueError('Record exceeds 1 MiB')
            if not line.endswith('\n'):raise ValueError(f'Interrupted JSONL at line {i}')
            value=json.loads(line,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('Non-finite JSON')))
            if not isinstance(value,dict):raise ValueError('Record must be an object')
            records.append(value)
            if len(records)>20000:raise ValueError('Too many records')
    return records

def integer(value):
    return int(value,0) if isinstance(value,str) else int(value)

def category(owner):
    # Deliberately narrow: a shared mesh renderer cannot distinguish terrain/car/sky.
    return {0x5641c0:'PARTICLE_BILLBOARD',0x587db0:'STOCK_SHADOW',
            0x56d110:'HUD_OR_UI',0x56c0d0:'HUD_OR_UI',
            0x589b70:'DEBUG',0x58a4f0:'DEBUG'}.get(owner,'UNKNOWN')

def annotate(records, callmap):
    header=next((r for r in records if r.get('type') in ('session','frame_begin')), {})
    known=header.get('exe_sha256')==TARGET_SHA and callmap.get('build_sha256')==TARGET_SHA
    index={}
    if known:
        for call in callmap['calls']:
            if call['interface']=='IDirect3DDevice8':
                index[(integer(call['return_rva']),call['method'])]=call
    result=[]
    for record in records:
        r=dict(record)
        if r.get('type') in ('draw','event'):
            caller=r.get('caller') or {};module=caller.get('module');exe=header.get('exe_path')
            module_match=bool(module and exe and ntpath.normcase(module)==ntpath.normcase(exe))
            call=index.get((integer(caller['return_rva']),r.get('method'))) if known and module_match and caller.get('return_rva') is not None else None
            r['annotation']={'matched':bool(call),'category':'UNKNOWN','evidence_grade':'UNCLASSIFIED',
                             'reason':'unknown build/map' if not known else 'module/RVA/method not matched'}
            if call:
                r['annotation']={'matched':True,'call_va':call['va'],'call_rva':call['rva'],
                    'return_rva':call['return_rva'],'owner_va':call['owner'],'owner_rva':call['owner_rva'],
                    'static_role':call['role'],'usage_scope':call.get('usage_scope'),
                    'category':category(integer(call['owner'])),
                    'evidence_grade':'STATIC_OWNER_MATCH_IN_TRACE',
                    'semantic_confirmation':False,'source':'R-GFX1 d3d8-callmap.json'}
        result.append(r)
    return result

def guarded_output(path):
    out=Path(path).resolve()
    if not out.is_relative_to(ROOT):raise ValueError('Analysis outputs must remain inside d3d8-proxy')
    return out
