"""Deterministic Blender-corner to existing-draw MR vertex compilation."""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Mapping, Sequence

from .errors import DxWriteError
from .model import DxModel
from .topology_writer import CompiledVertex, DrawGeometry


@dataclass(frozen=True)
class CornerInput:
    blender_vertex_id: int
    position: tuple[float, float, float]
    normal: tuple[float, float, float]
    color: bytes
    uvs: tuple[tuple[float, float], ...]
    source_vertex_id: int | None = None
    parent_source_vertex_id: int | None = None


@dataclass(frozen=True)
class FaceInput:
    corners: tuple[CornerInput, ...]
    draw_id: int | None = None
    material_slot: int | None = None
    source_triangle_id: int | None = None
    assignment_explicit: bool = False


@dataclass(frozen=True)
class CompileReport:
    source_vertex_count: int
    compiled_vertex_count: int
    source_triangle_count: int
    compiled_triangle_count: int
    generated_for_new_geometry: int
    split_for_uv_seam: int
    split_for_normal_discontinuity: int
    split_for_vertex_color_discontinuity: int
    split_for_draw_boundary: int
    changed_draws: tuple[int, ...]
    inferred_face_draw_count: int

    def to_dict(self) -> dict:
        return {key: list(value) if isinstance(value, tuple) else value for key, value in vars(self).items()}


def _pack_finite(values: Sequence[float], size: int, label: str) -> bytes:
    if len(values) != size or not all(math.isfinite(float(value)) for value in values):
        raise DxWriteError(f"{label}: expected {size} finite float values")
    try:
        return struct.pack("<" + "f" * size, *values)
    except (OverflowError, struct.error) as error:
        raise DxWriteError(f"{label}: float32 overflow") from error


def _resolve_draw(face: FaceInput, draw_count: int, material_draws: Mapping[int, Sequence[int]]) -> tuple[int, bool]:
    if face.assignment_explicit or face.source_triangle_id is not None:
        if face.draw_id is None or not 0 <= face.draw_id < draw_count:
            raise DxWriteError(f"invalid existing draw assignment: {face.draw_id}")
        return face.draw_id, False
    matches = tuple(material_draws.get(face.material_slot, ())) if face.material_slot is not None else ()
    if len(matches) != 1:
        raise DxWriteError("new face has no unique existing MR draw; assign a draw explicitly")
    return matches[0], True


