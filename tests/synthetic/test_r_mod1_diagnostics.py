from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import decode_r_mod1_crash as crash_decoder
from build_r_mod1_candidate import diagnostic_profile


class RMod1DiagnosticTests(unittest.TestCase):
    def test_av_record_decodes_exact_registers_parameters_and_setup_phase(self) -> None:
        information = [0, 0xDEADBEEF] + [0] * 13
        context = [0x0047B780, 0x0012F000, 0x0012F100, 0xC0000005,
                   0x11111111, 0x22222222, 0x33333333, 0x44444444,
                   0x55555555, 0x202]
        start = [6, 3, 3, 10, 2, 0, 0, 0, 0]
        stack = [0x0047B785, 0x70001754] + [0] * 30
        frames = [0x0012F100, 0x70001754] + [0] * 30
        payload = crash_decoder.RECORD.pack(
            crash_decoder.MAGIC, crash_decoder.RECORD.size, 1, 100, 101,
            3, 0xC0000005, 0, 0x0047B780, 2,
            *information, *context, *start, *stack, *frames,
        )
        self.assertEqual(len(payload), 436)
        row = crash_decoder.decode_bytes(payload)[0]
        self.assertEqual(row["kind"], "access_violation_unhandled")
        self.assertEqual(row["exception_information"], [0, 0xDEADBEEF])
        self.assertEqual(row["eip"], 0x0047B780)
        self.assertEqual(row["ecx"], 0x22222222)
        self.assertEqual(row["start_phase_name"], "prepared_validation_entered")
        self.assertEqual(row["opponent_count"], 3)
        self.assertEqual(row["stack_words"][:2], [0x0047B785, 0x70001754])
        self.assertEqual(row["frames"], [{"ebp": 0x0012F100, "return_address": 0x70001754}])

    def test_decoder_rejects_partial_or_unknown_records(self) -> None:
        with self.assertRaisesRegex(ValueError, "truncated"):
            crash_decoder.decode_bytes(b"RMCRASH1")
        bad = bytearray(crash_decoder.RECORD.size)
        with self.assertRaisesRegex(ValueError, "signature/size"):
            crash_decoder.decode_bytes(bytes(bad))

    def test_numeric_diagnostic_profiles_isolate_features_and_keep_race_count_at_three(self) -> None:
        cases = {
            "stock": (False, False, 3),
            "randomizer": (True, False, 3),
            "opponent": (False, True, 3),
            "both": (True, True, 3),
        }
        for label, args in cases.items():
            with self.subTest(label=label):
                content = diagnostic_profile(*args)
                self.assertIn("[Logging]\nEnabled = 1", content)
                self.assertIn("MaxOpponents = 3", content)
                self.assertIn("[Experimental]\nExtendedAI = 0", content)
                self.assertIn("Duplicates = 1", content)
                self.assertIn("Include = 0", content)
                self.assertEqual("Enabled = 1" in content.split("[Opponents]")[0].split("[Randomizer]")[1],
                                 args[0])
                opponents_section = content.split("[Opponents]")[1].split("[Addons]")[0]
                self.assertEqual("Enabled = 1" in opponents_section, args[1])
        menu = diagnostic_profile(False, True, 7, quick_race=0)
        self.assertIn("MaxOpponents = 7", menu)
        self.assertIn("Enabled = 1", menu.split("[Opponents]")[1].split("[Addons]")[0])
        both = diagnostic_profile(True, True, 3, quick_race=2)
        self.assertIn("Enabled = 1\nQuickRace = 2", both)
        self.assertIn("[Opponents]\nEnabled = 1\nMaxOpponents = 3", both)
        four = diagnostic_profile(True, True, 4, quick_race=2)
        self.assertIn("MaxOpponents = 4", four)
        self.assertIn("ExtendedAI = 0", four)
        experimental = diagnostic_profile(True, True, 4, quick_race=2,
                                          experimental_extended_ai=True)
        self.assertIn("[Experimental]\nExtendedAI = 1", experimental)
        self.assertIn("[Randomizer]\nEnabled = 1\nQuickRace = 2", experimental)
        self.assertIn("[Opponents]\nEnabled = 1\nMaxOpponents = 4", experimental)
        with self.assertRaisesRegex(ValueError, "1..7"):
            diagnostic_profile(False, True, 8)
        with self.assertRaisesRegex(ValueError, "0..6"):
            diagnostic_profile(True, False, 3, quick_race=7)


if __name__ == "__main__":
    unittest.main()
