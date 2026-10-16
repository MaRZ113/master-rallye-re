"""Full unconditional original CAR conversion. No runtime enablement.

All original static crew/interior are included exactly once. Named alternatives,
brake ON/glow and independent WHEEL resources never enter the mesh/index table.
"""
from pathlib import Path
import collections
import importlib.util
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path[:0] = [str(PORT / 'tools'), str(ROOT / 'ps2-research/tools')]
import prepare_vehicle_models as source

spec = importlib.util.spec_from_file_location('proven_car_vertex_gxi_conversion',
    PORT / 'docs/vehicle-model-port2/assets/convert_complete.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def convert(family, default):
    prototype = PORT / '.assets/vehicles' / family['prototype']['filename']
    data = prototype.read_bytes()
    if c.sha(data) != family['prototype']['sha256']:
        raise ValueError('Pinned private source prototype changed')
    source.validate(data)
    _, _, size, count, tx_count, source_sha = source.HEADER.unpack_from(data)
    offset = source.HEADER.size
    meta = json.loads(data[offset:offset + size])
    offset += size
    raw = data[offset:offset + count * 52]
    offset += count * 52
    original_textures = []
    for _ in range(tx_count):
        size = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        original_textures.append(data[offset:offset + size])
        offset += size
    if source_sha.hex() != family['source_ps2_car_sha256'] or meta['family'] != family['ps2_family']:
        raise ValueError('Original family/source mismatch')
    selected = {m['path']: m for m in family['source_roots'] if not m['conditional']}
    if len(selected) != len(family['private_unconditional_root_paths']):
        raise ValueError('Repeated private source root')
    textures, texture_rows, remapped = [], [], {}

    def texture(index):
        if index not in remapped:
            original = default if index == 'DEFAULT' else original_textures[index]
            info, pixels = c.texture(original)
            expected = c.DEFAULT_SHA if index == 'DEFAULT' else meta['textures'][index]['sha256']
            if c.sha(original) != expected:
                raise ValueError('Pinned original texture changed')
            remapped[index] = len(textures)
            textures.append(struct.pack('<3I', info['width'], info['height'], len(pixels)) + pixels)
            texture_rows.append(dict(path='\\TNG\\DEFAULT.GXI' if index == 'DEFAULT' else meta['textures'][index]['path'],
                                     sha256=expected, argb_sha256=c.sha(pixels),
                                     width=info['width'], height=info['height']))
        return remapped[index]

    indices, meshes, mesh_rows = [], [], []
    for mesh in meta['meshes']:
        if mesh['path'] not in selected:
            continue
        policy = selected[mesh['path']]
        mode = policy['mode']
        if mode not in (0, 1, 2, 3, 5, 20, 21):
            raise ValueError('Unsupported exact source mode at ' + mesh['path'])
        slots = [c.NONE] * 3
        authored_primary = next((s for s in mesh['textures'] if s['slot'] == 0), None)
        authored_secondary = next((s for s in mesh['textures'] if s['slot'] == 1), None)
        if authored_primary:
            slots[0] = texture(authored_primary['private_texture_index'])
        elif policy['primary_default_sha256'] == c.DEFAULT_SHA:
            slots[0] = texture('DEFAULT')
        else:
            raise ValueError('Missing original primary binding contract')
        if mode in (3, 5, 21) and authored_primary and authored_secondary:
            slots[1] = texture(authored_secondary['private_texture_index'])
        elif mode in (5, 21) and not policy['mixed_reflection']:
            raise ValueError('Missing source secondary for weighted material')
        ids, diagnostics = c.indices_for_mesh(raw, mesh)
        if len(ids) // 3 != policy['faces']:
            raise ValueError('Source triangle fidelity changed')
        meshes.append(c.MESH.pack(mesh['node_offset'], mode, *slots, len(indices), len(ids)))
        primary = authored_primary['name'].lower() if authored_primary else ''
        used = {i for i in ids}
        u = [struct.unpack_from('<f', raw, i * 52 + 20)[0] for i in used]
        wrap_u = 'tread' in primary and (min(u) < 0 or max(u) > 1)
        mesh_rows.append(dict(path=mesh['path'], node_offset=mesh['node_offset'],
                              material=mesh['material'], mode=mode, texture_indices=slots,
                              first_index=len(indices), index_count=len(ids), faces=len(ids) // 3,
                              contract=policy['contract'], mixed_reflection=policy['mixed_reflection'],
                              primary_u_wrap=wrap_u, primary_default=not bool(authored_primary),
                              source_texture_slots=mesh['textures'], **diagnostics))
        indices.extend(ids)
    if len(indices) // 3 != family['private_unconditional_faces']:
        raise ValueError('Incomplete or duplicated source chassis')
    manifest = dict(schema_version=2, role='FLEET_RACE_WHOLE_UNCONDITIONAL_CAR',
                     source_sha256=source_sha.hex(), pc_source_sha256=family['source_pc_car_sha256'],
                     source_prototype_sha256=family['prototype']['sha256'],
                     family=family['ps2_family'], meshes=mesh_rows, texture_upload=texture_rows,
                     excluded_source_conditional_paths=family['source_conditional_root_paths'],
                     crew='ALL_ORIGINAL_STATIC_CREW_INCLUDED_ONCE; SUPPRESS_CORRESPONDING_FULL_PC_SET',
                     coordinates='ORIGINAL_MODEL_LOCAL_CURRENT_CHASSIS_WORLD_REQUIRED',
                     normals='ORIGINAL_SOURCE_NO_NORMALIZATION', alpha='ORIGINAL_STORED_ALPHA_NO_REMAP',
                     primary_orientation='RAW_SOURCE_UV_RUNTIME_V_EQUALS_1_MINUS_V',
                     winding='ORIGINAL_ORDERED_SOURCE_KICKS_CULL_NONE',
                     native_suppression=family['native_suppression_record_paths'],
                     runtime='DISABLED_UNTIL_CURRENT_FAMILY_OWNER_SOURCE_WORLD_RESOURCE_CERTIFICATES')
    text = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    binary = (c.HEADER.pack(c.MAGIC, 2, len(text), len(meshes), count, len(indices), len(textures), source_sha)
              + text + b''.join(meshes) + b''.join(c.vertex(raw, i) for i in range(count))
              + struct.pack('<' + 'I' * len(indices), *indices) + b''.join(textures))
    selected_sources = [s for s in family['native_sources'] if s['whole_chassis_suppress_candidate']]
    return binary, dict(family=family['pc_family'], ps2_family=family['ps2_family'],
                        filename=family['ps2_family'] + '-CAR-FLEET.ps2model',
                        sha256=c.sha(binary), bytes=len(binary), vertices=count,
                        indices=len(indices), textures=len(textures), ps2_meshes=len(meshes),
                        original_ps2_source_sha256=source_sha.hex(), original_pc_source_sha256=family['source_pc_car_sha256'],
                        pc_sources=selected_sources,
                        native_root_count_candidate=family['original_pc_top_level_record_count'],
                        mesh_secondary_kinds=[dict(path=m['path'], mode=m['mode'],
                                                  mixed_reflection=m['mixed_reflection'],
                                                  primary_u_wrap=m['primary_u_wrap']) for m in mesh_rows],
                        excluded_conditional_native_sources=[s for s in family['native_sources'] if not s['whole_chassis_suppress_candidate']],
                        includes_static_crew=True, includes_conditional_geometry=False,
                        includes_independent_wheels=False, enabled=False,
                        damage='FAMILY_SPECIFIC_HEALTHY_REFERENCE_AND_DEFORMATION_CONTRACT_NOT_GRANTED_HERE')


def main():
    report = json.loads((HERE / 'fleet-car-contracts.json').read_text())
    default = (PORT / '.assets/vehicles/XTRAIL-default.gxi').read_bytes()
    if c.sha(default) != c.DEFAULT_SHA:
        raise ValueError('Original DEFAULT.GXI changed')
    profiles, rejected = [], []
    for family in report['fleet']:
        if 'prototype' not in family:
            continue
        try:
            data, profile = convert(family, default)
        except ValueError as error:
            rejected.append(dict(family=family['ps2_family'], error=str(error)))
            continue
        path = c.private_output(PORT / '.assets/vehicles' / profile['filename'])
        if path.exists() and path.read_bytes() != data:
            raise ValueError('Refusing existing private runtime prototype drift: ' + path.name)
        path.write_bytes(data)
        profiles.append(profile)
        print(profile['ps2_family'], profile['ps2_meshes'], profile['indices'] // 3, profile['sha256'], flush=True)
    owners = collections.defaultdict(set)
    for family in report['fleet']:
        for src in family.get('native_sources', []):
            owners[(src['vertices'], src['faces'], src['geometry_sha256'])].add(family['pc_family'])
    for profile in profiles:
        for src in profile['pc_sources']:
            src['unique_family_in_paired_car_corpus'] = len(owners[(src['vertices'], src['faces'], src['geometry_sha256'])]) == 1
    output = dict(schema=1, profiles=profiles, rejected=rejected,
                   source_contracts_sha256=c.sha((HERE / 'fleet-car-contracts.json').read_bytes()),
                   runtime_admission='NONE_SOURCE_READY_ONLY')
    (HERE / 'race-profiles.json').write_text(json.dumps(output, indent=2) + '\n')
    lines = ['#pragma once', '#include <cstddef>', '#include <cstdint>',
             '// Generated original-source identity profiles; not runtime admission.',
             'namespace gfx2::ps2port {',
             'struct FleetRaceSource { const char *geometry,*orderedPosition,*uvTopology,*uvWinding; unsigned vertices,triangles; bool unique; };',
             'struct FleetRaceProfile { const char *family,*ps2Family,*filename,*sha; size_t size; unsigned vertices,indices,textures,ps2Meshes,pcDrawCount,nativeRootCountCandidate; const FleetRaceSource* source; const bool *mixed,*wrapU; };']
    for profile in profiles:
        ident = profile['ps2_family']
        lines.append('inline constexpr FleetRaceSource kRaceFleetSource' + ident + '[]={')
        for src in profile['pc_sources']:
            lines.append(' {"%s","%s","%s","%s",%du,%du,%s},' %
                         (src['geometry_sha256'], src['ordered_position_sha256'], src['uv_topology_sha256'],
                          src['native_uv_winding_sha256'], src['vertices'], src['faces'],
                          'true' if src['unique_family_in_paired_car_corpus'] else 'false'))
        lines.append('};')
        for field, key in [('Mixed', 'mixed_reflection'), ('WrapU', 'primary_u_wrap')]:
            lines.append('inline constexpr bool kRaceFleet' + field + ident + '[]={' +
                         ','.join('true' if m[key] else 'false' for m in profile['mesh_secondary_kinds']) + '};')
    lines.append('inline constexpr FleetRaceProfile kRaceFleetProfiles[]={')
    for p in profiles:
        ident = p['ps2_family']
        lines.append(' {"%s","%s","%s","%s",%du,%du,%du,%du,%du,%du,%du,kRaceFleetSource%s,kRaceFleetMixed%s,kRaceFleetWrapU%s},' %
                     (p['family'], ident, p['filename'], p['sha256'], p['bytes'], p['vertices'], p['indices'],
                      p['textures'], p['ps2_meshes'], len(p['pc_sources']), p['native_root_count_candidate'], ident, ident, ident))
    lines += ['};', '}']
    (HERE / 'race_fleet_registry.hpp').write_text('\n'.join(lines) + '\n')
    print('Prepared', len(profiles), 'rejected', rejected)


if __name__ == '__main__':
    main()
