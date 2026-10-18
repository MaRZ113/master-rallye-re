"""Turkey3: how do the PS2 Left/RightOuterLimit2 lists relate to the four PC limit lists? (distance from each marker to the nearest marker / polyline of another list)."""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import course_delta as cd  # noqa: E402
import gcoll_map as gm  # noqa: E402


def seg_dist(p, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dz * dz
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / l2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz)


def poly_dist(p, pts):
    return min(seg_dist(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def stats(vals):
    v = sorted(vals)
    return {'n': len(v), 'median': round(v[len(v) // 2], 1), 'p90': round(v[int(.9 * (len(v) - 1))], 1), 'max': round(v[-1], 1)}


def main(pc_scene, ps2_scene, sdk_path, out):
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pc = Path(pc_scene).read_bytes()
    ps2 = Path(ps2_scene).read_bytes()
    route = gm.markers(sdk, pc, 'RaceLine')
    sets = {f'PC {n}': gm.markers(sdk, pc, n) for n in ('LeftOuterLimit', 'RightOuterLimit', 'LeftInnerLimit', 'RightInnerLimit')}
    sets.update({f'PS2 {n}': gm.markers(sdk, ps2, n) for n in ('LeftOuterLimit2', 'RightOuterLimit2')})
    res = {'sizes': {k: len(v) for k, v in sets.items()}, 'distance_to_route': {k: stats([min(math.dist(p, r) for r in route) for p in v]) for k, v in sets.items() if v}}
    pairs = {}
    for a in ('PS2 LeftOuterLimit2', 'PS2 RightOuterLimit2'):
        for b in [k for k in sets if k.startswith('PC ') and sets[k]]:
            pairs[f'{a} -> polyline of {b}'] = stats([poly_dist(p, sets[b]) for p in sets[a]])
    res['ps2_to_pc_polyline'] = pairs
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:5])
