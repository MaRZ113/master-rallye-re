"""Exercise the packaged add-on ZIP directly without installing to user config."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 4:
        raise SystemExit("expected addon.zip course.dx RaceTest.xml output.json after --")
    archive, dx_path, xml_path, output = (Path(value).resolve() for value in args)
    # The install smoke writes to Blender's external user profile. Import the
    # built ZIP as a Python package instead, keeping the test inside the repo.
    sys.path.insert(0, str(archive))
    import master_rallye_io
    from master_rallye_io.library import parse_course_xml, position_to_blender

    master_rallye_io.register()
    doc = parse_course_xml(xml_path)
    dx_status = bpy.ops.import_scene.master_rallye_course(
        "EXEC_DEFAULT", filepath=str(dx_path), load_textures=False
    )
    if dx_status != {"FINISHED"}:
        raise AssertionError(f"packaged course DX import failed: {dx_status}")
    xml_status = bpy.ops.import_scene.master_rallye_course_xml_markers(
        "EXEC_DEFAULT", filepath=str(xml_path)
    )
    if xml_status != {"FINISHED"}:
        raise AssertionError(f"packaged RaceTest XML import failed: {xml_status}")

    roots = [
        collection for collection in bpy.data.collections
        if collection.get("mr_xml_source") == str(xml_path)
        and collection.get("mr_xml_collection_kind") == "race_logic_root"
    ]
    if len(roots) != 1:
        raise AssertionError(f"packaged RaceTest hierarchy count is {len(roots)}")
    descendants = []
    def walk(collection):
        descendants.append(collection)
        for child in collection.children:
            walk(child)
    walk(roots[0])
    markers = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
    ]
    signs = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest split-time visual sign icon"
    ]
    candidates = next(
        (collection for collection in descendants if collection.get("mr_xml_collection_kind") == "split_sibling_candidates"),
        None,
    )
    expected_markers = [marker for marker in doc.markers if marker.position is not None]
    if len(markers) != len(expected_markers):
        raise AssertionError("packaged marker count differs from the hierarchy-aware parser")
    if len(signs) != len(doc.split_time_eggs):
        raise AssertionError("packaged split visual count differs from parsed split Egg count")
    if candidates is None or len(candidates.objects) != 12:
        raise AssertionError("packaged split sibling candidates were not kept as twelve UNKNOWN points")
    if any(sign.get("mr_trigger_position_status") != "UNKNOWN; deliberately not visualized" for sign in signs):
        raise AssertionError("packaged split visual helper conflated sign and trigger")
    for sign in signs:
        metadata = json.loads(sign["mr_source_egg_metadata_json"])
        if not any(value["name"] == "en3d Matrix" for value in metadata["egg_values"]):
            raise AssertionError("packaged split helper omitted raw Egg matrix metadata")
    start = doc.marker_list("StartArea")
    area = next((collection for collection in descendants if collection.get("mr_source_list_name") == "StartArea"), None)
    if start is None or area is None:
        raise AssertionError("packaged StartArea hierarchy is missing")
    first = next(obj for obj in area.objects if obj.get("mr_marker_index_in_list") == 0)
    expected_location = position_to_blender(start.markers[0].position)
    actual = tuple(float(first.location[index]) for index in range(3))
    if any(abs(actual[index] - expected_location[index]) > 1.0e-4 for index in range(3)):
        raise AssertionError("packaged StartArea position conversion differs from the canonical transform")

    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "archive": archive.name,
        "course_dx": dx_path.name,
        "racetest_xml": xml_path.name,
        "marker_count": len(markers),
        "split_visual_count": len(signs),
        "split_sibling_candidate_count": len(candidates.objects),
        "trigger_position": "UNKNOWN; not visualized",
        "user_profile_modified": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
