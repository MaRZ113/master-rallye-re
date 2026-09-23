"""Template-preserving, same-topology Master Rallye DX position writer."""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .dx import parse_dx_bytes
from .errors import DxWriteError
from .model import DxModel


@dataclass(frozen=True)
class ByteRange:
    start: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.start

    def to_dict(self) -> dict[str, int | str]:
        return {
            "start": self.start,
            "end": self.end,
            "start_hex": f"0x{self.start:X}",
            "size": self.size,
        }


@dataclass(frozen=True)
class PositionChange:
    vertex_index: int
    old_position: tuple[float, float, float]
    new_position: tuple[float, float, float]
    delta: tuple[float, float, float]
    source_offset: int
    changed_byte_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "vertex_index": self.vertex_index,
            "old_position": list(self.old_position),
            "new_position": list(self.new_position),
            "delta": list(self.delta),
            "source_offset": self.source_offset,
            "source_offset_hex": f"0x{self.source_offset:X}",
            "changed_byte_count": self.changed_byte_count,
        }


@dataclass(frozen=True)
class BinaryDiffAudit:
    changed_ranges: tuple[ByteRange, ...]
    allowed_ranges: tuple[ByteRange, ...]
    unexpected_ranges: tuple[ByteRange, ...]
    changed_byte_count: int

    @property
    def valid(self) -> bool:
        return not self.unexpected_ranges

    def to_dict(self) -> dict[str, object]:
        return {
            "changed_ranges": [item.to_dict() for item in self.changed_ranges],
            "allowed_ranges": [item.to_dict() for item in self.allowed_ranges],
            "unexpected_ranges": [item.to_dict() for item in self.unexpected_ranges],
            "changed_byte_count": self.changed_byte_count,
            "valid": self.valid,
        }


@dataclass(frozen=True)
class DxPositionPatchResult:
    data: bytes
    source_sha256: str
    output_sha256: str
    changes: tuple[PositionChange, ...]
    diff: BinaryDiffAudit
    original_model: DxModel
    output_model: DxModel
    section_hashes: dict[str, str]

    @property
    def byte_identical(self) -> bool:
        return (
            self.source_sha256 == self.output_sha256
            and self.diff.changed_byte_count == 0
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "source_sha256": self.source_sha256,
            "output_sha256": self.output_sha256,
            "byte_identical": self.byte_identical,
            "changes": [item.to_dict() for item in self.changes],
            "diff": self.diff.to_dict(),
            "section_hashes": self.section_hashes,
            "post_write_validated": self.output_model.diagnostics.validated,
            "original_warnings": list(self.original_model.diagnostics.warnings),
            "output_warnings": list(self.output_model.diagnostics.warnings),
        }


def _ranges(indices: Iterable[int]) -> tuple[ByteRange, ...]:
    ordered = sorted(set(int(value) for value in indices))
    if not ordered:
        return ()
    result: list[ByteRange] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value != previous + 1:
            result.append(ByteRange(start, previous + 1))
            start = value
        previous = value
    result.append(ByteRange(start, previous + 1))
    return tuple(result)


def audit_binary_diff(
    before: bytes,
    after: bytes,
    allowed_ranges: Iterable[tuple[int, int] | ByteRange],
) -> BinaryDiffAudit:
    if len(before) != len(after):
        raise DxWriteError(
            f"template size changed from {len(before)} to {len(after)} bytes"
        )
    allowed = tuple(
        item if isinstance(item, ByteRange) else ByteRange(int(item[0]), int(item[1]))
        for item in allowed_ranges
    )
    for item in allowed:
        if item.start < 0 or item.end < item.start or item.end > len(before):
            raise DxWriteError(f"invalid allowed byte range {item.start}:{item.end}")
    changed = [
        index
        for index, (left, right) in enumerate(zip(before, after))
        if left != right
    ]
    unexpected = [
        index
        for index in changed
        if not any(item.start <= index < item.end for item in allowed)
    ]
    return BinaryDiffAudit(
        changed_ranges=_ranges(changed),
        allowed_ranges=allowed,
        unexpected_ranges=_ranges(unexpected),
        changed_byte_count=len(changed),
    )


