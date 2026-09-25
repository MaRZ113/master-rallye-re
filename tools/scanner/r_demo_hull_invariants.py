"""Offline structural validator for a proposed flat `$chull` rigid translation.

This checks the serialized sidecar range and GXM triangle records. It cannot
validate loader hierarchy transforms or guarantee original-cooker success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from master_rallye.collision_oracle import rigid_translation_metrics
from master_rallye.gxm import (parse_gxm_geometry_prefix_bytes,
                                parse_gxm_prefix_bytes,
                                parse_gxm_triangle_prefix_bytes)
from master_rallye.sidecar import parse_sidecar


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _triangle_normal_area(points, triangle):
    p0, p1, p2 = (points[index] for index in triangle)
    u = tuple(p1[axis] - p0[axis] for axis in range(3))
    v = tuple(p2[axis] - p0[axis] for axis in range(3))
    cross = _cross(u, v)
    length = math.sqrt(sum(value * value for value in cross))
    return ((tuple(value / length for value in cross) if length else None), length * 0.5)


def validate_pair(baseline: bytes, candidate: bytes, sidecar_path: Path,
                  directive: str, translation_tolerance: float = 2e-6) -> dict:
    bp = parse_gxm_prefix_bytes(baseline, "baseline GXM")
    bg = parse_gxm_geometry_prefix_bytes(baseline, bp)
    bt = parse_gxm_triangle_prefix_bytes(baseline, bp, bg)
    cp = parse_gxm_prefix_bytes(candidate, "candidate GXM")
    cg = parse_gxm_geometry_prefix_bytes(candidate, cp)
    ct = parse_gxm_triangle_prefix_bytes(candidate, cp, cg)
    if (len(baseline) != len(candidate) or bp.header_words != cp.header_words
            or bt.record_count != ct.record_count or bt.vector_c_count != ct.vector_c_count
            or bg.vector_a_count != cg.vector_a_count or bg.vector_b_count != cg.vector_b_count):
        raise ValueError("candidate GXM layout differs from baseline")
    meshes = [mesh for mesh in parse_sidecar(sidecar_path).meshes if mesh.name == directive]
    if len(meshes) != 1:
        raise ValueError("sidecar must resolve to one exact hull directive")
    mesh = meshes[0]
    if mesh.index < 0 or mesh.size <= 0 or mesh.index + mesh.size > bt.record_count:
        raise ValueError("hull record range outside GXM")
    first, stop = mesh.index, mesh.index + mesh.size
    records = [struct.unpack_from("<10I", baseline, bt.record_offset + i * 52)
               for i in range(bt.record_count)]
    candidate_records = [struct.unpack_from("<10I", candidate, ct.record_offset + i * 52)
                         for i in range(ct.record_count)]
    topology_unchanged = records == candidate_records
    hull_ids = sorted({index for row in records[first:stop] for index in row[4:7]})
    outside_records = [i for i, row in enumerate(records)
                       if not first <= i < stop and set(row[4:7]).intersection(hull_ids)]
    before = {index: struct.unpack_from("<3f", baseline, bt.vector_c_offset + index * 12)
              for index in range(bt.vector_c_count)}
    after = {index: struct.unpack_from("<3f", candidate, ct.vector_c_offset + index * 12)
             for index in range(ct.vector_c_count)}
    changed_ids = {index for index in range(bt.vector_c_count) if before[index] != after[index]}
    try:
        translation = rigid_translation_metrics(
            {index: before[index] for index in hull_ids},
            {index: after[index] for index in hull_ids}, translation_tolerance)
        translation_error = None
    except ValueError as error:
        translation, translation_error = None, str(error)

    allowed = {offset for index in hull_ids
               for offset in range(bt.vector_c_offset + index * 12,
                                   bt.vector_c_offset + index * 12 + 12)}
    changed_byte_offsets = [index for index, (a, b) in enumerate(zip(baseline, candidate)) if a != b]
    only_hull_c_bytes_changed = all(index in allowed for index in changed_byte_offsets)
    all_hull_ids_changed = changed_ids == set(hull_ids)
    same_a_b_arrays = (baseline[bg.vector_a_offset:bg.vector_b_offset]
                       == candidate[cg.vector_a_offset:cg.vector_b_offset]
                       and baseline[bg.vector_b_offset:bg.sentinel_offset]
                       == candidate[cg.vector_b_offset:cg.sentinel_offset])

    area_deltas = []
    normal_angles = []
    degenerate_faces = 0
    for row in records[first:stop]:
        face = tuple(row[4:7])
        normal0, area0 = _triangle_normal_area(before, face)
        normal1, area1 = _triangle_normal_area(after, face)
        if normal0 is None or normal1 is None:
            degenerate_faces += 1
            continue
        dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(normal0, normal1))))
        normal_angles.append(math.degrees(math.acos(dot)))
        area_deltas.append(abs(area1 - area0))

    checks = {
        "record_topology_unchanged": topology_unchanged,
        "no_hull_c_positions_shared_with_outside_records": not outside_records,
        "all_and_only_hull_c_positions_changed": all_hull_ids_changed and changed_ids <= set(hull_ids),
        "all_changes_confined_to_hull_vector_c_bytes": only_hull_c_bytes_changed,
        "vector_a_and_b_arrays_unchanged": same_a_b_arrays,
        "hull_c_changes_are_one_rigid_translation": translation is not None,
        "all_source_faces_remain_nondegenerate": degenerate_faces == 0,
        "face_shape_changes_within_float32_noise": (max(normal_angles, default=0.0) <= 1e-3
                                                     and max(area_deltas, default=0.0) <= 1e-5),
    }
    return {
        "status": "FLAT_GXM_HULL_SOURCE_INVARIANTS_PASS" if all(checks.values()) else "REJECTED",
        "checks": checks,
        "directive": directive,
        "record_range_half_open": [first, stop],
        "hull_c_index_count": len(hull_ids),
        "changed_c_index_count": len(changed_ids),
        "outside_records_reusing_hull_c_indices": outside_records,
        "translation": translation,
        "translation_error": translation_error,
        "changed_byte_count": len(changed_byte_offsets),
        "degenerate_source_faces": degenerate_faces,
        "max_geometric_normal_angle_change_degrees": max(normal_angles, default=None),
        "max_triangle_area_absolute_change": max(area_deltas, default=None),
        "scope_limit": "Checks serialized flat GXM range only; does not validate loader remapping, hierarchy transforms, hidden descendants, or runtime cooker success.",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-gxm", type=Path, required=True)
    ap.add_argument("--candidate-gxm", type=Path, required=True)
    ap.add_argument("--sidecar", type=Path, required=True)
    ap.add_argument("--directive", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    scratch = (repo / ".research-output" / "r-demo2").resolve()
    baseline = args.baseline_gxm.resolve(strict=True)
    candidate = args.candidate_gxm.resolve(strict=True)
    sidecar = args.sidecar.resolve(strict=True)
    output = args.output.resolve()
    corpus = (repo.parent / "corpora").resolve()
    if corpus in candidate.parents:
        ap.error("candidate GXM must be outside the immutable corpus")
    if scratch not in candidate.parents or scratch not in output.parents or output.suffix.lower() != ".json":
        ap.error("candidate and JSON output must be under ignored .research-output/r-demo2")
    report = validate_pair(baseline.read_bytes(), candidate.read_bytes(), sidecar,
                           args.directive)
    report.update({"baseline_gxm": str(baseline), "candidate_gxm": str(candidate),
                   "sidecar": str(sidecar),
                   "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
                   "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                   "sidecar_sha256": hashlib.sha256(sidecar.read_bytes()).hexdigest()})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": report["checks"],
                      "translation": report["translation"]}))


if __name__ == "__main__":
    main()
