"""Recompute focused R4D.1 assertions from local vehicle DX/TXT/DXT sources."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from master_rallye.material_semantics import texture_presence_mask
from material_corpus import build


def analyze(corpus: dict) -> dict:
    draws = corpus["draws"]
    masks, presence = Counter(), Counter()
    flag_bytes = [Counter() for _ in range(4)]
    alpha_pairs, alpha_entries = Counter(), Counter()
    mask_exceptions, alpha_exceptions = [], []
    alpha_families = {"byte2_0": Counter(), "byte2_1": Counter()}
    for row in draws:
        slots = row["texture_slots"]
        flags = bytes.fromhex(row["control"]["flags_0x20_hex"])
        expected = texture_presence_mask(slots, flags[2])
        actual = row["control"]["unknown_0x24"]
        masks[str(actual)] += 1
        presence["".join("1" if slot.casefold() != "null" else "0" for slot in slots)] += 1
        for index, value in enumerate(flags):
            flag_bytes[index][str(value)] += 1
        if actual != expected:
            mask_exceptions.append({"resource": row["resource"], "draw": row["draw_index"],
                                    "observed": actual, "expected": expected})
        if len(row["material_candidates"]) != 1:
            continue
        material = row["material_candidates"][0]
        slot0 = next((item for item in material["textures"] if item["slot"] == 0), None)
        if slot0 is not None and slot0["UsesAlpha"] is not None:
            pair = (flags[0] != 0, slot0["UsesAlpha"])
            alpha_pairs[str(pair)] += 1
            if pair[0] != pair[1]:
                alpha_exceptions.append({
                    "resource": row["resource"], "draw": row["draw_index"],
                    "slot0": slots[0], "slot1": slots[1],
                    "flag_byte0": flags[0], "sidecar_slot0_UsesAlpha": slot0["UsesAlpha"],
                    "material": material["name"],
                })
        if flags[0]:
            alpha_families[f"byte2_{flags[2]}"][material["name"]] += 1
        for item in material["textures"]:
            slot = item["slot"]
            alpha = row["texture_alpha"][slot]
            if alpha is None or alpha.get("missing"):
                actual_alpha = None
            else:
                actual_alpha = alpha["zero"] + alpha["partial"] > 0
            key = f"HasAlpha={item['HasAlpha']};UsesAlpha={item['UsesAlpha']};DXT_alpha={actual_alpha}"
            alpha_entries[key] += 1
    return {
        "source": "recomputed from local DX/TXT/DXT corpus; source path omitted",
        "draws": len(draws),
        "resource_count": corpus["summary"]["resource_count"],
        "unique_sidecar_matches": corpus["summary"]["unique_material_match"],
        "unknown_0x24": {
            "formula": "(slot0 != Null ? 1 : 0) | (flags_0x20[2] != 0 ? 2 : 0) | (slot1 != Null ? 4 : 0)",
            "matches": len(draws) - len(mask_exceptions), "total": len(draws),
            "exceptions": mask_exceptions, "distribution": dict(sorted(masks.items())),
        },
        "slot_presence": dict(sorted(presence.items())),
        "flags_0x20_bytes": [dict(sorted(counter.items())) for counter in flag_bytes],
        "flag0_vs_slot0_UsesAlpha": {
            "matches": sum(int(v) for k, v in alpha_pairs.items() if k in {"(False, False)", "(True, True)"}),
            "total": sum(alpha_pairs.values()),
            "pairs": dict(sorted(alpha_pairs.items())),
            "exceptions": alpha_exceptions,
        },
        "flag2_to_mask_bit2": {
            "matches": sum(((bytes.fromhex(row["control"]["flags_0x20_hex"])[2] != 0)
                            == bool(row["control"]["unknown_0x24"] & 2)) for row in draws),
            "total": len(draws),
        },
        "alpha_texture_entries": dict(sorted(alpha_entries.items())),
        "alpha_family_names": {
            key: dict(counter.most_common(30)) for key, counter in alpha_families.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(build(args.vehicle_root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if report["resource_count"] == 78:
        checks = (
            report["draws"] == 1478,
            report["unknown_0x24"]["matches"] == report["draws"],
            report["flag2_to_mask_bit2"]["matches"] == report["draws"],
            set(report["flags_0x20_bytes"][2]) <= {"0", "1"},
            set(report["slot_presence"]) <= {"000", "010", "100", "110"},
            report["flag0_vs_slot0_UsesAlpha"]["matches"] == 1364,
            report["flag0_vs_slot0_UsesAlpha"]["total"] == 1365,
            [(item["resource"], item["draw"]) for item in
             report["flag0_vs_slot0_UsesAlpha"]["exceptions"]]
            == [("Kamaz/complete.dx", 19)],
            sum(report["alpha_texture_entries"].values()) == 2395,
        )
        if not all(checks):
            raise SystemExit("R4D.1 corpus assertions failed; inspect the written JSON")
    print(json.dumps({key: report[key] for key in (
        "draws", "unknown_0x24", "slot_presence", "flags_0x20_bytes",
        "flag0_vs_slot0_UsesAlpha", "flag2_to_mask_bit2", "alpha_texture_entries"
    )}, indent=2))


if __name__ == "__main__":
    main()
