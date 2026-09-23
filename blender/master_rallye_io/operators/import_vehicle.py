"""Import all discovered DX resources in one vehicle directory."""
from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import BoolProperty, StringProperty

from ..blender_materials import PreviewMaterialCache
from ..blender_mesh import create_collection, import_dx_resource


class IMPORT_SCENE_OT_master_rallye_vehicle(bpy.types.Operator):
    bl_idname = "import_scene.master_rallye_vehicle"
    bl_label = "Import Master Rallye Vehicle Folder"
    bl_description = "Discover and import every DX resource directly in a vehicle folder"
    bl_options = {"REGISTER", "UNDO"}

    directory: StringProperty(name="Vehicle folder", subtype="DIR_PATH")
    import_sidecar: BoolProperty(name="Import TXT sidecar metadata", default=True)
    load_textures: BoolProperty(name="Load DXT preview textures", default=True)
    strict_validation: BoolProperty(name="Require validated geometry", default=True)
    show_collision: BoolProperty(name="Show collision overlays", default=True)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        folder = Path(self.directory).resolve()
        if not folder.is_dir():
            self.report({"ERROR"}, f"Not a directory: {folder}")
            return {"CANCELLED"}
        resources = sorted(folder.glob("*.dx"), key=lambda item: item.name.casefold())
        if not resources:
            self.report({"ERROR"}, f"No DX resources found in {folder}")
            return {"CANCELLED"}

        parent = create_collection(f"Master Rallye - {folder.name}")
        cache = PreviewMaterialCache(folder, load_textures=self.load_textures)
        imported = []
        warnings = []
        for source in resources:
            resource_collection = create_collection(source.stem, parent=parent)
            try:
                result = import_dx_resource(
                    source,
                    resource_collection,
                    object_name=source.stem,
                    import_sidecar=self.import_sidecar,
                    load_textures=self.load_textures,
                    strict=self.strict_validation,
                    material_cache=cache,
                    show_collision=self.show_collision,
                )
                imported.append(result.object)
                result.object["mr_resource_role"] = {
                    "car.dx": "RACE BODY", "complete.dx": "PRESENTATION",
                    "wheel.dx": "WHEEL TEMPLATE"
                }.get(source.name.casefold(), "AUXILIARY")
                warnings.extend(result.warnings)
                for warning in result.warnings:
                    print(f"[Master Rallye] {source.name}: {warning}")
            except Exception as error:
                if self.strict_validation:
                    self.report({"ERROR"}, f"{source.name}: {error}")
                    return {"CANCELLED"}
                warnings.append(f"{source.name}: {error}")

        bpy.ops.object.select_all(action="DESELECT")
        for obj in imported:
            obj.select_set(True)
        if imported:
            context.view_layer.objects.active = imported[0]
        self.report(
            {"WARNING"} if warnings else {"INFO"},
            f"Imported {len(imported)}/{len(resources)} resources from {folder.name}; "
            f"{len(warnings)} warnings",
        )
        return {"FINISHED"}
