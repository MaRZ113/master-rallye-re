"""Headless smoke import for the read-only GXM startpoint candidate overlay."""
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
    from master_rallye_io.library import (
        parse_course_gxm_float3_pool_bytes,
        parse_course_gxm_object_table_bytes,
        parse_course_txt,
    )

    raw = source.read_bytes()
    table = parse_course_gxm_object_table_bytes(raw, parse_course_txt(source.with_suffix(".txt")), source.name)
    pool = parse_course_gxm_float3_pool_bytes(raw, table, source.name)
    master_rallye_io.register()
    status = bpy.ops.import_scene.master_rallye_course_gxm_startpoint("EXEC_DEFAULT", filepath=str(source))
    if status != {"FINISHED"}:
        raise AssertionError(f"GXM helper import failed: {status}")

    overlay = next(
        collection for collection in bpy.data.collections
        if collection.get("mr_gxm_source") == str(source)
    )
    points = sorted(
        overlay.objects,
        key=lambda obj: obj.get("mr_source_point_index", -1),
    )
    if len(points) != 8:
        raise AssertionError(f"expected eight startpoint candidate points, got {len(points)}")
    for point_index, obj in enumerate(points):
        expected = pool.points[point_index]
        if obj.type != "EMPTY" or tuple(obj.location) != expected:
            raise AssertionError(f"point {point_index} is not a point-only identity-coordinate import")
        if obj.get("mr_source_node_name") != "startpoint":
            raise AssertionError("source node name was not preserved")
        if obj.get("mr_source_point_index") != point_index:
            raise AssertionError("source point identity was not preserved")
        if obj.get("mr_source_byte_offset") != pool.offset + point_index * 12:
            raise AssertionError("source byte span was not preserved")
        if obj.get("mr_source_byte_size") != 12:
            raise AssertionError("source byte size was not preserved")
        if obj.get("mr_geometry_status") != "candidate vertex; no edges or faces inferred":
            raise AssertionError("overlay overstates unknown geometry connectivity")

    root = bpy.data.collections.get(f"Master Rallye Course - {source.stem}")
    helpers = next((child for child in root.children if child.name.startswith("Course Helpers")), None) if root else None
    if helpers is None or overlay.name not in helpers.children:
        raise AssertionError("point overlay is not organized under Course Helpers")
    if overlay.get("mr_geometry_status") != "eight source positions shown as points; triangle connectivity is UNKNOWN":
        raise AssertionError("collection does not preserve the undecoded connectivity status")

    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "blender_version": bpy.app.version_string,
        "status": "PASS",
        "course": source.stem,
        "candidate_point_count": len(points),
        "point_only": all(obj.type == "EMPTY" for obj in points),
        "collection": overlay.name,
        "node_index": overlay["mr_source_node_index"],
        "parent_id": overlay["mr_source_node_parent_id"],
        "node_span": [overlay["mr_source_mesh_index"], overlay["mr_source_mesh_size"]],
        "pool_offset": overlay["mr_point_pool_offset"],
        "coordinate_claim": overlay["mr_source_to_blender"],
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
