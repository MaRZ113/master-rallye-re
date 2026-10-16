from pathlib import Path
import json,unittest
HERE=Path(__file__).resolve().parent
class KiaLampEvidence(unittest.TestCase):
 def setUp(self):
  self.e=json.loads((HERE/'source-runtime.json').read_text());self.m={m['path']:m for m in self.e['meshes']}
 def test_conditional_off_own_mode3(self):
  m=self.m['root.25.0.0'];self.assertEqual((m['pc_record'],m['vertices'],m['faces'],m['mode']),(30,20,12,3));self.assertTrue(m['mixed_reflection']);self.assertTrue(m['conditional']);self.assertEqual(m['max_uv_error'],0);self.assertLess(m['max_position_error'],.001)
 def test_on_not_position_only_identity(self):
  off=self.m['root.25.0.0'];on=self.m['root.25.1.0'];self.assertEqual(off['geometry_sha256'],on['geometry_sha256']);self.assertNotEqual(off['position_uv_corner_sha256'],on['position_uv_corner_sha256']);self.assertEqual(on['ordered_texture_slots'][0],'breaklightson-tga')
 def test_unconditional_reflective_base_already_separate(self):
  m=self.m['root.13'];self.assertEqual(m['faces'],30);self.assertTrue(m['mixed_reflection']);self.assertFalse(m['conditional'])
 def test_runtime_off_on_layout_separated(self):
  frames={r['frame']:r for r in self.e['runtime']}
  off=frames[3336]['conditional_shape_candidates'];self.assertEqual(len(off),1);self.assertEqual((off[0]['fvf'],off[0]['stride']),(0x152,36));self.assertTrue(off[0]['forwarded'])
  for f in (3911,3913):
   on=frames[f]['conditional_shape_candidates'];self.assertEqual(len(on),1);self.assertEqual((on[0]['fvf'],on[0]['stride']),(0x102,20))
if __name__=='__main__':unittest.main()
