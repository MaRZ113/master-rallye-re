"""Conservative per-axis scaling of an existing finite tag101 hull."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import math
import struct
from typing import Sequence

from .bounds import compute_bounds1339, parse_bounds1339, replace_bounds1339
from .collision import ConvexHullTag101
from .collision_writer import (
    _aabb, _float32, _mean, _polygon_area, _require_translation_schema,
    replace_dx_tag101, serialize_tag101,
)
from .dx import parse_dx_bytes
from .dx_writer import ByteRange, audit_binary_diff
from .errors import CollisionWriteError


def _scaled(point, center, scales):
    return tuple(_float32(center[i] + scales[i] * (point[i] - center[i]),
                          f"scaled point axis {i}") for i in range(3))


def _rep_area(rep):
    return tuple(_float32(_polygon_area(rep.geometry_a.vertices, face.primary_indices),
                          "scaled face area") for face in rep.face_descriptors)


def scale_tag101(hull: ConvexHullTag101, scales: Sequence[float],
                 center: Sequence[float] | None = None) -> bytes:
    """Return same-size tag101 bytes; no index, adjacency or face-loop edits."""
    _require_translation_schema(hull)
    if len(scales) != 3 or any(not math.isfinite(v) or not 0 < v <= 10 for v in scales):
        raise CollisionWriteError("per-axis scale must contain three finite values in (0, 10]")
    scales = tuple(float(v) for v in scales)
    if center is None:
        center = hull.base_geometry.vertices[0]
    if len(center) != 3 or any(not math.isfinite(v) for v in center):
        raise CollisionWriteError("collision scale center must be a finite XYZ triple")
    center = tuple(float(v) for v in center)
    if scales == (1.0, 1.0, 1.0):
        return hull.raw
    source_a = hull.representation_a.geometry_a.vertices
    old_min, old_max = _aabb(source_a)
    detailed = tuple(_scaled(p, center, scales) for p in hull.representation_b.geometry_a.vertices)
    new_min, new_max = _aabb(detailed)
    corners = []
    for point in source_a:
        corner = []
        for axis in range(3):
            if abs(point[axis] - old_min[axis]) <= 1e-5:
                corner.append(new_min[axis])
            elif abs(point[axis] - old_max[axis]) <= 1e-5:
                corner.append(new_max[axis])
            else:
                raise CollisionWriteError("representation A is not an axis-aligned corner box")
        corners.append(tuple(corner))
    a_mean = tuple(_float32(v, "scaled A centroid") for v in _mean(corners))
    b_mean = tuple(_float32(v, "scaled B centroid") for v in _mean(detailed))
    a = replace(hull.representation_a,
                geometry_a=replace(hull.representation_a.geometry_a, vertices=tuple(corners)),
                geometry_b=replace(hull.representation_a.geometry_b, vertices=(a_mean,)))
    b = replace(hull.representation_b,
                geometry_a=replace(hull.representation_b.geometry_a, vertices=detailed),
                geometry_b=replace(hull.representation_b.geometry_b, vertices=(b_mean,)))
    a = replace(a, face_scalars=_rep_area(a))
    b = replace(b, face_scalars=_rep_area(b))
    radius = _float32(max(math.dist(point, a_mean) for point in corners), "scaled base radius")
    changed = replace(hull, base_geometry=replace(hull.base_geometry, vertices=(a_mean,)),
                      base_scalar=radius, representation_a=a, representation_b=b)
    output = serialize_tag101(changed)
    if len(output) != len(hull.raw):
        raise CollisionWriteError("tag101 scale changed serialized length")
    return output


def scale_dx_collision(template: bytes, scales: Sequence[float],
                       center: Sequence[float] | None = None) -> dict:
    """Scale one existing tag101, refresh bounds, reparse and audit all binary diffs."""
    model = parse_dx_bytes(template)
    hull = model.collision.convex_hull
    if hull is None or model.collision.errors:
        raise CollisionWriteError("DX has no validated tag101 hull")
    encoded = scale_tag101(hull, scales, center)
    if encoded == hull.raw:
        return {"data": template, "source_sha256": hashlib.sha256(template).hexdigest(),
                "output_sha256": hashlib.sha256(template).hexdigest(),
                "changed_byte_count": 0, "unexpected_diff_count": 0,
                "validation": "PASS", "bounds_recomputed": False}
    output = replace_dx_tag101(template, encoded)
    parsed = parse_dx_bytes(output)
    old_bounds = parse_bounds1339(model.collision.unparsed_data, model.collision.unparsed_offset)
    if old_bounds is None:
        raise CollisionWriteError("DX lacks marker-1339 bounds")
    new_bounds = compute_bounds1339(parsed.vertices.positions, parsed.collision.convex_hull,
                                    offset=parsed.collision.unparsed_offset)
    output = replace_bounds1339(output, new_bounds, footer_offset=parsed.collision.unparsed_offset)
    final = parse_dx_bytes(output)
    new_hull = final.collision.convex_hull
    if new_hull is None or final.collision.errors or not final.diagnostics.validated:
        raise CollisionWriteError("scaled DX failed full reparse")
    if final.vertices != model.vertices or final.uv_sets != model.uv_sets:
        raise CollisionWriteError("collision scale changed render attributes")
    if (final.local_indices != model.local_indices or final.physical_draws != model.physical_draws
            or final.global_index_table != model.global_index_table):
        raise CollisionWriteError("collision scale changed render topology/materials")
    for before, after in ((hull.representation_a, new_hull.representation_a),
                          (hull.representation_b, new_hull.representation_b)):
        for field in ("referenced_vertex_indices", "edges", "face_descriptors",
                      "edge_face_adjacency", "face_loop_indices"):
            if getattr(before, field) != getattr(after, field):
                raise CollisionWriteError(f"collision scale changed {field}")
        if before.geometry_a.triangles != after.geometry_a.triangles:
            raise CollisionWriteError("collision scale changed geometry triangles")
        for scalar, face in zip(after.face_scalars, after.face_descriptors):
            if abs(scalar - _polygon_area(after.geometry_a.vertices, face.primary_indices)) > 2e-5:
                raise CollisionWriteError("scaled face area failed validation")
    if model.collision.cylinder and model.collision.cylinder.raw != final.collision.cylinder.raw:
        raise CollisionWriteError("collision scale changed tag102")
    allowed = [ByteRange(old.vertex_data_offset, old.vertex_data_offset + 12 * old.vertex_count)
               for old in (hull.base_geometry, hull.representation_a.geometry_a,
                           hull.representation_a.geometry_b, hull.representation_b.geometry_a,
                           hull.representation_b.geometry_b)]
    allowed += [ByteRange(hull.base_scalar_offset, hull.base_scalar_offset + 4)]
    allowed += [ByteRange(rep.face_scalar_offset, rep.face_scalar_offset + 4 * rep.face_count)
                for rep in (hull.representation_a, hull.representation_b)]
    allowed += [ByteRange(model.collision.unparsed_offset + 4, model.collision.unparsed_offset + 44)]
    diff = audit_binary_diff(template, output, allowed)
    if not diff.valid:
        raise CollisionWriteError("collision scale changed bytes outside proven fields")
    return {"data": output, "source_sha256": hashlib.sha256(template).hexdigest(),
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "changed_byte_count": diff.changed_byte_count, "unexpected_diff_count": 0,
            "validation": "PASS", "bounds_recomputed": True,
            "old_bounds": old_bounds.to_dict(), "new_bounds": new_bounds.to_dict(),
            "scale": list(scales), "center": list(center if center is not None else hull.base_geometry.vertices[0])}
