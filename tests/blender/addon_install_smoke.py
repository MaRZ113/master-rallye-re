"""Install, enable, and exercise the built add-on ZIP in an isolated profile."""
from __future__ import annotations

import json
import importlib
import atexit
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import bpy


values = sys.argv[sys.argv.index("--") + 1:]
if len(values) not in (1, 2, 3, 4, 5):
    raise SystemExit(
        "usage after --: <addon.zip> [synthetic.dx] or "
        "<addon.zip> <course.dx> <RaceTest.xml> [source.gxm] or "
        "<addon.zip> <synthetic.dx> <course.dx> <RaceTest.xml> [-|source.gxm]"
    )
archive = Path(values[0]).resolve()
smoke_output = Path(tempfile.mkdtemp(prefix="master-rallye-addon-smoke-", dir=archive.parent))
atexit.register(shutil.rmtree, smoke_output, ignore_errors=True)
fixture = Path(values[1]).resolve() if len(values) == 2 else None
course_pair = (Path(values[1]).resolve(), Path(values[2]).resolve()) if len(values) in (3, 4) else None
gxm_source = Path(values[3]).resolve() if len(values) == 4 else None
if len(values) == 5:
    fixture = Path(values[1]).resolve()
    course_pair = (Path(values[2]).resolve(), Path(values[3]).resolve())
    gxm_source = Path(values[4]).resolve() if values[4] != "-" else None


class _LayoutDrawProbe:
    def __init__(self, valid_icons):
        self.valid_icons = valid_icons
        self.calls = 0

    def box(self):
        self.calls += 1
        return self

    def grid_flow(self, **_kwargs):
        self.calls += 1
        return self

    def label(self, *, icon=None, **_kwargs):
        self.calls += 1
        self._check_icon(icon)

    def operator(self, _operator, *, icon=None, **_kwargs):
        self.calls += 1
        self._check_icon(icon)
        return SimpleNamespace()

    def prop(self, *_args, **_kwargs):
        self.calls += 1

    def _check_icon(self, icon):
        if icon and icon not in self.valid_icons:
            raise AssertionError(f"unsupported Blender panel icon {icon!r}")


def _draw_panel(panel_type, obj, valid_icons):
    from master_rallye_io import ui as addon_ui
    context = SimpleNamespace(object=obj)
    if not panel_type.poll(context):
        raise AssertionError(f"{panel_type.__name__}.poll rejected smoke context")
    layout = _LayoutDrawProbe(valid_icons)
    panel_type.draw(SimpleNamespace(layout=layout), context)
    if not layout.calls:
        raise AssertionError(f"{panel_type.__name__}.draw emitted no controls")
    return layout.calls
result = bpy.ops.preferences.addon_install(filepath=str(archive), overwrite=True)
if result != {"FINISHED"}:
    raise AssertionError(f"add-on install failed: {result}")
addon_search_path = Path(bpy.utils.script_path_user()).resolve() / "addons"
sys.path.insert(0, str(addon_search_path))
importlib.invalidate_caches()
result = bpy.ops.preferences.addon_enable(module="master_rallye_io")
if result != {"FINISHED"}:
    raise AssertionError(f"add-on enable failed: {result}")
import master_rallye_io
installed_module = Path(master_rallye_io.__file__).resolve()
expected_module = (addon_search_path / "master_rallye_io" / "__init__.py").resolve()
if installed_module != expected_module:
    raise AssertionError(
        f"enabled add-on came from {installed_module}, expected isolated ZIP install {expected_module}"
    )
if not hasattr(bpy.ops.import_scene, "master_rallye_dx"):
    raise AssertionError("single DX operator missing after ZIP install")
if not hasattr(bpy.ops.import_scene, "master_rallye_vehicle"):
    raise AssertionError("vehicle folder operator missing after ZIP install")
if not hasattr(bpy.ops.import_scene, "master_rallye_course_xml_markers"):
    raise AssertionError("RaceTest XML marker operator missing after ZIP install")
if not hasattr(bpy.ops.import_scene, "master_rallye_course_gxm_startpoint"):
    raise AssertionError("GXM startpoint point-candidate operator missing after ZIP install")
if not hasattr(bpy.ops.export_scene, "master_rallye_dx_attributes"):
    raise AssertionError("R4E attribute DX operator missing after ZIP install")
if not hasattr(bpy.ops.export_scene, "master_rallye_dx_positions"):
    raise AssertionError("positions-only DX operator missing after ZIP install")

