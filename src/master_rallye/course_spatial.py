"""Read-only spatial comparisons for decoded course source and RaceTest data."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from typing import Iterable, Sequence

from .course_gxm import CourseGxmModelV7, CourseGxmNode

Point3 = tuple[float, float, float]
MeshOwner = tuple[int, str]


def _point3(point: Sequence[float]) -> Point3:
    if len(point) != 3:
        raise ValueError("expected a 3D point")
    result = (float(point[0]), float(point[1]), float(point[2]))
    if not all(math.isfinite(value) for value in result):
        raise ValueError("point components must be finite")
    return result


def gxm_source_to_runtime(point: Sequence[float]) -> Point3:
    """Map a GXM source point (x, y, z) to runtime/XML (x, z, -y)."""
    x, y, z = _point3(point)
    return x, z, -y


def runtime_to_blender(point: Sequence[float]) -> Point3:
    """Map runtime/XML (x, y, z) to the add-on's Blender frame (x, -z, y)."""
    x, y, z = _point3(point)
    return x, -z, y


def centroid3(points: Iterable[Sequence[float]]) -> Point3:
    values = tuple(_point3(point) for point in points)
    if not values:
        raise ValueError("cannot compute centroid of an empty point set")
    return tuple(sum(point[axis] for point in values) / len(values) for axis in range(3))  # type: ignore[return-value]


def bounds3(points: Iterable[Sequence[float]]) -> tuple[Point3, Point3] | None:
    values = tuple(_point3(point) for point in points)
    if not values:
        return None
    return (
        tuple(min(point[axis] for point in values) for axis in range(3)),  # type: ignore[return-value]
        tuple(max(point[axis] for point in values) for axis in range(3)),  # type: ignore[return-value]
    )


def distance3(first: Sequence[float], second: Sequence[float]) -> float:
    return math.dist(_point3(first), _point3(second))


def distance_xz(first: Sequence[float], second: Sequence[float]) -> float:
    a = _point3(first)
    b = _point3(second)
    return math.hypot(a[0] - b[0], a[2] - b[2])


def point_to_segment_distance_xz(
    point: Sequence[float], start: Sequence[float], end: Sequence[float],
) -> float:
    """Return horizontal X/Z distance from a point to a clamped edge segment."""
    p = _point3(point)
    a = _point3(start)
    b = _point3(end)
    dx, dz = b[0] - a[0], b[2] - a[2]
    length_squared = dx * dx + dz * dz
    if length_squared == 0.0:
        return distance_xz(p, a)
    fraction = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[2] - a[2]) * dz) / length_squared))
    closest = (a[0] + fraction * dx, 0.0, a[2] + fraction * dz)
    return distance_xz(p, closest)


def acute_xz_angle_degrees(first: Sequence[float], second: Sequence[float]) -> float | None:
    """Return the acute, direction-insensitive X/Z angle; None for a zero vector."""
    a = _point3(first)
    b = _point3(second)
    a_length = math.hypot(a[0], a[2])
    b_length = math.hypot(b[0], b[2])
    if a_length == 0.0 or b_length == 0.0:
        return None
    cosine = abs((a[0] * b[0] + a[2] * b[2]) / (a_length * b_length))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


@dataclass(frozen=True)
class SourceMeshSpatialMetrics:
    triangle_count: int
    unique_position_indices: tuple[int, ...]
    source_positions: tuple[Point3, ...]
    runtime_positions: tuple[Point3, ...]
    source_centroid: Point3 | None
    runtime_centroid: Point3 | None
    source_bounds: tuple[Point3, Point3] | None
    runtime_bounds: tuple[Point3, Point3] | None
    source_dimensions: Point3 | None
    runtime_dimensions: Point3 | None
    unique_edge_count: int
    edge_incidence_histogram: tuple[tuple[int, int], ...]
    all_edges_incident_to_two_triangles: bool


