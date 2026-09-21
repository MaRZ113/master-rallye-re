"""Headless validation against a small diverse read-only vehicle sample.

This developer-only check writes only ignored reports and a temporary .blend.
No game bytes or derived meshes are committed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


SAMPLES = (
    ("Astero", "complete.dx"),
    ("Astero", "car.dx"),
    ("Astero", "wheel.dx"),
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
        "mr_draw_id",
        "mr_source_triangle",
        "mr_group_id",
    }
    require(obj.type == "MESH", f"{obj.name}: object type")
    require(len(mesh.vertices) == model.vertex_count, f"{obj.name}: vertex count")
    require(len(mesh.polygons) == model.triangle_count, f"{obj.name}: triangle count")
    require(len(mesh.uv_layers) == len(model.uv_sets), f"{obj.name}: UV count")
    require(all(poly.loop_total == 3 for poly in mesh.polygons), f"{obj.name}: topology")
    require(required.issubset(mesh.attributes.keys()), f"{obj.name}: provenance attributes")
    require(len(mesh.corner_normals) == len(mesh.loops), f"{obj.name}: custom normals")
    require(obj["mr_authoring_status"] == "SOURCE_IDENTICAL", f"{obj.name}: initial status")
    metadata = json.loads(obj["mr_metadata_json"])
    require(metadata["validation"]["validated"], f"{obj.name}: validation")
    require(metadata["validation"]["global_indices_match"], f"{obj.name}: index table")
    require(len(metadata["draws"]) == len(model.physical_draws), f"{obj.name}: draw metadata")
    require(
        len(mesh.attributes["mr_draw_id"].data) == model.triangle_count,
        f"{obj.name}: draw face attributes",
    )
    return {
        "resource": f"{Path(model.source_path).parent.name}/{Path(model.source_path).name}",
        "vertices": model.vertex_count,
        "triangles": model.triangle_count,
        "draws": len(model.physical_draws),
        "groups": len(model.draw_groups),
        "uv_sets": len(model.uv_sets),
        "materials": len(mesh.materials),
        "record_tags": model.record_tags,
        "trailing_layout": model.trailing.layout_family,
        "warnings": list(model.diagnostics.warnings),
        "source_status": obj["mr_authoring_status"],
    }


def main() -> None:
    values = args_after_separator()
    if len(values) != 3:
        raise SystemExit("usage after --: <DataGx/Vehicles> <output.blend> <report.json>")
    vehicle_root, blend_path, report_path = map(Path, values)
    root = repository_root()
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "blender"))

    import master_rallye_io
    from master_rallye_io.blender_materials import PreviewMaterialCache
    from master_rallye_io.blender_mesh import create_collection, import_dx_resource
    from master_rallye_io.blender_metadata import authoring_status

    master_rallye_io.register()

    # Exercise the public folder operator with the real Astero folder.
    result = bpy.ops.import_scene.master_rallye_vehicle(
        directory=str(vehicle_root / "Astero"),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
    )
    require(result == {"FINISHED"}, "Astero folder operator failed")
    astero_objects = {
        Path(obj["mr_source_path"]).name: obj
        for obj in bpy.data.objects
        if "mr_metadata_json" in obj and Path(obj["mr_source_path"]).parent.name == "Astero"
    }
    require(set(astero_objects) == {"car.dx", "complete.dx", "wheel.dx"}, "Astero discovery mismatch")

    reports = []
    objects_by_resource = {}
    for family, filename in SAMPLES[:3]:
        obj = astero_objects[filename]
        from master_rallye import parse_dx
        model = parse_dx(vehicle_root / family / filename)
        reports.append(validate_import(obj, model))
        objects_by_resource[f"{family}/{filename}"] = obj

    validation_collection = create_collection("R2 diverse resource validation")
    caches = {}
    for family, filename in SAMPLES[3:]:
        source = vehicle_root / family / filename
        require(source.exists(), f"missing validation resource: {family}/{filename}")
        cache = caches.setdefault(family, PreviewMaterialCache(source.parent, load_textures=True))
        result = import_dx_resource(
            source,
            validation_collection,
            object_name=f"{family}_{source.stem}",
            import_sidecar=True,
            load_textures=True,
            strict=True,
            material_cache=cache,
        )
        reports.append(validate_import(result.object, result.model))
        objects_by_resource[f"{family}/{filename}"] = result.object

    require(len(reports) == len(SAMPLES), "sample count mismatch")
    require(any(item["record_tags"] == [2, 7, 8] for item in reports), "grouped tags not exercised")
    require(any(item["resource"].endswith("/sus.dx") for item in reports), "nonstandard resource missing")

    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    for family, filename in SAMPLES:
        candidates = [
            obj for obj in bpy.data.objects
            if obj.get("mr_source_path")
            and Path(obj["mr_source_path"]).parent.name == family
            and Path(obj["mr_source_path"]).name == filename
        ]
        require(len(candidates) == 1, f"{family}/{filename}: save/reload object")
        obj = candidates[0]
        require(authoring_status(obj) == "SOURCE_IDENTICAL", f"{family}/{filename}: reload status")
        require("mr_draw_id" in obj.data.attributes, f"{family}/{filename}: reload attributes")
        require(json.loads(obj["mr_metadata_json"])["draws"], f"{family}/{filename}: reload metadata")

    preview_images = [image for image in bpy.data.images if image.get("mr_dxt_source")]
    require(preview_images, "no real preview textures loaded")
    require(all(Path(image.filepath).exists() for image in preview_images), "preview path missing after reload")

    payload = {
        "blender_version": bpy.app.version_string,
        "status": "PASS",
        "vehicle_folder_operator": "PASS",
        "sample_count": len(reports),
        "save_reload": "PASS",
        "preview_image_count": len(preview_images),
        "samples": reports,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("R2_REAL_VEHICLE_PASS", json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
