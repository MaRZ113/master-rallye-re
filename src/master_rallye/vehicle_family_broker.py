"""R-PHYS2.1 evidence helpers for named-family to runtime-CarN setup.

The constants below record facts established from the exact retail
``MRallye.exe`` Ghidra audit. They deliberately keep the family name, numeric
type ID, participant index, and selectable-slot status as separate values.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .vehicle_config_analysis import VehicleConfigDocument


RETAIL_EXE_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
DIRECT_FAMILY_GROUPS = (
    "Dimensions",
    "Chassis",
    "Steering",
    "Engine",
    "Suspension",
    "DamageParams",
)


@dataclass(frozen=True)
class BrokerGroupPair:
    group: str
    reader: str
    writer: str
    evidence: str


# Order follows FUN_00493E30 and FUN_004938C0. The function pairs are supported
# by those call sequences and the retail Ghidra string references.
BROKER_GROUP_PAIRS = (
    BrokerGroupPair("Dimensions", "FUN_0049B0C0", "FUN_004940A0", "WheelBase and wheel-radius keys"),
    BrokerGroupPair("Chassis", "FUN_0049B940", "FUN_00494730", "/Chassis/ path segment"),
    BrokerGroupPair("Steering", "FUN_0049C950", "FUN_00495460", "Steering root fields in the family XML"),
    BrokerGroupPair("Engine", "FUN_0049CEF0", "FUN_004958E0", "/Engine/ path segment"),
    BrokerGroupPair("Suspension/Front", "FUN_0049E970", "FUN_00496D20", "/Suspension/Front/ path segment"),
    BrokerGroupPair("Suspension/Rear", "FUN_004A01D0", "FUN_00498090", "/Suspension/Rear/ path segment"),
    BrokerGroupPair("DamageParams", "FUN_004A1A30", "FUN_00499400", "/DamageParams/ path segment"),
    BrokerGroupPair("Modifications", "FUN_004A32F0", "FUN_0049A800", "13 player setup fields below Modifications/"),
)


# FUN_00458E70 initializes these type-ID/name records, IDs 0 through 24.
FAMILY_BY_TYPE_ID = (
    "Landcruiser",
    "Pajero",
    "Tata",
    "Terrano",
    "Chevyblazer",
    "Xtrail",
    "Frontera",
    "Navara",
    "Forester",
    "Jump",
    "Rmonster",
    "Patrol",
    "Newrav",
    "Kiasportage",
    "Wildcat",
    "Simmbugghini",
    "Astero",
    "Kangoo",
    "Megane",
    "Mattserati",
    "Bruno",
    "SeatBuggy",
    "Kamaz",
    "Icecream",
    "Ufo",
)


PLAYER_MODIFICATION_FIELDS = (
    "Suspension/Front/SpringRate",
    "Suspension/Front/DamperRate",
    "Suspension/Front/AuxRollStiffness",
    "Suspension/Front/RideHeight",
    "Suspension/Rear/SpringRate",
    "Suspension/Rear/DamperRate",
    "Suspension/Rear/AuxRollStiffness",
    "Suspension/Rear/RideHeight",
    "Engine/BrakeBias",
    "Engine/CentreLSDBias",
    "Engine/FrontLSDBias",
    "Engine/RearLSDBias",
    "Engine/GearRatioDiff",
)


@dataclass(frozen=True)
class FamilyIdentityAudit:
    family_name: str
    family_config_present: bool
    family_type_ids: tuple[int, ...]
    selectable_slot_status: str
    participant_index_contract: str
    base_field_count: int
    base_group_counts: dict[str, int]
    missing_base_groups: tuple[str, ...]
    base_modification_fields: tuple[str, ...]
    base_missing_modification_fields: tuple[str, ...]
    player1_modification_fields: tuple[str, ...]
    player1_missing_modification_fields: tuple[str, ...]
    player2_modification_fields: tuple[str, ...]
    player2_missing_modification_fields: tuple[str, ...]


def _validate_family_name(family: str) -> None:
    if not isinstance(family, str) or not family or family != family.strip():
        raise ValueError("family must be a non-empty exact name")
    if family in {".", ".."} or any(char in family for char in ("/", "\\", "\x00")):
        raise ValueError("family must be one path component")


def named_vehicle_path(family: str) -> str:
    """Return the raw-name path produced by FUN_00493770."""
    _validate_family_name(family)
    return f"Vehicles/{family}"


def runtime_car_path(participant_index: int) -> str:
    """Return the numeric path built for the same index by FUN_00493600."""
    if isinstance(participant_index, bool) or not isinstance(participant_index, int):
        raise ValueError("participant index must be a non-negative integer")
    if participant_index < 0:
        raise ValueError("participant index must be a non-negative integer")
    return f"Vehicles/Car{participant_index}"


def player_overlay_path(family: str, player_number: int) -> str:
    """Return the participant's separate Player1/Player2 setup subtree."""
    _validate_family_name(family)
    if (
        isinstance(player_number, bool)
        or not isinstance(player_number, int)
        or player_number not in (1, 2)
    ):
        raise ValueError("player number must be 1 or 2")
    return f"{named_vehicle_path(family)}/Player{player_number}"


def family_for_type_id(type_id: int) -> str | None:
    """Resolve only the IDs explicitly initialized by FUN_00458E70."""
    if isinstance(type_id, bool) or not isinstance(type_id, int):
        raise ValueError("vehicle type ID must be an integer")
    if 0 <= type_id < len(FAMILY_BY_TYPE_ID):
        return FAMILY_BY_TYPE_ID[type_id]
    return None


