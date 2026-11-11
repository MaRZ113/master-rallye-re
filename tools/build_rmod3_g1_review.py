#!/usr/bin/env python3
"""Create a compact, source-only R-MOD3-G1 implementation review archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / ".research-output/r-mod3/g1/first-integrated-candidate-g1"
DEFAULT_OUTPUT = ROOT / ".research-output/r-mod3/g1/r-mod3-g1-implementation-review.zip"

SOURCE_FILES = (
    "src/native/rmod1/core.hpp",
    "src/native/rmod1/runtime_core.cpp",
    "src/native/rmod1/exception_report.hpp",
    "src/native/rmod1/image_mapping.hpp",
    "src/native/rmod1/rmod2_startup_preflight.hpp",
    "tools/r_ai1_2_randomizer.py",
    "tools/r_ai1_hardening.py",
    "tools/r_ai2_capacity.py",
    "tools/r_ai1_mixed_class.py",
    "tools/r_ui1_opponents.py",
    "tools/patch_vehicle_slot25.py",
    "tools/r_mod1_native_plan.py",
    "tools/build_r_mod1_candidate.py",
    "tools/build_rmod2_boot_a.py",
    "tools/audit_dinput8_exports.py",
    "tools/build_rmod3_g1_candidate.py",
    "tools/build_rmod3_g1_review.py",
    "tools/r_mod1_core_tests.ps1",
    "tests/rmod1/core_tests.cpp",
    "tests/synthetic/test_r_mod1_core.py",
    "tests/synthetic/test_r_mod1_native_plan.py",
    "tests/synthetic/test_r_mod1_composition.py",
    "research/r-mod3/gameplay-expansion/README.md",
    "research/r-mod3/gameplay-expansion/duplicate-carid-root-cause.md",
    "research/r-mod3/gameplay-expansion/native-hook-map.md",
    "research/r-mod3/gameplay-expansion/cross-feature-interactions.md",
    "research/r-mod3/gameplay-expansion/implementation-roadmap.md",
    "research/r-mod1/native-patch-plan-f3.json",
    "research/r-mod1/candidate-v16-f3-manifest.json",
    "research/r-mod3/g1/README.md",
    "research/r-mod3/g1/duplicate-selection.md",
    "research/r-mod3/g1/challenge-clone-army-feasibility.md",
    "research/r-mod3/g1/runtime-handoff.md",
    "research/r-mod3/g1/validation-report.md",
)

ARTIFACT_FILES = (
    ("candidate-build-evidence.json", CANDIDATE / "candidate-build-evidence.json"),
    ("candidate-build-summary.txt", ROOT / ".research-output/r-mod3/g1/candidate-build-summary.txt"),
    ("candidate-verify.txt", ROOT / ".research-output/r-mod3/g1/candidate-verify.txt"),
    ("native-plan.json", CANDIDATE / "package/native-patch-plan.json"),
    ("native-plan.hpp", CANDIDATE / "native_plan.hpp"),
    ("candidate-manifest.json", CANDIDATE / "package/candidate-manifest.json"),
    ("package-README.txt", CANDIDATE / "package/README.txt"),
    ("full-synthetic-tests.txt", ROOT / ".research-output/r-mod3/g1/full-synthetic-tests.txt"),
    ("focused-tests.txt", ROOT / ".research-output/r-mod3/g1/focused-tests.txt"),
    ("core-x86-tests.txt", ROOT / ".research-output/r-mod3/g1/core-x86-tests.txt"),
    ("compileall.txt", ROOT / ".research-output/r-mod3/g1/compileall.txt"),
    ("diff-check.txt", ROOT / ".research-output/r-mod3/g1/diff-check.txt"),
    ("deterministic-rebuild.txt", ROOT / ".research-output/r-mod3/g1/deterministic-rebuild.txt"),
)

BANNED_SUFFIXES = {".exe", ".dll", ".sma", ".dx", ".dxt", ".gxm", ".gxi", ".sav", ".dump"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("git " + " ".join(args) + " failed: " + result.stderr.strip())
    return result.stdout


def deterministic_zip(root: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)


def build(output: Path = DEFAULT_OUTPUT) -> dict:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise RuntimeError("refusing to overwrite existing review archive: " + str(output))
    for relative in SOURCE_FILES:
        if not (ROOT / relative).is_file():
            raise RuntimeError("required review source is missing: " + relative)
    for label, path in ARTIFACT_FILES:
        if not path.is_file():
            raise RuntimeError("required review artifact is missing: " + label + " -> " + str(path))

    with tempfile.TemporaryDirectory(prefix="rmod3-g1-review-", dir=output.parent) as temporary:
        stage = Path(temporary) / "review"
        stage.mkdir()
        for relative in SOURCE_FILES:
            destination = stage / "source" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        for label, source in ARTIFACT_FILES:
            destination = stage / "evidence" / label
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        state = (
            "R-MOD3-G1 Git state snapshot\n\n"
            f"branch: {git('branch', '--show-current').strip()}\n"
            f"HEAD: {git('rev-parse', 'HEAD').strip()}\n"
            "working tree status (full current worktree, including pre-existing unrelated work):\n"
            f"{git('status', '--short')}\n"
            "tracked diff summary:\n"
            f"{git('diff', '--stat')}\n"
        )
        (stage / "GIT_STATE.txt").write_text(state, encoding="utf-8", newline="\n")

        rows = []
        for path in sorted(item for item in stage.rglob("*") if item.is_file()):
            relative = path.relative_to(stage).as_posix()
            if Path(relative).suffix.casefold() in BANNED_SUFFIXES:
                raise RuntimeError("binary or proprietary artifact entered source review: " + relative)
            if relative.casefold().endswith((".dump.bin", ".pak", ".dat", ".png", ".jpg", ".jpeg")):
                raise RuntimeError("raw dump, asset archive, or screenshot entered source review: " + relative)
            rows.append({"path": relative, "size": path.stat().st_size, "sha256": sha256(path)})
        index = {
            "schema_version": 1,
            "artifact_type": "R-MOD3-G1 source and derived-evidence review",
            "candidate_id": "first-integrated-candidate-g1",
            "contents": rows,
            "excluded": ["game executable", "compiled DLLs", "game assets", "raw Broker dumps", "screenshots", "saves", "Ghidra databases"],
        }
        (stage / "archive-index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n",
                                                   encoding="utf-8", newline="\n")
        deterministic_zip(stage, output)

    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(sha256(output) + "  " + output.name + "\n", encoding="ascii", newline="\n")
    return {"archive": str(output), "sha256": sha256(output), "size": output.stat().st_size,
            "indexed_file_count": len(rows), "source_only": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output), indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print("R-MOD3-G1 review archive failed closed: " + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
