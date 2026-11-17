"""Retail MR vehicle conventions that imported (RCX, Evo, TXR3) car models must follow.

Three contracts measured on the retail fleet (owner reports 2026-11-17: RCX cars snag on coarse ground, RCX and
4x4 Evo cars look too bright in Vehicle Select and under dust, RCX tail/brake lamps get no night glints):

1. Vertex prelight. Every retail car.dx / complete.dx body vertex carries a baked grey
   c = round(255 * (0.4 + 0.3 * sqrt(max(0, n_y)))) from its normal (102 facing down/sideways .. 179 facing up);
   exact for 99.8-100 % of the vertices of Megane, Forester, Pajero, Navara and X-Trail, R = G = B, alpha 255.
   Only the brake glow card (breaklightsonglow) is 255. wheel.dx is 255. The frontend lights complete.dx with
   that colour, the race multiplies textures by it and the R-SURFACE1 grime pass takes DIFFUSE x tint, so a
   converter that writes 255 everywhere is ~1.8x brighter than a stock car in the menu and under dust.

2. Hull ground clearance. The retail hull (tag101) bottom is not the body bottom: Megane body -0.246, hull
   -0.002; at rest the hull sits 0.34-0.50 m above the tyre contact (hub Y = -RideHeight, minus the wheel
   radius), which keeps it 0.09-0.20 m clear when the suspension is fully compressed (MaxBounce 0.25-0.30).
   An affine fit of the donor hull to the paint draws puts its bottom on the sills (RCX: -0.10 .. -0.17) and,
   with the RCX wheels (radius 0.25-0.34 instead of 0.39), 0.17-0.25 m above the contact: less than MaxBounce,
   so the body hull reaches the course BSP on every compression and the car catches on coarse ground.

3. Lamp lens names. The renderer finds lamp lenses by texture name (light | lamp | indicat | *bl), the brake ON
   layer by "breaklightson" and the glow card by "...glow"; lamp rigs are matched by a lens draw. Converter
   atlases are content hashes (uvs-<sha>), so imported lamps were never lenses at night.
"""
from __future__ import annotations
import math
import struct
from dataclasses import replace


def retail_shade(ny: float) -> int:
    return int(round(255 * (.4 + .3 * math.sqrt(min(1., max(0., ny))))))


def is_glow_draw(draw) -> bool:
    return 'glow' in draw.texture_tuple[0].lower()


def prelight_dx(raw: bytes, keep=is_glow_draw):
    """Retail prelight on every vertex of a car.dx / complete.dx; draws for which keep(draw) is true (the
    brake glow card) stay as authored. Positions, normals, UVs, indices and collision are unchanged."""
    from .dx import parse_dx_bytes
    m = parse_dx_bytes(raw)
    if not m.diagnostics.validated:
        raise ValueError('prelight requires a validated model')
    vd = m.vertices
    count = len(vd.positions)
    kept, lit = set(), set()
    for d in m.physical_draws:
        ids = set(m.draw_global_indices(d))
        (kept if keep(d) else lit).update(ids)
    shared = kept & lit
    out = bytearray(raw)
    changed = 0
    for i in range(count):
        if i in kept:
            continue
        o = vd.color_offset + 4 * i
        s = retail_shade(vd.normals[i][1])
        new = bytes((s, s, s, out[o + 3]))
        if out[o:o + 4] != new:
            out[o:o + 4] = new
            changed += 1
    result = bytes(out)
    after = parse_dx_bytes(result)
    if (not after.diagnostics.validated or after.vertices.positions != vd.positions or after.vertices.normals != vd.normals
            or after.uv_sets != m.uv_sets or after.physical_draws != m.physical_draws or after.local_indices != m.local_indices):
        raise ValueError('prelight changed more than vertex colours')
    if result[after.trailing.offset:] != raw[m.trailing.offset:]:
        raise ValueError('prelight changed collision bytes')
    return result, {'vertices': count, 'changed': changed, 'kept_255': len(kept), 'shared_kept': len(shared),
                    'rule': 'round(255*(0.4+0.3*sqrt(max(0,normal.y)))), glow card kept'}


# --- 2. hull ground clearance --------------------------------------------------------------------------------

