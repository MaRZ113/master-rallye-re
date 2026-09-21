"""Shared coordinate conventions for interchange and Blender authoring."""
from __future__ import annotations

import hashlib
import struct
from collections.abc import Iterable, Sequence

SOURCE_AXES = "right-handed XYZ; observed vehicle up axis +Y"
GLTF_AXIS_MAPPING = "identity XYZ (glTF +Y up)"
BLENDER_AXIS_MAPPING = "(X, -Z, Y), +90 degrees about X"
AUTHORING_SCALE = 1.0
HANDEDNESS = "preserved"
TRIANGLE_WINDING = "stored-global-order"
PREVIEW_UV_POLICY = "flip-v"

Vector3 = tuple[float, float, float]
Vector2 = tuple[float, float]
Triangle = tuple[int, int, int]


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
    """Inverse of position_to_blender for future writer research."""
    return (float(value[0]), float(value[2]), -float(value[1]))


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
    return tuple((float(value[0]), 1.0 - float(value[1]) if flip_v else float(value[1])) for value in values)


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
        digest.update(struct.pack("<3I", int(triangle[0]), int(triangle[1]), int(triangle[2])))
    return digest.hexdigest()


def convention_metadata() -> dict[str, object]:
    return {
        "source_axes": SOURCE_AXES,
        "gltf_axis_mapping": GLTF_AXIS_MAPPING,
        "blender_axis_mapping": BLENDER_AXIS_MAPPING,
        "scale": AUTHORING_SCALE,
        "handedness": HANDEDNESS,
        "triangle_winding": TRIANGLE_WINDING,
        "preview_uv_policy": PREVIEW_UV_POLICY,
        "world_unit_semantics": "UNKNOWN",
    }
