"""Shared coordinate conventions for interchange and Blender authoring."""
from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

SOURCE_AXES = "right-handed XYZ; observed vehicle up axis +Y"
GLTF_AXIS_MAPPING = "identity XYZ (glTF +Y up)"
BLENDER_AXIS_MAPPING = "(X, -Z, Y), +90 degrees about X"
AUTHORING_SCALE = 1.0
HANDEDNESS = "preserved"
TRIANGLE_WINDING = "stored-global-order"
GLTF_PREVIEW_UV_POLICY = "flip-v"
BLENDER_PREVIEW_UV_POLICY = "direct-v"
NORMAL_NEAR_ZERO_EPSILON = 1.0e-8

Vector3 = tuple[float, float, float]
Vector2 = tuple[float, float]
Triangle = tuple[int, int, int]


@dataclass(frozen=True)
class NormalDiagnostics:
    count: int
    non_finite_count: int
    near_zero_count: int
    min_magnitude: float | None
    max_magnitude: float | None

    def to_dict(self) -> dict[str, int | float | None]:
        return {
            "count": self.count,
            "non_finite_count": self.non_finite_count,
            "near_zero_count": self.near_zero_count,
            "min_magnitude": self.min_magnitude,
            "max_magnitude": self.max_magnitude,
        }


def position_to_authoring(value: Sequence[float]) -> Vector3:
    """R1 glTF/interchange mapping: preserve source XYZ and native scale."""
    return (float(value[0]), float(value[1]), float(value[2]))


def normal_to_authoring(value: Sequence[float]) -> Vector3:
    return (float(value[0]), float(value[1]), float(value[2]))


def position_to_blender(value: Sequence[float]) -> Vector3:
    """Rotate source/glTF +Y-up coordinates into Blender +Z-up coordinates."""
    return (float(value[0]), -float(value[2]), float(value[1]))


def normal_to_blender(value: Sequence[float]) -> Vector3:
    return (float(value[0]), -float(value[2]), float(value[1]))


def blender_position_to_source(value: Sequence[float]) -> Vector3:
    """Exact inverse of position_to_blender for authoring export."""
    return (float(value[0]), float(value[2]), -float(value[1]))


def transform_blender_positions_to_source(
    values: Iterable[Sequence[float]],
) -> tuple[Vector3, ...]:
    return tuple(blender_position_to_source(value) for value in values)


def transform_positions(values: Iterable[Sequence[float]]) -> tuple[Vector3, ...]:
    """Transform source positions for R1 glTF/interchange output."""
    return tuple(position_to_authoring(value) for value in values)


def transform_normals(values: Iterable[Sequence[float]]) -> tuple[Vector3, ...]:
    return tuple(normal_to_authoring(value) for value in values)


def transform_blender_positions(values: Iterable[Sequence[float]]) -> tuple[Vector3, ...]:
    return tuple(position_to_blender(value) for value in values)


def transform_blender_normals(values: Iterable[Sequence[float]]) -> tuple[Vector3, ...]:
    return tuple(normal_to_blender(value) for value in values)


def transform_uv_values(
    values: Iterable[Sequence[float]],
    flip_v: bool = True,
) -> tuple[Vector2, ...]:
    """Apply only the model-coordinate V transform, never a raster-row transform."""
    return tuple(
        (float(value[0]), 1.0 - float(value[1]) if flip_v else float(value[1]))
        for value in values
    )


def analyze_normals(values: Iterable[Sequence[float]]) -> NormalDiagnostics:
    vectors = tuple(tuple(float(component) for component in value) for value in values)
    magnitudes: list[float] = []
    non_finite_count = 0
    near_zero_count = 0
    for vector in vectors:
        if len(vector) != 3 or not all(math.isfinite(component) for component in vector):
            non_finite_count += 1
            continue
        magnitude = math.sqrt(sum(component * component for component in vector))
        magnitudes.append(magnitude)
        if magnitude <= NORMAL_NEAR_ZERO_EPSILON:
            near_zero_count += 1
    return NormalDiagnostics(
        count=len(vectors),
        non_finite_count=non_finite_count,
        near_zero_count=near_zero_count,
        min_magnitude=min(magnitudes) if magnitudes else None,
        max_magnitude=max(magnitudes) if magnitudes else None,
    )


