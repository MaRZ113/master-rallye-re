"""Fail-closed Blender bridge for template-preserving position export."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .blender_metadata import authoring_validation
from .library import transform_blender_positions_to_source, write_dx_positions


@dataclass(frozen=True)
class BlenderExportResult:
    output_path: Path
    status: str
    patch: object


def _object_transform_is_identity(obj) -> bool:
    identity = (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
    return all(
        abs(float(obj.matrix_basis[row][column]) - identity[row][column]) <= 1.0e-7
        for row in range(4)
        for column in range(4)
    )


def export_dx_positions(obj, output_path: Path) -> BlenderExportResult:
    validation = authoring_validation(obj)
    if not validation.exportable:
        details = "; ".join(validation.errors) or validation.status
        raise ValueError(f"positions-only export refused: {details}")
    if not _object_transform_is_identity(obj):
        raise ValueError(
            "positions-only export requires unapplied identity object transforms; "
            "edit mesh vertices in Edit Mode"
        )
    try:
        metadata = json.loads(obj["mr_metadata_json"])
        source = metadata["source"]
        source_path = Path(source["path"])
        expected_hash = source["sha256"]
        expected_size = int(source["byte_size"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("positions-only export requires valid source metadata") from error
    if not source_path.is_file():
        raise ValueError(f"source template is unavailable: {source_path}")
    if source_path.stat().st_size != expected_size:
        raise ValueError(
            f"source template byte size changed: expected {expected_size}, "
            f"got {source_path.stat().st_size}"
        )
    source_positions = transform_blender_positions_to_source(
        validation.positions_by_source
    )
    patch = write_dx_positions(
        source_path,
        Path(output_path),
        source_positions,
        expected_source_sha256=expected_hash,
        safe_bounds=True,
    )
    obj["mr_authoring_status"] = validation.status
    obj["mr_last_export_path"] = str(Path(output_path).resolve())
    obj["mr_last_export_changed_vertices"] = len(patch.changes)
    obj["mr_last_export_changed_bytes"] = patch.diff.changed_byte_count
    return BlenderExportResult(
        output_path=Path(output_path).resolve(),
        status=validation.status,
        patch=patch,
    )
