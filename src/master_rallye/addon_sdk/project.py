"""Donor-based public addon project initialization and compilation bridge.

The project manifest defines addon identity. VehicleProject remains the
existing, separate authoring layer for compatible donor DX/DXT edits.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from ..vehicle_project import VehicleProject, validate_vehicle
from ..vehicle_packaging import read_sma_member
from .compiler import build_to_directory
from .manifest import (
    AddonValidationError, canonical_json, classify_runtime_identity,
    load_capabilities, load_manifests, read_json,
)
from .physics import clone_vehicle_family_xml
from .physics_profile import compile_family,validate_profile,validate_player_defaults


_FAMILY = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,39}$")
_DONOR = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
_CLASS_DEFAULTS = {
    "T1": {"donor": "Landcruiser", "stats": [4, 3, 6, 5], "frame": 3,
           "smallcarsheet": 9, "audio": 0, "unlock": 3, "colour": [0.25, 0.55, 0.85, 1.0]},
    "T2": {"donor": "Navara", "stats": [7, 6, 6, 5], "frame": 23,
           "smallcarsheet": 13, "audio": 7, "unlock": 10, "colour": [0.25, 0.55, 0.85, 1.0]},
}
_ENABLED_AI = {
    "quick_race": {"enabled": True, "boundary": "new_race", "pool": "dynamic_class"},
    "rallye_cup": {"enabled": True, "boundary": "new_cup", "pool": "dynamic_class"},
    "master_rallye": {"enabled": True, "boundary": "new_competition", "pool": "dynamic_class"},
    "invitation": {"enabled": False, "reason": "V1 Invitation qualification is limited to an explicit ordinary T3 policy."},
    "challenge": {"enabled": False, "reason": "Challenge rosters are authored and are not automatically modified."},
    "practice": {"enabled": False, "reason": "No distinct stock Practice AI pool is qualified."},
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,63}", slug):
        raise AddonValidationError("project name must produce a stable addon_id with 2..64 safe characters")
    return slug


def _absolute_without_links(path: Path, label: str) -> Path:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise AddonValidationError(f"{label} path contains a symbolic link or junction: {current}")
    return absolute


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _physics_family_overlays(*, data_sma: Path, retail_data_root: Path,
                             capabilities: dict[str, Any], donor_family: str,
                             runtime_family: str, physics_profile: dict | None = None) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Clone qualified DataGame values from an exact retail archive and corpus."""
    archive = _absolute_without_links(Path(data_sma), "retail Data.sma")
    root = _absolute_without_links(Path(retail_data_root), "retail data root")
    if not archive.is_file() or not root.is_dir():
        raise AddonValidationError("retail Data.sma and unpacked retail data root are both required")
    expected_sha = capabilities.get("retail_data_sma_sha256")
    expected_size = capabilities.get("retail_data_sma_size")
    if not isinstance(expected_sha, str) or not isinstance(expected_size, int):
        raise AddonValidationError("capability profile does not pin an exact retail Data.sma")
    actual_size = archive.stat().st_size
    actual_sha = _hash_file(archive)
    if actual_size != expected_size or actual_sha != expected_sha:
        raise AddonValidationError("retail Data.sma size/SHA256 does not match the selected capability profile")

    generated: dict[str, bytes] = {}
    members: dict[str, Any] = {}
    for member in ("DataGame/vehicles.xml", "DataGame/Modifications.xml"):
        archive_bytes = read_sma_member(archive, member)
        loose = _absolute_without_links(root.joinpath(*Path(member).parts), f"unpacked {member}")
        if not loose.is_file() or loose.read_bytes() != archive_bytes:
            raise AddonValidationError(f"unpacked retail resource differs from exact Data.sma member: {member}")
        if physics_profile is None:
            result, detail = clone_vehicle_family_xml(
                archive_bytes, donor_family=donor_family, runtime_family=runtime_family,
                source_label=member)
        else:
            result, detail = compile_family(archive_bytes,physics_profile,
                donor_family=donor_family,runtime_family=runtime_family,source_label=member)
        generated[member] = result
        members[member] = {
            "retail_member_sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "output_sha256": hashlib.sha256(result).hexdigest(),
            **detail,
        }
    if physics_profile is not None:
        validate_player_defaults(generated['DataGame/vehicles.xml'],generated['DataGame/Modifications.xml'],runtime_family,physics_profile.get('ride_height_reference_m'))
    return generated, {
        "retail_data_sma_sha256": actual_sha,
        "retail_data_sma_size": actual_size,
        "physics_family": f"Vehicles/{runtime_family}",
        "donor_family": donor_family,
        "resources": members,
        "runtime_overlay_ready": True,
        "runtime_installable": False,
        **({"profile": physics_profile} if physics_profile is not None else {}),
    }


