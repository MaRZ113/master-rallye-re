"""Small, explicit geometry comparisons for same-build cooker oracles."""
from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence

Vec3 = tuple[float, float, float]
Triangle = tuple[int, int, int]


def gxm_to_demo_xyz(point: Vec3) -> Vec3:
    """Observed source-GXM to demo DX axis map: (x, y, z) -> (x, z, -y)."""
    return (point[0], point[2], -point[1])


def _cyclic_key(face: Sequence[int]) -> tuple[int, int, int]:
    if len(face) != 3:
        raise ValueError("triangle must have exactly three indices")
    a, b, c = face
    return min((a, b, c), (b, c, a), (c, a, b))


def _reverse_cyclic_key(face: Sequence[int]) -> tuple[int, int, int]:
    a, b, c = face
    return _cyclic_key((a, c, b))


def edge_loop_vertices(edges: Sequence[tuple[int, int]], edge_loop: Sequence[int]) -> tuple[int, ...]:
    """Resolve an ordered closed loop of edge indices to ordered vertex indices."""
    if len(edge_loop) < 3:
        raise ValueError("polygon edge loop must contain at least three edges")
    pairs = []
    for edge_index in edge_loop:
        if edge_index < 0 or edge_index >= len(edges):
            raise ValueError(f"edge loop index {edge_index} outside edge table")
        a, b = edges[edge_index]
        if a == b:
            raise ValueError("polygon loop contains a zero-length indexed edge")
        pairs.append((a, b))
    for reverse_first in (False, True):
        first = pairs[0][::-1] if reverse_first else pairs[0]
        vertices = [first[0], first[1]]
        for a, b in pairs[1:]:
            current = vertices[-1]
            if a == current:
                vertices.append(b)
            elif b == current:
                vertices.append(a)
            else:
                break
        else:
            if vertices[-1] == vertices[0]:
                return tuple(vertices[:-1])
    raise ValueError("indexed edges do not form an ordered closed polygon loop")


def exact_vertex_bijection(source: Mapping[int, Vec3], target: Sequence[Vec3]) -> dict:
    """Map target points to transformed source ids; exact first, unique nearest fallback.

    Returns an auditable row per target vertex. It fails closed on ambiguous nearest
    matches or reused source ids, while retaining exact-float match counts.
    """
    transformed = {index: gxm_to_demo_xyz(point) for index, point in source.items()}
    exact: dict[Vec3, list[int]] = defaultdict(list)
    for index, point in transformed.items():
        exact[point].append(index)
    rows = []
    used = set()
    for target_index, point in enumerate(target):
        candidates = exact.get(tuple(point), [])
        if len(candidates) == 1 and candidates[0] not in used:
            source_index = candidates[0]
            distance = 0.0
            exact_match = True
        else:
            ordered = sorted((math.dist(point, candidate), index)
                             for index, candidate in transformed.items())
            if not ordered:
                raise ValueError("source point set is empty")
            distance, source_index = ordered[0]
            if len(ordered) > 1 and abs(ordered[1][0] - distance) <= 1e-12:
                raise ValueError(f"ambiguous nearest source for target vertex {target_index}")
            exact_match = distance == 0.0
        if source_index in used:
            raise ValueError(f"source vertex {source_index} reused; mapping is not bijective")
        used.add(source_index)
        rows.append({"target_index": target_index, "source_c_index": source_index,
                     "distance": distance, "exact_float_match": exact_match})
    return {"rows": rows, "bijective": len(used) == len(target) == len(source),
            "source_count": len(source), "target_count": len(target),
            "all_source_points_used": len(used) == len(source),
            "exact_float_match_count": sum(row["exact_float_match"] for row in rows),
            "max_distance": max((row["distance"] for row in rows), default=0.0)}


