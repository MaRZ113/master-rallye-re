#!/usr/bin/env python3
"""Read-only marker-1339 vehicle corpus audit, no game bytes written."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.bounds import compute_bounds1339
from master_rallye.dx import parse_dx_bytes


def _f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def run(root: Path) -> dict:
    rows = []
    for path in sorted(root.rglob("*.dx")):
        model = parse_dx_bytes(path.read_bytes())
        stored = model.collision.spatial_bounds_1339
        if stored is None:
            raise ValueError(f"{path}: no typed marker-1339 footer")
        render = list(model.vertices.positions)
        hull = model.collision.convex_hull
        detailed = list(hull.representation_b.geometry_a.vertices) if hull else []
        helper = []
        if hull:
            for geom in (hull.base_geometry, hull.representation_a.geometry_a,
                         hull.representation_a.geometry_b, hull.representation_b.geometry_a,
                         hull.representation_b.geometry_b):
                helper.extend(geom.vertices)
        expected = compute_bounds1339(render, hull, offset=stored.offset)
        def radius(points):
            return _f32(max(math.dist(point, stored.center) for point in points))
        candidate = {
            "render_only": radius(render),
            "render_plus_detailed_b": radius(render + detailed),
            "render_plus_all_tag101": radius(render + helper),
            "aabb_half_diagonal": _f32(math.dist(stored.minimum, stored.maximum) / 2),
        }
        rows.append({
            "resource": path.relative_to(root).as_posix(),
            "role": path.name,
            "marker": 1339,
            "stored": stored.to_dict(),
            "recomputed": expected.to_dict(),
            "min_max_max_abs_error": max(abs(a - b) for a,b in zip(
                stored.minimum + stored.maximum, expected.minimum + expected.maximum)),
            "center_max_abs_error": max(abs(a - b) for a,b in zip(stored.center, expected.center)),
            "radius_candidates": candidate,
            "radius_abs_error": abs(stored.radius - candidate["render_plus_detailed_b"]),
            "raw_byte_equal": stored.raw == expected.raw,
            "has_tag101": hull is not None,
        })
    summary = {
        "resources": len(rows),
        "typed_footer": len(rows),
        "min_max_within_1e_6": sum(r["min_max_max_abs_error"] <= 1e-6 for r in rows),
        "center_within_1e_5": sum(r["center_max_abs_error"] <= 1e-5 for r in rows),
        "radius_detailed_b_within_1e_5": sum(r["radius_abs_error"] <= 1e-5 for r in rows),
        "radius_detailed_b_exact_f32": sum(r["radius_abs_error"] == 0 for r in rows),
        "recomputed_full_footer_byte_equal": sum(r["raw_byte_equal"] for r in rows),
        "wheel_count": sum(r["role"] == "wheel.dx" for r in rows),
        "wheel_radius_within_1e_5": sum(r["role"] == "wheel.dx" and r["radius_abs_error"] <= 1e-5 for r in rows),
        "maximum_radius_error": max(r["radius_abs_error"] for r in rows),
        "radius_exceptions": [r["resource"] for r in rows if r["radius_abs_error"] > 1e-5],
    }
    return {"summary": summary, "resources": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.vehicle_root.resolve())
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    s = report["summary"]
    args.markdown.write_text(
        "# Marker-1339 bounds corpus\n\n"
        "This read-only scan uses the protected 78-resource original vehicle corpus. "
        "Detailed rows, alternative radius formulas and byte equality are in bounds-corpus.json.\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in s.items()) + "\n",
        encoding="utf-8")
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
