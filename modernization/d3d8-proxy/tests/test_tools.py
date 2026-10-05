import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import generate_interfaces as generation
from verify_proxy import PE, verify, REQUIRED
from trace_common import TARGET_SHA, annotate, read_jsonl, guarded_output
from summarize_trace import summarize
from build import normalized_environment
import ghidra_readonly

def fixture():
    b=bytearray(0x1200)
    def put(at,fmt,*v):struct.pack_into(fmt,b,at,*v)
    b[:2]=b'MZ';put(0x3c,'<I',0x80);b[0x80:0x84]=b'PE\0\0'
    put(0x84,'<HHIIIHH',0x14c,1,0,0,0,224,0x2102)
    opt=0x98;put(opt,'<H',0x10b);put(opt+16,'<I',0x1400);put(opt+28,'<I',0x10000000)
    put(opt+60,'<I',0x200);put(opt+92,'<I',16)
    put(opt+96,'<II',0x1000,0x200);put(opt+104,'<II',0x1300,40)
    sec=opt+224;b[sec:sec+8]=b'.text\0\0\0';put(sec+8,'<IIII',0x1000,0x1000,0x1000,0x200)
    at=0x200;put(at+16,'<IIIIII',2,4,3,0x1040,0x1060,0x1080)
    put(0x240,'<IIII',0x1400,0x1410,0,0x1420)
    put(0x260,'<III',0x10a0,0x10c0,0x10e0);put(0x280,'<HHH',3,0,1)
    for at,name in [(0x2a0,b'Direct3DCreate8'),(0x2c0,b'ValidatePixelShader'),(0x2e0,b'ValidateVertexShader'),(0x580,b'KERNEL32.dll')]:
        b[at:at+len(name)+1]=name+b'\0'
    put(0x500,'<IIIII',0,0,0,0x1380,0)
    return b

class PETests(unittest.TestCase):
    def test_valid(self):
        r=verify(fixture());self.assertTrue(r['valid']);self.assertEqual(r['exports']['Direct3DCreate8']['ordinal'],5)
    def test_x64_rejected(self):
        b=fixture();struct.pack_into('<H',b,0x84,0x8664);self.assertFalse(verify(b)['valid'])
    def test_pe64_rejected(self):
        b=fixture();struct.pack_into('<H',b,0x98,0x20b)
        with self.assertRaises(ValueError):verify(b)
    def test_not_dll(self):
        b=fixture();struct.pack_into('<H',b,0x96,0x102);self.assertFalse(verify(b)['valid'])
    def test_self_import(self):
        b=fixture();b[0x580:0x58d]=b'd3d8.dll\0\0\0\0\0';self.assertFalse(verify(b)['valid'])
    def test_missing_export(self):
        b=fixture();b[0x2a0]=ord('X');self.assertFalse(verify(b)['valid'])
    def test_invalid_ordinal_index(self):
        b=fixture();struct.pack_into('<H',b,0x280,7)
        with self.assertRaises(ValueError):verify(b)
    def test_export_forwarder_rejected(self):
        b=fixture();struct.pack_into('<I',b,0x24c,0x10a0);self.assertFalse(verify(b)['valid'])
    def test_bounds(self):
        for length in (0,10,64,100,500,0x1100):
            with self.assertRaises(ValueError):PE(fixture()[:length])
    def test_delay_import_rejected(self):
        b=fixture();struct.pack_into('<II',b,0x98+96+13*8,0x1400,32);self.assertFalse(verify(b)['valid'])

