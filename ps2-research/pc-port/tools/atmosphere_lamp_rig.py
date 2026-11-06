"""ATMOSPHERE6.15 lamp rig: universal offline lamp/glint solver + simulator for car.dx vehicles.

For every car it finds the WHOLE lamp units (head, tail, brake, reverse) in car space and writes
  <out>/lamp_rigs.json          rigs the proxy loads (Atmosphere/lamps/lamp_rigs.json)
  <out>/<car>.png               front + rear + side check render (lamp texels, blight, glow card, glints)
  <out>/sheet-*.png             contact sheets

Contract (same for retail and mod cars, nothing per car hard-coded):
  * brake  = the OFF mesh of the $switch(blight) group (any texture); one glint per connected unit.
             The ON layer (breaklightson) and the glow card are only cross-checks.
  * lens draws = textures named light|lamp|indicat|*bl|lump + the blight OFF texture wherever it is reused.
  * a triangle's role comes from its texels (several samples, majority): white/bluish, red, amber, dark;
    only faces whose normal points mostly along the car axis (|nz| >= .45) in the front/rear 40 % count.
  * units = connected faces of one class (positions welded at 1 mm), then units closer than 2 cm merged.
  * head  = front white units, per side the largest + any >= 45 % of it (max 2); never outboard-small.
  * tail  = rear red units, per side the largest + any >= 45 % (max 2); a tail unit that overlaps a brake
            unit is folded into it (one glint, state decides brightness) -> no doubled glints.
  * reverse = rear white units (>= 3 cm); none -> dark rear units only when the car has no white unit.
  * glint = area-weighted centre of the unit's lens faces, placed on its outer surface (+-z extreme).
usage: PYTHONPATH=<master-rallye-re-vehicles>/src python atmosphere_lamp_rig.py OUT [--root DIR] [car ...]
"""
import sys, re, math, json, argparse
from pathlib import Path
from PIL import Image, ImageDraw
from master_rallye.dx import parse_dx
from master_rallye.dxt import parse_dxt

import os
DEBUG = bool(os.environ.get('RIG_DEBUG'))
ROLE_RGB = {'fog': (60, 255, 160), 'head': (90, 230, 255), 'tail': (255, 70, 60), 'brake': (255, 230, 0), 'reverse': (255, 255, 255)}
LENS_RE = re.compile(r'light|lamp|indicat|lump|beacon')

def lens_name(t):
    t = t.lower(); stem = t.split('-tga')[0]
    if re.search('windscreen|glass|lightson|glow|lightshine', t): return False
    return bool(LENS_RE.search(t)) or stem == 'bl' or (len(stem) == 3 and stem[1:] == 'bl')

def tclass(rgb):
    r, g, b = [c / 255 for c in rgb]; hi, lo = max(r, g, b), min(r, g, b)
    if hi < .25: return 'dark'
    sat = (hi - lo) / hi if hi else 0; h = 0
    if hi > lo:
        if hi == r: h = (60 * (g - b) / (hi - lo)) % 360
        elif hi == g: h = 60 * (b - r) / (hi - lo) + 120
        else: h = 60 * (r - g) / (hi - lo) + 240
    reddish = h >= 330 or h <= 15
    if sat < (.22 if reddish else .38): return 'white' if hi >= .45 else None
    if reddish: return 'red'
    if h <= 65: return 'amber'
    if hi >= .45: return 'blue'          # bluish headlamp glass
    return None

class Tex:
    cache = {}
    def __init__(self, root, car, name):
        self.t = None
        p = root / car / (name + '.dxt')
        if p.exists():
            try: self.t = parse_dxt(p)
            except Exception: self.t = None
    @classmethod
    def get(cls, root, car, name):
        k = (car, name)
        if k not in cls.cache: cls.cache[k] = cls(root, car, name)
        return cls.cache[k]
    def texel(self, u, v):
        t = self.t; u -= math.floor(u); v -= math.floor(v)
        x = min(t.width - 1, int(u * t.width)); y = min(t.height - 1, int(v * t.height))
        o = (y * t.width + x) * 4; b, g, r, a = t.bgra[o:o + 4]; return (r, g, b)

def raster(P, UV, tex, t):
    # every texel under triangle t: (3D position, rgb, 3D area per texel)
    T = tex.t; W, H = T.width, T.height
    uv = [(UV[v][0] * W, UV[v][1] * H) for v in t]
    (x0, y0), (x1, y1), (x2, y2) = uv
    det = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(det) < 1e-9: return []
    n, area, _ = tri_info(P, t); per = area / (abs(det) / 2)
    out = []
    for py in range(int(math.floor(min(y0, y1, y2))), int(math.ceil(max(y0, y1, y2))) + 1):
        for px in range(int(math.floor(min(x0, x1, x2))), int(math.ceil(max(x0, x1, x2))) + 1):
            cx, cy = px + .5, py + .5
            b1 = ((cx - x0) * (y2 - y0) - (x2 - x0) * (cy - y0)) / det; b2 = ((x1 - x0) * (cy - y0) - (cx - x0) * (y1 - y0)) / det; b0 = 1 - b1 - b2
            if min(b0, b1, b2) < -1e-6: continue
            pos = [b0 * P[t[0]][k] + b1 * P[t[1]][k] + b2 * P[t[2]][k] for k in range(3)]
            o = ((py % H) * W + (px % W)) * 4; b, g, r, a = T.bgra[o:o + 4]
            out.append((pos, (r, g, b), per, (py % H) * W + (px % W), (cx, cy)))
    return out

