#!/usr/bin/env python3
"""Build the BOOT-B in-process dinput8 activation test from the unchanged F3 core."""
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

from build_r_mod1_candidate import ROOT, compile_products, locate_toolchain
from build_rmod2_boot_a import BuildError, run, sha, zip_tree
from audit_dinput8_exports import EXPECTED, audit
from r_mod1_native_plan import public_plan, render_cpp_header

RETAIL = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
EXPECTED_RETAIL = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
# F3 descendant with only the non-mode-2 Start-gate pass-through correction.
EXPECTED_F3_CORE = "666cd52e2dcb1e53ed7e4a6f36a20fa43cb71f64c2ee0720a70fff47fff58eb4"
VSWHERE = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")


def build(output: Path) -> dict:
    output = Path(os.path.abspath(output))
    if output.exists():
        raise BuildError(f"refusing to overwrite existing output: {output}")
    if not RETAIL.is_file() or sha(RETAIL) != EXPECTED_RETAIL or RETAIL.stat().st_size != 3_121_214:
        raise BuildError("exact pristine retail executable is required as plan-generation input")
    output.mkdir(parents=True)
    work = output / "build"
    work.mkdir()
    package = output / "MasterRallye-Randomizer-BOOT-B-Test"
    package.mkdir()

    vcvars, msvc_root = locate_toolchain()
    runtime, _launcher, _exception_test, _log_test = compile_products(work / "f3-products", RETAIL, vcvars, msvc_root, checkpoint="f3")
    if sha(runtime) != EXPECTED_F3_CORE:
        raise BuildError("rebuilt F3 runtime core differs from the immutable, previously qualified identity")
    # compile_products produced the authoritative F3 plan/header from this exact
    # retail image and unchanged F3 policy sources. Re-render so the in-process
    # linker gets the generated callback-slot addresses from the same planner.
    from r_mod1_native_plan import build_plan
    plan = build_plan(RETAIL.read_bytes(), runtime.read_bytes(), checkpoint="f3")
    include_dir = work / "include"
    include_dir.mkdir(exist_ok=True)
    (include_dir / "native_plan.hpp").write_text(render_cpp_header(plan), encoding="ascii", newline="\n")
    plan_path = work / "native-patch-plan.json"
    plan_path.write_text(json.dumps(public_plan(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    test_ini = ("[General]\nConfigVersion = 2\n\n[Randomizer]\nQuickRace = 1\nRallyeCup = 0\n"
                "MasterRallye = 0\nInvitation = 0\nChallenge = 0\nDuplicates = 1\n\n"
                "[Opponents]\nMaxOpponents = 7\n\n[Addons]\nInclude = 0\n\n[Logging]\nEnabled = 1\n")
    # V2 installs the shared mode callbacks so valid policy edits can take
    # effect at the next native generation boundary; count the matching F3
    # operations while explicitly excluding the already-passed OEP hook.
    requested_features = 1
    selected_ids = [op["id"] for op in plan["operations"]
                    if op["id"] != "oep-bootstrap" and op["feature_mask"] & requested_features]

    x86_cl = msvc_root / "bin" / "Hostx64" / "x86" / "cl.exe"
    dumpbin = msvc_root / "bin" / "Hostx64" / "x86" / "dumpbin.exe"
    if not x86_cl.is_file():
        raise BuildError("MSVC x86 compiler is unavailable")
    from build_r_mod1_candidate import compiler_environment
    env = compiler_environment(vcvars, "x64_x86")
    proxy = work / "dinput8.dll"
    proxy_source = ROOT / "src/native/rmod1/dinput8_proxy.cpp"
    installer_source = ROOT / "src/native/rmod1/rmod2_inprocess.cpp"
    proxy_def = ROOT / "src/native/rmod1/dinput8_proxy.def"
    run([str(x86_cl), "/nologo", "/LD", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
         "/Brepro", "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800",
         "/I" + str(include_dir), "/I" + str(ROOT / "src/native/rmod1"),
         str(proxy_source), str(installer_source), "/link", "/DEF:" + str(proxy_def),
         "bcrypt.lib", "user32.lib", "/NOIMPLIB", "/Brepro", "/OUT:" + str(proxy)], env=env, cwd=work)
    exports = audit(proxy)
    exports.pop("path", None)
    exports["sha256"] = sha(proxy)
    if exports.get("required_match") is not True:
        raise BuildError("BOOT-B proxy exports differ from the audited BOOT-A contract")
    (work / "proxy-export-audit.json").write_text(json.dumps(exports, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    dump = run([str(dumpbin), "/headers", str(proxy)], env=env, cwd=work)
    if "14C machine (x86)" not in dump:
        raise BuildError("proxy is not PE32/I386")
    imports = run([str(dumpbin), "/imports", str(proxy)], env=env, cwd=work)
    if re.search(r"(?im)^\s*dinput8\.dll\s*$", imports):
        raise BuildError("proxy imports itself by name and would recurse")

    # Preserve the BOOT-A forwarding oracle and exercise BOOT-B's once-only
    # initializer concurrently under an intentionally unsupported host image.
    harness_dir = work / "bootb-harness"
    forward_dir = harness_dir / "forward"
    bootb_dir = harness_dir / "init-once"
    forward_dir.mkdir(parents=True)
    bootb_dir.mkdir(parents=True)
    proxy_harness = forward_dir / "dinput8_forward_harness.exe"
    bootb_harness = bootb_dir / "rmod2_boot_b_harness.exe"
    old_harness_source = ROOT / "tests/rmod1/dinput8_forward_harness.cpp"
    bootb_harness_source = ROOT / "tests/rmod1/rmod2_boot_b_harness.cpp"
    common_flags = ["/nologo", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX", "/Brepro", "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0601", "/DDIRECTINPUT_VERSION=0x0800"]
    run([str(x86_cl), *common_flags, str(old_harness_source), "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "/OUT:" + str(proxy_harness)], env=env, cwd=forward_dir)
    run([str(x86_cl), *common_flags, str(bootb_harness_source), "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "/OUT:" + str(bootb_harness)], env=env, cwd=bootb_dir)
    forward_test = run([str(proxy_harness), str(proxy)], env=env, cwd=forward_dir)
    if "DINPUT8_FORWARD_PASS named=6 ordinal=6 directinput8create=system-match joystick-format=system-match" not in forward_test:
        raise BuildError("BOOT-A export-forwarding Windows harness failed")
    bootb_test = run([str(bootb_harness), str(proxy)], env=env, cwd=bootb_dir)
    if "BOOT_B_INIT_ONCE_PASS concurrent_calls=8 invalid_host_fail_closed=1 directinput_forwarding=8/8" not in bootb_test:
        raise BuildError("BOOT-B concurrent fail-closed initialization harness failed")
    image_diff_dir = harness_dir / "mapped-image-diff"
    image_diff_dir.mkdir(parents=True)
    image_diff_harness = image_diff_dir / "runtime_image_diff_harness.exe"
    image_diff_source = ROOT / "tests/rmod1/runtime_image_diff_harness.cpp"
    image_diff_test_binary = run([str(x86_cl), *common_flags, "/I" + str(ROOT / "src/native/rmod1"),
                                  str(image_diff_source), "/link", "/Brepro", "/SUBSYSTEM:CONSOLE",
                                  "/OUT:" + str(image_diff_harness)], env=env, cwd=image_diff_dir)
    image_diff_test = run([str(image_diff_harness)], env=env, cwd=image_diff_dir)
    if "RUNTIME_IMAGE_DIFF_PASS virtual_extent_only=1 padding_ignored=1 non_hook_diagnostic=1 selected_hook_conflict=1 zero_fill=1" not in image_diff_test:
        raise BuildError("mapped executable virtual-extent/conflict diagnostic harness failed")
    preflight_dir = harness_dir / "host-qualified-preflight"
    preflight_dir.mkdir(parents=True)
    preflight_harness = preflight_dir / "rmod2_host_qualified_preflight_harness.exe"
    preflight_source = ROOT / "tests/rmod1/rmod2_host_qualified_preflight_harness.cpp"
    preflight_compile = run([str(x86_cl), *common_flags, "/I" + str(include_dir), "/I" + str(ROOT / "src/native/rmod1"),
                             str(preflight_source), "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "bcrypt.lib",
                             "/OUT:" + str(preflight_harness)], env=env, cwd=preflight_dir)
    preflight_test = run([str(preflight_harness), str(RETAIL)], env=env, cwd=preflight_dir)
    if "BOOT_B_HOST_QUALIFIED_PREFLIGHT_PASS" not in preflight_test:
        raise BuildError("host-qualified template/config/native-preimage preflight harness failed")

    shutil.copyfile(proxy, package / "dinput8.dll")
    shutil.copyfile(runtime, package / "MRallyeRandomizerRuntime.dll")
    (package / "MRallyeRandomizer.ini").write_text(test_ini, encoding="ascii", newline="\n")
    (package / "README.txt").write_text(
        "MASTER RALLYE R-MOD2 BOOT-B HUMAN TEST\n\n"
        "This package activates the existing R-MOD1-F3 runtime through a local x86 dinput8 proxy.\n"
        "Test only in two disposable copies of the exact retail game. Copy A must have the\n"
        "existing graphical d3d8.dll present; copy B must omit that proxy. Never edit or replace\n"
        "the original d3d8.dll. Keep MRallye.exe unchanged in both copies. Do not overwrite a\n"
        "foreign dinput8.dll.\n\n"
        "Extract these four files beside MRallye.exe in each copy and launch the original\n"
        "executable by double-clicking. No shell, launcher, modified executable, Vehicle SDK\n"
        "or add-on car is involved. The profile keeps QuickRace=T1 and MaxOpponents=7.\n"
        "Keep each copy's MRallyeRandomizer-boot.log. First require\n"
        "HOST_VERIFIED, RUNTIME_LOADED, CONFIG_ACCEPTED, NATIVE_INSTALL_COMPLETE and BOOT_B_READY.\n"
        "Only after NATIVE_INSTALL_COMPLETE and BOOT_B_READY appear, start one Practice race\n"
        "and one Checkpoint race with MaxOpponents=7; both must follow the native Start path.\n"
        "Then test the T1 Quick Race\n"
        "profile in both copies. Then, in one still-running process, change QuickRace = 1 to\n"
        "QuickRace = 4 and start a NEW race to verify live reload.\n"
        "If image diagnostics appear, preserve the first IMAGE_DIFFERENCE_* and any\n"
        "IMAGE_SELECTED_HOOK_CONFLICT record from both configurations.\n"
        "This corrected candidate removes redundant in-process config staging and passes through\n"
        "every non-mode-2 Start context without applying Quick Race count policy. The F3 gameplay\n"
        "selectors remain unchanged. The F3 core\n"
        "already accepted the INI through MRConfigureBlobV1, and the omitted OEP bootstrap\n"
        "was the only generated code that reads CONFIG_BLOB/DLL_PATH.\n\n"
        "Disable by removing dinput8.dll, MRallyeRandomizerRuntime.dll and the INI (the README may\n"
        "also be removed). Never remove or replace d3d8.dll.\n\n"
        "This is a human-test candidate, not a supported release. BOOT-B has not yet passed\n"
        "gameplay/renderer runtime qualification. Seven-AI T1/T2-player stability remains\n"
        "unqualified and is outside this initial three-AI test.\n", encoding="ascii", newline="\n")

    package_files = ["dinput8.dll", "MRallyeRandomizerRuntime.dll", "MRallyeRandomizer.ini", "README.txt"]
    candidate_zip = output / "MasterRallye-Randomizer-BOOT-B-Test.zip"
    zip_tree(package, candidate_zip, package_files)

    validation_rows = []
    validation_env = dict(os.environ)
    validation_env["PYTHONPATH"] = str(ROOT / "src")
    for label, command in [
        ("focused-bootb", [sys.executable, "-m", "unittest", "discover", "-s", "tests/synthetic", "-p", "test_r_mod2_boot_b.py", "-v"]),
        ("focused-boot-a", [sys.executable, "-m", "unittest", "discover", "-s", "tests/synthetic", "-p", "test_r_mod2_dinput8.py", "-v"]),
        ("full-synthetic", [sys.executable, "-m", "unittest", "discover", "-s", "tests/synthetic", "-v"]),
        ("compileall", [sys.executable, "-m", "compileall", "src", "tools", "tests"]),
        ("diff-check", ["git", "diff", "--check"]),
    ]:
        result = subprocess.run(command, cwd=ROOT, env=validation_env, capture_output=True, text=True, check=False)
        output_text = (result.stdout or "") + (result.stderr or "")
        validation_rows.append(f"$ {' '.join(command)}\nexit={result.returncode}\n{output_text}")
        if result.returncode:
            raise BuildError(f"validation step {label} failed ({result.returncode})\n{output_text[-6000:]}")
    validation_text = "\n".join(validation_rows)
    validation_text = re.sub(r"(?im)(Ran \d+ tests in )[0-9.]+s", lambda m: m.group(1) + "<elapsed>", validation_text)
    validation_text = re.sub(r"(?i)\\tmp[a-z0-9_]+", lambda _m: "\\<TEMP>", validation_text)
    validation_text = re.sub(r"(?i)/tmp/[a-z0-9_]+", "/<TEMP>", validation_text)

    review_root = output / "review-source"
    review_files = [
        "src/native/rmod1/dinput8_proxy.cpp", "src/native/rmod1/dinput8_proxy.def",
        "src/native/rmod1/rmod2_inprocess.cpp", "src/native/rmod1/rmod2_inprocess.hpp",
        "src/native/rmod1/runtime_core.cpp", "src/native/rmod1/runtime_core.def",
        "src/native/rmod1/exception_report.hpp", "src/native/rmod1/runtime_log.hpp",
        "src/native/rmod1/core.hpp", "src/native/rmod1/image_mapping.hpp",
        "tools/r_mod1_native_plan.py", "tools/build_r_mod1_candidate.py",
        "tools/build_rmod2_boot_a.py", "tools/build_rmod2_boot_b.py", "tools/audit_dinput8_exports.py",
        "tests/synthetic/test_r_mod2_dinput8.py", "tests/synthetic/test_r_mod2_boot_b.py",
        "tests/rmod1/dinput8_forward_harness.cpp", "tests/rmod1/rmod2_boot_b_harness.cpp",
        "tests/rmod1/rmod2_host_qualified_preflight_harness.cpp", "src/native/rmod1/rmod2_startup_preflight.hpp",
        "tests/rmod1/runtime_image_diff_harness.cpp", "src/native/rmod1/runtime_image_diff.hpp", "research/r-mod1/rmod2-boot-a.md",
        "research/r-mod1/rmod2-boot-a-validation.md", "research/r-mod1/rmod2-boot-b.md",
        "research/r-mod1/rmod2-boot-b-validation.md", "research/r-mod1/status.md",
        "research/r-mod1/bootstrap-and-renderer-compat.md",
    ]
    for relative in review_files:
        src = ROOT / relative
        if not src.is_file():
            continue
        target = review_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
    shutil.copyfile(plan_path, review_root / "native-patch-plan.json")
    shutil.copyfile(work / "f3-products/include/native_plan.hpp", review_root / "native_plan.hpp")
    (review_root / "windows-harness-results.txt").write_text(forward_test+"\n"+bootb_test+"\n"+image_diff_test+"\n"+preflight_compile+"\n"+preflight_test, encoding="utf-8", newline="\n")
    (review_root / "validation-results.txt").write_text(validation_text, encoding="utf-8", newline="\n")
    shutil.copyfile(work / "f3-products/exception-test.txt", review_root / "exception-test.txt") if (work / "f3-products/exception-test.txt").exists() else None
    status = subprocess.run(["git", "status", "--short", "--branch"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    (review_root / "git-state.txt").write_text(f"HEAD={head}\n{status}", encoding="utf-8", newline="\n")
    (review_root / "build-evidence.txt").write_text(
        f"retail_sha256={EXPECTED_RETAIL}\nretail_size=3121214\nF3_runtime_sha256={sha(runtime)}\n"
        f"native_plan_sha256={plan['plan_template_sha256']}\nplan_operations_including_OEP={len(plan['operations'])}\n"
        f"sample_profile_installed_operation_count={len(selected_ids)}\nselected_operations={','.join(selected_ids)}\n"
        "in_process_installer_omits=oep-bootstrap\nproxy_architecture=PE32/I386\n"
        f"windows_forward_harness={forward_test.strip()}\nwindows_bootb_harness={bootb_test.strip()}\n"
        f"windows_image_diff_harness={image_diff_test.strip()}\n"
        f"host_qualified_preflight={preflight_test.strip()}\n"
        "root_cause=non-mode-2 Start contexts were denied by Quick Race participant authorization; previous offset-unit fix remains in the installer\n",
        encoding="ascii", newline="\n")
    rows = [{"path": p.relative_to(review_root).as_posix(), "size": p.stat().st_size, "sha256": sha(p)}
            for p in sorted(review_root.rglob("*")) if p.is_file()]
    (review_root / "archive-index.json").write_text(json.dumps({"schema_version": 1, "files": rows}, indent=2, sort_keys=True)+"\n", encoding="utf-8", newline="\n")
    review_zip = output / "r-mod2-boot-b-implementation-review.zip"
    zip_tree(review_root, review_zip, [p.relative_to(review_root).as_posix() for p in review_root.rglob("*") if p.is_file()])
    manifest = {
        "candidate": "r-mod2-boot-b-practice-checkpoint-start-fix", "qualification": "STATIC_BUILD_PASS_HUMAN_GAME_TEST_PENDING",
        "root_cause": "non-mode-2 Start contexts were denied by the Quick Race participant capability gate",
        "retail_executable_sha256": EXPECTED_RETAIL, "retail_size": 3_121_214,
        "proxy_sha256": sha(package/"dinput8.dll"), "runtime_core_sha256": sha(package/"MRallyeRandomizerRuntime.dll"),
        "ini_sha256": sha(package/"MRallyeRandomizer.ini"), "f3_plan_sha256": plan["plan_template_sha256"],
        "native_operation_count_including_oep_record": len(plan["operations"]),
        "sample_profile_native_operation_count": len(selected_ids),
        "sample_profile_native_operations": selected_ids,
        "oep_operation_installed": False, "renderer_proxy_modified": False,
        "candidate_zip_sha256": sha(candidate_zip), "review_zip_sha256": sha(review_zip),
        "human_game_runtime": "PENDING", "package_files": [{"path": n, "size": (package/n).stat().st_size, "sha256": sha(package/n)} for n in package_files],
    }
    (output / "candidate-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8", newline="\n")
    return manifest


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    try: print(json.dumps(build(args.output),indent=2,sort_keys=True)); return 0
    except (BuildError,OSError,subprocess.SubprocessError,ValueError) as exc: print(f"ERROR: {exc}",file=sys.stderr);return 2

if __name__=="__main__": raise SystemExit(main())
