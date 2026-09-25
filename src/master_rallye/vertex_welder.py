"""Bounded demo-9.3.1 pre-hull weld oracle, derived from EXE control flow.

The exact supported domain is a selected set with no possible proximity pair.
No guessed sort axis or transitive union-find is substituted for the native
ordered, guarded coordinate-copy algorithm. Non-isolated selections fail closed.
"""
from __future__ import annotations

import math
import struct
from itertools import combinations
from collections import Counter
from fractions import Fraction

TOLERANCE = struct.unpack("<f", bytes.fromhex("0ad7233c"))[0]
DEGREES_TO_RADIANS = struct.unpack("<f", bytes.fromhex("35fa8e3c"))[0]


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _points(points):
    result = tuple(tuple(p) for p in points)
    if not result or any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in result):
        raise ValueError("nonempty finite float3 positions required")
    if any(f32(v) != v for p in result for v in p):
        raise ValueError("runtime storage requires binary32 positions")
    return result


def loader_positions(points, *, single_precision=False):
    """005b64d0: X unchanged, -90 degree X rotation, binary32 stores.

    single_precision includes rounding intermediate x87 arithmetic to 24 bits;
    the default uses wide intermediates. Neither is a captured runtime buffer.
    """
    points = _points(points)
    rnd = f32 if single_precision else lambda x: x
    angle = rnd(-90.0 * DEGREES_TO_RADIANS)
    c, s = f32(math.cos(angle)), f32(math.sin(angle))
    return tuple((x, f32(rnd(rnd(y*c) - rnd(z*s))),
                  f32(rnd(rnd(z*c) + rnd(y*s)))) for x, y, z in points)


def proximity_pairs(points, tolerance=TOLERANCE):
    """Unordered superset of 005ceac0 pairs, independent of its sort axis.

    Strict squared Euclidean comparison of exact binary32 operands. A positive
    near-boundary margin is required by isolation_proof, so its conclusion does
    not depend on x87 intermediate rounding at the comparison boundary.
    """
    points = _points(points)
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("positive finite tolerance required")
    result = []
    limit = Fraction(tolerance)**2
    for i, a in enumerate(points):
        for j in range(i + 1, len(points)):
            b = points[j]
            if any(abs(a[k]-b[k]) >= tolerance for k in range(3)):
                continue
            distance2 = sum((Fraction(a[k])-Fraction(b[k]))**2 for k in range(3))
            if distance2 < limit:
                result.append((i, j, math.sqrt(float(distance2))))
    return tuple(result)


def isolation_proof(points, selected, *, margin=1e-6):
    """Prove all selected positions untouched for every axis/order/guard result."""
    points = _points(points)
    selected = tuple(sorted(set(selected)))
    if not selected or min(selected) < 0 or max(selected) >= len(points):
        raise ValueError("nonempty in-range selected indices required")
    if not math.isfinite(margin) or margin < 1e-6:
        raise ValueError("isolation margin must be at least 1e-6")
    near = []
    nearest = math.inf
    for i in selected:
        for j, p in enumerate(points):
            if i == j:
                continue
            distance = math.dist(points[i], p)
            nearest = min(nearest, distance)
            if distance <= TOLERANCE + margin:
                near.append({"selected": i, "other": j, "distance": distance})
    complete = not near
    return {"complete": complete, "status": "PROVEN_UNTOUCHED" if complete else "UNRESOLVED",
            "tolerance": TOLERANCE, "margin": margin,
            "nearest_other_distance": nearest if math.isfinite(nearest) else None,
            "near_dependencies": near,
            "representatives": {i: i for i in selected} if complete else None,
            "welded_classes": [[i] for i in selected] if complete else None,
            "maximum_merge_distance": 0.0 if complete else None}


def emit_triangles(points, indices):
    points = _points(points)
    faces = tuple(tuple(face) for face in indices)
    if not faces or any(len(face) != 3 or any(i < 0 or i >= len(points) for i in face) for face in faces):
        raise ValueError("nonempty in-range triangles required")
    return tuple(tuple(points[i] for i in face) for face in faces)


def _face(face):
    a, b, c = face
    u = tuple(b[k]-a[k] for k in range(3))
    v = tuple(c[k]-a[k] for k in range(3))
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    size = math.sqrt(sum(x*x for x in n))
    return size / 2, tuple(x/size for x in n) if size else (0., 0., 0.)


def stream_metrics(points, indices):
    stream = emit_triangles(points, indices)
    corners = [p for face in stream for p in face]
    unique = set(corners)
    keys = [min(face[i:]+face[:i] for i in range(3)) for face in stream]
    return {"triangle_count": len(stream), "corner_count": len(corners),
            "unique_positions": len(unique),
            "degenerate_triangles": [i for i, face in enumerate(stream) if _face(face)[0] <= 1e-12],
            "duplicate_triangles": sum(n-1 for n in Counter(keys).values()),
            "bounds": [[min(p[k] for p in unique) for k in range(3)],
                       [max(p[k] for p in unique) for k in range(3)]],
            "unique_centroid": [sum(p[k] for p in sorted(unique))/len(unique) for k in range(3)],
            "corner_centroid": [sum(p[k] for p in corners)/len(corners) for k in range(3)]}


def classify(complete, mismatch, invariants_pass):
    """A requires a concrete, completely reconstructed mismatch; U stays U."""
    if not complete:
        return "U"
    if mismatch:
        return "A"
    return "B" if invariants_pass else "U"


