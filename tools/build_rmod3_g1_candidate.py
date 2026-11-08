#!/usr/bin/env python3
"""Build or verify the isolated R-MOD3-G1 DirectInput test candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from audit_dinput8_exports import audit
from build_r_mod1_candidate import (
    ROOT, CandidateBuildError, compile_products, compiler_environment,
    locate_toolchain, v2_profile,
)
from build_rmod2_boot_a import BuildError, run
from r_ai1_mixed_class import RETAIL_SHA256, RETAIL_SIZE
from r_mod1_native_plan import build_plan, public_plan, render_cpp_header


RETAIL = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
OUT = ROOT / ".research-output" / "r-mod3" / "g1" / "first-integrated-candidate-g1"
# This is the deterministic current-source F3 parent with the G1 callback
# marker disabled. G1's internal exhaustion signal changes the compiled core
# even when its Quick Race native selector is not enabled. The public beta's
# immutable runtime identity remains separately pinned by the release builder.
EXPECTED_F3_PARENT_CORE = "6992f3f108643769b2e7165c3f8313e8cf8c45bd49942f94830d8b9aeca30ffd"
F3_REFERENCE_PLAN = ROOT / "research" / "r-mod1" / "native-patch-plan-f3.json"
MAX_CONFIG = 4096

PROFILES = {
    "six-ai-t1-same-class.ini": (1, 6, 1),
    "seven-ai-t1-same-class.ini": (1, 7, 1),
    "seven-ai-t2-same-class.ini": (2, 7, 1),
    "seven-ai-t1-outside-class.ini": (1, 7, 1),
    "seven-ai-full-control.ini": (4, 7, 1),
    "seven-ai-t1-never.ini": (1, 7, 0),
}


class G1BuildError(RuntimeError):
    pass


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def deterministic_zip(root: Path, output: Path, paths: list[str]) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(paths):
            path = root / relative
            info = zipfile.ZipInfo(relative, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def _compare_plans(f3: dict, g1: dict) -> None:
    f3_ops = {row["id"]: row for row in f3["operations"]}
    g1_ops = {row["id"]: row for row in g1["operations"]}
    if f3_ops.keys() != g1_ops.keys() or len(g1_ops) != 17:
        raise G1BuildError("G1 must preserve the exact 17-operation F3 ownership set")
    expected_changed = {
        "quickrace-selector-init", "quickrace-selector-loop", "quickrace-selector-end",
    }
    for operation_id in f3_ops:
        if operation_id not in expected_changed and f3_ops[operation_id] != g1_ops[operation_id]:
            raise G1BuildError("G1 changed a non-Quick-Race F3 native operation: " + operation_id)
    if any(f3_ops[key] == g1_ops[key] for key in expected_changed):
        raise G1BuildError("G1 Quick Race selector sites did not target the duplicate-aware emitted code")
    spans = sorted((row["rva"], row["rva"] + len(bytes.fromhex(row["replacement_hex"])), row["id"])
                   for row in g1["operations"])
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise G1BuildError("G1 native operations overlap")
    if any(row["va"] == 0x00458090 for row in g1["operations"]):
        raise G1BuildError("G1 must not replace the retail physical chooser entry")
    if any(not (row["va"] + len(bytes.fromhex(row["replacement_hex"])) <= 0x00458382 or
                row["va"] >= 0x004584D6) for row in g1["operations"]):
        raise G1BuildError("G1 overlaps the retail refill, CarID/DriverID setters or chooser tail")
    if g1.get("duplicate_support", {}).get("status") != "STATICALLY_VERIFIED_HUMAN_RUNTIME_PENDING":
        raise G1BuildError("G1 plan must retain an explicit pending human runtime status")


def _verify_current_f3_against_reference(f3: dict) -> None:
    if not F3_REFERENCE_PLAN.is_file():
        raise G1BuildError("canonical current F3 native plan reference is missing")
    reference = json.loads(F3_REFERENCE_PLAN.read_text(encoding="utf-8"))
    # Runtime DLL identity and plan-template digest may change when the
    # internal core gains G1-only exhaustion signaling. Native ownership,
    # emitted remote allocations, and every F3 operation must remain exact.
    for key in ("operations", "remote_allocations", "code_symbols"):
        if reference.get(key) != f3.get(key):
            raise G1BuildError("current F3 differs from its canonical native-plan reference: " + key)


def _compile_g1_proxy(work: Path, runtime: Path, header: str,
                      vcvars: Path, msvc_root: Path, *, g2: bool = False) -> tuple[Path, dict, dict[str, str]]:
    include = work / "include"
    include.mkdir(parents=True)
    (include / "native_plan.hpp").write_text(header, encoding="ascii", newline="\n")
    x86_env = compiler_environment(vcvars, "x64_x86")
    x86 = msvc_root / "bin" / "Hostx64" / "x86" / "cl.exe"
    dumpbin = msvc_root / "bin" / "Hostx64" / "x86" / "dumpbin.exe"
    if not x86.is_file() or not dumpbin.is_file():
        raise G1BuildError("MSVC x86 compiler/dumpbin is unavailable")

    proxy = work / "dinput8.dll"
    g2_flags = ["/DRMOD3_G1_DUPLICATE_REPEAT_FALLBACK=1", "/DRMOD3_G2_PLAYER_OVERRIDE=1"] if g2 else []
    run([str(x86), "/nologo", "/LD", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
         "/Brepro", "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800",
         *g2_flags, "/I" + str(include), "/I" + str(ROOT / "src/native/rmod1"),
         str(ROOT / "src/native/rmod1/dinput8_proxy.cpp"),
         str(ROOT / "src/native/rmod1/rmod2_inprocess.cpp"),
         "/link", "/DEF:" + str(ROOT / "src/native/rmod1/dinput8_proxy.def"),
         "bcrypt.lib", "user32.lib", "/NOIMPLIB", "/Brepro", "/OUT:" + str(proxy)],
        env=x86_env, cwd=work)
    exports = audit(proxy)
    exports.pop("path", None)
    if exports.get("required_match") is not True:
        raise G1BuildError("G1 DirectInput proxy exports differ from the audited BOOT-A contract")
    headers = run([str(dumpbin), "/headers", str(proxy)], env=x86_env, cwd=work)
    if "14C machine (x86)" not in headers:
        raise G1BuildError("G1 DirectInput proxy is not PE32/I386")
    imports = run([str(dumpbin), "/imports", str(proxy)], env=x86_env, cwd=work)
    if re.search(r"(?im)^\s*dinput8\.dll\s*$", imports):
        raise G1BuildError("G1 proxy imports itself by name and would recurse")
    if "d3d8.dll" in imports.casefold():
        raise G1BuildError("G1 proxy must remain independent of the graphical d3d8 renderer")
    exports["sha256"] = file_sha(proxy)
    return proxy, exports, x86_env


def _run_bootstrap_harnesses(work: Path, proxy: Path, runtime: Path,
                             x86_env: dict[str, str], msvc_root: Path,
                             *, checkpoint: str = "g1") -> dict[str, str]:
    x86 = msvc_root / "bin" / "Hostx64" / "x86" / "cl.exe"
    common = ["/nologo", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX", "/Brepro",
              "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800"]
    results: dict[str, str] = {}
    work.mkdir(parents=True, exist_ok=True)

    forward = work / "forwarding-harness"
    forward.mkdir()
    shutil.copyfile(proxy, forward / "dinput8.dll")
    forward_exe = forward / "dinput8_forward_harness.exe"
    run([str(x86), *common, str(ROOT / "tests/rmod1/dinput8_forward_harness.cpp"),
         "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "/OUT:" + str(forward_exe)],
        env=x86_env, cwd=forward)
    forwarding = run([str(forward_exe), str(forward / "dinput8.dll")], env=x86_env, cwd=forward)
    if "DINPUT8_FORWARD_PASS named=6 ordinal=6 directinput8create=system-match joystick-format=system-match" not in forwarding:
        raise G1BuildError("DirectInput forwarding harness failed")
    results["directinput_forwarding"] = forwarding.strip()

    once = work / "init-once-harness"
    once.mkdir()
    shutil.copyfile(proxy, once / "dinput8.dll")
    shutil.copyfile(runtime, once / "MRallyeRandomizerRuntime.dll")
    once_exe = once / "rmod2_boot_b_harness.exe"
    run([str(x86), *common, str(ROOT / "tests/rmod1/rmod2_boot_b_harness.cpp"),
         "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "/OUT:" + str(once_exe)],
        env=x86_env, cwd=once)
    init_once = run([str(once_exe), str(once / "dinput8.dll")], env=x86_env, cwd=once)
    if "BOOT_B_INIT_ONCE_PASS concurrent_calls=8 invalid_host_fail_closed=1 directinput_forwarding=8/8" not in init_once:
        raise G1BuildError("once-only invalid-host fail-closed DirectInput harness failed")
    results["fail_closed_bootstrap"] = init_once.strip()

    image_diff = work / "image-difference-harness"
    image_diff.mkdir()
    image_exe = image_diff / "runtime_image_diff_harness.exe"
    run([str(x86), *common, "/I" + str(ROOT / "src/native/rmod1"),
         str(ROOT / "tests/rmod1/runtime_image_diff_harness.cpp"),
         "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "/OUT:" + str(image_exe)],
        env=x86_env, cwd=image_diff)
    differences = run([str(image_exe)], env=x86_env, cwd=image_diff)
    if "RUNTIME_IMAGE_DIFF_PASS virtual_extent_only=1 padding_ignored=1 non_hook_diagnostic=1 selected_hook_conflict=1 zero_fill=1" not in differences:
        raise G1BuildError("mapped image difference harness failed")
    results["mapped_image_diagnostics"] = differences.strip()

    preflight = work / "host-qualified-preflight"
    preflight.mkdir()
    preflight_exe = preflight / "rmod2_host_qualified_preflight_harness.exe"
    include = work / "plan-include"
    include.mkdir()
    preflight_products = work / (checkpoint + "-preflight-products")
    expected_preflight_runtime, _preflight_launcher, _exception, _log = compile_products(
        preflight_products, RETAIL, *locate_toolchain(), checkpoint=checkpoint)
    # compile_products' generated header is authoritative for this exact native plan
    # runtime; this harness compiles against it and verifies every selected
    # operation's pristine retail preimage.
    plan_path = preflight_products / "native-patch-plan.json"
    header_path = preflight_products / "include" / "native_plan.hpp"
    # The caller has already built the same deterministic plan once. Avoid
    # accepting a second, unrelated plan if toolchain output changes.
    if not plan_path.is_file() or not header_path.is_file():
        raise G1BuildError(checkpoint.upper() + " generated plan/header for preflight harness is missing")
    if file_sha(expected_preflight_runtime) != file_sha(runtime):
        raise G1BuildError("host-qualified preflight was compiled against a different " + checkpoint.upper() + " runtime")
    shutil.copyfile(header_path, include / "native_plan.hpp")
    run([str(x86), *common, "/I" + str(include), "/I" + str(ROOT / "src/native/rmod1"),
         str(ROOT / "tests/rmod1/rmod2_host_qualified_preflight_harness.cpp"),
         "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "bcrypt.lib", "/OUT:" + str(preflight_exe)],
        env=x86_env, cwd=preflight)
    preflight_output = run([str(preflight_exe), str(RETAIL)], env=x86_env, cwd=preflight)
    if "BOOT_B_HOST_QUALIFIED_PREFLIGHT_PASS" not in preflight_output:
        raise G1BuildError("host-qualified native-plan/preimage preflight harness failed")
    results["host_qualified_preflight"] = preflight_output.strip()
    return results


def _candidate_files(package: Path) -> list[str]:
    return sorted(path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file())


def build(output: Path = OUT, retail_exe: Path = RETAIL) -> dict:
    retail_exe = Path(os.path.abspath(retail_exe))
    output = Path(os.path.abspath(output))
    if not retail_exe.is_file() or retail_exe.stat().st_size != RETAIL_SIZE or file_sha(retail_exe) != RETAIL_SHA256:
        raise G1BuildError("input must be the exact pristine retail MRallye.exe")
    if output.exists():
        raise G1BuildError("refusing to overwrite an existing G1 candidate directory: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="rmod3-g1-build-", dir=output.parent))
    stage = Path(tempfile.mkdtemp(prefix="rmod3-g1-stage-", dir=output.parent))
    try:
        vcvars, msvc_root = locate_toolchain()
        # Rebuild current F3 source with the G1 callback marker disabled and
        # compare its native plan against the canonical F3 reference. The
        # public beta binary remains immutable and is not rebuilt or included.
        f3_runtime, _f3_launcher, _f3_exception, _f3_log = compile_products(
            work / "f3-parent", retail_exe, vcvars, msvc_root, checkpoint="f3")
        f3_sha = file_sha(f3_runtime)
        if f3_sha != EXPECTED_F3_PARENT_CORE:
            raise G1BuildError("current-source F3 parent core differs from its deterministic pinned identity: " + f3_sha)
        f3_plan = public_plan(build_plan(retail_exe.read_bytes(), f3_runtime.read_bytes(), checkpoint="f3"))
        _verify_current_f3_against_reference(f3_plan)

        runtime, _launcher, exception_test, log_test = compile_products(
            work / "g1-products", retail_exe, vcvars, msvc_root, checkpoint="g1")
        runtime_sha = file_sha(runtime)
        retail_bytes = retail_exe.read_bytes()
        g1_plan = build_plan(retail_bytes, runtime.read_bytes(), checkpoint="g1")
        _compare_plans(f3_plan, public_plan(g1_plan))
        plan_json = json.dumps(public_plan(g1_plan), indent=2, sort_keys=True) + "\n"
        header = render_cpp_header(g1_plan)

        proxy, exports, x86_env = _compile_g1_proxy(
            work / "g1-proxy", runtime, header, vcvars, msvc_root)
        harness_results = _run_bootstrap_harnesses(
            work / "g1-harnesses", proxy, runtime, x86_env, msvc_root)

        package = stage / "package"
        (package / "profiles").mkdir(parents=True)
        shutil.copyfile(proxy, package / "dinput8.dll")
        shutil.copyfile(runtime, package / "MRallyeRandomizerRuntime.dll")
        (package / "MRallyeRandomizer.ini").write_text(v2_profile(), encoding="ascii", newline="\n")
        (package / "native-patch-plan.json").write_text(plan_json, encoding="utf-8", newline="\n")
        for name, (policy, maximum, duplicates) in PROFILES.items():
            ini = v2_profile(quick_race=policy, max_opponents=maximum,
                             duplicates=duplicates, logging=1)
            if len(ini.encode("ascii")) > MAX_CONFIG:
                raise G1BuildError("generated test INI exceeds the native parser limit: " + name)
            (package / "profiles" / name).write_text(ini, encoding="ascii", newline="\n")
        readme = (
            "R-MOD3-G1 duplicate-capable Quick Race development candidate\n\n"
            "This package is separate from the published v0.1.0-beta.1 and contains no game EXE or game assets.\n"
            "Use a disposable copy of the exact retail game. Keep MRallye.exe and any graphical d3d8.dll unchanged.\n"
            "If the test copy already contains a different dinput8.dll, do not overwrite it; create a clean copy.\n"
            "Install this package beside MRallye.exe and launch MRallye.exe normally. Remove only this package to disable it.\n"
            "Before starting, copy one profiles\\*.ini file over MRallyeRandomizer.ini. MaxOpponents is startup-scoped,\n"
            "so restart the game when moving between six- and seven-AI profiles. Select the requested count in Quick Race.\n"
            "ConfigVersion=2 QuickRace numeric policy: 1=T1, 2=T2, 4=Full; Duplicates=1 means WhenNeeded.\n\n"
            "Suggested order: (1) six-ai-t1-same-class with a T1 player; (2) seven-ai-t1-same-class with a T1 player;\n"
            "(3) seven-ai-t2-same-class with a T2 player; (4) seven-ai-t1-outside-class with a non-T1 player;\n"
            "(5) seven-ai-full-control. For seven restricted-class AI with a same-class player, expect six distinct\n"
            "eligible AI CarIDs and at least one repeated physical CarID in a separate AI CarN participant. Keep the\n"
            "strict selected class. Check all eight participant slots, AI movement, one complete finish, Results and\n"
            "return to frontend. Use Observatory for CarID/Class/PlayerType/DriverID where available.\n\n"
            "The candidate changes only the Quick Race class-selector source-pool pruning after all unique eligible\n"
            "physical IDs are used. Retail native refill, CarID/Class/DriverID publication and participant creation remain\n"
            "the owners. This is static evidence, not proof that repeated-model vehicle actors or a complete eight-car\n"
            "race are safe at runtime. Stop on the first failure and preserve MRallyeRandomizer.log, the crash sidecar if\n"
            "present, the selected INI, and this candidate manifest. Do not continue to another profile after a crash.\n"
            "Duplicates=0 is Never; the candidate refuses only an impossible extended mode-2 Quick Race roster.\n"
            "Practice, Checkpoint and every non-Quick-Race Start path remain native passthrough.\n\n"
            "This is a development candidate, not a new public release. The published beta and Vehicle SDK are not\n"
            "included or required. The dinput8 proxy does not import or replace the graphical d3d8 renderer.\n"
        )
        (package / "README.txt").write_text(readme, encoding="ascii", newline="\n")
        listed = _candidate_files(package)
        rows = [{"path": name, "size": (package / name).stat().st_size,
                 "sha256": file_sha(package / name)} for name in listed]
        manifest = {
            "schema_version": 1,
            "candidate": "first-integrated-candidate-g1",
            "phase": "R-MOD3-G1",
            "qualification": "STATICALLY_VERIFIED_HUMAN_RUNTIME_PENDING",
            "published_beta_modified": False,
            "source_executable_sha256": RETAIL_SHA256,
            "source_executable_size": RETAIL_SIZE,
            "f3_parent_runtime_sha256": f3_sha,
            "runtime_core_sha256": runtime_sha,
            "directinput_proxy_sha256": file_sha(proxy),
            "native_plan_sha256": g1_plan["plan_template_sha256"],
            "operation_count": len(g1_plan["operations"]),
            "duplicate_support": public_plan(g1_plan)["duplicate_support"],
            "on_disk_game_executable_modified": False,
            "graphical_d3d8_modified": False,
            "files": rows,
        }
        _write_json(package / "candidate-manifest.json", manifest)
        package_files = _candidate_files(package)
        package_zip = stage / "first-integrated-candidate-g1.zip"
        deterministic_zip(package, package_zip, package_files)
        _write_json(stage / "candidate-build-evidence.json", {
            "f3_parent_runtime_sha256": f3_sha,
            "runtime_core_sha256": runtime_sha,
            "native_plan_sha256": g1_plan["plan_template_sha256"],
            "native_plan_operation_count": len(g1_plan["operations"]),
            "runtime_exception_harness": exception_test,
            "runtime_log_harness": log_test,
            "proxy_exports": exports,
            "windows_harnesses": harness_results,
            "package_zip_sha256": file_sha(package_zip),
            "package_zip_size": package_zip.stat().st_size,
        })

        # Expose a source-only plan header for technical inspection. Neither
        # the review artifact nor the user test ZIP contains the retail image.
        (stage / "native_plan.hpp").write_text(header, encoding="ascii", newline="\n")
        os.replace(stage, output)
        return {**manifest, "package_zip": str(output / package_zip.name),
                "package_zip_sha256": file_sha(output / package_zip.name)}
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def verify(output: Path = OUT, retail_exe: Path = RETAIL) -> dict:
    package = Path(os.path.abspath(output)) / "package"
    manifest_path = package / "candidate-manifest.json"
    if not manifest_path.is_file():
        raise G1BuildError("G1 candidate manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_executable_sha256") != RETAIL_SHA256 or manifest.get("source_executable_size") != RETAIL_SIZE:
        raise G1BuildError("G1 candidate is pinned to an unexpected original executable")
    for row in manifest.get("files", []):
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise G1BuildError("manifest contains an unsafe package path")
        path = package / relative
        if not path.is_file() or path.stat().st_size != row["size"] or file_sha(path) != row["sha256"]:
            raise G1BuildError("candidate package file failed hash/size verification: " + row["path"])
    names = {path.name.casefold() for path in package.rglob("*") if path.is_file()}
    if "mrallye.exe" in names or "data.sma" in names:
        raise G1BuildError("candidate package must not contain the game executable or Data.sma")
    runtime = package / "MRallyeRandomizerRuntime.dll"
    plan_file = package / "native-patch-plan.json"
    if not retail_exe.is_file() or file_sha(Path(os.path.abspath(retail_exe))) != RETAIL_SHA256:
        raise G1BuildError("verification requires the exact pristine retail executable")
    rebuilt = public_plan(build_plan(Path(os.path.abspath(retail_exe)).read_bytes(), runtime.read_bytes(), checkpoint="g1"))
    packaged_plan = json.loads(plan_file.read_text(encoding="utf-8"))
    if rebuilt != packaged_plan:
        raise G1BuildError("packaged G1 native plan does not reproduce from the exact retail/runtime inputs")
    package_zip = Path(os.path.abspath(output)) / "first-integrated-candidate-g1.zip"
    if not package_zip.is_file():
        raise G1BuildError("G1 test package ZIP is missing")
    with zipfile.ZipFile(package_zip) as archive:
        zip_names = archive.namelist()
        if sorted(zip_names) != sorted(_candidate_files(package)):
            raise G1BuildError("G1 test ZIP file set differs from the verified package tree")
        for name in zip_names:
            if archive.read(name) != (package / name).read_bytes():
                raise G1BuildError("G1 test ZIP content mismatch: " + name)
    return {"status": "G1_CANDIDATE_PACKAGE_VERIFIED", "candidate": manifest["candidate"],
            "runtime_core_sha256": file_sha(runtime),
            "directinput_proxy_sha256": file_sha(package / "dinput8.dll"),
            "native_plan_sha256": rebuilt["plan_template_sha256"],
            "operation_count": len(rebuilt["operations"]),
            "package_zip_sha256": file_sha(package_zip),
            "source_executable_sha256": file_sha(Path(os.path.abspath(retail_exe)))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--retail-exe", type=Path, default=RETAIL)
    parser.add_argument("--verify", action="store_true", help="verify an existing candidate package and plan")
    args = parser.parse_args()
    try:
        result = verify(args.output, args.retail_exe) if args.verify else build(args.output, args.retail_exe)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (G1BuildError, CandidateBuildError, BuildError, OSError, ValueError,
            subprocess.SubprocessError, json.JSONDecodeError) as error:
        print("R-MOD3-G1 candidate failed closed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
