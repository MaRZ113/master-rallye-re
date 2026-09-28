"""Evidence-oriented data model for Master Rallye vehicle assets."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .collision import CollisionSections


@dataclass(frozen=True)
class TextureSlot:
    slot: int
    value: str
    length_offset: int
    data_offset: int
    raw: bytes


@dataclass(frozen=True)
class MaterialCandidate:
    number: int
    name: str


@dataclass
class DrawRecord:
    record_path: str
    tag: int
    offset: int
    size: int
    own_size: int
    core_offset: int
    group_label: str | None
    control_words: tuple[int, ...]
    declared_child_count: int
    vertex_base: int
    local_vertex_max: int
    index_start: int
    index_count: int
    unknown_0x14: int | None
    unknown_0x18: int | None
    unknown_0x1c_float: float | None
    flags_0x20: bytes
    unknown_0x24: int | None
    texture_slots: list[TextureSlot]
    terminal_offset: int
    children: list["DrawRecord"] = field(default_factory=list)
    material_candidates: list[MaterialCandidate] = field(default_factory=list)
    draw_index: int | None = None
    top_level_index: int | None = None
    raw_index_min: int | None = None
    raw_index_max: int | None = None
    global_vertex_min: int | None = None
    global_vertex_max: int | None = None
    opaque_prefix: bytes | None = None
    raw_revision_prefix: bytes | None = None
    material_semantics: str = "REV135_CONFIRMED"

    @property
    def triangle_count(self) -> int:
        return self.index_count // 3

    @property
    def texture_tuple(self) -> tuple[str, ...]:
        return tuple(slot.value for slot in self.texture_slots)

    @property
    def vertex_range(self) -> tuple[int, int]:
        return self.vertex_base, self.vertex_base + self.local_vertex_max

    def flattened(self) -> list["DrawRecord"]:
        result = [self]
        for child in self.children:
            result.extend(child.flattened())
        return result


@dataclass
class DrawGroup:
    top_level_index: int
    root: DrawRecord
    draw_indices: list[int]


@dataclass(frozen=True)
class UVSet:
    offset: int
    values: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class VertexData:
    position_offset: int
    normal_offset: int
    color_offset: int
    positions: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    colors: bytes

    @property
    def position_stride(self) -> int:
        return 12

    @property
    def position_buffer_size(self) -> int:
        return len(self.positions) * self.position_stride

    @property
    def position_buffer_end(self) -> int:
        return self.position_offset + self.position_buffer_size


@dataclass(frozen=True)
class GlobalIndexTable:
    preamble_offset: int
    preamble: int
    count: int
    data_offset: int
    indices: tuple[int, ...]
    reconstructed_match: bool
    compared_index_count: int


@dataclass(frozen=True)
class BoundingData:
    unknown_0x00_u32: int
    unknown_0x04_float: float
    unknown_0x08_float: float
    unknown_0x0c_u32: int
    midpoint: tuple[float, float, float]
    unknown_0x1c_float: float
    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]
    matches_positions: bool


@dataclass(frozen=True)
class TrailingSection:
    offset: int
    data: bytes
    layout_family: str
    sha256: str
    bounding: BoundingData | None = None


@dataclass
class ValidationDiagnostics:
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    index_coverage: str = "unknown"
    vertex_coverage: str = "unknown"
    uncovered_index_count: int = 0
    overlapping_index_count: int = 0
    unused_vertex_count: int = 0
    shared_vertex_count: int = 0
    reconstructed_global_match: bool = False
    index_sequence_equal: bool = False
    oriented_triangle_sets_equal_per_draw: bool = False
    mismatch_position_count: int = 0
    first_mismatch_position: int | None = None
    compared_index_count: int = 0
    per_draw_topology_equal: list[bool] = field(default_factory=list)
    import_validated: bool = False
    validation_profile: str = "INVALID"
    writer_revision_supported: bool = True

    @property
    def exact_generated_valid(self) -> bool:
        """True only when import structure, exact order, and writer revision all pass."""
        return (
            self.import_validated
            and self.index_sequence_equal
            and self.writer_revision_supported
        )

    @property
    def validated(self) -> bool:
        # Compatibility alias retained for writers and existing callers. This
        # remains the strict generated/exact profile, never the broader import
        # profile.
        return self.exact_generated_valid


@dataclass
class DxModel:
    source: str
    source_path: Path | None
    byte_size: int
    magic: int
    word_0x04: int
    word_0x08: int
    vertices: VertexData
    uv_count_offset: int
    uv_sets: list[UVSet]
    local_index_count_offset: int
    local_index_offset: int
    local_indices: tuple[int, ...]
    draw_table_offset: int
    draw_table_preamble: int
    declared_top_level_record_count: int
    draw_groups: list[DrawGroup]
    global_index_table: GlobalIndexTable | None
    collision: CollisionSections
    trailing: TrailingSection
    diagnostics: ValidationDiagnostics

    @property
    def vertex_count(self) -> int:
        return len(self.vertices.positions)

    @property
    def dx_revision(self) -> int:
        return self.word_0x04

    @property
    def triangle_count(self) -> int:
        return len(self.local_indices) // 3

    @property
    def physical_draws(self) -> list[DrawRecord]:
        result: list[DrawRecord] = []
        for group in self.draw_groups:
            result.extend(group.root.flattened())
        return result

    @property
    def record_tags(self) -> list[int]:
        return sorted({draw.tag for draw in self.physical_draws})

    @property
    def group_labels(self) -> list[str]:
        return [draw.group_label for draw in self.physical_draws if draw.group_label]

    def draw_global_indices(self, draw: DrawRecord) -> tuple[int, ...]:
        local = self.local_indices[draw.index_start:draw.index_start + draw.index_count]
        values: list[int] = []
        for index in range(0, len(local), 3):
            if index + 2 >= len(local):
                break
            values.extend((
                local[index + 1] + draw.vertex_base,
                local[index] + draw.vertex_base,
                local[index + 2] + draw.vertex_base,
            ))
        return tuple(values)

    def to_summary(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "byte_size": self.byte_size,
            "dx_revision": self.dx_revision,
            "vertex_count": self.vertex_count,
            "uv_set_count": len(self.uv_sets),
            "local_index_count": len(self.local_indices),
            "triangle_count": self.triangle_count,
            "declared_top_level_record_count": self.declared_top_level_record_count,
            "physical_draw_count": len(self.physical_draws),
            "record_tags": self.record_tags,
            "group_labels": self.group_labels,
            "stored_global_indices": self.global_index_table is not None,
            "global_indices_match": self.global_index_table.reconstructed_match if self.global_index_table else False,
            "collision": {
                "tag_ids": list(self.collision.tag_ids),
                "parsed_end_offset": self.collision.end_offset,
                "unparsed_offset": self.collision.unparsed_offset,
                "unparsed_byte_count": len(self.collision.unparsed_data),
                "validated": self.collision.validated,
                "warnings": list(self.collision.warnings),
                "errors": list(self.collision.errors),
                "tag101": ({
                    "tag_offset": self.collision.convex_hull.tag_offset,
                    "payload_offset": self.collision.convex_hull.payload_offset,
                    "end_offset": self.collision.convex_hull.end_offset,
                    "payload_size": self.collision.convex_hull.payload_size,
                    "sha256": self.collision.convex_hull.sha256,
                } if self.collision.convex_hull else None),
            },
            "diagnostics": {
                "validated": self.diagnostics.validated,
                "exact_generated_valid": self.diagnostics.exact_generated_valid,
                "structural_import_valid": self.diagnostics.import_validated,
                "writer_revision_supported": self.diagnostics.writer_revision_supported,
                "validation_profile": self.diagnostics.validation_profile,
                "index_sequence_equal": self.diagnostics.index_sequence_equal,
                "oriented_triangle_sets_equal_per_draw": self.diagnostics.oriented_triangle_sets_equal_per_draw,
                "mismatch_position_count": self.diagnostics.mismatch_position_count,
                "first_mismatch_position": self.diagnostics.first_mismatch_position,
                "compared_index_count": self.diagnostics.compared_index_count,
                "index_coverage": self.diagnostics.index_coverage,
                "vertex_coverage": self.diagnostics.vertex_coverage,
                "uncovered_index_count": self.diagnostics.uncovered_index_count,
                "overlapping_index_count": self.diagnostics.overlapping_index_count,
                "unused_vertex_count": self.diagnostics.unused_vertex_count,
                "shared_vertex_count": self.diagnostics.shared_vertex_count,
                "warnings": self.diagnostics.warnings,
                "errors": self.diagnostics.errors,
            },
            "trailing": {
                "offset": self.trailing.offset,
                "byte_count": len(self.trailing.data),
                "layout_family": self.trailing.layout_family,
                "sha256": self.trailing.sha256,
                "recognized_bounding": self.trailing.bounding is not None,
            },
        }
