"""Source-only geometric reconstruction controls for GXM ``$chull`` input.

The policy implemented here is a deterministic geometric convex-hull model.
It is not represented as the DEMO 9.3.1 native cooker algorithm: the 9.3.1
PlaneThickness value and native tie-breaking rules have not been established.
This module intentionally has no DX/parser dependency.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .collision_oracle import gxm_to_demo_xyz
from .gxm_chull import analyze_gxm_chull

Vec3 = tuple[float, float, float]
Triangle = tuple[int, int, int]
Edge = tuple[int, int]


class HullPredictionError(ValueError):
    """A fail-closed source geometry or hull consistency error."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class HullPolicy:
    """Numerical policy for the generic geometry control, not native settings."""

    support_tolerance: float = 1e-6
    area_epsilon: float = 1e-10
    projection_epsilon: float = 1e-12

    def validate(self) -> None:
        for name, value in (("support_tolerance", self.support_tolerance),
                            ("area_epsilon", self.area_epsilon),
                            ("projection_epsilon", self.projection_epsilon)):
            if not math.isfinite(value) or value <= 0:
                raise HullPredictionError("INVALID_POLICY", f"{name} must be finite and positive")


@dataclass(frozen=True)
class PlaneDecision:
    combination_index: int
    source_c_indices: tuple[int, int, int]
    disposition: str
    normal: Vec3 | None
    distance: float | None
    cross_magnitude: float
    coplanar_source_c_indices: tuple[int, ...] = ()
    face_index: int | None = None


@dataclass(frozen=True)
class PolygonFacePrediction:
    source_c_indices: tuple[int, ...]
    coplanar_source_c_indices: tuple[int, ...]
    normal: Vec3
    distance: float
    first_supporting_triple: tuple[int, int, int]


@dataclass(frozen=True)
class RepBCorePrediction:
    directive: str
    source_record_range: tuple[int, int]
    source_triangle_record_count: int
    source_c_indices: tuple[int, ...]
    source_point_order: tuple[int, ...]
    source_positions: tuple[tuple[int, Vec3], ...]
    vertex_source_c_indices: tuple[int, ...]
    vertices: tuple[Vec3, ...]
    polygon_faces: tuple[PolygonFacePrediction, ...]
    triangles_source_c_indices: tuple[Triangle, ...]
    edges_source_c_indices: tuple[Edge, ...]
    edge_face_adjacency: tuple[tuple[int, int], ...]
    plane_trace: tuple[PlaneDecision, ...]
    policy: HullPolicy
    validation: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.validation

    def summary(self) -> dict:
        counts = {}
        for row in self.plane_trace:
            counts[row.disposition] = counts.get(row.disposition, 0) + 1
        return {
            "status": "VALID_GEOMETRIC_CONTROL" if self.valid else "INVALID",
            "algorithm_classification": "SOURCE_ONLY_GENERIC_GEOMETRIC_HULL_CONTROL",
            "native_equivalence": "NOT_CLAIMED",
            "directive": self.directive,
            "source_record_range": list(self.source_record_range),
            "source_triangle_record_count": self.source_triangle_record_count,
            "source_c_count": len(self.source_c_indices),
            "source_c_indices": list(self.source_c_indices),
            "source_point_order": list(self.source_point_order),
            "predicted_vertex_count": len(self.vertex_source_c_indices),
            "predicted_vertex_source_c_indices": list(self.vertex_source_c_indices),
            "polygon_face_count": len(self.polygon_faces),
            "polygon_face_source_loops": [list(face.source_c_indices) for face in self.polygon_faces],
            "triangle_count": len(self.triangles_source_c_indices),
            "edge_count": len(self.edges_source_c_indices),
            "edge_face_adjacency_count": len(self.edge_face_adjacency),
            "plane_decision_count": len(self.plane_trace),
            "plane_disposition_counts": counts,
            "policy": {
                "support_tolerance": self.policy.support_tolerance,
                "area_epsilon": self.policy.area_epsilon,
                "projection_epsilon": self.policy.projection_epsilon,
                "plane_thickness_source": "generic_policy_only; 9.3.1 native value unresolved",
            },
            "validation": list(self.validation),
        }


def _dot(first: Sequence[float], second: Sequence[float]) -> float:
    return sum(first[axis] * second[axis] for axis in range(3))


def _sub(first: Sequence[float], second: Sequence[float]) -> Vec3:
    return tuple(first[axis] - second[axis] for axis in range(3))


