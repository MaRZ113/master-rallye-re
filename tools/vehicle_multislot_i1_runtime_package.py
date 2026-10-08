#!/usr/bin/env python3
"""Build and verify the local R5V-I.1 authored ID27 qualification package.

The package contains the deterministic ID27/T2 candidate, the qualified
VehicleSelect scene overlay, a copied Navara-derived but separately addressed
R5VQualifier DX/DXT family with one controlled body texture recolour, and full
vehicles/Modifications XML overlays with new R5VQualifier paths. It never
modifies Data.sma or source/corpus files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from typing import Any
import xml.etree.ElementTree as ET

try:
    import build_vehicle_multislot_i0 as i0
    import build_vehicle_multislot_i1 as i1
    import prepare_multislot_vehicle_select_overlay as overlay
    import vehicle_multislot_runtime_package as i0_package
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style imports for tests
    from tools import build_vehicle_multislot_i0 as i0
    from tools import build_vehicle_multislot_i1 as i1
    from tools import prepare_multislot_vehicle_select_overlay as overlay
    from tools import vehicle_multislot_runtime_package as i0_package
    from tools import patch_vehicle_registry_id26 as registry

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
from master_rallye.dxt import decode_rgba_pixels, encode_dxt_pixels, parse_dxt_bytes  # noqa: E402
from master_rallye.vehicle_packaging import read_sma_member  # noqa: E402

DEFAULT_H2_ROOT = PROJECT_ROOT / ".research-output/vehicles/ai/mode-aware-id26/closeout-verified-runtime-package"
DEFAULT_RETAIL_EXE = PROJECT_ROOT.parent / "corpora/retail/MRallye.exe"
DEFAULT_RETAIL_SCENE = PROJECT_ROOT.parent / "corpora/retail/Data.sma_unpacked/DataScene/FrontendScreens/VehicleSelect.xml"
DEFAULT_RETAIL_DATA = PROJECT_ROOT.parent / "corpora/retail/Data.sma_unpacked"
DEFAULT_CANDIDATE = i1.DEFAULT_OUTPUT
DEFAULT_PATCH_MANIFEST = i1.DEFAULT_MANIFEST
DEFAULT_PACKAGE = PROJECT_ROOT / ".research-output/vehicles/multislot/i1/runtime-package"

RUNTIME_MANIFEST_NAME = "r5v-i1-runtime-package.json"
PATCH_MANIFEST_NAME = "MRallye.i1.patch-manifest.json"
OVERLAY_MANIFEST_NAME = "VehicleSelect.i1.manifest.json"
OVERLAY_RELATIVE = "DataScene/FrontendScreens/VehicleSelect.xml"
VEHICLE_NAME = i1.RUNTIME_FAMILY
VEHICLE_RELATIVE = f"DataGx/Vehicles/{VEHICLE_NAME}"
VEHICLES_XML_RELATIVE = "DataGame/vehicles.xml"
MODIFICATIONS_XML_RELATIVE = "DataGame/Modifications.xml"
SOURCE_VEHICLE_DIR = Path("DataGx/Vehicles/Navara")
BASE_FAMILY = "Navara"
PAINT_TEXTURE = "paintjeep-tga.dxt"
PAINT_SOURCE_SHA256 = "1d25b132568e8f30ae7ec8049de2289ec95727051df18868693fb251f5f9436c"
PAINT_RGBA = (255, 64, 210, 255)
EXPECTED_DX_SHA256 = {
    "car.dx": "2d3727f5bcd889ba38891276111c53f9c4d67cee1f5ece13de374a8235690655",
    "complete.dx": "0edab556302273db41736993cdd041e73b1894419a623526c91f458b5fcfdc2e",
    "wheel.dx": "2ae0c70a1912edfa8c628038541305132bf6843a00d33ce8761f351f17b72e08",
}
EXPECTED_H2_PROFILE = i0_package.EXPECTED_H2_PROFILE
EXPECTED_H2_SHA256 = i0.H2_SHA256


class PackageError(ValueError):
    """Refuse an unsupported source, malformed package, or unsafe output."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _safe_relative(raw: str) -> Path:
    normalized = raw.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (not normalized or pure.is_absolute() or ":" in normalized
            or any(part in {"", ".", ".."} for part in normalized.split("/"))):
        raise PackageError(f"unsafe relative package path: {raw!r}")
    return Path(*pure.parts)


