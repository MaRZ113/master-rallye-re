from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import vehicle_unlock_runtime_package as package


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _component(root: Path, relative: str, kind: str) -> dict[str, object]:
    path = root / Path(relative)
    files = [path] if kind == "file" else sorted(item for item in path.rglob("*") if item.is_file())
    rows = [{
        "path": item.relative_to(root).as_posix(),
        "size": item.stat().st_size,
        "sha256": _sha(item.read_bytes()),
    } for item in files]
    rows.sort(key=lambda row: row["path"].casefold())
    return {
        "root": relative,
        "kind": kind,
        "file_count": len(rows),
        "total_bytes": sum(row["size"] for row in rows),
        "inventory_sha256": package._inventory_sha256(rows),
    }


class VehicleUnlockRuntimePackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.source = self.repo / "captured-root"
        self.source.mkdir(parents=True)
        self.payloads = {
            "Data.sma": b"known archive bytes",
            "DataAudio/engine.wav": b"known audio bytes",
            "DataGame/options.xml": b"<Options />",
            "DataGx/Vehicles/Mercedes/car.dx": b"known Mercedes DX",
            "DataVideo/title.avi": b"known video bytes",
        }
        for relative, data in self.payloads.items():
            path = self.source / Path(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.exe_bytes = b"E" * 3121214
        self.exe_sha = _sha(self.exe_bytes)
        self.exe = self.repo / "candidate.exe"
        self.exe.write_bytes(self.exe_bytes)
        (self.source / "MRallye.exe").write_bytes(self.exe_bytes)
        (self.source / "DataGame/PlayerState.xml").write_bytes(b"stale profile")
        (self.source / "DataGame/PlayerState.xml#").write_bytes(b"profile backup")
        self.scene_bytes = b"<Scene id='locked-slot-overlay'/>\n"
        self.scene_sha = _sha(self.scene_bytes)
        self.scene = self.repo / "VehicleSelect.xml"
        self.scene.write_bytes(self.scene_bytes)
        self.profile = self.repo / "runtime-root-profile.json"
        components = [
            _component(self.source, "Data.sma", "file"),
            _component(self.source, "DataAudio", "tree"),
            _component(self.source, "DataGame/options.xml", "file"),
            _component(self.source, "DataGx/Vehicles/Mercedes", "tree"),
            _component(self.source, "DataVideo", "tree"),
        ]
        self.profile.write_text(json.dumps({
            "schema_version": 1,
            "profile": "test-profile",
            "provenance": {
                "exe_sha256": self.exe_sha,
                "loose_vehicle_select_scene_present": False,
            },
            "components": components,
        }), encoding="utf-8")
        self.profile_sha = _sha(self.profile.read_bytes())
        self.output = self.repo / ".research-output" / "runtime"

    def _stage(self) -> dict[str, object]:
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            return package.stage_package(
                self.source, self.exe, self.scene, self.output, self.profile, repo_root=self.repo)

    def test_stage_and_verify_put_exact_scene_at_root_and_omit_profiles(self) -> None:
        result = self._stage()
        self.assertEqual(result["status"], "PASS_STAGED")
        self.assertEqual(result["executable_sha256"], self.exe_sha)
        self.assertEqual(result["vehicle_select_sha256"], self.scene_sha)
        self.assertEqual((self.output / "DataScene/FrontendScreens/VehicleSelect.xml").read_bytes(),
                         self.scene_bytes)
        self.assertEqual((self.output / "DataGx/Vehicles/Mercedes/car.dx").read_bytes(),
                         b"known Mercedes DX")
        self.assertFalse((self.output / "DataGame/PlayerState.xml").exists())
        self.assertFalse((self.output / "DataGame/PlayerState.xml#").exists())
        self.assertFalse((self.source / "DataScene/FrontendScreens/VehicleSelect.xml").exists())
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            checked = package.verify_package(self.output, self.profile, repo_root=self.repo)
        self.assertEqual(checked["status"], "PASS")
        self.assertIn("capture the game's Root header", checked["runtime_note"])

    def test_source_component_tampering_fails_closed_before_staging(self) -> None:
        (self.source / "DataGx/Vehicles/Mercedes/car.dx").write_bytes(b"changed")
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            with self.assertRaisesRegex(package.PackageError, "byte count mismatch|hash inventory mismatch"):
                package.stage_package(
                    self.source, self.exe, self.scene, self.output, self.profile, repo_root=self.repo)
        self.assertFalse(self.output.exists())

    def test_wrong_executable_or_scene_hash_is_rejected(self) -> None:
        wrong = self.repo / "wrong.exe"
        wrong.write_bytes(b"wrong")
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            with self.assertRaisesRegex(package.PackageError, "candidate EXE hash/size"):
                package.stage_package(
                    self.source, wrong, self.scene, self.output, self.profile, repo_root=self.repo)
            wrong_scene = self.repo / "wrong.xml"
            wrong_scene.write_bytes(b"wrong scene")
            with self.assertRaisesRegex(package.PackageError, "overlay hash"):
                package.stage_package(
                    self.source, self.exe, wrong_scene, self.output, self.profile, repo_root=self.repo)

    def test_existing_loose_scene_is_not_silently_shadowed(self) -> None:
        loose = self.source / "DataScene/FrontendScreens/VehicleSelect.xml"
        loose.parent.mkdir(parents=True)
        loose.write_bytes(b"unknown prior scene")
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            with self.assertRaisesRegex(package.PackageError, "already has a loose VehicleSelect.xml"):
                package.stage_package(
                    self.source, self.exe, self.scene, self.output, self.profile, repo_root=self.repo)

    def test_verify_detects_scene_tamper_and_extra_profile_file(self) -> None:
        self._stage()
        scene = self.output / "DataScene/FrontendScreens/VehicleSelect.xml"
        scene.write_bytes(b"tampered")
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            with self.assertRaisesRegex(package.PackageError,
                                        "file set differs|scene does not match|staged resource mismatch"):
                package.verify_package(self.output, self.profile, repo_root=self.repo)
        scene.write_bytes(self.scene_bytes)
        (self.output / "DataGame/PlayerState.xml").write_bytes(b"stale")
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            with self.assertRaisesRegex(package.PackageError, "file set differs|not fresh-profile clean"):
                package.verify_package(self.output, self.profile, repo_root=self.repo)

    def test_verify_allows_runtime_state_only_when_explicitly_requested(self) -> None:
        self._stage()
        state = self.output / "DataGame/PlayerState.xml"
        state.write_bytes(b"user progress; verifier must not read or rewrite")
        options_backup = self.output / "DataGame/options.xml#"
        options_backup.write_bytes(b"user options backup")
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            with self.assertRaisesRegex(package.PackageError, "file set differs"):
                package.verify_package(self.output, self.profile, repo_root=self.repo)
            checked = package.verify_package(
                self.output, self.profile, repo_root=self.repo, allow_runtime_state=True)
        self.assertEqual(checked["status"], "PASS")
        self.assertEqual(checked["fresh_player_state"], "existing PlayerState.xml preserved")
        self.assertEqual(state.read_bytes(), b"user progress; verifier must not read or rewrite")
        self.assertEqual(options_backup.read_bytes(), b"user options backup")

    def test_install_final_candidate_updates_only_exe_and_manifest(self) -> None:
        self._stage()
        state = self.output / "DataGame/PlayerState.xml"
        state.write_bytes(b"unlocked campaign save")
        state_before = state.read_bytes()
        options_backup = self.output / "DataGame/options.xml#"
        options_backup.write_bytes(b"options backup")
        options_before = options_backup.read_bytes()
        final_bytes = b"F" * 3121214
        final_sha = _sha(final_bytes)
        candidate = self.repo / ".research-output" / "MRallye_g1_final_racedetails.exe"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(final_bytes)

        with mock.patch.multiple(
            package,
            EXPECTED_EXE_SHA256=self.exe_sha,
            FINAL_RACE_DETAILS_EXE_SHA256=final_sha,
            EXPECTED_SCENE_SHA256=self.scene_sha,
            EXPECTED_PROFILE_SHA256=self.profile_sha,
        ):
            result = package.install_candidate(
                self.output, candidate, self.profile, repo_root=self.repo)
            self.assertEqual(result["status"], "PASS_INSTALLED")
            self.assertEqual(result["executable_sha256"], final_sha)
            self.assertEqual(result["candidate_profile"],
                             "mercedes-g1-final-racedetails-localization")
            self.assertEqual(result["player_state"], "preserved without reading or modification")
            self.assertEqual((self.output / "MRallye.exe").read_bytes(), final_bytes)
            self.assertEqual(state.read_bytes(), state_before)
            self.assertEqual(options_backup.read_bytes(), options_before)
            manifest = json.loads((self.output / package.PACKAGE_MANIFEST_NAME).read_text())
            self.assertEqual(manifest["candidate_executable"]["sha256"], final_sha)
            self.assertEqual(manifest["runtime_update"]["physical_car_id"], 26)
            verified = package.verify_package(
                self.output, self.profile, repo_root=self.repo, allow_runtime_state=True)
            self.assertEqual(verified["status"], "PASS")

    def test_install_rejects_wrong_final_candidate_without_mutating_package(self) -> None:
        self._stage()
        original_exe = (self.output / "MRallye.exe").read_bytes()
        original_manifest = (self.output / package.PACKAGE_MANIFEST_NAME).read_bytes()
        candidate = self.repo / ".research-output" / "wrong.exe"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(b"wrong candidate")
        with mock.patch.multiple(package, EXPECTED_EXE_SHA256=self.exe_sha,
                                 EXPECTED_SCENE_SHA256=self.scene_sha,
                                 EXPECTED_PROFILE_SHA256=self.profile_sha):
            with self.assertRaisesRegex(package.PackageError, "not the exact final G.1"):
                package.install_candidate(self.output, candidate, self.profile, repo_root=self.repo)
        self.assertEqual((self.output / "MRallye.exe").read_bytes(), original_exe)
        self.assertEqual((self.output / package.PACKAGE_MANIFEST_NAME).read_bytes(), original_manifest)

    def test_output_must_be_inside_research_output(self) -> None:
        with self.assertRaisesRegex(package.PackageError, "inside this checkout"):
            package.validate_output_root(self.repo / "runtime-package", self.repo)


if __name__ == "__main__":
    unittest.main()
