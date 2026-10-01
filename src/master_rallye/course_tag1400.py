"""Bounded, read-only parser for the observed Retail rev135 tag-1400 region.

Field names are intentionally neutral. This module records the wire grammar
needed to delimit the region and compare typed fields; it does not assign
course, collision, grid, or surface semantics and exposes no writer API.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from .errors import BoundsError, FormatError


TAG1400 = 1400
TAG1400_FIXED_HEADER_SIZE = 40
TAG1400_RECORD_SIZE = 56
MAX_TAG1400_CELLS = 4_000_000
MAX_TAG1400_CELL_ENTRIES = 8_000_000
MAX_TAG1400_STRINGS = 65_536
MAX_TAG1400_STRING_BYTES = 8_000_000
MAX_TAG1400_RECORDS = 1_000_000


@dataclass(frozen=True)
class Tag1400Cell:
    index: int
    offset: int
    entries: tuple[int, ...]


@dataclass(frozen=True)
class Tag1400String:
    index: int
    offset: int
    raw_bytes: bytes


@dataclass(frozen=True)
class Tag1400Record56:
    index: int
    offset: int
    float_prefix: tuple[float, ...]
    string_ref_index: int
    float_suffix: tuple[float, float, float, float]


@dataclass(frozen=True)
class CourseTag1400:
    source: str
    byte_size: int
    tag_offset: int
    scalar: float
    dimension_0: int
    dimension_1: int
    vector_a: tuple[float, float, float]
    vector_b: tuple[float, float, float]
    cells: tuple[Tag1400Cell, ...]
    strings: tuple[Tag1400String, ...]
    records: tuple[Tag1400Record56, ...]
    consumed_size: int

    @property
    def trailing_size(self) -> int:
        return self.byte_size - self.consumed_size

    @property
    def complete(self) -> bool:
        return self.trailing_size == 0

    def structural_summary(self) -> dict:
        entry_count = sum(len(cell.entries) for cell in self.cells)
        return {
            "source": self.source,
            "tag_offset": self.tag_offset,
            "byte_size": self.byte_size,
            "consumed_size": self.consumed_size,
            "trailing_size": self.trailing_size,
            "scalar": self.scalar,
            "dimension_0": self.dimension_0,
            "dimension_1": self.dimension_1,
            "cell_count": len(self.cells),
            "cell_entry_count": entry_count,
            "max_cell_entry_count": max((len(cell.entries) for cell in self.cells), default=0),
            "string_count": len(self.strings),
            "string_byte_count": sum(len(item.raw_bytes) for item in self.strings),
            "record_count": len(self.records),
            "record_stride": TAG1400_RECORD_SIZE,
        }


class _Cursor:
    def __init__(self, data: bytes, source: str):
        self.data = data
        self.source = source
        self.offset = 0

    def require(self, size: int, label: str) -> None:
        if size < 0 or self.offset < 0 or size > len(self.data) - self.offset:
            raise BoundsError(
                f"{label} at 0x{self.offset:X} in {self.source} is truncated "
                f"(need {size} bytes, have {max(0, len(self.data) - self.offset)})"
            )

    def unpack(self, fmt: str, label: str):
        size = struct.calcsize(fmt)
        self.require(size, label)
        values = struct.unpack_from(fmt, self.data, self.offset)
        self.offset += size
        return values

    def blob(self, size: int, label: str) -> bytes:
        self.require(size, label)
        start = self.offset
        self.offset += size
        return self.data[start:self.offset]


def parse_course_tag1400_bytes(
    data: bytes,
    source: str = "<bytes>",
    *,
    allow_trailing: bool = False,
    tag_offset: int = 0,
) -> CourseTag1400:
    """Parse fixed fields, dimensioned uint32 cell lists, strings and 56-byte records.

    ``allow_trailing`` is intended for a containing tag100 suffix where a later
    section may follow. ``consumed_size`` always ends at the last decoded
    tag-1400 record; trailing bytes remain available to the caller verbatim.
    """
    cursor = _Cursor(data, source)
    (tag,) = cursor.unpack("<I", "tag1400 identifier")
    if tag != TAG1400:
        raise FormatError(f"expected tag 1400 at 0x0 in {source}, found {tag}")
    (scalar, dimension_0, dimension_1) = cursor.unpack("<fII", "tag1400 fixed scalar and dimensions")
    vector_a = tuple(cursor.unpack("<3f", "tag1400 vector_a"))
    vector_b = tuple(cursor.unpack("<3f", "tag1400 vector_b"))
    if cursor.offset != TAG1400_FIXED_HEADER_SIZE:
        raise AssertionError("internal tag1400 fixed-header size mismatch")

    if dimension_0 == 0 or dimension_1 == 0:
        raise FormatError(f"zero tag1400 dimension in {source}: {dimension_0} x {dimension_1}")
    if dimension_0 > MAX_TAG1400_CELLS or dimension_1 > MAX_TAG1400_CELLS:
        raise FormatError(f"unreasonable tag1400 dimensions in {source}: {dimension_0} x {dimension_1}")
    cell_count = dimension_0 * dimension_1
    if cell_count > MAX_TAG1400_CELLS:
        raise FormatError(f"tag1400 cell count {cell_count} exceeds limit in {source}")
    # Every cell starts with one uint32 count. This rejects impossible dimensions
    # before building a large Python object graph.
    if cell_count > (len(data) - cursor.offset) // 4:
        raise BoundsError(f"tag1400 cell count cannot fit in remaining bytes in {source}")

    cells: list[Tag1400Cell] = []
    total_entries = 0
    for cell_index in range(cell_count):
        cell_offset = cursor.offset
        (item_count,) = cursor.unpack("<I", f"tag1400 cell {cell_index} entry count")
        total_entries += item_count
        if total_entries > MAX_TAG1400_CELL_ENTRIES:
            raise FormatError(f"tag1400 cell entries exceed limit in {source}")
        if item_count > (len(data) - cursor.offset) // 4:
            raise BoundsError(f"tag1400 cell {cell_index} entries are truncated in {source}")
        entries = tuple(value[0] for value in (
            cursor.unpack("<I", f"tag1400 cell {cell_index} entry") for _ in range(item_count)
        ))
        cells.append(Tag1400Cell(cell_index, cell_offset, entries))

    (string_count,) = cursor.unpack("<I", "tag1400 string-table count")
    if string_count > MAX_TAG1400_STRINGS:
        raise FormatError(f"unreasonable tag1400 string count {string_count} in {source}")
    strings: list[Tag1400String] = []
    total_string_bytes = 0
    for string_index in range(string_count):
        string_offset = cursor.offset
        (byte_count,) = cursor.unpack("<I", f"tag1400 string {string_index} byte count")
        total_string_bytes += byte_count
        if total_string_bytes > MAX_TAG1400_STRING_BYTES:
            raise FormatError(f"tag1400 string bytes exceed limit in {source}")
        raw_bytes = cursor.blob(byte_count, f"tag1400 string {string_index} bytes")
        strings.append(Tag1400String(string_index, string_offset, raw_bytes))

    (record_count,) = cursor.unpack("<I", "tag1400 56-byte record count")
    if record_count > MAX_TAG1400_RECORDS:
        raise FormatError(f"unreasonable tag1400 record count {record_count} in {source}")
    if record_count > (len(data) - cursor.offset) // TAG1400_RECORD_SIZE:
        raise BoundsError(f"tag1400 records are truncated in {source}")
    records: list[Tag1400Record56] = []
    for record_index in range(record_count):
        record_offset = cursor.offset
        values = cursor.unpack("<9fI4f", f"tag1400 record {record_index}")
        ref_index = values[9]
        if ref_index >= string_count:
            raise FormatError(
                f"tag1400 record {record_index} at 0x{record_offset:X} references string "
                f"{ref_index}, table size is {string_count} in {source}"
            )
        records.append(Tag1400Record56(
            record_index,
            record_offset,
            tuple(values[:9]),
            ref_index,
            tuple(values[10:14]),
        ))

    if cursor.offset != len(data) and not allow_trailing:
        raise FormatError(
            f"tag1400 parser consumed 0x{cursor.offset:X} of 0x{len(data):X} bytes in {source}; "
            f"{len(data) - cursor.offset} trailing bytes remain"
        )

    return CourseTag1400(
        source=source,
        byte_size=len(data),
        tag_offset=tag_offset,
        scalar=scalar,
        dimension_0=dimension_0,
        dimension_1=dimension_1,
        vector_a=vector_a,
        vector_b=vector_b,
        cells=tuple(cells),
        strings=tuple(strings),
        records=tuple(records),
        consumed_size=cursor.offset,
    )
