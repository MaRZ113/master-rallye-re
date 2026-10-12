from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

PHASE = Path(__file__).resolve().parents[1]
TOOLS = PHASE / "tools"
sys.path.insert(0, str(TOOLS))

import audit_pilot_runtime as runtime_audit  # noqa: E402
import package_handoff  # noqa: E402
import verify_r5900_revalidation2 as r5900_verify  # noqa: E402


def synthetic_elf(word: int = 0x03C21018) -> bytes:
    image = bytearray(0x104)
    image[:7] = b"\x7fELF\x01\x01\x01"
    struct.pack_into(
        "<HHIIIIIHHHHHH", image, 16,
        2, 8, 1, 0x00100000, 52, 0, 0x20924001,
        52, 32, 1, 40, 0, 0,
    )
    struct.pack_into("<IIIIIIII", image, 52, 1, 0x100, 0x00100000,
                     0x00100000, 4, 4, 7, 0x1000)
    struct.pack_into("<I", image, 0x100, word)
    return bytes(image)


class ElfContractTests(unittest.TestCase):
    def test_elf32_le_and_segment_contract(self) -> None:
        header = r5900_verify.parse_elf32_le(synthetic_elf())
        self.assertEqual(header["class"], 32)
        self.assertEqual(header["endianness"], "little")
        self.assertEqual(header["machine"], 8)
        self.assertEqual(header["entry"], 0x00100000)
        self.assertEqual(header["load_segments"][0]["virtual_address"], 0x00100000)

    def test_va_mapping_uses_file_backed_range_only(self) -> None:
        header = r5900_verify.parse_elf32_le(synthetic_elf())
        self.assertEqual(r5900_verify.va_to_offset(0x00100000, 4, header["load_segments"]), 0x100)
        with self.assertRaisesRegex(ValueError, "maps to 0 file-backed"):
            r5900_verify.va_to_offset(0x00100004, 4, header["load_segments"])

    def test_bad_elf_class_or_endian_fails_closed(self) -> None:
        image = bytearray(synthetic_elf())
        image[4] = 2
        with self.assertRaisesRegex(ValueError, "ELF32 little-endian"):
            r5900_verify.parse_elf32_le(bytes(image))
        image = bytearray(synthetic_elf())
        image[5] = 2
        with self.assertRaisesRegex(ValueError, "ELF32 little-endian"):
            r5900_verify.parse_elf32_le(bytes(image))

    def test_ambiguous_or_non_file_backed_mapping_rejected(self) -> None:
        segment = {
            "virtual_address": 0x1000,
            "file_size": 0x100,
            "file_offset": 0x40,
        }
        with self.assertRaisesRegex(ValueError, "maps to 0"):
            r5900_verify.va_to_offset(0x1100, 4, [segment])
        with self.assertRaisesRegex(ValueError, "maps to 2"):
            r5900_verify.va_to_offset(0x1000, 4, [segment, dict(segment, file_offset=0x80)])


class R5900DecoderTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("rabbitizer"), "Rabbitizer 1.16.2 environment required")
    def test_known_r5900_mult_decodes_three_register_operands(self) -> None:
        import rabbitizer

        ins = rabbitizer.Instruction(0x03C21018, 0x0031D70C, rabbitizer.InstrCategory.R5900)
        self.assertTrue(ins.isValid())
        rendered = str(ins).lower()
        self.assertTrue(rendered.startswith("mult"), rendered)
        self.assertEqual(rendered.count(","), 2, rendered)
        self.assertTrue("$fp" in rendered or "$s8" in rendered, rendered)

    @unittest.skipUnless(importlib.util.find_spec("rabbitizer"), "Rabbitizer 1.16.2 environment required")
    def test_ghidra_listing_bytes_and_header_are_checked(self) -> None:
        import rabbitizer

        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "listing.txt"
            listing.write_text(
                "PROGRAM\tfixture\n"
                "LANGUAGE\tr5900:LE:32:default\n"
                "COMPILER\tdefault\n"
                "BYTE_ORDER\tLE\n"
                "IMAGE_BASE\t00100000\n"
                "INS\t00100000\t1810c203\tmult v0,s8,v0\n",
                encoding="utf-8",
            )
            result = r5900_verify.verify_ghidra_output(
                synthetic_elf(), r5900_verify.parse_elf32_le(synthetic_elf()), listing, rabbitizer
            )
            self.assertEqual(result["instruction_word_count"], 1)
            self.assertEqual(result["source_byte_mismatches"], 0)
            wrong = listing.read_text(encoding="utf-8").replace("1810c203", "00000000")
            listing.write_text(wrong, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "do not match source bytes"):
                r5900_verify.verify_ghidra_output(
                    synthetic_elf(), r5900_verify.parse_elf32_le(synthetic_elf()), listing, rabbitizer
                )


