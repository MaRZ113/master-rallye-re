"""Read-only course DX render interpretation layered on shared DX primitives."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .collision import parse_collision_sections
from .dx import (
    MAX_PHYSICAL_DRAWS,
    Reader,
    _classify_trailing,
    _parse_record,
    _validate,
    parse_dx_common_prefix,
)
from .errors import FormatError
from .model import DrawGroup, DrawRecord, DxModel, ValidationDiagnostics


MAX_COURSE_BATCHES = 10_000
MAX_COURSE_RECORD_DEPTH = 64


@dataclass(frozen=True)
class CourseDrawWrapper:
    offset: int
    tag: int
    control_words: tuple[int, int, int]
    child_count: int


@dataclass(frozen=True)
class CourseDrawBatch:
    offset: int
    preamble: int
    record_count: int
    records: tuple[DrawRecord, ...]
    raw: bytes


@dataclass
class CourseDxModel(DxModel):
    """Course render arrays plus bounded raw descriptions of unknown wrappers."""

    course_wrapper: CourseDrawWrapper | None
    course_root_records: tuple[DrawRecord, ...]
    course_batches: tuple[CourseDrawBatch, ...]

    @property
    def physical_draws(self) -> list[DrawRecord]:
        """Return index-bearing records and omit the opaque tag-5 containers."""
        result: list[DrawRecord] = []
        for group in self.draw_groups:
            for record in group.root.flattened():
                if record.tag in {1, 4, 5, 6} and record.opaque_prefix is not None and record.index_count == 0:
                    continue
                result.append(record)
        return result

    @property
    def course_render_validated(self) -> bool:
        """Require complete, non-overlapping draw coverage and valid references."""
        return (
            not self.diagnostics.errors
            and self.diagnostics.index_coverage == "complete-disjoint"
            and self.diagnostics.uncovered_index_count == 0
            and self.diagnostics.overlapping_index_count == 0
        )


def _parse_course_record(
    reader: Reader,
    offset: int,
    record_path: str,
    physical_counter: list[int],
    *,
    preceding: str | None = None,
    depth: int = 0,
) -> tuple[DrawRecord, int]:
    if depth > MAX_COURSE_RECORD_DEPTH:
        raise FormatError(f"course draw nesting exceeds {MAX_COURSE_RECORD_DEPTH} at 0x{offset:X}")
    tag = reader.u32(offset, f"course draw record {record_path} tag")
    if tag not in {1, 4, 5, 6}:
        record, end = _parse_record(
            reader, offset, record_path, physical_counter, preceding=preceding
        )
        return record, end

    if physical_counter[0] >= MAX_PHYSICAL_DRAWS:
        raise FormatError(f"course draw record count exceeds {MAX_PHYSICAL_DRAWS}")
    physical_counter[0] += 1
    start = offset
    prefix_size = {1: 4, 4: 12, 5: 20, 6: 20}[tag]
    own_size = prefix_size + 4
    label = f"course tag-{tag} record {record_path}"
    reader.require(start, own_size, f"{label} prefix")
    raw_prefix = reader.blob(start + 4, prefix_size, f"{label} opaque prefix")
    if tag == 4:
        control_words = reader.unpack("<3I", start + 4, f"{label} controls")
        child_count = control_words[2]
    elif tag == 1:
        control_words = (reader.u32(start + 4, f"{label} child count"),)
        child_count = control_words[0]
    elif tag == 6:
        control_words = (reader.u32(start + 20, f"{label} child count"),)
        child_count = control_words[0]
    else:
        control_words = (reader.u32(start + 20, f"{label} child count"),)
        child_count = control_words[0]
    if child_count > MAX_PHYSICAL_DRAWS:
        raise FormatError(f"course tag-5 record {record_path}: unreasonable child count {child_count}")
    offset = start + own_size
    children: list[DrawRecord] = []
    previous = record_path
    for child_index in range(child_count):
        child, offset = _parse_course_record(
            reader,
            offset,
            f"{record_path}.{child_index}",
            physical_counter,
            preceding=previous,
            depth=depth + 1,
        )
        children.append(child)
        previous = child.record_path
    return DrawRecord(
        record_path=record_path,
        tag=tag,
        offset=start,
        size=offset - start,
        own_size=own_size,
        core_offset=start + own_size,
        group_label=None,
        control_words=tuple(control_words),
        declared_child_count=child_count,
        vertex_base=0,
        local_vertex_max=0,
        index_start=0,
        index_count=0,
        unknown_0x14=0,
        unknown_0x18=0,
        unknown_0x1c_float=0.0,
        flags_0x20=b"",
        unknown_0x24=0,
        texture_slots=[],
        terminal_offset=start + own_size - 4,
        children=children,
        opaque_prefix=raw_prefix,
    ), offset


def _index_records(root: DrawRecord) -> list[DrawRecord]:
    return [
        item for item in root.flattened()
        if not (item.tag in {1, 4, 5, 6} and item.opaque_prefix is not None and item.index_count == 0)
    ]


def _records_to_groups(roots: list[DrawRecord]) -> tuple[list[DrawGroup], list[DrawRecord]]:
    groups: list[DrawGroup] = []
    physical: list[DrawRecord] = []
    for group_id, root in enumerate(roots):
        records = _index_records(root)
        for record in records:
            record.top_level_index = group_id
            record.draw_index = len(physical)
            physical.append(record)
        groups.append(DrawGroup(group_id, root, [record.draw_index for record in records]))
    return groups, physical


def parse_course_dx_bytes(
    data: bytes,
    source: str = "<bytes>",
    source_path: Path | None = None,
) -> CourseDxModel:
    """Parse rev-135 course render batches with shared tag-2/tag-7/tag-8 draws.

    The common arrays and existing draw records are reused. The initial tag-4
    wrapper, sequential ``(1, count)`` course batches, and tag-5 four-word
    prefix are course-side grammar. Tag-5 raw bytes are retained without
    assigning a meaning to their four floats.
    """
    prefix = parse_dx_common_prefix(data, source)
    if prefix.word_0x04 != 135:
        raise FormatError(
            f"course DX revision {prefix.word_0x04} in {source} is not the observed revision 135"
        )

    reader = Reader(data, source)
    offset = prefix.draw_table_offset
    reader.require(offset, 8, "course root draw envelope")
    root_preamble, root_count = reader.unpack("<2I", offset, "course root draw envelope")
    if root_preamble != 1:
        raise FormatError(
            f"unsupported course root preamble {root_preamble} at 0x{offset:X} in {source}"
        )
    offset += 8
    wrapper: CourseDrawWrapper | None = None
    root_records: list[DrawRecord] = []
    physical_counter = [0]
    if root_count > MAX_PHYSICAL_DRAWS:
        raise FormatError(f"unreasonable course root record count {root_count} in {source}")
    previous = "course.root"
    for record_index in range(root_count):
        record, offset = _parse_course_record(
            reader,
            offset,
            f"course.root.{record_index}",
            physical_counter,
            preceding=previous,
        )
        root_records.append(record)
        previous = record.record_path
    if root_count == 1 and root_records[0].tag == 4:
        root = root_records[0]
        wrapper = CourseDrawWrapper(
            root.offset, root.tag, tuple(root.control_words), root.declared_child_count
        )

    roots = list(root_records)
    batches: list[CourseDrawBatch] = []
    while len(data) - offset >= 8:
        batch_preamble, batch_count = reader.unpack("<2I", offset, "course draw batch envelope")
        if batch_preamble != 1:
            break
        if batch_count > MAX_PHYSICAL_DRAWS:
            raise FormatError(
                f"unreasonable course draw batch count {batch_count} at 0x{offset:X} in {source}"
            )
        if len(batches) >= MAX_COURSE_BATCHES:
            raise FormatError(f"course draw batch count exceeds {MAX_COURSE_BATCHES} in {source}")
        batch_offset = offset
        offset += 8
        batch_records: list[DrawRecord] = []
        previous = f"course.batch.{len(batches)}"
        for record_index in range(batch_count):
            record, offset = _parse_course_record(
                reader,
                offset,
                f"course.batch.{len(batches)}.{record_index}",
                physical_counter,
                preceding=previous,
            )
            batch_records.append(record)
            previous = record.record_path
        batches.append(CourseDrawBatch(
            batch_offset,
            batch_preamble,
            batch_count,
            tuple(batch_records),
            data[batch_offset:offset],
        ))
        roots.extend(batch_records)

    groups, physical_draws = _records_to_groups(roots)
    diagnostics, _, _ = _validate(
        len(prefix.vertices.positions), prefix.local_indices, physical_draws, None
    )
    diagnostics.warnings = [
        warning for warning in diagnostics.warnings
        if warning != "stored global index table is absent"
    ]
    diagnostics.warnings.append(
        "course draw batches parsed; trailing course/BSP payload remains separately classified"
    )

    trailing = _classify_trailing(data, offset, prefix.vertices.positions)
    collision = parse_collision_sections(
        trailing.data, base_offset=offset, source=source, strict=False
    )
    return CourseDxModel(
        source=source,
        source_path=source_path,
        byte_size=len(data),
        magic=prefix.magic,
        word_0x04=prefix.word_0x04,
        word_0x08=prefix.word_0x08,
        vertices=prefix.vertices,
        uv_count_offset=prefix.uv_count_offset,
        uv_sets=list(prefix.uv_sets),
        local_index_count_offset=prefix.local_index_count_offset,
        local_index_offset=prefix.local_index_offset,
        local_indices=prefix.local_indices,
        draw_table_offset=prefix.draw_table_offset,
        draw_table_preamble=root_preamble,
        declared_top_level_record_count=root_count,
        draw_groups=groups,
        global_index_table=None,
        collision=collision,
        trailing=trailing,
        diagnostics=diagnostics,
        course_wrapper=wrapper,
        course_root_records=tuple(root_records),
        course_batches=tuple(batches),
    )


def parse_course_dx(path: Path) -> CourseDxModel:
    resolved = path.resolve()
    return parse_course_dx_bytes(resolved.read_bytes(), resolved.name, resolved)
