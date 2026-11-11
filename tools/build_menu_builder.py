#!/usr/bin/env python3
"""Reproducible build of the Master Rallye Menu Builder (MENU-STUDIO1).

Products (under --output, default .research-output/menu-builder/<name>):
  editor/                          MenuBuilder.exe (WPF editor) + mrmenu.exe (CLI/API), framework-dependent .NET 8
  native/standalone/dinput8.dll    Menu Builder runtime only (no Randomizer plan, no Vehicle Manager roster, no
                                   Extra Options); compiled from the repository sources alone
  native/integrated/               the CURRENT Extra Options loader of this branch with the Menu Builder runtime
                                   linked in (tools/build_extra_capacity_candidate.py --menu-builder: roster-independent
                                   V-CAP3/Roster V4 loader, Ghost, five difficulties, tyres, PS2/PC/DEMO MODEL,
                                   Randomizer boot) + its runtime core MRallyeRandomizerRuntime.dll
  build-manifest.json              commit, dirty state, hashes of every product and of the sources used

No generated header of an older Extra Options build (EXTRA-SET2 / SDK33) is used. Nothing is installed into a game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_r_mod1_candidate import compiler_environment, locate_toolchain  # noqa: E402

NATIVE = ROOT / "src/native/rmod1"
SOLUTION = ROOT / "tools/menu-builder"
MENU_EXPORTS = ("    MRMenuAbiV1=_MRMenuAbiV1@0 @14\n"
                "    MRMenuRegisterActionV1=_MRMenuRegisterActionV1@8 @15\n"
                "    MRMenuQueryV1=_MRMenuQueryV1@8 @16\n"
                "    MRMenuAbiV2=_MRMenuAbiV2@0 @17\n"
                "    MRMenuRegisterValueV1=_MRMenuRegisterValueV1@8 @18\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def build_standalone(out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    vcvars, msvc = locate_toolchain()
    env = compiler_environment(vcvars, "x64_x86")
    definition = out / "dinput8.def"
    definition.write_text((NATIVE / "dinput8_proxy.def").read_text(encoding="ascii").rstrip() + "\n" + MENU_EXPORTS, encoding="ascii")
    dll = out / "dinput8.dll"
    command = [str(msvc / "bin/Hostx64/x86/cl.exe"), "/nologo", "/LD", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
               "/Brepro", "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800",
               "/DRMOD_MENU_BUILDER=1", "/DRMOD_MENU_BUILDER_STANDALONE=1", "/I" + str(NATIVE),
               str(NATIVE / "dinput8_proxy.cpp"), str(NATIVE / "menu_builder_runtime.cpp"),
               "/link", "/DEF:" + str(definition), "user32.lib", "gdi32.lib", "/NOIMPLIB", "/Brepro", "/OUT:" + str(dll)]
    subprocess.run(command, cwd=out, env=env, check=True)
    for obj in out.glob("*.obj"):
        obj.unlink()
    return dll


def build_integrated(out: Path, name: str, core: Path | None) -> dict:
    """The current Extra Options loader pipeline with --menu-builder (fresh isolated output under extra-set1)."""
    from build_extra_capacity_candidate import build as capacity_build  # noqa: E402
    work = ROOT / ".research-output/extra-set1" / f"menu-{name}"
    if work.exists():
        shutil.rmtree(work)
    report = capacity_build(work, None, None, menu_builder=True)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(work / "proxy/dinput8.dll", out / "dinput8.dll")
    # The runtime core is a separate product of the same pipeline; --core ships an already published, owner-tested
    # binary of the same sources instead of this build's copy (the loader does not pin the core hash with Extra Options).
    shutil.copyfile(core or work / "core/MRallyeRandomizerRuntime.dll", out / "MRallyeRandomizerRuntime.dll")
    shutil.copyfile(work / "capacity-build.json", out / "capacity-build.json")
    return report


def build_editor(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    for project in ("MenuBuilder.App", "MenuBuilder.Cli"):
        subprocess.run(["dotnet", "publish", str(SOLUTION / project), "-c", "Release", "-o", str(out),
                        "--nologo", "-p:DebugType=none", "-p:Deterministic=true"], check=True)
    return sorted(p for p in out.iterdir() if p.is_file())


README = r"""MASTER RALLYE MENU BUILDER 1.1 (MENU-STUDIO1) - private test package
=====================================================================

Editor\MenuBuilder.exe          WYSIWYG editor (needs the .NET 8 Desktop Runtime, x64)
Editor\mrmenu.exe               command line / JSON API; Editor\python\mr_menu_builder.py wraps it
Runtime\integrated\             dinput8.dll + MRallyeRandomizerRuntime.dll: the current Extra Options loader of
                                integration/base (Vehicle Registry / Roster V4, Randomizer, Ghost, five difficulties,
                                tyres, PS2/PC/DEMO MODEL) WITH the Menu Builder runtime. Replaces the loader pair of a
                                Definitive Edition install (keep a backup of yours).
Runtime\standalone\dinput8.dll  Menu Builder runtime only, for a plain retail install (no Extra Options/roster).
Examples\demo.mrmenu.json       qualification layout (MAIN MENU, OPTIONS > MENU BUILDER, QUICK RACE > VEHICLE CONFIG)
Docs\                           user guide, project schema, MENU-STUDIO1 report
Tests\                          in-game autotests + runners for an isolated copy of the game
Evidence\                       logs and screenshots of the qualification runs
BUILD-PROVENANCE.json           commit, hashes and build inputs of every binary

