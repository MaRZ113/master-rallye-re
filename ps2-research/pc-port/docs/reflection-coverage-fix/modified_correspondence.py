"""Bounded material correspondence for small source revisions, not geometry parity.

The .001 exact-geometry baseline stays unchanged. This diagnostic uses .005
source units to map one whole PC material draw to one PS2 carshiny root mesh;
it preserves differing UV evidence and independently proves the native PC hash.
"""
from pathlib import Path
import importlib.util
import itertools
import json
import struct

PORT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('source_audit',PORT/'docs/full-coverage/vehicles/audit.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
TOLERANCE=.005
FAMILIES=('Forester','Navara','Patrol','Bruno','Kamaz','LandCruiser','Xtrail','ChevyBlazer','SeatBuggy')


def main():
    a.w.verify_inputs(a.PS2)
    manifest,_=a.t.load_pak(a.PS2/'TNG.PAK')
    entries={e['path'].replace('\\','/').upper():e for e in manifest['entries'] if e['kind']=='file'}
    prior=json.loads((PORT/'docs/full-coverage/vehicles/registry-candidates.json').read_text())
    strict=json.loads((HERE/'source-audit/registry-additions.json').read_text())
    vertex=json.loads((HERE/'source-audit/vertex-material-candidates.json').read_text())
    existing={r['geometry_sha256'] for r in prior+strict+vertex}
    rows=[]
    for family in FAMILIES:
        psfamily='WOOLDAND' if family=='Forester' else family.upper()
        key='/TNG/DATAPSM/VEHICLES/'+psfamily+'/CAR.PSM'
        payload,_=a.t.read_payload(entries[key],a.PS2/'TNG.000')
        scene=a.r.decode_vehicle(payload);pcfile=a.PC/family/'car.dx';model=a.parse_dx(pcfile)
        meshes=[]
        for mesh in scene.meshes:
            slots=a.slot(mesh);contract=a.r.material_contract(mesh['material'],slots[1] if len(slots)>1 else '')
            if mesh['path'].count('.')!=1 or contract['mode']!=3 or contract['rubber_substring_preserved']:continue
            faces,_=a.w.mesh_triangles(scene,mesh);index={}
            for face in faces:
                for position in face:index.setdefault(tuple(int(v//TOLERANCE) for v in position),[]).append(face)
            meshes.append((mesh,faces,index))
        for draw in model.physical_draws:
            if draw.flags_0x20.hex()!='00000101':continue
            faces=a.faces(model,draw);nondegenerate=[f for f in faces if a.w.area_normal(f)[0]>1e-7]
            digest=a.geometry_signature(faces)
            if digest in existing:continue
            matches=[]
            for mesh,source,index in meshes:
                errors=[]
                for face in nondegenerate:
                    key0=tuple(int(v//TOLERANCE) for v in face[0])
                    candidates=[g for delta in itertools.product((-1,0,1),repeat=3)
                                for g in index.get(tuple(key0[j]+delta[j] for j in range(3)),[])]
                    errors.append(min((a.w.corner_error(face,g) for g in candidates),default=1e20))
                if errors and max(errors)<=TOLERANCE:matches.append((mesh,source,max(errors)))
            if len(matches)!=1:continue
            mesh,source,error=matches[0]
            records=[]
            for i in {i for strip in mesh['strips'] for i in range(strip['start'],strip['start']+strip['count'])}:
                records.append((scene.position(i),struct.unpack_from('<2f',payload,32+i*52+20)))
            ids=set(model.draw_global_indices(draw));uv=model.uv_sets[0].values;uv_errors=[]
            for i in ids:
                candidates=[q for q in records if max(abs(model.vertices.positions[i][j]-q[0][j]) for j in range(3))<=TOLERANCE]
                uv_errors.append(min((max(abs(uv[i][j]-q[1][j]) for j in range(2)) for q in candidates),default=1e10))
            owners=set()
            for f in sorted(a.PC.glob('*/*.dx')):
                other=a.parse_dx(f)
                for candidate in other.physical_draws:
                    if candidate.index_count//3==len(faces) and a.geometry_signature(a.faces(other,candidate))==digest:owners.add(f.parent.name)
            if owners!={family}:raise ValueError('Ambiguous current original compiled draw identity')
            rows.append({'vehicle':family,'draw_index':draw.draw_index,'triangles':len(faces),'vertices':draw.local_vertex_max+1,
                'geometry_sha256':digest,'pc_source_sha256':a.sha(pcfile.read_bytes()),'ps2_source_sha256':a.sha(payload),
                'ps2_resource':key,'binding':{'node':mesh['node_offset'],'path':mesh['path'],'material':mesh['material'],
                    'max_error':error,'matching_pc_faces':len(nondegenerate),'ps2_faces':len(source)},
                'geometry_relation':'GEOMETRY_MODIFIED_SMALL_LOCAL_DISPLACEMENT',
                'material_relation':'SINGLE_PS2_CARSHINY_MATERIAL_CORRESPONDENCE','tolerance':TOLERANCE,
                'independent_uv_check':{'unique_referenced_pc_vertices':len(ids),'position_and_uv_matches':sum(e<.00001 for e in uv_errors),
                    'max_uv_error':max(uv_errors),'uv_tolerance':.00001,'complete':all(e<.00001 for e in uv_errors)},
                'signature_owner_families':sorted(owners),'unique_vehicle_family':True,
                'evidence_grade':'CONFIRMED_BY_BYTES','activation':'MODE4_ONLY_CURRENT_NATIVE_OPAQUE_ENVIRONMENT_GATES'})
    result={'schema_version':1,'entries':rows,'activation':'BODY_MATERIAL_CORRESPONDENCE_WITH_EXACT_PC_RUNTIME_HASH',
            'boundary':'Material correspondence; original PC geometry/UVs preserved, not exact PS2 triangle parity',
            'excluded_non_body_records':['Forester:2','Forester:7']}
    (HERE/'modified-material-correspondence.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Correspondences:',[(r['vehicle'],r['draw_index'],r['binding']['max_error']) for r in rows])


if __name__=='__main__':main()