def _physics_profile(root,donor,family):
    path=_absolute_without_links(root/'physics-profile.json','physics profile')
    if not path.exists():return None
    if not path.is_file() or path.stat().st_size>65536:raise AddonValidationError('physics profile must be a regular bounded JSON file')
    profile,_=read_json(path)
    return validate_profile(profile,donor_family=donor,runtime_family=family)


def _audio_artifacts(root,addon,physical_id):
    """Optional source-pinned audio, bound to resolved identity and stock tuning."""
    path=_absolute_without_links(root/'audio-profile.json','audio profile')
    if not path.exists():return {},None
    if not path.is_file() or path.stat().st_size>65536:raise AddonValidationError('audio profile must be a bounded regular JSON file')
    from .audio_profile import compile_audio
    profile,_=read_json(path)
    resources,report=compile_audio(profile,root)
    if profile['physical_car_id']!=physical_id or profile['stock_audio_profile_id']!=addon['audio']['stock_audio_profile_id']:
        raise AddonValidationError('audio profile differs from resolved CarID or native stock tuning')
    return {**resources,'audio-profile.json':canonical_json(profile)},report


def _visual_fitment_profile(root):
    """Optional explicit draw corrections; never edits a physics parameter."""
    path=_absolute_without_links(root/'visual-fitment.json','visual fitment profile')
    if not path.exists():return None
    if not path.is_file() or path.stat().st_size>65536:
        raise AddonValidationError('visual fitment must be a bounded regular JSON file')
    profile,_=read_json(path)
    if (set(profile)!={'profile_version','roles','provenance'} or type(profile['profile_version']) is not int
        or profile['profile_version']!=1 or not isinstance(profile['roles'],dict)
        or not profile['roles'] or set(profile['roles'])-{'car.dx','complete.dx'}
        or not isinstance(profile['provenance'],str) or not profile['provenance'].strip()):
        raise AddonValidationError('unsupported visual fitment profile')
    return profile


def _apply_visual_fitment(root,resources):
    profile=_visual_fitment_profile(root)
    if profile is None:return resources,None
    from .visual_fitment import translate_mechanics
    result=dict(resources);reports={}
    for role,definition in profile['roles'].items():
        if role not in result:raise AddonValidationError('visual fitment role is absent: '+role)
        try:result[role],reports[role]=translate_mechanics(result[role],definition)
        except ValueError as exc:raise AddonValidationError('visual fitment: '+str(exc)) from exc
    return result,{'profile':profile,'roles':reports,'runtime_qualified':False}


def _shadow_artifacts(root,family,model_data,retail_data_sma):
    path=_absolute_without_links(root/'shadow-profile.json','shadow profile')
    if not path.exists():return {},None
    if not path.is_file() or path.stat().st_size>65536 or retail_data_sma is None:
        raise AddonValidationError('shadow profile requires bounded JSON and exact retail Data.sma')
    from .vehicle_shadow import validate_profile as validate_shadow,bind_profile
    profile,_=read_json(path)
    try:
        validate_shadow(profile,runtime_family=family)
        bound=bind_profile(profile,model_data,read_sma_member(retail_data_sma,'DataGx/Misc/Shadow/shadow.dxt'))
    except ValueError as exc:raise AddonValidationError('shadow profile: '+str(exc)) from exc
    return {'shadow-profile.json':canonical_json(profile)},bound


