import hashlib
import os
import pathlib
import struct
import unittest


EXPECTED_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
DEFAULT_EXE = pathlib.Path(r"D:\Game\Master Rallye Pristine\MRallye.exe")


def va_bytes(image: bytes, va: int, size: int) -> bytes:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    opt = pe + 24
    image_base = struct.unpack_from("<I", image, opt + 28)[0]
    assert va >= image_base
    rva = va - image_base
    sections = opt + optional_size
    for i in range(section_count):
        off = sections + i * 40
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from("<IIII", image, off + 8)
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            raw_offset = raw_pointer + rva - virtual_address
            assert raw_offset + size <= raw_pointer + raw_size
            return image[raw_offset:raw_offset + size]
    raise AssertionError(f"VA 0x{va:08x} does not map to a PE section")


class BrokerNullGuardRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = pathlib.Path(os.environ.get("MRR_PRISTINE_EXE", DEFAULT_EXE))
        if not path.is_file():
            raise unittest.SkipTest(f"pristine retail EXE not present: {path}")
        cls.path = path
        cls.image = path.read_bytes()

    def test_exact_retail_identity_and_pe32_i386(self):
        self.assertEqual(len(self.image), 3_121_214)
        self.assertEqual(hashlib.sha256(self.image).hexdigest(), EXPECTED_SHA256)
        pe = struct.unpack_from("<I", self.image, 0x3C)[0]
        self.assertEqual(self.image[pe:pe + 4], b"PE\0\0")
        self.assertEqual(struct.unpack_from("<H", self.image, pe + 4)[0], 0x14C)
        opt = pe + 24
        self.assertEqual(struct.unpack_from("<H", self.image, opt)[0], 0x10B)
        self.assertEqual(struct.unpack_from("<I", self.image, opt + 28)[0], 0x00400000)

    def test_stringlist_context_and_empty_path(self):
        context = va_bytes(self.image, 0x0060201E, 8)
        self.assertEqual(context, bytes.fromhex("8b 7b 04 3b 7b 08 74 1a"))
        self.assertEqual(0x0060201E + 8 + context[7], 0x00602040)
        self.assertEqual(va_bytes(self.image, 0x00602040, 6), bytes.fromhex("8b 15 84 7b 6f 00"))
        self.assertEqual(va_bytes(self.image, 0x00602024, 2), bytes.fromhex("74 1a"))

    def test_xmldata_context_and_both_continuations(self):
        context = va_bytes(self.image, 0x00602153, 13)
        self.assertEqual(context, bytes.fromhex("8b 10 8b c8 ff 52 0c 8b f8 85 ff 74 2e"))
        self.assertEqual(0x00602153 + 11 + 2 + context[12], 0x0060218E)
        self.assertEqual(va_bytes(self.image, 0x0060215A, 6), bytes.fromhex("8b f8 85 ff 74 2e"))
        self.assertEqual(va_bytes(self.image, 0x0060218E, 5), bytes.fromhex("8b 4c 24 0c 51"))


if __name__ == "__main__":
    unittest.main()
