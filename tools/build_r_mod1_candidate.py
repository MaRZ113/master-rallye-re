#!/usr/bin/env python3
"""Build a reproducible source-only R-MOD1 launcher package from exact retail inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from r_ai1_mixed_class import RETAIL_SHA256, RETAIL_SIZE
from r_mod1_native_plan import build_plan, public_plan, render_cpp_header, sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RETAIL = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
VSWHERE = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")
PACKAGE_FILES = (
    "MRallyeRandomizerLauncher.exe",
    "MRallyeRandomizerRuntime.dll",
    "MRallyeRandomizer.ini",
    "native-patch-plan.json",
    "README.txt",
    "MRallyeRandomizerCrashDecode.py",
    "exception-capture-self-test.txt",
    "runtime-log-self-test.txt",
    "profiles/stock-features-disabled.ini",
    "profiles/randomizer-only.ini",
    "profiles/opponent-extender-only.ini",
    "profiles/both-normal-counts.ini",
    "profiles/menu-seven-no-race.ini",
    "profiles/experimental-five-total-t1.ini",
    "profiles/experimental-six-total-t1.ini",
    "profiles/experimental-seven-total-t1.ini",
    "profiles/experimental-eight-total-t1.ini",
    "profiles/experimental-eight-total-stock.ini",
)
F1_PACKAGE_FILES = (
    "MRallyeRandomizerLauncher.exe", "MRallyeRandomizerRuntime.dll",
    "MRallyeRandomizer.ini", "native-patch-plan.json", "README.txt",
    "MRallyeRandomizerCrashDecode.py", "exception-capture-self-test.txt",
    "runtime-log-self-test.txt", "profiles/safe-stock-v2.ini",
    "profiles/quickrace-t1-v2.ini", "profiles/quickrace-full-v2.ini",
    "profiles/cup-mixed-v2.ini", "profiles/master-diverse-v2.ini",
    "profiles/invitation-t3-v2.ini", "profiles/challenge-full-v2.ini",
    "profiles/extended-seven-menu-only-v2.ini",
)


class CandidateBuildError(RuntimeError):
    pass


def locate_toolchain() -> tuple[Path, Path]:
    if not VSWHERE.is_file():
        raise CandidateBuildError("Visual Studio vswhere.exe is unavailable; MSVC x86/x64 tools are required.")
    result = subprocess.run(
        [str(VSWHERE), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=False,
    )
    install = Path(result.stdout.strip())
    if result.returncode or not install:
        raise CandidateBuildError("Visual Studio C++ x86/x64 component was not found.")
    vcvars = install / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    tools = install / "VC" / "Tools" / "MSVC"
    versions = sorted((path for path in tools.iterdir() if path.is_dir()), key=lambda p: p.name, reverse=True)
    if not vcvars.is_file() or not versions:
        raise CandidateBuildError("MSVC vcvarsall.bat/toolset directory is missing.")
    return vcvars, versions[0]


def compiler_environment(vcvars: Path, architecture: str) -> dict[str, str]:
    batch = (
        "@echo off\r\n"
        f'call "{vcvars}" {architecture} >nul\r\n'
        "if errorlevel 1 exit /b 1\r\n"
        "set\r\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".cmd", encoding="mbcs", delete=False) as handle:
        path = Path(handle.name)
        handle.write(batch)
    try:
        output = subprocess.run(["cmd.exe", "/d", "/c", str(path)], capture_output=True,
                                check=False)
        if output.returncode:
            raise CandidateBuildError("vcvarsall failed: " + output.stderr.decode("mbcs", "replace"))
        env = os.environ.copy()
        for raw_line in output.stdout.decode("mbcs", "replace").splitlines():
            if "=" not in raw_line or raw_line.startswith("="):
                continue
            key, value = raw_line.split("=", 1)
            env[key] = value
        return env
    finally:
        path.unlink(missing_ok=True)


def run(command: list[str], *, cwd: Path, env: dict[str, str], label: str) -> None:
    completed = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                               check=False)
    if completed.stdout:
        sys.stdout.write(completed.stdout.decode("mbcs", "replace"))
    if completed.stderr:
        sys.stderr.write(completed.stderr.decode("mbcs", "replace"))
    if completed.returncode:
        raise CandidateBuildError(f"{label} failed with exit code {completed.returncode}.")


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def diagnostic_profile(randomizer_enabled: bool, opponents_enabled: bool,
                       max_opponents: int, quick_race: int = 0,
                       duplicates: int = 1, addons: int = 0,
                       logging: int = 1, experimental_extended_ai: bool = False) -> str:
    if not 1 <= max_opponents <= 7:
        raise ValueError("diagnostic profile opponent limit must be 1..7")
    if not 0 <= quick_race <= 6:
        raise ValueError("diagnostic profile QuickRace selector must be 0..6")
    if duplicates not in (0, 1) or addons not in (0, 1) or logging not in (0, 1):
        raise ValueError("diagnostic profile numeric selector is outside its supported range")
    return (
        "[General]\nConfigVersion = 1\n\n"
        f"[Randomizer]\nEnabled = {int(randomizer_enabled)}\n"
        f"QuickRace = {quick_race}\nDuplicates = {duplicates}\n\n"
        f"[Opponents]\nEnabled = {int(opponents_enabled)}\n"
        f"MaxOpponents = {max_opponents}\n\n"
        f"[Experimental]\nExtendedAI = {int(experimental_extended_ai)}\n\n"
        f"[Addons]\nInclude = {addons}\n\n[Logging]\nEnabled = {logging}\n"
    )


def v2_profile(quick_race: int = 0, rallye_cup: int = 0,
               master_rallye: int = 0, invitation: int = 0,
               challenge: int = 0, max_opponents: int = 3,
               duplicates: int = 1, addons: int = 0,
               logging: int = 0) -> str:
    values = (quick_race, rallye_cup, master_rallye, invitation, challenge)
    if any(value not in range(7) for value in values):
        raise ValueError("ConfigVersion=2 policies must be in 0..6")
    if not 1 <= max_opponents <= 7 or duplicates not in (0, 1) or addons not in (0, 1) or logging not in (0, 1):
        raise ValueError("ConfigVersion=2 setting is outside its supported range")
    return (
        "[General]\nConfigVersion = 2\n\n[Randomizer]\n"
        f"QuickRace = {quick_race}\nRallyeCup = {rallye_cup}\n"
        f"MasterRallye = {master_rallye}\nInvitation = {invitation}\nChallenge = {challenge}\n"
        f"Duplicates = {duplicates}\n\n[Opponents]\nMaxOpponents = {max_opponents}\n\n"
        f"[Addons]\nInclude = {addons}\n\n[Logging]\nEnabled = {logging}\n"
    )


def legacy_v1_example() -> str:
    """Retain the V1 meanings for reproducible historical v11-v13 builds."""
    return (
        "[General]\nConfigVersion = 1\n\n[Randomizer]\nEnabled = 0\n"
        "QuickRace = 0\nDuplicates = 1\n\n[Opponents]\nEnabled = 0\n"
        "MaxOpponents = 3\n\n[Experimental]\nExtendedAI = 0\n\n"
        "[Addons]\nInclude = 0\n\n[Logging]\nEnabled = 0\n"
    )


def compile_products(work: Path, retail: Path, vsvars: Path,
                     msvc_root: Path, checkpoint: str = "v13") -> tuple[Path, Path, str, str]:
    work.mkdir(parents=True, exist_ok=True)
    include_dir = work / "include"
    include_dir.mkdir()
    dll = work / "MRallyeRandomizerRuntime.dll"
    launcher = work / "MRallyeRandomizerLauncher.exe"

    x86_env = compiler_environment(vsvars, "x64_x86")
    x64_env = compiler_environment(vsvars, "x64")
    cl_x86 = msvc_root / "bin" / "Hostx64" / "x86" / "cl.exe"
    cl_x64 = msvc_root / "bin" / "Hostx64" / "x64" / "cl.exe"
    for compiler in (cl_x86, cl_x64):
        if not compiler.is_file():
            raise CandidateBuildError("Required MSVC host/target compiler is missing: " + str(compiler))

    runtime_source = ROOT / "src" / "native" / "rmod1" / "runtime_core.cpp"
    runtime_def = ROOT / "src" / "native" / "rmod1" / "runtime_core.def"
    g1_flags = ["/DRMOD3_G1_DUPLICATE_REPEAT_FALLBACK=1"] if checkpoint in {"g1", "g2"} else []
    runtime_def_for_build = runtime_def
    if checkpoint == "g2":
        g1_flags.append("/DRMOD3_G2_PLAYER_OVERRIDE=1")
        definition = runtime_def.read_text(encoding="ascii")
        if "MRQuickRacePlayerCarV1=" in definition:
            raise CandidateBuildError("checked-in runtime definition unexpectedly contains the G2-only export")
        runtime_def_for_build = work / "runtime_core_g2.def"
        runtime_def_for_build.write_text(
            definition.rstrip() + "\n    MRQuickRacePlayerCarV1=_MRQuickRacePlayerCarV1@8\n",
            encoding="ascii", newline="\n")
    run([str(cl_x86), "/nologo", "/LD", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
         "/Brepro", "/O2", "/DNDEBUG", *g1_flags, str(runtime_source), "/link", "/DEF:" + str(runtime_def_for_build),
         "user32.lib", "advapi32.lib", "/Brepro", "/OUT:" + str(dll)],
        cwd=work, env=x86_env, label="x86 runtime-core build")

    runtime_bytes = dll.read_bytes()
    if not runtime_bytes:
        raise CandidateBuildError("MSVC reported success but runtime-core DLL is empty.")
    plan = build_plan(retail.read_bytes(), runtime_bytes, checkpoint=checkpoint)
    (include_dir / "native_plan.hpp").write_text(render_cpp_header(plan), encoding="ascii", newline="\n")
    plan_path = work / "native-patch-plan.json"
    plan_path.write_text(json.dumps(public_plan(plan), indent=2, sort_keys=True) + "\n",
                         encoding="utf-8", newline="\n")

    launcher_source = ROOT / "src" / "native" / "rmod1" / "launcher.cpp"
    shared_include = ROOT / "src" / "native" / "rmod1"
    run([str(cl_x64), "/nologo", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX", "/Brepro",
         "/O2", "/DNDEBUG", "/D_WIN32_WINNT=0x0A00", "/I" + str(include_dir),
         "/I" + str(shared_include), str(launcher_source), "/link", "bcrypt.lib", "/Brepro",
         "/SUBSYSTEM:CONSOLE", "/OUT:" + str(launcher)],
        cwd=work, env=x64_env, label="x64 suspended launcher build")

    harness = work / "runtime_exception_harness.exe"
    harness_source = ROOT / "tests" / "rmod1" / "runtime_exception_harness.cpp"
    run([str(cl_x86), "/nologo", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX", "/Brepro",
         "/O2", "/DNDEBUG", "/I" + str(shared_include), str(harness_source),
         "/link", "/Brepro", "/SUBSYSTEM:CONSOLE", "/OUT:" + str(harness)],
        cwd=work, env=x86_env, label="x86 exception-capture harness build")
    harness_dir = work / "exception-harness"
    harness_dir.mkdir()
    harness_copy = harness_dir / harness.name
    dll_copy = harness_dir / dll.name
    shutil.copyfile(harness, harness_copy)
    shutil.copyfile(dll, dll_copy)
    capture_test = subprocess.run([str(harness_copy), str(dll_copy)], cwd=harness_dir,
                                  capture_output=True, text=True, check=False)
    if capture_test.returncode or "RMDIAG_CAPTURE_PASS" not in capture_test.stdout:
        raise CandidateBuildError("Controlled x86 AV-capture harness failed:\n" +
                                  capture_test.stdout + capture_test.stderr)

    log_harness = work / "runtime_log_harness.exe"
    log_harness_source = ROOT / "tests" / "rmod1" / "runtime_log_harness.cpp"
    run([str(cl_x86), "/nologo", "/MT", "/EHsc", "/std:c++17", "/W4", "/WX",
         "/Brepro", "/O2", "/DNDEBUG", "/I" + str(shared_include),
         str(log_harness_source), "/link", "/Brepro", "/SUBSYSTEM:CONSOLE",
         "/OUT:" + str(log_harness)],
        cwd=work, env=x86_env, label="x86 append-only runtime-log harness build")
    log_test = subprocess.run([str(log_harness)], cwd=work, capture_output=True,
                              text=True, check=False)
    if log_test.returncode or "RMOD1_APPEND_LOG_PASS records=3 chronological=1 intact=1" not in log_test.stdout:
        raise CandidateBuildError("Runtime append-log regression harness failed:\n" +
                                  log_test.stdout + log_test.stderr)
    return dll, launcher, capture_test.stdout.strip(), log_test.stdout.strip()


def manifest_for(package: Path, plan: dict, preflight_status: str,
                 checkpoint: str = "v13") -> dict:
    rows = []
    for name in (PACKAGE_FILES if checkpoint == "v13" else F1_PACKAGE_FILES):
        path = package / name
        rows.append({"path": name, "size": path.stat().st_size, "sha256": file_sha(path)})
    candidate_id = {
        "v13": "first-integrated-candidate-v13",
        "f1": "first-integrated-candidate-v14-f1-r3",
        "f2": "first-integrated-candidate-v15-f2",
        "f3": "first-integrated-candidate-v16-f3",
    }[checkpoint]
    summaries = {
        "v13": "preserves the human-tested v13 integrated Quick Race behavior",
        "f1": "ConfigVersion=2 and stable generation-boundary live policy snapshots for Quick Race",
        "f2": "adds separate native generation-owner selectors for Rallye Cup, Invitation and new Master Rallye competitions",
        "f3": "adds a Challenge preview identity cache consumed by the matching race construction path",
    }
    return {
        "schema_version": 1,
        "product": "Master Rallye Randomizer & AI Extender",
        "phase": "R-MOD1-E" if checkpoint == "v13" else "R-MOD1-F",
        "checkpoint": checkpoint,
        "candidate_id": candidate_id,
        "change_summary": summaries[checkpoint],
        "qualification": "STATIC_CANDIDATE_NOT_HUMAN_RUNTIME_QUALIFIED",
        "source_executable_sha256": RETAIL_SHA256,
        "source_executable_size": RETAIL_SIZE,
        "runtime_plan_sha256": plan["plan_template_sha256"],
        "operation_count": len(plan["operations"]),
        "mode_scope": {
            "v13": ["QuickRace", "OpponentCount"],
            "f1": ["QuickRace", "LivePolicyReload"],
            "f2": ["QuickRace", "RallyeCup", "Invitation", "MasterRallye"],
            "f3": ["QuickRace", "RallyeCup", "Invitation", "MasterRallye", "ChallengePreviewSync"],
        }[checkpoint],
        "extended_ai_capability": {
            "static_minimum_ai": 4,
            "static_maximum_ai": 7,
            "runtime_qualified_maximum_ai": 4,
            "higher_counts": "PENDING_HUMAN_RUNTIME",
            "maximum_total_participants": 8,
            "raw_frontend_split_authoritative": False,
            "actual_human_topology_source": "RACE_NUMPLAYERS_AND_PARTICIPANT_PLAYERTYPE_AFTER_SETUP",
            "one_human_qualification_oracle": "experimental_extended_roster_matches",
            "post_setup_start_veto": "NONE; no observer hook installed",
            "native_physical_chooser": "CLASS_POLICY_SEAMS_ONLY_PHYSICAL_ID_DRIVER_ID_REFILL_BODY_RETAIL",
        },
        "suspended_image_preflight": preflight_status,
        "on_disk_executable_modified": False,
        "renderer_proxy_modified": False,
        "files": rows,
    }


def build_candidate(retail_exe: Path, output: Path, *, package_on_error_623: bool = False,
                    checkpoint: str = "v13") -> dict:
    # Path.resolve(strict=True) calls Win32 final-path resolution, which can be
    # denied for protected read-only corpus files even when ordinary read access
    # is allowed. Keep the caller's absolute lexical path and let the exact
    # file/hash checks establish identity.
    retail_exe = Path(os.path.abspath(retail_exe))
    output = Path(os.path.abspath(output))
    if not retail_exe.is_file() or retail_exe.stat().st_size != RETAIL_SIZE or file_sha(retail_exe) != RETAIL_SHA256:
        raise CandidateBuildError("Input must be the exact supported pristine retail MRallye.exe.")
    if output.exists():
        raise CandidateBuildError("Refusing to overwrite an existing candidate directory: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    vcvars, msvc_root = locate_toolchain()
    work = Path(tempfile.mkdtemp(prefix="rmod1-build-", dir=output.parent))
    stage = Path(tempfile.mkdtemp(prefix="rmod1-stage-", dir=output.parent))
    try:
        dll, launcher, exception_test_output, runtime_log_test_output = compile_products(
            work, retail_exe, vcvars, msvc_root, checkpoint=checkpoint)
        plan = json.loads((work / "native-patch-plan.json").read_text(encoding="utf-8"))
        shutil.copyfile(launcher, stage / "MRallyeRandomizerLauncher.exe")
        shutil.copyfile(dll, stage / "MRallyeRandomizerRuntime.dll")
        if checkpoint == "v13":
            ini_bytes = legacy_v1_example().encode("ascii")
        else:
            public_ini = ROOT / "research" / "r-mod1" / "MRallyeRandomizer.example.ini"
            if not public_ini.is_file() or public_ini.stat().st_size > 4096:
                raise CandidateBuildError("Canonical public INI is missing or exceeds the parser limit.")
            ini_bytes = public_ini.read_bytes()
        if len(ini_bytes) > 4096 or any(value > 0x7f for value in ini_bytes):
            raise CandidateBuildError("Canonical package INI must be strict ASCII and <=4096 bytes.")
        (stage / "MRallyeRandomizer.ini").write_bytes(ini_bytes)
        shutil.copyfile(work / "native-patch-plan.json", stage / "native-patch-plan.json")
        shutil.copyfile(ROOT / "tools" / "decode_r_mod1_crash.py",
                        stage / "MRallyeRandomizerCrashDecode.py")
        (stage / "exception-capture-self-test.txt").write_text(
            exception_test_output + "\n", encoding="ascii", newline="\n")
        (stage / "runtime-log-self-test.txt").write_text(
            runtime_log_test_output + "\n", encoding="ascii", newline="\n")
        profiles = stage / "profiles"
        profiles.mkdir()
        profile_rows = {
            "stock-features-disabled.ini": diagnostic_profile(False, False, 3, quick_race=0),
            "randomizer-only.ini": diagnostic_profile(True, False, 3, quick_race=2),
            "opponent-extender-only.ini": diagnostic_profile(False, True, 3, quick_race=0),
            "both-normal-counts.ini": diagnostic_profile(True, True, 3, quick_race=2),
            "menu-seven-no-race.ini": diagnostic_profile(False, True, 7, quick_race=0),
            "experimental-five-total-t1.ini": diagnostic_profile(
                True, True, 4, quick_race=2, experimental_extended_ai=True),
            "experimental-six-total-t1.ini": diagnostic_profile(
                True, True, 5, quick_race=2, experimental_extended_ai=True),
            "experimental-seven-total-t1.ini": diagnostic_profile(
                True, True, 6, quick_race=2, experimental_extended_ai=True),
            "experimental-eight-total-t1.ini": diagnostic_profile(
                True, True, 7, quick_race=2, experimental_extended_ai=True),
            "experimental-eight-total-stock.ini": diagnostic_profile(
                False, True, 7, quick_race=0, experimental_extended_ai=True),
        }
        if checkpoint != "v13":
            profile_rows = {
                "safe-stock-v2.ini": v2_profile(),
                "quickrace-t1-v2.ini": v2_profile(quick_race=1),
                "quickrace-full-v2.ini": v2_profile(quick_race=4),
                "cup-mixed-v2.ini": v2_profile(rallye_cup=5),
                "master-diverse-v2.ini": v2_profile(master_rallye=6),
                "invitation-t3-v2.ini": v2_profile(invitation=3),
                "challenge-full-v2.ini": v2_profile(challenge=4),
                "extended-seven-menu-only-v2.ini": v2_profile(max_opponents=7),
            }
        for name, content in profile_rows.items():
            (profiles / name).write_text(content, encoding="ascii", newline="\n")
        readme = (
            "R-MOD1-E v13 experimental five-to-eight-participant Randomizer and Opponent Extender candidate\n"
            "This package contains no game executable or game assets.\n"
            "Run: MRallyeRandomizerLauncher.exe --verify --game-dir <retail game folder>\n"
            "Before launch run: MRallyeRandomizerLauncher.exe --preflight --game-dir <retail game folder>\n"
            "Proceed only when --preflight reports SUSPENDED_PREFLIGHT_PASS; it terminates the child before resume.\n"
            "Launch: MRallyeRandomizerLauncher.exe --game-dir <retail game folder>\n"
            "Keep MRallye.exe and the graphical d3d8.dll in the game folder unchanged. Remove this package to disable it.\n"
            "The default MRallyeRandomizer.ini is numeric, commented, bounded, and safe.\n"
            "Copy a profile from profiles\\ to this package root as MRallyeRandomizer.ini, then run --verify and --preflight.\n"
            "A: stock-features-disabled.ini. B: randomizer-only.ini. C: opponent-extender-only.ini.\n"
            "D: both-normal-counts.ini. Compare these at one, two, and three AI with the same Quick Race settings.\n"
            "Complete a short race and confirm Results plus return to frontend for A-D. Combined runtime remains pending owner test.\n"
            "The extended gate is opt-in through Experimental.ExtendedAI=1 and MaxOpponents. One human plus 4..7 AI uses\n"
            "5..8 total participants. The raw SplitScreen flag is diagnostic only; verify the actual Race roster after setup.\n"
            "Use the progressive profiles in order: experimental-five-total-t1.ini, experimental-six-total-t1.ini,\n"
            "experimental-seven-total-t1.ini, then experimental-eight-total-t1.ini. Each raises MaxOpponents by one.\n"
            "Confirm each count before increasing the ceiling. experimental-eight-total-stock.ini also exercises the extender\n"
            "with Randomizer disabled. MaxOpponents is the selected-AI ceiling, not a fixed race roster.\n"
            "For the first v13 test use FIVE AI plus one human and capture Race/NumPlayers and each participant PlayerType.\n"
            "The raw frontend SplitScreen flag is logged but is not authoritative before Race participants exist.\n"
            "Do not interpret raw_split_screen=1 as a second human. Actual one-human qualification uses Race/NumPlayers\n"
            "and participant PlayerType from Observatory after setup. No post-setup veto/observer is installed.\n"
            "Choose a course/player configuration that is safe for your installation; Track10, player ID0 and T1 are not\n"
            "global guards or requirements. Stop if the observed Race topology is not one human plus the requested AI.\n"
            "The native setup call is followed by the stock state-10 transition without a premature Race-counter veto.\n"
            "The production patch leaves the native race-scene Broker getter call unchanged; no observer wraps its RET 4 ABI.\n"
            "CONFIG and START records are the only current gameplay diagnostics. Use Observatory/debugger for roster state.\n"
            "For each step confirm transition, actual NumCars/NumPlayers, every CarID/Class/PlayerType/DriverID, active AI,\n"
            "then finish, Results and frontend return. Stop at the first invalid state or unsafe spawn.\n"
            "The native chooser refills its physical-ID pool after unique eligible IDs are consumed, enabling repeated models\n"
            "in separate participant slots. This is static evidence; repeated-ID gameplay remains human-pending.\n"
            "To restore the safe default, use stock-features-disabled.ini or copy the commented example from a clean package.\n"
            "When Logging.Enabled=1, MRallyeRandomizer.log is written beside the game EXE. Crash records remain in\n"
            "MRallyeRandomizer-crash-v1.bin and can be decoded with MRallyeRandomizerCrashDecode.py.\n"
            "This candidate preserves the v7 stdcall tail-forward gateway, v6 UI-stack fix and v5 suspended image preflight.\n"
            "V11 one-human/four-AI runtime pass remains the regression reference. V13 five-to-seven AI are not runtime-qualified.\n"
            "Renderer-proxy compatibility remains unqualified.\n"
        )
        if checkpoint == "f1":
            readme = (
                "R-MOD1-F1 ConfigVersion=2 and live policy reload candidate.\n"
                "This package contains no game executable, game assets, Vehicle SDK or Observatory.\n"
                "Run --verify and --preflight with the exact pristine retail game folder before launch.\n"
                "Launch the original MRallye.exe through MRallyeRandomizerLauncher.exe. The original file remains unchanged.\n"
                "ConfigVersion=2 policy IDs: 0 Stock, 1 T1, 2 T2, 3 T3, 4 Full, 5 Mixed, 6 Diverse.\n"
                "Full samples the eligible class union; Mixed chooses a class then leaves physical identity to native code;\n"
                "Diverse cycles through a shuffled class order. Each mode policy is independent.\n"
                "Edit only Randomizer policies or Duplicates while the game is open. The complete strict ASCII INI is\n"
                "re-read at each fresh roster boundary, then frozen for every AI in that generation. A malformed or\n"
                "half-written edit keeps the last valid snapshot. MaxOpponents, Addons and Logging require restart.\n"
                "A displayed Challenge preview remains frozen until the Challenge hooks arrive in checkpoint F3.\n"
                "This F1 native plan keeps the exact v13 seven-operation Quick Race plan. Cup, Master, Invitation and\n"
                "Challenge remain Stock in this checkpoint even if their V2 policy keys are non-Stock. Do not test those\n"
                "policies yet. F1 human test: Quick Race, edit QuickRace from T1 to Full, create a new race and compare\n"
                "the roster; existing races/restarts are not re-randomized. Capture config version/hash and generation log.\n"
                "Native setup, opponent count, physical CarID/DriverID owners and v13 raw-SplitScreen behavior are retained.\n"
                "No new mode has human runtime qualification in this candidate. Renderer proxy remains unqualified.\n"
            )
        elif checkpoint in {"f2", "f3"}:
            challenge_text = (
                "Challenge uses a prepared absolute opponent CarID shared by Preview name/model and race construction. "
                "It is cached across redraw and Start; Back/reentry clears it. A live INI edit does not replace the "
                "currently visible opponent. Challenge runtime remains unqualified.\n"
                if checkpoint == "f3" else
                "Challenge remains on the authored Stock matchup in this F2 checkpoint.\n"
            )
            readme = (
                f"R-MOD1-{checkpoint.upper()} all-mode policy checkpoint.\n"
                "This package contains no game executable, game assets, Vehicle SDK or Observatory.\n"
                "Run --verify and --preflight with the exact pristine retail game folder before launch. Launch the "
                "original MRallye.exe through MRallyeRandomizerLauncher.exe; the retail file remains unchanged.\n"
                "ConfigVersion=2 uses 0 Stock, 1 T1, 2 T2, 3 T3, 4 Full, 5 Mixed and 6 Diverse for each mode.\n"
                "Full samples the eligible physical vehicle union; Mixed chooses an eligible class then retains native "
                "physical-ID/DriverID ownership; Diverse uses the shuffled class-cycle policy.\n"
                "F2 enables only the native new-roster owners for Quick Race, new Rallye Cup/Invitation creation and "
                "new Master Rallye competitions. Cup/Invitation stages and Master Rallye save/Resume reuse the "
                "native roster; no stage reroll is installed.\n" + challenge_text +
                "Edit Randomizer policies or Duplicates while running. A fully validated snapshot is read only at a "
                "fresh roster boundary and frozen for the entire generated roster. Invalid or half-written edits keep "
                "the last valid snapshot. MaxOpponents, Addons and Logging are startup-scoped.\n"
                "The safe example starts with all policies Stock and MaxOpponents=3. Copy a profile only for the "
                "specific mode under test. Profiles are configuration examples, not runtime evidence.\n"
                "Run one short human test at a time. Check initial generation, native stage/save reuse, physical "
                "CarID/Class/DriverID and full gameplay before advancing. No F2/F3 mode is claimed runtime-qualified "
                "by this static package. The established v13 five-participant Quick Race is the prior runtime baseline.\n"
                "No Vehicle SDK/addon provider, renderer change, DLL proxy or patched EXE is included.\n"
            )
        (stage / "README.txt").write_text(readme, encoding="ascii", newline="\n")
        verify = subprocess.run(
            [str(stage / "MRallyeRandomizerLauncher.exe"), "--verify", "--game-dir", str(retail_exe.parent)],
            capture_output=True, text=True, check=False,
        )
        if verify.returncode:
            raise CandidateBuildError("Candidate self-verification failed:\n" + verify.stdout + verify.stderr)
        preflight = subprocess.run(
            [str(stage / "MRallyeRandomizerLauncher.exe"), "--preflight", "--game-dir", str(retail_exe.parent)],
            capture_output=True, text=True, check=False,
        )
        preflight_ok = preflight.returncode == 0 and "SUSPENDED_PREFLIGHT_PASS" in preflight.stdout
        if not preflight_ok and not (
            package_on_error_623 and "Windows error 623" in preflight.stderr
        ):
            raise CandidateBuildError("Windows suspended-process preflight failed:\n" +
                                      preflight.stdout + preflight.stderr)
        preflight_status = ("WINDOWS_PASS_BEFORE_NATIVE_WRITES" if preflight_ok
                            else "PENDING_ENVIRONMENT_CREATEPROCESS_ERROR_623")
        verification_log = (
            "=== --verify ===\n" + verify.stdout + verify.stderr +
            "\n=== --preflight ===\n" + preflight.stdout + preflight.stderr
        )
        (stage / "self-verification.txt").write_text(verification_log, encoding="utf-8", newline="\n")
        result = manifest_for(stage, plan, preflight_status, checkpoint=checkpoint)
        result["files"].append({"path": "self-verification.txt", "size": (stage / "self-verification.txt").stat().st_size,
                                "sha256": file_sha(stage / "self-verification.txt")})
        (stage / "candidate-manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                                       encoding="utf-8", newline="\n")
        os.replace(stage, output)
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retail-exe", type=Path, default=DEFAULT_RETAIL)
    parser.add_argument("--output", type=Path, default=ROOT / ".research-output" / "r-mod1" / "first-integrated-candidate-v13")
    parser.add_argument("--package-on-preflight-error-623", action="store_true",
                        help="package a clearly pending candidate only when this host reports ERROR_ILLEGAL_DLL_RELOCATION before mapping")
    parser.add_argument("--checkpoint", choices=("v13", "f1", "f2", "f3"), default="v13")
    args = parser.parse_args()
    try:
        print(json.dumps(build_candidate(args.retail_exe, args.output,
                                         package_on_error_623=args.package_on_preflight_error_623,
                                         checkpoint=args.checkpoint),
                          indent=2, sort_keys=True))
        return 0
    except (CandidateBuildError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"R-MOD1 candidate build failed closed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
