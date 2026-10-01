"""RaceTest XML race-logic helpers with bounded, allowlist-only authoring."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix

from ..blender_mesh import create_collection
from ..library import load_course_project, load_course_race_logic_authoring, position_to_blender


def _walk_collections(collection):
    yield collection
    for child in collection.children:
        yield from _walk_collections(child)


def _contains_object(collection, target):
    if target is None:
        return False
    if target.name in collection.objects:
        return True
    return any(_contains_object(child, target) for child in collection.children)


def _get_child_collection(parent, name, kind):
    for child in parent.children:
        if child.get("mr_xml_collection_kind") == kind:
            return child
    child = create_collection(name, parent)
    child["mr_xml_collection_kind"] = kind
    return child


def _source_vector(value):
    return None if value is None else list(value)


def _set_evidence_metadata(obj, semantic_rule_evidence, record_evidence=()):
    obj["mr_semantic_rule_evidence"] = "; ".join(semantic_rule_evidence)
    obj["mr_record_evidence_json"] = json.dumps(list(record_evidence), ensure_ascii=False)


def _set_marker_metadata(obj, source, course_name, marker):
    obj["mr_resource_kind"] = "course"
    obj["mr_read_only"] = True
    obj["mr_course_helper_kind"] = "RaceTest XML Marker"
    obj["mr_course_identity"] = course_name
    obj["mr_xml_source"] = source
    obj["mr_xml_path"] = marker.record.xml_path
    obj["mr_marker_ordinal"] = marker.ordinal
    obj["mr_marker_list_name"] = marker.marker_list_name or ""
    obj["mr_marker_list_ordinal"] = -1 if marker.marker_list_ordinal is None else marker.marker_list_ordinal
    obj["mr_marker_index_in_list"] = marker.index_in_list
    obj["mr_marker_no"] = marker.marker_no or ""
    obj["mr_marker_type"] = marker.marker_type or ""
    obj["mr_source_position_xyz"] = _source_vector(marker.position) or []
    obj["mr_source_position_raw"] = marker.raw_position or ""
    obj["mr_source_direction_xyz"] = _source_vector(marker.direction) or []
    obj["mr_source_direction_raw"] = marker.raw_direction or ""
    obj["mr_xml_record_json"] = json.dumps(
        {
            "tag": marker.record.tag,
            "attributes": dict(marker.record.attributes),
            "xml_path": marker.record.xml_path,
            "values": [
                {
                    "name": value.name,
                    "type": value.type_name,
                    "value": value.value,
                    "attributes": dict(value.attributes),
                }
                for value in marker.record.values
            ],
            "issues": list(marker.issues),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _create_marker_point(
    collection, source, course_name, marker, area_kind=None,
    semantic_rule_evidence=(), record_evidence=(), area_supported=False, source_sha256="",
):
    label = marker.marker_type or "unknown"
    list_name = marker.marker_list_name or "Unlisted"
    obj = bpy.data.objects.new(
        f"{list_name} Marker {marker.index_in_list:04d} - {label}", None
    )
    collection.objects.link(obj)
    obj.empty_display_type = "CIRCLE" if area_kind in {"StartArea", "FinishArea"} else "SPHERE"
    obj.empty_display_size = 1.5 if area_kind else (0.65 if list_name == "RaceLine" else 1.0)
    obj.show_in_front = True
    obj.location = position_to_blender(marker.position)
    _set_marker_metadata(obj, source, course_name, marker)
    _set_evidence_metadata(obj, semantic_rule_evidence, record_evidence)
    if area_kind in {"StartArea", "FinishArea"}:
        obj["mr_race_logic_editable"] = bool(area_supported)
        obj["mr_race_logic_object_type"] = "area_marker"
        obj["mr_race_logic_area"] = area_kind
        obj["mr_source_xml_sha256"] = source_sha256
        obj["mr_initial_blender_position_json"] = json.dumps([float(value) for value in obj.location])
        obj["mr_initial_blender_rotation_json"] = json.dumps([float(value) for value in obj.rotation_euler])
        obj["mr_initial_blender_scale_json"] = json.dumps([float(value) for value in obj.scale])
        obj["mr_semantics_status"] = "CONFIRMED_BY_RUNTIME_EDIT" if area_supported else "read-only: ambiguous or incomplete source area"
        obj["mr_read_only"] = not area_supported
    return obj


def _create_area_outline(
    collection, source, course_name, marker_list, semantic_role,
    semantic_rule_evidence, record_evidence,
):
    markers = [item for item in marker_list.markers if item.position is not None]
    if len(markers) < 2:
        return None
    curve = bpy.data.curves.new(f"{marker_list.name} source-order outline", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.22
    curve.bevel_resolution = 1
    spline = curve.splines.new("POLY")
    spline.points.add(len(markers) - 1)
    for point, marker in zip(spline.points, markers):
        point.co = (*position_to_blender(marker.position), 1.0)
    spline.use_cyclic_u = len(markers) == 4
    obj = bpy.data.objects.new(f"{marker_list.name} source-order outline", curve)
    collection.objects.link(obj)
    obj.show_in_front = True
    obj.color = (0.1, 0.75, 0.95, 1.0) if marker_list.name == "StartArea" else (1.0, 0.35, 0.1, 1.0)
    obj["mr_resource_kind"] = "course"
    obj["mr_read_only"] = True
    obj["mr_course_helper_kind"] = "RaceTest XML source-order area outline"
    obj["mr_course_identity"] = course_name
    obj["mr_xml_source"] = source
    obj["mr_xml_path"] = marker_list.xml_path
    obj["mr_marker_list_name"] = marker_list.name or ""
    obj["mr_semantics"] = semantic_role
    obj["mr_marker_count"] = len(markers)
    obj["mr_source_marker_order"] = [marker.index_in_list for marker in markers]
    obj["mr_outline_only"] = True
    obj["mr_filled_area_created"] = False
    _set_evidence_metadata(obj, semantic_rule_evidence, record_evidence)
    obj["mr_semantics_limit"] = "Source-order outline only; no per-car interpolation or sole-subsystem claim"
    return obj


def _matrix_rotation(matrix):
    """Convert the serialized row-basis orientation through the shared axes."""
    rows = [matrix.row(index) for index in range(3)]
    if any(row is None for row in rows):
        return None
    # Source vectors use the add-on's proven (X, -Z, Y) axis conversion.
    axes = [position_to_blender(row[:3]) for row in rows]
    # Matrix's columns are the converted local basis vectors.
    return Matrix((
        (axes[0][0], axes[1][0], axes[2][0]),
        (axes[0][1], axes[1][1], axes[2][1]),
        (axes[0][2], axes[1][2], axes[2][2]),
    )).to_euler()


def _split_sign_material():
    name = "MR Race Logic Helper - Split Visual"
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
        material.diffuse_color = (1.0, 0.72, 0.05, 1.0)
        material.use_nodes = True
        principled = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
        if principled is not None:
            color = principled.inputs.get("Base Color")
            if color is not None:
                color.default_value = (1.0, 0.72, 0.05, 1.0)
            emission = principled.inputs.get("Emission Color") or principled.inputs.get("Emission")
            if emission is not None:
                emission.default_value = (1.0, 0.54, 0.015, 1.0)
            strength = principled.inputs.get("Emission Strength")
            if strength is not None:
                strength.default_value = 0.25
    return material


def _source_egg_metadata(egg):
    def value_payload(value):
        return {
            "name": value.name,
            "type": value.type_name,
            "value": value.value,
            "attributes": list(value.attributes),
        }

    return {
        "egg_attributes": list(egg.attributes),
        "egg_values": [value_payload(value) for value in egg.values],
        "ai_objects": [
            {
                "ordinal": ai.ordinal,
                "no": ai.ai_no,
                "name": ai.ai_name,
                "attributes": list(ai.attributes),
                "values": [value_payload(value) for value in ai.values],
                "xml_path": ai.xml_path,
                "components": [
                    {
                        "tag": component.tag,
                        "attributes": list(component.attributes),
                        "values": [value_payload(value) for value in component.values],
                        "xml_path": component.xml_path,
                    }
                    for component in ai.components
                ],
            }
            for ai in egg.ai_objects
        ],
    }


def _create_split_visual(collection, source, course_name, split, split_status, source_sha256):
    egg = split.source_egg
    matrix = egg.matrix("en3d Matrix")
    if matrix is None or split.center is None:
        return None
    label = str(split.split_id) if split.split_id is not None else (egg.name or str(egg.index_in_list))

    # A small, original arrow-board icon. This is a procedural visualization,
    # not a copied game model or texture.
    vertices = [
        (-1.10, 0.0, -0.28), (0.18, 0.0, -0.28), (0.18, 0.0, -0.62),
        (0.95, 0.0, 0.0), (0.18, 0.0, 0.62), (0.18, 0.0, 0.28),
        (-1.10, 0.0, 0.28), (-0.07, 0.0, -0.28), (0.07, 0.0, -0.28),
        (0.07, 0.0, -1.25), (-0.07, 0.0, -1.25),
    ]
    mesh = bpy.data.meshes.new(f"MR split visual icon {label}")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3, 4, 5, 6), (7, 8, 9, 10)])
    mesh.materials.append(_split_sign_material())
    obj = bpy.data.objects.new(f"MR_SplitTime{label}_Visual", mesh)
    collection.objects.link(obj)
    obj.location = position_to_blender(split.center)
    rotation = _matrix_rotation(matrix)
    if rotation is not None:
        obj.rotation_euler = rotation
    obj.show_in_front = True
    obj.color = (1.0, 0.72, 0.05, 1.0)
    obj["mr_resource_kind"] = "course"
    obj["mr_read_only"] = not split_status.supported
    obj["mr_course_helper_kind"] = "RaceTest split-time visual sign icon"
    obj["mr_course_identity"] = course_name
    obj["mr_xml_source"] = source
    obj["mr_xml_path"] = egg.xml_path
    obj["mr_egg_list_name"] = egg.list_name or ""
    obj["mr_egg_index_in_list"] = egg.index_in_list
    obj["mr_egg_name"] = egg.name or ""
    obj["mr_split_time_id_raw"] = split.split_id_raw or ""
    if split.split_id is not None:
        obj["mr_split_time_id"] = split.split_id
        obj["mr_source_split_time_id"] = split.split_id
        obj.id_properties_ui("mr_split_time_id").update(min=-(2 ** 31), max=2 ** 31 - 1)
    obj["mr_split_visual_position_xyz"] = list(split.center)
    obj["mr_split_visual_matrix_json"] = json.dumps(
        {"attributes": dict(matrix.attributes), "rows": [list(row) if row is not None else None for row in matrix.rows]},
        separators=(",", ":"),
    )
    obj["mr_split_radius_raw"] = split.radius_raw or ""
    obj["mr_split_extra_time_raw"] = split.extra_time_raw or ""
    if split.radius is not None:
        obj["mr_split_radius"] = split.radius
        obj["mr_source_split_radius"] = split.radius
    if split.extra_time is not None:
        obj["mr_split_extra_time"] = split.extra_time
    obj["mr_source_egg_metadata_json"] = json.dumps(
        _source_egg_metadata(egg), ensure_ascii=False, separators=(",", ":")
    )
    obj["mr_visual_position_rule_evidence"] = "; ".join(split.center_rule_evidence)
    obj["mr_gameplay_center_source"] = "same en3d Matrix Row3 as visual sign"
    obj["mr_center_rule_evidence"] = "; ".join(split.center_rule_evidence)
    obj["mr_trigger_shape"] = split.trigger_shape
    obj["mr_radius_rule_evidence"] = "; ".join(split.radius_rule_evidence)
    _set_evidence_metadata(obj, split.center_rule_evidence, split.record_evidence)
    obj["mr_extra_time_semantics"] = split.extra_time_semantics
    obj["mr_source_component_xml_path"] = split.source_component.xml_path
    obj["mr_icon_status"] = "procedural helper icon; not a game asset or exact render reproduction"
    obj["mr_race_logic_editable"] = bool(split_status.supported)
    obj["mr_race_logic_object_type"] = "split_center"
    obj["mr_split_source_identity"] = split_status.identity
    obj["mr_source_xml_sha256"] = source_sha256
    obj["mr_initial_blender_position_json"] = json.dumps([float(value) for value in obj.location])
    obj["mr_initial_blender_rotation_json"] = json.dumps([float(value) for value in obj.rotation_euler])
    obj["mr_initial_blender_scale_json"] = json.dumps([float(value) for value in obj.scale])
    obj["mr_semantics_status"] = "CONFIRMED_BY_EXECUTABLE; runtime edit confirmed for France1 SplitTime0" if split_status.supported else "read-only: ambiguous or incomplete split source"
    obj.lock_rotation = (True, True, True)
    obj.lock_scale = (True, True, True)
    return obj


def _create_split_checkpoint_group(collection, source, course_name, split, split_status):
    if split.center is None:
        return None
    label = split.egg_name or str(split.split_id if split.split_id is not None else "Unknown")
    obj = bpy.data.objects.new(f"{label}_Group", None)
    collection.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 2.0
    obj.show_in_front = True
    obj.location = position_to_blender(split.center)
    obj.color = (0.18, 0.72, 0.95, 1.0)
    obj["mr_resource_kind"] = "course"
    obj["mr_read_only"] = not split_status.supported
    obj["mr_course_helper_kind"] = "split_checkpoint_group"
    obj["mr_course_identity"] = course_name
    obj["mr_xml_source"] = source
    obj["mr_xml_path"] = split.egg_xml_path
    obj["mr_race_logic_object_type"] = "split_checkpoint_group"
    obj["mr_race_logic_editable"] = bool(split_status.supported)
    obj["mr_split_source_identity"] = split_status.identity
    obj["mr_split_source"] = split.egg_name or ""
    obj["mr_group_transform_rule"] = "translation only; child final world positions are exported"
    obj["mr_semantics_status"] = "CONFIRMED_BY_RUNTIME_EDIT: SplitTime center and visual companions remain separate editable points"
    obj.lock_rotation = (True, True, True)
    obj.lock_scale = (True, True, True)
    return obj


def _parent_preserving_world_transform(obj, parent):
    """Parent an imported helper while keeping its current world matrix exact."""
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = world
    bpy.context.view_layer.update()
    if "mr_initial_blender_position_json" in obj:
        obj["mr_initial_blender_position_json"] = json.dumps(
            [float(value) for value in obj.matrix_world.translation]
        )


def _create_split_trigger(collection, source, course_name, split, center_object):
    if not split.trigger_complete:
        return None
    radius = float(split.radius)
    label = str(split.split_id) if split.split_id is not None else (split.egg_name or "Unknown")
    curve = bpy.data.curves.new(f"MR split trigger sphere {label}", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.025 / radius
    curve.bevel_resolution = 1
    steps = 40
    for axis in range(3):
        spline = curve.splines.new("POLY")
        spline.points.add(steps - 1)
        for index, point in enumerate(spline.points):
            angle = 2.0 * 3.141592653589793 * index / steps
            cosine = __import__("math").cos(angle)
            sine = __import__("math").sin(angle)
            if axis == 0:
                co = (cosine, sine, 0.0, 1.0)
            elif axis == 1:
                co = (cosine, 0.0, sine, 1.0)
            else:
                co = (0.0, cosine, sine, 1.0)
            point.co = co
        spline.use_cyclic_u = True
    obj = bpy.data.objects.new(f"MR_SplitTime{label}_TriggerSphere", curve)
    collection.objects.link(obj)
    obj.parent = center_object
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (radius, radius, radius)
    obj.lock_location = (True, True, True)
    obj.lock_rotation = (True, True, True)
    obj.lock_scale = (True, True, True)
    obj.show_in_front = True
    obj.color = (0.95, 0.22, 0.08, 1.0)
    obj["mr_resource_kind"] = "course"
    obj["mr_read_only"] = True
    obj["mr_course_helper_kind"] = "split_trigger"
    obj["mr_course_identity"] = course_name
    obj["mr_split_time_id_raw"] = split.split_id_raw or ""
    if split.split_id is not None:
        obj["mr_split_time_id"] = split.split_id
    obj["mr_split_radius"] = radius
    obj["mr_split_radius_raw"] = split.radius_raw or ""
    obj["mr_split_extra_time_raw"] = split.extra_time_raw or ""
    obj["mr_split_extra_time_semantics"] = split.extra_time_semantics
    if split.extra_time is not None:
        obj["mr_split_extra_time"] = split.extra_time
    obj["mr_trigger_shape"] = split.trigger_shape
    obj["mr_trigger_center_source_xyz"] = list(split.center)
    obj["mr_source_xml_path"] = split.egg_xml_path
    obj["mr_component_xml_path"] = split.source_component.xml_path
    obj["mr_center_rule_evidence"] = "; ".join(split.center_rule_evidence)
    obj["mr_radius_rule_evidence"] = "; ".join(split.radius_rule_evidence)
    _set_evidence_metadata(obj, split.center_rule_evidence, split.record_evidence)
    obj["mr_coordinate_space_note"] = "center converted with canonical course source-to-Blender transform; radius unchanged"
    obj["mr_radius_visual_driver"] = "unit wire sphere scaled by its parent SplitTime Radius custom property"
    for axis in range(3):
        driver = obj.driver_add("scale", axis).driver
        driver.type = "SCRIPTED"
        driver.expression = "radius"
        variable = driver.variables.new()
        variable.name = "radius"
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = center_object
        variable.targets[0].data_path = '["mr_split_radius"]'
    return obj


def _create_visual_companion(
    collection, source, course_name, split, companion, companion_status, source_sha256,
):
    egg = companion.source_egg
    if companion.position is None:
        return None
    obj = bpy.data.objects.new(f"{egg.name or 'Split visual companion'}", None)
    collection.objects.link(obj)
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.8
    obj.show_in_front = True
    obj.location = position_to_blender(companion.position)
    obj["mr_resource_kind"] = "course"
    obj["mr_read_only"] = not bool(companion_status and companion_status.supported)
    obj["mr_course_helper_kind"] = "split_visual_companion"
    obj["mr_course_identity"] = course_name
    obj["mr_xml_source"] = source
    obj["mr_source_xml_path"] = egg.xml_path
    obj["mr_xml_path"] = egg.xml_path
    obj["mr_egg_list_name"] = egg.list_name or ""
    obj["mr_egg_index_in_list"] = egg.index_in_list
    obj["mr_egg_name"] = egg.name or ""
    obj["mr_model_name"] = egg.model_name or ""
    obj["mr_source_position_xyz"] = list(companion.position)
    obj["mr_source_xml_sha256"] = source_sha256
    obj["mr_race_logic_object_type"] = "split_visual_companion"
    obj["mr_race_logic_editable"] = bool(companion_status and companion_status.supported)
    obj["mr_split_source_identity"] = companion_status.split_identity if companion_status else ""
    source_identity = companion_status.source_identity if companion_status else ""
    obj["mr_visual_companion_source_identity"] = source_identity
    obj["mr_role"] = "split_visual_companion"
    obj["mr_split_source"] = split.egg_name or ""
    obj["mr_source_egg"] = egg.name or ""
    obj["mr_source_xml_identity"] = f"{course_name}:{source_identity}"
    obj["mr_initial_blender_position_json"] = json.dumps([float(value) for value in obj.location])
    obj["mr_initial_blender_rotation_json"] = json.dumps([float(value) for value in obj.rotation_euler])
    obj["mr_initial_blender_scale_json"] = json.dumps([float(value) for value in obj.scale])
    _set_evidence_metadata(
        obj,
        tuple(companion.semantic_rule_evidence) + ("CONFIRMED_BY_RUNTIME_EDIT",),
        companion.record_evidence,
    )
    obj["mr_is_trigger_center_source"] = False
    obj["mr_semantic_role"] = "visual checkpoint object; no trigger-center meaning assigned"
    obj["mr_source_egg_metadata_json"] = json.dumps(_source_egg_metadata(egg), ensure_ascii=False, separators=(",", ":"))
    obj.lock_scale = (True, True, True)
    return obj


class IMPORT_SCENE_OT_master_rallye_course_xml_markers(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.master_rallye_course_xml_markers"
    bl_label = "Load Course Race Logic"
    bl_description = "Load RaceTest helpers and enable only runtime-confirmed StartArea, FinishArea, and SplitTime edits"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".xml"
    filter_glob: StringProperty(default="*.xml", options={"HIDDEN"})

    def execute(self, context):
        source = Path(self.filepath).resolve()
        try:
            project = load_course_project(source)
            race_logic = project.race_logic
            if race_logic is None:
                raise ValueError("Course SDK could not parse the selected RaceTest XML")
            document = race_logic.source_document
            authoring = load_course_race_logic_authoring(source)
            area_status = {item.name: item for item in authoring.area_status}
            positioned = [marker for marker in document.markers if marker.position is not None]
            if not positioned and not race_logic.split_times:
                raise ValueError("XML contains no positioned Marker records or split-time visual eggs")

            candidates = [
                collection
                for collection in bpy.data.collections
                if collection.get("mr_resource_kind") == "course"
                and str(collection.get("mr_course_identity", "")).casefold().endswith(source.stem.casefold())
            ]
            active_matches = [collection for collection in candidates if _contains_object(collection, context.object)]
            if len(active_matches) == 1:
                root = active_matches[0]
            elif len(candidates) == 1:
                root = candidates[0]
            elif len(candidates) > 1:
                raise ValueError(
                    f"multiple imported course collections match {source.stem!r}; select one of their course meshes first"
                )
            else:
                root = bpy.data.collections.get(f"Master Rallye Course - {source.stem}")
            root_name = f"Master Rallye Course - {source.stem}"
            if root is None:
                root = create_collection(root_name)
                root["mr_resource_kind"] = "course"
                root["mr_course_identity"] = source.stem
                root["mr_read_only"] = True
                root["mr_import_note"] = "Created for RaceTest race-logic authoring; course render DX not imported"
            elif root.get("mr_resource_kind") != "course":
                raise ValueError(f"collection {root_name!r} exists but is not marked as a course")

            payload = source.read_bytes()
            source_path = str(source)
            if any(collection.get("mr_xml_source") == source_path for collection in _walk_collections(root)):
                raise ValueError(f"this XML source is already imported under {root.name}")

            helpers = next((child for child in root.children if child.name == "Course Helpers"), None)
            if helpers is None:
                helpers = create_collection("Course Helpers", root)
                helpers["mr_decode_status"] = "read-only RaceTest race-logic visualization"
            logic = create_collection("Race Logic", helpers)
            logic["mr_course_helper_kind"] = "RaceTest XML race-logic hierarchy"
            logic["mr_xml_collection_kind"] = "race_logic_root"
            logic["mr_xml_source"] = source_path
            logic["mr_xml_sha256"] = hashlib.sha256(payload).hexdigest()
            logic["mr_authoring_schema"] = "master-rallye-race-logic-edit-v1"
            logic["mr_course_identity"] = source.stem
            logic["mr_read_only"] = True
            logic["mr_marker_count"] = len(document.markers)
            logic["mr_split_visual_count"] = len(race_logic.split_times)
            logic["mr_split_trigger_count"] = sum(item.trigger_complete for item in race_logic.split_times)
            logic["mr_hierarchy_preserved"] = True
            logic["mr_semantics_source"] = "master_rallye.course_sdk CourseRaceLogic"
            logic["mr_read_only_semantics"] = False
            logic["mr_race_logic_authoring"] = True

            marker_lists_collection = _get_child_collection(logic, "MarkerLists - Other", "marker_lists_root")
            semantic_areas = {
                "StartArea": race_logic.start_area,
                "FinishArea": race_logic.finish_area,
            }
            for marker_list in document.marker_lists:
                semantic_area = semantic_areas.get(marker_list.name or "")
                if semantic_area is not None:
                    group = create_collection(marker_list.name or f"MarkerList {marker_list.ordinal}", logic)
                    kind = marker_list.name
                else:
                    group = create_collection(marker_list.name or f"MarkerList {marker_list.ordinal}", marker_lists_collection)
                    kind = None
                group["mr_xml_collection_kind"] = f"marker_list:{marker_list.ordinal}"
                group["mr_source_list_name"] = marker_list.name or ""
                group["mr_xml_path"] = marker_list.xml_path
                group["mr_source_list_ordinal"] = marker_list.ordinal
                group["mr_marker_count"] = len(marker_list.markers)
                if semantic_area is not None:
                    _set_evidence_metadata(group, semantic_area.semantic_rule_evidence, semantic_area.record_evidence)
                    group["mr_semantics"] = semantic_area.semantic_role
                    group["mr_centroid_xyz"] = list(semantic_area.centroid) if semantic_area.centroid else []
                    group["mr_local_xz_bounds"] = list(semantic_area.local_xz_bounds) if semantic_area.local_xz_bounds else []
                    group["mr_source_order_preserved"] = True
                    status = area_status[kind]
                    group["mr_authoring_supported"] = status.supported
                    group["mr_authoring_issues_json"] = json.dumps(list(status.issues), ensure_ascii=False)
                    group["mr_authoring_evidence"] = "CONFIRMED_BY_RUNTIME_EDIT"
                else:
                    group["mr_semantics_status"] = "UNKNOWN; ordered RaceTest markers preserved"
                for marker in marker_list.markers:
                    if marker.position is None:
                        continue
                    _create_marker_point(
                        group,
                        source_path,
                        source.stem,
                        marker,
                        kind,
                        semantic_area.semantic_rule_evidence if semantic_area is not None else (),
                        semantic_area.record_evidence if semantic_area is not None else (),
                        area_status[kind].supported if semantic_area is not None else False,
                        authoring.source_sha256,
                    )

            eggs_root = create_collection("EggLists_Version4", logic)
            eggs_root["mr_xml_collection_kind"] = "egg_lists_root"
            split_visuals = create_collection("SplitTimes", eggs_root)
            split_visuals["mr_xml_collection_kind"] = "egg_list:SplitTimes"
            split_visuals["mr_xml_path"] = "/Scene/EggLists_Version4/List[@Name='SplitTimes']"

            if len(race_logic.split_times) != len(authoring.split_status):
                raise ValueError("Course SDK and Race Logic authoring split inventories disagree")
            companion_status = {
                item.source_identity: item for item in authoring.visual_companion_status
            }
            for split, split_edit_status in zip(race_logic.split_times, authoring.split_status):
                egg = split.source_egg
                if split_edit_status.source_xml_path != split.egg_xml_path or split_edit_status.egg_name != split.egg_name:
                    raise ValueError(f"Course SDK and authoring source order disagree at {split.egg_xml_path}")
                split_label = str(split.split_id) if split.split_id is not None else (egg.name or str(egg.index_in_list))
                split_collection = create_collection(egg.name or f"SplitTime{split_label}", split_visuals)
                split_collection["mr_xml_collection_kind"] = f"split_egg:{split_label}"
                split_collection["mr_xml_path"] = egg.xml_path
                split_collection["mr_split_time_id_raw"] = split_label
                split_collection["mr_semantic_model"] = "master_rallye.course_sdk.CourseSplitTime"
                split_collection["mr_center_source"] = "en3d Matrix Row3"
                split_collection["mr_trigger_shape"] = split.trigger_shape
                split_collection["mr_center_rule_evidence"] = "; ".join(split.center_rule_evidence)
                split_collection["mr_radius_rule_evidence"] = "; ".join(split.radius_rule_evidence)
                split_collection["mr_companions_rule_evidence"] = "; ".join(split.companions_rule_evidence)
                _set_evidence_metadata(split_collection, split.center_rule_evidence, split.record_evidence)
                split_collection["mr_extra_time_semantics"] = split.extra_time_semantics
                split_collection["mr_sdk_issues_json"] = json.dumps(list(split.issues), ensure_ascii=False)

                group = _create_split_checkpoint_group(
                    split_collection, source_path, source.stem, split, split_edit_status
                )
                center = _create_split_visual(split_collection, source_path, source.stem, split, split_edit_status, authoring.source_sha256)
                if center is not None:
                    if group is not None:
                        _parent_preserving_world_transform(center, group)
                    _create_split_trigger(split_collection, source_path, source.stem, split, center)

                companions_collection = create_collection("Visual Checkpoint Objects", split_collection)
                companions_collection["mr_xml_collection_kind"] = "split_visual_companions"
                companions_collection["mr_semantic_role"] = "visual checkpoint objects; not trigger-center sources"
                _set_evidence_metadata(companions_collection, split.companions_rule_evidence)
                for companion in split.companions:
                    egg_identity = (
                        f"list[{companion.source_egg.list_ordinal}]"
                        f"/egg[{companion.source_egg.index_in_list}]"
                        f"/{companion.source_egg.name or '<unnamed>'}"
                    )
                    created = _create_visual_companion(
                        companions_collection,
                        source_path,
                        source.stem,
                        split,
                        companion,
                        companion_status.get(egg_identity),
                        authoring.source_sha256,
                    )
                    if created is not None and group is not None:
                        _parent_preserving_world_transform(created, group)

            self.report(
                {"INFO"},
                f"Loaded {len(positioned)} markers, {len(race_logic.split_times)} split records; runtime-confirmed fields are editable",
            )
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
