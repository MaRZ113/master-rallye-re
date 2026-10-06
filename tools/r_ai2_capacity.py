"""Exact five-car offline research proof; no live writes or unknown-build support."""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

from r_ai1_mixed_class import (RETAIL_SHA256, RETAIL_SIZE, ORIGINAL_TEXT_SIZE,
                              TEXT_SIZE_OFFSET, REPOSITORY, apply_ranges,
                              ignored_output, sha256, stock_map, verify_capture)
from r_ai1_hardening import BASE_SHA256, hardening_ranges, compose_ranges
from patch_vehicle_slot25 import parse_pe, va_to_file_offset

CAVE = 0x68E300
SITES = (0x47B88A, 0x47B8DD)
PROFILE = "retail-r-ai2-five-car-hardened"
CANDIDATE_SHA256 = "806ebedcd6d174682fcc4619fb75eaabca2a1281eda4d4d784807b3583f5f2e2"


def effective_opponents(opponents: int, mode: int, split: bool, ghost: int,
                        player: int, track: int) -> int:
    """Bounded policy specification; the native shim is separately emulated."""
    if any(type(v) is not int for v in (opponents, mode, ghost, player, track)) or type(split) is not bool:
        raise ValueError("Need typed frontend state")
    return 4 if (opponents, mode, split, ghost, player, track) == (3, 2, False, 0, 0, 10) else opponents


def shim() -> bytes:
    code = bytearray()
    branches = []
    def call(address):
        site = CAVE + len(code)
        code.extend(b"\xe8" + struct.pack("<i", address - site - 5))
    def reject(op):
        code.extend(bytes.fromhex(op)); branches.append(len(code)); code.extend(bytes(4))
    def frontend(getter):
        call(0x4AE700); code.extend(bytes.fromhex("8bc8")); call(getter)
    call(0x4AE150)  # Original read always runs, with original incoming ECX.
    code.extend(bytes.fromhex("9c6083f803")); reject("0f85")
    frontend(0x4AE090); code.extend(bytes.fromhex("83f802")); reject("0f85")
    frontend(0x4AE2D0); code.extend(bytes.fromhex("84c0")); reject("0f85")
    frontend(0x4AE0F0); code.extend(bytes.fromhex("85c0")); reject("0f85")
    frontend(0x4AE030); code.extend(bytes.fromhex("83f80a")); reject("0f85")
    code.extend(bytes.fromhex("6a00")); frontend(0x4ADFB0)
    code.extend(bytes.fromhex("85c0")); reject("0f85")
    code.extend(bytes.fromhex("c744241c04000000"))  # PUSHAD saved EAX only.
    end = len(code)
    code.extend(bytes.fromhex("619dc3"))
    for offset in branches:
        struct.pack_into("<i", code, offset, end - offset - 4)
    return bytes(code)


def capacity_ranges() -> list[dict]:
    def call_bytes(site, target):
        return b"\xe8" + struct.pack("<i", target - site - 5)
    rows = [{"offset": TEXT_SIZE_OFFSET, "va": None, "rva": None,
             "original": struct.pack("<I", ORIGINAL_TEXT_SIZE),
             "replacement": struct.pack("<I", CAVE + len(shim()) - 0x401000),
             "purpose": "Declare bounded five-car getter shim in existing text padding"}]
    for site in SITES:
        rows.append({"offset": site - 0x400000, "va": site, "rva": site - 0x400000,
                     "original": call_bytes(site, 0x4AE150), "replacement": call_bytes(site, CAVE),
                     "purpose": "Quick Race effective opponent read: guarded 3 -> 4",
                     "evidence": "47B780 consumes both count reads; ordinary chooser and NumCars increment retained"})
    rows.append({"offset": CAVE - 0x400000, "va": CAVE, "rva": CAVE - 0x400000,
                 "original": bytes(len(shim())), "replacement": shim(),
                 "purpose": "Original getter, exact one-human T1 ID0 / Track10 / Race / ghost-off guard",
                 "evidence": "Register/flags/stack preservation checked by native emulation"})
    return rows


def ranges() -> list[dict]:
    return compose_ranges(hardening_ranges(), capacity_ranges())


