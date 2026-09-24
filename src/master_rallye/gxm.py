"""Conservative reader for the evidenced GXM header and material prefix.

The geometry and hierarchy tail is intentionally left opaque. Header fields stay
named by offset except the table count proven by parsing the material prefix.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .errors import BoundsError, FormatError

MAX_MATERIALS = 10000
MAX_SLOTS = 32
MAX_STRING = 4096


@dataclass(frozen=True)
class GxmTextureSlot:
    flags3: bytes
    reference: str


@dataclass(frozen=True)
class GxmMaterial:
    name: str
    slots: tuple[GxmTextureSlot, ...]


@dataclass(frozen=True)
class GxmPrefix:
    source: str
    header_words: tuple[int, ...]
    materials: tuple[GxmMaterial, ...]
    tail_offset: int
    tail_size: int
    prefix_kind: str


def _require(data: bytes, offset: int, count: int, source: str) -> None:
    if offset < 0 or count < 0 or offset + count > len(data):
        raise BoundsError(f"GXM prefix in {source}: need {count} bytes at 0x{offset:X}, file size {len(data)}")


def _string(data: bytes, offset: int, source: str) -> tuple[str, int]:
    _require(data, offset, 2, source)
    size = struct.unpack_from("<H", data, offset)[0]
    if size > MAX_STRING:
        raise FormatError(f"GXM string length {size} at 0x{offset:X} in {source}")
    offset += 2
    _require(data, offset, size, source)
    raw = data[offset:offset + size]
    try:
        value = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise FormatError(f"non-ASCII GXM prefix string at 0x{offset:X} in {source}") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise FormatError(f"control byte in GXM prefix string at 0x{offset:X} in {source}")
    return value, offset + size


def parse_gxm_prefix_bytes(data: bytes, source: str = "<bytes>") -> GxmPrefix:
    _require(data, 0, 32, source)
    words = struct.unpack_from("<8I", data)
    if words[0] & 0xFF != 0x02:
        raise FormatError(f"unexpected GXM first byte 0x{words[0] & 0xFF:02X} in {source}")
    if words[0] & 0xFFFF != 0x0702 or words[2] != 0:
        return GxmPrefix(source, words, (), 32, len(data) - 32, "opaque_after_header")
    count = words[3]
    if count > MAX_MATERIALS:
        raise FormatError(f"GXM material count {count} exceeds limit in {source}")
    offset = 32
    materials = []
    for material_index in range(count):
        name, offset = _string(data, offset, source)
        _require(data, offset, 1, source)
        slot_count = data[offset]
        offset += 1
        if slot_count > MAX_SLOTS:
            raise FormatError(f"GXM material {material_index} has {slot_count} slots in {source}")
        slots = []
        for _ in range(slot_count):
            _require(data, offset, 3, source)
            flags = data[offset:offset + 3]
            offset += 3
            reference, offset = _string(data, offset, source)
            slots.append(GxmTextureSlot(flags, reference))
        materials.append(GxmMaterial(name, tuple(slots)))
    return GxmPrefix(source, words, tuple(materials), offset, len(data) - offset, "material_table")


def parse_gxm_prefix(path: Path) -> GxmPrefix:
    return parse_gxm_prefix_bytes(path.read_bytes(), str(path))



@dataclass(frozen=True)
class GxmGeometryPrefix:
    vector_a_offset: int
    vector_a_count: int
    vector_b_offset: int
    vector_b_count: int
    sentinel_offset: int
    remainder_offset: int
    vector_b_bounds: tuple[tuple[float, float], ...]


def parse_gxm_geometry_prefix_bytes(data: bytes, prefix: GxmPrefix) -> GxmGeometryPrefix:
    """Locate the two proven vector3 arrays in the material-table variant only."""
    import math

    if prefix.prefix_kind != "material_table":
        raise FormatError(f"GXM geometry prefix is unknown for {prefix.prefix_kind} in {prefix.source}")
    vector_a_count = prefix.header_words[4]
    vector_b_count = prefix.header_words[5]
    if vector_a_count != prefix.header_words[6] * 3:
        raise FormatError(f"GXM vector count relation fails in {prefix.source}")
    vector_a_offset = prefix.tail_offset
    vector_b_offset = vector_a_offset + vector_a_count * 12
    sentinel_offset = vector_b_offset + vector_b_count * 12
    _require(data, sentinel_offset, 12, prefix.source)
    if data[sentinel_offset:sentinel_offset + 12] != b"\xff" * 12:
        raise FormatError(f"GXM 12-byte separator differs at 0x{sentinel_offset:X} in {prefix.source}")
    vectors_a = struct.unpack_from(f"<{vector_a_count * 3}f", data, vector_a_offset)
    if any(not math.isfinite(value) for value in vectors_a):
        raise FormatError(f"nonfinite GXM unit vector in {prefix.source}")
    for index in range(0, len(vectors_a), 3):
        magnitude2 = sum(vectors_a[index + axis] ** 2 for axis in range(3))
        if abs(magnitude2 - 1.0) > 1e-4:
            raise FormatError(f"nonunit GXM vector A at index {index // 3} in {prefix.source}")
    vectors_b = struct.unpack_from(f"<{vector_b_count * 3}f", data, vector_b_offset)
    if any(not math.isfinite(value) for value in vectors_b):
        raise FormatError(f"nonfinite GXM vector B in {prefix.source}")
    bounds = (tuple((min(vectors_b[axis::3]), max(vectors_b[axis::3])) for axis in range(3))
              if vector_b_count else ())
    return GxmGeometryPrefix(vector_a_offset, vector_a_count, vector_b_offset,
                             vector_b_count, sentinel_offset, sentinel_offset + 12,
                             bounds)


@dataclass(frozen=True)
class GxmTrianglePrefix:
    record_offset: int
    record_count: int
    vector_c_offset: int
    vector_c_count: int
    hierarchy_offset: int
    vector_c_bounds: tuple[tuple[float, float], ...]
    no_material_record_count: int
    no_vector_b_record_count: int


def parse_gxm_triangle_prefix_bytes(
    data: bytes, prefix: GxmPrefix, geometry: GxmGeometryPrefix
) -> GxmTrianglePrefix:
    """Validate ten-word records, separators and the third float3 array."""
    import math

    record_count = prefix.header_words[6]
    vector_c_count = prefix.header_words[7]
    if record_count > 10_000_000 or vector_c_count > 10_000_000:
        raise FormatError(f"unreasonable GXM triangle-prefix count in {prefix.source}")
    record_offset = geometry.remainder_offset
    vector_c_offset = record_offset + record_count * 52 - (12 if record_count else 0)
    _require(data, vector_c_offset, vector_c_count * 12, prefix.source)
    no_material = 0
    no_vector_b = 0
    for index in range(record_count):
        offset = record_offset + index * 52
        record = struct.unpack_from("<10I", data, offset)
        field_0 = record[0]
        if field_0 == 0xFFFFFFFF:
            no_material += 1
        elif field_0 >= len(prefix.materials):
            raise FormatError(f"GXM record {index} field 0 outside material table in {prefix.source}")
        if record[1:4] == (0xFFFFFFFF,) * 3:
            no_vector_b += 1
        elif any(value >= geometry.vector_b_count for value in record[1:4]):
            raise FormatError(f"GXM record {index} index group B out of range in {prefix.source}")
        if any(value >= vector_c_count for value in record[4:7]):
            raise FormatError(f"GXM record {index} index group C out of range in {prefix.source}")
        if any(value >= geometry.vector_a_count for value in record[7:10]):
            raise FormatError(f"GXM record {index} index group A out of range in {prefix.source}")
        if index < record_count - 1 and data[offset + 40:offset + 52] != b"\xff" * 12:
            raise FormatError(f"GXM record {index} separator differs in {prefix.source}")
    values = struct.unpack_from(f"<{vector_c_count * 3}f", data, vector_c_offset)
    if any(not math.isfinite(value) for value in values):
        raise FormatError(f"nonfinite GXM vector C in {prefix.source}")
    bounds = tuple((min(values[axis::3]), max(values[axis::3])) for axis in range(3))
    return GxmTrianglePrefix(record_offset, record_count, vector_c_offset,
                             vector_c_count, vector_c_offset + vector_c_count * 12,
                             bounds, no_material, no_vector_b)
