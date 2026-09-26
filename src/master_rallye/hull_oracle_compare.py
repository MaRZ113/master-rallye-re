"""Post-prediction comparison of a source-only hull against parsed native DX."""
from __future__ import annotations

import math
from collections import Counter
from typing import Sequence

from .collision import ConvexHullRepresentation
from .collision_oracle import edge_loop_vertices
from .native_hull_reconstruction import RepBCorePrediction


def _sub3(first: Sequence[float], second: Sequence[float]) -> tuple[float, float, float]:
    return tuple(first[axis] - second[axis] for axis in range(3))


def _dot3(first: Sequence[float], second: Sequence[float]) -> float:
    return sum(first[axis] * second[axis] for axis in range(3))


def _cross3(first: Sequence[float], second: Sequence[float]) -> tuple[float, float, float]:
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def _cycle_key(values: Sequence[int], *, reverse: bool = False) -> tuple[int, ...]:
    sequence = tuple(reversed(values)) if reverse else tuple(values)
    if not sequence:
        return ()
    return min(sequence[index:] + sequence[:index] for index in range(len(sequence)))


def _triangle_key(values: Sequence[int]) -> tuple[int, int, int]:
    if len(values) != 3:
        raise ValueError("native Rep-B triangle does not have three vertices")
    return tuple(sorted(values))


def analyze_native_rep_b_loop_fan(native: ConvexHullRepresentation) -> dict:
    """Test fan triangulation anchored at each stored native polygon-loop vertex.

    This is an oracle-only diagnostic: it consumes parsed native loops and
    triangles and must not be called by the source-only builder.
    """
    loops = [edge_loop_vertices(native.edges, loop) for loop in native.face_loop_indices]
    native_triangles = [tuple(triangle) for triangle in native.geometry_a.triangles]
    by_face = []
    for face_index, loop in enumerate(loops):
        face_vertex_set = set(loop)
        actual = Counter(_triangle_key(triangle) for triangle in native_triangles
                         if set(triangle).issubset(face_vertex_set))
        anchor_results = {}
        for anchor_index in (0, 1):
            anchor = loop[anchor_index]
            around = [loop[(anchor_index + offset) % len(loop)]
                      for offset in range(1, len(loop))]
            fan = Counter(_triangle_key((anchor, around[index], around[index + 1]))
                          for index in range(len(around) - 1))
            anchor_results[f"loop_vertex_{anchor_index}"] = fan == actual
        by_face.append({"face_index": face_index, "loop_vertex_count": len(loop),
                        "native_triangle_count": sum(actual.values()),
                        "fan_from_loop_vertex_0_matches": anchor_results["loop_vertex_0"],
                        "fan_from_loop_vertex_1_matches": anchor_results["loop_vertex_1"]})
    return {
        "evidence_scope": "ORACLE_ONLY_STORED_NATIVE_LOOP_AND_TRIANGLE_COMPARISON",
        "face_count": len(loops),
        "fan_from_loop_vertex_0_match_count": sum(
            row["fan_from_loop_vertex_0_matches"] for row in by_face),
        "fan_from_loop_vertex_1_match_count": sum(
            row["fan_from_loop_vertex_1_matches"] for row in by_face),
        "fan_from_loop_vertex_0_matches_all_faces": all(
            row["fan_from_loop_vertex_0_matches"] for row in by_face),
        "fan_from_loop_vertex_1_matches_all_faces": all(
            row["fan_from_loop_vertex_1_matches"] for row in by_face),
        "per_face": by_face,
    }


