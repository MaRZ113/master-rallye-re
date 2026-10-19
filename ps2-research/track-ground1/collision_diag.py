"""TRACK-GROUND1 collision diagnostics: PS2 BSP vs original PC tag100 vs patched PC tag100, per world column, deterministic.

Domain: every cell of a fixed grid (step S, origin at the PS2 ground bounding box minimum) whose centre is covered by a PS2 ground triangle (the visible
PS2 terrain). For each column x,z with h_vis = highest visible PS2 ground height there:
  * three exact vertical segment queries from h_vis + UP to h_vis - DOWN (leaf traversal, no height sampling): first solid contact height in the
    PS2 BSP (solidity rule of the PS2 leaf classes), in the retail PC tag100 and in the patched PC tag100;
  * PS2 solid-exterior test: solid at h_vis + 3 (the PS2 shell is solid at +3, +30 and +100 above the ground) or a solid start of the query;
  * overhang test: after the PS2 first contact the column is empty at +0.3 and solid again within OVERHANG units above;
  * layers: number of visible PS2 ground triangles covering the column whose heights differ by more than 0.5.
Classes against the PS2 BSP (tolerance TOL):
  agree             both found and |patched - PS2| <= TOL, or neither finds a surface
  missing_support   the PS2 BSP has a surface and the patched tree has none, or its surface is lower by more than TOL (the car sinks)
  invisible_block   the patched surface is higher than the PS2 one by more than TOL, or the patched query starts inside solid while PS2 does not
  ps2_exterior      PS2 solid exterior interferes (excluded from the other classes, reported separately)
  ps2_void          the PS2 BSP has no solid anywhere in the column window while the patched tree has a surface (PS2 collision void under the visible
                    ground: PS2 behaviour, not a transfer error; reported separately and never a TRACK-COLL1 candidate)
  overhang / multilayer are flags on top of the class.
Regions: 8-connected groups of non-agreeing columns of one class. Output: JSON with every region's bounds, error statistics, expected contact heights
(PS2 BSP) and teleport-ready probe positions, plus a ranking of isolated candidate regions for TRACK-COLL1.
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TD1 = HERE.parent / 'track-delta1'
sys.path.insert(0, str(TD1))
sys.path.insert(0, str(TD1.parent / 'tools'))
sys.path.insert(0, str(TD1.parent.parent / 'src'))
import bsp_query as q  # noqa: E402
import gcoll_columns as gc  # noqa: E402
import gcoll_map as gm  # noqa: E402
import ground_delta_probe as gdp  # noqa: E402
import ps2_bsp  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
import course_delta as cd  # noqa: E402

UP, DOWN, OVERHANG, TOL = 6.0, 12.0, 8.0, 0.25


def ps2_surface(bsp, x, z, top, bottom):
    """First solid contact height of the PS2 BSP going down from `top`; (height | None, started_solid)."""
    t = q.ps2_first_solid_t(bsp, (x, top, z), (x, bottom, z))
    if t is None:
        return None, False
    return top + (bottom - top) * t, t <= 1e-9


MIN_SOLID = 1e-4   # units; a PC solid leaf thinner than this is a ray grazing a cell edge, not a surface (TRACK-COLL1A correction)


def pc_first_contact(nodes, a, b):
    length = math.dist(a, b)
    for leaf, t0, t1 in q.ps2_segment_leaves(nodes, a, b):
        if leaf.field_0 == 0xffffffff and (t1 - t0) * length > MIN_SOLID:
            return t0
    return None


def pc_surface(nodes, x, z, top, bottom):
    t = pc_first_contact(nodes, (x, top, z), (x, bottom, z))
    if t is None:
        return None, False
    return top + (bottom - top) * t, t <= 1e-9


def bsp_gap_below(bsp, x, z, s_ps2, bottom, step=0.5):
    """Height of a second PS2 BSP surface below the first one (empty gap, then solid again), or None: caves, arches, overhang undersides."""
    y = s_ps2 - 0.6
    gap = False
    while y > bottom:
        solid = q.ps2_is_solid(bsp, (x, y, z))
        if not solid:
            gap = True
        elif gap:
            return round(y, 2)
        y -= step
    return None


def layer_count(grid, x, z):
    heights = []
    for (ax, ay, az), (bx, by, bz), (cx, cy, cz) in grid.get((int(x // gdp.CELL), int(z // gdp.CELL)), []):
        den = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        if abs(den) < 1e-9:
            continue
        w1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / den
        w2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / den
        w3 = 1 - w1 - w2
        if min(w1, w2, w3) >= -1e-6:
            heights.append(w1 * ay + w2 * by + w3 * cy)
    heights.sort()
    layers = 0
    last = None
    for h in heights:
        if last is None or h - last > 0.5:
            layers += 1
        last = h
    return layers


def classify(h_vis, s_ps2, started_ps2, s_new, started_new, exterior):
    if exterior:
        return 'ps2_exterior'
    if s_ps2 is None and s_new is None:
        return 'agree'
    if s_ps2 is None:
        return 'ps2_void'
    if s_ps2 is not None and (s_new is None or s_new < s_ps2 - TOL):
        return 'missing_support'
    if s_new > s_ps2 + TOL or (started_new and not started_ps2):
        return 'invisible_block'
    return 'agree'


ELIGIBLE = {'columns': (3, 60), 'max_distance_to_raceline': 80.0, 'min_distance_to_converted_object': 60.0, 'min_isolation': 30.0, 'min_mean_error': 0.5}


def rank(regions, step, cols):
    """Eligible = bounded, resolved, single-layer (no BSP second surface, no visible multilayer, no overhang), reachable, away from converted objects and
    from other mismatch regions. Score: isolation (capped at 150) + 20 x mean error (capped at 4) - columns - 0.5 x distance to the RaceLine - 60 when PS2 exterior or void columns lie within 36 units."""
    out = []
    for r in regions:
        reasons = []
        if not ELIGIBLE['columns'][0] <= r['columns'] <= ELIGIBLE['columns'][1]:
            reasons.append('size')
        if r['unresolved_columns_without_ps2_or_patched_surface']:
            reasons.append('unresolved columns')
        if r['multilayer_columns'] or r['overhang_columns'] or r['bsp_second_surface_columns']:
            reasons.append('multilayer or overhang')
        if r['distance_to_raceline'] is None or r['distance_to_raceline'] > ELIGIBLE['max_distance_to_raceline']:
            reasons.append('far from the road')
        if r['distance_to_converted_object'] is not None and r['distance_to_converted_object'] < ELIGIBLE['min_distance_to_converted_object']:
            reasons.append('near a converted object')
        if r['isolation_to_next_region'] is not None and r['isolation_to_next_region'] < ELIGIBLE['min_isolation']:
            reasons.append('not isolated')
        if r['error_new_mean_abs'] is None or r['error_new_mean_abs'] < ELIGIBLE['min_mean_error']:
            reasons.append('error too small to observe')
        r['ineligible_reasons'] = reasons
        if reasons:
            continue
        cx, cz = r['centroid_xz']
        near = defaultdict(int)
        for c in cols.values():
            if math.dist((c['x'], c['z']), (cx, cz)) <= 36.0:
                near[c['class_new']] += 1
        exterior_free = near.get('ps2_exterior', 0) == 0 and near.get('ps2_void', 0) == 0
        score = (0 if exterior_free else -60) + min(r['isolation_to_next_region'] or 150.0, 150.0) + 20 * min(r['error_new_mean_abs'], 4.0) - r['columns'] - 0.5 * r['distance_to_raceline']
        out.append({'score': round(score, 1), 'exterior_free_within_36_units': exterior_free, 'neighbourhood_36_units_class_counts': dict(near), 'class': r['class'], 'centroid_xz': r['centroid_xz'], 'bounds_xz': r['bounds_xz'], 'columns': r['columns'], 'area_units2': r['area_units2'],
                    'error_new_max_abs': r['error_new_max_abs'], 'error_new_mean_abs': r['error_new_mean_abs'], 'distance_to_raceline': r['distance_to_raceline'],
                    'isolation_to_next_region': r['isolation_to_next_region'], 'distance_to_converted_object': r['distance_to_converted_object'],
                    'retail_class_counts': r['retail_class_counts'], 'probes': r['probes'],
                    'columns_table': [{'x': c['x'], 'z': c['z'], 'visible_ps2_height': c['h_vis'], 'ps2_bsp_contact': c['ps2'], 'retail_pc_contact': c['old'],
                                       'patched_pc_contact': c['new'], 'error_patched_minus_ps2': c['err_new']} for c in r['_columns']]})
    out.sort(key=lambda r: (not r['exterior_free_within_36_units'], -r['score']))  # exterior-free regions first, then by score
    for i, r in enumerate(out, 1):
        r['rank'] = i
    return out[:8]


def components(cells):
    seen, out = set(), []
    for c in sorted(cells):
        if c in seen:
            continue
        stack, comp = [c], []
        seen.add(c)
        while stack:
            i, j = stack.pop()
            comp.append((i, j))
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    n = (i + di, j + dj)
                    if n in cells and n not in seen:
                        seen.add(n)
                        stack.append(n)
        out.append(sorted(comp))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--bsp', type=Path, default=TD1.parent / 'data/track-bsp/TURKEY3.BSP')
    ap.add_argument('--retail-dx', type=Path, required=True)
    ap.add_argument('--patched-dx', type=Path, required=True)
    ap.add_argument('--sdk', type=Path, default=Path('D:/Game/Master Rallye/master-rallye-course'))
    ap.add_argument('--pc-xml', type=Path, required=True)
    ap.add_argument('--objects-report', type=Path, help='report.json of ps2_course_objects.py (object centres to keep away from)')
    ap.add_argument('--step', type=float, default=6.0)
    ap.add_argument('--limit', type=int, default=0, help='only the first N columns (smoke test)')
    ap.add_argument('--requery-pc', action='store_true', help='keep h_vis and the PS2 results of --columns-cache but query the two PC trees again (after the grazing-leaf correction)')
    ap.add_argument('--columns-cache', type=Path, help='gzip JSON of the raw per-column queries; reused when it exists (queries are the slow part)')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    bsp = ps2_bsp.parse(a.bsp.read_bytes())
    old, new = gc.pc_nodes(a.retail_dx), gc.pc_nodes(a.patched_dx)
    manifest, _ = o.t.load_pak(a.ps2_root / 'TNG.PAK')
    scene = o.w.decode_scene(o.extract(manifest, a.ps2_root, o.PSM_PATH))
    tris = gdp.ground_triangles(scene)
    grid = gdp.build_index(tris)
    xs = [p[0] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    x0, z0 = min(xs), min(zs)
    nx, nz = int((max(xs) - x0) // a.step) + 1, int((max(zs) - z0) // a.step) + 1
    sdk, _ = cd.sdk_modules(a.sdk)
    route = gm.markers(sdk, a.pc_xml.read_bytes(), 'RaceLine')
    objects = []
    if a.objects_report:
        rep = json.loads(a.objects_report.read_text())
        objects = [(i['translation'][0], i['translation'][2]) for m in rep['models'] for i in m['instances']]
    import gzip
    cols = {}
    count = 0
    cached = None
    if a.columns_cache and a.columns_cache.exists():
        cached = {tuple(map(int, k.split(','))): v for k, v in json.loads(gzip.open(a.columns_cache, 'rt').read()).items()}
    for i in range(nx if cached is None else 0):
        for j in range(nz):
            x, z = x0 + i * a.step, z0 + j * a.step
            h = gdp.height_at(grid, x, z)
            if h is None:
                continue
            count += 1
            if a.limit and count > a.limit:
                break
            top, bottom = h + UP, h - DOWN
            s_ps2, st_ps2 = ps2_surface(bsp, x, z, top, bottom)
            s_old, st_old = pc_surface(old, x, z, top, bottom)
            s_new, st_new = pc_surface(new, x, z, top, bottom)
            ext = st_ps2 or q.ps2_is_solid(bsp, (x, h + 3.0, z))
            over = None
            if s_ps2 is not None and not ext:
                tt = q.ps2_first_solid_t(bsp, (x, s_ps2 + 0.3, z), (x, s_ps2 + OVERHANG, z))
                if tt is not None and not q.ps2_is_solid(bsp, (x, s_ps2 + 0.3, z)):
                    over = round(s_ps2 + 0.3 + (OVERHANG - 0.3) * tt, 2)
            layers = layer_count(grid, x, z)
            cols[i, j] = {'x': round(x, 2), 'z': round(z, 2), 'h_vis': round(h, 3), 'ps2': None if s_ps2 is None else round(s_ps2, 3),
                          'old': None if s_old is None else round(s_old, 3), 'new': None if s_new is None else round(s_new, 3),
                          'exterior': bool(ext), 'overhang_at': over, 'layers': layers,
                          'st_ps2': bool(st_ps2), 'st_old': bool(st_old), 'st_new': bool(st_new)}
        else:
            continue
        break
    if cached is not None:
        cols = cached
        if a.requery_pc:
            for c in cols.values():
                top, bottom = c['h_vis'] + UP, c['h_vis'] - DOWN
                for key, st, nodes in (('old', 'st_old', old), ('new', 'st_new', new)):
                    h, started = pc_surface(nodes, c['x'], c['z'], top, bottom)
                    c[key], c[st] = (None if h is None else round(h, 3)), bool(started)
    elif a.columns_cache:
        a.columns_cache.write_bytes(gzip.compress(json.dumps({f'{k[0]},{k[1]}': v for k, v in cols.items()}).encode()))
    for c in cols.values():
        c['class_new'] = classify(c['h_vis'], c['ps2'], c['st_ps2'], c['new'], c['st_new'], c['exterior'])
        c['class_old'] = classify(c['h_vis'], c['ps2'], c['st_ps2'], c['old'], c['st_old'], c['exterior'])
        c['err_new'] = None if (c['ps2'] is None or c['new'] is None) else round(c['new'] - c['ps2'], 3)
    n = len(cols)
    tally = defaultdict(int)
    flows = defaultdict(int)
    for c in cols.values():
        tally[c['class_new']] += 1
        flows[(c['class_old'], c['class_new'])] += 1
    summary = {'step': a.step, 'columns': n, 'classes_patched': dict(tally), 'classes_retail': {k: sum(1 for c in cols.values() if c['class_old'] == k)
               for k in ('agree', 'missing_support', 'invisible_block', 'ps2_exterior', 'ps2_void')},
               'old_to_new': {f'{k[0]}->{k[1]}': v for k, v in sorted(flows.items())},
               'overhang_columns': sum(1 for c in cols.values() if c['overhang_at'] is not None), 'multilayer_columns': sum(1 for c in cols.values() if c['layers'] > 1),
               'ps2_surface_vs_visible_gt_0.5': sum(1 for c in cols.values() if c['ps2'] is not None and abs(c['ps2'] - c['h_vis']) > 0.5 and not c['exterior'])}
    regions = []
    comps_by_region = {}
    for cls in ('missing_support', 'invisible_block'):
        cells = {k for k, c in cols.items() if c['class_new'] == cls}
        for comp in components(cells):
            cs = [cols[k] for k in comp]
            errs = [abs(c['err_new']) for c in cs if c['err_new'] is not None]
            cx = sum(c['x'] for c in cs) / len(cs)
            cz = sum(c['z'] for c in cs) / len(cs)
            worst = max(cs, key=lambda c: abs(c['err_new']) if c['err_new'] is not None else 99.0)
            road = min((math.dist((cx, cz), p) for p in route), default=None)
            near_obj = min((math.dist((cx, cz), p) for p in objects), default=None)
            probes = [{'label': 'centroid_nearest', 'column': min(cs, key=lambda c: math.dist((c['x'], c['z']), (cx, cz)))},
                      {'label': 'worst_error', 'column': worst}]
            region_obj = {
                'class': cls, 'columns': len(cs), 'area_units2': round(len(cs) * a.step * a.step),
                'bounds_xz': [min(c['x'] for c in cs), min(c['z'] for c in cs), max(c['x'] for c in cs), max(c['z'] for c in cs)],
                'ps2_surface_range': [min((c['ps2'] for c in cs if c['ps2'] is not None), default=None), max((c['ps2'] for c in cs if c['ps2'] is not None), default=None)],
                'error_new_max_abs': round(max(errs), 3) if errs else None, 'error_new_mean_abs': round(sum(errs) / len(errs), 3) if errs else None,
                'unresolved_columns_without_ps2_or_patched_surface': sum(1 for c in cs if c['err_new'] is None),
                'overhang_columns': sum(1 for c in cs if c['overhang_at'] is not None), 'multilayer_columns': sum(1 for c in cs if c['layers'] > 1),
                'retail_class_counts': {k: sum(1 for c in cs if c['class_old'] == k) for k in ('agree', 'missing_support', 'invisible_block', 'ps2_exterior', 'ps2_void')},
                'distance_to_raceline': None if road is None else round(road, 1), 'distance_to_converted_object': None if near_obj is None else round(near_obj, 1),
                'centroid_xz': [round(cx, 2), round(cz, 2)],
                'probes': [{'label': p['label'], 'x': p['column']['x'], 'z': p['column']['z'], 'ps2_contact_height': p['column']['ps2'], 'retail_contact_height': p['column']['old'],
                            'patched_contact_height': p['column']['new'], 'teleport_point': f"{p['column']['x']},{round((p['column']['ps2'] if p['column']['ps2'] is not None else p['column']['h_vis']) + 1.5, 2)},{p['column']['z']},0"} for p in probes],
            }
            region_obj['_columns'] = [cols[k] for k in comp]
            comps_by_region[id(region_obj)] = comp
            regions.append(region_obj)
    for r in regions:
        cs = [cols[k] for k in comps_by_region[id(r)]]
        r['bsp_second_surface_columns'] = sum(1 for c in cs if c['ps2'] is not None and bsp_gap_below(bsp, c['x'], c['z'], c['ps2'], c['h_vis'] - DOWN) is not None)
    # isolation: nearest other region (any class) centroid
    for r in regions:
        others = [math.dist(r['centroid_xz'], s['centroid_xz']) for s in regions if s is not r]
        r['isolation_to_next_region'] = round(min(others), 1) if others else None
    ranking = rank(regions, a.step, cols)
    for r in regions:
        r.pop('_columns', None)
    a.out.write_text(json.dumps({'summary': summary, 'parameters': {'up': UP, 'down': DOWN, 'overhang': OVERHANG, 'tolerance': TOL, 'step': a.step},
                                 'ranking': ranking, 'regions': sorted(regions, key=lambda r: -r['columns'])}, indent=1))
    print(json.dumps(summary, indent=1))
    print(len(regions), 'regions')


if __name__ == '__main__':
    main()
