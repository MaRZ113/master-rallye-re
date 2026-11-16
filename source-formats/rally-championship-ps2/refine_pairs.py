"""ICP-refine candidate PC/PS2 pairs from coverage_matrix output and report the
fraction of PC vertices within 0.1 / 0.5 m (XZ) of PS2 vertices.
python refine_pairs.py <pc levels dir> <ps2 maps dir> <coverage.json> [top_n]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_tracks import pc_points, ps2_points, transform
from coverage_matrix import trim, grid, best_shift, CELL
from nn import NN2

pc_dir, ps2_dir, cov = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text())
top = int(sys.argv[4]) if len(sys.argv) > 4 else 2
for name, rows in cov['pc'].items():
    pc = trim(pc_points(next((pc_dir / name).glob('*.map')))[0])
    out = []
    for r in rows[:top]:
        q = transform(trim(ps2_points(ps2_dir / (r['ps2'] + '.DAT'))[0]), r['rot90'], r['mirror_x'])
        ga, mna = grid(pc); gb, mnb = grid(q); _, (sx, sz) = best_shift(ga, gb)
        off = np.array([sx * CELL + mna[0] - mnb[0], 0.0, sz * CELL + mna[2] - mnb[2]])
        for _ in range(8):
            t = NN2(q + off, 4.0); d, i = t.query(pc); m = d < 4
            if m.sum() < 10: break
            off += [np.median(pc[m, 0] - t.p[i[m], 0]), 0, np.median(pc[m, 2] - t.p[i[m], 2])]
        d, _ = NN2(q + off, 1.0).query(pc)
        out.append((r['ps2'], round(float(np.mean(d < 0.1)), 3), round(float(np.mean(d < 0.5)), 3)))
    print(name, out, flush=True)
