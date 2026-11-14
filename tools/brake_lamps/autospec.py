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


def converter_sprite_lamps(raw: bytes) -> bool:
    """True when the brake group is a 4x4 Evo converter's light sprite (ON textured ``*-stop-lit-tga``), whose
    real lamps are painted in the body texture."""
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    m = parse_dx_bytes(raw); cases, _ = logical_cases(m)
    return any(cases.get(d.draw_index) == (1, 2) and d.texture_tuple[0].endswith('-stop-lit-tga') for d in m.physical_draws)


def auto(raw: bytes, family: str, *, existing_rows=(), ps2_sources=None, read_texture=None) -> dict:
    """Default description: painted lenses for converter sprites or cars without a brake group, else from_glass."""
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    m = parse_dx_bytes(raw); cases, _ = logical_cases(m)
    if converter_sprite_lamps(raw) or not any(c == (1, 1) for c in cases.values()):
        return painted_spec(raw, family, read_texture=read_texture)
    return default_spec(raw, family, existing_rows=existing_rows, ps2_sources=ps2_sources)


def painted_spec(raw: bytes, family: str, *, pad=0.03, depth=0.05, read_texture=None) -> dict:
    """Painted-lens description for a converted car whose lamps are painted in the body texture.

    With converter light sprites in a blight group (4x4 Evo pilots), every sprite component marks one lamp: the
    candidate faces are opaque body faces overlapping its footprint (+``pad``), and ``bounds`` limit the painted
    patch to that footprint. Without sprites, the rear-facing body faces of the outer thirds (and a centre high
    stop lamp band) are candidates; the colour mask decides, so check the result in the editor.
    """
    import hashlib
    import numpy as np
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.topology_writer import source_geometry
    from master_rallye.preview_scene import logical_cases
    from master_rallye.addon_sdk.native_effect_reference import _components
    m = parse_dx_bytes(raw); geometry = source_geometry(m); cases, _ = logical_cases(m)
    body = [d for d in m.physical_draws if cases.get(d.draw_index) is None and not d.flags_0x20[0]]
    ids = {d.draw_index: face_ids([v.position for v in geometry[d.draw_index].vertices], geometry[d.draw_index].triangles) for d in body}
    sprites = [d for d in m.physical_draws if cases.get(d.draw_index) == (1, 1)]
    boxes = []
    for d in sprites:
        for part in _components(geometry[d.draw_index]):
            P = np.array([v.position for v in part.vertices])
            boxes.append((P.min(0), P.max(0)))
    if not boxes:
        allp = np.vstack([[v.position for v in geometry[d.draw_index].vertices] for d in body])
        lo, hi = allp.min(0), allp.max(0)
        w, length = hi[0] - lo[0], hi[2] - lo[2]
        rear = (lo[2] - .01, lo[2] + .12 * length)
        boxes = [(np.array([lo[0], lo[1], rear[0]]), np.array([lo[0] + w / 3, hi[1], rear[1]])),
                 (np.array([hi[0] - w / 3, lo[1], rear[0]]), np.array([hi[0], hi[1], rear[1]]))]
    lamps = []
    for lo, hi in boxes:
        blo, bhi = lo - pad, hi + [pad, pad, depth]
        faces = []
        for d in body:
            g = geometry[d.draw_index]
            for t, tri in enumerate(g.triangles):
                c = np.array([g.vertices[i].position for i in tri])
                if np.all(c.max(0) >= blo) and np.all(c.min(0) <= bhi):
                    faces.append(ids[d.draw_index][t])
        if not faces:
            continue
        x = (lo[0] + hi[0]) / 2
        side = 'centre' if lo[0] < 0 < hi[0] else 'left' if x < 0 else 'right'
        name = side if side not in {l['id'] for l in lamps} else f'{side}{len(lamps)}'
        lamps.append({'id': name, 'lens': {'draw': 'any', 'faces': faces},
                      'source': {'kind': 'painted', 'bounds': [[float(v) for v in blo], [float(v) for v in bhi]]},
                      'fit': {'mode': 'project', 'offset_mm': 1.5},
                      'notes': 'converter light sprite footprint' if sprites else 'rear outer third (no sprite): check in the editor'})
    if not lamps:
        raise ValueError(f'{family}: no painted lamp candidates')
    spec = {'schema': 'mr-brake-lamps/1', 'family': family, 'source_car_sha256': hashlib.sha256(raw).hexdigest(), 'lamps': lamps}
    if read_texture is not None:
        # A sprite with no visible painted texels under it (e.g. a high stop lamp the converter drew only as a
        # light sprite) is left out and recorded, instead of failing the whole car.
        from .compile import painted_lamp_problems
        problems = painted_lamp_problems(raw, spec, read_texture)
        if problems:
            spec['lamps'] = [l for l in lamps if l['id'] not in problems]
            spec['notes'] = '; '.join(f'{k} left out: {v}' for k, v in problems.items())
            if not spec['lamps']:
                raise ValueError(f'{family}: no painted lamp has visible lamp texels')
    return spec


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
