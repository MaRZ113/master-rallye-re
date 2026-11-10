"""Course Studio operators. Every editing operator is registered with UNDO."""
from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path

import bmesh
import bpy
import numpy as np
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import catalog, convert as C, jobs
from .core import ai as AI
from .core import collision as COL
from .core import materials as MAT
from .core import model as M
from .core import templates as TPL

UNDO = {"REGISTER", "UNDO"}
_TREES = {"current": None, "previous": None}


def _settings(context):
    return context.scene.mr_studio


def _cursor_game(context):
    return tuple(C.b2g(context.scene.cursor.location))


def _route_frame(context):
    from .core.ai import raceline
    route = C.active_route()
    if route is None:
        return None, []
    pts = C.curve_points(route)
    return route, pts


def _ground_bvh(context, roles=("terrain", "terrain_hidden")):
    """BVH of terrain objects in Blender space for ray/snap operations."""
    verts, polys = [], []
    depsgraph = context.evaluated_depsgraph_get()
    for obj in C.studio_objects("MESH"):
        if obj.type != "MESH" or obj.mr.role not in roles:
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        base = len(verts)
        mw = obj.matrix_world
        verts.extend(mw @ v.co for v in me.vertices)
        polys.extend(tuple(base + i for i in t.vertices) for t in me.loop_triangles)
        ev.to_mesh_clear()
    if not polys:
        return None
    return BVHTree.FromPolygons(verts, polys)


def ground_height_b(bvh, x, y, top=10000.0):
    hit = bvh.ray_cast(Vector((x, y, top)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else None


def _set_findings(context, findings, *, keep_categories=()):
    s = _settings(context)
    if keep_categories:
        kept = [(f.severity, f.category, f.message, f.hint, tuple(f.position), f.has_position, f.ref)
                for f in s.findings if f.category in keep_categories]
    else:
        kept = []
    s.findings.clear()
    for row in kept:
        item = s.findings.add()
        item.severity, item.category, item.message, item.hint, pos, item.has_position, item.ref = row
        item.position = pos
    for f in findings:
        item = s.findings.add()
        item.severity, item.category, item.message, item.hint = f.severity, f.category, f.message, f.hint
        if f.position is not None:
            item.position = C.g2b(f.position)
            item.has_position = True
        item.ref = ";".join(f"{k}={v}" for k, v in (f.ref or {}).items())


def _report_errors(op, findings):
    errors = [f for f in findings if f.severity == "error"]
    if errors:
        op.report({"ERROR"}, f"{len(errors)} error(s): {errors[0].message} (see Build > Problems)")
    return errors


# ===================================================================== project
def _environment_items(self, context):
    return catalog.scene_enum_items(context)


class MR_OT_new_course(bpy.types.Operator):
    bl_idname = "mr.new_course"
    bl_label = "New Course"
    bl_description = "Start a new course from scratch (no Retail geometry needed)"
    bl_options = UNDO

    name: StringProperty(name="Name", default="MyCourse")
    title: StringProperty(name="Menu title", default="My Course")
    start_from: EnumProperty(name="Start from", items=[
        ("VALLEY", "Valley with road", "Rolling terrain, road, building, route, start/finish and checkpoints"),
        ("FLAT", "Flat ground", "A flat terrain grid to sculpt"),
        ("EMPTY", "Empty", "Only materials; add or import terrain yourself")], default="VALLEY")
    size: FloatProperty(name="Size (m)", default=700.0, min=100.0, max=6000.0)
    environment: EnumProperty(name="Environment", items=_environment_items)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name")
        layout.prop(self, "title")
        layout.prop(self, "environment")
        layout.prop(self, "start_from", expand=True)
        if self.start_from != "EMPTY":
            layout.prop(self, "size")
        if bpy.data.collections.get(C.ROOT_COLLECTION):
            layout.label(text="The current course in this scene will be replaced", icon="ERROR")

    def execute(self, context):
        root = C.resource_root(context)
        retail = root is not None
        key = M.safe_key(self.name)
        if self.start_from == "VALLEY":
            project = TPL.valley_course(key, size=self.size, title=self.title, retail_textures=retail)
        else:
            project = TPL.new_project(key, title=self.title, retail_textures=retail)
        project.environment.template = self.environment
        C.project_to_scene(context, project, root)
        if self.start_from == "FLAT":
            bpy.ops.mr.add_terrain_grid(size=self.size, resolution=max(16, int(self.size / 6)), hills=0.0)
        s = _settings(context)
        s.environment_template = self.environment
        s.section = "TERRAIN"
        s.project_dirty = True
        if s.cap2_input == "":
            s.cap2_input = _default_cap2_input(context)
        _frame_all(context)
        self.report({"INFO"}, f"New course {key} created")
        return {"FINISHED"}


def _default_cap2_input(context) -> str:
    try:
        prefs = context.preferences.addons[__package__.split(".")[0]].preferences
        if prefs.cap2_input:
            return prefs.cap2_input
    except Exception:
        pass
    here = Path(__file__).resolve()
    for up in list(here.parents)[:6]:
        cand = up / ".research-output" / "course-cap2" / "menu-fix-01" / "build-input.json"
        if cand.exists():
            return str(cand)
    return ""


def _frame_all(context):
    for area in context.screen.areas if context.screen else []:
        if area.type == "VIEW_3D":
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if region is not None:
                with context.temp_override(area=area, region=region):
                    try:
                        bpy.ops.view3d.view_all()
                    except Exception:
                        pass


class MR_OT_open_retail(bpy.types.Operator):
    bl_idname = "mr.open_retail"
    bl_label = "Open Game Course"
    bl_description = ("Open an original course for editing (exported as a NEW course; the original is never "
                      "changed). Collision is recovered exactly from the game's collision tree")
    race: StringProperty()
    extract_collision: BoolProperty(name="Recover collision", default=True)

    def execute(self, context):
        root = C.resource_root(context)
        if root is None:
            self.report({"ERROR"}, "Game resources not found: set them in Project > Game resources")
            return {"CANCELLED"}
        race = self.race or context.window_manager.mr_retail_choice
        from .core.importer import import_retail_course

        def work(progress):
            return import_retail_course(root, race, extract_collision=self.extract_collision, progress=progress)

        def done(ctx, project):
            C.project_to_scene(ctx, project, root)
            s = _settings(ctx)
            s.section = "TERRAIN"
            s.project_dirty = True
            if not s.cap2_input:
                s.cap2_input = _default_cap2_input(ctx)
            _frame_all(ctx)
            return f"Opened {catalog.readable(race)} as {project.name}"
        jobs.start(context, f"Open {catalog.readable(race)}", work, done)
        return {"FINISHED"}


class MR_OT_open_project(bpy.types.Operator, ImportHelper):
    bl_idname = "mr.open_project"
    bl_label = "Open Course Project"
    bl_description = "Open a Course Studio project folder (project.json)"
    filename_ext = ".json"
    filter_glob: StringProperty(default="project.json;*.json", options={"HIDDEN"})

    def execute(self, context):
        path = Path(self.filepath)
        project = M.load_project(path)
        project.extras["project_dir"] = str(path.parent)
        C.project_to_scene(context, project, C.resource_root(context))
        _settings(context).project_dir = str(path.parent)
        _settings(context).project_dirty = False
        _frame_all(context)
        return {"FINISHED"}


def save_project(context, directory: Path | None = None) -> Path:
    s = _settings(context)
    directory = directory or C.project_dir(context.scene)
    if directory is None:
        raise ValueError("save the .blend file first or choose a project folder")
    project = C.scene_to_project(context, project_dir_path=directory)
    project.extras["resource_root_hint"] = str(C.resource_root(context) or "")
    path = M.save_project(project, directory)
    info = C.meta(context.scene)
    info.update(uid=project.uid)
    C.set_meta(context.scene, info)
    s.project_dirty = False
    return path


class MR_OT_save_project(bpy.types.Operator):
    bl_idname = "mr.save_project"
    bl_label = "Save Course Project"
    bl_description = "Write the course project (project.json + geometry.bin) next to the .blend file"
    save_as: BoolProperty(default=False, options={"HIDDEN"})
    directory: StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        if self.save_as or C.project_dir(context.scene) is None:
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}
        return self.execute(context)

    def execute(self, context):
        try:
            target = Path(self.directory) if self.directory else None
            if target is not None:
                _settings(context).project_dir = str(target)
            path = save_project(context, target)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Saved {path}")
        return {"FINISHED"}


class MR_OT_import_geometry(bpy.types.Operator, ImportHelper):
    bl_idname = "mr.import_geometry"
    bl_label = "Import Geometry"
    bl_description = "Import OBJ, FBX or glTF with Blender's importers and add it to the course with a role"
    bl_options = UNDO
    filter_glob: StringProperty(default="*.obj;*.fbx;*.glb;*.gltf", options={"HIDDEN"})
    role: EnumProperty(name="Use as", items=[
        ("terrain", "Terrain", ""), ("visual", "Visual only", ""), ("collision", "Collision only", ""),
        ("water", "Water", ""), ("terrain_hidden", "Invisible ground", "")], default="terrain")
    scale: FloatProperty(name="Scale", default=1.0, min=0.0001, max=10000.0)

    def execute(self, context):
        before = set(bpy.data.objects)
        ext = Path(self.filepath).suffix.lower()
        if ext == ".obj":
            bpy.ops.wm.obj_import(filepath=self.filepath)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=self.filepath)
        elif ext in (".glb", ".gltf"):
            bpy.ops.import_scene.gltf(filepath=self.filepath)
        else:
            self.report({"ERROR"}, f"unsupported format {ext}")
            return {"CANCELLED"}
        new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
        for obj in new:
            obj.scale = tuple(v * self.scale for v in obj.scale)
            assign_role(obj, self.role)
        _settings(context).collision_state = "DIRTY"
        self.report({"INFO"}, f"Imported {len(new)} mesh object(s) as {self.role}")
        return {"FINISHED"}


