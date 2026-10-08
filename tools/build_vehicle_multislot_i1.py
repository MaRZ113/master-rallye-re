#!/usr/bin/env python3
"""Build the R5V-I.1 authored, independent-family T2 qualifier candidate.

The executable keeps the already runtime-qualified physical ID27 / T2 local7
architecture. Its record now names an independently packaged R5VQualifier
model/physics family; the human-runtime package builder stages those resources.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

try:
    import build_vehicle_multislot_i0 as i0
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style imports for tests
    from tools import build_vehicle_multislot_i0 as i0
    from tools import patch_vehicle_registry_id26 as registry


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT.parent / "corpora" / "retail" / "MRallye.exe"
DEFAULT_OUTPUT = REPOSITORY_ROOT / ".research-output/vehicles/multislot/i1/candidate/MRallye.exe"
DEFAULT_MANIFEST = DEFAULT_OUTPUT.with_suffix(".manifest.json")

PROFILE = "i1-id27-r5v-qualifier-independent-t2-family"
PHASE = "R5V-I.1 authored independent T2 qualification vehicle"
RESULTS_LABEL = "R5V TEST DRIVER"
RUNTIME_FAMILY = "R5VQualifier"
DISPLAY_MANUFACTURER = "R5V"
DISPLAY_MODEL = "T2 QUALIFIER"
DISPLAY_COMBINED = "R5V T2 QUALIFIER"

ID27_RECORD = replace(
    i0.ID27_RECORD,
    profile_id=PROFILE,
    internal_name=RUNTIME_FAMILY,
    runtime_family=RUNTIME_FAMILY,
    model_family=RUNTIME_FAMILY,
    wheel_family=RUNTIME_FAMILY,
    physics_family=f"Vehicles/{RUNTIME_FAMILY}",
    asset_package=f"DataGx/Vehicles/{RUNTIME_FAMILY}",
    display_manufacturer=DISPLAY_MANUFACTURER,
    display_model=DISPLAY_MODEL,
    display_quickrace=DISPLAY_COMBINED,
    race_colour_rgba_bits=(0x3F800000,) * 4,
    race_colour_role="neutral authored qualifier tint; body DXT is the visual canary",
)


class CandidateError(ValueError):
    """Unsupported base or a deterministic I.1 candidate mismatch."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _absolute_without_links(path: Path, label: str) -> Path:
    """Canonicalize lexically while refusing linked output paths on Windows."""
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise CandidateError(f"{label} path contains a symlink or junction: {current}")
    return absolute


def make_candidate(data: bytes) -> tuple[bytes, dict[str, Any]]:
    try:
        candidate, manifest = i0.make_candidate(
            data,
            id27_record=ID27_RECORD,
            results_label=RESULTS_LABEL,
            profile=PROFILE,
            phase=PHASE,
        )
    except (i0.CandidateError, registry.PatchError, ValueError) as exc:
        raise CandidateError(f"could not compose the exact retail/H.2/I.0 registry layer: {exc}") from exc

    id27 = manifest["profiles"][1]
    id27.update({
        "profile_role": "AUTHORED SDK QUALIFICATION VEHICLE; NOT HISTORICAL CONTENT",
        "asset_directory": f"DataGx/Vehicles/{RUNTIME_FAMILY}",
        "asset_directory_is_independent": True,
        "physics_family_is_independent": True,
        "collision": "Navara-derived donor geometry; not a unique collision qualification",
        "frontend_art": "DONOR FRONTEND ART (Navara frame 23)",
        "stats": [7, 6, 6, 5],
        "stats_provenance": "Navara donor-derived, unchanged",
        "smallcarsheet_index": 13,
        "vehicle_select_frame": 23,
        "unlock_oracle_id": 10,
        "unlock_path": "Progress/UnlockedCars/T2CupCar1",
        "audio_profile_id": 7,
        "ai_pools": ["quickrace:T2", "rallye_cup:new-roster:T2", "master_rallye:new-competition:T2"],
        "native_driver_id_changed": False,
        "donor_frontend_art": True,
        "source_donor_physical_id": 7,
        "results_display": RESULTS_LABEL,
        "authenticity": "authored qualification family; not a historical Master Rallye vehicle",
    })
    manifest["runtime_architecture"].update({
        "id27_family_name": RUNTIME_FAMILY,
        "id27_asset_payload_required": True,
        "id27_physics_overlay_required": True,
        "id27_independent_family_candidate": True,
        "id27_is_real_independent_t2_payload": False,
        "id27_independent_family_qualification": True,
        "id27_model_and_physics_content_are_navara_derived": True,
        "physical_car_id_aliasing": False,
        "randomizer_present": False,
        "participant_count_changed": False,
    })
    manifest["higher_phase_boundary"].update({
        "i1_independent_family": "READY_FOR_HUMAN_RUNTIME",
        "i0_slot_architecture": "CONFIRMED_BY_RUNTIME / FULL PASS / CLOSED",
        "i1_real_t2_payload": "AUTHORED_R5VQUALIFIER_FAMILY; NAVARA_DERIVED; NOT_HISTORICAL_CONTENT",
        "r5v_i_full_pass": False,
        "r5v_j_started": False,
    })
    _verify_structure(candidate, manifest)
    return candidate, manifest


