"""Read-only X-Trail COMPLETE readiness; no geometry export or menu writes.

Existing strict readers and frozen source metadata remain authoritative. A
bounding-box-derived longitudinal offset is diagnostic, never admission proof.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PRIOR = ROOT / 'ps2-research/pc-port/docs/vehicle-model-port1'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shift_faces(faces, delta):
    return [tuple(tuple(p[i] + delta[i] for i in range(3)) for p in face)
            for face in faces]


def frontend_observation(record):
    scene = record.get('scene', {})
    return (record.get('type') == 'race_epoch_snapshot'
            and record.get('live_certificate_valid') is False
            and scene.get('read_complete') is True
            and scene.get('countdown') == 0
            and scene.get('requested_name') == 'FrontendScreens/VehicleSelect'
            and scene.get('committed_name') == 'FrontendScreens/VehicleSelect'
            and scene.get('job_source') == 'DataScene/FrontendScreens/VehicleSelect.xml')


def main():
    source_path = PRIOR / 'ps2-format-lights/complete-inventory.json'
    source_raw = source_path.read_bytes()
    inventory = json.loads(source_raw)
    frozen = next(x for x in inventory['inventory'] if x['family'] == 'XTRAIL')
    a = load_module('existing_vehicle_audit', ROOT / 'ps2-research/pc-port/docs/full-coverage/vehicles/audit.py')
    sys.path.insert(0, str(PRIOR / 'ps2-format-lights'))
    from complete_reader import decode_complete
    join = load_module('existing_menu_mesh_join', PRIOR / 'frontend-identity/mesh_join.py')
    manifest, _ = a.t.load_pak(a.PS2 / 'TNG.PAK')
    entries = [e for e in manifest['entries'] if e.get('path') == frozen['resource']]
    if len(entries) != 1:
        raise ValueError('Exact XTRAIL COMPLETE resource is missing or ambiguous')
    payload, provenance = a.t.read_payload(entries[0], a.PS2 / 'TNG.000')
    if a.sha(payload) != frozen['sha256']:
        raise ValueError('XTRAIL COMPLETE payload differs from frozen source identity')
    scene, trailer = decode_complete(payload)
    pc_path = a.PC / 'Xtrail/complete.dx'
    if a.sha(pc_path.read_bytes()) != frozen['pc_pair']['sha256']:
        raise ValueError('Xtrail complete.dx differs from frozen source identity')
    pc = a.parse_dx(pc_path)
    ps_faces = [f for m in scene.meshes for f in a.w.mesh_triangles(scene, m)[0]]
    # Derived from independently retained source bounds, not adjusted for matches.
    z_delta = frozen['bounds']['min'][2] - frozen['pc_pair']['bounds']['min'][2]
    translated = {}
    for tolerance in (.001, .005):
        rows = []
        for d in pc.physical_draws:
            faces = a.faces(pc, d)
            identity = join.corner_matches(faces, ps_faces, tolerance)
            candidate = join.corner_matches(shift_faces(faces, (0, 0, z_delta)), ps_faces, tolerance)
            rows.append({'draw_index': d.draw_index, 'triangles': len(faces),
                         'identity_matches': sum(r['matched'] for r in identity),
                         'candidate_translation_matches': sum(r['matched'] for r in candidate)})
        translated[str(tolerance)] = rows
    full = json.loads((PRIOR / 'frontend-identity/source-and-live-evidence.json').read_bytes())
    source_pc = next(s for s in full['source_inventory']['complete_resources'] if s['path'] == 'Xtrail/complete.dx')
    logs_root = Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')
    log_rows = []
    for path in sorted(logs_root.glob('frame*.jsonl'), key=lambda p:p.stat().st_mtime, reverse=True)[:4]:
        context = next((json.loads(line) for line in path.open(encoding='utf8')
                        if '"type":"race_epoch_snapshot"' in line or '"type": "race_epoch_snapshot"' in line), None)
        if context is None:
            # Format-independent bounded second pass.
            context = next((r for r in map(json.loads, path.open(encoding='utf8'))
                            if r.get('type') == 'race_epoch_snapshot'), {})
        log_rows.append({'file': path.name, 'sha256': a.sha(path.read_bytes()),
                         'frame': context.get('frame'), 'scene': context.get('scene'),
                         'frontend_context': frontend_observation(context),
                         'xtrail_owner_verified': False})
    report = {'schema_version': 1, 'phase': 'XTRAIL_FRONTEND_READINESS',
        'source_evidence': 'CONFIRMED_BY_BYTES', 'source_inputs_reverified': True,
        'frozen_inventory_sha256': hashlib.sha256(source_raw).hexdigest(),
        'ps2': {k:frozen[k] for k in ('resource','sha256','size','source_vertex_count','source_triangles','mesh_count','node_counts','named_and_indexed_nodes','bounds','meshes')},
        'trailer': trailer, 'packfs_provenance': provenance,
        'pc': source_pc, 'pc_bounds': frozen['pc_pair']['bounds'],
        'comparison': translated,
        'candidate_transform': {'pc_to_ps2_translation': [0,0,z_delta],
            'derivation': 'PS2 min-Z minus PC min-Z, held fixed before matching',
            'confidence': 'DIAGNOSTIC_REGISTRATION_ONLY',
            'independent_runtime_transform_proved': False,
            'suppression_authorized': False},
        'recent_log_inventory': log_rows,
        'current_frontend_owner_join': 'UNKNOWN',
        'replacement_status': 'NO_GO_PENDING_CURRENT_OWNER_AND_RESOURCE_JOIN',
        'missing_link': 'Current CarModel Egg -> en3d state/name/cached object -> current mirrored COMPLETE VB/IB set within stable VehicleSelect generation',
        'limitations': ['Source draws are not live draw ordinals.',
            'PS2 menu screenshot is COMPLETE; race screenshot cannot certify COMPLETE ownership.',
            'Position hashes exclude normals, UVs, colors and texture identity.',
            'No runtime memory reads, menu replacement, source mutation or collider transfer performed.']}
    (HERE/'readiness.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ps2_faces':len(ps_faces),'pc_faces':pc.triangle_count,
        'pc_records':len(pc.physical_draws),'unique_complete_records':sum(d['unique_to_complete_resource'] for d in source_pc['draws']),
        'offset':z_delta,'matches':{k:sum(x['candidate_translation_matches'] for x in v) for k,v in translated.items()},
        'frontend_capture_count':sum(r['frontend_context'] for r in log_rows)},indent=2))


if __name__ == '__main__':
    main()
