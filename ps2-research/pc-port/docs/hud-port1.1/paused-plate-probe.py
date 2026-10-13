"""One bounded RPM collection at an explicit user-held x32dbg pause.
Register values must be copied from the CURRENT paused debugger. This tool
does not attach a debugger, stop threads, call engine APIs or alter memory.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import struct

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
native = module('readonly_native', ROOT / 'tools/rigid_lifecycle_probe.py')
contract = module('plate_contract', HERE / 'plate-contract.py')

def collect(memory, registers):
    read = memory.read
    u32 = lambda p: struct.unpack('<I', read(p,4))[0]
    esp = registers['esp']
    if registers['eip'] != contract.CHECKPOINT:
        raise ValueError('exact paused checkpoint required')
    if read(contract.CHECKPOINT,3) != bytes.fromhex('8d4e20'):
        raise ValueError('loaded original instruction mismatch')
    owner, packet = u32(esp+0x11C), u32(esp+0x14)
    ai = u32(owner+4)
    if u32(owner+0x4C) != packet or u32(ai) != contract.SPEED_DIAL_VTABLE:
        raise ValueError('current original owner/class mismatch')
    before = read(owner+4,16) + read(owner+0x4C,4) + read(packet+8,8)
    rows_begin, rows_end = struct.unpack('<II', read(packet+8,8))
    if contract.bounded_span(rows_begin,rows_end,0x38,1) != 1:
        raise ValueError('one original plate row required')
    row = read(rows_begin,0x38)
    row_xyz = struct.unpack_from('<3f',row,0x14)
    if not all(math.isfinite(v) for v in row_xyz):
        raise ValueError('non-finite original row placement')
    keys_begin,keys_end = struct.unpack_from('<II',row,4)
    key_count = contract.bounded_span(keys_begin,keys_end,2,1)
    keys = list(struct.unpack('<'+'H'*key_count,read(keys_begin,2*key_count)))
    bank, subimage = u32(esp+0x1C),u32(esp+0x44)
    bank_before = read(bank+4,0x14)
    bank_begin,bank_end = struct.unpack_from('<II',bank_before)
    head = u32(bank+0x14)
    node = u32(head+4)
    nil = u32(0x6F6478)
    visited = set(); selected = None
    for _ in range(32):
        if node in (head,nil): break
        if node in visited: raise ValueError('cyclic original bank key tree')
        visited.add(node)
        data = read(node,0x10)
        key,index = struct.unpack_from('<hh',data,0xC)
        if key == 0: selected = index; break
        node = struct.unpack_from('<I',data,0 if key>0 else 8)[0]
    if selected is None: raise ValueError('image key0 not found in current bank')
    image = read(subimage,0x10)
    tri_begin,tri_end = struct.unpack_from('<II',image,4)
    status = contract.qualify(registers,owner,packet,u32(ai),keys,selected,
                              subimage,bank_begin,bank_end,tri_begin,tri_end)
    count = contract.bounded_span(tri_begin,tri_end,0x34,2)
    if count != 2: raise ValueError('expected complete two-triangle original plate')
    raw = read(tri_begin,0x34*count)
    triangles = [contract.decode_triangle(raw[i*0x34:(i+1)*0x34]) for i in range(count)]
    texture_wrapper = registers['eax']
    native_texture = u32(texture_wrapper)
    after = read(owner+4,16) + read(owner+0x4C,4) + read(packet+8,8)
    if (before != after or bank_before != read(bank+4,0x14)
            or raw != read(tri_begin,len(raw)) or row != read(rows_begin,0x38)
            or image != read(subimage,0x10) or data != read(node,0x10)):
        raise ValueError('original ownership/source changed during read')
    if u32(ai) != contract.SPEED_DIAL_VTABLE or u32(texture_wrapper) != native_texture:
        raise ValueError('original AI/texture identity changed during read')
    return dict(status, owner=owner,ai=ai,packet=packet,bank=bank,
                image_key=0,subimage_index=selected,texture_wrapper=texture_wrapper,
                native_texture_argument_pointer=native_texture,source_triangles=triangles,
                row_xyz=row_xyz,row_flag_byte_at_0x34=row[0x34],
                source_xy_to_native_vertex_rule='X=intX+rowX-0.5; Y=rowY+0.5-intY when row+0x34 flag is zero; transform follows separately',
                source_geometry_sha256=hashlib.sha256(raw).hexdigest(),
                registers=registers, bytes_read=memory.bytes_read,
                limitations=['Debugger pause is user declared, not verified by this RPM tool.',
                             'Texture pointer is not a COM generation or resource content hash.',
                             'Current player/race/UI lifetime must be joined to same-session trace.',
                             'No restart/reset lifetime or replacement authorization is inferred.'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pid',type=int,required=True)
    for name in ('eip','esp','esi','eax'):
        p.add_argument('--'+name,type=lambda x:int(x,16),required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); m=native.WindowsReadOnlyProcess(a.pid)
    try:
        result=collect(m,{n:getattr(a,n) for n in ('eip','esp','esi','eax')})
        result['identity']=m.identity
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    finally: m.close()

if __name__=='__main__': main()
