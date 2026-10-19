"""Build the full PS2 collision for one course as a loose PC course DX (W1).

    python build_collision.py --course Turkey3 --out <dir> [--surface ps2|retail]

The DX is the retail render prefix (unchanged) + the tag100-starting suffix rebuilt from PS2 data:
  tree      PS2 .BSP converted by ps2_to_tag100.convert (exact geometry, codes with provenance)
  tag1339   retail (render bounds: the render is unchanged in W1)
  tag1400   --surface ps2 (default): surface grid from the PS2 landscape triangles (surface_grid); --surface retail: the retail block
  tag1500   retail (meaning unknown)
Writes <out>/DataGx/Course/<dir>/<name>.dx and <out>/collision-report.json. Nothing is installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'course-port'))
sys.path.insert(0, str(HERE.parent / 'track-delta1'))
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402
import ps2_bsp  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402
import ps2_to_tag100 as conv  # noqa: E402
import surface_grid as sg  # noqa: E402
import tag100_tree as tt  # noqa: E402
import tag1400_io as io  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402
from master_rallye.course_tag1400 import parse_course_tag1400_bytes  # noqa: E402


def ps2_scene(course):
    payload = cc.read_ps2(course.ps2_psm)
    return o.w.decode_scene(payload), payload


def build(course, surface='ps2'):
    retail = course.pc_dx.read_bytes()
    sl = extract_tag100_from_dx_bytes(retail, course.pc_dx.name)
    tree_raw, b1339, u_retail, r1500 = io.split_suffix(sl.raw)
    pc = tt.Tree(sl.raw)
    bsp = ps2_bsp.parse(cc.read_ps2(course.ps2_bsp))
    scene, _ = ps2_scene(course)
    recs = sg.ps2_records(scene, o.source_triangles)
    xs = [r[0][i] for r in recs for i in (0, 3, 6)]
    ys = [r[0][i] for r in recs for i in (1, 4, 7)]
    zs = [r[0][i] for r in recs for i in (2, 5, 8)]
    centre = ((min(xs) + max(xs)) / 2, max(ys) + 50.0, (min(zs) + max(zs)) / 2)
    codes = conv.PlaneCodes(pc, centre)
    if surface == 'ps2':
        u, u_rep = sg.build(recs)
    else:
        u, u_rep = u_retail, {'retail': True}
    new, stats = conv.convert(bsp, codes, tail=b1339 + u + r1500)
    raw = new.serialize()
    dx = retail[:sl.tag_offset] + raw
    again = tt.Tree(raw)
    parsed_u = parse_course_tag1400_bytes(u, 'u')
    report = {
        'course': course.name, 'surface': surface,
        'ps2_bsp': {'nodes': len(bsp.nodes), 'plane_table': len(bsp.plane_table)},
        'tree': {'stats': dict(stats), 'code_provenance': dict(codes.provenance), 'default_code': codes.default, 'default_code_source': codes.default_source,
                 'retail_tree_bytes': len(tree_raw), 'new_tree_bytes': len(raw) - len(b1339 + u + r1500),
                 'retail_plane_nodes': sum(1 for p in pc.plane if p is not None), 'new_plane_nodes': stats['plane_nodes'],
                 'round_trip_identical': again.serialize() == raw, 'count_invariants_ok': new.counts_ok(),
                 'negative_codes': sum(1 for c in new.code if c is not None and c >= 0x80000000)},
        'tag1400': {**u_rep, 'retail_records': len(parse_course_tag1400_bytes(u_retail, 'r').records), 'new_records': len(parsed_u.records),
                    'dims': [parsed_u.dimension_0, parsed_u.dimension_1], 'bytes': len(u)},
        'render_prefix_identical': dx[:sl.tag_offset] == retail[:sl.tag_offset],
        'dx_bytes': len(dx), 'dx_sha256': hashlib.sha256(dx).hexdigest(),
    }
    return dx, new, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--course', required=True)
    ap.add_argument('--surface', choices=('ps2', 'retail'), default='ps2')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    course = cc.course(a.course)
    dx, _, rep = build(course, a.surface)
    rel = course.pc_dx.relative_to(cc.PC_ROOT)
    target = a.out / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(dx)
    (a.out / 'collision-report.json').write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
