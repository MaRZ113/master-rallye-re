"""Which PS2 map contains each PC stage?

For every PC stage x PS2 map x 8 orientations (4 x 90 degrees, X mirror) the XZ
occupancy grids are cross-correlated (FFT). Coverage = covered PC cells / PC cells.
The best pair is then checked exactly: a rigid offset is voted near the FFT peak
and the fraction of PC vertices that have a PS2 vertex within TOL metres (3-D)
is reported. Identity close to 1 = the PC stage geometry is a cut of that PS2 map.

Usage: python coverage_matrix.py <pc levels dir> <ps2 maps dir> <out.json>
"""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_tracks import pc_points, ps2_points, transform

CELL, TOL = 6.0, 0.15


def trim(p):
    lo, hi = np.percentile(p, 0.5, 0), np.percentile(p, 99.5, 0)
    return p[np.all((p >= lo) & (p <= hi), 1)].astype(np.float64)


def grid(p):
    mn = p.min(0)
    x = ((p[:, 0] - mn[0]) / CELL).astype(int)
    z = ((p[:, 2] - mn[2]) / CELL).astype(int)
    g = np.zeros((x.max() + 1, z.max() + 1), np.float32)
    g[x, z] = 1
    return g, mn


def best_shift(a, b):
    sh = (a.shape[0] + b.shape[0], a.shape[1] + b.shape[1])
    c = np.fft.irfft2(np.fft.rfft2(a, sh) * np.fft.rfft2(b[::-1, ::-1], sh), sh)
    i = np.unravel_index(np.argmax(c), c.shape)
    return c[i] / a.sum(), (i[0] - (b.shape[0] - 1), i[1] - (b.shape[1] - 1))


def key(p, tol):
    k = np.round(p / tol).astype(np.int64)
    return (k[:, 0] * 1_000_003 + k[:, 1]) * 1_000_033 + k[:, 2]


def identity(pc, q, coarse):
    """coarse = approximate XZ offset; vote the exact 3-D offset, then hit fraction."""
    rng = np.random.default_rng(0)
    a = pc[rng.choice(len(pc), min(len(pc), 4000), replace=False)]
    b = q[rng.choice(len(q), min(len(q), 4000), replace=False)]
    best, bestn = None, 0
    for v in a[:400]:
        d = v - b
        m = (np.abs(d[:, 0] - coarse[0]) < 2 * CELL) & (np.abs(d[:, 2] - coarse[1]) < 2 * CELL)
        if not m.any():
            continue
        dk = np.round(d[m] / TOL).astype(np.int64)
        u, c = np.unique(dk, axis=0, return_counts=True)
        # accumulate by refining over all candidates of this sample
        for row, n in zip(u, c):
            pass
        if best is None:
            best = {}
        for row in map(tuple, dk):
            best[row] = best.get(row, 0) + 1
    if not best:
        return 0.0, None
    off = np.array(max(best, key=best.get), np.float64) * TOL
    qs = set(key(q + off, TOL).tolist())
    hits = np.fromiter((k in qs for k in key(pc, TOL).tolist()), bool, len(pc))
    return float(hits.mean()), off.tolist()


def main():
    pc_dir, ps2_dir, out = map(Path, sys.argv[1:4])
    pcs = {}
    for d in sorted(pc_dir.iterdir()):
        m = next(d.glob('*.map'), None)
        if m:
            pcs[d.name] = trim(pc_points(m)[0])
    ps2 = {f.stem: trim(ps2_points(f)[0]) for f in sorted(ps2_dir.glob('MAP*.DAT'))}
    variants = {}
    for k, p in ps2.items():
        for rot in range(4):
            for mir in (False, True):
                q = transform(p, rot, mir)
                variants[(k, rot, mir)] = (q, *grid(q))
    res = {}
    for name, p in pcs.items():
        ga, mna = grid(p)
        rows = []
        for (k, rot, mir), (q, gb, mnb) in variants.items():
            cov, (sx, sz) = best_shift(ga, gb)
            rows.append((cov, k, rot, mir, (sx * CELL + mna[0] - mnb[0], sz * CELL + mna[2] - mnb[2])))
        rows.sort(key=lambda r: -r[0])
        top = []
        seen = set()
        for cov, k, rot, mir, coarse in rows:
            if k in seen:
                continue
            seen.add(k)
            ident, off = identity(p, variants[(k, rot, mir)][0], coarse) if len(top) < 2 else (None, None)
            top.append({'ps2': k, 'coverage': round(float(cov), 3), 'rot90': rot, 'mirror_x': mir,
                        'identity': None if ident is None else round(ident, 3), 'offset': off})
            if len(top) == 4:
                break
        res[name] = top
        print(name, [(t['ps2'], t['coverage'], t['identity']) for t in top], flush=True)
    out.write_text(json.dumps({'cell_m': CELL, 'tol_m': TOL, 'pc': res}, indent=1) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
