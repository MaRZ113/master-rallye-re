"""Compact provenance metadata and authoring-status diagnostics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .library import (
    AuthoringValidation,
    BLENDER_PREVIEW_UV_POLICY,
    GLTF_PREVIEW_UV_POLICY,
    convention_metadata,
    geometry_fingerprint,
    provenance_fingerprint,
    validate_authoring_state,
)

IMPORTER_VERSION = "4.0.0"
FORMAT_STATUS = "R4B_VEHICLE_DX_COLLISION_READ"
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
    face_draws = []
    source_triangles = []
    face_groups = []
    for draw in model.physical_draws:
        for relative_index in range(draw.triangle_count):
            face_draws.append(draw.draw_index)
            source_triangles.append(draw.index_start // 3 + relative_index)
            face_groups.append(draw.top_level_index)
    source_vertex_ids = tuple(range(model.vertex_count))
    hull = model.collision.convex_hull
    collision_metadata = {
        "tags": list(model.collision.tag_ids),
        "validated": model.collision.validated,
        "warnings": list(model.collision.warnings),
        "errors": list(model.collision.errors),
        "tag101_present": hull is not None,
        "tag101": None if hull is None else {
            "tag_offset": hull.tag_offset,
            "payload_offset": hull.payload_offset,
            "end_offset": hull.end_offset,
            "payload_size": hull.payload_size,
            "sha256": hull.sha256,
            "base_center": list(hull.base_geometry.vertices[0]) if hull.base_geometry.vertex_count == 1 else None,
            "base_scalar": hull.base_scalar,
            "base_scalar_semantics": "bounding-radius-CONFIRMED_BY_CORPUS-for-27-nonempty-vehicle-hulls",
            "representation_a": {
                "vertex_count": hull.representation_a.geometry_a.vertex_count,
                "triangle_count": hull.representation_a.geometry_a.triangle_count,
                "edge_count": len(hull.representation_a.edges),
                "face_count": hull.representation_a.face_count,
            },
            "representation_b": {
                "vertex_count": hull.representation_b.geometry_a.vertex_count,
                "triangle_count": hull.representation_b.geometry_a.triangle_count,
                "edge_count": len(hull.representation_b.edges),
                "face_count": hull.representation_b.face_count,
            },
        },
    }
    return {
        "schema_version": 3,
        "phase": "R4B",
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
            "source_provenance_fingerprint": provenance_fingerprint(
                triangles,
                source_vertex_ids,
                source_triangles,
                face_draws,
                face_groups,
            ),
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
        "collision": collision_metadata,
        "round_trip": {
            "writer_available": True,
            "writer_mode": "template-preserving-positions-only",
            "same_topology_required": True,
            "source_template_sha256_required": True,
            "safe_bounds_required": True,
            "source_identity_is_provenance_only": True,
            "arbitrary_topology_edits_supported": False,
        },
    }


def apply_object_metadata(obj, metadata):
    geometry = metadata["geometry"]
    source = metadata["source"]
    obj["mr_source_path"] = source["path"]
    obj["mr_source_sha256"] = source["sha256"]
    obj["mr_source_byte_size"] = source["byte_size"]
    obj["mr_resource_name"] = source["name"]
    obj["mr_vertex_count"] = geometry["vertex_count"]
    obj["mr_triangle_count"] = geometry["triangle_count"]
    obj["mr_uv_set_count"] = geometry["uv_set_count"]
    obj["mr_draw_count"] = geometry["draw_count"]
    obj["mr_format_status"] = metadata["format_status"]
    obj["mr_importer_version"] = metadata["importer_version"]
    obj["mr_display_normal_strategy"] = metadata["normal_provenance"]["display_strategy"]
    obj["mr_source_geometry_fingerprint"] = geometry["source_fingerprint"]
    obj["mr_source_provenance_fingerprint"] = geometry[
        "source_provenance_fingerprint"
    ]
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


def _attribute_values(mesh, name, member):
    attribute = mesh.attributes.get(name)
    if attribute is None:
        return None
    return tuple(getattr(item, member) for item in attribute.data)


def authoring_validation(obj):
    if obj is None or obj.type != "MESH" or "mr_metadata_json" not in obj:
        return AuthoringValidation("INVALID_PROVENANCE", ("not an imported Master Rallye mesh",), ())
    mesh = obj.data
    attribute_names = set(mesh.attributes.keys())
    if not REQUIRED_POINT_ATTRIBUTES.issubset(attribute_names):
        missing = sorted(REQUIRED_POINT_ATTRIBUTES - attribute_names)
        return AuthoringValidation("INVALID_PROVENANCE", (f"missing point attributes: {missing}",), ())
    if not REQUIRED_FACE_ATTRIBUTES.issubset(attribute_names):
        missing = sorted(REQUIRED_FACE_ATTRIBUTES - attribute_names)
        return AuthoringValidation("INVALID_PROVENANCE", (f"missing face attributes: {missing}",), ())
    positions = tuple(tuple(float(value) for value in vertex.co) for vertex in mesh.vertices)
    faces = _mesh_triangles(mesh)
    return validate_authoring_state(
        positions=positions,
        faces=faces,
        source_vertex_ids=_attribute_values(mesh, "mr_source_vertex", "value"),
        source_vertex_valid=_attribute_values(mesh, "mr_source_vertex_valid", "value"),
        source_triangle_ids=_attribute_values(mesh, "mr_source_triangle", "value"),
        draw_ids=_attribute_values(mesh, "mr_draw_id", "value"),
        group_ids=_attribute_values(mesh, "mr_group_id", "value"),
        expected_vertex_count=int(obj.get("mr_vertex_count", -1)),
        expected_face_count=int(obj.get("mr_triangle_count", -1)),
        expected_geometry_fingerprint=str(obj.get("mr_source_geometry_fingerprint", "")),
        expected_provenance_fingerprint=str(obj.get("mr_source_provenance_fingerprint", "")),
    )


def authoring_status(obj):
    return authoring_validation(obj).status


def refresh_authoring_status(obj):
    status = authoring_status(obj)
    if obj is not None:
        obj["mr_authoring_status"] = status
    return status
