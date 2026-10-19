"""Build and validate the full PS2 collision for every course; write a summary table (W1).

    python run_all.py --out <dir for the built DX files> --summary collision-36.json [--step 12] [--points 50000]
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_collision as bc  # noqa: E402
import course_config as cc  # noqa: E402
import validate_collision as vc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--summary', type=Path, required=True)
    ap.add_argument('--step', type=float, default=12.0)
    ap.add_argument('--points', type=int, default=50000)
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    rows = {}
    for course in cc.courses():
        if a.only and course.name not in a.only:
            continue
        t0 = time.time()
        try:
            dx, _, rep = bc.build(course, 'ps2')
            target = a.out / course.pc_dx.relative_to(cc.PC_ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(dx)
            val = vc.validate(course, dx, a.step, a.points)
            rows[course.name] = {'build': rep, 'validation': val, 'seconds': round(time.time() - t0, 1)}
            c = val['columns']
            print(course.name, 'points mismatch', val['random_points']['mismatch'], 'columns', c.get('columns'), 'new differs', c.get('new_differs', 0),
                  'retail differs', c.get('retail_differs', 0), 'codes', rep['tree']['code_provenance'], flush=True)
        except Exception as e:  # noqa: BLE001 - one course must not stop the others
            rows[course.name] = {'error': f'{type(e).__name__}: {e}', 'trace': traceback.format_exc()[-1500:]}
            print(course.name, 'ERROR', e, flush=True)
        a.summary.write_text(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