class RuntimeAuditTests(unittest.TestCase):
    def test_jpeg_sof_dimensions_without_external_decoder(self) -> None:
        jpeg = bytes.fromhex("ffd8 ffc0 0011 08 0002 0003 03 011100 021100 031100 ffd9")
        self.assertEqual(runtime_audit.jpeg_dimensions(jpeg), (3, 2))

    def test_session_summary_preserves_mode_and_missing_frame_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session-2.jsonl"
            rows = [
                {"type": "session", "exe_sha256": "exe", "proxy_sha256": "proxy"},
                {"type": "ps2_port_mode_selected", "mode": 2, "mode_name": "alpha_blend_only", "requested_mask": 15},
                {"type": "ps2_port_draw_identity", "identity": "TARGET_IDENTITY_CONFIRMED", "geometry_sha256": "geom", "vertex_generation": 7, "index_generation": 8, "mode": 2, "requested_mask": 15, "applied_mask": 15, "override_applied": True, "pre_draw_restore_ok": True},
                {"type": "capture_written", "path": str(root / "frame-1.jsonl"), "complete_file": True},
            ]
            session.write_text("\n".join(json.dumps(row) for row in rows) + "\n{truncated\n", encoding="utf-8")
            report = runtime_audit.audit_session(session, root)
            self.assertEqual(report["malformed_lines"], 1)
            self.assertEqual(report["selected_mode"]["mode"], 2)
            self.assertEqual(report["target_identity"]["applied_mask"], 15)
            self.assertTrue(report["target_identity"]["pre_draw_restore_ok"])
            self.assertFalse(report["capture_references"][0]["exists_in_supplied_logs_dir"])

    def test_capture_frame_number_uses_terminal_capture_suffix(self) -> None:
        self.assertEqual(runtime_audit.capture_frame_number("frame-39960-d1-00005291.jsonl"), 5291)
        self.assertIsNone(runtime_audit.capture_frame_number("not-a-frame.jsonl"))

    def test_frame_summary_extracts_only_target_draw_and_selected_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frame.jsonl"
            path.write_text("\n".join([
                json.dumps({"type": "frame_summary", "frame": 7608, "primitive_total": 17807}),
                json.dumps({"type": "draw", "method": "DrawIndexedPrimitive", "arguments": [4, 1, 2, 3, 4], "frame": 7608}),
                json.dumps({"type": "native_override", "method": "SetRenderState", "sequence": 9, "arguments": [14, 0], "result": 0, "feature_mask": 128, "native_only": True, "forwarded": True}),
                json.dumps({"type": "draw", "method": "DrawIndexedPrimitive", "arguments": runtime_audit.TARGET_ARGS + [0, 0, 0], "frame": 7608, "draw_index": 45, "sequence": 10, "result": 0, "native_override_applied": False, "state": {"render_states": {"14": 1, "15": 1, "27": 0}}}),
                json.dumps({"type": "native_override", "method": "SetRenderState", "sequence": 11, "arguments": [14, 1], "result": 0, "feature_mask": 128, "native_only": True, "forwarded": True}),
                json.dumps({"type": "frame_end", "frame": 7608, "draw_records": 704, "complete": True, "truncated": False, "dropped_records": 0}),
            ]) + "\n", encoding="utf-8")
            result = runtime_audit.audit_frame(path)
            self.assertEqual(result["frame_draw_count"], 704)
            self.assertEqual(result["frame_primitive_total"], 17807)
            self.assertTrue(result["frame_complete"])
            self.assertEqual(result["target_draw_matches"], 1)
            self.assertEqual(result["target_draw"]["draw_index_zero_based"], 45)
            self.assertEqual(result["target_draw"]["state_snapshot"]["ZWRITEENABLE"], 1)
            self.assertEqual(result["target_draw"]["native_state_events_before"][0]["value"], 0)
            self.assertEqual(result["target_draw"]["native_state_events_after"][0]["value"], 1)
            self.assertTrue(result["target_draw"]["restoration_matches_pre_draw_snapshot"])
            self.assertFalse(result["target_draw"]["native_override_applied_field"])


