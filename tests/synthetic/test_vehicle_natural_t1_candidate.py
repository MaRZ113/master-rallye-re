from __future__ import annotations

import hashlib
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_vehicle_ai_candidate as ai
import build_vehicle_audio_candidate as audio
import build_vehicle_hardened_candidate as hardened
import build_vehicle_natural_t1_candidate as natural
import patch_vehicle_registry_id26 as registry
from test_vehicle_hardened_candidate import hardened_pristine_fixture


def natural_fixture_and_pins() -> tuple[bytes, dict[str, str]]:
    data = bytearray(hardened_pristine_fixture())
    pe = registry.parse_pe(data)
    for va, expected in (
        (natural.T1_REENTRY_VA, natural.T1_REENTRY_BYTES),
        (natural.T1_EXIT_HOOK_VA - 5, natural.T1_BOUND_BYTES),
        (natural.RESULTS_LOOKUP_CONTINUATION_VA, natural.RESULTS_LOOKUP_AND_PUSH_BYTES),
    ):
        offset = registry.va_to_file_offset(pe, va, len(expected))
        data[offset:offset + len(expected)] = expected
    source = bytes(data)
    source_sha = hashlib.sha256(source).hexdigest()
    g1, _ = registry.make_candidate(
        source, expected_sha256=source_sha,
        id26_profile=registry.ID26_MERCEDES_G1_STOCK_UNLOCK,
    )
    g1_sha = hashlib.sha256(g1).hexdigest()
    g2, _ = audio.make_candidate(
        source, 0, expected_source_sha256=source_sha,
        expected_g1_sha256=g1_sha,
    )
    g2_sha = hashlib.sha256(g2).hexdigest()
    neutral, _ = hardened.make_candidate(
        source, hardened.PROFILE_ORDINARY,
        expected_source_sha256=source_sha,
        expected_g1_sha256=g1_sha,
        expected_g2_sha256=g2_sha,
    )
    return source, {
        "source": source_sha,
        "g1": g1_sha,
        "g2": g2_sha,
        "neutral": hashlib.sha256(neutral).hexdigest(),
    }