def family_type_ids(family: str) -> tuple[int, ...]:
    _validate_family_name(family)
    return tuple(i for i, name in enumerate(FAMILY_BY_TYPE_ID) if name == family)


def _overlay_fields(document: VehicleConfigDocument, family: str, player_number: int) -> set[str]:
    relative_prefix = f"Player{player_number}/Modifications/"
    paths = document.families.get(family, {})
    return {
        path.removeprefix(relative_prefix)
        for path in paths
        if path.startswith(relative_prefix)
    }


def analyze_family_identity(
    vehicle_config: VehicleConfigDocument,
    modifications_config: VehicleConfigDocument,
    family: str,
) -> FamilyIdentityAudit:
    """Compare exact family roots and per-player overlay keys without aliasing."""
    _validate_family_name(family)
    base = vehicle_config.families.get(family, {})
    group_counts: dict[str, int] = {}
    for path in base:
        group = path.split("/", 1)[0]
        group_counts[group] = group_counts.get(group, 0) + 1

    base_modifications = {
        path.removeprefix("Modifications/")
        for path in base
        if path.startswith("Modifications/")
    }
    player1 = _overlay_fields(modifications_config, family, 1)
    player2 = _overlay_fields(modifications_config, family, 2)
    expected = set(PLAYER_MODIFICATION_FIELDS)
    return FamilyIdentityAudit(
        family_name=family,
        family_config_present=family in vehicle_config.families,
        family_type_ids=family_type_ids(family),
        # Static family/type evidence does not establish frontend selectability.
        selectable_slot_status="UNRESOLVED",
        participant_index_contract=(
            "FUN_0044A320 loop index -> FUN_0044ED50 param_1 -> "
            "FUN_004938C0 index -> Vehicles/Car<same index>"
        ),
        base_field_count=len(base),
        base_group_counts=dict(sorted(group_counts.items())),
        missing_base_groups=tuple(sorted(set(DIRECT_FAMILY_GROUPS) - set(group_counts))),
        base_modification_fields=tuple(sorted(base_modifications)),
        base_missing_modification_fields=tuple(sorted(expected - base_modifications)),
        player1_modification_fields=tuple(sorted(player1)),
        player1_missing_modification_fields=tuple(sorted(expected - player1)),
        player2_modification_fields=tuple(sorted(player2)),
        player2_missing_modification_fields=tuple(sorted(expected - player2)),
    )


def build_family_config_report(
    vehicle_config: VehicleConfigDocument,
    modifications_config: VehicleConfigDocument,
    families: tuple[str, ...] = ("Navara", "Jump", "Trooper", "forklift"),
) -> dict[str, Any]:
    """Build a JSON-safe audit while retaining source hashes and identity layers."""
    audits = [asdict(analyze_family_identity(vehicle_config, modifications_config, name))
              for name in families]
    return {
        "schema_version": 1,
        "retail_exe_sha256": RETAIL_EXE_SHA256,
        "vehicle_config_source": {
            "path": vehicle_config.source,
            "sha256": vehicle_config.sha256,
            "file_size": vehicle_config.file_size,
        },
        "modifications_config_source": {
            "path": modifications_config.source,
            "sha256": modifications_config.sha256,
            "file_size": modifications_config.file_size,
        },
        "family_type_catalog": [
            {"type_id": type_id, "family_name": family}
            for type_id, family in enumerate(FAMILY_BY_TYPE_ID)
        ],
        "broker_group_pairs": [asdict(pair) for pair in BROKER_GROUP_PAIRS],
        "families": audits,
        "evidence_boundary": {
            "family_name": "Exact string in the initialized retail type catalog or config XML.",
            "type_id": "Only IDs 0 through 24 initialized by FUN_00458E70 are listed.",
            "selectable_slot": "UNRESOLVED by this static broker audit.",
            "model_directory": "Not inferred from family/type presence; use the separate resource inventory.",
        },
    }


def write_family_config_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Write generated JSON and a compact Markdown summary to an output directory."""
    import json

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "retail-family-config-audit.json"
    markdown_path = output_dir / "retail-family-config-audit.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# R-PHYS2.1 retail family/config audit",
        "",
        "Generated from read-only retail XML and the fixed-build Ghidra findings.",
        "",
        f"- `vehicles.xml`: {report['vehicle_config_source']['file_size']} bytes, SHA-256 `{report['vehicle_config_source']['sha256']}`",
        f"- `Modifications.xml`: {report['modifications_config_source']['file_size']} bytes, SHA-256 `{report['modifications_config_source']['sha256']}`",
        f"- retail EXE SHA-256: `{report['retail_exe_sha256']}`",
        "",
        "| Identity | Config family | Type IDs in initialized table | Base fields | Missing base groups | Base Modifications fields | Player1 setup fields | Player2 setup fields | Selectable slot |",
        "|---|---:|---|---:|---|---:|---:|---:|---|",
    ]
    for item in report["families"]:
        lines.append(
            f"| {item['family_name']} | {'yes' if item['family_config_present'] else 'no'} | "
            f"{', '.join(map(str, item['family_type_ids'])) or 'none'} | {item['base_field_count']} | "
            f"{', '.join(item['missing_base_groups']) or 'none'} | "
            f"{len(item['base_modification_fields'])} | "
            f"{len(item['player1_modification_fields'])} | {len(item['player2_modification_fields'])} | "
            f"{item['selectable_slot_status']} |"
        )
    lines.extend(("", "The type catalog, config family, participant index, and selectable slot are separate identities.", ""))
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, markdown_path
