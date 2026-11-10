"""Blender scene <-> Course Studio project.

Source of truth inside Blender:

* geometry, markers and routes are ordinary objects in the ``MR Course``
  collections (``obj.mr`` says what they are);
* materials are Blender materials with ``material.mr`` settings;
* environment/build settings live in ``scene.mr_studio``; provenance and the
  stable project id in ``scene["mr_project_meta"]``.

Game space (RaceTest/DX: X, Y up, Z) maps to Blender ``(x, -z, y)``; headings
(degrees, 0 = game +Z) map to ``rotation_euler.z = radians(heading + 180)`` of
an object whose local +Y is the driving direction.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import bpy
import numpy as np

from .core import model as M
from .core import textures as T

ROOT_COLLECTION = "MR Course"
SECTIONS = {
    "terrain": "MR Terrain", "objects": "MR Objects", "collision": "MR Collision", "water": "MR Water",
    "markers": "MR Markers", "ai": "MR Routes & AI", "diagnostics": "MR Diagnostics",
}
ROLE_SECTION = {M.ROLE_TERRAIN: "terrain", M.ROLE_HIDDEN: "terrain", M.ROLE_VISUAL: "objects",
                M.ROLE_COLLISION: "collision", M.ROLE_WATER: "water"}
ROLE_COLOURS = {M.ROLE_COLLISION: (1.0, 0.25, 0.1, 0.35), M.ROLE_HIDDEN: (0.6, 0.2, 1.0, 0.35)}


def g2b(p):
    return (p[0], -p[2], p[1])


def b2g(v):
    return (v[0], v[2], -v[1])


def heading_to_rot(h: float) -> float:
    return math.radians(h + 180.0)


def rot_to_heading(r: float) -> float:
    h = math.degrees(r) - 180.0
    return (h + 180.0) % 360.0 - 180.0


# ---------------------------------------------------------------------- collections
def collection(name: str, parent=None):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    parent = parent or bpy.context.scene.collection
    if coll.name not in parent.children:
        try:
            parent.children.link(coll)
        except RuntimeError:
            pass
    return coll


def section(key: str):
    root = collection(ROOT_COLLECTION)
    return collection(SECTIONS[key], root)


def ensure_collections():
    root = collection(ROOT_COLLECTION)
    return {k: collection(v, root) for k, v in SECTIONS.items()}


def studio_objects(kind=None):
    root = bpy.data.collections.get(ROOT_COLLECTION)
    if root is None:
        return []
    out = []
    for obj in root.all_objects:
        if getattr(obj, "mr", None) is None or obj.mr.kind == "NONE":
            continue
        if kind is None or obj.mr.kind == kind:
            out.append(obj)
    return out


def link(obj, key):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    section(key).objects.link(obj)


# ---------------------------------------------------------------------- textures and materials
def texture_key_for_image(image) -> str:
    stem = os.path.splitext(image.name)[0].lower()
    stem = "".join(c if (c.isascii() and (c.isalnum() or c in "-_ ")) else "_" for c in stem).strip() or "texture"
    return stem if stem.endswith("-tga") else f"{stem}-tga"


def image_from_feed(name: str, data: bytes):
    w, h, rgba = T.decode_feed(data)
    img = bpy.data.images.get(name)
    if img is None or tuple(img.size) != (w, h):
        img = bpy.data.images.new(name, w, h, alpha=True)
    arr = np.frombuffer(rgba, dtype=np.uint8).reshape(h, w, 4)[::-1].astype(np.float32) / 255.0
    img.pixels.foreach_set(arr.ravel())
    img.pack()
    img["mr_texture_key"] = name
    return img


def image_rgba(image):
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    arr = (np.clip(px.reshape(h, w, 4)[::-1], 0, 1) * 255 + 0.5).astype(np.uint8)
    return w, h, arr.tobytes()


def build_preview_nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.get("MR Base")
    image = mat.mr.base_image
    if image is not None:
        if tex is None:
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.name = "MR Base"
            tex.location = (-400, 200)
        tex.image = image
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if mat.mr.alpha != "opaque":
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    colour = {"water": (0.1, 0.3, 0.6, 1.0)}.get(mat.mr.shader)
    if image is None and colour:
        bsdf.inputs["Base Color"].default_value = colour
    try:
        mat.surface_render_method = "BLENDED" if mat.mr.alpha == "blend" else "DITHERED"
    except Exception:
        pass
    bsdf.inputs["Roughness"].default_value = 0.9


def material_to_blender(project: M.CourseProject, key: str, resource_root: Path | None):
    name = f"MR {key}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    src = project.materials[key]
    p = mat.mr
    p.key = key
    p.label = src.label or key
    p.shader = src.shader
    p.surface = src.surface or "NONE"
    p.alpha = src.alpha
    p.clamp = src.clamp or "NONE"
    p.mip = src.mip
    p.noise = src.noise
    p.scroll = src.scroll or ""
    p.native = src.native or ""
    base = src.textures[0] if src.textures else None
    p.base_key = base or ""
    if len(src.textures) > 1 and src.textures[1]:
        p.secondary_key = src.textures[1]
        sec = project.textures.get(src.textures[1])
        p.secondary_native = (sec.native or "") if sec else ""
    if base:
        tex = project.textures.get(base)
        p.base_native = (tex.native or "") if tex else ""
        img = bpy.data.images.get(base)
        if img is None and tex is not None:
            data = None
            if tex.native and resource_root is not None:
                from .core.validate import ci_path
                path = ci_path(resource_root, tex.native)
                if path is not None:
                    data = path.read_bytes()
            if data is not None:
                try:
                    img = image_from_feed(base, data)
                except Exception:
                    img = None
            elif tex.source and project.extras.get("project_dir"):
                path = Path(project.extras["project_dir"]) / tex.source
                if path.exists():
                    img = bpy.data.images.load(str(path), check_existing=True)
                    img["mr_texture_key"] = base
        p.base_image = img
    build_preview_nodes(mat)
    return mat


def material_from_blender(mat, project: M.CourseProject, project_dir: Path | None):
    p = mat.mr
    key = p.key or M.safe_key(mat.name).lower()
    textures = [None, None, None]
    image = p.base_image
    if image is not None:
        tkey = image.get("mr_texture_key") or p.base_key or texture_key_for_image(image)
        textures[0] = tkey
        if tkey not in project.textures:
            native = p.base_native if (p.base_native and tkey == p.base_key and not image.is_dirty) else None
            tex = M.Texture(key=tkey, native=native or None, width=image.size[0], height=image.size[1])
            if not native:
                if project_dir is None:
                    raise ValueError("save the project before building: new textures are written into its folder")
                out = Path(project_dir) / "textures" / f"{tkey}.png"
                out.parent.mkdir(parents=True, exist_ok=True)
                w, h, rgba = image_rgba(image)
                out.write_bytes(T.encode_png(w, h, rgba))
                tex.source = f"textures/{tkey}.png"
                tex.has_alpha = T.has_alpha(rgba)
            project.textures[tkey] = tex
    elif p.base_key:
        textures[0] = p.base_key
        if p.base_key not in project.textures:
            project.textures[p.base_key] = M.Texture(key=p.base_key, native=p.base_native or None)
    if p.shader == "metal" and p.secondary_key:
        textures[1] = p.secondary_key
        if p.secondary_key not in project.textures:
            project.textures[p.secondary_key] = M.Texture(key=p.secondary_key, native=p.secondary_native or None)
    native = p.native or None
    if native and not _native_matches(native, p):
        native = None          # the user changed a field: rebuild the name from the fields
    project.materials[key] = M.Material(
        key=key, label=p.label or mat.name, shader=p.shader, surface=None if p.surface == "NONE" else p.surface,
        textures=textures, noise=p.noise, alpha=p.alpha, clamp="" if p.clamp == "NONE" else p.clamp, mip=p.mip,
        scroll=p.scroll or None, native=native)
    return key


def _native_matches(native: str, p) -> bool:
    from .core.materials import parse_native_name
    info = parse_native_name(native)
    return (info["shader"] == p.shader and (info["surface"] or "NONE") == p.surface
            and info["clamp"] == ("" if p.clamp == "NONE" else p.clamp)
            and abs(info["mip"] - p.mip) < 1e-6 and (info["alpha"] == "cutout") == (p.alpha == "cutout"))


# ---------------------------------------------------------------------- meshes
def mesh_to_object(mesh: M.Mesh, project: M.CourseProject, resource_root=None):
    data = bpy.data.meshes.new(mesh.name)
    verts = np.array(mesh.positions, dtype=np.float32).reshape(-1, 3)
    bverts = np.stack((verts[:, 0], -verts[:, 2], verts[:, 1]), axis=1)
    tris = np.array(mesh.triangles, dtype=np.int32).reshape(-1, 3)
    data.vertices.add(len(bverts))
    data.vertices.foreach_set("co", bverts.ravel())
    n = len(tris)
    data.loops.add(n * 3)
    data.loops.foreach_set("vertex_index", tris.ravel())
    data.polygons.add(n)
    data.polygons.foreach_set("loop_start", np.arange(0, 3 * n, 3, dtype=np.int32))
    if mesh.uv is not None and len(mesh.uv) == 6 * n:
        uv = data.uv_layers.new(name="UVMap")
        uvs = np.array(mesh.uv, dtype=np.float32).reshape(-1, 2).copy()
        uv.data.foreach_set("uv", uvs.ravel())
    if mesh.colors is not None and len(mesh.colors) == 12 * n:
        attr = data.color_attributes.new("MR_Color", "BYTE_COLOR", "CORNER")
        cols = np.array(mesh.colors, dtype=np.float32) / 255.0
        attr.data.foreach_set("color_srgb", cols)
    slots = []
    for key in mesh.materials:
        if key in project.materials:
            slots.append(material_to_blender(project, key, resource_root))
    for mat in slots:
        data.materials.append(mat)
    if mesh.tri_material and len(slots) == len(mesh.materials):
        data.polygons.foreach_set("material_index", np.array(mesh.tri_material, dtype=np.int32))
    data.update(calc_edges=True)
    data.validate(clean_customdata=False)
    if mesh.normals is not None and len(mesh.normals) == 9 * n:
        nrm = np.array(mesh.normals, dtype=np.float32).reshape(-1, 3)
        bn = np.stack((nrm[:, 0], -nrm[:, 2], nrm[:, 1]), axis=1)
        try:
            data.normals_split_custom_set([tuple(v) for v in bn])
        except Exception:
            pass
    obj = bpy.data.objects.new(mesh.name, data)
    obj.mr.kind = "MESH"
    obj.mr.role = mesh.role
    obj.mr.uid = mesh.id
    obj.mr.source = mesh.source
    obj["mr_group"] = mesh.group
    link(obj, ROLE_SECTION.get(mesh.role, "objects"))
    style_object(obj)
    return obj


def style_object(obj):
    role = obj.mr.role
    if role in (M.ROLE_COLLISION, M.ROLE_HIDDEN):
        obj.display_type = "WIRE"
        obj.color = ROLE_COLOURS[role]
        obj.hide_render = True
    else:
        obj.display_type = "TEXTURED"


def object_to_mesh(obj, depsgraph, project: M.CourseProject, project_dir: Path | None) -> M.Mesh | None:
    ev = obj.evaluated_get(depsgraph)
    data = ev.to_mesh()
    try:
        data.calc_loop_triangles()
        nt = len(data.loop_triangles)
        if nt == 0:
            return None
        mw = np.array(obj.matrix_world, dtype=np.float64)
        co = np.empty(len(data.vertices) * 3, dtype=np.float32)
        data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3).astype(np.float64)
        world = co @ mw[:3, :3].T + mw[:3, 3]
        positions = np.stack((world[:, 0], world[:, 2], -world[:, 1]), axis=1)
        tri_verts = np.empty(nt * 3, dtype=np.int32)
        data.loop_triangles.foreach_get("vertices", tri_verts)
        tri_loops = np.empty(nt * 3, dtype=np.int32)
        data.loop_triangles.foreach_get("loops", tri_loops)
        tri_mat = np.empty(nt, dtype=np.int32)
        data.loop_triangles.foreach_get("material_index", tri_mat)
        if obj.matrix_world.determinant() < 0:      # mirrored object: keep outward winding
            tri_verts = tri_verts.reshape(-1, 3)[:, [0, 2, 1]].ravel()
            tri_loops = tri_loops.reshape(-1, 3)[:, [0, 2, 1]].ravel()
        mesh = M.Mesh(id=obj.mr.uid or M.new_uid("mesh_"), name=obj.name, role=obj.mr.role, source=obj.mr.source,
                      group=obj.get("mr_group", ""))
        mesh.positions = positions.astype(np.float64).ravel().tolist()
        mesh.triangles = tri_verts.tolist()
        uv_layer = data.uv_layers.active
        if uv_layer is not None:
            uv = np.empty(len(data.loops) * 2, dtype=np.float32)
            uv_layer.data.foreach_get("uv", uv)
            uv = uv.reshape(-1, 2)[tri_loops]
            mesh.uv = uv.astype(np.float64).ravel().tolist()
        if obj.mr.role != M.ROLE_COLLISION:
            nrm = np.empty(len(data.loops) * 3, dtype=np.float32)
            try:
                data.corner_normals.foreach_get("vector", nrm)
            except AttributeError:
                data.loops.foreach_get("normal", nrm)
            nrm = nrm.reshape(-1, 3)[tri_loops].astype(np.float64)
            nm = np.linalg.inv(mw[:3, :3]).T
            nrm = nrm @ nm.T
            nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
            mesh.normals = np.stack((nrm[:, 0], nrm[:, 2], -nrm[:, 1]), axis=1).ravel().tolist()
            attr = data.color_attributes.get("MR_Color")
            if attr is not None:
                cols = np.empty(len(attr.data) * 4, dtype=np.float32)
                attr.data.foreach_get("color_srgb", cols)
                cols = cols.reshape(-1, 4)
                if attr.domain == "CORNER":
                    cols = cols[tri_loops]
                else:
                    cols = cols[tri_verts]
                mesh.colors = (np.clip(cols, 0, 1) * 255 + 0.5).astype(np.int32).ravel().tolist()
        keys = []
        for slot in obj.material_slots:
            mat = slot.material
            keys.append(material_from_blender(mat, project, project_dir) if mat else _fallback_material(project, obj))
        if not keys:
            keys = [_fallback_material(project, obj)]
        tri_mat = np.clip(tri_mat, 0, len(keys) - 1)
        used = sorted(set(tri_mat.tolist()))
        remap = {old: i for i, old in enumerate(used)}
        mesh.materials = [keys[i] for i in used]
        mesh.tri_material = [remap[i] for i in tri_mat.tolist()]
        return mesh
    finally:
        ev.to_mesh_clear()


def _fallback_material(project, obj):
    role = obj.mr.role
    key = "collision" if role == M.ROLE_COLLISION else "default_ground" if role in M.LAND_ROLES else "default_object"
    if key not in project.materials:
        shader = "ground" if role in M.LAND_ROLES else "object"
        project.materials[key] = M.Material(key=key, label=key, shader=shader,
                                            surface="grass" if role in M.LAND_ROLES else None,
                                            noise=role in M.LAND_ROLES, textures=[None, None, None])
    return key


# ---------------------------------------------------------------------- markers
def _empty(name, display, size, section_key, kind):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = display
    obj.empty_display_size = size
    obj.mr.kind = kind
    obj.mr.uid = M.new_uid(kind.lower() + "_")
    link(obj, section_key)
    return obj


def area_object(kind: str, area: M.Area):
    name = "MR Start Area" if kind == "START" else "MR Finish Area"
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        me = bpy.data.meshes.new(name)
        me.from_pydata([(-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0)], [], [(0, 1, 2, 3)])
        obj = bpy.data.objects.new(name, me)
        obj.mr.kind = kind
        obj.mr.uid = kind.lower()
        link(obj, "markers")
        obj.display_type = "WIRE"
        obj.show_in_front = True
        obj.hide_render = True
    center, heading, width, depth = area.center, area.heading, area.width, area.depth
    if area.corners:
        center, heading, width, depth = fit_rectangle([tuple(c) for c in area.corners])
    obj.location = g2b(center)
    obj.rotation_euler = (0.0, 0.0, heading_to_rot(heading))
    obj.scale = (width, depth, 1.0)
    obj.color = (0.1, 1.0, 0.2, 1.0) if kind == "START" else (1.0, 0.85, 0.1, 1.0)
    return obj


def fit_rectangle(corners):
    cx = sum(p[0] for p in corners) / 4
    cy = sum(p[1] for p in corners) / 4
    cz = sum(p[2] for p in corners) / 4
    e01 = math.dist(corners[0], corners[1])
    e12 = math.dist(corners[1], corners[2])
    # the longer side is across the road
    if e01 >= e12:
        a, b, width, depth = corners[0], corners[1], e01, e12
        c = corners[2]
        fx, fz = c[0] - b[0], c[2] - b[2]
    else:
        a, b, width, depth = corners[1], corners[2], e12, e01
        c = corners[3]
        fx, fz = corners[0][0] - corners[1][0], corners[0][2] - corners[1][2]
    heading = math.degrees(math.atan2(fx, fz))
    return (cx, cy, cz), heading, max(width, 1.0), max(depth, 1.0)


def area_from_object(obj) -> M.Area:
    loc = b2g(obj.matrix_world.translation)
    return M.Area(center=tuple(loc), heading=rot_to_heading(obj.matrix_world.to_euler().z),
                  width=abs(obj.scale.x), depth=abs(obj.scale.y))


def checkpoint_object(cp: M.Checkpoint, order: int):
    obj = _empty(cp.name or f"MR Checkpoint {order + 1}", "SPHERE", 1.0, "markers", "CHECKPOINT")
    obj.mr.uid = cp.uid
    obj.location = g2b(cp.center)
    obj.rotation_euler = (0.0, 0.0, heading_to_rot(cp.heading))
    obj.scale = (cp.radius, cp.radius, cp.radius)
    obj.mr.extra_time = cp.extra_time
    obj.mr.boards = cp.boards
    obj.mr.board_spacing = cp.board_spacing
    obj.mr.order = order
    obj.show_in_front = True
    return obj


def checkpoint_from_object(obj) -> M.Checkpoint:
    s = obj.matrix_world.to_scale()
    return M.Checkpoint(uid=obj.mr.uid, center=tuple(b2g(obj.matrix_world.translation)),
                        radius=float(max(abs(s.x), abs(s.y))), extra_time=obj.mr.extra_time,
                        heading=rot_to_heading(obj.matrix_world.to_euler().z), boards=obj.mr.boards,
                        board_spacing=obj.mr.board_spacing, name=obj.name)


def curve_object(name, points, kind, colour=(0.2, 0.6, 1.0, 1.0)):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "CURVE":
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        obj = bpy.data.objects.new(name, cu)
        obj.mr.kind = kind
        obj.mr.uid = M.new_uid(kind.lower() + "_")
        link(obj, "ai")
    cu = obj.data
    cu.splines.clear()
    sp = cu.splines.new("POLY")
    sp.points.add(max(0, len(points) - 1))
    for i, p in enumerate(points):
        b = g2b(p)
        sp.points[i].co = (b[0], b[1], b[2], 1.0)
    obj.color = colour
    obj.show_in_front = True
    return obj


def curve_points(obj):
    out = []
    mw = obj.matrix_world
    for sp in obj.data.splines:
        if sp.type == "BEZIER":
            pts = [mw @ bp.co for bp in sp.bezier_points]
        else:
            pts = [mw @ p.co.xyz for p in sp.points]
        out.extend(tuple(b2g(p)) for p in pts)
        break   # one polyline per route object
    return out


def pacenote_object(note: M.PaceNote):
    obj = _empty("MR Pace Note", "SINGLE_ARROW", 6.0, "ai", "PACENOTE")
    obj.mr.uid = note.uid
    obj.location = g2b(note.position)
    obj.rotation_euler = (math.radians(-90), 0.0, heading_to_rot(note.heading))
    obj.mr.note_id = note.note_id
    obj.mr.note_distance = note.distance
    return obj


def sound_object(snd: M.SoundAnchor):
    obj = _empty(f"MR Sound {snd.template}", "SPHERE", 3.0, "objects", "SOUND")
    obj.mr.uid = snd.uid
    obj.location = g2b(snd.position)
    obj.mr.sound_template = snd.template
    return obj


def camera_object(p):
    obj = _empty("MR Replay Camera", "CONE", 3.0, "ai", "CAMERA")
    obj.location = g2b(p)
    return obj


# ---------------------------------------------------------------------- whole project
def meta(scene) -> dict:
    try:
        return json.loads(scene.get("mr_project_meta", "{}"))
    except ValueError:
        return {}


def set_meta(scene, data: dict):
    scene["mr_project_meta"] = json.dumps(data)


def project_dir(scene) -> Path | None:
    s = scene.mr_studio
    if s.project_dir:
        return Path(bpy.path.abspath(s.project_dir))
    if bpy.data.filepath:
        return Path(bpy.data.filepath).with_suffix("").parent / (Path(bpy.data.filepath).stem + "_mrcourse")
    return None


def resource_root(context) -> Path | None:
    s = context.scene.mr_studio
    prefs = None
    try:
        prefs = context.preferences.addons[__package__.split(".")[0]].preferences
    except Exception:
        pass
    hints = [bpy.path.abspath(s.resource_root)] if s.resource_root else []
    if prefs is not None and getattr(prefs, "resource_root", ""):
        hints.append(bpy.path.abspath(prefs.resource_root))
    from .core import resolve_resource_root
    extra = [Path(h) for h in hints[1:]]
    here = Path(__file__).resolve()
    for up in list(here.parents)[:6]:
        extra += [up / "corpora" / "retail", up.parent / "corpora" / "retail"]
    return resolve_resource_root(hints[0] if hints else None, extra=extra)


def scene_to_project(context, *, project_dir_path: Path | None = None) -> M.CourseProject:
    scene = context.scene
    s = scene.mr_studio
    info = meta(scene)
    project = M.CourseProject(name=s.course_name or "Course", uid=info.get("uid") or M.new_uid())
    if info.get("provenance"):
        project.provenance = M.Provenance(**info["provenance"])
    project.history = info.get("history", [])
    project.extras = info.get("extras", {})
    context.view_layer.update()
    depsgraph = context.evaluated_depsgraph_get()
    pdir = project_dir_path or project_dir(scene)
    import base64
    for key in list(scene.keys()):
        if key.startswith("mr_blob_"):
            project.blobs[key[8:]] = base64.b64decode(scene[key])
    physical_to_project(context, project, depsgraph)
    for obj in studio_objects("MESH"):
        if obj.type != "MESH" or obj.mr.role in ("NONE", "physical"):
            continue
        mesh = object_to_mesh(obj, depsgraph, project, pdir)
        if mesh is not None:
            project.meshes.append(mesh)
    for obj in studio_objects("START"):
        project.start = area_from_object(obj)
    for obj in studio_objects("FINISH"):
        project.finish = area_from_object(obj)
    cps = sorted(studio_objects("CHECKPOINT"), key=lambda o: (o.mr.order, o.name))
    project.checkpoints = [checkpoint_from_object(o) for o in cps]
    route = active_route()
    if route is not None:
        project.route.points = curve_points(route)
    project.route.spacing = s.route_spacing
    project.limits.mode = s.limits_mode
    project.limits.inner, project.limits.outer = s.limits_inner, s.limits_outer
    if s.limits_mode == "manual":
        from .core.ai import LIMIT_NAMES
        lists = {}
        for name in LIMIT_NAMES:
            obj = bpy.data.objects.get(f"MR {name}")
            if obj is not None:
                lists[name] = curve_points(obj)
        project.limits.lists = lists
    project.pacenotes = [M.PaceNote(uid=o.mr.uid, position=tuple(b2g(o.matrix_world.translation)),
                                    heading=rot_to_heading(o.matrix_world.to_euler().z), note_id=o.mr.note_id,
                                    distance=o.mr.note_distance) for o in studio_objects("PACENOTE")]
    project.sounds = [M.SoundAnchor(uid=o.mr.uid, position=tuple(b2g(o.matrix_world.translation)),
                                    template=o.mr.sound_template, name=o.name.replace("MR Sound ", ""))
                      for o in studio_objects("SOUND")]
    env = project.environment
    env.template = s.environment_template
    env.time_to_first_checkpoint = s.time_to_first_checkpoint
    env.percentage_time_change = s.percentage_time_change
    env.keep_template_sounds = s.keep_template_sounds
    env.replay_cameras = [tuple(b2g(o.matrix_world.translation)) for o in studio_objects("CAMERA")]
    env.vertex_light = tuple(b2g(s.sun_direction))
    b = project.build
    b.course_key = M.safe_key(s.course_key or s.course_name)
    b.title = s.course_title or s.course_name
    b.output = bpy.path.abspath(s.build_output) if s.build_output else "build"
    b.catalog = bpy.path.abspath(s.cap2_input) if s.cap2_input else ""
    b.menu_group = s.menu_group
    b.menu_position = s.menu_position
    b.collision_skirt = s.collision_skirt
    b.pacenotes = s.pacenote_mode
    return project


def active_route():
    routes = studio_objects("ROUTE")
    active = [r for r in routes if r.mr.route_active]
    return (active or routes or [None])[0]


def project_to_scene(context, project: M.CourseProject, root: Path | None, *, clear=True):
    scene = context.scene
    s = scene.mr_studio
    if clear:
        clear_course()
    ensure_collections()
    s.course_name = project.name
    s.course_key = project.build.course_key or project.name
    s.course_title = project.build.title or project.name
    s.environment_template = project.environment.template
    s.time_to_first_checkpoint = project.environment.time_to_first_checkpoint
    s.percentage_time_change = project.environment.percentage_time_change
    s.keep_template_sounds = project.environment.keep_template_sounds
    s.limits_mode = project.limits.mode if project.limits.mode in ("auto", "wide", "manual") else "auto"
    s.limits_inner, s.limits_outer = project.limits.inner, project.limits.outer
    s.route_spacing = project.route.spacing
    s.menu_group = project.build.menu_group
    s.menu_position = project.build.menu_position
    s.collision_skirt = project.build.collision_skirt
    s.pacenote_mode = project.build.pacenotes
    set_meta(scene, {"uid": project.uid, "provenance": M.asdict(project.provenance) if hasattr(M, "asdict") else
                     project.provenance.__dict__, "history": project.history[-500:], "extras": project.extras})
    import base64
    for name, data in project.blobs.items():
        scene[f"mr_blob_{name}"] = base64.b64encode(data).decode("ascii")
    for mesh in project.meshes:
        mesh_to_object(mesh, project, root)
    for item in project.extras.get("ps2_props", []):
        if item["model"] in ("haybale", "tumblweed", "checkpoint"):
            ps2prop_object(item)
    area_object("START", project.start)
    area_object("FINISH", project.finish)
    for i, cp in enumerate(project.checkpoints):
        checkpoint_object(cp, i)
    if project.route.points:
        obj = curve_object("MR AI Route", project.route.points, "ROUTE")
        obj.mr.route_active = True
    if project.limits.mode == "manual":
        for name, pts in project.limits.lists.items():
            if pts:
                curve_object(f"MR {name}", pts, "LIMIT", (1.0, 0.3, 0.3, 1.0))
    for note in project.pacenotes:
        pacenote_object(note)
    for snd in project.sounds:
        sound_object(snd)
    for p in project.environment.replay_cameras:
        camera_object(p)
    s.collision_state = "DIRTY"


def clear_course():
    root = bpy.data.collections.get(ROOT_COLLECTION)
    if root is None:
        return
    for obj in list(root.all_objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)


# ---------------------------------------------------------------------- physical objects
def ps2prop_object(item):
    obj = _empty(f"MR PS2 {item['model']}", "CUBE", 0.6, "objects", "PS2PROP")
    obj.location = g2b(item["position"])
    obj.rotation_euler = (0.0, 0.0, heading_to_rot(item.get("heading", 0.0)))
    obj.mr.ps2_model = item["model"]
    obj.mr.mass = item.get("mass", 300.0)
    obj.mr.trigger = item.get("trigger", 5.0)
    obj.mr.shadow = item.get("shadow", True)
    return obj


def physical_to_project(context, project, depsgraph):
    """Physical objects -> extras['ps2_props'] (+ extras['ps2_models'] for Studio models)."""
    from .core import ps2_objects as P
    props, models = [], {}
    for obj in studio_objects("PS2PROP"):
        props.append({"model": obj.mr.ps2_model, "position": tuple(b2g(obj.matrix_world.translation)),
                      "heading": rot_to_heading(obj.matrix_world.to_euler().z), "mass": obj.mr.mass,
                      "trigger": obj.mr.trigger, "shadow": obj.mr.shadow,
                      **({} if obj.mr.ps2_model != "checkpoint" else {})})
    for obj in studio_objects("MESH"):
        if obj.type != "MESH" or obj.mr.role != "physical":
            continue
        key = M.safe_key(obj.data.name).lower()[:15]
        if key not in models:
            ev = obj.evaluated_get(depsgraph)
            me = ev.to_mesh()
            me.calc_loop_triangles()
            scale = obj.matrix_world.to_scale()
            uv = me.uv_layers.active
            verts, normals = [], []
            for tri in me.loop_triangles:
                for li in (tri.loops[0], tri.loops[2], tri.loops[1]):   # model space is the game's (left-handed) frame
                    v = me.vertices[me.loops[li].vertex_index].co
                    x, y, z = v.x * scale.x, v.y * scale.y, v.z * scale.z
                    u, w = (uv.data[li].uv if uv else (0.0, 0.0))
                    verts.append((x, z, -y, 0xFFFFFFFF, u, 1.0 - w))
                    n = me.loops[li].normal if hasattr(me.loops[li], "normal") else tri.normal
                    normals.append((n.x, n.z, -n.y))
            ev.to_mesh_clear()
            texture = None
            mat = obj.active_material
            if mat is not None and getattr(mat, "mr", None) is not None:
                texture = material_from_blender(mat, project, project_dir(context.scene))
                texture = project.materials[texture].textures[0]
            models[key] = {"vertices": verts, "normals": normals, "texture": texture,
                           "material": obj.mr.phys_material}
        dims = obj.dimensions
        size = (dims.x, dims.z, dims.y)
        props.append({"model": key, "position": tuple(b2g(obj.matrix_world.translation)),
                      "heading": rot_to_heading(obj.matrix_world.to_euler().z), "mass": obj.mr.mass,
                      "moi": P.box_inertia(obj.mr.mass, size), "trigger": obj.mr.trigger, "shadow": obj.mr.shadow})
    if props:
        project.extras["ps2_props"] = props
        project.extras["ps2_models"] = models
    else:
        project.extras.pop("ps2_props", None)
        project.extras.pop("ps2_models", None)
