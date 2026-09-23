"""Experimental vehicle DX render-core rebuilder for existing draws only.

Triangles use the parser's stored-global winding. Wire local triangles swap
corners 0 and 1. Original material records and collision suffix are copied.
"""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from .dx import MAX_INDICES, MAX_VERTICES, parse_dx_bytes
from .bounds import compute_bounds1339, parse_bounds1339, replace_bounds1339
from .errors import DxWriteError
from .model import DxModel


@dataclass(frozen=True)
class CompiledVertex:
    position: tuple[float, float, float]
    normal: tuple[float, float, float]
    color: bytes
    uvs: tuple[tuple[float, float], ...]
    source_vertex_id: int | None = None
    parent_source_vertex_id: int | None = None


@dataclass(frozen=True)
class DrawGeometry:
    vertices: tuple[CompiledVertex, ...]
    triangles: tuple[tuple[int, int, int], ...]  # stored-global/display winding, draw-local IDs


@dataclass(frozen=True)
class TopologyRebuild:
    data: bytes
    source_sha256: str
    output_sha256: str
    source_vertex_count: int
    output_vertex_count: int
    source_triangle_count: int
    output_triangle_count: int
    source_core_end: int
    output_core_end: int
    changed_draws: tuple[int, ...]
    external_diff_count: int
    collision_sha256: str
    suffix_sha256: str
    byte_identical: bool
    semantic_equivalent: bool
    output_model: DxModel = field(repr=False)

    def to_dict(self) -> dict:
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in vars(self).items() if key not in {"data", "output_model"}
        }


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_vertex(model: DxModel, index: int) -> CompiledVertex:
    color = model.vertices.colors[index * 4:index * 4 + 4]
    return CompiledVertex(
        model.vertices.positions[index], model.vertices.normals[index], color,
        tuple(layer.values[index] for layer in model.uv_sets), source_vertex_id=index,
    )


def source_geometry(model: DxModel) -> dict[int, DrawGeometry]:
    """Represent original draw-local geometry without changing vertex identity."""
    result = {}
    for draw in model.physical_draws:
        base = draw.vertex_base
        vertices = tuple(_source_vertex(model, index) for index in range(base, base + draw.local_vertex_max + 1))
        globals_ = model.draw_global_indices(draw)
        triangles = tuple(
            tuple(globals_[start + corner] - base for corner in range(3))
            for start in range(0, len(globals_), 3)
        )
        result[draw.draw_index] = DrawGeometry(vertices, triangles)
    return result


def _same_number(left: float, right: float) -> bool:
    return left == right or (math.isnan(left) and math.isnan(right))


