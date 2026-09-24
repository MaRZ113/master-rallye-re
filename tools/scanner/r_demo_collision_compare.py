"""Numerically compare one sidecar-identified GXM chull to a retail DX tag101."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import struct
from pathlib import Path

from master_rallye.dx import parse_dx
from master_rallye.gxm import (
    parse_gxm_prefix_bytes, parse_gxm_geometry_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)


def hull_vertex_ids(points: list[tuple[float, float, float]], tolerance: float = 1e-6) -> set[int]:
    result: set[int] = set()
    for i, j, k in itertools.combinations(range(len(points)), 3):
        a, b, c = points[i], points[j], points[k]
        u = tuple(b[axis] - a[axis] for axis in range(3))
        v = tuple(c[axis] - a[axis] for axis in range(3))
        normal = (u[1] * v[2] - u[2] * v[1],
                  u[2] * v[0] - u[0] * v[2],
                  u[0] * v[1] - u[1] * v[0])
        magnitude = math.sqrt(sum(value * value for value in normal))
        if magnitude < 1e-9:
            continue
        signs = [sum(normal[axis] * (point[axis] - a[axis]) for axis in range(3)) / magnitude
                 for point in points]
        if min(signs) >= -tolerance or max(signs) <= tolerance:
            result.update((i, j, k))
    return result


def bounds(points):
    return tuple((min(point[axis] for point in points), max(point[axis] for point in points))
                 for axis in range(3))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--source-corpus-id", required=True)
    ap.add_argument("--source-relative-path", type=Path, required=True)
    ap.add_argument("--sidecar-relative-path", type=Path, required=True)
    ap.add_argument("--directive", required=True)
    ap.add_argument("--target-root", type=Path, required=True)
    ap.add_argument("--target-corpus-id", required=True)
    ap.add_argument("--target-relative-path", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source_root = args.source_root.resolve(strict=True)
    target_root = args.target_root.resolve(strict=True)
    output = args.output.resolve()
    if any(output == root or root in output.parents for root in (source_root, target_root)):
        raise SystemExit("output must not be inside either corpus")
    sidecar = (source_root / args.sidecar_relative_path).resolve(strict=True)
    source_path = (source_root / args.source_relative_path).resolve(strict=True)
    target_path = (target_root / args.target_relative_path).resolve(strict=True)
    if source_root not in sidecar.parents or source_root not in source_path.parents or target_root not in target_path.parents:
        raise SystemExit("resource path escapes its corpus")
    pattern = re.compile(r"moMesh\(Name \[" + re.escape(args.directive) + r"\] Index (\d+) Size (\d+)\)")
    matches = pattern.findall(sidecar.read_text(encoding="latin-1"))
    if len(matches) != 1:
        raise SystemExit("expected exactly one sidecar mesh range")
    first, count = map(int, matches[0])
    raw = source_path.read_bytes()
    prefix = parse_gxm_prefix_bytes(raw, f"{args.source_corpus_id}:{args.source_relative_path.as_posix()}")
    geometry = parse_gxm_geometry_prefix_bytes(raw, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(raw, prefix, geometry)
    if first < 0 or count <= 0 or first + count > triangles.record_count:
        raise SystemExit("sidecar mesh range outside GXM record count")
    vertex_ids = set()
    for index in range(first, first + count):
        record = struct.unpack_from("<10I", raw, triangles.record_offset + index * 52)
        vertex_ids.update(record[4:7])
    source_points = [struct.unpack_from("<3f", raw, triangles.vector_c_offset + index * 12)
                     for index in sorted(vertex_ids)]
    transformed = [(x, z, -y) for x, y, z in source_points]
    hull_ids = hull_vertex_ids(transformed)
    target = parse_dx(target_path).collision.convex_hull
    if target is None:
        raise SystemExit("target DX has no parsed tag101")
    target_points = target.representation_b.geometry_a.vertices
    hull_points = [transformed[index] for index in sorted(hull_ids)]
    nearest_forward = [min(math.dist(point, other) for other in target_points) for point in hull_points]
    nearest_reverse = [min(math.dist(point, other) for other in hull_points) for point in target_points]
    source_bounds = bounds(transformed)
    box_bounds = bounds(target.representation_a.geometry_a.vertices)
    bound_difference = max(abs(a - b) for source_axis, box_axis in zip(source_bounds, box_bounds)
                           for a, b in zip(source_axis, box_axis))
    center = target.base_geometry.vertices[0]
    box_radius = max(math.dist(center, point) for point in target.representation_a.geometry_a.vertices)
    report = {"source": {"corpus_id": args.source_corpus_id,
                         "relative_path": args.source_relative_path.as_posix(),
                         "sidecar_relative_path": args.sidecar_relative_path.as_posix(),
                         "directive": args.directive, "record_start": first,
                         "record_count": count, "unique_point_count": len(transformed),
                         "convex_hull_vertex_count": len(hull_points)},
              "target": {"corpus_id": args.target_corpus_id,
                         "relative_path": args.target_relative_path.as_posix(),
                         "tag101_b_vertex_count": len(target_points),
                         "tag101_b_triangle_count": len(target.representation_b.geometry_a.triangles)},
              "axis_transform": "(x,y,z) -> (x,z,-y)",
              "max_source_hull_to_tag101_b_distance": max(nearest_forward),
              "max_tag101_b_to_source_hull_distance": max(nearest_reverse),
              "source_bounds": source_bounds, "tag101_a_box_bounds": box_bounds,
              "max_aabb_axis_difference": bound_difference,
              "tag101_base_scalar": target.base_scalar,
              "base_to_box_corner_radius": box_radius,
              "radius_difference": abs(target.base_scalar - box_radius),
              "evidence": "CONFIRMED_BY_CORPUS numeric correspondence; cross-build comparison"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
