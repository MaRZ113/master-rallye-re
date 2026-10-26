#!/usr/bin/env python3
"""Compile and verify a fail-closed J.3-B addon collection runtime bundle.

This compiler is deliberately limited to the audited two-slot retail profile:
physical ID26/T1 Mercedes plus physical ID27/T2. ID27 may be supplied either
by a validated Vehicle SDK project build or, for the compatibility regression,
by the exact qualified I.1 resource package. It emits the same bundle format
consumed by the existing J.1/J.2 external launcher; it does not emit an EXE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
from typing import Any
import zipfile

try:
    import addon_runtime
    import build_vehicle_multislot_i0 as i0
    import vehicle_multislot_i1_runtime_package as i1_package
    import build_runtime_launcher
    import j2_frontend_reentry as j2
    import prepare_multislot_vehicle_select_overlay as vehicle_select
except ImportError:  # pragma: no cover - package-style imports for tests
    from tools import addon_runtime, build_vehicle_multislot_i0 as i0
    from tools import vehicle_multislot_i1_runtime_package as i1_package
    from tools import build_runtime_launcher, j2_frontend_reentry as j2
    from tools import prepare_multislot_vehicle_select_overlay as vehicle_select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.addon_sdk.compiler import build_artifacts, verify_build  # noqa: E402
from master_rallye.addon_sdk.manifest import (  # noqa: E402
    AddonValidationError, canonical_json, load_capabilities,
    load_manifests,
)
from master_rallye.addon_sdk.physics import clone_vehicle_family_xml  # noqa: E402
from master_rallye.addon_sdk.physics_profile import apply_profile,validate_profile,validate_player_defaults  # noqa: E402
from master_rallye.addon_sdk import ui_assets  # noqa: E402

DEFAULT_RETAIL_EXE = addon_runtime.DEFAULT_RETAIL_EXE
DEFAULT_CAPABILITIES = addon_runtime.DEFAULT_CAPABILITIES
DEFAULT_BASE_PACKAGE = addon_runtime.DEFAULT_I1_PACKAGE
DEFAULT_OUTPUT = PROJECT_ROOT / ".research-output/vehicles/sdk/j3b/glacier-sprint-runtime"
RUNTIME_PROFILE_KIND = "j3b-compiled-addon-collection-runtime"
SUPPORT_LAYOUT = "physical-id26-t1-plus-id27-t2"
RETAIL_DATA_SMA_SHA256 = "03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f"
RETAIL_DATA_SMA_SIZE = 282_396_172
QUALIFIED_I1_PACKAGE_MANIFEST_SHA256 = "1880d850da88ab57b66a4ad996c68efded31e8fd5c237bfd641cb5d9064baebf"
QUALIFIED_I1_PACKAGE_DATA_SMA_SHA256 = "131d61ee8241df9cee4885db046e4e68d4df8177df40638bab01662ee12dc736"
QUALIFIED_I1_PACKAGE_DATA_SMA_SIZE = 282_687_977
REPLACED_BASE_RESOURCES = {
    "datagame/vehicles.xml",
    "datagame/modifications.xml",
    "datascene/frontendscreens/vehicleselect.xml",
}
MODE_KEYS = {
    "quickrace": "quick_race",
    "rallye_cup": "rallye_cup",
    "master_rallye": "master_rallye",
}


class CollectionRuntimeError(ValueError):
    """Reject unsupported collections, unsafe sources, or non-reproducible bundles."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_root(path: Path, label: str, *, must_exist: bool = True) -> Path:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise CollectionRuntimeError(f"{label} path contains a link: {current}")
    if must_exist and not absolute.exists():
        raise CollectionRuntimeError(f"{label} is missing: {absolute}")
    return absolute


