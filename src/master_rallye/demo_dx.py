"""Conservative structural inspection of the observed demo DX vehicle family.

The demo draw grammar is retained as raw bytes. This module does not construct
a retail DxModel or assign meanings to unproved draw records.
"""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass

from .collision import CollisionSections, parse_collision_sections
from .dx import Reader
from .errors import BoundsError, FormatError

MAX_VERTICES = 1_000_000
MAX_INDICES = 10_000_000
MAX_UV_SETS = 8


@dataclass(frozen=True)
class DemoDxView:
    data: bytes
    source: str
    header: tuple[int, int, int, int]
    positions: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    colors: bytes
    uv_sets: tuple[bytes, ...]
    local_indices: tuple[int, ...]
    draw_offset: int
    draw_raw: bytes
    global_offset: int
    global_indices: tuple[int, ...]
    collision: CollisionSections

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


def inspect_demo_dx(data: bytes, source: str = "<bytes>") -> DemoDxView:
    reader = Reader(data, source)
    magic, word04, word08, count = reader.unpack("<4I", 0, "demo DX header")
    if magic != 0xD00D or not 0 < count <= MAX_VERTICES:
        raise FormatError(f"unsupported demo DX header in {source}")
    offset = 16
    positions = tuple(reader.unpack("<3f", offset + i * 12, "position") for i in range(count))
    offset += count * 12
    normals = tuple(reader.unpack("<3f", offset + i * 12, "normal") for i in range(count))
    offset += count * 12
    if any(not math.isfinite(value) for row in positions + normals for value in row):
        raise FormatError(f"non-finite demo DX position or normal in {source}")
    colors = reader.blob(offset, count * 4, "colors")
    offset += count * 4
    uv_count = reader.u32(offset, "UV set count")
    if uv_count > MAX_UV_SETS:
        raise FormatError(f"unreasonable demo UV set count {uv_count}")
    offset += 4
    uv_sets = []
    for _ in range(uv_count):
        uv_sets.append(reader.blob(offset, count * 8, "UV array"))
        offset += count * 8
    local_count = reader.u32(offset, "local index count")
    if local_count > MAX_INDICES:
        raise FormatError(f"unreasonable demo local index count {local_count}")
    offset += 4
    local_indices = reader.unpack(f"<{local_count}H", offset, "local indices") if local_count else ()
    offset += local_count * 2
    draw_offset = offset
    reader.require(draw_offset, 8, "demo draw envelope")

    # The observed demo family has one raw draw region followed by a unique
    # (1, local-index-count) global table. Reject ambiguous candidate boundaries.
    marker = struct.pack("<II", 1, local_count)
    candidates: list[tuple[int, tuple[int, ...], CollisionSections]] = []
    start = draw_offset + 8
    while (found := data.find(marker, start)) >= 0:
        start = found + 1
        table_end = found + 8 + local_count * 4
        if table_end > len(data):
            continue
        global_indices = reader.unpack(f"<{local_count}I", found + 8, "global indices") if local_count else ()
        if any(index >= count for index in global_indices):
            continue
        try:
            collision = parse_collision_sections(data[table_end:], base_offset=table_end,
                                                 source=source, strict=False)
        except (BoundsError, FormatError):
            continue
        if collision.errors or collision.warnings or (collision.unparsed_data and collision.spatial_bounds_1339 is None):
            continue
        if collision.unparsed_data and len(collision.unparsed_data) != 44:
            continue
        candidates.append((found, global_indices, collision))
    if len(candidates) != 1:
        raise FormatError(f"demo DX global-table boundary ambiguous or absent in {source}: {len(candidates)} candidates")
    global_offset, global_indices, collision = candidates[0]
    return DemoDxView(data, source, (magic, word04, word08, count), positions,
                      normals, colors, tuple(uv_sets), tuple(local_indices),
                      draw_offset, data[draw_offset:global_offset], global_offset,
                      tuple(global_indices), collision)


def _float_stats(first, second) -> dict:
    a = tuple(tuple(row) for row in first)
    b = tuple(tuple(row) for row in second)
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        return {"same_shape": False, "first_count": len(a), "second_count": len(b)}
    differences = [abs(x - y) for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b)]
    return {"same_shape": True, "count": len(a),
            "changed_items": sum(any(x != y for x, y in zip(row_a, row_b))
                                 for row_a, row_b in zip(a, b)),
            "changed_components": sum(value != 0 for value in differences),
            "max_abs_delta": max(differences, default=0.0),
            "rms_delta": math.sqrt(sum(value * value for value in differences) / len(differences))
            if differences else 0.0}


