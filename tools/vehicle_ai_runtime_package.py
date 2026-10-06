#!/usr/bin/env python3
"""Stage and verify the exact R5V-H.0 forced-ID26 runtime package.

The package combines one hash-locked H executable with the pinned G.1
VehicleSelect overlay and all resource components from the verified G.1 runtime
profile. Runtime-generated PlayerState files are deliberately excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Any

try:
    import build_vehicle_ai_candidate as ai_candidate
    import vehicle_unlock_runtime_package as unlock_package
except ImportError:  # pragma: no cover - package-style import for tests
    from tools import build_vehicle_ai_candidate as ai_candidate
    from tools import vehicle_unlock_runtime_package as unlock_package


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_G1_ROOT = REPO_ROOT / ".research-output/vehicles/unlock/runtime-package"
DEFAULT_CANDIDATE = REPO_ROOT / ".research-output/vehicles/ai/forced-id26-proof/candidate/MRallye.exe"
DEFAULT_CANDIDATE_MANIFEST = DEFAULT_CANDIDATE.with_name("patch-manifest.json")
DEFAULT_RUNTIME_ROOT = REPO_ROOT / ".research-output/vehicles/ai/forced-id26-proof/runtime-package"
PACKAGE_MANIFEST_NAME = "runtime-package-manifest.json"
H_MODE = "forced-id26-proof"
EXPECTED_H_SHA256 = "dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13"
EXPECTED_H_MANIFEST_SHA256 = "68ee11ae153daf4a48974676dd9f1bb31245cb774a4beee53ec165134d537fca"
EXPECTED_H_SIZE = 3121214
EXPECTED_G1_RUNTIME_EXE_SHA256 = unlock_package.FINAL_RACE_DETAILS_EXE_SHA256
EXPECTED_G2_PROFILE_ID = 0
MERCEDES_ASSET_ROOT = "DataGx/Vehicles/Mercedes"
VERIFY_FILE_NAME = "VERIFY_RUNTIME.txt"


class RuntimePackageError(ValueError):
    """Raised when a candidate or runtime package does not match its pins."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, role: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimePackageError(f"cannot read {role}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimePackageError(f"{role} must be a JSON object")
    return data


