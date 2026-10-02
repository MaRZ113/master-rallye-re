"""Headless Blender check for RaceTest authoring helpers and safe XML export."""
from __future__ import annotations

import json
import sys
import tempfile
import copy
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

from mathutils import Vector

import bpy


def _descendants(collection):
    yield collection
    for child in collection.children:
        yield from _descendants(child)


def _close3(a, b, epsilon=1.0e-4):
    return all(abs(float(a[index]) - float(b[index])) <= epsilon for index in range(3))


class _LayoutDrawProbe:
    """Run real panel draw callbacks and validate icons against Blender RNA."""

    def __init__(self, valid_icons):
        self.valid_icons = valid_icons
        self.draw_calls = 0

    def box(self):
        self.draw_calls += 1
        return self

    def grid_flow(self, **_kwargs):
        self.draw_calls += 1
        return self

    def label(self, *, text="", icon=None, **_kwargs):
        self.draw_calls += 1
        self._check_icon(icon)

    def operator(self, _operator, *, text="", icon=None, **_kwargs):
        self.draw_calls += 1
        self._check_icon(icon)
        return SimpleNamespace()

    def prop(self, *_args, **_kwargs):
        self.draw_calls += 1

    def _check_icon(self, icon):
        if icon and icon not in self.valid_icons:
            raise AssertionError(f"Panel.draw used unsupported Blender {bpy.app.version_string} icon {icon!r}")


def _draw_panel(panel_type, obj, valid_icons):
    context = SimpleNamespace(object=obj)
    if not panel_type.poll(context):
        raise AssertionError(f"{panel_type.__name__}.poll rejected the smoke context")
    probe = _LayoutDrawProbe(valid_icons)
    panel_type.draw(SimpleNamespace(layout=probe), context)
    if probe.draw_calls == 0:
        raise AssertionError(f"{panel_type.__name__}.draw did not issue UI controls")
    return probe.draw_calls


