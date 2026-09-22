"""Compact provenance metadata and authoring-status diagnostics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .library import (
    BLENDER_PREVIEW_UV_POLICY,
    GLTF_PREVIEW_UV_POLICY,
    convention_metadata,
    geometry_fingerprint,
)

IMPORTER_VERSION = "2.0.1"
FORMAT_STATUS = "R1_VEHICLE_DX_HIGH"
REQUIRED_POINT_ATTRIBUTES = {
    "mr_source_vertex",
    "mr_source_vertex_valid",
    "mr_source_normal",
    "mr_source_normal_valid",
    "mr_source_normal_bits_x",
    "mr_source_normal_bits_y",
    "mr_source_normal_bits_z",
}
REQUIRED_FACE_ATTRIBUTES = {"mr_draw_id", "mr_source_triangle", "mr_group_id"}


def _draw_metadata(draw):
    return {
        "draw_id": draw.draw_index,
        "record_path": draw.record_path,
        "record_tag": draw.tag,
        "record_offset": draw.offset,
        "record_size": draw.size,
        "own_size": draw.own_size,
        "core_offset": draw.core_offset,
        "top_level_index": draw.top_level_index,
        "group_label": draw.group_label,
        "control_words": list(draw.control_words),
        "declared_child_count": draw.declared_child_count,
        "child_record_paths": [child.record_path for child in draw.children],
        "vertex_base": draw.vertex_base,
        "local_vertex_max": draw.local_vertex_max,
        "index_start": draw.index_start,
        "index_count": draw.index_count,
        "unknown_0x14": draw.unknown_0x14,
        "unknown_0x18": draw.unknown_0x18,
        "unknown_0x1c_float": draw.unknown_0x1c_float,
        "flags_0x20_hex": draw.flags_0x20.hex(),
        "unknown_0x24": draw.unknown_0x24,
        "texture_slots": [slot.value for slot in draw.texture_slots],
        "material_candidates": [
            {"number": item.number, "name": item.name}
            for item in draw.material_candidates
        ],
    }


def build_metadata(
    model,
    sidecar,
    source_path: Path,
    positions,
    triangles,
    *,
    normal_diagnostics,
    display_normal_strategy: str,
):
    positions = tuple(positions)
    return {
        "schema_version": 2,
        "phase": "R2",
        "importer_version": IMPORTER_VERSION,
        "format_status": FORMAT_STATUS,
        "source": {
            "path": str(source_path.resolve()),
            "name": source_path.name,
            "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "byte_size": model.byte_size,
        },
        "coordinate_convention": convention_metadata(),
        "texture_presentation": {
            "dxt_raw_rows": "preserved",
            "png_row_policy": "flip-vertical",
            "gltf_uv_policy": GLTF_PREVIEW_UV_POLICY,
            "blender_uv_policy": BLENDER_PREVIEW_UV_POLICY,
        },
        "normal_provenance": {
            "source_space": "dx-source-xyz",
            "float_vector_attribute": "mr_source_normal",
            "validity_attribute": "mr_source_normal_valid",
            "exact_float32_bit_attributes": [
                "mr_source_normal_bits_x",
                "mr_source_normal_bits_y",
                "mr_source_normal_bits_z",
            ],
            "diagnostics": normal_diagnostics.to_dict(),
            "display_strategy": display_normal_strategy,
            "display_strategy_reason": (
                "safe Blender 5.2.2 preview policy; native custom-normal APIs disabled"
            ),
            "custom_normal_api_applied": False,
            "per_corner_candidate_validated": (
                normal_diagnostics.count == model.vertex_count
                and normal_diagnostics.non_finite_count == 0
                and normal_diagnostics.near_zero_count == 0
            ),
            "display_candidate_normalized": (
                normal_diagnostics.count == model.vertex_count
                and normal_diagnostics.non_finite_count == 0
                and normal_diagnostics.near_zero_count == 0
            ),
            "display_candidate_applied": False,
        },
        "geometry": {
            "vertex_count": model.vertex_count,
            "triangle_count": len(triangles),
            "uv_set_count": len(model.uv_sets),
            "draw_count": len(model.physical_draws),
            "source_fingerprint": geometry_fingerprint(positions, triangles),
        },
        "validation": {
            "validated": model.diagnostics.validated,
            "global_indices_match": (
                model.global_index_table.reconstructed_match
                if model.global_index_table else False
            ),
            "warnings": list(model.diagnostics.warnings),
            "errors": list(model.diagnostics.errors),
        },
        "draws": [_draw_metadata(draw) for draw in model.physical_draws],
        "groups": [
            {
                "group_id": group.top_level_index,
                "root_record_path": group.root.record_path,
                "label": group.root.group_label,
                "draw_ids": list(group.draw_indices),
            }
            for group in model.draw_groups
        ],
        "sidecar": None if sidecar is None else {
            "source": sidecar.source,
            "declared_material_count": sidecar.declared_material_count,
            "materials": [
                {
                    "number": material.number,
                    "name": material.name,
                    "textures": [
                        {
                            "slot": texture.slot,
                            "source_tga": texture.source_tga,
                            "resource_stem": texture.resource_stem,
                            "has_alpha": texture.has_alpha,
                            "uses_alpha": texture.uses_alpha,
                            "is_noise": texture.is_noise,
                        }
                        for texture in material.textures
                    ],
                }
                for material in sidecar.materials
            ],
            "meshes": [
                {"name": mesh.name, "index": mesh.index, "size": mesh.size}
                for mesh in sidecar.meshes
            ],
        },
        "trailing": {
            "layout_family": model.trailing.layout_family,
            "byte_count": len(model.trailing.data),
            "sha256": model.trailing.sha256,
            "raw_embedded": False,
        },
        "round_trip": {
            "writer_available": False,
            "source_identity_is_provenance_only": True,
            "arbitrary_topology_edits_supported": False,
        },
    }


def apply_object_metadata(obj, metadata):
    geometry = metadata["geometry"]
    source = metadata["source"]
    obj["mr_source_path"] = source["path"]
    obj["mr_resource_name"] = source["name"]
    obj["mr_vertex_count"] = geometry["vertex_count"]
    obj["mr_triangle_count"] = geometry["triangle_count"]
    obj["mr_uv_set_count"] = geometry["uv_set_count"]
    obj["mr_draw_count"] = geometry["draw_count"]
    obj["mr_format_status"] = metadata["format_status"]
    obj["mr_importer_version"] = metadata["importer_version"]
    obj["mr_display_normal_strategy"] = metadata["normal_provenance"]["display_strategy"]
    obj["mr_source_geometry_fingerprint"] = geometry["source_fingerprint"]
    obj["mr_metadata_json"] = json.dumps(
        metadata,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    obj["mr_authoring_status"] = "SOURCE_IDENTICAL"


def _mesh_triangles(mesh):
    return tuple(
        tuple(int(value) for value in polygon.vertices)
        for polygon in mesh.polygons
    )


def current_geometry_fingerprint(mesh):
    positions = tuple(
        tuple(float(component) for component in vertex.co)
        for vertex in mesh.vertices
    )
    return geometry_fingerprint(positions, _mesh_triangles(mesh))


def authoring_status(obj):
    if obj is None or obj.type != "MESH" or "mr_metadata_json" not in obj:
        return "UNKNOWN"
    mesh = obj.data
    if len(mesh.vertices) != int(obj.get("mr_vertex_count", -1)):
        return "TOPOLOGY_CHANGED"
    if len(mesh.polygons) != int(obj.get("mr_triangle_count", -1)):
        return "TOPOLOGY_CHANGED"
    attribute_names = set(mesh.attributes.keys())
    if not REQUIRED_POINT_ATTRIBUTES.issubset(attribute_names):
        return "TOPOLOGY_CHANGED"
    if not REQUIRED_FACE_ATTRIBUTES.issubset(attribute_names):
        return "TOPOLOGY_CHANGED"
    expected = obj.get("mr_source_geometry_fingerprint", "")
    if not expected:
        return "UNKNOWN"
    return (
        "SOURCE_IDENTICAL"
        if current_geometry_fingerprint(mesh) == expected
        else "GEOMETRY_EDITED"
    )


def refresh_authoring_status(obj):
    status = authoring_status(obj)
    if obj is not None:
        obj["mr_authoring_status"] = status
    return status
