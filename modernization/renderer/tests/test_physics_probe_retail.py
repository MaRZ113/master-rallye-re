import hashlib
import os
from pathlib import Path
import struct
import unittest


RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
RETAIL_SIZE = 3_121_214
IMAGE_BASE = 0x00400000

CONTEXTS = {
    "controller": (0x00443820, bytes.fromhex("56 57 8b f9 8b 4f 14 e8 b4 12 00 00 33 f6")),
    "substep_begin": (0x0043F8A7, bytes.fromhex("8b ce d9 5c 24 0c e8 9e fd ff ff 8b 7c 24 0c")),
    "substep_tail": (0x0043F8DC, bytes.fromhex(
        "57 8b ce e8 1c 03 00 00 8b ce e8 b5 04 00 00 "
        "8b ce e8 0e 05 00 00 4b 75 a6")),
    "route_getter": (0x004CCCA6, bytes.fromhex(
        "8d 46 54 50 e8 11 85 01 00 8b c8 e8 6a 80 01 00")),
    "road_adjust": (0x004CCD2B, bytes.fromhex(
        "8b 4c 24 28 57 51 55 8b ce e8 c7 04 00 00 8b 57 "
        "04 8d 2c c0 c1 e5 03 89 44 24 28 8b 4c 2a 38")),
    "clear_gate": (0x004CCC6D, bytes.fromhex("8b 40 08 c6 40 33 00")),
    "clear_recovery": (0x004CD19E, bytes.fromhex("8b 48 08 c6 41 33 00")),
    "clear_timer": (0x004CD1DB, bytes.fromhex("8b 40 08 88 48 33")),
}

CALLS = {
    "controller": (0x00443827, 0x00444AE0),
    "substep_begin": (0x0043F8AD, 0x0043F650),
    "substep_tail": (0x0043F8ED, 0x0043FE00),
    "route_getter": (0x004CCCB1, 0x004E4D20),
    "road_adjust": (0x004CCD34, 0x004CD200),
}

ROUTE_GETTER_CONTRACT = (
    0x004E4D20,
    bytes.fromhex(
        "8b 44 24 04 8b 10 8b 41 04 85 c0 74 12 8b 49 08 "
        "2b c8 c1 f9 02 3b d1 73 06 8b 04 90 c2 04 00 33 c0 c2 04 00"
    ),
)

ROAD_ADJUST_NATIVE_CONTRACT = {
    "entry": (0x004CD200, bytes.fromhex(
        "83 ec 30 8b 44 24 3c 53 55 8b 6c 24 40 56 8b f1")),
    "callee_cleanup": (0x004CD48B, bytes.fromhex("c2 0c 00")),
}


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def pe_text_map(data):
    if data[:2] != b"MZ":
        raise AssertionError("missing DOS MZ signature")
    pe = u32(data, 0x3C)
    if data[pe:pe + 4] != b"PE\0\0":
        raise AssertionError("missing PE signature")
    if u16(data, pe + 4) != 0x014C:
        raise AssertionError("retail image is not I386")
    section_count = u16(data, pe + 6)
    optional_size = u16(data, pe + 20)
    optional = pe + 24
    if u16(data, optional) != 0x010B:
        raise AssertionError("retail image is not PE32")
    image_base = u32(data, optional + 28)
    section_table = optional + optional_size
    sections = []
    for index in range(section_count):
        offset = section_table + 40 * index
        name = data[offset:offset + 8].split(b"\0", 1)[0].decode("ascii")
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", data, offset + 8)
        sections.append((name, virtual_address, virtual_size, raw_offset, raw_size))
    text = next((s for s in sections if s[0] == ".text"), None)
    if image_base != IMAGE_BASE or text is None:
        raise AssertionError("unexpected image base or missing .text")

    def read_va(va, size):
        rva = va - image_base
        for name, virtual_address, virtual_size, raw_offset, raw_size in sections:
            if name == ".text" and virtual_address <= rva and rva + size <= virtual_address + raw_size:
                file_offset = raw_offset + rva - virtual_address
                return data[file_offset:file_offset + size]
        raise AssertionError(f"VA 0x{va:08X} is not backed by .text bytes")

    return read_va


