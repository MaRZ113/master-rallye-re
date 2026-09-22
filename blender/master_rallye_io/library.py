"""Resolve the canonical library in development or its build-time vendored copy."""
from __future__ import annotations

try:
    from master_rallye.assets import AssetResolver
    from master_rallye.coords import (
        BLENDER_PREVIEW_UV_POLICY,
        GLTF_PREVIEW_UV_POLICY,
        analyze_normals,
        convention_metadata,
        expand_corner_normals,
        float32_signed_bits,
        geometry_fingerprint,
        prepare_display_normals,
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
    from master_rallye.dx_writer import write_dx_positions
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
    from .vendor.master_rallye.coords import (
        BLENDER_PREVIEW_UV_POLICY,
        GLTF_PREVIEW_UV_POLICY,
        analyze_normals,
        convention_metadata,
        expand_corner_normals,
        float32_signed_bits,
        geometry_fingerprint,
        prepare_display_normals,
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
    from .vendor.master_rallye.dx_writer import write_dx_positions
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
