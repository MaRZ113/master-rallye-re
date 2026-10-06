"""Read-only, loader-guided parser for the revision-135 trailing tag-100 region.

Names in this module describe wire shape and allocation role only. The full
runtime meaning of the records is not established by their serialized form.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from .errors import BoundsError, FormatError


TAG100 = 100
TAG100_HEADER_SIZE = 24  # tag word followed by five uint32 values
MAX_TAG100_NODES = 2_000_000
MAX_TAG100_LIST_ITEMS = 2_000_000
MAX_TAG100_NESTING = 65_536


@dataclass(frozen=True)
class Tag100Float4Code:
    offset: int
    values: tuple[float, float, float, float]
    code: int


@dataclass(frozen=True)
class Tag100Vector3FloatCode:
    offset: int
    vector: tuple[float, float, float]
    value: float
    code: int


@dataclass(frozen=True)
class Tag100Node:
    index: int
    offset: int
    depth: int
    allocation_role: str
    parent_index: int | None
    field_0: int
    field_1: int
    optional_record: Tag100Float4Code | None
    list_offset: int | None
    list_items: tuple[Tag100Vector3FloatCode, ...]
    first_child_index: int | None
    next_sibling_index: int | None


@dataclass(frozen=True)
class CourseTag100:
    source: str
    byte_size: int
    header_words: tuple[int, int, int, int, int]
    tree_offset: int
    root_index: int
    nodes: tuple[Tag100Node, ...]
    consumed_size: int
    allocation_role_counts: tuple[tuple[str, int], ...]
    list_item_count: int

    @property
    def trailing_size(self) -> int:
        return self.byte_size - self.consumed_size

    @property
    def complete(self) -> bool:
        return self.trailing_size == 0

    @property
    def optional_record_count(self) -> int:
        return sum(node.optional_record is not None for node in self.nodes)

    @property
    def list_block_count(self) -> int:
        return sum(node.list_offset is not None for node in self.nodes)

    def expected_wire_size(self) -> int:
        """Compute serialized bytes from parsed record counts.

        A present list also has a uint32 item count, so the general expression
        includes four bytes per list block. Retail rev135 files in the current
        corpus have no list blocks, reducing to 23 + 13*N + 20*P.
        """
        node_count = len(self.nodes)
        selector_count = max(0, node_count - 1)
        return (
            TAG100_HEADER_SIZE
            + 12 * node_count
            + 20 * self.optional_record_count
            + 4 * self.list_block_count
            + 20 * self.list_item_count
            + selector_count
        )

    def count_invariants(self) -> dict[str, bool]:
        """Return observed Retail hierarchy/count relationships without naming semantics."""
        word_0, word_1, word_2, word_3, _word_4 = self.header_words
        node_count = len(self.nodes)
        plane_bearing = self.optional_record_count
        terminal_like = node_count - plane_bearing
        return {
            "word0_plus_word1_eq_word2_plus_one": word_0 + word_1 == word_2 + 1,
            "word2_eq_word3": word_2 == word_3,
            "node_count_eq_word0_plus_word1_plus_word2": node_count == word_0 + word_1 + word_2,
            "plane_bearing_count_eq_word2": plane_bearing == word_2,
            "terminal_count_eq_plane_count_plus_one": terminal_like == plane_bearing + 1,
            "node_count_eq_twice_plane_count_plus_one": node_count == 2 * plane_bearing + 1,
            "wire_size_formula_matches_consumed_size": self.expected_wire_size() == self.consumed_size,
        }

    def structural_summary(self) -> dict:
        roles = dict(self.allocation_role_counts)
        return {
            "source": self.source,
            "byte_size": self.byte_size,
            "header_words": list(self.header_words),
            "tree_offset": self.tree_offset,
            "node_count": len(self.nodes),
            "allocation_role_counts": roles,
            "list_item_count": self.list_item_count,
            "list_block_count": self.list_block_count,
            "max_depth": max((node.depth for node in self.nodes), default=0),
            "optional_record_count": self.optional_record_count,
            "consumed_size": self.consumed_size,
            "expected_wire_size": self.expected_wire_size(),
            "count_invariants": self.count_invariants(),
            "trailing_size": self.trailing_size,
        }


class _Cursor:
    def __init__(self, data: bytes, source: str):
        self.data = data
        self.source = source
        self.offset = 0

    def _need(self, size: int, label: str) -> None:
        if size < 0 or self.offset < 0 or self.offset + size > len(self.data):
            raise BoundsError(
                f"{label} at 0x{self.offset:X} in {self.source} is truncated "
                f"(need {size} bytes, have {max(0, len(self.data) - self.offset)})"
            )

    def unpack(self, fmt: str, label: str):
        size = struct.calcsize(fmt)
        self._need(size, label)
        values = struct.unpack_from(fmt, self.data, self.offset)
        self.offset += size
        return values

    def boolean(self, label: str) -> bool:
        (value,) = self.unpack("<B", label)
        if value not in (0, 1):
            raise FormatError(
                f"{label} at 0x{self.offset - 1:X} in {self.source} has non-boolean value {value}"
            )
        return bool(value)


@dataclass
class _NodeBuilder:
    index: int
    offset: int
    depth: int
    allocation_role: str
    parent_index: int | None
    field_0: int
    field_1: int
    optional_record: Tag100Float4Code | None
    list_offset: int | None
    list_items: tuple[Tag100Vector3FloatCode, ...]
    first_child_index: int | None = None
    next_sibling_index: int | None = None


def parse_course_tag100_bytes(
    data: bytes, source: str = "<bytes>", *, allow_trailing: bool = False,
) -> CourseTag100:
    """Parse a tag-100 payload using the retail revision-135 loader grammar.

    The three allocation roles mirror the loader's typed pools: an 8-byte
    child-selected role, an 8-byte sibling-selected role, and a 36-byte role.
    These labels do not assign gameplay semantics to those objects.
    """
    cursor = _Cursor(data, source)
    (tag,) = cursor.unpack("<I", "tag100 identifier")
    if tag != TAG100:
        raise FormatError(f"expected tag 100 at 0x0 in {source}, found {tag}")
    header_words = tuple(cursor.unpack("<5I", "tag100 header counts"))
    if sum(header_words[:3]) > MAX_TAG100_NODES or header_words[4] > MAX_TAG100_LIST_ITEMS:
        raise FormatError(f"unreasonable tag100 header counts in {source}: {header_words}")
    tree_offset = cursor.offset

    builders: list[_NodeBuilder] = []
    role_counts = {"root": 0, "pool8_child": 0, "pool8_sibling": 0, "pool36": 0}
    list_item_count = 0

    # A pending node is (allocation role, parent index, depth, link kind, link source).
    pending: tuple[str, int | None, int, str, int | None] | None = ("root", None, 0, "root", None)
    # After a child chain ends, the parent node's sibling flag follows it in the stream.
    after_child: list[int] = []

    def read_sibling_for(node_index: int) -> tuple[str, int | None, int, str, int | None] | None:
        has_sibling = cursor.boolean("node sibling-present flag")
        if not has_sibling:
            return None
        selector = cursor.boolean("node sibling allocation selector")
        node = builders[node_index]
        role = "pool8_sibling" if selector else "pool36"
        return (role, node.parent_index, node.depth, "sibling", node_index)

    while pending is not None or after_child:
        if pending is None:
            parent_waiting = after_child.pop()
            pending = read_sibling_for(parent_waiting)
            continue

        role, parent_index, depth, link_kind, link_source = pending
        pending = None
        if depth > MAX_TAG100_NESTING:
            raise FormatError(f"tag100 nesting exceeds {MAX_TAG100_NESTING} in {source}")
        if len(builders) >= MAX_TAG100_NODES:
            raise FormatError(f"tag100 node count exceeds {MAX_TAG100_NODES} in {source}")

        node_offset = cursor.offset
        (field_0, field_1) = cursor.unpack("<2I", "tag100 node leading fields")
        has_optional = cursor.boolean("node optional-record flag")
        optional_record = None
        if has_optional:
            record_offset = cursor.offset
            values = cursor.unpack("<4fI", "tag100 float4/code record")
            optional_record = Tag100Float4Code(record_offset, tuple(values[:4]), values[4])

        has_list = cursor.boolean("node list-present flag")
        list_offset = None
        list_items: tuple[Tag100Vector3FloatCode, ...] = ()
        if has_list:
            (item_count,) = cursor.unpack("<I", "tag100 node list count")
            if item_count > MAX_TAG100_LIST_ITEMS or list_item_count + item_count > MAX_TAG100_LIST_ITEMS:
                raise FormatError(f"unreasonable tag100 node list count {item_count} in {source}")
            list_offset = cursor.offset
            items = []
            for _ in range(item_count):
                item_offset = cursor.offset
                values = cursor.unpack("<4fI", "tag100 float3/float/code list item")
                items.append(Tag100Vector3FloatCode(item_offset, tuple(values[:3]), values[3], values[4]))
            list_items = tuple(items)
            list_item_count += item_count

        has_child = cursor.boolean("node child-present flag")
        index = len(builders)
        builder = _NodeBuilder(
            index=index,
            offset=node_offset,
            depth=depth,
            allocation_role=role,
            parent_index=parent_index,
            field_0=field_0,
            field_1=field_1,
            optional_record=optional_record,
            list_offset=list_offset,
            list_items=list_items,
        )
        builders.append(builder)
        role_counts[role] += 1
        if link_kind == "child":
            assert parent_index is not None
            builders[parent_index].first_child_index = index
        elif link_kind == "sibling":
            assert link_source is not None
            builders[link_source].next_sibling_index = index

        if has_child:
            selector = cursor.boolean("node child allocation selector")
            after_child.append(index)
            child_role = "pool8_child" if selector else "pool36"
            pending = (child_role, index, depth + 1, "child", index)
        else:
            pending = read_sibling_for(index)

    if list_item_count > header_words[4]:
        raise FormatError(
            f"tag100 contains {list_item_count} list items, exceeds header count {header_words[4]} in {source}"
        )
    observed = (role_counts["pool8_child"], role_counts["pool8_sibling"], role_counts["pool36"])
    if any(value > declared for value, declared in zip(observed, header_words[:3])):
        raise FormatError(
            f"tag100 typed-pool use {observed} exceeds declared counts {header_words[:3]} in {source}"
        )
    if cursor.offset != len(data) and not allow_trailing:
        raise FormatError(
            f"tag100 parser consumed 0x{cursor.offset:X} of 0x{len(data):X} bytes in {source}; "
            f"{len(data) - cursor.offset} trailing bytes remain"
        )

    nodes = tuple(Tag100Node(
        index=node.index,
        offset=node.offset,
        depth=node.depth,
        allocation_role=node.allocation_role,
        parent_index=node.parent_index,
        field_0=node.field_0,
        field_1=node.field_1,
        optional_record=node.optional_record,
        list_offset=node.list_offset,
        list_items=node.list_items,
        first_child_index=node.first_child_index,
        next_sibling_index=node.next_sibling_index,
    ) for node in builders)
    return CourseTag100(
        source=source,
        byte_size=len(data),
        header_words=header_words,
        tree_offset=tree_offset,
        root_index=0,
        nodes=nodes,
        consumed_size=cursor.offset,
        allocation_role_counts=tuple(role_counts.items()),
        list_item_count=list_item_count,
    )


def translate_plane_distance(
    normal: tuple[float, float, float],
    distance: float,
    translation: tuple[float, float, float],
) -> float:
    """Return d' for n·x+d=0 after translating points by ``translation``."""
    if len(normal) != 3 or len(translation) != 3:
        raise ValueError("normal and translation must each have three components")
    values = (*normal, distance, *translation)
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("plane and translation values must be finite")
    return float(distance) - sum(float(n) * float(t) for n, t in zip(normal, translation))
