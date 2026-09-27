"""Read-only retail vehicle-family, config, and model-resource inventory."""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .vehicle_config_analysis import VehicleConfigDocument
from .vehicle_family_broker import (
    FAMILY_BY_TYPE_ID,
    PLAYER_MODIFICATION_FIELDS,
)
from .vehicle_config_schema import FIXED_BASE_GROUP_COUNTS, analyze_vehicle_base_schema
from .vehicle_physics_binding import RETAIL_FAMILY_CATALOG
from .vehicle_packaging import normalize_sma_member_name


MODEL_RESOURCES = ("car.dx", "complete.dx", "wheel.dx")
WHEELLESS_DESIGNED_FAMILIES = frozenset({"ufo"})


def inventory_vehicle_model_packages(
    archive_members: Iterable[str],
    loose_vehicles_root: Path,
) -> dict[str, dict[str, Any]]:
    """Merge Data.sma and loose vehicle files using Windows lookup precedence.

    The returned mapping is keyed by ``family.casefold()``. A loose file with
    the same family-relative path overrides its archive counterpart, while
    other resources continue to fall through to Data.sma.
    """
    archive_files: dict[str, dict[str, list[str]]] = {}
    archive_names: dict[str, set[str]] = {}
    for raw_name in archive_members:
        name, is_directory = normalize_sma_member_name(raw_name)
        if is_directory:
            continue
        parts = PurePosixPath(name).parts
        if len(parts) < 4 or parts[0].casefold() != "datagx" or parts[1].casefold() != "vehicles":
            continue
        family = parts[2]
        key = family.casefold()
        relative = "/".join(parts[3:])
        archive_files.setdefault(key, {}).setdefault(relative.casefold(), []).append(relative)
        archive_names.setdefault(key, set()).add(family)

    loose_root = Path(loose_vehicles_root)
    loose_files: dict[str, dict[str, list[Path]]] = {}
    loose_names: dict[str, set[str]] = {}
    if loose_root.is_dir():
        for directory, dirnames, filenames in os.walk(loose_root, followlinks=False):
            current = Path(directory)
            if current == loose_root:
                dirnames[:] = sorted(dirnames, key=str.casefold)
                for family in dirnames:
                    loose_names.setdefault(family.casefold(), set()).add(family)
            try:
                relative_directory = current.relative_to(loose_root)
            except ValueError:
                dirnames[:] = []
                continue
            if not relative_directory.parts:
                continue
            family = relative_directory.parts[0]
            key = family.casefold()
            loose_names.setdefault(key, set()).add(family)
            for filename in filenames:
                path = current / filename
                if path.is_file():
                    relative = path.relative_to(loose_root / family).as_posix()
                    loose_files.setdefault(key, {}).setdefault(relative.casefold(), []).append(path)
            dirnames[:] = sorted(dirnames, key=str.casefold)

    result: dict[str, dict[str, Any]] = {}
    for key in sorted(set(archive_files) | set(loose_files)):
        archive_by_path = archive_files.get(key, {})
        loose_by_path = loose_files.get(key, {})
        archive_count = sum(len(items) for items in archive_by_path.values())
        loose_count = sum(len(items) for items in loose_by_path.values())
        archive_present = archive_count > 0
        loose_present = loose_count > 0
        if archive_present and loose_present:
            provenance = "DATA_SMA+LOOSE"
        elif loose_present:
            provenance = "LOOSE_OVERRIDE"
        elif archive_present:
            provenance = "DATA_SMA"
        else:
            provenance = "MISSING"

        resource_sources: dict[str, str] = {}
        ambiguous_resources: list[str] = []
        for resource in MODEL_RESOURCES:
            archive_hits = archive_by_path.get(resource, [])
            loose_hits = loose_by_path.get(resource, [])
            if len(loose_hits) > 1 or (not loose_hits and len(archive_hits) > 1):
                resource_sources[resource] = "AMBIGUOUS"
                ambiguous_resources.append(resource)
            elif loose_hits:
                resource_sources[resource] = "LOOSE_OVERRIDE"
            elif archive_hits:
                resource_sources[resource] = "DATA_SMA"
            else:
                resource_sources[resource] = "MISSING"

        family_names = sorted(archive_names.get(key, set()) | loose_names.get(key, set()),
                              key=lambda name: (name.casefold(), name))
        case_collision = (
            len(archive_names.get(key, set())) > 1
            or len(loose_names.get(key, set())) > 1
        )
        required = ["car.dx", "complete.dx"]
        is_wheel_less = key in WHEELLESS_DESIGNED_FAMILIES
        if not is_wheel_less:
            required.append("wheel.dx")
        missing = [name for name in required if resource_sources[name] == "MISSING"]
        if ambiguous_resources or case_collision:
            status = "AMBIGUOUS_CASE_COLLISION"
        elif missing:
            status = "INCOMPLETE" if archive_present or loose_present else "MISSING"
        elif is_wheel_less and resource_sources["wheel.dx"] == "MISSING":
            status = "COMPLETE_WHEELLESS"
        else:
            status = "COMPLETE"

        effective_resources = {
            name: {
                "source": resource_sources[name],
                "present": resource_sources[name] in {"DATA_SMA", "LOOSE_OVERRIDE"},
            }
            for name in MODEL_RESOURCES
        }
        result[key] = {
            "family_names": family_names,
            "provenance": provenance,
            "status": status,
            "wheelless_by_design": is_wheel_less,
            "required_resources": required,
            "missing_resources": missing,
            "ambiguous_resources": ambiguous_resources,
            "resources": effective_resources,
            "archive_file_count": archive_count,
            "loose_file_count": loose_count,
        }
    return result


