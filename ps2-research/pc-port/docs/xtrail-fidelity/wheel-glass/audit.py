"""Bounded read-only Xtrail CAR/WHEEL source join and F10 layout audit.

No original geometry is output. F10 ordinals/pointers are observation only;
current buffer bytes are required separately for runtime admission.
"""
from collections import Counter, defaultdict
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
TOL = .001


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recommendation(shader, secondary):
    if shader == 'carglass': return 'GLASS_DISTINCT_FROM_BODY_ENVIRONMENT'
    if shader == 'carshiny' and 'rubber' in secondary.lower(): return 'KEEP_AUTHORED_RUBBER_MAP_NO_BODY_ENV_OVERRIDE'
    if shader == 'carshiny': return 'VERIFIED_ENVIRONMENT_MATERIAL_CURRENT_IDENTITY_REQUIRED'
    if shader == 'carflat': return 'FLAT_DISTINCT_FROM_BODY_ENVIRONMENT'
    return 'UNKNOWN_KEEP_STOCK'


def digest_values(values):
    return hashlib.sha256(b''.join(struct.pack('<f', 0. if value == 0 else value)
                                  for vector in values for value in vector)).hexdigest()


def ordered_runs(labels):
    result=[]
    for face,label in enumerate(labels):
        if not result or result[-1]['category']!=label:
            result.append({'first_source_face':face,'source_faces':1,'category':label})
        else:result[-1]['source_faces']+=1
    return result


