"""Course Studio Blender properties (scene settings, per-object and per-material data)."""
from __future__ import annotations

import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty, FloatVectorProperty,
                       IntProperty, PointerProperty, StringProperty)

from .core.materials import SHADER_LABELS, SURFACE_LABELS, SURFACE_TABLE

SECTIONS = [
    ("PROJECT", "Project", "Create, open, save and set up the course", "FILE_FOLDER", 0),
    ("TERRAIN", "Terrain", "Model and sculpt the landscape", "MESH_GRID", 1),
    ("OBJECTS", "Objects", "Buildings, props, obstacles and sound sources", "OBJECT_DATA", 2),
    ("MATERIALS", "Materials", "Textures, shaders and surface types", "MATERIAL", 3),
    ("COLLISION", "Collision", "Collision geometry and the game's collision tree", "MOD_PHYSICS", 4),
    ("MARKERS", "Markers", "Start, finish and checkpoints", "FLAG", 5),
    ("ROUTES", "Routes & AI", "AI route, limits and pace notes", "CURVE_PATH", 6),
    ("ENVIRONMENT", "Environment", "Sky, sound, timing and lighting", "WORLD", 7),
    ("BUILD", "Build", "Check the course and export it to the game", "EXPORT", 8),
]
ROLE_ITEMS = [
    ("NONE", "Not part of the course", "Ignored by the build"),
    ("terrain", "Terrain", "Drawn, drivable, collides and carries surface types"),
    ("terrain_hidden", "Invisible ground", "Collides and carries surface types, not drawn"),
    ("visual", "Visual only", "Drawn, no collision (give it a collision proxy to make it solid)"),
    ("collision", "Collision only", "Invisible solid geometry (walls, proxies, blockers)"),
    ("water", "Water", "Drawn water surface; never solid (Surface.xml)"),
    ("physical", "Physical object", "Movable rigid body (optional Renderer RigidProps module; the course runs "
                                    "without it, then the object is absent)"),
]
SHADER_ITEMS = [(k, v.split(" (")[0], v) for k, v in SHADER_LABELS.items()]
SURFACE_ITEMS = [("NONE", "None", "No surface type (objects that wheels never touch)")] + [
    (k, v, f"Surface.xml: friction {SURFACE_TABLE[k][2]:.2f}, restitution {SURFACE_TABLE[k][1]:.2f}, "
        f"{'solid' if SURFACE_TABLE[k][4] else 'not solid'}, tyre tracks {SURFACE_TABLE[k][3]}")
    for k, v in SURFACE_LABELS.items()]
ALPHA_ITEMS = [("opaque", "Opaque", ""), ("blend", "Blended", "Uses the texture alpha for transparency"),
               ("cutout", "Alpha test", "Cut-out transparency (vegetation, fences)")]
CLAMP_ITEMS = [("NONE", "Repeat", ""), ("u", "Clamp U", ""), ("v", "Clamp V", ""), ("uv", "Clamp U and V", "")]
KIND_ITEMS = [("NONE", "None", ""), ("MESH", "Geometry", ""), ("START", "Start area", ""), ("FINISH", "Finish area", ""),
              ("CHECKPOINT", "Checkpoint", ""), ("ROUTE", "AI route", ""), ("LIMIT", "Limit line", ""),
              ("PACENOTE", "Pace note", ""), ("SOUND", "Sound source", ""), ("CAMERA", "Replay camera", ""),
              ("PS2PROP", "PS2 physical object", ""), ("DIAGNOSTIC", "Diagnostic", "")]


def _mark_dirty(self, context):
    try:
        context.scene.mr_studio.project_dirty = True
    except Exception:
        pass


def template_items(self, context):
    from . import catalog
    return catalog.scene_enum_items(context)


class MRStudioPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__.split(".")[0]
    resource_root: StringProperty(name="Game resources", subtype="DIR_PATH",
                                  description="Folder with DataGx and DataScene (an unpacked Data.sma); "
                                              "found automatically when empty")
    cap2_input: StringProperty(name="COURSE-CAP2 input", subtype="FILE_PATH",
                               description="Accepted COURSE-CAP2 build input used to register new courses")

    def draw(self, context):
        self.layout.prop(self, "resource_root")
        self.layout.prop(self, "cap2_input")


