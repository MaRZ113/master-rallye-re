#!/usr/bin/env python3
"""Validate RaceTest no-op exports and France1 allowlisted edit scenarios."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from master_rallye.course_race_authoring import CourseRaceLogicAuthoring  # noqa: E402


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_corpus(data_root: Path) -> dict:
    course_root = data_root / "DataGx" / "Course"
    folders = sorted((item for item in course_root.iterdir() if item.is_dir()), key=lambda item: item.name.casefold())
    sdk_inventory_path = REPOSITORY / "research" / "r5t_sdk1" / "retail-corpus-validation.json"
    sdk_inventory = json.loads(sdk_inventory_path.read_text(encoding="utf-8"))
    project_rows = {item["identity"].casefold(): item for item in sdk_inventory["course_projects"]}
    if len(project_rows) != 36 or {item.name.casefold() for item in folders} != set(project_rows):
        raise ValueError("current Retail folders do not match the 36 HNT-linked CourseProject inventory")
    split_counts: Counter[int] = Counter()
    companion_counts: Counter[int] = Counter()
    companion_counts_per_split: Counter[int] = Counter()
    radius_values: list[float] = []
    courses = []
    errors = []
    supported_start = supported_finish = supported_splits = no_op_byte_identity = 0
    supported_companions = total_companions = total_splits = 0
    unusual_companion_layouts = []

    for folder in folders:
        try:
            project = project_rows[folder.name.casefold()]
            xml_path = data_root / project["race_test_xml"]
            if not xml_path.is_file():
                raise FileNotFoundError(f"CourseProject-linked RaceTest XML is missing: {project['race_test_xml']}")
            source = xml_path.read_bytes()
            editor = CourseRaceLogicAuthoring(source, str(xml_path))
            output, export_report = editor.export()
            byte_identical = output == source
            if not byte_identical or export_report.changed_semantic_paths:
                raise ValueError("zero-edit RaceTest export was not byte-identical")
            no_op_byte_identity += 1
            area_status = {item.name: item for item in editor.area_status}
            supported_start += int(area_status["StartArea"].supported)
            supported_finish += int(area_status["FinishArea"].supported)
            supported_splits += sum(item.supported for item in editor.split_status)
            total_splits += len(editor.split_status)
            split_counts[len(editor.split_status)] += 1
            radius_values.extend(item.radius for item in editor.split_status if item.radius is not None)
            companion_status_by_split: dict[str, list] = {}
            for companion in editor.visual_companion_status:
                companion_status_by_split.setdefault(companion.split_identity, []).append(companion)
                supported_companions += int(companion.supported)
                total_companions += 1
            course_companion_count = 0
            course_companion_records = []
            for split in editor.split_status:
                companions = companion_status_by_split.get(split.identity, [])
                companion_counts_per_split[len(companions)] += 1
                names = [item.egg_name for item in companions]
                course_companion_count += len(companions)
                course_companion_records.append({
                    "split_egg": split.egg_name,
                    "count": len(companions),
                    "supported_count": sum(item.supported for item in companions),
                })
                expected_names = [f"{split.egg_name}-{index}" for index in range(len(companions))]
                if names != expected_names or len(companions) != 4:
                    unusual_companion_layouts.append({
                        "course_identity": project["identity"],
                        "split_egg": split.egg_name,
                        "names": names,
                        "count": len(companions),
                    })
            companion_counts[sum(len(items) for items in companion_status_by_split.values())] += 1
            courses.append({
                "course_identity": project["identity"],
                "race_test_xml": xml_path.relative_to(data_root).as_posix(),
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "parse_status": "PASS",
                "no_op_export": "BYTE_IDENTICAL",
                "start_area": {
                    "present": area_status["StartArea"].present,
                    "marker_count": area_status["StartArea"].marker_count,
                    "authoring_supported": area_status["StartArea"].supported,
                    "issues": list(area_status["StartArea"].issues),
                },
                "finish_area": {
                    "present": area_status["FinishArea"].present,
                    "marker_count": area_status["FinishArea"].marker_count,
                    "authoring_supported": area_status["FinishArea"].supported,
                    "issues": list(area_status["FinishArea"].issues),
                },
                "split_count": len(editor.split_status),
                "supported_split_count": sum(item.supported for item in editor.split_status),
                "visual_companion_count": course_companion_count,
                "supported_visual_companion_count": sum(
                    item.supported for item in editor.visual_companion_status
                ),
                "split_visual_companions": course_companion_records,
                "unsupported_splits": [
                    {"identity": item.identity, "issues": list(item.issues)}
                    for item in editor.split_status if not item.supported
                ],
            })
        except Exception as error:
            errors.append({"course_folder": folder.name, "error": str(error)})

    return {
        "schema": "course-race-logic-authoring-corpus-validation-v1",
        "evidence": "CONFIRMED_BY_CORPUS",
        "corpus_root": "corpora/retail/Data.sma_unpacked",
        "course_folder_count": len(folders),
        "parsed_principal_xml_count": len(courses),
        "no_op_byte_identical_count": no_op_byte_identity,
        "authoring_supported": {
            "StartArea_courses": supported_start,
            "FinishArea_courses": supported_finish,
            "SplitTime_records": supported_splits,
            "SplitTime_visual_companion_Eggs": supported_companions,
        },
        "split_count_distribution": {str(count): total for count, total in sorted(split_counts.items())},
        "main_split_time_record_count": total_splits,
        "visual_companion_egg_count": total_companions,
        "visual_companion_count_per_split_distribution": {
            str(count): total for count, total in sorted(companion_counts_per_split.items())
        },
        "visual_companion_count_per_course_distribution": {
            str(count): total for count, total in sorted(companion_counts.items())
        },
        "unusual_visual_companion_layouts": unusual_companion_layouts,
        "split_radius_min": min(radius_values) if radius_values else None,
        "split_radius_max": max(radius_values) if radius_values else None,
        "safely_refused": [
            {
                "course_identity": item["course_identity"],
                "area": area_name,
                "marker_count": item["start_area" if area_name == "StartArea" else "finish_area"]["marker_count"],
                "issues": item["start_area" if area_name == "StartArea" else "finish_area"]["issues"],
            }
            for item in courses
            for area_name in ("StartArea", "FinishArea")
            if not item["start_area" if area_name == "StartArea" else "finish_area"]["authoring_supported"]
            and item["start_area" if area_name == "StartArea" else "finish_area"]["present"]
        ],
        "errors": errors,
        "courses": courses,
        "status": "PASS" if len(folders) == 36 and len(courses) == 36 and not errors and no_op_byte_identity == 36 else "PARTIAL",
    }


def validate_france1_edits(data_root: Path) -> dict:
    path = data_root / "DataScene" / "RaceTest" / "France1.xml"
    source = path.read_bytes()
    base = CourseRaceLogicAuthoring(source, str(path))
    result = []

    editor = CourseRaceLogicAuthoring(source, str(path))
    for index, point in enumerate(editor.area_status[0].positions):
        assert point is not None
        editor.set_start_marker(index, (point[0] + 3.0, point[1], point[2]))
    output, report = editor.export()
    expected = [f"/MarkerLists/StartArea/Marker[{index}]/Value[@Name='Marker Pos']/@Value" for index in range(4)]
    if list(report.changed_semantic_paths) != expected:
        raise ValueError("France1 StartArea translation changed unexpected XML fields")
    result.append({"scenario": "StartArea rigid +3 runtime X", "status": "PASS", "changed_fields": len(report.changes), "output_sha256": report.exported_sha256})

    editor = CourseRaceLogicAuthoring(source, str(path))
    finish = editor.area_status[1]
    if not finish.supported or any(point is None for point in finish.positions):
        raise ValueError("France1 FinishArea is not authoring-supported")
    points = [tuple(point) for point in finish.positions]
    center = tuple(sum(point[axis] for point in points) / 4 for axis in range(3))
    for index, point in enumerate(points):
        editor.set_finish_marker(index, (
            center[0] + 2.0 * (point[0] - center[0]),
            point[1],
            center[2] + 2.0 * (point[2] - center[2]),
        ))
    output, report = editor.export()
    expected = [f"/MarkerLists/FinishArea/Marker[{index}]/Value[@Name='Marker Pos']/@Value" for index in range(4)]
    if list(report.changed_semantic_paths) != expected:
        raise ValueError("France1 FinishArea scale changed unexpected XML fields")
    result.append({"scenario": "FinishArea X/Z scale 2 around centroid", "status": "PASS", "changed_fields": len(report.changes), "output_sha256": report.exported_sha256})

    split = base.split_status[0]
    if not split.supported or split.center is None or split.radius is None:
        raise ValueError("France1 SplitTime0 is not authoring-supported")
    editor = CourseRaceLogicAuthoring(source, str(path))
    editor.set_split_center(split.identity, (split.center[0] + 50.0, split.center[1] + 10.0, split.center[2] - 15.0))
    output, report = editor.export()
    if len(report.changes) != 1 or "@Row3[XYZ]" not in report.changed_semantic_paths[0]:
        raise ValueError("France1 SplitTime center edit changed unexpected XML fields")
    result.append({"scenario": "SplitTime0 center move", "status": "PASS", "changed_fields": 1, "output_sha256": report.exported_sha256})

    editor = CourseRaceLogicAuthoring(source, str(path))
    editor.set_split_radius(split.identity, split.radius + 25.0)
    output, report = editor.export()
    if len(report.changes) != 1 or "Name='Radius']/@Value" not in report.changed_semantic_paths[0]:
        raise ValueError("France1 SplitTime Radius edit changed unexpected XML fields")
    result.append({"scenario": "SplitTime0 Radius edit", "status": "PASS", "changed_fields": 1, "output_sha256": report.exported_sha256})
    return {
        "schema": "course-race-logic-authoring-france1-edit-validation-v1",
        "evidence": "STATIC_ALLOWLIST_VALIDATION; no runtime claim",
        "source": "DataScene/RaceTest/France1.xml",
        "source_sha256": base.source_sha256,
        "edited_game_files_written": False,
        "scenarios": result,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=REPOSITORY.parent / "corpora" / "retail" / "Data.sma_unpacked")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY / "research" / "g0")
    args = parser.parse_args()
    data_root = args.data_root.expanduser().resolve()
    if not data_root.is_dir():
        raise SystemExit(f"Retail course corpus not found: {data_root}")
    corpus = validate_corpus(data_root)
    france = validate_france1_edits(data_root)
    _write(args.output_dir / "retail-race-logic-validation.json", corpus)
    _write(args.output_dir / "france1-edit-validation.json", france)
    lines = [
        "# G0 RaceTest authoring validation",
        "",
        f"Status: **{corpus['status']}** for principal corpus no-op validation; France1 edit scenarios: **{france['status']}**.",
        "",
        f"- Principal Retail course projects: {corpus['course_folder_count']}",
        f"- RaceTest XML parsed and no-op exported byte-identically: {corpus['no_op_byte_identical_count']}/{corpus['course_folder_count']}",
        f"- StartArea authoring supported: {corpus['authoring_supported']['StartArea_courses']}/{corpus['course_folder_count']}",
        f"- FinishArea authoring supported: {corpus['authoring_supported']['FinishArea_courses']}/{corpus['course_folder_count']}",
        f"- SplitTime records authoring supported: {corpus['authoring_supported']['SplitTime_records']}",
        f"- SplitTime visual companion Egg Row3 positions supported: {corpus['authoring_supported']['SplitTime_visual_companion_Eggs']}/{corpus['visual_companion_egg_count']}",
        f"- Visual companion count per course: `{json.dumps(corpus['visual_companion_count_per_course_distribution'], sort_keys=True)}`",
        f"- Visual companion count per split: `{json.dumps(corpus['visual_companion_count_per_split_distribution'], sort_keys=True)}`",
        f"- Split companion layout exceptions: {len(corpus['unusual_visual_companion_layouts'])}",
        f"- Split count distribution: `{json.dumps(corpus['split_count_distribution'], sort_keys=True)}`",
        "",
        "## Safely refused source structures",
        "",
    ]
    if corpus["safely_refused"]:
        for item in corpus["safely_refused"]:
            lines.append(f"- {item['course_identity']} {item['area']}: {item['marker_count']} markers; {', '.join(item['issues'])}.")
    else:
        lines.append("- None.")
    lines.extend(["", "## France1 static edit checks", ""])
    for item in france["scenarios"]:
        lines.append(f"- PASS — {item['scenario']}: {item['changed_fields']} allowlisted field(s), output SHA256 `{item['output_sha256']}`.")
    lines.extend(["", "These generated XML bytes were checked in memory only. No proprietary RaceTest file was written or runtime-tested.", ""])
    (args.output_dir / "retail-race-logic-validation.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"corpus": {key: corpus[key] for key in ("status", "course_folder_count", "no_op_byte_identical_count", "authoring_supported", "split_count_distribution")}, "france1_edits": france["status"]}, indent=2))
    return 0 if corpus["status"] == "PASS" and france["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
