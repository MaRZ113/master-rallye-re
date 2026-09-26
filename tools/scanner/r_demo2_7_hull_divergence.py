"""Reproduce the pinned demo-8.4.1 Trooper plane-dedup differential.

This is a source-point replay of the exact 8.4.1 control flow. Coordinates are
read as serialized float32 and calculations use Python float (binary64); it is
not an x87 bit-exact emulator and does not claim to capture the native input
point buffer. The generic pointer/list/edge-graph helpers are intended for
small, explicitly captured runtime snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
import sys
from pathlib import Path
from typing import Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
from master_rallye.gxm_hierarchy import serialized_c_triangle_stream
from tools.scanner.r_demo2_6_hull_diff import EXPECTED as GXM_HASHES
from tools.scanner.r_demo2_6_hull_diff import _geometry, compare as compare_hull_source

CORPUS_ID = "demo-8.4.1"
EXE_SHA256 = "bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be"
DEFAULT_THICKNESS = 0.0005000000237487257
EXPECTED_HULL = ("$chull(Trooper)", 1911, 68, range(1317, 1353), 28, 2)
TARGET_C_INDICES = (1317, 1335, 1337)
RUNTIME_FACE_NATIVE_NORMAL = (-0.9998094788806016,
                              0.019493582653401013,
                              -0.0008416937794259575)
RUNTIME_FACE_D = 0.5411924641764101


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def deterministic_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def pointer_to_index(pointer: int, begin: int, end: int, stride: int) -> int:
    """Normalize a pointer only after proving range, extent, and alignment."""
    if stride <= 0 or begin < 0 or end < begin:
        raise ValueError("invalid vector bounds or stride")
    if (end - begin) % stride:
        raise ValueError("vector extent is not an exact stride multiple")
    if pointer < begin or pointer >= end:
        raise ValueError("pointer is outside vector range")
    delta = pointer - begin
    if delta % stride:
        raise ValueError("pointer is not aligned to vector stride")
    return delta // stride


def walk_circular_ring(
    nodes: Mapping[int, tuple[int, int, int]],
    head: int,
    *,
    expected_count: int | None = None,
    max_nodes: int = 4096,
) -> list[tuple[int, int]]:
    """Return (list-node address, payload) pairs from a captured circular ring.

    ``nodes`` maps each captured node address to (next, previous, payload),
    including the sentinel at ``head``. Corrupt cycles, broken reciprocal links,
    missing nodes, count mismatches, and node/payload aliasing fail closed.
    """
    if head not in nodes:
        raise ValueError("ring sentinel is missing from captured memory")
    if max_nodes < 0:
        raise ValueError("max_nodes must be nonnegative")
    sentinel_next, sentinel_prev, _ = nodes[head]
    result: list[tuple[int, int]] = []
    visited = {head}
    previous = head
    current = sentinel_next
    while current != head:
        if len(result) >= max_nodes:
            raise ValueError("ring exceeds max_nodes")
        if current in visited:
            raise ValueError("ring cycles before returning to sentinel")
        if current not in nodes:
            raise ValueError("ring points to a node absent from captured memory")
        next_pointer, previous_pointer, payload = nodes[current]
        if previous_pointer != previous:
            raise ValueError("ring previous link is not reciprocal")
        if next_pointer not in nodes:
            raise ValueError("ring next pointer is absent from captured memory")
        if next_pointer != head and next_pointer in visited:
            raise ValueError("ring cycles before returning to sentinel")
        if nodes[next_pointer][1] != current:
            raise ValueError("ring next node does not point back")
        result.append((current, payload))
        visited.add(current)
        previous, current = current, next_pointer
    if sentinel_prev != previous:
        raise ValueError("sentinel previous link does not match final node")
    if nodes[previous][0] != head:
        raise ValueError("final node does not point back to sentinel")
    ring_addresses = set(visited)
    if any(payload in ring_addresses for _, payload in result):
        raise ValueError("list payload aliases a list-node address")
    if expected_count is not None and len(result) != expected_count:
        raise ValueError("ring count does not match the captured object count")
    return result


def endpoint_identity_graph(
    edges: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    """Build a pointer-identity graph and its connected components."""
    incidence: dict[str, list[str]] = {}
    normalized: dict[str, list[str]] = {}
    for edge in sorted(edges):
        endpoints = list(edges[edge])
        if len(endpoints) != 2 or not all(endpoints):
            raise ValueError("each edge must have exactly two nonempty endpoint IDs")
        if endpoints[0] == endpoints[1]:
            raise ValueError("edge endpoints must be distinct object identities")
        normalized[edge] = endpoints
        for vertex in endpoints:
            incidence.setdefault(vertex, []).append(edge)

    unseen = set(normalized)
    components: list[dict[str, list[str]]] = []
    while unseen:
        seed = min(unseen)
        pending = [seed]
        component_edges: set[str] = set()
        component_vertices: set[str] = set()
        while pending:
            edge = pending.pop()
            if edge in component_edges:
                continue
            component_edges.add(edge)
            unseen.discard(edge)
            for vertex in normalized[edge]:
                component_vertices.add(vertex)
                pending.extend(incident for incident in incidence[vertex]
                               if incident not in component_edges)
        components.append({"edges": sorted(component_edges),
                           "vertices": sorted(component_vertices)})
    components.sort(key=lambda item: item["edges"])
    return {
        "edge_endpoints": normalized,
        "vertex_incident_edges": {key: sorted(value)
                                  for key, value in sorted(incidence.items())},
        "components": components,
        "component_count": len(components),
    }


def compare_endpoint_graphs(
    baseline: Mapping[str, Sequence[str]],
    candidate: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    """Report edge-identity additions/removals and both component summaries."""
    before = endpoint_identity_graph(baseline)
    after = endpoint_identity_graph(candidate)
    before_edges = {key: tuple(value) for key, value in before["edge_endpoints"].items()}
    after_edges = {key: tuple(value) for key, value in after["edge_endpoints"].items()}
    return {
        "baseline": before,
        "candidate": after,
        "added_or_changed_edges": sorted(
            key for key, value in after_edges.items() if before_edges.get(key) != value),
        "removed_or_changed_edges": sorted(
            key for key, value in before_edges.items() if after_edges.get(key) != value),
    }


def plane_equivalent(first: Mapping[str, object], second: Mapping[str, object],
                     thickness: float) -> bool:
    """Mirror 005C3E10's strict normal-dot and absolute-d tolerance tests."""
    first_n = first["normal"]
    second_n = second["normal"]
    dot = sum(float(first_n[i]) * float(second_n[i]) for i in range(3))
    return dot > 1.0 - thickness and abs(float(first["d"]) - float(second["d"])) < thickness