def _verify_structure(candidate: bytes, manifest: dict[str, Any]) -> None:
    i0._verify_structure(candidate, manifest, expected_profile=PROFILE,
                         expected_id27_name=RUNTIME_FAMILY)
    if manifest.get("phase") != PHASE or manifest.get("status") != "READY_FOR_HUMAN_RUNTIME":
        raise CandidateError("candidate is not the pinned I.1 qualification profile")
    if manifest.get("source_sha256") != i0.RETAIL_SHA256:
        raise CandidateError("candidate source is not the exact pristine retail executable")
    if manifest.get("parent_candidate", {}).get("sha256") != i0.H2_SHA256:
        raise CandidateError("candidate does not compose from the exact H.2 parent")
    boundary = manifest.get("higher_phase_boundary", {})
    if (boundary.get("i0_slot_architecture") != "CONFIRMED_BY_RUNTIME / FULL PASS / CLOSED"
            or boundary.get("i1_real_t2_payload") !=
            "AUTHORED_R5VQUALIFIER_FAMILY; NAVARA_DERIVED; NOT_HISTORICAL_CONTENT"
            or boundary.get("r5v_i_full_pass") is not False
            or boundary.get("r5v_j_started") is not False):
        raise CandidateError("I.1 candidate status metadata overstates slot or family qualification")
    id26, id27 = manifest.get("profiles", [{}, {}])
    if (id26.get("physical_id"), id26.get("runtime_family"), id26.get("results_display")) != (
            26, "Mercedes", "JEAN-PIERRE STRUGO"):
        raise CandidateError("I.1 must preserve the runtime-qualified ID26 Mercedes profile")
    expected = {
        "physical_id": 27,
        "class": 1,
        "local_index": 7,
        "name": RUNTIME_FAMILY,
        "runtime_family": RUNTIME_FAMILY,
        "model_family": RUNTIME_FAMILY,
        "wheel_family": RUNTIME_FAMILY,
        "physics_family": f"Vehicles/{RUNTIME_FAMILY}",
        "asset_directory": f"DataGx/Vehicles/{RUNTIME_FAMILY}",
        "asset_directory_is_independent": True,
        "physics_family_is_independent": True,
        "unlock_oracle_id": 10,
        "audio_profile_id": 7,
        "results_display": RESULTS_LABEL,
        "native_driver_id_changed": False,
        "collision": "Navara-derived donor geometry; not a unique collision qualification",
        "authenticity": "authored qualification family; not a historical Master Rallye vehicle",
    }
    for field, value in expected.items():
        if id27.get(field) != value:
            raise CandidateError(f"I.1 ID27 manifest field {field!r} is not {value!r}")
    if id27.get("display") != {
            "manufacturer": DISPLAY_MANUFACTURER,
            "model": DISPLAY_MODEL,
            "combined": DISPLAY_COMBINED,
            "results": RESULTS_LABEL}:
        raise CandidateError("I.1 frontend or Results identity differs from the authored qualifier")
    if manifest.get("class_mapping", {}).get("T2_local7") != 27:
        raise CandidateError("physical ID27 must remain T2 local7")
    if manifest.get("ai_pools", {}).get("quickrace_t2") != [7, 8, 9, 10, 11, 12, 13, 27]:
        raise CandidateError("the I.0 T2 Quick Race pool was changed")
    for mode in ("rallye_cup_t2_new_roster_only", "master_rallye_t2_new_competition_only"):
        if manifest.get("ai_pools", {}).get(mode) != [7, 8, 9, 10, 11, 12, 13, 27]:
            raise CandidateError(f"the I.0 {mode} pool was changed")
    if id27.get("display", {}).get("manufacturer") == "SLOT PROOF" or id27.get("name") == "Navara":
        raise CandidateError("I.0 donor identity leaked into I.1 runtime identity")
    architecture = manifest.get("runtime_architecture", {})
    if (architecture.get("id27_independent_family_qualification") is not True
            or architecture.get("id27_is_real_independent_t2_payload") is not False
            or architecture.get("id27_model_and_physics_content_are_navara_derived") is not True):
        raise CandidateError("I.1 family-path proof must remain distinct from a unique-content claim")


