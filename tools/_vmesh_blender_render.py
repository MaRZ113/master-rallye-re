"""Blender (headless) Workbench renderer used by vmesh_preview.py.  Run via ``blender -b --python``."""
import json
import math
import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
cfg = json.loads(argv[0])
bpy.ops.wm.read_factory_settings(use_empty=True)
for path in cfg["objs"]:
    bpy.ops.wm.obj_import(filepath=path)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.show_backface_culling = cfg.get("cull", False)
sh.color_type = "MATERIAL" if cfg["mode"] == "role" else "TEXTURE"
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.8, 0.85, 0.9)
sc.render.resolution_x, sc.render.resolution_y = cfg.get("size", [960, 420])
if cfg["mode"] == "role":
    colors = {int(k): v for k, v in cfg["colors"].items()}
    hide = set(cfg.get("hide", []))
    for o in meshes:
        for slot in o.material_slots:
            m = slot.material
            digits = [int(p) for p in m.name.split("_") if p.isdigit()]
            idx = digits[0] if digits else -1
            col = colors.get(idx, [0.6, 0.6, 0.6])
            m.diffuse_color = (col[0], col[1], col[2], 1.0)
if cfg.get("hide"):
    for o in list(meshes):
        keep = []
        mesh = o.data
        # hide polygons of hidden draws by material slot index
        for i, slot in enumerate(o.material_slots):
            digits = [int(p) for p in slot.material.name.split("_") if p.isdigit()]
            if digits and digits[0] in set(cfg["hide"]):
                for poly in mesh.polygons:
                    if poly.material_index == i:
                        poly.hide = True
        o.hide_set(False)
    # polygon hide does not affect render; delete them instead
    import bmesh
    for o in meshes:
        bpy.context.view_layer.objects.active = o
        bm = bmesh.new()
        bm.from_mesh(o.data)
        kill = []
        for f in bm.faces:
            slot = o.material_slots[f.material_index].material
            digits = [int(p) for p in slot.name.split("_") if p.isdigit()]
            if digits and digits[0] in set(cfg["hide"]):
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
pts = [o.matrix_world @ mathutils.Vector(c) for o in meshes for c in o.bound_box]
mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
c = (mn + mx) / 2
size = (mx - mn).length
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
for name, (az, el, zoom) in cfg["views"].items():
    az, el = math.radians(az), math.radians(el)
    d = size * 2
    cam.location = c + mathutils.Vector((d * math.cos(el) * math.sin(az), -d * math.cos(el) * math.cos(az), d * math.sin(el)))
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = size * zoom * 1.5
    sc.render.filepath = cfg["out"] + "_" + name + ".png"
    bpy.ops.render.render(write_still=True)
