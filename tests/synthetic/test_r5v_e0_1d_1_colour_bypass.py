from contextlib import redirect_stdout
import hashlib
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_r5v_e0_1d_1_override_bypass as bypass


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
    callsite = bypass.va_to_file_offset(pe, 0x4A7659, len(bypass.CALL_SITE_ORIGINAL))
    data[callsite:callsite + len(bypass.CALL_SITE_ORIGINAL)] = bypass.CALL_SITE_ORIGINAL
    return bytes(data)


class AbiCorrectColourBypassTests(unittest.TestCase):
    def setUp(self):
        self.source = make_pe()
        self.source_hash = hashlib.sha256(self.source).hexdigest()
        self.expected_hash = bypass.BASELINE_SHA256
        bypass.BASELINE_SHA256 = self.source_hash

    def tearDown(self):
        bypass.BASELINE_SHA256 = self.expected_hash

    def test_helper_has_ret4_bypass_and_tail_jmp_to_original(self):
        stub = bypass.build_stub()
        self.assertEqual(len(stub), 16)
        self.assertEqual(stub[:11], bytes.fromhex("83 7E 18 00 75 05 33 C0 C2 04 00"))
        self.assertEqual(stub[11], 0xE9)
        self.assertEqual(struct.unpack("b", stub[5:6])[0], 5)
        self.assertEqual(bypass.HELPER_VA + 6 + stub[5], bypass.HELPER_VA + 11)
        displacement = struct.unpack_from("<i", stub, 12)[0]
        self.assertEqual(bypass.HELPER_VA + 16 + displacement, bypass.EXISTS_GETTER_VA)

        # At helper entry ESP points to the CALL return address and ESP+4 to
        # the original PUSH argument. RET 4 consumes both stack words.
        self.assertEqual(stub[8:11], bytes.fromhex("C2 04 00"))
        entry_sp = 0x1000
        bypass_return_sp = entry_sp + 4 + 4
        original_getter_return_sp = entry_sp + 4 + 4
        self.assertEqual(bypass_return_sp, original_getter_return_sp)
        self.assertEqual(bypass_return_sp, entry_sp + 8)

    def test_build_is_deterministic_and_changes_only_approved_ranges(self):
        first, ranges = bypass.build_candidate(self.source)
        second, _ = bypass.build_candidate(self.source)
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(self.source))
        pe = bypass.parse_pe(self.source)
        hook = bypass.va_to_file_offset(pe, bypass.HOOK_VA, 5)
        helper = bypass.va_to_file_offset(pe, bypass.HELPER_VA, bypass.STUB_SIZE)
        self.assertEqual(first[hook:hook + 5], bytes.fromhex("E8 9A 6C 1E 00"))
        self.assertEqual(first[helper:helper + bypass.STUB_SIZE], bypass.build_stub())
        self.assertEqual(first[helper + 11], 0xE9)
        self.assertEqual(first[helper + 8:helper + 11], bytes.fromhex("C2 04 00"))
        self.assertTrue(ranges)
        changed = {i for i, (a, b) in enumerate(zip(self.source, first)) if a != b}
        section = pe["sections"][0]
        allowed = (set(range(hook, hook + 5))
                   | set(range(helper, helper + bypass.STUB_SIZE))
                   | set(range(section["header"] + 8, section["header"] + 12)))
        self.assertTrue(changed <= allowed)
        self.assertEqual(bypass.sha256(self.source), self.source_hash)
        self.assertEqual(bypass._u32(first, section["header"] + 8), bypass.TEXT_VIRTUAL_SIZE_NEW)
        self.assertLess(section["rva"] + bypass.TEXT_VIRTUAL_SIZE_NEW,
                        pe["sections"][1]["rva"])

    def test_manifest_records_abi_hashes_and_exact_diff(self):
        candidate, ranges = bypass.build_candidate(self.source)
        manifest = bypass.make_manifest(
            Path("source.exe"), Path("candidate.exe"), self.source,
            candidate, ranges,
        )
        self.assertEqual(manifest["source_sha256"], self.source_hash)
        self.assertEqual(manifest["output_sha256"], bypass.sha256(candidate))
        self.assertEqual(manifest["paired_xml_red_data_sha256"], bypass.XML_RED_DATA_SHA256)
        self.assertEqual(manifest["operations"][1]["replacement"], bypass.build_stub().hex(" "))
        text_header = bypass.parse_pe(self.source)["sections"][0]["header"]
        self.assertEqual(
            [(item["offset"], item["length"]) for item in manifest["changed_byte_ranges"]],
            [(text_header + 8, 1), (0xA7662, 3), (0x28E300, 3),
             (0x28E304, 6), (0x28E30B, 5)],
        )
        self.assertIn("RET 4", manifest["abi_contract"]["slot_zero"])
        self.assertIn("JMP", manifest["abi_contract"]["other_slots"])

    def test_wrong_hash_callsite_or_nonzero_cave_is_rejected(self):
        with self.assertRaisesRegex(bypass.PatchError, "SHA-256"):
            bypass.build_candidate(self.source[:-1])

        changed_callsite = bytearray(self.source)
        pe = bypass.parse_pe(self.source)
        callsite = bypass.va_to_file_offset(pe, 0x4A7659, len(bypass.CALL_SITE_ORIGINAL))
        changed_callsite[callsite] ^= 1
        bypass.BASELINE_SHA256 = bypass.sha256(changed_callsite)
        with self.assertRaisesRegex(bypass.PatchError, "call-site ABI"):
            bypass.build_candidate(bytes(changed_callsite))

        changed_cave = bytearray(self.source)
        cave = bypass.va_to_file_offset(pe, bypass.HELPER_VA, bypass.STUB_SIZE)
        changed_cave[cave] = 0xCC
        bypass.BASELINE_SHA256 = bypass.sha256(changed_cave)
        with self.assertRaisesRegex(bypass.PatchError, "zero-filled"):
            bypass.build_candidate(bytes(changed_cave))

    def test_rejects_unrecognized_section_layout(self):
        bad_layout = bytearray(self.source)
        pe = bypass.parse_pe(self.source)
        struct.pack_into("<I", bad_layout, pe["sections"][0]["header"] + 8, 0x28D301)
        bypass.BASELINE_SHA256 = hashlib.sha256(bad_layout).hexdigest()
        with self.assertRaisesRegex(bypass.PatchError, "section layout"):
            bypass.build_candidate(bytes(bad_layout))

    def test_path_guard_requires_distinct_paths_and_ignored_output_root(self):
        source = Path("source.exe").resolve()
        outside = Path("outside/candidate.exe").resolve()
        manifest = Path("outside/manifest.json").resolve()
        diff = Path("outside/binary-diff.txt").resolve()
        with self.assertRaisesRegex(bypass.PatchError, "outputs must remain under"):
            bypass.validate_paths(source, outside, manifest, diff)
        with self.assertRaisesRegex(bypass.PatchError, "distinct paths"):
            bypass.validate_paths(source, source, manifest, diff)

    def test_cli_writes_new_outputs_without_overwriting_source(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as scratch:
            scratch_root = Path(scratch)
            source_path = scratch_root / "source.exe"
            source_path.write_bytes(self.source)
            original_bytes = source_path.read_bytes()
            original_hash = bypass.OUTPUT_ROOT
            try:
                bypass.OUTPUT_ROOT = scratch_root
                output_path = scratch_root / "candidate.exe"
                manifest_path = scratch_root / "patch-manifest.json"
                diff_path = scratch_root / "binary-diff.txt"
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(bypass.main([
                        "--source", str(source_path),
                        "--output", str(output_path),
                        "--manifest", str(manifest_path),
                        "--diff", str(diff_path),
                    ]), 0)
                self.assertEqual(source_path.read_bytes(), original_bytes)
                self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(), self.source_hash)
                self.assertTrue(output_path.is_file())
                self.assertTrue(manifest_path.is_file())
                self.assertTrue(diff_path.is_file())
            finally:
                bypass.OUTPUT_ROOT = original_hash


if __name__ == "__main__":
    unittest.main()
