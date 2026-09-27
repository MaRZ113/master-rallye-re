#!/usr/bin/env python3
"""Master Rallye Vehicle Composer command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.errors import FormatError  # noqa: E402
from master_rallye.vehicle_family_binder import (  # noqa: E402
    USER_FACING_NAME,
    load_install_inventory,
    run_interactive_wizard,
    run_restore_menu,
    run_status_view,
)
from master_rallye.vehicle_config_analysis import parse_vehicle_config  # noqa: E402
from master_rallye.vehicle_composition import (  # noqa: E402
    VehicleComposition,
    apply_vehicle_composition,
    build_vehicle_composition_plan,
    choose_composition_manifest_path,
    choose_composition_output_exe,
    discover_vehicle_composition_manifests,
    restore_vehicle_composition,
)
from master_rallye.vehicle_physics_binding import (  # noqa: E402
    RETAIL_BUILD_NAME,
    apply_binding_copy,
    load_binding_config,
    restore_binding_copy,
    validate_binding_request,
)


def _find_config(install_root: Path, filename: str) -> Path:
    candidates = (
        install_root / "DataGame" / filename,
        install_root / "Data.sma_unpacked" / "DataGame" / filename,
        install_root / "corpora" / "retail" / "Data.sma_unpacked" / "DataGame" / filename,
    )
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def _add_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--install-root", type=Path, required=True,
                        help="retail game directory containing MRallye.exe")
    parser.add_argument("--config", type=Path, required=True,
                        help="schema-v1 family binding or schema-v2 vehicle composition JSON")
    parser.add_argument("--vehicles-xml", type=Path,
                        help="default: <install-root>/DataGame/vehicles.xml")
    parser.add_argument("--modifications-xml", type=Path,
                        help="default: <install-root>/DataGame/Modifications.xml")
    parser.add_argument(
        "--allow-unverified-schema",
        action="store_true",
        help="explicitly permit an unexplained schema variant (experimental only)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python tools/physics_bind.py",
        description=(
            f"{USER_FACING_NAME}. With no subcommand, compose a retail carrier, "
            "physics family, and model donor interactively. Explicit "
            "validate/apply/restore commands remain available for scripts and "
            "research reproduction."
        ),
    )
    parser.add_argument("--install-root", dest="wizard_install_root", type=Path,
                        help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true",
                        help="preview the interactive vehicle composition without writing files")
    commands = parser.add_subparsers(dest="command")

    validate = commands.add_parser("validate", help="read-only binding validation")
    _add_inputs(validate)
    validate.add_argument(
        "--text", action="store_true",
        help="print a concise semantic schema summary instead of the default JSON",
    )

    apply = commands.add_parser("apply", help="apply a legacy family binding or vehicle composition")
    _add_inputs(apply)
    apply.add_argument("--output-exe", type=Path,
                       help="optional new executable path; omitted for carrier==physics or auto-named")

    restore = commands.add_parser("restore", help="restore a copy or open the restore menu")
    restore.add_argument("--output-exe", type=Path,
                         help="explicit tool-owned executable copy to restore")
    restore.add_argument("--manifest", type=Path,
                         help="explicit R-VEH1 vehicle-composition manifest to restore")
    restore.add_argument("--install-root", type=Path,
                         help="root used to discover known manifests when no --output-exe is given")

    status = commands.add_parser("status", help="show bindings, model resources, and manifests")
    status.add_argument("--install-root", type=Path,
                        help="game root; auto-detected from the current directory when omitted")
    return parser


def _config_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    vehicles = args.vehicles_xml or _find_config(args.install_root, "vehicles.xml")
    modifications = args.modifications_xml or _find_config(args.install_root, "Modifications.xml")
    return vehicles, modifications


def _print_validation_summary(report: dict) -> None:
    print(f"Validation: {report['status']}")
    for binding in report["bindings"]:
        schema = binding["config_schema"]
        print(f"\nFamily: {binding['physics_family']}")
        print(f"  Model donor: {binding.get('model_donor', binding['physics_family'])}")
        print(f"  Runtime family: {binding.get('runtime_family', binding['physics_family'])}")
        print(f"  Schema: {schema['compatibility_class']}")
        print(
            f"  Fixed fields: {schema['fixed_fields_present']}/"
            f"{schema['fixed_fields_expected']}"
        )
        print("  Engine dynamic schema:")
        print(f"    Gears = {schema['gears_count']}")
        for name, label in (
            ("Gear", "Gear entries"),
            ("ChangeUpRevs", "ChangeUpRevs"),
            ("ChangeDownRevs", "ChangeDownRevs"),
        ):
            present = schema["gear_fields_present"].get(name, 0)
            expected = schema["gear_fields_expected"]
            expected_text = str(expected) if expected is not None else "unknown"
            print(f"    {label}: {present}/{expected_text}")
        print(f"    TorqueEntries = {schema['torque_entries_count']}")
        expected = schema["torque_fields_expected"]
        expected_text = str(expected) if expected is not None else "unknown"
        print(f"    Torque entries: {schema['torque_fields_present']}/{expected_text}")
        print(f"  Total fields: {schema['total_fields']}")
        print(f"  Player1 fields: {binding['player1_overlay_fields']}")
        if binding["schema_override_used"]:
            print("  WARNING: unverified-schema experimental override was used")
        for label, paths in (
            ("Missing", schema["missing_paths"]),
            ("Unexpected", schema["unexpected_paths"]),
        ):
            if paths:
                print(f"  {label}: " + ", ".join(paths))
        if schema["type_mismatches"]:
            print("  Type mismatches:")
            for path, expected_type, actual_type in schema["type_mismatches"]:
                print(f"    {path}: expected {expected_type}, got {actual_type}")
        if schema["count_errors"]:
            print("  Count errors: " + "; ".join(schema["count_errors"]))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command is None:
            return run_interactive_wizard(args.wizard_install_root, dry_run=args.dry_run)
        if args.command == "status":
            return run_status_view(args.install_root)
        if args.command == "restore":
            if args.manifest is not None:
                result = restore_vehicle_composition(
                    args.manifest, install_root=args.install_root
                )
            elif args.output_exe is None:
                return run_restore_menu(args.install_root)
            else:
                root = args.install_root or args.output_exe.expanduser().resolve().parent
                composition = next((
                    item for item in discover_vehicle_composition_manifests(root)
                    if item.get("output_exe") is not None
                    and item["output_exe"].resolve() == args.output_exe.expanduser().resolve()
                ), None)
                if composition is not None:
                    result = restore_vehicle_composition(
                        composition["manifest"], install_root=root
                    )
                else:
                    result = restore_binding_copy(args.output_exe)
        else:
            source_exe = args.install_root / "MRallye.exe"
            vehicles_xml, modifications_xml = _config_paths(args)
            bindings = load_binding_config(args.config)
            use_composer = (
                any(binding.model_donor is not None for binding in bindings)
                or (len(bindings) == 1 and any(
                    binding.carrier_type.casefold() == binding.physics_family.casefold()
                    for binding in bindings
                ))
            )
            if use_composer:
                inventory = load_install_inventory(args.install_root)
                vehicle_config = (
                    parse_vehicle_config(vehicles_xml, build=RETAIL_BUILD_NAME)
                    if vehicles_xml.is_file() else inventory.vehicle_config
                )
                modifications_config = (
                    parse_vehicle_config(modifications_xml, build=RETAIL_BUILD_NAME)
                    if modifications_xml.is_file() else inventory.modifications_config
                )
                if len(bindings) != 1:
                    raise ValueError(
                        "schema-v2 composition apply currently accepts one carrier per transaction; "
                        "legacy schema-v1 batches remain supported"
                    )
                binding = bindings[0]
                composition = VehicleComposition(
                    binding.carrier_type,
                    binding.physics_family,
                    binding.effective_model_donor,
                )
                output_exe = choose_composition_output_exe(
                    args.install_root, composition, output_exe=getattr(args, "output_exe", None)
                    if args.command == "apply" else None
                )
                plan = build_vehicle_composition_plan(
                    source_exe,
                    args.install_root,
                    composition,
                    vehicle_config,
                    modifications_config,
                    inventory.data_sma,
                    inventory.archive_members,
                    args.install_root / "DataGx" / "Vehicles",
                    model_packages=inventory.model_packages,
                    allow_unverified_schema=args.allow_unverified_schema,
                    output_exe=output_exe,
                )
                manifest_path = choose_composition_manifest_path(
                    args.install_root, composition, output_exe=output_exe
                )
                result = {
                    "status": "VALID",
                    "mode": "DRY_RUN_NO_FILES_WRITTEN",
                    **plan.preview(),
                    "manifest": str(manifest_path),
                    "source_executable_modified": False,
                }
                if args.command == "apply":
                    result = apply_vehicle_composition(plan, manifest_path=manifest_path)
            elif args.command == "validate":
                result = validate_binding_request(
                    source_exe,
                    bindings,
                    vehicles_xml,
                    modifications_xml,
                    allow_unverified_schema=args.allow_unverified_schema,
                )
                if args.text:
                    _print_validation_summary(result)
                    return 0
            else:
                output_path = args.output_exe
                if output_path is None:
                    from master_rallye.vehicle_family_binder import _default_output_name  # noqa: E402
                    output_path = args.install_root / _default_output_name(
                        bindings[0].carrier_type, bindings[0].physics_family
                    )
                result = apply_binding_copy(
                    source_exe,
                    output_path,
                    bindings,
                    vehicles_xml,
                    modifications_xml,
                    allow_unverified_schema=args.allow_unverified_schema,
                )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (FormatError, OSError, ValueError) as exc:
        print(f"{USER_FACING_NAME}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
