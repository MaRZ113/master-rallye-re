"""Bounded Xtrail COMPLETE runtime buffer conversion; never grants ownership.

Reuses PS2VEH01 validation and GXI decoder. The first runtime consumer MUST use
CULL_NONE: original strip flag/backface semantics remain unproved. All source
mesh/strip metadata is retained in the embedded manifest. No fitted transforms,
alpha amplification, normal normalization or generated textures are introduced.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct
import sys

PORT = Path(__file__).resolve().parents[3]
ROOT = PORT.parents[1]
sys.path[:0] = [str(PORT / 'tools'), str(ROOT / 'ps2-research/tools')]
import prepare_vehicle_models as source
import psbtool
import reflection_runtime

MAGIC = b'PS2MDL02'
HEADER = struct.Struct('<8s6I32s')
MESH = struct.Struct('<7I')  # node_offset, mode, slot0/1/2, first_index, count
VERTEX = struct.Struct('<3f3fI2f')  # XYZ, normal, D3DCOLOR, primary UV (FVF152)
XTRAIL_SHA = '30f976c4e4e371851e8ebd45dabc1db4ea6c676f9bf99684f70a9a2932096e38'
XTRAIL_PRIVATE_SHA = 'aaa54bcf21a8820d2432e393fac411abf4a92ac3fce99fb2008233640e44b662'
NONE = 0xffffffff
DEFAULT_SHA = 'ad2960c11407794294b6d188db3660478f21ecea1a9b0fef4e69fc0a4ccef6d5'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def private_output(path):
    expected = PORT / '.assets/vehicles'
    if path.parent != expected:
        raise ValueError('Private output outside canonical asset directory')
    for at in (path, path.parent, path.parent.parent):
        if at.is_symlink() or getattr(at, 'is_junction', lambda: False)():
            raise ValueError('Linked private output')
    if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
        raise ValueError('Nonregular private output')
    return path


def vertex(raw, index):
    at = index * 52
    normal = struct.unpack_from('<3f', raw, at)
    rgba = struct.unpack_from('<I', raw, at + 16)[0]
    uv = struct.unpack_from('<2f', raw, at + 20)
    xyz = struct.unpack_from('<3f', raw, at + 36)
    if not all(math.isfinite(v) for v in xyz + normal + uv):
        raise ValueError('Non-finite original attribute')
    argb = ((rgba & 255) << 24) | (rgba >> 8)
    return VERTEX.pack(*xyz, *normal, argb, *uv)


def indices_for_mesh(raw, mesh):
    result, adc, degenerate = [], 0, 0
    for strip in mesh['strips']:
        for newest in range(strip['start'] + 2, strip['start'] + strip['count']):
            if struct.unpack_from('<I', raw, newest * 52 + 12)[0] & 1:
                adc += 1
                continue
            ids = (newest - 2, newest - 1, newest)
            points = [struct.unpack_from('<3f', raw, i * 52 + 36) for i in ids]
            if reflection_runtime.w.area_normal(points)[0] <= 1e-7:
                degenerate += 1
                continue
            # Ordered source kicks retained. No unproved flag/parity cull policy.
            result.extend(ids)
    return result, {'adc_suppressed': adc, 'diagnostic_degenerate': degenerate}


def texture(raw):
    info = psbtool.parse_gxi(raw)
    pixels = bytearray()
    for at in range(8, len(raw), 4):
        r, g, b, a = raw[at:at + 4]
        pixels.extend((b, g, r, a))
    return info, bytes(pixels)


def convert(data, default_gxi=None):
    if sha(data) != XTRAIL_PRIVATE_SHA:
        raise ValueError('Frozen private source artifact drift')
    source.validate(data)
    _, _, meta_size, count, tex_count, source_sha = source.HEADER.unpack_from(data)
    pos = source.HEADER.size
    meta = json.loads(data[pos:pos + meta_size]); pos += meta_size
    if meta['family'] != 'XTRAIL' or source_sha.hex() != XTRAIL_SHA:
        raise ValueError('Only frozen XTRAIL COMPLETE is admitted')
    if meta['extra_nodes'] or [m['path'] for m in meta['meshes']] != ['root.' + str(i) for i in range(24)]:
        raise ValueError('Unknown node transforms/hierarchy')
    if meta['unresolved_textures']:
        raise ValueError('Unresolved texture')
    raw = data[pos:pos + count * 52]; pos += count * 52
    vertices = b''.join(vertex(raw, i) for i in range(count))
    textures, texture_rows = [], []
    for i in range(tex_count):
        size = struct.unpack_from('<I', data, pos)[0]; pos += 4
        gxi = data[pos:pos + size]; pos += size
        info, pixels = texture(gxi)
        if info['sha256'] != meta['textures'][i]['sha256']:
            raise ValueError('Texture provenance mismatch')
        textures.append(struct.pack('<3I', info['width'], info['height'], len(pixels)) + pixels)
        texture_rows.append({**meta['textures'][i], 'argb_sha256': sha(pixels),
                             'alpha_min': info['alpha_min'], 'alpha_max': info['alpha_max']})
    if default_gxi is not None:
        if sha(default_gxi) != DEFAULT_SHA:
            raise ValueError('Original default texture drift')
        info, pixels = texture(default_gxi)
        textures.append(struct.pack('<3I', info['width'], info['height'], len(pixels)) + pixels)
        texture_rows.append({**info, 'path': '\\TNG\\DEFAULT.GXI', 'argb_sha256': sha(pixels),
                             'role': 'ORIGINAL_NO_PRIMARY_DEFAULT_RESIDENT_HANDLE'})
    index_data, mesh_data, mesh_rows = [], [], []
    for mesh in meta['meshes']:
        ids, diagnostics = indices_for_mesh(raw, mesh)
        slots = [NONE] * 3
        for slot in mesh['textures']:
            if slot['private_texture_index'] is None:
                raise ValueError('Missing original texture')
            slots[slot['slot']] = slot['private_texture_index']
        secondary = next((s['name'] for s in mesh['textures'] if s['slot'] == 1), '')
        contract = reflection_runtime.material_contract(mesh['material'], secondary)
        mode = contract['mode'] or 0
        if mesh['path'] == 'root.17' and default_gxi is not None:
            if mesh['material'] != 'shit' or slots != [NONE, 2, NONE]:
                raise ValueError('Original default material layout drift')
            slots = [tex_count, NONE, NONE]
            contract = {**contract, 'mode': 0, 'effective_secondary': None,
                        'effective_primary': 'ORIGINAL_DEFAULT_GXI',
                        'default_resolver': '39177c->3918fc;391b68->391bd4;37163c->2fd788',
                        'evidence_grade': 'CONFIRMED_BY_ORIGINAL_R5900_BYTES_AND_GXI'}
        mesh_data.append(MESH.pack(mesh['node_offset'], mode, *slots, len(index_data), len(ids)))
        mesh_rows.append({**mesh, 'contract': contract, 'index_start': len(index_data),
                          'index_count': len(ids), 'faces': len(ids) // 3, **diagnostics})
        index_data.extend(ids)
    if len(index_data) != 4636 * 3 or count != 6606 or tex_count != 27:
        raise ValueError('Frozen Xtrail count drift')
    manifest = {'schema_version': 2, 'source': meta, 'meshes': mesh_rows,
                'texture_upload': texture_rows, 'source_asset_sha256': sha(data),
                'vertex_layout': 'D3DFVF_XYZ_NORMAL_DIFFUSE_TEX1_36_BYTES',
                'coordinates': 'SOURCE_MODEL_LOCAL_NO_TRANSFORMS_APPLIED',
                'winding': 'ORDERED_SOURCE_TRIPLES_CULL_NONE_REQUIRED_PARITY_NOT_PROVEN',
                'alpha': 'ORIGINAL_STORED_ALPHA_NO_REMAP_PC255_VS_GS128_UNRESOLVED',
                'render_admission': ('OWNER_REQUIRED_MATERIAL_PARITY_RUNTIME_PENDING' if default_gxi is not None
                                     else 'OWNER_REQUIRED_UNKNOWN_MATERIAL_ROOT17_BLOCKS_FULL_PARITY')}
    text = json.dumps(manifest, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    binary = (HEADER.pack(MAGIC, 2, len(text), len(mesh_data), count, len(index_data), len(textures), source_sha)
              + text + b''.join(mesh_data) + vertices
              + struct.pack('<%dI' % len(index_data), *index_data) + b''.join(textures))
    report = {'source_sha256': XTRAIL_SHA, 'asset_sha256': sha(binary), 'bytes': len(binary),
              'vertices': count, 'meshes': len(mesh_data), 'faces': len(index_data) // 3,
              'textures': len(textures), 'meshes_detail': mesh_rows, 'textures_detail': texture_rows,
              'unknown_materials': [m['path'] for m in mesh_rows if m['contract']['mode'] is None],
              'alpha_remapping': False, 'transforms_applied': False}
    return binary, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=PORT / '.assets/vehicles/XTRAIL-COMPLETE.ps2vehicle')
    parser.add_argument('--ps2-root', type=Path,
                        help='Verify canonical inputs and prepare XTRAIL through established decoder first')
    args = parser.parse_args()
    if args.ps2_root is not None:
        # Use the established function rather than its CLI: preserve the full
        # existing 29-model preparation report instead of overwriting it with one.
        source.prepare(args.ps2_root, ['XTRAIL'])
    default = None
    if args.ps2_root is not None:
        import tngtool
        pack, _ = tngtool.load_pak(args.ps2_root / 'TNG.PAK')
        entries = [e for e in pack['entries'] if e['kind'] == 'file'
                   and tngtool.logical_path(e['path']).upper() == '\\TNG\\DEFAULT.GXI']
        if len(entries) != 1:
            raise ValueError('Nonunique original default texture')
        default, _ = tngtool.read_payload(entries[0], args.ps2_root / 'TNG.000')
        default_path = private_output(PORT / '.assets/vehicles/XTRAIL-default.gxi')
        if default_path.exists() and default_path.read_bytes() != default:
            raise ValueError('Conflicting private default texture')
        default_path.write_bytes(default)
    else:
        default_path = private_output(PORT / '.assets/vehicles/XTRAIL-default.gxi')
        if default_path.exists():
            default = default_path.read_bytes()
    data, report = convert(args.input.read_bytes(), default)
    out = private_output(PORT / '.assets/vehicles/XTRAIL-COMPLETE.ps2model')
    if out.exists() and out.read_bytes() != data:
        previous = out.read_bytes()
        if default is None or sha(previous) != '641406d6ff45e028bb26d38bf69ea53dd48afd3d0fe420284e8055ca5f5809cc':
            raise ValueError('Different private output already exists')
        preserved = private_output(out.with_name('XTRAIL-COMPLETE-source-only.ps2model'))
        if preserved.exists() and preserved.read_bytes() != previous:
            raise ValueError('Different preserved private output already exists')
        preserved.write_bytes(previous)
    out.write_bytes(data)
    (Path(__file__).parent / 'conversion-evidence.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, list)}))


if __name__ == '__main__':
    main()
