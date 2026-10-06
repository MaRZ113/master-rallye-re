from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import build_vehicle_ai_candidate as ai
import build_vehicle_audio_candidate as audio
import patch_vehicle_registry_id26 as registry
from test_vehicle_registry_id26_patcher import retail_layout_fixture


def synthetic_pristine() -> bytes:
    data = bytearray(retail_layout_fixture())
    pe = registry.parse_pe(data)
    audio_offset = registry.va_to_file_offset(pe, audio.ID26_AUDIO_LOOKUP_CALL_VA, 5)
    data[audio_offset:audio_offset + 5] = audio._call_rel32(
        audio.ID26_AUDIO_LOOKUP_CALL_VA, audio.RACE_CAR_ID_GETTER_VA
    )
    hook_offset = registry.va_to_file_offset(
        pe, ai.AI_PUBLICATION_HOOK_VA, len(ai.EXPECTED_PUBLICATION_BYTES)
    )
    data[hook_offset:hook_offset + len(ai.EXPECTED_PUBLICATION_BYTES)] = ai.EXPECTED_PUBLICATION_BYTES
    for call_va in (ai.SPLIT_SCREEN_CALL_VA, ai.SINGLE_PLAYER_CALL_VA):
        offset = registry.va_to_file_offset(pe, call_va, 5)
        data[offset:offset + 5] = audio._call_rel32(call_va, ai.AI_POOL_FUNCTION_VA)
    return bytes(data)


def synthetic_composition_hashes(source: bytes) -> tuple[str, str, str]:
    source_hash = ai.sha256(source)
    g1, _g1_manifest = registry.make_candidate(
        source,
        expected_sha256=source_hash,
        id26_profile=registry.ID26_MERCEDES_G1_STOCK_UNLOCK,
    )
    g2, _g2_manifest = audio.make_candidate(
        source,
        0,
        expected_source_sha256=source_hash,
        expected_g1_sha256=ai.sha256(g1),
    )
    return source_hash, ai.sha256(g1), ai.sha256(g2)


def emulate_generated_stub(stub: bytes, context: dict[str, int]) -> dict[str, int]:
    """Tiny test-only interpreter for exactly the emitted proof-stub opcodes."""
    stack = dict(context["stack"])
    esi = context["esi"]
    ebp = context["ebp"]
    zf = False
    eax = -1
    pushed = -1
    pc = 0

    while pc < len(stub):
        if stub[pc:pc + 3] == b"\x81\xBC\x24":
            offset = struct.unpack_from("<I", stub, pc + 3)[0]
            immediate = struct.unpack_from("<I", stub, pc + 7)[0]
            zf = (stack[offset] & 0xFFFFFFFF) == immediate
            pc += 11
        elif stub[pc:pc + 3] == b"\x83\xFE\x01":
            zf = esi == 1
            pc += 3
        elif stub[pc:pc + 3] == b"\x83\xFD\x04":
            zf = ebp == 4
            pc += 3
        elif stub[pc:pc + 3] == b"\x83\xBC\x24":
            offset = struct.unpack_from("<I", stub, pc + 3)[0]
            immediate = struct.unpack_from("b", stub, pc + 7)[0]
            zf = (stack[offset] & 0xFFFFFFFF) == (immediate & 0xFFFFFFFF)
            pc += 8
        elif stub[pc:pc + 2] == b"\x0F\x85":
            displacement = struct.unpack_from("<i", stub, pc + 2)[0]
            pc = pc + 6 + displacement if not zf else pc + 6
        elif stub[pc:pc + 3] == b"\xC7\x44\x24":
            offset = stub[pc + 3]
            stack[offset] = struct.unpack_from("<I", stub, pc + 4)[0]
            pc += 8
        elif stub[pc:pc + 4] == b"\x8B\x44\x24\x14":
            eax = stack[ai.STACK_SELECTED_CAR_ID]
            pc += 4
        elif stub[pc] == 0x50:
            pushed = eax
            pc += 1
        elif stub[pc] == 0xE9:
            displacement = struct.unpack_from("<i", stub, pc + 1)[0]
            target = ai.AI_PROOF_STUB_VA + pc + 5 + displacement
            return {"selected_id": stack[ai.STACK_SELECTED_CAR_ID],
                    "eax": eax, "pushed": pushed, "resume_va": target,
                    "driver_id": stack[0x18]}
        else:
            raise AssertionError(f"unrecognized proof stub opcode at {pc:#x}: {stub[pc:pc + 8].hex()}")
    raise AssertionError("proof stub did not reach its resume JMP")


