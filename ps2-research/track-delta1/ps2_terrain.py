"""T4c: carry the PS2 ground triangles that differ from the PC ground into a loose PC course (visual + collision).

Ground = PS2 PSM meshes with shader(ground); PC ground = course-DX draws whose third texture slot is noise-tga. A triangle is exact when the other
side has a triangle with the same three vertices (0.001). For Turkey3: 4,020 PS2 and 3,512 PC non-exact ground triangles; 3,424 of the PS2 ones
share the XZ footprint of a PC triangle (2,694 of them with identical heights: only UV, colour or texture differ).

Visual: every PC non-exact ground triangle is neutralised in the course DX (its three local indices set to the same vertex, no structural change) and
every PS2 non-exact ground triangle is added as per-texture static models (one Egg each, template DX, GXI to DXT, vertex tint and UV from the PS2).
Collision: per PS2 triangle a fill slab (solid between the PC surface and the PS2 surface where PS2 is higher) and a carve slab (empty where PS2 is
lower), in the tag100 tree; slab planes carry a valid ground code and normals pointing to the empty side. Triangles with the same footprint and the
same heights need no collision change.
"""
import math
import struct
import sys
import zlib
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ground_clusters as gcl  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
import gcoll_walls_vs_limits as gw  # noqa: E402
import ground_material as gmat  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, rebuild_topology  # noqa: E402

BS = chr(92)
MODEL_DIR = 'DataGx/Misc/PS2Port/terrain/'


def make_dxt(bgra, width, height, template_header):
    """DXT file bytes: 20-byte header (magic and word_0x04 from the template, word_0x08 = CRC32 of the pixel payload, width, height) + BGRA rows.

    word_0x08 is the CRC32 of the payload in all 25 Turkey3 files checked (track-ground1 audit); the earlier converters copied the haybale value into
    every converted texture."""
    payload = bytes(bgra)
    if len(payload) != width * height * 4:
        raise ValueError('payload size does not match the dimensions')
    return template_header[:8] + struct.pack('<3I', zlib.crc32(payload) & 0xFFFFFFFF, width, height) + payload


def kxz(points):
    return tuple(sorted((round(p[0], 2), round(p[2], 2)) for p in points))


def plane_up(points):
    """(n, d) of the plane through three points with the normal pointing up, or None when it is nearly vertical."""
    a, b, c = points
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    ln = math.sqrt(sum(x * x for x in n))
    if ln < 1e-9:
        return None
    n = tuple(x / ln for x in n)
    if n[1] < 0:
        n = tuple(-x for x in n)
    if n[1] < 0.05:
        return None
    return n, -(n[0] * a[0] + n[1] * a[1] + n[2] * a[2])


def side_planes(points):
    """Outward vertical half-spaces of the XZ projection of the triangle."""
    out = []
    for i in range(3):
        a, b, c = points[i], points[(i + 1) % 3], points[(i + 2) % 3]
        dx, dz = b[0] - a[0], b[2] - a[2]
        ln = math.hypot(dx, dz)
        if ln < 1e-9:
            return None
        n = (dz / ln, 0.0, -dx / ln)
        d = -(n[0] * a[0] + n[2] * a[2])
        if n[0] * c[0] + n[2] * c[2] + d > 0:
            n, d = (-n[0], 0.0, -n[2]), -d
        out.append((n, d))
    return out


def slab(sides, upper, lower):
    """Half-spaces of the volume under plane `upper` and above plane `lower` (both (n_up, d)) inside the vertical prism."""
    (nu, du), (nl, dl) = upper, lower
    return sides + [(nu, du), ((-nl[0], -nl[1], -nl[2]), -dl)]


def load_delta(ps2_root, pc_dx):
    scene, ps2, model, pc = gcl.load(ps2_root, pc_dx)
    ps2_keys = {gcl.key(t['p']) for t in ps2}
    pc_keys = {gcl.key(t['p']) for t in pc}
    ps2_non = [t for t in ps2 if t['ground'] and gcl.key(t['p']) not in pc_keys]
    pc_non = [t for t in pc if t['ground'] and gcl.key(t['p']) not in ps2_keys]
    return scene, model, ps2_non, pc_non, pc