def compare_streams(before, after, before_indices, after_indices, before_proof, after_proof,
                    *, expected=(0.4, 0., 0.), pre_hull_stages_excluded=False,
                    source_scope_validated=False, tolerance=1e-6):
    if not math.isfinite(tolerance) or tolerance <= 0 or len(expected) != 3 or not all(math.isfinite(v) for v in expected):
        raise ValueError("finite expected translation and positive finite tolerance required")
    a = emit_triangles(before, before_indices)
    b = emit_triangles(after, after_indices)
    ma, mb = stream_metrics(before, before_indices), stream_metrics(after, after_indices)
    complete = before_proof["complete"] and after_proof["complete"]
    topology = tuple(map(tuple, before_indices)) == tuple(map(tuple, after_indices))
    matching = len(a) == len(b)
    deltas = [tuple(q[k]-p[k] for k in range(3)) for fa, fb in zip(a, b) for p, q in zip(fa, fb)]
    mean = tuple(sum(d[k] for d in deltas)/len(deltas) for k in range(3))
    residual = max(math.dist(d, mean) for d in deltas)
    expected_residual = max(math.dist(d, expected) for d in deltas)
    areas = [abs(_face(fa)[0]-_face(fb)[0]) for fa, fb in zip(a, b)]
    normals = [math.dist(_face(fa)[1], _face(fb)[1]) for fa, fb in zip(a, b)]
    classes = complete and before_proof["representatives"] == after_proof["representatives"]
    checks = {"same_triangle_count": matching, "same_indices_topology_winding_adjacency": topology,
              "same_unique_position_count": ma["unique_positions"] == mb["unique_positions"],
              "no_degenerates": not ma["degenerate_triangles"] and not mb["degenerate_triangles"],
              "no_duplicate_triangles": ma["duplicate_triangles"] == mb["duplicate_triangles"] == 0,
              "same_representatives_no_external_dependency": classes,
              "uniform_translation": residual <= tolerance and expected_residual <= tolerance,
              "areas_preserved": max(areas) <= tolerance,
              "normals_preserved": max(normals) <= tolerance,
              "pre_hull_stages_excluded": pre_hull_stages_excluded,
              "source_scope_validated": source_scope_validated,
              "post_weld_reconstruction_complete": complete}
    mismatch = complete and (not topology or not classes or residual > tolerance or
                            ma["unique_positions"] != mb["unique_positions"] or
                            bool(mb["degenerate_triangles"]))
    passed = all(checks.values())
    return {"decision": classify(complete and pre_hull_stages_excluded and source_scope_validated,
                                  mismatch, passed), "checks": checks, "passed": passed,
            "baseline": ma, "candidate": mb, "expected_translation": expected,
            "fitted_translation": mean, "maximum_rigid_residual": residual,
            "maximum_expected_translation_residual": expected_residual,
            "maximum_area_change": max(areas), "maximum_normal_vector_change": max(normals)}


PLANE_THICKNESS = 0.0005000000237487257  # Initial binary64 at VA 0067c6f0; config can override.


def early_hull_probe(points, indices, *, thickness=PLANE_THICKNESS):
    """Diagnostic 005f3190/3630/2fc0/37c0/005fc2b0/ca60 mathematics.

    Binary64 Python probe, not a native x87 emulator or a complete hull builder.
    Plane deduplication/edges/intersections are deliberately excluded.
    """
    if not math.isfinite(thickness) or thickness <= 0:
        raise ValueError("positive finite plane thickness required")
    corners = [p for face in emit_triangles(points, indices) for p in face]
    unique, representative_corners = [], []
    for corner_id, p in enumerate(corners):
        if not any(math.dist(p,q) < thickness for q in unique):
            unique.append(p)
            representative_corners.append(corner_id)
    if len(unique) < 4:
        raise ValueError("insufficient hull points")
    center = tuple((min(p[k] for p in unique)+max(p[k] for p in unique))*0.5 for k in range(3))
    diameter = 2*max(math.dist(p,center) for p in unique)
    signatures, support = [], 0
    nearest_gate = math.inf
    for ids in combinations(range(len(unique)), 3):
        a,b,c = (unique[i] for i in ids)
        area, normal = _face((a,b,c))
        length = 2*area
        nearest_gate = min(nearest_gate, abs(length-thickness))
        if length < thickness:
            signatures.append((ids, "rejected_cross_length"))
            continue
        if length < 9.999999974752427e-7:
            normal = (0., 0., 0.)
        if sum((a[k]-center[k])*normal[k] for k in range(3)) < 0:
            normal = tuple(-v for v in normal)
        constant = sum(a[k]*normal[k] for k in range(3))
        distances = [sum(p[k]*normal[k] for k in range(3))-constant for p in unique]
        nearest_gate = min(nearest_gate, *(abs(abs(v)-thickness) for v in distances))
        sides = tuple(1 if v > thickness else -1 if v < -thickness else 0 for v in distances)
        if 1 not in sides:
            support += 1
        signatures.append((ids, sides))
    return {"unique_count": len(unique), "representative_corner_ids": representative_corners,
            "center": center, "twice_centered_radius": diameter,
            "triples": len(signatures), "supporting_triples_before_plane_dedup": support,
            "nearest_epsilon_gate_margin": nearest_gate, "signatures": signatures}
