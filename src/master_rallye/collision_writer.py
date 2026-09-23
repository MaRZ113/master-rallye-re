"""Exact tag-101 serializer and conservative translation-only DX patcher."""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Sequence

from .collision import (
    CollisionGeometryBlock,
    ConvexHullRepresentation,
    ConvexHullTag101,
    TAG_CONVEX_HULL,
    parse_collision_sections,
)
from .dx import parse_dx_bytes
from .dx_writer import BinaryDiffAudit, ByteRange, audit_binary_diff
from .errors import CollisionWriteError
from .model import DxModel


TRANSLATED_GEOMETRY_PATHS = (
    "base_geometry",
    "representation_a.geometry_a",
    "representation_a.geometry_b",
    "representation_b.geometry_a",
    "representation_b.geometry_b",
)


@dataclass(frozen=True)
class CollisionFieldChange:
    field_path: str
    vertex_index: int
    source_offset: int
    old_value: tuple[float, float, float]
    new_value: tuple[float, float, float]
    changed_byte_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "field_path": self.field_path,
            "vertex_index": self.vertex_index,
            "source_offset": self.source_offset,
            "source_offset_hex": f"0x{self.source_offset:X}",
            "old_value": list(self.old_value),
            "new_value": list(self.new_value),
            "changed_byte_count": self.changed_byte_count,
        }


@dataclass(frozen=True)
class Tag101TranslationResult:
    data: bytes
    original: ConvexHullTag101
    translated: ConvexHullTag101
    delta: tuple[float, float, float]
    changes: tuple[CollisionFieldChange, ...]
    diff: BinaryDiffAudit
    validation: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "delta": list(self.delta),
            "source_sha256": self.original.sha256,
            "output_sha256": self.translated.sha256,
            "changed_fields": [item.to_dict() for item in self.changes],
            "diff": self.diff.to_dict(),
            "validation": self.validation,
        }


@dataclass(frozen=True)
class DxCollisionPatchResult:
    data: bytes
    source_sha256: str
    output_sha256: str
    translation: Tag101TranslationResult
    diff: BinaryDiffAudit
    original_model: DxModel
    output_model: DxModel
    preserved_section_hashes: dict[str, object]

    @property
    def byte_identical(self) -> bool:
        return self.source_sha256 == self.output_sha256

    def to_dict(self) -> dict[str, object]:
        return {
            "source_sha256": self.source_sha256,
            "output_sha256": self.output_sha256,
            "translation": self.translation.to_dict(),
            "changed_byte_count": self.diff.changed_byte_count,
            "changed_ranges": [item.to_dict() for item in self.diff.changed_ranges],
            "unexpected_diff_count": sum(item.size for item in self.diff.unexpected_ranges),
            "parser_status": "PASS" if self.output_model.diagnostics.validated else "FAIL",
            "tag101_validation_status": (
                "PASS" if self.output_model.collision.validated else "FAIL"
            ),
            "visual_geometry_changed_bytes": 0,
            "preserved_section_hashes": self.preserved_section_hashes,
        }


def _pack_i32(values: Iterable[int]) -> bytes:
    values = tuple(int(value) for value in values)
    return struct.pack(f"<{len(values)}i", *values) if values else b""


def _serialize_geometry(geometry: CollisionGeometryBlock) -> bytes:
    output = bytearray(struct.pack("<2i", geometry.vertex_count, geometry.triangle_count))
    for vertex in geometry.vertices:
        if len(vertex) != 3:
            raise CollisionWriteError("geometry vertex is not an XYZ triple")
        try:
            output += struct.pack("<3f", *vertex)
        except (OverflowError, struct.error) as error:
            raise CollisionWriteError("geometry vertex is not representable as float32") from error
    for triangle in geometry.triangles:
        if len(triangle) != 3:
            raise CollisionWriteError("geometry triangle is not an index triple")
        output += _pack_i32(triangle)
    return bytes(output)


