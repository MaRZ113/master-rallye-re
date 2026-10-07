"""Strict offline reader for the PS2 F001/125 image-bank stream and simple GXI.

No writer, repacker or PC UI implementation. All offsets refer to decoded
payloads. Diagnostic images require Pillow; parsing uses the standard library.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

SCHEMA_VERSION = 1
MAX_SIZE = 16 * 1024 * 1024


class FormatError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False)+'\n',
                    encoding='utf-8', newline='\n')


def bounds(points):
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)] if points else None


def parse_psb(data):
    if len(data) > MAX_SIZE or len(data) < 16:
        raise FormatError('PSB size outside supported bounds')
    magic, version, count = struct.unpack_from('<3I', data)
    if (magic, version) != (0xf001, 125):
        raise FormatError('Unsupported PSB signature/version')
    if count > 65536 or count > (len(data)-16)//8:
        raise FormatError('Impossible mapping count')
    mappings, seen = [], set()
    for i in range(count):
        at = 12+i*8
        key, index = struct.unpack_from('<2I', data, at)
        if key > 65535 or index > 65535 or key in seen:
            raise FormatError('Invalid or duplicate PSB mapping')
        seen.add(key)
        mappings.append({'offset':at, 'width':8, 'key_u32':key, 'image_index_u32':index,
                         'printable_character':chr(key) if 32<=key<=126 else None,
                         'evidence':'CONFIRMED_BY_BOTH'})
    pos = 12+count*8
    count_at = pos
    image_count = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    if image_count > 65536 or image_count > (len(data)-pos)//4:
        raise FormatError('Impossible image count')
    if any(m['image_index_u32'] >= image_count for m in mappings):
        raise FormatError('Mapping references absent image')
    images, refs, unknown = [], set(), []
    total = 0
    for image_index in range(image_count):
        if pos+4 > len(data): raise FormatError('Truncated triangle count')
        start = pos
        triangle_count = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        if triangle_count > 65536 or triangle_count > (len(data)-pos)//69:
            raise FormatError('Impossible triangle count')
        triangles = []
        for triangle_index in range(triangle_count):
            at = pos
            if pos+68 > len(data): raise FormatError('Truncated triangle record')
            uv = list(struct.unpack_from('<6f', data, pos))
            uv_bits = struct.unpack_from('<6I', data, pos)
            coords = struct.unpack_from('<6i', data, pos+24)
            rect = list(struct.unpack_from('<4i', data, pos+48))
            name_length = struct.unpack_from('<I', data, pos+64)[0]
            pos += 68
            if not 1<=name_length<=1023 or pos+name_length>len(data):
                raise FormatError('Invalid or truncated resource-name length')
            raw_name = data[pos:pos+name_length]
            if raw_name in (b'.',b'..') or not re.fullmatch(rb'[A-Za-z0-9_.-]+', raw_name):
                raise FormatError('Invalid resource-name bytes')
            name = raw_name.decode('ascii')
            pos += name_length
            null = name == 'Null'
            if not null:
                if any(not math.isfinite(v) or not 0<=v<=1 for v in uv):
                    raise FormatError('Invalid normalized UV')
                if not 0<=rect[0]<rect[2]<=16384 or not 0<=rect[1]<rect[3]<=16384:
                    raise FormatError('Invalid atlas rectangle')
                refs.add(name)
            else:
                # Runtime skips Null texture resolution. Preserve uninterpreted fields,
                # including canonical NaN/Inf bit patterns, without guessing UV.
                unknown.append({'offset':at, 'size':24, 'raw_hex':data[at:at+24].hex(),
                                'reason':'Null texture: uninterpreted UV values', 'evidence':'UNKNOWN'})
                unknown.append({'offset':at+48, 'size':16, 'raw_hex':data[at+48:at+64].hex(),
                                'reason':'Null texture: uninterpreted source rectangle', 'evidence':'UNKNOWN'})
            points = [list(coords[i:i+2]) for i in (0,2,4)]
            triangles.append({'index':triangle_index, 'offset':at, 'size':pos-at,
                              'uv_offset':at, 'uv_pairs':[[v if math.isfinite(v) else None for v in uv[i:i+2]] for i in (0,2,4)],
                              'uv_raw_u32':[f'{v:08x}' for v in uv_bits],
                              'vertices_offset':at+24, 'vertices_xy':points,
                              'source_rect_offset':at+48, 'source_rect_xyxy':rect,
                              'source_rect_evidence':'UNKNOWN' if null else 'STATIC_INFERENCE',
                              'name_length_offset':at+64, 'name_length':name_length,
                              'name_offset':at+68, 'texture_name':name,
                              'texture_resolution':'NULL_SENTINEL' if null else 'UNRESOLVED',
                              'evidence':'CONFIRMED_BY_BOTH'})
        images.append({'image_index':image_index, 'offset':start, 'size':pos-start,
                       'triangle_count':triangle_count, 'triangles':triangles,
                       'local_bounds_xyxy':bounds([p for r in triangles for p in r['vertices_xy']]),
                       'quads':derive_quads(triangles), 'evidence':'CONFIRMED_BY_BOTH'})
        total += triangle_count
    if pos<len(data):
        unknown.append({'offset':pos, 'size':len(data)-pos, 'raw_hex':data[pos:].hex(),
                        'reason':'Unrecognized trailing bytes', 'evidence':'UNKNOWN'})
    return {'schema_version':SCHEMA_VERSION, 'format':'PS2_PSB_F001_125',
            'provenance':{'decoded_size':len(data),'decoded_sha256':sha(data)},
            'header':{'magic':magic,'version':version,'mapping_count':count,
                      'image_count_offset':count_at,'image_count':image_count},
            'mappings':mappings, 'images':images, 'triangle_count':total,
            'texture_references':sorted(refs), 'unknown_ranges':unknown,
            'recognized_size':pos, 'confidence':'CONFIRMED_BY_BOTH'}


def derive_quads(triangles):
    """Only pair adjacent records when both geometry and UV prove a rectangle."""
    result = []
    for i in range(0,len(triangles)-1,2):
        a,b = triangles[i:i+2]
        if a['texture_name']=='Null' or a['texture_name']!=b['texture_name']: continue
        if a['source_rect_xyxy']!=b['source_rect_xyxy']: continue
        points = a['vertices_xy']+b['vertices_xy']
        box = bounds(points)
        corners = {(box[x],box[y]) for x in (0,2) for y in (1,3)}
        uv = a['uv_pairs']+b['uv_pairs']
        uv_box = bounds(uv)
        uv_corners = {(uv_box[x],uv_box[y]) for x in (0,2) for y in (1,3)}
        def area(p):
            return abs((p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[1][1]-p[0][1])*(p[2][0]-p[0][0]))
        if len(corners)!=4 or set(map(tuple,points))!=corners or set(map(tuple,uv))!=uv_corners: continue
        if area(a['vertices_xy'])+area(b['vertices_xy'])!=2*(box[2]-box[0])*(box[3]-box[1]): continue
        if len(set(map(tuple,a['vertices_xy'])) & set(map(tuple,b['vertices_xy'])))!=2: continue
        shared = list(set(map(tuple,a['vertices_xy'])) & set(map(tuple,b['vertices_xy'])))
        if shared[0][0]==shared[1][0] or shared[0][1]==shared[1][1]: continue
        if area(a['uv_pairs'])==0 or area(b['uv_pairs'])==0: continue
        # Supported PSB quads map X to U and increasing local Y to decreasing V.
        if any(abs(uvp[0]-(uv_box[0]+(pt[0]-box[0])/(box[2]-box[0])*(uv_box[2]-uv_box[0])))>1e-6 or
               abs(uvp[1]-(uv_box[3]-(pt[1]-box[1])/(box[3]-box[1])*(uv_box[3]-uv_box[1])))>1e-6
               for pt,uvp in zip(points,uv)): continue
        result.append({'triangle_indices':[i,i+1], 'texture_name':a['texture_name'],
                       'local_bounds_xyxy':box, 'uv_bounds':uv_box,
                       'source_rect_xyxy':a['source_rect_xyxy'],
                       'evidence':'STATIC_INFERENCE'})
    return result


def parse_gxi(data):
    if len(data)<8 or len(data)>MAX_SIZE: raise FormatError('GXI size outside supported bounds')
    magic,width,height = struct.unpack_from('<IHH',data)
    if magic!=0x13039: raise FormatError('Unsupported GXI magic/variant')
    if not width or not height or len(data)!=8+width*height*4:
        raise FormatError('GXI dimensions/payload size mismatch')
    alpha = data[11::4]
    return {'format':'PS2_SIMPLE_GXI_13039', 'magic':magic,'width':width,'height':height,
            'size':len(data),'sha256':sha(data),'bytes_per_pixel':4,
            'channel_order':'RGBA','channel_order_evidence':'CONFIRMED_BY_VISUAL_RECONSTRUCTION',
            'alpha_min':min(alpha),'alpha_max':max(alpha),'alpha_unique_count':len(set(alpha)),
            'alpha_nonzero_pixels':sum(v!=0 for v in alpha),
            'average_rgba':[round(sum(data[8+c::4])/(width*height),6) for c in range(4)]}


def resolve_textures(document, psb_path, manifest):
    lookup = {r['path']:r for r in manifest['entries'] if r['kind']=='file'}
    directory = psb_path.rsplit('\\',1)[0]
    resolved = {}
    for name in document['texture_references']:
        path = directory+'\\'+name.upper()+'.GXI'
        if path not in lookup: raise FormatError('Missing texture reference: '+path)
        resolved[name] = path
    for image in document['images']:
        for row in image['triangles']:
            if row['texture_name']!='Null':
                row['logical_texture_path'] = resolved[row['texture_name']]
                row['texture_resolution'] = 'EXACT_MANIFEST_MATCH'
    return resolved


def glyphs(document):
    return [{'key_u32':r['key_u32'],'character':r['printable_character'],
             'image_index':r['image_index_u32'],
             'local_bounds_xyxy':document['images'][r['image_index_u32']]['local_bounds_xyxy'],
             'triangles':document['images'][r['image_index_u32']]['triangle_count'],
             'advance':None,'bearing':None,'baseline':None,
             'metrics_evidence':'UNKNOWN: no font advance/baseline fields in PSB'} for r in document['mappings']]


def verify(document, textures=None):
    if any(r['reason']=='Unrecognized trailing bytes' for r in document['unknown_ranges']):
        raise FormatError('Unknown trailing bytes prevent verification')
    checks = 0
    if textures is not None:
        for image in document['images']:
            for row in image['triangles']:
                if row['texture_name']=='Null': continue
                if row['texture_name'] not in textures: raise FormatError('Missing texture bytes')
                gxi = parse_gxi(textures[row['texture_name']])
                x0,y0,x1,y1 = row['source_rect_xyxy']
                if x1>gxi['width'] or y1>gxi['height']: raise FormatError('Atlas rectangle exceeds texture')
                u,v = zip(*row['uv_pairs'])
                actual = [min(u),min(v),max(u),max(v)]
                # Serialized rectangle encloses the allocated cell, including
                # padding. Actual UV can stop before its right/bottom edges.
                pixel_bounds = [actual[0]*gxi['width'],actual[1]*gxi['height'],
                                actual[2]*gxi['width'],actual[3]*gxi['height']]
                if (pixel_bounds[0]<x0-1e-6 or pixel_bounds[1]<y0-1e-6 or
                    pixel_bounds[2]>x1+1e-6 or pixel_bounds[3]>y1+1e-6):
                    raise FormatError('UV bounds exceed allocated atlas rectangle')
                checks += 1
    return {'verified':True,'decoded_sha256':document['provenance']['decoded_sha256'],
            'images':len(document['images']),'triangles':document['triangle_count'],
            'uninterpreted_field_ranges':len(document['unknown_ranges']),
            'texture_checks':checks,'scope':'structural' if textures is None else 'structural and exact textures'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command',choices=['info','dump','strings','sprites','glyphs','verify'])
    ap.add_argument('file',type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--texture-dir',type=Path)
    a = ap.parse_args()
    if a.file.stat().st_size>MAX_SIZE:raise FormatError('PSB size outside supported bounds')
    doc = parse_psb(a.file.read_bytes())
    if a.command=='dump': value=doc
    elif a.command=='info':
        value={k:doc[k] for k in ('schema_version','format','provenance','header','triangle_count','texture_references','confidence')}
        value['unknown_range_count']=len(doc['unknown_ranges'])
    elif a.command=='strings': value=[{'offset':t['name_offset'],'length':t['name_length'],'value':t['texture_name']} for i in doc['images'] for t in i['triangles']]
    elif a.command=='sprites': value=doc['images']
    elif a.command=='glyphs': value=glyphs(doc)
    else:
        textures = {n:(a.texture_dir/(n.upper()+'.GXI')).read_bytes() for n in doc['texture_references']} if a.texture_dir else None
        value=verify(doc,textures)
    if a.command not in ('info','dump'):
        value={'schema_version':SCHEMA_VERSION,'provenance':doc['provenance'],
               {'strings':'strings','sprites':'sprites','glyphs':'glyphs','verify':'verification'}[a.command]:value}
    if a.output: write_json(a.output,value)
    else: print(json.dumps(value,indent=2,allow_nan=False))


if __name__=='__main__':
    try: main()
    except (FormatError,OSError) as e: sys.exit('psbtool: '+str(e))
