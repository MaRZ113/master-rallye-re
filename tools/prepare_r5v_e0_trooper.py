#!/usr/bin/env python3
"""Build a fail-closed local ID25/Trooper P0 package from retail and Demo 9.3.1."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import patch_vehicle_slot25 as slot25  # noqa: E402
from master_rallye.collision_writer import patch_dx_collision_translation, serialize_tag101  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt_bytes  # noqa: E402
from master_rallye.dx_revision_upgrade import upgrade_dx_131_to_135_with_report  # noqa: E402
from master_rallye.sidecar import normalize_texture_value  # noqa: E402
from master_rallye.vehicle_composition import resolve_effective_model_package  # noqa: E402
from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes  # noqa: E402
from master_rallye.vehicle_model_inventory import inventory_vehicle_model_packages  # noqa: E402
from master_rallye.vehicle_packaging import index_sma_members, read_sma_member  # noqa: E402
from master_rallye.vehicle_physics_binding import validate_vehicle_family_config  # noqa: E402


ARTIFACT_ROOT = ROOT / ".research-output" / "r5v_e0"
DEFAULT_OUTPUT = ARTIFACT_ROOT / "runtime-test"
RETAIL_EXE_SHA256 = slot25.SOURCE_SHA256
RUNTIME_TESTED_DX = {
    "car.dx": {
        "source_sha256": "8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1",
        "output_sha256": "04a9aa09b813a0893953e6813b2d8ec4ac63a5545b987e12a29e692773de06e1",
    },
    "complete.dx": {
        "source_sha256": "27b429e271fc7afb3b71f45bf14c197c779473b087227dbf468fd48ad97a911f",
        "output_sha256": "a8ceffebf7f6fc8b8af489e1e4c7f62ca5ef3b537db4af3f8048e687997629bc",
    },
    "wheel.dx": {
        "source_sha256": "9e7da7b3ea525fb5f29b61be763894ae98cd54fd0430c1b46b9f64d76e48d0ed",
        "output_sha256": "1a1aa4605e0319dd0d3fc68691845ed34559d1635c320986b23f9fe5750406ab",
    },
}


class CandidateError(ValueError):
    """A required source identity or validation gate did not match."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_output_path(path: Path) -> Path:
    requested = path.expanduser()
    absolute = Path(os.path.abspath(requested))
    cursor = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        cursor /= part
        if cursor.is_symlink():
            raise CandidateError(f"output path contains a symlink: {cursor}")
    output = absolute.resolve(strict=False)
    root = ARTIFACT_ROOT.resolve(strict=False)
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise CandidateError(f"output must stay under {root}") from exc
    if output == root or output.exists():
        raise CandidateError(f"output must be a new directory: {output}")
    return output


def _read_required_file(path: Path, label: str) -> bytes:
    requested = path.expanduser()
    if requested.is_symlink():
        raise CandidateError(f"{label} is a symlink: {requested}")
    source = requested.resolve(strict=True)
    if not source.is_file():
        raise CandidateError(f"{label} is not a regular source file: {source}")
    return source.read_bytes()


