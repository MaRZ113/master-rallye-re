"""Independent carrier, physics-family, and model-donor composition.

This module builds copy-only executable plans and per-file model overlays.  It
keeps the existing retail family patcher as the only executable patch backend.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .dx import parse_dx_bytes
from .errors import FormatError
from .sidecar import normalize_texture_value
from .vehicle_config_analysis import VehicleConfigDocument
from .vehicle_family_broker import RETAIL_EXE_SHA256
from .vehicle_model_inventory import MODEL_RESOURCES, inventory_vehicle_model_packages
from .vehicle_packaging import normalize_sma_member_name, read_sma_member
from .vehicle_physics_binding import (
    RETAIL_BUILD_NAME,
    RETAIL_FAMILY_CATALOG,
    PhysicsBinding,
    _atomic_write,
    _sha256,
    _validate_retail_executable_bytes,
    patch_family_initializer,
    validate_binding_families,
)


USER_FACING_NAME = "Master Rallye Vehicle Composer"
MANIFEST_SUFFIX = ".vehicle-compose.json"
ARTIFACT_RELATIVE = Path(".research-output") / "r-veh1"
OVERRIDE_MISSING_MODEL = "ALLOW MISSING MODEL"
OVERRIDE_INCOMPLETE_MODEL = "ALLOW INCOMPLETE MODEL"


@dataclass(frozen=True)
class VehicleComposition:
    """The three user identities; runtime family is always physics_family."""

    carrier_type: str
    physics_family: str
    model_donor: str

    @property
    def runtime_family(self) -> str:
        return self.physics_family

    def to_dict(self) -> dict[str, str]:
        return {
            "carrier_type": self.carrier_type,
            "physics_family": self.physics_family,
            "model_donor": self.model_donor,
            "runtime_family": self.runtime_family,
        }


@dataclass
class VehicleCompositionPlan:
    composition: VehicleComposition
    install_root: Path
    source_exe: Path
    catalog: tuple[Any, ...]
    expected_exe_sha256: str
    type_id: int
    config_validation: Any
    source_exe_sha256: str
    exe_patch_required: bool
    model_overlay_required: bool
    donor_package: dict[str, Any] | None
    overlay_writes: list[dict[str, Any]]
    overlay_removals: list[dict[str, Any]]
    archive_fallbacks: list[str]
    destination_directory: Path
    output_exe: Path | None
    planned_exe_sha256: str | None
    changed_ranges: tuple[dict[str, Any], ...]
    created_directories: tuple[str, ...]

    def preview(self) -> dict[str, Any]:
        return {
            "composition": self.composition.to_dict(),
            "carrier_type_id": self.type_id,
            "config_schema": self.config_validation.config_schema.to_dict(),
            "player1_modification_fields": self.config_validation.player1_overlay_count,
            "exe_patch_required": self.exe_patch_required,
            "model_overlay_required": self.model_overlay_required,
            "model_donor_file_count": (
                len(self.donor_package["files"]) if self.donor_package else 0
            ),
            "model_overlay_write_count": len(self.overlay_writes),
            "model_overlay_stale_removal_count": len(self.overlay_removals),
            "model_archive_fallbacks": list(self.archive_fallbacks),
            "destination_directory": str(self.destination_directory),
            "output_exe": str(self.output_exe) if self.output_exe else None,
            "planned_exe_sha256": self.planned_exe_sha256,
            "changed_ranges": list(self.changed_ranges),
            "created_directories": list(self.created_directories),
        }


def _safe_family_name(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise ValueError(f"{label} must be a non-empty family name")
    if any(char in value for char in ("/", "\\", ":", "\x00")):
        raise ValueError(f"{label} must be a single safe path component")
    if value[-1:] in {".", " "}:
        raise ValueError(f"{label} cannot end in a dot or space")
    if any(ord(char) < 32 or char in '<>:"|?*' for char in value):
        raise ValueError(f"{label} contains a character unsafe for Windows paths")
    if value.split(".", 1)[0].upper() in {
        "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        raise ValueError(f"{label} is a reserved Windows filename")
    return value


def _safe_relative_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"unsafe model-relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(
        part in {"", ".", ".."} or ":" in part or part[-1:] in {".", " "}
        or any(ord(char) < 32 or char in '<>:"|?*' for char in part)
        for part in path.parts
    ):
        raise ValueError(f"unsafe model-relative path: {value!r}")
    if any(part.split(".", 1)[0].upper() in {
        "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    } for part in path.parts):
        raise ValueError(f"reserved Windows name in model-relative path: {value!r}")
    return path


def _archive_vehicle_files(
    archive_members: Iterable[str], family: str
) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for raw_name in archive_members:
        name, is_directory = normalize_sma_member_name(raw_name)
        if is_directory:
            continue
        parts = PurePosixPath(name).parts
        if (
            len(parts) < 4
            or parts[0].casefold() != "datagx"
            or parts[1].casefold() != "vehicles"
            or parts[2].casefold() != family.casefold()
        ):
            continue
        relative = "/".join(parts[3:])
        _safe_relative_path(relative)
        result.setdefault(relative.casefold(), []).append({
            "relative_path": relative,
            "archive_member": name,
        })
    return result


def _read_resolved_files(
    archive_path: Path | None,
    loose_vehicles_root: Path,
    package: dict[str, Any],
    donor_family: str,
) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for entry in package.get("effective_files", []):
        relative_path = _safe_relative_path(entry["relative_path"]).as_posix()
        folded = relative_path.casefold()
        if folded in files:
            raise ValueError(f"ambiguous case-insensitive donor path: {relative_path}")
        provenance = entry.get("source")
        if provenance == "DATA_SMA":
            if archive_path is None:
                raise ValueError(f"Data.sma source is unavailable for {relative_path}")
            member = entry.get("archive_member")
            if not member:
                raise ValueError(f"archive member identity is missing for {relative_path}")
            content = read_sma_member(Path(archive_path), member)
        elif provenance == "LOOSE_OVERRIDE":
            source = Path(entry.get("loose_path", ""))
            if not source.is_file() or source.is_symlink():
                raise ValueError(f"loose donor file is missing or unsafe: {source}")
            try:
                source.resolve().relative_to(Path(loose_vehicles_root).resolve())
            except ValueError as exc:
                raise ValueError(f"loose donor file escapes DataGx/Vehicles: {source}") from exc
            content = source.read_bytes()
        else:
            raise ValueError(f"unsupported source provenance for {relative_path}: {provenance}")
        files[folded] = {
            "relative_path": relative_path,
            "source_provenance": provenance,
            "source_path": entry.get("loose_path") or entry.get("archive_member"),
            "sha256": _sha256(content),
            "data": content,
        }
    return files


def _dx_texture_dependencies(files: dict[str, dict[str, Any]]) -> tuple[set[str], list[dict[str, str]]]:
    dependencies: set[str] = set()
    unresolved: list[dict[str, str]] = []
    for resource in MODEL_RESOURCES:
        item = files.get(resource.casefold())
        if item is None:
            continue
        model = parse_dx_bytes(item["data"], item["relative_path"])
        for draw in model.physical_draws:
            for slot in draw.texture_slots:
                if slot.value.strip().casefold() == "null":
                    continue
                texture_path = f"{normalize_texture_value(slot.value)}.dxt"
                texture_key = texture_path.casefold()
                dependencies.add(texture_key)
                if texture_key not in files:
                    unresolved.append({
                        "dx_resource": item["relative_path"],
                        "texture_name": slot.value,
                        "expected_relative_path": texture_path,
                    })
    return dependencies, unresolved


def resolve_effective_model_package(
    archive_path: Path | None,
    archive_members: Iterable[str],
    loose_vehicles_root: Path,
    model_donor: str,
    *,
    model_packages: dict[str, dict[str, Any]] | None = None,
    require_complete: bool = True,
) -> dict[str, Any]:
    """Read a complete donor package from Data.sma overlaid by loose files."""
    donor = _safe_family_name(model_donor, "model donor")
    members = tuple(archive_members)
    packages = model_packages or inventory_vehicle_model_packages(members, loose_vehicles_root)
    package = packages.get(donor.casefold())
    if package is None or package.get("provenance") == "MISSING":
        raise ValueError(f"model donor package is missing: DataGx/Vehicles/{donor}")
    if len(package.get("family_names", [])) > 1 or package.get("ambiguous_paths"):
        raise ValueError(f"model donor package has ambiguous case-colliding paths: {donor}")
    if require_complete and package.get("status") not in {"COMPLETE", "COMPLETE_WHEELLESS"}:
        missing = ", ".join(package.get("missing_resources", [])) or package.get("status", "incomplete")
        raise ValueError(f"model donor {donor} is incomplete: {missing}")
    files = _read_resolved_files(archive_path, loose_vehicles_root, package, donor)
    if not files:
        raise ValueError(f"model donor package has no readable files: {donor}")
    present = set(files)
    expected = {name.casefold() for name in package.get("required_resources", [])}
    missing = sorted(expected - present)
    if require_complete and missing:
        raise ValueError(f"model donor {donor} is missing required files: {', '.join(missing)}")
    dependencies, unresolved = _dx_texture_dependencies(files)
    if require_complete and unresolved:
        details = ", ".join(row["expected_relative_path"] for row in unresolved)
        raise ValueError(f"model donor {donor} has unresolved DX texture dependencies: {details}")
    return {
        "family": package.get("family_names", [donor])[0],
        "status": package.get("status", "UNKNOWN"),
        "provenance": package.get("provenance", "UNKNOWN"),
        "wheelless_by_design": bool(package.get("wheelless_by_design")),
        "files": files,
        "file_count": len(files),
        "texture_dependencies": sorted(dependencies),
        "unresolved_texture_dependencies": unresolved,
    }


def _find_family_directory(loose_vehicles_root: Path, runtime_family: str) -> Path:
    root = Path(loose_vehicles_root)
    if root.is_symlink():
        raise ValueError(f"DataGx/Vehicles root is a symlink: {root}")
    matches = []
    if root.is_dir():
        for child in root.iterdir():
            if child.is_symlink():
                if child.name.casefold() == runtime_family.casefold():
                    raise ValueError(f"runtime model directory is a symlink: {child}")
                continue
            if child.is_dir() and child.name.casefold() == runtime_family.casefold():
                matches.append(child)
    if len(matches) > 1:
        raise ValueError(f"runtime model directory has case-colliding names: {runtime_family}")
    return matches[0] if matches else root / runtime_family


def _scan_loose_package(directory: Path, install_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    if not directory.exists():
        return result
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"runtime model destination is not a safe directory: {directory}")
    for current_name, dirnames, filenames in os.walk(directory, followlinks=False):
        current = Path(current_name)
        if current.is_symlink():
            raise ValueError(f"symlink directory in runtime model package: {current}")
        for dirname in list(dirnames):
            path = current / dirname
            if path.is_symlink():
                raise ValueError(f"symlink directory in runtime model package: {path}")
        dirnames.sort(key=str.casefold)
        for filename in filenames:
            path = current / filename
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"unsafe file in runtime model package: {path}")
            relative = _safe_relative_path(path.relative_to(directory).as_posix()).as_posix()
            folded = relative.casefold()
            if folded in result:
                raise ValueError(f"case-colliding runtime model files: {relative}")
            try:
                path.resolve().relative_to(install_root.resolve())
            except ValueError as exc:
                raise ValueError(f"runtime model file escapes install root: {path}") from exc
            result[folded] = path
    return result


def _overlay_plan(
    install_root: Path,
    loose_vehicles_root: Path,
    archive_members: Iterable[str],
    composition: VehicleComposition,
    donor_package: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], Path, tuple[str, ...]]:
    runtime_family = composition.runtime_family
    try:
        Path(loose_vehicles_root).resolve(strict=False).relative_to(Path(install_root).resolve())
    except ValueError as exc:
        raise ValueError("DataGx/Vehicles resolves outside the game install root") from exc
    destination_directory = _find_family_directory(loose_vehicles_root, runtime_family)
    target_archive_files = _archive_vehicle_files(archive_members, runtime_family)
    target_loose_files = _scan_loose_package(destination_directory, install_root)
    donor_files: dict[str, dict[str, Any]] = donor_package["files"]
    donor_paths = set(donor_files)
    dependencies = set(donor_package["texture_dependencies"])

    archive_collisions = sorted(path for path, rows in target_archive_files.items() if len(rows) > 1)
    if archive_collisions:
        raise ValueError(
            "runtime family has ambiguous archive paths: " + ", ".join(archive_collisions)
        )
    unmaskable_core = [
        resource for resource in MODEL_RESOURCES
        if resource.casefold() not in donor_paths
        and resource.casefold() in target_archive_files
    ]
    if unmaskable_core:
        raise ValueError(
            "the selected donor omits runtime resources that remain in Data.sma and cannot be masked: "
            + ", ".join(unmaskable_core)
        )
    unmaskable_dependencies = sorted(
        path for path in dependencies
        if path not in donor_paths and path in target_archive_files
    )
    if unmaskable_dependencies:
        raise ValueError(
            "Data.sma would supply runtime-family textures absent from the donor package: "
            + ", ".join(unmaskable_dependencies)
        )

    writes: list[dict[str, Any]] = []
    for folded_path in sorted(donor_files):
        source = donor_files[folded_path]
        destination = target_loose_files.get(folded_path)
        pre_bytes = destination.read_bytes() if destination is not None else None
        if pre_bytes is not None and _sha256(pre_bytes) == source["sha256"]:
            continue
        relative = (
            destination.relative_to(install_root).as_posix()
            if destination is not None
            else (destination_directory / PurePosixPath(source["relative_path"])).relative_to(install_root).as_posix()
        )
        writes.append({
            "operation": "WRITE_DONOR_FILE",
            "destination_relative_path": relative,
            "destination_path": (
                destination if destination is not None
                else destination_directory / Path(*PurePosixPath(source["relative_path"]).parts)
            ),
            "donor_family": donor_package["family"],
            "donor_relative_path": source["relative_path"],
            "source_provenance": source["source_provenance"],
            "source_path": source["source_path"],
            "data": source["data"],
            "applied_sha256": source["sha256"],
            "existed_before": destination is not None,
            "pre_apply_sha256": _sha256(pre_bytes) if pre_bytes is not None else None,
            "pre_apply_data": pre_bytes,
        })

    removals: list[dict[str, Any]] = []
    for folded_path, destination in sorted(target_loose_files.items()):
        if folded_path in donor_paths:
            continue
        pre_bytes = destination.read_bytes()
        removals.append({
            "operation": "REMOVE_STALE_LOOSE",
            "destination_relative_path": destination.relative_to(install_root).as_posix(),
            "destination_path": destination,
            "donor_family": donor_package["family"],
            "donor_relative_path": None,
            "source_provenance": "STALE_DESTINATION",
            "source_path": None,
            "data": None,
            "applied_sha256": None,
            "existed_before": True,
            "pre_apply_sha256": _sha256(pre_bytes),
            "pre_apply_data": pre_bytes,
        })

    archive_fallbacks = sorted(
        rows[0]["relative_path"]
        for folded_path, rows in target_archive_files.items()
        if folded_path not in donor_paths and folded_path not in dependencies
    )

    created_directories: set[str] = set()
    for entry in writes:
        current = Path(entry["destination_path"]).parent
        while current != install_root and install_root in current.parents:
            if not current.exists():
                created_directories.add(current.relative_to(install_root).as_posix())
            current = current.parent
    return (
        writes,
        removals,
        archive_fallbacks,
        destination_directory,
        tuple(sorted(created_directories, key=lambda value: (value.count("/"), value), reverse=True)),
    )


def build_vehicle_composition_plan(
    source_exe: Path,
    install_root: Path,
    composition: VehicleComposition,
    vehicle_config: VehicleConfigDocument,
    modifications_config: VehicleConfigDocument,
    archive_path: Path | None,
    archive_members: Iterable[str],
    loose_vehicles_root: Path,
    *,
    model_packages: dict[str, dict[str, Any]] | None = None,
    allow_unverified_schema: bool = False,
    allow_missing_natural_model: bool = False,
    allow_incomplete_model: bool = False,
    output_exe: Path | None = None,
    expected_exe_sha256: str = RETAIL_EXE_SHA256,
    catalog: tuple[Any, ...] = RETAIL_FAMILY_CATALOG,
) -> VehicleCompositionPlan:
    """Validate the composition and resolve all donor/destination bytes read-only."""
    carrier = _safe_family_name(composition.carrier_type, "carrier")
    physics_family = _safe_family_name(composition.physics_family, "physics family")
    model_donor = _safe_family_name(composition.model_donor, "model donor")
    normalized = VehicleComposition(carrier, physics_family, model_donor)
    root = Path(install_root).expanduser().resolve()
    source_path = Path(source_exe).expanduser().resolve()
    if source_path != (root / "MRallye.exe").resolve():
        raise ValueError("composition source must be the verified install-root MRallye.exe")
    source_data = source_path.read_bytes()
    source_sha = _validate_retail_executable_bytes(source_data, expected_exe_sha256)

    legacy_binding = PhysicsBinding(carrier, physics_family)
    validated = validate_binding_families(
        (legacy_binding,),
        vehicle_config,
        modifications_config,
        catalog=catalog,
        allow_unverified_schema=allow_unverified_schema,
    )[0]
    catalog_entry = next(item for item in catalog if item.family.casefold() == carrier.casefold())
    exe_patch_required = carrier.casefold() != physics_family.casefold()
    patch_result = None
    if exe_patch_required:
        if output_exe is None:
            raise ValueError("an output executable path is required when carrier and physics family differ")
        output_path = Path(output_exe).expanduser().resolve()
        try:
            output_path.relative_to(root)
        except ValueError as exc:
            raise ValueError("composition output executable must be inside the game install root") from exc
        if output_path == source_path:
            raise ValueError("refusing to overwrite the source retail executable")
        patch_result = patch_family_initializer(
            source_data, (legacy_binding,), catalog=catalog
        )
    else:
        output_path = None

    members = tuple(archive_members)
    packages = model_packages or inventory_vehicle_model_packages(members, loose_vehicles_root)
    donor_record = packages.get(model_donor.casefold())
    natural_model_missing = (
        model_donor.casefold() == physics_family.casefold()
        and (donor_record is None or donor_record.get("provenance") == "MISSING")
    )
    if natural_model_missing:
        if not allow_missing_natural_model:
            raise ValueError(
                f"physics family {physics_family} has no effective model package at "
                f"DataGx/Vehicles/{physics_family}"
            )
        donor_package = None
    else:
        donor_package = resolve_effective_model_package(
            archive_path,
            members,
            loose_vehicles_root,
            model_donor,
            model_packages=packages,
            require_complete=not allow_incomplete_model,
        )

    model_overlay_required = model_donor.casefold() != physics_family.casefold()
    if model_overlay_required:
        if donor_package is None:
            raise ValueError("an independent model donor must have a readable effective package")
        writes, removals, fallbacks, destination_directory, created_directories = _overlay_plan(
            root, loose_vehicles_root, members, normalized, donor_package
        )
    else:
        writes, removals, fallbacks = [], [], []
        destination_directory = _find_family_directory(loose_vehicles_root, physics_family)
        created_directories = ()

    return VehicleCompositionPlan(
        composition=normalized,
        install_root=root,
        source_exe=source_path,
        catalog=catalog,
        expected_exe_sha256=expected_exe_sha256,
        type_id=catalog_entry.type_id,
        config_validation=validated,
        source_exe_sha256=source_sha,
        exe_patch_required=exe_patch_required,
        model_overlay_required=model_overlay_required,
        donor_package=donor_package,
        overlay_writes=writes,
        overlay_removals=removals,
        archive_fallbacks=fallbacks,
        destination_directory=destination_directory,
        output_exe=output_path,
        planned_exe_sha256=patch_result.patched_sha256 if patch_result else None,
        changed_ranges=patch_result.changed_ranges if patch_result else (),
        created_directories=created_directories,
    )


def _safe_name(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    if not result:
        raise ValueError("composition identity cannot produce a safe filename")
    return result


def default_composition_stem(composition: VehicleComposition) -> str:
    return "MRallye_C-{}-P-{}-M-{}".format(
        _safe_name(composition.carrier_type),
        _safe_name(composition.physics_family),
        _safe_name(composition.model_donor),
    )


def default_composition_output_exe(
    install_root: Path, composition: VehicleComposition
) -> Path | None:
    if composition.carrier_type.casefold() == composition.physics_family.casefold():
        return None
    return Path(install_root) / (default_composition_stem(composition) + ".exe")


def choose_composition_manifest_path(
    install_root: Path,
    composition: VehicleComposition,
    *,
    output_exe: Path | None = None,
) -> Path:
    root = Path(install_root).expanduser().resolve()
    if output_exe is not None:
        stem = Path(output_exe).stem + "-composition"
    else:
        stem = default_composition_stem(composition)
    directory = root / ARTIFACT_RELATIVE / "manifests"
    candidate = directory / f"{stem}{MANIFEST_SUFFIX}"
    suffix = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{suffix}{MANIFEST_SUFFIX}"
        suffix += 1
    return candidate


def choose_composition_output_exe(
    install_root: Path,
    composition: VehicleComposition,
    *,
    output_exe: Path | None = None,
) -> Path | None:
    if composition.carrier_type.casefold() == composition.physics_family.casefold():
        if output_exe is not None:
            raise ValueError("an EXE output is not used when carrier and physics family match")
        return None
    root = Path(install_root).expanduser().resolve()
    if output_exe is not None:
        return Path(output_exe).expanduser().resolve()
    candidate = default_composition_output_exe(root, composition)
    assert candidate is not None
    stem = candidate.stem
    number = 2
    while True:
        associated_manifest = (
            root / ARTIFACT_RELATIVE / "manifests"
            / f"{candidate.stem}-composition{MANIFEST_SUFFIX}"
        )
        if not (
            candidate.exists()
            or candidate.with_name(candidate.name + ".original").exists()
            or associated_manifest.exists()
        ):
            break
        candidate = root / f"{stem}-{number}.exe"
        number += 1
    return candidate


def _install_relative(root: Path, path: Path) -> str:
    resolved_root = Path(root).resolve()
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"transaction path escapes install root: {path}") from exc


def _join_install_relative(root: Path, value: str) -> Path:
    relative = _safe_relative_path(value)
    resolved_root = Path(root).resolve()
    path = resolved_root.joinpath(*relative.parts)
    current = resolved_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"transaction path contains a symlink: {current}")
        try:
            current.resolve(strict=False).relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"manifest path escapes install root: {value}") from exc
    return path


def _manifest_backup_path(
    install_root: Path, backup_root: Path, index: int
) -> tuple[str, Path]:
    path = backup_root / "files" / f"{index:05d}.bin"
    return _install_relative(install_root, path), path


def _manifest_overlay_rows(
    plan: VehicleCompositionPlan, backup_root: Path
) -> list[dict[str, Any]]:
    result = []
    counter = 0
    for source in (*plan.overlay_writes, *plan.overlay_removals):
        row = {
            key: source.get(key)
            for key in (
                "operation", "destination_relative_path", "donor_family",
                "donor_relative_path", "source_provenance", "source_path",
                "applied_sha256", "existed_before", "pre_apply_sha256",
            )
        }
        row["backup_relative_path"] = None
        row["backup_sha256"] = None
        if source["existed_before"]:
            backup_relative, backup_path = _manifest_backup_path(
                plan.install_root, backup_root, counter
            )
            counter += 1
            row["backup_relative_path"] = backup_relative
            row["backup_sha256"] = source["pre_apply_sha256"]
            source["_backup_path"] = backup_path
        result.append(row)
    return result


def _composition_manifest_path(root: Path, candidate: Path | None) -> Path:
    if candidate is None:
        raise ValueError("composition manifest path is required")
    resolved_root = Path(root).resolve()
    raw_candidate = Path(candidate).expanduser()
    if not raw_candidate.is_absolute():
        raw_candidate = resolved_root / raw_candidate
    absolute_candidate = Path(os.path.abspath(raw_candidate))
    try:
        relative = absolute_candidate.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError("composition manifest must be inside this install root") from exc
    safe_relative = _safe_relative_path(relative)
    expected_parts = (".research-output", "r-veh1", "manifests")
    if (
        len(safe_relative.parts) != 4
        or tuple(part.casefold() for part in safe_relative.parts[:3]) != expected_parts
        or not safe_relative.name.casefold().endswith(MANIFEST_SUFFIX)
    ):
        raise ValueError("composition manifest must be inside .research-output/r-veh1/manifests")
    return _join_install_relative(resolved_root, safe_relative.as_posix())


def _cleanup_artifact_files(paths: Iterable[Path], directories: Iterable[Path]) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    for directory in sorted(set(directories), key=lambda item: len(item.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def apply_vehicle_composition(
    plan: VehicleCompositionPlan,
    *,
    manifest_path: Path,
) -> dict[str, Any]:
    """Apply the already validated plan with per-file backups and rollback."""
    root = plan.install_root.resolve()
    if not plan.exe_patch_required and not plan.overlay_writes and not plan.overlay_removals:
        return {
            "status": "NO_CHANGES",
            "composition": plan.composition.to_dict(),
            "output_exe": None,
            "manifest": None,
            "source_exe_modified": False,
        }
    manifest = _composition_manifest_path(root, manifest_path)
    if plan.exe_patch_required and plan.output_exe is None:
        raise ValueError("validated plan has no output executable")
    if manifest.exists():
        raise ValueError(f"composition manifest already exists: {manifest}")
    output_exe = plan.output_exe
    output_backup = output_exe.with_name(output_exe.name + ".original") if output_exe else None
    if output_exe and (output_exe.exists() or output_backup.exists()):
        raise ValueError("composition executable or its original backup already exists")

    # Confirm the destination is still exactly as it was when previewed.
    for entry in (*plan.overlay_writes, *plan.overlay_removals):
        destination = Path(entry["destination_path"])
        if entry["existed_before"]:
            if not destination.is_file() or destination.is_symlink():
                raise ValueError(f"destination changed after preview: {destination}")
            if _sha256(destination.read_bytes()) != entry["pre_apply_sha256"]:
                raise ValueError(f"destination changed after preview: {destination}")
        elif destination.exists():
            raise ValueError(f"destination appeared after preview: {destination}")

    source_data = plan.source_exe.read_bytes()
    current_source_sha = _validate_retail_executable_bytes(
        source_data, plan.source_exe_sha256
    )
    patch_result = None
    if plan.exe_patch_required:
        binding = PhysicsBinding(
            plan.composition.carrier_type, plan.composition.physics_family
        )
        patch_result = patch_family_initializer(
            source_data, (binding,), catalog=plan.catalog
        )
        if patch_result.patched_sha256 != plan.planned_exe_sha256:
            raise ValueError("executable bytes changed after composition preview")

    # Stage every donor byte before creating or replacing a runtime resource.
    artifact_root = root / ARTIFACT_RELATIVE
    backup_root = artifact_root / "backups" / manifest.stem
    manifest.parent.mkdir(parents=True, exist_ok=True)
    backup_root.mkdir(parents=True, exist_ok=False)
    backup_paths: list[Path] = []
    temporary_directory: tempfile.TemporaryDirectory[str] | None = None
    manifest_written = False
    try:
        backup_files_dir = backup_root / "files"
        backup_files_dir.mkdir(parents=True, exist_ok=True)
        overlay_rows = _manifest_overlay_rows(plan, backup_root)
        for entry in (*plan.overlay_writes, *plan.overlay_removals):
            backup_path = entry.get("_backup_path")
            if backup_path is not None:
                _atomic_write(backup_path, entry["pre_apply_data"])
                backup_paths.append(backup_path)

        if plan.overlay_writes:
            temporary_directory = tempfile.TemporaryDirectory(
                prefix="r-veh1-stage-", dir=artifact_root
            )
            stage_root = Path(temporary_directory.name)
            for index, entry in enumerate(plan.overlay_writes):
                stage_path = stage_root / f"{index:05d}.stage"
                stage_path.write_bytes(entry["data"])
                if _sha256(stage_path.read_bytes()) != entry["applied_sha256"]:
                    raise ValueError(f"staged donor hash mismatch: {entry['donor_relative_path']}")
                entry["_staged_path"] = stage_path

        exe_changes = None
        if patch_result is not None and output_exe is not None and output_backup is not None:
            exe_changes = {
                "source_exe_relative_path": _install_relative(root, plan.source_exe),
                "source_sha256": current_source_sha,
                "output_exe_relative_path": _install_relative(root, output_exe),
                "original_backup_relative_path": _install_relative(root, output_backup),
                "patched_sha256": patch_result.patched_sha256,
                "changed_ranges": list(patch_result.changed_ranges),
                "patches": [
                    {
                        "carrier_type": row.carrier_type,
                        "type_id": row.type_id,
                        "physics_family": row.physics_family,
                        "changed": row.changed,
                        "pointer_source": row.pointer_source,
                    }
                    for row in patch_result.patches
                ],
            }

        artifact_relative = artifact_root.relative_to(root).as_posix()
        manifest_payload = {
            "schema_version": 1,
            "tool": USER_FACING_NAME,
            "build": RETAIL_BUILD_NAME,
            "status": "applying",
            "install_root": str(root),
            "source_exe_sha256": current_source_sha,
            "composition": plan.composition.to_dict(),
            "runtime_family": plan.composition.runtime_family,
            "exe_patch_required": plan.exe_patch_required,
            "model_overlay_required": plan.model_overlay_required,
            "exe_changes": exe_changes,
            "model_overlay_changes": overlay_rows,
            "model_donor_package": {
                "family": plan.donor_package["family"] if plan.donor_package else plan.composition.model_donor,
                "provenance": plan.donor_package["provenance"] if plan.donor_package else "MISSING_ADVANCED_OVERRIDE",
                "file_count": plan.donor_package["file_count"] if plan.donor_package else 0,
                "archive_fallback_paths": list(plan.archive_fallbacks),
            },
            "model_destination_directory": _install_relative(
                root, plan.destination_directory
            ),
            # The preview records directories that may need creation. The
            # manifest starts empty and is updated only after this transaction
            # itself successfully creates each directory.
            "created_directories": [],
            "backup_root_relative_path": f"{artifact_relative}/backups/{manifest.stem}",
            "source_exe_modified": False,
        }
        _atomic_write(
            manifest,
            (json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        )
        manifest_written = True

        for relative in sorted(
            plan.created_directories,
            key=lambda value: (value.count("/"), value.casefold()),
        ):
            directory = _join_install_relative(root, relative)
            if directory.exists():
                if directory.is_symlink() or not directory.is_dir():
                    raise ValueError(f"planned model directory is not a safe directory: {directory}")
                continue
            try:
                directory.mkdir()
            except FileExistsError:
                # A directory created between exists() and mkdir() is not
                # tool-owned and must never be recorded for restore cleanup.
                if directory.is_symlink() or not directory.is_dir():
                    raise ValueError(f"planned model directory is not a safe directory: {directory}")
                continue
            manifest_payload["created_directories"].append(relative)
            _atomic_write(
                manifest,
                (json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
            )
        for entry in plan.overlay_writes:
            destination = Path(entry["destination_path"])
            _atomic_write(destination, Path(entry["_staged_path"]).read_bytes())
        for entry in plan.overlay_removals:
            Path(entry["destination_path"]).unlink()

        if patch_result is not None and output_exe is not None and output_backup is not None:
            _atomic_write(output_backup, source_data)
            _atomic_write(output_exe, patch_result.data)

        manifest_payload["status"] = "applied"
        manifest_payload["patched_exe_sha256"] = patch_result.patched_sha256 if patch_result else None
        _atomic_write(
            manifest,
            (json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        )
    except Exception as exc:
        if manifest_written:
            try:
                restore_vehicle_composition(manifest, expected_exe_sha256=current_source_sha)
            except Exception as rollback_exc:
                raise RuntimeError(
                    f"composition apply failed ({exc}); automatic rollback also needs attention "
                    f"({rollback_exc}); manifest: {manifest}"
                ) from exc
        else:
            _cleanup_artifact_files(
                backup_paths,
                (backup_root / "files", backup_root, backup_root.parent),
            )
        raise
    finally:
        if temporary_directory is not None:
            temporary_directory.cleanup()

    return {
        "status": "APPLIED_COMPOSITION",
        "composition": plan.composition.to_dict(),
        "output_exe": str(output_exe) if output_exe else None,
        "manifest": str(manifest),
        "exe_patch_required": plan.exe_patch_required,
        "model_overlay_required": plan.model_overlay_required,
        "model_overlay_written": len(plan.overlay_writes),
        "stale_loose_files_removed": len(plan.overlay_removals),
        "source_exe_modified": False,
    }


def _read_composition_manifest(
    manifest_path: Path,
    *,
    install_root: Path | None = None,
    expected_exe_sha256: str = RETAIL_EXE_SHA256,
) -> tuple[Path, dict[str, Any]]:
    raw_path = Path(manifest_path).expanduser()
    if not raw_path.is_absolute():
        if install_root is None:
            raw_path = Path.cwd() / raw_path
        else:
            raw_path = Path(install_root).expanduser().resolve() / raw_path
    path = Path(os.path.abspath(raw_path))
    if install_root is None:
        parts = path.parts
        if len(parts) < 5 or tuple(part.casefold() for part in parts[-4:-1]) != (
            ".research-output", "r-veh1", "manifests"
        ):
            raise ValueError("manifest is not under .research-output/r-veh1/manifests")
        root = Path(*parts[:-4]).resolve()
    else:
        root = Path(install_root).expanduser().resolve()
    path = _composition_manifest_path(root, path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"vehicle composition manifest is unreadable: {path}") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or data.get("tool") != USER_FACING_NAME
        or not isinstance(data.get("install_root"), str)
        or Path(data["install_root"]).resolve() != root
    ):
        raise ValueError("vehicle composition manifest has an unsupported schema or install root")
    _validate_composition_manifest_structure(
        root, path, data, expected_exe_sha256=expected_exe_sha256
    )
    return root, data


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def _validate_composition_manifest_structure(
    root: Path,
    manifest_path: Path,
    data: dict[str, Any],
    *,
    expected_exe_sha256: str,
) -> None:
    """Fail closed on edited manifests before restore can touch install files."""
    composition = data.get("composition")
    if not isinstance(composition, dict):
        raise ValueError("vehicle composition manifest has no composition identity")
    identities = {}
    for field, label in (
        ("carrier_type", "carrier"),
        ("physics_family", "physics family"),
        ("model_donor", "model donor"),
        ("runtime_family", "runtime family"),
    ):
        value = composition.get(field)
        identities[field] = _safe_family_name(value, label)
    if identities["runtime_family"].casefold() != identities["physics_family"].casefold():
        raise ValueError("manifest runtime family must equal the selected physics family")
    manifest_runtime = data.get("runtime_family")
    if not isinstance(manifest_runtime, str) or manifest_runtime.casefold() != identities["runtime_family"].casefold():
        raise ValueError("manifest runtime-family fields disagree")
    if data.get("source_exe_sha256") != expected_exe_sha256:
        raise ValueError("composition manifest source EXE hash is not the verified retail build")
    if data.get("source_exe_modified") is not False:
        raise ValueError("composition manifest claims the source executable was modified")

    expected_backup_root = (ARTIFACT_RELATIVE / "backups" / manifest_path.stem).as_posix()
    backup_root = data.get("backup_root_relative_path")
    if not isinstance(backup_root, str) or backup_root.casefold() != expected_backup_root.casefold():
        raise ValueError("composition manifest has an unexpected backup root")
    _join_install_relative(root, expected_backup_root)

    target_parts = ("DataGx", "Vehicles", identities["runtime_family"])
    target_key = tuple(part.casefold() for part in target_parts)
    destination_value = data.get("model_destination_directory")
    if not isinstance(destination_value, str):
        raise ValueError("composition manifest has no model destination directory")
    destination_parts = _safe_relative_path(destination_value).parts
    if tuple(part.casefold() for part in destination_parts) != target_key:
        raise ValueError("composition manifest model destination disagrees with runtime family")

    exe_patch_required = identities["carrier_type"].casefold() != identities["physics_family"].casefold()
    if type(data.get("exe_patch_required")) is not bool or data["exe_patch_required"] != exe_patch_required:
        raise ValueError("composition manifest EXE patch flag disagrees with carrier and physics identities")
    model_overlay_required = identities["model_donor"].casefold() != identities["runtime_family"].casefold()
    if type(data.get("model_overlay_required")) is not bool or data["model_overlay_required"] != model_overlay_required:
        raise ValueError("composition manifest model-overlay flag disagrees with its identities")

    overlay_rows = data.get("model_overlay_changes")
    if not isinstance(overlay_rows, list):
        raise ValueError("composition manifest model-overlay changes are malformed")
    destinations: set[str] = set()
    backup_paths: set[str] = set()
    allowed_created_dirs: set[str] = set()
    for row in overlay_rows:
        if not isinstance(row, dict):
            raise ValueError("composition manifest contains a malformed model-overlay row")
        relative = _safe_relative_path(row.get("destination_relative_path"))
        if len(relative.parts) < 4 or tuple(part.casefold() for part in relative.parts[:3]) != target_key:
            raise ValueError("manifest model file is outside its runtime-family directory")
        folded_destination = relative.as_posix().casefold()
        if folded_destination in destinations:
            raise ValueError("composition manifest repeats a model destination")
        destinations.add(folded_destination)
        _join_install_relative(root, relative.as_posix())
        if not isinstance(row.get("donor_family"), str) or row["donor_family"].casefold() != identities["model_donor"].casefold():
            raise ValueError("manifest donor identity disagrees with the composition")
        operation = row.get("operation")
        existed_before = row.get("existed_before")
        if type(existed_before) is not bool:
            raise ValueError("manifest model row has an invalid existed_before flag")
        if operation == "WRITE_DONOR_FILE":
            _safe_relative_path(row.get("donor_relative_path"))
            if row.get("source_provenance") not in {"DATA_SMA", "LOOSE_OVERRIDE"}:
                raise ValueError("manifest donor file has unknown source provenance")
            if not _is_sha256(row.get("applied_sha256")):
                raise ValueError("manifest donor file has an invalid applied SHA-256")
            for index in range(1, len(relative.parts)):
                current = relative.parts[:index]
                allowed_created_dirs.add("/".join(part.casefold() for part in current))
        elif operation == "REMOVE_STALE_LOOSE":
            if row.get("donor_relative_path") is not None or row.get("applied_sha256") is not None:
                raise ValueError("manifest stale-file row contains donor write metadata")
            if row.get("source_provenance") != "STALE_DESTINATION" or not existed_before:
                raise ValueError("manifest stale-file row has invalid provenance or state")
        else:
            raise ValueError("composition manifest contains an unsupported model operation")

        if existed_before:
            pre_sha = row.get("pre_apply_sha256")
            backup_relative = row.get("backup_relative_path")
            backup_sha = row.get("backup_sha256")
            if not _is_sha256(pre_sha) or backup_sha != pre_sha:
                raise ValueError("manifest original model-file hashes are inconsistent")
            backup_path = _safe_relative_path(backup_relative)
            expected_backup_prefix = tuple(part.casefold() for part in PurePosixPath(expected_backup_root, "files").parts)
            if (
                len(backup_path.parts) != len(expected_backup_prefix) + 1
                or tuple(part.casefold() for part in backup_path.parts[:-1]) != expected_backup_prefix
                or re.fullmatch(r"[0-9]+\.bin", backup_path.name, re.IGNORECASE) is None
            ):
                raise ValueError("manifest model backup path is outside its transaction backup directory")
            folded_backup = backup_path.as_posix().casefold()
            if folded_backup in backup_paths:
                raise ValueError("composition manifest repeats a model backup path")
            backup_paths.add(folded_backup)
            _join_install_relative(root, backup_path.as_posix())
        elif any(row.get(field) is not None for field in (
            "pre_apply_sha256", "backup_relative_path", "backup_sha256"
        )):
            raise ValueError("new model file unexpectedly has original-file backup metadata")

    created = data.get("created_directories")
    if not isinstance(created, list):
        raise ValueError("composition manifest created-directory list is malformed")
    seen_created: set[str] = set()
    for value in created:
        directory = _safe_relative_path(value)
        folded = directory.as_posix().casefold()
        if folded not in allowed_created_dirs or folded in seen_created:
            raise ValueError("composition manifest lists an unrelated or duplicate created directory")
        seen_created.add(folded)
        _join_install_relative(root, directory.as_posix())

    exe_changes = data.get("exe_changes")
    if exe_patch_required != (exe_changes is not None):
        raise ValueError("composition manifest EXE changes disagree with patch flag")
    if exe_changes is not None:
        if not isinstance(exe_changes, dict):
            raise ValueError("composition manifest EXE changes are malformed")
        if exe_changes.get("source_sha256") != expected_exe_sha256:
            raise ValueError("composition manifest EXE source hash is invalid")
        source_relative = _safe_relative_path(exe_changes.get("source_exe_relative_path"))
        if source_relative.as_posix().casefold() != "mrallye.exe":
            raise ValueError("composition manifest source path is not MRallye.exe")
        output_relative = _safe_relative_path(exe_changes.get("output_exe_relative_path"))
        if output_relative.as_posix().casefold() == "mrallye.exe" or output_relative.suffix.casefold() != ".exe":
            raise ValueError("composition manifest output path is not a separate executable copy")
        backup_relative = _safe_relative_path(exe_changes.get("original_backup_relative_path"))
        if backup_relative.as_posix().casefold() != (output_relative.as_posix() + ".original").casefold():
            raise ValueError("composition manifest executable backup path is inconsistent")
        if not _is_sha256(exe_changes.get("patched_sha256")):
            raise ValueError("composition manifest patched executable SHA-256 is invalid")
        _join_install_relative(root, output_relative.as_posix())
        _join_install_relative(root, backup_relative.as_posix())


def _composition_current_state(
    root: Path, manifest_path: Path, data: dict[str, Any], expected_exe_sha256: str
) -> tuple[bool, list[str], list[tuple[dict[str, Any], Path, str]]]:
    conflicts: list[str] = []
    states: list[tuple[dict[str, Any], Path, str]] = []
    status = data.get("status")
    if status not in {"applying", "applied", "restoring", "restored"}:
        raise ValueError("vehicle composition manifest has an unknown state")
    for row in data.get("model_overlay_changes", []):
        destination = _join_install_relative(root, row.get("destination_relative_path", ""))
        current_sha = _sha256(destination.read_bytes()) if destination.is_file() and not destination.is_symlink() else None
        operation = row.get("operation")
        pre_sha = row.get("pre_apply_sha256")
        applied_sha = row.get("applied_sha256")
        if operation == "WRITE_DONOR_FILE":
            if current_sha == applied_sha:
                state = "applied"
            elif row.get("existed_before") and current_sha == pre_sha:
                state = "restored"
            elif not row.get("existed_before") and current_sha is None:
                state = "restored"
            else:
                conflicts.append(str(destination))
                state = "conflict"
        elif operation == "REMOVE_STALE_LOOSE":
            if current_sha is None:
                state = "applied"
            elif current_sha == pre_sha:
                state = "restored"
            else:
                conflicts.append(str(destination))
                state = "conflict"
        else:
            raise ValueError(f"unsupported model overlay operation: {operation}")

        if row.get("existed_before"):
            backup_relative = row.get("backup_relative_path")
            if not isinstance(backup_relative, str):
                raise ValueError(f"manifest backup is missing for {destination}")
            backup = _join_install_relative(root, backup_relative)
            if not backup.is_file() or _sha256(backup.read_bytes()) != row.get("backup_sha256"):
                raise ValueError(f"verified model backup is missing or changed: {backup}")
        states.append((row, destination, state))

    exe_changes = data.get("exe_changes")
    exe_state = "none"
    if exe_changes is not None:
        if exe_changes.get("source_sha256") != expected_exe_sha256:
            raise ValueError("composition manifest source EXE hash is not the verified retail build")
        output = _join_install_relative(root, exe_changes.get("output_exe_relative_path", ""))
        backup = _join_install_relative(root, exe_changes.get("original_backup_relative_path", ""))
        if backup.exists():
            if not backup.is_file() or _sha256(backup.read_bytes()) != expected_exe_sha256:
                raise ValueError("verified original executable backup is missing or changed")
        elif status != "applying":
            # During the initial applying state, the atomic backup write may
            # not have happened yet. A present but incorrect backup is never
            # treated as an interrupted write.
            raise ValueError("verified original executable backup is missing or changed")
        current_sha = _sha256(output.read_bytes()) if output.is_file() else None
        if current_sha == exe_changes.get("patched_sha256"):
            exe_state = "applied"
        elif current_sha == expected_exe_sha256:
            exe_state = "restored"
        elif current_sha is None and status == "applying":
            exe_state = "restored"
        else:
            conflicts.append(str(output))
            exe_state = "conflict"
        if output.resolve() == Path(data.get("install_root", "")).resolve() / "MRallye.exe":
            raise ValueError("manifest illegally targets the source retail executable")

    return not conflicts, conflicts, states + ([({"_exe": exe_changes}, output, exe_state)] if exe_changes else [])


def restore_vehicle_composition(
    manifest_path: Path,
    *,
    expected_exe_sha256: str = RETAIL_EXE_SHA256,
    install_root: Path | None = None,
) -> dict[str, Any]:
    """Restore only recorded files still matching their applied hashes."""
    root, data = _read_composition_manifest(
        manifest_path,
        install_root=install_root,
        expected_exe_sha256=expected_exe_sha256,
    )
    manifest = Path(manifest_path).expanduser().resolve()
    safe, conflicts, states = _composition_current_state(
        root, manifest, data, expected_exe_sha256
    )
    if not safe:
        raise ValueError(
            "restore conflicts with files changed after apply; no files were restored: "
            + ", ".join(conflicts)
        )
    if data.get("status") == "restored" and all(state == "restored" for _, _, state in states):
        return {
            "status": "ALREADY_RESTORED",
            "manifest": str(manifest),
            "composition": data.get("composition"),
        }

    data["status"] = "restoring"
    _atomic_write(manifest, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    restored_files = 0
    for row, destination, state in states:
        if "_exe" in row:
            exe_changes = row["_exe"]
            if state == "applied":
                backup = _join_install_relative(root, exe_changes["original_backup_relative_path"])
                _atomic_write(destination, backup.read_bytes())
                restored_files += 1
            continue
        if state == "restored":
            continue
        if row["operation"] == "WRITE_DONOR_FILE":
            if row["existed_before"]:
                backup = _join_install_relative(root, row["backup_relative_path"])
                _atomic_write(destination, backup.read_bytes())
            else:
                destination.unlink()
        elif row["operation"] == "REMOVE_STALE_LOOSE":
            backup = _join_install_relative(root, row["backup_relative_path"])
            _atomic_write(destination, backup.read_bytes())
        restored_files += 1

    for relative in sorted(
        data.get("created_directories", []),
        key=lambda value: (value.count("/"), value.casefold()),
        reverse=True,
    ):
        directory = _join_install_relative(root, relative)
        if directory.is_dir() and not directory.is_symlink():
            try:
                directory.rmdir()
            except OSError:
                pass
    data["status"] = "restored"
    data["restored_files"] = restored_files
    _atomic_write(manifest, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return {
        "status": "RESTORED_COMPOSITION",
        "manifest": str(manifest),
        "composition": data.get("composition"),
        "restored_files": restored_files,
    }


def discover_vehicle_composition_manifests(
    install_root: Path,
    *,
    expected_exe_sha256: str = RETAIL_EXE_SHA256,
) -> list[dict[str, Any]]:
    """List manifests and classify current file state without modifying files."""
    root = Path(install_root).expanduser().resolve()
    directory = root / ARTIFACT_RELATIVE / "manifests"
    if not directory.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(directory.glob(f"*{MANIFEST_SUFFIX}"), key=lambda item: item.name.casefold()):
        item: dict[str, Any] = {
            "manifest": path,
            "valid": False,
            "status": "INVALID_MANIFEST",
            "composition": None,
            "output_exe": None,
        }
        try:
            manifest_root, data = _read_composition_manifest(
                path, install_root=root, expected_exe_sha256=expected_exe_sha256
            )
            safe, conflicts, states = _composition_current_state(
                manifest_root, path, data, expected_exe_sha256
            )
            current_status = data.get("status")
            if not safe:
                shown_status = "CONFLICT"
            elif all(state == "restored" for _, _, state in states):
                shown_status = "restored"
            elif current_status == "applied" and all(state == "applied" for _, _, state in states):
                shown_status = "applied"
            else:
                shown_status = "interrupted"
            exe_changes = data.get("exe_changes") or {}
            output = exe_changes.get("output_exe_relative_path")
            item.update({
                "valid": safe,
                "status": shown_status,
                "composition": data.get("composition"),
                "output_exe": _join_install_relative(root, output) if output else None,
                "manifest_data": data,
                "error": "; ".join(conflicts) if conflicts else None,
            })
        except (OSError, ValueError, FormatError) as exc:
            item["error"] = str(exc)
        result.append(item)
    return result