def _inside(root: Path, relative: str) -> Path:
    root = Path(os.path.abspath(root))
    if not root.is_dir() or root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise PackageError("package root is missing or link-backed")
    path = root
    for part in _safe_relative(relative).parts:
        path = path / part
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise PackageError(f"package member path contains a link: {relative}")
    if not path.is_file():
        raise PackageError(f"package member is not a regular file: {relative}")
    return path


def _validate_output(path: Path) -> Path:
    resolved = i0_package._absolute_without_links(path, "I.1 runtime package")
    if not registry._is_research_output(resolved):
        raise PackageError("I.1 output must be inside ignored research-output")
    return resolved


def _source_exe(path: Path) -> Path:
    # Windows realpath resolution for the protected corpus EXE can deny
    # FILE_READ_ATTRIBUTES even though stat/open/read are allowed. Keep the
    # literal absolute path and rely on pinned SHA/size verification.
    resolved = Path(os.path.abspath(path))
    if not resolved.is_file():
        raise PackageError(f"retail executable source is missing: {resolved}")
    return resolved


def _record(path: Path, relative: str, role: str) -> dict[str, Any]:
    return {"path": relative.replace("\\", "/"), "size": path.stat().st_size,
            "sha256": sha256_file(path), "role": role}


def _retail_member(data_sma: Path, member: str, expected_file: Path) -> bytes:
    archive_bytes = read_sma_member(data_sma, member)
    loose_bytes = expected_file.read_bytes()
    if archive_bytes != loose_bytes:
        raise PackageError(f"unpacked corpus differs from exact H.2 Data.sma member: {member}")
    return archive_bytes


def _family_xml_overlay(source: bytes, *, source_label: str) -> tuple[bytes, int]:
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise PackageError(f"invalid {source_label} XML source") from exc
    original_values = [node for node in root.iter("Value")
                       if (node.get("Name") or "").startswith(f"Vehicles/{BASE_FAMILY}/")]
    existing = [node.get("Name", "") for node in root.iter("Value")
                if (node.get("Name") or "").startswith(f"Vehicles/{VEHICLE_NAME}/")]
    if not original_values or existing:
        raise PackageError(f"{source_label} lacks a clean, non-empty Navara donor namespace")

    line_pattern = re.compile(rb'<Value\s+Name="Vehicles/Navara/[^"]+"[^>]*/>')
    source_lines = source.splitlines()
    clones: list[bytes] = []
    for line in source_lines:
        if b'<Value ' not in line or b'Name="Vehicles/Navara/' not in line:
            continue
        match = line_pattern.search(line)
        if match is None:
            raise PackageError(f"unrecognized {source_label} Navara Value serialization")
        clones.append(line.replace(b'Name="Vehicles/Navara/',
                                   f'Name="Vehicles/{VEHICLE_NAME}/'.encode("ascii"), 1))
    if len(clones) != len(original_values):
        raise PackageError(
            f"{source_label} Navara clone count differs between XML and serialized source: "
            f"{len(original_values)} vs {len(clones)}")
    marker = b"</Broker>"
    if source.count(marker) != 1:
        raise PackageError(f"{source_label} must have exactly one Broker close marker")
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    insertion = newline + newline.join(clones) + newline
    output = source.replace(marker, insertion + marker, 1)
    try:
        out_root = ET.fromstring(output)
    except ET.ParseError as exc:
        raise PackageError(f"generated {source_label} overlay is not valid XML") from exc
    out_values = list(out_root.iter("Value"))
    if len(out_values) != sum(1 for _ in root.iter("Value")) + len(clones):
        raise PackageError(f"generated {source_label} overlay changed the source Value count")
    output_names = [node.get("Name", "") for node in out_values]
    if len(output_names) != len(set(output_names)):
        raise PackageError(f"generated {source_label} overlay contains duplicate Broker paths")
    cloned_values = [node for node in out_values
                     if (node.get("Name") or "").startswith(f"Vehicles/{VEHICLE_NAME}/")]
    if len(cloned_values) != len(original_values):
        raise PackageError(f"generated {source_label} overlay lost cloned family values")
    for original, clone in zip(original_values, cloned_values):
        expected_attrs = dict(original.attrib)
        expected_attrs["Name"] = expected_attrs["Name"].replace(
            f"Vehicles/{BASE_FAMILY}/", f"Vehicles/{VEHICLE_NAME}/", 1)
        if clone.attrib != expected_attrs:
            raise PackageError(f"generated {source_label} family value differs from its donor")
    return output, len(clones)


