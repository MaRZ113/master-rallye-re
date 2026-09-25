"""Synthetic PE tests for the exact retail slot25 patch recipe."""

from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import patch_vehicle_slot25 as slot25  # noqa: E402


def synthetic_retail_layout() -> bytes:
    """A blank synthetic image with the checked PE shape and patch-site bytes."""
    data = bytearray(0x2FA000)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x118)
    data[0x118:0x11C] = b"PE\0\0"
    coff = 0x11C
    struct.pack_into("<HH", data, coff, 0x14C, 4)
    struct.pack_into("<H", data, coff + 16, 0xE0)
    optional = coff + 20
    struct.pack_into("<H", data, optional, 0x10B)
    struct.pack_into("<IIII", data, optional + 28, 0x400000, 0x1000, 0x1000, 0)
    struct.pack_into("<I", data, optional + 56, 0x311000)
    sections = (
        (b".text", 0x28D294, 0x1000, 0x28E000, 0x1000, 0x60000020),
        (b".rdata", 0x1E432, 0x28F000, 0x1F000, 0x28F000, 0x40000040),
        (b".data", 0x5E608, 0x2AE000, 0x48000, 0x2AE000, 0xC0000040),
        (b".rsrc", 0x3AB8, 0x30D000, 0x4000, 0x2F6000, 0x40000040),
    )
    for i, (name, vsize, rva, raw_size, raw_offset, flags) in enumerate(sections):
        sh = 0x210 + i * 40
        struct.pack_into("<8sIIIIIIHHI", data, sh, name, vsize, rva, raw_size,
                         raw_offset, 0, 0, 0, 0, flags)
    data[0x58D3F:0x58D44] = slot25._rel32(slot25.HOOK_VA,
                                          slot25.ORIGINAL_CONTINUATION_CALL_VA)
    data[0x80A65] = 0x0B
    data[0x5A282:0x5A286] = b"\x6A\x0F\xE8\x87"
    data[0x2B3CB4:0x2B3CBB] = b"Astero\0"
    return bytes(data)


