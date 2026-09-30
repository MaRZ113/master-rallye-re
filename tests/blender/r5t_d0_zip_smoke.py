"""Verify semantic race helpers using only the packaged add-on ZIP."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def _descendants(collection):
    yield collection
    for child in collection.children:
        yield from _descendants(child)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 4:
        raise SystemExit("expected addon.zip course.dx RaceTest.xml output.json after --")
    archive, dx_path, xml_path, output = (Path(value).resolve() for value in args)
    sys.path.insert(0, str(archive))
    import master_rallye_io
    from master_rallye_io.library import load_course_project, position_to_blender

    master_rallye_io.register()
    project = load_course_project(xml_path, search_roots=(dx_path.parent,))
    race_logic = project.race_logic
    if race_logic is None:
        raise AssertionError("packaged Course SDK did not parse the RaceTest XML")
    if bpy.ops.import_scene.master_rallye_course(
        "EXEC_DEFAULT", filepath=str(dx_path), load_textures=False
    ) != {"FINISHED"}:
        raise AssertionError("packaged course DX import failed")
    if bpy.ops.import_scene.master_rallye_course_xml_markers(
        "EXEC_DEFAULT", filepath=str(xml_path)
    ) != {"FINISHED"}:
        raise AssertionError("packaged RaceTest import failed")

    roots = [
        item for item in bpy.data.collections
        if item.get("mr_resource_kind") == "course"
        and str(item.get("mr_course_identity", "")).casefold().endswith(dx_path.parent.name.casefold())
    ]
    if len(roots) != 1:
        raise AssertionError(f"packaged course root count is {len(roots)}")
    logic_roots = [
        item for item in _descendants(roots[0])
        if item.get("mr_xml_source") == str(xml_path)
        and item.get("mr_xml_collection_kind") == "race_logic_root"
    ]
    if len(logic_roots) != 1:
        raise AssertionError("packaged Race Logic hierarchy is missing")
    descendants = tuple(_descendants(logic_roots[0]))
    markers = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
    ]
    signs = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest split-time visual sign icon"
    ]
    triggers = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "split_trigger"
    ]
    companions = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "split_visual_companion"
    ]
    if len(markers) != sum(marker.position is not None for marker in race_logic.source_document.markers):
        raise AssertionError("packaged marker inventory differs from source XML")
    if len(signs) != len(race_logic.split_times):
        raise AssertionError("packaged sign count differs from semantic split count")
    complete_splits = [split for split in race_logic.split_times if split.trigger_complete]
    if len(triggers) != len(complete_splits):
        raise AssertionError("packaged trigger count differs from complete semantic split count")
    expected_companions = sum(
        companion.position is not None
        for split in race_logic.split_times for companion in split.companions
    )
    if len(companions) != expected_companions:
        raise AssertionError("packaged visual companion count differs from semantic association")

    trigger_by_id = {int(item["mr_split_time_id"]): item for item in triggers}
    for split in complete_splits:
        item = trigger_by_id[split.split_id]
        expected = position_to_blender(split.center)
        if any(abs(float(item.location[i]) - expected[i]) > 1.0e-4 for i in range(3)):
            raise AssertionError("packaged trigger center transform differs from canonical conversion")
        if abs(float(item["mr_split_radius"]) - split.radius) > 1.0e-5:
            raise AssertionError("packaged trigger radius differs from the semantic model")
        if item.get("mr_trigger_shape") != "sphere" or len(item.data.splines) != 3:
            raise AssertionError("packaged trigger is not a three-ring sphere")
        if item.get("mr_split_extra_time_semantics") != "UNKNOWN":
            raise AssertionError("packaged ExtraTime semantics were overclaimed")
    if any(item.get("mr_is_trigger_center_source") is not False for item in companions):
        raise AssertionError("packaged visual companion was marked as a trigger source")
    if not any(item.get("mr_source_list_name") == "StartArea" for item in descendants):
        raise AssertionError("packaged StartArea hierarchy is missing")
    if race_logic.finish_area and not any(item.get("mr_source_list_name") == "FinishArea" for item in descendants):
        raise AssertionError("packaged FinishArea hierarchy is missing")
    if any(item.name in {"Future Collision", "Future Route Data", "Split Sibling Egg Points - UNKNOWN"} for item in descendants):
        raise AssertionError("packaged addon retains obsolete unknown placeholder collections")

    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "archive": archive.name,
        "course_dx": dx_path.name,
        "racetest_xml": xml_path.name,
        "marker_count": len(markers),
        "split_visual_count": len(signs),
        "split_trigger_sphere_count": len(triggers),
        "visual_companion_count": len(companions),
        "semantic_model": "master_rallye.course_sdk.CourseRaceLogic",
        "user_profile_modified": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
