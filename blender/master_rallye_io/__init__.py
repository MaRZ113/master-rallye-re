"""Master Rallye vehicle DX importer for Blender."""
from __future__ import annotations

bl_info = {
    "name": "Master Rallye Vehicle IO",
    "author": "master-rallye-re clean-room project",
    "version": (2, 0, 1),
    "blender": (4, 3, 0),
    "location": "File > Import; 3D View > Sidebar > Master Rallye",
    "description": "Import Master Rallye vehicle DX resources as editable meshes",
    "category": "Import-Export",
}

import bpy

from .operators import CLASSES as OPERATOR_CLASSES
from .ui import CLASSES as UI_CLASSES

CLASSES = OPERATOR_CLASSES + UI_CLASSES


def _menu_import(self, context):
    self.layout.operator("import_scene.master_rallye_dx", text="Master Rallye DX (.dx)")
    self.layout.operator(
        "import_scene.master_rallye_vehicle",
        text="Master Rallye Vehicle Folder",
    )


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(_menu_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(_menu_import)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
