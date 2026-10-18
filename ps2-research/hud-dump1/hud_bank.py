"""Image-bank readers for the PS2 PSB (F001/125, records with a 16-byte cell) and the PC DXB (F001/125, no cell).

Both banks: u32 magic 0xf001, u32 version 125, u32 mapping count, pairs (key,image), u32 image count, then per
image u32 triangle count and per triangle 6 f32 UV, 6 i32 XY, [PSB: 4 i32 cell], u32 name length, name bytes.
Returns {'mappings': [(key,image)], 'images': [[(texture, [(u,v)x3], [(x,y)x3])...]...]}.
"""
import struct


def read_bank(data, pc):
    magic, version, count = struct.unpack_from('<3I', data, 0)
    if magic != 0xf001 or version != 125:
        raise ValueError('not an F001/125 image bank')
    off = 12
    mappings = [struct.unpack_from('<2I', data, off + 8 * i) for i in range(count)]
    off += 8 * count
    (images,) = struct.unpack_from('<I', data, off); off += 4
    out = []
    for _ in range(images):
        (triangles,) = struct.unpack_from('<I', data, off); off += 4
        tris = []
        for _ in range(triangles):
            uv = struct.unpack_from('<6f', data, off); off += 24
            xy = struct.unpack_from('<6i', data, off); off += 24
            if not pc:
                off += 16
            (n,) = struct.unpack_from('<I', data, off); off += 4
            if n > 64 or off + n > len(data):
                raise ValueError('bad name length')
            name = data[off:off + n].decode('ascii'); off += n
            tris.append((name.lower(), [(uv[0], uv[1]), (uv[2], uv[3]), (uv[4], uv[5])], [(xy[0], xy[1]), (xy[2], xy[3]), (xy[4], xy[5])]))
        out.append(tris)
    if off != len(data):
        raise ValueError('trailing bytes: %d' % (len(data) - off))
    return {'mappings': mappings, 'images': out}


def image_box(tris):
    xs = [p[0] for t in tris for p in t[2]]; ys = [p[1] for t in tris for p in t[2]]
    return (min(xs), min(ys), max(xs), max(ys))
