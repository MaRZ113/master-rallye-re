#!/usr/bin/env python3
"""Reproducible build of the Master Rallye Menu Builder.

Products (under --output, default .research-output/menu-builder/<name>):
  editor/            MenuBuilder.exe (WPF editor) + mrmenu.exe (CLI/API), framework-dependent .NET 8
  native/standalone/dinput8.dll   loader with the Menu Builder runtime only (plus the stock Randomizer boot path)
  native/integrated/dinput8.dll   the EXTRA-SET2 Extra Options/SDK loader + Menu Builder runtime (same flags as
                                  tools/build_extra_sdk_binding.py, plus /DRMOD_MENU_BUILDER=1)
  build-manifest.json             hashes of every product and of the sources used

The generated headers of the Extra Options build (native_plan.hpp, extra_sdk_profile.hpp,
extra_options_package.hpp) are owner-local inputs; pass the include directory of an existing
EXTRA-SET2 proxy build with --include. Retail data and binaries are never copied into the repository.
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
DEFAULT_INCLUDE = Path(r"D:\Game\Master Rallye\master-rallye-re-rmod1\.research-output\extra-set1\extra-set2-03\proxy\include")
MENU_EXPORTS = ("    MRMenuAbiV1=_MRMenuAbiV1@0 @13\n"
                "    MRMenuRegisterActionV1=_MRMenuRegisterActionV1@8 @14\n"
                "    MRMenuQueryV1=_MRMenuQueryV1@8 @15\n")
EXTRA_EXPORTS = ("    MRExtraSdkBindingAbi=_MRExtraSdkBindingAbi@0 @7\n"
                 "    MRExtraOptionsAbi=_MRExtraOptionsAbi@0 @8\n"
                 "    MRExtraVisualV1=_MRExtraVisualV1@12 @9\n"
                 "    MRExtraRevisionV1=_MRExtraRevisionV1@12 @10\n"
                 "    MRExtraTextureV1=_MRExtraTextureV1@36 @11\n"
                 "    MRExtraVisualV2=_MRExtraVisualV2@12 @12\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_native(out: Path, include: Path, integrated: bool) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    vcvars, msvc = locate_toolchain()
    env = compiler_environment(vcvars, "x64_x86")
    base_def = (NATIVE / "dinput8_proxy.def").read_text(encoding="ascii").rstrip() + "\n"
    definition = out / "dinput8.def"
    definition.write_text(base_def + (EXTRA_EXPORTS if integrated else "") + MENU_EXPORTS, encoding="ascii")
    dll = out / "dinput8.dll"
    command = [str(msvc / "bin/Hostx64/x86/cl.exe"), "/nologo", "/LD", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
               "/Brepro", "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800",
               "/DRMOD_MENU_BUILDER=1", "/I" + str(include), "/I" + str(NATIVE),
               str(NATIVE / "dinput8_proxy.cpp"), str(NATIVE / "rmod2_inprocess.cpp"), str(NATIVE / "menu_builder_runtime.cpp")]
    if integrated:
        command[1:1] = ["/DRMOD_EXTRA_OPTIONS=1", "/DRMOD_EXTRA_SDK_BINDING=1"]
        command += [str(NATIVE / "extra_options_runtime.cpp"), str(NATIVE / "extra_ghost.cpp")]
    command += ["/link", "/DEF:" + str(definition), "bcrypt.lib", "user32.lib", "gdi32.lib", "/NOIMPLIB", "/Brepro", "/OUT:" + str(dll)]
    subprocess.run(command, cwd=out, env=env, check=True)
    for obj in out.glob("*.obj"):
        obj.unlink()
    return dll


def build_editor(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    for project in ("MenuBuilder.App", "MenuBuilder.Cli"):
        subprocess.run(["dotnet", "publish", str(SOLUTION / project), "-c", "Release", "-o", str(out),
                        "--nologo", "-p:DebugType=none", "-p:Deterministic=true"], check=True)
    return sorted(p for p in out.iterdir() if p.is_file())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", default="mb-01")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--include", type=Path, default=DEFAULT_INCLUDE, help="generated headers of an EXTRA-SET2 proxy build")
    ap.add_argument("--skip-editor", action="store_true")
    ap.add_argument("--skip-native", action="store_true")
    a = ap.parse_args()
    out = a.output or ROOT / ".research-output/menu-builder" / a.name
    if out.exists():
        shutil.rmtree(out)
    manifest: dict = {"schema": "menu-builder-build/1", "name": a.name, "products": {}, "sources": {}}
    if not a.skip_native:
        if not (a.include / "native_plan.hpp").is_file():
            raise SystemExit(f"{a.include} has no native_plan.hpp (pass --include of an EXTRA-SET2 proxy build)")
        for kind in ("standalone", "integrated"):
            dll = build_native(out / "native" / kind, a.include, kind == "integrated")
            manifest["products"][f"native/{kind}/dinput8.dll"] = sha(dll)
        manifest["include"] = {p.name: sha(p) for p in sorted(a.include.glob("*.hpp"))}
    if not a.skip_editor:
        for f in build_editor(out / "editor"):
            if f.suffix.lower() in (".exe", ".dll"):
                manifest["products"][f"editor/{f.name}"] = sha(f)
    for src in sorted([*NATIVE.glob("menu_builder_runtime.*"), NATIVE / "dinput8_proxy.cpp", NATIVE / "extra_options_runtime.cpp",
                       *SOLUTION.rglob("*.cs"), *SOLUTION.rglob("*.xaml"), *SOLUTION.rglob("*.csproj")]):
        if "obj" in src.parts or "bin" in src.parts:
            continue
        manifest["sources"][str(src.relative_to(ROOT)).replace("\\", "/")] = sha(src)
    (out / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "sources"}, indent=2))
    print(out)


if __name__ == "__main__":
    main()
