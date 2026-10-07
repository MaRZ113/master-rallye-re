from __future__ import annotations

import hashlib
import struct
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import build_vehicle_multislot_i0 as i0
import prepare_multislot_vehicle_select_overlay as overlay
import vehicle_multislot_runtime_package as package


def rel32_target(instruction_va: int, instruction: bytes) -> int:
    if len(instruction) != 5 or instruction[0] != 0xE9:
        raise AssertionError("expected a five-byte relative JMP")
    return instruction_va + 5 + struct.unpack_from("<i", instruction, 1)[0]


def emulate_t2_append(stub_va: int, reentry_va: int, exit_va: int,
                      excluded_ids: tuple[int, ...] = ()) -> dict[str, object]:
    """Model the small append shim around the audited native exclusion body."""
    code = i0.t2_append_stub_bytes(stub_va, reentry_va, exit_va)
    esi = 14  # the native T2 candidate loop's stock end sentinel
    first_target = stub_va + 5 + struct.unpack_from("<b", code, 4)[0]
    appended: list[int] = []
    trace: list[int] = [stub_va]

    if esi == 28:
        esi = struct.unpack_from("<I", code, 16)[0]
        return {"appended": appended, "esi": esi, "exit": rel32_target(stub_va + 20, code[20:25])}

    esi = struct.unpack_from("<I", code, 6)[0]
    reentry = rel32_target(stub_va + 10, code[10:15])
    if esi not in excluded_ids:
        appended.append(esi)
    # The unchanged native exclusion/append loop processes ID27, then advances
    # to its stock end sentinel plus the appended entry.
    esi = 28
    trace.extend((reentry, stub_va))

    second_target = stub_va + 5 + struct.unpack_from("<b", code, 4)[0]
    if esi == 28:
        esi = struct.unpack_from("<I", code, 16)[0]
        exit_target = rel32_target(stub_va + 20, code[20:25])
    else:  # pragma: no cover - guards emulator drift
        raise AssertionError("second shim visit did not see its termination sentinel")

    return {"appended": appended, "esi": esi, "exit": exit_target,
            "first_reentry": reentry, "first_target": first_target,
            "second_target": second_target, "trace": trace}


