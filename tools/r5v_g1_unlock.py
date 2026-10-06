#!/usr/bin/env python3
"""Evidence-bounded R5V-G.1 progress model and Observatory capture summary.

This module models only the statically recovered retail predicates. Capture
output is a Broker-state summary; it cannot prove what a UI widget displayed or
which executable hook ran.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


UNLOCK_PATH_BY_ID: dict[int, str] = {
    3: "Progress/UnlockedCars/T1CupCar1",
    4: "Progress/UnlockedCars/T1CupCar2",
    5: "Progress/UnlockedCars/T1CupCar3",
    6: "Progress/UnlockedCars/T1MasterRallyeCar",
    10: "Progress/UnlockedCars/T2CupCar1",
    11: "Progress/UnlockedCars/T2CupCar2",
    12: "Progress/UnlockedCars/T2CupCar3",
    13: "Progress/UnlockedCars/T2MasterRallyeCar",
    18: "Progress/UnlockedCars/T3CupCar1",
    19: "Progress/UnlockedCars/T3CupCar2",
    20: "Progress/UnlockedCars/T3CupCar3",
    21: "Progress/UnlockedCars/T3MasterRallyeCar",
    22: "Progress/UnlockedCars/ChallengeCar",
    23: "Progress/UnlockedCars/Invitation",
    24: "Progress/UnlockedCars/Bonus1",
    25: "Progress/UnlockedCars/Bonus2",
}
UNCONDITIONAL_STOCK_IDS = frozenset({0, 1, 2, 7, 8, 9, 14, 15, 16, 17})
QUICK_RACE_CLASS_PATHS = {
    "t2": "Progress/OpenedModes/T2Cup",
    "t3": "Progress/OpenedModes/T3Cup",
    "unlock_cups": "Progress/Cheats/UnlockCups",
    "unlock_all": "Progress/Cheats/UnlockAll",
}
LOCK_REASON_SELECTOR_BY_ID = {
    3: 9,
    4: 10,
    5: 11,
    6: 19,
    10: 12,
    11: 13,
    12: 14,
    13: 20,
    18: 15,
    19: 16,
    20: 17,
    21: 21,
    22: 23,
    23: 22,
    24: 25,
    25: 26,
}
GLOBAL_CAR_CHEAT_PATHS = (
    "Progress/Cheats/UnlockAll",
    "Progress/Cheats/UnlockCars",
)
OBSERVATORY_SUMMARY_PATHS = {
    "vehicle_select_car_model": "Frontend/VehicleSelect/CarModel",
    "vehicle_select_manufacturer": "Frontend/VehicleSelect/ManufacturerName",
    "vehicle_select_model_name": "Frontend/VehicleSelect/ModelName",
    "vehicle_select_class": "Frontend/VehicleSelect/VehicleText",
    "vehicle_select_class_index": "Frontend/VehicleSelect/Vehicle",
    "network_selected_car": "FrontEnd/Network/selectedCar",
    "ui_enabled": "UI/Enabled",
    "race_car0_id": "Race/Car0/CarID",
    "race_car0_class": "Race/Car0/CarClass",
    "race_details_vehicle_string": "Frontend/RaceDetails/CurrentVehicleString",
    "race_details_race_string": "Frontend/RaceDetails/CurrentRaceString",
    "race_details_mode": "Frontend/RaceDetails/Race",
}


def stock_vehicle_gate(vehicle_id: int, unlocked: dict[str, Any],
                       cheats: dict[str, Any]) -> bool | None:
    """Evaluate the recovered retail ID switch, returning None on missing data.

    The default switch arm (including ID > 25) is available. Special IDs use
    their named Progress/UnlockedCars flag after the two global bypass flags.
    """
    for name in ("UnlockAll", "UnlockCars"):
        value = cheats.get(name)
        if value is True:
            return True
    if vehicle_id in UNCONDITIONAL_STOCK_IDS:
        return True
    path = UNLOCK_PATH_BY_ID.get(vehicle_id)
    if path is None:
        return True
    key = path.rsplit("/", 1)[-1]
    value = unlocked.get(key)
    if value is True:
        return True
    if value is not False:
        return None
    if cheats.get("UnlockAll") is False and cheats.get("UnlockCars") is False:
        return False
    return None


def id26_stock_mirror_gate(record_id: int, unlocked: dict[str, Any],
                           cheats: dict[str, Any]) -> bool | None:
    """Model the G.1 hook: only ID26 substitutes stock gate input ID3."""
    return stock_vehicle_gate(3 if record_id == 26 else record_id, unlocked, cheats)


def stock_locked_reason_selector(vehicle_id: int) -> int:
    """Return the selector from retail's ID-3..25 jump table (default is 8)."""
    return LOCK_REASON_SELECTOR_BY_ID.get(vehicle_id, 8)


