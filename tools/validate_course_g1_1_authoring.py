#!/usr/bin/env python3
"""Validate bounded G1.1 Marker Pos authoring against the Retail XML corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from master_rallye.course_race_authoring import G1_MARKER_LISTS, CourseRaceLogicAuthoring  # noqa: E402
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402


def _expected_role(name: str) -> str:
    if name == "RaceLine":
        return "race.route.raceline.marker_position"
    side = "left" if name.startswith("Left") else "right"
    kind = "inner" if "Inner" in name else "outer"
    return f"race.limit.{side}_{kind}.marker_position"


def validate(data_root: Path) -> dict:
    course_root = data_root / "DataGx" / "Course"
    folders = sorted((item for item in course_root.iterdir() if item.is_dir()), key=lambda item: item.name.casefold())
    inventory_path = REPOSITORY / "research" / "r5t_sdk1" / "retail-corpus-validation.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    project_rows = {item["identity"].casefold(): item for item in inventory["course_projects"]}
    if len(project_rows) != 36 or {item.name.casefold() for item in folders} != set(project_rows):
        raise ValueError("Retail folders do not match the 36 HNT-linked CourseProject inventory")

    coverage = {name: 0 for name in G1_MARKER_LISTS}
    supported = {name: 0 for name in G1_MARKER_LISTS}
    count_distribution = {name: Counter() for name in G1_MARKER_LISTS}
    rows = []
    errors = []
    no_op_count = 0
    for folder in folders:
        project = project_rows[folder.name.casefold()]
        xml_path = data_root / project["race_test_xml"]
        try:
            source = xml_path.read_bytes()
            editor = CourseRaceLogicAuthoring(source, str(xml_path.resolve()))
            no_op, no_op_report = editor.export()
            if no_op != source or no_op_report.changed_semantic_paths:
                raise ValueError("no-op export was not byte-identical")
            no_op_count += 1
            statuses = {item.name: item for item in editor.marker_list_status}
            course_lists = {}
            for name in G1_MARKER_LISTS:
                status = statuses[name]
                coverage[name] += int(status.present)
                supported[name] += int(status.supported)
                count_distribution[name][status.marker_count] += int(status.present)
                edit_result = "SOURCE_BINDING_SUPPORTED" if status.supported else "READ_ONLY"
                course_lists[name] = {
                    "present": status.present,
                    "supported": status.supported,
                    "marker_count": status.marker_count,
                    "source_list_ordinal": status.source_list_ordinal,
                    "edit_roundtrip": edit_result,
                    "evidence_status": status.evidence_status,
                    "issues": list(status.issues),
                }
            rows.append({
                "course_identity": project["identity"],
                "race_test_xml": project["race_test_xml"],
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "no_op_export": "BYTE_IDENTICAL",
                "marker_lists": course_lists,
            })
        except Exception as error:
            errors.append({"course_identity": folder.name, "error": str(error)})

    france1_path = data_root / "DataScene" / "RaceTest" / "France1.xml"
    france1_source = france1_path.read_bytes()
    france1_authoring = CourseRaceLogicAuthoring(france1_source, str(france1_path.resolve()))
    france1_before = parse_course_xml_bytes(france1_source, str(france1_path))
    france1_before_lists = {item.name: item for item in france1_before.marker_lists}
    france1_edit_roundtrip = {}
    for name in G1_MARKER_LISTS:
        status = {item.name: item for item in france1_authoring.marker_list_status}[name]
        if not status.supported or not status.positions or status.positions[0] is None:
            france1_edit_roundtrip[name] = {"status": "FAIL", "reason": "France1 binding is unsupported"}
            continue
        old_position = status.positions[0]
        new_position = (old_position[0] + 0.125, old_position[1], old_position[2])
        edit = CourseRaceLogicAuthoring(france1_source, str(france1_path.resolve()))
        edit.set_marker_position(name, 0, new_position)
        edited, report = edit.export()
        after = parse_course_xml_bytes(edited, str(france1_path))
        after_lists = {item.name: item for item in after.marker_lists}
        valid = (
            len(report.changes) == 1
            and report.changes[0]["semantic_role"] == _expected_role(name)
            and [item.name for item in france1_before.marker_lists] == [item.name for item in after.marker_lists]
        )
        if valid:
            for checked_name in G1_MARKER_LISTS:
                old_list = france1_before_lists.get(checked_name)
                new_list = after_lists.get(checked_name)
                if old_list is None or new_list is None:
                    valid = old_list is new_list
                    continue
                if len(old_list.markers) != len(new_list.markers):
                    valid = False
                    break
                for index, (old_marker, new_marker) in enumerate(zip(old_list.markers, new_list.markers)):
                    expected = new_position if checked_name == name and index == 0 else old_marker.position
                    if new_marker.position != expected or new_marker.direction != old_marker.direction:
                        valid = False
                        break
                if not valid:
                    break
        france1_edit_roundtrip[name] = {
            "status": "PASS" if valid else "FAIL",
            "changed_paths": list(report.changed_semantic_paths),
            "source_order_unchanged": valid,
            "Marker_Dir_unchanged": valid,
            "unknown_content_preserved": report.unknown_content_preserved,
        }

    success = (
        len(folders) == 36 and len(rows) == 36 and no_op_count == 36 and not errors
        and all(coverage[name] == 36 and supported[name] == 36 for name in G1_MARKER_LISTS)
        and all(item["status"] == "PASS" for item in france1_edit_roundtrip.values())
    )
    return {
        "schema": "course-g1-1-marker-position-authoring-corpus-v1",
        "evidence": "CONFIRMED_BY_CORPUS; runtime evidence remains separately labeled",
        "corpus_root": "corpora/retail/Data.sma_unpacked",
        "course_count": len(folders),
        "parsed_course_count": len(rows),
        "no_op_byte_identical_count": no_op_count,
        "list_coverage": coverage,
        "authoring_supported": supported,
        "france1_one_position_edit_roundtrip": france1_edit_roundtrip,
        "marker_count_distributions": {
            name: {str(count): total for count, total in sorted(values.items())}
            for name, values in count_distribution.items()
        },
        "errors": errors,
        "courses": rows,
        "status": "PASS" if success else "PARTIAL",
        "writer_scope": "Existing Marker Pos Value Vector3 fields on exactly five literal lists; no list/marker/Dir edits.",
        "runtime_test_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root", type=Path,
        default=REPOSITORY.parent / "corpora" / "retail" / "Data.sma_unpacked",
    )
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY / "research" / "g1_1")
    args = parser.parse_args()
    data_root = args.data_root.expanduser().resolve()
    if not data_root.is_dir():
        raise SystemExit(f"Retail course corpus not found: {data_root}")
    result = validate(data_root)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "retail-authoring-corpus.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# G1.1 Retail Marker Pos authoring corpus",
        "",
        f"Status: **{result['status']}**; this is static corpus validation, not a runtime test.",
        "",
        f"- Principal Retail courses parsed: {result['parsed_course_count']}/{result['course_count']}",
        f"- Byte-identical no-op exports: {result['no_op_byte_identical_count']}/{result['course_count']}",
        "- France1 one-position source-preserving edit/export validation:",
    ]
    for name in G1_MARKER_LISTS:
        counts = result["marker_count_distributions"][name]
        lines.append(
            f"  - `{name}`: present {result['list_coverage'][name]}/36; supported "
            f"{result['authoring_supported'][name]}/36; France1 edit "
            f"{result['france1_one_position_edit_roundtrip'][name]['status']}; counts `{json.dumps(counts, sort_keys=True)}`."
        )
    if result["errors"]:
        lines.extend(["", "## Outliers", ""])
        lines.extend(f"- {row['course_identity']}: {row['error']}" for row in result["errors"])
    lines.extend([
        "",
        "The five list inventories, marker counts, source order, all Marker Dir values, and non-target fields were checked. Candidate bytes were held in memory; no game XML was written.",
        "",
    ])
    (output_dir / "retail-authoring-corpus.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "course_count", "parsed_course_count", "no_op_byte_identical_count",
        "list_coverage", "authoring_supported", "france1_one_position_edit_roundtrip", "errors",
    )}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