def prepare_display_normals(
    values: Iterable[Sequence[float]],
    expected_count: int,
) -> tuple[tuple[Vector3, ...] | None, NormalDiagnostics, str | None]:
    """Validate and normalize a display copy without altering source values."""
    vectors = tuple(tuple(float(component) for component in value) for value in values)
    diagnostics = analyze_normals(vectors)
    if diagnostics.count != expected_count:
        return None, diagnostics, (
            f"normal count {diagnostics.count} differs from vertex count {expected_count}"
        )
    if diagnostics.non_finite_count:
        return None, diagnostics, f"{diagnostics.non_finite_count} non-finite source normals"
    if diagnostics.near_zero_count:
        return None, diagnostics, (
            f"{diagnostics.near_zero_count} zero/near-zero source normals"
        )
    normalized = []
    for vector in vectors:
        magnitude = math.sqrt(sum(component * component for component in vector))
        normalized.append(tuple(component / magnitude for component in vector))
    return tuple(normalized), diagnostics, None


def expand_corner_normals(
    display_normals: Sequence[Sequence[float]],
    loop_vertex_indices: Iterable[int],
) -> tuple[Vector3, ...]:
    """Build a checked per-corner candidate without calling Blender native APIs."""
    vectors = tuple(
        (float(value[0]), float(value[1]), float(value[2]))
        for value in display_normals
    )
    result = []
    for vertex_index in loop_vertex_indices:
        index = int(vertex_index)
        if index < 0 or index >= len(vectors):
            raise ValueError(f"corner vertex index {index} outside {len(vectors)} normals")
        result.append(vectors[index])
    return tuple(result)


def float32_signed_bits(value: float) -> int:
    """Signed Blender INT representation of the exact IEEE-754 float32 bits."""
    return struct.unpack("<i", struct.pack("<f", float(value)))[0]


def triangles_from_indices(indices: Sequence[int]) -> tuple[Triangle, ...]:
    if len(indices) % 3:
        raise ValueError(f"triangle index sequence has {len(indices)} entries")
    return tuple(
        (int(indices[offset]), int(indices[offset + 1]), int(indices[offset + 2]))
        for offset in range(0, len(indices), 3)
    )


def geometry_fingerprint(
    positions: Iterable[Sequence[float]],
    triangles: Iterable[Sequence[int]],
) -> str:
    """Stable target-space fingerprint for edit-status diagnostics."""
    digest = hashlib.sha256()
    positions_tuple = tuple(positions)
    triangles_tuple = tuple(triangles)
    digest.update(struct.pack("<II", len(positions_tuple), len(triangles_tuple)))
    for position in positions_tuple:
        digest.update(struct.pack("<3f", *position_to_authoring(position)))
    for triangle in triangles_tuple:
        digest.update(
            struct.pack("<3I", int(triangle[0]), int(triangle[1]), int(triangle[2]))
        )
    return digest.hexdigest()


def convention_metadata() -> dict[str, object]:
    return {
        "source_axes": SOURCE_AXES,
        "gltf_axis_mapping": GLTF_AXIS_MAPPING,
        "blender_axis_mapping": BLENDER_AXIS_MAPPING,
        "scale": AUTHORING_SCALE,
        "handedness": HANDEDNESS,
        "triangle_winding": TRIANGLE_WINDING,
        "gltf_preview_uv_policy": GLTF_PREVIEW_UV_POLICY,
        "blender_preview_uv_policy": BLENDER_PREVIEW_UV_POLICY,
        "world_unit_semantics": "UNKNOWN",
    }
