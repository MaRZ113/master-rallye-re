from __future__ import annotations

import hashlib
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import patch_vehicle_registry_id26 as patcher


def retail_layout_fixture() -> bytes:
    """Small deterministic PE layout carrying the retail instruction bytes."""
    pe_offset = 0x80
    image = bytearray(0x2FA000)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, pe_offset)
    image[pe_offset:pe_offset + 4] = b"PE\0\0"
    coff = pe_offset + 4
    struct.pack_into("<HHIIIHH", image, coff, 0x14C, 4, 0, 0, 0, 0xE0, 0x010F)
    optional = coff + 20
    struct.pack_into("<H", image, optional, 0x10B)
    struct.pack_into("<I", image, optional + 28, patcher.IMAGE_BASE)
    struct.pack_into("<II", image, optional + 32, 0x1000, 0x1000)
    struct.pack_into("<I", image, optional + 56, 0x311000)
    section_table = optional + 0xE0
    sections = [
        (b".text", 0x28D294, 0x1000, 0x28E000, 0x1000, 0x60000020),
        (b".rdata", 0x1E432, 0x28F000, 0x1F000, 0x28F000, 0x40000040),
        (b".data", 0x5E608, 0x2AE000, 0x48000, 0x2AE000, 0xC0000040),
        (b".rsrc", 0x3AB8, 0x30D000, 0x4000, 0x2F6000, 0x40000040),
    ]
    for index, (name, virtual_size, rva, raw_size, raw_offset, characteristics) in enumerate(sections):
        header = section_table + index * 40
        image[header:header + len(name)] = name
        struct.pack_into("<IIII", image, header + 8, virtual_size, rva, raw_size, raw_offset)
        struct.pack_into("<I", image, header + 36, characteristics)

    def put(va: int, raw: bytes) -> None:
        offset = 0x1000 + va - 0x401000
        image[offset:offset + len(raw)] = raw

    fixed = {
        0x45A3E0: struct.pack("<I", 0xC00),
        0x458CF4: b"\x1A",
        0x458D12: struct.pack("<I", 0x54C),
        0x458E2C: struct.pack("<I", 0x54C),
        0x458E46: b"\x1A",
        0x686796: b"\x1A",
        0x6867B3: struct.pack("<I", 0x54C),
        0x480A4A: bytes.fromhex("b807000000894620894624"),
        0x480A65: b"\x0B",
        0x481E20: bytes.fromhex("8b411083e800"),
        0x481E50: bytes.fromhex("8b44240456"),
        0x45A282: bytes.fromhex("6a0fe887"),
        0x4819CE: patcher._rel32_call(0x4819CE, 0x45A150),
        0x481ACF: bytes.fromhex("83f8167775"),
        0x4819BD: bytes.fromhex("8bf8e8fc89fdff"),
        0x481A0E: bytes.fromhex("8b10576a338bc8ff520c"),
        0x481A4B: bytes.fromhex("8b10576a348bc8ff520c"),
        0x47A65F: bytes.fromhex("8b10566a338bc8ff520c"),
        0x47A6C4: bytes.fromhex("8b10566a348bc8ff520c"),
        0x44FA29: bytes.fromhex("8b10576a358bc8ff520c"),
        0x481A10: b"\x57",
        0x481A4D: b"\x57",
        0x458D3F: patcher._rel32_call(0x458D3F, patcher.ORIGINAL_SECONDARY_INITIALIZER_VA),
        0x458D10: bytes.fromhex("8d8e4c050000"),
        0x458E2A: bytes.fromhex("8d864c050000"),
        0x6867B2: bytes.fromhex("054c050000"),
    }
    for call_va in patcher.QUICKRACE_SELECTOR_CALLS:
        fixed[call_va] = patcher._rel32_call(call_va, patcher.QUICKRACE_SELECTOR_GETTER_VA)
    for call_va in patcher.QUICKRACE_LOCALIZATION_CALLS:
        fixed[call_va] = bytes.fromhex("506a358bceff570c")
    for va, raw in fixed.items():
        put(va, raw)
    for va, disp in patcher.SECONDARY_INIT_LEAS:
        put(va, b"\x8D\x8E" + struct.pack("<I", disp))
    opcodes = {
        0x449CAD: bytes.fromhex("8b8488"),
        0x45003B: bytes.fromhex("8bb438"),
        0x4500B0: bytes.fromhex("8bbc38"),
        0x45010E: bytes.fromhex("8bbc38"),
        0x45EC29: bytes.fromhex("8b9c38"),
        0x45EC35: bytes.fromhex("8bbc38"),
        0x47B83D: bytes.fromhex("8d8490"),
        0x47ED43: bytes.fromhex("8b8c38"),
        0x47ED53: bytes.fromhex("8bac38"),
        0x47F155: bytes.fromhex("d98438"),
        0x47F1F2: bytes.fromhex("8bbc38"),
    }
    for va, disp in patcher.SECONDARY_CONSUMER_DISPS:
        put(va, opcodes[va] + struct.pack("<I", disp))
    return bytes(image)


