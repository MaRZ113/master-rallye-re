"""Build and verify the exact retail R-GRID8 eight-car start-audit candidate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import r_ai2_1_capacity as capacity
from patch_vehicle_slot25 import parse_pe, va_to_file_offset
from r_ai1_mixed_class import RETAIL_SHA256, RETAIL_SIZE, apply_ranges, ignored_output, sha256

PROFILE = "retail-r-grid8-audit"
EXPECTED_CANDIDATE_SHA256 = "75942c0b65147b96b8b2254ee536f6aefc7f3a501c23d12be640f85a562680ac"
TRACK_IDS = tuple(range(39))
TRACK_GUARD_ORIGINAL = bytes.fromhex("83f80a0f851e000000")
TRACK_GUARD_REPLACEMENT = bytes.fromhex("83f8260f871e000000")
KEEP_VAS = {0x464F69, 0x47B88A, 0x47B8DD, 0x47B96E, 0x68E300, 0x68E400}


def track_guard(track_id: int) -> bool:
    """The encoded unsigned `cmp eax,38; ja stock` predicate."""
    return type(track_id) is int and 0 <= track_id <= 38


def ranges() -> list[dict]:
    """Reuse R-AI2.1 N=8 ranges, dropping only its native Dump hardening."""
    full = capacity.ranges(8)
    kept = []
    for source in full:
        row = dict(source)
        if row["va"] is None:
            # The capacity builder's merged VirtualSize already ends after the
            # highest retained roster cave; verify that assumption below.
            kept.append(row)
        elif row["va"] in KEEP_VAS:
            kept.append(row)
    expected_vas = KEEP_VAS
    if {row["va"] for row in kept if row["va"] is not None} != expected_vas:
        raise ValueError("R-AI2.1 range layout changed; audit candidate needs review")

    count_row = next(row for row in kept if row["va"] == 0x68E300)
    code = count_row["replacement"]
    if code.count(TRACK_GUARD_ORIGINAL) != 1:
        raise ValueError("Expected exactly one original Track10 guard in count shim")
    count_row["replacement"] = code.replace(TRACK_GUARD_ORIGINAL,
                                            TRACK_GUARD_REPLACEMENT, 1)
    count_row["purpose"] = (
        "R-AI2.1 exact N=8 count/context shim; only Track10 guard broadened "
        "to registered scene IDs 0..38"
    )

    for row in kept:
        if row["va"] in (0x60201E, 0x602153, 0x68E2A0, 0x68E2C0):
            raise ValueError("Native Broker Dump hardening must remain stock")
    return sorted(kept, key=lambda row: row["offset"])


def manifest(output_sha256: str) -> dict:
    patch_ranges = ranges()
    return {
        "phase": "R-GRID8",
        "profile": PROFILE,
        "source_profile": "retail-pristine",
        "source_sha256": RETAIL_SHA256,
        "output_sha256": output_sha256,
        "size": RETAIL_SIZE,
        "status": "READY_FOR_HUMAN_AUDIT",
        "broker_dump_variant": "stock",
        "participants": 8,
        "num_players": 1,
        "visible_opponents_choice": 3,
        "effective_ai_count": 7,
        "guard": {
            "quick_race_mode": 2,
            "visible_opponents_choice": 3,
            "split_screen": False,
            "ghost": 0,
            "player_id": 0,
            "track_predicate": "unsigned TrackID <= 38",
            "accepted_registered_scene_ids": list(TRACK_IDS),
            "chooser_scope": "normal one-human Quick Race chooser call; split-screen and other game modes are not targeted",
        },
        "roster": [
            {"slot": n, "CarID": vehicle_id,
             "CarClass": 0 if vehicle_id < 7 else 1 if vehicle_id < 14 else 2,
             "DriverID": 30 if n == 0 else n - 1}
            for n, vehicle_id in enumerate(capacity.ROSTER)
        ],
        "changes": {
            "only_track_guard_broadened": True,
            "legacy_loading_to_false_attract_hardening_retained": True,
            "native_broker_dump_hardening": False,
            "ui_changes": False,
            "randomizer_dependency": False,
            "vehicle_registry_expansion": False,
            "course_assets_modified": False,
            "global_grid_formula_modified": False,
            "physical_participant_storage_expanded": False,
        },
        "track_guard_delta": {
            "va": "0x0068E359",
            "original": TRACK_GUARD_ORIGINAL.hex(),
            "replacement": TRACK_GUARD_REPLACEMENT.hex(),
            "semantic": "cmp eax,10 / jne stock -> cmp eax,38 / ja stock",
        },
        "ranges": [
            {**{k: v for k, v in row.items()
                if k not in ("original", "replacement")},
             "length": len(row["original"]),
             "original_hex": row["original"].hex(),
             "replacement_hex": row["replacement"].hex()}
            for row in patch_ranges
        ],
        "reproduction": (
            "python tools/r_grid8_candidate.py build <retail-MRallye.exe> "
            "--output .research-output/general-re/grid8/MRallye.exe"
        ),
    }


def build(source: bytes, *, pin_output: bool = True) -> tuple[bytes, dict]:
    if len(source) != RETAIL_SIZE or sha256(source) != RETAIL_SHA256:
        raise ValueError("Require exact pristine retail SHA256 and size")
    pe = parse_pe(source)
    patch_ranges = ranges()
    for row in patch_ranges:
        if row["va"] is not None and va_to_file_offset(pe, row["va"]) != row["offset"]:
            raise ValueError("R-GRID8 target VA/file-offset layout mismatch")
    output = apply_ranges(source, patch_ranges, RETAIL_SHA256)
    digest = sha256(output)
    if pin_output and EXPECTED_CANDIDATE_SHA256 and digest != EXPECTED_CANDIDATE_SHA256:
        raise ValueError("R-GRID8 candidate differs from the pinned deterministic output")
    return output, manifest(digest)


def verify(candidate: bytes) -> dict:
    if not EXPECTED_CANDIDATE_SHA256:
        raise ValueError("Candidate output SHA256 has not been pinned")
    if len(candidate) != RETAIL_SIZE or sha256(candidate) != EXPECTED_CANDIDATE_SHA256:
        raise ValueError("Unknown R-GRID8 candidate size/hash")
    patch_ranges = ranges()
    restored = bytearray(candidate)
    for row in patch_ranges:
        start = row["offset"]
        if candidate[start:start + len(row["replacement"])] != row["replacement"]:
            raise ValueError(f"Replacement verification failed at file offset {start:#x}")
        restored[start:start + len(row["original"])] = row["original"]
    if sha256(restored) != RETAIL_SHA256:
        raise ValueError("Inverse restoration did not recover pristine retail")
    rebuilt, result = build(bytes(restored))
    if rebuilt != candidate:
        raise ValueError("Deterministic reproduction differs byte-for-byte")
    result["inverse_verified"] = True
    result["byte_equal_reproduction"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("source", type=Path)
    build_parser.add_argument("--output", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        output_path = ignored_output(args.output)
        manifest_path = output_path.with_suffix(".manifest.json")
        if output_path.exists() or manifest_path.exists():
            raise ValueError("Refusing to overwrite candidate or manifest")
        data, result = build(args.source.read_bytes(), pin_output=False)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(data)
        manifest_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(verify(args.candidate.read_bytes()), indent=2))


if __name__ == "__main__":
    main()