class InterfaceTests(unittest.TestCase):
    def test_header_manifest(self):
        actual=generation.interfaces((ROOT/'vendor/d3d8/d3d8.h').read_text())
        manifest=json.loads((ROOT/'data/interface-map.json').read_text())['interfaces']
        self.assertEqual(actual,manifest)
        for name,count in [('IDirect3D8',16),('IDirect3DDevice8',97)]:
            self.assertEqual(list(range(count)),[m['slot'] for m in manifest[name]])
            self.assertEqual(len({m['method'] for m in manifest[name]}),count)
            self.assertTrue(all(m['implemented_wrapper'] for m in manifest[name]))
    def test_generation_is_deterministic(self):
        paths=['include/wrappers.hpp','include/method_names.hpp','src/forwarders.cpp','data/interface-map.json','tests/mock_interfaces.hpp']
        before=[(ROOT/p).read_bytes() for p in paths];generation.generate()
        self.assertEqual(before,[(ROOT/p).read_bytes() for p in paths])
    def test_pinned_headers(self):
        manifest=json.loads((ROOT/'data/header-provenance.json').read_text())
        for row in manifest:
            self.assertEqual(hashlib.sha256((ROOT/'vendor/d3d8'/row['file']).read_bytes()).hexdigest(),row['sha256'])
    def test_environment(self):
        self.assertEqual(normalized_environment({'PATH':'a','Path':'b'}),{'PATH':'b'})
    def test_export_manifest(self):
        manifest=json.loads((ROOT/'data/required-exports.json').read_text())
        self.assertEqual({r['name']:r['ordinal'] for r in manifest['exports']},REQUIRED)
        definition=(ROOT/'exports.def').read_text()
        for name,ordinal in REQUIRED.items():
            self.assertRegex(definition,name+r'=\S+\s+@'+str(ordinal))
    def test_ghidra_output_guard(self):
        self.assertEqual(ghidra_readonly.guarded_output(ROOT/'.analysis/test'),ROOT/'.analysis/test')
        with self.assertRaises(ValueError):ghidra_readonly.guarded_output(ROOT.parent/'renderer-recon/.analysis/bad')
    def test_ghidra_wrong_build_before_loading_dependencies(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.analysis') as d:
            binary=Path(d)/'synthetic.bin';binary.write_bytes(b'not the game')
            result=subprocess.run([sys.executable,str(ROOT/'tools/ghidra_readonly.py'),
                '--install',d,'--project',d,'--java',d,'--binary',str(binary),
                '--output',str(Path(d)/'output')],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('Not the pristine retail executable',result.stderr)
            self.assertFalse((Path(d)/'output').exists())

class TraceTests(unittest.TestCase):
    def setUp(self):
        self.callmap=json.loads((ROOT.parent/'renderer-recon/data/d3d8-callmap.json').read_text())
        self.call=next(c for c in self.callmap['calls'] if c['method']=='DrawPrimitive' and int(c['owner'],16)==0x5641c0)
        self.records=[{'type':'frame_begin','exe_sha256':TARGET_SHA,'exe_path':r'D:\Game\MRallye.exe'},
            {'type':'draw','sequence':0,'method':'DrawPrimitive','primitive_count':3,'caller':{'module':r'D:\Game\MRallye.exe','return_rva':int(self.call['return_rva'],16)},'state':{}},
            {'type':'frame_end','complete':True,'truncated':False}]
    def test_return_rva_not_call_rva(self):
        out=annotate(self.records,self.callmap);self.assertTrue(out[1]['annotation']['matched'])
        self.records[1]['caller']['return_rva']=int(self.call['rva'],16)
        self.assertFalse(annotate(self.records,self.callmap)[1]['annotation']['matched'])
    def test_narrow_category(self):
        out=annotate(self.records,self.callmap);self.assertEqual(out[1]['annotation']['category'],'PARTICLE_BILLBOARD')
        self.assertFalse(out[1]['annotation']['semantic_confirmation'])
    def test_unknown_build(self):
        self.records[0]['exe_sha256']='0'*64
        self.assertFalse(annotate(self.records,self.callmap)[1]['annotation']['matched'])
    def test_wrong_map_build(self):
        self.callmap['build_sha256']='0'*64
        self.assertFalse(annotate(self.records,self.callmap)[1]['annotation']['matched'])
    def test_other_module(self):
        self.records[1]['caller']['module']=r'D:\Other\MRallye.exe'
        self.assertFalse(annotate(self.records,self.callmap)[1]['annotation']['matched'])
    def test_unknown_module(self):
        self.records[1]['caller']['module']=None
        self.assertFalse(annotate(self.records,self.callmap)[1]['annotation']['matched'])
    def test_wrong_method(self):
        self.records[1]['method']='DrawPrimitiveUP'
        self.assertFalse(annotate(self.records,self.callmap)[1]['annotation']['matched'])
    def test_complete_zero_vs_unknown(self):
        self.assertEqual(summarize(self.records)['lighting_shader_calls']['SetLight'],0)
        self.records[-1]['truncated']=True
        self.assertIsNone(summarize(self.records)['lighting_shader_calls']['SetLight'])
    def test_incomplete_frame(self):
        self.assertFalse(summarize(self.records[:-1])['complete_frame'])
    def test_reader_json_boundary(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.analysis') as d:
            p=Path(d)/'synthetic.jsonl';p.write_text('{"type":"event"}\n')
            self.assertEqual(len(read_jsonl(p)),1)
            for text in ('{"type":"event"}','{bad}\n','{"v":NaN}\n'):
                p.write_text(text)
                with self.assertRaises((ValueError,json.JSONDecodeError)):read_jsonl(p)
    def test_output_boundary(self):
        with self.assertRaises(ValueError):guarded_output(ROOT.parent/'renderer-recon/findings.md')

if __name__=='__main__':unittest.main()
