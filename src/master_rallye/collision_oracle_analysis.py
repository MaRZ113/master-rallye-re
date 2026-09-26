"""Conservative reusable analyses for demo tag-101 cooker comparisons.

This module distinguishes established connectivity from auxiliary face-list data.
It does not assign meaning to secondary descriptor integers.
"""
from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from .collision import ConvexHullRepresentation
from .collision_oracle import edge_loop_vertices
from .bounds import compute_bounds1339
from .gxm_chull import analyze_gxm_chull


def compare_secondary_descriptors(first_faces, second_faces) -> dict:
    """Compare secondary tuples without treating their order as topology.

    Exact tuple order and per-face multisets are both preserved in the report.
    Their semantics remain unresolved regardless of equality.
    """
    changed_faces = []
    permutation_faces = []
    multisets_equal = len(first_faces) == len(second_faces)
    for index in range(max(len(first_faces), len(second_faces))):
        first = tuple(first_faces[index].secondary_indices) if index < len(first_faces) else None
        second = tuple(second_faces[index].secondary_indices) if index < len(second_faces) else None
        same_multiset = first is not None and second is not None and Counter(first) == Counter(second)
        if not same_multiset:
            multisets_equal = False
        if first != second:
            row = {"face_index": index, "first": list(first) if first is not None else None,
                   "second": list(second) if second is not None else None,
                   "per_face_multiset_equal": same_multiset}
            changed_faces.append(row)
            if same_multiset:
                permutation_faces.append(index)
    exact_equal = len(first_faces) == len(second_faces) and not changed_faces
    return {
        "classification": ("AUXILIARY_SECONDARY_DESCRIPTORS_EQUAL" if exact_equal
                           else "AUXILIARY_SECONDARY_DESCRIPTORS_DIFFER"),
        "semantics": "UNRESOLVED",
        "exact_tuples_equal": exact_equal,
        "per_face_multisets_equal": multisets_equal,
        "changed_face_count": len(changed_faces),
        "pure_permutation_face_indices": permutation_faces,
        "changed_faces": changed_faces,
    }


def compare_core_topology(first: ConvexHullRepresentation,
                          second: ConvexHullRepresentation) -> dict:
    """Compare only parser-established primary connectivity fields."""
    first_primary = tuple(face.primary_indices for face in first.face_descriptors)
    second_primary = tuple(face.primary_indices for face in second.face_descriptors)
    checks = {
        "vertex_count_equal": first.geometry_a.vertex_count == second.geometry_a.vertex_count,
        "triangle_count_equal": first.geometry_a.triangle_count == second.geometry_a.triangle_count,
        "triangle_indices_equal": first.geometry_a.triangles == second.geometry_a.triangles,
        "referenced_vertex_indices_equal": first.referenced_vertex_indices == second.referenced_vertex_indices,
        "edges_equal": first.edges == second.edges,
        "primary_descriptors_equal": first_primary == second_primary,
        "edge_face_adjacency_equal": first.edge_face_adjacency == second.edge_face_adjacency,
        "face_loops_equal": first.face_loop_indices == second.face_loop_indices,
    }
    return {"classification": "CORE_TOPOLOGY_EQUAL" if all(checks.values())
            else "CORE_TOPOLOGY_DIFFERENT", "checks": checks}


def map_gxm_chull_to_rep_b(source_points, target_vertices,
                           retained_source_indices: Sequence[int], *,
                           tolerance: float = 1e-5) -> dict:
    """Map supplied retained GXM C points to target Rep-B vertices by geometry.

    The caller must provide the tested retained source index set; this function
    does not claim to reproduce the native hull-selection algorithm.
    """
    from .collision_oracle import exact_vertex_bijection

    retained = {index: source_points[index] for index in retained_source_indices}
    mapping = exact_vertex_bijection(retained, target_vertices, tolerance=tolerance)
    return {"mapping": mapping,
            "target_to_source": {row["target_index"]: row["source_c_index"]
                                 for row in mapping["rows"]},
            "source_to_target": {row["source_c_index"]: row
                                 for row in mapping["rows"]},
            "selection_semantics": "caller-supplied; native hull selection is not inferred"}


def polygon_area(vertices: Sequence[Sequence[float]], indices: Sequence[int]) -> float:
    """Area of a planar polygon from an ordered vertex loop."""
    if len(indices) < 3:
        return 0.0
    origin = vertices[indices[0]]
    cross_sum = [0.0, 0.0, 0.0]
    for index in range(1, len(indices) - 1):
        left, right = vertices[indices[index]], vertices[indices[index + 1]]
        a = tuple(left[axis] - origin[axis] for axis in range(3))
        b = tuple(right[axis] - origin[axis] for axis in range(3))
        cross_sum[0] += a[1] * b[2] - a[2] * b[1]
        cross_sum[1] += a[2] * b[0] - a[0] * b[2]
        cross_sum[2] += a[0] * b[1] - a[1] * b[0]
    return math.sqrt(sum(component * component for component in cross_sum)) * 0.5