def sub(a, b): return [a[i] - b[i] for i in range(3)]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

def tri_info(P, t):
    a, b, c = (P[i] for i in t); n = cross(sub(b, a), sub(c, a)); l = math.sqrt(sum(x * x for x in n)) or 1e-12
    return [x / l for x in n], l / 2, [(a[k] + b[k] + c[k]) / 3 for k in range(3)]

def weld_components(P, tris):
    vs = sorted({v for t in tris for v in t}); parent = {v: v for v in vs}
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def join(a, b):
        a, b = find(a), find(b)
        if a != b: parent[b] = a
    for a, b, c in tris: join(a, b); join(a, c)
    order = sorted(vs, key=lambda i: P[i][0])
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            pa, pb = P[order[i]], P[order[j]]
            if pb[0] - pa[0] > .001: break
            if abs(pa[1] - pb[1]) <= .001 and abs(pa[2] - pb[2]) <= .001: join(order[i], order[j])
    parts = {}
    for t in tris: parts.setdefault(find(t[0]), []).append(t)
    return list(parts.values())

class Unit:
    def __init__(self, P, tris, cls, src):
        self.tris = list(tris); self.cls = cls; self.src = set([src]) if isinstance(src, str) else set(src)
        vs = {v for t in tris for v in t}
        self.lo = [min(P[v][k] for v in vs) for k in range(3)]; self.hi = [max(P[v][k] for v in vs) for k in range(3)]
        self.area = 0; c = [0, 0, 0]
        for t in tris:
            n, a, m = tri_info(P, t); self.area += a
            for k in range(3): c[k] += m[k] * a
        self.centre = [x / self.area for x in c] if self.area > 0 else [(self.lo[k] + self.hi[k]) / 2 for k in range(3)]
        self.nverts = len(vs)
    def face(self): return math.hypot(self.hi[0] - self.lo[0], self.hi[1] - self.lo[1])
    def gap(self, o):
        return max(max(self.lo[k] - o.hi[k], o.lo[k] - self.hi[k]) for k in range(3))
    def merge(self, P, o): return Unit(P, self.tris + o.tris, self.cls, self.src | o.src)

def merge_close(P, units, tol=.02):
    units = list(units); changed = True
    while changed:
        changed = False
        for i in range(len(units)):
            for j in range(i + 1, len(units)):
                if units[i].cls == units[j].cls and units[i].gap(units[j]) < tol and (units[i].centre[0] < 0) == (units[j].centre[0] < 0) and units[i].src == units[j].src:
                    units[i] = units[i].merge(P, units[j]); del units[j]; changed = True; break
            if changed: break
    return units