def verify_existing(source: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    source = Path(os.path.abspath(source))
    output = _absolute_without_links(output, "candidate")
    manifest_path = _absolute_without_links(manifest_path, "candidate manifest")
    if not output.is_file() or not manifest_path.is_file():
        raise CandidateError("candidate executable or manifest is missing")
    if not source.is_file():
        raise CandidateError("pristine retail source is not a regular file")
    if (os.path.normcase(str(source)) == os.path.normcase(str(output))
            or os.path.samefile(source, output)):
        raise CandidateError("candidate must not overwrite pristine retail")
    expected_candidate, expected_manifest = make_candidate(source.read_bytes())
    if output.read_bytes() != expected_candidate:
        raise CandidateError("existing I.1 executable differs from deterministic retail rebuild")
    expected_manifest_bytes = (json.dumps(expected_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if manifest_path.read_bytes() != expected_manifest_bytes:
        raise CandidateError("existing I.1 manifest differs from deterministic rebuild")
    return expected_manifest


def write_candidate(source: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    source = Path(os.path.abspath(source))
    if not source.is_file():
        raise CandidateError("pristine retail source is not a regular file")
    output = _absolute_without_links(output, "candidate")
    manifest_path = _absolute_without_links(manifest_path, "candidate manifest")
    if (output.exists() or manifest_path.exists()
            or os.path.normcase(str(output)) == os.path.normcase(str(source))):
        raise CandidateError("refusing to overwrite source, candidate or manifest")
    if not registry._is_research_output(output) or not registry._is_research_output(manifest_path):
        raise CandidateError("I.1 candidate and manifest must remain under ignored research-output")
    raw = source.read_bytes()
    before = sha256(raw)
    candidate, manifest = make_candidate(raw)
    if before != manifest["source_sha256"]:
        raise CandidateError("retail source changed while the candidate was being built")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8", newline="\n")
    if sha256(output.read_bytes()) != manifest["patched_sha256"]:
        raise CandidateError("written candidate failed its output SHA256 check")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    build.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    build.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    verify = sub.add_parser("verify")
    verify.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    verify.add_argument("--candidate", type=Path, default=DEFAULT_OUTPUT)
    verify.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = write_candidate(args.source, args.output, args.manifest)
            candidate_path = args.output
        else:
            result = verify_existing(args.source, args.candidate, args.manifest)
            candidate_path = args.candidate
    except (CandidateError, i0.CandidateError, registry.PatchError, OSError,
            ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"R5V-I.1 candidate refused: {exc}\n")
    print(json.dumps({
        "status": "VERIFIED" if args.command == "verify" else result["status"],
        "profile": result["profile"],
        "source_sha256": result["source_sha256"],
        "h2_sha256": result["parent_candidate"]["sha256"],
        "candidate_sha256": result["patched_sha256"],
        "size": result["file_size"],
        "id27": result["profiles"][1],
        "output": str(candidate_path.resolve(strict=False)),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
