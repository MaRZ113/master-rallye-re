"""Read-only R4D vehicle draw/material inventory."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from master_rallye.assets import AssetResolver
from master_rallye.dx import parse_dx
from master_rallye.dxt import parse_dxt
from master_rallye.sidecar import resolve_sidecar, match_materials


def alpha_stats(path):
    texture = parse_dxt(path)
    counts = Counter(texture.bgra[3::4])
    return {
        "width": texture.width, "height": texture.height,
        "pixels": texture.width * texture.height,
        "opaque": counts[255], "zero": counts[0],
        "partial": sum(n for value, n in counts.items() if 0 < value < 255),
        "distinct_alpha": len(counts),
    }


def build(root):
    draws, textures = [], {}
    resources = 0
    for path in sorted(root.glob("*/*.dx"), key=lambda p: str(p).casefold()):
        model = parse_dx(path)
        if not model.diagnostics.validated:
            raise ValueError(f"unvalidated DX: {path}")
        resources += 1
        sidecar = resolve_sidecar(model, path.parent)
        by_number = {m.number: m for m in sidecar.sidecar.materials} if sidecar.sidecar else {}
        resolver = AssetResolver(path.parent)
        for draw in model.physical_draws:
            slots = [slot.value for slot in draw.texture_slots]
            candidates = []
            for candidate in match_materials(draw, sidecar.sidecar):
                material = by_number[candidate.number]
                candidates.append({
                    "number": candidate.number, "name": candidate.name,
                    "textures": [{
                        "slot": t.slot, "stem": t.resource_stem,
                        "HasAlpha": t.has_alpha, "UsesAlpha": t.uses_alpha,
                        "IsNoise": t.is_noise,
                    } for t in sorted(material.textures, key=lambda t: t.slot)],
                })
            slot_alpha = []
            for value in slots:
                if value.casefold() == "null":
                    slot_alpha.append(None)
                    continue
                resolved = resolver.resolve_texture(value)
                if resolved is None:
                    slot_alpha.append({"missing": True})
                    continue
                key = f"{path.parent.name}/{resolved.name}"
                if key not in textures:
                    textures[key] = alpha_stats(resolved)
                slot_alpha.append({"texture": key, **textures[key]})
            start, end = draw.vertex_range
            colors = model.vertices.colors[start * 4:(end + 1) * 4]
            color_words = [colors[i:i + 4] for i in range(0, len(colors), 4)]
            signature = (f"slots={len(slots)};"
                         f"null={''.join('1' if v.casefold() == 'null' else '0' for v in slots)};"
                         f"tag={draw.tag};f20={draw.flags_0x20.hex()}")
            draws.append({
                "vehicle": path.parent.name, "resource": f"{path.parent.name}/{path.name}",
                "draw_index": draw.draw_index, "record_path": draw.record_path,
                "draw_tag": draw.tag, "group_label": draw.group_label,
                "top_level_index": draw.top_level_index,
                "vertex_base": draw.vertex_base, "local_vertex_max": draw.local_vertex_max,
                "index_start": draw.index_start, "index_count": draw.index_count,
                "texture_slots": slots,
                "non_null_slots": [{"slot": i, "name": v} for i, v in enumerate(slots) if v.casefold() != "null"],
                "texture_alpha": slot_alpha,
                "sidecar": sidecar.selected_path.name if sidecar.selected_path else None,
                "sidecar_ambiguous": sidecar.ambiguous,
                "material_candidates": candidates,
                "material_ambiguity": "unique" if len(candidates) == 1 else "unmatched" if not candidates else "multiple",
                "vertex_colors": {
                    "vertex_count": len(color_words),
                    "distinct_words": len(set(color_words)),
                    "all_255_count": sum(c == bytes((255, 255, 255, 255)) for c in color_words),
                    "byte_min": [min(colors[i::4], default=0) for i in range(4)],
                    "byte_max": [max(colors[i::4], default=0) for i in range(4)],
                },
                "control": {
                    "core_offset": draw.core_offset,
                    "unknown_0x14": draw.unknown_0x14,
                    "unknown_0x18": draw.unknown_0x18,
                    "unknown_0x1c_bits": struct.unpack("<I", struct.pack("<f", draw.unknown_0x1c_float))[0],
                    "flags_0x20_hex": draw.flags_0x20.hex(),
                    "unknown_0x24": draw.unknown_0x24,
                    "prefix_words": list(draw.control_words),
                },
                "signature": signature,
            })
    summary = {
        "vehicle_count": len({e["vehicle"] for e in draws}),
        "resource_count": resources, "draw_count": len(draws),
        "unique_material_match": sum(e["material_ambiguity"] == "unique" for e in draws),
        "multiple_material_matches": sum(e["material_ambiguity"] == "multiple" for e in draws),
        "unmatched_materials": sum(e["material_ambiguity"] == "unmatched" for e in draws),
        "referenced_texture_instances": len(textures),
        "alpha_bearing_texture_instances": sum(t["zero"] + t["partial"] > 0 for t in textures.values()),
        "slot_counts": dict(sorted(Counter(len(e["texture_slots"]) for e in draws).items())),
        "draw_tags": dict(sorted(Counter(e["draw_tag"] for e in draws).items())),
    }
    return {
        "schema_version": 1, "source": "external DataGx/Vehicles (path omitted)",
        "summary": summary, "signatures": dict(Counter(e["signature"] for e in draws).most_common()),
        "textures": textures, "draws": draws,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.vehicle_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    lines = [
        "{",
        '  "schema_version": 1,',
        '  "source": ' + compact(report["source"]) + ",",
        '  "summary": ' + compact(report["summary"]) + ",",
        '  "signatures": ' + compact(report["signatures"]) + ",",
        '  "textures": {',
    ]
    items = list(report["textures"].items())
    lines += [
        "    " + compact(key) + ": " + compact(value) + ("," if i + 1 < len(items) else "")
        for i, (key, value) in enumerate(items)
    ]
    lines += ['  },', '  "draws": [']
    lines += [
        "    " + compact(draw) + ("," if i + 1 < len(report["draws"]) else "")
        for i, draw in enumerate(report["draws"])
    ]
    lines += ["  ]", "}"]
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