def manifest(output_hash: str) -> dict:
    return {"phase": "R-AI2", "profile": PROFILE, "source_sha256": RETAIL_SHA256,
            "hardened_base_sha256": BASE_SHA256, "output_sha256": output_hash,
            "image_size": RETAIL_SIZE, "broker_dump_variant": "native_hardened",
            "status": "PREPARED_RUNTIME_UNTESTED", "num_cars": 5, "num_players": 1,
            "active_indices": list(range(5)), "mixed_class_chooser": False,
            "frontend_opponent_choice": 3, "effective_opponents": 4,
            "guard": {"mode": 2, "split_screen": False, "ghost": 0, "player_id": 0, "track": 10},
            "arrays_relocated": False, "participant_loops_patched": False,
            "ranges": [{**{k: v for k, v in row.items() if k not in ("original", "replacement")},
                        "length": len(row["original"]), "original_hex": row["original"].hex(),
                        "replacement_hex": row["replacement"].hex()} for row in ranges()]}


def build(source: bytes) -> tuple[bytes, dict]:
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError("Need exact pristine retail size/SHA256")
    pe = parse_pe(source)
    for row in ranges():
        if row["va"] is not None and va_to_file_offset(pe, row["va"]) != row["offset"]:
            raise ValueError("Unexpected PE layout")
    result = apply_ranges(source, ranges(), RETAIL_SHA256)
    digest = sha256(result)
    if digest != CANDIDATE_SHA256:
        raise ValueError("Output differs from the exact audited five-car profile")
    return result, manifest(digest)


def verify(candidate: bytes) -> dict:
    if len(candidate) != RETAIL_SIZE or sha256(candidate) != CANDIDATE_SHA256:
        raise ValueError("Unknown five-car candidate")
    restored = bytearray(candidate)
    for row in ranges():
        start = row["offset"]; end = start + len(row["replacement"])
        if candidate[start:end] != row["replacement"]:
            raise ValueError("Replacement bytes differ")
        restored[start:end] = row["original"]
    rebuilt, result = build(bytes(restored))
    if rebuilt != candidate:
        raise ValueError("Inverse/reproduction mismatch")
    return result


