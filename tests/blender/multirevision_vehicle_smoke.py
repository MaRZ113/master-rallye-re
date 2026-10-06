"""Exercise the existing add-on on read-only multi-generation vehicle folders.

Run in Blender background mode with three arguments after ``--``:
<demo-input-root> <retail-vehicle-root> <report.json>.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def _role(path: Path) -> str:
    return {
        "car.dx": "RACE BODY",
        "complete.dx": "PRESENTATION",
        "wheel.dx": "WHEEL TEMPLATE",
    }.get(path.name.casefold(), "AUXILIARY")


def _assert_imported_object(obj, model, source: Path, resolver):
    require(obj.type == "MESH", f"{source.name}: expected a mesh")
    require(obj["mr_dx_revision"] == model.dx_revision, f"{source.name}: revision metadata")
    require(obj["mr_source_filename"] == source.name, f"{source.name}: source filename metadata")
    require(obj["mr_resource_role"] == _role(source), f"{source.name}: role metadata")
    require(len(obj.data.vertices) == model.vertex_count, f"{source.name}: vertex count")
    require(len(obj.data.polygons) == model.triangle_count, f"{source.name}: triangle count")
    require(all(polygon.loop_total == 3 for polygon in obj.data.polygons), f"{source.name}: non-triangle face")
    require(len(obj.data.uv_layers) == len(model.uv_sets), f"{source.name}: UV layer count")

    metadata = json.loads(obj["mr_metadata_json"])
    require(metadata["schema_version"] == 4, f"{source.name}: metadata schema")
    validation = metadata["validation"]
    require(validation["structural_import_valid"], f"{source.name}: strict import profile")
    require(validation["index_sequence_equal"] == model.diagnostics.index_sequence_equal, f"{source.name}: exact sequence metadata")
    require(validation["exact_generated_valid"] == model.diagnostics.exact_generated_valid, f"{source.name}: strict writer profile")
    require(validation["writer_revision_supported"] == model.diagnostics.writer_revision_supported, f"{source.name}: writer revision metadata")
    require(validation["validation_profile"] == model.diagnostics.validation_profile, f"{source.name}: validation profile")
    require(metadata["source"]["dx_revision"] == model.dx_revision, f"{source.name}: source revision")
    require(metadata["texture_presentation"]["blender_uv_policy"] == "direct-v", f"{source.name}: UV policy")
    require(
        metadata["normal_provenance"]["custom_normal_api_applied"] is False,
        f"{source.name}: unsafe custom normal setter enabled",
    )

    texture_resolutions = []
    for draw in model.physical_draws:
        for slot in draw.texture_slots:
            if slot.value.casefold() == "null":
                continue
            texture_path = resolver.resolve_texture(slot.value)
            texture_resolutions.append({"slot": slot.value, "resolved": texture_path is not None})
    for material in obj.data.materials:
        if material is None:
            continue
        primary = material.get("mr_primary_texture_slot")
        if not primary or str(primary).casefold() == "null":
            continue
        texture_path = resolver.resolve_texture(str(primary))
        if texture_path is not None:
            require(
                material.get("mr_dxt_source") == str(texture_path.resolve()),
                f"{source.name}: existing DXT did not resolve into the preview material ({primary})",
            )
    resolved = [item for item in texture_resolutions if item["resolved"]]
    if resolved:
        require(
            all(
                image.get("mr_png_row_policy") == "flip-vertical"
                for image in bpy.data.images
                if image.get("mr_dxt_source")
                and Path(image["mr_dxt_source"]).parent.resolve() == source.parent.resolve()
            ),
            f"{source.name}: DXT row policy changed",
        )

    return {
        "source": source.name,
        "revision": model.dx_revision,
        "role": _role(source),
        "vertices": model.vertex_count,
        "triangles": model.triangle_count,
        "draws": len(model.physical_draws),
        "uv_sets": len(model.uv_sets),
        "texture_references": len(texture_resolutions),
        "resolved_texture_references": len(resolved),
        "collision_tags": list(model.collision.tag_ids),
        "collision_validated": model.collision.validated,
        "validation_profile": model.diagnostics.validation_profile,
        "warnings": list(metadata["blender"]["import_warnings"]),
    }


def _new_imported_objects(before):
    return [
        obj for obj in bpy.data.objects
        if obj not in before and obj.get("mr_source_path")
    ]


def _folder_import(folder: Path, root: Path, parser, resolver_type):
    sources = sorted(folder.glob("*.dx"), key=lambda item: item.name.casefold())
    require(sources, f"{folder}: no DX resources")
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.master_rallye_vehicle(
        directory=str(folder),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
        show_collision=True,
    )
    require(result == {"FINISHED"}, f"{folder.name}: folder operator result {result}")
    objects = _new_imported_objects(before)
    require(len(objects) == len(sources), f"{folder.name}: imported {len(objects)}/{len(sources)} DX resources")
    by_source = {Path(obj["mr_source_path"]).resolve(): obj for obj in objects}
    reports = []
    for source in sources:
        resolved = source.resolve()
        require(resolved in by_source, f"{folder.name}: missing imported object for {source.name}")
        model = parser(source)
        reports.append(_assert_imported_object(by_source[resolved], model, source, resolver_type(source.parent)))
    return {
        "folder": folder.relative_to(root).as_posix(),
        "status": "PASS",
        "resource_count": len(sources),
        "ordering_warning_count": sum(
            item["validation_profile"] == "VALID_WITH_INDEX_ORDERING_DIVERGENCE"
            for item in reports
        ),
        "resources": reports,
    }


def _single_import(source: Path, parser, resolver_type):
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.master_rallye_dx(
        filepath=str(source),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
        show_collision=True,
    )
    require(result == {"FINISHED"}, f"{source}: single-file operator result {result}")
    objects = _new_imported_objects(before)
    require(len(objects) == 1, f"{source}: expected one imported mesh, got {len(objects)}")
    model = parser(source)
    return _assert_imported_object(objects[0], model, source, resolver_type(source.parent))


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("usage after --: <demo-input-root> <retail-vehicle-root> <report.json>")
    demo_root, retail_root, report_path = map(Path, args)
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root / "blender"))

    from master_rallye.dx import parse_dx
    from master_rallye.assets import AssetResolver
    import master_rallye_io

    bpy.ops.wm.read_factory_settings(use_empty=True)
    master_rallye_io.register()

    unsupported = []
    demo_folders = []
    for dx_path in sorted(demo_root.rglob("*.dx"), key=lambda item: item.as_posix().casefold()):
        revision = int.from_bytes(dx_path.read_bytes()[4:8], "little") if dx_path.stat().st_size >= 8 else None
        if revision not in (127, 131, 135):
            unsupported.append({"source": dx_path.relative_to(demo_root).as_posix(), "revision": revision})
            continue
        if dx_path.parent not in demo_folders:
            demo_folders.append(dx_path.parent)

    folder_results = []
    for folder in demo_folders:
        folder_results.append(_folder_import(folder, demo_root, parse_dx, AssetResolver))

    retail_families = ("Astero", "Pajero", "Terrano")
    retail_results = []
    for family in retail_families:
        folder = retail_root / family
        retail_results.append(_folder_import(folder, retail_root, parse_dx, AssetResolver))

    single_samples = [
        demo_root / "8.4.1_Trooper" / "car.dx",
        demo_root / "9.3.1_Trooper" / "car.dx",
        demo_root / "!other_research" / "9.10.0_dxForester" / "car.dx",
        retail_root / "Astero" / "car.dx",
    ]
    single_results = [_single_import(source, parse_dx, AssetResolver) for source in single_samples]

    payload = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "addon_version": list(master_rallye_io.bl_info["version"]),
        "single_imports": single_results,
        "demo_folder_imports": folder_results,
        "retail_folder_imports": retail_results,
        "unsupported_demo_inputs": unsupported,
        "normal_policy": "Blender-calculated fallback; native custom-normal setters remain unused",
        "uv_policy": "one direct-v Blender UV policy; DXT PNG rows flipped vertically",
        "total_demo_resources": sum(item["resource_count"] for item in folder_results),
        "total_retail_resources": sum(item["resource_count"] for item in retail_results),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes((json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print("R5V_D_BLENDER_SMOKE_PASS", json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