def analyze_source_mesh(model: CourseGxmModelV7, node: CourseGxmNode) -> SourceMeshSpatialMetrics:
    """Resolve a source mesh's true triangle/position topology and spatial bounds."""
    triangle_indices = model.mesh_triangle_indices(node)
    triplets = tuple(model.triangle(index).position_indices for index in triangle_indices)
    unique_indices = tuple(sorted({index for triangle in triplets for index in triangle}))
    source_positions = tuple(model.position(index) for index in unique_indices)
    runtime_positions = tuple(gxm_source_to_runtime(point) for point in source_positions)
    source_bounds = bounds3(source_positions)
    runtime_bounds = bounds3(runtime_positions)

    edge_counts: Counter[tuple[int, int]] = Counter()
    for a, b, c in triplets:
        edge_counts[tuple(sorted((a, b)))] += 1
        edge_counts[tuple(sorted((b, c)))] += 1
        edge_counts[tuple(sorted((c, a)))] += 1

    source_centroid = centroid3(source_positions) if source_positions else None
    runtime_centroid = gxm_source_to_runtime(source_centroid) if source_centroid else None
    source_dimensions = (
        tuple(high - low for low, high in zip(*source_bounds)) if source_bounds else None
    )
    runtime_dimensions = (
        tuple(high - low for low, high in zip(*runtime_bounds)) if runtime_bounds else None
    )
    return SourceMeshSpatialMetrics(
        triangle_count=len(triplets),
        unique_position_indices=unique_indices,
        source_positions=source_positions,
        runtime_positions=runtime_positions,
        source_centroid=source_centroid,
        runtime_centroid=runtime_centroid,
        source_bounds=source_bounds,
        runtime_bounds=runtime_bounds,
        source_dimensions=source_dimensions,  # type: ignore[arg-type]
        runtime_dimensions=runtime_dimensions,  # type: ignore[arg-type]
        unique_edge_count=len(edge_counts),
        edge_incidence_histogram=tuple(sorted(Counter(edge_counts.values()).items())),
        all_edges_incident_to_two_triangles=bool(edge_counts) and all(value == 2 for value in edge_counts.values()),
    )


@dataclass(frozen=True)
class MeshSpanRef:
    source_ordinal: int
    literal_name: str
    triangle_start: int
    triangle_count: int


def position_mesh_owners(
    triangle_position_triplets: Sequence[Sequence[int]],
    mesh_spans: Sequence[MeshSpanRef],
) -> dict[int, tuple[MeshOwner, ...]]:
    """Map each source position index to all moMesh spans that reference it.

    Every triangle must have exactly one owning span. Invalid, overlapping, or
    incomplete span tables are rejected so mutation eligibility fails closed.
    """
    owner_per_triangle: list[MeshOwner | None] = [None] * len(triangle_position_triplets)
    for span in mesh_spans:
        if span.triangle_start < 0 or span.triangle_count < 0:
            raise ValueError(f"negative moMesh span for {span.literal_name!r}")
        end = span.triangle_start + span.triangle_count
        if end > len(owner_per_triangle):
            raise ValueError(f"moMesh span exceeds triangle bank: {span.literal_name!r}")
        owner = (span.source_ordinal, span.literal_name)
        for triangle_index in range(span.triangle_start, end):
            if owner_per_triangle[triangle_index] is not None:
                raise ValueError(f"overlapping moMesh spans at triangle {triangle_index}")
            owner_per_triangle[triangle_index] = owner
    if any(owner is None for owner in owner_per_triangle):
        raise ValueError("triangle bank has unowned records")

    by_position: dict[int, set[MeshOwner]] = {}
    for triangle_index, triplet in enumerate(triangle_position_triplets):
        if len(triplet) != 3:
            raise ValueError(f"triangle {triangle_index} does not have three position references")
        owner = owner_per_triangle[triangle_index]
        assert owner is not None
        for position_index in triplet:
            by_position.setdefault(int(position_index), set()).add(owner)
    return {index: tuple(sorted(owners)) for index, owners in by_position.items()}


def source_model_position_owners(model: CourseGxmModelV7) -> dict[int, tuple[MeshOwner, ...]]:
    triplets = tuple(model.triangle(index).position_indices for index in range(model.triangles.count))
    spans = tuple(
        MeshSpanRef(node.ordinal, node.name, node.mesh_index, node.mesh_size)
        for node in model.object_table.nodes
        if node.class_name.casefold() == "momesh"
        and node.mesh_index is not None
        and node.mesh_size is not None
    )
    return position_mesh_owners(triplets, spans)


