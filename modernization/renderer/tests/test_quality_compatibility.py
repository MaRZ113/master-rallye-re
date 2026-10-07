import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from generate_fingerprints import recipe,TARGET
from audit_quality_runtime import audit
from trace_common import read_jsonl

class SyntheticPE:
    class OPTIONAL_HEADER:ImageBase=0x400000
    def __init__(self,code):self.code=code
    def get_data(self,start,size):return self.code[start:start+size]
    def get_section_by_rva(self,rva):return None

class QualityCompatibilityTests(unittest.TestCase):
    def test_recipe_full_decode_and_reject_unknown_callee(self):
        r=recipe(SyntheticPE(bytes.fromhex('85ff751190')) ,0,5,2,2,True)
        self.assertEqual([i['length'] for i in r['instructions']],[2,2,1])
        self.assertFalse(any(i['relative_call'] for i in r['instructions']))
        with self.assertRaises(ValueError):recipe(SyntheticPE(b'\x0f'),0,1,0,1)
        with self.assertRaises(ValueError):recipe(SyntheticPE(bytes.fromhex('e800000000')),0,5,0,1)
    def test_generator_rejects_unknown_before_writes(self):
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'include/fingerprint_recipes.hpp',ROOT/'research/r-gfx5/fingerprint-recipes.json']}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'synthetic.exe';path.write_bytes(b'unknown')
            result=subprocess.run([sys.executable,str(ROOT/'tools/generate_fingerprints.py'),str(path)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('Not the canonical pristine image',result.stderr)
        for p,sha in before.items():self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),sha)
    def test_ui_recipe_known_owner_and_instruction_normalization(self):
        rows=json.loads((ROOT/'research/r-gfx5/fingerprint-recipes.json').read_text(encoding='utf-8'))
        self.assertEqual(rows['sha256'],TARGET)
        f=rows['features']['WidescreenUI'];self.assertEqual(f['known_rva']+f['target_offset'],0x161ed3)
        self.assertEqual(bytes(f['bytes'][-6:]),bytes.fromhex('ff9094000000'))
        for ins in f['instructions']:
            if ins['relative_call']:
                self.assertEqual(f['bytes'][ins['offset']],0xe8);self.assertEqual(ins['length'],5);self.assertEqual(len(ins['callee_prefix']),12)
    def test_runtime_audit_does_not_invent_visual_pass(self):
        matrix=[0.0]*16;matrix[0]=2/640;matrix[5]=2/480
        bits=list(struct.unpack('<16I',struct.pack('<16f',*matrix)))
        rows=[dict(type='frame_begin',proxy_version='synthetic'),dict(type='event',method='SetTransform',arguments=[3],payload_bits=bits,effective_payload_bits=bits,caller={'return_rva':0x161ed3},feature_mask=0),dict(type='frame_end')]
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'fixture.jsonl';f.write_text('\n'.join(map(json.dumps,rows)),encoding='utf-8')
            r=audit(f);self.assertEqual(r['ui_projection_observations'][0]['return_rva'],0x161ed3);self.assertTrue(r['ui_projection_observations'][0]['requested_equals_effective'])
            self.assertNotIn('visual_pass',r);self.assertEqual(r['successful_resets'],0)
            f.write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):audit(f)
    def test_production_native_ui_capture(self):
        exe=ROOT/'.build-msvc/Release/quality_tests.exe';self.assertTrue(exe.exists())
        sha=hashlib.sha256(exe.read_bytes()).hexdigest();events=[]
        for p in (exe.parent/'MRRRenderer/logs').glob('frame*.jsonl'):
            with p.open(encoding='utf-8') as f:h=json.loads(f.readline())
            if h.get('exe_sha256')==sha and h.get('proxy_version')=='R-GFX5-4':
                rows=read_jsonl(p);events.extend(r for r in rows if r.get('widescreen_applied'))
        self.assertTrue(events,'Run the native production UI setter test first')
        r=next(r for r in events if r.get('widescreen_source')=='validated_ui_projection_owner')
        self.assertNotEqual(r['payload_bits'],r['effective_payload_bits']);self.assertEqual(r['feature_mask']&32,32)
        self.assertAlmostEqual(r['virtual_width'],480*16/9,places=2);self.assertAlmostEqual(r['center_offset'],(480*16/9-640)/2,places=2)

if __name__=='__main__':unittest.main()
