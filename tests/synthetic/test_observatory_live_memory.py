from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/runtime"))
sys.path.insert(0, str(ROOT / "tools"))
import observatory_compatibility as compat


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "observatory_j1_native_dump_memory.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
RETAIL_SHA = FIXTURE["provenance"]["disk_executable_sha256"]
RETAIL_SIZE = FIXTURE["provenance"]["disk_executable_size"]


class MockProcessMemory:
    """Small bounded address-space fixture; absent ranges behave as RPM failures."""

    def __init__(self, ranges=()):
        self.ranges = [(int(address, 16) if isinstance(address, str) else address, bytes(data))
                       for address, data in ranges]

    def read(self, address: int, size: int) -> bytes:
        for start, data in self.ranges:
            if start <= address and address + size <= start + len(data):
                offset = address - start
                return data[offset:offset + size]
        raise OSError(f"unmapped synthetic process range 0x{address:08X}+{size}")


def j1_memory(*, walker: bytes | None = None, omit_stub: str | None = None,
              mutate_stub: str | None = None) -> MockProcessMemory:
    walker_bytes = bytes.fromhex(walker.hex()) if walker is not None else bytes.fromhex(FIXTURE["walker"]["j1_bytes_hex"])
    rows = [(FIXTURE["walker"]["va"], walker_bytes)]
    for stub in FIXTURE["trampolines"]:
        if stub["name"] == omit_stub:
            continue
        data = bytes.fromhex(stub["bytes_hex"])
        if stub["name"] == mutate_stub:
            data = bytes([data[0] ^ 1]) + data[1:]
        rows.append((stub["va"], data))
    return MockProcessMemory(rows)


