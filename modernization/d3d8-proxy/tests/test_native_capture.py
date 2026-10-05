"""Inspect JSONL emitted by the GPU-free native test, not a game capture."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from trace_common import read_jsonl, annotate, DEFAULT_MAP
from summarize_trace import summarize
import json

class NativeCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files=list((ROOT/'.build-msvc/Release/MRRGFX2/logs').glob('frame-*-d2-*.jsonl'))
        if not files:raise unittest.SkipTest('Run tools/build.py native tests first')
        # Two output frames share PID; choose newest test run only.
        newest=max(files,key=lambda p:p.stat().st_mtime_ns)
        prefix=newest.name.split('-d2-')[0]
        cls.frames=[read_jsonl(p) for p in files if p.name.startswith(prefix+'-d2-')]
    def test_complete_small_capture(self):
        frame=next(f for f in self.frames if not f[-1]['truncated'])
        self.assertTrue(frame[-1]['complete']);self.assertEqual(frame[0]['build'],'UNKNOWN_BUILD')
        draw=next(r for r in frame if r['type']=='draw')
        self.assertEqual(draw['state']['matrices']['2']['values'],[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])
        self.assertIsNone(draw['state']['matrices']['256'])
        self.assertIsNotNone(draw['caller']['module']);self.assertIsNotNone(draw['caller']['return_rva'])
        self.assertEqual(draw['draw_index'],0)
    def test_overflow_is_closed_marked_frame(self):
        frame=next(f for f in self.frames if f[-1]['truncated'])
        self.assertTrue(frame[-1]['complete']);self.assertEqual(frame[-1]['draw_records'],8192)
        self.assertGreater(frame[-1]['dropped_records'],0)
        self.assertEqual(sum(r['type']=='draw' for r in frame),8192)
        self.assertFalse(summarize(frame)['complete_frame'])
    def test_unknown_build_stays_generic(self):
        frame=next(f for f in self.frames if not f[-1]['truncated'])
        out=annotate(frame,json.loads(DEFAULT_MAP.read_text()))
        self.assertTrue(all(not r['annotation']['matched'] for r in out if 'annotation' in r))
    def test_actual_wrapper_return_address(self):
        files=list((ROOT/'.build-msvc/Release/MRRGFX2/logs').glob('frame-*-d1-*.jsonl'))
        if not files:raise unittest.SkipTest('Rebuild native wrapper capture test')
        frame=read_jsonl(max(files,key=lambda p:p.stat().st_mtime_ns))
        draw=next(r for r in frame if r['type']=='draw');caller=draw['caller']
        self.assertEqual(caller['address']-caller['base'],caller['return_rva'])
        self.assertEqual(caller['module'],frame[0]['exe_path'])
        self.assertGreater(caller['return_rva'],0)
        self.assertEqual(draw['result'],0x88761234)
        self.assertEqual(draw['arguments'][:3],[4,0,1])

if __name__=='__main__':unittest.main()