payload = {
    "blender_version": bpy.app.version_string,
    "archive": archive.name,
    "installed_module": str(installed_module),
    "install": "PASS",
    "vendored_import": "NOT_RUN",
    "vendored_course_import": "NOT_RUN",
    "course_material_scope": "NOT_RUN",
    "panel_draw": "NOT_RUN",
}
if fixture is not None:
    result = bpy.ops.import_scene.master_rallye_dx(
        filepath=str(fixture),
        import_sidecar=True,
        load_textures=True,
        strict_validation=True,
    )
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged synthetic import failed: {result}")
    objects = [obj for obj in bpy.data.objects if "mr_metadata_json" in obj]
    if len(objects) != 1:
        raise AssertionError("packaged add-on created wrong object count")
    obj = objects[0]
    metadata = json.loads(obj["mr_metadata_json"])
    if metadata.get("vehicle_material_semantics_version") != "R_MAT1_V3":
        raise AssertionError("vendored vehicle semantics model missing")
    if any(material.get("mr_preview_semantics") != "R_MAT1_RUNTIME_STAGES_V3"
           for material in obj.data.materials):
        raise AssertionError("vendored vehicle preview is stale")
    if len(obj.data.vertices) != 4 or len(obj.data.polygons) != 2:
        raise AssertionError("vendored parser geometry mismatch")
    if [draw["record_tag"] for draw in metadata["draws"]] != [7, 8]:
        raise AssertionError("vendored parser group tags mismatch")
    if metadata["texture_presentation"]["blender_uv_policy"] != "direct-v":
        raise AssertionError("vendored Blender UV policy mismatch")
    if metadata["normal_provenance"]["display_strategy"] != "blender-calculated-fallback":
        raise AssertionError("vendored normal strategy mismatch")
    if not metadata["collision"]["tag101_present"]:
        raise AssertionError("vendored collision parser metadata missing")
    from master_rallye_io.library import MaterialSemantics
    if MaterialSemantics.__module__ != "master_rallye_io.vendor.master_rallye.material_semantics":
        raise AssertionError("R-MAT1 semantics were not loaded from the installed add-on's vendored library")
    overlays = [item for item in bpy.data.objects if item.get("mr_collision_owner") == obj["mr_source_path"]]
    if len(overlays) != 3:
        raise AssertionError("vendored collision overlay mismatch")
    payload["vendored_import"] = "PASS"
    payload["material_semantics_import"] = MaterialSemantics.__module__
    payload["blender_uv_policy"] = "direct-v"
    payload["display_normal_strategy"] = "blender-calculated-fallback"
    payload["collision_overlay"] = "PASS"
    zero_output = smoke_output / "packaged-zero-edit.dx"
    result = bpy.ops.export_scene.master_rallye_dx_positions(
        filepath=str(zero_output),
    )
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged zero-edit export failed: {result}")
    if zero_output.read_bytes() != fixture.read_bytes():
        raise AssertionError("packaged zero-edit export was not byte-identical")
    payload["positions_only_export"] = "PASS"

