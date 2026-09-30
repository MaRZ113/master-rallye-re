#!/usr/bin/env python3
"""Stage and audit manual cold cooks with the original Demo 9.10 runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import stat
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.dx_course import parse_course_dx


SEED_RUNTIME = ROOT / "research-output" / "r5t_b" / "cooker-lab"
OUTPUT_ROOT = ROOT / "research-output" / "r5t_f0" / "cooker-lab"
RUNTIME_HASH = "13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78"
BASE_GXM_HASH = "56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2"
MODIFIED_GXM = ROOT / "research-output" / "r5t_f0" / "modified-source" / "France1.gxm"
XML_RELATIVE = Path("DataScene") / "RaceTest" / "France1.xml"
COURSE_RELATIVE = Path("DataGx") / "Course" / "France1"
GENERATED_SUFFIXES = {".dx", ".dxt"}
EXPECTED_RUNS = tuple(f"{cohort}-{i:02d}" for cohort in ("baseline", "modified") for i in range(1, 4))
OUTPUT_REPORT = ROOT / "research" / "r5t_f0" / "cook-differential.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _runtime(cohort: str) -> Path:
    if cohort not in {"baseline", "modified"}:
        raise ValueError("cohort must be baseline or modified")
    return (OUTPUT_ROOT / cohort / "runtime").resolve()


def _course_root(cohort: str) -> Path:
    runtime = _runtime(cohort)
    root = (runtime / COURSE_RELATIVE).resolve()
    if runtime not in root.parents:
        raise ValueError("course directory escapes staged runtime")
    if not root.is_dir() or root.is_symlink():
        raise FileNotFoundError(f"staged course directory missing or symlinked: {root}")
    return root


def _hash_map(root: Path, *, generated: bool) -> dict[str, dict[str, Any]]:
    result = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file():
            continue
        if generated and path.suffix.casefold() not in GENERATED_SUFFIXES:
            continue
        if not generated and path.suffix.casefold() in GENERATED_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        result[relative.casefold()] = {"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256(path)}
    return result


def _remove_generated(course_root: Path) -> list[str]:
    removed = []
    for path in sorted(course_root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if path.is_file() and path.suffix.casefold() in GENERATED_SUFFIXES:
            path.chmod(path.stat().st_mode | stat.S_IWRITE)
            removed.append(path.relative_to(course_root).as_posix())
            path.unlink()
    return removed


def _replace_staged_copy(target: Path, source: Path) -> None:
    """Replace one copied, possibly read-only input inside a staged runtime."""
    target.chmod(target.stat().st_mode | stat.S_IWRITE)
    target.unlink()
    shutil.copy2(source, target)


def stage() -> dict[str, Any]:
    if OUTPUT_ROOT.exists():
        raise FileExistsError(f"refusing to overwrite cooker stage: {OUTPUT_ROOT}")
    if not SEED_RUNTIME.is_dir() or SEED_RUNTIME.is_symlink():
        raise FileNotFoundError(f"existing verified Demo 9.10 lab missing: {SEED_RUNTIME}")
    seed_exe = SEED_RUNTIME / "MRallye.exe"
    seed_gxm = SEED_RUNTIME / COURSE_RELATIVE / "France1.gxm"
    seed_xml = SEED_RUNTIME / XML_RELATIVE
    if sha256(seed_exe) != RUNTIME_HASH:
        raise ValueError("seed runtime executable hash differs from previously verified Demo 9.10 runtime")
    if sha256(seed_gxm) != BASE_GXM_HASH:
        raise ValueError("seed runtime does not contain the hash-pinned old France1 GXM")
    if sha256(MODIFIED_GXM) == BASE_GXM_HASH:
        raise ValueError("modified source GXM is missing or identical to baseline")

    stage_record: dict[str, Any] = {
        "schema": "r5t-f0-original-9.10-cooker-stage-v1",
        "seed_runtime": str(SEED_RUNTIME),
        "runtime_executable_sha256": RUNTIME_HASH,
        "race_test_xml_sha256": sha256(seed_xml),
        "course_target": COURSE_RELATIVE.as_posix(),
        "run_ids": list(EXPECTED_RUNS),
        "cohorts": {},
        "manual_runtime_selection_required": True,
    }
    try:
        for cohort in ("baseline", "modified"):
            cohort_root = OUTPUT_ROOT / cohort
            cohort_root.mkdir(parents=True)
            runtime_root = cohort_root / "runtime"
            shutil.copytree(SEED_RUNTIME, runtime_root, copy_function=shutil.copy2)
            course_root = _course_root(cohort)
            removed = _remove_generated(course_root)
            target_gxm = course_root / "France1.gxm"
            if cohort == "modified":
                # copytree/copy2 preserve Windows read-only attributes from the
                # seed. Replace only this staged copy after clearing that bit;
                # the source lab and the independently prepared GXM stay intact.
                _replace_staged_copy(target_gxm, MODIFIED_GXM)
            target_hash = sha256(target_gxm)
            expected_hash = BASE_GXM_HASH if cohort == "baseline" else sha256(MODIFIED_GXM)
            if target_hash != expected_hash:
                raise AssertionError(f"staged {cohort} GXM hash mismatch")
            xml_hash = sha256(runtime_root / XML_RELATIVE)
            if xml_hash != stage_record["race_test_xml_sha256"]:
                raise AssertionError(f"staged {cohort} RaceTest XML changed")
            stage_record["cohorts"][cohort] = {
                "runtime": str(runtime_root),
                "course_input_gxm_sha256": target_hash,
                "course_txt_sha256": sha256(course_root / "France1.txt"),
                "race_test_xml_sha256": xml_hash,
                "source_inputs": _hash_map(course_root, generated=False),
                "generated_caches_removed": removed,
                "initial_dx_dxt_count": 0,
            }
            (cohort_root / "snapshots").mkdir()

        baseline_inputs = stage_record["cohorts"]["baseline"]["source_inputs"]
        modified_inputs = stage_record["cohorts"]["modified"]["source_inputs"]
        differences = [key for key in sorted(set(baseline_inputs) | set(modified_inputs))
                       if baseline_inputs.get(key) != modified_inputs.get(key)]
        expected_relative = "france1.gxm"
        if differences != [expected_relative]:
            raise AssertionError(f"cohorts differ outside the single France1 GXM: {differences[:10]}")
        stage_record["only_course_source_input_difference"] = "France1.gxm"
        stage_record["unmodified_input_difference_count"] = 1
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        (OUTPUT_ROOT / "stage.json").write_text(json.dumps(stage_record, indent=2) + "\n", encoding="utf-8")
        write_instructions()
        return stage_record
    except Exception:
        # Preserve the staged evidence for inspection if validation fails.
        raise


def write_instructions() -> None:
    lines = [
        "# R5T-F.0 manual Demo 9.10 cold-cook sequence",
        "",
        "This stage uses two isolated copies of the existing Demo 9.10 cooker lab.",
        "It requires manual course selection in the runtime; no command-line cook command was found.",
        "Never launch the source lab or retail installation for this experiment.",
        "",
        f"Baseline runtime: `{_runtime('baseline')}`",
        f"Modified runtime: `{_runtime('modified')}`",
        f"Course path inside each: `{COURSE_RELATIVE.as_posix()}`",
        "",
        "For each run below:",
        "1. From PowerShell, launch only the specified cohort copy, using its runtime directory as the working directory:",
        "",
        "```powershell",
        "$exe = 'D:\\Game\\Master Rallye\\master-rallye-re\\research-output\\r5t_f0\\cooker-lab\\baseline\\runtime\\MRallye.exe'",
        "Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe)",
        "```",
        "",
        "For modified runs, replace `baseline` in that path with `modified`.",
        "2. Select France1 and wait for it to load successfully. With DX/DXT caches absent, the runtime performs the cook.",
        "3. Exit the runtime completely, return to the repository root, and capture the output:",
        "",
        "```powershell",
        "python tools\\r5t_f0_cooker_runs.py capture --cohort COHORT --run-id RUN_ID",
        "```",
        "",
        "After runs 01 and 02 in each cohort, reset its generated cache before continuing:",
        "",
        "```powershell",
        "python tools\\r5t_f0_cooker_runs.py reset --cohort COHORT",
        "```",
        "",
        "After run 03, do not reset. Those last validated runtime trees are kept cooked for the later baseline/modified in-game comparison.",
        "Run only one runtime at a time. Never launch the seed lab or retail installation.",
        "",
        "Run order:",
        *[f"- `{run_id}`" for run_id in EXPECTED_RUNS],
        "",
        "Run `compare` after all six snapshots. Capture/reset commands reject unknown cohort or run IDs and operate only inside these staged runtime copies.",
        "",
    ]
    (OUTPUT_ROOT / "COOK-INSTRUCTIONS.md").write_text("\n".join(lines), encoding="utf-8")


def capture(cohort: str, run_id: str) -> dict[str, Any]:
    allowed = {f"{cohort}-{i:02d}" for i in range(1, 4)}
    if run_id not in allowed:
        raise ValueError(f"run ID must be one of {sorted(allowed)}")
    runtime_root = _runtime(cohort)
    course_root = _course_root(cohort)
    stage_record = json.loads((OUTPUT_ROOT / "stage.json").read_text(encoding="utf-8"))
    cohort_record = stage_record["cohorts"][cohort]
    expected_gxm = cohort_record["course_input_gxm_sha256"]
    if sha256(course_root / "France1.gxm") != expected_gxm:
        raise ValueError("staged GXM changed after preparation")
    if sha256(runtime_root / XML_RELATIVE) != stage_record["race_test_xml_sha256"]:
        raise ValueError("RaceTest XML changed after preparation")
    dx_files = tuple(path for path in course_root.iterdir() if path.is_file() and path.suffix.casefold() == ".dx")
    if len(dx_files) != 1:
        raise FileNotFoundError(f"expected exactly one cooked course DX, found {len(dx_files)}")
    dx_path = dx_files[0]
    model = parse_course_dx(dx_path)
    if model.word_0x04 != 135 or not model.course_render_validated:
        raise ValueError(f"cooked DX failed revision-135 render validation: rev={model.word_0x04}, valid={model.course_render_validated}")
    output_dir = OUTPUT_ROOT / cohort / "snapshots" / run_id
    if output_dir.exists():
        raise FileExistsError(f"snapshot already exists: {output_dir}")
    output_course = output_dir / "DataGx" / "Course" / "France1"
    output_course.mkdir(parents=True)
    copied = []
    for path in sorted(course_root.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_file() and path.suffix.casefold() in GENERATED_SUFFIXES:
            target = output_course / path.name
            shutil.copy2(path, target)
            copied.append({"path": path.name, "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    bsp = model.collision.bsp
    record = {
        "schema": "r5t-f0-cook-snapshot-v1",
        "run_id": run_id,
        "cohort": cohort,
        "runtime_executable_sha256": stage_record["runtime_executable_sha256"],
        "input_gxm_sha256": expected_gxm,
        "input_txt_sha256": cohort_record["course_txt_sha256"],
        "race_test_xml_sha256": stage_record["race_test_xml_sha256"],
        "generated_files": copied,
        "dx": {
            "file": dx_path.name,
            "size_bytes": dx_path.stat().st_size,
            "sha256": sha256(dx_path),
            "revision": model.word_0x04,
            "vertex_count": model.vertex_count,
            "triangle_count": model.triangle_count,
            "draw_count": len(model.physical_draws),
            "render_validated": model.course_render_validated,
            "render_prefix_end": bsp.tag_offset if bsp else None,
            "tag100": None if bsp is None else {
                "offset": bsp.tag_offset,
                "end_offset": bsp.end_offset,
                "size_bytes": len(bsp.raw),
                "sha256": bsp.sha256,
                "semantics": "UNKNOWN",
            },
        },
    }
    (output_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def reset(cohort: str) -> dict[str, Any]:
    course_root = _course_root(cohort)
    removed = _remove_generated(course_root)
    return {"cohort": cohort, "removed_generated_files": removed, "remaining_dx_dxt": 0}


def _diff_bytes(first: bytes, second: bytes) -> dict[str, Any]:
    if len(first) != len(second):
        return {"same_size": False, "changed_bytes": None, "changed_ranges": None}
    offsets = [index for index, (a, b) in enumerate(zip(first, second)) if a != b]
    ranges = []
    if offsets:
        start = previous = offsets[0]
        for current in offsets[1:]:
            if current != previous + 1:
                ranges.append({"offset": start, "length": previous - start + 1})
                start = current
            previous = current
        ranges.append({"offset": start, "length": previous - start + 1})
    return {"same_size": True, "changed_bytes": len(offsets), "changed_ranges": ranges}


def _load_run(cohort: str, run_id: str) -> tuple[dict[str, Any], Path, Any]:
    run_dir = OUTPUT_ROOT / cohort / "snapshots" / run_id
    record = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    dx_path = run_dir / "DataGx" / "Course" / "France1" / record["dx"]["file"]
    model = parse_course_dx(dx_path)
    return record, dx_path, model


def _render_near_box(points, bounds, expansion=0.5) -> dict[str, Any]:
    if bounds is None:
        return {"vertex_count": 0, "nearest_point": None}
    low, high = bounds
    inside = [point for point in points if all(
        low[axis] - expansion <= point[axis] <= high[axis] + expansion for axis in range(3)
    )]
    center = tuple((low[axis] + high[axis]) / 2.0 for axis in range(3))
    nearest = min(points, key=lambda point: math.dist(point, center)) if points else None
    return {
        "aabb_expansion": expansion,
        "vertex_count_inside_expanded_aabb": len(inside),
        "nearest_compiled_vertex": list(nearest) if nearest else None,
        "nearest_compiled_vertex_distance_to_center": math.dist(nearest, center) if nearest else None,
    }


def compare(minimum_runs: int = 3) -> dict[str, Any]:
    stage_record = json.loads((OUTPUT_ROOT / "stage.json").read_text(encoding="utf-8"))
    cohort_runs = {}
    models = {}
    dx_bytes = {}
    tag_bytes = {}
    for cohort in ("baseline", "modified"):
        ids = [f"{cohort}-{index:02d}" for index in range(1, minimum_runs + 1)]
        records = []
        cohort_models = []
        for run_id in ids:
            record, path, model = _load_run(cohort, run_id)
            if not model.course_render_validated or model.word_0x04 != 135:
                raise ValueError(f"invalid cooked output {run_id}")
            bsp = model.collision.bsp
            record["revalidated"] = True
            records.append(record)
            cohort_models.append(model)
            dx_bytes[run_id] = path.read_bytes()
            tag_bytes[run_id] = bsp.raw if bsp else None
        cohort_runs[cohort] = records
        models[cohort] = cohort_models

    tag_stability = {}
    for cohort, records in cohort_runs.items():
        tags = [tag_bytes[item["run_id"]] for item in records]
        tag_stability[cohort] = {
            "all_present": all(item is not None for item in tags),
            "byte_identical_within_cohort": bool(tags) and all(item == tags[0] for item in tags[1:]),
            "hashes": [item["dx"]["tag100"]["sha256"] if item["dx"]["tag100"] else None for item in records],
        }
    first_baseline = cohort_runs["baseline"][0]
    first_modified = cohort_runs["modified"][0]
    baseline_model = models["baseline"][0]
    modified_model = models["modified"][0]
    base_tag = tag_bytes[first_baseline["run_id"]]
    modified_tag = tag_bytes[first_modified["run_id"]]
    tag_diff = _diff_bytes(base_tag, modified_tag) if base_tag is not None and modified_tag is not None else None

    # Runtime position mapping for the probe is (+20,0,0). Report local decoded
    # render vertices only as correspondence clues, never as semantic proof.
    old_bounds = ((-1472.298828125, 63.67451858520508, 352.06646728515625),
                  (-1471.231689453125, 73.11727142333984, 353.04193115234375))
    new_bounds = ((old_bounds[0][0] + 20.0, old_bounds[0][1], old_bounds[0][2]),
                  (old_bounds[1][0] + 20.0, old_bounds[1][1], old_bounds[1][2]))
    render_check = {
        "coordinate_space": "compiled DX / runtime (x,y,z)",
        "baseline": _render_near_box(baseline_model.vertices.positions, old_bounds),
        "modified_near_old": _render_near_box(modified_model.vertices.positions, old_bounds),
        "modified_near_new": _render_near_box(modified_model.vertices.positions, new_bounds),
        "interpretation": "spatial decoded-render proximity only; not gameplay or physical-role proof",
    }
    baseline_tag_stable = tag_stability["baseline"]["byte_identical_within_cohort"]
    modified_tag_stable = tag_stability["modified"]["byte_identical_within_cohort"]
    report = {
        "schema": "r5t-f0-cook-differential-v1",
        "status": "COOKS_VALIDATED_TAG100_CAUSALITY_PENDING_STABILITY",
        "stage": str(OUTPUT_ROOT),
        "runtime_executable_sha256": stage_record["runtime_executable_sha256"],
        "race_test_xml_sha256_unchanged": stage_record["race_test_xml_sha256"],
        "run_count_per_cohort": minimum_runs,
        "cohorts": cohort_runs,
        "tag100_stability": tag_stability,
        "tag100_baseline_vs_modified_first_run": {
            "baseline_sha256": first_baseline["dx"]["tag100"]["sha256"] if first_baseline["dx"]["tag100"] else None,
            "modified_sha256": first_modified["dx"]["tag100"]["sha256"] if first_modified["dx"]["tag100"] else None,
            "byte_diff": tag_diff,
            "stable_causal_difference_supported": bool(baseline_tag_stable and modified_tag_stable and tag_diff and tag_diff.get("changed_bytes", 0) > 0),
            "semantics": "UNKNOWN",
        },
        "render_region": render_check,
        "full_dx_byte_identity_within_cohorts": {
            cohort: all(
                dx_bytes[records[0]["run_id"]] == dx_bytes[item["run_id"]]
                for item in records[1:]
            )
            for cohort, records in cohort_runs.items()
        },
        "interpretation": {
            "tag100_name": "trailing tag100 structure",
            "tag100_physical_semantics": "UNKNOWN",
            "source_geometry_gameplay_semantics": "UNKNOWN",
        },
    }
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stage", help="stage two isolated runtime copies and remove France1 DX/DXT caches")
    snap = commands.add_parser("capture", help="snapshot a completed run after closing its runtime")
    snap.add_argument("--cohort", choices=("baseline", "modified"), required=True)
    snap.add_argument("--run-id", required=True)
    reset_args = commands.add_parser("reset", help="remove generated France1 DX/DXT caches after closing runtime")
    reset_args.add_argument("--cohort", choices=("baseline", "modified"), required=True)
    comp = commands.add_parser("compare", help="validate three cold cooks per cohort")
    comp.add_argument("--minimum-runs", type=int, default=3)
    args = parser.parse_args()
    if args.command == "stage":
        result = stage()
    elif args.command == "capture":
        result = capture(args.cohort, args.run_id)
    elif args.command == "reset":
        result = reset(args.cohort)
    else:
        if args.minimum_runs != 3:
            raise ValueError("R5T-F.0 requires exactly three baseline and three modified cold cooks")
        result = compare(args.minimum_runs)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