Nothing in this package installs itself. To try it:
 1. Back up dinput8.dll and MRallyeRandomizerRuntime.dll of the game folder.
 2. Copy Runtime\integrated\* (Definitive Edition) or Runtime\standalone\dinput8.dll (plain retail) next to MRallye.exe.
 3. Start Editor\MenuBuilder.exe, pick the game folder, open Examples\demo.mrmenu.json (or create a project).
 4. Game > Install & activate layout (F8). Layouts go to <game>\MenuBuilder\Layouts\<name> (transactional; a failed
    install keeps the previous layout). Game > Switch to Classic menus restores the native frontend.
Logs: <game>\MenuBuilder\MenuBuilder.log, live dumps: <game>\MenuBuilder\live\<screen>.txt
"""


def assemble_package(out: Path, evidence: Path, manifest: dict) -> dict:
    pkg = out / "package"
    if pkg.exists():
        shutil.rmtree(pkg)
    (pkg / "Runtime/standalone").mkdir(parents=True)
    shutil.copytree(out / "editor", pkg / "Editor")
    shutil.copytree(SOLUTION / "python", pkg / "Editor/python", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(out / "native/integrated", pkg / "Runtime/integrated", ignore=shutil.ignore_patterns("*.json"))
    shutil.copyfile(out / "native/standalone/dinput8.dll", pkg / "Runtime/standalone/dinput8.dll")
    (pkg / "Examples").mkdir()
    shutil.copyfile(ROOT / "examples/menu-builder/demo.mrmenu.json", pkg / "Examples/demo.mrmenu.json")
    (pkg / "Docs").mkdir()
    for doc in ("docs/menu-builder.md", "docs/menu-builder/project.schema.json", "docs/menu-builder/MENU-STUDIO1-REPORT.md"):
        if (ROOT / doc).is_file():
            shutil.copyfile(ROOT / doc, pkg / "Docs" / Path(doc).name)
    shutil.copytree(SOLUTION / "test", pkg / "Tests")
    if evidence.is_dir():
        shutil.copytree(evidence, pkg / "Evidence")
    (pkg / "README.txt").write_text(README, encoding="ascii")
    (pkg / "BUILD-PROVENANCE.json").write_text(json.dumps({k: v for k, v in manifest.items() if k != "sources"}, indent=2) + "\n", encoding="utf-8")
    return {str(p.relative_to(pkg)).replace("\\", "/"): sha(p) for p in sorted(pkg.rglob("*"))
            if p.is_file() and p.suffix.lower() in (".exe", ".dll", ".json", ".py", ".md", ".txt")
            and "Evidence" not in p.parts}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", default="mb-1.1")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--skip-editor", action="store_true")
    ap.add_argument("--skip-native", action="store_true")
    ap.add_argument("--package", action="store_true", help="assemble package/ (editor, runtimes, example, docs, tests, evidence)")
    ap.add_argument("--evidence", type=Path, default=ROOT / ".research-output/menu-evidence")
    ap.add_argument("--core", type=Path, help="MRallyeRandomizerRuntime.dll to ship with the integrated loader (default: rebuilt)")
    a = ap.parse_args()
    out = a.output or ROOT / ".research-output/menu-builder" / a.name
    if out.exists():
        shutil.rmtree(out)
    manifest: dict = {"schema": "menu-builder-build/2", "name": a.name, "builder_version": "1.1.0",
                      "commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                      "dirty": bool(git("status", "--porcelain", "--untracked-files=no")), "products": {}, "sources": {}}
    if not a.skip_native:
        dll = build_standalone(out / "native/standalone")
        manifest["products"]["native/standalone/dinput8.dll"] = sha(dll)
        report = build_integrated(out / "native/integrated", a.name, a.core)
        for f in ("dinput8.dll", "MRallyeRandomizerRuntime.dll"):
            manifest["products"][f"native/integrated/{f}"] = sha(out / "native/integrated" / f)
        manifest["integrated_pipeline"] = {"tool": "tools/build_extra_capacity_candidate.py --menu-builder (roster-independent)",
                                           "sdk_binding": report.get("sdk_binding"),
                                           "runtime_core": {"source": str(a.core) if a.core else "rebuilt by the pipeline",
                                                            "rebuilt_sha256": report.get("sdk_binding", {}).get("runtime_core_sha256"),
                                                            "shipped_sha256": sha(out / "native/integrated/MRallyeRandomizerRuntime.dll")}}
    if not a.skip_editor:
        for f in build_editor(out / "editor"):
            if f.suffix.lower() in (".exe", ".dll"):
                manifest["products"][f"editor/{f.name}"] = sha(f)
    for src in sorted([*NATIVE.glob("*.cpp"), *NATIVE.glob("*.hpp"), *SOLUTION.rglob("*.cs"), *SOLUTION.rglob("*.xaml"),
                       *SOLUTION.rglob("*.csproj"), ROOT / "tools/build_menu_builder.py", ROOT / "tools/build_extra_sdk_binding.py"]):
        if "obj" in src.parts or "bin" in src.parts:
            continue
        manifest["sources"][str(src.relative_to(ROOT)).replace("\\", "/")] = sha(src)
    if a.package:
        manifest["package"] = assemble_package(out, a.evidence, manifest)
    (out / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("sources", "package")}, indent=2))
    print(out)


if __name__ == "__main__":
    main()