class VehicleRegistryId26PatcherTests(unittest.TestCase):
    def test_candidates_accept_dot_research_output_root(self) -> None:
        self.assertTrue(patcher._is_research_output(Path(".research-output/MRallye.exe")))
        self.assertTrue(patcher._is_research_output(Path("research-output/MRallye.exe")))
        self.assertFalse(patcher._is_research_output(Path("output/MRallye.exe")))

    def test_expands_storage_construction_destruction_and_secondary_array(self) -> None:
        source = retail_layout_fixture()
        candidate, manifest = patcher.make_candidate(source, expected_sha256=patcher.sha256(source))

        structural = manifest["structural_self_check"]
        self.assertEqual(structural["registry_capacity"], 27)
        self.assertEqual(structural["registry_object_size"], 0xC34)
        self.assertEqual(structural["record25_offset"], 0x518)
        self.assertEqual(structural["record26_offset"], 0x54C)
        self.assertEqual(structural["racetest"]["new_base"], 0x580)
        self.assertEqual(structural["racetest"]["new_end_exclusive"], 0xC34)
        self.assertEqual(manifest["operation_counts_by_category"]["secondary-array-construction"], 39)
        self.assertEqual(manifest["operation_counts_by_category"]["secondary-array-consumer"], 11)
        self.assertEqual(len(candidate), len(source))

        operation_map = {operation["name"]: operation for operation in manifest["operations"]}
        self.assertEqual(operation_map["construct_vehicle_record_count"]["replacement_bytes"], "1b")
        self.assertEqual(operation_map["destroy_vehicle_record_count"]["replacement_bytes"], "1b")
        self.assertEqual(operation_map["registry_object_allocation"]["replacement_bytes"], "340c0000")
        self.assertEqual(operation_map["construct_racetest_base"]["replacement_bytes"], "80050000")
        self.assertEqual(operation_map["destroy_racetest_base"]["replacement_bytes"], "80050000")

    def test_sparse_mapping_and_donor_profile_are_explicit_and_isolated(self) -> None:
        source = retail_layout_fixture()
        _candidate, manifest = patcher.make_candidate(source, expected_sha256=patcher.sha256(source))
        structural = manifest["structural_self_check"]
        self.assertEqual(structural["class_mappings"]["T1"]["local_7"], 26)
        self.assertEqual(structural["class_mappings"]["T1"]["capacity"], 8)
        self.assertEqual(structural["class_mappings"]["T2"]["capacity"], 7)
        self.assertEqual(structural["class_mappings"]["T3"]["capacity"], 12)
        self.assertEqual(structural["class_mappings"]["reverse_id26"], {"class": 0, "local_index": 7})
        self.assertEqual(structural["id25"]["internal_name"], "Trooper")
        self.assertEqual(structural["id25"]["class"], 2)
        self.assertEqual(structural["id25"]["class_local_index"], 11)
        self.assertEqual(structural["id25"]["smallcarsheet_index"], 29)
        self.assertEqual(structural["id26"]["internal_name"], "Landcruiser")
        self.assertEqual(structural["id26"]["donor_id"], 0)
        self.assertEqual(structural["id26"]["frontend_stats"], [4, 2, 4, 6])
        self.assertEqual(structural["id26"]["smallcarsheet_index"], 9)
        self.assertEqual(structural["id26"]["runtime_family"], "Landcruiser")
        self.assertEqual(structural["id26"]["vehicle_select_icon_frame"], 3)
        self.assertEqual(structural["id26"]["display_selector_by_group"],
                         {"0x33": 0, "0x34": 0, "0x35": 0})
        self.assertEqual(structural["id26"]["race_colour_rgba_bits"],
                         ["3f800000", "00000000", "00000000", "3f800000"])
        payload = bytes.fromhex(next(op["replacement_bytes"] for op in manifest["operations"]
                                     if op["name"] == "id26_code_cave_payload"))
        self.assertIn(b"Trooper\x00Landcruiser\x00", payload)
        self.assertEqual(structural["race_colour_canary"]["id0_record_touched"], False)
        self.assertFalse(any("id0" in op["name"].lower() for op in manifest["operations"]))
        operations = {op["name"]: op for op in manifest["operations"]}
        self.assertEqual(operations["display_group_33_selector"]["original_bytes"], "57")
        self.assertEqual(operations["display_group_33_selector"]["replacement_bytes"], "53")
        self.assertEqual(operations["display_group_34_selector"]["original_bytes"], "57")
        self.assertEqual(operations["display_group_34_selector"]["replacement_bytes"], "53")

    def test_mercedes_cook_harness_changes_only_id26_resource_family(self) -> None:
        source = retail_layout_fixture()
        candidate, manifest = patcher.make_candidate(
            source,
            expected_sha256=patcher.sha256(source),
            id26_profile=patcher.ID26_MERCEDES_COOK_HARNESS,
        )

        structural = manifest["structural_self_check"]
        self.assertEqual(manifest["phase"], "R5V-F.2b isolated retail cook harness")
        self.assertEqual(manifest["runtime_validation"], "NOT RUN — isolated cook trigger only")
        self.assertEqual(structural["registry_capacity"], 27)
        self.assertEqual(structural["class_mappings"]["T1"]["capacity"], 8)
        self.assertEqual(structural["class_mappings"]["T2"]["capacity"], 7)
        self.assertEqual(structural["class_mappings"]["T3"]["capacity"], 12)
        self.assertEqual(structural["id25"]["internal_name"], "Trooper")
        self.assertEqual(structural["id26"]["internal_name"], "Mercedes")
        self.assertEqual(structural["id26"]["runtime_family"], "Mercedes")
        self.assertEqual(structural["id26"]["frontend_stats"], [4, 2, 4, 6])
        self.assertEqual(structural["id26"]["race_colour_rgba_bits"],
                         ["3f800000", "00000000", "00000000", "3f800000"])
        self.assertEqual(structural["race_colour_canary"]["id0_record_touched"], False)
        payload = bytes.fromhex(next(op["replacement_bytes"] for op in manifest["operations"]
                                     if op["name"] == "id26_code_cave_payload"))
        self.assertIn(b"Trooper\x00Mercedes\x00", payload)
        self.assertEqual(len(candidate), len(source))

        # The default F.1 profile and its status label remain unchanged.
        _cleanup_candidate, cleanup_manifest = patcher.make_candidate(
            source, expected_sha256=patcher.sha256(source)
        )
        self.assertEqual(cleanup_manifest["profile"], "donor-cleanup-landcruiser-red-canary")
        self.assertEqual(cleanup_manifest["phase"], "R5V-F.1 cleanup")
        self.assertEqual(cleanup_manifest["runtime_validation"], "WAITING FOR CLEANUP P0")
        cleanup_ops = {op["name"]: op for op in cleanup_manifest["operations"]}
        harness_ops = {op["name"]: op for op in manifest["operations"]}
        self.assertEqual(set(cleanup_ops), set(harness_ops))
        self.assertEqual({name for name in cleanup_ops if cleanup_ops[name] != harness_ops[name]},
                         {"pe_text_virtual_size", "id26_code_cave_payload"})

    def test_mercedes_final_profile_uses_id26_only_historic_display_strings(self) -> None:
        source = retail_layout_fixture()
        candidate, manifest = patcher.make_candidate(
            source,
            expected_sha256=patcher.sha256(source),
            id26_profile=patcher.ID26_MERCEDES_FINAL,
        )
        rebuilt, rebuilt_manifest = patcher.make_candidate(
            source,
            expected_sha256=patcher.sha256(source),
            id26_profile=patcher.ID26_MERCEDES_FINAL,
        )
        self.assertEqual(candidate, rebuilt)
        self.assertEqual(manifest, rebuilt_manifest)
        self.assertEqual(len(manifest["operations"]), 72)
        structural = manifest["structural_self_check"]
        profile = structural["id26"]
        self.assertEqual(manifest["phase"], "R5V-F.2e final Mercedes ML-320 ID26 acceptance candidate")
        self.assertEqual(manifest["runtime_validation"],
                         "STATIC ACCEPTANCE CANDIDATE — WAITING FOR HUMAN P0/P1")
        self.assertEqual(structural["registry_capacity"], 27)
        self.assertEqual(structural["class_mappings"]["T1"], {
            "local_0_to_6": "absolute IDs 0..6", "local_7": 26, "capacity": 8,
        })
        self.assertEqual(structural["class_mappings"]["T2"]["capacity"], 7)
        self.assertEqual(structural["class_mappings"]["T3"]["capacity"], 12)
        self.assertEqual(profile["internal_name"], "Mercedes")
        self.assertEqual(profile["runtime_family"], "Mercedes")
        self.assertEqual(profile["frontend_stats"], [4, 3, 6, 5])
        self.assertEqual(profile["smallcarsheet_index"], 9)
        self.assertEqual(profile["vehicle_select_icon_frame"], 3)
        self.assertEqual(profile["asset_package"], "DataGx/Vehicles/Mercedes")
        self.assertEqual(profile["model_family"], "Mercedes")
        self.assertEqual(profile["wheel_family"], "Mercedes")
        self.assertEqual(profile["physics_family"], "Vehicles/Mercedes")
        self.assertIsNone(profile["donor_id"])
        self.assertEqual(structural["id25"]["internal_name"], "Trooper")
        self.assertEqual(structural["id25"]["id"], 25)
        self.assertEqual(structural["display_selector"]["id26_by_localization_group"], None)
        self.assertEqual(structural["display_selector"]["id26_string_by_context"], {
            "0x33_vehicle_select_manufacturer": "MERCEDES",
            "0x34_vehicle_select_model": "ML-320",
            "0x35_quickrace": "MERCEDES ML-320",
        })
        self.assertEqual(structural["display_selector"]["race_id_unchanged"], 26)
        self.assertEqual(structural["race_colour_canary"]["rgba_bits"],
                         ["3f800000", "00000000", "00000000", "3f800000"])

        operations = {op["name"]: op for op in manifest["operations"]}
        self.assertEqual(operations["vehicle_select_manufacturer_string_override"]["virtual_address"], 0x481A0E)
        self.assertEqual(operations["vehicle_select_model_string_override"]["virtual_address"], 0x481A4B)
        self.assertEqual({operations[name]["virtual_address"] for name in operations
                          if name.startswith("quickrace_name_string_override_")},
                         set(patcher.QUICKRACE_LOCALIZATION_CALLS))
        self.assertNotIn("display_group_33_selector", operations)
        self.assertNotIn("display_group_34_selector", operations)
        self.assertFalse(any(name.startswith("quickrace_group_35_selector_") for name in operations))

        payload = bytes.fromhex(operations["id26_code_cave_payload"]["replacement_bytes"])
        self.assertIn(b"MERCEDES\x00ML-320\x00MERCEDES ML-320\x00", payload)

        # Check both paths in each trampoline against the Ghidra-verified call
        # contract: the non-ID26 route replays the original indirect call,
        # while ID26 returns a code-cave C string and resumes after that call.
        entrypoints = {name: int(value, 16)
                       for name, value in structural["code_entrypoints"].items()}

        def check_literal_and_resume(target: int, expected_text: str, resume: int) -> int:
            target_offset = target - patcher.STUB_VA
            self.assertEqual(payload[target_offset], 0xB8)  # mov eax, imm32
            text_va = struct.unpack_from("<I", payload, target_offset + 1)[0]
            text_offset = text_va - patcher.STUB_VA
            self.assertGreaterEqual(text_offset, 0)
            self.assertLess(text_offset, len(payload))
            self.assertEqual(payload[text_offset:].split(b"\x00", 1)[0].decode("ascii"), expected_text)
            jump_offset = target_offset + 5
            self.assertEqual(payload[jump_offset], 0xE9)
            delta = struct.unpack_from("<i", payload, jump_offset + 1)[0]
            self.assertEqual(patcher.STUB_VA + jump_offset + 5 + delta, resume)
            return text_va

        def check_vehicle_select(name: str, group: int, resume: int, text: str) -> None:
            address = entrypoints[name]
            offset = address - patcher.STUB_VA
            code = payload[offset:]
            self.assertEqual(code[:6], bytes.fromhex("81ff1a000000"))
            self.assertEqual(code[6:8], b"\x0f\x84")
            id26_delta = struct.unpack_from("<i", code, 8)[0]
            id26_target = address + 12 + id26_delta
            self.assertEqual(code[12:22], b"\x8b\x10\x57\x6a" + bytes((group,)) + b"\x8b\xc8\xff\x52\x0c")
            self.assertEqual(code[22], 0xE9)
            other_delta = struct.unpack_from("<i", code, 23)[0]
            self.assertEqual(address + 27 + other_delta, resume)
            check_literal_and_resume(id26_target, text, resume)

        check_vehicle_select("vehicle_select_manufacturer_lookup", 0x33, 0x481A18, "MERCEDES")
        check_vehicle_select("vehicle_select_model_lookup", 0x34, 0x481A55, "ML-320")

        for index, call_va in enumerate(patcher.QUICKRACE_LOCALIZATION_CALLS):
            address = entrypoints[f"quickrace_name_lookup_{index}"]
            offset = address - patcher.STUB_VA
            code = payload[offset:]
            self.assertEqual(code[:5], bytes.fromhex("3d1a000000"))
            self.assertEqual(code[5:7], b"\x0f\x84")
            id26_delta = struct.unpack_from("<i", code, 7)[0]
            id26_target = address + 11 + id26_delta
            self.assertEqual(code[11:19], bytes.fromhex("506a358bceff570c"))
            self.assertEqual(code[19], 0xE9)
            other_delta = struct.unpack_from("<i", code, 20)[0]
            resume = call_va + 8
            self.assertEqual(address + 24 + other_delta, resume)
            check_literal_and_resume(id26_target, "MERCEDES ML-320", resume)

            operation = operations[f"quickrace_name_string_override_{index}"]
            replacement = bytes.fromhex(operation["replacement_bytes"])
            self.assertEqual(len(replacement), 8)
            self.assertEqual(replacement[5:], b"\x90" * 3)
            displacement = struct.unpack_from("<i", replacement, 1)[0]
            entrypoint = int(structural["code_entrypoints"][f"quickrace_name_lookup_{index}"], 16)
            self.assertEqual(call_va + 5 + displacement, entrypoint)
        self.assertEqual(len(candidate), len(source))

    def test_f2f_adds_only_the_two_id26_race_options_string_writers(self) -> None:
        source = retail_layout_fixture()
        candidate, manifest = patcher.make_candidate(
            source,
            expected_sha256=patcher.sha256(source),
            id26_profile=patcher.ID26_MERCEDES_F2F,
        )
        rebuilt, rebuilt_manifest = patcher.make_candidate(
            source,
            expected_sha256=patcher.sha256(source),
            id26_profile=patcher.ID26_MERCEDES_F2F,
        )
        self.assertEqual(candidate, rebuilt)
        self.assertEqual(manifest, rebuilt_manifest)
        self.assertEqual(manifest["phase"],
                         "R5V-F.2f Mercedes Race Options frontend identity candidate")
        self.assertEqual(manifest["runtime_validation"],
                         "STATIC F.2f CANDIDATE — WAITING FOR HUMAN P0 FRONTEND")
        self.assertEqual(len(manifest["operations"]), 74)
        structural = manifest["structural_self_check"]
        self.assertEqual(structural["id26"]["id"], 26)
        self.assertEqual(structural["id26"]["class"], 0)
        self.assertEqual(structural["id26"]["class_local_index"], 7)
        self.assertEqual(structural["id26"]["internal_name"], "Mercedes")
        self.assertEqual(structural["display_selector"]["race_id_unchanged"], 26)
        self.assertEqual(structural["frontend_writer_hooks"]["CurrentManufacturerString"], {
            "writer": "0x0047A540",
            "call_va": "0x0047A65F",
            "group": "0x33",
            "selector_register": "ESI physical Vehicle ID",
            "id26_value": "MERCEDES",
        })
        self.assertEqual(structural["frontend_writer_hooks"]["CurrentVehicleString"], {
            "writer": "0x0047A540",
            "call_va": "0x0047A6C4",
            "group": "0x34",
            "selector_register": "ESI physical Vehicle ID",
            "id26_value": "ML-320",
        })

        operations = {op["name"]: op for op in manifest["operations"]}
        payload = bytes.fromhex(operations["id26_code_cave_payload"]["replacement_bytes"])
        for call_va, group, label, string_label, resume in patcher.RACE_OPTIONS_LOCALIZATION_CALLS:
            op = operations[f"{label}_id26_string_override"]
            self.assertEqual(op["virtual_address"], call_va)
            replacement = bytes.fromhex(op["replacement_bytes"])
            original = bytes.fromhex(op["original_bytes"])
            self.assertEqual(original, bytes.fromhex("8b10566a") + bytes((group,)
                             ) + bytes.fromhex("8bc8ff520c"))
            self.assertEqual(replacement[5:], b"\x90" * 5)
            helper_va = int(structural["code_entrypoints"][label], 16)
            self.assertEqual(call_va + 5 + struct.unpack_from("<i", replacement, 1)[0],
                             helper_va)

            helper = payload[helper_va - patcher.STUB_VA:]
            self.assertEqual(helper[:6], bytes.fromhex("81fe1a000000"))  # compare physical ID in ESI
            self.assertEqual(helper[6:8], bytes.fromhex("0f84"))
            branch_delta = struct.unpack_from("<i", helper, 8)[0]
            id26_branch = helper_va + 12 + branch_delta
            self.assertEqual(helper[12:22], original)  # all other IDs replay the native call
            self.assertEqual(helper[22], 0xE9)
            stock_resume_delta = struct.unpack_from("<i", helper, 23)[0]
            self.assertEqual(helper_va + 27 + stock_resume_delta, resume)
            self.assertEqual(payload[id26_branch - patcher.STUB_VA], 0xB8)  # direct presentation pointer
            literal_va = struct.unpack_from("<I", payload, id26_branch - patcher.STUB_VA + 1)[0]
            expected_text = {"vehicle_select_manufacturer_text": "MERCEDES",
                             "vehicle_select_model_text": "ML-320"}[string_label]
            self.assertEqual(payload[literal_va - patcher.STUB_VA:].split(b"\x00", 1)[0],
                             expected_text.encode("ascii"))
            id26_resume_delta = struct.unpack_from(
                "<i", payload, id26_branch - patcher.STUB_VA + 6)[0]
            self.assertEqual(id26_branch + 10 + id26_resume_delta, resume)

        # The older F.2e profile remains byte-for-byte at its 72-operation scope.
        _f2e, f2e_manifest = patcher.make_candidate(
            source,
            expected_sha256=patcher.sha256(source),
            id26_profile=patcher.ID26_MERCEDES_FINAL,
        )
        self.assertEqual(len(f2e_manifest["operations"]), 72)
        self.assertFalse(any(op["category"] == "race-options-display-string-override"
                             for op in f2e_manifest["operations"]))

    def test_frontend_identity_writer_order_keeps_model_and_manufacturer_split(self) -> None:
        # Deterministic semantic model of the independently verified native
        # writer order; this does not claim to execute the retail frontend.
        def localized_or_id26(group: int, car_id: int) -> str:
            if car_id == 26 and group == 0x33:
                return "MERCEDES"
            if car_id == 26 and group == 0x34:
                return "ML-320"
            if car_id == 26 and group == 0x35:
                return "MERCEDES ML-320"
            return {0x33: "TOMMEK", 0x34: "DIRTBEAST", 0x35: "TOMMEK DIRTBEAST"}[group]

        state = {
            "Frontend/QuickRace/CurrentVehicleString": "TOMMEK DIRTBEAST",
            "Frontend/QuickRace/CurrentManufacturerString": "",
        }
        # Vehicle Select changes CarModel, but the capture shows it does not
        # itself refresh these Quick Race keys.
        selected_car_id = 26
        self.assertEqual(state["Frontend/QuickRace/CurrentVehicleString"], "TOMMEK DIRTBEAST")

        # FUN_0047A540 writes manufacturer via 0x33, then model via 0x34.
        state["Frontend/QuickRace/CurrentManufacturerString"] = localized_or_id26(0x33, selected_car_id)
        state["Frontend/QuickRace/CurrentVehicleString"] = localized_or_id26(0x34, selected_car_id)
        self.assertEqual(state["Frontend/QuickRace/CurrentManufacturerString"], "MERCEDES")
        self.assertEqual(state["Frontend/QuickRace/CurrentVehicleString"], "ML-320")

        # FUN_0047B040 writes the combined group-0x35 name and does not write
        # CurrentManufacturerString; no ID or type identity is changed.
        state["Frontend/QuickRace/CurrentVehicleString"] = localized_or_id26(0x35, selected_car_id)
        self.assertEqual(state["Frontend/QuickRace/CurrentVehicleString"], "MERCEDES ML-320")
        self.assertEqual(state["Frontend/QuickRace/CurrentManufacturerString"], "MERCEDES")
        self.assertEqual(selected_car_id, 26)

        # Stock vehicles continue through their original group-specific values.
        self.assertEqual((localized_or_id26(0x33, 0), localized_or_id26(0x34, 0),
                          localized_or_id26(0x35, 0)),
                         ("TOMMEK", "DIRTBEAST", "TOMMEK DIRTBEAST"))
        self.assertNotEqual(localized_or_id26(0x33, 25), "MERCEDES")
        self.assertNotEqual(localized_or_id26(0x34, 25), "ML-320")

    def test_emitted_capacity_stub_sets_t1_eight_and_t2_seven(self) -> None:
        source = retail_layout_fixture()
        candidate, manifest = patcher.make_candidate(source, expected_sha256=patcher.sha256(source))
        operation = next(op for op in manifest["operations"]
                         if op["name"] == "frontend_independent_t1_t2_capacity")
        replacement = bytes.fromhex(operation["replacement_bytes"])
        self.assertEqual(len(replacement), 11)
        self.assertEqual(replacement[5:], b"\x90" * 6)
        displacement = struct.unpack_from("<i", replacement, 1)[0]
        capacity_helper_va = int(
            manifest["structural_self_check"]["code_entrypoints"]["capacity_init"], 16)
        self.assertEqual(0x480A4A + 5 + displacement, capacity_helper_va)

        payload = bytes.fromhex(next(op["replacement_bytes"] for op in manifest["operations"]
                                     if op["name"] == "id26_code_cave_payload"))
        helper = payload[capacity_helper_va - patcher.STUB_VA:]
        # Decode the exact x86 instructions emitted by the patcher.
        self.assertEqual(helper[:5], bytes.fromhex("b807000000"))  # preserve original EAX=7
        self.assertEqual(helper[5:7], b"\xC7\x46")
        t1_offset = helper[7]
        t1_value = struct.unpack_from("<I", helper, 8)[0]
        self.assertEqual(helper[12:14], b"\xC7\x46")
        t2_offset = helper[14]
        t2_value = struct.unpack_from("<I", helper, 15)[0]
        self.assertEqual((t1_offset, t1_value), (0x20, 8))
        self.assertEqual((t2_offset, t2_value), (0x24, 7))
        jmp_at = 19
        self.assertEqual(helper[jmp_at], 0xE9)
        jump_delta = struct.unpack_from("<i", helper, jmp_at + 1)[0]
        self.assertEqual(capacity_helper_va + jmp_at + 5 + jump_delta,
                         patcher.CAPACITY_INIT_CONTINUATION_VA)
        self.assertEqual(candidate[operation["file_offset"]:
                                   operation["file_offset"] + len(replacement)], replacement)

        memory: dict[int, int] = {}
        memory[t1_offset] = t1_value
        memory[t2_offset] = t2_value
        self.assertEqual(memory, {0x20: 8, 0x24: 7})
        self.assertEqual(manifest["structural_self_check"]["class_mappings"]["T2"]["capacity"], 7)

    def test_quickrace_alias_wrapper_preserves_stdcall_and_only_aliases_id26(self) -> None:
        source = retail_layout_fixture()
        _candidate, manifest = patcher.make_candidate(source, expected_sha256=patcher.sha256(source))
        structural = manifest["structural_self_check"]
        payload = bytes.fromhex(next(op["replacement_bytes"] for op in manifest["operations"]
                                     if op["name"] == "id26_code_cave_payload"))
        helper_va = int(structural["code_entrypoints"]["quickrace_display_selector"], 16)
        helper = payload[helper_va - patcher.STUB_VA:]
        self.assertEqual(helper[:4], bytes.fromhex("ff742404"))  # preserve original arg for nested call
        self.assertEqual(helper[4], 0xE8)
        original_call_delta = struct.unpack_from("<i", helper, 5)[0]
        self.assertEqual(helper_va + 9 + original_call_delta, patcher.QUICKRACE_SELECTOR_GETTER_VA)
        self.assertEqual(helper[9:14], bytes.fromhex("3d1a000000"))
        self.assertEqual(helper[14:16], bytes.fromhex("7502"))
        self.assertEqual(helper[16:18], bytes.fromhex("31c0"))
        self.assertEqual(helper[18:21], b"\xC2\x04\x00")  # same RET 4 cleanup as original getter

        call_ops = [op for op in manifest["operations"]
                    if op["category"] == "quickrace-display-localization"]
        self.assertEqual({op["virtual_address"] for op in call_ops}, set(patcher.QUICKRACE_SELECTOR_CALLS))
        for op in call_ops:
            call_va = op["virtual_address"]
            patch = bytes.fromhex(op["replacement_bytes"])
            self.assertEqual(patch[0], 0xE8)
            delta = struct.unpack_from("<i", patch, 1)[0]
            self.assertEqual(call_va + 5 + delta, helper_va)

        def alias(selector: int) -> int:
            return 0 if selector == 26 else selector

        self.assertEqual(alias(26), 0)
        self.assertEqual(alias(0), 0)
        self.assertEqual(alias(14), 14)

    def test_deterministic_patch_and_no_source_mutation(self) -> None:
        source = retail_layout_fixture()
        before = hashlib.sha256(source).hexdigest()
        first, first_manifest = patcher.make_candidate(source, expected_sha256=before)
        second, second_manifest = patcher.make_candidate(source, expected_sha256=before)
        self.assertEqual(first, second)
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(hashlib.sha256(source).hexdigest(), before)
        self.assertEqual(len(first_manifest["operations"]), 72)
        self.assertEqual(first_manifest["runtime_validation"], "WAITING FOR CLEANUP P0")

    def test_wrong_hash_and_overlap_are_rejected(self) -> None:
        source = retail_layout_fixture()
        with self.assertRaisesRegex(patcher.PatchError, "unsupported retail source SHA256"):
            patcher.make_candidate(source, expected_sha256="0" * 64)

        operation = {"name": "overlap", "file_offset": 0,
                     "original_bytes": "4d5a", "replacement_bytes": "4d5a"}
        with self.assertRaisesRegex(patcher.PatchError, "overlapping"):
            patcher.validate_operations(source, [operation, operation.copy()])


if __name__ == "__main__":
    unittest.main()
