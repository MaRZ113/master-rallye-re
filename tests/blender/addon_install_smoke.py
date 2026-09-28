"""Install, enable, and exercise the built add-on ZIP in an isolated profile."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


values = sys.argv[sys.argv.index("--") + 1:]
if len(values) not in (1, 2, 3):
    raise SystemExit("usage after --: <addon.zip> [synthetic.dx] or <addon.zip> <course.dx> <RaceTest.xml>")
archive = Path(values[0]).resolve()
fixture = Path(values[1]).resolve() if len(values) == 2 else None
course_pair = (Path(values[1]).resolve(), Path(values[2]).resolve()) if len(values) == 3 else None
result = bpy.ops.preferences.addon_install(filepath=str(archive), overwrite=True)
if result != {"FINISHED"}:
    raise AssertionError(f"add-on install failed: {result}")
result = bpy.ops.preferences.addon_enable(module="master_rallye_io")
if result != {"FINISHED"}:
    raise AssertionError(f"add-on enable failed: {result}")
if not hasattr(bpy.ops.import_scene, "master_rallye_dx"):
    raise AssertionError("single DX operator missing after ZIP install")
if not hasattr(bpy.ops.import_scene, "master_rallye_vehicle"):
    raise AssertionError("vehicle folder operator missing after ZIP install")
if not hasattr(bpy.ops.import_scene, "master_rallye_course_xml_markers"):
    raise AssertionError("RaceTest XML marker operator missing after ZIP install")
if not hasattr(bpy.ops.export_scene, "master_rallye_dx_attributes"):
    raise AssertionError("R4E attribute DX operator missing after ZIP install")
if not hasattr(bpy.ops.export_scene, "master_rallye_dx_positions"):
    raise AssertionError("positions-only DX operator missing after ZIP install")

payload = {
    "blender_version": bpy.app.version_string,
    "archive": archive.name,
    "install": "PASS",
    "vendored_import": "NOT_RUN",
    "vendored_course_import": "NOT_RUN",
}
if fixture is not None:
    result = bpy.ops.import_scene.master_rallye_dx(
        filepath=str(fixture),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
    )
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged synthetic import failed: {result}")
    objects = [obj for obj in bpy.data.objects if "mr_metadata_json" in obj]
    if len(objects) != 1:
        raise AssertionError("packaged add-on created wrong object count")
    obj = objects[0]
    metadata = json.loads(obj["mr_metadata_json"])
    if len(obj.data.vertices) != 4 or len(obj.data.polygons) != 2:
        raise AssertionError("vendored parser geometry mismatch")
    if [draw["record_tag"] for draw in metadata["draws"]] != [7, 8]:
        raise AssertionError("vendored parser group tags mismatch")
    if metadata["texture_presentation"]["blender_uv_policy"] != "direct-v":
        raise AssertionError("vendored Blender UV policy mismatch")
    if metadata["normal_provenance"]["display_strategy"] != "blender-calculated-fallback":
        raise AssertionError("vendored normal strategy mismatch")
    if not metadata["collision"]["tag101_present"]:
        raise AssertionError("vendored collision parser metadata missing")
    overlays = [item for item in bpy.data.objects if item.get("mr_collision_owner") == obj["mr_source_path"]]
    if len(overlays) != 3:
        raise AssertionError("vendored collision overlay mismatch")
    payload["vendored_import"] = "PASS"
    payload["blender_uv_policy"] = "direct-v"
    payload["display_normal_strategy"] = "blender-calculated-fallback"
    payload["collision_overlay"] = "PASS"
    zero_output = archive.parent / "packaged-zero-edit.dx"
    result = bpy.ops.export_scene.master_rallye_dx_positions(
        filepath=str(zero_output),
    )
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged zero-edit export failed: {result}")
    if zero_output.read_bytes() != fixture.read_bytes():
        raise AssertionError("packaged zero-edit export was not byte-identical")
    payload["positions_only_export"] = "PASS"

if course_pair is not None:
    course_dx, xml_path = course_pair
    result = bpy.ops.import_scene.master_rallye_course(
        filepath=str(course_dx), load_textures=False
    )
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged course DX import failed: {result}")
    from master_rallye_io.library import parse_course_xml
    document = parse_course_xml(xml_path)
    expected = sum(marker.position is not None for marker in document.markers)
    result = bpy.ops.import_scene.master_rallye_course_xml_markers(filepath=str(xml_path))
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged XML marker import failed: {result}")
    overlays = [
        collection for collection in bpy.data.collections
        if collection.get("mr_xml_source") == str(xml_path)
    ]
    if len(overlays) != 1 or len(overlays[0].objects) != expected:
        raise AssertionError("packaged XML marker count or collection mismatch")
    payload["vendored_course_import"] = "PASS"
    payload["course_xml_overlay"] = "PASS"
    payload["course_xml_marker_count"] = expected

print("R3_ADDON_INSTALL_PASS", json.dumps(payload, sort_keys=True))
