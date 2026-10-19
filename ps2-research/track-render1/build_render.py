"""Build the render section of a PC course DX from the PS2 landscape (W2 step 2).

    python build_render.py --course Turkey3 --suffix-from <W1 course DX> --out <dir> [--noise fit]

Every triangle of every drawn PS2 landscape mesh becomes a triangle of the PC course DX, nothing else stays. Per triangle:
  * matched: the PC course has the same triangle (positions, 1e-3) with the same base texture -> the PC vertex attributes (normal, both UV sets)
    and the PC corner order are copied and the triangle joins a draw with the PC draw fields; the colour is the PS2 one (PS2 bakes the shade of
    its own objects into it; equal to PC within 8 on most vertices);
  * otherwise PS2 attributes: position, normal (+0), colour = PS2 bytes (+17, +18, +19, +16), UV (+20) with V flipped; corner order such that
    (b - a) x (c - a) points against the vertex normals (the PC convention on 96.6 percent of the shared triangles; matched ones keep the PC order);
    draw fields from a PC draw with the same texture tuple and directive group, else from the directive rule table (NOTES.md, material-map-36.json).
Noise UV (second set) for ground triangles that use noise-tga and are not matched: the PS2 vertex pair at +28 plus 0.5 (`--noise ps2`, default;
equal to the PC noise UV modulo 1 on every shared vertex of 36 courses, ps2_mesh.noise_uv). Older modes: `plain` takes the PC noise UV of a PC
vertex at the same position and drops the noise layer otherwise; `local` fits the planar map of the nearest PC noise triangle. Non-noise draws
have a zero second UV set (as PC).
Batches: the PC batch / sector partition is kept; each triangle goes to the batch whose tag1500 sector polygon contains its XZ centroid. A
triangle outside every sector polygon goes to the root record (always drawn), which is where PC keeps exactly such triangles; PC root triangles
stay in the root. Alpha-blended groups are wrapped in a tag-5 sphere and a tag-6 sort tree built from polygon planes.
The suffix (tag100, tag1339, tag1400, tag1500) comes from --suffix-from; tag1339 is widened when the new vertices leave it.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'course-port'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
sys.path.insert(0, str(HERE.parent / 'track-coll2'))
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402
import material_map as mm  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
import ps2_terrain as terrain  # noqa: E402
import tag1400_io as io  # noqa: E402
import tag1500_probe as sectors_mod  # noqa: E402
import ps2_mesh  # noqa: E402
from master_rallye.course_render_writer import Container, CourseRender, Draw  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402

MAX_LOCAL = 65535
ONE = struct.pack('<f', 1.0)


# ------------------------------------------------------------------ PS2 side
def ps2_vertex(payload, i):
    """PS2 vertex: position, normal, colour (PS2 bytes +17, +18, +19, +16), UV as is (the PC course uses the raw PS2 UV, see ps2_mesh)."""
    return ps2_mesh.vertex(payload, i)


def ps2_mesh_triangles(scene, mesh):
    return ps2_mesh.mesh_triangles(scene, mesh)


ORIENTATION_MAP = HERE / 'orientation-map-36.json'


def group_key(mat, textures):
    """Directive group without $clamp (key of orientation-map-36.json)."""
    d = mm.directives(mat)
    d.pop('clamp', None)
    noise = any('noise' in t['name'].lower() for t in textures)
    return json.dumps({**d, 'noise_texture': noise}, sort_keys=True)


def two_sided_rule(mat, textures, table):
    """True when PC stores this material two-sided (each triangle plus a reversed copy): from the measured PC fraction of the group (>= 0.5), or,
    for a group PC never shows, when it is alpha-tested or alpha-blended (every such measured group is two-sided on PC)."""
    g = group_key(mat, textures)
    row = table.get(g)
    if row and row['shared'] >= 20:
        return row['two_sided_fraction'] >= 0.5, 'measured'
    d = mm.directives(mat)
    return ('alphatest' in d or 'alphablend' in d), 'alpha_rule'


def tex_stem(name):
    return name.replace('/', '\\').split('\\')[-1]


# ------------------------------------------------------------------ geometry helpers
def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def point_in_polygon(x, z, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, z1 = poly[i]
        x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z):
            xi = x1 + (z - z1) * (x2 - x1) / (z2 - z1)
            if x < xi:
                inside = not inside
    return inside


def dist_to_polygon(x, z, poly):
    best = math.inf
    n = len(poly)
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        dx, dz = x2 - x1, z2 - z1
        t = 0.0 if dx == dz == 0 else max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - x1 - t * dx, z - z1 - t * dz))
    return best


# ------------------------------------------------------------------ rule table
def clamp_word(dirs):
    return {'u': 2, 'v': 4, 'uv': 0}.get(dirs.get('clamp'), 1)


def rule_fields(dirs, noise, slot1):
    """Draw fields from PS2 directives (NOTES.md table; derived from 1.2 million shared triangles on 36 courses)."""
    shader = dirs.get('shader')
    w14 = clamp_word(dirs)
    if shader in ('puddle', 'water'):
        return {'flags': '00000101', 'w14': w14, 'w18': 1, 'w24': 19, 'sorted': False}, 'rule:water'
    if shader == 'waterfall':
        return {'flags': '01000001', 'w14': w14, 'w18': 2, 'w24': 1, 'sorted': False}, 'rule:waterfall'
    if 'alphablend' in dirs or shader in ('wires', 'wire'):
        return {'flags': '01000001', 'w14': w14, 'w18': 0, 'w24': 1, 'sorted': True}, 'rule:alphablend'
    if 'alphatest' in dirs:
        return {'flags': '01010101', 'w14': w14, 'w18': 0, 'w24': 7 if slot1 else 3, 'sorted': False}, 'rule:alphatest'
    if noise:
        return {'flags': '00000101', 'w14': w14, 'w18': 0, 'w24': 11, 'sorted': False}, 'rule:ground_noise'
    return {'flags': '00000101', 'w14': w14, 'w18': 0, 'w24': 7 if slot1 else 3, 'sorted': False}, 'rule:opaque'


def draw_fields(d):
    return {'flags': d.flags_0x20.hex(), 'w14': d.unknown_0x14, 'w18': d.unknown_0x18, 'w24': d.unknown_0x24}


def alpha_class(flags_hex):
    """'test', 'blend' or 'opaque' from the draw flags (byte 0 alpha on, byte 1 alpha test; see rule_fields)."""
    if flags_hex[2:4] == '01':
        return 'test'
    return 'blend' if flags_hex[:2] == '01' else 'opaque'


def cyc(pts):
    """Cyclic corner order normalised to start at the smallest corner (winding identity of a triangle)."""
    i = pts.index(min(pts))
    return tuple(pts[i:] + pts[:i])


def rkey(p):
    return tuple(round(c, 3) for c in p)


# ------------------------------------------------------------------ builder
class Builder:
    def __init__(self, course, noise_mode='ps2', two_sided_mode='all'):
        self.course = course
        self.noise_mode = noise_mode
        self.two_sided_mode = two_sided_mode
        self.retail = course.pc_dx.read_bytes()
        self.pc = CourseRender.from_bytes(self.retail, course.name)
        self.payload = cc.read_ps2(course.ps2_psm)
        self.scene = o.w.decode_scene(self.payload)
        self.report = collections.Counter()
        self.textures = {}               # stem -> (dxt bytes or None when the PC file is used as is, source)
        self.pc_dir = course.pc_dx.parent
        self.orientation = json.loads(ORIENTATION_MAP.read_text()) if ORIENTATION_MAP.exists() else {}
        header = (self.pc_dir / 'noise-tga.dxt').read_bytes()[:20] if (self.pc_dir / 'noise-tga.dxt').exists() else None
        self.dxt_header = header
        self._index_pc()
        self._sectors()

    # PC triangle index and per-position noise UV
    def _index_pc(self):
        self.pc_tris = {}
        self.pc_noise_uv = {}
        self.pc_templates = {}           # texture tuple -> fields of the first PC draw with it
        self._tuple_votes = collections.defaultdict(collections.Counter)   # texture tuple -> fields json -> PC triangles
        self.pc_orient = collections.defaultdict(set)                      # triangle key -> PC corner orders (cyc)
        self._base_votes = collections.defaultdict(collections.Counter)
        sorted_draws = set()

        def mark(rec, inside):
            if isinstance(rec, Container):
                for c in rec.children:
                    mark(c, inside or rec.tag in (5, 6))
            elif inside:
                sorted_draws.add(id(rec))
        for b in self.pc.batches:
            for r in b:
                mark(r, False)
        r = self.pc
        root_draws = set()

        def mark_root(rec):
            if isinstance(rec, Container):
                for c in rec.children:
                    mark_root(c)
            else:
                root_draws.add(id(rec))
        for rr in r.roots:
            mark_root(rr)
        for d in r.draws():
            tt_ = d.texture_tuple
            f = draw_fields(d)
            f['sorted'] = id(d) in sorted_draws
            self.pc_templates.setdefault(tt_, f)
            self._tuple_votes[tt_][json.dumps(f, sort_keys=True)] += d.index_count // 3
            self._base_votes[tt_[0]][(tt_, json.dumps(f, sort_keys=True))] += d.index_count // 3
            noise = len(tt_) > 2 and tt_[2] == 'noise-tga'
            for k in range(d.index_start, d.index_start + d.index_count, 3):
                vids = [d.vertex_base + r.indices[k + j] for j in range(3)]
                pts = [r.positions[v] for v in vids]
                self.pc_tris[mm.key(pts)] = (d, vids, tt_, f, id(d) in root_draws)
                self.pc_orient[mm.key(pts)].add(cyc([rkey(p) for p in pts]))
                if noise:
                    for v in vids:
                        self.pc_noise_uv.setdefault(tuple(round(c, 3) for c in r.positions[v]), r.uv_sets[1][v])

    def _sectors(self):
        sl = extract_tag100_from_dx_bytes(self.retail, 'retail')
        _, self.tag1339, _, r1500 = io.split_suffix(sl.raw)
        ents, _ = sectors_mod.parse(r1500)
        self.sectors = [[(p[0], p[2]) for p in e['points']] for e in ents]
        self.n_batches = len(self.pc.batches)
        if len(self.sectors) != self.n_batches + 1:
            raise ValueError('sector count is not batches + 1')

    def batch_of(self, tri):
        cx = sum(p[0] for p in tri) / 3
        cz = sum(p[2] for p in tri) / 3
        hits = [i for i in range(1, len(self.sectors)) if point_in_polygon(cx, cz, self.sectors[i])]
        if hits:
            self.report['batch_inside_sector'] += 1
            return hits[0] - 1
        # outside every sector polygon: the root record, as PC does (every PC root triangle lies outside all sectors on France1, FranceM,
        # Turkey2, Italy2; 99.98 percent of PC batch triangles lie inside their own sector)
        self.report['root_outside_sectors'] += 1
        dd = min(dist_to_polygon(cx, cz, self.sectors[i]) for i in range(1, len(self.sectors)))
        self.report['root_outside_sectors_max_distance'] = round(max(self.report.get('root_outside_sectors_max_distance', 0.0), dd), 2)
        return -1

    def texture(self, ps2_name):
        """PC texture stem for a PS2 texture name, by the TRACK-GROUND1 policy; PS2-only textures are converted and recorded."""
        stem = tex_stem(ps2_name)
        if stem in self.textures:
            return self.textures[stem][0]
        path = '\\TNG\\DATAPSM\\' + ps2_name.replace('/', '\\').upper() + '.GXI'
        rgba = w_ = h_ = None
        try:
            gxi = cc.read_ps2(path)
            tex = o.p.parse_gxi(gxi)
            w_, h_ = tex['width'], tex['height']
            rgba = gxi[8:8 + w_ * h_ * 4]
            if len(rgba) != w_ * h_ * 4:
                rgba = None
        except Exception:  # noqa: BLE001 - reported below
            rgba = None
        res = terrain.choose_texture(stem, rgba, w_, h_, self.dxt_header, self.pc_dir)
        if res is None:
            name, data, src = stem, None, 'missing'
        else:
            data, _, src = res
            name = src.split(':', 1)[1] if src.startswith('pc_renamed:') else stem
            if src.startswith('pc'):
                data = None          # the PC file is in the retail course folder already
            elif src == 'ps2':
                # PC DXT rows are bottom-up and the course uses the raw PS2 UV: write the GXI rows flipped
                data = terrain.make_dxt(ps2_mesh.convert_gxi_rows(rgba, w_, h_), w_, h_, self.dxt_header)
        self.textures[stem] = (name, data, src)
        self.report['texture_' + src.split(':')[0]] += 1
        return name

    def oriented(self, idx):
        """PC corner order of a PS2 triangle: PC's own order where PC has the same triangle single-sided (whatever its texture), else the normal
        rule (ps2_mesh.pc_order). The normal rule fails where the ground folds under a rock: the visible face looks down there and the smoothed
        vertex normals point up (Turkey3 rock foot, owner's fourth test: PC culled the triangle and the sky colour showed through)."""
        o = ps2_mesh.pc_order(self.payload, idx)
        P = [ps2_mesh.vertex(self.payload, i)[0] for i in o]
        dirs = self.pc_orient.get(mm.key(P))
        if dirs and len(dirs) == 1 and cyc([rkey(p) for p in P]) not in dirs:
            return (o[1], o[0], o[2]), True
        return o, False

    def template_for(self, tt_, want):
        """Fields of the PC draws with this texture tuple whose alpha class is in `want` (most PC triangles first), or None. The texture tuple
        alone is not enough: ItalyW2 draws gate01 opaque first, and the PS2 `$alphatest` gate took that draw (owner's fence test)."""
        votes = [(n, fj) for fj, n in self._tuple_votes.get(tt_, {}).items() if alpha_class(json.loads(fj)['flags']) in want]
        if not votes:
            return None
        return json.loads(max(votes)[1])

    def ground_winding_suspects(self):
        """Keys of PS2-only ground triangles whose final corner order runs most of their shared edges in the same direction as the neighbour
        (an inconsistently oriented surface: one of them is flipped). Such a triangle gets both sides."""
        tris = []
        for m in self.scene.meshes:
            mat = m['material']
            if 'nodraw' in mm.directives(mat) or not ('$shader(ground)' in mat.lower() or '$surfacetype' in mat):
                continue
            for idx in ps2_mesh_triangles(self.scene, m):
                o, _ = self.oriented(idx)
                P = [ps2_mesh.vertex(self.payload, i)[0] for i in o]
                pts = [rkey(p) for p in P]
                if len(set(pts)) == 3:
                    tris.append((pts, mm.key(P)))
        edges = collections.defaultdict(int)
        for pts, _ in tris:
            for j in range(3):
                edges[(pts[j], pts[(j + 1) % 3])] += 1
        out = set()
        for pts, k in tris:
            if k in self.pc_orient:
                continue
            good = bad = 0
            for j in range(3):
                a, b = pts[j], pts[(j + 1) % 3]
                if edges.get((b, a)):
                    good += 1
                elif edges[(a, b)] > 1:
                    bad += 1
            if bad > good:
                out.add(k)
        return out

    def build(self):
        tris = []          # (batch, group key, cluster, [(pos, nrm, col, uv0, uv1)] x 3, fields, provenance)
        ps2_keys = []
        suspects = self.ground_winding_suspects()
        for mi, m in enumerate(self.scene.meshes):
            mat = m['material']
            dirs = mm.directives(mat)
            if 'nodraw' in dirs:
                self.report['skipped_nodraw_triangles'] += len(ps2_mesh_triangles(self.scene, m))
                continue
            names = [t['name'] for t in m['textures']]
            noise = any('noise' in tex_stem(n).lower() for n in names)
            base = self.texture(names[0]) if names else 'Null'
            slot1 = None
            if len(names) > 1 and 'noise' not in tex_stem(names[1]).lower():
                slot1 = self.texture(names[1])
            group_two_sided, why0 = two_sided_rule(mat, m['textures'], self.orientation)
            is_ground = '$shader(ground)' in mat.lower() or '$surfacetype' in mat
            # PC material of this mesh's matched triangles (texture tuple, fields json) -> triangles: the unmatched triangles of the same mesh take
            # it first (ItalyW2 posts: PC draws the matched ones 00000101/3, the first PC draw with gate01 is 00000001/1)
            mesh_votes = collections.Counter()
            for idx in ps2_mesh_triangles(self.scene, m):
                hit = self.pc_tris.get(mm.key([self.scene.position(i) for i in idx]))
                if hit and hit[2][0] == base:
                    mesh_votes[(hit[2], json.dumps(hit[3], sort_keys=True))] += 1
            for idx in ps2_mesh_triangles(self.scene, m):
                order_idx, from_pc = self.oriented(idx)
                if from_pc:
                    self.report['tri_winding_from_pc'] += 1
                verts = [ps2_vertex(self.payload, i) for i in order_idx]
                pos = [v[0] for v in verts]
                k = mm.key(pos)
                two_sided, why = group_two_sided, why0
                if is_ground and not two_sided and k in suspects:
                    two_sided, why = True, 'ground_winding_inconsistent'
                if not two_sided and (self.two_sided_mode == 'all' or k not in self.pc_tris):
                    # PS2 shows back sides (no culling), PC culls them: open shells and the open undersides of rocks show holes on PC (owner's
                    # v2/v3 tests). Mode 'all': every object and every steep or downward-facing ground triangle gets both sides; mode 'ps2only':
                    # only geometry PC does not have. Outward normal = -(b - a) x (c - a) in PC order; flat ground is never seen from below
                    if dirs.get('shader') in ('sign', 'water', 'puddle', 'waterfall', 'waterall'):
                        pass   # signs stay single-sided: PC keeps 99 percent of them single-sided; two-sided banners show mirrored text and
                               # fight with a banner mounted back to back (seen in the v1 test)
                    elif not is_ground:
                        two_sided, why = True, 'object_' + self.two_sided_mode
                    else:
                        fn = cross(sub(pos[1], pos[0]), sub(pos[2], pos[0]))
                        ln = math.sqrt(dot(fn, fn)) or 1.0
                        if -fn[1] / ln < 0.5:
                            two_sided, why = True, 'steep_ground_' + self.two_sided_mode
                ps2_keys.append(k)
                if two_sided:
                    ps2_keys.append(k)          # the reversed copy
                    self.report['tri_two_sided_' + why] += 1
                hit = self.pc_tris.get(k)
                if hit and hit[2][0] == base:
                    d, vids, tt_, f, in_root = hit
                    r = self.pc
                    # colour from PS2: PS2 bakes the shade of its own objects (trees PC does not have) into the vertex colour, PC lit those
                    # vertices without them; a PC colour next to a PS2-only triangle leaves a hard light/dark edge (owner's Turkey2 test)
                    ps2_col = {tuple(round(c, 3) for c in v[0]): bytes(v[2]) for v in verts}
                    attrs = [(r.positions[v], r.normals[v], ps2_col.get(tuple(round(c, 3) for c in r.positions[v]), bytes(r.colors[4 * v:4 * v + 4])),
                              r.uv_sets[0][v], r.uv_sets[1][v]) for v in vids]
                    self.report['vert_colour_ps2_differs_from_pc'] += sum(
                        1 for v in vids if max(abs(a - c) for a, c in zip(ps2_col.get(tuple(round(c, 3) for c in r.positions[v]), bytes(r.colors[4 * v:4 * v + 4])),
                                                                         bytes(r.colors[4 * v:4 * v + 4]))) > 8)
                    # PC triangles drawn from the root record (always drawn, no sector) stay in the root
                    if two_sided:
                        # PC keeps a two-sided triangle twice; the copy found first may be the reversed one: use the PS2-rule order
                        order = [tuple(round(c, 3) for c in v[0]) for v in verts]
                        if len(set(order)) == 3:
                            attrs = sorted(attrs, key=lambda a: order.index(tuple(round(c, 3) for c in a[0])))
                    batch = -1 if in_root else self.batch_of(pos)
                    tris.append((batch, tt_, f, mi, attrs, 'pc_copy'))
                    if two_sided:
                        tris.append((batch, tt_, f, mi, [attrs[1], attrs[0], attrs[2]], 'pc_copy'))
                    self.report['tri_pc_copy_root' if in_root else 'tri_pc_copy'] += 1
                    continue
                # PS2 attributes (corner order already by ps2_mesh.pc_order)
                tri_noise = noise            # per triangle: a triangle without noise UV must not change the mesh flag
                tt_ = (base, slot1 or 'Null', 'noise-tga' if tri_noise else 'Null')
                uv1 = [(0.0, 0.0)] * 3
                if tri_noise and self.noise_mode == 'ps2':
                    uv1 = [ps2_mesh.noise_uv(self.payload, i) for i in order_idx]
                    self.report['tri_noise_uv_ps2'] += 1
                elif tri_noise:
                    got = [self.pc_noise_uv.get(tuple(round(c, 3) for c in v[0])) for v in verts]
                    if all(g is not None for g in got):
                        uv1 = got
                        self.report['tri_noise_uv_pc_vertex'] += 1
                    elif self.noise_mode == 'local' and self.fit_noise(base, verts) is not None:
                        uv1 = self.fit_noise(base, verts)
                        self.report['tri_noise_uv_local_plane_EXPERIMENTAL'] += 1
                    else:
                        tt_ = (base, slot1 or 'Null', 'Null')
                        tri_noise = False
                        self.report['tri_noise_dropped_no_pc_uv'] += 1
                mesh_alpha = bool(m['flags'][0]) and 'alphatest' not in dirs and 'alphablend' not in dirs
                if 'alphatest' in dirs:
                    want = ('test',)
                elif 'alphablend' in dirs or dirs.get('shader') in ('wires', 'wire', 'waterfall'):
                    want = ('blend',)
                elif mesh_alpha:
                    want = ('test', 'blend')
                else:
                    want = ('opaque',) if dirs.get('shader') not in ('water', 'puddle') else ('opaque', 'blend')
                same_mesh = [(n, fj) for (t, fj), n in mesh_votes.items() if t == tt_ and alpha_class(json.loads(fj)['flags']) in want]
                first = self.pc_templates.get(tt_)
                if same_mesh:
                    tmpl, tprov = json.loads(max(same_mesh)[1]), 'pc_same_mesh'
                elif first is not None and alpha_class(first['flags']) in want:
                    tmpl, tprov = first, 'pc_template'
                else:
                    tmpl, tprov = self.template_for(tt_, want), 'pc_template_alpha_class'
                if first is not None and tmpl != first:
                    self.report['tri_template_not_first_pc_draw'] += 1
                if tmpl is not None:
                    f, prov = tmpl, tprov
                elif mesh_alpha:
                    # PS2 mesh flag 0 = alpha on without a directive (fence, fencegate): on 36 courses PC draws 91 percent of such triangles with
                    # alpha, mostly blended. Use PC's own material of this base texture when it is an alpha material, else alpha blend + sort.
                    votes = [(n, t, json.loads(fj)) for (t, fj), n in self._base_votes.get(base, {}).items()]
                    votes = [v for v in votes if v[2]['flags'][:2] == '01']
                    if votes:
                        _, tt_, f = max(votes, key=lambda v: v[0])
                        tt_ = tuple(tt_)
                        prov = 'pc_base_texture_alpha'
                    else:
                        f, prov = {'flags': '01000101', 'w14': clamp_word(dirs), 'w18': 0, 'w24': 7 if slot1 else 3, 'sorted': True}, 'rule:mesh_alpha_flag'
                else:
                    f, prov = rule_fields(dirs, tri_noise, slot1)
                self.report['tri_fields_' + prov.split(':')[0]] += 1
                attrs = [(v[0], v[1], v[2], v[3], uv1[j]) for j, v in enumerate(verts)]
                batch = self.batch_of(pos)
                tris.append((batch, tt_, f, mi, attrs, prov))
                if two_sided:
                    tris.append((batch, tt_, f, mi, [attrs[1], attrs[0], attrs[2]], prov))
        self.ps2_keys = ps2_keys
        return self.assemble(tris)

    def fit_noise(self, base, verts):
        """EXPERIMENTAL (--noise local): noise UV from the planar XZ map of the nearest PC noise triangle. On held-out PC Turkey3 vertices this
        predicts the PC noise UV exactly modulo 1 (median, p75 and p90 error 0.0 over 1,315 samples): the PC noise UV is a planar XZ projection per
        mesh. For new PS2 geometry it is still an extrapolation."""
        if not hasattr(self, '_noise_grid'):
            import collections as _c
            self._noise_tris, self._noise_grid = [], _c.defaultdict(list)
            r = self.pc
            for d in r.draws():
                t = d.texture_tuple
                if len(t) < 3 or t[2] != 'noise-tga':
                    continue
                for kk in range(d.index_start, d.index_start + d.index_count, 3):
                    vs = [d.vertex_base + r.indices[kk + j] for j in range(3)]
                    tri = ([r.positions[v] for v in vs], [r.uv_sets[1][v] for v in vs])
                    cx = sum(p[0] for p in tri[0]) / 3
                    cz = sum(p[2] for p in tri[0]) / 3
                    self._noise_grid[(int(cx // 10), int(cz // 10))].append(len(self._noise_tris))
                    self._noise_tris.append((tri, (cx, cz)))
        cx = sum(v[0][0] for v in verts) / 3
        cz = sum(v[0][2] for v in verts) / 3
        best = None
        for ring in range(0, 6):
            for dx in range(-ring, ring + 1):
                for dz in range(-ring, ring + 1):
                    if max(abs(dx), abs(dz)) != ring:
                        continue
                    for i in self._noise_grid.get((int(cx // 10) + dx, int(cz // 10) + dz), ()):
                        tri, c = self._noise_tris[i]
                        dd = math.dist(c, (cx, cz))
                        if (best is None or dd < best[0]) and _xz_map(tri) is not None:
                            best = (dd, tri)
            if best is not None:
                break
        if best is None:
            return None
        f = _xz_map(best[1])
        return [f(v[0][0], v[0][2]) for v in verts]

    def assemble(self, tris):
        r = self.pc
        positions, normals, colors, uv0, uv1, indices = [], [], bytearray(), [], [], []
        batches = [[] for _ in range(self.n_batches)]
        root_records = []
        groups = collections.defaultdict(list)
        for batch, tt_, f, mi, attrs, prov in tris:
            key = (batch, tt_, json.dumps(f, sort_keys=True), mi if f.get('sorted') else -1)
            groups[key].append(attrs)

        def emit(tri_list, tt_, f):
            """Draws (split at 65535 local vertices) for a list of triangles; returns [Draw]."""
            out = []
            start = 0
            while start < len(tri_list):
                vmap, base = {}, len(positions)
                istart = len(indices)
                k = start
                while k < len(tri_list):
                    new = [a for a in tri_list[k] if (a[0], a[1], a[2], a[3], a[4]) not in vmap]
                    if len(vmap) + len(new) > MAX_LOCAL + 1:
                        break
                    for a in tri_list[k]:
                        kk = (a[0], a[1], a[2], a[3], a[4])
                        if kk not in vmap:
                            vmap[kk] = len(vmap)
                            positions.append(a[0])
                            normals.append(a[1])
                            colors.extend(a[2])
                            uv0.append(a[3])
                            uv1.append(a[4])
                        indices.append(vmap[kk])
                    k += 1
                slots = [s.encode('ascii') for s in tt_]
                out.append(Draw(base, len(vmap) - 1, istart, len(indices) - istart, f['w14'], f['w18'], ONE, bytes.fromhex(f['flags']), f['w24'], slots))
                start = k
            return out

        for key in sorted(groups, key=lambda k: (k[0], k[1], k[2], k[3])):
            batch, tt_, fj, mi = key
            f = json.loads(fj)
            tl = groups[key]
            target = root_records if batch < 0 else batches[batch]
            if f.get('sorted'):
                target.append(self.sort_container(tl, tt_, f, emit))
                self.report['sorted_clusters'] += 1
            else:
                target.extend(emit(tl, tt_, f))
        wrappers = [x for x in r.roots if isinstance(x, Container) and x.tag == 4]
        if len(wrappers) != 1:
            raise ValueError('expected exactly one tag-4 root record')
        # control words kept, child count rewritten by the writer; every root-drawn triangle goes under it
        roots = [Container(4, wrappers[0].prefix, root_records)]
        if len(r.roots) != 1:
            self.report['root_records_merged_into_wrapper'] = len(r.roots)   # Italy_S2: one direct root draw besides the wrapper
        out = CourseRender(r.word_0x04, r.word_0x08, positions, normals, colors, [uv0, uv1], indices, roots, batches, b'')
        return out

    def sort_container(self, tl, tt_, f, emit):
        pts = [a[0] for t in tl for a in t]
        c = tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))
        rad = max(math.dist(c, p) for p in pts)
        sphere = Container(5, struct.pack('<4fI', *c, rad, 1), [])

        def tree(tl, depth=0):
            if len(tl) <= 12 or depth > 12:
                return emit(tl, tt_, f)
            a, b, cc_ = (x[0] for x in tl[0])
            n = cross(sub(b, a), sub(cc_, a))
            ln = math.sqrt(dot(n, n)) or 1.0
            n = tuple(x / ln for x in n)
            d = -dot(n, a)
            front = [t for t in tl if min(dot(n, x[0]) + d for x in t) >= -1e-3]
            back = [t for t in tl if min(dot(n, x[0]) + d for x in t) < -1e-3]
            if not front or not back:
                return emit(tl, tt_, f)
            g1 = Container(1, struct.pack('<I', 0), tree(front, depth + 1))
            g2 = Container(1, struct.pack('<I', 0), tree(back, depth + 1))
            return [Container(6, struct.pack('<4fI', *n, d, 2), [g1, g2])]
        sphere.children = tree(tl)
        return sphere


def _xz_map(tri):
    """Affine map (x, z) -> noise UV through the three vertices of a triangle, or None when its XZ projection is degenerate."""
    (a, b, c), (ua, ub, uc) = tri
    x1, z1, x2, z2 = b[0] - a[0], b[2] - a[2], c[0] - a[0], c[2] - a[2]
    det = x1 * z2 - x2 * z1
    if abs(det) < 1e-9:
        return None

    def f(x, z):
        dx, dz = x - a[0], z - a[2]
        s_ = (dx * z2 - x2 * dz) / det
        t_ = (x1 * dz - dx * z1) / det
        return (ua[0] + s_ * (ub[0] - ua[0]) + t_ * (uc[0] - ua[0]), ua[1] + s_ * (ub[1] - ua[1]) + t_ * (uc[1] - ua[1]))
    return f


def _affine(rows):
    """Least squares (u1, v1) = A (u0, v0) + t over rows [((u0, v0), (u1, v1))]; None when there are too few rows."""
    if len(rows) < 6:
        return None
    # normal equations for [u0 v0 1] -> u1 and -> v1
    import itertools
    S = [[0.0] * 3 for _ in range(3)]
    bu, bv = [0.0] * 3, [0.0] * 3
    for (u0, v0), (u1, v1) in rows:
        x = (u0, v0, 1.0)
        for i, j in itertools.product(range(3), range(3)):
            S[i][j] += x[i] * x[j]
        for i in range(3):
            bu[i] += x[i] * u1
            bv[i] += x[i] * v1

    def solve(M, y):
        M = [row[:] + [y[i]] for i, row in enumerate(M)]
        for c in range(3):
            p = max(range(c, 3), key=lambda r_: abs(M[r_][c]))
            if abs(M[p][c]) < 1e-12:
                return None
            M[c], M[p] = M[p], M[c]
            for r_ in range(3):
                if r_ != c:
                    fct = M[r_][c] / M[c][c]
                    M[r_] = [M[r_][k] - fct * M[c][k] for k in range(4)]
        return [M[i][3] / M[i][i] for i in range(3)]
    a, b = solve(S, bu), solve(S, bv)
    return None if a is None or b is None else (a[0], a[1], a[2], b[0], b[1], b[2])


def widen_1339(tag1339, positions):
    v = list(struct.unpack('<I10f', tag1339))
    ys = [p[1] for p in positions]
    lo, hi = min(ys), max(ys)
    changed = False
    if lo < v[6]:
        v[6] = lo
        changed = True
    if hi > v[9]:
        v[9] = hi
        changed = True
    if changed:
        v[2] = (v[6] + v[9]) / 2
    return struct.pack('<I10f', *v), changed


def build(course, suffix_dx, noise_mode='ps2', two_sided_mode='all'):
    b = Builder(course, noise_mode, two_sided_mode)
    render = b.build()
    sl = extract_tag100_from_dx_bytes(suffix_dx, 'suffix')
    tree, t1339, u, r1500 = io.split_suffix(sl.raw)
    t1339, widened = widen_1339(t1339, render.positions)
    render.suffix = tree + t1339 + u + r1500
    data = render.serialize()
    model = parse_course_dx_bytes(data, course.name)
    out_keys = collections.Counter()
    for d in render.draws():
        for k in range(d.index_start, d.index_start + d.index_count, 3):
            out_keys[mm.key([render.positions[d.vertex_base + render.indices[k + j]] for j in range(3)])] += 1
    ps2_keys = collections.Counter(b.ps2_keys)
    new_names = {v[0] for v in b.textures.values() if v[1] is not None}
    unresolved = collections.Counter()
    for d in render.draws():
        for s in d.texture_tuple:
            if s != 'Null' and s not in new_names and not (b.pc_dir / (s + '.dxt')).exists():
                unresolved[s] += 1
    pc_keys = set(b.pc_tris)
    report = dict(b.report)
    report['unresolved_texture_slots'] = dict(unresolved)
    report['retail_triangles_not_in_ps2'] = len(pc_keys - set(ps2_keys))
    report.update({
        'course': course.name, 'noise_mode': noise_mode, 'two_sided_mode': two_sided_mode,
        'ps2_triangles': sum(ps2_keys.values()), 'output_triangles': sum(out_keys.values()),
        'triangle_multiset_equal_ps2': out_keys == ps2_keys,
        'vertices': len(render.positions), 'retail_vertices': len(b.pc.positions), 'indices': len(render.indices), 'draws': sum(1 for _ in render.draws()),
        'retail_draws': sum(1 for _ in b.pc.draws()), 'batches': len(render.batches),
        'course_render_validated': model.course_render_validated, 'tag1339_widened': widened,
        'textures': {k: {'name': v[0], 'source': v[2]} for k, v in b.textures.items()},
        'dx_bytes': len(data), 'dx_sha256': hashlib.sha256(data).hexdigest(),
    })
    new_textures = {v[0]: v[1] for v in b.textures.values() if v[1] is not None}
    return data, new_textures, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--course', required=True)
    ap.add_argument('--suffix-from', type=Path, required=True, help='course DX whose tag100-starting suffix is used (W1 build)')
    ap.add_argument('--noise', choices=('ps2', 'plain', 'local'), default='ps2', help="'local' = EXPERIMENTAL noise UV from the nearest PC noise triangle's XZ map")
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    course = cc.course(a.course)
    data, textures, rep = build(course, a.suffix_from.read_bytes(), a.noise)
    rel = course.pc_dx.relative_to(cc.PC_ROOT)
    (a.out / rel).parent.mkdir(parents=True, exist_ok=True)
    (a.out / rel).write_bytes(data)
    for name, blob in textures.items():
        (a.out / rel.parent / (name + '.dxt')).write_bytes(blob)
    (a.out / 'render-report.json').write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if k != 'textures'}, indent=1))


if __name__ == '__main__':
    main()
