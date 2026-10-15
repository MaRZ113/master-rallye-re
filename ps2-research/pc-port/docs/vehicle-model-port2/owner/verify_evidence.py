"""Independent original-file windows for current native hierarchy/caller seam."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'vehicle-model-port1'/'frontend-identity'))
from verify_native_bytes import file_offset,SHA,EXE

HERE=Path(__file__).parent


def main():
    data=EXE.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('Original EXE changed')
    checked=[]
    for name in ('group-dispatch-evidence.json','mesh-dispatch-evidence.json'):
        for row in json.loads((HERE/name).read_text())['instructions']:
            address=int(row['address'],16);raw=bytes.fromhex(row['bytes']);offset=file_offset(data,address,len(raw))
            if data[offset:offset+len(raw)]!=raw:raise ValueError('Original instruction bytes differ')
            checked.append(dict(address=hex(address),bytes=raw.hex(),file_offset=offset))
    # Six COM pushes and indirect CALL; return slot is pre-call ESP-28.
    call_window=bytes.fromhex('8b44241452518b500c8b400852506a0456ff931c010000')
    offset=file_offset(data,0x577067,len(call_window))
    if data[offset:offset+len(call_window)]!=call_window:raise ValueError('Caller stack seam changed')
    report=dict(exe_sha256=SHA,instruction_windows=checked,
        native_draw_call_window=dict(address='0x577067',bytes=call_window.hex(),file_offset=offset,return_address='0x57707e',com_push_count=6),
        return_slot_offsets=dict(instance='0x4c',mesh='0x34',vertex_descriptor='0x30',index_descriptor='0x44'),result='PASS')
    (HERE/'native-byte-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(checked),'original instruction windows and native caller stack seam')


if __name__=='__main__':main()
