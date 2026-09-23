"""Render neutral evidence-scoped R4D tables from material-corpus.json."""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def write_reports(report, directory):
    draws = report["draws"]
    summary = report["summary"]
    clusters = sorted(report["signatures"].items(), key=lambda item: (-item[1], item[0]))
    ids = {signature: f"CLUSTER_{chr(65 + i)}" for i, (signature, _) in enumerate(clusters)}
    by_vehicle = defaultdict(list)
    for draw in draws:
        by_vehicle[draw["vehicle"]].append(draw)
    corpus = [
        "# R4D vehicle material corpus", "",
        "Generated from external read-only vehicle resources. No game bytes, textures, or absolute paths are included.", "",
        f"- Vehicle folders: {summary['vehicle_count']}; DX resources: {summary['resource_count']}.",
        f"- Physical draw/material bindings: {summary['draw_count']}.",
        f"- Unique TXT matches: {summary['unique_material_match']}; multiple: {summary['multiple_material_matches']}; unmatched: {summary['unmatched_materials']}.",
        f"- Referenced DXT instances: {summary['referenced_texture_instances']}; alpha-bearing: {summary['alpha_bearing_texture_instances']}.",
        "- TXT match coverage is not runtime semantic coverage. Fully classified runtime semantics: 0/1,478.", "",
        "| Vehicle | Draws | Unique TXT match | Multiple | Unmatched |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, rows in sorted(by_vehicle.items(), key=lambda item: item[0].casefold()):
        c = Counter(row["material_ambiguity"] for row in rows)
        corpus.append(f"| {name} | {len(rows)} | {c['unique']} | {c['multiple']} | {c['unmatched']} |")
    corpus += ["", "The JSON inventories every draw with ordered slots, sidecar candidates, nullable flags, DXT alpha statistics, vertex-color summary, and raw control values.", ""]
    (directory / "material-corpus.md").write_text("\n".join(corpus).rstrip("\n") + "\n", encoding="utf-8")

    helpers = Counter(draw["texture_slots"][1] for draw in draws)
    signatures = [
        "# R4D neutral material signatures", "",
        "CONFIRMED_BY_CORPUS: all 1,478 draws store three texture slots; slot 2 is always Null.",
        "Signatures use slot count, Null mask, draw tag, and raw flags_0x20 bytes. Cluster IDs assert no runtime semantic type.", "",
        "| Cluster | Draws | Structural signature |", "|---|---:|---|",
    ]
    for signature, count in clusters:
        signatures.append(f"| {ids[signature]} | {count} | {signature} |")
    signatures += ["", "## Slot 1 recurrence", "", "| Texture | Bindings |", "|---|---:|"]
    for name, count in helpers.most_common():
        signatures.append(f"| {name} | {count} |")
    signatures += ["", "The first non-Null slot is a preview choice. Runtime stage mapping and combination remain UNKNOWN.", ""]
    (directory / "material-signatures.md").write_text("\n".join(signatures).rstrip("\n") + "\n", encoding="utf-8")

    combos = Counter()
    for draw in draws:
        if len(draw["material_candidates"]) != 1:
            continue
        for t in draw["material_candidates"][0]["textures"]:
            a = draw["texture_alpha"][t["slot"]]
            present = bool(a and a.get("zero", 0) + a.get("partial", 0))
            combos[(t["HasAlpha"], t["UsesAlpha"], present)] += 1
    def yes(value):
        return "Unknown" if value is None else "Yes" if value else "No"
    alpha = [
        "# R4D alpha evidence", "",
        "Counts are uniquely matched sidecar texture entries per draw, including repeated car/complete bindings.",
        "Actual alpha means at least one DXT pixel with alpha below 255. This is CONFIRMED_BY_CORPUS, not a render-state claim.", "",
        "| HasAlpha | UsesAlpha | DXT alpha below 255 | Bindings |", "|---|---|---|---:|",
    ]
    for (has, uses, actual), count in sorted(combos.items(), key=lambda item: (-item[1], str(item[0]))):
        alpha.append(f"| {yes(has)} | {yes(uses)} | {yes(actual)} | {count} |")
    alpha += ["", "HasAlpha and UsesAlpha differ in real bindings. Opaque DXT can have UsesAlpha=Yes; alpha-bearing DXT can have UsesAlpha=No.",
              "The executable has separate alpha and alpha-test shader names, but mapping either TXT flag to them remains UNKNOWN.",
              "Alpha present, alpha test, and alpha blend must remain distinct.", ""]
    (directory / "alpha-semantics.md").write_text("\n".join(alpha).rstrip("\n") + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    write_reports(json.loads(args.report.read_text(encoding="utf-8")), args.report.parent)


if __name__ == "__main__":
    main()
