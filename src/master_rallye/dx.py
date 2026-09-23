"""Bounds-checked parser for the evidenced Master Rallye vehicle DX layout."""
from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path

from .collision import parse_collision_sections
from .errors import BoundsError, FormatError, UnknownRecordEvidence, UnknownRecordTagError
from .model import (
    BoundingData,
    DrawGroup,
    DrawRecord,
    DxModel,
    GlobalIndexTable,
    TextureSlot,
    TrailingSection,
    UVSet,
    ValidationDiagnostics,
    VertexData,
)

MAGIC = 0x0000D00D
MAX_VERTICES = 10_000_000
MAX_UV_SETS = 8
MAX_INDICES = 100_000_000
MAX_TOP_LEVEL_RECORDS = 100_000
MAX_PHYSICAL_DRAWS = 200_000
MAX_TEXTURE_SLOTS = 32
MAX_STRING_BYTES = 4096
MAX_RECORD_DEPTH = 32


class Reader:
    def __init__(self, data: bytes, source: str):
        self.data = data
        self.source = source

    def require(self, offset: int, size: int, label: str) -> None:
        available = len(self.data) - offset
        if offset < 0 or size < 0 or available < size:
            raise BoundsError(
                f"{label} at 0x{offset:X} in {self.source}: "
                f"need {size} bytes, have {max(available, 0)}"
            )

    def unpack(self, fmt: str, offset: int, label: str):
        size = struct.calcsize(fmt)
        self.require(offset, size, label)
        return struct.unpack_from(fmt, self.data, offset)

    def u32(self, offset: int, label: str) -> int:
        return self.unpack("<I", offset, label)[0]

    def blob(self, offset: int, size: int, label: str) -> bytes:
        self.require(offset, size, label)
        return self.data[offset:offset + size]


def _read_length_string(reader: Reader, offset: int, label: str) -> tuple[str, int, int, int, bytes]:
    length_offset = offset
    length = reader.u32(offset, f"{label} length")
    offset += 4
    if length > MAX_STRING_BYTES:
        raise FormatError(f"{label} at 0x{length_offset:X}: unreasonable length {length}")
    data_offset = offset
    raw = reader.blob(offset, length, label)
    offset += length
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise FormatError(f"{label} at 0x{data_offset:X}: non-ASCII data") from exc
    return text, offset, length_offset, data_offset, raw


def _unknown_tag(reader: Reader, offset: int, tag: int, preceding: str | None) -> UnknownRecordTagError:
    start = max(0, offset - 32)
    end = min(len(reader.data), offset + 64)
    return UnknownRecordTagError(UnknownRecordEvidence(
        source=reader.source,
        offset=offset,
        tag=tag,
        context_start=start,
        context_hex=reader.data[start:end].hex(" "),
        preceding_context=preceding,
    ))


