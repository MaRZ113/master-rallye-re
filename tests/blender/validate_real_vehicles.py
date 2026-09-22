"""Headless validation against diverse read-only vehicle resources.

This developer-only check writes only ignored reports and a temporary .blend.
No game bytes or derived meshes are committed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


FOLDER_FAMILIES = ("Astero", "Pajero", "Forester", "Bruno", "Ufo", "megane")
REQUIRED_SAMPLES = (
    ("Astero", "complete.dx"),
    ("Astero", "car.dx"),
    ("Astero", "wheel.dx"),
    ("Pajero", "car.dx"),
    ("Pajero", "complete.dx"),
    ("Pajero", "wheel.dx"),
    ("Forester", "complete.dx"),
    ("Bruno", "car.dx"),
    ("Bruno", "wheel.dx"),
    ("ChevyBlazer", "car.dx"),
    ("Ufo", "complete.dx"),
    ("megane", "sus.dx"),
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def args_after_separator() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def require(condition, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_import(obj, model) -> dict:
    mesh = obj.data
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
    }
    resource = f"{Path(model.source_path).parent.name}/{Path(model.source_path).name}"
    require(obj.type == "MESH", f"{resource}: object type")
    require(len(mesh.vertices) == model.vertex_count, f"{resource}: vertex count")
    require(len(mesh.polygons) == model.triangle_count, f"{resource}: triangle count")
    require(len(mesh.uv_layers) == len(model.uv_sets), f"{resource}: UV count")
    require(all(poly.loop_total == 3 for poly in mesh.polygons), f"{resource}: topology")
    require(required.issubset(mesh.attributes.keys()), f"{resource}: provenance")
    require(len(mesh.corner_normals) == len(mesh.loops), f"{resource}: normals")
    require(obj["mr_authoring_status"] == "SOURCE_IDENTICAL", f"{resource}: status")
    metadata = json.loads(obj["mr_metadata_json"])
    require(metadata["validation"]["validated"], f"{resource}: validation")
    require(metadata["validation"]["global_indices_match"], f"{resource}: indices")
    require(len(metadata["draws"]) == len(model.physical_draws), f"{resource}: draws")
    require(
        metadata["texture_presentation"]["blender_uv_policy"] == "direct-v",
        f"{resource}: Blender UV policy",
    )
    require(
        metadata["texture_presentation"]["gltf_uv_policy"] == "flip-v",
        f"{resource}: glTF UV policy",
    )
    normal = metadata["normal_provenance"]
    require(normal["diagnostics"]["count"] == model.vertex_count, f"{resource}: normal count")
    import_warnings = metadata["blender"]["import_warnings"]
    if (
        normal["diagnostics"]["non_finite_count"] == 0
        and normal["diagnostics"]["near_zero_count"] == 0
    ):
        require(
            not any("display normals fallback" in warning for warning in import_warnings),
            f"{resource}: valid normals emitted fallback warning",
        )
    return {
        "resource": resource,
        "vertices": model.vertex_count,
        "triangles": model.triangle_count,
        "draws": len(model.physical_draws),
        "groups": len(model.draw_groups),
        "uv_sets": len(model.uv_sets),
        "materials": len(mesh.materials),
        "record_tags": model.record_tags,
        "trailing_layout": model.trailing.layout_family,
        "warnings": list(import_warnings),
        "source_status": obj["mr_authoring_status"],
        "normal_count": normal["diagnostics"]["count"],
        "normal_non_finite": normal["diagnostics"]["non_finite_count"],
        "normal_near_zero": normal["diagnostics"]["near_zero_count"],
        "normal_min_magnitude": normal["diagnostics"]["min_magnitude"],
        "normal_max_magnitude": normal["diagnostics"]["max_magnitude"],
        "display_normal_strategy": normal["display_strategy"],
    }


def objects_for_family(family: str):
    return [
        obj
        for obj in bpy.data.objects
        if obj.get("mr_source_path")
        and Path(obj["mr_source_path"]).parent.name.casefold() == family.casefold()
    ]


def main() -> None:
    values = args_after_separator()
    if len(values) != 3:
        raise SystemExit("usage after --: <DataGx/Vehicles> <output.blend> <report.json>")
    vehicle_root, blend_path, report_path = map(Path, values)
    root = repository_root()
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "blender"))

    import master_rallye_io
    from master_rallye import parse_dx
    from master_rallye_io.blender_materials import PreviewMaterialCache
    from master_rallye_io.blender_mesh import create_collection, import_dx_resource
    from master_rallye_io.blender_metadata import authoring_status
    from master_rallye_io.blender_export import export_dx_positions

    bpy.ops.wm.read_factory_settings(use_empty=True)
    master_rallye_io.register()

    folder_results = {}
    reports_by_resource = {}
    for family in FOLDER_FAMILIES:
        folder = vehicle_root / family
        expected_count = len(list(folder.glob("*.dx")))
        result = bpy.ops.import_scene.master_rallye_vehicle(
            directory=str(folder),
            import_sidecar=True,
            load_textures=True,
            strict_validation=True,
        )
        require(result == {"FINISHED"}, f"{family} folder operator failed")
        imported = objects_for_family(family)
        require(
            len(imported) == expected_count,
            f"{family}: imported {len(imported)}/{expected_count}",
        )
        family_warning_count = 0
        for obj in imported:
            model = parse_dx(Path(obj["mr_source_path"]))
            item = validate_import(obj, model)
            family_warning_count += len(item["warnings"])
            reports_by_resource[item["resource"]] = item
        folder_results[family] = {
            "status": "PASS",
            "resource_count": len(imported),
            "warning_count": family_warning_count,
        }

    # Preserve the established ChevyBlazer grouped/declared-count sample.
    source = vehicle_root / "ChevyBlazer" / "car.dx"
    result = import_dx_resource(
        source,
        create_collection("R2 ChevyBlazer validation"),
        object_name="ChevyBlazer_car",
        import_sidecar=True,
        load_textures=True,
        strict=True,
        material_cache=PreviewMaterialCache(source.parent, load_textures=True),
    )
    item = validate_import(result.object, result.model)
    reports_by_resource[item["resource"]] = item

    for family, filename in REQUIRED_SAMPLES:
        key = f"{family}/{filename}"
        require(key in reports_by_resource, f"required sample missing: {key}")

    require(
        any(item["record_tags"] == [2, 7, 8] for item in reports_by_resource.values()),
        "grouped tags not exercised",
    )
    require(
        any(item["resource"].endswith("/sus.dx") for item in reports_by_resource.values()),
        "nonstandard resource missing",
    )

    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    for resource in reports_by_resource:
        family, filename = resource.split("/", 1)
        candidates = [
            obj
            for obj in bpy.data.objects
            if obj.get("mr_source_path")
            and Path(obj["mr_source_path"]).parent.name.casefold() == family.casefold()
            and Path(obj["mr_source_path"]).name.casefold() == filename.casefold()
        ]
        require(len(candidates) == 1, f"{resource}: save/reload object")
        obj = candidates[0]
        require(authoring_status(obj) == "SOURCE_IDENTICAL", f"{resource}: reload status")
        require("mr_draw_id" in obj.data.attributes, f"{resource}: reload face attrs")
        require("mr_source_normal_bits_x" in obj.data.attributes, f"{resource}: reload normals")
        metadata = json.loads(obj["mr_metadata_json"])
        require(metadata["draws"], f"{resource}: reload metadata")
        require(
            metadata["normal_provenance"]["display_strategy"]
            == reports_by_resource[resource]["display_normal_strategy"],
            f"{resource}: reload normal strategy",
        )

    zero_edit_results = []
    zero_root = report_path.parent / "r3-zero-edit"
    zero_root.mkdir(parents=True, exist_ok=True)
    for family, filename in REQUIRED_SAMPLES:
        obj = next(
            item for item in bpy.data.objects
            if item.get("mr_source_path")
            and Path(item["mr_source_path"]).parent.name.casefold() == family.casefold()
            and Path(item["mr_source_path"]).name.casefold() == filename.casefold()
        )
        output = zero_root / f"{family}-{filename}"
        result = export_dx_positions(obj, output)
        source_bytes = Path(obj["mr_source_path"]).read_bytes()
        require(result.patch.byte_identical, f"{family}/{filename}: zero edit")
        require(output.read_bytes() == source_bytes, f"{family}/{filename}: byte identity")
        zero_edit_results.append(f"{family}/{filename}")

    preview_images = [image for image in bpy.data.images if image.get("mr_dxt_source")]
    require(preview_images, "no real preview textures loaded")
    require(
        all(Path(image.filepath).exists() for image in preview_images),
        "preview path missing after reload",
    )

    samples = [reports_by_resource[f"{family}/{filename}"] for family, filename in REQUIRED_SAMPLES]
    payload = {
        "blender_version": bpy.app.version_string,
        "status": "PASS",
        "folder_results": folder_results,
        "validated_resource_count": len(reports_by_resource),
        "required_sample_count": len(samples),
        "save_reload": "PASS",
        "preview_image_count": len(preview_images),
        "required_samples": samples,
        "r3_zero_edit_exports": zero_edit_results,
        "all_resources": sorted(reports_by_resource.values(), key=lambda item: item["resource"]),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("R3_REAL_VEHICLE_PASS", json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
