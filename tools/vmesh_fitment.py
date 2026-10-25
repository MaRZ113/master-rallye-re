"""Alpha-aware offline wheel fitment diagnostics. Anchor positions remain explicitly supplied hypotheses."""
from __future__ import annotations

import math
from pathlib import Path
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt, decode_rgba_pixels, PNG_ROWS_FLIP_VERTICAL


def tyre_outline(model):
    """Convex Y/Z silhouette of the actual wheel vertices; the donor is slightly oval."""
    points = sorted(set((v[1], v[2]) for v in model.vertices.positions))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    def chain(seq):
        result = []
        for p in seq:
            while len(result) >= 2 and cross(result[-2], result[-1], p) <= 0:
                result.pop()
            result.append(p)
        return result
    hull = chain(points)[:-1] + chain(reversed(points))[:-1]
    if len(hull) < 3:
        raise ValueError("wheel has no nondegenerate Y/Z outline")
    return hull


def outline_depth(point, hull):
    """Positive inward distance to the closest outline edge; negative outside."""
    return min(((b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])) / math.dist(a, b)
               for a, b in zip(hull, hull[1:] + hull[:1]))


def material_clearance(family: Path, resource: str, draws, hubs, radius, half_width, subdivisions=16,
                       *, textures=None, fallback_family: Path | None = None):
    """Test a barycentric grid per triangle, respecting the actual serialized alpha selector and texture masks.

    Samples are bounded offline observations, not a collision proof. Count hidden mask samples separately. Supplied
    draws must include every generated body pool, rather than the donor's old paint draw only.
    """
    model = parse_dx_bytes((family / resource).read_bytes())
    wheel = parse_dx_bytes((family / "wheel.dx").read_bytes())
    outline = tyre_outline(wheel)
    samples, hidden, tested_draws, cache = [], 0, [], {}
    for draw_id in sorted(set(draws)):
        draw = model.physical_draws[draw_id]
        tested_draws.append(draw_id)
        name = draw.texture_slots[0].value
        if name not in cache:
            if textures is not None and name + ".dxt" in textures:
                cache[name] = textures[name + ".dxt"]
            else:
                path = family / (name + ".dxt")
                if not path.exists() and fallback_family is not None:
                    path = fallback_family / (name + ".dxt")
                tex = parse_dxt(path)
                cache[name] = tex.width, tex.height, decode_rgba_pixels(tex, PNG_ROWS_FLIP_VERTICAL)
        tw, th, pixels = cache[name]
        enabled, selector = (bool(v) for v in draw.flags_0x20[:2])
        for triangle in range(draw.triangle_count):
            ids = model.global_index_table.indices[draw.index_start + triangle * 3:draw.index_start + triangle * 3 + 3]
            ps = [model.vertices.positions[i] for i in ids]
            uv = [model.uv_sets[0].values[i] for i in ids]
            for i in range(subdivisions + 1):
                for j in range(subdivisions + 1 - i):
                    weights = (i / subdivisions, j / subdivisions, 1 - (i + j) / subdivisions)
                    u, v = (sum(weights[t] * uv[t][axis] for t in range(3)) for axis in range(2))
                    alpha = pixels[((math.floor((1 - v) * th) % th) * tw + math.floor(u * tw) % tw) * 4 + 3]
                    if enabled and alpha <= (128 if selector else 8):
                        hidden += 1
                        continue
                    samples.append(tuple(sum(weights[t] * ps[t][axis] for t in range(3)) for axis in range(3)))
    rows = []
    for hx, hy, hz in hubs:
        depths = (outline_depth((p[1] - hy, p[2] - hz), outline) for p in samples
                  if abs(p[0] - hx) <= half_width and abs(p[1] - hy) < radius * 1.1
                  and abs(p[2] - hz) < radius * 1.1)
        penetrations = [depth for depth in depths if depth > 0]
        rows.append({"hub": list((hx, hy, hz)), "visible_samples_inside_tyre": len(penetrations),
                     "max_sample_penetration_m": max(penetrations, default=0.0)})
    return {"method": "texture-aware barycentric grid against convex Y/Z tyre outline extruded across its width; not an exact 3D intersection proof",
            "subdivisions": subdivisions, "body_draws": tested_draws, "visible_samples": len(samples),
            "masked_samples_skipped": hidden, "radius": radius, "half_width": half_width,
            "actual_wheel_radial_envelope_m": max(math.hypot(v[1], v[2]) for v in wheel.vertices.positions),
            "tyre_outline_vertices": len(outline),
            "anchor_status": "H1 donor complete.dx anchors; race instancing remains unverified", "hubs": rows}


def scale_to_clear_samples(wheel_model, report, margin=0.002):
    """Conservative radial shrink bound for sampled protrusions of a convex wheel silhouette."""
    if not math.isfinite(margin) or margin < 0:
        raise ValueError("fitment margin must be finite and non-negative")
    depth = max(h["max_sample_penetration_m"] for h in report["hubs"])
    if depth <= 0:
        return 1.0
    hull = tyre_outline(wheel_model)
    support = outline_depth((0, 0), hull)
    factor = 1 - (depth + margin) / support
    if not 0.9 <= factor <= 1:
        raise ValueError("sampled fit would require more than 10 percent radial shrink; review anchors/body")
    return factor
