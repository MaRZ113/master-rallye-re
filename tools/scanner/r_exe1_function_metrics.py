#!/usr/bin/env python3
"""Reproduce selected R-EXE1 cross-build mnemonic-sequence similarity values.

Input is the bounded Ghidra Bridge JSON under ignored research-output/. This is
an exploratory fingerprint only: the comparison discards operands, addresses,
data references, and CFG topology.
"""
from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path


BUILDS = ("8.4.1", "9.3.1", "9.10.0", "retail")
ANCHORS = {
    "resource_root_registration": {
        "8.4.1": "004cecf0", "9.3.1": "00513e10",
        "9.10.0": "0052a320", "retail": "00541640",
    },
    "udp_listener": {
        "8.4.1": "0042fbf0", "9.3.1": "00430f20",
        "9.10.0": "00431f50", "retail": "00433240",
    },
    "shader_registry": {
        "8.4.1": "00512800", "9.3.1": "00534b50",
        "9.10.0": "00544270", "retail": "00565da0",
    },
    "progress_win_status_writer": {
        "8.4.1": "0046e020", "9.3.1": "0048ce00",
        "9.10.0": "004a2ea0", "retail": "004af3b0",
    },
    "application_settings_registration": {
        "8.4.1": "00484ef0", "9.3.1": "004aee40",
        "9.10.0": "004c3a00", "retail": "004d7bd0",
    },
    "wrong_way_hud_constructor": {
        "8.4.1": "0046ade0", "9.3.1": "00489080",
        "9.10.0": "0049ecb0", "retail": "004a91e0",
    },
    "default_vehicle_broker_registration": {
        "8.4.1": "00456590", "9.3.1": "00471380",
        "9.10.0": "00485550", "retail": "0048fa10",
    },
}


def mnemonics(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = []
    for line in data.get("assembly", []):
        parts = line.strip().split()
        if len(parts) >= 2:
            result.append(parts[1].split(",", 1)[0].upper())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root", type=Path,
        default=Path("research-output/r-exe1/bridge-selected"),
        help="Directory containing <build>/<address>.json exports",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    args = parser.parse_args()

    report = {"schema_version": 1, "metric": "SequenceMatcher ratio over mnemonic-only instruction lists", "anchors": {}}
    for name, addresses in ANCHORS.items():
        sequences = {}
        missing = []
        for build, address in addresses.items():
            path = args.input_root / build / f"{address}.json"
            if not path.is_file():
                missing.append(f"{build}:{address}")
                continue
            sequences[build] = mnemonics(path)
        pairs = {}
        for left, right in zip(BUILDS, BUILDS[1:]):
            if left in sequences and right in sequences:
                pairs[f"{left}->{right}"] = round(
                    difflib.SequenceMatcher(a=sequences[left], b=sequences[right]).ratio(), 3
                )
        report["anchors"][name] = {
            "addresses": addresses,
            "instruction_counts": {build: len(items) for build, items in sequences.items()},
            "pair_similarity": pairs,
            "missing_exports": missing,
        }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report["metric"])
        for name, result in report["anchors"].items():
            print(f"{name}: {result['pair_similarity']}" + (f" missing={result['missing_exports']}" if result["missing_exports"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
