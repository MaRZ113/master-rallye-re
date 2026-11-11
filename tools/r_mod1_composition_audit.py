#!/usr/bin/env python3
"""Audit historical R-AI/R-UI patch ranges without composing their binaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRISTINE_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _range_rows(name: str, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for entry in manifest.get("ranges", []):
        start = entry.get("offset", entry.get("file_offset"))
        length = entry.get("length")
        if start is None or length is None:
            continue
        if isinstance(start, str):
            start = int(start, 0)
        rows.append({
            "source": name,
            "start": int(start),
            "end": int(start) + int(length),
            "length": int(length),
            "purpose": str(entry.get("purpose", "unspecified")),
            "original_sha256": entry.get("original_sha256"),
            "replacement_sha256": entry.get("replacement_sha256"),
            "original_hex": entry.get("original_hex"),
            "replacement_hex": entry.get("replacement_hex"),
        })
    return rows


def load_historical_ranges(root: Path = ROOT) -> tuple[dict[str, str], dict[str, list[dict[str, Any]]]]:
    randomizer_doc = _read(root / "research/r-ai1-2/build-summary.json")
    randomizer = next(
        profile for profile in randomizer_doc["profiles"]
        if profile.get("profile") == "retail-r-ai1-2-four-hardened"
    )
    randomizer["source_sha256"] = randomizer_doc["source_sha256"]

    capacity_doc = _read(root / "research/r-ai2-1/patch-manifest.json")
    capacity = next(candidate for candidate in capacity_doc["candidates"] if candidate.get("num_cars") == 8)

    ui = _read(root / "research/r-ui1/patch-manifest.json")
    sources = {
        "randomizer": randomizer,
        "capacity": capacity,
        "ui": ui,
    }
    source_hashes = {
        "randomizer": randomizer.get("source_sha256", ""),
        "capacity": capacity.get("source_sha256", ""),
        "ui": ui.get("source_sha256", ""),
    }
    if any(value != PRISTINE_SHA256 for value in source_hashes.values()):
        raise ValueError("Historical patch manifests do not share the pinned pristine source hash")
    return source_hashes, {name: _range_rows(name, manifest) for name, manifest in sources.items()}


def classify_overlap(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["start"] == 0x218 and right["start"] == 0x218:
        return "SHARED_PE_VIRTUALSIZE_FIELD_RECOMPUTE_ONCE"
    same_span = left["start"] == right["start"] and left["end"] == right["end"]
    same_bytes = (
        left.get("original_sha256") == right.get("original_sha256")
        and left.get("replacement_sha256") == right.get("replacement_sha256")
        and bool(left.get("replacement_sha256"))
    )
    if same_span and same_bytes:
        return "IDENTICAL_SHARED_OPERATION_DEDUPLICATE"
    return "SEMANTIC_OR_CAVE_CONFLICT_RECOMPOSE_REQUIRED"


def audit_composition(root: Path = ROOT) -> dict[str, Any]:
    source_hashes, ranges = load_historical_ranges(root)
    pairs = []
    conflict_pairs = 0
    identical_pairs = 0
    shared_size_fields = 0
    for left_name, right_name in (("randomizer", "capacity"), ("randomizer", "ui"), ("capacity", "ui")):
        overlaps = []
        for left in ranges[left_name]:
            for right in ranges[right_name]:
                if left["start"] >= right["end"] or right["start"] >= left["end"]:
                    continue
                kind = classify_overlap(left, right)
                overlaps.append({
                    "start": f"0x{max(left['start'], right['start']):X}",
                    "end_exclusive": f"0x{min(left['end'], right['end']):X}",
                    "classification": kind,
                    "left_purpose": left["purpose"],
                    "right_purpose": right["purpose"],
                    "left_replacement_sha256": left.get("replacement_sha256"),
                    "right_replacement_sha256": right.get("replacement_sha256"),
                })
                if kind == "IDENTICAL_SHARED_OPERATION_DEDUPLICATE":
                    identical_pairs += 1
                elif kind == "SHARED_PE_VIRTUALSIZE_FIELD_RECOMPUTE_ONCE":
                    shared_size_fields += 1
                else:
                    conflict_pairs += 1
        pairs.append({"sources": [left_name, right_name], "overlaps": overlaps})
    return {
        "phase": "R-MOD1-A",
        "evidence_class": "CONFIRMED_BY_EXE_PATCH_MANIFESTS",
        "baseline_executable_sha256": PRISTINE_SHA256,
        "historical_sources": source_hashes,
        "historical_patch_binaries_imported": False,
        "integrated_patch_bundle_created": False,
        "overlap_summary": {
            "identical_shared_operations_to_deduplicate": identical_pairs,
            "shared_pe_virtual_size_fields_to_recompute_once": shared_size_fields,
            "semantic_or_code_cave_conflicts": conflict_pairs,
        },
        "pairs": pairs,
        "release_implication": (
            "Do not overlay historical candidates. Build one fresh plan from the pristine image, "
            "deduplicate identical hardening operations only where still required, recompute PE sizing once, "
            "and move new code/data to verified runtime allocations or a newly audited disjoint layout."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_composition(args.root)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
