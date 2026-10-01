#!/usr/bin/env python3
"""Classify meaningful strings and xrefs from the four Ghidra Bridge exports."""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path
from typing import Any


BUILDS = ("8.4.1", "9.3.1", "9.10.0", "retail")
RULES = {
    "filesystem_resource": re.compile(r"Data(?:Game|Gx|Scene|Audio|Video)/|\\\\data(?:game|gx|scene|audio|video)\\\\|\.(?:dx|dxt|gxm|gxi|gxb|sfl|hnt|xml|txt)\b|resource|cached (?:image|model|texture)|Reading GX[MI]|Can't (?:open|load) (?:game|scene|file)", re.I),
    "xml_parameter_brokers": re.compile(r"\bXML\b|Xml(?:Filename|Data)|Broker|ParamBroker|ControllerCarBrokerAccess|Number of Broker", re.I),
    "graphics_renderer": re.compile(r"Direct3D|\bD3D8?\b|shader|render state|texture stage|alpha(?:test|blend)?|Reflections|DetailPasses|GXM|GXI", re.I),
    "model_scene_loading": re.compile(r"model|scene|moModel|GXM|GXI|model cache|image bank", re.I),
    "frontend_menu": re.compile(r"Front(?:End|end)|Menu|VehicleSelect|CourseSelect|Screen|Unlock|Locked|Selection", re.I),
    "course_race_route": re.compile(r"\bRace/|\bCourse/|gaRace|RaceLine|LastMarker|WrongWay|PaceNote|SplitTime|SplitPoint|RecordSpline|StartArea|FinishArea|Marker", re.I),
    "vehicle_physics_damage": re.compile(r"Vehicle|Vehicles/|Race/Car|Physics|Suspension|Damage|Wheel|Chassis|Engine", re.I),
    "ai_opponent": re.compile(r"\bAI\b|gaAi|ai[A-Z]|opponent|steer|waypoint|raceline", re.I),
    "input_controller": re.compile(r"DirectInput|DINPUT|Controller|Input/|Input\\|Keyboard|Joystick|Gamepad", re.I),
    "audio_music": re.compile(r"DirectSound|DSOUND|Sound/|Music/|Audio|\bWAV\b|\bMP3\b", re.I),
    "save_progress_unlocks": re.compile(r"Save|Unlock|Championship|Progress|Record|Profile|Career|Cup", re.I),
    "networking": re.compile(r"Network|UDP|Winsock|WSAStartup|sendto|recvfrom|ChatRequest|NetworkSync", re.I),
    "developer_debug_cooker": re.compile(r"Debug|DebugWindow|DebugDraw|Editor|Editing/|DataEditors|BuildData|cooker|Cook|assert|Assertion|Test\.xml|Test\.txt", re.I),
    "timing_profiling": re.compile(r"Timer|Timing|Profile|\bFPS\b|Frame|Elapsed|Cycle|Performance", re.I),
    "replay_ghost": re.compile(r"Ghost|Replay|Playback|RecordSpline", re.I),
    "source_build_metadata": re.compile(r"(?:[A-Z]:\\|[A-Za-z0-9_./-]+\.(?:cpp|c|h|hpp|pdb)\b|Steel Monkeys|Projects\\)", re.I),
}
LIBRARY = re.compile(r"(?:libpng|libjpeg|zlib|unzip 0\.15|Copyright 199[0-9]|DirectInput8Create|DirectSoundCreate|D3DERR_|DXGI_ERROR_|Microsoft\(R\)|Run-Time Check Failure|bad allocation|std::|basic_string|invalid parameter|heap corruption)", re.I)


def load_records(root: Path, build: str) -> list[dict[str, Any]]:
    path = root / build / "_strings.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload.values() if isinstance(payload, dict) else payload
    return [row for row in values if isinstance(row, dict) and row.get("value")]


