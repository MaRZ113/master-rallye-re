#!/usr/bin/env python3
"""Stage and verify coherent G.1/G.2 hardened Mercedes runtime packages.

The source resource tree must be the exact captured G.1 package. Only the
profile-pinned components and the pinned VehicleSelect overlay are copied;
runtime-generated PlayerState files are excluded. The candidate EXE remains
separately rebuildable and hash-verified from pristine retail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import tempfile
from typing import Any

try:
    import build_vehicle_hardened_candidate as candidate_builder
    import build_vehicle_natural_t1_candidate as natural_candidate_builder
    import vehicle_unlock_runtime_package as unlock
except ImportError:  # pragma: no cover - package-style import for tests
    from tools import build_vehicle_hardened_candidate as candidate_builder
    from tools import build_vehicle_natural_t1_candidate as natural_candidate_builder
    from tools import vehicle_unlock_runtime_package as unlock


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = REPO_ROOT / ".research-output/vehicles/unlock/runtime-package"
DEFAULT_RETAIL = REPO_ROOT.parent / "corpora/retail/MRallye.exe"
PACKAGE_MANIFEST = "hardened-runtime-package.json"
SCENE = unlock.SCENE_RELATIVE.as_posix()
SUPPORTED_RUNTIME_PROFILES = candidate_builder.SUPPORTED_PROFILES + (natural_candidate_builder.PROFILE,)


class RuntimePackageError(ValueError):
    """Raised when the package source, staged tree, or candidate is unsupported."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_path(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    win = PureWindowsPath(relative)
    if rel.is_absolute() or win.is_absolute() or bool(win.drive) or not rel.parts or "\\" in relative or any(
            part in ("", ".", "..") for part in rel.parts):
        raise RuntimePackageError(f"unsafe package-relative path: {relative}")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimePackageError(f"symbolic link is not accepted: {relative}")
    return current


