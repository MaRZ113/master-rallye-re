"""Read-only all-material source joins, including conditional brake-light meshes.

Original strips stay in memory only. Output is counts, hashes and provenance.
No shader guess or activation policy is introduced by this diagnostic.
"""
from pathlib import Path
import collections
import importlib.util
import itertools
import json
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('original_audit', PORT/'docs/full-coverage/vehicles/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
FAMILIES = ('LandCruiser', 'ChevyBlazer', 'Xtrail', 'Bruno', 'SeatBuggy', 'Forester')
TOL = .005


def metadata(mesh):
    slots = a.slot(mesh)
    contract = a.r.material_contract(mesh['material'], slots[1] if len(slots)>1 else '')
    maps={r['slot']:r for r in mesh['textures']}
    mode=0
    if 0 in maps:
        mode=1
        if maps[0]['flags'][0] and maps[0]['flags'][1]: mode=5 if 1 in maps else 2
        elif 1 in maps:mode=3
        elif 2 in maps:mode=4
    final_mode=contract['mode'] if contract['mode'] is not None else mode
    primary=maps.get(0,{}).get('name','').lower()
    post_shader_override=None
    if 'breaklightsonglow-' in primary:
        final_mode=14;post_shader_override='BREAKLIGHTSONGLOW_PRIMARY_SUBSTRING'
    elif 'breaklightson-' in primary:
        final_mode=1;post_shader_override='BREAKLIGHTSON_PRIMARY_SUBSTRING'
    return {'path': mesh['path'], 'node_offset': mesh['node_offset'], 'material_offset': mesh['material_offset'],
            'material': mesh['material'], 'texture_slots': slots, 'contract': contract,
            'texture_records':mesh['textures'], 'generic_pre_shader_mode':mode,
            'fallback_mode_if_unregistered':mode if contract['mode'] is None else None,
            'fallback_secondary':'AUTHORED_MAP_RETAINED_NOT_RENDERTARGET_OVERRIDE' if contract['mode'] is None else None,
            'final_mode_in_loader':final_mode,'post_shader_texture_override':post_shader_override,
            'conditional_named_child': mesh['path'].count('.')>1}


def main():
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2/'TNG.PAK')
    entries = {e['path'].replace('\\','/').split('/')[-2].upper(): e for e in manifest['entries']
               if e['kind']=='file' and '/VEHICLES/' in e['path'].replace('\\','/').upper()
               and e['path'].upper().endswith('CAR.PSM')}
    active = json.loads((PORT/'docs/reflection-coverage-fix/active-registry.json').read_text())
    digests = {r['geometry_sha256'] for r in active['entries']}
    result = {'schema_version':1, 'tolerance':TOL, 'exact_tolerance':.001,
              'coordinate_frame':'MODEL_LOCAL_SOURCE', 'evidence_grade':'CONFIRMED_BY_BYTES',
              'runtime_validation':'NOT_PERFORMED', 'remaining_families':[], 'brake_family_inventory':[]}
    for family, entry in sorted(entries.items()):
        payload, provenance = a.t.read_payload(entry, a.PS2/'TNG.000')
        try: scene = a.r.decode_vehicle(payload)
        except Exception as error:
            result['brake_family_inventory'].append({'family':family,'error':str(error)});continue
        lights = []
        for mesh in scene.meshes:
            if 'brake' in mesh['material'].lower() or any(any(s in x['name'].lower() for s in ('brake','breaklight')) for x in mesh['textures']):
                fs, controls = a.w.mesh_triangles(scene, mesh)
                lights.append({**metadata(mesh),'source_faces':len(fs),'controls':controls})
        result['brake_family_inventory'].append({'family':family,'source':entry['path'],
            'sha256':a.sha(payload),'light_meshes':lights,'named_nodes':scene.extra_nodes})
        pc_family = 'Forester' if family=='WOOLDAND' else next((x for x in FAMILIES if x.upper()==family),None)
        if pc_family not in FAMILIES: continue
        if family=='FORESTER':continue
        model = a.parse_dx(a.PC/pc_family/'car.dx')
        item = {'vehicle':pc_family, 'ps2_source':entry['path'], 'ps2_sha256':a.sha(payload),
                'pc_sha256':a.sha((a.PC/pc_family/'car.dx').read_bytes()), 'draws':[]}
        result['remaining_families'].append(item)
        meshmeta=[]; index=collections.defaultdict(list)
        for mesh in scene.meshes:
            mid=len(meshmeta);meshmeta.append(metadata(mesh))
            fs,_=a.w.mesh_triangles(scene,mesh)
            for face in fs:
                for key in {tuple(int(v//TOL) for v in p) for p in face}:index[key].append((mid,face))
        for draw in model.physical_draws:
            fs=a.faces(model,draw); nondeg=[f for f in fs if a.w.area_normal(f)[0]>1e-7]
            digest=a.geometry_signature(fs); matches=collections.Counter(); strict=collections.Counter()
            missing=0; errors=[]
            for face in nondeg:
                key=tuple(int(v//TOL) for v in face[0]); best={}
                for delta in itertools.product((-1,0,1),repeat=3):
                    for mid,candidate in index.get(tuple(key[i]+delta[i] for i in range(3)),()):
                        error=a.w.corner_error(face,candidate)
                        if error<=TOL:best[mid]=min(best.get(mid,TOL),error)
                matches.update(best.keys());strict.update(mid for mid,error in best.items() if error<=.001)
                missing+=not bool(best)
                if best:errors.append(min(best.values()))
            ids=set(model.draw_global_indices(draw))
            item['draws'].append({'draw':draw.draw_index,'record_path':draw.record_path,'record_offset':draw.offset,
                'geometry_sha256':digest,'already_registered':digest in digests,'triangles':len(fs),
                'nondegenerate':len(nondeg),'unmatched_faces':missing,'flags':draw.flags_0x20.hex(),
                'pc_slots':[s.value for s in draw.texture_slots], 'pc_vertex_alpha_values':sorted({model.vertices.colors[i*4+3] for i in ids}),
                'max_matched_error':max(errors,default=None), 'material_matches':[{'mesh':meshmeta[mid],
                    'matched_faces':count,'strict_faces':strict[mid]} for mid,count in sorted(matches.items())]})
        print(pc_family,'processed',len(item['draws']),flush=True)
    (HERE/'source-joins.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf8')


if __name__=='__main__':main()