def assign_role(obj, role):
    obj.mr.kind = "MESH"
    obj.mr.role = role
    if not obj.mr.uid:
        obj.mr.uid = M.new_uid("mesh_")
    C.link(obj, C.ROLE_SECTION.get(role, "objects"))
    C.style_object(obj)
    if not obj.material_slots and role != "collision":
        obj.data.materials.append(_preset_material("Grass" if role in ("terrain", "terrain_hidden") else
                                                   "Water" if role == "water" else "Building / object"))


def _preset_material(preset: str, name: str | None = None):
    name = name or f"MR {preset}"
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    values = MAT.PRESETS[preset]
    p = mat.mr
    p.key = M.safe_key(name).lower()
    p.label = preset
    p.shader = values["shader"]
    p.surface = values.get("surface") or "NONE"
    p.noise = values.get("noise", False)
    p.alpha = values.get("alpha", "opaque")
    C.build_preview_nodes(mat)
    return mat


class MR_OT_reopen_build(bpy.types.Operator):
    bl_idname = "mr.reopen_build"
    bl_label = "Reopen Exported Course"
    bl_description = "Import the last built course back from its exported game files (round-trip check)"

    def execute(self, context):
        s = _settings(context)
        if not s.last_build:
            self.report({"ERROR"}, "No build yet")
            return {"CANCELLED"}
        root = Path(s.last_build) / "resource-root"
        key = Path(s.last_build).name
        from .core.importer import import_retail_course

        def work(progress):
            return import_retail_course(root, key, extract_collision=True, progress=progress)

        def done(ctx, project):
            scene = bpy.data.scenes.new(f"Reopened {key}")
            ctx.window.scene = scene
            C.project_to_scene(ctx, project, root)
            return f"Reopened {key} in scene '{scene.name}'"
        jobs.start(context, f"Reopen {key}", work, done)
        return {"FINISHED"}


# ===================================================================== terrain
class MR_OT_add_terrain_grid(bpy.types.Operator):
    bl_idname = "mr.add_terrain_grid"
    bl_label = "Add Terrain"
    bl_description = "Add a terrain grid at the 3D cursor (then sculpt or edit it freely)"
    bl_options = UNDO
    size: FloatProperty(name="Size (m)", default=400.0, min=10.0, max=8000.0)
    resolution: IntProperty(name="Subdivisions", default=64, min=2, max=1000)
    hills: FloatProperty(name="Hills (m)", default=8.0, min=0.0, max=500.0)

    def execute(self, context):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=self.resolution, y_subdivisions=self.resolution,
                                        size=self.size, location=context.scene.cursor.location)
        obj = context.active_object
        obj.name = "Terrain"
        if self.hills > 0:
            me = obj.data
            for v in me.vertices:
                x, y = v.co.x, v.co.y
                v.co.z = self.hills * (math.sin(x / 61.0) * math.cos(y / 47.0) + 0.4 * math.sin((x + y) / 23.0))
        uv = obj.data.uv_layers.active
        if uv is not None:
            for loop in obj.data.loops:
                co = obj.data.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (co.x / 12.0, co.y / 12.0)
        assign_role(obj, "terrain")
        _settings(context).collision_state = "DIRTY"
        return {"FINISHED"}


class MR_OT_set_role(bpy.types.Operator):
    bl_idname = "mr.set_role"
    bl_label = "Set Role"
    bl_description = "Set what the selected objects are in the game"
    bl_options = UNDO
    role: EnumProperty(items=[("terrain", "Terrain", ""), ("terrain_hidden", "Invisible ground", ""),
                              ("visual", "Visual only", ""), ("collision", "Collision only", ""),
                              ("water", "Water", ""), ("NONE", "Exclude", "")])

    def execute(self, context):
        n = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            if self.role == "NONE":
                obj.mr.kind = "NONE"
                obj.mr.role = "NONE"
            else:
                assign_role(obj, self.role)
            n += 1
        _settings(context).collision_state = "DIRTY"
        self.report({"INFO"}, f"{n} object(s) set to {self.role}")
        return {"FINISHED"}


def _route_samples_b(context, spacing=2.0):
    route, pts = _route_frame(context)
    if len(pts) < 2:
        return None
    from .core.ai import resample_route
    return [Vector(C.g2b(p)) for p in resample_route(pts, spacing)]


