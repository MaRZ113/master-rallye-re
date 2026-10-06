"""Headless Blender smoke for read-only G1 RaceLine/limit/camera diagnostics."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import bpy
from mathutils import Vector


TARGET_LISTS = (
    "RaceLine", "LeftInnerLimit", "LeftOuterLimit", "RightInnerLimit",
    "RightOuterLimit", "Cameras",
)


def _descendants(collection):
    yield collection
    for child in collection.children:
        yield from _descendants(child)


class _LayoutProbe:
    def __init__(self, valid_icons):
        self.valid_icons = valid_icons
        self.draws = 0

    def box(self):
        self.draws += 1
        return self

    def grid_flow(self, **_kwargs):
        self.draws += 1
        return self

    def label(self, *, text="", icon=None, **_kwargs):
        self.draws += 1
        self._icon(icon)

    def operator(self, _operator, *, text="", icon=None, **_kwargs):
        self.draws += 1
        self._icon(icon)
        return SimpleNamespace()

    def prop(self, *_args, **_kwargs):
        self.draws += 1

    def _icon(self, icon):
        if icon and icon not in self.valid_icons:
            raise AssertionError(f"unsupported Blender icon {icon!r}")


def _draw(panel, obj, valid_icons):
    context = SimpleNamespace(object=obj)
    if not panel.poll(context):
        raise AssertionError(f"{panel.__name__}.poll rejected the intended context")
    layout = _LayoutProbe(valid_icons)
    panel.draw(SimpleNamespace(layout=layout), context)
    if not layout.draws:
        raise AssertionError(f"{panel.__name__}.draw produced no UI")
    return layout.draws


def _close(a, b, epsilon=2.0e-4):
    return all(abs(float(a[i]) - float(b[i])) <= epsilon for i in range(3))


def _direction(value):
    vector = Vector(value)
    if vector.length_squared <= 1.0e-12:
        return None
    return vector.normalized()


def _main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) not in {3, 4}:
        raise SystemExit("expected course.dx RaceTest.xml output.json [addon.zip] after --")
    dx_path, xml_path, output_path = (Path(value).resolve() for value in args[:3])
    archive = Path(args[3]).resolve() if len(args) == 4 else None
    repository = Path(__file__).resolve().parents[2]
    if archive:
        sys.path.insert(0, str(archive))
        addon_source = archive.name
    else:
        for path in (repository / "src", repository / "blender"):
            sys.path.insert(0, str(path))
        addon_source = "workspace source"

    import master_rallye_io
    from master_rallye_io import ui as addon_ui
    from master_rallye_io.library import load_course_project, position_to_blender

    master_rallye_io.register()
    course_status = bpy.ops.import_scene.master_rallye_course(
        "EXEC_DEFAULT", filepath=str(dx_path), load_textures=False
    )
    if course_status != {"FINISHED"}:
        raise AssertionError(f"course DX import failed: {course_status}")
    project = load_course_project(xml_path)
    document = project.race_logic.source_document

    xml_status = bpy.ops.import_scene.master_rallye_course_xml_markers(
        "EXEC_DEFAULT", filepath=str(xml_path), show_marker_direction_rays=False
    )
    if xml_status != {"FINISHED"}:
        raise AssertionError(f"RaceTest XML import failed: {xml_status}")
    logic_roots = [
        collection for collection in bpy.data.collections
        if collection.get("mr_xml_collection_kind") == "race_logic_root"
        and collection.get("mr_xml_source") == str(xml_path)
    ]
    if len(logic_roots) != 1:
        raise AssertionError(f"expected one imported logic hierarchy, found {len(logic_roots)}")
    logic_root = logic_roots[0]
    descendants = tuple(_descendants(logic_root))
    all_objects = tuple(logic_root.all_objects)

    marker_results = {}
    for list_name in TARGET_LISTS:
        source_lists = [item for item in document.marker_lists if item.name == list_name]
        source_markers = [marker for marker_list in source_lists for marker in marker_list.markers]
        helpers = [
            obj for obj in all_objects
            if obj.get("mr_course_helper_kind") == "RaceTest XML Marker"
            and obj.get("mr_marker_list_name") == list_name
        ]
        if len(helpers) != len(source_markers):
            raise AssertionError(f"{list_name} helper count {len(helpers)} != source count {len(source_markers)}")
        by_index = {int(obj["mr_marker_index_in_list"]): obj for obj in helpers}
        if len(by_index) != len(helpers) or sorted(by_index) != list(range(len(source_markers))):
            raise AssertionError(f"{list_name} source marker order/identity was not retained")
        if any(not obj.get("mr_read_only") or not obj.get("mr_editor_only") for obj in helpers):
            raise AssertionError(f"{list_name} helpers are not explicitly read-only/editor-only")
        if any(obj.get("mr_race_logic_editable") or obj.get("mr_race_logic_object_type") for obj in helpers):
            raise AssertionError(f"{list_name} leaked into the stable G0 authoring allowlist")

        source_list = source_lists[0] if source_lists else None
        polyline = [
            obj for obj in all_objects
            if obj.get("mr_course_helper_kind") == "RaceTest MarkerList source-order diagnostic polyline"
            and obj.get("mr_marker_list_name") == list_name
        ]
        expected_polyline = list_name != "Cameras" and source_list is not None and len(source_list.markers) >= 2
        if bool(polyline) != bool(expected_polyline) or len(polyline) > 1:
            raise AssertionError(f"{list_name} polyline policy did not match source family")
        if polyline:
            curve = polyline[0].data
            if len(curve.splines) != 1 or curve.splines[0].type != "POLY":
                raise AssertionError(f"{list_name} did not use a literal source-order POLY spline")
            expected = [position_to_blender(marker.position) for marker in source_list.markers]
            actual = [tuple(point.co[:3]) for point in curve.splines[0].points]
            if len(actual) != len(expected) or any(not _close(a, b) for a, b in zip(actual, expected)):
                raise AssertionError(f"{list_name} polyline reordered or changed source positions")
            if not polyline[0].get("mr_source_order_preserved") or not polyline[0].get("mr_editor_only"):
                raise AssertionError(f"{list_name} curve metadata does not mark it as an editor-only source-order view")

        bpy.context.view_layer.update()
        checked = 0
        for marker in source_markers:
            if marker.position is None or marker.direction is None:
                continue
            helper = by_index[marker.index_in_list]
            target = _direction(position_to_blender(marker.direction))
            if target is None:
                continue
            actual = (helper.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
            if (actual - target).length > 1.0e-3:
                raise AssertionError(f"{list_name}[{marker.index_in_list}] orientation preview ignores its Marker Dir")
            checked += 1
        marker_results[list_name] = {
            "count": len(helpers),
            "position_and_direction_helpers": checked,
            "source_order_polyline": bool(polyline),
            "read_only": True,
        }

    marker_rays = [
        obj for obj in all_objects
        if obj.get("mr_course_helper_kind") == "diagnostic_direction_ray"
        and obj.get("mr_direction_basis") == "parent marker's own Marker Dir; visual direction only"
    ]
    if marker_rays:
        raise AssertionError("Marker Dir rays must be optional and disabled by default")
    camera_polylines = [obj for obj in all_objects if obj.get("mr_marker_list_name") == "Cameras"
                        and obj.get("mr_course_helper_kind") == "RaceTest MarkerList source-order diagnostic polyline"]
    if camera_polylines:
        raise AssertionError("Cameras markers must not be presented as an invented ordered path")

    # The ordinary Race Logic exporter must ignore all read-only G1 helpers.
    area_helper = next(
        obj for obj in all_objects
        if obj.get("mr_race_logic_object_type") == "area_marker"
        and obj.get("mr_race_logic_area") == "StartArea"
    )
    bpy.context.view_layer.objects.active = area_helper
    with tempfile.TemporaryDirectory(prefix="mr_g1_blender_smoke_") as temp_name:
        temp = Path(temp_name)
        noop = temp / "France1_g1_noop.xml"
        export_status = bpy.ops.export_scene.master_rallye_race_logic_xml(
            "EXEC_DEFAULT", filepath=str(noop)
        )
        if export_status != {"FINISHED"} or noop.read_bytes() != xml_path.read_bytes():
            raise AssertionError("G1 helper import changed stable no-op RaceTest export identity")
        manifest = json.loads(Path(str(noop) + ".mr-race-edit.json").read_text(encoding="utf-8"))
        if manifest.get("changes") or not manifest.get("unknown_content_preserved"):
            raise AssertionError("G1 diagnostics polluted the bounded G0 export manifest")

        rays_xml = temp / "France1_marker_rays.xml"
        shutil.copyfile(xml_path, rays_xml)
        rays_status = bpy.ops.import_scene.master_rallye_course_xml_markers(
            "EXEC_DEFAULT", filepath=str(rays_xml), show_marker_direction_rays=True
        )
        if rays_status != {"FINISHED"}:
            raise AssertionError(f"opt-in Marker Dir visualization import failed: {rays_status}")
        rays_roots = [
            collection for collection in bpy.data.collections
            if collection.get("mr_xml_collection_kind") == "race_logic_root"
            and collection.get("mr_xml_source") == str(rays_xml)
        ]
        if len(rays_roots) != 1:
            raise AssertionError("opt-in direction import did not create its own source hierarchy")
        ray_objects = [
            obj for obj in rays_roots[0].all_objects
            if obj.get("mr_course_helper_kind") == "diagnostic_direction_ray"
            and obj.get("mr_direction_basis") == "parent marker's own Marker Dir; visual direction only"
        ]
        expected_rays = sum(
            marker.direction is not None
            for marker_list in document.marker_lists
            if marker_list.name in TARGET_LISTS
            for marker in marker_list.markers
        )
        if len(ray_objects) != expected_rays:
            raise AssertionError(f"opt-in direction ray count {len(ray_objects)} != expected {expected_rays}")
        bpy.context.view_layer.update()
        for ray in ray_objects:
            parent = ray.parent
            expected = _direction(position_to_blender(parent["mr_source_direction_xyz"]))
            actual = (ray.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
            if expected is None or (actual - expected).length > 1.0e-3:
                raise AssertionError(f"{ray.name} does not follow its own Marker Dir")

    valid_icons = {
        item.identifier
        for item in bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
    }
    course_obj = next(
        obj for obj in bpy.data.objects
        if obj.get("mr_resource_kind") == "course" and "mr_metadata_json" in obj
    )
    panel_course_draws = _draw(addon_ui.VIEW3D_PT_master_rallye_course, course_obj, valid_icons)
    panel_logic_draws = _draw(addon_ui.VIEW3D_PT_master_rallye_course_race_logic, area_helper, valid_icons)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "addon_source": addon_source,
        "course": "France1",
        "marker_lists": marker_results,
        "optional_marker_rays": len(ray_objects),
        "cameras_rendered_as_polyline": False,
        "read_only_helpers_outside_g0_allowlist": True,
        "noop_export_byte_identical": True,
        "manifest_changes": 0,
        "panel_draw_callbacks": {
            "master_rallye_course": panel_course_draws,
            "course_race_logic": panel_logic_draws,
            "icons_checked_against_blender_rna": True,
        },
        "runtime_test_claimed": False,
    }
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
