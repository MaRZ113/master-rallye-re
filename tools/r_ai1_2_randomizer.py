"""R-AI1.2 exact-build research bridge, config and evidence-limited oracles."""
from __future__ import annotations
import argparse
import json
import math
import struct
from pathlib import Path
from r_ai1_mixed_class import (REPOSITORY, RETAIL_SHA256, RETAIL_SIZE,
    ORIGINAL_TEXT_SIZE, TEXT_SIZE_OFFSET, apply_ranges, ignored_output, sha256,
    stock_class_local, stock_map, VEHICLES_SHA256, verify_capture)
from r_ai1_hardening import hardening_ranges, compose_ranges
from r_ai2_capacity import capacity_ranges
from patch_vehicle_slot25 import parse_pe, va_to_file_offset

MODES = ("QuickRace", "Challenge", "RallyeCup", "Invitation", "MasterRallye")
POLICIES = ("Stock", "Mixed", "Diverse")
MAX_CONFIG = 4096
PROFILE_SHA256 = {
    False: "60946990b685390032510c4bbed448674faebf33c929a46f52bc527e219dfc85",
    True: "32a09c466b9bb40513d8a801e0e9f420e902d6486ceb7ae76b243c7408404629",
}
BASE = 0x68E400  # R-AI2's separately audited 68E300..68E383 stays untouched.
LOADER = 0x68ED00
DLL_NAME = 0x68EE80
EXPORT_NAME = 0x68EEA0
EXPORT_CHALLENGE = 0x68EEC0
IAT = {"LoadLibraryA": 0x68F0B8, "GetProcAddress": 0x68F0C0,
       "GetModuleFileNameA": 0x68F178, "GetModuleHandleA": 0x68F238}


def config(data: bytes | None) -> dict[str, str]:
    result = dict.fromkeys(MODES, "Stock")
    if data is None or len(data) > MAX_CONFIG or b"\0" in data:
        return result
    try:
        # Mirror the bounded native V1 grammar, including its whitespace and
        # literal '=' rules; ConfigParser accepts extra syntax the DLL rejects.
        section = False
        values = {}
        for line in data.decode("ascii").split("\n"):
            line = line.strip(" \t\r")
            if not line or line[0] in ";#":
                continue
            if line.startswith("["):
                if section or line.casefold() != "[opponentrandomizer]":
                    return result
                section = True
                continue
            key, separator, value = line.partition("=")
            key, value = key.strip(" \t\r").casefold(), value.strip(" \t\r")
            if (not section or not separator or key in values or
                    key not in {m.casefold() for m in (*MODES, "ConfigVersion")}):
                return result
            values[key] = value
        if values.get("configversion") != "1":
            return result
        for mode in MODES:
            value = values.get(mode.casefold(), "").casefold()
            result[mode] = next((p for p in POLICIES if p.casefold() == value), "Stock")
    except UnicodeError:
        return dict.fromkeys(MODES, "Stock")
    return result


class Asm:
    def __init__(self, base):
        self.base, self.code, self.labels, self.fixups = base, bytearray(), {}, []
    def emit(self, value):
        self.code.extend(bytes.fromhex(value) if isinstance(value, str) else value)
    def label(self, name):
        self.labels[name] = self.base + len(self.code)
    def branch(self, op, target):
        self.emit(op); self.fixups.append((len(self.code), target)); self.emit(bytes(4))
    def call(self, target):
        self.branch("e8", target)
    def finish(self):
        for offset, target in self.fixups:
            destination = self.labels[target] if isinstance(target, str) else target
            struct.pack_into("<i", self.code, offset, destination - self.base - offset - 4)
        return bytes(self.code), self.labels