def _position_bounds(
    model: DxModel,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    values = model.vertices.positions
    return (
        tuple(min(value[axis] for value in values) for axis in range(3)),
        tuple(max(value[axis] for value in values) for axis in range(3)),
    )


def _validate_position(
    value: Sequence[float],
    index: int,
) -> tuple[float, float, float]:
    if len(value) != 3:
        raise DxWriteError(f"vertex {index}: expected XYZ, got {len(value)} values")
    result = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in result):
        raise DxWriteError(f"vertex {index}: position contains a non-finite value")
    try:
        struct.pack("<3f", *result)
    except (OverflowError, struct.error) as error:
        raise DxWriteError(
            f"vertex {index}: position cannot be represented as float32"
        ) from error
    return result


def _draw_signature(model: DxModel) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            draw.record_path,
            draw.tag,
            draw.offset,
            draw.size,
            draw.own_size,
            draw.core_offset,
            draw.group_label,
            draw.control_words,
            draw.declared_child_count,
            draw.vertex_base,
            draw.local_vertex_max,
            draw.index_start,
            draw.index_count,
            draw.unknown_0x14,
            draw.unknown_0x18,
            struct.pack("<f", draw.unknown_0x1c_float),
            draw.flags_0x20,
            draw.unknown_0x24,
            draw.terminal_offset,
            tuple(
                (
                    slot.slot,
                    slot.value,
                    slot.length_offset,
                    slot.data_offset,
                    slot.raw,
                )
                for slot in draw.texture_slots
            ),
        )
        for draw in model.physical_draws
    )


def _section_hashes(data: bytes, model: DxModel) -> dict[str, str]:
    ranges = {
        "header": (0, model.vertices.position_offset),
        "non_position_payload": (model.vertices.position_buffer_end, len(data)),
        "normals": (model.vertices.normal_offset, model.vertices.color_offset),
        "colors": (model.vertices.color_offset, model.uv_count_offset),
        "uv_and_local_indices": (model.uv_count_offset, model.draw_table_offset),
        "draw_and_global_tables": (model.draw_table_offset, model.trailing.offset),
        "trailing": (model.trailing.offset, len(data)),
        "collision": (model.collision.offset, model.collision.end_offset),
    }
    return {
        name: hashlib.sha256(data[start:end]).hexdigest()
        for name, (start, end) in ranges.items()
    }


def _validate_reparse(
    original: DxModel,
    output: DxModel,
    expected_positions: tuple[tuple[float, float, float], ...],
) -> None:
    failures: list[str] = []
    comparisons = (
        ("vertex count", original.vertex_count, output.vertex_count),
        ("local indices", original.local_indices, output.local_indices),
        ("draw structure", _draw_signature(original), _draw_signature(output)),
        (
            "draw groups",
            [(g.top_level_index, g.draw_indices) for g in original.draw_groups],
            [(g.top_level_index, g.draw_indices) for g in output.draw_groups],
        ),
        ("normals", original.vertices.normals, output.vertices.normals),
        ("colors", original.vertices.colors, output.vertices.colors),
        (
            "UV sets",
            [item.values for item in original.uv_sets],
            [item.values for item in output.uv_sets],
        ),
        (
            "global indices",
            original.global_index_table.indices if original.global_index_table else None,
            output.global_index_table.indices if output.global_index_table else None,
        ),
        ("trailing bytes", original.trailing.data, output.trailing.data),
        (
            "tag101 payload hash",
            original.collision.convex_hull.sha256 if original.collision.convex_hull else None,
            output.collision.convex_hull.sha256 if output.collision.convex_hull else None,
        ),
        ("warnings", original.diagnostics.warnings, output.diagnostics.warnings),
        ("errors", original.diagnostics.errors, output.diagnostics.errors),
    )
    for label, before, after in comparisons:
        if before != after:
            failures.append(label)
    if output.vertices.positions != expected_positions:
        failures.append("patched positions")
    if original.diagnostics.validated != output.diagnostics.validated:
        failures.append("validation status")
    if failures:
        raise DxWriteError(
            "post-write reparse changed forbidden structure: " + ", ".join(failures)
        )


