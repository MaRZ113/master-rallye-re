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
from typing import Any, Callable

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
    extension = profile.get('native_extension')
    if extension is not None:
        allocation=extension.get('allocation_size')
        large_damage=(allocation==131072 and profile.get('profile')=='sdk-native-damage-coverage-alpha'
                      and type(extension.get('size')) is int and extension['size']>65536)
        roster=profile.get('sdk_roster_layout',{})
        combined=(allocation==262144 and profile.get('profile')=='sdk-multi-addon-roster'
                  and isinstance(roster,dict) and set(roster)=={'record_count','addon_ids'}
                  and type(roster['record_count']) is int and roster['record_count'] in (29,30)
                  and roster['addon_ids']==list(range(26,roster['record_count'])))
        if (set(extension)-{'writable_ranges'} != {'address','size','sha256','allocation_size'}
                or extension['address'] != 0x10000000
                or type(extension['size']) is not int or not 1 <= extension['size'] <= (262144 if combined else 131072 if large_damage else 65536)
                or (allocation!=65536 and not large_damage and not combined)
                or not isinstance(extension['sha256'], str) or len(extension['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in extension['sha256'])):
            raise LauncherBuildError('unsupported private native extension layout')
        ranges=extension.get('writable_ranges',[])
        if not isinstance(ranges,list) or len(ranges)>1:
            raise LauncherBuildError('unsupported native writable ranges')
        for region in ranges:
            if (not isinstance(region,dict) or set(region)!={'offset','size'}
                or type(region['offset']) is not int or type(region['size']) is not int
                or region['offset']<4096 or region['offset']%4096 or region['size']!=4096
                or region['offset']+region['size']>extension['size']):
                raise LauncherBuildError('invalid bounded native data page')
        if ranges:
            rows.extend((f"#define MR_EXTENSION_RW_OFFSET {ranges[0]['offset']}u",f"#define MR_EXTENSION_RW_SIZE {ranges[0]['size']}u"))
        rows.extend((f"#define MR_EXTENSION_SIZE {extension['size']}u",
                     f"#define MR_EXTENSION_ADDRESS {extension['address']}u",
                     f"#define MR_EXTENSION_ALLOCATION_SIZE {extension['allocation_size']}u",
                     f"#define MR_EXTENSION_SHA256 \"{extension['sha256']}\""))
    return ("\n".join(rows) + "\n").encode("ascii")


def build_launcher(*, bundle: Path, output: Path = DEFAULT_OUTPUT,
                   retail_exe: Path | None = None,
                   generator: str = "Visual Studio 18 2026",
                   bundle_verifier: Callable[[], dict[str, Any]] | None = None) -> dict[str, Any]:
    if os.name != "nt":
        raise LauncherBuildError("the native launcher can only be built on Windows")
    bundle = Path(bundle)
    retail_exe = Path(retail_exe or addon_runtime.DEFAULT_RETAIL_EXE).resolve()
    verified = (bundle_verifier() if bundle_verifier is not None
                else addon_runtime.verify_bundle(bundle, retail_exe=retail_exe))
    output = addon_runtime._under_research_output(Path(output))
    profile = json.loads((bundle / "runtime-profile.json").read_text(encoding="utf-8"))
    patch_manifest = json.loads((bundle / "native-patch-manifest.json").read_text(encoding="utf-8"))
    allowed_statuses = {"PASS_STATIC_RUNTIME_BUNDLE", "PASS_STATIC_COLLECTION_RUNTIME_BUNDLE"}
    if verified.get("status") not in allowed_statuses or verified.get("runtime_qualified") is not False:
        raise LauncherBuildError("bundle is not a statically verified, unqualified runtime candidate")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    # MSVC/CMake's nested TryCompile paths exceed MAX_PATH in ordinary deep
    # Workshop projects. Keep compiler scratch short; publish atomically into
    # the original fresh output tree after successful validation.
    scratch = tempfile.TemporaryDirectory(prefix='mrl-')
    try:
        include_dir = Path(scratch.name) / "generated"
        include_dir.mkdir()
        (include_dir / "trusted_profile.hpp").write_bytes(_header(profile, patch_manifest))
        shutil.copytree(include_dir, stage / 'generated')
        build_dir = Path(scratch.name) / "build"
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
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    finally:
        scratch.cleanup()
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
