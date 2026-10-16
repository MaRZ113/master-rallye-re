"""Pinned index-only PS2 root19 -> native PC10 correspondence; no asset writes."""
from pathlib import Path
import hashlib
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path.insert(0, str(ROOT.parent / 'master-rallye-re-course/src'))
from master_rallye.dx import parse_dx

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    source = ROOT.parent / 'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/car.dx'
    asset = PORT / '.assets/vehicles/XTRAIL-CAR.ps2model'
    assert sha(source.read_bytes()) == 'e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f'
    raw = asset.read_bytes()
    assert sha(raw) == 'a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac'
    pc = parse_dx(source)
    draw = pc.physical_draws[10]
    assert draw.record_path == '10' and draw.local_vertex_max + 1 == 22 and draw.index_count == 54
    original = pc.vertices.positions[draw.vertex_base:draw.vertex_base + 22]
    uv = b''.join(struct.pack('<2f', *pc.uv_sets[0].values[draw.vertex_base + i]) for i in range(22))
    native_ids = [i - draw.vertex_base for i in pc.draw_global_indices(draw)]
    for face in range(0, len(native_ids), 3):
        native_ids[face], native_ids[face + 1] = native_ids[face + 1], native_ids[face]
    ib = struct.pack('<%dI' % len(native_ids), *native_ids)
    h = struct.unpack_from('<8s6I32s', raw)
    offset = 64 + h[2]
    meshes = [struct.unpack_from('<7I', raw, offset + i * 28) for i in range(h[3])]
    offset += h[3] * 28
    positions = [struct.unpack_from('<3f', raw, offset + i * 36) for i in range(h[4])]
    offset += h[4] * 36
    ids = struct.unpack_from('<%dI' % h[5], raw, offset)
    mesh = meshes[19]
    assert mesh[1] == 20 and mesh[6] == 54
    referenced = sorted(set(ids[mesh[5]:mesh[5] + mesh[6]]))
    mapping, candidates, unmapped = [], [], []
    for vertex in referenced:
        accepted = [i for i, xyz in enumerate(original) if max(abs(positions[vertex][j] - xyz[j]) for j in range(3)) <= 0.00001]
        if not accepted:
            unmapped.append(vertex)
        mapping.append((vertex, len(candidates), len(accepted)))
        candidates.extend(accepted)
    report = dict(schema=1, pc_record=10, ps2_root=19, mode=20, vertices=22, triangles=18,
                  original_geometry_sha256='fad797c65838c39d359767a9ef06d0d5579d847fa2b23a9ee8febe8c171b361c',
                  ordered_xyz_sha256=sha(b''.join(struct.pack('<3f', *v) for v in original)),
                  ordered_uv_sha256=sha(uv), normalized_index_sha256=sha(ib), ordered_uv_winding_sha256=sha(uv + ib),
                  source_pc_sha256=sha(source.read_bytes()), source_ps2_sha256=sha(raw), tolerance=0.00001,
                  referenced_private_vertices=len(referenced), unmapped=unmapped,
                  maximum_candidate_multiplicity=max(row[2] for row in mapping),
                  mappings=[dict(vertex=v, candidates=candidates[f:f+c]) for v,f,c in mapping])
    lines = ['#pragma once', '#include <cstdint>', '// INDEX-ONLY DRAFT; NO ORIGINAL VERTEX OR UV BYTES.',
             'namespace gfx2::ps2port::headlight_damage_draft {',
             'struct Mapping { uint32_t vertex,first,count; };',
             'inline constexpr uint16_t candidates[]={' + ','.join(str(x)+'u' for x in candidates) + '};',
             'inline constexpr Mapping mapping[]={' + ','.join('{%du,%du,%du}' % x for x in mapping) + '};']
    for key in ['ordered_xyz_sha256', 'ordered_uv_winding_sha256', 'original_geometry_sha256']:
        lines.append('inline constexpr const char* ' + key + '="' + report[key] + '";')
    lines.append('}')
    (HERE / 'headlight-mapping-draft.hpp').write_text('\n'.join(lines) + '\n')
    (HERE / 'headlight-mapping.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'mappings'}, indent=2))

if __name__ == '__main__':
    main()