class Slot25PatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = synthetic_retail_layout()
        cls.digest = hashlib.sha256(cls.source).hexdigest()

    def _candidate(self, data: bytes | None = None):
        raw = self.source if data is None else data
        return slot25.make_candidate(raw, expected_sha256=hashlib.sha256(raw).hexdigest())

    def test_supported_sha_path_accepts_exact_synthetic_fixture(self):
        patched, manifest = self._candidate()
        self.assertEqual(manifest["source_sha256"], self.digest)
        self.assertEqual(manifest["patched_sha256"], slot25.sha256(patched))

    def test_unsupported_sha_is_rejected(self):
        with self.assertRaisesRegex(slot25.PatchError, "Unsupported source SHA256"):
            slot25.make_candidate(self.source)

    def test_wrong_expected_original_bytes_are_rejected(self):
        bad = bytearray(self.source)
        bad[0x80A65] = 0x0A
        with self.assertRaisesRegex(slot25.PatchError, "Original bytes mismatch"):
            self._candidate(bytes(bad))

    def test_pe_mapping_and_executable_region(self):
        pe = slot25.parse_pe(self.source)
        self.assertEqual(slot25.va_to_file_offset(pe, slot25.HOOK_VA), 0x58D3F)
        self.assertEqual(slot25.va_to_file_offset(pe, slot25.STUB_VA), 0x28E2A0)
        self.assertEqual(pe["sections"][0]["characteristics"] & 0x20000000, 0x20000000)
        self.assertLess(slot25.STUB_VA + len(slot25.build_stub()), 0x68E300)
        with self.assertRaises(slot25.PatchError):
            slot25.va_to_file_offset(pe, 0x800000)

    def test_patch_operations_do_not_overlap(self):
        pe = slot25.parse_pe(self.source)
        operations = slot25.build_operations(self.source, pe)
        slot25.validate_operations(self.source, operations)
        duplicate = dict(operations[1])
        with self.assertRaisesRegex(slot25.PatchError, "Overlapping"):
            slot25.validate_operations(self.source, operations + [duplicate])

    def test_every_difference_is_declared_and_matches_manifest(self):
        patched, manifest = self._candidate()
        self.assertEqual(len(patched), len(self.source))
        allowed = set()
        for op in manifest["operations"]:
            start = op["file_offset"]
            original = bytes.fromhex(op["original_bytes"])
            replacement = bytes.fromhex(op["replacement_bytes"])
            self.assertEqual(self.source[start:start + len(original)], original)
            self.assertEqual(patched[start:start + len(replacement)], replacement)
            allowed.update(range(start, start + len(original)))
            if op["virtual_address"] is not None:
                self.assertEqual(op["virtual_address"] - 0x400000, op["rva"])
        changed = {i for i, (a, b) in enumerate(zip(self.source, patched)) if a != b}
        self.assertTrue(changed)
        self.assertLessEqual(changed, allowed)
        self.assertEqual(self.source[0x58E70:0x598D0], patched[0x58E70:0x598D0])

    def test_deterministic_from_clean_source(self):
        one, manifest1 = self._candidate()
        two, manifest2 = self._candidate()
        self.assertEqual(one, two)
        self.assertEqual(manifest1, manifest2)
        self.assertEqual(self.source, synthetic_retail_layout())

    def test_output_path_must_differ_from_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.exe"
            source.write_bytes(self.source)
            with self.assertRaisesRegex(slot25.PatchError, "must differ"):
                slot25.write_candidate(source, source, Path(folder) / "manifest.json")

    def test_manifest_path_must_not_overwrite_source_or_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.exe"
            output = Path(folder) / "test.exe"
            source.write_bytes(self.source)
            with self.assertRaisesRegex(slot25.PatchError, "Manifest path must differ"):
                slot25.write_candidate(source, output, source)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.exe"
            output = Path(folder) / "test.exe"
            manifest_path = Path(folder) / "manifest.json"
            source.write_bytes(self.source)
            real_make = slot25.make_candidate
            with patch.object(slot25, "make_candidate",
                              side_effect=lambda raw: real_make(raw, expected_sha256=self.digest)):
                manifest = slot25.write_candidate(source, output, manifest_path, dry_run=True)
            self.assertEqual(manifest["source_sha256"], self.digest)
            self.assertFalse(output.exists())
            self.assertFalse(manifest_path.exists())
            self.assertEqual(source.read_bytes(), self.source)

    def test_written_candidate_is_reproducible_and_source_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.exe"
            source.write_bytes(self.source)
            real_make = slot25.make_candidate
            with patch.object(slot25, "make_candidate",
                              side_effect=lambda raw: real_make(raw, expected_sha256=self.digest)):
                first = slot25.write_candidate(source, Path(folder) / "first.exe",
                                               Path(folder) / "first.json")
                second = slot25.write_candidate(source, Path(folder) / "second.exe",
                                                Path(folder) / "second.json")
            self.assertEqual(source.read_bytes(), self.source)
            self.assertEqual((Path(folder) / "first.exe").read_bytes(),
                             (Path(folder) / "second.exe").read_bytes())
            self.assertEqual(first, second)
            self.assertEqual(first["patched_sha256"],
                             slot25.sha256((Path(folder) / "first.exe").read_bytes()))
            with self.assertRaisesRegex(slot25.PatchError, "already exists"):
                slot25.write_candidate(source, Path(folder) / "first.exe",
                                       Path(folder) / "other.json")


    def test_verify_existing_detects_candidate_and_manifest_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.exe"
            output = Path(folder) / "test.exe"
            manifest = Path(folder) / "manifest.json"
            source.write_bytes(self.source)
            real_make = slot25.make_candidate
            with patch.object(slot25, "make_candidate",
                              side_effect=lambda raw: real_make(raw, expected_sha256=self.digest)):
                slot25.write_candidate(source, output, manifest)
                slot25.verify_existing(source, output, manifest)
                original = output.read_bytes()
                bad = bytearray(original)
                bad[0x80A65] ^= 1
                output.write_bytes(bad)
                with self.assertRaisesRegex(slot25.PatchError, "Candidate bytes differ"):
                    slot25.verify_existing(source, output, manifest)
                output.write_bytes(original)
                manifest.write_text("{}", encoding="utf-8")
                with self.assertRaisesRegex(slot25.PatchError, "manifest does not match"):
                    slot25.verify_existing(source, output, manifest)


if __name__ == "__main__":
    unittest.main()