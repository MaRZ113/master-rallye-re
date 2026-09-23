"""Import one Master Rallye vehicle DX resource."""
from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy_extras.io_utils import ImportHelper

from ..blender_mesh import create_collection, import_dx_resource


class IMPORT_SCENE_OT_master_rallye_dx(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.master_rallye_dx"
    bl_label = "Import Master Rallye DX"
    bl_description = "Import one Master Rallye vehicle DX as an editable mesh"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".dx"
    filter_glob: StringProperty(default="*.dx", options={"HIDDEN"})
    import_sidecar: BoolProperty(name="Import TXT sidecar metadata", default=True)
    load_textures: BoolProperty(name="Load DXT preview textures", default=True)
    strict_validation: BoolProperty(name="Require validated geometry", default=True)
    show_collision: BoolProperty(name="Show collision overlay", default=True)
    collection_name: StringProperty(name="Collection name", default="")

    def execute(self, context):
        source = Path(self.filepath)
        name = self.collection_name.strip() or f"Master Rallye - {source.stem}"
        collection = create_collection(name)
        try:
            result = import_dx_resource(
                source,
                collection,
                object_name=source.stem,
                import_sidecar=self.import_sidecar,
                load_textures=self.load_textures,
                strict=self.strict_validation,
                show_collision=self.show_collision,
            )
        except Exception as error:
            bpy.data.collections.remove(collection)
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        bpy.ops.object.select_all(action="DESELECT")
        result.object.select_set(True)
        context.view_layer.objects.active = result.object
        self.report(
            {"WARNING"} if result.warnings else {"INFO"},
            f"Imported {source.name}: {len(result.object.data.vertices)} vertices, "
            f"{len(result.object.data.polygons)} triangles, {len(result.warnings)} warnings",
        )
        return {"FINISHED"}