def refine(ps2_non, pc_non, pc_all, height_tolerance=0.01, uv_tolerance=2e-3):
    """Split the PS2 non-exact ground triangles into equivalent (kept as the native PC triangle) and replacing ones.

    A PS2 triangle is equivalent to a PC ground triangle with the same XZ footprint when (a) the heights agree within `height_tolerance`,
    (b) the base texture name is the same and (c) the base UV agrees at the three vertices, either exactly or by one integer offset that is the same
    for all three (identical mapping under texture wrap addressing; 1,706 of Turkey3's 1,723 same-geometry same-texture UV differences are such offsets).
    Vertex colours are not compared: the PC prelight stays. Equivalent PS2 triangles are not added and their PC twins are not neutralised, so they keep the
    native PC material including the noise stage. Everything else replaces: different geometry, different base texture, a different UV mapping or no PC
    triangle with that footprint.
    Returns (ps2_replace, pc_candidates, stats); pc_candidates = pc_non without the twins of equivalent triangles."""
    twins = defaultdict(list)
    for t in pc_all:
        if t['ground']:
            twins[kxz(t['p'])].append(t)
    replace, keep_pc, stats = [], set(), defaultdict(int)
    for t in ps2_non:
        tw = twins.get(kxz(t['p']))
        if not tw:
            replace.append(t)
            stats['no_pc_footprint'] += 1
            continue
        match = tw[0]
        pos = {(round(p[0], 2), round(p[2], 2)): k for k, p in enumerate(match['p'])}
        order = [pos.get((round(p[0], 2), round(p[2], 2))) for p in t['p']]
        if None in order:
            replace.append(t)
            stats['footprint_vertex_mismatch'] += 1
            continue
        dy = max(abs(p[1] - match['p'][order[k]][1]) for k, p in enumerate(t['p']))
        name = t['tex'].split(BS)[-1]
        if dy >= height_tolerance:
            replace.append(t)
            stats['geometry_differs'] += 1
        elif name != match['tex']:
            replace.append(t)
            stats['base_texture_differs'] += 1
        else:
            d = [(t['uv'][k][0] - match['uv'][order[k]][0], t['uv'][k][1] - match['uv'][order[k]][1]) for k in range(3)]
            exact = all(abs(a) < uv_tolerance and abs(b) < uv_tolerance for a, b in d)
            integer = (all(abs(a - round(a)) < uv_tolerance and abs(b - round(b)) < uv_tolerance for a, b in d)
                       and len({(round(a), round(b)) for a, b in d}) == 1)
            if exact or integer:
                keep_pc.add((match['draw'], match['first_index']))
                stats['equivalent_exact_uv' if exact else 'equivalent_integer_uv_offset'] += 1
            else:
                replace.append(t)
                stats['uv_mapping_differs'] += 1
    candidates = [t for t in pc_non if (t['draw'], t['first_index']) not in keep_pc]
    stats['ps2_replace'] = len(replace)
    stats['pc_candidates'] = len(candidates)
    stats['pc_kept_equivalent'] = len(pc_non) - len(candidates)
    return replace, candidates, dict(stats)


