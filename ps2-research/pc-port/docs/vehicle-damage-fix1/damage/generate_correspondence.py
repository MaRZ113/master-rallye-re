"""Generate index-only source-backed damage correspondence, never runtime search.

No original vertex, UV, triangle-stream or texture bytes enter the header.
Runtime CPU references require verified healthy source certificates first.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path.insert(0, str(ROOT.parent / 'master-rallye-re-course/src'))
from master_rallye.dx import parse_dx

PC = ROOT.parent / 'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/car.dx'
PS2 = PORT / '.assets/vehicles/XTRAIL-CAR.ps2model'
EXPECTED_PC = 'e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f'
EXPECTED_PS2 = 'a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac'
ROOTS = [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 14, 16, 17]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bits(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def main():
    assert sha(PC.read_bytes()) == EXPECTED_PC
    asset = PS2.read_bytes()
    assert sha(asset) == EXPECTED_PS2
    pc = parse_dx(PC)
    header = struct.unpack_from('<8s6I32s', asset)
    offset = 64 + header[2]
    meshes = [struct.unpack_from('<7I', asset, offset + i * 28)
              for i in range(header[3])]
    offset += header[3] * 28
    private = [struct.unpack_from('<3f', asset, offset + i * 36)
               for i in range(header[4])]
    offset += header[4] * 36
    indices = struct.unpack_from('<' + 'I' * header[5], asset, offset)
    registry = (PORT / 'renderer/race_model_registry.hpp').read_text()
    profiles = re.findall(r'\{"([0-9a-f]{64})",(\d+)u,(\d+)u\}',
                          registry.split('constexpr bool')[0])
    output = ['#pragma once', '#include <cstdint>',
              '// INDEX CORRESPONDENCE ONLY; NO ORIGINAL VERTEX BYTES.',
              'namespace gfx2::ps2port::damage_source_draft {',
              'struct Mapping { uint32_t vertex,first,count; };']
    summaries = []
    topology = json.loads((HERE / 'source-uv-topology.json').read_text())['rows']
    for slot, ((geometry, n, faces), root) in enumerate(zip(profiles, ROOTS)):
        n, faces = int(n), int(faces)
        matching = [d for d in pc.physical_draws
                    if d.local_vertex_max + 1 == n and d.index_count // 3 == faces]
        assert len(matching) == 1
        draw = matching[0]
        original = pc.vertices.positions[draw.vertex_base:draw.vertex_base + n]
        normalized = [i - draw.vertex_base for i in pc.draw_global_indices(draw)]
        # Original PC compiler reverses each source DX triangle's first pair.
        # This exact stream conversion is independently checked against F10.
        for face in range(0, len(normalized), 3):
            normalized[face], normalized[face + 1] = normalized[face + 1], normalized[face]
        uv = b''.join(struct.pack('<2f', *pc.uv_sets[0].values[draw.vertex_base + i])
                      for i in range(n))
        winding_sha = sha(uv + struct.pack('<' + 'I' * len(normalized), *normalized))
        position_sha = sha(b''.join(struct.pack('<3f', *xyz) for xyz in original))
        mesh = meshes[root]
        mask = range(mesh[6] // 3)
        if root in (0, 7):
            match = re.search(r'kRaceWithoutDriver' + str(root) + r'\[\]=\{([^}]+)', registry)
            mask = [int(x) for x in match[1].split(',')]
        referenced = sorted({indices[mesh[5] + f * 3 + k]
                             for f in mask for k in range(3)})
        tolerance = .005 if root == 17 else .00001
        mapping, candidates, unmapped = [], [], []
        for vertex in referenced:
            accepted = [i for i, xyz in enumerate(original)
                        if max(abs(private[vertex][j] - xyz[j]) for j in range(3)) <= tolerance]
            if not accepted:
                unmapped.append(vertex)
            mapping.append((vertex, len(candidates), len(accepted)))
            candidates.extend(accepted)
        output.append('inline constexpr uint16_t candidates_' + str(slot) + '[]={' +
                      ','.join(str(v) + 'u' for v in candidates) + '};')
        output.append('inline constexpr Mapping mapping_' + str(slot) + '[]={' +
                      ','.join('{' + ','.join(str(v) + 'u' for v in row) + '}'
                               for row in mapping) + '};')
        summaries.append(dict(source_slot=slot, ps2_root=root, pc_record=draw.record_path,
                              native_vertices=n, native_triangles=faces,
                              original_geometry_sha256=geometry,
                              ordered_original_position_sha256=position_sha,
                              ordered_uv_normalized_topology_sha256=topology[slot]['ordered_uv_normalized_topology_sha256'],
                              ordered_uv_winding_topology_sha256=winding_sha,
                              referenced_private_vertices=len(referenced),
                              source_correspondence_tolerance=tolerance,
                              candidate_indices=len(candidates), unmapped_private_vertices=unmapped,
                              runtime_rule='EXACT_CURRENT_OWNER_AND_UV_ORDERED_TOPOLOGY; ALL_CANDIDATE_DELTAS_MUST_AGREE; NO_RUNTIME_POSITION_SEARCH'))
    output += ['struct Profile { unsigned root,vertices,triangles,mappings,candidates; const Mapping* mapping; const uint16_t* candidate; const char* ordered_position_sha; const char* uv_topology_sha; const char* uv_winding_sha; };',
               'inline constexpr Profile profiles[]={']
    for r in summaries:
        slot = r['source_slot']
        output.append('{' + ','.join(str(r[k]) + 'u' for k in ('ps2_root','native_vertices','native_triangles','referenced_private_vertices','candidate_indices')) +
                      ',mapping_' + str(slot) + ',candidates_' + str(slot) + ',' +
                      ','.join('"' + r[k] + '"' for k in ('ordered_original_position_sha256','ordered_uv_normalized_topology_sha256','ordered_uv_winding_topology_sha256')) + '},')
    output += ['};', '}']
    generated = HERE / 'generated'
    generated.mkdir(exist_ok=True)
    (generated / '.gitignore').write_text('*\n!.gitignore\n')
    draft = generated / 'xtrail_damage_source_draft.hpp'
    draft.write_text('\n'.join(output) + '\n')
    result = dict(schema=1, original_pc_sha256=EXPECTED_PC,
                  private_ps2_car_sha256=EXPECTED_PS2,
                  draft_sha256=sha(draft.read_bytes()), profiles=summaries,
                  status='INDEX_ONLY_CORRESPONDENCE_DRAFT; VERIFIED_HEALTHY_CPU_REFERENCE_REQUIRED; UNMAPPED_STATIC_INTERIOR_REQUIRES_EXPLICIT_POLICY')
    (HERE / 'deformation-correspondence-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Generated private draft:', draft, 'bytes=', draft.stat().st_size)
    print('Unmapped:', [(r['ps2_root'], len(r['unmapped_private_vertices'])) for r in summaries])


if __name__ == '__main__':
    main()
