"""Bounded read-only WOOLDAND versus Forester join; compact evidence only."""
from pathlib import Path
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
spec = importlib.util.spec_from_file_location('full_vehicle_audit', ROOT / 'ps2-research/pc-port/docs/full-coverage/vehicles/audit.py')
existing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(existing)

OUT = Path(__file__).parent


def bounds(fs):
    if not fs:
        return None
    return {'min': [min(p[i] for f in fs for p in f) for i in range(3)],
            'max': [max(p[i] for f in fs for p in f) for i in range(3)]}


def main():
    existing.w.verify_inputs(existing.PS2)
    manifest, _ = existing.t.load_pak(existing.PS2 / 'TNG.PAK')
    path = existing.PC / 'Forester/car.dx'
    model = existing.parse_dx(path)
    pc_faces = {d.draw_index: existing.faces(model, d) for d in model.physical_draws}
    report = {'schema_version': 1, 'phase': 'REFLECTION_COVERAGE_FIX_WOOLDAND',
              'coordinates': 'MODEL_LOCAL_SOURCE_IDENTITY', 'tolerance': .001,
              'pc_source': {'path': 'Forester/car.dx', 'sha256': existing.sha(path.read_bytes())},
              'method': 'Unsigned corner permutations, max corner distance <= .001; no texture prefilter',
              'sources': [], 'registry_candidates': [], 'runtime_validation': 'NOT_PERFORMED'}
    for family in ('WOOLDAND', 'FORESTER'):
        resource = '\\TNG\\DATAPSM\\VEHICLES\\' + family + '\\CAR.PSM'
        entries = [e for e in manifest['entries'] if existing.t.logical_path(e['path']) == existing.t.logical_path(resource)]
        if len(entries) != 1:
            raise ValueError('Resource not unique: ' + resource)
        payload, provenance = existing.t.read_payload(entries[0], existing.PS2 / 'TNG.000')
        scene = existing.r.decode_vehicle(payload)
        meshes = []
        all_faces = []
        for m in scene.meshes:
            fs, controls = existing.w.mesh_triangles(scene, m)
            all_faces += fs
            tx = existing.slot(m)
            contract = existing.r.material_contract(m['material'], tx[1] if len(tx) > 1 else '')
            meshes.append((m, fs, existing.index_faces(fs), tx, contract, controls))
        source = {'family': family, 'resource': resource, 'sha256': existing.sha(payload),
                  'provenance': provenance, 'total_source_triangles': len(all_faces),
                  'bounds': bounds(all_faces), 'mesh_count': len(meshes), 'draws': [],
                  'visual_meshes': [{'path': m['path'], 'node_offset': m['node_offset'],
                                    'material_offset': m['material_offset'], 'material': m['material'],
                                    'texture_slots': tx, 'contract': contract, 'triangles': len(fs),
                                    'geometry_sha256': existing.geometry_signature(fs),
                                    'bounds': bounds(fs), 'strip_controls': controls,
                                    'live_child_selection': 'UNKNOWN' if m['path'].count('.') > 1 else 'ROOT_SOURCE_MESH'}
                                   for m, fs, idx, tx, contract, controls in meshes]}
        report['sources'].append(source)
        for draw in model.physical_draws:
            fs = pc_faces[draw.draw_index]
            tx = [s.value for s in draw.texture_slots]
            joins = []
            for m, pfs, idx, ptx, contract, controls in meshes:
                matched = sum(existing.matches(f, idx) for f in fs)
                if not matched:
                    continue
                reverse = sum(existing.matches(f, existing.index_faces(fs)) for f in pfs)
                joins.append({'mesh_path': m['path'], 'node_offset': m['node_offset'],
                              'material_offset': m['material_offset'], 'material': m['material'],
                              'texture_slots': ptx, 'contract': contract,
                              'pc_matching_faces': matched, 'pc_faces': len(fs),
                              'ps2_matching_faces': reverse, 'ps2_faces': len(pfs),
                              'bounds': bounds(pfs), 'strip_controls': controls})
            record = {'draw_index': draw.draw_index, 'record_path': draw.record_path,
                      'record_offset': draw.offset, 'vertex_base': draw.vertex_base,
                      'vertices': draw.local_vertex_max + 1, 'index_start': draw.index_start,
                      'index_count': draw.index_count, 'triangles': len(fs), 'texture_slots': tx,
                      'flags_hex': draw.flags_0x20.hex(), 'geometry_sha256': existing.geometry_signature(fs),
                      'bounds': bounds(fs), 'matches': joins,
                      'best_matching_faces': max((j['pc_matching_faces'] for j in joins), default=0)}
            union_index = existing.index_faces(all_faces)
            record['union_matching_faces'] = sum(existing.matches(f, union_index) for f in fs)
            shiny_faces = [f for m, pfs, idx, ptx, contract, controls in meshes
                           if m['path'].count('.') == 1 and contract['interned_shader'] == 'carshiny'
                           and not contract['rubber_substring_preserved'] for f in pfs]
            shiny_index = existing.index_faces(shiny_faces)
            record['unconditional_nonrubber_carshiny_matching_faces'] = sum(existing.matches(f, shiny_index) for f in fs)
            unmatched = [f for f in fs if not existing.matches(f, union_index)]
            closest = [min(existing.w.corner_error(f, g) for g in all_faces) for f in unmatched]
            record['unmatched_closest_corner_errors'] = sorted(closest)
            record['diffuse_alpha_values'] = sorted({model.vertices.colors[i * 4 + 3] for i in model.draw_global_indices(draw)})
            source['draws'].append(record)
            accepted = [j for j in joins if j['pc_matching_faces'] == len(fs) and
                        j['mesh_path'].count('.') == 1 and j['contract']['interned_shader'] == 'carshiny'
                        and not j['contract']['rubber_substring_preserved']]
            if family == 'WOOLDAND' and len(accepted) == 1 and record['flags_hex'] == '00000101':
                report['registry_candidates'].append({'vehicle': 'Forester', 'ps2_family': family,
                    **record, 'ps2_source_sha256': existing.sha(payload),
                    'pc_source_sha256': report['pc_source']['sha256'], 'ps2_binding': accepted[0],
                    'evidence_grade': 'CONFIRMED_BY_BYTES',
                    'activation': 'CURRENT_NATIVE_OWNER_AND_ENVIRONMENT_STATE_GATES_REQUIRED'})
    hashes = {r['geometry_sha256'] for r in report['registry_candidates']}
    counts = {r['index_count'] for r in report['registry_candidates']}
    hits = {h: [] for h in sorted(hashes)}
    scanned = 0
    unsupported = []
    for dx in sorted(existing.PC.glob('*/*.dx')):
        scanned += 1
        try:
            current = existing.parse_dx(dx)
        except Exception as error:
            unsupported.append({'path': str(dx.relative_to(existing.PC)), 'error': str(error)})
            continue
        for draw in current.physical_draws:
            if draw.index_count not in counts:
                continue
            signature = existing.geometry_signature(existing.faces(current, draw))
            if signature in hashes:
                hits[signature].append({'path': str(dx.relative_to(existing.PC)).replace('\\', '/'),
                                        'draw_index': draw.draw_index})
    for item in report['registry_candidates']:
        owners = sorted({h['path'].split('/')[0] for h in hits[item['geometry_sha256']]})
        item['signature_owner_families'] = owners
        item['unique_vehicle_family'] = owners == ['Forester']
    report['negative_controls'] = {'files_scanned': scanned, 'unsupported': unsupported, 'signature_hits': hits}
    (OUT / 'join-evidence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'sources': [{'family': s['family'], 'source_faces': s['total_source_triangles'],
                                  'full_pc_draw_matches': sum(d['best_matching_faces'] == d['triangles'] for d in s['draws'])}
                                 for s in report['sources']],
                      'registry_candidates': [{k: r[k] for k in ('draw_index', 'triangles', 'geometry_sha256', 'unique_vehicle_family')}
                                              for r in report['registry_candidates']]}, indent=2))


if __name__ == '__main__':
    main()
