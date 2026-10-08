#!/usr/bin/env python3
"""Stage and verify the deterministic R5V-I.0 research runtime package.

The package is composed from the already qualified H.2 resource root, the
hash-pinned I.0 executable and the generated T2_Car8 overlay. It is local,
ignored research output and contains no profile/save state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Any

try:
    import build_vehicle_multislot_i0 as i0
    import prepare_multislot_vehicle_select_overlay as overlay
    import patch_vehicle_registry_id26 as registry
except ImportError:  # pragma: no cover - package-style imports for tests
    from tools import build_vehicle_multislot_i0 as i0
    from tools import prepare_multislot_vehicle_select_overlay as overlay
    from tools import patch_vehicle_registry_id26 as registry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_H2_ROOT = PROJECT_ROOT / ".research-output/vehicles/ai/mode-aware-id26/closeout-verified-runtime-package"
DEFAULT_RETAIL_EXE = PROJECT_ROOT.parent / "corpora/retail/MRallye.exe"
DEFAULT_RETAIL_SCENE = PROJECT_ROOT.parent / "corpora/retail/Data.sma_unpacked/DataScene/FrontendScreens/VehicleSelect.xml"
DEFAULT_CANDIDATE = PROJECT_ROOT / ".research-output/vehicles/multislot/i0/candidate/MRallye.exe"
DEFAULT_PATCH_MANIFEST = PROJECT_ROOT / ".research-output/vehicles/multislot/i0/candidate/patch-manifest.json"
DEFAULT_OVERLAY = PROJECT_ROOT / ".research-output/vehicles/multislot/i0/overlay/DataScene/FrontendScreens/VehicleSelect.xml"
DEFAULT_OVERLAY_MANIFEST = PROJECT_ROOT / ".research-output/vehicles/multislot/i0/overlay/manifest.json"
DEFAULT_PACKAGE = PROJECT_ROOT / ".research-output/vehicles/multislot/i0/runtime-package"

RUNTIME_MANIFEST_NAME = "r5v-i0-runtime-package.json"
PATCH_MANIFEST_NAME = "MRallye.i0.patch-manifest.json"
OVERLAY_MANIFEST_NAME = "VehicleSelect.i0.manifest.json"
OVERLAY_ARTIFACT_RELATIVE = ".research-output/vehicles/multislot/i0/overlay/DataScene/FrontendScreens/VehicleSelect.xml"
OVERLAY_MANIFEST_RELATIVE = ".research-output/vehicles/multislot/i0/overlay/manifest.json"
EXPECTED_H2_SHA256 = i0.H2_SHA256
EXPECTED_H2_PROFILE = "mode-aware-natural-t1-id26"
EXPECTED_H2_SCENE_SHA256 = overlay.G1_OVERLAY_SHA256
EXPECTED_I0_PROFILE = i0.PROFILE
EXPECTED_ID27_ROLE = "SLOT PROOF / DONOR; NOT A REAL SECOND ADDON"


class PackageError(ValueError):
    """Refuse malformed inputs, unverified components, or unsafe outputs."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    with path.open("wb") as stream:
        stream.write(_json_bytes(value))


def _safe_relative(raw: str) -> Path:
    normalized = raw.replace("\\", "/")
    pure = PurePosixPath(normalized)
    raw_parts = normalized.split("/")
    if (not normalized or pure.is_absolute() or ":" in normalized
            or any(part in {"", ".", ".."} for part in raw_parts)):
        raise PackageError(f"unsafe package-relative path: {raw!r}")
    return Path(*pure.parts)


def _inside(root: Path, relative: str) -> Path:
    root = Path(os.path.abspath(root))
    if not root.is_dir() or root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise PackageError("package root is missing or link-backed")
    candidate = root
    for part in _safe_relative(relative).parts:
        candidate = candidate / part
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            raise PackageError(f"package path contains a link: {relative!r}")
    if not candidate.is_file():
        raise PackageError(f"package resource is not a regular file: {relative!r}")
    return candidate


