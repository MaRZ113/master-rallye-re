"""Optional validation against owner-supplied local retail inputs.

Run with: python -m unittest discover -s tests/integration -v
"""
import contextlib
import io
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import grid8_audit as grid_audit
import r_grid8_candidate as grid_candidate
import research_build_profiles as profiles


class MercExecutableIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = profiles.ROOT / "inputs" / "MRallye_merc.exe"
        if not cls.image.is_file():
            raise unittest.SkipTest("owner-supplied inputs/MRallye_merc.exe is unavailable")

    def test_verify_build_cli_does_not_require_audit_only_flag(self):
        stdout = io.StringIO()
        with patch.object(sys, "argv", ["research_build_profiles.py", "verify-build", str(self.image)]), \
                contextlib.redirect_stdout(stdout):
            profiles.main()
        self.assertIn("Compatibility family: retail-broker-v1", stdout.getvalue())
        self.assertIn("Local profile: committed exact profile", stdout.getvalue())

    def test_audit_only_cli_reports_independent_registry_detection(self):
        stdout = io.StringIO()
        with patch.object(sys, "argv", ["research_build_profiles.py", "audit-build", str(self.image), "--audit-only"]), \
                contextlib.redirect_stdout(stdout):
            profiles.main()
        self.assertIn("Vehicle registry: merc-id26", stdout.getvalue())

    def test_available_merc_v1_passes_family_and_registry_audits(self):
        report = profiles.audit_build(self.image.read_bytes())
        self.assertTrue(report["anchor_compatible"])
        self.assertEqual(report["compatibility_family"], "retail-broker-v1")
        self.assertEqual(report["registry_profile"], "merc-id26")
        self.assertTrue(report["capabilities"]["broker_capture_active_race"])
        self.assertFalse(report["capabilities"]["post_results_native_dump_safe"])

    def test_cosmetic_unknown_sha_audits_and_local_profile_reuses(self):
        data = bytearray(self.image.read_bytes())
        data[-1] ^= 1
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / "build-profiles"
            first = profiles.resolve_build(bytes(data), cache_root=cache)
            self.assertEqual(first["profile_origin"], "locally_audited")
            self.assertIsNone(first["exact_profile_id"])
            self.assertEqual(first["compatibility_family"], "retail-broker-v1")
            self.assertEqual(first["vehicle_registry_profile"], "merc-id26")
            self.assertTrue(Path(first["local_profile_cache"]).is_file())
            second = profiles.resolve_build(bytes(data), cache_root=cache)
            self.assertTrue(second["cache_reused"])
            self.assertEqual(first["audit_fingerprint"], second["audit_fingerprint"])

    def test_cache_is_bound_to_sha_and_changed_bytes_reaudit(self):
        data = bytearray(self.image.read_bytes())
        data[-1] ^= 1
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / "build-profiles"
            first = profiles.resolve_build(bytes(data), cache_root=cache)
            changed = bytearray(data)
            changed[-2] ^= 1
            audit = profiles.audit_build(bytes(changed))
            self.assertIsNone(profiles._load_valid_cache(Path(first["local_profile_cache"]), audit))
            next_profile = profiles.resolve_build(bytes(changed), cache_root=cache)
            self.assertNotEqual(first["sha256"], next_profile["sha256"])
            self.assertFalse(next_profile["cache_reused"])

    def test_wrong_pe_machine_is_rejected(self):
        data = bytearray(self.image.read_bytes())
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        struct.pack_into("<H", data, pe + 4, 0x8664)
        with self.assertRaises(ValueError):
            profiles.audit_build(bytes(data))

    def test_unknown_registry_build_can_check_generic_broker_without_vehicle_claims(self):
        data = bytearray(self.image.read_bytes())
        data[0x81E20] ^= 1  # Break registry-map evidence outside Broker anchors.
        build = profiles.resolve_build(bytes(data), write_local_profile=False)
        self.assertEqual(build["compatibility_family"], "retail-broker-v1")
        self.assertEqual(build["vehicle_registry_profile"], "unknown")
        snap = dict(kind="master-rallye-broker-dump-snapshot", schema_version=1,
                    source=dict(image_sha256=build["sha256"], image_size=build["size"],
                                exe_sha256=build["sha256"], exe_size=build["size"],
                                build_profile=build["profile_id"],
                                profile_origin="locally_audited",
                                compatibility_family=build["compatibility_family"],
                                audit_version=build["audit_version"],
                                audit_fingerprint=build["audit_fingerprint"],
                                vehicle_registry_profile="unknown"),
                    entries=[dict(path="Race/NumCars", value=1),
                             dict(path="Race/Car0/CarID", value=27),
                             dict(path="Race/Car0/PlayerType", value=1)])
        result = profiles.check_broker_capture(snap, build)
        self.assertEqual(result["status"], "BROKER_STRUCTURE_MATCH_ONLY")
        self.assertEqual(result["participants"][0]["CarID"], 27)
        self.assertEqual(result["vehicle_semantics"], "NOT_CHECKED")
        with self.assertRaisesRegex(ValueError, "UNKNOWN_REGISTRY_PROFILE"):
            profiles.check_vehicle(snap, build, 0)


class RetailExecutableCorpusIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_path = ROOT / "corpora" / "retail" / "MRallye.exe"
        if not cls.source_path.is_file():
            raise unittest.SkipTest("owner-supplied corpora/retail/MRallye.exe is unavailable")

    def test_exact_candidate_inverse_and_reproduction(self):
        output, _manifest = grid_candidate.build(self.source_path.read_bytes())
        result = grid_candidate.verify(output)
        self.assertEqual(result["output_sha256"], grid_candidate.EXPECTED_CANDIDATE_SHA256)
        self.assertTrue(result["inverse_verified"])
        self.assertTrue(result["byte_equal_reproduction"])


class RetailCourseCorpusIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = grid_audit.DEFAULT_CORPUS
        if not cls.corpus.is_dir():
            raise unittest.SkipTest("owner-supplied corpora/retail/Data.sma_unpacked is unavailable")

    def test_canonical_map_has_all_36_resources_and_39_scene_ids(self):
        transforms, table, rows = grid_audit.derive(self.corpus)
        self.assertEqual(len(rows), 36)
        self.assertEqual(table["scene_registration_count"], 39)
        self.assertEqual(transforms["unique_registered_scene_ids"], list(range(39)))
        self.assertEqual(sum(len(course["grid"]["transforms"])
                             for course in transforms["courses"]), 288)
        self.assertTrue(all(course["quick_race_finishing_type"] == 0
                            for course in transforms["courses"]))
        self.assertTrue(all(course["grid"]["clearance"] == "UNKNOWN_NOT_PHYSICALLY_TESTED"
                            for course in transforms["courses"]))
        self.assertTrue(all(row["runtime_status"] == "NOT_TESTED" for row in rows))
