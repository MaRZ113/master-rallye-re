"""Headless smoke test for the read-only RaceTest XML marker overlay.

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
    overlays = [child for child in root.children if child.get("mr_xml_source") == str(xml_path)]
    if len(overlays) != 1:
        raise AssertionError(f"expected one XML marker overlay, found {len(overlays)}")
    objects = list(overlays[0].objects)
    if len(objects) != len(expected):
        raise AssertionError(f"marker count {len(objects)} differs from parsed XML {len(expected)}")
    first = expected[0]
    first_object = next(obj for obj in objects if obj.get("mr_marker_ordinal") == first.ordinal)
    expected_location = position_to_blender(first.position)
    actual_location = tuple(float(first_object.location[i]) for i in range(3))
    if any(abs(actual_location[i] - expected_location[i]) > 1.0e-4 for i in range(3)):
        raise AssertionError(
            f"first XML marker location {actual_location} differs from converted {expected_location}"
        )
    if tuple(first_object["mr_source_position_xyz"]) != first.position:
        raise AssertionError("source XML marker coordinates were not preserved")

    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "course_dx": dx_path.name,
        "racetest_xml": xml_path.name,
        "root_collection": root.name,
        "marker_count": len(objects),
        "markers_with_issues": sum(bool(marker.issues) for marker in doc.markers),
        "first_marker_source_position": list(first.position),
        "first_marker_blender_position": list(expected_location),
        "collection": overlays[0].name,
        "writer_available": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
