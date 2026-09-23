"""R4E same-topology attribute export operator."""
from pathlib import Path
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
from ..blender_export import export_dx_attributes

class EXPORT_SCENE_OT_master_rallye_dx_attributes(bpy.types.Operator, ExportHelper):
    bl_idname="export_scene.master_rallye_dx_attributes"
    bl_label="Export Master Rallye DX - Safe Attributes"
    bl_description="Patch positions, source normals, UVs, raw vertex colors and approved material bytes"
    bl_options={"REGISTER"}
    filename_ext=".dx"
    filter_glob:StringProperty(default="*.dx",options={"HIDDEN"})
    @classmethod
    def poll(cls,context):
        obj=context.active_object
        return obj is not None and obj.type=="MESH" and "mr_metadata_json" in obj
    def execute(self,context):
        try:
            result=export_dx_attributes(context.active_object,Path(self.filepath))
        except Exception as error:
            self.report({"ERROR"},str(error))
            return {"CANCELLED"}
        self.report({"INFO"},f"DX {result.status}: {result.patch.diff.changed_byte_count} changed bytes")
        return {"FINISHED"}
