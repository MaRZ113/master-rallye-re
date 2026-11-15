"""Exact replay of MR's gaLimitsAI test, and a guard that keeps it from resetting cars on the road.

Retail ``gaLimitsAI`` update (0x4CD9B0) and nearest-marker helper (0x4CE140), MRallye.exe
SHA-256 BF8AEF32...5F96B4:

* Each of the two lists of a pair (Left/Right Inner, then Left/Right Outer) is searched separately for the marker
  nearest to the car in 3-D (index ``n``). If ``0 < n < N-1`` and ``|P[n+1]-P[n]|^2 < |P[n+1]-car|^2``, ``n`` becomes
  ``n-1``; then ``n`` is clamped to ``0..N-3``.
* With ``cr(a, b, c) = (b.x-c.x)(b.z-a.z) - (b.z-c.z)(b.x-a.x)`` (X/Z only), the car is beyond the left list when
  ``cr(P[n], P[n+1], car) < 0`` AND ``cr(P[n+1], P[n+2], car) < 0``, and beyond the right list when both are ``> 0``.
  The two segments are infinite lines, so the test only holds near the nearest marker.
* Beyond either inner list -> the outer pair is tested the same way; beyond either outer list for 8 consecutive
  samples -> ``LimitState`` 2 (reset). Beyond the inner lists only -> state 1 ("OFF COURSE" on the HUD).

Two equal consecutive markers make ``cr`` exactly 0 for any car, so a triple that contains such a pair can never
classify the car as outside: :func:`guard` duplicates markers exactly where the replay finds the car "outside" while
it is on the road (folds on the inside of tight turns, the other leg's markers at crossings), and leaves the limits
untouched everywhere else.
"""
from __future__ import annotations

import numpy as np

PAIRS = (("LeftInnerLimit", "RightInnerLimit"), ("LeftOuterLimit", "RightOuterLimit"))


def nearest_index(P: np.ndarray, cars: np.ndarray) -> np.ndarray:
    N = len(P)
    d = ((cars[:, None, :] - P[None, :, :]) ** 2).sum(-1)
    n = d.argmin(1)                                   # first minimum, as the strict '<' scan
    mid = (n > 0) & (n < N - 1)
    nn = np.minimum(n + 1, N - 1)
    seg = ((P[nn] - P[n]) ** 2).sum(-1)
    to_car = ((P[nn] - cars) ** 2).sum(-1)
    n = np.where(mid & (seg < to_car), n - 1, n)
    n = np.where(n >= N - 2, N - 3, n)
    return np.maximum(n, 0)


def _cr(a, b, c):
    return (b[:, 0] - c[:, 0]) * (b[:, 2] - a[:, 2]) - (b[:, 2] - c[:, 2]) * (b[:, 0] - a[:, 0])


def beyond(P: np.ndarray, cars: np.ndarray, side: int):
    """(outside mask, index n) of cars against one list; side -1 = left, +1 = right."""
    if len(P) < 3:
        return np.zeros(len(cars), bool), np.zeros(len(cars), int)
    n = nearest_index(P, cars)
    c1, c2 = _cr(P[n], P[n + 1], cars), _cr(P[n + 1], P[n + 2], cars)
    out = (c1 < 0) & (c2 < 0) if side < 0 else (c1 > 0) & (c2 > 0)
    return out, n


def road_samples(line, offsets=(-10.0, -7.0, -4.0, -2.0, 0.0, 2.0, 4.0, 7.0, 10.0), step=1.0, lift=0.6):
    """Car positions along the route (every ``step`` m) at lateral offsets, ``lift`` m above the route points."""
    line = np.asarray(line, float)
    pts = []
    for a, b in zip(line[:-1], line[1:]):
        k = max(1, int(np.linalg.norm(b - a) / step))
        for t in range(k):
            pts.append(a + (b - a) * t / k)
    pts.append(line[-1])
    pts = np.array(pts)
    fwd = np.roll(pts, -3, 0) - np.roll(pts, 3, 0)
    fwd[:3] = pts[6] - pts[0]
    fwd[-3:] = pts[-1] - pts[-7]
    fwd[:, 1] = 0
    fwd /= np.linalg.norm(fwd, axis=1, keepdims=True) + 1e-9
    side = np.stack([fwd[:, 2], np.zeros(len(pts)), -fwd[:, 0]], 1)
    cars = np.concatenate([pts + side * o + np.array([0.0, lift, 0.0]) for o in offsets])
    return cars


def outside(lists: dict, cars: np.ndarray):
    """Per car: state as gaLimitsAI (0 inside inner, 1 inside outer, 2 outside outer), plus the triples to blame."""
    state = np.zeros(len(cars), int)
    blame = []
    test = np.ones(len(cars), bool)
    for level, (lname, rname) in enumerate(PAIRS):
        L, R = np.asarray(lists[lname], float), np.asarray(lists[rname], float)
        lo, ln = beyond(L, cars, -1)
        ro, rn = beyond(R, cars, 1)
        bad = test & (lo | ro)
        state[bad] = level + 1
        blame.append((lname, ln[bad & lo]))
        blame.append((rname, rn[bad & ro]))
        test = bad
    return state, blame


def guard(lists: dict, line, max_rounds: int = 60):
    """Duplicate markers until no road sample is outside the inner limits (so neither "OFF COURSE" nor a reset
    happens on the road). Returns (new lists, stats)."""
    cars = road_samples(line)
    work = {k: [[tuple(p), 1] for p in v] for k, v in lists.items()}

    def expand():
        return {k: np.array([p for p, c in v for _ in range(c)], float) for k, v in work.items()}

    def owner(name, idx):
        # expanded index -> entry index in work[name]
        acc = 0
        for e, (_, c) in enumerate(work[name]):
            if idx < acc + c:
                return e
            acc += c
        return len(work[name]) - 1

    first = None
    doubled = 0
    for _ in range(max_rounds):
        cur = expand()
        state, blame = outside(cur, cars)
        if first is None:
            first = {"on_road_off_course": int((state >= 1).sum()), "on_road_reset": int((state >= 2).sum())}
        if not (state >= 1).any():
            break
        for name, idx in blame:
            for n in sorted(set(int(i) for i in idx)):
                for k in (n, n + 1, n + 2):
                    e = owner(name, k)
                    if work[name][e][1] == 1:
                        work[name][e][1] = 2
                        doubled += 1
    cur = expand()
    state, _ = outside(cur, cars)
    stats = dict(first or {})
    stats.update({"markers_doubled": doubled, "after_off_course": int((state >= 1).sum()),
                  "after_reset": int((state >= 2).sum()), "samples": len(cars)})
    return {k: [tuple(map(float, p)) for p in v] for k, v in cur.items()}, stats
