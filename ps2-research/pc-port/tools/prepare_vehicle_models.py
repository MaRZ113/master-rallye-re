"""Read-only PSM -> private lossless visual representation. No runtime admission.

No list-triangulation or new winding policy: original 52-byte source vertices,
strips, flags and hierarchy are retained for a later admitted renderer. Original
GXI blobs exist only in the ignored private output; they are never packaged.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import struct
import sys

PORT=Path(__file__).resolve().parents[1]
ROOT=PORT.parents[1]
HEADER=struct.Struct('<8s4I32s')
MAGIC=b'PS2VEH01'
INVENTORY=PORT/'docs/vehicle-model-port1/ps2-format-lights/complete-inventory.json'

def sha(data):return hashlib.sha256(data).hexdigest()

def serialize(metadata,vertices,textures):
    if not vertices or len(vertices)%52 or len(vertices)>52*1000000:raise ValueError('Invalid source vertex storage')
    if len(textures)>256:raise ValueError('Texture budget exceeded')
    for i in range(len(vertices)//52):
        values=struct.unpack_from('<3f',vertices,i*52)+struct.unpack_from('<4f',vertices,i*52+20)+struct.unpack_from('<4f',vertices,i*52+36)
        if not all(math.isfinite(v) for v in values):raise ValueError('Non-finite original vertex')
    meta=json.dumps(metadata,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if len(meta)>4*1024*1024:raise ValueError('Metadata budget exceeded')
    digest=bytes.fromhex(metadata['source_sha256'])
    if len(digest)!=32:raise ValueError('Invalid source identity')
    data=bytearray(HEADER.pack(MAGIC,1,len(meta),len(vertices)//52,len(textures),digest))
    data.extend(meta);data.extend(vertices)
    for texture in textures:
        if not texture or len(texture)>16*1024*1024:raise ValueError('Texture outside budget')
        data.extend(struct.pack('<I',len(texture)));data.extend(texture)
    return bytes(data)

def validate(data):
    if len(data)<HEADER.size:raise ValueError('Truncated header')
    magic,version,size,count,tx_count,source=HEADER.unpack_from(data)
    if magic!=MAGIC or version!=1 or not 0<count<=1000000 or size>4*1024*1024 or tx_count>256:raise ValueError('Unsupported header')
    pos=HEADER.size;end=pos+size
    if end+count*52>len(data):raise ValueError('Truncated geometry')
    meta=json.loads(data[pos:end]);vertices=data[end:end+count*52];pos=end+count*52
    textures=[]
    for _ in range(tx_count):
        if pos+4>len(data):raise ValueError('Truncated texture size')
        n=struct.unpack_from('<I',data,pos)[0];pos+=4
        if not 0<n<=16*1024*1024 or pos+n>len(data):raise ValueError('Truncated/oversized texture')
        textures.append(data[pos:pos+n]);pos+=n
    if pos!=len(data) or source.hex()!=meta['source_sha256']:raise ValueError('Trailer/source identity mismatch')
    if serialize(meta,vertices,textures)!=data:raise ValueError('Noncanonical representation')
    for mesh in meta.get('meshes',[]):
        for strip in mesh['strips']:
            if not 0<=strip['start']<=count or not 0<=strip['count']<=count-strip['start']:raise ValueError('Strip outside vertex storage')
    return {'source_sha256':source.hex(),'vertices':count,'textures':tx_count,'bytes':len(data),
        'asset_sha256':sha(data),'runtime_admission':'NOT_IMPLEMENTED_OWNER_JOIN_REQUIRED'}

def output_path(family):
    if not family or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for c in family):raise ValueError('Invalid family')
    path=PORT/'.assets/vehicles'/f'{family}-COMPLETE.ps2vehicle'
    root=PORT.resolve()
    current=PORT
    for part in path.relative_to(PORT).parts:
        current/=part
        if current.is_symlink() or getattr(current,'is_junction',lambda:False)():raise ValueError('Linked output component')
    if not path.resolve().is_relative_to(root):raise ValueError('Output outside ignored private root')
    if path.exists() and (not path.is_file() or path.stat().st_nlink!=1):raise ValueError('Nonregular output')
    return path

def prepare(ps2_root,families,replace_verified=False):
    sys.path.insert(0,str(ROOT/'ps2-research/tools'))
    import tngtool as t
    import water_runtime as w
    import psbtool as p
    spec=importlib.util.spec_from_file_location('proved_complete_reader',PORT/'docs/vehicle-model-port1/ps2-format-lights/complete_reader.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    ps2_root=Path(ps2_root);w.verify_inputs(ps2_root)
    manifest,_=t.load_pak(ps2_root/'TNG.PAK')
    entries={t.logical_path(e['path']).upper():e for e in manifest['entries'] if e['kind']=='file'}
    if len(entries)!=sum(e['kind']=='file' for e in manifest['entries']):raise ValueError('Nonunique archive paths')
    inventory=json.loads(INVENTORY.read_text())['inventory'];rows=[]
    for item in inventory:
        family=item['family']
        if families and family not in families:continue
        original,provenance=t.read_payload(entries[t.logical_path(item['resource']).upper()],ps2_root/'TNG.000')
        if sha(original)!=item['sha256']:raise ValueError('Frozen COMPLETE hash mismatch: '+family)
        scene,trailer=reader.decode_complete(original)
        textures=[];texture_meta=[];indices={};meshes=[];unresolved=[]
        for mesh in scene.meshes:
            slots=[]
            for slot in mesh['textures']:
                key=t.logical_path('\\TNG\\DATAPSM\\'+slot['name']+'.GXI').upper()
                resource_index=None
                if key not in indices:
                    entry=entries.get(key)
                    if entry:
                        raw,prov=t.read_payload(entry,ps2_root/'TNG.000');decoded=p.parse_gxi(raw)
                        indices[key]=len(textures);textures.append(raw)
                        texture_meta.append({'path':entry['path'],'sha256':sha(raw),'width':decoded['width'],
                            'height':decoded['height'],'format':'ORIGINAL_GXI','provenance':prov})
                    else:unresolved.append(key)
                resource_index=indices.get(key)
                slots.append({**slot,'private_texture_index':resource_index})
            meshes.append({'path':mesh['path'],'node_offset':mesh['node_offset'],
                'material_offset':mesh['material_offset'],'material':mesh['material'],
                'textures':slots,'strips':mesh['strips'],
                'visibility':'AUTHORED_SOURCE_RUNTIME_SELECTION_UNKNOWN'})
        metadata={'family':family,'source_resource':item['resource'],'source_sha256':sha(original),
            'source_provenance':provenance,'vertex_layout':'ORIGINAL_52_BYTE_LE',
            'coordinates':'MODEL_LOCAL_GAME_SOURCE','source_color':'RAW_0xRRGGBBAA_NO_ALPHA_REMAP',
            'tree_end':scene.end,'trailer':trailer,'extra_nodes':scene.extra_nodes,
            'meshes':meshes,'textures':texture_meta,'unresolved_textures':sorted(set(unresolved)),
            'runtime_admission':'DISABLED_CURRENT_NATIVE_OWNER_AND_SUBMISSION_REQUIRED',
            'winding':'ORIGINAL_STRIP_ORDER_FLAGS_AND_ADC_RETAINED_NO_TRIANGLELIST_GUESS'}
        asset=serialize(metadata,original[32:32+scene.vertex_count*52],textures)
        check=validate(asset);path=output_path(family);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=asset:
            prior=validate(path.read_bytes())
            if not replace_verified or prior['source_sha256']!=check['source_sha256']:
                raise ValueError('Refusing different existing private asset: '+str(path))
        path.write_bytes(asset)
        rows.append({'family':family,'asset':path.relative_to(PORT).as_posix(),**check,
            'texture_count':len(textures),'unresolved_texture_count':len(set(unresolved)),
            'source_faces':item['source_triangles'],'source_meshes':item['mesh_count']})
        print(family,check['bytes'],len(textures),'textures',len(set(unresolved)),'unresolved',flush=True)
    if families and set(families)!={r['family'] for r in rows}:raise ValueError('Requested family not in verified inventory')
    return {'schema_version':1,'private_format':'PS2VEH01','runtime_replacement':'NOT_IMPLEMENTED',
        'proprietary_data_committed':False,'models':rows}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--ps2-root',type=Path,required=True)
    parser.add_argument('--family',action='append');args=parser.parse_args()
    report=prepare(args.ps2_root,args.family)
    output=PORT/'docs/vehicle-model-port1/private-model-preparation.json'
    output.write_text(json.dumps(report,indent=2)+'\n')
