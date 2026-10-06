"""Small reusable viewport-only helpers for course source diagnostics."""
from __future__ import annotations

from mathutils import Matrix, Vector

import bpy


def _parent_at_local_origin(obj, parent):
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    return obj


def create_direction_ray(
    collection,
    name: str,
    parent,
    *,
    local_direction=(0.0, 0.0, 1.0),
    length: float = 8.0,
    color=(0.1, 0.9, 1.0, 1.0),
    thickness: float = 0.035,
):
    """Create an editor-only arrow in a parent's local orientation basis.

    The vector is intentionally expressed in parent-local coordinates so a
    caller can visualize an imported matrix basis without asserting gameplay
    meaning for that basis.
    """
    direction = Vector(local_direction)
    if direction.length_squared < 1.0e-12 or length <= 0.0 or thickness <= 0.0:
        raise ValueError("direction ray needs a nonzero direction and positive dimensions")
    direction.normalize()
    side_seed = Vector((1.0, 0.0, 0.0))
    if abs(direction.dot(side_seed)) > 0.9:
        side_seed = Vector((0.0, 1.0, 0.0))
    side = (side_seed - direction * direction.dot(side_seed)).normalized()
    tip = direction * length
    head_length = min(length * 0.18, 1.0)
    head_width = min(length * 0.075, 0.42)
    left = tip - direction * head_length + side * head_width
    right = tip - direction * head_length - side * head_width

    curve = bpy.data.curves.new(f"{name} diagnostic curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = thickness
    curve.bevel_resolution = 2
    for points in ((Vector((0.0, 0.0, 0.0)), tip), (left, tip), (right, tip)):
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for point, coordinate in zip(spline.points, points):
            point.co = (*coordinate, 1.0)

    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    _parent_at_local_origin(obj, parent)
    obj.show_in_front = True
    obj.color = color
    obj["mr_editor_only"] = True
    obj["mr_read_only"] = True
    obj["mr_course_helper_kind"] = "diagnostic_direction_ray"
    obj["mr_role"] = "diagnostic_orientation_basis_ray"
    obj["mr_direction_local_xyz"] = list(local_direction)
    obj["mr_direction_length"] = float(length)
    return obj


def create_marker_billboard(
    collection,
    name: str,
    parent,
    label: str,
    *,
    panel_material,
    text_material,
    local_right=(1.0, 0.0, 0.0),
    local_up=(0.0, 1.0, 0.0),
    local_offset=(0.0, 0.0, 0.0),
    width: float = 2.35,
    height: float = 1.05,
    pole_width: float = 0.10,
):
    """Create a labeled, procedural panel aligned to local right/up vectors.

    Returns ``(panel_object, text_object)``. The helper has no game textures or
    geometry and is suitable for read-only viewport diagnostics.
    """
    right = Vector(local_right)
    up = Vector(local_up)
    if right.length_squared < 1.0e-12 or up.length_squared < 1.0e-12:
        raise ValueError("billboard right/up vectors must be nonzero")
    right.normalize()
    up.normalize()
    if abs(right.dot(up)) > 1.0e-4:
        raise ValueError("billboard right/up vectors must be perpendicular")
    normal = right.cross(up).normalized()
    if width <= 0.0 or height <= 0.0 or pole_width <= 0.0:
        raise ValueError("billboard dimensions must be positive")

    pole_top = 0.32
    panel_top = pole_top + height

    def point(horizontal: float, vertical: float, depth: float = 0.0):
        return tuple(right * horizontal + up * vertical + normal * depth)

    vertices = [
        point(-pole_width / 2, 0.0), point(pole_width / 2, 0.0),
        point(pole_width / 2, pole_top), point(-pole_width / 2, pole_top),
        point(-width / 2, pole_top), point(width / 2, pole_top),
        point(width / 2, panel_top), point(-width / 2, panel_top),
    ]
    mesh = bpy.data.meshes.new(f"{name} procedural panel mesh")
    mesh.from_pydata(vertices, [], ((0, 1, 2, 3), (4, 5, 6, 7)))
    mesh.materials.append(panel_material)
    panel = bpy.data.objects.new(name, mesh)
    collection.objects.link(panel)
    _parent_at_local_origin(panel, parent)
    panel.location = tuple(Vector(local_offset))
    panel.show_in_front = True
    panel.color = (1.0, 0.72, 0.05, 1.0)
    panel["mr_editor_only"] = True
    panel["mr_read_only"] = True
    panel["mr_course_helper_kind"] = "diagnostic_marker_billboard"
    panel["mr_role"] = "split_billboard"
    panel["mr_billboard_local_offset"] = [float(value) for value in local_offset]

    text_data = bpy.data.curves.new(f"{name} label data", type="FONT")
    text_data.body = str(label)
    text_data.size = min(0.38, height * 0.40)
    text_data.align_x = "CENTER"
    text_data.align_y = "CENTER"
    text_data.materials.append(text_material)
    text_obj = bpy.data.objects.new(f"{name}_Label", text_data)
    collection.objects.link(text_obj)
    text_obj.parent = panel
    text_obj.matrix_parent_inverse = Matrix.Identity(4)
    text_obj.location = tuple(up * (pole_top + height / 2) + normal * 0.015)
    basis = Matrix((right, up, normal)).transposed()
    text_obj.rotation_euler = basis.to_euler()
    text_obj.show_in_front = True
    text_obj.color = (0.035, 0.025, 0.01, 1.0)
    text_obj["mr_editor_only"] = True
    text_obj["mr_read_only"] = True
    text_obj["mr_course_helper_kind"] = "diagnostic_marker_billboard_label"
    text_obj["mr_role"] = "split_billboard_label"
    return panel, text_obj
