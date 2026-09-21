"""Headless Blender smoke test using only generated synthetic resources."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def repository_root():
    return Path(__file__).resolve().parents[2]


def args_after_separator():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate_object(obj, expected):
    mesh = obj.data
    require(obj.type == "MESH", "import did not create a mesh object")
    require(len(mesh.vertices) == expected["vertex_count"], "vertex count mismatch")
    require(len(mesh.polygons) == expected["triangle_count"], "triangle count mismatch")
    require(len(mesh.materials) == expected["material_count"], "material slot mismatch")
    require(len(mesh.uv_layers) == expected["uv_set_count"], "UV layer mismatch")
    required = {
        "mr_source_vertex", "mr_source_vertex_valid", "mr_draw_id",
        "mr_source_triangle", "mr_group_id", "mr_color_byte_0",
        "mr_color_byte_1", "mr_color_byte_2", "mr_color_byte_3",
    }
    require(required.issubset(mesh.attributes.keys()), "source attributes missing")
    require([entry.value for entry in mesh.attributes["mr_source_vertex"].data] == list(range(6)), "source vertex IDs changed")
    require([entry.value for entry in mesh.attributes["mr_draw_id"].data] == [0, 1], "draw IDs changed")
    require([entry.value for entry in mesh.attributes["mr_source_triangle"].data] == [0, 1], "source triangle IDs changed")
    require([entry.value for entry in mesh.attributes["mr_group_id"].data] == [0, 0], "group IDs changed")
    metadata = json.loads(obj["mr_metadata_json"])
    require([draw["record_tag"] for draw in metadata["draws"]] == expected["record_tags"], "record tags missing")
    require(len(metadata["groups"]) == expected["group_count"], "group metadata missing")
    require(metadata["groups"][0]["draw_ids"] == [0, 1], "group hierarchy draw IDs changed")
    require(metadata["texture_presentation"]["png_row_policy"] == "flip-vertical", "PNG policy changed")
    require(metadata["texture_presentation"]["uv_policy"] == "flip-v", "UV policy changed")
    require(obj["mr_authoring_status"] == "SOURCE_IDENTICAL", "initial authoring status changed")
    require(all(polygon.loop_total == 3 for polygon in mesh.polygons), "mesh is not triangular")
    require(len(mesh.corner_normals) == len(mesh.loops), "custom corner normals missing")
    require(all(normal.vector.y < -0.99 for normal in mesh.corner_normals), "custom normals changed")
    require(all(material and material.use_nodes for material in mesh.materials), "preview materials missing")
    images = [node.image for material in mesh.materials for node in material.node_tree.nodes if node.type == "TEX_IMAGE"]
    require(len(images) == 2 and all(image is not None for image in images), "preview images missing")
    return metadata


def main():
    values = args_after_separator()
    if len(values) != 3:
        raise SystemExit("usage after --: <fixture-dir> <output.blend> <report.json>")
    fixture, blend_path, report_path = map(Path, values)
    root = repository_root()
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "blender"))
    import master_rallye_io
    from master_rallye_io.blender_metadata import authoring_status

    expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
    master_rallye_io.register()
    require(hasattr(bpy.ops.import_scene, "master_rallye_dx"), "single DX operator not registered")
    require(hasattr(bpy.ops.import_scene, "master_rallye_vehicle"), "vehicle folder operator not registered")

    folder_result = bpy.ops.import_scene.master_rallye_vehicle(
        directory=str(fixture),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
    )
    require(folder_result == {"FINISHED"}, "vehicle folder operator failed")
    require(any(collection.name.startswith("Master Rallye -") for collection in bpy.data.collections), "vehicle collection missing")
    folder_objects = [obj for obj in bpy.data.objects if "mr_metadata_json" in obj]
    require(len(folder_objects) == 1, "vehicle folder discovery imported wrong resource count")
    validate_object(folder_objects[0], expected)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    single_result = bpy.ops.import_scene.master_rallye_dx(
        filepath=str(fixture / "synthetic.dx"),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
    )
    require(single_result == {"FINISHED"}, "single DX operator failed")
    obj = next(obj for obj in bpy.data.objects if "mr_metadata_json" in obj)
    metadata = validate_object(obj, expected)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    require(obj.mode == "EDIT", "mesh cannot enter Edit Mode")
    bpy.ops.object.mode_set(mode="OBJECT")
    require(authoring_status(obj) == "SOURCE_IDENTICAL", "status check changed untouched mesh")
    original_x = obj.data.vertices[0].co.x
    obj.data.vertices[0].co.x = original_x + 0.25
    require(authoring_status(obj) == "GEOMETRY_EDITED", "coordinate edit was not detected")
    obj.data.vertices[0].co.x = original_x
    require(authoring_status(obj) == "SOURCE_IDENTICAL", "restored geometry did not recover source status")

    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    reloaded = next(obj for obj in bpy.data.objects if "mr_metadata_json" in obj)
    reloaded_metadata = validate_object(reloaded, expected)
    require(reloaded_metadata["groups"] == metadata["groups"], "group metadata did not survive reload")
    require(all(Path(image.filepath).exists() for image in bpy.data.images if image.get("mr_dxt_source")), "cached image path did not survive reload")

    report = {
        "blender_version": bpy.app.version_string,
        "single_dx_operator": "PASS",
        "vehicle_folder_operator": "PASS",
        "editable_mesh": "PASS",
        "save_reload": "PASS",
        "vertex_count": len(reloaded.data.vertices),
        "triangle_count": len(reloaded.data.polygons),
        "material_count": len(reloaded.data.materials),
        "attributes": sorted(reloaded.data.attributes.keys()),
        "metadata_group_count": len(reloaded_metadata["groups"]),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("R2_SYNTHETIC_BLENDER_PASS", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
