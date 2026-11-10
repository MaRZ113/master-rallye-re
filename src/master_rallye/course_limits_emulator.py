"""Offline emulation of Retail ``gaLimitsAI`` classification (``FUN_004CD9B0``).

Reconstructed from the executable (R5T-INV E1.5):

* ``FUN_004CE140`` finds, per list, the marker nearest to the car in 3D
  (a +-24 marker window around the cached ordinal; a full scan every 15 ticks
  per car). If the next marker is closer to the selected one than to the car,
  the selection steps back by one; the result is clamped to ``0..n-3``.
* With selected ordinal ``c`` the test uses markers ``c, c+1, c+2`` in X/Z.
  For each segment ``(a, b)``: ``cross = (b.z - a.z)(b.x - px) - (b.x - a.x)(b.z - pz)``.
  Outside-left when both left crosses are ``< 0``; outside-right when both
  right crosses are ``> 0``.
* Inner lists are tested first; if outside them, the outer lists decide
  ``LimitState`` 1 (inside outer) or, after eight consecutive outside ticks, 2.

This lets generated limit lists be checked before a runtime test.
"""
from __future__ import annotations

from typing import Sequence

Vec3 = tuple[float, float, float]


def _select(markers: Sequence[Vec3], p: Vec3) -> int:
    n = len(markers)
    best, index = float("inf"), -1
    for i, m in enumerate(markers):
        d = (p[0] - m[0]) ** 2 + (p[1] - m[1]) ** 2 + (p[2] - m[2]) ** 2
        if d < best:
            best, index = d, i
    if 0 < index < n - 1:
        a, b = markers[index], markers[index + 1]
        if sum((b[k] - a[k]) ** 2 for k in range(3)) < sum((b[k] - p[k]) ** 2 for k in range(3)):
            index -= 1
    if index >= n - 2:
        index = n - 3
    return max(0, index)


def _cross(a: Vec3, b: Vec3, p: Vec3) -> float:
    return (b[2] - a[2]) * (b[0] - p[0]) - (b[0] - a[0]) * (b[2] - p[2])


def outside(left: Sequence[Vec3], right: Sequence[Vec3], p: Vec3) -> bool:
    i = _select(left, p)
    out_left = _cross(left[i], left[i + 1], p) < 0 and _cross(left[i + 1], left[i + 2], p) < 0
    j = _select(right, p)
    out_right = _cross(right[j], right[j + 1], p) > 0 and _cross(right[j + 1], right[j + 2], p) > 0
    return out_left or out_right


def limit_state(lists: dict[str, Sequence[Vec3]], p: Vec3) -> int:
    """0 inside inner, 1 inside outer only, 2 outside outer (ignoring the 8-tick delay)."""
    if not outside(lists["LeftInnerLimit"], lists["RightInnerLimit"], p):
        return 0
    if not outside(lists["LeftOuterLimit"], lists["RightOuterLimit"], p):
        return 1
    return 2


def scan_route(lists: dict[str, Sequence[Vec3]], route: Sequence[Vec3], lateral: Sequence[float] = (0.0,)) -> list[dict]:
    """LimitState along the RaceLine (optionally shifted sideways in X/Z)."""
    import math

    rows = []
    cum = 0.0
    for k, p in enumerate(route):
        if k:
            cum += math.dist(route[k - 1], p)
        a = route[max(0, k - 1)]
        b = route[min(len(route) - 1, k + 1)]
        dx, dz = b[0] - a[0], b[2] - a[2]
        n = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / n, dx / n
        for offset in lateral:
            q = (p[0] + nx * offset, p[1] + 1.0, p[2] + nz * offset)
            rows.append({"index": k, "along": round(cum, 1), "offset": offset, "state": limit_state(lists, q)})
    return rows