def _geometry(first, second) -> dict:
    return {"first_counts": [first.vertex_count, first.triangle_count],
            "second_counts": [second.vertex_count, second.triangle_count],
            "vertices": _float_stats(first.vertices, second.vertices),
            "triangles_equal": first.triangles == second.triangles}


def _representation(first, second) -> dict:
    return {"geometry_a": _geometry(first.geometry_a, second.geometry_a),
            "geometry_b": _geometry(first.geometry_b, second.geometry_b),
            "referenced_vertex_indices_equal": first.referenced_vertex_indices == second.referenced_vertex_indices,
            "edges_equal": first.edges == second.edges,
            "primary_descriptors_equal": tuple(face.primary_indices for face in first.face_descriptors) ==
                                         tuple(face.primary_indices for face in second.face_descriptors),
            "secondary_descriptors_equal": tuple(face.secondary_indices for face in first.face_descriptors) ==
                                           tuple(face.secondary_indices for face in second.face_descriptors),
            "secondary_descriptor_changed_faces": sum(a.secondary_indices != b.secondary_indices
                                                      for a, b in zip(first.face_descriptors, second.face_descriptors)),
            "secondary_descriptor_multisets_equal_per_face": (
                len(first.face_descriptors) == len(second.face_descriptors) and
                all(sorted(a.secondary_indices) == sorted(b.secondary_indices)
                    for a, b in zip(first.face_descriptors, second.face_descriptors))),
            "edge_face_adjacency_equal": first.edge_face_adjacency == second.edge_face_adjacency,
            "face_loops_equal": first.face_loop_indices == second.face_loop_indices,
            "face_scalars": _float_stats(((x,) for x in first.face_scalars),
                                          ((x,) for x in second.face_scalars))}


def _collision(first: CollisionSections, second: CollisionSections) -> dict:
    result = {"tag_ids_first": first.tag_ids, "tag_ids_second": second.tag_ids,
              "bsp_raw_equal": (first.bsp.raw if first.bsp else None) == (second.bsp.raw if second.bsp else None),
              "cylinder_raw_equal": (first.cylinder.raw if first.cylinder else None) ==
                                    (second.cylinder.raw if second.cylinder else None),
              "unparsed_raw_equal": first.unparsed_data == second.unparsed_data,
              "tag101": None, "bounds_1339": None}
    if first.convex_hull and second.convex_hull:
        a, b = first.convex_hull, second.convex_hull
        result["tag101"] = {"first_size": len(a.raw), "second_size": len(b.raw),
                            "raw_equal": a.raw == b.raw,
                            "base_geometry": _geometry(a.base_geometry, b.base_geometry),
                            "base_scalar": _float_stats(((a.base_scalar,),), ((b.base_scalar,),)),
                            "representation_a": _representation(a.representation_a, b.representation_a),
                            "representation_b": _representation(a.representation_b, b.representation_b)}
    if first.spatial_bounds_1339 and second.spatial_bounds_1339:
        a, b = first.spatial_bounds_1339, second.spatial_bounds_1339
        result["bounds_1339"] = {"raw_equal": a.raw == b.raw,
                                 "center": _float_stats((a.center,), (b.center,)),
                                 "radius": _float_stats(((a.radius,),), ((b.radius,),)),
                                 "minimum": _float_stats((a.minimum,), (b.minimum,)),
                                 "maximum": _float_stats((a.maximum,), (b.maximum,))}
    return result


def _collision_nonfloat_equal(first: DemoDxView, second: DemoDxView, *, mask_secondary: bool = False) -> bool:
    """Require every unmodelled collision byte to match before float-drift status."""
    def masked(view: DemoDxView) -> bytes:
        data = bytearray(view.data[view.collision.offset:])
        def clear(absolute: int, size: int) -> None:
            start = absolute - view.collision.offset
            if start < 0 or start + size > len(data):
                raise FormatError("parsed collision float range outside trailer")
            data[start:start + size] = bytes(size)
        hull = view.collision.convex_hull
        if hull:
            clear(hull.base_geometry.vertex_data_offset, 12 * hull.base_geometry.vertex_count)
            clear(hull.base_scalar_offset, 4)
            for rep in (hull.representation_a, hull.representation_b):
                for geom in (rep.geometry_a, rep.geometry_b):
                    clear(geom.vertex_data_offset, 12 * geom.vertex_count)
                clear(rep.face_scalar_offset, 4 * len(rep.face_scalars))
                if mask_secondary:
                    for face in rep.face_descriptors:
                        clear(face.secondary_count_offset + 4, 4 * len(face.secondary_indices))
        cyl = view.collision.cylinder
        if cyl:
            clear(cyl.payload_offset, 8)
        bounds = view.collision.spatial_bounds_1339
        if bounds:
            clear(bounds.offset + 4, 40)
        return bytes(data)
    return masked(first) == masked(second)


