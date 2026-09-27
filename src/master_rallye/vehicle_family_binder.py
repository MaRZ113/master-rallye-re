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
    build_vehicle_family_inventory,
    inventory_vehicle_model_packages,
    select_family_row,
    select_retail_carrier,
)
from .vehicle_packaging import index_sma_members, read_sma_member
from .vehicle_physics_binding import (
    RETAIL_BUILD_NAME,
    RETAIL_FAMILY_CATALOG,
    PhysicsBinding,
    apply_binding_copy,
    restore_binding_copy,
    validate_binding_families,
    validate_binding_request,
)


USER_FACING_NAME = "Master Rallye Vehicle Family Binder"
MISSING_MODEL_OVERRIDE = "ALLOW MISSING MODEL"
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
        "DATA_SMA+LOOSE": "Data.sma + loose overrides",
        "MISSING": "missing",
    }.get(model["provenance"], model["provenance"])


def _family_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        " #  Family               Base config       Player1 mods   Model status / source",
        " -- -------------------- ----------------- -------------- ----------------------------",
    ]
    for index, row in enumerate(rows, 1):
        base = row["base_config"]
        overlay = row["player1_modifications"]
        model = row["model"]
        base_label = f"{base['status']} {base['field_count']}/{base['expected_field_count']}"
        overlay_label = f"{overlay['status']} {overlay['field_count']}/{overlay['expected_field_count']}"
        model_label = f"{model['status']} / {_model_provenance_label(model)}"
        lines.append(
            f" {index:>2}  {row['family']:<20.20} {base_label:<17} "
            f"{overlay_label:<14} {model_label}"
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


def _validate_selected_family(inventory: InstallInventory, family: str) -> None:
    # The established validator checks exact base schema and the typed Player1
    # overlay. A known initialized carrier is used only to enter that validator;
    # the user has not selected a carrier yet.
    named_vehicle_path(family)
    validate_binding_families(
        (PhysicsBinding(RETAIL_FAMILY_CATALOG[0].family, family),),
        inventory.vehicle_config,
        inventory.modifications_config,
    )


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
    output_fn(f"  New family:     {family_row['family']}")
    output_fn(f"  Model:          DataGx\\Vehicles\\{family_row['family']}")
    output_fn(f"  Model source:   {_model_provenance_label(model)} ({model['status']})")
    output_fn(f"  Physics:        Vehicles/{family_row['family']} - {base['status']}")
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


def run_interactive_wizard(
    install_root: Path | None = None,
    *,
    dry_run: bool = False,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], Any] | None = None,
) -> int:
    """Family-first wizard; validation and file writes use the shared backend."""
    input_fn = input_fn or input
    output_fn = output_fn or print
    try:
        root = choose_install_root(install_root, input_fn=input_fn, output_fn=output_fn)
        inventory = load_install_inventory(root)
        output_fn(f"{USER_FACING_NAME}")
        output_fn(f"Install root: {root}")
        output_fn(f"Retail executable build: verified ({inventory.executable_sha256})")
        output_fn("")
        output_fn("Vehicle families (config-only and model-only entries are included):")
        for line in _family_table(inventory.families):
            output_fn(line)

        family_row = _ask_selection(
            "Select vehicle family to activate (number or name): ",
            lambda value: select_family_row(inventory.families, value),
            input_fn=input_fn,
            output_fn=output_fn,
        )
        family = family_row["family"]
        if family_row["base_config"]["status"] != "COMPLETE":
            raise ValueError(
                f"{family} has no complete base vehicle config "
                f"({family_row['base_config']['status']}); it cannot be bound."
            )
        if family_row["player1_modifications"]["status"] != "COMPLETE":
            overlay = family_row["player1_modifications"]
            details = ", ".join(overlay["missing_fields"][:4]) or overlay["status"]
            raise ValueError(f"{family}/Player1 modifications are incomplete: {details}")
        _validate_selected_family(inventory, family)

        model = family_row["model"]
        if model["status"] not in {"COMPLETE", "COMPLETE_WHEELLESS"}:
            missing = ", ".join(model["missing_resources"]) or model["status"]
            if model["provenance"] == "MISSING":
                output_fn(
                    f"{family} configuration exists, but no model package was found at:\n\n"
                    f"    DataGx\\Vehicles\\{family}\n\n"
                    f"Missing resources: {missing}. The patched executable would not load "
                    "the required car/complete/wheel resources."
                )
            else:
                output_fn(
                    f"{family} model package is incomplete at DataGx\\Vehicles\\{family}: "
                    f"{missing}."
                )
            override = input_fn(
                f"Type {MISSING_MODEL_OVERRIDE} to continue anyway (advanced), or press Enter to stop: "
            ).strip()
            if override != MISSING_MODEL_OVERRIDE:
                return 2

        output_fn("")
        output_fn("Choose retail vehicle slot to replace (initialized release catalog only):")
        for entry in RETAIL_FAMILY_CATALOG:
            output_fn(f"  [{entry.type_id:>2}] {entry.family}")
        carrier = _ask_selection(
            "Carrier type ID or name: ",
            select_retail_carrier,
            input_fn=input_fn,
            output_fn=output_fn,
        )
        if carrier.family.casefold() == family.casefold():
            raise ValueError("the selected family already matches this carrier; no binding is needed")

        binding = PhysicsBinding(carrier.family, family)
        output_path = _choose_output_path(root, carrier.family, family)
        _show_family_preview(inventory, family_row, carrier, output_path, output_fn)
        with _materialized_config_paths(inventory) as (vehicles_xml, modifications_xml):
            report = validate_binding_request(
                inventory.executable,
                (binding,),
                vehicles_xml,
                modifications_xml,
            )
            output_fn("")
            output_fn(
                "Patch plan: VALID; source executable remains unchanged; "
                f"planned copy SHA-256 {report['planned_executable_sha256']}"
            )
            if dry_run:
                output_fn("Preview complete. No executable, backup, or manifest was written.")
                return 0
            if not _ask_yes_no(
                "Apply this vehicle-family binding? [Y/n]: ",
                default=True,
                input_fn=input_fn,
                output_fn=output_fn,
            ):
                output_fn("Cancelled. No executable, backup, or manifest was written.")
                return 0
            result = apply_binding_copy(
                inventory.executable,
                output_path,
                (binding,),
                vehicles_xml,
                modifications_xml,
            )

        output_fn(f"Binding copy ready: {result['output_exe']}")
        output_fn(f"Verified original backup: {result.get('backup', 'already present')}")
        output_fn(f"Manifest: {result['manifest']}")
        output_fn("Launch the output copy from the game directory to test the binding.")
        output_fn("Restore it later with: python tools/physics_bind.py restore")
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
    if not manifests:
        output_fn("No vehicle-family binding manifests found.")
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
            output_fn(f"Current binding: type {entry.type_id if entry else '?'} {carrier} -> {family}")
            output_fn(
                f"Model package:  DataGx\\Vehicles\\{family} - "
                f"{model['status']} / {_model_provenance_label(model)}"
            )
            output_fn(f"Physics/config: Vehicles/{family} + {family}/Player1")
        output_fn(f"Patched SHA-256: {data.get('patched_sha256', '?')}")
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
    manifests = discover_binding_manifests(root)
    if not manifests:
        output_fn(f"No binding manifests or backups were found in {root}.")
        return 0
    output_fn("Tool-owned executable copies:")
    for index, item in enumerate(manifests, 1):
        label = "ready to restore" if item["valid"] and item["status"] == "applied" else item["status"]
        binding_text = ", ".join(
            f"{row.get('carrier_type', '?')} -> {row.get('physics_family', '?')}"
            for row in item["bindings"]
        )
        output_fn(f"  [{index}] {item['output_exe'].name} - {binding_text or 'no binding'} - {label}")
    while True:
        try:
            selection = input_fn("Select copy to restore, or press Enter to cancel: ").strip()
        except EOFError:
            output_fn("Cancelled. No executable was changed.")
            return 0
        if not selection:
            output_fn("Cancelled. No executable was changed.")
            return 0
        if not selection.isdecimal() or not 1 <= int(selection) <= len(manifests):
            output_fn("Invalid selection.")
            continue
        selected = manifests[int(selection) - 1]
        if not selected["valid"]:
            output_fn(f"Cannot restore this entry: {selected.get('error', selected['status'])}")
            return 2
        if selected["status"] != "applied":
            output_fn("This copy is already restored.")
            return 0
        break
    try:
        confirmed = _ask_yes_no(
            f"Restore {selected['output_exe'].name} from its verified original backup? [y/N]: ",
            default=False,
            input_fn=input_fn,
            output_fn=output_fn,
        )
    except EOFError:
        output_fn("Cancelled. No executable was changed.")
        return 0
    if not confirmed:
        output_fn("Cancelled. No executable was changed.")
        return 0
    try:
        result = restore_binding_copy(selected["output_exe"])
    except EOFError:
        output_fn("Cancelled. No executable was changed.")
        return 0
    except (FormatError, OSError, ValueError) as exc:
        output_fn(f"Restore refused: {exc}")
        return 2
    output_fn(f"Restore result: {result['status']}")
    output_fn(f"Output: {result['output_exe']}")
    output_fn("The original MRallye.exe was not changed.")
    return 0


def build_status_payload(install_root: Path) -> dict[str, Any]:
    """Machine-readable inventory helper used by tests and future automation."""
    root = Path(install_root).expanduser().resolve()
    inventory = load_install_inventory(root)
    manifests = discover_binding_manifests(root)
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
    }
