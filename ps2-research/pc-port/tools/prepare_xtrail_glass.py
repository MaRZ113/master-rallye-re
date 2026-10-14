"""Prepare exactly one verified X-Trail headlight cover; original content ignored."""
from pathlib import Path
import hashlib,importlib.util,itertools,json,struct,sys
PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
sys.path[:0]=[str(ROOT/'ps2-research/tools'),r'D:/Game/Master Rallye/master-rallye-re-course/src']
import tngtool as t,water_runtime as w,reflection_runtime as r,psbtool as p
from master_rallye.dx import parse_dx
HEADER=struct.Struct('<8s4I');ENTRY=struct.Struct('<32s3f2fI3f2fI')
MAGIC=b'XGLASS01'
def sha(b):return hashlib.sha256(b).hexdigest()
def packed(v):return struct.pack('<%df'%len(v),*(0. if x==0 else x for x in v))
def main():
    ps2=Path(r'D:/Game/Master Rallye PS2');w.verify_inputs(ps2)
    manifest,_=t.load_pak(ps2/'TNG.PAK')
    def extract(path):
        es=[e for e in manifest['entries'] if e['kind']=='file' and e['path'].upper()==path.upper()]
        if len(es)!=1:raise ValueError('Nonunique/missing canonical resource')
        raw,prov=t.read_payload(es[0],ps2/'TNG.000');return raw,prov
    raw,prov=extract(r'\TNG\DATAPSM\VEHICLES\XTRAIL\CAR.PSM');scene=r.decode_vehicle(raw)
    evidence=json.loads((PORT/'docs/xtrail-fidelity/wheel-glass/source-evidence.json').read_text())['models'][0]
    if sha(raw)!=evidence['ps2_sha256']:raise ValueError('Original PSM drift')
    dx=Path(r'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/car.dx')
    if t.file_hash(dx)!=evidence['pc_sha256']:raise ValueError('Original DX drift')
    model=parse_dx(dx);draw=model.physical_draws[10]
    mesh=next(m for m in scene.meshes if m['path']=='root.19')
    source_ids=set(i for st in mesh['strips'] for i in range(st['start'],st['start']+st['count']))
    entries=[]
    for i in sorted(set(model.draw_global_indices(draw))):
        ids=[j for j in source_ids if max(abs(model.vertices.positions[i][k]-scene.position(j)[k]) for k in range(3))<=.001]
        attrs={(*struct.unpack_from('<3f',raw,32+j*52),*struct.unpack_from('<2f',raw,32+j*52+20),struct.unpack_from('<I',raw,32+j*52+16)[0]) for j in ids}
        if len(attrs)!=1:raise ValueError('Ambiguous original glass attributes')
        nx,ny,nz,u,v,rgba=next(iter(attrs));color=((rgba&255)<<24)|(rgba>>8)
        pc_color=bytes(model.vertices.colors[i*4:i*4+4])
        if pc_color[0]!=pc_color[1] or pc_color[1]!=pc_color[2]:raise ValueError('PC color channel order needs proof')
        entries.append(ENTRY.pack(hashlib.sha256(packed(model.vertices.positions[i])).digest(),
            *model.vertices.normals[i],*model.uv_sets[0].values[i],struct.unpack('<I',pc_color)[0],nx,ny,nz,u,v,color))
    entries.sort(key=lambda e:e[:32])
    if len(entries)!=22 or len({x[:32] for x in entries})!=22:raise ValueError('Unexpected headlight ownership')
    primary,pp=extract(r'\TNG\DATAPSM\COMMONTEXTURES\WINDSCREEN32-TGA.GXI')
    highlight,hp=extract(r'\TNG\DATAPSM\COMMONTEXTURES\WINDSCREEN-REFLECT.GXI')
    pt=p.parse_gxi(primary);ht=p.parse_gxi(highlight)
    if (pt['width'],pt['height'])!=(16,16) or (ht['width'],ht['height'])!=(32,32):raise ValueError('Unexpected image format')
    asset=HEADER.pack(MAGIC,1,22,len(primary),len(highlight))+b''.join(entries)+primary+highlight
    out=PORT/'.assets/vehicles/XtrailHeadlight.ps2glass';out.parent.mkdir(parents=True,exist_ok=True)
    for at in (out,out.parent,out.parent.parent):
        if at.is_symlink() or getattr(at,'is_junction',lambda:False)():raise ValueError('Linked output')
    if out.exists() and out.read_bytes()!=asset:raise ValueError('Refusing conflicting existing private artifact')
    out.write_bytes(asset)
    docs=PORT/'docs/xtrail-lights-model';docs.mkdir(parents=True,exist_ok=True)
    report={'schema_version':1,'asset_sha256':sha(asset),'asset_size':len(asset),'geometry_sha256':evidence['draws'][10]['geometry_sha256'],
        'pc_source_sha256':evidence['pc_sha256'],'ps2_source_sha256':sha(raw),'source_owner':'root.19',
        'source_faces':18,'source_vertices':22,'primary':pt,'primary_provenance':pp,'highlight':ht,'highlight_provenance':hp,
        'runtime_validation':'NOT_PERFORMED','alpha_rule':'Primary stored alpha unchanged; D3D8 /255 vs PS2 /128 sampling is an approximation',
        'highlight_rule':'RGB *96/128, original alpha not blend weight','private_output':out.relative_to(PORT).as_posix()}
    (docs/'glass-source.json').write_text(json.dumps(report,indent=2)+'\n')
    (PORT/'renderer/xtrail_glass_identity.hpp').write_text('#pragma once\nnamespace gfx2::ps2port {\ninline constexpr char kXtrailGlassAssetSha[]="'+sha(asset)+'";\ninline constexpr char kXtrailGlassGeometrySha[]="'+report['geometry_sha256']+'";\n}\n')
    print(json.dumps({'asset_bytes':len(asset),'sha256':sha(asset),'vertices':22,'faces':18}))
if __name__=='__main__':main()
