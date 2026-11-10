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
_MARKER_TYPES = {"route_marker", "limit_marker"}
_CURVE_KIND = "RaceTest MarkerList source-order diagnostic polyline"
STATUS_PROPERTY = "mr_polyline_refresh_status"


def _identity(obj):
    return (
        obj.get("mr_xml_source"),
        obj.get("mr_source_list_ordinal", obj.get("mr_marker_list_ordinal", -1)),
        obj.get("mr_source_list_name", obj.get("mr_marker_list_name", "")),
    )


def _collect(identities):
    """One pass over bpy.data.objects: markers and curves for the given lists."""
    markers = {identity: [] for identity in identities}
    curves = {identity: [] for identity in identities}
    for obj in bpy.data.objects:
        if obj.get("mr_race_logic_object_type") in _MARKER_TYPES:
            bucket = markers.get(_identity(obj))
        elif obj.get("mr_course_helper_kind") == _CURVE_KIND:
            bucket = curves.get(_identity(obj))
        else:
            continue
        if bucket is not None:
            bucket.append(obj)
    return markers, curves


def _set_status(curve_obj, status):
    if curve_obj.get(STATUS_PROPERTY) != status:
        curve_obj[STATUS_PROPERTY] = status
        if status != "ok":
            print(f"Master Rallye: {curve_obj.name}: polyline not refreshed ({status})")


def _refresh(curve_list, markers):
    if len(curve_list) != 1:
        return False
    curve_obj = curve_list[0]
    if len(markers) < 2 or len(curve_obj.data.splines) != 1:
        _set_status(curve_obj, "fewer than two markers or unexpected spline count")
        return False
    markers = sorted(markers, key=lambda obj: int(obj.get("mr_marker_index_in_list", -1)))
    indices = [int(obj.get("mr_marker_index_in_list", -1)) for obj in markers]
    if len(set(indices)) != len(indices):
        # A duplicated helper (Shift+D) carries the same list ordinal; the
        # exporter refuses it too, so make the stale curve visible here.
        _set_status(curve_obj, "duplicate marker helpers; remove copies to resume")
        return False
    points = curve_obj.data.splines[0].points
    if len(points) != len(markers):
        _set_status(curve_obj, f"{len(markers)} markers for {len(points)} curve points")
        return False
    world_to_curve = curve_obj.matrix_world.inverted_safe()
    for point, marker in zip(points, markers):
        local = world_to_curve @ marker.matrix_world.translation
        point.co = (local.x, local.y, local.z, 1.0)
    curve_obj.data.update_tag()
    _set_status(curve_obj, "ok")
    return True


def refresh_marker_list_polyline(source, list_ordinal, list_name):
    """Refresh one imported source-order curve from its current marker helpers."""
    if list_name not in _AUTHORABLE_LISTS:
        return False
    identity = (source, list_ordinal, list_name)
    markers, curves = _collect({identity})
    return _refresh(curves[identity], markers[identity])


@persistent
def _refresh_course_marker_polylines(_scene, depsgraph):
    dirty = set()
    for update in depsgraph.updates:
        obj = update.id
        if not isinstance(obj, bpy.types.Object):
            continue
        if obj.get("mr_race_logic_object_type") not in _MARKER_TYPES:
            continue
        if not getattr(update, "is_updated_transform", False):
            continue
        source, ordinal, name = _identity(obj)
        if source and name in _AUTHORABLE_LISTS:
            dirty.add((source, ordinal, name))
    if not dirty:
        return
    markers, curves = _collect(dirty)
    for identity in dirty:
        _refresh(curves[identity], markers[identity])


def register():
    handlers = bpy.app.handlers.depsgraph_update_post
    if _refresh_course_marker_polylines not in handlers:
        handlers.append(_refresh_course_marker_polylines)


def unregister():
    handlers = bpy.app.handlers.depsgraph_update_post
    if _refresh_course_marker_polylines in handlers:
        handlers.remove(_refresh_course_marker_polylines)
