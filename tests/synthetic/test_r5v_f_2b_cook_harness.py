from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import prepare_r5v_f_2b_cook_harness as harness


def make_source_tree(root: Path) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    for name in ("car.gxm", "complete.gxm", "wheel.gxm"):
        (root / name).write_bytes(name.encode("ascii"))
    for ext, count in (("gxi", 25), ("dxt", 25), ("txt", 3), ("dx", 3)):
        for index in range(count):
            name = f"asset{index:02d}.{ext}"
            (root / name).write_bytes(f"{name}\n".encode("ascii"))
    return {name: harness.sha256_file(root / name)
            for name in ("car.gxm", "complete.gxm", "wheel.gxm")}


class R5vF2bCookHarnessTests(unittest.TestCase):
    def test_wrong_retail_hashes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exe = root / "MRallye.exe"
            sma = root / "Data.sma"
            exe.write_bytes(b"retail exe test sentinel")
            sma.write_bytes(b"retail archive test sentinel")
            with self.assertRaisesRegex(harness.PreparationError, "MRallye.exe SHA-256 mismatch"):
                harness.verify_retail_inputs(exe, sma)

    def test_wrong_gxm_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_source_tree(root)
            with self.assertRaisesRegex(harness.PreparationError, "car.gxm SHA-256 mismatch"):
                harness.inventory_source_tree(root)

    def test_missing_source_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = make_source_tree(root)
            (root / "asset24.dxt").unlink()
            with self.assertRaisesRegex(harness.PreparationError, "unexpected source file inventory"):
                harness.inventory_source_tree(root, expected_gxm_hashes=expected)

    def test_adjacent_lpha_assets_keep_their_separate_gxm_family(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            variant = Path(temporary) / "lpha"
            variant.mkdir()
            (variant / "car.gxm").write_bytes(
                b"D:/Projects/MRallyeTNG/DataGx/Vehicles/MercedesAlpha/body.gxi"
            )
            inventory = harness.inventory_adjacent_lpha_variant(Path(temporary))
            self.assertIsNotNone(inventory)
            self.assertEqual(inventory["gxm_resource_roots"], ["MercedesAlpha"])
            self.assertIn("EXCLUDED", inventory["status"])

    def test_unknown_existing_authoring_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(harness.PreparationError, "without an R5V-F.2b ownership marker"):
            harness.authorize_authoring_path(
                link_exists=True,
                marker=None,
                link_type="Junction",
                resolved_target=r"D:\unknown",
                expected_link_path=r"D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes",
                expected_target=r"D:\Game\Master Rallye\research-output\r5v_f_2b\authoring-root\Mercedes",
            )

    def test_unexpected_junction_target_is_rejected_for_removal(self) -> None:
        link_path = r"D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes"
        target = r"D:\Game\Master Rallye\research-output\r5v_f_2b\authoring-root\Mercedes"
        marker = {"phase": "R5V-F.2b", "state": "created", "link_path": link_path, "target": target}
        with self.assertRaisesRegex(harness.PreparationError, "actual target mismatch"):
            harness.authorize_junction_removal(
                marker=marker,
                link_type="Junction",
                resolved_target=r"D:\user-data\Mercedes",
                expected_link_path=link_path,
                expected_target=target,
            )

    def test_creating_marker_recovers_only_for_the_exact_junction(self) -> None:
        link_path = r"D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes"
        target = r"D:\Game\Master Rallye\research-output\r5v_f_2b\authoring-root\Mercedes"
        marker = {"phase": "R5V-F.2b", "state": "creating", "link_path": link_path, "target": target}
        state = harness.authorize_authoring_path(
            link_exists=True,
            marker=marker,
            link_type="Junction",
            resolved_target=target,
            expected_link_path=link_path,
            expected_target=target,
        )
        self.assertEqual(state, "recover")
        with self.assertRaisesRegex(harness.PreparationError, "unexpected target"):
            harness.authorize_authoring_path(
                link_exists=True,
                marker=marker,
                link_type="Junction",
                resolved_target=r"D:\other\Mercedes",
                expected_link_path=link_path,
                expected_target=target,
            )

    def test_staging_preserves_source_and_omits_legacy_dx(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "Copy of Mercedes"
            expected_gxm = make_source_tree(source)
            manifest = harness.inventory_source_tree(source, expected_gxm_hashes=expected_gxm)
            before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in source.iterdir()}
            authoring = base / "authoring-root" / "Mercedes"
            runtime = base / "runtime" / "DataGx" / "Vehicles" / "Mercedes"
            authoring.mkdir(parents=True)
            runtime.mkdir(parents=True)

            staged = harness.stage_source_resources(
                source, authoring, runtime, manifest, expected_gxm_hashes=expected_gxm
            )

            self.assertEqual(len(staged["authoring_gxi"]), 25)
            self.assertEqual(len(staged["runtime_gxm_dxt"]), 28)
            self.assertEqual(len(list(authoring.glob("*.gxi"))), 25)
            self.assertEqual(len(list(runtime.glob("*.gxm"))), 3)
            self.assertEqual(len(list(runtime.glob("*.dxt"))), 25)
            self.assertEqual(list(runtime.glob("*.dx")), [])
            after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in source.iterdir()}
            self.assertEqual(after, before)

    def test_f1_cleanup_profile_definition_remains_the_same(self) -> None:
        profile = harness.patcher.ID26_PROFILES["donor-cleanup"]
        self.assertIs(profile, harness.patcher.ID26_DONOR_CLEANUP)
        self.assertEqual(profile.profile_id, "donor-cleanup-landcruiser-red-canary")
        self.assertEqual(profile.internal_name, "Landcruiser")
        self.assertEqual(profile.runtime_family, "Landcruiser")
        self.assertEqual(harness.patcher.NEW_RECORD_COUNT, 27)

    def test_junction_helpers_are_exact_path_and_nonrecursive(self) -> None:
        scripts = Path(harness.TOOLS_DIR) / "r5v_f_2b"
        check = (scripts / "CHECK_AUTHORING_PATH.ps1").read_text(encoding="utf-8")
        setup = (scripts / "SETUP_MERCEDES_JUNCTION.ps1").read_text(encoding="utf-8")
        removal = (scripts / "REMOVE_MERCEDES_JUNCTION.ps1").read_text(encoding="utf-8")
        for script in (check, setup, removal):
            self.assertIn(r"D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes", script)
            self.assertIn("R5V-F.2b", script)
            self.assertIn("$targets = @($Item.Target)", script)
            self.assertNotRegex(script, r"Resolve-Path\s+-LiteralPath\s+\$linkPath")
        self.assertIn("$marker.state -eq 'creating'", setup)
        self.assertIn("$marker.state = 'created'", setup)
        self.assertIn("$Item.LinkType -ne 'Junction'", removal)
        self.assertIn("[IO.Directory]::Delete($linkPath, $false)", removal)
        self.assertNotRegex(removal, r"Remove-Item\s+-Recurse")


if __name__ == "__main__":
    unittest.main()
