"""Bounds-checked parser for DX collision sections.

The wire layout is based on matching executable writer/reader functions. The
models keep neutral names where runtime semantics are not proven. This module
is read-only: it contains no collision serializer.
"""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from .bounds import DxSpatialBounds1339, parse_bounds1339

from .errors import BoundsError, FormatError

TAG_BSP = 100
TAG_CONVEX_HULL = 101
TAG_CYLINDER = 102
MAX_GEOMETRY_VERTICES = 1_000_000
MAX_GEOMETRY_TRIANGLES = 2_000_000
MAX_REPRESENTATION_ITEMS = 2_000_000


@dataclass(frozen=True)
class CollisionGeometryBlock:
    offset: int
    end_offset: int
    vertex_count_offset: int
    triangle_count_offset: int
    vertex_data_offset: int
    triangle_data_offset: int
    vertices: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def triangle_count(self) -> int:
        return len(self.triangles)


@dataclass(frozen=True)
class CollisionFaceDescriptor:
    offset: int
    end_offset: int
    primary_count_offset: int
    primary_indices: tuple[int, ...]
    secondary_count_offset: int
    secondary_indices: tuple[int, ...]


@dataclass(frozen=True)
class ConvexHullRepresentation:
    offset: int
    end_offset: int
    geometry_a: CollisionGeometryBlock
    geometry_b: CollisionGeometryBlock
    referenced_vertex_count_offset: int
    referenced_vertex_indices: tuple[int, ...]
    edge_count_offset: int
    edges: tuple[tuple[int, int], ...]
    face_count_offset: int
    face_descriptors: tuple[CollisionFaceDescriptor, ...]
    edge_face_adjacency_offset: int
    edge_face_adjacency: tuple[tuple[int, int], ...]
    face_loop_offset: int
    face_loop_indices: tuple[tuple[int, ...], ...]
    face_scalar_offset: int
    face_scalars: tuple[float, ...]

    @property
    def face_count(self) -> int:
        return len(self.face_descriptors)


@dataclass(frozen=True)
class ConvexHullTag101:
    tag_offset: int
    payload_offset: int
    end_offset: int
    base_geometry: CollisionGeometryBlock
    base_scalar_offset: int
    base_scalar: float
    representation_a: ConvexHullRepresentation
    representation_b: ConvexHullRepresentation
    raw: bytes
    sha256: str

    @property
    def payload_size(self) -> int:
        return self.end_offset - self.payload_offset


@dataclass(frozen=True)
class CylinderTag102:
    tag_offset: int
    payload_offset: int
    end_offset: int
    value_0: float
    value_1: float
    raw: bytes
    sha256: str


@dataclass(frozen=True)
class RawCollisionSection:
    tag: int
    tag_offset: int
    end_offset: int
    raw: bytes
    sha256: str
    status: str


@dataclass(frozen=True)
class CollisionSections:
    offset: int
    end_offset: int
    bsp: RawCollisionSection | None
    convex_hull: ConvexHullTag101 | None
    cylinder: CylinderTag102 | None
    unparsed_offset: int
    unparsed_data: bytes
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    spatial_bounds_1339: DxSpatialBounds1339 | None = None

    @property
    def tag_ids(self) -> tuple[int, ...]:
        result: list[int] = []
        if self.bsp is not None:
            result.append(TAG_BSP)
        if self.convex_hull is not None:
            result.append(TAG_CONVEX_HULL)
        if self.cylinder is not None:
            result.append(TAG_CYLINDER)
        return tuple(result)

    @property
    def validated(self) -> bool:
        return not self.errors


class _Reader:
    def __init__(self, data: bytes, source: str, base_offset: int, strict: bool):
        self.data = data
        self.source = source
        self.base_offset = base_offset
        self.strict = strict
        self.errors: list[str] = []

    def absolute(self, offset: int) -> int:
        return self.base_offset + offset

    def require(self, offset: int, size: int, label: str) -> None:
        available = len(self.data) - offset
        if offset < 0 or size < 0 or available < size:
            raise BoundsError(
                f"{label} at 0x{self.absolute(offset):X} in {self.source}: "
                f"need {size} bytes, have {max(available, 0)}"
            )

    def i32(self, offset: int, label: str) -> int:
        self.require(offset, 4, label)
        return struct.unpack_from("<i", self.data, offset)[0]

    def u32(self, offset: int, label: str) -> int:
        self.require(offset, 4, label)
        return struct.unpack_from("<I", self.data, offset)[0]

    def f32(self, offset: int, label: str) -> float:
        self.require(offset, 4, label)
        value = struct.unpack_from("<f", self.data, offset)[0]
        if not math.isfinite(value):
            message = (
                f"{label} at 0x{self.absolute(offset):X} in {self.source}: non-finite float"
            )
            if self.strict:
                raise FormatError(message)
            self.errors.append(message)
        return value

    def ints(self, offset: int, count: int, label: str) -> tuple[int, ...]:
        self.require(offset, count * 4, label)
        return tuple(struct.unpack_from(f"<{count}i", self.data, offset)) if count else ()


