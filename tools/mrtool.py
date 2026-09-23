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

from master_rallye.audit import audit_texture_tree
from master_rallye.coverage import write_coverage_reports
from master_rallye.collision_analysis import write_collision_corpus_reports
from master_rallye.dx import parse_dx
from master_rallye.export.gltf import export_gltf
from master_rallye.export.obj import export_obj
from master_rallye.sidecar import apply_material_candidates, parse_sidecar, resolve_sidecar
from master_rallye.roles import write_vehicle_role_reports
from master_rallye.r4e_writer import patch_dx_attributes, write_dx_attributes
from master_rallye.texture_authoring import export_texture, replace_texture
from master_rallye.vehicle_project import VehicleProject, validate_vehicle, build_vehicle_mod
from master_rallye.vehicle_packaging import (
    vehicle_dependencies, texture_users, bundle_vehicle, pack_sma, unpack_sma,
)
import hashlib

def r4e_command(args):
    command=args.command
    if command=="inspect-vehicle":
        result=vehicle_dependencies(args.vehicle_dir)
    elif command=="texture-users":
        result=texture_users(args.vehicle_dir,args.texture)
    elif command=="export-texture":
        result=export_texture(args.source,args.output)
    elif command=="replace-texture":
        result=replace_texture(args.source,args.png,args.output,expected_source_sha256=args.source_sha256)
    elif command=="validate-edit":
        data=args.source.read_bytes()
        spec=json.loads(args.edit.read_text(encoding="utf-8"))
        expected=spec.get("source_sha256")
        if hashlib.sha256(data).hexdigest()!=expected:
            raise ValueError("source SHA-256 mismatch")
        patch=patch_dx_attributes(data,positions=spec.get("positions"),normals=spec.get("normals"),uv_sets=spec.get("uv_sets"),colors=spec.get("colors"),material_alpha={int(k):v for k,v in spec.get("material_alpha",{}).items()},material_env={int(k):v for k,v in spec.get("material_env",{}).items()})
        result=patch.to_dict()
        if args.output:
            if args.output.resolve()==args.source.resolve():
                raise ValueError("refusing to overwrite DX source")
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_bytes(patch.data)
    elif command=="bundle-vehicle":
        spec=json.loads(args.replacements.read_text(encoding="utf-8"))
        result=bundle_vehicle(args.vehicle_dir,{key:Path(value) for key,value in spec.items()},args.output)
    elif command=="pack-sma":
        result=pack_sma(args.root,args.output,json.loads(args.overrides.read_text(encoding="utf-8")) if args.overrides else None)
    elif command=="unpack-sma":
        result=unpack_sma(args.source,args.output)
    elif command=="validate-vehicle":
        project=VehicleProject.load(args.project)
        result=validate_vehicle(project)
    elif command=="build-vehicle-mod":
        project=VehicleProject.load(args.project)
        result=build_vehicle_mod(project,args.output,sma=args.sma,sma_root=args.sma_root)
    else:
        raise ValueError(f"unsupported command {command}")
    if command in {"validate-vehicle", "build-vehicle-mod"}:
        dependencies = result.get("dependency_manifest") or {}
        display = {key:value for key,value in result.items()
                   if key not in {"compiled", "dependency_manifest"}}
        display["dependencies"] = {
            "binding_count": len(dependencies.get("bindings", [])),
            "unresolved_count": dependencies.get("unresolved_count")}
        print(json.dumps(display,indent=2,ensure_ascii=False))
        return 1 if result["status"] == "FAIL" else 0
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0



def load_sidecar(model, input_path: Path, explicit: Path | None):
    if explicit is not None:
        return parse_sidecar(explicit) if explicit.exists() else None
    return resolve_sidecar(model, input_path.parent).sidecar


def inspect_command(args) -> int:
    model = parse_dx(args.input)
    sidecar = load_sidecar(model, args.input, args.sidecar)
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
    sidecar = load_sidecar(model, args.input, args.sidecar)
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


def audit_textures_command(args) -> int:
    report = audit_texture_tree(args.input)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    summary = report["summary"]
    print(
        f"texture audit: {summary['dxt_present']} present, "
        f"{summary['apparently_unreferenced']} apparently unreferenced, "
        f"{summary['missing_referenced_resources']} missing references",
        file=sys.stderr,
    )
    return 0


