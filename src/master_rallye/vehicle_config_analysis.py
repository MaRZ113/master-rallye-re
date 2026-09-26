"""Read-only vehicle-config, model-folder, and cross-build comparison helpers.

This module treats every corpus as an independently identified input. It does
not equate spelling variants (for example, Rav4 and NewRav), write XML, or
infer physics semantics from a field name alone.
"""
from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .errors import FormatError


RETAIL_CONFIG_FAMILY_EXCLUSIONS = frozenset({"Tyres"})
NUMERIC_RUNTIME_FAMILY = re.compile(r"^Car\d+$", re.IGNORECASE)

STATIC_RUNTIME_READERS: dict[str, dict[str, str]] = {
    "Dimensions/WheelBase": {
        "status": "READ_BY_RETAIL_SPLINE_AI_PATH",
        "evidence": "Retail 0x004bc590 formats Vehicles/Car%d/Dimensions/WheelBase; its only direct caller is the gaVehicleSplineRecordAI constructor at 0x004c0b20. This proves a spline-record path, not the general physics binding.",
    },
    "Dimensions/TrackWidthFront": {
        "status": "READ_BY_RETAIL_SPLINE_AI_PATH",
        "evidence": "Retail 0x004bc590 formats Vehicles/Car%d/Dimensions/TrackWidthFront; its only direct caller is the gaVehicleSplineRecordAI constructor at 0x004c0b20. This proves a spline-record path, not the general physics binding.",
    },
    "Dimensions/TrackWidthRear": {
        "status": "READ_BY_RETAIL_SPLINE_AI_PATH",
        "evidence": "Retail 0x004bc590 formats Vehicles/Car%d/Dimensions/TrackWidthRear; its only direct caller is the gaVehicleSplineRecordAI constructor at 0x004c0b20. This proves a spline-record path, not the general physics binding.",
    },
    "Suspension/Front/RideHeight": {
        "status": "READ_BY_RETAIL_SPLINE_AI_PATH",
        "evidence": "Retail 0x004bc590 formats Vehicles/Car%d/Suspension/Front/RideHeight; its only direct caller is the gaVehicleSplineRecordAI constructor at 0x004c0b20. This proves a spline-record path, not the general physics binding.",
    },
    "Suspension/Rear/RideHeight": {
        "status": "READ_BY_RETAIL_SPLINE_AI_PATH",
        "evidence": "Retail 0x004bc590 formats Vehicles/Car%d/Suspension/Rear/RideHeight; its only direct caller is the gaVehicleSplineRecordAI constructor at 0x004c0b20. This proves a spline-record path, not the general physics binding.",
    },
    "Suspension/Front/MaxDroop": {
        "status": "READ_BY_RETAIL_SPLINE_AI_PATH",
        "evidence": "Retail 0x004bc590 formats Vehicles/Car%d/Suspension/Front/MaxDroop; its only direct caller is the gaVehicleSplineRecordAI constructor at 0x004c0b20. This proves a spline-record path, not the general physics binding.",
    },
}

WHEEL_SOURCE_LINKAGE_STATUS = "UNRESOLVED"
WHEEL_SOURCE_LINKAGE_EVIDENCE = {
    "visual_runtime_path": "Retail gaWheelSplinePlaybackAI reads cached per-car dimensions and builds a wheel model transform in 0x004c00d0.",
    "physical_contact_path": "No matching suspension/contact constructor path was established in this phase.",
    "classification": WHEEL_SOURCE_LINKAGE_STATUS,
}


@dataclass(frozen=True)
class VehicleConfigDocument:
    build: str
    source: str
    sha256: str
    file_size: int
    families: dict[str, dict[str, dict[str, str]]]
    excluded_families: dict[str, dict[str, dict[str, str]]]


def _read_xml(path: Path) -> tuple[bytes, ET.Element]:
    try:
        raw = path.read_bytes()
        root = ET.fromstring(raw)
    except (OSError, ET.ParseError) as exc:
        raise FormatError(f"cannot parse vehicle config {path}: {exc}") from exc
    return raw, root


