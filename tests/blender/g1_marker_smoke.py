"""Headless Blender smoke for bounded G1 Marker Pos authoring and diagnostics."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
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
    from master_rallye_io.course_route import refresh_marker_list_polyline
    from master_rallye_io.library import load_course_project, position_to_blender, blender_position_to_source

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
        authorable = list_name in TARGET_LISTS[:-1]
        if any(bool(obj.get("mr_read_only")) != (not authorable) for obj in helpers):
            raise AssertionError(f"{list_name} helper read-only state does not match its bounded authoring status")
        if any(bool(obj.get("mr_editor_only")) for obj in helpers):
            raise AssertionError(f"{list_name} source marker helpers must remain semantic points, not editor-only geometry")
        if authorable:
            expected_type = "route_marker" if list_name == "RaceLine" else "limit_marker"
            if any(not obj.get("mr_race_logic_editable")
                   or not obj.get("mr_marker_position_editable")
                   or obj.get("mr_race_logic_object_type") != expected_type
                   for obj in helpers):
                raise AssertionError(f"{list_name} did not expose only bounded Marker Pos authoring")
        elif any(obj.get("mr_race_logic_editable") or obj.get("mr_marker_position_editable")
                 or obj.get("mr_race_logic_object_type") != "camera_marker" for obj in helpers):
            raise AssertionError("Cameras marker diagnostics leaked into the authoring allowlist")

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
            "position_authoring": authorable,
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

    # The no-op exporter preserves bytes; a deliberate marker move changes only one Marker Pos.
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
        if manifest.get("changes") or manifest.get("warnings") or not manifest.get("unknown_content_preserved"):
            raise AssertionError("G1 marker import polluted the no-op export manifest")

        route_marker = next(
            obj for obj in all_objects
            if obj.get("mr_race_logic_object_type") == "route_marker"
            and obj.get("mr_marker_index_in_list") == 265
        )
        route_polyline = next(
            obj for obj in all_objects
            if obj.get("mr_course_helper_kind") == "RaceTest MarkerList source-order diagnostic polyline"
            and obj.get("mr_marker_list_name") == "RaceLine"
        )
        route_marker.location.x += 0.25
        bpy.context.view_layer.update()
        if not refresh_marker_list_polyline(str(xml_path), route_marker["mr_source_list_ordinal"], "RaceLine"):
            raise AssertionError("moving a RaceLine point did not update its source-order polyline")
        curve_point = route_polyline.matrix_world @ Vector(route_polyline.data.splines[0].points[265].co[:3])
        if (curve_point - route_marker.matrix_world.translation).length > 2.0e-4:
            raise AssertionError("RaceLine polyline did not follow the moved source marker")
        outer_marker = next(
            obj for obj in all_objects
            if obj.get("mr_race_logic_object_type") == "limit_marker"
            and obj.get("mr_source_list_name") == "LeftOuterLimit"
            and obj.get("mr_marker_index_in_list") == 58
        )
        outer_marker.location.x += 0.5
        edited_xml = temp / "France1_g1_marker_positions.xml"
        edited_status = bpy.ops.export_scene.master_rallye_race_logic_xml(
            "EXEC_DEFAULT", filepath=str(edited_xml)
        )
        if edited_status != {"FINISHED"}:
            raise AssertionError(f"bounded RaceLine/Limit export failed: {edited_status}")
        edited_manifest = json.loads(
            Path(str(edited_xml) + ".mr-race-edit.json").read_text(encoding="utf-8")
        )
        changes = edited_manifest.get("changes", [])
        if len(changes) != 2 or {item.get("semantic_role") for item in changes} != {
            "race.route.raceline.marker_position", "race.limit.left_outer.marker_position"
        }:
            raise AssertionError(f"unexpected G1.1 manifest semantic paths: {changes!r}")
        edited_root = ET.parse(edited_xml).getroot()
        for list_name, marker_index, helper in (
            ("RaceLine", 265, route_marker),
            ("LeftOuterLimit", 58, outer_marker),
        ):
            old = next(item for item in document.marker_lists if item.name == list_name).markers[marker_index]
            values = edited_root.findall(f"./MarkerLists/List[@Name='{list_name}']/Marker")
            new_marker = values[marker_index]
            new_pos = new_marker.find("Value[@Name='Marker Pos']").get("Value").split()
            expected_source = blender_position_to_source(helper.matrix_world.translation)
            if any(abs(float(value) - expected_source[axis]) > 2.0e-4 for axis, value in enumerate(new_pos)):
                raise AssertionError(f"{list_name}[{marker_index}] did not export final world position")
            new_dir = new_marker.find("Value[@Name='Marker Dir']").get("Value")
            if new_dir != old.raw_direction:
                raise AssertionError(f"{list_name}[{marker_index}] Marker Dir changed unexpectedly")

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
    panel_logic_draws = _draw(addon_ui.VIEW3D_PT_master_rallye_course_race_logic, route_marker, valid_icons)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "addon_source": addon_source,
        "course": "France1",
        "marker_lists": marker_results,
        "optional_marker_rays": len(ray_objects),
        "cameras_rendered_as_polyline": False,
        "bounded_route_limit_marker_pos_export": True,
        "marker_dir_and_topology_unchanged": True,
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