class MRFinding(bpy.types.PropertyGroup):
    severity: StringProperty()
    category: StringProperty()
    message: StringProperty()
    hint: StringProperty()
    position: FloatVectorProperty(size=3)
    has_position: BoolProperty()
    ref: StringProperty()


class MRObjectProps(bpy.types.PropertyGroup):
    kind: EnumProperty(items=KIND_ITEMS, default="NONE")
    role: EnumProperty(name="Role", items=ROLE_ITEMS, default="NONE", update=_mark_dirty,
                       description="What this object is in the game")
    uid: StringProperty()
    source: StringProperty()
    order: IntProperty(name="Order", min=0, description="Checkpoint order along the route")
    extra_time: FloatProperty(name="Extra time (s)", default=60.0, min=0.0, max=3600.0,
                              description="Seconds added to the countdown when the car passes this checkpoint")
    boards: BoolProperty(name="Checkpoint boards", default=True,
                         description="Place the four native checkpoint boards around the gate")
    board_spacing: FloatProperty(name="Board spacing", default=26.0, min=4.0, max=120.0)
    route_active: BoolProperty(name="Active route", default=False,
                               description="The route exported as the native RaceLine and AI field")
    note_id: IntProperty(name="Pace note graphic", default=12, min=0, max=23,
                         description="Pace Note ID (Graphics to Display)")
    note_distance: FloatProperty(name="Distance", default=20.0, min=0.0, max=200.0)
    sound_template: StringProperty(name="Sound", description="Template sound source of the environment scene")
    proxy_of: StringProperty(name="Collision proxy of")
    ps2_model: EnumProperty(name="Model", items=[("haybale", "Hay bale", ""), ("tumblweed", "Tumbleweed", ""),
                                                  ("checkpoint", "Checkpoint barrel", "")], default="haybale")
    mass: FloatProperty(name="Mass (kg)", default=300.0, min=0.1, max=100000.0)
    trigger: FloatProperty(name="Wake distance", default=5.0, min=0.0, max=500.0,
                           description="Distance at which the body starts simulating (Trigger Distance)")
    shadow: BoolProperty(name="Casts shadow", default=True)
    phys_material: EnumProperty(name="Material", items=[("object", "Solid", "Low bounce, high grip"),
                                                        ("treeblend", "Light / springy", "Tumbleweed-like"),
                                                        ("metal", "Metal", "Drum-like")], default="object")


class MRMaterialProps(bpy.types.PropertyGroup):
    key: StringProperty(name="Key")
    label: StringProperty(name="Name", update=_mark_dirty)
    shader: EnumProperty(name="Shader", items=SHADER_ITEMS, default="ground", update=_mark_dirty)
    surface: EnumProperty(name="Surface", items=SURFACE_ITEMS, default="grass", update=_mark_dirty,
                          description="Physical surface type used by the game for grip, sound and tyre tracks")
    alpha: EnumProperty(name="Transparency", items=ALPHA_ITEMS, default="opaque", update=_mark_dirty)
    clamp: EnumProperty(name="Texture wrap", items=CLAMP_ITEMS, default="NONE", update=_mark_dirty)
    mip: FloatProperty(name="Mip bias", default=1.0, min=0.1, max=8.0, update=_mark_dirty)
    noise: BoolProperty(name="Ground detail pass", default=True, update=_mark_dirty,
                        description="Retail ground noise layer (ground shader only)")
    scroll: StringProperty(name="Scroll", description="Scrolling texture, e.g. v,+1 (waterfalls)")
    native: StringProperty(name="Native name", description="Original material name kept while unchanged")
    base_image: PointerProperty(name="Texture", type=bpy.types.Image, update=_mark_dirty)
    base_key: StringProperty()
    base_native: StringProperty()
    secondary_key: StringProperty(name="Environment layer", default="aluminium-tga")
    secondary_native: StringProperty()


