"""Pinned CAR/WHEEL source contracts and ignored lossless CAR prototypes.

No native/runtime ownership is granted by this source inventory.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path[:0] = [str(ROOT / 'ps2-research/tools'), str(PORT / 'tools'),
               str(ROOT.parent / 'master-rallye-re-course/src')]
import tngtool as t
import reflection_runtime as r
import psbtool
import prepare_vehicle_models as private
from master_rallye.dx import parse_dx
from prepare_reflection_pilot import geometry_signature

PS2 = Path('D:/Game/Master Rallye PS2')
PC = ROOT.parent / 'corpora/retail/Data.sma_unpacked/DataGx/Vehicles'
spec = importlib.util.spec_from_file_location('proved_wheel_trailer_reader',
    PORT / 'docs/vehicle-model-port1/ps2-format-lights/complete_reader.py')
wheel_reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wheel_reader)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pc_record(model, draw):
    n = draw.local_vertex_max + 1
    ids = model.draw_global_indices(draw)
    faces = [tuple(model.vertices.positions[i] for i in ids[k:k + 3])
             for k in range(0, len(ids), 3)]
    xyz = b''.join(struct.pack('<3f', *model.vertices.positions[draw.vertex_base + i])
                   for i in range(n))
    uv = b''.join(struct.pack('<2f', *model.uv_sets[0].values[draw.vertex_base + i])
                  for i in range(n))
    triangles = [tuple(i - draw.vertex_base for i in ids[k:k + 3])
                 for k in range(0, len(ids), 3)]
    topology = sorted(tuple(sorted(face)) for face in triangles)
    native = [(face[1], face[0], face[2]) for face in triangles]
    unconditional = draw.tag == 2 and draw.group_label is None and '.' not in draw.record_path
    return dict(record_path=draw.record_path, record_offset=draw.offset,
                top_level_index=draw.top_level_index, tag=draw.tag,
                group_label=draw.group_label, vertices=n, faces=len(faces),
                vertex_base_source_only=draw.vertex_base,
                ordered_texture_slots=[s.value for s in draw.texture_slots],
                geometry_sha256=geometry_signature(faces), ordered_position_sha256=sha(xyz),
                uv_topology_sha256=sha(uv + b''.join(struct.pack('<3I', *f) for f in topology)),
                native_uv_winding_sha256=sha(uv + b''.join(struct.pack('<3I', *f) for f in native)),
                whole_chassis_suppress_candidate=unconditional,
                admission='CURRENT_NATIVE_OWNER_AND_EXACT_SOURCE_CERTIFICATE_REQUIRED')


def mesh_row(scene, mesh):
    primary = next((s for s in mesh['textures'] if s['slot'] == 0), None)
    authored_secondary = next((s['name'] for s in mesh['textures'] if s['slot'] == 1), '')
    # Original primary-absent branch bypasses BOTH source-name copies.
    secondary = authored_secondary if primary else ''
    contract = r.material_contract(mesh['material'], secondary)
    mode = contract['mode']
    token = mesh['material'].lower()
    generic_unknown = token in ('$shader(crashiny)', '$shader(carbrakelight)')
    if mode is None and ('$shader(' not in token or generic_unknown):
        mode = 0 if not primary else 5 if secondary and all(primary['flags'][:2]) else 3 if secondary else 1
        contract = {**contract, 'effective_mode': mode,
                    'generic_authority': 'SHARED_ORIGINAL_PSM_CONSTRUCTOR_SOURCE_PRESENCE_AND_FLAGS; FIXED_REGISTRY_UNKNOWN_TOKEN_NO_WRITES',
                    'effective_secondary': secondary if mode in (3, 5) else None,
                    'secondary_policy': 'AUTHORED_GENERIC' if mode in (3, 5) else 'INACTIVE'}
    faces, _ = r.w.mesh_triangles(scene, mesh)
    conditional = mesh['path'].count('.') > 1
    return dict(path=mesh['path'], node_offset=mesh['node_offset'],
                faces=len(faces), mode=mode, material=mesh['material'],
                contract=contract, ordered_texture_slots=mesh['textures'],
                primary_default_resource='\\TNG\\DEFAULT.GXI' if not primary else None,
                primary_default_sha256='ad2960c11407794294b6d188db3660478f21ecea1a9b0fef4e69fc0a4ccef6d5' if not primary else None,
                mixed_reflection=mode in (3, 21) and contract.get('effective_secondary') == 'CommonTextures\\rendertarget64x64',
                conditional=conditional,
                action='KEEP_NATIVE_BRANCH' if conditional else 'PRIVATE_WHOLE_CHASSIS_SOURCE',
                local_transform='ORIGINAL_MODEL_LOCAL_NO_MATRIX_WRAPPER',
                geometry_sha256=geometry_signature(faces))


def prepare_source(raw, provenance, scene, family, resource, entries):
    textures, texture_meta, indices, meshes, unresolved = [], [], {}, [], []
    for mesh in scene.meshes:
        slots = []
        for slot in mesh['textures']:
            key = t.logical_path('\\TNG\\DATAPSM\\' + slot['name'] + '.GXI').upper()
            if key not in indices:
                entry = entries.get(key)
                if entry:
                    data, tx_provenance = t.read_payload(entry, PS2 / 'TNG.000')
                    decoded = psbtool.parse_gxi(data)
                    indices[key] = len(textures)
                    textures.append(data)
                    texture_meta.append(dict(path=entry['path'], sha256=sha(data),
                                             width=decoded['width'], height=decoded['height'],
                                             provenance=tx_provenance))
                else:
                    unresolved.append(key)
            slots.append({**slot, 'private_texture_index': indices.get(key)})
        meshes.append(dict(path=mesh['path'], node_offset=mesh['node_offset'],
                           material_offset=mesh['material_offset'], material=mesh['material'],
                           textures=slots, strips=mesh['strips'],
                           visibility='ORIGINAL_CONDITIONAL_HIERARCHY_RETAINED_NOT_RUNTIME_ADMITTED'))
    metadata = dict(family=family, role='CAR', source_resource=resource,
                    source_sha256=sha(raw), source_provenance=provenance,
                    coordinates='ORIGINAL_MODEL_LOCAL', vertex_layout='ORIGINAL_52_BYTE_LE',
                    meshes=meshes, textures=texture_meta, extra_nodes=scene.extra_nodes,
                    unresolved_textures=sorted(set(unresolved)),
                    runtime_admission='DISABLED_SOURCE_ONLY_PROTOTYPE')
    data = private.serialize(metadata, raw[32:32 + scene.vertex_count * 52], textures)
    checked = private.validate(data)
    path = PORT / '.assets/vehicles' / (family + '-CAR-SOURCE.ps2vehicle')
    if path.exists() and path.read_bytes() != data:
        raise ValueError('Refusing prototype drift: ' + family)
    path.write_bytes(data)
    return dict(filename=path.name, bytes=len(data), sha256=sha(data),
                source_sha256=checked['source_sha256'], textures=len(textures),
                unresolved_textures=sorted(set(unresolved)),
                status='SOURCE_ONLY_NO_NATIVE_SUPPRESSION_OR_RUNTIME_ENABLEMENT')


def main():
    r.w.verify_inputs(PS2)
    archive, _ = t.load_pak(PS2 / 'TNG.PAK')
    entries = {t.logical_path(e['path']).upper(): e for e in archive['entries'] if e['kind'] == 'file'}
    prior = json.loads((PORT / 'docs/vehicle-crew-port1/fleet/coverage.json').read_text())
    prior_candidates = json.loads((PORT / 'docs/vehicle-crew-port1/fleet/car-candidates.json').read_text())
    conditional_proofs = {f['ps2_family']: {d['record_path']: d for d in f.get('draws', [])}
                          for f in prior_candidates['fleet']}
    result = []
    for old in prior['fleet']:
        family, pc_family = old['ps2_family'], old['pc_family']
        row = dict(ps2_family=family, pc_family=pc_family,
                   enabled=False, runtime_status='NOT_GRANTED_BY_SOURCE_AUDIT')
        result.append(row)
        if not pc_family or family == 'FORKLIFT':
            row['decision'] = 'NO_PC_COUNTERPART' if not pc_family else 'EXCLUDED_FORKLIFT'
            continue
        original = old['models']['CAR']
        key = t.logical_path(original['resource']).upper()
        raw, provenance = t.read_payload(entries[key], PS2 / 'TNG.000')
        if sha(raw) != original['sha256']:
            raise ValueError('Original CAR source drift: ' + family)
        scene = r.decode_vehicle(raw)
        native_path = PC / pc_family / 'car.dx'
        if sha(native_path.read_bytes()) != original['pc_compiled_source']['sha256']:
            raise ValueError('Original PC CAR source drift: ' + family)
        model = parse_dx(native_path)
        records = [pc_record(model, d) for d in model.physical_draws]
        for record in records:
            proof = conditional_proofs[family][record['record_path']]
            if proof['geometry_sha256'] != record['geometry_sha256']:
                raise ValueError('Conditional source proof drift: ' + family)
            record['source_conditional_face_hits'] = proof['exact_conditional_faces']
            record['original_source_glow_or_on_guard'] = proof['native_glow_or_on_texture']
            if proof['exact_conditional_faces'] or proof['native_glow_or_on_texture']:
                record['whole_chassis_suppress_candidate'] = False
                record['admission'] = 'KEEP_NATIVE_CONDITIONAL_GLOW_OR_ON_SOURCE_BOUNDARY'
        roots = [mesh_row(scene, m) for m in scene.meshes]
        body_sources = [m for m in roots if not m['conditional']]
        row.update(source_ps2_car_sha256=sha(raw), source_pc_car_sha256=sha(native_path.read_bytes()),
                   source_ps2_vertices=scene.vertex_count,
                   original_pc_top_level_record_count=model.declared_top_level_record_count,
                   native_sources=records, source_roots=roots,
                   native_suppression_record_paths=[d['record_path'] for d in records if d['whole_chassis_suppress_candidate']],
                   native_suppression_physical_record_mask_hex=hex(sum(1 << i for i, d in enumerate(records) if d['whole_chassis_suppress_candidate'])),
                   private_unconditional_mesh_indices=[i for i, m in enumerate(roots) if not m['conditional']],
                   private_unconditional_root_paths=[m['path'] for m in body_sources],
                   private_unconditional_faces=sum(m['faces'] for m in body_sources),
                   native_conditional_record_paths=[d['record_path'] for d in records if not d['whole_chassis_suppress_candidate']],
                   source_conditional_root_paths=[m['path'] for m in roots if m['conditional']],
                   root_map_policy='EXACT_CURRENT_WHOLE_CHASSIS_OWNER: ENTIRE_NATIVE_SUPPRESSION_SET_TO_ENTIRE_PRIVATE_UNCONDITIONAL_ROOT_SET; NO_PER_MATERIAL_OR_CREW_SUBSET_INFERENCE',
                   static_crew_interior_policy='WHOLE_UNCONDITIONAL_SOURCE_REPLACEMENT_INCLUDES_ALL_PS2_CREW_AND_INTERIOR; NO_TEXTURE_BASED_CREW_DELETION',
                   required_current_transform='EVERY_SUPPRESSED_NATIVE_RECORD_MUST_SHARE_CURRENT_CHASSIS_WORLD; OTHERWISE_KEEP_STOCK',
                   damage_policy='CURRENT_FAMILY_SPECIFIC_DEFORMATION_CERTIFICATE_REQUIRED_OR_EXPLICIT_STOCK_DAMAGE_FALLBACK')
        row['prototype'] = prepare_source(raw, provenance, scene, family, key, entries)
        material_blocks = []
        for m in body_sources:
            if m['mode'] not in (0, 1, 2, 3, 5, 20, 21):
                material_blocks.append(dict(path=m['path'], mode=m['mode'], material=m['material'],
                                            reason='UNPROVED_OR_UNSUPPORTED_UNCONDITIONAL_MATERIAL'))
        row['material_blocks'] = material_blocks
        wheel_key = t.logical_path('\\TNG\\DATAPSM\\VEHICLES\\' + family + '\\WHEEL.PSM').upper()
        wheel_native = PC / pc_family / 'wheel.dx'
        if wheel_key in entries and wheel_native.exists():
            wheel_raw, _ = t.read_payload(entries[wheel_key], PS2 / 'TNG.000')
            wheel_scene, wheel_trailer = wheel_reader.decode_complete(wheel_raw)
            wheel_pc = parse_dx(wheel_native)
            row['wheel_contract'] = dict(source_ps2_sha256=sha(wheel_raw), source_pc_sha256=sha(wheel_native.read_bytes()),
                                         source_ps2_vertices=wheel_scene.vertex_count,
                                         original_post_tree_auxiliary=wheel_trailer,
                                         source_meshes=[mesh_row(wheel_scene, m) for m in wheel_scene.meshes],
                                         native_sources=[pc_record(wheel_pc, d) for d in wheel_pc.physical_draws],
                                         transform='SEPARATE_CURRENT_WHEEL_OWNER_WORLD_PER_STEERING_SUSPENSION_SPIN; NEVER_CHASSIS_WORLD',
                                         admission='CURRENT_CHASSIS_FAMILY_JOIN_AND_EACH_WHEEL_SOURCE_CERTIFICATE_REQUIRED')
        else:
            row['wheel_contract'] = dict(status='MISSING_EXPLICIT_SOURCE_OR_NATIVE_WHEEL_RESOURCE',
                                         ps2_resource_present=wheel_key in entries, pc_resource_present=wheel_native.exists())
        row['decision'] = 'SOURCE_CONVERSION_READY_WITH_EXPLICIT_RUNTIME_AND_DAMAGE_GATES' if not material_blocks else 'MATERIAL_CONTRACT_BLOCKED'
        print(family, len(row['native_suppression_record_paths']), len(body_sources), row['private_unconditional_faces'], len(material_blocks), flush=True)
    report = dict(schema=1, original_ps2_families=29, paired_including_forklift=26,
                  selected_race_families=25, enabled_by_this_audit=0,
                  runtime_grant='NONE_SOURCE_CERTIFICATES_AND_PROTOTYPES_ONLY', fleet=result)
    (HERE / 'fleet-car-contracts.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
