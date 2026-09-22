#!/usr/bin/env python3
"""Compare legacy-generated DX files against an original with the modern parser."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.dx import parse_dx


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def draw_signature(model):
    return [
        {
            "tag": draw.tag,
            "record_path": draw.record_path,
            "vertex_base": draw.vertex_base,
            "local_vertex_max": draw.local_vertex_max,
            "index_start": draw.index_start,
            "index_count": draw.index_count,
            "texture_slots": list(draw.texture_tuple),
        }
        for draw in model.physical_draws
    ]


def raw_sections(model, size: int):
    global_start = (
        model.global_index_table.preamble_offset
        if model.global_index_table else model.trailing.offset
    )
    return {
        "header": (0, 16),
        "positions": (model.vertices.position_offset, model.vertices.normal_offset),
        "normals": (model.vertices.normal_offset, model.vertices.color_offset),
        "colors": (model.vertices.color_offset, model.uv_count_offset),
        "uv_and_local_headers": (model.uv_count_offset, model.local_index_offset),
        "local_indices": (model.local_index_offset, model.draw_table_offset),
        "draw_table": (model.draw_table_offset, global_start),
        "global_index_table": (global_start, model.trailing.offset),
        "trailing_data": (model.trailing.offset, size),
    }


def compare(original_path: Path, rebuilt_path: Path, label: str):
    original_bytes = original_path.read_bytes()
    rebuilt_bytes = rebuilt_path.read_bytes()
    original = parse_dx(original_path)
    try:
        rebuilt = parse_dx(rebuilt_path)
    except Exception as error:
        return {
            "label": label,
            "parse_success": False,
            "error": f"{type(error).__name__}: {error}",
            "byte_size": len(rebuilt_bytes),
            "sha256": sha256(rebuilt_bytes),
        }

    overlap = min(len(original_bytes), len(rebuilt_bytes))
    differing = [
        index
        for index in range(overlap)
        if original_bytes[index] != rebuilt_bytes[index]
    ]
    differing_count = len(differing) + abs(len(original_bytes) - len(rebuilt_bytes))
    sections = {}
    for name, (start, end) in raw_sections(original, len(original_bytes)).items():
        sections[name] = original_bytes[start:end] == rebuilt_bytes[start:end]

    original_global = (
        original.global_index_table.indices if original.global_index_table else None
    )
    rebuilt_global = (
        rebuilt.global_index_table.indices if rebuilt.global_index_table else None
    )
    return {
        "label": label,
        "parse_success": True,
        "modern_validated": rebuilt.diagnostics.validated,
        "modern_warnings": list(rebuilt.diagnostics.warnings),
        "modern_errors": list(rebuilt.diagnostics.errors),
        "byte_size": len(rebuilt_bytes),
        "sha256": sha256(rebuilt_bytes),
        "byte_identical": original_bytes == rebuilt_bytes,
        "differing_byte_count": differing_count,
        "first_differing_offset": f"0x{differing[0]:X}" if differing else None,
        "last_differing_offset": f"0x{differing[-1]:X}" if differing else None,
        "first_differing_offsets": [f"0x{value:X}" for value in differing[:64]],
        "section_bytes_equal": sections,
        "field_equality": {
            "vertex_count": original.vertex_count == rebuilt.vertex_count,
            "positions": original.vertices.positions == rebuilt.vertices.positions,
            "normals": original.vertices.normals == rebuilt.vertices.normals,
            "colors": original.vertices.colors == rebuilt.vertices.colors,
            "uv_sets": original.uv_sets == rebuilt.uv_sets,
            "local_indices": original.local_indices == rebuilt.local_indices,
            "global_indices": original_global == rebuilt_global,
            "draw_structure": draw_signature(original) == draw_signature(rebuilt),
            "trailing_data": original.trailing.data == rebuilt.trailing.data,
            "trailing_layout": (
                original.trailing.layout_family == rebuilt.trailing.layout_family
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("candidate", nargs="+", help="LABEL=PATH")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    original_bytes = args.original.read_bytes()
    records = []
    for item in args.candidate:
        if "=" not in item:
            parser.error("candidate must be LABEL=PATH")
        label, raw_path = item.split("=", 1)
        records.append(compare(args.original, Path(raw_path), label))
    report = {
        "schema_version": 1,
        "source_descriptor": args.original.name,
        "original": {
            "byte_size": len(original_bytes),
            "sha256": sha256(original_bytes),
        },
        "experiments": records,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for record in records:
        print(
            f"{record['label']}: parse={record['parse_success']} "
            f"validated={record.get('modern_validated')} "
            f"byte-identical={record.get('byte_identical')} "
            f"diff={record.get('differing_byte_count')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
