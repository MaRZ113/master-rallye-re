"""3D View overlays: route direction, trigger zones, checkpoint boards, area arrows, limits, problems.

Batches are rebuilt only when a course object changed (depsgraph handler sets
a flag), so moving one route point does not rebuild everything every frame.
"""
from __future__ import annotations

import math

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from . import convert as C

_HANDLE = None
_STATE = {"dirty": True, "batches": []}


def _shader():
    try:
        return gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
    except Exception:
        return gpu.shader.from_builtin("UNIFORM_COLOR")


def mark_dirty(*_args):
    _STATE["dirty"] = True


def _circle(center, radius, n=48, z=0.3):
    return [center + Vector((radius * math.cos(2 * math.pi * k / n), radius * math.sin(2 * math.pi * k / n), z))
            for k in range(n + 1)]


def _arrow(origin, forward, length, width):
    f = forward.normalized() * length
    side = Vector((-f.y, f.x, 0.0)).normalized() * width
    tip = origin + f
    return [origin, tip, tip, tip - f * 0.3 + side, tip, tip - f * 0.3 - side]


def _rebuild(context):
    s = context.scene.mr_studio
    lines = []   # (points as list of line pairs, colour, width)
    def add(pairs, colour, width=2.0):
        if pairs:
            lines.append((pairs, colour, width))
    route = C.active_route()
    if route is not None:
        pts = [route.matrix_world @ p.co.xyz for sp in route.data.splines[:1] for p in sp.points]
        pairs = []
        total = 0.0
        for a, b in zip(pts, pts[1:]):
            seg = (b - a).length
            if seg < 1e-6:
                continue
            k = 0.0
            while k < seg:
                if int(total + k) % 40 == 0:
                    o = a + (b - a) * (k / seg)
                    pairs += _arrow(o, b - a, 4.0, 1.6)
                k += 10.0
            total += seg
        add(pairs, (0.25, 0.7, 1.0, 1.0), 2.5)
        if pts:
            add(_arrow(pts[0], (pts[1] - pts[0]) if len(pts) > 1 else Vector((0, 1, 0)), 12.0, 5.0), (0.2, 1, 0.3, 1), 3.0)
    if s.show_zones:
        for obj in C.studio_objects("CHECKPOINT"):
            c = obj.matrix_world.translation
            r = obj.matrix_world.to_scale().x
            ring = _circle(c, r)
            pairs = [p for a, b in zip(ring, ring[1:]) for p in (a, b)]
            add(pairs, (1.0, 0.85, 0.1, 0.9), 2.0)
            fwd = obj.matrix_world.to_3x3() @ Vector((0, 1, 0))
            fwd.z = 0
            add(_arrow(c + Vector((0, 0, 0.5)), fwd, r * 0.8, r * 0.25), (1.0, 0.6, 0.1, 1.0), 3.0)
            if obj.mr.boards:
                h = C.rot_to_heading(obj.matrix_world.to_euler().z)
                for k in range(4):
                    ang = math.radians(h + 45.0 + 90.0 * k)
                    rr = obj.mr.board_spacing / math.sqrt(2.0)
                    gx, gz = math.sin(ang) * rr, math.cos(ang) * rr
                    p = c + Vector((gx, -gz, 0.0))
                    add([p, p + Vector((0, 0, 3.0))], (1.0, 1.0, 1.0, 1.0), 4.0)
        for name, colour in (("MR Start Area", (0.2, 1.0, 0.3, 1.0)), ("MR Finish Area", (1.0, 0.85, 0.1, 1.0))):
            obj = bpy.data.objects.get(name)
            if obj is not None:
                fwd = obj.matrix_world.to_3x3() @ Vector((0, 1, 0))
                fwd.z = 0
                add(_arrow(obj.matrix_world.translation + Vector((0, 0, 0.5)), fwd, 10.0, 3.0), colour, 3.0)
    if s.show_limits:
        for obj in C.studio_objects("LIMIT"):
            pts = [obj.matrix_world @ p.co.xyz for sp in obj.data.splines[:1] for p in sp.points]
            add([p for a, b in zip(pts, pts[1:]) for p in (a, b)], (1.0, 0.3, 0.3, 0.8), 1.5)
    for f in s.findings:
        if f.has_position and f.severity == "error":
            p = Vector(f.position)
            add([p, p + Vector((0, 0, 6.0)), p + Vector((-1.5, 0, 0)), p + Vector((1.5, 0, 0)),
                 p + Vector((0, -1.5, 0)), p + Vector((0, 1.5, 0))], (1.0, 0.1, 0.1, 1.0), 3.0)
    shader = _shader()
    _STATE["batches"] = [(batch_for_shader(shader, "LINES", {"pos": [tuple(p) for p in pairs]}), colour, width)
                         for pairs, colour, width in lines]
    _STATE["shader"] = shader
    _STATE["dirty"] = False


def _draw():
    context = bpy.context
    scene = context.scene
    if scene is None or not hasattr(scene, "mr_studio") or not scene.mr_studio.show_overlays:
        return
    if bpy.data.collections.get(C.ROOT_COLLECTION) is None:
        return
    if _STATE["dirty"]:
        try:
            _rebuild(context)
        except Exception:
            _STATE["batches"] = []
            _STATE["dirty"] = False
    shader = _STATE.get("shader")
    if shader is None:
        return
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("NONE")
    region = context.region
    for batch, colour, width in _STATE["batches"]:
        shader.bind()
        try:
            shader.uniform_float("viewportSize", (region.width, region.height))
            shader.uniform_float("lineWidth", width)
        except Exception:
            pass
        shader.uniform_float("color", colour)
        batch.draw(shader)
    gpu.state.blend_set("NONE")


def _depsgraph(scene, depsgraph):
    for update in depsgraph.updates:
        idt = update.id
        obj = getattr(idt, "original", idt)
        if isinstance(obj, bpy.types.Object) and getattr(obj, "mr", None) is not None and obj.mr.kind != "NONE":
            _STATE["dirty"] = True
            if obj.mr.kind == "MESH" and update.is_updated_geometry and obj.mr.role in (
                    "terrain", "terrain_hidden", "collision"):
                s = scene.mr_studio
                if s.collision_state == "OK":
                    s.collision_state = "DIRTY"
            if (update.is_updated_geometry or update.is_updated_transform) and not scene.mr_studio.project_dirty:
                scene.mr_studio.project_dirty = True
            return


def register():
    global _HANDLE
    if bpy.app.background:
        return
    _HANDLE = bpy.types.SpaceView3D.draw_handler_add(_draw, (), "WINDOW", "POST_VIEW")


def register_handlers():
    if _depsgraph not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_depsgraph)


def unregister():
    global _HANDLE
    if _HANDLE is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_HANDLE, "WINDOW")
        _HANDLE = None
    if _depsgraph in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_depsgraph)