def synthetic_pe_image() -> bytes:
    """Minimal bounded PE32 used only for mapped-header identity checks."""
    image = bytearray(0x400)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 0x80)
    image[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHI", image, 0x84, 0x14C, 1, 0x12345678)
    struct.pack_into("<H", image, 0x94, 0xE0)
    opt = 0x98
    struct.pack_into("<H", image, opt, 0x10B)
    struct.pack_into("<I", image, opt + 16, 0x1000)
    struct.pack_into("<I", image, opt + 28, 0x400000)
    struct.pack_into("<I", image, opt + 56, 0x2000)
    section = opt + 0xE0
    image[section:section + 8] = b".text\0\0\0"
    struct.pack_into("<IIII", image, section + 8, 0x100, 0x1000, 0x200, 0x200)
    struct.pack_into("<I", image, section + 36, 0x60000020)
    return bytes(image)


class ObservatoryLiveMemoryTests(unittest.TestCase):
    def setUp(self):
        self.pe = compat.definitions()["retail_pe"]
        self.identity = dict(profile_sha256=RETAIL_SHA, profile_size=RETAIL_SIZE,
                             disk_sha256=RETAIL_SHA, disk_size=RETAIL_SIZE)

    def test_stock_walker_is_accepted_and_results_safety_stays_false(self):
        memory = MockProcessMemory([(FIXTURE["walker"]["va"],
                                     bytes.fromhex(FIXTURE["walker"]["stock_bytes_hex"]))])
        result = compat.classify_native_dump_walker(memory.read, self.pe, **self.identity)
        self.assertEqual(result["variant"], "native_stock")
        self.assertEqual(result["walker_sha256"], FIXTURE["walker"]["stock_sha256"])
        self.assertEqual(result["verified_trampolines"], [])
        self.assertIs(compat.native_dump_post_results_safe(result["variant"]), False)

    def test_exact_j1_walker_and_both_trampolines_are_accepted(self):
        result = compat.classify_native_dump_walker(j1_memory().read, self.pe, **self.identity)
        self.assertEqual(result["variant"], "native-hardened-null-safe-stubs-v1")
        self.assertEqual(result["walker_sha256"], "16d85b7cae971b50f0ad1fd33425bae992cc758c0416c856199eb5ea3dfe2fe9")
        self.assertEqual([row["target_va"] for row in result["verified_trampolines"]],
                         ["0x0068E6D0", "0x0068E6F0"])
        self.assertEqual([row["sha256"] for row in result["verified_trampolines"]],
                         ["1262617fb90ce85e293c226ac947578ec8e844e6c9048f51696205501114a4c5",
                          "247e2d5ea0fd0c7b0c97cbc79247d39bfad7b783c023fe641d6af44a71c85a87"])
        self.assertIs(compat.native_dump_post_results_safe(result["variant"]), True)

    def test_single_byte_walker_change_is_rejected(self):
        walker = bytearray.fromhex(FIXTURE["walker"]["j1_bytes_hex"])
        walker[100] ^= 1
        with self.assertRaisesRegex(ValueError, "neither exact stock"):
            compat.classify_native_dump_walker(j1_memory(walker=bytes(walker)).read,
                                               self.pe, **self.identity)

    def test_changed_trampoline_destination_is_rejected(self):
        walker = bytearray.fromhex(FIXTURE["walker"]["j1_bytes_hex"])
        walker[798 + 1] ^= 1
        with self.assertRaisesRegex(ValueError, "neither exact stock"):
            compat.classify_native_dump_walker(j1_memory(walker=bytes(walker)).read,
                                               self.pe, **self.identity)

    def test_single_byte_trampoline_change_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "neither exact stock"):
            compat.classify_native_dump_walker(j1_memory(mutate_stub="stringlist-null-guard").read,
                                               self.pe, **self.identity)

    def test_missing_unreadable_trampoline_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "neither exact stock"):
            compat.classify_native_dump_walker(j1_memory(omit_stub="xmldata-null-guard").read,
                                               self.pe, **self.identity)

    def test_wrong_or_unknown_executable_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "exact pristine retail"):
            compat.validate_pristine_runtime_identity(RETAIL_SHA, RETAIL_SIZE,
                                                      "0" * 64, RETAIL_SIZE)
        with self.assertRaisesRegex(ValueError, "exact pristine retail"):
            compat.validate_pristine_runtime_identity("1" * 64, RETAIL_SIZE,
                                                      "1" * 64, RETAIL_SIZE)
        with self.assertRaisesRegex(ValueError, "exact pristine retail"):
            compat.classify_native_dump_walker(j1_memory().read, self.pe,
                                               profile_sha256="1" * 64, profile_size=RETAIL_SIZE,
                                               disk_sha256="1" * 64, disk_size=RETAIL_SIZE)

    def test_unrelated_required_broker_anchor_mismatch_is_rejected(self):
        original = b"route-ok"
        anchor = {"name": "broker_editor_dump_route", "rva": 0x1200,
                  "length": len(original), "sha256": hashlib.sha256(original).hexdigest()}
        memory = MockProcessMemory([(0x1200, original)])
        self.assertEqual(compat.verify_runtime_anchor_fingerprints(memory.read, [anchor]),
                         ["broker_editor_dump_route"])
        changed = MockProcessMemory([(0x1200, b"route-no")])
        with self.assertRaisesRegex(ValueError, "broker_editor_dump_route"):
            compat.verify_runtime_anchor_fingerprints(changed.read, [anchor])

    def test_mapped_base_size_and_header_must_match(self):
        image = synthetic_pe_image()
        pe = compat.pe_layout(image)
        span = compat.mapped_header_size(image)
        headers = image[:span]
        self.assertEqual(compat.validate_mapped_image_identity(
            image, headers, pe, pe["image_base"], pe["size_of_image"]), span)
        with self.assertRaisesRegex(ValueError, "base/size"):
            compat.validate_mapped_image_identity(image, headers, pe,
                                                  pe["image_base"] + 0x10000,
                                                  pe["size_of_image"])
        with self.assertRaisesRegex(ValueError, "base/size"):
            compat.validate_mapped_image_identity(image, headers, pe,
                                                  pe["image_base"], pe["size_of_image"] - 1)
        altered = bytearray(headers)
        altered[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "Mapped PE headers"):
            compat.validate_mapped_image_identity(image, bytes(altered), pe,
                                                  pe["image_base"], pe["size_of_image"])

    def test_modified_reference_definition_cannot_retarget_j1_variant(self):
        canonical = copy.deepcopy(compat.definitions())
        walker = next(row for row in canonical["anchors"] if row["name"] == "native_dump_walker")
        variant = next(row for row in walker["semantic_variants"]
                       if row["id"] == "native-hardened-null-safe-stubs-v1")
        variant["hooks"][0]["stub_va"] += 0x100
        with patch.object(compat, "definitions", return_value=canonical):
            with self.assertRaisesRegex(ValueError, "neither exact stock"):
                compat.classify_native_dump_walker(j1_memory().read, self.pe, **self.identity)


if __name__ == "__main__":
    unittest.main()
