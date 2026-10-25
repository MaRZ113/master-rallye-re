#!/usr/bin/env python3
"""Verify and summarize the supplied J.2 Observatory JSON/raw archive pairs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = Path(
    r"D:\Game\Master Rallye Pristine\MasterRallye-Observatory-0.2.3-beta"
    r"\observatory-data\captures\2026-10-09\2026-10-09.zip")
DEFAULT_OUTPUT = PROJECT_ROOT / "research/vehicles/sdk/j2/runtime-evidence-2026-10-09.json"
RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
HARDENED_WALKER_SHA256 = "16d85b7cae971b50f0ad1fd33425bae992cc758c0416c856199eb5ea3dfe2fe9"
HARDENED_VARIANT = "native-hardened-null-safe-stubs-v1"


class CaptureArchiveError(ValueError):
    """The provided capture archive is incomplete or inconsistent."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _values(capture: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for entry in capture.get("entries", []):
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            output[entry["path"]] = entry.get("value")
    return output


def _capture_row(name: str, json_bytes: bytes, raw_bytes: bytes) -> dict[str, Any]:
    capture = json.loads(json_bytes.decode("utf-8"))
    source = capture.get("source")
    if not isinstance(source, dict):
        raise CaptureArchiveError(f"capture has no source metadata: {name}")
    label = source.get("label")
    raw_name = source.get("raw_sidecar")
    if not isinstance(label, str) or not isinstance(raw_name, str):
        raise CaptureArchiveError(f"capture label or raw sidecar is missing: {name}")
    actual_raw_sha = _sha(raw_bytes)
    if source.get("raw_sha256") != actual_raw_sha:
        raise CaptureArchiveError(f"raw sidecar SHA256 mismatch: {raw_name}")
    if source.get("raw_byte_length") != len(raw_bytes):
        raise CaptureArchiveError(f"raw sidecar byte length mismatch: {raw_name}")
    if (source.get("image_sha256") != RETAIL_SHA256
            or source.get("image_size") != 3_121_214):
        raise CaptureArchiveError(f"capture is not from the exact pristine on-disk retail build: {name}")
    if (source.get("native_dump_verification") != "verified"
            or source.get("effective_broker_dump_variant") != "native_hardened"
            or source.get("native_dump_walker_variant") != HARDENED_VARIANT
            or source.get("native_dump_walker_sha256") != HARDENED_WALKER_SHA256
            or source.get("native_dump_post_results_safe") is not True):
        raise CaptureArchiveError(f"capture lacks verified J.1 hardened live Dump provenance: {name}")

    values = _values(capture)
    wanted = (
        "Frontend/QuickRace/Car0", "Frontend/QuickRace/Car1",
        "Frontend/VehicleSelect/PlayerID", "Frontend/VehicleSelect/Vehicle",
        "Frontend/VehicleSelect/CarModel", "FrontEnd/Network/selectedCar",
        "UI/XYButton/XValue", "UI/XYButton/YValue",
        "Race/Type", "Race/NumCars", "Race/NumPlayers",
        "Frontend/RaceDetails/CurrentRaceString", "Frontend/RaceDetails/Race",
        "MasterRallye/Stage",
    )
    state = {key: values.get(key) for key in wanted if key in values}
    race_roster: dict[str, dict[str, Any]] = {}
    native_roster: dict[str, dict[str, Any]] = {}
    fields = ("CarID", "CarClass", "PlayerType", "DriverID", "CarType", "WheelType", "Colour")
    for slot in range(4):
        race = {field: values.get(f"Race/Car{slot}/{field}") for field in fields}
        if race["CarID"] is not None:
            race_roster[str(slot)] = race
        native = {field: values.get(f"MasterRallye/Car{slot}/{field}") for field in fields}
        if native["CarID"] is not None:
            native_roster[str(slot)] = native
    return {
        "capture_json": name,
        "capture_json_sha256": _sha(json_bytes),
        "capture_label": label,
        "raw_sidecar": raw_name,
        "raw_sha256": actual_raw_sha,
        "raw_byte_length": len(raw_bytes),
        "process_id": source.get("process_id"),
        "disk_exe_sha256": source.get("image_sha256"),
        "disk_exe_size": source.get("image_size"),
        "profile_id": source.get("exact_profile_id"),
        "disk_build_classification": source.get("disk_build_classification"),
        "effective_broker_dump_variant": source.get("effective_broker_dump_variant"),
        "native_dump_walker_variant": source.get("native_dump_walker_variant"),
        "native_dump_walker_sha256": source.get("native_dump_walker_sha256"),
        "native_dump_verification": source.get("native_dump_verification"),
        "post_results_native_dump_safe": source.get("native_dump_post_results_safe"),
        "runtime_verified_native_dump_anchors": source.get("runtime_native_dump_verified_anchors"),
        "broker_state": state,
        "race_roster": race_roster,
        "masterrallye_native_roster": native_roster,
    }


def _by_label(captures: list[dict[str, Any]], label: str) -> dict[str, Any]:
    matches = [row for row in captures if row["capture_label"] == label]
    if len(matches) != 1:
        raise CaptureArchiveError(f"expected one capture labeled {label!r}, found {len(matches)}")
    return matches[0]


