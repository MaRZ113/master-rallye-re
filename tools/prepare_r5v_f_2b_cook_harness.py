#!/usr/bin/env python3
"""Prepare an isolated retail-native Mercedes cooker harness.

This tool verifies the pinned retail EXE/archive and the selected demo-8.4.1
source, then creates new-only copies under the top-level research-output tree.
It does not edit the canonical corpus, the retail installation, GXM files, or
the retail Data.sma. Runtime cooking remains a manual game step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import patch_vehicle_registry_id26 as patcher  # noqa: E402


EXPECTED_GXM_SHA256 = {
    "car.gxm": "ff238b391da254ef10904bb59b7430d17e1000cfceec8821d61f98b7158993fe",
    "complete.gxm": "95caced8716239d4fa093fc0320e737e13dc1eedc8b649456d4cc89444fe354d",
    "wheel.gxm": "74bfb66a0b411cb3814bbc16f4c672bc9d42b5b7b7e7e7415686ba805ac517ea",
}
EXPECTED_RETAIL_EXE_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
EXPECTED_RETAIL_SMA_SHA256 = "03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f"
EXPECTED_SOURCE_COUNTS = {".gxm": 3, ".gxi": 25, ".dxt": 25, ".txt": 3, ".dx": 3}
PHASE_ID = "R5V-F.2b"


class PreparationError(ValueError):
    """A source, path, or staging invariant failed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_hash(actual: str, expected: str, label: str) -> None:
    if actual.casefold() != expected.casefold():
        raise PreparationError(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def _safe_regular_files(root: Path) -> list[Path]:
    if not root.is_dir() or root.is_symlink():
        raise PreparationError(f"source is not an ordinary directory: {root}")
    entries = list(root.iterdir())
    if any(item.is_symlink() for item in entries):
        raise PreparationError("Mercedes source contains a symlink")
    unexpected_dirs = [item.name for item in entries if item.is_dir() and item.name.casefold() != "lpha"]
    if unexpected_dirs:
        raise PreparationError(f"unexpected directories in selected Mercedes source: {unexpected_dirs}")
    if any(not item.is_file() and not item.is_dir() for item in entries):
        raise PreparationError("Mercedes source contains a non-file, non-directory entry")
    return sorted((item for item in entries if item.is_file()), key=lambda item: item.name.casefold())


def inventory_adjacent_lpha_variant(source: Path) -> dict[str, Any] | None:
    """Inventory the observed nested alternate without staging its resources."""
    variant = source / "lpha"
    if not variant.exists():
        return None
    if variant.is_symlink() or not variant.is_dir():
        raise PreparationError("the adjacent lpha variant is not an ordinary directory")
    entries = list(variant.iterdir())
    if any(item.is_symlink() or not item.is_file() for item in entries):
        raise PreparationError("the adjacent lpha variant contains an unsafe or nested entry")
    files = []
    resource_roots: set[str] = set()
    path_pattern = re.compile(rb"(?:D:/|D:/Projects/|D:/projects/)MRallyeTNG/DataGx/Vehicles/([^/\\]+)", re.IGNORECASE)
    for path in sorted(entries, key=lambda item: item.name.casefold()):
        data = path.read_bytes()
        if path.suffix.casefold() == ".gxm":
            resource_roots.update(match.group(1).decode("ascii", errors="replace") for match in path_pattern.finditer(data))
        files.append({"name": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    counts: dict[str, int] = {}
    for entry in files:
        suffix = Path(entry["name"]).suffix.casefold().lstrip(".")
        counts[suffix] = counts.get(suffix, 0) + 1
    return {
        "folder_name": "lpha",
        "status": "EXCLUDED; alternate GXM path family is separately named",
        "gxm_resource_roots": sorted(resource_roots, key=str.casefold),
        "counts": {"files": len(files), **counts},
        "files": files,
    }


def inventory_source_tree(
    source: Path,
    *,
    expected_gxm_hashes: dict[str, str] = EXPECTED_GXM_SHA256,
) -> dict[str, Any]:
    """Hash-lock the selected source, its three GXM files, and texture pairs."""
    files = _safe_regular_files(source)
    counts: dict[str, int] = {}
    entries: list[dict[str, Any]] = []
    hashes_by_name: dict[str, str] = {}
    for path in files:
        suffix = path.suffix.casefold()
        counts[suffix] = counts.get(suffix, 0) + 1
        digest = sha256_file(path)
        hashes_by_name[path.name.casefold()] = digest
        entries.append({"name": path.name, "bytes": path.stat().st_size, "sha256": digest})
    if counts != EXPECTED_SOURCE_COUNTS:
        raise PreparationError(f"unexpected source file inventory: {counts}")

    for name, expected in expected_gxm_hashes.items():
        actual = hashes_by_name.get(name.casefold())
        if actual is None:
            raise PreparationError(f"required Mercedes source file is missing: {name}")
        require_hash(actual, expected, name)

    gxi_stems = {path.stem.casefold() for path in files if path.suffix.casefold() == ".gxi"}
    dxt_stems = {path.stem.casefold() for path in files if path.suffix.casefold() == ".dxt"}
    if gxi_stems != dxt_stems:
        missing_dxt = sorted(gxi_stems - dxt_stems)
        missing_gxi = sorted(dxt_stems - gxi_stems)
        raise PreparationError(f"GXI/DXT texture pairs do not close; missing DXT={missing_dxt}, missing GXI={missing_gxi}")

    return {
        "build": "demo-8.4.1",
        "folder": "DataGx/Vehicles/Copy of Mercedes",
        "counts": {"files": len(entries), **{ext.lstrip("."): count for ext, count in sorted(counts.items())}},
        "files": entries,
        "texture_pairs": sorted(gxi_stems),
        "adjacent_unstaged_variant": inventory_adjacent_lpha_variant(source),
    }


def inventory_runtime_sidecars(sidecar_roots: dict[str, Path]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for name, root in sidecar_roots.items():
        if not root.is_dir() or root.is_symlink():
            raise PreparationError(f"required retail sidecar folder is absent or unsafe: {root}")
        entries: list[dict[str, Any]] = []
        for path in sorted(root.rglob("*"), key=lambda item: str(item).casefold()):
            if path.is_symlink():
                raise PreparationError(f"retail sidecar contains a symlink: {path}")
            if path.is_file():
                entries.append({"path": path.relative_to(root).as_posix(),
                                "bytes": path.stat().st_size,
                                "sha256": sha256_file(path)})
        result[name] = entries
    return result


def verify_retail_inputs(
    retail_exe: Path,
    retail_sma: Path,
    *,
    expected_exe_sha256: str = EXPECTED_RETAIL_EXE_SHA256,
    expected_sma_sha256: str = EXPECTED_RETAIL_SMA_SHA256,
) -> dict[str, Any]:
    for path, label in ((retail_exe, "retail MRallye.exe"), (retail_sma, "retail Data.sma")):
        if not path.is_file() or path.is_symlink():
            raise PreparationError(f"{label} is absent or not a regular file: {path}")
    exe_hash = sha256_file(retail_exe)
    sma_hash = sha256_file(retail_sma)
    require_hash(exe_hash, expected_exe_sha256, "retail MRallye.exe")
    require_hash(sma_hash, expected_sma_sha256, "retail Data.sma")
    return {
        "MRallye.exe": {"bytes": retail_exe.stat().st_size, "sha256": exe_hash},
        "Data.sma": {"bytes": retail_sma.stat().st_size, "sha256": sma_hash},
    }


def authorize_authoring_path(
    *,
    link_exists: bool,
    marker: dict[str, Any] | None,
    link_type: str | None,
    resolved_target: str | None,
    expected_link_path: str,
    expected_target: str,
) -> str:
    """Return create/reuse only for absent or positively marked phase junctions."""
    if not link_exists:
        if marker is not None:
            raise PreparationError("authoring path is absent but a phase marker exists; inspect manually")
        return "create"
    if marker is None:
        raise PreparationError("authoring path already exists without an R5V-F.2b ownership marker")
    state = marker.get("state")
    if marker.get("phase") != PHASE_ID or state not in {"creating", "created"}:
        raise PreparationError("authoring path marker is not a recoverable R5V-F.2b junction record")
    if os.path.normcase(os.path.normpath(str(marker.get("link_path", "")))) != os.path.normcase(os.path.normpath(expected_link_path)):
        raise PreparationError("authoring path marker names a different junction path")
    if link_type != "Junction":
        raise PreparationError("existing authoring path is not a Windows Junction")
    if os.path.normcase(os.path.normpath(resolved_target or "")) != os.path.normcase(os.path.normpath(expected_target)):
        raise PreparationError("existing authoring junction resolves to an unexpected target")
    if os.path.normcase(os.path.normpath(str(marker.get("target", "")))) != os.path.normcase(os.path.normpath(expected_target)):
        raise PreparationError("authoring path marker names an unexpected target")
    return "recover" if state == "creating" else "reuse"


def authorize_junction_removal(
    *,
    marker: dict[str, Any] | None,
    link_type: str | None,
    resolved_target: str | None,
    expected_link_path: str,
    expected_target: str,
) -> None:
    """Raise unless the exact R5V-F.2b junction is positively identified."""
    if marker is None or marker.get("phase") != PHASE_ID or marker.get("state") != "created":
        raise PreparationError("junction removal refused: missing completed phase ownership marker")
    if os.path.normcase(os.path.normpath(str(marker.get("link_path", "")))) != os.path.normcase(os.path.normpath(expected_link_path)):
        raise PreparationError("junction removal refused: marker path mismatch")
    if link_type != "Junction":
        raise PreparationError("junction removal refused: path is not a Windows Junction")
    if os.path.normcase(os.path.normpath(resolved_target or "")) != os.path.normcase(os.path.normpath(expected_target)):
        raise PreparationError("junction removal refused: actual target mismatch")
    if os.path.normcase(os.path.normpath(str(marker.get("target", "")))) != os.path.normcase(os.path.normpath(expected_target)):
        raise PreparationError("junction removal refused: recorded target mismatch")


def _copy_new(source: Path, destination: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    if destination.exists() or destination.is_symlink():
        raise PreparationError(f"refusing to overwrite staged path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    digest = sha256_file(destination)
    if expected_sha256 is not None:
        require_hash(digest, expected_sha256, f"staged copy {destination.name}")
    return {"path": destination.as_posix(), "bytes": destination.stat().st_size, "sha256": digest}


def stage_source_resources(
    source: Path,
    authoring_root: Path,
    runtime_vehicle_root: Path,
    source_manifest: dict[str, Any],
    *,
    expected_gxm_hashes: dict[str, str] = EXPECTED_GXM_SHA256,
) -> dict[str, list[dict[str, Any]]]:
    before = inventory_source_tree(source, expected_gxm_hashes=expected_gxm_hashes)
    if before != source_manifest:
        raise PreparationError("Mercedes source changed after its manifest was created")
    staged_authoring: list[dict[str, Any]] = []
    staged_runtime: list[dict[str, Any]] = []
    for entry in source_manifest["files"]:
        name = entry["name"]
        suffix = Path(name).suffix.casefold()
        if suffix == ".gxi":
            staged_authoring.append(_copy_new(source / name, authoring_root / name, entry["sha256"]))
        elif suffix in {".gxm", ".dxt"}:
            staged_runtime.append(_copy_new(source / name, runtime_vehicle_root / name, entry["sha256"]))
    if any(path.suffix.casefold() == ".dx" for path in runtime_vehicle_root.iterdir()):
        raise PreparationError("runtime cook staging unexpectedly contains a DX cache")
    after = inventory_source_tree(source, expected_gxm_hashes=expected_gxm_hashes)
    if after != before:
        raise PreparationError("canonical demo source changed during staging")
    return {"authoring_gxi": staged_authoring, "runtime_gxm_dxt": staged_runtime}


def _copy_tree_new(source: Path, destination: Path) -> list[dict[str, Any]]:
    entries = inventory_runtime_sidecars({"sidecar": source})["sidecar"]
    destination.mkdir(parents=True, exist_ok=False)
    copied: list[dict[str, Any]] = []
    for entry in entries:
        relative = Path(entry["path"])
        copied.append(_copy_new(source / relative, destination / relative, entry["sha256"]))
    if inventory_runtime_sidecars({"sidecar": source})["sidecar"] != entries:
        raise PreparationError(f"retail sidecar changed while staging: {source}")
    return copied


def prepare_harness(
    *,
    source: Path,
    retail_exe: Path,
    retail_sma: Path,
    sidecar_roots: dict[str, Path],
    output_root: Path,
) -> dict[str, Any]:
    """Verify first, then write a new isolated harness tree; never overwrite."""
    source = source.resolve(strict=True)
    retail_exe = retail_exe.resolve(strict=True)
    retail_sma = retail_sma.resolve(strict=True)
    output_root = output_root.resolve(strict=False)
    if "research-output" not in {part.casefold() for part in output_root.parts}:
        raise PreparationError("output must be inside the unhidden research-output directory")
    if output_root.exists() or output_root.is_symlink():
        raise PreparationError(f"phase output already exists; refusing to overwrite: {output_root}")

    source_manifest = inventory_source_tree(source)
    retail_manifest = verify_retail_inputs(retail_exe, retail_sma)
    sidecar_manifest = inventory_runtime_sidecars(sidecar_roots)
    source_original = source_manifest

    output_root.mkdir(parents=True, exist_ok=False)
    candidate_root = output_root / "candidate"
    candidate_path = candidate_root / "MRallye.exe"
    patch_manifest_path = candidate_root / "patch-manifest.json"
    binary_diff_path = candidate_root / "binary-diff.txt"
    patch_manifest = patcher.write_candidate(
        retail_exe,
        candidate_path,
        patch_manifest_path,
        binary_diff_path,
        id26_profile=patcher.ID26_MERCEDES_COOK_HARNESS,
    )

    runtime_root = output_root / "runtime-cook"
    runtime_root.mkdir()
    runtime_exe = _copy_new(candidate_path, runtime_root / "MRallye.exe", patch_manifest["patched_sha256"])
    runtime_sma = _copy_new(retail_sma, runtime_root / "Data.sma", retail_manifest["Data.sma"]["sha256"])
    staged_sidecars: dict[str, list[dict[str, Any]]] = {}
    for name, root in sidecar_roots.items():
        staged_sidecars[name] = _copy_tree_new(root, runtime_root / name)

    authoring_root = output_root / "authoring-root" / "Mercedes"
    runtime_vehicle_root = runtime_root / "DataGx" / "Vehicles" / "Mercedes"
    authoring_root.mkdir(parents=True)
    runtime_vehicle_root.mkdir(parents=True)
    staged_resources = stage_source_resources(source, authoring_root, runtime_vehicle_root, source_manifest)

    script_source = TOOLS_DIR / "r5v_f_2b"
    scripts_target = output_root / "scripts"
    scripts_target.mkdir()
    for script_name in ("CHECK_AUTHORING_PATH.ps1", "SETUP_MERCEDES_JUNCTION.ps1", "REMOVE_MERCEDES_JUNCTION.ps1"):
        _copy_new(script_source / script_name, scripts_target / script_name)

    for empty_name in ("cook-a", "cook-b", "cache-only"):
        (output_root / empty_name).mkdir()

    # Hash again before publishing manifests; this is an explicit no-mutation check.
    if inventory_source_tree(source) != source_original:
        raise PreparationError("canonical demo-8.4.1 Mercedes source was modified")
    if verify_retail_inputs(retail_exe, retail_sma) != retail_manifest:
        raise PreparationError("canonical retail EXE/Data.sma changed during staging")

    manifest = {
        "schema_version": 1,
        "phase": PHASE_ID,
        "status": "PREPARED; NO RUNTIME COOK HAS BEEN RUN",
        "source": source_manifest,
        "retail": retail_manifest,
        "retail_sidecars": sidecar_manifest,
        "staged": {
            "candidate_exe": runtime_exe,
            "data_sma": runtime_sma,
            "sidecars": staged_sidecars,
            **staged_resources,
        },
        "registry_profile": {
            "profile_id": patch_manifest["profile"],
            "physical_id": 26,
            "class": "T1",
            "local_index": 7,
            "resource_family": "Mercedes",
            "capacity": 27,
            "class_capacities": {"T1": 8, "T2": 7, "T3": 12},
            "id25_internal_name": "Trooper",
            "cleanup_profile_changed": False,
        },
        "archive_probe": {
            "retail_data_sma_mercedes_vehicle_members": 0,
            "method": "ZIP-compatible Data.sma member index filtered to DataGx/Vehicles/Mercedes/",
        },
        "gxm_rewrite": "NOT USED; runtime relies on a reversible authoring-root junction",
        "runtime_dx_initial_state": "ABSENT from loose DataGx/Vehicles/Mercedes staging",
    }
    _write_json_new(output_root / "source-manifest.json", {
        "schema_version": 1,
        "source": source_manifest,
        "retail": retail_manifest,
        "retail_sidecars": sidecar_manifest,
        "archive_probe": manifest["archive_probe"],
    })
    _write_json_new(output_root / "cook-manifest.json", manifest)
    _write_text_new(output_root / "HUMAN_COOK_INSTRUCTIONS.txt",
                    _human_instructions(output_root.resolve()))
    return manifest


def _write_json_new(path: Path, value: Any) -> None:
    if path.exists() or path.is_symlink():
        raise PreparationError(f"refusing to overwrite manifest: {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text_new(path: Path, value: str) -> None:
    if path.exists() or path.is_symlink():
        raise PreparationError(f"refusing to overwrite instructions: {path}")
    path.write_text(value, encoding="utf-8", newline="\n")


def _human_instructions(phase_root: Path) -> str:
    runtime_root = phase_root / "runtime-cook"
    vehicle_root = runtime_root / "DataGx" / "Vehicles" / "Mercedes"
    return f"""R5V-F.2b HUMAN COOK STEPS
=========================

Prepared state
--------------
- Research phase folder: {phase_root}
- Isolated retail executable: {runtime_root / 'MRallye.exe'}
- Isolated working directory: {runtime_root}
- Mercedes loose resources: {vehicle_root}
- Exact authoring path embedded in the byte-identical GXM files:
  D:\\projects\\MRallyeTNG\\DataGx\\Vehicles\\Mercedes
- Junction target, copied from the demo source:
  {phase_root / 'authoring-root' / 'Mercedes'}

1. Check and create the authoring junction
------------------------------------------
Close any Master Rallye instance. In PowerShell run:

  $phase = '{phase_root}'
  & "$phase\\scripts\\CHECK_AUTHORING_PATH.ps1"
  & "$phase\\scripts\\SETUP_MERCEDES_JUNCTION.ps1"

Expected safe setup output names the exact link above and the isolated target.
The helper refuses any pre-existing unknown directory, file, link, or reparse
point and does not change the original demo source. If it refuses or reports an
unexpected path, stop and send Codex the complete output.

2. Capture the first, complete-only cook
----------------------------------------
Open `D:\\Game\\Master Rallye\\_reverse-tools\\DebugView\\Dbgview64.exe`.
Clear its display and enable Capture Win32 Events before launching the game.
Save the full capture to:

  {phase_root / 'cook-a' / 'complete-cook.log'}

Then launch the isolated EXE from its own working directory:

  Set-Location -LiteralPath '{runtime_root}'
  .\\MRallye.exe

In Vehicle Select choose T1 and move to local position 7 (the eighth T1 entry,
physical ID26). Wait for the preview to finish. The first complete cook should
show the cache miss followed by `Reading GXM`, `Making dx model`,
`Saved cached model`, and `Loaded cached model`; a new `complete.dx` should
appear in the Mercedes loose-resource folder.

As soon as the preview is shown and the new complete.dx is written, exit the
game normally. Do not enter Practice yet. Preserve the full DebugView log and
the new complete.dx; Codex will validate revision 135, structure, references,
and semantic counts before the car/wheel cook gate opens.

3. Car and wheel cook (after complete.dx validation)
---------------------------------------------------
Only after Codex confirms complete.dx passes, start a separate DebugView
capture at:

  {phase_root / 'cook-a' / 'car-wheel-cook.log'}

Before launching, confirm car.dx and wheel.dx are absent and their GXM files
exist. Start the isolated EXE again, use an offline Practice or Quick Race only
to force resource loading, and capture the car and wheel GXM, making, and
saved-cache messages. Once both new DX files appear, exit normally; do not drive
aggressively. Preserve both files and the complete log for SDK and collision
validation.

4. Later reproducibility and cache-only gates
---------------------------------------------
Do not create Cook B or the cache-only runtime yet. Codex must validate the
first car/wheel outputs before generating any repeat or portable package. The
removal helper is for the later cache-only stage, after validation and after
the game is closed:

  & "$phase\\scripts\\REMOVE_MERCEDES_JUNCTION.ps1"

It verifies the phase marker, Junction type, exact target, and copied GXI
hashes; it removes only the exact Junction node. It never recursively deletes
the target or its parent directories.

Return to Codex with the exact paths and hashes of:
- cook-a\\complete-cook.log
- runtime-cook\\DataGx\\Vehicles\\Mercedes\\complete.dx
- a DebugView screenshot only if a line is clipped or ambiguous

This cook-trigger profile does not establish final Mercedes P0/P1 acceptance.
"""


def _default_paths(project_root: Path) -> tuple[Path, Path, Path, dict[str, Path], Path]:
    corpus_root = project_root.parent / "corpora"
    return (
        corpus_root / "demo-8.4.1" / "DataGx" / "Vehicles" / "Copy of Mercedes",
        corpus_root / "retail" / "MRallye.exe",
        corpus_root / "retail" / "Data.sma",
        {"DataAudio": corpus_root / "retail" / "DataAudio",
         "DataVideo": corpus_root / "retail" / "DataVideo"},
        project_root.parent / "research-output" / "r5v_f_2b",
    )


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    default_source, default_exe, default_sma, default_sidecars, default_output = _default_paths(project_root)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=default_source)
    parser.add_argument("--retail-exe", type=Path, default=default_exe)
    parser.add_argument("--retail-data-sma", type=Path, default=default_sma)
    parser.add_argument("--data-audio", type=Path, default=default_sidecars["DataAudio"])
    parser.add_argument("--data-video", type=Path, default=default_sidecars["DataVideo"])
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--dry-run", action="store_true", help="verify source identities without writing")
    args = parser.parse_args(argv)
    try:
        source_manifest = inventory_source_tree(args.source.resolve(strict=True))
        retail_manifest = verify_retail_inputs(args.retail_exe.resolve(strict=True),
                                               args.retail_data_sma.resolve(strict=True))
        sidecar_manifest = inventory_runtime_sidecars({"DataAudio": args.data_audio.resolve(strict=True),
                                                       "DataVideo": args.data_video.resolve(strict=True)})
        if args.dry_run:
            print(json.dumps({"status": "VERIFIED; NO FILES WRITTEN", "source": source_manifest,
                              "retail": retail_manifest, "retail_sidecars": sidecar_manifest}, indent=2))
            return 0
        result = prepare_harness(
            source=args.source,
            retail_exe=args.retail_exe,
            retail_sma=args.retail_data_sma,
            sidecar_roots={"DataAudio": args.data_audio, "DataVideo": args.data_video},
            output_root=args.output,
        )
    except (OSError, PreparationError, patcher.PatchError) as exc:
        parser.exit(2, f"R5V-F.2b preparation refused: {exc}\n")
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "source_files": result["source"]["counts"],
                      "staged_gxi": len(result["staged"]["authoring_gxi"]),
                      "staged_gxm_dxt": len(result["staged"]["runtime_gxm_dxt"]),
                      "candidate_sha256": result["staged"]["candidate_exe"]["sha256"],
                      "data_sma_sha256": result["staged"]["data_sma"]["sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
