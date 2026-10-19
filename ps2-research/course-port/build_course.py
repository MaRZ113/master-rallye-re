"""Full PS2 course package for one or all courses (W7): PS2 collision (W1) + PS2 render (W2) + PS2-only textures, plus the offline checks.

    python build_course.py --course Turkey3 --out <dir> [--noise plain|local]
    python build_course.py --all --out <dir> --summary course-packages-36.json

Each package is <out>/<Course>/DataGx/Course/<dir>/<name>.dx (+ .dxt files) and <out>/<Course>/package-report.json. Nothing is installed. The
RaceTest XML is not part of the package (W4 has no writer yet); the retail XML stays in use.
Checks per package: collision against the PS2 BSP (validate_collision, random points and columns), render triangle set equal to PS2, render
section validated by the parser, every texture slot resolved, tag100 round trip.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'track-coll2'))
sys.path.insert(0, str(HERE.parent / 'track-render1'))
import build_collision as bc  # noqa: E402
import build_render as br  # noqa: E402
import course_config as cc  # noqa: E402
import validate_collision as vc  # noqa: E402


def package(course, out_root, noise='plain', step=12.0, points=50000):
    t0 = time.time()
    coll_dx, _, coll_rep = bc.build(course, 'ps2')
    data, textures, render_rep = br.build(course, coll_dx, noise, 'all')
    if render_rep['vertices'] > 87479 or render_rep['indices'] > 227061:
        # two-sided everything would leave the retail range: fall back to two-sided PS2-only geometry (v3 rule), recorded in the report
        data, textures, render_rep = br.build(course, coll_dx, noise, 'ps2only')
        render_rep['two_sided_fallback'] = 'all -> ps2only (retail vertex/index range)'
    val = vc.validate(course, data, step, points)
    rel = course.pc_dx.relative_to(cc.PC_ROOT)
    root = out_root / course.name
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_bytes(data)
    for name, blob in textures.items():
        (root / rel.parent / (name + '.dxt')).write_bytes(blob)
    checks = {
        'collision_points_match_ps2': val['random_points']['mismatch'] == 0,
        'collision_columns_match_ps2': val['columns'].get('new_differs', 0) == 0,
        'render_triangles_equal_ps2': render_rep['triangle_multiset_equal_ps2'],
        'render_validated': render_rep['course_render_validated'],
        'textures_resolved': not render_rep['unresolved_texture_slots'],
        'tag100_round_trip': coll_rep['tree']['round_trip_identical'] and coll_rep['tree']['count_invariants_ok'],
        'no_negative_codes': coll_rep['tree']['negative_codes'] == 0,
        # PC stores 97 percent of its surface records facing down; a PS2 build must not differ by more than a few percent
        # retail ranges (all 36 retail course DX): at most 87,479 vertices (FranceM) and 227,061 local indices (FranceM)
        'within_retail_vertex_and_index_range': render_rep['vertices'] <= 87479 and render_rep['indices'] <= 227061,
        'surface_records_face_down': coll_rep['tag1400']['records_normal_down_fraction'] >= coll_rep['tag1400']['retail_records_normal_down_fraction'] - 0.05,
    }
    rep = {'course': course.name, 'noise': noise, 'checks': checks, 'all_checks_passed': all(checks.values()),
           'collision': coll_rep, 'render': render_rep, 'collision_validation': val, 'seconds': round(time.time() - t0, 1),
           'installed': False, 'runtime_checked': False}
    (root / 'package-report.json').write_text(json.dumps(rep, indent=1))
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--course')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--noise', choices=('plain', 'local'), default='plain')
    ap.add_argument('--summary', type=Path)
    a = ap.parse_args()
    courses = cc.courses() if a.all else [cc.course(a.course)]
    summary = {}
    for course in courses:
        try:
            rep = package(course, a.out, a.noise)
            summary[course.name] = {'checks': rep['checks'], 'all_checks_passed': rep['all_checks_passed'], 'seconds': rep['seconds'],
                                    'draws': rep['render']['draws'], 'vertices': rep['render']['vertices'], 'indices': rep['render']['indices'],
                                    'two_sided': {k: v for k, v in rep['render'].items() if k.startswith('tri_two_sided')},
                                    'two_sided_mode': rep['render']['two_sided_mode'], 'two_sided_fallback': rep['render'].get('two_sided_fallback'),
                                    'alpha_fields': {k: v for k, v in rep['render'].items() if 'alpha' in k},
                                    'root_outside_sectors': rep['render'].get('root_outside_sectors', 0),
                                    'root_outside_sectors_max_distance': rep['render'].get('root_outside_sectors_max_distance', 0),
                                    'noise_dropped': rep['render'].get('tri_noise_dropped_no_pc_uv', 0),
                                    'ps2_textures': sorted(k for k, v in rep['render']['textures'].items() if v['source'] == 'ps2')}
        except Exception as e:  # noqa: BLE001 - one course must not stop the others
            summary[course.name] = {'error': f'{type(e).__name__}: {e}', 'trace': traceback.format_exc()[-1500:]}
        print(course.name, json.dumps(summary[course.name])[:300], flush=True)
        if a.summary:
            a.summary.write_text(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
