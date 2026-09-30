"""Build a local diagnostic Blender scene for France1 source/XML correlation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def _collection(parent, name):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def _material(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = 0.75
    return material


def _area_helpers(area, collection, material, runtime_to_blender):
    points = [marker.position for marker in area.markers]
    if len(points) < 2 or any(point is None for point in points):
        raise AssertionError(f"{area.name} marker data incomplete")
    for marker in area.markers:
        empty = bpy.data.objects.new(f"{area.name} Marker {marker.index_in_list:02d}", None)
        empty.empty_display_type = "SPHERE"
        empty.empty_display_size = 1.5
        empty.location = runtime_to_blender(marker.position)
        empty["mr_racetest_list"] = area.name
        empty["mr_marker_index"] = marker.index_in_list
        empty["mr_source_xml_path"] = marker.record.xml_path
        collection.objects.link(empty)

    curve = bpy.data.curves.new(f"{area.name} marker-order outline", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.10
    curve.bevel_resolution = 1
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for index, point in enumerate(points):
        x, y, z = runtime_to_blender(point)
        spline.points[index].co = (x, y, z, 1.0)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(f"{area.name} marker-order outline", curve)
    obj.data.materials.append(material)
    obj["mr_racetest_list"] = area.name
    obj["mr_coordinate_space"] = "RaceTest runtime/XML converted to Blender (x,-z,y)"
    collection.objects.link(obj)
    return len(points), obj


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 5:
        raise SystemExit("expected GXM TXT France1.xml output.blend report.json after --")
    gxm_path, txt_path, xml_path, blend_path, report_path = (Path(item).resolve() for item in args)
    repository = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repository / "src"))

    from master_rallye.course_gxm import parse_course_gxm_model_v7
    from master_rallye.course_source import parse_course_txt
    from master_rallye.course_spatial import analyze_source_mesh, runtime_to_blender
    from master_rallye.course_xml import parse_course_xml

    model = parse_course_gxm_model_v7(gxm_path, parse_course_txt(txt_path))
    xml = parse_course_xml(xml_path)
    areas = {name: xml.marker_list(name) for name in ("StartArea", "FinishArea")}
    if any(area is None for area in areas.values()):
        raise AssertionError("France1 RaceTest XML must contain StartArea and FinishArea")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in tuple(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)

    root = _collection(bpy.context.scene.collection, "R5T-F.0 France1 Spatial Diagnostic")
    race_logic = _collection(root, "Race Logic")
    start_collection = _collection(race_logic, "StartArea")
    finish_collection = _collection(race_logic, "FinishArea")
    named_collection = _collection(root, "Named Source Geometry - Semantics Unknown")
    node_by_ordinal = {item.ordinal: item for item in model.object_table.nodes}
    start_material = _material("Diagnostic StartArea", (0.10, 0.72, 0.24))
    finish_material = _material("Diagnostic FinishArea", (0.95, 0.72, 0.10))
    source_material = _material("Diagnostic Named Source Mesh", (0.10, 0.45, 0.92))

    area_counts = {}
    for name, area in areas.items():
        collection = start_collection if name == "StartArea" else finish_collection
        material = start_material if name == "StartArea" else finish_material
        count, _curve = _area_helpers(area, collection, material, runtime_to_blender)
        area_counts[name] = count

    source_meshes = {}
    expected_spans = {
        "COLLIDE_finishline01": (47011, 24),
        "COLLIDE_finishline": (47035, 24),
        "COLLIDE_finishline02": (47059, 24),
        "COLLIDE_finishline03": (47083, 24),
    }
    for name, expected_span in expected_spans.items():
        node = model.find_mesh(name)
        if (node.mesh_index, node.mesh_size) != expected_span:
            raise AssertionError(f"unexpected {name} moMesh span")
        metrics = analyze_source_mesh(model, node)
        position_remap = {source_index: local_index for local_index, source_index in enumerate(metrics.unique_position_indices)}
        faces = []
        for triangle_index in model.mesh_triangle_indices(node):
            faces.append(tuple(position_remap[index] for index in model.triangle(triangle_index).position_indices))
        mesh_data = bpy.data.meshes.new(name)
        mesh_data.from_pydata(metrics.source_positions, [], faces)
        mesh_data.update()
        mesh_data.materials.append(source_material)
        obj = bpy.data.objects.new(name, mesh_data)
        obj.show_wire = True
        obj.show_all_edges = True
        obj["literal_source_name"] = name
        path_parts = [node.name]
        parent_id = node.parent_id
        seen = {node.ordinal}
        while parent_id is not None and parent_id in node_by_ordinal and parent_id not in seen:
            parent = node_by_ordinal[parent_id]
            path_parts.append(parent.name)
            seen.add(parent.ordinal)
            parent_id = parent.parent_id
        obj["source_hierarchy_path"] = "/".join(reversed(path_parts))
        obj["source_index"] = node.mesh_index
        obj["source_size"] = node.mesh_size
        obj["gameplay_semantics"] = "UNKNOWN"
        obj["source_name_only"] = True
        obj["coordinate_note"] = "GXM source to Blender identity is a high-confidence spatial inference"
        obj["runtime_centroid"] = list(metrics.runtime_centroid)
        named_collection.objects.link(obj)
        source_meshes[name] = {
            "triangles": len(mesh_data.polygons),
            "vertices": len(mesh_data.vertices),
            "gameplay_semantics": "UNKNOWN",
        }

    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report = {
        "blender_version": bpy.app.version_string,
        "status": "PASS",
        "scene": str(blend_path),
        "gxm": str(gxm_path),
        "xml": str(xml_path),
        "coordinate_spaces": {
            "source_meshes": "GXM source coordinates; approximately identity into Blender",
            "race_logic": "RaceTest runtime/XML transformed to Blender (x,-z,y)",
        },
        "area_marker_counts": area_counts,
        "source_meshes": source_meshes,
        "semantic_labels": "UNKNOWN; literal source identity only",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