def _serialize_representation(representation: ConvexHullRepresentation) -> bytes:
    output = bytearray(_serialize_geometry(representation.geometry_a))
    output += _serialize_geometry(representation.geometry_b)
    output += struct.pack("<i", len(representation.referenced_vertex_indices))
    output += _pack_i32(representation.referenced_vertex_indices)
    output += struct.pack("<i", len(representation.edges))
    for edge in representation.edges:
        output += _pack_i32(edge)
    output += struct.pack("<i", representation.face_count)
    for descriptor in representation.face_descriptors:
        output += struct.pack("<i", len(descriptor.primary_indices))
        output += _pack_i32(descriptor.primary_indices)
        output += struct.pack("<i", len(descriptor.secondary_indices))
        output += _pack_i32(descriptor.secondary_indices)
    for pair in representation.edge_face_adjacency:
        output += _pack_i32(pair)
    for loop in representation.face_loop_indices:
        output += struct.pack("<i", len(loop))
        output += _pack_i32(loop)
    for scalar in representation.face_scalars:
        try:
            output += struct.pack("<f", scalar)
        except (OverflowError, struct.error) as error:
            raise CollisionWriteError("face scalar is not representable as float32") from error
    return bytes(output)


def serialize_tag101(hull: ConvexHullTag101) -> bytes:
    """Serialize the parsed tag-101 object without reordering any collection."""
    output = bytearray(struct.pack("<I", TAG_CONVEX_HULL))
    output += _serialize_geometry(hull.base_geometry)
    try:
        output += struct.pack("<f", hull.base_scalar)
    except (OverflowError, struct.error) as error:
        raise CollisionWriteError("base scalar is not representable as float32") from error
    output += _serialize_representation(hull.representation_a)
    output += _serialize_representation(hull.representation_b)
    encoded = bytes(output)
    try:
        reparsed = parse_collision_sections(
            encoded,
            base_offset=hull.tag_offset,
            source="<serialized tag101>",
            strict=False,
        )
    except Exception as error:
        raise CollisionWriteError(f"serialized tag101 failed structural reparse: {error}") from error
    if reparsed.convex_hull is None or reparsed.convex_hull.end_offset != hull.tag_offset + len(encoded):
        raise CollisionWriteError("serialized tag101 did not consume its exact output")
    if reparsed.unparsed_data:
        raise CollisionWriteError("serialized tag101 left unparsed bytes")
    return encoded


def _float32(value: float, label: str) -> float:
    if not math.isfinite(value):
        raise CollisionWriteError(f"{label} is non-finite")
    try:
        return struct.unpack("<f", struct.pack("<f", value))[0]
    except (OverflowError, struct.error) as error:
        raise CollisionWriteError(f"{label} is not representable as float32") from error


def _validated_delta(delta: Sequence[float]) -> tuple[float, float, float]:
    if len(delta) != 3:
        raise CollisionWriteError(f"translation must have three components, got {len(delta)}")
    return tuple(_float32(float(value), f"translation component {axis}") for axis, value in enumerate(delta))


def _mean(vertices: Sequence[Sequence[float]]) -> tuple[float, float, float]:
    return tuple(sum(vertex[axis] for vertex in vertices) / len(vertices) for axis in range(3))


def _distance(left: Sequence[float], right: Sequence[float]) -> float:
    return math.sqrt(sum((left[axis] - right[axis]) ** 2 for axis in range(3)))


def _aabb(vertices: Sequence[Sequence[float]]):
    return (
        tuple(min(vertex[axis] for vertex in vertices) for axis in range(3)),
        tuple(max(vertex[axis] for vertex in vertices) for axis in range(3)),
    )


def _polygon_area(vertices, indices) -> float:
    if len(indices) < 3:
        return 0.0
    origin = vertices[indices[0]]
    cross_sum = [0.0, 0.0, 0.0]
    for index in range(1, len(indices) - 1):
        left = vertices[indices[index]]
        right = vertices[indices[index + 1]]
        a = tuple(left[axis] - origin[axis] for axis in range(3))
        b = tuple(right[axis] - origin[axis] for axis in range(3))
        cross_sum[0] += a[1] * b[2] - a[2] * b[1]
        cross_sum[1] += a[2] * b[0] - a[0] * b[2]
        cross_sum[2] += a[0] * b[1] - a[1] * b[0]
    return math.sqrt(sum(value * value for value in cross_sum)) * 0.5


def _geometry_paths(hull: ConvexHullTag101):
    return (
        ("base_geometry", hull.base_geometry),
        ("representation_a.geometry_a", hull.representation_a.geometry_a),
        ("representation_a.geometry_b", hull.representation_a.geometry_b),
        ("representation_b.geometry_a", hull.representation_b.geometry_a),
        ("representation_b.geometry_b", hull.representation_b.geometry_b),
    )


