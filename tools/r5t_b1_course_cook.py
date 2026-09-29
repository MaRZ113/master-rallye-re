#!/usr/bin/env python3
"""Prepare, snapshot, and compare isolated R5T-B.1 course cooker runs.

The Demo 9.10 cooker is triggered by launching the runtime and selecting a
course. This tool never launches the game. It only copies an input runtime to
ignored research output, removes the named course's generated DX/DXT caches,
snapshots completed outputs, and compares cohorts of repeated runs.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import shutil
import stat
import struct
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from master_rallye.course_diff import compare_course_cook_sets, render_course_cook_set_markdown
from master_rallye.course_gxm import parse_course_gxm_float3_pool_bytes, parse_course_gxm_object_table_bytes
from master_rallye.course_source import parse_course_txt


WORK_ROOT = (ROOT / ".research-output" / "r5t_b1").resolve()
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
GENERATED_SUFFIXES = {".dx", ".dxt"}
SOURCE_SUFFIXES = {".gxm", ".txt", ".gxi"}


def _safe_id(value: str, label: str) -> str:
    if not ID_PATTERN.fullmatch(value) or value in {".", ".."}:
        raise ValueError(f"invalid {label} {value!r}; use 1-64 letters, digits, dots, underscores, or hyphens")
    return value


def _safe_relative(value: str, label: str) -> Path:
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    raw_parts = normalized.split("/")
    if (
        pure.is_absolute()
        or not normalized
        or normalized.startswith("/")
        or ":" in raw_parts[0]
        or any(part in {"", ".", ".."} for part in raw_parts)
    ):
        raise ValueError(f"{label} must be a non-empty relative path without '.' or '..': {value!r}")
    return Path(*pure.parts)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_symlinks(root: Path, label: str) -> None:
    if root.is_symlink():
        raise ValueError(f"{label} may not be a symlink: {root}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} contains a symlink; refusing to follow it: {path}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest(root: Path, suffixes: set[str] | None = None) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or (suffixes is not None and path.suffix.casefold() not in suffixes):
            continue
        relative = path.relative_to(root).as_posix()
        key = relative.casefold()
        if key in items:
            raise ValueError(f"case-insensitive path collision in {root}: {relative}")
        items[key] = {"path": relative, "bytes": path.stat().st_size, "sha256": _sha256(path)}
    return dict(sorted(items.items()))


def _experiment_root(experiment: str) -> Path:
    return WORK_ROOT / "experiments" / _safe_id(experiment, "experiment id")


def _cohort_root(experiment: str, cohort: str) -> Path:
    if cohort not in {"baseline", "modified"}:
        raise ValueError("cohort must be 'baseline' or 'modified'")
    return _experiment_root(experiment) / cohort


def _remove_generated_course_outputs(course_root: Path) -> list[str]:
    removed: list[str] = []
    for path in sorted(course_root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if path.is_file() and path.suffix.casefold() in GENERATED_SUFFIXES:
            removed.append(path.relative_to(course_root).as_posix())
            path.chmod(path.stat().st_mode | stat.S_IWRITE)
            path.unlink()
    return removed


def _test_instructions(experiment: str, cohort: str, runtime_root: Path, target_relative: Path) -> str:
    run_ids = [f"{cohort}-{index:02d}" for index in range(1, 4)]
    lines = [
        "R5T-B.1 isolated cooker cohort",
        "",
        f"Experiment: {experiment}",
        f"Cohort: {cohort}",
        f"Runtime: {runtime_root}",
        f"Course: {target_relative.as_posix()}",
        "",
        "The staged runtime is a copy under ignored .research-output. The original installation and corpus are untouched.",
        "",
        "For each of the three independent runs:",
        "1. Start the MRallye.exe inside this cohort's runtime directory, with that directory as its working directory.",
        "2. Select France1 in the Demo 9.10 runtime and wait for the course to load successfully.",
        "3. In a PowerShell terminal at the repository root, snapshot the run using the command below.",
        "4. Exit the runtime completely before resetting the generated DX/DXT files for the next run.",
        "",
        "Snapshot command (replace RUN_ID with the next id listed below):",
        f"python tools\\r5t_b1_course_cook.py snapshot --experiment {experiment} --cohort {cohort} --run-id RUN_ID --course-target {target_relative.as_posix()}",
        "",
        "Reset command, only after closing the runtime:",
        f"python tools\\r5t_b1_course_cook.py reset --experiment {experiment} --cohort {cohort} --course-target {target_relative.as_posix()}",
        "",
        "Run IDs:",
        *[f"- {run_id}" for run_id in run_ids],
        "",
        "If a plain-text cooker log is available, add `--log path\\to\\cooker.log` to the snapshot command. Do not provide screenshots as the only machine-readable log evidence.",
        "The cohort comparer verifies identical GXM/TXT/GXI inputs within each group. The controlled experiment comparer additionally requires the one recorded France1 GXM float to be the only input difference between cohorts.",
        "",
    ]
    patch_path = _experiment_root(experiment) / "source-patch.json"
    if cohort == "modified" and patch_path.is_file():
        patch = json.loads(patch_path.read_text(encoding="utf-8"))["patch"]
        lines.extend([
            f"Controlled edit: point {patch['point_index']} {patch['axis']} {patch['expected_value_f32']} -> {patch['replacement_value_f32']} (delta {patch['delta']}).",
            "The source-node association is a high-confidence inference. The runtime/cooker result is still pending.",
            "",
        ])
    return "\n".join(lines)


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    experiment = _safe_id(args.experiment, "experiment id")
    cohort = args.cohort
    cohort_root = _cohort_root(experiment, cohort)
    runtime_source = args.runtime_source.resolve(strict=True)
    course_source = args.source_course.resolve(strict=True)
    target_relative = _safe_relative(args.course_target, "course target")
    if not runtime_source.is_dir() or not course_source.is_dir():
        raise ValueError("runtime source and source course must both be directories")
    if not _is_within(cohort_root, WORK_ROOT):
        raise ValueError("resolved staging directory escapes the ignored R5T-B.1 output root")
    if _is_within(cohort_root, runtime_source) or _is_within(cohort_root, course_source):
        raise ValueError("staging output may not be nested inside either read-only input tree")
    if cohort_root.exists():
        raise FileExistsError(f"cohort staging directory already exists; refusing to overwrite: {cohort_root}")
    _reject_symlinks(runtime_source, "runtime source")
    _reject_symlinks(course_source, "course source")

    source_manifest = _manifest(course_source)
    source_names = {Path(item["path"]).name.casefold() for item in source_manifest.values()}
    paired_sources = [
        stem for stem in (Path(item["path"]).stem.casefold() for item in source_manifest.values())
        if f"{stem}.gxm" in source_names and f"{stem}.txt" in source_names
    ]
    if not paired_sources:
        raise ValueError(f"source course must contain at least one same-stem GXM/TXT pair: {course_source}")

    staged_runtime = cohort_root / "runtime"
    shutil.copytree(runtime_source, staged_runtime, copy_function=shutil.copy2)
    target_root = (staged_runtime / target_relative).resolve()
    if not _is_within(target_root, staged_runtime):
        raise ValueError("course target resolves outside the staged runtime")
    target_root.mkdir(parents=True, exist_ok=True)
    for existing in target_root.rglob("*"):
        if existing.is_file():
            existing.chmod(existing.stat().st_mode | stat.S_IWRITE)
    shutil.copytree(course_source, target_root, dirs_exist_ok=True, copy_function=shutil.copy2)
    removed = _remove_generated_course_outputs(target_root)
    runtime_exe = next(
        (path for path in (runtime_source / "MRallye.exe", runtime_source / "MRallye 9.10 runtime.exe") if path.is_file()),
        None,
    )
    record = {
        "schema": "r5t-b1-cook-stage-v1",
        "experiment": experiment,
        "cohort": cohort,
        "runtime_source": str(runtime_source),
        "runtime_executable_sha256": _sha256(runtime_exe) if runtime_exe else None,
        "course_source": str(course_source),
        "course_target": target_relative.as_posix(),
        "source_manifest": _manifest(course_source, SOURCE_SUFFIXES),
        "staged_source_manifest": _manifest(target_root, SOURCE_SUFFIXES),
        "removed_generated_cache_files": removed,
        "generated_suffixes_removed": sorted(GENERATED_SUFFIXES),
        "runtime_launch": "manual: launch the staged Demo 9.10 runtime and select the staged course",
    }
    cohort_root.mkdir(parents=True, exist_ok=True)
    (cohort_root / "prepare.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (cohort_root / "TEST_INSTRUCTIONS.txt").write_text(
        _test_instructions(experiment, cohort, staged_runtime, target_relative), encoding="utf-8"
    )
    return {"staged_runtime": str(staged_runtime), "course_target": target_relative.as_posix(), "removed_cache_files": len(removed)}


def patch_startpoint(args: argparse.Namespace) -> dict[str, Any]:
    """Create one bounded source-copy edit to a verified startpoint candidate point."""
    experiment = _safe_id(args.experiment, "experiment id")
    source_course = args.source_course.resolve(strict=True)
    if not source_course.is_dir():
        raise ValueError("source course must be a directory")
    _reject_symlinks(source_course, "source course")
    pairs = []
    for gxm in source_course.glob("*.gxm"):
        txt = next((item for item in source_course.glob("*.txt") if item.stem.casefold() == gxm.stem.casefold()), None)
        if txt:
            pairs.append((gxm, txt))
    if len(pairs) != 1:
        raise ValueError(f"controlled startpoint patch needs exactly one paired GXM/TXT in {source_course}; found {len(pairs)}")
    gxm_path, txt_path = pairs[0]
    raw = gxm_path.read_bytes()
    txt = parse_course_txt(txt_path)
    table = parse_course_gxm_object_table_bytes(raw, txt, gxm_path.name)
    pool = parse_course_gxm_float3_pool_bytes(raw, table, gxm_path.name)
    nodes = [node for node in table.nodes if node.name.casefold() == "startpoint"]
    if len(nodes) != 1 or nodes[0].class_name.casefold() != "momesh":
        raise ValueError("source pair does not contain one moMesh named startpoint")
    node = nodes[0]
    if (node.mesh_index, node.mesh_size) != (0, 12) or len(pool.points) < 8:
        raise ValueError("startpoint node/pool does not match the observed France1 candidate structure")
    first = pool.points[:8]
    axes = [sorted({point[axis] for point in first}) for axis in range(3)]
    corners = set(itertools.product(*axes)) if all(len(values) == 2 for values in axes) else set()
    if len(set(first)) != 8 or set(first) != corners:
        raise ValueError("first eight float3 points are not the observed eight-corner startpoint candidate")
    if not 0 <= args.point_index < 8:
        raise ValueError("point index must be in the observed first-eight startpoint candidate range [0, 7]")
    axis_index = {"x": 0, "y": 1, "z": 2}[args.axis]
    expected = float(args.expected)
    replacement = float(args.replacement)
    if not math.isfinite(expected) or not math.isfinite(replacement):
        raise ValueError("expected and replacement coordinates must be finite")
    if abs(replacement - expected) > 2.0:
        raise ValueError("controlled startpoint displacement must not exceed 2.0 source units")
    byte_offset = pool.offset + args.point_index * 12 + axis_index * 4
    expected_bytes = struct.pack("<f", expected)
    replacement_bytes = struct.pack("<f", replacement)
    if raw[byte_offset:byte_offset + 4] != expected_bytes:
        observed = raw[byte_offset:byte_offset + 4].hex()
        raise ValueError(f"source coordinate preimage mismatch at 0x{byte_offset:X}: expected {expected_bytes.hex()}, found {observed}")

    experiment_root = _experiment_root(experiment)
    output_course = experiment_root / "modified-source"
    patch_record_path = experiment_root / "source-patch.json"
    if output_course.exists() or patch_record_path.exists():
        raise FileExistsError(f"modified source already exists for {experiment}; refusing to overwrite")
    if not _is_within(output_course, WORK_ROOT) or _is_within(output_course, source_course):
        raise ValueError("modified source destination must be an isolated path under .research-output/r5t_b1")
    shutil.copytree(source_course, output_course, copy_function=shutil.copy2)
    patched = bytearray(raw)
    patched[byte_offset:byte_offset + 4] = replacement_bytes
    staged_gxm = output_course / gxm_path.name
    staged_gxm.chmod(staged_gxm.stat().st_mode | stat.S_IWRITE)
    staged_gxm.write_bytes(patched)
    record = {
        "schema": "r5t-b1-startpoint-source-patch-v1",
        "evidence": "CONTROLLED_SOURCE_EDIT; startpoint node association remains HIGH_CONFIDENCE_INFERENCE until cooker response is observed",
        "source_course": str(source_course),
        "modified_course": str(output_course),
        "gxm_name": gxm_path.name,
        "txt_name": txt_path.name,
        "source_node": {"name": node.name, "ordinal": node.ordinal, "parent_id": node.parent_id, "mesh_index": node.mesh_index, "mesh_size": node.mesh_size, "record_offset": node.record_offset, "record_size": node.record_size},
        "point_pool": {"offset": pool.offset, "count": pool.count, "sha256_before": hashlib.sha256(pool.raw).hexdigest()},
        "patch": {
            "point_index": args.point_index,
            "axis": args.axis,
            "byte_offset": byte_offset,
            "byte_size": 4,
            "expected_value_f32": expected,
            "replacement_value_f32": replacement,
            "expected_bytes_hex": expected_bytes.hex(),
            "replacement_bytes_hex": replacement_bytes.hex(),
            "delta": replacement - expected,
        },
        "gxm_sha256_before": hashlib.sha256(raw).hexdigest(),
        "gxm_sha256_after": hashlib.sha256(patched).hexdigest(),
        "all_other_source_files_copied_unchanged": True,
    }
    patch_record_path.parent.mkdir(parents=True, exist_ok=True)
    patch_record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"modified_source_course": str(output_course), "patch_record": str(patch_record_path), "patch": record["patch"]}


def _staged_runtime(args: argparse.Namespace) -> tuple[str, str, Path, Path]:
    experiment = _safe_id(args.experiment, "experiment id")
    cohort = args.cohort
    cohort_root = _cohort_root(experiment, cohort)
    runtime_root = (args.runtime_root or cohort_root / "runtime").resolve(strict=True)
    if not _is_within(runtime_root, cohort_root / "runtime") or not runtime_root.is_dir():
        raise ValueError(f"runtime root must be the prepared isolated clone: {cohort_root / 'runtime'}")
    target_relative = _safe_relative(args.course_target, "course target")
    course_root = (runtime_root / target_relative).resolve(strict=True)
    if not _is_within(course_root, runtime_root) or not course_root.is_dir():
        raise ValueError("course target must resolve to a directory inside the isolated runtime")
    return experiment, cohort, runtime_root, course_root


def reset(args: argparse.Namespace) -> dict[str, Any]:
    experiment, cohort, _, course_root = _staged_runtime(args)
    removed = _remove_generated_course_outputs(course_root)
    return {
        "experiment": experiment,
        "cohort": cohort,
        "course_root": str(course_root),
        "removed_generated_cache_files": removed,
    }


def snapshot(args: argparse.Namespace) -> dict[str, Any]:
    experiment, cohort, runtime_root, course_root = _staged_runtime(args)
    run_id = _safe_id(args.run_id, "run id")
    if not any(path.is_file() and path.suffix.casefold() == ".dx" for path in course_root.rglob("*")):
        raise ValueError(f"no cooked DX found under {course_root}; snapshot requires a successful cook")
    _reject_symlinks(course_root, "cooked course output")
    log_source = args.log.resolve(strict=True) if args.log else None
    if log_source is not None and not log_source.is_file():
        raise ValueError("--log must name a readable file")
    run_root = _cohort_root(experiment, cohort) / "runs" / run_id
    course_snapshot = run_root / "course"
    if run_root.exists():
        raise FileExistsError(f"run snapshot already exists; refusing to overwrite: {run_root}")
    if not _is_within(run_root, _experiment_root(experiment)):
        raise ValueError("snapshot destination escapes the experiment output directory")
    shutil.copytree(course_root, course_snapshot, copy_function=shutil.copy2)
    if log_source is not None:
        shutil.copy2(log_source, run_root / "cooker.log")
    metadata = {
        "schema": "r5t-b1-cook-run-v1",
        "experiment": experiment,
        "cohort": cohort,
        "run_id": run_id,
        "runtime_root": str(runtime_root),
        "course_target": args.course_target.replace("\\", "/"),
        "input_manifest": _manifest(course_snapshot, SOURCE_SUFFIXES),
        "resource_manifest": _manifest(course_snapshot),
        "cooker_log_captured": log_source is not None,
    }
    (run_root / "run.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"run_root": str(run_root), "course_file_count": len(metadata["resource_manifest"]), "log_captured": log_source is not None}


def _common_input_manifest(runs: list[Path], cohort: str) -> dict[str, Any]:
    manifests = []
    for course_root in runs:
        run_path = course_root.parent / "run.json"
        if not run_path.is_file():
            raise ValueError(f"{cohort} run is missing captured run.json input hashes: {run_path}")
        metadata = json.loads(run_path.read_text(encoding="utf-8"))
        manifest = metadata.get("input_manifest")
        if not isinstance(manifest, dict):
            raise ValueError(f"{cohort} run has no input_manifest: {run_path}")
        manifests.append(manifest)
    canonical = {json.dumps(item, sort_keys=True, separators=(",", ":")) for item in manifests}
    if len(canonical) != 1:
        raise ValueError(f"{cohort} source inputs differ between runs")
    return manifests[0]


def validate_source_patch_inputs(experiment_root: Path, baseline_runs: list[Path], modified_runs: list[Path]) -> dict[str, Any]:
    patch_path = experiment_root / "source-patch.json"
    if not patch_path.is_file():
        return {"status": "not available; no recorded controlled source patch"}
    patch_record = json.loads(patch_path.read_text(encoding="utf-8"))
    baseline_inputs = _common_input_manifest(baseline_runs, "baseline")
    modified_inputs = _common_input_manifest(modified_runs, "modified")
    gxm_name = str(patch_record["gxm_name"]).casefold()
    gxm_keys = [key for key in baseline_inputs.keys() | modified_inputs.keys() if Path(key).name.casefold() == gxm_name]
    if len(gxm_keys) != 1:
        raise ValueError(f"source patch GXM is not uniquely captured in cook snapshots: {patch_record['gxm_name']}")
    gxm_key = gxm_keys[0]
    changed_input_paths = sorted(
        key for key in baseline_inputs.keys() | modified_inputs.keys()
        if baseline_inputs.get(key) != modified_inputs.get(key)
    )
    if changed_input_paths != [gxm_key]:
        raise ValueError(f"expected only the patched GXM to differ between cohorts; got {changed_input_paths}")
    if gxm_key not in baseline_inputs or gxm_key not in modified_inputs:
        raise ValueError("patched GXM must be present in both source input manifests")
    if baseline_inputs[gxm_key].get("sha256") != patch_record["gxm_sha256_before"]:
        raise ValueError("baseline cook input GXM hash differs from the recorded original source")
    if modified_inputs[gxm_key].get("sha256") != patch_record["gxm_sha256_after"]:
        raise ValueError("modified cook input GXM hash differs from the recorded one-float source patch")
    return {
        "status": "PASS",
        "baseline_runs_share_identical_source_inputs": True,
        "modified_runs_share_identical_source_inputs": True,
        "only_cross_cohort_input_change": gxm_key,
        "source_gxm_before_sha256": baseline_inputs[gxm_key]["sha256"],
        "source_gxm_after_sha256": modified_inputs[gxm_key]["sha256"],
    }


def compare(args: argparse.Namespace) -> dict[str, Any]:
    experiment = _safe_id(args.experiment, "experiment id")
    experiment_root = _experiment_root(experiment)
    groups: dict[str, list[Path]] = {}
    for cohort in ("baseline", "modified"):
        run_root = experiment_root / cohort / "runs"
        groups[cohort] = sorted(
            (path / "course" for path in run_root.iterdir() if path.is_dir() and (path / "course").is_dir()),
            key=lambda path: path.parent.name.casefold(),
        ) if run_root.is_dir() else []
    report = compare_course_cook_sets(groups["baseline"], groups["modified"])
    report["experiment"] = experiment
    report["input_validation"] = validate_source_patch_inputs(
        experiment_root, groups["baseline"], groups["modified"]
    )
    report["stage_records"] = {
        cohort: str(experiment_root / cohort / "prepare.json")
        for cohort in ("baseline", "modified")
    }
    (experiment_root / "variance-aware-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (experiment_root / "variance-aware-report.md").write_text(
        render_course_cook_set_markdown(report), encoding="utf-8"
    )
    return {
        "report_json": str(experiment_root / "variance-aware-report.json"),
        "report_markdown": str(experiment_root / "variance-aware-report.md"),
        "summary": report["summary"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    stage = commands.add_parser("prepare", help="clone an isolated runtime and stage one paired source course")
    stage.add_argument("--experiment", required=True)
    stage.add_argument("--cohort", choices=("baseline", "modified"), required=True)
    stage.add_argument("--runtime-source", type=Path, required=True)
    stage.add_argument("--source-course", type=Path, required=True)
    stage.add_argument("--course-target", required=True, help="relative runtime path, e.g. DataGx/Course/France1")
    stage.set_defaults(function=prepare)

    source_patch = commands.add_parser("patch-startpoint", help="copy a source course and make one exact, <=2-unit candidate point change")
    source_patch.add_argument("--experiment", required=True)
    source_patch.add_argument("--source-course", type=Path, required=True)
    source_patch.add_argument("--point-index", type=int, required=True, choices=range(8))
    source_patch.add_argument("--axis", choices=("x", "y", "z"), required=True)
    source_patch.add_argument("--expected", type=float, required=True)
    source_patch.add_argument("--replacement", type=float, required=True)
    source_patch.set_defaults(function=patch_startpoint)

    reset_parser = commands.add_parser("reset", help="remove only DX/DXT generated caches in the staged course")
    reset_parser.add_argument("--experiment", required=True)
    reset_parser.add_argument("--cohort", choices=("baseline", "modified"), required=True)
    reset_parser.add_argument("--runtime-root", type=Path)
    reset_parser.add_argument("--course-target", required=True)
    reset_parser.set_defaults(function=reset)

    snap = commands.add_parser("snapshot", help="copy one completed cook output into an immutable run snapshot")
    snap.add_argument("--experiment", required=True)
    snap.add_argument("--cohort", choices=("baseline", "modified"), required=True)
    snap.add_argument("--run-id", required=True)
    snap.add_argument("--runtime-root", type=Path)
    snap.add_argument("--course-target", required=True)
    snap.add_argument("--log", type=Path, help="optional readable cooker log to copy beside the resource snapshot")
    snap.set_defaults(function=snapshot)

    compare_parser = commands.add_parser("compare", help="compare all captured baseline and modified cook runs")
    compare_parser.add_argument("--experiment", required=True)
    compare_parser.set_defaults(function=compare)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.function(args)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