class VehicleMultiSlotI0StaticTests(unittest.TestCase):
    def test_registry_layout_moves_only_adjacent_racetest_array(self) -> None:
        h2 = i0.registry_layout(26)
        i0_layout = i0.registry_layout(27)
        self.assertEqual(h2["record_count"], 27)
        self.assertEqual(h2["racetest_base"], 0x580)
        self.assertEqual(h2["allocation_size"], 0xC34)
        self.assertEqual(i0_layout["record_count"], 28)
        self.assertEqual(i0_layout["record25_offset"], 0x518)
        self.assertEqual(i0_layout["record26_offset"], 0x54C)
        self.assertEqual(i0_layout["record27_offset"], 0x580)
        self.assertEqual(i0_layout["racetest_base"], 0x5B4)
        self.assertEqual(i0_layout["allocation_size"], 0xC68)
        self.assertEqual(i0_layout["racetest_count"], 39)
        self.assertEqual(i0_layout["racetest_stride"], 0x2C)

    def test_sparse_class_mapping_preserves_all_prior_physical_ids(self) -> None:
        for physical_id in range(28):
            with self.subTest(physical_id=physical_id):
                pair = i0.physical_to_class_local(physical_id)
                self.assertEqual(i0.class_local_to_physical(*pair), physical_id)
        self.assertEqual(i0.class_local_to_physical(0, 7), 26)
        self.assertEqual(i0.class_local_to_physical(1, 7), 27)
        self.assertEqual(i0.class_local_to_physical(2, 11), 25)
        self.assertNotEqual(i0.class_local_to_physical(1, 7), 14)
        self.assertEqual(i0.physical_to_class_local(14), (2, 0))

    def test_exact_class_populations_and_sparse_dynamic_pools(self) -> None:
        self.assertEqual(i0.T1_PHYSICAL_IDS, (*range(7), 26))
        self.assertEqual(i0.T2_PHYSICAL_IDS, (*range(7, 14), 27))
        self.assertEqual(i0.T3_BASE_PHYSICAL_IDS, tuple(range(14, 21)))
        for mode in ("quickrace", "rallye_cup", "master_rallye"):
            with self.subTest(mode=mode):
                self.assertEqual(i0.pool_for_mode(mode, 0), [0, 1, 2, 3, 4, 5, 6, 26])
                self.assertEqual(i0.pool_for_mode(mode, 1), [7, 8, 9, 10, 11, 12, 13, 27])
                self.assertEqual(i0.pool_for_mode(mode, 2), list(range(14, 21)))
                self.assertEqual(i0.pool_for_mode(mode, 1, (7,)), [8, 9, 10, 11, 12, 13, 27])
                self.assertNotIn(14, i0.pool_for_mode(mode, 1))
                self.assertNotIn(7, i0.pool_for_mode(mode, 0))
        with self.assertRaises(i0.CandidateError):
            i0.pool_for_mode("challenge", 1)
        with self.assertRaises(i0.CandidateError):
            i0.pool_for_mode("quickrace", 3)

    def test_id27_profile_is_explicitly_a_navara_donor_and_keeps_id7(self) -> None:
        profile = i0.ID27_RECORD
        self.assertEqual((profile.slot_id, profile.vehicle_class, profile.local_index), (27, 1, 7))
        self.assertEqual(profile.donor_id, 7)
        self.assertEqual((profile.runtime_family, profile.model_family, profile.wheel_family),
                         ("Navara", "Navara", "Navara"))
        self.assertEqual(profile.stats, (7, 6, 6, 5))
        self.assertEqual(profile.vehicle_select_icon_frame, 23)
        self.assertEqual(profile.unlock_policy, "mirror-stock-vehicle-id-10")
        self.assertEqual(profile.race_colour_role,
                         "cyan physical-ID27 slot canary; not authentic addon art")
        self.assertTrue(profile.asset_package.startswith("retail Data.sma"))
        self.assertEqual(i0.unlock_oracle(27), 10)
        self.assertEqual(i0.locked_reason_selector(27), 12)
        self.assertEqual(i0.audio_profile_for(27), 7)
        self.assertEqual(i0.audio_profile_for(26), 0)

    def test_t2_append_shim_preserves_native_exclusion_and_loop_exit(self) -> None:
        cases = (
            (i0.QUICKRACE_T2_HOOK_VA, i0.QUICKRACE_T2_REENTRY_VA, i0.QUICKRACE_T2_EXIT_VA),
            (i0.CUP_T2_HOOK_VA, i0.CUP_T2_REENTRY_VA, i0.CUP_T2_EXIT_VA),
            (i0.MASTER_T2_HOOK_VA, i0.MASTER_T2_REENTRY_VA, i0.MASTER_T2_EXIT_VA),
        )
        for stub_va, reentry_va, exit_va in cases:
            with self.subTest(stub=hex(stub_va)):
                code = i0.t2_append_stub_bytes(stub_va, reentry_va, exit_va)
                self.assertEqual(len(code), 25)
                self.assertEqual(code[:5], bytes.fromhex("83FE1C740A"))
                self.assertEqual(code[5:10], bytes.fromhex("BE1B000000"))
                self.assertEqual(rel32_target(stub_va + 10, code[10:15]), reentry_va)
                self.assertEqual(code[15:20], bytes.fromhex("BE0E000000"))
                self.assertEqual(rel32_target(stub_va + 20, code[20:25]), exit_va)
                result = emulate_t2_append(stub_va, reentry_va, exit_va)
                self.assertEqual(result["appended"], [27])
                self.assertEqual(result["esi"], 14)
                self.assertEqual(result["exit"], exit_va)
                self.assertEqual(result["first_reentry"], reentry_va)
                self.assertEqual(result["first_target"], stub_va + 15)
                self.assertEqual(result["second_target"], stub_va + 15)
                excluded = emulate_t2_append(stub_va, reentry_va, exit_va, (27,))
                self.assertEqual(excluded["appended"], [])
                self.assertEqual(excluded["exit"], exit_va)

    def test_package_paths_reject_traversal_and_accept_nested_resource_names(self) -> None:
        self.assertEqual(package._safe_relative("DataScene/FrontendScreens/VehicleSelect.xml"),
                         Path("DataScene/FrontendScreens/VehicleSelect.xml"))
        for unsafe in ("", "/absolute/file", "../escape", "a/../escape", "a//b", "a/./b", "C:/game/file"):
            with self.subTest(path=unsafe), self.assertRaises(package.PackageError):
                package._safe_relative(unsafe)


