"""PC tag1400 surface grid built from a list of triangles (W1).

Rule recovered from retail Turkey3 and checked on all retail courses (`test_surface_grid.py`, `surface-grid-corpus.json`):
  * records: one per landscape triangle, 9 float32 vertex coordinates, string index, plane = normalize((b-a) x (c-a)) with d = -n.a
    (float32, see tag1400_io.triangle_plane_f32; a degenerate triangle keeps a NaN plane);
  * min / max = bounding box of all record vertices; cell size 20; dim = int((max - min) / 20) + 1 for x and z;
  * cells are stored x-major (index = ix + iz * dim_x); a cell lists, in ascending order, every record whose XZ bounding box overlaps it
    (ix = floor(float32((x - min_x) / 20)), clamped);
  * strings: the material names of the landscape meshes (PC: `$surfacetype(...) $shader(ground) ...$grnd:... Noise Pass`).
PS2 source (`ps2_records`): every triangle of a PS2 visual mesh whose material contains `$surfacetype`, with the PS2 material name minus its
`$detail(...)` tokens (the PC compiler drops them: 22,001 of 23,071 triangles shared by PS2 and PC Turkey3 have exactly that string, the rest have a
different PS2 material).
"""
from __future__ import annotations

import math
import re
import struct

import tag1400_io as io

CELL = 20.0
DETAIL = re.compile(r' ?\$detail\([^)]*\)')


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def build(records, cell=CELL):
    """records: [(9 floats, string bytes)] -> tag1400 bytes, report. Degenerate triangles are kept with a NaN plane, as retail does."""
    strings, sidx, recs, degenerate = [], {}, [], 0
    for verts, s in records:
        verts = tuple(f32(v) for v in verts)
        pl = io.triangle_plane_f32(verts[0:3], verts[3:6], verts[6:9])
        degenerate += pl[0] != pl[0]
        if s not in sidx:
            sidx[s] = len(strings)
            strings.append(s)
        recs.append((verts, sidx[s], pl))
    return grid_bytes(recs, strings, cell), {'records': len(recs), 'strings': len(strings), 'degenerate_nan_plane': degenerate}


def _cell_index(x, lo, cell):
    # float32 arithmetic: double arithmetic disagrees with retail Italy2 in 3 cells (triangles exactly on a cell border)
    return math.floor(f32(f32(x - lo) / cell))


def grid_bytes(recs, strings, cell=CELL):
    xs = [v[i] for v, _, _ in recs for i in (0, 3, 6)]
    ys = [v[i] for v, _, _ in recs for i in (1, 4, 7)]
    zs = [v[i] for v, _, _ in recs for i in (2, 5, 8)]
    vmin, vmax = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    nx, nz = int((vmax[0] - vmin[0]) / cell) + 1, int((vmax[2] - vmin[2]) / cell) + 1
    cells = [[] for _ in range(nx * nz)]
    for rid, (v, _, _) in enumerate(recs):
        x0, x1 = min(v[0], v[3], v[6]), max(v[0], v[3], v[6])
        z0, z1 = min(v[2], v[5], v[8]), max(v[2], v[5], v[8])
        i0, i1 = _cell_index(x0, vmin[0], cell), _cell_index(x1, vmin[0], cell)
        j0, j1 = _cell_index(z0, vmin[2], cell), _cell_index(z1, vmin[2], cell)
        for j in range(max(0, j0), min(nz - 1, j1) + 1):
            for i in range(max(0, i0), min(nx - 1, i1) + 1):
                cells[i + j * nx].append(rid)
    return io.serialize(cell, (nx, nz), vmin, vmax, cells, strings, recs)


def rebuild_from_parsed(t):
    """Re-derive bounds, dimensions and cells from the records of a parsed retail block (rule check)."""
    recs = [(r.float_prefix, r.string_ref_index, r.float_suffix) for r in t.records]
    return grid_bytes(recs, [s.raw_bytes for s in t.strings], t.scalar)


def ps2_records(scene, source_triangles):
    """[(9 floats, string bytes)] from the PS2 scene: triangles of meshes whose material carries $surfacetype."""
    out = []
    for m in scene.meshes:
        if '$surfacetype' not in m['material']:
            continue
        name = DETAIL.sub('', m['material']).encode('ascii')
        for pos, _, _ in source_triangles(scene, m):
            out.append(((*pos[0], *pos[1], *pos[2]), name))
    return out


def surface_type(s):
    m = re.search(rb'\$surfacetype\((\w+)\)', s)
    return m.group(1).decode() if m else None
