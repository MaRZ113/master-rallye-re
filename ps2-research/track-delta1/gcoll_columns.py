"""G-COLL query 1: vertical first-contact heights, PS2 BSP versus PC tag100, on Turkey3 ground columns.

Columns are centroids of PS2 visual ground triangles, split into those that match PC visuals exactly and the
non-exact (candidate extra) ones. Contact = first solid leaf entry or payload polygon hit when marching down from
`lift` above to `depth` below the visual surface. Orientation and leaf semantics come from bsp_orientation.py;
PC tag100 uses the same plane convention (verified there: 98% empty above, 99% solid below ground).
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import geometry_delta as g  # noqa: E402
import ps2_bsp  # noqa: E402
import bsp_query as q  # noqa: E402
from master_rallye.course_tag100 import parse_course_tag100_bytes  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx  # noqa: E402


class _N:
    __slots__ = ('plane', 'child', 'sibling', 'field_0', 'payload')


def pc_nodes(dx_path):
    r = parse_course_tag100_bytes(extract_tag100_from_dx(Path(dx_path)).raw, 'pc', allow_trailing=True)
    nodes = []
    for n in r.nodes:
        o = _N()
        o.plane = n.optional_record.values if n.optional_record else None
        o.child, o.sibling, o.field_0, o.payload = n.first_child_index, n.next_sibling_index, n.field_0, None
        nodes.append(o)
    return nodes


def pc_first_contact(nodes, a, b):
    for leaf, t0, _t1 in q.ps2_segment_leaves(nodes, a, b):
        if leaf.field_0 == 0xffffffff:
            return t0
    return None


def columns(a, forward, limit):
    rel = {r['source']: r['geometry_relation'] for r in forward}
    exact, extra = [], []
    for f in a.faces:
        if 'shader(ground)' not in a.groups[f.group]['material'].lower():
            continue
        n = g.normal(f.points)
        if abs(n[1]) < .95:
            continue
        c = tuple(sum(p[i] for p in f.points) / 3 for i in range(3))
        (exact if rel[f.identifier] == 'EXACT_TRIANGLE_MATCH' else extra).append(c)
    def thin(v):
        return v[::max(1, len(v) // limit)]
    return thin(exact), thin(extra)


def stats(pairs):
    both = [(p, c) for p, c in pairs if p is not None and c is not None]
    d = sorted(p - c for p, c in both)
    def pct(x):
        return round(d[int(x * (len(d) - 1))], 3) if d else None
    return {'columns': len(pairs), 'both_hit': len(both),
            'ps2_only': sum(p is not None and c is None for p, c in pairs),
            'pc_only': sum(p is None and c is not None for p, c in pairs),
            'neither': sum(p is None and c is None for p, c in pairs),
            'within_0.05': sum(abs(x) <= .05 for x in d), 'within_0.25': sum(abs(x) <= .25 for x in d),
            'within_1.0': sum(abs(x) <= 1 for x in d),
            'dy_ps2_minus_pc_percentiles': {p: pct(p / 100) for p in (1, 10, 50, 90, 99)}}


def main(ps2_root, pc_root, sdk, ps2_bsp_path, limit=1500, lift=3.0, depth=6.0):
    a, b, _ = g.load_pair(Path(ps2_root), Path(pc_root), Path(sdk), 'TURKEY3')
    _, forward, _ = g.compare(a, b)
    bsp = ps2_bsp.parse(Path(ps2_bsp_path).read_bytes())
    pcn = pc_nodes(Path(pc_root) / 'DataGx/Course/Turkey3/turkey3.dx')
    exact, extra = columns(a, forward, limit)
    out = {}
    for name, cols in (('exact_match_ground', exact), ('non_exact_ground', extra)):
        pairs = []
        for c in cols:
            top, bot = (c[0], c[1] + lift, c[2]), (c[0], c[1] - depth, c[2])
            h = q.ps2_first_contact(bsp, top, bot)
            ps2_y = None if h is None else top[1] + (bot[1] - top[1]) * h[0]
            t = pc_first_contact(pcn, top, bot)
            pc_y = None if t is None else top[1] + (bot[1] - top[1]) * t
            pairs.append((None if ps2_y is None else ps2_y - c[1], None if pc_y is None else pc_y - c[1]))
        # report heights relative to the visual surface, plus PS2-vs-PC difference
        rel = [p for p, _ in pairs if p is not None]
        out[name] = {**stats(pairs),
                     'ps2_vs_visual_within_0.05': sum(abs(x) <= .05 for x in rel),
                     'pc_vs_visual_within_0.05': sum(abs(c) <= .05 for _, c in pairs if c is not None)}
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:5])