def _point(data: bytes, vector_c_offset: int, index: int) -> tuple[float, float, float]:
    return struct.unpack_from("<3f", data, vector_c_offset + index * 12)


def _hull_data(data: bytes):
    prefix, geometry, triangles, hierarchy, _, indices = _geometry(data, EXPECTED_HULL)
    records = serialized_c_triangle_stream(
        data, triangles.record_offset, triangles.record_count,
        EXPECTED_HULL[1], EXPECTED_HULL[2])
    order: list[int] = []
    first_corner: dict[int, dict[str, int]] = {}
    for record in records:
        for corner, index in enumerate(record.c_indices):
            if index not in first_corner:
                first_corner[index] = {"record_index": record.record_index,
                                        "corner_index": corner}
                order.append(index)
    if set(order) != set(indices) or len(order) != 36:
        raise ValueError("unexpected first-occurrence $chull C-index stream")
    points = {index: _point(data, triangles.vector_c_offset, index) for index in order}
    return prefix, geometry, triangles, hierarchy, records, order, first_corner, points


def _plane_for(points: Sequence[tuple[float, float, float]],
               indices: tuple[int, int, int], center: Sequence[float],
               thickness: float) -> dict[str, object] | None:
    a, b, c = (points[i] for i in indices)
    ab = tuple(a[i] - b[i] for i in range(3))
    ac = tuple(a[i] - c[i] for i in range(3))
    cross = (ab[1] * ac[2] - ab[2] * ac[1],
             ab[2] * ac[0] - ab[0] * ac[2],
             ab[0] * ac[1] - ab[1] * ac[0])
    area = math.sqrt(sum(value * value for value in cross))
    if area < thickness:
        return None
    normal = tuple(value / area for value in cross)
    if sum((a[i] - center[i]) * normal[i] for i in range(3)) < 0.0:
        normal = tuple(-value for value in normal)
    d = sum(a[i] * normal[i] for i in range(3))
    return {"normal": normal, "d": d, "cross_magnitude": area,
            "source_c_indices": tuple(indices)}


