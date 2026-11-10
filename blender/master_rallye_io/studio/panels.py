"""Course Studio user interface: one sidebar tab with nine sections."""
from __future__ import annotations

import bpy

from . import catalog, convert as C, jobs
from .core.materials import SURFACE_TABLE
from .props import SECTIONS

CATEGORY = "MR Course Studio"


def _s(context):
    return context.scene.mr_studio


class _Base:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY


class MR_UL_findings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon = {"error": "CANCEL", "warning": "ERROR", "info": "INFO"}.get(item.severity, "DOT")
        row = layout.row(align=True)
        op = row.operator("mr.select_finding", text="", icon="VIEWZOOM", emboss=False)
        op.index = index
        row.label(text=f"[{item.category}] {item.message}", icon=icon)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        s = _s(context)
        flags = []
        for it in items:
            ok = (s.filter_severity == "ALL" or it.severity == s.filter_severity)
            if self.filter_name and self.filter_name.lower() not in it.message.lower():
                ok = False
            flags.append(self.bitflag_filter_item if ok else 0)
        order = sorted(range(len(items)), key=lambda i: {"error": 0, "warning": 1, "info": 2}.get(items[i].severity, 3))
        return flags, [order.index(i) for i in range(len(items))]


class MR_UL_materials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = item.material
        if mat is None:
            layout.label(text="(empty slot)")
            return
        row = layout.row()
        row.label(text=mat.mr.label or mat.name, icon_value=layout.icon(mat))
        row.label(text=f"{mat.mr.shader} / {mat.mr.surface if mat.mr.surface != 'NONE' else '-'}")


class MR_PT_studio(_Base, bpy.types.Panel):
    bl_label = "Master Rallye Course Studio"
    bl_idname = "MR_PT_studio"

    def draw(self, context):
        s = _s(context)
        layout = self.layout
        grid = layout.grid_flow(row_major=True, columns=5, even_columns=True, align=True)
        for ident, name, desc, icon, _ in SECTIONS:
            op = grid.operator("mr.section", text=name if context.region.width > 360 else "", icon=icon,
                               depress=s.section == ident)
            op.section = ident
        if s.busy:
            box = layout.box()
            box.label(text=s.busy, icon="TIME")
            box.prop(s, "progress", text="Progress (Esc cancels)", slider=True)
        if bpy.data.collections.get(C.ROOT_COLLECTION) is None and s.section != "PROJECT":
            layout.label(text="No course yet: Project > New Course or Open", icon="INFO")


def _section_panel(ident):
    class P(_Base, bpy.types.Panel):
        bl_parent_id = "MR_PT_studio"
        bl_options = {"HIDE_HEADER"}

        @classmethod
        def poll(cls, context):
            return _s(context).section == ident
    return P


class MR_PT_project(_section_panel("PROJECT")):
    bl_label = "Project"
    bl_idname = "MR_PT_project"

    def draw(self, context):
        s = _s(context)
        layout = self.layout
        col = layout.column(align=True)
        col.operator("mr.new_course", icon="ADD")
        row = col.row(align=True)
        row.operator("mr.open_project", text="Open Project", icon="FILE_FOLDER")
        row.operator("mr.save_project", text="Save", icon="FILE_TICK")
        row.operator("mr.save_project", text="Save As", icon="DUPLICATE").save_as = True
        if s.project_dirty:
            layout.label(text="Unsaved course changes (saved with the .blend)", icon="ERROR")
        box = layout.box()
        box.label(text="Edit an original course", icon="WORLD")
        root = C.resource_root(context)
        if root is None:
            box.label(text="Game resources not found", icon="ERROR")
        else:
            box.template_icon_view(context.window_manager, "mr_retail_choice", show_labels=True, scale=5.0)
            stem = context.window_manager.mr_retail_choice
            box.label(text=catalog.readable(stem))
            op = box.operator("mr.open_retail", text="Open as New Course", icon="IMPORT")
            op.race = stem
            box.label(text="The original files are never changed", icon="LOCKED")
        box = layout.box()
        box.label(text="Course", icon="PROPERTIES")
        box.prop(s, "course_name")
        box.prop(s, "course_title")
        box.prop(s, "project_dir")
        box.prop(s, "resource_root")
        if root is not None:
            box.label(text=f"Resources: {root}", icon="CHECKMARK")
        layout.operator("mr.import_geometry", text="Import OBJ / FBX / glTF", icon="IMPORT")
        info = C.meta(context.scene).get("provenance") or {}
        if info.get("kind") == "retail":
            layout.label(text=f"Derived from {catalog.readable(info.get('race', ''))}", icon="LINKED")


