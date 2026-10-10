import re
import struct
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import inspect_legacy_attract as guard

class GuardContracts(unittest.TestCase):
    def test_unknown_image_rejected_without_candidate_output(self):
        for image in (b'',bytes(3121214)):
            with self.assertRaisesRegex(ValueError,'exact pristine'):guard.inspect(image)

    def test_expected_complete_native_instruction_and_success_target(self):
        context=guard.expected_loading();self.assertEqual(len(context),374)
        off=guard.PATCH_RVA-guard.LOADING_RVA
        self.assertEqual(context[off:off+5],bytes.fromhex('68841f6b00'))
        self.assertEqual(guard.PATCH_RVA+5+struct.unpack('<i',guard.REPLACEMENT[1:])[0],guard.SUCCESS_RVA)
        self.assertEqual(context[0xfa:0xfc],bytes.fromhex('752d'))
        self.assertEqual(context[0x104:0x106],bytes.fromhex('7e23'))

    def test_no_overlap_with_existing_native_hooks(self):
        from inspect_camera_scope import SITES
        # Every existing camera/lifecycle anchor range stays outside the five-byte guard.
        for va,_name,code,_target in SITES:
            self.assertFalse(va<0x464f6e and va+len(bytes.fromhex(code))>0x464f69)
        for va in (0x5b015c,0x6532dd,0x56d110):self.assertFalse(0x464f69<=va<0x464f6e)

    def test_shipping_patcher_is_not_the_research_exe_writer(self):
        source=(ROOT/'src/legacy_attract_guard.cpp').read_text()
        self.assertNotIn('CreateFile',source);self.assertNotIn('WriteFile',source)
        self.assertNotIn('Race/AttractMode',source);self.assertNotIn('Race/Type',source)
        self.assertIn('std::call_once',source)
        self.assertIn('Thread32Next',source)
        entry=(ROOT/'src/real_d3d8.cpp').read_text().split('ProxyDirect3DCreate8(UINT sdk){',1)[1]
        self.assertLess(entry.index('install_legacy_attract_guard'),entry.index('ensure()'))

if __name__=='__main__':unittest.main()
