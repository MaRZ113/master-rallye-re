"""Headless smoke import for two retail course DX resources.

Run with Blender, passing Italy1 DX, France1 DX, then a JSON output path after
the ``--`` separator. The output contains derived validation metadata only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 3:
        raise SystemExit("expected italy1.dx france1.dx output.json after --")
    italy, france, output = (Path(value).resolve() for value in args)
    repository = Path(__file__).resolve().parents[2]
    for path in (repository / "src", repository / "blender"):
        sys.path.insert(0, str(path))

    import master_rallye_io
    from master_rallye_io.library import parse_course_dx

    master_rallye_io.register()
    results = []
    for source in (italy, france):
        model = parse_course_dx(source)
        if not model.course_render_validated:
            raise AssertionError(f"course DX failed render validation: {source}")
        before = {obj.as_pointer() for obj in bpy.data.objects}
        status = bpy.ops.import_scene.master_rallye_course(
            "EXEC_DEFAULT", filepath=str(source), load_textures=True
        )
        if status != {"FINISHED"}:
            raise AssertionError(f"Blender course import failed for {source}: {status}")
        imported = [obj for obj in bpy.data.objects if obj.as_pointer() not in before]
        meshes = [obj for obj in imported if obj.type == "MESH"]
        if len(meshes) != 1:
            raise AssertionError(f"expected one render mesh for {source}, found {len(meshes)}")
        obj = meshes[0]
        metadata = json.loads(obj["mr_metadata_json"])
        if obj.get("mr_resource_kind") != "course":
            raise AssertionError("import did not retain the course resource identity")
        if metadata.get("round_trip", {}).get("writer_available") is not False:
            raise AssertionError("course metadata unexpectedly enables writing")
        if len(obj.data.vertices) != model.vertex_count:
            raise AssertionError("Blender vertex count differs from parsed course DX")
        expected_faces = sum(draw.triangle_count for draw in model.physical_draws)
        if len(obj.data.polygons) != expected_faces:
            raise AssertionError("Blender triangle count differs from parsed course draws")
        for attribute in ("mr_draw_id", "mr_source_triangle", "mr_group_id"):
            if obj.data.attributes.get(attribute) is None:
                raise AssertionError(f"missing source identity attribute {attribute}")
        root = bpy.data.collections.get(f"Master Rallye Course - {source.parent.name}")
        if root is None:
            raise AssertionError("course root collection is missing")
        render_collections = [
            collection
            for collection in root.children
            if collection.name == "Render Geometry"
            or collection.name.startswith("Render Geometry.")
        ]
        if not any(obj.name in collection.objects for collection in render_collections):
            raise AssertionError("course mesh is not under its root's Render Geometry collection")
        if bpy.ops.export_scene.master_rallye_dx_positions.poll():
            raise AssertionError("vehicle positions exporter is enabled for course geometry")
        if bpy.ops.export_scene.master_rallye_dx_attributes.poll():
            raise AssertionError("vehicle attribute exporter is enabled for course geometry")
        if bpy.ops.export_scene.master_rallye_dx_topology.poll():
            raise AssertionError("vehicle topology exporter is enabled for course geometry")
        dxt_materials = [
            material for material in obj.data.materials
            if material and material.get("mr_dxt_source")
        ]
        results.append({
            "course": source.parent.name,
            "source_path": source.as_posix(),
            "revision": model.word_0x04,
            "vertices": len(obj.data.vertices),
            "triangles": len(obj.data.polygons),
            "draws": len(model.physical_draws),
            "uv_sets": len(obj.data.uv_layers),
            "material_slots": len(obj.data.materials),
            "materials_with_loaded_dxt": len(dxt_materials),
            "warnings": metadata.get("blender", {}).get("import_warnings", []),
            "unsupported_sections": {
                "route_decoded": metadata["course"]["opaque_course_data"]["route_data_decoded"],
                "surface_decoded": metadata["course"]["opaque_course_data"]["surface_data_decoded"],
                "trailing_tag_ids": metadata["course"]["opaque_course_data"]["trailing_tag_ids"],
                "tag100_semantics": metadata["course"]["opaque_course_data"]["tag100"]["semantics"],
            },
            "metadata_writer_available": metadata["round_trip"]["writer_available"],
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "blender_version": bpy.app.version_string,
        "status": "PASS",
        "courses": results,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output), "courses": results}, indent=2))


if __name__ == "__main__":
    main()
