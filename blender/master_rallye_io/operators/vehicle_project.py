"""Vehicle SDK project and limited collision operations for Blender."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from ..library import parse_dx, transform_blender_positions
from ..blender_collision import set_collision_visibility

try:
    from master_rallye.collision_scale import scale_dx_collision
    from master_rallye.collision_writer import patch_dx_collision_translation
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.vehicle_project import VehicleProject, validate_vehicle, build_vehicle_mod
except ModuleNotFoundError:
    from ..vendor.master_rallye.collision_scale import scale_dx_collision
    from ..vendor.master_rallye.collision_writer import patch_dx_collision_translation
    from ..vendor.master_rallye.dx import parse_dx_bytes
    from ..vendor.master_rallye.vehicle_project import VehicleProject, validate_vehicle, build_vehicle_mod


def _active(context):
    obj = context.active_object
    if obj is None or "mr_source_path" not in obj:
        raise ValueError("select an imported Master Rallye resource")
    return obj


def _vehicle_objects(folder: Path):
    for obj in bpy.data.objects:
        if "mr_source_path" not in obj:
            continue
        source = Path(obj["mr_source_path"]).resolve()
        if source.parent == folder and source.name.casefold() in {"car.dx", "complete.dx", "wheel.dx"}:
            yield obj


def _refresh_collision_preview(owner, model):
    hull = model.collision.convex_hull
    if hull is None:
        return
    for helper in bpy.data.objects:
        if helper.get("mr_collision_owner") != owner:
            continue
        role = helper.get("mr_collision_role")
        if role == "base-radius-preview":
            helper.location = transform_blender_positions(hull.base_geometry.vertices)[0]
            helper.empty_display_size = hull.base_scalar
        elif role in {"representation-a", "representation-b"}:
            geometry = (hull.representation_a if role == "representation-a" else hull.representation_b).geometry_a
            old_mesh = helper.data
            mesh = bpy.data.meshes.new(f"{helper.name} scaled preview")
            mesh.from_pydata(transform_blender_positions(geometry.vertices), [], geometry.triangles)
            mesh.update(calc_edges=True)
            helper.data = mesh
            if old_mesh and old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)


class OBJECT_OT_master_rallye_bounds_visibility(bpy.types.Operator):
    bl_idname = "object.master_rallye_bounds_visibility"
    bl_label = "Show / Hide Marker-1339 Bounds"
    visible: BoolProperty(default=True)

    def execute(self, context):
        try:
            obj = _active(context)
            owner = str(Path(obj["mr_source_path"]).resolve())
            helpers = [item for item in bpy.data.objects if item.get("mr_bounds_owner") == owner]
            if self.visible and not helpers:
                candidate = Path(obj.get("mr_last_export_path", owner)).resolve()
                path = candidate if candidate.is_file() else Path(owner)
                bounds = parse_dx(path).collision.spatial_bounds_1339
                if bounds is None:
                    raise ValueError("marker-1339 bounds unavailable")
                center = transform_blender_positions((bounds.center,))[0]
                extents = tuple(bounds.maximum[i] - bounds.minimum[i] for i in range(3))
                collection = obj.users_collection[0]
                box = bpy.data.objects.new(f"{obj.name} - Spatial Bounds", None)
                box.empty_display_type = "CUBE"
                box.empty_display_size = 1.0
                box.location = center
                box.scale = (extents[0] / 2, extents[2] / 2, extents[1] / 2)
                box["mr_bounds_owner"] = owner
                box.hide_select = True
                box.hide_render = True
                collection.objects.link(box)
                sphere = bpy.data.objects.new(f"{obj.name} - Spatial Radius", None)
                sphere.empty_display_type = "SPHERE"
                sphere.empty_display_size = bounds.radius
                sphere.location = center
                sphere["mr_bounds_owner"] = owner
                sphere.hide_select = True
                sphere.hide_render = True
                collection.objects.link(sphere)
                helpers = [box, sphere]
            for helper in helpers:
                helper.hide_viewport = not self.visible
            self.report({"INFO"}, f"{'Shown' if self.visible else 'Hidden'} {len(helpers)} bounds helpers")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}


class OBJECT_OT_master_rallye_collision_preview(bpy.types.Operator):
    bl_idname = "object.master_rallye_collision_preview"
    bl_label = "Validate / Preview Collision Transform"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and "mr_source_path" in context.active_object

    def execute(self, context):
        obj = _active(context)
        try:
            source = Path(obj["mr_source_path"]).resolve()
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != obj["mr_source_sha256"]:
                raise ValueError("source DX changed after import")
            scale = tuple(float(v) for v in obj["mr_collision_scale"])
            delta = tuple(float(v) for v in obj["mr_collision_translation"])
            result = scale_dx_collision(data, scale)
            data = result["data"]
            if delta != (0.0, 0.0, 0.0):
                data = patch_dx_collision_translation(data, delta).data
            model = parse_dx_bytes(data)
            hull = model.collision.convex_hull
            if hull is None or model.collision.errors:
                raise ValueError("collision transform did not validate")
            _refresh_collision_preview(str(source), model)
            points = hull.representation_a.geometry_a.vertices
            aabb_min = [min(p[i] for p in points) for i in range(3)]
            aabb_max = [max(p[i] for p in points) for i in range(3)]
            obj["mr_collision_preview_json"] = json.dumps({
                "center": list(hull.base_geometry.vertices[0]), "radius": hull.base_scalar,
                "minimum": aabb_min, "maximum": aabb_max,
                "source_sha256": obj["mr_source_sha256"], "status": "PASS"})
            obj["mr_collision_validation_status"] = "PASS"
            set_collision_visibility(str(source), True)
            self.report({"INFO"}, "Collision transform validated; source DX unchanged")
            return {"FINISHED"}
        except Exception as error:
            obj["mr_collision_validation_status"] = "FAIL"
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}


class OBJECT_OT_master_rallye_collision_reset(bpy.types.Operator):
    bl_idname = "object.master_rallye_collision_reset"
    bl_label = "Reset Collision to Source"
    bl_options = {"REGISTER"}

    def execute(self, context):
        obj = _active(context)
        obj["mr_collision_scale"] = [1.0, 1.0, 1.0]
        obj["mr_collision_translation"] = [0.0, 0.0, 0.0]
        return bpy.ops.object.master_rallye_collision_preview()


class EXPORT_SCENE_OT_master_rallye_vehicle_project(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.master_rallye_vehicle_project"
    bl_label = "Save Master Rallye Vehicle Project"
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        try:
            active = _active(context)
            source = Path(active["mr_source_path"]).resolve()
            folder = source.parent
            output = Path(self.filepath).resolve()
            if (output.exists() or output == source or folder in output.parents
                    or (folder.parent.name.casefold() == "vehicles"
                        and (output == folder.parent or folder.parent in output.parents))):
                raise ValueError("project JSON must be a fresh file outside the source vehicle folder")
            spec = {"vehicle_name": folder.name, "source_vehicle_dir": str(folder),
                    "resources": {}, "texture_replacements": {}}
            objects = list(_vehicle_objects(folder))
            for obj in objects:
                path = Path(obj["mr_source_path"]).resolve()
                entry = {"source_sha256": obj["mr_source_sha256"]}
                candidate = obj.get("mr_last_export_path")
                if candidate:
                    candidate = Path(candidate).resolve()
                    if candidate.is_file() and candidate != path:
                        entry["candidate"] = str(candidate)
                scale = [float(v) for v in obj.get("mr_collision_scale", (1, 1, 1))]
                delta = [float(v) for v in obj.get("mr_collision_translation", (0, 0, 0))]
                if path.name.casefold() == "car.dx":
                    if scale != [1.0, 1.0, 1.0]:
                        entry["collision_scale"] = scale
                    if delta != [0.0, 0.0, 0.0]:
                        entry["collision_translation"] = delta
                spec["resources"][path.name] = entry
                staged = json.loads(obj.get("mr_staged_texture_json", "{}"))
                for name, replacement in staged.items():
                    original = folder / name
                    if original.is_file() and Path(replacement).is_file():
                        spec["texture_replacements"][name] = {
                            "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                            "candidate": str(Path(replacement).resolve())}
            if not spec["resources"]:
                raise ValueError("no imported vehicle resources in active source folder")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
            for obj in objects:
                obj["mr_vehicle_project_path"] = str(output)
            self.report({"INFO"}, f"Saved project with {len(spec['resources'])} DX resources")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}


class OBJECT_OT_master_rallye_validate_vehicle(bpy.types.Operator):
    bl_idname = "object.master_rallye_validate_vehicle"
    bl_label = "Validate Master Rallye Vehicle"

    def execute(self, context):
        try:
            obj = _active(context)
            path = obj.get("mr_vehicle_project_path")
            if not path:
                raise ValueError("save a Vehicle Project JSON first")
            report = validate_vehicle(VehicleProject.load(Path(path)))
            obj["mr_vehicle_validation_status"] = report["status"]
            if report["status"] == "FAIL":
                raise ValueError("; ".join(x["message"] for x in report["diagnostics"]))
            self.report({"WARNING"} if report["status"] == "WARN" else {"INFO"},
                        f"Vehicle {report['status']}: {len(report['compiled'])} edited resources")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}


class EXPORT_SCENE_OT_master_rallye_build_vehicle(bpy.types.Operator):
    bl_idname = "export_scene.master_rallye_build_vehicle"
    bl_label = "Build Master Rallye Vehicle Mod"
    directory: StringProperty(name="Fresh output folder", subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            obj = _active(context)
            path = obj.get("mr_vehicle_project_path")
            if not path:
                raise ValueError("save a Vehicle Project JSON first")
            report = build_vehicle_mod(VehicleProject.load(Path(path)), Path(self.directory))
            self.report({"INFO"}, f"Staged {len(report['files'])} resources in {report['staging_root']}")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}


CLASSES = (
    OBJECT_OT_master_rallye_bounds_visibility,
    OBJECT_OT_master_rallye_collision_preview,
    OBJECT_OT_master_rallye_collision_reset,
    EXPORT_SCENE_OT_master_rallye_vehicle_project,
    OBJECT_OT_master_rallye_validate_vehicle,
    EXPORT_SCENE_OT_master_rallye_build_vehicle,
)
