"""R-AI1: one exact retail selector patch, stock mapping and offline oracle.

No process-memory writes, assets, registry changes or capacity changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from patch_vehicle_slot25 import parse_pe, va_to_file_offset

REPOSITORY = Path(__file__).resolve().parents[1]
RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
RETAIL_SIZE = 3_121_214
CANDIDATE_SHA256 = "bae5de6aa3ba6cfcd08425c5a00341a3c374ec503b4ba944db6fc2c0d6a77a57"
SITE = 0x00458428
CONTINUE = 0x0045842D
SELECTOR = 0x0068E300
ORIGINAL = bytes.fromhex("8b44241450")
TEXT_SIZE_OFFSET = 0x218  # .text section header + VirtualSize
ORIGINAL_TEXT_SIZE = 0x28D294
CLASS_STARTS = (0, 7, 14)
CLASS_COUNTS = (7, 7, 11)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stock_class_local(vehicle_id: int) -> tuple[int, int]:
    if type(vehicle_id) is not int or not 0 <= vehicle_id < 25:
        raise ValueError("Only named stock retail IDs 0..24 are supported")
    cls = 0 if vehicle_id < 7 else 1 if vehicle_id < 14 else 2
    return cls, vehicle_id - CLASS_STARTS[cls]


def stock_absolute(cls: int, local: int) -> int:
    if (type(cls) is not int or type(local) is not int or
            not 0 <= cls < 3 or not 0 <= local < CLASS_COUNTS[cls]):
        raise ValueError("Invalid stock class/local index")
    return CLASS_STARTS[cls] + local


def stock_map() -> list[dict]:
    existing = json.loads((REPOSITORY / "research/r5v_a/final-vehicle-registry.json").read_text())
    rows = []
    for item in existing["canonical_registry"]:
        vehicle_id = item["numeric_id"]
        cls, local = stock_class_local(vehicle_id)
        if item["class_id"] != cls or item["registry_index"] != vehicle_id:
            raise ValueError("Canonical stock registry contradicts retail conversion")
        rows.append({"id": vehicle_id, "class": cls, "class_name": f"T{cls + 1}",
                     "local_index": local, "family": item["internal_name"],
                     "display_name": item["display_name"], "folder": item["folder"]})
    if sorted(row["id"] for row in rows) != list(range(25)):
        raise ValueError("Canonical stock registry incomplete")
    return sorted(rows, key=lambda row: row["id"])


def selector_code() -> bytes:
    # Entry ESP is unchanged by a JMP. Save flags, so offsets increase by four.
    # ESI=participant; first AI/count/class retain their input values.
    # The original player-ID argument slots have already become scratch values
    # (driver-pool item 9 and last vehicle-pool item); never guard on them here.
    code = bytearray(b"\x9c\x83\xfe\x01\x75\x00")
    branches = [5]
    for offset, expected in ((0x88, 1), (0x8C, 3), (0x90, 0)):
        code += b"\x83\xbc\x24" + struct.pack("<I", offset) + bytes([expected & 255])
        code += b"\x75\x00"
        branches.append(len(code) - 1)
    # Change only the chosen ID local after RNG/pool/driver bookkeeping.
    code += bytes.fromhex("c74424180e000000")
    restore = len(code)
    for branch in branches:
        code[branch] = restore - (branch + 1)
    code += b"\x9d" + ORIGINAL
    code += b"\xe9" + struct.pack("<i", CONTINUE - (SELECTOR + len(code) + 5))
    return bytes(code)


def patch_ranges() -> list[dict]:
    code = selector_code()
    return [
        {"offset": TEXT_SIZE_OFFSET, "va": None,
         "original": struct.pack("<I", ORIGINAL_TEXT_SIZE),
         "replacement": struct.pack("<I", SELECTOR + len(code) - 0x401000),
         "purpose": "Declare the selector in existing .text raw padding; no page/image growth"},
        {"offset": SITE - 0x400000, "va": SITE, "original": ORIGINAL,
         "replacement": b"\xe9" + struct.pack("<i", SELECTOR - (SITE + 5)),
         "purpose": "Guarded per-participant absolute-ID substitution before stock setters"},
        {"offset": SELECTOR - 0x400000, "va": SELECTOR,
         "original": bytes(len(code)), "replacement": code,
         "purpose": "Car1 ID14 only for retained args (first AI1,count3,class0); replay MOV/PUSH"},
    ]


def apply_ranges(source: bytes, ranges: list[dict], expected_hash: str) -> bytes:
    if sha256(source) != expected_hash:
        raise ValueError("Input SHA256 does not match the exact supported source")
    result = bytearray(source)
    end = 0
    for patch in sorted(ranges, key=lambda item: item["offset"]):
        offset, original, replacement = patch["offset"], patch["original"], patch["replacement"]
        if (offset < end or len(original) != len(replacement) or
                offset + len(original) > len(source) or
                source[offset:offset + len(original)] != original):
            raise ValueError("Unexpected original bytes, range overlap or invalid bounds")
        result[offset:offset + len(original)] = replacement
        end = offset + len(original)
    return bytes(result)


def build_candidate(source: bytes) -> tuple[bytes, dict]:
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError("R-AI1 accepts only exact pristine retail")
    pe = parse_pe(source)  # Reuse established fail-closed PE layout validation.
    for address in (SITE, SELECTOR):
        if va_to_file_offset(pe, address) != address - 0x400000:
            raise ValueError("Unexpected target PE layout")
    result = apply_ranges(source, patch_ranges(), RETAIL_SHA256)
    if sha256(result) != CANDIDATE_SHA256:
        raise ValueError("Selector no longer reproduces the pinned R-AI1 profile")
    return result, patch_manifest(sha256(result))


def patch_manifest(output_hash: str) -> dict:
    return {"phase": "R-AI1", "profile": "retail-r-ai1-fresh-profile-v2",
            "source_sha256": RETAIL_SHA256, "output_sha256": output_hash,
            "image_size": RETAIL_SIZE, "num_cars_changed": False,
            "guards": {"participant": 1, "first_ai": 1, "ai_count": 3,
                       "requested_class": 0},
            "controlled_human_player_id": 0,
            "target_id": 14, "driver_id_changed": False,
            "ranges": [{**{k: v for k, v in item.items() if k not in ("original", "replacement")},
                        "original_hex": item["original"].hex(),
                        "replacement_hex": item["replacement"].hex()}
                       for item in patch_ranges()]}


def verify_candidate(candidate: bytes) -> dict:
    if len(candidate) != RETAIL_SIZE:
        raise ValueError("Candidate size mismatch")
    restored = bytearray(candidate)
    for patch in patch_ranges():
        offset = patch["offset"]
        end = offset + len(patch["replacement"])
        if candidate[offset:end] != patch["replacement"]:
            raise ValueError("Candidate selector/manifest bytes mismatch")
        restored[offset:end] = patch["original"]
    if sha256(restored) != RETAIL_SHA256:
        raise ValueError("Candidate contains unapproved changes")
    if sha256(candidate) != CANDIDATE_SHA256:
        raise ValueError("Candidate differs from the pinned R-AI1 profile")
    return patch_manifest(sha256(candidate))


def mixed_plan(participants: list[dict], num_cars: int) -> list[dict]:
    if type(num_cars) is not int or num_cars != 4 or len(participants) != 4:
        raise ValueError("R-AI1 requires exactly four existing participants")
    if (participants[0]["CarID"] != 0 or type(participants[0]["PlayerType"]) is not int or
            participants[0]["PlayerType"] != 1):
        raise ValueError("Player must follow the normal ID0 human path")
    for n, participant in enumerate(participants):
        cls, _ = stock_class_local(participant["CarID"])
        if participant["CarClass"] != cls or cls != 0:
            raise ValueError("Source participants must all be stock T1")
        if n and (type(participant["PlayerType"]) is not int or participant["PlayerType"] != 2 or
                  type(participant["DriverID"]) is not int or not 0 <= participant["DriverID"] <= 9):
            raise ValueError("Source AI identity invalid")
    if len({item["CarID"] for item in participants}) != 4:
        raise ValueError("Source participants alias vehicle IDs")
    result = [dict(item) for item in participants]
    result[1].update(CarID=14, CarClass=2)
    return result


def check_snapshot(snapshot: dict, image_hash: str) -> dict:
    source = snapshot.get("source", {})
    if (image_hash != CANDIDATE_SHA256 or
            snapshot.get("kind") != "master-rallye-broker-dump-snapshot" or
            snapshot.get("schema_version") != 1 or
            source.get("image_sha256") != image_hash or
            source.get("freshness") != "post_baseline_complete_dump_proven" or
            source.get("label") != "mixed-race"):
        raise ValueError("Need a fresh mixed-race Observatory capture of the exact candidate")
    entries = snapshot["entries"]
    def get(path):
        matches = [row for row in entries if row["path"] == path]
        if len(matches) != 1:
            raise ValueError(f"Missing/ambiguous Broker path: {path}")
        return matches[0]["value"]
    for path, expected in {"Race/NumCars": 4, "Race/NumPlayers": 1,
                           "Race/Type": 2, "Race/Networked": False,
                           "Frontend/Active": True, "Frontend/QuickRace/Track": 10}.items():
        value = get(path)
        if type(value) is not type(expected) or value != expected:
            raise ValueError(f"Unexpected {path}: {value!r}")
    vehicles = stock_map()
    participants = []
    for n in range(4):
        row = {key: get(f"Race/Car{n}/{key}") for key in
               ("CarID", "CarClass", "PlayerType", "DriverID", "CarType", "WheelType")}
        cls, _ = stock_class_local(row["CarID"])
        expected_cls = 2 if n == 1 else 0
        if type(row["CarClass"]) is not int or row["CarClass"] != cls or cls != expected_cls:
            raise ValueError(f"Car{n} class/ID mismatch")
        if n in (2, 3) and not 1 <= row["CarID"] <= 6:
            raise ValueError("Controlled proof requires stock T1 AI controls (IDs1..6)")
        if type(row["PlayerType"]) is not int or row["PlayerType"] != (1 if n == 0 else 2):
            raise ValueError(f"Car{n} player/AI mismatch")
        if n and (type(row["DriverID"]) is not int or not 0 <= row["DriverID"] < 10):
            raise ValueError(f"Car{n} AI DriverID invalid")
        if n == 0 and (type(row["DriverID"]) is not int or row["DriverID"] != 30):
            raise ValueError("Player DriverID must remain the ordinary one-human value30")
        for key in ("CarType", "WheelType"):
            if str(row[key]).casefold() != vehicles[row["CarID"]]["family"].casefold():
                raise ValueError(f"Car{n} {key} contradicts ID")
        participants.append(row)
    if participants[0]["CarID"] != 0 or participants[1]["CarID"] != 14:
        raise ValueError("Controlled player/target IDs differ")
    if len({row["CarID"] for row in participants}) != 4:
        raise ValueError("Participant CarID alias")
    if len({row["DriverID"] for row in participants[1:]}) != 3:
        raise ValueError("Stock AI driver pool unexpectedly aliases DriverIDs")
    # Independent named-physics values, chosen for stock T1/T3 distinction.
    physics = {"Dimensions/WheelBase": 2.77, "Dimensions/TrackWidthFront": 1.66,
               "Engine/GearRatioDiff": 3.72}
    for suffix, expected in physics.items():
        value = get("Vehicles/Car1/" + suffix)
        if type(value) not in (int, float) or not math.isclose(value, expected, abs_tol=0.0001):
            raise ValueError(f"Target named-physics mismatch: {suffix}")
    observed = {f"{prefix}/Car{n}": sum(row["path"].startswith(f"{prefix}/Car{n}/")
                                      for row in entries)
                for prefix in ("Vehicles", "Physics", "Controller", "Network") for n in range(4)}
    lifecycle = {row["path"]: row["value"] for row in entries
                 if row["path"] in {f"{prefix}/Car{n}/Finished"
                                     for prefix in ("Race", "Network") for n in range(4)} or
                 row["path"] in ("Race/ID", "Race/Name", "Frontend/Running")}
    return {"status": "BROKER_STATE_MATCH_ONLY", "runtime_full_pass": False,
            "participants": participants, "target_physics": physics,
            "lifecycle_values_not_actor_proof": lifecycle,
            "subsystem_path_counts_not_actor_proof": observed,
            "human_evidence_required": ["model/wheels/collision identity", "AI drives",
                                        "HUD/progress/results", "normal exit/frontend return"]}


def verify_capture(snapshot: dict, raw: bytes, parse_dump) -> None:
    """Bind the JSON evidence to its latest complete raw Dump using Observatory."""
    source = snapshot["source"]
    if sha256(raw) != source["raw_sha256"]:
        raise ValueError("Capture raw sidecar hash mismatch")
    parsed = parse_dump(raw)
    for key in ("selected_block_offset", "selected_block_length", "selected_block_sha256"):
        if source[key] != parsed["source"][key]:
            raise ValueError("Selected Dump block mismatch")
    for key in ("entries", "dump"):
        if snapshot[key] != parsed[key]:
            raise ValueError(f"Snapshot {key} differs from raw Dump")


def ignored_output(path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to(REPOSITORY / ".research-output"):
        raise ValueError("Generated R-AI1 artifacts must stay in this checkout's .research-output")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("map")
    build = sub.add_parser("build")
    build.add_argument("source", type=Path)
    build.add_argument("output", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("candidate", type=Path)
    check = sub.add_parser("check")
    check.add_argument("candidate", type=Path)
    check.add_argument("snapshot", type=Path)
    check.add_argument("--observatory", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "map":
        result = stock_map()
    elif args.command == "build":
        output = ignored_output(args.output)
        data, result = build_candidate(args.source.read_bytes())
        if output.exists() or output.with_suffix(".manifest.json").exists():
            raise ValueError("Refusing to overwrite an existing candidate or manifest")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        output.with_suffix(".manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    else:
        result = verify_candidate(args.candidate.read_bytes())
        if args.command == "check":
            snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
            source = snapshot["source"]
            sidecar = source["raw_sidecar"]
            if Path(sidecar).name != sidecar:
                raise ValueError("Invalid raw sidecar name")
            raw = args.snapshot.with_name(sidecar).read_bytes()
            from r_ai1_observe import load_profile
            observe = load_profile(args.observatory, args.candidate)
            verify_capture(snapshot, raw, observe.core.parse_dump_bytes)
            result = check_snapshot(snapshot, result["output_sha256"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
