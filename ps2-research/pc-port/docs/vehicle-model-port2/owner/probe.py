"""One-shot owner/cache read, only from a current paused debugger observation.

Reuses existing read/query-only Win32 handle and 64KiB cap. No scan, native call,
write, injection, state mutation, or persistent pointer identity.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
from rigid_lifecycle_probe import WindowsReadOnlyProcess, ProbeError, pointer, u32


def sample(memory, ai, egg):
    pointer(ai); pointer(egg)
    if u32(memory, ai) != 0x69020c:
        raise ProbeError('Not current gaFrontendCarMoverAI')
    if u32(memory, 0x69021c) != 0x44c4c0:
        raise ProbeError('Loaded callback differs')
    packet = pointer(u32(memory, egg + 0x50))
    name = u32(memory, packet + 0xc)
    cache = pointer(u32(memory, packet + 0x74))
    # Only fields independently proved by 56BBC0/54C9D0. Model data bytes and
    # arbitrary cache offsets deliberately remain undecoded.
    cache_owner = u32(memory, cache + 0xb0)
    model = pointer(u32(memory, cache + 0x8c))
    model_raw = memory.read(model, 0x1c)
    if (u32(memory, ai) != 0x69020c or u32(memory, egg + 0x50) != packet
            or u32(memory, packet + 0xc) != name
            or u32(memory, packet + 0x74) != cache
            or u32(memory, cache + 0xb0) != cache_owner
            or u32(memory, cache + 0x8c) != model
            or memory.read(model, 0x1c) != model_raw):
        raise ProbeError('Owner/cache changed during one-shot read')
    return dict(status='READ_SNAPSHOT_NOT_ATOMIC', ai=hex(ai), egg=hex(egg),
                packet=hex(packet), name_id=name, cache=hex(cache),
                cache_packet_backref=hex(cache_owner),
                cache_packet_backref_matches=cache_owner == packet,
                compiled_model=hex(model), model_header_u32=list(struct.unpack('<7I',model_raw)),
                model_name_path='UNKNOWN_STRING_ID_RESOLVER',
                draw_resource_join='UNKNOWN_PENDING_CURRENT_CONSUMER',
                replacement_authorized=False)


def model_mesh_membership(memory, model, mesh):
    """Current compiled-model list membership; exact observed X-Trail node types.

    Reject other hierarchy formats rather than recursively guessing layouts.
    Traversal is capped at32 roots/children, total64 nodes, no arbitrary scan.
    """
    pointer(model);pointer(mesh)
    list_object=pointer(u32(memory,model+0x18))
    sentinel=pointer(u32(memory,list_object))
    root=u32(memory,sentinel+4)
    leaves=[];visited=set();headers=[]
    while root:
        pointer(root)
        if root in visited or len(visited)>=64:raise ProbeError('Invalid/capped model hierarchy')
        visited.add(root)
        raw=memory.read(root,12);vt,child,nxt=struct.unpack('<3I',raw)
        if vt!=0x6921b0 or u32(memory,vt+0x30)!=0x578f30:
            raise ProbeError('Unsupported compiled-model group')
        headers.append((root,raw));node=child
        while node:
            pointer(node)
            if node in visited or len(visited)>=64 or len(leaves)>=32:
                raise ProbeError('Invalid/capped compiled mesh list')
            visited.add(node)
            raw=memory.read(node,12);vt,opaque,nxtchild=struct.unpack('<3I',raw)
            if vt!=0x692364 or u32(memory,vt+0x30)!=0x576910:
                raise ProbeError('Unsupported compiled mesh node')
            headers.append((node,raw));leaves.append(node);node=nxtchild
        root=nxt
    if (u32(memory,model+0x18)!=list_object or u32(memory,list_object)!=sentinel
            or any(memory.read(address,12)!=raw for address,raw in headers)):
        raise ProbeError('Model hierarchy changed during read')
    return dict(source_mesh_in_model=mesh in leaves, leaf_count=len(leaves),
                leaf_addresses=[hex(x) for x in leaves], replacement_authorized=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pid',type=int,required=True)
    p.add_argument('--ai',type=lambda s:int(s,0),required=True)
    p.add_argument('--egg',type=lambda s:int(s,0),required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    mem=WindowsReadOnlyProcess(a.pid)
    try:
        report=dict(process=mem.identity, observation=sample(mem,a.ai,a.egg))
        report['bytes_read']=mem.bytes_read
        with a.output.open('x',encoding='utf8') as f:
            json.dump(report,f,indent=2);f.write('\n')
        print(json.dumps(report,indent=2))
    finally:
        mem.close()


if __name__=='__main__':main()