def analyze_native_rep_b_loop_order_hypotheses(
    prediction: RepBCorePrediction,
    native: ConvexHullRepresentation,
    *,
    tolerance: float = 1e-5,
) -> dict:
    """Test source-order and first-plane-triple hypotheses against native loops."""
    native_to_source, vertex_rows = _map_native_vertices(prediction,
                                                         native.geometry_a.vertices,
                                                         tolerance)
    native_loops = []
    for edge_loop in native.face_loop_indices:
        vertex_loop = edge_loop_vertices(native.edges, edge_loop)
        native_loops.append(tuple(native_to_source[index] for index in vertex_loop))
    native_by_set = {frozenset(loop): (index, loop) for index, loop in enumerate(native_loops)}
    source_positions = dict(prediction.source_positions)
    order_rank = {source_id: index for index, source_id in enumerate(prediction.source_point_order)}
    interior = tuple(sum(point[axis] for point in source_positions.values()) / len(source_positions)
                     for axis in range(3))
    rows = []
    for predicted_index, face in enumerate(prediction.polygon_faces):
        matched = native_by_set.get(frozenset(face.source_c_indices))
        if matched is None:
            rows.append({"predicted_face_index": predicted_index, "status": "NO_NATIVE_FACE"})
            continue
        native_index, native_loop = matched
        earliest = min(face.source_c_indices, key=order_rank.__getitem__)
        triple = face.first_supporting_triple
        first, second, third = (source_positions[source_id] for source_id in triple)
        raw_normal = _cross3(_sub3(second, first), _sub3(third, first))
        raw_points_outward = _dot3(raw_normal, _sub3(interior, first)) < 0
        predicted_loop = face.source_c_indices
        same = _cycle_key(native_loop) == _cycle_key(predicted_loop)
        reversed_loop = _cycle_key(native_loop) == _cycle_key(predicted_loop, reverse=True)
        rows.append({
            "predicted_face_index": predicted_index,
            "native_face_index": native_index,
            "native_loop_start_source_c_index": native_loop[0],
            "first_occurrence_source_c_index": earliest,
            "native_start_matches_first_occurrence": native_loop[0] == earliest,
            "first_supporting_triple": list(triple),
            "native_start_matches_first_supporting_triple_positions": [
                native_loop[0] == source_id for source_id in triple],
            "native_loop_matches_outward_cycle_up_to_rotation": same,
            "native_loop_is_reversed_outward_cycle_up_to_rotation": reversed_loop,
            "first_supporting_triple_normal_points_outward": raw_points_outward,
            "native_winding_matches_first_supporting_triple_normal": (
                same if raw_points_outward else reversed_loop),
        })
    valid_rows = [row for row in rows if row.get("status") != "NO_NATIVE_FACE"]
    return {
        "evidence_scope": "ORACLE_ONLY_HYPOTHESIS_CHECK_AFTER_SOURCE_PREDICTION",
        "matched_face_count": len(valid_rows),
        "native_start_matches_first_occurrence_count": sum(
            row["native_start_matches_first_occurrence"] for row in valid_rows),
        "native_winding_matches_first_supporting_triple_count": sum(
            row["native_winding_matches_first_supporting_triple_normal"] for row in valid_rows),
        "native_face_order_matches_prediction": [row["native_face_index"] for row in valid_rows]
        == list(range(len(valid_rows))),
        "vertex_mapping_failures": [row for row in vertex_rows if row["status"] != "MATCH"],
        "per_face": rows,
    }


def _map_native_vertices(prediction: RepBCorePrediction,
                         native_vertices: Sequence[Sequence[float]],
                         tolerance: float) -> tuple[dict[int, int], list[dict]]:
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("mapping tolerance must be finite and nonnegative")
    predicted = {source_id: point for source_id, point in
                 zip(prediction.vertex_source_c_indices, prediction.vertices)}
    mapping: dict[int, int] = {}
    rows = []
    used_source_ids = set()
    for native_index, native_point in enumerate(native_vertices):
        ranked = sorted((math.dist(tuple(native_point), point), source_id)
                        for source_id, point in predicted.items())
        if not ranked or ranked[0][0] > tolerance:
            rows.append({"native_vertex_index": native_index, "status": "NO_MATCH",
                         "nearest_source_c_index": ranked[0][1] if ranked else None,
                         "distance": ranked[0][0] if ranked else None})
            continue
        if len(ranked) > 1 and abs(ranked[1][0] - ranked[0][0]) <= 1e-12:
            rows.append({"native_vertex_index": native_index, "status": "AMBIGUOUS_MATCH",
                         "source_c_indices": [ranked[0][1], ranked[1][1]],
                         "distances": [ranked[0][0], ranked[1][0]]})
            continue
        distance, source_id = ranked[0]
        if source_id in used_source_ids:
            rows.append({"native_vertex_index": native_index, "status": "DUPLICATE_SOURCE_MATCH",
                         "source_c_index": source_id, "distance": distance})
            continue
        mapping[native_index] = source_id
        used_source_ids.add(source_id)
        rows.append({"native_vertex_index": native_index, "status": "MATCH",
                     "source_c_index": source_id, "distance": distance})
    return mapping, rows