def _load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PackageError(f"invalid JSON metadata: {path}") from exc
    if not isinstance(value, dict):
        raise PackageError(f"JSON metadata must be an object: {path}")
    return value, raw


def _entry(path: Path, relative: str, role: str) -> dict[str, Any]:
    return {
        "path": relative.replace("\\", "/"),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
        "role": role,
    }


def _absolute_without_links(path: Path, label: str) -> Path:
    """Use a lexical absolute path without allowing symlink/junction traversal."""
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise PackageError(f"{label} path contains a symlink or junction: {current}")
    return absolute


def _validate_output_directory(path: Path) -> Path:
    resolved = _absolute_without_links(path, "runtime package")
    if not registry._is_research_output(resolved):
        raise PackageError("runtime package output must be inside ignored research-output")
    return resolved


def verify_h2_source(root: Path) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    root = _absolute_without_links(root, "H.2 package")
    if not root.is_dir():
        raise PackageError(f"H.2 package directory is missing: {root}")
    manifest_path = root / "hardened-runtime-package.json"
    manifest, manifest_bytes = _load_json(manifest_path)
    candidate = manifest.get("candidate", {})
    if (manifest.get("status") != "R5V_H2_MODE_AWARE_T1_RUNTIME_PACKAGE_READY_FOR_HUMAN"
            or manifest.get("profile") != EXPECTED_H2_PROFILE
            or candidate.get("sha256") != EXPECTED_H2_SHA256):
        raise PackageError("unsupported H.2 runtime package identity")
    candidate_path = _inside(root, candidate.get("path", ""))
    if candidate_path.stat().st_size != candidate.get("size") or sha256_file(candidate_path) != EXPECTED_H2_SHA256:
        raise PackageError("H.2 executable does not match its pinned profile")

    resources = manifest.get("resources")
    if not isinstance(resources, list) or not resources:
        raise PackageError("H.2 package has no resource inventory")
    seen: set[str] = set()
    verified: list[dict[str, Any]] = []
    for record in resources:
        if not isinstance(record, dict):
            raise PackageError("H.2 resource entry is malformed")
        relative = record.get("path")
        if not isinstance(relative, str):
            raise PackageError("H.2 resource path is malformed")
        key = relative.replace("\\", "/").casefold()
        if key in seen:
            raise PackageError(f"duplicate H.2 resource path: {relative}")
        seen.add(key)
        path = _inside(root, relative)
        size, digest = record.get("size"), record.get("sha256")
        if path.stat().st_size != size or sha256_file(path) != digest:
            raise PackageError(f"H.2 resource hash/size mismatch: {relative}")
        if Path(relative).name.casefold() in {"playerstate.xml", "playerstate.xml#"}:
            raise PackageError("H.2 source package unexpectedly contains player state")
        verified.append({"path": relative.replace("\\", "/"), "size": size, "sha256": digest})

    scene = manifest.get("vehicle_select_scene", {})
    if (scene.get("path") != "DataScene/FrontendScreens/VehicleSelect.xml"
            or scene.get("sha256") != EXPECTED_H2_SCENE_SHA256):
        raise PackageError("H.2 resource root does not pin the qualified G.1 VehicleSelect scene")
    scene_entry = next((item for item in verified if item["path"] == scene["path"]), None)
    if scene_entry is None or scene_entry["sha256"] != EXPECTED_H2_SCENE_SHA256:
        raise PackageError("qualified H.2 VehicleSelect scene is absent from the resource inventory")
    if manifest.get("resource_root") != ".":
        raise PackageError("unsupported H.2 resource root layout")

    expected_files = seen | {
        candidate.get("path", "").replace("\\", "/").casefold(),
        "hardened-runtime-package.json",
    }
    actual_files = {
        path.relative_to(root).as_posix().casefold()
        for path in root.rglob("*") if path.is_file()
    }
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        extra = sorted(actual_files - expected_files)
        raise PackageError(f"H.2 source tree differs from its exact inventory; missing={missing}, extra={extra}")
    return manifest, manifest_bytes, verified


