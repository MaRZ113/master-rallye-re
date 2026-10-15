import json,unittest
from pathlib import Path
class Registry(unittest.TestCase):
 def setUp(self):
  self.d=json.loads(Path(__file__).with_name('registry-candidates.json').read_text());self.r={r['source_draw']:r for r in self.d['pc_records']}
 def test_front_screen_ambiguity(self):
  for k in ('geometry_sha256','source_uv0_sha256','source_normal_sha256','attribute_corner_sha256'):self.assertEqual(self.r[30][k],self.r[31][k])
  self.assertNotEqual(self.r[30]['slots'],self.r[31]['slots'])
 def test_brake_attribute_separation(self):
  self.assertEqual(self.r[23]['geometry_sha256'],self.r[24]['geometry_sha256']);self.assertNotEqual(self.r[23]['attribute_corner_sha256'],self.r[24]['attribute_corner_sha256'])
  self.assertEqual([b['mesh']['path'] for b in self.r[23]['bindings'] if b['uv_max_abs']==0],['root.20.0.0'])
 def test_mixed_screen_materials(self):
  for n in (26,29):self.assertEqual(sorted(b['mesh']['source_faces'] for b in self.r[n]['bindings'] if b['uv_max_abs']==0),[1,5])
 def test_all_source_conditional_meshes(self):self.assertEqual(len(self.d['ps2_meshes']),11)
if __name__=='__main__':unittest.main()
