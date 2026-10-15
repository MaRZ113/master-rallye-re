import json, unittest
from pathlib import Path
class LampRegistry(unittest.TestCase):
 def setUp(self):
  self.r=json.loads(Path(__file__).with_name('source-registry.json').read_text())
  self.x={m['path']:m for f in self.r['families'] if f['ps2_family']=='XTRAIL' for m in f['meshes']}
 def test_off_on_not_geometry_only(self):
  off,on=self.x['root.20.0.0'],self.x['root.20.1.0']
  self.assertEqual(off['bounds'],on['bounds']);self.assertEqual(off['faces'],on['faces'])
  self.assertNotEqual(off['pc_candidates'][0]['position_uv_corner_sha256'],on['pc_candidates'][0]['position_uv_corner_sha256'])
  self.assertEqual([off['mode'],on['mode'],self.x['root.20.1.1']['mode']],[3,1,14])
 def test_off_original_indices_and_unique_owner_record(self):
  m=self.x['root.20.0.0'];self.assertEqual(len(m['source_indices']),18)
  self.assertEqual((min(m['source_indices']),max(m['source_indices'])),(3170,3179))
  self.assertEqual([r['record'] for r in m['pc_candidates']],[23]);self.assertEqual(m['pc_candidates'][0]['max_uv_error'],0)
 def test_front_and_rear_distinct(self):
  self.assertGreater(self.x['root.5']['bounds']['min'][2],1.9)
  self.assertGreater(self.x['root.11']['bounds']['min'][2],1.9)
  self.assertLess(self.x['root.20.0.0']['bounds']['max'][2],-2)
 def test_fleet_inventory_does_not_alias_foresters(self):
  fs={f['ps2_family']:f for f in self.r['families']};self.assertEqual(len(fs),29)
  self.assertEqual(fs['WOOLDAND']['pc_family'],'Forester');self.assertIsNone(fs['FORESTER']['pc_family'])
  self.assertEqual(sum(m['mode']==14 for f in fs.values() for m in f['meshes']),28)
 def test_glow_candidates_have_geometry_uv_proof(self):
  for f in self.r['families']:
   for m in f['meshes']:
    for c in m['pc_candidates']:
     self.assertLessEqual(c['max_position_error'],.001);self.assertLessEqual(c['max_uv_error'],.000001)
     self.assertEqual(len(c['position_uv_corner_sha256']),64)
if __name__=='__main__':unittest.main()