def analyze_face_scalars(rep: ConvexHullRepresentation) -> dict:
    """Compare stored face scalars to areas using parsed edge-loop connectivity."""
    rows = []
    for index, (edges, scalar) in enumerate(zip(rep.face_loop_indices, rep.face_scalars)):
        vertices = edge_loop_vertices(rep.edges, edges)
        area = polygon_area(rep.geometry_a.vertices, vertices)
        rows.append({"face_index": index, "vertex_loop": list(vertices),
                     "stored_scalar": scalar, "computed_polygon_area": area,
                     "absolute_error": abs(scalar - area)})
    errors = [row["absolute_error"] for row in rows]
    return {"face_count": len(rows), "rows": rows,
            "max_abs_area_error": max(errors, default=0.0),
            "mean_abs_area_error": sum(errors) / len(errors) if errors else 0.0}


def aabb_corners(vertices: Sequence[Sequence[float]]) -> tuple[tuple[float, float, float], ...]:
    if not vertices:
        raise ValueError("AABB requires at least one point")
    minimum = tuple(min(point[axis] for point in vertices) for axis in range(3))
    maximum = tuple(max(point[axis] for point in vertices) for axis in range(3))
    return tuple(tuple(maximum[axis] if mask & (1 << axis) else minimum[axis]
                       for axis in range(3)) for mask in range(8))


def analyze_rep_a_aabb(rep_a_vertices, rep_b_vertices) -> dict:
    """Test Rep A against the eight corners generated from Rep B's AABB."""
    expected = aabb_corners(rep_b_vertices)
    unmatched = list(range(len(rep_a_vertices)))
    matches = []
    for expected_index, point in enumerate(expected):
        if not unmatched:
            matches.append({"expected_corner_index": expected_index, "matched_rep_a_index": None,
                            "distance": None})
            continue
        chosen = min(unmatched, key=lambda index: math.dist(point, rep_a_vertices[index]))
        distance = math.dist(point, rep_a_vertices[chosen])
        unmatched.remove(chosen)
        matches.append({"expected_corner_index": expected_index,
                        "matched_rep_a_index": chosen, "distance": distance})
    errors = [row["distance"] for row in matches if row["distance"] is not None]
    return {"rep_a_vertex_count": len(rep_a_vertices), "expected_corner_count": 8,
            "all_eight_matched": len(errors) == 8 and not unmatched,
            "maximum_corner_error": max(errors, default=None), "matches": matches,
            "unmatched_rep_a_indices": unmatched}


def analyze_tag101_rep_a(rep_a: ConvexHullRepresentation,
                         rep_b: ConvexHullRepresentation) -> dict:
    box = analyze_rep_a_aabb(rep_a.geometry_a.vertices, rep_b.geometry_a.vertices)
    return {"aabb_corners": box,
            "vertex_count": rep_a.geometry_a.vertex_count,
            "triangle_count": rep_a.geometry_a.triangle_count,
            "vertices_equal_rep_b_aabb_corners": box["all_eight_matched"],
            "triangles": [list(face) for face in rep_a.geometry_a.triangles]}


def recompute_marker1339(render_positions, rep_b_vertices, *, offset: int = 0):
    """Apply the corpus-supported render-plus-Rep-B point-set bounds policy."""
    return compute_bounds1339(tuple(render_positions) + tuple(rep_b_vertices), offset=offset)


def compare_collision_oracle(first_dx: bytes, second_dx: bytes, *,
                             tolerance: float = 1e-5) -> dict:
    """Reusable parser-level DX comparison with separate core/auxiliary states."""
    from .demo_dx import compare_demo_dx, inspect_demo_dx

    first, second = inspect_demo_dx(first_dx, "oracle first"), inspect_demo_dx(second_dx, "oracle second")
    parsed = compare_demo_dx(first_dx, second_dx, float_tolerance=tolerance)
    hull_a, hull_b = first.collision.convex_hull, second.collision.convex_hull
    if hull_a is None or hull_b is None:
        return {"parser_verdict": parsed["verdict"],
                "core_topology": "NOT_PARSED",
                "secondary_descriptors": "NOT_PARSED"}
    reps = {}
    for name in ("representation_a", "representation_b"):
        a, b = getattr(hull_a, name), getattr(hull_b, name)
        reps[name] = {"core_topology": compare_core_topology(a, b),
                      "secondary_descriptors": compare_secondary_descriptors(
                          a.face_descriptors, b.face_descriptors)}
    return {"parser_verdict": parsed["verdict"], "representations": reps,
            "core_topology": ("CORE_TOPOLOGY_EQUAL" if all(
                item["core_topology"]["classification"] == "CORE_TOPOLOGY_EQUAL"
                for item in reps.values()) else "CORE_TOPOLOGY_DIFFERENT"),
            "secondary_descriptor_semantics": "UNRESOLVED"}
