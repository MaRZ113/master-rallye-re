import json
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze_vehicle_lighting_inputs import pearson,directional_fit,vertex_stats
from analyze_vehicle_draws import decode_fvf,analyze,rectangle,constellations,reflection_audit
from validate_vehicle_correlation import metrics,correlate
from trace_common import TARGET_SHA

class LightingInputsTests(unittest.TestCase):
    def test_constant_color(self):
        s=vertex_stats([(0,0,0),(0,1,0),(0,2,0)],[(0,1,0)]*3,bytes([255,255,255,255])*3)
        self.assertEqual(s['unique_rgb'],1);self.assertIsNone(s['height_luma_pearson']);self.assertEqual(s['alpha_histogram'],{255:3})
    def test_variation_alpha_channels(self):
        s=vertex_stats([(0,0,0),(0,1,0),(0,2,0)],[(0,1,0)]*3,bytes([0,0,0,0,0,0,128,128,255,255,255,255]))
        self.assertEqual(s['unique_rgb'],3);self.assertEqual(s['alpha_histogram'],{0:1,128:1,255:1});self.assertGreater(s['height_luma_pearson'],.9)
    def test_directional_heuristic(self):
        n=[(1,0,0),(0,1,0),(0,0,1),(-1,0,0),(0,-1,0),(0,0,-1)]
        l=[.5+.2*x-.1*y+.05*z for x,y,z in n];fit=directional_fit(n,l)
        self.assertAlmostEqual(fit['r_squared'],1);self.assertAlmostEqual(fit['coefficients'][0],.2)
        self.assertIsNone(directional_fit([(0,1,0)]*6,l))
    def test_invalid_vertex_arrays(self):
        with self.assertRaises(ValueError):vertex_stats([],[],b'')
        with self.assertRaises(ValueError):vertex_stats([(float('nan'),0,0)],[(0,1,0)],bytes(4))
    def test_fvf_header_layouts(self):
        expected={0x102:(20,False,False,1),0x142:(24,False,True,1),0x152:(36,True,True,1),0x112:(32,True,False,1),0x242:(32,False,True,2),0x252:(44,True,True,2)}
        for f,(stride,normal,diffuse,uv) in expected.items():
            d=decode_fvf(f);self.assertEqual((d['stride'],d['normal'],d['diffuse'],d['uv_count']),(stride,normal,diffuse,uv))
        self.assertFalse(decode_fvf(0x80000001)['known_layout'])
    def test_pinned_constants(self):
        text=(Path(__file__).resolve().parents[1]/'vendor/d3d8/d3d8types.h').read_text()
        for token,value in [('D3DFVF_NORMAL','0x0010'),('D3DFVF_DIFFUSE','0x0040'),('D3DTSS_TCI_CAMERASPACENORMAL','0x10000'),('D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR','0x30000')]:
            self.assertRegex(text,token+r'\s+'+value)
    def test_legacy_and_unknown_frames(self):
        rows=[{'type':'frame_begin','exe_sha256':TARGET_SHA},{'type':'frame_end','complete':True,'truncated':False}]
        a=analyze(rows);self.assertTrue(a['exact_build_and_complete']);self.assertEqual(a['legacy_temporal_status'],'UNAVAILABLE')
        rows[0]['exe_sha256']='unknown';self.assertFalse(analyze(rows)['exact_build_and_complete'])
        rows[0]['exe_sha256']=TARGET_SHA;rows[-1]['truncated']=True;self.assertFalse(analyze(rows)['exact_build_and_complete'])
    def test_wheel_axle_preserved(self):
        identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        spin=[1,0,0,0,0,0,1,0,0,-1,0,0,0,0,0,1]
        self.assertEqual(metrics(identity,spin,True)['orientation_error'],0)
        self.assertAlmostEqual(metrics(identity,spin,False)['orientation_error'],90)
    def test_material_summary_and_temporal_fields(self):
        header={'type':'frame_begin','exe_sha256':TARGET_SHA,'exe_path':'game.exe'}
        draw={'type':'draw','method':'DrawIndexedPrimitive','result':0,'caller':{'return_rva':0x17707e,'module':'game.exe'},'primitive_type':4,'primitive_count':2,'state':{'vertex_shader':0x152,'texture_stage_states':[{},{}],'render_states':{'27':0},'textures':[],'matrices':{'256':{'values':[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]}}},'object_classification':'DYNAMIC_ENV_OBJECT','transform_dynamic':True,'transform_track_id':7,'reflection_feature':'Stock'}
        result=analyze([header,draw,{'type':'frame_end','complete':True,'truncated':False}])
        self.assertEqual(result['families'][0]['triangles'],2);self.assertEqual(result['families'][0]['layout']['stride'],36)
        self.assertTrue(result['transform_groups'][0]['dynamic']);self.assertEqual(result['reflection_modified_draws'],0)
    def test_broker_mismatch(self):
        with self.assertRaises(ValueError):correlate({'entries':[],'source':{'image_sha256':'unknown'}},[{'exe_sha256':TARGET_SHA},{'complete':True}])
    def test_actual_trace_additive_fields(self):
        release=Path(__file__).resolve().parents[1]/'.build-msvc/Release'
        current_sha=hashlib.sha256((release/'reflection_tests.exe').read_bytes()).hexdigest()
        captures=list((release/'MRRRenderer/logs').glob('frame*.jsonl'))
        matched=[]
        for p in captures:
            with p.open() as stream:rows=[json.loads(line) for line in stream]
            if rows[0].get('proxy_version')=='R-GFX4-5' and rows[0].get('exe_sha256')==current_sha:matched.extend(r for r in rows if r.get('type')=='draw')
        self.assertTrue(matched,'Run native contracts before Python trace checks')
        modified=[d for d in matched if d.get('native_override_applied')]
        self.assertTrue(modified,'Native reflection integration must produce a bounded positive capture')
        for d in modified:
            if d.get('vehicle_semantic_source')!='learned_signature':self.assertEqual(d['object_class_at_draw'],'VEHICLE_BODY')
            else:
                self.assertTrue(d['semantic_signature_id']);self.assertEqual(d['semantic_signature_state'],'PROVEN_VEHICLE_BODY_ENV')
            self.assertEqual(d['state']['vertex_shader'],0x152)
            self.assertTrue(d['native_restore_success']);self.assertEqual(d['requested_stage1_tci']&0xffff0000,0x10000)
            self.assertEqual(d['effective_stage1_tci_for_draw']&0xffff0000,0x30000)
            self.assertEqual(d['effective_state']['stage1']['11'],d['effective_stage1_tci_for_draw'])
            self.assertTrue(d['feature_mask']&8)
        for d in matched:
            self.assertIn('object_classification',d);self.assertIn('transform_track_id',d);self.assertIn('object_class',d);self.assertIn('native_restore_success',d);self.assertIn('effective_stage1_tci_for_draw',d)

    def test_actual_full_race_hud_capture(self):
        verified=[]
        release=Path(__file__).resolve().parents[1]/'.build-msvc/Release'
        current_sha=hashlib.sha256((release/'reflection_tests.exe').read_bytes()).hexdigest()
        for p in (release/'MRRRenderer/logs').glob('frame*.jsonl'):
            rows=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
            if rows[0].get('proxy_version')!='R-GFX4-5' or rows[0].get('exe_sha256')!=current_sha:continue
            hud=[r['sequence'] for r in rows if r.get('method')=='SetTransform' and r.get('arguments',[0])[0]==3 and len(r.get('payload_bits',[]))==16 and r['payload_bits'][11]==0]
            draws=[r for r in rows if r.get('type')=='draw']
            if not hud or not any(r.get('native_override_applied') for r in draws):continue
            if any(r.get('vehicle_semantic_source')=='learned_signature' for r in draws):continue # Covered by the independent lost-constellation capture test.
            summary=next(r for r in rows if r.get('type')=='frame_summary')['classifier']
            self.assertTrue(summary['race_seen_this_frame']);self.assertGreater(summary['vehicle_body_draws'],0);self.assertGreater(summary['vehicle_wheel_draws'],0)
            late=[r for r in draws if r['sequence']>max(hud)]
            self.assertTrue(late)
            for d in late:
                self.assertFalse(d['race_context']);self.assertFalse(d['geometry_signature']);self.assertFalse(d['native_override_applied'])
            self.assertEqual(rows[-1]['draw_records'],len(draws))
            verified.append(p)
        self.assertTrue(verified,'Native full-frame test must capture mature world then unclassified HUD')

