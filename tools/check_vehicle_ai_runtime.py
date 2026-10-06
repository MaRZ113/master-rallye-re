#!/usr/bin/env python3
"""Summarize Broker evidence for the R5V-H forced-ID26 AI proof.

The result is intentionally limited to Broker-state agreement. It cannot prove
that the Mercedes model rendered, AI drove, collisions worked, or a race ended.
"""
from __future__ import annotations

import argparse
import json
import ntpath
from pathlib import Path
from typing import Any


SLOT_FIELDS = ("PlayerType", "DriverID", "CarID", "CarClass", "CarType", "WheelType", "RaceState")
STOCK_T1_CONTROL_IDS = frozenset(range(1, 7))


def _unique_entry_values(entries: list[Any]) -> tuple[dict[str, Any], set[str]]:
    grouped: dict[str, list[Any]] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        grouped.setdefault(item["path"].casefold(), []).append(item.get("value"))
    values: dict[str, Any] = {}
    ambiguous: set[str] = set()
    for path, path_values in grouped.items():
        if len(path_values) == 1:
            values[path] = path_values[0]
        else:
            ambiguous.add(path)
    return values, ambiguous


def _observed(path: str, values: dict[str, Any], ambiguous: set[str]) -> dict[str, Any]:
    key = path.casefold()
    if key in ambiguous:
        return {"status": "AMBIGUOUS", "value": None}
    if key not in values:
        return {"status": "UNKNOWN", "value": None}
    return {"status": "OBSERVED", "value": values[key]}


def _slot_value(slot: dict[str, dict[str, Any]], field: str) -> Any:
    item = slot.get(field, {})
    return item.get("value") if item.get("status") == "OBSERVED" else None


def _is_int(value: Any) -> bool:
    return type(value) is int


def _pass_if(condition: bool | None) -> str:
    if condition is None:
        return "UNKNOWN"
    return "PASS" if condition else "FAIL"


def _normalized_windows_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = ntpath.normcase(ntpath.normpath(value.strip().replace("/", "\\")))
    if not ntpath.isabs(normalized):
        return None
    return normalized.rstrip("\\")