class VehicleAICandidateTests(unittest.TestCase):
    def _run_stub(self, *, esi: int = 1, ebp: int = 4, call_return: int | None = None,
                  class_id: int = 0, player_id: int = 0, second_id: int = -1,
                  original_choice: int = 5, driver_id: int = 8) -> dict[str, int]:
        stub = ai.forced_proof_stub_bytes()
        stack = {
            ai.STACK_RETURN_ADDRESS: (call_return if call_return is not None
                                      else ai.SINGLE_PLAYER_RETURN_VA),
            ai.STACK_CLASS_ARGUMENT: class_id,
            ai.STACK_PLAYER_CAR_ID_ARGUMENT: player_id,
            ai.STACK_SECOND_CAR_ID_ARGUMENT: second_id,
            ai.STACK_SELECTED_CAR_ID: original_choice,
            0x18: driver_id,
        }
        return emulate_generated_stub(stub, {"esi": esi, "ebp": ebp, "stack": stack})

    def test_stub_substitutes_only_final_car1_id_and_replays_publication(self) -> None:
        result = self._run_stub()
        self.assertEqual(result["selected_id"], 26)
        self.assertEqual(result["eax"], 26)
        self.assertEqual(result["pushed"], 26)
        self.assertEqual(result["resume_va"], ai.AI_PUBLICATION_RESUME_VA)
        self.assertEqual(result["driver_id"], 8)

    def test_every_failed_guard_preserves_stock_choice_and_driver(self) -> None:
        cases = [
            {"esi": 2},
            {"esi": 3},
            {"ebp": 3},
            {"ebp": 5},
            {"class_id": 1},
            {"player_id": 1},
            {"second_id": 7},
            {"call_return": ai.SPLIT_SCREEN_CALL_VA + 5},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                result = self._run_stub(**overrides)
                self.assertEqual(result["selected_id"], 5)
                self.assertEqual(result["eax"], 5)
                self.assertEqual(result["pushed"], 5)
                self.assertEqual(result["resume_va"], ai.AI_PUBLICATION_RESUME_VA)
                self.assertEqual(result["driver_id"], 8)

    def test_guard_branch_targets_all_land_at_replayed_retail_instructions(self) -> None:
        stub = ai.forced_proof_stub_bytes()
        jne_offsets = [offset for offset in range(len(stub) - 1)
                       if stub[offset:offset + 2] == b"\x0F\x85"]
        self.assertEqual(len(jne_offsets), 6)
        restore_offset = stub.index(bytes.fromhex("C74424141A000000")) + 8
        for offset in jne_offsets:
            displacement = struct.unpack_from("<i", stub, offset + 2)[0]
            self.assertEqual(offset + 6 + displacement, restore_offset)
        self.assertEqual(stub[restore_offset:restore_offset + 5], bytes.fromhex("8B44241450"))
        jump_offset = len(stub) - 5
        jump_target = ai.AI_PROOF_STUB_VA + jump_offset + 5 + struct.unpack_from("<i", stub, jump_offset + 1)[0]
        self.assertEqual(jump_target, ai.AI_PUBLICATION_RESUME_VA)

    def test_forced_candidate_rebuild_is_deterministic_and_preserves_g2(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash, g2_hash = synthetic_composition_hashes(source)
        candidate, manifest = ai.make_candidate(
            source,
            expected_source_sha256=source_hash,
            expected_g1_sha256=g1_hash,
            expected_g2_sha256=g2_hash,
        )
        repeated, repeated_manifest = ai.make_candidate(
            source,
            expected_source_sha256=source_hash,
            expected_g1_sha256=g1_hash,
            expected_g2_sha256=g2_hash,
        )
        self.assertEqual(candidate, repeated)
        self.assertEqual(manifest, repeated_manifest)
        self.assertEqual(manifest["g2_base_sha256"], g2_hash)
        self.assertEqual(manifest["audio_identity"]["stock_audio_profile_id"], 0)
        self.assertEqual(manifest["ai_proof"]["participant_count_changed"], False)
        self.assertEqual(manifest["ai_proof"]["CarClass_written_by_H"], False)
        self.assertEqual(manifest["ai_proof"]["driver_selection_changed"], False)
        self.assertEqual(manifest["structural_self_check"]["id26"]["id"], 26)
        self.assertEqual(manifest["structural_self_check"]["id26"]["class"], 0)

    def test_h_patch_changes_only_hook_stub_and_text_virtual_size_from_g2(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash, g2_hash = synthetic_composition_hashes(source)
        g2, _g2_manifest = audio.make_candidate(
            source, 0, expected_source_sha256=source_hash, expected_g1_sha256=g1_hash
        )
        candidate, manifest = ai.make_candidate(
            source,
            expected_source_sha256=source_hash,
            expected_g1_sha256=g1_hash,
            expected_g2_sha256=g2_hash,
        )
        pe = registry.parse_pe(source)
        hook = registry.va_to_file_offset(pe, ai.AI_PUBLICATION_HOOK_VA, 5)
        stub = registry.va_to_file_offset(pe, ai.AI_PROOF_STUB_VA,
                                          len(ai.forced_proof_stub_bytes()))
        size_op = next(op for op in manifest["operations"] if op["name"] == "pe_text_virtual_size")
        size_offset = size_op["file_offset"]
        stub_bytes = ai.forced_proof_stub_bytes()
        touched_ranges = ((hook, hook + 5), (stub, stub + len(stub_bytes)),
                          (size_offset, size_offset + 4))
        expected_diff = {
            offset for start, end in touched_ranges for offset in range(start, end)
            if g2[offset] != candidate[offset]
        }
        actual_diff = {offset for offset, (before, after) in enumerate(zip(g2, candidate))
                       if before != after}
        self.assertEqual(actual_diff, expected_diff)

    def test_candidate_rejects_wrong_source_composition_and_unavailable_natural_mode(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash, g2_hash = synthetic_composition_hashes(source)
        with self.assertRaisesRegex(ai.CandidateError, "unsupported pristine retail SHA256"):
            ai.make_candidate(source, expected_source_sha256="0" * 64,
                              expected_g1_sha256=g1_hash, expected_g2_sha256=g2_hash)
        with self.assertRaisesRegex(audio.CandidateError, "G.1 reproduction hash mismatch"):
            ai.make_candidate(source, expected_source_sha256=source_hash,
                              expected_g1_sha256="0" * 64, expected_g2_sha256=g2_hash)
        with self.assertRaisesRegex(ai.CandidateError, "G.2 profile-0 reproduction hash mismatch"):
            ai.make_candidate(source, expected_source_sha256=source_hash,
                              expected_g1_sha256=g1_hash, expected_g2_sha256="0" * 64)
        with self.assertRaisesRegex(ai.CandidateError, "natural-t1-pool mode is intentionally unavailable"):
            ai.make_candidate(source, mode="natural-t1-pool", expected_source_sha256=source_hash,
                              expected_g1_sha256=g1_hash, expected_g2_sha256=g2_hash)

    def test_candidate_structural_verifier_rejects_mutated_hook_and_stub(self) -> None:
        source = synthetic_pristine()
        source_hash, g1_hash, g2_hash = synthetic_composition_hashes(source)
        candidate, manifest = ai.make_candidate(
            source,
            expected_source_sha256=source_hash,
            expected_g1_sha256=g1_hash,
            expected_g2_sha256=g2_hash,
        )
        pe = registry.parse_pe(source)
        for va, length in ((ai.AI_PUBLICATION_HOOK_VA, 5),
                           (ai.AI_PROOF_STUB_VA, len(ai.forced_proof_stub_bytes()))):
            with self.subTest(va=va):
                offset = registry.va_to_file_offset(pe, va, length)
                mutated = bytearray(candidate)
                mutated[offset] ^= 1
                bad_manifest = dict(manifest)
                bad_manifest["patched_sha256"] = ai.sha256(bytes(mutated))
                with self.assertRaises(ai.CandidateError):
                    ai._verify_structure(bytes(mutated), bad_manifest)


if __name__ == "__main__":
    unittest.main()
