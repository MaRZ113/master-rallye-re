"""Master Rallye vehicle tools and integrated Course Studio for Blender."""
from __future__ import annotations

bl_info = {
    "name": "Master Rallye IO",
    "author": "master-rallye-re clean-room project",
    "version": (5, 0, 0),
    "blender": (4, 3, 0),
    "location": "3D View > Sidebar > MR Course Studio; File > Import",
    "description": "Master Rallye Course Studio (create, edit and build courses) and vehicle asset tools",
    "category": "Import-Export",
}

import bpy

from . import studio
from .operators import CLASSES as OPERATOR_CLASSES
from .ui import CLASSES as UI_CLASSES  # vehicle/resource tools; the course UI is the Course Studio

CLASSES = OPERATOR_CLASSES + UI_CLASSES


def _menu_import(self, context):
    self.layout.operator("import_scene.master_rallye_dx", text="Master Rallye DX (.dx)")
    self.layout.operator(
        "import_scene.master_rallye_vehicle",
        text="Master Rallye Vehicle Folder",
    )


def _menu_export(self, context):
    self.layout.operator("export_scene.master_rallye_dx_attributes", text="Master Rallye DX - Safe Attributes")
    self.layout.operator("export_scene.master_rallye_dx_topology", text="Master Rallye DX - Topology Changing (Experimental)")
    self.layout.operator(
        "export_scene.master_rallye_dx_positions",
        text="Master Rallye DX — Positions Only (Experimental)",
    )


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    studio.register()
    bpy.types.TOPBAR_MT_file_import.append(_menu_import)
    bpy.types.TOPBAR_MT_file_export.append(_menu_export)


def unregister():
    studio.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(_menu_export)
    bpy.types.TOPBAR_MT_file_import.remove(_menu_import)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
