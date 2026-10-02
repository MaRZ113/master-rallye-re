#!/usr/bin/env python3
"""Static spatial comparison of paired Demo 8.4 GXM and RaceTest RaceLine."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from master_rallye.course_gxm import parse_course_gxm_model_v7  # noqa: E402
from master_rallye.course_source import parse_course_txt  # noqa: E402
from master_rallye.course_xml import parse_course_xml  # noqa: E402


CASES = (
    ("France1", "France1", "France1.gxm", "_raceline"),
    ("Italy1", "Italy1", "track01.gxm", "raceline"),
)


def _nearest_xz(point, route):
    px, pz = point[0], point[2]
    best = None
    for index, (a, b) in enumerate(zip(route, route[1:])):
        dx, dz = b[0] - a[0], b[2] - a[2]
        denominator = dx * dx + dz * dz
        t = 0.0 if denominator <= 1.0e-12 else max(0.0, min(1.0, ((px - a[0]) * dx + (pz - a[2]) * dz) / denominator))
        qx, qz = a[0] + t * dx, a[2] + t * dz
        distance = math.hypot(px - qx, pz - qz)
        if best is None or distance < best[0]:
            best = (distance, index, t)
    return best


def _quantile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    low = int(position)
    blend = position - low
    return ordered[low] * (1.0 - blend) + ordered[low + 1] * blend


def _bounds(points):
    return [[min(point[axis] for point in points), max(point[axis] for point in points)] for axis in range(3)]


def analyze(demo_root: Path) -> dict:
    rows = []
    for course, folder, gxm_name, mesh_name in CASES:
        directory = demo_root / "DataGx" / "Course" / folder
        gxm_path = directory / gxm_name
        txt_path = directory / f"{Path(gxm_name).stem}.txt"
        xml_path = demo_root / "DataScene" / "RaceTest" / f"{course}.xml"
        for path in (gxm_path, txt_path, xml_path):
            if not path.is_file():
                raise FileNotFoundError(path)

        model = parse_course_gxm_model_v7(gxm_path, parse_course_txt(txt_path))
        mesh = model.find_mesh(mesh_name)
        triangle_indices = tuple(model.mesh_triangle_indices(mesh))
        position_indices = tuple(sorted(set(model.mesh_position_indices(mesh))))
        source_points = [model.position(index) for index in position_indices]
        runtime_points = [(point[0], point[2], -point[1]) for point in source_points]
        document = parse_course_xml(xml_path)
        marker_list = document.marker_list("RaceLine")
        if marker_list is None or len(marker_list.markers) < 2:
            raise ValueError(f"{course}: missing usable RaceLine MarkerList")
        route = [item.position for item in marker_list.markers if item.position is not None]
        distances = [_nearest_xz(point, route)[0] for point in runtime_points]
        within = {str(threshold): sum(value <= threshold for value in distances) for threshold in (1, 5, 10, 20)}
        rows.append({
            "course": course,
            "build": "Demo 8.4.1",
            "gxm": gxm_path.relative_to(demo_root).as_posix(),
            "gxm_sha256": hashlib.sha256(gxm_path.read_bytes()).hexdigest().upper(),
            "txt": txt_path.relative_to(demo_root).as_posix(),
            "txt_sha256": hashlib.sha256(txt_path.read_bytes()).hexdigest().upper(),
            "racetest_xml": xml_path.relative_to(demo_root).as_posix(),
            "racetest_xml_sha256": hashlib.sha256(xml_path.read_bytes()).hexdigest().upper(),
            "mesh_name": mesh.name,
            "mesh_triangle_index": mesh.mesh_index,
            "mesh_triangle_count": len(triangle_indices),
            "unique_position_indices": len(position_indices),
            "source_to_runtime_coordinate_map": "(x, y, z) -> (x, z, -y)",
            "runtime_transformed_mesh_bounds_xyz": _bounds(runtime_points),
            "raceline_marker_count": len(route),
            "raceline_bounds_xyz": _bounds(route),
            "nearest_source_order_raceline_segment_distance_xz": {
                "count": len(distances), "min": min(distances), "median": statistics.median(distances),
                "p90": _quantile(distances, 0.90), "p95": _quantile(distances, 0.95),
                "p99": _quantile(distances, 0.99), "max": max(distances),
                "within_threshold_count": within,
                "within_threshold_fraction": {key: count / len(distances) for key, count in within.items()},
            },
            "interpretation": "STATIC_SPATIAL_CORRELATION_ONLY; GXM mesh and RaceTest MarkerLists/RaceLine remain distinct resources.",
        })
    return {
        "schema": "master-rallye-g1-gxm-raceline-correlation-v1",
        "evidence": "CONFIRMED_BY_CORPUS; static geometry only",
        "source_corpus": "Demo 8.4.1 corpus (paths are relative to the corpus root)",
        "cases": rows,
        "semantic_limits": [
            "No runtime relationship between GXM mesh names and RaceTest list names is asserted.",
            "Distances use nearest source-order RaceLine segment in runtime X/Z only; vertical mismatch is reported separately in bounds.",
            "Nearest-segment proximity cannot distinguish a center path, road strip, helper mesh, or other related geometry by itself.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=REPOSITORY / "research" / "g1" / "gxm-raceline-correlation.json")
    args = parser.parse_args()
    report = analyze(args.demo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.output.resolve()}")
    for item in report["cases"]:
        metrics = item["nearest_source_order_raceline_segment_distance_xz"]
        print(f"{item['course']}: triangles={item['mesh_triangle_count']} positions={item['unique_position_indices']} median={metrics['median']:.3f} p95={metrics['p95']:.3f} <=5={metrics['within_threshold_fraction']['5']:.3%} <=20={metrics['within_threshold_fraction']['20']:.3%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
