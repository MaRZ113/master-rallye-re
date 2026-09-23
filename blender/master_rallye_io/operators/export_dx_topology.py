"""Explicit experimental topology export and existing-draw assignment."""
from __future__ import annotations

import json
from pathlib import Path

import bpy
from bpy.props import IntProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from ..blender_topology_export import export_topology, preview_topology


class OBJECT_OT_master_rallye_assign_draw(bpy.types.Operator):
    bl_idname = "object.master_rallye_assign_draw"
    bl_label = "Assign Selected Faces to MR Draw"
    bl_options = {"REGISTER", "UNDO"}
    draw_id: IntProperty(default=-1)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and "mr_metadata_json" in obj

    def execute(self, context):
        obj = context.active_object
        metadata = json.loads(obj["mr_metadata_json"])
        target = self.draw_id if self.draw_id >= 0 else int(obj.get("mr_target_draw_id", -1))
        if not 0 <= target < len(metadata["draws"]):
            self.report({"ERROR"}, "choose an existing MR draw ID")
            return {"CANCELLED"}
        was_edit = obj.mode == "EDIT"
        if was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")
        try:
            mesh = obj.data
            selected = [polygon for polygon in mesh.polygons if polygon.select]
            if not selected:
                raise ValueError("select at least one face")
            attrs = mesh.attributes
            for name in ("mr_draw_id", "mr_source_triangle", "mr_source_face_valid", "mr_draw_assignment_valid"):
                if attrs.get(name) is None:
                    raise ValueError(f"missing MR face attribute {name}; reimport resource")
            old_ids = [int(attrs["mr_source_triangle"].data[polygon.index].value) for polygon in mesh.polygons]
            counts = {source_id: old_ids.count(source_id) for source_id in set(old_ids) if source_id >= 0}
            for polygon in selected:
                face = polygon.index
                old_draw = int(attrs["mr_draw_id"].data[face].value)
                source_id = old_ids[face]
                generated = old_draw != target or (source_id >= 0 and counts.get(source_id, 0) > 1)
                attrs["mr_draw_id"].data[face].value = target
                attrs["mr_group_id"].data[face].value = metadata["draws"][target]["top_level_index"]
                attrs["mr_draw_assignment_valid"].data[face].value = True
                if generated:
                    attrs["mr_source_face_valid"].data[face].value = False
                    attrs["mr_source_triangle"].data[face].value = -1
                polygon.material_index = int(obj.get(f"mr_draw_material_slot_{target}", polygon.material_index))
            source_used_points = {
                mesh.loops[loop_id].vertex_index
                for polygon in mesh.polygons if attrs["mr_source_face_valid"].data[polygon.index].value
                for loop_id in polygon.loop_indices
            }
            generated_attr = attrs.get("mr_generated_vertex")
            parent_attr = attrs.get("mr_parent_source_vertex")
            valid_attr = attrs.get("mr_source_vertex_valid")
            source_attr = attrs.get("mr_source_vertex")
            if all(item is not None for item in (generated_attr, parent_attr, valid_attr, source_attr)):
                for polygon in selected:
                    if attrs["mr_source_face_valid"].data[polygon.index].value:
                        continue
                    for loop_id in polygon.loop_indices:
                        point = mesh.loops[loop_id].vertex_index
                        if point not in source_used_points and valid_attr.data[point].value:
                            parent_attr.data[point].value = source_attr.data[point].value
                            generated_attr.data[point].value = True
                            valid_attr.data[point].value = False
            mesh.update()
            self.report({"INFO"}, f"Assigned {len(selected)} faces to existing draw {target}")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        finally:
            if was_edit:
                bpy.ops.object.mode_set(mode="EDIT")


class EXPORT_SCENE_OT_master_rallye_dx_topology(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.master_rallye_dx_topology"
    bl_label = "Export Master Rallye DX - Topology Changing (Experimental)"
    bl_description = "Rebuild existing draw render topology; collision/material identities are preserved"
    bl_options = {"REGISTER"}
    filename_ext = ".dx"
    filter_glob: StringProperty(default="*.dx", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and "mr_metadata_json" in obj

    def invoke(self, context, event):
        try:
            _, rebuilt, compiled = preview_topology(context.active_object)
            self._summary = (rebuilt, compiled)
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        summary = getattr(self, "_summary", None)
        if summary is None:
            return
        rebuilt, compiled = summary
        column = self.layout.column(align=True)
        column.label(text=f"Vertices: {rebuilt.source_vertex_count} -> {rebuilt.output_vertex_count}")
        column.label(text=f"Triangles: {rebuilt.source_triangle_count} -> {rebuilt.output_triangle_count}")
        column.label(text=f"New geometry vertices: {compiled.generated_for_new_geometry}")
        column.label(text=f"UV/normal/color/draw splits: {compiled.split_for_uv_seam}/{compiled.split_for_normal_discontinuity}/{compiled.split_for_vertex_color_discontinuity}/{compiled.split_for_draw_boundary}")
        column.label(text=f"Changed draws: {', '.join(map(str, rebuilt.changed_draws)) or 'none'}")
        column.label(text="Collision and original material records preserved")
        warnings = rebuilt.output_model.diagnostics.warnings
        column.label(text=f"Topology warnings: {len(warnings)} (source warnings retained)")
        for warning in warnings[:3]:
            column.label(text=warning[:80])

    def execute(self, context):
        try:
            rebuilt, compiled = export_topology(context.active_object, Path(self.filepath))
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        if hasattr(rebuilt, "source_vertex_count"):
            self.report({"INFO"}, f"Experimental DX: {rebuilt.source_vertex_count}->{rebuilt.output_vertex_count} vertices; {rebuilt.source_triangle_count}->{rebuilt.output_triangle_count} triangles; {compiled.generated_for_new_geometry} generated; changed draws {rebuilt.changed_draws}")
        else:
            self.report({"INFO"}, "Same topology: exported through the proven safe attribute patcher")
        return {"FINISHED"}


CLASSES = (OBJECT_OT_master_rallye_assign_draw, EXPORT_SCENE_OT_master_rallye_dx_topology)
