"""ForesterSTI brake ON layers: original PS2 set for the PS2 body, transferred set for the PC body.

The PC (Demo) body is a rescaled PS2 body, so one native lamp set cannot sit on
both. FORESTER/CAR.PSM supplies the ON core (root.15.0.0), glow (root.15.0.1) and
OFF lamp (root.15.1.0). The PS2 set keeps their exact positions; its OFF lamp replaces
the PC OFF lamp in front of a PS2 body, which would otherwise hide the PS2 ON core. The PC set moves the same vertices onto
the PC tail lamp: the PS2 OFF lamp root.15.1.0 and the PC OFF lamp of the blight
group are the same 16-vertex mesh with identical UVs, so every ON vertex (which
lies on an OFF vertex) maps one-to-one; each glow halo vertex keeps its PS2
offset from the inner vertex it borders, scaled by the PS2->PC body scale fitted
on those 16 pairs. Topology and UVs stay PS2; vertex colours of the PS2 OFF lamp and PS2 panes
take the PC shade (round 5), ON/glow stay white like the PC records; the PC OFF lamp's UVs
equal the PS2 source UVs, so source UVs are used unflipped. The blight group becomes
OFF = [PC OFF, PS2 OFF] and ON = [PC ON, PC glow, PS2 ON, PS2 glow] (the original PS2
ON node has no OFF lamp under its opaque core). MR-ADDON-LAMPS 3 marks the sets
PS2_BODY_ONLY / PC_BODY_ONLY (layer 2 = OFF lamp); the renderer draws the set of the
body presented for that car and keeps ordinary PC lamp art on the PC set.

Operate only on an explicitly selected private candidate; body and collision
bytes are checked unchanged.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
from vehicle_lamp_authoring import parts_with_states, draw_identity
from ps2_fleet_new_families import PORT, DOCS, load

LAYERS = (('breaklightson-tga', 'root.15.0.0'), ('breaklightsonglow-tga', 'root.15.0.1'))
PS2_OFF = 'root.15.1.0'
# PS2 glass: front, +x side, -x side; .0.0 intact, .1.0 cracked (windscreenc32).
GLASS = {'front': ('root.11.0.0', 'root.11.1.0'), 'right': ('root.12.0.0', 'root.12.1.0'), 'left': ('root.13.0.0', 'root.13.1.0')}
GLASS_LABELS = ('screenfront', 'screenrear', 'screenleft', 'screenright')


def source_meshes():
    rt = load('forester_source_converter', DOCS / 'convert_runtime.py')
    blob = (PORT / '.assets/vehicles/FORESTER-CAR-SOURCE.ps2vehicle').read_bytes()
    rt.source.validate(blob)
    _, _, size, count, _, _ = rt.source.HEADER.unpack_from(blob)
    meta = json.loads(blob[rt.source.HEADER.size:rt.source.HEADER.size + size])
    source = blob[rt.source.HEADER.size + size:][:count * 52]

    def mesh(path):
        m = next(m for m in meta['meshes'] if m['path'] == path)
        ids, diag = rt.c.indices_for_mesh(source, m)
        used = sorted(set(ids))
        local = {v: i for i, v in enumerate(used)}
        rows = [{'position': struct.unpack_from('<3f', source, i * 52 + 36),
                 'normal': struct.unpack_from('<3f', source, i * 52),
                 'uv': struct.unpack_from('<2f', source, i * 52 + 20),
                 'color': rt.c.vertex(source, i)[24:28]} for i in used]
        tris = [(local[ids[k]], local[ids[k + 1]], local[ids[k + 2]]) for k in range(0, len(ids), 3)]
        return {'path': path, 'texture': m['textures'][0]['name'], 'vertices': rows, 'triangles': tris, 'strip_diagnostics': diag}
    return {path: mesh(path) for path in (PS2_OFF,) + tuple(p for _, p in LAYERS) + tuple(x for pair in GLASS.values() for x in pair)}


def oriented(mesh):
    """PS2 strips alternate winding; orient every triangle by its vertex normals like the
    native PC records (SDK display winding: (b-a)x(c-a) . n > 0)."""
    out = []
    for t in mesh['triangles']:
        a, b, c = (mesh['vertices'][i]['position'] for i in t)
        n = [sum(mesh['vertices'][i]['normal'][k] for i in t) for k in range(3)]
        u = [b[k] - a[k] for k in range(3)]; w = [c[k] - a[k] for k in range(3)]
        cross = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        d = sum(cross[k] * n[k] for k in range(3))
        out.append(t if d >= 0 else (t[1], t[0], t[2]))  # zero-area strip joints stay as authored
    return out


def blight_off(items):
    found = [i for i in items if isinstance(i, tuple) and i[0] == 'blight']
    assert len(found) == 1 and len(found[0][1]) == 1, 'expected one native OFF tail lamp draw'
    return found[0][1][0]


def transfer(meshes, pc_off):
    """Return {ps2 position: pc position} for ON/glow vertices and the fit evidence."""
    ps2_off = meshes[PS2_OFF]['vertices']
    pc = [(v.position, v.uvs[0]) for v in pc_off.vertices]
    assert len(ps2_off) == len(pc) == 16
    pairs = {}
    for v in ps2_off:
        u = v['uv']
        hits = [p for p, t in pc if abs(t[0] - u[0]) < 1e-4 and abs(t[1] - u[1]) < 1e-4 and (p[0] > 0) == (v['position'][0] > 0)]
        assert len(hits) == 1, ('PS2/PC OFF lamp UV correspondence', v['position'])
        pairs[v['position']] = hits[0]
    assert len(set(pairs.values())) == 16, 'PS2->PC OFF lamp map must be one-to-one'
    # Least-squares per-axis scale of the body (no translation): PC = s * PS2 per axis.
    scale = tuple(sum(a[k] * b[k] for a, b in pairs.items()) / sum(a[k] * a[k] for a in pairs) for k in range(3))
    residual = max(sum((a[k] * scale[k] - b[k]) ** 2 for k in range(3)) ** .5 for a, b in pairs.items())
    on = meshes[LAYERS[0][1]]['vertices']
    assert all(v['position'] in pairs for v in on), 'every PS2 ON vertex must lie on a PS2 OFF vertex'
    mapped = {}
    glow = meshes[LAYERS[1][1]]['vertices']
    for v in glow:
        p = v['position']
        if p in pairs:
            mapped[p] = pairs[p]; continue
        # Halo vertex: nearest inner (ON) vertex on the same side carries it.
        inner = min((q for q in pairs if (q[0] > 0) == (p[0] > 0) and any(w['position'] == q for w in on)),
                    key=lambda q: sum((p[k] - q[k]) ** 2 for k in range(3)))
        mapped[p] = tuple(pairs[inner][k] + scale[k] * (p[k] - inner[k]) for k in range(3))
    for v in on:
        mapped[v['position']] = pairs[v['position']]
    return mapped, {'pairs': len(pairs), 'body_scale': scale, 'affine_residual_m': residual,
                    'inner_vertices_exact': sum(1 for v in glow if v['position'] in pairs)}


def author(raw):
    from master_rallye.topology_writer import CompiledVertex, DrawGeometry
    from master_rallye.scene_dx_writer import ScenePart
    from master_rallye.addon_sdk.native_states import wrap_states
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.preview_scene import logical_cases
    from dataclasses import replace
    meshes = source_meshes()
    items = parts_with_states(raw, [])
    pc_off_part = blight_off(items); pc_off = pc_off_part.geometry
    mapped, fit = transfer(meshes, pc_off)
    sets = {'PC_BODY_ONLY': lambda p: mapped[p], 'PS2_BODY_ONLY': lambda p: p}

    def geometry(mesh, place, colour=None):
        return DrawGeometry(tuple(CompiledVertex(tuple(place(v['position'])), v['normal'], colour(v) if colour else v['color'], (tuple(v['uv']),)) for v in mesh['vertices']),
                            tuple(oriented(mesh)))
    off = meshes[PS2_OFF]; assert off['texture'].lower().endswith(chr(92) + pc_off_part.textures[0])
    # Round 5 (owner 2026-11-12): the converted PS2 source carries full-white vertex colours, the native PC
    # records carry their baked shade (OFF lamp ~0x77, panes ~0xa9/0x92), so the PS2 OFF lamp and PS2 panes looked
    # lit. The OFF lamp takes the colour of its exact PC counterpart (same UV + side); ON/glow stay white like PC.
    def pc_off_colour(v):
        hits = [w.color for w in pc_off.vertices if abs(w.uvs[0][0] - v['uv'][0]) < 1e-4 and abs(w.uvs[0][1] - v['uv'][1]) < 1e-4 and (w.position[0] > 0) == (v['position'][0] > 0)]
        assert len(hits) == 1; return hits[0]
    ps2_off_part = replace(pc_off_part, geometry=geometry(off, lambda p: p, pc_off_colour))
    lamps = []
    authored = {(pc_off_part.textures[0], tuple(sorted(v.position for v in pc_off.vertices))): ('PC_BODY_ONLY', 2),
                (pc_off_part.textures[0], tuple(sorted(v.position for v in ps2_off_part.geometry.vertices))): ('PS2_BODY_ONLY', 2)}
    evidence = [{'set': 'PS2_BODY_ONLY', 'layer': 2, 'source_path': PS2_OFF, 'vertices': len(off['vertices']), 'triangles': len(off['triangles']), 'strip_diagnostics': off['strip_diagnostics']}]
    for policy, place in sets.items():
        for layer, (name, path) in enumerate(LAYERS):
            mesh = meshes[path]
            assert mesh['texture'].lower().endswith(chr(92) + name)
            g = geometry(mesh, place)
            lamps.append(ScenePart(g, (name, 'Null', 'Null'), alpha=layer == 1, diffuse=False))
            authored[(name, tuple(sorted(v.position for v in g.vertices)))] = (policy, layer)
            evidence.append({'set': policy, 'layer': layer, 'source_path': path, 'vertices': len(g.vertices), 'triangles': len(g.triangles), 'strip_diagnostics': mesh['strip_diagnostics']})
    # Each ON core lies exactly on the OFF lamp of its own body.
    assert {v.position for v in lamps[0].geometry.vertices} == {v.position for v in pc_off.vertices}, 'PC ON core must coincide with the PC OFF lamp'
    assert {v.position for v in lamps[2].geometry.vertices} == {v.position for v in ps2_off_part.geometry.vertices}, 'PS2 ON core must coincide with the PS2 OFF lamp'
    items = [('blight', [pc_off_part, ps2_off_part], lamps) if isinstance(i, tuple) and i[0] == 'blight' else i for i in items]
    # Glass: one draw per pane state (native damage selector). PC triangles first, original PS2
    # triangles after them; the renderer submits only the half of the presented body (SPLIT:n).
    from vehicle_lamp_authoring import merge
    glass = {}; merged_items = []
    for item in items:
        if not (isinstance(item, tuple) and item[0] in GLASS_LABELS):
            merged_items.append(item); continue
        label, intact, cracked = item
        assert len(intact) == len(cracked) == 1
        xs = [v.position[0] for v in intact[0].geometry.vertices]; centre = (min(xs) + max(xs)) / 2
        zone = 'front' if abs(centre) < .3 else 'right' if centre > 0 else 'left'
        states = []
        for part, path in zip((intact[0], cracked[0]), GLASS[zone]):
            mesh = meshes[path]
            # PS2 pane vertex: shade of the nearest PC pane vertex (PS2 position in PC body space).
            pc_pts = [(w.position, w.color) for w in part.geometry.vertices]
            near = lambda v: min(pc_pts, key=lambda t: sum((v['position'][k] * fit['body_scale'][k] - t[0][k]) ** 2 for k in range(3)))[1]
            ps2 = geometry(mesh, lambda q: q, near)
            states.append(replace(part, geometry=merge([part.geometry, ps2])))
            glass[(label, path)] = {'pc_triangles': len(part.geometry.triangles), 'ps2_triangles': len(ps2.triangles), 'texture': part.textures[0], 'ps2_texture': mesh['texture'].split(chr(92))[-1],
                                    'pc': part.geometry, 'ps2_vertices': len(mesh['vertices']), 'strip_diagnostics': mesh['strip_diagnostics']}
        merged_items.append((label, [states[0]], [states[1]]))
    assert len(glass) == 6, 'expected front/left/right intact and cracked panes'
    items = merged_items
    output = wrap_states(raw, items)
    old, new = parse_dx_bytes(raw), parse_dx_bytes(output)
    oc, _ = logical_cases(old); nc, _ = logical_cases(new)
    glass_textures = {g['texture'] for g in glass.values()}
    body = lambda m, c: [(d.texture_tuple, bytes(d.flags_0x20), c.get(d.draw_index), draw_identity(m, d)) for d in m.physical_draws if not (d.texture_tuple[0].startswith('breaklights') or d.texture_tuple[0] in glass_textures or (d.texture_tuple[0] == pc_off_part.textures[0] and d.local_vertex_max + 1 == 16))]
    assert body(old, oc) == body(new, nc), 'body draws changed'
    corners = lambda m, d: [(tuple(m.vertices.positions[i]), tuple(m.uv_sets[0].values[i])) for i in m.draw_global_indices(d)]
    old_glass = [d for d in old.physical_draws if d.texture_tuple[0] in glass_textures]
    new_glass = [d for d in new.physical_draws if d.texture_tuple[0] in glass_textures]
    assert len(old_glass) == len(new_glass) == 6
    for a, b in zip(old_glass, new_glass):
        split = a.triangle_count; assert b.triangle_count > split and oc.get(a.draw_index) == nc.get(b.draw_index)
        # Native writer keeps the authored triangle order: the PC half is the untouched original pane.
        assert sorted(zip(*[iter(corners(old, a))] * 3)) == sorted(zip(*[iter(corners(new, b)[:split * 3])] * 3)), 'PC pane half changed'
    assert raw[old.collision.offset:old.collision.unparsed_offset] == output[new.collision.offset:new.collision.unparsed_offset]
    cases = nc; rows = []
    for d in new.physical_draws:
        if cases.get(d.draw_index) in ((1, 1), (1, 2)) and (d.texture_tuple[0] in dict(LAYERS) or d.texture_tuple[0] == pc_off_part.textures[0]):
            idx = new.draw_global_indices(d)
            key = (d.texture_tuple[0], tuple(sorted(tuple(new.vertices.positions[i]) for i in sorted(set(idx)))))
            hits = [v for k, v in authored.items() if k[0] == key[0] and len(k[1]) == len(key[1]) and all(abs(a - b) < 1e-5 for pa, pb in zip(k[1], key[1]) for a, b in zip(pa, pb))]
            assert len(hits) == 1, ('authored lamp draw', d.draw_index); policy, layer = hits[0]
            assert layer == 2 or int(bool(d.flags_0x20[0])) == layer
            geom, uv = draw_identity(new, d)
            rows.append(f'ForesterSTI {layer} {d.local_vertex_max + 1} {d.triangle_count} {geom} {uv} {policy}')
    assert len(rows) == 6 and len({tuple(r.split()[4:6]) for r in rows}) == 6
    for a, b in zip(old_glass, new_glass):
        geom, uv = draw_identity(new, b)
        rows.append(f'ForesterSTI 3 {b.local_vertex_max + 1} {b.triangle_count} {geom} {uv} SPLIT:{a.triangle_count}')
    assert len({tuple(r.split()[4:6]) for r in rows}) == 12
    evidence += [{'set': 'SPLIT', 'layer': 3, 'label': k[0], 'source_path': k[1], **{x: y for x, y in v.items() if x != 'pc'}} for k, v in glass.items()]
    return output, rows, {'layers': evidence, 'pc_transfer': fit}


def apply(host):
    from vehicle_presentation_fix import sha
    changes = []
    for root in (host / 'MRMods/Vehicles/active', host / 'MRMods/Vehicles/manager/base'):
        p = root / 'resources/DataGx/Vehicles/ForesterSTI/car.dx'
        if not p.exists(): continue
        original = p.read_bytes(); updated, rows, evidence = author(original); p.write_bytes(updated)
        registry = root / 'addon-brake-lamps.tsv'
        lines = registry.read_text().splitlines()
        version = lines[0]; assert version in ('MR-ADDON-LAMPS 1', 'MR-ADDON-LAMPS 2', 'MR-ADDON-LAMPS 3')
        keep = [l + (' ANY_MODEL' if version.endswith(' 1') else '') for l in lines[1:] if l.strip() and not l.startswith('ForesterSTI ')]
        registry.write_text('MR-ADDON-LAMPS 3\n' + '\n'.join(keep + rows) + '\n')
        cat = root / 'catalog.json'
        if cat.exists():
            c = json.loads(cat.read_text()); c['resources'] = [{'path': f.relative_to(root / 'resources').as_posix(), 'size': f.stat().st_size, 'sha256': sha(f.read_bytes())} for f in sorted((root / 'resources').rglob('*')) if f.is_file()]
            cat.write_text(json.dumps(c, indent=1) + '\n')
        changes.append({'root': str(root), 'before': sha(original), 'after': sha(updated), 'rows': rows, **evidence})
    return changes


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--candidate', type=Path, required=True); ap.add_argument('--sdk', type=Path, required=True)
    a = ap.parse_args(); sys.path.insert(0, str(a.sdk.resolve() / 'src'))
    result = apply(a.candidate.resolve()); print(json.dumps(result, indent=2)); (a.candidate / 'forester-lamp-authoring.json').write_text(json.dumps(result, indent=2) + '\n')
