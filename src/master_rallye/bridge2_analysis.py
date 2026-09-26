"""Read-only analysis helpers for the R-BRIDGE2 9.10 cooker bridge.

The helpers preserve build identity and keep complete-model mesh spans tied to
the hierarchy or diagnostic sidecar that supplied them. They do not write or
convert game assets.
"""
from __future__ import annotations

import hashlib
import math
import re
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .demo_dx import inspect_demo_dx
from .dx import parse_dx_bytes
from .errors import BoundsError, FormatError
from .gxm import (
    parse_gxm_geometry_prefix_bytes,
    parse_gxm_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)
from .gxm_hierarchy import parse_gxm_hierarchy_tail, walk_depth_first
from .sidecar import SidecarModel, parse_sidecar


DX_COORDINATE_TRANSFORM = "(x, y, z) -> (x, z, -y)"
WHEEL_NODE_PREFIX = "wheel $cylinder"
COMPATIBILITY_STATUSES = frozenset({
    "CONFIRMED_BY_RUNTIME",
    "CONFIRMED_BY_STATIC",
    "SUPPORTED",
    "REJECTED_BY_RUNTIME",
    "REJECTED_BY_STATIC",
    "UNKNOWN",
})

RAW_DX_COMPATIBILITY_MATRIX: dict[str, dict[str, str]] = {
    "8.4.1": {
        "8.4.1": "CONFIRMED_BY_RUNTIME",
        "9.3.1": "UNKNOWN",
        "9.10.0": "UNKNOWN",
        "retail": "REJECTED_BY_STATIC",
    },
    "9.3.1": {
        "8.4.1": "UNKNOWN",
        "9.3.1": "CONFIRMED_BY_RUNTIME",
        "9.10.0": "UNKNOWN",
        "retail": "REJECTED_BY_STATIC",
    },
    "9.10.0": {
        "8.4.1": "UNKNOWN",
        "9.3.1": "UNKNOWN",
        "9.10.0": "CONFIRMED_BY_RUNTIME",
        "retail": "CONFIRMED_BY_RUNTIME",
    },
    "retail": {
        "8.4.1": "UNKNOWN",
        "9.3.1": "UNKNOWN",
        "9.10.0": "CONFIRMED_BY_RUNTIME",
        "retail": "CONFIRMED_BY_RUNTIME",
    },
}


@dataclass(frozen=True)
class WheelMeshGeometry:
    name: str
    record_start: int
    record_count: int
    span_source: str
    unique_vector_c_indices: tuple[int, ...]
    source_aabb_minimum: tuple[float, float, float]
    source_aabb_maximum: tuple[float, float, float]
    source_aabb_center: tuple[float, float, float]
    dx_aabb_minimum: tuple[float, float, float]
    dx_aabb_maximum: tuple[float, float, float]
    dx_aabb_center: tuple[float, float, float]


@dataclass(frozen=True)
class CompleteWheelGeometry:
    source: str
    file_size: int
    sha256: str
    header_words: tuple[int, ...]
    triangle_record_count: int
    vector_c_count: int
    hierarchy_status: str
    hierarchy_error: str | None
    meshes: tuple[WheelMeshGeometry, ...]


def _bounds(points: tuple[tuple[float, float, float], ...]) -> tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]:
    if not points:
        raise FormatError("cannot compute bounds for an empty mesh span")
    minimum = tuple(min(point[axis] for point in points) for axis in range(3))
    maximum = tuple(max(point[axis] for point in points) for axis in range(3))
    center = tuple((minimum[axis] + maximum[axis]) / 2.0 for axis in range(3))
    return minimum, maximum, center


