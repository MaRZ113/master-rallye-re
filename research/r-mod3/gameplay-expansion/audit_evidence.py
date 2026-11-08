#!/usr/bin/env python3
"""Read-only consistency checks for the R-MOD3 feasibility package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
RETAIL_SIZE = 3_121_214
EXPECTED_MODES = {
    "QuickRace": (2, "0x47B780", "0x458090"),
    "Challenge": (7, "0x45EA60", "0x44FEC0"),
    "RallyeCup": (6, "0x481722", "0x45BE10 -> 0x45ABC0"),
    "Invitation": (8, "0x462678 / 0x481722", "0x45BE10 -> 0x45ABC0"),
    "MasterRallye": (5, "0x48157C", "0x452590 -> 0x451DD0"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_exact_identity(path: Path, expected_sha256: str, expected_size: int) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"missing file: {path}")
    actual_size = path.stat().st_size
    actual_sha256 = sha256_file(path)
    if actual_size != expected_size:
        raise ValueError(f"size mismatch: expected {expected_size}, got {actual_size}")
    if actual_sha256.lower() != expected_sha256.lower():
        raise ValueError(f"SHA256 mismatch: expected {expected_sha256}, got {actual_sha256}")
    return {"file": path.name, "size": actual_size, "sha256": actual_sha256}


def _load_json(repo: Path, relative: str) -> Any:
    path = repo / relative
    if not path.is_file():
        raise ValueError(f"missing evidence file: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def audit_mode_map(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("source_sha256") != RETAIL_SHA256:
        raise ValueError("mode map is not pinned to the supported retail SHA")
    modes = {entry.get("mode"): entry for entry in data.get("modes", [])}
    missing = sorted(set(EXPECTED_MODES) - set(modes))
    if missing:
        raise ValueError("mode map lacks owners: " + ", ".join(missing))
    checked: dict[str, Any] = {}
    for name, expected in EXPECTED_MODES.items():
        mode = modes[name]
        actual = (mode.get("race_type"), mode.get("frontend_owner"), mode.get("builder"))
        if actual != expected:
            raise ValueError(f"{name} owner mismatch: expected {expected}, got {actual}")
        checked[name] = {"race_type": actual[0], "frontend_owner": actual[1], "builder": actual[2]}
    return checked


def audit_patch_ranges(plan: dict[str, Any]) -> dict[str, Any]:
    source = plan.get("source_executable", {})
    if source.get("sha256") != RETAIL_SHA256 or source.get("size") != RETAIL_SIZE:
        raise ValueError("F3 plan is not pinned to the exact retail executable")
    operations = plan.get("operations", [])
    ranges: list[tuple[int, int, str]] = []
    for operation in operations:
        try:
            start = int(operation["rva"])
            expected = bytes.fromhex(operation["expected_original_hex"])
            replacement = bytes.fromhex(operation["replacement_hex"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid patch operation: {operation!r}") from error
        if not expected or len(expected) != len(replacement):
            raise ValueError(f"invalid patch size in {operation.get('id', '<unnamed>')}")
        ranges.append((start, start + len(expected), str(operation.get("id", "<unnamed>"))))
    ranges.sort()
    for previous, current in zip(ranges, ranges[1:]):
        if current[0] < previous[1]:
            raise ValueError(f"overlapping F3 operations: {previous[2]} and {current[2]}")
    return {"operation_count": len(operations), "overlap_count": 0}


def audit_patch_preimages(plan: dict[str, Any], image_path: Path) -> dict[str, Any]:
    image = image_path.read_bytes()
    checked = 0
    for operation in plan.get("operations", []):
        try:
            offset = int(operation["file_offset"])
            expected = bytes.fromhex(operation["expected_original_hex"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"invalid patch preimage operation: {operation!r}") from error
        actual = image[offset : offset + len(expected)] if 0 <= offset else b""
        if not expected or len(actual) != len(expected):
            raise ValueError(f"preimage range is invalid for {operation.get('id', '<unnamed>')}")
        if actual != expected:
            raise ValueError(f"retail preimage mismatch for {operation.get('id', '<unnamed>')} at file offset 0x{offset:X}")
        checked += 1
    return {"preimage_checked_count": checked}


def audit_grid(data: dict[str, Any]) -> dict[str, Any]:
    courses = data.get("courses", [])
    if data.get("course_count") != 36 or len(courses) != 36:
        raise ValueError("grid audit no longer describes the 36-course corpus")
    if data.get("scene_registration_count") != 39:
        raise ValueError("grid audit registration count changed")
    statuses = [course.get("runtime_status") for course in courses]
    if any(status is None for status in statuses):
        raise ValueError("a course lacks an explicit runtime clearance status")
    return {
        "course_count": len(courses),
        "scene_registration_count": data["scene_registration_count"],
        "runtime_status_counts": {status: statuses.count(status) for status in sorted(set(statuses))},
    }


def audit_repository(repo: Path, retail_exe: Path | None = None) -> dict[str, Any]:
    mode_map = _load_json(repo, "research/r-ai1-2/mode-map.json")
    chooser_note = repo / "research/r-mod1/native-chooser-count-evidence.md"
    capacity_note = repo / "research/r-mod1/participant-capacity.md"
    ghidra_config = repo / "scratch_rmod1/ghidra-bridge.yaml"
    if not chooser_note.is_file() or not capacity_note.is_file() or not ghidra_config.is_file():
        raise ValueError("required chooser/capacity/Ghidra provenance note is missing")
    chooser_text = chooser_note.read_text(encoding="utf-8")
    if RETAIL_SHA256 not in chooser_text:
        raise ValueError("chooser evidence note is not pinned to retail SHA")
    ghidra_text = ghidra_config.read_text(encoding="utf-8")
    if "ghidra_12.1.4_PUBLIC" not in ghidra_text or "program_name: MRallye.exe" not in ghidra_text:
        raise ValueError("existing Ghidra provenance does not identify the audited program/version")

    exports: dict[str, dict[str, Any]] = {}
    for filename, address, required in [
        ("00458090.json", "00458090", ["004584d3  RET 0x14", "00450580", "00458980"]),
        ("004116a0.json", "004116a0", ["004116af  SAR EAX,0x2", "004116b2  RET"]),
        ("00450580.json", "00450580", ["004505e7  RET", "0x005c37b8"]),
        ("00458980.json", "00458980", ["00458a76  RET 0x4"]),
        ("0047b780.json", "0047b780", ["0047b96e  CALL 0x00458090", "0047b780"]),
        ("0045abc0.json", "0045abc0", ["0045b14a  RET 0xc"]),
        ("00451dd0.json", "00451dd0", ["0045234d  RET 0xc"]),
        ("0044fec0.json", "0044fec0", ["0045010e", "004501ae  RET 0x4"]),
        ("0048eb40.json", "0048eb40", ["0048f160  RET 0x4"]),
    ]:
        item = _load_json(repo, f"scratch_rmod1/ghidra/{filename}")
        if item.get("address", "").lower() != address:
            raise ValueError(f"Ghidra export address mismatch in {filename}")
        assembly = "\n".join(item.get("assembly", []))
        absent = [token for token in required if token.lower() not in assembly.lower()]
        if absent:
            raise ValueError(f"Ghidra export {filename} missing audited instruction(s): {absent}")
        exports[filename] = {"address": item["address"], "assembly_lines": len(item.get("assembly", []))}

    patch = _load_json(repo, "research/r-mod1/native-patch-plan-f3.json")
    grid = _load_json(repo, "research/general-re/grid8/grid8-audit.json")
    identity = None
    preimages = None
    if retail_exe is not None:
        identity = verify_exact_identity(retail_exe, RETAIL_SHA256, RETAIL_SIZE)
        preimages = audit_patch_preimages(patch, retail_exe)
    return {
        "schema": "rmod3-evidence-audit-v1",
        "status": "PASS",
        "retail_file_identity": identity or "NOT_CHECKED_NO_PATH_SUPPLIED",
        "mode_owners": audit_mode_map(mode_map),
        "f3_plan": audit_patch_ranges(patch),
        "f3_retail_preimages": preimages or "NOT_CHECKED_NO_PATH_SUPPLIED",
        "grid_corpus": audit_grid(grid),
        "ghidra_exports": exports,
        "limitations": [
            "Read-only source/evidence consistency; not gameplay or runtime qualification.",
            "Seven-AI crash cause remains unknown without a matching exception capture.",
            "Course clearance remains whatever explicit statuses the source audit records.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--retail-exe", type=Path, help="optional exact retail image to hash")
    parser.add_argument("--output", type=Path, help="write deterministic JSON report")
    args = parser.parse_args(argv)
    try:
        report = audit_repository(args.repo.resolve(), args.retail_exe)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"R-MOD3 AUDIT FAIL: {error}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