# Reuse only the chosen-ID/driver locals BEFORE their draw; never the saved
# EBX/EBP/ESI/EDI words at ESP+0..c. The x86 oracle checks all restored registers.
SPECS = (
    {"name": "QuickRace", "hint": 0, "base": BASE, "first": 0x84, "count": 0x88,
     "cls": 0x8C, "primary": 0x20, "remaining": 0x30, "endreg": "ebp", "slot": 0x14, "marker": 0x18,
     "pool": 0x458112, "init": (0x45810B, "8b84248c000000"),
     "loop": (0x458379, "8d4c2430e81e93fbff"),
     "end": (0x4582D5, "8a942494000000"), "getter": 0x4AC660},
    {"name": "MasterRallye", "hint": 4, "base": BASE + 0x300, "first": 0x88, "count": 0x8C,
     "cls": 0x90, "primary": 0x24, "remaining": 0x34, "endreg": "ebp", "slot": 0x14, "marker": 0x18,
     "pool": 0x451E97, "init": (0x451E90, "8b842490000000"),
     "loop": (0x4520D2, "8b44243885c0"),
     "end": (0x45202D, "8a8c2490000000"), "getter": 0x4B0630},
    {"name": "RallyeCup/Invitation", "hint": 2, "base": BASE + 0x600, "first": 0x84,
     "count": 0x88, "cls": 0x8C, "primary": 0x20, "remaining": 0x30, "endreg": "edi",
     "slot": 0x18, "marker": 0x14, "pool": 0x45ACD0, "init": (0x45AC79, "e8823a0500"),
     "loop": (0x45AF0F, "8b44243485c0"),
     "end": (0x45AE66, "8a8c248c000000"), "getter": 0x4B0630},
)


def selection_code(spec):
    a = Asm(spec["base"])
    slot, marker = spec["slot"], spec["marker"]
    a.label("init"); a.emit(bytes((0xc7, 0x44, 0x24, marker)) + bytes(4))
    if spec["hint"] == 2:
        a.call(0x4AE700)
    else:
        a.emit(spec["init"][1])
    a.branch("e9", spec["init"][0] + len(bytes.fromhex(spec["init"][1])))
    a.label("loop"); a.emit("9c608d54242456")  # EDX=original ESP, push slot
    a.emit(b"\x8b\x8a" + struct.pack("<I", spec["count"]))
    a.emit("518bc5" if spec["endreg"] == "ebp" else "518bc7")
    a.emit("2bc150")  # immutable first=end-count; campaign arg is later a log scratch
    a.emit(bytes((0x6a, spec["hint"])))
    a.call(LOADER)
    a.emit("83f802"); a.branch("0f87", "stock")  # -1/invalid => Stock
    a.emit(b"\x89\x84\x24" + struct.pack("<I", spec["cls"] + 36))
    a.emit("8944241c")
    a.emit(bytes((0x89, 0x74, 0x24, slot + 36)))
    if spec["hint"] != 0:
        a.emit("8b4c2408" if spec["endreg"] == "ebp" else "8b0c24")
        a.emit(b"\x89\x8c\x24" + struct.pack("<I", spec["first"] + 36))  # retain end in dead arg scratch
    if spec["hint"] == 0:
        for offset in (0x90, 0x94):
            a.emit(b"\xc7\x84\x24" + struct.pack("<I", offset + 36) + b"\xff" * 4)
    for vector in (spec["primary"], spec["remaining"]):
        a.emit(bytes((0x8d, 0x4c, 0x24, vector + 36))); a.call(0x41FA50)
    a.emit(bytes((0xc7, 0x44, 0x24, marker + 36)) + b"\xff"*4 + b"\x61\x9d")
    if spec["hint"] != 0:
        a.emit("31f6bdffffffffbfffffffff")
    if spec["hint"] == 2:
        # Invitation core T3 pool has no reward additions.
        a.emit("83f802"); a.branch("0f85", "cup_dispatch")
        a.emit("9c60"); a.call(0x4AE700); a.emit("8bc8"); a.call(0x4AE620)
        a.emit("83f805"); a.branch("0f85", "cup_normal")
        a.emit("619d"); a.branch("e9", 0x45AC8A)
        a.label("cup_normal"); a.emit("619d")
        a.label("cup_dispatch")
    a.branch("e9", spec["pool"])
    a.label("stock"); a.emit("619d")
    a.label("draw")
    if spec["hint"] == 0:
        a.emit("8d4c2430"); a.call(0x4116A0)
    else:
        a.emit(spec["loop"][1])
    a.branch("e9", spec["loop"][0] + len(bytes.fromhex(spec["loop"][1])))
    a.label("pool_end"); a.emit(bytes((0x9c,0x83,0x7c,0x24,marker+4,0xff))); a.branch("0f85", "initial_pool")
    a.emit("9d31ff")
    a.label("participant"); a.emit(bytes((0x3b,0x7c,0x24,slot))); a.branch("0f8d", "pool_ready")
    a.emit("57"); a.call(0x4ADA50 if spec["hint"] == 0 else 0x4B0AF0)
    a.emit("8bc8"); a.call(spec["getter"])
    a.emit(bytes((0x89,0x44,0x24,marker)))
    a.emit(bytes((0x8b, 0x6c, 0x24, spec["primary"] + 4)))
    a.label("filter")
    a.emit(bytes((0x3b, 0x6c, 0x24, spec["primary"] + 8)))
    a.branch("0f83", "next_participant")
    a.emit(bytes((0x8b,0x44,0x24,marker))+bytes.fromhex("394500")); a.branch("0f85", "next_vehicle")
    a.emit(bytes((0x55, 0x8d, 0x4c, 0x24, spec["primary"] + 4)))
    a.call(0x416620); a.branch("e9", "filter")
    a.label("next_vehicle"); a.emit("83c504"); a.branch("e9", "filter")
    a.label("next_participant"); a.emit("47"); a.branch("e9", "participant")
    a.label("pool_ready"); a.emit(bytes((0xc7,0x44,0x24,marker))+bytes(4)+bytes((0x8b,0x74,0x24,slot)))
    a.emit(b"\x8b\xac\x24" + struct.pack("<I", spec["first"]))
    if spec["hint"] == 0:
        a.emit(b"\x03\xac\x24" + struct.pack("<I", spec["count"]))
    if spec["endreg"] == "edi":
        a.emit("8bfd")
    a.branch("e9", "draw")
    a.label("initial_pool"); a.emit("9d"); a.emit(spec["end"][1])
    a.branch("e9", spec["end"][0] + len(bytes.fromhex(spec["end"][1])))
    code, labels = a.finish()
    if len(code) > 0x300:
        raise ValueError("Selector exceeded assigned interval")
    return code, labels


