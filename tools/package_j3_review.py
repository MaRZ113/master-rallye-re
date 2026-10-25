#!/usr/bin/env python3
"""Create a compact, source-only R5V-J.3 implementation review archive."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / ".research-output/vehicles/sdk/j3"
    / f"r5v-j3-sdk-v1-implementation-review-{date.today().isoformat()}.zip"
)

TOOLS = (
    "tools/addon_collection_runtime.py",
    "tools/addon_runtime.py",
    "tools/build_runtime_launcher.py",
    "tools/build_vehicle_ai_candidate.py",
    "tools/build_vehicle_audio_candidate.py",
    "tools/build_vehicle_hardened_candidate.py",
    "tools/build_vehicle_mode_ai_candidate.py",
    "tools/build_vehicle_multislot_i0.py",
    "tools/build_vehicle_multislot_i1.py",
    "tools/build_vehicle_natural_t1_candidate.py",
    "tools/j2_frontend_reentry.py",
    "tools/mrtool.py",
    "tools/package_j3_review.py",
    "tools/patch_vehicle_registry_id26.py",
    "tools/patch_vehicle_slot25.py",
    "tools/prepare_multislot_vehicle_select_overlay.py",
    "tools/prepare_vehicle_unlock_overlay.py",
    "tools/scanner/inventory.py",
    "tools/vehicle_multislot_i1_runtime_package.py",
    "tools/vehicle_multislot_runtime_package.py",
)
TESTS = (
    "tests/synthetic/test_addon_collection_runtime.py",
    "tests/synthetic/test_addon_sdk.py",
    "tests/synthetic/test_addon_sdk_j2_composition.py",
    "tests/synthetic/test_addon_sdk_project.py",
    "tests/synthetic/test_addon_sdk_runtime.py",
    "tests/synthetic/test_j2_frontend_reentry.py",
    "tests/synthetic/test_library.py",
)
DOCS = (
    "README.md",
    "pyproject.toml",
    "research/vehicles/architecture.md",
    "research/vehicles/status.md",
    "research/vehicles/sdk/architecture.md",
    "research/vehicles/sdk/compilation.md",
    "research/vehicles/sdk/frontend-lifecycle.md",
    "research/vehicles/sdk/manifest-schema.md",
    "research/vehicles/sdk/remaining-gates.md",
    "research/vehicles/sdk/runtime-deployment.md",
    "research/vehicles/sdk/capabilities/retail-2001.json",
    "research/vehicles/sdk/schema/addon-manifest-v1.schema.json",
    "research/vehicles/sdk/fixtures/frontend-reentry.json",
    "research/vehicles/multislot/i1-runtime-evidence.json",
    "research/vehicles/sdk/examples/mercedes-ml320.json",
    "research/vehicles/sdk/examples/r5v-qualifier-t2.json",
    "research/vehicles/sdk/examples/glacier-sprint-t2.json",
    "research/vehicles/sdk/examples/glacier-sprint-t2-project/README.md",
    "research/vehicles/sdk/examples/glacier-sprint-t2-project/addon.json",
    "research/vehicles/sdk/examples/glacier-sprint-t2-project/donor-provenance.json",
    "research/vehicles/sdk/examples/glacier-sprint-t2-project/vehicle-project.json",
    "research/vehicles/audio/stock-audio-matrix.json",
    "research/vehicles/sdk/j2/closeout-2026-10-09.md",
    "research/vehicles/sdk/j2/closeout-runtime-report-2026-10-09.json",
    "runtime_launcher/CMakeLists.txt",
    "runtime_launcher/src/main.cpp",
)
J3_DOCS = "research/vehicles/sdk/j3"
RUNTIME_CHECKS = {
    "offline-reference-addon-plan.json": ".research-output/vehicles/sdk/j0-reference-build-20261008/addon-plan.json",
    "author-addon-plan.json": ".research-output/vehicles/sdk/j3/glacier-sprint-build-20261009-2/addon-plan.json",
    "author-build-manifest.json": ".research-output/vehicles/sdk/j3/glacier-sprint-build-20261009-2/build-manifest.json",
    "author-frontend-overlay-plan.json": ".research-output/vehicles/sdk/j3/glacier-sprint-build-20261009-2/frontend-overlay.plan.json",
    "author-resource-inventory.json": ".research-output/vehicles/sdk/j3/glacier-sprint-build-20261009-2/resource-inventory.json",
    "focused-tests-output.txt": ".research-output/vehicles/sdk/j3/focused-tests.log",
    "full-synthetic-output.txt": ".research-output/vehicles/sdk/j3/full-tests-review.log",
    "compileall-output.txt": ".research-output/vehicles/sdk/j3/compileall.log",
    "j0-reference-verify.json": ".research-output/vehicles/sdk/j3/j0-reference-verify.json",
    "j1-parent-verify.json": ".research-output/vehicles/sdk/j3/j1-parent-verify.json",
    "j2-reentry-verify.json": ".research-output/vehicles/sdk/j3/j2-reentry-verify.json",
    "author-build-verify.json": ".research-output/vehicles/sdk/j3/author-build-verify.json",
    "deterministic-build-comparison.json": ".research-output/vehicles/sdk/j3/deterministic-build-comparison.json",
    "diff-check-output.txt": ".research-output/vehicles/sdk/j3/diff-check-output.txt",
    "cli-help-output.txt": ".research-output/vehicles/sdk/j3/cli-help-output.txt",
    "j3b-reference-runtime-verify.json": ".research-output/vehicles/sdk/j3b/reference-pair-verify.json",
    "j3b-reference-native-patch-manifest.json": ".research-output/vehicles/sdk/j3b/reference-pair-runtime-byte-exact/native-patch-manifest.json",
    "j3b-reference-resource-manifest.json": ".research-output/vehicles/sdk/j3b/reference-pair-runtime-byte-exact/resource-manifest.json",
    "j3b-glacier-runtime-verify.json": ".research-output/vehicles/sdk/j3b/glacier-sprint-verify.json",
    "j3b-glacier-native-patch-manifest.json": ".research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final/native-patch-manifest.json",
    "j3b-glacier-resource-manifest.json": ".research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final/resource-manifest.json",
    "j3b-glacier-collection-inputs.json": ".research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final/collection-inputs.json",
    "j3b-glacier-runtime-profile.json": ".research-output/vehicles/sdk/j3b/glacier-sprint-runtime-final/runtime-profile.json",
    "j3b-glacier-launcher-build.json": ".research-output/vehicles/sdk/j3b/glacier-sprint-launcher/launcher-build.json",
    "j3b-glacier-launcher-verify.txt": ".research-output/vehicles/sdk/j3b/glacier-launcher-verify.txt",
    "j3b-reference-prepare-reproduction.txt": ".research-output/vehicles/sdk/j3b/reference-prepare-repro.log",
    "j3b-reference-verify-reproduction.txt": ".research-output/vehicles/sdk/j3b/reference-verify-repro.log",
    "j3b-glacier-prepare-reproduction.txt": ".research-output/vehicles/sdk/j3b/glacier-prepare-repro.log",
    "j3b-glacier-verify-reproduction.txt": ".research-output/vehicles/sdk/j3b/glacier-verify-repro.log",
    "j3b-runtime-compiler-determinism.json": ".research-output/vehicles/sdk/j3b/runtime-compiler-determinism.json",
    "j3b-wrong-exe-rejection.txt": ".research-output/vehicles/sdk/j3b/wrong-exe-rejection.txt",
    "j3b-t2-only-rejection.txt": ".research-output/vehicles/sdk/j3b/t2-only-rejection.txt",
    "j3b-focused-tests.txt": ".research-output/vehicles/sdk/j3b/focused-tests.log",
    "j3b-archive-focused-reproduction.txt": ".research-output/vehicles/sdk/j3b/archive-focused-repro.log",
    "j3b-full-synthetic-tests.txt": ".research-output/vehicles/sdk/j3b/full-synthetic.log",
    "j3b-compileall.txt": ".research-output/vehicles/sdk/j3b/compileall.log",
    "j3b-diff-check.txt": ".research-output/vehicles/sdk/j3b/diff-check.log",
    "j3b-j0-verify.json": ".research-output/vehicles/sdk/j3b/j0-reference-verify.json",
    "j3b-j1-parent-verify.json": ".research-output/vehicles/sdk/j3b/j1-parent-verify.json",
    "j3b-j2-corrected-verify.json": ".research-output/vehicles/sdk/j3b/j2-reentry-verify.json",
}
FORBIDDEN_SUFFIXES = {
    ".exe", ".dll", ".dx", ".dxt", ".gxm", ".gxi", ".sma", ".sav", ".bin",
}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _read(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"required review input is missing or linked: {path.relative_to(ROOT)}")
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        raise ValueError(f"proprietary/binary input is forbidden in review archive: {path.name}")
    return path.read_bytes()


def _sanitize_log(data: bytes) -> bytes:
    text = data.decode("utf-8", errors="replace")
    text = re.sub(re.escape(str(ROOT)), "<VEHICLE_WORKTREE>", text, flags=re.IGNORECASE)
    text = text.replace(r"C:\\Users\\MaRZ", "<USERPROFILE>")
    text = text.replace(r"C:\Users\MaRZ", "<USERPROFILE>")
    return text.encode("utf-8")


def _git_state() -> bytes:
    state = {
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "status_porcelain_v1": _git("status", "--porcelain=v1"),
        "changed_files_summary": _git("status", "--short"),
        "source_changes_committed": False,
    }
    return (json.dumps(state, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _collect_inputs() -> dict[str, bytes]:
    files: dict[str, bytes] = {}

    for path in DOCS + TOOLS + TESTS:
        files[path] = _read(ROOT / path)

    # Include all importable SDK library source, not bytecode or runtime assets.
    for path in sorted((ROOT / "src/master_rallye").rglob("*.py")):
        if "__pycache__" in path.parts or path.is_symlink():
            continue
        files[path.relative_to(ROOT).as_posix()] = _read(path)

    for path in sorted((ROOT / J3_DOCS).rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        files[path.relative_to(ROOT).as_posix()] = _read(path)

    for archive_name, relative in RUNTIME_CHECKS.items():
        files[f"validation-output/{archive_name}"] = _sanitize_log(_read(ROOT / relative))

    files["WORKTREE-STATE.json"] = _git_state()
    files["project/README.md"] = files["README.md"]
    files["README.md"] = files["research/vehicles/sdk/j3/review-readme.md"]
    files["COMMANDS.txt"] = (
        "$env:PYTHONPATH='src'; python -m unittest tests.synthetic.test_addon_collection_runtime "
        "tests.synthetic.test_addon_sdk "
        "tests.synthetic.test_addon_sdk_project tests.synthetic.test_addon_sdk_runtime "
        "tests.synthetic.test_addon_sdk_j2_composition tests.synthetic.test_j2_frontend_reentry -v\n"
        "python -m unittest discover -s tests/synthetic -v\n"
        "python -m compileall src tools tests\n"
        "python tools/mrtool.py addon build --manifest research/vehicles/sdk/examples/mercedes-ml320.json "
        "--manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json "
        "--capabilities research/vehicles/sdk/capabilities/retail-2001.json "
        "--output .research-output/j3-reference-plan\n"
        "python tools/mrtool.py addon verify .research-output/j3-reference-plan\n"
    ).encode("utf-8")

    for name, data in files.items():
        if Path(name).suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"forbidden file extension in review package: {name}")
    return dict(sorted(files.items()))


def build_archive(output: Path) -> dict[str, object]:
    output = output.resolve()
    allowed_root = (ROOT / ".research-output/vehicles/sdk/j3").resolve()
    if allowed_root not in output.parents:
        raise ValueError("review archive output must stay under .research-output/vehicles/sdk/j3")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing review archive: {output}")
    if output.with_suffix(output.suffix + ".sha256").exists():
        raise FileExistsError(f"refusing to overwrite existing archive hash sidecar: {output}.sha256")

    files = _collect_inputs()
    index = {
        "format": "r5v-j3-review-archive-index-v1",
        "archive_scope": "source, tests, docs and sanitized validation output; no proprietary runtime payloads",
        "files": [
            {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        ],
    }
    index_data = (json.dumps(index, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
        info = zipfile.ZipInfo("archive-index.json", date_time=(2026, 10, 9, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, index_data)

    with zipfile.ZipFile(output, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"ZIP CRC check failed for {bad}")
        names = set(archive.namelist())
        if names != set(files) | {"archive-index.json"}:
            raise ValueError("archive file list differs from the indexed source set")
        recorded = json.loads(archive.read("archive-index.json"))
        for row in recorded["files"]:
            data = archive.read(row["path"])
            if len(data) != row["size"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError(f"archive index verification failed: {row['path']}")

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {output.name}\n", encoding="ascii", newline="\n")
    return {"status": "PASS", "path": str(output), "sha256": digest,
            "indexed_files": len(files), "size": output.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = build_archive(args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
