"""29 original COMPLETE sources and compiled PC controls; metadata only."""
from pathlib import Path
from collections import Counter
import importlib.util
import itertools
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0,str(HERE))
from complete_reader import decode_complete
spec=importlib.util.spec_from_file_location('existing_vehicle_source_audit',ROOT/'ps2-research/pc-port/docs/full-coverage/vehicles/audit.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def bounds(faces):
    return {'min':[min(p[i] for f in faces for p in f) for i in range(3)],
            'max':[max(p[i] for f in faces for p in f) for i in range(3)]} if faces else None


def position_matches(source, target):
    """Distinct numeric XYZ positions, independent of strip triangulation."""
    index={}
    for p in set(target):index.setdefault(tuple(int(x//.001) for x in p),[]).append(p)
    found=0
    for p in set(source):
        key=tuple(int(x//.001) for x in p)
        if any(max(abs(p[i]-q[i]) for i in range(3)) <= .001
            for delta in itertools.product((-1,0,1),repeat=3)
            for q in index.get(tuple(key[i]+delta[i] for i in range(3)),[])):
            found+=1
    return {'source_distinct_xyz':len(set(source)),'target_distinct_xyz':len(set(target)),
        'matching_source_xyz':found,'method':'DISTINCT_XYZ_MAX_AXIS_DISTANCE_0_001'}


def main():
    a.w.verify_inputs(a.PS2)
    manifest,_=a.t.load_pak(a.PS2/'TNG.PAK')
    entries=sorted((e for e in manifest['entries'] if e['kind']=='file' and
        '\\VEHICLES\\' in e['path'].upper() and e['path'].upper().endswith('\\COMPLETE.PSM')),
        key=lambda e:e['path'])
    pcs={p.parent.name.upper():p for p in sorted(a.PC.glob('*/complete.dx'))}
    report={'schema_version':1,'phase':'PS2-VEHICLE-MODEL-PORT1',
        'representation':'PS2_AUTHORED_VISUAL_SOURCE_AND_PC_COMPILED_RENDER_DRAW',
        'frame':'MODEL_LOCAL_IDENTITY_NO_FITTED_TRANSFORM','tolerance':.001,
        'evidence_grade':'CONFIRMED_BY_BYTES','runtime_visibility':'UNKNOWN',
        'canonical_inputs_verified':True,'ps2_complete_count':len(entries),
        'pc_complete_count':len(pcs),'inventory':[]}
    for entry in entries:
        payload,provenance=a.t.read_payload(entry,a.PS2/'TNG.000')
        family=entry['path'].split('\\')[-2]
        item={'family':family,'resource':entry['path'],'sha256':a.sha(payload),
            'size':len(payload),'provenance':provenance,'decoder':'FAIL_CLOSED'}
        report['inventory'].append(item)
        try:scene,trailer=decode_complete(payload)
        except a.t.FormatError as e:
            item['error']=str(e);continue
        meshes=[];fs=[];rootfs=[]
        for mesh in scene.meshes:
            faces,control=a.w.mesh_triangles(scene,mesh);fs.extend(faces)
            conditional=mesh['path'].count('.')>1
            if not conditional:rootfs.extend(faces)
            slots=a.slot(mesh)
            meshes.append({'path':mesh['path'],'node_offset':mesh['node_offset'],
                'material_offset':mesh['material_offset'],'material':mesh['material'],
                'textures':mesh['textures'],'source_triangles':len(faces),
                'bounds':bounds(faces),'geometry_sha256':a.geometry_signature(faces),
                'strip_controls':control,'conditional':conditional,
                'contract':a.r.material_contract(mesh['material'],slots[1] if len(slots)>1 else '')})
        item.update({'decoder':'SUPPORTED_PROVED_GRAMMAR','trailer':trailer,
            'source_vertex_count':scene.vertex_count,'source_triangles':len(fs),
            'root_source_triangles':len(rootfs),'mesh_count':len(meshes),
            'node_counts':scene.node_counts,'named_and_indexed_nodes':scene.extra_nodes,
            'bounds':bounds(fs),'meshes':meshes})
        # FORESTER remains a separate PS2 car; it is not another name for WOOLDAND.
        key='FORESTER' if family=='WOOLDAND' else family
        p=pcs.get(key) if family!='FORESTER' else None
        if p is None:
            item['pc_pair']='NO_VERIFIED_PC_COUNTERPART'; print(family,'no PC counterpart',flush=True);continue
        model=a.parse_dx(p);pcfs=[];draws=[];idx=a.index_faces(fs);ridx=a.index_faces(rootfs)
        for draw in model.physical_draws:
            faces=a.faces(model,draw);pcfs.extend(faces)
            draws.append({'draw_index':draw.draw_index,'record_path':draw.record_path,
                'record_offset':draw.offset,'vertex_base':draw.vertex_base,'index_start':draw.index_start,
                'index_count':draw.index_count,'source_triangles':len(faces),
                'texture_slots':[s.value for s in draw.texture_slots],'flags_hex':draw.flags_0x20.hex(),
                'geometry_sha256':a.geometry_signature(faces),'bounds':bounds(faces),
                'ps2_triangle_matches':sum(a.matches(f,idx) for f in faces),
                'ps2_root_matches':sum(a.matches(f,ridx) for f in faces)})
        item['pc_pair']={'path':p.relative_to(a.PC).as_posix(),'sha256':a.sha(p.read_bytes()),
            'source_triangles':len(pcfs),'bounds':bounds(pcfs),'draws':draws,
            'ps2_triangle_matches':sum(d['ps2_triangle_matches'] for d in draws),
            'ps2_root_matches':sum(d['ps2_root_matches'] for d in draws),
            'position_matches':position_matches([p for f in pcfs for p in f],[p for f in fs for p in f]),
            'pairing':'GEOMETRY_CHECKED_SAME_FAMILY_OR_PROVED_WOOLDAND_FORESTER',
            'source_correspondence_status':'EXACT_SOURCE_SURFACE_ANCHORS_PRESENT' if any(d['ps2_triangle_matches'] for d in draws)
                else 'NO_EXACT_TRIANGLE_IN_IDENTITY_FRAME_NOT_PLATFORM_EXCLUSIVITY'}
        print(family,len(fs),len(pcfs),item['pc_pair']['ps2_triangle_matches'],flush=True)
    report['decoder_counts']=dict(Counter(x['decoder'] for x in report['inventory']))
    report['trailer_counts']=dict(Counter(str(x['trailer']['tag']) for x in report['inventory'] if 'trailer'in x))
    (HERE/'complete-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Original COMPLETE source coverage','',
        'All29 supported visual trees; authored totals are not simultaneous menu/runtime budgets.',
        'Identity source coordinates, unsigned triangles, maximum corner distance0.001.',
        'PC resource names are candidate links; exact matches are independent surface anchors.',
        'Zero exact matches do not prove platform exclusivity. No fitted transforms.','',
        '| PS2 source family | Trailer | PS2 source faces | Mesh records | PC candidate | PC source faces | Exact matched PC faces |',
        '|---|---:|---:|---:|---|---:|---:|']
    for row in report['inventory']:
        pc=row['pc_pair'];paired=isinstance(pc,dict)
        lines.append('|%s|%s|%s|%s|%s|%s|%s|' % (row['family'],row['trailer']['tag'],
            row['source_triangles'],row['mesh_count'],pc['path'] if paired else 'UNKNOWN',
            pc['source_triangles'] if paired else 'UNKNOWN',pc['ps2_triangle_matches'] if paired else 'UNKNOWN'))
    lines+=['','WOOLDAND is the current PC Forester source; PS2 FORESTER remains a separate additional-car candidate.',
        'No native menu replacement, material override or collision transfer is validated by this table.','']
    (HERE/'complete-coverage.md').write_text('\n'.join(lines))


if __name__=='__main__':main()