def loader_code():
    """Resolve only the DLL adjacent to EXE; bounded path, stdcall four args."""
    a = Asm(LOADER)
    a.emit("558bec53565781ec080100008bf4")
    a.emit("6804010000566a00ff15" + struct.pack("<I", IAT["GetModuleFileNameA"]).hex())
    a.emit("85c0"); a.branch("0f84", "fail")
    a.emit("3d04010000"); a.branch("0f83", "fail")
    a.emit("8d3c0631db")
    a.label("back"); a.emit("4f3bfe"); a.branch("0f82", "fail")
    a.emit("803f5c"); a.branch("0f84", "found")
    a.emit("803f2f"); a.branch("0f85", "back")
    a.label("found"); a.emit("478bdf2bde81fbec000000"); a.branch("0f87", "fail")
    a.emit("be" + struct.pack("<I", DLL_NAME).hex() + "b916000000f3a4")
    a.emit("54ff15" + struct.pack("<I", IAT["GetModuleHandleA"]).hex())
    a.emit("85c0"); a.branch("0f85", "loaded")
    a.emit("54ff15" + struct.pack("<I", IAT["LoadLibraryA"]).hex())
    a.emit("85c0"); a.branch("0f84", "fail")
    a.label("loaded"); a.emit("bb" + struct.pack("<I", EXPORT_NAME).hex())
    a.emit("837d0801"); a.branch("0f85", "resolve")
    a.emit("bb" + struct.pack("<I", EXPORT_CHALLENGE).hex())
    a.label("resolve"); a.emit("5350ff15" + struct.pack("<I", IAT["GetProcAddress"]).hex())
    a.emit("85c0"); a.branch("0f84", "fail")
    a.emit("ff7514ff7510ff750cff7508ffd0"); a.branch("e9", "done")
    a.label("fail"); a.emit("b8ffffffff")
    a.label("done"); a.emit("81c4080100005f5e5b5dc21000")
    return a.finish()[0]


