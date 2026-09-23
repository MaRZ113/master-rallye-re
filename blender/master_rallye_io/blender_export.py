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


def export_dx_attributes(obj, output_path: Path) -> BlenderExportResult:
    """Export supported Blender attributes through the source-byte patcher."""
    import hashlib
    from .library import (
        aggregate_corners, parse_dx, transform_blender_positions_to_source,
        write_dx_attributes,
    )
    validation = authoring_validation(obj)
    if not validation.exportable:
        details = "; ".join(validation.errors) or validation.status
        raise ValueError(f"REQUIRES_R4F_TOPOLOGY_WRITER: {details}")
    if not _object_transform_is_identity(obj):
        raise ValueError("export requires identity object transform")
    metadata = json.loads(obj["mr_metadata_json"])
    source = metadata["source"]
    source_path = Path(source["path"])
    if not source_path.is_file() or source_path.stat().st_size != int(source["byte_size"]):
        raise ValueError("source DX template missing or byte size changed")
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError("source DX hash changed")
    original = parse_dx(source_path)
    mesh = obj.data
    ids = tuple(int(x.value) for x in mesh.attributes["mr_source_vertex"].data)
    loops = tuple(int(ids[loop.vertex_index]) for loop in mesh.loops)
    positions = transform_blender_positions_to_source(validation.positions_by_source)
    uv_sets = []
    if len(mesh.uv_layers) != len(original.uv_sets):
        raise ValueError("REQUIRES_R4F_TOPOLOGY_WRITER: UV layer count changed")
    for index, source_set in enumerate(original.uv_sets):
        layer = mesh.uv_layers.get(f"MR UV {index}")
        if layer is None:
            raise ValueError(f"source UV layer {index} missing")
        uv_sets.append(aggregate_corners(
            loops,
            tuple(tuple(float(x) for x in item.uv) for item in layer.data),
            source_set.values,
            field=f"UV{index}",
        ))
    normals_attr = mesh.attributes.get("mr_source_normal")
    if normals_attr is None or normals_attr.domain not in {"POINT", "CORNER"}:
        raise ValueError("source-normal edit attribute missing or wrong domain")
    if normals_attr.domain == "POINT":
        normals = [None] * original.vertex_count
        for mesh_index, source_id in enumerate(ids):
            normals[source_id] = tuple(float(x) for x in normals_attr.data[mesh_index].vector)
    else:
        normals = aggregate_corners(
            loops,
            tuple(tuple(float(x) for x in item.vector) for item in normals_attr.data),
            original.vertices.normals,
            field="normal",
        )
    for index, valid in enumerate(original.vertices.normals):
        if not all(__import__("math").isfinite(x) for x in valid):
            normals[index] = None
    color_attr = mesh.color_attributes.get("MR Vertex Color")
    if color_attr is None or color_attr.domain not in {"POINT", "CORNER"}:
        raise ValueError("MR Vertex Color attribute missing or wrong domain")
    source_raw = original.vertices.colors
    source_colors = tuple(tuple(source_raw[i*4:i*4+4]) for i in range(original.vertex_count))
    def raw_color(item, source_index):
        values = tuple(float(x) for x in (
            item.color_srgb if hasattr(item, "color_srgb") else item.color
        ))
        old = source_colors[source_index]
        if all(abs(value - channel/255.0) <= 1.0e-5 for value,channel in zip(values,old)):
            return old
        return tuple(max(0,min(255,round(value*255))) for value in values)
    if color_attr.domain == "POINT":
        colors = [None]*original.vertex_count
        for mesh_index, source_id in enumerate(ids):
            colors[source_id] = raw_color(color_attr.data[mesh_index],source_id)
    else:
        corner_colors = [
            raw_color(item,source_id)
            for item,source_id in zip(color_attr.data,loops)
        ]
        colors = aggregate_corners(loops,corner_colors,source_colors,field="color",tolerance=0)
    if any(item is None for item in colors):
        raise ValueError("source color identity missing")
    edits={}
    # The import stores source-space normal values. Their bit attributes preserve
    # original exact bytes when Blender leaves the vector unedited.
    for draw_id, enabled in json.loads(obj.get("mr_material_alpha_edits_json","{}")).items():
        edits[int(draw_id)]=bool(enabled)
    env={}
    for draw_id, enabled in json.loads(obj.get("mr_material_env_edits_json","{}")).items():
        env[int(draw_id)]=bool(enabled)
    patch=write_dx_attributes(
        source_path,Path(output_path),
        expected_source_sha256=source["sha256"],
        positions=positions,normals=normals,uv_sets=uv_sets,colors=colors,
        material_alpha=edits,material_env=env,
        safe_bounds=True,
    )
    obj["mr_authoring_status"]=patch.classification
    obj["mr_last_export_path"]=str(Path(output_path).resolve())
    obj["mr_last_export_changed_bytes"]=patch.diff.changed_byte_count
    return BlenderExportResult(Path(output_path).resolve(),patch.classification,patch)