class MR_OT_carve_road(bpy.types.Operator):
    bl_idname = "mr.carve_road"
    bl_label = "Carve Road Along Route"
    bl_description = "Flatten the selected terrain along the AI route (road bed) with a smooth shoulder"
    bl_options = UNDO
    width: FloatProperty(name="Road width", default=9.0, min=1.0, max=80.0)
    shoulder: FloatProperty(name="Shoulder", default=10.0, min=0.0, max=200.0)
    depth: FloatProperty(name="Below route", default=0.3, min=-5.0, max=5.0)
    assign_material: BoolProperty(name="Assign road material", default=True)

    def execute(self, context):
        samples = _route_samples_b(context)
        if samples is None:
            self.report({"ERROR"}, "Draw an AI route first (Routes & AI)")
            return {"CANCELLED"}
        from mathutils.kdtree import KDTree
        kd = KDTree(len(samples))
        for i, p in enumerate(samples):
            kd.insert(Vector((p.x, p.y, 0.0)), i)
        kd.balance()
        targets = [o for o in context.selected_objects if o.type == "MESH" and o.mr.role in ("terrain", "terrain_hidden")]
        if not targets:
            self.report({"ERROR"}, "Select the terrain to carve")
            return {"CANCELLED"}
        road = _preset_material("Tarmac road", "MR Road") if self.assign_material else None
        half = self.width / 2
        for obj in targets:
            mw, mi = obj.matrix_world, obj.matrix_world.inverted()
            me = obj.data
            moved = 0
            for v in me.vertices:
                w = mw @ v.co
                co, idx, dist = kd.find(Vector((w.x, w.y, 0.0)))
                if dist > half + self.shoulder:
                    continue
                target = samples[idx].z - self.depth
                t = 1.0 if dist <= half else 1.0 - (dist - half) / max(self.shoulder, 1e-6)
                t = t * t * (3 - 2 * t)
                w.z = w.z * (1 - t) + target * t
                v.co = mi @ w
                moved += 1
            if road is not None:
                if road.name not in [m.name for m in me.materials if m]:
                    me.materials.append(road)
                slot = [m.name if m else "" for m in me.materials].index(road.name)
                for poly in me.polygons:
                    c = mw @ poly.center
                    if kd.find(Vector((c.x, c.y, 0.0)))[2] <= half:
                        poly.material_index = slot
            me.update()
        _settings(context).collision_state = "DIRTY"
        return {"FINISHED"}


class MR_OT_merge_terrain(bpy.types.Operator):
    bl_idname = "mr.merge_terrain"
    bl_label = "Merge Terrains"
    bl_description = "Join the selected terrain pieces into the active one and weld seams within a distance"
    bl_options = UNDO
    weld: FloatProperty(name="Weld distance", default=0.05, min=0.0, max=10.0)

    def execute(self, context):
        if len(context.selected_objects) < 2 or context.active_object is None:
            self.report({"ERROR"}, "Select two or more terrain objects (the active one receives the others)")
            return {"CANCELLED"}
        bpy.ops.object.join()
        obj = context.active_object
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        before = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=self.weld)
        bm.to_mesh(obj.data)
        bm.free()
        self.report({"INFO"}, f"Merged; welded {before - len(obj.data.vertices)} seam vertices")
        _settings(context).collision_state = "DIRTY"
        return {"FINISHED"}


class MR_OT_find_gaps(bpy.types.Operator):
    bl_idname = "mr.find_gaps"
    bl_label = "Find Gaps"
    bl_description = "Select open (boundary) and non-manifold edges of the active terrain in Edit Mode"
    bl_options = UNDO

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="EDGE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True, use_multi_face=True,
                                         use_non_contiguous=True, use_verts=True)
        bm = bmesh.from_edit_mesh(obj.data)
        n = sum(1 for e in bm.edges if e.select)
        self.report({"INFO"}, f"{n} open/non-manifold edges selected (the outer map edge is expected)")
        return {"FINISHED"}


class MR_OT_split_terrain(bpy.types.Operator):
    bl_idname = "mr.split_terrain"
    bl_label = "Split Into Sections"
    bl_description = "Split the active terrain into a grid of separate objects (easier editing of large courses)"
    bl_options = UNDO
    cells: IntProperty(name="Sections per side", default=4, min=2, max=32)

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}
        mw = obj.matrix_world
        xs = [(mw @ v.co).x for v in obj.data.vertices]
        ys = [(mw @ v.co).y for v in obj.data.vertices]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.faces.layers.int.get("mr_section") or bm.faces.layers.int.new("mr_section")
        for f in bm.faces:
            c = mw @ f.calc_center_median()
            i = min(self.cells - 1, int((c.x - x0) / max(x1 - x0, 1e-6) * self.cells))
            j = min(self.cells - 1, int((c.y - y0) / max(y1 - y0, 1e-6) * self.cells))
            f[layer] = j * self.cells + i
        for section in range(self.cells * self.cells - 1, 0, -1):
            bpy.ops.mesh.select_all(action="DESELECT")
            for f in bm.faces:
                f.select = f[layer] == section
            if any(f.select for f in bm.faces):
                bmesh.update_edit_mesh(obj.data)
                bpy.ops.mesh.separate(type="SELECTED")
                bm = bmesh.from_edit_mesh(obj.data)
                layer = bm.faces.layers.int.get("mr_section")
        bpy.ops.object.mode_set(mode="OBJECT")
        for o in context.selected_objects:
            if o.type == "MESH":
                o.mr.uid = M.new_uid("mesh_") if o is not obj else o.mr.uid
        self.report({"INFO"}, "Terrain split into sections; collision stays one tree on export")
        return {"FINISHED"}


class MR_OT_align_seam(bpy.types.Operator):
    bl_idname = "mr.align_seam"
    bl_label = "Snap Edges to Neighbour"
    bl_description = ("Move the open-edge vertices of the selected terrains onto the active terrain's surface "
                      "(closes height steps between joined landscapes)")
    bl_options = UNDO
    distance: FloatProperty(name="Search distance", default=4.0, min=0.01, max=100.0)

    def execute(self, context):
        active = context.active_object
        others = [o for o in context.selected_objects if o is not active and o.type == "MESH"]
        if active is None or not others:
            self.report({"ERROR"}, "Select the terrains to align, then the reference terrain last (active)")
            return {"CANCELLED"}
        depsgraph = context.evaluated_depsgraph_get()
        bvh = BVHTree.FromObject(active, depsgraph)
        mi_a, mw_a = active.matrix_world.inverted(), active.matrix_world
        moved = 0
        for obj in others:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            mw, mi = obj.matrix_world, obj.matrix_world.inverted()
            for v in bm.verts:
                if not v.is_boundary:
                    continue
                w = mw @ v.co
                loc, normal, index, dist = bvh.find_nearest(mi_a @ w, self.distance)
                if loc is not None:
                    v.co = mi @ (mw_a @ loc)
                    moved += 1
            bm.to_mesh(obj.data)
            bm.free()
        self.report({"INFO"}, f"{moved} edge vertices snapped")
        _settings(context).collision_state = "DIRTY"
        return {"FINISHED"}


class MR_OT_bake_lighting(bpy.types.Operator):
    bl_idname = "mr.bake_lighting"
    bl_label = "Bake Vertex Lighting"
    bl_description = "Write prelit vertex colours (MR_Color) from the baked light direction; Retail courses are prelit"
    bl_options = UNDO

    def execute(self, context):
        sun = Vector(_settings(context).sun_direction).normalized()
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            me = obj.data
            attr = me.color_attributes.get("MR_Color") or me.color_attributes.new("MR_Color", "BYTE_COLOR", "CORNER")
            nm = obj.matrix_world.to_3x3().inverted().transposed()
            try:
                normals = [c.vector for c in me.corner_normals]
            except AttributeError:
                normals = [l.normal for l in me.loops]
            for i, n in enumerate(normals):
                v = 0.55 + 0.45 * max(0.0, (nm @ n).normalized().dot(sun))
                attr.data[i].color_srgb = (v, v, v, 1.0)
        return {"FINISHED"}