class ExactRetailPhysicsProbeContexts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = []
        configured = os.environ.get("MR_PRISTINE_EXE")
        if configured:
            candidates.append(Path(configured))
        candidates.append(Path(r"D:\Game\Master Rallye Pristine\MRallye.exe"))
        cls.executable = next((path for path in candidates if path.is_file()), None)
        if cls.executable is None:
            raise unittest.SkipTest("set MR_PRISTINE_EXE to verify contexts against retail .text")
        cls.data = cls.executable.read_bytes()
        cls.read_va = staticmethod(pe_text_map(cls.data))

    def test_exact_pristine_identity(self):
        self.assertEqual(len(self.data), RETAIL_SIZE)
        self.assertEqual(hashlib.sha256(self.data).hexdigest(), RETAIL_SHA256)

    def test_complete_contexts_are_in_retail_text(self):
        for name, (va, expected) in CONTEXTS.items():
            with self.subTest(context=name):
                self.assertEqual(self.read_va(va, len(expected)), expected)

    def test_native_call_targets_are_in_retail_text(self):
        for name, (va, target) in CALLS.items():
            with self.subTest(call=name):
                raw = self.read_va(va, 5)
                self.assertEqual(raw[0], 0xE8)
                displacement = struct.unpack("<i", raw[1:])[0]
                self.assertEqual(va + 5 + displacement, target)

    def test_route_getter_register_and_stack_contract(self):
        va, expected = ROUTE_GETTER_CONTRACT
        self.assertEqual(self.read_va(va, len(expected)), expected)

    def test_stock_recovery_adjustment_register_and_stack_contract(self):
        for name, (va, expected) in ROAD_ADJUST_NATIVE_CONTRACT.items():
            with self.subTest(contract=name):
                self.assertEqual(self.read_va(va, len(expected)), expected)

    def test_complete_single_participant_adjustment_body_and_countdown_contract(self):
        body = self.read_va(0x004CD200, 0x29A)
        digest = hashlib.sha256(body).hexdigest()
        self.assertEqual(digest, "0d81df8f1a1af9de4d10bd3baa2ea8adf703fbe52ad9f8abb503b54c274f2688")
        header = (Path(__file__).parents[1] / "include/physics_probe_model.hpp").read_text()
        self.assertIn(digest, header)
        # count==1 / participant==0 skips self, increments to count and exits;
        # the large initial nearest-distance then chooses the unchanged EBP result.
        contexts = {
            0x004CD262: "3b 7c 24 44 0f 84 b5 00 00 00",
            0x004CD321: "8b 46 14 47 3b f8 0f 8c 35 ff ff ff",
            0x004CD48E: "5f 8b c5 5e 5d 5b 83 c4 30 c2 0c 00",
            0x004CCB67: "8b 46 50 8b 04 38 85 c0",
            0x004CD166: "8b 56 50 c7 04 1a 00 00 00 00",
        }
        for va, text in contexts.items():
            self.assertEqual(self.read_va(va, len(bytes.fromhex(text))), bytes.fromhex(text))

    def test_stock_publication_and_timer_branch_contract(self):
        # Flag is set before (not after) the later matrix copy. Neither the
        # timer helper nor its caller checks that physics consumed the flag.
        contexts = {
            0x004CCFEA: "8b 68 08 8d 46 5c 50 c6 45 33 01 8b 4e 1c 03 cb 51 e8 c0 be 00 00",
            0x004CD11C: "8d 4c 24 54 c7 44 24 60 00 00 00 00 51 8d 4d 34 e8 2f 7d f3 ff",
            0x004CD1D5: "33 c9 3b c1 74 1f 8b 40 08 88 48 33 8b 56 50 39 0c 3a 74 11",
            0x004CCBB9: "8b 4e 50 55 8d 04 39 8b 0c 39 49 89 08 8b 56 44 8b ce "
                        "c7 04 3a 00 00 00 00 e8 d9 05 00 00 8b 46 50 83 3c 38 00 75 09 "
                        "53 55 8b ce e8 a7 00 00 00",
        }
        for va, expected in contexts.items():
            with self.subTest(va=hex(va)):
                raw = bytes.fromhex(expected)
                self.assertEqual(self.read_va(va, len(raw)), raw)

    def test_transaction_production_constants_and_complete_matrix_copy(self):
        # Production's exact context arrays are the source of test expectations.
        import re
        header=(Path(__file__).resolve().parents[1]/"include/physics_probe_model.hpp").read_text()
        sites={"PUBLISH_CONTEXT":0x004CCFF1,"MATRIX_COMPLETE_CONTEXT":0x004CD131,
            "INPUT_FLAG_CONTEXT":0x00591345,"RESTORE_FLAG_CONTEXT":0x004CB62A,
            "RESTORE_CALLEE_CONTEXT":0x004D0580,"MATRIX_COPY_CONTEXT":0x00404E60}
        for name,va in sites.items():
            match=re.search(r"std::array<uint8_t,\s*(\d+)>\s+"+name+r"\s*=\s*\{([^}]+)\}",header)
            self.assertIsNotNone(match)
            expected=bytes(int(n,16) for n in re.findall(r"0x([0-9A-Fa-f]+)",match[2]))
            self.assertEqual(len(expected),int(match[1]))
            self.assertEqual(self.read_va(va,len(expected)),expected)
        self.assertEqual(self.read_va(0x004D0597,3),bytes.fromhex("c2 04 00"))
        self.assertEqual(self.read_va(0x0059133F,12),bytes.fromhex("8b 41 2c 8a 51 78 88 50 33 8b 41 2c"))
        # Unrolled copy writes every destination DWORD +0x00..+0x3C, then ret4.
        copy=bytes.fromhex("8b c1 8b 4c 24 04 8b 11 89 10")
        for offset in range(4,60,4):copy+=bytes([0x8b,0x51,offset,0x89,0x50,offset])
        copy+=bytes.fromhex("8b 49 3c 89 48 3c c2 04 00")
        self.assertEqual(len(copy),103)
        self.assertEqual(self.read_va(0x00404E60,len(copy)),copy)
        raw=self.read_va(0x004CD12C,5)
        self.assertEqual(0x004CD131+struct.unpack("<i",raw[1:])[0],0x00404E60)
        # Additional restore writer's relocated call must retain this exact ret4 target.
        raw=self.read_va(0x004CB62D,5)
        self.assertEqual(0x004CB632+struct.unpack("<i",raw[1:])[0],0x004D0580)


if __name__ == "__main__":
    unittest.main()