def _texture_dependencies(models: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for role, model in models.items():
        for draw in model.physical_draws:
            for slot in draw.texture_slots:
                if slot.value.strip().casefold() == "null":
                    continue
                relative = PurePosixPath(normalize_texture_value(slot.value) + ".dxt")
                if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
                    raise CandidateError(f"unsafe texture path in {role}: {slot.value!r}")
                key = relative.as_posix().casefold()
                result.setdefault(key, relative.as_posix())
    return result


def _validate_closed_geometry(geometry: Any) -> dict[str, Any]:
    edge_uses: Counter[tuple[int, int]] = Counter()
    minimum_area = math.inf
    finite = all(math.isfinite(component) for vertex in geometry.vertices for component in vertex)
    for a, b, c in geometry.triangles:
        for left, right in ((a, b), (b, c), (c, a)):
            edge_uses[tuple(sorted((left, right)))] += 1
        pa, pb, pc = (geometry.vertices[index] for index in (a, b, c))
        u = tuple(pb[index] - pa[index] for index in range(3))
        v = tuple(pc[index] - pa[index] for index in range(3))
        cross = (
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        )
        minimum_area = min(minimum_area, math.sqrt(sum(value * value for value in cross)) / 2)
    return {
        "vertex_count": len(geometry.vertices),
        "triangle_count": len(geometry.triangles),
        "finite_coordinates": finite,
        "finite_triangle_areas": math.isfinite(minimum_area),
        "closed_two_manifold": bool(edge_uses) and set(edge_uses.values()) == {2},
        "edge_use_counts": dict(sorted(Counter(edge_uses.values()).items())),
        "minimum_triangle_area": None if not geometry.triangles else minimum_area,
    }


def _validate_dx(role: str, source_data: bytes, output_data: bytes, report: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    expected = RUNTIME_TESTED_DX[role]
    source_hash = sha256(source_data)
    output_hash = sha256(output_data)
    if source_hash != expected["source_sha256"] or output_hash != expected["output_sha256"]:
        raise CandidateError(f"{role} conversion hashes differ from the runtime-tested R-COOKER1.1 pair")
    model = parse_dx_bytes(output_data, source=f"Trooper/{role}")
    if model.word_0x04 != 135 or not model.diagnostics.validated:
        raise CandidateError(f"{role} failed revision-135 parser/index validation")
    if model.diagnostics.errors or model.diagnostics.warnings:
        raise CandidateError(f"{role} has DX validation diagnostics")
    finite_positions = all(math.isfinite(x) for row in model.vertices.positions for x in row)
    finite_normals = all(math.isfinite(x) for row in model.vertices.normals for x in row)
    if not finite_positions or not finite_normals:
        raise CandidateError(f"{role} has non-finite positions or normals")
    preservation = {
        key: report.get(key)
        for key in (
            "geometry_preserved", "local_index_order_preserved", "collision_preserved",
            "global_index_table_preserved", "trailing_data_preserved",
        )
    }
    if any(value is not True for value in preservation.values()):
        raise CandidateError(f"{role} converter did not prove complete byte-structure preservation")
    return model, {
        "source_sha256": source_hash,
        "source_size": len(source_data),
        "source_revision": report.get("source_revision"),
        "converted_sha256": output_hash,
        "converted_size": len(output_data),
        "converted_revision": model.word_0x04,
        "vertex_count": model.vertex_count,
        "triangle_count": model.triangle_count,
        "draw_count": len(model.physical_draws),
        "texture_slot_reference_count": sum(len(draw.texture_slots) for draw in model.physical_draws),
        "diagnostics": {"errors": model.diagnostics.errors, "warnings": model.diagnostics.warnings},
        "preservation": preservation,
    }


def _validate_collision(car_model: Any, car_data: bytes) -> dict[str, Any]:
    sections = car_model.collision
    hull = sections.convex_hull
    if hull is None or sections.errors:
        raise CandidateError("Trooper car.dx does not have a valid tag101 collision hull")
    if not math.isfinite(hull.base_scalar) or hull.base_scalar <= 0:
        raise CandidateError("Trooper tag101 radius-like base scalar is not finite and positive")
    if serialize_tag101(hull) != hull.raw:
        raise CandidateError("Trooper tag101 serializer roundtrip changed source bytes")
    detailed = _validate_closed_geometry(hull.representation_b.geometry_a)
    if (not detailed["finite_coordinates"] or not detailed["finite_triangle_areas"]
            or not detailed["closed_two_manifold"]):
        raise CandidateError("Trooper detailed tag101 representation is not finite and closed")
    if not detailed["triangle_count"] or not detailed["minimum_triangle_area"] > 0:
        raise CandidateError("Trooper detailed tag101 representation has degenerate or empty faces")
    translated = patch_dx_collision_translation(
        car_data, (0.001, -0.002, 0.003), source="Trooper/car.dx collision validation"
    )
    if translated.translation.validation.get("status") != "PASS":
        raise CandidateError("Trooper tag101 rigid-translation invariants did not pass")
    return {
        "tag_ids": list(sections.tag_ids),
        "tag101_sha256": hull.sha256,
        "tag101_bytes": len(hull.raw),
        "base_scalar": hull.base_scalar,
        "serializer_roundtrip_byte_identical": True,
        "detailed_representation_b_geometry_a": detailed,
        "rigid_translation_invariant_validation": translated.translation.validation,
        "collision_errors": list(sections.errors),
        "test_translation_written": False,
    }


def _family_config_summary(document: Any, validation: Any) -> dict[str, Any]:
    fields = document.families.get("Trooper") or document.families.get("trooper")
    if fields is None:
        raise CandidateError("Retail vehicles.xml does not contain Vehicles/Trooper physics")
    values = {
        path: field["value"]
        for path, field in fields.items()
        if path in {
            "Dimensions/WheelBase", "Dimensions/TrackWidthFront", "Dimensions/TrackWidthRear",
            "Dimensions/WheelRadiusFront", "Dimensions/WheelRadiusRear",
            "Chassis/TotalMass", "Engine/Gears", "Engine/TorqueEntries",
        }
    }
    schema = validation.config_schema
    if schema.compatibility_class != "COMPATIBLE" or validation.player1_overlay_count != 13:
        raise CandidateError("Retail Trooper base schema or Player1 overlay is incomplete")
    return {
        "family": validation.family,
        "compatibility_class": schema.compatibility_class,
        "field_count": schema.total_fields,
        "fixed_required_fields": schema.fixed_fields_expected,
        "fixed_fields_present": schema.fixed_fields_present,
        "engine_gears": schema.gears_count,
        "engine_torque_entries": schema.torque_entries_count,
        "group_counts": schema.group_counts,
        "player1_modification_fields": validation.player1_overlay_count,
        "selected_values": values,
        "vehicles_xml_sha256": document.sha256,
    }


def prepare_candidate(
    retail_exe: Path,
    retail_data_sma: Path,
    demo_trooper_dir: Path,
    output_root: Path,
    texture_dir: Path | None = None,
) -> dict[str, Any]:
    output = _safe_output_path(output_root)
    exe_data = _read_required_file(retail_exe, "retail executable")
    exe_hash = sha256(exe_data)
    if exe_hash != RETAIL_EXE_SHA256:
        raise CandidateError(f"unsupported retail executable SHA256: {exe_hash}")
    requested_archive = retail_data_sma.expanduser()
    if requested_archive.is_symlink():
        raise CandidateError(f"retail Data.sma is a symlink: {requested_archive}")
    archive_path = requested_archive.resolve(strict=True)
    if not archive_path.is_file():
        raise CandidateError(f"retail Data.sma is not a regular source file: {archive_path}")
    archive_hash = sha256(archive_path.read_bytes())
    members = index_sma_members(archive_path)
    requested_demo_root = demo_trooper_dir.expanduser()
    if requested_demo_root.is_symlink():
        raise CandidateError(f"Demo 9.3.1 Trooper source is a symlink: {requested_demo_root}")
    demo_root = requested_demo_root.resolve(strict=True)
    if not demo_root.is_dir():
        raise CandidateError(f"Demo 9.3.1 Trooper source is not a regular directory: {demo_root}")
    requested_texture_root = texture_dir.expanduser() if texture_dir is not None else requested_demo_root
    if requested_texture_root.is_symlink():
        raise CandidateError(f"Demo 9.3.1 Trooper texture source is a symlink: {requested_texture_root}")
    texture_root = requested_texture_root.resolve(strict=True)
    if not texture_root.is_dir():
        raise CandidateError(f"Demo 9.3.1 Trooper texture source is not a regular directory: {texture_root}")

    vehicle_xml = read_sma_member(archive_path, "DataGame/vehicles.xml")
    modifications_xml = read_sma_member(archive_path, "DataGame/Modifications.xml")
    vehicle_config = parse_vehicle_config_bytes(
        vehicle_xml, build="retail", source="retail Data.sma:DataGame/vehicles.xml"
    )
    modifications_config = parse_vehicle_config_bytes(
        modifications_xml, build="retail", source="retail Data.sma:DataGame/Modifications.xml"
    )
    physics_validation = validate_vehicle_family_config(
        "Trooper", vehicle_config, modifications_config
    )
    physics_report = _family_config_summary(vehicle_config, physics_validation)
    physics_report["modifications_xml_sha256"] = modifications_config.sha256

    converted: dict[str, bytes] = {}
    conversion_reports: dict[str, dict[str, Any]] = {}
    parsed_models: dict[str, Any] = {}
    for role in RUNTIME_TESTED_DX:
        source_path = demo_root / role
        source_data = _read_required_file(source_path, f"Demo 9.3.1 Trooper {role}")
        converted_data, conversion = upgrade_dx_131_to_135_with_report(source_data, role)
        model, report = _validate_dx(role, source_data, converted_data, conversion)
        converted[role] = converted_data
        parsed_models[role] = model
        conversion_reports[role] = report

    texture_names = _texture_dependencies(parsed_models)
    source_textures: dict[str, Path] = {}
    for path in texture_root.rglob("*.dxt"):
        if path.is_symlink() or not path.is_file():
            raise CandidateError(f"unsafe Demo 9.3.1 texture source: {path}")
        relative = path.relative_to(texture_root).as_posix()
        key = relative.casefold()
        if key in source_textures:
            raise CandidateError(f"case-colliding Demo 9.3.1 DXT source: {relative}")
        source_textures[key] = path
    missing_textures = sorted(name for name in texture_names if name not in source_textures)
    if missing_textures:
        raise CandidateError("missing Trooper DXT dependencies: " + ", ".join(missing_textures))
    texture_manifest: dict[str, dict[str, Any]] = {}
    texture_bytes: dict[str, bytes] = {}
    for key, relative in sorted(texture_names.items()):
        path = source_textures[key]
        raw = _read_required_file(path, f"Trooper DXT {relative}")
        texture = parse_dxt_bytes(raw, source=f"demo-9.3.1/Trooper/{relative}")
        texture_bytes[relative] = raw
        texture_manifest[relative] = {
            "source_sha256": sha256(raw),
            "size": len(raw),
            "width": getattr(texture, "width", None),
            "height": getattr(texture, "height", None),
        }

    collision_report = _validate_collision(parsed_models["car.dx"], converted["car.dx"])

    candidate_exe, patch_manifest = slot25.make_candidate(
        exe_data, profile=slot25.TROOPER_PROFILE
    )
    if patch_manifest["record25"]["name"] != "Trooper" or patch_manifest["record25"]["id"] != 25:
        raise CandidateError("slot25 patch profile did not produce Trooper ID25")

    with tempfile.TemporaryDirectory(prefix="r5v_e0_source_", dir=ARTIFACT_ROOT.parent) as scratch:
        scratch_vehicles = Path(scratch) / "DataGx" / "Vehicles"
        scratch_trooper = scratch_vehicles / "Trooper"
        scratch_trooper.mkdir(parents=True)
        for name, raw in converted.items():
            (scratch_trooper / name).write_bytes(raw)
        for relative, raw in texture_bytes.items():
            destination = scratch_trooper.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        packages = inventory_vehicle_model_packages(members, scratch_vehicles)
        package = packages.get("trooper")
        if package is None or package.get("provenance") != "LOOSE_OVERRIDE":
            raise CandidateError("Trooper package source is not isolated as a loose-only model donor")
        effective = resolve_effective_model_package(
            archive_path, members, scratch_vehicles, "Trooper",
            model_packages=packages, require_complete=True,
        )
        effective_files = effective["files"]
        for core in ("car.dx", "complete.dx", "wheel.dx"):
            item = effective_files.get(core.casefold())
            if item is None or item["source_provenance"] != "LOOSE_OVERRIDE":
                raise CandidateError(f"effective Trooper package does not use the staged {core}")
        unresolved = effective.get("unresolved_texture_dependencies", [])
        if unresolved:
            raise CandidateError("composer found unresolved Trooper texture references")
        output_manifest_files = {
            item["relative_path"]: {
                "sha256": item["sha256"],
                "size": len(item["data"]),
                "source_provenance": item["source_provenance"],
            }
            for item in effective_files.values()
        }

    output.mkdir(parents=True)
    try:
        (output / "MRallye_slot25_trooper_test.exe").write_bytes(candidate_exe)
        (output / "patch-manifest.json").write_text(
            json.dumps(patch_manifest, indent=2) + "\n", encoding="utf-8"
        )
        overlay = output / "DataGx" / "Vehicles" / "Trooper"
        for relative, item in effective_files.items():
            destination = overlay.joinpath(*PurePosixPath(item["relative_path"]).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(item["data"])

        data_manifest = {
            "phase": "R5V-E0",
            "runtime_validation": "WAITING FOR HUMAN P0",
            "slot_profile": patch_manifest["record25"],
            "source_builds": {
                "retail": {
                    "executable_sha256": exe_hash,
                    "data_sma_sha256": archive_hash,
                    "vehicle_config": physics_report,
                },
                "model": {
                    "build": "demo-9.3.1",
                    "internal_name": "Trooper",
                    "dx_source_dir": str(demo_root),
                    "texture_source_dir": str(texture_root),
                    "conversion": "retail-proven DX revision 131 -> 135 converter",
                    "resources": conversion_reports,
                },
            },
            "collision": collision_report,
            "textures": {
                "required_dependency_count": len(texture_manifest),
                "dependencies": texture_manifest,
                "unused_source_dxt_count": len(source_textures) - len(texture_manifest),
                "source_dir": str(texture_root),
                "conversion": "none; copied unchanged from demo-9.3.1",
            },
            "composition_resolver": {
                "module": "master_rallye.vehicle_composition.resolve_effective_model_package",
                "physics_family": "Trooper",
                "model_donor": "Trooper",
                "status": effective["status"],
                "provenance": effective["provenance"],
                "file_count": effective["file_count"],
                "unresolved_texture_dependencies": effective["unresolved_texture_dependencies"],
                "overlay_relative_root": "DataGx/Vehicles/Trooper",
                "files": output_manifest_files,
            },
            "p0": {
                "goal": "ID25 loads Trooper complete.dx and all referenced DXT in frontend preview",
                "race_allowed": False,
                "display_name_expected": "STEEL MONKEYS FORKLIFT",
                "stats_and_floats_source": "Astero ID16 cosmetic donor",
            },
        }
        (output / "data-manifest.json").write_text(
            json.dumps(data_manifest, indent=2) + "\n", encoding="utf-8"
        )
        (output / "TEST_INSTRUCTIONS.txt").write_text(
            _test_instructions(output), encoding="utf-8"
        )
    except Exception:
        shutil.rmtree(output)
        raise

    return {
        "output": str(output),
        "candidate_exe_sha256": sha256(candidate_exe),
        "patch_manifest": str(output / "patch-manifest.json"),
        "data_manifest": str(output / "data-manifest.json"),
        "overlay_directory": str(output / "DataGx" / "Vehicles" / "Trooper"),
        "overlay_file_count": len(output_manifest_files),
        "texture_dependency_count": len(texture_manifest),
        "physics_schema": physics_report["compatibility_class"],
        "collision": "PASS",
        "runtime_validation": "WAITING FOR HUMAN P0",
    }


def _test_instructions(output: Path) -> str:
    return f"""R5V-E0 TROOPER — P0 MENU / PREVIEW ONLY

Candidate executable SHA-256: {sha256((output / 'MRallye_slot25_trooper_test.exe').read_bytes()) if (output / 'MRallye_slot25_trooper_test.exe').exists() else '(written during preparation)'}

1. Close the game. Keep the original retail MRallye.exe and Data.sma intact.
2. Copy MRallye_slot25_trooper_test.exe from this package into the retail game
   directory under the same distinct filename. Launch that copy from the game
   directory so it sees the retail Data.sma and DataGame files.
3. Copy this package's DataGx\\Vehicles\\Trooper folder to the matching loose
   path beside the retail archive. Loose files override matching archive files;
   this filewise precedence was runtime-tested by the beta Vehicle Composer.
4. Open T3 vehicle selection and navigate to the existing twelfth position.
   The legacy ID25 display name may still say STEEL MONKEYS FORKLIFT; the
   preview model and textures should be Trooper. Check stats and move away/back
   repeatedly, leave and re-enter the selector, then exit normally.
5. Do NOT start a race. Capture retail debug output around
   `vehicles\\trooper\\complete.dx` and referenced DXT loads.
6. After testing, close the game and remove only the distinct test executable
   and the newly added `DataGx\\Vehicles\\Trooper` loose folder.

Report P0 FULL PASS, COSMETIC PARTIAL PASS, or FAIL. P1 race testing starts only
after the owner reports P0 FULL PASS or COSMETIC PARTIAL PASS.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retail-exe", type=Path, required=True)
    parser.add_argument("--retail-data-sma", type=Path, required=True)
    parser.add_argument("--demo-trooper-dir", type=Path, required=True,
                        help="Exact Trooper DX input folder (revision 131)")
    parser.add_argument("--texture-dir", type=Path,
                        help="Trooper DXT source folder; defaults to --demo-trooper-dir")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = prepare_candidate(args.retail_exe, args.retail_data_sma,
                                   args.demo_trooper_dir, args.output,
                                   texture_dir=args.texture_dir)
    except Exception as exc:
        parser.exit(2, f"R5V-E0 candidate refused ({type(exc).__name__}): {exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
