import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze_vehicle_lighting_inputs import pearson,directional_fit,vertex_stats
from analyze_vehicle_draws import decode_fvf,analyze
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
        captures=list((Path(__file__).resolve().parents[1]/'.build-msvc/Release/MRRRenderer/logs').glob('frame*.jsonl'))
        matched=[]
        for p in captures:
            with p.open() as stream:rows=[json.loads(line) for line in stream]
            if rows[0].get('proxy_version')=='R-GFX4-1':matched.extend(r for r in rows if r.get('type')=='draw')
        self.assertTrue(matched,'Run native contracts before Python trace checks')
        for d in matched:
            self.assertIn('object_classification',d);self.assertIn('transform_track_id',d);self.assertEqual(d['reflection_feature'],'Stock')