def _safe_path(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if (rel.is_absolute() or not rel.parts or "\\" in relative
            or any(part in ("", ".", "..") for part in rel.parts)):
        raise RuntimePackageError(f"unsafe relative package path: {relative}")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimePackageError(f"symbolic link is not accepted: {relative}")
    return current


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validated_candidate(candidate: Path, candidate_manifest: Path,
                         retail_exe: Path) -> dict[str, Any]:
    candidate = candidate.resolve(strict=True)
    manifest_path = candidate_manifest.resolve(strict=True)
    retail_exe = retail_exe.resolve(strict=True)
    output_root = (REPO_ROOT / ".research-output").resolve(strict=False)
    if not _is_under(candidate, output_root):
        raise RuntimePackageError("H candidate must be under this checkout's .research-output")
    if candidate.stat().st_size != EXPECTED_H_SIZE or sha256_file(candidate) != EXPECTED_H_SHA256:
        raise RuntimePackageError("H candidate executable hash/size is not the pinned R5V-H.0 build")
    if sha256_file(manifest_path) != EXPECTED_H_MANIFEST_SHA256:
        raise RuntimePackageError("H patch manifest hash is not the pinned R5V-H.0 manifest")
    try:
        ai_candidate.verify_existing(retail_exe, candidate, manifest_path, mode=H_MODE)
    except (ai_candidate.CandidateError, OSError, ValueError) as exc:
        raise RuntimePackageError(f"H candidate reproduction failed: {exc}") from exc
    data = _load_json(manifest_path, "H patch manifest")
    proof = data.get("ai_proof")
    audio = data.get("audio_identity")
    expected_guard = {
        "current_slot_esi": 1,
        "end_slot_ebp": 4,
        "class_argument": 0,
        "player_car_id_required": False,
        "caller_return_required": False,
        "exclusion_argument_slots_read": False,
    }
    if (data.get("h_research_mode") != H_MODE
            or data.get("patched_sha256") != EXPECTED_H_SHA256
            or not isinstance(proof, dict)
            or proof.get("guard") != expected_guard
            or proof.get("participant_count_changed") is not False
            or proof.get("ai_pool_membership_changed") is not False
            or not isinstance(audio, dict)
            or audio.get("stock_audio_profile_id") != EXPECTED_G2_PROFILE_ID):
        raise RuntimePackageError("H patch manifest mode, guard, or G.2 audio policy is invalid")
    return {
        "path": "MRallye.exe",
        "sha256": EXPECTED_H_SHA256,
        "size": EXPECTED_H_SIZE,
        "patch_manifest_sha256": EXPECTED_H_MANIFEST_SHA256,
        "mode": H_MODE,
        "g2_audio_profile_id": EXPECTED_G2_PROFILE_ID,
        "source_sha256": data.get("source_sha256"),
        "g1_base_sha256": data.get("g1_base_sha256"),
        "g2_base_sha256": data.get("g2_base_sha256"),
    }


def _component_rows(root: Path, profile: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    by_component: dict[str, dict[str, Any]] = {}
    for component in profile["components"]:
        relative = str(component["root"])
        base = _safe_path(root, relative)
        if component["kind"] == "file":
            paths = [base] if base.is_file() else []
        else:
            if not base.is_dir():
                raise RuntimePackageError(f"required resource component is missing: {relative}")
            paths = sorted(base.rglob("*"))
            if any(path.is_symlink() for path in paths):
                raise RuntimePackageError(f"symbolic links are not accepted in resource component: {relative}")
            paths = [path for path in paths if path.is_file()]
        component_rows = [unlock_package._file_row(path, path.relative_to(root).as_posix())
                          for path in paths]
        component_rows.sort(key=lambda row: row["path"].casefold())
        if (len(component_rows) != component["file_count"]
                or sum(row["size"] for row in component_rows) != component["total_bytes"]
                or unlock_package._inventory_sha256(component_rows) != component["inventory_sha256"]):
            raise RuntimePackageError(f"pinned G.1 resource inventory mismatch: {relative}")
        rows.extend(component_rows)
        by_component[relative.casefold()] = {
            "path": relative,
            "file_count": len(component_rows),
            "total_bytes": sum(row["size"] for row in component_rows),
            "inventory_sha256": unlock_package._inventory_sha256(component_rows),
            "files": component_rows,
        }
    rows.sort(key=lambda row: row["path"].casefold())
    return rows, by_component


def _resource_rows(root: Path, profile: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows, components = _component_rows(root, profile)
    scene_path = _safe_path(root, unlock_package.SCENE_RELATIVE.as_posix())
    if not scene_path.is_file():
        raise RuntimePackageError("qualified VehicleSelect.xml is missing")
    scene_row = unlock_package._file_row(scene_path, unlock_package.SCENE_RELATIVE.as_posix())
    if scene_row["sha256"] != unlock_package.EXPECTED_SCENE_SHA256:
        raise RuntimePackageError("VehicleSelect.xml does not match the pinned G.1 overlay")
    rows.append(scene_row)
    rows.sort(key=lambda row: row["path"].casefold())
    return rows, components


def _runtime_manifest(*, candidate: dict[str, Any], profile: dict[str, Any],
                      profile_sha256: str, resource_rows: list[dict[str, Any]],
                      components: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mercedes = components.get(MERCEDES_ASSET_ROOT.casefold())
    if not mercedes or mercedes["file_count"] < 1:
        raise RuntimePackageError("pinned profile does not provide Mercedes runtime assets")
    return {
        "schema_version": 1,
        "status": "R5V_H0_RUNTIME_PACKAGE_READY_FOR_HUMAN",
        "phase": "R5V-H.0 forced ID26 AI proof correction",
        "candidate": candidate,
        "resource_root": ".",
        "effective_vehicle_select_scene": {
            "path": unlock_package.SCENE_RELATIVE.as_posix(),
            "sha256": unlock_package.EXPECTED_SCENE_SHA256,
        },
        "g1_resource_profile": {
            "profile": profile["profile"],
            "profile_sha256": profile_sha256,
            "source_executable_sha256": EXPECTED_G1_RUNTIME_EXE_SHA256,
            "fresh_profile": True,
            "player_state_files_staged": False,
        },
        "mercedes_runtime_assets": {
            "root": MERCEDES_ASSET_ROOT,
            "file_count": mercedes["file_count"],
            "total_bytes": mercedes["total_bytes"],
            "inventory_sha256": mercedes["inventory_sha256"],
        },
        "g2_audio_policy": {"stock_audio_profile_id": EXPECTED_G2_PROFILE_ID},
        "resource_files": resource_rows,
        "component_inventories": [
            {key: component[key] for key in ("path", "file_count", "total_bytes", "inventory_sha256")}
            for _, component in sorted(components.items())
        ],
        "runtime_provenance_contract": {
            "capture_source_fields": ["image_sha256", "image_path", "active_root"],
            "image_path": "<runtime_root>/MRallye.exe",
            "active_root": "<runtime_root>",
        },
    }


def _verify_tree(root: Path, *, candidate: dict[str, Any], profile: dict[str, Any],
                 profile_sha256: str, enforce_output_root: bool) -> dict[str, Any]:
    root = (unlock_package.validate_output_root(root, REPO_ROOT) if enforce_output_root
            else root.resolve(strict=True))
    if not root.is_dir():
        raise RuntimePackageError("runtime root must be a directory")
    resource_rows, components = _resource_rows(root, profile)
    exe = _safe_path(root, "MRallye.exe")
    if (not exe.is_file() or exe.stat().st_size != EXPECTED_H_SIZE
            or sha256_file(exe) != candidate["sha256"]):
        raise RuntimePackageError("runtime package executable does not match the pinned H candidate")
    if candidate["patch_manifest_sha256"] != EXPECTED_H_MANIFEST_SHA256:
        raise RuntimePackageError("runtime manifest refers to another H candidate manifest")

    expected_manifest = _runtime_manifest(
        candidate=candidate, profile=profile, profile_sha256=profile_sha256,
        resource_rows=resource_rows, components=components,
    )
    expected_paths = {"MRallye.exe", PACKAGE_MANIFEST_NAME}
    expected_paths.update(row["path"] for row in resource_rows)
    actual_paths: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimePackageError(f"runtime package contains a symbolic link: {path}")
        if path.is_file():
            actual_paths.add(path.relative_to(root).as_posix())
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)
        raise RuntimePackageError(f"runtime package file set differs (missing={missing[:5]}, extra={extra[:5]})")
    stored = _load_json(_safe_path(root, PACKAGE_MANIFEST_NAME), "H runtime-package manifest")
    if stored != expected_manifest:
        raise RuntimePackageError("H runtime-package manifest differs from the pinned expected package")
    return {
        "status": "PASS",
        "exe": "PASS",
        "root": "PASS",
        "vehicle_select_xml": "PASS",
        "mercedes_assets": "PASS",
        "mode": "PASS",
        "effective_executable": str(exe),
        "executable_sha256": candidate["sha256"],
        "effective_root": str(root),
        "effective_vehicle_select_scene": str(_safe_path(root, unlock_package.SCENE_RELATIVE.as_posix())),
        "vehicle_select_sha256": unlock_package.EXPECTED_SCENE_SHA256,
        "mercedes_asset_root": str(_safe_path(root, MERCEDES_ASSET_ROOT)),
        "mercedes_asset_files": components[MERCEDES_ASSET_ROOT.casefold()]["file_count"],
        "candidate_mode": H_MODE,
        "stock_audio_profile_id": EXPECTED_G2_PROFILE_ID,
        "fresh_profile": "PlayerState.xml excluded",
        "file_count": len(actual_paths),
    }


def verify_runtime_package(runtime_root: Path, candidate_manifest: Path,
                           retail_exe: Path, *,
                           profile_path: Path = unlock_package.DEFAULT_PROFILE,
                           enforce_output_root: bool = True) -> dict[str, Any]:
    try:
        candidate = _validated_candidate(
            runtime_root / "MRallye.exe",
            candidate_manifest,
            retail_exe,
        )
        profile, profile_sha256 = unlock_package._load_profile(profile_path)
    except (OSError, unlock_package.PackageError) as exc:
        raise RuntimePackageError(f"runtime verifier input rejected: {exc}") from exc
    result = _verify_tree(
        runtime_root, candidate=candidate, profile=profile,
        profile_sha256=profile_sha256, enforce_output_root=enforce_output_root,
    )
    if result["executable_sha256"] != EXPECTED_H_SHA256:
        raise RuntimePackageError("effective runtime EXE SHA256 mismatch")
    return result


def _stage(runtime_source: Path, candidate_exe: Path, candidate_manifest: Path,
           retail_exe: Path, output_root: Path,
           profile_path: Path = unlock_package.DEFAULT_PROFILE) -> dict[str, Any]:
    source = runtime_source.resolve(strict=True)
    output = unlock_package.validate_output_root(output_root, REPO_ROOT)
    if output.exists():
        raise RuntimePackageError("H runtime output already exists; choose a new package path")
    verify_file = output.parent / VERIFY_FILE_NAME
    if verify_file.exists():
        raise RuntimePackageError("H runtime verification handoff already exists")
    if output == source or _is_under(output, source) or _is_under(source, output):
        raise RuntimePackageError("output must be separate from the verified G.1 source package")
    source_real = unlock_package.validate_output_root(source, REPO_ROOT)
    source_verification = unlock_package.verify_package(
        source_real, profile_path, repo_root=REPO_ROOT,
        enforce_output_root=True, allow_runtime_state=True,
    )
    if source_verification["executable_sha256"] != EXPECTED_G1_RUNTIME_EXE_SHA256:
        raise RuntimePackageError("G.1 resource source must be the exact final qualified G.1 package")
    source_manifest = _load_json(source / unlock_package.PACKAGE_MANIFEST_NAME,
                                 "verified G.1 package manifest")
    candidate = _validated_candidate(candidate_exe, candidate_manifest, retail_exe)
    profile, profile_sha256 = unlock_package._load_profile(profile_path)

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    try:
        # Copy only profile-pinned resources. Generated PlayerState files and
        # the old G.1 EXE/manifest are intentionally not propagated.
        for component in profile["components"]:
            relative = str(component["root"])
            source_component = unlock_package._path_for(source, relative)
            if component["kind"] == "file":
                files = [source_component]
            else:
                files = sorted(path for path in source_component.rglob("*") if path.is_file())
            for file_path in files:
                rel = file_path.relative_to(source).as_posix()
                target = _safe_path(temp, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file_path, target)
        scene_rel = unlock_package.SCENE_RELATIVE.as_posix()
        source_scene = unlock_package._path_for(source, scene_rel)
        scene_target = _safe_path(temp, scene_rel)
        scene_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_scene, scene_target)
        shutil.copyfile(candidate_exe.resolve(strict=True), temp / "MRallye.exe")

        resource_rows, components = _resource_rows(temp, profile)
        manifest = _runtime_manifest(
            candidate=candidate, profile=profile, profile_sha256=profile_sha256,
            resource_rows=resource_rows, components=components,
        )
        # The source G.1 manifest is consumed only after its package verifier
        # has validated every component. Its records are not copied into H.
        if source_manifest.get("candidate_executable", {}).get("sha256") != EXPECTED_G1_RUNTIME_EXE_SHA256:
            raise RuntimePackageError("G.1 source manifest executable provenance mismatch")
        (temp / PACKAGE_MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        # Recompute the expected manifest with the included provenance count.
        result = _verify_tree(
            temp, candidate=candidate, profile=profile,
            profile_sha256=profile_sha256, enforce_output_root=False,
        )
        os.replace(temp, output)
        result = _verify_tree(
            output, candidate=candidate, profile=profile,
            profile_sha256=profile_sha256, enforce_output_root=True,
        )
        verify_text = _verification_instructions(output, candidate_manifest, retail_exe)
        verify_file.write_text(verify_text, encoding="utf-8")
        result["status"] = "PASS_STAGED"
        result["source_g1_package"] = str(source)
        result["runtime_verification_file"] = str(verify_file)
        return result
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise


def _verification_instructions(runtime_root: Path, candidate_manifest: Path,
                               retail_exe: Path) -> str:
    return (
        "R5V-H.0 verified runtime package\n\n"
        "Run from the master-rallye-re-vehicles checkout before launch:\n\n"
        "$env:PYTHONPATH = (Resolve-Path 'src').Path\n"
        "python tools\\vehicle_ai_runtime_package.py verify `\n"
        f"  --runtime-root '{runtime_root}' `\n"
        f"  --candidate-manifest '{candidate_manifest.resolve()}' `\n"
        f"  --retail-exe '{retail_exe.resolve()}'\n\n"
        f"Expected EXE SHA256: {EXPECTED_H_SHA256}\n"
        f"Expected VehicleSelect.xml SHA256: {unlock_package.EXPECTED_SCENE_SHA256}\n"
        "Launch MRallye.exe from this package root only after all verifier checks print PASS.\n"
        "After launch, verify the Broker raw-dump Root header equals this package root.\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage", help="create a coherent ignored H runtime package")
    stage.add_argument("--source-g1-root", type=Path, default=DEFAULT_G1_ROOT)
    stage.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    stage.add_argument("--candidate-manifest", type=Path, default=DEFAULT_CANDIDATE_MANIFEST)
    stage.add_argument("--retail-exe", type=Path, required=True)
    stage.add_argument("--output-root", type=Path, default=DEFAULT_RUNTIME_ROOT)
    verify = sub.add_parser("verify", help="fail-closed verification before runtime launch")
    verify.add_argument("--runtime-root", type=Path, required=True)
    verify.add_argument("--candidate-manifest", type=Path, required=True)
    verify.add_argument("--retail-exe", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "stage":
            result = _stage(args.source_g1_root, args.candidate,
                            args.candidate_manifest, args.retail_exe,
                            args.output_root)
        else:
            result = verify_runtime_package(
                args.runtime_root, args.candidate_manifest, args.retail_exe,
            )
    except (RuntimePackageError, unlock_package.PackageError, OSError, ValueError) as exc:
        parser.exit(2, f"vehicle H runtime package refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.command == "verify":
        print("EXE                PASS")
        print("ROOT               PASS")
        print("VEHICLESELECT XML  PASS")
        print("MERCEDES ASSETS    PASS")
        print("MODE               PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