def analyze_complete_wheel_geometry(
    data: bytes,
    *,
    source: str = "<bytes>",
    sidecar: SidecarModel | None = None,
) -> CompleteWheelGeometry:
    """Extract the four named wheel-mesh Vector-C bounds from complete.gxm.

    Type-1/version-1 hierarchy spans are preferred. A parsed matching sidecar
    can supply spans if the hierarchy parser fails closed on another node
    layout (as it currently does for the inspected 9.10 Navara). The returned
    values describe referenced source mesh vertices; they are not asserted to
    be runtime hardpoints.
    """
    prefix = parse_gxm_prefix_bytes(data, source)
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)

    hierarchy_status = "ACCEPTED"
    hierarchy_error = None
    spans: list[tuple[str, int, int, str]] = []
    try:
        hierarchy = parse_gxm_hierarchy_tail(data, triangles.hierarchy_offset)
        spans = [
            (node.name, node.mesh_start, node.mesh_count, "hierarchy")
            for node in walk_depth_first(hierarchy.roots)
            if node.name.casefold().startswith(WHEEL_NODE_PREFIX)
        ]
    except (BoundsError, FormatError) as exc:
        hierarchy_status = "UNSUPPORTED_OR_REJECTED"
        hierarchy_error = f"{type(exc).__name__}: {exc}"

    if hierarchy_status != "ACCEPTED":
        if sidecar is None:
            raise FormatError(
                f"cannot obtain wheel mesh spans from {source}: {hierarchy_error}; "
                "no sidecar fallback was supplied"
            )
        spans = [
            (mesh.name, mesh.index, mesh.size, "sidecar")
            for mesh in sidecar.meshes
            if mesh.name.casefold().startswith(WHEEL_NODE_PREFIX)
        ]

    if len(spans) != 4:
        raise FormatError(f"{source}: expected exactly four wheel-cylinder spans, found {len(spans)}")
    if len({name.casefold() for name, *_ in spans}) != 4:
        raise FormatError(f"{source}: duplicate wheel-cylinder span name")

    c_values = struct.unpack_from(f"<{triangles.vector_c_count * 3}f", data,
                                  triangles.vector_c_offset)
    meshes: list[WheelMeshGeometry] = []
    for name, start, count, span_source in spans:
        if count <= 0 or start < 0 or start + count > triangles.record_count:
            raise FormatError(f"{source}: {name!r} span {start}+{count} leaves the triangle table")
        c_indices: set[int] = set()
        for record_index in range(start, start + count):
            record = struct.unpack_from("<10I", data, triangles.record_offset + record_index * 52)
            c_indices.update(record[4:7])
        if not c_indices:
            raise FormatError(f"{source}: {name!r} has no referenced Vector-C positions")
        source_points = tuple(tuple(c_values[index * 3:index * 3 + 3]) for index in sorted(c_indices))
        dx_points = tuple((x, z, -y) for x, y, z in source_points)
        source_min, source_max, source_center = _bounds(source_points)
        dx_min, dx_max, dx_center = _bounds(dx_points)
        meshes.append(WheelMeshGeometry(
            name=name,
            record_start=start,
            record_count=count,
            span_source=span_source,
            unique_vector_c_indices=tuple(sorted(c_indices)),
            source_aabb_minimum=source_min,
            source_aabb_maximum=source_max,
            source_aabb_center=source_center,
            dx_aabb_minimum=dx_min,
            dx_aabb_maximum=dx_max,
            dx_aabb_center=dx_center,
        ))

    return CompleteWheelGeometry(
        source=source,
        file_size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        header_words=prefix.header_words,
        triangle_record_count=triangles.record_count,
        vector_c_count=triangles.vector_c_count,
        hierarchy_status=hierarchy_status,
        hierarchy_error=hierarchy_error,
        meshes=tuple(meshes),
    )


def analyze_complete_wheel_file(gxm_path: Path, sidecar_path: Path | None = None) -> CompleteWheelGeometry:
    sidecar = parse_sidecar(sidecar_path) if sidecar_path is not None else None
    return analyze_complete_wheel_geometry(gxm_path.read_bytes(), source=str(gxm_path), sidecar=sidecar)


def parse_vehicle_properties(xml_path: Path, vehicle_name: str) -> dict[str, dict[str, str]]:
    """Return raw type/value attributes under one exact Vehicles/<name>/ path."""
    if not vehicle_name or "/" in vehicle_name or "\\" in vehicle_name:
        raise ValueError("vehicle_name must be one path component")
    prefix = f"Vehicles/{vehicle_name}/"
    result: dict[str, dict[str, str]] = {}
    for value in ET.parse(xml_path).iter("Value"):
        name = value.get("Name")
        if name is None or not name.startswith(prefix):
            continue
        relative = name[len(prefix):]
        if relative in result:
            raise FormatError(f"duplicate vehicle property {name!r} in {xml_path}")
        raw = value.get("Value")
        kind = value.get("Type")
        if raw is None or kind is None:
            raise FormatError(f"vehicle property {name!r} lacks Type or Value in {xml_path}")
        result[relative] = {"type": kind, "value": raw}
    return result

def audit_vehicle_config_roots(xml_path: Path) -> dict[str, Any]:
    """List named and numeric CarN roots without guessing an alias between them."""
    roots: set[str] = set()
    for value in ET.parse(xml_path).iter("Value"):
        name = value.get("Name", "")
        match = re.match(r"^Vehicles/([^/]+)/", name)
        if match:
            roots.add(match.group(1))
    numeric = sorted(root for root in roots if re.fullmatch(r"Car\d+", root, re.IGNORECASE))
    named = sorted((root for root in roots if root not in numeric), key=str.casefold)
    return {
        "status": "NUMERIC_CAR_ROOTS_PRESENT" if numeric else "NO_NUMERIC_CAR_ROOTS_FOUND",
        "numeric_car_roots": numeric,
        "named_vehicle_roots": named,
        "alias_resolution": "UNRESOLVED",
    }


