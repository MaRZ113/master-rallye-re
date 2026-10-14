"""Bounded existing-log check; counts are candidate filters, never identities."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = Path(r'D:/Game/Master Rallye Pristine/MRRRenderer/logs')


def main():
    source = json.loads((HERE/'partition-evidence.json').read_text())
    targets = {(d['index_count']//3,d['vertex_count']): (v['pc_family'],d)
               for v in source['vehicles'] for d in v['draws']}
    hashes = {d['geometry_sha256']:(v['pc_family'],d['draw_index'])
              for v in source['vehicles'] for d in v['draws']}
    files = sorted([p for p in LOGS.iterdir() if p.name.startswith('frame-10348-')])
    sessions = sorted([p for p in LOGS.iterdir() if p.name.startswith('session-20261014-') and p.stat().st_size],
                      key=lambda p:p.stat().st_mtime, reverse=True)[:3]
    report = {'schema_version':1,'log_root_role':'USER_RUNTIME_CAPTURE_REFERENCE_ONLY',
              'bounded_files':[p.name for p in files+sessions], 'input_files':[],
              'exact_current_hash_events':[], 'layout_only_candidates':[],
              'invalid_json_line_counts':{},
              'limitation':'No numerical VB/IB ID, draw ordinal or primitive/vertex count is an admission identity.'}
    for path in files+sessions:
        snapshot=path.read_bytes();digest=hashlib.sha256(snapshot).hexdigest(); invalid=0
        report['input_files'].append({'name':path.name,'size':len(snapshot),'sha256':digest})
        for line in snapshot.decode('utf8').splitlines():
            try: row=json.loads(line)
            except ValueError:invalid+=1;continue
            exact=row.get('geometry_sha256') or (row.get('foliage') or {}).get('geometry_multiset_sha256')
            if exact in hashes:
                report['exact_current_hash_events'].append({'file':path.name,'vehicle':hashes[exact][0],
                    'source_record':hashes[exact][1],'geometry_sha256':exact,'frame':row.get('frame'),
                    'type':row.get('type'),'reason':row.get('reason'),'override_applied':row.get('override_applied')})
            args=row.get('arguments',[])
            if row.get('type')!='draw' or row.get('method')!='DrawIndexedPrimitive' or len(args)<5:continue
            key=(args[4],args[2])
            if key not in targets:continue
            family, d=targets[key]
            state=row.get('state') or {}
            effective=row.get('effective_state') or {}
            stages=state.get('texture_stage_states') or []
            relevant_stages=[{k:stage.get(k) for k in ('1','2','3','4','5','6','11','24')}
                             for stage in stages[:2]]
            streams=state.get('streams') or []
            report['layout_only_candidates'].append({'file':path.name,'frame':row.get('frame'),
                'candidate_family':family,'candidate_record':d['draw_index'],
                'native_arguments':args[:5],'result':row.get('result'),'caller':row.get('caller'),
                'draw_sequence_for_capture_only':row.get('draw_index'), 'race_context':row.get('race_context'),
                'fvf':state.get('vertex_shader'),'stream0':streams[0] if streams else None,'indices':state.get('indices'),
                'logical_texture_stage_states':relevant_stages,'effective_state_overrides':effective,
                'classification':'LAYOUT_ONLY_NOT_GEOMETRY_IDENTITY'})
        if invalid:report['invalid_json_line_counts'][path.name]=invalid
    (HERE/'runtime-evidence.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf8')
    print(json.dumps({'files_scanned':len(files+sessions),'exact_events':len(report['exact_current_hash_events']),
                      'layout_candidates':len(report['layout_only_candidates']),
                      'layouts':dict(Counter(str(r['fvf']) for r in report['layout_only_candidates']))}))


if __name__=='__main__':main()
