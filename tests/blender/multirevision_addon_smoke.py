"""Install the packaged add-on and exercise its vendored multi-revision parser."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def import_folder(folder: Path, expected_revision: int):
    sources = sorted(folder.glob("*.dx"), key=lambda item: item.name.casefold())
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.master_rallye_vehicle(
        directory=str(folder),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
        show_collision=True,
    )
    require(result == {"FINISHED"}, f"{folder}: folder import {result}")
    objects = [obj for obj in bpy.data.objects if obj not in before and obj.get("mr_source_path")]
    require(len(objects) == len(sources), f"{folder}: imported {len(objects)}/{len(sources)} resources")
    rows = []
    for obj in objects:
        metadata = json.loads(obj["mr_metadata_json"])
        require(metadata["schema_version"] == 4, f"{obj.name}: metadata schema")
        require(obj["mr_dx_revision"] == expected_revision, f"{obj.name}: revision")
        require(metadata["validation"]["structural_import_valid"], f"{obj.name}: structural validation")
        require(
            metadata["validation"]["exact_generated_valid"]
            == metadata["validation"]["validated"],
            f"{obj.name}: strict writer profile metadata",
        )
        require(len(obj.data.vertices) == metadata["geometry"]["vertex_count"], f"{obj.name}: vertices")
        require(len(obj.data.polygons) == metadata["geometry"]["triangle_count"], f"{obj.name}: triangles")
        rows.append({
            "source": f"{folder.name}/{Path(obj['mr_source_path']).name}",
            "revision": obj["mr_dx_revision"],
            "role": obj["mr_resource_role"],
            "vertices": len(obj.data.vertices),
            "triangles": len(obj.data.polygons),
            "validation_profile": metadata["validation"]["validation_profile"],
            "warnings": metadata["blender"]["import_warnings"],
        })
    return rows


def main():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(values) != 4:
        raise SystemExit("usage after --: <addon.zip> <demo-input-root> <retail-vehicle-root> <report.json>")
    archive, demo_root, retail_root, report_path = map(Path, values)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    result = bpy.ops.preferences.addon_install(filepath=str(archive), overwrite=True)
    require(result == {"FINISHED"}, f"add-on install failed: {result}")
    result = bpy.ops.preferences.addon_enable(module="master_rallye_io")
    require(result == {"FINISHED"}, f"add-on enable failed: {result}")
    require(hasattr(bpy.ops.import_scene, "master_rallye_dx"), "single DX operator missing")
    require(hasattr(bpy.ops.import_scene, "master_rallye_vehicle"), "vehicle-folder operator missing")

    demo_samples = (
        (demo_root / "8.4.1_Trooper", 127),
        (demo_root / "9.3.1_Trooper", 131),
        (demo_root / "!other_research" / "9.10.0_dxForester", 135),
    )
    retail_samples = ((retail_root / "Astero", 135),)
    report = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "demo_folder_imports": [
            {"folder": folder.name, "resources": import_folder(folder, revision)}
            for folder, revision in demo_samples
        ],
        "retail_folder_imports": [
            {"folder": folder.name, "resources": import_folder(folder, revision)}
            for folder, revision in retail_samples
        ],
        "uv_policy": "direct-v",
        "custom_normal_api_applied": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes((json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print("R5V_D_PACKAGED_ADDON_SMOKE_PASS", json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
