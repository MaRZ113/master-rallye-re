from __future__ import annotations

import json
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import addon_runtime
import j2_frontend_reentry as reentry


class VehicleSelectReentryModelTests(unittest.TestCase):
    def test_sparse_physical_id_restoration_yields_class_and_local_ordinal(self) -> None:
        self.assertEqual(reentry.expected_xy_for_physical_id(27), (1, 7))
        self.assertEqual(reentry.expected_xy_for_physical_id(26), (0, 7))
        self.assertEqual(reentry.expected_xy_for_physical_id(7), (1, 0))
        self.assertEqual(reentry.expected_xy_for_physical_id(0), (0, 0))
        self.assertEqual(reentry.expected_xy_for_physical_id(25), (2, 11))

    def test_player_slots_map_independently_without_aliasing(self) -> None:
        stored_by_player = {0: 27, 1: 26}
        state_by_player = {
            player_id: (physical_id, *reentry.expected_xy_for_physical_id(physical_id))
            for player_id, physical_id in stored_by_player.items()
        }
        self.assertEqual(state_by_player[0], (27, 1, 7))
        self.assertEqual(state_by_player[1], (26, 0, 7))
        self.assertEqual(stored_by_player, {0: 27, 1: 26})

    def test_stock_class_switch_ordinals_remain_native(self) -> None:
        for physical_id in (0, 6, 7, 13, 14, 25):
            class_index, local = reentry.expected_xy_for_physical_id(physical_id)
            self.assertEqual(local, physical_id - (0, 7, 14)[class_index])
        with self.assertRaisesRegex(reentry.ReentryBundleError, "not in the qualified catalog"):
            reentry.expected_xy_for_physical_id(28)

    def test_native_stub_only_republishes_xy_and_replays_vehicle_list(self) -> None:
        stub = reentry.make_republish_stub()
        self.assertEqual(stub[0], 0x9C)  # pushfd
        self.assertEqual(stub[-11], 0x9D)  # popfd, followed by replayed PUSH + JMP
        self.assertIn(struct.pack("<I", reentry.YVALUE_PATH_VA), stub)
        self.assertIn(struct.pack("<I", reentry.XVALUE_PATH_VA), stub)
        self.assertIn(struct.pack("<I", reentry.VEHICLE_LIST_PATH_VA), stub)
        call_targets = []
        for offset, opcode in enumerate(stub):
            if opcode == 0xE8:
                displacement = struct.unpack_from("<i", stub, offset + 1)[0]
                call_targets.append(reentry.STUB_VA + offset + 5 + displacement)
        self.assertEqual(call_targets, [
            reentry.BROKER_PATH_INIT_VA, reentry.BROKER_VALUE_GET_VA, reentry.BROKER_VALUE_SET_VA,
            reentry.BROKER_PATH_INIT_VA, reentry.BROKER_VALUE_GET_VA, reentry.BROKER_VALUE_SET_VA,
        ])
        self.assertIn(b"\x8b\x47\x10", stub)
        self.assertIn(b"\x8b\x44\x97\x14", stub)
        self.assertNotIn(struct.pack("<I", 0x006E5868), stub)  # QuickRace/Car0 read remains native.
        self.assertNotIn(struct.pack("<I", 0x006E5850), stub)  # QuickRace/Car1 read remains native.
        self.assertNotIn(b"\x68\x1a\x00\x00\x00", stub)  # no fixed CarID26 publication
        self.assertNotIn(b"\x68\x1b\x00\x00\x00", stub)  # no fixed CarID27 publication
        self.assertEqual(len(stub), len(reentry.make_republish_stub()))

    def test_emitted_stub_bytes_resolve_both_path_objects_to_the_initialized_local(self) -> None:
        stub = reentry.make_republish_stub()
        audit = reentry.verify_republish_stub(stub)
        self.assertEqual(audit["status"], "PASS_SYMBOLIC_STUB_ABI")
        self.assertEqual(audit["broker_path_object_offsets"], [0x14, 0x14])
        self.assertEqual(audit["entry_esp_before_replayed_push"], 0)
        self.assertEqual(audit["continuation_esp"], -4)
        self.assertEqual(audit["path_init_ret_cleanup"], 4)
        self.assertEqual(audit["value_get_ret_cleanup"], 0)
        self.assertEqual(audit["value_set_ret_cleanup"], 8)
        self.assertEqual(audit["replayed_push"], "PUSH 0x006b74f8")
        self.assertEqual(audit["continuation"], "0x00481157")

    def test_previous_bad_post_path_init_displacements_are_rejected(self) -> None:
        stub = bytearray(reentry.make_republish_stub())
        bad_instruction = b"\x8d\x4c\x24\x18"
        occurrences = [i for i in range(len(stub)) if stub.startswith(bad_instruction, i)]
        self.assertEqual(len(occurrences), 2)
        for offset in occurrences:
            stub[offset + 3] = 0x14
        self.assertEqual(
            hashlib.sha256(stub).hexdigest(),
            "f0485557df0654c21a48b0acfed4639e0bb36591b8f80f16963c315981e857e1",
        )
        with self.assertRaisesRegex(reentry.ReentryBundleError, "audited ABI template"):
            reentry.verify_republish_stub(bytes(stub))

