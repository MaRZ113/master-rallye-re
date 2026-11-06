"""ATMOSPHERE6.13 offline simulation of the proxy lamp-lens glint roles over retail car.dx files.
usage: PYTHONPATH=<master-rallye-re-vehicles>/src python atmosphere_lamp_glint_sim.py OUTDIR [car ...]  (ALGO=613 default)"""
import sys, re, math
from pathlib import Path
from PIL import Image, ImageDraw
from master_rallye.dx import parse_dx
from master_rallye.dxt import parse_dxt

ROOT = Path(r'D:/Game/Master Rallye/Data.sma_unpacked/DataGx/Vehicles')
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
cars = sys.argv[2:] or sorted(p.name for p in ROOT.iterdir() if (p / 'car.dx').exists())

def is_lamp_name(t):
    return bool(re.search('light|lamp', t)) and not re.search('windscreen|glass', t)

def excluded(names):
    return any(('lightson' in n or 'glow' in n) for n in names)

def components(P, tris):
    vs = sorted({v for t in tris for v in t})
    parent = {v: v for v in vs}
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
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
    for t in tris:
        r = find(t[0]); parts.setdefault(r, []).append(t)
    return list(parts.values())

def bbox(P, tris):
    vs = {v for t in tris for v in t}
    lo = [min(P[v][k] for v in vs) for k in range(3)]; hi = [max(P[v][k] for v in vs) for k in range(3)]
    return lo, hi, len(vs)

def tex_of(car, name):
    p = ROOT / car / (name + '.dxt')
    if not p.exists(): return None
    t = parse_dxt(p); return t

def texel(t, u, v):
    u -= math.floor(u); v -= math.floor(v)
    x = min(t.width - 1, int(u * t.width)); y = min(t.height - 1, int(v * t.height))
    o = (y * t.width + x) * 4; b, g, r, a = t.bgra[o:o + 4]; return r, g, b

def simulate(car, algo):
    m = parse_dx(ROOT / car / 'car.dx'); P = m.vertices.positions; UV = m.uv_sets[0].values if m.uv_sets else None
    draws = m.physical_draws
    glow = [d for d in draws if 'breaklightsonglow' in d.texture_tuple[0].lower()]
    brake_local = None
    if glow:
        vs = sorted(set(m.draw_global_indices(glow[0])))
        brake_local = [sum(P[v][k] for v in vs) / len(vs) for k in range(3)]
        glow_box = ([min(P[v][k] for v in vs) for k in range(3)], [max(P[v][k] for v in vs) for k in range(3)])
    else: glow_box = None
    brake_boxes = []
    for d in draws:
        t0 = d.texture_tuple[0].lower()
        if 'breaklightson' in t0 and 'glow' not in t0:
            g = m.draw_global_indices(d); tris = [tuple(g[i:i + 3]) for i in range(0, len(g) - 2, 3)]
            for comp in components(P, tris):
                lo, hi, n = bbox(P, comp); brake_boxes.append((lo, hi))
    def inside_share(vs):
        if not brake_boxes: return 0
        k_in = sum(1 for v in vs if any(all(b[0][k]-.03 <= P[v][k] <= b[1][k]+.03 for k in range(3)) for b in brake_boxes))
        return k_in / len(vs)
    lamps = []
    for d in draws:
        names = [n.lower() for n in d.texture_tuple]
        if excluded(names): continue
        g = m.draw_global_indices(d); tris = [tuple(g[i:i + 3]) for i in range(0, len(g) - 2, 3)]
        if not tris: continue
        vs = sorted({v for t in tris for v in t}); c = [sum(P[v][k] for v in vs) / len(vs) for k in range(3)]
        lamp = is_lamp_name(names[0])
        brake_zone = False
        lo3 = [min(P[v][k] for v in vs) for k in range(3)]; hi3 = [max(P[v][k] for v in vs) for k in range(3)]
        if not lamp and inside_share(vs) >= .5:
            lamp = brake_zone = True
        if lamp: lamps.append(dict(draw=d, tris=tris, names=names, brake_zone=brake_zone, label=d.group_label))
    return m, P, UV, lamps, brake_local, algo(P, UV, lamps, car, brake_boxes)

def algo_612(P, UV, lamps, car, glow_box=None):
    pts = []
    for L in lamps:
        parts = []
        for comp in components(P, L['tris']):
            lo, hi, n = bbox(P, comp); parts.append([lo, hi, n, True])
        merged = True
        while merged:
            merged = False
            for a in parts:
                for b in parts:
                    if a is b or not a[3] or not b[3]: continue
                    if all(not (a[0][k] > b[1][k] + .02 or b[0][k] > a[1][k] + .02) for k in range(3)):
                        for k in range(3): a[0][k] = min(a[0][k], b[0][k]); a[1][k] = max(a[1][k], b[1][k])
                        a[2] += b[2]; b[3] = False; merged = True
        live = [p for p in parts if p[3] and p[2] >= 3]
        quad = lambda p: (0 if (p[0][0] + p[1][0]) < 0 else 1) + (2 if (p[0][2] + p[1][2]) < 0 else 0)
        ext = lambda p: math.hypot(p[1][0] - p[0][0], p[1][1] - p[0][1])
        largest = {}
        for p in live: largest[quad(p)] = max(largest.get(quad(p), 0), ext(p))
        for p in live:
            if ext(p) < .5 * largest[quad(p)]: continue
            cz = (p[0][2] + p[1][2]) / 2
            if abs(cz) < 1.2: continue
            z = p[1][2] if abs(p[1][2]) > abs(p[0][2]) else p[0][2]
            pts.append(dict(x=(p[0][0] + p[1][0]) / 2, y=(p[0][1] + p[1][1]) / 2, z=z, front=z > 0, src=L['names'][0], kind='brake' if L['brake_zone'] else 'lamp'))
    return pts