@dataclass(frozen=True)
class MarkerEdgeMetric:
    edge_index: int
    start_marker_index: int
    end_marker_index: int
    midpoint: Point3
    angle_to_pair_degrees: float | None
    pair_midpoint_distance_xz: float
    pair_midpoint_segment_distance_xz: float


@dataclass(frozen=True)
class PointMarkerPolygonMetric:
    marker_distances_3d: tuple[float, ...]
    polygon_centroid: Point3
    distance_to_polygon_centroid_3d: float
    edge_segment_distances_xz: tuple[float, ...]
    edge_midpoint_distances_xz: tuple[float, ...]
    nearest_edge_index: int


def point_to_marker_polygon(
    point: Sequence[float], marker_positions: Sequence[Sequence[float]],
) -> PointMarkerPolygonMetric:
    """Measure a point against every marker and closed X/Z polygon edge."""
    if len(marker_positions) < 2:
        raise ValueError("marker polygon requires at least two positions")
    value = _point3(point)
    markers = tuple(_point3(marker) for marker in marker_positions)
    center = centroid3(markers)
    segment_distances = []
    midpoint_distances = []
    for edge_index, start in enumerate(markers):
        end = markers[(edge_index + 1) % len(markers)]
        midpoint = tuple((start[axis] + end[axis]) / 2.0 for axis in range(3))
        segment_distances.append(point_to_segment_distance_xz(value, start, end))
        midpoint_distances.append(distance_xz(value, midpoint))
    return PointMarkerPolygonMetric(
        marker_distances_3d=tuple(distance3(value, marker) for marker in markers),
        polygon_centroid=center,
        distance_to_polygon_centroid_3d=distance3(value, center),
        edge_segment_distances_xz=tuple(segment_distances),
        edge_midpoint_distances_xz=tuple(midpoint_distances),
        nearest_edge_index=min(range(len(segment_distances)), key=segment_distances.__getitem__),
    )


def pair_to_marker_polygon(
    first: Sequence[float],
    second: Sequence[float],
    marker_positions: Sequence[Sequence[float]],
) -> dict[str, object]:
    """Measure pair separation/orientation against every closed marker-list edge."""
    if len(marker_positions) < 2:
        raise ValueError("marker polygon requires at least two positions")
    a, b = _point3(first), _point3(second)
    markers = tuple(_point3(point) for point in marker_positions)
    midpoint = tuple((a[axis] + b[axis]) / 2.0 for axis in range(3))
    direction = tuple(b[axis] - a[axis] for axis in range(3))
    edge_metrics = []
    for edge_index, start in enumerate(markers):
        end_index = (edge_index + 1) % len(markers)
        end = markers[end_index]
        edge_direction = tuple(end[axis] - start[axis] for axis in range(3))
        edge_midpoint = tuple((start[axis] + end[axis]) / 2.0 for axis in range(3))
        edge_metrics.append(MarkerEdgeMetric(
            edge_index=edge_index,
            start_marker_index=edge_index,
            end_marker_index=end_index,
            midpoint=edge_midpoint,  # type: ignore[arg-type]
            angle_to_pair_degrees=acute_xz_angle_degrees(direction, edge_direction),
            pair_midpoint_distance_xz=distance_xz(midpoint, edge_midpoint),
            pair_midpoint_segment_distance_xz=point_to_segment_distance_xz(midpoint, start, end),
        ))
    edges = tuple(edge_metrics)
    return {
        "pair_separation_3d": distance3(a, b),
        "pair_midpoint": midpoint,
        "pair_direction_xz": (direction[0], direction[2]),
        "edge_comparisons": edges,
        "smallest_angular_difference_edge": min(
            edges, key=lambda edge: math.inf if edge.angle_to_pair_degrees is None else edge.angle_to_pair_degrees,
        ),
        "nearest_edge_segment_to_midpoint": min(edges, key=lambda edge: edge.pair_midpoint_segment_distance_xz),
    }
