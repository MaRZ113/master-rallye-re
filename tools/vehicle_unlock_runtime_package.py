#!/usr/bin/env python3
"""Stage, update, and verify the exact G.1 vehicle-unlock runtime tree.

The package is deliberately built as a new ignored output directory. It copies
captured resource-root components pinned by the canonical profile, installs
the exact candidate EXE, and places the exact VehicleSelect overlay at the
resource root. Candidate updates replace only MRallye.exe and preserve
game-generated profile state. The tool never edits the supplied source root or
retail corpus.
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


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = REPO_ROOT / "research/vehicles/unlock/runtime-root-profile.json"
EXPECTED_EXE_SHA256 = "3346eb00442b88cca3f76f7a65606ca56006c5b981acdbf0ee4ad16412e5b055"
FINAL_RACE_DETAILS_EXE_SHA256 = "722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7"
EXPECTED_SCENE_SHA256 = "6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d"
EXPECTED_PROFILE_SHA256 = "bd4700d6d127a4c3bb2e7faaafd6c5573f72999097e8da02ef34b1d11448fd32"
SCENE_RELATIVE = PurePosixPath("DataScene/FrontendScreens/VehicleSelect.xml")
PACKAGE_MANIFEST_NAME = "vehicle-unlock-package.json"
PLAYER_STATE_PATHS = (
    PurePosixPath("DataGame/PlayerState.xml"),
    PurePosixPath("DataGame/PlayerState.xml#"),
)
RUNTIME_STATE_PATHS = frozenset({
    "DataGame/PlayerState.xml",
    "DataGame/PlayerState.xml#",
    "DataGame/options.xml#",
})


class PackageError(ValueError):
    """Raised when a package input or generated runtime tree is unsupported."""


def _supported_runtime_exes() -> dict[str, str]:
    """Build the allowlist from constants so tests can pin synthetic fixtures."""
    supported = {
        EXPECTED_EXE_SHA256: "mercedes-g1-stock-t1-cup-car1-unlock-locked-state-correction",
    }
    if FINAL_RACE_DETAILS_EXE_SHA256 != EXPECTED_EXE_SHA256:
        supported[FINAL_RACE_DETAILS_EXE_SHA256] = "mercedes-g1-final-racedetails-localization"
    return supported


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _posix_path(path: PurePosixPath) -> str:
    if (path.is_absolute() or not path.parts or "\\" in str(path)
            or any(part in ("", ".", "..") for part in path.parts)):
        raise PackageError(f"unsafe relative path in profile: {path}")
    return path.as_posix()


def _path_for(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    _posix_path(rel)
    result = root.joinpath(*rel.parts)
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise PackageError(f"symbolic link is not accepted in runtime tree: {relative}")
    return result


def _file_row(path: Path, relative: str) -> dict[str, Any]:
    if not path.is_file():
        raise PackageError(f"required runtime input is missing or not a file: {relative}")
    return {"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)}


def _component_files(root: Path, component: dict[str, Any]) -> list[Path]:
    relative = _posix_path(PurePosixPath(str(component.get("root", ""))))
    base = _path_for(root, relative)
    kind = component.get("kind")
    if kind == "file":
        if not base.is_file():
            raise PackageError(f"required runtime input is missing: {relative}")
        return [base]
    if kind != "tree" or not base.is_dir():
        raise PackageError(f"unsupported or missing runtime component: {relative}")
    paths = sorted(base.rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise PackageError(f"symbolic link is not accepted in runtime component: {path}")
    files = [path for path in paths if path.is_file()]
    if not files:
        raise PackageError(f"runtime component is empty: {relative}")
    return files


def _inventory_sha256(rows: list[dict[str, Any]]) -> str:
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _load_profile(profile_path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = profile_path.read_bytes()
        profile = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"cannot read runtime-root profile: {exc}") from exc
    if not isinstance(profile, dict) or profile.get("schema_version") != 1:
        raise PackageError("unsupported runtime-root profile schema")
    profile_sha = hashlib.sha256(raw).hexdigest()
    if profile_sha != EXPECTED_PROFILE_SHA256:
        raise PackageError("runtime-root profile hash is not the pinned G.1 package profile")
    provenance = profile.get("provenance")
    if (not isinstance(provenance, dict)
            or provenance.get("exe_sha256") != EXPECTED_EXE_SHA256
            or provenance.get("loose_vehicle_select_scene_present") is not False):
        raise PackageError("runtime-root provenance does not match the pinned captured state")
    components = profile.get("components")
    if not isinstance(components, list) or not components:
        raise PackageError("runtime-root profile has no components")
    seen: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            raise PackageError("invalid runtime-root component entry")
        key = _posix_path(PurePosixPath(str(component.get("root", "")))).casefold()
        if key in seen:
            raise PackageError(f"duplicate runtime-root component: {key}")
        seen.add(key)
        if component.get("kind") not in {"file", "tree"}:
            raise PackageError(f"invalid component kind for {key}")
        if not isinstance(component.get("file_count"), int) or component["file_count"] < 1:
            raise PackageError(f"invalid file count for {key}")
        if not isinstance(component.get("total_bytes"), int) or component["total_bytes"] < 1:
            raise PackageError(f"invalid size for {key}")
        expected = component.get("inventory_sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise PackageError(f"invalid inventory hash for {key}")
    return profile, profile_sha


def inspect_resource_root(root: Path, profile_path: Path = DEFAULT_PROFILE) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    """Validate and inventory only the profile's allowlisted resource files."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise PackageError("resource root must be a directory")
    root_exe = root / "MRallye.exe"
    if (not root_exe.is_file() or root_exe.stat().st_size != 3121214
            or sha256_file(root_exe) != EXPECTED_EXE_SHA256):
        raise PackageError("captured resource root does not contain the expected G.1 executable")
    profile, profile_sha = _load_profile(profile_path)
    loose_scene = root.joinpath(*SCENE_RELATIVE.parts)
    if loose_scene.exists():
        raise PackageError(
            "source resource root already has a loose VehicleSelect.xml; refusing to shadow an unknown scene"
        )

    rows: list[dict[str, Any]] = []
    for component in profile["components"]:
        component_rows = []
        for path in _component_files(root, component):
            relative = path.relative_to(root).as_posix()
            component_rows.append(_file_row(path, relative))
        component_rows.sort(key=lambda row: row["path"].casefold())
        if len(component_rows) != component["file_count"]:
            raise PackageError(f"file count mismatch for runtime component {component['root']}")
        total = sum(row["size"] for row in component_rows)
        if total != component["total_bytes"]:
            raise PackageError(f"byte count mismatch for runtime component {component['root']}")
        if _inventory_sha256(component_rows) != component["inventory_sha256"]:
            raise PackageError(f"hash inventory mismatch for runtime component {component['root']}")
        rows.extend(component_rows)
    rows.sort(key=lambda row: row["path"].casefold())
    return rows, profile, profile_sha


