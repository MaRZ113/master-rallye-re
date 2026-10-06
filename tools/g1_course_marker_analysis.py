#!/usr/bin/env python3
"""Read-only geometry and inventory analysis for Retail RaceTest marker lists."""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from master_rallye.course_xml import parse_course_xml  # noqa: E402


RETAIL_EXE_SHA256 = "BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4"
LISTS = (
    "RaceLine", "LeftInnerLimit", "LeftOuterLimit", "RightInnerLimit",
    "RightOuterLimit", "Cameras",
)
LIMITS = ("LeftInnerLimit", "LeftOuterLimit", "RightInnerLimit", "RightOuterLimit")


def _norm3(v):
    length = math.sqrt(sum(float(x) * float(x) for x in v))
    return None if length <= 1.0e-12 else tuple(float(x) / length for x in v)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _stats(values):
    clean = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not clean:
        return {"count": 0, "min": None, "median": None, "mean": None, "p05": None, "p95": None, "max": None}

    def percentile(fraction):
        if len(clean) == 1:
            return clean[0]
        position = fraction * (len(clean) - 1)
        low = int(position)
        high = min(low + 1, len(clean) - 1)
        blend = position - low
        return clean[low] * (1.0 - blend) + clean[high] * blend

    return {
        "count": len(clean), "min": clean[0], "median": statistics.median(clean),
        "mean": statistics.fmean(clean), "p05": percentile(0.05),
        "p95": percentile(0.95), "max": clean[-1],
    }


def _delta(a, b):
    return tuple(float(b[i]) - float(a[i]) for i in range(3))


def _length(v, horizontal=False):
    values = (v[0], v[2]) if horizontal else v
    return math.sqrt(sum(value * value for value in values))


def _cosine(a, b, horizontal=False):
    if horizontal:
        a, b = (a[0], a[2]), (b[0], b[2])
    na, nb = _norm3(a) if not horizontal else _norm2(a), _norm3(b) if not horizontal else _norm2(b)
    if na is None or nb is None:
        return None
    return max(-1.0, min(1.0, sum(x * y for x, y in zip(na, nb))))


def _norm2(v):
    length = math.hypot(v[0], v[1])
    return None if length <= 1.0e-12 else (v[0] / length, v[1] / length)


def _race_geometry(markers):
    points = [marker.position for marker in markers if marker.position is not None]
    segments = [_delta(a, b) for a, b in zip(points, points[1:])]
    lengths3 = [_length(segment) for segment in segments]
    lengths_xz = [_length(segment, True) for segment in segments]
    turns = []
    for first, second in zip(segments, segments[1:]):
        cosine = _cosine(first, second)
        if cosine is not None:
            turns.append(math.degrees(math.acos(cosine)))
    duplicates = sum(length <= 1.0e-6 for length in lengths3)
    distinct = {tuple(round(float(v), 6) for v in point) for point in points}
    route_length = sum(lengths3)
    first_last = _length(_delta(points[0], points[-1])) if len(points) > 1 else 0.0
    alignments = {key: [] for key in (
        "forward_3d", "backward_3d", "central_3d",
        "forward_xz", "backward_xz", "central_xz",
    )}
    for i, marker in enumerate(markers):
        if marker.position is None or marker.direction is None:
            continue
        if i + 1 < len(points):
            tangent = _delta(points[i], points[i + 1])
            for key, value in (("forward_3d", _cosine(marker.direction, tangent)),
                               ("forward_xz", _cosine(marker.direction, tangent, True))):
                if value is not None:
                    alignments[key].append(value)
        if i > 0:
            # The backward tangent points from this marker toward its previous
            # source-order sample. Keep it distinct from the forward tangent.
            tangent = _delta(points[i], points[i - 1])
            for key, value in (("backward_3d", _cosine(marker.direction, tangent)),
                               ("backward_xz", _cosine(marker.direction, tangent, True))):
                if value is not None:
                    alignments[key].append(value)
        if 0 < i < len(points) - 1:
            tangent = _delta(points[i - 1], points[i + 1])
            for key, value in (("central_3d", _cosine(marker.direction, tangent)),
                               ("central_xz", _cosine(marker.direction, tangent, True))):
                if value is not None:
                    alignments[key].append(value)
    return {
        "position_count": len(points),
        "source_order_polyline_length_3d": route_length,
        "source_order_polyline_length_xz": sum(lengths_xz),
        "consecutive_spacing_3d": _stats(lengths3),
        "consecutive_spacing_xz": _stats(lengths_xz),
        "first_to_last_distance_3d": first_last,
        "closure_ratio_to_polyline_length": first_last / route_length if route_length > 0 else None,
        "consecutive_duplicate_count": duplicates,
        "distinct_position_count_1e-6": len(distinct),
        "sharp_turn_count_over_45_degrees": sum(turn > 45.0 for turn in turns),
        "turn_angle_degrees": _stats(turns),
        "direction_alignment_cosine": {key: _stats(values) for key, values in alignments.items()},
        # Kept private by the caller so it can calculate pooled corpus stats
        # without serializing every per-marker scalar into the report.
        "_direction_alignment_samples": alignments,
    }