def _publish_new_project(stage,output):
    """Bounded Windows sharing-lock retry; never replace an existing project."""
    import time
    for attempt in range(10):
        if output.exists():raise FileExistsError('project output already exists: '+str(output))
        try:os.replace(stage,output);return
        except PermissionError as error:
            if os.name!='nt' or getattr(error,'winerror',None)not in (5,32,33) or attempt==9:raise
            time.sleep(.05*(attempt+1))


def _mechanical_artifacts(root,family,resources,retail_data_sma,*,donor_family):
    path=_absolute_without_links(root/'mechanical-attachments.json','mechanical attachment profile')
    if not path.exists():return resources,None
    if _visual_fitment_profile(root) is not None:
        raise AddonValidationError('choose static visual fitment or dynamic mechanical attachments, not both')
    if not path.is_file() or path.stat().st_size>65536 or retail_data_sma is None:
        raise AddonValidationError('mechanical attachments require bounded JSON and exact retail Data.sma')
    profile,_=read_json(path)
    if (set(profile)!={'profile_version','definition','provenance'} or type(profile['profile_version']) is not int
        or profile['profile_version']!=1 or not isinstance(profile['provenance'],str) or not profile['provenance'].strip()):
        raise AddonValidationError('unsupported mechanical attachment profile')
    from .mechanical_attachments import build_mechanical_resources
    try:
        generated,detail=build_mechanical_resources(resources['car.dx'],resources['wheel.dx'],profile['definition'],
            stock_brake_template=read_sma_member(retail_data_sma,f'DataGx/Vehicles/{donor_family}/car.dx'))
    except ValueError as exc:raise AddonValidationError('mechanical attachments: '+str(exc)) from exc
    keys=[f'vehicles/{family}/'+group['resource'].removesuffix('.dx') for group in detail['groups']]
    return {**resources,**generated},{'profile':profile,'resources':detail,
        'native_profile':{'runtime_family':family,'resource_keys':keys},'runtime_qualified':False}


def _default_manifest(name: str, vehicle_class: str, family: str, donor: str) -> dict[str, Any]:
    defaults = _CLASS_DEFAULTS[vehicle_class]
    model = name.strip().upper()
    manufacturer = "MY MOD"
    return {
        "manifest_version": 1,
        "addon_id": _slug(name),
        "description": f"Donor-based {vehicle_class} addon authored from {donor}; replace these starter details with your project provenance.",
        "vehicle_class": vehicle_class,
        "physical_id": {"policy": "auto", "value": None},
        "class_local_placement": "append",
        "identity": {
            "runtime_family": family,
            "model_family": family,
            "wheel_family": family,
            "physics_family": f"Vehicles/{family}",
        },
        "assets": {
            "model_package_root": f"DataGx/Vehicles/{family}",
            "required_roles": ["car.dx", "complete.dx", "wheel.dx"],
        },
        "frontend": {
            "manufacturer": manufacturer,
            "model": model,
            "combined": f"{manufacturer} {model}",
            "stats": list(defaults["stats"]),
            "vehicle_select_art": {"policy": "stock_frame", "frame": defaults["frame"]},
            "smallcarsheet": {"policy": "stock_frame", "frame": defaults["smallcarsheet"]},
        },
        "race_colour_rgba": list(defaults["colour"]),
        "unlock": {"policy": "mirror_stock_unlock", "stock_vehicle_id": defaults["unlock"]},
        "audio": {"policy": "stock_profile", "stock_audio_profile_id": defaults["audio"]},
        "ai_eligibility": _ENABLED_AI,
        "results": {"policy": "fixed", "display_name": "TEST DRIVER"},
    }