def _load_json(path: Path, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"cannot read {role}: {exc}") from exc
    if not isinstance(value, dict):
        raise PackageError(f"{role} must be a JSON object")
    return value


def _expected_package_manifest(rows: list[dict[str, Any]], profile: dict[str, Any],
                               profile_sha: str, exe_sha256: str | None = None
                               ) -> dict[str, Any]:
    if exe_sha256 is None:
        exe_sha256 = EXPECTED_EXE_SHA256
    supported = _supported_runtime_exes()
    if exe_sha256 not in supported:
        raise PackageError("runtime executable is not an exact supported G.1 candidate")
    manifest = {
        "schema_version": 1,
        "status": "G1_RUNTIME_TREE_STAGED",
        "source_profile": profile.get("profile"),
        "source_profile_sha256": profile_sha,
        "candidate_executable": {
            "path": "MRallye.exe",
            "sha256": exe_sha256,
            "size": 3121214,
        },
        "resource_root": ".",
        "vehicle_select_scene": {
            "path": SCENE_RELATIVE.as_posix(),
            "sha256": EXPECTED_SCENE_SHA256,
        },
        "fresh_profile_policy": {
            "PlayerState.xml": "not copied; game creates a new profile on first launch",
            "PlayerState.xml#": "not copied",
        },
        "base_components": profile["components"],
        "payload_files": rows,
    }
    if exe_sha256 == FINAL_RACE_DETAILS_EXE_SHA256:
        manifest["candidate_executable"]["profile"] = supported[exe_sha256]
        manifest["runtime_update"] = {
            "scope": "ID26-only Race Details group-0x35 presentation",
            "existing_player_state": "preserved; not read or modified by EXE installation",
            "physical_car_id": 26,
        }
        manifest["fresh_profile_policy"] = {
            "PlayerState.xml": "existing runtime state is preserved if present",
            "PlayerState.xml#": "existing runtime state is preserved if present",
        }
    return manifest


