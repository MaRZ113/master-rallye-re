import copy,math,struct,unittest
from master_rallye.frontend_presentation import validate_profile,bind_profile,pose,scene_transform,TARGET
from vehicle_frontend_native import make_wrapper,append_frontend

class FrontendTests(unittest.TestCase):
    def test_complete_origin_rebase_changes_only_y_and_bounds_not_race_hubs(self):
        from unittest.mock import patch
        from master_rallye.frontend_presentation import align_complete_rest_frame
        from master_rallye.dx import parse_dx_bytes
        from tests.synthetic.test_heritage_source import fixture
        raw=fixture();resources={n:raw for n in ('car.dx','complete.dx','wheel.dx')}
        a={'body_translation':[0.,0.,0.],'race_wheel_instances':[{'qualified':'fixture'}]};b={**a,'body_translation':[0.,.39,0.]}
        with patch('master_rallye.preview_scene.presentation_wheels',side_effect=[a,b,b]):data,report=align_complete_rest_frame(resources,resources)
        before,after=parse_dx_bytes(raw),parse_dx_bytes(data)
        for p,q in zip(before.vertices.positions,after.vertices.positions):
            self.assertEqual((p[0],p[2]),(q[0],q[2]));self.assertAlmostEqual(p[1]+.39,q[1],places=5)
        allowed={i for v in range(before.vertex_count)for i in range(before.vertices.position_offset+v*before.vertices.position_stride+4,before.vertices.position_offset+v*before.vertices.position_stride+8)}|set(range(before.collision.unparsed_offset,len(raw)))
        self.assertTrue(all(x==y or i in allowed for i,(x,y)in enumerate(zip(raw,data))))
        self.assertEqual(resources['car.dx'],raw);self.assertEqual(report['translation_m'],[0.,.39,0.])
        with patch('master_rallye.preview_scene.presentation_wheels',side_effect=[a,{**b,'body_translation':[1.,.39,0.]}]):
            with self.assertRaisesRegex(ValueError,'Unsupported'):align_complete_rest_frame(resources,resources)
    def profile(self):return {'version':1,'car_id':29,'runtime_family':'HeritageTrooper','source_model_sha256':'0'*64,'vertical_offset_m':.45}
    def test_schema_fails_closed(self):
        p=self.profile();self.assertIs(validate_profile(p),p)
        for key,value in [('version',True),('car_id',True),('car_id',30),('runtime_family','../car'),('source_model_sha256','bad'),('vertical_offset_m',float('nan')),('vertical_offset_m',2),('vertical_offset_m',True)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate_profile({**p,key:value})
        with self.assertRaises(ValueError):validate_profile({**p,'FOV':45})
    def test_source_hash_before_decoder(self):
        with self.assertRaisesRegex(ValueError,'source changed'):bind_profile(self.profile(),b'unknown')
    def test_scene_transform_and_target_are_separate(self):
        self.assertAlmostEqual(scene_transform((1,2,3),True)[0],.89-1.35,6)
        self.assertEqual(scene_transform((0,1,0)),(0.,1.,0.))
        a,b=pose(),pose(.4);self.assertEqual(a['eye'],b['eye']);self.assertEqual(a['source_fov_degrees'],45.)
        self.assertAlmostEqual(a['target'][1]-b['target'][1],.4,6)
        for value in (True,2.,float('nan')):
            with self.assertRaises(ValueError):pose(value)
    def test_wrapper_is_deterministic_and_does_not_mutate_binding(self):
        b={'profile':self.profile(),'model_resource':'vehicles/heritagetrooper/complete','native_bounds_values_hex':('00'*44)};before=copy.deepcopy(b)
        self.assertEqual(make_wrapper(0x10000000,[b]),make_wrapper(0x10000000,[b]));self.assertEqual(b,before)
    def test_noop_and_foreign_exe_fail_closed(self):
        self.assertEqual(append_frontend(b'a',b'b',b'c',0,[],10),(b'b',b'c',None))
        b={'profile':self.profile(),'model_resource':'vehicles/heritagetrooper/complete','native_bounds_values_hex':'00'*44}
        with self.assertRaisesRegex(ValueError,'Unqualified'):append_frontend(b'a',b'a',b'',0,[b],262144)
        with self.assertRaisesRegex(ValueError,'Duplicate'):append_frontend(b'a',b'a',b'',0,[b,b],262144)

if __name__=='__main__':unittest.main()
