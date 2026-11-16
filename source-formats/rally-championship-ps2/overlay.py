"""Overlay a PS2 map on a PC map after the best grid alignment (red = PC, green = PS2).
python overlay.py <pc.map> <ps2.DAT> <out.png> [scale]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_tracks import pc_points, ps2_points, grid, CELL, transform

pc = pc_points(Path(sys.argv[1]))[0].astype(np.float64)
ps = ps2_points(Path(sys.argv[2]))[0].astype(np.float64)
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
ps = ps * scale
# trim outliers
def trim(p):
    lo, hi = np.percentile(p, 0.5, 0), np.percentile(p, 99.5, 0)
    return p[np.all((p >= lo) & (p <= hi), 1)]
pc, ps = trim(pc), trim(ps)
best = None
for rot in range(4):
    for mir in (False, True):
        q = transform(ps, rot, mir)
        a = grid(pc, 0, False); b = grid(q, 0, False)
        sh = (a.shape[0] + b.shape[0], a.shape[1] + b.shape[1])
        c = np.fft.irfft2(np.fft.rfft2(a, sh) * np.fft.rfft2(b[::-1, ::-1], sh), sh)
        i = np.unravel_index(np.argmax(c), c.shape)
        sc = c[i] / min(a.sum(), b.sum())
        if best is None or sc > best[0]:
            dx = (i[0] - (b.shape[0] - 1)) * CELL + pc[:, 0].min() - q[:, 0].min()
            dz = (i[1] - (b.shape[1] - 1)) * CELL + pc[:, 2].min() - q[:, 2].min()
            best = (sc, rot, mir, q + np.array([dx, 0, dz]))
sc, rot, mir, q = best
print('score %.3f rot %d mirror %s' % (sc, rot, mir))
allp = np.concatenate([pc, q]); S = 700
mn = allp.min(0); s = max(np.ptp(allp[:, 0]), np.ptp(allp[:, 2]))
img = np.zeros((S, S, 3), np.uint8)
for p, col in ((pc, (255, 60, 60)), (q, (60, 255, 60))):
    u = ((p[:, 0] - mn[0]) / s * (S - 1)).astype(int); v = ((p[:, 2] - mn[2]) / s * (S - 1)).astype(int)
    img[S - 1 - v, u] = np.maximum(img[S - 1 - v, u], np.array(col, np.uint8))
Image.fromarray(img).save(sys.argv[3])
