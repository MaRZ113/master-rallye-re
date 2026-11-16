"""Rally Championship Xtreme (PC, Warthog 2001) car formats, read-only.

Copied and adapted from research/source-formats `source-formats/rcx/` (rcx_extract.py,
qto_inspect.py, tex_decode.py; Rally.exe archive decoder at VA 0x4829C0):

* RCX v4 archive: magic c65e0bb004000000, u32 count, 0x128-byte records (name 0x100, then
  type, expanded, stored, offset, index, ...); type 6 = file (LZ when expanded != 0), 5 = directory.
* QTO v7.2 mesh: 32-byte header (ver, sub, groups, textures, vertices, indices, aux, ?), 57-byte
  groups (draw id, texture index, ?, material flags, ..., start, count, triangles), texture
  names, 64-byte vertices (pos @0, normal @28, uv @48), u16 indices.
* MSH: magic 0xB00B10AD, u32 count, 136-byte part records (name 32, parent u32, bbox 6f,
  4x4 matrix 16f row-major with translation in 12..14).
* TEX v1: magic 0x0DA7ADDE, A8R8G8B8 / X8R8G8B8 / DXT1 / DXT3 with mips.
"""
from __future__ import annotations
import math
import struct
from PIL import Image

RCX_MAGIC = bytes.fromhex('c65e0bb004000000')


def _unpack(src, expected):
    out = bytearray(); p = 0
    def literal(n):
        nonlocal p
        if p + n > len(src) or len(out) + n > expected: raise ValueError('literal outside bounds')
        out.extend(src[p:p + n]); p += n
    def back(dist, n):
        if dist > len(out) or len(out) + n > expected: raise ValueError('backreference outside bounds')
        for _ in range(n): out.append(out[-dist])
    while True:
        if p >= len(src): raise ValueError('missing terminator')
        c = src[p]; p += 1
        if c < 0x80:
            b = src[p]; p += 1; literal(c & 3); back(((c >> 5) << 8) + b + 1, ((c >> 2) & 7) + 3)
        elif c < 0xC0:
            a, b = src[p:p + 2]; p += 2; literal(a >> 6); back(((a & 63) << 8) + b + 1, (c & 63) + 4)
        elif c < 0xE0:
            a, b, d = src[p:p + 3]; p += 3; literal(c & 3); back(((c & 16) << 12) + (a << 8) + b + 1, ((c & 12) << 6) + d + 5)
        elif c < 0xFC:
            literal(((c & 31) + 1) * 4)
        else:
            literal(c & 3)
            if len(out) != expected: raise ValueError('decoded size mismatch')
            return bytes(out)


def read_rcx(data: bytes) -> dict:
    """name (lower case, without directory) -> decoded bytes."""
    if data[:8] != RCX_MAGIC: raise ValueError('not an RCX v4 archive')
    count = struct.unpack_from('<I', data, 8)[0]
    files = {}
    for i in range(1, count):
        h = 0x110 + i * 0x128
        name = data[h - 0x104:h - 4].split(b'\0', 1)[0].decode('latin1')
        typ, expanded, stored, off, idx = struct.unpack_from('<5I', data, h)
        if idx != i: raise ValueError('bad RCX index %d' % i)
        if typ != 6: continue
        raw = data[off:off + stored]
        files[name.replace('\\', '/').split('/')[-1].lower()] = _unpack(raw, expanded) if expanded else raw
    return files


def parse_qto(b: bytes) -> dict:
    ver, sub, ng, nt, nv, ni, na, _ = struct.unpack_from('<8I', b)
    if (ver, sub) != (7, 2): raise ValueError('unsupported QTO %d.%d' % (ver, sub))
    groups = []
    for i in range(ng):
        p = 32 + i * 57
        draw_id, tex, _, flags = struct.unpack_from('<4I', b, p)
        start, count, ntri = struct.unpack_from('<3I', b, p + 17)
        groups.append({'draw_id': draw_id, 'texture_index': tex if nt else None, 'flags': flags,
                       'start': start, 'end': start + count, 'triangles': ntri, 'raw_hex': b[p:p + 57].hex()})
    off = 32 + ng * 57; names = []
    for _ in range(nt):
        e = b.index(b'\0', off); names.append(b[off:e].decode('latin1')); off = e + 1
    if off + nv * 64 + ni * 2 + na * 2 != len(b): raise ValueError('unexpected QTO layout')
    verts = []
    for i in range(nv):
        at = off + i * 64
        pos = struct.unpack_from('<3f', b, at); nrm = struct.unpack_from('<3f', b, at + 28); uv = struct.unpack_from('<2f', b, at + 48)
        verts.append((pos, nrm, uv))
    idx = struct.unpack_from('<%dH' % ni, b, off + nv * 64)
    return {'groups': groups, 'textures': [n.replace('\\', '/').split('/')[-1].lower() for n in names],
            'vertices': verts, 'indices': idx}


def parse_msh(b: bytes) -> dict:
    magic, count = struct.unpack_from('<II', b)
    if magic != 0xB00B10AD or len(b) != 8 + count * 136: raise ValueError('unknown MSH')
    out = {}
    for i in range(count):
        p = 8 + i * 136
        name = b[p:p + 32].split(b'\0')[0].decode('latin1').lower()
        parent = struct.unpack_from('<I', b, p + 32)[0]
        bbox = struct.unpack_from('<6f', b, p + 36); m = struct.unpack_from('<16f', b, p + 72)
        out[name] = {'index': i, 'parent': parent, 'bbox': bbox, 'matrix': m}
    return out


def apply(m, p):
    """MSH matrix (row-major, translation in 12..14) applied to a point."""
    x, y, z = p
    return (x * m[0] + y * m[4] + z * m[8] + m[12], x * m[1] + y * m[5] + z * m[9] + m[13], x * m[2] + y * m[6] + z * m[10] + m[14])


def rotate(m, n):
    x, y, z = n
    v = (x * m[0] + y * m[4] + z * m[8], x * m[1] + y * m[5] + z * m[9], x * m[2] + y * m[6] + z * m[10])
    s = math.sqrt(sum(c * c for c in v)) or 1.
    return tuple(c / s for c in v)


FORMATS = {21: 'A8R8G8B8', 22: 'X8R8G8B8', 0x31545844: 'DXT1', 0x33545844: 'DXT3'}


def decode_tex(data: bytes) -> dict:
    magic, version, w, h, fmt, levels = struct.unpack_from('<6I', data)
    if magic != 0x0DA7ADDE or version != 1 or fmt not in FORMATS: raise ValueError('unsupported TEX')
    pos = 24
    size = w * h * 4 if fmt in (21, 22) else max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * (8 if fmt == 0x31545844 else 16)
    raw = data[pos:pos + size]
    if fmt in (21, 22):
        rgba = bytearray(Image.frombytes('RGBA', (w, h), raw, 'raw', 'BGRA').tobytes())
        if fmt == 22: rgba[3::4] = b'\xff' * (w * h)
        rgba = bytes(rgba)
    else:
        rgba = Image.frombytes('RGBA', (w, h), raw, 'bcn', (1, 'DXT1') if fmt == 0x31545844 else (2, 'DXT3')).tobytes()
    return {'width': w, 'height': h, 'format': FORMATS[fmt], 'mip_count': levels, 'rgba': rgba}