def patch_dx_positions(
    template_bytes: bytes,
    positions: Iterable[Sequence[float]],
    *,
    source: str = "<template>",
    safe_bounds: bool = True,
) -> DxPositionPatchResult:
    original = parse_dx_bytes(template_bytes, source=source)
    candidates = tuple(
        _validate_position(value, index) for index, value in enumerate(positions)
    )
    if len(candidates) != original.vertex_count:
        raise DxWriteError(
            f"position count {len(candidates)} does not match template "
            f"vertex count {original.vertex_count}"
        )
    minimum, maximum = _position_bounds(original)
    if safe_bounds:
        for index, value in enumerate(candidates):
            if any(
                value[axis] < minimum[axis] or value[axis] > maximum[axis]
                for axis in range(3)
            ):
                raise DxWriteError(
                    f"vertex {index}: position {value!r} is outside original "
                    f"AABB {minimum!r}..{maximum!r}"
                )

    output = bytearray(template_bytes)
    changes: list[PositionChange] = []
    allowed: list[ByteRange] = []
    expected: list[tuple[float, float, float]] = []
    for index, (old, new) in enumerate(
        zip(original.vertices.positions, candidates)
    ):
        offset = (
            original.vertices.position_offset
            + index * original.vertices.position_stride
        )
        original_raw = template_bytes[
            offset:offset + original.vertices.position_stride
        ]
        encoded = struct.pack("<3f", *new)
        rounded = struct.unpack("<3f", encoded)
        expected.append(rounded)
        if encoded == original_raw:
            continue
        output[offset:offset + original.vertices.position_stride] = encoded
        changed_bytes = sum(
            left != right for left, right in zip(original_raw, encoded)
        )
        changes.append(
            PositionChange(
                vertex_index=index,
                old_position=old,
                new_position=rounded,
                delta=tuple(rounded[axis] - old[axis] for axis in range(3)),
                source_offset=offset,
                changed_byte_count=changed_bytes,
            )
        )
        allowed.append(
            ByteRange(offset, offset + original.vertices.position_stride)
        )

    result_bytes = bytes(output)
    diff = audit_binary_diff(template_bytes, result_bytes, allowed)
    if not diff.valid:
        raise DxWriteError(
            "writer changed bytes outside authorized position records"
        )
    output_model = parse_dx_bytes(
        result_bytes,
        source=f"{source} (patched)",
    )
    expected_tuple = tuple(expected)
    _validate_reparse(original, output_model, expected_tuple)
    before_hashes = _section_hashes(template_bytes, original)
    after_hashes = _section_hashes(result_bytes, output_model)
    mismatched = [
        name
        for name in before_hashes
        if before_hashes[name] != after_hashes[name]
    ]
    if mismatched:
        raise DxWriteError(
            "preserved section hash mismatch: " + ", ".join(mismatched)
        )
    return DxPositionPatchResult(
        data=result_bytes,
        source_sha256=hashlib.sha256(template_bytes).hexdigest(),
        output_sha256=hashlib.sha256(result_bytes).hexdigest(),
        changes=tuple(changes),
        diff=diff,
        original_model=original,
        output_model=output_model,
        section_hashes=before_hashes,
    )


def write_dx_positions(
    source_path: Path,
    output_path: Path,
    positions: Iterable[Sequence[float]],
    *,
    expected_source_sha256: str,
    safe_bounds: bool = True,
) -> DxPositionPatchResult:
    source_resolved = source_path.resolve()
    output_resolved = output_path.resolve()
    if source_resolved == output_resolved:
        raise DxWriteError("safe mode refuses to overwrite the source DX")
    template = source_resolved.read_bytes()
    actual_hash = hashlib.sha256(template).hexdigest()
    if actual_hash.casefold() != expected_source_sha256.casefold():
        raise DxWriteError(
            "source template SHA-256 mismatch: "
            f"expected {expected_source_sha256}, got {actual_hash}"
        )
    result = patch_dx_positions(
        template,
        positions,
        source=str(source_resolved),
        safe_bounds=safe_bounds,
    )
    output_resolved.parent.mkdir(parents=True, exist_ok=True)
    output_resolved.write_bytes(result.data)
    return result