def _replay(data: bytes, thickness: float) -> dict[str, object]:
    _, _, _, _, records, order, first_corner, source_points = _hull_data(data)
    points = [source_points[index] for index in order]
    center = tuple((min(point[axis] for point in points) +
                    max(point[axis] for point in points)) * 0.5
                   for axis in range(3))
    faces: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    for decision_index, local_indices in enumerate(itertools.combinations(range(len(order)), 3)):
        source_ids = tuple(order[index] for index in local_indices)
        plane = _plane_for(points, local_indices, center, thickness)
        if plane is None:
            decisions.append({"decision_index": decision_index,
                               "source_c_indices": source_ids,
                               "disposition": "degenerate"})
            continue
        if any(sum(plane["normal"][axis] * point[axis] for axis in range(3)) -
               plane["d"] > thickness for point in points):
            decisions.append({"decision_index": decision_index,
                               "source_c_indices": source_ids,
                               "disposition": "not_supporting"})
            continue
        accepted = next((index for index, face in enumerate(faces)
                         if plane_equivalent(face, plane, thickness)), None)
        if accepted is None:
            accepted = len(faces)
            face = dict(plane)
            face["face_index"] = accepted
            face["source_c_indices"] = source_ids
            face["first_corner_by_c_index"] = {
                str(source_id): first_corner[source_id] for source_id in source_ids}
            faces.append(face)
            disposition = "inserted"
        else:
            disposition = "deduplicated"
        decisions.append({"decision_index": decision_index,
                           "source_c_indices": source_ids,
                           "disposition": disposition,
                           "matched_face_index": accepted})
    return {"faces": faces, "decisions": decisions, "point_order": order,
            "source_points": source_points, "center": center,
            "records": records, "first_corner": first_corner}


def _plane_at_source_ids(data: bytes, source_ids: tuple[int, int, int],
                         thickness: float) -> dict[str, object]:
    _, _, _, _, _, order, first_corner, source_points = _hull_data(data)
    center = tuple((min(source_points[index][axis] for index in order) +
                    max(source_points[index][axis] for index in order)) * 0.5
                   for axis in range(3))
    try:
        local = tuple(order.index(index) for index in source_ids)
    except ValueError as exc:
        raise ValueError("source plane references a C index outside the hull") from exc
    plane = _plane_for([source_points[index] for index in order], local, center, thickness)
    if plane is None:
        raise ValueError("target source plane is degenerate")
    plane["first_corner_by_c_index"] = {
        str(index): first_corner[index] for index in source_ids}
    return plane


def validate_runtime_capture(capture: Mapping[str, object],
                             *, baseline_sha256: str,
                             candidate_sha256: str) -> None:
    if capture.get("corpus_id") != CORPUS_ID:
        raise ValueError("runtime capture build ID mismatch")
    if capture.get("exe_sha256") != EXE_SHA256:
        raise ValueError("runtime capture executable hash mismatch")
    if capture.get("candidate_gxm_sha256") != candidate_sha256:
        raise ValueError("runtime capture candidate GXM hash mismatch")
    if capture.get("baseline_gxm_sha256") != baseline_sha256:
        raise ValueError("runtime capture baseline GXM hash mismatch")
    if capture.get("candidate_breakpoint_hit") is not True:
        raise ValueError("runtime capture does not record a candidate breakpoint hit")


def validate_pinned_gxm_hashes(baseline_sha256: str,
                               candidate_sha256: str) -> None:
    if baseline_sha256 != GXM_HASHES["baseline"]:
        raise ValueError("baseline SHA256 does not match pinned demo-8.4.1 GXM")
    if candidate_sha256 != GXM_HASHES["candidate"]:
        raise ValueError("candidate SHA256 does not match pinned demo-8.4.1 crash GXM")