def id26_locked_reason_selector(vehicle_id: int) -> int:
    """Model the G.1 presentation hook: ID26 uses stock ID3's group-6 reason."""
    return stock_locked_reason_selector(3 if vehicle_id == 26 else vehicle_id)


def quickrace_reachable_classes(progress: dict[str, Any]) -> list[str] | None:
    """Return the recovered Quick Race class list, or None if evidence is absent."""
    t3 = progress.get("T3Cup")
    unlock_cups = progress.get("UnlockCups")
    unlock_all = progress.get("UnlockAll")
    if any(value is True for value in (t3, unlock_cups, unlock_all)):
        return ["T1", "T2", "T3"]
    if any(value is not False for value in (t3, unlock_cups, unlock_all)):
        return None
    t2 = progress.get("T2Cup")
    if t2 is True:
        return ["T1", "T2"]
    if t2 is False:
        return ["T1"]
    return None


def _unique_entry_values(entries: list[Any]) -> tuple[dict[str, Any], set[str]]:
    grouped: dict[str, list[Any]] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        grouped.setdefault(item["path"].casefold(), []).append(item.get("value"))
    values: dict[str, Any] = {}
    ambiguous: set[str] = set()
    for key, matches in grouped.items():
        if len(matches) == 1:
            values[key] = matches[0]
        else:
            ambiguous.add(key)
    return values, ambiguous


def _observed(path: str, values: dict[str, Any], ambiguous: set[str]) -> dict[str, Any]:
    key = path.casefold()
    if key in ambiguous:
        return {"status": "AMBIGUOUS", "value": None}
    if key not in values:
        return {"status": "UNKNOWN", "value": None}
    return {"status": "OBSERVED", "value": values[key]}


