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


class Slot25ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = synthetic_retail_layout()
        cls.digest = hashlib.sha256(cls.source).hexdigest()
        cls.pe = slot25.parse_pe(cls.source)

    def _candidate(self, profile):
        return slot25.make_candidate(
            self.source,
            expected_sha256=self.digest,
            profile=profile,
        )

    def test_astero_profile_retains_original_stub_and_manifest(self):
        default_bytes, default_manifest = slot25.make_candidate(
            self.source, expected_sha256=self.digest
        )
        profile_bytes, profile_manifest = self._candidate(slot25.ASTERO_PROOF_PROFILE)
        self.assertEqual(profile_bytes, default_bytes)
        self.assertEqual(profile_manifest, default_manifest)
        self.assertNotIn("profile", profile_manifest)

    def test_trooper_name_is_appended_after_return_in_executable_padding(self):
        patched, manifest = self._candidate(slot25.TROOPER_PROFILE)
        literal = manifest["injection"]["name_literal"]
        literal_offset = slot25.va_to_file_offset(
            self.pe, literal["virtual_address"], literal["size"]
        )
        self.assertEqual(literal["storage"], "appended-to-read-only-text-section")
        self.assertEqual(patched[literal_offset:literal_offset + literal["size"]], b"Trooper\0")
        self.assertEqual(
            literal["virtual_address"],
            slot25.STUB_VA + len(slot25.build_stub(slot25.TROOPER_PROFILE, name_literal_va=0)),
        )
        self.assertEqual(manifest["record25"]["name"], "Trooper")

    def test_trooper_profile_keeps_slot_gates_and_original_records(self):
        patched, manifest = self._candidate(slot25.TROOPER_PROFILE)
        astero, _ = self._candidate(slot25.ASTERO_PROOF_PROFILE)
        self.assertNotEqual(patched, astero)
        self.assertEqual(patched[0x58E70:0x598D0], self.source[0x58E70:0x598D0])
        self.assertEqual(manifest["record25"]["id"], 25)
        self.assertEqual(manifest["record25"]["class"], 2)
        self.assertEqual(manifest["record25"]["stats"], [6, 6, 8, 8])
        self.assertIn("Astero ID16 cosmetic donor", manifest["profile"]["stats_source"])
        operations = {item["name"]: item for item in manifest["operations"]}
        self.assertEqual(bytes.fromhex(operations["class2_capacity"]["replacement_bytes"]), b"\x0c")
        self.assertEqual(
            bytes.fromhex(operations["id25_unlock_only"]["replacement_bytes"]),
            b"\xb0\x01\x5e\xc3",
        )

    def test_trooper_smallsheet29_is_deterministic_and_serializes_selector(self):
        base, base_manifest = self._candidate(slot25.TROOPER_PROFILE)
        diagnostic, manifest = self._candidate(slot25.TROOPER_SMALLCARSHEET29_PROFILE)
        rebuilt, rebuilt_manifest = self._candidate(slot25.TROOPER_SMALLCARSHEET29_PROFILE)

        self.assertEqual(slot25.get_profile("trooper").smallcarsheet_index, 0)
        self.assertEqual(slot25.get_profile("trooper-smallsheet29").smallcarsheet_index, 29)
        self.assertEqual(diagnostic, rebuilt)
        self.assertEqual(manifest, rebuilt_manifest)
        self.assertEqual(manifest["phase"], "R5V-E0.1a")
        self.assertEqual(manifest["record25"]["smallcarsheet_index"], 29)
        self.assertEqual(manifest["profile"]["smallcarsheet_index"], 29)
        self.assertEqual(base_manifest["record25"]["meta"], 0)
        self.assertNotIn("smallcarsheet_index", base_manifest["record25"])

        byte_differences = [
            offset for offset, (before, after) in enumerate(zip(base, diagnostic))
            if before != after
        ]
        self.assertEqual(len(byte_differences), 1)
        base_ops = {item["name"]: item for item in base_manifest["operations"]}
        diag_ops = {item["name"]: item for item in manifest["operations"]}
        base_stub = bytes.fromhex(base_ops["slot25_stub"]["replacement_bytes"])
        diag_stub = bytes.fromhex(diag_ops["slot25_stub"]["replacement_bytes"])
        stub_differences = [
            offset for offset, (before, after) in enumerate(zip(base_stub, diag_stub))
            if before != after
        ]
        self.assertEqual(len(stub_differences), 1)
        self.assertEqual(base_stub[stub_differences[0]], 0)
        self.assertEqual(diag_stub[stub_differences[0]], 29)
        self.assertEqual(
            byte_differences[0],
            diag_ops["slot25_stub"]["file_offset"] + stub_differences[0],
        )
        self.assertEqual(
            {name for name in base_ops if name != "slot25_stub"},
            {name for name in diag_ops if name != "slot25_stub"},
        )
        for name in base_ops:
            if name != "slot25_stub":
                self.assertEqual(base_ops[name], diag_ops[name])

    def test_trooper_frontend_stats_diagnostic_changes_only_four_stat_pushes(self):
        base, base_manifest = self._candidate(
            slot25.TROOPER_SMALLCARSHEET29_PROFILE
        )
        diagnostic, manifest = self._candidate(
            slot25.TROOPER_STATS_DIAGNOSTIC_PROFILE
        )
        rebuilt, rebuilt_manifest = self._candidate(
            slot25.TROOPER_STATS_DIAGNOSTIC_PROFILE
        )

        profile = slot25.get_profile("trooper-stats-diag")
        self.assertEqual(
            (profile.frontend_speed, profile.frontend_acceleration,
             profile.frontend_handling, profile.frontend_endurance),
            (3, 4, 6, 10),
        )
        self.assertEqual(diagnostic, rebuilt)
        self.assertEqual(manifest, rebuilt_manifest)
        self.assertEqual(manifest["phase"], "R5V-E0.1b")
        expected_stats = {
            "speed": 3,
            "acceleration": 4,
            "handling": 6,
            "endurance": 10,
        }
        self.assertEqual(manifest["record25"]["frontend_stats"], expected_stats)
        self.assertEqual(manifest["profile"]["frontend_stats"], expected_stats)
        self.assertEqual(manifest["record25"]["smallcarsheet_index"], 29)
        self.assertEqual(manifest["record25"]["name"], "Trooper")
        self.assertEqual(manifest["record25"]["stats"], [3, 4, 6, 10])
        self.assertEqual(base_manifest["record25"]["smallcarsheet_index"], 29)
        self.assertEqual(base_manifest["record25"]["stats"], [6, 6, 8, 8])

        operations = {item["name"]: item for item in manifest["operations"]}
        base_operations = {item["name"]: item for item in base_manifest["operations"]}
        self.assertEqual(set(operations), set(base_operations))
        for name in operations:
            if name != "slot25_stub":
                self.assertEqual(operations[name], base_operations[name])

        base_stub = bytes.fromhex(base_operations["slot25_stub"]["replacement_bytes"])
        diagnostic_stub = bytes.fromhex(operations["slot25_stub"]["replacement_bytes"])
        marker = b"\x6a\x00\x8b\xcc\x68"
        marker_offset = base_stub.index(marker)
        stat_push_immediates = tuple(range(marker_offset + 17, marker_offset + 25, 2))
        self.assertEqual(
            [base_stub[offset] for offset in stat_push_immediates], [8, 8, 6, 6]
        )
        self.assertEqual(
            [diagnostic_stub[offset] for offset in stat_push_immediates],
            [10, 6, 4, 3],
        )
        self.assertTrue(all(base_stub[offset - 1] == 0x6A
                            for offset in stat_push_immediates))

        changed = [
            offset for offset, (before, after) in enumerate(zip(base, diagnostic))
            if before != after
        ]
        stub_offset = operations["slot25_stub"]["file_offset"]
        self.assertEqual(changed, [stub_offset + offset for offset in stat_push_immediates])

    def test_frontend_stat_diagnostic_stays_inside_existing_gradient_frame_range(self):
        self.assertEqual(slot25.FRONTEND_STAT_FRAME_MAX, 10)
        for value in (-1, 11):
            invalid = slot25.replace(
                slot25.TROOPER_PROFILE,
                profile_id=f"bad-stat-{value}",
                stats=(value, 4, 6, 10),
            )
            with self.subTest(value=value), self.assertRaisesRegex(
                    slot25.PatchError, "Frontend stat values must address a retail gradient frame"):
                self._candidate(invalid)

    def test_smallsheet_selector_is_limited_to_existing_retail_frames(self):
        for value in (-1, 30):
            invalid = slot25.replace(
                slot25.TROOPER_PROFILE,
                profile_id=f"bad-selector-{value}",
                smallcarsheet_index=value,
            )
            with self.subTest(value=value), self.assertRaisesRegex(
                    slot25.PatchError, "SmallCarSheet index must address a retail frame"):
                self._candidate(invalid)

    def test_diagnostic_uses_profile_value_in_emitted_stub(self):
        base_stub = slot25.build_stub(slot25.TROOPER_PROFILE)
        diagnostic_stub = slot25.build_stub(slot25.TROOPER_SMALLCARSHEET29_PROFILE)
        changed = [i for i, (a, b) in enumerate(zip(base_stub, diagnostic_stub)) if a != b]
        self.assertEqual(len(changed), 1)
        self.assertEqual(base_stub[changed[0]], 0)
        self.assertEqual(diagnostic_stub[changed[0]], 29)
        self.assertEqual(base_stub[changed[0] - 1], 0x6A)
        self.assertEqual(diagnostic_stub[changed[0] - 1], 0x6A)

    def test_profile_is_confined_to_class2_slot25(self):
        invalid = slot25.VehicleSlotProfile(
            profile_id="bad", slot_id=24, vehicle_class=2, internal_name="Trooper",
            stats=(0, 0, 0, 0), smallcarsheet_index=0, float_bits=(0, 0, 0, 0),
            donor_record_id=None, stats_source="test", floats_source="test",
        )
        with self.assertRaisesRegex(slot25.PatchError, "Only allocated retail slot25"):
            self._candidate(invalid)


if __name__ == "__main__":
    unittest.main()
