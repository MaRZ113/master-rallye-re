"""Small read-only inspection panel for imported Master Rallye objects."""
from __future__ import annotations

import json
from pathlib import Path

import bpy

from .blender_metadata import refresh_authoring_status


class OBJECT_OT_master_rallye_print_metadata(bpy.types.Operator):
    bl_idname = "object.master_rallye_print_metadata"
    bl_label = "Print Master Rallye Metadata"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        obj = context.object
        payload = obj.get("mr_metadata_json") if obj else None
        if not payload:
            self.report({"ERROR"}, "Active object has no Master Rallye metadata")
            return {"CANCELLED"}
        print(json.dumps(json.loads(payload), indent=2, ensure_ascii=False))
        self.report({"INFO"}, "Master Rallye metadata printed to the system console")
        return {"FINISHED"}


class OBJECT_OT_master_rallye_reload_textures(bpy.types.Operator):
    bl_idname = "object.master_rallye_reload_textures"
    bl_label = "Reload Preview Textures"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        count = 0
        for image in bpy.data.images:
            if image.get("mr_dxt_source"):
                try:
                    image.reload()
                    count += 1
                except RuntimeError:
                    pass
        self.report({"INFO"}, f"Reloaded {count} Master Rallye preview images")
        return {"FINISHED"}


class VIEW3D_PT_master_rallye_resource(bpy.types.Panel):
    bl_label = "Master Rallye Resource"
    bl_idname = "VIEW3D_PT_master_rallye_resource"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Master Rallye"

    @classmethod
    def poll(cls, context):
        return context.object is not None and "mr_metadata_json" in context.object

    def draw(self, context):
        obj = context.object
        layout = self.layout
        status = refresh_authoring_status(obj)
        layout.label(text=obj.get("mr_resource_name", obj.name), icon="MESH_DATA")
        layout.label(text=f"Authoring: {status}")
        source = Path(obj.get("mr_source_path", ""))
        layout.label(text=f"Source: {source.name or 'unknown'}")
        grid = layout.grid_flow(columns=2, even_columns=True, align=True)
        grid.label(text="Vertices")
        grid.label(text=str(len(obj.data.vertices)))
        grid.label(text="Triangles")
        grid.label(text=str(len(obj.data.polygons)))
        grid.label(text="Draws")
        grid.label(text=str(obj.get("mr_draw_count", 0)))
        try:
            metadata = json.loads(obj["mr_metadata_json"])
            group_count = len(metadata.get("groups", []))
            texture_count = sum(
                len(draw.get("texture_slots", [])) for draw in metadata.get("draws", [])
            )
            validation_status = (
                "VALIDATED" if metadata.get("validation", {}).get("validated") else "PARTIAL"
            )
        except (AttributeError, ValueError, TypeError):
            group_count = texture_count = 0
            validation_status = "UNKNOWN"
        grid.label(text="Validation")
        grid.label(text=validation_status)
        grid.label(text="Groups")
        grid.label(text=str(group_count))
        grid.label(text="UV sets")
        grid.label(text=str(obj.get("mr_uv_set_count", 0)))
        grid.label(text="Texture bindings")
        grid.label(text=str(texture_count))
        grid.label(text="Display normals")
        grid.label(text=str(obj.get("mr_display_normal_strategy", "unknown")))
        row = layout.row(align=True)
        row.operator("object.master_rallye_print_metadata", icon="CONSOLE")
        row.operator("object.master_rallye_reload_textures", icon="FILE_REFRESH")
        layout.separator()
        layout.operator(
            "export_scene.master_rallye_dx_positions",
            text="Export DX — Positions Only",
            icon="EXPORT",
        )


CLASSES = (
    OBJECT_OT_master_rallye_print_metadata,
    OBJECT_OT_master_rallye_reload_textures,
    VIEW3D_PT_master_rallye_resource,
)
