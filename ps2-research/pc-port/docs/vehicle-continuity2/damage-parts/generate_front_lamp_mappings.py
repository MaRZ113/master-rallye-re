"""Index-only front lamp damage mappings; original source hashes remain pinned."""
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
    raw = (PORT / '.assets/vehicles/XTRAIL-CAR.ps2model').read_bytes()
    assert sha(source.read_bytes()) == 'e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f'
    assert sha(raw) == 'a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac'
    pc = parse_dx(source)
    h = struct.unpack_from('<8s6I32s', raw)
    off = 64 + h[2]
    meshes = [struct.unpack_from('<7I', raw, off + i * 28) for i in range(h[3])]
    off += h[3] * 28
    positions = [struct.unpack_from('<3f', raw, off + i * 36) for i in range(h[4])]
    off += h[4] * 36
    ids = struct.unpack_from('<%dI' % h[5], raw, off)
    reports = []
    for root, record, expected_hash in [(5, 21, 'cb24d664e8af1db40cc4b161c7875e34a2042e709a5783384179b37f0ce5fe63'),
                                         (11, 22, '7e42aed180591ce5a99972f8766f1d999d59da87c8212183e528f7fd7fd5f838')]:
        draw = pc.physical_draws[record]
        n = draw.local_vertex_max + 1
        original = pc.vertices.positions[draw.vertex_base:draw.vertex_base + n]
        uv = b''.join(struct.pack('<2f', *pc.uv_sets[0].values[draw.vertex_base+i]) for i in range(n))
        native_ids = [i-draw.vertex_base for i in pc.draw_global_indices(draw)]
        for face in range(0, len(native_ids), 3):
            native_ids[face], native_ids[face+1] = native_ids[face+1], native_ids[face]
        ib = struct.pack('<%dI' % len(native_ids), *native_ids)
        mesh = meshes[root]
        assert mesh[1] == 3 and mesh[6] == draw.index_count
        referenced = sorted(set(ids[mesh[5]:mesh[5]+mesh[6]]))
        mapping, candidates, unmapped = [], [], []
        for vertex in referenced:
            accepted = [i for i, xyz in enumerate(original) if max(abs(positions[vertex][j]-xyz[j]) for j in range(3)) <= 0.00001]
            if not accepted:
                unmapped.append(vertex)
            mapping.append((vertex, len(candidates), len(accepted)))
            candidates.extend(accepted)
        report = dict(ps2_root=root, pc_record=record, mode=3, vertices=n, triangles=draw.index_count//3,
                      original_geometry_sha256=expected_hash,
                      ordered_xyz_sha256=sha(b''.join(struct.pack('<3f', *v) for v in original)),
                      ordered_uv_winding_sha256=sha(uv+ib), referenced_private_vertices=len(referenced),
                      tolerance=0.00001, unmapped=unmapped, maximum_candidate_multiplicity=max(m[2] for m in mapping),
                      mappings=[dict(vertex=v, candidates=candidates[f:f+c]) for v,f,c in mapping])
        lines=['#pragma once','#include <cstdint>','// INDEX-ONLY SOURCE DRAFT; NO ORIGINAL VERTEX OR UV BYTES.',
               'namespace gfx2::ps2port::front_lamp_%d_damage_draft {' % root,
               'struct Mapping { uint32_t vertex,first,count; };',
               'inline constexpr uint16_t candidates[]={' + ','.join(str(x)+'u' for x in candidates) + '};',
               'inline constexpr Mapping mapping[]={' + ','.join('{%du,%du,%du}' % x for x in mapping) + '};']
        for key in ['ordered_xyz_sha256','ordered_uv_winding_sha256','original_geometry_sha256']:
            lines.append('inline constexpr const char* '+key+'="'+report[key]+'";')
        lines.append('}')
        (HERE / ('front-lamp-%d-mapping-draft.hpp' % root)).write_text('\n'.join(lines)+'\n')
        reports.append(report)
    manifest=dict(schema=1,source_pc_sha256=sha(source.read_bytes()),source_ps2_sha256=sha(raw),profiles=reports)
    (HERE / 'front-lamp-mappings.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='mappings'} for r in reports],indent=2))

if __name__ == '__main__':
    main()