def _resource_path(raw: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise CollectionRuntimeError("resource path must be a non-empty string")
    normalized = raw.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (pure.is_absolute() or ":" in normalized
            or any(part in {"", ".", ".."} for part in normalized.split("/"))
            or any(ch in normalized for ch in "\t|\r\n\x00")):
        raise CollectionRuntimeError(f"unsafe runtime resource path: {raw!r}")
    return pure.as_posix()


def _under(root: Path, relative: str) -> Path:
    path = root
    for part in PurePosixPath(_resource_path(relative)).parts:
        path = path / part
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise CollectionRuntimeError(f"resource source contains a link: {relative}")
    if not path.is_file():
        raise CollectionRuntimeError(f"runtime resource is missing: {relative}")
    return path


def _file_row(path: str, source: Path | bytes, role: str) -> dict[str, Any]:
    relative = _resource_path(path)
    if isinstance(source, bytes):
        size, digest = len(source), _sha(source)
    else:
        size, digest = source.stat().st_size, _sha_file(source)
    return {"path": relative, "size": size, "sha256": digest, "role": role}


def _assert_exact_stock_pair(plan: dict[str, Any], capabilities_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    addons = plan.get("addons")
    if not isinstance(addons, list) or len(addons) != 2:
        if isinstance(addons, list) and len(addons) == 1 and addons[0].get("physical_id") == 27:
            raise CollectionRuntimeError(
                "RUNTIME_LAYOUT_UNSUPPORTED: ID27-only is blocked because the audited native profile owns ID26/Mercedes; "
                "the compiler will not add Mercedes implicitly"
            )
        raise CollectionRuntimeError(
            "RUNTIME_LAYOUT_UNSUPPORTED: this audited native profile requires exactly ID26/T1 and ID27/T2; "
            "a T2-only collection must not acquire hidden Mercedes resources"
        )
    by_id = {row.get("physical_id"): row for row in addons}
    if set(by_id) != {26, 27}:
        if 27 in by_id and 26 not in by_id:
            raise CollectionRuntimeError(
                "RUNTIME_LAYOUT_UNSUPPORTED: ID27-only is blocked because the audited H.2 parent owns ID26/Mercedes; "
                "the compiler will not add Mercedes implicitly"
            )
        raise CollectionRuntimeError("RUNTIME_LAYOUT_UNSUPPORTED: only the qualified ID26 + ID27 sparse layout is supported")
    try:
        capabilities, _ = load_capabilities(capabilities_path)
        reference, _ = addon_runtime._reference_plan(addon_runtime.DEFAULT_MANIFESTS, capabilities_path)
    except (AddonValidationError, addon_runtime.RuntimeIntegrationError) as exc:
        raise CollectionRuntimeError(f"qualified reference policy could not be loaded: {exc}") from exc
    ref26 = next((row for row in reference.get("addons", []) if row.get("physical_id") == 26), None)
    row26, row27 = by_id[26], by_id[27]
    if ref26 is None or canonical_json(row26) != canonical_json(ref26):
        raise CollectionRuntimeError("ID26 must match the qualified Mercedes/T1 manifest and native policy exactly")
    if (row27.get("vehicle_class"), row27.get("class_local_index")) != ("T2", 7):
        raise CollectionRuntimeError("ID27 must remain the qualified physical T2/local7 slot")
    identity = row27.get("identity", {})
    families = (identity.get("runtime_family"), identity.get("model_family"),
                identity.get("wheel_family"), identity.get("physics_family"))
    runtime_family = families[0]
    if (not runtime_family or any(value != runtime_family for value in families[:3])
            or families[3] != f"Vehicles/{runtime_family}"):
        raise CollectionRuntimeError(
            "NATIVE_IDENTITY_UNSUPPORTED: the audited ID27 record routes model, wheels and physics through one family; "
            "runtime/model/wheel family names and Vehicles/<family> must agree"
        )
    unlock = row27.get("unlock", {})
    if (unlock.get("policy"), unlock.get("stock_vehicle_id")) != ("mirror_stock_unlock", 10):
        raise CollectionRuntimeError("ID27 runtime integration currently supports only the qualified T2CupCar1/stock-ID10 gate")
    if row27.get("audio", {}).get("policy") != "stock_profile":
        raise CollectionRuntimeError("ID27 must select an audited stock audio profile")
    if (row27.get("results", {}).get("policy") != "fixed"
            or not row27.get("results", {}).get("display_name")):
        raise CollectionRuntimeError("ID27 needs a fixed Results presentation identity")
    _ = capabilities
    return row26, row27


def _family_value_map(data: bytes, family: str, source_label: str) -> dict[str, dict[str, str]]:
    try:
        root = ET.fromstring(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, ET.ParseError) as exc:
        raise CollectionRuntimeError(f"{source_label} is not valid UTF-8 XML: {exc}") from exc
    prefix = f"Vehicles/{family}/"
    output: dict[str, dict[str, str]] = {}
    for node in root.iter("Value"):
        name = node.get("Name", "")
        if name.startswith(prefix):
            output[name] = dict(node.attrib)
    return output


def _assert_family_is_clone(data: bytes, donor: str, target: str, source_label: str) -> int:
    donor_values = _family_value_map(data, donor, source_label)
    target_values = _family_value_map(data, target, source_label)
    if not donor_values or not target_values:
        raise CollectionRuntimeError(f"{source_label} lacks donor or qualified addon family {target}")
    if len(donor_values) != len(target_values):
        raise CollectionRuntimeError(f"{source_label} donor and {target} family counts differ")
    for name, attributes in donor_values.items():
        target_name = name.replace(f"Vehicles/{donor}/", f"Vehicles/{target}/", 1)
        expected = dict(attributes)
        expected["Name"] = target_name
        if target_values.get(target_name) != expected:
            raise CollectionRuntimeError(f"{source_label} {target} values are not an exact donor clone")
    return len(target_values)


def _remove_family_rows(data: bytes, family: str, donor: str, source_label: str) -> bytes:
    _assert_family_is_clone(data, donor, family, source_label)
    marker = f'Name="Vehicles/{family}/'.encode("ascii")
    lines = data.splitlines(keepends=True)
    removed: list[bytes] = []
    kept: list[bytes] = []
    for line in lines:
        if marker in line:
            if b"<Value " not in line or b"/>" not in line:
                raise CollectionRuntimeError(f"{source_label} {family} values do not use the audited one-line Value format")
            removed.append(line)
        else:
            kept.append(line)
    if len(removed) != len(_family_value_map(data, family, source_label)):
        raise CollectionRuntimeError(f"{source_label} did not remove exactly the {family} overlay rows")
    result = b"".join(kept)
    if _family_value_map(result, family, source_label):
        raise CollectionRuntimeError(f"{source_label} still contains {family} rows after removal")
    return result


def _compose_family_xml(base_data: bytes, *, base_family: str, addon_family: str,
                        donor_family: str, expected_project_data: bytes | None,
                        source_label: str, physics_profile: dict | None = None) -> tuple[bytes, dict[str, Any]]:
    without_old = _remove_family_rows(base_data, base_family, "Navara", source_label)
    before_mercedes = _family_value_map(without_old, "Mercedes", source_label)
    try:
        output, report = clone_vehicle_family_xml(
            without_old, donor_family=donor_family, runtime_family=addon_family,
            source_label=source_label,
        )
        if physics_profile is not None:
            output,delta=apply_profile(output,physics_profile,donor_family=donor_family,
                runtime_family=addon_family,source_label=source_label)
            report.update(delta)
    except AddonValidationError as exc:
        raise CollectionRuntimeError(f"could not compose {source_label} for {addon_family}: {exc}") from exc
    if base_family != addon_family and _family_value_map(output, base_family, source_label):
        raise CollectionRuntimeError(f"composed {source_label} retains the replaced family {base_family}")
    after_mercedes = _family_value_map(output, "Mercedes", source_label)
    if before_mercedes != after_mercedes:
        raise CollectionRuntimeError(f"composed {source_label} changed the qualified ID26 Mercedes rows")
    if expected_project_data is not None:
        generated = _family_value_map(expected_project_data, addon_family, f"project {source_label}")
        composed = _family_value_map(output, addon_family, source_label)
        if generated != composed:
            raise CollectionRuntimeError(f"project-generated {source_label} differs from the composed collection output")
    return output, {"removed_family": base_family, "added_family": addon_family,
                    "donor_family": donor_family, "id26_mercedes_rows_preserved": True,
                    **report}


def _build_scene(base_scene: bytes, *, frame: int, project_frame: bool = False) -> tuple[bytes, dict[str, Any]]:
    try:
        text = base_scene.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CollectionRuntimeError("qualified VehicleSelect overlay is not UTF-8") from exc
    try:
        root = vehicle_select.g1._parse_xml(text)
    except Exception as exc:
        raise CollectionRuntimeError(f"qualified VehicleSelect XML failed parsing: {exc}") from exc
    frames: set[int] = set()
    for egg in root.iter("Egg"):
        value = vehicle_select.g1._direct_value(egg, "en2d Image Bank Index")
        if value is not None:
            raw = value.get("Value")
            if raw and raw.isdecimal():
                frames.add(int(raw))
    if project_frame and frame != ui_assets.BANKS['vehicle_select_art'][1]:
        raise CollectionRuntimeError('project Vehicle Select art must append exactly the admitted bank frame')
    if not project_frame and frame not in frames:
        raise CollectionRuntimeError(f"Vehicle Select stock art frame {frame} is not used by the qualified scene")
    start, end = vehicle_select.g1._egg_span(text, "T2_Car8")
    egg_text = text[start:end]
    slot_root = vehicle_select.g1._parse_xml(f"<Scene>{egg_text}</Scene>")
    slot = slot_root.find("./Egg")
    if slot is None or slot.get("Name") != "T2_Car8":
        raise CollectionRuntimeError("qualified T2_Car8 scene slot is missing or ambiguous")
    normal = vehicle_select.g1._direct_value(slot, "en2d Image Bank Index")
    if normal is None:
        raise CollectionRuntimeError("T2_Car8 has no normal image frame")
    _ai, disabler = vehicle_select.g1._ai_node(slot, "0", "gaFrontendDisablerAI")
    disabler_values = vehicle_select.g1._body_values(disabler)
    if (disabler_values.get("False Value") != "15"
            or disabler_values.get("Broker Value1*") != "Progress/UnlockedCars/T2CupCar1"):
        raise CollectionRuntimeError("T2_Car8 no longer has the qualified locked frame and T2 unlock oracle")
    button = vehicle_select.g1._ai_node(slot, "2", "gaFrontendXYButtonAI")[1]
    button_values = vehicle_select.g1._body_values(button)
    if (button_values.get("X ID") != "7" or button_values.get("Y ID") != "1"
            or button_values.get("XPos*") != "Frontend/VehicleSelect/Button7XPos"):
        raise CollectionRuntimeError("T2_Car8 no longer targets the qualified T2/local7 selector")
    changed = vehicle_select.g1._replace_value(egg_text, "en2d Image Bank Index", str(frame))
    changed = vehicle_select.g1._replace_value(changed, "True Value", str(frame))
    output_text = text[:start] + changed + text[end:]
    output = (b"\xef\xbb\xbf" if base_scene.startswith(b"\xef\xbb\xbf") else b"") + output_text.encode("utf-8")
    if output_text[:start] != text[:start] or output_text[start + len(changed):] != text[end:]:
        raise CollectionRuntimeError("VehicleSelect generation changed bytes outside the ID27 T2_Car8 slot")
    try:
        out_root = vehicle_select.g1._parse_xml(output_text)
    except Exception as exc:
        raise CollectionRuntimeError(f"generated VehicleSelect XML is invalid: {exc}") from exc
    out_start, out_end = vehicle_select.g1._egg_span(output_text, "T2_Car8")
    out_slot_root = vehicle_select.g1._parse_xml(f"<Scene>{output_text[out_start:out_end]}</Scene>")
    out_slot = out_slot_root.find("./Egg")
    out_frame = vehicle_select.g1._direct_value(out_slot, "en2d Image Bank Index") if out_slot is not None else None
    _ = out_root
    if out_frame is None or out_frame.get("Value") != str(frame):
        raise CollectionRuntimeError("generated T2_Car8 art frame does not match the addon manifest")
    return output, {"path": "DataScene/FrontendScreens/VehicleSelect.xml",
                    "base_sha256": _sha(base_scene), "sha256": _sha(output),
                    "widget": "T2_Car8", "physical_id": 27, "class_local_index": 7,
                    "unlocked_frame": frame, "locked_frame": 15,
                    "stock_slot_and_unlock_controls_preserved": True}


def _record_for_id27(row: dict[str, Any], profile: str) -> i0.registry.VehicleRecordProfile:
    identity = row["identity"]
    frontend = row["frontend"]
    rgba = bytes.fromhex(row["race_colour_rgba_f32le_hex"])
    if len(rgba) != 16:
        raise CollectionRuntimeError("ID27 manifest race marker must encode four little-endian floats")
    color_bits = struct.unpack("<4I", rgba)
    values = tuple(float(value) for value in row["race_colour_rgba"])
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise CollectionRuntimeError("ID27 race_colour_rgba is outside finite normalized range")
    if struct.pack("<4f", *values) != rgba:
        raise CollectionRuntimeError("ID27 race_colour_rgba float bytes differ from the canonical plan")
    family = identity["runtime_family"]
    unlock = row["unlock"]
    return i0.registry.VehicleRecordProfile(
        profile_id=profile,
        slot_id=27,
        vehicle_class=1,
        local_index=7,
        internal_name=family,
        stats=tuple(frontend["stats"]),
        smallcarsheet_index=frontend["smallcarsheet"]["frame"],
        race_colour_rgba_bits=tuple(color_bits),
        donor_id=7,
        runtime_family=identity["runtime_family"],
        vehicle_select_icon_frame=frontend["vehicle_select_art"]["frame"],
        display_selector_by_group=(),
        unlock_policy=f"mirror-stock-vehicle-id-{unlock['stock_vehicle_id']}",
        race_colour_role="manifest-configured runtime progress-marker RGBA; independent of vehicle textures",
        display_manufacturer=frontend["manufacturer"],
        display_model=frontend["model"],
        display_quickrace=frontend["combined"],
        asset_package=row["assets"]["model_package_root"],
        model_family=identity["model_family"],
        wheel_family=identity["wheel_family"],
        physics_family=identity["physics_family"],
    )


def _verify_independent_donor(root,donor,family,profile):
    """Recompute both exact retail member overlays before admitting a new donor.

    This is initialization-resource qualification, not new handling gameplay
    evidence. Legacy J.3-B retains its Navara-only default admission.
    """
    from master_rallye.addon_sdk.physics_profile import MEMBERS,compile_family,validate_player_defaults
    from master_rallye.addon_sdk.project import read_sma_member
    validate_profile(profile,donor_family=donor,runtime_family=family)
    outputs={}
    for member in MEMBERS:
        raw=read_sma_member(PROJECT_ROOT.parent/'corpora/retail/Data.sma',member)
        if _sha(raw)!=profile['source_sha256'][member]:raise CollectionRuntimeError('Independent donor retail source pin differs')
        data,_=compile_family(raw,profile,donor_family=donor,runtime_family=family,source_label=member)
        if data!=_under(root,member).read_bytes():raise CollectionRuntimeError('Independent donor overlay differs from exact retail recompilation')
        outputs[member]=data
    validate_player_defaults(outputs[MEMBERS[0]],outputs[MEMBERS[1]],family,profile.get('ride_height_reference_m'))


def _load_project_build(addon_id: str, manifest: dict[str, Any], manifest_bytes: bytes,
                        row: dict[str, Any], build_path: Path, *, allow_profile_donor: bool = False) -> tuple[Path, list[tuple[str, Path, str]], dict[str, Any]]:
    root = _safe_root(Path(build_path), f"{addon_id} project build")
    try:
        verified = verify_build(root)
        build_manifest = json.loads((root / "build-manifest.json").read_text(encoding="utf-8"))
        built_plan = json.loads((root / "addon-plan.json").read_text(encoding="utf-8"))
        inventory = json.loads((root / "resource-inventory.json").read_text(encoding="utf-8"))
    except (AddonValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        raise CollectionRuntimeError(f"{addon_id} project build failed validation: {exc}") from exc
    raw_manifest_sha = _sha(manifest_bytes)
    authoring = build_manifest.get("authoring_project", {})
    if (build_manifest.get("runtime_installable") is not False
            or authoring.get("runtime_installable") is not False
            or authoring.get("source_validation") != "PASS"
            or authoring.get("addon_manifest_sha256") != raw_manifest_sha
            or authoring.get("runtime_family") != row["identity"]["runtime_family"]):
        raise CollectionRuntimeError(f"{addon_id} project build provenance does not match the selected manifest")
    input_rows = build_manifest.get("input_manifests", [])
    if len(input_rows) != 1 or input_rows[0].get("sha256") != raw_manifest_sha:
        raise CollectionRuntimeError(f"{addon_id} project build was not created from this exact addon manifest")
    built_rows = {item.get("physical_id"): item for item in built_plan.get("addons", [])}
    if built_rows.get(row["physical_id"]) is None or canonical_json(built_rows[row["physical_id"]]) != canonical_json(row):
        raise CollectionRuntimeError(f"{addon_id} standalone project plan differs from the selected collection row")
    physics = authoring.get("physics_family_resources")
    if (not isinstance(physics, dict) or physics.get("runtime_overlay_ready") is not True
            or physics.get("retail_data_sma_sha256") != RETAIL_DATA_SMA_SHA256
            or physics.get("retail_data_sma_size") != RETAIL_DATA_SMA_SIZE
            or physics.get("physics_family") != row["identity"]["physics_family"]):
        raise CollectionRuntimeError(f"{addon_id} has no exact-build validated DataGame physics-family overlay")
    donor = authoring.get("donor_family")
    if donor != "Navara":
        if not allow_profile_donor or physics.get('profile') is None:
            raise CollectionRuntimeError("Non-Navara donors require the explicit roster path and a pinned independently compiled physics profile")
        _verify_independent_donor(root,donor,row['identity']['runtime_family'],physics['profile'])
    if physics.get('profile') is not None:
        profile=validate_profile(physics['profile'],donor_family=donor,runtime_family=row['identity']['runtime_family'])
        if _under(root,'physics-profile.json').read_bytes()!=canonical_json(profile):
            raise CollectionRuntimeError('physics profile artifact differs from build provenance')
        if any(profile['source_sha256'].get(member)!=record.get('retail_member_sha256') for member,record in physics.get('resources',{}).items()):
            raise CollectionRuntimeError('physics profile source pins differ from the validated archive members')
    if row["identity"]["runtime_family"].casefold() == donor.casefold():
        raise CollectionRuntimeError("addon runtime family must be independent of its donor family")

    expected_artifacts = build_manifest.get("artifact_sha256", {})
    visual=authoring.get('visual_fitment')
    if visual is not None:
        if canonical_json(visual.get('profile'))!=_under(root,'visual-fitment.json').read_bytes():
            raise CollectionRuntimeError('visual fitment sidecar differs from build provenance')
        for role,detail in visual.get('roles',{}).items():
            if role not in ('car.dx','complete.dx') or detail.get('status')!='PASS_STATIC_MECHANICAL_TRANSLATION':
                raise CollectionRuntimeError('unqualified visual fitment role')
            if _sha_file(_under(root,row['assets']['model_package_root']+'/'+role))!=detail.get('output_sha256'):
                raise CollectionRuntimeError('visual fitment output differs from build provenance')
    shadow=authoring.get('shadow_bounds')
    if shadow is not None:
        from master_rallye.addon_sdk.vehicle_shadow import bind_profile,validate_profile as validate_shadow
        from master_rallye.vehicle_packaging import read_sma_member
        definition=shadow.get('profile');validate_shadow(definition,runtime_family=row['identity']['runtime_family'])
        if canonical_json(definition)!=_under(root,'shadow-profile.json').read_bytes():
            raise CollectionRuntimeError('shadow profile sidecar differs from build provenance')
        car=_under(root,row['assets']['model_package_root']+'/car.dx').read_bytes()
        texture=read_sma_member(PROJECT_ROOT.parent/'corpora/retail/Data.sma','DataGx/Misc/Shadow/shadow.dxt')
        if bind_profile(definition,car,texture)!=shadow:
            raise CollectionRuntimeError('shadow bounds differ from verified emitted model and original texture')
    mechanics=authoring.get('mechanical_attachments')
    if mechanics is not None:
        if canonical_json(mechanics.get('profile'))!=_under(root,'mechanical-attachments.json').read_bytes():
            raise CollectionRuntimeError('mechanical attachment sidecar differs from provenance')
        expected_keys=[]
        for group in mechanics['resources']['groups']:
            role=group['resource']
            if role not in row['assets']['required_roles']:
                raise CollectionRuntimeError('mechanical resource must be an explicitly required DX role')
            if _sha_file(_under(root,row['assets']['model_package_root']+'/'+role))!=group['output_sha256']:
                raise CollectionRuntimeError('mechanical resource differs from provenance')
            expected_keys.append('vehicles/'+row['identity']['runtime_family']+'/'+role.removesuffix('.dx'))
        if mechanics['native_profile']!={'runtime_family':row['identity']['runtime_family'],'resource_keys':expected_keys}:
            raise CollectionRuntimeError('native mechanical resource keys differ from sealed family assets')
        if _sha_file(_under(root,row['assets']['model_package_root']+'/car.dx'))!=mechanics['resources']['body_sha256']:
            raise CollectionRuntimeError('mechanical body differs from provenance')
    audio=authoring.get('audio_resources');audio_path=None;audio_hashes={}
    if audio is not None:
        from master_rallye.addon_sdk.audio_profile import validate_profile as validate_audio,engine_resource,decode_pcm,audio_resource_hashes
        audio_profile=audio.get('audio_profile');validate_audio(audio_profile)
        if audio_profile['physical_car_id']!=row['physical_id'] or audio_profile['stock_audio_profile_id']!=row['audio']['stock_audio_profile_id']:
            raise CollectionRuntimeError('custom audio identity or stock tuning conflicts with collection')
        audio_path='DataAudio/'+engine_resource(audio_profile)+'.wav'
        if audio.get('resource_path')!=audio_path or canonical_json(audio_profile)!=(root/'audio-profile.json').read_bytes():
            raise CollectionRuntimeError('custom audio declaration differs from build provenance')
        audio_hashes=audio_resource_hashes(audio)
    actual_artifacts = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*") if path.is_file() and path.name != "build-manifest.json"
    }
    if actual_artifacts != set(expected_artifacts):
        raise CollectionRuntimeError(f"{addon_id} project build contains undeclared files")

    model_root = row["assets"]["model_package_root"].rstrip("/") + "/"
    expected_family_files: list[tuple[str, Path, str]] = []
    seen: set[str] = set()
    for item in inventory.get("resources", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise CollectionRuntimeError(f"{addon_id} resource inventory is malformed")
        path = _resource_path(item["path"])
        folded = path.casefold()
        if folded in seen:
            raise CollectionRuntimeError(f"{addon_id} resource inventory has duplicate path {path}")
        seen.add(folded)
        if path.casefold().startswith(model_root.casefold()):
            if item.get("status") != "HASHED_AND_PARSED":
                raise CollectionRuntimeError(f"{addon_id} model resource was not parsed and hashed: {path}")
            source = _under(root, path)
            if (source.stat().st_size, _sha_file(source)) != (item.get("size"), item.get("sha256")):
                raise CollectionRuntimeError(f"{addon_id} model resource hash differs: {path}")
            expected_family_files.append((path, source, "validated_addon_model_or_texture"))
        elif path in audio_hashes:
            source=_under(root,path);raw=source.read_bytes();_samples,fmt=decode_pcm(raw)
            if (len(raw),_sha(raw))!=(item.get('size'),item.get('sha256')) or _sha(raw)!=audio_hashes[path]:
                raise CollectionRuntimeError('custom audio resource hash differs from provenance')
            if (fmt['sample_rate'],fmt['channels'],fmt['bits_per_sample'])!=(48000,1,16) or len(raw)!=44+fmt['frames']*2:
                raise CollectionRuntimeError('unsupported native custom audio encoding')
            expected_family_files.append((path,source,'validated_independent_bov_release' if path.endswith('/bov_release.wav') else 'validated_independent_turbo_spool' if path.endswith('/turbo_spool.wav') else 'validated_independent_transmission_whine' if path.endswith('/transmission_whine.wav') else 'validated_independent_engine_audio'))
        elif path.casefold() in {"datagame/vehicles.xml", "datagame/modifications.xml"}:
            source = _under(root, path)
            if (source.stat().st_size, _sha_file(source)) != (item.get("size"), item.get("sha256")):
                raise CollectionRuntimeError(f"{addon_id} generated physics resource hash differs: {path}")
        elif any(row['frontend'][key]['policy']=='project_frame' and path in {
                ui_assets.BANKS[key][0]+'.dxb',
                ui_assets.BANKS[key][0]+f'_{ui_assets.BANKS[key][1]:03d}_000.dxt'} for key in ui_assets.BANKS):
            source = _under(root, path)
            if (source.stat().st_size, _sha_file(source)) != (item.get('size'), item.get('sha256')):
                raise CollectionRuntimeError(f'{addon_id} UI resource hash differs: {path}')
        else:
            raise CollectionRuntimeError(f"{addon_id} build declares an unsupported runtime resource: {path}")
    required_paths = {f"{row['assets']['model_package_root']}/{role}".casefold()
                      for role in row["assets"]["required_roles"]}
    present_paths = {item[0].casefold() for item in expected_family_files}
    if not required_paths <= present_paths:
        raise CollectionRuntimeError(f"{addon_id} build lacks required DX resources: {sorted(required_paths-present_paths)}")
    if not expected_family_files:
        raise CollectionRuntimeError(f"{addon_id} build has no selected family asset resources")
    if any(path.casefold() not in present_paths for path in audio_hashes):
        raise CollectionRuntimeError('declared custom audio resource is absent')
    return root, expected_family_files, {
        "addon_id": addon_id, "build_manifest_sha256": _sha((root / "build-manifest.json").read_bytes()),
        "addon_manifest_sha256": raw_manifest_sha, "donor_family": donor,
        "runtime_family": row["identity"]["runtime_family"],
        "resource_count": len(expected_family_files),
        "physics_vehicles_sha256": _sha_file(root / "DataGame" / "vehicles.xml"),
        "physics_modifications_sha256": _sha_file(root / "DataGame" / "Modifications.xml"),
        **({"physics_profile": physics['profile']} if physics.get('profile') is not None else {}),
        **({'audio_profile':audio_profile,'audio_resources':audio} if audio is not None else {}),
        **({'visual_fitment':visual} if visual is not None else {}),
        **({'shadow_bounds':shadow} if shadow is not None else {}),
        **({'mechanical_attachments':mechanics} if mechanics is not None else {}),
        "verification": verified,
    }


def _collection_resources(*, base_package: Path, base_rows: list[dict[str, Any]],
                          base_manifest: dict[str, Any], row27: dict[str, Any],
                          project_build: Path | None,
                          project_family_files: list[tuple[str, Path, str]],
                          project_source_report: dict[str, Any] | None,
                          output_row_sources: dict[str, tuple[dict[str, Any], Path | bytes]],
                          project_report: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    source_id27 = base_manifest.get("id27", {})
    source_family = source_id27.get("runtime_family")
    if not isinstance(source_family, str) or not source_family:
        raise CollectionRuntimeError("qualified base package has no ID27 family source metadata")
    if project_build is None and source_family != row27["identity"]["runtime_family"]:
        raise CollectionRuntimeError(
            "ID27 needs an exact validated author project build; base-package assets may only satisfy the matching reference identity"
        )

    base_kept: list[dict[str, Any]] = []
    old_family_prefix = f"DataGx/Vehicles/{source_family}/".casefold()
    selected_family_prefix = f"DataGx/Vehicles/{row27['identity']['model_family']}/".casefold()
    for item in base_rows:
        path = _resource_path(item["path"])
        folded = path.casefold()
        if folded.startswith(old_family_prefix) or folded in REPLACED_BASE_RESOURCES:
            continue
        if folded.startswith("datagx/vehicles/" + source_family.casefold() + "/"):
            continue
        base_kept.append(item)

    id27_assets: list[tuple[str, Path, str]] = []
    source_report: dict[str, Any]
    if project_build is not None:
        id27_assets = list(project_family_files)
        if not id27_assets or project_source_report is None:
            raise CollectionRuntimeError("validated ID27 project resources are missing from compile context")
        source_report = dict(project_source_report)
        if source_report["runtime_family"] != row27["identity"]["runtime_family"]:
            raise CollectionRuntimeError("project runtime family differs from collection identity")
    else:
        if (source_id27.get("physical_id"), source_id27.get("class"), source_id27.get("local_index")) != (27, 1, 7):
            raise CollectionRuntimeError("qualified reference asset source is not the physical ID27/T2-local7 package")
        if source_family != row27["identity"]["runtime_family"]:
            raise CollectionRuntimeError("reference package family differs from the requested ID27 family")
        for item in base_rows:
            path = _resource_path(item["path"])
            if path.casefold().startswith(selected_family_prefix):
                id27_assets.append((path, addon_runtime._inside(base_package, path), "qualified_reference_addon_resource"))
        if not id27_assets:
            raise CollectionRuntimeError("qualified base package has no ID27 family resource payload")
        source_report = {"addon_id": row27["addon_id"], "source_kind": "exact-qualified-I1-reference-package",
                         "runtime_family": source_family, "resource_count": len(id27_assets),
                         "resource_package_manifest_sha256": _sha_file(base_package / i1_package.RUNTIME_MANIFEST_NAME)}

    asset_paths = {path.casefold() for path, _source, _role in id27_assets}
    required = {f"{row27['assets']['model_package_root']}/{role}".casefold()
                for role in row27["assets"]["required_roles"]}
    if not required <= asset_paths:
        raise CollectionRuntimeError(f"ID27 resource source lacks required roles: {sorted(required-asset_paths)}")

    # The base I.1 package supplies stock files and the already-qualified
    # Mercedes/ID26 family. Its previous ID27 family and family XML are removed;
    # selected ID27 assets and two freshly composed DataGame files are added.
    for item in base_kept:
        path = _resource_path(item["path"])
        output_row_sources[path.casefold()] = (dict(item), addon_runtime._inside(base_package, path))
    for path, source, role in id27_assets:
        row = _file_row(path, source, role)
        key = row["path"].casefold()
        if key in output_row_sources:
            raise CollectionRuntimeError(f"case-insensitive runtime resource collision: {path}")
        output_row_sources[key] = (row, source)

    # Replace only the old ID27 clone rows, then append the new independently
    # named clone. Compare it against the exact J.3-A project output.
    old_vehicles = addon_runtime._inside(base_package, "DataGame/vehicles.xml").read_bytes()
    old_modifications = addon_runtime._inside(base_package, "DataGame/Modifications.xml").read_bytes()
    expected_vehicles = expected_modifications = None
    donor_family = "Navara"
    if project_build is not None:
        build_root = _safe_root(project_build, "ID27 project build")
        expected_vehicles = _under(build_root, "DataGame/vehicles.xml").read_bytes()
        expected_modifications = _under(build_root, "DataGame/Modifications.xml").read_bytes()
        donor_family = source_report["donor_family"]
    if project_build is None and row27["identity"]["runtime_family"] == source_family:
        # The reference collection already contains the exact qualified ID27
        # DataGame family. Verify its donor relationship, then retain the
        # source bytes to keep the compatibility regression resource-exact.
        vehicles_count = _assert_family_is_clone(
            old_vehicles, "Navara", source_family, "DataGame/vehicles.xml")
        modifications_count = _assert_family_is_clone(
            old_modifications, "Navara", source_family, "DataGame/Modifications.xml")
        vehicle_xml, mods_xml = old_vehicles, old_modifications
        vehicle_report = {
            "source_label": "DataGame/vehicles.xml", "runtime_family": source_family,
            "donor_family": "Navara", "verified_existing_family_value_count": vehicles_count,
            "reused_exact_qualified_base_bytes": True, "id26_mercedes_rows_preserved": True,
            "stock_values_preserved_byte_exact": True, "semantic_delta": False,
        }
        mods_report = {
            "source_label": "DataGame/Modifications.xml", "runtime_family": source_family,
            "donor_family": "Navara", "verified_existing_family_value_count": modifications_count,
            "reused_exact_qualified_base_bytes": True, "id26_mercedes_rows_preserved": True,
            "stock_values_preserved_byte_exact": True, "semantic_delta": False,
        }
    else:
        vehicle_xml, vehicle_report = _compose_family_xml(
            old_vehicles, base_family=source_family,
            addon_family=row27["identity"]["runtime_family"], donor_family=donor_family,
            expected_project_data=expected_vehicles, source_label="DataGame/vehicles.xml",
            physics_profile=source_report.get('physics_profile'))
        mods_xml, mods_report = _compose_family_xml(
            old_modifications, base_family=source_family,
            addon_family=row27["identity"]["runtime_family"], donor_family=donor_family,
            expected_project_data=expected_modifications, source_label="DataGame/Modifications.xml",
            physics_profile=source_report.get('physics_profile'))
    if source_report.get('physics_profile') is not None:
        validate_player_defaults(vehicle_xml,mods_xml,row27['identity']['runtime_family'],source_report['physics_profile'].get('ride_height_reference_m'))
    for path, data, role in (
        ("DataGame/vehicles.xml", vehicle_xml, "composed_stock_ID26_and_selected_ID27_vehicle_physics"),
        ("DataGame/Modifications.xml", mods_xml, "composed_stock_ID26_and_selected_ID27_modifications"),
    ):
        row = _file_row(path, data, role)
        output_row_sources[path.casefold()] = (row, data)

    scene_source = addon_runtime._inside(base_package, "DataScene/FrontendScreens/VehicleSelect.xml").read_bytes()
    frame = row27["frontend"]["vehicle_select_art"]["frame"]
    if (row27["frontend"]["vehicle_select_art"].get("policy") not in {"stock_frame", "project_frame"}
            or type(frame) is not int or frame < 0):
        raise CollectionRuntimeError("ID27 Vehicle Select art must use a valid stock_frame selector")
    scene, scene_report = _build_scene(scene_source, frame=frame,
        project_frame=row27['frontend']['vehicle_select_art']['policy']=='project_frame')
    scene_row = _file_row("DataScene/FrontendScreens/VehicleSelect.xml", scene,
                          "generated_ID27_T2_Car8_art_and_existing_lock_control")
    output_row_sources[scene_row["path"].casefold()] = (scene_row, scene)

    # SmallCarSheet frames are embedded in Data.sma, not loose runtime files.
    # Verify the selected atlas entry exists without extracting or rewriting
    # the stock archive.
    small_frame = row27["frontend"]["smallcarsheet"]["frame"]
    small_path = f"DataGx/Frontend/RaceResults/smallcarsheet_{small_frame:03d}_000.dxt"
    try:
        with zipfile.ZipFile(base_package / "Data.sma") as archive:
            has_ui=any(row27['frontend'][key]['policy']=='project_frame' for key in ui_assets.BANKS)
            if has_ui:
                if project_build is None:raise CollectionRuntimeError('project_frame requires a validated author build')
                generated_ui=ui_assets.verify_ui_resources(project_build,row27,archive)
                for path, data in generated_ui.items():
                    ui_row=_file_row(path,data,'validated_append_only_UI_bank_or_frame')
                    output_row_sources[path.casefold()]=(ui_row,data)
            if row27['frontend']['smallcarsheet']['policy']=='project_frame':
                small_bytes=generated_ui[small_path]
            else:
                matches = [name for name in archive.namelist() if name.casefold() == small_path.casefold()]
                if len(matches) != 1:
                    raise CollectionRuntimeError(f"ID27 SmallCarSheet frame {small_frame} is absent or ambiguous in Data.sma")
                small_bytes = archive.read(matches[0])  # also verifies the member CRC
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise CollectionRuntimeError(f"could not verify ID27 SmallCarSheet frame {small_frame} in Data.sma") from exc

    resources = [dict(value[0]) for value in output_row_sources.values()]
    resources.sort(key=lambda item: item["path"].casefold())
    addon_runtime._resource_index(resources)  # validates paths, hashes, and case-insensitive uniqueness
    if any(item["path"].casefold() == "mrallye.exe" for item in resources):
        raise CollectionRuntimeError("runtime resource root must not include a replacement executable")
    if project_build is not None and row27["identity"]["runtime_family"].casefold() != source_family.casefold():
        # No selected output may retain the displaced reference family's paths
        # or text. Binary Data.sma is stock and is checked separately.
        for path, source, _role in id27_assets:
            if source_family.casefold() in path.casefold():
                raise CollectionRuntimeError("selected addon resource path retains the displaced base family")
        for key, (_row, source) in output_row_sources.items():
            if key.startswith("datagx/vehicles/") and key.startswith(old_family_prefix):
                raise CollectionRuntimeError("runtime root contains displaced ID27 family resources")
            if key in {"datagame/vehicles.xml", "datagame/modifications.xml"}:
                data = source if isinstance(source, bytes) else source.read_bytes()
                if source_family.encode("ascii") in data:
                    raise CollectionRuntimeError("composed DataGame XML retains displaced family references")
        if b"R5VQualifier" in runtime_family_bytes(row27):
            raise CollectionRuntimeError("custom native ID27 profile contains a stale R5VQualifier identity")

    report = {
        "base_resource_profile": base_manifest.get("profile"),
        "base_package_manifest_sha256": _sha_file(base_package / i1_package.RUNTIME_MANIFEST_NAME),
        "base_resource_count": len(base_rows),
        "selected_id27_source": source_report,
        "selected_id27_resource_count": len(id27_assets),
        "smallcarsheet_archive_asset": {"path": small_path, "size": len(small_bytes),
                                        "sha256": _sha(small_bytes),
                                        "staged_as_loose_override": row27['frontend']['smallcarsheet']['policy']=='project_frame'},
        "replaced_id27_family": source_family,
        "resource_count": len(resources),
        "vehicle_select": scene_report,
        "physics": {"vehicles": vehicle_report, "modifications": mods_report},
        "resource_inventory_sha256": _sha(addon_runtime.canonical_json({"resources": resources})),
        "original_stock_archive_modified": False,
        "original_executable_copied": False,
    }
    if project_report is not None:
        project_report.update(source_report)
    return {"artifact_version": 1,
            "artifact_kind": "validated selected collection runtime-resource inventory",
            "status": "STAGED_STATIC_EXTERNAL_RESOURCE_ROOT",
            "resources": resources}, report


def runtime_family_bytes(row: dict[str, Any]) -> bytes:
    identity = row.get("identity", {})
    frontend = row.get("frontend", {})
    results = row.get("results", {})
    return "\0".join(str(value) for value in (
        identity.get("runtime_family"), identity.get("model_family"),
        identity.get("wheel_family"), identity.get("physics_family"),
        frontend.get("manufacturer"), frontend.get("model"), frontend.get("combined"),
        results.get("display_name"),
    )).encode("ascii", errors="strict")


def _compile_context(*, manifest_paths: list[Path], project_builds: dict[str, Path],
                     capabilities_path: Path, retail_exe: Path, base_package: Path) -> dict[str, Any]:
    try:
        manifests, provenance = load_manifests(manifest_paths)
        capabilities, capability_sha = load_capabilities(capabilities_path)
        artifacts = build_artifacts(manifests, capabilities)
    except (AddonValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        raise CollectionRuntimeError(f"addon collection validation failed: {exc}") from exc
    plan_bytes = artifacts["addon-plan.json"]
    plan = json.loads(plan_bytes.decode("utf-8"))
    row26, row27 = _assert_exact_stock_pair(plan, capabilities_path)
    source = _safe_root(retail_exe, "retail executable")
    exe_check = addon_runtime.verify_retail_executable(source, capabilities)
    if (exe_check["sha256"] != addon_runtime.RETAIL_SHA256
            or exe_check["size"] != addon_runtime.RETAIL_SIZE):
        raise CollectionRuntimeError("runtime compiler requires the exact pristine supported retail executable")
    if _sha_file(source) != addon_runtime.RETAIL_SHA256:
        raise CollectionRuntimeError("retail executable changed during collection validation")
    cap_file = _safe_root(capabilities_path, "capabilities file")
    base = _safe_root(base_package, "qualified resource base package")
    try:
        base_manifest, base_rows = addon_runtime._expected_resources(base)
    except (addon_runtime.RuntimeIntegrationError, OSError, ValueError, KeyError, TypeError) as exc:
        raise CollectionRuntimeError(f"qualified resource base package failed verification: {exc}") from exc
    base_manifest_path = base / i1_package.RUNTIME_MANIFEST_NAME
    if _sha_file(base_manifest_path) != QUALIFIED_I1_PACKAGE_MANIFEST_SHA256:
        raise CollectionRuntimeError("resource base package manifest differs from the qualified I.1 runtime package")
    data_row = next((item for item in base_rows if item.get("path", "").casefold() == "data.sma"), None)
    if (data_row is None or data_row.get("sha256") != QUALIFIED_I1_PACKAGE_DATA_SMA_SHA256
            or data_row.get("size") != QUALIFIED_I1_PACKAGE_DATA_SMA_SIZE):
        raise CollectionRuntimeError("resource base package Data.sma differs from the exact qualified I.1 overlay archive")
    if (base_manifest.get("id27", {}).get("physical_id"),
            base_manifest.get("id27", {}).get("class"),
            base_manifest.get("id27", {}).get("local_index")) != (27, 1, 7):
        raise CollectionRuntimeError("resource base package is not the qualified sparse ID27/T2-local7 profile")

    manifest_by_id: dict[str, dict[str, Any]] = {}
    raw_manifest_by_id: dict[str, bytes] = {}
    for path in manifest_paths:
        raw = _safe_root(path, "addon manifest").read_bytes()
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CollectionRuntimeError(f"addon manifest is invalid JSON: {path.name}") from exc
        manifest_by_id[data.get("addon_id")] = data
        raw_manifest_by_id[data.get("addon_id")] = raw
    if set(project_builds) - {row27["addon_id"]}:
        raise CollectionRuntimeError("only the ID27 author project can be supplied as a project-build input")
    if len(project_builds) > 1:
        raise CollectionRuntimeError("one validated ID27 project build is supported in this qualified collection")
    project_report: dict[str, Any] | None = None
    project_family_files: list[tuple[str, Path, str]] = []
    project_root: Path | None = None
    if project_builds:
        project_root, project_family_files, project_report = _load_project_build(
            row27["addon_id"], manifest_by_id[row27["addon_id"]],
            raw_manifest_by_id[row27["addon_id"]], row27,
            project_builds[row27["addon_id"]])

    # The reference plan is a byte-level regression, while collection identity
    # and resources are generated from the caller's manifest files.
    profile_seed = _sha(plan_bytes)[:12]
    parent_profile = f"r5v-j3b-collection-parent-{profile_seed}"
    profile = f"r5v-j3b-collection-j2-{profile_seed}"
    source_bytes = source.read_bytes()
    record = _record_for_id27(row27, parent_profile)
    ai_modes = tuple(native for native, key in MODE_KEYS.items()
                     if row27["ai_eligibility"].get(key, {}).get("enabled") is True)
    generated_candidate, i0_manifest = i0.make_candidate(
        source_bytes,
        id27_record=record,
        results_label=row27["results"]["display_name"],
        profile=parent_profile,
        phase="R5V-J.3-B collection-generated ID27/T2 native integration",
        unlock_oracle_id=row27["unlock"]["stock_vehicle_id"],
        audio_profile_id=row27["audio"]["stock_audio_profile_id"],
        ai_pool_modes=ai_modes,
    )
    if i0_manifest.get("profiles", [{}, {}])[1].get("race_colour_rgba_bits") != [
            f"{value:08x}" for value in record.race_colour_rgba_bits]:
        raise CollectionRuntimeError("native VehicleRecord initializer does not match manifest race marker RGBA")
    if i0_manifest.get("profiles", [{}, {}])[1].get("name") != row27["identity"]["runtime_family"]:
        raise CollectionRuntimeError("native VehicleRecord runtime family differs from the addon collection")
    if _sha(plan_bytes) == addon_runtime.REFERENCE_PLAN_SHA256:
        reference_profile_path = addon_runtime.DEFAULT_OUTPUT / "runtime-profile.json"
        try:
            reference_profile = json.loads(reference_profile_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CollectionRuntimeError("the pinned J.1 reference runtime profile is unavailable") from exc
        requested_color = tuple(struct.unpack("<4I", bytes.fromhex(row27["race_colour_rgba_f32le_hex"])))
        if (reference_profile.get("addon_plan_sha256") != _sha(plan_bytes)
                or reference_profile.get("reconstructed_reference_file_sha256") != i0_manifest.get("patched_sha256")
                or record.race_colour_rgba_bits != requested_color):
            raise CollectionRuntimeError("reference-pair native operation regression differs from the qualified J.1 plan/image")

    try:
        native_manifest, native_ops, parent_image = addon_runtime._native_patch_artifacts(
            source_bytes, plan, generated_candidate=(generated_candidate, i0_manifest),
            expected_plan_sha256=_sha(plan_bytes), profile=parent_profile)
    except (addon_runtime.RuntimeIntegrationError, i0.CandidateError, Exception) as exc:
        # Preserve a concise public diagnostic while refusing any partially
        # emitted native operation set.
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise CollectionRuntimeError(f"collection native operations failed audited preimage/layout checks: {exc}") from exc

    temp_parent = Path(tempfile.mkdtemp(prefix=".j3b-native-parent-", dir=base.parent))
    try:
        (temp_parent / "native-patch-manifest.json").write_bytes(addon_runtime.canonical_json(native_manifest))
        (temp_parent / "native-patch-ops.rvp").write_bytes(native_ops)
        (temp_parent / "runtime-profile.json").write_bytes(addon_runtime.canonical_json({
            "profile": parent_profile,
            "status": "STATICALLY_VERIFIED_COLLECTION_PARENT",
            "addon_plan_sha256": _sha(plan_bytes),
            "native_patch_manifest_sha256": _sha(addon_runtime.canonical_json(native_manifest)),
            "native_patch_operations_sha256": _sha(native_ops),
            "reconstructed_reference_file_sha256": _sha(parent_image),
        }))
        try:
            j2_manifest, final_ops, final_profile, final_image, final_manifest_bytes = j2._j2_artifacts(
                source_bytes, temp_parent,
                expected_plan_sha256=_sha(plan_bytes), profile_name=profile,
                allow_generic_collection=True,
            )
        except (j2.ReentryBundleError, addon_runtime.RuntimeIntegrationError) as exc:
            raise CollectionRuntimeError(f"collection J.2 frontend reverse-mapper composition failed: {exc}") from exc
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)

    # Validate the class-local inverse explicitly. The retained J.2 instruction
    # stores T2/local7 at this+0x18 (0x14 + 4*class_id), not the T1 field.
    reverse = j2._verify_id27_reverse_mapper(final_image)
    if reverse.get("local_field_offset") != 0x18 or reverse.get("class_local_field_expected") != 0x18:
        raise CollectionRuntimeError("generated sparse ID27 mapper violates local_field_offset = 0x14 + 4*class_id")
    collection_inputs = {
        "schema_version": 1,
        "artifact_kind": "reproducible source-input record for collection runtime compilation",
        "retail_exe_sha256": exe_check["sha256"],
        "capabilities_sha256": _sha(cap_file.read_bytes()),
        "base_resource_package_manifest_sha256": _sha_file(base / i1_package.RUNTIME_MANIFEST_NAME),
        "addon_manifests": [
            {"addon_id": addon_id, "sha256": _sha(raw_manifest_by_id[addon_id]),
             "physical_id": next(row["physical_id"] for row in plan["addons"] if row["addon_id"] == addon_id)}
            for addon_id in sorted(raw_manifest_by_id)
        ],
        "id27_resource_source": project_report or {
            "addon_id": row27["addon_id"], "source_kind": "exact-qualified-I1-reference-package",
            "runtime_family": row27["identity"]["runtime_family"],
        },
    }
    resource_sources: dict[str, tuple[dict[str, Any], Path | bytes]] = {}
    resource_inventory, resource_report = _collection_resources(
        base_package=base, base_rows=base_rows, base_manifest=base_manifest,
        row27=row27, project_build=project_root,
        project_family_files=project_family_files,
        project_source_report=project_report,
        output_row_sources=resource_sources, project_report=project_report,
    )
    resource_index = addon_runtime._resource_index(resource_inventory["resources"])
    resource_manifest = {
        "schema_version": 1,
        "artifact_kind": "verified collection-specific external loose-resource root inventory",
        "status": "STAGED_STATIC_EXTERNAL_RESOURCE_ROOT",
        "profile": profile,
        "addon_plan_sha256": _sha(plan_bytes),
        "resource_count": len(resource_inventory["resources"]),
        "index_sha256": _sha(resource_index),
        "resources": resource_inventory["resources"],
        "runtime_state_paths": sorted(addon_runtime.RUNTIME_STATE_PATHS),
        "runtime_state_hashing": "excluded and preserved as user state",
        "root_resolution": {
            "intended_process_current_directory": "resource-root",
            "co-location_with_executable": False,
            "evidence": "same verified external loose-resource-root contract consumed by the J.1/J.2 launcher",
        },
        "original_installation_files_modified": False,
        "stock_resource_archive_modified": False,
        "replacement_executable_included": False,
    }
    resource_manifest_bytes = addon_runtime.canonical_json(resource_manifest)
    final_profile = json.loads(json.dumps(final_profile))
    final_profile.update({
        "profile": profile,
        "status": "READY_FOR_HUMAN_RUNTIME",
        "runtime_level": "STATICALLY_VERIFIED_J2_COLLECTION_BUNDLE_FOR_EXISTING_LAUNCHER",
        "retail_exe": {"sha256": addon_runtime.RETAIL_SHA256, "size": addon_runtime.RETAIL_SIZE,
                        "machine": "I386", "image_base": addon_runtime.IMAGE_BASE, "relocations": "STRIPPED"},
        "addon_plan_sha256": _sha(plan_bytes),
        "native_patch_manifest_sha256": _sha(final_manifest_bytes),
        "native_patch_operations_sha256": _sha(final_ops),
        "resource_manifest_sha256": _sha(resource_manifest_bytes),
        "resource_index_sha256": _sha(resource_index),
        "resource_count": len(resource_inventory["resources"]),
        "resource_root": "resource-root",
        "reconstructed_reference_file_sha256": _sha(final_image),
        "reconstructed_reference_file_size": len(final_image),
        "reference_executable_written_to_disk": False,
        "runtime_installable": False,
        "runtime_qualified": False,
        "identity_runtime_qualified": row27["identity"]["runtime_family"] == "R5VQualifier",
        "physical_slots_runtime_qualified": [26, 27],
        "unresolved_runtime_gates": [
            "human runtime qualification of this exact compiled collection and external launcher",
            "new ID27 runtime family identity remains unqualified until its complete player-race test",
        ] if row27["identity"]["runtime_family"] != "R5VQualifier" else [
            "human runtime qualification of this exact production compiler bundle",
        ],
    })
    runtime_artifact = {
        "schema_version": 1,
        "artifact_kind": RUNTIME_PROFILE_KIND,
        "status": "READY_FOR_HUMAN_RUNTIME",
        "offline_plan_status": "OFFLINE_PLAN_ONLY",
        "native_integration_status": "STATICALLY_VERIFIED_EXACT_RETAIL_OPERATIONS",
        "resource_staging_status": "STATICALLY_VERIFIED_COLLECTION_INVENTORY",
        "launcher_compatibility": "EXISTING_J1_J2_EXTERNAL_LAUNCHER_FORMAT",
        "runtime_qualified": False,
        "profile": profile,
        "supported_layout": SUPPORT_LAYOUT,
        "physical_addon_ids": [26, 27],
        "runtime_family_id27": row27["identity"]["runtime_family"],
        "new_identity_runtime_qualified": row27["identity"]["runtime_family"] == "R5VQualifier",
        "addon_plan_sha256": _sha(plan_bytes),
        "native_patch_manifest_sha256": _sha(final_manifest_bytes),
        "native_patch_operations_sha256": _sha(final_ops),
        "resource_manifest_sha256": _sha(resource_manifest_bytes),
        "resource_index_sha256": _sha(resource_index),
        "resource_count": len(resource_inventory["resources"]),
        "reconstructed_reference_image_sha256": _sha(final_image),
        "vehicle_select_reentry": reverse,
        "removal_policy": "disable by launching pristine MRallye.exe directly; delete only this external bundle after game exit; never delete saves or stock resources",
        "original_executable_written": False,
        "stock_data_sma_written": False,
    }
    expected_files = {
        "addon-plan.json": plan_bytes,
        "frontend-overlay.plan.json": artifacts["frontend-overlay.plan.json"],
        "offline-resource-inventory.json": artifacts["resource-inventory.json"],
        "resource-inventory.json": addon_runtime.canonical_json(resource_inventory),
        "native-patch-manifest.json": final_manifest_bytes,
        "native-patch-ops.rvp": final_ops,
        "resource-index.tsv": resource_index,
        "resource-manifest.json": resource_manifest_bytes,
        "runtime-profile.json": addon_runtime.canonical_json(final_profile),
        "runtime-artifact.json": addon_runtime.canonical_json(runtime_artifact),
        "collection-inputs.json": addon_runtime.canonical_json(collection_inputs),
    }
    return {
        "plan": plan, "artifacts": artifacts, "row26": row26, "row27": row27,
        "retail_exe": source, "base_package": base,
        "resource_sources": resource_sources, "resource_inventory": resource_inventory,
        "resource_report": resource_report,
        "expected_files": expected_files, "native_manifest": j2_manifest,
        "patch_operation_count": len(j2_manifest.get("operations", [])),
        "process_memory_operation_count": j2_manifest.get("process_memory_operation_count"),
        "profile": final_profile, "runtime_artifact": runtime_artifact,
    }


def _verify_tree(bundle: Path, context: dict[str, Any]) -> dict[str, Any]:
    expected_files: dict[str, bytes] = context["expected_files"]
    for relative, expected in expected_files.items():
        path = bundle / relative
        if not path.is_file() or path.is_symlink() or path.read_bytes() != expected:
            raise CollectionRuntimeError(f"runtime bundle artifact differs from deterministic rebuild: {relative}")
    root = bundle / "resource-root"
    if not root.is_dir() or root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise CollectionRuntimeError("runtime bundle resource-root is missing or link-backed")
    expected_rows = context["resource_inventory"]["resources"]
    expected_keys = {row["path"].casefold() for row in expected_rows}
    actual_keys: set[str] = set()
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            item = Path(current) / name
            if item.is_symlink() or getattr(item, "is_junction", lambda: False)():
                raise CollectionRuntimeError(f"runtime resource root contains a linked directory: {item.name}")
        for name in files:
            item = Path(current) / name
            if item.is_symlink():
                raise CollectionRuntimeError(f"runtime resource root contains a symlink: {item.name}")
            relative = item.relative_to(root).as_posix().casefold()
            if relative not in addon_runtime.RUNTIME_STATE_PATHS:
                actual_keys.add(relative)
    if actual_keys != expected_keys:
        raise CollectionRuntimeError(
            f"runtime resource file set differs; missing={sorted(expected_keys-actual_keys)}, "
            f"unexpected={sorted(actual_keys-expected_keys)}"
        )
    for row in expected_rows:
        path = _under(root, row["path"])
        if addon_runtime.is_user_editable_resource(row["path"]):
            addon_runtime.validate_user_editable_resource(path, row["path"])
            continue
        if (path.stat().st_size, _sha_file(path)) != (row["size"], row["sha256"]):
            raise CollectionRuntimeError(f"runtime resource hash/size mismatch: {row['path']}")
    top_expected = set(expected_files) | {"resource-root"}
    top_actual = {path.name for path in bundle.iterdir()}
    if top_actual != top_expected:
        raise CollectionRuntimeError(f"runtime bundle has unexpected top-level entries: {sorted(top_actual ^ top_expected)}")
    if (root / "MRallye.exe").exists():
        raise CollectionRuntimeError("runtime resource root must not contain MRallye.exe")
    return {
        "status": "PASS_STATIC_COLLECTION_RUNTIME_BUNDLE",
        "retail_exe_sha256": addon_runtime.RETAIL_SHA256,
        "addon_plan_sha256": _sha(expected_files["addon-plan.json"]),
        "native_patch_operation_count": context["patch_operation_count"],
        "process_memory_operation_count": context["process_memory_operation_count"],
        "native_patch_manifest_sha256": _sha(expected_files["native-patch-manifest.json"]),
        "native_patch_operations_sha256": _sha(expected_files["native-patch-ops.rvp"]),
        "resource_count": len(expected_rows),
        "resource_index_sha256": _sha(expected_files["resource-index.tsv"]),
        "resource_manifest_sha256": _sha(expected_files["resource-manifest.json"]),
        "reference_image_sha256": context["profile"]["reconstructed_reference_file_sha256"],
        "runtime_qualified": False,
        "original_executable_written": False,
    }


def prepare_bundle(*, manifest_paths: list[Path], project_builds: dict[str, Path] | None = None,
                   capabilities_path: Path = DEFAULT_CAPABILITIES,
                   retail_exe: Path = DEFAULT_RETAIL_EXE,
                   base_package: Path = DEFAULT_BASE_PACKAGE,
                   output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output = addon_runtime._under_research_output(Path(output))
    if output.exists():
        raise CollectionRuntimeError(f"refusing to overwrite existing runtime bundle: {output}")
    context = _compile_context(
        manifest_paths=manifest_paths, project_builds=project_builds or {},
        capabilities_path=capabilities_path, retail_exe=retail_exe, base_package=base_package,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        for relative, data in context["expected_files"].items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        resource_root = stage / "resource-root"
        for row in context["resource_inventory"]["resources"]:
            source_row, source = context["resource_sources"][row["path"].casefold()]
            if source_row != row:
                raise CollectionRuntimeError(f"resource source row changed during staging: {row['path']}")
            target = resource_root.joinpath(*PurePosixPath(row["path"]).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(source, bytes):
                target.write_bytes(source)
            else:
                shutil.copyfile(source, target)
            if (target.stat().st_size, _sha_file(target)) != (row["size"], row["sha256"]):
                raise CollectionRuntimeError(f"resource copy verification failed: {row['path']}")
        verified = _verify_tree(stage, context)
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {**verified, "bundle": str(output),
            "runtime_family_id27": context["row27"]["identity"]["runtime_family"],
            "resource_composition": context["resource_report"],
            "status_boundary": context["runtime_artifact"]["status"]}


def verify_bundle(bundle: Path, *, manifest_paths: list[Path],
                  project_builds: dict[str, Path] | None = None,
                  capabilities_path: Path = DEFAULT_CAPABILITIES,
                  retail_exe: Path = DEFAULT_RETAIL_EXE,
                  base_package: Path = DEFAULT_BASE_PACKAGE) -> dict[str, Any]:
    bundle = _safe_root(Path(bundle), "runtime bundle")
    if not bundle.is_dir():
        raise CollectionRuntimeError("runtime bundle is not a directory")
    context = _compile_context(
        manifest_paths=manifest_paths, project_builds=project_builds or {},
        capabilities_path=capabilities_path, retail_exe=retail_exe, base_package=base_package,
    )
    result = _verify_tree(bundle, context)
    return {**result, "bundle": str(bundle),
            "runtime_family_id27": context["row27"]["identity"]["runtime_family"],
            "resource_composition": context["resource_report"]}


def build_collection_launcher(*, bundle: Path, manifest_paths: list[Path],
                              project_builds: dict[str, Path] | None = None,
                              capabilities_path: Path = DEFAULT_CAPABILITIES,
                              retail_exe: Path = DEFAULT_RETAIL_EXE,
                              base_package: Path = DEFAULT_BASE_PACKAGE,
                              output: Path) -> dict[str, Any]:
    def verifier() -> dict[str, Any]:
        return verify_bundle(bundle, manifest_paths=manifest_paths, project_builds=project_builds,
                             capabilities_path=capabilities_path, retail_exe=retail_exe,
                             base_package=base_package)
    return build_runtime_launcher.build_launcher(
        bundle=bundle, retail_exe=retail_exe, output=output,
        bundle_verifier=verifier,
    )


def _parse_project_builds(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise CollectionRuntimeError("--project-build must use ADDON_ID=PATH")
        addon_id, raw_path = value.split("=", 1)
        if not addon_id or not raw_path or addon_id in result:
            raise CollectionRuntimeError("--project-build contains an empty or duplicate addon ID")
        result[addon_id] = Path(raw_path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "verify", "launcher-build"):
        command = commands.add_parser(name)
        command.add_argument("bundle", nargs="?", type=Path)
        command.add_argument("--manifest", action="append", required=True, type=Path)
        command.add_argument("--project-build", action="append", default=[])
        command.add_argument("--capabilities", type=Path, default=DEFAULT_CAPABILITIES)
        command.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL_EXE)
        command.add_argument("--base-package", type=Path, default=DEFAULT_BASE_PACKAGE)
        command.add_argument("--output", type=Path)
        if name == "launcher-build":
            command.add_argument("--launcher-output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        projects = _parse_project_builds(args.project_build)
        if args.command == "prepare":
            if args.output is None:
                raise CollectionRuntimeError("prepare requires --output")
            result = prepare_bundle(
                manifest_paths=args.manifest, project_builds=projects,
                capabilities_path=args.capabilities, retail_exe=args.retail_exe,
                base_package=args.base_package, output=args.output,
            )
        elif args.command == "verify":
            if args.bundle is None:
                raise CollectionRuntimeError("verify requires a bundle path")
            result = verify_bundle(
                args.bundle, manifest_paths=args.manifest, project_builds=projects,
                capabilities_path=args.capabilities, retail_exe=args.retail_exe,
                base_package=args.base_package,
            )
        else:
            if args.bundle is None:
                raise CollectionRuntimeError("launcher-build requires a bundle path")
            result = build_collection_launcher(
                bundle=args.bundle, manifest_paths=args.manifest, project_builds=projects,
                capabilities_path=args.capabilities, retail_exe=args.retail_exe,
                base_package=args.base_package, output=args.launcher_output,
            )
    except (CollectionRuntimeError, addon_runtime.RuntimeIntegrationError,
            AddonValidationError, i0.CandidateError, i0.registry.PatchError,
            OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
