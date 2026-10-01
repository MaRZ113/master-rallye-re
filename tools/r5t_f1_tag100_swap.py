#!/usr/bin/env python3
"""R5T-F.1 research-only reciprocal tag100 region swap for France1 rev135."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from master_rallye.dx_course import CourseDxModel, parse_course_dx, parse_course_dx_bytes
from r5t_f0_cooker_runs import _render_near_box

PHASE = "R5T-F.1"
RUNTIME_SHA256 = "13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78"
BASE_GXM_SHA256 = "56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2"
MOD_GXM_SHA256 = "2e93f6291f9b5e4b0606b218e42f7926a7d4f0d37a1eb76f359d9ccbff4dc2a2"
RACETEST_SHA256 = "6048ed26c78118f3f82d9ddbcaf4f75c6655b24d805189d3cf3bd772202dc0df"
EXPECTED = {
    "baseline": {
        "run_id": "baseline-03",
        "dx_sha256": "b7820fe13c5ef7eb53593bcee4e54943cf97780244b47f6fe7cb549d5c5ee7f2",
        "tag100_sha256": "9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7",
        "gxm_sha256": BASE_GXM_SHA256,
        "txt_sha256": "71ea372203bcc6e84bfee87e7d2f410e22c1fdcdc5f653c87274100df38c0d43",
    },
    "modified": {
        "run_id": "modified-03",
        "dx_sha256": "01289e705750fa257037b65f55f7b469db795b4c649f74b45777da0a8d08bac2",
        "tag100_sha256": "e31f79ae9ac83db3141a631363e7f982e0fbd9d4ba281bbb5f4a4f21bdf19d07",
        "gxm_sha256": MOD_GXM_SHA256,
        "txt_sha256": "71ea372203bcc6e84bfee87e7d2f410e22c1fdcdc5f653c87274100df38c0d43",
    },
}
COOKER_ROOT = ROOT / "research-output" / "r5t_f0" / "cooker-lab"
OUTPUT_ROOT = ROOT / "research-output" / "r5t_f1"
RUNTIME_ROOT = OUTPUT_ROOT / "runtime"
RESEARCH_MANIFEST = ROOT / "research" / "r5t_f1" / "swap-manifest.json"
REPORT_PATH = ROOT / "research" / "r5t_f0" / "cook-differential.json"
STAGE_PATH = COOKER_ROOT / "stage.json"
COURSE_DX_REL = Path("DataGx") / "Course" / "France1" / "france1.dx"
RACETEST_REL = Path("DataScene") / "RaceTest" / "France1.xml"

OLD_BOUNDS = (
    (-1472.298828125, 63.67451858520508, 352.06646728515625),
    (-1471.231689453125, 73.11727142333984, 353.04193115234375),
)
NEW_BOUNDS = (
    (OLD_BOUNDS[0][0] + 20.0, OLD_BOUNDS[0][1], OLD_BOUNDS[0][2]),
    (OLD_BOUNDS[1][0] + 20.0, OLD_BOUNDS[1][1], OLD_BOUNDS[1][2]),
)


@dataclass(frozen=True)
class Regions:
    label: str
    data: bytes
    model: CourseDxModel
    prefix: bytes
    tag100: bytes
    tag_offset: int
    tag_end: int


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_hashes(root: Path, *, exclude_course_dx: bool = False) -> dict[str, dict[str, Any]]:
    result = {}
    excluded = COURSE_DX_REL.as_posix().casefold()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if exclude_course_dx and relative.casefold() == excluded:
            continue
        result[relative.casefold()] = {
            "path": relative,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return result


def _tree_hashes_sha256(items: dict[str, dict[str, Any]]) -> str:
    payload = json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload)


def parse_regions(data: bytes, label: str) -> Regions:
    """Split a validated rev135 course DX at the parser-derived tag100 boundary."""
    model = parse_course_dx_bytes(data, label)
    if model.word_0x04 != 135:
        raise ValueError(f"{label}: expected revision 135, found {model.word_0x04}")
    if not model.course_render_validated:
        raise ValueError(f"{label}: render section did not validate")
    tag = model.collision.bsp
    if tag is None:
        raise ValueError(f"{label}: parser did not find trailing tag100")
    if tag.tag != 100 or tag.tag_offset < 0 or tag.end_offset != len(data):
        raise ValueError(f"{label}: tag100 boundary is incomplete or not at EOF")
    prefix = data[:tag.tag_offset]
    tag_bytes = data[tag.tag_offset:tag.end_offset]
    if tag_bytes != tag.raw or sha256(tag_bytes) != tag.sha256:
        raise ValueError(f"{label}: parsed tag100 bytes do not match their exact file slice")
    if model.collision.errors or model.collision.unparsed_data:
        raise ValueError(f"{label}: trailing section has parser errors or unparsed bytes")
    return Regions(label, data, model, prefix, tag_bytes, tag.tag_offset, tag.end_offset)


def validate_regions(
    regions: Regions,
    *,
    expected_dx_sha256: str | None = None,
    expected_tag100_sha256: str | None = None,
) -> None:
    if expected_dx_sha256 and sha256(regions.data) != expected_dx_sha256:
        raise ValueError(f"{regions.label}: donor DX SHA-256 does not match accepted snapshot")
    if expected_tag100_sha256 and sha256(regions.tag100) != expected_tag100_sha256:
        raise ValueError(f"{regions.label}: donor tag100 SHA-256 does not match accepted cohort")


def build_reciprocal_bytes(
    baseline_data: bytes,
    modified_data: bytes,
    *,
    expected_baseline_tag_sha256: str,
    expected_modified_tag_sha256: str,
    expected_baseline_dx_sha256: str | None = None,
    expected_modified_dx_sha256: str | None = None,
) -> tuple[dict[str, Regions], dict[str, bytes]]:
    baseline = parse_regions(baseline_data, "baseline")
    modified = parse_regions(modified_data, "modified")
    validate_regions(
        baseline,
        expected_dx_sha256=expected_baseline_dx_sha256,
        expected_tag100_sha256=expected_baseline_tag_sha256,
    )
    validate_regions(
        modified,
        expected_dx_sha256=expected_modified_dx_sha256,
        expected_tag100_sha256=expected_modified_tag_sha256,
    )
    hybrids = {
        "hybrid-a": baseline.prefix + modified.tag100,
        "hybrid-b": modified.prefix + baseline.tag100,
    }
    regions = {"baseline": baseline, "modified": modified}
    pairs = {
        "hybrid-a": (baseline, modified),
        "hybrid-b": (modified, baseline),
    }
    for name, data in hybrids.items():
        prefix_donor, tag_donor = pairs[name]
        verify_hybrid_bytes(data, prefix_donor, tag_donor)
    return regions, hybrids


def verify_hybrid_bytes(data: bytes, prefix_donor: Regions, tag_donor: Regions) -> Regions:
    hybrid = parse_regions(data, "hybrid")
    if hybrid.prefix != prefix_donor.prefix:
        raise ValueError("hybrid prefix bytes differ from selected prefix donor")
    if hybrid.tag100 != tag_donor.tag100:
        raise ValueError("hybrid tag100 bytes differ from selected tag100 donor")
    if hybrid.tag_offset != len(prefix_donor.prefix):
        raise ValueError("hybrid tag100 offset does not equal selected prefix size")
    if len(hybrid.data) != len(prefix_donor.prefix) + len(tag_donor.tag100):
        raise ValueError("hybrid total size does not equal the selected region sizes")
    return hybrid


def _donor_path(cohort: str) -> Path:
    run_id = EXPECTED[cohort]["run_id"]
    return COOKER_ROOT / cohort / "snapshots" / run_id / COURSE_DX_REL


def _runtime_path(cohort: str) -> Path:
    return COOKER_ROOT / cohort / "runtime"


def _load_accepted_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    stage = json.loads(STAGE_PATH.read_text(encoding="utf-8"))
    differential = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    if stage.get("runtime_executable_sha256") != RUNTIME_SHA256:
        raise ValueError("R5T-F.0 stage runtime hash is not the accepted Demo 9.10 build")
    if stage.get("race_test_xml_sha256") != RACETEST_SHA256:
        raise ValueError("R5T-F.0 stage RaceTest XML hash changed")
    if stage.get("only_course_source_input_difference") != "France1.gxm":
        raise ValueError("R5T-F.0 stage does not identify the single GXM input change")
    if stage.get("unmodified_input_difference_count") != 1:
        raise ValueError("R5T-F.0 stage input-difference count is not one")
    baseline_inputs = stage["cohorts"]["baseline"]["source_inputs"]
    modified_inputs = stage["cohorts"]["modified"]["source_inputs"]
    if set(baseline_inputs) != set(modified_inputs):
        raise ValueError("R5T-F.0 source input inventories do not have identical paths")
    changed_inputs = [
        key for key in baseline_inputs
        if baseline_inputs[key].get("sha256") != modified_inputs[key].get("sha256")
    ]
    if len(changed_inputs) != 1 or Path(changed_inputs[0]).name.casefold() != "france1.gxm":
        raise ValueError("R5T-F.0 source manifests do not isolate only France1.gxm")
    if differential.get("status") != "COOKS_VALIDATED_STABLE_TAG100_DIFFERENCE":
        raise ValueError("accepted R5T-F.0 cooker differential is missing or inconclusive")
    if differential.get("run_count_per_cohort") != 3:
        raise ValueError("R5T-F.0 differential does not contain three runs per cohort")
    stability = differential.get("tag100_stability", {})
    if not all(stability.get(name, {}).get("byte_identical_within_cohort") for name in EXPECTED):
        raise ValueError("R5T-F.0 tag100 cohort repeatability is not confirmed")
    tag_result = differential.get("tag100_baseline_vs_modified_first_run", {})
    if not tag_result.get("stable_causal_difference_supported"):
        raise ValueError("R5T-F.0 stable source-to-tag100 effect is not confirmed")

    for cohort, expected in EXPECTED.items():
        source_record = stage["cohorts"][cohort]
        if source_record.get("course_input_gxm_sha256") != expected["gxm_sha256"]:
            raise ValueError(f"{cohort}: source GXM hash differs from accepted probe")
        if source_record.get("course_txt_sha256") != expected["txt_sha256"]:
            raise ValueError(f"{cohort}: source TXT hash differs from accepted probe")
        run = next(
            (item for item in differential["cohorts"][cohort] if item.get("run_id") == expected["run_id"]),
            None,
        )
        if run is None or run.get("dx", {}).get("sha256") != expected["dx_sha256"]:
            raise ValueError(f"{cohort}: accepted run-03 DX identity does not match")
        if run.get("dx", {}).get("tag100", {}).get("sha256") != expected["tag100_sha256"]:
            raise ValueError(f"{cohort}: accepted run-03 tag100 identity does not match")
    return stage, differential


def _record_regions(regions: Regions, snapshot_path: Path) -> dict[str, Any]:
    return {
        "snapshot_path": snapshot_path.relative_to(ROOT).as_posix(),
        "runtime_copy_path": (_runtime_path(regions.label) / COURSE_DX_REL).relative_to(ROOT).as_posix(),
        "dx_sha256": sha256(regions.data),
        "dx_size_bytes": len(regions.data),
        "revision": regions.model.word_0x04,
        "render_validated": regions.model.course_render_validated,
        "prefix": {
            "offset": 0,
            "end_offset": regions.tag_offset,
            "size_bytes": len(regions.prefix),
            "sha256": sha256(regions.prefix),
        },
        "tag100": {
            "offset": regions.tag_offset,
            "end_offset": regions.tag_end,
            "size_bytes": len(regions.tag100),
            "sha256": sha256(regions.tag100),
        },
    }


def _render_diagnostic(model: CourseDxModel) -> dict[str, Any]:
    return {
        "coordinate_space": "compiled DX / runtime (x,y,z)",
        "old_location": _render_near_box(model.vertices.positions, OLD_BOUNDS),
        "new_location": _render_near_box(model.vertices.positions, NEW_BOUNDS),
        "vertex_count": model.vertex_count,
        "triangle_count": model.triangle_count,
        "draw_count": len(model.physical_draws),
        "interpretation": "render-parser proximity check only; physical behavior is not inferred",
    }


def _runtime_sources(stage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for cohort in EXPECTED:
        runtime = _runtime_path(cohort)
        dx_path = runtime / COURSE_DX_REL
        exe = runtime / "MRallye.exe"
        xml = runtime / RACETEST_REL
        if sha256_file(exe) != RUNTIME_SHA256:
            raise ValueError(f"{cohort}: run-03 runtime executable hash mismatch")
        if sha256_file(dx_path) != EXPECTED[cohort]["dx_sha256"]:
            raise ValueError(f"{cohort}: retained runtime DX is not the accepted run-03 donor")
        if sha256_file(xml) != RACETEST_SHA256:
            raise ValueError(f"{cohort}: retained runtime RaceTest XML hash mismatch")
        result[cohort] = {
            "runtime_path": runtime.relative_to(ROOT).as_posix(),
            "runtime_executable_sha256": RUNTIME_SHA256,
            "race_test_xml_sha256": RACETEST_SHA256,
            "course_dx_sha256_before_swap": EXPECTED[cohort]["dx_sha256"],
            "file_count": sum(1 for path in runtime.rglob("*") if path.is_file()),
            "total_file_bytes": sum(path.stat().st_size for path in runtime.rglob("*") if path.is_file()),
            "input_manifest_source_gxm_sha256": stage["cohorts"][cohort]["course_input_gxm_sha256"],
        }
    return result


def inspect_donors() -> dict[str, Any]:
    stage, _ = _load_accepted_inputs()
    runtime_sources = _runtime_sources(stage)
    donors = {}
    for cohort, expected in EXPECTED.items():
        path = _donor_path(cohort)
        regions = parse_regions(path.read_bytes(), cohort)
        validate_regions(
            regions,
            expected_dx_sha256=expected["dx_sha256"],
            expected_tag100_sha256=expected["tag100_sha256"],
        )
        donors[cohort] = _record_regions(regions, path)
    return {
        "phase": PHASE,
        "status": "DONORS_VALIDATED",
        "runtime_sources": runtime_sources,
        "donors": donors,
    }


def _copy_runtime(source: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite staged runtime: {destination}")
    shutil.copytree(source, destination, copy_function=shutil.copy2)


def build() -> dict[str, Any]:
    if OUTPUT_ROOT.exists():
        raise FileExistsError(f"refusing to overwrite R5T-F.1 output: {OUTPUT_ROOT}")
    if RESEARCH_MANIFEST.exists():
        raise FileExistsError(f"refusing to overwrite manifest: {RESEARCH_MANIFEST}")
    stage, differential = _load_accepted_inputs()
    runtime_sources = _runtime_sources(stage)

    donor_paths = {cohort: _donor_path(cohort) for cohort in EXPECTED}
    donor_bytes = {cohort: path.read_bytes() for cohort, path in donor_paths.items()}
    regions, hybrid_bytes = build_reciprocal_bytes(
        donor_bytes["baseline"],
        donor_bytes["modified"],
        expected_baseline_tag_sha256=EXPECTED["baseline"]["tag100_sha256"],
        expected_modified_tag_sha256=EXPECTED["modified"]["tag100_sha256"],
        expected_baseline_dx_sha256=EXPECTED["baseline"]["dx_sha256"],
        expected_modified_dx_sha256=EXPECTED["modified"]["dx_sha256"],
    )
    hybrid_pairs = {
        "hybrid-a": ("baseline", "modified"),
        "hybrid-b": ("modified", "baseline"),
    }
    manifest: dict[str, Any] = {
        "schema": "r5t-f1-tag100-reciprocal-swap-v1",
        "phase": PHASE,
        "status": "READY_FOR_RUNTIME_SWAP_TEST",
        "research_only": True,
        "course_writing": "NOT_IMPLEMENTED",
        "source_probe": {
            "source_node": "Model/$autovsphere_300/$bsp/$nodraw/COLLIDE_finishline03",
            "source_index": 47083,
            "source_triangle_count": 24,
            "unique_source_positions": 14,
            "source_translation": {"axis": "X", "delta": 20.0, "coordinate_space": "GXM"},
            "expected_runtime_translation": {"axis": "X", "delta": 20.0},
            "race_test_xml_unchanged_sha256": RACETEST_SHA256,
        },
        "runtime_executable_sha256": RUNTIME_SHA256,
        "accepted_cooker_differential": {
            "path": REPORT_PATH.relative_to(ROOT).as_posix(),
            "status": differential["status"],
            "run_count_per_cohort": differential["run_count_per_cohort"],
        },
        "donors": {
            cohort: _record_regions(regions[cohort], donor_paths[cohort])
            for cohort in EXPECTED
        },
        "hybrids": {},
        "render_diagnostic": {},
        "runtime_clones": {},
        "interpretation": {
            "tag100_physical_carrier": "UNKNOWN until reciprocal runtime observations",
            "tag100_semantics": "UNKNOWN",
            "tag100_name": "trailing tag100 structure",
            "literal_region_swap": "both hybrids parsed as rev135 with validated render sections",
        },
    }

    output_parent = OUTPUT_ROOT.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    build_root = Path(tempfile.mkdtemp(prefix="r5t_f1-building-", dir=output_parent))
    try:
        (build_root / "runtime").mkdir()
        runtime_template = _runtime_path("baseline")
        runtime_template_non_dx = _tree_hashes(runtime_template, exclude_course_dx=True)
        for name, (prefix_name, tag_name) in hybrid_pairs.items():
            prefix_regions = regions[prefix_name]
            tag_regions = regions[tag_name]
            blob = hybrid_bytes[name]
            hybrid = verify_hybrid_bytes(blob, prefix_regions, tag_regions)
            runtime_destination = build_root / "runtime" / name / "runtime"
            # Both experiments use the exact same baseline-03 runtime tree so
            # France1.gxm and every non-DX resource are held constant.
            _copy_runtime(runtime_template, runtime_destination)
            runtime_dx = runtime_destination / COURSE_DX_REL
            runtime_dx.write_bytes(blob)
            if sha256_file(runtime_dx) != sha256(blob):
                raise ValueError(f"{name}: staged runtime DX hash changed during copy")
            if sha256_file(runtime_destination / "MRallye.exe") != RUNTIME_SHA256:
                raise ValueError(f"{name}: copied runtime executable hash mismatch")
            if sha256_file(runtime_destination / RACETEST_REL) != RACETEST_SHA256:
                raise ValueError(f"{name}: copied RaceTest XML hash mismatch")
            copied_non_dx = _tree_hashes(runtime_destination, exclude_course_dx=True)
            if copied_non_dx != runtime_template_non_dx:
                raise ValueError(f"{name}: a non-DX runtime file differs from the shared template")

            render = _render_diagnostic(hybrid.model)
            donor_render = _render_diagnostic(regions[prefix_name].model)
            if render != donor_render:
                raise ValueError(f"{name}: decoded render geometry differs from prefix donor")
            manifest["hybrids"][name] = {
                "prefix_donor": prefix_name,
                "tag100_donor": tag_name,
                "full_size_bytes": len(blob),
                "full_sha256": sha256(blob),
                "prefix_size_bytes": len(prefix_regions.prefix),
                "prefix_sha256": sha256(prefix_regions.prefix),
                "tag100_size_bytes": len(tag_regions.tag100),
                "tag100_sha256": sha256(tag_regions.tag100),
                "parser_validation": {
                    "revision": hybrid.model.word_0x04,
                    "render_validated": hybrid.model.course_render_validated,
                    "tag100_offset": hybrid.tag_offset,
                    "tag100_end_offset": hybrid.tag_end,
                    "collision_errors": list(hybrid.model.collision.errors),
                    "unparsed_bytes": len(hybrid.model.collision.unparsed_data),
                },
                "provenance_validation": {
                    "prefix_byte_identical_to_donor": hybrid.prefix == prefix_regions.prefix,
                    "tag100_byte_identical_to_donor": hybrid.tag100 == tag_regions.tag100,
                    "total_size_matches_regions": len(blob) == len(prefix_regions.prefix) + len(tag_regions.tag100),
                },
                "staged_runtime_dx_path": (
                    (RUNTIME_ROOT / name / "runtime" / COURSE_DX_REL).relative_to(ROOT).as_posix()
                ),
                "runtime_non_dx_files_byte_identical_to_shared_template": True,
            }
            manifest["render_diagnostic"][name] = {
                "prefix_donor": prefix_name,
                "matches_prefix_donor": render == donor_render,
                **render,
            }
            manifest["runtime_clones"][name] = {
                "source_runtime": runtime_sources["baseline"]["runtime_path"],
                "source_course_gxm_sha256": BASE_GXM_SHA256,
                "staged_runtime": (RUNTIME_ROOT / name / "runtime").relative_to(ROOT).as_posix(),
                "runtime_executable_sha256": RUNTIME_SHA256,
                "race_test_xml_sha256": RACETEST_SHA256,
                "replaced_course_dx_sha256": sha256(blob),
                "non_dx_file_count": len(runtime_template_non_dx),
                "non_dx_tree_hash_sha256": _tree_hashes_sha256(runtime_template_non_dx),
                "non_dx_files_byte_identical_to_shared_template": True,
            }

        # Include the local copy beside the ignored runtime trees for easy verification.
        (build_root / "swap-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        OUTPUT_ROOT.parent.mkdir(parents=True, exist_ok=True)
        os.replace(build_root, OUTPUT_ROOT)
        RESEARCH_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        RESEARCH_MANIFEST.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except Exception:
        if build_root.exists():
            shutil.rmtree(build_root)
        if OUTPUT_ROOT.exists() and not RESEARCH_MANIFEST.exists():
            shutil.rmtree(OUTPUT_ROOT)
        raise
    return manifest


def verify() -> dict[str, Any]:
    manifest = json.loads(RESEARCH_MANIFEST.read_text(encoding="utf-8"))
    local_manifest = json.loads((OUTPUT_ROOT / "swap-manifest.json").read_text(encoding="utf-8"))
    if manifest != local_manifest:
        raise ValueError("tracked and local swap manifests differ")
    stage, _ = _load_accepted_inputs()
    checks = {}
    for name, spec in manifest["hybrids"].items():
        prefix_name = spec["prefix_donor"]
        tag_name = spec["tag100_donor"]
        prefix_path = _donor_path(prefix_name)
        tag_path = _donor_path(tag_name)
        prefix_regions = parse_regions(prefix_path.read_bytes(), prefix_name)
        tag_regions = parse_regions(tag_path.read_bytes(), tag_name)
        runtime_dx = ROOT / spec["staged_runtime_dx_path"]
        blob = runtime_dx.read_bytes()
        hybrid = verify_hybrid_bytes(blob, prefix_regions, tag_regions)
        if sha256(blob) != spec["full_sha256"]:
            raise ValueError(f"{name}: staged hybrid hash mismatch")
        if hybrid.model.word_0x04 != 135 or not hybrid.model.course_render_validated:
            raise ValueError(f"{name}: staged hybrid parser validation failed")
        if sha256_file(runtime_dx.parents[3] / "MRallye.exe") != RUNTIME_SHA256:
            raise ValueError(f"{name}: staged runtime executable hash mismatch")
        if sha256_file(runtime_dx.parents[3] / RACETEST_REL) != RACETEST_SHA256:
            raise ValueError(f"{name}: staged runtime RaceTest XML hash mismatch")
        checks[name] = {
            "prefix_byte_identity": True,
            "tag100_byte_identity": True,
            "full_sha256_matches": True,
            "revision": hybrid.model.word_0x04,
            "render_validated": hybrid.model.course_render_validated,
            "runtime_executable_unchanged": True,
            "race_test_xml_unchanged": True,
        }
    return {"phase": PHASE, "status": "STATIC_SWAP_VALIDATION_PASS", "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inspect", help="validate accepted run-03 donors without writing")
    subparsers.add_parser("build", help="build reciprocal hybrids and isolated runtime clones")
    subparsers.add_parser("verify", help="re-verify staged hybrid provenance and runtime inputs")
    args = parser.parse_args()
    if args.command == "inspect":
        result = inspect_donors()
    elif args.command == "build":
        result = build()
    else:
        result = verify()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