def summarize_capture(capture: Any) -> dict[str, Any]:
    """Produce a conservative summary from a decoded Observatory JSON object."""
    if not isinstance(capture, dict) or not isinstance(capture.get("entries"), list):
        raise ValueError("capture must be an Observatory JSON object with an entries array")
    values, ambiguous = _unique_entry_values(capture["entries"])

    progress_paths = {
        "T1CupCar1": "Progress/UnlockedCars/T1CupCar1",
        "T1CupCar2": "Progress/UnlockedCars/T1CupCar2",
        "T1CupCar3": "Progress/UnlockedCars/T1CupCar3",
        "T1MasterRallyeCar": "Progress/UnlockedCars/T1MasterRallyeCar",
        "T2CupCar1": "Progress/UnlockedCars/T2CupCar1",
        "T3CupCar1": "Progress/UnlockedCars/T3CupCar1",
        "ChallengeCar": "Progress/UnlockedCars/ChallengeCar",
        "Invitation": "Progress/UnlockedCars/Invitation",
        "Bonus1": "Progress/UnlockedCars/Bonus1",
        "Bonus2": "Progress/UnlockedCars/Bonus2",
        "T2Cup": "Progress/OpenedModes/T2Cup",
        "T3Cup": "Progress/OpenedModes/T3Cup",
        "UnlockCars": "Progress/Cheats/UnlockCars",
        "UnlockCups": "Progress/Cheats/UnlockCups",
        "UnlockAll": "Progress/Cheats/UnlockAll",
    }
    progress = {name: _observed(path, values, ambiguous)
                for name, path in progress_paths.items()}

    def bool_value(name: str) -> Any:
        item = progress[name]
        return item["value"] if item["status"] == "OBSERVED" and isinstance(item["value"], bool) else None

    classes = quickrace_reachable_classes({
        "T2Cup": bool_value("T2Cup"),
        "T3Cup": bool_value("T3Cup"),
        "UnlockCups": bool_value("UnlockCups"),
        "UnlockAll": bool_value("UnlockAll"),
    })
    id3_expected = stock_vehicle_gate(
        3,
        {"T1CupCar1": bool_value("T1CupCar1")},
        {"UnlockCars": bool_value("UnlockCars"), "UnlockAll": bool_value("UnlockAll")},
    )
    source = capture.get("source") if isinstance(capture.get("source"), dict) else {}
    summary = {name: _observed(path, values, ambiguous)
               for name, path in OBSERVATORY_SUMMARY_PATHS.items()}
    selected = summary["network_selected_car"]
    highlighted_id = selected["value"] if selected["status"] == "OBSERVED" else None
    t1_locked = bool_value("T1CupCar1") is False
    unlock_cheats_off = (bool_value("UnlockCars") is False
                         and bool_value("UnlockAll") is False)
    locked_context = (highlighted_id in (3, 26) and t1_locked and unlock_cheats_off
                      and summary["vehicle_select_car_model"] == {"status": "OBSERVED", "value": -1})
    if locked_context:
        manufacturer = summary["vehicle_select_manufacturer"]
        model_name = summary["vehicle_select_model_name"]
        if (manufacturer == {"status": "OBSERVED", "value": "CAR LOCKED"}
                and model_name == {"status": "OBSERVED", "value": "UNLOCK BY WINNING 2 T1 CUPS"}):
            lock_text_status = "LOCK_TEXT_OK"
        elif manufacturer["status"] == "OBSERVED" and model_name["status"] == "OBSERVED":
            lock_text_status = "LOCK_TEXT_MISMATCH"
        else:
            lock_text_status = "UNKNOWN"
        button = summary["ui_enabled"]
        if button == {"status": "OBSERVED", "value": False}:
            button_status = "BUTTON_LOCKED"
        elif button == {"status": "OBSERVED", "value": True}:
            button_status = "BUTTON_NOT_LOCKED"
        else:
            button_status = "UNKNOWN"
    else:
        if highlighted_id is None:
            lock_text_status = "UNKNOWN"
            button_status = "UNKNOWN"
        elif highlighted_id not in (3, 26):
            lock_text_status = "NOT_APPLICABLE"
            button_status = "NOT_APPLICABLE"
        else:
            lock_text_status = "UNKNOWN"
            button_status = "UNKNOWN"

    race_car0 = summary["race_car0_id"]
    details_name = summary["race_details_vehicle_string"]
    details_mode = summary["race_details_mode"]
    if race_car0 == {"status": "OBSERVED", "value": 26} and details_name["status"] == "OBSERVED":
        details_status = ("RACE_DETAILS_NAME_UNKNOWN" if details_name["value"] == "GALOCAL UNKNOWN"
                          else "RACE_DETAILS_ID26_NAME_OBSERVED")
    else:
        details_status = "UNKNOWN"
    return {
        "status": "UNLOCK_STATE_SUMMARY_ONLY",
        "evidence_limit": "Broker state does not prove rendered visibility, loaded XML provenance, native hook execution, or runtime selectability; selectedCar is only the highlighted/current frontend identity.",
        "capture": {
            "label": source.get("label"),
            "build": source.get("build"),
            "build_profile": source.get("build_profile"),
            "image_sha256": source.get("image_sha256"),
        },
        "quickrace_reachable_classes": classes if classes is not None else "UNKNOWN",
        "stock_vehicle_id3_gate_expected": id3_expected if id3_expected is not None else "UNKNOWN",
        "progress": progress,
        "observed_state": summary,
        "locked_slot_oracle": {
            "highlighted_vehicle_id": highlighted_id if highlighted_id is not None else "UNKNOWN",
            "lock_text": lock_text_status,
            "button": button_status,
            "commit_behavior": "UNKNOWN_NOT_PROVEN_BY_BROKER",
        },
        "race_details_oracle": {
            "mode": details_mode,
            "vehicle_string": details_name,
            "current_race_string": summary["race_details_race_string"],
            "race_car0_id": race_car0,
            "status": details_status,
            "evidence_limit": "Broker values establish state only, not visible text rendering.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="Read-only Broker Observatory JSON capture")
    args = parser.parse_args(argv)
    try:
        capture = json.loads(args.capture.read_text(encoding="utf-8-sig"))
        result = summarize_capture(capture)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"R5V-G.1 capture check refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