def bridge_ranges():
    rows = []
    def row(va, old, new, purpose):
        rows.append({"offset": va - 0x400000, "va": va,
                     "original": old, "replacement": new, "purpose": purpose})
    for spec in SPECS:
        code, labels = selection_code(spec)
        for site, label in (("init", "init"), ("loop", "loop"), ("end", "pool_end")):
            va, oldhex = spec[site]; old = bytes.fromhex(oldhex)
            row(va, old, b"\xe9" + struct.pack("<i", labels[label] - va - 5) + b"\x90" * (len(old) - 5),
                spec["name"] + ": native pool " + label)
        row(spec["base"], bytes(len(code)), code, spec["name"] + ": active-count policy/class-pool reuse")
    a = Asm(0x68EE00); a.emit("8bbc38740500009c606a016a016a016a01"); a.call(LOADER)
    a.emit("83f818"); a.branch("0f87", "stock")
    a.emit("89442400")  # PUSHAD saved EDI=chosen ID
    a.label("stock"); a.emit("619d"); a.branch("e9", 0x450115)
    code = a.finish()[0]
    row(0x45010E, bytes.fromhex("8bbc3874050000"), b"\xe9" + struct.pack("<i", 0x68EE00 - 0x45010E - 5) + b"\x90\x90",
        "Challenge AI ID before stock registry-derived class; one-human branch only")
    row(0x68EE00, bytes(len(code)), code, "Challenge fixed-ID load always executes")
    code = loader_code(); row(LOADER, bytes(len(code)), code, "Bounded adjacent-DLL loader; absent module => Stock")
    strings = b"MRallyeRandomizer.dll\0".ljust(0x20, b"\0") + b"MRChooseV1\0".ljust(0x20, b"\0") + b"MRChallengeV1\0"
    row(DLL_NAME, bytes(len(strings)), strings, "Relative DLL/export names")
    end = max(r["va"] + len(r["replacement"]) for r in rows)
    rows.append({"offset": TEXT_SIZE_OFFSET, "va": None, "original": struct.pack("<I", ORIGINAL_TEXT_SIZE),
                 "replacement": struct.pack("<I", end - 0x401000), "purpose": "Declare bridge in existing text padding"})
    return rows


def ranges(five=False):
    groups = [hardening_ranges(), bridge_ranges()]
    if five:
        groups.append(capacity_ranges())
    result = groups[0]
    for group in groups[1:]:
        result = compose_ranges(result, group)
    return result


def build(source: bytes, five=False):
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError("Require exact pristine retail SHA256/size")
    pe = parse_pe(source); patch = ranges(five)
    for row in patch:
        if row["va"] is not None and va_to_file_offset(pe, row["va"]) != row["offset"]:
            raise ValueError("Unexpected PE target layout")
    output = apply_ranges(source, patch, RETAIL_SHA256)
    if sha256(output) != PROFILE_SHA256[five]:
        raise ValueError("Output differs from pinned R-AI1.2 profile")
    result = {"phase": "R-AI1.2", "profile": "retail-r-ai1-2-" + ("five" if five else "four") + "-hardened",
        "status": "PREPARED_RUNTIME_UNTESTED", "source_sha256": RETAIL_SHA256,
        "output_sha256": sha256(output), "size": len(output), "randomizer_changes_count": False,
        "capacity_composed": five, "max_supported_total": 5, "policy_version": 1,
        "broker_dump_variant": "native_hardened",
        "ranges": [{**{k: v for k, v in r.items() if k not in ("original", "replacement")},
                    "length": len(r["original"]), "original_hex": r["original"].hex(),
                    "replacement_hex": r["replacement"].hex()} for r in patch]}
    return output, result


def verify(candidate: bytes, five=False):
    if len(candidate) != RETAIL_SIZE:
        raise ValueError("Unexpected candidate size")
    restored = bytearray(candidate)
    for row in ranges(five):
        begin = row["offset"]; end = begin + len(row["original"])
        if candidate[begin:end] != row["replacement"]:
            raise ValueError("Replacement mismatch")
        restored[begin:end] = row["original"]
    output, result = build(bytes(restored), five)
    if output != candidate:
        raise ValueError("Inverse/reproduction mismatch")
    return result