def _verify_component_builds(retail_exe: Path, retail_scene: Path,
                             candidate: Path, patch_manifest: Path,
                             scene_overlay: Path, overlay_manifest: Path
                             ) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        candidate_manifest = i0.verify_existing(retail_exe, candidate, patch_manifest)
        expected_scene, overlay_base = overlay.build_overlay_bytes(retail_scene.read_bytes())
        overlay_manifest_value, overlay_manifest_bytes = _load_json(overlay_manifest)
    except (i0.CandidateError, overlay.OverlayError, OSError, ValueError,
            KeyError, TypeError) as exc:
        raise PackageError(f"I.0 executable or overlay verification failed: {exc}") from exc
    if candidate_manifest.get("patched_sha256") != sha256_file(candidate):
        raise PackageError("verified candidate hash does not match the executable file")
    if candidate_manifest.get("profile") != EXPECTED_I0_PROFILE:
        raise PackageError("unsupported I.0 executable profile")
    if scene_overlay.read_bytes() != expected_scene:
        raise PackageError("VehicleSelect overlay differs from deterministic retail rebuild")
    expected_overlay_manifest = {
        **overlay_base,
        "output_path": OVERLAY_ARTIFACT_RELATIVE,
        "manifest_path": OVERLAY_MANIFEST_RELATIVE,
    }
    if overlay_manifest_bytes != _json_bytes(expected_overlay_manifest):
        raise PackageError("VehicleSelect overlay manifest differs from deterministic artifact provenance")
    if overlay_manifest_value.get("output_sha256") != sha256_file(scene_overlay):
        raise PackageError("verified VehicleSelect manifest does not describe the overlay output")
    return candidate_manifest, overlay_manifest_value


def _build_runtime_manifest(*, h2_manifest: dict[str, Any], h2_manifest_bytes: bytes,
                            h2_resources: list[dict[str, Any]],
                            candidate_manifest: dict[str, Any], candidate: Path,
                            scene_overlay: Path, overlay_manifest: dict[str, Any],
                            copied_resources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "phase": "R5V-I.0 second sparse vehicle slot / T2 local7",
        "status": "READY_FOR_HUMAN_RUNTIME",
        "profile": EXPECTED_I0_PROFILE,
        "candidate": {
            "path": "MRallye.exe",
            "size": candidate.stat().st_size,
            "sha256": sha256_file(candidate),
            "patch_manifest_path": PATCH_MANIFEST_NAME,
            "patch_manifest_sha256": hashlib.sha256(_json_bytes(candidate_manifest)).hexdigest(),
        },
        "source": {
            "retail_sha256": i0.RETAIL_SHA256,
            "h2_parent_sha256": EXPECTED_H2_SHA256,
            "h2_profile": EXPECTED_H2_PROFILE,
            "h2_package_manifest_sha256": hashlib.sha256(h2_manifest_bytes).hexdigest(),
            "h2_resource_source_profile_sha256": h2_manifest.get("resource_source_profile_sha256"),
            "h2_resource_count": len(h2_resources),
        },
        "vehicle_select_scene": {
            "path": "DataScene/FrontendScreens/VehicleSelect.xml",
            "sha256": sha256_file(scene_overlay),
            "manifest_path": OVERLAY_MANIFEST_NAME,
            "manifest_sha256": hashlib.sha256(_json_bytes(overlay_manifest)).hexdigest(),
            "g1_base_sha256": overlay.G1_OVERLAY_SHA256,
        },
        "profiles": [
            {
                "physical_id": 26, "class": 0, "class_name": "T1", "local_index": 7,
                "name": "Mercedes ML-320", "runtime_family": "Mercedes",
                "audio_profile_id": 0, "result_identity": "JEAN-PIERRE STRUGO",
                "status": "PREVIOUSLY_CONFIRMED_BY_RUNTIME",
            },
            {
                "physical_id": 27, "class": 1, "class_name": "T2", "local_index": 7,
                "name": "Navara donor", "runtime_family": "Navara",
                "donor_physical_id": 7, "role": EXPECTED_ID27_ROLE,
                "audio_profile_id": 7, "race_colour_canary_rgba": [0, 1, 1, 1],
                "status": "DIAGNOSTIC_ONLY_NOT_REAL_ADDON",
            },
        ],
        "resource_inventory": copied_resources,
        "omitted_state": ["PlayerState.xml", "PlayerState.xml#", "save files", "raw captures"],
        "runtime_boundary": {
            "participant_count_changed": False,
            "randomizer_present": False,
            "id27_is_real_independent_t2_payload": False,
            "r5v_i_full_pass": False,
        },
    }


