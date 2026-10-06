from __future__ import annotations

import copy
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import build_vehicle_audio_candidate as audio
import patch_vehicle_registry_id26 as registry
from test_vehicle_registry_id26_patcher import retail_layout_fixture


def synthetic_pristine() -> bytes:
    data = bytearray(retail_layout_fixture())
    pe = registry.parse_pe(data)
    offset = registry.va_to_file_offset(pe, audio.ID26_AUDIO_LOOKUP_CALL_VA, 5)
    data[offset:offset + 5] = audio._call_rel32(
        audio.ID26_AUDIO_LOOKUP_CALL_VA, audio.RACE_CAR_ID_GETTER_VA
    )
    return bytes(data)


def synthetic_hashes(data: bytes) -> tuple[str, str]:
    base, _manifest = registry.make_candidate(
        data,
        expected_sha256=audio.sha256(data),
        id26_profile=registry.ID26_MERCEDES_G1_STOCK_UNLOCK,
    )
    return audio.sha256(data), audio.sha256(base)


class VehicleAudioCandidateTests(unittest.TestCase):
    def test_stock_audio_matrix_covers_ids_and_distinct_profile_groups(self) -> None:
        matrix_path = Path(__file__).resolve().parents[2] / "research" / "vehicles" / "audio" / "stock-audio-matrix.json"
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        rows = matrix["vehicles"]
        self.assertEqual([row["id"] for row in rows], list(range(26)))
        tuned = rows[:25]
        composites = {
            (row["sample_family"], row["sample_scalar_bits"],
             row["tuning_field_0x14_bits"], row["curve_group"])
            for row in tuned
        }
        self.assertEqual(len(composites), 25)
        self.assertTrue(all(row["profile"] is not None for row in tuned))
        self.assertIsNone(rows[25]["profile"])
        self.assertFalse(rows[25]["explicit_tuned_case"])
        self.assertEqual(rows[0]["name"], "Landcruiser")
        self.assertEqual(rows[15]["name"], "Simmbugghini")
        self.assertEqual(rows[19]["name"], "Mattserati")
        self.assertEqual((rows[4]["curve_group"], rows[18]["curve_group"]), ("B", "C"))

    def test_profile_selection_only_substitutes_physical_id26(self) -> None:
        for donor in (0, 19):
            for car_id in range(26):
                self.assertEqual(audio.resolve_audio_profile_id(car_id, donor), car_id)
            self.assertEqual(audio.resolve_audio_profile_id(26, donor), donor)
            self.assertEqual(audio.resolve_audio_profile_id(27, donor), 27)
            self.assertEqual(audio.resolve_audio_profile_id(255, donor), 255)

    def test_wrapper_forwards_slot_lookup_and_keeps_original_return_cleanup(self) -> None:
        wrapper_va = 0x0068E679
        for donor in (0, 19):
            body = audio.audio_wrapper_bytes(donor, wrapper_va)
            self.assertEqual(len(body), 22)
            self.assertEqual(body[:4], bytes.fromhex("ff742404"))
            self.assertEqual(body[4:9], audio._call_rel32(
                wrapper_va + 4, audio.RACE_CAR_ID_GETTER_VA
            ))
            self.assertEqual(body[9:14], bytes.fromhex("83f81a7505"))
            self.assertEqual(body[14:19], b"\xB8" + struct.pack("<I", donor))
            self.assertEqual(body[19:22], bytes.fromhex("c20400"))

    def test_candidates_are_deterministic_and_a_b_diff_only_at_donor_immediate(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash = synthetic_hashes(source)
        candidate_a, manifest_a = audio.make_candidate(
            source, 0, expected_source_sha256=source_hash, expected_g1_sha256=g1_hash
        )
        candidate_a_again, manifest_a_again = audio.make_candidate(
            source, 0, expected_source_sha256=source_hash, expected_g1_sha256=g1_hash
        )
        candidate_b, manifest_b = audio.make_candidate(
            source, 19, expected_source_sha256=source_hash, expected_g1_sha256=g1_hash
        )
        self.assertEqual(candidate_a, candidate_a_again)
        self.assertEqual(manifest_a, manifest_a_again)
        self.assertEqual(manifest_a["patched_sha256"], audio.sha256(candidate_a))
        self.assertEqual(manifest_b["patched_sha256"], audio.sha256(candidate_b))
        diff = [index for index, pair in enumerate(zip(candidate_a, candidate_b))
                if pair[0] != pair[1]]
        wrapper_va = int(manifest_a["audio_identity"]["wrapper_va"], 16)
        pe = registry.parse_pe(source)
        wrapper_offset = registry.va_to_file_offset(pe, wrapper_va, 22)
        self.assertEqual(diff, [wrapper_offset + 15])
        self.assertEqual(manifest_a["g1_base_sha256"], g1_hash)

    def test_g1_vehicle_and_unlock_identity_is_carried_without_audio_registry_edits(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash = synthetic_hashes(source)
        candidate, manifest = audio.make_candidate(
            source, 19, expected_source_sha256=source_hash, expected_g1_sha256=g1_hash
        )
        profile = manifest["structural_self_check"]["id26"]
        self.assertEqual(profile["id"], 26)
        self.assertEqual(profile["class"], 0)
        self.assertEqual(profile["class_local_index"], 7)
        self.assertEqual(profile["internal_name"], "Mercedes")
        self.assertEqual(profile["runtime_family"], "Mercedes")
        self.assertEqual(profile["model_family"], "Mercedes")
        self.assertEqual(profile["wheel_family"], "Mercedes")
        self.assertEqual(profile["physics_family"], "Vehicles/Mercedes")
        self.assertEqual(manifest["structural_self_check"]["unlock"]["id26"]["physical_record_id_preserved"], 26)
        self.assertEqual(manifest["audio_identity"]["physical_vehicle_id"], 26)
        self.assertFalse(manifest["audio_identity"]["physical_identity_changed"])
        self.assertFalse(manifest["audio_identity"]["class_model_wheel_physics_registry_changed"])
        new_ops = [op["name"] for op in manifest["operations"]
                   if op["name"].startswith("id26_audio_profile_")]
        self.assertEqual(set(new_ops), {
            "id26_audio_profile_lookup_call",
            "id26_audio_profile_selector_wrapper",
        })
        self.assertEqual(len(candidate), len(source))

    def test_candidate_verification_rejects_a_mismatched_source_hash(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash = synthetic_hashes(source)
        with self.assertRaisesRegex(audio.CandidateError, "unsupported pristine retail SHA256"):
            audio.make_candidate(source, 0, expected_source_sha256="0" * 64,
                                 expected_g1_sha256=g1_hash)
        with self.assertRaisesRegex(audio.CandidateError, "G.1 reproduction hash mismatch"):
            audio.make_candidate(source, 0, expected_source_sha256=source_hash,
                                 expected_g1_sha256="0" * 64)

    def test_candidate_refuses_unexpected_original_audio_call_bytes(self) -> None:
        source = bytearray(synthetic_pristine())
        pe = registry.parse_pe(source)
        offset = registry.va_to_file_offset(pe, audio.ID26_AUDIO_LOOKUP_CALL_VA, 5)
        source[offset] = 0x90
        source = bytes(source)
        source_hash, g1_hash = synthetic_hashes(source)
        with self.assertRaisesRegex(audio.CandidateError, "audio lookup call bytes changed"):
            audio.make_candidate(source, 0, expected_source_sha256=source_hash,
                                 expected_g1_sha256=g1_hash)

    def test_candidate_refuses_unsupported_audio_profile_donor(self) -> None:
        with self.assertRaisesRegex(audio.CandidateError, "unsupported donor CarID"):
            audio.audio_wrapper_bytes(18, 0x0068E679)
        with self.assertRaisesRegex(audio.CandidateError, "unsupported donor CarID"):
            audio.resolve_audio_profile_id(26, 18)

    def test_candidate_structural_verifier_rejects_a_mutated_hook(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash = synthetic_hashes(source)
        candidate, manifest = audio.make_candidate(
            source, 0, expected_source_sha256=source_hash, expected_g1_sha256=g1_hash
        )
        mutated = bytearray(candidate)
        pe = registry.parse_pe(source)
        hook_offset = registry.va_to_file_offset(pe, audio.ID26_AUDIO_LOOKUP_CALL_VA, 5)
        mutated[hook_offset] ^= 1
        mutated_manifest = copy.deepcopy(manifest)
        mutated_manifest["patched_sha256"] = audio.sha256(bytes(mutated))
        with self.assertRaisesRegex(audio.CandidateError, "candidate audio call does not target"):
            audio._verify_structure(bytes(mutated), mutated_manifest)


if __name__ == "__main__":
    unittest.main()
