"""Exact demo-8.4.1 Trooper $chull source differential (read only).

The CLI pins both known inputs. The reusable comparison accepts byte strings so
small synthetic fixtures can exercise validation without distributing assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from master_rallye.gxm import (parse_gxm_prefix_bytes,
                               parse_gxm_geometry_prefix_bytes,
                               parse_gxm_triangle_prefix_bytes)
from master_rallye.gxm_hierarchy import (find_nodes, parse_gxm_hierarchy_tail,
                                         serialized_c_triangle_stream)

EXPECTED = {
    "baseline": "fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047",
    "candidate": "0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699",
}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _geometry(data: bytes, expected):
    prefix = parse_gxm_prefix_bytes(data)
    geom = parse_gxm_geometry_prefix_bytes(data, prefix)
    tri = parse_gxm_triangle_prefix_bytes(data, prefix, geom)
    hierarchy = parse_gxm_hierarchy_tail(data, tri.hierarchy_offset)
    if prefix.header_words[0] != 0x00020702 or prefix.header_words[1] != 0:
        raise ValueError("unexpected GXM type/version/root header")
    name, start, count, expected_ids, node_count, root_count = expected
    if hierarchy.node_count != node_count or len(hierarchy.roots) != root_count:
        raise ValueError("unexpected Trooper hierarchy shape")
    hulls = find_nodes(hierarchy.roots, name)
    if len(hulls) != 1:
        raise ValueError("expected one Trooper hull node")
    hull = hulls[0]
    if (hull.mesh_start, hull.mesh_count) != (start, count) or hull.children:
        raise ValueError("unexpected Trooper hull range or descendants")
    triangles = serialized_c_triangle_stream(data, tri.record_offset, tri.record_count,
                                             hull.mesh_start, hull.mesh_count)
    indices = tuple(sorted({i for t in triangles for i in t.c_indices}))
    if indices != tuple(expected_ids):
        raise ValueError("unexpected Trooper hull C indices")
    return prefix, geom, tri, hierarchy, triangles, indices


def _point(data: bytes, offset: int, index: int) -> tuple[float, float, float]:
    return struct.unpack_from("<3f", data, offset + index * 12)


def _bounds(points):
    return [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]


def _centroid(points):
    return [sum(p[i] for p in points) / len(points) for i in range(3)]


def _plane(points, indices):
    p, q, r = (points[i] for i in indices)
    u = [q[i] - p[i] for i in range(3)]
    v = [r[i] - p[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1],
         u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    area2 = math.sqrt(sum(x * x for x in n))
    if area2 == 0:
        return None
    normal = tuple(x / area2 for x in n)
    return normal, -sum(normal[i] * p[i] for i in range(3)), area2


def compare(baseline: bytes, candidate: bytes, *, expected=("$chull(Trooper)", 1911, 68, range(1317, 1353), 28, 2)) -> dict:
    if len(baseline) != len(candidate):
        raise ValueError("GXM sizes differ")
    a = _geometry(baseline, expected)
    b = _geometry(candidate, expected)
    ap, ag, at, ah, triangles, ids = a
    bp, bg, bt, bh, other_triangles, other_ids = b
    if (ap.header_words != bp.header_words or ag != bg or ah != bh or
            (at.record_offset, at.record_count, at.vector_c_offset, at.vector_c_count,
             at.hierarchy_offset) !=
            (bt.record_offset, bt.record_count, bt.vector_c_offset, bt.vector_c_count,
             bt.hierarchy_offset)):
        raise ValueError("GXM layouts or hierarchy differ")
    if triangles != other_triangles or ids != other_ids:
        raise ValueError("hull record topology differs")
    allowed = {at.vector_c_offset + i * 12 + byte for i in ids for byte in range(4)}
    changed = [i for i, (x, y) in enumerate(zip(baseline, candidate)) if x != y]
    outside = [i for i in changed if i not in allowed]
    if outside:
        raise ValueError(f"non-hull-X edit at 0x{outside[0]:X}")
    if not changed:
        raise ValueError("inputs are identical")
    pa = {i: _point(baseline, at.vector_c_offset, i) for i in ids}
    pb = {i: _point(candidate, at.vector_c_offset, i) for i in ids}
    deltas = [pb[i][0] - pa[i][0] for i in ids]
    if any(pb[i][1:] != pa[i][1:] for i in ids):
        raise ValueError("hull Y/Z changed")
    if any(abs(x - 0.4) > 1e-6 for x in deltas):
        raise ValueError("hull translation differs from +0.4 X")
    def external_gap(data):
        other = [_point(data, at.vector_c_offset, i)
                 for i in range(at.vector_c_count) if i not in ids]
        if not other:
            return None
        return min(math.dist(point, remote) for point in
                   (_point(data, at.vector_c_offset, i) for i in ids)
                   for remote in other)

    def radii(points, center):
        values = [math.dist(point, center) for point in points]
        return [min(values), max(values)]
    centers = (_centroid(list(pa.values())), _centroid(list(pb.values())))
    planes = []
    for t in triangles:
        before = _plane(pa, t.c_indices)
        after = _plane(pb, t.c_indices)
        if before is not None and after is not None:
            planes.append((before, after))
    return {
        "schema": "r-demo2.6-exact-841-hull-diff-v1",
        "corpus_id": "demo-8.4.1",
        "baseline_sha256": _digest(baseline),
        "candidate_sha256": _digest(candidate),
        "size": len(baseline),
        "changed_byte_count": len(changed),
        "changed_min_offset": changed[0],
        "changed_max_offset": changed[-1],
        "changed_indices": list(ids),
        "changed_component": "Vector C source X only",
        "record_range": [expected[1], expected[1] + expected[2]],
        "record_count": len(triangles),
        "corner_count": len(triangles) * 3,
        "topology_unchanged": True,
        "non_hull_bytes_unchanged": True,
        "vector_a_b_bytes_unchanged": True,
        "hierarchy_bytes_unchanged": True,
        "source_x_delta_min_max": [min(deltas), max(deltas)],
        "source_bounds_before": _bounds(list(pa.values())),
        "source_bounds_after": _bounds(list(pb.values())),
        "source_centroid_before": centers[0],
        "source_centroid_after": centers[1],        "source_radius_from_origin_before": radii(list(pa.values()), (0, 0, 0)),
        "source_radius_from_origin_after": radii(list(pb.values()), (0, 0, 0)),
        "source_radius_from_centroid_before": radii(list(pa.values()), centers[0]),
        "source_radius_from_centroid_after": radii(list(pb.values()), centers[1]),
        "min_hull_to_nonhull_c_distance_before": external_gap(baseline),
        "min_hull_to_nonhull_c_distance_after": external_gap(candidate),
        "nondegenerate_source_triangles": len(planes),
        "max_cross_magnitude_delta": max((abs(x[0][2] - x[1][2]) for x in planes), default=None),
        "max_normal_component_delta": max((abs(x[0][0][j] - x[1][0][j]) for x in planes for j in range(3)), default=None),
        "plane_d_delta_min_max": [min((x[1][1] - x[0][1] for x in planes), default=None),
                                  max((x[1][1] - x[0][1] for x in planes), default=None)],
        "plane_d_predicted_translation_max_residual": max((abs((x[1][1] - x[0][1]) +
                                                                x[0][0][0] * 0.4) for x in planes), default=None),
        "precision_note": "source binary32 coordinates, derived geometry calculated in Python binary64; not native 8.4.1 post-weld bytes",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source, edited = args.baseline.read_bytes(), args.candidate.read_bytes()
    for key, data in (("baseline", source), ("candidate", edited)):
        if _digest(data) != EXPECTED[key]:
            parser.error(f"{key} SHA256 does not match pinned demo-8.4.1 input")
    report = compare(source, edited)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
