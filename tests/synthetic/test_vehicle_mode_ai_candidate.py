from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import build_vehicle_mode_ai_candidate as mode_ai


def rel32_target(instruction_va: int, instruction: bytes) -> int:
    if instruction[0] != 0xE9 or len(instruction) != 5:
        raise AssertionError("expected a five-byte relative JMP")
    return instruction_va + 5 + struct.unpack_from("<i", instruction, 1)[0]


def emulate_append_stub(stub_va: int, reentry_va: int, common_exit_va: int,
                        excluded_ids: tuple[int, ...] = ()) -> dict[str, object]:
    """Interpret the audited stub branches and the native append-loop boundary.

    This deliberately models only the shim instructions and the already-audited
    native exclusion/append boundary; the executable verifier checks the real
    bytes against the exact retail image.
    """
    code = mode_ai.t1_append_stub_bytes(stub_va, reentry_va, common_exit_va)
    esi = 7
    trace: list[int] = []
    appended: list[int] = []

    # First visit: CMP ESI,27 / JE; MOV ESI,26 / JMP native body.
    trace.append(stub_va)
    if esi == 27:
        esi = struct.unpack_from("<I", code, 16)[0]
        return {"esi": esi, "trace": trace, "appended": appended,
                "exit": rel32_target(stub_va + 20, code[20:25])}
    esi = struct.unpack_from("<I", code, 6)[0]
    if esi not in excluded_ids:
        appended.append(esi)
    if rel32_target(stub_va + 10, code[10:15]) != reentry_va:
        raise AssertionError("append stub does not re-enter the native exclusion body")

    # Native T1 body processes one candidate and returns to the patched exit.
    esi += 1
    trace.extend((reentry_va, stub_va))
    if esi != 27:
        raise AssertionError("native append loop did not reach the expected sentinel")

    # Second visit: restore stock loop-end index and exit the class arm.
    esi = struct.unpack_from("<I", code, 16)[0]
    exit_va = rel32_target(stub_va + 20, code[20:25])
    return {"esi": esi, "trace": trace, "appended": appended, "exit": exit_va}