def main():
    a = load('xtrail_source_common', PORT/'docs/full-coverage/vehicles/audit.py')
    complete = load('xtrail_exact_trailer', PORT/'docs/vehicle-model-port1/ps2-format-lights/complete_reader.py')
    import psbtool
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2/'TNG.PAK')
    report = {'schema_version':1,'tolerance':TOL,'coordinate_frame':'MODEL_LOCAL_GAME_SOURCE',
              'evidence_grade':'CONFIRMED_BY_BYTES','runtime_identity':'CURRENT_GEOMETRY_HASH_NOT_PRESENT_IN_F10',
              'models':[], 'texture_resources':[], 'live_layout_observations':[]}
    for kind in ('CAR','WHEEL'):
        entry = next(e for e in manifest['entries'] if e['path'].upper().endswith('XTRAIL\\'+kind+'.PSM'))
        payload, provenance = a.t.read_payload(entry, a.PS2/'TNG.000')
        scene, trailer = complete.decode_complete(payload)
        pc_path = a.PC/'Xtrail'/(kind.lower()+'.dx')
        pc = a.parse_dx(pc_path)
        item = {'kind':kind,'ps2_path':entry['path'],'ps2_sha256':a.sha(payload),
                'ps2_provenance':provenance,'pc_path':'Xtrail/'+pc_path.name,
                'pc_sha256':a.sha(pc_path.read_bytes()),'trailer':trailer,'meshes':[], 'draws':[]}
        report['models'].append(item)
        index = defaultdict(list)
        for mesh in scene.meshes:
            slots = a.slot(mesh)
            contract = a.r.material_contract(mesh['material'],slots[1] if len(slots)>1 else '')
            fs, controls = a.w.mesh_triangles(scene,mesh)
            meta = {'path':mesh['path'],'node_offset':mesh['node_offset'],'material_offset':mesh['material_offset'],
                    'material':mesh['material'],'slots':slots,'mode':contract['mode'],
                    'effective_secondary':contract['effective_secondary'],
                    'shader':contract['interned_shader'],'rubber_preserved':contract['rubber_substring_preserved'],
                    'source_faces':len(fs),'conditional':mesh['path'].count('.')>1,
                    'recommendation':recommendation(contract['interned_shader'],slots[1] if len(slots)>1 else '')}
            item['meshes'].append(meta)
            for strip in mesh['strips']:
                for newest in range(strip['start']+2,strip['start']+strip['count']):
                    if scene.control(newest)&1:continue
                    ids=(newest-2,newest-1,newest)
                    face=tuple(scene.position(i) for i in ids)
                    if a.w.area_normal(face)[0]<=1e-7:continue
                    for key in {tuple(int(v//TOL) for v in point) for point in face}:
                        index[key].append((meta,ids,face))
        for draw in pc.physical_draws:
            fs=a.faces(pc,draw); ids=pc.draw_global_indices(draw); bindings={}; labels=[]
            for ordinal,face in enumerate(fs):
                key=tuple(int(v//TOL) for v in face[0]); found={}
                for delta in itertools.product((-1,0,1),repeat=3):
                    for meta,pids,candidate in index.get(tuple(key[i]+delta[i] for i in range(3)),()):
                        if a.w.corner_error(face,candidate)>TOL:continue
                        pindices=ids[ordinal*3:ordinal*3+3]; permutations=[]
                        for perm in itertools.permutations(range(3)):
                            if max(abs(face[i][k]-candidate[perm[i]][k]) for i in range(3) for k in range(3))>TOL:continue
                            nr=ur=0.
                            for corner in range(3):
                                normal=struct.unpack_from('<3f',payload,32+pids[perm[corner]]*52)
                                uv=struct.unpack_from('<2f',payload,32+pids[perm[corner]]*52+20)
                                nr=max(nr,max(abs(pc.vertices.normals[pindices[corner]][k]-normal[k]) for k in range(3)))
                                ur=max(ur,max(abs(pc.uv_sets[0].values[pindices[corner]][k]-uv[k]) for k in range(2)))
                            permutations.append((nr,ur))
                        residual=min(permutations)
                        found[meta['path']] = (meta,residual)
                categories={value[0]['recommendation'] for value in found.values()}
                labels.append(next(iter(categories)) if len(categories)==1 else 'AMBIGUOUS' if categories else 'UNMATCHED')
                for path,(meta,(nr,ur)) in found.items():
                    if path not in bindings:bindings[path]={'mesh':meta,'matched_source_faces':set(),'normal_max_abs':0.,'uv_max_abs':0.}
                    row=bindings[path];row['matched_source_faces'].add(ordinal)
                    row['normal_max_abs']=max(row['normal_max_abs'],nr);row['uv_max_abs']=max(row['uv_max_abs'],ur)
            for row in bindings.values():row['matched_source_faces']=len(row['matched_source_faces'])
            vertices=sorted(set(ids))
            item['draws'].append({'source_draw':draw.draw_index,'record_path':draw.record_path,'record_offset':draw.offset,
                'vertex_base':draw.vertex_base,'vertex_count':draw.local_vertex_max+1,'index_start':draw.index_start,
                'index_count':draw.index_count,'triangles':len(fs),'geometry_sha256':a.geometry_signature(fs),
                'slots':[s.value for s in draw.texture_slots],'flags_hex':draw.flags_0x20.hex(),
                'bounds':{'min':[min(p[i] for f in fs for p in f)for i in range(3)],'max':[max(p[i] for f in fs for p in f)for i in range(3)]},
                'source_normal_sha256':digest_values(pc.vertices.normals[i] for i in vertices),
                'source_uv0_sha256':digest_values(pc.uv_sets[0].values[i] for i in vertices),
                'source_alpha_values':sorted({pc.vertices.colors[i*4+3] for i in vertices}),
                'categories':dict(sorted(Counter(labels).items())),'source_ordered_runs':ordered_runs(labels),
                'bindings':list(bindings.values())})
            if kind=='CAR' and draw.draw_index==13:
                table=defaultdict(set)
                for i in vertices:
                    key=digest_values([pc.vertices.positions[i]])
                    table[key].add(tuple(pc.vertices.normals[i]))
                item['decal_normal_augmentation']={'source':'Original PC DX normals validated against PS2 root.14',
                    'normal_max_abs_to_ps2':max(b['normal_max_abs'] for b in bindings.values()),
                    'entries':[{'pc_xyz_sha256':key,'normal':list(next(iter(normals)))} for key,normals in sorted(table.items()) if len(normals)==1],
                    'ambiguous_positions':sum(len(normals)!=1 for normals in table.values()),
                    'runtime_gate':'Require exact current whole geometry, source-compatible UV0/diffuse, same owned race transform and current resource generations; F10 lacks uploaded UV/diffuse bytes'}
    selected = {d['geometry_sha256'] for item in report['models'] for d in item['draws']
                if item['kind']=='WHEEL' or d['source_draw'] in (10,13,21,22)}
    counts = {d['index_count'] for item in report['models'] for d in item['draws']
              if item['kind']=='WHEEL' or d['source_draw'] in (10,13,21,22)}
    hits = {key:[] for key in sorted(selected)}
    files = list(sorted(a.PC.glob('*/*.dx')))
    for path in files:
        other = a.parse_dx(path)
        for draw in other.physical_draws:
            if draw.index_count not in counts:continue
            key = a.geometry_signature(a.faces(other,draw))
            if key in hits:hits[key].append({'path':str(path.relative_to(a.PC)).replace('\\','/'),'draw':draw.draw_index,
                                            'slots':[s.value for s in draw.texture_slots]})
    report['negative_controls'] = {'pc_files':len(files),'exact_geometry_hits':hits,
                                  'policy':'Exact keys unique in examined 78-file corpus. This bounded source uniqueness is not a live wheel owner, transform or resource-lifetime capture.'}
    for entry in manifest['entries']:
        name=entry['path'].replace('\\','/').upper()
        if '/COMMONTEXTURES/' not in name or not any(name.endswith('/'+x+'.GXI') for x in ('JUMPWHEEL64-TGA','XWHEEL-TGA','MERCWHEEL643-TGA','WINDSCREEN32-TGA','LIGHTS-TGA','MASTERSTICKER069-TGA')):continue
        payload, provenance=a.t.read_payload(entry,a.PS2/'TNG.000')
        report['texture_resources'].append({'path':entry['path'],'provenance':provenance,**psbtool.parse_gxi(payload)})
    LOGS=Path(r'D:/Game/Master Rallye Pristine/MRRRenderer/logs')
    for name in ('frame-27240-d1-00008422.jsonl','frame-4888-d1-00001274.jsonl'):
        raw=(LOGS/name).read_bytes()
        file={'name':name,'sha256':a.sha(raw),'size':len(raw),'records':[]}
        report['live_layout_observations'].append(file)
        for line in raw.decode('utf8').splitlines():
            row=json.loads(line); args=row.get('arguments',[])
            if row.get('type')!='draw' or row.get('method')!='DrawIndexedPrimitive' or len(args)<5 or (args[2],args[4]) not in ((20,14),(22,18),(30,28),(18,14)):continue
            state=row['state']; rs=state.get('render_states',{}); stages=state.get('texture_stage_states',[])[:2]
            file['records'].append({'frame':row.get('frame'),'capture_draw_ordinal':row.get('draw_index'),
                'arguments':args[:5],'caller_rva':row.get('caller',{}).get('return_rva'),
                'fvf':state.get('vertex_shader'),'stream0':state.get('streams',[None])[0],'indices':state.get('indices'),
                'texture_generations':[x.get('last_creation_serial') for x in state.get('textures',[])[:2]],
                'native_states':{k:rs.get(k) for k in ('7','14','15','23','27','19','20','137')},
                'stages':[{k:s.get(k) for k in ('1','2','3','4','5','6','11','24')} for s in stages],
                'qualification':'LAYOUT_CORRELATION_ONLY_NOT_RUNTIME_GEOMETRY_HASH'})
    (HERE/'source-evidence.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf8')
    print('Wrote',len(report['models']),'models and',sum(len(x['records'])for x in report['live_layout_observations']),'bounded layout rows')


if __name__=='__main__':main()