def roster(snapshot, mode, policy, expected_count, player_id):
    """CLI requires verified JSON/raw provenance. Never proves actors."""
    entries = snapshot["entries"]
    def get(path):
        values = [r["value"] for r in entries if r["path"] == path]
        if len(values) != 1: raise ValueError("Missing/ambiguous " + path)
        return values[0]
    types = {"QuickRace": 2, "Challenge": 7, "RallyeCup": 6, "Invitation": 8, "MasterRallye": 5}
    if mode not in types or policy not in POLICIES or type(expected_count) is not int or not 1 <= expected_count <= 5:
        raise ValueError("Unsupported mode/policy/count")
    for path, expected in {"Race/NumCars": expected_count, "Race/NumPlayers": 1,
        "Race/NumNetworkPlayers": 0, "Race/Type": types[mode],
        "Race/AttractMode": False, "Race/PlaybackReplay": False}.items():
        value = get(path)
        if type(value) is not type(expected) or value != expected: raise ValueError("Unexpected " + path)
    cars = []
    for n in range(expected_count):
        row = {key: get(f"Race/Car{n}/{key}") for key in ("CarID", "CarClass", "DriverID", "PlayerType")}
        if stock_class_local(row["CarID"])[0] != row["CarClass"] or type(row["CarClass"]) is not int:
            raise ValueError("ID/class inconsistency")
        if row["PlayerType"] != (1 if n == 0 else 2) or type(row["PlayerType"]) is not int:
            raise ValueError("Human/AI mismatch")
        if type(row["DriverID"]) is not int or (row["DriverID"] != 30 if n == 0 else not 0 <= row["DriverID"] < 10):
            raise ValueError("Unexpected driver identity")
        cars.append(row)
    duplicate = len({r["CarID"] for r in cars}) != len(cars)
    if cars[0]["CarID"] != player_id or (duplicate and not (mode == "Challenge" and policy == "Stock")):
        raise ValueError("Player changed or duplicate IDs")
    classes = [r["CarClass"] for r in cars[1:]]
    if len({c["DriverID"] for c in cars[1:]}) != len(cars)-1:
        raise ValueError("Duplicate AI drivers")
    if policy == "Stock" and mode != "Challenge" and any(c != cars[0]["CarClass"] for c in classes):
        raise ValueError("Stock class-pool mismatch")
    if policy == "Diverse" and any(len(set(classes[i:i + 3])) != len(classes[i:i + 3]) for i in range(0, len(classes), 3)):
        raise ValueError("Diverse cycle violated")
    families = stock_map()
    canaries = json.loads((REPOSITORY / "research/r-ai1-1/vehicle-physics-canaries.json").read_text())
    if canaries["source_sha256"] != VEHICLES_SHA256:
        raise ValueError("Wrong canonical physics source")
    identity = []
    for n, car in enumerate(cars):
        observed = {}
        paths = {f"Race/Car{n}/{k}": families[car["CarID"]]["family"] for k in ("CarType", "WheelType")}
        paths.update({f"Vehicles/Car{n}/{k}": v for k, v in canaries["vehicles"][car["CarID"]]["values"].items()})
        for path, expected in paths.items():
            if not any(e["path"] == path for e in entries):
                continue
            value = get(path)
            matches = (isinstance(value, str) and value.casefold() == expected.casefold()) if isinstance(expected, str) else (
                type(value) in (int, float) and math.isclose(value, expected, abs_tol=0.0001))
            if not matches:
                raise ValueError("Registry/materialization mismatch: " + path)
            observed[path] = value
        identity.append(observed)
    counts = {f"{prefix}/Car{n}": sum(e["path"].startswith(f"{prefix}/Car{n}/") for e in entries)
              for prefix in ("Vehicles", "Physics", "Controller", "Network") for n in range(expected_count)}
    return {"status": "BROKER_STATE_MATCH_ONLY", "runtime_full_pass": False,
            "mode": mode, "policy": policy, "participants": cars,
            "duplicate_policy": "native_fixed_pair" if mode == "Challenge" and policy == "Stock" else "exclude_prior_ids",
            "available_identity_checks": identity, "subsystem_path_counts_not_actor_proof": counts}