def _nearest_segment(point, route):
    px, py, pz = point
    best = None
    for i, (a, b) in enumerate(zip(route, route[1:])):
        dx, dz = b[0] - a[0], b[2] - a[2]
        denom = dx * dx + dz * dz
        t = 0.0 if denom <= 1.0e-12 else max(0.0, min(1.0, ((px - a[0]) * dx + (pz - a[2]) * dz) / denom))
        qx, qz = a[0] + t * dx, a[2] + t * dz
        dist_xz = math.hypot(px - qx, pz - qz)
        qy = a[1] + t * (b[1] - a[1])
        dist_3d = math.sqrt((px - qx) ** 2 + (py - qy) ** 2 + (pz - qz) ** 2)
        cross = dx * (pz - qz) - dz * (px - qx)
        candidate = (dist_xz, i, t, dist_3d, cross)
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is None:
        return None
    dist_xz, index, t, dist3, cross = best
    denominator = max(1, len(route) - 1)
    return {
        "progress": (index + t) / denominator,
        "segment_index": index,
        "segment_t": t,
        "distance_xz": dist_xz,
        "distance_3d": dist3,
        "side_cross_xz": cross,
        "side_sign": 0 if abs(cross) < 1.0e-9 else (1 if cross > 0 else -1),
    }


def _marker_extras(marker):
    known = {"Marker Pos", "Marker Dir"}
    return sorted({value.name for value in marker.record.values if value.name not in known})


