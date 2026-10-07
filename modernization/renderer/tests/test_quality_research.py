import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from quality_research import (ROOT as TOOL_ROOT, TARGET, read_locked, output_guard,
    instructions, evaluate, signed_bits, capture_audit, FREEZE_CONTEXT, UI_CONTEXT)
from reference_ghidra import PATCHER_SHA
from trace_common import read_jsonl

class QualityResearchTests(unittest.TestCase):
    def test_identity_and_output_guard(self):
        self.assertEqual(ROOT,TOOL_ROOT)
        self.assertEqual(output_guard(ROOT/'research/r-gfx5/result.json'),ROOT/'research/r-gfx5/result.json')
        for outside in [ROOT/'src/result.json', ROOT.parent/'input/result.json']:
            with self.assertRaises(ValueError):output_guard(outside)
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'input';f.write_bytes(b'synthetic')
            self.assertEqual(read_locked(f,hashlib.sha256(b'synthetic').hexdigest()),b'synthetic')
            with self.assertRaises(ValueError):read_locked(f,TARGET)
    def test_cave_evaluator_synthetic_cmp_and_branch(self):
        # cmp [eax+30], 565.0; je positive; jmp neutral. No game bytes needed.
        base=0x1000;code=bytes.fromhex('81783000400d447405e901000000')
        rows=instructions(code,base)
        self.assertEqual(evaluate(rows,565,75,base=base,targets={0x100e:1,0x100f:0}),1)
        self.assertEqual(evaluate(rows,20,75,base=base,targets={0x100e:1,0x100f:0}),0)
    def test_unknown_instruction_and_bounds_fail_closed(self):
        with self.assertRaises(ValueError):instructions(b'\x90',0x1000)
        with self.assertRaises(ValueError):evaluate({0x1000:(2,'jmp',0x1000,0)},1,1,base=0x1000,targets={})
        with self.assertRaises(ValueError):evaluate({},1,1,base=0x1000,targets={})
    def test_capture_present_and_clear_semantics(self):
        rows=[{'type':'frame_begin','exe_sha256':TARGET},
              {'type':'event','method':'Present','arguments':[0]*8},
              {'type':'event','method':'Clear','arguments':[0,0,3,0,0,0,0,0]},
              {'type':'frame_end','complete':True}]
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'fixture.jsonl';f.write_text('\n'.join(map(json.dumps,rows)))
            report=capture_audit(f);self.assertTrue(report['all_present_arguments_null']);self.assertEqual(report['full_color_depth_clears'],1)
            rows[1]['arguments'][0]=1;f.write_text('\n'.join(map(json.dumps,rows)));self.assertFalse(capture_audit(f)['all_present_arguments_null'])
            rows[0]['exe_sha256']='unknown';f.write_text('\n'.join(map(json.dumps,rows)))
            with self.assertRaises(ValueError):capture_audit(f)
    def test_reference_hash_rejected_before_ghidra(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.analysis') as tmp:
            f=Path(tmp)/'synthetic.bin';f.write_bytes(b'not a patcher')
            out=Path(tmp)/'output'
            command=[sys.executable,str(ROOT/'tools/reference_ghidra.py'),'--install',tmp,'--binary',str(f),'--java',tmp,'--output',str(out)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('Not the supplied widescreen reference patcher',result.stderr);self.assertFalse(out.exists())
    def test_curated_rules_match_native_header(self):
        report=json.loads((ROOT/'research/r-gfx5/input-evidence.json').read_text())
        rules=json.loads((ROOT/'research/r-gfx5/margin-rules.json').read_text())['point_rules']
        self.assertEqual(rules,report['reference_cave']['point_rules']);self.assertEqual(len(rules),51)
        header=(ROOT/'include/margin_rules.hpp').read_text()
        native=[[float(x),float(y),int(d)] for x,y,d in re.findall(r'\{(\d+)\.f,(\d+)\.f,(-?1)\}',header)]
        self.assertEqual(native,rules)
        self.assertEqual(report['inputs'][2]['sha256'],PATCHER_SHA)
    def test_pristine_signatures_match_native(self):
        def constants(file,name):
            text=(ROOT/'include'/file).read_text();body=re.search(name+r'\[\]=\{([^}]+)',text).group(1)
            return bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]+)',body))
        self.assertEqual(constants('menu_freeze.hpp','FREEZE_CONTEXT'),FREEZE_CONTEXT)
        report=json.loads((ROOT/'research/r-gfx5/input-evidence.json').read_text());self.assertEqual(bytes.fromhex(report['ui_sort']['context_hex']),UI_CONTEXT)
    def test_native_quality_capture_is_physical_and_virtualized(self):
        release=ROOT/'.build-msvc/Release';exe=release/'quality_tests.exe'
        self.assertTrue(exe.exists(),'Build the native suites first')
        sha=hashlib.sha256(exe.read_bytes()).hexdigest();frames=[]
        for path in (release/'MRRRenderer/logs').glob('frame*.jsonl'):
            with path.open() as f:
                head=json.loads(f.readline())
            if head.get('exe_sha256')==sha and head.get('proxy_version')=='R-GFX5-2':frames.append(read_jsonl(path))
        self.assertTrue(frames,'Native production wrapper must emit its positive capture')
        frame=next(f for f in reversed(frames) if f[0]['quality']['effective']['multisample']==4);self.assertTrue(frame[-1]['complete']);self.assertFalse(frame[-1]['truncated'])
        pp=frame[0]['quality']['effective'];self.assertEqual((pp['width'],pp['height'],pp['multisample'],pp['swap_effect']),(1920,1080,4,1))
        for name in ('physical_backbuffer','physical_depth'):
            surface=frame[0]['quality'][name];self.assertEqual((surface['width'],surface['height'],surface['multisample']),(1920,1080,4))
        draws=[r for r in frame if r.get('type')=='draw'];self.assertEqual(len(draws),2)
        self.assertEqual(draws[0]['state']['viewport'][:4],[0,0,640,480])
        self.assertEqual(draws[0]['effective_state']['viewport'][:4],[0,0,1920,1080])
        self.assertEqual(draws[1]['effective_state']['viewport'][:4],[960,540,960,540])

if __name__=='__main__':unittest.main()
