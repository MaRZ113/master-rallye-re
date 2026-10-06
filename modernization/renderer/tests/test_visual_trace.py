import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from summarize_visual_trace import effective_state,summarize,projection

def capture_executable(path):
    with path.open(encoding='utf-8') as stream:
        return json.loads(stream.readline())['exe_path'].casefold()

class VisualTraceTests(unittest.TestCase):
    def fixture(self):
        m=[1.12245429,0,0,0,0,1.49660575,0,0,0,0,1.00020003,1,0,0,-.200040013,0]
        return {'type':'draw','draw_index':0,'method':'DrawPrimitive','state':{'texture_stage_states':[{'16':2,'17':2,'18':1,'21':1},{}],'matrices':{'3':{'values':m}}}}
    def test_legacy_r_gfx2(self):
        d=self.fixture();self.assertEqual(effective_state(d),d['state'])
    def test_overlay(self):
        d=self.fixture();d['effective_state']={'inherits_logical':True,'stage0':{'17':3,'21':8}}
        e=effective_state(d);self.assertEqual(e['texture_stage_states'][0]['17'],3);self.assertEqual(d['state']['texture_stage_states'][0]['17'],2)
        self.assertEqual(e['texture_stage_states'][1],{})
    def test_unknown_overlay(self):
        d=self.fixture();d['effective_state']={'inherits_logical':False}
        with self.assertRaises(ValueError):effective_state(d)
    def test_projection(self):
        d=self.fixture();self.assertAlmostEqual(projection(d['state']['matrices']['3'])['vfov'],67.5,places=5)
    def test_ortho(self):
        m=[2/640,0,0,0,0,2/480,0,0,0,0,.001,0,-1,-1,0,1]
        self.assertEqual(projection({'values':m})['logical_height'],480)
    def test_stock_no_modification(self):
        self.assertEqual(summarize([{'type':'frame_begin'},self.fixture(),{'type':'frame_end','complete':True,'truncated':False}])['modified_draws'],[])
    def test_suppression_recorded(self):
        d=self.fixture();d['forwarded']=False;d['feature_mask']=4
        r=summarize([{},d,{'type':'frame_end','complete':True,'truncated':False}]);self.assertEqual(r['suppressed_draws'],1);self.assertEqual(r['visual_runtime_pass'],'PENDING_HUMAN')
    def test_actual_visual_wrapper_trace(self):
        root=Path(__file__).resolve().parents[1]
        files=[p for p in (root/'.build-msvc/Release/MRRRenderer/logs').glob('frame-*-d1-*.jsonl') if capture_executable(p).endswith('visual_tests.exe')]
        if not files:self.skipTest('Run native visual_contracts first')
        from trace_common import read_jsonl
        r=summarize(read_jsonl(max(files,key=lambda p:p.stat().st_mtime_ns)))
        self.assertTrue(r['complete']);self.assertTrue(r['modified_draws']);self.assertEqual(r['modified_draws'][0]['differences']['stage0.17'],{'requested':2,'effective':3})

if __name__=='__main__':unittest.main()