class FrozenPhaseEvidenceTests(unittest.TestCase):
    def test_four_mode_report_keeps_target_and_state_policies_separate(self) -> None:
        report = json.loads((PHASE / "render-contract.json").read_text(encoding="utf-8"))
        modes = {item["mode"]: item for item in report["pc_pilot13_runtime"]["modes"]}
        self.assertEqual(set(modes), {0, 1, 2, 3})
        self.assertEqual(modes[0]["applied_mask"], "0x00")
        self.assertIn("no ZWRITE write", modes[2]["policy"])
        self.assertIn("no alpha-state write", modes[3]["policy"])
        self.assertEqual(report["pc_pilot13_runtime"]["target_draw"], "DrawIndexedPrimitive(4,11940,28,22944,48,...)")

    def test_runtime_correlation_has_one_same_target_per_mode_frame(self) -> None:
        report = json.loads((PHASE / "runtime-correlation.json").read_text(encoding="utf-8"))
        self.assertEqual(len(report["reference_frames"]), 6)
        for frame in report["reference_frames"][:4]:
            draw = frame["target_draw"]
            self.assertEqual(frame["target_draw_matches"], 1)
            self.assertEqual(draw["draw_index_zero_based"], 45)
            self.assertEqual(draw["result"], 0)
        for frame in report["reference_frames"][1:4]:
            self.assertTrue(frame["target_draw"]["restoration_matches_pre_draw_snapshot"])
        mode2 = report["reference_frames"][2]["target_draw"]
        mode3 = report["reference_frames"][3]["target_draw"]
        self.assertNotIn(14, [row["state_id"] for row in mode2["native_state_events_before"]])
        self.assertEqual([row["state_id"] for row in mode3["native_state_events_before"]], [14])

    def test_probe_file_is_bound_to_canonical_elf_and_has_unique_addresses(self) -> None:
        probes = json.loads((PHASE / "instruction-probes.json").read_text(encoding="utf-8"))
        self.assertEqual(probes["canonical_elf_sha256"], "b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2")
        rows = [row for window in probes["windows"] for row in window["instructions"]]
        self.assertEqual(len(rows), probes["instruction_count"])
        addresses = [row["va"] for row in rows]
        self.assertEqual(len(addresses), len(set(addresses)))

    def test_handoff_archive_is_deterministic_and_contains_only_phase_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = package_handoff.build_archive(root / "one.zip")
            second = package_handoff.build_archive(root / "two.zip")
            self.assertEqual(first["archive_sha256"], second["archive_sha256"])
            import zipfile

            with zipfile.ZipFile(root / "one.zip") as archive:
                names = archive.namelist()
                self.assertIn("PS2-R5900-REVALIDATION2/SHA256SUMS.txt", names)
                self.assertTrue(all(name.startswith("PS2-R5900-REVALIDATION2/") for name in names))
                self.assertFalse(any("SLES_509.06" in name or "TNG.000" in name for name in names))


if __name__ == "__main__":
    unittest.main()
