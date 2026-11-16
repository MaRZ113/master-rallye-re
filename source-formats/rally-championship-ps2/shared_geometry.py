"""Exact PC/PS2 shared-geometry matrix.

Finding (manx1 vs MAP21): PS2 world = PC world with X negated, same origin, no
offset. So for every PC stage and PS2 map we measure, without any search, the
fraction of PC vertices that have a PS2 vertex within 0.1 m (XZ) and the
fraction of the PC road corridor cells (6 m) present in the PS2 map, and the
reverse (PS2 cells present in PC).

Usage: python shared_geometry.py <pc levels dir> <ps2 maps dir> <out.json>
"""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_tracks import pc_points, ps2_points
from nn import NN2


def cells(p, c=6.0):
    k = np.floor(p[:, [0, 2]] / c).astype(np.int64)
    return set((k[:, 0] * 2_000_003 + k[:, 1]).tolist())


def main():
    pc_dir, ps2_dir, out = map(Path, sys.argv[1:4])
    pcs = {d.name: pc_points(next(d.glob('*.map')))[0].astype(np.float64)
           for d in sorted(pc_dir.iterdir()) if next(d.glob('*.map'), None)}
    ps2 = {}
    for f in sorted(ps2_dir.glob('MAP*.DAT')):
        p = ps2_points(f)[0].astype(np.float64)
        p[:, 0] = -p[:, 0]
        ps2[f.stem] = p
    pcc = {k: cells(v) for k, v in pcs.items()}
    psc = {k: cells(v) for k, v in ps2.items()}
    trees = {k: NN2(v, 1.0) for k, v in ps2.items()}
    res = {}
    for name, p in pcs.items():
        rows = []
        for k in ps2:
            inter = len(pcc[name] & psc[k])
            if inter < 0.05 * len(pcc[name]):
                continue
            d, _ = trees[k].query(p)
            rows.append({'ps2': k, 'vertex_exact': round(float(np.mean(d < 0.1)), 3),
                         'pc_cells_in_ps2': round(inter / len(pcc[name]), 3),
                         'ps2_cells_in_pc': round(inter / len(psc[k]), 3)})
        rows.sort(key=lambda r: -r['pc_cells_in_ps2'])
        res[name] = rows[:4]
        print(name, [(r['ps2'], r['pc_cells_in_ps2'], r['ps2_cells_in_pc'], r['vertex_exact']) for r in rows[:3]], flush=True)
    out.write_text(json.dumps(res, indent=1) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