def summarize_capture(capture: Any, *, expected_exe_sha256: str,
                      expected_image_path: str, expected_active_root: str) -> dict[str, Any]:
    """Classify package provenance and Broker state; never claim human AI behavior."""
    if (len(expected_exe_sha256) != 64
            or any(char not in "0123456789abcdefABCDEF" for char in expected_exe_sha256)):
        raise ValueError("expected executable SHA256 must be exactly 64 hexadecimal characters")
    if (_normalized_windows_path(expected_image_path) is None
            or _normalized_windows_path(expected_active_root) is None):
        raise ValueError("expected image path and active Root must be absolute paths")
    if not isinstance(capture, dict) or not isinstance(capture.get("entries"), list):
        raise ValueError("capture must be an Observatory JSON object with an entries array")
    values, ambiguous = _unique_entry_values(capture["entries"])
    paths: dict[str, Any] = {
        "num_cars": "Race/NumCars",
        "num_players": "Race/NumPlayers",
    }
    observed = {name: _observed(path, values, ambiguous) for name, path in paths.items()}
    participants: dict[int, dict[str, dict[str, Any]]] = {}
    for slot_index in range(4):
        slot: dict[str, dict[str, Any]] = {}
        for field in SLOT_FIELDS:
            path = f"Race/Car{slot_index}/{field}"
            slot[field] = _observed(path, values, ambiguous)
        participants[slot_index] = slot

    player = participants[0]
    target = participants[1]
    controls = (participants[2], participants[3])
    player_type = _slot_value(player, "PlayerType")
    target_type = _slot_value(target, "PlayerType")
    control_types = tuple(_slot_value(slot, "PlayerType") for slot in controls)
    if all(value is not None for value in (player_type, target_type, *control_types)):
        controls_agree = control_types[0] == control_types[1]
        target_matches_controls = target_type == control_types[0]
        differs_from_player = player_type != control_types[0]
        ai_type_status = _pass_if(controls_agree and target_matches_controls and differs_from_player)
        ai_type_evidence = {
            "classification": "RELATIVE_TO_PLAYER_AND_STOCK_AI_CONTROLS",
            "player_raw_value": player_type,
            "target_raw_value": target_type,
            "control_raw_values": list(control_types),
            "numeric_enum_assumed": False,
        }
    else:
        ai_type_status = "UNKNOWN"
        ai_type_evidence = {
            "classification": "UNKNOWN",
            "player_raw_value": player_type,
            "target_raw_value": target_type,
            "control_raw_values": list(control_types),
            "numeric_enum_assumed": False,
        }

    target_id = _slot_value(target, "CarID")
    target_class = _slot_value(target, "CarClass")
    target_car_type = _slot_value(target, "CarType")
    target_wheel_type = _slot_value(target, "WheelType")
    player_id = _slot_value(player, "CarID")
    player_class = _slot_value(player, "CarClass")
    control_ids = [_slot_value(slot, "CarID") for slot in controls]
    control_classes = [_slot_value(slot, "CarClass") for slot in controls]

    classifications = {
        "ID26_AI_PRESENT": ai_type_status if target_id == 26 else _pass_if(None if target_id is None else False),
        "ID26_IS_PHYSICAL_26": _pass_if(None if target_id is None else target_id == 26),
        "ID26_CLASS_IS_T1": _pass_if(None if target_class is None else target_class == 0),
        "ID26_MERCEDES_FAMILY": _pass_if(
            None if target_car_type is None or target_wheel_type is None
            else target_car_type == "Mercedes" and target_wheel_type == "Mercedes"
        ),
        "PLAYER_UNCHANGED": _pass_if(
            None if not _is_int(player_id) or not _is_int(player_class)
            or player_type is None or control_types[0] is None
            else player_id == 0 and player_class == 0 and player_type != control_types[0]
        ),
        "STOCK_CONTROLS_PRESENT": _pass_if(
            None if any(not _is_int(value) for value in (*control_ids, *control_classes, player_id))
            else all(vehicle_id in STOCK_T1_CONTROL_IDS for vehicle_id in control_ids)
            and control_classes == [0, 0]
            and len(set(control_ids)) == 2
            and player_id not in control_ids
        ),
        "PLAYER_TYPE_MATCHES_AI_CONTROLS": ai_type_status,
        "NUM_CARS_IS_FOUR": _pass_if(
            None if observed["num_cars"]["status"] != "OBSERVED"
            else observed["num_cars"]["value"] == 4
        ),
        "NUM_PLAYERS_IS_ONE": _pass_if(
            None if observed["num_players"]["status"] != "OBSERVED"
            else observed["num_players"]["value"] == 1
        ),
    }

    source = capture.get("source") if isinstance(capture.get("source"), dict) else {}
    observed_hash = source.get("image_sha256")
    if isinstance(observed_hash, str):
        observed_hash = observed_hash.lower()
    observed_image_path = source.get("image_path")
    observed_active_root = source.get("active_root")
    hash_match = isinstance(observed_hash, str) and observed_hash == expected_exe_sha256.lower()
    image_path_match = (
        _normalized_windows_path(observed_image_path)
        == _normalized_windows_path(expected_image_path)
        and _normalized_windows_path(observed_image_path) is not None
    )
    active_root_match = (
        _normalized_windows_path(observed_active_root)
        == _normalized_windows_path(expected_active_root)
        and _normalized_windows_path(observed_active_root) is not None
    )
    provenance_complete = all((
        isinstance(observed_hash, str),
        _normalized_windows_path(observed_image_path) is not None,
        _normalized_windows_path(observed_active_root) is not None,
    ))
    candidate_identity = "MATCH" if hash_match and image_path_match and active_root_match else (
        "MISMATCH" if provenance_complete else "INCOMPLETE"
    )

    forced_identity_pass = all(classifications[key] == "PASS" for key in (
        "ID26_IS_PHYSICAL_26", "ID26_CLASS_IS_T1", "ID26_MERCEDES_FAMILY",
    ))
    all_state_pass = all(value == "PASS" for value in classifications.values())
    if candidate_identity != "MATCH":
        status = "RUNTIME_PACKAGE_MISMATCH"
        force_classification = "NOT_ASSESSED"
    elif not forced_identity_pass:
        status = "FORCED_ID26_NOT_OBSERVED"
        force_classification = "FORCED_ID26_NOT_OBSERVED"
    elif all_state_pass:
        status = "HUMAN_AI_CONFIRMATION_REQUIRED"
        force_classification = "FORCED_ID26_BROKER_MATCH"
    else:
        status = "BROKER_STATE_INCOMPLETE_OR_MISMATCH"
        force_classification = "FORCED_ID26_BROKER_MATCH"

    compact_participants = []
    for slot_index, slot in participants.items():
        compact_participants.append({
            "slot": slot_index,
            **{field: slot[field] for field in SLOT_FIELDS},
        })

    return {
        "status": status,
        "evidence_limit": (
            "Broker state only. It cannot prove model rendering, wheel/texture visibility, "
            "AI control behavior, physics, collision, damage, progress, or race completion."
        ),
        "candidate_identity": {
            "status": candidate_identity,
            "expected_exe_sha256": expected_exe_sha256,
            "capture_image_sha256": observed_hash,
            "expected_image_path": expected_image_path,
            "capture_image_path": observed_image_path,
            "expected_active_root": expected_active_root,
            "capture_active_root": observed_active_root,
            "checks": {
                "sha256": "MATCH" if hash_match else "MISMATCH_OR_MISSING",
                "image_path": "MATCH" if image_path_match else "MISMATCH_OR_MISSING",
                "active_root": "MATCH" if active_root_match else "MISMATCH_OR_MISSING",
            },
        },
        "forced_id26_classification": force_classification,
        "observed_race_state": observed,
        "participants": compact_participants,
        "ai_control_type_comparison": ai_type_evidence,
        "classifications": classifications,
        "ai_vehicle_ids": [value for value in [
            _slot_value(participants[slot_index], "CarID") for slot_index in (1, 2, 3)
        ] if _is_int(value)],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="Read-only Broker Observatory JSON snapshot")
    parser.add_argument("--expected-exe-sha256", required=True, help="exact verified H candidate SHA256")
    parser.add_argument("--expected-image-path", required=True, help="exact runtime-package MRallye.exe path")
    parser.add_argument("--expected-active-root", required=True, help="exact verified H runtime package root")
    args = parser.parse_args(argv)
    try:
        capture = json.loads(args.capture.read_text(encoding="utf-8-sig"))
        result = summarize_capture(
            capture,
            expected_exe_sha256=args.expected_exe_sha256,
            expected_image_path=args.expected_image_path,
            expected_active_root=args.expected_active_root,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"vehicle AI capture check refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "HUMAN_AI_CONFIRMATION_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
