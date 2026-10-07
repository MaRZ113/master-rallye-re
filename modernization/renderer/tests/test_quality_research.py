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
    def current_native_session(self):
        release=ROOT/'.build-msvc/Release'
        sha=hashlib.sha256((release/'quality_tests.exe').read_bytes()).hexdigest()
        matching=[]
        for path in (release/'MRRRenderer/logs').glob('session*.jsonl'):
            with path.open(encoding='utf-8-sig') as f:
                head=json.loads(f.readline())
            if head.get('exe_sha256')==sha and head.get('proxy_version')=='R-GFX5-4':
                matching.append(path)
        self.assertTrue(matching,'Run current native suites before Python')
        # Anchor IDs are session-local. Repeated identical native builds must
        # not merge separate lifetimes just because the executable hash matches.
        latest=max(matching,key=lambda p:(p.stat().st_mtime_ns,p.name))
        return read_jsonl(latest)

    def test_native_windowed_maximize_restore_telemetry(self):
        events=[r for r in self.current_native_session() if r.get('type')=='window_state_transition']
        maximized=[r for r in events if r.get('window_state')=='maximized']
        self.assertGreaterEqual(len(maximized),4)
        for r in maximized:
            self.assertEqual(r['normal_target'],dict(width=1280,height=720))
            self.assertEqual(r['actual_client'],r['effective_backbuffer'])
        triples=[events[i:i+3] for i in range(len(events)-2)]
        self.assertTrue(any([r['window_state'] for r in t]==['normal','maximized','normal'] for t in triples))

    def test_native_consumer_anchor_provenance_preserves_animation(self):
        rows=[r for r in self.current_native_session() if r.get('type')=='ui_packet_lifetime' and r.get('event')=='consume']
        new=next(r for r in rows if r.get('anchor_new') and r.get('engine_x')==565)
        retained=[r for r in rows if r.get('anchor_id')==new['anchor_id'] and r.get('anchor_retained') and r.get('current_rule_match')==0]
        self.assertEqual(new['anchor_source'],'exact_historical_rule')
        self.assertEqual([r['engine_x'] for r in retained],[562,558])
        for r in retained:
            self.assertEqual(r['anchor_direction'],'right')
            self.assertEqual(r['anchor_source'],'retained_identity')
            self.assertAlmostEqual(r['effective_x']-r['engine_x'],new['effective_x']-new['engine_x'],places=3)
        duplicate=next(r for r in rows if r.get('anchor_id')==new['anchor_id'] and r.get('frame')==new['frame'] and not r.get('anchor_new'))
        self.assertFalse(duplicate['shifted']);self.assertEqual(duplicate['effective_x'],new['effective_x'])
        center=next(r for r in rows if r.get('engine_x')==300 and r.get('anchor_direction')=='none')
        self.assertEqual(center['effective_x'],300);self.assertEqual(center['anchor_id'],0)

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
            if head.get('exe_sha256')==sha and head.get('proxy_version')=='R-GFX5-4':frames.append(read_jsonl(path))
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
