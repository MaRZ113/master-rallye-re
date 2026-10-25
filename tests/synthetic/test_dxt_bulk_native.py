"""Generated pixel fixtures; optional user-local exact retail CPU instruction oracle."""
import importlib.util,unittest
from pathlib import Path
from tools.vehicle_dxt_bulk_native import append_dxt_bulk,compile_helper,SITE
from tools.native_audio_coff import link_object
from tools.validate_vehicle_dxt_bulk_native import validate

EXE=Path(__file__).resolve().parents[3]/'corpora/retail/MRallye.exe'


@unittest.skipUnless(EXE.is_file() and importlib.util.find_spec('unicorn'),'local original EXE/Unicorn oracle unavailable')
class DxtBulkNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.exe=EXE.read_bytes()

    def test_original_equivalence_fallback_and_failure_cleanup(self):
        report=validate(self.exe);self.assertEqual(len(report['cases']),12);self.assertFalse(report['runtime_qualified'])

    def test_deterministic_helper_and_prefix(self):
        first=link_object(compile_helper()[0],0x10000000)[0];second=link_object(compile_helper()[0],0x10000000)[0];self.assertEqual(first,second)
        prefix=b'EXISTING_PAYLOAD!';image,blob,report=append_dxt_bulk(self.exe,self.exe,prefix,0x10000000,65536)
        self.assertEqual(blob[:len(prefix)],prefix);self.assertEqual(len(report['operations']),1)
        changed=[i for i,(a,b) in enumerate(zip(self.exe,image)) if a!=b];offset=report['operations'][0]['file_offset'];self.assertTrue(all(offset<=i<offset+5 for i in changed))

    def test_preimage_and_storage_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'unqualified'):append_dxt_bulk(b'X'+self.exe[1:],self.exe,b'',0x10000000,65536)
        image,_,_=append_dxt_bulk(self.exe,self.exe,b'',0x10000000,65536)
        with self.assertRaisesRegex(ValueError,'preimage'):append_dxt_bulk(self.exe,image,b'',0x10000000,65536)
        with self.assertRaisesRegex(ValueError,'exceeds'):append_dxt_bulk(self.exe,self.exe,b'',0x10000000,1)
