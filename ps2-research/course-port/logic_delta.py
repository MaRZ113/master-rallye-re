"""Race logic of the PS2 vs the PC RaceTest XML, per course (W4 survey, read only).

Marker lists: count on each side and, for lists present on both, the largest distance from a PC marker to the nearest PS2 marker of the same list
(XZ), plus whether the lists are point-for-point equal (0.01). Eggs: grouped by (AI component classes, model), counted per side; Eggs with a
gaRaceSplitTimeAI component are listed with positions.

    python logic_delta.py --out logic-delta-36.json
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402


def lists(doc):
    return {ml.name: [m.position for m in ml.markers if m.position] for ml in doc.marker_lists}


def egg_key(e):
    classes = sorted({c.tag for c in e.components()})
    return json.dumps({'ai': classes, 'model': (e.model_name or '').lower()}, sort_keys=True)


def compare(course):
    ps2 = parse_course_xml_bytes(cc.read_ps2(course.ps2_xml), 'ps2')
    pc = parse_course_xml_bytes(course.pc_xml.read_bytes(), 'pc')
    lp, lc = lists(ps2), lists(pc)
    out_lists = {}
    for name in sorted(set(lp) | set(lc)):
        a, b = lp.get(name), lc.get(name)
        row = {'ps2': None if a is None else len(a), 'pc': None if b is None else len(b)}
        if a and b:
            row['max_pc_to_nearest_ps2_xz'] = round(max(min(math.dist((p[0], p[2]), (q[0], q[2])) for q in a) for p in b), 2)
            row['equal'] = len(a) == len(b) and all(math.dist(p, q) <= 0.01 for p, q in zip(a, b))
        out_lists[name] = row
    ep = collections.Counter(egg_key(e) for e in ps2.eggs)
    ec = collections.Counter(egg_key(e) for e in pc.eggs)
    eggs = {k: {'ps2': ep.get(k, 0), 'pc': ec.get(k, 0)} for k in sorted(set(ep) | set(ec)) if ep.get(k, 0) != ec.get(k, 0)}

    def splits(doc):
        res = []
        for e in doc.split_time_eggs:
            m = e.matrix()
            res.append({'name': e.name, 'pos': None if m is None or m.position is None else [round(v, 2) for v in m.position]})
        return res
    return {'lists': out_lists, 'egg_groups_that_differ': eggs, 'splits': {'ps2': splits(ps2), 'pc': splits(pc)},
            'eggs_total': {'ps2': len(ps2.eggs), 'pc': len(pc.eggs)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    res = {}
    for c in cc.courses():
        try:
            res[c.name] = compare(c)
        except Exception as e:  # noqa: BLE001
            res[c.name] = {'error': f'{type(e).__name__}: {e}'}
        r = res[c.name]
        if 'error' in r:
            print(c.name, r['error'])
            continue
        diff = {k: v for k, v in r['lists'].items() if not v.get('equal')}
        print(c.name, 'eggs', r['eggs_total'], 'lists differing', {k: (v['ps2'], v['pc'], v.get('max_pc_to_nearest_ps2_xz')) for k, v in diff.items()})
    a.out.write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
