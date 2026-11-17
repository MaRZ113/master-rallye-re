"""Retail-sized DX draw records for Course Studio builds.

Course Studio splits a material's triangles into draw records only at the 16-bit index limit (65,536 local vertices).
Retail courses never come close: France1 / Italy2 have ~1,000 draw records of at most ~2,000 vertices and ~4,700
indices each. The first Evo 2 builds produced records of up to 39,536 vertices / 85,752 indices; in the game those
records rendered scrambled (object parts and checkpoint banners scattered across the map, wrong texture regions on
the terrain; host-evo-tracks-01, Pikes Peak) while the same project rendered correctly in Blender. Records here stay
within the Retail envelope.

install() replaces ``_RenderBank.add_record`` of the Course Studio DX builder for this process (the Course Studio tree
is used read-only; nothing in it is changed on disk).

RCX-PERF1 (``install(spatial=True)``): the records are also kept spatially compact. Course Studio writes the flat
course layout without the Retail sector visibility graph, so the game submits every record every frame; the renderer
culls records outside the view (PS2Port.ini [CourseCull]), which only pays off when a record covers a small area.
Chunking a material's triangles in authoring order gave records spanning the whole stage (RcxScottish2: median 771 m).
With spatial=True the triangles of a material are sorted along a Hilbert curve of their centroid (1 m cells) before the
chunking, and a record also ends when its ground extent would pass MAX_EXTENT_M: Hilbert order alone left most
materials (< 2000 vertices) as one stage-wide record; fixed 256 m tiles multiplied the records by 5 (offline estimate
with tools/rcx_tracks/rcx_cull_eval.py: 640 m keeps culled frames at ~120-220 draws).
"""
from __future__ import annotations

import master_rallye.studio.dx_build as dx_build

MAX_VERTICES = 2000            # local vertices per draw record (Retail max observed 1,982)
MAX_INDICES = 4800             # indices per draw record (Retail max observed 4,710)
SPATIAL = False                # RCX-PERF1: Hilbert-ordered triangles before chunking
HILBERT_BITS = 16             # 65 536 one-metre cells per axis, centred on the origin
MAX_EXTENT_M = 640.0          # RCX-PERF1: largest x or z size of a spatial record


def _hilbert(x: int, y: int, order: int = HILBERT_BITS) -> int:
    """Index of cell (x, y) on the Hilbert curve of a 2**order grid."""
    d, s = 0, 1 << (order - 1)
    while s:
        rx = 1 if x & s else 0
        ry = 1 if y & s else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        s >>= 1
    return d


def _spatial(corners):
    """Triangles (3 corners each) sorted along the Hilbert curve of their (x, z) centroid."""
    half, top = 1 << (HILBERT_BITS - 1), (1 << HILBERT_BITS) - 1
    keyed = []
    for i in range(0, len(corners), 3):
        tri = corners[i:i + 3]
        cx = int((tri[0][0][0] + tri[1][0][0] + tri[2][0][0]) / 3.0) + half
        cz = int((tri[0][0][2] + tri[1][0][2] + tri[2][0][2]) / 3.0) + half
        keyed.append((_hilbert(min(max(cx, 0), top), min(max(cz, 0), top)), i))
    keyed.sort()
    out = []
    for _, i in keyed:
        out.extend(corners[i:i + 3])
    return out


def _patches(corners):
    """Hilbert-ordered triangles cut into runs whose x/z extent stays within MAX_EXTENT_M."""
    out, run, lo, hi = [], [], None, None
    for i in range(0, len(corners), 3):
        tri = corners[i:i + 3]
        xs, zs = [c[0][0] for c in tri], [c[0][2] for c in tri]
        if lo is None:
            lo, hi = [min(xs), min(zs)], [max(xs), max(zs)]
        else:
            nlo, nhi = [min(lo[0], min(xs)), min(lo[1], min(zs))], [max(hi[0], max(xs)), max(hi[1], max(zs))]
            if max(nhi[0] - nlo[0], nhi[1] - nlo[1]) > MAX_EXTENT_M and run:
                out.append(run)
                run, nlo, nhi = [], [min(xs), min(zs)], [max(xs), max(zs)]
            lo, hi = nlo, nhi
        run.extend(tri)
    if run:
        out.append(run)
    return out


def _add_record(self, material, fields, slots, corners):
    """Same record layout as the Course Studio builder, with Retail-sized limits (spatially ordered with SPATIAL)."""
    if not SPATIAL:
        _add_chunks(self, material, fields, slots, corners)
        return
    for patch in _patches(_spatial(corners)):
        _add_chunks(self, material, fields, slots, patch)


def _add_chunks(self, material, fields, slots, corners):
    start = 0
    while start < len(corners):
        lookup, local = {}, []
        base = len(self.positions)
        index_start = len(self.indices)
        pos = start
        while pos < len(corners):
            tri = corners[pos:pos + 3]
            new = sum(1 for c in tri if self._key(c) not in lookup)
            if len(lookup) + new > MAX_VERTICES or len(local) + 3 > MAX_INDICES:
                break
            for c in tri:
                key = self._key(c)
                slot = lookup.get(key)
                if slot is None:
                    slot = len(lookup)
                    lookup[key] = slot
                    p, n, col, t0, t1 = c
                    self.positions.append(p); self.normals.append(n); self.colors.append(col)
                    self.uv0.append(t0); self.uv1.append(t1)
                local.append(slot)
            pos += 3
        if pos == start:
            raise dx_build.BuildError("a single triangle exceeds the local vertex limit")
        self.indices.extend(local)
        self.records.append({"material": material, "fields": fields, "slots": slots, "vertex_base": base,
                             "local_vertex_max": len(lookup) - 1, "index_start": index_start,
                             "index_count": len(local)})
        start = pos


def install(spatial: bool = False):
    global SPATIAL
    SPATIAL = bool(spatial)
    dx_build._RenderBank.add_record = _add_record
