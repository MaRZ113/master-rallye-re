from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from unittest.mock import patch
from pathlib import Path

from master_rallye.authoring_paths import (
    AuthoringPathError,
    discover_embedded_authoring_paths,
    materialize_authoring_mirror,
)
from master_rallye.dx_revision_upgrade import upgrade_dx_131_to_135
from master_rallye.gxm import parse_gxm_prefix
from master_rallye.gxi import encode_gxi_as_observed_dxt, parse_gxi_bytes
from master_rallye.source_cooker import (
    ModelStrategy,
    SourceCookerError,
    TextureStrategy,
    VEHICLE_ROLES,
    build_runtime_package,
    build_texture_assets,
    build_validation_status,
    collect_native_cook_job,
    inventory_vehicle_source,
    plan_vehicle_source,
    prepare_native_gxm_job,
    _build_parser,
    select_model_strategy,
    validate_cache_only_package,
)


def _u32_string(raw: bytes) -> bytes:
    return struct.pack("<I", len(raw)) + raw


def _rev131_fixture() -> bytes:
    points = (
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        (2.0, 0.0, 0.0), (3.0, 0.0, 0.0), (2.0, 1.0, 0.0),
    )
    indices = (0, 1, 2, 0, 1, 2)
    data = bytearray(struct.pack("<4I", 0xD00D, 131, 1337, len(points)))
    for point in points:
        data += struct.pack("<3f", *point)
    for _ in points:
        data += struct.pack("<3f", 0.0, 0.0, 1.0)
    data += bytes((20, 30, 40, 255)) * len(points)
    data += struct.pack("<I", 1)
    for uv in ((0, 0), (1, 0), (0, 1), (0, 0), (1, 0), (0, 1)):
        data += struct.pack("<2f", *uv)
    data += struct.pack("<I6H", len(indices), *indices)
    data += struct.pack("<2I", 1, 2)
    for base, start, x_value in ((0, 0, 5), (3, 3, 9)):
        data += struct.pack("<5I", 2, base, 2, start, 3)
        data += bytes((0x11, 0x22, 0x33)) + struct.pack("<II", x_value, 2)
        data += _u32_string(b"body-tga") + _u32_string(b"Null") + struct.pack("<I", 0)
    data += struct.pack("<2I6I", 1, len(indices), 1, 0, 2, 4, 3, 5)
    return bytes(data)


def _rev131_two_triangles() -> bytes:
    points = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0))
    indices = (0, 1, 2, 1, 3, 2)
    data = bytearray(struct.pack("<4I", 0xD00D, 131, 0, 4))
    for point in points:
        data += struct.pack("<3f", *point)
    for _ in points:
        data += struct.pack("<3f", 0, 0, 1)
    data += b"\x01\x02\x03\xff" * 4
    data += struct.pack("<I", 0)
    data += struct.pack("<I6H", len(indices), *indices)
    data += struct.pack("<2I5I", 1, 1, 2, 0, 3, 0, len(indices))
    data += bytes((0x11, 0x22, 0x33)) + struct.pack("<II", 7, 1)
    data += _u32_string(b"body-tga") + struct.pack("<I", 0)
    data += struct.pack("<2I6I", 1, len(indices), 1, 0, 2, 3, 1, 2)
    return bytes(data)


def _gxm_fixture(reference: str = "D:/projects/MRallyeTNG/DataGx/Vehicles/Test/body-tga.gxi") -> bytes:
    ref = reference.encode("ascii")
    material = (
        struct.pack("<H", 4) + b"body" + b"\x01"
        + b"\x01\x00\x00" + struct.pack("<H", len(ref)) + ref
    )
    header = struct.pack("<8I", 0x00020702, 0, 0, 1, 3, 0, 1, 3)
    vector_a = struct.pack("<9f", 1, 0, 0, 0, 1, 0, 0, 0, 1)
    record = struct.pack("<10I", 0, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0, 1, 2, 0, 1, 2)
    vector_c = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    return header + material + vector_a + b"\xff" * 12 + record + vector_c + b"opaque-hierarchy"