def wheel_dimension_properties(properties: dict[str, dict[str, str]]) -> dict[str, str]:
    """Select direct dimension/suspension fields without assigning hardpoint semantics."""
    exact = (
        "Dimensions/WheelBase",
        "Dimensions/TrackWidthFront",
        "Dimensions/TrackWidthRear",
        "Dimensions/WheelRadiusFront",
        "Dimensions/WheelRadiusRear",
        "Suspension/Front/RideHeight",
        "Suspension/Rear/RideHeight",
        "Suspension/Front/SuspAppPointOffset",
        "Suspension/Rear/SuspAppPointOffset",
        "Suspension/Front/SuspAppPointOffsetLat",
        "Suspension/Front/SuspAppPointOffsetLong",
        "Suspension/Front/SuspAppPointOffsetVert",
        "Suspension/Rear/SuspAppPointOffsetLat",
        "Suspension/Rear/SuspAppPointOffsetLong",
        "Suspension/Rear/SuspAppPointOffsetVert",
        "Suspension/Front/MaxDroop",
        "Suspension/Rear/MaxDroop",
    )
    return {key: properties[key]["value"] for key in exact if key in properties}


def validate_compatibility_matrix(matrix: dict[str, dict[str, str]],
                                  builds: tuple[str, ...] = ("8.4.1", "9.3.1", "9.10.0", "retail")) -> None:
    """Fail closed on missing, extra, or unsupported producer/loader cells."""
    if set(matrix) != set(builds):
        raise ValueError("compatibility matrix producer rows do not match requested builds")
    for producer in builds:
        row = matrix[producer]
        if set(row) != set(builds):
            raise ValueError(f"compatibility matrix loader columns are incomplete for {producer}")
        invalid = {status for status in row.values() if status not in COMPATIBILITY_STATUSES}
        if invalid:
            raise ValueError(f"unsupported compatibility status in {producer}: {sorted(invalid)}")


def validate_transfer_provenance(record: dict[str, Any]) -> dict[str, Any]:
    """Validate supplied hashes while preserving explicitly unknown provenance."""
    if record.get("evidence") != "HUMAN_RUNTIME_CONFIRMED":
        raise ValueError("transfer record must retain its human runtime evidence label")
    for field in ("source_hashes", "generated_hashes"):
        values = record.get(field)
        if values is None:
            continue
        if not isinstance(values, list):
            raise ValueError(f"{field} must be a list or null when unknown")
        if any(not isinstance(value, str) or len(value) != 64
               or any(char not in "0123456789abcdef" for char in value.lower()) for value in values):
            raise ValueError(f"{field} contains a malformed SHA-256")
    return {
        "valid": True,
        "source_hashes_verified": bool(record.get("source_hashes")),
        "generated_hashes_verified": bool(record.get("generated_hashes")),
        "source_build_identified": record.get("source_build") not in (None, "UNKNOWN_FROM_USER_REPORT"),
        "target_slot_identified": record.get("target_slot") not in (None, "UNKNOWN_FROM_USER_REPORT"),
    }


def _float_array_stats(first: tuple[tuple[float, ...], ...],
                       second: tuple[tuple[float, ...], ...]) -> dict[str, Any]:
    if len(first) != len(second) or any(len(a) != len(b) for a, b in zip(first, second)):
        return {"same_shape": False, "first_count": len(first), "second_count": len(second)}
    deltas = [abs(a - b) for row_a, row_b in zip(first, second) for a, b in zip(row_a, row_b)]
    changed_items = sum(a != b for a, b in zip(first, second))
    return {
        "same_shape": True,
        "count": len(first),
        "changed_items": changed_items,
        "changed_components": sum(delta != 0.0 for delta in deltas),
        "max_abs_delta": max(deltas, default=0.0),
        "rms_delta": math.sqrt(sum(delta * delta for delta in deltas) / len(deltas)) if deltas else 0.0,
    }