def verify_module(binary, manifest):
    # Pinned by the checked-in build summary; generated manifests cannot grant
    # unknown modules support merely by asserting their own checksum.
    canonical = json.loads((REPOSITORY / "research/r-ai1-2/build-summary.json").read_text())
    expected = canonical["module"]
    if (len(binary) != expected["size"] or sha256(binary) != expected["sha256"] or
            manifest.get("phase") != "R-AI1.2" or manifest.get("implementation_version") != 1 or
            manifest.get("module_sha256") != expected["sha256"] or manifest.get("module_size") != expected["size"] or
            manifest.get("source_hashes") != expected["source_hashes"]):
        raise ValueError("Unknown module or manifest")
    for relative, digest in expected["source_hashes"].items():
        if sha256((REPOSITORY / relative).read_bytes()) != digest:
            raise ValueError("Module source differs from verified build")
    profiles = manifest.get("supported_profiles", [])
    if ([p.get("output_sha256") for p in profiles] != [PROFILE_SHA256[False], PROFILE_SHA256[True]] or
            any(p.get("source_sha256") != RETAIL_SHA256 or p.get("size") != RETAIL_SIZE for p in profiles)):
        raise ValueError("Unexpected module supported profiles")
    return {"module_sha256": expected["sha256"], "module_size": expected["size"], "implementation_version": 1}