def _require_translation_schema(hull: ConvexHullTag101) -> None:
    geometries = dict(_geometry_paths(hull))
    if hull.base_geometry.vertex_count != 1 or hull.base_geometry.triangle_count != 0:
        raise CollisionWriteError("translation requires the validated 1v/0t base geometry")
    for name in ("representation_a.geometry_a", "representation_b.geometry_a"):
        if not geometries[name].vertices or not geometries[name].triangles:
            raise CollisionWriteError(f"translation requires non-empty {name}")
    for name in ("representation_a.geometry_b", "representation_b.geometry_b"):
        geometry = geometries[name]
        if geometry.vertex_count != 1 or geometry.triangle_count != 0:
            raise CollisionWriteError(f"translation requires the validated 1v/0t {name}")
    for name, geometry in geometries.items():
        if not all(math.isfinite(component) for vertex in geometry.vertices for component in vertex):
            raise CollisionWriteError(f"translation refuses non-finite coordinates in {name}")
    tolerance = 1e-5
    base = hull.base_geometry.vertices[0]
    a_mean = _mean(hull.representation_a.geometry_a.vertices)
    b_mean = _mean(hull.representation_b.geometry_a.vertices)
    if _distance(base, a_mean) > tolerance:
        raise CollisionWriteError("base point is not representation-A vertex mean")
    if _distance(hull.representation_a.geometry_b.vertices[0], a_mean) > tolerance:
        raise CollisionWriteError("representation-A geometry-B point is not its vertex mean")
    if _distance(hull.representation_b.geometry_b.vertices[0], b_mean) > tolerance:
        raise CollisionWriteError("representation-B geometry-B point is not its vertex mean")


def _translate_geometry(
    geometry: CollisionGeometryBlock,
    delta: tuple[float, float, float],
) -> CollisionGeometryBlock:
    vertices = tuple(
        tuple(
            _float32(vertex[axis] + delta[axis], f"translated vertex component {axis}")
            for axis in range(3)
        )
        for vertex in geometry.vertices
    )
    return replace(geometry, vertices=vertices)


def _translation_validation(
    before: ConvexHullTag101,
    after: ConvexHullTag101,
    delta: tuple[float, float, float],
) -> dict[str, object]:
    tolerance = 2e-5
    before_paths = dict(_geometry_paths(before))
    after_paths = dict(_geometry_paths(after))
    maximum_delta_error = 0.0
    maximum_distance_error = 0.0
    for path in TRANSLATED_GEOMETRY_PATHS:
        left = before_paths[path]
        right = after_paths[path]
        if left.triangles != right.triangles or len(left.vertices) != len(right.vertices):
            raise CollisionWriteError(f"translation changed topology in {path}")
        for old, new in zip(left.vertices, right.vertices):
            maximum_delta_error = max(
                maximum_delta_error,
                *(abs((new[axis] - old[axis]) - delta[axis]) for axis in range(3)),
            )
        for index, first in enumerate(left.vertices):
            for second_index in range(index + 1, len(left.vertices)):
                maximum_distance_error = max(
                    maximum_distance_error,
                    abs(
                        _distance(first, left.vertices[second_index])
                        - _distance(right.vertices[index], right.vertices[second_index])
                    ),
                )
    if maximum_delta_error > tolerance or maximum_distance_error > tolerance:
        raise CollisionWriteError("translation failed vector/distance invariants")

    if struct.pack("<f", before.base_scalar) != struct.pack("<f", after.base_scalar):
        raise CollisionWriteError("translation changed base radius")
    for old_rep, new_rep in (
        (before.representation_a, after.representation_a),
        (before.representation_b, after.representation_b),
    ):
        for attribute in (
            "referenced_vertex_indices", "edges", "face_descriptors",
            "edge_face_adjacency", "face_loop_indices",
        ):
            if getattr(old_rep, attribute) != getattr(new_rep, attribute):
                raise CollisionWriteError(f"translation changed {attribute}")
        if tuple(struct.pack("<f", value) for value in old_rep.face_scalars) != tuple(
            struct.pack("<f", value) for value in new_rep.face_scalars
        ):
            raise CollisionWriteError("translation changed face areas")

    area_error = 0.0
    for old_rep, new_rep in (
        (before.representation_a, after.representation_a),
        (before.representation_b, after.representation_b),
    ):
        for descriptor in old_rep.face_descriptors:
            area_error = max(
                area_error,
                abs(
                    _polygon_area(old_rep.geometry_a.vertices, descriptor.primary_indices)
                    - _polygon_area(new_rep.geometry_a.vertices, descriptor.primary_indices)
                ),
            )
    if area_error > tolerance:
        raise CollisionWriteError("translation changed polygon area")

    old_min, old_max = _aabb(before.representation_a.geometry_a.vertices)
    new_min, new_max = _aabb(after.representation_a.geometry_a.vertices)
    aabb_error = max(
        *(abs((new_min[axis] - old_min[axis]) - delta[axis]) for axis in range(3)),
        *(abs((new_max[axis] - old_max[axis]) - delta[axis]) for axis in range(3)),
    )
    if aabb_error > tolerance:
        raise CollisionWriteError("translation failed AABB shift invariant")
    _require_translation_schema(after)
    return {
        "status": "PASS",
        "float32_tolerance": tolerance,
        "maximum_delta_error": maximum_delta_error,
        "maximum_pairwise_distance_error": maximum_distance_error,
        "maximum_face_area_error": area_error,
        "maximum_aabb_shift_error": aabb_error,
        "base_radius_unchanged": True,
        "topology_unchanged": True,
        "adjacency_unchanged": True,
        "centroid_relationships_preserved": True,
    }


