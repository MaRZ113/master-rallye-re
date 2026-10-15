"""Bounded original surface negative controls for future fleet CAR admission."""
from pathlib import Path
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path.insert(0, str(HERE))
import inventory as inv
spec = importlib.util.spec_from_file_location('existing_fleet_surface_match', PORT / 'docs/full-coverage/vehicles/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def main():
    coverage = json.loads((HERE / 'coverage.json').read_text())
    root = Path('D:/Game/Master Rallye PS2')
    pack, _ = a.t.load_pak(root / 'TNG.PAK')
    entries = {a.t.logical_path(e['path']).upper(): e for e in pack['entries'] if e['kind'] == 'file'}
    report = []
    for family in coverage['fleet']:
        src = family['models']['CAR']
        row = {'ps2_family': family['ps2_family'], 'pc_family': family['pc_family'],
               'runtime': 'NOT_GRANTED_SOURCE_SURFACE_CONTROL_ONLY', 'draws': []}
        report.append(row)
        if not family['pc_family']:
            row['decision'] = 'NO_VERIFIED_PC_COUNTERPART'
            continue
        raw, _ = a.t.read_payload(entries[src['resource']], root / 'TNG.000')
        if a.sha(raw) != src['sha256']:
            raise ValueError('CAR source drift')
        scene = a.r.decode_vehicle(raw)
        roots, conditional, meshes = [], [], []
        for m in scene.meshes:
            fs, _ = a.w.mesh_triangles(scene, m)
            if m['path'].count('.') > 1:
                conditional.extend(fs)
            else:
                roots.extend(fs)
                meshes.append((m, fs))
        rootidx, conditionalidx = a.index_faces(roots), a.index_faces(conditional)
        pc = a.parse_dx(a.PC / src['pc_compiled_source']['path'])
        selected_faces = []
        for draw, meta in zip(pc.physical_draws, src['pc_compiled_source']['draws']):
            fs = a.faces(pc, draw)
            hits = sum(a.matches(f, rootidx) for f in fs)
            chits = sum(a.matches(f, conditionalidx) for f in fs)
            glow = any('glow' in s.value.lower() or 'breaklightson' in s.value.lower()
                       for s in draw.texture_slots)
            named = draw.tag != 2 or draw.group_label is not None or '.' in draw.record_path
            accepted = hits == len(fs) and not chits and not glow and not named
            row['draws'].append({**meta, 'exact_unconditional_faces': hits,
                                 'exact_conditional_faces': chits, 'native_glow_or_on_texture': glow,
                                 'named_or_alternative': named, 'surface_candidate': accepted})
            if accepted:
                selected_faces.extend(fs)
        selected_index = a.index_faces(selected_faces)
        row['root_coverage'] = [{'path': m['path'], 'faces': len(fs),
                                 'covered_by_selected_pc_faces': sum(a.matches(f, selected_index) for f in fs),
                                 'mode': next(x['mode'] for x in src['meshes'] if x['path'] == m['path'])}
                                for m, fs in meshes]
        row['candidate_pc_records'] = sum(d['surface_candidate'] for d in row['draws'])
        row['fully_covered_ps2_roots'] = sum(x['faces'] == x['covered_by_selected_pc_faces'] for x in row['root_coverage'])
        row['decision'] = 'PER_ROOT_PARTITION_REQUIRED_NOT_FULL_FLEET_RACE_CERTIFICATE'
        print(family['ps2_family'], row['candidate_pc_records'], row['fully_covered_ps2_roots'], flush=True)
    (HERE / 'car-candidates.json').write_text(json.dumps({'schema_version': 1, 'tolerance': .001,
        'method': 'UNSIGNED_TRIANGLE_MAX_CORNER_DISTANCE_EXISTING_GEOM1', 'fleet': report}, indent=2) + '\n')


if __name__ == '__main__':
    main()