def _same_vector(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == len(right) and all(_same_number(a, b) for a, b in zip(left, right))


def _pack_vector(value: Sequence[float], size: int, label: str) -> bytes:
    if len(value) != size or not all(math.isfinite(float(component)) for component in value):
        raise DxWriteError(f"{label}: expected {size} finite float32 values")
    try:
        return struct.pack("<" + "f" * size, *value)
    except (OverflowError, struct.error) as error:
        raise DxWriteError(f"{label}: float32 overflow") from error


def _attribute_bytes(
    source: bytes, model: DxModel, vertex: CompiledVertex, draw_id: int,
    kind: str, uv_index: int | None = None,
) -> bytes:
    source_id = vertex.source_vertex_id
    if source_id is not None:
        if not 0 <= source_id < model.vertex_count:
            raise DxWriteError(f"draw {draw_id}: source vertex ID {source_id} outside source buffer")
        original = model.vertices.positions[source_id] if kind == "position" else (
            model.vertices.normals[source_id] if kind == "normal" else model.uv_sets[uv_index].values[source_id]
        )
        current = vertex.position if kind == "position" else vertex.normal if kind == "normal" else vertex.uvs[uv_index]
        if _same_vector(original, current):
            offset = (model.vertices.position_offset + source_id * 12 if kind == "position" else
                      model.vertices.normal_offset + source_id * 12 if kind == "normal" else
                      model.uv_sets[uv_index].offset + source_id * 8)
            return source[offset:offset + (8 if kind == "uv" else 12)]
    current = vertex.position if kind == "position" else vertex.normal if kind == "normal" else vertex.uvs[uv_index]
    return _pack_vector(current, 2 if kind == "uv" else 3, f"draw {draw_id} {kind}")


def _check_grammar(source: bytes, model: DxModel) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if not model.diagnostics.validated or model.global_index_table is None:
        raise DxWriteError("source DX is not fully validated with a stored global table")
    if model.magic != 0xD00D or (model.word_0x04, model.word_0x08) != (135, 1337):
        raise DxWriteError("unsupported vehicle DX header")
    draws = model.physical_draws
    if not draws or model.draw_table_preamble != 1:
        raise DxWriteError("unsupported draw table")
    # Some source files already disagree with the parser-derived root count.
    # The fixed draw set preserves the declared count byte-for-byte.
    if model.diagnostics.vertex_coverage != "complete-disjoint" or model.diagnostics.index_coverage != "complete-disjoint":
        raise DxWriteError("source draw ranges must cover disjoint contiguous render pools")
    if model.collision.bsp is not None or model.collision.errors and not all("non-finite" in e for e in model.collision.errors):
        raise DxWriteError("unsupported collision suffix grammar")
    if len(model.collision.unparsed_data) != 44 or struct.unpack_from("<I", model.collision.unparsed_data)[0] != 1339:
        raise DxWriteError("unrecognized vehicle bounds footer")
    minimum = struct.unpack_from("<3f", model.collision.unparsed_data, 20)
    maximum = struct.unpack_from("<3f", model.collision.unparsed_data, 32)
    center = struct.unpack_from("<3f", model.collision.unparsed_data, 4)
    for axis in range(3):
        if (not math.isfinite(minimum[axis]) or not math.isfinite(maximum[axis])
            or not minimum[axis] <= maximum[axis]
            or abs(center[axis] - (minimum[axis] + maximum[axis]) / 2) > 1e-5):
            raise DxWriteError("invalid original bounds footer")
    bounded_vertices = list(model.vertices.positions)
    hull = model.collision.convex_hull
    if hull is not None:
        bounded_vertices.extend(hull.base_geometry.vertices)
        for representation in (hull.representation_a, hull.representation_b):
            bounded_vertices.extend(representation.geometry_a.vertices)
            bounded_vertices.extend(representation.geometry_b.vertices)
    if any(
        math.isfinite(vertex[axis]) and not minimum[axis] - 1e-5 <= vertex[axis] <= maximum[axis] + 1e-5
        for vertex in bounded_vertices for axis in range(3)
    ):
        raise DxWriteError("original bounds footer does not cover source render/collision vertices")
    expected_vertex = expected_index = 0
    expected_record = model.draw_table_offset + 8
    for draw in draws:
        if draw.vertex_base != expected_vertex or draw.index_start != expected_index:
            raise DxWriteError(f"draw {draw.draw_index}: noncontiguous source ranges")
        if draw.offset != expected_record or draw.own_size <= 0:
            raise DxWriteError(f"draw {draw.draw_index}: noncontiguous record bytes")
        if draw.raw_index_min != 0 or draw.raw_index_max != draw.local_vertex_max:
            raise DxWriteError(f"draw {draw.draw_index}: local index coverage differs from observed corpus")
        expected_vertex += draw.local_vertex_max + 1
        expected_index += draw.index_count
        expected_record += draw.own_size
    if expected_vertex != model.vertex_count or expected_index != len(model.local_indices):
        raise DxWriteError("source draw spans do not cover render arrays")
    if expected_record != model.global_index_table.preamble_offset or model.global_index_table.preamble != 1:
        raise DxWriteError("global table does not immediately follow draw records")
    if model.global_index_table.data_offset + 4 * model.global_index_table.count != model.trailing.offset:
        raise DxWriteError("unrecognized bytes between global table and suffix")
    if model.collision.unparsed_offset + 44 != len(source):
        raise DxWriteError("unrecognized bytes after bounds footer")
    return minimum, maximum


def rebuild_topology(source: bytes, edits: Mapping[int, DrawGeometry] | None = None, *, bounds_mode: str = "preserve") -> TopologyRebuild:
    """Rebuild render arrays/indices for the fixed source draw set; never save a file."""
    if bounds_mode not in {"preserve", "recompute"}:
        raise DxWriteError("bounds_mode must be preserve or recompute")
    model = parse_dx_bytes(source)
    minimum, maximum = _check_grammar(source, model)
    originals = source_geometry(model)
    edits = dict(edits or {})
    if set(edits) - set(originals):
        raise DxWriteError(f"unknown draw IDs: {sorted(set(edits) - set(originals))}")
    geometry = {**originals, **edits}
    uv_count = len(model.uv_sets)
    positions = bytearray()
    normals = bytearray()
    colors = bytearray()
    uv_arrays = [bytearray() for _ in range(uv_count)]
    local = []
    global_indices = []
    new_spans = []
    changed_draws = []
    vertex_base = index_start = 0
    for draw in model.physical_draws:
        candidate = geometry[draw.draw_index]
        if not candidate.vertices or not candidate.triangles:
            raise DxWriteError(f"draw {draw.draw_index}: empty draw is not representable")
        if len(candidate.vertices) > 65536:
            raise DxWriteError(f"draw {draw.draw_index}: uint16 local-index capacity exceeded")
        if len(candidate.triangles) > MAX_INDICES // 3:
            raise DxWriteError(f"draw {draw.draw_index}: triangle count exceeds parser limit")
        for vertex in candidate.vertices:
            if len(vertex.position) != 3 or len(vertex.normal) != 3 or len(vertex.color) != 4 or len(vertex.uvs) != uv_count:
                raise DxWriteError(f"draw {draw.draw_index}: incomplete compiled vertex")
            if vertex.source_vertex_id is None and math.sqrt(sum(float(value)**2 for value in vertex.normal)) <= 1e-8:
                raise DxWriteError(f"draw {draw.draw_index}: generated vertex has no valid normal")
            if vertex.source_vertex_id is not None and not draw.vertex_base <= vertex.source_vertex_id <= draw.vertex_base + draw.local_vertex_max:
                raise DxWriteError(f"draw {draw.draw_index}: source provenance belongs to another draw")
            for axis, component in enumerate(vertex.position):
                if not math.isfinite(component) or abs(component) > 10000:
                    raise DxWriteError(f"draw {draw.draw_index}: vertex position outside sane finite range")
                if bounds_mode == "preserve" and not minimum[axis] - 1e-6 <= component <= maximum[axis] + 1e-6:
                    raise DxWriteError(f"draw {draw.draw_index}: vertex position outside original bounds")
            positions += _attribute_bytes(source, model, vertex, draw.draw_index, "position")
            normals += _attribute_bytes(source, model, vertex, draw.draw_index, "normal")
            colors += bytes(vertex.color)
            for uv_index in range(uv_count):
                uv_arrays[uv_index] += _attribute_bytes(source, model, vertex, draw.draw_index, "uv", uv_index)
        referenced_vertices: set[int] = set()
        for triangle in candidate.triangles:
            if len(triangle) != 3 or any(type(v) is not int or not 0 <= v < len(candidate.vertices) for v in triangle):
                raise DxWriteError(f"draw {draw.draw_index}: invalid local triangle {triangle!r}")
            a, b, c = triangle
            referenced_vertices.update(triangle)
            local.extend((b, a, c))
            global_indices.extend((a + vertex_base, b + vertex_base, c + vertex_base))
        if len(referenced_vertices) != len(candidate.vertices):
            raise DxWriteError(f"draw {draw.draw_index}: unreferenced compiled vertices are unsupported")
        index_count = len(candidate.triangles) * 3
        new_spans.append((vertex_base, len(candidate.vertices) - 1, index_start, index_count))
        if candidate != originals[draw.draw_index]:
            changed_draws.append(draw.draw_index)
        vertex_base += len(candidate.vertices)
        index_start += index_count
        if vertex_base > min(MAX_VERTICES, 0xFFFFFFFF) or index_start > min(MAX_INDICES, 0xFFFFFFFF):
            raise DxWriteError("top-level render count capacity exceeded")
    prefix = source[:12]
    header_count = struct.pack("<I", vertex_base)
    uv_count_bytes = source[model.uv_count_offset:model.uv_count_offset + 4]
    array_region = (
        header_count + positions + normals + colors + uv_count_bytes
        + b"".join(uv_arrays) + struct.pack("<I", index_start)
        + struct.pack(f"<{len(local)}H", *local)
    )
    table = bytearray(source[model.draw_table_offset:model.global_index_table.preamble_offset])
    for draw, (base, local_max, start, count) in zip(model.physical_draws, new_spans):
        for relative, value in zip((4, 8, 12, 16), (base, local_max, start, count)):
            struct.pack_into("<I", table, draw.core_offset - model.draw_table_offset + relative, value)
    global_region = (
        source[model.global_index_table.preamble_offset:model.global_index_table.preamble_offset + 4]
        + struct.pack("<I", len(global_indices))
        + struct.pack(f"<{len(global_indices)}I", *global_indices)
    )
    suffix = source[model.trailing.offset:]
    output = prefix + array_region + table + global_region + suffix
    parsed = parse_dx_bytes(output)
    if bounds_mode == "recompute" and output != source:
        source_bounds = parse_bounds1339(model.collision.unparsed_data, model.collision.unparsed_offset)
        if source_bounds is None:
            raise DxWriteError("unrecognized source spatial bounds")
        new_bounds = compute_bounds1339(parsed.vertices.positions, parsed.collision.convex_hull,
                                        offset=parsed.collision.unparsed_offset)
        output = replace_bounds1339(output, new_bounds, footer_offset=parsed.collision.unparsed_offset)
        parsed = parse_dx_bytes(output)
    if not parsed.diagnostics.validated or parsed.diagnostics.warnings != model.diagnostics.warnings:
        raise DxWriteError(f"rebuilt DX failed validation: {parsed.diagnostics.errors}; {parsed.diagnostics.warnings}")
    if parsed.vertex_count != vertex_base or parsed.local_indices != tuple(local) or parsed.global_index_table.indices != tuple(global_indices):
        raise DxWriteError("rebuilt render counts or indices differ from compilation")
    if len(parsed.physical_draws) != len(model.physical_draws):
        raise DxWriteError("draw count changed")
    for old, new, span in zip(model.physical_draws, parsed.physical_draws, new_spans):
        if (new.vertex_base, new.local_vertex_max, new.index_start, new.index_count) != span:
            raise DxWriteError(f"draw {old.draw_index}: rebuilt range differs")
        if (old.tag, old.group_label, old.control_words, old.texture_tuple,
            old.unknown_0x14, old.unknown_0x18, old.flags_0x20, old.unknown_0x24) != (
            new.tag, new.group_label, new.control_words, new.texture_tuple,
            new.unknown_0x14, new.unknown_0x18, new.flags_0x20, new.unknown_0x24):
            raise DxWriteError(f"draw {old.draw_index}: material or hierarchy metadata changed")
        raw_old = bytearray(source[old.offset:old.offset + old.own_size])
        raw_new = bytearray(output[new.offset:new.offset + new.own_size])
        for relative in (4, 8, 12, 16):
            start = old.core_offset - old.offset + relative
            raw_old[start:start + 4] = b"\x00" * 4
            start = new.core_offset - new.offset + relative
            raw_new[start:start + 4] = b"\x00" * 4
        if raw_old != raw_new:
            raise DxWriteError(f"draw {old.draw_index}: unexpected record bytes changed")
    if output[:12] != prefix:
        raise DxWriteError("external prefix changed")
    if bounds_mode == "preserve" or output == source:
        if output[parsed.trailing.offset:] != suffix:
            raise DxWriteError("external suffix changed")
    elif output[parsed.trailing.offset:parsed.collision.unparsed_offset] != source[model.trailing.offset:model.collision.unparsed_offset]:
        raise DxWriteError("collision or pre-bounds suffix changed")
    if model.collision.convex_hull is not None:
        before = model.collision.convex_hull.raw
        after = parsed.collision.convex_hull.raw if parsed.collision.convex_hull else None
        if before != after:
            raise DxWriteError("tag-101 collision bytes changed")
    if parsed.collision.tag_ids != model.collision.tag_ids:
        raise DxWriteError("collision tag structure changed")
    if bounds_mode == "preserve" and parsed.collision.unparsed_data != model.collision.unparsed_data:
        raise DxWriteError("bounds footer changed unexpectedly")
    if bounds_mode == "recompute" and parsed.collision.spatial_bounds_1339 is None:
        raise DxWriteError("rebuilt spatial bounds failed reparse")
    semantic_equivalent = (
        parsed.vertex_count == model.vertex_count
        and parsed.vertices.positions == model.vertices.positions
        and all(_same_vector(a, b) for a, b in zip(parsed.vertices.normals, model.vertices.normals))
        and parsed.vertices.colors == model.vertices.colors
        and [item.values for item in parsed.uv_sets] == [item.values for item in model.uv_sets]
        and parsed.local_indices == model.local_indices
        and parsed.global_index_table.indices == model.global_index_table.indices
        and all((a.vertex_base, a.local_vertex_max, a.index_start, a.index_count) ==
                (b.vertex_base, b.local_vertex_max, b.index_start, b.index_count)
                for a, b in zip(parsed.physical_draws, model.physical_draws))
    )
    return TopologyRebuild(
        output, _sha(source), _sha(output), model.vertex_count, parsed.vertex_count,
        model.triangle_count, parsed.triangle_count, model.trailing.offset, parsed.trailing.offset,
        tuple(changed_draws), 0, _sha(source[model.collision.offset:model.collision.end_offset]),
        _sha(output[parsed.trailing.offset:]), output == source, semantic_equivalent, parsed,
    )


def write_topology(source_path: Path, output_path: Path, edits: Mapping[int, DrawGeometry], *, expected_source_sha256: str) -> TopologyRebuild:
    source_path = Path(source_path).resolve()
    output_path = Path(output_path).resolve()
    if source_path == output_path:
        raise DxWriteError("output must differ from source")
    source = source_path.read_bytes()
    if _sha(source) != expected_source_sha256:
        raise DxWriteError("source DX SHA-256 mismatch")
    result = rebuild_topology(source, edits)
    if output_path.exists():
        raise DxWriteError("output already exists; choose a fresh candidate path")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.data)
    return result
