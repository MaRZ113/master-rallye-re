"""Deterministic offline addon integration-plan compiler and verifier."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from .manifest import (
    AddonValidationError, canonical_json, load_capabilities, load_manifests, read_json, validate_manifests,
)
from ..dx import parse_dx
from ..dxt import parse_dxt
from ..vehicle_packaging import vehicle_dependencies


OUTPUT_FILES = ("addon-plan.json", "frontend-overlay.plan.json", "resource-inventory.json")


def _safe_relative(value: str) -> PurePosixPath:
    if not isinstance(value, str) or "\\" in value or "\x00" in value:
        raise AddonValidationError(f"unsafe resource path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} or ":" in part for part in path.parts):
        raise AddonValidationError(f"unsafe resource path: {value}")
    return path


def _tree_resource_inventory(plan: dict[str, Any], assets_root: Path | None) -> tuple[dict[str, Any], list[tuple[Path, PurePosixPath]]]:
    rows: list[dict[str, Any]] = []
    copies: list[tuple[Path, PurePosixPath]] = []
    for addon in plan["addons"]:
        root = addon["assets"]["model_package_root"]
        if assets_root is None:
            for role in addon["assets"]["required_roles"]:
                dest = _safe_relative(f"{root}/{role}")
                rows.append({"addon_id": addon["addon_id"], "path": dest.as_posix(), "role": role,
                             "status": "EXTERNAL_PAYLOAD_NOT_STAGED"})
            continue

        root_real = assets_root.resolve()
        vehicle_dir = (root_real / Path(*_safe_relative(root).parts)).resolve()
        if root_real != vehicle_dir and root_real not in vehicle_dir.parents:
            raise AddonValidationError(f"asset package escapes asset root: {root}")
        current = root_real
        for part in _safe_relative(root).parts:
            current = current / part
            if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
                raise AddonValidationError(f"asset path contains a symlink or junction: {current}")
        if not vehicle_dir.is_dir():
            raise AddonValidationError(f"required model package is missing: {root}")

        try:
            dependency_report = vehicle_dependencies(vehicle_dir)
        except Exception as exc:
            raise AddonValidationError(f"asset package validation failed for {addon['addon_id']}: {exc}") from exc
        parsed_roles = {row["resource"] for row in dependency_report["resources"] if row["status"] == "PARSED"}
        missing_roles = set(addon["assets"]["required_roles"]) - parsed_roles
        if missing_roles:
            raise AddonValidationError(f"{addon['addon_id']} missing/invalid DX roles: {sorted(missing_roles)}")
        if dependency_report["unresolved_count"]:
            unresolved = sorted({row["texture_name"] for row in dependency_report["bindings"]
                                 if row["resolution"] != "RESOLVED"})
            raise AddonValidationError(f"{addon['addon_id']} has unresolved DXT dependencies: {unresolved}")

        sources: dict[str, tuple[Path, str]] = {}
        for role in addon["assets"]["required_roles"]:
            source = vehicle_dir / role
            sources[source.name.casefold()] = (source, role)
        for binding in dependency_report["bindings"]:
            source = Path(binding["source_path"]).resolve()
            if vehicle_dir != source.parent and vehicle_dir not in source.parents:
                raise AddonValidationError(f"texture dependency escapes family directory: {source}")
            if source.is_symlink() or getattr(source, "is_junction", lambda: False)():
                raise AddonValidationError(f"texture path is a symlink or junction: {source}")
            sources.setdefault(source.name.casefold(), (source, "referenced_dxt"))

        for source, role in sorted(sources.values(), key=lambda row: row[0].name.casefold()):
            if source.suffix.casefold() == ".dxt":
                try:
                    parse_dxt(source)
                except (OSError, ValueError) as exc:
                    raise AddonValidationError(f"invalid DXT dependency {source}: {exc}") from exc
            elif source.suffix.casefold() == ".dx":
                if not parse_dx(source).diagnostics.validated:
                    raise AddonValidationError(f"DX dependency did not pass structural validation: {source}")
            else:
                raise AddonValidationError(f"unsupported runtime asset extension: {source}")
            relative = _safe_relative(f"{root}/{source.name}")
            data = source.read_bytes()
            rows.append({"addon_id": addon["addon_id"], "path": relative.as_posix(), "role": role,
                         "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
                         "status": "HASHED_AND_PARSED"})
            copies.append((source, relative))
    return ({"status": "REFERENCES_ONLY" if assets_root is None else "REQUIRED_ASSETS_VALIDATED",
             "asset_root_supplied": assets_root is not None, "resources": rows}, copies)


def build_artifacts(manifests: list[dict[str, Any]], capabilities: dict[str, Any],
                    asset_root: Path | None = None) -> dict[str, bytes]:
    plan = validate_manifests(manifests, capabilities)
    plan_bytes = canonical_json(plan)
    frontend = {
        "artifact_version": 1,
        "artifact_kind": "semantic frontend integration plan; not native game XML",
        "vehicle_select_entries": [
            {"addon_id": addon["addon_id"], "physical_id": addon["physical_id"],
             "vehicle_class": addon["vehicle_class"], "class_local_index": addon["class_local_index"],
             "manufacturer": addon["frontend"]["manufacturer"], "model": addon["frontend"]["model"],
             "combined": addon["frontend"]["combined"], "art": addon["frontend"]["vehicle_select_art"],
             "smallcarsheet": addon["frontend"]["smallcarsheet"], "stats": addon["frontend"]["stats"]}
            for addon in plan["addons"]
        ],
        "frontend_lifecycle_gates": {
            "absolute_to_local_map_required": True,
            "local_to_absolute_map_required": True,
            "reentry_restore": "unresolved; do not synthesize or silently reset scene selection",
            "split_screen_selection": "per-player ownership must be audited before runtime integration",
        },
    }
    inventory, _copies = _tree_resource_inventory(plan, asset_root)
    return {
        "addon-plan.json": plan_bytes,
        "frontend-overlay.plan.json": canonical_json(frontend),
        "resource-inventory.json": canonical_json(inventory),
    }


def build_to_directory(manifest_paths: list[Path], capabilities_path: Path, output: Path,
                       *, assets_root: Path | None = None, retail_exe: Path | None = None) -> dict[str, Any]:
    manifests, provenance = load_manifests(manifest_paths)
    capabilities, capability_sha = load_capabilities(capabilities_path)
    executable_provenance = verify_retail_executable(retail_exe, capabilities) if retail_exe else None
    artifacts = build_artifacts(manifests, capabilities, assets_root)
    plan = json.loads(artifacts["addon-plan.json"].decode("utf-8"))
    inventory = json.loads(artifacts["resource-inventory.json"].decode("utf-8"))
    copy_rows: list[tuple[Path, PurePosixPath]] = []
    if assets_root is not None:
        _, copy_rows = _tree_resource_inventory(plan, Path(assets_root))
    output = Path(output).resolve()
    if output.exists():
        raise AddonValidationError(f"output already exists; refusing to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        for relative, data in artifacts.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for source, relative in copy_rows:
            dest = stage.joinpath(*relative.parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        artifact_hashes = {}
        for file in sorted((p for p in stage.rglob("*") if p.is_file()), key=lambda p: p.relative_to(stage).as_posix().casefold()):
            name = file.relative_to(stage).as_posix()
            artifact_hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest()
        build_manifest = {
            "build_manifest_version": 1,
            "compiler": "master-rallye-re addon-sdk offline planner v1",
            "capability_profile_sha256": capability_sha,
            "retail_executable_check": executable_provenance or "NOT_SUPPLIED_OFFLINE_PLAN_ONLY",
            "input_manifests": sorted(provenance, key=lambda row: row["path_label"].casefold()),
            "asset_root_supplied": assets_root is not None,
            "artifact_sha256": artifact_hashes,
            "output_status": "OFFLINE_PLAN_ONLY",
            "runtime_installable": False,
        }
        (stage / "build-manifest.json").write_bytes(canonical_json(build_manifest))
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {"status": "PASS", "output": str(output), "artifact_count": len(artifact_hashes),
            "resource_count": len(inventory["resources"]), "runtime_installable": False,
            "plan_sha256": hashlib.sha256(artifacts["addon-plan.json"]).hexdigest()}


def verify_retail_executable(path: Path, capabilities: dict[str, Any]) -> dict[str, Any]:
    """Fail closed when a supplied on-disk game image differs from the profile."""
    path = Path(path)
    if not path.is_file():
        raise AddonValidationError(f"retail executable does not exist: {path}")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != capabilities["retail_exe_sha256"]:
        raise AddonValidationError("retail executable SHA256 does not match the selected capability profile")
    expected_size = capabilities.get("retail_exe_size")
    if expected_size is not None and len(data) != expected_size:
        raise AddonValidationError("retail executable size does not match the selected capability profile")
    return {"status": "EXACT_RETAIL_BUILD_VERIFIED", "sha256": digest, "size": len(data),
            "path_label": path.name}


def verify_build(path: Path) -> dict[str, Any]:
    root = Path(path).resolve()
    manifest_path = root / "build-manifest.json"
    if not root.is_dir() or not manifest_path.is_file():
        raise AddonValidationError("build directory or build-manifest.json is missing")
    manifest, _ = read_json(manifest_path)
    if manifest.get("build_manifest_version") != 1 or manifest.get("runtime_installable") is not False:
        raise AddonValidationError("unsupported or unsafe addon build manifest")
    expected = manifest.get("artifact_sha256")
    if not isinstance(expected, dict):
        raise AddonValidationError("build manifest has no artifact SHA map")
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "build-manifest.json"}
    if actual_files != set(expected):
        raise AddonValidationError("build output file set differs from manifest")
    for relative, digest in expected.items():
        rel = _safe_relative(relative)
        file = root.joinpath(*rel.parts)
        if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise AddonValidationError(f"artifact SHA256 mismatch: {relative}")
    plan_path = root / "addon-plan.json"
    if not plan_path.is_file():
        raise AddonValidationError("addon plan missing")
    plan, _ = read_json(plan_path)
    if plan.get("build_target", {}).get("runtime_deployment") != "NOT_IMPLEMENTED_FAIL_CLOSED":
        raise AddonValidationError("plan does not preserve fail-closed runtime boundary")
    return {"status": "PASS", "artifact_count": len(expected), "runtime_installable": False,
            "plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest()}
