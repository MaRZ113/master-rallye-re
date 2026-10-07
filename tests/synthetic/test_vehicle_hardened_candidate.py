from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_vehicle_ai_candidate as ai
import build_vehicle_audio_candidate as audio
import build_vehicle_hardened_candidate as hardened
import patch_vehicle_registry_id26 as registry
from test_vehicle_ai_candidate import synthetic_pristine


def hardened_pristine_fixture() -> bytes:
    """Return the existing retail-layout fixture with exact added hook sites."""
    data = bytearray(synthetic_pristine())
    pe = registry.parse_pe(data)
    originals = (
        (hardened.LOADING_HOOK_VA, hardened.LOADING_ORIGINAL),
        (hardened.STRINGLIST_HOOK_VA, hardened.STRINGLIST_ORIGINAL),
        (hardened.XMLDATA_HOOK_VA, hardened.XMLDATA_ORIGINAL),
        (hardened.RESULTS_NAME_HOOK_VA, hardened.RESULTS_NAME_ORIGINAL),
    )
    for va, expected in originals:
        offset = registry.va_to_file_offset(pe, va, len(expected))
        data[offset:offset + len(expected)] = expected
    for va, stub in (
        (hardened.STRINGLIST_STUB_VA, hardened.stringlist_stub_bytes()),
        (hardened.XMLDATA_STUB_VA, hardened.xmldata_stub_bytes()),
        (hardened.RESULTS_NAME_STUB_VA, hardened.results_name_stub_bytes()),
    ):
        offset = registry.va_to_file_offset(pe, va, len(stub))
        data[offset:offset + len(stub)] = bytes(len(stub))
    return bytes(data)


def composition_hashes(source: bytes) -> tuple[str, str, str]:
    source_sha = hardened.sha256(source)
    g1, _ = registry.make_candidate(
        source,
        expected_sha256=source_sha,
        id26_profile=registry.ID26_MERCEDES_G1_STOCK_UNLOCK,
    )
    g1_sha = hardened.sha256(g1)
    g2, _ = audio.make_candidate(
        source, 0, expected_source_sha256=source_sha,
        expected_g1_sha256=g1_sha,
    )
    return source_sha, g1_sha, hardened.sha256(g2)


def emulate_results_name_stub(stub: bytes, *, car_id: int, driver_id: int) -> tuple[int, int]:
    """Execute the exact emitted selector path for one synthetic competitor."""
    ecx = 0x1000  # current competitor pointer
    memory = {ecx + 4: driver_id, ecx + 8: car_id}
    pushed: list[int] = []
    pc = 0
    while pc < len(stub):
        op = stub[pc:]
        if op.startswith(bytes.fromhex("8B0CAE")):
            ecx = 0x1000  # pointer reload; the synthetic ESI/EBP index is fixed
            pc += 3
        elif op.startswith(bytes.fromhex("8B10")):
            pc += 2  # vtable load is unchanged and not needed for selector result
        elif op.startswith(bytes.fromhex("8B4908")):
            ecx = memory[ecx + 8]
            pc += 3
        elif op.startswith(bytes.fromhex("83F91A")):
            equal = ecx == 26
            pc += 3
        elif op.startswith(bytes.fromhex("7506")):
            if not equal:
                pc += 2 + 6
            else:
                pc += 2
        elif op.startswith(bytes.fromhex("8B4904")):
            ecx = memory[0x1004]
            pc += 3
        elif op.startswith(bytes.fromhex("516A39")):
            pushed.extend((ecx, 0x39))
            pc += 3
        elif op[0] == 0xE9:
            return pushed[0], pushed[1]
        else:
            raise AssertionError(f"unexpected emitted Results opcode at +0x{pc:X}: {op[:8].hex()}")
    raise AssertionError("Results selector stub did not reach its original continuation")


class VehicleHardenedCandidateTests(unittest.TestCase):
    def test_results_selector_uses_driver_only_for_physical_id26(self) -> None:
        stub = hardened.results_name_stub_bytes()
        self.assertEqual(emulate_results_name_stub(stub, car_id=26, driver_id=8), (8, 0x39))
        self.assertEqual(emulate_results_name_stub(stub, car_id=3, driver_id=8), (3, 0x39))
        self.assertEqual(emulate_results_name_stub(stub, car_id=25, driver_id=2), (25, 0x39))

    def test_results_selector_does_not_write_physical_car_id(self) -> None:
        stub = hardened.results_name_stub_bytes()
        self.assertEqual(
            stub[:19],
            bytes.fromhex("8b0cae8b108b490883f91a75068b0cae8b4904"),
        )
        self.assertIn(bytes.fromhex("8B4908"), stub)
        self.assertIn(bytes.fromhex("8B4904"), stub)
        self.assertEqual(hardened.RESULTS_NAME_ORIGINAL.hex(), "8b0cae8b108b4908516a39")

    def test_neutral_stub_targets_preserve_stock_continuations(self) -> None:
        str_stub = hardened.stringlist_stub_bytes()
        xml_stub = hardened.xmldata_stub_bytes()
        str_cleanup = struct.unpack_from("<i", str_stub, 4)[0] + hardened.STRINGLIST_STUB_VA + 8
        xml_cleanup = struct.unpack_from("<i", xml_stub, 4)[0] + hardened.XMLDATA_STUB_VA + 8
        self.assertEqual(str_cleanup, hardened.STRINGLIST_CLEANUP_VA)
        self.assertEqual(xml_cleanup, hardened.XMLDATA_CLEANUP_VA)
        self.assertEqual(str_stub[8:14], hardened.STRINGLIST_ORIGINAL)
        self.assertEqual(xml_stub[8:15], hardened.XMLDATA_ORIGINAL)

    def test_exact_retail_compositions_build_deterministically_without_randomizer(self) -> None:
        source = hardened_pristine_fixture()
        source_sha, g1_sha, g2_sha = composition_hashes(source)
        for profile in hardened.SUPPORTED_PROFILES:
            with self.subTest(profile=profile):
                candidate, manifest = hardened.make_candidate(
                    source,
                    profile,
                    expected_source_sha256=source_sha,
                    expected_g1_sha256=g1_sha,
                    expected_g2_sha256=g2_sha,
                )
                rebuilt, rebuilt_manifest = hardened.make_candidate(
                    source,
                    profile,
                    expected_source_sha256=source_sha,
                    expected_g1_sha256=g1_sha,
                    expected_g2_sha256=g2_sha,
                )
                self.assertEqual(candidate, rebuilt)
                self.assertEqual(manifest, rebuilt_manifest)
                self.assertFalse(manifest["randomizer"]["present"])
                self.assertEqual(
                    manifest["forced_ai_proof"]["included"],
                    profile == hardened.PROFILE_FORCED,
                )
                self.assertTrue(manifest["hardening"]["null_stringlist_dump_guard"])
                self.assertTrue(manifest["hardening"]["null_xmldata_dump_guard"])
                self.assertEqual(manifest["file_size"], len(source))

    def test_wrong_retail_hash_fails_closed(self) -> None:
        with self.assertRaisesRegex(hardened.CandidateError, "unsupported pristine retail SHA256"):
            hardened.make_candidate(b"unknown", hardened.PROFILE_ORDINARY)

    def test_randomizer_profile_is_not_an_accepted_candidate_profile(self) -> None:
        with self.assertRaisesRegex(hardened.CandidateError, "unsupported hardened profile"):
            hardened.make_candidate(hardened_pristine_fixture(), "mixed-randomizer")


if __name__ == "__main__":
    unittest.main()
