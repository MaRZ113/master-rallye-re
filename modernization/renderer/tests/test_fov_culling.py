import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from inspect_fov_culling import SITES,angle_model,inspect,verify_sites

class SyntheticPE:
    image_base=0x400000
    def __init__(self):
        self.offsets={};self.blob=b''
        for va,_,signature,_ in SITES:
            self.offsets[va-self.image_base]=len(self.blob)
            self.blob+=bytes.fromhex(signature)
    def offset(self,rva,n=1):return self.offsets[rva]

class FovReconTests(unittest.TestCase):
    def test_reject_unknown_before_pe(self):
        with self.assertRaisesRegex(ValueError,'Not pristine retail'):inspect(b'synthetic-not-an-exe')
    def test_pinned_call_targets_and_each_wrong_signature(self):
        pe=SyntheticPE();rows=verify_sites(pe.blob,pe)
        self.assertEqual(rows[-1]['call_target'],'0x00509680')
        self.assertEqual(rows[-1]['expected_bytes'],'e89e63ebff')
        for va,_,_,_ in SITES:
            bad=bytearray(pe.blob);bad[pe.offset(va-0x400000)]^=1
            with self.assertRaisesRegex(ValueError,'Signature mismatch'):verify_sites(bad,pe)
        pe.image_base=0x500000
        with self.assertRaisesRegex(ValueError,'image base'):verify_sites(pe.blob,pe)
    def test_vfov_aspect_and_unsafe_linear_source(self):
        a=angle_model(640,480);b=angle_model(1920,1027);c=angle_model(1920,1027,110)
        self.assertEqual(a['stock_vfov'],67.5);self.assertAlmostEqual(a['linear_source_if_used'],106.66666666667)
        self.assertAlmostEqual(b['linear_source_if_used'],149.5618305745)
        for m in (a,b,c):
            self.assertLess(m['target_hfov'],180)
            self.assertAlmostEqual(math.tan(math.radians(m['target_hfov']/2)),math.tan(math.radians(m['target_vfov']/2))*m['aspect'])
        self.assertFalse(c['linear_source_safe'])
        for args in ((0,480,80),(640,-1,80),(16385,480,80),(640,480,float('nan')),(640,480,111)):
            with self.assertRaises(ValueError):angle_model(*args)
        self.assertEqual(angle_model(480,640)['stock_vfov'],90)
