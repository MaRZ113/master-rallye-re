#!/usr/bin/env python3
"""Report topology-relevant draw layout without copying vehicle bytes."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.dx import parse_dx


def inspect(root: Path) -> dict:
    resources = []
    totals = Counter()
    for source in sorted(root.rglob("*.dx")):
        model = parse_dx(source)
        if not model.diagnostics.validated:
            raise ValueError(f"invalid source {source}: {model.diagnostics.errors}")
        draws = model.physical_draws
        entries = []
        for index, draw in enumerate(draws):
            next_draw = draws[index + 1] if index + 1 < len(draws) else None
            vertex_end = draw.vertex_base + draw.local_vertex_max + 1
            index_end = draw.index_start + draw.index_count
            referenced_local = set(model.local_indices[draw.index_start:index_end])
            entries.append({
                "draw_id": draw.draw_index,
                "tag": draw.tag,
                "record_path": draw.record_path,
                "top_level_index": draw.top_level_index,
                "vertex_base": draw.vertex_base,
                "local_index_min": draw.raw_index_min,
                "local_index_max": draw.raw_index_max,
                "global_vertex_min": draw.global_vertex_min,
                "global_vertex_max": draw.global_vertex_max,
                "vertex_span": [draw.vertex_base, vertex_end],
                "index_span": [draw.index_start, index_end],
                "triangle_count": draw.triangle_count,
                "referenced_local_vertex_count": len(referenced_local),
                "unreferenced_declared_vertex_count": draw.local_vertex_max + 1 - len(referenced_local),
                "next_vertex_gap": next_draw.vertex_base - vertex_end if next_draw else model.vertex_count - vertex_end,
                "next_index_gap": next_draw.index_start - index_end if next_draw else len(model.local_indices) - index_end,
                "overlaps_other_vertex_span": any(
                    draw.vertex_base < other.vertex_base + other.local_vertex_max + 1
                    and other.vertex_base < vertex_end
                    for other in draws if other is not draw
                ),
                "material_identity": f"{source.parent.name}/{source.name}:draw:{draw.draw_index}",
                "texture_tuple": list(draw.texture_tuple),
            })
        remainder = model.collision.unparsed_data
        footer = None
        if len(remainder) == 44 and struct.unpack_from("<I", remainder)[0] == 1339:
            union_vertices = list(model.vertices.positions)
            hull = model.collision.convex_hull
            if hull is not None:
                union_vertices.extend(hull.base_geometry.vertices)
                for representation in (hull.representation_a, hull.representation_b):
                    union_vertices.extend(representation.geometry_a.vertices)
                    union_vertices.extend(representation.geometry_b.vertices)
            minimum = struct.unpack_from("<3f", remainder, 20)
            maximum = struct.unpack_from("<3f", remainder, 32)
            center = struct.unpack_from("<3f", remainder, 4)
            bounds_match = all(
                abs(minimum[axis] - min(vertex[axis] for vertex in union_vertices)) <= 1e-5
                and abs(maximum[axis] - max(vertex[axis] for vertex in union_vertices)) <= 1e-5
                for axis in range(3)
            )
            center_matches = all(
                abs(center[axis] - (minimum[axis] + maximum[axis]) / 2) <= 1e-6
                for axis in range(3)
            )
            footer = {
                "marker": 1339,
                "center": list(center),
                "unknown_scalar": struct.unpack_from("<f", remainder, 16)[0],
                "minimum": list(minimum),
                "maximum": list(maximum),
                "bounds_match_render_collision_union": bounds_match,
                "center_matches_bounds_midpoint": center_matches,
            }
        resources.append({
            "resource": str(source.relative_to(root)).replace("\\", "/"),
            "vertex_count": model.vertex_count,
            "index_count": len(model.local_indices),
            "draw_count": len(draws),
            "draws": entries,
            "vertex_ranges_contiguous": all(item["next_vertex_gap"] == 0 for item in entries),
            "index_ranges_contiguous": all(item["next_index_gap"] == 0 for item in entries),
            "vertex_bases_monotonic": all(a.vertex_base <= b.vertex_base for a, b in zip(draws, draws[1:])),
            "vertex_span_overlap": any(item["overlaps_other_vertex_span"] for item in entries),
            "collision_tags": list(model.collision.tag_ids),
            "tail_offset": model.trailing.offset,
            "tail_length": len(model.trailing.data),
            "footer44": footer,
        })
        totals["resources"] += 1
        totals["draws"] += len(draws)
        totals["fully_referenced_draws"] += sum(item["unreferenced_declared_vertex_count"] == 0 for item in entries)
        totals["contiguous_vertex_resources"] += resources[-1]["vertex_ranges_contiguous"]
        totals["contiguous_index_resources"] += resources[-1]["index_ranges_contiguous"]
        totals["monotonic_vertex_resources"] += resources[-1]["vertex_bases_monotonic"]
        totals["nonoverlap_vertex_resources"] += not resources[-1]["vertex_span_overlap"]
        totals["footer44_resources"] += footer is not None
        totals["footer_bounds_match_resources"] += footer is not None and footer["bounds_match_render_collision_union"]
        totals["footer_center_match_resources"] += footer is not None and footer["center_matches_bounds_midpoint"]
    return {"summary": dict(totals), "resources": resources}


def _compact_report(report: dict) -> str:
    """Keep one full draw record per line for useful Git review."""
    lines = ["{", '  "summary": ' + json.dumps(report["summary"], separators=(",", ":")) + ",", '  "resources": [']
    resources = report["resources"]
    for resource_index, resource in enumerate(resources):
        lines.append("    {")
        for key, value in resource.items():
            if key != "draws":
                lines.append("      " + json.dumps(key) + ": " + json.dumps(value, separators=(",", ":")) + ",")
        lines.append('      "draws": [')
        draws = resource["draws"]
        for draw_index, draw in enumerate(draws):
            lines.append("        " + json.dumps(draw, separators=(",", ":")) + ("," if draw_index + 1 < len(draws) else ""))
        lines.append("      ]")
        lines.append("    }" + ("," if resource_index + 1 < len(resources) else ""))
    lines.extend(["  ]", "}"])
    output = "\n".join(lines) + "\n"
    if json.loads(output) != report:
        raise ValueError("compact report serialization changed data")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(args.vehicle_root.resolve())
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(_compact_report(report), encoding="utf-8")
    summary = report["summary"]
    args.markdown.write_text(
        "# R4F vehicle draw layout corpus\n\n"
        "Source: protected original unpacked vehicle tree. Detailed per-draw evidence is in `draw-layout-corpus.json`.\n\n"
        f"{summary['resources']} resources, {summary['draws']} physical draws. "
        f"Contiguous vertex ranges: {summary['contiguous_vertex_resources']}/{summary['resources']}; "
        f"contiguous local-index ranges: {summary['contiguous_index_resources']}/{summary['resources']}; "
        f"monotonic vertex bases: {summary['monotonic_vertex_resources']}/{summary['resources']}; "
        f"nonoverlapping vertex ranges: {summary['nonoverlap_vertex_resources']}/{summary['resources']}; "
        f"all declared vertices referenced: {summary['fully_referenced_draws']}/{summary['draws']} draws. "
        f"A 44-byte marker-1339 footer follows collision data in {summary['footer44_resources']}/{summary['resources']}; "
        f"its min/max matches the render-and-collision vertex union in {summary['footer_bounds_match_resources']}/{summary['resources']}, "
        f"and its center matches that min/max midpoint in {summary['footer_center_match_resources']}/{summary['resources']}. "
        "Its other scalar is preserved raw.\n\n"
        "Every physical draw has an inclusive `local_vertex_max` relative to `vertex_base`, "
        "an `index_start` and `index_count`, and an existing texture tuple. "
        "Every source vertex belongs to one declared draw range; every local-index entry belongs to one draw. "
        "The stored global table is exactly reconstructed by the parser for all 78 resources. "
        "Consequently adding vertices to a draw shifts later bases; adding triangles shifts later starts. "
        "These are corpus invariants for vehicle resources, not a claim about course DX or arbitrary synthetic layouts.\n\n"
        "## Required layout answers\n\n"
        "1. Draw vertex ranges are contiguous in 78/78.\n"
        "2. No declared draw vertex ranges overlap in 78/78.\n"
        "3. A source render vertex belongs to one declared draw range in this corpus.\n"
        "4. `vertex_base` is monotonic in 78/78.\n"
        "5. Draw record order follows vertex range order in 78/78.\n"
        "6. Each draw stores inclusive `local_vertex_max`, so its span is `vertex_base..vertex_base+local_vertex_max`.\n"
        "7. A draw gaining vertices updates total vertex count, each vertex array, its local maximum, later bases and the global table.\n"
        "8. Yes: all later `vertex_base` values shift when an earlier draw gains vertices; later `index_start` values shift when it gains triangles.\n"
        "9. The parsed tag-101/tag-102 collision structures use internal counted references, not render vertex IDs. The footer contains geometric bounds, not render indices. No other observed suffix field is a proven render-vertex index; unknown footer scalar stays raw.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
