"""Headless Blender check for RaceTest authoring helpers and safe XML export."""
from __future__ import annotations

import json
import sys
import tempfile
import copy
import xml.etree.ElementTree as ET
from pathlib import Path

import bpy


def _descendants(collection):
    yield collection
    for child in collection.children:
        yield from _descendants(child)


def _close3(a, b, epsilon=1.0e-4):
    return all(abs(float(a[index]) - float(b[index])) <= epsilon for index in range(3))


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
    if len(starts) != 4 or len(finishes) != 4:
        raise AssertionError("Race Logic collection must have four editable markers for each area")
    if len(split_centers) != len(authoring.split_status) or len(trigger_spheres) != len(split_centers):
        raise AssertionError("Race Logic collection must have one center and trigger sphere per SplitTime")
    if any(not obj.get("mr_read_only") for obj in companions):
        raise AssertionError("visual checkpoint Eggs must remain read-only and separate")

    center_by_identity = {obj["mr_split_source_identity"]: obj for obj in split_centers}
    trigger_by_parent = {obj.parent.name: obj for obj in trigger_spheres}
    for status in authoring.split_status:
        center = center_by_identity[status.identity]
        trigger = trigger_by_parent.get(center.name)
        if trigger is None:
            raise AssertionError(f"{center.name} has no attached trigger sphere")
        if not _close3(center.location, position_to_blender(status.center)):
            raise AssertionError("SplitTime center helper does not use the canonical coordinate transform")
        bpy.context.view_layer.update()
        if any(abs(float(value) - status.radius) > 1.0e-3 for value in trigger.scale):
            raise AssertionError("trigger radius display does not follow the editable Radius value")
        if len(trigger.data.splines) != 3 or len(trigger.animation_data.drivers) != 3:
            raise AssertionError("trigger radius must be an actual 3D unit sphere driven by Radius")
        if center.get("mr_extra_time_semantics") != "UNKNOWN":
            raise AssertionError("ExtraTime semantics were overclaimed")
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

        starts[0].location.x += 3.0
        finishes[0].location.z += 2.0
        split = next(item for item in authoring.split_status if item.split_id == 0)
        center = center_by_identity[split.identity]
        center.location.x += 15.0
        center["mr_split_radius"] = float(split.radius) + 5.0
        center["mr_split_time_id"] = int(split.split_id) + 10
        bpy.context.view_layer.update()
        trigger = trigger_by_parent[center.name]
        if abs(float(trigger.scale.x) - float(center["mr_split_radius"])) > 1.0e-3:
            raise AssertionError("radius custom property did not update the Blender trigger visualization")

        edited_path = temp / "France1_g0_edited.xml"
        if bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(edited_path)) != {"FINISHED"}:
            raise AssertionError("Blender RaceTest authoring export failed")
        manifest_path = Path(str(edited_path) + ".mr-race-edit.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if len(manifest["changes"]) != 5 or not manifest["unknown_content_preserved"]:
            raise AssertionError("Race Logic export manifest has unexpected change count or preservation status")
        if manifest["source_xml_sha256"] != authoring.source_sha256:
            raise AssertionError("Race Logic sidecar source hash differs from imported source")

        exported = load_course_race_logic_authoring(edited_path)
        if not _close3(exported.area_status[0].positions[0], blender_position_to_source(starts[0].matrix_world.translation)):
            raise AssertionError("Blender StartArea world position was not converted back to runtime coordinates")
        output_split = next(item for item in exported.split_status if item.split_id == 10)
        expected_center = blender_position_to_source(center.matrix_world.translation)
        if not _close3(output_split.center, expected_center) or abs(output_split.radius - center["mr_split_radius"]) > 1.0e-5:
            raise AssertionError("Blender SplitTime center/Radius did not round-trip through the XML writer")
        source_tree = load_course_race_logic_authoring(xml_path)
        source_split0 = next(item for item in source_tree.split_status if item.split_id == 0)
        source_split10 = next(item for item in exported.split_status if item.split_id == 10)
        if source_split0.extra_time_raw != source_split10.extra_time_raw:
            raise AssertionError("SplitTime ExtraTime was changed by Blender authoring")

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
        unsupported_finish[0].location.x += 1.0
        bpy.context.view_layer.objects.active = unsupported_finish[0]
        unsupported_finish[0].select_set(True)
        refused_output = temp / "unsupported_area_must_not_export.xml"
        try:
            result = bpy.ops.export_scene.master_rallye_race_logic_xml("EXEC_DEFAULT", filepath=str(refused_output))
        except RuntimeError as error:
            if "is read-only or ambiguous" not in str(error):
                raise
            result = {"CANCELLED"}
        if result != {"CANCELLED"} or refused_output.exists():
            raise AssertionError("moved unsupported FinishArea helper was not refused")

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
        "visual_checkpoint_helpers": len(companions),
        "noop_export_byte_identical": True,
        "changed_allowlisted_fields": 5,
        "writer_scope": "RaceTest XML only",
        "runtime_test_claimed": False,
    }
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
