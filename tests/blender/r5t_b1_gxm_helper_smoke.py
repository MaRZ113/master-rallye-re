"""Headless smoke import for decoded read-only GXM startpoint topology."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 2:
        raise SystemExit("expected France1.gxm output.json after --")
    source, output = (Path(value).resolve() for value in args)
    repository = Path(__file__).resolve().parents[2]
    for path in (repository / "src", repository / "blender"):
        sys.path.insert(0, str(path))

    import master_rallye_io
    from master_rallye_io.library import parse_course_gxm_model_v7, parse_course_txt

    model = parse_course_gxm_model_v7(source, parse_course_txt(source.with_suffix(".txt")))
    node = model.find_mesh("startpoint")
    position_indices = tuple(sorted(set(model.mesh_position_indices(node))))
    master_rallye_io.register()
    status = bpy.ops.import_scene.master_rallye_course_gxm_startpoint("EXEC_DEFAULT", filepath=str(source))
    if status != {"FINISHED"}:
        raise AssertionError(f"GXM topology import failed: {status}")

    obj = next(item for item in bpy.data.objects if item.get("mr_gxm_source") == str(source))
    if obj.type != "MESH":
        raise AssertionError("decoded source topology was not imported as a mesh")
    if len(obj.data.vertices) != 8 or len(obj.data.polygons) != 12 or len(obj.data.edges) != 18:
        raise AssertionError("decoded startpoint mesh counts mismatch")
    if tuple(obj["mr_source_position_indices"]) != position_indices:
        raise AssertionError("source position indices were not preserved")
    if tuple(obj["mr_source_triangle_indices"]) != tuple(range(12)):
        raise AssertionError("source triangle identities were not preserved")
    if obj.get("mr_source_node_name") != "startpoint":
        raise AssertionError("literal source node name was not preserved")
    if obj.get("mr_geometry_status") != "version-7 triangle records resolved to source positions; gameplay role UNKNOWN":
        raise AssertionError("decoded topology or semantic uncertainty was not recorded")
    if tuple(obj.data.vertices[0].co) != model.position(position_indices[0]):
        raise AssertionError("source-to-Blender coordinate mapping changed")

    root = bpy.data.collections.get(f"Master Rallye Course - {source.stem}")
    helpers = next((child for child in root.children if child.name.startswith("Course Helpers")), None) if root else None
    if helpers is None or obj.name not in helpers.objects:
        raise AssertionError("source mesh is not organized under Course Helpers")

    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "blender_version": bpy.app.version_string,
        "status": "PASS",
        "course": source.stem,
        "source_mesh": obj.name,
        "position_count": len(obj.data.vertices),
        "triangle_count": len(obj.data.polygons),
        "edge_count": len(obj.data.edges),
        "node_index": obj["mr_source_node_index"],
        "mesh_span": [obj["mr_source_mesh_index"], obj["mr_source_mesh_size"]],
        "gameplay_role": "UNKNOWN",
        "coordinate_claim": obj["mr_source_to_blender"],
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
