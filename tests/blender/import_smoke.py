"""Headless Blender smoke test using only generated synthetic resources."""
from __future__ import annotations

import json
import math
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


def source_normal_bits(mesh):
    return [
        [
            mesh.attributes[f"mr_source_normal_bits_{axis}"].data[index].value
            for axis in ("x", "y", "z")
        ]
        for index in range(len(mesh.vertices))
    ]


def validate_object(obj, expected):
    mesh = obj.data
    require(obj.type == "MESH", "import did not create a mesh object")
    require(len(mesh.vertices) == expected["vertex_count"], "vertex count mismatch")
    require(len(mesh.polygons) == expected["triangle_count"], "triangle count mismatch")
    require(len(mesh.materials) == expected["material_count"], "material slot mismatch")
    require(len(mesh.uv_layers) == expected["uv_set_count"], "UV layer mismatch")
    required = {
        "mr_source_vertex",
        "mr_source_vertex_valid",
        "mr_source_normal",
        "mr_source_normal_valid",
        "mr_source_normal_bits_x",
        "mr_source_normal_bits_y",
        "mr_source_normal_bits_z",
        "mr_draw_id",
        "mr_source_triangle",
        "mr_group_id",
        "mr_color_byte_0",
        "mr_color_byte_1",
        "mr_color_byte_2",
        "mr_color_byte_3",
    }
    require(required.issubset(mesh.attributes.keys()), "source attributes missing")
    require(
        [entry.value for entry in mesh.attributes["mr_source_vertex"].data]
        == list(range(expected["vertex_count"])),
        "source vertex IDs changed",
    )
    require(
        [entry.value for entry in mesh.attributes["mr_draw_id"].data] == [0, 1],
        "draw IDs changed",
    )
    require(
        [entry.value for entry in mesh.attributes["mr_source_triangle"].data]
        == [0, 1],
        "source triangle IDs changed",
    )
    require(
        [entry.value for entry in mesh.attributes["mr_group_id"].data] == [0, 0],
        "group IDs changed",
    )
    require(
        source_normal_bits(mesh) == expected["source_normal_bits"],
        "exact source-normal bits changed",
    )
    source_vectors = [
        tuple(item.vector)
        for item in mesh.attributes["mr_source_normal"].data
    ]
    require(
        math.isclose(source_vectors[0][2], 2.0)
        and math.isclose(source_vectors[1][2], 0.5)
        and math.isclose(source_vectors[3][2], 3.0),
        "non-unit source normals were overwritten",
    )

    metadata = json.loads(obj["mr_metadata_json"])
    require(
        [draw["record_tag"] for draw in metadata["draws"]]
        == expected["record_tags"],
        "record tags missing",
    )
    require(len(metadata["groups"]) == expected["group_count"], "group metadata missing")
    require(
        metadata["sidecar"]["materials"][0]["textures"][0]["has_alpha"] is False
        and metadata["sidecar"]["materials"][0]["textures"][0]["uses_alpha"] is True
        and metadata["sidecar"]["materials"][0]["textures"][0]["is_noise"] is False,
        "TXT texture flags missing from Blender metadata",
    )
    require(
        metadata["sidecar_resolution"]["selected_path"].endswith("synthetic.txt")
        and not metadata["sidecar_resolution"]["ambiguous"],
        "evidence-scored sidecar selection metadata missing",
    )
    require(metadata["groups"][0]["draw_ids"] == [0, 1], "group hierarchy changed")
    presentation = metadata["texture_presentation"]
    require(presentation["png_row_policy"] == "flip-vertical", "PNG policy changed")
    require(presentation["gltf_uv_policy"] == "flip-v", "glTF UV policy changed")
    require(presentation["blender_uv_policy"] == "direct-v", "Blender UV policy wrong")
    require(
        metadata["normal_provenance"]["display_strategy"]
        == "blender-calculated-fallback",
        "safe display-normal fallback not used",
    )
    require(
        obj["mr_display_normal_strategy"] == "blender-calculated-fallback",
        "normal fallback strategy property missing",
    )
    require(obj["mr_authoring_status"] == "SOURCE_IDENTICAL", "initial status changed")
    require(all(polygon.loop_total == 3 for polygon in mesh.polygons), "not triangular")
    require(len(mesh.corner_normals) == len(mesh.loops), "corner normals missing")
    expected_uvs = [tuple(value) for value in expected["uvs"]]
    uv_layer = mesh.uv_layers["MR UV 0"]
    for loop in mesh.loops:
        actual = tuple(uv_layer.data[loop.index].uv)
        expected_uv = expected_uvs[loop.vertex_index]
        require(
            all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(actual, expected_uv)),
            "Blender UVs are not direct source V",
        )

    require(
        all(material and material.use_nodes for material in mesh.materials),
        "preview materials missing",
    )
    images = [
        node.image
        for material in mesh.materials
        for node in material.node_tree.nodes
        if node.type == "TEX_IMAGE"
    ]
    require(
        len(images) == 2 and all(image is not None for image in images),
        "preview images missing",
    )
    top_image = next(image for image in images if "synthetic-top" in image.name)
    bottom_left = tuple(top_image.pixels[:4])
    require(
        bottom_left[2] > 0.9
        and bottom_left[0] < 0.05
        and bottom_left[1] < 0.05,
        "upright PNG bottom row is not blue in Blender",
    )
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
    from master_rallye_io.blender_materials import PreviewMaterialCache
    from master_rallye_io.blender_mesh import (
        _apply_display_normals,
        create_collection,
        import_dx_resource,
    )
    from master_rallye_io.blender_metadata import authoring_status

    expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
    master_rallye_io.register()
    require(
        hasattr(bpy.ops.import_scene, "master_rallye_dx"),
        "single DX operator not registered",
    )
    require(
        hasattr(bpy.ops.import_scene, "master_rallye_vehicle"),
        "vehicle folder operator not registered",
    )
    require(
        hasattr(bpy.ops.export_scene, "master_rallye_dx_positions"),
        "positions-only export operator not registered",
    )

    folder_result = bpy.ops.import_scene.master_rallye_vehicle(
        directory=str(fixture),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
    )
    require(folder_result == {"FINISHED"}, "vehicle folder operator failed")
    folder_objects = [obj for obj in bpy.data.objects if "mr_metadata_json" in obj]
    require(len(folder_objects) == 2, "multi-DX folder discovery failed")
    primary = next(
        obj for obj in folder_objects if obj["mr_resource_name"] == "synthetic.dx"
    )
    validate_object(primary, expected)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    single_result = bpy.ops.import_scene.master_rallye_dx(
        filepath=str(fixture / "synthetic.dx"),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
    )
    require(single_result == {"FINISHED"}, "single DX operator failed")
    obj = next(
        obj for obj in bpy.data.objects
        if obj.get("mr_resource_name") == "synthetic.dx"
    )
    metadata = validate_object(obj, expected)

    valid_direct = import_dx_resource(
        fixture / "synthetic.dx",
        create_collection("valid warning check"),
        object_name="valid warning check",
        import_sidecar=True,
        load_textures=True,
        strict=True,
    )
    require(
        not any("display normals fallback" in warning for warning in valid_direct.warnings),
        "valid intentional display strategy emitted a warning",
    )

    fallback = import_dx_resource(
        fixture / "fallback" / "synthetic-fallback.dx",
        create_collection("normal fallback"),
        object_name="synthetic fallback",
        import_sidecar=False,
        load_textures=False,
        strict=True,
    )
    fallback_metadata = json.loads(fallback.object["mr_metadata_json"])
    require(
        fallback_metadata["normal_provenance"]["display_strategy"]
        == "blender-calculated-fallback",
        "invalid source normals did not select safe fallback",
    )
    diagnostics = fallback_metadata["normal_provenance"]["diagnostics"]
    require(diagnostics["non_finite_count"] == 1, "non-finite count mismatch")
    require(diagnostics["near_zero_count"] == 1, "near-zero count mismatch")
    require(
        any("display normals fallback" in warning for warning in fallback.warnings),
        "normal fallback warning missing",
    )
    require(
        source_normal_bits(fallback.object.data)
        == expected["fallback_source_normal_bits"],
        "fallback source-normal bits changed",
    )

    diagnostic_mesh = bpy.data.meshes.new("normal diagnostic mesh")
    diagnostic_mesh.from_pydata(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        [],
        (),
    )
    _, non_finite_diagnostics, non_finite_warnings = _apply_display_normals(
        diagnostic_mesh,
        ((float("nan"), 0.0, 1.0), (0.0, 0.0, 1.0)),
    )
    require(non_finite_diagnostics.non_finite_count == 1, "non-finite diagnostic")
    require(len(non_finite_warnings) == 1, "non-finite normal warning missing")
    _, zero_diagnostics, zero_warnings = _apply_display_normals(
        diagnostic_mesh,
        ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    )
    require(zero_diagnostics.near_zero_count == 1, "near-zero diagnostic")
    require(len(zero_warnings) == 1, "near-zero normal warning missing")
    _, count_diagnostics, count_warnings = _apply_display_normals(
        diagnostic_mesh,
        ((0.0, 0.0, 1.0),),
    )
    require(count_diagnostics.count == 1, "count diagnostic")
    require(len(count_warnings) == 1, "normal-count warning missing")

    warning_folder = fixture / "warning-cache"
    shared_cache = PreviewMaterialCache(warning_folder, load_textures=True)
    missing_result = import_dx_resource(
        warning_folder / "a-missing.dx",
        create_collection("warning resource A"),
        import_sidecar=False,
        load_textures=True,
        strict=True,
        material_cache=shared_cache,
    )
    clean_result = import_dx_resource(
        warning_folder / "b-clean.dx",
        create_collection("warning resource B"),
        import_sidecar=False,
        load_textures=True,
        strict=True,
        material_cache=shared_cache,
    )
    missing_warnings = [
        warning for warning in missing_result.warnings if "missing texture" in warning
    ]
    require(len(missing_warnings) == 1, "resource A missing texture not reported once")
    require(
        not any("missing texture" in warning for warning in clean_result.warnings),
        "resource B inherited resource A material warning",
    )
    require(len(shared_cache.warnings) == 1, "cache-wide diagnostics were not retained")
    folder_warning_count = len(missing_result.warnings) + len(clean_result.warnings)
    expected_folder_warning_count = (
        len(missing_result.model.diagnostics.warnings)
        + len(clean_result.model.diagnostics.warnings)
        + 1
    )
    require(
        folder_warning_count == expected_folder_warning_count,
        f"folder warning count does not equal current-resource issues: "
        f"A={missing_result.warnings!r}, B={clean_result.warnings!r}",
    )

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    require(obj.mode == "EDIT", "mesh cannot enter Edit Mode")
    bpy.ops.object.mode_set(mode="OBJECT")
    require(authoring_status(obj) == "SOURCE_IDENTICAL", "untouched status changed")
    zero_output = blend_path.parent / "synthetic-zero-edit.dx"
    bpy.context.view_layer.objects.active = obj
    zero_result = bpy.ops.export_scene.master_rallye_dx_positions(
        filepath=str(zero_output),
    )
    require(zero_result == {"FINISHED"}, "zero-edit export operator failed")
    require(
        zero_output.read_bytes() == (fixture / "synthetic.dx").read_bytes(),
        "zero-edit Blender export was not byte-identical",
    )
    original_x = obj.data.vertices[0].co.x
    obj.data.vertices[0].co.x = original_x + 0.25
    require(
        authoring_status(obj) == "POSITIONS_ONLY_CHANGED",
        "positions-only edit not detected",
    )
    edited_output = blend_path.parent / "synthetic-one-vertex.dx"
    edited_result = bpy.ops.export_scene.master_rallye_dx_positions(
        filepath=str(edited_output),
    )
    require(edited_result == {"FINISHED"}, "one-vertex export failed")
    from master_rallye.dx_writer import patch_dx_positions
    from master_rallye.dx import parse_dx
    expected_positions = list(parse_dx(fixture / "synthetic.dx").vertices.positions)
    expected_positions[0] = (expected_positions[0][0] + 0.25, 0.0, 0.0)
    expected_patch = patch_dx_positions(
        (fixture / "synthetic.dx").read_bytes(),
        expected_positions,
    )
    require(
        edited_output.read_bytes() == expected_patch.data,
        "Blender one-vertex output differs from canonical writer",
    )
    obj.data.vertices[0].co.x = original_x
    require(authoring_status(obj) == "SOURCE_IDENTICAL", "restored status changed")

    duplicate = obj.data.attributes["mr_source_vertex"].data
    original_source_id = duplicate[1].value
    duplicate[1].value = duplicate[0].value
    refused_output = blend_path.parent / "must-not-exist.dx"
    if refused_output.exists():
        refused_output.unlink()
    try:
        refused = bpy.ops.export_scene.master_rallye_dx_positions(
            filepath=str(refused_output),
        )
    except RuntimeError as error:
        refused = {"CANCELLED"}
        require("duplicate source vertex IDs" in str(error), "wrong refusal reason")
    require(refused == {"CANCELLED"}, "invalid provenance export was not refused")
    require(not refused_output.exists(), "refused export wrote a file")
    duplicate[1].value = original_source_id
    from master_rallye_io.blender_metadata import refresh_authoring_status
    require(
        refresh_authoring_status(obj) == "SOURCE_IDENTICAL",
        "restored provenance status changed",
    )

    import bmesh
    from master_rallye_io.blender_export import export_dx_positions
    topology_obj = obj.copy()
    topology_obj.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(topology_obj)
    topology_mesh = topology_obj.data
    edit_mesh = bmesh.new()
    edit_mesh.from_mesh(topology_mesh)
    edit_mesh.verts.new((0.25, 0.25, 0.25))
    edit_mesh.to_mesh(topology_mesh)
    edit_mesh.free()
    topology_output = blend_path.parent / "topology-must-not-exist.dx"
    if topology_output.exists():
        topology_output.unlink()
    try:
        export_dx_positions(topology_obj, topology_output)
    except ValueError as error:
        require("vertex count" in str(error), "wrong topology refusal reason")
    else:
        raise AssertionError("topology-modified mesh export was not refused")
    require(not topology_output.exists(), "topology refusal wrote a file")
    bpy.data.objects.remove(topology_obj, do_unlink=True)

    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    reloaded = next(
        obj for obj in bpy.data.objects
        if obj.get("mr_resource_name") == "synthetic.dx"
    )
    reloaded_metadata = validate_object(reloaded, expected)
    require(reloaded_metadata["groups"] == metadata["groups"], "groups lost on reload")
    reloaded_fallback = next(
        obj for obj in bpy.data.objects
        if obj.get("mr_resource_name") == "synthetic-fallback.dx"
    )
    require(
        source_normal_bits(reloaded_fallback.data)
        == expected["fallback_source_normal_bits"],
        "fallback source-normal provenance did not survive reload",
    )
    require(
        reloaded_fallback["mr_display_normal_strategy"]
        == "blender-calculated-fallback",
        "fallback strategy did not survive reload",
    )
    require(
        all(
            Path(image.filepath).exists()
            for image in bpy.data.images
            if image.get("mr_dxt_source")
        ),
        "cached image path did not survive reload",
    )
    bpy.context.view_layer.objects.active = reloaded
    reloaded.select_set(True)
    reload_output = blend_path.parent / "synthetic-reloaded-zero-edit.dx"
    reload_result = bpy.ops.export_scene.master_rallye_dx_positions(
        filepath=str(reload_output),
    )
    require(reload_result == {"FINISHED"}, "save/reload export failed")
    require(
        reload_output.read_bytes() == (fixture / "synthetic.dx").read_bytes(),
        "save/reload zero-edit output was not byte-identical",
    )

    report = {
        "blender_version": bpy.app.version_string,
        "single_dx_operator": "PASS",
        "vehicle_folder_operator_multiple_dx": "PASS",
        "editable_mesh": "PASS",
        "save_reload": "PASS",
        "blender_uv_policy": "direct-v",
        "gltf_uv_policy": "flip-v",
        "png_row_policy": "flip-vertical",
        "display_normal_strategy": reloaded["mr_display_normal_strategy"],
        "fallback_normal_strategy": reloaded_fallback["mr_display_normal_strategy"],
        "valid_normal_warning_count": sum(
            "display normals fallback" in warning
            for warning in valid_direct.warnings
        ),
        "invalid_normal_warning_cases": 3,
        "cache_warning_duplication": "PASS",
        "folder_warning_count": folder_warning_count,
        "positions_only_export": "PASS",
        "zero_edit_byte_identical": True,
        "one_vertex_export": "PASS",
        "invalid_provenance_rejection": "PASS",
        "topology_modification_rejection": "PASS",
        "save_reload_export": "PASS",
        "vertex_count": len(reloaded.data.vertices),
        "triangle_count": len(reloaded.data.polygons),
        "material_count": len(reloaded.data.materials),
        "attributes": sorted(reloaded.data.attributes.keys()),
        "metadata_group_count": len(reloaded_metadata["groups"]),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("R3_SYNTHETIC_BLENDER_PASS", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
