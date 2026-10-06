from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import vehicle_ai_runtime_package as package
import vehicle_unlock_runtime_package as unlock


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VehicleAIRuntimePackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scene_bytes = b"synthetic pinned scene"
        self.exe_bytes = b"synthetic candidate"
        self.asset_bytes = b"mercedes runtime bytes"
        self.base_bytes = b"synthetic data archive"
        self.candidate = {
            "path": "MRallye.exe",
            "sha256": _sha(self.exe_bytes),
            "size": len(self.exe_bytes),
            "patch_manifest_sha256": "f" * 64,
            "mode": package.H_MODE,
            "g2_audio_profile_id": 0,
            "source_sha256": "1" * 64,
            "g1_base_sha256": "2" * 64,
            "g2_base_sha256": "3" * 64,
        }
        component_specs = [
            {
                "root": "Data.sma",
                "kind": "file",
                "file_count": 1,
                "total_bytes": len(self.base_bytes),
                "inventory_sha256": "",
            },
            {
                "root": package.MERCEDES_ASSET_ROOT,
                "kind": "tree",
                "file_count": 1,
                "total_bytes": len(self.asset_bytes),
                "inventory_sha256": "",
            },
        ]
        base_row = {"path": "Data.sma", "size": len(self.base_bytes), "sha256": _sha(self.base_bytes)}
        asset_row = {
            "path": f"{package.MERCEDES_ASSET_ROOT}/body.dx",
            "size": len(self.asset_bytes),
            "sha256": _sha(self.asset_bytes),
        }
        component_specs[0]["inventory_sha256"] = unlock._inventory_sha256([base_row])
        component_specs[1]["inventory_sha256"] = unlock._inventory_sha256([asset_row])
        self.profile = {"profile": "synthetic-g1", "components": component_specs}
        self.profile_sha = "a" * 64
        scene_pin = patch.object(unlock, "EXPECTED_SCENE_SHA256", _sha(self.scene_bytes))
        scene_pin.start()
        self.addCleanup(scene_pin.stop)
        self._write_package_files()

    def _write_package_files(self) -> None:
        (self.root / "Data.sma").write_bytes(self.base_bytes)
        asset_dir = self.root / package.MERCEDES_ASSET_ROOT
        asset_dir.mkdir(parents=True, exist_ok=True)
        (asset_dir / "body.dx").write_bytes(self.asset_bytes)
        scene_path = self.root / unlock.SCENE_RELATIVE.as_posix()
        scene_path.parent.mkdir(parents=True, exist_ok=True)
        scene_path.write_bytes(self.scene_bytes)
        (self.root / "MRallye.exe").write_bytes(self.exe_bytes)

    def _verify(self) -> dict:
        resource_rows, components = package._resource_rows(self.root, self.profile)
        manifest = package._runtime_manifest(
            candidate=self.candidate,
            profile=self.profile,
            profile_sha256=self.profile_sha,
            resource_rows=resource_rows,
            components=components,
        )
        (self.root / package.PACKAGE_MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        with patch.multiple(
            package,
            EXPECTED_H_SIZE=len(self.exe_bytes),
            EXPECTED_H_MANIFEST_SHA256="f" * 64,
        ), patch.object(unlock, "EXPECTED_SCENE_SHA256", _sha(self.scene_bytes)):
            return package._verify_tree(
                self.root,
                candidate=self.candidate,
                profile=self.profile,
                profile_sha256=self.profile_sha,
                enforce_output_root=False,
            )

    def test_exact_synthetic_package_passes_all_component_checks(self) -> None:
        result = self._verify()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["exe"], "PASS")
        self.assertEqual(result["vehicle_select_xml"], "PASS")
        self.assertEqual(result["mercedes_assets"], "PASS")
        self.assertEqual(result["mode"], "PASS")

    def test_missing_or_omitted_vehicle_select_overlay_is_rejected(self) -> None:
        (self.root / unlock.SCENE_RELATIVE.as_posix()).unlink()
        with self.assertRaisesRegex(package.RuntimePackageError, "VehicleSelect.xml is missing"):
            self._verify()

    def test_wrong_vehicle_select_hash_is_rejected(self) -> None:
        (self.root / unlock.SCENE_RELATIVE.as_posix()).write_bytes(b"wrong overlay")
        with self.assertRaisesRegex(package.RuntimePackageError, "pinned G.1 overlay"):
            self._verify()

    def test_wrong_executable_hash_is_rejected(self) -> None:
        (self.root / "MRallye.exe").write_bytes(b"wrong executable")
        with self.assertRaisesRegex(package.RuntimePackageError, "executable does not match"):
            self._verify()

    def test_missing_mercedes_asset_root_is_rejected(self) -> None:
        shutil_path = self.root / package.MERCEDES_ASSET_ROOT / "body.dx"
        shutil_path.unlink()
        shutil_path.parent.rmdir()
        with self.assertRaisesRegex(package.RuntimePackageError, "required resource component is missing"):
            self._verify()

    def test_manifest_cannot_name_a_different_candidate(self) -> None:
        self._verify()
        manifest_path = self.root / package.PACKAGE_MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["candidate"]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with patch.multiple(
            package,
            EXPECTED_H_SIZE=len(self.exe_bytes),
            EXPECTED_H_MANIFEST_SHA256="f" * 64,
        ), patch.object(unlock, "EXPECTED_SCENE_SHA256", _sha(self.scene_bytes)):
            with self.assertRaisesRegex(package.RuntimePackageError, "manifest differs"):
                package._verify_tree(
                    self.root, candidate=self.candidate, profile=self.profile,
                    profile_sha256=self.profile_sha, enforce_output_root=False,
                )

    def test_stage_builds_self_contained_package_and_drops_profile_state(self) -> None:
        research_output = package.REPO_ROOT / ".research-output"
        research_output.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=research_output) as temp_name:
            work = Path(temp_name)
            source = work / "g1-source"
            source.mkdir()
            candidate_path = work / "candidate.exe"
            candidate_path.write_bytes(self.exe_bytes)
            manifest_path = work / "patch-manifest.json"
            manifest_path.write_text("{}\n", encoding="utf-8")
            retail_path = work / "retail.exe"
            retail_path.write_bytes(b"retail")
            (source / "Data.sma").write_bytes(self.base_bytes)
            asset_dir = source / package.MERCEDES_ASSET_ROOT
            asset_dir.mkdir(parents=True)
            (asset_dir / "body.dx").write_bytes(self.asset_bytes)
            scene_path = source / unlock.SCENE_RELATIVE.as_posix()
            scene_path.parent.mkdir(parents=True)
            scene_path.write_bytes(self.scene_bytes)
            (source / "MRallye.exe").write_bytes(b"prior-g1")
            player_state = source / "DataGame" / "PlayerState.xml"
            player_state.parent.mkdir()
            player_state.write_text("should not be copied", encoding="utf-8")
            (source / unlock.PACKAGE_MANIFEST_NAME).write_text(json.dumps({
                "candidate_executable": {"sha256": package.EXPECTED_G1_RUNTIME_EXE_SHA256},
                "payload_files": [],
            }), encoding="utf-8")
            output = work / "runtime-package"
            pins = patch.multiple(
                package,
                EXPECTED_H_SIZE=len(self.exe_bytes),
                EXPECTED_H_MANIFEST_SHA256="f" * 64,
            )
            scene_pin = patch.object(unlock, "EXPECTED_SCENE_SHA256", _sha(self.scene_bytes))
            validated_candidate = patch.object(package, "_validated_candidate", return_value=self.candidate)
            loaded_profile = patch.object(unlock, "_load_profile", return_value=(self.profile, self.profile_sha))
            verified_g1 = patch.object(
                unlock, "verify_package",
                return_value={"executable_sha256": package.EXPECTED_G1_RUNTIME_EXE_SHA256},
            )
            with pins, scene_pin, validated_candidate, loaded_profile, verified_g1:
                result = package._stage(
                    source, candidate_path, manifest_path, retail_path, output,
                )
            self.assertEqual(result["status"], "PASS_STAGED")
            self.assertEqual((output / "MRallye.exe").read_bytes(), self.exe_bytes)
            self.assertEqual(
                _sha((output / unlock.SCENE_RELATIVE.as_posix()).read_bytes()),
                _sha(self.scene_bytes),
            )
            self.assertFalse((output / "DataGame" / "PlayerState.xml").exists())
            self.assertTrue((work / package.VERIFY_FILE_NAME).is_file())


if __name__ == "__main__":
    unittest.main()
