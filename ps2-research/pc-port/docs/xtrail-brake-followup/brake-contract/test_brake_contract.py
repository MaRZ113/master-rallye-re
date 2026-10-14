import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

class BrakeContractTests(unittest.TestCase):
    def test_original_dispatch_priority(self):
        evidence = json.loads((HERE / 'mode14-gs-evidence.json').read_text())
        table = {row['mode']: row['original_word'] for row in evidence['dispatch_table']}
        self.assertEqual(table, {0: '0x3126e4', 1: '0x3126e4', 14: '0x31300c'})
        self.assertEqual(evidence['rabbitizer_category'], 'R5900')
        self.assertEqual(evidence['original_instruction_words_verified'], 4623)

    def test_glow_uses_fix_not_source_alpha(self):
        word = 0x8000000029
        self.assertEqual([(word >> shift) & 3 for shift in (0, 2, 4, 6)], [1, 2, 2, 0])
        self.assertEqual((word >> 32) & 255, 128)
        source, destination = 37, 82
        self.assertEqual((destination - 0) * 128 // 128 + source, 119)

    def test_primitive_preserves_higher_inherited_fields(self):
        for inherited in (0, (1 << 54), (1 << 55), (1 << 56), (1 << 57)):
            value = (inherited & 0xffc07fffffffffff) | 0x2e000000000000
            self.assertEqual((value >> 47) & 127, 0x5c)
            self.assertEqual(value & sum(1 << i for i in range(54, 58)), inherited)

    def test_texture_mode_rgba_decal(self):
        value = (0xffffffffffffffff & 0xffffffe3ffffffff) | 0xc00000000
        self.assertEqual((value >> 34) & 1, 1)
        self.assertEqual((value >> 35) & 3, 1)
        self.assertEqual(value & ((1 << 34) - 1), (1 << 34) - 1)

    def test_texture1_mip_and_mtba_remain_inherited(self):
        inherited = (5 << 2) | (1 << 9)
        value = (inherited & 0xfffff000ffe7fe1e) | 0x120
        self.assertEqual((value >> 2) & 7, 5)
        self.assertEqual((value >> 9) & 1, 1)
        self.assertEqual((value >> 5) & 1, 1)
        self.assertEqual((value >> 6) & 7, 4)

    def test_depth_enable_is_inherited(self):
        for inherited in (0, 1 << 16, 1 << 14, (1 << 16) | (1 << 14)):
            value = (inherited & 0xfffffffffff9c000) | 0x41000
            self.assertEqual(value & ((1 << 16) | (1 << 14)), inherited)
            self.assertEqual(value & 1, 0)
            self.assertEqual((value >> 17) & 3, 2)

    def test_depth_write_mask_does_not_replace_base(self):
        inherited = 0x320055
        value = (inherited & 0xfffffffeffffffff) | 0x100000000
        self.assertEqual(value & 0xffffffff, inherited)
        self.assertEqual((value >> 32) & 1, 1)

    def test_pc_matches_threshold_and_bounds(self):
        evidence = json.loads((HERE / 'pc-brake-contract.json').read_text())
        self.assertEqual(evidence['update']['threshold_word'], '0x3dcccccd')
        self.assertEqual(evidence['update']['writer'], '0x4d3c50')
        self.assertEqual(evidence['update']['bounds'], '0x4ca1d0..0x4ca23e')
        self.assertEqual(len(evidence['update_original_byte_windows']), 41)

if __name__ == '__main__':
    unittest.main()