def classify(value: str) -> tuple[list[str], bool]:
    categories = [name for name, pattern in RULES.items() if pattern.search(value)]
    return categories, bool(LIBRARY.search(value))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", type=Path, help="Defaults to research-output/r-exe1/bridge-strings")
    ap.add_argument("--output-dir", type=Path, help="Defaults to research/r-exe1")
    ap.add_argument("--max-per-category", type=int, default=60)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    input_dir = (args.input_dir or (repo / "research-output" / "r-exe1" / "bridge-strings")).resolve()
    output_dir = (args.output_dir or (repo / "research" / "r-exe1")).resolve()
    entries: list[dict[str, Any]] = []
    summary: dict[str, Any] = {"schema_version": 1, "builds": {}, "categories": list(RULES), "generic_library": {}}
    library_records = []
    category_build_counts: dict[str, collections.Counter[str]] = {name: collections.Counter() for name in RULES}
    for build in BUILDS:
        records = load_records(input_dir, build)
        summary["builds"][build] = {"all_defined_strings": len(records), "meaningful": 0, "generic_library": 0}
        for row in records:
            value = str(row["value"]).replace("\x00", "")
            categories, is_library = classify(value)
            refs = row.get("references", [])
            if is_library:
                summary["builds"][build]["generic_library"] += 1
                library_records.append({"build": build, "address": row.get("address"), "text": value, "category": "generic_library", "xrefs": refs})
            if not categories:
                continue
            summary["builds"][build]["meaningful"] += 1
            for category in categories:
                category_build_counts[category][build] += 1
            entries.append({
                "build": build,
                "address": row.get("address"),
                "text": value,
                "categories": categories,
                "likely_subsystem": categories[0],
                "xrefs": refs,
                "confidence": "HIGH" if refs else "MEDIUM",
                "reason": "string has a direct Ghidra code xref" if refs else "subsystem-specific literal without a direct Ghidra xref",
            })
    summary["category_counts_by_build"] = {name: dict(counter) for name, counter in category_build_counts.items()}
    summary["generic_library"]["counts_by_build"] = {build: summary["builds"][build]["generic_library"] for build in BUILDS}
    summary["generic_library"]["sample_records"] = library_records[:120]
    summary["records"] = entries
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "string-catalog.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = ["# Cross-build executable string catalog", "", "Ghidra Bridge defined strings are indexed by build, address, direct function xrefs, subsystem and confidence. The JSON retains all matching records; the Markdown is a curated route map, capped per category so generic engine/library text does not swamp the architectural evidence.", "", "## Coverage", "", "| Build | Defined strings | Classified game/engine strings | Generic library matches |", "|---|---:|---:|---:|"]
    for build, counts in summary["builds"].items():
        lines.append(f"| {build} | {counts['all_defined_strings']:,} | {counts['meaningful']:,} | {counts['generic_library']:,} |")
    lines += ["", "## Category coverage", "", "| Category | 8.4.1 | 9.3.1 | 9.10.0 | retail |", "|---|---:|---:|---:|---:|"]
    for category, counts in summary["category_counts_by_build"].items():
        lines.append(f"| {category} | {counts.get('8.4.1', 0)} | {counts.get('9.3.1', 0)} | {counts.get('9.10.0', 0)} | {counts.get('retail', 0)} |")
    lines += ["", "## Representative strings with xrefs", ""]
    preferred = re.compile(r"Data(?:Game|Gx|Scene)/|Reading GX[MI]|cached (?:model|texture|image bank)|gaRace|Race/Car%d/(?:LastMarker|PaceNote|SplitPoint|RecordSpline|WrongWay)|Race/SplitTime|\bNetwork/|gaNetwork|shader/|DebugWindow|Editing/EditorsOpen|BuildData|data\.sma|GhostPlayback|DirectX/Options", re.I)
    for category in RULES:
        selected = [e for e in entries if category in e["categories"] and e["xrefs"] and preferred.search(e["text"])]
        if not selected:
            continue
        lines += [f"### {category}", "", "| Build | Address | Text | Referencing functions | Confidence |", "|---|---:|---|---|---|"]
        seen = set()
        count = 0
        for item in selected:
            key = (item["build"], item["address"], item["text"])
            if key in seen:
                continue
            seen.add(key)
            funcs = ", ".join(sorted({str(ref.get("func_name")) for ref in item["xrefs"] if ref.get("func_name")})) or "xref target unresolved"
            text = item["text"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {item['build']} | `{item['address']}` | `{text}` | {funcs} | {item['confidence']} |")
            count += 1
            if count >= args.max_per_category:
                break
        lines.append("")
    lines += ["## Evidence limits", "", "- A direct string xref proves that code references the literal, not what the surrounding operation does.", "- Strings without direct xrefs may be reached through tables, generated keys, or may be retained but unused.", "- Library signatures are separately counted and sampled; they are not presented as Master Rallye-specific behavior.", ""]
    (output_dir / "string-catalog.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Catalogued {len(entries)} classified string records across {len(BUILDS)} builds; generic-library matches={len(library_records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
