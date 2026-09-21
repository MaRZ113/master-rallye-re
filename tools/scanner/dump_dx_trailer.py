#!/usr/bin/env python3
"""Raw, minimally interpreted dump of the variable trailer after a DX index buffer."""
from __future__ import annotations
import argparse, hashlib, json, math, struct
from pathlib import Path
class DumpError(ValueError): pass
class Reader:
    def __init__(self,data): self.data=data
    def need(self,off,size,label):
        if off<0 or size<0 or off+size>len(self.data): raise DumpError(f'{label} at 0x{off:X}: need {size} bytes, file has {len(self.data)-off}')
    def u32(self,off,label): self.need(off,4,label);return struct.unpack_from('<I',self.data,off)[0]
    def f32(self,off,label): self.need(off,4,label);return struct.unpack_from('<f',self.data,off)[0]
    def bytes(self,off,size,label):self.need(off,size,label);return self.data[off:off+size]
def leading_end(r):
    r.need(0,16,'header');n=r.u32(12,'vertex count');
    if n==0 or n>10_000_000:raise DumpError(f'unreasonable vertex count {n}')
    off=16+n*28;r.need(16,n*28,'vertex arrays');u=r.u32(off,'UV set count');off+=4
    if u>8:raise DumpError(f'unreasonable UV set count {u}')
    r.need(off,u*n*8,'UV arrays');off+=u*n*8;i=r.u32(off,'index count');off+=4
    if i>100_000_000:raise DumpError(f'unreasonable index count {i}')
    r.need(off,i*2,'index array');return off+i*2,n,i
def parse(path,root=None):
    data=path.read_bytes();r=Reader(data);off,n,index_count=leading_end(r);trailer=off
    preamble=r.u32(off,'trailer word 0');count=r.u32(off+4,'candidate record count');off+=8
    if count>10000:raise DumpError(f'unreasonable record count {count}')
    records=[]
    for record_index in range(count):
        start=off;prefix=r.bytes(off,40,f'record {record_index} prefix');u32s=list(struct.unpack('<10I',prefix));f32s=list(struct.unpack('<10f',prefix))
        if u32s[0]!=2:raise DumpError(f'record {record_index} at 0x{start:X}: non-simple tag {u32s[0]}; use dx_mesh_probe.py for variants')
        off+=40
        string_count=r.u32(off,f'record {record_index} string count');off+=4
        if string_count>32:raise DumpError(f'record {record_index} at 0x{start:X}: unreasonable string count {string_count} at 0x{off-4:X}')
        strings=[]
        for string_index in range(string_count):
            length=r.u32(off,f'record {record_index} string {string_index} length');length_off=off;off+=4
            if length>4096:raise DumpError(f'unreasonable string length {length}')
            raw=r.bytes(off,length,f'record {record_index} string {string_index}');off+=length
            strings.append({'length_offset':f'0x{length_off:X}','data_offset':f'0x{off-length:X}','length':length,'raw_hex':raw.hex(' '),'text':raw.decode('ascii','replace')})
        terminal=r.u32(off,f'record {record_index} terminal');off+=4
        records.append({'index':record_index,'offset':f'0x{start:X}','size':off-start,'prefix_hex':prefix.hex(' '),
                        'fields':[{'relative_offset':f'0x{i*4:02X}','raw_hex':prefix[i*4:i*4+4].hex(' '),'u32':u32s[i],
                                   'f32':f32s[i] if math.isfinite(f32s[i]) else None} for i in range(10)],
                        'string_count_offset':f'0x{start+40:X}','string_count':string_count,'strings':strings,
                        'terminal_offset':f'0x{off-4:X}','terminal_u32':terminal,'end_offset':f'0x{off:X}'})
    second_start=off;second_preamble=r.u32(off,'post-record word 0');expanded_count=r.u32(off+4,'post-record count');off+=8
    if expanded_count>100_000_000:raise DumpError(f'unreasonable expanded count {expanded_count}')
    r.need(off,expanded_count*4,'post-record u32 array');expanded=list(struct.unpack_from(f'<{expanded_count}I',data,off));off+=expanded_count*4
    footer=data[off:]
    display=path.name
    if root:
        try:display=path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:display=path.name
    return {'path':display,'file_size':len(data),'vertex_count':n,'index_count':index_count,'trailer_offset':f'0x{trailer:X}',
            'trailer_preamble_u32':preamble,'candidate_record_count':count,'records':records,
            'post_record_section':{'offset':f'0x{second_start:X}','preamble_u32':second_preamble,'count':expanded_count,
                                   'data_offset':f'0x{second_start+8:X}','end_offset':f'0x{off:X}',
                                   'min':min(expanded) if expanded else None,'max':max(expanded) if expanded else None,
                                   'sha256':hashlib.sha256(data[second_start+8:off]).hexdigest(),
                                   'first_12':expanded[:12],'last_12':expanded[-12:]},
            'footer':{'offset':f'0x{off:X}','size':len(footer),'raw_hex':footer.hex(' ')}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('files',nargs='+',type=Path);ap.add_argument('--root',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args();result={'schema_version':1,'files':[parse(p.resolve(),a.root) for p in a.files]};payload=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(payload,encoding='utf-8')
    else:print(payload,end='')
if __name__=='__main__':main()
