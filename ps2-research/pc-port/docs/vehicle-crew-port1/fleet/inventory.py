"""Read-only fleet source/PC identity inventory; metadata only, no runtime grant."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path[:0] = [str(ROOT / 'ps2-research/tools'), str(PORT / 'tools'),
               'D:/Game/Master Rallye/master-rallye-re-course/src']
import tngtool as t
import reflection_runtime as r
import psbtool
from prepare_reflection_pilot import geometry_signature
from master_rallye.dx import parse_dx


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pair(family):
    # Previous name-only CAR audit paired the wrong PS2 Forester. Never inherit it.
    if family in ('FORESTER', 'MOONBUGGY', 'TANK'):
        return None
    return 'FORESTER' if family == 'WOOLDAND' else family


def main():
    ps2 = Path('D:/Game/Master Rallye PS2')
    pc = Path('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles')
    r.w.verify_inputs(ps2)
    manifest, _ = t.load_pak(ps2 / 'TNG.PAK')
    entries = {t.logical_path(e['path']).upper(): e for e in manifest['entries'] if e['kind'] == 'file'}
    old_path = PORT / 'docs/vehicle-model-port1/ps2-format-lights/complete-inventory.json'
    old = json.loads(old_path.read_text())
    spec = importlib.util.spec_from_file_location('fleet_complete', old_path.with_name('complete_reader.py'))
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    pc_dirs = {p.name.upper(): p for p in pc.iterdir() if p.is_dir()}
    rows = []
    for known in old['inventory']:
        family = known['family']
        mapped = pair(family)
        directory = pc_dirs.get(mapped)
        row = {'ps2_family': family, 'pc_family': directory.name if directory else None,
               'pairing': 'PROVED_WOOLDAND_PC_FORESTER' if family == 'WOOLDAND' else
               'SEPARATE_PS2_MODEL_NO_PC_ALIAS' if family == 'FORESTER' else
               'NO_PC_COUNTERPART' if not directory else 'SOURCE_FAMILY_PAIR', 'models': {}}
        rows.append(row)
        for role in ('COMPLETE', 'CAR'):
            key = '\\TNG\\DATAPSM\\VEHICLES\\' + family + '\\' + role + '.PSM'
            raw, _ = t.read_payload(entries[key], ps2 / 'TNG.000')
            if role == 'COMPLETE' and sha(raw) != known['sha256']:
                raise ValueError('Prior original COMPLETE source drift: ' + family)
            if role == 'COMPLETE':
                scene, trailer = reader.decode_complete(raw)
            else:
                scene, trailer = r.decode_vehicle(raw), None
            modes, unresolved, texture_rows, mesh_rows = collections.Counter(), [], {}, []
            total = root_total = 0
            for m in scene.meshes:
                secondary = next((s['name'] for s in m['textures'] if s['slot'] == 1), '')
                contract = r.material_contract(m['material'], secondary)
                mode = contract['mode']
                modes[str(mode)] += 1
                fs, _ = r.w.mesh_triangles(scene, m)
                total += len(fs)
                conditional = m['path'].count('.') > 1
                if not conditional:
                    root_total += len(fs)
                mesh_rows.append({'path': m['path'], 'node_offset': m['node_offset'],
                                  'mode': mode, 'material': m['material'], 'faces': len(fs),
                                  'conditional': conditional, 'texture_slots': m['textures']})
                for s in m['textures']:
                    tx = t.logical_path('\\TNG\\DATAPSM\\' + s['name'] + '.GXI').upper()
                    if tx not in texture_rows:
                        if tx not in entries:
                            unresolved.append(tx)
                            texture_rows[tx] = {'status': 'MISSING'}
                            continue
                        b, _ = t.read_payload(entries[tx], ps2 / 'TNG.000')
                        info = psbtool.parse_gxi(b)
                        texture_rows[tx] = {'sha256': sha(b), 'width': info['width'],
                                            'height': info['height'], 'status': 'VERIFIED_ORIGINAL_GXI'}
            blockers = []
            if not directory:
                blockers.append('NO_VERIFIED_PC_REPLACEMENT_OWNER')
            unsupported = sorted(k for k in modes if k not in ('0', '1', '3', '20', 'None'))
            if unsupported:
                blockers.append('UNIMPLEMENTED_PRIVATE_MATERIAL_MODES_' + '_'.join(unsupported))
            if modes.get('None'):
                blockers.append('PER_MESH_DEFAULT_MATERIAL_BINDING_REQUIRES_VALIDATION')
            if unresolved:
                blockers.append('UNRESOLVED_AUTHORED_TEXTURE')
            if role == 'CAR' and scene.extra_nodes:
                blockers.append('CONDITIONAL_BRANCH_ADMISSION_REQUIRED_KEEP_NATIVE_UNTIL_PROVED')
            result = {'resource': key, 'sha256': sha(raw), 'vertices': scene.vertex_count,
                      'faces_all_authored_branches': total, 'faces_unconditional': root_total,
                      'meshes': mesh_rows, 'node_counts': scene.node_counts,
                      'wrappers': scene.extra_nodes, 'trailer': trailer,
                      'material_mode_mesh_counts': dict(sorted(modes.items())),
                      'textures': texture_rows, 'blockers': blockers,
                      'decoder': 'SUPPORTED_ORIGINAL_SOURCE_GRAMMAR',
                      'runtime_admission': 'XTRAIL_EXISTING_PIPELINE' if family == 'XTRAIL' else
                                           'NOT_YET_IMPLEMENTED_CURRENT_OWNER_AND_SUPPRESSION_CERTIFICATE_REQUIRED'}
            row['models'][role] = result
            target = directory / (role.lower() + '.dx') if directory else None
            if target and target.exists():
                model = parse_dx(target)
                draws = []
                for d in model.physical_draws:
                    ids = model.draw_global_indices(d)
                    fs = [tuple(model.vertices.positions[i] for i in ids[n:n+3])
                          for n in range(0, len(ids), 3)]
                    draws.append({'record_path': d.record_path, 'record_offset': d.offset,
                                  'tag': d.tag, 'group_label': d.group_label,
                                  'declared_child_count': d.declared_child_count,
                                  'vertex_base': d.vertex_base, 'index_start': d.index_start,
                                  'vertices': d.local_vertex_max + 1,
                                  'index_count': d.index_count, 'faces': len(fs),
                                  'geometry_sha256': geometry_signature(fs),
                                  'ordered_texture_slots': [s.value for s in d.texture_slots]})
                result['pc_compiled_source'] = {'path': target.relative_to(pc).as_posix(),
                                                'sha256': sha(target.read_bytes()), 'draws': draws}
            print(family, role, len(scene.meshes), total, flush=True)
    report = {'schema_version': 1, 'phase': 'PS2-VEHICLE-CREW-PORT1',
              'evidence': 'ORIGINAL_PAYLOADS_AND_PC_COMPILED_SOURCES_REDECODED',
              'runtime_claim': 'SOURCE_ELIGIBILITY_IS_NOT_RUNTIME_ADMISSION',
              'prior_complete_inventory_sha256': sha(old_path.read_bytes()), 'fleet': rows}
    (HERE / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Vehicle fleet source and runtime-readiness matrix', '',
             'Original PS2 payloads redecoded; every existing PC compiled source has exact per-record geometry signatures.',
             'These are source identities, never historical live addresses or draw ordinals. New live admission is still required.', '',
             '| PS2 | PC | COMPLETE meshes/faces | CAR unconditional/all faces | Private material modes | Source exceptions |',
             '|---|---|---:|---:|---|---|']
    for row in rows:
        co, ca = row['models']['COMPLETE'], row['models']['CAR']
        exceptions = sorted(set(co['blockers'] + ca['blockers']))
        lines.append('|%s|%s|%d / %d|%d / %d|%s|%s|' %
                     (row['ps2_family'], row['pc_family'] or 'NONE', len(co['meshes']),
                      co['faces_all_authored_branches'], ca['faces_unconditional'], ca['faces_all_authored_branches'],
                      ','.join(co['material_mode_mesh_counts']), '; '.join(exceptions) or 'No source parser/material exception'))
    lines += ['', 'All COMPLETE trees are flat roots, so the already verified caller/cache transform path is structurally reusable.',
              'That does not authorize suppressing another family without an exact full compiled-record certificate.',
              'CAR named/indexed branches represent alternative brake/glass states; summed totals are not simultaneous visibility.',
              'WOOLDAND maps to PC Forester. PS2 FORESTER is a separate model and has no permitted alias here.',
              'Mode2 (Mattserati/Simmbugghini) and mode21 (UFO) are precise private-render material gaps, not parse failures.', '']
    (HERE / 'coverage.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