if course_pair is not None:
    course_dx, xml_path = course_pair
    from master_rallye_io.library import load_course_project
    course_project = load_course_project(course_dx)
    if course_project.render is None:
        raise AssertionError(f"installed CourseProject omitted render data: {course_project.diagnostics}")
    course_model = course_project.render._parsed_model
    payload["course_project_validation"] = {
        "passed": course_project.render.validation_passed,
        "diagnostics": list(course_project.diagnostics),
        "render_errors": list(course_model.diagnostics.errors),
    }
    if not course_project.render.validation_passed:
        raise AssertionError(f"installed CourseProject validation failed: {payload['course_project_validation']}")
    result = bpy.ops.import_scene.master_rallye_course(
        filepath=str(course_dx), load_textures=False
    )
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged course DX import failed: {result}")
    course_objects = [
        obj for obj in bpy.data.objects
        if obj.get("mr_source_path") == str(course_dx.resolve()) and obj.get("mr_resource_kind") == "course"
    ]
    if not course_objects:
        raise AssertionError("packaged course DX import did not create a course-scoped render object")
    if any(material.get("mr_preview_semantics") == "R_MAT1_RUNTIME_STAGES_V3"
           for obj in course_objects for material in obj.data.materials):
        raise AssertionError("vehicle R-MAT1 semantics were applied to course materials")
    course_metadata = json.loads(course_objects[0]["mr_metadata_json"])
    if "vehicle_material_semantics_version" in course_metadata:
        raise AssertionError("course DX metadata must not claim vehicle R-MAT1 semantics")
    payload["course_material_scope"] = "UNSCOPED_COURSE_PREVIEW"
    from master_rallye_io.library import parse_course_xml
    document = parse_course_xml(xml_path)
    expected = sum(marker.position is not None for marker in document.markers)
    result = bpy.ops.import_scene.master_rallye_course_xml_markers(filepath=str(xml_path))
    if result != {"FINISHED"}:
        raise AssertionError(f"packaged XML marker import failed: {result}")
    overlays = [
        collection for collection in bpy.data.collections
        if collection.get("mr_xml_source") == str(xml_path)
        and collection.get("mr_xml_collection_kind") == "race_logic_root"
    ]
    if len(overlays) != 1:
        raise AssertionError("packaged XML race-logic hierarchy was not created exactly once")
    descendants = []
    def walk(collection):
        descendants.append(collection)
        for child in collection.children:
            walk(child)
    walk(overlays[0])
    marker_count = sum(
        1 for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
    )
    split_count = sum(
        1 for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "split_center"
    )
    if marker_count != expected or split_count != len(document.split_time_eggs):
        raise AssertionError(
            f"packaged XML marker/helper count mismatch: markers {marker_count}/{expected}, "
            f"split centers {split_count}/{len(document.split_time_eggs)}"
        )
    companions = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "split_visual_companion"
    ]
    billboards = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "diagnostic_marker_billboard"
    ]
    rays = [
        obj for collection in descendants for obj in collection.objects
        if obj.get("mr_course_helper_kind") == "diagnostic_direction_ray"
    ]
    if len(companions) != 12 or len(billboards) != 12 or len(rays) != 12:
        raise AssertionError("packaged course diagnostics lost a SplitTime companion, billboard, or ray")
    if any(obj.get("mr_direction_basis") != "this companion en3d Matrix local -Z (-Row2); route/travel diagnostic"
           for obj in rays):
        raise AssertionError("packaged SplitTime route rays are stale or use the source-facing direction")
    split_center = next((obj for obj in bpy.data.objects if obj.get("mr_course_helper_kind") == "split_center"), None)
    course_object = next((obj for obj in course_objects if obj.type == "MESH"), None)
    if split_center is None or course_object is None:
        raise AssertionError("course panel draw context is missing")
    valid_icons = {
        item.identifier
        for item in bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
    }
    from master_rallye_io import ui as addon_ui
    course_draw_calls = _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course, course_object, valid_icons)
    race_draw_calls = _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course_race_logic, split_center, valid_icons)
    payload["panel_draw"] = {"course": course_draw_calls, "race_logic": race_draw_calls}

    no_op_xml = smoke_output / "packaged-race-logic-noop.xml"
    result = bpy.ops.export_scene.master_rallye_race_logic_xml(filepath=str(no_op_xml))
    if result != {"FINISHED"} or no_op_xml.read_bytes() != xml_path.read_bytes():
        raise AssertionError("installed package Race Logic no-op export was not byte-identical")
    edit_manifest = json.loads(Path(str(no_op_xml) + ".mr-race-edit.json").read_text(encoding="utf-8"))
    if edit_manifest["changes"] or not edit_manifest["unknown_content_preserved"]:
        raise AssertionError("installed package export manifest includes unexpected edits")
    payload["packaged_race_logic_noop_export"] = "BYTE_IDENTICAL"
    payload["panel_draw_after_export"] = {
        "course": _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course, course_object, valid_icons),
        "race_logic": _draw_panel(addon_ui.VIEW3D_PT_master_rallye_course_race_logic, split_center, valid_icons),
    }
    payload["vendored_course_import"] = "PASS"
    payload["course_xml_overlay"] = "PASS"
    payload["course_xml_marker_count"] = marker_count
    payload["course_xml_split_visual_count"] = split_count
    if gxm_source is not None:
        result = bpy.ops.import_scene.master_rallye_course_gxm_startpoint(filepath=str(gxm_source))
        if result != {"FINISHED"}:
            raise AssertionError(f"packaged GXM topology import failed: {result}")
        gxm_meshes = [
            obj for obj in bpy.data.objects
            if obj.get("mr_gxm_source") == str(gxm_source)
        ]
        if len(gxm_meshes) != 1:
            raise AssertionError("packaged GXM decoded source mesh mismatch")
        gxm_mesh = gxm_meshes[0]
        if (gxm_mesh.type != "MESH" or len(gxm_mesh.data.vertices) != 8
                or len(gxm_mesh.data.polygons) != 12 or len(gxm_mesh.data.edges) != 18):
            raise AssertionError("packaged GXM startpoint geometry counts mismatch")
        if gxm_mesh.get("mr_source_node_name") != "startpoint":
            raise AssertionError("packaged GXM mesh did not preserve literal source node identity")
        payload["vendored_gxm_startpoint_mesh"] = "PASS"
        payload["gxm_startpoint_vertices"] = len(gxm_mesh.data.vertices)
        payload["gxm_startpoint_triangles"] = len(gxm_mesh.data.polygons)

print("R3_ADDON_INSTALL_PASS", json.dumps(payload, sort_keys=True))
