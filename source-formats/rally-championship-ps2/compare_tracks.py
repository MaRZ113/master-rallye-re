"""Compare PC Rally Championship Xtreme stages with PS2 Rally Championship stages.

Both games store world vertices as float xyz records (PC .map: 32-byte records in
blocks, PS2 MAPxx.DAT: one 16-byte array of MapHeader.numMapVertices records).
Records are located by scanning for long runs of plausible coordinates; the 2-D
(XZ) occupancy grids are then matched by FFT cross-correlation over translation,
the four 90-degree rotations and an X mirror. A high overlap score means the same
terrain/road layout; scores are a research heuristic, not a byte identity.

Usage: python compare_tracks.py <pc levels dir> <ps2 maps dir> <out.json>
"""
import json
import struct
import sys
from pathlib import Path
import numpy as np

CELL = 8.0  # metres per grid cell


def runs(b, stride, lo=-20000.0, hi=20000.0, minrun=300):
    a = np.frombuffer(b[:len(b) // 4 * 4], dtype='<f4')
    out = []
    step = stride // 4
    for phase in range(step):
        v = a[phase:]
        n = len(v) // step
        if n < minrun:
            continue
        m = v[:n * step].reshape(n, step)[:, :3]
        good = np.all(np.isfinite(m), axis=1) & np.all((m > lo) & (m < hi), axis=1) \
            & (np.abs(m[:, 0]) > 1e-2) & (np.abs(m[:, 2]) > 1e-2)
        # split into runs
        idx = np.flatnonzero(np.diff(np.concatenate(([0], good.astype(np.int8), [0]))))
        for s, e in zip(idx[::2], idx[1::2]):
            if e - s >= minrun:
                out.append(m[s:e])
    return np.concatenate(out) if out else np.zeros((0, 3), np.float32)


def pc_points(path):
    b = path.read_bytes()
    lo = struct.unpack_from('<3f', b, 0x40)
    hi = struct.unpack_from('<3f', b, 0x4C)
    p = runs(b, 32)
    keep = np.all((p >= np.array(lo) - 1) & (p <= np.array(hi) + 1), axis=1)
    return p[keep], (lo, hi)


def ps2_points(path):
    b = path.read_bytes()
    nv = struct.unpack_from('<I', b, 1452)[0]
    p = runs(b, 16, minrun=min(nv, 300))
    return p, nv


def grid(p, rot, mirror):
    x, z = p[:, 0].astype(np.float64), p[:, 2].astype(np.float64)
    if mirror:
        x = -x
    for _ in range(rot):
        x, z = -z, x
    x = ((x - x.min()) / CELL).astype(int)
    z = ((z - z.min()) / CELL).astype(int)
    g = np.zeros((x.max() + 1, z.max() + 1), np.float32)
    g[x, z] = 1.0
    return g


def match(a, b):
    """Best overlap fraction of occupied cells of b on a, over integer shifts."""
    sh = (a.shape[0] + b.shape[0], a.shape[1] + b.shape[1])
    fa = np.fft.rfft2(a, sh)
    fb = np.fft.rfft2(b[::-1, ::-1], sh)
    c = np.fft.irfft2(fa * fb, sh)
    return float(c.max() / max(1.0, min(a.sum(), b.sum())))


def transform(p, rot, mirror):
    x, y, z = p[:, 0].astype(np.float64), p[:, 1].astype(np.float64), p[:, 2].astype(np.float64)
    if mirror:
        x = -x
    for _ in range(rot):
        x, z = -z, x
    return np.stack([x, y, z], 1)


def vertex_identity(pc, ps2, rot, mirror, tol=0.25):
    """Fraction of PS2 vertices that coincide with a PC vertex after a rigid
    translation (found by voting on pairwise offsets of a sample)."""
    q = transform(ps2, rot, mirror)
    p = pc.astype(np.float64)
    rng = np.random.default_rng(1)
    sp = p[rng.choice(len(p), min(len(p), 3000), replace=False)]
    sq = q[rng.choice(len(q), min(len(q), 3000), replace=False)]
    votes = {}
    for v in sq[:600]:
        d = np.round((sp - v) / tol).astype(np.int64)
        for t in map(tuple, d):
            votes[t] = votes.get(t, 0) + 1
    off = np.array(max(votes, key=votes.get), np.float64) * tol
    keys = set(map(tuple, np.round(p / tol).astype(np.int64)))
    moved = np.round((q + off) / tol).astype(np.int64)
    hit = 0
    for k in map(tuple, moved):
        if k in keys:
            hit += 1
    return hit / len(q), off.tolist()


def main():
    pc_dir, ps2_dir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    pcs = {}
    for d in sorted(pc_dir.iterdir()):
        m = next(d.glob('*.map'), None)
        if m:
            p, bb = pc_points(m)
            pcs[d.name] = (p, bb)
    ps2 = {}
    for f in sorted(ps2_dir.glob('MAP*.DAT')):
        p, nv = ps2_points(f)
        ps2[f.stem] = (p, nv)
    pc_grids = {k: grid(v[0], 0, False) for k, v in pcs.items() if len(v[0])}
    result = {'cell_m': CELL, 'pc': {}, 'ps2': {}, 'pairs': []}
    for k, (p, bb) in pcs.items():
        ext = (p.max(0) - p.min(0)).tolist() if len(p) else None
        result['pc'][k] = {'points': int(len(p)), 'extent_m': ext}
    for k, (p, nv) in ps2.items():
        ext = (p.max(0) - p.min(0)).tolist() if len(p) else None
        result['ps2'][k] = {'points': int(len(p)), 'header_vertices': nv, 'extent_m': ext}
        if not len(p):
            continue
        variants = [(r, m, grid(p, r, m)) for r in range(4) for m in (False, True)]
        scores = []
        for pk, pg in pc_grids.items():
            best = max((match(pg, g), r, m) for r, m, g in variants)
            scores.append({'pc': pk, 'score': round(best[0], 3), 'rot90': best[1], 'mirror_x': best[2]})
        scores.sort(key=lambda s: -s['score'])
        for s in scores[:3]:
            frac, off = vertex_identity(pcs[s['pc']][0], p, s['rot90'], s['mirror_x'])
            s['vertex_identity'] = round(frac, 3)
            s['offset'] = [round(x, 2) for x in off]
        scores[:3] = sorted(scores[:3], key=lambda s: -s['vertex_identity'])
        result['pairs'].append({'ps2': k, 'best': scores[:3]})
        print(k, scores[:2], flush=True)
    out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