def _expected_paths(rows: list[dict[str, Any]]) -> set[str]:
    return {row["path"] for row in rows} | {
        "MRallye.exe",
        SCENE_RELATIVE.as_posix(),
        PACKAGE_MANIFEST_NAME,
    }


def _verify_payload(root: Path, rows: list[dict[str, Any]], *,
                    allow_runtime_state: bool = False,
                    expected_exe_sha256: str = EXPECTED_EXE_SHA256) -> None:
    expected = _expected_paths(rows)
    actual: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PackageError(f"symbolic link is not accepted in staged package: {path}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    allowed_state = RUNTIME_STATE_PATHS if allow_runtime_state else frozenset()
    if not expected.issubset(actual) or actual - expected - allowed_state:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected - allowed_state)
        raise PackageError(f"package file set differs (missing={missing[:4]}, extra={extra[:4]})")
    for relative in allowed_state & actual:
        state_path = _path_for(root, relative)
        if not state_path.is_file():
            raise PackageError(f"runtime state path is not a regular file: {relative}")
    for row in rows:
        path = _path_for(root, row["path"])
        if path.stat().st_size != row["size"] or sha256_file(path) != row["sha256"]:
            raise PackageError(f"staged resource mismatch: {row['path']}")
    exe = root / "MRallye.exe"
    if exe.stat().st_size != 3121214 or sha256_file(exe) != expected_exe_sha256:
        raise PackageError("staged executable does not match the exact G.1 candidate")
    scene = _path_for(root, SCENE_RELATIVE.as_posix())
    if sha256_file(scene) != EXPECTED_SCENE_SHA256:
        raise PackageError("staged VehicleSelect.xml does not match the exact correction overlay")
    if not allow_runtime_state:
        for relative in PLAYER_STATE_PATHS:
            if root.joinpath(*relative.parts).exists():
                raise PackageError(f"staged tree is not fresh-profile clean: {relative.as_posix()}")


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_output_root(output_root: Path, repo_root: Path = REPO_ROOT) -> Path:
    if output_root.is_symlink():
        raise PackageError("runtime package output cannot be a symbolic link")
    repo_root = repo_root.resolve(strict=True)
    output = output_root.resolve(strict=False)
    allowed = (repo_root / ".research-output").resolve(strict=False)
    allowed_legacy = (repo_root / "research-output").resolve(strict=False)
    if not (_is_under(output, allowed) or _is_under(output, allowed_legacy)):
        raise PackageError("runtime package output must be inside this checkout's ignored research-output")
    if output == allowed or output == allowed_legacy:
        raise PackageError("runtime package output must name a child directory")
    if output.exists() and output.is_symlink():
        raise PackageError("runtime package output cannot be a symbolic link")
    return output


def verify_package(package_root: Path, profile_path: Path = DEFAULT_PROFILE,
                   *, repo_root: Path = REPO_ROOT, enforce_output_root: bool = True,
                   allow_runtime_state: bool = False) -> dict[str, Any]:
    if enforce_output_root:
        root = validate_output_root(package_root, repo_root)
    else:
        root = package_root.resolve(strict=True)
    if not root.is_dir():
        raise PackageError("package root must be a directory")
    exe_path = root / "MRallye.exe"
    if not exe_path.is_file() or exe_path.stat().st_size != 3121214:
        raise PackageError("runtime package executable is missing or has an unsupported size")
    exe_sha256 = sha256_file(exe_path)
    supported = _supported_runtime_exes()
    if exe_sha256 not in supported:
        raise PackageError("runtime package executable is not an exact supported G.1 candidate")
    profile, profile_sha = _load_profile(profile_path)
    rows = []
    for component in profile["components"]:
        base = PurePosixPath(component["root"])
        # Reconstruct the pinned package inventory from its component rows.
        component_root = _path_for(root, base.as_posix())
        if component["kind"] == "file":
            files = [component_root]
        else:
            files = sorted(path for path in component_root.rglob("*") if path.is_file())
        component_rows = [_file_row(path, path.relative_to(root).as_posix()) for path in files]
        component_rows.sort(key=lambda row: row["path"].casefold())
        if (len(component_rows) != component["file_count"]
                or sum(row["size"] for row in component_rows) != component["total_bytes"]
                or _inventory_sha256(component_rows) != component["inventory_sha256"]):
            raise PackageError(f"staged component differs from pinned profile: {component['root']}")
        rows.extend(component_rows)
    rows.extend([
        {"path": "MRallye.exe", "size": 3121214, "sha256": exe_sha256},
        {"path": SCENE_RELATIVE.as_posix(),
         "size": _path_for(root, SCENE_RELATIVE.as_posix()).stat().st_size,
         "sha256": EXPECTED_SCENE_SHA256},
    ])
    rows.sort(key=lambda row: row["path"].casefold())
    _verify_payload(root, rows, allow_runtime_state=allow_runtime_state,
                    expected_exe_sha256=exe_sha256)
    manifest = _expected_package_manifest(rows, profile, profile_sha, exe_sha256)
    stored_manifest = _load_json(root / PACKAGE_MANIFEST_NAME, "runtime package manifest")
    if stored_manifest != manifest:
        raise PackageError("runtime package manifest differs from deterministic expected manifest")
    return {
        "status": "PASS",
        "resource_root": str(root),
        "effective_executable": str(root / "MRallye.exe"),
        "staged_vehicle_select_scene": str(root.joinpath(*SCENE_RELATIVE.parts)),
        "executable_sha256": exe_sha256,
        "candidate_profile": supported[exe_sha256],
        "vehicle_select_sha256": EXPECTED_SCENE_SHA256,
        "fresh_player_state": ("PlayerState.xml absent" if not any(
            root.joinpath(*PurePosixPath(relative).parts).exists()
            for relative in PLAYER_STATE_PATHS) else "existing PlayerState.xml preserved"),
        "file_count": len(rows) + 1,
        "runtime_note": "PASS verifies the on-disk launch tree; capture the game's Root header after launch to verify runtime root selection.",
    }


