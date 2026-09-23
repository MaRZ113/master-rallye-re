"""Explicit experimental Blender topology export; safe patch exporters stay separate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .blender_export import _object_transform_is_identity, export_dx_attributes
from .library import parse_dx

try:
    from master_rallye.coords import blender_position_to_source
    from master_rallye.topology_writer import rebuild_topology, source_geometry
    from master_rallye.vertex_compiler import CornerInput, FaceInput, compile_faces
except ModuleNotFoundError:
    from .vendor.master_rallye.coords import blender_position_to_source
    from .vendor.master_rallye.topology_writer import rebuild_topology, source_geometry
    from .vendor.master_rallye.vertex_compiler import CornerInput, FaceInput, compile_faces


def _source_and_model(obj):
    if obj is None or obj.type != "MESH" or "mr_metadata_json" not in obj:
        raise ValueError("select one imported Master Rallye mesh")
    if not _object_transform_is_identity(obj):
        raise ValueError("apply object transforms before topology export; edit mesh positions directly")
    metadata = json.loads(obj["mr_metadata_json"])
    source_metadata = metadata["source"]
    source_path = Path(source_metadata["path"]).resolve()
    if not source_path.is_file():
        raise ValueError("source DX template is unavailable")
    source_bytes = source_path.read_bytes()
    if len(source_bytes) != source_metadata["byte_size"] or hashlib.sha256(source_bytes).hexdigest() != source_metadata["sha256"]:
        raise ValueError("source DX template changed after import")
    if obj.get("mr_material_alpha_edits_json", "{}") != "{}" or obj.get("mr_material_env_edits_json", "{}") != "{}":
        raise ValueError("topology export does not combine staged material-state edits; apply those separately")
    return source_path, source_bytes, parse_dx(source_path)


def _color_bytes(item, source_color: bytes | None) -> bytes:
    values = tuple(float(x) for x in (item.color_srgb if hasattr(item, "color_srgb") else item.color))
    if len(values) != 4:
        raise ValueError("vertex color must have four channels")
    if source_color is not None and all(abs(value - channel / 255.0) <= 1e-5 for value, channel in zip(values, source_color)):
        return source_color
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("vertex color channel outside 0..1")
    return bytes(max(0, min(255, round(value * 255))) for value in values)


def _faces_from_blender(obj, model):
    mesh = obj.data
    required = ("mr_source_vertex", "mr_source_vertex_valid", "mr_draw_id", "mr_source_triangle", "mr_group_id", "mr_source_normal")
    for name in required:
        if mesh.attributes.get(name) is None:
            raise ValueError(f"missing MR provenance attribute {name}")
    if len(mesh.uv_layers) != len(model.uv_sets):
        raise ValueError("topology export requires the original UV-set count")
    uv_layers = []
    for index in range(len(model.uv_sets)):
        layer = mesh.uv_layers.get(f"MR UV {index}")
        if layer is None:
            raise ValueError(f"MR UV {index} missing")
        uv_layers.append(layer)
    color = mesh.color_attributes.get("MR Vertex Color")
    normal = mesh.attributes["mr_source_normal"]
    if color is None or color.domain not in {"POINT", "CORNER"} or normal.domain not in {"POINT", "CORNER"}:
        raise ValueError("MR color and source-normal attributes must be POINT or CORNER")
    source_ids = mesh.attributes["mr_source_vertex"].data
    source_valid = mesh.attributes["mr_source_vertex_valid"].data
    face_valid = mesh.attributes.get("mr_source_face_valid")
    assignment_valid = mesh.attributes.get("mr_draw_assignment_valid")
    material_draws = {}
    for polygon in mesh.polygons:
        if face_valid is not None and not face_valid.data[polygon.index].value:
            continue
        triangle_id = mesh.attributes["mr_source_triangle"].data[polygon.index].value
        draw_id = mesh.attributes["mr_draw_id"].data[polygon.index].value
        if 0 <= draw_id < len(model.physical_draws) and triangle_id >= 0:
            material_draws.setdefault(polygon.material_index, set()).add(draw_id)
    faces = []
    for polygon in mesh.polygons:
        if len(polygon.loop_indices) != 3:
            raise ValueError(f"face {polygon.index}: triangulate quads/n-gons before export")
        draw_id = mesh.attributes["mr_draw_id"].data[polygon.index].value
        source_face = bool(face_valid.data[polygon.index].value) if face_valid is not None else True
        explicit = bool(assignment_valid.data[polygon.index].value) if assignment_valid is not None else source_face
        source_triangle = mesh.attributes["mr_source_triangle"].data[polygon.index].value if source_face else None
        corners = []
        for loop_index in polygon.loop_indices:
            loop = mesh.loops[loop_index]
            point = loop.vertex_index
            source_id = int(source_ids[point].value) if source_valid[point].value else None
            if source_id is not None and not 0 <= source_id < model.vertex_count:
                raise ValueError(f"point {point}: invalid source vertex ID {source_id}")
            coordinate = blender_position_to_source(mesh.vertices[point].co)
            normal_item = normal.data[point if normal.domain == "POINT" else loop_index]
            normal_value = tuple(float(x) for x in normal_item.vector)
            color_item = color.data[point if color.domain == "POINT" else loop_index]
            source_color = model.vertices.colors[source_id * 4:source_id * 4 + 4] if source_id is not None else None
            uvs = tuple(tuple(float(x) for x in layer.data[loop_index].uv) for layer in uv_layers)
            parent_attr = mesh.attributes.get("mr_parent_source_vertex")
            parent_id = int(parent_attr.data[point].value) if parent_attr is not None else -1
            corners.append(CornerInput(point, coordinate, normal_value, _color_bytes(color_item, source_color), uvs, source_id,
                                       parent_id if parent_id >= 0 else None))
        faces.append(FaceInput(tuple(corners), int(draw_id) if explicit or source_face else None,
                               int(polygon.material_index), int(source_triangle) if source_triangle is not None else None,
                               explicit))
    return faces, {slot: tuple(sorted(ids)) for slot, ids in material_draws.items()}


def preview_topology(obj):
    source_path, source, model = _source_and_model(obj)
    faces, material_draws = _faces_from_blender(obj, model)
    geometry, compilation = compile_faces(model, faces, material_draws)
    rebuilt = rebuild_topology(source, geometry)
    return source_path, rebuilt, compilation


def export_topology(obj, destination: Path):
    source_path, rebuilt, compilation = preview_topology(obj)
    destination = Path(destination).resolve()
    if destination == source_path or destination.exists():
        raise ValueError("topology output must be a fresh path different from the source")
    model = parse_dx(source_path)
    faces, material_draws = _faces_from_blender(obj, model)
    geometry, _ = compile_faces(model, faces, material_draws)
    originals = source_geometry(model)
    same_topology = all(
        geometry[draw_id].triangles == original.triangles
        and tuple(vertex.source_vertex_id for vertex in geometry[draw_id].vertices)
            == tuple(vertex.source_vertex_id for vertex in original.vertices)
        for draw_id, original in originals.items()
    )
    if same_topology:
        # Keep the frozen SDK v1 patch path authoritative for same-topology files.
        safe_result = export_dx_attributes(obj, destination)
        obj["mr_topology_last_export_json"] = json.dumps({
            "mode": "SAFE_SAME_TOPOLOGY_PATCH", "output": str(destination),
            "compilation": compilation.to_dict(),
        })
        return safe_result, compilation
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(rebuilt.data)
    obj["mr_topology_last_export_json"] = json.dumps({
        "mode": "EXPERIMENTAL_TOPOLOGY_REBUILD",
        "compilation": compilation.to_dict(),
        "rebuild": rebuilt.to_dict(),
        "generated_provenance": "source IDs retained where unique; generated/split vertices use parent IDs only in tooling",
        "output": str(destination),
    })
    return rebuilt, compilation
