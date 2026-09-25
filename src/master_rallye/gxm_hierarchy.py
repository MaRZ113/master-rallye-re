"""Narrow reader for the typed hierarchy tail found in demo 9.3.1 Trooper GXM.

This is not a general GXM hierarchy parser. It supports only node type 1,
version 1 records, whose layout is confirmed by the exact 9.3.1 EXE.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from .errors import BoundsError, FormatError

MAX_DEPTH = 64
MAX_NODES = 100_000
MAX_NAME_BYTES = 4096


@dataclass(frozen=True)
class GxmNode:
    name: str
    node_type: int
    version: int
    child_count: int
    mesh_start: int
    mesh_count: int
    record_offset: int
    name_offset: int
    children: tuple["GxmNode", ...]


@dataclass(frozen=True)
class GxmHierarchy:
    root_name: str
    roots: tuple[GxmNode, ...]
    tail_offset: int
    tail_size: int
    consumed_size: int
    node_count: int


def _need(data: bytes, offset: int, size: int) -> None:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise BoundsError(f"GXM hierarchy needs {size} bytes at 0x{offset:X}; size={len(data)}")


def _read_name(data: bytes, offset: int) -> tuple[str, int]:
    _need(data, offset, 2)
    size = struct.unpack_from("<H", data, offset)[0]
    if size > MAX_NAME_BYTES:
        raise FormatError(f"GXM hierarchy name length {size} at 0x{offset:X} exceeds limit")
    offset += 2
    _need(data, offset, size)
    try:
        name = data[offset:offset + size].decode("ascii")
    except UnicodeDecodeError as exc:
        raise FormatError(f"non-ASCII GXM hierarchy name at 0x{offset:X}") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise FormatError(f"control byte in GXM hierarchy name at 0x{offset:X}")
    return name, offset + size


def parse_gxm_hierarchy_tail(data: bytes, tail_offset: int, *, tail_size: int | None = None) -> GxmHierarchy:
    """Parse a root name plus type-1/version-1 records through the bounded tail.

    Each record is `<u8 type, u8 version, u16 children, u32 start, u32 count,
    u16 name_bytes, name, child records...>`. Top-level roots are consumed until
    the tail boundary because the root name has no count field in this layout.
    """
    if tail_size is None:
        tail_size = len(data) - tail_offset
    _need(data, tail_offset, tail_size)
    end = tail_offset + tail_size
    root_name, offset = _read_name(data, tail_offset)
    if offset > end:
        raise BoundsError("GXM hierarchy root name exceeds the bounded tail")
    if root_name != "Model":
        raise FormatError(f"unsupported GXM hierarchy root {root_name!r}; expected 'Model'")
    node_count = 0

    def read_node(pos: int, depth: int) -> tuple[GxmNode, int]:
        nonlocal node_count
        if depth > MAX_DEPTH:
            raise FormatError(f"GXM hierarchy exceeds depth limit {MAX_DEPTH}")
        if pos + 12 > end:
            raise BoundsError(f"truncated GXM node header/range at 0x{pos:X}")
        record_offset = pos
        node_type, version, child_count = struct.unpack_from("<BBH", data, pos)
        if (node_type, version) != (1, 1):
            raise FormatError(f"unsupported GXM node type/version {node_type}/{version} at 0x{pos:X}")
        mesh_start, mesh_count = struct.unpack_from("<II", data, pos + 4)
        name_offset = pos + 12
        name, pos = _read_name(data, name_offset)
        if pos > end:
            raise BoundsError(f"GXM node name exceeds bounded tail at 0x{name_offset:X}")
        node_count += 1
        if node_count > MAX_NODES:
            raise FormatError(f"GXM hierarchy exceeds node limit {MAX_NODES}")
        children = []
        for _ in range(child_count):
            child, pos = read_node(pos, depth + 1)
            children.append(child)
        return GxmNode(name, node_type, version, child_count, mesh_start, mesh_count,
                       record_offset, name_offset, tuple(children)), pos

    roots = []
    while offset < end:
        node, offset = read_node(offset, 0)
        roots.append(node)
    if offset != end:
        raise FormatError(f"GXM hierarchy ended at 0x{offset:X}, expected 0x{end:X}")
    if not roots:
        raise FormatError("GXM Model hierarchy has no top-level nodes")
    return GxmHierarchy(root_name, tuple(roots), tail_offset, tail_size,
                        offset - tail_offset, node_count)


def walk_depth_first(roots: tuple[GxmNode, ...]):
    """Yield nodes in loader preorder: node, then its children in stored order."""
    for node in roots:
        yield node
        yield from walk_depth_first(node.children)


def find_nodes(roots: tuple[GxmNode, ...], name: str) -> tuple[GxmNode, ...]:
    return tuple(node for node in walk_depth_first(roots) if node.name == name)


@dataclass(frozen=True)
class RuntimeNodeBinding:
    """Static loader-derived binding; native process addresses are unavailable."""
    node: GxmNode
    parent_name: str | None
    previous_sibling_name: str | None
    next_sibling_name: str | None
    child_pointer_offset: int = 0x04
    sibling_pointer_offset: int = 0x08
    parent_pointer_offset: int = 0x0C
    name_pointer_offset: int = 0x14
    mesh_start_offset: int = 0x1C
    mesh_count_offset: int = 0x20


def runtime_node_bindings(roots: tuple[GxmNode, ...]) -> tuple[RuntimeNodeBinding, ...]:
    """Map serialized nesting/order to EXE-confirmed runtime link slots."""
    result: list[RuntimeNodeBinding] = []

    def visit_siblings(nodes: tuple[GxmNode, ...], parent_name: str | None) -> None:
        for index, node in enumerate(nodes):
            result.append(RuntimeNodeBinding(
                node=node,
                parent_name=parent_name,
                previous_sibling_name=nodes[index - 1].name if index else None,
                next_sibling_name=nodes[index + 1].name if index + 1 < len(nodes) else None,
            ))
            visit_siblings(node.children, node.name)

    visit_siblings(roots, None)
    return tuple(result)


@dataclass(frozen=True)
class SerializedTriangle:
    record_index: int
    c_indices: tuple[int, int, int]


def serialized_c_triangle_stream(
    data: bytes, record_offset: int, total_records: int, start: int, count: int
) -> tuple[SerializedTriangle, ...]:
    """Read source record C-index triples; this is pre-normalizer, not runtime proof."""
    if min(record_offset, total_records, start, count) < 0 or start + count > total_records:
        raise FormatError("serialized GXM triangle range is outside the declared record table")
    _need(data, record_offset, total_records * 52)
    result = []
    for index in range(start, start + count):
        values = struct.unpack_from("<3I", data, record_offset + index * 52 + 16)
        result.append(SerializedTriangle(index, values))
    return tuple(result)
