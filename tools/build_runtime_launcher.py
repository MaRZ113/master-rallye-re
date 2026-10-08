#!/usr/bin/env python3
"""Build the x64 Windows J.1 launcher for one verified runtime bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import addon_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / ".research-output/vehicles/sdk/j1/launcher-release"


class LauncherBuildError(RuntimeError):
    pass


def _header(profile: dict[str, Any], patch_manifest: dict[str, Any]) -> bytes:
    values = {
        "MR_RETAIL_SHA256": profile["retail_exe"]["sha256"],
        "MR_ADDON_PLAN_SHA256": profile["addon_plan_sha256"],
        "MR_PATCH_MANIFEST_SHA256": profile["native_patch_manifest_sha256"],
        "MR_PATCH_OPS_SHA256": profile["native_patch_operations_sha256"],
        "MR_RESOURCE_MANIFEST_SHA256": profile["resource_manifest_sha256"],
        "MR_RESOURCE_INDEX_SHA256": profile["resource_index_sha256"],
        "MR_REFERENCE_IMAGE_SHA256": profile["reconstructed_reference_file_sha256"],
    }
    for key, value in values.items():
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise LauncherBuildError(f"invalid trusted-profile value: {key}")
    operation_count = len(patch_manifest.get("operations", []))
    resource_count = profile.get("resource_count")
    if type(operation_count) is not int or not 1 <= operation_count <= 512:
        raise LauncherBuildError("native operation count is outside launcher bounds")
    if type(resource_count) is not int or resource_count <= 0:
        raise LauncherBuildError("invalid trusted resource count")
    rows = ["#pragma once", "// Generated from the independently verified J.1 bundle."]
    rows.extend(f'#define {key} "{value}"' for key, value in sorted(values.items()))
    rows.extend((f"#define MR_PATCH_OPERATION_COUNT {operation_count}u",
                 f"#define MR_RESOURCE_COUNT {resource_count}u"))
    return ("\n".join(rows) + "\n").encode("ascii")


def build_launcher(*, bundle: Path, output: Path = DEFAULT_OUTPUT,
                   retail_exe: Path | None = None,
                   generator: str = "Visual Studio 18 2026") -> dict[str, Any]:
    if os.name != "nt":
        raise LauncherBuildError("the native launcher can only be built on Windows")
    bundle = Path(bundle)
    retail_exe = Path(retail_exe or addon_runtime.DEFAULT_RETAIL_EXE).resolve()
    verified = addon_runtime.verify_bundle(bundle, retail_exe=retail_exe)
    output = addon_runtime._under_research_output(Path(output))
    profile = json.loads((bundle / "runtime-profile.json").read_text(encoding="utf-8"))
    patch_manifest = json.loads((bundle / "native-patch-manifest.json").read_text(encoding="utf-8"))
    if verified.get("status") != "PASS_STATIC_RUNTIME_BUNDLE" or verified.get("runtime_qualified") is not False:
        raise LauncherBuildError("bundle is not a statically verified, unqualified runtime candidate")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        include_dir = stage / "generated"
        include_dir.mkdir()
        (include_dir / "trusted_profile.hpp").write_bytes(_header(profile, patch_manifest))
        build_dir = stage / "cmake-build"
        configure = ["cmake", "-S", str(PROJECT_ROOT / "runtime_launcher"), "-B", str(build_dir),
                     "-G", generator, "-A", "x64", f"-DPROFILE_INCLUDE_DIR={include_dir}"]
        subprocess.run(configure, check=True)
        subprocess.run(["cmake", "--build", str(build_dir), "--config", "Release",
                        "--target", "mr-runtime-launcher"], check=True)
        candidates = list(build_dir.rglob("mr-runtime-launcher.exe"))
        if len(candidates) != 1 or not candidates[0].is_file():
            raise LauncherBuildError("CMake did not produce exactly one launcher executable")
        launcher = stage / "mr-runtime-launcher.exe"
        shutil.copyfile(candidates[0], launcher)
        data = launcher.read_bytes()
        if len(data) < 4096 or data[:2] != b"MZ":
            raise LauncherBuildError("built launcher does not look like a Windows executable")
        metadata = {
            "schema_version": 1,
            "artifact_kind": "native external runtime launcher build",
            "status": "STATIC_BUILD_ONLY_NOT_RUNTIME_QUALIFIED",
            "architecture": "x64 launcher / x86 target process",
            "generator": generator,
            "launcher_sha256": hashlib.sha256(data).hexdigest(),
            "launcher_size": len(data),
            "bundle_profile": profile["profile"],
            "bundle_verified_status": verified["status"],
            "retail_exe_sha256": profile["retail_exe"]["sha256"],
            "addon_plan_sha256": profile["addon_plan_sha256"],
            "native_patch_manifest_sha256": profile["native_patch_manifest_sha256"],
            "resource_manifest_sha256": profile["resource_manifest_sha256"],
            "resource_index_sha256": profile["resource_index_sha256"],
            "runtime_qualified": False,
        }
        (stage / "launcher-build.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shutil.rmtree(build_dir)
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return json.loads((output / "launcher-build.json").read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the native x64 J.1 suspended-process launcher")
    parser.add_argument("--bundle", type=Path, default=addon_runtime.DEFAULT_OUTPUT)
    parser.add_argument("--retail-exe", type=Path, default=addon_runtime.DEFAULT_RETAIL_EXE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--generator", default="Visual Studio 18 2026")
    args = parser.parse_args(argv)
    try:
        result = build_launcher(bundle=args.bundle, output=args.output,
                                retail_exe=args.retail_exe, generator=args.generator)
    except (LauncherBuildError, addon_runtime.RuntimeIntegrationError, OSError,
            subprocess.CalledProcessError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