def solve(root, car):
    m = parse_dx(root / car / 'car.dx'); P = m.vertices.positions
    UV = m.uv_sets[0].values if m.uv_sets else None
    draws = m.physical_draws
    tri = lambda d: [tuple(x) for x in zip(*[iter(m.draw_global_indices(d))] * 3)]
    allv = [P[v] for d in draws for t in tri(d) for v in t]
    lo = [min(p[k] for p in allv) for k in range(3)]; hi = [max(p[k] for p in allv) for k in range(3)]
    L = hi[2] - lo[2]; front_z = hi[2] - .30 * L; rear_z = lo[2] + .30 * L
    # $switch(blight) group: records whose path is the blight record or its children
    bl = [d for d in draws if d.group_label == 'blight']
    group = set()
    for d in bl:
        base = str(d.record_path)
        for e in draws:
            if str(e.record_path) == base or str(e.record_path).startswith(base + '.'): group.add(id(e))
    on_draws = [d for d in draws if id(d) in group and re.search('lightson|glow', d.texture_tuple[0].lower())]
    off_draws = [d for d in draws if id(d) in group and d not in on_draws]
    glow_draws = [d for d in draws if 'breaklightsonglow' in d.texture_tuple[0].lower()]
    on_layer = [d for d in on_draws if 'glow' not in d.texture_tuple[0].lower()]
    report = {'car': car, 'length': round(L, 3), 'bounds': [lo, hi], 'warnings': []}
    # brake units from the OFF mesh (fallback: ON layer)
    brake_src = off_draws or on_layer
    if not off_draws: report['warnings'].append('no blight OFF mesh, brake from ON layer')
    brake_tris = [t for d in brake_src for t in tri(d)]
    brakes = merge_close(P, [Unit(P, c, 'brake', 'blight') for c in weld_components(P, brake_tris)], .03) if brake_tris else []
    # 6.15.2: lamps that exist only in the ON layer (Mattserati inner pair) are brake units too
    on_tris = [t for d in on_layer for t in tri(d)]
    if off_draws and on_tris:
        for c in weld_components(P, on_tris):
            u = Unit(P, c, 'brake', 'blighton')
            if u.area > 1e-5 and all(u.gap(b) > .03 for b in brakes): brakes.append(u)
    brakes = merge_close(P, [u for u in brakes if u.area > 1e-5], .05)
    # lens draws
    off_tex = {d.texture_tuple[0].lower() for d in off_draws}
    # the blight OFF texture is NOT a lens hint (Kangoo/Mattserati use the body livery there)
    lens = [d for d in draws if id(d) not in group and lens_name(d.texture_tuple[0])]
    faces = {}   # class -> [(tri, src)]
    tri_lum = {}; tri_src = {}
    classified = []
    for d in lens:
        name = d.texture_tuple[0].lower(); tx = Tex.get(root, car, name)
        for t in tri(d):
            n, a, c = tri_info(P, t)
            if a < 1e-7: continue
            end = 'front' if c[2] > front_z else 'rear' if c[2] < rear_z else None
            facing = abs(n[2]) >= .45
            cls = None
            if tx.t is not None and UV is not None:
                votes = {}
                for w in ((1/3, 1/3, 1/3), (.6, .2, .2), (.2, .6, .2), (.2, .2, .6)):
                    u = sum(UV[t[i]][0] * w[i] for i in range(3)); v = sum(UV[t[i]][1] * w[i] for i in range(3))
                    k = tclass(tx.texel(u, v)); votes[k] = votes.get(k, 0) + 1
                cls = max(votes, key=lambda k: (votes[k], k is not None))
            else:
                cls = 'white' if end == 'front' else 'red'
            classified.append((t, name, cls, end, facing)); tri_src[t] = name
            if tx.t is not None and UV is not None:
                lum = 0
                for w in ((1/3, 1/3, 1/3), (.6, .2, .2), (.2, .6, .2), (.2, .2, .6)):
                    u = sum(UV[t[i]][0] * w[i] for i in range(3)); v = sum(UV[t[i]][1] * w[i] for i in range(3))
                    r_, g_, b_ = tx.texel(u, v); lum += (.3 * r_ + .59 * g_ + .11 * b_) / 255 / 4
                tri_lum[t] = lum
            if end and facing and cls:
                key = (end, 'white' if cls in ('white', 'blue') else cls)
                faces.setdefault(key, []).append((t, name))
    def units_for(key):
        items = faces.get(key, []); out = []
        by_src = {}
        for t, s in items:
            cx = tri_info(P, t)[2][0]   # never weld lamps across the car's centre line
            by_src.setdefault((s, 'L' if cx < -.08 else 'R' if cx > .08 else 'C'), []).append(t)
        for s, ts in by_src.items():
            for c in weld_components(P, ts): out.append(Unit(P, c, key[1], s[0]))
        units = [u for u in merge_close(P, out) if u.nverts >= 3 and .03 <= u.face() <= .8]
        units = merge_stacked(units)
        return [u for u in units if exposed(u, key[0])]
    side = lambda u: 0 if u.centre[0] < 0 else 1
    def merge_stacked(units):
        # double-layer lenses (reflector + outer glass): same class, footprints overlap >= 50 %
        units = list(units); changed = True
        def xy_share(a, b):
            ix = min(a.hi[0], b.hi[0]) - max(a.lo[0], b.lo[0]); iy = min(a.hi[1], b.hi[1]) - max(a.lo[1], b.lo[1])
            if ix <= 0 or iy <= 0: return 0
            sa = max(1e-6, (a.hi[0] - a.lo[0]) * (a.hi[1] - a.lo[1])); sb = max(1e-6, (b.hi[0] - b.lo[0]) * (b.hi[1] - b.lo[1]))
            return ix * iy / min(sa, sb)
        while changed:
            changed = False
            for i in range(len(units)):
                for j in range(i + 1, len(units)):
                    if units[i].cls == units[j].cls and abs(units[i].centre[2] - units[j].centre[2]) < .25 and xy_share(units[i], units[j]) >= .5:
                        units[i] = units[i].merge(P, units[j]); del units[j]; changed = True; break
                if changed: break
        return units
    body_tris = [t for d in draws if d not in lens and id(d) not in group and 'glow' not in d.texture_tuple[0].lower()
                 and not re.search('windscreen|glass|perspex', d.texture_tuple[0].lower()) for t in tri(d)]
    body_box = [(t, [min(P[v][k] for v in t) for k in range(3)], [max(P[v][k] for v in t) for k in range(3)]) for t in body_tris]
    def ray_hits(o, dz):
        # Moller-Trumbore along +-z from o; returns nearest hit distance
        best = None
        for t, blo, bhi in body_box:
            if not (blo[0] <= o[0] <= bhi[0] and blo[1] <= o[1] <= bhi[1]): continue
            if dz > 0 and bhi[2] < o[2] or dz < 0 and blo[2] > o[2]: continue
            a, b, c = (P[v] for v in t); e1 = sub(b, a); e2 = sub(c, a); d = [0, 0, dz]
            pv = cross(d, e2); det = sum(e1[k] * pv[k] for k in range(3))
            if abs(det) < 1e-12: continue
            inv = 1 / det; tv = sub(o, a); u = sum(tv[k] * pv[k] for k in range(3)) * inv
            if u < 0 or u > 1: continue
            qv = cross(tv, e1); v = sum(d[k] * qv[k] for k in range(3)) * inv
            if v < 0 or u + v > 1: continue
            dist = sum(e2[k] * qv[k] for k in range(3)) * inv
            if dist > 1e-4 and (best is None or dist < best): best = dist
        return best
    def exposed(u, end):
        # a lamp unit is seen from its end: its outer centre is not covered by body faces further out (>8 cm)
        dz = 1 if end == 'front' else -1
        o = [u.centre[0], u.centre[1], u.hi[2] if dz > 0 else u.lo[2]]
        # 9 rays over the unit's footprint (grille tubes / bull bars may cover a few); >= 1/3 clear
        clear = 0
        for fx in (.25, .5, .75):
            for fy in (.25, .5, .75):
                q = [u.lo[0] + fx * (u.hi[0] - u.lo[0]), u.lo[1] + fy * (u.hi[1] - u.lo[1]), o[2]]
                h = ray_hits(q, dz); clear += h is None or h < .08
        u.exposure = clear / 9
        if DEBUG: print('   unit', end, u.cls, [round(x, 2) for x in u.centre], 'area', round(u.area, 4), 'exposed', clear, '/9', sorted(u.src))
        return clear >= 3
    def pick(units, share, cap, drop_outboard):
        keep = []
        for s in (0, 1):
            us = sorted([u for u in units if side(u) == s], key=lambda u: -u.area)
            if not us: continue
            top = us[0]; edge = max(abs(top.lo[0]), abs(top.hi[0]))
            sel = [top]
            for u in us[1:]:
                if len(sel) >= cap or u.area < share * top.area: continue
                if drop_outboard and abs(u.centre[0]) > edge - .03 and u.area < .6 * top.area: continue
                sel.append(u)
            keep += sel
        return keep
    front_units = units_for(('front', 'white'))
    heads = pick(front_units, .45, 2, True)
    # fog / auxiliary lamps: other exposed front white units >= 12 % of the side's main lamp, not touching a head
    fogs = []
    # a second 'head' on a side that is clearly lower/smaller than the main lamp is an auxiliary (fog) lamp
    for s_ in (0, 1):
        hs = sorted([u for u in heads if side(u) == s_], key=lambda u: -u.area)
        for u in hs[1:]:
            if u.area < .7 * hs[0].area or abs(u.centre[1] - hs[0].centre[1]) > .12:
                heads.remove(u); fogs.append(u)
    for s_ in (0, 1):
        hs = [u for u in heads if side(u) == s_]
        if not hs: continue
        top = max(u.area for u in hs)
        cand = sorted([u for u in front_units if side(u) == s_ and u not in heads and u not in fogs and u.area >= .12 * top
                       and all(u.gap(h) > 0 for h in hs)], key=lambda u: -u.area)
        fogs += cand[:3]
    # indicators are amber lenses with a white rim: amber area inside the unit's box > white area -> no fog
    amber = [t for t, _ in faces.get(('front', 'amber'), [])]
    def amber_area(u):
        return sum(tri_info(P, t)[1] for t in amber if all(u.lo[k] - .02 <= tri_info(P, t)[2][k] <= u.hi[k] + .02 for k in range(3)))
    fogs = [u for u in fogs if amber_area(u) <= u.area]
    # corner indicators / side lights: outboard of the side's main lamp and right next to it (Terrano, Pajero, Xtrail)
    def corner(u):
        for h in heads:
            if side(h) != side(u): continue
            edge = max(abs(h.lo[0]), abs(h.hi[0]))
            if abs(u.centre[0]) > edge - .03 and u.gap(h) < .06: return True
        return False
    fogs = [u for u in fogs if not corner(u)]
    # auxiliary lamps come in mirrored pairs (or sit on the centre line): a lone one is dropped, a missing twin added
    def twin(u, pool):
        for o in pool:
            if o is not u and abs(o.centre[0] + u.centre[0]) < .08 and abs(o.centre[1] - u.centre[1]) < .04 and abs(o.centre[2] - u.centre[2]) < .08: return o
        return None
    paired = []
    for u in fogs:
        if abs(u.centre[0]) < .05: paired.append(u); continue
        o = twin(u, fogs) or twin(u, [x for x in front_units if x not in heads and amber_area(x) <= x.area and not corner(x)])
        if o is not None:
            for x in (u, o):
                if x not in paired: paired.append(x)
    fogs = paired
    tails = pick(units_for(('rear', 'red')), .45, 2, False)
    whites = [u for u in units_for(('rear', 'white')) if u.face() >= .03]
    reverse = pick(whites, .45, 1, False)
    if not reverse:
        # 6.15.2: white sections smaller than one triangle (Bruno, megane): classify texels, not triangles
        texel_rev = []
        for t, name, cls, end, facing in classified:
            if end != 'rear' or not facing: continue
            tx = Tex.get(root, car, name)
            if tx.t is None or UV is None: continue
            for pos, rgb, per, *_ in raster(P, UV, tx, t):
                if tclass(rgb) == 'white': texel_rev.append((pos, per))
        for s_ in (0, 1):
            pts_ = [q for q in texel_rev if (q[0][0] < 0) == (s_ == 0)]
            clusters = []
            for pos, per in pts_:
                for cl in clusters:
                    if any(abs(pos[0] - o[0][0]) < .04 and abs(pos[1] - o[0][1]) < .04 and abs(pos[2] - o[0][2]) < .06 for o in cl[-40:]): cl.append((pos, per)); break
                else: clusters.append([(pos, per)])
            if not clusters: continue
            best = max(clusters, key=lambda cl: sum(q[1] for q in cl)); a_ = sum(q[1] for q in best)
            if a_ < 4e-4: continue
            cen = [sum(q[0][k] * q[1] for q in best) / a_ for k in range(3)]
            reverse.append(('texel', cen, a_, min(q[0][2] for q in best)))
        if reverse: report['warnings'].append('reverse from lens texels')
    if not reverse:
        darks = units_for(('rear', 'dark'))
        if darks: reverse = pick(darks, .45, 1, False); [setattr(u, 'cls', 'dark') for u in reverse]
        report['warnings'].append('reverse from dark lens' if darks else 'no reverse lamp in the model: synthetic at the brake units')
        if not darks:
            reverse = []
            for s_ in (0, 1):
                bs = [b for b in brakes if side(b) == s_]
                if bs: b = max(bs, key=lambda b: b.area); reverse.append(('synthetic', b.centre, b.area * .4, b.lo[2]))
    # fold tails overlapping a brake unit into it
    def overlaps(a, b, tol=.04):
        return all(not (a.lo[k] > b.hi[k] + tol or b.lo[k] > a.hi[k] + tol) for k in (0, 1))
    tail_pts = []
    for u in tails:
        hit = [b for b in brakes if overlaps(u, b, .12)]
        if hit: hit[0].tail = True
        else: tail_pts.append(u)   # 6.15.2: a separate red lamp keeps its own tail glint (Mattserati, Astero pillars)
    for b in brakes: b.tail = True   # the blight OFF lens is the rear lamp at night (tail glint), brighter while braking
    def point(u, role, end):
        if role in ('head', 'fog'):
            # glint at the lamp's drawn detail: texels weighted by |luminance - median of the lens|^2 (bulb, ring,
            # reflector lines stand out of a flat glass/background), texel-exact through the UV raster
            tx_ = []
            for t in u.tris:
                tx = Tex.get(root, car, tri_src.get(t, ''))
                if tx.t is not None and UV is not None: tx_ += raster(P, UV, tx, t)
            sw = 0; c = [0, 0, 0]
            if tx_:
                lums = sorted(.3 * q[1][0] + .59 * q[1][1] + .11 * q[1][2] for q in tx_); med = lums[len(lums) // 2]
                for pos, rgb, per, *_ in tx_:
                    w_ = per * ((.3 * rgb[0] + .59 * rgb[1] + .11 * rgb[2] - med) / 255) ** 2
                    sw += w_; c = [c[k] + pos[k] * w_ for k in range(3)]
            if sw > 1e-9:
                bc = [c[k] / sw for k in range(3)]
                # stay inside the lens footprint
                u.centre = [min(max(bc[0], u.lo[0]), u.hi[0]), min(max(bc[1], u.lo[1]), u.hi[1]), bc[2]]
        z = u.hi[2] if end == 'front' else u.lo[2]
        # outer surface at the centre: max/min z of faces whose xy box contains the centre
        cz = None
        for t in u.tris:
            xs = [P[v][0] for v in t]; ys = [P[v][1] for v in t]
            if min(xs) - .005 <= u.centre[0] <= max(xs) + .005 and min(ys) - .005 <= u.centre[1] <= max(ys) + .005:
                zz = sum(P[v][2] for v in t) / 3
                cz = zz if cz is None else (max(cz, zz) if end == 'front' else min(cz, zz))
        z = cz if cz is not None else u.centre[2]
        return {'role': role, 'side': 'L' if u.centre[0] < 0 else 'R', 'pos': [round(u.centre[0], 4), round(u.centre[1], 4), round(z, 4)],
                'size': round(math.sqrt(u.area), 4), 'extent': [round(u.hi[k] - u.lo[k], 4) for k in range(3)],
                'also_tail': bool(getattr(u, 'tail', False)), 'sources': sorted(u.src), 'class': u.cls}
    pts = [point(u, 'head', 'front') for u in heads] + [point(u, 'fog', 'front') for u in fogs] + [point(u, 'tail', 'rear') for u in tail_pts] + \
          [point(u, 'brake', 'rear') for u in brakes] + [point(u, 'reverse', 'rear') if not isinstance(u, tuple) else
          {'role': 'reverse', 'side': 'L' if u[1][0] < 0 else 'R', 'pos': [round(u[1][0], 4), round(u[1][1], 4), round(u[3], 4)], 'size': round(math.sqrt(u[2]), 4),
           'extent': [0, 0, 0], 'also_tail': False, 'sources': [u[0]], 'class': u[0]} for u in reverse]
    if not heads: report['warnings'].append('no headlight')
    if not brakes: report['warnings'].append('no brake unit')
    for s in 'LR':
        if not any(p['role'] == 'head' and p['side'] == s for p in pts): report['warnings'].append(f'no head on {s}')
        if not any(p['role'] in ('brake', 'tail') and p['side'] == s for p in pts): report['warnings'].append(f'no tail/brake on {s}')
    # 6.16 night lens textures: only the lamp's working area stays emissive. Texels under lens faces at the car's
    # ends whose own class is white/blue/red are lamp; amber (indicators), dark, stickers and body texels are not.
    # A head/fog unit whose drawn lamp (bulb, ring, reflector) is clearly smaller than its glass (Navara fog quad)
    # is cut to the ellipse around those features.
    masks = {}
    def mask_of(name):
        tx = Tex.get(root, car, name)
        if tx.t is None: return None
        if name not in masks: masks[name] = [0.0] * (tx.t.width * tx.t.height)
        return masks[name]
    cover = {}
    for t, name, cls, end, facing in classified:
        if end is None or UV is None: continue
        m_ = mask_of(name)
        if m_ is None: continue
        for pos, rgb, per, idx, _ in raster(P, UV, Tex.get(root, car, name), t):
            k = tclass(rgb); cover.setdefault(name, set()).add(idx)
            # everything under the lamp glass glows, except indicators (amber) and red print at the front
            if k != 'amber' and not (end == 'front' and k == 'red'): m_[idx] = 1.0
    for d in off_draws:   # the blight OFF lens keeps its texels too (same texture may be shared with a lens draw)
        name = d.texture_tuple[0].lower(); m_ = mask_of(name) if lens_name(name) else None
        if m_ is None or UV is None: continue
        for t in tri(d):
            for pos, rgb, per, idx, _ in raster(P, UV, Tex.get(root, car, name), t):
                if tclass(rgb) != 'amber': m_[idx] = 1.0; cover.setdefault(name, set()).add(idx)
    # stickers / paint printed around the glass: flat bright texels connected to the edge of the covered area
    for name, cov in cover.items():
        T = Tex.get(root, car, name).t; W, H = T.width, T.height; m_ = masks[name]
        L = lambda i: .3 * T.bgra[i * 4 + 2] + .59 * T.bgra[i * 4 + 1] + .11 * T.bgra[i * 4]
        def nb(i):
            x, y = i % W, i // W
            return [((y + dy) % H) * W + (x + dx) % W for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        flat = set()
        for i in cov:
            x, y = i % W, i // W; ls = [L(((y + dy) % H) * W + (x + dx) % W) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            if max(ls) - min(ls) < 14 and L(i) > 150: flat.add(i)
        seeds = [i for i in flat if any(j not in cov for j in nb(i))]
        seen = set(seeds)
        while seeds:
            i = seeds.pop()
            for j in nb(i):
                if j in flat and j not in seen: seen.add(j); seeds.append(j)
        if len(seen) < .6 * len(cov):
            for i in seen: m_[i] = 0.0
        report.setdefault('mask_cuts', []).append({'texture': name, 'flat_edge_cut': len(seen)}) if seen else None
    report.setdefault('mask_cuts', [])
    for u in heads + fogs:
        by_tex = {}
        for t in u.tris:
            name = tri_src.get(t)
            if name and UV is not None and Tex.get(root, car, name).t is not None: by_tex.setdefault(name, []).extend(raster(P, UV, Tex.get(root, car, name), t))
        for name, tx_ in by_tex.items():
            if len(tx_) < 24: continue
            lum = lambda q: .3 * q[1][0] + .59 * q[1][1] + .11 * q[1][2]
            ls = sorted(lum(q) for q in tx_); med = ls[len(ls) // 2]
            feat = [q for q in tx_ if abs(lum(q) - med) > 46]
            if len(feat) < 8: continue
            mx = sum(q[4][0] for q in feat) / len(feat); my = sum(q[4][1] for q in feat) / len(feat)
            sxx = sum((q[4][0] - mx) ** 2 for q in feat) / len(feat); syy = sum((q[4][1] - my) ** 2 for q in feat) / len(feat)
            sxy = sum((q[4][0] - mx) * (q[4][1] - my) for q in feat) / len(feat); det = sxx * syy - sxy * sxy
            if det <= 1e-6: continue
            ixx, iyy, ixy = syy / det, sxx / det, -sxy / det
            d2 = lambda q: ixx * (q[4][0] - mx) ** 2 + 2 * ixy * (q[4][0] - mx) * (q[4][1] - my) + iyy * (q[4][1] - my) ** 2
            r2 = sorted(d2(q) for q in feat)[int(.95 * (len(feat) - 1))] * 1.25
            area = math.pi * math.sqrt(det) * r2
            if area >= .7 * len(set(q[3] for q in tx_)): continue
            m_ = masks.get(name)
            cut = 0
            for q in tx_:
                if d2(q) > r2 and m_[q[3]] > 0: m_[q[3]] = 0.0; cut += 1
            report['mask_cuts'].append({'texture': name, 'texels_cut': cut, 'ellipse_texels': round(area)})
    report['masks'] = masks
    # runtime fingerprints of the lens draws (texture, vertex count, car-space bounds)
    fps = []
    for d in lens + off_draws + on_layer + glow_draws:
        vs = sorted({v for t in tri(d) for v in t})
        vr = d.vertex_range; rv = [P[i] for i in range(vr[0], vr[1] + 1)] if vr else [P[v] for v in vs]
        fps.append({'texture': d.texture_tuple[0].lower(), 'record': str(d.record_path), 'vertices': len(vs), 'triangles': len(tri(d)),
                    'range_vertices': len(rv), 'range_lo': [round(min(q[k] for q in rv), 3) for k in range(3)], 'range_hi': [round(max(q[k] for q in rv), 3) for k in range(3)],
                    'lo': [round(min(P[v][k] for v in vs), 3) for k in range(3)], 'hi': [round(max(P[v][k] for v in vs), 3) for k in range(3)],
                    'kind': 'brake_off' if d in off_draws else 'brake_on' if d in on_layer else 'glow' if d in glow_draws else 'lens'})
    report['points'] = pts; report['draws'] = fps
    ctx = dict(m=m, P=P, draws=draws, tri=tri, lens=lens, classified=classified, brakes=brakes, glow=glow_draws, on=on_layer, lo=lo, hi=hi)
    return report, ctx

def render(root, car, report, ctx, path):
    P = ctx['P']; lo, hi = ctx['lo'], ctx['hi']
    W, H = 1500, 560
    span = max(hi[0] - lo[0], hi[1] - lo[1], 1.0); S = min(420 / span, 230)
    img = Image.new('RGB', (W, H), (16, 16, 22)); dr = ImageDraw.Draw(img)
    views = [('front', 250), ('rear', 750), ('side', 1240)]
    def proj(p, view, ox):
        if view == 'front': x = -p[0]
        elif view == 'rear': x = p[0]
        else:
            Sz = min(S, 520 / max(1e-3, hi[2] - lo[2])); return (ox + (p[2] - (lo[2] + hi[2]) / 2) * Sz, H - 40 - (p[1] - lo[1]) * Sz)
        return (ox + x * S, H - 40 - (p[1] - lo[1]) * S)
    body = [t for d in ctx['draws'] for t in ctx['tri'](d) if d not in ctx['lens'] and 'glow' not in d.texture_tuple[0].lower()]
    for view, ox in views:
        key = (lambda t: sum(P[v][2] for v in t)) if view == 'front' else (lambda t: -sum(P[v][2] for v in t)) if view == 'rear' else (lambda t: -sum(P[v][0] for v in t))
        for t in sorted(body, key=key):
            n, a, c = tri_info(P, t); sh = int(40 + 45 * abs(n[2] if view != 'side' else n[0]))
            dr.polygon([proj(P[v], view, ox) for v in t], fill=(sh, sh, sh + 6))
        lens = sorted(ctx['classified'], key=lambda x: key(x[0]))
        for t, name, cls, end, facing in lens:
            if view == 'front' and end != 'front' or view == 'rear' and end != 'rear': continue
            tx = Tex.get(root, car, name); col = (150, 150, 150)
            if tx.t is not None and ctx['m'].uv_sets:
                UV = ctx['m'].uv_sets[0].values; u = sum(UV[v][0] for v in t) / 3; vv = sum(UV[v][1] for v in t) / 3; col = tx.texel(u, vv)
            dr.polygon([proj(P[v], view, ox) for v in t], fill=col, outline=(70, 70, 90) if facing else (120, 40, 120))
        if view != 'front':
            for b in ctx['brakes']:
                for t in b.tris: dr.polygon([proj(P[v], view, ox) for v in t], outline=(0, 255, 90))
            for d in ctx['glow']:
                for t in ctx['tri'](d):
                    q = [proj(P[v], view, ox) for v in t]; dr.line(q + [q[0]], fill=(110, 110, 0))
        for p in report['points']:
            if view == 'front' and p['role'] not in ('head', 'fog') or view == 'rear' and p['role'] in ('head', 'fog'): continue
            x, y = proj(p['pos'], view, ox); r = 7 if p['role'] != 'reverse' else 5
            dr.ellipse((x - r, y - r, x + r, y + r), outline=ROLE_RGB[p['role']], width=3)
            if p.get('also_tail'): dr.ellipse((x - r - 4, y - r - 4, x + r + 4, y + r + 4), outline=ROLE_RGB['tail'], width=2)
        dr.text((ox - 60, 12), view, fill=(220, 220, 220))
    dr.text((10, H - 22), f"{car}  cyan=head  green=fog/aux  red=tail  yellow=brake (blight OFF unit, green outline; red ring = tail folded in)  white=reverse  olive=glow card  magenta edge=lens face not facing the axis   "
            + '; '.join(report['warnings']), fill=(230, 230, 230))
    img.save(path)
    return img

NIGHT_DIM = .3
def write_masks(root, rigs, out):
    import struct
    for car, r in rigs.items():
        r['mask_files'] = {}
        for name, m in (r.pop('masks', None) or {}).items():
            tx = Tex.get(root, car, name).t
            if tx is None or not any(m): continue
            W, H = tx.width, tx.height
            sm = [0.0] * (W * H)   # 3x3 soft edge
            for y in range(H):
                for x in range(W):
                    acc = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1): acc += m[((y + dy) % H) * W + (x + dx) % W]
                    sm[y * W + x] = max(m[y * W + x] * .75, acc / 9)
            px = bytearray(tx.bgra)
            for i in range(W * H):
                k = NIGHT_DIM + (1 - NIGHT_DIM) * min(1.0, sm[i])
                for c in range(3): px[i * 4 + c] = int(px[i * 4 + c] * k + .5)
            rel = f'lamp_masks/{car}/{name}.dxt'; path = out / rel; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(struct.pack('<5I', 0xfeed, 0, 0, W, H) + bytes(px))
            prev = Image.frombytes('RGBA', (W, H), bytes(px), 'raw', 'BGRA').convert('RGB')
            orig = Image.frombytes('RGBA', (W, H), bytes(tx.bgra), 'raw', 'BGRA').convert('RGB')
            pv = Image.new('RGB', (W * 2 + 4, H)); pv.paste(orig, (0, 0)); pv.paste(prev, (W + 4, 0)); pv.save(path.with_suffix('.png'))
            r['mask_files'][name] = rel

ROLE_ID = {'head': 0, 'tail': 1, 'brake': 2, 'reverse': 3, 'fog': 4}
def write_txt(rigs, path):
    # proxy format (renderer/atmosphere_headlights.hpp read_lamp_rigs): car-space metres, z = forward
    lines = ['# ATMOSPHERE6.15 lamp rigs, generated by tools/atmosphere_lamp_rig.py - do not edit by hand',
             '# car <name> | draw <texture> <vertices> lo.x lo.y lo.z hi.x hi.y hi.z | off <range vertices> lo hi (blight OFF lens) | point <role> x y z size tail(0/1) dark(0/1)']
    for car, r in rigs.items():
        if not r['points']: continue
        lines.append(f'car {car}')
        for d in r['draws']:
            if d['kind'] != 'lens': continue
            lines.append('draw {} {} {}'.format(d['texture'], d['vertices'], ' '.join(f'{x:.3f}' for x in d['lo'] + d['hi'])))
        for name, rel in sorted(r.get('mask_files', {}).items()):
            lines.append(f'mask {name} {rel}')
        for d in r['draws']:
            if d['kind'] == 'brake_off':
                lines.append('off {} {}'.format(d['range_vertices'], ' '.join(f'{x:.3f}' for x in d['range_lo'] + d['range_hi'])))
        for q in r['points']:
            lines.append('point {} {:.4f} {:.4f} {:.4f} {:.3f} {} {}'.format(ROLE_ID[q['role']], *q['pos'], q['size'], int(q['also_tail']), int(q['class'] == 'dark')))
    path.write_text(chr(10).join(lines) + chr(10))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--root', default=r'D:/Game/Master Rallye/Data.sma_unpacked/DataGx/Vehicles')
    ap.add_argument('cars', nargs='*'); a = ap.parse_args()
    root = Path(a.root); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    cars = a.cars or sorted(p.name for p in root.iterdir() if (p / 'car.dx').exists())
    rigs = {}; imgs = []
    for car in cars:
        try: rep, ctx = solve(root, car)
        except Exception as e: print(car, 'ERR', repr(e)); continue
        rigs[car] = rep; imgs.append(render(root, car, rep, ctx, out / f'{car}.png'))
        roles = {}
        for p in rep['points']: roles[p['role']] = roles.get(p['role'], 0) + 1
        print(f"{car:13} {roles} {'; '.join(rep['warnings'])}")
        for p in rep['points']: print(f"    {p['role']:7} {p['side']} pos={p['pos']} size={p['size']} tail={p['also_tail']} {p['sources']} {p['class']}")
    for i in range(0, len(imgs), 4):
        sheet = Image.new('RGB', (1500, 560 * len(imgs[i:i + 4])))
        for j, im in enumerate(imgs[i:i + 4]): sheet.paste(im, (0, 560 * j))
        sheet.save(out / f'sheet-{i // 4 + 1}.png')
    write_masks(root, rigs, out)
    write_txt(rigs, out / 'lamp_rigs.txt')
    (out / 'lamp_rigs.json').write_text(json.dumps({'version': 1, 'generator': 'atmosphere_lamp_rig.py 6.15', 'cars': rigs}, indent=1))

if __name__ == '__main__':
    main()
