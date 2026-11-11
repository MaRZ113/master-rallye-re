#!/usr/bin/env python3
"""Build/verify the isolated R-MOD3-G2 Quick Race player-vehicle candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from audit_dinput8_exports import audit
from build_r_mod1_candidate import compile_products, locate_toolchain
from build_rmod2_boot_a import run
from build_rmod3_g1_candidate import (
    G1BuildError, _candidate_files, _compile_g1_proxy, _run_bootstrap_harnesses,
    deterministic_zip,
)
from r_ai1_mixed_class import RETAIL_SHA256, RETAIL_SIZE
from r_mod1_native_plan import build_plan, public_plan, render_cpp_header


ROOT = Path(__file__).resolve().parents[1]
RETAIL = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
OUT = ROOT / ".research-output" / "r-mod3" / "g2" / "first-integrated-candidate-g2"
MAX_CONFIG = 4096


class G2BuildError(RuntimeError):
    pass


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def v3_profile(*, player_mode: int = 0, forced_car_id: int = 0,
                random_policy: int = 4, quick_race: int = 0,
                max_opponents: int = 3, logging: int = 1) -> str:
    if player_mode not in range(3) or forced_car_id not in range(25) or random_policy not in range(7):
        raise ValueError("player vehicle setting is outside ConfigVersion=3 range")
    if quick_race not in range(7) or not 1 <= max_opponents <= 7 or logging not in (0, 1):
        raise ValueError("AI policy or opponent limit is outside supported range")
    return (
        "[General]\nConfigVersion = 3\n\n[Randomizer]\n"
        f"QuickRace = {quick_race}\nRallyeCup = 0\nMasterRallye = 0\n"
        "Invitation = 0\nChallenge = 0\nDuplicates = 1\n\n"
        f"[Opponents]\nMaxOpponents = {max_opponents}\n\n"
        "[Addons]\nInclude = 0\n\n"
        f"[Logging]\nEnabled = {logging}\n\n"
        f"[Player]\nMode = {player_mode}\nForcedCarID = {forced_car_id}\n"
        f"RandomPolicy = {random_policy}\n"
    )


def package_files(package: Path) -> list[str]:
    return sorted(path.relative_to(package).as_posix()
                  for path in package.rglob("*") if path.is_file())


def verify_package(package: Path, archive_path: Path, retail_exe: Path) -> dict:
    retail_exe = Path(os.path.abspath(retail_exe))
    if not retail_exe.is_file() or retail_exe.stat().st_size != RETAIL_SIZE or file_sha(retail_exe) != RETAIL_SHA256:
        raise G2BuildError("verification requires the exact pristine retail executable")
    manifest_path = package / "candidate-manifest.json"
    if not manifest_path.is_file():
        raise G2BuildError("G2 candidate manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_executable_sha256") != RETAIL_SHA256 or manifest.get("source_executable_size") != RETAIL_SIZE:
        raise G2BuildError("candidate is pinned to an unexpected retail executable")
    for row in manifest.get("files", []):
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise G2BuildError("manifest contains an unsafe package path")
        path = package / relative
        if not path.is_file() or path.stat().st_size != row["size"] or file_sha(path) != row["sha256"]:
            raise G2BuildError("candidate package file failed hash/size verification: " + row["path"])
    names = {path.name.casefold() for path in package.rglob("*") if path.is_file()}
    if names & {"mrallye.exe", "data.sma", "d3d8.dll"}:
        raise G2BuildError("candidate must not contain the game EXE, Data.sma, or the graphical renderer proxy")
    if any(path.suffix.casefold() in {".dx", ".dxt", ".gxm", ".gxi", ".dump", ".bin"}
           for path in package.rglob("*")):
        raise G2BuildError("candidate unexpectedly contains game assets or raw dumps")

    runtime = package / "MRallyeRandomizerRuntime.dll"
    rebuilt = public_plan(build_plan(retail_exe.read_bytes(), runtime.read_bytes(), checkpoint="g2"))
    packaged = json.loads((package / "native-patch-plan.json").read_text(encoding="utf-8"))
    if rebuilt != packaged:
        raise G2BuildError("packaged G2 native plan does not reproduce from exact retail/runtime inputs")
    proxy_audit = audit(package / "dinput8.dll")
    if proxy_audit.get("required_match") is not True:
        raise G2BuildError("G2 DirectInput proxy exports differ from the audited BOOT-A contract")
    if not archive_path.is_file():
        raise G2BuildError("G2 candidate ZIP is missing")
    with zipfile.ZipFile(archive_path) as archive:
        names_in_zip = archive.namelist()
        if sorted(names_in_zip) != package_files(package):
            raise G2BuildError("G2 ZIP file set differs from the verified package tree")
        for name in names_in_zip:
            if archive.read(name) != (package / name).read_bytes():
                raise G2BuildError("G2 ZIP content mismatch: " + name)
    return {
        "status": "G2_STATIC_CANDIDATE_PACKAGE_VERIFIED",
        "qualification": manifest["qualification"],
        "candidate": manifest["candidate"],
        "runtime_core_sha256": file_sha(runtime),
        "directinput_proxy_sha256": file_sha(package / "dinput8.dll"),
        "native_plan_sha256": rebuilt["plan_template_sha256"],
        "operation_count": len(rebuilt["operations"]),
        "package_zip_sha256": file_sha(archive_path),
        "source_executable_sha256": file_sha(retail_exe),
        "source_executable_unchanged": True,
    }


def build(output: Path = OUT, retail_exe: Path = RETAIL) -> dict:
    retail_exe = Path(os.path.abspath(retail_exe))
    output = Path(os.path.abspath(output))
    if not retail_exe.is_file() or retail_exe.stat().st_size != RETAIL_SIZE or file_sha(retail_exe) != RETAIL_SHA256:
        raise G2BuildError("input must be the exact pristine retail MRallye.exe")
    if output.exists():
        raise G2BuildError("refusing to overwrite an existing G2 candidate directory: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="rmod3-g2-build-", dir=output.parent))
    stage = Path(tempfile.mkdtemp(prefix="rmod3-g2-stage-", dir=output.parent))
    try:
        vcvars, msvc_root = locate_toolchain()
        products = work / "products"
        runtime, _launcher, exception_test, log_test = compile_products(
            products, retail_exe, vcvars, msvc_root, checkpoint="g2")
        generated_plan = json.loads((products / "native-patch-plan.json").read_text(encoding="utf-8"))
        rebuilt = build_plan(retail_exe.read_bytes(), runtime.read_bytes(), checkpoint="g2")
        if public_plan(rebuilt) != generated_plan:
            raise G2BuildError("compile_products G2 plan differs from independent deterministic rebuild")
        header = render_cpp_header(rebuilt)

        proxy, exports, x86_env = _compile_g1_proxy(
            work / "g2-proxy", runtime, header, vcvars, msvc_root, g2=True)
        harnesses = _run_bootstrap_harnesses(
            work / "g2-harnesses", proxy, runtime, x86_env, msvc_root, checkpoint="g2")

        package = stage / "package"
        profiles = package / "profiles"
        profiles.mkdir(parents=True)
        shutil.copyfile(proxy, package / "dinput8.dll")
        shutil.copyfile(runtime, package / "MRallyeRandomizerRuntime.dll")
        (package / "MRallyeRandomizer.ini").write_text(v3_profile(), encoding="ascii", newline="\n")
        (package / "native-patch-plan.json").write_text(
            json.dumps(generated_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        profile_rows = {
            "safe-stock-v3.ini": v3_profile(),
            "forced-id12.ini": v3_profile(player_mode=1, forced_car_id=12),
            "random-t1.ini": v3_profile(player_mode=2, random_policy=1),
            "random-t2.ini": v3_profile(player_mode=2, random_policy=2),
            "random-full.ini": v3_profile(player_mode=2, random_policy=4),
            "g1-seven-ai-t1-regression.ini": v3_profile(quick_race=1, max_opponents=7),
        }
        for name, content in profile_rows.items():
            encoded = content.encode("ascii")
            if len(encoded) > MAX_CONFIG:
                raise G2BuildError("generated ConfigVersion=3 profile exceeds the 4096-byte parser limit: " + name)
            (profiles / name).write_bytes(encoded)

        readme = (
            "R-MOD3-G2 experimental Quick Race player-vehicle candidate\n\n"
            "This is a development test package, separate from the published Beta and G1 reference. It contains no\n"
            "game executable or game assets. Use a disposable copy of the supported retail installation.\n"
            "The original MRallye.exe and graphical d3d8.dll remain untouched. Do not overwrite another dinput8.dll\n"
            "proxy; use a clean test copy and preserve any renderer wrapper. This package does not require Vehicle SDK.\n\n"
            "Copy one profiles\\*.ini file to MRallyeRandomizer.ini beside the original game, then launch MRallye.exe\n"
            "normally. Remove only dinput8.dll, MRallyeRandomizerRuntime.dll, MRallyeRandomizer.ini and this mod's log\n"
            "to disable it. The proxy forwards the audited DirectInput exports to Windows and does not import d3d8.dll.\n"
            "The default profile leaves the player and AI policies Stock. ConfigVersion=2 continues to use its existing\n"
            "parser and policy meanings; only ConfigVersion=3 accepts [Player].\n\n"
            "Forced test: install forced-id12.ini. Enter Quick Race Vehicle Select and check the displayed car, then\n"
            "Start and confirm Race/Car0/CarID is the same physical ID. Random test: install random-t1.ini, enter\n"
            "Vehicle Select, record the car and confirm it does not change while staying on that screen; Start and check\n"
            "Race/Car0/CarID. Leave and re-enter to verify a new selection may occur. Then restore safe-stock-v3.ini.\n"
            "The G1 seven-AI regression profile is optional and should be used only after the forced/random checks pass.\n\n"
            "Native static ownership: Quick Race Vehicle Select constructor FUN_0047AB30 reads Frontend/QuickRace/Car0\n"
            "at 0x0047AC50 and publishes it as VehicleSelect/CarModel. Quick Race setup FUN_0047B780 reads the same\n"
            "Car0 at 0x0047B78A before it publishes Race/Car0/CarID and derives class from the physical record.\n"
            "The G2 callbacks prepare once at the constructor boundary and consume the prepared ID at setup. Native\n"
            "participant, controller, PlayerType and DriverID creation remain owned by retail. Vehicle browsing while\n"
            "an override is active is not intercepted yet: confirm the displayed/committed identity and report any\n"
            "mismatch. This candidate is not human-runtime-qualified.\n\n"
            "Cup, Master Rallye, Invitation and Challenge are not modified for player-car selection. Existing G1\n"
            "duplicate handling and the F3 mode/Challenge plan remain present. No new add-on support is enabled.\n"
        )
        (package / "README.txt").write_text(readme, encoding="ascii", newline="\n")
        listed = package_files(package)
        rows = [{"path": name, "size": (package / name).stat().st_size,
                 "sha256": file_sha(package / name)} for name in listed]
        manifest = {
            "schema_version": 1,
            "candidate": "first-integrated-candidate-g2",
            "phase": "R-MOD3-G2",
            "qualification": "READY_FOR_HUMAN_GAMEPLAY_TESTING",
            "scope": "Quick Race player zero forced/random selection only",
            "g1_baseline": {
                "status": "OWNER_CONFIRMED_RUNTIME_AND_BROKER_EVIDENCE",
                "complete_eight_participant_t2_race": True,
                "duplicate_id": 8,
                "duplicate_slots": [3, 7],
                "separate_driver_ids": [6, 5],
                "all_finished_and_eight_results": True,
                "candidate_sha256_supplied": False,
            },
            "source_executable_sha256": RETAIL_SHA256,
            "source_executable_size": RETAIL_SIZE,
            "runtime_core_sha256": file_sha(runtime),
            "directinput_proxy_sha256": file_sha(proxy),
            "native_plan_sha256": generated_plan["plan_template_sha256"],
            "native_operation_count": len(generated_plan["operations"]),
            "g2_operations": ["quickrace-player-select-entry", "quickrace-player-setup-consume"],
            "config_version_2_unchanged": True,
            "original_executable_modified": False,
            "graphical_d3d8_modified": False,
            "vehicle_sdk_required": False,
            "files": rows,
        }
        _write_json(package / "candidate-manifest.json", manifest)
        archive_path = stage / "first-integrated-candidate-g2.zip"
        deterministic_zip(package, archive_path, package_files(package))
        verification = verify_package(package, archive_path, retail_exe)
        _write_json(stage / "candidate-build-evidence.json", {
            "source_executable_sha256": file_sha(retail_exe),
            "runtime_core_sha256": file_sha(runtime),
            "directinput_proxy_sha256": file_sha(proxy),
            "proxy_export_audit": exports,
            "native_plan_sha256": generated_plan["plan_template_sha256"],
            "native_operation_count": len(generated_plan["operations"]),
            "native_patch_ids": [row["id"] for row in generated_plan["operations"]],
            "runtime_exception_harness": exception_test,
            "runtime_log_harness": log_test,
            "bootstrap_harnesses": harnesses,
            "verification": verification,
            "test_status": "STATIC_ONLY_HUMAN_RUNTIME_PENDING",
            "package_zip_sha256": file_sha(archive_path),
            "package_zip_size": archive_path.stat().st_size,
        })
        (stage / "native_plan.hpp").write_text(header, encoding="ascii", newline="\n")
        os.replace(stage, output)
        return {**manifest, "package_zip": str(output / archive_path.name),
                "package_zip_sha256": file_sha(output / archive_path.name),
                "proxy_exports": exports, "bootstrap_harnesses": harnesses}
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def verify(output: Path = OUT, retail_exe: Path = RETAIL) -> dict:
    root = Path(os.path.abspath(output))
    package = root / "package"
    return verify_package(package, root / "first-integrated-candidate-g2.zip", retail_exe)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--retail-exe", type=Path, default=RETAIL)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.output, args.retail_exe) if args.verify else build(args.output, args.retail_exe)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (G2BuildError, G1BuildError, OSError, ValueError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        print("R-MOD3-G2 candidate failed closed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
