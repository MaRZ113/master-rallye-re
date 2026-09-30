"""Interactive console workflow for the validated vehicle-family binder."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from .vehicle_config_analysis import VehicleConfigDocument, parse_vehicle_config_bytes
from .errors import FormatError
from .vehicle_family_broker import RETAIL_EXE_SHA256, named_vehicle_path
from .vehicle_model_inventory import (
    MODEL_RESOURCES,
    available_model_donors,
    build_vehicle_family_inventory,
    inventory_vehicle_model_packages,
    select_family_row,
    select_model_donor,
    select_retail_carrier,
)
from .vehicle_packaging import index_sma_members, read_sma_member
from .vehicle_physics_binding import (
    RETAIL_BUILD_NAME,
    RETAIL_FAMILY_CATALOG,
    PhysicsBinding,
    apply_binding_copy,
    restore_binding_copy,
    validate_vehicle_family_config,
    validate_binding_request,
)
from .vehicle_composition import (
    MANIFEST_SUFFIX as COMPOSITION_MANIFEST_SUFFIX,
    OVERRIDE_INCOMPLETE_MODEL,
    OVERRIDE_MISSING_MODEL,
    VehicleComposition,
    apply_vehicle_composition,
    build_vehicle_composition_plan,
    choose_composition_manifest_path,
    choose_composition_output_exe,
    discover_vehicle_composition_manifests,
    restore_vehicle_composition,
)


USER_FACING_NAME = "Master Rallye Vehicle Composer"
MISSING_MODEL_OVERRIDE = OVERRIDE_MISSING_MODEL
UNVERIFIED_SCHEMA_OVERRIDE = "ALLOW UNVERIFIED SCHEMA"
MANIFEST_SUFFIX = ".physics-bind.json"


@dataclass(frozen=True)
class InstallInventory:
    root: Path
    executable: Path
    executable_sha256: str
    data_sma: Path | None
    archive_members: tuple[str, ...]
    vehicles_xml_bytes: bytes
    modifications_xml_bytes: bytes
    vehicle_config: VehicleConfigDocument
    modifications_config: VehicleConfigDocument
    model_packages: dict[str, dict[str, Any]]
    families: list[dict[str, Any]]
    config_sources: dict[str, str]


def detect_install_root(start: Path | None = None) -> Path | None:
    """Find the nearest ancestor containing the retail executable."""
    current = Path(start or Path.cwd()).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "MRallye.exe").is_file():
            return candidate
    return None


def _normalize_path_input(value: str) -> Path:
    trimmed = value.strip().strip('"').strip("'")
    if not trimmed:
        raise ValueError("install root is required")
    return Path(trimmed).expanduser().resolve()


def choose_install_root(
    supplied: Path | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], Any] = print,
) -> Path:
    """Use an explicit root, auto-detect, or ask once for a pasted path."""
    root = Path(supplied).expanduser().resolve() if supplied is not None else detect_install_root()
    if root is None:
        output_fn("Master Rallye install root was not detected.")
        root = _normalize_path_input(input_fn("Install root: "))
    if not root.is_dir():
        raise ValueError(f"install root does not exist: {root}")
    executable = root / "MRallye.exe"
    if not executable.is_file():
        raise ValueError(f"retail executable was not found: {executable}")
    return root


def _read_config_payload(
    root: Path,
    archive: Path | None,
    archive_members: tuple[str, ...],
    filename: str,
) -> tuple[bytes, str]:
    loose = root / "DataGame" / filename
    if loose.is_file():
        return loose.read_bytes(), str(loose)
    member = f"DataGame/{filename}"
    if archive is not None:
        if not any(name.casefold() == member.casefold() for name in archive_members):
            raise ValueError(f"{member} is absent from {archive}")
        return read_sma_member(archive, member), f"{archive}!{member}"
    unpacked = root / "Data.sma_unpacked" / "DataGame" / filename
    if unpacked.is_file():
        return unpacked.read_bytes(), str(unpacked)
    raise ValueError(
        f"cannot find {filename}: expected loose {loose}, Data.sma member {member}, "
        "or Data.sma_unpacked fallback"
    )


def load_install_inventory(root: Path) -> InstallInventory:
    """Verify the exact retail build and inventory configs/models read-only."""
    root = Path(root).expanduser().resolve()
    executable = root / "MRallye.exe"
    try:
        executable_bytes = executable.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read retail executable {executable}: {exc}") from exc
    executable_sha = hashlib.sha256(executable_bytes).hexdigest()
    if executable_sha != RETAIL_EXE_SHA256:
        raise ValueError(
            f"unsupported retail executable SHA-256 {executable_sha}; "
            f"expected {RETAIL_EXE_SHA256}"
        )

    data_sma = root / "Data.sma"
    if data_sma.is_file():
        archive_members = index_sma_members(data_sma)
        archive: Path | None = data_sma
    else:
        archive_members = ()
        archive = None

    vehicles_bytes, vehicles_source = _read_config_payload(
        root, archive, archive_members, "vehicles.xml"
    )
    modifications_bytes, modifications_source = _read_config_payload(
        root, archive, archive_members, "Modifications.xml"
    )
    vehicle_config = parse_vehicle_config_bytes(
        vehicles_bytes, build=RETAIL_BUILD_NAME, source=vehicles_source
    )
    modifications_config = parse_vehicle_config_bytes(
        modifications_bytes, build=RETAIL_BUILD_NAME, source=modifications_source
    )
    model_packages = inventory_vehicle_model_packages(
        archive_members, root / "DataGx" / "Vehicles"
    )
    families = build_vehicle_family_inventory(
        vehicle_config, modifications_config, model_packages
    )
    return InstallInventory(
        root=root,
        executable=executable,
        executable_sha256=executable_sha,
        data_sma=data_sma if archive is not None else None,
        archive_members=archive_members,
        vehicles_xml_bytes=vehicles_bytes,
        modifications_xml_bytes=modifications_bytes,
        vehicle_config=vehicle_config,
        modifications_config=modifications_config,
        model_packages=model_packages,
        families=families,
        config_sources={"vehicles.xml": vehicles_source, "Modifications.xml": modifications_source},
    )


@contextmanager
def _materialized_config_paths(inventory: InstallInventory) -> Iterator[tuple[Path, Path]]:
    """Give the existing path-based backend exact temporary copies of XML inputs."""
    with tempfile.TemporaryDirectory(prefix="mr-family-binder-") as temporary:
        directory = Path(temporary)
        vehicles = directory / "vehicles.xml"
        modifications = directory / "Modifications.xml"
        vehicles.write_bytes(inventory.vehicles_xml_bytes)
        modifications.write_bytes(inventory.modifications_xml_bytes)
        yield vehicles, modifications


def _model_provenance_label(model: dict[str, Any]) -> str:
    return {
        "DATA_SMA": "Data.sma",
        "LOOSE_OVERRIDE": "loose override",
        "LOOSE": "loose package",
        "DATA_SMA+LOOSE": "Data.sma + loose overrides",
        "MISSING": "missing",
    }.get(model["provenance"], model["provenance"])


def _family_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        " #  Family               Config              Fields  Gears  Torque  Player1    Model / source",
        " -- -------------------- ------------------ ------ ------ ------- ---------- ----------------------------",
    ]
    for index, row in enumerate(rows, 1):
        base = row["base_config"]
        overlay = row["player1_modifications"]
        model = row["model"]
        schema = base.get("schema_audit") or {}
        gears = schema.get("gears_count")
        torque = schema.get("torque_entries_count")
        base_label = base["status"]
        field_label = str(base["field_count"]) if base["field_count"] else "-"
        gears_label = str(gears) if gears is not None else "-"
        torque_label = str(torque) if torque is not None else "-"
        overlay_label = (
            f"{overlay['status']} {overlay['field_count']}/{overlay['expected_field_count']}"
        )
        model_label = f"{model['status']} / {_model_provenance_label(model)}"
        lines.append(
            f" {index:>2}  {row['family']:<20.20} {base_label:<18.18} "
            f"{field_label:>6} {gears_label:>6} {torque_label:>7} "
            f"{overlay_label:<10.10} {model_label}"
        )
    return lines


def _ask_selection(
    prompt: str,
    resolver: Callable[[str], Any],
    *,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], Any],
) -> Any:
    while True:
        value = input_fn(prompt)
        try:
            return resolver(value)
        except ValueError as exc:
            output_fn(f"Invalid selection: {exc}")


def _ask_yes_no(
    prompt: str,
    *,
    default: bool,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], Any],
) -> bool:
    while True:
        value = input_fn(prompt).strip().casefold()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        output_fn("Enter Y or N.")


def _default_output_name(carrier: str, family: str) -> str:
    def safe_component(value: str) -> str:
        result = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
        if not result:
            raise ValueError("vehicle family cannot produce a safe output filename")
        return result

    if carrier.casefold() == family.casefold():
        return f"MRallye_{safe_component(family)}.exe"
    return f"MRallye_{safe_component(carrier)}-to-{safe_component(family)}.exe"


def _choose_output_path(root: Path, carrier: str, family: str) -> Path:
    base = _default_output_name(carrier, family)
    candidate = root / base
    binding_row = {"carrier_type": carrier, "physics_family": family}
    for item in discover_binding_manifests(root):
        if (
            item["output_exe"] == candidate
            and item["valid"]
            and item["status"] in {"applied", "restored"}
            and item["bindings"] == [binding_row]
        ):
            return candidate
    suffix = Path(base).suffix
    stem = Path(base).stem
    number = 2
    while candidate.exists() or candidate.with_name(candidate.name + ".original").exists() \
            or candidate.with_name(candidate.name + MANIFEST_SUFFIX).exists():
        candidate = root / f"{stem}-{number}{suffix}"
        number += 1
    return candidate


def _validate_selected_family(
    inventory: InstallInventory,
    family: str,
    *,
    allow_unverified_schema: bool = False,
) -> Any:
    """Call the same semantic schema and overlay validator used by apply."""
    named_vehicle_path(family)
    return validate_vehicle_family_config(
        family,
        inventory.vehicle_config,
        inventory.modifications_config,
        allow_unverified_schema=allow_unverified_schema,
    )


def _show_schema_detail(
    family_row: dict[str, Any], output_fn: Callable[[str], Any]
) -> None:
    base = family_row["base_config"]
    audit = base.get("schema_audit")
    output_fn("")
    output_fn(f"Config detail: {family_row['family']}")
    output_fn(f"  Schema:       {base['status']}")
    if audit is None:
        output_fn("  No base vehicle config fields are present.")
        return
    output_fn(
        f"  Fixed fields: {audit['fixed_fields_present']}/"
        f"{audit['fixed_fields_expected']} ({'OK' if audit['fixed_schema_ok'] else 'check required'})"
    )
    output_fn(f"  Total fields: {audit['total_fields']}")
    output_fn("  Engine:")
    gear_total = audit["gear_fields_expected"]
    gear_total_text = str(gear_total) if gear_total is not None else "unknown"
    for name, label in (
        ("Gear", "Gear entries"),
        ("ChangeUpRevs", "ChangeUpRevs"),
        ("ChangeDownRevs", "ChangeDownRevs"),
    ):
        present = audit["gear_fields_present"].get(name, 0)
        output_fn(f"    {label}: {present}/{gear_total_text}")
    torque_total = audit["torque_fields_expected"]
    torque_total_text = str(torque_total) if torque_total is not None else "unknown"
    output_fn(f"    Gears = {audit['gears_count']}")
    output_fn(f"    TorqueEntries = {audit['torque_entries_count']}")
    output_fn(
        f"    Torque entries: {audit['torque_fields_present']}/{torque_total_text}"
    )
    if audit["missing_paths"]:
        output_fn("  Missing required paths: " + ", ".join(audit["missing_paths"]))
    if audit["unexpected_paths"]:
        output_fn("  Unexplained paths: " + ", ".join(audit["unexpected_paths"]))
    if audit["type_mismatches"]:
        output_fn("  Type mismatches: " + "; ".join(
            f"{path} expected {expected}, got {actual}"
            for path, expected, actual in audit["type_mismatches"]
        ))
    if audit["count_errors"]:
        output_fn("  Count errors: " + "; ".join(audit["count_errors"]))


def _show_family_preview(
    inventory: InstallInventory,
    family_row: dict[str, Any],
    carrier: Any,
    output_path: Path,
    output_fn: Callable[[str], Any],
) -> None:
    model = family_row["model"]
    base = family_row["base_config"]
    overlay = family_row["player1_modifications"]
    resource_lines = []
    for resource in ("car.dx", "complete.dx", "wheel.dx"):
        source = model["resources"][resource]["source"]
        if resource == "wheel.dx" and model.get("wheelless_by_design") and source == "MISSING":
            source = "EXPECTED ABSENT (Ufo design)"
        resource_lines.append(f"    {resource}: {source}")
    output_fn("")
    output_fn("Binding preview")
    output_fn(f"  Carrier:        type {carrier.type_id} / {carrier.family}")
    output_fn(f"  Physics family: {family_row['family']}")
    output_fn(f"  Runtime family: {family_row['family']}")
    output_fn(f"  Model donor:    {family_row['family']} (same as runtime family)")
    output_fn(f"  Runtime model path: DataGx\\Vehicles\\{family_row['family']}")
    output_fn(f"  Model donor package: {_model_provenance_label(model)} ({model['status']})")
    output_fn(f"  Physics config: Vehicles/{family_row['family']} - {base['status']}")
    output_fn(
        f"  Modifications:  {family_row['family']}/Player1 - {overlay['status']}"
    )
    output_fn("  Model resources:")
    for line in resource_lines:
        output_fn(line)
    output_fn(f"  Effective map:  {carrier.family} -> {family_row['family']}")
    output_fn(f"  Output copy:    {output_path}")
    output_fn(
        "  Runtime effect: this persistent family binding changes both model/resource "
        "lookup and vehicle configuration/physics lookup."
    )
    output_fn(f"  Retail EXE:     {inventory.executable_sha256} (verified)")


def _show_model_donor_table(
    inventory: InstallInventory, output_fn: Callable[[str], Any]
) -> None:
    output_fn("Available model donors (physics config is not required):")
    for index, row in enumerate(available_model_donors(inventory.model_packages), 1):
        model = row["model"]
        resources = ", ".join(
            f"{name}={model['resources'][name]['source']}"
            for name in MODEL_RESOURCES
        )
        if model.get("wheelless_by_design") and model["resources"]["wheel.dx"]["source"] == "MISSING":
            resources = resources.replace("wheel.dx=MISSING", "wheel.dx=EXPECTED ABSENT")
        output_fn(
            f"  [{index:>2}] {row['family']:<18.18} {model['status']:<26.26} "
            f"{_model_provenance_label(model)} | {resources}"
        )


def _choose_model_donor(
    inventory: InstallInventory,
    carrier: Any,
    physics_family: str,
    *,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], Any],
) -> tuple[str, bool, bool]:
    while True:
        output_fn("")
        output_fn("Model donor:")
        output_fn(f"  [1] Use physics-family model ({physics_family})")
        output_fn(f"  [2] Keep carrier model ({carrier.family})")
        output_fn("  [3] Choose another model donor")
        choice = input_fn("Select model donor [1-3]: ").strip()
        if choice == "1":
            donor = physics_family
            break
        if choice == "2":
            donor = carrier.family
            break
        if choice == "3":
            _show_model_donor_table(inventory, output_fn)
            donor = _ask_selection(
                "Model donor number or name: ",
                lambda value: select_model_donor(inventory.model_packages, value)["family"],
                input_fn=input_fn,
                output_fn=output_fn,
            )
            break
        output_fn("Enter 1, 2, or 3.")

    model = inventory.model_packages.get(donor.casefold())
    if model is None or model.get("provenance") == "MISSING":
        if donor.casefold() != physics_family.casefold():
            raise ValueError(
                f"model donor {donor} has no effective package under DataGx\\Vehicles\\{donor}"
            )
        output_fn(
            f"{donor} has no installed model package. An explicit advanced override "
            "can keep the configuration-only experiment."
        )
        phrase = input_fn(
            f"Type {OVERRIDE_MISSING_MODEL} to continue, or press Enter to stop: "
        ).strip()
        if phrase != OVERRIDE_MISSING_MODEL:
            raise ValueError("model package is missing; no composition was applied")
        return donor, True, False

    if model.get("status") not in {"COMPLETE", "COMPLETE_WHEELLESS"}:
        output_fn(
            f"Model donor {donor} is {model['status']}; missing: "
            f"{', '.join(model.get('missing_resources', [])) or 'package validation issue'}"
        )
        phrase = input_fn(
            f"Type {OVERRIDE_INCOMPLETE_MODEL} to continue experimentally, or press Enter to stop: "
        ).strip()
        if phrase != OVERRIDE_INCOMPLETE_MODEL:
            raise ValueError("model donor is incomplete; no composition was applied")
        return donor, False, True
    return donor, False, False


def _show_composition_preview(
    inventory: InstallInventory,
    plan: Any,
    manifest_path: Path,
    output_fn: Callable[[str], Any],
) -> None:
    composition = plan.composition
    model = plan.donor_package
    output_fn("")
    output_fn("COMPOSITION PREVIEW")
    output_fn(f"  Carrier:              type {plan.type_id} / {composition.carrier_type}")
    output_fn(f"  Physics family:       {composition.physics_family}")
    output_fn(f"  Model donor:          {composition.model_donor}")
    output_fn(f"  Runtime family:       {composition.runtime_family}")
    output_fn(f"  Physics config:       Vehicles/{composition.physics_family} / "
              f"{plan.config_validation.config_schema.compatibility_class}")
    output_fn(f"  Modifications:        {composition.physics_family}/Player1 / "
              f"{plan.config_validation.player1_overlay_count} fields")
    if model:
        output_fn(
            f"  Model donor package:  DataGx\\Vehicles\\{composition.model_donor} / "
            f"{model['provenance']} / {model['file_count']} files"
        )
    else:
        output_fn("  Model donor package:  MISSING (advanced natural-family override)")
    output_fn(
        f"  Runtime model path:   DataGx\\Vehicles\\{composition.runtime_family}"
    )
    if plan.exe_patch_required:
        output_fn(
            f"  EXE mapping:          {composition.carrier_type} -> {composition.physics_family}"
        )
        output_fn(f"  EXE patch:            REQUIRED / {plan.output_exe}")
    else:
        output_fn("  EXE mapping:          unchanged")
        output_fn("  EXE patch:            NOT REQUIRED")
    output_fn(
        "  Model overlay:        "
        + (f"REQUIRED ({len(plan.overlay_writes)} writes, "
           f"{len(plan.overlay_removals)} stale loose removals)"
           if plan.model_overlay_required else "NOT REQUIRED (natural runtime-family package)")
    )
    if plan.archive_fallbacks:
        output_fn(
            f"  Unreferenced archive fallbacks retained: {len(plan.archive_fallbacks)} "
            "(parsed car/complete/wheel texture references are checked)"
        )
    output_fn(f"  Manifest:             {manifest_path}")
    output_fn(
        "  Runtime identity uses the physics family for both config/physics lookup "
        "and model-resource lookup."
    )
    output_fn(f"  Retail EXE:           {inventory.executable_sha256} (verified)")


def run_interactive_wizard(
    install_root: Path | None = None,
    *,
    dry_run: bool = False,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], Any] | None = None,
) -> int:
    """Compose a retail carrier, physics family, and independent model donor."""
    input_fn = input_fn or input
    output_fn = output_fn or print
    try:
        root = choose_install_root(install_root, input_fn=input_fn, output_fn=output_fn)
        inventory = load_install_inventory(root)
        output_fn(f"{USER_FACING_NAME}")
        output_fn(f"Install root: {root}")
        output_fn(f"Retail executable build: verified ({inventory.executable_sha256})")
        output_fn("")
        output_fn("Vehicle inventory (config-only and model-only entries are included):")
        for line in _family_table(inventory.families):
            output_fn(line)

        output_fn("")
        physics_rows = [
            row for row in inventory.families
            if row["base_config"]["status"] != "MISSING"
        ]
        output_fn("")
        output_fn("Select physics family (named config families only):")
        for index, row in enumerate(physics_rows, 1):
            output_fn(
                f"  [{index:>2}] {row['family']:<20.20} "
                f"{row['base_config']['status']:<24.24} "
                f"Player1 {row['player1_modifications']['status']}"
            )
        family_row = _ask_selection(
            "Physics family number or name: ",
            lambda value: select_family_row(physics_rows, value),
            input_fn=input_fn,
            output_fn=output_fn,
        )
        physics_family = family_row["family"]
        _show_schema_detail(family_row, output_fn)
        allow_unverified_schema = False
        schema_status = family_row["base_config"]["status"]
        if schema_status == "UNVERIFIED_SCHEMA":
            output_fn(
                "This family differs from the understood retail reader schema. "
                "Its runtime compatibility is UNVERIFIED."
            )
            phrase = input_fn(
                f"Type {UNVERIFIED_SCHEMA_OVERRIDE} to continue experimentally, or press Enter to stop: "
            ).strip()
            if phrase != UNVERIFIED_SCHEMA_OVERRIDE:
                return 2
            allow_unverified_schema = True
        elif schema_status != "COMPATIBLE":
            _validate_selected_family(inventory, physics_family)
            raise ValueError(
                f"{physics_family} config schema is {schema_status}; it cannot be bound."
            )
        _validate_selected_family(
            inventory,
            physics_family,
            allow_unverified_schema=allow_unverified_schema,
        )

        output_fn("")
        output_fn("Choose retail carrier to replace (initialized release catalog only):")
        for entry in RETAIL_FAMILY_CATALOG:
            output_fn(f"  [{entry.type_id:>2}] {entry.family}")
        carrier = _ask_selection(
            "Carrier type ID or name: ",
            select_retail_carrier,
            input_fn=input_fn,
            output_fn=output_fn,
        )

        model_donor, allow_missing_natural_model, allow_incomplete_model = _choose_model_donor(
            inventory,
            carrier,
            physics_family,
            input_fn=input_fn,
            output_fn=output_fn,
        )
        composition = VehicleComposition(carrier.family, physics_family, model_donor)
        output_path = choose_composition_output_exe(root, composition)
        manifest_path = choose_composition_manifest_path(
            root, composition, output_exe=output_path
        )
        plan = build_vehicle_composition_plan(
            inventory.executable,
            root,
            composition,
            inventory.vehicle_config,
            inventory.modifications_config,
            inventory.data_sma,
            inventory.archive_members,
            root / "DataGx" / "Vehicles",
            model_packages=inventory.model_packages,
            allow_unverified_schema=allow_unverified_schema,
            allow_missing_natural_model=allow_missing_natural_model,
            allow_incomplete_model=allow_incomplete_model,
            output_exe=output_path,
        )
        _show_composition_preview(inventory, plan, manifest_path, output_fn)
        if plan.config_validation.schema_override_used:
            output_fn(
                "WARNING: this family uses an unverified schema; the advanced "
                "schema override will be recorded in the validation manifest."
            )
        if not plan.exe_patch_required and not plan.model_overlay_required:
            output_fn("No EXE or model files need to change for this composition.")
            return 0
        if dry_run:
            output_fn("Preview complete. No executable, model files, backups, or manifest were written.")
            return 0
        if not _ask_yes_no(
            "Apply this vehicle composition? [Y/n]: ",
            default=True,
            input_fn=input_fn,
            output_fn=output_fn,
        ):
            output_fn("Cancelled. No executable, model files, backups, or manifest were written.")
            return 0
        result = apply_vehicle_composition(plan, manifest_path=manifest_path)

        output_fn(f"Composition ready: {result['composition']}")
        output_fn(f"Launch: {result['output_exe'] or inventory.executable}")
        output_fn(f"Manifest: {result['manifest']}")
        output_fn(
            "Restore later with: python tools/vehicle_composer.py restore --manifest "
            f'"{result["manifest"]}"'
        )
        return 0
    except EOFError:
        output_fn("Cancelled. No executable, backup, or manifest was written.")
        return 0
    except (FormatError, OSError, ValueError) as exc:
        output_fn(f"{USER_FACING_NAME}: {exc}")
        return 2


def discover_binding_manifests(install_root: Path) -> list[dict[str, Any]]:
    """Read direct-child tool manifests and verify their adjacent artifacts."""
    root = Path(install_root).expanduser().resolve()
    result = []
    for manifest_path in sorted(root.glob(f"*{MANIFEST_SUFFIX}"), key=lambda p: p.name.casefold()):
        output_name = manifest_path.name[:-len(MANIFEST_SUFFIX)]
        output_exe = root / output_name
        backup_path = output_exe.with_name(output_exe.name + ".original")
        row: dict[str, Any] = {
            "manifest": manifest_path,
            "output_exe": output_exe,
            "backup": backup_path,
            "manifest_data": None,
            "valid": False,
            "status": "INVALID_MANIFEST",
            "bindings": [],
        }
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("output_exe_name") != output_exe.name:
                raise ValueError("manifest output name does not match its filename")
            if data.get("backup_name") != backup_path.name:
                raise ValueError("manifest backup name does not match its output")
            source_sha = data.get("source_sha256")
            if source_sha != RETAIL_EXE_SHA256 or not backup_path.is_file():
                raise ValueError("verified retail backup is missing")
            backup_sha = hashlib.sha256(backup_path.read_bytes()).hexdigest()
            if backup_sha != source_sha:
                raise ValueError("backup SHA-256 does not match the manifest")
            state = data.get("status")
            bindings = data.get("bindings")
            if (
                not isinstance(bindings, list)
                or not bindings
                or any(
                    not isinstance(binding, dict)
                    or not isinstance(binding.get("carrier_type"), str)
                    or not isinstance(binding.get("physics_family"), str)
                    for binding in bindings
                )
            ):
                raise ValueError("manifest bindings are malformed")
            if state == "applied":
                if not output_exe.is_file() or hashlib.sha256(output_exe.read_bytes()).hexdigest() != data.get("patched_sha256"):
                    raise ValueError("bound output differs from the manifest")
            elif state == "restored":
                if not output_exe.is_file() or hashlib.sha256(output_exe.read_bytes()).hexdigest() != source_sha:
                    raise ValueError("restored output is not byte-identical to retail")
            else:
                raise ValueError("unknown manifest state")
            row.update({
                "manifest_data": data,
                "valid": True,
                "status": state,
                "bindings": data.get("bindings", []),
            })
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            row["error"] = str(exc)
        result.append(row)
    return result


def _find_model_for_family(
    model_packages: dict[str, dict[str, Any]], family: str
) -> dict[str, Any]:
    return model_packages.get(family.casefold(), {
        "provenance": "MISSING", "status": "MISSING", "missing_resources": list(MODEL_RESOURCES),
    })


def run_status_view(
    install_root: Path | None = None,
    *,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], Any] | None = None,
) -> int:
    input_fn = input_fn or input
    output_fn = output_fn or print
    try:
        root = choose_install_root(install_root, input_fn=input_fn, output_fn=output_fn)
    except EOFError:
        output_fn("Cancelled. No executable was changed.")
        return 0
    except (FormatError, OSError, ValueError) as exc:
        output_fn(f"{USER_FACING_NAME}: {exc}")
        return 2
    output_fn(f"{USER_FACING_NAME} - status")
    output_fn(f"Install root: {root}")
    try:
        inventory = load_install_inventory(root)
        output_fn(
            f"Retail source executable: {inventory.executable} "
            f"(verified SHA-256 {inventory.executable_sha256})"
        )
        model_packages = inventory.model_packages
    except EOFError:
        output_fn("Cancelled. No executable was changed.")
        return 0
    except (FormatError, OSError, ValueError) as exc:
        output_fn(f"Retail inventory unavailable: {exc}")
        model_packages = {}
    manifests = discover_binding_manifests(root)
    compositions = discover_vehicle_composition_manifests(root)
    if not manifests and not compositions:
        output_fn("No vehicle composition or legacy binding manifests found.")
        return 0
    for item in manifests:
        output_fn("")
        output_fn(f"Executable: {item['output_exe']}")
        output_fn(f"Manifest:   {item['manifest']} ({item['status']})")
        output_fn(f"Backup:     {item['backup']} ({'verified' if item['valid'] else 'unavailable'})")
        if not item["valid"]:
            output_fn(f"  Detail: {item.get('error', 'manifest validation failed')}")
            continue
        data = item["manifest_data"]
        for binding in item["bindings"]:
            carrier = binding.get("carrier_type", "?")
            family = binding.get("physics_family", "?")
            entry = next((candidate for candidate in RETAIL_FAMILY_CATALOG
                          if candidate.family == carrier), None)
            model = _find_model_for_family(model_packages, family)
            output_fn(
                f"Carrier: type {entry.type_id if entry else '?'} / {carrier}"
            )
            output_fn(f"Physics family: {family}")
            output_fn(f"Runtime family: {family}")
            output_fn(f"Model donor: {family} (runtime-family package)")
            output_fn(
                f"Model donor package: DataGx\\Vehicles\\{family} - "
                f"{model['status']} / {_model_provenance_label(model)}"
            )
            output_fn(f"Physics config: Vehicles/{family} + {family}/Player1")
        output_fn(f"Patched SHA-256: {data.get('patched_sha256', '?')}")
    for item in compositions:
        data = item.get("manifest_data") or {}
        composition = item.get("composition") or {}
        output_fn("")
        output_fn(f"Composition manifest: {item['manifest']} ({item['status']})")
        if not item["valid"]:
            output_fn(f"  Detail: {item.get('error', 'manifest validation failed')}")
            continue
        exe_changes = data.get("exe_changes")
        output_fn(f"Carrier:       {composition.get('carrier_type', '?')}")
        output_fn(f"Physics family: {composition.get('physics_family', '?')}")
        output_fn(f"Model donor:   {composition.get('model_donor', '?')}")
        output_fn(f"Runtime family: {data.get('runtime_family', '?')}")
        output_fn(f"EXE patch:     {'yes' if exe_changes else 'no'}")
        output_fn(f"Output EXE:    {item.get('output_exe') or 'MRallye.exe'}")
        output_fn(f"Model files:   {len(data.get('model_overlay_changes', []))} tracked changes")
        output_fn(f"Destination:   {data.get('model_destination_directory', '?')}")
        output_fn(f"Source hash:   {data.get('source_exe_sha256', '?')}")
    return 0


def run_restore_menu(
    install_root: Path | None = None,
    *,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], Any] | None = None,
) -> int:
    input_fn = input_fn or input
    output_fn = output_fn or print
    try:
        root = choose_install_root(install_root, input_fn=input_fn, output_fn=output_fn)
    except EOFError:
        output_fn("Cancelled. No executable was changed.")
        return 0
    except (FormatError, OSError, ValueError) as exc:
        output_fn(f"{USER_FACING_NAME}: {exc}")
        return 2
    legacy_manifests = discover_binding_manifests(root)
    composition_manifests = discover_vehicle_composition_manifests(root)
    manifests = [
        {**item, "kind": "legacy"} for item in legacy_manifests
    ] + [
        {**item, "kind": "composition"} for item in composition_manifests
    ]
    if not manifests:
        output_fn(f"No vehicle composition manifests or legacy backups were found in {root}.")
        return 0
    output_fn("Tool-managed vehicle compositions and executable copies:")
    for index, item in enumerate(manifests, 1):
        label = "ready to restore" if item["valid"] and item["status"] == "applied" else item["status"]
        if item["kind"] == "legacy":
            binding_text = ", ".join(
                f"Carrier {row.get('carrier_type', '?')} -> physics family "
                f"{row.get('physics_family', '?')}"
                for row in item["bindings"]
            )
            shown_path = item["output_exe"].name
        else:
            composition = item.get("composition") or {}
            binding_text = (
                f"{composition.get('carrier_type', '?')} / "
                f"{composition.get('physics_family', '?')} / "
                f"{composition.get('model_donor', '?')}"
            )
            shown_path = item.get("output_exe").name if item.get("output_exe") else "model overlay only"
        output_fn(f"  [{index}] {shown_path} - {binding_text} - {label}")
    while True:
        try:
            selection = input_fn("Select copy to restore, or press Enter to cancel: ").strip()
        except EOFError:
            output_fn("Cancelled. No files were changed.")
            return 0
        if not selection:
            output_fn("Cancelled. No files were changed.")
            return 0
        if not selection.isdecimal() or not 1 <= int(selection) <= len(manifests):
            output_fn("Invalid selection.")
            continue
        selected = manifests[int(selection) - 1]
        if not selected["valid"]:
            output_fn(f"Cannot restore this entry: {selected.get('error', selected['status'])}")
            return 2
        restorable_statuses = (
            {"applied", "interrupted"} if selected["kind"] == "composition"
            else {"applied"}
        )
        if selected["status"] not in restorable_statuses:
            output_fn("This composition or copy is already restored.")
            return 0
        break
    try:
        if selected["kind"] == "composition":
            composition = selected.get("composition") or {}
            restore_label = (
                f"composition {composition.get('carrier_type', '?')} / "
                f"{composition.get('physics_family', '?')} / "
                f"{composition.get('model_donor', '?')}"
            )
        else:
            restore_label = f"{selected['output_exe'].name} from its verified original backup"
        confirmed = _ask_yes_no(
            f"Restore {restore_label}? [y/N]: ",
            default=False,
            input_fn=input_fn,
            output_fn=output_fn,
        )
    except EOFError:
        output_fn("Cancelled. No files were changed.")
        return 0
    if not confirmed:
        output_fn("Cancelled. No files were changed.")
        return 0
    try:
        if selected["kind"] == "composition":
            result = restore_vehicle_composition(selected["manifest"], install_root=root)
        else:
            result = restore_binding_copy(selected["output_exe"])
    except EOFError:
        output_fn("Cancelled. No files were changed.")
        return 0
    except (FormatError, OSError, ValueError) as exc:
        output_fn(f"Restore refused: {exc}")
        return 2
    output_fn(f"Restore result: {result['status']}")
    if result.get("output_exe"):
        output_fn(f"Output: {result['output_exe']}")
    output_fn("The installed source MRallye.exe was not changed.")
    return 0


def build_status_payload(install_root: Path) -> dict[str, Any]:
    """Machine-readable inventory helper used by tests and future automation."""
    root = Path(install_root).expanduser().resolve()
    inventory = load_install_inventory(root)
    manifests = discover_binding_manifests(root)
    compositions = discover_vehicle_composition_manifests(root)
    return {
        "install_root": str(root),
        "retail_executable": str(inventory.executable),
        "retail_executable_sha256": inventory.executable_sha256,
        "families": inventory.families,
        "manifests": [
            {
                "manifest": str(item["manifest"]),
                "output_exe": str(item["output_exe"]),
                "status": item["status"],
                "valid": item["valid"],
                "bindings": item["bindings"],
            }
            for item in manifests
        ],
        "compositions": [
            {
                "manifest": str(item["manifest"]),
                "status": item["status"],
                "valid": item["valid"],
                "composition": item.get("composition"),
                "output_exe": str(item["output_exe"]) if item.get("output_exe") else None,
            }
            for item in compositions
        ],
    }