def _count(reader: _Reader, offset: int, label: str, limit: int) -> int:
    value = reader.i32(offset, label)
    if value < 0 or value > limit:
        raise FormatError(
            f"{label} at 0x{reader.absolute(offset):X} in {reader.source}: "
            f"unreasonable count {value}"
        )
    return value


def _geometry(reader: _Reader, offset: int, label: str) -> tuple[CollisionGeometryBlock, int]:
    start = offset
    vertex_count_offset = offset
    vertex_count = _count(reader, offset, f"{label} vertex count", MAX_GEOMETRY_VERTICES)
    triangle_count_offset = offset + 4
    triangle_count = _count(reader, triangle_count_offset, f"{label} triangle count", MAX_GEOMETRY_TRIANGLES)
    offset += 8
    vertex_data_offset = offset
    reader.require(offset, vertex_count * 12, f"{label} vertices")
    vertices = tuple(
        tuple(reader.f32(offset + index * 12 + axis * 4, f"{label} vertex {index} component {axis}") for axis in range(3))
        for index in range(vertex_count)
    )
    offset += vertex_count * 12
    triangle_data_offset = offset
    reader.require(offset, triangle_count * 12, f"{label} triangles")
    triangles = tuple(struct.unpack_from("<3i", reader.data, offset + index * 12) for index in range(triangle_count))
    for index, triangle in enumerate(triangles):
        if any(value < 0 or value >= vertex_count for value in triangle):
            raise FormatError(
                f"{label} triangle {index} at 0x{reader.absolute(offset + index * 12):X}: "
                f"index {triangle!r} outside 0..{vertex_count - 1}"
            )
    offset += triangle_count * 12
    return CollisionGeometryBlock(
        reader.absolute(start), reader.absolute(offset), reader.absolute(vertex_count_offset),
        reader.absolute(triangle_count_offset), reader.absolute(vertex_data_offset),
        reader.absolute(triangle_data_offset), vertices, triangles,
    ), offset


def _validate_indices(reader: _Reader, values: tuple[int, ...], limit: int, label: str, offset: int) -> None:
    for index, value in enumerate(values):
        if value < 0 or value >= limit:
            raise FormatError(
                f"{label} {index} at 0x{reader.absolute(offset + index * 4):X}: "
                f"index {value} outside 0..{limit - 1}"
            )


def _representation(reader: _Reader, offset: int, label: str) -> tuple[ConvexHullRepresentation, int]:
    start = offset
    geometry_a, offset = _geometry(reader, offset, f"{label} geometry A")
    geometry_b, offset = _geometry(reader, offset, f"{label} geometry B")
    referenced_count_offset = offset
    referenced_count = _count(reader, offset, f"{label} referenced vertex count", MAX_REPRESENTATION_ITEMS)
    offset += 4
    referenced = reader.ints(offset, referenced_count, f"{label} referenced vertex indices")
    _validate_indices(reader, referenced, geometry_a.vertex_count, f"{label} referenced vertex", offset)
    offset += referenced_count * 4
    edge_count_offset = offset
    edge_count = _count(reader, offset, f"{label} edge count", MAX_REPRESENTATION_ITEMS)
    offset += 4
    reader.require(offset, edge_count * 8, f"{label} edge vertex pairs")
    edges = tuple(struct.unpack_from("<2i", reader.data, offset + index * 8) for index in range(edge_count))
    _validate_indices(reader, tuple(value for edge in edges for value in edge), geometry_a.vertex_count, f"{label} edge vertex", offset)
    offset += edge_count * 8
    face_count_offset = offset
    face_count = _count(reader, offset, f"{label} face count", MAX_REPRESENTATION_ITEMS)
    offset += 4
    descriptors = []
    for face_index in range(face_count):
        descriptor_start = offset
        primary_count_offset = offset
        primary_count = _count(reader, offset, f"{label} face {face_index} primary count", MAX_REPRESENTATION_ITEMS)
        offset += 4
        primary = reader.ints(offset, primary_count, f"{label} face {face_index} primary indices")
        _validate_indices(reader, primary, geometry_a.vertex_count, f"{label} face {face_index} primary", offset)
        offset += primary_count * 4
        secondary_count_offset = offset
        secondary_count = _count(reader, offset, f"{label} face {face_index} secondary count", MAX_REPRESENTATION_ITEMS)
        offset += 4
        secondary = reader.ints(offset, secondary_count, f"{label} face {face_index} secondary indices")
        _validate_indices(reader, secondary, geometry_a.vertex_count, f"{label} face {face_index} secondary", offset)
        offset += secondary_count * 4
        descriptors.append(CollisionFaceDescriptor(
            reader.absolute(descriptor_start), reader.absolute(offset), reader.absolute(primary_count_offset),
            primary, reader.absolute(secondary_count_offset), secondary,
        ))
    edge_face_offset = offset
    reader.require(offset, edge_count * 8, f"{label} edge-face adjacency")
    edge_face_adjacency = tuple(struct.unpack_from("<2i", reader.data, offset + index * 8) for index in range(edge_count))
    _validate_indices(reader, tuple(value for pair in edge_face_adjacency for value in pair), face_count, f"{label} edge-face adjacency", offset)
    offset += edge_count * 8
    face_loop_offset = offset
    face_loops = []
    for face_index in range(face_count):
        loop_count = _count(reader, offset, f"{label} face {face_index} loop count", MAX_REPRESENTATION_ITEMS)
        offset += 4
        loop = reader.ints(offset, loop_count, f"{label} face {face_index} loop indices")
        _validate_indices(reader, loop, edge_count, f"{label} face {face_index} loop", offset)
        offset += loop_count * 4
        face_loops.append(loop)
    face_scalar_offset = offset
    scalars = tuple(reader.f32(offset + index * 4, f"{label} face {index} scalar") for index in range(face_count))
    offset += face_count * 4
    return ConvexHullRepresentation(
        reader.absolute(start), reader.absolute(offset), geometry_a, geometry_b,
        reader.absolute(referenced_count_offset), referenced, reader.absolute(edge_count_offset), edges,
        reader.absolute(face_count_offset), tuple(descriptors), reader.absolute(edge_face_offset),
        edge_face_adjacency, reader.absolute(face_loop_offset), tuple(face_loops),
        reader.absolute(face_scalar_offset), scalars,
    ), offset


