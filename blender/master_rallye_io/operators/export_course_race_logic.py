"""Export only allowlisted RaceTest race-logic edits from Blender helpers."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from ..library import blender_position_to_source, load_course_race_logic_authoring, position_to_blender


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


def _original_transform_warnings(obj, *, role):
    warnings = []
    rotation_changed = (
        "mr_initial_blender_rotation_json" in obj
        and _changed(obj.rotation_euler, _json_vector(obj, "mr_initial_blender_rotation_json"))
    )
    scale_changed = (
        "mr_initial_blender_scale_json" in obj
        and _changed(obj.scale, _json_vector(obj, "mr_initial_blender_scale_json"))
    )
    if role == "split_center":
        if rotation_changed:
            warnings.append("SplitTime helper rotation is not exported; source matrix orientation is preserved")
        if scale_changed:
            warnings.append("SplitTime object scale does not change gameplay Radius; edit Radius explicitly.")
    elif role == "split_visual_companion" and (rotation_changed or scale_changed):
        warnings.append("Split visual companion rotation/scale are not exported; only final world positions are authored")
    # A checkpoint may contain four visual children. Report unsupported
    # transform classes once, rather than spamming one identical warning per
    # child while preserving distinct warning categories.
    return list(dict.fromkeys(warnings))


def _split_group_identity(obj):
    return str(obj.get("mr_split_source_identity", ""))


def _validate_group_translation_only(group):
    rotation = tuple(float(value) for value in group.rotation_euler)
    scale = tuple(float(value) for value in group.scale)
    if _changed(rotation, (0.0, 0.0, 0.0)) or _changed(scale, (1.0, 1.0, 1.0)):
        raise ValueError(f"{group.name} supports translation only; reset group rotation and scale before export")


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

    groups = [
        obj for obj in objects
        if obj.get("mr_course_helper_kind") == "split_checkpoint_group"
    ]
    group_by_identity = {}
    for group in groups:
        identity = _split_group_identity(group)
        if not identity or identity in group_by_identity:
            raise ValueError(f"SplitTime checkpoint group has a missing or duplicate source identity: {group.name}")
        group_by_identity[identity] = group
        _validate_group_translation_only(group)
    if group_by_identity and set(group_by_identity) != set(authorable_splits):
        missing = sorted(set(authorable_splits) - set(group_by_identity))
        extra = sorted(set(group_by_identity) - set(authorable_splits))
        raise ValueError(f"SplitTime checkpoint group inventory changed (missing={missing}, unexpected={extra})")

    for identity, status in authorable_splits.items():
        obj = split_by_identity[identity]
        initial_blender = _json_vector(obj, "mr_initial_blender_position_json")
        world_position = tuple(float(value) for value in obj.matrix_world.translation)
        warnings.extend(_original_transform_warnings(obj, role="split_center"))
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

    companion_status = {item.source_identity: item for item in editor.visual_companion_status}
    companion_by_identity = {}
    for obj in objects:
        if obj.get("mr_course_helper_kind") != "split_visual_companion":
            continue
        identity = obj.get("mr_visual_companion_source_identity")
        if not identity:
            # G0 files saved before G0.1 have a source XML path but lack the
            # stable identity custom property added by this version.
            source_path = obj.get("mr_source_xml_path")
            candidates = [
                item.source_identity for item in editor.visual_companion_status
                if item.source_xml_path == source_path
            ]
            identity = candidates[0] if len(candidates) == 1 else None
        if not identity or identity in companion_by_identity or identity not in companion_status:
            raise ValueError(f"Split visual companion has a missing, duplicate, or stale source identity: {obj.name}")
        companion_by_identity[identity] = obj
    expected_companions = {
        identity for identity, status in companion_status.items() if status.supported
    }
    actual_supported_companions = {
        identity for identity, obj in companion_by_identity.items()
        if obj.get("mr_race_logic_editable")
    }
    if actual_supported_companions != expected_companions:
        missing = sorted(expected_companions - actual_supported_companions)
        extra = sorted(actual_supported_companions - expected_companions)
        raise ValueError(f"Split visual companion helper inventory changed (missing={missing}, unexpected={extra})")

    for identity, obj in companion_by_identity.items():
        status = companion_status[identity]
        initial_raw = obj.get("mr_initial_blender_position_json")
        if initial_raw is not None:
            initial_position = _json_vector(obj, "mr_initial_blender_position_json")
        elif status.position is not None:
            initial_position = position_to_blender(status.position)
        else:
            initial_position = None
        world_position = tuple(float(value) for value in obj.matrix_world.translation)
        if not status.supported or not obj.get("mr_race_logic_editable"):
            if initial_position is not None and _changed(world_position, initial_position):
                raise ValueError(f"{obj.name} is read-only or ambiguous; its position cannot be exported")
            continue
        if initial_position is None:
            raise ValueError(f"{obj.name} is missing its source world-position metadata")
        warnings.extend(_original_transform_warnings(obj, role="split_visual_companion"))
        if _changed(world_position, initial_position):
            editor.set_split_visual_companion_position(
                status.split_identity,
                identity,
                blender_position_to_source(world_position),
            )
    # Several children may have the same ignored editor-only transform. Keep
    # one contextual warning per transform category for the whole export.
    return list(dict.fromkeys(warnings))


class EXPORT_SCENE_OT_master_rallye_race_logic_xml(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.master_rallye_race_logic_xml"
    bl_label = "Export Race Logic XML"
    bl_description = "Export allowlisted StartArea, FinishArea, and SplitTime race-logic fields from the selected project"
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
            if report.warnings:
                self.report(
                    {"WARNING"},
                    f"Exported {len(report.changes)} RaceTest field edits; {len(report.warnings)} warning(s). {report.warnings[0]}",
                )
            else:
                self.report(
                    {"INFO"},
                    f"Exported {len(report.changes)} RaceTest field edits with no warnings: {report.source_sha256[:12]} → {report.exported_sha256[:12]}",
                )
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
