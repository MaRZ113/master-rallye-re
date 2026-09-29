"""Headless smoke test for hierarchy-aware RaceTest XML helpers.

Run with Blender, passing a course DX, its RaceTest XML, and an output JSON
path after the ``--`` separator. Output contains derived validation metadata.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 3:
        raise SystemExit("expected course.dx RaceTest.xml output.json after --")
    dx_path, xml_path, output = (Path(value).resolve() for value in args)
    repository = Path(__file__).resolve().parents[2]
    for path in (repository / "src", repository / "blender"):
        sys.path.insert(0, str(path))

    import master_rallye_io
    from master_rallye_io.library import parse_course_xml, position_to_blender

    master_rallye_io.register()
    dx_status = bpy.ops.import_scene.master_rallye_course(
        "EXEC_DEFAULT", filepath=str(dx_path), load_textures=False
    )
    if dx_status != {"FINISHED"}:
        raise AssertionError(f"course DX import failed: {dx_status}")
    doc = parse_course_xml(xml_path)
    expected = [marker for marker in doc.markers if marker.position is not None]
    xml_status = bpy.ops.import_scene.master_rallye_course_xml_markers(
        "EXEC_DEFAULT", filepath=str(xml_path)
    )
    if xml_status != {"FINISHED"}:
        raise AssertionError(f"RaceTest XML marker import failed: {xml_status}")

    roots = [
        collection for collection in bpy.data.collections
        if collection.get("mr_resource_kind") == "course"
        and str(collection.get("mr_course_identity", "")).casefold().endswith(dx_path.parent.name.casefold())
    ]
    if not roots:
        roots = [
            collection for collection in bpy.data.collections
            if collection.get("mr_resource_kind") == "course"
            and str(collection.get("mr_course_identity", "")).casefold().endswith(xml_path.stem.casefold())
        ]
    if len(roots) != 1:
        raise AssertionError(f"expected one matching course root, found {len(roots)}")
    root = roots[0]
    overlays = [
        collection for collection in bpy.data.collections
        if collection.get("mr_xml_source") == str(xml_path)
        and collection.get("mr_xml_collection_kind") == "race_logic_root"
    ]
    if len(overlays) != 1:
        raise AssertionError(f"expected one RaceTest race-logic root, found {len(overlays)}")
    logic = overlays[0]
    descendants = []
    def walk(collection):
        descendants.append(collection)
        for child in collection.children:
            walk(child)
    walk(logic)
    marker_objects = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
    ]
    if len(marker_objects) != len(expected):
        raise AssertionError(f"marker count {len(marker_objects)} differs from parsed XML {len(expected)}")
    first = expected[0]
    first_object = next(obj for obj in marker_objects if obj.get("mr_marker_ordinal") == first.ordinal)
    expected_location = position_to_blender(first.position)
    actual_location = tuple(float(first_object.location[i]) for i in range(3))
    if any(abs(actual_location[i] - expected_location[i]) > 1.0e-4 for i in range(3)):
        raise AssertionError(
            f"first XML marker location {actual_location} differs from converted {expected_location}"
        )
    if tuple(first_object["mr_source_position_xyz"]) != first.position:
        raise AssertionError("source XML marker coordinates were not preserved")
    start_list = doc.marker_list("StartArea")
    finish_list = doc.marker_list("FinishArea")
    start_collection = next((item for item in descendants if item.get("mr_source_list_name") == "StartArea"), None)
    finish_collection = next((item for item in descendants if item.get("mr_source_list_name") == "FinishArea"), None)
    if start_list is None or start_collection is None or sum(
        1 for obj in start_collection.objects if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
    ) != len(start_list.markers):
        raise AssertionError("StartArea marker hierarchy/helper count mismatch")
    if finish_list is None or finish_collection is None or sum(
        1 for obj in finish_collection.objects if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
    ) != len(finish_list.markers):
        raise AssertionError("FinishArea marker hierarchy/helper count mismatch")
    for area_collection, expected_order in ((start_collection, list(range(4))), (finish_collection, list(range(4)))):
        outlines = [obj for obj in area_collection.objects if obj.type == "CURVE"]
        if len(outlines) != 1 or list(outlines[0].get("mr_source_marker_order", [])) != expected_order:
            raise AssertionError("area source-order outline is missing or reordered")
        if outlines[0].get("mr_filled_area_created") is not False:
            raise AssertionError("area helper should remain an outline without a speculative fill")
    split_visuals = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest split-time visual sign icon"
    ]
    if len(split_visuals) != len(doc.split_time_eggs):
        raise AssertionError("split visual helper count differs from split Egg count")
    if any(obj.get("mr_trigger_position_status") != "UNKNOWN; deliberately not visualized" for obj in split_visuals):
        raise AssertionError("split trigger position must stay independent and unknown")
    if any(obj.get("mr_split_visual_position_xyz") is None for obj in split_visuals):
        raise AssertionError("split visual position metadata was not preserved")
    for sign in split_visuals:
        metadata = json.loads(sign["mr_source_egg_metadata_json"])
        if not any(value["name"] == "en3d Matrix" for value in metadata["egg_values"]):
            raise AssertionError("raw split Egg matrix value metadata was not preserved")
        if not any(
            component["tag"] == "gaRaceSplitTimeAI"
            and any(value["name"] == "Radius" for value in component["values"])
            for ai in metadata["ai_objects"] for component in ai["components"]
        ):
            raise AssertionError("raw split AI component values were not preserved")
    if any(obj.get("mr_course_helper_kind") == "RaceTest split-time gameplay trigger" for obj in split_visuals):
        raise AssertionError("no gameplay trigger helper may be emitted while its position is unknown")
    candidate_collection = next(
        (item for item in descendants if item.get("mr_xml_collection_kind") == "split_sibling_candidates"),
        None,
    )
    expected_candidate_count = sum(
        1 for egg in doc.eggs
        if egg.name and any(egg.name.startswith(f"SplitTime{split.split_time_component.value('Split Time ID').value}-")
                            for split in doc.split_time_eggs if split.split_time_component
                            and split.split_time_component.value("Split Time ID"))
        and egg.matrix("en3d Matrix") is not None and egg.matrix("en3d Matrix").position is not None
    )
    if candidate_collection is None or len(candidate_collection.objects) != expected_candidate_count:
        raise AssertionError("split sibling candidate point set does not match source XML")
    if any(obj.get("mr_semantics_status", "").startswith("UNKNOWN") is False for obj in candidate_collection.objects):
        raise AssertionError("split sibling points must remain explicitly unknown candidates")

    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "course_dx": dx_path.name,
        "racetest_xml": xml_path.name,
        "root_collection": root.name,
        "marker_count": len(marker_objects),
        "markers_with_issues": sum(bool(marker.issues) for marker in doc.markers),
        "first_marker_source_position": list(first.position),
        "first_marker_blender_position": list(expected_location),
        "start_area_marker_count": len(start_list.markers),
        "finish_area_marker_count": len(finish_list.markers),
        "split_visual_count": len(split_visuals),
        "split_sibling_candidate_point_count": expected_candidate_count,
        "split_trigger_position": "UNKNOWN; not visualized",
        "collection": logic.name,
        "writer_available": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