def compile_faces(
    model: DxModel,
    faces: Sequence[FaceInput],
    material_draws: Mapping[int, Sequence[int]],
) -> tuple[dict[int, DrawGeometry], CompileReport]:
    """Compile in sorted draw order, stable face order, stable corner order.

    First encountered variant of a source vertex keeps provenance. Extra point
    copies and corner variants retain only parent provenance, never a fake
    source ID. Generated vertices are never welded across Blender point IDs.
    """
    draws = model.physical_draws
    per_draw: dict[int, list[tuple[int, FaceInput]]] = {draw.draw_index: [] for draw in draws}
    inferred = 0
    seen_source_triangles: set[int] = set()
    source_point_owner: dict[int, int] = {}
    for face_index, face in enumerate(faces):
        if len(face.corners) != 3:
            raise DxWriteError(f"face {face_index}: triangulate quads/n-gons explicitly before export")
        draw_id, was_inferred = _resolve_draw(face, len(draws), material_draws)
        inferred += was_inferred
        for corner in face.corners:
            if corner.source_vertex_id is not None:
                owner = source_point_owner.setdefault(corner.source_vertex_id, corner.blender_vertex_id)
                if owner != corner.blender_vertex_id:
                    raise DxWriteError(
                        f"source vertex {corner.source_vertex_id} claimed by multiple Blender points; "
                        "assign the duplicated face so its copied point provenance is marked generated"
                    )
            if corner.parent_source_vertex_id is not None and not 0 <= corner.parent_source_vertex_id < model.vertex_count:
                raise DxWriteError("generated vertex has an invalid parent source ID")
        if face.source_triangle_id is not None:
            source_triangle = face.source_triangle_id
            draw = draws[draw_id]
            if not draw.index_start // 3 <= source_triangle < (draw.index_start + draw.index_count) // 3:
                raise DxWriteError(f"face {face_index}: source triangle belongs to another draw")
            if source_triangle in seen_source_triangles:
                raise DxWriteError(f"face {face_index}: duplicate source triangle ID; mark new face generated and assign draw")
            seen_source_triangles.add(source_triangle)
        per_draw[draw_id].append((face_index, face))
    compiled: dict[int, DrawGeometry] = {}
    counts = dict(generated=0, uv=0, normal=0, color=0, draw=0)
    blender_draws: dict[int, set[int]] = {}
    changed_draws = []
    for draw in draws:
        draw_id = draw.draw_index
        assigned = per_draw[draw_id]
        if not assigned:
            raise DxWriteError(f"draw {draw_id}: removing every triangle is unsupported")
        records: list[tuple[CompiledVertex, tuple, int, int, int]] = []
        key_to_index: dict[tuple, int] = {}
        face_indices = []
        first_variant: dict[int, tuple[bytes, bytes, bytes]] = {}
        provenance_used: set[int] = set()
        for face_index, face in assigned:
            triangle = []
            for corner_index, corner in enumerate(face.corners):
                if len(corner.color) != 4 or len(corner.uvs) != len(model.uv_sets):
                    raise DxWriteError(f"face {face_index}: incomplete vertex color or UV sets")
                position_key = _pack_finite(corner.position, 3, "position")
                source_id = corner.source_vertex_id
                source_normal = source_id is not None and 0 <= source_id < model.vertex_count and corner.normal == model.vertices.normals[source_id]
                normal_key = (
                    struct.pack("<3f", *corner.normal) if source_normal and all(math.isfinite(x) for x in corner.normal)
                    else _pack_finite(corner.normal, 3, "normal")
                )
                uv_key = b"".join(_pack_finite(uv, 2, "UV") for uv in corner.uvs)
                if source_id is not None and not draw.vertex_base <= source_id <= draw.vertex_base + draw.local_vertex_max:
                    raise DxWriteError(f"face {face_index}: source vertex ID belongs to another draw")
                key = (draw_id, corner.blender_vertex_id, position_key, normal_key, bytes(corner.color), uv_key)
                index = key_to_index.get(key)
                if index is None:
                    original_id = source_id if source_id is not None and source_id not in provenance_used else None
                    if original_id is not None:
                        provenance_used.add(original_id)
                    else:
                        counts["generated"] += corner.blender_vertex_id not in first_variant
                    vertex = CompiledVertex(
                        corner.position, corner.normal, bytes(corner.color), corner.uvs,
                        source_vertex_id=original_id,
                        parent_source_vertex_id=(source_id if source_id is not None else corner.parent_source_vertex_id)
                        if original_id is None else None,
                    )
                    previous = first_variant.get(corner.blender_vertex_id)
                    if previous is not None:
                        counts["uv"] += previous[2] != uv_key
                        counts["normal"] += previous[1] != normal_key
                        counts["color"] += previous[0] != corner.color
                    else:
                        first_variant[corner.blender_vertex_id] = (bytes(corner.color), normal_key, uv_key)
                    existing_draws = blender_draws.setdefault(corner.blender_vertex_id, set())
                    counts["draw"] += bool(existing_draws and draw_id not in existing_draws)
                    existing_draws.add(draw_id)
                    index = len(records)
                    key_to_index[key] = index
                    records.append((vertex, key, face_index, corner_index, corner.blender_vertex_id))
                triangle.append(index)
            face_indices.append(tuple(triangle))
        ordered = sorted(range(len(records)), key=lambda index: (
            records[index][0].source_vertex_id is None,
            records[index][0].source_vertex_id if records[index][0].source_vertex_id is not None else records[index][4],
            records[index][2], records[index][3],
        ))
        old_to_new = {old: new for new, old in enumerate(ordered)}
        vertices = tuple(records[index][0] for index in ordered)
        triangles = tuple(tuple(old_to_new[index] for index in triangle) for triangle in face_indices)
        compiled[draw_id] = DrawGeometry(vertices, triangles)
        source_indices = model.draw_global_indices(draw)
        original_triangles = tuple(
            tuple(source_indices[start + corner] - draw.vertex_base for corner in range(3))
            for start in range(0, len(source_indices), 3)
        )
        if len(vertices) != draw.local_vertex_max + 1 or triangles != original_triangles:
            changed_draws.append(draw_id)
    report = CompileReport(
        model.vertex_count, sum(len(item.vertices) for item in compiled.values()),
        model.triangle_count, sum(len(item.triangles) for item in compiled.values()),
        counts["generated"], counts["uv"], counts["normal"], counts["color"], counts["draw"],
        tuple(changed_draws), inferred,
    )
    return compiled, report