def _gxi_fixture(rgba: bytes = b"\x11\x22\x33\xff") -> bytes:
    return struct.pack("<IHH", 0x00013039, 1, 1) + rgba


def _dxt_fixture(bgra: bytes = b"\x33\x22\x11\xff") -> bytes:
    return struct.pack("<5I", 0xFEED, 1, zlib.crc32(bgra) & 0xFFFFFFFF, 1, 1) + bgra


def _write_role_files(root: Path, *, gxm: bool = False, revision: int = 131) -> None:
    root.mkdir(parents=True, exist_ok=True)
    raw = _rev131_fixture()
    if revision == 135:
        raw = upgrade_dx_131_to_135(raw)
    elif revision != 131:
        raw = bytearray(raw)
        struct.pack_into("<I", raw, 4, revision)
        raw = bytes(raw)
    for role in VEHICLE_ROLES:
        (root / f"{role}.dx").write_bytes(raw)
        if gxm:
            (root / f"{role}.gxm").write_bytes(_gxm_fixture())


class SourceCookerInventoryTests(unittest.TestCase):
    def test_inventory_hashes_roles_and_keeps_nested_alternates_out_of_role_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Source With Spaces"
            _write_role_files(root, gxm=True)
            (root / "lpha").mkdir()
            (root / "lpha" / "car.dx").write_bytes(b"nested alternate")
            inventory = inventory_vehicle_source(root, "TestFamily")
            self.assertEqual(inventory.family, "TestFamily")
            self.assertEqual(inventory.role_files["car"][".dx"]["relative_path"], "car.dx")
            nested = next(item for item in inventory.files if item["relative_path"] == "lpha/car.dx")
            self.assertIsNone(nested["role"])
            self.assertEqual(inventory.role_files["complete"][".gxm"]["format_status"], "PASS_SUPPORTED_PREFIX")
            self.assertEqual(inventory.role_files["car"][".dx"]["format_details"]["revision"], 131)

    def test_known_forester_spelling_is_recognized_but_ambiguous_duplicate_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_role_files(root, gxm=False)
            for role in ("car", "wheel"):
                (root / f"{role}.gxm").write_bytes(_gxm_fixture())
            (root / "comlplete.gxm").write_bytes(_gxm_fixture())
            inventory = inventory_vehicle_source(root, "Forester")
            self.assertEqual(inventory.role_files["complete"][".gxm"]["filename_alias"], "comlplete.gxm")
            (root / "complete.gxm").write_bytes(_gxm_fixture())
            with self.assertRaises(SourceCookerError):
                inventory_vehicle_source(root, "Forester")

    def test_strategy_priority_and_fail_closed_revision_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_role_files(root, gxm=True, revision=131)
            inventory = inventory_vehicle_source(root, "Test")
            self.assertEqual(select_model_strategy(inventory).selected, ModelStrategy.RETAIL_NATIVE_GXM)
            for role in VEHICLE_ROLES:
                (root / f"{role}.gxm").unlink()
            inventory = inventory_vehicle_source(root, "Test")
            self.assertEqual(select_model_strategy(inventory).selected, ModelStrategy.OFFLINE_DX_131_TO_135)
            _write_role_files(root, revision=135)
            self.assertEqual(
                select_model_strategy(inventory_vehicle_source(root, "Test")).selected,
                ModelStrategy.PASS_THROUGH_135,
            )
            _write_role_files(root, revision=127)
            decision = select_model_strategy(inventory_vehicle_source(root, "Test"))
            self.assertEqual(decision.selected, ModelStrategy.UNSUPPORTED_REV127_CACHE_ONLY)
            self.assertEqual(decision.status, "UNSUPPORTED")

    def test_explicit_unsupported_strategy_requires_revision127_without_usable_gxm(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_role_files(root, gxm=True, revision=131)
            with self.assertRaisesRegex(SourceCookerError, "applies only when all three DX roles are revision 127"):
                select_model_strategy(inventory_vehicle_source(root, "Test"), "unsupported-rev127-cache-only")
            _write_role_files(root, gxm=True, revision=127)
            with self.assertRaisesRegex(SourceCookerError, "applies only when all three DX roles are revision 127"):
                select_model_strategy(inventory_vehicle_source(root, "Test"), "unsupported-rev127-cache-only")
            for role in VEHICLE_ROLES:
                (root / f"{role}.gxm").unlink()
            decision = select_model_strategy(
                inventory_vehicle_source(root, "Test"), "unsupported-rev127-cache-only",
            )
            self.assertEqual(decision.selected, ModelStrategy.UNSUPPORTED_REV127_CACHE_ONLY)

    def test_cli_exposes_only_supported_model_strategies(self):
        parser = _build_parser()
        subparsers = next(action for action in parser._actions if action.dest == "command")
        vehicle_parser = subparsers.choices["vehicle"]
        strategy_action = next(action for action in vehicle_parser._actions if action.dest == "model_strategy")
        self.assertEqual(strategy_action.choices, (
            "auto", "retail-native-gxm", "offline-131-to-135", "pass-through-135",
        ))
        self.assertIn("plan", subparsers.choices)
        self.assertIn("cook", subparsers.choices)
        self.assertIn("status", subparsers.choices)
        self.assertIn("resume", subparsers.choices)
        self.assertIn("cleanup", subparsers.choices)
        self.assertIn("recover", subparsers.choices)

    def test_native_job_schema_is_relocatable_and_generates_no_powershell_workflow(self):
        with tempfile.TemporaryDirectory(prefix="source cooker lifecycle ") as temporary:
            base = Path(temporary)
            source = base / "Forester source"
            source.mkdir()
            for role_name in ("car", "wheel"):
                (source / f"{role_name}.gxm").write_bytes(_gxm_fixture())
            (source / "comlplete.gxm").write_bytes(_gxm_fixture())
            (source / "body-tga.gxi").write_bytes(_gxi_fixture())
            template = base / "isolated retail harness"
            template.mkdir()
            (template / "MRallye.exe").write_bytes(b"synthetic exe")
            (template / "Data.sma").write_bytes(b"synthetic archive")
            job_root = base / "job output with spaces"

            def expected_hash(path):
                path = Path(path)
                if path.name.casefold() == "mrallye.exe":
                    return "a6a5f0590405e1a2051ef21f2be58197857e72f4a651506627c8966083a21d91"
                if path.name.casefold() == "data.sma":
                    return "03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f"
                return hashlib.sha256(path.read_bytes()).hexdigest()

            with patch("master_rallye.source_cooker.sha256_file", side_effect=expected_hash):
                result = prepare_native_gxm_job(source, "Forester", template, job_root)
            manifest = json.loads((job_root / "job-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], 2)
            self.assertEqual(manifest["state"], "PREFLIGHT_OK")
            self.assertEqual(manifest["job_kind"], "NATIVE_GXM_COOK")
            self.assertNotIn("status", manifest)
            self.assertEqual(manifest["paths"]["runtime"], "runtime")
            self.assertEqual(manifest["authoring_links"][0]["target_relative_to_job"], "authoring-root/root-00")
            self.assertEqual(result["authoring_discovery"]["status"], "PASS")
            self.assertFalse(list(job_root.glob("*.ps1")))
            self.assertFalse((job_root / "HUMAN_COOK_INSTRUCTIONS.txt").exists())
            self.assertTrue((job_root / "runtime" / "MRallye.exe").is_file())

    def test_validation_status_keeps_evidence_dimensions_independent(self):
        status = build_validation_status(
            FORMAT_VALIDATED="PASS",
            CACHE_ONLY_PORTABLE="CONFIRMED_BY_RUNTIME",
        )
        self.assertEqual(status["FORMAT_VALIDATED"], "PASS")
        self.assertEqual(status["CACHE_ONLY_PORTABLE"], "CONFIRMED_BY_RUNTIME")
        self.assertEqual(status["GAMEPLAY_RUNTIME_CONFIRMED"], "NOT_ASSESSED")
        self.assertEqual(len(status), 6)
        with self.assertRaisesRegex(SourceCookerError, "unknown validation status fields"):
            build_validation_status(ALL="PASS")

    def test_mixed_role_revisions_are_not_silently_combined(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_role_files(root, revision=131)
            (root / "wheel.dx").write_bytes(upgrade_dx_131_to_135(_rev131_fixture()))
            with self.assertRaisesRegex(SourceCookerError, "mixed or missing"):
                select_model_strategy(inventory_vehicle_source(root, "Test"))

    def test_plan_extracts_rev131_texture_references_through_canonical_adapter(self):
        with tempfile.TemporaryDirectory(prefix="source cooker plan ") as temporary:
            source = Path(temporary) / "vehicle source"
            _write_role_files(source, revision=131)
            (source / "body-tga.dxt").write_bytes(_dxt_fixture())
            plan = plan_vehicle_source(source, "Test", model_strategy="offline-131-to-135")
            self.assertEqual(plan["model"]["selected"], "offline-131-to-135")
            self.assertEqual(plan["texture_plan"]["count"], 1)
            self.assertEqual(plan["texture_plan"]["strategy_counts"], {"reuse-valid-dxt": 1})


class AuthoringPathTests(unittest.TestCase):
    def test_absolute_paths_group_and_mirror_only_referenced_gxi_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            root.mkdir()
            for role in VEHICLE_ROLES:
                (root / f"{role}.gxm").write_bytes(_gxm_fixture())
            (root / "body-tga.gxi").write_bytes(_gxi_fixture())
            gxm_paths = {role: root / f"{role}.gxm" for role in VEHICLE_ROLES}
            discovery = discover_embedded_authoring_paths(root, gxm_paths)
            self.assertEqual(discovery["status"], "PASS")
            self.assertEqual(len(discovery["historical_roots"]), 1)
            self.assertEqual(discovery["historical_roots"][0]["historical_root"], r"D:\projects\MRallyeTNG\DataGx\Vehicles\Test")
            mirror = Path(temporary) / "mirror"
            records = materialize_authoring_mirror(root, discovery, mirror)
            self.assertEqual(len(records), 1)
            target = Path(records[0]["target_path"])
            self.assertEqual(target.read_bytes(), (root / "body-tga.gxi").read_bytes())
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), records[0]["copied_sha256"])
            self.assertTrue((root / "body-tga.gxi").is_file())

    def test_ambiguous_nested_basename_is_blocked_when_no_top_level_source_exists(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            root.mkdir()
            for role in VEHICLE_ROLES:
                (root / f"{role}.gxm").write_bytes(_gxm_fixture())
            (root / "one").mkdir()
            (root / "two").mkdir()
            (root / "one" / "body-tga.gxi").write_bytes(_gxi_fixture(b"\x01\x02\x03\xff"))
            (root / "two" / "body-tga.gxi").write_bytes(_gxi_fixture(b"\x04\x05\x06\xff"))
            result = discover_embedded_authoring_paths(root, {r: root / f"{r}.gxm" for r in VEHICLE_ROLES})
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("ambiguous_source_GXI_basename", result["unresolved"][0]["reason"])


class TextureAndPackageTests(unittest.TestCase):
    def test_auto_texture_policy_reuses_dxt_then_encodes_missing_dxt_from_gxi(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "body-tga.dxt").write_bytes(_dxt_fixture())
            gxi = _gxi_fixture()
            (root / "normal-tga.gxi").write_bytes(gxi)
            textures = build_texture_assets(root, ["body-tga", "normal-tga"], "auto")
            by_name = {item.name: item for item in textures}
            self.assertEqual(by_name["body-tga"].strategy, TextureStrategy.REUSE_VALID_DXT.value)
            self.assertEqual(by_name["normal-tga"].strategy, TextureStrategy.OFFLINE_GXI_TO_DXT.value)
            self.assertEqual(by_name["normal-tga"].data, encode_gxi_as_observed_dxt(parse_gxi_bytes(gxi)))
            self.assertEqual(by_name["normal-tga"].byte_identical_to_historical_dxt, None)

    def test_malformed_existing_dxt_does_not_silently_fall_back_to_gxi(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "body-tga.dxt").write_bytes(b"bad")
            (root / "body-tga.gxi").write_bytes(_gxi_fixture())
            with self.assertRaisesRegex(SourceCookerError, "malformed"):
                build_texture_assets(root, ["body-tga"], "auto")

    def test_rev131_package_uses_r_cooker2_adapter_and_excludes_authoring_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source with spaces"
            _write_role_files(root)
            (root / "body-tga.dxt").write_bytes(_dxt_fixture())
            output = Path(temporary) / "cooked"
            inventory = inventory_vehicle_source(root, "Test")
            result = build_runtime_package(
                {role: root / f"{role}.dx" for role in VEHICLE_ROLES},
                root,
                output,
                family="Test",
                source_inventory=inventory,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["manifest"]["model_strategy"], ModelStrategy.OFFLINE_DX_131_TO_135.value)
            self.assertEqual(result["manifest"]["texture_outputs"][0]["strategy"], TextureStrategy.REUSE_VALID_DXT.value)
            self.assertEqual(result["manifest"]["source_files"]["car"]["relative_path"], "car.dx")
            self.assertEqual(result["manifest"]["source_files"]["car"]["kind"], "dx")
            self.assertEqual(set(path.name for path in output.iterdir()), {
                "complete.dx", "car.dx", "wheel.dx", "body-tga.dxt",
                "package-manifest.json", "validation-report.json",
            })
            self.assertEqual(validate_cache_only_package(output)["status"], "PASS")
            for role in VEHICLE_ROLES:
                data = (output / f"{role}.dx").read_bytes()
                self.assertEqual(struct.unpack_from("<I", data, 4)[0], 135)
                self.assertEqual(result["manifest"]["model_outputs"][role]["validation"]["adapter"], "R-COOKER2")

    def test_valid_existing_rev135_package_is_copied_without_rewrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            upgraded = upgrade_dx_131_to_135(_rev131_fixture())
            for role in VEHICLE_ROLES:
                (root / f"{role}.dx").write_bytes(upgraded)
            (root / "body-tga.dxt").write_bytes(_dxt_fixture())
            output = root / "package"
            result = build_runtime_package(
                {role: root / f"{role}.dx" for role in VEHICLE_ROLES},
                root,
                output,
                family="Test",
            )
            self.assertEqual(result["manifest"]["model_strategy"], ModelStrategy.PASS_THROUGH_135.value)
            self.assertEqual((output / "car.dx").read_bytes(), upgraded)

    def test_collect_native_cook_job_preserves_source_gxm_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            job = root / "job"
            asset_dir = job / "runtime" / "DataGx" / "Vehicles" / "Forester"
            asset_dir.mkdir(parents=True)
            upgraded = upgrade_dx_131_to_135(_rev131_fixture())
            for role in VEHICLE_ROLES:
                (asset_dir / f"{role}.dx").write_bytes(upgraded)
            (asset_dir / "body-tga.dxt").write_bytes(_dxt_fixture())
            source_gxm = {
                role: {"relative_path": f"{role}.gxm", "sha256": f"{role}-hash", "size": 100}
                for role in VEHICLE_ROLES
            }
            manifest = {
                "phase": "R-COOKER3",
                "status": "PREPARED_FOR_HUMAN_NATIVE_COOK",
                "job_id": "fixture-job",
                "runtime_root": "runtime",
                "runtime_family": "Forester",
                "source_family": "Forester",
                "source_manifest": "source-manifest.json",
                "retail_build_exe_sha256": "retail-hash",
                "runtime_harness_exe_sha256": "harness-hash",
                "gxm_sources": source_gxm,
                "validation_status": {},
            }
            (job / "job-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            output = root / "portable-package"
            result = collect_native_cook_job(job, output)
            self.assertEqual(result["status"], "PASS")
            package_manifest = json.loads((output / "package-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(package_manifest["source_provenance"]["native_cook_job_id"], "fixture-job")
            self.assertEqual(package_manifest["source_provenance"]["source_gxm"]["complete"]["sha256"], "complete-hash")
            updated_job = json.loads((job / "job-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(updated_job["job_kind"], "NATIVE_GXM_COOK")
            self.assertEqual(updated_job["state"], "PACKAGED")
            self.assertNotIn("status", updated_job)


if __name__ == "__main__":
    unittest.main()
