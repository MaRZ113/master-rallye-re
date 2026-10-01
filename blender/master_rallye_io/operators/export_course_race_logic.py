"""Export only allowlisted RaceTest race-logic edits from Blender helpers."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from ..library import blender_position_to_source, load_course_race_logic_authoring


_TRANSFORM_EPSILON = 1.0e-5


def _walk(collection):
    yield collection
    for child in collection.children:
        yield from _walk(child)


def _selected_logic_root(context):
    obj = context.object
    source = obj.get("mr_xml_source") if obj else None
    roots = [
        item for item in bpy.data.collections
        if item.get("mr_xml_collection_kind") == "race_logic_root"
        and item.get("mr_xml_source")
        and (source is None or item.get("mr_xml_source") == source)
    ]
    if len(roots) != 1:
        raise ValueError("Select a helper from one imported Race Logic collection before exporting")
    return roots[0]


def _json_vector(obj, key, size=3):
    try:
        result = tuple(float(value) for value in json.loads(obj[key]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"{obj.name} is missing valid {key} metadata") from error
    if len(result) != size or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{obj.name} has invalid {key} metadata")
    return result


def _changed(actual, original, epsilon=_TRANSFORM_EPSILON):
    return math.dist(tuple(float(value) for value in actual), original) > epsilon


def _original_transform_warnings(obj):
    warnings = []
    for key, value_name, label in (
        ("mr_initial_blender_rotation_json", obj.rotation_euler, "rotation"),
        ("mr_initial_blender_scale_json", obj.scale, "scale"),
    ):
        if key not in obj:
            continue
        original = _json_vector(obj, key)
        if _changed(value_name, original):
            warnings.append(f"{obj.name}: {label} is ignored by RaceTest export; only marker/center translation is authored")
    return warnings


def _apply_scene_edits(root, editor):
    objects = tuple(root.all_objects)
    warnings = []

    for area_name, setter in (
        ("StartArea", editor.set_start_marker),
        ("FinishArea", editor.set_finish_marker),
    ):
        status = next(item for item in editor.area_status if item.name == area_name)
        area_helpers = [
            obj for obj in objects
            if obj.get("mr_race_logic_object_type") == "area_marker"
            and obj.get("mr_race_logic_area") == area_name
        ]
        if not status.supported:
            for obj in area_helpers:
                initial = _json_vector(obj, "mr_initial_blender_position_json")
                current = tuple(float(value) for value in obj.matrix_world.translation)
                if _changed(current, initial):
                    raise ValueError(
                        f"{area_name} is read-only or ambiguous; {obj.name} was moved and cannot be exported"
                    )
            continue
        helpers = [obj for obj in area_helpers if obj.get("mr_race_logic_editable")]
        by_index = {}
        for obj in helpers:
            index = obj.get("mr_marker_index_in_list")
            if not isinstance(index, int) or index in by_index:
                raise ValueError(f"{area_name} has an invalid or duplicate Blender marker index")
            by_index[index] = obj
        if set(by_index) != {0, 1, 2, 3}:
            raise ValueError(f"{area_name} needs exactly four intact marker helpers to export")
        for index in range(4):
            obj = by_index[index]
            initial_blender = _json_vector(obj, "mr_initial_blender_position_json")
            world_position = tuple(float(value) for value in obj.matrix_world.translation)
            warnings.extend(_original_transform_warnings(obj))
            if _changed(world_position, initial_blender):
                setter(index, blender_position_to_source(world_position))

    authorable_splits = {item.identity: item for item in editor.split_status if item.supported}
    all_split_helpers = [
        obj for obj in objects
        if obj.get("mr_race_logic_object_type") == "split_center"
    ]
    helpers = [
        obj for obj in objects
        if obj.get("mr_race_logic_editable") and obj.get("mr_race_logic_object_type") == "split_center"
    ]
    split_by_identity = {}
    for obj in helpers:
        identity = obj.get("mr_split_source_identity")
        if not identity or identity in split_by_identity:
            raise ValueError(f"SplitTime helper has a missing or duplicate source identity: {obj.name}")
        split_by_identity[identity] = obj
    for obj in all_split_helpers:
        if obj.get("mr_race_logic_editable"):
            continue
        initial = _json_vector(obj, "mr_initial_blender_position_json")
        current = tuple(float(value) for value in obj.matrix_world.translation)
        if _changed(current, initial):
            raise ValueError(f"{obj.name} is read-only or ambiguous; its center cannot be exported")
        for key, source_key, label in (
            ("mr_split_radius", "mr_source_split_radius", "Radius"),
            ("mr_split_time_id", "mr_source_split_time_id", "Split Time ID"),
        ):
            if source_key in obj and key in obj and obj[key] != obj[source_key]:
                raise ValueError(f"{obj.name} is read-only or ambiguous; {label} cannot be exported")
    if set(split_by_identity) != set(authorable_splits):
        missing = sorted(set(authorable_splits) - set(split_by_identity))
        extra = sorted(set(split_by_identity) - set(authorable_splits))
        raise ValueError(f"SplitTime helper inventory changed (missing={missing}, unexpected={extra})")

    for identity, status in authorable_splits.items():
        obj = split_by_identity[identity]
        initial_blender = _json_vector(obj, "mr_initial_blender_position_json")
        world_position = tuple(float(value) for value in obj.matrix_world.translation)
        warnings.extend(_original_transform_warnings(obj))
        if _changed(world_position, initial_blender):
            editor.set_split_center(identity, blender_position_to_source(world_position))
        try:
            radius = float(obj["mr_split_radius"])
            split_id = obj["mr_split_time_id"]
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{obj.name} is missing its editable Radius or Split Time ID") from error
        if isinstance(split_id, bool) or not isinstance(split_id, int):
            raise ValueError(f"{obj.name} Split Time ID must remain an integer")
        if status.radius is None or radius != status.radius:
            editor.set_split_radius(identity, radius)
        if status.split_id is None or isinstance(split_id, bool) or int(split_id) != status.split_id:
            editor.set_split_id(identity, split_id)
    return warnings


class EXPORT_SCENE_OT_master_rallye_race_logic_xml(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.master_rallye_race_logic_xml"
    bl_label = "Export Race Logic XML"
    bl_description = "Export only StartArea, FinishArea, and SplitTime fields from the selected Race Logic project"
    bl_options = {"REGISTER"}

    filename_ext = ".xml"
    filter_glob: StringProperty(default="*.xml", options={"HIDDEN"})

    def invoke(self, context, event):
        try:
            root = _selected_logic_root(context)
            source = Path(root["mr_xml_source"])
            self.filepath = str(source.with_name(source.stem + "_edited.xml"))
        except Exception:
            self.filepath = "RaceTest_edited.xml"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            root = _selected_logic_root(context)
            source = Path(root["mr_xml_source"]).resolve()
            payload = source.read_bytes()
            source_hash = hashlib.sha256(payload).hexdigest()
            if source_hash != root.get("mr_xml_sha256"):
                raise ValueError("The source RaceTest XML changed after import; reload its helpers before exporting")
            editor = load_course_race_logic_authoring(source)
            if editor.source_sha256 != source_hash:
                raise ValueError("RaceTest source hash changed while preparing the export")
            blender_warnings = _apply_scene_edits(root, editor)
            report = editor.write_export(Path(self.filepath), additional_warnings=blender_warnings)
            warning_count = len(report.warnings)
            self.report(
                {"INFO"},
                f"Exported {len(report.changes)} RaceTest field edits; {warning_count} warning(s): {report.source_sha256[:12]} → {report.exported_sha256[:12]}",
            )
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
