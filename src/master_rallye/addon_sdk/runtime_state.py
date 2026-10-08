"""Evidence-limited Broker checker for sparse Vehicle Select restoration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .manifest import AddonValidationError, read_json


CLASS_NAMES = {0: "T1", 1: "T2", 2: "T3"}
PHYSICAL_TO_CLASS = {
    **{value: ("T1", value) for value in range(7)},
    **{value: ("T2", value - 7) for value in range(7, 14)},
    **{value: ("T3", value - 14) for value in range(14, 26)},
    26: ("T1", 7),
    27: ("T2", 7),
}


def _capture_values(capture: dict[str, Any]) -> dict[str, Any]:
    entries = capture.get("entries")
    if not isinstance(entries, list):
        raise AddonValidationError("capture has no entries array")
    wanted = {
        "Frontend/QuickRace/Car0",
        "Frontend/VehicleSelect/Vehicle",
        "Frontend/VehicleSelect/CarModel",
        "FrontEnd/Network/selectedCar",
        "UI/XYButton/XValue",
        "Frontend/VehicleSelect/ManufacturerName",
        "Frontend/VehicleSelect/ModelName",
    }
    values: dict[str, list[tuple[int, Any]]] = {key: [] for key in wanted}
    for entry in entries:
        if isinstance(entry, dict) and entry.get("path") in wanted:
            values[entry["path"]].append((entry.get("ordinal", -1), entry.get("value")))
    output: dict[str, Any] = {}
    for key, rows in values.items():
        if len(rows) > 1:
            distinct = {json.dumps(value, sort_keys=True, ensure_ascii=False) for _, value in rows}
            if len(distinct) > 1:
                raise AddonValidationError(f"capture contains conflicting duplicate Broker path: {key}")
        output[key] = max(rows, key=lambda row: row[0])[1] if rows else None
    return output


def inspect_frontend_capture(path: Path, *, expected_exe_sha256: str | None = None) -> dict[str, Any]:
    capture, raw = read_json(path)
    source = capture.get("source", {})
    image_sha = source.get("image_sha256") if isinstance(source, dict) else None
    if expected_exe_sha256 and image_sha != expected_exe_sha256.lower():
        raise AddonValidationError("capture executable SHA256 does not match expected build")
    values = _capture_values(capture)
    stored = values["Frontend/QuickRace/Car0"]
    displayed = values["Frontend/VehicleSelect/CarModel"]
    selected = values["FrontEnd/Network/selectedCar"]
    class_index = values["Frontend/VehicleSelect/Vehicle"]
    local = values["UI/XYButton/XValue"]
    expected_mapping = PHYSICAL_TO_CLASS.get(stored) if type(stored) is int else None
    expected_class = expected_mapping[0] if expected_mapping else None
    expected_local = expected_mapping[1] if expected_mapping else None
    observed_class = CLASS_NAMES.get(class_index) if type(class_index) is int else None
    in_sync = (
        stored is not None and stored == displayed == selected
        and expected_mapping is not None
        and observed_class == expected_class
        and local == expected_local
    )
    return {
        "status": "FRONTEND_SELECTION_CONSISTENT" if in_sync else "FRONTEND_SELECTION_DIVERGENCE_STORED_ID_RETAINED",
        "capture_sha256": hashlib.sha256(raw).hexdigest(),
        "capture_label": source.get("label") if isinstance(source, dict) else None,
        "exe_sha256": image_sha,
        "process_id": source.get("process_id") if isinstance(source, dict) else None,
        "stored_quickrace_car_id": stored,
        "displayed_car_model": displayed,
        "selected_car_highlight_or_current_identity": selected,
        "vehicle_class_index": class_index,
        "vehicle_class": observed_class,
        "xybutton_local_ordinal": local,
        "expected_class_from_stored_id": expected_class,
        "expected_local_from_stored_id": expected_local,
        "manufacturer": values["Frontend/VehicleSelect/ManufacturerName"],
        "model": values["Frontend/VehicleSelect/ModelName"],
        "stored_physical_id_retained": stored is not None,
        "physical_vehicle_record_loss": "NOT_INFERRED_FROM_THIS_FRONTEND_CAPTURE",
        "interpretation": "Stored absolute Quick Race ID is reported independently; selectedCar is not treated as commit proof.",
    }
