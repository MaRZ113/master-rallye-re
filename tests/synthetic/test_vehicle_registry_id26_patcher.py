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
        0x4819BD: bytes.fromhex("8bf8e8fc89fdff"),
        0x481A10: b"\x57",
        0x481A4D: b"\x57",
        0x458D3F: patcher._rel32_call(0x458D3F, patcher.ORIGINAL_SECONDARY_INITIALIZER_VA),
        0x458D10: bytes.fromhex("8d8e4c050000"),
        0x458E2A: bytes.fromhex("8d864c050000"),
        0x6867B2: bytes.fromhex("054c050000"),
    }
    for call_va in patcher.QUICKRACE_SELECTOR_CALLS:
        fixed[call_va] = patcher._rel32_call(call_va, patcher.QUICKRACE_SELECTOR_GETTER_VA)
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