def compare_prediction_to_native_rep_b(
    prediction: RepBCorePrediction,
    native: ConvexHullRepresentation,
    *,
    tolerance: float = 1e-5,
) -> dict:
    """Compare a completed source-only prediction to native data afterward.

    This function is deliberately separate from the builder. Native geometry
    is used only here, as a comparison oracle.
    """
    native_geometry = native.geometry_a
    native_to_source, vertex_rows = _map_native_vertices(prediction,
                                                         native_geometry.vertices,
                                                         tolerance)
    predicted_vertex_set = set(prediction.vertex_source_c_indices)
    native_vertex_set = set(native_to_source.values())

    predicted_face_loops = [face.source_c_indices for face in prediction.polygon_faces]
    native_face_loops = []
    unresolved_face_loops = []
    for face_index, edge_loop in enumerate(native.face_loop_indices):
        try:
            native_vertices = edge_loop_vertices(native.edges, edge_loop)
            native_face_loops.append(tuple(native_to_source[index] for index in native_vertices))
        except (ValueError, KeyError) as exc:
            unresolved_face_loops.append({"face_index": face_index, "reason": str(exc)})

    predicted_face_sets = Counter(frozenset(loop) for loop in predicted_face_loops)
    native_face_sets = Counter(frozenset(loop) for loop in native_face_loops)
    exact_face_set_match = predicted_face_sets == native_face_sets and not unresolved_face_loops
    predicted_face_cycles = Counter(_cycle_key(loop) for loop in predicted_face_loops)
    native_face_cycles = Counter(_cycle_key(loop) for loop in native_face_loops)
    same_oriented_cycle_match = predicted_face_cycles == native_face_cycles and not unresolved_face_loops
    predicted_unoriented_cycles = Counter(
        min(_cycle_key(loop), _cycle_key(loop, reverse=True)) for loop in predicted_face_loops)
    native_unoriented_cycles = Counter(
        min(_cycle_key(loop), _cycle_key(loop, reverse=True)) for loop in native_face_loops)
    same_cycle_up_to_winding = (predicted_unoriented_cycles == native_unoriented_cycles
                                and not unresolved_face_loops)
    native_faces_by_set = {frozenset(loop): index for index, loop in enumerate(native_face_loops)}
    ordered_cycle_rows = []
    ordered_cycle_counts = {"SAME_ORIENTATION_UP_TO_ROTATION": 0,
                            "REVERSED_UP_TO_ROTATION": 0,
                            "ORDER_DIFFERENT": 0,
                            "MISSING_NATIVE_FACE": 0}
    for predicted_index, predicted_loop in enumerate(predicted_face_loops):
        native_index = native_faces_by_set.get(frozenset(predicted_loop))
        if native_index is None:
            classification = "MISSING_NATIVE_FACE"
        else:
            native_loop = native_face_loops[native_index]
            if _cycle_key(native_loop) == _cycle_key(predicted_loop):
                classification = "SAME_ORIENTATION_UP_TO_ROTATION"
            elif _cycle_key(native_loop) == _cycle_key(predicted_loop, reverse=True):
                classification = "REVERSED_UP_TO_ROTATION"
            else:
                classification = "ORDER_DIFFERENT"
        ordered_cycle_counts[classification] += 1
        ordered_cycle_rows.append({"predicted_face_index": predicted_index,
                                   "native_face_index": native_index,
                                   "classification": classification})

    predicted_edges = Counter(tuple(sorted(edge)) for edge in prediction.edges_source_c_indices)
    native_edges = Counter(tuple(sorted((native_to_source[first], native_to_source[second])))
                           for first, second in native.edges
                           if first in native_to_source and second in native_to_source)
    exact_edge_set_match = predicted_edges == native_edges

    native_face_index: dict[frozenset[int], int] = {}
    if exact_face_set_match:
        native_face_index = {frozenset(loop): index for index, loop in enumerate(native_face_loops)}
    predicted_face_index = {frozenset(loop): index for index, loop in enumerate(predicted_face_loops)}
    predicted_adjacency = Counter()
    for edge, face_pair in zip(prediction.edges_source_c_indices,
                               prediction.edge_face_adjacency):
        predicted_adjacency[(tuple(sorted(edge)), tuple(sorted(face_pair)))] += 1
    native_adjacency = Counter()
    if native_face_index:
        for edge, face_pair in zip(native.edges, native.edge_face_adjacency):
            if edge[0] not in native_to_source or edge[1] not in native_to_source:
                continue
            first_face, second_face = face_pair
            if not (0 <= first_face < len(native_face_loops)
                    and 0 <= second_face < len(native_face_loops)):
                continue
            first_signature = frozenset(native_face_loops[first_face])
            second_signature = frozenset(native_face_loops[second_face])
            if first_signature not in predicted_face_index or second_signature not in predicted_face_index:
                continue
            pair = tuple(sorted((predicted_face_index[first_signature],
                                 predicted_face_index[second_signature])))
            mapped_edge = tuple(sorted((native_to_source[edge[0]], native_to_source[edge[1]])))
            native_adjacency[(mapped_edge, pair)] += 1
    exact_adjacency_match = native_adjacency == predicted_adjacency

    predicted_triangles = Counter(_triangle_key(triangle)
                                  for triangle in prediction.triangles_source_c_indices)
    native_mapped_triangles = [tuple(native_to_source[index] for index in triangle)
                               for triangle in native_geometry.triangles
                               if all(index in native_to_source for index in triangle)]
    native_triangles = Counter(_triangle_key(triangle) for triangle in native_mapped_triangles)
    exact_triangle_partition_match = predicted_triangles == native_triangles
    predicted_only_triangles = sorted(predicted_triangles - native_triangles)
    native_only_triangles = sorted(native_triangles - predicted_triangles)
    predicted_oriented_triangles = Counter(_cycle_key(triangle)
                                           for triangle in prediction.triangles_source_c_indices)
    native_oriented_triangles = Counter(_cycle_key(triangle) for triangle in native_mapped_triangles)
    predicted_unoriented_triangles = Counter(
        min(_cycle_key(triangle), _cycle_key(triangle, reverse=True))
        for triangle in prediction.triangles_source_c_indices)
    native_unoriented_triangles = Counter(
        min(_cycle_key(triangle), _cycle_key(triangle, reverse=True))
        for triangle in native_mapped_triangles)
    same_triangle_set_and_winding = predicted_oriented_triangles == native_oriented_triangles
    same_triangle_set_ignoring_winding = predicted_unoriented_triangles == native_unoriented_triangles
    if same_triangle_set_and_winding:
        triangulation_classification = "EXACT_TRIANGLE_SET"
    elif same_triangle_set_ignoring_winding:
        triangulation_classification = "SAME_GEOMETRIC_TRIANGULATION_DIFFERENT_WINDING"
    elif exact_face_set_match:
        triangulation_classification = "SAME_POLYGON_DIFFERENT_TRIANGULATION"
    else:
        triangulation_classification = "TOPOLOGY_DIFFERENT"

    native_order_source_ids = [native_to_source[index] for index in range(len(native_geometry.vertices))
                               if index in native_to_source]
    native_face_order = [frozenset(loop) for loop in native_face_loops]
    predicted_face_order = [frozenset(loop) for loop in predicted_face_loops]
    native_edge_order = [tuple(sorted((native_to_source[first], native_to_source[second])))
                         for first, second in native.edges
                         if first in native_to_source and second in native_to_source]

    return {
        "status": ("FULL_TRIANGULATED_CORE_MATCH" if exact_face_set_match
                   and exact_edge_set_match and exact_adjacency_match and exact_triangle_partition_match
                   else "POLYGON_SHELL_MATCH" if exact_face_set_match and exact_edge_set_match
                   and exact_adjacency_match else "CORE_DIFFERENCE"),
        "native_equivalence": "COMPARISON_ONLY_AFTER_SOURCE_PREDICTION",
        "tolerance": tolerance,
        "vertex_membership": {
            "native_vertex_count": native_geometry.vertex_count,
            "predicted_vertex_count": len(predicted_vertex_set),
            "matched_count": len(native_to_source),
            "exact_source_id_set_match": native_vertex_set == predicted_vertex_set,
            "missing_source_c_indices": sorted(predicted_vertex_set - native_vertex_set),
            "extra_source_c_indices": sorted(native_vertex_set - predicted_vertex_set),
            "mapping_rows": vertex_rows,
            "max_position_error": max((row["distance"] for row in vertex_rows
                                       if row["status"] == "MATCH"), default=None),
        },
        "polygon_faces": {
            "predicted_face_count": len(predicted_face_loops),
            "native_face_count": len(native_face_loops),
            "unresolved_native_faces": unresolved_face_loops,
            "same_per_face_vertex_sets": exact_face_set_match,
            "same_ordered_cycles_up_to_rotation": same_oriented_cycle_match,
            "same_cycles_up_to_rotation_and_winding": same_cycle_up_to_winding,
            "ordered_cycle_classification_counts": ordered_cycle_counts,
            "ordered_cycle_rows": ordered_cycle_rows,
            "predicted_source_loops": [list(loop) for loop in predicted_face_loops],
            "native_mapped_source_loops": [list(loop) for loop in native_face_loops],
        },
        "edges": {
            "predicted_count": len(predicted_edges),
            "native_count": len(native_edges),
            "same_undirected_edge_set": exact_edge_set_match,
        },
        "edge_face_adjacency": {
            "same_after_face_identity_mapping": exact_adjacency_match,
        },
        "triangulation": {
            "classification": triangulation_classification,
            "predicted_triangle_count": len(predicted_triangles),
            "native_triangle_count": native_geometry.triangle_count,
            "same_unoriented_triangle_partition": exact_triangle_partition_match,
            "same_triangle_set_and_winding": same_triangle_set_and_winding,
            "same_triangle_set_ignoring_winding": same_triangle_set_ignoring_winding,
            "predicted_only_unoriented_triangles": [list(item) for item in predicted_only_triangles],
            "native_only_unoriented_triangles": [list(item) for item in native_only_triangles],
            "predicted_source_triangles": [list(item) for item in prediction.triangles_source_c_indices],
            "native_mapped_source_triangles": [
                [native_to_source[index] for index in triangle]
                for triangle in native_geometry.triangles
                if all(index in native_to_source for index in triangle)
            ],
        },
        "native_ordering": {
            "vertex_order_matches_prediction": tuple(native_order_source_ids)
            == prediction.vertex_source_c_indices,
            "native_vertex_order_as_source_ids": native_order_source_ids,
            "predicted_vertex_order_as_source_ids": list(prediction.vertex_source_c_indices),
            "face_order_matches_prediction": native_face_order == predicted_face_order,
            "native_edge_order_as_source_ids": [list(edge) for edge in native_edge_order],
            "predicted_edge_order_as_source_ids": [list(edge) for edge in prediction.edges_source_c_indices],
            "edge_order_matches_prediction": native_edge_order
            == list(prediction.edges_source_c_indices),
            "triangle_list_order_and_winding_match_prediction": native_mapped_triangles
            == list(prediction.triangles_source_c_indices),
        },
    }
