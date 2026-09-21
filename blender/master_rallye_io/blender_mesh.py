"""Create one editable Blender mesh object for one parsed vehicle DX resource."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import bpy

from .library import (
    BLENDER_PREVIEW_UV_POLICY,
    apply_material_candidates,
    expand_corner_normals,
    float32_signed_bits,
    parse_dx,
    parse_sidecar,
    prepare_display_normals,
    transform_blender_normals,
    transform_blender_positions,
    transform_uv_values,
    triangles_from_indices,
)

from .blender_materials import PreviewMaterialCache
from .blender_metadata import apply_object_metadata, build_metadata


@dataclass
class BlenderImportResult:
    object: object
    model: object
    sidecar: object | None
    warnings: tuple[str, ...]


def create_collection(name: str, parent=None):
    collection = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(collection)
    else:
        parent.children.link(collection)
    return collection


def _integer_attribute(mesh, name: str, domain: str, values):
    attribute = mesh.attributes.new(name=name, type="INT", domain=domain)
    for item, value in zip(attribute.data, values):
        item.value = int(value)
    return attribute


def _boolean_attribute(mesh, name: str, domain: str, values):
    attribute = mesh.attributes.new(name=name, type="BOOLEAN", domain=domain)
    for item, value in zip(attribute.data, values):
        item.value = bool(value)
    return attribute


def _vector_attribute(mesh, name: str, domain: str, values):
    attribute = mesh.attributes.new(name=name, type="FLOAT_VECTOR", domain=domain)
    for item, value in zip(attribute.data, values):
        item.vector = tuple(float(component) for component in value)
    return attribute


def _normal_is_finite(value) -> bool:
    return len(value) == 3 and all(math.isfinite(float(component)) for component in value)


def _apply_source_attributes(
    mesh,
    face_draws,
    source_triangles,
    face_groups,
    raw_colors,
    source_normals,
):
    vertex_count = len(mesh.vertices)
    _integer_attribute(mesh, "mr_source_vertex", "POINT", range(vertex_count))
    _boolean_attribute(
        mesh,
        "mr_source_vertex_valid",
        "POINT",
        (True for _ in range(vertex_count)),
    )
    _integer_attribute(mesh, "mr_draw_id", "FACE", face_draws)
    _integer_attribute(mesh, "mr_source_triangle", "FACE", source_triangles)
    _integer_attribute(mesh, "mr_group_id", "FACE", face_groups)
    for channel in range(4):
        _integer_attribute(
            mesh,
            f"mr_color_byte_{channel}",
            "POINT",
            (raw_colors[index * 4 + channel] for index in range(vertex_count)),
        )

    normal_valid = tuple(_normal_is_finite(value) for value in source_normals)
    _vector_attribute(
        mesh,
        "mr_source_normal",
        "POINT",
        (
            value if valid else (0.0, 0.0, 0.0)
            for value, valid in zip(source_normals, normal_valid)
        ),
    )
    _boolean_attribute(mesh, "mr_source_normal_valid", "POINT", normal_valid)
    for component, label in enumerate(("x", "y", "z")):
        _integer_attribute(
            mesh,
            f"mr_source_normal_bits_{label}",
            "POINT",
            (float32_signed_bits(value[component]) for value in source_normals),
        )


def _apply_uv_layers(mesh, uv_sets):
    flip_v = BLENDER_PREVIEW_UV_POLICY == "flip-v"
    for uv_index, uv_set in enumerate(uv_sets):
        preview_uvs = transform_uv_values(uv_set.values, flip_v=flip_v)
        layer = mesh.uv_layers.new(name=f"MR UV {uv_index}")
        for loop in mesh.loops:
            layer.data[loop.index].uv = preview_uvs[loop.vertex_index]


def _apply_color_preview(mesh, raw_colors):
    attribute = mesh.color_attributes.new(
        name="MR Vertex Color",
        type="BYTE_COLOR",
        domain="POINT",
    )
    for index, item in enumerate(attribute.data):
        color = tuple(
            raw_colors[index * 4 + channel] / 255.0 for channel in range(4)
        )
        if hasattr(item, "color_srgb"):
            item.color_srgb = color
        else:
            item.color = color


def _face_records(model):
    faces = []
    draws = []
    source_triangles = []
    groups = []
    for draw in model.physical_draws:
        triangles = triangles_from_indices(model.draw_global_indices(draw))
        for relative_index, triangle in enumerate(triangles):
            faces.append(triangle)
            draws.append(draw.draw_index)
            source_triangles.append(draw.index_start // 3 + relative_index)
            groups.append(draw.top_level_index)
    return faces, draws, source_triangles, groups


def _apply_display_normals(mesh, transformed_source_normals):
    display_normals, diagnostics, fallback_reason = prepare_display_normals(
        transformed_source_normals,
        len(mesh.vertices),
    )
    warnings = []
    if display_normals is not None:
        # Generate and validate the preferred per-corner candidate in Python,
        # but do not call Blender 5.2.2 custom-normal APIs: both its
        # from-vertices and per-corner paths caused native access violations
        # during real multi-resource folder imports.
        corner_normals = expand_corner_normals(
            display_normals,
            (loop.vertex_index for loop in mesh.loops),
        )
        if len(corner_normals) != len(mesh.loops):
            fallback_reason = "corner-normal count mismatch"
        else:
            fallback_reason = None
    if fallback_reason is not None:
        warnings.append(f"display normals fallback: {fallback_reason}")
    mesh.update()
    return "blender-calculated-fallback", diagnostics, warnings


def import_dx_resource(
    dx_path: Path,
    collection,
    *,
    object_name: str | None = None,
    import_sidecar: bool = True,
    load_textures: bool = True,
    strict: bool = True,
    material_cache: PreviewMaterialCache | None = None,
):
    source = dx_path.resolve()
    model = parse_dx(source)
    if strict and not model.diagnostics.validated:
        raise ValueError(
            "DX geometry validation did not pass: "
            + "; ".join(model.diagnostics.errors)
        )

    sidecar_path = source.with_suffix(".txt")
    sidecar = (
        parse_sidecar(sidecar_path)
        if import_sidecar and sidecar_path.exists()
        else None
    )
    apply_material_candidates(model.physical_draws, sidecar)
    positions = transform_blender_positions(model.vertices.positions)
    transformed_normals = transform_blender_normals(model.vertices.normals)
    faces, face_draws, source_triangles, face_groups = _face_records(model)

    mesh = bpy.data.meshes.new(f"{object_name or source.stem} Mesh")
    mesh.from_pydata(positions, [], faces)
    mesh.update(calc_edges=True)
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    _apply_uv_layers(mesh, model.uv_sets)
    _apply_color_preview(mesh, model.vertices.colors)
    _apply_source_attributes(
        mesh,
        face_draws,
        source_triangles,
        face_groups,
        model.vertices.colors,
        model.vertices.normals,
    )
    normal_strategy, normal_diagnostics, normal_warnings = _apply_display_normals(
        mesh,
        transformed_normals,
    )

    cache = material_cache or PreviewMaterialCache(
        source.parent,
        load_textures=load_textures,
    )
    warning_start = len(cache.warnings)
    slot_by_material = {}
    draw_material_slots = {}
    for draw in model.physical_draws:
        material = cache.material_for_draw(draw)
        pointer = material.as_pointer()
        if pointer not in slot_by_material:
            mesh.materials.append(material)
            slot_by_material[pointer] = len(mesh.materials) - 1
        draw_material_slots[draw.draw_index] = slot_by_material[pointer]
    for polygon, draw_id in zip(mesh.polygons, face_draws):
        polygon.material_index = draw_material_slots[draw_id]

    resource_material_warnings = cache.warnings[warning_start:]
    warnings = tuple(
        list(model.diagnostics.warnings)
        + normal_warnings
        + resource_material_warnings
    )

    obj = bpy.data.objects.new(object_name or source.stem, mesh)
    collection.objects.link(obj)
    metadata = build_metadata(
        model,
        sidecar,
        source,
        positions,
        faces,
        normal_diagnostics=normal_diagnostics,
        display_normal_strategy=normal_strategy,
    )
    metadata["blender"] = {
        "representation": "one-object-per-dx",
        "point_attributes": [
            "mr_source_vertex",
            "mr_source_vertex_valid",
            "mr_source_normal",
            "mr_source_normal_valid",
            "mr_source_normal_bits_x",
            "mr_source_normal_bits_y",
            "mr_source_normal_bits_z",
        ],
        "face_attributes": ["mr_draw_id", "mr_source_triangle", "mr_group_id"],
        "raw_color_attributes": [f"mr_color_byte_{index}" for index in range(4)],
        "uv_layers": [f"MR UV {index}" for index in range(len(model.uv_sets))],
        "material_slots": len(mesh.materials),
        "display_normal_strategy": normal_strategy,
        "import_warnings": list(warnings),
    }
    apply_object_metadata(obj, metadata)
    return BlenderImportResult(
        object=obj,
        model=model,
        sidecar=sidecar,
        warnings=warnings,
    )
