"""Synthetic SDK/diagnostic regressions; these are never runtime acceptance."""
from pathlib import Path
import importlib.util,json,tempfile,unittest,subprocess,sys

TOOLS=Path(__file__).resolve().parents[1]/'tools'
def module(name):
    spec=importlib.util.spec_from_file_location(name,TOOLS/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
coverage=module('course_lighting_coverage')

def admission(frame=101):
    return dict(type='course_admission',frame=frame,material='testpanel',texture_sha256='a'*64,admission='Lit candidate',reason='synthetic',category=4,fvf=322,vertex_generation=8,index_generation=9,texture_generation=3,min_index=10,vertices=3,start_index=9,triangles=1)
def draw(hr=0):
    return dict(type='draw',method='DrawIndexedPrimitive',caller={'return_rva':0x17707e},arguments=[4,10,3,9,1,0,0,0],result=hr,state={'vertex_shader':322,'streams':[{'last_creation_serial':8}],'indices':{'last_creation_serial':9},'render_states':{'7':1,'28':1},'matrices':{'2':{'bits':[0]*16},'3':{'bits':[0]*16}}})
class CoverageTests(unittest.TestCase):
    def test_missing_and_failed_draws_are_never_lit(self):
        self.assertEqual(coverage.join_admissions([admission()],[])[0]['runtime_verdict'],'Unconfirmed')
        self.assertEqual(coverage.join_admissions([admission()],[draw(1)])[0]['runtime_verdict'],'Draw failed')
    def test_generation_mismatch_cannot_borrow_success(self):
        d=draw();d['state']['streams'][0]['last_creation_serial']=99
        self.assertEqual(coverage.join_admissions([admission()],[d])[0]['runtime_verdict'],'Unconfirmed')
    def test_duplicate_draw_keys_are_consumed_once(self):
        rows=coverage.join_admissions([admission(),admission()],[draw()])
        self.assertEqual([r['runtime_verdict'] for r in rows],['Lit','Unconfirmed'])
    def test_native_png_roundtrip_and_invalid_signature(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.png';coverage.write_rgb(p,2,1,b'\x01\x02\x03\x04\x05\x06')
            self.assertEqual(coverage.rgb_png(p),(2,1,b'\x01\x02\x03\x04\x05\x06'))
            p.write_bytes(b'invalid')
            with self.assertRaises(ValueError):coverage.rgb_png(p)
    def fixture(self,root,mode):
        pair=root/'pair';logs=root/'logs';pair.mkdir();logs.mkdir()
        meta=dict(status='CAPTURED_MATCHED_CAMERA_RUNTIME_TRACE_JOIN_REQUIRED',camera_equal_by_bits=True,lit_frame=101,native_frame=102,pid=1,device=1,proxy_sha256='f'*64,course='RaceTest/Test')
        (pair/'pair.json').write_text(json.dumps(meta));(pair/'admissions.jsonl').write_text('\n'.join(json.dumps(admission(f)) for f in [101,102]))
        for frame in [101,102]:
            rows=[dict(type='frame_begin',proxy_sha256='e'*64 if mode=='dll' else 'f'*64),draw(),dict(type='frame_summary',complete_interval=mode!='incomplete',present_hresult=0),dict(type='frame_end',complete=True,truncated=False)]
            if mode=='camera' and frame==102:rows[1]['state']['matrices']['2']['bits'][0]=1
            (logs/f'frame-1-d1-{frame:08}.jsonl').write_text('\n'.join(json.dumps(x) for x in rows))
        return pair,logs
    def test_incomplete_identity_or_camera_mismatch_does_not_certify_pair(self):
        for mode in ['dll','camera','incomplete']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                root=Path(d);pair,logs=self.fixture(root,mode);report=coverage.analyze(pair,logs,root/'report')
                self.assertEqual(report['status'],'UNCONFIRMED');self.assertNotIn('Lit',report['counts'])
    def test_scene_identity_comes_from_xml_not_folder_spelling(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);scene=root/'FranceS1.xml'
            scene.write_text('<Scene><Egg><Value Name="en3d Model Name" Value="course\\france_s1\\frances1"/><Value Name="en3d Matrix" Row0="1 0 0 0" Row1="0 1 0 0" Row2="0 0 1 0" Row3="0 0 0 1"/></Egg></Scene>')
            code="import runpy,sys,pathlib,json; m=runpy.run_path(sys.argv[1]); print(json.dumps(m['scene_references'](pathlib.Path(sys.argv[2]),{'france_s1':'France_S1'},{'France_S1':{'frances1'}})))"
            completed=subprocess.run([sys.executable,'-c',code,str(TOOLS/'course_lighting_batch.py'),str(scene)],capture_output=True,text=True,check=True)
            rows=json.loads(completed.stdout);self.assertEqual(rows[0]['folder'],'France_S1');self.assertTrue(rows[0]['identity_matrix'])
    def test_discover_includes_layout_alias_and_multiple_models(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'Alias').mkdir();(root/'Alias/track01.dx').touch();(root/'Alias/second.DX').touch();(root/'textures').mkdir()
            code="import runpy,sys,pathlib,json; m=runpy.run_path(sys.argv[1]); print(json.dumps(m['discover']([pathlib.Path(sys.argv[2])])))"
            completed=subprocess.run([sys.executable,'-c',code,str(TOOLS/'course_lighting_batch.py'),str(root)],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(completed.stdout),['Alias'])

if __name__=='__main__':unittest.main()