def log_generation(data, mode, policy, config_hash, classes):
    """Separate DLL diagnostic provenance; never label these lines native Dump."""
    if len(data) > 131072:
        raise ValueError("Oversize diagnostic log")
    groups, group = [], []
    for line in data.decode("ascii").splitlines():
        tokens = line.split()
        if len(tokens) not in (5, 6):
            raise ValueError("Malformed module diagnostic")
        name, selected_policy, count, slot, cls = tokens[:5]
        if name not in MODES or selected_policy not in POLICIES or not count.isdigit() or not slot.isdigit():
            raise ValueError("Invalid diagnostic context")
        count, slot = int(count), int(slot)
        if not 1 <= count <= 4 or not 1 <= slot <= count or cls not in ("-", "0", "1", "2"):
            raise ValueError("Invalid diagnostic selection")
        digest = tokens[5] if len(tokens) == 6 else ""
        if digest and (len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("Invalid diagnostic config hash")
        row = (name, selected_policy, count, slot, cls, digest)
        if slot == 1:
            group = []
        if group and (row[:3] != group[0][:3] or digest != group[0][5] or slot != len(group) + 1):
            group = []
        if slot == len(group) + 1:
            group.append(row)
            if len(group) == count:
                groups.append(group)
    wanted = ["-" if policy == "Stock" else str(c) for c in classes]
    matches = [g for g in groups if g[0][:3] == (mode, policy, len(classes)) and
               g[0][5] == config_hash and [r[4] for r in g] == wanted]
    if not matches:
        raise ValueError("No complete generation matching mode/count/config/Broker classes")
    return {"status": "MODULE_LOG_MATCH_ONLY", "complete_generations": len(groups),
            "matching_generations": len(matches), "log_sha256": sha256(data), "native_dump": False}


def summarize(reports):
    if not reports or any(r.get("status") != "BROKER_STATE_MATCH_ONLY" for r in reports):
        raise ValueError("Need verified checker reports")
    if len({(r["mode"], r["policy"], len(r["participants"])) for r in reports}) != 1:
        raise ValueError("Variation samples must use the same mode/policy/count")
    ids = [tuple(c["CarID"] for c in r["participants"][1:]) for r in reports]
    classes = [tuple(c["CarClass"] for c in r["participants"][1:]) for r in reports]
    return {"status": "BROKER_SAMPLE_SUMMARY_ONLY", "runtime_full_pass": False,
            "samples": len(reports), "ai_ids_vary": len(set(ids)) > 1,
            "ai_classes_vary": len(set(classes)) > 1,
            "fresh_generation_requires_lifecycle_evidence": True,
            "rng_uniformity_proven": False}


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        q = sub.add_parser(name); q.add_argument("input", type=Path); q.add_argument("--five", action="store_true")
        if name == "build": q.add_argument("--output", type=Path, required=True)
    q = sub.add_parser("check-race"); q.add_argument("snapshot", type=Path); q.add_argument("--raw", type=Path, required=True)
    q.add_argument("--candidate", type=Path, required=True); q.add_argument("--five", action="store_true")
    q.add_argument("--config", type=Path, required=True); q.add_argument("--mode", choices=MODES, required=True)
    q.add_argument("--observatory", type=Path, required=True)
    q.add_argument("--module", type=Path, required=True); q.add_argument("--module-manifest", type=Path, required=True)
    q.add_argument("--log", type=Path, required=True, help="Preserved module log, separate from native Dump")
    q.add_argument("--count", type=int, required=True); q.add_argument("--player", type=int, required=True)
    q = sub.add_parser("verify-module"); q.add_argument("module", type=Path); q.add_argument("manifest", type=Path)
    q = sub.add_parser("compare-roster"); q.add_argument("before", type=Path); q.add_argument("after", type=Path)
    q = sub.add_parser("summarize-mode"); q.add_argument("reports", nargs="+", type=Path)
    args = p.parse_args()
    if args.command == "build":
        output, report = build(args.input.read_bytes(), args.five)
        dest = ignored_output(args.output); dest.mkdir(parents=True, exist_ok=True)
        (dest / "MRallye.exe").write_bytes(output)
        (dest / "patch-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    elif args.command == "verify": report = verify(args.input.read_bytes(), args.five)
    elif args.command == "verify-module":
        report = verify_module(args.module.read_bytes(), json.loads(args.manifest.read_text()))
    elif args.command == "check-race":
        report = verify(args.candidate.read_bytes(), args.five)
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8")); raw = args.raw.read_bytes()
        from r_ai1_observe import load_profile
        observe = load_profile(args.observatory, args.candidate)
        verify_capture(snapshot, raw, observe.core.parse_dump_bytes)
        module = json.loads(args.module_manifest.read_text())
        verify_module(args.module.read_bytes(), module)
        if source_fresh := snapshot["source"].get("freshness"):
            if source_fresh != "post_baseline_complete_dump_proven":
                raise ValueError("Need fresh native Dump at known lifecycle point")
        else:
            raise ValueError("Missing capture freshness evidence")
        source = snapshot["source"]
        if source.get("image_sha256") != report["output_sha256"] or source.get("build_profile") != report["profile"]:
            raise ValueError("Capture candidate identity mismatch")
        data = args.config.read_bytes(); result = roster(snapshot, args.mode, config(data)[args.mode], args.count, args.player)
        provenance = log_generation(args.log.read_bytes(), args.mode, result["policy"], sha256(data),
                                    [c["CarClass"] for c in result["participants"][1:]]) if args.count > 1 else None
        report = {**result, "candidate_sha256": report["output_sha256"], "config_sha256": sha256(data),
                  "module_sha256": module["module_sha256"], "implementation_version": 1,
                  "module_log_provenance": provenance}
    elif args.command == "summarize-mode":
        report = summarize([json.loads(p.read_text()) for p in args.reports])
    else:
        before = json.loads(args.before.read_text()); after = json.loads(args.after.read_text())
        if any(r.get("status") != "BROKER_STATE_MATCH_ONLY" for r in (before, after)):
            raise ValueError("Need verified checker reports")
        if any(before.get(k) != after.get(k) for k in ("mode","candidate_sha256","module_sha256","implementation_version")):
            raise ValueError("Roster comparison requires the same mode/build/module")
        equal = before["participants"] == after["participants"]
        report = {"status": "BROKER_ROSTER_COMPARISON_ONLY", "equal": equal, "runtime_full_pass": False}
        if not equal: raise ValueError("Persisted roster differs")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
