"""Bounded retained Terrano brake-pair inspection; never an admission predicate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')
FILES = {'released': ('frame-2080-d1-00001288.jsonl', [263]),
         'held': ('frame-2080-d1-00001569.jsonl', [290, 295])}
STATE_KEYS = {'ZENABLE': 7, 'ZWRITEENABLE': 14, 'ALPHATESTENABLE': 15,
              'ALPHABLENDENABLE': 27, 'SRCBLEND': 19, 'DESTBLEND': 20,
              'ZFUNC': 23, 'CULLMODE': 22, 'FOGENABLE': 28}


def inspect(path, ordinals):
    data = path.read_bytes()
    rows = [json.loads(line) for line in data.splitlines()]
    begin = rows[0]
    epoch = next(r for r in rows if r['type'] == 'race_epoch_snapshot')
    if begin['exe_sha256'] != 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4':
        raise ValueError('Unsupported original PC executable identity')
    candidates = []
    for ordinal in ordinals:
        draw = next(r for r in rows if r['type'] == 'draw' and r['draw_index'] == ordinal)
        state = draw['state']
        before = max((r['sequence'] for r in rows if r['type'] == 'draw' and
                      r['sequence'] < draw['sequence']), default=0)
        after = min((r['sequence'] for r in rows if r['type'] == 'draw' and
                     r['sequence'] > draw['sequence']), default=draw['sequence'] + 1)
        overrides = [{'sequence': r['sequence'], 'method': r['method'],
                      'arguments': r['arguments'], 'hresult': r['result']}
                     for r in rows if r['type'] == 'native_override' and
                     before < r['sequence'] < after]
        candidates.append({
            'captured_draw_ordinal_not_persistent_identity': ordinal,
            'sequence': draw['sequence'], 'method': draw['method'],
            'arguments': draw['arguments'], 'hresult': draw['result'],
            'fvf': state['vertex_shader'], 'stream0': state['streams'][0],
            'indices': state['indices'], 'textures': state['textures'][:2],
            'native_logical_states': {name: state['render_states'].get(str(key))
                                      for name, key in STATE_KEYS.items()},
            'stage0_stage1': [{key: stage.get(key) for key in
                              ['1', '2', '3', '4', '5', '6', '11', '24']}
                             for stage in state['texture_stage_states'][:2]],
            'world_view_projection': {key: state['matrices'][key]
                                      for key in ['256', '2', '3']},
            'object_classification': draw['object_classification'],
            'identity_source': draw['object_identity_source_at_draw'],
            'surrounding_native_overrides': overrides,
            'uploaded_geometry_byte_identity_verified': False})
    return {'file': path.name, 'sha256': hashlib.sha256(data).hexdigest(),
            'frame': begin['frame'], 'exe_sha256': begin['exe_sha256'],
            'proxy_sha256': begin['proxy_sha256'],
            'course': epoch['root_job_success']['scene'],
            'live_race_certificate': epoch['live_certificate_valid'],
            'race_lifecycle_generation': epoch['race_lifecycle_generation'],
            'owner_lifetime': epoch['owner']['lifetime'], 'candidates': candidates,
            'total_native_draw_records': sum(r['type'] == 'draw' for r in rows)}


def main():
    source = json.loads((HERE.parent / 'terrano-source.json').read_bytes())
    relevant = [d for d in source['draws'] if d['source_draw'] in [30, 31, 32]]
    report = {'schema_version': 1, 'phase': 'TERRANO_NATIVE_BRAKE_PAIR',
              'observation_grade': 'CONFIRMED_BY_RUNTIME',
              'source_join_grade': 'STATIC_INFERENCE_LAYOUT_CORRELATION',
              'control_labels': 'USER_RUNTIME_OBSERVATION released/held brake',
              'source_identity': {k: source[k] for k in ['family', 'pc_sha256', 'ps2_sha256']},
              'source_lamp_records': relevant,
              'frames': {name: inspect(LOGS / file, ids) for name, (file, ids) in FILES.items()},
              'limitations': ['Captured ordinals/pointers/ranges are observations only.',
                              'No current CPU upload bytes or immutable face hashes in F10.',
                              'No controller-slot direct read or function call performed.',
                              'World and camera pose changed; no pixel-level visual comparison.',
                              'Original PC glow blend is not proof of original PS2 mode14 GS state.']}
    (HERE / 'runtime-join.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Saved two frame identities, three lamp candidates and original native states.')


if __name__ == '__main__':
    main()
