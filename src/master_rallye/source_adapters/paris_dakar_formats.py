"""Independent bounded TC/Gex/TIM research reader, revision 1.

Field interpretation is tied to owner-local dakar.exe static evidence. No
third-party implementation, executable execution, MR authoring or asset writes.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import re
import struct
from .. import universal_vehicle_scene as uvs

EXE_SHA256 = '94008b8708ddaf918397b56c2e194086ed9b088a7ec0e7e185effdebd51d1482'
MAX_FILE = 64 * 1024 * 1024
MAX_MEMBERS = 4096


@dataclass(frozen=True)
class Keys:
    header: bytes
    directory: bytes


def executable_keys(data: bytes) -> Keys:
    """Read key strings through verified PE mappings, rather than ship them."""
    if uvs.sha(data) != EXE_SHA256:
        raise ValueError('unqualified Paris-Dakar executable hash')
    # Original PE .data: file18b000 -> VA58b000, confirmed loader mappings.
    def key(pointer_offset):
        address = struct.unpack_from('<I', data, pointer_offset)[0]
        offset = address - 0x400000
        if not 0x18b000 <= offset < 0x1c2000:
            raise ValueError('unqualified key address mapping')
        end = data.find(b'\0', offset, offset + 1024)
        if end < offset + 1:
            raise ValueError('unterminated key')
        return data[offset:end]
    return Keys(key(0x1a1ef4), key(0x1a1efc))


def xor(data: bytes, key: bytes) -> bytes:
    if not key or len(key) > 1024 or len(data) > MAX_FILE:
        raise ValueError('XOR input/key budget')
    return bytes(v ^ key[i % len(key)] for i, v in enumerate(data))


def name(raw: bytes) -> str:
    end = raw.find(b'\0')
    if end < 1:
        raise ValueError('empty/unterminated resource name')
    try:
        value = raw[:end].decode('ascii')
    except UnicodeError as error:
        raise ValueError('non-ASCII resource name') from error
    if any(ord(v) < 32 for v in value) or any(v in value for v in '/\\:'):
        raise ValueError('unsafe resource name')
    uvs.relative_name(value)
    return value


def container(data: bytes, keys: Keys) -> dict:
    if not 80 <= len(data) <= MAX_FILE:
        raise ValueError('TC header/file byte budget')
    header = xor(data[:80], keys.header)
    if struct.unpack_from('<I', header)[0] != 0xdeafbeef:
        raise ValueError('TC signature/version unsupported (only clear-payload DEAFBEEF)')
    count, offset = struct.unpack_from('<II', header, 68)
    if not 1 <= count <= MAX_MEMBERS or offset < 80 or offset + count * 404 != len(data):
        raise ValueError('TC directory count/range')
    table = xor(data[offset:], keys.directory)
    entries = []; names = set(); spans = []
    for i in range(count):
        at = i * 404; record = table[at:at+404]
        kind, timestamp, start, size = struct.unpack_from('<4I', record)
        resource_name = name(record[20:276])
        if resource_name.casefold() in names:
            raise ValueError('TC duplicate resource name')
        names.add(resource_name.casefold())
        if not size or start < 80 or start + size > offset or start % 2048:
            raise ValueError('TC resource range/alignment')
        spans.append((start, start+size))
        entries.append({'index':i, 'name':resource_name, 'type_raw':kind,
                        'timestamp_raw':timestamp, 'offset':start, 'bytes':size,
                        'sha256':uvs.sha(data[start:start+size]),
                        'directory_record_offset':offset+at, 'directory_record_hex':record.hex()})
    spans.sort()
    if any(a[1] > b[0] for a,b in zip(spans,spans[1:])):
        raise ValueError('TC overlapping resource spans')
    return {'signature':'DEAFBEEF', 'header_decoded_hex':header.hex(),
            'directory_offset':offset, 'entries':entries, 'compression':'none for qualified payloads'}


def gex(data: bytes) -> dict:
    if not 112 <= len(data) <= 16*1024*1024 or data[:4] != b'Gex#':
        raise ValueError('Gex signature/header budget; DirectX xof not assumed')
    original_name = name(data[4:68]); bounds = list(struct.unpack_from('<6f',data,68))
    ntri, unknown, nt, nm, unique_hint = struct.unpack_from('<5I', data,92)
    if not 0 <= nt <= 256 or not 1 <= nm <= 256 or not 0 < ntri <= 200000:
        raise ValueError('Gex geometry/material budget')
    start = 112 + nt*40 + nm*84
    if start+128 > len(data):
        raise ValueError('truncated Gex tables')
    textures = [name(data[112+i*40:152+i*40]) for i in range(nt)]
    materials=[]
    for i in range(nm):
        at=112+nt*40+i*84; raw=data[at:at+84]
        materials.append({'name':name(raw[20:80]), 'texture_index':struct.unpack_from('<H',raw,18)[0],
                          'offset':at, 'raw_hex':raw.hex(), 'raw_fields':list(raw)})
    batches=[]; pos=start; nvtotal=tritotal=0
    while True:
        if len(batches)>=16384 or pos+128>len(data):
            raise ValueError('Gex batch count/truncation')
        nxt=struct.unpack_from('<I',data,pos)[0]
        material, ni, nv=struct.unpack_from('<3I',data,pos+32)
        end=pos+128+nv*32
        if not 1<=nv<=85 or not 0<ni<=48 or ni%3 or material>=nm or end>len(data):
            raise ValueError('Gex batch layout/index count/material reference')
        raw_indices=list(data[pos+64:pos+64+ni])
        if any(v%3 or v//3>=nv for v in raw_indices):
            raise ValueError('Gex invalid geometry/UV vertex index')
        vertices=[list(struct.unpack_from('<8f',data,pos+128+i*32)) for i in range(nv)]
        # The original loader reorders source px,py,pz,nz,u,v,nx,ny to D3D FVF112.
        if any(not math.isfinite(v) or abs(v)>1e6 for row in vertices for v in row):
            raise ValueError('Gex nonfinite/excessive vertex/UV')
        if any(not 0.99<sum(row[k]**2 for k in (3,6,7))<1.01 for row in vertices):
            raise ValueError('Gex unqualified normal layout')
        nvtotal+=nv;tritotal+=ni//3
        if nvtotal>200000 or tritotal>200000:
            raise ValueError('Gex aggregate allocation budget')
        batches.append({'offset':pos,'bytes':end-pos,'material_index':material,
                        'header_hex':data[pos:pos+64].hex(), 'vertices_original':vertices,
                        'indices_original':raw_indices,
                        'positions':[v[:3] for v in vertices],
                        'normals':[[v[6],v[7],v[3]] for v in vertices],
                        'uvs':[v[4:6] for v in vertices],
                        'triangles':[[v//3 for v in raw_indices[i:i+3]]for i in range(0,ni,3)]})
        if nxt==0:
            if end != len(data):
                raise ValueError('Gex trailing/ambiguous batch bytes')
            break
        if nxt != end-pos:
            raise ValueError('Gex next batch offset/overlap')
        pos+=nxt
    if tritotal != ntri or not all(math.isfinite(v) for v in bounds):
        raise ValueError('Gex declared triangle count/bounds')
    return {'name':original_name,'bounds_original':bounds,'textures':textures,
            'materials':materials,'batches':batches,'triangles':tritotal,'vertices':nvtotal,
            'unknown_header_u32_at96':unknown,'unique_vertex_hint_at108':unique_hint,
            'header_hex':data[:112].hex()}


def tim(data: bytes) -> tuple[dict,bytes,bytes,bytes]:
    """Qualified PC TIM-like indexed RGBA palette + four stored mip planes.

    This differs from PS1 TIM: palette is 256 RGBA32 entries directly at8.
    Return original alpha unchanged, including flag9 variable alpha palettes.
    """
    if not 1044 <= len(data) <= 8*1024*1024:
        raise ValueError('PC TIM texture byte budget')
    magic, flags=struct.unpack_from('<II',data)
    if magic!=16 or flags not in (0x40001,0x40009):
        raise ValueError('unqualified PC TIM signature/format/mip count')
    block,xy,w,h=struct.unpack_from('<IIHH',data,1032)
    if not 8<=w<=4096 or not 8<=h<=4096 or w&(w-1) or h&(h-1) or block!=12+w*h:
        raise ValueError('PC TIM dimensions/plane length')
    palette=data[8:1032]; a=1044;planes=[]
    for lod in range(4):
        size=(w>>lod)*(h>>lod)
        if a+size>len(data):raise ValueError('truncated PC TIM mip samples')
        planes.append({'lod':lod,'offset':a,'bytes':size,'width':w>>lod,'height':h>>lod,
                       'sha256':uvs.sha(data[a:a+size])});a+=size
    if a!=len(data):raise ValueError('PC TIM unexpected trailing mip bytes')
    samples=data[1044:1044+w*h]
    rgba=b''.join(palette[v*4:v*4+4] for v in samples)
    return ({'width':w,'height':h,'format':'PC TIM indexed8 RGBA32 palette',
             'flags_raw':flags,'image_xy_raw':xy,'mip_planes':planes,
             'source_channels':{'samples_per_pixel':1,'raw_sample_bytes':len(samples),
                                'raw_samples_sha256':uvs.sha(samples),'palette_bytes':len(palette),
                                'palette_sha256':uvs.sha(palette),'palette_order':'RGBA',
                                'alpha_status':'original palette channel retained; blend/render policy separate'}},
            rgba,samples,palette)


def description(data: bytes) -> dict:
    if len(data)>65536 or not data.startswith(b'RallyCar 1.00\r\n'):
        raise ValueError('unqualified RallyCar description/version/budget')
    try: text=data.decode('ascii')
    except UnicodeError as error:raise ValueError('non-ASCII RallyCar description') from error
    if '\0' in text:raise ValueError('unexpected description padding')
    rows=[];offset=0
    for line in text.splitlines(keepends=True):
        value=line.strip()
        if value:rows.append({'offset':offset,'text':value})
        offset+=len(line)
    def field(row,kind,key):
        match=re.fullmatch(re.escape(kind)+' +'+re.escape(key)+r'\s*:\s*(.+)',row['text'])
        return match.group(1) if match else None
    def vector(value):
        v=[float(x)for x in value.split()]
        if len(v)!=3 or any(not math.isfinite(x)or abs(x)>10000 for x in v):
            raise ValueError('invalid description vector')
        return v
    refs={};wheels=[];objects=[];current=None
    for row in rows:
        m=re.fullmatch(r'ArchList (.+?)\s*:\s*(.+)',row['text'])
        if m:
            key,value=m.groups()
            if key in ('Body','BodyShadow','FrontWheel','RearWheel','FrontWheelShadow','RearWheelShadow'):
                if key in refs:raise ValueError('duplicate assembly field')
                refs[key]={'value':value,'offset':row['offset']}
        value=field(row,'Vector3','Attach Point')
        if value:
            current={'attach_point':vector(value),'offset':row['offset']};wheels.append(current)
        if current and len(wheels)<=4:
            for key in ('Radius','Rest Position','Upper Limit','Lower Limit'):
                value=field(row,'Float',key)
                if value is not None and key not in current:
                    v=float(value)
                    if not math.isfinite(v)or abs(v)>100:raise ValueError('invalid suspension field')
                    current[key]=v
        value=field(row,'ArchList','Object')
        if value is not None:
            current=None;objects.append({'member':value,'reference_offset':row['offset']})
        value=field(row,'Vector3','Position')
        if value and objects and 'position' not in objects[-1]:
            objects[-1].update(position=vector(value),position_offset=row['offset'])
    if len(wheels)!=4 or any('Radius'not in w or 'Rest Position'not in w for w in wheels):
        raise ValueError('missing/ambiguous four-wheel suspension records')
    if any(key not in refs for key in ('Body','FrontWheel','RearWheel')):
        raise ValueError('missing body/wheel assembly references')
    if not (wheels[0]['attach_point'][0]<0<wheels[1]['attach_point'][0] and
            wheels[2]['attach_point'][0]<0<wheels[3]['attach_point'][0] and
            wheels[0]['attach_point'][2]>wheels[2]['attach_point'][2]):
        raise ValueError('unqualified/ambiguous wheel coordinate ordering')
    return {'records':rows,'references':refs,'wheels':wheels,'objects':objects}
