"""Compile a brake_lamps.json into car.dx (blight OFF/ON group) and MR-ADDON-LAMPS 3 registry rows.

* Every lamp body ``ANY``: blight OFF = the existing OFF lens draws, ON = OFF draws + one core + one halo draw.
* Body-scoped (``PC``/``PS2``, ForesterSTI): ON = core + halo per set (no OFF under them, the Forester convention);
  each OFF draw gets a layer-2 row with the policy of the set whose lens it carries.
* Lens faces in a body draw of a model without state groups (painted-on lamps of imported cars): the faces are
  extracted into a new brake group by the SDK's ``author_states`` (one ``ANY`` set).

Rows of other layers (glass SPLIT, layer 3) of the family are kept when they still bind to a draw of the output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import struct
import sys
from pathlib import Path

import numpy as np

from . import build
from .build import Layer, join
from .carmodel import ON_CORE_TEXTURE, ON_GLOW_TEXTURE
from .geometry import Mesh, merge
from .spec import normalise, SpecError

TOOLS = Path(__file__).resolve().parents[1]
CORE_PARTS = (ON_CORE_TEXTURE, 'Null', 'Null')
GLOW_PARTS = (ON_GLOW_TEXTURE, 'Null', 'Null')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def draw_identity(m, d):
    """Registry identity (geometry face digest, position/UV corner digest), as tools/vehicle_lamp_authoring.py."""
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    from vehicle_lamp_authoring import draw_identity as native_identity
    return native_identity(m, d)


@dataclass
class Compiled:
    car_dx: bytes
    rows: list
    lamps: list
    textures: dict = field(default_factory=dict)
    report: dict = field(default_factory=dict)


def ps2_mesh_loader():
    """Loader for ``source.kind == 'ps2'``: (asset .ps2vehicle path, mesh path) -> Layer (oriented, source UVs)."""
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    import json
    from ps2_fleet_new_families import PORT, DOCS, load
    from forester_ps2_lamps import oriented
    rt = load('brake_lamps_ps2_converter', DOCS / 'convert_runtime.py')
    cache = {}

    def mesh(asset, path):
        p = Path(asset)
        if not p.is_absolute():
            p = PORT / p
        if p not in cache:
            blob = p.read_bytes(); rt.source.validate(blob)
            _, _, size, count, _, _ = rt.source.HEADER.unpack_from(blob)
            meta = json.loads(blob[rt.source.HEADER.size:rt.source.HEADER.size + size])
            cache[p] = (meta, blob[rt.source.HEADER.size + size:][:count * 52])
        meta, source = cache[p]
        m = next((m for m in meta['meshes'] if m['path'] == path), None)
        if m is None:
            raise SpecError(f'PS2 mesh {path} not in {p.name}')
        ids, _ = rt.c.indices_for_mesh(source, m)
        used = sorted(set(ids)); local = {v: i for i, v in enumerate(used)}
        rows = [{'position': struct.unpack_from('<3f', source, i * 52 + 36), 'normal': struct.unpack_from('<3f', source, i * 52),
                 'uv': struct.unpack_from('<2f', source, i * 52 + 20), 'color': rt.c.vertex(source, i)[24:28]} for i in used]
        tris = [(local[ids[k]], local[ids[k + 1]], local[ids[k + 2]]) for k in range(0, len(ids), 3)]
        tris = oriented({'vertices': rows, 'triangles': tris})
        return Layer(np.array([r['position'] for r in rows], float), np.array([r['uv'] for r in rows], float),
                     np.array(tris, dtype=np.int64), np.array([r['normal'] for r in rows], float), [bytes(r['color']) for r in rows])
    return mesh


def fit_spec(raw: bytes, spec: dict, *, donor_dx: bytes | None = None, ps2_loader=None):
    """Fit every lamp of ``spec`` onto ``raw``. Returns (normalised spec, fitted lamps, context)."""
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.topology_writer import source_geometry
    from master_rallye.preview_scene import logical_cases
    from .carmodel import load as load_car
    spec = normalise(spec)
    m = parse_dx_bytes(raw); geometry = source_geometry(m); cases, _ = logical_cases(m)
    car = load_car(raw, spec['family'])
    lamp_draws = {d.index for d in car.draws if d.role in ('on_core', 'on_glow')}
    # Occluders: everything opaque drawn while braking except the ON layers being re-authored.
    occluders = merge(d.mesh for d in car.draws if d.role in ('body', 'off_glass_on') and not d.alpha and d.index not in lamp_draws)
    fitted, lenses = [], {}
    for lamp in spec['lamps']:
        if lamp['mirror']:
            continue
        faces = build.resolve_faces(m, geometry, cases, lamp)
        lens = build.lens_mesh(geometry, faces)
        lenses[lamp['id']] = faces
        if lamp['source']['kind'] == 'ps2' and ps2_loader is None:
            ps2_loader = ps2_mesh_loader()
        fitted.append(build.fit_lamp(lamp, lens, occluders, donor_dx=donor_dx, ps2_loader=ps2_loader))
    by_id = {f.id: f for f in fitted}
    for lamp in spec['lamps']:
        if not lamp['mirror']:
            continue
        src = by_id[lamp['mirror']['of']]
        # Exact X-mirror of the fitted source lamp (layers and lens); no re-fit.
        mirrored = Mesh(src.lens.positions * [-1, 1, 1], src.lens.triangles[:, [0, 2, 1]])
        twin = {**lamp, 'lens': None}
        twin['source'] = {'kind': 'custom', 'core': _as_custom(build.mirror_layer(src.core)), 'glow': _as_custom(build.mirror_layer(src.glow))}
        twin['fit'] = {**lamp['fit'], 'mode': 'none'}
        f = build.fit_lamp(twin, mirrored, occluders)
        f.id = lamp['id']
        fitted.append(f)
        lenses[lamp['id']] = [('mirror', lamp['mirror']['of'])]
    return spec, fitted, {'model': m, 'geometry': geometry, 'cases': cases, 'occluders': occluders, 'lenses': lenses, 'car': car}


def _as_custom(layer: Layer) -> dict:
    return {'positions': layer.positions.tolist(), 'uvs': layer.uvs.tolist(), 'triangles': layer.triangles.tolist()}


def compile_car(raw: bytes, spec: dict, *, donor_dx: bytes | None = None, ps2_loader=None, existing_rows=(), glow_texture: bytes | None = None) -> Compiled:
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.scene_dx_writer import ScenePart
    from master_rallye.addon_sdk.native_states import wrap_states, author_states
    from master_rallye.preview_scene import logical_cases
    from vehicle_lamp_authoring import parts_with_states
    spec, fitted, ctx = fit_spec(raw, spec, donor_dx=donor_dx, ps2_loader=ps2_loader)
    m, cases = ctx['model'], ctx['cases']
    family = spec['family']
    sets = {}
    for f in fitted:
        sets.setdefault(f.body, []).append(f)
    scoped = set(sets) != {'ANY'}
    if scoped and 'ANY' in sets:
        raise SpecError('mix of ANY and body-scoped lamps in one car')
    parts, authored = [], {}
    for body in sorted(sets):
        for layer, (texture, alpha) in enumerate(((CORE_PARTS, False), (GLOW_PARTS, True))):
            mesh = join([f.core if layer == 0 else f.glow for f in sets[body]])
            part = ScenePart(mesh.geometry(), texture, alpha=alpha, diffuse=False)
            parts.append(part)
            authored[(texture[0], _key(mesh.positions))] = (body, layer)
    has_blight = any(cases.get(d.draw_index) == (1, 1) for d in m.physical_draws)
    painted = [l for l in spec['lamps'] if not l['mirror']] if not has_blight else []
    if painted:
        if scoped or any(not isinstance(l['lens']['draw'], int) for l in painted):
            raise SpecError('a model without a blight group needs lens faces of one body draw (index) and body ANY')
        draws = {d for l in painted for d, _ in ctx['lenses'][l['id']]}
        if len(draws) != 1:
            raise SpecError('painted-on lens faces must come from one body draw')
        index = draws.pop()
        ids = sorted({t for l in painted for d, tt in ctx['lenses'][l['id']] for t in tt})
        recipe = {'source_sha256': sha(raw), 'brake': {'source_draw': index, 'triangles': ids, 'lit_texture': ON_CORE_TEXTURE,
                                                      'glow_texture': ON_GLOW_TEXTURE, 'evidence': f'brake_lamps.json lens faces of draw {index}'}}
        output, _ = author_states(raw, recipe, brake_lit=parts[0], brake_glow=parts[1],
                                  brake_material={'alpha': False, 'alpha_test': False, 'environment': False, 'diffuse': False, 'secondary_texture': 'Null'})
    else:
        items = parts_with_states(raw, [])
        blight = [i for i in items if isinstance(i, tuple) and i[0] == 'blight']
        if len(blight) != 1:
            raise SpecError('model has no blight group; give lens.draw as a body draw index for painted-on lamps')
        label, off, _ = blight[0]
        on = parts if scoped else off + parts
        if len(on) > 17 or len(off) > 17:
            raise SpecError('blight case exceeds 17 draws')
        items = [(label, off, on) if isinstance(i, tuple) and i[0] == 'blight' else i for i in items]
        output = wrap_states(raw, items)
    out = parse_dx_bytes(output); oc, _ = logical_cases(out)
    assert raw[m.collision.offset:m.collision.unparsed_offset] == output[out.collision.offset:out.collision.unparsed_offset], 'collision changed'
    rows = []
    for d in out.physical_draws:
        if oc.get(d.draw_index) != (1, 2) or d.texture_tuple[0] not in (ON_CORE_TEXTURE, ON_GLOW_TEXTURE):
            continue
        idx = sorted(set(out.draw_global_indices(d)))
        key = (d.texture_tuple[0], _key(np.array([out.vertices.positions[i] for i in idx])))
        hits = [v for k, v in authored.items() if k[0] == key[0] and _same(k[1], key[1])]
        if len(hits) != 1:
            raise SpecError(f'cannot bind compiled lamp draw {d.draw_index} to its authored layer')
        body, layer = hits[0]
        if bytes(d.flags_0x20) != bytes([layer, 0, 0, 1]) or d.unknown_0x24 != 1:
            raise SpecError('compiled lamp material differs from the native ON layer material')
        g, uv = draw_identity(out, d)
        rows.append(f'{family} {layer} {d.local_vertex_max + 1} {d.triangle_count} {g} {uv} {build.POLICY[body]}')
    if len(rows) != 2 * len(sets):
        raise SpecError('expected one core and one halo row per lamp set')
    if scoped:
        # Layer 2: OFF lens draws, with the set whose lamps reference them.
        owner = {}
        for f, lamp in ((f, next(l for l in spec['lamps'] if l['id'] == f.id)) for f in fitted):
            for d, _ in ctx['lenses'][f.id]:
                if d != 'mirror':
                    owner.setdefault(d, set()).add(f.body)
        offs = [d for d in m.physical_draws if cases.get(d.draw_index) == (1, 1)]
        new_offs = [d for d in out.physical_draws if oc.get(d.draw_index) == (1, 1)]
        if len(offs) != len(new_offs):
            raise SpecError('OFF lens draw count changed')
        for old, new in zip(offs, new_offs):
            bodies = owner.get(old.draw_index)
            if not bodies or len(bodies) != 1:
                raise SpecError(f'OFF draw {old.draw_index} must carry the lens of exactly one body set')
            g, uv = draw_identity(out, new)
            rows.insert(0, f'{family} 2 {new.local_vertex_max + 1} {new.triangle_count} {g} {uv} {build.POLICY[next(iter(bodies))]}')
    # Keep the family's other rows (glass SPLIT) when they still bind to an output draw.
    identities = {(str(d.local_vertex_max + 1), str(d.triangle_count), *draw_identity(out, d)) for d in out.physical_draws}
    kept, dropped = [], []
    for row in existing_rows:
        f = row.split()
        if len(f) < 6 or f[0] != family or f[1] in ('0', '1', '2'):
            continue
        (kept if tuple(f[2:6]) in identities else dropped).append(row)
    if dropped:
        raise SpecError(f'{len(dropped)} kept registry rows no longer bind to the compiled model')
    rows += kept
    if len({tuple(r.split()[2:6]) for r in rows}) != len(rows):
        raise SpecError('ambiguous registry identities')
    textures = {}
    tints = {(tuple(l['halo']['color']), float(l['halo']['brightness'])) for l in spec['lamps']}
    if len(tints) != 1:
        raise SpecError('all lamps of a car share one PC halo tint (one per-car halo texture)')
    if glow_texture is not None:
        color, brightness = tints.pop()
        textures[ON_GLOW_TEXTURE + '.dxt'] = build.tinted_glow(glow_texture, color, brightness)
    report = {'family': family, 'source_sha256': sha(raw), 'output_sha256': sha(output), 'sets': sorted(sets), 'rows': len(rows),
              'lamps': [lamp_report(f) for f in fitted]}
    return Compiled(output, rows, fitted, textures, report)


def lamp_report(f) -> dict:
    strip = lambda e: {k: v for k, v in e.items() if not k.startswith('_')}
    return {'id': f.id, 'body': f.body, 'offset_mm': f.offset_mm, 'core_vertices': len(f.core.positions), 'core_triangles': len(f.core.triangles),
            'halo_vertices': len(f.glow.positions), 'halo_triangles': len(f.glow.triangles),
            'core': strip(f.checks['core']), 'halo': strip(f.checks['halo']), 'fit_ok': f.checks['buried'] == 0,
            'evaluated_against_body': f.checks.get('evaluated', True)}


def _key(positions):
    return tuple(sorted(tuple(round(float(x), 5) for x in p) for p in np.asarray(positions)))


def _same(a, b):
    return len(a) == len(b) and all(abs(x - y) < 2e-5 for pa, pb in zip(a, b) for x, y in zip(pa, pb))