def initialize_project(*, name: str, vehicle_class: str, donor: str,
                       output: Path, family: str | None = None,
                       donor_source: Path | None = None) -> dict[str, Any]:
    """Create a minimal author project without copying proprietary donor data."""
    if not isinstance(name, str) or not name.strip() or not name.isascii() or "\x00" in name:
        raise AddonValidationError("project name must be non-empty ASCII text without NUL")
    if vehicle_class not in _CLASS_DEFAULTS:
        raise AddonValidationError("V1 currently initializes only the runtime-qualified T1 and T2 addon classes")
    if not isinstance(donor, str) or not _DONOR.fullmatch(donor):
        raise AddonValidationError("donor must be a safe stock/demo family name, for example Navara")
    family_name = family or re.sub(r"[^A-Za-z0-9_]", "", name.replace(" ", ""))
    if not _FAMILY.fullmatch(family_name):
        raise AddonValidationError("family must be a safe resource identifier of 2..40 letters, digits or underscores")
    output = _absolute_without_links(Path(output), "project destination")
    if output.exists() or output.is_symlink() or getattr(output, "is_junction", lambda: False)():
        raise AddonValidationError(f"project destination already exists or is linked: {output}")
    if donor_source is not None:
        donor_source = _absolute_without_links(Path(donor_source), "donor source")
        if not donor_source.is_dir():
            raise AddonValidationError(f"donor source directory does not exist: {donor_source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.creating-", dir=output.parent))
    try:
        source_rel = Path("assets") / "source" / donor
        (stage / source_rel).mkdir(parents=True)
        for relative in ("assets/build", "physics", "artwork"):
            (stage / relative).mkdir(parents=True)
        manifest = _default_manifest(name, vehicle_class, family_name, donor)
        (stage / "addon.json").write_bytes(canonical_json(manifest))
        source_dir = str(donor_source) if donor_source else source_rel.as_posix()
        vehicle_project = {
            "vehicle_name": donor,
            "source_vehicle_dir": source_dir,
            "resources": {},
            "texture_edits": {},
            "texture_replacements": {},
        }
        (stage / "vehicle-project.json").write_bytes(canonical_json(vehicle_project))
        provenance = {
            "provenance_version": 1,
            "donor_family": donor,
            "vehicle_class": vehicle_class,
            "donor_source_is_bundled": False,
            "source_reference": "User-provided compatible retail/demo installation or previously validated VehicleProject.",
            "compatibility_must_be_verified": True,
        }
        (stage / "donor-provenance.json").write_bytes(canonical_json(provenance))
        readme = f"""# {name} — donor-based addon project

This project separates donor authoring (`vehicle-project.json`) from addon
identity/integration (`addon.json`). No game assets are included.

## First steps

1. Put your own compatible `{donor}` donor resources in
   `assets/source/{donor}/`, or set `source_vehicle_dir` in
   `vehicle-project.json` to a local verified source folder.
2. Use the existing Vehicle Authoring SDK workflow to edit DX/DXT resources;
   keep donor topology/material constraints and source hashes.
3. Edit `addon.json` display identity, stats, marker colour, unlock/audio
   donor, and fixed Results label. The starter class and identity family are
   safe defaults; change all four family fields together when changing family.
4. Run `mrtool addon project-validate {output.name}` and then
   `mrtool addon project-build {output.name} --output <new-output-dir>`.

The initial build is a deterministic offline integration plan plus validated
asset closure. It is not an installable runtime package until the selected
native target profile has a generated and verified runtime integration.
Only physical IDs 26/T1 and 27/T2 are currently runtime-qualified.
"""
        (stage / "README.md").write_text(readme, encoding="utf-8", newline="\n")
        _publish_new_project(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {"status": "PROJECT_INITIALIZED", "project": str(output),
            "addon_id": manifest["addon_id"], "runtime_family": family_name,
            "vehicle_class": vehicle_class, "donor": donor,
            "donor_source_supplied": donor_source is not None}


def validate_project(project_root: Path, capabilities_path: Path, *,
                     retail_data_sma: Path | None = None,
                     retail_data_root: Path | None = None) -> dict[str, Any]:
    root = _absolute_without_links(Path(project_root), "project")
    if not root.is_dir():
        raise AddonValidationError(f"project directory is missing: {root}")
    manifest_path = root / "addon.json"
    vehicle_path = root / "vehicle-project.json"
    _absolute_without_links(manifest_path, "addon manifest")
    _absolute_without_links(vehicle_path, "VehicleProject")
    if not manifest_path.is_file() or not vehicle_path.is_file():
        raise AddonValidationError("project requires addon.json and vehicle-project.json")
    manifests, _ = load_manifests([manifest_path])
    vehicle_spec, _ = read_json(vehicle_path)
    source_value = vehicle_spec.get("source_vehicle_dir")
    if not isinstance(source_value, str) or not source_value.strip():
        raise AddonValidationError("vehicle-project.json requires a non-empty source_vehicle_dir")
    source_path = Path(source_value)
    if not source_path.is_absolute():
        source_path = root / source_path
    source_path = _absolute_without_links(source_path, "donor source").resolve(strict=False)
    capabilities, _ = load_capabilities(capabilities_path)
    from .manifest import validate_manifests
    plan = validate_manifests(manifests, capabilities)
    try:
        vehicle = VehicleProject.load(vehicle_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AddonValidationError(f"VehicleProject configuration is invalid: {exc}") from exc
    if vehicle.source_vehicle_dir != source_path:
        raise AddonValidationError("VehicleProject donor source resolution changed during validation")
    if not vehicle.source_vehicle_dir.is_dir():
        return {"status": "FAIL", "addon_id": plan["addons"][0]["addon_id"],
                "physical_id": plan["addons"][0]["physical_id"],
                "vehicle_class": plan["addons"][0]["vehicle_class"],
                "diagnostics": [{"level": "FAIL", "message": f"donor source folder is absent: {vehicle.source_vehicle_dir.name}"}],
                "asset_diagnostics": None}
    for child in vehicle.source_vehicle_dir.iterdir():
        if child.is_symlink() or getattr(child, "is_junction", lambda: False)():
            raise AddonValidationError(f"donor source contains a linked entry: {child.name}")
    addon = plan["addons"][0]
    family = addon["identity"]["model_family"]
    if addon["identity"]["runtime_family"] != family or addon["identity"]["wheel_family"] != family:
        raise AddonValidationError("v1 author project must route runtime/model/wheel through its declared family")
    if addon["identity"]["physics_family"] != f"Vehicles/{family}":
        raise AddonValidationError("v1 author project physics_family must be Vehicles/<model family>")
    if addon["assets"]["model_package_root"] != f"DataGx/Vehicles/{family}":
        raise AddonValidationError("model package path must match the selected family")
    source_report = validate_vehicle(vehicle)
    if source_report["status"] == "FAIL":
        return {"status": "FAIL", "addon_id": addon["addon_id"],
                "physical_id": addon["physical_id"], "vehicle_class": addon["vehicle_class"],
                "diagnostics": source_report["diagnostics"],
                "asset_diagnostics": source_report.get("dependency_manifest")}
    if (retail_data_sma is None) != (retail_data_root is None):
        raise AddonValidationError("--retail-data-sma and --retail-data-root must be supplied together")
    physics_report = None
    profile = _physics_profile(root,vehicle.vehicle_name,family)
    if profile is not None and retail_data_sma is None:raise AddonValidationError('physics-profile.json requires exact retail Data.sma and unpacked root')
    if retail_data_sma is not None and retail_data_root is not None:
        _overlays, physics_report = _physics_family_overlays(
            data_sma=retail_data_sma, retail_data_root=retail_data_root,
            capabilities=capabilities, donor_family=vehicle.vehicle_name,
            runtime_family=family,physics_profile=profile)
    from .ui_assets import build_ui_assets
    if any(addon['frontend'][key]['policy']=='project_frame' for key in ('vehicle_select_art','smallcarsheet')):
        if retail_data_sma is None:
            raise AddonValidationError('project_frame UI assets require the stock --retail-data-sma')
        build_ui_assets(root, addon, retail_data_sma)  # validate the optional sidecar before building
    _audio,audio_report=_audio_artifacts(root,addon,addon['physical_id'])
    geometry={
        role:source_report.get('compiled',{}).get(role) or (vehicle.source_vehicle_dir/role).read_bytes()
        for role in ('car.dx','complete.dx','wheel.dx')}
    if profile and profile.get('collision_fit'):
        from .physics_collision import fit_collision
        geometry['car.dx'],_=fit_collision(geometry['car.dx'],profile['collision_fit'])
    _mechanical,mechanical_report=_mechanical_artifacts(root,family,geometry,retail_data_sma,donor_family=vehicle.vehicle_name)
    _visual,visual_report=_apply_visual_fitment(root,_mechanical)
    _shadow,shadow_report=_shadow_artifacts(root,family,
        _visual['car.dx'],retail_data_sma)
    return {"status": source_report["status"], "addon_id": addon["addon_id"],
            "physical_id": addon["physical_id"], "vehicle_class": addon["vehicle_class"],
            "class_local_index": addon["class_local_index"],
            "runtime_family": family, "physics_family": addon["identity"]["physics_family"],
            "donor": vehicle.vehicle_name, "source_validation": source_report,
            "runtime_qualification": classify_runtime_identity(addon, capabilities),
            "physics_family_resources": physics_report or "NOT_REQUESTED",
            **({'audio_resources':audio_report} if audio_report else {}),
            **({'visual_fitment':visual_report} if visual_report else {}),
            **({'shadow_bounds':shadow_report} if shadow_report else {}),
            **({'mechanical_attachments':mechanical_report} if mechanical_report else {}),
            "runtime_installable": False}


def build_project(project_root: Path, capabilities_path: Path, output: Path, *,
                  retail_data_sma: Path | None = None,
                  retail_data_root: Path | None = None) -> dict[str, Any]:
    """Bridge a validated VehicleProject payload into the deterministic addon compiler."""
    validation = validate_project(project_root, capabilities_path,
                                  retail_data_sma=retail_data_sma, retail_data_root=retail_data_root)
    if validation["status"] == "FAIL":
        details = "; ".join(row.get("message", "validation failed") for row in validation["diagnostics"])
        raise AddonValidationError(f"donor project validation failed: {details}")
    root = _absolute_without_links(Path(project_root), "project")
    output_path = _absolute_without_links(Path(output), "build output")
    if output_path == root or root in output_path.parents:
        raise AddonValidationError("build output must be outside the author project")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "addon.json"
    vehicle = VehicleProject.load(root / "vehicle-project.json")
    if output_path == vehicle.source_vehicle_dir or vehicle.source_vehicle_dir in output_path.parents:
        raise AddonValidationError("build output must be outside the donor source folder")
    source_validation = validation["source_validation"]
    family = validation["runtime_family"]
    manifests, _ = load_manifests([manifest_path])
    addon = manifests[0]
    physics_artifacts: dict[str, bytes] = {}
    physics_provenance: dict[str, Any] | None = None
    audio_artifacts,audio_report=_audio_artifacts(root,addon,validation['physical_id'])
    if (retail_data_sma is None) != (retail_data_root is None):
        raise AddonValidationError("--retail-data-sma and --retail-data-root must be supplied together")
    if retail_data_sma is not None and retail_data_root is not None:
        capabilities, _ = load_capabilities(capabilities_path)
        physics_artifacts, physics_provenance = _physics_family_overlays(
            data_sma=retail_data_sma, retail_data_root=retail_data_root,
            capabilities=capabilities, donor_family=vehicle.vehicle_name,
            runtime_family=family,physics_profile=_physics_profile(root,vehicle.vehicle_name,family))
        if physics_provenance.get('profile') is not None:
            physics_artifacts['physics-profile.json']=canonical_json(physics_provenance['profile'])
    physics_artifacts.update(audio_artifacts)
    from .ui_assets import build_ui_assets
    if any(addon['frontend'][key]['policy']=='project_frame' for key in ('vehicle_select_art','smallcarsheet')):
        if retail_data_sma is None:
            raise AddonValidationError('project_frame UI assets require the stock --retail-data-sma')
        ui_artifacts, ui_report = build_ui_assets(root, addon, retail_data_sma)
        physics_artifacts.update(ui_artifacts)
        physics_artifacts['ui-assets.report.json'] = canonical_json(ui_report)
    with tempfile.TemporaryDirectory(prefix=".mr-addon-author-build-", dir=output_path.parent) as temporary:
        temporary_root = Path(temporary)
        assets_root = temporary_root / "assets"
        target = assets_root.joinpath(*Path(addon["assets"]["model_package_root"]).parts)
        target.mkdir(parents=True)
        # Copy only model/texture resources. Authoring text sidecars and unrelated
        # donor data are not runtime dependencies.
        for source in sorted(vehicle.source_vehicle_dir.iterdir(), key=lambda item: item.name.casefold()):
            if source.is_symlink() or getattr(source, "is_junction", lambda: False)():
                raise AddonValidationError(f"donor resource is linked: {source.name}")
            if source.is_file() and source.suffix.casefold() in {".dx", ".dxt"}:
                shutil.copyfile(source, target / source.name)
        for role, data in source_validation.get("compiled", {}).items():
            (target / role).write_bytes(data)
        profile=(physics_provenance or {}).get('profile')
        if profile and profile.get('collision_fit'):
            from .physics_collision import fit_collision
            data,collision_report=fit_collision((target/'car.dx').read_bytes(),profile['collision_fit'])
            (target/'car.dx').write_bytes(data)
            physics_provenance['collision_fit']=collision_report
        mechanical,mechanical_report=_mechanical_artifacts(root,family,{
            role:(target/role).read_bytes() for role in ('car.dx','wheel.dx')},retail_data_sma,donor_family=vehicle.vehicle_name)
        for role,data in mechanical.items():(target/role).write_bytes(data)
        if mechanical_report:
            physics_artifacts['mechanical-attachments.json']=canonical_json(mechanical_report['profile'])
        visual_profile=_visual_fitment_profile(root)
        corrected,visual_report=_apply_visual_fitment(root,{
            role:(target/role).read_bytes() for role in (visual_profile or {}).get('roles',{})})
        for role,data in corrected.items():(target/role).write_bytes(data)
        if visual_profile is not None:
            physics_artifacts['visual-fitment.json']=canonical_json(visual_profile)
        shadow_artifacts,shadow_report=_shadow_artifacts(root,family,(target/'car.dx').read_bytes(),retail_data_sma)
        physics_artifacts.update(shadow_artifacts)
        project_hash = hashlib.sha256((root / "vehicle-project.json").read_bytes()).hexdigest()
        manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        source_hashes = [
            {"name": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
            for source in sorted(vehicle.source_vehicle_dir.iterdir(), key=lambda item: item.name.casefold())
            if source.is_file() and source.suffix.casefold() in {".dx", ".dxt"}
        ]
        provenance = {
            "project_metadata_version": 1,
            "project_path_label": root.name,
            "addon_manifest_sha256": manifest_hash,
            "vehicle_project_sha256": project_hash,
            "donor_family": vehicle.vehicle_name,
            "donor_resource_sha256": source_hashes,
            "runtime_family": family,
            "source_validation": validation["status"],
            "runtime_qualification": validation["runtime_qualification"],
            "physics_family_resources": physics_provenance or "NOT_REQUESTED",
            **({'audio_resources':audio_report} if audio_report else {}),
            **({'visual_fitment':visual_report} if visual_report else {}),
            **({'shadow_bounds':shadow_report} if shadow_report else {}),
            **({'mechanical_attachments':mechanical_report} if mechanical_report else {}),
            "runtime_installable": False,
        }
        return build_to_directory([manifest_path], capabilities_path, output_path,
                                  assets_root=assets_root, project_metadata=provenance,
                                  additional_artifacts=physics_artifacts)
