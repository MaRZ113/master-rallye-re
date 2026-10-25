#!/usr/bin/env python3
"""Build the J.2-specific trust-profile launcher without changing J.1 source."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import addon_runtime  # noqa: E402
import build_runtime_launcher  # noqa: E402
import j2_frontend_reentry  # noqa: E402


DEFAULT_OUTPUT = j2_frontend_reentry.J2_BUNDLE
DEFAULT_BUNDLE = DEFAULT_OUTPUT / "bundle"
GENERATOR = "Visual Studio 18 2026"


class J2LauncherBuildError(RuntimeError):
    """The candidate did not pass static bundle/build validation."""


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_launcher(*, bundle: Path = DEFAULT_BUNDLE, output: Path = DEFAULT_OUTPUT,
                   retail_exe: Path = addon_runtime.DEFAULT_RETAIL_EXE,
                   base_bundle: Path = addon_runtime.DEFAULT_OUTPUT,
                   package: Path = addon_runtime.DEFAULT_I1_PACKAGE,
                   capabilities: Path = addon_runtime.DEFAULT_CAPABILITIES,
                   generator: str = GENERATOR) -> dict[str, Any]:
    if os.name != "nt":
        raise J2LauncherBuildError("the native Windows launcher must be built on Windows")
    output = Path(output).resolve()
    research_output = (PROJECT_ROOT / ".research-output").resolve()
    try:
        output.relative_to(research_output)
    except ValueError as exc:
        raise J2LauncherBuildError("launcher output must remain under ignored .research-output") from exc
    if output.is_symlink() or getattr(output, "is_junction", lambda: False)() or not output.is_dir():
        raise J2LauncherBuildError("candidate output root must already exist and be a real directory")
    launcher_path = output / "mr-runtime-launcher.exe"
    metadata_path = output / "launcher-build.json"
    if launcher_path.exists() or metadata_path.exists():
        raise J2LauncherBuildError("refusing to overwrite an existing J.2 launcher candidate")

    verified = j2_frontend_reentry.verify_candidate(
        bundle, base_bundle=base_bundle, retail_exe=retail_exe,
        package=package, capabilities=capabilities)
    if verified.get("status") != "PASS_STATIC_J2_REENTRY_BUNDLE":
        raise J2LauncherBuildError("J.2 bundle verification failed")
    profile = json.loads((bundle / "runtime-profile.json").read_text(encoding="utf-8"))
    manifest = json.loads((bundle / "native-patch-manifest.json").read_text(encoding="utf-8"))
    trusted_header = build_runtime_launcher._header(profile, manifest)

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".j2-launcher-building-", dir=output.parent))
    try:
        include_dir = stage / "generated"
        include_dir.mkdir()
        (include_dir / "trusted_profile.hpp").write_bytes(trusted_header)
        build_dir = stage / "cmake-build"
        configure = ["cmake", "-S", str(PROJECT_ROOT / "runtime_launcher"), "-B", str(build_dir),
                     "-G", generator, "-A", "x64", f"-DPROFILE_INCLUDE_DIR={include_dir}"]
        subprocess.run(configure, check=True)
        subprocess.run(["cmake", "--build", str(build_dir), "--config", "Release",
                        "--target", "mr-runtime-launcher"], check=True)
        candidates = list(build_dir.rglob("mr-runtime-launcher.exe"))
        if len(candidates) != 1 or not candidates[0].is_file():
            raise J2LauncherBuildError("CMake did not produce exactly one Windows launcher")
        built = candidates[0]
        data = built.read_bytes()
        if len(data) < 4096 or data[:2] != b"MZ":
            raise J2LauncherBuildError("built launcher is not a valid-looking PE executable")
        (stage / "mr-runtime-launcher.exe").write_bytes(data)
        metadata = {
            "schema_version": 1,
            "artifact_kind": "J.2 native external runtime launcher build",
            "status": "STATIC_BUILD_ONLY_READY_FOR_HUMAN_RUNTIME",
            "generator": generator,
            "architecture": "x64 launcher / x86 target process",
            "launcher_sha256": hashlib.sha256(data).hexdigest(),
            "launcher_size": len(data),
            "candidate_profile": profile["profile"],
            "retail_exe_sha256": profile["retail_exe"]["sha256"],
            "addon_plan_sha256": profile["addon_plan_sha256"],
            "native_patch_manifest_sha256": profile["native_patch_manifest_sha256"],
            "native_patch_operations_sha256": profile["native_patch_operations_sha256"],
            "resource_manifest_sha256": profile["resource_manifest_sha256"],
            "resource_index_sha256": profile["resource_index_sha256"],
            "runtime_qualified": False,
        }
        (stage / "launcher-build.json").write_bytes(addon_runtime.canonical_json(metadata))
        # The candidate directory is an ignored, generated research artifact;
        # copy only the two new launcher outputs into it, preserving the bundle.
        shutil.copyfile(stage / "mr-runtime-launcher.exe", launcher_path)
        try:
            metadata_path.write_bytes(addon_runtime.canonical_json(metadata))
        except Exception:
            launcher_path.unlink(missing_ok=True)
            raise
        return metadata
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the J.2 re-entry launcher with a dedicated trusted profile")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--retail-exe", type=Path, default=addon_runtime.DEFAULT_RETAIL_EXE)
    parser.add_argument("--base-bundle", type=Path, default=addon_runtime.DEFAULT_OUTPUT)
    parser.add_argument("--i1-package", type=Path, default=addon_runtime.DEFAULT_I1_PACKAGE)
    parser.add_argument("--capabilities", type=Path, default=addon_runtime.DEFAULT_CAPABILITIES)
    parser.add_argument("--generator", default=GENERATOR)
    args = parser.parse_args(argv)
    try:
        result = build_launcher(bundle=args.bundle, output=args.output,
                                retail_exe=args.retail_exe, base_bundle=args.base_bundle,
                                package=args.i1_package, capabilities=args.capabilities,
                                generator=args.generator)
    except (J2LauncherBuildError, addon_runtime.RuntimeIntegrationError,
            j2_frontend_reentry.ReentryBundleError, OSError, ValueError,
            KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