def parse_vehicle_config(path: Path, *, build: str) -> VehicleConfigDocument:
    """Parse all Vehicles/<family>/<path> Value entries without aliasing roots."""
    if not build:
        raise ValueError("build identity is required")
    raw, root = _read_xml(path)
    families: dict[str, dict[str, dict[str, str]]] = {}
    excluded: dict[str, dict[str, dict[str, str]]] = {}
    seen_names: set[str] = set()
    for node in root.iter("Value"):
        name = node.get("Name")
        if name is None or not name.startswith("Vehicles/"):
            continue
        parts = name.split("/")
        if len(parts) < 3 or any(not part for part in parts[1:]):
            raise FormatError(f"invalid vehicle config path {name!r} in {path}")
        if name in seen_names:
            raise FormatError(f"duplicate vehicle config path {name!r} in {path}")
        seen_names.add(name)
        value_type = node.get("Type")
        value = node.get("Value")
        if value_type is None or value is None:
            raise FormatError(f"vehicle config value {name!r} lacks Type or Value in {path}")
        family = parts[1]
        relative_path = "/".join(parts[2:])
        record = {"type": value_type, "value": value}
        target = excluded if (
            family.casefold() in {item.casefold() for item in RETAIL_CONFIG_FAMILY_EXCLUSIONS}
            or NUMERIC_RUNTIME_FAMILY.fullmatch(family)
        ) else families
        target.setdefault(family, {})[relative_path] = record
    return VehicleConfigDocument(
        build=build,
        source=str(path),
        sha256=hashlib.sha256(raw).hexdigest(),
        file_size=len(raw),
        families=families,
        excluded_families=excluded,
    )


def inventory_vehicle_directories(root: Path) -> list[dict[str, Any]]:
    """Inventory exact top-level vehicle directory names and local resources."""
    if not root.is_dir():
        raise FormatError(f"vehicle directory root does not exist: {root}")
    result: list[dict[str, Any]] = []
    for directory in sorted((item for item in root.iterdir() if item.is_dir()),
                            key=lambda item: (item.name.casefold(), item.name)):
        files = sorted((item for item in directory.rglob("*") if item.is_file()),
                       key=lambda item: item.relative_to(directory).as_posix().casefold())
        relative_files = [item.relative_to(directory).as_posix() for item in files]
        top_level = {item.name.casefold(): item for item in directory.iterdir() if item.is_file()}
        dxt = [name for name in relative_files if Path(name).suffix.casefold() == ".dxt"]
        result.append({
            "name": directory.name,
            "path": str(directory),
            "file_count": len(files),
            "car_dx": top_level.get("car.dx") is not None,
            "complete_dx": top_level.get("complete.dx") is not None,
            "wheel_dx": top_level.get("wheel.dx") is not None,
            "car_gxm": top_level.get("car.gxm") is not None,
            "complete_gxm": top_level.get("complete.gxm") is not None,
            "texture_count_dxt": len(dxt),
            "texture_files_dxt": [name for name in dxt],
            "other_local_files": [
                name for name in relative_files
                if Path(name).suffix.casefold() not in {".dxt", ".dx", ".gxm", ".gxi"}
            ],
            "files": relative_files,
        })
    return result


def classify_config_families_against_directories(
    families: list[str] | tuple[str, ...],
    directories: list[dict[str, Any]] | list[str],
    *,
    possible_aliases: dict[str, tuple[str, ...]] | None = None,
) -> list[dict[str, Any]]:
    """Compare exact and case-insensitive names; aliases are hypotheses only."""
    directory_names = [item if isinstance(item, str) else str(item["name"]) for item in directories]
    folded: dict[str, list[str]] = {}
    for name in directory_names:
        folded.setdefault(name.casefold(), []).append(name)
    aliases = possible_aliases or {}
    result: list[dict[str, Any]] = []
    for family in sorted(set(families), key=lambda item: (item.casefold(), item)):
        if family.casefold() in {item.casefold() for item in RETAIL_CONFIG_FAMILY_EXCLUSIONS}:
            result.append({
                "config_family": family,
                "status": "NON-VEHICLE_CONFIG_FAMILY",
                "exact_directory_match": None,
                "case_insensitive_directory_matches": [],
                "possible_aliases": [],
            })
            continue
        matches = folded.get(family.casefold(), [])
        exact = family if family in directory_names else None
        candidates = list(aliases.get(family, ()))
        if exact is not None:
            status = "MATCHED_EXACT"
        elif matches:
            status = "DIRECTORY_NAME_MISMATCH"
        elif candidates:
            status = "POSSIBLE_ALIAS"
        else:
            status = "EXACT_CONFIG_ONLY"
        result.append({
            "config_family": family,
            "status": status,
            "exact_directory_match": exact,
            "case_insensitive_directory_matches": matches,
            "possible_aliases": candidates,
        })
    return result


