"""Exact source-face trim masks. Writes compact metadata only, never assets."""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, itertools, json, struct, sys
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]; ROOT=PORT.parents[1]
sys.path.insert(0,str(ROOT.parent/'master-rallye-re-course/src'))
from master_rallye.dx import parse_dx
PC_SHA='e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f'
ASSET_SHA='a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac'
TOL=.001

def face_hash(face):
    words=[tuple(struct.unpack('<I',struct.pack('<f',0.0 if v==0 else v))[0] for v in p) for p in face]
    return hashlib.sha256(b''.join(struct.pack('<3I',*p) for p in sorted(words))).hexdigest()

def matches(a,b):
    return any(all(abs(a[i][k]-b[order[i]][k])<=TOL for i in range(3) for k in range(3)) for order in itertools.permutations(range(3)))

def runtime_categories(rows,current):
    """Order-independent, exact original float32 keys and multiplicities."""
    expected=Counter({r['hash']:r['multiplicity'] for r in rows})
    if Counter(current)!=expected:return None
    by_hash={r['hash']:r['category'] for r in rows}
    return [by_hash[h] for h in current]

def generate(pc_path=None,asset_path=None):
    pc_path=pc_path or ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/car.dx'
    asset_path=asset_path or PORT/'.assets/vehicles/XTRAIL-CAR.ps2model'
    if hashlib.sha256(pc_path.read_bytes()).hexdigest()!=PC_SHA:raise ValueError('PC source drift')
    raw=asset_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ASSET_SHA:raise ValueError('Private CAR conversion drift')
    magic,version,jlen,nmesh,nvert,nidx,ntx,source=struct.unpack_from('<8s6I32s',raw)
    if magic!=b'PS2MDL02' or version!=2:raise ValueError('Asset version')
    meta=json.loads(raw[64:64+jlen]); at=64+jlen
    meshes=[struct.unpack_from('<7I',raw,at+i*28) for i in range(nmesh)];at+=28*nmesh
    vertices=[struct.unpack_from('<3f',raw,at+i*36) for i in range(nvert)];at+=36*nvert
    indices=struct.unpack_from('<%dI'%nidx,raw,at)
    ps={}
    for i,m in enumerate(meshes):
        ids=indices[m[5]:m[5]+m[6]]
        ps[i]=[tuple(vertices[j] for j in ids[k:k+3]) for k in range(0,len(ids),3)]
    model=parse_dx(pc_path); pc={}
    for d in model.physical_draws:
        ids=model.draw_global_indices(d)
        pc[d.draw_index]=[tuple(model.vertices.positions[j] for j in ids[k:k+3]) for k in range(0,len(ids),3)]
    selections={2:{},15:{},18:{}};records={};all_used=set()
    for record in (1,2,3,17):
        rows=[]
        for face_ordinal,face in enumerate(pc[record]):
            found=[(root,i) for root in selections for i,pface in enumerate(ps[root]) if matches(face,pface)]
            if len(found)>1:raise ValueError('Ambiguous PS2 face ownership')
            label='KEEP_NATIVE'
            if found:
                root,i=found[0];key=(root,i)
                if key in all_used:raise ValueError('PS2 face multiply claimed')
                all_used.add(key); selections[root].setdefault(record,[]).append(i);label='PS2_ROOT_%d'%root
            rows.append({'pc_face':face_ordinal,'hash':face_hash(face),'category':label,'ps2_face':found[0][1] if found else None})
        table={}
        for r in rows:
            e=table.setdefault(r['hash'],{'hash':r['hash'],'category':r['category'],'multiplicity':0})
            if e['category']!=r['category']:raise ValueError('Conflicting runtime hash category')
            e['multiplicity']+=1
        records[str(record)]={'face_count':len(rows),'categories':dict(Counter(r['category'] for r in rows)), 'faces':rows,'runtime_hash_categories':sorted(table.values(),key=lambda r:r['hash'])}
    expected={2:{1:14,2:28,3:8},15:{2:6,17:2},18:{17:2}}
    if {r:{p:len(ids) for p,ids in maps.items()} for r,maps in selections.items()}!=expected:raise ValueError('Source mask coverage drift')
    for root,maps in selections.items():
        if sorted(i for ids in maps.values() for i in ids)!=list(range(len(ps[root]))):raise ValueError('PS2 root coverage incomplete')
    return {'schema_version':1,'pc_sha256':PC_SHA,'private_asset_sha256':ASSET_SHA,'ps2_source_sha256':source.hex(),'tolerance':TOL,'match_rule':'ALL_VERTEX_PERMUTATIONS_MAX_COMPONENT_DISTANCE_LE_TOL_UNIQUE_SOURCE_FACE','coordinate_transform':'IDENTITY_MODEL_LOCAL','ps2_masks':selections,'records':records,'runtime_admission':'REQUIRES_CURRENT_OWNER_RESOURCE_GENERATION_AND_FULL_RECORD_SIGNATURE','pc17_native_faces':38}

if __name__=='__main__':
    report=generate();HERE.joinpath('masks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['ps2_masks']))
