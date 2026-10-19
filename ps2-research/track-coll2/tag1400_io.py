"""Writer for the PC course tag1400 block (surface grid: cells of triangle ids, material strings, triangle records) and the suffix split.

Wire layout (parser `master_rallye.course_tag1400`, loader 0x005541D0):
  u32 1400, f32 cell_size, u32 dim_x, u32 dim_z, 3f min, 3f max,
  dim_x * dim_z cells: u32 count, count x u32 record id
  u32 string count; per string: u32 length, bytes
  u32 record count; per record: 9 f32 (triangle vertices a, b, c), u32 string index, 4 f32 plane (n, d; n = normalize((b-a) x (c-a)))
The meaning of the fields is read from the retail data (see REPORT.md); the engine side that consumes them is not reversed.
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'src'))
from master_rallye.course_tag100 import parse_course_tag100_bytes  # noqa: E402
from master_rallye.course_tag1400 import parse_course_tag1400_bytes  # noqa: E402


def split_suffix(tag100_raw):
    """tag100-starting suffix -> (tree bytes, tag1339 bytes, tag1400 bytes, rest bytes). The tag1339 record sits between the tree and tag1400."""
    p = parse_course_tag100_bytes(tag100_raw, 'suffix', allow_trailing=True)
    tree, tail = tag100_raw[:p.consumed_size], tag100_raw[p.consumed_size:]
    if struct.unpack_from('<I', tail, 0)[0] != 1339:
        raise ValueError('expected tag1339 after the tag100 tree')
    off = 44
    if struct.unpack_from('<I', tail, off)[0] != 1400:
        raise ValueError('expected tag1400 after the 44-byte tag1339 record')
    t = parse_course_tag1400_bytes(tail[off:], 'tag1400', allow_trailing=True)
    return tree, tail[:off], tail[off:off + t.consumed_size], tail[off + t.consumed_size:]


def serialize(cell_size, dims, vmin, vmax, cells, strings, records):
    """cells: list of lists of record ids (x-major as stored); strings: list of bytes; records: [(9 floats, string index, 4 floats)]."""
    out = bytearray(struct.pack('<IfII3f3f', 1400, cell_size, dims[0], dims[1], *vmin, *vmax))
    if len(cells) != dims[0] * dims[1]:
        raise ValueError('cell count does not match the dimensions')
    for c in cells:
        out += struct.pack('<I', len(c)) + struct.pack('<%dI' % len(c), *c)
    out += struct.pack('<I', len(strings))
    for s in strings:
        out += struct.pack('<I', len(s)) + s
    out += struct.pack('<I', len(records))
    for verts, si, plane in records:
        out += struct.pack('<9fI4f', *verts, si, *plane)
    return bytes(out)


def from_parsed(t):
    return serialize(t.scalar, (t.dimension_0, t.dimension_1), t.vector_a, t.vector_b, [list(c.entries) for c in t.cells],
                     [s.raw_bytes for s in t.strings], [(r.float_prefix, r.string_ref_index, r.float_suffix) for r in t.records])


def triangle_plane(a, b, c):
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
    ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
    if ln == 0:
        return None
    n = (n[0] / ln, n[1] / ln, n[2] / ln)
    return (*n, -(n[0] * a[0] + n[1] * a[1] + n[2] * a[2]))


def _f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def triangle_plane_f32(a, b, c):
    """Record plane in float32 steps (normal scaled by 1/length, d from vertex a). Matches retail Turkey3 bit for bit on 74 percent of the
    records and within float32 rounding (|dd| <= 0.01 at |d| ~ 3000) on the rest; the compiler probably used x87 intermediates.
    A degenerate triangle gets a NaN plane, as in retail."""
    f = _f32
    u = [f(b[i] - a[i]) for i in range(3)]
    w = [f(c[i] - a[i]) for i in range(3)]
    n = [f(f(u[1] * w[2]) - f(u[2] * w[1])), f(f(u[2] * w[0]) - f(u[0] * w[2])), f(f(u[0] * w[1]) - f(u[1] * w[0]))]
    ln = f(math.sqrt(f(f(f(n[0] * n[0]) + f(n[1] * n[1])) + f(n[2] * n[2]))))
    if ln == 0:
        return (math.nan,) * 4
    inv = f(1 / ln)
    n = [f(x * inv) for x in n]
    d = f(-f(f(f(n[0] * a[0]) + f(n[1] * a[1])) + f(n[2] * a[2])))
    return (*n, d)