class VehicleModeAICandidateTests(unittest.TestCase):
    def test_all_dynamic_mode_t1_pools_are_sparse_and_exclusion_aware(self) -> None:
        for mode in ("quickrace", "rallye_cup", "invitation", "master_rallye"):
            with self.subTest(mode=mode):
                self.assertEqual(mode_ai.pool_for_mode(mode, 0),
                                 [0, 1, 2, 3, 4, 5, 6, 26])
                self.assertEqual(mode_ai.pool_for_mode(mode, 0, (0,)),
                                 [1, 2, 3, 4, 5, 6, 26])
                self.assertEqual(mode_ai.pool_for_mode(mode, 0, (26,)),
                                 [0, 1, 2, 3, 4, 5, 6])
                self.assertEqual(mode_ai.pool_for_mode(mode, 0, (0, 26)),
                                 [1, 2, 3, 4, 5, 6])
                self.assertNotIn(7, mode_ai.pool_for_mode(mode, 0))

    def test_non_t1_source_pools_are_unchanged_and_do_not_add_id26(self) -> None:
        self.assertEqual(mode_ai.pool_for_mode("rallye_cup", 1), list(range(7, 14)))
        self.assertEqual(mode_ai.pool_for_mode("master_rallye", 2), list(range(14, 21)))
        self.assertEqual(mode_ai.pool_for_mode("invitation", 4), list(range(14, 21)))
        for class_code in (1, 2, 4):
            with self.subTest(class_code=class_code):
                self.assertNotIn(26, mode_ai.pool_for_mode("rallye_cup", class_code))

    def test_authored_or_unmapped_modes_fail_closed(self) -> None:
        for mode in ("challenge", "practice", "unknown"):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(mode_ai.CandidateError, "no dynamic vehicle pool"):
                    mode_ai.pool_for_mode(mode, 0)

    def test_native_exclusions_are_bounded_and_typed(self) -> None:
        with self.assertRaisesRegex(mode_ai.CandidateError, "at most two"):
            mode_ai.pool_for_mode("master_rallye", 0, (0, 1, 2))
        with self.assertRaisesRegex(mode_ai.CandidateError, "integer exclusions"):
            mode_ai.pool_for_mode("rallye_cup", 0, ("26",))

    def test_cup_invitation_stub_appends_once_then_restores_native_loop_index(self) -> None:
        outcome = emulate_append_stub(mode_ai.CUP_T1_STUB_VA,
                                      mode_ai.CUP_T1_REENTRY_VA,
                                      mode_ai.CUP_T1_COMMON_EXIT_VA)
        self.assertEqual(outcome["appended"], [26])
        self.assertEqual(outcome["esi"], 7)
        self.assertEqual(outcome["exit"], mode_ai.CUP_T1_COMMON_EXIT_VA)
        self.assertEqual(outcome["trace"], [mode_ai.CUP_T1_STUB_VA,
                                             mode_ai.CUP_T1_REENTRY_VA,
                                             mode_ai.CUP_T1_STUB_VA])

    def test_master_stub_preserves_exclusion_and_native_control_flow(self) -> None:
        included = emulate_append_stub(mode_ai.MASTER_T1_STUB_VA,
                                       mode_ai.MASTER_T1_REENTRY_VA,
                                       mode_ai.MASTER_T1_COMMON_EXIT_VA)
        excluded = emulate_append_stub(mode_ai.MASTER_T1_STUB_VA,
                                       mode_ai.MASTER_T1_REENTRY_VA,
                                       mode_ai.MASTER_T1_COMMON_EXIT_VA,
                                       (26,))
        self.assertEqual(included["appended"], [26])
        self.assertEqual(excluded["appended"], [])
        for outcome in (included, excluded):
            self.assertEqual(outcome["esi"], 7)
            self.assertEqual(outcome["exit"], mode_ai.MASTER_T1_COMMON_EXIT_VA)

    def test_stubs_branch_to_native_exclusion_body_and_common_exit(self) -> None:
        for stub_va, reentry_va, exit_va in (
            (mode_ai.CUP_T1_STUB_VA, mode_ai.CUP_T1_REENTRY_VA,
             mode_ai.CUP_T1_COMMON_EXIT_VA),
            (mode_ai.MASTER_T1_STUB_VA, mode_ai.MASTER_T1_REENTRY_VA,
             mode_ai.MASTER_T1_COMMON_EXIT_VA),
        ):
            with self.subTest(stub=hex(stub_va)):
                stub = mode_ai.t1_append_stub_bytes(stub_va, reentry_va, exit_va)
                self.assertEqual(stub[:5], bytes.fromhex("83FE1B740A"))
                self.assertEqual(stub[5:10], bytes.fromhex("BE1A000000"))
                self.assertEqual(struct.unpack_from("<I", stub, 16)[0], 7)
                self.assertEqual(rel32_target(stub_va + 10, stub[10:15]), reentry_va)
                self.assertEqual(rel32_target(stub_va + 20, stub[20:25]), exit_va)

    def test_generated_manifest_records_scope_lifecycle_and_identity(self) -> None:
        pools = mode_ai.dynamic_t1_mode_pools()
        lifecycle = mode_ai.eligibility_lifecycle_manifest()
        identity = mode_ai.id26_identity_manifest()
        self.assertEqual(mode_ai.H1_SHA256,
                         "e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a")
        self.assertEqual(set(pools),
                         {"quickrace", "rallye_cup", "invitation", "master_rallye"})
        self.assertEqual(pools["quickrace"]["status"],
                         "PRESERVED_FROM_H1_CONFIRMED_BY_RUNTIME")
        for mode in ("rallye_cup", "invitation", "master_rallye"):
            self.assertEqual(pools[mode]["source_ids"], [0, 1, 2, 3, 4, 5, 6, 26])
            self.assertEqual(pools[mode]["status"], "STATIC_PATCH_READY_FOR_HUMAN_RUNTIME")
        self.assertTrue(lifecycle["id26_appended_only_at_new_dynamic_roster_generation"])
        self.assertFalse(lifecycle["native_cup_invitation_roster_storage_changed"])
        self.assertFalse(lifecycle["masterrallye_car_n_storage_changed"])
        self.assertFalse(lifecycle["master_save_or_load_changed"])
        self.assertFalse(lifecycle["existing_rosters_mutated"])
        self.assertFalse(lifecycle["stage_reroll_added"])
        self.assertFalse(lifecycle["class_randomization_added"])
        self.assertEqual(identity["physical_car_id"], 26)
        self.assertFalse(identity["native_driver_id_selection_changed"])
        self.assertEqual(identity["results_display"], "JEAN-PIERRE STRUGO")
        self.assertEqual(identity["audio_profile"], 0)


if __name__ == "__main__":
    unittest.main()