def _analyse(data_root: Path, exe_path: Path) -> dict:
    sdk = json.loads((REPOSITORY / "research" / "r5t_sdk1" / "retail-corpus-validation.json").read_text(encoding="utf-8"))
    courses = sdk.get("course_projects", [])
    if len(courses) != 36:
        raise ValueError(f"expected 36 curated Retail courses, got {len(courses)}")
    exe_hash = __import__("hashlib").sha256(exe_path.read_bytes()).hexdigest().upper()
    if exe_hash != RETAIL_EXE_SHA256:
        raise ValueError(f"Retail executable SHA256 mismatch: {exe_hash}")
    inventory = {
        name: {"courses": [], "count_by_course": {}, "total_markers": 0, "positions_present": 0,
               "directions_present": 0, "positions_missing": 0, "directions_missing": 0,
               "extra_fields": Counter(), "list_occurrences": 0, "duplicate_named_courses": [],
               "_position_y_by_course": {}}
        for name in LISTS
    }
    race_details = []
    limit_details = []
    camera_details = []
    limit_distance_samples = {name: {"xz": [], "3d": []} for name in LIMITS}
    direction_alignment_samples = {
        key: [] for key in (
            "forward_3d", "backward_3d", "central_3d",
            "forward_xz", "backward_xz", "central_xz",
        )
    }
    for project in courses:
        identity = project["identity"]
        document = parse_course_xml(data_root / project["race_test_xml"])
        names = Counter(item.name for item in document.marker_lists)
        for name in LISTS:
            found = [item for item in document.marker_lists if item.name == name]
            if not found:
                continue
            row = inventory[name]
            row["courses"].append(identity)
            row["list_occurrences"] += len(found)
            row["count_by_course"][identity] = sum(len(item.markers) for item in found)
            position_y = [marker.position[1] for marker_list in found for marker in marker_list.markers
                          if marker.position is not None]
            if position_y:
                row["_position_y_by_course"][identity] = position_y
            if names[name] > 1:
                row["duplicate_named_courses"].append(identity)
            for marker_list in found:
                for marker in marker_list.markers:
                    row["total_markers"] += 1
                    row["positions_present"] += marker.position is not None
                    row["directions_present"] += marker.direction is not None
                    row["positions_missing"] += marker.position is None
                    row["directions_missing"] += marker.direction is None
                    row["extra_fields"].update(_marker_extras(marker))

        race_lists = [item for item in document.marker_lists if item.name == "RaceLine"]
        if race_lists:
            race_markers = tuple(marker for item in race_lists for marker in item.markers)
            geometry = _race_geometry(race_markers)
            for key, values in geometry.pop("_direction_alignment_samples").items():
                direction_alignment_samples[key].extend(values)
            route = [marker.position for marker in race_markers if marker.position is not None]
            race_details.append({"course": identity, "list_occurrences": len(race_lists),
                                 "marker_count": len(race_markers), "geometry": geometry})
            mapped_lists = {}
            for family in LIMITS:
                entries = [item for item in document.marker_lists if item.name == family]
                markers = [marker for item in entries for marker in item.markers]
                projections = [_nearest_segment(marker.position, route) for marker in markers if marker.position is not None]
                for projection in projections:
                    if projection is not None:
                        limit_distance_samples[family]["xz"].append(projection["distance_xz"])
                        limit_distance_samples[family]["3d"].append(projection["distance_3d"])
                mapped_lists[family] = projections
                limit_details.append({
                    "course": identity, "list": family,
                    "marker_count": len(markers), "mapped_count": sum(p is not None for p in projections),
                    "distance_to_raceline_xz": _stats(p["distance_xz"] for p in projections if p),
                    "distance_to_raceline_3d": _stats(p["distance_3d"] for p in projections if p),
                    "progress": _stats(p["progress"] for p in projections if p),
                    "side_sign_counts": dict(Counter(str(p["side_sign"]) for p in projections if p)),
                    "source_order_polyline_length_xz": sum(_length(_delta(a.position, b.position), True)
                                                           for a, b in zip(markers, markers[1:])
                                                           if a.position is not None and b.position is not None),
                })
            for side in ("Left", "Right"):
                inner = mapped_lists[f"{side}InnerLimit"]
                outer = mapped_lists[f"{side}OuterLimit"]
                pairs = []
                for item in inner:
                    if item is None or not outer:
                        continue
                    candidate = min((entry for entry in outer if entry is not None),
                                    key=lambda entry: abs(entry["progress"] - item["progress"]), default=None)
                    if candidate is not None and abs(candidate["progress"] - item["progress"]) <= 0.0125:
                        pairs.append({"progress_delta": abs(candidate["progress"] - item["progress"]),
                                      "inner_distance_xz": item["distance_xz"],
                                      "outer_distance_xz": candidate["distance_xz"],
                                      "outer_farther": candidate["distance_xz"] > item["distance_xz"]})
                limit_details.append({
                    "course": identity, "comparison": f"{side}InnerLimit_vs_{side}OuterLimit",
                    "progress_tolerance": 0.0125, "matched_progress_pairs": len(pairs),
                    "outer_farther_fraction": (sum(item["outer_farther"] for item in pairs) / len(pairs)) if pairs else None,
                    "distance_delta_xz": _stats(item["outer_distance_xz"] - item["inner_distance_xz"] for item in pairs),
                })
        cams = [item for item in document.marker_lists if item.name == "Cameras"]
        if cams:
            markers = [marker for item in cams for marker in item.markers]
            camera_details.append({"course": identity, "marker_count": len(markers),
                                   "positions_present": sum(m.position is not None for m in markers),
                                   "directions_present": sum(m.direction is not None for m in markers),
                                   "extra_fields": sorted({key for m in markers for key in _marker_extras(m)})})

    for name, row in inventory.items():
        counts = list(row["count_by_course"].values())
        row["course_coverage"] = len(row["courses"])
        row["per_course_count"] = {
            "min": min(counts) if counts else None,
            "median": statistics.median(counts) if counts else None,
            "max": max(counts) if counts else None,
        }
        row["count_distribution"] = dict(sorted(Counter(str(value) for value in counts).items(), key=lambda x: int(x[0])))
        row["extra_fields"] = dict(sorted(row["extra_fields"].items()))
        y_by_course = row.pop("_position_y_by_course")
        row["position_y_by_course"] = {
            course: {"min": min(values), "max": max(values), "unique_values": len(set(values))}
            for course, values in sorted(y_by_course.items())
        }
        row["courses_with_constant_position_y"] = sum(
            len(set(values)) == 1 for values in y_by_course.values()
        )
        row["unique_position_y_values"] = len({value for values in y_by_course.values() for value in values})

    limit_rows = [row for row in limit_details if "comparison" not in row]
    limit_comparisons = [row for row in limit_details if "comparison" in row]
    side_summaries = {}
    for name in LIMITS:
        rows = [row for row in limit_rows if row["list"] == name]
        signs = Counter()
        course_dominant_signs = Counter()
        course_dominant_fractions = []
        for row in rows:
            counts = {key: int(value) for key, value in row["side_sign_counts"].items()}
            signs.update(counts)
            total = sum(counts.values())
            if total:
                dominant = max(counts, key=lambda key: counts[key])
                course_dominant_signs[dominant] += 1
                course_dominant_fractions.append(counts[dominant] / total)
        side_summaries[name] = {
            "side_sign_counts": dict(sorted(signs.items())),
            "course_dominant_sign_counts": dict(sorted(course_dominant_signs.items())),
            "mean_per_course_dominant_fraction": statistics.fmean(course_dominant_fractions) if course_dominant_fractions else None,
            "evidence_limit": "signed X/Z side relative to each course's source-order RaceLine tangent; not a runtime left/right label",
        }
    comparison_summaries = {}
    for name in ("LeftInnerLimit_vs_LeftOuterLimit", "RightInnerLimit_vs_RightOuterLimit"):
        rows = [row for row in limit_comparisons if row["comparison"] == name]
        pair_count = sum(row["matched_progress_pairs"] for row in rows)
        weighted_outer_farther = sum(
            round(row["outer_farther_fraction"] * row["matched_progress_pairs"])
            for row in rows
            if row["outer_farther_fraction"] is not None
        )
        comparison_summaries[name] = {
            "course_count": sum(row["matched_progress_pairs"] > 0 for row in rows),
            "matched_progress_pairs": pair_count,
            "outer_farther_pairs": weighted_outer_farther,
            "outer_farther_fraction": weighted_outer_farther / pair_count if pair_count else None,
            "per_course_outer_farther_fraction": _stats(
                row["outer_farther_fraction"] for row in rows if row["outer_farther_fraction"] is not None
            ),
            "distance_delta_xz_per_course_median": _stats(
                row["distance_delta_xz"]["median"] for row in rows if row["distance_delta_xz"]["median"] is not None
            ),
            "progress_tolerance": 0.0125,
        }
    limit_distance_summaries = {}
    for name in LIMITS:
        distances_xz = limit_distance_samples[name]["xz"]
        distances_3d = limit_distance_samples[name]["3d"]
        limit_distance_summaries[name] = {
            "marker_count": len(distances_xz),
            "distance_to_raceline_xz": _stats(distances_xz),
            "distance_to_raceline_3d": _stats(distances_3d),
        }

    raceline_lengths = [row["geometry"]["source_order_polyline_length_xz"] for row in race_details]
    raceline_spacing_medians = [row["geometry"]["consecutive_spacing_xz"]["median"] for row in race_details]
    raceline_closure_ratios = [row["geometry"]["closure_ratio_to_polyline_length"] for row in race_details]
    raceline_duplicate_total = sum(row["geometry"]["consecutive_duplicate_count"] for row in race_details)
    raceline_sharp_turn_total = sum(row["geometry"]["sharp_turn_count_over_45_degrees"] for row in race_details)
    return {
        "schema": "master-rallye-g1-marker-corpus-v1",
        "evidence": "CONFIRMED_BY_CORPUS",
        "retail_executable_sha256": exe_hash,
        "retail_course_count": len(courses),
        "source_selection": "curated Retail course_projects from research/r5t_sdk1; probe-edited parent unpack excluded",
        "source_order_preserved": True,
        "list_inventory": inventory,
        "raceline_courses": race_details,
        "limit_geometry_courses": limit_details,
        "camera_courses": camera_details,
        "raceline_geometry_summary": {
            "course_count": len(race_details),
            "source_order_polyline_length_xz_by_course": _stats(raceline_lengths),
            "median_consecutive_spacing_xz_by_course": _stats(raceline_spacing_medians),
            "first_to_last_over_length_by_course": _stats(raceline_closure_ratios),
            "consecutive_duplicate_count": raceline_duplicate_total,
            "turns_over_45_degrees_total": raceline_sharp_turn_total,
            "direction_alignment_cosine_pooled": {
                key: _stats(values) for key, values in direction_alignment_samples.items()
            },
        },
        "limit_geometry_summary": {
            "per_list_distance_to_raceline": limit_distance_summaries,
            "side_sign_by_list": side_summaries,
            "inner_outer_at_similar_progress": comparison_summaries,
        },
        "semantic_limits": [
            "XML MarkerLists/RaceLine and GXM _raceline/raceline are distinct resources; only static spatial correlation is computed.",
            "Polyline order is literal source order; no nearest-neighbor reordering is applied.",
            "Side sign is the signed X/Z cross product relative to the nearest source-order RaceLine segment; it is not a semantic left/right claim.",
            "Inner/outer comparisons pair nearest route progress only within 0.0125 normalized progress; geometric correlation is not runtime proof.",
        ],
    }