def translate_tag101(
    hull: ConvexHullTag101,
    dx: float,
    dy: float,
    dz: float,
) -> Tag101TranslationResult:
    """Rigidly translate only proven positional GeometryBlock vertices."""
    _require_translation_schema(hull)
    delta = _validated_delta((dx, dy, dz))
    rep_a = replace(
        hull.representation_a,
        geometry_a=_translate_geometry(hull.representation_a.geometry_a, delta),
        geometry_b=_translate_geometry(hull.representation_a.geometry_b, delta),
    )
    rep_b = replace(
        hull.representation_b,
        geometry_a=_translate_geometry(hull.representation_b.geometry_a, delta),
        geometry_b=_translate_geometry(hull.representation_b.geometry_b, delta),
    )
    candidate = replace(
        hull,
        base_geometry=_translate_geometry(hull.base_geometry, delta),
        representation_a=rep_a,
        representation_b=rep_b,
    )
    encoded = serialize_tag101(candidate)
    parsed = parse_collision_sections(
        encoded,
        base_offset=hull.tag_offset,
        source="<translated tag101>",
        strict=True,
    ).convex_hull
    assert parsed is not None
    allowed = []
    changes = []
    for path, old_geometry in _geometry_paths(hull):
        new_geometry = dict(_geometry_paths(parsed))[path]
        for index, (old_vertex, new_vertex) in enumerate(zip(old_geometry.vertices, new_geometry.vertices)):
            source_offset = old_geometry.vertex_data_offset + index * 12
            relative = source_offset - hull.tag_offset
            old_raw = hull.raw[relative:relative + 12]
            new_raw = encoded[relative:relative + 12]
            allowed.append(ByteRange(relative, relative + 12))
            if old_raw != new_raw:
                changes.append(CollisionFieldChange(
                    path, index, source_offset, old_vertex, new_vertex,
                    sum(left != right for left, right in zip(old_raw, new_raw)),
                ))
    diff = audit_binary_diff(hull.raw, encoded, allowed)
    if not diff.valid:
        raise CollisionWriteError("tag101 translation changed bytes outside positional fields")
    validation = _translation_validation(hull, parsed, delta)
    return Tag101TranslationResult(
        encoded, hull, parsed, delta, tuple(changes), diff, validation
    )


