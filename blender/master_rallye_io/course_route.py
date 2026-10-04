"""Keep read-only source-order route/corridor curves aligned with editable markers."""
from __future__ import annotations

import bpy
from bpy.app.handlers import persistent


_AUTHORABLE_LISTS = {
    "RaceLine",
    "LeftInnerLimit",
    "LeftOuterLimit",
    "RightInnerLimit",
    "RightOuterLimit",
}


def _identity(obj):
    return (
        obj.get("mr_xml_source"),
        obj.get("mr_source_list_ordinal", obj.get("mr_marker_list_ordinal", -1)),
        obj.get("mr_source_list_name", obj.get("mr_marker_list_name", "")),
    )


def refresh_marker_list_polyline(source, list_ordinal, list_name):
    """Refresh one imported source-order curve from its current marker helpers."""
    if list_name not in _AUTHORABLE_LISTS:
        return False
    identity = (source, list_ordinal, list_name)
    markers = [
        obj for obj in bpy.data.objects
        if obj.get("mr_race_logic_object_type") in {"route_marker", "limit_marker"}
        and _identity(obj) == identity
    ]
    markers.sort(key=lambda obj: int(obj.get("mr_marker_index_in_list", -1)))
    curves = [
        obj for obj in bpy.data.objects
        if obj.get("mr_course_helper_kind") == "RaceTest MarkerList source-order diagnostic polyline"
        and _identity(obj) == identity
    ]
    if len(curves) != 1 or len(markers) < 2:
        return False
    curve_obj = curves[0]
    if len(curve_obj.data.splines) != 1:
        return False
    points = curve_obj.data.splines[0].points
    if len(points) != len(markers):
        return False
    world_to_curve = curve_obj.matrix_world.inverted_safe()
    for point, marker in zip(points, markers):
        local = world_to_curve @ marker.matrix_world.translation
        point.co = (local.x, local.y, local.z, 1.0)
    curve_obj.data.update_tag()
    return True


@persistent
def _refresh_course_marker_polylines(_scene, depsgraph):
    dirty = set()
    for update in depsgraph.updates:
        obj = update.id
        if not isinstance(obj, bpy.types.Object):
            continue
        if obj.get("mr_race_logic_object_type") not in {"route_marker", "limit_marker"}:
            continue
        if not getattr(update, "is_updated_transform", False):
            continue
        source, ordinal, name = _identity(obj)
        if source and name in _AUTHORABLE_LISTS:
            dirty.add((source, ordinal, name))
    for source, ordinal, name in dirty:
        refresh_marker_list_polyline(source, ordinal, name)


def register():
    handlers = bpy.app.handlers.depsgraph_update_post
    if _refresh_course_marker_polylines not in handlers:
        handlers.append(_refresh_course_marker_polylines)


def unregister():
    handlers = bpy.app.handlers.depsgraph_update_post
    if _refresh_course_marker_polylines in handlers:
        handlers.remove(_refresh_course_marker_polylines)