# ===================================================================== objects
OBJECT_PRESETS = {
    "HOUSE": ("Building", (12.0, 8.0, 7.0), "Building / object"),
    "WALL": ("Wall", (20.0, 0.6, 2.0), "Building / object"),
    "BARRIER": ("Barrier", (6.0, 0.5, 1.0), "Metal object"),
    "ROCK": ("Rock", (4.0, 3.5, 2.5), "Rock face"),
    "CRATE": ("Crate", (1.2, 1.2, 1.2), "Building / object"),
}


class MR_OT_add_object(bpy.types.Operator):
    bl_idname = "mr.add_object"
    bl_label = "Add Object"
    bl_description = "Add a static object at the 3D cursor with a collision proxy"
    bl_options = UNDO
    preset: EnumProperty(items=[(k, v[0], "") for k, v in OBJECT_PRESETS.items()])
    with_collision: BoolProperty(name="Solid (collision proxy)", default=True)

    def execute(self, context):
        name, size, material = OBJECT_PRESETS[self.preset]
        loc = context.scene.cursor.location.copy()
        bvh = _ground_bvh(context)
        if bvh is not None:
            g = ground_height_b(bvh, loc.x, loc.y)
            if g is not None:
                loc.z = g
        if self.preset == "ROCK":
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=loc)
        else:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        obj = context.active_object
        obj.name = name
        obj.scale = size
        obj.location.z += size[2] / 2
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign_role(obj, "visual")
        obj.data.materials.clear()
        obj.data.materials.append(_preset_material(material))
        if self.with_collision:
            make_proxy(context, obj, "box" if self.preset != "ROCK" else "hull")
        _settings(context).collision_state = "DIRTY"
        return {"FINISHED"}


def make_proxy(context, obj, kind):
    depsgraph = context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    pts = [tuple(C.b2g(obj.matrix_world @ v.co)) for v in me.vertices]
    ev.to_mesh_clear()
    project_like = M.CourseProject(name="tmp")
    for t in C.studio_objects("MESH"):
        if t.mr.role == "terrain" and t.type == "MESH":
            m = C.object_to_mesh(t, depsgraph, project_like, None)
            if m:
                project_like.meshes.append(m)
    hf = COL.HeightField(COL.terrain_triangles(project_like)) if project_like.meshes else None
    tris = COL.grounded_proxy(pts, hf, kind=kind)
    if not tris:
        return None
    name = f"{obj.name} collision"
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    verts, faces, lookup = [], [], {}
    for tri in tris:
        face = []
        for p in tri:
            key = tuple(round(c, 4) for c in p)
            if key not in lookup:
                lookup[key] = len(verts)
                verts.append(C.g2b(p))
            face.append(lookup[key])
        faces.append(face)
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    proxy = bpy.data.objects.new(name, data)
    assign_role(proxy, "collision")
    proxy.mr.proxy_of = obj.name
    proxy.parent = obj
    proxy.matrix_parent_inverse = obj.matrix_world.inverted()
    return proxy


class MR_OT_make_proxy(bpy.types.Operator):
    bl_idname = "mr.make_proxy"
    bl_label = "Make Collision Proxy"
    bl_description = "Create a grounded collision proxy (convex hull or box) for the selected objects"
    bl_options = UNDO
    kind: EnumProperty(items=[("hull", "Convex hull", ""), ("box", "Box", "")], default="hull")

    def execute(self, context):
        n = 0
        for obj in list(context.selected_objects):
            if obj.type == "MESH" and obj.mr.role in ("visual", "NONE"):
                if obj.mr.role == "NONE":
                    assign_role(obj, "visual")
                if make_proxy(context, obj, self.kind) is not None:
                    n += 1
        _settings(context).collision_state = "DIRTY"
        self.report({"INFO"}, f"{n} collision proxies")
        return {"FINISHED"}