class VehicleNaturalT1CandidateTests(unittest.TestCase):
    def test_source_pool_exact_membership_and_human_exclusions(self) -> None:
        cases = (
            ((), [0, 1, 2, 3, 4, 5, 6, 26]),
            ((0,), [1, 2, 3, 4, 5, 6, 26]),
            ((3,), [0, 1, 2, 4, 5, 6, 26]),
            ((26,), [0, 1, 2, 3, 4, 5, 6]),
            ((0, 26), [1, 2, 3, 4, 5, 6]),
            ((3, 5), [0, 1, 2, 4, 6, 26]),
        )
        for exclusions, expected in cases:
            with self.subTest(exclusions=exclusions):
                pool = natural.source_pool_after_exclusions(exclusions)
                self.assertEqual(pool, expected)
                self.assertNotIn(7, pool)

    def test_t2_and_t3_source_pools_are_unchanged(self) -> None:
        self.assertEqual(natural.T2_SOURCE_POOL, tuple(range(7, 14)))
        self.assertEqual(natural.T3_BASE_POOL, tuple(range(14, 21)))
        self.assertEqual(natural.T3_PROGRESS_POOL, (21, 22, 23, 24))

    def test_native_remove_after_selection_keeps_unique_ai_ids(self) -> None:
        pool = natural.source_pool_after_exclusions((0,))
        orders = (
            [26, 1, 2, 3, 4, 5, 6],
            [1, 26, 2, 3, 4, 5, 6],
            [1, 2, 26, 3, 4, 5, 6],
        )
        for order in orders:
            selected = natural.select_without_repeat(pool, order, 3)
            self.assertEqual(len(set(selected)), 3)
            self.assertIn(26, selected)
            self.assertNotIn(7, selected)

    def test_t1_hook_reenters_native_exclusion_body_and_restores_loop_index(self) -> None:
        stub = natural.natural_t1_exit_stub_bytes()
        self.assertEqual(stub[:5], bytes.fromhex("83FE1B740A"))
        self.assertEqual(stub[5:10], bytes.fromhex("BE1A000000"))
        self.assertEqual(stub[15:20], bytes.fromhex("BE07000000"))
        first_jump = struct.unpack_from("<i", stub, 11)[0] + natural.T1_POOL_STUB_VA + 15
        second_jump = struct.unpack_from("<i", stub, 21)[0] + natural.T1_POOL_STUB_VA + 25
        self.assertEqual(first_jump, natural.T1_REENTRY_VA)
        self.assertEqual(second_jump, natural.T1_COMMON_EXIT_VA)

    def test_id26_fixed_results_name_does_not_touch_driver_or_physical_identity(self) -> None:
        stub = natural.results_name_stub_bytes()
        self.assertIn(b"JEAN-PIERRE STRUGO\0", stub)
        self.assertEqual(stub[:8], bytes.fromhex("8B0CAE8B108B4908"))
        self.assertEqual(stub[8:11], bytes.fromhex("83F91A"))
        fixed_ptr = struct.unpack_from("<I", stub, 18)[0]
        self.assertEqual(fixed_ptr, natural.RESULTS_NAME_STUB_VA + stub.index(b"JEAN-PIERRE STRUGO\0"))
        fixed_target = struct.unpack_from("<i", stub, 23)[0] + natural.RESULTS_NAME_STUB_VA + 27
        self.assertEqual(fixed_target, natural.RESULTS_AFTER_LOOKUP_VA)
        # The non-ID26 branch uses the original CarID selector and group 0x39.
        self.assertEqual(stub[27:36], bytes.fromhex("8B0CAE8B4908516A39"))
        self.assertNotIn(bytes.fromhex("8B4904"), stub)  # no DriverID rewrite/read
        self.assertNotIn(bytes.fromhex("C744"), stub)    # no participant field store

    def test_candidate_composes_ordinary_base_and_only_h1_policy(self) -> None:
        source, pins = natural_fixture_and_pins()
        candidate, manifest = natural.make_candidate(
            source,
            expected_source_sha256=pins["source"],
            expected_g1_sha256=pins["g1"],
            expected_g2_sha256=pins["g2"],
            expected_neutral_base_sha256=pins["neutral"],
        )
        rebuilt, rebuilt_manifest = natural.make_candidate(
            source,
            expected_source_sha256=pins["source"],
            expected_g1_sha256=pins["g1"],
            expected_g2_sha256=pins["g2"],
            expected_neutral_base_sha256=pins["neutral"],
        )
        self.assertEqual(candidate, rebuilt)
        self.assertEqual(manifest, rebuilt_manifest)
        self.assertEqual(manifest["profile"], natural.PROFILE)
        self.assertEqual(manifest["natural_t1_id26_pool"]["source_ids"], [0, 1, 2, 3, 4, 5, 6, 26])
        self.assertFalse(manifest["forced_ai_proof"]["included"])
        self.assertFalse(manifest["randomizer"]["present"])
        self.assertFalse(manifest["participant_count_changed"])
        self.assertEqual(manifest["results_identity"]["display_name"], "JEAN-PIERRE STRUGO")
        self.assertEqual(manifest["results_identity"]["classification"], "REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER")
        self.assertEqual(manifest["results_identity"]["exact_ml320_pairing"], "unproven")
        self.assertFalse(manifest["results_identity"]["native_driver_id_selection_changed"])
        self.assertFalse(manifest["results_identity"]["native_driver_id_written"])
        self.assertTrue(manifest["hardening"]["null_stringlist_dump_guard"])
        self.assertEqual(manifest["base_manifest"]["stock_audio_profile_id"], 0)
        self.assertEqual(manifest["g2_base_sha256"], pins["g2"])

    def test_candidate_keeps_forced_publication_hook_and_h0_stub_absent(self) -> None:
        source, pins = natural_fixture_and_pins()
        candidate, manifest = natural.make_candidate(
            source,
            expected_source_sha256=pins["source"],
            expected_g1_sha256=pins["g1"],
            expected_g2_sha256=pins["g2"],
            expected_neutral_base_sha256=pins["neutral"],
        )
        pe = ai._parse_candidate_pe(candidate)
        hook = registry.va_to_file_offset(pe, ai.AI_PUBLICATION_HOOK_VA,
                                          len(ai.EXPECTED_PUBLICATION_BYTES))
        self.assertEqual(candidate[hook:hook + 5], ai.EXPECTED_PUBLICATION_BYTES)
        forced = registry.va_to_file_offset(pe, ai.AI_PROOF_STUB_VA, 64)
        self.assertEqual(candidate[forced:forced + 64], bytes(64))
        t1 = registry.va_to_file_offset(pe, natural.T1_EXIT_HOOK_VA, 5)
        self.assertEqual(candidate[t1:t1 + 5], ai._relative_jump(natural.T1_EXIT_HOOK_VA, natural.T1_POOL_STUB_VA))
        self.assertTrue(any(op["name"] == "natural_t1_pool_exit_hook" for op in manifest["operations"]))

    def test_unknown_source_and_pool_overlap_fail_closed(self) -> None:
        source, pins = natural_fixture_and_pins()
        with self.assertRaisesRegex(natural.CandidateError, "unsupported pristine retail SHA256"):
            natural.make_candidate(b"unknown")
        corrupted = bytearray(source)
        pe = registry.parse_pe(corrupted)
        offset = registry.va_to_file_offset(pe, natural.T1_EXIT_HOOK_VA, 5)
        corrupted[offset] ^= 0x01
        with self.assertRaisesRegex(natural.CandidateError, "native T1 source-pool exit"):
            natural.make_candidate(
                bytes(corrupted),
                expected_source_sha256=hashlib.sha256(corrupted).hexdigest(),
                expected_neutral_base_sha256=pins["neutral"],
                expected_g1_sha256=pins["g1"],
                expected_g2_sha256=pins["g2"],
            )


if __name__ == "__main__":
    unittest.main()
