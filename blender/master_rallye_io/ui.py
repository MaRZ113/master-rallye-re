"""Small read-only inspection panel for imported Master Rallye objects."""
from __future__ import annotations

import json
from pathlib import Path

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .blender_collision import set_collision_visibility
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


class OBJECT_OT_master_rallye_collision_visibility(bpy.types.Operator):
    bl_idname = "object.master_rallye_collision_visibility"
    bl_label = "Set Master Rallye Collision Visibility"
    bl_options = {"INTERNAL"}

    visible: BoolProperty(default=True)

    def execute(self, context):
        obj = context.object
        owner = obj.get("mr_source_path") if obj else None
        if not owner:
            self.report({"ERROR"}, "Active object has no Master Rallye source path")
            return {"CANCELLED"}
        count = set_collision_visibility(owner, self.visible)
        self.report({"INFO"}, f"Updated {count} collision helper objects")
        return {"FINISHED"}


def _selected_texture(context):
    obj=context.object
    if not obj or obj.type!="MESH" or not obj.active_material:
        raise ValueError("Select an imported mesh material")
    source=obj.active_material.get("mr_dxt_source")
    if not source:
        raise ValueError("selected material has no resolved primary DXT")
    return Path(source)


class OBJECT_OT_master_rallye_export_texture(bpy.types.Operator, ExportHelper):
    bl_idname="object.master_rallye_export_texture"
    bl_label="Export Selected MR Texture to PNG"
    filename_ext=".png"
    filter_glob:StringProperty(default="*.png",options={"HIDDEN"})
    def execute(self,context):
        try:
            from .library import parse_dxt, write_png
            source=_selected_texture(context)
            output=Path(self.filepath).resolve()
            if output==source.resolve():
                raise ValueError("cannot overwrite source texture")
            write_png(parse_dxt(source),output)
            self.report({"INFO"},f"Exported upright PNG: {output}")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"},str(error))
            return {"CANCELLED"}


class OBJECT_OT_master_rallye_replace_texture(bpy.types.Operator, ImportHelper):
    bl_idname="object.master_rallye_replace_texture"
    bl_label="Replace MR Texture from PNG"
    filename_ext=".png"
    filter_glob:StringProperty(default="*.png",options={"HIDDEN"})
    def execute(self,context):
        try:
            from .library import replace_texture
            source=_selected_texture(context)
            obj=context.object
            staging=obj.get("mr_staging_directory")
            if not staging:
                raise ValueError("Set MR staging directory on the object first")
            output=Path(staging).resolve()/source.name
            result=replace_texture(source,Path(self.filepath),output,expected_source_sha256=obj.active_material.get("mr_dxt_sha256",""))
            obj["mr_staged_texture_json"]=json.dumps({**json.loads(obj.get("mr_staged_texture_json","{}")),source.name:str(output)})
            count=(result.get("reverse_dependencies") or {}).get("count",0)
            self.report({"INFO"},f"Staged {source.name} to {output}; {count} draw bindings affected")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"},str(error))
            return {"CANCELLED"}


class OBJECT_OT_master_rallye_validate_texture(bpy.types.Operator, ImportHelper):
    bl_idname="object.master_rallye_validate_texture"
    bl_label="Validate MR Texture Replacement"
    filename_ext=".png"
    filter_glob:StringProperty(default="*.png",options={"HIDDEN"})
    def execute(self,context):
        try:
            from .library import decode_rgba_png, parse_dxt
            source=_selected_texture(context)
            template=parse_dxt(source)
            width,height,_=decode_rgba_png(Path(self.filepath).read_bytes())
            if (width,height)!=(template.width,template.height):
                raise ValueError(f"PNG size {width}x{height} differs from DXT {template.width}x{template.height}")
            self.report({"INFO"},f"Valid same-size RGBA8 PNG for {source.name}")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"},str(error))
            return {"CANCELLED"}


