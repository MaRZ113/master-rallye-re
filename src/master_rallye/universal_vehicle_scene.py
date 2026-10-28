"""Versioned source-only vehicle scene. No MR authoring or donor substitution.

Geometry arrays and local matrices remain in source units. Normalization is a
separate evidenced reversible matrix. Sidecars are private, hash checked and
bounded; source-root contents are never opened for writing.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

SCHEMA = 'universal-vehicle-scene/1'
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_OUTPUT_BYTES = 128 * 1024 * 1024
MAX_VERTICES = 200000
MAX_TRIANGLES = 400000
MAX_TEXTURE_BYTES = 64 * 1024 * 1024
IDENTITY = [1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unlinked(path: Path) -> None:
    for part in (path.absolute(), *path.absolute().parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(),'st_file_attributes',0) & 0x400):
            raise ValueError('linked/reparse path component rejected')


def relative_name(value: str) -> str:
    if not isinstance(value,str) or not value or '\\' in value or ':' in value or '\0' in value:
        raise ValueError('unsafe sidecar path')
    p=PurePosixPath(value)
    if p.is_absolute() or any(v in ('','.','..') for v in value.split('/')):
        raise ValueError('unsafe sidecar path')
    for part in p.parts:
        if part.rstrip(' .')!=part or any(ord(c)<32 or c in '<>"|?*'for c in part)or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',part,re.I):
            raise ValueError('unsafe Windows sidecar component')
    return p.as_posix()


def read_bounded(path: Path, limit: int) -> bytes:
    unlinked(path)
    before=path.stat()
    if not path.is_file() or before.st_size>limit:
        raise ValueError('input type/byte budget exceeded')
    with path.open('rb') as stream: data=stream.read(limit+1)
    after=path.stat()
    if len(data)>limit or len(data)!=before.st_size or (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('input changed during read or exceeds budget')
    return data


def canonical(value) -> bytes:
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')


def load_json(raw: bytes):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate JSON object key')
            result[key]=value
        return result
    def constant(_value):raise ValueError('non-finite JSON constant')
    def floating(value):
        result=float(value)
        if not math.isfinite(result):raise ValueError('non-finite JSON number')
        return result
    try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant,parse_float=floating)
    except (UnicodeError,json.JSONDecodeError) as error:raise ValueError('invalid scene JSON')from error


def number(value) -> bool:
    return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value)


def vector(value, size):
    if not isinstance(value,list) or len(value)!=size or not all(number(v) for v in value):
        raise ValueError('invalid finite vector')


def matrix(value):
    vector(value,16)
    if value[12:] != [0,0,0,1]: raise ValueError('only affine source transforms supported')
    det=determinant(value)
    if not math.isfinite(det)or abs(det)<1e-12: raise ValueError('singular/non-finite transform determinant')


def determinant(m):
    return m[0]*(m[5]*m[10]-m[6]*m[9])-m[1]*(m[4]*m[10]-m[6]*m[8])+m[2]*(m[4]*m[9]-m[5]*m[8])


def transform_point(m,p):
    return [sum(m[row*4+k]*p[k] for k in range(3))+m[row*4+3] for row in range(3)]


def multiply(a,b):
    return [sum(a[r*4+k]*b[k*4+c] for k in range(4)) for r in range(4) for c in range(4)]


def _ids(records,label,max_count=4096):
    if not isinstance(records,list) or len(records)>max_count: raise ValueError(label+' count budget')
    result={}
    for row in records:
        if not isinstance(row,dict):raise ValueError(label+' record must be an object')
        key=row.get('id')
        if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}',key) or key in result:
            raise ValueError('invalid/duplicate '+label+' ID')
        result[key]=row
    return result


def _hash(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('sidecar hash missing')


def _size(value,limit=MAX_OUTPUT_BYTES):
    if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<=limit:raise ValueError('sidecar byte budget')


def _paths(names):
    seen=set()
    for name in names:
        relative_name(name);key=name.casefold()
        if key in seen:raise ValueError('duplicate/case-aliased sidecar path')
        seen.add(key)
    for name in seen:
        if any(parent.as_posix()in seen for parent in PurePosixPath(name).parents if parent.as_posix()!='.'):
            raise ValueError('sidecar file/directory collision')


def _bindings(scene):
    """Declared private content must remain bound independently of the manifest."""
    result=[]
    for tex in scene['textures']:
        result.append((tex['rgba_path'],tex['width']*tex['height']*4,tex['rgba_sha256']))
        channels=tex['source_channels']
        sample_keys=('raw_samples_path','raw_sample_bytes','raw_samples_sha256')
        if any(key in channels for key in sample_keys):
            path=relative_name(channels.get('raw_samples_path'));size=channels.get('raw_sample_bytes');_size(size,MAX_TEXTURE_BYTES);_hash(channels.get('raw_samples_sha256'))
            spp=channels.get('samples_per_pixel')
            if not isinstance(spp,int) or isinstance(spp,bool) or not 1<=spp<=16 or size!=tex['width']*tex['height']*spp:
                raise ValueError('raw texture sample/channel size mismatch')
            result.append((path,size,channels['raw_samples_sha256']))
        palette_size=channels.get('palette_bytes',0);_size(palette_size,MAX_TEXTURE_BYTES)
        if palette_size:
            path=relative_name(channels.get('palette_path'));_hash(channels.get('palette_sha256'))
            result.append((path,palette_size,channels['palette_sha256']))
        elif channels.get('palette_path')is not None or channels.get('palette_sha256')is not None:
            raise ValueError('empty palette has a sidecar/hash claim')
    resources=scene['source'].get('resources',[])
    if not isinstance(resources,list) or len(resources)>4096:raise ValueError('source resource count budget')
    by_member={};snapshots=[]
    for row in resources:
        if not isinstance(row,dict):raise ValueError('source resource record required')
        path=relative_name(row.get('snapshot_path'));_size(row.get('bytes'));_hash(row.get('sha256'))
        member=relative_name(row.get('member'))
        if member.casefold()in by_member:raise ValueError('duplicate source member identity')
        by_member[member.casefold()]=row;snapshots.append(path)
        result.append((path,row['bytes'],row['sha256']))
    _paths(snapshots)
    if 'resources'in scene['source']:
        for mesh in scene['meshes']:
            claim=mesh['source'];member=claim.get('member')
            if member is not None or 'member_sha256'in claim:
                expected=by_member.get(relative_name(member).casefold())
                if expected is None or claim.get('member_sha256')!=expected['sha256']:
                    raise ValueError('mesh source provenance is not bound to original resource')
        for tex in scene['textures']:
            claim=tex.get('source')
            if claim is not None:
                if not isinstance(claim,dict):raise ValueError('texture source provenance object required')
                expected=by_member.get(relative_name(claim.get('member')).casefold())
                if expected is None or any(claim.get(key)!=expected[key]for key in ('snapshot_path','bytes','sha256')):
                    raise ValueError('texture source provenance is not bound to original resource')
    return result


def validate_scene(scene: dict) -> dict:
    if not isinstance(scene,dict) or scene.get('schema')!=SCHEMA: raise ValueError('unsupported scene schema')
    if not isinstance(scene.get('source'),dict) or not isinstance(scene.get('metadata'),dict): raise ValueError('source/metadata required')
    root=scene['source'].get('root')
    if not isinstance(root,str) or not root or len(root)>4096 or any(ord(c)<32 for c in root) or not Path(root).is_absolute():
        raise ValueError('absolute source root metadata required')
    protected=scene['source'].get('protected_roots',[])
    if not isinstance(protected,list)or len(protected)>256 or any(not isinstance(p,str)or not p or any(ord(c)<32 for c in p)or not Path(p).is_absolute()for p in protected):
        raise ValueError('invalid protected root metadata')
    if not isinstance(scene.get('unknown_semantics'),list): raise ValueError('unknown semantics must remain explicit')
    coord=scene.get('coordinate_system',{})
    if not isinstance(coord,dict):raise ValueError('coordinate system object required')
    if not coord.get('interpretation_status') or not coord.get('evidence'): raise ValueError('coordinate interpretation requires evidence')
    matrix(coord.get('source_to_normalized'))
    meshes=_ids(scene.get('meshes'),'mesh');nodes=_ids(scene.get('nodes'),'node')
    materials=_ids(scene.get('materials'),'material');textures=_ids(scene.get('textures'),'texture',256)
    if not meshes or not nodes: raise ValueError('empty scene')
    texture_bytes=0
    for tex in textures.values():
        width,height=tex.get('width'),tex.get('height')
        if not all(isinstance(v,int) and not isinstance(v,bool) and 1<=v<=4096 for v in (width,height)):
            raise ValueError('texture dimension budget')
        texture_bytes+=width*height*4
        relative_name(tex.get('rgba_path'))
        _hash(tex.get('rgba_sha256'))
        if not isinstance(tex.get('source_channels'),dict): raise ValueError('original channel metadata required')
    if texture_bytes>MAX_TEXTURE_BYTES: raise ValueError('aggregate texture budget')
    for mat in materials.values():
        if not isinstance(mat.get('diffuse_texture_id'),str)or mat['diffuse_texture_id'] not in textures: raise ValueError('missing material texture')
        if 'bump_texture_id'in mat and (not isinstance(mat['bump_texture_id'],str)or mat['bump_texture_id']not in textures):raise ValueError('missing bump texture')
        if not isinstance(mat.get('raw_fields'),list) or not isinstance(mat.get('unsupported'),list):raise ValueError('raw material/unknowns required')
    nv=nt=animated_vertices=0
    for mesh in meshes.values():
        ps,ns,uv,tri=(mesh.get(k) for k in ('positions','normals','uvs','triangles'))
        if not all(isinstance(v,list) for v in (ps,ns,uv,tri)):raise ValueError('mesh arrays required')
        nv+=len(ps);nt+=len(tri)
        if nv>MAX_VERTICES or nt>MAX_TRIANGLES:raise ValueError('aggregate geometry budget')
        if not ps or len(ns)!=len(ps) or len(uv)!=len(ps): raise ValueError('incomplete position/normal/UV association')
        for row in ps:vector(row,3)
        for row in ns:vector(row,3)
        for row in uv:vector(row,2)
        for face in tri:
            if not isinstance(face,list) or len(face)!=3 or any(not isinstance(i,int) or isinstance(i,bool) or not 0<=i<len(ps) for i in face):
                raise ValueError('invalid geometry/UV vertex index')
        if not isinstance(mesh.get('material_id'),str)or mesh['material_id'] not in materials:raise ValueError('missing mesh material')
        if not isinstance(mesh.get('source'),dict):raise ValueError('geometry provenance required')
        frames=mesh.get('animation_frames',[])
        if not isinstance(frames,list) or len(frames)>256:raise ValueError('animation frame budget')
        for frame in frames:
            if not isinstance(frame,list) or len(frame)!=len(ps):raise ValueError('animation frame shape')
            animated_vertices+=len(frame)
            if animated_vertices>MAX_VERTICES:raise ValueError('aggregate animation allocation budget')
            for vertex in frame:vector(vertex,8)
    for node in nodes.values():
        parent=node.get('parent_id')
        if parent is not None and (not isinstance(parent,str)or parent not in nodes): raise ValueError('missing parent node')
        if not isinstance(node.get('mesh_ids'),list) or any(not isinstance(i,str)or i not in meshes for i in node['mesh_ids']):raise ValueError('missing node mesh')
        if type(node.get('visible')) is not bool or type(node.get('source_visible')) is not bool:raise ValueError('explicit visibility required')
        matrix(node.get('local_transform'))
        if node.get('source_local_transform') is not None:matrix(node['source_local_transform'])
        if not node.get('transform_evidence'):raise ValueError('transform evidence required')
        seen=set();key=node['id']
        while key is not None:
            if key in seen or len(seen)>128:raise ValueError('node hierarchy cycle/depth')
            seen.add(key);key=nodes[key].get('parent_id')
    _bindings(scene)
    return {'meshes':len(meshes),'nodes':len(nodes),'vertices':nv,'triangles':nt,'texture_bytes':texture_bytes}


def output_directory(output: Path, protected_roots=()) -> Path:
    output=Path(output).absolute();unlinked(output);target=output.resolve()
    for root in protected_roots:
        root=Path(root).resolve()
        if target==root or target.is_relative_to(root) or root.is_relative_to(target):
            raise ValueError('output overlaps protected source/tool root')
    if output.exists():raise ValueError('output must be a fresh directory')
    return output


def save_scene(scene: dict, output: Path, assets: dict[str,bytes], *, protected_roots=()) -> dict:
    counts=validate_scene(scene)
    output=output_directory(output,[*protected_roots,scene['source']['root'],*scene['source'].get('protected_roots',[])])
    encoded=canonical(scene)
    if len(encoded)>MAX_JSON_BYTES:raise ValueError('scene JSON budget')
    if not isinstance(assets,dict)or len(assets)>1023:raise ValueError('sidecar count budget')
    _paths(['scene.json','manifest.json',*assets])
    total=len(encoded)
    for name,blob in assets.items():
        relative_name(name)
        if not isinstance(blob,bytes):raise ValueError('sidecars must be exact bytes')
        total+=len(blob)
    if total>MAX_OUTPUT_BYTES:raise ValueError('aggregate scene output budget')
    for name,size,digest in _bindings(scene):
        data=assets.get(name)
        if data is None or len(data)!=size or sha(data)!=digest:
            raise ValueError('texture channels/sidecar hash mismatch')
    files={'scene.json':encoded,**assets}
    manifest={'schema':'universal-vehicle-scene-manifest/1','scene_sha256':sha(encoded),
              'files':{name:{'bytes':len(blob),'sha256':sha(blob)}for name,blob in sorted(files.items())}}
    manifest_blob=canonical(manifest)
    if total+len(manifest_blob)>MAX_OUTPUT_BYTES:raise ValueError('manifest output budget')
    output.mkdir(parents=True,exist_ok=False)
    for name,blob in files.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(blob)
    with (output/'manifest.json').open('xb')as stream:stream.write(manifest_blob)
    return {'scene':str(output/'scene.json'),'manifest':str(output/'manifest.json'),
            'scene_sha256':sha(encoded),'manifest_sha256':sha(manifest_blob),'counts':counts,'output_bytes':total+len(manifest_blob)}


def load_scene(path: Path) -> dict:
    path=Path(path);root=path.parent;raw=read_bounded(path,MAX_JSON_BYTES)
    scene=load_json(raw);validate_scene(scene)
    manifest=load_json(read_bounded(root/'manifest.json',2*1024*1024))
    if not isinstance(manifest,dict)or manifest.get('schema')!='universal-vehicle-scene-manifest/1' or manifest.get('scene_sha256')!=sha(raw):
        raise ValueError('scene manifest/hash mismatch')
    files=manifest.get('files')
    if not isinstance(files,dict) or len(files)>1024 or 'scene.json' not in files:raise ValueError('manifest file count')
    _paths([*files,'manifest.json'])
    if not isinstance(files['scene.json'],dict)or files['scene.json'].get('sha256')!=sha(raw)or files['scene.json'].get('bytes')!=len(raw):raise ValueError('unbound scene file')
    total=0
    for name,row in files.items():
        relative_name(name)
        if not isinstance(row,dict):raise ValueError('sidecar manifest record required')
        size=row.get('bytes')
        _size(size);_hash(row.get('sha256'))
        total+=size
        if total>MAX_OUTPUT_BYTES:raise ValueError('aggregate reopen byte budget')
        data=read_bounded(root/name,size)
        if len(data)!=size or sha(data)!=row.get('sha256'):raise ValueError('sidecar size/hash mismatch')
    for name,size,digest in _bindings(scene):
        row=files.get(name,{})
        if row.get('bytes')!=size or row.get('sha256')!=digest:
            raise ValueError('unbound texture sidecar')
    return scene
