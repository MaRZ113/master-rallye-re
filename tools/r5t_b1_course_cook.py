#!/usr/bin/env python3
"""Prepare, snapshot, and compare isolated R5T-B.1/C course cooker runs.

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


def _test_instructions(
    experiment: str,
    cohort: str,
    runtime_root: Path,
    target_relative: Path,
    run_count: int = 3,
) -> str:
    run_ids = [f"{cohort}-{index:02d}" for index in range(1, run_count + 1)]
    lines = [
        "Isolated course cooker cohort",
        "",
        f"Experiment: {experiment}",
        f"Cohort: {cohort}",
        f"Runtime: {runtime_root}",
        f"Course: {target_relative.as_posix()}",
        "",
        "The staged runtime is a copy under ignored .research-output. The original installation and corpus are untouched.",
        "",
        f"For each of the {run_count} independent runs:",
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
        "The cohort comparer verifies identical GXM/TXT/GXI inputs within each group. The controlled experiment comparer additionally requires the recorded GXM to be the only input difference between cohorts.",
        f"After both cohorts are staged, validate the candidate with: python tools\\r5t_b1_course_cook.py validate --experiment {experiment}",
        f"After both cohorts complete, compare with: python tools\\r5t_b1_course_cook.py compare --experiment {experiment} --minimum-runs {run_count}",
        "",
    ]
    patch_path = _experiment_root(experiment) / "source-patch.json"
    if cohort == "modified" and patch_path.is_file():
        record = json.loads(patch_path.read_text(encoding="utf-8"))
        if "patch" in record:
            patch = record["patch"]
            edit = (
                f"Controlled edit: point {patch['point_index']} {patch['axis']} "
                f"{patch['expected_value_f32']} -> {patch['replacement_value_f32']} "
                f"(delta {patch['delta']})."
            )
        else:
            vector = record.get("translation_vector_source", {})
            edit = (
                "Controlled edit: translate the eight-point startpoint candidate "
                f"by source vector ({vector.get('x')}, {vector.get('y')}, {vector.get('z')})."
            )
        lines.extend([
            edit,
            "The source-node association is a high-confidence inference. Observe runtime behavior separately from the compiled byte effect.",
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

    run_count = getattr(args, "run_count", 3)
    if not isinstance(run_count, int) or not 2 <= run_count <= 10:
        raise ValueError("run count must be an integer from 2 through 10")

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
        "run_count": run_count,
    }
    cohort_root.mkdir(parents=True, exist_ok=True)
    (cohort_root / "prepare.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (cohort_root / "TEST_INSTRUCTIONS.txt").write_text(
        _test_instructions(experiment, cohort, staged_runtime, target_relative, run_count), encoding="utf-8"
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


def patch_startpoint_volume(args: argparse.Namespace) -> dict[str, Any]:
    """Translate the eight verified France1 candidate box points as one unit."""
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
        raise ValueError(f"controlled startpoint-volume patch needs exactly one paired GXM/TXT in {source_course}; found {len(pairs)}")
    gxm_path, txt_path = pairs[0]
    original = gxm_path.read_bytes()
    txt = parse_course_txt(txt_path)
    table = parse_course_gxm_object_table_bytes(original, txt, gxm_path.name)
    pool = parse_course_gxm_float3_pool_bytes(original, table, gxm_path.name)
    nodes = [node for node in table.nodes if node.name.casefold() == "startpoint"]
    if len(nodes) != 1 or nodes[0].class_name.casefold() != "momesh":
        raise ValueError("source pair does not contain one moMesh named startpoint")
    node = nodes[0]
    if (node.mesh_index, node.mesh_size) != (0, 12) or len(pool.points) < 8:
        raise ValueError("startpoint node/pool does not match the observed France1 candidate structure")
    points_before = tuple(tuple(float(v) for v in point) for point in pool.points[:8])
    axes = [sorted({point[axis] for point in points_before}) for axis in range(3)]
    corners = set(itertools.product(*axes)) if all(len(values) == 2 for values in axes) else set()
    if len(set(points_before)) != 8 or set(points_before) != corners:
        raise ValueError("first eight float3 points are not the observed eight-corner startpoint candidate")
    axis_index = {"x": 0, "y": 1, "z": 2}[args.axis]
    delta = float(args.delta)
    if not math.isfinite(delta) or abs(delta) < 0.25 or abs(delta) > 5.0:
        raise ValueError("startpoint translation magnitude must be finite and between 0.25 and 5.0 source units")

    def bounds(points: tuple[tuple[float, float, float], ...]) -> dict[str, list[float]]:
        return {
            name: [min(point[i] for point in points), max(point[i] for point in points)]
            for i, name in enumerate(("x", "y", "z"))
        }

    def center(points: tuple[tuple[float, float, float], ...]) -> list[float]:
        return [sum(point[i] for point in points) / len(points) for i in range(3)]

    expected_aabb = bounds(points_before)
    pool_bounds = bounds(tuple(pool.points))
    new_aabb_candidate = dict(expected_aabb)
    new_aabb_candidate[args.axis] = [value + delta for value in expected_aabb[args.axis]]
    if new_aabb_candidate[args.axis][0] < pool_bounds[args.axis][0] or new_aabb_candidate[args.axis][1] > pool_bounds[args.axis][1]:
        raise ValueError("translated startpoint box would leave the measured source point-pool bounds")

    patched = bytearray(original)
    point_edits: list[dict[str, Any]] = []
    allowed_byte_offsets: set[int] = set()
    for point_index, point in enumerate(points_before):
        byte_offset = pool.offset + point_index * 12 + axis_index * 4
        old_bytes = original[byte_offset:byte_offset + 4]
        old_value = struct.unpack("<f", old_bytes)[0]
        new_bytes = struct.pack("<f", old_value + delta)
        new_value = struct.unpack("<f", new_bytes)[0]
        if not math.isfinite(old_value) or not math.isfinite(new_value) or new_value == old_value:
            raise ValueError(f"point {point_index} translation is non-finite or rounds to no float32 change")
        patched[byte_offset:byte_offset + 4] = new_bytes
        allowed_byte_offsets.update(range(byte_offset, byte_offset + 4))
        point_edits.append({
            "point_index": point_index,
            "byte_offset": byte_offset,
            "before_f32": old_value,
            "after_f32": new_value,
            "observed_delta_f32": new_value - old_value,
        })

    changed_offsets = {i for i, (before, after) in enumerate(zip(original, patched)) if before != after}
    if not changed_offsets or not changed_offsets.issubset(allowed_byte_offsets):
        raise ValueError("source patch changed bytes outside the eight authorized float32 fields")
    point_rows = []
    for point_index in range(8):
        row = list(points_before[point_index])
        row[axis_index] = point_edits[point_index]["after_f32"]
        point_rows.append(tuple(row))
    points_after = tuple(point_rows)
    if len(set(points_after)) != 8 or set(points_after) != set(itertools.product(*[
        sorted({point[axis] for point in points_after}) for axis in range(3)
    ])):
        raise ValueError("translation failed the eight-corner box geometry check")
    max_pairwise_distance_delta = 0.0
    for left in range(8):
        for right in range(left + 1, 8):
            old_distance = math.dist(points_before[left], points_before[right])
            new_distance = math.dist(points_after[left], points_after[right])
            max_pairwise_distance_delta = max(max_pairwise_distance_delta, abs(old_distance - new_distance))
    if max_pairwise_distance_delta > 1e-3:
        raise ValueError(f"translation changed pairwise box geometry by {max_pairwise_distance_delta:.6g}")

    experiment_root = _experiment_root(experiment)
    output_course = experiment_root / "modified-source"
    patch_record_path = experiment_root / "source-patch.json"
    if output_course.exists() or patch_record_path.exists():
        raise FileExistsError(f"modified source already exists for {experiment}; refusing to overwrite")
    if not _is_within(output_course, WORK_ROOT) or _is_within(output_course, source_course):
        raise ValueError("modified source destination must be an isolated path under .research-output/r5t_b1")
    source_manifest = _manifest(source_course)
    shutil.copytree(source_course, output_course, copy_function=shutil.copy2)
    staged_gxm = output_course / gxm_path.name
    staged_gxm.chmod(staged_gxm.stat().st_mode | stat.S_IWRITE)
    staged_gxm.write_bytes(patched)
    after_manifest = _manifest(output_course)
    changed_files = [
        key for key in sorted(source_manifest.keys() | after_manifest.keys())
        if source_manifest.get(key) != after_manifest.get(key)
    ]
    if changed_files != [gxm_path.name.casefold()]:
        raise ValueError(f"source patch copy changed an unexpected file set: {changed_files}")
    reloaded_table = parse_course_gxm_object_table_bytes(bytes(patched), txt, gxm_path.name)
    reloaded_pool = parse_course_gxm_float3_pool_bytes(bytes(patched), reloaded_table, gxm_path.name)
    if tuple(reloaded_pool.points[:8]) != points_after:
        raise ValueError("patched GXM reparse does not reproduce the translated eight points")

    translation = {axis: 0.0 for axis in ("x", "y", "z")}
    translation[args.axis] = delta
    record = {
        "schema": "r5t-c-startpoint-volume-patch-v1",
        "evidence": "controlled whole-candidate-box source translation; binding of first eight pool points to startpoint remains HIGH_CONFIDENCE_INFERENCE",
        "source_course": str(source_course),
        "modified_course": str(output_course),
        "gxm_name": gxm_path.name,
        "txt_name": txt_path.name,
        "source_node": {
            "name": node.name,
            "ordinal": node.ordinal,
            "parent_id": node.parent_id,
            "mesh_index": node.mesh_index,
            "mesh_size": node.mesh_size,
            "record_offset": node.record_offset,
            "record_size": node.record_size,
        },
        "point_pool": {
            "offset": pool.offset,
            "count": pool.count,
            "candidate_point_count": 8,
            "sha256_before": hashlib.sha256(pool.raw).hexdigest(),
            "sha256_after": hashlib.sha256(reloaded_pool.raw).hexdigest(),
        },
        "translation_vector_source": translation,
        "old_aabb_source": expected_aabb,
        "new_aabb_source": bounds(points_after),
        "old_center_source": center(points_before),
        "new_center_source": center(points_after),
        "max_pairwise_distance_delta": max_pairwise_distance_delta,
        "point_edits": point_edits,
        "changed_byte_count": len(changed_offsets),
        "all_changed_bytes_confined_to_eight_float32_fields": True,
        "changed_source_files": changed_files,
        "gxm_sha256_before": hashlib.sha256(original).hexdigest(),
        "gxm_sha256_after": hashlib.sha256(patched).hexdigest(),
        "all_other_source_files_copied_unchanged": True,
    }
    patch_record_path.parent.mkdir(parents=True, exist_ok=True)
    patch_record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "modified_source_course": str(output_course),
        "patch_record": str(patch_record_path),
        "translation_vector_source": translation,
        "old_aabb_source": expected_aabb,
        "new_aabb_source": record["new_aabb_source"],
        "changed_byte_count": len(changed_offsets),
    }


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


def validate_staged_experiment(args: argparse.Namespace) -> dict[str, Any]:
    """Validate the paired isolated source/runtime stages before any cook."""
    experiment = _safe_id(args.experiment, "experiment id")
    experiment_root = _experiment_root(experiment)
    patch_path = experiment_root / "source-patch.json"
    if not patch_path.is_file():
        raise ValueError(f"missing controlled source patch record: {patch_path}")
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    if patch.get("schema") != "r5t-c-startpoint-volume-patch-v1":
        raise ValueError("validate requires a recorded whole-startpoint-volume patch")
    edits = patch.get("point_edits")
    vector = patch.get("translation_vector_source")
    if not isinstance(edits, list) or len(edits) != 8 or [item.get("point_index") for item in edits] != list(range(8)):
        raise ValueError("source patch must contain exactly the ordered eight candidate-point edits")
    nonzero_axes = [axis for axis, value in vector.items() if float(value) != 0.0]
    if len(nonzero_axes) != 1:
        raise ValueError("source patch must translate along exactly one source axis")
    delta = float(vector[nonzero_axes[0]])
    if not math.isfinite(delta) or abs(delta) < 0.25 or abs(delta) > 5.0:
        raise ValueError("recorded translation is outside the validated 0.25-5.0-unit range")
    for item in edits:
        observed = float(item["after_f32"]) - float(item["before_f32"])
        if abs(observed - delta) > 1.0e-4:
            raise ValueError(f"point {item['point_index']} does not share the recorded translation")
    if float(patch.get("max_pairwise_distance_delta", math.inf)) > 1.0e-3:
        raise ValueError("source patch does not preserve the measured eight-point box dimensions")
    if patch.get("changed_source_files") != [str(patch["gxm_name"]).casefold()]:
        raise ValueError("source patch changed files outside the expected GXM")

    baseline_path = experiment_root / "baseline" / "prepare.json"
    modified_path = experiment_root / "modified" / "prepare.json"
    if not baseline_path.is_file() or not modified_path.is_file():
        raise ValueError("both baseline and modified runtime cohorts must be staged first")
    prepared = {
        "baseline": json.loads(baseline_path.read_text(encoding="utf-8")),
        "modified": json.loads(modified_path.read_text(encoding="utf-8")),
    }
    for cohort, record in prepared.items():
        if record.get("schema") != "r5t-b1-cook-stage-v1" or record.get("experiment") != experiment or record.get("cohort") != cohort:
            raise ValueError(f"invalid {cohort} stage record")
        if record.get("run_count", 0) < 2:
            raise ValueError(f"{cohort} cohort must stage at least two independent cooks")
    if prepared["baseline"].get("run_count") != prepared["modified"].get("run_count"):
        raise ValueError("baseline and modified run counts differ")
    if prepared["baseline"].get("course_target") != prepared["modified"].get("course_target"):
        raise ValueError("baseline and modified course targets differ")
    if prepared["baseline"].get("runtime_executable_sha256") != prepared["modified"].get("runtime_executable_sha256"):
        raise ValueError("baseline and modified runtime executables differ")

    expected_gxm = str(patch["gxm_name"]).casefold()
    source_manifests = {cohort: record.get("source_manifest", {}) for cohort, record in prepared.items()}
    source_keys = set(source_manifests["baseline"]) | set(source_manifests["modified"])
    source_differences = [
        key for key in sorted(source_keys)
        if source_manifests["baseline"].get(key) != source_manifests["modified"].get(key)
    ]
    if source_differences != [expected_gxm]:
        raise ValueError(f"source inputs must differ only in {expected_gxm}; found {source_differences}")
    if source_manifests["baseline"].get(expected_gxm, {}).get("sha256") != patch.get("gxm_sha256_before"):
        raise ValueError("baseline source GXM hash differs from the patch preimage")
    if source_manifests["modified"].get(expected_gxm, {}).get("sha256") != patch.get("gxm_sha256_after"):
        raise ValueError("modified source GXM hash differs from the patch output")

    staged_differences: list[str] = []
    runtime_hashes: dict[str, str] = {}
    xml_path = None
    xml_hashes: dict[str, str] = {}
    for cohort, record in prepared.items():
        runtime_root = _cohort_root(experiment, cohort) / "runtime"
        if not runtime_root.is_dir():
            raise ValueError(f"missing isolated {cohort} runtime: {runtime_root}")
        runtime_exe = next(
            (path for path in (runtime_root / "MRallye.exe", runtime_root / "MRallye 9.10 runtime.exe") if path.is_file()),
            None,
        )
        if runtime_exe is None:
            raise ValueError(f"missing runtime executable in {runtime_root}")
        actual_runtime_hash = _sha256(runtime_exe)
        if actual_runtime_hash != record.get("runtime_executable_sha256"):
            raise ValueError(f"{cohort} runtime executable no longer matches its prepare record")
        runtime_hashes[cohort] = actual_runtime_hash

        target_relative = _safe_relative(record["course_target"], "course target")
        course_root = (runtime_root / target_relative).resolve(strict=True)
        if not _is_within(course_root, runtime_root):
            raise ValueError(f"{cohort} course target escapes its runtime")
        actual_manifest = _manifest(course_root, SOURCE_SUFFIXES)
        if actual_manifest != record.get("staged_source_manifest"):
            raise ValueError(f"{cohort} staged source files changed after preparation")
        if any(path.is_file() and path.suffix.casefold() in GENERATED_SUFFIXES for path in course_root.rglob("*")):
            raise ValueError(f"{cohort} target still contains generated DX/DXT files; reset before cooking")

        xml_candidate = runtime_root / "DataScene" / "RaceTest" / f"{target_relative.name}.xml"
        if not xml_candidate.is_file():
            raise ValueError(f"expected RaceTest XML is missing from {cohort} runtime: {xml_candidate}")
        xml_path = xml_candidate.relative_to(runtime_root).as_posix()
        xml_hashes[cohort] = _sha256(xml_candidate)
    if xml_hashes["baseline"] != xml_hashes["modified"]:
        raise ValueError("RaceTest XML differs between the staged runtimes")

    staged_manifests = {cohort: record.get("staged_source_manifest", {}) for cohort, record in prepared.items()}
    staged_keys = set(staged_manifests["baseline"]) | set(staged_manifests["modified"])
    staged_differences = [
        key for key in sorted(staged_keys)
        if staged_manifests["baseline"].get(key) != staged_manifests["modified"].get(key)
    ]
    if staged_differences != [expected_gxm]:
        raise ValueError(f"staged course source must differ only in {expected_gxm}; found {staged_differences}")

    validation = {
        "schema": "r5t-c-startpoint-stage-validation-v1",
        "experiment": experiment,
        "status": "PASS_STAGED",
        "compile_status": "PENDING_TWO_BASELINE_TWO_MODIFIED_COOKS",
        "runtime_status": "PENDING_HUMAN_OBSERVATION",
        "source_patch": {
            "gxm_name": patch["gxm_name"],
            "point_count": len(edits),
            "translation_vector_source": vector,
            "old_aabb_source": patch["old_aabb_source"],
            "new_aabb_source": patch["new_aabb_source"],
            "max_pairwise_distance_delta": patch["max_pairwise_distance_delta"],
            "changed_byte_count": patch["changed_byte_count"],
            "source_hash_before": patch["gxm_sha256_before"],
            "source_hash_after": patch["gxm_sha256_after"],
        },
        "cohorts": {
            "run_count_each": prepared["baseline"]["run_count"],
            "runtime_executable_sha256": runtime_hashes["baseline"],
            "course_target": prepared["baseline"]["course_target"],
            "only_source_manifest_difference": expected_gxm,
            "racetest_xml_path": xml_path,
            "racetest_xml_sha256": xml_hashes["baseline"],
            "generated_dx_dxt_absent_before_cooking": True,
        },
        "semantic_diff_report": "variance-aware-report.json (created by compare after all snapshots)",
    }
    validation_path = experiment_root / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    instructions = [
        "R5T-C whole-startpoint runtime observation",
        f"Experiment: {experiment}",
        "",
        "Use only the isolated baseline and modified runtime clones listed in their TEST_INSTRUCTIONS.txt files.",
        "First complete baseline-01 and modified-01 cooker runs. In each, enter the same France1 race state and record:",
        "- player initial position and heading;",
        "- AI starting positions and formation;",
        "- countdown and whether the race starts normally;",
        "- visible start-line/trigger behavior, if any.",
        "Repeat baseline and modified with run 02 to check compiled repeatability; gameplay observation need only be repeated if run 01 differs or is ambiguous.",
        "The eight-point source box association is HIGH_CONFIDENCE_INFERENCE. Record only observed behavior; no spawn, trigger, or collision meaning is assumed.",
        "The matching RaceTest XML is byte-identical in both staged runtimes. Compare observations between the two cohorts, not with an unmodified runtime from another build.",
        "After all four cooks are snapshotted, run the compare command printed in TEST_INSTRUCTIONS.txt.",
        "",
    ]
    (experiment_root / "RUNTIME_TEST_INSTRUCTIONS.txt").write_text("\n".join(instructions), encoding="utf-8")
    return {
        "validation_json": str(validation_path),
        "runtime_test_instructions": str(experiment_root / "RUNTIME_TEST_INSTRUCTIONS.txt"),
        "status": validation["status"],
        "compile_status": validation["compile_status"],
        "runtime_status": validation["runtime_status"],
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
    staged_counts = []
    for cohort in ("baseline", "modified"):
        stage_path = experiment_root / cohort / "prepare.json"
        if stage_path.is_file():
            stage = json.loads(stage_path.read_text(encoding="utf-8"))
            staged_counts.append(int(stage.get("run_count", 3)))
    if staged_counts and len(set(staged_counts)) != 1:
        raise ValueError(f"baseline and modified cohorts were staged with different run counts: {staged_counts}")
    minimum_runs = getattr(args, "minimum_runs", None)
    if minimum_runs is None:
        minimum_runs = staged_counts[0] if staged_counts else 3
    if staged_counts and minimum_runs != staged_counts[0]:
        raise ValueError(f"requested minimum {minimum_runs} differs from staged cohort count {staged_counts[0]}")
    report = compare_course_cook_sets(
        groups["baseline"], groups["modified"], minimum_runs=minimum_runs
    )
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
    stage.add_argument("--run-count", type=int, choices=range(2, 11), default=3,
                       help="independent cooks to stage; default 3, use 2 only after target-field repeatability is established")
    stage.set_defaults(function=prepare)

    validate_parser = commands.add_parser(
        "validate",
        help="validate paired baseline/modified source and runtime stages before cooking",
    )
    validate_parser.add_argument("--experiment", required=True)
    validate_parser.set_defaults(function=validate_staged_experiment)

    source_patch = commands.add_parser("patch-startpoint", help="copy a source course and make one exact, <=2-unit candidate point change")
    source_patch.add_argument("--experiment", required=True)
    source_patch.add_argument("--source-course", type=Path, required=True)
    source_patch.add_argument("--point-index", type=int, required=True, choices=range(8))
    source_patch.add_argument("--axis", choices=("x", "y", "z"), required=True)
    source_patch.add_argument("--expected", type=float, required=True)
    source_patch.add_argument("--replacement", type=float, required=True)
    source_patch.set_defaults(function=patch_startpoint)

    volume_patch = commands.add_parser(
        "patch-startpoint-volume",
        help="copy a course and translate exactly the eight points of the validated candidate startpoint box",
    )
    volume_patch.add_argument("--experiment", required=True)
    volume_patch.add_argument("--source-course", type=Path, required=True)
    volume_patch.add_argument("--axis", choices=("x", "y", "z"), required=True)
    volume_patch.add_argument("--delta", type=float, required=True, help="signed source-space displacement, magnitude 0.25-5")
    volume_patch.set_defaults(function=patch_startpoint_volume)

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
    compare_parser.add_argument("--minimum-runs", type=int, choices=range(2, 11),
                               help="defaults to the staged run count; two requires prior target-field repeatability evidence")
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