def ride_heights(retail_sma, physics_family: str) -> dict:
    """Suspension/<axle>/RideHeight and MaxBounce of a retail physics family (DataGame/vehicles.xml)."""
    import re
    from .addon_sdk.project import read_sma_member
    xml = read_sma_member(retail_sma, 'DataGame/vehicles.xml').decode('latin1')
    out = {}
    for axle in ('Front', 'Rear'):
        for key in ('RideHeight', 'MaxBounce'):
            m = re.search(r'Name="Vehicles/%s/Suspension/%s/%s"[^>]*Value="([-0-9.]+)"' % (re.escape(physics_family), axle, key), xml, re.I)
            if not m:
                raise ValueError('no %s %s %s in vehicles.xml' % (physics_family, axle, key))
            out[axle + key] = float(m.group(1))
    return out


def hull_bounds(raw: bytes):
    from .dx import parse_dx_bytes
    v = parse_dx_bytes(raw).collision.convex_hull.representation_a.geometry_a.vertices
    return [[f(p[k] for p in v) for k in range(3)] for f in (min, max)]


def contact_y(suspension: dict, wheel_radius: float) -> float:
    """Tyre contact Y at the native attachment (hub Y = -RideHeight), the higher of the two axles."""
    return max(-suspension['FrontRideHeight'], -suspension['RearRideHeight']) - wheel_radius


def donor_clearance(donor_car_dx: bytes, suspension: dict, donor_wheel_radius: float) -> float:
    """Height of the retail donor hull bottom above its tyre contact at rest."""
    return hull_bounds(donor_car_dx)[0][1] - contact_y(suspension, donor_wheel_radius)


def fit_collision_floor(raw: bytes, core_draw_indices, floor_y: float):
    """fit_collision (affine donor hull onto the bounds of the selected core draws) with the hull bottom raised to
    floor_y when the core draws reach lower. Same topology, guards and footer recomputation as the SDK fit."""
    import hashlib
    from .dx import parse_dx_bytes
    from .collision_scale import scale_dx_collision
    from .collision_writer import patch_dx_collision_translation
    from .bounds import compute_bounds1339, replace_bounds1339
    model = parse_dx_bytes(raw); hull = model.collision.convex_hull
    if not model.diagnostics.validated or not hull:
        raise ValueError('collision fitting requires validated tag101')
    selected = []
    for index in core_draw_indices:
        matches = [d for d in model.physical_draws if d.draw_index == index and d.tag == 2]
        if len(matches) != 1:
            raise ValueError('collision core draw is absent or not a leaf')
        d = matches[0]
        selected.extend(model.vertices.positions[d.vertex_base + i] for i in model.local_indices[d.index_start:d.index_start + d.index_count])
    bounds = lambda pts: [[f(p[k] for p in pts) for k in range(3)] for f in (min, max)]
    before = bounds(hull.representation_a.geometry_a.vertices); target = bounds(selected)
    body_floor = target[0][1]
    target[0][1] = max(target[0][1], floor_y)
    factors = [(target[1][k] - target[0][k]) / (before[1][k] - before[0][k]) for k in range(3)]
    if any(not .5 <= s <= 1.5 for s in factors):
        raise ValueError('collision fit exceeds conservative [0.5,1.5] affine guard')
    scaled = scale_dx_collision(raw, factors, before[0]); delta = [target[0][k] - before[0][k] for k in range(3)]
    translated = patch_dx_collision_translation(scaled['data'], delta); final = parse_dx_bytes(translated.data)
    footer = compute_bounds1339(final.vertices.positions, final.collision.convex_hull, offset=final.collision.unparsed_offset)
    out = replace_bounds1339(translated.data, footer, footer_offset=final.collision.unparsed_offset)
    parsed = parse_dx_bytes(out)
    if (not parsed.diagnostics.validated or parsed.vertices != model.vertices or parsed.uv_sets != model.uv_sets
            or parsed.physical_draws != model.physical_draws or parsed.local_indices != model.local_indices):
        raise ValueError('collision fit altered render structure')
    after = bounds(parsed.collision.convex_hull.representation_a.geometry_a.vertices)
    if any(abs(after[j][k] - target[j][k]) > 2e-5 for j in range(2) for k in range(3)):
        raise ValueError('collision target bounds mismatch')
    return out, {'source_sha256': hashlib.sha256(raw).hexdigest(), 'output_sha256': hashlib.sha256(out).hexdigest(),
                 'core_draw_indices': list(core_draw_indices), 'before_aabb_m': before, 'after_aabb_m': after,
                 'body_floor_y_m': body_floor, 'hull_floor_y_m': target[0][1], 'scale': factors, 'translation_m': delta}


