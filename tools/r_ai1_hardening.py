"""Exact pristine retail hardening, optionally composed with the existing MIXED policy.

Research files only; no live writes or public Observatory modifications.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from r_ai1_mixed_class import (RETAIL_SHA256, RETAIL_SIZE, ORIGINAL_TEXT_SIZE,
                              TEXT_SIZE_OFFSET, apply_ranges, general_ranges,
                              ignored_output, sha256)
from patch_vehicle_slot25 import parse_pe, va_to_file_offset

BASE_SHA256 = "bbb9f0a8bb2523adf125582d16512c25f9b51db7a4104ee5edf8f7251865ae00"
MIXED_SHA256 = "603f0c06ca2a502367baa7e49fcaeab9e2ab9a7d6c47dd46ed82ca27cb9840a1"
STRING_CAVE = 0x68E2A0
XML_CAVE = 0x68E2C0
PROFILES = {"base": "retail-rbase-hardened", "mixed": "retail-r-ai1-1-hardened"}


def jump(site: int, destination: int) -> bytes:
    return b"\xe9" + struct.pack("<i", destination - site - 5)


def hardening_ranges() -> list[dict]:
    string = (b"\x85\xdb\x0f\x84" + struct.pack("<i", 0x602040 - STRING_CAVE - 8) +
              bytes.fromhex("8b7b043b7b08") + jump(STRING_CAVE + 14, 0x602024))
    # Preserve flags for both continuations; replay the virtual call only if EAX != 0.
    xml = (bytes.fromhex("9c85c00f84") + struct.pack("<i", XML_CAVE + 22 - XML_CAVE - 9) +
           bytes.fromhex("9d8b108bc8ff520c") + jump(XML_CAVE + 17, 0x60215A) +
           b"\x9d" + jump(XML_CAVE + 23, 0x60218E))
    def row(va, old, new, purpose, continuation, evidence):
        return {"offset": va - 0x400000, "va": va, "rva": va - 0x400000,
                "original": old, "replacement": new, "purpose": purpose,
                "continuation": continuation, "evidence": evidence}
    return [
        {"offset": TEXT_SIZE_OFFSET, "va": None, "rva": None,
         "original": struct.pack("<I", ORIGINAL_TEXT_SIZE),
         "replacement": struct.pack("<I", XML_CAVE + len(xml) - 0x401000),
         "purpose": "Declare guards in existing executable text padding; same aligned pages"},
        row(0x464F69, bytes.fromhex("68841f6b00"), jump(0x464F69, 0x464F46),
            "loading_attract_legacy_media_check_neutralization", 0x464F46,
            "464E40 odd counter -> stat/size failure -> 464F69; stock success sets Starter1"),
        row(0x60201E, bytes.fromhex("8b7b043b7b08"), jump(0x60201E, STRING_CAVE) + b"\x90",
            "broker_dump_null_stringlist_guard", STRING_CAVE,
            "4DE1C0 accepts NULL; 47D340/47D400 set NULL lists; Dump dereferences EBX"),
        row(STRING_CAVE, bytes(len(string)), string,
            "StringList NULL joins stock allocated-empty cleanup; non-NULL replays MOV/CMP",
            0x602024, "NULL -> 602040 closes brace, restores indent and continues next entry"),
        row(0x602153, bytes.fromhex("8b108bc8ff520c"), jump(0x602153, XML_CAVE) + b"\x90\x90",
            "broker_dump_null_xmldata_guard", XML_CAVE,
            "4DDA10 explicitly returns NULL; 4DE480/4D84C0 accept it, editor forwards getter"),
        row(XML_CAVE, bytes(len(xml)), xml,
            "XmlData NULL uses existing no-root continuation; non-NULL replays virtual call",
            0x60215A, "NULL -> 60218E; preserve flags; no text grammar change"),
    ]


def compose_ranges(hardening: list[dict], chooser: list[dict]) -> list[dict]:
    """Only the audited four-byte .text VirtualSize header may be shared."""
    rows = [dict(row) for row in hardening]
    for incoming in chooser:
        overlap = [row for row in rows if max(row["offset"], incoming["offset"]) <
                   min(row["offset"] + len(row["original"]), incoming["offset"] + len(incoming["original"]))]
        if overlap:
            if (len(overlap) != 1 or incoming["offset"] != TEXT_SIZE_OFFSET or
                    overlap[0]["offset"] != TEXT_SIZE_OFFSET or
                    incoming["va"] is not None or overlap[0]["va"] is not None or
                    incoming["original"] != struct.pack("<I", ORIGINAL_TEXT_SIZE) or
                    overlap[0]["original"] != incoming["original"] or
                    len(incoming["replacement"]) != 4 or len(overlap[0]["replacement"]) != 4):
                raise ValueError("Unexpected hardening/chooser range overlap")
            header = overlap[0]
            header["replacement"] = struct.pack("<I", max(struct.unpack("<I", row["replacement"])[0]
                                                          for row in (header, incoming)))
            header["purpose"] = "Explicit shared VirtualSize merge: maximum declared guard/chooser end"
        else:
            rows.append(dict(incoming))
    return sorted(rows, key=lambda row: row["offset"])


def ranges_for(profile: str) -> list[dict]:
    if profile not in PROFILES:
        raise ValueError("Only exact base/mixed hardening profiles are supported")
    return compose_ranges(hardening_ranges(), general_ranges() if profile == "mixed" else [])


def manifest(profile: str) -> dict:
    return {"phase": "R-AI1.1 hardening", "profile": PROFILES[profile],
            "source_sha256": RETAIL_SHA256, "hardened_base_sha256": BASE_SHA256,
            "output_sha256": BASE_SHA256 if profile == "base" else MIXED_SHA256,
            "image_size": RETAIL_SIZE, "num_cars_changed": False,
            "existing_mixed_chooser_unchanged": profile == "mixed",
            "broker_dump_variant": "native_hardened", "runtime_validation": "PENDING",
            "ranges": [{**{k: v for k, v in row.items() if k not in ("original", "replacement")},
                        "rva": row["va"] - 0x400000 if row["va"] is not None else None,
                        "code_cave": {0x60201E: STRING_CAVE, 0x602153: XML_CAVE}.get(row["va"]),
                        "null_continuation": {STRING_CAVE: 0x602040, XML_CAVE: 0x60218E}.get(row["va"]),
                        "source_evidence": row.get("evidence", "Audited pristine PE / existing R-AI1.1 generalized-class-policy.md"),
                        "original_hex": row["original"].hex(),
                        "replacement_hex": row["replacement"].hex()} for row in ranges_for(profile)]}


def build(source: bytes, profile: str) -> tuple[bytes, dict]:
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError("Hardening requires exact pristine retail size and SHA256")
    pe = parse_pe(source)
    rows = ranges_for(profile)
    for row in rows:
        if row["va"] is not None and va_to_file_offset(pe, row["va"]) != row["offset"]:
            raise ValueError("Unexpected pristine PE layout")
    result = apply_ranges(source, rows, RETAIL_SHA256)
    expected = BASE_SHA256 if profile == "base" else MIXED_SHA256
    if sha256(result) != expected:
        raise ValueError("Hardening output differs from the pinned audited profile")
    return result, manifest(profile)


def verify(candidate: bytes) -> dict:
    digest = sha256(candidate)
    if len(candidate) != RETAIL_SIZE or digest not in (BASE_SHA256, MIXED_SHA256):
        raise ValueError("Unknown hardening candidate size/hash")
    profile = "base" if digest == BASE_SHA256 else "mixed"
    restored = bytearray(candidate)
    for row in ranges_for(profile):
        offset, old, new = row["offset"], row["original"], row["replacement"]
        if candidate[offset:offset + len(new)] != new:
            raise ValueError("Hardening replacement-byte verification failed")
        restored[offset:offset + len(old)] = old
    _, result = build(bytes(restored), profile)
    return result


def check_results_snapshot(snapshot: dict) -> dict:
    source = snapshot.get("source", {})
    if (snapshot.get("kind") != "master-rallye-broker-dump-snapshot" or
            snapshot.get("schema_version") != 1 or
            source.get("image_sha256") != MIXED_SHA256 or
            source.get("build_profile") != PROFILES["mixed"] or
            source.get("broker_dump_variant") != "native_hardened" or
            source.get("freshness") != "post_baseline_complete_dump_proven" or
            source.get("label") != "mixed-hardened-results"):
        raise ValueError("Need a fresh Results capture from the exact hardened mixed profile")
    entries = snapshot.get("entries", [])
    def entry(suffix):
        rows = [row for row in entries if row["path"] == "Frontend/RaceResults/" + suffix]
        if len(rows) != 1:
            raise ValueError("Missing/ambiguous Results path: " + suffix)
        return rows[0]
    if entry("ResultsType")["value"] != "RACE TIME":
        raise ValueError("Smoke requires the ordinary RACE TIME result path")
    points = entry("PointsList")
    if points.get("type") != "StringList" or points.get("value") != []:
        raise ValueError("Expected complete empty StringList representation")
    for suffix in ("NameList", "TimeList"):
        row = entry(suffix)
        if row.get("type") != "StringList" or not isinstance(row.get("value"), list) or not row["value"]:
            raise ValueError("Expected populated Results " + suffix)
    index = entries.index(points)
    later = entries[index + 1:]
    if not later:
        raise ValueError("No entries after PointsList; continuation not demonstrated")
    return {"status": "BROKER_RESULTS_DUMP_MATCH_ONLY", "runtime_full_pass": False,
            "following_entries": len(later), "first_following_path": later[0]["path"],
            "empty_list_does_not_prove_allocated_empty_or_null": True,
            "human_checks": ["game alive after Dump", "subsequent loading/restart is normal"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build")
    create.add_argument("source", type=Path)
    create.add_argument("output", type=Path)
    create.add_argument("--profile", choices=tuple(PROFILES), required=True)
    check = sub.add_parser("verify")
    check.add_argument("candidate", type=Path)
    results = sub.add_parser("check-results")
    results.add_argument("candidate", type=Path)
    results.add_argument("snapshot", type=Path)
    results.add_argument("--observatory", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "build":
        output = ignored_output(args.output)
        if output.exists() or output.with_suffix(".manifest.json").exists():
            raise ValueError("Refusing to overwrite candidate or manifest")
        data, result = build(args.source.read_bytes(), args.profile)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        output.with_suffix(".manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    else:
        result = verify(args.candidate.read_bytes())
        if args.command == "check-results":
            if result["output_sha256"] != MIXED_SHA256:
                raise ValueError("Results smoke requires the exact composed mixed profile")
            from r_ai1_observe import load_profile
            from r_ai1_mixed_class import verify_capture
            observe = load_profile(args.observatory, args.candidate)
            snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
            sidecar = snapshot["source"]["raw_sidecar"]
            if Path(sidecar).name != sidecar:
                raise ValueError("Invalid raw sidecar name")
            verify_capture(snapshot, args.snapshot.with_name(sidecar).read_bytes(), observe.core.parse_dump_bytes)
            result = check_results_snapshot(snapshot)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