class J2ReentryPatchPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retail = addon_runtime.DEFAULT_RETAIL_EXE
        cls.base_bundle = reentry.J1_BUNDLE
        if not cls.retail.is_file() or not (cls.base_bundle / "native-patch-ops.rvp").is_file():
            raise unittest.SkipTest("exact retail executable or verified J.1 bundle is unavailable")
        cls.source = cls.retail.read_bytes()
        verified = addon_runtime.verify_bundle(cls.base_bundle)
        if verified.get("status") != "PASS_STATIC_RUNTIME_BUNDLE":
            raise unittest.SkipTest("exact J.1 bundle did not pass its deterministic verifier")
        cls.manifest, cls.operations, cls.profile, cls.reference_image, cls.manifest_bytes = (
            reentry._j2_artifacts(cls.source, cls.base_bundle))

    def test_actual_candidate_reverse_mapper_writes_id27_to_t2_local_slot(self) -> None:
        audit = self.manifest["id27_reverse_mapping_correction"]
        self.assertEqual(audit["status"], "PASS_ID27_NATIVE_REVERSE_FORWARD_MAP")
        self.assertEqual(audit["class_field_offset"], 0x10)
        self.assertEqual(audit["class_value"], 1)
        self.assertEqual(audit["local_field_offset"], 0x18)
        self.assertEqual(audit["local_value"], 7)
        self.assertEqual(audit["restored_state"], {"CarClass": 1, "local_ordinal": 7})
        self.assertEqual(audit["forward_physical_id"], 27)
        self.assertFalse(audit["physical_id_written"])

    def test_old_i1_reverse_mapper_displacement_fails_native_state_audit(self) -> None:
        _parent, old_image, _rows = reentry._parse_and_reconstruct(
            self.source, (self.base_bundle / "native-patch-ops.rvp").read_bytes())
        with self.assertRaisesRegex(reentry.ReentryBundleError, "local ordinal write"):
            reentry._verify_id27_reverse_mapper(old_image)

    def test_j2_changes_only_the_id27_mapper_displacement_and_reentry_ranges(self) -> None:
        _parent, old_image, _rows = reentry._parse_and_reconstruct(
            self.source, (self.base_bundle / "native-patch-ops.rvp").read_bytes())
        changed = {i for i, (before, after) in enumerate(zip(old_image, self.reference_image))
                   if before != after}
        _pe, sections = addon_runtime._pe_sections(self.source)
        hook_offset, _ = reentry._rva_to_file_offset(
            sections, reentry.HOOK_RVA, len(reentry.EXPECTED_HOOK))
        stub_offset, _ = reentry._rva_to_file_offset(
            sections, reentry.STUB_RVA, len(reentry.make_republish_stub()))
        hook = next(row for row in self.manifest["operations"]
                    if row["name"] == "vehicle_select_republish_final_class_local_xy")
        stub = next(row for row in self.manifest["operations"]
                    if row["name"] == "vehicle_select_republish_stub")
        expected_changes = {
            hook_offset + i for i, (before, after) in enumerate(zip(
                bytes.fromhex(hook["expected_original_bytes"]),
                bytes.fromhex(hook["replacement_bytes"]))) if before != after
        } | {
            stub_offset + i for i, (before, after) in enumerate(zip(
                bytes.fromhex(stub["expected_original_bytes"]),
                bytes.fromhex(stub["replacement_bytes"]))) if before != after
        } | {reentry.ID27_REVERSE_LOCAL_STORE_FILE_OFFSET + 2}
        self.assertEqual(changed, expected_changes)
        self.assertEqual(
            self.reference_image[reentry.ID27_REVERSE_LOCAL_STORE_FILE_OFFSET:
                                 reentry.ID27_REVERSE_LOCAL_STORE_FILE_OFFSET + 4],
            reentry.ID27_REVERSE_LOCAL_STORE_FIXED)

    def test_id26_and_stock_reverse_mapper_fallback_bytes_are_unchanged(self) -> None:
        _parent, old_image, _rows = reentry._parse_and_reconstruct(
            self.source, (self.base_bundle / "native-patch-ops.rvp").read_bytes())
        for start, end in (
            (0x0068E340, 0x0068E380),  # H.2 ID26 sparse reverse helper / stock continuation
            (0x0068E87A, 0x0068E895),  # ID27 forward fallback and reverse discriminator
            (0x0068E89C, 0x0068E8B0),  # common tail and following code
        ):
            offset = start - reentry.IMAGE_BASE
            self.assertEqual(self.reference_image[offset:end - reentry.IMAGE_BASE],
                             old_image[offset:end - reentry.IMAGE_BASE])

    def test_site_hook_uses_exact_stock_preimage_and_reaches_stub(self) -> None:
        hook = next(row for row in self.manifest["operations"]
                    if row["name"] == "vehicle_select_republish_final_class_local_xy")
        self.assertEqual(hook["preferred_va"], reentry.HOOK_VA)
        self.assertEqual(bytes.fromhex(hook["expected_original_bytes"]), reentry.EXPECTED_HOOK)
        jump = bytes.fromhex(hook["replacement_bytes"])
        self.assertEqual(jump[0], 0xE9)
        self.assertEqual(reentry.HOOK_VA + 5 + struct.unpack_from("<i", jump, 1)[0], reentry.STUB_VA)

    def test_stub_is_in_executable_zero_fill_after_parent_payload(self) -> None:
        stub_op = next(row for row in self.manifest["operations"]
                       if row["name"] == "vehicle_select_republish_stub")
        self.assertEqual(stub_op["preferred_va"], reentry.STUB_VA)
        self.assertTrue(set(bytes.fromhex(stub_op["expected_original_bytes"])) <= {0})
        self.assertEqual(bytes.fromhex(stub_op["replacement_bytes"]), reentry.make_republish_stub())
        self.assertEqual(stub_op["page_class"], "EXECUTE_READWRITE")

    def test_two_new_ops_do_not_mutate_physical_selection_or_commit_state(self) -> None:
        added = self.manifest["operations"][-2:]
        self.assertEqual([row["name"] for row in added], [
            "vehicle_select_republish_final_class_local_xy", "vehicle_select_republish_stub",
        ])
        for row in added:
            self.assertNotIn("selectedCar", json.dumps(row))
            self.assertNotIn("QuickRace/Car0", json.dumps(row))
            self.assertNotIn("QuickRace/Car1", json.dumps(row))
            self.assertNotIn("Unlock", json.dumps(row))
        self.assertFalse(self.manifest["vehicle_select_reentry"]["physical_car_id_or_commit_state_written"])
        self.assertFalse(self.manifest["vehicle_select_reentry"]["global_xy_override"])
        self.assertFalse(self.manifest["reference_image"]["written_to_disk"])

    def test_j1_parent_is_untouched_and_j2_has_one_parent_row_fix(self) -> None:
        parent = (self.base_bundle / "native-patch-ops.rvp").read_bytes()
        parent_fields = addon_runtime.RVP_HEADER.unpack_from(parent)
        final_fields = addon_runtime.RVP_HEADER.unpack_from(self.operations)
        self.assertEqual(parent_fields[6], 246)
        self.assertEqual(final_fields[6], 248)
        self.assertEqual((self.base_bundle / "native-patch-ops.rvp").read_bytes(), parent)
        _old_header, _old_image, old_rows = reentry._parse_and_reconstruct(self.source, parent)
        _new_header, _new_image, new_rows = reentry._parse_and_reconstruct(self.source, self.operations)
        self.assertEqual(len(old_rows), 246)
        self.assertEqual(len(new_rows), 248)
        deltas = []
        for before, after in zip(old_rows, new_rows[:246]):
            if before != after:
                deltas.append((before, after))
        self.assertEqual(len(deltas), 1)
        before, after = deltas[0]
        self.assertEqual(before["file_offset"], reentry.ID27_REVERSE_LOCAL_STORE_FILE_OFFSET)
        self.assertEqual(before["before"], after["before"])
        self.assertEqual(before["after"], reentry.ID27_REVERSE_LOCAL_STORE_EXPECTED)
        self.assertEqual(after["after"], reentry.ID27_REVERSE_LOCAL_STORE_FIXED)
        self.assertEqual(before["after"][:2], after["after"][:2])
        self.assertEqual(before["after"][3:], after["after"][3:])
        self.assertEqual(self.profile["addon_plan_sha256"], addon_runtime.REFERENCE_PLAN_SHA256)
        self.assertFalse(self.profile["runtime_installable"])
        self.assertFalse(self.profile["runtime_qualified"])
        self.assertEqual(len(self.reference_image), addon_runtime.RETAIL_SIZE)

    def test_patch_plan_is_deterministic_and_preserves_identity_maps(self) -> None:
        other = reentry._j2_artifacts(self.source, self.base_bundle)
        self.assertEqual(self.manifest_bytes, other[4])
        self.assertEqual(self.operations, other[1])
        self.assertEqual(self.reference_image, other[3])
        self.assertEqual(reentry.expected_xy_for_physical_id(26), (0, 7))
        self.assertEqual(reentry.expected_xy_for_physical_id(27), (1, 7))
        self.assertEqual(reentry.expected_xy_for_physical_id(7), (1, 0))

    def test_wrong_build_is_rejected_before_j2_derivation(self) -> None:
        with self.assertRaisesRegex(reentry.ReentryBundleError, "exact pristine retail"):
            reentry._j2_artifacts(b"not a retail executable", self.base_bundle)


if __name__ == "__main__":
    unittest.main()