class MRStudioSettings(bpy.types.PropertyGroup):
    section: EnumProperty(items=SECTIONS, default="PROJECT")
    project_dir: StringProperty(name="Project folder", subtype="DIR_PATH")
    resource_root: StringProperty(name="Game resources", subtype="DIR_PATH")
    project_dirty: BoolProperty(default=False)
    course_name: StringProperty(name="Name", default="NewCourse", update=_mark_dirty)
    course_key: StringProperty(name="Course folder", description="ASCII folder/file name of the exported course")
    course_title: StringProperty(name="Menu title", update=_mark_dirty)
    environment_template: EnumProperty(name="Environment", items=template_items,
                                       description="Retail scene providing sky, sound, physics, cameras and HUD")
    time_to_first_checkpoint: FloatProperty(name="Time to first checkpoint", default=90.0, min=5.0, max=3600.0,
                                            subtype="TIME_ABSOLUTE")
    percentage_time_change: FloatProperty(name="Time scale %", default=100.0, min=10.0, max=400.0)
    keep_template_sounds: BoolProperty(name="Keep template sound sources", default=False)
    sun_direction: FloatVectorProperty(name="Baked light direction", size=3, default=(0.35, -0.40, 0.85),
                                       subtype="DIRECTION")
    route_spacing: FloatProperty(name="Marker spacing", default=20.0, min=5.0, max=60.0,
                                 description="Distance between native RaceLine markers (Retail about 20)")
    limits_mode: EnumProperty(name="Limits", items=[
        ("auto", "Road corridor", "Reset lines at a fixed distance from the route"),
        ("wide", "Open terrain", "Reset lines 150/300 m from the route: free off-road driving"),
        ("manual", "Manual", "Edit the four limit curves")], default="auto", update=_mark_dirty)
    limits_inner: FloatProperty(name="Inner", default=25.0, min=3.0, max=500.0)
    limits_outer: FloatProperty(name="Outer", default=45.0, min=5.0, max=1000.0)
    pacenote_mode: EnumProperty(name="Pace notes", items=[("auto", "Automatic", "From route corners"),
                                                          ("manual", "Manual", "Pace-note objects"),
                                                          ("none", "None", "")], default="auto")
    collision_skirt: BoolProperty(name="Close map edge", default=True,
                                  description="Invisible walls along the open edge of the terrain (required for a "
                                              "consistent collision tree, like Retail $skirt)")
    collision_state: EnumProperty(items=[("NONE", "Not built", ""), ("DIRTY", "Out of date", ""), ("OK", "Up to date", "")],
                                  default="NONE")
    collision_summary: StringProperty()
    probe_spacing: FloatProperty(name="Probe spacing", default=6.0, min=1.0, max=50.0)
    preview_radius: FloatProperty(name="Preview radius", default=150.0, min=10.0, max=5000.0)
    build_output: StringProperty(name="Output folder", subtype="DIR_PATH")
    cap2_input: StringProperty(name="COURSE-CAP2 input", subtype="FILE_PATH",
                               description="Accepted COURSE-CAP2 build input (registers the course in the game menu)")
    make_package: BoolProperty(name="Make private game package", default=False,
                               description="Also run the COURSE-CAP2 build (private launcher package)")
    menu_group: IntProperty(name="Menu group", default=0, min=0, max=7)
    menu_position: IntProperty(name="Menu position", default=-1, min=-1, max=64, description="-1: after the last entry")
    findings: CollectionProperty(type=MRFinding)
    findings_index: IntProperty()
    filter_severity: EnumProperty(name="Show", items=[("ALL", "All", ""), ("error", "Errors", ""),
                                                      ("warning", "Warnings", ""), ("info", "Advice", "")],
                                  default="ALL")
    search: StringProperty(name="Search", options={"TEXTEDIT_UPDATE"})
    last_build: StringProperty()
    busy: StringProperty()
    progress: FloatProperty(min=0.0, max=1.0, subtype="FACTOR")
    show_overlays: BoolProperty(name="Course overlays", default=True)
    show_limits: BoolProperty(name="Limits", default=True)
    show_zones: BoolProperty(name="Trigger zones", default=True)


CLASSES = (MRStudioPreferences, MRFinding, MRObjectProps, MRMaterialProps, MRStudioSettings)


def register():
    bpy.types.Scene.mr_studio = PointerProperty(type=MRStudioSettings)
    bpy.types.Object.mr = PointerProperty(type=MRObjectProps)
    bpy.types.Material.mr = PointerProperty(type=MRMaterialProps)


def unregister():
    del bpy.types.Material.mr
    del bpy.types.Object.mr
    del bpy.types.Scene.mr_studio