def _verify_runtime_manifest(package: Path, manifest: dict[str, Any]) -> None:
    package = _validate_output_directory(package)
    if not package.is_dir():
        raise PackageError("runtime package directory is missing")
    if manifest.get("status") != "READY_FOR_HUMAN_RUNTIME" or manifest.get("profile") != EXPECTED_I0_PROFILE:
        raise PackageError("runtime package is not the pinned I.0 profile")
    candidate_meta = manifest.get("candidate", {})
    candidate_path = _inside(package, candidate_meta.get("path", ""))
    patch_path = _inside(package, candidate_meta.get("patch_manifest_path", ""))
    if (candidate_path.stat().st_size != candidate_meta.get("size")
            or sha256_file(candidate_path) != candidate_meta.get("sha256")):
        raise PackageError("runtime package executable differs from its manifest")
    if sha256_file(patch_path) != candidate_meta.get("patch_manifest_sha256"):
        raise PackageError("runtime package executable manifest hash mismatch")

    scene_meta = manifest.get("vehicle_select_scene", {})
    scene_path = _inside(package, scene_meta.get("path", ""))
    scene_manifest_path = _inside(package, scene_meta.get("manifest_path", ""))
    if sha256_file(scene_path) != scene_meta.get("sha256"):
        raise PackageError("runtime package VehicleSelect hash mismatch")
    if sha256_file(scene_manifest_path) != scene_meta.get("manifest_sha256"):
        raise PackageError("runtime package VehicleSelect manifest hash mismatch")

    profiles = manifest.get("profiles", [])
    if len(profiles) != 2 or [entry.get("physical_id") for entry in profiles] != [26, 27]:
        raise PackageError("runtime package must describe physical IDs 26 and 27 separately")
    id27 = profiles[1]
    if (id27.get("role") != EXPECTED_ID27_ROLE or id27.get("class") != 1
            or id27.get("local_index") != 7 or id27.get("donor_physical_id") != 7):
        raise PackageError("runtime package lost the diagnostic-only ID27 donor boundary")

    resources = manifest.get("resource_inventory")
    if not isinstance(resources, list) or not resources:
        raise PackageError("runtime package resource inventory is empty")
    seen: set[str] = set()
    for entry in resources:
        relative = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(relative, str):
            raise PackageError("runtime package resource record is malformed")
        key = relative.replace("\\", "/").casefold()
        if key in seen:
            raise PackageError(f"duplicate runtime resource path: {relative}")
        seen.add(key)
        path = _inside(package, relative)
        if path.stat().st_size != entry.get("size") or sha256_file(path) != entry.get("sha256"):
            raise PackageError(f"runtime resource hash/size mismatch: {relative}")
        if path.name.casefold() in {"playerstate.xml", "playerstate.xml#"}:
            raise PackageError("runtime package unexpectedly contains profile state")
    scene_entry = next((item for item in resources
                        if item.get("path") == scene_meta.get("path")), None)
    if scene_entry is None or scene_entry.get("sha256") != scene_meta.get("sha256"):
        raise PackageError("VehicleSelect overlay is not part of the packaged resource inventory")

    expected = seen | {
        candidate_meta["path"].casefold(),
        candidate_meta["patch_manifest_path"].casefold(),
        scene_meta["manifest_path"].casefold(),
        RUNTIME_MANIFEST_NAME.casefold(),
    }
    actual = {
        path.relative_to(package).as_posix().casefold()
        for path in package.rglob("*") if path.is_file()
    }
    if actual != expected:
        raise PackageError(
            f"runtime package file set differs from manifest; missing={sorted(expected-actual)}, "
            f"extra={sorted(actual-expected)}"
        )
    if manifest.get("omitted_state") != ["PlayerState.xml", "PlayerState.xml#", "save files", "raw captures"]:
        raise PackageError("runtime package state-exclusion policy changed")


