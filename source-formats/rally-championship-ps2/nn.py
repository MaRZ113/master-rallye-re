"""Small XZ nearest-neighbour helper (no scipy): hashed 1-m cells, 3x3 neighbourhood."""
import numpy as np


class NN2:
    def __init__(self, pts, cell=1.0):
        self.p, self.c = pts, cell
        k = np.floor(pts[:, [0, 2]] / cell).astype(np.int64)
        order = np.lexsort((k[:, 1], k[:, 0]))
        self.p = pts[order]
        ks = k[order]
        self.keys = ks[:, 0] * 2_000_003 + ks[:, 1]
        self.uk, self.start = np.unique(self.keys, return_index=True)
        self.end = np.append(self.start[1:], len(self.keys))

    def query(self, q):
        """distance (XZ) to nearest point within 1.5 cells, index; inf if none."""
        k = np.floor(q[:, [0, 2]] / self.c).astype(np.int64)
        best = np.full(len(q), np.inf); idx = np.full(len(q), -1)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                kk = (k[:, 0] + dx) * 2_000_003 + (k[:, 1] + dz)
                pos = np.searchsorted(self.uk, kk)
                ok = (pos < len(self.uk)) & (self.uk[np.minimum(pos, len(self.uk) - 1)] == kk)
                if not ok.any():
                    continue
                qi = np.flatnonzero(ok)
                s, e = self.start[pos[qi]], self.end[pos[qi]]
                maxlen = int((e - s).max())
                for j in range(maxlen):
                    m = s + j < e
                    if not m.any():
                        break
                    qq = qi[m]; pi = (s + j)[m]
                    d = np.hypot(*(q[qq][:, [0, 2]] - self.p[pi][:, [0, 2]]).T)
                    better = d < best[qq]
                    best[qq[better]] = d[better]; idx[qq[better]] = pi[better]
        return best, idx
