"""Read-only inspection of the existing PS2MDL02 private render interchange.

This is not a new PSM decoder or permission to replace pinned Proxy resources.
"""
import json
import math
import struct

from .vehicle_setup import digest, decode_json, MAX_RESOURCE


def transfer_rgb_rows(base, source, width, height, *, flip_rows):
    """Explicit derived atlas operation; never copies or reinterprets alpha."""
    if type(width) is not int or type(height) is not int or not 0<width<=1024 or not 0<height<=1024 or type(flip_rows) is not bool:
        raise ValueError('Invalid bounded atlas transfer')
    if len(base)!=width*height*4 or len(source)!=len(base):
        raise ValueError('Atlas transfer size mismatch')
    result=bytearray(base)
    for y in range(height):
        row=(height-y-1 if flip_rows else y)*width*4
        for x in range(width):
            at=(y*width+x)*4;sample=row+x*4
            result[at:at+3]=source[sample:sample+3]
    return bytes(result)


def ps2_model(raw):
    if not 64 <= len(raw) <= MAX_RESOURCE or raw[:8] != b'PS2MDL02':
        raise ValueError('Unsupported PS2 render interchange')
    version, metadata_size, meshes, vertices, indices, textures = struct.unpack_from('<6I', raw, 8)
    if version != 2 or not 0 < meshes <= 256 or not 0 < vertices <= 100000 or not 0 < indices <= 1000000 or not 0 < textures <= 128:
        raise ValueError('PS2 interchange budget/version')
    at = 64 + metadata_size
    end = at + meshes * 28 + vertices * 36 + indices * 4
    if at > len(raw) or end > len(raw):
        raise ValueError('Truncated PS2 interchange geometry')
    metadata = decode_json(raw[64:at])
    draws = []
    for i in range(meshes):
        node, mode, t0, t1, t2, first, count = struct.unpack_from('<7I', raw, at + i * 28)
        if any(t != 0xffffffff and t >= textures for t in (t0, t1, t2)) or t0 == 0xffffffff or first > indices or count > indices - first or count % 3 or count == 0:
            raise ValueError('Invalid PS2 draw texture/index ownership')
        draws.append({'node': node, 'mode': mode, 'textures': [t0, t1, t2], 'first': first, 'count': count})
    vertex_at = at + meshes * 28
    for row in struct.iter_unpack('<6fI2f', raw[vertex_at:vertex_at + vertices * 36]):
        if any(not math.isfinite(v) for v in (*row[:6], *row[7:])):
            raise ValueError('Nonfinite PS2 vertex')
    index_at = vertex_at + vertices * 36
    if any(i[0] >= vertices for i in struct.iter_unpack('<I', raw[index_at:end])):
        raise ValueError('Invalid PS2 vertex reference')
    geometry = digest(raw[at:end])
    at = end
    images = []
    uploads = metadata.get('texture_upload', [])
    for i in range(textures):
        if at + 12 > len(raw):
            raise ValueError('Truncated PS2 texture header')
        w, h, size = struct.unpack_from('<3I', raw, at); at += 12
        if not 0 < w <= 1024 or not 0 < h <= 1024 or size != w * h * 4 or size > len(raw) - at:
            raise ValueError('Invalid PS2 texture size')
        pixels = raw[at:at + size]; at += size
        images.append({'index': i, 'width': w, 'height': h,
                       'bgra_sha256': digest(pixels), 'alpha_sha256': digest(pixels[3::4]),
                       'source': uploads[i] if i < len(uploads) else None, '_bgra': pixels})
    if at != len(raw):
        raise ValueError('Unexpected PS2 interchange trailer')
    return {'source_sha256': digest(raw), 'family': metadata.get('family'),
            'original_source_sha256': metadata.get('source_sha256'),
            'geometry_sha256': geometry, 'vertices': vertices, 'indices': indices,
            'draws': draws, 'textures': images, 'metadata': metadata}


def public_model(value):
    return {k: v if k != 'textures' else [{a: b for a, b in row.items() if not a.startswith('_')} for row in v]
            for k, v in value.items()}


def compare_native_atlas(ps2, native_textures):
    """Same names/dimensions are leads, not a proof of UV correspondence."""
    from ..dxt import parse_dxt_bytes
    rows = []
    for image in ps2['textures']:
        source = image['source'] or {}
        name = source.get('path', '').replace('\\', '/').split('/')[-1].lower()
        if name.endswith('.gxi'):
            name = name[:-4] + '.dxt'
        raw = native_textures.get(name)
        row = {'ps2_texture_index': image['index'], 'native_name': name,
               'status': 'MISSING_INPUT'}
        if raw is not None:
            decoded = parse_dxt_bytes(raw)
            equal = (decoded.width, decoded.height) == (image['width'], image['height'])
            row.update(native_sha256=digest(raw), dimensions_equal=equal,
                       pixels_equal=decoded.bgra == image['_bgra'],
                       alpha_equal=decoded.bgra[3::4] == image['_bgra'][3::4],
                       status='IDENTICAL_PIXELS' if decoded.bgra == image['_bgra'] and equal else 'UV_CORRESPONDENCE_NOT_QUALIFIED')
        rows.append(row)
    return rows