class MR_PT_terrain(_section_panel("TERRAIN")):
    bl_label = "Terrain"
    bl_idname = "MR_PT_terrain"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("mr.add_terrain_grid", icon="MESH_GRID")
        col.operator("mr.import_geometry", text="Import Terrain", icon="IMPORT").role = "terrain"
        row = layout.row(align=True)
        row.operator("object.mode_set", text="Edit", icon="EDITMODE_HLT").mode = "EDIT"
        row.operator("object.mode_set", text="Sculpt", icon="SCULPTMODE_HLT").mode = "SCULPT"
        row.operator("object.mode_set", text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
        box = layout.box()
        box.label(text="Road and shape", icon="MOD_SMOOTH")
        box.operator("mr.carve_road", icon="CURVE_PATH")
        box.operator("mr.bake_lighting", icon="LIGHT_SUN")
        box = layout.box()
        box.label(text="Join and split", icon="AUTOMERGE_ON")
        box.operator("mr.merge_terrain", icon="AUTOMERGE_ON")
        box.operator("mr.align_seam", icon="SNAP_EDGE")
        box.operator("mr.find_gaps", icon="VIEWZOOM")
        box.operator("mr.split_terrain", icon="MOD_EXPLODE")
        layout.label(text="Set role of selection:")
        grid = layout.grid_flow(columns=2, align=True)
        for role, text in (("terrain", "Terrain"), ("terrain_hidden", "Invisible ground"), ("visual", "Visual only"),
                           ("collision", "Collision"), ("water", "Water"), ("NONE", "Exclude")):
            grid.operator("mr.set_role", text=text).role = role


class MR_PT_objects(_section_panel("OBJECTS")):
    bl_label = "Objects"
    bl_idname = "MR_PT_objects"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Add at 3D cursor:")
        grid = layout.grid_flow(columns=3, align=True)
        for key, text in (("HOUSE", "Building"), ("WALL", "Wall"), ("BARRIER", "Barrier"), ("ROCK", "Rock"),
                          ("CRATE", "Crate")):
            grid.operator("mr.add_object", text=text).preset = key
        col = layout.column(align=True)
        col.operator("mr.import_geometry", text="Import Object", icon="IMPORT").role = "visual"
        row = col.row(align=True)
        row.operator("mr.make_proxy", text="Hull Collision", icon="MESH_ICOSPHERE").kind = "hull"
        row.operator("mr.make_proxy", text="Box Collision", icon="MESH_CUBE").kind = "box"
        col.operator("mr.add_blocker", icon="MOD_PHYSICS")
        col.operator("mr.add_sound", icon="SPEAKER")
        box = layout.box()
        box.label(text="Physical objects (Renderer module)", icon="PHYSICS")
        grid = box.grid_flow(columns=2, align=True)
        for key, text in (("haybale", "Hay bale"), ("tumblweed", "Tumbleweed"), ("checkpoint", "Barrel"),
                          ("SELECTED", "Selected mesh")):
            grid.operator("mr.add_physical", text=text).kind = key
        box.label(text="Optional: the course runs without the Renderer, then they are absent", icon="INFO")
        objs = C.studio_objects("MESH")
        layout.label(text=f"{sum(o.mr.role == 'visual' for o in objs)} visual, "
                          f"{sum(o.mr.role == 'collision' for o in objs)} collision objects")


class MR_PT_materials(_section_panel("MATERIALS")):
    bl_label = "Materials"
    bl_idname = "MR_PT_materials"

    def draw(self, context):
        layout = self.layout
        layout.operator_menu_enum("mr.new_material", "preset", text="New Material", icon="ADD")
        obj = context.object
        if obj is None or obj.type != "MESH":
            layout.label(text="Select a course mesh", icon="INFO")
            return
        layout.template_list("MR_UL_materials", "", obj, "material_slots", obj, "active_material_index", rows=4)
        mat = obj.active_material
        if mat is None:
            return
        p = mat.mr
        box = layout.box()
        box.prop(p, "label")
        row = box.row(align=True)
        row.template_ID(p, "base_image", open="image.open")
        box.operator("mr.load_texture", text="Load / Replace Texture", icon="FILE_IMAGE")
        if p.base_image is not None:
            w, h = p.base_image.size
            box.label(text=f"{w} x {h}" + ("" if (w & (w - 1)) == 0 and (h & (h - 1)) == 0
                                             else " (conformed to a power of two on build)"))
        row = box.row(align=True)
        row.operator("mr.export_texture", text="Export PNG", icon="EXPORT")
        row.operator("mr.texture_users", text="Users", icon="LINKED")
        box.prop(p, "shader")
        box.prop(p, "surface")
        if p.surface != "NONE":
            q, rest, fr, track, solid = SURFACE_TABLE[p.surface]
            box.label(text=f"Game physics: friction {fr:.2f}, bounce {rest:.2f}, "
                           f"{'solid' if solid else 'NOT solid'}", icon="PHYSICS")
        box.prop(p, "alpha")
        box.prop(p, "clamp")
        row = box.row()
        row.prop(p, "mip")
        if p.shader == "ground":
            row.prop(p, "noise", text="Detail")
        if p.shader == "metal":
            box.prop(p, "secondary_key")
        if p.shader == "waterall":
            box.prop(p, "scroll")
        if p.native:
            box.label(text="Original name kept while unchanged", icon="LOCKED")
        row = layout.row(align=True)
        row.operator("object.material_slot_assign", text="Assign to Faces")
        row.operator("mr.select_material_faces", text="Select Faces")


class MR_PT_collision(_section_panel("COLLISION")):
    bl_label = "Collision"
    bl_idname = "MR_PT_collision"

    def draw(self, context):
        s = _s(context)
        layout = self.layout
        state = {"NONE": ("Collision not built yet", "INFO"), "DIRTY": ("Terrain changed: rebuild collision", "ERROR"),
                 "OK": ("Collision is up to date", "CHECKMARK")}[s.collision_state]
        layout.label(text=state[0], icon=state[1])
        if s.collision_summary:
            layout.label(text=s.collision_summary)
        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("mr.build_collision", text="Generate / Rebuild Collision", icon="FILE_REFRESH")
        col = layout.column(align=True)
        col.operator("mr.preview_collision", icon="HIDE_OFF")
        col.prop(s, "preview_radius")
        col.operator("mr.collision_diff", icon="ARROW_LEFTRIGHT")
        col.operator("mr.probe_cursor", icon="SNAP_INCREMENT")
        layout.prop(s, "probe_spacing")
        layout.prop(s, "collision_skirt")
        box = layout.box()
        box.label(text="Collision geometry", icon="MOD_PHYSICS")
        box.operator("mr.add_blocker", icon="MESH_CUBE")
        row = box.row(align=True)
        row.operator("mr.make_proxy", text="Hull Proxy").kind = "hull"
        row.operator("mr.make_proxy", text="Box Proxy").kind = "box"
        box.operator("mr.set_role", text="Selected -> Collision only").role = "collision"


class MR_PT_markers(_section_panel("MARKERS")):
    bl_label = "Markers"
    bl_idname = "MR_PT_markers"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("mr.add_area", text="Place Start", icon="TRIA_RIGHT").kind = "START"
        row.operator("mr.add_area", text="Place Finish", icon="SNAP_FACE").kind = "FINISH"
        col = layout.column(align=True)
        col.operator("mr.add_checkpoint", icon="ADD")
        col.operator("mr.place_checkpoints", icon="PARTICLE_POINT")
        col.operator("mr.renumber_checkpoints", icon="SORTSIZE")
        col.operator("mr.snap_markers", icon="SNAP_ON")
        col.operator("mr.reverse_course", icon="ARROW_LEFTRIGHT")
        cps = sorted(C.studio_objects("CHECKPOINT"), key=lambda o: o.mr.order)
        box = layout.box()
        box.label(text=f"{len(cps)} checkpoints (native timed gates)", icon="FLAG")
        for o in cps:
            r = box.row(align=True)
            r.label(text=f"{o.mr.order + 1}. {o.name}")
            r.label(text=f"r {o.scale.x:.0f} m, +{o.mr.extra_time:.0f} s")
        s = _s(context)
        layout.prop(s, "show_zones")


class MR_PT_routes(_section_panel("ROUTES")):
    bl_label = "Routes & AI"
    bl_idname = "MR_PT_routes"

    def draw(self, context):
        s = _s(context)
        layout = self.layout
        col = layout.column(align=True)
        col.operator("mr.new_route", icon="CURVE_PATH")
        row = col.row(align=True)
        row.operator("mr.route_tool", text="Smooth").action = "SMOOTH"
        row.operator("mr.route_tool", text="Resample").action = "RESAMPLE"
        row.operator("mr.route_tool", text="Reverse").action = "REVERSE"
        col.operator("mr.snap_markers", text="Snap Route to Terrain", icon="SNAP_ON")
        col.operator("mr.check_route", icon="CHECKMARK")
        col.operator("mr.ai_preview", icon="AUTO")
        routes = C.studio_objects("ROUTE")
        if len(routes) > 1:
            box = layout.box()
            box.label(text="The game uses one AI route; choose it:")
            for r in routes:
                row = box.row()
                row.label(text=r.name, icon="RADIOBUT_ON" if r.mr.route_active else "RADIOBUT_OFF")
                if not r.mr.route_active and context.object == r:
                    row.operator("mr.route_tool", text="Use").action = "ACTIVATE"
        layout.prop(s, "route_spacing")
        box = layout.box()
        box.label(text="Reset limits (player freedom)", icon="MOD_OFFSET")
        box.prop(s, "limits_mode", text="")
        if s.limits_mode == "auto":
            row = box.row(align=True)
            row.prop(s, "limits_inner")
            row.prop(s, "limits_outer")
        box.operator("mr.generate_limits", icon="CURVE_BEZCURVE")
        box.prop(s, "show_limits")
        box = layout.box()
        box.label(text="Pace notes", icon="SORTALPHA")
        box.prop(s, "pacenote_mode", text="")
        box.operator("mr.generate_pacenotes", icon="ADD")


class MR_PT_environment(_section_panel("ENVIRONMENT")):
    bl_label = "Environment"
    bl_idname = "MR_PT_environment"

    def draw(self, context):
        s = _s(context)
        layout = self.layout
        layout.prop(s, "environment_template")
        layout.label(text="Sky, weather, sounds, cameras and HUD come from this scene", icon="INFO")
        layout.prop(s, "time_to_first_checkpoint")
        layout.prop(s, "percentage_time_change")
        layout.prop(s, "keep_template_sounds")
        layout.prop(s, "sun_direction")
        layout.operator("mr.add_sound", icon="SPEAKER")
        layout.prop(s, "show_overlays")


class MR_PT_build(_section_panel("BUILD")):
    bl_label = "Build"
    bl_idname = "MR_PT_build"

    def draw(self, context):
        s = _s(context)
        layout = self.layout
        layout.prop(s, "course_title")
        layout.prop(s, "course_key")
        row = layout.row(align=True)
        row.prop(s, "menu_group")
        row.prop(s, "menu_position")
        layout.prop(s, "build_output")
        layout.prop(s, "cap2_input")
        layout.prop(s, "make_package")
        col = layout.column(align=True)
        col.scale_y = 1.4
        col.operator("mr.validate", icon="CHECKMARK")
        col.operator("mr.build_course", icon="EXPORT")
        row = layout.row(align=True)
        row.operator("mr.open_folder", icon="FILE_FOLDER")
        row.operator("mr.reopen_build", icon="FILE_REFRESH")
        if s.last_build:
            layout.label(text=f"Last build: {s.last_build}")


class MR_PT_problems(_Base, bpy.types.Panel):
    bl_label = "Problems"
    bl_idname = "MR_PT_problems"
    bl_parent_id = "MR_PT_studio"

    @classmethod
    def poll(cls, context):
        return len(_s(context).findings) > 0

    def draw(self, context):
        s = _s(context)
        errors = sum(f.severity == "error" for f in s.findings)
        warnings = sum(f.severity == "warning" for f in s.findings)
        self.layout.label(text=f"{errors} errors, {warnings} warnings, {len(s.findings) - errors - warnings} advice")
        self.layout.prop(s, "filter_severity", expand=True)
        self.layout.template_list("MR_UL_findings", "", s, "findings", s, "findings_index", rows=6)
        if 0 <= s.findings_index < len(s.findings) and s.findings[s.findings_index].hint:
            self.layout.label(text=s.findings[s.findings_index].hint, icon="LIGHT")


class MR_PT_selected(_Base, bpy.types.Panel):
    bl_label = "Selected Course Object"
    bl_idname = "MR_PT_selected"
    bl_parent_id = "MR_PT_studio"

    @classmethod
    def poll(cls, context):
        return context.object is not None and getattr(context.object, "mr", None) is not None and \
            context.object.mr.kind not in ("NONE", "DIAGNOSTIC")

    def draw(self, context):
        obj = context.object
        p = obj.mr
        layout = self.layout
        layout.label(text=obj.name, icon="OBJECT_DATA")
        if p.kind == "MESH":
            layout.prop(p, "role")
            if obj.type == "MESH":
                layout.label(text=f"{len(obj.data.polygons)} faces, {len(obj.data.vertices)} vertices")
            if p.proxy_of:
                layout.label(text=f"Collision proxy of {p.proxy_of}", icon="LINKED")
        elif p.kind == "CHECKPOINT":
            layout.prop(obj, "scale", index=0, text="Radius")
            layout.prop(p, "extra_time")
            layout.prop(p, "order")
            layout.prop(p, "boards")
            if p.boards:
                layout.prop(p, "board_spacing")
        elif p.kind in ("START", "FINISH"):
            layout.prop(obj, "scale", index=0, text="Width")
            layout.prop(obj, "scale", index=1, text="Depth")
            layout.prop(obj, "rotation_euler", index=2, text="Direction")
        elif p.kind == "ROUTE":
            layout.prop(p, "route_active")
            pts = sum(len(sp.points) for sp in obj.data.splines)
            layout.label(text=f"{pts} points (Edit Mode: E extrudes, X deletes)")
        elif p.kind == "PACENOTE":
            layout.prop(p, "note_id")
            layout.prop(p, "note_distance")
        elif p.kind == "SOUND":
            layout.prop(p, "sound_template")
        if p.kind == "PS2PROP" or (p.kind == "MESH" and p.role == "physical"):
            if p.kind == "PS2PROP":
                layout.prop(p, "ps2_model")
            else:
                layout.prop(p, "phys_material")
            layout.prop(p, "mass")
            layout.prop(p, "trigger")
            layout.prop(p, "shadow")
            layout.label(text="Needs the Renderer RigidProps module", icon="INFO")


def _retail_items(self, context):
    root = C.resource_root(context)
    items = []
    for i, (stem, name) in enumerate(catalog.retail_scenes(root)):
        icon = catalog.preview_icon(root, stem) if root else 0
        items.append((stem, name, stem, icon, i))
    _retail_items.cache = items or [("France1", "France - Stage 1", "", 0, 0)]
    return _retail_items.cache


CLASSES = (MR_UL_findings, MR_UL_materials, MR_PT_studio, MR_PT_project, MR_PT_terrain, MR_PT_objects,
           MR_PT_materials, MR_PT_collision, MR_PT_markers, MR_PT_routes, MR_PT_environment, MR_PT_build,
           MR_PT_problems, MR_PT_selected)


def register():
    bpy.types.WindowManager.mr_retail_choice = bpy.props.EnumProperty(name="Course", items=_retail_items)


def unregister():
    del bpy.types.WindowManager.mr_retail_choice
