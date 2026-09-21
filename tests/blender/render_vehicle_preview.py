"""Render ignored Astero previews for manual R2 visual validation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def args_after_separator() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def look_at(camera, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def add_camera(name: str, location: Vector, target: Vector, ortho_scale: float):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    look_at(camera, target)
    return camera


def render(scene, camera, path: Path) -> None:
    scene.camera = camera
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    values = args_after_separator()
    if len(values) != 2:
        raise SystemExit("usage after --: <Astero/complete.dx> <output-directory>")
    source = Path(values[0])
    output = Path(values[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    root = repository_root()
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "blender"))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    import master_rallye_io
    from master_rallye_io.blender_mesh import create_collection, import_dx_resource

    master_rallye_io.register()
    result = import_dx_resource(
        source,
        create_collection("Astero visual validation"),
        object_name="Astero complete",
        import_sidecar=True,
        load_textures=True,
        strict=True,
    )
    obj = result.object

    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    center = (minimum + maximum) * 0.5
    extents = maximum - minimum
    span = max(extents)
    target = Vector((center.x, center.y, minimum.z + extents.z * 0.48))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 660
    scene.render.resolution_y = 390
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("R2 Preview World")
    scene.world.color = (0.035, 0.035, 0.035)

    for rotation, energy in ((Vector((0.4, -0.5, 0.75)), 3.0), (Vector((-0.6, 0.2, 0.5)), 1.5)):
        light_data = bpy.data.lights.new(f"Sun {len(bpy.data.lights)}", "SUN")
        light_data.energy = energy
        light = bpy.data.objects.new(light_data.name, light_data)
        scene.collection.objects.link(light)
        light.rotation_euler = rotation

    side = add_camera(
        "Side",
        Vector((maximum.x + span * 1.7, center.y, target.z)),
        target,
        max(extents.y * 1.18, extents.z * 1.8),
    )
    three_quarter = add_camera(
        "Three Quarter",
        Vector((maximum.x + span * 1.25, minimum.y - span * 1.2, maximum.z + span * 0.42)),
        target,
        span * 1.32,
    )
    render(scene, side, output / "astero-complete-side.png")
    render(scene, three_quarter, output / "astero-complete-three-quarter.png")
    payload = {
        "blender_version": bpy.app.version_string,
        "source_resource": "Astero/complete.dx",
        "vertices": len(obj.data.vertices),
        "triangles": len(obj.data.polygons),
        "materials": len(obj.data.materials),
        "bounds_blender": {"minimum": list(minimum), "maximum": list(maximum)},
        "coordinate_mapping": "(X, -Z, Y)",
        "scale": 1.0,
        "png_rows": "flip-vertical",
        "uv_policy": "flip-v",
        "outputs": ["astero-complete-side.png", "astero-complete-three-quarter.png"],
    }
    (output / "render-report.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("R2_ASTERO_RENDER_PASS", json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
