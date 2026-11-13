"""Mesh math for brake-lamp authoring: ray/triangle tests, surface projection, view sets.

Pure numpy; no Master Rallye bytes or SDK imports. Coordinates are native car.dx
model space: +X right, +Y up, +Z forward (the tail lamps sit at the most negative Z).
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

EPS = 1e-9


@dataclass(frozen=True)
class Mesh:
    """Triangle soup in model space. ``positions`` (N,3) float64, ``triangles`` (M,3) int."""
    positions: np.ndarray
    triangles: np.ndarray

    @staticmethod
    def of(positions, triangles) -> 'Mesh':
        p = np.asarray(positions, dtype=np.float64).reshape(-1, 3)
        t = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
        if len(t) and (t.min() < 0 or t.max() >= len(p)):
            raise ValueError('triangle index outside vertex range')
        return Mesh(p, t)

    def corners(self) -> np.ndarray:
        """(M,3,3) triangle corner positions."""
        return self.positions[self.triangles]

    def face_normals(self) -> np.ndarray:
        c = self.corners()
        n = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0])
        length = np.linalg.norm(n, axis=1, keepdims=True)
        return np.divide(n, length, out=np.zeros_like(n), where=length > EPS)

    def areas(self) -> np.ndarray:
        c = self.corners()
        return .5 * np.linalg.norm(np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]), axis=1)

    def merged(self, other: 'Mesh') -> 'Mesh':
        return Mesh(np.vstack([self.positions, other.positions]), np.vstack([self.triangles, other.triangles + len(self.positions)]))

    def bounds(self):
        return self.positions.min(axis=0), self.positions.max(axis=0)


def merge(meshes) -> Mesh:
    meshes = [m for m in meshes if len(m.triangles)]
    if not meshes:
        return Mesh(np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64))
    out = meshes[0]
    for m in meshes[1:]:
        out = out.merged(m)
    return out


def area_weighted_normal(mesh: Mesh) -> np.ndarray:
    c = mesh.corners()
    n = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]).sum(axis=0)
    length = np.linalg.norm(n)
    if length < EPS:
        raise ValueError('degenerate surface has no normal')
    return n / length


def ray_hits(origins: np.ndarray, direction: np.ndarray, mesh: Mesh, *, t_min=0.0, chunk=4096) -> np.ndarray:
    """Distance to the first triangle hit along ``direction`` (one shared or per-ray) per origin; inf when none.

    Both triangle faces count (an occluder hides regardless of winding). Möller–Trumbore, vectorised.
    """
    origins = np.asarray(origins, dtype=np.float64).reshape(-1, 3)
    d = np.asarray(direction, dtype=np.float64)
    d = np.broadcast_to(d.reshape(-1, 3), origins.shape) if d.size == 3 or d.shape[0] == len(origins) else None
    if d is None:
        raise ValueError('direction must be one vector or one per origin')
    best = np.full(len(origins), np.inf)
    if not len(mesh.triangles) or not len(origins):
        return best
    c = mesh.corners()
    v0, e1, e2 = c[:, 0], c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]
    for at in range(0, len(origins), chunk):
        o = origins[at:at + chunk, None, :]
        dd = d[at:at + chunk, None, :]
        p = np.cross(dd, e2[None])
        det = np.einsum('rtk,tk->rt', p, e1)
        ok = np.abs(det) > 1e-14
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        s = o - v0[None]
        u = np.einsum('rtk,rtk->rt', s, p) * inv
        q = np.cross(s, e1[None])
        v = np.einsum('rtk,rtk->rt', dd, q) * inv
        t = np.einsum('tk,rtk->rt', e2, q) * inv
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > t_min)
        t = np.where(hit, t, np.inf)
        best[at:at + chunk] = t.min(axis=1)
    return best


def closest_on_mesh(points: np.ndarray, mesh: Mesh):
    """Closest point on the mesh surface for each point: (closest (N,3), triangle index (N,), distance (N,))."""
    points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    c = mesh.corners()
    a, b, cc = c[:, 0][None], c[:, 1][None], c[:, 2][None]
    p = points[:, None, :]
    # Ericson, Real-Time Collision Detection 5.1.5, vectorised over (points, triangles).
    ab, ac, ap = b - a, cc - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b
    d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - cc
    d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    denom = va + vb + vc
    safe = lambda x: np.where(np.abs(x) > 1e-18, x, 1e-18)
    v = vb / safe(denom)
    w = vc / safe(denom)
    result = a + ab * v[..., None] + ac * w[..., None]
    # Edge and vertex regions, applied from least to most specific.
    t_bc = (d4 - d3) / safe((d4 - d3) + (d5 - d6))
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    result = np.where(m[..., None], b + (cc - b) * t_bc[..., None], result)
    t_ac = d2 / safe(d2 - d6)
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    result = np.where(m[..., None], a + ac * t_ac[..., None], result)
    t_ab = d1 / safe(d1 - d3)
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    result = np.where(m[..., None], a + ab * t_ab[..., None], result)
    m = (d6 >= 0) & (d5 <= d6)
    result = np.where(m[..., None], np.broadcast_to(cc, result.shape), result)
    m = (d3 >= 0) & (d4 <= d3)
    result = np.where(m[..., None], np.broadcast_to(b, result.shape), result)
    m = (d1 <= 0) & (d2 <= 0)
    result = np.where(m[..., None], np.broadcast_to(a, result.shape), result)
    dist = np.linalg.norm(result - p, axis=-1)
    tri = dist.argmin(axis=1)
    rows = np.arange(len(points))
    return result[rows, tri], tri, dist[rows, tri]


def samples(mesh: Mesh, density=2):
    """Barycentric samples per triangle (vertices excluded, centroid + interior grid) and their triangle index."""
    weights = []
    n = density + 1
    for i in range(n + 1):
        for j in range(n + 1 - i):
            k = n - i - j
            if min(i, j, k) == 0 and density > 0:
                continue
            weights.append((i / n, j / n, k / n))
    if not weights:
        weights = [(1 / 3, 1 / 3, 1 / 3)]
    w = np.array(weights)
    c = mesh.corners()
    pts = np.einsum('sk,tkd->tsd', w, c).reshape(-1, 3)
    tri = np.repeat(np.arange(len(mesh.triangles)), len(w))
    return np.vstack([pts, mesh.positions]), np.concatenate([tri, np.full(len(mesh.positions), -1)])


def rotation_matrix(degrees_xyz) -> np.ndarray:
    """Rotation applied X then Y then Z (degrees), right-handed."""
    rx, ry, rz = (math.radians(a) for a in degrees_xyz)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Z @ Y @ X


def view_directions(count=8, *, rear_axis=(0.0, 0.0, -1.0)) -> dict:
    """Camera directions (from the lamp toward the camera) around the car rear.

    Eight viewpoints: straight rear, rear ±30° and ±60° yaw, rear high (25° up), rear low (10° down)
    and chase camera (rear, 12° up). These are the angles a following car or the chase/replay camera sees.
    """
    r = np.asarray(rear_axis, dtype=np.float64)
    if abs(r[1]) > 1e-6:
        raise ValueError('rear axis must be horizontal')
    def look(yaw, pitch):
        yaw, pitch = math.radians(yaw), math.radians(pitch)
        base = np.array([r[0] * math.cos(yaw) + r[2] * math.sin(yaw), 0.0, -r[0] * math.sin(yaw) + r[2] * math.cos(yaw)])
        v = base * math.cos(pitch) + np.array([0.0, math.sin(pitch), 0.0])
        return v / np.linalg.norm(v)
    # Yaw sign follows +X (yaw +30 puts the camera on the -X side); no left/right claim is made here.
    table = {'rear': (0, 0), 'yaw+30': (30, 0), 'yaw-30': (-30, 0), 'yaw+60': (60, 0),
             'yaw-60': (-60, 0), 'high_25': (0, 25), 'low_10': (0, -10), 'chase_12': (0, 12)}
    items = list(table.items())[:count]
    return {name: look(*angles) for name, angles in items}
