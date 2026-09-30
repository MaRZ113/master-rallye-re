"""Read-only import of an observed Master Rallye course DX render resource."""
from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy_extras.io_utils import ImportHelper

from ..blender_mesh import create_collection, import_dx_resource
from ..library import load_course_project


def _remove_collection_tree(collection):
    for child in list(collection.children):
        _remove_collection_tree(child)
    for obj in list(collection.objects):
        data = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)
    bpy.data.collections.remove(collection)


class IMPORT_SCENE_OT_master_rallye_course(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.master_rallye_course"
    bl_label = "Import Master Rallye Course"
    bl_description = "Import read-only course render geometry; RaceTest logic is available through the XML helper import"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".dx"
    filter_glob: StringProperty(default="*.dx", options={"HIDDEN"})
    load_textures: BoolProperty(name="Load DXT preview textures", default=True)
    collection_name: StringProperty(name="Collection name", default="")

    def execute(self, context):
        source = Path(self.filepath)
        root_name = self.collection_name.strip() or f"Master Rallye Course - {source.parent.name}"
        root = create_collection(root_name)
        root["mr_resource_kind"] = "course"
        root["mr_course_identity"] = source.parent.name
        root["mr_read_only"] = True
        root["mr_source_dx"] = str(source.resolve())
        render = create_collection("Render Geometry", root)
        create_collection("Course Helpers", root)["mr_decode_status"] = "Import the matching RaceTest XML to add semantic StartArea, FinishArea, and split trigger helpers"
        opaque = create_collection("Unknown - Opaque", root)
        opaque["mr_read_only"] = True
        opaque["mr_semantics_status"] = "tag100 and other unresolved course data are preserved as neutral metadata"
        try:
            project = load_course_project(source)
            if project.render is None:
                details = "; ".join(project.diagnostics) or "course render resource was not discovered"
                raise ValueError(details)
            model = project.render._parsed_model
            if not project.render.validation_passed:
                raise ValueError("course render geometry did not pass index/range validation")
            result = import_dx_resource(
                source,
                render,
                object_name=source.stem,
                import_sidecar=True,
                load_textures=self.load_textures,
                strict=True,
                show_collision=False,
                parsed_model=model,
                resource_kind="course",
            )
            result.object["mr_course_identity"] = source.parent.name
            result.object["mr_course_folder"] = str(source.parent.resolve())
            result.object["mr_course_sdk_model"] = "master_rallye.course_sdk.CourseProject"
            result.object["mr_course_sdk_read_only"] = True
            result.object["mr_course_sdk_diagnostics"] = "; ".join(project.diagnostics)
            root["mr_course_sdk_identity"] = project.identity
            root["mr_course_sdk_resource_counts"] = {
                "render_dx": len(project.resources.candidate_paths("render_dx")),
                "race_test_xml": len(project.resources.candidate_paths("race_test_xml")),
                "hnt": len(project.resources.candidate_paths("hnt")),
                "sfl": len(project.resources.candidate_paths("sfl")),
            }
            root["mr_course_tag100_status"] = project.render.tag100.semantics
            root["mr_course_tag100_present"] = project.render.tag100.present
            opaque["mr_tag100_byte_size"] = project.render.tag100.byte_size
            opaque["mr_tag100_sha256"] = project.render.tag100.sha256 or ""
            opaque["mr_tag100_boundary_status"] = project.render.tag100.boundary_status
            opaque["mr_tag100_semantics"] = project.render.tag100.semantics
        except Exception as error:
            _remove_collection_tree(root)
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        result.object.select_set(True)
        context.view_layer.objects.active = result.object
        self.report(
            {"WARNING"} if result.warnings else {"INFO"},
            f"Imported {source.name}: {model.vertex_count} vertices, "
            f"{model.triangle_count} source triangles, {len(model.physical_draws)} draws; "
            "course resource is read-only",
        )
        return {"FINISHED"}
