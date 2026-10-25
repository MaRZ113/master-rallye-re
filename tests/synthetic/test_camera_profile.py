import unittest
from master_rallye.addon_sdk.camera_profile import validate_camera_profile,camera_extent_comparison
class CameraProfileTests(unittest.TestCase):
 def test_native_zero_id_is_not_silently_missing_key(self):
  from master_rallye.addon_sdk.camera_profile import bind_camera_profile
  p={'version':1,'car_id':0,'policy':'native_follow_extents','runtime_family':'Test','source_model_sha256':'0'*64,'follow_extents':{'half_length_m':2,'height_m':1.5}}
  with self.assertRaisesRegex(ValueError,'CarID0'):bind_camera_profile(p,b'')
 def test_isolation_and_runtime_gate(self):
  p={'version':1,'car_id':28,'policy':'diagnostic_only','follow_extents':{'half_length_m':2.25,'height_m':1.5}}
  self.assertEqual(camera_extent_comparison(p,27,3,2)['diagnostic'],[3,2]);self.assertEqual(camera_extent_comparison(p,28,3,2)['diagnostic'],[2.25,1.5])
  p['policy']='native_follow_override'
  with self.assertRaises(ValueError):validate_camera_profile(p)
 def test_nonfinite_and_unsupported(self):
  p={'version':1,'car_id':28,'policy':'diagnostic_only','follow_extents':{'half_length_m':float('nan'),'height_m':1.5}}
  with self.assertRaises(ValueError):validate_camera_profile(p)
  p['follow_extents']={'fov':90}
  with self.assertRaises(ValueError):validate_camera_profile(p)
