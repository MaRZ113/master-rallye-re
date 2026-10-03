"""Resolve the canonical library in development or its build-time vendored copy."""
from __future__ import annotations

try:
    from master_rallye.assets import AssetResolver
    from master_rallye.material_semantics import MaterialSemantics
    from master_rallye.coords import (
        BLENDER_PREVIEW_UV_POLICY,
        GLTF_PREVIEW_UV_POLICY,
        analyze_normals,
        convention_metadata,
        expand_corner_normals,
        float32_signed_bits,
        geometry_fingerprint,
        prepare_display_normals,
        position_to_blender,
        blender_position_to_source,
        transform_blender_normals,
        transform_blender_positions,
        transform_blender_positions_to_source,
        transform_normals,
        transform_positions,
        transform_uv_values,
        triangles_from_indices,
    )
    from master_rallye.authoring import (
        AuthoringValidation,
        INVALID_PROVENANCE,
        POSITIONS_ONLY_CHANGED,
        SOURCE_IDENTICAL,
        UNSUPPORTED_TOPOLOGY_CHANGED,
        provenance_fingerprint,
        validate_authoring_state,
    )
    from master_rallye.dx import parse_dx
    from master_rallye.dx_course import parse_course_dx
    from master_rallye.course_sdk import (
        build_course_race_logic,
        discover_course_resources,
        load_course_project,
    )
    from master_rallye.course_race_authoring import load_course_race_logic_authoring
    from master_rallye.course_gxm import parse_course_gxm_model_v7
    from master_rallye.course_source import parse_course_txt
    from master_rallye.course_xml import parse_course_xml
    from master_rallye.course_metadata import mark_course_metadata
    from master_rallye.dx_writer import write_dx_positions
    from master_rallye.r4e_writer import aggregate_corners, classify_edit, write_dx_attributes
    from master_rallye.texture_authoring import decode_rgba_png, replace_texture
    from master_rallye.vehicle_packaging import texture_users
    from master_rallye.dxt import (
        PNG_ROWS_FLIP_VERTICAL,
        has_transparency,
        parse_dxt,
        write_png,
    )
    from master_rallye.sidecar import (
        apply_material_candidates,
        normalize_texture_value,
        parse_sidecar,
        resolve_sidecar,
    )
except ModuleNotFoundError:
    from .vendor.master_rallye.assets import AssetResolver
    from .vendor.master_rallye.material_semantics import MaterialSemantics
    from .vendor.master_rallye.coords import (
        BLENDER_PREVIEW_UV_POLICY,
        GLTF_PREVIEW_UV_POLICY,
        analyze_normals,
        convention_metadata,
        expand_corner_normals,
        float32_signed_bits,
        geometry_fingerprint,
        prepare_display_normals,
        position_to_blender,
        blender_position_to_source,
        transform_blender_normals,
        transform_blender_positions,
        transform_blender_positions_to_source,
        transform_normals,
        transform_positions,
        transform_uv_values,
        triangles_from_indices,
    )
    from .vendor.master_rallye.authoring import (
        AuthoringValidation,
        INVALID_PROVENANCE,
        POSITIONS_ONLY_CHANGED,
        SOURCE_IDENTICAL,
        UNSUPPORTED_TOPOLOGY_CHANGED,
        provenance_fingerprint,
        validate_authoring_state,
    )
    from .vendor.master_rallye.dx import parse_dx
    from .vendor.master_rallye.dx_course import parse_course_dx
    from .vendor.master_rallye.course_sdk import (
        build_course_race_logic,
        discover_course_resources,
        load_course_project,
    )
    from .vendor.master_rallye.course_race_authoring import load_course_race_logic_authoring
    from .vendor.master_rallye.course_gxm import parse_course_gxm_model_v7
    from .vendor.master_rallye.course_source import parse_course_txt
    from .vendor.master_rallye.course_xml import parse_course_xml
    from .vendor.master_rallye.course_metadata import mark_course_metadata
    from .vendor.master_rallye.dx_writer import write_dx_positions
    from .vendor.master_rallye.r4e_writer import aggregate_corners, classify_edit, write_dx_attributes
    from .vendor.master_rallye.texture_authoring import decode_rgba_png, replace_texture
    from .vendor.master_rallye.vehicle_packaging import texture_users
    from .vendor.master_rallye.dxt import (
        PNG_ROWS_FLIP_VERTICAL,
        has_transparency,
        parse_dxt,
        write_png,
    )
    from .vendor.master_rallye.sidecar import (
        apply_material_candidates,
        normalize_texture_value,
        parse_sidecar,
        resolve_sidecar,
    )
