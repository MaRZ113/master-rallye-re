"""Read-only COMPLETE sampler-policy inventory; emits hashes/counts, no assets."""
from pathlib import Path
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]


def inspect(path):
    data = path.read_bytes()
    header = struct.unpack_from('<8s6I32s', data)
    if header[0] != b'PS2MDL02':
        return None
    meta = json.loads(data[64:64 + header[2]])
    offset = 64 + header[2]
    meshes = [struct.unpack_from('<7I', data, offset + i * 28)
              for i in range(header[3])]
    offset += header[3] * 28
    vertices = [struct.unpack_from('<3f3fI2f', data, offset + i * 36)
                for i in range(header[4])]
    offset += header[4] * 36
    indices = struct.unpack_from('<' + 'I' * header[5], data, offset)
    treads = []
    for mesh_index, mesh in enumerate(meshes):
        source = meta['meshes'][mesh_index]
        textures = source.get('textures', [])
        primary = next((t['name'] for t in textures if t['slot'] == 0), '')
        if 'tread' not in primary.lower():
            continue
        referenced = [vertices[i] for i in indices[mesh[5]:mesh[5] + mesh[6]]]
        treads.append(dict(mesh=mesh_index, source_path=source.get('path'),
                           source_primary=primary,
                           source_secondary=[t['name'] for t in textures if t['slot'] > 0],
                           mode=mesh[1], faces=mesh[6] // 3,
                           u_range=[min(v[7] for v in referenced), max(v[7] for v in referenced)],
                           v_range=[min(v[8] for v in referenced), max(v[8] for v in referenced)]))
    return dict(filename=path.name, asset_sha256=hashlib.sha256(data).hexdigest(),
                original_source_sha256=meta.get('source_asset_sha256', meta.get('source_sha256')),
                meshes=header[3],
                tread_u_wrap_mask=sum(1 << t['mesh'] for t in treads
                                      if t['u_range'][0] < 0 or t['u_range'][1] > 1),
                treads=treads)


if __name__ == '__main__':
    rows = [inspect(path) for path in sorted((PORT / '.assets/vehicles').glob('*COMPLETE*.ps2model'))]
    rows = [row for row in rows if row]
    (HERE / 'complete-tread-policy.json').write_text(json.dumps(rows, indent=2) + '\n')
    print('COMPLETE asset variants audited:', len(rows))
