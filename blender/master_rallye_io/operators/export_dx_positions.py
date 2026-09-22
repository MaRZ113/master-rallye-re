"""Export imported mesh positions by patching the original DX template."""
from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from ..blender_export import export_dx_positions


class EXPORT_SCENE_OT_master_rallye_dx_positions(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.master_rallye_dx_positions"
    bl_label = "Export Master Rallye DX — Positions Only (Experimental)"
    bl_description = (
        "Patch only same-topology vertex positions into the verified original DX template"
    )
    bl_options = {"REGISTER"}

    filename_ext = ".dx"
    filter_glob: StringProperty(default="*.dx", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and "mr_metadata_json" in obj

    def execute(self, context):
        try:
            result = export_dx_positions(context.active_object, Path(self.filepath))
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Positions-only DX written: {len(result.patch.changes)} changed vertices, "
            f"{result.patch.diff.changed_byte_count} changed bytes",
        )
        return {"FINISHED"}
