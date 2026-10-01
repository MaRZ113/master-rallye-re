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
        0x480A4B: b"\x07\x00\x00\x00",
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
        self.assertEqual(structural["id25"]["smallcarsheet_index"], 29)
        self.assertEqual(structural["id26"]["internal_name"], "Landcruiser")
        self.assertEqual(structural["id26"]["donor_id"], 0)
        self.assertEqual(structural["id26"]["frontend_stats"], [4, 2, 4, 6])
        self.assertEqual(structural["id26"]["smallcarsheet_index"], 9)
        payload = bytes.fromhex(next(op["replacement_bytes"] for op in manifest["operations"]
                                     if op["name"] == "id26_code_cave_payload"))
        self.assertIn(b"Trooper\x00Landcruiser\x00", payload)

    def test_deterministic_patch_and_no_source_mutation(self) -> None:
        source = retail_layout_fixture()
        before = hashlib.sha256(source).hexdigest()
        first, first_manifest = patcher.make_candidate(source, expected_sha256=before)
        second, second_manifest = patcher.make_candidate(source, expected_sha256=before)
        self.assertEqual(first, second)
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(hashlib.sha256(source).hexdigest(), before)
        self.assertEqual(len(first_manifest["operations"]), 69)
        self.assertEqual(first_manifest["runtime_validation"], "WAITING FOR HUMAN P0")

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