def check_snapshot(snapshot: dict, results=False) -> dict:
    source = snapshot.get("source", {})
    label = "five-results" if results else "five-race"
    if (snapshot.get("kind") != "master-rallye-broker-dump-snapshot" or snapshot.get("schema_version") != 1 or
            source.get("image_sha256") != CANDIDATE_SHA256 or source.get("build_profile") != PROFILE or
            source.get("broker_dump_variant") != "native_hardened" or source.get("label") != label or
            source.get("freshness") != "post_baseline_complete_dump_proven"):
        raise ValueError("Need fresh exact-profile capture at the specified lifecycle point")
    entries = snapshot["entries"]
    def get(path):
        rows = [row for row in entries if row["path"] == path]
        if len(rows) != 1:
            raise ValueError("Missing/ambiguous path: " + path)
        return rows[0]["value"]
    expected = {"Race/NumCars": 5, "Race/NumPlayers": 1, "Race/NumNetworkPlayers": 0,
                "Race/Type": 2, "Race/FinishingType": 0, "Race/AttractMode": False,
                "Race/NetworkSyncActive": False, "Race/GhostPlayback": False,
                "Frontend/QuickRace/Track": 10, "Frontend/QuickRace/Ghost": 0}
    for path, value in expected.items():
        actual = get(path)
        if type(actual) is not type(value) or actual != value:
            raise ValueError("Unexpected " + path)
    vehicles = stock_map()
    participants = []
    for n in range(5):
        row = {key: get(f"Race/Car{n}/{key}") for key in
               ("CarID", "CarClass", "PlayerType", "DriverID", "CarType", "WheelType")}
        if type(row["CarID"]) is not int or row["CarID"] not in ((0,) if n == 0 else range(1, 7)):
            raise ValueError("Need ordinary stock T1 identity")
        for key, value in {"CarClass": 0, "PlayerType": 1 if n == 0 else 2}.items():
            if type(row[key]) is not int or row[key] != value:
                raise ValueError(f"Car{n} {key} mismatch")
        driver = row["DriverID"]
        if type(driver) is not int or (driver != 30 if n == 0 else not 0 <= driver < 10):
            raise ValueError("Invalid driver identity")
        for key in ("CarType", "WheelType"):
            if not isinstance(row[key], str) or row[key].casefold() != vehicles[row["CarID"]]["family"].casefold():
                raise ValueError("Family/ID mismatch")
        participants.append(row)
    if len({row["CarID"] for row in participants}) != 5 or len({row["DriverID"] for row in participants[1:]}) != 4:
        raise ValueError("Vehicle/AI-driver alias")
    canaries = json.loads((REPOSITORY / "research/r-ai1-1/vehicle-physics-canaries.json").read_text())
    values = next(row["values"] for row in canaries["vehicles"] if row["id"] == participants[4]["CarID"])
    for suffix, value in values.items():
        actual = get("Vehicles/Car4/" + suffix)
        if type(actual) not in (int, float) or not math.isclose(actual, value, abs_tol=0.0001):
            raise ValueError("Car4 named physics mismatch")
    observed = {f"{prefix}/Car{n}": sum(row["path"].startswith(f"{prefix}/Car{n}/") for row in entries)
                for prefix in ("Vehicles", "Physics", "Controller", "Network") for n in range(5)}
    report = {"status": "BROKER_RESULTS_MATCH_ONLY" if results else "BROKER_STATE_MATCH_ONLY",
              "runtime_full_pass": False, "participants": participants,
              "car4_named_physics": values, "subsystem_paths_not_actor_proof": observed}
    if results:
        lists = {}
        for suffix in ("PositionList", "NameList", "TimeList"):
            value = get("Frontend/RaceResults/" + suffix)
            rows = [row for row in entries if row["path"] == "Frontend/RaceResults/" + suffix]
            if rows[0].get("type") != "StringList" or not isinstance(value, list) or len(value) != 5 or any(not isinstance(v, str) for v in value):
                raise ValueError("Need five logical result entries: " + suffix)
            lists[suffix] = value
        # The pinned public parser preserves each native StringList item's
        # enclosing quotes. Keep that representation bound to the raw Dump.
        if lists["PositionList"] != [f'"{n}"' for n in range(1, 6)]:
            raise ValueError("Unexpected five-place result ranking")
        report["result_lists"] = lists
        icons = [get(f"Frontend/RaceResults/Car{n}") for n in range(8)]
        registry = json.loads((REPOSITORY / "research/r5v_a/final-vehicle-registry.json").read_text())
        image_ids = {row["index"]: row["raw_numeric_arguments_push_order"][0]
                     for row in registry["executable_registry"]["records"]}
        if any(type(v) is not int for v in icons) or sorted(icons[:5]) != sorted(image_ids[row["CarID"]] for row in participants) or icons[5:] != [12] * 3:
            raise ValueError("Five vehicle result icons / three blank slots mismatch")
        report["result_icons_are_registry_image_ids"] = icons
    report["human_evidence_required"] = ["five active models", "Car4 wheels/physics/collision/damage",
                                         "four AI drive and progress", "ranking/finish/results", "stable exit/cleanup"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build"); create.add_argument("source", type=Path); create.add_argument("output", type=Path)
    check = sub.add_parser("verify"); check.add_argument("candidate", type=Path)
    for name in ("check-race", "check-results"):
        p = sub.add_parser(name); p.add_argument("candidate", type=Path); p.add_argument("snapshot", type=Path)
        p.add_argument("--observatory", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "build":
        output = ignored_output(args.output)
        if output.exists() or output.with_suffix(".manifest.json").exists():
            raise ValueError("Refusing to overwrite candidate/manifest")
        data, result = build(args.source.read_bytes()); output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data); output.with_suffix(".manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    else:
        result = verify(args.candidate.read_bytes())
        if args.command.startswith("check-"):
            from r_ai1_observe import load_profile
            observe = load_profile(args.observatory, args.candidate)
            snapshot = json.loads(args.snapshot.read_text(encoding="utf-8")); sidecar = snapshot["source"]["raw_sidecar"]
            if Path(sidecar).name != sidecar:
                raise ValueError("Invalid raw sidecar name")
            verify_capture(snapshot, args.snapshot.with_name(sidecar).read_bytes(), observe.core.parse_dump_bytes)
            result = check_snapshot(snapshot, results=args.command == "check-results")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