def _source_egg_map(xml_bytes):
    root = ET.fromstring(xml_bytes)
    result = {}
    for egg in root.iter("Egg"):
        matrix = next(
            (value for value in list(egg) if value.tag == "Value" and value.get("Name") == "en3d Matrix"),
            None,
        )
        if matrix is not None:
            result[egg.get("Name", "")] = matrix.attrib.copy()
    return result


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) not in {2, 3}:
        raise SystemExit("expected RaceTest.xml output.json [addon.zip] after --")
    xml_path, result_path = (Path(value).resolve() for value in args[:2])
    archive = Path(args[2]).resolve() if len(args) == 3 else None
    repository = Path(__file__).resolve().parents[2]
    if archive is not None:
        sys.path.insert(0, str(archive))
    else:
        for path in (repository / "src", repository / "blender"):
            sys.path.insert(0, str(path))

    import master_rallye_io
    from master_rallye_io import ui as addon_ui
    from master_rallye_io.library import (
        blender_position_to_source,
        load_course_project,
        load_course_race_logic_authoring,
        position_to_blender,
    )

    master_rallye_io.register()
    project = load_course_project(xml_path)
    if project.race_logic is None:
        raise AssertionError("Course SDK did not parse the RaceTest XML")
    authoring = load_course_race_logic_authoring(xml_path)
    if not all(item.supported for item in authoring.area_status):
        raise AssertionError("France1 StartArea/FinishArea authoring is not fully supported")
    if not all(item.supported for item in authoring.split_status):
        raise AssertionError("France1 SplitTime authoring is not fully supported")
    if len(authoring.visual_companion_status) != 12 or not all(
        item.supported for item in authoring.visual_companion_status
    ):
        raise AssertionError("France1 visual checkpoint companion Row3 authoring is not fully supported")

    if bpy.ops.import_scene.master_rallye_course_xml_markers("EXEC_DEFAULT", filepath=str(xml_path)) != {"FINISHED"}:
        raise AssertionError("RaceTest authoring helper import failed")
    roots = [
        item for item in bpy.data.collections
        if item.get("mr_xml_collection_kind") == "race_logic_root"
        and item.get("mr_xml_source") == str(xml_path)
    ]
    if len(roots) != 1:
        raise AssertionError(f"expected one source Race Logic collection, found {len(roots)}")
    logic_root = roots[0]
    descendants = tuple(_descendants(logic_root))
    objects = tuple(logic_root.all_objects)
    area_markers = [obj for obj in objects if obj.get("mr_race_logic_object_type") == "area_marker"]
    starts = [obj for obj in area_markers if obj.get("mr_race_logic_area") == "StartArea"]
    finishes = [obj for obj in area_markers if obj.get("mr_race_logic_area") == "FinishArea"]
    split_centers = [
        obj for obj in objects
        if obj.get("mr_race_logic_editable") and obj.get("mr_race_logic_object_type") == "split_center"
    ]
    trigger_spheres = [obj for obj in objects if obj.get("mr_course_helper_kind") == "split_trigger"]
    companions = [obj for obj in objects if obj.get("mr_course_helper_kind") == "split_visual_companion"]
    groups = [obj for obj in objects if obj.get("mr_course_helper_kind") == "split_checkpoint_group"]
    billboards = [obj for obj in objects if obj.get("mr_course_helper_kind") == "diagnostic_marker_billboard"]
    billboard_labels = [obj for obj in objects if obj.get("mr_course_helper_kind") == "diagnostic_marker_billboard_label"]
    direction_rays = [obj for obj in objects if obj.get("mr_course_helper_kind") == "diagnostic_direction_ray"]
    diagnostic_collections = [
        item for item in descendants
        if item.get("mr_xml_collection_kind") == "split_companion_diagnostics"
    ]
    if len(starts) != 4 or len(finishes) != 4:
        raise AssertionError("Race Logic collection must have four editable markers for each area")
    if len(split_centers) != len(authoring.split_status) or len(trigger_spheres) != len(split_centers):
        raise AssertionError("Race Logic collection must have one center and trigger sphere per SplitTime")
    if len(companions) != 12 or len(groups) != len(split_centers):
        raise AssertionError("each France1 split needs one group and its four visual companions")
    if len(billboards) != len(companions) or len(direction_rays) != len(companions):
        raise AssertionError("each visual companion needs its own billboard and direction ray")
    if len(billboard_labels) != len(companions) or len(diagnostic_collections) != len(split_centers):
        raise AssertionError("every companion needs a labeled preview in its split diagnostics collection")
    if any(not obj.get("mr_editor_only") or obj.get("mr_race_logic_object_type") for obj in (
        *billboards, *billboard_labels, *direction_rays, *trigger_spheres,
    )):
        raise AssertionError("diagnostic sign/ray/radius helpers must be explicitly excluded from writer semantics")
    if any(not obj.get("mr_race_logic_editable") for obj in companions):
        raise AssertionError("identified visual checkpoint Egg Row3 positions should be allowlisted")
    if any(obj.get("mr_role") != "split_visual_companion" or not obj.get("mr_source_xml_identity") for obj in companions):
        raise AssertionError("visual companion source identity metadata is incomplete")

    center_by_identity = {obj["mr_split_source_identity"]: obj for obj in split_centers}
    group_by_identity = {obj["mr_split_source_identity"]: obj for obj in groups}
    trigger_by_parent = {obj.parent.name: obj for obj in trigger_spheres}
    companion_by_identity = {obj["mr_visual_companion_source_identity"]: obj for obj in companions}
    billboard_by_companion = {obj.parent["mr_visual_companion_source_identity"]: obj for obj in billboards}
    ray_by_companion = {obj.parent["mr_visual_companion_source_identity"]: obj for obj in direction_rays}
    label_by_companion = {obj.parent.parent["mr_visual_companion_source_identity"]: obj for obj in billboard_labels}
    for status in authoring.split_status:
        center = center_by_identity[status.identity]
        group = group_by_identity[status.identity]
        trigger = trigger_by_parent.get(center.name)
        if trigger is None:
            raise AssertionError(f"{center.name} has no attached trigger sphere")
        if center.type != "EMPTY" or not all(center.lock_rotation):
            raise AssertionError("SplitTime center must remain a simple, non-rotating trigger helper")
        if not _close3(center.location, position_to_blender(status.center)):
            raise AssertionError("SplitTime center helper does not use the canonical coordinate transform")
        bpy.context.view_layer.update()
        if any(abs(float(value) - status.radius) > 1.0e-3 for value in trigger.scale):
            raise AssertionError("trigger radius display does not follow the editable Radius value")
        if len(trigger.data.splines) != 3 or len(trigger.animation_data.drivers) != 3:
            raise AssertionError("trigger radius must be an actual 3D unit sphere driven by Radius")
        if center.get("mr_extra_time_semantics") != "UNKNOWN":
            raise AssertionError("ExtraTime semantics were overclaimed")
        if center.parent != group or any(companion.parent != group for companion in companions if companion.get("mr_split_source_identity") == status.identity):
            raise AssertionError("checkpoint group must parent its trigger center and visual companions")
    if len(companion_by_identity) != len(companions):
        raise AssertionError("visual companion source identities must be unique")
    source_companions = {
        (companion.source_egg.xml_path, companion.source_egg.name): companion
        for split in project.race_logic.split_times
        for companion in split.companions
    }
    if len(billboard_by_companion) != len(companions) or len(ray_by_companion) != len(companions) or len(label_by_companion) != len(companions):
        raise AssertionError("companion diagnostic helpers must preserve one-to-one companion identity")
    if any(obj.parent in split_centers for obj in billboards):
        raise AssertionError("no large SplitTime billboard may be attached to a gameplay trigger center")
    for identity, helper in companion_by_identity.items():
        source_companion = source_companions.get((helper["mr_xml_path"], helper["mr_source_egg"]))
        if source_companion is None:
            raise AssertionError(f"could not bind {helper.name} to its own source Egg matrix")
        billboard = billboard_by_companion.get(identity)
        ray = ray_by_companion.get(identity)
        label = label_by_companion.get(identity)
        if billboard is None or ray is None or label is None:
            raise AssertionError(f"{helper.name} has no companion-attached billboard/ray")
        if billboard.parent != helper or ray.parent != helper or label.parent != billboard:
            raise AssertionError("companion previews must be parented to that exact visual companion")
        if helper.get("mr_model_name") != source_companion.source_egg.model_name:
            raise AssertionError("visual companion model identity was not preserved")
        if billboard.type != "MESH" or label.type != "FONT" or label.data.body != helper.get("mr_source_egg"):
            raise AssertionError("companion billboard must identify its source Egg, not the main split trigger")
        if billboard.get("mr_billboard_style") != "procedural companion diagnostic fallback; no game texture/model":
            raise AssertionError("companion fallback must be explicitly marked as a non-game visual")
        if ray.get("mr_direction_basis") != "this companion en3d Matrix local +Z (Row2)":
            raise AssertionError("companion ray must identify its own Matrix Row2 basis")
        if not all(helper.lock_rotation) or helper.get("mr_orientation_export_policy") != "rotation is preserved from source and not authored":
            raise AssertionError("companion orientation must be presented as read-only")
        matrix = source_companion.source_egg.matrix("en3d Matrix")
        expected_row2 = Vector(position_to_blender(matrix.row(2)[:3])).normalized()
        actual_ray = (
            ray.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
        ).normalized()
        if (actual_ray - expected_row2).length > 1.0e-3:
            raise AssertionError("companion direction ray does not follow its own Matrix Row2")
        panel_normal = (billboard.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
        if (panel_normal - actual_ray).length > 1.0e-3:
            raise AssertionError("companion billboard normal and direction ray disagree")

    valid_icons = {
        item.identifier
        for item in bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
    }
    course_mesh = bpy.data.meshes.new("G0.1 panel draw smoke mesh")
    course_mesh.from_pydata(((0, 0, 0), (1, 0, 0), (0, 1, 0)), [], ((0, 1, 2),))
    course_obj = bpy.data.objects.new("G0.1 panel draw course", course_mesh)
    bpy.context.scene.collection.objects.link(course_obj)
    course_obj["mr_resource_kind"] = "course"
    course_obj["mr_course_identity"] = "France1"
    course_obj["mr_metadata_json"] = json.dumps({"course": {}, "draws": [], "blender": {}})
    course_draw_calls = _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course, course_obj, valid_icons)
    race_draw_calls = _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course_race_logic, starts[0], valid_icons)
    split_draw_calls = _draw_panel(
        addon_ui.VIEW3D_PT_master_rallye_course_race_logic, split_centers[0], valid_icons
    )
    group_draw_calls = _draw_panel(
        addon_ui.VIEW3D_PT_master_rallye_course_race_logic, groups[0], valid_icons
    )
    companion_draw_calls = _draw_panel(
        addon_ui.VIEW3D_PT_master_rallye_course_race_logic, companions[0], valid_icons
    )
    if len([item for item in descendants if item.get("mr_xml_collection_kind") == "marker_lists_root"]) != 1:
        raise AssertionError("unknown MarkerLists hierarchy was not retained")

    active = starts[0]
    bpy.context.view_layer.objects.active = active
    active.select_set(True)
    temp_parent = result_path.parent
    temp_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="g0-race-logic-", dir=temp_parent) as temporary:
        temp = Path(temporary)
        no_op_path = temp / "France1_noop.xml"
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(no_op_path)) != {"FINISHED"}:
            raise AssertionError("zero-edit Blender RaceTest export failed")
        if no_op_path.read_bytes() != xml_path.read_bytes():
            raise AssertionError("zero-edit Blender RaceTest output is not byte-identical")

        # Companion diagnostic transforms are explicitly outside the RaceTest writer.
        diagnostic_helpers = (*billboards, *billboard_labels, *direction_rays)
        diagnostic_transforms = {obj: obj.location.copy() for obj in diagnostic_helpers}
        billboards[0].location.x += 0.4
        direction_rays[0].location.y += 0.25
        diagnostic_path = temp / "France1_diagnostic_only.xml"
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(diagnostic_path)) != {"FINISHED"}:
            raise AssertionError("editor-only diagnostic helper export failed")
        diagnostic_manifest = json.loads(Path(str(diagnostic_path) + ".mr-race-edit.json").read_text(encoding="utf-8"))
        if diagnostic_path.read_bytes() != xml_path.read_bytes() or diagnostic_manifest["changes"] or diagnostic_manifest["warnings"]:
            raise AssertionError("diagnostic helper transforms must not affect RaceTest XML or manifest semantics")
        for obj, location in diagnostic_transforms.items():
            obj.location = location
        bpy.context.view_layer.update()

        start_original = {obj: obj.location.copy() for obj in starts}
        finish_original = {obj: obj.location.copy() for obj in finishes}
        for obj in starts:
            obj.location.x += 3.0
        finish_center = sum((obj.location.copy() for obj in finishes), Vector()) / len(finishes)
        for obj in finishes:
            obj.location = finish_center + 1.5 * (obj.location - finish_center)
            obj.scale = (1.5, 1.5, 1.5)
        bpy.context.view_layer.update()

        area_path = temp / "France1_area_points.xml"
        bpy.context.view_layer.objects.active = starts[0]
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(area_path)) != {"FINISHED"}:
            raise AssertionError("StartArea/FinishArea point export failed")
        area_manifest = json.loads(Path(str(area_path) + ".mr-race-edit.json").read_text(encoding="utf-8"))
        area_roles = [item["semantic_role"] for item in area_manifest["changes"]]
        if area_roles.count("race.start.marker_position") != 4 or area_roles.count("race.finish.marker_position") != 4:
            raise AssertionError("area export manifest must distinguish four StartArea and four FinishArea points")
        if any("scale" in warning.casefold() for warning in area_manifest["warnings"]):
            raise AssertionError("point-marker scale must not produce a misleading RaceTest export warning")
        for obj, location in start_original.items():
            obj.location = location
        for obj, location in finish_original.items():
            obj.location = location
            obj.scale = (1.0, 1.0, 1.0)
        bpy.context.view_layer.update()

        split = next(item for item in authoring.split_status if item.split_id == 0)
        center = center_by_identity[split.identity]
        group = group_by_identity[split.identity]
        matching_companions = [obj for obj in companions if obj.get("mr_split_source_identity") == split.identity]
        if len(matching_companions) != 4:
            raise AssertionError("SplitTime0 must have four source-identified visual companions")
        center_world = center.matrix_world.translation.copy()
        companion_world = {obj: obj.matrix_world.translation.copy() for obj in matching_companions}
        group_location = group.location.copy()
        group_delta = Vector((5.0, -2.0, 3.0))
        group.location += group_delta
        bpy.context.view_layer.update()
        trigger = trigger_by_parent[center.name]
        if not _close3(center.matrix_world.translation, center_world + group_delta):
            raise AssertionError("whole checkpoint translation did not move the trigger center by one world delta")
        if any(not _close3(obj.matrix_world.translation, companion_world[obj] + group_delta) for obj in matching_companions):
            raise AssertionError("whole checkpoint translation did not move all visual companions by the same delta")
        if abs(float(trigger.scale.x) - float(center["mr_split_radius"])) > 1.0e-3:
            raise AssertionError("checkpoint translation changed or obscured the explicit gameplay Radius")

        edited_path = temp / "France1_split_group.xml"
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(edited_path)) != {"FINISHED"}:
            raise AssertionError("whole SplitTime checkpoint export failed")
        manifest_path = Path(str(edited_path) + ".mr-race-edit.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        role_counts = {role: sum(item["semantic_role"] == role for item in manifest["changes"]) for role in (
            "race.split.trigger_center", "race.split.visual_companion_position", "race.split.radius", "race.split.id",
        )}
        if role_counts != {
            "race.split.trigger_center": 1,
            "race.split.visual_companion_position": 4,
            "race.split.radius": 0,
            "race.split.id": 0,
        } or not manifest["unknown_content_preserved"]:
            raise AssertionError("group move manifest must include one center and four visual positions only")
        if not any("SplitTime" in status.egg_name for status in authoring.visual_companion_status):
            raise AssertionError("split visual companion source inventory is unexpectedly empty")
        if manifest["source_xml_sha256"] != authoring.source_sha256:
            raise AssertionError("Race Logic sidecar source hash differs from imported source")

        exported = load_course_race_logic_authoring(edited_path)
        output_split = next(item for item in exported.split_status if item.split_id == split.split_id)
        expected_center = blender_position_to_source(center.matrix_world.translation)
        if not _close3(output_split.center, expected_center) or abs(output_split.radius - split.radius) > 1.0e-5:
            raise AssertionError("whole checkpoint translation did not preserve center/Radius semantics")
        output_companions = {item.source_identity: item for item in exported.visual_companion_status}
        for obj in matching_companions:
            identity = obj["mr_visual_companion_source_identity"]
            if not _close3(output_companions[identity].position, blender_position_to_source(obj.matrix_world.translation)):
                raise AssertionError("visual companion world position did not round-trip")
        source_tree = load_course_race_logic_authoring(xml_path)
        source_split0 = next(item for item in source_tree.split_status if item.split_id == 0)
        output_split0 = next(item for item in exported.split_status if item.split_id == 0)
        if source_split0.extra_time_raw != output_split0.extra_time_raw or source_split0.split_id != output_split0.split_id:
            raise AssertionError("SplitTime ID or ExtraTime changed during whole-checkpoint translation")
        source_matrices = _source_egg_map(xml_path.read_bytes())
        group_matrices = _source_egg_map(edited_path.read_bytes())
        for name in ("SplitTime0", *(obj["mr_source_egg"] for obj in matching_companions)):
            for row in ("Row0", "Row1", "Row2"):
                if source_matrices[name].get(row) != group_matrices[name].get(row):
                    raise AssertionError(f"whole checkpoint edit changed protected {name} {row}")
            if source_matrices[name]["Row3"].split()[3] != group_matrices[name]["Row3"].split()[3]:
                raise AssertionError(f"whole checkpoint edit changed protected {name} Row3 W")

        group.location = group_location
        bpy.context.view_layer.update()
        independently_moved = matching_companions[0]
        companion_start = independently_moved.matrix_world.translation.copy()
        center_start = center.matrix_world.translation.copy()
        independently_moved.location += Vector((0.0, 2.0, 0.0))
        bpy.context.view_layer.update()
        if not _close3(center.matrix_world.translation, center_start):
            raise AssertionError("moving one visual companion also moved the gameplay trigger center")
        companion_path = temp / "France1_single_visual_companion.xml"
        bpy.context.view_layer.objects.active = independently_moved
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(companion_path)) != {"FINISHED"}:
            raise AssertionError("independent visual companion export failed")
        companion_manifest = json.loads(Path(str(companion_path) + ".mr-race-edit.json").read_text(encoding="utf-8"))
        if len(companion_manifest["changes"]) != 1 or companion_manifest["changes"][0]["semantic_role"] != "race.split.visual_companion_position":
            raise AssertionError("individual visual companion edit must change only its Row3 XYZ")
        companion_export = load_course_race_logic_authoring(companion_path)
        comp_status = {item.source_identity: item for item in companion_export.visual_companion_status}
        if not _close3(comp_status[independently_moved["mr_visual_companion_source_identity"]].position,
                       blender_position_to_source(independently_moved.matrix_world.translation)):
            raise AssertionError("independent visual companion world position did not round-trip")
        if not _close3(next(item for item in companion_export.split_status if item.split_id == 0).center,
                       blender_position_to_source(center_start)):
            raise AssertionError("individual visual companion edit changed SplitTime trigger center")

        independently_moved.location -= Vector((0.0, 2.0, 0.0))
        bpy.context.view_layer.update()
        companion_transforms = {
            obj: (obj.rotation_euler.copy(), obj.scale.copy())
            for obj in matching_companions[:2]
        }
        for obj in companion_transforms:
            obj.rotation_euler.z += 0.1
            obj.scale *= 1.1
        bpy.context.view_layer.update()
        companion_transform_path = temp / "France1_visual_companion_transform_warning.xml"
        bpy.context.view_layer.objects.active = matching_companions[0]
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(companion_transform_path)) != {"FINISHED"}:
            raise AssertionError("visual companion transform-safety export failed")
        companion_transform_manifest = json.loads(
            Path(str(companion_transform_path) + ".mr-race-edit.json").read_text(encoding="utf-8")
        )
        companion_transform_warnings = companion_transform_manifest["warnings"]
        if len(companion_transform_warnings) != 1 or "visual companion rotation/scale" not in companion_transform_warnings[0]:
            raise AssertionError("multiple companion transforms must produce one contextual warning")
        if companion_transform_manifest["changes"]:
            raise AssertionError("unsupported companion rotation/scale must not change RaceTest XML")
        for obj, (rotation, scale) in companion_transforms.items():
            obj.rotation_euler = rotation
            obj.scale = scale
        bpy.context.view_layer.update()

        center.scale = (1.25, 1.25, 1.25)
        bpy.context.view_layer.update()
        scale_path = temp / "France1_split_scale_warning.xml"
        bpy.context.view_layer.objects.active = center
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(scale_path)) != {"FINISHED"}:
            raise AssertionError("SplitTime object-scale safety export failed")
        scale_manifest = json.loads(Path(str(scale_path) + ".mr-race-edit.json").read_text(encoding="utf-8"))
        if not any("object scale does not change gameplay Radius" in item for item in scale_manifest["warnings"]):
            raise AssertionError("SplitTime object scale must produce the explicit Radius safety warning")
        center.scale = (1.0, 1.0, 1.0)
        bpy.context.view_layer.update()
        _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course, course_obj, valid_icons)
        _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course_race_logic, center, valid_icons)

        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))
        synthetic_root = ET.fromstring(xml_path.read_bytes(), parser=parser)
        marker_lists = synthetic_root.find("MarkerLists")
        finish_list = next(
            item for item in marker_lists.findall("List")
            if item.get("Name") == "FinishArea"
        )
        finish_markers = finish_list.findall("Marker")
        finish_list.append(copy.deepcopy(finish_markers[0]))
        unsupported_xml = temp / "France1_five_marker.xml"
        ET.ElementTree(synthetic_root).write(unsupported_xml, encoding="utf-8", xml_declaration=True)
        if bpy.ops.import_scene.master_rallye_course_xml_markers("EXEC_DEFAULT", filepath=str(unsupported_xml)) != {"FINISHED"}:
            raise AssertionError("synthetic unsupported-area helper import failed")
        unsupported_root = next(
            item for item in bpy.data.collections
            if item.get("mr_xml_collection_kind") == "race_logic_root"
            and item.get("mr_xml_source") == str(unsupported_xml)
        )
        unsupported_finish = [
            obj for obj in unsupported_root.all_objects
            if obj.get("mr_race_logic_object_type") == "area_marker"
            and obj.get("mr_race_logic_area") == "FinishArea"
        ]
        if len(unsupported_finish) != 5 or any(obj.get("mr_race_logic_editable") for obj in unsupported_finish):
            raise AssertionError("five-marker FinishArea was not safely exposed read-only")

    result_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "addon_source": archive.name if archive else "workspace source",
        "racetest_xml": xml_path.name,
        "start_area_helpers": len(starts),
        "finish_area_helpers": len(finishes),
        "split_center_helpers": len(split_centers),
        "radius_spheres": len(trigger_spheres),
        "main_center_billboards": sum(obj.parent in split_centers for obj in billboards),
        "companion_billboards": len(billboards),
        "companion_billboard_labels": len(billboard_labels),
        "companion_direction_rays": len(direction_rays),
        "visual_checkpoint_helpers": len(companions),
        "split_checkpoint_groups": len(groups),
        "noop_export_byte_identical": True,
        "area_point_scale_warning_suppressed": True,
        "whole_split_checkpoint_translation": True,
        "independent_visual_companion_translation": True,
        "companion_rays_follow_own_imported_matrix_row2": True,
        "companion_billboards_follow_own_imported_matrix": True,
        "diagnostic_helpers_excluded_from_export": True,
        "companion_orientation_is_read_only": True,
        "split_scale_radius_warning": True,
        "panel_draw_callbacks": {
            "master_rallye_course": course_draw_calls,
            "race_logic_area_marker": race_draw_calls,
            "race_logic_split_trigger": split_draw_calls,
            "race_logic_split_group": group_draw_calls,
            "race_logic_visual_companion": companion_draw_calls,
            "valid_icons_checked_against_blender_rna": True,
        },
        "area_point_change_fields": 8,
        "whole_group_change_fields": 5,
        "single_visual_companion_change_fields": 1,
        "writer_scope": "RaceTest XML only",
        "runtime_test_claimed": False,
    }
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