def _md(report: dict) -> str:
    lines = [
        "# G1 Retail RaceTest marker corpus", "",
        f"Evidence: `{report['evidence']}`; courses: {report['retail_course_count']}; Retail EXE SHA256: `{report['retail_executable_sha256']}`.",
        "Source order is preserved. These reports describe structure and geometry, not semantics inferred from names.", "",
        "## Marker-list inventory", "",
        "| List | Coverage | Total markers | Per-course min / median / max | Pos | Dir | Extra fields |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for name, row in report["list_inventory"].items():
        dist = row["per_course_count"]
        lines.append(f"| `{name}` | {row['course_coverage']}/36 | {row['total_markers']} | {dist['min']} / {dist['median']} / {dist['max']} | {row['positions_present']} present, {row['positions_missing']} missing | {row['directions_present']} present, {row['directions_missing']} missing | {', '.join(row['extra_fields']) or 'none'} |")
    lines += ["", "## RaceLine geometry", "", "| Course | Count | Length X/Z | Spacing X/Z min / median / max | First-last / length | duplicates | turns >45° | Dir central X/Z median cosine |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in report["raceline_courses"]:
        g = row["geometry"]
        s = g["consecutive_spacing_xz"]
        d = g["direction_alignment_cosine"]["central_xz"]["median"]
        lines.append(f"| {row['course']} | {row['marker_count']} | {g['source_order_polyline_length_xz']:.2f} | {s['min']:.2f} / {s['median']:.2f} / {s['max']:.2f} | {g['closure_ratio_to_polyline_length']:.4f} | {g['consecutive_duplicate_count']} | {g['sharp_turn_count_over_45_degrees']} | {d if d is not None else 'n/a'} |")
    summary = report["raceline_geometry_summary"]
    lines += ["", "## Marker Dir versus source-order tangents", "", "Pooled over all present marker directions. Cosine is measured after the documented common course-to-Blender axis rotation; comparisons remain geometric and do not establish runtime use of `Marker Dir`.", "", "| Tangent | Dimension | Samples | Min | Median | Mean | P05 | P95 | Max |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for tangent in ("forward", "backward", "central"):
        for dimension in ("3d", "xz"):
            stats = summary["direction_alignment_cosine_pooled"][f"{tangent}_{dimension}"]
            lines.append(f"| {tangent} | {dimension.upper()} | {stats['count']} | {stats['min']:.4f} | {stats['median']:.4f} | {stats['mean']:.4f} | {stats['p05']:.4f} | {stats['p95']:.4f} | {stats['max']:.4f} |")
    limit_summary = report["limit_geometry_summary"]
    lines += ["", "## Limit-to-route geometry", "", "Positions are projected onto the nearest source-order RaceLine segment in X/Z. Distances in 3D are also retained because some lists use course-dependent Y values. Retail executable helper `0x004CE140` selects the nearest marker by 3D distance; for all four France1 limit lists Y is constant at 280.3, so the per-list nearest-marker ordering there reduces to X/Z distance. That statement does not generalize to all 36 courses. Side signs use each course's ordered route tangent and are not runtime labels.", "", "| List | Markers | Y constant courses | X/Z distance median (min–max) | 3D distance median (min–max) | dominant side by course | mean dominant fraction |", "|---|---:|---:|---:|---:|---|---:|"]
    for name in LIMITS:
        entry = limit_summary["per_list_distance_to_raceline"][name]
        side = limit_summary["side_sign_by_list"][name]
        xz, d3 = entry["distance_to_raceline_xz"], entry["distance_to_raceline_3d"]
        constant_y_courses = report["list_inventory"][name]["courses_with_constant_position_y"]
        lines.append(f"| {name} | {entry['marker_count']} | {constant_y_courses}/36 | {xz['median']:.2f} ({xz['min']:.2f}–{xz['max']:.2f}) | {d3['median']:.2f} ({d3['min']:.2f}–{d3['max']:.2f}) | {side['course_dominant_sign_counts']} | {side['mean_per_course_dominant_fraction']:.4f} |")
    lines += ["", "| Inner/outer comparison | Courses | matched progress pairs | Outer farther | per-course fraction median | distance delta X/Z median of per-course medians |", "|---|---:|---:|---:|---:|---:|"]
    for name, entry in limit_summary["inner_outer_at_similar_progress"].items():
        delta = entry["distance_delta_xz_per_course_median"]["median"]
        lines.append(f"| {name} | {entry['course_count']} | {entry['matched_progress_pairs']} | {entry['outer_farther_pairs']}/{entry['matched_progress_pairs']} ({entry['outer_farther_fraction']:.3%}) | {entry['per_course_outer_farther_fraction']['median']:.3%} | {delta:.2f} |")
    lines += ["", "## Bounded interpretation", "", *[f"- {item}" for item in report["semantic_limits"]], ""]
    return "\n".join(lines)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=REPOSITORY.parent / "corpora" / "retail" / "Data.sma_unpacked")
    parser.add_argument("--exe", type=Path, default=REPOSITORY.parent / "corpora" / "retail" / "MRallye.exe")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY / "research" / "g1")
    args = parser.parse_args()
    report = _analyse(args.data_root.resolve(), args.exe.resolve())
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "marker-corpus.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "raceline-corpus.json").write_text(json.dumps({"schema": report["schema"], "evidence": report["evidence"], "retail_course_count": report["retail_course_count"], "retail_executable_sha256": report["retail_executable_sha256"], "list_inventory": {"RaceLine": report["list_inventory"]["RaceLine"]}, "geometry_summary": report["raceline_geometry_summary"], "courses": report["raceline_courses"], "semantic_limits": report["semantic_limits"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "limits-corpus.json").write_text(json.dumps({"schema": report["schema"], "evidence": report["evidence"], "retail_course_count": report["retail_course_count"], "retail_executable_sha256": report["retail_executable_sha256"], "lists": {key: report["list_inventory"][key] for key in LIMITS}, "geometry_summary": report["limit_geometry_summary"], "course_geometry": [row for row in report["limit_geometry_courses"] if "comparison" not in row], "matched_inner_outer_progress_comparisons": [row for row in report["limit_geometry_courses"] if "comparison" in row], "semantic_limits": report["semantic_limits"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "marker-corpus.md").write_text(_md(report), encoding="utf-8")
    print(f"Retail courses={report['retail_course_count']}; lists={len(report['list_inventory'])}; output={out}")
    for name, row in report["list_inventory"].items():
        print(f"{name}: coverage={row['course_coverage']}/36 total={row['total_markers']} counts={row['per_course_count']} Pos={row['positions_present']} Dir={row['directions_present']} extras={row['extra_fields']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
