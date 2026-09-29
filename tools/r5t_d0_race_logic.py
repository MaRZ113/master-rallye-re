#!/usr/bin/env python3
"""Build a read-only structural/spatial RaceTest XML report for R5T-D.0."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from master_rallye.course_xml import CourseXmlEgg, CourseXmlMarker, CourseXmlMarkerList, parse_course_xml  # noqa: E402


THRESHOLDS = (5, 10, 20, 40, 80, 150)


def _distance(a, b, dimensions: int = 3) -> float:
    if dimensions == 2:
        return math.hypot(float(a[0]) - float(b[0]), float(a[2]) - float(b[2]))
    return math.dist(a[:dimensions], b[:dimensions])


def _mean(points):
    points = [tuple(map(float, point[:3])) for point in points]
    if not points:
        return None
    return [sum(point[axis] for point in points) / len(points) for axis in range(3)]


def _value_map(component) -> dict[str, str]:
    return {item.name: item.value for item in component.values}


def _matrix_dict(matrix):
    if matrix is None:
        return None
    return {
        "name": matrix.name,
        "type": matrix.type_name,
        "attributes": dict(matrix.attributes),
        "rows_float": [list(row) if row is not None else None for row in matrix.rows],
        "position_xyz": list(matrix.position) if matrix.position is not None else None,
        "issues": list(matrix.issues),
    }


def _marker_dict(marker: CourseXmlMarker) -> dict:
    return {
        "list_name": marker.marker_list_name,
        "list_ordinal": marker.marker_list_ordinal,
        "index_in_list": marker.index_in_list,
        "ordinal": marker.ordinal,
        "no": marker.marker_no,
        "type": marker.marker_type,
        "position_xyz": list(marker.position) if marker.position is not None else None,
        "direction_xyz": list(marker.direction) if marker.direction is not None else None,
        "raw_position": marker.raw_position,
        "raw_direction": marker.raw_direction,
        "xml_path": marker.record.xml_path,
        "issues": list(marker.issues),
        "record_attributes": dict(marker.record.attributes),
        "values": [
            {"name": value.name, "type": value.type_name, "value": value.value,
             "attributes": dict(value.attributes)}
            for value in marker.record.values
        ],
    }


def _marker_summary(marker: CourseXmlMarker) -> dict:
    """Compact location record used when a full Marker record is not needed."""
    return {
        "list_name": marker.marker_list_name,
        "list_ordinal": marker.marker_list_ordinal,
        "index_in_list": marker.index_in_list,
        "ordinal": marker.ordinal,
        "no": marker.marker_no,
        "type": marker.marker_type,
        "position_xyz": list(marker.position) if marker.position is not None else None,
        "direction_xyz": list(marker.direction) if marker.direction is not None else None,
        "raw_position": marker.raw_position,
        "raw_direction": marker.raw_direction,
        "xml_path": marker.record.xml_path,
        "issues": list(marker.issues),
    }


def _marker_list_item(marker: CourseXmlMarker) -> dict:
    return {
        "index": marker.index_in_list,
        "no": marker.marker_no,
        "type": marker.marker_type,
        "position_xyz": list(marker.position) if marker.position is not None else None,
        "direction_xyz": list(marker.direction) if marker.direction is not None else None,
        "raw_position": marker.raw_position,
        "raw_direction": marker.raw_direction,
        "issues": list(marker.issues),
    }


def _area_report(marker_list: CourseXmlMarkerList | None) -> dict | None:
    if marker_list is None:
        return None
    positions = [marker.position for marker in marker_list.markers if marker.position is not None]
    centroid = _mean(positions)
    xz = [(point[0], point[2]) for point in positions]
    ordered_area = None
    turns = []
    edge_lengths = []
    if len(positions) >= 3:
        ordered_area = 0.5 * sum(
            positions[index][0] * positions[(index + 1) % len(positions)][2]
            - positions[(index + 1) % len(positions)][0] * positions[index][2]
            for index in range(len(positions))
        )
        if len(positions) == len(marker_list.markers):
            for index in range(len(positions)):
                a, b, c = positions[index], positions[(index + 1) % len(positions)], positions[(index + 2) % len(positions)]
                turns.append((b[0] - a[0]) * (c[2] - b[2]) - (b[2] - a[2]) * (c[0] - b[0]))
                edge_lengths.append(_distance(a, b))
    nonzero_turns = [value for value in turns if abs(value) > 1.0e-8]
    convex_source_order = len(nonzero_turns) == len(positions) and (
        all(value > 0 for value in nonzero_turns) or all(value < 0 for value in nonzero_turns)
    ) if positions else False
    return {
        "list_name": marker_list.name,
        "list_ordinal": marker_list.ordinal,
        "xml_path": marker_list.xml_path,
        "marker_count": len(marker_list.markers),
        "valid_position_count": len(positions),
        "centroid_xyz": centroid,
        "local_xz_bounds": {
            "min_x": min((point[0] for point in xz), default=None),
            "max_x": max((point[0] for point in xz), default=None),
            "min_z": min((point[1] for point in xz), default=None),
            "max_z": max((point[1] for point in xz), default=None),
        },
        "source_order_xz_signed_area": ordered_area,
        "source_order_convex_turn_test": convex_source_order,
        "source_order_edge_lengths_3d": edge_lengths,
        "source_order_turn_values_xz": turns,
        "markers": [
            _marker_dict(marker) if marker_list.name in {"StartArea", "FinishArea"}
            else _marker_list_item(marker)
            for marker in marker_list.markers
        ],
    }


def _egg_dict(egg: CourseXmlEgg) -> dict:
    components = []
    for ai in egg.ai_objects:
        components.append({
            "ordinal": ai.ordinal,
            "ai_no": ai.ai_no,
            "ai_name": ai.ai_name,
            "xml_path": ai.xml_path,
            "attributes": dict(ai.attributes),
            "values": [
                {"name": value.name, "type": value.type_name, "value": value.value,
                 "attributes": dict(value.attributes)}
                for value in ai.values
            ],
            "components": [
                {
                    "tag": item.tag,
                    "xml_path": item.xml_path,
                    "attributes": dict(item.attributes),
                    "values": [
                        {"name": value.name, "type": value.type_name, "value": value.value,
                         "attributes": dict(value.attributes)}
                        for value in item.values
                    ],
                }
                for item in ai.components
            ],
        })
    return {
        "egg_name": egg.name,
        "egg_list_name": egg.list_name,
        "egg_list_ordinal": egg.list_ordinal,
        "egg_index_in_list": egg.index_in_list,
        "egg_ordinal": egg.ordinal,
        "model_name": egg.model_name,
        "xml_path": egg.xml_path,
        "attributes": dict(egg.attributes),
        "values": [
            {"name": value.name, "type": value.type_name, "value": value.value,
             "attributes": dict(value.attributes)}
            for value in egg.values
        ],
        "matrices": [_matrix_dict(matrix) for matrix in egg.matrices],
        "ai_objects": components,
    }


def _egg_location_summary(egg: CourseXmlEgg) -> dict:
    matrix = egg.matrix("en3d Matrix")
    return {
        "egg_ordinal": egg.ordinal,
        "egg_name": egg.name,
        "egg_list_name": egg.list_name,
        "egg_index_in_list": egg.index_in_list,
        "model_name": egg.model_name,
        "position_xyz": list(matrix.position) if matrix and matrix.position is not None else None,
        "ai_components": [
            {"ai_no": ai.ai_no, "ai_name": ai.ai_name, "component_tags": [item.tag for item in ai.components]}
            for ai in egg.ai_objects
        ],
        "xml_path": egg.xml_path,
    }


def _nearby_markers(position, markers):
    positioned = [marker for marker in markers if marker.position is not None]
    sorted3 = sorted(positioned, key=lambda marker: (_distance(position, marker.position), marker.ordinal))
    sorted_xz = sorted(positioned, key=lambda marker: (_distance(position, marker.position, 2), marker.ordinal))
    thresholds = {}
    for threshold in THRESHOLDS:
        hits = [marker for marker in positioned if _distance(position, marker.position) <= threshold]
        thresholds[str(threshold)] = {
            "count_3d": len(hits),
            "by_marker_list": dict(sorted(Counter(marker.marker_list_name or "<unlisted>" for marker in hits).items())),
        }
    return {
        "threshold_counts_3d": thresholds,
        "nearest_3d": [
            {"distance": _distance(position, marker.position), "marker": _marker_summary(marker)}
            for marker in sorted3[:12]
        ],
        "nearest_xz": [
            {"distance": _distance(position, marker.position, 2), "marker": _marker_summary(marker)}
            for marker in sorted_xz[:8]
        ],
        "nearest_by_list": {
            name: [
                {"distance": _distance(position, marker.position), "marker": _marker_summary(marker)}
                for marker in sorted(
                    (item for item in positioned if item.marker_list_name == name),
                    key=lambda item: (_distance(position, item.position), item.index_in_list),
                )[:5]
            ]
            for name in sorted({item.marker_list_name for item in positioned if item.marker_list_name})
        },
    }


def _split_report(egg: CourseXmlEgg, doc) -> dict:
    component = egg.split_time_component
    values = _value_map(component) if component is not None else {}
    raw_id = values.get("Split Time ID")
    split_id = int(raw_id) if raw_id is not None and raw_id.lstrip("+-").isdigit() else None
    visual_matrix = egg.matrix("en3d Matrix")
    visual_position = visual_matrix.position if visual_matrix is not None else None
    companions = []
    if split_id is not None:
        prefix = f"SplitTime{split_id}-"
        companions = [
            other for other in doc.eggs
            if other.list_name == egg.list_name and other.name and other.name.startswith(prefix)
        ]
    companion_positions = [item.matrix("en3d Matrix").position for item in companions if item.matrix("en3d Matrix") and item.matrix("en3d Matrix").position]
    companion_centroid = _mean(companion_positions)
    try:
        radius = float(values["Radius"]) if "Radius" in values else None
    except ValueError:
        radius = None
    companion_distances = [
        _distance(companion_centroid, position)
        for position in companion_positions
    ] if companion_centroid else []
    race_line = doc.marker_list("RaceLine")
    race_line_near = []
    if visual_position is not None and race_line is not None:
        race_line_near = sorted(
            (marker for marker in race_line.markers if marker.position is not None),
            key=lambda marker: (_distance(visual_position, marker.position), marker.index_in_list),
        )[:8]
    nearby_eggs = []
    if visual_position is not None:
        for other in doc.eggs:
            matrix = other.matrix("en3d Matrix")
            if other is egg or matrix is None or matrix.position is None:
                continue
            nearby_eggs.append({"distance_3d": _distance(visual_position, matrix.position), "egg": _egg_location_summary(other)})
        nearby_eggs.sort(key=lambda item: (item["distance_3d"], item["egg"]["egg_ordinal"]))

    return {
        "split_id": split_id,
        "split_id_raw": raw_id,
        "visual_egg": _egg_dict(egg),
        "visual_en3d_matrix": _matrix_dict(visual_matrix),
        "visual_position_xyz": list(visual_position) if visual_position is not None else None,
        "radius_raw": values.get("Radius"),
        "radius": radius,
        "extra_time_raw": values.get("ExtraTime"),
        "extra_time": values.get("ExtraTime"),
        "gameplay_trigger_position": None,
        "gameplay_trigger_position_status": "UNKNOWN",
        "marker_proximity": _nearby_markers(visual_position, doc.markers) if visual_position is not None else None,
        "nearest_raceline_markers": [
            {"distance_3d": _distance(visual_position, marker.position), "index": marker.index_in_list,
             "no": marker.marker_no, "position_xyz": list(marker.position), "direction_xyz": list(marker.direction) if marker.direction else None,
             "xml_path": marker.record.xml_path}
            for marker in race_line_near
        ],
        "same_list_split_companion_eggs": [_egg_dict(item) for item in companions],
        "companion_group_analysis": {
            "candidate_only": True,
            "point_count": len(companion_positions),
            "centroid_xyz": companion_centroid,
            "centroid_to_visual_distance_3d": _distance(companion_centroid, visual_position) if companion_centroid and visual_position else None,
            "centroid_offset_from_visual_xyz": [companion_centroid[i] - visual_position[i] for i in range(3)] if companion_centroid and visual_position else None,
            "centroid_corner_distance_3d": companion_distances,
            "corner_radius_min_max": [min(companion_distances), max(companion_distances)] if companion_distances else None,
            "radius_minus_corner_distance": [radius - item for item in companion_distances] if radius is not None else None,
            "relation_to_radius_is_structural_correlation_only": True,
        },
        "nearby_eggs_by_visual_position": nearby_eggs[:12],
        "evidence": {
            "visual_en3d_row3_is_marker_position": "CONFIRMED_BY_RUNTIME_EDIT",
            "visual_en3d_row3_is_gameplay_trigger_center": "REJECTED / NOT SUPPORTED by controlled edit",
            "radius_affects_split_trigger_extent": "CONFIRMED_BY_RUNTIME_EDIT",
            "trigger_center": "UNKNOWN",
        },
    }


def _retail_corpus_summary(directory: Path | None) -> dict | None:
    if directory is None:
        return None
    files = sorted(directory.rglob("*.xml"))
    parsed = []
    parse_failures = []
    split_egg_counts = Counter()
    split_component_counts = Counter()
    radii = []
    extra_times = []
    start_area_count = finish_area_count = split_ai_count = 0
    split_courses = []
    for path in files:
        try:
            document = parse_course_xml(path)
        except Exception as error:  # report corpus outliers rather than hiding them
            parse_failures.append({"file": path.name, "error": str(error)})
            continue
        splits = document.split_time_eggs
        split_records = document.split_time_records
        split_egg_counts[len(splits)] += 1
        split_component_counts[len(split_records)] += 1
        start = document.marker_list("StartArea")
        finish = document.marker_list("FinishArea")
        start_area_count += start is not None
        finish_area_count += finish is not None
        split_ai_count += bool(split_records)
        for record in split_records:
            values = _value_map(record)
            try:
                radii.append(float(values["Radius"]))
            except (KeyError, ValueError):
                pass
            try:
                extra_times.append(float(values["ExtraTime"]))
            except (KeyError, ValueError):
                pass
        if split_records or splits:
            split_courses.append({
                "file": path.name,
                "split_component_count": len(split_records),
                "split_egg_count": len(splits),
                "split_ids": [
                    record.value("Split Time ID").value if record.value("Split Time ID") else None
                    for record in split_records
                ],
            })
        parsed.append(path.name)
    return {
        "directory_relative_to_user_corpus": "retail/Data.sma_unpacked/DataScene/RaceTest",
        "xml_file_count": len(files),
        "parsed_xml_count": len(parsed),
        "parse_failures": parse_failures,
        "start_area_course_xml_count": start_area_count,
        "finish_area_course_xml_count": finish_area_count,
        "xml_files_with_split_time_ai": split_ai_count,
        "split_time_component_count_distribution": {
            str(key): value for key, value in sorted(split_component_counts.items())
        },
        "split_time_egg_count_distribution": {
            str(key): value for key, value in sorted(split_egg_counts.items())
        },
        "radius_range": [min(radii), max(radii)] if radii else None,
        "radius_observation_count": len(radii),
        "extra_time_range": [min(extra_times), max(extra_times)] if extra_times else None,
        "extra_time_observation_count": len(extra_times),
        "files_with_split_time_ai": split_courses,
    }


def build_report(xml_path: Path, retail_directory: Path | None) -> dict:
    data = xml_path.read_bytes()
    document = parse_course_xml(xml_path)
    marker_list_payload = [_area_report(item) for item in document.marker_lists]
    marker_list_by_name = {item.name: item for item in document.marker_lists}
    start_area = _area_report(marker_list_by_name.get("StartArea"))
    finish_area = _area_report(marker_list_by_name.get("FinishArea"))
    splits = [_split_report(egg, document) for egg in document.split_time_eggs]
    return {
        "report": "R5T-D.0 France1 RaceTest XML structure and spatial correlation",
        "evidence_scope": "Static XML structure plus user-provided runtime-edit observations; static spatial correlation does not prove trigger linkage.",
        "source": {"file": xml_path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "root_tag": document.root_tag},
        "hierarchy": {
            "root_tag": document.root_tag,
            "root_child_order": [child.tag for child in document.root.children],
            "egg_list_names_in_source_order": [child.attribute("Name") for child in document.root.children if child.tag == "EggLists_Version4" for child in child.children],
            "marker_list_names_in_source_order": [item.name for item in document.marker_lists],
            "egg_count": len(document.eggs),
            "marker_count": len(document.markers),
            "split_component_record_count": len(document.split_time_records),
        },
        "start_area": start_area,
        "finish_area": finish_area,
        "marker_lists": marker_list_payload,
        "split_events": splits,
        "correlation_findings": {
            "split_companion_group_candidate": {
                "status": "HIGH_CONFIDENCE_INFERENCE; NOT RUNTIME CONFIRMED",
                "basis": [
                    "each of SplitTime0/1/2 has four sibling eggs named SplitTimeN-0 through SplitTimeN-3 in the SplitTimes list",
                    "the four Row3 positions form a compact repeated group whose centroid is within 2.426 source units of its main SplitTimeN visual egg",
                    "their centroid-to-corner distances closely track the corresponding Radius values for all three splits",
                    "the main visual egg was moved alone; its yellow visual marker moved but its gameplay trigger stayed at the old course location",
                ],
                "interpretation_limit": "This supports the four sibling transforms as a gameplay-trigger spatial candidate. It does not prove that they are read by gaRaceSplitTimeAI or define a gate/volume.",
            },
            "raceline_candidate": {
                "status": "PLAUSIBLE SPATIAL CORRELATION; NOT RUNTIME CONFIRMED",
                "basis": "The nearest RaceLine marker to SplitTime0/1/2 visual positions is respectively index 112/224/336 at distances approximately 6.181/4.834/0.000; the repeated 112-index spacing is a structural correlation only.",
                "interpretation_limit": "No controlled RaceLine edit or XML reference binds these markers to split triggers.",
            },
            "runtime_evidence": {
                "StartArea_translation_rotation_scale_and_heading": "CONFIRMED_BY_RUNTIME_EDIT",
                "FinishArea_controls_or_contributes_to_race_completion_region": "CONFIRMED_BY_RUNTIME_EDIT; not proven sole finish subsystem",
                "split_radius_changes_trigger_extent": "CONFIRMED_BY_RUNTIME_EDIT",
                "split_egg_row3_is_visual_position": "CONFIRMED_BY_RUNTIME_EDIT",
                "split_egg_row3_is_gameplay_trigger_center": "REJECTED / NOT SUPPORTED",
                "split_trigger_center": "UNKNOWN",
                "ExtraTime_semantics": "UNKNOWN",
            },
        },
        "retail_corpus_summary": _retail_corpus_summary(retail_directory),
    }


def _point(point):
    return "UNKNOWN" if point is None else "(" + ", ".join(f"{item:.3f}" for item in point) + ")"


def render_markdown(report: dict) -> str:
    lines = [
        "# France1 RaceTest XML race-logic inventory",
        "",
        f"Source: `{report['source']['file']}` ({report['source']['bytes']:,} bytes, SHA-256 `{report['source']['sha256']}`).",
        "",
        f"Parsed {report['hierarchy']['marker_count']} Marker records in {len(report['marker_lists'])} source-ordered MarkerLists and {report['hierarchy']['egg_count']} Eggs. The XML tree and all marker positions/directions are preserved in the companion JSON.",
        "",
        "## Area lists",
        "",
        "| List | Markers | Centroid (source XYZ) | Local X bounds | Local Z bounds | Ordered XZ outline |",
        "|---|---:|---|---|---|---|",
    ]
    for area in (report["start_area"], report["finish_area"]):
        if area is None:
            continue
        bounds = area["local_xz_bounds"]
        lines.append(
            f"| {area['list_name']} | {area['marker_count']} | {_point(area['centroid_xyz'])} | "
            f"{bounds['min_x']:.3f} … {bounds['max_x']:.3f} | {bounds['min_z']:.3f} … {bounds['max_z']:.3f} | "
            f"convex source order: {str(area['source_order_convex_turn_test']).lower()} |"
        )
    lines += [
        "",
        "### Source-order area positions",
        "",
    ]
    for area_index, area in enumerate((report["start_area"], report["finish_area"])):
        if area is None:
            continue
        if area_index:
            lines.append("")
        lines.append(f"**{area['list_name']}**")
        for marker in area["markers"]:
            lines.append(f"- Marker {marker['index_in_list']} (No {marker['no']}): Pos `{marker['raw_position']}`, Dir `{marker['raw_direction']}`")
    lines += [
        "",
        "Runtime edits confirm StartArea moves/rotates/scales the physical start grid and its heading. FinishArea expansion made race completion occur earlier. These are runtime observations from the project owner; neither list is asserted to be the only related subsystem.",
        "",
        "## Split visual objects and spatial candidates",
        "",
        "| Split ID | Visual Egg Row3 | Radius | ExtraTime | nearest RaceLine marker (distance) | 4-point group centroid to visual | group corner distance range |",
        "|---:|---|---:|---:|---|---:|---|",
    ]
    for split in report["split_events"]:
        nearest = split["nearest_raceline_markers"][0] if split["nearest_raceline_markers"] else None
        group = split["companion_group_analysis"]
        corner_range = group["corner_radius_min_max"]
        lines.append(
            f"| {split['split_id']} | {_point(split['visual_position_xyz'])} | {split['radius_raw']} | {split['extra_time_raw']} | "
            f"{nearest['index']} ({nearest['distance_3d']:.3f}) | {group['centroid_to_visual_distance_3d']:.3f} | "
            f"{corner_range[0]:.3f} … {corner_range[1]:.3f} |"
        )
    lines += [
        "",
        "The visual Egg's `en3d Matrix` Row3 is **CONFIRMED_BY_RUNTIME_EDIT** as the yellow sign position. Moving it alone moved the sign but left the gameplay trigger at the old location; Row3 as trigger center is therefore **REJECTED / NOT SUPPORTED**. Radius changes the event's trigger extent (**CONFIRMED_BY_RUNTIME_EDIT**), but the trigger center remains **UNKNOWN**.",
        "",
        "### Strongest next trigger-position candidate",
        "",
        "The strongest static candidate is the repeated four-Egg sibling group `SplitTimes/SplitTimeN-0 … SplitTimeN-3`, considered as a group rather than any single Egg. Across IDs 0, 1, and 2, the four Row3 points form a compact cluster; their centroid is within 0.253, 2.426, and 1.033 units of the corresponding visual Egg, and their centroid-to-corner radii closely track Radius values 21, 13, and 12. This is a **HIGH_CONFIDENCE_INFERENCE candidate only**: no XML reference or runtime edit has yet bound these transforms to `gaRaceSplitTimeAI`.",
        "",
        "The nearest RaceLine markers are a separate plausible correlate: indices 112, 224, 336, respectively, with visual-position distances 6.181, 4.834, and 0.000. Their regular spacing is not proof of a trigger link. The next test should move only the four SplitTime0 sibling Egg Row3 XYZ values by one common translation to the StartArea centroid, keeping the visual SplitTime0 Egg and RaceLine unchanged.",
        "",
        "If the event moves, the four-point group is linked to trigger placement. If the event remains at the original split, that group is not sufficient; the unchanged RaceLine candidate or another structure remains open. The four sibling Eggs may be visible course objects, so the test may also relocate their corresponding objects. Do not interpret that visual movement as the trigger result; judge the split event separately.",
        "",
        "## Retail RaceTest XML corpus",
        "",
    ]
    corpus = report.get("retail_corpus_summary")
    if corpus:
        lines += [
            f"Scanned {corpus['xml_file_count']} XML files: {corpus['parsed_xml_count']} parsed; {len(corpus['parse_failures'])} failures.",
            f"StartArea: {corpus['start_area_course_xml_count']} files; FinishArea: {corpus['finish_area_course_xml_count']} files; files with split AI: {corpus['xml_files_with_split_time_ai']}.",
            f"Split component-record count distribution: `{json.dumps(corpus['split_time_component_count_distribution'], sort_keys=True)}`.",
            f"Split Egg count distribution: `{json.dumps(corpus['split_time_egg_count_distribution'], sort_keys=True)}`.",
            f"Radius range: {corpus['radius_range']}; ExtraTime range: {corpus['extra_time_range']}. These are corpus ranges only; no additional runtime semantics are inferred.",
        ]
        if corpus["parse_failures"]:
            lines.append("Parse failures: " + "; ".join(f"{item['file']}: {item['error']}" for item in corpus["parse_failures"]))
    else:
        lines.append("Corpus scan was not run.")
    lines += [
        "",
        "## Evidence boundary",
        "",
        "- StartArea grid translation/orientation/scale and heading: **CONFIRMED_BY_RUNTIME_EDIT**.",
        "- FinishArea contribution to completion region: **CONFIRMED_BY_RUNTIME_EDIT**; not proven exclusive.",
        "- Split Radius affects trigger extent: **CONFIRMED_BY_RUNTIME_EDIT**.",
        "- Split visual transform vs gameplay trigger: separate; visual position confirmed, trigger position **UNKNOWN**.",
        "- `ExtraTime` semantics: **UNKNOWN**.",
        "- Runtime version participant-to-slot order: not analyzed in this phase.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    default_xml = REPOSITORY.parent / "corpora" / "retail" / "Data.sma_unpacked" / "DataScene" / "RaceTest" / "France1.xml"
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=Path, default=default_xml)
    parser.add_argument("--retail-dir", type=Path, default=default_xml.parent)
    parser.add_argument("--json", type=Path, default=REPOSITORY / "research" / "r5t_d0" / "france1-race-logic.json")
    parser.add_argument("--markdown", type=Path, default=REPOSITORY / "research" / "r5t_d0" / "france1-race-logic.md")
    args = parser.parse_args()
    report = build_report(args.xml.resolve(), args.retail_dir.resolve() if args.retail_dir and args.retail_dir.exists() else None)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "source": report["source"],
        "marker_count": report["hierarchy"]["marker_count"],
        "marker_lists": report["hierarchy"]["marker_list_names_in_source_order"],
        "split_count": len(report["split_events"]),
        "retail_corpus": report["retail_corpus_summary"],
        "json": str(args.json),
        "markdown": str(args.markdown),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
