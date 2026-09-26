#!/usr/bin/env python3
"""Read-only R-BRIDGE1 Jump/Trooper/Navara inventory and DX comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from master_rallye.bridge_analysis import compare_dx_generations, validate_bridge_candidate
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.gxi import parse_gxi_bytes
from master_rallye.gxm import parse_gxm_prefix_bytes
from master_rallye.demo_dx import compare_demo_dx, inspect_demo_dx


def fingerprint(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    result = {"path": path.relative_to(root).as_posix(), "size": len(data),
              "sha256": hashlib.sha256(data).hexdigest()}
    suffix = path.suffix.lower()
    if suffix == ".dx":
        try:
            view = inspect_demo_dx(data, path.name)
            result["demo_structural_parser"] = {"status": "ACCEPTED", "header": list(view.header),
                                                "vertex_count": len(view.positions),
                                                "local_index_count": len(view.local_indices),
                                                "draw_region_size": len(view.draw_raw),
                                                "collision_tags": list(view.collision.tag_ids)}
        except Exception as exc:
            result["demo_structural_parser"] = {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
        validation = validate_bridge_candidate(data, source=path.name)
        result["retail_structural_parser"] = validation["retail_parser"]
        result["bridge_validator_status"] = validation["status"]
        result["retail_cache_header_gate"] = validation["retail_cache_header_gate"]
    elif suffix == ".gxm":
        try:
            prefix = parse_gxm_prefix_bytes(data, path.name)
            result["gxm_prefix"] = {"status": "PARTIAL_PREFIX_PARSED", "prefix_kind": prefix.prefix_kind,
                                    "header_words": list(prefix.header_words),
                                    "material_count": len(prefix.materials),
                                    "material_slot_count": sum(len(material.slots) for material in prefix.materials),
                                    "texture_references": [
                                        {"material": material.name, "slot": slot_index,
                                         "flags_hex": slot.flags3.hex(), "reference": slot.reference}
                                        for material in prefix.materials
                                        for slot_index, slot in enumerate(material.slots)],
                                    "tail_offset": prefix.tail_offset, "tail_size": prefix.tail_size}
        except Exception as exc:
            result["gxm_prefix"] = {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
    elif suffix == ".dxt":
        try:
            texture = parse_dxt_bytes(data, path.name)
            result["dxt"] = {"status": "ACCEPTED", "width": texture.width, "height": texture.height,
                             "word_0x04": texture.word_0x04, "word_0x08": texture.word_0x08}
        except Exception as exc:
            result["dxt"] = {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
    elif suffix == ".gxi":
        try:
            image = parse_gxi_bytes(data, path.name)
            result["gxi"] = {"status": "ACCEPTED", "width": image.width, "height": image.height,
                             "kind": image.kind}
        except Exception as exc:
            result["gxi"] = {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
    elif suffix == ".txt":
        text = data.decode("latin-1")
        result["sidecar_texture_mentions"] = sorted(
            {reference.replace("\\", "/") for reference in
             re.findall(r"Name\[([^\]]+\.tga)\]", text, flags=re.IGNORECASE)},
            key=str.lower)
    return result


def vehicle_inventory(root: Path, corpus_id: str, vehicle: str) -> dict[str, Any]:
    directory = root / vehicle
    if not directory.is_dir():
        return {"corpus": corpus_id, "vehicle": vehicle, "status": "MISSING"}
    files = sorted((path for path in directory.rglob("*") if path.is_file()),
                   key=lambda path: path.relative_to(root).as_posix().lower())
    return {"corpus": corpus_id, "vehicle": vehicle, "status": "PRESENT",
            "files": [fingerprint(path, root) for path in files]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-841-vehicles", type=Path, required=True)
    parser.add_argument("--demo-931-vehicles", type=Path, required=True)
    parser.add_argument("--retail-vehicles", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    roots = {
        "demo-8.4.1": args.demo_841_vehicles.resolve(),
        "demo-9.3.1": args.demo_931_vehicles.resolve(),
        "retail": args.retail_vehicles.resolve(),
    }
    target = args.output.resolve()
    for corpus, root in roots.items():
        if not root.is_dir() or root == target or root in target.parents or target in root.parents:
            raise SystemExit(f"invalid or overlapping source/output root: {corpus}")
    selected = (("demo-8.4.1", "Jump"), ("demo-9.3.1", "Jump"), ("retail", "Jump"),
                ("demo-9.3.1", "Trooper"), ("retail", "Navara"))
    inventories = [vehicle_inventory(roots[corpus], corpus, vehicle)
                   for corpus, vehicle in selected]
    by_key = {(entry["corpus"], entry["vehicle"]): entry for entry in inventories}
    comparisons = {}
    evolution = {}
    for role in ("car", "complete", "wheel"):
        demo_rel = f"Jump/{role}.dx"
        retail_rel = f"Jump/{role}.dx"
        demo_path = roots["demo-9.3.1"] / demo_rel
        retail_path = roots["retail"] / retail_rel
        if demo_path.is_file() and retail_path.is_file():
            comparisons[role] = compare_dx_generations(demo_path.read_bytes(), retail_path.read_bytes(),
                                                       demo_source=f"demo-9.3.1/{demo_rel}",
                                                       retail_source=f"retail/{retail_rel}")
        old_path = roots["demo-8.4.1"] / demo_rel
        if old_path.is_file() and demo_path.is_file():
            evolution[role] = compare_demo_dx(old_path.read_bytes(), demo_path.read_bytes(),
                                              first_source=f"demo-8.4.1/{demo_rel}",
                                              second_source=f"demo-9.3.1/{demo_rel}")
    target.parent.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1,
              "scope": "Read-only inventory; DX parser comparison is not runtime acceptance proof.",
              "corpora": inventories, "jump_demo841_vs_demo931": evolution,
              "jump_demo931_vs_retail": comparisons}
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "vehicle_directories": len(inventories),
                      "jump_role_comparisons": sorted(comparisons),
                      "primary_jump_hashes": {
                          "demo-9.3.1": next(item["sha256"] for item in by_key[("demo-9.3.1", "Jump")]["files"]
                                             if item["path"].lower() == "jump/car.dx"),
                          "retail": next(item["sha256"] for item in by_key[("retail", "Jump")]["files"]
                                         if item["path"].lower() == "jump/car.dx")}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
