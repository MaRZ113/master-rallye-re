"""Research-grade orchestration for portable Master Rallye vehicle packages.

This is deliberately not a GXM cooker. Native model output still comes from
the verified, isolated retail runtime and a human loads the prepared vehicle.
The module inventories sources, selects one consistent model strategy,
resolves textures, validates cooked DX, and assembles cache-only packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from . import __version__
from .authoring_paths import (
    AuthoringPathError,
    discover_embedded_authoring_paths,
    materialize_authoring_mirror,
    write_guarded_junction_scripts,
)
from .collision_analysis import analyze_collision_geometry_topology
from .collision_writer import serialize_tag101
from .dx import parse_dx_bytes
from .dx_revision_upgrade import (
    DxRevisionUpgradeError,
    REVISION_131,
    REVISION_135,
    upgrade_dx_131_to_135_with_report,
    validate_existing_rev135,
    validate_generated_rev135,
)
from .dxt import parse_dxt_bytes
from .gxm import (
    parse_gxm_geometry_prefix_bytes,
    parse_gxm_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)
from .gxi import encode_gxi_as_observed_dxt, parse_gxi_bytes
from .sidecar import normalize_texture_value


VEHICLE_ROLES = ("complete", "car", "wheel")
ROLE_ALIASES = {"complete": ("comlplete.gxm",)}
SUPPORTED_RETAIL_EXE_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
SUPPORTED_RETAIL_DATA_SMA_SHA256 = "03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f"
SUPPORTED_COOK_HARNESS_EXE_SHA256 = "a6a5f0590405e1a2051ef21f2be58197857e72f4a651506627c8966083a21d91"
_SOURCE_EXTENSIONS = {".dx", ".dxt", ".gxm", ".gxi", ".gxb", ".gxp", ".txt", ".tga"}
_PACKAGE_ALLOWED_FILES = {"package-manifest.json", "validation-report.json"}
class SourceCookerError(ValueError):
    """A source package or orchestration job did not meet a safety gate."""


class ModelStrategy(str, Enum):
    RETAIL_NATIVE_GXM = "retail-native-gxm"
    OFFLINE_DX_131_TO_135 = "offline-131-to-135"
    PASS_THROUGH_135 = "pass-through-135"
    UNSUPPORTED_REV127_CACHE_ONLY = "unsupported-rev127-cache-only"


class TextureStrategy(str, Enum):
    AUTO = "auto"
    REUSE_VALID_DXT = "reuse-valid-dxt"
    OFFLINE_GXI_TO_DXT = "offline-gxi-to-dxt"


_MODEL_STRATEGY_CHOICES = (
    "auto",
    ModelStrategy.RETAIL_NATIVE_GXM.value,
    ModelStrategy.OFFLINE_DX_131_TO_135.value,
    ModelStrategy.PASS_THROUGH_135.value,
)
_VALIDATION_STATUS_KEYS = (
    "FORMAT_VALIDATED",
    "TEXTURES_RESOLVED",
    "COLLISION_STRUCTURALLY_VALID",
    "DETERMINISTIC_COOK_CONFIRMED",
    "CACHE_ONLY_PORTABLE",
    "GAMEPLAY_RUNTIME_CONFIRMED",
)


def build_validation_status(**updates: str) -> dict[str, str]:
    """Return the independent evidence dimensions without collapsing them."""
    unexpected = set(updates) - set(_VALIDATION_STATUS_KEYS)
    if unexpected:
        raise SourceCookerError(f"unknown validation status fields: {sorted(unexpected)}")
    result = {key: "NOT_ASSESSED" for key in _VALIDATION_STATUS_KEYS}
    for key, value in updates.items():
        if not isinstance(value, str) or not value.strip():
            raise SourceCookerError(f"validation status {key} must be a non-empty string")
        result[key] = value
    return result


@dataclass(frozen=True)
class VehicleSourceInventory:
    source_root: Path
    family: str
    files: tuple[dict[str, Any], ...]
    role_files: dict[str, dict[str, dict[str, Any]]]
    gxm_info: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "tool": "Master Rallye Source Cooker",
            "tool_version": __version__,
            "family": self.family,
            "source_root": str(self.source_root),
            "file_count": len(self.files),
            "files": list(self.files),
            "roles": self.role_files,
            "gxm_validation": self.gxm_info,
        }


@dataclass(frozen=True)
class StrategyDecision:
    selected: ModelStrategy
    requested: str
    output_revision: int | None
    role_inputs: dict[str, str | None]
    source_revisions: dict[str, int | None]
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected": self.selected.value,
            "requested": self.requested,
            "output_revision": self.output_revision,
            "role_inputs": self.role_inputs,
            "source_revisions": self.source_revisions,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class TextureAsset:
    name: str
    strategy: str
    output_filename: str
    source_relative_path: str
    source_sha256: str
    output_sha256: str
    width: int
    height: int
    byte_identical_to_historical_dxt: bool | None
    data: bytes

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "strategy": self.strategy,
            "output_filename": self.output_filename,
            "source_relative_path": self.source_relative_path,
            "source_sha256": self.source_sha256,
            "output_sha256": self.output_sha256,
            "width": self.width,
            "height": self.height,
            "byte_identical_to_historical_dxt": self.byte_identical_to_historical_dxt,
            "size": len(self.data),
        }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_reparse_or_symlink(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0) & 0x400)
    except (OSError, TypeError):
        return False


def _safe_files(root: Path) -> list[Path]:
    root = Path(root).resolve()
    if not root.is_dir():
        raise SourceCookerError(f"source directory does not exist: {root}")
    result = []
    for path in root.rglob("*"):
        if _is_reparse_or_symlink(path):
            if path.is_dir():
                raise SourceCookerError(f"source tree contains a reparse directory: {path}")
            continue
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError as exc:
            raise SourceCookerError(f"source file escapes source directory: {path}") from exc
        result.append(path)
    return sorted(result, key=lambda item: item.relative_to(root).as_posix().casefold())


def _role_for_filename(filename: str, extension: str) -> tuple[str | None, str | None]:
    folded = filename.casefold()
    if extension.casefold() == ".gxm":
        for role in VEHICLE_ROLES:
            if folded == f"{role}.gxm":
                return role, None
            for alias in ROLE_ALIASES.get(role, ()):
                if folded == alias.casefold():
                    return role, alias
    elif extension.casefold() == ".dx":
        for role in VEHICLE_ROLES:
            if folded == f"{role}.dx":
                return role, None
    return None, None


def _probe_gxm(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    prefix = parse_gxm_prefix_bytes(data, str(path))
    if prefix.prefix_kind != "material_table":
        return {
            "status": "UNSUPPORTED_PREFIX",
            "prefix_kind": prefix.prefix_kind,
            "material_count": len(prefix.materials),
            "tail_bytes": prefix.tail_size,
            "texture_references": [],
        }
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
    references = sorted({
        slot.reference for material in prefix.materials for slot in material.slots
        if slot.reference.casefold() != "null" and slot.reference.casefold().endswith(".gxi")
    }, key=str.casefold)
    return {
        "status": "PASS_SUPPORTED_PREFIX",
        "prefix_kind": prefix.prefix_kind,
        "material_count": len(prefix.materials),
        "vector_a_count": geometry.vector_a_count,
        "vector_b_count": geometry.vector_b_count,
        "triangle_record_count": triangles.record_count,
        "vector_c_count": triangles.vector_c_count,
        "opaque_tail_bytes": len(data) - triangles.hierarchy_offset,
        "texture_references": references,
    }


def _file_record(root: Path, path: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    extension = path.suffix.casefold()
    # Model roles are top-level package entries. Nested legacy variants such as
    # ``lpha/car.dx`` remain inventoried but cannot shadow the selected role.
    role, alias = _role_for_filename(path.name, extension) if path.parent == root else (None, None)
    data = path.read_bytes()
    record: dict[str, Any] = {
        "relative_path": relative,
        "filename": path.name,
        "size": len(data),
        "sha256": _sha256(data),
        "extension": extension,
        "role": role,
        "filename_alias": alias,
        "format_status": "INVENTORIED_ONLY",
        "format_details": {},
    }
    try:
        if extension == ".dx":
            if len(data) < 8 or struct.unpack_from("<I", data)[0] != 0xD00D:
                raise SourceCookerError("DX magic mismatch")
            revision = struct.unpack_from("<I", data, 4)[0]
            record["format_status"] = "HEADER_READ"
            record["format_details"] = {"revision": revision}
        elif extension == ".gxm":
            detail = _probe_gxm(path)
            record["format_status"] = detail["status"]
            record["format_details"] = detail
        elif extension == ".dxt":
            image = parse_dxt_bytes(data, relative)
            record["format_status"] = "PASS"
            record["format_details"] = {"width": image.width, "height": image.height}
        elif extension == ".gxi":
            image = parse_gxi_bytes(data, relative)
            record["format_status"] = "PASS"
            record["format_details"] = {"width": image.width, "height": image.height}
    except Exception as exc:
        record["format_status"] = "FAIL"
        record["format_details"] = {"error": f"{type(exc).__name__}: {exc}"}
    return record


def inventory_vehicle_source(source_root: Path, family: str | None = None) -> VehicleSourceInventory:
    root = Path(source_root).resolve()
    if not root.is_dir():
        raise SourceCookerError(f"source vehicle folder does not exist: {root}")
    family_name = family or root.name
    if not family_name or family_name in {".", ".."} or any(char in family_name for char in "\\/:*?\"<>|"):
        raise SourceCookerError(f"invalid output family name: {family_name!r}")
    files = tuple(_file_record(root, path) for path in _safe_files(root))
    role_files: dict[str, dict[str, dict[str, Any]]] = {role: {} for role in VEHICLE_ROLES}
    gxm_info: dict[str, dict[str, Any]] = {}
    for record in files:
        role = record["role"]
        extension = record["extension"]
        if role:
            if extension in role_files[role]:
                previous = role_files[role][extension]
                raise SourceCookerError(
                    f"ambiguous {role}{extension}: {previous['relative_path']} and {record['relative_path']}"
                )
            role_files[role][extension] = record
            if extension == ".gxm":
                gxm_info[role] = dict(record["format_details"], status=record["format_status"])
    for role, aliases in ROLE_ALIASES.items():
        alias_files = [
            record for record in files
            if record["role"] == role
            and record["filename"].casefold() in {name.casefold() for name in aliases}
        ]
        if role_files[role].get(".gxm") and role_files[role][".gxm"].get("filename_alias") is None and alias_files:
            raise SourceCookerError(
                f"both canonical and known typo GXM filenames exist for role {role}: "
                f"{role_files[role]['.gxm']['relative_path']} and {alias_files[0]['relative_path']}"
            )
    return VehicleSourceInventory(root, family_name, files, role_files, gxm_info)


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _role_path(inventory: VehicleSourceInventory, role: str, extension: str) -> Path | None:
    item = inventory.role_files.get(role, {}).get(extension)
    return inventory.source_root / item["relative_path"] if item else None


def _all_roles_have_gxm(inventory: VehicleSourceInventory) -> bool:
    return all(
        (record := inventory.role_files[role].get(".gxm")) is not None
        and record["format_status"] == "PASS_SUPPORTED_PREFIX"
        for role in VEHICLE_ROLES
    )


def _dx_role_revisions(inventory: VehicleSourceInventory) -> dict[str, int | None]:
    revisions: dict[str, int | None] = {}
    for role in VEHICLE_ROLES:
        record = inventory.role_files[role].get(".dx")
        revisions[role] = record.get("format_details", {}).get("revision") if record else None
    return revisions


def _check_dx_strategy(inventory: VehicleSourceInventory, revision: int) -> None:
    for role in VEHICLE_ROLES:
        path = _role_path(inventory, role, ".dx")
        if path is None:
            raise SourceCookerError(f"missing required {role}.dx for revision {revision} strategy")
        data = path.read_bytes()
        actual = struct.unpack_from("<I", data, 4)[0] if len(data) >= 8 else None
        if actual != revision:
            raise SourceCookerError(f"{role}.dx has revision {actual!r}, expected {revision}")
        if revision == REVISION_131:
            upgrade_dx_131_to_135_with_report(data, str(path))
        elif revision == REVISION_135:
            validate_existing_rev135(data, str(path))
        else:
            raise SourceCookerError(f"unsupported DX revision: {revision}")


def select_model_strategy(
    inventory: VehicleSourceInventory,
    requested: str = "auto",
) -> StrategyDecision:
    requested = requested.casefold().strip()
    valid_values = {"auto", *(item.value for item in ModelStrategy)}
    if requested not in valid_values:
        raise SourceCookerError(f"unknown model strategy {requested!r}; expected one of {sorted(valid_values)}")
    role_inputs = {
        role: (
            _role_path(inventory, role, ".gxm").relative_to(inventory.source_root).as_posix()
            if _role_path(inventory, role, ".gxm") else
            _role_path(inventory, role, ".dx").relative_to(inventory.source_root).as_posix()
            if _role_path(inventory, role, ".dx") else None
        )
        for role in VEHICLE_ROLES
    }
    revisions = _dx_role_revisions(inventory)
    if requested in {"auto", ModelStrategy.RETAIL_NATIVE_GXM.value} and _all_roles_have_gxm(inventory):
        return StrategyDecision(
            ModelStrategy.RETAIL_NATIVE_GXM, requested, REVISION_135, role_inputs, revisions,
            "READY", "all three GXM roles pass the currently supported material/geometry/triangle prefix checks",
        )
    if requested == ModelStrategy.RETAIL_NATIVE_GXM.value:
        details = {role: inventory.gxm_info.get(role, {}).get("status", "MISSING") for role in VEHICLE_ROLES}
        raise SourceCookerError(f"retail-native GXM strategy requires usable complete/car/wheel GXM: {details}")

    if requested in {"auto", ModelStrategy.OFFLINE_DX_131_TO_135.value} and all(
        revisions[role] == REVISION_131 for role in VEHICLE_ROLES
    ):
        _check_dx_strategy(inventory, REVISION_131)
        return StrategyDecision(
            ModelStrategy.OFFLINE_DX_131_TO_135, requested, REVISION_135, role_inputs, revisions,
            "READY", "all three roles are supported revision-131 vehicle DX and convert through the canonical R-COOKER2 adapter",
        )
    if requested == ModelStrategy.OFFLINE_DX_131_TO_135.value:
        raise SourceCookerError(f"offline conversion requires revision 131 for all roles; found {revisions}")

    if requested in {"auto", ModelStrategy.PASS_THROUGH_135.value} and all(
        revisions[role] == REVISION_135 for role in VEHICLE_ROLES
    ):
        _check_dx_strategy(inventory, REVISION_135)
        return StrategyDecision(
            ModelStrategy.PASS_THROUGH_135, requested, REVISION_135, role_inputs, revisions,
            "READY", "all three roles are structurally valid revision-135 vehicle DX",
        )
    if requested == ModelStrategy.PASS_THROUGH_135.value:
        raise SourceCookerError(f"pass-through requires revision 135 for all roles; found {revisions}")

    rev127_only = all(revisions[role] == 127 for role in VEHICLE_ROLES)
    usable_gxm = _all_roles_have_gxm(inventory)
    if requested == ModelStrategy.UNSUPPORTED_REV127_CACHE_ONLY.value and (not rev127_only or usable_gxm):
        raise SourceCookerError(
            "unsupported-rev127-cache-only applies only when all three DX roles are revision 127 "
            "and no complete/car/wheel GXM source set is usable"
        )
    if (requested == ModelStrategy.UNSUPPORTED_REV127_CACHE_ONLY.value and rev127_only and not usable_gxm) or (
        requested == "auto" and rev127_only and not usable_gxm
    ):
        return StrategyDecision(
            ModelStrategy.UNSUPPORTED_REV127_CACHE_ONLY, requested, None, role_inputs, revisions,
            "UNSUPPORTED", "revision-127 DX without a usable source GXM has no safe conversion path",
        )

    present = {
        role: {
            "gxm": inventory.gxm_info.get(role, {}).get("status", "MISSING"),
            "dx_revision": revisions[role],
        }
        for role in VEHICLE_ROLES
    }
    raise SourceCookerError(
        "no single consistent model strategy supports all complete/car/wheel roles; "
        f"mixed or missing inputs are not silently combined: {present}"
    )


def _find_asset(root: Path, stem: str, extension: str) -> tuple[Path | None, list[Path]]:
    folded = stem.casefold()
    candidates = [
        path for path in _safe_files(root)
        if path.suffix.casefold() == extension.casefold() and path.stem.casefold() == folded
    ]
    if not candidates:
        return None, []
    top_level = [path for path in candidates if path.parent == root]
    if top_level:
        candidates = top_level
    hashes = {sha256_file(path) for path in candidates}
    if len(hashes) > 1:
        raise SourceCookerError(
            f"ambiguous {extension} files for {stem!r} have different bytes: "
            + ", ".join(path.relative_to(root).as_posix() for path in candidates)
        )
    return candidates[0], candidates


def build_texture_assets(
    source_root: Path,
    required_names: Sequence[str],
    strategy: str = "auto",
) -> list[TextureAsset]:
    """Resolve each DX/GXM texture to validated DXT bytes or the known GXI encoder."""
    source_root = Path(source_root).resolve()
    if not source_root.is_dir():
        raise SourceCookerError(f"texture source directory does not exist: {source_root}")
    try:
        selected_policy = TextureStrategy(strategy.casefold())
    except ValueError as exc:
        raise SourceCookerError(f"unknown texture strategy {strategy!r}") from exc
    normalized = sorted(
        {normalize_texture_value(name) for name in required_names if name.strip().casefold() != "null"},
        key=str.casefold,
    )
    if any(not name or Path(name).name != name or name in {".", ".."} for name in normalized):
        raise SourceCookerError("unsafe texture reference name")

    results: list[TextureAsset] = []
    for name in normalized:
        dxt_path, dxt_candidates = _find_asset(source_root, name, ".dxt")
        gxi_path, gxi_candidates = _find_asset(source_root, name, ".gxi")
        dxt_data: bytes | None = None
        dxt_image = None
        if dxt_path is not None:
            dxt_data = dxt_path.read_bytes()
            try:
                dxt_image = parse_dxt_bytes(dxt_data, str(dxt_path))
            except Exception as exc:
                raise SourceCookerError(f"existing DXT is malformed; refusing silent fallback: {dxt_path}: {exc}") from exc
        gxi_data: bytes | None = None
        gxi_image = None
        if gxi_path is not None:
            gxi_data = gxi_path.read_bytes()
            try:
                gxi_image = parse_gxi_bytes(gxi_data, str(gxi_path))
            except Exception as exc:
                if selected_policy == TextureStrategy.OFFLINE_GXI_TO_DXT:
                    raise SourceCookerError(f"required GXI is malformed: {gxi_path}: {exc}") from exc
                gxi_image = None

        if selected_policy == TextureStrategy.REUSE_VALID_DXT:
            if dxt_data is None or dxt_image is None:
                raise SourceCookerError(f"valid DXT required for {name}, but none was found")
            actual_policy = TextureStrategy.REUSE_VALID_DXT.value
            data = dxt_data
            source_path = dxt_path
            source_hash = _sha256(dxt_data)
            dimensions = (dxt_image.width, dxt_image.height)
            identical = True
        elif selected_policy == TextureStrategy.OFFLINE_GXI_TO_DXT:
            if gxi_data is None or gxi_image is None:
                raise SourceCookerError(f"valid GXI required for offline encoding of {name}, but none was found")
            actual_policy = TextureStrategy.OFFLINE_GXI_TO_DXT.value
            data = encode_gxi_as_observed_dxt(gxi_image)
            output_image = parse_dxt_bytes(data, f"encoded {name}")
            source_path = gxi_path
            source_hash = _sha256(gxi_data)
            dimensions = (output_image.width, output_image.height)
            identical = data == dxt_data if dxt_data is not None else None
        elif dxt_data is not None and dxt_image is not None:
            actual_policy = TextureStrategy.REUSE_VALID_DXT.value
            data = dxt_data
            source_path = dxt_path
            source_hash = _sha256(dxt_data)
            dimensions = (dxt_image.width, dxt_image.height)
            identical = True
        elif gxi_data is not None and gxi_image is not None:
            actual_policy = TextureStrategy.OFFLINE_GXI_TO_DXT.value
            data = encode_gxi_as_observed_dxt(gxi_image)
            output_image = parse_dxt_bytes(data, f"encoded {name}")
            source_path = gxi_path
            source_hash = _sha256(gxi_data)
            dimensions = (output_image.width, output_image.height)
            identical = None
        else:
            raise SourceCookerError(f"required texture {name}.dxt is missing and no valid matching GXI exists")

        if dxt_image is not None and dimensions != (dxt_image.width, dxt_image.height):
            raise SourceCookerError(f"encoded DXT dimensions disagree with historical DXT for {name}")
        results.append(TextureAsset(
            name=name,
            strategy=actual_policy,
            output_filename=f"{name}.dxt",
            source_relative_path=source_path.relative_to(source_root).as_posix(),
            source_sha256=source_hash,
            output_sha256=_sha256(data),
            width=dimensions[0],
            height=dimensions[1],
            byte_identical_to_historical_dxt=identical,
            data=data,
        ))
    return results


def _collision_validation(model) -> dict[str, Any]:
    collision = model.collision
    details: dict[str, Any] = {
        "status": "PASS" if not collision.errors and not collision.warnings else "FAIL",
        "tags": list(collision.tag_ids),
        "errors": list(collision.errors),
        "warnings": list(collision.warnings),
        "tag101": None,
    }
    hull = collision.convex_hull
    if hull is None:
        return details
    try:
        serialized = serialize_tag101(hull)
        rep_a = analyze_collision_geometry_topology(hull.representation_a.geometry_a)
        rep_b = analyze_collision_geometry_topology(hull.representation_b.geometry_a)
        roundtrip = serialized == hull.raw
        topology_ok = all(
            item["all_triangle_edges_incident_twice"]
            and item["euler_characteristic"] == 2
            and item["convex_supporting_planes"] is True
            for item in (rep_a, rep_b)
        )
        details["tag101"] = {
            "roundtrip_byte_identical": roundtrip,
            "representation_a": {
                "vertices": hull.representation_a.geometry_a.vertex_count,
                "triangles": hull.representation_a.geometry_a.triangle_count,
                "topology": rep_a,
            },
            "representation_b": {
                "vertices": hull.representation_b.geometry_a.vertex_count,
                "triangles": hull.representation_b.geometry_a.triangle_count,
                "topology": rep_b,
            },
            "status": "PASS" if roundtrip and topology_ok else "FAIL",
            "secondary_descriptor_semantics": "UNRESOLVED",
        }
        if not roundtrip or not topology_ok:
            details["status"] = "FAIL"
    except Exception as exc:
        details["status"] = "FAIL"
        details["tag101"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    return details


def _model_validation(data: bytes, source: str, expected_strategy: ModelStrategy) -> tuple[bytes, dict[str, Any], Any]:
    if len(data) < 8 or struct.unpack_from("<I", data)[0] != 0xD00D:
        raise SourceCookerError(f"invalid or truncated DX header: {source}")
    revision = struct.unpack_from("<I", data, 4)[0]
    if revision == REVISION_131:
        if expected_strategy != ModelStrategy.OFFLINE_DX_131_TO_135:
            raise SourceCookerError(f"{source} is revision 131 but selected strategy is {expected_strategy.value}")
        output, conversion = upgrade_dx_131_to_135_with_report(data, source)
        validation = validate_generated_rev135(output, f"{source} [generated]")
        validation["adapter"] = "R-COOKER2"
        validation["conversion_report"] = conversion
    elif revision == REVISION_135:
        if expected_strategy == ModelStrategy.OFFLINE_DX_131_TO_135:
            raise SourceCookerError(f"{source} is revision 135 in a revision-131 strategy package")
        output = data
        validation = validate_existing_rev135(output, source)
        validation["adapter"] = (
            "retail-native-cook" if expected_strategy == ModelStrategy.RETAIL_NATIVE_GXM
            else "pass-through"
        )
    else:
        raise SourceCookerError(
            f"unsupported model revision {revision} for {source}; revision-127 cache-only is not converted"
        )
    model = parse_dx_bytes(output, source)
    if validation.get("status") not in {"PASS", "VALID", "VALID_WITH_ORDERING_DIVERGENCE"}:
        raise SourceCookerError(f"{source} did not pass rev135 validation")
    collision_report = _collision_validation(model)
    validation["collision_validation"] = collision_report
    if collision_report["status"] != "PASS":
        raise SourceCookerError(f"{source} collision structure failed validation")
    return output, validation, model


def validate_cache_only_package(package_root: Path, family: str | None = None) -> dict[str, Any]:
    package_root = Path(package_root).resolve()
    if not package_root.is_dir():
        raise SourceCookerError(f"runtime package does not exist: {package_root}")
    files = _safe_files(package_root)
    relative = {path.relative_to(package_root).as_posix().casefold(): path for path in files}
    forbidden = [
        path.relative_to(package_root).as_posix()
        for path in files if path.suffix.casefold() in {".gxm", ".gxi"}
    ]
    if forbidden:
        raise SourceCookerError("cache-only package contains authoring files: " + ", ".join(forbidden))
    unexpected = [
        path.relative_to(package_root).as_posix()
        for path in files
        if path.suffix.casefold() not in {".dx", ".dxt", ".json"}
    ]
    if unexpected:
        raise SourceCookerError("runtime package contains unsupported files: " + ", ".join(unexpected))
    role_models = {}
    required_textures: set[str] = set()
    for role in VEHICLE_ROLES:
        matches = [path for key, path in relative.items() if PurePosixPath(key).name == f"{role}.dx"]
        if len(matches) != 1:
            raise SourceCookerError(f"cache-only package requires exactly one {role}.dx")
        data = matches[0].read_bytes()
        validation = validate_existing_rev135(data, str(matches[0]))
        model = parse_dx_bytes(data, str(matches[0]))
        required_textures.update(
            normalize_texture_value(slot.value)
            for draw in model.physical_draws for slot in draw.texture_slots
            if slot.value.strip().casefold() != "null"
        )
        role_models[role] = {
            "sha256": _sha256(data),
            "size": len(data),
            "revision": REVISION_135,
            "validation_status": validation["status"],
        }
    texture_records = {}
    for name in sorted(required_textures, key=str.casefold):
        matches = [path for key, path in relative.items() if PurePosixPath(key).name.casefold() == f"{name}.dxt".casefold()]
        if len(matches) != 1:
            raise SourceCookerError(f"required runtime DXT {name}.dxt missing or ambiguous")
        texture = parse_dxt_bytes(matches[0].read_bytes(), str(matches[0]))
        texture_records[name] = {
            "relative_path": matches[0].relative_to(package_root).as_posix(),
            "sha256": sha256_file(matches[0]),
            "width": texture.width,
            "height": texture.height,
        }
    allowed_json = _PACKAGE_ALLOWED_FILES | {"source-manifest.json", "job-manifest.json"}
    extra_json = [
        path.relative_to(package_root).as_posix()
        for path in files if path.suffix.casefold() == ".json"
        and path.name.casefold() not in {name.casefold() for name in allowed_json}
    ]
    if extra_json:
        raise SourceCookerError("runtime package contains unrecognized JSON: " + ", ".join(extra_json))
    return {
        "schema_version": 1,
        "status": "PASS",
        "policy": "CACHE_ONLY_PACKAGE",
        "family": family or package_root.name,
        "models": role_models,
        "required_texture_count": len(required_textures),
        "textures": texture_records,
        "authoring_files": [],
        "file_count": len(files),
    }


def build_runtime_package(
    model_inputs: Mapping[str, Path],
    texture_source_root: Path,
    output_root: Path,
    *,
    family: str,
    model_strategy: str = "auto",
    texture_strategy: str = "auto",
    source_inventory: VehicleSourceInventory | None = None,
    runtime_evidence: Mapping[str, str] | None = None,
    determinism: Mapping[str, Any] | None = None,
    source_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate/convert three DX roles and atomically assemble a cache-only package."""
    if set(model_inputs) != set(VEHICLE_ROLES):
        raise SourceCookerError(f"model input roles must be exactly {VEHICLE_ROLES}")
    if not family or family in {".", ".."} or any(char in family for char in "\\/:*?\"<>|"):
        raise SourceCookerError(f"invalid package family: {family!r}")
    requested = model_strategy.casefold()
    if requested == "auto":
        revisions = {}
        for role, path in model_inputs.items():
            data = Path(path).read_bytes()
            revisions[role] = struct.unpack_from("<I", data, 4)[0] if len(data) >= 8 else None
        if all(value == REVISION_131 for value in revisions.values()):
            selected = ModelStrategy.OFFLINE_DX_131_TO_135
        elif all(value == REVISION_135 for value in revisions.values()):
            selected = ModelStrategy.PASS_THROUGH_135
        else:
            raise SourceCookerError(f"package input revisions are mixed or unsupported: {revisions}")
    else:
        try:
            selected = ModelStrategy(requested)
        except ValueError as exc:
            raise SourceCookerError(f"unknown model strategy: {model_strategy}") from exc
    if selected == ModelStrategy.UNSUPPORTED_REV127_CACHE_ONLY:
        raise SourceCookerError("revision-127 cache-only inputs are unsupported")

    outputs: dict[str, bytes] = {}
    reports: dict[str, dict[str, Any]] = {}
    parsed_models = {}
    texture_refs: set[str] = set()
    source_records = {}
    for role in VEHICLE_ROLES:
        source_path = Path(model_inputs[role]).resolve()
        data = source_path.read_bytes()
        cooked, report, model = _model_validation(data, str(source_path), selected)
        outputs[role] = cooked
        reports[role] = report
        parsed_models[role] = model
        texture_refs.update(
            slot.value for draw in model.physical_draws for slot in draw.texture_slots
            if slot.value.strip().casefold() != "null"
        )
        source_records[role] = {
            "source_filename": source_path.name,
            "source_size": len(data),
            "source_sha256": _sha256(data),
            "source_revision": struct.unpack_from("<I", data, 4)[0],
            "output_filename": f"{role}.dx",
            "output_size": len(cooked),
            "output_sha256": _sha256(cooked),
            "output_revision": REVISION_135,
            "validation": {
                "status": report["status"],
                "policy": report.get("policy"),
                "adapter": report.get("adapter"),
                "draw_count": report.get("draw_count"),
                "vertex_count": report.get("vertex_count"),
                "triangle_count": report.get("triangle_count"),
                "collision_tags": report.get("collision_tags"),
                "collision_validation": report["collision_validation"],
            },
        }

    textures = build_texture_assets(texture_source_root, sorted(texture_refs), texture_strategy)
    final = Path(output_root).resolve()
    if final.exists():
        raise SourceCookerError(f"output path already exists; refusing overwrite: {final}")
    final.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{final.name}.tmp-", dir=final.parent))
    try:
        for role, data in outputs.items():
            (temporary / f"{role}.dx").write_bytes(data)
        for asset in textures:
            (temporary / asset.output_filename).write_bytes(asset.data)
        source_files = {}
        for role in VEHICLE_ROLES:
            input_path = Path(model_inputs[role]).resolve()
            source_record = None
            if source_inventory:
                try:
                    input_relative = input_path.relative_to(source_inventory.source_root).as_posix()
                except ValueError:
                    input_relative = None
                for extension in (input_path.suffix.casefold(), ".dx", ".gxm"):
                    candidate = source_inventory.role_files[role].get(extension)
                    if candidate and candidate["relative_path"] == input_relative:
                        source_record = candidate
                        break
            source_files[role] = {
                "relative_path": source_record["relative_path"] if source_record else input_path.name,
                "kind": input_path.suffix.casefold().lstrip("."),
                "sha256": source_records[role]["source_sha256"],
                "size": source_records[role]["source_size"],
            }
        manifest = {
            "schema_version": 1,
            "tool": "Master Rallye Source Cooker",
            "tool_version": __version__,
            "family": family,
            "model_strategy": selected.value,
            "texture_strategy_requested": texture_strategy,
            "source_files": source_files,
            "source_provenance": dict(source_provenance or {}),
            "model_outputs": source_records,
            "texture_outputs": [asset.to_dict() for asset in textures],
            "runtime_evidence": dict(runtime_evidence or {
                "DETERMINISTIC_COOK_CONFIRMED": "NOT_ASSESSED",
                "CACHE_ONLY_PORTABLE": "STATICALLY_VALIDATED",
                "GAMEPLAY_RUNTIME_CONFIRMED": "NOT_ASSESSED",
            }),
            "determinism": dict(determinism or {"status": "NOT_ASSESSED"}),
            "validation_status": build_validation_status(
                FORMAT_VALIDATED="PASS",
                TEXTURES_RESOLVED="PASS",
                COLLISION_STRUCTURALLY_VALID=(
                    "PASS" if all(item["validation"]["collision_validation"]["status"] == "PASS"
                                  for item in source_records.values()) else "FAIL"
                ),
                DETERMINISTIC_COOK_CONFIRMED=dict(determinism or {}).get("status", "NOT_ASSESSED"),
                CACHE_ONLY_PORTABLE=dict(runtime_evidence or {}).get("CACHE_ONLY_PORTABLE", "STATICALLY_VALIDATED"),
                GAMEPLAY_RUNTIME_CONFIRMED=dict(runtime_evidence or {}).get(
                    "GAMEPLAY_RUNTIME_CONFIRMED", "NOT_ASSESSED",
                ),
            ),
        }
        report = {
            "schema_version": 1,
            "status": "PASS",
            "model_roles": reports,
            "texture_count": len(textures),
            "texture_strategy_counts": {
                policy: sum(item.strategy == policy for item in textures)
                for policy in sorted({item.strategy for item in textures})
            },
        }
        write_json(temporary / "package-manifest.json", manifest)
        write_json(temporary / "validation-report.json", report)
        package_validation = validate_cache_only_package(temporary, family)
        if package_validation["status"] != "PASS":
            raise SourceCookerError("assembled package failed cache-only validation")
        os.replace(temporary, final)
        return {
            "status": "PASS",
            "package_root": str(final),
            "manifest": manifest,
            "validation_report": report,
            "cache_only_validation": package_validation,
        }
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceCookerError(f"cannot read JSON manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SourceCookerError(f"manifest must contain a JSON object: {path}")
    return data


def _copytree_reject_reparse(source: Path, target: Path) -> None:
    source = Path(source).resolve()
    if not source.is_dir():
        raise SourceCookerError(f"runtime template is not a directory: {source}")
    for path in source.rglob("*"):
        if _is_reparse_or_symlink(path):
            raise SourceCookerError(f"runtime template contains a symlink/Junction: {path}")
    shutil.copytree(source, target, copy_function=shutil.copy2)


def _all_gxm_texture_references(inventory: VehicleSourceInventory) -> list[str]:
    refs: set[str] = set()
    for role in VEHICLE_ROLES:
        path = _role_path(inventory, role, ".gxm")
        if path is None:
            raise SourceCookerError(f"missing {role}.gxm")
        probe = _probe_gxm(path)
        if probe["status"] != "PASS_SUPPORTED_PREFIX":
            raise SourceCookerError(f"{role}.gxm source prefix is unsupported")
        refs.update(probe["texture_references"])
    return sorted(refs, key=str.casefold)


def prepare_native_gxm_job(
    source_root: Path,
    family: str,
    runtime_template: Path,
    job_root: Path,
    *,
    runtime_family: str | None = None,
    texture_strategy: str = "auto",
) -> dict[str, Any]:
    """Create a fresh isolated human-cook job from the one verified harness.
    No game process is launched and no historical Junction is created here.
    """
    inventory = inventory_vehicle_source(source_root, family)
    decision = select_model_strategy(inventory, ModelStrategy.RETAIL_NATIVE_GXM.value)
    discovery = discover_embedded_authoring_paths(
        inventory.source_root,
        {role: _role_path(inventory, role, ".gxm") for role in VEHICLE_ROLES},
    )
    if discovery["status"] != "PASS":
        raise SourceCookerError(f"embedded authoring GXI references unresolved: {discovery['unresolved']}")
    texture_refs = _all_gxm_texture_references(inventory)
    planned_textures = build_texture_assets(inventory.source_root, texture_refs, texture_strategy)

    template = Path(runtime_template).resolve()
    exe = template / "MRallye.exe"
    archive = template / "Data.sma"
    if not exe.is_file() or sha256_file(exe) != SUPPORTED_COOK_HARNESS_EXE_SHA256:
        raise SourceCookerError(
            "runtime template must use the verified isolated ID26/T1 cook harness "
            f"(MRallye.exe SHA256 {SUPPORTED_COOK_HARNESS_EXE_SHA256})"
        )
    if not archive.is_file() or sha256_file(archive) != SUPPORTED_RETAIL_DATA_SMA_SHA256:
        raise SourceCookerError(
            "runtime template Data.sma does not match the verified retail archive "
            f"SHA256 {SUPPORTED_RETAIL_DATA_SMA_SHA256}"
        )
    job = Path(job_root).resolve()
    for guarded in (inventory.source_root, template):
        if job == guarded or job in guarded.parents or guarded in job.parents:
            raise SourceCookerError("job directory must be separate from source and runtime template")
    if job.exists():
        raise SourceCookerError(f"job directory already exists; refusing overwrite: {job}")

    gxm_files = {
        role: _role_path(inventory, role, ".gxm").read_bytes()
        for role in VEHICLE_ROLES
    }
    source_hashes = {
        role: _sha256(data) for role, data in gxm_files.items()
    }
    job_id = _sha256(json.dumps({
        "family": inventory.family,
        "runtime_family": runtime_family or inventory.family,
        "gxm_sha256": source_hashes,
        "texture_policy": texture_strategy,
        "tool_version": __version__,
    }, sort_keys=True).encode("utf-8"))[:20]
    runtime_family_name = runtime_family or inventory.family
    if not runtime_family_name or any(char in runtime_family_name for char in "\\/:*?\"<>|"):
        raise SourceCookerError(f"invalid temporary runtime family: {runtime_family_name!r}")

    job.mkdir(parents=True)
    try:
        mirror = job / "authoring-root"
        copied_authoring = materialize_authoring_mirror(inventory.source_root, discovery, mirror)
        runtime = job / "runtime"
        _copytree_reject_reparse(template, runtime)
        asset_dir = runtime / "DataGx" / "Vehicles" / runtime_family_name
        asset_dir.mkdir(parents=True, exist_ok=True)
        managed_extensions = {".dx", ".dxt", ".gxm", ".gxi"}
        for path in asset_dir.iterdir():
            if path.is_file() and path.suffix.casefold() in managed_extensions:
                path.unlink()
            elif path.is_dir() and _is_reparse_or_symlink(path):
                raise SourceCookerError(f"runtime vehicle directory contains a reparse point: {path}")
        for role in VEHICLE_ROLES:
            source_path = _role_path(inventory, role, ".gxm")
            destination = asset_dir / f"{role}.gxm"
            shutil.copyfile(source_path, destination)
            if sha256_file(destination) != source_hashes[role]:
                raise SourceCookerError(f"staged GXM hash mismatch for {role}")
        for asset in planned_textures:
            (asset_dir / asset.output_filename).write_bytes(asset.data)
        if any((asset_dir / f"{role}.dx").exists() for role in VEHICLE_ROLES):
            raise SourceCookerError("pre-cook runtime still contains one or more DX outputs")

        bridge_mappings = []
        mirror_by_root = {
            row["historical_root"].casefold(): mirror / row["mirror_id"]
            for row in discovery["historical_roots"]
        }
        for row in discovery["historical_roots"]:
            bridge_mappings.append({
                "link_path": row["historical_root"],
                "target": str(mirror_by_root[row["historical_root"].casefold()]),
            })
        ownership = write_guarded_junction_scripts(
            bridge_mappings,
            job_id=job_id,
            ownership_manifest=job / "junction-ownership.json",
            setup_script=job / "SetupAuthoringBridge.ps1",
            cleanup_script=job / "RemoveAuthoringBridge.ps1",
        )
        source_manifest = inventory.to_dict()
        source_manifest["source_root_label"] = inventory.source_root.name
        source_manifest["source_root"] = "<local source path omitted from portable package>"
        write_json(job / "source-manifest.json", source_manifest)
        write_json(job / "embedded-authoring-paths.json", discovery)

        manifest = {
            "schema_version": 1,
            "phase": "R-COOKER3",
            "job_id": job_id,
            "tool_version": __version__,
            "status": "PREPARED_FOR_HUMAN_NATIVE_COOK",
            "source_family": inventory.family,
            "runtime_family": runtime_family_name,
            "source_manifest": "source-manifest.json",
            "source_root": str(inventory.source_root),
            "runtime_template": str(template),
            "runtime_root": "runtime",
            "retail_build_exe_sha256": SUPPORTED_RETAIL_EXE_SHA256,
            "runtime_harness_exe_sha256": sha256_file(runtime / "MRallye.exe"),
            "retail_data_sma_sha256": sha256_file(runtime / "Data.sma"),
            "model_strategy": decision.to_dict(),
            "texture_strategy_requested": texture_strategy,
            "texture_outputs": [asset.to_dict() for asset in planned_textures],
            "gxm_sources": {
                role: {
                    "relative_path": inventory.role_files[role][".gxm"]["relative_path"],
                    "sha256": source_hashes[role],
                    "size": len(gxm_files[role]),
                    "staged_name": f"{role}.gxm",
                }
                for role in VEHICLE_ROLES
            },
            "authoring_reference_count": len(discovery["references"]),
            "authoring_gxi_count": len(copied_authoring),
            "junction_ownership_manifest": "junction-ownership.json",
            "outputs": {
                role: {"path": f"runtime/DataGx/Vehicles/{runtime_family_name}/{role}.dx", "status": "MISSING_EXPECTED_BEFORE_COOK"}
                for role in VEHICLE_ROLES
            },
            "validation_status": build_validation_status(
                FORMAT_VALIDATED="PENDING_NATIVE_COOK",
                TEXTURES_RESOLVED="PASS",
                COLLISION_STRUCTURALLY_VALID="PENDING_NATIVE_COOK",
                DETERMINISTIC_COOK_CONFIRMED="NOT_ASSESSED_BY_THIS_JOB",
            ),
            "runtime_evidence": {
                "harness_profile": "existing ID26 / T1 local7 isolated cook harness",
                "launch_performed_by_tool": False,
            },
        }
        write_json(job / "job-manifest.json", manifest)
        instructions = _human_cook_instructions(job, manifest)
        (job / "HUMAN_COOK_INSTRUCTIONS.txt").write_text(instructions, encoding="utf-8")
        return {
            "status": manifest["status"],
            "job_id": job_id,
            "job_root": str(job),
            "manifest": manifest,
            "authoring_discovery": discovery,
            "package_ready": False,
            "reason": "native retail GXM cook is pending the operator's isolated runtime load",
        }
    except Exception:
        shutil.rmtree(job, ignore_errors=True)
        raise


def _human_cook_instructions(job_root: Path, manifest: Mapping[str, Any]) -> str:
    runtime = (Path(job_root) / "runtime").resolve()
    family_path = f"DataGx/Vehicles/{manifest['runtime_family']}"
    return f"""MASTER RALLYE SOURCE COOKER — HUMAN NATIVE GXM COOK

Job: {manifest['job_id']}
Source family: {manifest['source_family']}
Temporary runtime family: {manifest['runtime_family']}

The job is an isolated copy of the verified retail cook harness. The tool did
not launch the game and did not create any historical Junction.

1. Review the job manifest and source-manifest.json.
2. In a PowerShell window, run:
   & '{Path(job_root) / 'SetupAuthoringBridge.ps1'}'
   The helper creates only Junctions listed in junction-ownership.json. It
   stops for a real directory, an unknown reparse point, an ownership mismatch,
   or a target mismatch.
3. Launch the copied runtime only, with its working directory set to:
   '{runtime}'
   Executable: '{runtime / 'MRallye.exe'}'
4. Use the established isolated harness profile (ID26 / T1 local7). Load the
   frontend preview to cook complete.gxm. Enter Practice/Quick Race to cook
   car.gxm and wheel.gxm. Do not cook in the canonical retail installation.
5. Confirm the three expected cache outputs exist:
   {runtime / family_path / 'complete.dx'}
   {runtime / family_path / 'car.dx'}
   {runtime / family_path / 'wheel.dx'}
6. Collect and validate them with:
   python -m master_rallye.source_cooker collect --job '{Path(job_root)}' --output '{Path(job_root) / 'runtime-package'}'
7. Close the game, then run:
   & '{Path(job_root) / 'RemoveAuthoringBridge.ps1'}'

The cleanup helper removes only a Junction still matching this job's
ownership manifest and exact target. It never recursively deletes a target.
Textures are pre-staged under the selected texture policy; this runtime path
does not rely on the ordinary cache-miss path regenerating DXT from GXI.
"""


def collect_native_cook_job(job_root: Path, output_root: Path) -> dict[str, Any]:
    job = Path(job_root).resolve()
    manifest_path = job / "job-manifest.json"
    manifest = _load_json(manifest_path)
    if manifest.get("phase") != "R-COOKER3" or manifest.get("status") not in {
        "PREPARED_FOR_HUMAN_NATIVE_COOK", "NATIVE_OUTPUTS_COLLECTED",
    }:
        raise SourceCookerError("job manifest is not a prepared R-COOKER3 native-cook job")
    runtime = job / manifest["runtime_root"]
    asset_dir = runtime / "DataGx" / "Vehicles" / manifest["runtime_family"]
    role_paths = {role: asset_dir / f"{role}.dx" for role in VEHICLE_ROLES}
    missing = [str(path) for path in role_paths.values() if not path.is_file()]
    if missing:
        raise SourceCookerError("native cook outputs are missing: " + ", ".join(missing))
    # Native output texture closure is resolved against the runtime cache directory.
    gxm_sources = manifest.get("gxm_sources", {})
    result = build_runtime_package(
        role_paths,
        asset_dir,
        output_root,
        family=manifest["source_family"],
        model_strategy=ModelStrategy.RETAIL_NATIVE_GXM.value,
        texture_strategy="reuse-valid-dxt",
        runtime_evidence={
            "DETERMINISTIC_COOK_CONFIRMED": "NOT_ASSESSED_FOR_THIS_JOB",
            "CACHE_ONLY_PORTABLE": "STATICALLY_VALIDATED",
            "GAMEPLAY_RUNTIME_CONFIRMED": "NOT_ASSESSED_FOR_THIS_JOB",
        },
        source_provenance={
            "native_cook_job_id": manifest["job_id"],
            "source_family": manifest["source_family"],
            "runtime_family": manifest["runtime_family"],
            "retail_build_exe_sha256": manifest["retail_build_exe_sha256"],
            "cook_harness_exe_sha256": manifest["runtime_harness_exe_sha256"],
            "source_gxm": {
                role: {
                    "relative_path": row["relative_path"],
                    "sha256": row["sha256"],
                    "size": row["size"],
                }
                for role, row in gxm_sources.items()
            },
        },
    )
    manifest["status"] = "NATIVE_OUTPUTS_COLLECTED"
    manifest["outputs"] = {
        role: {
            "path": f"runtime/DataGx/Vehicles/{manifest['runtime_family']}/{role}.dx",
            "size": role_paths[role].stat().st_size,
            "sha256": sha256_file(role_paths[role]),
            "revision": REVISION_135,
            "validation_status": result["manifest"]["model_outputs"][role]["validation"]["status"],
        }
        for role in VEHICLE_ROLES
    }
    manifest["package_root"] = str(Path(output_root).resolve())
    manifest["validation_status"] = build_validation_status(
        FORMAT_VALIDATED="PASS",
        TEXTURES_RESOLVED="PASS",
        COLLISION_STRUCTURALLY_VALID="PASS",
        DETERMINISTIC_COOK_CONFIRMED="NOT_ASSESSED_BY_COLLECT",
        CACHE_ONLY_PORTABLE="STATICALLY_VALIDATED",
        GAMEPLAY_RUNTIME_CONFIRMED="NOT_ASSESSED_BY_COLLECT",
    )
    write_json(manifest_path, manifest)
    return result


def _write_cli_json(value: Mapping[str, Any], path: Path | None = None) -> None:
    serialized = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
    if path:
        write_json(path, value)
    else:
        print(serialized)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m master_rallye.source_cooker",
        description="Master Rallye Source Cooker - source inventory, safe cook orchestration and package validation.",
    )
    parser.add_argument("--version", action="version", version=f"Master Rallye Source Cooker {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    inventory = commands.add_parser("inventory", help="hash and validate known vehicle source files")
    inventory.add_argument("--source", required=True, type=Path)
    inventory.add_argument("--family")
    inventory.add_argument("--json", type=Path)

    vehicle = commands.add_parser("vehicle", help="select a model strategy and prepare or build a runtime package")
    vehicle.add_argument("--source", required=True, type=Path)
    vehicle.add_argument("--family", required=True)
    vehicle.add_argument("--output", required=True, type=Path)
    vehicle.add_argument("--retail-root", "--runtime-template", dest="runtime_template", type=Path,
                         help="isolated, verified ID26 cook-harness template; never point at the canonical install")
    vehicle.add_argument("--runtime-family", help="temporary harness family namespace; defaults to --family")
    vehicle.add_argument("--model-strategy", default="auto", choices=_MODEL_STRATEGY_CHOICES)
    vehicle.add_argument("--texture-strategy", default="auto", choices=[item.value for item in TextureStrategy])

    collect = commands.add_parser("collect", help="validate native DX cooked in a prepared isolated job")
    collect.add_argument("--job", required=True, type=Path)
    collect.add_argument("--output", required=True, type=Path)

    validate = commands.add_parser("validate-package", help="check a portable cache-only DX/DXT package")
    validate.add_argument("package", type=Path)
    validate.add_argument("--family")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            inventory = inventory_vehicle_source(args.source, args.family)
            _write_cli_json(inventory.to_dict(), args.json)
            return 0
        if args.command == "vehicle":
            inventory = inventory_vehicle_source(args.source, args.family)
            decision = select_model_strategy(inventory, args.model_strategy)
            if decision.selected == ModelStrategy.UNSUPPORTED_REV127_CACHE_ONLY:
                raise SourceCookerError(decision.reason)
            if decision.selected == ModelStrategy.RETAIL_NATIVE_GXM:
                if args.runtime_template is None:
                    raise SourceCookerError(
                        "retail-native GXM requires --retail-root pointing to a separate verified cook-harness copy"
                    )
                result = prepare_native_gxm_job(
                    args.source, args.family, args.runtime_template, args.output,
                    runtime_family=args.runtime_family, texture_strategy=args.texture_strategy,
                )
            else:
                role_paths = {role: _role_path(inventory, role, ".dx") for role in VEHICLE_ROLES}
                if any(path is None for path in role_paths.values()):
                    raise SourceCookerError("selected DX strategy has a missing model role")
                result = build_runtime_package(
                    role_paths,
                    inventory.source_root,
                    args.output,
                    family=args.family,
                    model_strategy=decision.selected.value,
                    texture_strategy=args.texture_strategy,
                    source_inventory=inventory,
                )
            _write_cli_json({**result, "model_strategy": decision.to_dict()})
            return 0
        if args.command == "collect":
            result = collect_native_cook_job(args.job, args.output)
            _write_cli_json(result)
            return 0
        if args.command == "validate-package":
            _write_cli_json(validate_cache_only_package(args.package, args.family))
            return 0
    except (SourceCookerError, AuthoringPathError, DxRevisionUpgradeError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
