"""Reader-aware validation for the retail vehicle configuration schema.

The retail base record has 118 fixed path/type pairs, two integer count
headers, and four count-driven Engine arrays.  The fixed map below was taken
from the hash-locked retail Navara schema, with those Engine arrays and count
headers deliberately separated for semantic validation.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping


RETAIL_FIXED_BASE_SCHEMA_ROWS = (
    ("Chassis/AerodynamicDownForceCoeff", "Float"),
    ("Chassis/AerodynamicDragCoeff", "Float"),
    ("Chassis/BrakeTorqueFront", "Float"),
    ("Chassis/BrakeTorqueRear", "Float"),
    ("Chassis/CentreOfGravity", "Vector3"),
    ("Chassis/DragCoeff", "Float"),
    ("Chassis/Gravity", "Float"),
    ("Chassis/HandBrakeTorque", "Float"),
    ("Chassis/MaxAerodynamicDownForceSpeed", "Float"),
    ("Chassis/MinAerodynamicDownForceSpeed", "Float"),
    ("Chassis/MomentOfInertia", "Vector3"),
    ("Chassis/Restitution", "Float"),
    ("Chassis/RollingDrag", "Float"),
    ("Chassis/SlidingFriction", "Float"),
    ("Chassis/TotalMass", "Float"),
    ("Chassis/UseCuboidMOI", "Bool"),
    ("DamageParams/EngineDamageResetScore", "Float"),
    ("DamageParams/EngineDamageStrength", "Float"),
    ("DamageParams/EngineThresholdDamageScore", "Float"),
    ("DamageParams/EngineThresholdDamageSpeed", "Float"),
    ("DamageParams/GearDamageResetScore", "Float"),
    ("DamageParams/GearDamageStrength", "Float"),
    ("DamageParams/GearThresholdDamageScore", "Float"),
    ("DamageParams/GearThresholdDamageSpeed", "Float"),
    ("DamageParams/MaxEngineDamage", "Float"),
    ("DamageParams/MaxGearDamage", "Float"),
    ("DamageParams/MaxSteeringDamage", "Float"),
    ("DamageParams/MaxSuspensionDamage", "Float"),
    ("DamageParams/MaxTyreDamage", "Float"),
    ("DamageParams/SteeringDamageResetScore", "Float"),
    ("DamageParams/SteeringDamageStrength", "Float"),
    ("DamageParams/SteeringThresholdDamageScore", "Float"),
    ("DamageParams/SteeringThresholdDamageSpeed", "Float"),
    ("DamageParams/SuspensionDamageResetScore", "Float"),
    ("DamageParams/SuspensionDamageStrength", "Float"),
    ("DamageParams/SuspensionThresholdDamageScore", "Float"),
    ("DamageParams/SuspensionThresholdDamageSpeed", "Float"),
    ("DamageParams/TyreDamageResetScore", "Float"),
    ("DamageParams/TyreDamageStrength", "Float"),
    ("DamageParams/TyreThresholdDamageScore", "Float"),
    ("DamageParams/TyreThresholdDamageSpeed", "Float"),
    ("Dimensions/Height", "Float"),
    ("Dimensions/Length", "Float"),
    ("Dimensions/TrackWidthFront", "Float"),
    ("Dimensions/TrackWidthRear", "Float"),
    ("Dimensions/WheelBase", "Float"),
    ("Dimensions/WheelRadiusFront", "Float"),
    ("Dimensions/WheelRadiusRear", "Float"),
    ("Dimensions/Width", "Float"),
    ("Engine/AutoGears", "Bool"),
    ("Engine/BrakeBias", "Float"),
    ("Engine/CentreLSDBias", "Float"),
    ("Engine/ClutchSwitchTime", "Int"),
    ("Engine/DriveShaftInertia", "Float"),
    ("Engine/DriveType", "Int"),
    ("Engine/EngineDamping", "Float"),
    ("Engine/EngineInertia", "Float"),
    ("Engine/FrontLSDBias", "Float"),
    ("Engine/GearRatioDiff", "Float"),
    ("Engine/IdleRevs", "Float"),
    ("Engine/LiftOffEngineDamping", "Float"),
    ("Engine/MaxClutchTorque", "Float"),
    ("Engine/PeakTorque", "Float"),
    ("Engine/RearLSDBias", "Float"),
    ("Engine/RevLimit", "Float"),
    ("Steering/MaxSpeed", "Float"),
    ("Steering/MaxSteer", "Float"),
    ("Steering/MinSpeed", "Float"),
    ("Steering/SteerOffset", "Float"),
    ("Steering/SteerScale", "Float"),
    ("Suspension/Front/AntiDiveCoeff", "Float"),
    ("Suspension/Front/AuxRollStiffness", "Float"),
    ("Suspension/Front/Camber", "Float"),
    ("Suspension/Front/CamverVsJounce", "Float"),
    ("Suspension/Front/DamperArmRatio", "Float"),
    ("Suspension/Front/DamperRate", "Float"),
    ("Suspension/Front/MaxBounce", "Float"),
    ("Suspension/Front/MaxDroop", "Float"),
    ("Suspension/Front/RideHeight", "Float"),
    ("Suspension/Front/SpringArmRatio", "Float"),
    ("Suspension/Front/SpringRate", "Float"),
    ("Suspension/Front/SteerVsLat", "Float"),
    ("Suspension/Front/SteerVsMoment", "Float"),
    ("Suspension/Front/SuspAppPointOffsetLat", "Float"),
    ("Suspension/Front/SuspAppPointOffsetLong", "Float"),
    ("Suspension/Front/SuspAppPointOffsetVert", "Float"),
    ("Suspension/Front/ToeIn", "Float"),
    ("Suspension/Front/ToeVsJounce", "Float"),
    ("Suspension/Front/ToeVsLong", "Float"),
    ("Suspension/Front/TyreType", "String"),
    ("Suspension/Front/UnsprungMass", "Float"),
    ("Suspension/Front/WaterDamping", "Float"),
    ("Suspension/Front/WheelDamping", "Float"),
    ("Suspension/Front/WheelMOI", "Float"),
    ("Suspension/Rear/AntiDiveCoeff", "Float"),
    ("Suspension/Rear/AuxRollStiffness", "Float"),
    ("Suspension/Rear/Camber", "Float"),
    ("Suspension/Rear/CamverVsJounce", "Float"),
    ("Suspension/Rear/DamperArmRatio", "Float"),
    ("Suspension/Rear/DamperRate", "Float"),
    ("Suspension/Rear/MaxBounce", "Float"),
    ("Suspension/Rear/MaxDroop", "Float"),
    ("Suspension/Rear/RideHeight", "Float"),
    ("Suspension/Rear/SpringArmRatio", "Float"),
    ("Suspension/Rear/SpringRate", "Float"),
    ("Suspension/Rear/SteerVsLat", "Float"),
    ("Suspension/Rear/SteerVsMoment", "Float"),
    ("Suspension/Rear/SuspAppPointOffsetLat", "Float"),
    ("Suspension/Rear/SuspAppPointOffsetLong", "Float"),
    ("Suspension/Rear/SuspAppPointOffsetVert", "Float"),
    ("Suspension/Rear/ToeIn", "Float"),
    ("Suspension/Rear/ToeVsJounce", "Float"),
    ("Suspension/Rear/ToeVsLong", "Float"),
    ("Suspension/Rear/TyreType", "String"),
    ("Suspension/Rear/UnsprungMass", "Float"),
    ("Suspension/Rear/WaterDamping", "Float"),
    ("Suspension/Rear/WheelDamping", "Float"),
    ("Suspension/Rear/WheelMOI", "Float"),
)

RETAIL_FIXED_BASE_SCHEMA: dict[str, str] = dict(RETAIL_FIXED_BASE_SCHEMA_ROWS)
RETAIL_ENGINE_COUNT_SCHEMA = {
    "Engine/Gears": "Int",
    "Engine/TorqueEntries": "Int",
}
RETAIL_REQUIRED_FIXED_SCHEMA = {
    **RETAIL_FIXED_BASE_SCHEMA,
    **RETAIL_ENGINE_COUNT_SCHEMA,
}
FIXED_BASE_GROUP_COUNTS: dict[str, int] = {}
for _path in RETAIL_REQUIRED_FIXED_SCHEMA:
    _group = _path.split("/", 1)[0]
    FIXED_BASE_GROUP_COUNTS[_group] = FIXED_BASE_GROUP_COUNTS.get(_group, 0) + 1
FIXED_BASE_GROUP_COUNTS = dict(sorted(FIXED_BASE_GROUP_COUNTS.items()))
RETAIL_FIXED_SCHEMA_SHA256 = hashlib.sha256(
    json.dumps(
        sorted(RETAIL_REQUIRED_FIXED_SCHEMA.items()),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
).hexdigest()

_DYNAMIC_ARRAYS = {
    "Gear": (re.compile(r"Engine/Gear(0|[1-9][0-9]*)\Z"), "Gears", "Float"),
    "ChangeUpRevs": (re.compile(r"Engine/ChangeUpRevs(0|[1-9][0-9]*)\Z"), "Gears", "Float"),
    "ChangeDownRevs": (re.compile(r"Engine/ChangeDownRevs(0|[1-9][0-9]*)\Z"), "Gears", "Float"),
    "TorqueEntry": (re.compile(r"Engine/TorqueEntry(0|[1-9][0-9]*)\Z"), "TorqueEntries", "Vector2"),
}
_DYNAMIC_PATH_PREFIXES = (
    "Engine/Gear",
    "Engine/ChangeUpRevs",
    "Engine/ChangeDownRevs",
    "Engine/TorqueEntry",
)
_MAX_MISSING_PATHS = 64
_MAX_SIGNED_INT = 0x7FFFFFFF


@dataclass(frozen=True)
class VehicleSchemaAudit:
    compatibility_class: str
    fixed_schema_ok: bool
    dynamic_shape_ok: bool
    fixed_fields_expected: int
    fixed_fields_present: int
    total_fields: int
    expected_total_fields: int | None
    gears_count: int | None
    torque_entries_count: int | None
    gear_fields_expected: int | None
    gear_fields_present: dict[str, int]
    torque_fields_expected: int | None
    torque_fields_present: int
    group_counts: dict[str, int]
    missing_paths: tuple[str, ...]
    missing_path_count: int
    unexpected_paths: tuple[str, ...]
    type_mismatches: tuple[tuple[str, str, str], ...]
    count_errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_count(fields: Mapping[str, Mapping[str, str]], path: str) -> tuple[int | None, str | None]:
    row = fields.get(path)
    if row is None:
        return None, None
    raw_value = row.get("value", "").strip()
    if not re.fullmatch(r"[0-9]+", raw_value):
        return None, f"{path} must be a positive decimal Int count; got {raw_value!r}"
    value = int(raw_value, 10)
    if value < 1:
        return None, f"{path} must be at least 1; got {value}"
    if value > _MAX_SIGNED_INT:
        return None, f"{path} exceeds the signed 32-bit Int range: {value}"
    return value, None


def _missing_index_paths(
    prefix: str,
    expected_count: int,
    present_indices: set[int],
    *,
    limit: int = _MAX_MISSING_PATHS,
) -> tuple[list[str], int]:
    valid = sorted(index for index in present_indices if 0 <= index < expected_count)
    missing_count = expected_count - len(valid)
    if missing_count <= 0 or limit <= 0:
        return [], max(0, missing_count)
    missing: list[str] = []
    expected_index = 0
    for index in valid:
        if index > expected_index:
            gap_end = min(index, expected_count)
            for absent in range(expected_index, min(gap_end, expected_index + (limit - len(missing)))):
                missing.append(f"{prefix}{absent}")
                if len(missing) >= limit:
                    return missing, missing_count
        expected_index = index + 1
        if len(missing) >= limit:
            return missing, missing_count
    for absent in range(expected_index, min(expected_count, expected_index + (limit - len(missing)))):
        missing.append(f"{prefix}{absent}")
        if len(missing) >= limit:
            break
    return missing, missing_count


def analyze_vehicle_base_schema(
    fields: Mapping[str, Mapping[str, str]],
) -> VehicleSchemaAudit:
    """Check the exact fixed retail fields and count-driven Engine index sets."""
    missing_paths: list[str] = []
    missing_path_count = 0
    unexpected_paths: set[str] = set()
    type_mismatches: list[tuple[str, str, str]] = []
    count_errors: list[str] = []
    group_counts: dict[str, int] = {}
    for path in fields:
        group = path.split("/", 1)[0]
        group_counts[group] = group_counts.get(group, 0) + 1

    for path, expected_type in RETAIL_REQUIRED_FIXED_SCHEMA.items():
        row = fields.get(path)
        if row is None:
            missing_paths.append(path)
            missing_path_count += 1
        elif row.get("type") != expected_type:
            type_mismatches.append((path, expected_type, str(row.get("type"))))

    gears_count, gears_error = _parse_count(fields, "Engine/Gears")
    torque_count, torque_error = _parse_count(fields, "Engine/TorqueEntries")
    for error in (gears_error, torque_error):
        if error is not None:
            count_errors.append(error)

    dynamic_indices: dict[str, set[int]] = {name: set() for name in _DYNAMIC_ARRAYS}
    dynamic_types_ok = True
    for path, row in fields.items():
        if path in RETAIL_REQUIRED_FIXED_SCHEMA:
            continue
        matched = False
        for name, (pattern, _count_field, expected_type) in _DYNAMIC_ARRAYS.items():
            match = pattern.fullmatch(path)
            if match is None:
                continue
            matched = True
            index = int(match.group(1), 10)
            dynamic_indices[name].add(index)
            if row.get("type") != expected_type:
                type_mismatches.append((path, expected_type, str(row.get("type"))))
                dynamic_types_ok = False
            count = gears_count if name != "TorqueEntry" else torque_count
            if count is not None and index >= count:
                unexpected_paths.add(path)
            break
        if not matched:
            unexpected_paths.add(path)

    dynamic_missing_count = 0
    gear_fields_present: dict[str, int] = {}
    for name in ("Gear", "ChangeUpRevs", "ChangeDownRevs"):
        indices = dynamic_indices[name]
        gear_fields_present[name] = len(indices)
        if gears_count is not None:
            absent, absent_count = _missing_index_paths(
                f"Engine/{name}", gears_count, indices
            )
            missing_paths.extend(absent)
            missing_path_count += absent_count
            dynamic_missing_count += absent_count
    torque_present = len(dynamic_indices["TorqueEntry"])
    if torque_count is not None:
        absent, absent_count = _missing_index_paths(
            "Engine/TorqueEntry", torque_count, dynamic_indices["TorqueEntry"]
        )
        missing_paths.extend(absent)
        missing_path_count += absent_count
        dynamic_missing_count += absent_count

    all_fixed_type_mismatches = any(
        path in RETAIL_REQUIRED_FIXED_SCHEMA
        for path, _expected, _actual in type_mismatches
    )
    fixed_schema_ok = not any(
        path in RETAIL_REQUIRED_FIXED_SCHEMA for path in missing_paths
    ) and not all_fixed_type_mismatches
    counts_valid = gears_count is not None and torque_count is not None
    dynamic_extra = False
    # `unexpected_paths` also contains unrecognized fixed paths. Detect extra
    # indexed paths directly so the dynamic result stays separately meaningful.
    for name, (_pattern, _count_field, _expected_type) in _DYNAMIC_ARRAYS.items():
        count = gears_count if name != "TorqueEntry" else torque_count
        if count is not None and any(index >= count for index in dynamic_indices[name]):
            dynamic_extra = True
    dynamic_type_mismatch = any(
        path not in RETAIL_REQUIRED_FIXED_SCHEMA
        for path, _expected, _actual in type_mismatches
    )
    malformed_dynamic = any(
        path.startswith(_DYNAMIC_PATH_PREFIXES)
        for path in unexpected_paths
    )
    count_types_ok = all(
        fields.get(path, {}).get("type") == expected_type
        for path, expected_type in RETAIL_ENGINE_COUNT_SCHEMA.items()
    )
    dynamic_shape_ok = (
        counts_valid
        and dynamic_missing_count == 0
        and not dynamic_extra
        and not malformed_dynamic
        and dynamic_types_ok
        and not dynamic_type_mismatch
        and count_types_ok
        and not count_errors
    )

    expected_total = (
        len(RETAIL_FIXED_BASE_SCHEMA) + 2 + 3 * gears_count + torque_count
        if counts_valid else None
    )
    if type_mismatches:
        status = "TYPE_MISMATCH"
    elif missing_path_count:
        status = "INCOMPLETE"
    elif count_errors or unexpected_paths:
        status = "UNVERIFIED_SCHEMA"
    else:
        status = "COMPATIBLE"

    return VehicleSchemaAudit(
        compatibility_class=status,
        fixed_schema_ok=fixed_schema_ok,
        dynamic_shape_ok=bool(dynamic_shape_ok),
        fixed_fields_expected=len(RETAIL_REQUIRED_FIXED_SCHEMA),
        fixed_fields_present=sum(path in fields for path in RETAIL_REQUIRED_FIXED_SCHEMA),
        total_fields=len(fields),
        expected_total_fields=expected_total,
        gears_count=gears_count,
        torque_entries_count=torque_count,
        gear_fields_expected=gears_count,
        gear_fields_present=gear_fields_present,
        torque_fields_expected=torque_count,
        torque_fields_present=torque_present,
        group_counts=dict(sorted(group_counts.items())),
        missing_paths=tuple(missing_paths[:_MAX_MISSING_PATHS]),
        missing_path_count=missing_path_count,
        unexpected_paths=tuple(sorted(unexpected_paths)),
        type_mismatches=tuple(sorted(set(type_mismatches))),
        count_errors=tuple(count_errors),
    )


def fixed_schema_fingerprint() -> str:
    """Return a descriptive hash for the fixed retail schema, not a gate."""
    return RETAIL_FIXED_SCHEMA_SHA256
