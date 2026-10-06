#!/usr/bin/env python3
"""Summarize Broker evidence for the R5V-H forced-ID26 AI proof.

The result is intentionally limited to Broker-state agreement. It cannot prove
that the Mercedes model rendered, AI drove, collisions worked, or a race ended.
"""
from __future__ import annotations

import argparse
import json
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


def summarize_capture(capture: Any, *, expected_exe_sha256: str | None = None) -> dict[str, Any]:
    """Report the four-car forced proof state without claiming runtime behavior."""
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
    observed_hash = source.get("image_sha256") or source.get("exe_sha256")
    if isinstance(observed_hash, str):
        observed_hash = observed_hash.lower()
    if expected_exe_sha256 is None:
        candidate_identity = "NOT_REQUESTED"
    elif not isinstance(observed_hash, str):
        candidate_identity = "UNKNOWN"
    else:
        candidate_identity = "MATCH" if observed_hash == expected_exe_sha256.lower() else "MISMATCH"

    all_state_pass = all(value == "PASS" for value in classifications.values())
    candidate_identity_pass = expected_exe_sha256 is None or candidate_identity == "MATCH"
    if candidate_identity == "MISMATCH":
        status = "CANDIDATE_IDENTITY_MISMATCH"
    elif all_state_pass and candidate_identity_pass:
        status = "BROKER_STATE_MATCH_ONLY"
    else:
        status = "BROKER_STATE_INCOMPLETE_OR_MISMATCH"

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
        },
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
    parser.add_argument("--expected-exe-sha256", help="optional exact candidate hash to compare with capture metadata")
    args = parser.parse_args(argv)
    try:
        capture = json.loads(args.capture.read_text(encoding="utf-8-sig"))
        result = summarize_capture(capture, expected_exe_sha256=args.expected_exe_sha256)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"vehicle AI capture check refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "BROKER_STATE_MATCH_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
