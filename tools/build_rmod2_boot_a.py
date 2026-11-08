#!/usr/bin/env python3
"""Build and verify the R-MOD2 BOOT-A DirectInput proxy test artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from build_r_mod1_candidate import compiler_environment, locate_toolchain
from audit_dinput8_exports import EXPECTED, audit

ROOT = Path(__file__).resolve().parents[1]
VSWHERE = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")


class BuildError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], *, env: dict[str, str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, check=False)
    output = (result.stdout or "") + (result.stderr or "")
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    if result.returncode:
        raise BuildError(f"command failed ({result.returncode}): {args[0]}")
    return output


def locate_tools() -> tuple[Path, Path, Path]:
    vcvars, msvc_root = locate_toolchain()
    compiler = msvc_root / "bin" / "Hostx64" / "x86" / "cl.exe"
    dumpbin = msvc_root / "bin" / "Hostx64" / "x86" / "dumpbin.exe"
    if not compiler.is_file() or not dumpbin.is_file():
        raise BuildError("MSVC x86 compiler/dumpbin are required")
    return vcvars, compiler, dumpbin


def zip_tree(root: Path, output: Path, relative_files: list[str]) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(relative_files):
            path = root / relative
            info = zipfile.ZipInfo(relative.replace("\\", "/"), date_time=(2026, 10, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def build(output: Path) -> dict:
    output = Path(os.path.abspath(output))
    if output.exists():
        raise BuildError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    work = output / "build"
    work.mkdir()
    package = output / "MasterRallye-Randomizer-BOOT-A-Test"
    package.mkdir()

    vcvars, compiler, dumpbin = locate_tools()
    env = compiler_environment(vcvars, "x64_x86")
    proxy = work / "dinput8.dll"
    harness = work / "dinput8_forward_harness.exe"
    proxy_source = ROOT / "src/native/rmod1/dinput8_proxy.cpp"
    proxy_def = ROOT / "src/native/rmod1/dinput8_proxy.def"
    harness_source = ROOT / "tests/rmod1/dinput8_forward_harness.cpp"

    run([str(compiler), "/nologo", "/LD", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
         "/Brepro", "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800", str(proxy_source),
         "/link", "/DEF:" + str(proxy_def), "/NOIMPLIB", "/Brepro", "/OUT:" + str(proxy)], env=env, cwd=work)
    run([str(compiler), "/nologo", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
         "/Brepro", "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800", str(harness_source),
         "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "/OUT:" + str(harness)], env=env, cwd=work)

    exports = audit(proxy)
    # The binary identity is the durable evidence; omit the absolute build path
    # so the review evidence stays portable and byte-reproducible across runs.
    exports.pop("path", None)
    exports["sha256"] = sha(proxy)
    audit_path = work / "proxy-export-audit.json"
    audit_path.write_text(json.dumps(exports, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    dump = run([str(dumpbin), "/headers", str(proxy)], env=env, cwd=work)
    if "14C machine (x86)" not in dump and "14C machine (x86)" not in dump.upper():
        raise BuildError("dumpbin did not identify an I386 proxy DLL")
    imports = run([str(dumpbin), "/imports", str(proxy)], env=env, cwd=work)
    if re.search(r"(?im)^\s*dinput8\.dll\s*$", imports):
        raise BuildError("proxy has a static import of dinput8.dll and would recurse")
    test_output = run([str(harness), str(proxy)], env=env, cwd=work)
    if "DINPUT8_FORWARD_PASS named=6 ordinal=6 directinput8create=system-match joystick-format=system-match" not in test_output:
        raise BuildError("Windows DirectInput forwarding harness did not report PASS")
    (work / "forward-harness.txt").write_text(test_output, encoding="utf-8", newline="\n")

    shutil.copyfile(proxy, package / "dinput8.dll")
    (package / "README.txt").write_text(
        "MASTER RALLYE R-MOD2 BOOT-A TEST ARTIFACT\n\n"
        "This checkpoint tests only the launcher-free x86 DirectInput proxy.\n"
        "It forwards DirectInput exports to the Windows system DLL and does not\n"
        "install Randomizer gameplay hooks. It is not a gameplay mod or release.\n\n"
        "For the human test, use a disposable copy of the exact retail game folder.\n"
        "Do not overwrite an existing dinput8.dll from another mod. Extract this\n"
        "single dinput8.dll beside MRallye.exe, then launch MRallye.exe normally.\n"
        "Test first without a graphics proxy, then with the existing d3d8.dll left\n"
        "unchanged. Verify keyboard/gamepad navigation, graphics, race loading,\n"
        "Results, exit and a second launch. Remove only this dinput8.dll afterward.\n"
        "The Randomizer remains inactive in this BOOT-A checkpoint.\n",
        encoding="ascii", newline="\n")
    release_files = ["dinput8.dll", "README.txt"]
    package_rows = [{"path": name, "size": (package / name).stat().st_size,
                     "sha256": sha(package / name)} for name in release_files]
    manifest = {
        "candidate": "r-mod2-boot-a-dinput8-forwarding-test",
        "checkpoint": "BOOT-A",
        "qualification": "STATIC_AND_WINDOWS_FORWARDING_HARNESS_PASS_HUMAN_GAME_TEST_PENDING",
        "retail_executable_sha256": "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",
        "proxy_architecture": "PE32/I386",
        "proxy_sha256": sha(proxy),
        "forwarded_exports": EXPECTED,
        "gameplay_hooks_installed": False,
        "renderer_proxy_modified": False,
        "package_files": package_rows,
        "windows_harness": test_output.strip(),
        "human_game_runtime": "PENDING",
    }
    (output / "candidate-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                                                      encoding="utf-8", newline="\n")
    zip_path = output / "MasterRallye-Randomizer-BOOT-A-Test.zip"
    zip_tree(package, zip_path, release_files)

    review_files = [
        "src/native/rmod1/dinput8_proxy.cpp", "src/native/rmod1/dinput8_proxy.def",
        "tests/rmod1/dinput8_forward_harness.cpp", "tests/synthetic/test_r_mod2_dinput8.py",
        "tools/audit_dinput8_exports.py", "tools/build_rmod2_boot_a.py",
        "research/r-mod1/rmod2-boot-a.md", "research/r-mod1/rmod2-boot-a-validation.md",
    ]
    review_root = output / "review-source"
    for relative in review_files:
        target = review_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    shutil.copyfile(audit_path, review_root / "proxy-export-audit.json")
    shutil.copyfile(work / "forward-harness.txt", review_root / "forward-harness.txt")
    status = subprocess.run(["git", "status", "--short", "--branch"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()
    (review_root / "git-state.txt").write_text(f"HEAD={head}\n{status}", encoding="utf-8", newline="\n")
    review_rows = []
    for path in sorted(p for p in review_root.rglob("*") if p.is_file()):
        review_rows.append({"path": path.relative_to(review_root).as_posix(),
                            "size": path.stat().st_size, "sha256": sha(path)})
    (review_root / "archive-index.json").write_text(
        json.dumps({"schema_version": 1, "files": review_rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    review_zip = output / "r-mod2-boot-a-implementation-review.zip"
    review_relative = [p.relative_to(review_root).as_posix() for p in review_root.rglob("*") if p.is_file()]
    zip_tree(review_root, review_zip, review_relative)
    manifest["candidate_zip_sha256"] = sha(zip_path)
    manifest["review_zip_sha256"] = sha(review_zip)
    (output / "candidate-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                                                      encoding="utf-8", newline="\n")
    return {"candidate": manifest["candidate"], "output": str(output),
            "proxy_sha256": manifest["proxy_sha256"], "package_zip_sha256": manifest["candidate_zip_sha256"],
            "review_zip_sha256": manifest["review_zip_sha256"], "forwarding_test": test_output.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output), indent=2, sort_keys=True))
    except (BuildError, OSError, subprocess.SubprocessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
