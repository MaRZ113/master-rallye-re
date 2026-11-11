#!/usr/bin/env python3
"""Verify a generated R-MOD1 package and exercise safe launcher rejection paths."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from r_ai1_mixed_class import RETAIL_SHA256, RETAIL_SIZE
from r_mod1_native_plan import build_plan, public_plan, parse_pe, va_to_file_offset


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_launcher(launcher: Path, game_dir: Path, mode: str = "--verify") -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(launcher), mode, "--game-dir", str(game_dir)],
                          capture_output=True, text=True, check=False)


def verify_package(candidate: Path, retail_exe: Path, *, allow_preflight_blocked: bool = False) -> dict:
    candidate = candidate.absolute()
    retail_exe = retail_exe.absolute()
    manifest_path = candidate / "candidate-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest["qualification"] == "STATIC_CANDIDATE_NOT_HUMAN_RUNTIME_QUALIFIED",
            "candidate must not claim human runtime qualification")
    require(manifest["source_executable_sha256"] == RETAIL_SHA256 and
            manifest["source_executable_size"] == RETAIL_SIZE,
            "manifest does not pin the exact supported retail image")
    require(manifest.get("suspended_image_preflight") in {
                "WINDOWS_PASS_BEFORE_NATIVE_WRITES",
                "PENDING_ENVIRONMENT_CREATEPROCESS_ERROR_623",
            }, "candidate manifest lacks an explicit suspended-image preflight status")
    candidate_identity = {
        ("R-MOD1-D", "first-integrated-candidate-v11"),
        ("R-MOD1-E", "first-integrated-candidate-v12"),
        ("R-MOD1-E", "first-integrated-candidate-v13"),
        ("R-MOD1-F", "first-integrated-candidate-v14-f1"),
        ("R-MOD1-F", "first-integrated-candidate-v14-f1-r2"),
        ("R-MOD1-F", "first-integrated-candidate-v14-f1-r3"),
        ("R-MOD1-F", "first-integrated-candidate-v15-f2"),
        ("R-MOD1-F", "first-integrated-candidate-v16-f3"),
    }
    require((manifest.get("phase"), manifest.get("candidate_id")) in candidate_identity,
            "candidate identity is neither the preserved D/v11 baseline nor a supported E candidate")
    if manifest["candidate_id"] == "first-integrated-candidate-v12":
        capability = manifest.get("extended_ai_capability", {})
        require(capability == {
                    "static_minimum_ai": 4,
                    "static_maximum_ai": 7,
                    "runtime_qualified_maximum_ai": 4,
                    "higher_counts": "PENDING_HUMAN_RUNTIME",
                    "maximum_total_participants": 8,
                    "split_screen_extended": False,
                    "native_physical_chooser": "CLASS_POLICY_SEAMS_ONLY_PHYSICAL_ID_DRIVER_ID_REFILL_BODY_RETAIL",
                }, "v12 candidate manifest must separate static and runtime count evidence")
    if manifest["candidate_id"] == "first-integrated-candidate-v13":
        capability = manifest.get("extended_ai_capability", {})
        require(capability.get("raw_frontend_split_authoritative") is False and
                capability.get("actual_human_topology_source") ==
                    "RACE_NUMPLAYERS_AND_PARTICIPANT_PLAYERTYPE_AFTER_SETUP" and
                capability.get("one_human_qualification_oracle") == "experimental_extended_roster_matches" and
                capability.get("post_setup_start_veto") == "NONE; no observer hook installed" and
                capability.get("maximum_total_participants") == 8,
                "v13 must record diagnostic-only raw SplitScreen and the authoritative topology oracle")
    require(digest(retail_exe) == RETAIL_SHA256 and retail_exe.stat().st_size == RETAIL_SIZE,
            "provided retail executable does not match the exact build")
    rows = manifest["files"]
    listed = {row["path"] for row in rows}
    require(len(listed) == len(rows), "manifest contains duplicate file paths")
    for row in rows:
        path = candidate / row["path"]
        require(path.is_file() and not path.is_symlink(), "missing/linked package file: " + row["path"])
        require(path.stat().st_size == row["size"] and digest(path) == row["sha256"],
                "package file hash/size mismatch: " + row["path"])
    require("MRallye.exe" not in {path.name for path in candidate.rglob("*") if path.is_file()},
            "candidate package must not contain the proprietary game executable")
    require(not any(path.suffix.lower() in {".dx", ".dxt", ".dump", ".bin"}
                    for path in candidate.rglob("*") if path.is_file()),
            "candidate package must not contain game assets or raw dumps")
    readme = (candidate / "README.txt").read_text(encoding="ascii")
    if manifest["candidate_id"] == "first-integrated-candidate-v13":
        require("raw frontend SplitScreen flag is logged but is not authoritative" in readme and
                "Extended SplitScreen is refused" not in readme,
                "v13 handoff must not reintroduce the false raw SplitScreen veto")
    plan = json.loads((candidate / "native-patch-plan.json").read_text(encoding="utf-8"))
    exception_test = (candidate / "exception-capture-self-test.txt").read_text(encoding="ascii")
    require("RMDIAG_CAPTURE_PASS" in exception_test and "first_chance_av=preserved" in exception_test,
            "runtime DLL first-chance exception diagnostics did not pass the controlled x86 harness")
    log_test = (candidate / "runtime-log-self-test.txt").read_text(encoding="ascii")
    require("RMOD1_APPEND_LOG_PASS records=3 chronological=1 intact=1" in log_test,
            "native append-only logger regression harness did not pass")
    require(plan["status"] == "STATICALLY_VERIFIED_RUNTIME_PLAN_TEMPLATE" and
            plan["runtime_qualified"] is False, "native plan incorrectly claims runtime qualification")
    expected_operations = {"v13": 7, "f1": 7, "f2": 13, "f3": 17}.get(manifest.get("checkpoint"))
    require(expected_operations is not None and
            len(plan["operations"]) == manifest["operation_count"] == expected_operations,
            "unexpected integrated native operation count for checkpoint")
    if manifest["candidate_id"] in {"first-integrated-candidate-v12", "first-integrated-candidate-v13"}:
        limits = plan["limits"]
        require(limits["static_extended_ai_minimum"] == 4 and
                limits["static_extended_ai_maximum"] == 7 and
                limits["runtime_qualified_extended_ai"] == 4 and
                limits["runtime_qualified_total_participants"] == 5 and
                limits["higher_count_runtime"] == "PENDING_HUMAN_QUALIFICATION" and
                limits["maximum_total_participants"] == 8,
                "extended plan must separate the static 4..7 envelope from runtime qualification")
        if manifest["candidate_id"] == "first-integrated-candidate-v13":
            require(limits.get("raw_frontend_split_authoritative") is False and
                    limits.get("post_setup_start_veto") == "NONE; no observer hook installed",
                    "v13 plan must preserve diagnostic-only raw SplitScreen handling without a post-setup veto")
    feature_masks = {row["id"]: row["feature_mask"] for row in plan["operations"]}
    expected_feature_masks = {
        "oep-bootstrap": 4,
        "quickrace-selector-init": 1,
        "quickrace-selector-loop": 1,
        "quickrace-selector-end": 1,
        "opponent-list-append": 2,
        "opponent-arrow-bound": 2,
        "quickrace-start-guard": 2,
    }
    if manifest["checkpoint"] in {"f2", "f3"}:
        expected_feature_masks.update({
            "masterrallye-selector-init": 1,
            "masterrallye-selector-loop": 1,
            "masterrallye-selector-end": 1,
            "cup-invitation-selector-init": 1,
            "cup-invitation-selector-loop": 1,
            "cup-invitation-selector-end": 1,
        })
    if manifest["checkpoint"] == "f3":
        expected_feature_masks.update({
            "challenge-preview-identity": 1,
            "challenge-screen-entry-reset": 1,
            "challenge-back-reset": 1,
            "challenge-race-consume": 1,
        })
    require(feature_masks == expected_feature_masks,
            "native plan does not preserve per-mode feature ownership")
    if manifest["checkpoint"] in {"f2", "f3"}:
        require(plan["mode_generation_owners"]["MasterRallye"]["selection_sites"] ==
                [0x451E90, 0x4520D2, 0x45202D] and
                plan["mode_generation_owners"]["RallyeCup"]["selection_sites"] ==
                [0x45AC79, 0x45AF0F, 0x45AE66] and
                plan["mode_generation_owners"]["Invitation"]["shared_builder"] == "RallyeCup" and
                plan["mode_generation_owners"]["MasterRallye"]["existing_roster"] == "native save/load reuse",
                "F2 must hook only the native new-roster selector owners")
    if manifest["checkpoint"] == "f3":
        require(plan["mode_generation_owners"]["Challenge"]["preview_car_id"] == 0x45EC35 and
                plan["mode_generation_owners"]["Challenge"]["race_consume_car_id"] == 0x45010E and
                "ChallengePreviewCache" in plan["mode_generation_owners"]["Challenge"]["lifetime"],
                "F3 must share one prepared physical ID across preview and race construction")
    getter_va = 0x0040869B
    retail_bytes = retail_exe.read_bytes()
    getter_offset = va_to_file_offset(parse_pe(retail_bytes), getter_va, 5)
    require(retail_bytes[getter_offset:getter_offset + 5] == bytes.fromhex("e8c0e00c00"),
            "exact retail NumCars getter call preimage changed")
    require(not any(int(row["va"]) <= getter_va <
                    int(row["va"]) + len(bytes.fromhex(row["replacement_hex"]))
                    for row in plan["operations"]),
            "production patch plan must leave the native RET 4 getter call untouched")
    require("MRObserveInitializedQuickRaceV1" not in plan["runtime_core"]["required_exports"] and
            "MRObserveInitializedQuickRaceV1" not in plan["data_symbols"]["exports"],
            "runtime plan still contains the removed observer callback wiring")
    ranges = sorted((int(row["rva"]), int(row["rva"]) + len(bytes.fromhex(row["replacement_hex"])))
                    for row in plan["operations"])
    require(all(left[1] <= right[0] for left, right in zip(ranges, ranges[1:])),
            "integrated native image operations overlap")
    require(plan["executable_image_modification"] is False and
            plan["renderer_proxy_modified"] is False,
            "plan claims an on-disk EXE or renderer proxy modification")
    if manifest["candidate_id"] == "first-integrated-candidate-v14-f1-r2":
        # Preserve the frozen F1-r2 handoff verbatim. Its executable operation
        # bytes are pinned by this plan identity; later plans improve selector
        # address metadata and are emitted under a new candidate ID.
        require(plan["plan_template_sha256"] ==
                "4375139fbfdf4ee2b4b6b729358c734de2e737a8d2d043dea7cabe71e356aa05",
                "frozen F1-r2 plan identity changed")
    else:
        regenerated = public_plan(build_plan(retail_exe.read_bytes(),
                                             (candidate / "MRallyeRandomizerRuntime.dll").read_bytes(),
                                             checkpoint=manifest.get("checkpoint", "v13")))
        regenerated_bytes = (json.dumps(regenerated, indent=2, sort_keys=True) + "\n").encode("utf-8")
        require((candidate / "native-patch-plan.json").read_bytes() == regenerated_bytes,
                "native plan does not reproduce from the exact retail image and packaged runtime DLL")

    launcher = candidate / "MRallyeRandomizerLauncher.exe"
    positive = run_launcher(launcher, retail_exe.parent)
    require(positive.returncode == 0 and "VERIFY_PASS" in positive.stdout,
            "launcher positive exact-build verifier failed: " + positive.stdout + positive.stderr)
    if manifest.get("checkpoint") != "v13":
        require("effective_numeric_config=config_version=2,randomizer=0,quickrace=0:Stock,modes=0:Stock,0:Stock,0:Stock,0:Stock,0:Stock,duplicates=1:WhenNeeded,opponents=0,max_ai=3,experimental_extended_ai=0,addons=0:StockOnly,logging=0" in positive.stdout,
                "F1 package must verify as a safe ConfigVersion=2 snapshot")
        profile_expectations = (
            ("safe-stock-v2.ini", "config_version=2,randomizer=0"),
            ("quickrace-t1-v2.ini", "config_version=2,randomizer=1,quickrace=1:T1"),
            ("quickrace-full-v2.ini", "config_version=2,randomizer=1,quickrace=4:Full"),
            ("cup-mixed-v2.ini", "config_version=2,randomizer=1"),
            ("master-diverse-v2.ini", "config_version=2,randomizer=1"),
            ("invitation-t3-v2.ini", "config_version=2,randomizer=1"),
            ("challenge-full-v2.ini", "config_version=2,randomizer=1"),
            ("extended-seven-menu-only-v2.ini", "config_version=2,randomizer=0"),
        )
    else:
        require("effective_numeric_config=randomizer=0,quickrace=0:Stock,duplicates=1:WhenNeeded,opponents=0,max_ai=3,experimental_extended_ai=0,addons=0:StockOnly,logging=0" in positive.stdout,
                "packaged public INI is not the safe numeric stock default")
        profile_expectations = (
            ("stock-features-disabled.ini", "randomizer=0"),
            ("randomizer-only.ini", "randomizer=1,quickrace=2:T1"),
            ("opponent-extender-only.ini", "randomizer=0,quickrace=0:Stock,duplicates=1:WhenNeeded,opponents=1,max_ai=3"),
            ("both-normal-counts.ini", "randomizer=1,quickrace=2:T1,duplicates=1:WhenNeeded,opponents=1,max_ai=3"),
            ("menu-seven-no-race.ini", "randomizer=0,quickrace=0:Stock,duplicates=1:WhenNeeded,opponents=1,max_ai=7"),
            ("experimental-five-total-t1.ini", "randomizer=1,quickrace=2:T1,duplicates=1:WhenNeeded,opponents=1,max_ai=4,experimental_extended_ai=1"),
            ("experimental-six-total-t1.ini", "randomizer=1,quickrace=2:T1,duplicates=1:WhenNeeded,opponents=1,max_ai=5,experimental_extended_ai=1"),
            ("experimental-seven-total-t1.ini", "randomizer=1,quickrace=2:T1,duplicates=1:WhenNeeded,opponents=1,max_ai=6,experimental_extended_ai=1"),
            ("experimental-eight-total-t1.ini", "randomizer=1,quickrace=2:T1,duplicates=1:WhenNeeded,opponents=1,max_ai=7,experimental_extended_ai=1"),
            ("experimental-eight-total-stock.ini", "randomizer=0,quickrace=0:Stock,duplicates=1:WhenNeeded,opponents=1,max_ai=7,experimental_extended_ai=1"),
        )
    with tempfile.TemporaryDirectory(prefix="rmod1-profile-check-", dir=candidate.parent) as profile_root_text:
        profile_root = Path(profile_root_text)
        for profile_name, expected in profile_expectations:
            if not (candidate / "profiles" / profile_name).is_file():
                if manifest["candidate_id"] in {"first-integrated-candidate-v12", "first-integrated-candidate-v13"}:
                    raise RuntimeError("candidate is missing its progressive profile: " + profile_name)
                continue
            configured = profile_root / profile_name.replace(".ini", "")
            configured.mkdir()
            shutil.copyfile(launcher, configured / launcher.name)
            shutil.copyfile(candidate / "MRallyeRandomizerRuntime.dll", configured / "MRallyeRandomizerRuntime.dll")
            shutil.copyfile(candidate / "profiles" / profile_name, configured / "MRallyeRandomizer.ini")
            result = run_launcher(configured / launcher.name, retail_exe.parent)
            require(result.returncode == 0 and expected in result.stdout,
                    "numeric profile does not resolve to expected effective configuration: " + profile_name)
    suspended = run_launcher(launcher, retail_exe.parent, "--preflight")
    preflight_status = "WINDOWS_PASS_BEFORE_NATIVE_WRITES"
    if (suspended.returncode != 0 or "SUSPENDED_PREFLIGHT_PASS" not in suspended.stdout or
            "native_writes=0" not in suspended.stdout or "child_terminated_before_resume=1" not in suspended.stdout):
        if allow_preflight_blocked and "Windows error 623" in suspended.stderr:
            preflight_status = "BLOCKED_ENVIRONMENT_CREATEPROCESS_ERROR_623"
        else:
            require(False, "real suspended-process image preflight failed: " +
                    suspended.stdout + suspended.stderr)

    with tempfile.TemporaryDirectory(prefix="rmod1-negative-", dir=candidate.parent) as temporary:
        root = Path(temporary)
        bad_game = root / "wrong-game"
        bad_game.mkdir()
        (bad_game / "MRallye.exe").write_bytes(b"MZ-not-the-retail-build")
        wrong_build = run_launcher(launcher, bad_game)
        require(wrong_build.returncode != 0 and "exact retail SHA256/size required" in wrong_build.stderr,
                "wrong-size executable negative case did not fail closed")

        missing_game = root / "missing-game"
        missing_game.mkdir()
        missing = run_launcher(launcher, missing_game)
        require(missing.returncode != 0 and "retail executable is missing" in missing.stderr,
                "missing executable negative case did not fail closed")

        wrong_hash_game = root / "wrong-hash-game"
        wrong_hash_game.mkdir()
        (wrong_hash_game / "MRallye.exe").write_bytes(bytes(RETAIL_SIZE))
        wrong_hash = run_launcher(launcher, wrong_hash_game)
        require(wrong_hash.returncode != 0 and "exact retail SHA256/size required" in wrong_hash.stderr,
                "exact-size wrong-hash executable negative case did not fail closed")

        corrupted_mod = root / "corrupted-mod"
        corrupted_mod.mkdir()
        shutil.copyfile(launcher, corrupted_mod / launcher.name)
        runtime = candidate / "MRallyeRandomizerRuntime.dll"
        damaged = bytearray(runtime.read_bytes())
        damaged[len(damaged) // 2] ^= 0x01
        (corrupted_mod / runtime.name).write_bytes(damaged)
        shutil.copyfile(candidate / "MRallyeRandomizer.ini", corrupted_mod / "MRallyeRandomizer.ini")
        bad_dll = run_launcher(corrupted_mod / launcher.name, retail_exe.parent)
        require(bad_dll.returncode != 0 and "runtime core DLL SHA256 differs" in bad_dll.stderr,
                "altered-runtime negative case did not fail closed")

        for label, ini_bytes in (
            ("malformed", b"[General]\nConfigVersion=9\n[Randomizer]\nEnabled=1\n"),
            ("oversized", b"x" * 4097),
        ):
            safe_mod = root / ("safe-" + label)
            safe_mod.mkdir()
            shutil.copyfile(launcher, safe_mod / launcher.name)
            shutil.copyfile(runtime, safe_mod / runtime.name)
            (safe_mod / "MRallyeRandomizer.ini").write_bytes(ini_bytes)
            safe = run_launcher(safe_mod / launcher.name, retail_exe.parent)
            require(safe.returncode == 0 and "features=randomizer:off,opponents:off" in safe.stdout and
                    "effective_numeric_config=randomizer=0,quickrace=0:Stock,duplicates=1:WhenNeeded,opponents=0,max_ai=3,experimental_extended_ai=0,addons=0:StockOnly,logging=0" in safe.stdout,
                    label + " INI must select whole-file stock defaults")

        missing_config = root / "safe-missing-config"
        missing_config.mkdir()
        shutil.copyfile(launcher, missing_config / launcher.name)
        shutil.copyfile(runtime, missing_config / runtime.name)
        safe_missing = run_launcher(missing_config / launcher.name, retail_exe.parent)
        require(safe_missing.returncode == 0 and "features=randomizer:off,opponents:off" in safe_missing.stdout and
                "effective_numeric_config=randomizer=0,quickrace=0:Stock,duplicates=1:WhenNeeded,opponents=0,max_ai=3,experimental_extended_ai=0,addons=0:StockOnly,logging=0" in safe_missing.stdout,
                "missing INI must select stock defaults")

    return {"status": ("CANDIDATE_STATIC_AND_NEGATIVE_PATHS_PASS" if preflight_status.startswith("WINDOWS_PASS")
                        else "CANDIDATE_STATIC_PASS_SUSPENDED_PREFLIGHT_BLOCKED"),
            "candidate": str(candidate), "retail_sha256": RETAIL_SHA256,
            "operation_count": len(plan["operations"]),
            "suspended_preflight": preflight_status,
            "checks": ["package hashes", "plan boundaries",
                       f"{expected_operations}-operation checkpoint feature ownership/non-overlap",
                       "native RET 4 getter preimage unchanged and observer absent",
                       "v13 raw SplitScreen handoff is diagnostic-only",
            "safe public numeric INI and progressive count profiles with randomized and Stock-class extender modes",
                       "append-only CONFIG/START/ROSTER native logger harness",
                       "launcher exact-build positive",
                       "Windows suspended CreateProcess/VirtualQueryEx preflight attempted before native writes",
                       "plan regeneration from exact EXE and package DLL",
                       "missing executable rejected", "wrong-size executable rejected",
                       "exact-size wrong-hash executable rejected", "altered runtime DLL rejected",
                       "malformed INI selects stock", "oversized INI selects stock",
                       "missing INI selects stock"],
            "runtime_qualified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--retail-exe", type=Path, required=True)
    parser.add_argument("--allow-preflight-blocked", action="store_true",
                        help="finish package-only checks when this host returns CreateProcessW error 623; does not qualify the candidate")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_package(args.candidate, args.retail_exe,
                                        allow_preflight_blocked=args.allow_preflight_blocked),
                         indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        print("R-MOD1 candidate verification failed: " + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
