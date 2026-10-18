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
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ground_clusters as gcl  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
import gcoll_walls_vs_limits as gw  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, rebuild_topology  # noqa: E402

BS = chr(92)
MODEL_DIR = 'DataGx/Misc/PS2Port/terrain/'


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


def collision(tree, ps2_non, pc_all, pcn):
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
        if twin:
            stats['twin'] += 1
            m = {(round(p[0], 2), round(p[2], 2)): p[1] for p in twin[0]['p']}
            pc_pts = [(p[0], m[(round(p[0], 2), round(p[2], 2))], p[2]) for p in pts]
            if max(abs(a[1] - b[1]) for a, b in zip(pts, pc_pts)) < 1e-3:
                stats['same_height'] += 1
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


def texture_dxt(manifest, ps2_root, name, hay_header):
    path = BS + 'TNG' + BS + 'DATAPSM' + BS + 'COURSE' + BS + 'TURKEY3' + BS + name.split(BS)[-1].upper() + '.GXI'
    try:
        gxi = o.extract(manifest, ps2_root, path)
    except SystemExit:
        return None
    try:
        tex = o.p.parse_gxi(gxi)
    except Exception:
        return None
    w_, h_ = tex['width'], tex['height']
    rgba = gxi[8:8 + w_ * h_ * 4]
    if len(rgba) != w_ * h_ * 4:
        return None
    bgra = bytearray(len(rgba))
    for i in range(0, len(rgba), 4):
        bgra[i], bgra[i + 1], bgra[i + 2], bgra[i + 3] = rgba[i + 2], rgba[i + 1], rgba[i], rgba[i + 3]
    return hay_header[:12] + struct.pack('<2I', w_, h_) + bytes(bgra), (w_, h_)


def visual_models(ps2_root, manifest, ps2_non, template, hay):
    """Per-texture static models of the PS2 non-exact ground triangles: ({path: bytes}, [(egg name, model name, centroid)], report)."""
    by_tex = defaultdict(list)
    for t in ps2_non:
        by_tex[t['tex']].append(t)
    files, eggs, report = {}, [], {'textures': []}
    for n, (tex, tris) in enumerate(sorted(by_tex.items(), key=lambda kv: -len(kv[1]))):
        built = texture_dxt(manifest, ps2_root, tex, hay.header) if tex else None
        if built is None:
            report['textures'].append({'texture': tex, 'triangles': len(tris), 'skipped': 'texture not convertible'})
            continue
        dxt, size = built
        allp = [p for t in tris for p in t['p']]
        c = tuple(sum(p[i] for p in allp) / len(allp) for i in range(3))
        vertices, faces = [], []
        for t in tris:
            local = [(p[0] - c[0], p[1] - c[1], p[2] - c[2]) for p in t['p']]
            nrm = o.normal_of(*local)
            order = (0, 1, 2) if nrm[1] >= 0 else (0, 2, 1)  # ground faces point up; mirrored triangles are flipped
            if nrm[1] < 0:
                nrm = tuple(-x for x in nrm)
            base = len(vertices)
            for i in order:
                u, v = t['uv'][i]
                vertices.append(CompiledVertex(tuple(local[i]), nrm, t['col'][i], ((u, 1.0 - v),)))
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
        eggs.append((f'ps2_{name}', 'misc' + BS + 'ps2port' + BS + 'terrain' + BS + name + BS + name, c))
        report['textures'].append({'texture': tex, 'model': name, 'triangles': len(tris), 'vertices': len(vertices), 'size': list(size)})
    return files, eggs, report