def _collision_verdict(collision: dict, tolerance: float) -> tuple[bool, bool]:
    """Return (proven topology difference, unresolved non-float difference)."""
    if collision["tag_ids_first"] != collision["tag_ids_second"]:
        return True, False
    unresolved = not collision["bsp_raw_equal"] or not collision["cylinder_raw_equal"]
    a = collision["tag101"]
    if a:
        if a["first_size"] != a["second_size"]:
            return True, False
        for label in ("base_geometry", "representation_a", "representation_b"):
            blocks = [a[label]] if label == "base_geometry" else [a[label]["geometry_a"], a[label]["geometry_b"]]
            for block in blocks:
                if block["first_counts"] != block["second_counts"] or not block["triangles_equal"]:
                    return True, False
                if not block["vertices"]["same_shape"] or block["vertices"]["max_abs_delta"] > tolerance:
                    unresolved = True
        for label in ("representation_a", "representation_b"):
            rep = a[label]
            if not all(rep[key] for key in ("referenced_vertex_indices_equal", "edges_equal",
                                            "primary_descriptors_equal", "edge_face_adjacency_equal",
                                            "face_loops_equal")):
                unresolved = True
            if not rep["secondary_descriptors_equal"]:
                unresolved = True  # Secondary list semantics have not been resolved.
            if not rep["face_scalars"]["same_shape"] or rep["face_scalars"]["max_abs_delta"] > tolerance:
                unresolved = True
        if a["base_scalar"]["max_abs_delta"] > tolerance:
            unresolved = True
    bounds = collision["bounds_1339"]
    if bounds:
        if any(bounds[key]["max_abs_delta"] > tolerance for key in ("center", "radius", "minimum", "maximum")):
            unresolved = True
    if not collision["unparsed_raw_equal"] and bounds is None:
        unresolved = True
    return False, unresolved


def compare_demo_dx(first: bytes, second: bytes, *, first_source: str = "first",
                    second_source: str = "second", float_tolerance: float = 1e-5) -> dict:
    if not math.isfinite(float_tolerance) or float_tolerance < 0:
        raise ValueError("float_tolerance must be finite and nonnegative")
    a = inspect_demo_dx(first, first_source)
    b = inspect_demo_dx(second, second_source)
    position = _float_stats(a.positions, b.positions)
    normal = _float_stats(a.normals, b.normals)
    if position["same_shape"]:
        position["changed_vertices"] = position["changed_items"]
    if normal["same_shape"]:
        normal["changed_vertices"] = normal["changed_items"]
    collision = _collision(a.collision, b.collision)
    collision["nonfloat_bytes_equal"] = _collision_nonfloat_equal(a, b)
    collision["other_bytes_equal_after_float_and_secondary_mask"] = (
        _collision_nonfloat_equal(a, b, mask_secondary=True))
    topology_diff, unresolved = _collision_verdict(collision, float_tolerance)
    header_equal = a.header == b.header
    local_equal = a.local_indices == b.local_indices
    global_equal = a.global_indices == b.global_indices
    if first == second:
        verdict = "BYTE_IDENTICAL"
    elif not header_equal or not local_equal or not global_equal or topology_diff or len(a.uv_sets) != len(b.uv_sets):
        verdict = "STRUCTURALLY_DIFFERENT"
    elif (unresolved or not collision["nonfloat_bytes_equal"] or a.draw_raw != b.draw_raw or a.colors != b.colors or a.uv_sets != b.uv_sets or
          not position["same_shape"] or not normal["same_shape"] or
          position["max_abs_delta"] > float_tolerance or normal["max_abs_delta"] > float_tolerance):
        verdict = "UNRESOLVED"
    else:
        verdict = "SEMANTICALLY_EQUIVALENT_WITH_FLOAT_DRIFT"
    return {"first": {"source": first_source, "size": len(first), "sha256": a.sha256},
            "second": {"source": second_source, "size": len(second), "sha256": b.sha256},
            "header": {"first": a.header, "second": b.header, "equal": header_equal},
            "positions": position, "normals": normal,
            "colors_equal": a.colors == b.colors,
            "uv_sets_equal": a.uv_sets == b.uv_sets,
            "local_indices": {"first_count": len(a.local_indices), "second_count": len(b.local_indices),
                              "equal": local_equal},
            "draw_material_raw": {"first_size": len(a.draw_raw), "second_size": len(b.draw_raw),
                                  "equal": a.draw_raw == b.draw_raw},
            "global_indices": {"first_count": len(a.global_indices), "second_count": len(b.global_indices),
                               "equal": global_equal},
            "collision": collision, "verdict": verdict,
            "float_tolerance_for_classification": float_tolerance}
