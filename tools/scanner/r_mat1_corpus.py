"""Recompute retail vehicle material classifications from read-only DX/TXT/DXT.

Reports contain forensic metadata only. No game binary or decoded pixels are
copied. Unsupported branches are reported, never silently assigned a family.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from master_rallye.dx import parse_dx
from master_rallye.material_semantics import MaterialSemantics
from material_corpus import build
from material_hardening import analyze


def inventory(root: Path) -> dict:
    corpus = build(root)
    hardening = analyze(corpus)
    masks, alpha, families, classes, helpers = (Counter() for _ in range(5))
    slot_counts = [Counter() for _ in range(3)]
    flags = [Counter() for _ in range(4)]
    resources, rows, corners, truth = [], [], [], defaultdict(list)
    named = defaultdict(list)
    for source in sorted(root.glob("*/*.dx"), key=lambda p: str(p).casefold()):
        model = parse_dx(source)
        resources.append({"resource": source.relative_to(root).as_posix(),
                          "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                          "draws": len(model.physical_draws)})
        for draw in model.physical_draws:
            sem = MaterialSemantics.from_draw(draw)
            off = MaterialSemantics.from_draw(draw, reflections=False)
            row = {"resource": source.relative_to(root).as_posix(), "draw": draw.draw_index,
                   "slots": list(sem.texture_slots), "flags": draw.flags_0x20.hex(), "mask": draw.unknown_0x24,
                   "alpha_mode": sem.alpha_mode, "shader_reflections_on": sem.runtime_shader_family,
                   "shader_reflections_off": off.runtime_shader_family,
                   "classification": sem.classification, "unknown_reasons": list(sem.unknown_reasons),
                   "env_bound": sem.texture_stage_mapping["slot1"].bound,
                   "env_effective_in_preview": sem.null_slot_behavior["stage1_effective"]}
            rows.append(row)
            masks[str(draw.unknown_0x24)] += 1
            alpha[sem.alpha_mode] += 1
            families[sem.runtime_shader_family or "UNKNOWN"] += 1
            classes[sem.classification] += 1
            for i, value in enumerate(sem.texture_slots):
                slot_counts[i]["Null" if value.casefold() == "null" else "present"] += 1
            for i, value in enumerate(draw.flags_0x20):
                flags[i][str(value)] += 1
            if sem.texture_slots[1].casefold() != "null":
                helpers[sem.texture_slots[1]] += 1
            if sem.texture_slots[0].casefold() == "null":
                corners.append(row)
            key = (row["flags"], row["mask"], row["alpha_mode"], row["shader_reflections_on"])
            truth[key].append(row)
            for category, needles in (("decal_name", ("sticker", "decal", "number")),
                                      ("glow_name", ("glow",)), ("lamp_name", ("light", "lamp"))):
                if any(needle in value.casefold() for value in sem.texture_slots for needle in needles):
                    named[category].append(row)
    return {
        "schema_version": 1, "phase": "R-MAT1", "source": "protected retail corpus; read-only; local path omitted",
        "summary": {"resources": len(resources), "draws": len(rows), "slot_counts": slot_counts,
                    "feature_masks": dict(sorted(masks.items())), "alpha_modes": dict(alpha),
                    "shader_families_reflections_on": dict(sorted(families.items())), "classification": dict(classes),
                    "flag_bytes": flags, "env_enabled": sum(row["env_bound"] for row in rows),
                    "env_effective_in_preview": sum(row["env_effective_in_preview"] for row in rows),
                    "old_filename_helper_coverage": sum(n for name, n in helpers.items() if name.casefold() in {"whitepaint-tga", "chrome-tga"}),
                    "slot1_names": dict(helpers.most_common())},
        "hardening": hardening, "null_slot0_cases": corners,
        "truth_table": [{"flags": key[0], "mask": key[1], "alpha_mode": key[2], "shader_reflections_on": key[3],
                         "count": len(values), "example": values[0]} for key, values in sorted(truth.items())],
        "named_layer_summary": {name: {"draws": len(values),
                              "families": dict(Counter(row["shader_reflections_on"] for row in values)),
                              "examples": values[:6]} for name, values in named.items()},
        "resources": resources, "draws": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = inventory(args.vehicle_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    if report["summary"]["classification"].get("UNKNOWN"):
        raise SystemExit("Explicit UNKNOWN material branches found; inspect the report")


if __name__ == "__main__":
    main()