def _player1_overlay_status(document: VehicleConfigDocument, family: str) -> dict[str, Any]:
    values = document.families.get(family, {})
    prefix = "Player1/Modifications/"
    rows = {
        path.removeprefix(prefix): row
        for path, row in values.items()
        if path.startswith(prefix)
    }
    expected = set(PLAYER_MODIFICATION_FIELDS)
    actual = set(rows)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    wrong_type = sorted(name for name in actual & expected if rows[name]["type"] != "Float")
    complete = not missing and not unexpected and not wrong_type
    return {
        "status": "COMPLETE" if complete else (
            "TYPE_MISMATCH" if wrong_type else "INCOMPLETE"
        ),
        "field_count": len(actual),
        "expected_field_count": len(expected),
        "missing_fields": missing,
        "unexpected_fields": unexpected,
        "wrong_type_fields": wrong_type,
    }


def build_vehicle_family_inventory(
    vehicle_config: VehicleConfigDocument,
    modifications_config: VehicleConfigDocument,
    model_packages: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge all named config families with model-only families such as forklift."""
    display_names = list(vehicle_config.families)
    config_keys = {name.casefold() for name in display_names}
    for key, package in model_packages.items():
        if key not in config_keys:
            display_names.append(package["family_names"][0])
            config_keys.add(key)

    type_ids: dict[str, list[int]] = {}
    for type_id, family in enumerate(FAMILY_BY_TYPE_ID):
        type_ids.setdefault(family.casefold(), []).append(type_id)

    rows: list[dict[str, Any]] = []
    config_variant_counts: dict[str, int] = {}
    for config_name in vehicle_config.families:
        folded = config_name.casefold()
        config_variant_counts[folded] = config_variant_counts.get(folded, 0) + 1

    for name in sorted(display_names, key=lambda item: (item.casefold(), item)):
        key = name.casefold()
        config_values = vehicle_config.families.get(name)
        schema_audit = analyze_vehicle_base_schema(config_values or {})
        group_counts = schema_audit.group_counts
        if config_variant_counts.get(key, 0) > 1:
            base_status = "AMBIGUOUS_CASE_COLLISION"
        elif config_values is None:
            base_status = "MISSING"
        else:
            base_status = schema_audit.compatibility_class

        overlay = _player1_overlay_status(modifications_config, name)
        if config_values is None and overlay["field_count"] == 0:
            overlay["status"] = "MISSING"
        package = model_packages.get(key, {
            "family_names": [], "provenance": "MISSING", "status": "MISSING",
            "wheelless_by_design": key in WHEELLESS_DESIGNED_FAMILIES,
            "required_resources": ["car.dx", "complete.dx"] + (
                [] if key in WHEELLESS_DESIGNED_FAMILIES else ["wheel.dx"]
            ),
            "missing_resources": ["car.dx", "complete.dx"] + (
                [] if key in WHEELLESS_DESIGNED_FAMILIES else ["wheel.dx"]
            ),
            "ambiguous_resources": [],
            "resources": {resource: {"source": "MISSING", "present": False}
                          for resource in MODEL_RESOURCES},
            "archive_file_count": 0,
            "loose_file_count": 0,
        })
        rows.append({
            "family": name,
            "identity_kind": (
                "CONFIG_CASE_COLLISION" if config_variant_counts.get(key, 0) > 1
                else "CONFIG_AND_MODEL" if config_values is not None and package["provenance"] != "MISSING"
                else "CONFIG_ONLY" if config_values is not None
                else "MODEL_ONLY"
            ),
            "type_ids": type_ids.get(key, []),
            "base_config": {
                "status": base_status,
                "compatibility_class": base_status,
                "field_count": len(config_values) if config_values is not None else 0,
                "group_counts": group_counts,
                "fixed_fields_expected": (
                    schema_audit.fixed_fields_expected if config_values is not None
                    else sum(FIXED_BASE_GROUP_COUNTS.values())
                ),
                "fixed_fields_present": schema_audit.fixed_fields_present if config_values is not None else 0,
                "missing_groups": sorted({
                    path.split("/", 1)[0]
                    for path in schema_audit.missing_paths
                    if path.split("/", 1)[0] in FIXED_BASE_GROUP_COUNTS
                }),
                "schema_audit": schema_audit.to_dict() if config_values is not None else None,
            },
            "player1_modifications": overlay,
            "model": package,
        })
    return rows


def select_family_row(rows: list[dict[str, Any]], selection: str) -> dict[str, Any]:
    """Resolve a displayed 1-based row number or an exact family name."""
    value = selection.strip().strip('"').strip("'")
    if not value:
        raise ValueError("select a family by row number or name")
    if value.isdecimal():
        index = int(value)
        if 1 <= index <= len(rows):
            return rows[index - 1]
        raise ValueError(f"family selection {value!r} is outside 1..{len(rows)}")
    matches = [row for row in rows if row["family"].casefold() == value.casefold()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"family name {value!r} is ambiguous by case")
    raise ValueError(f"unknown family selection: {value!r}")


def select_retail_carrier(selection: str) -> Any:
    """Resolve only a type ID/name from the initialized retail type catalog."""
    value = selection.strip().strip('"').strip("'")
    if not value:
        raise ValueError("select a retail carrier by type ID or name")
    if value.isdecimal():
        type_id = int(value)
        matches = [entry for entry in RETAIL_FAMILY_CATALOG if entry.type_id == type_id]
    else:
        matches = [entry for entry in RETAIL_FAMILY_CATALOG
                   if entry.family.casefold() == value.casefold()]
    if len(matches) != 1:
        raise ValueError(f"unknown retail carrier selection: {value!r}")
    return matches[0]
