#!/usr/bin/env python3
"""Read-only R-BRIDGE2 inventory, DX comparison, and complete-wheel geometry scan."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any

from master_rallye.bridge2_analysis import (
    RAW_DX_COMPATIBILITY_MATRIX,
    analyze_complete_wheel_file,
    audit_vehicle_config_roots,
    compare_dx_assets,
    parse_vehicle_properties,
    validate_compatibility_matrix,
    validate_transfer_provenance,
    wheel_dimension_properties,
)
from master_rallye.demo_dx import inspect_demo_dx
from master_rallye.dx import parse_dx_bytes
from master_rallye.gxm import (
    parse_gxm_geometry_prefix_bytes,
    parse_gxm_prefix_bytes,
    parse_gxm_triangle_prefix_bytes,
)
from master_rallye.sidecar import parse_sidecar


VEHICLES_BY_BUILD: dict[str, tuple[str, ...]] = {
    "8.4.1": ("Jump", "Trooper", "Rav4"),
    "9.3.1": ("Jump", "Trooper", "Rav4"),
    "9.10.0": ("Jump", "Navara"),
    "retail": ("Jump", "Navara", "Trooper", "Rav4"),
}
INVENTORY_SUFFIXES = {".dx", ".gxm", ".txt", ".dxt", ".gxi"}
TRANSFER_CLAIMS = [
    {
        "vehicle": vehicle,
        "evidence": "HUMAN_RUNTIME_CONFIRMED",
        "source_build": "UNKNOWN_FROM_USER_REPORT",
        "source_hashes": None,
        "cooker_build": "9.10.0",
        "generated_hashes": None,
        "target_build": "retail",
        "target_slot": "Navara" if vehicle == "Trooper" else "UNKNOWN_FROM_USER_REPORT",
        "working_observations": ["body/model render", "damage"],
        "known_issue": "race/runtime wheel placement differs from complete-model presentation",
        "resource_roles_tested": ["car", "complete", "wheel", "materials", "damage"],
        "physics_equivalence": "NOT_TESTED",
        "provenance_note": (
            "The user confirmed this vehicle transfer through the 9.10.0 cooker. "
            "The supplied runtime report did not include source corpus identity or file hashes; "
            "the Navara target slot is explicitly established for Trooper only."
        ),
    }
    for vehicle in ("Trooper", "Rav4")
]


def _hash(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    record: dict[str, Any] = {
        "path": path.relative_to(root).as_posix(),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    suffix = path.suffix.casefold()
    if suffix == ".dx":
        if len(data) >= 16:
            record["header_words"] = list(struct.unpack_from("<4I", data))
        try:
            view = inspect_demo_dx(data, path.name)
            record["common_vehicle_dx_parser"] = "ACCEPTED"
            record["vehicle_dx"] = {
                "vertex_count": len(view.positions),
                "local_index_count": len(view.local_indices),
                "draw_region_size": len(view.draw_raw),
                "collision_tags": list(view.collision.tag_ids),
            }
        except Exception as exc:
            record["common_vehicle_dx_parser"] = "REJECTED"
            record["common_vehicle_dx_error"] = f"{type(exc).__name__}: {exc}"
        try:
            parse_dx_bytes(data, path.name)
            record["retail_typed_dx_parser"] = "ACCEPTED"
        except Exception as exc:
            record["retail_typed_dx_parser"] = "REJECTED"
            record["retail_typed_dx_error"] = f"{type(exc).__name__}: {exc}"
    elif suffix == ".gxm":
        try:
            prefix = parse_gxm_prefix_bytes(data, path.name)
            summary: dict[str, Any] = {
                "status": "PREFIX_ACCEPTED",
                "prefix_kind": prefix.prefix_kind,
                "header_words": list(prefix.header_words),
                "material_count": len(prefix.materials),
                "tail_offset": prefix.tail_offset,
                "tail_size": prefix.tail_size,
            }
            if prefix.prefix_kind == "material_table":
                geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
                triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
                summary["geometry_prefix"] = {
                    "vector_a_count": geometry.vector_a_count,
                    "vector_b_count": geometry.vector_b_count,
                    "triangle_record_count": triangles.record_count,
                    "vector_c_count": triangles.vector_c_count,
                    "hierarchy_offset": triangles.hierarchy_offset,
                }
            record["gxm"] = summary
        except Exception as exc:
            record["gxm"] = {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
    return record


def _corpus_paths(corpora_root: Path) -> dict[str, Path]:
    return {
        "8.4.1": corpora_root / "demo-8.4.1",
        "9.3.1": corpora_root / "demo-9.3.1",
        "9.10.0": corpora_root / "demo-9.10.0",
        "retail": corpora_root / "retail",
    }


def _data_gx_root(build_root: Path, build: str) -> Path:
    return build_root / "DataGx" if build != "retail" else build_root / "Data.sma_unpacked" / "DataGx"


def _vehicle_root(build_root: Path, build: str) -> Path:
    return _data_gx_root(build_root, build) / "Vehicles"


def _dx_revision_inventory(root: Path) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    parser_counts: Counter[str] = Counter()
    files = []
    for path in sorted(root.rglob("*.dx"), key=lambda item: item.as_posix().casefold()):
        data = path.read_bytes()
        revision = struct.unpack_from("<I", data, 4)[0] if len(data) >= 8 else None
        counts[str(revision)] += 1
        try:
            parse_dx_bytes(data, str(path))
            status = "ACCEPTED"
        except Exception as exc:
            status = "REJECTED"
            error = f"{type(exc).__name__}: {exc}"
            files.append({"path": path.relative_to(root).as_posix(), "revision": revision,
                          "retail_typed_parser": status, "error": error})
            parser_counts[status] += 1
            continue
        files.append({"path": path.relative_to(root).as_posix(), "revision": revision,
                      "retail_typed_parser": status})
        parser_counts[status] += 1
    return {"file_count": len(files), "revision_counts": dict(counts),
            "retail_typed_parser_counts": dict(parser_counts), "files": files}


def _asset_inventory(corpora: dict[str, Path]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for build, vehicles in VEHICLES_BY_BUILD.items():
        root = _vehicle_root(corpora[build], build)
        build_rows = {}
        for vehicle in vehicles:
            folder = root / vehicle
            if not folder.is_dir():
                build_rows[vehicle] = {"status": "MISSING"}
                continue
            rows = [
                _hash(path, root)
                for path in sorted(folder.rglob("*"), key=lambda item: item.as_posix().casefold())
                if path.is_file() and path.suffix.casefold() in INVENTORY_SUFFIXES
            ]
            build_rows[vehicle] = {"status": "PRESENT", "files": rows}
        report[build] = build_rows
    return report


def _wheel_geometry(corpora: dict[str, Path]) -> list[dict[str, Any]]:
    result = []
    for build, vehicles in VEHICLES_BY_BUILD.items():
        root = _vehicle_root(corpora[build], build)
        for vehicle in vehicles:
            directory = root / vehicle
            gxm = directory / "complete.gxm"
            if not gxm.is_file():
                continue
            sidecar = directory / "complete.txt"
            parsed = analyze_complete_wheel_file(gxm, sidecar if sidecar.is_file() else None)
            result.append({
                "build": build,
                "vehicle": vehicle,
                "hierarchy_status": parsed.hierarchy_status,
                "hierarchy_error": parsed.hierarchy_error,
                "source": parsed.source,
                "size": parsed.file_size,
                "sha256": parsed.sha256,
                "header_words": list(parsed.header_words),
                "triangle_record_count": parsed.triangle_record_count,
                "vector_c_count": parsed.vector_c_count,
                "coordinate_transform_used_for_report": "(x,y,z)->(x,z,-y)",
                "interpretation_limit": "geometry centers from named mesh spans, not runtime hardpoints",
                "wheels": [
                    {
                        "name": mesh.name,
                        "record_span": [mesh.record_start, mesh.record_count],
                        "span_source": mesh.span_source,
                        "unique_vector_c_indices": list(mesh.unique_vector_c_indices),
                        "source_aabb_center": list(mesh.source_aabb_center),
                        "dx_aabb_center": list(mesh.dx_aabb_center),
                        "dx_aabb_minimum": list(mesh.dx_aabb_minimum),
                        "dx_aabb_maximum": list(mesh.dx_aabb_maximum),
                    }
                    for mesh in parsed.meshes
                ],
            })
    return result


def _vehicle_config(corpora: dict[str, Path]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for build, vehicles in VEHICLES_BY_BUILD.items():
        build_root = corpora[build]
        if build == "retail":
            xml_path = build_root / "Data.sma_unpacked" / "DataGame" / "vehicles.xml"
        else:
            xml_path = build_root / "DataGame" / "vehicles.xml"
        if not xml_path.is_file():
            result[build] = {"status": "MISSING"}
            continue
        result[build] = {"root_audit": audit_vehicle_config_roots(xml_path)}
        result[build].update({
            vehicle: wheel_dimension_properties(parse_vehicle_properties(xml_path, vehicle))
            for vehicle in vehicles
        })
    return result


def _comparisons(corpora: dict[str, Path]) -> dict[str, Any]:
    result: dict[str, Any] = {"jump_wheel_adjacent_generations": {}, "navara_910_vs_retail": {}}
    jump_paths = {
        build: _vehicle_root(root, build) / "Jump" / "wheel.dx"
        for build, root in corpora.items()
    }
    for first, second in (("8.4.1", "9.3.1"), ("9.3.1", "9.10.0"), ("9.10.0", "retail")):
        left, right = jump_paths[first], jump_paths[second]
        if left.is_file() and right.is_file():
            key = f"{first}_to_{second}"
            result["jump_wheel_adjacent_generations"][key] = compare_dx_assets(
                left.read_bytes(), right.read_bytes(), first_source=f"{first}/Jump/wheel.dx",
                second_source=f"{second}/Jump/wheel.dx")
    for role in ("car", "complete", "wheel"):
        left = _vehicle_root(corpora["9.10.0"], "9.10.0") / "Navara" / f"{role}.dx"
        right = _vehicle_root(corpora["retail"], "retail") / "Navara" / f"{role}.dx"
        if left.is_file() and right.is_file():
            result["navara_910_vs_retail"][role] = compare_dx_assets(
                left.read_bytes(), right.read_bytes(), first_source=f"9.10.0/Navara/{role}.dx",
                second_source=f"retail/Navara/{role}.dx")
    for role in ("car", "complete", "wheel"):
        left = _vehicle_root(corpora["9.10.0"], "9.10.0") / "Jump" / f"{role}.dx"
        right = _vehicle_root(corpora["retail"], "retail") / "Jump" / f"{role}.dx"
        if left.is_file() and right.is_file():
            result.setdefault("jump_910_vs_retail", {})[role] = compare_dx_assets(
                left.read_bytes(), right.read_bytes(), first_source=f"9.10.0/Jump/{role}.dx",
                second_source=f"retail/Jump/{role}.dx")
    return result


def _static_wheel_trace(corpora: dict[str, Path]) -> dict[str, Any]:
    executable = corpora["retail"] / "MRallye.exe"
    digest = hashlib.sha256(executable.read_bytes()).hexdigest() if executable.is_file() else None
    return {
        "evidence": "STATIC_EXECUTABLE_DISASSEMBLY",
        "executable": "MRallye.exe",
        "sha256": digest,
        "functions": {
            "read_vehicle_dimensions": "0x004BC590",
            "wheel_instance_creation_loop": "0x004BFE00",
            "wheel_instance_constructor": "0x004BFFA0",
            "wheel_transform_update": "0x004C00D0",
        },
        "config_path_templates": [
            "Vehicles/Car%d/Dimensions/WheelBase",
            "Vehicles/Car%d/Dimensions/TrackWidthFront",
            "Vehicles/Car%d/Dimensions/TrackWidthRear",
            "Vehicles/Car%d/Suspension/Front/RideHeight",
            "Vehicles/Car%d/Suspension/Rear/RideHeight",
            "Vehicles/Car%d/Suspension/Front/MaxDroop",
        ],
        "wheel_instance_fields": {
            "+0x10": "wheel index 0..3",
            "+0x18": "WheelBase",
            "+0x1C": "Front RideHeight",
            "+0x20": "Rear RideHeight",
            "+0x24": "TrackWidthFront",
            "+0x28": "TrackWidthRear",
            "+0x2C": "Front MaxDroop snapshot",
        },
        "index_to_signed_half_dimensions": {
            "0": {"axle": "front", "lateral_sign": -1, "longitudinal_sign": 1},
            "1": {"axle": "front", "lateral_sign": 1, "longitudinal_sign": 1},
            "2": {"axle": "rear", "lateral_sign": -1, "longitudinal_sign": -1},
            "3": {"axle": "rear", "lateral_sign": 1, "longitudinal_sign": -1},
        },
        "transform_inputs": "per-car dimensions plus per-wheel state feed render-instance transform construction",
        "xml_named_vehicle_alias": "UNRESOLVED; executable requests Vehicles/Car%d while extracted vehicles.xml uses named vehicle roots",
        "physics_equivalence": "NOT_ESTABLISHED",
    }


def build_report(corpora_root: Path) -> dict[str, Any]:
    corpora = _corpus_paths(corpora_root.resolve())
    missing = [f"{build}: {path}" for build, path in corpora.items() if not path.is_dir()]
    if missing:
        raise SystemExit("missing corpus roots: " + "; ".join(missing))
    matrix = {producer: dict(row) for producer, row in RAW_DX_COMPATIBILITY_MATRIX.items()}
    validate_compatibility_matrix(matrix)
    transfer_records = [dict(record) for record in TRANSFER_CLAIMS]
    transfer_validations = [validate_transfer_provenance(record) for record in transfer_records]
    comparisons = _comparisons(corpora)
    dx_root = _data_gx_root(corpora["9.10.0"], "9.10.0")
    vehicle_dx_root = _vehicle_root(corpora["9.10.0"], "9.10.0")
    return {
        "schema_version": 1,
        "scope": "Read-only R-BRIDGE2 corpus analysis. Parser acceptance is not runtime acceptance.",
        "builds": {build: str(root) for build, root in corpora.items()},
        "raw_dx_compatibility_matrix": matrix,
        "matrix_scope": {
            "8.4.1_to_retail": "static revision 127 gate on inspected model DX files",
            "9.3.1_to_retail": "static revision 131 gate on inspected model DX files",
            "9.10.0_to_retail": "human runtime confirmed for 9.10.0-cooker output used in reported vehicle transfers; sampled corpus files also pass retail header/parser checks",
            "retail_to_9.10.0": "human runtime confirmation for the resource sets reported; exact hashes not supplied",
            "unknown_cells": "not filled by inference",
        },
        "demo_9.10_dx_revisions": {
            "all_DataGx": _dx_revision_inventory(dx_root),
            "Vehicles_only": _dx_revision_inventory(vehicle_dx_root),
        },
        "assets": _asset_inventory(corpora),
        "cooker_bridge": {
            "status": "CONFIRMED_BY_HUMAN_RUNTIME",
            "pipeline": "older demo source/assets -> original demo 9.10.0 cooker -> generated DX/DXT -> retail existing slot",
            "source_build_and_generated_hashes": "UNKNOWN_FROM_USER_REPORT",
            "tested_vehicle_records": transfer_records,
        },
        "jump_wheel_adjacent_comparisons": comparisons["jump_wheel_adjacent_generations"],
        "jump_910_vs_retail": comparisons.get("jump_910_vs_retail", {}),
        "navara_910_vs_retail": comparisons["navara_910_vs_retail"],
        "complete_model_wheel_geometry": _wheel_geometry(corpora),
        "wheel_related_vehicle_config": _vehicle_config(corpora),
        "retail_static_wheel_trace": _static_wheel_trace(corpora),
        "human_runtime_transfer_records": transfer_records,
        "human_runtime_transfer_record_validation": transfer_validations,
        "limitations": [
            "Trooper and Rav4 transferred-file hashes and exact source corpus are absent from the user-supplied runtime note.",
            "Complete-model wheel centers are geometric measurements, not proven race hardpoints.",
            "GXM hierarchy type 3/version 1 remains unsupported; Navara complete.gxm wheel spans use its TXT sidecar.",
            "Retail EXE numeric Vehicles/Car%d properties are not directly mapped to the named Vehicles/<vehicle> XML roots in this corpus.",
            "The scan does not establish physical handling equivalence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    output_root = (repo_root / ".research-output").resolve()
    target = args.output.resolve()
    if output_root not in target.parents:
        raise SystemExit("output must be beneath this repository's ignored .research-output directory")
    report = build_report(args.corpora_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(target),
        "demo_9.10_all_dx_revisions": report["demo_9.10_dx_revisions"]["all_DataGx"]["revision_counts"],
        "demo_9.10_vehicle_dx_revisions": report["demo_9.10_dx_revisions"]["Vehicles_only"]["revision_counts"],
        "wheel_geometry_vehicle_count": len(report["complete_model_wheel_geometry"]),
        "comparison_groups": sorted(key for key, value in report.items() if "comparison" in key and value),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
