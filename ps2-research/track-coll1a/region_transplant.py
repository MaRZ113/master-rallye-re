"""Regional PS2 BSP -> PC tag100 transplant for one course DX (TRACK-COLL1A). Reusable: the course name, files and region are arguments.

    python region_transplant.py --bsp TURKEY3.BSP --retail-dx <retail turkey3.dx> --current-dx <TRACK-GROUND1 turkey3.dx> \
        --ranking ../track-ground1/collision-regions.json --rank 1 --out <dir> [--base-package <TRACK-GROUND1 package dir>]

The region is either --box x0 x1 y0 y1 z0 z1 or a ranked region of collision-regions.json (bounds + margin, y from 12 below the lowest PS2 contact to
3 above the highest). Nothing is installed anywhere; the output directory receives the candidate `turkey3.dx` (or the whole base package with only the
course DX replaced) and `transplant-report.json`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TD1 = HERE.parent / 'track-delta1'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TD1))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import bsp_region as br  # noqa: E402
import bsp_graft as bg  # noqa: E402
import region_validate as rv  # noqa: E402
import ps2_bsp  # noqa: E402
import tag100_tree as tt  # noqa: E402
from master_rallye.course_tag100 import parse_course_tag100_bytes  # noqa: E402
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes  # noqa: E402

TOL_CONTACT = 0.05


def load_tree(dx_bytes, name):
    sl = extract_tag100_from_dx_bytes(dx_bytes, name)
    return tt.Tree(sl.raw), sl


def region_from_ranking(path, rank, margin):
    r = json.loads(Path(path).read_text())['ranking'][rank - 1]
    cols = r['columns_table']
    x0, z0, x1, z1 = r['bounds_xz']
    heights = [c['ps2_bsp_contact'] for c in cols if c['ps2_bsp_contact'] is not None]
    return (x0 - margin, min(heights) - 12.0, z0 - margin), (x1 + margin, max(heights) + 3.0, z1 + margin), r


def build(retail_dx, current_dx, bsp, lo, hi, name='course.dx', method='graft'):
    """Returns (candidate dx bytes, report, trees). Raises (the current bytes are never modified) when a check fails."""
    sl_cur = extract_tag100_from_dx_bytes(current_dx, name)
    ref = tt.Tree(sl_cur.raw)           # untouched copy of the current tree
    cand = tt.Tree(sl_cur.raw)
    old, _ = load_tree(retail_dx, name)
    n0 = len(cand.plane)
    tr = (bg.transplant if method == 'graft' else br.transplant_brush)(cand, bsp, lo, hi)
    raw = cand.serialize()
    new_dx = current_dx[:sl_cur.tag_offset] + raw
    report = {'box_lo': list(lo), 'box_hi': list(hi), 'transplant': tr}

    # structure: round trip, invariants, codes, links changed only near the box
    again = tt.Tree(raw)
    parsed = parse_course_tag100_bytes(raw, 'cand', allow_trailing=True)
    changed = rv.changed_links(cand, ref.child, ref.sib, n0)
    near = rv.reachable_near_box(ref, lo, hi)
    added_codes = [c for c in cand.code[n0:] if c is not None]
    report['structure'] = {
        'round_trip_identical': again.serialize() == raw,
        'count_invariants_ok': all(parsed.count_invariants().values()),
        'header_before': list(ref.header), 'header_after': list(parsed.header_words),
        'tree_bytes_before': len(ref.serialize()), 'tree_bytes_after': len(raw),
        'tail_bytes_equal': again.tail == ref.tail,
        'dx_prefix_equal': new_dx[:sl_cur.tag_offset] == current_dx[:sl_cur.tag_offset],
        'changed_existing_links': len(changed),
        'changed_links_outside_box_subtrees': sum(1 for i, _ in changed if i not in near),
        'nodes_allocated': len(cand.plane) - n0,
        'added_plane_codes_distinct': sorted(set(added_codes)),
        'negative_codes_added': sum(1 for c in added_codes if c >= 0x80000000),
        'reachable_nodes_before': bg.reachable_nodes(ref), 'reachable_nodes_after': bg.reachable_nodes(cand),
        'node_growth_percent': round(100.0 * (bg.reachable_nodes(cand) - bg.reachable_nodes(ref)) / bg.reachable_nodes(ref), 3),
        'tree_bytes_growth_percent': round(100.0 * (len(raw) - len(ref.serialize())) / len(ref.serialize()), 3),
    }
    trees = {'original_pc': old, 'current_ground1': ref, 'candidate': cand}
    return new_dx, report, trees


def validate(bsp, lo, hi, trees, report):
    rows, contact = rv.first_contact_table(bsp, trees, lo, hi)
    n_cls, cls = rv.classification_table(bsp, trees, lo, hi, rows)
    rays = rv.region_rays(lo, hi)
    ray = {name: rv.ray_check(bsp, trees['current_ground1'], trees[name], lo, hi, rays) for name in ('candidate',)}
    n_out, out_diffs = rv.outside_sample_check(trees['current_ground1'], trees['candidate'], lo, hi)
    n_ring, ring_diffs = rv.boundary_ring_check(trees['current_ground1'], trees['candidate'], lo, hi)
    report['validation'] = {
        'first_contact_2_unit_grid': {'columns': len(rows), 'tolerance': TOL_CONTACT, 'per_tree': contact},
        'classification_samples': {'points': n_cls, 'per_tree': cls},
        'rays': {k: {'rays': v['rays'], 'crossing_box': v['rays_crossing_box'], 'inside_mismatch': len(v['inside_mismatch']), 'outside_mismatch': len(v['outside_mismatch']),
                     'first_inside_mismatches': v['inside_mismatch'][:5], 'first_outside_mismatches': v['outside_mismatch'][:5]} for k, v in ray.items()},
        'outside_points_compared': n_out, 'outside_points_changed': len(out_diffs), 'first_outside_changes': out_diffs[:5],
        'boundary_shell_points_compared': n_ring, 'boundary_shell_points_changed': len(ring_diffs), 'first_boundary_changes': ring_diffs[:5],
    }
    report['_rows'] = rows
    return report


def passed(report):
    v, s = report['validation'], report['structure']
    c = v['first_contact_2_unit_grid']['per_tree']['candidate']
    return {
        'first_contact_within_tolerance': c['agree'] == v['first_contact_2_unit_grid']['columns'],
        'classification_matches_ps2': v['classification_samples']['per_tree']['candidate']['mismatch'] == 0,
        'rays_inside_match_ps2': all(r['inside_mismatch'] == 0 for r in v['rays'].values()),
        'rays_outside_unchanged': all(r['outside_mismatch'] == 0 for r in v['rays'].values()),
        'no_change_outside_box': v['outside_points_changed'] == 0 and v['boundary_shell_points_changed'] == 0 and s['changed_links_outside_box_subtrees'] == 0,
        'tag100_valid': s['round_trip_identical'] and s['count_invariants_ok'] and s['tail_bytes_equal'] and s['dx_prefix_equal'],
        'codes_valid': s['negative_codes_added'] == 0,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bsp', type=Path, required=True)
    ap.add_argument('--retail-dx', type=Path, required=True)
    ap.add_argument('--current-dx', type=Path, required=True)
    ap.add_argument('--box', type=float, nargs=6, metavar=('X0', 'X1', 'Y0', 'Y1', 'Z0', 'Z1'))
    ap.add_argument('--ranking', type=Path)
    ap.add_argument('--rank', type=int, default=1)
    ap.add_argument('--margin', type=float, default=6.0)
    ap.add_argument('--base-package', type=Path, help='copy this package to --out and replace only the course DX in it')
    ap.add_argument('--dx-relpath', default='DataGx/Course/Turkey3/turkey3.dx')
    ap.add_argument('--method', choices=('graft', 'brush'), default='graft')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    if a.box:
        lo, hi, rinfo = (a.box[0], a.box[2], a.box[4]), (a.box[1], a.box[3], a.box[5]), None
    else:
        lo, hi, rinfo = region_from_ranking(a.ranking, a.rank, a.margin)
    bsp = ps2_bsp.parse(a.bsp.read_bytes())
    retail, current = a.retail_dx.read_bytes(), a.current_dx.read_bytes()
    new_dx, report, trees = build(retail, current, bsp, lo, hi, a.current_dx.name, a.method)
    validate(bsp, lo, hi, trees, report)
    report['checks'] = passed(report)
    report['all_checks_passed'] = all(report['checks'].values())
    rows = report.pop('_rows')
    report['region'] = rinfo and {k: rinfo[k] for k in ('rank', 'class', 'centroid_xz', 'bounds_xz', 'columns')}
    report['inputs'] = {'bsp_sha256': hashlib.sha256(a.bsp.read_bytes()).hexdigest()[:16], 'retail_dx_sha256': hashlib.sha256(retail).hexdigest()[:16],
                        'current_dx_sha256': hashlib.sha256(current).hexdigest()[:16]}
    report['output'] = {'dx_bytes': len(new_dx), 'dx_sha256': hashlib.sha256(new_dx).hexdigest()}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'transplant-report.json').write_text(json.dumps(report, indent=1))
    (a.out / 'first-contact-grid.json').write_text(json.dumps(rows, indent=0))
    if report['all_checks_passed']:
        if a.base_package:
            if a.out.resolve() == a.base_package.resolve():
                raise SystemExit('refusing to write into the base package')
            for src in a.base_package.rglob('*'):
                if src.is_file() and src.name != 'report.json':
                    dst = a.out / src.relative_to(a.base_package)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
            target = a.out / a.dx_relpath
        else:
            target = a.out / 'candidate.dx'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(new_dx)
    print(json.dumps({k: report[k] for k in ('transplant', 'structure', 'checks', 'all_checks_passed')}, indent=1))
    print(json.dumps(report['validation']['first_contact_2_unit_grid'], indent=1))
    print(json.dumps(report['validation']['classification_samples'], indent=1))
    if not report['all_checks_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