def compare_dx_assets(first: bytes, second: bytes, *, first_source: str = "first",
                      second_source: str = "second") -> dict[str, Any]:
    """Compare the common vehicle-DX structure without assigning draw semantics."""
    a = inspect_demo_dx(first, first_source)
    b = inspect_demo_dx(second, second_source)
    changed_offsets = [index for index, (left, right) in enumerate(zip(first, second)) if left != right]
    byte_diff = len(changed_offsets) + abs(len(first) - len(second))
    try:
        parse_dx_bytes(first, first_source)
        first_retail = {"status": "ACCEPTED"}
    except Exception as exc:  # parser errors are recorded, never interpreted as runtime failures
        first_retail = {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
    try:
        parse_dx_bytes(second, second_source)
        second_retail = {"status": "ACCEPTED"}
    except Exception as exc:
        second_retail = {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}

    first_collision = first[a.collision.offset:]
    second_collision = second[b.collision.offset:]
    byte_regions = _same_layout_byte_regions(first, second, a, b)
    return {
        "first": {"source": first_source, "size": len(first), "sha256": a.sha256,
                  "header": list(a.header), "retail_parser": first_retail},
        "second": {"source": second_source, "size": len(second), "sha256": b.sha256,
                   "header": list(b.header), "retail_parser": second_retail},
        "byte_diff": {"exact_equal": first == second, "changed_byte_count": byte_diff,
                      "common_length_changed_byte_count": len(changed_offsets),
                      "common_length_changed_ranges": _ranges(changed_offsets),
                      "length_delta": len(second) - len(first),
                      "same_layout_regions": byte_regions},
        "render": {
            "positions": _float_array_stats(a.positions, b.positions),
            "normals": _float_array_stats(a.normals, b.normals),
            "colors_equal": a.colors == b.colors,
            "uv_sets_equal": a.uv_sets == b.uv_sets,
            "local_indices_equal": a.local_indices == b.local_indices,
            "global_indices_equal": a.global_indices == b.global_indices,
        },
        "draw_material_raw": {"first_size": len(a.draw_raw), "second_size": len(b.draw_raw),
                              "exact_equal": a.draw_raw == b.draw_raw},
        "collision_raw": {"first_size": len(first_collision), "second_size": len(second_collision),
                          "exact_equal": first_collision == second_collision,
                          "first_tags": list(a.collision.tag_ids),
                          "second_tags": list(b.collision.tag_ids)},
    }


def _same_layout_byte_regions(first: bytes, second: bytes, a, b) -> dict[str, Any] | None:
    """Account for raw byte changes by parsed region when both layouts align."""
    if len(first) != len(second):
        return None
    count = a.header[3]
    if count != b.header[3] or len(a.positions) != len(b.positions):
        return None

    positions = (16, 16 + count * 12)
    normals = (positions[1], positions[1] + count * 12)
    colors = (normals[1], normals[1] + count * 4)
    uv_count_offset = colors[1]
    uv_count_a = struct.unpack_from("<I", first, uv_count_offset)[0]
    uv_count_b = struct.unpack_from("<I", second, uv_count_offset)[0]
    if uv_count_a != uv_count_b or len(a.uv_sets) != len(b.uv_sets):
        return None
    uv_bytes = count * 8 * uv_count_a
    uv_sets = (uv_count_offset + 4, uv_count_offset + 4 + uv_bytes)
    local_count_offset = uv_sets[1]
    local_count_a = struct.unpack_from("<I", first, local_count_offset)[0]
    local_count_b = struct.unpack_from("<I", second, local_count_offset)[0]
    if local_count_a != local_count_b or len(a.local_indices) != len(b.local_indices):
        return None
    local_indices = (local_count_offset + 4, local_count_offset + 4 + local_count_a * 2)
    regions = {
        "header_and_counts": (0, 16),
        "positions": positions,
        "normals": normals,
        "colors": colors,
        "uv_count": (uv_count_offset, uv_count_offset + 4),
        "uv_sets": uv_sets,
        "local_index_count": (local_count_offset, local_count_offset + 4),
        "local_indices": local_indices,
        "draw_material_raw": (a.draw_offset, a.global_offset),
        "global_index_table": (a.global_offset, a.collision.offset),
        "collision_and_tail": (a.collision.offset, len(first)),
    }
    ordered = sorted((start, end, name) for name, (start, end) in regions.items())
    cursor = 0
    for start, end, _name in ordered:
        if start != cursor or end < start:
            return None
        cursor = end
    if cursor != len(first):
        return None

    counts = {
        name: sum(first[offset] != second[offset] for offset in range(start, end))
        for name, (start, end) in regions.items()
    }
    changed = sum(counts.values())
    expected = sum(left != right for left, right in zip(first, second))
    return {
        "valid_partition": changed == expected,
        "changed_byte_count": changed,
        "regions": counts,
        "unexplained_changed_byte_count": expected - changed,
    }


def _ranges(offsets: list[int]) -> list[dict[str, int]]:
    if not offsets:
        return []
    result: list[dict[str, int]] = []
    start = previous = offsets[0]
    for offset in offsets[1:]:
        if offset != previous + 1:
            result.append({"start": start, "end_exclusive": previous + 1})
            start = offset
        previous = offset
    result.append({"start": start, "end_exclusive": previous + 1})
    return result
