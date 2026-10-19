"""COURSE-ALIVE1 automatic verification of the moving PS2 spline objects (24 objects, 17 courses).

Checks, each reported PASS / FAIL / NOT_PERFORMED:
1. inventory: the asset holds exactly the gaEntitySpline Eggs of the 36 PS2 RaceTest XML (24 in 17 courses, AMBIENT1
   case-evidence.json), each with its PS2 model, route and the eleven properties as `spline_runtime.parse_case` reads them;
2. resources: every model equals its W5 PC conversion (DX vertices in retail loader winding, DXT pixels), textures are
   power-of-two BGRA, every draw references an existing texture;
3. reference: the C++ controller (tests/spline_objects_tests.cpp --dump, built by the overlay) equals the AMBIENT1
   float32 reference `ps2-research/tools/spline_runtime.py` bit for bit for every object and every invocation of a
   20,000-invocation schedule (400 s at 50 Hz) with missing, far and near Car0 observers; plus pose summaries at
   0/10/60/120/300 s;
4. bounds, loops and re-initialisation: positions stay inside the control-point box widened by the Catmull-Rom
   overshoot bound, closed routes return to marker 0 at the cycle end, open routes hold the last marker, a second start
   gives the same timeline;
5. no static duplicates: the PS2 course packages (research-output/course-port-36) have no spline Egg, no Egg with a
   W5 model and no landscape mesh of the object texture within the model size of any route marker; the package
   course DX differs from the retail one, so the runtime guard admits it, and the retail DX is refused.

    python ps2-research/pc-port/tools/verify_spline_objects.py [--report docs/course-alive1/verification.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PORT / 'tools'))
import prepare_spline_objects as prep  # noqa: E402  (sets up the course-port / tools import paths)
from prepare_spline_objects import build_objects, cc, sr  # noqa: E402

TICKS = 20000
DUMP_ROW = struct.Struct('<BB2x11f2i')
PACKAGES = Path('D:/Game/Master Rallye/research-output/course-port-36')
TEST_EXE = PORT / '.build' / 'ps2-enabled' / 'Release' / 'ps2_spline_objects_tests.exe'
MARKS_S = (0, 10, 60, 120, 300)
F32 = struct.Struct('<f')


def bits(x):
    return F32.pack(x)


def decode_asset(blob):
    """Python mirror of decode_spline_objects_layout (independent of the C++ reader)."""
    h = prep.HEADER.unpack_from(blob, 0)
    if h[0] != prep.MAGIC or h[1] != prep.VERSION:
        raise ValueError('magic/version')
    at = prep.HEADER.size
    textures = []
    for _ in range(h[2]):
        w, ht = prep.TEXTURE.unpack_from(blob, at); at += prep.TEXTURE.size
        textures.append((w, ht, blob[at:at + w * ht * 4])); at += w * ht * 4
    models = []
    for _ in range(h[3]):
        r = prep.MODEL.unpack_from(blob, at); at += prep.MODEL.size
        models.append({'name': r[0].rstrip(b'\0').decode(), 'draws': [r[2 + 3 * i:5 + 3 * i] for i in range(r[1])], 'radius': r[8]})
    verts = [prep.VERTEX.unpack_from(blob, at + i * prep.VERTEX.size) for i in range(h[4])]; at += h[4] * prep.VERTEX.size
    courses = []
    for _ in range(h[5]):
        r = prep.COURSE.unpack_from(blob, at); at += prep.COURSE.size
        courses.append({'id': r[0].rstrip(b'\0').decode(), 'dx': r[1].rstrip(b'\0').decode(), 'retail': r[2].hex(), 'first': r[3], 'count': r[4]})
    objects = []
    for _ in range(h[6]):
        r = prep.OBJECT.unpack_from(blob, at); at += prep.OBJECT.size
        objects.append({'egg': r[0].rstrip(b'\0').decode(), 'model': r[1], 'first': r[2], 'count': r[3],
                        'flags': r[4:8], 'floats': r[8:12], 'ints': r[12:14]})
    npts = sum(o['count'] for o in objects)
    points = [prep.POINT.unpack_from(blob, at + i * 12) for i in range(npts)]; at += npts * 12
    if at != len(blob):
        raise ValueError('trailing bytes')
    return {'textures': textures, 'models': models, 'vertices': verts, 'courses': courses, 'objects': objects, 'points': points}


class Report:
    def __init__(self):
        self.checks = {}

    def set(self, name, status, **detail):
        self.checks[name] = {'status': status, **detail}
        print(f'{status:14} {name} {json.dumps(detail)[:300]}', flush=True)


def check_inventory(rep, asset, models, courses):
    expected = {}
    for c in cc.courses():
        eggs = prep.spline_eggs(cc.read_ps2(c.ps2_xml))
        if eggs:
            expected[c.name] = [e for e, _ in eggs]
    got = {c['id'].split('/', 1)[1]: [asset['objects'][c['first'] + i]['egg'] for i in range(c['count'])] for c in asset['courses']}
    evidence = json.loads((PORT.parent / 'ambient1' / 'case-evidence.json').read_text(encoding='utf-8'))
    # AMBIENT1 applicability rows (24): same Egg, route hash and duration as this phase reads them.
    ours = {(o['egg'], o['route_sha256']): o for c in courses for o in c['objects']}
    rows = evidence['applicability']
    matched = sum(1 for r in rows if (r['egg'], r['route_sha256']) in ours and
                  bits(ours[(r['egg'], r['route_sha256'])]['duration']) == bits(r['duration']))
    n_evidence = len(rows)
    ok = got == expected and sum(map(len, got.values())) == 24 and len(got) == 17 and matched == n_evidence == 24
    for c in courses:
        for o in c['objects']:
            a = next(x for x in asset['objects'] if x['egg'] == o['egg'] and x['first'] == _first_point(asset, c, o))
            k = o['config']
            ok &= a['flags'] == (k.const_speed, k.loop, k.trigger, k.rest)
            ok &= all(bits(x) == bits(y) for x, y in zip(a['floats'], (k.speed, k.on, k.off, k.banking)))
            ok &= a['ints'] == (k.rest_ticks, k.samples)
            ok &= [tuple(bits(v) for v in p) for p in asset['points'][a['first']:a['first'] + a['count']]] == \
                  [tuple(bits(v) for v in p) for p in o['points']]
            ok &= asset['models'][a['model']]['name'] == o['pc_model']
    rep.set('inventory_24_objects_17_courses', 'PASS' if ok else 'FAIL', courses=len(got), objects=sum(map(len, got.values())),
            ambient1_applicability_rows=n_evidence, ambient1_rows_matched=matched)


def _first_point(asset, c, o):
    idx = next(i for i, x in enumerate(asset['courses']) if x['id'] == c['id'])
    ac = asset['courses'][idx]
    for i in range(ac['count']):
        a = asset['objects'][ac['first'] + i]
        if a['egg'] == o['egg']:
            return a['first']
    raise KeyError(o['egg'])


def check_resources(rep, asset, models):
    ok, rows = True, {}
    for m in asset['models']:
        src = next(x for x in models.values() if x['name'] == m['name'])
        verts = [v for d in src['draws'] for v in d['vertices']]
        got = [asset['vertices'][i] for d in m['draws'] for i in range(d[1], d[1] + d[2])]
        same = [tuple(bits(x) if isinstance(x, float) else x for x in v) for v in got] == \
               [tuple(bits(x) if isinstance(x, float) else x for x in v) for v in verts]
        tex = all(asset['textures'][d[0]][2] == s['texture'][2] and asset['textures'][d[0]][:2] == s['texture'][:2]
                  for d, s in zip(m['draws'], src['draws']))
        pow2 = all(w & (w - 1) == 0 and h & (h - 1) == 0 for w, h, _ in asset['textures'])
        tris = sum(d[2] for d in m['draws']) // 3
        ok &= same and tex and pow2 and tris == 2 * src['ps2_triangles'] and src['two_sided_copies']
        rows[m['name']] = {'vertices_equal_w5_dx': same, 'textures_equal_w5_dxt': tex, 'triangles': tris,
                           'ps2_triangles': src['ps2_triangles'], 'dx_sources': src['sources']}
    rep.set('resources_equal_w5_models', 'PASS' if ok else 'FAIL', models=rows)


def observer_schedule(c):
    """Per course: absent (no Car0 payload), far, at marker 0 of the first object, far again, near again."""
    p0 = c['objects'][0]['points'][0]
    far = (p0[0] + 50000.0, p0[1], p0[2] + 50000.0)
    near = (p0[0] + 5.0, p0[1] + 2.0, p0[2] - 5.0)
    out = []
    for t in range(TICKS):
        if t < 50:
            out.append(None)
        elif t < 550:
            out.append(far)
        elif t < 12000:
            out.append(near)
        elif t < 14000:
            out.append(far)
        else:
            out.append(near)
    return out


def reference_timeline(o, observers):
    ctrl = sr.Controller(sr.PathState(o['points'], o['config']), 0)
    rows = []
    for ob in observers:
        r = ctrl.step(ob)
        status = {'NO_OBSERVER': 0, 'INACTIVE': 1, 'ACTIVE': 2}[r['status']]
        rows.append((status, int(r['active']), r['next_time'], *r['position'], *r['forward'], *r['up'], r['bank_mean'],
                     r['rest_counter'], r['ring_index']))
    return rows


def check_reference(rep, asset_path, courses):
    if not TEST_EXE.exists():
        rep.set('cpp_equals_ambient1_reference', 'NOT_PERFORMED', reason=f'{TEST_EXE} missing (build the overlay first)')
        return None
    with tempfile.TemporaryDirectory() as tmp:
        obs_path, out_path = Path(tmp) / 'obs.bin', Path(tmp) / 'dump.bin'
        schedules = [observer_schedule(c) for c in courses]
        nan = float('nan')
        obs_path.write_bytes(b''.join(struct.pack('<3f', *(o if o else (nan, nan, nan))) for s in schedules for o in s))
        subprocess.run([str(TEST_EXE), '--dump', str(asset_path), str(TICKS), str(obs_path), str(out_path)], check=True)
        dump = out_path.read_bytes()
    at, mismatches, compared, summaries = 0, [], 0, {}
    for c, sched in zip(courses, schedules):
        n = len(c['objects'])
        cpp = [[None] * TICKS for _ in range(n)]
        for t in range(TICKS):
            for i in range(n):
                cpp[i][t] = DUMP_ROW.unpack_from(dump, at); at += DUMP_ROW.size
        for i, o in enumerate(c['objects']):
            ref = reference_timeline(o, sched)
            for t in range(TICKS):
                a, b = cpp[i][t], ref[t]
                same = a[0] == b[0] and a[1] == b[1] and all(bits(x) == bits(y) for x, y in zip(a[2:13], b[2:13])) and a[13:] == b[13:]
                compared += 1
                if not same and len(mismatches) < 10:
                    mismatches.append({'course': c['name'], 'egg': o['egg'], 'tick': t, 'cpp': list(a), 'reference': list(b)})
                elif not same:
                    mismatches.append(None)
            marks = {}
            for s in MARKS_S:
                t = max(0, s * 50 - 1)
                r = ref[t]
                marks[f'{s}s'] = {'status': r[0], 'time': round(r[2], 4), 'moved_from_start': round(math.dist(r[3:6], o['points'][0]), 3)}
            summaries[f'{c["name"]}/{o["egg"]}'] = marks
    if at != len(dump):
        mismatches.append({'error': 'dump size'})
    rep.set('cpp_equals_ambient1_reference', 'PASS' if not mismatches else 'FAIL', invocations_compared=compared,
            ticks_per_object=TICKS, mismatches=len(mismatches), first=[m for m in mismatches if m][:3])
    return summaries


def check_bounds_loops(rep, courses):
    ok, rows = True, {}
    for c in courses:
        for o in c['objects']:
            pts = o['points']
            chord = max(math.dist(a, b) for a, b in zip(pts, pts[1:] + ([pts[0]] if o['config'].loop else [])))
            lo = [min(p[k] for p in pts) - 0.25 * chord for k in range(3)]
            hi = [max(p[k] for p in pts) + 0.25 * chord for k in range(3)]
            cfg = o['config']
            path = sr.PathState(pts, cfg)
            cycle = math.floor(path.duration * 30) + 2
            far = (1e7, 0.0, 1e7)
            a = sr.Controller(sr.PathState(pts, cfg), 0)
            if cfg.trigger:
                a.active = True  # bounds/loop shape only; activation is covered by the reference check
            inside, positions = True, []
            for _ in range(cycle + 5):
                r = a.step(far if not cfg.trigger else tuple(a.position))
                p = r['position']; positions.append(p)
                inside &= all(lo[k] <= p[k] <= hi[k] for k in range(3))
            if cfg.loop:
                end_ok = any(math.dist(p, pts[0]) < 1e-3 for p in positions[cycle - 4:cycle + 5])
            else:
                end_ok = math.dist(positions[-1], pts[-1]) < 1e-3
            b = sr.Controller(sr.PathState(pts, cfg), 0)
            if cfg.trigger:
                b.active = True
            again = [b.step(far if not cfg.trigger else tuple(b.position))['position'] for _ in range(200)]
            reinit = [tuple(bits(v) for v in p) for p in again] == [tuple(bits(v) for v in p) for p in positions[:200]]
            ok &= inside and end_ok and reinit
            rows[f'{c["name"]}/{o["egg"]}'] = {'inside_control_box_plus_quarter_chord': inside,
                                               'closed_returns_to_marker0' if cfg.loop else 'open_holds_last_marker': end_ok,
                                               'reinit_identical': reinit, 'cycle_invocations': cycle - 2}
    rep.set('bounds_loops_reinit', 'PASS' if ok else 'FAIL', objects=rows)


def check_duplicates(rep, courses):
    if not PACKAGES.exists():
        rep.set('no_static_duplicates_and_guard', 'NOT_PERFORMED', reason=f'{PACKAGES} missing')
        return
    from master_rallye.dx_course import parse_course_dx_bytes
    ok, rows = True, {}
    tex_key = {'reddinghy': 'dinghy', 'bluedinghy': 'dinghy', 'airship': 'stamp', 'barge': 'plating2'}
    for c in courses:
        pkg = PACKAGES / c['name']
        xml = (pkg / 'DataScene' / 'RaceTest' / f'{c["name"]}.xml').read_bytes().lower()
        no_egg = b'gaentityspline' not in xml and b'ps2port' not in xml and not any(
            k.encode() in xml for k in ('dinghys\\', 'airship\\airship', 'barge\\barge'))
        dx_path = pkg / Path(c['pc_dx_path'])
        if not dx_path.exists():
            dx_path = next((pkg / 'DataGx' / 'Course').rglob('*.dx'))
        dx = dx_path.read_bytes()
        guard_package = hashlib.sha256(dx).hexdigest() != c['retail_pc_dx_sha256']
        m = parse_course_dx_bytes(dx)
        pos = m.vertices.positions
        close = []
        for o in c['objects']:
            key = tex_key[o['pc_model']]
            radius = next(x for x in prep_models if x['name'] == o['pc_model'])['radius']
            for d in m.physical_draws:
                if not any(key in s.lower() for s in d.texture_tuple):
                    continue
                idx = m.draw_global_indices(d)
                if len(idx) // 3 > 2 * 81:  # larger than any spline model: harbour scenery, not a copy
                    continue
                cen = [sum(pos[i][k] for i in idx) / len(idx) for k in range(3)]
                if min(math.dist(cen, p) for p in o['points']) < radius:
                    close.append({'egg': o['egg'], 'draw': d.draw_index, 'triangles': len(idx) // 3})
        rows[c['name']] = {'xml_has_no_spline_or_w5_egg': no_egg, 'landscape_copies_near_route': close,
                           'package_dx_differs_from_retail': guard_package, 'package_dx': dx_path.relative_to(pkg).as_posix()}
        ok &= no_egg and not close and guard_package
    rep.set('no_static_duplicates_and_guard', 'PASS' if ok else 'FAIL', courses=rows)


prep_models = []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--asset', type=Path, default=prep.ASSET)
    a = ap.parse_args()
    rep = Report()
    models, courses = prep.collect()
    prep_models.extend(models.values())
    blob, _ = prep.build_asset(models, courses)
    on_disk = a.asset.read_bytes() if a.asset.exists() else b''
    digest = hashlib.sha256(blob).hexdigest()
    pinned = (PORT / 'renderer' / 'spline_objects.hpp').read_text(encoding='utf-8').split('kSplineObjectsArtifactSha[]="')[1][:64]
    rep.set('asset_deterministic_and_pinned', 'PASS' if on_disk == blob and digest == pinned else 'FAIL', sha256=digest, pinned=pinned,
            bytes=len(blob), on_disk_equal=on_disk == blob)
    asset = decode_asset(blob)
    check_inventory(rep, asset, models, courses)
    check_resources(rep, asset, models)
    summaries = check_reference(rep, a.asset, courses)
    check_bounds_loops(rep, courses)
    check_duplicates(rep, courses)
    result = {'schema_version': 1, 'phase': 'COURSE-ALIVE1', 'asset_sha256': digest,
              'overall': 'PASS' if all(v['status'] == 'PASS' for v in rep.checks.values()) else
              ('FAIL' if any(v['status'] == 'FAIL' for v in rep.checks.values()) else 'PARTIAL'),
              'checks': rep.checks, 'time_marks': summaries}
    if a.report:
        a.report.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print('OVERALL', result['overall'])
    return 0 if result['overall'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
