"""Build the PS2 render section for every course and collect the checks (W2 on 36 courses).

    python run_all_render.py --summary render-36.json [--suffix-root <dir with W1 course DX files>] [--out <dir>]
Without --suffix-root the retail suffix is used (render-only check). With --out the DX and the PS2-only textures are written.
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_render as br  # noqa: E402
import course_config as cc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--summary', type=Path, required=True)
    ap.add_argument('--suffix-root', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    rows = {}
    for course in cc.courses():
        if a.only and course.name not in a.only:
            continue
        t0 = time.time()
        try:
            rel = course.pc_dx.relative_to(cc.PC_ROOT)
            suffix = (a.suffix_root / rel).read_bytes() if a.suffix_root else course.pc_dx.read_bytes()
            data, textures, rep = br.build(course, suffix)
            if a.out:
                (a.out / rel).parent.mkdir(parents=True, exist_ok=True)
                (a.out / rel).write_bytes(data)
                for name, blob in textures.items():
                    (a.out / rel.parent / (name + '.dxt')).write_bytes(blob)
            rep['seconds'] = round(time.time() - t0, 1)
            rows[course.name] = rep
            print(course.name, 'equal', rep['triangle_multiset_equal_ps2'], 'valid', rep['course_render_validated'], 'unresolved', rep['unresolved_texture_slots'],
                  'root (outside sectors)', rep.get('root_outside_sectors', 0), 'draws', rep['draws'], 'vertices', rep['vertices'], flush=True)
        except Exception as e:  # noqa: BLE001
            rows[course.name] = {'error': f'{type(e).__name__}: {e}', 'trace': traceback.format_exc()[-1500:]}
            print(course.name, 'ERROR', e, flush=True)
        a.summary.write_text(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