def vehicle_roles_command(args) -> int:
    markdown = args.markdown or args.report.with_suffix(".md")
    report = write_vehicle_role_reports(
        args.vehicle_root, args.report, markdown, args.comparison
    )
    summary = report["summary"]
    print(
        f"vehicle roles: {summary['vehicle_folder_count']} folders, "
        f"{summary['dx_resource_count']} DX, {summary['car_complete_pair_count']} car/complete pairs, "
        f"{summary['parse_failure_count']} failures"
    )
    return 0


def collision_corpus_command(args) -> int:
    markdown = args.markdown or args.report.with_suffix(".md")
    report = write_collision_corpus_reports(args.vehicle_root, args.report, markdown)
    summary = report["summary"]
    print(
        f"collision corpus: {summary['dx_resource_count']} DX, "
        f"tag101 {summary['tag101_count']}, validated {summary['tag101_validated_count']}, "
        f"failures {summary['failed_resource_count']}"
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

    audit = commands.add_parser("audit-textures", help="read-only DX/TXT/DXT reference audit")
    audit.add_argument("input", type=Path)
    audit.add_argument("--report", type=Path)
    audit.set_defaults(function=audit_textures_command)

    roles = commands.add_parser("vehicle-roles", help="read-only vehicle resource-role matrix")
    roles.add_argument("vehicle_root", type=Path)
    roles.add_argument("--report", required=True, type=Path)
    roles.add_argument("--markdown", type=Path)
    roles.add_argument("--comparison", type=Path)
    roles.set_defaults(function=vehicle_roles_command)

    collision = commands.add_parser("scan-collision", help="read-only vehicle collision-section scan")
    collision.add_argument("vehicle_root", type=Path)
    collision.add_argument("--report", required=True, type=Path)
    collision.add_argument("--markdown", type=Path)
    collision.set_defaults(function=collision_corpus_command)
    vehicle=commands.add_parser("inspect-vehicle",help="exact DX/DXT dependencies for one vehicle")
    vehicle.add_argument("vehicle_dir",type=Path)
    vehicle.set_defaults(function=r4e_command)
    users=commands.add_parser("texture-users",help="reverse DX draw users for a vehicle DXT")
    users.add_argument("vehicle_dir",type=Path)
    users.add_argument("texture")
    users.set_defaults(function=r4e_command)
    tex_export=commands.add_parser("export-texture",help="DXT to upright PNG")
    tex_export.add_argument("source",type=Path)
    tex_export.add_argument("--output",required=True,type=Path)
    tex_export.set_defaults(function=r4e_command)
    tex_replace=commands.add_parser("replace-texture",help="same-size PNG into header-preserving DXT")
    tex_replace.add_argument("source",type=Path)
    tex_replace.add_argument("png",type=Path)
    tex_replace.add_argument("--source-sha256",required=True)
    tex_replace.add_argument("--output",required=True,type=Path)
    tex_replace.set_defaults(function=r4e_command)
    edit=commands.add_parser("validate-edit",help="validate and optionally write source-indexed DX edits")
    edit.add_argument("source",type=Path)
    edit.add_argument("edit",type=Path)
    edit.add_argument("--output",type=Path)
    edit.set_defaults(function=r4e_command)
    bundle=commands.add_parser("bundle-vehicle",help="stage validated vehicle replacements")
    bundle.add_argument("vehicle_dir",type=Path)
    bundle.add_argument("replacements",type=Path,help="JSON mapping original basename to replacement path")
    bundle.add_argument("--output",required=True,type=Path)
    bundle.set_defaults(function=r4e_command)
    unpack=commands.add_parser("unpack-sma",help="unpack ZIP-compatible Data.sma")
    unpack.add_argument("source",type=Path)
    unpack.add_argument("--output",required=True,type=Path)
    unpack.set_defaults(function=r4e_command)
    pack=commands.add_parser("pack-sma",help="pack validated DataGx/DataGame tree")
    pack.add_argument("root",type=Path)
    pack.add_argument("--output",required=True,type=Path)
    pack.add_argument("--overrides",type=Path,help="JSON archive path to replacement file map")
    pack.set_defaults(function=r4e_command)
    validate=commands.add_parser("validate-vehicle",help="check a VehicleProject with actionable PASS/WARN/FAIL diagnostics")
    validate.add_argument("project",type=Path)
    validate.set_defaults(function=r4e_command)
    build=commands.add_parser("build-vehicle-mod",help="validate project edits and stage a vehicle mod")
    build.add_argument("project",type=Path)
    build.add_argument("--output",required=True,type=Path)
    build.add_argument("--sma",type=Path)
    build.add_argument("--sma-root",type=Path,help="full unpacked source archive required for --sma")
    build.set_defaults(function=r4e_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