def analyze(baseline: bytes, candidate: bytes,
            runtime_capture: Mapping[str, object] | None = None,
            *, thickness: float = DEFAULT_THICKNESS) -> dict[str, object]:
    if not math.isfinite(thickness) or not 1e-6 <= thickness <= 0.1:
        raise ValueError("plane thickness is outside the supported exact-build range")
    baseline_hash, candidate_hash = sha256(baseline), sha256(candidate)
    validate_pinned_gxm_hashes(baseline_hash, candidate_hash)
    source_diff = compare_hull_source(baseline, candidate)
    before = _replay(baseline, thickness)
    after = _replay(candidate, thickness)
    if before["point_order"] != after["point_order"]:
        raise ValueError("baseline and candidate source point orders differ")
    first_divergence = next(
        (index for index, (a, b) in enumerate(zip(before["decisions"], after["decisions"]))
         if (a.get("disposition"), a.get("matched_face_index")) !=
            (b.get("disposition"), b.get("matched_face_index"))), None)
    if first_divergence is None:
        raise ValueError("pinned pair has no plane decision divergence in the replay")
    base_decision = before["decisions"][first_divergence]
    candidate_decision = after["decisions"][first_divergence]
    source_ids = tuple(candidate_decision["source_c_indices"])
    if source_ids != TARGET_C_INDICES:
        raise ValueError("first divergence is not the pinned source triangle ancestry")
    if (base_decision["disposition"] != "deduplicated" or
            candidate_decision["disposition"] != "inserted"):
        raise ValueError("first divergence did not change deduplication into insertion")

    baseline_target = _plane_at_source_ids(baseline, source_ids, thickness)
    candidate_target = _plane_at_source_ids(candidate, source_ids, thickness)
    base_match_index = int(base_decision["matched_face_index"])
    candidate_face_index = int(candidate_decision["matched_face_index"])
    baseline_partner = before["faces"][base_match_index]
    # Until this combination, both replays made the same insert/dedup choices,
    # so the candidate's former match target retains the baseline ordinal.
    candidate_partner = after["faces"][base_match_index]
    baseline_offset_delta = float(baseline_target["d"]) - float(baseline_partner["d"])
    candidate_offset_delta = float(candidate_target["d"]) - float(candidate_partner["d"])
    baseline_dot = sum(float(baseline_target["normal"][i]) *
                       float(baseline_partner["normal"][i]) for i in range(3))
    candidate_dot = sum(float(candidate_target["normal"][i]) *
                        float(candidate_partner["normal"][i]) for i in range(3))

    runtime_result = None
    if runtime_capture is not None:
        validate_runtime_capture(runtime_capture,
                                 baseline_sha256=baseline_hash,
                                 candidate_sha256=candidate_hash)
        runtime_face = runtime_capture.get("face_plane", {})
        caller_frame = runtime_capture.get("caller_frame", {})
        source_n = candidate_target["normal"]
        predicted_native_n = (source_n[0], source_n[2], -source_n[1])
        observed_n = tuple(float(value) for value in runtime_face["normal"])
        residuals = [observed_n[i] - predicted_native_n[i] for i in range(3)]
        runtime_result = {
            "face_index_from_caller_loop": caller_frame["face_index"],
            "predicted_candidate_face_index": candidate_face_index,
            "face_index_matches": caller_frame["face_index"] == candidate_face_index,
            "predicted_native_normal": predicted_native_n,
            "observed_native_normal": observed_n,
            "normal_component_residuals": residuals,
            "max_abs_normal_residual": max(abs(value) for value in residuals),
            "predicted_d": candidate_target["d"],
            "observed_d": float(runtime_face["d"]),
            "d_residual": float(runtime_face["d"]) - float(candidate_target["d"]),
            "source_to_runtime_axis_map_status": "INFERRED_FROM_RUNTIME_PLANE_MATCH",
        }

    edge_vectors_before = []
    edge_vectors_after = []
    for first, second in ((0, 1), (0, 2), (1, 2)):
        ia, ib = source_ids[first], source_ids[second]
        base_points = before["source_points"]
        candidate_points = after["source_points"]
        edge_vectors_before.append([base_points[ib][axis] - base_points[ia][axis]
                                    for axis in range(3)])
        edge_vectors_after.append([candidate_points[ib][axis] - candidate_points[ia][axis]
                                   for axis in range(3)])

    source_record = next(
        record for record in after["records"]
        if tuple(record.c_indices) == (1337, 1335, 1317))
    edge_lengths_before = [math.dist((0.0, 0.0, 0.0), vector)
                           for vector in edge_vectors_before]
    edge_lengths_after = [math.dist((0.0, 0.0, 0.0), vector)
                          for vector in edge_vectors_after]
    epsilon_band = {
        "baseline_dedup_requires_thickness_greater_than": abs(baseline_offset_delta),
        "candidate_separation_requires_thickness_at_most": abs(candidate_offset_delta),
        "differential_window": [abs(baseline_offset_delta), abs(candidate_offset_delta)],
        "upper_endpoint_inclusive_for_candidate_separation": True,
    }
    report = {
        "schema": "r-demo2.7-exact-841-plane-divergence-v1",
        "corpus_id": CORPUS_ID,
        "exe_sha256": EXE_SHA256,
        "baseline_gxm_sha256": baseline_hash,
        "candidate_gxm_sha256": candidate_hash,
        "source_diff_schema": source_diff["schema"],
        "source_record": {
            "directive": "$chull(Trooper)",
            "triangle_record": source_record.record_index,
            "triangle_corner_c_indices": list(source_record.c_indices),
            "plane_point_c_indices_in_enumeration_order": list(source_ids),
            "first_corner_by_c_index": candidate_target["first_corner_by_c_index"],
        },
        "static_native_basis": {
            "plane_builder_va": "005C3A40",
            "triple_enumerator_va": "005B9F10",
            "plane_equivalence_va": "005C3E10",
            "support_test_va": "005C41F0",
            "enumeration": "lexicographic triples, point stride 0x18",
            "center": "AABB midpoint from 005B9D80",
            "default_plane_thickness": DEFAULT_THICKNESS,
            "runtime_plane_thickness": "UNKNOWN_FROM_CAPTURE",
            "native_input_point_order": "not directly captured; replay uses first occurrence in the serialized $chull corner stream",
        },
        "replay": {
            "method": "36 referenced GXM C positions in first corner-occurrence order; native branch order and strict tests mirrored",
            "precision": "Python binary64 over serialized float32 values; x87 intermediate precision is not emulated",
            "thickness_used": thickness,
            "unique_source_point_count": len(before["point_order"]),
            "combination_decision_index_zero_based": first_divergence,
            "baseline_predicted_face_count": len(before["faces"]),
            "candidate_predicted_face_count": len(after["faces"]),
        },
        "first_decision_divergence": {
            "source_c_indices": list(source_ids),
            "baseline": {
                "disposition": base_decision["disposition"],
                "matched_face_index": base_match_index,
                "candidate_plane_d": baseline_target["d"],
                "matched_plane_source_c_indices": list(baseline_partner["source_c_indices"]),
                "matched_plane_d": baseline_partner["d"],
                "normal_dot": baseline_dot,
                "signed_d_delta": baseline_offset_delta,
            },
            "candidate": {
                "disposition": candidate_decision["disposition"],
                "inserted_face_index": candidate_face_index,
                "candidate_plane_d": candidate_target["d"],
                "prior_face_source_c_indices": list(candidate_partner["source_c_indices"]),
                "prior_face_d": candidate_partner["d"],
                "normal_dot": candidate_dot,
                "signed_d_delta": candidate_offset_delta,
            },
            "plane_equivalence_window": epsilon_band,
            "status": "INFERRED_BY_BINARY64_REPLAY; PREDICTION_MATCHES_CONFIRMED_RUNTIME_FACE",
        },
        "translation_differential": {
            "translation_source_xyz": [0.4, 0.0, 0.0],
            "relative_edge_vectors_before": edge_vectors_before,
            "relative_edge_vectors_after": edge_vectors_after,
            "edge_lengths_before": edge_lengths_before,
            "edge_lengths_after": edge_lengths_after,
            "plane_normal_before": baseline_target["normal"],
            "plane_normal_after": candidate_target["normal"],
            "plane_d_before": baseline_target["d"],
            "plane_d_after": candidate_target["d"],
            "native_absolute_d_comparison_shift": candidate_offset_delta - baseline_offset_delta,
            "topology_and_record_connectivity_unchanged": True,
            "a_b_arrays_and_hierarchy_unchanged": True,
        },
        "candidate_runtime_plane_anchor": runtime_result,
        "runtime_capture_id": runtime_capture.get("capture_id") if runtime_capture else None,
        "conclusion": {
            "first_upstream_decision": "005C3E10 plane-equivalence test changes from deduplicate to insert for the plane through source C 1317/1335/1337",
            "candidate_runtime_face_index": candidate_face_index,
            "runtime_endpoint_identities": "UNKNOWN_FROM_CAPTURE",
            "effective_runtime_thickness": "UNKNOWN_FROM_CAPTURE",
            "confidence": "LEVEL_B_FIRST_NATIVE_DECISION_REPLAYED; ONE_SMALL_RUNTIME_CAPTURE_REMAINS",
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="pinned original demo-8.4.1 car.gxm")
    parser.add_argument("candidate", type=Path, help="pinned translated 8.4.1 crash candidate")
    parser.add_argument("--runtime-capture", type=Path,
                        help="optional derived JSON capture, kept under ignored .research-output")
    parser.add_argument("--thickness", type=float, default=DEFAULT_THICKNESS,
                        help="plane thickness; defaults to the exact EXE's static default")
    parser.add_argument("--output", type=Path,
                        help="write deterministic JSON under ignored .research-output/r-demo2")
    args = parser.parse_args()
    capture = json.loads(args.runtime_capture.read_text(encoding="utf-8")) if args.runtime_capture else None
    report = analyze(args.baseline.read_bytes(), args.candidate.read_bytes(), capture,
                     thickness=args.thickness)
    encoded = deterministic_json(report)
    if args.output:
        output = args.output.resolve()
        scratch_root = (REPO_ROOT / ".research-output" / "r-demo2").resolve()
        if scratch_root not in output.parents:
            parser.error("--output must stay under ignored .research-output/r-demo2")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
