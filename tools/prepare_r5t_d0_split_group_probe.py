#!/usr/bin/env python3
"""Prepare, but do not run, the isolated France1 split-group XML probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from master_rallye.course_xml import CourseXmlEgg, parse_course_xml_bytes  # noqa: E402


DEFAULT_SOURCE = REPOSITORY.parent / "corpora" / "retail" / "Data.sma_unpacked" / "DataScene" / "RaceTest" / "France1.xml"
DEFAULT_OUTPUT = REPOSITORY / ".research-output" / "r5t_d0" / "split0-companion-group-shift" / "DataScene" / "RaceTest" / "France1.xml"
TARGET_NAMES = tuple(f"SplitTime0-{index}" for index in range(4))


def _row3(egg: CourseXmlEgg) -> tuple[str, tuple[float, float, float, float]]:
    matrix = egg.matrix("en3d Matrix")
    if matrix is None:
        raise ValueError(f"{egg.name} is missing en3d Matrix")
    raw = dict(matrix.attributes).get("Row3")
    if raw is None or matrix.row(3) is None:
        raise ValueError(f"{egg.name} is missing a valid en3d Matrix Row3")
    return raw, matrix.row(3)


def _replace_egg_row3(data: bytes, egg_name: str, replacement: str) -> bytes:
    egg_pattern = re.compile(
        rb"(<Egg\b(?=[^>]*\bName\s*=\s*['\"]" + re.escape(egg_name.encode("ascii"))
        + rb"['\"])[^>]*>.*?</Egg>)",
        re.DOTALL,
    )
    matches = list(egg_pattern.finditer(data))
    if len(matches) != 1:
        raise ValueError(f"expected one XML Egg named {egg_name!r}, found {len(matches)}")
    block = matches[0].group(1)
    row_pattern = re.compile(
        rb"(<Value\b(?=[^>]*\bName\s*=\s*['\"]en3d Matrix['\"])[^>]*\bRow3\s*=\s*['\"])([^'\"]*)(['\"][^>]*>)"
    )
    rows = list(row_pattern.finditer(block))
    if len(rows) != 1:
        raise ValueError(f"expected one en3d Matrix Row3 in {egg_name!r}, found {len(rows)}")
    old_raw = rows[0].group(2).decode("ascii")
    new_block = row_pattern.sub(lambda match: match.group(1) + replacement.encode("ascii") + match.group(3), block, count=1)
    return data[:matches[0].start()] + new_block + data[matches[0].end():]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(source: Path, output: Path) -> dict:
    source = source.resolve()
    output = output.resolve()
    if source == output:
        raise ValueError("probe output must be a distinct file; original source will not be overwritten")
    try:
        output.relative_to((REPOSITORY / ".research-output").resolve())
    except ValueError as error:
        raise ValueError("probe output must stay inside this repository's ignored .research-output directory") from error

    original = source.read_bytes()
    baseline = parse_course_xml_bytes(original, source.name)
    split0 = [egg for egg in baseline.split_time_eggs if egg.name == "SplitTime0"]
    start_area = baseline.marker_list("StartArea")
    if len(split0) != 1 or start_area is None or len(start_area.markers) != 4:
        raise ValueError("expected one SplitTime0 and a four-marker StartArea")
    component = split0[0].split_time_component
    split_fields = {item.name: item.value for item in component.values} if component else {}
    if split_fields.get("Split Time ID") != "0" or split_fields.get("Radius") != "21.00000" or split_fields.get("ExtraTime") != "77.50000":
        raise ValueError("France1 SplitTime0 controls no longer match the expected baseline values")

    targets = []
    for name in TARGET_NAMES:
        matches = [egg for egg in baseline.eggs if egg.list_name == "SplitTimes" and egg.name == name]
        if len(matches) != 1:
            raise ValueError(f"expected one SplitTimes/{name}, found {len(matches)}")
        raw, values = _row3(matches[0])
        targets.append({"egg": matches[0], "old_raw": raw, "old_values": values})

    points = [item.position for item in start_area.markers]
    area_centroid = tuple(sum(point[axis] for point in points) / len(points) for axis in range(3))
    group_center = tuple(sum(item["old_values"][axis] for item in targets) / len(targets) for axis in range(3))
    delta = tuple(round(area_centroid[axis] - group_center[axis], 2) for axis in range(3))
    translated = original
    replacements = []
    for item in targets:
        old = item["old_values"]
        new_values = tuple(old[axis] + delta[axis] for axis in range(3)) + (old[3],)
        new_raw = " ".join(f"{value:.2f}" for value in new_values[:3]) + f" {new_values[3]:.2f}"
        translated = _replace_egg_row3(translated, item["egg"].name, new_raw)
        replacements.append({
            "egg_name": item["egg"].name,
            "xml_path": item["egg"].xml_path + "/Value[@Name='en3d Matrix']/@Row3",
            "baseline_row3_raw": item["old_raw"],
            "modified_row3_raw": new_raw,
            "baseline_row3_xyz": list(old[:3]),
            "modified_row3_xyz": list(new_values[:3]),
            "unchanged_row3_w": new_values[3],
        })

    # Reversing only the four authorized Row3 attributes must restore every
    # original byte, including all whitespace and unrelated XML fields.
    reversed_data = translated
    for replacement in replacements:
        reversed_data = _replace_egg_row3(reversed_data, replacement["egg_name"], replacement["baseline_row3_raw"])
    if reversed_data != original:
        raise ValueError("probe edit failed the exact four-attribute byte-isolation audit")

    modified = parse_course_xml_bytes(translated, output.name)
    modified_split0 = [egg for egg in modified.split_time_eggs if egg.name == "SplitTime0"]
    if len(modified_split0) != 1 or _row3(modified_split0[0])[0] != _row3(split0[0])[0]:
        raise ValueError("visual SplitTime0 Egg Row3 changed unexpectedly")
    if modified.marker_list("RaceLine").markers != baseline.marker_list("RaceLine").markers:
        raise ValueError("RaceLine changed unexpectedly")
    if modified.marker_list("StartArea").markers != baseline.marker_list("StartArea").markers:
        raise ValueError("StartArea changed unexpectedly")
    if len(modified.split_time_eggs) != len(baseline.split_time_eggs):
        raise ValueError("split Egg count changed unexpectedly")
    for original_egg in baseline.eggs:
        changed_egg = next((egg for egg in modified.eggs if egg.xml_path == original_egg.xml_path), None)
        if changed_egg is None:
            raise ValueError(f"Egg disappeared after edit: {original_egg.xml_path}")
        is_target = original_egg.name in TARGET_NAMES and original_egg.list_name == "SplitTimes"
        if not is_target and original_egg.matrices != changed_egg.matrices:
            raise ValueError(f"non-target Egg matrix changed: {original_egg.xml_path}")
    if _sha256(source.read_bytes()) != _sha256(original):
        raise ValueError("source XML changed while preparing the copy")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(translated)
    manifest = {
        "experiment": "R5T-D.0 France1 split0 companion Egg group translation candidate",
        "status": "PREPARED_NOT_RUNTIME_TESTED",
        "source_file": source.name,
        "source_bytes": len(original),
        "source_sha256": _sha256(original),
        "prepared_xml": str(output),
        "prepared_bytes": len(translated),
        "prepared_sha256": _sha256(translated),
        "target_group": "EggLists_Version4/List[@Name='SplitTimes']/Egg[@Name='SplitTime0-0' through 'SplitTime0-3']/Value[@Name='en3d Matrix']/@Row3",
        "baseline_group_center_xyz": list(group_center),
        "StartArea_centroid_xyz": list(area_centroid),
        "common_translation_xyz": list(delta),
        "target_group_center_after_xyz": [group_center[axis] + delta[axis] for axis in range(3)],
        "modified_fields": replacements,
        "unchanged_controls": {
            "SplitTime0_visual_Egg_Row3": _row3(split0[0])[0],
            "SplitTime0_ID_Radius_ExtraTime": split_fields,
            "SplitTime1_and_2": "all source matrix rows and split component fields",
            "RaceLine": "all 448 markers; exact parser equality",
            "StartArea": "all four markers; exact parser equality",
            "FinishArea": "all four markers; exact source unchanged by byte-isolation audit",
        },
        "byte_isolation": {
            "only_four_en3d_Matrix_Row3_attributes_modified": True,
            "changed_xyz_float_components": 12,
            "Row3_w_preserved": True,
            "reverse_patch_restores_original_exactly": True,
            "original_overwritten": False,
        },
        "runtime_test": {
            "not_performed_by_tool": True,
            "load_only_this_XML_override_in_a_separate_Retail_test_copy": True,
            "observe_split0_event_location_separately_from_visual_sign_and_moved_checkpoint_objects": True,
            "do_not_treat_moved_sibling_Egg_visuals_as_the_split_event": True,
        },
    }
    manifest_path = output.with_name("probe-manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = prepare(args.source, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
