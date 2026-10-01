from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_r5v_e0_1d_2_record_colour as colour


def make_stub() -> bytes:
    stub = bytearray(94)
    stub[:6] = bytes.fromhex("56 8B F1 83 EC 10")
    for (instruction_offset, displacement, immediate_offset), bits in zip(
        colour.STACK_IMMEDIATE_FIELDS, colour.SOURCE_RGBA_BITS
    ):
        stub[instruction_offset:instruction_offset + 4] = bytes(
            (0xC7, 0x44, 0x24, displacement)
        )
        stub[immediate_offset:immediate_offset + 4] = int(bits, 16).to_bytes(4, "little")
    return bytes(stub)


class RecordColourDiagnosticTests(unittest.TestCase):
    def test_changes_only_three_rgb_dwords_and_preserves_alpha(self):
        source = make_stub()
        result, relative_changes = colour.rewrite_tail_stub(source)
        expected_offsets = [
            *range(10, 14), *range(18, 22), *range(26, 30),
        ]
        actual_offsets = [i for i, (a, b) in enumerate(zip(source, result)) if a != b]
        self.assertEqual(actual_offsets, expected_offsets)
        self.assertEqual(relative_changes, expected_offsets)
        self.assertEqual(result[34:38], bytes.fromhex("00 00 80 3F"))
        self.assertEqual(result[:10], source[:10])
        self.assertEqual(result[14:18], source[14:18])
        self.assertEqual(result[22:26], source[22:26])
        self.assertEqual(result[30:], source[30:])

    def test_rejects_unknown_original_colour_bits(self):
        stub = bytearray(make_stub())
        stub[10] ^= 1
        with self.assertRaises(colour.PatchError):
            colour.rewrite_tail_stub(bytes(stub))

    def test_rejects_wrong_stack_destination(self):
        stub = bytearray(make_stub())
        stub[17] = 0x08
        with self.assertRaises(colour.PatchError):
            colour.rewrite_tail_stub(bytes(stub))

    def test_baseline_identity_is_pinned(self):
        self.assertEqual(
            colour.BASELINE_SHA256,
            "e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df",
        )
        self.assertEqual(colour.DIAGNOSTIC_RGBA_BITS,
                         ("3f800000", "00000000", "00000000", "3f800000"))


if __name__ == "__main__":
    unittest.main()