def _tag101(reader: _Reader, offset: int) -> tuple[ConvexHullTag101, int]:
    tag_offset = offset
    if reader.u32(offset, "tag101 tag") != TAG_CONVEX_HULL:
        raise FormatError(f"expected tag {TAG_CONVEX_HULL} at 0x{reader.absolute(offset):X}")
    offset += 4
    payload_offset = offset
    base, offset = _geometry(reader, offset, "tag101 base geometry")
    scalar_offset = offset
    scalar = reader.f32(offset, "tag101 base scalar")
    offset += 4
    representation_a, offset = _representation(reader, offset, "tag101 representation A")
    representation_b, offset = _representation(reader, offset, "tag101 representation B")
    raw = reader.data[tag_offset:offset]
    return ConvexHullTag101(
        reader.absolute(tag_offset), reader.absolute(payload_offset), reader.absolute(offset), base,
        reader.absolute(scalar_offset), scalar, representation_a, representation_b,
        raw, hashlib.sha256(raw).hexdigest(),
    ), offset


def parse_collision_sections(
    data: bytes,
    *,
    base_offset: int = 0,
    source: str = "<bytes>",
    strict: bool = True,
) -> CollisionSections:
    """Parse the ordered tag-100/101/102 prefix and preserve the remainder."""
    reader = _Reader(data, source, base_offset, strict)
    offset = 0
    bsp = None
    convex = None
    cylinder = None
    while len(data) - offset >= 4:
        tag = reader.u32(offset, "collision section tag")
        if tag == TAG_BSP:
            raw = data[offset:]
            bsp = RawCollisionSection(tag, reader.absolute(offset), reader.absolute(len(data)), raw, hashlib.sha256(raw).hexdigest(), "raw-length-unresolved")
            offset = len(data)
            break
        if tag == TAG_CONVEX_HULL:
            if convex is not None:
                raise FormatError(f"duplicate tag101 at 0x{reader.absolute(offset):X}")
            convex, offset = _tag101(reader, offset)
            continue
        if tag == TAG_CYLINDER:
            if cylinder is not None:
                raise FormatError(f"duplicate tag102 at 0x{reader.absolute(offset):X}")
            start = offset
            reader.require(offset, 12, "tag102 cylinder")
            value_0 = reader.f32(offset + 4, "tag102 value 0")
            value_1 = reader.f32(offset + 8, "tag102 value 1")
            offset += 12
            raw = data[start:offset]
            cylinder = CylinderTag102(reader.absolute(start), reader.absolute(start + 4), reader.absolute(offset), value_0, value_1, raw, hashlib.sha256(raw).hexdigest())
            continue
        break
    return CollisionSections(
        base_offset, reader.absolute(offset), bsp, convex, cylinder,
        reader.absolute(offset), data[offset:], (), tuple(reader.errors),
        parse_bounds1339(data[offset:], reader.absolute(offset)),
    )