def _decimal(value: str) -> Decimal | None:
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def classify_config_subsystem(relative_path: str) -> str:
    """Return the literal first path component, not an inferred physics role."""
    return relative_path.split("/", 1)[0] if relative_path else "UNKNOWN"


def compare_vehicle_configs(
    document_a: VehicleConfigDocument,
    family_a: str,
    document_b: VehicleConfigDocument,
    family_b: str | None = None,
) -> dict[str, Any]:
    """Compare two exact family records while preserving missing/type/value changes."""
    family_b = family_b or family_a
    values_a = _lookup_family(document_a.families, family_a)
    values_b = _lookup_family(document_b.families, family_b)
    rows: list[dict[str, Any]] = []
    for path in sorted(set(values_a) | set(values_b), key=str.casefold):
        a = values_a.get(path)
        b = values_b.get(path)
        if a is None:
            status = "ADDED_IN_B"
        elif b is None:
            status = "REMOVED_IN_B"
        elif a["type"] != b["type"]:
            status = "TYPE_CHANGED"
        else:
            num_a, num_b = _decimal(a["value"]), _decimal(b["value"])
            if a["value"] == b["value"]:
                status = "EXACT_EQUAL"
            elif num_a is not None and num_b is not None and num_a == num_b:
                status = "NUMERIC_EQUAL_TEXT_DIFFERENT"
            else:
                status = "VALUE_CHANGED"
        num_a = _decimal(a["value"]) if a else None
        num_b = _decimal(b["value"]) if b else None
        reader = STATIC_RUNTIME_READERS.get(path, {
            "status": "PRESENT_BUT_USAGE_UNRESOLVED",
            "evidence": "No field-specific retail executable read path has been established in this phase.",
        })
        rows.append({
            "path": path,
            "full_path_a": f"Vehicles/{family_a}/{path}" if a else None,
            "full_path_b": f"Vehicles/{family_b}/{path}" if b else None,
            "subsystem": classify_config_subsystem(path),
            "type_a": a["type"] if a else None,
            "value_a": a["value"] if a else None,
            "type_b": b["type"] if b else None,
            "value_b": b["value"] if b else None,
            "numeric_delta_b_minus_a": str(num_b - num_a) if num_a is not None and num_b is not None else None,
            "status": status,
            "runtime_reader_status": reader["status"],
            "runtime_reader_evidence": reader["evidence"],
        })
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "build_a": document_a.build,
        "source_a": document_a.source,
        "source_sha256_a": document_a.sha256,
        "family_a": family_a,
        "build_b": document_b.build,
        "source_b": document_b.source,
        "source_sha256_b": document_b.sha256,
        "family_b": family_b,
        "field_count": len(rows),
        "status_counts": counts,
        "fields": rows,
    }


def _lookup_family(
    families: dict[str, dict[str, dict[str, str]]], name: str
) -> dict[str, dict[str, str]]:
    if name in families:
        return families[name]
    matches = [key for key in families if key.casefold() == name.casefold()]
    if len(matches) > 1:
        raise FormatError(f"ambiguous case-insensitive vehicle family {name!r}: {matches}")
    return families[matches[0]] if matches else {}


