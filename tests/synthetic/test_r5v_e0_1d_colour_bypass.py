import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_r5v_e0_1d_override_bypass as bypass


def make_pe() -> bytes:
    data = bytearray(0x2FA100)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    coff = 0x84
    struct.pack_into("<HHIIIHH", data, coff, 0x14C, 4, 0, 0, 0, 0xE0, 0x010F)
    optional = coff + 20
    struct.pack_into("<H", data, optional, 0x10B)
    struct.pack_into("<I", data, optional + 28, bypass.IMAGE_BASE)
    struct.pack_into("<I", data, optional + 32, 0x1000)
    struct.pack_into("<I", data, optional + 36, 0x1000)
    struct.pack_into("<I", data, optional + 56, 0x311000)
    table = optional + 0xE0
    sections = [
        (b".text", 0x28D300, 0x1000, 0x28E000, 0x1000, 0x60000020),
        (b".rdata", 0x1E432, 0x28F000, 0x1F000, 0x28F000, 0x40000040),
        (b".data", 0x5E608, 0x2AE000, 0x48000, 0x2AE000, 0xC0000040),
        (b".rsrc", 0x3AB8, 0x2F6000, 0x4000, 0x2F6000, 0x40000040),
    ]
    for index, section in enumerate(sections):
        name, vsize, rva, raw_size, raw_offset, chars = section
        header = table + index * 40
        data[header:header + len(name)] = name
        struct.pack_into("<IIII", data, header + 8, vsize, rva, raw_size, raw_offset)
        struct.pack_into("<I", data, header + 36, chars)
    pe = {"image_base": bypass.IMAGE_BASE, "sections": [
        {"name": name.decode(), "header": table + index * 40, "virtual_size": vsize,
         "rva": rva, "raw_size": raw_size, "raw_offset": raw_offset,
         "characteristics": chars}
        for index, (name, vsize, rva, raw_size, raw_offset, chars) in enumerate(sections)
    ]}
    hook = bypass.va_to_file_offset(pe, bypass.HOOK_VA, len(bypass.HOOK_ORIGINAL))
    data[hook:hook + len(bypass.HOOK_ORIGINAL)] = bypass.HOOK_ORIGINAL
    return bytes(data)


class ColourBypassPatchTests(unittest.TestCase):
    def setUp(self):
        self.source = make_pe()
        self.source_hash = hashlib.sha256(self.source).hexdigest()
        self.expected_hash = bypass.BASELINE_SHA256
        bypass.BASELINE_SHA256 = self.source_hash

    def tearDown(self):
        bypass.BASELINE_SHA256 = self.expected_hash

    def test_build_is_deterministic_and_changes_only_approved_ranges(self):
        first, ranges = bypass.build_candidate(self.source)
        second, _ = bypass.build_candidate(self.source)
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(self.source))
        pe = bypass.parse_pe(self.source)
        hook = bypass.va_to_file_offset(pe, bypass.HOOK_VA, 5)
        stub = bypass.va_to_file_offset(pe, bypass.HELPER_VA, bypass.STUB_SIZE)
        self.assertEqual(first[hook:hook + 5], bypass._rel32_call(bypass.HOOK_VA, bypass.HELPER_VA))
        self.assertEqual(first[stub:stub + bypass.STUB_SIZE][:9], bypass.STUB_PREFIX)
        self.assertEqual(first[stub + bypass.STUB_SIZE - 1], 0xC3)
        self.assertTrue(ranges)
        changed = {i for i, (a, b) in enumerate(zip(self.source, first)) if a != b}
        allowed = (set(range(hook, hook + 5))
                   | set(range(stub, stub + bypass.STUB_SIZE))
                   | set(range(pe["sections"][0]["header"] + 8,
                               pe["sections"][0]["header"] + 12)))
        self.assertTrue(changed <= allowed)
        self.assertEqual(bypass.sha256(self.source), self.source_hash)

    def test_rejects_unrecognized_source_hash(self):
        bypass.BASELINE_SHA256 = "0" * 64
        with self.assertRaisesRegex(bypass.PatchError, "SHA-256"):
            bypass.build_candidate(self.source)

    def test_rejects_modified_hook_or_nonzero_cave(self):
        bad_hook = bytearray(self.source)
        pe = bypass.parse_pe(self.source)
        hook = bypass.va_to_file_offset(pe, bypass.HOOK_VA, 1)
        bad_hook[hook] = 0x90
        bypass.BASELINE_SHA256 = hashlib.sha256(bad_hook).hexdigest()
        with self.assertRaisesRegex(bypass.PatchError, "call bytes"):
            bypass.build_candidate(bytes(bad_hook))

        bad_cave = bytearray(self.source)
        cave = bypass.va_to_file_offset(pe, bypass.HELPER_VA, 1)
        bad_cave[cave] = 0xCC
        bypass.BASELINE_SHA256 = hashlib.sha256(bad_cave).hexdigest()
        with self.assertRaisesRegex(bypass.PatchError, "zero-filled"):
            bypass.build_candidate(bytes(bad_cave))

    def test_rejects_unsupported_section_layout(self):
        bad_layout = bytearray(self.source)
        pe = bypass.parse_pe(self.source)
        struct.pack_into("<I", bad_layout, pe["sections"][0]["header"] + 8, 0x28D301)
        bypass.BASELINE_SHA256 = hashlib.sha256(bad_layout).hexdigest()
        with self.assertRaisesRegex(bypass.PatchError, "section layout"):
            bypass.build_candidate(bytes(bad_layout))

    def test_outputs_must_stay_under_ignored_phase_directory(self):
        source = Path("source.exe").resolve()
        output = Path("outside/candidate.exe").resolve()
        manifest = Path("outside/manifest.json").resolve()
        with self.assertRaisesRegex(bypass.PatchError, "outputs must remain under"):
            bypass.validate_paths(source, output, manifest)


if __name__ == "__main__":
    unittest.main()
