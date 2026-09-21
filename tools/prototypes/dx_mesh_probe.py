#!/usr/bin/env python3
"""Minimal evidence-driven parser for the confirmed leading sections of .dx.

This is an R0 diagnostic prototype, not a complete production converter.
"""
from __future__ import annotations
import argparse, json, math, re, struct
from pathlib import Path

MAGIC=0x0000D00D

def take(fmt,data,offset):
    out=struct.unpack_from(fmt,data,offset); return out,offset+struct.calcsize(fmt)

def parse_sidecar(path):
    if not path or not path.exists(): return None
    text=path.read_text(encoding='latin-1')
    mm=re.search(r'Materials\(Size\s+(\d+)\)',text)
    meshes=[{"name":m.group(1),"index":int(m.group(2)),"size":int(m.group(3))}
            for m in re.finditer(r'moMesh\(Name \[(.*?)\] Index (\d+) Size (\d+)\)',text)]
    return {"material_count":int(mm.group(1)) if mm else None,"mesh_count":len(meshes),
            "mesh_span":max((m['index']+m['size'] for m in meshes),default=0)}

def parse_dx(path):
    data=path.read_bytes(); off=0
    (magic,word04,word08,vertex_count),off=take('<4I',data,off)
    if magic!=MAGIC: raise ValueError(f'bad magic 0x{magic:08X}')
    need=16+vertex_count*28+4
    if vertex_count==0 or need>len(data): raise ValueError('implausible vertex count')
    positions=[]; normals=[]
    for _ in range(vertex_count): v,off=take('<3f',data,off); positions.append(v)
    for _ in range(vertex_count): v,off=take('<3f',data,off); normals.append(v)
    colors=data[off:off+vertex_count*4]; off+=vertex_count*4
    (uv_set_count,),off=take('<I',data,off)
    if not 0<=uv_set_count<=8: raise ValueError(f'implausible UV set count {uv_set_count}')
    uv_sets=[]
    for _ in range(uv_set_count):
        values=[]
        for _ in range(vertex_count): uv,off=take('<2f',data,off); values.append(uv)
        uv_sets.append(values)
    (index_count,),off=take('<I',data,off)
    if off+index_count*2>len(data): raise ValueError('index buffer exceeds file')
    indices=list(struct.unpack_from(f'<{index_count}H',data,off)); off+=index_count*2
    trailing_words=list(struct.unpack_from('<2I',data,off)) if off+8<=len(data) else []
    lengths=[math.sqrt(x*x+y*y+z*z) for x,y,z in normals]
    result={"schema_version":1,"file":path.name,"size":len(data),
            "header":{"magic":f'0x{magic:08X}',"word_0x04":word04,"word_0x08":word08,"vertex_count":vertex_count},
            "sections":{"positions":{"offset":"0x10","count":vertex_count,
                         "bbox_min":[min(v[i] for v in positions) for i in range(3)],"bbox_max":[max(v[i] for v in positions) for i in range(3)]},
                        "normals":{"count":vertex_count,"length_min":min(lengths),"length_max":max(lengths),
                                   "length_mean":sum(lengths)/len(lengths)},
                        "colors":{"count":vertex_count,"byte_length":len(colors),"alpha_values":sorted(set(colors[3::4]))},
                        "uv_sets":{"count":uv_set_count,"entries_per_set":vertex_count,
                                   "ranges":[{"min":[min(v[i] for v in uvs) for i in range(2)],"max":[max(v[i] for v in uvs) for i in range(2)]} for uvs in uv_sets]},
                        "indices":{"offset":f'0x{off-index_count*2:X}',"count":index_count,"triangle_count":index_count//3,
                                   "divisible_by_3":index_count%3==0,"min":min(indices) if indices else None,"max":max(indices) if indices else None,
                                   "all_in_vertex_range":all(i<vertex_count for i in indices)},
                        "trailing":{"offset":f'0x{off:X}',"first_two_u32":trailing_words,"unparsed_bytes":len(data)-off}},
            "sidecar":parse_sidecar(path.with_suffix('.txt'))}
    return result,(positions,normals,uv_sets,indices)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('files',nargs='+',type=Path);ap.add_argument('--json',type=Path)
    args=ap.parse_args();results=[]
    for p in args.files:
        result,arrays=parse_dx(p);results.append(result)
    payload=json.dumps({"schema_version":1,"files":results},indent=2)+'\n'
    if args.json:args.json.write_text(payload,encoding='utf-8')
    else:print(payload,end='')
if __name__=='__main__':main()