def stage_package(*, h2_root: Path = DEFAULT_H2_ROOT,
                  retail_exe: Path = DEFAULT_RETAIL_EXE,
                  retail_scene: Path = DEFAULT_RETAIL_SCENE,
                  candidate: Path = DEFAULT_CANDIDATE,
                  patch_manifest: Path = DEFAULT_PATCH_MANIFEST,
                  scene_overlay: Path = DEFAULT_OVERLAY,
                  overlay_manifest: Path = DEFAULT_OVERLAY_MANIFEST,
                  output: Path = DEFAULT_PACKAGE) -> dict[str, Any]:
    output = _validate_output_directory(output)
    if output.exists():
        raise PackageError("refusing to overwrite an existing runtime package")
    h2_root = _absolute_without_links(h2_root, "H.2 package")
    if not h2_root.is_dir():
        raise PackageError("H.2 package directory is missing")
    retail_exe = Path(os.path.abspath(retail_exe))
    if not retail_exe.is_file():
        raise PackageError("retail executable source is not a regular file")
    retail_scene = Path(os.path.abspath(retail_scene))
    if not retail_scene.is_file():
        raise PackageError("retail VehicleSelect scene is missing")
    candidate = _absolute_without_links(candidate, "I.0 candidate")
    patch_manifest = _absolute_without_links(patch_manifest, "I.0 patch manifest")
    scene_overlay = _absolute_without_links(scene_overlay, "I.0 VehicleSelect overlay")
    overlay_manifest = _absolute_without_links(overlay_manifest, "I.0 overlay manifest")
    if any(not item.is_file() for item in (candidate, patch_manifest, scene_overlay, overlay_manifest)):
        raise PackageError("an I.0 candidate or overlay component is missing")
    h2_manifest, h2_manifest_bytes, h2_resources = verify_h2_source(h2_root)
    candidate_meta, overlay_meta = _verify_component_builds(
        retail_exe, retail_scene, candidate, patch_manifest, scene_overlay, overlay_manifest)
    if candidate_meta["parent_candidate"]["sha256"] != EXPECTED_H2_SHA256:
        raise PackageError("candidate does not descend from the exact H.2 executable")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=output.name + ".staging-", dir=output.parent))
    try:
        copied: list[dict[str, Any]] = []
        scene_relative = "DataScene/FrontendScreens/VehicleSelect.xml"
        for record in h2_resources:
            relative = record["path"]
            destination = temporary / _safe_relative(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = scene_overlay if relative == scene_relative else _inside(h2_root, relative)
            shutil.copy2(source, destination)
            role = "R5V-I.0 VehicleSelect overlay" if relative == scene_relative else "qualified H.2 resource root"
            copied.append(_entry(destination, relative, role))

        shutil.copy2(candidate, temporary / "MRallye.exe")
        shutil.copy2(patch_manifest, temporary / PATCH_MANIFEST_NAME)
        shutil.copy2(overlay_manifest, temporary / OVERLAY_MANIFEST_NAME)
        manifest = _build_runtime_manifest(
            h2_manifest=h2_manifest,
            h2_manifest_bytes=h2_manifest_bytes,
            h2_resources=h2_resources,
            candidate_manifest=candidate_meta,
            candidate=temporary / "MRallye.exe",
            scene_overlay=temporary / scene_relative,
            overlay_manifest=overlay_meta,
            copied_resources=sorted(copied, key=lambda row: row["path"].casefold()),
        )
        _write_json(temporary / RUNTIME_MANIFEST_NAME, manifest)
        _verify_runtime_manifest(temporary, manifest)
        os.replace(temporary, output)
    except Exception:
        temp_resolved = Path(os.path.abspath(temporary))
        parent_resolved = Path(os.path.abspath(output.parent))
        if (temp_resolved.parent == parent_resolved
                and temp_resolved.name.startswith(output.name + ".staging-")
                and registry._is_research_output(temp_resolved)):
            shutil.rmtree(temp_resolved)
        raise

    return verify_package(output, retail_exe=retail_exe, retail_scene=retail_scene)


def verify_package(package: Path, *, retail_exe: Path = DEFAULT_RETAIL_EXE,
                   retail_scene: Path = DEFAULT_RETAIL_SCENE) -> dict[str, Any]:
    package = _validate_output_directory(package)
    if not package.is_dir():
        raise PackageError(f"runtime package directory is missing: {package}")
    retail_exe = Path(os.path.abspath(retail_exe))
    if not retail_exe.is_file():
        raise PackageError("retail executable source is not a regular file")
    retail_scene = Path(os.path.abspath(retail_scene))
    if not retail_scene.is_file():
        raise PackageError("retail VehicleSelect scene is missing")
    manifest, _raw = _load_json(package / RUNTIME_MANIFEST_NAME)
    _verify_runtime_manifest(package, manifest)
    _verify_component_builds(
        retail_exe, retail_scene,
        package / "MRallye.exe",
        package / PATCH_MANIFEST_NAME,
        package / "DataScene/FrontendScreens/VehicleSelect.xml",
        package / OVERLAY_MANIFEST_NAME,
    )
    return {
        "status": "VERIFIED",
        "profile": manifest["profile"],
        "candidate_sha256": manifest["candidate"]["sha256"],
        "vehicle_select_sha256": manifest["vehicle_select_scene"]["sha256"],
        "resource_count": len(manifest["resource_inventory"]),
        "id26": manifest["profiles"][0],
        "id27": manifest["profiles"][1],
        "package": str(package),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage", help="verify source components and stage a new ignored runtime package")
    stage.add_argument("--h2-root", type=Path, default=DEFAULT_H2_ROOT)
    stage.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL_EXE)
    stage.add_argument("--retail-scene", type=Path, default=DEFAULT_RETAIL_SCENE)
    stage.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    stage.add_argument("--patch-manifest", type=Path, default=DEFAULT_PATCH_MANIFEST)
    stage.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    stage.add_argument("--overlay-manifest", type=Path, default=DEFAULT_OVERLAY_MANIFEST)
    stage.add_argument("--output", type=Path, default=DEFAULT_PACKAGE)

    verify = sub.add_parser("verify", help="verify package hashes, provenance and deterministic rebuilds")
    verify.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    verify.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL_EXE)
    verify.add_argument("--retail-scene", type=Path, default=DEFAULT_RETAIL_SCENE)
    args = parser.parse_args(argv)
    try:
        if args.command == "stage":
            result = stage_package(
                h2_root=args.h2_root, retail_exe=args.retail_exe,
                retail_scene=args.retail_scene, candidate=args.candidate,
                patch_manifest=args.patch_manifest, scene_overlay=args.overlay,
                overlay_manifest=args.overlay_manifest, output=args.output)
        else:
            result = verify_package(args.package, retail_exe=args.retail_exe,
                                    retail_scene=args.retail_scene)
    except (PackageError, i0.CandidateError, overlay.OverlayError, registry.PatchError,
            OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"R5V-I.0 runtime package refused: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
