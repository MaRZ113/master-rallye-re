"""Master Rallye Course Studio (Blender side). Core logic lives in ``master_rallye.studio``."""
from __future__ import annotations

import bpy
from bpy.app.handlers import persistent

from . import catalog, draw, jobs, ops, panels, props

CLASSES = props.CLASSES + jobs.CLASSES + ops.CLASSES + panels.CLASSES


@persistent
def _save_post(*_args):
    """Saving the .blend also writes the course project next to it (portable, relative paths)."""
    scene = bpy.context.scene
    if scene is None or not hasattr(scene, "mr_studio") or bpy.data.collections.get("MR Course") is None:
        return
    try:
        ops.save_project(bpy.context)
    except Exception as exc:
        print(f"Course Studio: project not saved with the .blend: {exc}")


@persistent
def _load_post(*_args):
    draw.mark_dirty()
    for scene in bpy.data.scenes:
        if hasattr(scene, "mr_studio"):
            scene.mr_studio.busy = ""
            if scene.mr_studio.collision_state == "OK":
                scene.mr_studio.collision_state = "DIRTY"   # the in-memory tree is not stored in the .blend


def _menu_import(self, context):
    self.layout.operator("mr.open_project", text="Master Rallye Course Project (project.json)")


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    props.register()
    panels.register()
    draw.register()
    draw.register_handlers()
    bpy.app.handlers.save_post.append(_save_post)
    bpy.app.handlers.load_post.append(_load_post)
    bpy.types.TOPBAR_MT_file_import.append(_menu_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(_menu_import)
    for handler, items in ((_save_post, bpy.app.handlers.save_post), (_load_post, bpy.app.handlers.load_post)):
        if handler in items:
            items.remove(handler)
    draw.unregister()
    catalog.unregister()
    panels.unregister()
    props.unregister()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
