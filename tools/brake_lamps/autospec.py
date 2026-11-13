"""Default ``brake_lamps.json`` for a car: one lamp per OFF lens cluster, from_glass + project fit.

Clusters are the connected lens patches of the blight OFF case grouped by side (X sign of the patch centre; a
patch spanning X=0 is a centre lamp). For a model with several OFF draws carrying registry layer-2 rows
(body-scoped sets, ForesterSTI), each draw's lamps take that row's body; a ``PS2`` set keeps the original PS2
meshes when ``ps2_sources`` names them (asset, core, glow), otherwise it is fitted from its glass.
"""
from __future__ import annotations

import numpy as np

from .carmodel import face_ids


def _patches(g):
    """Connected triangle groups (shared positions) of a draw."""
    parent = list(range(len(g.triangles)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    owner = {}
    for i, t in enumerate(g.triangles):
        for v in t:
            p = tuple(round(x, 6) for x in g.vertices[v].position)
            if p in owner:
                parent[find(i)] = find(owner[p])
            else:
                owner[p] = i
    groups = {}
    for i in range(len(g.triangles)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def default_spec(raw: bytes, family: str, *, existing_rows=(), ps2_sources=None) -> dict:
    import hashlib
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.topology_writer import source_geometry
    from master_rallye.preview_scene import logical_cases
    from .compile import draw_identity
    m = parse_dx_bytes(raw); geometry = source_geometry(m); cases, _ = logical_cases(m)
    offs = [d for d in m.physical_draws if cases.get(d.draw_index) == (1, 1)]
    if not offs:
        raise ValueError(f'{family}: no blight OFF lens; author painted-on lens faces explicitly')
    policy = {}
    for row in existing_rows:
        f = row.split()
        if len(f) == 7 and f[0] == family and f[1] == '2':
            policy[(f[2], f[3], f[4], f[5])] = {'PC_BODY_ONLY': 'PC', 'PS2_BODY_ONLY': 'PS2'}.get(f[6], 'ANY')
    lamps = []
    for d in offs:
        body = policy.get((str(d.local_vertex_max + 1), str(d.triangle_count), *draw_identity(m, d)), 'ANY')
        g = geometry[d.draw_index]
        ids = face_ids([v.position for v in g.vertices], g.triangles)
        if body == 'PS2' and ps2_sources:
            lamps.append({'id': 'ps2', 'body': 'PS2', 'lens': {'draw': 'blight', 'faces': ids},
                          'source': {'kind': 'ps2', **ps2_sources}, 'fit': {'mode': 'none'},
                          'notes': 'original PS2 ON/glow meshes on the PS2 body, positions unchanged'})
            continue
        sides = {}
        for patch in _patches(g):
            xs = [g.vertices[v].position[0] for t in patch for v in g.triangles[t]]
            side = 'centre' if min(xs) < 0 < max(xs) else 'left' if max(xs) <= 0 else 'right'
            sides.setdefault(side, []).extend(patch)
        for side, tris in sorted(sides.items()):
            name = side if body == 'ANY' else f'{body.lower()}_{side}'
            lamps.append({'id': name, 'body': body, 'lens': {'draw': 'blight', 'faces': [ids[t] for t in sorted(tris)]},
                          'source': {'kind': 'from_glass'}, 'fit': {'mode': 'project', 'offset_mm': 1.5}})
    return {'schema': 'mr-brake-lamps/1', 'family': family, 'source_car_sha256': hashlib.sha256(raw).hexdigest(), 'lamps': lamps}
