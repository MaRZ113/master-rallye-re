"""Verify a patched loose turkey3.dx: PC collision ground height vs the PS2 ground (visual triangles) at the PS2 non-exact ground triangle centroids,
and unchanged collision elsewhere (random points compared with the retail tree)."""
import argparse
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ground_delta_probe as g  # noqa: E402
import ps2_terrain as terrain  # noqa: E402
import gcoll_columns as gc  # noqa: E402
import gcoll_walls_vs_limits as gw  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--retail-dx', type=Path, required=True)
    ap.add_argument('--patched-dx', type=Path, required=True)
    ap.add_argument('--samples', type=int, default=3000)
    a = ap.parse_args()
    scene, model, ps2_non, pc_non, pc_all = terrain.load_delta(a.ps2_root, a.retail_dx)
    grid = g.build_index(g.ground_triangles(scene))
    old = gc.pc_nodes(a.retail_dx)
    new = gc.pc_nodes(a.patched_dx)
    rnd = random.Random(3)
    sample = rnd.sample(ps2_non, min(a.samples, len(ps2_non)))
    before, after, none_ = [], [], 0
    for t in sample:
        x = sum(p[0] for p in t['p']) / 3
        z = sum(p[2] for p in t['p']) / 3
        ref = g.height_at(grid, x, z)
        h_old, h_new = gw.ground_at(old, x, z), gw.ground_at(new, x, z)
        if ref is None or h_old is None or h_new is None:
            none_ += 1
            continue
        before.append(abs(h_old - ref))
        after.append(abs(h_new - ref))
    before.sort()
    after.sort()

    def pct(v, q):
        return round(v[int(q * (len(v) - 1))], 3)
    print('samples', len(before), 'unresolved', none_)
    print('|PC - PS2| before patch percentiles 50/90/99:', pct(before, .5), pct(before, .9), pct(before, .99), ' within .1:', round(sum(x < .1 for x in before) / len(before), 3))
    print('|PC - PS2| after  patch percentiles 50/90/99:', pct(after, .5), pct(after, .9), pct(after, .99), ' within .1:', round(sum(x < .1 for x in after) / len(after), 3))
    xs = [p[0] for t in ps2_non for p in t['p']]
    zs = [p[2] for t in ps2_non for p in t['p']]
    changed = total = 0
    for _ in range(4000):
        x, z = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(zs), max(zs))
        h0, h1 = gw.ground_at(old, x, z), gw.ground_at(new, x, z)
        if h0 is None or h1 is None:
            continue
        total += 1
        changed += abs(h0 - h1) > 0.05
    print('random columns over the course box whose collision ground changed:', changed, 'of', total)


if __name__ == '__main__':
    main()
