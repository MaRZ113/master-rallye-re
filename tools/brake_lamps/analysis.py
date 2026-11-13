"""Penetration / visibility analysis of authored brake-lamp ON layers against the car body."""
from __future__ import annotations

import numpy as np

from .geometry import Mesh, area_weighted_normal, closest_on_mesh, ray_hits, samples, view_directions

# A layer point closer than this behind an occluder along the view ray is depth-equal (z-fight band),
# not buried. 0.5 mm ~ the 24-bit depth resolution of the chase camera at a few metres.
DEPTH_TOLERANCE = 0.0005


def layer_visibility(layer: Mesh, occluders: Mesh, *, views=None, density=2, tolerance=DEPTH_TOLERANCE):
    """Per view: fraction of layer samples hidden by an occluder and the buried depth along the ray.

    A sample counts as hidden when an occluder is hit farther than ``tolerance`` along the ray toward the camera.
    Back-facing triangles are reported separately (native cull mode removes them).
    """
    views = views or view_directions()
    pts, tri = samples(layer, density)
    normals = layer.face_normals()
    out = {}
    per_sample_hidden = np.zeros(len(pts), dtype=int)
    depth_max = np.zeros(len(pts))
    for name, direction in views.items():
        # Start the ray at the sample itself; anything hit beyond the tolerance lies between it and the camera.
        t = ray_hits(pts, direction, occluders, t_min=tolerance)
        hidden = np.isfinite(t)
        per_sample_hidden += hidden
        facing = normals @ direction
        out[name] = {'hidden_fraction': round(float(hidden.mean()), 4) if len(pts) else 0.0,
                     'back_facing_triangles': int((facing < 0).sum()),
                     'triangles': int(len(layer.triangles))}
    # Buried depth: how far the sample lies behind the first surface seen from straight behind.
    rear = views.get('rear', next(iter(views.values())))
    t = ray_hits(pts, rear, occluders, t_min=tolerance)
    depth = np.where(np.isfinite(t), t, 0.0)
    return out, {'samples': pts, 'triangle': tri, 'hidden_views': per_sample_hidden, 'rear_depth': depth}


def lens_offsets(layer: Mesh, lens: Mesh):
    """Signed offset of each layer vertex from the OFF lens surface along the lens' outward normal (m)."""
    closest, tri, dist = closest_on_mesh(layer.positions, lens)
    n = lens.face_normals()[tri]
    signed = ((layer.positions - closest) * n).sum(axis=1)
    return signed, dist


def outward(lens: Mesh, rear_axis=(0.0, 0.0, -1.0)) -> np.ndarray:
    """Outward lens normal; oriented toward the rear when the lens winding is ambiguous."""
    n = area_weighted_normal(lens)
    return n if n @ np.asarray(rear_axis) >= 0 else -n


def oriented_face_normals(mesh: Mesh, out: np.ndarray) -> np.ndarray:
    n = mesh.face_normals()
    flip = (n @ out) < 0
    n[flip] *= -1
    return n


def summarise(car, *, views=None):
    occ = car.occluders()
    lens = car.mesh('off_glass')
    result = {'family': car.family, 'car_sha256': car.sha256, 'layers': {}}
    for role in ('on_core', 'on_glow'):
        layer = car.mesh(role)
        if not len(layer.triangles):
            continue
        vis, raw = layer_visibility(layer, occ, views=views)
        entry = {'views': vis,
                 'worst_view_hidden': max(v['hidden_fraction'] for v in vis.values()),
                 'rear_hidden': vis.get('rear', {}).get('hidden_fraction'),
                 'max_rear_buried_depth_mm': round(float(raw['rear_depth'].max()) * 1000, 2)}
        if len(lens.triangles):
            n = outward(lens)
            closest, tri, dist = closest_on_mesh(layer.positions, lens)
            fn = oriented_face_normals(lens, n)[tri]
            signed = ((layer.positions - closest) * fn).sum(axis=1)
            entry['lens_offset_mm'] = {'min': round(float(signed.min()) * 1000, 2), 'max': round(float(signed.max()) * 1000, 2),
                                       'below_lens_vertices': int((signed < -DEPTH_TOLERANCE).sum()), 'vertices': int(len(signed))}
        result['layers'][role] = entry
        result['layers'][role]['_raw'] = raw
    return result