# --- 3. lamp lens textures -----------------------------------------------------------------------------------

def _pow2(n: int, cap: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return min(p, cap)


def lens_crop(parts: list, indices, assets, name: str, margin: int = 2) -> list:
    """Give the lamp parts parts[i] (i in indices) their own lens texture `name` (a power-of-two crop of the atlas
    texels they use, UVs remapped; texel row = v * height, as the RCX brake lens check shows). One texture per
    source atlas (`name`, then name with 1, 2 ... before -tga). Writes <assets>/<texture>.dxt; returns the new
    texture names."""
    from .dxt import parse_dxt_bytes
    from .addon_sdk.auto_features import feed
    by_texture = {}
    for i in indices:
        by_texture.setdefault(parts[i].textures[0], []).append(i)
    # parts whose atlas regions lie apart (RCX Mini: lamp glass at one corner, indicator at another) get separate
    # crops: union of UV boxes closer than 1/16 of the atlas
    groups = []
    for src, ids in sorted(by_texture.items()):
        boxes = []
        for i in ids:
            uv = [v.uvs[0] for v in parts[i].geometry.vertices]
            box = [min(u for u, _ in uv), min(v for _, v in uv), max(u for u, _ in uv), max(v for _, v in uv)]
            for b in boxes:
                if box[0] < b[1][2] + 1 / 16 and b[1][0] < box[2] + 1 / 16 and box[1] < b[1][3] + 1 / 16 and b[1][1] < box[3] + 1 / 16:
                    b[0].append(i); b[1][:] = [min(b[1][0], box[0]), min(b[1][1], box[1]), max(b[1][2], box[2]), max(b[1][3], box[3])]
                    break
            else:
                boxes.append(([i], box))
        merged = True
        while merged:                                     # transitive merge
            merged = False
            for a in range(len(boxes)):
                for c in range(a + 1, len(boxes)):
                    x, y = boxes[a][1], boxes[c][1]
                    if x[0] < y[2] + 1 / 16 and y[0] < x[2] + 1 / 16 and x[1] < y[3] + 1 / 16 and y[1] < x[3] + 1 / 16:
                        boxes[a] = (boxes[a][0] + boxes[c][0], [min(x[0], y[0]), min(x[1], y[1]), max(x[2], y[2]), max(x[3], y[3])])
                        del boxes[c]; merged = True; break
                if merged:
                    break
        groups += [(src, b[0]) for b in boxes]
    made = []
    for k, (src, ids) in enumerate(groups):
        tex = parse_dxt_bytes((assets / (src + '.dxt')).read_bytes()); W, H = tex.width, tex.height
        uv = [v.uvs[0] for i in ids for v in parts[i].geometry.vertices]
        us, vs = [u for u, _ in uv], [v for _, v in uv]
        if min(us) < -1e-3 or max(us) > 1 + 1e-3 or min(vs) < -1e-3 or max(vs) > 1 + 1e-3:
            x0, y0, w, h = 0, 0, W, H                     # tiled lens UVs: whole atlas under the lens name
        else:
            px0, px1 = max(0, math.floor(min(us) * W) - margin), min(W, math.ceil(max(us) * W) + margin)
            py0, py1 = max(0, math.floor(min(vs) * H) - margin), min(H, math.ceil(max(vs) * H) + margin)
            w, h = _pow2(px1 - px0, W), _pow2(py1 - py0, H)
            x0, y0 = min(px0, W - w), min(py0, H - h)
        rows = b''.join(tex.bgra[4 * ((y0 + y) * W + x0):4 * ((y0 + y) * W + x0 + w)] for y in range(h))
        tname = name if k == 0 else name.replace('-tga', '%d-tga' % k)
        (assets / (tname + '.dxt')).write_bytes(feed(rows, w, h))
        for i in ids:
            g = parts[i].geometry
            verts = tuple(replace(v, uvs=(((v.uvs[0][0] * W - x0) / w, (v.uvs[0][1] * H - y0) / h),) + tuple(v.uvs[1:]))
                          for v in g.vertices)
            parts[i] = replace(parts[i], geometry=replace(g, vertices=verts), textures=(tname,) + tuple(parts[i].textures[1:]))
        made.append({'texture': tname, 'source': src, 'region': [x0, y0, w, h], 'atlas': [W, H], 'parts': ids})
    return made
