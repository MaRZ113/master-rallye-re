#!/usr/bin/env python3
"""Create a compact, deterministic, source-only R-MOD3-G2 review archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".research-output" / "r-mod3" / "g2" / "r-mod3-g2-implementation-review-2026-10-11.zip"
G2 = ROOT / ".research-output" / "r-mod3" / "g2" / "first-integrated-candidate-g2"
LOGS = ROOT / ".research-output" / "r-mod3" / "g2" / "logs"

SOURCE_FILES = [
    "README.md",
    "research/r-mod3/g1/README.md",
    "research/r-mod3/g1/validation-report.md",
    "research/r-mod3/g2/README.md",
    "research/r-mod3/g2/configuration-v3.md",
    "research/r-mod3/g2/native-ownership.md",
    "research/r-mod3/g2/runtime-handoff.md",
    "research/r-mod3/g2/validation-report.md",
    "src/native/rmod1/core.hpp",
    "src/native/rmod1/runtime_core.cpp",
    "src/native/rmod1/launcher.cpp",
    "src/native/rmod1/dinput8_proxy.cpp",
    "src/native/rmod1/dinput8_proxy.def",
    "src/native/rmod1/rmod2_inprocess.cpp",
    "src/native/rmod1/rmod2_inprocess.hpp",
    "src/native/rmod1/rmod2_startup_preflight.hpp",
    "src/native/rmod1/image_mapping.hpp",
    "src/native/rmod1/runtime_image_diff.hpp",
    "src/native/rmod1/runtime_log.hpp",
    "src/native/rmod1/exception_report.hpp",
    "tools/build_r_mod1_candidate.py",
    "tools/build_rmod2_boot_a.py",
    "tools/build_rmod3_g1_candidate.py",
    "tools/build_rmod3_g2_candidate.py",
    "tools/build_rmod3_g2_review.py",
    "tools/r_mod1_native_plan.py",
    "tools/r_mod1_core_tests.ps1",
    "tools/audit_dinput8_exports.py",
    "tools/r_ai1_mixed_class.py",
    "tests/rmod1/core_tests.cpp",
    "tests/rmod1/dinput8_forward_harness.cpp",
    "tests/rmod1/rmod2_boot_b_harness.cpp",
    "tests/rmod1/rmod2_host_qualified_preflight_harness.cpp",
    "tests/rmod1/runtime_image_diff_harness.cpp",
    "tests/rmod1/runtime_exception_harness.cpp",
    "tests/rmod1/runtime_log_harness.cpp",
    "tests/synthetic/test_r_mod1_native_plan.py",
    "tests/synthetic/test_r_mod2_boot_b.py",
    "tests/synthetic/test_r_mod2_dinput8.py",
]
LOG_FILES = [
    "full-suite.txt", "focused-native-plan.txt", "core-g2.txt", "compileall.txt",
    "diff-check.txt", "g1-verify.json", "g2-verify.json", "g2-repro-verify.json",
    "deterministic-rebuild.txt",
]
TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".hpp", ".cpp", ".def", ".ps1", ".ini"}
FORBIDDEN_SUFFIXES = {".exe", ".dll", ".dx", ".dxt", ".gxm", ".gxi", ".bin", ".pak", ".sav"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_state() -> str:
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT,
                            check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain=v1"], cwd=ROOT,
                            check=True, capture_output=True, text=True).stdout
    return f"branch: {branch}\nHEAD: {head}\n\nworking tree status (pre-existing and current; no cleanup performed):\n{status}"


def build(output: Path) -> dict:
    output = Path(os.path.abspath(output))
    if output.exists():
        raise ValueError(f"refusing to overwrite review archive: {output}")
    stage: dict[str, bytes] = {}
    for relative in SOURCE_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"required review source is missing: {relative}")
        stage["source/" + relative] = path.read_bytes()

    for relative in ("candidate-build-evidence.json", "native_plan.hpp"):
        path = G2 / relative
        if not path.is_file():
            raise ValueError(f"required derived G2 evidence is missing: {relative}")
        stage["candidate-reference/" + relative] = path.read_bytes()
    package = G2 / "package"
    manifest_path = package / "candidate-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("required derived G2 evidence is missing: package/candidate-manifest.json")
    stage["candidate-reference/package/candidate-manifest.json"] = manifest_path.read_bytes()
    for path in sorted(package.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            if path.name in {"dinput8.dll", "MRallyeRandomizerRuntime.dll"}:
                continue  # review ZIP carries their verified hashes, never the binary payloads
            raise ValueError(f"non-text candidate package member refused: {path.relative_to(G2)}")
        stage["candidate-reference/package/" + path.relative_to(package).as_posix()] = path.read_bytes()

    for name in LOG_FILES:
        path = LOGS / name
        if not path.is_file():
            raise ValueError(f"required validation record is missing: {name}")
        stage["validation/" + name] = path.read_bytes()
    stage["validation/git-state.txt"] = git_state().encode("utf-8")
    stage["README-review.txt"] = (
        "R-MOD3-G2 implementation review (source/evidence only)\n\n"
        "This archive excludes the retail executable, generated DLL/proxy binaries, game assets, raw Broker dumps, "
        "screenshots and Ghidra databases. candidate-reference contains only text metadata, plan/header sources, "
        "and INI/README package files.\n\n"
        "Reproduce the package from the full canonical checkout and the exact pristine retail executable with:\n"
        "  python tools/build_rmod3_g2_candidate.py --output .research-output/r-mod3/g2/repro\n"
        "Verify with:\n"
        "  python tools/build_rmod3_g2_candidate.py --verify --output .research-output/r-mod3/g2/repro\n"
        "  PYTHONPATH=src python -m unittest discover -s tests/synthetic -v\n"
        "  powershell -ExecutionPolicy Bypass -File tools/r_mod1_core_tests.ps1 -G2\n"
        "  python -m compileall src tools tests\n"
        "  git diff --check\n\n"
        "Build prerequisites: Windows x86 MSVC toolchain plus the repository's Python dependencies. The exact retail "
        "input SHA is pinned by the builder. Synthetic and native harnesses do not qualify G2 gameplay; the attached "
        "runtime handoff is still required. See source/research/r-mod3/g2/.\n"
    ).encode("utf-8")

    for name, data in stage.items():
        suffix = Path(name).suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES:
            raise ValueError(f"proprietary/binary file refused: {name}")
        if suffix in TEXT_SUFFIXES and b"\x00" in data:
            raise ValueError(f"unexpected binary payload in text member: {name}")

    index = {
        "schema_version": 1,
        "archive": output.name,
        "scope": "R-MOD3-G2 implementation review; source and derived text evidence only",
        "candidate_manifest_sha256": sha256(stage["candidate-reference/package/candidate-manifest.json"]),
        "members": [{"path": name, "size": len(data), "sha256": sha256(data)}
                    for name, data in sorted(stage.items())],
    }
    stage["archive-index.json"] = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(stage.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return {"archive": str(output), "sha256": sha256(output.read_bytes()),
            "size": output.stat().st_size, "members": len(stage),
            "indexed_members": len(index["members"]), "status": "SOURCE_ONLY_REVIEW_ARCHIVE_BUILT"}


def verify(output: Path) -> dict:
    output = Path(os.path.abspath(output))
    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or "archive-index.json" not in names:
            raise ValueError("review ZIP has duplicate members or no archive index")
        index = json.loads(archive.read("archive-index.json"))
        expected = {row["path"]: row for row in index.get("members", [])}
        if set(names) != set(expected) | {"archive-index.json"}:
            raise ValueError("review ZIP member set does not match archive-index.json")
        for name, row in expected.items():
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or path.suffix.lower() in FORBIDDEN_SUFFIXES:
                raise ValueError("review archive contains an unsafe or prohibited member: " + name)
            data = archive.read(name)
            if len(data) != row["size"] or sha256(data) != row["sha256"]:
                raise ValueError("review archive member hash/size mismatch: " + name)
    return {"archive": str(output), "sha256": sha256(output.read_bytes()),
            "members": len(expected), "status": "REVIEW_ARCHIVE_INDEX_VERIFIED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--verify", action="store_true", help="verify archive-index.json and all member hashes")
    args = parser.parse_args()
    try:
        result = verify(args.output) if args.verify else build(args.output)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"R-MOD3-G2 review archive failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
