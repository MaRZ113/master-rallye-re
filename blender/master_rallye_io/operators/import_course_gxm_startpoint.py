"""Read-only visualization of the decoded version-7 GXM startpoint mesh."""
from __future__ import annotations

import hashlib
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..blender_mesh import create_collection
from ..library import parse_course_gxm_model_v7, parse_course_txt


def _contains_object(collection, target):
    if target is None:
        return False
    if target.name in collection.objects:
        return True
    return any(_contains_object(child, target) for child in collection.children)


class IMPORT_SCENE_OT_master_rallye_course_gxm_startpoint(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.master_rallye_course_gxm_startpoint"
    bl_label = "Import GXM Startpoint Mesh"
    bl_description = "Import decoded version-7 startpoint triangles from a paired GXM/TXT source"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".gxm"
    filter_glob: StringProperty(default="*.gxm", options={"HIDDEN"})

    def execute(self, context):
        source = Path(self.filepath).resolve()
        txt_source = source.with_suffix(".txt")
        try:
            if not source.is_file() or not txt_source.is_file():
                raise ValueError("GXM topology import needs a same-stem GXM and TXT pair")
            raw = source.read_bytes()
            model = parse_course_gxm_model_v7(source, parse_course_txt(txt_source))
            node = model.find_mesh("startpoint")
            triangle_range = model.mesh_triangle_indices(node)
            position_indices = tuple(sorted(set(model.mesh_position_indices(node))))
            if not position_indices:
                raise ValueError("startpoint moMesh has no triangle position references")
            index_map = {source_index: local_index for local_index, source_index in enumerate(position_indices)}
            vertices = [model.position(index) for index in position_indices]
            faces = [
                tuple(index_map[index] for index in model.triangle(triangle_index).position_indices)
                for triangle_index in triangle_range
            ]

            course_roots = [
                collection for collection in bpy.data.collections
                if collection.get("mr_resource_kind") == "course"
                and str(collection.get("mr_course_identity", "")).casefold().endswith(source.stem.casefold())
            ]
            active_roots = [root for root in course_roots if _contains_object(root, context.object)]
            if len(active_roots) == 1:
                root = active_roots[0]
            elif len(course_roots) == 1:
                root = course_roots[0]
            elif len(course_roots) > 1:
                raise ValueError(f"multiple course collections match {source.stem!r}; select one of their objects")
            else:
                root = bpy.data.collections.get(f"Master Rallye Course - {source.stem}")
            if root is None:
                root = create_collection(f"Master Rallye Course - {source.stem}")
                root["mr_resource_kind"] = "course"
                root["mr_course_identity"] = source.stem
                root["mr_read_only"] = True
                root["mr_import_note"] = "Created for read-only GXM source-topology diagnostics; no course DX imported"
            elif root.get("mr_resource_kind") != "course":
                raise ValueError(f"collection {root.name!r} is not marked as a course")

            helpers = next((child for child in root.children if child.name.startswith("Course Helpers")), None)
            if helpers is None:
                helpers = create_collection("Course Helpers", root)
                helpers["mr_decode_status"] = "version-7 GXM source mesh topology decoded"
            if any(child.get("mr_gxm_source") == str(source) for child in helpers.children):
                raise ValueError(f"this GXM source is already imported under {helpers.name}")

            digest = hashlib.sha256(raw).hexdigest()
            mesh = bpy.data.meshes.new(f"GXM startpoint mesh - {source.stem}")
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            obj = bpy.data.objects.new(f"GXM startpoint - {source.stem}", mesh)
            helpers.objects.link(obj)
            obj["mr_resource_kind"] = "course"
            obj["mr_read_only"] = True
            obj["mr_course_helper_kind"] = "GXM decoded source mesh"
            obj["mr_course_identity"] = source.stem
            obj["mr_gxm_source"] = str(source)
            obj["mr_gxm_sha256"] = digest
            obj["mr_source_node_name"] = node.name
            obj["mr_source_node_index"] = node.ordinal
            obj["mr_source_node_parent_id"] = -1 if node.parent_id is None else node.parent_id
            obj["mr_source_node_byte_offset"] = node.record_offset
            obj["mr_source_node_byte_size"] = node.record_size
            obj["mr_source_mesh_index"] = node.mesh_index
            obj["mr_source_mesh_size"] = node.mesh_size
            obj["mr_source_triangle_indices"] = list(triangle_range)
            obj["mr_source_position_indices"] = list(position_indices)
            obj["mr_source_position_pool_offset"] = model.positions.offset
            obj["mr_source_to_blender"] = "identity; HIGH_CONFIDENCE_INFERENCE from source-to-DX and DX-to-Blender transforms"
            obj["mr_geometry_status"] = "version-7 triangle records resolved to source positions; gameplay role UNKNOWN"
            self.report({"INFO"}, f"Imported {len(faces)} decoded source triangles and {len(vertices)} positions")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
