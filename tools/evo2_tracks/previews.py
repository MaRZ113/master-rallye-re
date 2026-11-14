"""Menu artwork for converted courses: two 128x128 Race Select screenshots per race (Blender render of the built
Course Studio project) and the category banner.

  python previews.py <project dir> --out <dir> [--blender <blender.exe>]

The project is exported as OBJ in Blender axes (MR world is right-handed, Y up -> Blender X, -Z, Y: a rotation) and
rendered with EEVEE from the start (behind the grid, looking down the route) and from mid-route.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_BLENDER = Path(r"D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64\blender.exe")


def export_obj(project, project_dir: Path, out: Path, *, skip_roles=("collision",)) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    tex_dir = out / "tex"
    tex_dir.mkdir(exist_ok=True)
    mtl = []
    for key, mat in project.materials.items():
        tkey = mat.textures[0] if mat.textures else None
        tex = project.textures.get(tkey) if tkey else None
        mtl.append(f"newmtl {key}\nKd 1 1 1\n")
        if tex and tex.source:
            src = project_dir / tex.source
            if src.is_file():
                shutil.copyfile(src, tex_dir / src.name)
                mtl.append(f"map_Kd tex/{src.name}\n")
                if tex.has_alpha or mat.alpha != "opaque":
                    mtl.append(f"map_d tex/{src.name}\n")
    (out / "scene.mtl").write_text("".join(mtl))
    lines = ["mtllib scene.mtl\n"]
    vbase, tbase = 1, 1
    for mesh in project.meshes:
        if mesh.role in skip_roles or not mesh.triangles:
            continue
        lines.append(f"o {mesh.name.replace(' ', '_')}\n")
        pos = mesh.positions
        for i in range(0, len(pos), 3):
            x, y, z = pos[i], pos[i + 1], pos[i + 2]
            lines.append(f"v {x:.3f} {-z:.3f} {y:.3f}\n")
        uv = mesh.uv or []
        ntri = len(mesh.triangles) // 3
        has_uv = len(uv) == ntri * 6
        if has_uv:
            for i in range(0, len(uv), 2):
                lines.append(f"vt {uv[i]:.5f} {1 - uv[i + 1]:.5f}\n")
        current = None
        for t in range(ntri):
            mat = mesh.materials[mesh.tri_material[t]] if mesh.tri_material else mesh.materials[0]
            if mat != current:
                lines.append(f"usemtl {mat}\n")
                current = mat
            a, b, c = mesh.triangles[3 * t:3 * t + 3]
            if has_uv:
                lines.append(f"f {a + vbase}/{tbase + 3 * t} {b + vbase}/{tbase + 3 * t + 1} {c + vbase}/{tbase + 3 * t + 2}\n")
            else:
                lines.append(f"f {a + vbase} {b + vbase} {c + vbase}\n")
        vbase += len(pos) // 3
        if has_uv:
            tbase += ntri * 3
    (out / "scene.obj").write_text("".join(lines))
    return out / "scene.obj"


def cameras(project):
    """Two views: behind the start looking down the route, and at the route's middle gate."""
    pts = project.route.points
    def view(i, back=14.0, up=3.2, ahead=40):
        a, b = pts[i], pts[min(len(pts) - 1, i + max(2, ahead // 10))]
        dx, dz = b[0] - a[0], b[2] - a[2]
        n = math.hypot(dx, dz) or 1
        dx, dz = dx / n, dz / n
        eye = (a[0] - dx * back, a[1] + up, a[2] - dz * back)
        target = (b[0], b[1] + 1.0, b[2])
        to_b = lambda p: (p[0], -p[2], p[1])
        return {"eye": to_b(eye), "target": to_b(target)}
    mid = len(pts) // 2
    if project.checkpoints:
        c = project.checkpoints[len(project.checkpoints) // 2].center
        mid = min(range(len(pts)), key=lambda i: (pts[i][0] - c[0]) ** 2 + (pts[i][2] - c[2]) ** 2)
        mid = max(2, mid - 3)
    return [view(1), view(mid)]


BLENDER_SCRIPT = r'''
import bpy, json, sys, math, mathutils
args = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=args["obj"], forward_axis="Y", up_axis="Z")
for mat in bpy.data.materials:
    mat.use_backface_culling = False
    if mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Roughness"].default_value = 0.9
                if "Specular IOR Level" in n.inputs: n.inputs["Specular IOR Level"].default_value = 0.1
            if n.type == "TEX_IMAGE": n.interpolation = "Closest" if False else "Linear"
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 256
scene.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.42, 0.58, 0.85, 1); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 18; cam.data.clip_end = 4000
for k, v in enumerate(args["views"]):
    eye = mathutils.Vector(v["eye"]); target = mathutils.Vector(v["target"])
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = args["out"] + f"/shot{k + 1}.png"
    bpy.ops.render.render(write_still=True)
'''


def render(project_dir: Path, out: Path, blender: Path = DEFAULT_BLENDER) -> list[Path]:
    from master_rallye.studio.model import load_project
    from PIL import Image
    project_dir, out = Path(project_dir).resolve(), Path(out).resolve()
    project = load_project(project_dir)
    export_obj(project, project_dir, out / "obj")
    script = out / "render_previews_blender.py"
    script.write_text(BLENDER_SCRIPT)
    args = {"obj": str(out / "obj" / "scene.obj"), "out": str(out), "views": cameras(project)}
    with open(out / "blender.log", "w") as log:
        subprocess.run([str(blender), "-b", "--factory-startup", "-P", str(script), "--", json.dumps(args)], check=True,
                       stdout=log, stderr=subprocess.STDOUT, timeout=1800)
    shots = []
    for k in (1, 2):
        im = Image.open(out / f"shot{k}.png").convert("RGBA").resize((128, 128), Image.LANCZOS)
        path = out / f"screenshot{k}.png"
        im.save(path)
        shots.append(path)
    return shots


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--blender", type=Path, default=DEFAULT_BLENDER)
    a = ap.parse_args(argv)
    print([str(p) for p in render(a.project, a.out, a.blender)])


if __name__ == "__main__":
    main()
