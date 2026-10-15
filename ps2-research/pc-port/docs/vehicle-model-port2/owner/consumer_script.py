"""Generate one identity-filtered debugger stop from this session's packet.
The packet must come from the current paused PORT2_OWNER observation.
"""
import argparse
import hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'vehicle-model-port1'/'frontend-identity'))
from verify_native_bytes import file_offset, SHA


def script(packet,emitter=False):
    if not 0x10000<=packet<=0x7ffffffc or packet%4:
        raise ValueError('Invalid current packet')
    a='00577067' if emitter else '0056BDD4'
    condition=f'[[esp+30]+B0] == {packet:X}' if emitter else f'esi == {packet:X}'
    record=("PORT2_EMITTER tid={x:tid()} vertex_desc={p:[esp+14]} index_desc={p:edi} source_vb={p:[[[esp+14]]]} source_ib={p:[[edi]]} stride={u:[[esp+14]+14]} fvf={x:[[esp+14]+10]} mesh={p:[esp+18]} instance={p:[esp+30]} packet={p:[[esp+30]+B0]} model={p:[[esp+30]+8C]} min_vertex={u:[[esp+14]+8]} vertices={u:[[esp+14]+C]} index_start={u:[edi+8]} indices={u:[edi+C]}" if emitter else "PORT2_CONSUMER tid={x:tid()} packet={p:esi} model={p:ecx} instance={p:[esp]} backref={p:[[esp]+B0]} cached_model={p:[[esp]+8C]}")
    return '\n'.join([
        '// Exact retail one-stop consumer; current packet is session-only.',
        f'bp {a}, "PORT2_same_packet_model_consumer"',
        f'SetBreakpointCondition {a}, "{condition}"',
        f'SetBreakpointFastResume {a}, 1',
        f'SetBreakpointLogCondition {a}, "{condition}"',
        f'SetBreakpointLog {a}, "{record}"',
        f'SetBreakpointCommand {a}, "bpd {a}"',
        f'SetBreakpointCommandCondition {a}, "{condition}"',''])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--packet',type=lambda s:int(s,0),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--emitter',action='store_true')
    a=p.parse_args();data=a.exe.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('Original EXE SHA mismatch')
    address,size,raw=(0x577067,4,'8b442414') if a.emitter else (0x56bdd4,5,'e8f70bfeff')
    off=file_offset(data,address,size)
    if data[off:off+size]!=bytes.fromhex(raw):raise ValueError('Original consumer instruction changed')
    with a.output.open('x',encoding='utf8') as f:f.write(script(a.packet,a.emitter))


if __name__=='__main__':main()
