"""Read-only PS2 COMPLETE.PSM inventory and two original PC complete.dx joins.

Reuses validated PackFS and visual readers. Writes compact metadata only.
No model export, SDK write, runtime interception or executable analysis.
"""
from pathlib import Path
import importlib.util
import json
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'ps2-research/tools'))
import reflection_runtime as r
import tngtool as t
import water_runtime as w
# Synthetic grammar checks do not require the external PC SDK/corpus. The full
# source comparison imports the existing SDK adapter only when main runs.
existing = SimpleNamespace(r=r,t=t,w=w)
OUT = Path(__file__).parent


def bounds(faces):
    return {'min': [min(p[i] for f in faces for p in f) for i in range(3)],
            'max': [max(p[i] for f in faces for p in f) for i in range(3)]} if faces else None


def unique_resource(entries, path):
    matches = [e for e in entries if existing.t.logical_path(e['path']) == existing.t.logical_path(path)]
    if len(matches) != 1:
        raise ValueError('Resource not uniquely identified: ' + path)
    return matches[0]


def failed_terminal_evidence(error, payload):
    """Compact independent bytes at the strict parser's actual failure boundary.

    Does not accept a new terminal or promote partial parsing to decoded geometry.
    """
    trace = error.__traceback__
    while trace:
        if trace.tb_frame.f_code.co_name == 'decode_scene':
            offset = trace.tb_frame.f_locals.get('end')
            if offset is not None:
                return {'terminal_offset': offset, 'terminal_bytes_hex': payload[offset:offset+16].hex(),
                        'trailer_bytes_including_terminal': len(payload) - offset}
        trace = trace.tb_next
    return {}


def decode_menu(payload):
    try:
        return existing.r.decode_vehicle(payload)
    except existing.t.FormatError as error:
        probe = failed_terminal_evidence(error, payload)
        # Existing standalone grammar requires sentinel at exact EOF. No new
        # tag102 support or unexplained trailer acceptance is added here.
        if (probe.get('terminal_bytes_hex') == 'ffffffff' and
                probe.get('terminal_offset') == len(payload) - 4):
            return existing.w.decode_scene(payload,
                {7: existing.r._named_node, 8: existing.r._indexed_node}, terminator=0xffffffff)
        raise


