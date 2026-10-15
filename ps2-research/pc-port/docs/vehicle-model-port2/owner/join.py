"""Compact exact same-session native-owner/upload join, no live reads."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).parent
LOGS=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')


def main():
    owner=json.loads((HERE/'current-owner-53228.json').read_text())
    bind=json.loads((HERE/'port2-current-bind-53228.json').read_text())
    tree=json.loads((HERE/'port2-current-model-children-53228.json').read_text())
    uploads=json.loads((HERE/'current-upload-53228.json').read_text())
    assert owner['process']['process_creation_filetime']==bind['process']['process_creation_filetime']==tree['process']['process_creation_filetime']
    assert owner['observation']['packet']==bind['packet']==tree['packet']
    assert owner['observation']['compiled_model']==bind['model']==tree['model']
    assert tree['source_mesh_in_dispatch_list'] and not tree['truncated'] and len(tree['children'])==24
    frames=[]
    for frame in uploads['frames']:
        path=LOGS/f'frame-53228-d1-{frame:08d}.jsonl'
        records=[json.loads(line) for line in path.read_text().splitlines()]
        draws=[r for r in records if r.get('type')=='draw' and r.get('arguments',[])[:5]==[4,20739,286,33312,213]]
        assert len(draws)==1
        d=draws[0]
        current=[r for r in uploads['records'] if r['frame']==frame]
        assert len(current)==24 and {r['source_record_metadata_index'] for r in current}==set(range(24))
        first=[r for r in current if (r['vertices'],r['triangles'],r['min_index'],r['start_index'])==(286,213,20739,33312)]
        assert len(first)==1 and first[0]['source_record_metadata_index']==0
        assert all(r['world_view_projection_current'] and r['matrix_hresults']==[0,0,0] for r in current)
        frames.append(dict(frame=frame,capture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            source_record=first[0],native_draw_arguments=d['arguments'][:5],native_draw_hresult=d['result'],
            caller_rva=d['caller']['return_rva'],stream=d['state']['streams'][0],indices=d['state']['indices'],
            source_records=24,source_triangles=sum(r['triangles'] for r in current)))
    assert frames[0]['source_triangles']==frames[1]['source_triangles']==2487
    result=dict(schema=1,phase='PORT2_CURRENT_OWNER_UPLOAD_JOIN',process=owner['process'],
        native_owner_chain='Current CarMover callback -> Egg+50 -> packet+74 -> instance+B0/+8C -> compiled model dispatch list -> actual emitter source mesh',
        native_source_draw_join='CONFIRMED_CURRENT_PAUSED_RUNTIME',frames=frames,
        proxy_to_native_pointer_bridge='Existing Device8.unwrap_vertex_buffer/unwrap_index_buffer required at runtime; source proxy pointers differ from F10 native pointers',
        persistent_pointer_authority=False,string_id_path='UNKNOWN_RESOLVER',
        model_replacement_runtime='NOT_IMPLEMENTED_BY_THIS_AUDIT')
    (HERE/'current-join.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS current owner/source draw and24/24 upload records in both frames')


if __name__=='__main__':main()
