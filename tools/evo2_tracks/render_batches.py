"""Retail-sized DX draw records for Course Studio builds.

Course Studio splits a material's triangles into draw records only at the 16-bit index limit (65,536 local vertices).
Retail courses never come close: France1 / Italy2 have ~1,000 draw records of at most ~2,000 vertices and ~4,700
indices each. The first Evo 2 builds produced records of up to 39,536 vertices / 85,752 indices; in the game those
records rendered scrambled (object parts and checkpoint banners scattered across the map, wrong texture regions on
the terrain; host-evo-tracks-01, Pikes Peak) while the same project rendered correctly in Blender. Records here stay
within the Retail envelope.

install() replaces ``_RenderBank.add_record`` of the Course Studio DX builder for this process (the Course Studio tree
is used read-only; nothing in it is changed on disk).
"""
from __future__ import annotations

import master_rallye.studio.dx_build as dx_build

MAX_VERTICES = 2000            # local vertices per draw record (Retail max observed 1,982)
MAX_INDICES = 4800             # indices per draw record (Retail max observed 4,710)


def _add_record(self, material, fields, slots, corners):
    """Same record layout as the Course Studio builder, with Retail-sized limits."""
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


def install():
    dx_build._RenderBank.add_record = _add_record
