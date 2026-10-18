"""PS2 BSP vertical polygon-hit query versus visual ground height (Turkey3)."""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE))
import geometry_delta as g  # noqa: E402
import ps2_bsp  # noqa: E402
import bsp_query as q  # noqa: E402
from bsp_orientation import sample_faces  # noqa: E402


def main(ps2_root, pc_root, sdk, bsp_path, lift=3.0, depth=6.0):
    a, _, _ = g.load_pair(Path(ps2_root), Path(pc_root), Path(sdk), 'TURKEY3')
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    faces = sample_faces(a, limit=2000)
    res = Counter()
    firsts, anys = [], []
    for c, _n in faces:
        top = (c[0], c[1] + lift, c[2])
        bot = (c[0], c[1] - depth, c[2])
        hits = q.ps2_ray_hits(bsp, top, bot)
        ys = [top[1] + (bot[1] - top[1]) * t for t, _, _ in hits]
        contact = q.ps2_first_contact(bsp, top, bot)
        if contact is None:
            res['no contact'] += 1
            continue
        res['contact_' + contact[1]] += 1
        y_first = top[1] + (bot[1] - top[1]) * contact[0]
        firsts.append(y_first - c[1])
        anys.append(min(ys + [y_first], key=lambda y: abs(y - c[1])) - c[1])
        res['hit'] += 1
    def share(v, tol):
        return round(sum(abs(x) <= tol for x in v) / max(1, len(v)), 3)
    print(json.dumps({'samples': len(faces), **res,
                      'nearest_hit_within_0.05': share(anys, .05), 'nearest_hit_within_0.25': share(anys, .25),
                      'first_hit_within_0.05': share(firsts, .05), 'first_hit_within_0.25': share(firsts, .25),
                      'first_hit_above_ground_by_more_than_0.25': round(sum(x > .25 for x in firsts) / max(1, len(firsts)), 3)}, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:5])