class VehicleMultiSlotI0OverlayTests(unittest.TestCase):
    source = REPO.parent / "corpora/retail/Data.sma_unpacked/DataScene/FrontendScreens/VehicleSelect.xml"

    @unittest.skipUnless(source.is_file(), "retail VehicleSelect corpus fixture is not packaged")
    def test_t2_car8_overlay_is_deterministic_and_keeps_native_lock_gate(self) -> None:
        output, manifest = overlay.build_overlay_bytes(self.source.read_bytes())
        self.assertEqual(hashlib.sha256(output).hexdigest(),
                         "0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490")
        self.assertEqual(manifest["change"]["widget"], "T2_Car8")
        self.assertEqual(manifest["change"]["physical_vehicle_id"], 27)
        self.assertEqual(manifest["change"]["class_local_index"], 7)
        self.assertEqual(manifest["change"]["donor_art"],
                         "stock physical ID7/Navara carsheet frame 23; diagnostic only")
        self.assertFalse(manifest["audit"]["physical_id27_is_real_independent_vehicle"])
        self.assertTrue(manifest["audit"]["stock_t2_button_unlocker_retained"])


class VehicleMultiSlotI0ExecutableTests(unittest.TestCase):
    source = REPO.parent / "corpora/retail/MRallye.exe"

    @classmethod
    def setUpClass(cls) -> None:
        if not cls.source.is_file():
            raise unittest.SkipTest("pristine retail executable fixture is not packaged")
        data = cls.source.read_bytes()
        cls.source_bytes = data
        cls.candidate, cls.manifest = i0.make_candidate(data)
        cls.parent, cls.parent_manifest = i0.h2.make_candidate(data)

    def test_exact_candidate_is_reproducible_from_pristine_and_h2(self) -> None:
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), i0.RETAIL_SHA256)
        self.assertEqual(hashlib.sha256(self.parent).hexdigest(), i0.H2_SHA256)
        self.assertEqual(hashlib.sha256(self.candidate).hexdigest(),
                         "50ff267d2758c1ff894d91bcdafd7dba4a2fa278d678a075e7767120727abbea")
        self.assertEqual(len(self.candidate), i0.RETAIL_SIZE)
        self.assertEqual(self.manifest["status"], "READY_FOR_HUMAN_RUNTIME")
        self.assertFalse(self.manifest["higher_phase_boundary"]["r5v_i_full_pass"])
        self.assertEqual(self.manifest["higher_phase_boundary"]["i1_real_t2_payload"],
                         "REAL_T2_PAYLOAD_REQUIRED")

    def test_unknown_pristine_bytes_fail_closed(self) -> None:
        changed = bytearray(self.source_bytes)
        changed[0x100] ^= 0x01
        with self.assertRaisesRegex(i0.CandidateError, "unsupported pristine retail image"):
            i0.make_candidate(bytes(changed))

    def test_candidate_layout_pool_modes_and_native_driver_policy(self) -> None:
        manifest = self.manifest
        self.assertEqual(manifest["layout"]["record_count"], 28)
        self.assertEqual(manifest["layout"]["record27_offset"], 0x580)
        self.assertEqual(manifest["layout"]["racetest_base"], 0x5B4)
        self.assertEqual(manifest["capacity"], {"T1": 8, "T2": 8, "T3": 12})
        self.assertEqual(manifest["class_mapping"]["T1_local7"], 26)
        self.assertEqual(manifest["class_mapping"]["T2_local7"], 27)
        self.assertEqual(manifest["class_mapping"]["T3_local0_to11"], list(range(14, 26)))
        self.assertEqual(manifest["ai_pools"]["quickrace_t2"], list(range(7, 14)) + [27])
        self.assertEqual(manifest["ai_pools"]["rallye_cup_t2_new_roster_only"], list(range(7, 14)) + [27])
        self.assertEqual(manifest["ai_pools"]["master_rallye_t2_new_competition_only"], list(range(7, 14)) + [27])
        self.assertFalse(manifest["ai_pools"]["id27_forced_participant"])
        self.assertFalse(manifest["ai_pools"]["existing_competition_rosters_mutated"])
        self.assertFalse(manifest["profiles"][1]["native_driver_id_changed"])
        self.assertEqual(manifest["profiles"][0]["results_display"], "JEAN-PIERRE STRUGO")
        self.assertEqual(manifest["profiles"][1]["display"]["results"], "ID27 SLOT PROOF")

    def test_secondary_array_relocation_and_physical_bounds_are_explicit(self) -> None:
        manifest = self.manifest
        arrays = manifest["registry_arrays"]
        self.assertEqual(arrays["vehicle_record_stride"], 0x34)
        self.assertEqual(arrays["secondary_racetest_displacement_from_retail"], 0x68)
        self.assertEqual(arrays["secondary_initializer_lea_count"], 39)
        self.assertEqual(arrays["secondary_consumer_count"], 11)
        self.assertEqual(arrays["racetest_array_count"], 39)
        self.assertFalse(arrays["physical_allocation_changed_other_than_vehicle_registry_and_adjacent_racetest"])
        operations = manifest["operations"]
        self.assertEqual(sum(op["category"] == "secondary-array-construction" for op in operations), 39)
        self.assertEqual(sum(op["category"] == "secondary-array-consumer" for op in operations), 11)
        spans = []
        for operation in operations:
            start = operation["file_offset"]
            original = bytes.fromhex(operation["original_bytes"])
            replacement = bytes.fromhex(operation["replacement_bytes"])
            self.assertEqual(len(original), len(replacement))
            self.assertEqual(self.parent[start:start + len(original)], original)
            self.assertEqual(self.candidate[start:start + len(replacement)], replacement)
            spans.append((start, start + len(replacement)))
        spans.sort()
        self.assertTrue(all(left[1] <= right[0] for left, right in zip(spans, spans[1:])))

    def test_code_cave_is_mapped_before_rdata_and_all_entrypoints_are_inside(self) -> None:
        size = self.manifest["text_virtual_size"]
        cave_start = int(size["code_cave_va"], 16)
        cave_end = int(size["payload_end_exclusive_va"], 16)
        rdata = int(size["rdata_va"], 16)
        self.assertLess(cave_start, cave_end)
        self.assertLessEqual(cave_end, rdata)
        self.assertTrue(size["zero_fill_verified_in_h2"])
        self.assertTrue(size["non_overlap_proven"])
        for name, raw in self.manifest["code_entrypoints"].items():
            with self.subTest(name=name):
                address = int(raw, 16)
                self.assertGreaterEqual(address, cave_start)
                self.assertLess(address, cave_end)
        self.assertFalse(self.manifest["runtime_architecture"]["randomizer_present"])
        self.assertFalse(self.manifest["runtime_architecture"]["participant_count_changed"])

    def test_inverse_restores_exact_h2_bytes(self) -> None:
        restored = bytearray(self.candidate)
        for operation in reversed(self.manifest["operations"]):
            start = operation["file_offset"]
            original = bytes.fromhex(operation["original_bytes"])
            replacement = bytes.fromhex(operation["replacement_bytes"])
            self.assertEqual(restored[start:start + len(replacement)], replacement)
            restored[start:start + len(original)] = original
        self.assertEqual(bytes(restored), self.parent)
        self.assertEqual(hashlib.sha256(restored).hexdigest(), i0.H2_SHA256)
        self.assertTrue(self.manifest["inverse"]["i0_layer_restores_exact_h2_bytes"])


if __name__ == "__main__":
    unittest.main()