def replace_dx_tag101(template_bytes: bytes, replacement: bytes, *, source: str = "<template>") -> bytes:
    """Replace only the existing same-size tag-101 range in a DX template."""
    model = parse_dx_bytes(template_bytes, source=source)
    hull = model.collision.convex_hull
    if hull is None:
        raise CollisionWriteError("DX template does not contain tag101")
    if len(replacement) != len(hull.raw):
        raise CollisionWriteError(
            f"replacement tag101 size {len(replacement)} does not match template {len(hull.raw)}"
        )
    parsed = parse_collision_sections(
        replacement,
        base_offset=hull.tag_offset,
        source="<replacement tag101>",
        strict=False,
    )
    if parsed.convex_hull is None or parsed.convex_hull.end_offset != hull.end_offset or parsed.unparsed_data:
        raise CollisionWriteError("replacement is not one exact tag101 section")
    output = bytearray(template_bytes)
    output[hull.tag_offset:hull.end_offset] = replacement
    return bytes(output)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_dx_collision_translation(
    template_bytes: bytes,
    delta: Sequence[float],
    *,
    source: str = "<template>",
) -> DxCollisionPatchResult:
    original = parse_dx_bytes(template_bytes, source=source)
    hull = original.collision.convex_hull
    if hull is None:
        raise CollisionWriteError("DX template does not contain tag101")
    if original.collision.errors:
        raise CollisionWriteError(
            "source tag101 is not valid for translation: " + "; ".join(original.collision.errors)
        )
    values = _validated_delta(delta)
    translated = translate_tag101(hull, *values)
    output_bytes = replace_dx_tag101(template_bytes, translated.data, source=source)
    allowed = [
        ByteRange(change.source_offset, change.source_offset + 12)
        for change in translated.changes
    ]
    diff = audit_binary_diff(template_bytes, output_bytes, allowed)
    if not diff.valid:
        raise CollisionWriteError("full DX changed bytes outside tag101 positional fields")
    output = parse_dx_bytes(output_bytes, source=f"{source} (collision translated)")
    if output.collision.errors:
        raise CollisionWriteError("translated full DX failed tag101 validation")
    if template_bytes[:hull.tag_offset] != output_bytes[:hull.tag_offset]:
        raise CollisionWriteError("bytes before tag101 changed")
    if template_bytes[hull.end_offset:] != output_bytes[hull.end_offset:]:
        raise CollisionWriteError("bytes after tag101 changed")
    output_hull = output.collision.convex_hull
    if output_hull is None or output_hull.raw != translated.data:
        raise CollisionWriteError("full-DX reparse did not preserve translated tag101")
    if original.diagnostics != output.diagnostics:
        raise CollisionWriteError("collision translation changed DX diagnostics")
    if original.vertices != output.vertices or original.uv_sets != output.uv_sets:
        raise CollisionWriteError("collision translation changed visual vertex data")
    if original.local_indices != output.local_indices or original.physical_draws != output.physical_draws:
        raise CollisionWriteError("collision translation changed render topology/draws")
    if original.global_index_table != output.global_index_table:
        raise CollisionWriteError("collision translation changed global indices")
    if (original.collision.cylinder.raw if original.collision.cylinder else None) != (
        output.collision.cylinder.raw if output.collision.cylinder else None
    ):
        raise CollisionWriteError("collision translation changed tag102")
    def preserved_range(start: int, end: int) -> dict[str, object]:
        source_hash = _sha256(template_bytes[start:end])
        output_hash = _sha256(output_bytes[start:end])
        return {
            "start": start,
            "end": end,
            "source_sha256": source_hash,
            "output_sha256": output_hash,
            "match": source_hash == output_hash,
        }

    preserved = {
        "before_tag101": preserved_range(0, hull.tag_offset),
        "render_positions": preserved_range(
            original.vertices.position_offset,
            original.vertices.position_buffer_end,
        ),
        "render_normals": preserved_range(
            original.vertices.normal_offset,
            original.vertices.color_offset,
        ),
        "render_colors": preserved_range(
            original.vertices.color_offset,
            original.uv_count_offset,
        ),
        "uv_local_indices": preserved_range(
            original.uv_count_offset,
            original.draw_table_offset,
        ),
        "draw_global_tables": preserved_range(
            original.draw_table_offset,
            original.trailing.offset,
        ),
        "tag102_and_remainder": preserved_range(hull.end_offset, len(template_bytes)),
    }
    return DxCollisionPatchResult(
        output_bytes,
        _sha256(template_bytes),
        _sha256(output_bytes),
        translated,
        diff,
        original,
        output,
        preserved,
    )


def write_dx_collision_translation(
    source_path: Path,
    output_path: Path,
    delta: Sequence[float],
    *,
    expected_source_sha256: str,
) -> DxCollisionPatchResult:
    source_resolved = source_path.resolve()
    output_resolved = output_path.resolve()
    if source_resolved == output_resolved:
        raise CollisionWriteError("safe mode refuses to overwrite the source DX")
    template = source_resolved.read_bytes()
    actual = _sha256(template)
    if actual.casefold() != expected_source_sha256.casefold():
        raise CollisionWriteError(
            f"source template SHA-256 mismatch: expected {expected_source_sha256}, got {actual}"
        )
    result = patch_dx_collision_translation(template, delta, source=str(source_resolved))
    output_resolved.parent.mkdir(parents=True, exist_ok=True)
    output_resolved.write_bytes(result.data)
    return result
