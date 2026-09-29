"""Bounded read-only prefix probe for old course GXM resources.

The parser intentionally preserves the counted 16-byte bank as opaque bytes.
Its value semantics and the remaining post-bank grammar are not established.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path

from .errors import BoundsError, FormatError
from .course_source import CourseTxtDocument, CourseTxtNode


HEADER_SIZE = 32
OPAQUE_RECORD_STRIDE = 16
MAX_OPAQUE_RECORDS = 4_000_000


@dataclass(frozen=True)
class CourseGxmPrefix:
    source: str
    byte_size: int
    header_words: tuple[int, int, int, int, int, int, int, int]
    record_count: int
    record_stride: int
    record_offset: int
    record_end: int
    opaque_records: bytes
    opaque_tail: bytes


@dataclass(frozen=True)
class CourseGxmNode:
    ordinal: int
    class_name: str
    name: str
    parent_id: int | None
    class_code: int | None
    flags: int | None
    record_control_u16: int
    child_count: int
    mesh_index: int | None
    mesh_size: int | None
    record_offset: int
    record_size: int


@dataclass(frozen=True)
class CourseGxmObjectTable:
    source: str
    table_offset: int
    table_size: int
    nodes: tuple[CourseGxmNode, ...]
    root_name: str
    txt_crosscheck: str


@dataclass(frozen=True)
class CourseGxmFloat3Pool:
    """Header-bounded float3 bank; its point semantics remain corpus inference."""

    source: str
    offset: int
    count: int
    byte_size: int
    raw: bytes
    points: tuple[tuple[float, float, float], ...]


def parse_course_gxm_bytes(data: bytes, source: str = "<bytes>") -> CourseGxmPrefix:
    """Parse the fixed header and bounded opaque bank found in old course GXM.

    Header word 2 is used as a count of 16-byte records for this boundary probe.
    No position, transform, node, or helper semantics are assigned here.
    """
    if len(data) < HEADER_SIZE:
        raise BoundsError(f"course GXM header in {source}: need {HEADER_SIZE} bytes, have {len(data)}")
    header = struct.unpack_from("<8I", data, 0)
    record_count = header[2]
    if record_count > MAX_OPAQUE_RECORDS:
        raise FormatError(
            f"course GXM record count {record_count} in {source} exceeds {MAX_OPAQUE_RECORDS}"
        )
    record_offset = HEADER_SIZE
    record_end = record_offset + record_count * OPAQUE_RECORD_STRIDE
    if record_end > len(data):
        raise BoundsError(
            f"course GXM opaque bank in {source}: count {record_count} at 0x{record_offset:X} "
            f"requires end 0x{record_end:X}, file has {len(data)} bytes"
        )
    return CourseGxmPrefix(
        source=source,
        byte_size=len(data),
        header_words=tuple(header),
        record_count=record_count,
        record_stride=OPAQUE_RECORD_STRIDE,
        record_offset=record_offset,
        record_end=record_end,
        opaque_records=data[record_offset:record_end],
        opaque_tail=data[record_end:],
    )


def parse_course_gxm(path: Path) -> CourseGxmPrefix:
    resolved = path.resolve()
    return parse_course_gxm_bytes(resolved.read_bytes(), resolved.name)


def _expected_table_size(nodes: tuple[CourseTxtNode, ...]) -> int:
    if not nodes:
        raise FormatError("course TXT has no nodes; cannot bound the GXM object table")
    root = nodes[0]
    if root.class_name.casefold() != "momodel" or root.parent_id is not None:
        raise FormatError("course TXT root is not a parentless moModel node")
    size = 2 + len(root.name.encode("latin-1"))
    for node in nodes[1:]:
        encoded_name_size = len(node.name.encode("latin-1"))
        if node.class_name.casefold() == "momesh":
            size += 4 + 8 + 2 + encoded_name_size
        elif node.class_name.casefold() == "mounknown":
            size += 4 + 2 + encoded_name_size
        else:
            raise FormatError(f"unsupported course TXT node class {node.class_name!r}")
    return size


def _expected_direct_child_counts(nodes: tuple[CourseTxtNode, ...]) -> dict[int, int]:
    counts = {node.node_id: 0 for node in nodes}
    for node in nodes:
        if node.parent_id is not None:
            if node.parent_id not in counts:
                raise FormatError(f"course TXT node {node.node_id} has missing parent {node.parent_id}")
            counts[node.parent_id] += 1
    return counts


def parse_course_gxm_object_table_bytes(
    data: bytes,
    txt_document: CourseTxtDocument,
    source: str = "<bytes>",
) -> CourseGxmObjectTable:
    """Parse the exact trailing node records, cross-checked against the paired TXT.

    The paired TXT inventory supplies the expected sequence and therefore an
    exact table boundary. The parser validates every length, class, name,
    child count, and mesh span; it does not search for names in the GXM bytes.
    Current evidence covers old 8.4.1 France1 and Italy1 source pairs only.
    """
    if txt_document.unparsed_node_lines:
        line, text = txt_document.unparsed_node_lines[0]
        raise FormatError(f"paired course TXT has unparsed node at line {line}: {text!r}")
    nodes = txt_document.nodes
    expected_size = _expected_table_size(nodes)
    table_offset = len(data) - expected_size
    header = parse_course_gxm_bytes(data, source)
    if table_offset < header.record_end:
        raise BoundsError(
            f"course GXM object table in {source} overlaps the bounded header bank: "
            f"table starts 0x{table_offset:X}, bank ends 0x{header.record_end:X}"
        )

    offset = table_offset
    root = nodes[0]
    if offset + 2 > len(data):
        raise BoundsError(f"course GXM root name length in {source} is truncated")
    root_length = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    root_end = offset + root_length
    if root_end > len(data):
        raise BoundsError(f"course GXM root name in {source} is truncated")
    root_name = data[offset:root_end].decode("latin-1")
    offset = root_end
    if root_name != root.name:
        raise FormatError(
            f"course GXM root name {root_name!r} in {source} differs from paired TXT {root.name!r}"
        )
    parsed = [CourseGxmNode(
        ordinal=root.node_id,
        class_name=root.class_name,
        name=root_name,
        parent_id=None,
        class_code=None,
        flags=None,
        record_control_u16=0,
        child_count=sum(1 for node in nodes if node.parent_id == root.node_id),
        mesh_index=None,
        mesh_size=None,
        record_offset=table_offset,
        record_size=offset - table_offset,
    )]
    child_counts = _expected_direct_child_counts(nodes)

    for expected in nodes[1:]:
        start = offset
        if offset + 4 > len(data):
            raise BoundsError(f"course GXM node header {expected.node_id} in {source} is truncated")
        class_code, flags, record_control = struct.unpack_from("<BBH", data, offset)
        offset += 4
        class_name = expected.class_name.casefold()
        expected_code = 1 if class_name == "momesh" else 3
        if class_code != expected_code:
            raise FormatError(
                f"course GXM node {expected.node_id} {expected.name!r} in {source}: "
                f"class code {class_code} differs from paired TXT class {expected.class_name}"
            )
        if flags != 1:
            raise FormatError(
                f"course GXM node {expected.node_id} {expected.name!r} in {source}: "
                f"unobserved node flags {flags}"
            )

        mesh_index = mesh_size = None
        if class_name == "momesh":
            if offset + 8 > len(data):
                raise BoundsError(f"course GXM mesh span for {expected.name!r} in {source} is truncated")
            mesh_index, mesh_size = struct.unpack_from("<II", data, offset)
            offset += 8
            if (mesh_index, mesh_size) != (expected.mesh_index, expected.mesh_size):
                raise FormatError(
                    f"course GXM mesh span for {expected.name!r} in {source} is "
                    f"({mesh_index}, {mesh_size}), paired TXT says ({expected.mesh_index}, {expected.mesh_size})"
                )
        elif record_control != child_counts[expected.node_id]:
            raise FormatError(
                f"course GXM node {expected.name!r} in {source} declares {record_control} children, "
                f"paired TXT hierarchy has {child_counts[expected.node_id]}"
            )

        if offset + 2 > len(data):
            raise BoundsError(f"course GXM node name length for {expected.name!r} in {source} is truncated")
        name_length = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        name_end = offset + name_length
        if name_end > len(data):
            raise BoundsError(f"course GXM node name for {expected.name!r} in {source} is truncated")
        name = data[offset:name_end].decode("latin-1")
        offset = name_end
        if name != expected.name:
            raise FormatError(
                f"course GXM node name {name!r} at ordinal {expected.node_id} in {source} "
                f"differs from paired TXT {expected.name!r}"
            )
        parsed.append(CourseGxmNode(
            ordinal=expected.node_id,
            class_name=expected.class_name,
            name=name,
            parent_id=expected.parent_id,
            class_code=class_code,
            flags=flags,
            record_control_u16=record_control,
            child_count=child_counts[expected.node_id],
            mesh_index=mesh_index,
            mesh_size=mesh_size,
            record_offset=start,
            record_size=offset - start,
        ))

    if offset != len(data):
        raise FormatError(
            f"course GXM node table in {source} consumed through 0x{offset:X}, "
            f"file ends at 0x{len(data):X}"
        )
    return CourseGxmObjectTable(
        source,
        table_offset,
        len(data) - table_offset,
        tuple(parsed),
        root_name,
        "exact names, node classes, hierarchy child counts, and mesh spans match paired TXT",
    )


def parse_course_gxm_float3_pool_bytes(
    data: bytes,
    object_table: CourseGxmObjectTable,
    source: str = "<bytes>",
) -> CourseGxmFloat3Pool:
    """Read the final header-counted float3 bank before an exact node table.

    The current France1, Italy1, and Boinds source/cooked comparisons support
    interpreting this bank as course points. This parser preserves the raw
    values and does not associate them with individual node mesh spans.
    """
    header = parse_course_gxm_bytes(data, source)
    if object_table.table_offset < header.record_end:
        raise BoundsError(f"course GXM object table in {source} overlaps the header bank")
    if object_table.table_offset + object_table.table_size != len(data):
        raise FormatError(f"course GXM object table boundary does not match {source} length")
    count = header.header_words[7]
    byte_size = count * 12
    offset = object_table.table_offset - byte_size
    if offset < header.record_end:
        raise BoundsError(
            f"course GXM float3 pool in {source}: count {count} at 0x{offset:X} overlaps "
            f"the bounded header bank ending at 0x{header.record_end:X}"
        )
    raw = data[offset:object_table.table_offset]
    if len(raw) != byte_size:
        raise BoundsError(
            f"course GXM float3 pool in {source}: expected {byte_size} bytes, got {len(raw)}"
        )
    points = tuple(struct.iter_unpack("<3f", raw))
    for index, point in enumerate(points):
        if not all(math.isfinite(value) for value in point):
            raise FormatError(f"course GXM float3 pool in {source} has non-finite point at index {index}")
    return CourseGxmFloat3Pool(source, offset, count, byte_size, raw, points)
