import struct,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'tools'),str(Path(__file__).resolve().parents[2]/'src')]
from gt3_audio_inspect import events
from vehicle_turbo_source import synthesize_spool,synthesize_bov
from master_rallye.addon_sdk.audio_profile import decode_pcm


class SourceTests(unittest.TestCase):
    def test_named_opaque_event(self):
        raw=b'GTSE'+struct.pack('<5I',1,0,1,24,0x01010010)+b'turbine\0'
        self.assertEqual(events(raw),[{'name':'turbine','token':'0x01010010','record_offset':16}])

    def test_reject_pointer(self):
        with self.assertRaises(ValueError):events(b'GTSE'+struct.pack('<5I',1,0,1,16,0)+b'x\0')

    def test_reject_duplicate(self):
        with self.assertRaises(ValueError):events(b'GTSE'+struct.pack('<7I',1,0,2,32,1,32,2)+b'x\0')

    def test_sources_deterministic_and_bounded(self):
        for factory,frames in ((synthesize_spool,48000),(synthesize_bov,16800)):
            raw=factory();self.assertEqual(raw,factory());values,fmt=decode_pcm(raw)
            self.assertEqual(len(values),frames);self.assertEqual(fmt['sample_rate'],48000)
            self.assertLess(max(map(abs,values)),15000);self.assertGreater(max(map(abs,values)),1000)

    def test_spool_loop_join_and_bov_release(self):
        values,_=decode_pcm(synthesize_spool());self.assertLess(abs(values[-1]-values[0]),3000)
        values,_=decode_pcm(synthesize_bov());self.assertEqual(values[0],0)
        self.assertLess(max(map(abs,values[-480:])),64)


if __name__=='__main__':unittest.main()
