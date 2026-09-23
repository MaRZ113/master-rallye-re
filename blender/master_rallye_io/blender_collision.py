"""Read-only Blender visualization of parsed Master Rallye collision data."""
from __future__ import annotations

import json

import bpy

from .library import transform_blender_positions


def _collision_mesh(name, geometry, collection, owner, role, color):
    mesh = bpy.data.meshes.new(f"{name} Mesh")
    mesh.from_pydata(
        transform_blender_positions(geometry.vertices),
        [],
        geometry.triangles,
    )
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.color = color
    obj.hide_render = True
    obj.hide_select = True
    obj.show_name = True
    obj["mr_collision_read_only"] = True
    obj["mr_collision_owner"] = owner
    obj["mr_collision_role"] = role
    obj["mr_collision_geometry_offset"] = geometry.offset
    obj["mr_collision_geometry_end_offset"] = geometry.end_offset
    obj["mr_collision_metadata_json"] = json.dumps({
        "tag": 101,
        "role": role,
        "vertex_count": geometry.vertex_count,
        "triangle_count": geometry.triangle_count,
        "offset": geometry.offset,
        "end_offset": geometry.end_offset,
        "read_only": True,
        "export_supported": False,
    }, separators=(",", ":"))
    return obj


def create_collision_overlay(model, parent_collection, owner: str, resource_name: str):
    """Create non-selectable helper objects; never alter the authoring mesh."""
    hull = model.collision.convex_hull
    if hull is None or model.collision.errors:
        return (), None
    collection = bpy.data.collections.new(f"Master Rallye Collision - {resource_name}")
    parent_collection.children.link(collection)
    collection.hide_render = True
    collection["mr_collision_owner"] = owner
    collection["mr_collision_tag"] = 101
    collection["mr_collision_read_only"] = True
    objects = []
    if hull.base_geometry.vertex_count == 1 and hull.base_scalar > 0.0:
        center = transform_blender_positions(hull.base_geometry.vertices)[0]
        sphere = bpy.data.objects.new(f"{resource_name} - Base Radius Preview", None)
        sphere.empty_display_type = "SPHERE"
        sphere.empty_display_size = hull.base_scalar
        sphere.location = center
        sphere.color = (0.95, 0.8, 0.15, 0.35)
        sphere.hide_render = True
        sphere.hide_select = True
        sphere.show_name = True
        sphere["mr_collision_read_only"] = True
        sphere["mr_collision_owner"] = owner
        sphere["mr_collision_role"] = "base-radius-preview"
        sphere["mr_collision_tag_offset"] = hull.tag_offset
        collection.objects.link(sphere)
        objects.append(sphere)
    for label, representation, color in (
        ("Representation A", hull.representation_a, (1.0, 0.45, 0.05, 0.35)),
        ("Representation B", hull.representation_b, (0.1, 0.75, 1.0, 0.35)),
    ):
        geometry = representation.geometry_a
        if geometry.vertex_count:
            objects.append(_collision_mesh(
                f"{resource_name} - {label}", geometry, collection, owner,
                label.casefold().replace(" ", "-"), color,
            ))
    return tuple(objects), collection


def set_collision_visibility(owner: str, visible: bool) -> int:
    count = 0
    for obj in bpy.data.objects:
        if obj.get("mr_collision_owner") == owner:
            obj.hide_viewport = not visible
            count += 1
    return count