class ContinuationAnalysisTests(unittest.TestCase):
    def test_rectangle_models_and_rejection(self):
        for x,z in ((.75,1.225),(.875,1.385),(1,1.375),(.825,1.2),(1.5,2.3)):
            p=[(-x,0,-z),(x,0,-z),(-x,0,z),(x,0,z)]
            self.assertEqual(rectangle(p),0);self.assertEqual(rectangle(list(reversed(p))),0)
            self.assertIsNone(rectangle(p[:3]));self.assertIsNone(rectangle(p[:3]+[p[0]]))
        self.assertIsNone(rectangle([(float('nan'),0,1)]*4))
    def test_offline_no_independent_wheel_motion(self):
        def group(x,z,body=False,track=1):
            return {'world':[1,0,0,0,0,1,0,0,0,0,1,0,x,0,z,1],'draws':4,'triangles':252,'tracks':[track],'dynamic':body,'ambiguous':False,'body_draws':4 if body else 0,'body_env_draws':2 if body else 0,'wheel_draws':0 if body else 4}
        gs=[group(0,0,True,100)]+[group(x,z,track=i+1) for i,(x,z) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1)))]
        p=constellations(gs)[0];self.assertTrue(p['accepted']);self.assertEqual(p['wheels_independently_dynamic'],[False]*4)
        self.assertFalse(constellations(gs[:4])[0]['accepted']);self.assertFalse(constellations(gs+[group(-1.01,-1,track=99)])[0]['accepted'])
    def test_resource_segments(self):
        from analyze_resource_lifetime import analyze as lifetime
        rows=[{'exe_sha256':TARGET_SHA},{'type':'resource_create','method':'CreateTexture','arguments':[8,8,1,0,21,1]},
              {'type':'reset','hresult':0},{'type':'resource_create','method':'CreateVertexBuffer','arguments':[720000,0,0,0]}]
        result=lifetime(rows);self.assertEqual(result['segments'][0]['resource_creations'],{'CreateTexture:MANAGED':1});self.assertEqual(result['segments'][1]['resource_creations'],{'CreateVertexBuffer:DEFAULT':1})
        rows[0]['exe_sha256']='unknown';self.assertFalse(lifetime(rows)['exact_build'])

    def test_reflection_provenance_audit(self):
        setter=lambda value:{'type':'native_override','method':'SetTextureStageState','arguments':[1,11,value],'result':0}
        draw={'type':'draw','native_override_applied':True,'native_restore_success':True,'object_class_at_draw':'VEHICLE_BODY','constellation_id_at_draw':1,'method':'DrawIndexedPrimitive',
              'requested_stage1_tci':0x10001,'effective_stage1_tci_for_draw':0x30001,'state':{'vertex_shader':0x152,'render_states':{'27':0,'14':1},'texture_stage_states':[{}, {'1':18,'2':1,'3':2,'4':4,'5':1,'6':2,'24':2}]}}
        draw.update(classifier_confidence='STRONG_FOUR_WHEEL',classifier_reasons=['dynamic_chassis','body_draw_cluster','wheel_signature','four_wheel_match','bilateral_symmetry','axle_pairing','unambiguous_assignment'],associated_wheel_track_ids=[2,3,4,5])
        rows=[setter(0x30001),draw,setter(0x10001)]
        self.assertEqual(reflection_audit(rows,True)['status'],'AUTOMATED_TRACE_PASS')
        self.assertEqual(reflection_audit(rows,False)['status'],'FAIL')
        draw['native_restore_success']=False;self.assertEqual(reflection_audit(rows,True)['status'],'FAIL')
        draw['native_restore_success']=True;draw['object_class_at_draw']='VEHICLE_WHEEL';self.assertEqual(reflection_audit(rows,True)['status'],'FAIL')
