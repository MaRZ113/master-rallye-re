#!/usr/bin/env python3
"""Minimal R1 research CLI for Master Rallye vehicle assets."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.coverage import write_coverage_reports
from master_rallye.dx import parse_dx
from master_rallye.export.gltf import export_gltf
from master_rallye.export.obj import export_obj
from master_rallye.sidecar import apply_material_candidates, parse_sidecar


def load_sidecar(input_path: Path, explicit: Path | None):
    path = explicit or input_path.with_suffix(".txt")
    return parse_sidecar(path) if path.exists() else None


def inspect_command(args) -> int:
    model = parse_dx(args.input)
    sidecar = load_sidecar(args.input, args.sidecar)
    apply_material_candidates(model.physical_draws, sidecar)
    summary = model.to_summary()
    summary["sidecar_present"] = sidecar is not None
    summary["draws"] = [
        {
            "draw_index": draw.draw_index,
            "record_path": draw.record_path,
            "tag": draw.tag,
            "offset": f"0x{draw.offset:X}",
            "group_label": draw.group_label,
            "vertex_base": draw.vertex_base,
            "local_vertex_max": draw.local_vertex_max,
            "index_start": draw.index_start,
            "index_count": draw.index_count,
            "texture_slots": [slot.value for slot in draw.texture_slots],
            "material_candidates": [
                {"number": candidate.number, "name": candidate.name}
                for candidate in draw.material_candidates
            ],
        }
        for draw in model.physical_draws
    ]
    payload = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


def export_command(args) -> int:
    model = parse_dx(args.input)
    if args.strict and not model.diagnostics.validated:
        raise SystemExit("strict export refused: geometry validation did not pass")
    sidecar = load_sidecar(args.input, args.sidecar)
    texture_directory = args.texture_directory or args.input.parent
    if args.format == "gltf":
        result = export_gltf(
            model,
            args.output,
            sidecar,
            texture_directory,
            args.flip_v,
            args.strict,
        )
        print(
            f"exported glTF: {result.primitive_count} primitives, "
            f"{result.texture_count} decoded textures -> {result.gltf_path}"
        )
        if result.warnings:
            print(f"warnings: {len(result.warnings)}")
    else:
        obj_path, _ = export_obj(
            model, args.output, sidecar, texture_directory, args.flip_v
        )
        print(f"exported OBJ -> {obj_path}")
    return 0


def scan_command(args) -> int:
    markdown = args.markdown or args.report.with_suffix(".md")
    unknown = args.unknown_records or args.report.with_name("unknown-records.json")
    report = write_coverage_reports(args.vehicle_root, args.report, markdown, unknown)
    summary = report["summary"]
    print(
        f"vehicle DX {summary['total_dx']}: parsed {summary['parsed']}, "
        f"validated {summary['validated']}, fully {summary['fully_accounted']}, "
        f"partial {summary['partially_accounted']}, failed {summary['failed']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mrtool", description="Master Rallye clean-room research CLI")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="inspect one vehicle DX")
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--sidecar", type=Path)
    inspect.add_argument("--json", type=Path, help="write JSON instead of stdout")
    inspect.set_defaults(function=inspect_command)

    export = commands.add_parser("export", help="export one parsed vehicle resource")
    export.add_argument("input", type=Path)
    export.add_argument("--format", choices=("gltf", "obj"), default="gltf")
    export.add_argument("--output", required=True, type=Path)
    export.add_argument("--sidecar", type=Path)
    export.add_argument("--texture-directory", type=Path)
    export.add_argument(
        "--flip-v",
        action="store_true",
        help="apply the evidenced 1-V coordinate transform, independent of PNG row flipping",
    )
    export.add_argument("--strict", action="store_true")
    export.set_defaults(function=export_command)

    scan = commands.add_parser("scan-vehicles", help="scan only DataGx/Vehicles")
    scan.add_argument("vehicle_root", type=Path)
    scan.add_argument("--report", required=True, type=Path)
    scan.add_argument("--markdown", type=Path)
    scan.add_argument("--unknown-records", type=Path)
    scan.set_defaults(function=scan_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
