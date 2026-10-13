"""Full read-only vehicle source join; compact metadata only, no asset output."""
from pathlib import Path
import sys, json, hashlib, itertools
ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT/'ps2-research/tools'),str(ROOT/'ps2-research/pc-port/tools'),r'D:/Game/Master Rallye/master-rallye-re-course/src']
import tngtool as t
import reflection_runtime as r
import water_runtime as w
from course_delta import EXPECTED
from prepare_reflection_pilot import geometry_signature
from master_rallye.dx import parse_dx
PS2=Path(r'D:/Game/Master Rallye PS2')
PC=Path(r'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles')
OUT=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
def slot(mesh):return [x['name'].replace('\\','/').split('/')[-1].lower() for x in mesh['textures']]
def faces(model,draw):
    ids=model.draw_global_indices(draw)
    return [tuple(model.vertices.positions[i] for i in ids[n:n+3]) for n in range(0,len(ids),3)]
def index_faces(fs):
    idx={}
    for f in fs:
        for p in f:idx.setdefault(tuple(int(x//.001) for x in p),[]).append(f)
    return idx
def matches(f,idx):
    key=tuple(int(x//.001) for x in f[0])
    return any(w.corner_error(f,g)<=.001 for delta in itertools.product((-1,0,1),repeat=3)
               for g in idx.get(tuple(key[i]+delta[i] for i in range(3)),[]))
def main():
    w.verify_inputs(PS2)
    manifest,_=t.load_pak(PS2/'TNG.PAK')
    entries=sorted((e for e in manifest['entries'] if e['kind']=='file' and '/VEHICLES/' in e['path'].replace('\\','/').upper() and e['path'].upper().endswith('CAR.PSM')),key=lambda e:e['path'])
    pcs={p.name.upper():p for p in sorted(PC.iterdir()) if p.is_dir()}
    report={'schema_version':1,'canonical_inputs':{name:{'size':(PS2/name).stat().st_size,'sha256':digest} for name,digest in EXPECTED.items()},'coordinate_frame':'MODEL_LOCAL_SOURCE','matching_tolerance':.001,'runtime_validation':'NOT_PERFORMED_NEW_CANDIDATES','vehicles':[],'registry':[],'pc_only_families':[], 'negative_controls':{}}
    for e in entries:
        family=e['path'].replace('\\','/').split('/')[-2]
        b,prov=t.read_payload(e,PS2/'TNG.000')
        item={'ps2_family':family,'ps2_source':{'resource':e['path'],'sha256':sha(b),'provenance':prov},'pc_family':None,'meshes':[],'draws':[],'blockers':[]}
        report['vehicles'].append(item)
        try:scene=r.decode_vehicle(b)
        except Exception as error:item['blockers'].append('PSM_DECODER: '+str(error));continue
        indexed=[]
        for m in scene.meshes:
            tx=slot(m);contract=r.material_contract(m['material'],tx[1] if len(tx)>1 else '')
            fs,controls=w.mesh_triangles(scene,m)
            meta={'path':m['path'],'node_offset':m['node_offset'],'material_offset':m['material_offset'],'material':m['material'],'texture_slots':tx,'contract':contract,'triangles':len(fs),'strip_controls':controls}
            item['meshes'].append(meta)
            if contract['interned_shader']=='carshiny' and not contract['rubber_substring_preserved']:
                indexed.append((meta,fs,index_faces(fs)))
        pcdir=pcs.get(family)
        if not pcdir:item['blockers'].append('NO_EXACT_PC_FAMILY_NAME');continue
        item['pc_family']=pcdir.name
        path=pcdir/'car.dx'
        if not path.exists():item['blockers'].append('NO_PC_CAR_DX');continue
        try:model=parse_dx(path)
        except Exception as error:item['blockers'].append('DX_DECODER: '+str(error));continue
        item['pc_source']={'path':str(path.relative_to(PC)).replace('\\','/'),'sha256':sha(path.read_bytes())}
        for draw in model.physical_draws:
            tx=[s.value for s in draw.texture_slots]
            if tx[1] in ('Null','rubber-tga','glass-tga'):continue
            fs=faces(model,draw);h=geometry_signature(fs)
            joined=[]
            for meta,pfs,idx in indexed:
                # Texture references only prefilter an independently tested shape join.
                if tx[:2]!=meta['texture_slots'][:2]:continue
                matched=sum(matches(f,idx) for f in fs)
                if matched:joined.append({'mesh_path':meta['path'],'node_offset':meta['node_offset'],'material_offset':meta['material_offset'],'pc_matching_faces':matched,'pc_faces':len(fs),'ps2_faces':len(pfs),'shader':'carshiny','effective_secondary':meta['contract']['effective_secondary']})
            best=max((j['pc_matching_faces'] for j in joined),default=0)
            accepted=[j for j in joined if j['pc_matching_faces']==len(fs)]
            role='PAINT_BODY' if tx[1] in ('whitepaint-tga','silverpaint-tga') else 'REFLECTIVE_TRIM_OR_OTHER'
            # Named child geometry can be a wheel/driver/LOD alternative; preserve it, fail closed.
            root_accepted=[j for j in accepted if j['mesh_path'].count('.')==1]
            verdict='VERIFIED_COMPATIBLE_SOURCE' if len(root_accepted)==1 and draw.flags_0x20.hex()=='00000101' else 'BLOCKED_SOURCE_JOIN'
            meta={'draw_index':draw.draw_index,'record_path':draw.record_path,'record_offset':draw.offset,'vertex_base':draw.vertex_base,'vertices':draw.local_vertex_max+1,'index_start':draw.index_start,'index_count':draw.index_count,'triangles':len(fs),'texture_slots':tx,'flags_hex':draw.flags_0x20.hex(),'geometry_sha256':h,'role':role,'matches':joined,'status':verdict,'bounds':{'min':[min(p[i] for f in fs for p in f) for i in range(3)],'max':[max(p[i] for f in fs for p in f) for i in range(3)]},'best_matching_faces':best}
            item['draws'].append(meta)
            if verdict=='VERIFIED_COMPATIBLE_SOURCE':report['registry'].append({'vehicle':pcdir.name,**meta,'ps2_source_sha256':sha(b),'pc_source_sha256':item['pc_source']['sha256'],'ps2_binding':root_accepted[0],'evidence_grade':'CONFIRMED_BY_BYTES','activation':'CURRENT_NATIVE_OPAQUE_ENVIRONMENT_STATE_AND_OWNER_GATES_REQUIRED'})
        print(family,len(item['draws']),sum(x['status']=='VERIFIED_COMPATIBLE_SOURCE' for x in item['draws']),flush=True)
    paired={v['pc_family'] for v in report['vehicles'] if v['pc_family']}
    report['pc_only_families']=[p.name for p in sorted(PC.iterdir()) if p.is_dir() and p.name not in paired]
    digests={x['geometry_sha256'] for x in report['registry']};counts={x['index_count'] for x in report['registry']};hits={h:[] for h in sorted(digests)};unsupported=[];checked=0
    for path in sorted(PC.glob('*/*.dx')):
        try:model=parse_dx(path)
        except Exception as error:unsupported.append({'path':str(path.relative_to(PC)),'error':str(error)});continue
        for draw in model.physical_draws:
            if draw.index_count not in counts:continue
            checked+=1;h=geometry_signature(faces(model,draw))
            if h in hits:hits[h].append({'path':str(path.relative_to(PC)).replace('\\','/'),'draw':draw.draw_index,'slots':[s.value for s in draw.texture_slots]})
    for candidate in report['registry']:
        owners=sorted({hit['path'].split('/')[0] for hit in hits[candidate['geometry_sha256']]})
        candidate['signature_owner_families']=owners
        candidate['unique_vehicle_family']=owners==[candidate['vehicle']]
    report['negative_controls']={'files_scanned':len(list(PC.glob('*/*.dx'))),'candidate_count_records_checked':checked,'signature_hits':hits,'unsupported':unsupported,'limitation':'Complete/menu source repeats within the same family are expected; current native semantic owner remains mandatory.'}
    (OUT/'vehicle-coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'registry-candidates.json').write_text(json.dumps([x for x in report['registry'] if x['unique_vehicle_family']],indent=2)+'\n')
if __name__=='__main__':main()