def main():
    global existing
    spec = importlib.util.spec_from_file_location('existing_vehicle_audit', ROOT / 'ps2-research/pc-port/docs/full-coverage/vehicles/audit.py')
    existing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(existing)
    existing.w.verify_inputs(existing.PS2)
    manifest, _ = existing.t.load_pak(existing.PS2 / 'TNG.PAK')
    entries = sorted((e for e in manifest['entries'] if e['kind'] == 'file' and
                      '\\VEHICLES\\' in e['path'].upper() and e['path'].upper().endswith('\\COMPLETE.PSM')),
                     key=lambda e: e['path'])
    report = {'schema_version': 1, 'phase': 'FRONTEND_MODEL_FEASIBILITY',
              'evidence_grade': 'CONFIRMED_BY_BYTES', 'runtime_validation': 'NOT_PERFORMED',
              'coordinate_frame': 'MODEL_LOCAL_SOURCE_NO_FITTED_TRANSFORM',
              'tolerance': .001, 'inventory': [], 'cases': [],
              'pc_complete_sources': []}
    for path in sorted(existing.PC.glob('*/complete.dx')):
        report['pc_complete_sources'].append({'path': path.relative_to(existing.PC).as_posix(),
            'size': path.stat().st_size, 'sha256': existing.sha(path.read_bytes())})
    for entry in entries:
        payload, provenance = existing.t.read_payload(entry, existing.PS2 / 'TNG.000')
        item = {'resource': entry['path'], 'size': len(payload), 'sha256': existing.sha(payload),
                'provenance': provenance}
        report['inventory'].append(item)
        # Bounded parser feasibility over the entire menu-model family; no exports.
        try:
            scene = decode_menu(payload)
            all_faces = []
            for mesh in scene.meshes:
                fs, _ = existing.w.mesh_triangles(scene, mesh)
                all_faces.extend(fs)
            item.update({'decoder': 'SUPPORTED_EXISTING_VEHICLE_GRAMMAR',
                         'source_triangles': len(all_faces), 'mesh_count': len(scene.meshes),
                         'node_counts': scene.node_counts, 'bounds': bounds(all_faces),
                         'terminal_offset': scene.end,
                         'terminal_word_hex': payload[scene.end:scene.end+4].hex(),
                         'trailer_unparsed_bytes': len(payload) - scene.end - 4,
                         'visibility': 'ALL_AUTHORED_SUBSETS_LIVE_SELECTION_UNKNOWN'})
        except Exception as error:
            item.update({'decoder': 'UNSUPPORTED_FAIL_CLOSED', 'error': str(error),
                         **failed_terminal_evidence(error, payload)})
    for family, pc_family in [('TATA', 'Tata'), ('WOOLDAND', 'Forester')]:
        case = {'ps2_family': family, 'pc_family': pc_family, 'sources': [], 'comparisons': []}
        report['cases'].append(case)
        ps2s = {}
        for model_name in ('COMPLETE', 'CAR'):
            resource = '\\TNG\\DATAPSM\\VEHICLES\\' + family + '\\' + model_name + '.PSM'
            entry = unique_resource(manifest['entries'], resource)
            payload, provenance = existing.t.read_payload(entry, existing.PS2 / 'TNG.000')
            try:
                scene = decode_menu(payload)
            except Exception as error:
                case['sources'].append({'kind': 'PS2_' + model_name, 'resource': resource,
                    'sha256': existing.sha(payload), 'provenance': provenance,
                    'decoder': 'UNSUPPORTED_FAIL_CLOSED', 'error': str(error),
                    **failed_terminal_evidence(error, payload)})
                ps2s[model_name] = None
                continue
            meshes = []
            faces = []
            for mesh in scene.meshes:
                fs, control = existing.w.mesh_triangles(scene, mesh)
                faces.extend(fs)
                slots = existing.slot(mesh)
                meshes.append({'path': mesh['path'], 'node_offset': mesh['node_offset'],
                    'material_offset': mesh['material_offset'], 'material': mesh['material'],
                    'texture_slots': slots, 'triangles': len(fs), 'strip_controls': control,
                    'bounds': bounds(fs), 'geometry_sha256': existing.geometry_signature(fs),
                    'contract': existing.r.material_contract(mesh['material'], slots[1] if len(slots) > 1 else ''),
                    'conditional': mesh['path'].count('.') > 1})
            case['sources'].append({'kind': 'PS2_' + model_name, 'resource': resource,
                'sha256': existing.sha(payload), 'provenance': provenance, 'source_triangles': len(faces),
                'bounds': bounds(faces), 'meshes': meshes, 'extra_nodes': scene.extra_nodes,
                'visibility': 'AUTHORED_SOURCE_NOT_RUNTIME_BUDGET'})
            ps2s[model_name] = existing.index_faces(faces)
        for model_name in ('complete', 'car'):
            path = existing.PC / pc_family / (model_name + '.dx')
            model = existing.parse_dx(path)
            draws = []
            faces = []
            for draw in model.physical_draws:
                fs = existing.faces(model, draw)
                faces.extend(fs)
                draws.append({'draw_index': draw.draw_index, 'record_path': draw.record_path,
                    'record_offset': draw.offset, 'vertex_base': draw.vertex_base,
                    'index_start': draw.index_start, 'index_count': draw.index_count,
                    'triangles': len(fs), 'flags_hex': draw.flags_0x20.hex(),
                    'texture_slots': [slot.value for slot in draw.texture_slots],
                    'geometry_sha256': existing.geometry_signature(fs), 'bounds': bounds(fs),
                    'ps2_complete_matches': sum(existing.matches(f, ps2s['COMPLETE']) for f in fs) if ps2s['COMPLETE'] is not None else None,
                    'ps2_car_matches': sum(existing.matches(f, ps2s['CAR']) for f in fs)})
            case['sources'].append({'kind': 'PC_' + model_name.upper(),
                'path': path.relative_to(existing.PC).as_posix(), 'sha256': existing.sha(path.read_bytes()),
                'source_triangles': len(faces), 'bounds': bounds(faces), 'draws': draws,
                'visibility': 'COMPILED_DRAW_SOURCE_NOT_RUNTIME_CAPTURE'})
            case['comparisons'].append({'pc_model': model_name, 'pc_triangles': len(faces),
                'ps2_complete_matching_pc_faces': sum(d['ps2_complete_matches'] for d in draws) if ps2s['COMPLETE'] is not None else None,
                'ps2_car_matching_pc_faces': sum(d['ps2_car_matches'] for d in draws),
                'matching_method': 'UNSIGNED_PERMUTED_TRIANGLE_MAX_CORNER_DISTANCE',
                'transform': 'IDENTITY_DIAGNOSTIC_NO_RUNTIME_WORLD_CLAIM'})
        print(family, case['comparisons'], flush=True)
    (OUT / 'source-evidence.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