def compare_triangle_topology(source_faces: Sequence[Triangle], target_faces: Sequence[Triangle],
                              target_to_source: Mapping[int, int]) -> dict:
    """Compare face membership and oriented cyclic order after vertex mapping."""
    source_by_set: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for index, face in enumerate(source_faces):
        source_by_set[tuple(sorted(face))].append(index)
    source_oriented = defaultdict(list)
    source_reversed = defaultdict(list)
    for index, face in enumerate(source_faces):
        source_oriented[_cyclic_key(face)].append(index)
        source_reversed[_reverse_cyclic_key(face)].append(index)
    rows = []
    set_matches = oriented_matches = reversed_matches = 0
    for target_index, face in enumerate(target_faces):
        mapped = tuple(target_to_source[index] for index in face)
        candidates = source_by_set.get(tuple(sorted(mapped)), [])
        oriented = source_oriented.get(_cyclic_key(mapped), [])
        reversed_ = source_reversed.get(_cyclic_key(mapped), [])
        set_matches += bool(candidates)
        oriented_matches += bool(oriented)
        reversed_matches += bool(reversed_)
        rows.append({"target_face_index": target_index, "mapped_source_c_indices": mapped,
                     "matching_source_record_indices": candidates,
                     "orientation": ("same" if oriented else "reversed" if reversed_ else "unmatched")})
    return {"source_face_count": len(source_faces), "target_face_count": len(target_faces),
            "target_faces_matching_source_unordered": set_matches,
            "target_faces_matching_source_oriented": oriented_matches,
            "target_faces_matching_source_reversed": reversed_matches,
            "rows": rows}


def rigid_translation_metrics(before: Mapping[int, Vec3], after: Mapping[int, Vec3],
                              tolerance: float = 2e-6) -> dict:
    """Validate that matching indexed points differ by one rigid translation."""
    if set(before) != set(after) or not before:
        raise ValueError("rigid translation requires the same nonempty indexed point set")
    deltas = [tuple(after[index][axis] - before[index][axis] for axis in range(3))
              for index in sorted(before)]
    mean = tuple(sum(delta[axis] for delta in deltas) / len(deltas) for axis in range(3))
    residuals = [math.dist(delta, mean) for delta in deltas]
    maximum = max(residuals, default=0.0)
    if maximum > tolerance:
        raise ValueError(f"point deltas are not a rigid translation: residual {maximum:g}")
    if math.dist(mean, (0.0, 0.0, 0.0)) <= tolerance:
        raise ValueError("candidate has no meaningful translation")
    return {"translation_xyz": mean, "maximum_delta_residual": maximum,
            "point_count": len(before), "rigid_within_tolerance": True}


def face_normal_metrics(points: Mapping[int, Vec3], face: Triangle,
                        normal_indices: Triangle, normals: Sequence[Vec3]) -> dict:
    """Compare three referenced source normals with the geometric face normal."""
    p0, p1, p2 = (gxm_to_demo_xyz(points[index]) for index in face)
    u = tuple(p1[i] - p0[i] for i in range(3))
    v = tuple(p2[i] - p0[i] for i in range(3))
    cross = (u[1] * v[2] - u[2] * v[1],
             u[2] * v[0] - u[0] * v[2],
             u[0] * v[1] - u[1] * v[0])
    magnitude = math.sqrt(sum(value * value for value in cross))
    if magnitude == 0.0:
        return {"degenerate": True}
    geometric = tuple(value / magnitude for value in cross)
    values = [gxm_to_demo_xyz(normals[index]) for index in normal_indices]
    normalized = []
    for normal in values:
        length = math.sqrt(sum(value * value for value in normal))
        normalized.append(tuple(value / length for value in normal) if length else (0.0, 0.0, 0.0))
    dots = [max(-1.0, min(1.0, sum(a * b for a, b in zip(geometric, normal))))
            for normal in normalized]
    angles = [math.degrees(math.acos(dot)) for dot in dots]
    spread = max((math.dist(a, b) for a in normalized for b in normalized), default=0.0)
    return {"degenerate": False, "geometric_normal_demo_xyz": geometric,
            "referenced_a_indices": list(normal_indices), "signed_dot_products": dots,
            "angles_degrees": angles, "max_pairwise_normal_distance": spread}