def _parse_record(
    reader: Reader,
    offset: int,
    record_path: str,
    physical_counter: list[int],
    preceding: str | None = None,
) -> tuple[DrawRecord, int]:
    physical_counter[0] += 1
    if physical_counter[0] > MAX_PHYSICAL_DRAWS:
        raise FormatError(f"physical draw count exceeds {MAX_PHYSICAL_DRAWS}")

    start = offset
    tag = reader.u32(offset, f"draw record {record_path} tag")
    group_label: str | None = None
    control_words: tuple[int, ...] = ()
    child_count = 0

    if tag == 2:
        core_offset = offset
    elif tag == 7:
        group_label, offset, _, _, _ = _read_length_string(
            reader, offset + 4, f"draw record {record_path} label"
        )
        reader.require(offset, 20, f"draw record {record_path} type-7 control words")
        control_words = reader.unpack("<5I", offset, f"draw record {record_path} type-7 control words")
        child_count = control_words[4]
        if child_count > MAX_PHYSICAL_DRAWS:
            raise FormatError(f"draw record {record_path}: unreasonable child count {child_count}")
        offset += 20
        core_offset = offset
    elif tag == 8:
        reader.require(offset + 4, 8, f"draw record {record_path} type-8 control words")
        control_words = reader.unpack("<2I", offset + 4, f"draw record {record_path} type-8 control words")
        core_offset = offset + 12
    else:
        raise _unknown_tag(reader, offset, tag, preceding)

    core = reader.blob(core_offset, 40, f"draw record {record_path} core")
    words = struct.unpack("<10I", core)
    if words[0] != 2:
        raise FormatError(
            f"draw record {record_path} at 0x{start:X}: "
            f"embedded core tag {words[0]}, expected 2"
        )
    unknown_float = struct.unpack_from("<f", core, 0x1C)[0]
    offset = core_offset + 40
    slot_count = reader.u32(offset, f"draw record {record_path} texture slot count")
    offset += 4
    if slot_count > MAX_TEXTURE_SLOTS:
        raise FormatError(f"draw record {record_path}: unreasonable texture slot count {slot_count}")

    slots: list[TextureSlot] = []
    for slot_index in range(slot_count):
        value, offset, length_offset, data_offset, raw = _read_length_string(
            reader, offset, f"draw record {record_path} texture {slot_index}"
        )
        slots.append(TextureSlot(slot_index, value, length_offset, data_offset, raw))

    terminal_offset = offset
    terminal = reader.u32(offset, f"draw record {record_path} terminal")
    offset += 4
    if terminal != 0:
        raise FormatError(
            f"draw record {record_path} terminal at 0x{terminal_offset:X}: expected 0, got {terminal}"
        )

    return DrawRecord(
        record_path=record_path,
        tag=tag,
        offset=start,
        size=offset - start,
        own_size=offset - start,
        core_offset=core_offset,
        group_label=group_label,
        control_words=tuple(control_words),
        declared_child_count=child_count,
        vertex_base=words[1],
        local_vertex_max=words[2],
        index_start=words[3],
        index_count=words[4],
        unknown_0x14=words[5],
        unknown_0x18=words[6],
        unknown_0x1c_float=unknown_float,
        flags_0x20=core[0x20:0x24],
        unknown_0x24=words[9],
        texture_slots=slots,
        terminal_offset=terminal_offset,
    ), offset