def _build_payloads(*, data_sma: Path, retail_data_root: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    source_dir = retail_data_root / "DataGx" / "Vehicles" / BASE_FAMILY
    if not source_dir.is_dir():
        raise PackageError(f"qualified retail Navara asset folder is missing: {source_dir}")
    source_files = sorted((path for path in source_dir.iterdir()
                           if path.is_file() and path.suffix.casefold() in {".dx", ".dxt"}),
                          key=lambda path: path.name.casefold())
    source_names = {path.name.casefold() for path in source_files}
    required = {"car.dx", "complete.dx", "wheel.dx", PAINT_TEXTURE.casefold()}
    if not required <= source_names:
        raise PackageError(f"qualified Navara package lacks required resources: {sorted(required-source_names)}")

    payloads: dict[str, bytes] = {}
    source_asset_records: list[dict[str, Any]] = []
    for source_path in source_files:
        relative_member = f"{SOURCE_VEHICLE_DIR.as_posix()}/{source_path.name}"
        source = _retail_member(data_sma, relative_member, source_path)
        if source_path.suffix.casefold() == ".dx" and b"Navara" in source:
            raise PackageError(f"compiled model embeds donor-family routing bytes: {source_path.name}")
        output = source
        if source_path.name.casefold() == PAINT_TEXTURE.casefold():
            if sha256(source) != PAINT_SOURCE_SHA256:
                raise PackageError("Navara body paint DXT does not match the qualified authoring source")
            texture = parse_dxt_bytes(source, source_path.name)
            rgba = decode_rgba_pixels(texture)
            recolored = bytes(PAINT_RGBA) * (texture.width * texture.height)
            if rgba == recolored:
                raise PackageError("body texture already has the I.1 qualifier color")
            output = encode_dxt_pixels(texture, recolored, texture.width, texture.height)
            rebuilt = parse_dxt_bytes(output, f"{VEHICLE_NAME}/{source_path.name}")
            if rebuilt.header != texture.header or (rebuilt.width, rebuilt.height) != (texture.width, texture.height):
                raise PackageError("body DXT recolor changed its header or dimensions")
            if decode_rgba_pixels(rebuilt) != recolored:
                raise PackageError("body DXT recolor did not round-trip exactly")
        relative_output = f"{VEHICLE_RELATIVE}/{source_path.name}"
        payloads[relative_output] = output
        source_asset_records.append({
            "source_member": relative_member,
            "source_sha256": sha256(source),
            "path": relative_output,
            "size": len(output),
            "sha256": sha256(output),
            "modified": source_path.name.casefold() == PAINT_TEXTURE.casefold(),
        })

    # Verify every authoring sidecar texture reference resolves in the copied
    # compiled runtime package; sidecars themselves are not runtime resources.
    expected_dxt: set[str] = set()
    for sidecar_name in ("car.txt", "complete.txt", "wheel.txt"):
        sidecar = source_dir / sidecar_name
        if not sidecar.is_file():
            raise PackageError(f"Navara authoring evidence sidecar is missing: {sidecar_name}")
        text = sidecar.read_text(encoding="latin-1")
        expected_dxt.update((Path(name.replace("\\", "/")).stem + "-tga.dxt").casefold()
                            for name in re.findall(r"Name\[[^\]]*[/\\]([^/\\]+\.tga)\]", text, re.I))
    payload_paths = {path.casefold() for path in payloads}
    absent = sorted(name for name in expected_dxt
                    if f"{VEHICLE_RELATIVE}/{name}".casefold() not in payload_paths)
    if absent:
        raise PackageError(f"Navara-derived runtime payload is missing referenced DXT files: {absent}")
    if PAINT_TEXTURE.casefold() not in expected_dxt:
        raise PackageError("the selected qualifier body texture is not referenced by the authored model sidecars")

    data_game = retail_data_root / "DataGame"
    vehicles_xml_raw = _retail_member(data_sma, "DataGame/vehicles.xml", data_game / "vehicles.xml")
    mods_xml_raw = _retail_member(data_sma, "DataGame/Modifications.xml", data_game / "Modifications.xml")
    vehicles_xml, physics_count = _family_xml_overlay(vehicles_xml_raw, source_label="vehicles.xml")
    modifications_xml, modification_count = _family_xml_overlay(mods_xml_raw, source_label="Modifications.xml")
    payloads[VEHICLES_XML_RELATIVE] = vehicles_xml
    payloads[MODIFICATIONS_XML_RELATIVE] = modifications_xml

    metadata = {
        "source_family": BASE_FAMILY,
        "source_physical_id": 7,
        "source_archive": "Data.sma",
        "source_vehicle_config_sha256": sha256(vehicles_xml_raw),
        "source_modifications_config_sha256": sha256(mods_xml_raw),
        "runtime_family": VEHICLE_NAME,
        "runtime_asset_directory": VEHICLE_RELATIVE,
        "asset_files": source_asset_records,
        "asset_file_count": len(source_asset_records),
        "required_models": ["car.dx", "complete.dx", "wheel.dx"],
        "authoring_sidecars_used_for_reference_audit": ["car.txt", "complete.txt", "wheel.txt"],
        "sidecars_in_runtime_package": False,
        "gxm_gxi_in_runtime_package": False,
        "body_visual_canary": {
            "path": f"{VEHICLE_RELATIVE}/{PAINT_TEXTURE}",
            "source_sha256": PAINT_SOURCE_SHA256,
            "output_sha256": sha256(payloads[f"{VEHICLE_RELATIVE}/{PAINT_TEXTURE}"]),
            "rgba": list(PAINT_RGBA),
            "dimensions": [16, 16],
            "header_preserved": True,
            "source_material": "car.txt Material [jeep], Texture [0] paintjeep.tga",
        },
        "physics": {
            "overlay_path": VEHICLES_XML_RELATIVE,
            "family_path_prefix": f"Vehicles/{VEHICLE_NAME}/",
            "source_family_path_prefix": "Vehicles/Navara/",
            "values_cloned": physics_count,
            "semantic_delta": False,
            "collision": "donor-derived from unchanged Navara car.dx",
        },
        "player_modifications": {
            "overlay_path": MODIFICATIONS_XML_RELATIVE,
            "family_path_prefix": f"Vehicles/{VEHICLE_NAME}/",
            "source_family_path_prefix": "Vehicles/Navara/",
            "values_cloned": modification_count,
        },
    }
    return payloads, metadata


def _verify_h2(root: Path) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    try:
        return i0_package.verify_h2_source(root)
    except (i0_package.PackageError, OSError, ValueError, KeyError, TypeError) as exc:
        raise PackageError(f"H.2 resource root verification failed: {exc}") from exc


def _verify_candidate(retail_exe: Path, candidate: Path, manifest_path: Path) -> dict[str, Any]:
    try:
        manifest = i1.verify_existing(retail_exe, candidate, manifest_path)
    except (i1.CandidateError, i0.CandidateError, registry.PatchError,
            OSError, ValueError, KeyError, TypeError) as exc:
        raise PackageError(f"I.1 candidate verification failed: {exc}") from exc
    return manifest


def _build_package_manifest(*, h2_manifest: dict[str, Any], h2_manifest_bytes: bytes,
                            h2_resources: list[dict[str, Any]], candidate_manifest: dict[str, Any],
                            candidate: Path, scene_path: Path, scene_manifest: dict[str, Any],
                            inventory: list[dict[str, Any]], payload_metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "phase": "R5V-I.1 authored independent T2 qualification vehicle",
        "status": "READY_FOR_HUMAN_RUNTIME",
        "profile": i1.PROFILE,
        "candidate": {
            "path": "MRallye.exe",
            "size": candidate.stat().st_size,
            "sha256": sha256_file(candidate),
            "patch_manifest_path": PATCH_MANIFEST_NAME,
            "patch_manifest_sha256": sha256(_json_bytes(candidate_manifest)),
        },
        "source": {
            "retail_exe_sha256": i0.RETAIL_SHA256,
            "h2_candidate_sha256": EXPECTED_H2_SHA256,
            "h2_profile": EXPECTED_H2_PROFILE,
            "h2_package_manifest_sha256": sha256(h2_manifest_bytes),
            "h2_resource_count": len(h2_resources),
            "h2_resource_inventory_sha256": sha256(_json_bytes(h2_resources)),
        },
        "vehicle_select_scene": {
            "path": OVERLAY_RELATIVE,
            "sha256": sha256_file(scene_path),
            "manifest_path": OVERLAY_MANIFEST_NAME,
            "manifest_sha256": sha256(_json_bytes(scene_manifest)),
            "base_profile": "R5V-I.0 qualified T2_Car8 scene",
        },
        "id27": {
            "physical_id": 27,
            "class": 1,
            "class_name": "T2",
            "local_index": 7,
            "internal_name": VEHICLE_NAME,
            "runtime_family": VEHICLE_NAME,
            "model_family": VEHICLE_NAME,
            "wheel_family": VEHICLE_NAME,
            "physics_family": f"Vehicles/{VEHICLE_NAME}",
            "display": {
                "manufacturer": i1.DISPLAY_MANUFACTURER,
                "model": i1.DISPLAY_MODEL,
                "combined": i1.DISPLAY_COMBINED,
                "results": i1.RESULTS_LABEL,
            },
            "unlock_oracle_id": 10,
            "unlock_path": "Progress/UnlockedCars/T2CupCar1",
            "audio_profile_id": 7,
            "ai_pools_unchanged": True,
            "native_driver_id_changed": False,
            "details": payload_metadata,
        },
        "resource_inventory": inventory,
        "omitted_state": ["PlayerState.xml", "PlayerState.xml#", "save files", "raw captures", "screenshots"],
        "runtime_boundary": {
            "participant_count_changed": False,
            "randomizer_present": False,
            "id28_present": False,
            "player_or_ai_runtime_confirmed": False,
            "r5v_i_full_pass": False,
        },
    }


def _verify_package_tree(package: Path, manifest: dict[str, Any]) -> None:
    package = Path(os.path.abspath(package))
    if not package.is_dir():
        raise PackageError("I.1 runtime package directory is missing")
    if manifest.get("status") != "READY_FOR_HUMAN_RUNTIME" or manifest.get("profile") != i1.PROFILE:
        raise PackageError("runtime package is not the exact I.1 profile")
    candidate_meta = manifest.get("candidate", {})
    candidate = _inside(package, candidate_meta.get("path", ""))
    patch_manifest = _inside(package, candidate_meta.get("patch_manifest_path", ""))
    if candidate.stat().st_size != candidate_meta.get("size") or sha256_file(candidate) != candidate_meta.get("sha256"):
        raise PackageError("I.1 package executable hash/size mismatch")
    if sha256_file(patch_manifest) != candidate_meta.get("patch_manifest_sha256"):
        raise PackageError("I.1 patch manifest hash mismatch")
    scene_meta = manifest.get("vehicle_select_scene", {})
    scene = _inside(package, scene_meta.get("path", ""))
    scene_manifest = _inside(package, scene_meta.get("manifest_path", ""))
    if sha256_file(scene) != scene_meta.get("sha256"):
        raise PackageError("I.1 VehicleSelect scene hash mismatch")
    if sha256_file(scene_manifest) != scene_meta.get("manifest_sha256"):
        raise PackageError("I.1 VehicleSelect manifest hash mismatch")

    id27 = manifest.get("id27", {})
    expected = (27, 1, 7, VEHICLE_NAME, f"Vehicles/{VEHICLE_NAME}")
    actual = (id27.get("physical_id"), id27.get("class"), id27.get("local_index"),
              id27.get("runtime_family"), id27.get("physics_family"))
    if actual != expected:
        raise PackageError("I.1 package changed physical ID27/T2-local7 identity")
    if id27.get("display", {}).get("results") != i1.RESULTS_LABEL:
        raise PackageError("I.1 package lost the qualifier Results label")

    resources = manifest.get("resource_inventory")
    if not isinstance(resources, list) or not resources:
        raise PackageError("I.1 resource inventory is missing")
    seen: set[str] = set()
    for item in resources:
        relative = item.get("path") if isinstance(item, dict) else None
        if not isinstance(relative, str):
            raise PackageError("I.1 resource record is malformed")
        key = relative.replace("\\", "/").casefold()
        if key in seen:
            raise PackageError(f"duplicate I.1 resource path: {relative}")
        seen.add(key)
        path = _inside(package, relative)
        if path.stat().st_size != item.get("size") or sha256_file(path) != item.get("sha256"):
            raise PackageError(f"I.1 resource hash/size mismatch: {relative}")
        if path.name.casefold() in {"playerstate.xml", "playerstate.xml#"}:
            raise PackageError("I.1 package must not carry user save state")

    family_files = sorted(path for path in seen if path.startswith((VEHICLE_RELATIVE + "/").casefold()))
    if not {f"{VEHICLE_RELATIVE}/car.dx".casefold(),
            f"{VEHICLE_RELATIVE}/complete.dx".casefold(),
            f"{VEHICLE_RELATIVE}/wheel.dx".casefold()} <= set(family_files):
        raise PackageError("I.1 package lacks the independent family model files")
    if f"{VEHICLE_RELATIVE}/{PAINT_TEXTURE}".casefold() not in family_files:
        raise PackageError("I.1 package lacks its recolored body DXT")
    if VEHICLES_XML_RELATIVE.casefold() not in seen or MODIFICATIONS_XML_RELATIVE.casefold() not in seen:
        raise PackageError("I.1 package lacks its full physics/player-modification XML overlays")
    for relative in ("DataGx/Vehicles/Navara/car.dx", "DataGx/Vehicles/Navara/complete.dx",
                    "DataGx/Vehicles/Navara/wheel.dx"):
        if relative.casefold() in seen:
            raise PackageError("I.1 package must route ID27 model/wheels through R5VQualifier, not loose Navara files")
    expected_tree = seen | {candidate_meta["path"].casefold(), patch_manifest.name.casefold(),
                            scene_meta["manifest_path"].casefold(), RUNTIME_MANIFEST_NAME.casefold()}
    actual_tree = {path.relative_to(package).as_posix().casefold()
                   for path in package.rglob("*") if path.is_file()}
    if actual_tree != expected_tree:
        raise PackageError(f"I.1 package file set differs; missing={sorted(expected_tree-actual_tree)}, "
                           f"extra={sorted(actual_tree-expected_tree)}")


def stage_package(*, h2_root: Path = DEFAULT_H2_ROOT,
                  retail_exe: Path = DEFAULT_RETAIL_EXE,
                  retail_scene: Path = DEFAULT_RETAIL_SCENE,
                  retail_data_root: Path = DEFAULT_RETAIL_DATA,
                  candidate: Path = DEFAULT_CANDIDATE,
                  patch_manifest: Path = DEFAULT_PATCH_MANIFEST,
                  output: Path = DEFAULT_PACKAGE) -> dict[str, Any]:
    output = _validate_output(output)
    if output.exists():
        raise PackageError("refusing to overwrite an existing I.1 runtime package")
    h2_root = i0_package._absolute_without_links(h2_root, "H.2 package")
    if not h2_root.is_dir():
        raise PackageError("H.2 package directory is missing")
    retail_exe, retail_scene = _source_exe(retail_exe), Path(os.path.abspath(retail_scene))
    retail_data_root = Path(os.path.abspath(retail_data_root))
    candidate = i1._absolute_without_links(candidate, "I.1 candidate")
    patch_manifest = i1._absolute_without_links(patch_manifest, "I.1 candidate manifest")
    if not retail_scene.is_file() or not retail_data_root.is_dir():
        raise PackageError("retail scene or data corpus is missing")
    if not candidate.is_file() or not patch_manifest.is_file():
        raise PackageError("I.1 candidate or patch manifest is missing")
    h2_manifest, h2_manifest_bytes, h2_resources = _verify_h2(h2_root)
    if h2_manifest.get("profile") != EXPECTED_H2_PROFILE:
        raise PackageError("unexpected H.2 parent profile")
    if h2_manifest.get("candidate", {}).get("sha256") != EXPECTED_H2_SHA256:
        raise PackageError("unexpected H.2 parent candidate SHA256")
    if h2_manifest.get("resource_root") != ".":
        raise PackageError("unsupported H.2 resource root layout")
    candidate_manifest = _verify_candidate(retail_exe, candidate, patch_manifest)
    if candidate_manifest.get("parent_candidate", {}).get("sha256") != EXPECTED_H2_SHA256:
        raise PackageError("I.1 candidate is not based on exact H.2")

    data_sma = i0_package._inside(h2_root, "Data.sma")
    payloads, payload_meta = _build_payloads(data_sma=data_sma, retail_data_root=retail_data_root)
    scene_raw = retail_scene.read_bytes()
    scene_bytes, scene_base_manifest = overlay.build_overlay_bytes(scene_raw)
    scene_manifest = {
        **scene_base_manifest,
        "output_path": ".research-output/vehicles/multislot/i1/overlay/DataScene/FrontendScreens/VehicleSelect.xml",
        "manifest_path": ".research-output/vehicles/multislot/i1/overlay/manifest.json",
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=output.name + ".staging-", dir=output.parent))
    try:
        inventory: list[dict[str, Any]] = []
        for entry in h2_resources:
            relative = entry["path"]
            destination = temporary / _safe_relative(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if relative == OVERLAY_RELATIVE:
                destination.write_bytes(scene_bytes)
                role = "qualified T2_Car8 VehicleSelect overlay"
            else:
                shutil.copy2(_inside(h2_root, relative), destination)
                role = "verified H.2 resource root"
            inventory.append(_record(destination, relative, role))

        for relative, data in payloads.items():
            destination = temporary / _safe_relative(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            role = ("Navara-derived independent R5VQualifier vehicle resource"
                    if relative.startswith(VEHICLE_RELATIVE + "/") else
                    "full stock XML plus appended independent R5VQualifier family")
            inventory.append(_record(destination, relative, role))

        shutil.copy2(candidate, temporary / "MRallye.exe")
        shutil.copy2(patch_manifest, temporary / PATCH_MANIFEST_NAME)
        (temporary / OVERLAY_MANIFEST_NAME).write_bytes(_json_bytes(scene_manifest))
        manifest = _build_package_manifest(
            h2_manifest=h2_manifest, h2_manifest_bytes=h2_manifest_bytes,
            h2_resources=h2_resources, candidate_manifest=candidate_manifest,
            candidate=temporary / "MRallye.exe",
            scene_path=temporary / OVERLAY_RELATIVE, scene_manifest=scene_manifest,
            inventory=sorted(inventory, key=lambda item: item["path"].casefold()),
            payload_metadata=payload_meta,
        )
        (temporary / RUNTIME_MANIFEST_NAME).write_bytes(_json_bytes(manifest))
        _verify_package_tree(temporary, manifest)
        os.replace(temporary, output)
    except Exception:
        temp_resolved = Path(os.path.abspath(temporary))
        output_parent = Path(os.path.abspath(output.parent))
        if (temp_resolved.parent == output_parent
                and temp_resolved.name.startswith(output.name + ".staging-")
                and registry._is_research_output(temp_resolved)):
            shutil.rmtree(temp_resolved)
        raise
    return verify_package(output, retail_exe=retail_exe, retail_scene=retail_scene,
                          retail_data_root=retail_data_root, h2_root=h2_root)


def verify_package(package: Path, *, h2_root: Path = DEFAULT_H2_ROOT,
                   retail_exe: Path = DEFAULT_RETAIL_EXE,
                   retail_scene: Path = DEFAULT_RETAIL_SCENE,
                   retail_data_root: Path = DEFAULT_RETAIL_DATA) -> dict[str, Any]:
    package = _validate_output(package)
    if not package.is_dir():
        raise PackageError(f"I.1 package is missing: {package}")
    h2_root = i0_package._absolute_without_links(h2_root, "H.2 package")
    if not h2_root.is_dir():
        raise PackageError("H.2 package directory is missing")
    retail_exe, retail_scene = _source_exe(retail_exe), Path(os.path.abspath(retail_scene))
    retail_data_root = Path(os.path.abspath(retail_data_root))
    if not retail_scene.is_file() or not retail_data_root.is_dir():
        raise PackageError("retail scene or data corpus is missing")
    manifest_path = package / RUNTIME_MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError("I.1 runtime package manifest is invalid") from exc
    _verify_package_tree(package, manifest)
    candidate_manifest = _verify_candidate(retail_exe, package / "MRallye.exe",
                                           package / PATCH_MANIFEST_NAME)
    expected_candidate, expected_manifest = i1.make_candidate(retail_exe.read_bytes())
    if (package / "MRallye.exe").read_bytes() != expected_candidate:
        raise PackageError("I.1 runtime EXE differs from deterministic build")
    if (package / PATCH_MANIFEST_NAME).read_bytes() != _json_bytes(expected_manifest):
        raise PackageError("I.1 runtime patch manifest differs from deterministic build")

    h2_manifest, h2_manifest_bytes, h2_resources = _verify_h2(h2_root)
    if manifest["source"].get("h2_package_manifest_sha256") != sha256(h2_manifest_bytes):
        raise PackageError("I.1 package references a different H.2 package manifest")
    data_sma = i0_package._inside(h2_root, "Data.sma")
    payloads, payload_meta = _build_payloads(data_sma=data_sma, retail_data_root=retail_data_root)
    if manifest.get("id27", {}).get("details") != payload_meta:
        raise PackageError("I.1 payload provenance differs from deterministic source rebuild")
    for relative, expected in payloads.items():
        if _inside(package, relative).read_bytes() != expected:
            raise PackageError(f"I.1 staged vehicle/config overlay differs from deterministic rebuild: {relative}")

    expected_scene, scene_meta = overlay.build_overlay_bytes(retail_scene.read_bytes())
    scene_manifest = {
        **scene_meta,
        "output_path": ".research-output/vehicles/multislot/i1/overlay/DataScene/FrontendScreens/VehicleSelect.xml",
        "manifest_path": ".research-output/vehicles/multislot/i1/overlay/manifest.json",
    }
    if (package / OVERLAY_RELATIVE).read_bytes() != expected_scene:
        raise PackageError("I.1 VehicleSelect scene differs from the deterministic overlay")
    if (package / OVERLAY_MANIFEST_NAME).read_bytes() != _json_bytes(scene_manifest):
        raise PackageError("I.1 VehicleSelect overlay manifest differs from deterministic provenance")

    expected_h2_paths = {item["path"].casefold() for item in h2_resources}
    expected_custom = {path.casefold() for path in payloads}
    actual_resource = {item["path"].casefold() for item in manifest["resource_inventory"]}
    if actual_resource != expected_h2_paths | expected_custom:
        raise PackageError("I.1 package resource inventory differs from H.2 plus authored family overlays")
    return {
        "status": "VERIFIED",
        "profile": manifest["profile"],
        "candidate_sha256": manifest["candidate"]["sha256"],
        "candidate_size": manifest["candidate"]["size"],
        "vehicle_family": VEHICLE_NAME,
        "asset_file_count": payload_meta["asset_file_count"],
        "physics_values": payload_meta["physics"]["values_cloned"],
        "modification_values": payload_meta["player_modifications"]["values_cloned"],
        "resource_count": len(manifest["resource_inventory"]),
        "package": str(package),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage")
    for command in (stage,):
        command.add_argument("--h2-root", type=Path, default=DEFAULT_H2_ROOT)
        command.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL_EXE)
        command.add_argument("--retail-scene", type=Path, default=DEFAULT_RETAIL_SCENE)
        command.add_argument("--retail-data-root", type=Path, default=DEFAULT_RETAIL_DATA)
        command.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
        command.add_argument("--patch-manifest", type=Path, default=DEFAULT_PATCH_MANIFEST)
    stage.add_argument("--output", type=Path, default=DEFAULT_PACKAGE)
    verify = sub.add_parser("verify")
    verify.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    verify.add_argument("--h2-root", type=Path, default=DEFAULT_H2_ROOT)
    verify.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL_EXE)
    verify.add_argument("--retail-scene", type=Path, default=DEFAULT_RETAIL_SCENE)
    verify.add_argument("--retail-data-root", type=Path, default=DEFAULT_RETAIL_DATA)
    args = parser.parse_args(argv)
    try:
        if args.command == "stage":
            result = stage_package(
                h2_root=args.h2_root, retail_exe=args.retail_exe,
                retail_scene=args.retail_scene, retail_data_root=args.retail_data_root,
                candidate=args.candidate, patch_manifest=args.patch_manifest, output=args.output)
        else:
            result = verify_package(
                args.package, h2_root=args.h2_root, retail_exe=args.retail_exe,
                retail_scene=args.retail_scene, retail_data_root=args.retail_data_root)
    except (PackageError, i0_package.PackageError, i1.CandidateError, i0.CandidateError,
            overlay.OverlayError, registry.PatchError, OSError, ValueError, TypeError,
            KeyError) as exc:
        parser.exit(2, f"R5V-I.1 runtime package refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
