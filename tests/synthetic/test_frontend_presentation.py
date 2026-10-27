import copy,math,struct,unittest
from master_rallye.frontend_presentation import validate_profile,bind_profile,pose,scene_transform,TARGET
from vehicle_frontend_native import make_wrapper,append_frontend

class FrontendTests(unittest.TestCase):
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