class MR_OT_add_blocker(bpy.types.Operator):
    bl_idname = "mr.add_blocker"
    bl_label = "Add Collision Blocker"
    bl_description = "Add an invisible solid box at the 3D cursor (impassable obstacle or wall)"
    bl_options = UNDO
    width: FloatProperty(name="Width", default=10.0, min=0.1)
    depth: FloatProperty(name="Depth", default=1.0, min=0.1)
    height: FloatProperty(name="Height", default=4.0, min=0.1)

    def execute(self, context):
        loc = context.scene.cursor.location.copy()
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(loc.x, loc.y, loc.z + self.height / 2 - 1.0))
        obj = context.active_object
        obj.name = "Blocker"
        obj.scale = (self.width, self.depth, self.height + 2.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.clear()
        assign_role(obj, "collision")
        _settings(context).collision_state = "DIRTY"
        return {"FINISHED"}


def _sound_templates(self, context):
    root = C.resource_root(context)
    items = []
    if root is not None:
        from .core.race import read_scene
        from .core.validate import ci_path
        path = ci_path(root, f"DataScene/RaceTest/{_settings(context).environment_template}.xml")
        if path is not None:
            for snd in read_scene(path)["sounds"]:
                items.append((snd["name"], snd["name"], "Sound source of the environment scene"))
    return items or [("river1", "river1", "")]


class MR_OT_add_sound(bpy.types.Operator):
    bl_idname = "mr.add_sound"
    bl_label = "Add Sound Source"
    bl_description = "Place an environment sound source (copied from the environment scene) at the 3D cursor"
    bl_options = UNDO
    template: EnumProperty(name="Sound", items=_sound_templates)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = C.sound_object(M.SoundAnchor(uid=M.new_uid("snd_"), position=_cursor_game(context), template=self.template))
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class MR_OT_add_physical(bpy.types.Operator):
    bl_idname = "mr.add_physical"
    bl_label = "Add Physical Object"
    bl_description = ("Place a movable rigid body at the 3D cursor (optional Renderer RigidProps module): a PS2 "
                      "family, or make the selected mesh a new physical object model")
    bl_options = UNDO
    kind: EnumProperty(items=[("haybale", "Hay bale", ""), ("tumblweed", "Tumbleweed", ""),
                              ("checkpoint", "Checkpoint barrel", ""), ("SELECTED", "Selected mesh (new model)", "")])

    def execute(self, context):
        if self.kind == "SELECTED":
            objs = [o for o in context.selected_objects if o.type == "MESH"]
            if not objs:
                self.report({"ERROR"}, "Select the mesh to turn into a physical object")
                return {"CANCELLED"}
            for o in objs:
                assign_role(o, "physical")
                o.mr.mass = max(1.0, 400.0 * o.dimensions.x * o.dimensions.y * o.dimensions.z)
            self.report({"INFO"}, f"{len(objs)} physical object(s); instances share one model (same mesh data)")
            return {"FINISHED"}
        loc = context.scene.cursor.location.copy()
        bvh = _ground_bvh(context)
        if bvh is not None:
            g = ground_height_b(bvh, loc.x, loc.y)
            if g is not None:
                loc.z = g + 0.6
        obj = C.ps2prop_object({"model": self.kind, "position": tuple(C.b2g(loc)),
                                "mass": {"haybale": 300.0, "tumblweed": 8.0, "checkpoint": 500.0}[self.kind],
                                "trigger": 5.0})
        context.view_layer.objects.active = obj
        return {"FINISHED"}


# ===================================================================== materials
class MR_OT_new_material(bpy.types.Operator):
    bl_idname = "mr.new_material"
    bl_label = "New Material"
    bl_description = "Create a course material from a preset and assign it to the selection (faces in Edit Mode)"
    bl_options = UNDO
    preset: EnumProperty(items=[(k, k, "") for k in MAT.PRESETS])
    name: StringProperty(name="Name", default="")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        base = self.name or self.preset
        name = f"MR {base}"
        k = 1
        while bpy.data.materials.get(name):
            k += 1
            name = f"MR {base} {k}"
        mat = _preset_material(self.preset, name)
        obj = context.active_object
        if obj is not None and obj.type == "MESH":
            if obj.mode == "EDIT":
                obj.data.materials.append(mat)
                obj.active_material_index = len(obj.data.materials) - 1
                bpy.ops.object.material_slot_assign()
            else:
                for o in context.selected_objects:
                    if o.type == "MESH":
                        o.data.materials.append(mat) if not o.data.materials else o.data.materials.__setitem__(0, mat)
        return {"FINISHED"}


class MR_OT_load_texture(bpy.types.Operator, ImportHelper):
    bl_idname = "mr.load_texture"
    bl_label = "Load Texture"
    bl_description = "Use an image file as the material texture (any size; conformed to a power of two on build)"
    bl_options = UNDO
    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.tga;*.bmp;*.dxt", options={"HIDDEN"})

    def execute(self, context):
        mat = context.object.active_material if context.object else None
        if mat is None:
            self.report({"ERROR"}, "Select an object with a course material")
            return {"CANCELLED"}
        path = Path(self.filepath)
        if path.suffix.lower() == ".dxt":
            img = C.image_from_feed(path.stem.lower(), path.read_bytes())
        else:
            img = bpy.data.images.load(str(path), check_existing=True)
            img["mr_texture_key"] = C.texture_key_for_image(img)
        mat.mr.base_image = img
        mat.mr.base_native = ""
        mat.mr.base_key = img["mr_texture_key"]
        C.build_preview_nodes(mat)
        return {"FINISHED"}


class MR_OT_export_texture(bpy.types.Operator):
    bl_idname = "mr.export_texture"
    bl_label = "Export Texture PNG"
    bl_description = "Save the material texture as an upright RGBA PNG for editing in an image editor"
    filepath: StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        mat = context.object.active_material if context.object else None
        if mat is None or mat.mr.base_image is None:
            return {"CANCELLED"}
        from .core.textures import encode_png
        w, h, rgba = C.image_rgba(mat.mr.base_image)
        Path(self.filepath).write_bytes(encode_png(w, h, rgba))
        return {"FINISHED"}


class MR_OT_texture_users(bpy.types.Operator):
    bl_idname = "mr.texture_users"
    bl_label = "Find Texture Users"
    bl_description = "List materials and objects that use the same texture (shared textures change everywhere)"

    def execute(self, context):
        mat = context.object.active_material if context.object else None
        if mat is None or mat.mr.base_image is None:
            return {"CANCELLED"}
        img = mat.mr.base_image
        users = [m.name for m in bpy.data.materials if getattr(m, "mr", None) and m.mr.base_image == img]
        objs = [o.name for o in C.studio_objects("MESH") if any(s.material and s.material.name in users
                                                               for s in o.material_slots)]
        self.report({"INFO"}, f"{img.name}: {len(users)} material(s) {users[:6]}, {len(objs)} object(s)")
        return {"FINISHED"}


class MR_OT_select_material_faces(bpy.types.Operator):
    bl_idname = "mr.select_material_faces"
    bl_label = "Select Faces"
    bl_description = "Select the faces of the active object that use the active material"

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.material_slot_select()
        return {"FINISHED"}


# ===================================================================== collision
class MR_OT_build_collision(bpy.types.Operator):
    bl_idname = "mr.build_collision"
    bl_label = "Rebuild Collision"
    bl_description = ("Build the game's collision tree from terrain and collision objects, then probe it the way "
                      "the game queries it (holes, phantom bumps, blocked route)")

    def execute(self, context):
        try:
            project = C.scene_to_project(context)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        spacing = _settings(context).probe_spacing

        def work(progress):
            progress("collision tree", 0.05)
            tree, provenance, stats = COL.build_tree(project)
            progress("probing", 0.6)
            report = COL.validate_tree(project, tree, spacing=spacing)
            return tree, stats, report, project

        def done(ctx, result):
            tree, stats, report, project = result
            _TREES["previous"], _TREES["current"] = _TREES["current"], tree
            s = _settings(ctx)
            s.collision_state = "OK"
            summary = report.summary()
            s.collision_summary = (f"{stats['planes']} planes, {stats['solid_leaves']} solid cells | "
                                   f"holes {summary['holes']}, bumps {summary['phantoms']}, "
                                   f"route blocked {summary['route_blocked']} of {summary['route_samples']}")
            from .core.validate import validate_project
            findings = [f for f in validate_project(project, collision_report=report) if f.category == "collision"]
            _set_findings(ctx, findings, keep_categories=("geometry", "gameplay", "materials", "resources"))
            _points_object(ctx, "MR Collision Problems", [i.position for i in report.issues], (1, 0, 0, 1))
            return "Collision rebuilt: " + s.collision_summary
        jobs.start(context, "Rebuild collision", work, done)
        return {"FINISHED"}


def _points_object(context, name, game_points, colour):
    old = bpy.data.objects.get(name)
    if old is not None:
        me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    if not game_points:
        return None
    me = bpy.data.meshes.new(name)
    me.from_pydata([C.g2b(p) for p in game_points], [], [])
    obj = bpy.data.objects.new(name, me)
    obj.mr.kind = "DIAGNOSTIC"
    C.link(obj, "diagnostics")
    obj.color = colour
    obj.show_in_front = True
    return obj


class MR_OT_collision_diff(bpy.types.Operator):
    bl_idname = "mr.collision_diff"
    bl_label = "Show Collision Differences"
    bl_description = "Points where the last two collision builds disagree (solid vs empty)"

    def execute(self, context):
        if _TREES["previous"] is None or _TREES["current"] is None:
            self.report({"ERROR"}, "Rebuild collision twice (before and after an edit) to compare")
            return {"CANCELLED"}
        project = C.scene_to_project(context)
        diff = COL.tree_difference(_TREES["previous"], _TREES["current"], project)
        added = [(x, y, z) for x, y, z, was, now in diff if now and not was]
        removed = [(x, y, z) for x, y, z, was, now in diff if was and not now]
        _points_object(context, "MR Collision Added", added, (1.0, 0.2, 0.2, 1.0))
        _points_object(context, "MR Collision Removed", removed, (0.2, 0.6, 1.0, 1.0))
        self.report({"INFO"}, f"{len(added)} points became solid, {len(removed)} became empty")
        return {"FINISHED"}


class MR_OT_preview_collision(bpy.types.Operator):
    bl_idname = "mr.preview_collision"
    bl_label = "Show Game Collision"
    bl_description = ("Extract the exact solid/empty boundary of the built collision tree around the 3D cursor: "
                      "this is what the game collides with")

    def execute(self, context):
        tree = _TREES["current"]
        if tree is None:
            self.report({"ERROR"}, "Rebuild collision first")
            return {"CANCELLED"}
        r = _settings(context).preview_radius
        c = _cursor_game(context)
        lo, hi = (c[0] - r, c[1] - r, c[2] - r), (c[0] + r, c[1] + r, c[2] + r)

        def work(progress):
            tris, stats = COL.extract_native_collision(tree, lo, hi, progress=lambda s, n: progress("extract", None))
            return tris, stats

        def done(ctx, result):
            tris, stats = result
            name = "MR Game Collision (preview)"
            old = bpy.data.objects.get(name)
            if old is not None:
                bpy.data.objects.remove(old, do_unlink=True)
            mesh = COL.triangles_to_mesh(tris, name=name, role="collision", material="collision", source="preview")
            verts = [C.g2b(mesh.vertex(i)) for i in range(mesh.vertex_count)]
            faces = [mesh.triangle(t) for t in range(mesh.triangle_count)]
            me = bpy.data.meshes.new(name)
            me.from_pydata(verts, [], faces)
            obj = bpy.data.objects.new(name, me)
            obj.mr.kind = "DIAGNOSTIC"
            C.link(obj, "diagnostics")
            obj.display_type = "WIRE"
            obj.color = (1.0, 0.4, 0.0, 1.0)
            obj.show_in_front = True
            return f"Game collision preview: {stats['triangles']} faces"
        jobs.start(context, "Collision preview", work, done)
        return {"FINISHED"}


class MR_OT_probe_cursor(bpy.types.Operator):
    bl_idname = "mr.probe_cursor"
    bl_label = "Probe at Cursor"
    bl_description = "Report solid/empty intervals of the collision tree on the vertical line through the 3D cursor"

    def execute(self, context):
        tree = _TREES["current"]
        if tree is None:
            self.report({"ERROR"}, "Rebuild collision first")
            return {"CANCELLED"}
        x, y, z = _cursor_game(context)
        state, start, out = None, None, []
        for k in range(-400, 401):
            yy = y + k * 0.25
            solid = COL.classify(tree, (x, yy, z))
            if state is None:
                state, start = solid, yy
            elif solid != state:
                out.append(f"{'solid' if state else 'empty'} {start:.1f}..{yy:.1f}")
                state, start = solid, yy
        out.append(f"{'solid' if state else 'empty'} {start:.1f}..")
        self.report({"INFO"}, " | ".join(out[-6:]))
        return {"FINISHED"}


# ===================================================================== markers
def _nearest_route(context, point_game):
    route, pts = _route_frame(context)
    if len(pts) < 2:
        return None, 0.0, None
    from .core.ai import resample_route
    line = resample_route(pts, 2.0)
    best = min(range(len(line)), key=lambda i: (line[i][0] - point_game[0]) ** 2 + (line[i][2] - point_game[2]) ** 2)
    a, b = line[max(0, best - 1)], line[min(len(line) - 1, best + 1)]
    return line[best], math.degrees(math.atan2(b[0] - a[0], b[2] - a[2])), best / max(1, len(line) - 1)


class MR_OT_add_area(bpy.types.Operator):
    bl_idname = "mr.add_area"
    bl_label = "Place Start / Finish"
    bl_description = "Place the start or finish area at the 3D cursor, aligned to the AI route"
    bl_options = UNDO
    kind: EnumProperty(items=[("START", "Start", ""), ("FINISH", "Finish", "")])
    width: FloatProperty(name="Width", default=24.0, min=4.0, max=200.0)
    depth: FloatProperty(name="Depth", default=12.0, min=2.0, max=200.0)

    def execute(self, context):
        c = _cursor_game(context)
        near, heading, _ = _nearest_route(context, c)
        center = near if near is not None and math.dist(near, c) < 40 else c
        obj = C.area_object(self.kind, M.Area(center=center, heading=heading or 0.0, width=self.width, depth=self.depth))
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class MR_OT_add_checkpoint(bpy.types.Operator):
    bl_idname = "mr.add_checkpoint"
    bl_label = "Add Checkpoint"
    bl_description = ("Add a native timed checkpoint (gaRaceSplitTimeAI gate + four boards) at the 3D cursor; "
                      "its order follows the AI route")
    bl_options = UNDO
    radius: FloatProperty(name="Radius", default=21.0, min=4.0, max=120.0)
    extra_time: FloatProperty(name="Extra time (s)", default=60.0, min=0.0)

    def execute(self, context):
        c = _cursor_game(context)
        near, heading, _ = _nearest_route(context, c)
        center = near if near is not None and math.dist(near, c) < 30 else c
        cp = M.Checkpoint(uid=M.new_uid("cp_"), center=center, radius=self.radius, extra_time=self.extra_time,
                          heading=heading or 0.0)
        obj = C.checkpoint_object(cp, len(C.studio_objects("CHECKPOINT")))
        renumber_checkpoints(context)
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


def renumber_checkpoints(context):
    context.view_layer.update()          # new objects need an evaluated matrix_world
    cps = C.studio_objects("CHECKPOINT")
    route, pts = _route_frame(context)
    if len(pts) >= 2:
        from .core.ai import resample_route
        line = resample_route(pts, 2.0)
        def along(o):
            g = C.b2g(o.matrix_world.translation)
            return min(range(len(line)), key=lambda i: (line[i][0] - g[0]) ** 2 + (line[i][2] - g[2]) ** 2)
        cps.sort(key=along)
    else:
        cps.sort(key=lambda o: o.mr.order)
    for i, o in enumerate(cps):
        o.mr.order = i
        o.name = f"MR Checkpoint {i + 1}"
    return cps


class MR_OT_place_checkpoints(bpy.types.Operator):
    bl_idname = "mr.place_checkpoints"
    bl_label = "Place Checkpoints Along Route"
    bl_description = "Replace all checkpoints by gates evenly spaced along the AI route"
    bl_options = UNDO
    count: IntProperty(name="Count", default=4, min=1, max=99)
    radius: FloatProperty(name="Radius", default=21.0, min=4.0, max=120.0)
    extra_time: FloatProperty(name="Extra time (s)", default=60.0, min=0.0)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        route, pts = _route_frame(context)
        if len(pts) < 2:
            self.report({"ERROR"}, "Draw an AI route first")
            return {"CANCELLED"}
        for o in C.studio_objects("CHECKPOINT"):
            bpy.data.objects.remove(o, do_unlink=True)
        for i, (p, h) in enumerate(AI.place_along(pts, self.count)):
            C.checkpoint_object(M.Checkpoint(uid=M.new_uid("cp_"), center=p, radius=self.radius,
                                             extra_time=self.extra_time, heading=h), i)
        renumber_checkpoints(context)
        return {"FINISHED"}


class MR_OT_renumber_checkpoints(bpy.types.Operator):
    bl_idname = "mr.renumber_checkpoints"
    bl_label = "Renumber by Route"
    bl_description = "Number checkpoints in the order the AI route passes them and face them along the route"
    bl_options = UNDO

    def execute(self, context):
        cps = renumber_checkpoints(context)
        for o in cps:
            near, heading, _ = _nearest_route(context, tuple(C.b2g(o.matrix_world.translation)))
            if heading is not None:
                o.rotation_euler.z = C.heading_to_rot(heading)
        return {"FINISHED"}


class MR_OT_snap_markers(bpy.types.Operator):
    bl_idname = "mr.snap_markers"
    bl_label = "Snap to Ground"
    bl_description = "Put the selected (or all) markers and the AI route on the terrain surface"
    bl_options = UNDO
    lift: FloatProperty(name="Route lift", default=0.3, min=-5.0, max=10.0)

    def execute(self, context):
        bvh = _ground_bvh(context)
        if bvh is None:
            self.report({"ERROR"}, "No terrain")
            return {"CANCELLED"}
        kinds = ("START", "FINISH", "CHECKPOINT", "PACENOTE", "SOUND", "CAMERA", "ROUTE", "LIMIT", "PS2PROP")
        objs = [o for o in context.selected_objects if o.mr.kind in kinds]
        if not objs:            # nothing marker-like selected: snap every marker and route
            objs = [o for o in C.studio_objects() if o.mr.kind in kinds]
        for o in objs:
            if o.mr.kind in ("ROUTE", "LIMIT"):
                mi = o.matrix_world.inverted()
                for sp in o.data.splines:
                    for p in sp.points:
                        w = o.matrix_world @ p.co.xyz
                        g = ground_height_b(bvh, w.x, w.y)
                        if g is not None:
                            w.z = g + self.lift
                            p.co = (*(mi @ w), 1.0)
            else:
                w = o.matrix_world.translation
                g = ground_height_b(bvh, w.x, w.y)
                if g is not None:
                    o.location.z += g - w.z
        return {"FINISHED"}


class MR_OT_reverse_course(bpy.types.Operator):
    bl_idname = "mr.reverse_course"
    bl_label = "Reverse Direction"
    bl_description = "Reverse the AI route, swap start and finish, and turn checkpoints around"
    bl_options = UNDO

    def execute(self, context):
        route = C.active_route()
        if route is not None:
            pts = C.curve_points(route)[::-1]
            C.curve_object(route.name, pts, "ROUTE")
        start, finish = bpy.data.objects.get("MR Start Area"), bpy.data.objects.get("MR Finish Area")
        if start and finish:
            sm, fm = start.matrix_world.copy(), finish.matrix_world.copy()
            start.matrix_world, finish.matrix_world = fm, sm
            for o in (start, finish):
                o.rotation_euler.z += math.pi
        for o in C.studio_objects("CHECKPOINT"):
            o.rotation_euler.z += math.pi
        renumber_checkpoints(context)
        return {"FINISHED"}


# ===================================================================== routes & AI
class MR_OT_new_route(bpy.types.Operator):
    bl_idname = "mr.new_route"
    bl_label = "Draw AI Route"
    bl_description = ("Create a new AI route: from the selected curve/edges, or a two-point line at the 3D cursor "
                      "that you extend in Edit Mode (E to extrude points)")
    bl_options = UNDO

    def execute(self, context):
        obj = context.active_object
        pts = None
        if obj is not None and obj.type == "CURVE" and obj.mr.kind != "ROUTE":
            pts = [tuple(C.b2g(obj.matrix_world @ (p.co.xyz if hasattr(p.co, "xyz") else p.co)))
                   for sp in obj.data.splines[:1] for p in (sp.points if sp.type != "BEZIER" else sp.bezier_points)]
        elif obj is not None and obj.type == "MESH" and obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            verts = _ordered_path([v for v in bm.verts if v.select])
            pts = [tuple(C.b2g(obj.matrix_world @ v.co)) for v in verts]
            bpy.ops.object.mode_set(mode="OBJECT")
        if not pts or len(pts) < 2:
            c = _cursor_game(context)
            pts = [c, (c[0], c[1], c[2] + 40.0)]
        for r in C.studio_objects("ROUTE"):
            r.mr.route_active = False
        name = "MR AI Route" if not bpy.data.objects.get("MR AI Route") else f"MR AI Route {len(C.studio_objects('ROUTE')) + 1}"
        route = C.curve_object(name, pts, "ROUTE")
        route.mr.route_active = True
        for o in context.selected_objects:
            o.select_set(False)
        route.select_set(True)
        context.view_layer.objects.active = route
        return {"FINISHED"}


def _ordered_path(verts):
    if not verts:
        return []
    sel = set(verts)
    ends = [v for v in verts if sum(1 for e in v.link_edges if e.other_vert(v) in sel) <= 1]
    cur = ends[0] if ends else verts[0]
    out, seen = [cur], {cur}
    while True:
        nxt = next((e.other_vert(cur) for e in cur.link_edges if e.other_vert(cur) in sel and e.other_vert(cur) not in seen), None)
        if nxt is None:
            break
        out.append(nxt)
        seen.add(nxt)
        cur = nxt
    return out


class MR_OT_route_tool(bpy.types.Operator):
    bl_idname = "mr.route_tool"
    bl_label = "Route Tool"
    bl_options = UNDO
    action: EnumProperty(items=[("SMOOTH", "Smooth", "Smooth the route curve"),
                                ("RESAMPLE", "Resample", "Even point spacing"),
                                ("REVERSE", "Reverse", "Drive the route the other way"),
                                ("ACTIVATE", "Make Active", "Export this route as the native RaceLine")])
    spacing: FloatProperty(name="Spacing", default=10.0, min=1.0, max=100.0)

    @classmethod
    def description(cls, context, props):
        return {"SMOOTH": "Smooth the AI route", "RESAMPLE": "Re-space AI route points evenly",
                "REVERSE": "Reverse the AI route direction", "ACTIVATE": "Use the selected route for the game"}[props.action]

    def execute(self, context):
        obj = context.active_object if context.active_object and context.active_object.mr.kind == "ROUTE" else C.active_route()
        if obj is None:
            self.report({"ERROR"}, "No AI route")
            return {"CANCELLED"}
        pts = C.curve_points(obj)
        if self.action == "SMOOTH" and len(pts) > 2:
            for _ in range(2):
                pts = [pts[0]] + [tuple((pts[i - 1][k] + 2 * pts[i][k] + pts[i + 1][k]) / 4 for k in range(3))
                                  for i in range(1, len(pts) - 1)] + [pts[-1]]
        elif self.action == "RESAMPLE":
            from .core.ai import resample_route
            pts = resample_route(pts, self.spacing)
        elif self.action == "REVERSE":
            pts = pts[::-1]
        elif self.action == "ACTIVATE":
            for r in C.studio_objects("ROUTE"):
                r.mr.route_active = r is obj
            return {"FINISHED"}
        mw = obj.matrix_world.copy()
        obj.matrix_world = mw.Identity(4)
        C.curve_object(obj.name, pts, "ROUTE")
        return {"FINISHED"}


class MR_OT_check_route(bpy.types.Operator):
    bl_idname = "mr.check_route"
    bl_label = "Check Route"
    bl_description = "Check corners, grades, ground contact and the start/checkpoint/finish order along the route"

    def execute(self, context):
        project = C.scene_to_project(context)
        hf = COL.HeightField(COL.terrain_triangles(project)) if project.meshes_with("terrain") else None
        issues = AI.route_issues(project, (lambda x, z: hf.ground(x, z)) if hf else None)
        from .core.validate import Finding
        _set_findings(context, [Finding(i.severity, "gameplay", i.message, {"route_point": i.index}, i.position)
                                for i in issues])
        self.report({"INFO"} if not issues else {"WARNING"}, f"{len(issues)} route issue(s) (Build > Problems)")
        return {"FINISHED"}


class MR_OT_generate_limits(bpy.types.Operator):
    bl_idname = "mr.generate_limits"
    bl_label = "Generate Limit Curves"
    bl_description = "Create the four editable gaLimitsAI lines from the route (switches limits to Manual)"
    bl_options = UNDO

    def execute(self, context):
        s = _settings(context)
        project = C.scene_to_project(context)
        project.limits.mode = "auto" if s.limits_mode == "manual" else s.limits_mode
        lists = AI.limit_lists(project)
        for name, pts in lists.items():
            C.curve_object(f"MR {name}", pts, "LIMIT", (1.0, 0.3, 0.3, 1.0))
        s.limits_mode = "manual"
        return {"FINISHED"}


class MR_OT_ai_preview(bpy.types.Operator):
    bl_idname = "mr.ai_preview"
    bl_label = "Preview AI Path"
    bl_description = ("Build the native AI heading field from the route and trace the path a car steering by it "
                      "would take from the start (yellow line)")

    def execute(self, context):
        project = C.scene_to_project(context)
        if len(project.route.points) < 2:
            self.report({"ERROR"}, "Draw an AI route first")
            return {"CANCELLED"}

        def work(progress):
            line = AI.raceline(project)
            progress("AI field", 0.2)
            sfl = AI.sfl_bytes(project, line)
            progress("trace", 0.8)
            a, b = line[0], line[1]
            return AI.simulate_ai_path(sfl, line[0], math.degrees(math.atan2(b[0] - a[0], b[2] - a[2])),
                                       stop_at=line[-1])

        def done(ctx, path):
            name = "MR AI Path Preview"
            obj = C.curve_object(name, path[::2], "DIAGNOSTIC", (1.0, 0.9, 0.1, 1.0))
            obj.mr.kind = "DIAGNOSTIC"
            C.link(obj, "diagnostics")
            end = path[-1]
            final = project.route.points[-1]
            return f"AI path traced: {len(path)} m, ends {math.dist(end, final):.0f} m from the route end"
        jobs.start(context, "AI preview", work, done)
        return {"FINISHED"}


class MR_OT_generate_pacenotes(bpy.types.Operator):
    bl_idname = "mr.generate_pacenotes"
    bl_label = "Generate Pace Notes"
    bl_description = "Create editable pace-note arrows at the route's corners (switches pace notes to Manual)"
    bl_options = UNDO

    def execute(self, context):
        project = C.scene_to_project(context)
        for o in C.studio_objects("PACENOTE"):
            bpy.data.objects.remove(o, do_unlink=True)
        notes = AI.auto_pacenotes(AI.raceline(project))
        for p, h, nid in notes:
            C.pacenote_object(M.PaceNote(uid=M.new_uid("pn_"), position=p, heading=h, note_id=nid))
        _settings(context).pacenote_mode = "manual"
        self.report({"INFO"}, f"{len(notes)} pace notes")
        return {"FINISHED"}


# ===================================================================== validation & build
class MR_OT_validate(bpy.types.Operator):
    bl_idname = "mr.validate"
    bl_label = "Check Course"
    bl_description = "Check geometry, collision, gameplay and resources; problems are listed below"

    def execute(self, context):
        try:
            project = C.scene_to_project(context)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        from .core.validate import summary, validate_project
        findings = validate_project(project, resource_root=C.resource_root(context),
                                    project_dir=C.project_dir(context.scene))
        _set_findings(context, findings)
        sm = summary(findings)
        self.report({"WARNING"} if sm["errors"] else {"INFO"},
                    f"{sm['errors']} error(s), {sm['warnings']} warning(s), {sm['info']} advice")
        return {"FINISHED"}


class MR_OT_build(bpy.types.Operator):
    bl_idname = "mr.build_course"
    bl_label = "Build Course"
    bl_description = ("Check the course, write every game file (geometry, collision, surfaces, textures, scene, "
                      "AI), register it in COURSE-CAP2 and publish the build folder")

    def execute(self, context):
        s = _settings(context)
        pdir = C.project_dir(context.scene)
        if pdir is None:
            self.report({"ERROR"}, "Save the .blend file (or set a project folder) before building")
            return {"CANCELLED"}
        try:
            save_project(context, pdir)
            project = C.scene_to_project(context, project_dir_path=pdir)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        root = C.resource_root(context)
        out = Path(bpy.path.abspath(s.build_output)) if s.build_output else pdir / "build"
        package = s.make_package
        from .core.build import build_course

        def work(progress):
            return build_course(project, project_dir=pdir, resource_root=root, output=out, progress=progress,
                                run_cap2=package)

        def done(ctx, result):
            st = _settings(ctx)
            _set_findings(ctx, result.findings)
            if result.ok:
                st.last_build = str(result.output)
                st.collision_state = "OK"
                cap2 = result.report.get("cap2", {}).get("output", "")
                return f"Built {result.output}" + (f"; game package {cap2}" if cap2 else "")
            errs = result.errors()
            raise RuntimeError(f"build stopped: {errs[0].message if errs else 'see Problems'}")
        jobs.start(context, "Build course", work, done)
        return {"FINISHED"}


class MR_OT_select_finding(bpy.types.Operator):
    bl_idname = "mr.select_finding"
    bl_label = "Go to Problem"
    bl_description = "Select the object of this problem and frame its location"
    index: IntProperty()

    def execute(self, context):
        s = _settings(context)
        if not 0 <= self.index < len(s.findings):
            return {"CANCELLED"}
        f = s.findings[self.index]
        refs = dict(part.split("=", 1) for part in f.ref.split(";") if "=" in part)
        target = None
        for o in C.studio_objects():
            if o.mr.uid and o.mr.uid in (refs.get("mesh"), refs.get("checkpoint")):
                target = o
        if refs.get("area") == "start":
            target = bpy.data.objects.get("MR Start Area")
        if refs.get("area") == "finish":
            target = bpy.data.objects.get("MR Finish Area")
        if target is None and refs.get("route_point") is not None:
            target = C.active_route()
        if target is not None:
            for o in context.selected_objects:
                o.select_set(False)
            target.hide_set(False)
            target.select_set(True)
            context.view_layer.objects.active = target
        if f.has_position:
            context.scene.cursor.location = f.position
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                region = next(r for r in area.regions if r.type == "WINDOW")
                with context.temp_override(area=area, region=region):
                    if f.has_position:
                        bpy.ops.view3d.view_center_cursor()
                    elif target is not None:
                        bpy.ops.view3d.view_selected()
        return {"FINISHED"}


class MR_OT_open_folder(bpy.types.Operator):
    bl_idname = "mr.open_folder"
    bl_label = "Open Build Folder"
    bl_description = "Show the last build in the file browser"

    def execute(self, context):
        path = _settings(context).last_build
        if path and os.path.isdir(path):
            if os.name == "nt":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        return {"FINISHED"}


class MR_OT_section(bpy.types.Operator):
    bl_idname = "mr.section"
    bl_label = "Course Studio Section"
    bl_description = "Switch the Course Studio section"
    section: StringProperty()

    def execute(self, context):
        _settings(context).section = self.section
        return {"FINISHED"}


CLASSES = (
    MR_OT_new_course, MR_OT_open_retail, MR_OT_open_project, MR_OT_save_project, MR_OT_import_geometry,
    MR_OT_reopen_build, MR_OT_add_terrain_grid, MR_OT_set_role, MR_OT_carve_road, MR_OT_merge_terrain,
    MR_OT_find_gaps, MR_OT_split_terrain, MR_OT_align_seam, MR_OT_bake_lighting, MR_OT_add_object,
    MR_OT_make_proxy, MR_OT_add_blocker, MR_OT_add_sound, MR_OT_add_physical, MR_OT_new_material, MR_OT_load_texture,
    MR_OT_export_texture, MR_OT_texture_users, MR_OT_select_material_faces, MR_OT_build_collision,
    MR_OT_collision_diff, MR_OT_preview_collision, MR_OT_probe_cursor, MR_OT_add_area, MR_OT_add_checkpoint,
    MR_OT_place_checkpoints, MR_OT_renumber_checkpoints, MR_OT_snap_markers, MR_OT_reverse_course,
    MR_OT_new_route, MR_OT_route_tool, MR_OT_check_route, MR_OT_generate_limits, MR_OT_ai_preview,
    MR_OT_generate_pacenotes, MR_OT_validate, MR_OT_build, MR_OT_select_finding, MR_OT_open_folder,
    MR_OT_section,
)