def with_replacement(pc_non, ps2_non, cell=12.0, ratio=0.75):
    """PC triangles that have a PS2 replacement near them: some PS2 added triangle whose centroid lies within `ratio` of the PC triangle's longest edge
    (3D). PC triangles without one stay (neutralising them leaves a hole, seen in the first terrain build at the rock arch near 2600, 85, -845)."""
    def cen(p):
        return tuple(sum(q[i] for q in p) / 3 for i in range(3))
    grid = defaultdict(list)
    for t in ps2_non:
        c = cen(t['p'])
        grid[int(c[0] // cell), int(c[1] // cell), int(c[2] // cell)].append(c)
    keep, drop = [], []
    for t in pc_non:
        c = cen(t['p'])
        edge = max(math.dist(t['p'][i], t['p'][(i + 1) % 3]) for i in range(3))
        kx, ky, kz = int(c[0] // cell), int(c[1] // cell), int(c[2] // cell)
        near = min((math.dist(c, q) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) for q in grid.get((kx + dx, ky + dy, kz + dz), [])), default=1e9)
        (keep if near <= ratio * edge else drop).append(t)
    return keep, drop


def neutralise(course, model, pc_non):
    """Set the three local indices of every listed PC triangle to its first one (zero area, no structural change)."""
    data = bytearray(course)
    base = model.local_index_offset
    for t in pc_non:
        o0 = base + 2 * t['first_index']
        first = data[o0:o0 + 2]
        data[o0 + 2:o0 + 4] = first
        data[o0 + 4:o0 + 6] = first
    return bytes(data)


def collision(tree, ps2_non, pc_all, pcn, ps2_top=None, max_dy=8.0):
    """Fill / carve slabs for the PS2 non-exact ground triangles; returns a report dict."""
    twins = defaultdict(list)
    for t in pc_all:
        if t['ground']:
            twins[kxz(t['p'])].append(t)
    stats = {'triangles': len(ps2_non), 'same_height': 0, 'skipped_vertical': 0, 'fill_brushes': 0, 'carve_brushes': 0, 'leaves_filled': 0,
             'leaves_carved': 0, 'twin': 0, 'estimated_lower': 0}
    for t in ps2_non:
        pts = t['p']
        up_ps2 = plane_up(pts)
        sides = side_planes(pts)
        if up_ps2 is None or sides is None:
            stats['skipped_vertical'] += 1
            continue
        twin = twins.get(kxz(pts))
        if not twin:
            stats['no_twin_skipped'] = stats.get('no_twin_skipped', 0) + 1  # PC surface unknown under this triangle: no collision edit
            continue
        centroid_xz = (sum(p[0] for p in pts) / 3, sum(p[2] for p in pts) / 3)
        if ps2_top is not None:
            top = ps2_top(*centroid_xz)
            if top is not None and sum(p[1] for p in pts) / 3 < top - 0.05:
                stats['lower_layer_skipped'] = stats.get('lower_layer_skipped', 0) + 1  # arches, overhangs, rock undersides: slabs would fill or cut passages
                continue
        if twin:
            stats['twin'] += 1
            m = {(round(p[0], 2), round(p[2], 2)): p[1] for p in twin[0]['p']}
            pc_pts = [(p[0], m[(round(p[0], 2), round(p[2], 2))], p[2]) for p in pts]
            dys = max(abs(a[1] - b[1]) for a, b in zip(pts, pc_pts))
            if dys < 1e-3:
                stats['same_height'] += 1
                continue
            if dys > max_dy:
                stats['too_thick_skipped'] = stats.get('too_thick_skipped', 0) + 1
                continue
        else:
            stats['estimated_lower'] += 1
            heights = [gw.ground_at(pcn, p[0], p[2]) for p in pts]
            if any(h is None for h in heights):
                stats['skipped_vertical'] += 1
                continue
            pc_pts = [(p[0], h, p[2]) for p, h in zip(pts, heights)]
        up_pc = plane_up(pc_pts)
        if up_pc is None:
            stats['skipped_vertical'] += 1
            continue
        centroid = tuple(sum(p[i] for p in pts) / 3 for i in range(3))
        code = tree.reference_code((centroid[0], min(p[1] for p in list(pts) + pc_pts) - 0.5, centroid[2]))
        if code is None:
            code = 0
        n = tree.apply_brush(slab(sides, up_ps2, up_pc), code, 'fill')
        if n:
            stats['fill_brushes'] += 1
            stats['leaves_filled'] += n
        n = tree.apply_brush(slab(sides, up_pc, up_ps2), code, 'carve')
        if n:
            stats['carve_brushes'] += 1
            stats['leaves_carved'] += n
    return stats


def texture_difference(pc, rgba, w_, h_, flip_rows=True, flip_cols=False):
    """Mean absolute RGB difference (0..255) between a PC DXT (box-filtered to w_ x h_) and PS2 RGBA rows; None when the sizes are not a whole ratio.

    PC rows are bottom-up and GXI rows top-down, so the expected orientation is flip_rows=True. Other flags exist for the audit only."""
    if pc.width % w_ or pc.height % h_:
        return None
    fx, fy = pc.width // w_, pc.height // h_
    total = 0.0
    for y in range(h_):
        for x in range(w_):
            acc = [0, 0, 0]
            for yy in range(fy):
                for xx in range(fx):
                    row = (pc.height - 1 - (y * fy + yy)) if flip_rows else (y * fy + yy)
                    col = (pc.width - 1 - (x * fx + xx)) if flip_cols else (x * fx + xx)
                    i = (row * pc.width + col) * 4
                    acc[0] += pc.bgra[i + 2]
                    acc[1] += pc.bgra[i + 1]
                    acc[2] += pc.bgra[i]
            g = (y * w_ + x) * 4
            n = fx * fy
            total += abs(acc[0] / n - rgba[g]) + abs(acc[1] / n - rgba[g + 1]) + abs(acc[2] / n - rgba[g + 2])
    return total / (w_ * h_ * 3)


def texture_dxt(manifest, ps2_root, name, hay_header, pc_dir=None, tolerance=8.0, rename_tolerance=2.0):
    """DXT bytes for a PS2 texture name: the PC texture of the same name when it exists and shows the same image, otherwise the PS2 GXI (64x64).

    The PC course textures are 128x128, the PS2 ones 64x64. Similarity: the PC image is box-filtered to the PS2 size (PC rows are bottom-up, GXI rows
    top-down) and the mean absolute channel difference must be below `tolerance` (0..255; true same-artwork pairs on Turkey3 measure at most 6.6, the
    first different-artwork pair 11.8). If the same-name PC file is missing or different, a PC file of another name showing this image within
    `rename_tolerance` is used ('pc_renamed:<name>': PS2 plating2 is PC tanky, PS2 i2a_planks2 is PC wood_01). Otherwise the PS2 file is kept.
    Returns (dxt bytes, (w, h), 'pc' | 'pc_renamed:<name>' | 'pc_unchecked' | 'ps2') or None.
    """
    base = name.split(BS)[-1]
    path = BS + 'TNG' + BS + 'DATAPSM' + BS + 'COURSE' + BS + 'TURKEY3' + BS + base.upper() + '.GXI'
    rgba = w_ = h_ = None
    try:
        gxi = o.extract(manifest, ps2_root, path)
        tex = o.p.parse_gxi(gxi)
        w_, h_ = tex['width'], tex['height']
        rgba = gxi[8:8 + w_ * h_ * 4]
        if len(rgba) != w_ * h_ * 4:
            rgba = None
    except Exception:  # noqa: BLE001
        rgba = None
    return choose_texture(base, rgba, w_, h_, hay_header, pc_dir, tolerance, rename_tolerance)


def choose_texture(base, rgba, w_, h_, hay_header, pc_dir=None, tolerance=8.0, rename_tolerance=2.0):
    """Pure part of texture_dxt: `rgba` = PS2 pixels (w_ x h_, top-down) or None when the PS2 file is unreadable."""
    gxi = rgba
    if pc_dir is not None:
        pc_file = Path(pc_dir) / (base + '.dxt')
        if pc_file.exists():
            pc = parse_dxt_bytes(pc_file.read_bytes())
            if gxi is None:
                return pc_file.read_bytes(), (pc.width, pc.height), 'pc_unchecked'  # no readable PS2 texture to compare with; reported, never silent
            diff = texture_difference(pc, rgba, w_, h_)
            if diff is not None and diff <= tolerance:
                return pc_file.read_bytes(), (pc.width, pc.height), 'pc'
    if pc_dir is not None and gxi is not None:
        # same-name PC texture missing or showing other artwork: a PC texture of another name that shows this very image (renamed on the PC)
        best = None
        for other in sorted(Path(pc_dir).glob('*.dxt')):
            if other.stem == base:
                continue
            key = (str(other), w_, h_)
            ot = parse_dxt_bytes(other.read_bytes())
            d = texture_difference(ot, rgba, w_, h_)
            if d is not None and (best is None or d < best[1]):
                best = (other, d, ot)
        if best is not None and best[1] <= rename_tolerance:
            return best[0].read_bytes(), (best[2].width, best[2].height), 'pc_renamed:' + best[0].stem
    if gxi is None:
        return None
    bgra = bytearray(len(rgba))
    for i in range(0, len(rgba), 4):
        bgra[i], bgra[i + 1], bgra[i + 2], bgra[i + 3] = rgba[i + 2], rgba[i + 1], rgba[i], rgba[i + 3]
    return make_dxt(bgra, w_, h_, hay_header), (w_, h_), 'ps2'


def noise_mean_factor(pc_dir):
    """Mean factor of the native PC ground noise stage (stage 1 CURRENT x TEXTURE MODULATE2X with noise-tga): 2 x mean(noise RGB) / 255, from the PC file.

    Measured 0.9537 on Turkey3 (the same file is in all 36 courses). The added ground models have no noise stage, so their vertex tint is scaled by this
    factor to match the PC ground on average; the noise detail itself is not reproduced (the PS2 data has no noise UV, see track-ground1/material-parity.md)."""
    if pc_dir is None:
        return None
    f = Path(pc_dir) / 'noise-tga.dxt'
    if not f.exists():
        return None
    tex = parse_dxt_bytes(f.read_bytes())
    vals = [tex.bgra[i + c] for i in range(0, len(tex.bgra), 4) for c in range(3)]
    return 2.0 * sum(vals) / len(vals) / 255.0


def visual_models(ps2_root, manifest, ps2_non, template, hay, pc_dir=None, tint=True, detail='tint'):
    """Per-texture static models of the PS2 non-exact ground triangles: ({path: bytes}, [(egg name, model name, centroid)], report)."""
    by_tex = defaultdict(list)
    for t in ps2_non:
        by_tex[t['tex']].append(t)
    # detail 'tint' (default): vertex tint x mean noise factor. detail 'noise2' (EXPERIMENTAL, HYPOTHESIS): second UV set from the PS2 +28/+32 pair and slot 2 =
    # noise-tga, so the engine may apply the native noise stage; no tint then.
    noise2 = detail == 'noise2'
    if noise2:
        template = gmat.two_uv_noise_template(template)
        noise_file = Path(pc_dir) / 'noise-tga.dxt'
        if not noise_file.exists():
            raise SystemExit('noise2 needs the PC noise-tga.dxt')
    factor = noise_mean_factor(pc_dir) if (tint and not noise2) else None
    files, eggs, report = {}, [], {'textures': [], 'noise_mean_factor': factor, 'detail': detail}
    for n, (tex, tris) in enumerate(sorted(by_tex.items(), key=lambda kv: -len(kv[1]))):
        built = texture_dxt(manifest, ps2_root, tex, hay.header, pc_dir) if tex else None
        if built is None:
            report['textures'].append({'texture': tex, 'triangles': len(tris), 'skipped': 'texture not convertible'})
            continue
        dxt, size, source = built
        allp = [p for t in tris for p in t['p']]
        c = tuple(sum(p[i] for p in allp) / len(allp) for i in range(3))
        vertices, faces = [], []
        for t in tris:
            local = [(p[0] - c[0], p[1] - c[1], p[2] - c[2]) for p in t['p']]
            nrm = o.normal_of(*local)
            # gentle slopes are written once, facing up; steep, vertical and downward faces (cliffs, rock undersides) in both windings:
            # the PS2 strip winding is not resolved and a wrong single winding is culled away (holes in the first terrain build)
            if abs(nrm[1]) > 0.7:
                variants = [((0, 1, 2), nrm)] if nrm[1] > 0 else [((0, 2, 1), tuple(-x for x in nrm))]
            else:
                variants = [((0, 1, 2), nrm), ((0, 2, 1), tuple(-x for x in nrm))]
            for order, vn in variants:
                base = len(vertices)
                for i in order:
                    u, v = t['uv'][i]
                    col = t['col'][i]
                    if factor is not None:
                        col = bytes(min(255, int(round(c * factor))) for c in col[:3]) + col[3:]
                    uvs = ((u, 1.0 - v), (t['aux'][i][0], 1.0 - t['aux'][i][1])) if noise2 else ((u, 1.0 - v),)
                    vertices.append(CompiledVertex(tuple(local[i]), vn, col, uvs))
                faces.append((base, base + 1, base + 2))
        if len(vertices) > 65000:
            report['textures'].append({'texture': tex, 'triangles': len(tris), 'skipped': 'more than 65,000 vertices'})
            continue
        rebuilt = rebuild_topology(template, {0: DrawGeometry(tuple(vertices), tuple(faces))}, bounds_mode='recompute')
        dx = bytearray(rebuilt.data)
        slot = next(s for s in rebuilt.output_model.physical_draws[0].texture_slots if s.slot == 0)
        slot_name = f'g{n:02d}-tga'.encode()
        dx[slot.data_offset:slot.data_offset + len(slot_name)] = slot_name
        parse_dx_bytes(bytes(dx))
        name = f'terrain{n:02d}'
        files[MODEL_DIR + name + '/' + name + '.dx'] = bytes(dx)
        files[MODEL_DIR + name + '/' + slot_name.decode() + '.dxt'] = dxt
        if noise2:
            files[MODEL_DIR + name + '/noise-tga.dxt'] = noise_file.read_bytes()
        eggs.append((f'ps2_{name}', 'misc' + BS + 'ps2port' + BS + 'terrain' + BS + name + BS + name, c))
        report['textures'].append({'texture': tex, 'model': name, 'triangles': len(tris), 'vertices': len(vertices), 'size': list(size), 'texture_source': source})
    return files, eggs, report
