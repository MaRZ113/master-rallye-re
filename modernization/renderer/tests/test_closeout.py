import json
import tempfile
import math
import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from summarize_closeout import source_angle, session_counts, digest, EXE, PRE_FIX

class CloseoutTests(unittest.TestCase):
    def test_counts(self):
        rows = [{'type':'frame_summary','present_hresult':0,'bypass_suspected':False},
                {'type':'frame_summary','present_hresult':1,'bypass_suspected':True},
                {'type':'reset','hresult':0,'parameters_after':{'width':640,'height':480}},
                {'type':'reset','hresult':1,'parameters_after':{'width':640,'height':480}}]
        r = session_counts(rows)
        self.assertEqual((r['summaries'],r['present_failures'],r['bypass_suspected'],r['reset_success'],r['reset_failures']), (2,1,1,1,1))
    def test_source_families(self):
        for aspect in (640/480,1920/1027,.75):
            for angle in (45,90):
                y = 1/math.tan(math.radians(angle/max(1,aspect))/2)
                floats = [y/aspect,0,0,0,0,y,0,0,0,0,1.0002,1,0,0,-.2,0]
                bits = struct.unpack('<16I', struct.pack('<16f',*floats))
                self.assertAlmostEqual(source_angle(bits)['source_angle'],angle,places=5)
    def test_invalid_matrix(self):
        self.assertIsNone(source_angle([]))
        self.assertIsNone(source_angle([0]*16))

    def test_digest_exact_identity_and_broker_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);logs = root/'logs';brokers = root/'brokers';logs.mkdir();brokers.mkdir()
            header = {'type':'session','exe_sha256':EXE,'proxy_sha256':PRE_FIX}
            good = json.dumps(header)+'\n'+json.dumps({'type':'frame_summary','present_hresult':0,'bypass_suspected':False})+'\n'
            (logs/'session-good.jsonl').write_text(good)
            header['exe_sha256'] = 'unknown'
            (logs/'session-unknown.jsonl').write_text(json.dumps(header)+'\n')
            (brokers/'test-gfx3.json').write_text(json.dumps({'entries':[{'path':'Camera/Setup','continuation_lines':['<root><Value Name="No Follow Cameras" Value="3"/></root>']}]}))
            first = digest(logs,brokers)
            self.assertEqual(first,digest(logs,brokers))
            self.assertEqual(len(first['sessions']),1)
            self.assertEqual(first['sessions'][0]['summaries'],1)
            self.assertEqual(first['broker_camera_setup'][0]['values']['No Follow Cameras'],'3')
            self.assertEqual(len(first['sessions'][0]['sha256']),64)
