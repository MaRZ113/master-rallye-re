"""Point-only visualization of the inferred France1 source startpoint cluster."""
from __future__ import annotations

import hashlib
import itertools
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..blender_mesh import create_collection
from ..library import parse_course_gxm_float3_pool_bytes, parse_course_gxm_object_table_bytes, parse_course_txt


def _contains_object(collection, target):
    if target is None:
        return False
    if target.name in collection.objects:
        return True
    return any(_contains_object(child, target) for child in collection.children)


def _startpoint_candidate(points):
    if len(points) < 8:
        return False
    first_eight = points[:8]
    if len(set(first_eight)) != 8:
        return False
    axes = [sorted({point[axis] for point in first_eight}) for axis in range(3)]
    if any(len(values) != 2 for values in axes):
        return False
    corners = set(itertools.product(*axes))
    return set(first_eight) == corners


class IMPORT_SCENE_OT_master_rallye_course_gxm_startpoint(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.master_rallye_course_gxm_startpoint"
    bl_label = "Import GXM Startpoint Point Candidate"
    bl_description = "Show the eight inferred France1 startpoint vertices as points, without invented edges or faces"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".gxm"
    filter_glob: StringProperty(default="*.gxm", options={"HIDDEN"})

    def execute(self, context):
        source = Path(self.filepath).resolve()
        txt_source = source.with_suffix(".txt")
        try:
            if not source.is_file() or not txt_source.is_file():
                raise ValueError("GXM startpoint probe needs a same-stem GXM and TXT pair")
            raw = source.read_bytes()
            txt = parse_course_txt(txt_source)
            table = parse_course_gxm_object_table_bytes(raw, txt, source.name)
            pool = parse_course_gxm_float3_pool_bytes(raw, table, source.name)
            matches = [node for node in table.nodes if node.name.casefold() == "startpoint"]
            if len(matches) != 1:
                raise ValueError(f"expected one literal startpoint node; found {len(matches)}")
            node = matches[0]
            if node.class_name.casefold() != "momesh" or (node.mesh_index, node.mesh_size) != (0, 12):
                raise ValueError("startpoint node does not match the observed Index 0 / Size 12 source record")
            if not _startpoint_candidate(pool.points):
                raise ValueError("first eight float3 points are not the observed eight-corner startpoint candidate")

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
                root["mr_import_note"] = "Created for read-only GXM point diagnostics; no course DX imported"
            elif root.get("mr_resource_kind") != "course":
                raise ValueError(f"collection {root.name!r} is not marked as a course")

            helpers = next((child for child in root.children if child.name.startswith("Course Helpers")), None)
            if helpers is None:
                helpers = create_collection("Course Helpers", root)
                helpers["mr_decode_status"] = "partial; GXM startpoint candidate points only"
            if any(child.get("mr_gxm_source") == str(source) for child in helpers.children):
                raise ValueError(f"this GXM source is already imported under {helpers.name}")

            digest = hashlib.sha256(raw).hexdigest()
            overlay = create_collection(f"GXM Startpoint Candidate - {source.stem}", helpers)
            overlay["mr_course_helper_kind"] = "GXM startpoint candidate point overlay"
            overlay["mr_gxm_source"] = str(source)
            overlay["mr_gxm_sha256"] = digest
            overlay["mr_source_node_name"] = node.name
            overlay["mr_source_node_index"] = node.ordinal
            overlay["mr_source_node_parent_id"] = -1 if node.parent_id is None else node.parent_id
            overlay["mr_source_node_byte_offset"] = node.record_offset
            overlay["mr_source_node_byte_size"] = node.record_size
            overlay["mr_source_mesh_index"] = node.mesh_index
            overlay["mr_source_mesh_size"] = node.mesh_size
            overlay["mr_point_pool_offset"] = pool.offset
            overlay["mr_point_pool_count"] = pool.count
            overlay["mr_source_to_blender"] = "identity; HIGH_CONFIDENCE_INFERENCE from source-to-DX and DX-to-Blender transforms"
            overlay["mr_geometry_status"] = "eight source positions shown as points; triangle connectivity is UNKNOWN"

            for point_index, position in enumerate(pool.points[:8]):
                obj = bpy.data.objects.new(f"GXM startpoint candidate point {point_index:02d}", None)
                overlay.objects.link(obj)
                obj.empty_display_type = "SPHERE"
                obj.empty_display_size = 0.6
                obj.show_in_front = True
                # GXM source coordinates compose to Blender coordinates by identity for this corpus pair.
                obj.location = position
                obj["mr_resource_kind"] = "course"
                obj["mr_read_only"] = True
                obj["mr_course_helper_kind"] = "GXM startpoint candidate point"
                obj["mr_course_identity"] = source.stem
                obj["mr_gxm_source"] = str(source)
                obj["mr_gxm_sha256"] = digest
                obj["mr_source_node_name"] = node.name
                obj["mr_source_node_index"] = node.ordinal
                obj["mr_source_node_parent_id"] = -1 if node.parent_id is None else node.parent_id
                obj["mr_source_mesh_index"] = node.mesh_index
                obj["mr_source_mesh_size"] = node.mesh_size
                obj["mr_source_point_index"] = point_index
                obj["mr_source_byte_offset"] = pool.offset + point_index * 12
                obj["mr_source_byte_size"] = 12
                obj["mr_source_position_xyz"] = list(position)
                obj["mr_geometry_status"] = "candidate vertex; no edges or faces inferred"

            self.report({"WARNING"}, "Imported 8 inferred startpoint points; connectivity and gameplay meaning remain unknown")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
