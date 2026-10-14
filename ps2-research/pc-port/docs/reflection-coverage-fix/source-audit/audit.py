"""Bounded source-shape audit, deliberately independent of texture slot equality.

Read original assets only. Reports hashes/offsets/metadata, never complete meshes.
"""
from pathlib import Path
import importlib.util
import collections
import itertools
import json
import time

OUT = Path(__file__).parent
PORT = OUT.parents[2]
spec = importlib.util.spec_from_file_location('prior_vehicle_audit', PORT / 'docs/full-coverage/vehicles/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
import geometry_delta as g
FAMILIES = ('LANDCRUISER', 'TATA', 'CHEVYBLAZER', 'XTRAIL', 'NAVARA', 'JUMP',
            'PATROL', 'BRUNO', 'SEATBUGGY', 'KAMAZ', 'ICECREAM', 'UFO')


def cell(point):
    return tuple(int(x // .001) for x in point)


def main():
    started = time.perf_counter()
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2 / 'TNG.PAK')
    entries = {e['path'].replace('\\', '/').split('/')[-2].upper(): e
               for e in manifest['entries'] if e['kind'] == 'file'
               and '/VEHICLES/' in e['path'].replace('\\', '/').upper()
               and e['path'].upper().endswith('CAR.PSM')}
    pcdirs = {p.name.upper(): p for p in a.PC.iterdir() if p.is_dir()}
    old = json.loads((PORT / 'docs/full-coverage/vehicles/registry-candidates.json').read_text())
    old_keys = {(x['vehicle'].upper(), x['draw_index']) for x in old}
    report = {'schema_version': 1, 'matching_tolerance': .001,
              'method': 'all PC physical draw faces vs original PS2 carshiny corner-permutation; spatial cell candidates, no texture equality prefilter',
              'coordinate_frame': 'MODEL_LOCAL_SOURCE', 'runtime_validation': 'NOT_PERFORMED',
              'vehicles': [], 'additions': [], 'vertex_material_candidates': [], 'conditional_candidates': []}
    for family in FAMILIES:
        e = entries[family]
        payload, provenance = a.t.read_payload(e, a.PS2 / 'TNG.000')
        scene = a.r.decode_vehicle(payload)
        meshes = []
        root_faces = []
        root_vertices = collections.defaultdict(list)
        index = collections.defaultdict(list)
        for mesh in scene.meshes:
            slots = a.slot(mesh)
            contract = a.r.material_contract(mesh['material'], slots[1] if len(slots) > 1 else '')
            if contract['interned_shader'] != 'carshiny' or contract['rubber_substring_preserved']:
                continue
            fs, controls = a.w.mesh_triangles(scene, mesh)
            mid = len(meshes)
            meshes.append({'path': mesh['path'], 'node_offset': mesh['node_offset'],
                           'material_offset': mesh['material_offset'], 'material': mesh['material'],
                           'texture_slots': slots, 'contract': contract, 'triangles': len(fs),
                           'strip_controls': controls})
            if mesh['path'].count('.') == 1:
                for strip in mesh['strips']:
                    for vi in range(strip['start'], strip['start']+strip['count']):
                        point = scene.position(vi)
                        root_vertices[cell(point)].append((mid, point))
            for face in fs:
                if mesh['path'].count('.') == 1:
                    root_faces.append(g.Face(str(len(root_faces)), str(mid), face))
                for key in {cell(p) for p in face}:
                    index[key].append((mid, face))
        root_spatial = g.SpatialIndex(root_faces, cell=.25)
        source = pcdirs[family] / 'car.dx'
        model = a.parse_dx(source)
        item = {'vehicle': pcdirs[family].name, 'ps2_resource': e['path'],
                'ps2_source_sha256': a.sha(payload), 'ps2_provenance': provenance,
                'pc_source_sha256': a.sha(source.read_bytes()), 'draws': [], 'carshiny_meshes': meshes}
        report['vehicles'].append(item)
        for draw in model.physical_draws:
            faces = a.faces(model, draw)
            if not faces:
                continue
            nondegenerate = [face for face in faces if a.w.area_normal(face)[0] > 1e-7]
            per_mesh = collections.Counter()
            union = 0
            root_union = 0
            equivalent = 0
            partial_metrics = []
            surface_meshes = set()
            for face in nondegenerate:
                key = cell(face[0])
                found = set()
                for delta in itertools.product((-1, 0, 1), repeat=3):
                    for mid, candidate in index.get(tuple(key[i] + delta[i] for i in range(3)), ()):
                        if mid not in found and a.w.corner_error(face, candidate) <= .001:
                            found.add(mid)
                union += bool(found)
                root_found = any(meshes[mid]['path'].count('.') == 1 for mid in found)
                root_union += root_found
                if not root_found:
                    n = g.normal(face)
                    planar = []
                    for cid in root_spatial.candidates(g.bounds(face), .001):
                        candidate = root_faces[cid].points
                        if abs(g.dot(n, root_spatial.normals[cid])) < .99999: continue
                        if max(abs(g.dot(n, tuple(p[j]-face[0][j] for j in range(3)))) for p in candidate) > .001: continue
                        if g.union_coverage(face, [candidate]) <= 1e-8: continue
                        planar.append(cid)
                    coverage = g.union_coverage(face, [root_faces[cid].points for cid in planar])
                    equivalent += coverage >= .99999
                    partial_metrics.append({'area': a.w.area_normal(face)[0], 'coplanar_root_coverage': coverage,
                                            'source_face_ordinal': faces.index(face)})
                    if coverage >= .99999:
                        surface_meshes.update(int(root_faces[cid].group) for cid in planar)
                per_mesh.update(found)
            slots = [s.value for s in draw.texture_slots]
            joined = [{**meshes[mid], 'pc_matching_faces': count}
                      for mid, count in sorted(per_mesh.items())]
            full = [m for m in joined if m['pc_matching_faces'] == len(nondegenerate)] if nondegenerate else []
            root = [m for m in full if m['path'].count('.') == 1]
            ids = model.draw_global_indices(draw)
            pc_points = sorted({p for face in nondegenerate for p in face})
            point_matches = 0
            point_materials = set()
            unmatched_point_bounds = []
            for point in pc_points:
                key = cell(point)
                found = set()
                for delta in itertools.product((-1,0,1), repeat=3):
                    for mid, candidate in root_vertices.get(tuple(key[i]+delta[i] for i in range(3)), ()):
                        if max(abs(x-y) for x,y in zip(point,candidate)) <= .001:
                            found.add(mid)
                point_matches += bool(found)
                point_materials.update(found)
                if not found: unmatched_point_bounds.append(point)
            record = {'vehicle': pcdirs[family].name, 'draw_index': draw.draw_index,
                      'record_path': draw.record_path, 'record_offset': draw.offset,
                      'vertex_base': draw.vertex_base, 'vertices': draw.local_vertex_max + 1,
                      'index_start': draw.index_start, 'index_count': draw.index_count,
                      'triangles': len(faces), 'nondegenerate_triangles': len(nondegenerate),
                      'diagnostic_degenerate_triangles': len(faces)-len(nondegenerate), 'texture_slots': slots,
                      'flags_hex': draw.flags_0x20.hex(), 'geometry_sha256': a.geometry_signature(faces),
                      'diffuse_alpha_values': sorted({model.vertices.colors[i*4+3] for i in ids}),
                      'bounds': {'min': [min(p[i] for f in faces for p in f) for i in range(3)],
                                 'max': [max(p[i] for f in faces for p in f) for i in range(3)]},
                      'matches': joined, 'pc_faces_matching_carshiny_union': union,
                      'pc_faces_matching_root_carshiny_union': root_union,
                      'root_surface_equivalent_faces': equivalent,
                      'root_material_vertex_agreement': {'pc_unique_nondegenerate_positions': len(pc_points),
                          'matching_positions': point_matches,
                          'ps2_material_meshes': [meshes[mid]['path'] for mid in sorted(point_materials)],
                          'unmatched_position_bounds': g.bounds(unmatched_point_bounds)},
                      'exact_unmatched_face_metrics': partial_metrics,
                      'existing_registry': (family, draw.draw_index) in old_keys,
                      'complete_root_matches': len(root), 'complete_conditional_matches': len(full)-len(root)}
            item['draws'].append(record)
            roots = [m for m in joined if m['path'].count('.') == 1]
            roots.extend({**meshes[mid], 'pc_matching_faces': 0, 'surface_equivalence_binding': True}
                         for mid in sorted(surface_meshes) if not any(m['path']==meshes[mid]['path'] for m in roots))
            if not record['existing_registry'] and nondegenerate and root_union+equivalent == len(nondegenerate):
                best_root = max(roots, key=lambda m: m['pc_matching_faces'])
                reasons = []
                if slots[1] in ('Null', 'rubber-tga', 'glass-tga'): reasons.append('OLD_SLOT1_EXCLUSION')
                if not any(slots[:2] == m['texture_slots'][:2] for m in roots): reasons.append('OLD_EXACT_TEXTURE_PREFILTER')
                if record['flags_hex'] != '00000101': reasons.append('OLD_NATIVE_FLAGS_PREFILTER')
                if record['diagnostic_degenerate_triangles']: reasons.append('OLD_PC_DEGENERATE_FACES_NOT_REMOVED')
                if not root: reasons.append('PC_DRAW_SPLITS_OR_MERGES_PS2_ROOT_MATERIAL_GROUPS')
                if equivalent: reasons.append('OLD_IDENTICAL_TRIANGLE_REQUIREMENT_TOPOLOGY_DIFFERENCE')
                report['additions'].append({**record, 'ps2_binding': best_root, 'ps2_bindings': roots,
                    'ps2_source_sha256': item['ps2_source_sha256'], 'pc_source_sha256': item['pc_source_sha256'],
                    'evidence_grade': 'STATIC_INFERENCE' if equivalent else 'CONFIRMED_BY_BYTES', 'omission_reasons': reasons,
                    'activation': 'CURRENT_NATIVE_SEMANTIC_OWNER_RESOURCE_GENERATIONS_AND_VERIFIED_STAGE_LAYOUT_REQUIRED'})
            elif not record['existing_registry'] and full:
                report['conditional_candidates'].append(record)
            elif not record['existing_registry'] and root_union and point_matches == len(pc_points):
                vertex_roots = [{**meshes[mid], 'pc_matching_faces': per_mesh[mid]}
                                for mid in sorted(point_materials)]
                report['vertex_material_candidates'].append({**record, 'ps2_bindings': vertex_roots,
                    'ps2_binding': max(vertex_roots, key=lambda m:m['pc_matching_faces']),
                    'ps2_source_sha256': item['ps2_source_sha256'], 'pc_source_sha256': item['pc_source_sha256'],
                    'evidence_grade': 'CONFIRMED_BY_BYTES', 'geometric_relation': 'SOURCE_VERTEX_MATERIAL_JOIN_TOPOLOGY_DIFFERENT',
                    'runtime_identity': 'NOT_PERFORMED',
                    'limitation': 'All nondegenerate PC positions are owned by original root carshiny source strips; remaining PC faces are not proved equivalent PS2 visual primitives.'})
        print(family, 'draws', len(item['draws']), 'new-root', sum(x['vehicle'].upper()==family for x in report['additions']), flush=True)
    proposed = report['additions']+report['vertex_material_candidates']
    hashes = {x['geometry_sha256'] for x in proposed}
    counts = {x['index_count'] for x in proposed}
    hits = {h: [] for h in sorted(hashes)}
    failures = []
    for source in sorted(a.PC.glob('*/*.dx')):
        try: model = a.parse_dx(source)
        except Exception as error:
            failures.append({'source': str(source.relative_to(a.PC)), 'error': str(error)})
            continue
        for draw in model.physical_draws:
            if draw.index_count not in counts: continue
            digest = a.geometry_signature(a.faces(model, draw))
            if digest in hits: hits[digest].append({'source': str(source.relative_to(a.PC)).replace('\\','/'), 'draw': draw.draw_index})
    for row in proposed:
        owners = sorted({hit['source'].split('/')[0] for hit in hits[row['geometry_sha256']]})
        row['signature_owner_families'] = owners
        row['unique_vehicle_family'] = owners == [row['vehicle']]
    report['negative_controls'] = {'retail_dx_files': len(list(a.PC.glob('*/*.dx'))), 'hits': hits, 'unsupported': failures}
    report['runtime_seconds'] = time.perf_counter()-started
    (OUT/'source-coverage.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf8')
    (OUT/'registry-additions.json').write_text(json.dumps([x for x in report['additions'] if x['unique_vehicle_family']], indent=2, allow_nan=False)+'\n', encoding='utf8')
    (OUT/'vertex-material-candidates.json').write_text(json.dumps(report['vertex_material_candidates'], indent=2, allow_nan=False)+'\n', encoding='utf8')
    print('Complete additions', len(report['additions']), 'conditional', len(report['conditional_candidates']), 'seconds', report['runtime_seconds'])


if __name__ == '__main__': main()