def _inventory(source_root: Path, profile: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for component in profile["components"]:
        base = unlock._path_for(source_root, str(component["root"]))
        files = [base] if component["kind"] == "file" else sorted(
            path for path in base.rglob("*") if path.is_file()
        )
        component_rows = [unlock._file_row(path, path.relative_to(source_root).as_posix())
                          for path in files]
        component_rows.sort(key=lambda row: row["path"].casefold())
        if (len(component_rows) != component["file_count"]
                or sum(row["size"] for row in component_rows) != component["total_bytes"]
                or unlock._inventory_sha256(component_rows) != component["inventory_sha256"]):
            raise RuntimePackageError(f"source component differs from pinned profile: {component['root']}")
        rows.extend(component_rows)
    rows.append({
        "path": SCENE,
        "size": unlock._path_for(source_root, SCENE).stat().st_size,
        "sha256": unlock.EXPECTED_SCENE_SHA256,
    })
    rows.sort(key=lambda row: row["path"].casefold())
    return rows


def _expected_manifest(*, profile: dict[str, Any], profile_sha256: str,
                       candidate: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    natural = candidate["profile"] == natural_candidate_builder.PROFILE
    result = {
        "schema_version": 1,
        "status": ("R5V_H1_NATURAL_T1_RUNTIME_PACKAGE_READY_FOR_HUMAN" if natural
                    else "R5V_H0_1_HARDENED_RUNTIME_PACKAGE"),
        "profile": candidate["profile"],
        "candidate": {
            "path": "MRallye.exe",
            "sha256": candidate["patched_sha256"],
            "size": candidate["file_size"],
            "patch_manifest_sha256": candidate["patch_manifest_sha256"],
        },
        "resource_source_profile": profile.get("profile"),
        "resource_source_profile_sha256": profile_sha256,
        "resource_root": ".",
        "vehicle_select_scene": {"path": SCENE, "sha256": unlock.EXPECTED_SCENE_SHA256},
        "fresh_profile_policy": {
            "PlayerState.xml": "excluded; first launch creates a fresh profile",
            "PlayerState.xml#": "excluded",
            "options.xml#": "excluded",
        },
        "resources": rows,
        "randomizer": "not present",
        "forced_ai_proof": candidate["profile"] == candidate_builder.PROFILE_FORCED,
    }
    if natural:
        result["natural_t1_id26_pool"] = True
        result["participant_count_changed"] = False
        result["results_name_policy"] = {
            "physical_car_id": 26,
            "display_name": natural_candidate_builder.RESULTS_FIXED_DISPLAY_NAME,
            "native_driver_id_selection_changed": False,
        }
    return result


def _validate_candidate(exe: Path, manifest_path: Path, retail: Path,
                        profile_name: str) -> dict[str, Any]:
    try:
        if profile_name == natural_candidate_builder.PROFILE:
            manifest = natural_candidate_builder.verify_existing(retail, exe, manifest_path)
        else:
            manifest = candidate_builder.verify_existing(retail, exe, manifest_path, profile_name)
    except (candidate_builder.CandidateError, natural_candidate_builder.CandidateError,
            OSError, ValueError) as exc:
        raise RuntimePackageError(f"candidate verification failed: {exc}") from exc
    return {
        "profile": manifest["profile"],
        "patched_sha256": manifest["patched_sha256"],
        "file_size": manifest["file_size"],
        "patch_manifest_sha256": sha256_file(manifest_path),
        "randomizer_present": manifest["randomizer"]["present"],
        "forced_ai_proof": manifest.get("forced_ai_proof", {}).get("included", False),
        "natural_t1_id26_pool": manifest.get("natural_t1_id26_pool", {}).get("included", False),
        "results_name_policy": manifest.get("results_identity", {}).get("policy"),
    }


def verify_package(runtime_root: Path, candidate_manifest: Path, retail: Path,
                   source_root: Path, profile_name: str, *,
                   profile_path: Path = unlock.DEFAULT_PROFILE,
                   enforce_output_root: bool = True) -> dict[str, Any]:
    try:
        root = (unlock.validate_output_root(runtime_root, REPO_ROOT) if enforce_output_root
                else runtime_root.resolve(strict=True))
        source = source_root.resolve(strict=True)
        candidate_manifest = candidate_manifest.resolve(strict=True)
        retail = retail.resolve(strict=True)
        profile, profile_sha = unlock._load_profile(profile_path)
        source_report = unlock.verify_package(
            source, profile_path, repo_root=REPO_ROOT,
            enforce_output_root=enforce_output_root, allow_runtime_state=True,
        )
        if source_report["executable_sha256"] != unlock.FINAL_RACE_DETAILS_EXE_SHA256:
            raise RuntimePackageError("resource source is not the pinned final G.1 package")
    except (OSError, unlock.PackageError) as exc:
        raise RuntimePackageError(f"runtime verifier input refused: {exc}") from exc
    candidate = _validate_candidate(root / "MRallye.exe", candidate_manifest, retail, profile_name)
    if candidate["randomizer_present"] is not False:
        raise RuntimePackageError("candidate contains a randomizer")
    rows = _inventory(root, profile)
    expected = _expected_manifest(
        profile=profile, profile_sha256=profile_sha,
        candidate={**candidate, "patch_manifest_sha256": candidate["patch_manifest_sha256"]},
        rows=rows,
    )
    expected_paths = {row["path"] for row in rows} | {"MRallye.exe", PACKAGE_MANIFEST}
    actual_paths: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimePackageError(f"runtime package contains a symbolic link: {path}")
        if path.is_file():
            actual_paths.add(path.relative_to(root).as_posix())
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)
        raise RuntimePackageError(f"runtime package file set differs (missing={missing[:4]}, extra={extra[:4]})")
    try:
        stored = json.loads((root / PACKAGE_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimePackageError("runtime package manifest is invalid") from exc
    if stored != expected:
        raise RuntimePackageError("runtime package manifest differs from verified files")
    if sha256_file(root / "MRallye.exe") != candidate["patched_sha256"]:
        raise RuntimePackageError("runtime executable hash mismatch")
    return {
        "status": "PASS",
        "profile": profile_name,
        "executable": str(root / "MRallye.exe"),
        "executable_sha256": candidate["patched_sha256"],
        "resource_root": str(root),
        "vehicle_select_scene": str(root.joinpath(*PurePosixPath(SCENE).parts)),
        "vehicle_select_scene_sha256": unlock.EXPECTED_SCENE_SHA256,
        "randomizer_present": False,
        "forced_ai_proof": candidate["forced_ai_proof"],
        "natural_t1_id26_pool": candidate["natural_t1_id26_pool"],
        "file_count": len(actual_paths),
        "fresh_player_state": "excluded",
    }


def stage_package(source_root: Path, candidate_exe: Path, candidate_manifest: Path,
                  retail: Path, output_root: Path, profile_name: str,
                  profile_path: Path = unlock.DEFAULT_PROFILE) -> dict[str, Any]:
    source = source_root.resolve(strict=True)
    output = unlock.validate_output_root(output_root, REPO_ROOT)
    if output.exists():
        raise RuntimePackageError("output already exists; choose a new package path")
    if output == source or _is_under(output, source) or _is_under(source, output):
        raise RuntimePackageError("source and output runtime roots must be separate")
    try:
        source_report = unlock.verify_package(
            source, profile_path, repo_root=REPO_ROOT,
            enforce_output_root=True, allow_runtime_state=True,
        )
        if source_report["executable_sha256"] != unlock.FINAL_RACE_DETAILS_EXE_SHA256:
            raise RuntimePackageError("source root is not the pinned final G.1 package")
        profile, profile_sha = unlock._load_profile(profile_path)
    except (OSError, unlock.PackageError) as exc:
        raise RuntimePackageError(f"source resource root refused: {exc}") from exc
    candidate = _validate_candidate(candidate_exe.resolve(strict=True),
                                    candidate_manifest.resolve(strict=True),
                                    retail.resolve(strict=True), profile_name)
    rows = _inventory(source, profile)
    expected = _expected_manifest(profile=profile, profile_sha256=profile_sha,
                                   candidate=candidate, rows=rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    try:
        for component in profile["components"]:
            base = unlock._path_for(source, str(component["root"]))
            files = [base] if component["kind"] == "file" else sorted(
                path for path in base.rglob("*") if path.is_file()
            )
            for source_file in files:
                relative = source_file.relative_to(source).as_posix()
                target = _safe_path(temp, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_file, target)
        scene_source = unlock._path_for(source, SCENE)
        scene_target = _safe_path(temp, SCENE)
        scene_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(scene_source, scene_target)
        shutil.copyfile(candidate_exe, temp / "MRallye.exe")
        (temp / PACKAGE_MANIFEST).write_text(
            json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        verify_package(temp, candidate_manifest, retail, source, profile_name,
                       profile_path=profile_path, enforce_output_root=False)
        os.replace(temp, output)
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    result = verify_package(output, candidate_manifest, retail, source, profile_name,
                            profile_path=profile_path, enforce_output_root=True)
    return result


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage")
    stage.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    stage.add_argument("--candidate", type=Path, required=True)
    stage.add_argument("--candidate-manifest", type=Path, required=True)
    stage.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL)
    stage.add_argument("--output-root", type=Path, required=True)
    stage.add_argument("--profile", choices=SUPPORTED_RUNTIME_PROFILES, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--runtime-root", type=Path, required=True)
    verify.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    verify.add_argument("--candidate-manifest", type=Path, required=True)
    verify.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL)
    verify.add_argument("--profile", choices=SUPPORTED_RUNTIME_PROFILES, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "stage":
            result = stage_package(args.source_root, args.candidate, args.candidate_manifest,
                                   args.retail_exe, args.output_root, args.profile)
        else:
            result = verify_package(args.runtime_root, args.candidate_manifest,
                                    args.retail_exe, args.source_root, args.profile)
    except (RuntimePackageError, candidate_builder.CandidateError,
            natural_candidate_builder.CandidateError,
            unlock.PackageError, OSError, ValueError) as exc:
        parser.exit(2, f"hardened runtime package refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