def stage_package(resource_root: Path, candidate_exe: Path, scene_overlay: Path,
                  output_root: Path, profile_path: Path = DEFAULT_PROFILE,
                  *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    source_root = resource_root.resolve(strict=True)
    exe = candidate_exe.resolve(strict=True)
    scene = scene_overlay.resolve(strict=True)
    output = validate_output_root(output_root, repo_root)
    if output == source_root or _is_under(output, source_root) or _is_under(source_root, output):
        raise PackageError("output package must be separate from the captured resource root")
    if sha256_file(exe) != EXPECTED_EXE_SHA256 or exe.stat().st_size != 3121214:
        raise PackageError("candidate EXE hash/size is not the exact G.1 locked-state correction")
    if sha256_file(scene) != EXPECTED_SCENE_SHA256:
        raise PackageError("VehicleSelect overlay hash is not the exact G.1 correction overlay")
    rows, profile, profile_sha = inspect_resource_root(source_root, profile_path)
    payload_rows = rows + [
        {"path": "MRallye.exe", "size": 3121214, "sha256": EXPECTED_EXE_SHA256},
        {"path": SCENE_RELATIVE.as_posix(), "size": scene.stat().st_size,
         "sha256": EXPECTED_SCENE_SHA256},
    ]
    payload_rows.sort(key=lambda row: row["path"].casefold())
    manifest = _expected_package_manifest(payload_rows, profile, profile_sha)

    if output.exists():
        result = verify_package(output, profile_path, repo_root=repo_root)
        result["status"] = "PASS_ALREADY_STAGED"
        return result

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    try:
        for row in rows:
            src = _path_for(source_root, row["path"])
            dst = _path_for(temp, row["path"])
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        shutil.copyfile(exe, temp / "MRallye.exe")
        scene_target = _path_for(temp, SCENE_RELATIVE.as_posix())
        scene_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(scene, scene_target)
        manifest_path = temp / PACKAGE_MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        verify_package(temp, profile_path, repo_root=repo_root, enforce_output_root=False)
        os.replace(temp, output)
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    result = verify_package(output, profile_path, repo_root=repo_root)
    result["status"] = "PASS_STAGED"
    result["source_resource_root"] = str(source_root)
    return result


def _component_rows_from_package(root: Path, profile: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for component in profile["components"]:
        component_root = _path_for(root, _posix_path(PurePosixPath(component["root"])))
        files = ([component_root] if component["kind"] == "file"
                 else sorted(path for path in component_root.rglob("*") if path.is_file()))
        component_rows = [_file_row(path, path.relative_to(root).as_posix()) for path in files]
        component_rows.sort(key=lambda row: row["path"].casefold())
        if (len(component_rows) != component["file_count"]
                or sum(row["size"] for row in component_rows) != component["total_bytes"]
                or _inventory_sha256(component_rows) != component["inventory_sha256"]):
            raise PackageError(f"staged component differs from pinned profile: {component['root']}")
        rows.extend(component_rows)
    return rows


def _atomic_bytes(path: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                                                   dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def install_candidate(package_root: Path, candidate_exe: Path,
                      profile_path: Path = DEFAULT_PROFILE, *,
                      repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Atomically update only the EXE in the verified G.1 runtime package.

    Runtime-generated PlayerState files are allowed and remain byte-for-byte
    untouched so an already-unlocked test profile can be reused.
    """
    root = validate_output_root(package_root, repo_root)
    candidate = candidate_exe.resolve(strict=True)
    allowed_candidate_root = (repo_root.resolve(strict=True) / ".research-output").resolve(strict=False)
    if not _is_under(candidate, allowed_candidate_root):
        raise PackageError("candidate EXE must come from this checkout's ignored .research-output")
    if (candidate.stat().st_size != 3121214
            or sha256_file(candidate) != FINAL_RACE_DETAILS_EXE_SHA256):
        raise PackageError("candidate EXE is not the exact final G.1 Race Details build")

    current = verify_package(root, profile_path, repo_root=repo_root,
                              allow_runtime_state=True)
    if current["executable_sha256"] == FINAL_RACE_DETAILS_EXE_SHA256:
        return {**current, "status": "PASS_ALREADY_INSTALLED"}
    if current["executable_sha256"] != EXPECTED_EXE_SHA256:
        raise PackageError("runtime package does not contain the expected prior G.1 executable")

    profile, profile_sha = _load_profile(profile_path)
    rows = _component_rows_from_package(root, profile)
    rows.extend([
        {"path": "MRallye.exe", "size": 3121214,
         "sha256": FINAL_RACE_DETAILS_EXE_SHA256},
        {"path": SCENE_RELATIVE.as_posix(),
         "size": _path_for(root, SCENE_RELATIVE.as_posix()).stat().st_size,
         "sha256": EXPECTED_SCENE_SHA256},
    ])
    rows.sort(key=lambda row: row["path"].casefold())
    new_manifest = _expected_package_manifest(rows, profile, profile_sha,
                                              FINAL_RACE_DETAILS_EXE_SHA256)
    exe_path = root / "MRallye.exe"
    manifest_path = root / PACKAGE_MANIFEST_NAME
    old_exe = exe_path.read_bytes()
    old_manifest = manifest_path.read_bytes()
    new_exe = candidate.read_bytes()
    if sha256_file(candidate) != hashlib.sha256(new_exe).hexdigest():
        raise PackageError("candidate executable changed while preparing the package update")
    try:
        _atomic_bytes(exe_path, new_exe)
        _atomic_bytes(manifest_path, (json.dumps(new_manifest, indent=2, ensure_ascii=False)
                                      + "\n").encode("utf-8"))
        verified = verify_package(root, profile_path, repo_root=repo_root,
                                  allow_runtime_state=True)
    except Exception:
        _atomic_bytes(exe_path, old_exe)
        _atomic_bytes(manifest_path, old_manifest)
        raise
    return {
        **verified,
        "status": "PASS_INSTALLED",
        "previous_executable_sha256": EXPECTED_EXE_SHA256,
        "player_state": "preserved without reading or modification",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    stage = subparsers.add_parser("stage", help="build a fresh isolated runtime package")
    stage.add_argument("--resource-root", type=Path, required=True,
                       help="captured runtime Root containing pinned Data.sma and Mercedes assets")
    stage.add_argument("--candidate-exe", type=Path, required=True)
    stage.add_argument("--scene-overlay", type=Path, required=True)
    stage.add_argument("--output-root", type=Path, required=True,
                       help="new directory inside this checkout's .research-output")

    verify = subparsers.add_parser("verify", help="verify package files before launch")
    verify.add_argument("--package-root", type=Path, required=True)
    verify.add_argument("--allow-runtime-state", action="store_true",
                        help="allow game-generated PlayerState/options backup files")

    install = subparsers.add_parser(
        "install-candidate", help="replace only MRallye.exe in a verified staged package")
    install.add_argument("--package-root", type=Path, required=True)
    install.add_argument("--candidate-exe", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "stage":
            result = stage_package(args.resource_root, args.candidate_exe, args.scene_overlay,
                                   args.output_root)
        elif args.command == "install-candidate":
            result = install_candidate(args.package_root, args.candidate_exe)
        else:
            result = verify_package(args.package_root,
                                    allow_runtime_state=args.allow_runtime_state)
    except (OSError, PackageError, ValueError) as exc:
        parser.exit(2, f"G.1 runtime package refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