def _bbox(positions: tuple[tuple[float, float, float], ...]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    return (
        tuple(min(value[axis] for value in positions) for axis in range(3)),
        tuple(max(value[axis] for value in positions) for axis in range(3)),
    )


def _classify_trailing(
    data: bytes,
    offset: int,
    positions: tuple[tuple[float, float, float], ...],
) -> TrailingSection:
    trailing = data[offset:]
    digest = hashlib.sha256(trailing).hexdigest()
    if not trailing:
        return TrailingSection(offset, trailing, "none", digest)
    if len(trailing) != 56:
        return TrailingSection(offset, trailing, "opaque", digest)

    minimum = struct.unpack_from("<3f", trailing, 0x20)
    maximum = struct.unpack_from("<3f", trailing, 0x2C)
    actual_minimum, actual_maximum = _bbox(positions)
    matches = all(
        math.isclose(observed, actual, rel_tol=0.0, abs_tol=1e-5)
        for observed, actual in zip(minimum + maximum, actual_minimum + actual_maximum)
    )
    bounding = BoundingData(
        unknown_0x00_u32=struct.unpack_from("<I", trailing, 0)[0],
        unknown_0x04_float=struct.unpack_from("<f", trailing, 4)[0],
        unknown_0x08_float=struct.unpack_from("<f", trailing, 8)[0],
        unknown_0x0c_u32=struct.unpack_from("<I", trailing, 12)[0],
        midpoint=struct.unpack_from("<3f", trailing, 0x10),
        unknown_0x1c_float=struct.unpack_from("<f", trailing, 0x1C)[0],
        minimum=minimum,
        maximum=maximum,
        matches_positions=matches,
    )
    family = "footer56-bounds" if matches else "footer56-unmatched"
    return TrailingSection(offset, trailing, family, digest, bounding)


def _validate(
    vertex_count: int,
    local_indices: tuple[int, ...],
    draws: list[DrawRecord],
    stored_indices: tuple[int, ...] | None,
) -> tuple[ValidationDiagnostics, bool, int]:
    diagnostics = ValidationDiagnostics()
    index_owners: list[list[int]] = [[] for _ in local_indices]
    vertex_owners: list[list[int]] = [[] for _ in range(vertex_count)]
    expected: list[int | None] = [None] * len(local_indices)
    conflicts = 0

    for draw_index, draw in enumerate(draws):
        draw.draw_index = draw_index
        if draw.index_count % 3:
            diagnostics.errors.append(
                f"draw {draw.record_path}: index_count {draw.index_count} is not divisible by 3"
            )
        if draw.index_start > len(local_indices) or draw.index_count > len(local_indices) - draw.index_start:
            diagnostics.errors.append(
                f"draw {draw.record_path}: index range {draw.index_start}+{draw.index_count} "
                f"exceeds {len(local_indices)}"
            )
            continue

        vertex_end = draw.vertex_base + draw.local_vertex_max
        vertex_range_valid = draw.vertex_base < vertex_count and vertex_end < vertex_count
        if not vertex_range_valid:
            diagnostics.errors.append(
                f"draw {draw.record_path}: vertex range {draw.vertex_base}..{vertex_end} "
                f"exceeds {vertex_count}"
            )
        else:
            for vertex_index in range(draw.vertex_base, vertex_end + 1):
                vertex_owners[vertex_index].append(draw_index)

        raw = local_indices[draw.index_start:draw.index_start + draw.index_count]
        draw.raw_index_min = min(raw) if raw else None
        draw.raw_index_max = max(raw) if raw else None
        if raw and max(raw) > draw.local_vertex_max:
            diagnostics.errors.append(
                f"draw {draw.record_path}: local index max {max(raw)} exceeds declared {draw.local_vertex_max}"
            )
        global_values = [value + draw.vertex_base for value in raw]
        draw.global_vertex_min = min(global_values) if global_values else None
        draw.global_vertex_max = max(global_values) if global_values else None
        if global_values and max(global_values) >= vertex_count:
            diagnostics.errors.append(
                f"draw {draw.record_path}: reconstructed vertex {max(global_values)} exceeds {vertex_count - 1}"
            )

        for relative in range(0, len(raw) - 2, 3):
            source_position = draw.index_start + relative
            triangle = (
                raw[relative + 1] + draw.vertex_base,
                raw[relative] + draw.vertex_base,
                raw[relative + 2] + draw.vertex_base,
            )
            for corner, value in enumerate(triangle):
                position = source_position + corner
                index_owners[position].append(draw_index)
                if expected[position] is None:
                    expected[position] = value
                elif expected[position] != value:
                    conflicts += 1

    uncovered_indices = sum(not owners for owners in index_owners)
    overlapping_indices = sum(len(owners) > 1 for owners in index_owners)
    unused_vertices = sum(not owners for owners in vertex_owners)
    shared_vertices = sum(len(owners) > 1 for owners in vertex_owners)
    diagnostics.uncovered_index_count = uncovered_indices
    diagnostics.overlapping_index_count = overlapping_indices
    diagnostics.unused_vertex_count = unused_vertices
    diagnostics.shared_vertex_count = shared_vertices

    if uncovered_indices and overlapping_indices:
        diagnostics.index_coverage = "gaps-and-overlap"
    elif uncovered_indices:
        diagnostics.index_coverage = "gaps"
    elif overlapping_indices:
        diagnostics.index_coverage = "overlap"
    else:
        diagnostics.index_coverage = "complete-disjoint"
    if unused_vertices and shared_vertices:
        diagnostics.vertex_coverage = "unused-and-shared"
    elif unused_vertices:
        diagnostics.vertex_coverage = "unused"
    elif shared_vertices:
        diagnostics.vertex_coverage = "shared"
    else:
        diagnostics.vertex_coverage = "complete-disjoint"

    if uncovered_indices:
        diagnostics.warnings.append(f"{uncovered_indices} local index entries are not covered by draws")
    if overlapping_indices:
        diagnostics.warnings.append(f"{overlapping_indices} local index entries are covered by multiple draws")
    if unused_vertices:
        diagnostics.warnings.append(f"{unused_vertices} vertices are outside declared draw ranges")
    if shared_vertices:
        diagnostics.warnings.append(f"{shared_vertices} vertices occur in multiple declared draw ranges")
    if conflicts:
        diagnostics.errors.append(f"{conflicts} overlapping index positions reconstruct to conflicting vertices")

    compared = 0
    exact = False
    if stored_indices is None:
        diagnostics.warnings.append("stored global index table is absent")
    else:
        if len(stored_indices) != len(local_indices):
            diagnostics.errors.append(
                f"stored global index count {len(stored_indices)} does not match local count {len(local_indices)}"
            )
        limit = min(len(stored_indices), len(expected))
        mismatches = []
        for index in range(limit):
            if expected[index] is None:
                continue
            compared += 1
            if expected[index] != stored_indices[index]:
                mismatches.append(index)
        if mismatches:
            first = mismatches[0]
            diagnostics.errors.append(
                f"stored global indices differ at {len(mismatches)} covered positions; first 0x{first:X}"
            )
        exact = (
            len(stored_indices) == len(local_indices)
            and uncovered_indices == 0
            and conflicts == 0
            and not mismatches
        )
    diagnostics.reconstructed_global_match = exact
    return diagnostics, exact, compared


def parse_dx_bytes(data: bytes, source: str = "<bytes>", source_path: Path | None = None) -> DxModel:
    reader = Reader(data, source)
    reader.require(0, 16, "DX header")
    magic, word_0x04, word_0x08, vertex_count = reader.unpack("<4I", 0, "DX header")
    if magic != MAGIC:
        raise FormatError(f"bad DX magic 0x{magic:08X} in {source}, expected 0x{MAGIC:08X}")
    if not 0 < vertex_count <= MAX_VERTICES:
        raise FormatError(f"unreasonable vertex count {vertex_count} in {source}")

    offset = 16
    position_offset = offset
    reader.require(offset, vertex_count * 12, "position section")
    positions = tuple(reader.unpack("<3f", offset + index * 12, f"position {index}") for index in range(vertex_count))
    offset += vertex_count * 12
    normal_offset = offset
    reader.require(offset, vertex_count * 12, "normal section")
    normals = tuple(reader.unpack("<3f", offset + index * 12, f"normal {index}") for index in range(vertex_count))
    offset += vertex_count * 12
    color_offset = offset
    colors = reader.blob(offset, vertex_count * 4, "color section")
    offset += vertex_count * 4

    uv_count_offset = offset
    uv_count = reader.u32(offset, "UV set count")
    offset += 4
    if uv_count > MAX_UV_SETS:
        raise FormatError(f"unreasonable UV set count {uv_count} at 0x{uv_count_offset:X}")
    uv_sets: list[UVSet] = []
    for uv_index in range(uv_count):
        uv_offset = offset
        reader.require(offset, vertex_count * 8, f"UV set {uv_index}")
        values = tuple(reader.unpack("<2f", offset + index * 8, f"UV set {uv_index} entry {index}") for index in range(vertex_count))
        uv_sets.append(UVSet(uv_offset, values))
        offset += vertex_count * 8

    local_count_offset = offset
    local_count = reader.u32(offset, "local index count")
    offset += 4
    if local_count > MAX_INDICES:
        raise FormatError(f"unreasonable local index count {local_count} at 0x{local_count_offset:X}")
    local_offset = offset
    reader.require(offset, local_count * 2, "local index array")
    local_indices = tuple(reader.unpack(f"<{local_count}H", offset, "local index array")) if local_count else ()
    offset += local_count * 2

    draw_table_offset = offset
    reader.require(offset, 8, "draw table envelope")
    draw_preamble = reader.u32(offset, "draw table preamble")
    top_count = reader.u32(offset + 4, "top-level draw record count")
    offset += 8
    if top_count > MAX_TOP_LEVEL_RECORDS:
        raise FormatError(f"unreasonable top-level draw record count {top_count}")

    flat_records: list[DrawRecord] = []
    physical_counter = [0]
    preceding: str | None = None
    global_marker = False
    while True:
        if offset == len(data):
            break
        reader.require(offset, 4, "draw record or global index table")
        tag_or_preamble = reader.u32(offset, "draw record tag or global index preamble")
        if tag_or_preamble == 1 and len(data) - offset >= 8:
            candidate_count = reader.u32(offset + 4, "global index count")
            if candidate_count > MAX_INDICES:
                raise FormatError(f"unreasonable global index count {candidate_count} at 0x{offset + 4:X}")
            global_marker = True
            break
        record, offset = _parse_record(
            reader, offset, f"flat.{len(flat_records)}", physical_counter, preceding=preceding
        )
        flat_records.append(record)
        preceding = record.record_path

    global_table: GlobalIndexTable | None = None
    if global_marker:
        candidate_preamble = reader.u32(offset, "global index table preamble")
        candidate_count = reader.u32(offset + 4, "global index count")
        table_offset = offset
        offset += 8
        reader.require(offset, candidate_count * 4, "global index array")
        stored = tuple(reader.unpack(f"<{candidate_count}I", offset, "global index array")) if candidate_count else ()
        data_offset = offset
        offset += candidate_count * 4
        global_table = GlobalIndexTable(
            table_offset, candidate_preamble, candidate_count, data_offset, stored, False, 0
        )

    def consume_record(index: int, record_path: str, depth: int = 0) -> tuple[DrawRecord, int]:
        if depth > MAX_RECORD_DEPTH:
            raise FormatError(f"draw hierarchy exceeds {MAX_RECORD_DEPTH} levels")
        if index >= len(flat_records):
            raise FormatError(f"draw hierarchy at {record_path} requests a missing child")
        record = flat_records[index]
        record.record_path = record_path
        cursor = index + 1
        children: list[DrawRecord] = []
        for child_index in range(record.declared_child_count):
            child, cursor = consume_record(cursor, f"{record_path}.{child_index + 1}", depth + 1)
            children.append(child)
        record.children = children
        if children:
            record.size = children[-1].offset + children[-1].size - record.offset
        return record, cursor

    roots: list[DrawRecord] = []
    cursor = 0
    while cursor < len(flat_records):
        root, cursor = consume_record(cursor, str(len(roots)))
        roots.append(root)

    groups: list[DrawGroup] = []
    flat_draws: list[DrawRecord] = []
    for top_index, root in enumerate(roots):
        group_indices: list[int] = []
        for draw in root.flattened():
            draw.draw_index = len(flat_draws)
            draw.top_level_index = top_index
            group_indices.append(draw.draw_index)
            flat_draws.append(draw)
        groups.append(DrawGroup(top_index, root, group_indices))

    stored_indices = global_table.indices if global_table else None
    diagnostics, exact_match, compared_count = _validate(vertex_count, local_indices, flat_draws, stored_indices)
    if len(roots) != top_count:
        diagnostics.warnings.append(
            f"declared top-level count {top_count} differs from reconstructed root count {len(roots)}"
        )
    if global_table is not None:
        global_table = GlobalIndexTable(
            global_table.preamble_offset,
            global_table.preamble,
            global_table.count,
            global_table.data_offset,
            global_table.indices,
            exact_match,
            compared_count,
        )

    trailing = _classify_trailing(data, offset, positions)
    collision = parse_collision_sections(
        trailing.data, base_offset=offset, source=source, strict=False
    )
    if trailing.layout_family == "footer56-unmatched":
        diagnostics.warnings.append("56-byte trailing structure does not match the position bounds")

    vertices = VertexData(position_offset, normal_offset, color_offset, positions, normals, colors)
    return DxModel(
        source=source,
        source_path=source_path,
        byte_size=len(data),
        magic=magic,
        word_0x04=word_0x04,
        word_0x08=word_0x08,
        vertices=vertices,
        uv_count_offset=uv_count_offset,
        uv_sets=uv_sets,
        local_index_count_offset=local_count_offset,
        local_index_offset=local_offset,
        local_indices=local_indices,
        draw_table_offset=draw_table_offset,
        draw_table_preamble=draw_preamble,
        declared_top_level_record_count=top_count,
        draw_groups=groups,
        global_index_table=global_table,
        collision=collision,
        trailing=trailing,
        diagnostics=diagnostics,
    )


def parse_dx(path: Path) -> DxModel:
    resolved = path.resolve()
    return parse_dx_bytes(resolved.read_bytes(), resolved.name, resolved)