class OBJECT_OT_master_rallye_texture_users(bpy.types.Operator):
    bl_idname="object.master_rallye_texture_users"
    bl_label="Show MR Texture Users"
    def execute(self,context):
        try:
            from .library import texture_users
            source=_selected_texture(context)
            result=texture_users(source.parent,source.name)
            print(json.dumps(result,indent=2))
            self.report({"INFO"},f"{source.name}: {result['count']} draw bindings (details in console)")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"},str(error))
            return {"CANCELLED"}


class OBJECT_OT_master_rallye_material_state(bpy.types.Operator):
    bl_idname="object.master_rallye_material_state"
    bl_label="Stage MR Material State"
    draw_id:IntProperty()
    field:StringProperty()
    enabled:BoolProperty()
    def execute(self,context):
        obj=context.object
        try:
            metadata=json.loads(obj["mr_metadata_json"])
            draw=metadata["draws"][self.draw_id]
            if draw["draw_id"]!=self.draw_id or draw["record_tag"] not in (2,7,8):
                raise ValueError("selected draw cannot be patched")
            if self.field=="alpha":
                if bytes.fromhex(draw["flags_0x20_hex"])[1]:
                    raise ValueError("alpha-test draw requires separate runtime evidence")
                key="mr_material_alpha_edits_json"
            elif self.field=="env":
                if draw["texture_slots"][1].casefold()=="null":
                    raise ValueError("draw has no existing slot-1 helper")
                key="mr_material_env_edits_json"
            else:
                raise ValueError("unsupported material field")
            edits=json.loads(obj.get(key,"{}"))
            edits[str(self.draw_id)]=bool(self.enabled)
            obj[key]=json.dumps(edits)
            self.report({"INFO"},f"Staged draw {self.draw_id} {self.field}={self.enabled}; export DX to apply")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"},str(error))
            return {"CANCELLED"}


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
        layout.label(text=f"Role: {obj.get('mr_resource_role', 'AUXILIARY')}")
        layout.label(text=f"Position/topology: {status}")
        source = Path(obj.get("mr_source_path", ""))
        layout.label(text=f"Source: {source.name or 'unknown'}")
        grid = layout.grid_flow(columns=2, even_columns=True, align=True)
        grid.label(text="Vertices")
        grid.label(text=str(len(obj.data.vertices)))
        grid.label(text="Triangles")
        grid.label(text=str(len(obj.data.polygons)))
        grid.label(text="Draws")
        grid.label(text=str(obj.get("mr_draw_count", 0)))
        collision = {}
        try:
            metadata = json.loads(obj["mr_metadata_json"])
            group_count = len(metadata.get("groups", []))
            texture_count = sum(
                len(draw.get("texture_slots", [])) for draw in metadata.get("draws", [])
            )
            validation_status = (
                "VALIDATED" if metadata.get("validation", {}).get("validated") else "PARTIAL"
            )
            collision = metadata.get("collision", {})
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
        grid.label(text="Tag 101")
        grid.label(text="present" if collision.get("tag101_present") else "absent")
        if collision.get("tag101_present"):
            hull = collision.get("tag101") or {}
            grid.label(text="Collision bytes")
            grid.label(text=str(hull.get("payload_size", 0)))
            a = hull.get("representation_a", {})
            b = hull.get("representation_b", {})
            grid.label(text="Rep A V/T/F")
            grid.label(text=f"{a.get('vertex_count', 0)}/{a.get('triangle_count', 0)}/{a.get('face_count', 0)}")
            grid.label(text="Rep B V/T/F")
            grid.label(text=f"{b.get('vertex_count', 0)}/{b.get('triangle_count', 0)}/{b.get('face_count', 0)}")
            row = layout.row(align=True)
            show = row.operator("object.master_rallye_collision_visibility", text="Show Collision", icon="HIDE_OFF")
            show.visible = True
            hide = row.operator("object.master_rallye_collision_visibility", text="Hide Collision", icon="HIDE_ON")
            hide.visible = False
        if collision.get("tag101_present") and obj.get("mr_resource_name", "").casefold() == "car.dx":
            edit_box = layout.box()
            edit_box.label(text="Collision authoring: source XYZ", icon="MESH_CUBE")
            edit_box.prop(obj, '["mr_collision_translation"]', text="Translate")
            edit_box.prop(obj, '["mr_collision_scale"]', text="Per-axis scale")
            buttons = edit_box.row(align=True)
            buttons.operator("object.master_rallye_collision_preview", text="Validate / Preview")
            buttons.operator("object.master_rallye_collision_reset", text="Reset")
            edit_box.label(text=f"Status: {obj.get('mr_collision_validation_status', 'SOURCE')}")
            try:
                preview = json.loads(obj.get("mr_collision_preview_json", "{}"))
                edit_box.label(text=f"Center: {preview.get('center', 'source')}")
                edit_box.label(text=f"Radius: {preview.get('radius', 'source')}")
                edit_box.label(text=f"AABB min: {preview.get('minimum', 'source')}")
                edit_box.label(text=f"AABB max: {preview.get('maximum', 'source')}")
            except (ValueError, TypeError):
                pass
            edit_box.label(text=f"Source SHA: {str(obj.get('mr_source_sha256',''))[:16]}...")
        row = layout.row(align=True)
        row.operator("object.master_rallye_print_metadata", icon="CONSOLE")
        row.operator("object.master_rallye_reload_textures", icon="FILE_REFRESH")
        layout.separator()
        if "mr_staging_directory" in obj:
            layout.prop(obj,'["mr_staging_directory"]',text="Staging directory")
        else:
            layout.label(text="Reimport to set staging directory")
        if obj.active_material:
            material=obj.active_material
            slots=json.loads(material.get("mr_texture_slots_json","[]"))
            box=layout.box()
            box.label(text="Selected material (runtime evidence)")
            box.label(text=f"Slot 0: {slots[0] if slots else 'unknown'}")
            box.label(text=f"Slot 1 helper: {slots[1] if len(slots)>1 else 'unknown'}")
            flags=str(material.get("mr_serialized_flags_0x20_hex",""))
            box.label(text=f"Raw flags: {flags}")
            box.label(text=f"Alpha: {'test (experimental)' if material.get('mr_runtime_alpha_test') else 'blend' if material.get('mr_runtime_alpha_enabled') else 'opaque'}")
            box.label(text=f"Env: {'enabled' if int(material.get('mr_serialized_texture_mask',0)) & 4 else 'disabled'}")
            box.label(text="Alpha: executable + M2/M4 runtime")
            box.label(text="Env: executable + M1/M3 runtime")
            if material.get("mr_dxt_source"):
                row=box.row(align=True)
                row.operator("object.master_rallye_export_texture",text="Export PNG")
                row.operator("object.master_rallye_replace_texture",text="Replace PNG")
                row=box.row(align=True)
                row.operator("object.master_rallye_validate_texture",text="Validate PNG")
                row.operator("object.master_rallye_texture_users",text="Show Users")
            if obj.data.polygons and obj.active_material_index < len(obj.data.materials):
                draw_ids=sorted({int(obj.data.attributes["mr_draw_id"].data[p.index].value)
                                 for p in obj.data.polygons if p.material_index==obj.active_material_index})
                if draw_ids:
                    box.label(text=f"Draw IDs: {', '.join(map(str,draw_ids[:8]))}")
                    draw_id=draw_ids[0]
                    buttons=box.row(align=True)
                    off=buttons.operator("object.master_rallye_material_state",text="Alpha Off")
                    off.draw_id=draw_id; off.field="alpha"; off.enabled=False
                    on=buttons.operator("object.master_rallye_material_state",text="Alpha On")
                    on.draw_id=draw_id; on.field="alpha"; on.enabled=True
                    if len(slots)>1 and slots[1].casefold()!="null":
                        buttons=box.row(align=True)
                        off=buttons.operator("object.master_rallye_material_state",text="Env Off")
                        off.draw_id=draw_id; off.field="env"; off.enabled=False
                        on=buttons.operator("object.master_rallye_material_state",text="Env On")
                        on.draw_id=draw_id; on.field="env"; on.enabled=True
        layout.separator()
        topology = layout.box()
        topology.label(text="Topology (experimental)", icon="MESH_DATA")
        selected_draws = set()
        try:
            if obj.mode == "EDIT":
                import bmesh
                bm = bmesh.from_edit_mesh(obj.data)
                draw_layer = bm.faces.layers.int.get("mr_draw_id")
                if draw_layer is not None:
                    selected_draws = {face[draw_layer] for face in bm.faces if face.select}
            else:
                draw_attr = obj.data.attributes.get("mr_draw_id")
                if draw_attr is not None:
                    selected_draws = {draw_attr.data[face.index].value for face in obj.data.polygons if face.select}
        except Exception:
            selected_draws = set()
        topology.label(text=f"Selected face draw IDs: {', '.join(map(str, sorted(selected_draws))) if selected_draws else 'none'}")
        if "mr_target_draw_id" in obj:
            topology.prop(obj, '["mr_target_draw_id"]', text="Existing draw ID")
        topology.operator("object.master_rallye_assign_draw", text="Assign Selected Faces to MR Draw")
        try:
            draw_metadata = json.loads(obj["mr_metadata_json"])["draws"]
            draw_list = topology.column(align=True)
            for draw in draw_metadata:
                slots = draw.get("texture_slots", [])
                draw_list.label(text=f"{draw['draw_id']}: {slots[0] if slots else 'Null'} / {slots[1] if len(slots)>1 else 'Null'}")
        except Exception:
            topology.label(text="Draw list unavailable")
        topology.operator("export_scene.master_rallye_dx_topology", text="Export DX - Topology Changing (Experimental)", icon="EXPORT")
        bounds_row = layout.row(align=True)
        show_bounds = bounds_row.operator("object.master_rallye_bounds_visibility", text="Show Bounds")
        show_bounds.visible = True
        hide_bounds = bounds_row.operator("object.master_rallye_bounds_visibility", text="Hide Bounds")
        hide_bounds.visible = False
        project_box = layout.box()
        project_box.label(text="Vehicle project", icon="OUTLINER_COLLECTION")
        project_box.operator("import_scene.master_rallye_vehicle", text="Import Vehicle Folder")
        project_box.operator("export_scene.master_rallye_vehicle_project", text="Save Vehicle Project")
        project_box.operator("object.master_rallye_validate_vehicle", text="Validate Vehicle")
        project_box.operator("export_scene.master_rallye_build_vehicle", text="Build Vehicle Mod")
        project_box.label(text=f"Project: {Path(obj.get('mr_vehicle_project_path', '')).name or 'unsaved'}")
        project_box.label(text=f"Validation: {obj.get('mr_vehicle_validation_status', 'not run')}")
        layout.separator()
        layout.operator("export_scene.master_rallye_dx_attributes", text="Export DX - Safe Attributes", icon="EXPORT")
        layout.operator(
            "export_scene.master_rallye_dx_positions",
            text="Export DX — Positions Only",
            icon="EXPORT",
        )


CLASSES = (
    OBJECT_OT_master_rallye_export_texture,
    OBJECT_OT_master_rallye_replace_texture,
    OBJECT_OT_master_rallye_validate_texture,
    OBJECT_OT_master_rallye_texture_users,
    OBJECT_OT_master_rallye_material_state,
    OBJECT_OT_master_rallye_print_metadata,
    OBJECT_OT_master_rallye_reload_textures,
    OBJECT_OT_master_rallye_collision_visibility,
    VIEW3D_PT_master_rallye_resource,
)
