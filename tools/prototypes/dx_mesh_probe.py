#!/usr/bin/env python3
"""Bounds-checked R0.5 parser for confirmed Master Rallye DX sections.

The parser reconstructs draw-local indices but deliberately preserves unknown
record fields under offset-based names.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, struct
from pathlib import Path

MAGIC = 0x0000D00D
MAX_VERTICES = 10_000_000
MAX_UV_SETS = 8
MAX_INDICES = 100_000_000
MAX_DRAW_RECORDS = 100_000
MAX_TEXTURE_SLOTS = 32
MAX_STRING_BYTES = 4096

class DxParseError(ValueError):
    pass

class Reader:
    def __init__(self, data: bytes): self.data = data
    def require(self, offset: int, size: int, label: str) -> None:
        remaining = len(self.data) - offset
        if offset < 0 or size < 0 or remaining < size:
            raise DxParseError(f"{label} at 0x{offset:X}: need {size} bytes, have {max(remaining, 0)}")
    def unpack(self, fmt: str, offset: int, label: str):
        size = struct.calcsize(fmt); self.require(offset, size, label)
        return struct.unpack_from(fmt, self.data, offset)
    def u32(self, offset: int, label: str) -> int:
        return self.unpack('<I', offset, label)[0]
    def blob(self, offset: int, size: int, label: str) -> bytes:
        self.require(offset, size, label); return self.data[offset:offset+size]

MATERIAL_RE = re.compile(r"Material number \[\s*(\d+)\] has name \[(.*?)\]")
TEXTURE_RE = re.compile(r"Texture \[\s*(\d+)\].*?Name\[([^\]]+\.tga)\]", re.I)
MESH_RE = re.compile(r"moMesh\(Name \[(.*?)\] Index (\d+) Size (\d+)\)")

def texture_stem(path: str) -> str:
    return Path(path.replace('\\', '/')).stem.lower() + '-tga'

def parse_sidecar(path: Path | None):
    if path is None or not path.exists(): return None
    text = path.read_text(encoding='latin-1')
    materials=[]; current=None
    for line in text.splitlines():
        material=MATERIAL_RE.search(line)
        if material:
            current={"number":int(material.group(1)),"name":material.group(2),"texture_slots":[]};materials.append(current);continue
        texture=TEXTURE_RE.search(line)
        if texture and current is not None:
            current["texture_slots"].append({"slot":int(texture.group(1)),"source_tga":Path(texture.group(2).replace('\\','/')).name,
                                             "resource_stem":texture_stem(texture.group(2))})
    meshes=[{"name":m.group(1),"index":int(m.group(2)),"size":int(m.group(3))} for m in MESH_RE.finditer(text)]
    mm=re.search(r"Materials\(Size\s+(\d+)\)",text)
    return {"path":path.name,"material_count":int(mm.group(1)) if mm else None,"materials":materials,"mesh_count":len(meshes),"meshes":meshes,
            "mesh_span":max((m['index']+m['size'] for m in meshes),default=0)}

def read_length_string(reader: Reader, offset: int, label: str):
    length=reader.u32(offset,f'{label} length');length_offset=offset;offset+=4
    if length>MAX_STRING_BYTES:raise DxParseError(f'{label} at 0x{length_offset:X}: unreasonable length {length}')
    raw=reader.blob(offset,length,label);data_offset=offset;offset+=length
    try:text=raw.decode('ascii')
    except UnicodeDecodeError as exc:raise DxParseError(f'{label} at 0x{data_offset:X}: non-ASCII data') from exc
    return text,offset,{"length_offset":f'0x{length_offset:X}',"data_offset":f'0x{data_offset:X}',"length":length,"raw_hex":raw.hex(' '),"text":text}

def parse_draw_record(reader: Reader, offset: int, record_index: int):
    start=offset;variant=reader.u32(offset,f'draw record {record_index} tag');label=None;variant_fields=[];child_count=0
    if variant==2:
        core=offset
    elif variant==7:
        label,offset,label_raw=read_length_string(reader,offset+4,f'draw record {record_index} label')
        reader.require(offset,20,f'draw record {record_index} type-7 prefix')
        values=list(struct.unpack_from('<5I',reader.data,offset));variant_fields=[{"relative_offset":f'0x{offset-start+i*4:02X}',"u32":v} for i,v in enumerate(values)];child_count=values[3];offset+=20;core=offset
    elif variant==8:
        reader.require(offset+4,8,f'draw record {record_index} type-8 prefix')
        values=list(struct.unpack_from('<2I',reader.data,offset+4));variant_fields=[{"relative_offset":f'0x{4+i*4:02X}',"u32":v} for i,v in enumerate(values)];core=offset+12
    else:
        raise DxParseError(f'draw record {record_index} at 0x{start:X}: unsupported variant tag {variant}')
    prefix=reader.blob(core,40,f'draw record {record_index} core')
    words=list(struct.unpack('<10I',prefix))
    if words[0]!=2:raise DxParseError(f'draw record {record_index} at 0x{start:X}: embedded core tag is {words[0]}, expected 2')
    scale=struct.unpack_from('<f',prefix,28)[0];flags=list(prefix[32:36]);offset=core+40
    slot_count=reader.u32(offset,f'draw record {record_index} texture slot count');slot_count_offset=offset;offset+=4
    if slot_count>MAX_TEXTURE_SLOTS:raise DxParseError(f'draw record {record_index} at 0x{start:X}: unreasonable texture slot count {slot_count}')
    slots=[]
    for slot in range(slot_count):
        text,offset,raw=read_length_string(reader,offset,f'draw record {record_index} texture {slot}');raw['slot']=slot;slots.append(raw)
    terminal=reader.u32(offset,f'draw record {record_index} terminal');terminal_offset=offset;offset+=4
    if terminal!=0:raise DxParseError(f'draw record {record_index} terminal at 0x{terminal_offset:X}: expected 0, got {terminal}')
    own_end=offset;subrecords=[]
    if variant==7:
        for child_index in range(child_count):
            child,offset=parse_draw_record(reader,offset,f'{record_index}.{child_index+1}')
            if child['variant_tag']==7:
                raise DxParseError(f'draw record {record_index}: nested type-7 group is unsupported')
            subrecords.append(child)
    return {"record_index":record_index,"offset":f'0x{start:X}',"size":offset-start,"own_size":own_end-start,"variant_tag":variant,"variant_label":label,
            "variant_fields":variant_fields,"declared_child_count":child_count,"core_offset":f'0x{core:X}',"core_relative_offset":f'0x{core-start:X}',"core_raw_hex":prefix.hex(' '),
            "unknown_0x00":words[0],"vertex_base":words[1],"local_vertex_max":words[2],"index_start":words[3],"index_count":words[4],
            "unknown_0x14":words[5],"unknown_0x18":words[6],"unknown_0x1C_float":scale,"flags_0x20_u8":flags,"unknown_0x24":words[9],
            "texture_slot_count_offset":f'0x{slot_count_offset:X}',"texture_slots":slots,"terminal_offset":f'0x{terminal_offset:X}',
            "own_end_offset":f'0x{own_end:X}',"end_offset":f'0x{offset:X}',"subrecords":subrecords},offset

def material_candidates(record,sidecar):
    if not sidecar:return []
    actual=[s['text'].lower() for s in record['texture_slots']]
    matches=[]
    for material in sidecar['materials']:
        expected=[s['resource_stem'] for s in material['texture_slots']]
        expected=(expected+['Null']*len(actual))[:len(actual)];expected=[s.lower() for s in expected]
        if expected==actual:matches.append({"number":material['number'],"name":material['name']})
    return matches

def parse_dx(path: Path, sidecar_path: Path | None = None):
    data=path.read_bytes();reader=Reader(data);reader.require(0,16,'DX header')
    magic,word04,word08,vertex_count=reader.unpack('<4I',0,'DX header')
    if magic!=MAGIC:raise DxParseError(f'bad magic 0x{magic:08X}, expected 0x{MAGIC:08X}')
    if not 0<vertex_count<=MAX_VERTICES:raise DxParseError(f'unreasonable vertex count {vertex_count}')
    offset=16;position_offset=offset;reader.require(offset,vertex_count*12,'position section')
    positions=[reader.unpack('<3f',offset+i*12,f'position {i}') for i in range(vertex_count)];offset+=vertex_count*12
    normal_offset=offset;reader.require(offset,vertex_count*12,'normal section')
    normals=[reader.unpack('<3f',offset+i*12,f'normal {i}') for i in range(vertex_count)];offset+=vertex_count*12
    color_offset=offset;colors=reader.blob(offset,vertex_count*4,'color section');offset+=vertex_count*4
    uv_count_offset=offset;uv_set_count=reader.u32(offset,'UV set count');offset+=4
    if uv_set_count>MAX_UV_SETS:raise DxParseError(f'unreasonable UV set count {uv_set_count} at 0x{uv_count_offset:X}')
    uv_sets=[];uv_offsets=[]
    for uv_set in range(uv_set_count):
        uv_offsets.append(offset);reader.require(offset,vertex_count*8,f'UV set {uv_set}')
        uv_sets.append([reader.unpack('<2f',offset+i*8,f'UV set {uv_set} entry {i}') for i in range(vertex_count)]);offset+=vertex_count*8
    index_count_offset=offset;index_count=reader.u32(offset,'index count');offset+=4
    if index_count>MAX_INDICES:raise DxParseError(f'unreasonable index count {index_count} at 0x{index_count_offset:X}')
    index_offset=offset;reader.require(offset,index_count*2,'local index array')
    local_indices=list(struct.unpack_from(f'<{index_count}H',data,offset));offset+=index_count*2;trailer_offset=offset
    reader.require(offset,8,'draw table preamble');table_preamble=reader.u32(offset,'draw table preamble');record_count=reader.u32(offset+4,'draw record count');offset+=8
    if record_count>MAX_DRAW_RECORDS:raise DxParseError(f'unreasonable draw record count {record_count} at 0x{trailer_offset+4:X}')
    top_records=[]
    for record_index in range(record_count):
        record,offset=parse_draw_record(reader,offset,record_index);top_records.append(record)
    records=[];top_level_groups=[]
    def flatten_record(record,top_index):
        children=record.pop('subrecords');record['top_level_index']=top_index;record['draw_index']=len(records);indices=[record['draw_index']];records.append(record)
        for child in children:indices.extend(flatten_record(child,top_index))
        return indices
    for top_index,record in enumerate(top_records):
        indices=flatten_record(record,top_index)
        top_level_groups.append({"top_level_index":top_index,"offset":record['offset'],"size":record['size'],"variant_tag":record['variant_tag'],"variant_label":record['variant_label'],"draw_indices":indices})
    draw_table_end=offset;reader.require(offset,8,'expanded index section preamble')
    expanded_preamble=reader.u32(offset,'expanded index preamble');expanded_count=reader.u32(offset+4,'expanded index count');offset+=8
    if expanded_count>MAX_INDICES:raise DxParseError(f'unreasonable expanded index count {expanded_count} at 0x{offset-4:X}')
    if expanded_count!=index_count:raise DxParseError(f'expanded index count {expanded_count} does not match local index count {index_count}')
    expanded_offset=offset;reader.require(offset,expanded_count*4,'expanded index array')
    expanded_indices=list(struct.unpack_from(f'<{expanded_count}I',data,offset));offset+=expanded_count*4
    reconstructed=[None]*index_count;vertex_coverage=[None]*vertex_count
    for record in records:
        start,count=record['index_start'],record['index_count'];base,local_max=record['vertex_base'],record['local_vertex_max']
        if count%3:raise DxParseError(f"draw {record['record_index']} index count {count} is not divisible by 3")
        if start>index_count or count>index_count-start:raise DxParseError(f"draw {record['record_index']} index range {start}+{count} exceeds {index_count}")
        end_vertex=base+local_max
        if base>=vertex_count or end_vertex>=vertex_count:raise DxParseError(f"draw {record['record_index']} vertex range {base}..{end_vertex} exceeds {vertex_count}")
        raw=local_indices[start:start+count]
        if raw and max(raw)>local_max:raise DxParseError(f"draw {record['record_index']} raw max {max(raw)} exceeds declared local max {local_max}")
        for i in range(start,start+count):
            if reconstructed[i] is not None:raise DxParseError(f'draw index ranges overlap at index {i}')
            reconstructed[i]=local_indices[i]+base
        for i in range(base,end_vertex+1):
            if vertex_coverage[i] is not None:raise DxParseError(f'draw vertex ranges overlap at vertex {i}')
            vertex_coverage[i]=record['record_index']
        record['raw_index_min']=min(raw) if raw else None;record['raw_index_max']=max(raw) if raw else None
        record['global_vertex_min']=min((x+base for x in raw),default=None);record['global_vertex_max']=max((x+base for x in raw),default=None)
        record['triangle_count']=count//3
    if any(value is None for value in reconstructed):raise DxParseError('draw records do not cover the complete local index array')
    if any(value is None for value in vertex_coverage):raise DxParseError('draw records do not cover the complete vertex array')
    local_plus_base=[int(value) for value in reconstructed]
    expanded_expected=[]
    for i in range(0,index_count,3):
        expanded_expected.extend((local_plus_base[i+1],local_plus_base[i],local_plus_base[i+2]))
    if expanded_expected!=expanded_indices:
        mismatch=next(i for i,(a,b) in enumerate(zip(expanded_expected,expanded_indices)) if a!=b)
        raise DxParseError(f'expanded index mismatch at {mismatch}: expected {expanded_expected[mismatch]}, stored {expanded_indices[mismatch]}')
    sidecar=parse_sidecar(sidecar_path if sidecar_path is not None else path.with_suffix('.txt'))
    for record in records:
        record['material_candidates']=material_candidates(record,sidecar)
    bbox_min=[min(v[i] for v in positions) for i in range(3)];bbox_max=[max(v[i] for v in positions) for i in range(3)]
    lengths=[math.sqrt(x*x+y*y+z*z) for x,y,z in normals];footer=data[offset:]
    footer_info={"offset":f'0x{offset:X}',"size":len(footer),"sha256":hashlib.sha256(footer).hexdigest(),
                 "first_64_hex":footer[:64].hex(' '),"last_64_hex":footer[-64:].hex(' ') if footer else ""}
    if len(footer)<=256:footer_info["raw_hex"]=footer.hex(' ')
    if len(footer)==56:
        footer_bbox_min=list(struct.unpack_from('<3f',footer,0x20));footer_bbox_max=list(struct.unpack_from('<3f',footer,0x2C))
        footer_info.update({"unknown_0x00_u32":struct.unpack_from('<I',footer,0)[0],"unknown_0x04_float":struct.unpack_from('<f',footer,4)[0],
                            "unknown_0x08_float":struct.unpack_from('<f',footer,8)[0],"unknown_0x0C_u32":struct.unpack_from('<I',footer,12)[0],
                            "center_0x10":[*struct.unpack_from('<3f',footer,0x10)],"unknown_0x1C_float":struct.unpack_from('<f',footer,0x1C)[0],
                            "bbox_min_0x20":footer_bbox_min,"bbox_max_0x2C":footer_bbox_max,
                            "bbox_matches_positions":all(abs(a-b)<1e-5 for a,b in zip(footer_bbox_min+footer_bbox_max,bbox_min+bbox_max))})
    result={"schema_version":2,"file":path.name,"size":len(data),"header":{"magic":f'0x{magic:08X}',"word_0x04":word04,"word_0x08":word08,"vertex_count":vertex_count},
            "sections":{"positions":{"offset":f'0x{position_offset:X}',"count":vertex_count,"bbox_min":bbox_min,"bbox_max":bbox_max},
                        "normals":{"offset":f'0x{normal_offset:X}',"count":vertex_count,"length_min":min(lengths),"length_max":max(lengths),"length_mean":sum(lengths)/len(lengths)},
                        "colors":{"offset":f'0x{color_offset:X}',"count":vertex_count,"byte_length":len(colors),"alpha_values":sorted(set(colors[3::4]))},
                        "uv_sets":{"count_offset":f'0x{uv_count_offset:X}',"count":uv_set_count,"offsets":[f'0x{x:X}' for x in uv_offsets],"entries_per_set":vertex_count,
                                   "ranges":[{"min":[min(v[i] for v in values) for i in range(2)],"max":[max(v[i] for v in values) for i in range(2)]} for values in uv_sets]},
                        "indices":{"count_offset":f'0x{index_count_offset:X}',"offset":f'0x{index_offset:X}',"count":index_count,"triangle_count":index_count//3,"divisible_by_3":index_count%3==0,
                                   "raw_min":min(local_indices) if local_indices else None,"raw_max":max(local_indices) if local_indices else None},
                        "draw_table":{"offset":f'0x{trailer_offset:X}',"preamble_u32":table_preamble,"declared_top_level_record_count":record_count,"physical_draw_count":len(records),"top_level_groups":top_level_groups,"records":records,"end_offset":f'0x{draw_table_end:X}',
                                      "complete_index_partition":True,"complete_vertex_partition":True},
                        "expanded_indices":{"preamble_offset":f'0x{draw_table_end:X}',"preamble_u32":expanded_preamble,"count":expanded_count,"offset":f'0x{expanded_offset:X}',
                                            "end_offset":f'0x{offset:X}',"matches_local_plus_base_with_first_two_swapped":True},"footer":footer_info},"sidecar":sidecar}
    arrays={"positions":positions,"normals":normals,"colors":colors,"uv_sets":uv_sets,"local_indices":local_indices,"local_plus_base":local_plus_base,"global_indices":expanded_indices,
            "expanded_indices":expanded_indices,"draw_records":records}
    return result,arrays

def main():
    ap=argparse.ArgumentParser();ap.add_argument('files',nargs='+',type=Path);ap.add_argument('--json',type=Path);ap.add_argument('--root',type=Path)
    args=ap.parse_args();results=[]
    for path in args.files:
        result,_=parse_dx(path.resolve());
        if args.root:
            try:result['file']=path.resolve().relative_to(args.root.resolve()).as_posix()
            except ValueError:pass
        results.append(result)
    payload=json.dumps({"schema_version":2,"files":results},indent=2,ensure_ascii=False)+'\n'
    if args.json:args.json.write_text(payload,encoding='utf-8')
    else:print(payload,end='')
if __name__=='__main__':main()