def _identity_roster(capture: dict[str, Any], field: str) -> list[tuple[Any, Any]]:
    roster = capture[field]
    return [(row.get("CarID"), row.get("DriverID")) for _slot, row in sorted(roster.items(), key=lambda item: int(item[0]))]


def summarize_archive(archive: Path) -> dict[str, Any]:
    archive = Path(archive)
    if not archive.is_file():
        raise CaptureArchiveError(f"capture archive is missing: {archive}")
    archive_bytes = archive.read_bytes()
    try:
        zipped = zipfile.ZipFile(archive)
    except zipfile.BadZipFile as exc:
        raise CaptureArchiveError("capture archive is not a valid ZIP") from exc
    with zipped:
        names = set(zipped.namelist())
        json_names = sorted(name for name in names if name.casefold().endswith(".json"))
        raw_names = {name for name in names if name.casefold().endswith(".dump.bin")}
        if len(json_names) != 19 or len(raw_names) != 19:
            raise CaptureArchiveError(f"expected 19 JSON/raw pairs, got {len(json_names)} JSON and {len(raw_names)} raw")
        captures = []
        used_raw: set[str] = set()
        for json_name in json_names:
            json_bytes = zipped.read(json_name)
            metadata = json.loads(json_bytes.decode("utf-8")).get("source", {})
            raw_sidecar = metadata.get("raw_sidecar") if isinstance(metadata, dict) else None
            if not isinstance(raw_sidecar, str) or raw_sidecar not in names:
                raise CaptureArchiveError(f"missing declared raw sidecar for {json_name}")
            if raw_sidecar in used_raw:
                raise CaptureArchiveError(f"raw sidecar is paired more than once: {raw_sidecar}")
            used_raw.add(raw_sidecar)
            captures.append(_capture_row(json_name, json_bytes, zipped.read(raw_sidecar)))
        if used_raw != raw_names:
            raise CaptureArchiveError("archive has unpaired or undeclared raw sidecars")

    # Assert the requested runtime claims directly from captured Broker values.
    split = _by_label(captures, "R5VQ-quickrace-splitscreen")
    split_cars = split["race_roster"]
    if not (split["broker_state"].get("Race/NumPlayers") == 2
            and split_cars.get("0", {}).get("CarID") == 27
            and split_cars.get("0", {}).get("CarClass") == 1
            and split_cars.get("0", {}).get("PlayerType") == 1
            and split_cars.get("0", {}).get("CarType") == "R5VQualifier"
            and split_cars.get("0", {}).get("WheelType") == "R5VQualifier"
            and split_cars.get("1", {}).get("CarID") == 26
            and split_cars.get("1", {}).get("CarClass") == 0
            and split_cars.get("1", {}).get("PlayerType") == 1
            and split_cars.get("1", {}).get("CarType") == "Mercedes"
            and split_cars.get("1", {}).get("WheelType") == "Mercedes"):
        raise CaptureArchiveError("SplitScreen physical ID26+ID27 runtime oracle did not match")

    cup1 = _by_label(captures, "R5VQ-rallyecup-race1")
    cup2 = _by_label(captures, "R5VQ-rallyecup-race2")
    if not (cup1["broker_state"].get("Race/Type") == cup2["broker_state"].get("Race/Type") == 6
            and cup1["broker_state"].get("Frontend/RaceDetails/CurrentRaceString") == "RACE 1/3"
            and cup2["broker_state"].get("Frontend/RaceDetails/CurrentRaceString") == "RACE 2/3"
            and _identity_roster(cup1, "race_roster") == _identity_roster(cup2, "race_roster")
            and (27, 7) in _identity_roster(cup1, "race_roster")):
        raise CaptureArchiveError("Rallye Cup stage identity/persistence oracle did not match")

    master0 = _by_label(captures, "R5VQ-masterrallye-race1-AI-beforeres")
    master1 = _by_label(captures, "R5VQ-masterrallye-race2-AI-afterres")
    master0_roster = _identity_roster(master0, "masterrallye_native_roster")
    master1_roster = _identity_roster(master1, "masterrallye_native_roster")
    if not (master0["process_id"] == 42244 and master1["process_id"] == 41800
            and master0["broker_state"].get("MasterRallye/Stage") == 0
            and master1["broker_state"].get("MasterRallye/Stage") == 1
            and master0_roster == master1_roster
            and (27, 4) in master0_roster
            and _identity_roster(master0, "race_roster") == master0_roster
            and _identity_roster(master1, "race_roster") == master1_roster):
        raise CaptureArchiveError("Master Rallye fresh-process stage identity/persistence oracle did not match")

    afterrace = _by_label(captures, "R5VQ-quickrace-afterrace")
    reset = _by_label(captures, "R5VQ-quickrace-afterrace-carselect-z-navarareset")
    if not (afterrace["broker_state"].get("Frontend/QuickRace/Car0") == 27
            and reset["broker_state"].get("Frontend/QuickRace/Car0") == 27
            and afterrace["broker_state"].get("Frontend/VehicleSelect/PlayerID") !=
                reset["broker_state"].get("Frontend/VehicleSelect/PlayerID")
            and reset["broker_state"].get("Frontend/VehicleSelect/CarModel") == 7
            and reset["broker_state"].get("UI/XYButton/XValue") == 0):
        raise CaptureArchiveError("Vehicle Select re-entry/player-slot divergence was not reproduced as described")

    walker_hashes = {row["native_dump_walker_sha256"] for row in captures}
    pids = {row["process_id"] for row in captures}
    if walker_hashes != {HARDENED_WALKER_SHA256}:
        raise CaptureArchiveError("capture set mixes native Dump walker variants")
    return {
        "schema_version": 2,
        "phase": "R5V-J.2 final evidence closeout and Vehicle Select re-entry regression",
        "evidence_kind": "verified Observatory Broker captures plus separately identified human-only stock-launch observation",
        "archive_name": archive.name,
        "archive_sha256": _sha(archive_bytes),
        "archive_size_bytes": len(archive_bytes),
        "capture_pair_count": len(captures),
        "all_json_raw_pairs_verified": True,
        "all_captures_same_retail_exe_sha256": RETAIL_SHA256,
        "all_captures_same_live_walker_sha256": HARDENED_WALKER_SHA256,
        "all_captures_same_live_walker_variant": HARDENED_VARIANT,
        "all_captures_dump_verification": "verified",
        "all_captures_post_results_dump_safe": True,
        "process_ids_observed": sorted(pids),
        "runtime_results": {
            "splitscreen_id27_t2_r5vqualifier_plus_id26_t1_mercedes": {
                "status": "CONFIRMED_BY_RUNTIME",
                "capture": split["capture_json"],
                "race_roster": split_cars,
            },
            "rallye_cup_stage_roster_persistence": {
                "status": "CONFIRMED_BY_RUNTIME",
                "stage1_capture": cup1["capture_json"],
                "stage1": cup1["broker_state"].get("Frontend/RaceDetails/CurrentRaceString"),
                "stage2_capture": cup2["capture_json"],
                "stage2": cup2["broker_state"].get("Frontend/RaceDetails/CurrentRaceString"),
                "same_carid_driverid_roster": _identity_roster(cup1, "race_roster"),
                "id27_driverid": 7,
            },
            "master_rallye_fresh_process_roster_persistence": {
                "status": "CONFIRMED_BY_RUNTIME",
                "stage0_capture": master0["capture_json"],
                "stage0_process_id": master0["process_id"],
                "stage0": master0["broker_state"].get("MasterRallye/Stage"),
                "stage1_capture": master1["capture_json"],
                "stage1_process_id": master1["process_id"],
                "stage1": master1["broker_state"].get("MasterRallye/Stage"),
                "same_carid_driverid_roster": master0_roster,
                "id27_driverid": 4,
            },
            "vehicle_select_reentry_divergence": {
                "status": "REPRODUCED_BOUNDED_FRONTEND_STATE_DIVERGENCE",
                "stored_quickrace_car0_both": 27,
                "afterrace_player_id": afterrace["broker_state"].get("Frontend/VehicleSelect/PlayerID"),
                "afterrace_car_model": afterrace["broker_state"].get("Frontend/VehicleSelect/CarModel"),
                "afterrace_x_ordinal": afterrace["broker_state"].get("UI/XYButton/XValue"),
                "navara_reset_player_id": reset["broker_state"].get("Frontend/VehicleSelect/PlayerID"),
                "navara_reset_car_model": reset["broker_state"].get("Frontend/VehicleSelect/CarModel"),
                "navara_reset_x_ordinal": reset["broker_state"].get("UI/XYButton/XValue"),
                "different_player_ids": True,
                "vehicle_record_loss_inferred": False,
            },
            "original_stock_launch_without_loader": {
                "status": "HUMAN_CONFIRMED_UNINSTRUMENTED",
                "instrumented_capture": None,
                "observations": ["no addon vehicles present", "normal stock save environment observed"],
            },
        },
        "captures": captures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the 19-pair Observatory J.2 runtime archive")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true", help="write the verified derived evidence JSON")
    args = parser.parse_args(argv)
    try:
        result = summarize_archive(args.archive)
        if args.write:
            output = Path(args.output).resolve()
            research_root = (PROJECT_ROOT / "research/vehicles/sdk/j2").resolve()
            try:
                output.relative_to(research_root)
            except ValueError as exc:
                raise CaptureArchiveError("derived evidence output must stay under research/vehicles/sdk/j2") from exc
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS_CAPTURE_ARCHIVE", "capture_pair_count": result["capture_pair_count"],
                          "archive_sha256": result["archive_sha256"],
                          "all_raw_hashes_verified": result["all_json_raw_pairs_verified"],
                          "summary_written": str(args.output.resolve()) if args.write else None},
                         indent=2, ensure_ascii=False, sort_keys=True))
    except (CaptureArchiveError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, ensure_ascii=False))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
