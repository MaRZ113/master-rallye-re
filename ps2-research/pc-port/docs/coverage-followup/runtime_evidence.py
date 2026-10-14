"""Compact bounded existing capture evidence, never full buffers or screenshots."""
import collections
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).parent
LOGS=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')


def main():
    source=LOGS/'session-20261014-024049-10348.jsonl'
    types=collections.Counter();malformed=0;selected=[];buffers=[]
    for line in source.open(errors='replace'):
        try:row=json.loads(line)
        except json.JSONDecodeError:malformed+=1;continue
        types[row.get('type')]+=1
        if row.get('type')=='reset_policy':
            selected.append({k:row.get(k) for k in ('type','native_reset_called','result','completed_race_proof_preserved','requested','effective')})
        if row.get('type')=='ps2_reflection_material':
            selected.append({k:row.get(k) for k in ('type','frame','vehicle','identity_reason','identity_authority','override_applied','geometry_sha256','native_draw_hresult','restore_hresult')})
        if row.get('type')=='resource_create' and row.get('method') in ('CreateVertexBuffer','CreateIndexBuffer'):
            buffers.append({k:row.get(k) for k in ('method','frame','serial','pool')})
    result={
        'schema_version':1,'session':source.name,'session_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'proxy_sha256':'abf005f8ff2f9535a2abb644e2066a224fc389734dc5f36fbdec5694ff37f48a',
        'records':selected,'buffer_pool_counts':dict(collections.Counter(str(b.get('pool')) for b in buffers)),
        'buffer_sources':buffers,'malformed_records_not_interpreted':malformed,
        'evidence_boundary':'Pre-fix logs plus USER_RUNTIME_OBSERVATION. No post-fix Reset runtime captured.',
        'user_accepted_coverage_fix':['Tata','Navara','Patrol','Kamaz','IceCream','Ufo','Jump'],
        'user_remaining_visual_failures':['SeatBuggy','Bruno','Forester (PS2 WOOLDAND)','LandCruiser','ChevyBlazer','Xtrail'],
        'user_reset_failure':'Reflection disappears after window reset and does not return.',
        'source_cause':'Successful Reset invalidates every CPU mirror; actual managed buffers survive. Source-provable defect, live first failing gate not independently logged.',
    }
    (HERE/'runtime-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Original records summarized:',len(selected),'buffers:',len(buffers),'malformed:',malformed)


if __name__=='__main__':main()
