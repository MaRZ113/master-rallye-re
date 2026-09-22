"""Pure provenance checks shared by Blender import/export and tests."""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import Iterable, Sequence

from .coords import geometry_fingerprint

SOURCE_IDENTICAL = "SOURCE_IDENTICAL"
POSITIONS_ONLY_CHANGED = "POSITIONS_ONLY_CHANGED"
UNSUPPORTED_TOPOLOGY_CHANGED = "UNSUPPORTED_TOPOLOGY_CHANGED"
INVALID_PROVENANCE = "INVALID_PROVENANCE"


@dataclass(frozen=True)
class AuthoringValidation:
    status: str
    errors: tuple[str, ...]
    positions_by_source: tuple[tuple[float, float, float], ...]

    @property
    def exportable(self) -> bool:
        return self.status in {SOURCE_IDENTICAL, POSITIONS_ONLY_CHANGED}


def provenance_fingerprint(
    faces: Iterable[Sequence[int]],
    source_vertex_ids: Sequence[int],
    source_triangle_ids: Sequence[int],
    draw_ids: Sequence[int],
    group_ids: Sequence[int],
) -> str:
    records = []
    for face, triangle_id, draw_id, group_id in zip(
        faces, source_triangle_ids, draw_ids, group_ids
    ):
        records.append(
            (
                int(triangle_id),
                tuple(int(source_vertex_ids[int(index)]) for index in face),
                int(draw_id),
                int(group_id),
            )
        )
    records.sort(key=lambda item: item[0])
    digest = hashlib.sha256()
    digest.update(struct.pack("<I", len(records)))
    for triangle_id, vertices, draw_id, group_id in records:
        digest.update(
            struct.pack(
                "<6i",
                triangle_id,
                vertices[0],
                vertices[1],
                vertices[2],
                draw_id,
                group_id,
            )
        )
    return digest.hexdigest()


def validate_authoring_state(
    *,
    positions: Sequence[Sequence[float]],
    faces: Sequence[Sequence[int]],
    source_vertex_ids: Sequence[int],
    source_vertex_valid: Sequence[bool],
    source_triangle_ids: Sequence[int],
    draw_ids: Sequence[int],
    group_ids: Sequence[int],
    expected_vertex_count: int,
    expected_face_count: int,
    expected_geometry_fingerprint: str,
    expected_provenance_fingerprint: str,
) -> AuthoringValidation:
    errors: list[str] = []
    if len(positions) != expected_vertex_count:
        errors.append(
            f"vertex count {len(positions)} differs from source {expected_vertex_count}"
        )
    if len(faces) != expected_face_count:
        errors.append(
            f"face count {len(faces)} differs from source {expected_face_count}"
        )
    if len(source_vertex_ids) != len(positions):
        errors.append("source vertex ID attribute count mismatch")
    if len(source_vertex_valid) != len(positions):
        errors.append("source vertex validity attribute count mismatch")
    if len(source_vertex_valid) == len(positions) and not all(source_vertex_valid):
        errors.append("one or more source vertex identities are marked invalid")
    if len(source_vertex_ids) == expected_vertex_count:
        expected_ids = set(range(expected_vertex_count))
        actual_ids = set(int(value) for value in source_vertex_ids)
        if len(actual_ids) != len(source_vertex_ids):
            errors.append("duplicate source vertex IDs")
        if actual_ids != expected_ids:
            errors.append("source vertex IDs are missing or out of range")
    else:
        errors.append("source vertex ID attribute count mismatch")

    face_lengths = {
        len(source_triangle_ids),
        len(draw_ids),
        len(group_ids),
    }
    if face_lengths != {len(faces)}:
        errors.append("face provenance attribute count mismatch")
    if len(source_triangle_ids) == expected_face_count:
        expected_triangles = set(range(expected_face_count))
        actual_triangles = set(int(value) for value in source_triangle_ids)
        if len(actual_triangles) != len(source_triangle_ids):
            errors.append("duplicate source triangle IDs")
        if actual_triangles != expected_triangles:
            errors.append("source triangle IDs are missing or out of range")
    else:
        errors.append("source triangle attribute count mismatch")

    positions_by_source: list[tuple[float, float, float] | None] = [
        None
    ] * expected_vertex_count
    if (
        len(positions) == expected_vertex_count
        and len(source_vertex_ids) == expected_vertex_count
    ):
        for position, source_id in zip(positions, source_vertex_ids):
            source_index = int(source_id)
            if 0 <= source_index < expected_vertex_count:
                positions_by_source[source_index] = tuple(
                    float(component) for component in position
                )
    ordered_positions = tuple(
        value if value is not None else (0.0, 0.0, 0.0)
        for value in positions_by_source
    )
    topology_count_changed = (
        len(positions) != expected_vertex_count
        or len(faces) != expected_face_count
    )
    provenance_errors = any(
        "source vertex" in error
        or "source triangle" in error
        or "provenance attribute" in error
        for error in errors
    )
    if errors:
        status = (
            UNSUPPORTED_TOPOLOGY_CHANGED
            if topology_count_changed
            else INVALID_PROVENANCE
            if provenance_errors
            else UNSUPPORTED_TOPOLOGY_CHANGED
        )
        return AuthoringValidation(status, tuple(dict.fromkeys(errors)), ordered_positions)

    current_provenance = provenance_fingerprint(
        faces,
        source_vertex_ids,
        source_triangle_ids,
        draw_ids,
        group_ids,
    )
    if current_provenance != expected_provenance_fingerprint:
        return AuthoringValidation(
            UNSUPPORTED_TOPOLOGY_CHANGED,
            ("topology, source triangle mapping, or draw membership changed",),
            ordered_positions,
        )

    ordered_faces = [
        None
    ] * expected_face_count
    for face, triangle_id in zip(faces, source_triangle_ids):
        ordered_faces[int(triangle_id)] = tuple(
            int(source_vertex_ids[int(vertex_index)])
            for vertex_index in face
        )
    current_geometry = geometry_fingerprint(ordered_positions, ordered_faces)
    status = (
        SOURCE_IDENTICAL
        if current_geometry == expected_geometry_fingerprint
        else POSITIONS_ONLY_CHANGED
    )
    return AuthoringValidation(status, (), ordered_positions)
