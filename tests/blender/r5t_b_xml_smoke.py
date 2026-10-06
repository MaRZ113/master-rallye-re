"""Headless smoke for semantic Course SDK RaceTest helpers in Blender."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def _descendants(collection):
    yield collection
    for child in collection.children:
        yield from _descendants(child)


def _close3(actual, expected, tolerance=1.0e-4):
    return all(abs(float(actual[index]) - float(expected[index])) <= tolerance for index in range(3))


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 3:
        raise SystemExit("expected course.dx RaceTest.xml output.json after --")
    dx_path, xml_path, output = (Path(value).resolve() for value in args)
    repository = Path(__file__).resolve().parents[2]
    for path in (repository / "src", repository / "blender"):
        sys.path.insert(0, str(path))

    import master_rallye_io
    from master_rallye_io.library import load_course_project, position_to_blender, load_course_race_logic_authoring

    master_rallye_io.register()
    project = load_course_project(xml_path, search_roots=(dx_path.parent,))
    race_logic = project.race_logic
    if race_logic is None:
        raise AssertionError("Course SDK did not create semantic RaceTest model")
    doc = race_logic.source_document
    authoring = load_course_race_logic_authoring(xml_path)
    if not all(item.supported for item in authoring.area_status) or not all(item.supported for item in authoring.split_status):
        raise AssertionError("Retail France1 should expose supported StartArea, FinishArea, and SplitTime authoring fields")
    dx_status = bpy.ops.import_scene.master_rallye_course(
        "EXEC_DEFAULT", filepath=str(dx_path), load_textures=False
    )
    if dx_status != {"FINISHED"}:
        raise AssertionError(f"course DX import failed: {dx_status}")
    xml_status = bpy.ops.import_scene.master_rallye_course_xml_markers(
        "EXEC_DEFAULT", filepath=str(xml_path)
    )
    if xml_status != {"FINISHED"}:
        raise AssertionError(f"RaceTest XML semantic import failed: {xml_status}")

    roots = [
        collection for collection in bpy.data.collections
        if collection.get("mr_resource_kind") == "course"
        and str(collection.get("mr_course_identity", "")).casefold().endswith(dx_path.parent.name.casefold())
    ]
    if len(roots) != 1:
        raise AssertionError(f"expected one matching course root, found {len(roots)}")
    logic_roots = [
        collection for collection in _descendants(roots[0])
        if collection.get("mr_xml_source") == str(xml_path)
        and collection.get("mr_xml_collection_kind") == "race_logic_root"
    ]
    if len(logic_roots) != 1:
        raise AssertionError(f"expected one Race Logic collection, found {len(logic_roots)}")
    logic_root = logic_roots[0]
    descendants = tuple(_descendants(logic_root))
    marker_objects = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
    ]
    expected_markers = [marker for marker in doc.markers if marker.position is not None]
    if len(marker_objects) != len(expected_markers):
        raise AssertionError("marker count differs from hierarchy-aware source XML")

    for semantic_area in (race_logic.start_area, race_logic.finish_area):
        if semantic_area is None:
            continue
        area = next((item for item in descendants if item.get("mr_source_list_name") == semantic_area.source_list_name), None)
        if area is None:
            raise AssertionError(f"{semantic_area.source_list_name} collection is missing")
        area_markers = [obj for obj in area.objects if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"]
        if len(area_markers) != len([item for item in semantic_area.markers if item.position is not None]):
            raise AssertionError(f"{semantic_area.source_list_name} marker count mismatch")
        if len(area_markers) == 4 and not all(obj.get("mr_race_logic_editable") for obj in area_markers):
            raise AssertionError(f"{semantic_area.source_list_name} runtime-confirmed markers are not authorable")
        if sorted(int(obj["mr_marker_index_in_list"]) for obj in area_markers) != list(range(len(area_markers))):
            raise AssertionError(f"{semantic_area.source_list_name} marker order was not preserved")

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
    if len(signs) != len(race_logic.split_times):
        raise AssertionError("split sign count differs from Course SDK semantic split count")
    expected_triggers = [split for split in race_logic.split_times if split.trigger_complete]
    if len(triggers) != len(expected_triggers):
        raise AssertionError("trigger sphere count differs from complete semantic split records")
    expected_companions = [
        item for split in race_logic.split_times for item in split.companions if item.position is not None
    ]
    if len(companions) != len(expected_companions):
        raise AssertionError("visual companion count differs from exact sibling associations")

    trigger_by_id = {int(obj["mr_split_time_id"]): obj for obj in triggers}
    sign_by_id = {int(obj["mr_split_time_id"]): obj for obj in signs}
    for split in expected_triggers:
        trigger = trigger_by_id[split.split_id]
        expected_center = position_to_blender(split.center)
        if not _close3(trigger.matrix_world.translation, expected_center):
            raise AssertionError(f"SplitTime{split.split_id} trigger center conversion differs")
        if abs(float(trigger["mr_split_radius"]) - split.radius) > 1.0e-5:
            raise AssertionError(f"SplitTime{split.split_id} trigger radius differs")
        if trigger.get("mr_trigger_shape") != "sphere" or len(trigger.data.splines) != 3:
            raise AssertionError("split gameplay trigger is not represented by three wire sphere rings")
        if trigger.get("mr_split_extra_time_semantics") != "UNKNOWN":
            raise AssertionError("ExtraTime semantics were overclaimed")
        if not trigger.get("mr_read_only") or not trigger.show_in_front:
            raise AssertionError("split trigger must be a visible read-only helper")
        if not trigger.parent or trigger.parent.get("mr_race_logic_object_type") != "split_center":
            raise AssertionError("trigger sphere is not attached to its editable SplitTime center helper")
        sign = sign_by_id[split.split_id]
        if sign.get("mr_gameplay_center_source") != "same en3d Matrix Row3 as visual sign":
            raise AssertionError("split sign helper does not preserve the confirmed center relation")
        if sign.get("mr_center_rule_evidence") != "; ".join(split.center_rule_evidence):
            raise AssertionError("sign semantic-rule evidence differs from the Course SDK model")
        if not sign.get("mr_race_logic_editable") or sign.get("mr_read_only"):
            raise AssertionError("runtime-confirmed SplitTime sign/center helper is not editable")
        if len(trigger.animation_data.drivers) != 3:
            raise AssertionError("trigger wire sphere Radius is not driven by the editable Radius field")
        if trigger.get("mr_center_rule_evidence") != "; ".join(split.center_rule_evidence):
            raise AssertionError("trigger semantic-rule evidence differs from the Course SDK model")
        if trigger.get("mr_radius_rule_evidence") != "; ".join(split.radius_rule_evidence):
            raise AssertionError("radius semantic-rule evidence differs from the Course SDK model")
        if json.loads(sign.get("mr_record_evidence_json", "[]")) != list(split.record_evidence):
            raise AssertionError("sign record-specific evidence differs from the Course SDK model")
        if json.loads(trigger.get("mr_record_evidence_json", "[]")) != list(split.record_evidence):
            raise AssertionError("trigger record-specific evidence differs from the Course SDK model")
        if "mr_trigger_position_status" in sign or "mr_center_evidence" in trigger:
            raise AssertionError("ambiguous legacy evidence metadata remains")
    if not all(companion.get("mr_is_trigger_center_source") is False for companion in companions):
        raise AssertionError("visual checkpoint companion was marked as a trigger center source")

    if any(item.name in {"Future Collision", "Future Route Data", "Split Sibling Egg Points - UNKNOWN"} for item in descendants):
        raise AssertionError("obsolete placeholder collections remain")

    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "course_dx": dx_path.name,
        "racetest_xml": xml_path.name,
        "marker_count": len(marker_objects),
        "start_area_count": len(race_logic.start_area.markers) if race_logic.start_area else 0,
        "finish_area_count": len(race_logic.finish_area.markers) if race_logic.finish_area else 0,
        "split_visual_count": len(signs),
        "split_trigger_sphere_count": len(triggers),
        "visual_companion_count": len(companions),
        "semantic_model": "master_rallye.course_sdk.CourseRaceLogic",
        "writer_available": True,
        "race_logic_writer": "allowlist-constrained RaceTest XML only",
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