def tclass(rgb):
    r,g,b=[c/255 for c in rgb];hi,lo=max(r,g,b),min(r,g,b);v=hi;sat=0 if hi==0 else (hi-lo)/hi
    if v<.25: return None
    if hi==lo: h=0
    elif hi==r: h=60*((g-b)/(hi-lo))%360
    elif hi==g: h=60*((b-r)/(hi-lo))+120
    else: h=60*((r-g)/(hi-lo))+240
    reddish=h>=330 or h<=15
    if sat<(.22 if reddish else .38): return 'white' if v>=.45 else None
    if reddish: return 'red'
    if h<=65: return 'amber'
    return None

def algo_613(P, UV, lamps, car, glow_box=None):
    pts=[]
    for L in lamps:
        t=None
        try: t=tex_of(car, L['names'][0])
        except Exception: pass
        if t is None or UV is None: continue
        cls={}
        for tri in L['tris']:
            u=sum(UV[v][0] for v in tri)/3; vv=sum(UV[v][1] for v in tri)/3; cls[tri]=tclass(texel(t,u,vv))
        for c in (('red',) if L['brake_zone'] else ('white','red')):
            tris=[tri for tri in L['tris'] if cls[tri]==c]
            if not tris: continue
            for comp in components(P,tris):
                lo,hi,n=bbox(P,comp)
                cz=(lo[2]+hi[2])/2
                if abs(cz)<1.2 or n<4: continue
                if math.hypot(hi[0]-lo[0],hi[1]-lo[1])<.05: continue
                front=cz>0
                if front and c!='white': continue
                z=hi[2] if abs(hi[2])>abs(lo[2]) else lo[2]
                x=(lo[0]+hi[0])/2;y=(lo[1]+hi[1])/2
                if front: kind='head'
                elif c=='white': kind='reverse'
                else:
                    area=max(1e-6,(hi[0]-lo[0])*(hi[1]-lo[1]));best=0
                    for bb in (glow_box or []):
                        if lo[2]>bb[1][2]+.05 or hi[2]<bb[0][2]-.05: continue
                        ix=min(hi[0],bb[1][0]+.01)-max(lo[0],bb[0][0]-.01);iy=min(hi[1],bb[1][1]+.01)-max(lo[1],bb[0][1]-.01)
                        if ix>0 and iy>0: best=max(best,ix*iy/area)
                    inside=best>=.5
                    kind='brake' if inside else 'tail'
                if any(q['kind']==kind and abs(q['x']-x)<.05 and abs(q['y']-y)<.05 and abs(q['z']-z)<.08 for q in pts): continue
                pts.append(dict(x=x,y=y,z=z,front=front,src=L['names'][0],kind=kind))
    return pts

ALGOS = {'612': algo_612, '613': algo_613}

def render(car, P, UV, lamps, pts, path, front):
    W, H, S = 700, 520, 220.0
    img = Image.new('RGB', (W, H), (20, 20, 28)); dr = ImageDraw.Draw(img)
    def proj(p):  # view from outside: front view mirrors x
        x = -p[0] if front else p[0]
        return (W / 2 + x * S, H - 30 - p[1] * S)
    for L in lamps:
        t = None
        try: t = tex_of(car, L['names'][0])
        except Exception: pass
        for tri in L['tris']:
            zs = [P[v][2] for v in tri]
            if front and not all(z > 0.8 for z in zs): continue
            if not front and not all(z < -0.8 for z in zs): continue
            col = (200, 200, 200)
            if t and UV:
                u = sum(UV[v][0] for v in tri) / 3; vv = sum(UV[v][1] for v in tri) / 3; col = texel(t, u, vv)
            dr.polygon([proj(P[v]) for v in tri], fill=col, outline=(90, 90, 120) if not L['brake_zone'] else (60, 160, 60))
    for p in pts:
        if p['front'] != front: continue
        x, y = proj((p['x'], p['y'], p['z']))
        c = {'lamp':(80,255,255),'head':(80,255,255),'tail':(255,80,80),'brake':(255,255,0),'reverse':(255,255,255)}[p['kind']]
        dr.ellipse((x - 6, y - 6, x + 6, y + 6), outline=c, width=2)
    dr.text((8, 8), f"{car} {'front' if front else 'rear'}  cyan=head red=tail yellow=brake white=reverse; green outline=brake-zone draw", fill=(255, 255, 255))
    img.save(path)

import os
algo = ALGOS.get(os.environ.get('ALGO','613'))
for car in cars:
    try:
        m, P, UV, lamps, bl, pts = simulate(car, algo)
    except Exception as e:
        print(car, 'ERR', e); continue
    print(f"== {car} lamps={[ (L['names'][0], L['label'], L['brake_zone']) for L in lamps]}")
    for p in pts: print(f"   {'F' if p['front'] else 'R'} {p['kind']:5} x={p['x']:+.2f} y={p['y']:.2f} z={p['z']:+.2f} {p['src']}")
    for front in (True, False): render(car, P, UV, lamps, pts, out / f"{car}-{'front' if front else 'rear'}.png", front)