def _cross(first: Sequence[float], second: Sequence[float]) -> Vec3:
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def _magnitude(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _normalized(vector: Sequence[float]) -> Vec3:
    length = _magnitude(vector)
    if length == 0:
        raise HullPredictionError("ZERO_VECTOR", "cannot normalize a zero-length vector")
    return tuple(value / length for value in vector)


def _boundary_loop(coplanar_ids: Sequence[int], points: Mapping[int, Vec3], normal: Vec3,
                   epsilon: float) -> tuple[int, ...]:
    """Return the 2D convex boundary, dropping collinear/interior coplanar points."""
    axis = min(range(3), key=lambda index: abs(normal[index]))
    reference = tuple(1.0 if index == axis else 0.0 for index in range(3))
    u = _normalized(_cross(normal, reference))
    v = _cross(normal, u)  # u x v points along the outward normal.
    projected = []
    for source_id in coplanar_ids:
        point = points[source_id]
        projected.append((_dot(point, u), _dot(point, v), source_id))
    projected.sort()

    def turn(origin, first, second) -> float:
        return ((first[0] - origin[0]) * (second[1] - origin[1])
                - (first[1] - origin[1]) * (second[0] - origin[0]))

    lower = []
    for point in projected:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= epsilon:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(projected):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= epsilon:
            upper.pop()
        upper.append(point)
    loop = tuple(point[2] for point in lower[:-1] + upper[:-1])
    if len(loop) < 3 or len(set(loop)) != len(loop):
        raise HullPredictionError("DEGENERATE_FACE", "supporting plane did not produce a simple polygon")
    return loop


def triangulate_polygon_faces(
    faces: Sequence[PolygonFacePrediction], *, anchor_index: int = 0,
) -> tuple[Triangle, ...]:
    """Create a source-only fan triangulation from a polygon-loop position."""
    if not isinstance(anchor_index, int) or anchor_index < 0:
        raise HullPredictionError("INVALID_TRIANGULATION_POLICY", "anchor_index must be a nonnegative integer")
    triangles = []
    for face in faces:
        loop = face.source_c_indices
        if len(loop) < 3:
            raise HullPredictionError("DEGENERATE_FACE", "cannot triangulate a face with fewer than three vertices")
        anchor_offset = anchor_index % len(loop)
        anchor = loop[anchor_offset]
        around = [loop[(anchor_offset + offset) % len(loop)]
                  for offset in range(1, len(loop))]
        triangles.extend((anchor, around[index], around[index + 1])
                         for index in range(len(around) - 1))
    return tuple(triangles)


def build_rep_b_core_from_source_points(
    source_points: Mapping[int, Sequence[float]],
    source_point_order: Sequence[int],
    *,
    directive: str = "<source-points>",
    source_record_range: tuple[int, int] = (0, 0),
    source_triangle_record_count: int = 0,
    policy: HullPolicy = HullPolicy(),
) -> RepBCorePrediction:
    """Predict a geometric hull core using source points only.

    Source IDs in the result remain GXM Vector-C identities. The algorithm
    enumerates triples of the ordered unique input points, groups supporting
    planes by their coplanar source-ID set, orders each polygon with a 2D hull,
    and derives a sorted undirected edge graph. This is a generic control
    algorithm; it does not claim native plane-thickness or ordering semantics.
    """
    policy.validate()
    order = tuple(source_point_order)
    if len(set(order)) != len(order):
        raise HullPredictionError("DUPLICATE_SOURCE_ID", "source point order contains duplicate IDs")
    if set(order) != set(source_points):
        raise HullPredictionError("SOURCE_ID_MISMATCH", "source point order and point map must have identical IDs")
    if len(order) < 4:
        raise HullPredictionError("INSUFFICIENT_OR_DUPLICATE_INPUT", "need at least four unique source point IDs")
    points: dict[int, Vec3] = {}
    for source_id, source_xyz in source_points.items():
        if len(source_xyz) != 3 or any(not math.isfinite(float(value)) for value in source_xyz):
            raise HullPredictionError("INVALID_SOURCE_POINT", f"Vector C[{source_id}] is not a finite float3")
        points[source_id] = gxm_to_demo_xyz(tuple(float(value) for value in source_xyz))
    exact_positions: dict[Vec3, int] = {}
    for source_id in order:
        previous = exact_positions.get(points[source_id])
        if previous is not None:
            raise HullPredictionError(
                "DUPLICATE_SOURCE_POSITION",
                f"Vector C[{previous}] and Vector C[{source_id}] have identical coordinates",
            )
        exact_positions[points[source_id]] = source_id

    # The arithmetic mean is inside the convex hull of finite source points.
    # The 8.4.1 native AABB-center orientation behavior is not assumed here.
    center = tuple(sum(point[axis] for point in points.values()) / len(points)
                   for axis in range(3))
    grouped_planes: dict[tuple[int, ...], dict] = {}
    trace: list[PlaneDecision] = []
    for combination_index, source_ids in enumerate(itertools.combinations(order, 3)):
        first, second, third = (points[source_id] for source_id in source_ids)
        cross = _cross(_sub(second, first), _sub(third, first))
        cross_magnitude = _magnitude(cross)
        if cross_magnitude <= policy.area_epsilon:
            trace.append(PlaneDecision(combination_index, source_ids, "DEGENERATE_TRIPLE",
                                       None, None, cross_magnitude))
            continue
        normal = tuple(value / cross_magnitude for value in cross)
        distance = _dot(normal, first)
        if _dot(normal, _sub(center, first)) > 0:
            normal = tuple(-value for value in normal)
            distance = -distance
        signed = {source_id: _dot(normal, point) - distance for source_id, point in points.items()}
        if max(signed.values()) > policy.support_tolerance:
            trace.append(PlaneDecision(combination_index, source_ids, "NOT_SUPPORTING",
                                       normal, distance, cross_magnitude))
            continue
        coplanar = tuple(source_id for source_id in order
                         if abs(signed[source_id]) <= policy.support_tolerance)
        if len(coplanar) < 3:
            trace.append(PlaneDecision(combination_index, source_ids, "INSUFFICIENT_COPLANAR_POINTS",
                                       normal, distance, cross_magnitude, coplanar))
            continue
        existing = grouped_planes.get(coplanar)
        if existing is None:
            face_index = len(grouped_planes)
            grouped_planes[coplanar] = {
                "normal": normal, "distance": distance,
                "first_triple": source_ids,
            }
            disposition = "INSERTED_SUPPORTING_PLANE"
        else:
            face_index = next(index for index, key in enumerate(grouped_planes) if key == coplanar)
            disposition = "DEDUPLICATED_BY_COPLANAR_SOURCE_SET"
        trace.append(PlaneDecision(combination_index, source_ids, disposition,
                                   normal, distance, cross_magnitude, coplanar, face_index))

    if len(grouped_planes) < 4:
        raise HullPredictionError("INSUFFICIENT_SUPPORTING_PLANES", "source geometry did not yield a 3D closed hull")

    polygon_faces = []
    for coplanar_ids, plane in grouped_planes.items():
        loop = _boundary_loop(coplanar_ids, points, plane["normal"], policy.projection_epsilon)
        polygon_faces.append(PolygonFacePrediction(loop, coplanar_ids, plane["normal"],
                                                   plane["distance"], plane["first_triple"]))
    vertex_ids = tuple(source_id for source_id in order
                       if any(source_id in face.source_c_indices for face in polygon_faces))
    vertex_set = set(vertex_ids)

    edge_faces: dict[Edge, list[int]] = {}
    directed_edges: dict[Edge, list[tuple[int, int]]] = {}
    for face_index, face in enumerate(polygon_faces):
        loop = face.source_c_indices
        if any(source_id not in vertex_set for source_id in loop):
            raise HullPredictionError("FACE_VERTEX_MISSING", "polygon references an unretained source point")
        for edge_index, first_id in enumerate(loop):
            second_id = loop[(edge_index + 1) % len(loop)]
            edge = tuple(sorted((first_id, second_id)))
            edge_faces.setdefault(edge, []).append(face_index)
            directed_edges.setdefault(edge, []).append((first_id, second_id))
    triangles = triangulate_polygon_faces(polygon_faces)

    edges = tuple(sorted(edge_faces))
    adjacency = []
    for edge in edges:
        incident = edge_faces[edge]
        if len(incident) != 2 or incident[0] == incident[1]:
            raise HullPredictionError("NON_MANIFOLD_EDGE", f"edge {edge} has {len(incident)} incident faces")
        directions = directed_edges[edge]
        if len(directions) != 2 or directions[0] != directions[1][::-1]:
            raise HullPredictionError("INCONSISTENT_FACE_ORIENTATION", f"edge {edge} is not oppositely traversed")
        adjacency.append((incident[0], incident[1]))
    if len(vertex_ids) - len(edges) + len(polygon_faces) != 2:
        raise HullPredictionError("EULER_INVARIANT_FAILED", "predicted shell does not satisfy V-E+F=2")

    return RepBCorePrediction(
        directive=directive,
        source_record_range=source_record_range,
        source_triangle_record_count=source_triangle_record_count,
        source_c_indices=tuple(sorted(source_points)),
        source_point_order=order,
        source_positions=tuple((source_id, points[source_id]) for source_id in order),
        vertex_source_c_indices=vertex_ids,
        vertices=tuple(points[source_id] for source_id in vertex_ids),
        polygon_faces=tuple(polygon_faces),
        triangles_source_c_indices=triangles,
        edges_source_c_indices=edges,
        edge_face_adjacency=tuple(adjacency),
        plane_trace=tuple(trace),
        policy=policy,
        validation=(),
    )


def build_rep_b_core_from_gxm_chull(
    gxm_data: bytes,
    sidecar_path: str | Path,
    directive: str,
    *,
    policy: HullPolicy = HullPolicy(),
) -> RepBCorePrediction:
    """Extract and predict one ``$chull`` using only its GXM and sidecar."""
    source = analyze_gxm_chull(gxm_data, sidecar_path, directive)
    first_occurrence = []
    for record in source["records"]:
        for source_id in record[4:7]:
            if source_id not in first_occurrence:
                first_occurrence.append(source_id)
    start, end = source["record_range_half_open"]
    return build_rep_b_core_from_source_points(
        source["source_c_points"], first_occurrence,
        directive=directive,
        source_record_range=(start, end),
        source_triangle_record_count=source["record_count"],
        policy=policy,
    )