def build_vehicle_schema(documents: list[VehicleConfigDocument]) -> list[dict[str, Any]]:
    """Aggregate field path/type coverage and retain each observed raw value."""
    records: dict[tuple[str, str, str], dict[str, Any]] = {}
    for document in documents:
        for family, values in document.families.items():
            for path, record in values.items():
                full_path = f"Vehicles/{family}/{path}"
                key = (full_path, record["type"], family)
                entry = records.setdefault(key, {
                    "full_path": full_path,
                    "family": family,
                    "relative_path": path,
                    "subsystem": classify_config_subsystem(path),
                    "type": record["type"],
                    "vehicle_coverage": [],
                    "build_coverage": [],
                    "observations": [],
                    "runtime_reader_status": STATIC_RUNTIME_READERS.get(path, {}).get(
                        "status", "PRESENT_BUT_USAGE_UNRESOLVED"),
                })
                if family not in entry["vehicle_coverage"]:
                    entry["vehicle_coverage"].append(family)
                if document.build not in entry["build_coverage"]:
                    entry["build_coverage"].append(document.build)
                entry["observations"].append({
                    "build": document.build,
                    "config_sha256": document.sha256,
                    "value": record["value"],
                })
    return sorted(records.values(), key=lambda item: item["full_path"].casefold())


def config_schema_summary(document: VehicleConfigDocument) -> dict[str, Any]:
    """Summarize literal path groups and value type counts for one build."""
    groups: dict[str, int] = {}
    types: dict[str, int] = {}
    total = 0
    for family, values in document.families.items():
        for path, record in values.items():
            total += 1
            group = f"Vehicles/{family}/{classify_config_subsystem(path)}"
            groups[group] = groups.get(group, 0) + 1
            types[record["type"]] = types.get(record["type"], 0) + 1
    return {
        "build": document.build,
        "source": document.source,
        "sha256": document.sha256,
        "file_size": document.file_size,
        "vehicle_family_count": len(document.families),
        "excluded_family_counts": {key: len(value) for key, value in document.excluded_families.items()},
        "vehicle_value_count": total,
        "type_counts": dict(sorted(types.items())),
        "subsystem_value_counts": dict(sorted(groups.items(), key=lambda item: item[0].casefold())),
    }


def family_value_rows(document: VehicleConfigDocument, family: str) -> list[dict[str, str]]:
    """Return full source-value rows for one family, allowing case-only spelling."""
    values = _lookup_family(document.families, family)
    return [
        {"full_path": f"Vehicles/{family}/{path}", "path": path,
         "type": record["type"], "value": record["value"]}
        for path, record in sorted(values.items(), key=lambda item: item[0].casefold())
    ]


def wheel_spline_playback_local_offset(
    wheel_index: int,
    *,
    wheel_base: float,
    track_width_front: float,
    track_width_rear: float,
    ride_height_front: float,
    ride_height_rear: float,
    front_max_droop: float,
    dynamic_vertical_sample: float,
) -> dict[str, float | str | int]:
    """Reproduce the established local offset selection in retail 0x004c00d0.

    Returned axes are local component names. The surrounding matrix maps them
    into the runtime/world transform. This models the gaWheelSplinePlaybackAI
    path only; it does not claim equivalence with physical contact points.
    """
    if wheel_index not in range(4):
        raise ValueError("wheel_index must be in 0..3")
    front = wheel_index < 2
    side_sign = -1.0 if wheel_index in (0, 2) else 1.0
    axle_sign = 1.0 if front else -1.0
    track = track_width_front if front else track_width_rear
    ride = ride_height_front if front else ride_height_rear
    # The inspected spline playback constructor carries the front MaxDroop
    # field for all four wheel instances; a rear-specific clamp was not read.
    vertical_sample = max(dynamic_vertical_sample, -front_max_droop) - ride
    return {
        "wheel_index": wheel_index,
        "axle": "front" if front else "rear",
        "lateral_side": "negative" if side_sign < 0 else "positive",
        "local_lateral": side_sign * track / 2.0,
        "local_longitudinal": axle_sign * wheel_base / 2.0,
        "local_vertical_component": vertical_sample,
    }
