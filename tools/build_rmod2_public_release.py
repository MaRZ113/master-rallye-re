#!/usr/bin/env python3
"""Build a deterministic, source-free player ZIP from the audited BOOT-B candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from audit_dinput8_exports import EXPECTED as DINPUT_EXPORTS, exports as parse_exports

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / ".research-output/r-mod2/practice-checkpoint-start-hotfix-2026-10-10-r2/MasterRallye-Randomizer-BOOT-B-Test"
DEFAULT_OUTPUT = ROOT / ".research-output/r-mod2/release-prep-2026-10-10"
RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
PROXY_SHA256 = "25a279f0b3191806e81cf243986c7341fca694abf05c4549c9c4b073961d5441"
RUNTIME_SHA256 = "666cd52e2dcb1e53ed7e4a6f36a20fa43cb71f64c2ee0720a70fff47fff58eb4"
RELEASE_NAME = "MasterRallye-Randomizer-v0.1.0-beta.1-win32.zip"
PUBLIC_FILES = (
    "README.md", "CHANGELOG.md", "LICENSE", "MRallyeRandomizer.ini",
    "docs/INSTALLATION.md", "docs/CONFIGURATION.md", "docs/LIVE_RELOAD.md",
    "docs/COMPATIBILITY.md", "docs/TROUBLESHOOTING.md",
)


class ReleaseError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pe_machine(path: Path) -> int:
    data = path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ReleaseError(f"{path.name}: missing PE DOS header")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if pe + 6 > len(data) or data[pe:pe + 4] != b"PE\0\0":
        raise ReleaseError(f"{path.name}: invalid PE signature")
    return struct.unpack_from("<H", data, pe + 4)[0]


def audit_release_ini(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) > 4096 or data.startswith(b"\xef\xbb\xbf") or any(byte > 0x7F for byte in data):
        raise ReleaseError("release INI must be ASCII, without a BOM, and at most 4096 bytes")
    text = data.decode("ascii")
    required = (
        "[General]\nConfigVersion = 2", "[Randomizer]", "QuickRace = 4",
        "RallyeCup = 4", "MasterRallye = 4", "Invitation = 4", "Challenge = 4",
        "Duplicates = 1", "[Opponents]", "MaxOpponents = 5", "[Addons]\n",
        "Include = 0", "[Logging]\n", "Enabled = 0",
    )
    for marker in required:
        if marker not in text:
            raise ReleaseError(f"release INI is missing required default: {marker!r}")
    for value, name in enumerate(("Stock", "T1", "T2", "T3", "Full", "Mixed", "Diverse")):
        if f"; {value} = {name}\n" not in text:
            raise ReleaseError(f"release INI is missing vertical policy legend entry {value}={name}")
    if "Experimental.ExtendedAI" in text or "[Experimental]" in text or "Randomizer.Enabled" in text:
        raise ReleaseError("ConfigVersion 2 release INI must not contain legacy/experimental switches")
    if b"\r" in data:
        raise ReleaseError("release INI must use canonical LF line endings")
    return {"bytes": len(data), "ascii": True, "config_version": 2,
            "policy_values": {key: 4 for key in ("QuickRace", "RallyeCup", "MasterRallye", "Invitation", "Challenge")},
            "max_opponents": 5, "addons_include": 0, "logging_enabled": 0}


def create_zip(source: Path, archive: Path, relative_paths: list[str]) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for relative in sorted(relative_paths):
            path = source / relative
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def create_source_review(output: Path, archive: Path) -> dict:
    selected = (
        "tools/build_rmod2_public_release.py", "tools/build_rmod2_boot_b.py",
        "tools/build_rmod2_boot_a.py", "tools/build_r_mod1_candidate.py",
        "tools/r_mod1_native_plan.py", "tools/audit_dinput8_exports.py",
        "tools/r_mod1_core_tests.ps1",
        "src/native/rmod1/core.hpp", "src/native/rmod1/dinput8_proxy.cpp",
        "src/native/rmod1/dinput8_proxy.def", "src/native/rmod1/rmod2_inprocess.cpp",
        "src/native/rmod1/rmod2_inprocess.hpp", "src/native/rmod1/runtime_core.cpp",
        "src/native/rmod1/runtime_core.def", "src/native/rmod1/runtime_image_diff.hpp",
        "src/native/rmod1/rmod2_startup_preflight.hpp",
        "tests/rmod1/core_tests.cpp", "tests/rmod1/dinput8_forward_harness.cpp",
        "tests/rmod1/rmod2_boot_b_harness.cpp",
        "tests/rmod1/rmod2_host_qualified_preflight_harness.cpp",
        "tests/rmod1/runtime_image_diff_harness.cpp",
        "tests/synthetic/test_r_mod1_core.py",
        "tests/synthetic/test_r_mod1_native_plan.py", "tests/synthetic/test_r_mod2_boot_b.py",
        "tests/synthetic/test_r_mod2_dinput8.py", "tests/synthetic/test_r_mod2_public_release.py",
        "README.md", "LICENSE", "research/r-mod1/MRallyeRandomizer.release.ini",
        "research/r-mod1/public/README.md", "research/r-mod1/public/CHANGELOG.md",
        "research/r-mod1/configuration.md", "research/r-mod1/rmod2-boot-b.md",
        "research/r-mod1/rmod2-boot-b-validation.md", "research/r-mod1/bootstrap-and-renderer-compat.md",
        "docs/releases/master-rallye-randomizer-v0.1.0-beta.1.md",
        "docs/INSTALLATION.md", "docs/CONFIGURATION.md", "docs/LIVE_RELOAD.md",
        "docs/COMPATIBILITY.md", "docs/TROUBLESHOOTING.md",
    )
    missing = [relative for relative in selected if not (ROOT / relative).is_file()]
    if missing:
        raise ReleaseError(f"source-review inputs are missing: {missing}")
    with tempfile.TemporaryDirectory(prefix="rmod-public-review-") as temp_name:
        temp = Path(temp_name)
        for relative in selected:
            target = temp / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        readme = (
            "# R-MOD2 source review package\n\n"
            "This archive contains selected source, tests, and public documentation for the standalone beta. "
            "It contains no game executable, game assets, runtime DLLs, raw captures, or user saves.\n\n"
            "## Reproduction\n\n"
            "1. Use the complete repository checkout and the exact supported retail executable supplied by the owner.\n"
            "2. Build/verify the BOOT-B candidate with `python tools/build_rmod2_boot_b.py --output <new-output>`.\n"
            "3. Build the player package with `python tools/build_rmod2_public_release.py --candidate-dir <BOOT-B-test-package> --output <new-output>`.\n"
            "4. The packager invokes the x86 C++ core/parser checks against the release INI and emits file hashes.\n\n"
            "The runtime uses the exact retail hash in the source and fails closed on other executable builds. "
            "The proprietary executable and assets must be obtained separately from a legitimate game installation.\n"
        )
        (temp / "REPRODUCE.md").write_text(readme, encoding="utf-8", newline="\n")
        file_rows = []
        for path in sorted(p for p in temp.rglob("*") if p.is_file()):
            file_rows.append({"path": path.relative_to(temp).as_posix(), "size": path.stat().st_size,
                              "sha256": sha256(path)})
        metadata = {
            "branch": subprocess.run(["git", "branch", "--show-current"], cwd=ROOT,
                                      capture_output=True, text=True, check=True).stdout.strip(),
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                        capture_output=True, text=True, check=True).stdout.strip(),
            "working_tree_at_packaging": "contains prior research changes; this archive uses an explicit allowlist",
            "files": file_rows,
        }
        (temp / "archive-index.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                                                   encoding="utf-8", newline="\n")
        names = [p.relative_to(temp).as_posix() for p in temp.rglob("*") if p.is_file()]
        create_zip(temp, archive, names)
    return {"path": archive.name, "size": archive.stat().st_size, "sha256": sha256(archive)}


def build(candidate: Path, output: Path) -> dict:
    candidate = candidate.resolve()
    output = output.resolve()
    if output.exists():
        raise ReleaseError(f"refusing to overwrite output: {output}")
    proxy = candidate / "dinput8.dll"
    runtime = candidate / "MRallyeRandomizerRuntime.dll"
    if not proxy.is_file() or not runtime.is_file():
        raise ReleaseError("candidate must contain the BOOT-B DirectInput proxy and runtime DLL")
    if sha256(proxy) != PROXY_SHA256 or sha256(runtime) != RUNTIME_SHA256:
        raise ReleaseError("candidate DLL identity differs from the owner-tested BOOT-B build")
    if pe_machine(proxy) != 0x14C or pe_machine(runtime) != 0x14C:
        raise ReleaseError("release DLLs must be PE32/I386")
    if parse_exports(proxy.read_bytes()) != DINPUT_EXPORTS:
        raise ReleaseError("DirectInput proxy export names/ordinals differ from the forwarding contract")
    manifest_path = candidate.parent / "candidate-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("retail_executable_sha256") != RETAIL_SHA256 or manifest.get("renderer_proxy_modified") is not False:
        raise ReleaseError("candidate manifest does not describe the exact retail/d3d8-safe build")

    release_ini = ROOT / "research/r-mod1/MRallyeRandomizer.release.ini"
    ini_check = audit_release_ini(release_ini)
    # Exercise the real C++ parser against the release file, not a Python clone.
    ps_script = ROOT / "tools/r_mod1_core_tests.ps1"
    result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                             "-File", str(ps_script), "-PublicIniPath", str(release_ini)],
                            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ReleaseError("C++ parser/core validation failed:\n" + result.stdout[-8000:])
    output.mkdir(parents=True)
    package = output / "package"
    package.mkdir()
    shutil.copyfile(proxy, package / "dinput8.dll")
    shutil.copyfile(runtime, package / "MRallyeRandomizerRuntime.dll")
    shutil.copyfile(release_ini, package / "MRallyeRandomizer.ini")
    for relative in PUBLIC_FILES:
        if relative == "MRallyeRandomizer.ini":
            continue
        src = ROOT / relative if relative != "README.md" and relative != "CHANGELOG.md" else ROOT / "research/r-mod1/public" / relative
        if relative == "LICENSE":
            src = ROOT / "LICENSE"
        if not src.is_file():
            raise ReleaseError(f"missing public document: {src}")
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, destination)

    file_records = []
    for path in sorted(p for p in package.rglob("*") if p.is_file()):
        rel = path.relative_to(package).as_posix()
        file_records.append({"path": rel, "size": path.stat().st_size, "sha256": sha256(path)})
    sums = "".join(f"{row['sha256']}  {row['path']}\n" for row in file_records)
    (package / "SHA256SUMS.txt").write_text(sums, encoding="ascii", newline="\n")
    file_records.append({"path": "SHA256SUMS.txt", "size": (package / "SHA256SUMS.txt").stat().st_size,
                         "sha256": sha256(package / "SHA256SUMS.txt")})
    public_manifest = {
        "product": "Master Rallye Randomizer & AI Extender",
        "version": "0.1.0-beta.1",
        "supported_retail_executable_sha256": RETAIL_SHA256,
        "installation": "Extract beside the original MRallye.exe; run the game normally.",
        "on_disk_executable_modified": False,
        "graphical_d3d8_proxy_included_or_modified": False,
        "dlls": {"dinput8.dll": PROXY_SHA256, "MRallyeRandomizerRuntime.dll": RUNTIME_SHA256},
        "ini": ini_check,
        "known_issue": "Some seven-AI T1/T2-player Quick Races have shown instability; cause unknown.",
        "files": file_records,
    }
    (package / "release-manifest.json").write_text(json.dumps(public_manifest, indent=2, sort_keys=True) + "\n",
                                                     encoding="utf-8", newline="\n")
    members = [p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()]
    archive = output / RELEASE_NAME
    create_zip(package, archive, members)
    expected_files = {"dinput8.dll", "MRallyeRandomizerRuntime.dll", "MRallyeRandomizer.ini",
                      "README.md", "CHANGELOG.md", "LICENSE", "SHA256SUMS.txt", "release-manifest.json",
                      "docs/INSTALLATION.md", "docs/CONFIGURATION.md", "docs/LIVE_RELOAD.md",
                      "docs/COMPATIBILITY.md", "docs/TROUBLESHOOTING.md"}
    with zipfile.ZipFile(archive) as zf:
        if set(zf.namelist()) != expected_files:
            raise ReleaseError("release ZIP content set differs from the audited allowlist")
        prohibited = (".exe", ".sma", ".dx", ".dxt", ".gxm", ".gxi", ".dump", ".bin")
        if any(name.lower().endswith(prohibited) for name in zf.namelist()):
            raise ReleaseError("release ZIP contains a prohibited game binary, asset, or dump")
        for name in zf.namelist():
            if b"D:\\Game\\" in zf.read(name) or b"C:\\Users\\" in zf.read(name):
                raise ReleaseError(f"machine-specific path found in package file: {name}")
        archive_records = [{"path": name, "size": len(zf.read(name)),
                            "sha256": hashlib.sha256(zf.read(name)).hexdigest()}
                           for name in sorted(zf.namelist())]
    review_archive = output / "r-mod2-public-release-source-review.zip"
    review = create_source_review(output, review_archive)
    (output / "github-release-draft.md").write_text(
        "# Draft GitHub release\n\n"
        "**Title:** Master Rallye Randomizer & AI Extender v0.1.0-beta.1\n\n"
        "**Description:**\n\n"
        "First beta of the standalone Master Rallye Randomizer & AI Extender. "
        "Configure AI vehicle policies for Quick Race, Rallye Cup, Master Rallye, Invitation, and Challenge; "
        "select up to five AI opponents in Quick Race by default. The package uses the original retail "
        "executable without modifying it and is designed to coexist with the existing graphical d3d8.dll.\n\n"
        "This beta supports only the exact retail executable identified in the included compatibility notes. "
        "Seven-AI Quick Races have shown instability with some T1/T2 player-car setups; the cause is unknown. "
        "Review the included installation, configuration, compatibility, and troubleshooting guides before use.\n\n"
        "This is an unofficial fan-made modification. No game executable or game assets are included.\n",
        encoding="utf-8", newline="\n")
    external_manifest = {
        "release_zip": archive.name, "release_zip_size": archive.stat().st_size,
        "release_zip_sha256": sha256(archive), "source_review": review,
        "public_package_files": archive_records,
    }
    (output / "release-candidate-manifest.json").write_text(
        json.dumps(external_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"package_dir": str(package), "release_zip": str(archive),
            "release_zip_sha256": sha256(archive), "release_zip_size": archive.stat().st_size,
            "runtime_core_sha256": RUNTIME_SHA256, "proxy_sha256": PROXY_SHA256,
            "retail_sha256": RETAIL_SHA256, "ini_bytes": ini_check["bytes"],
            "cpp_parser_test": result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "passed",
            "file_count": len(expected_files), "source_review_zip": str(review_archive),
            "source_review_sha256": review["sha256"], "source_review_size": review["size"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        report = build(args.candidate_dir, args.output)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"release build failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
