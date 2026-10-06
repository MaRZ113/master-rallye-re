"""R-AI1/R-AI1.1: exact retail research selectors, stock mapping and offline oracles.

No process-memory writes, assets, registry changes or capacity changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
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
                           "Race/Type": 2, "Race/NumNetworkPlayers": 0,
                           "Race/NetworkSyncActive": False,
                           "Frontend/Active": True, "Frontend/QuickRace/Track": 10}.items():
        value = get(path)
        if type(value) is not type(expected) or value != expected:
            raise ValueError(f"Unexpected {path}: {value!r}")
    # The key is registered by retail but absent from the supplied live Dump.
    # Reject an explicit network value when present; use actual live offline
    # counters above rather than inventing a mandatory exported path.
    networked = [row for row in entries if row["path"] == "Race/Networked"]
    if networked and (len(networked) != 1 or networked[0]["value"] is not False):
        raise ValueError("Unexpected Race/Networked")
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
                 row["path"] in ("Race/RaceID", "Race/RaceName", "Frontend/Running")}
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



# R-AI1.1 reuses the native inline class-pool builder and original driver loop.
GENERAL_SHA256 = "f9e8e556842602252ec39b2174e796f6cb67651d8f573f2565f9d2e5569bd9ac"
GENERAL_BASE = 0x0068E300
VEHICLES_SHA256 = "a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0"
POOL_START = 0x00458112
POOL_JOIN = 0x004582DC
DRAW_JOIN = 0x00458382
GENERAL_SITES = ((0x0045810B, bytes.fromhex("8b84248c000000")),
                 (0x00458379, bytes.fromhex("8d4c2430e81e93fbff")),
                 (0x004582D5, bytes.fromhex("8a942494000000")))


def physics_canary_table(path: Path) -> dict:
    from scanner.r5v_a_inventory import xml_values
    if sha256(path.read_bytes()) != VEHICLES_SHA256:
        raise ValueError("Need exact protected retail vehicles.xml")
    values = {item["Name"].casefold(): item["Value"] for item in xml_values(path)}
    suffixes = ("Dimensions/WheelBase", "Dimensions/TrackWidthFront", "Engine/GearRatioDiff")
    return {"source_sha256": VEHICLES_SHA256, "evidence": "CONFIRMED_BY_CORPUS",
            "vehicles": [{"id": row["id"], "family": row["family"],
                          "values": {key: float(values[f"Vehicles/{row['family']}/{key}".casefold()])
                                     for key in suffixes}} for row in stock_map()]}


def class_plan(policy: str, player_class: int, draws=(0, 1, 2)) -> tuple[int, ...]:
    if type(player_class) is not int or player_class not in (0, 1, 2):
        raise ValueError("Invalid stock player class")
    if policy == "stock":
        return (player_class,) * 3
    if policy == "diverse":
        return (2, 1, 0)
    if policy != "mixed" or len(draws) != 3 or any(type(n) is not int or n not in (0, 1, 2) for n in draws):
        raise ValueError("Need three valid independent class draws")
    return tuple(draws)


def general_code(policy="mixed") -> tuple[bytes, dict]:
    if policy not in ("mixed", "diverse"):
        raise ValueError("Only research MIXED/DIVERSE code; STOCK is pristine")
    code = bytearray()
    labels, fixups = {}, []
    def emit(value):
        code.extend(bytes.fromhex(value))
    def label(name):
        labels[name] = GENERAL_BASE + len(code)
    def branch(op, target):
        emit(op)
        fixups.append((len(code), target))
        code.extend(bytes(4))
    def call(address):
        branch("e8", address)
    label("init")
    emit("c744241800000000")  # initialize scratch marker before first pool build
    code.extend(GENERAL_SITES[0][1])
    branch("e9", POOL_START)
    label("loop")
    emit("9c60")  # preserve all incoming registers/flags; original ESP+36
    emit("83bc24a800000001"); branch("0f85", "stock_draw")
    emit("83bc24ac00000003"); branch("0f85", "stock_draw")
    emit("83fe01"); branch("0f82", "stock_draw")
    emit("83fe03"); branch("0f87", "stock_draw")
    call(0x4ADA50); emit("8bc8"); call(0x4ABE90)
    emit("83f802"); branch("0f85", "stock_draw")
    if policy == "mixed":
        emit("6a036a00"); call(0x4D1E90); emit("8bc8"); call(0x4D1DF0)
    else:
        emit("b8030000002bc6")  # diverse: independent inputs Car1/2/3 =2/1/0
    emit("83f802"); branch("0f87", "stock_draw")
    # Keep the native remaining pool if its class matches; no class RNG reads it.
    emit("3b8424b0000000"); branch("0f84", "stock_draw")
    emit("898424b00000008944241c89742438")  # class cache, saved EAX, current slot
    emit("c78424b4000000ffffffffc78424b8000000ffffffff")
    emit("8d4c2444"); call(0x41FA50)  # clear eligible/used vector (retain allocation)
    emit("8d4c2454"); call(0x41FA50)  # clear remaining vector
    emit("c744243cffffffff619d")  # marker at original ESP+18; restore frame
    branch("e9", POOL_START)  # stock class cases, no driver-pool reconstruction
    label("stock_draw")
    emit("619d")
    label("draw")
    emit("8d4c2430"); call(0x4116A0)
    branch("e9", DRAW_JOIN)
    label("pool_end")
    emit("9c837c241cff"); branch("0f85", "initial_pool")
    emit("9d31ff")  # filter already configured Car0..currentSlot-1
    label("participant")
    emit("3b7c2414"); branch("0f8d", "pool_ready")
    emit("57"); call(0x4ADA50); emit("8bc8"); call(0x4AC660)
    emit("894424188b6c2424")  # prior CarID and eligible iterator
    label("filter")
    emit("3b6c2428"); branch("0f83", "next_participant")
    emit("8b442418394500"); branch("0f85", "next_vehicle")
    emit("558d4c2424"); call(0x416620)  # stock vector erase; EBP preserved
    branch("e9", "filter")
    label("next_vehicle")
    emit("83c504"); branch("e9", "filter")
    label("next_participant")
    emit("47"); branch("e9", "participant")
    label("pool_ready")
    emit("c7442418000000008b7424148bac248400000003ac2488000000")
    branch("e9", "draw")
    label("initial_pool")
    emit("9d"); code.extend(GENERAL_SITES[2][1])
    branch("e9", POOL_JOIN)
    for offset, target in fixups:
        destination = labels[target] if isinstance(target, str) else target
        struct.pack_into("<i", code, offset, destination - (GENERAL_BASE + offset + 4))
    return bytes(code), labels


def general_ranges(policy="mixed") -> list[dict]:
    code, labels = general_code(policy)
    ranges = [{"offset": TEXT_SIZE_OFFSET, "va": None,
               "original": struct.pack("<I", ORIGINAL_TEXT_SIZE),
               "replacement": struct.pack("<I", GENERAL_BASE + len(code) - 0x401000),
               "purpose": "Declare research code in existing text padding; same pages/image"}]
    for (address, old), label in zip(GENERAL_SITES, ("init", "loop", "pool_end")):
        ranges.append({"offset": address - 0x400000, "va": address, "original": old,
                       "replacement": b"\xe9" + struct.pack("<i", labels[label] - address - 5) + b"\x90" * (len(old) - 5),
                       "purpose": "Native class-pool reuse: " + label})
    ranges.append({"offset": GENERAL_BASE - 0x400000, "va": GENERAL_BASE,
                   "original": bytes(len(code)), "replacement": code,
                   "purpose": "Independent class policy, stock pool/erase/draw/driver/publication"})
    return ranges


def build_general(source: bytes, policy="mixed") -> tuple[bytes, dict]:
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError("R-AI1.1 requires exact pristine retail")
    ranges = [] if policy == "stock" else general_ranges(policy)
    pe = parse_pe(source)
    for row in ranges:
        if row["va"] is not None and va_to_file_offset(pe, row["va"]) != row["offset"]:
            raise ValueError("Unexpected target layout")
    result = apply_ranges(source, ranges, RETAIL_SHA256)
    if policy == "mixed" and sha256(result) != GENERAL_SHA256:
        raise ValueError("R-AI1.1 MIXED profile changed; audit required")
    manifest = {"phase": "R-AI1.1", "policy": policy, "source_sha256": RETAIL_SHA256,
                "output_sha256": sha256(result), "image_size": RETAIL_SIZE,
                "num_cars_changed": False, "guards": {"first_ai": 1, "count": 3, "race_type": 2},
                "ranges": [{**{k: v for k, v in row.items() if k not in ("original", "replacement")},
                            "original_hex": row["original"].hex(), "replacement_hex": row["replacement"].hex()}
                           for row in ranges]}
    return result, manifest


def verify_general(candidate: bytes) -> dict:
    if len(candidate) != RETAIL_SIZE or sha256(candidate) != GENERAL_SHA256:
        raise ValueError("Need exact R-AI1.1 MIXED image")
    source = bytearray(candidate)
    for row in general_ranges():
        begin, old, new = row["offset"], row["original"], row["replacement"]
        if candidate[begin:begin + len(new)] != new:
            raise ValueError("Generalized candidate original-byte/manifest mismatch")
        source[begin:begin + len(old)] = old
    _, manifest = build_general(bytes(source))
    return manifest


def check_general_snapshot(snapshot: dict, image_hash: str) -> dict:
    from r_ai1_hardening import MIXED_SHA256, PROFILES
    source = snapshot.get("source", {})
    if (image_hash not in (GENERAL_SHA256, MIXED_SHA256) or source.get("image_sha256") != image_hash or
            snapshot.get("kind") != "master-rallye-broker-dump-snapshot" or
            snapshot.get("schema_version") != 1 or
            source.get("freshness") != "post_baseline_complete_dump_proven" or
            not re.fullmatch(r"mixed-random-race-[1-9][0-9]*", source.get("label", ""))):
        raise ValueError("Need a fresh active-race capture of the exact R-AI1.1 profile")
    if image_hash == MIXED_SHA256 and (source.get("build_profile") != PROFILES["mixed"] or
                                     source.get("broker_dump_variant") != "native_hardened"):
        raise ValueError("Hardened capture provenance is missing or inconsistent")
    entries = snapshot["entries"]
    def get(path):
        values = [item["value"] for item in entries if item["path"] == path]
        if len(values) != 1:
            raise ValueError(f"Missing/ambiguous Broker path: {path}")
        return values[0]
    guards = {"Race/NumCars": 4, "Race/NumPlayers": 1, "Race/Type": 2,
              "Race/NumNetworkPlayers": 0, "Race/NetworkSyncActive": False,
              "Race/AttractMode": False, "Frontend/Active": True,
              "Frontend/QuickRace/Car0": 0, "Frontend/QuickRace/Mode": 2,
              "Frontend/QuickRace/NumOpponents": 3, "Frontend/QuickRace/Ghost": 0}
    for path, expected in guards.items():
        value = get(path)
        if type(value) is not type(expected) or value != expected:
            raise ValueError(f"Unexpected {path}: {value!r}")
    if any(item["path"] == "Race/Networked" and item["value"] is not False for item in entries):
        raise ValueError("Explicit networked state")
    families = stock_map()
    canaries = json.loads((REPOSITORY / "research/r-ai1-1/vehicle-physics-canaries.json").read_text())
    if canaries["source_sha256"] != VEHICLES_SHA256:
        raise ValueError("Wrong canonical physics source")
    participants = []
    for n in range(4):
        row = {key: get(f"Race/Car{n}/{key}") for key in
               ("CarID", "CarClass", "PlayerType", "DriverID", "CarType", "WheelType")}
        cls, _ = stock_class_local(row["CarID"])
        if type(row["CarClass"]) is not int or row["CarClass"] != cls:
            raise ValueError(f"Car{n} ID/class mismatch")
        if type(row["PlayerType"]) is not int or row["PlayerType"] != (1 if n == 0 else 2):
            raise ValueError(f"Car{n} player type mismatch")
        driver = row["DriverID"]
        if type(driver) is not int or (driver != 30 if n == 0 else not 0 <= driver < 10):
            raise ValueError(f"Car{n} driver invalid")
        if n == 0 and row["CarID"] != 0:
            raise ValueError("Controlled normal human ID0 changed")
        if row["CarID"] > 20:
            raise ValueError("Fresh-profile protocol has no bonus vehicle unlocks")
        for key in ("CarType", "WheelType"):
            if str(row[key]).casefold() != families[row["CarID"]]["family"].casefold():
                raise ValueError(f"Car{n} {key} mismatches registry")
        physics = canaries["vehicles"][row["CarID"]]
        if physics["id"] != row["CarID"] or physics["family"] != families[row["CarID"]]["family"]:
            raise ValueError("Canonical canary table inconsistent")
        for suffix, expected in physics["values"].items():
            value = get(f"Vehicles/Car{n}/" + suffix)
            if type(value) not in (int, float) or not math.isclose(value, expected, abs_tol=0.0001):
                raise ValueError(f"Car{n} named-physics mismatch: {suffix}")
        row["named_physics"] = physics["values"]
        participants.append(row)
    if len({row["CarID"] for row in participants}) != 4:
        raise ValueError("CarID alias")
    if len({row["DriverID"] for row in participants[1:]}) != 3:
        raise ValueError("AI DriverID alias")
    counts = {f"{prefix}/Car{n}": sum(item["path"].startswith(f"{prefix}/Car{n}/") for item in entries)
              for prefix in ("Vehicles", "Physics", "Controller", "Network") for n in range(4)}
    return {"status": "BROKER_STATE_MATCH_ONLY", "runtime_full_pass": False,
            "label": source["label"], "participants": participants,
            "course": get("Frontend/QuickRace/Track"),
            "subsystem_path_counts_not_actor_proof": counts,
            "human_evidence_required": ["own models/wheels/collision", "AI movement/progress",
                                        "one normal finish/results/icons/frontend return"],
            "post_results_dump": ("NATIVE_NULL_GUARDS_PREPARED; human hardening smoke pending"
                                  if image_hash == MIXED_SHA256 else
                                  "UNSAFE; restart process before further native Dump")}


def summarize_general(reports: list[dict]) -> dict:
    if len(reports) < 5 or len({r["label"] for r in reports}) != len(reports):
        raise ValueError("Need at least five distinct active-race capture labels")
    if len({report["course"] for report in reports}) != 1:
        raise ValueError("Use the same course for the controlled samples")
    classes = {tuple(p["CarClass"] for p in r["participants"][1:]) for r in reports}
    ids = {tuple(p["CarID"] for p in r["participants"][1:]) for r in reports}
    non_player = sum(p["CarClass"] != r["participants"][0]["CarClass"]
                     for r in reports for p in r["participants"][1:])
    checks = {"ai_class_assignments_vary": len(classes) > 1,
              "ai_ids_vary": len(ids) > 1, "two_non_player_class_outcomes": non_player >= 2,
              "simultaneous_mixed_classes": any(len({p["CarClass"] for p in r["participants"]}) > 1 for r in reports)}
    return {"status": "BROKER_SAMPLING_MATCH_ONLY" if all(checks.values()) else "MORE_SAMPLES_NEEDED",
            "runtime_full_pass": False, "checks": checks, "non_player_outcomes": non_player,
            "samples": reports,
            "limitation": "Distinct labels cannot prove new race creations; human protocol and lifecycle observations required"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("map")
    physics_map_cli = sub.add_parser("physics-map")
    physics_map_cli.add_argument("vehicles", type=Path)
    build = sub.add_parser("build")
    build.add_argument("source", type=Path)
    build.add_argument("output", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("candidate", type=Path)
    build_general_cli = sub.add_parser("build-general")
    build_general_cli.add_argument("source", type=Path)
    build_general_cli.add_argument("output", type=Path)
    verify_general_cli = sub.add_parser("verify-general")
    verify_general_cli.add_argument("candidate", type=Path)
    summarize = sub.add_parser("summarize-general")
    summarize.add_argument("candidate", type=Path)
    summarize.add_argument("snapshots", nargs="+", type=Path)
    summarize.add_argument("--observatory", required=True, type=Path)
    check = sub.add_parser("check")
    check.add_argument("candidate", type=Path)
    check.add_argument("snapshot", type=Path)
    check.add_argument("--observatory", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "map":
        result = stock_map()
    elif args.command == "physics-map":
        result = physics_canary_table(args.vehicles)
    elif args.command in ("build", "build-general"):
        output = ignored_output(args.output)
        builder = build_general if args.command == "build-general" else build_candidate
        data, result = builder(args.source.read_bytes())
        if output.exists() or output.with_suffix(".manifest.json").exists():
            raise ValueError("Refusing to overwrite an existing candidate or manifest")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        output.with_suffix(".manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    else:
        verifier = verify_general if args.command in ("verify-general", "summarize-general") else verify_candidate
        if args.command == "summarize-general":
            from r_ai1_hardening import MIXED_SHA256, verify as verify_hardening
            if sha256(args.candidate.read_bytes()) == MIXED_SHA256:
                verifier = verify_hardening
        result = verifier(args.candidate.read_bytes())
        if args.command in ("check", "summarize-general"):
            from r_ai1_observe import load_profile
            observe = load_profile(args.observatory, args.candidate)
            reports = []
            for path in ([args.snapshot] if args.command == "check" else args.snapshots):
                snapshot = json.loads(path.read_text(encoding="utf-8"))
                sidecar = snapshot["source"]["raw_sidecar"]
                if Path(sidecar).name != sidecar:
                    raise ValueError("Invalid raw sidecar name")
                verify_capture(snapshot, path.with_name(sidecar).read_bytes(), observe.core.parse_dump_bytes)
                checker = check_snapshot if args.command == "check" else check_general_snapshot
                reports.append(checker(snapshot, result["output_sha256"]))
            result = reports[0] if args.command == "check" else summarize_general(reports)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
