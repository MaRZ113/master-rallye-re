import unittest,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Evidence(unittest.TestCase):
 def test_same_session_current_owner(self):
  a,b=json.loads((HERE/'runtime-pair.json').read_text());self.assertTrue(a['owner_verified'] and b['owner_verified']);self.assertFalse(a['private_tree']);self.assertTrue(b['private_tree']);self.assertEqual(a['instance'],b['instance']);self.assertEqual(a['packet'],b['packet'])
 def test_cloned_resource_not_original_xyz(self):
  a,b=json.loads((HERE/'runtime-pair.json').read_text());self.assertNotEqual(a['position_sha'],b['position_sha']);self.assertNotEqual(a['mesh'],b['mesh']);self.assertEqual(a['uv_sha'],b['uv_sha']);self.assertEqual(a['material_vector'],b['material_vector']);self.assertEqual(a['material_token'],b['material_token']);self.assertEqual(a['texture_generation'],b['texture_generation'])
 def test_normalized_index_topology_exact(self):
  a,b=json.loads((HERE/'topology-pair.json').read_text());self.assertEqual(a['normalized_uv_index_sha256'],b['normalized_uv_index_sha256'])
 def test_ps2_on_core_is_not_pink(self):
  on,glow=json.loads((HERE/'ps2-color-source.json').read_text());self.assertEqual(on['rgba_words'],[0xffffffff]);self.assertEqual(on['resources'][0]['channel_ranges'][2],[0,0]);self.assertEqual(on['resources'][0]['sha256'],'fd4c121f962ef4e9ee7491666c71b65db008d6ca276d9188881c0b35c7846131');self.assertEqual(glow['resources'][0]['sha256'],'b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09')
 def test_pc_on_core_differs_from_glow(self):
  on,glow=json.loads((HERE/'pc-color-source.json').read_text());self.assertGreater(on['mean_blue'],100);self.assertLess(glow['mean_blue'],1)
 def test_new_dll_live_healthy_and_damaged_layers(self):
  rows=json.loads((HERE/'runtime-acceptance.json').read_text())['evidence'];self.assertEqual(len(rows),2)
  for i,row in enumerate(rows):
   self.assertEqual(row['frame_metadata']['proxy_sha256'],'d8e01ce1ddb98514a1e53671756a3380add65ec79ea774bff6ed008c8f58e9d7')
   events=[e for e in row['events'] if e['type']=='kia_brake_continuity'];self.assertEqual({e['layer'] for e in events},{'ON_CORE','ADDITIVE_GLOW'})
   for event in events:
    self.assertTrue(event['owner_verified'] and event['override_applied']);self.assertEqual([event[k] for k in ('apply_hresult','draw_hresult','restore_hresult')],[0,0,0]);self.assertEqual(event['damaged_branch'],bool(i))
    if i:self.assertTrue(event['damaged_branch_matched'])
 def test_live_msaa_reset_and_body_wheels(self):
  rows=json.loads((HERE/'runtime-acceptance.json').read_text())['evidence'];self.assertEqual([r['frame_metadata']['quality_reset_epoch'] for r in rows],[0,1])
  for row in rows:
   self.assertEqual(row['frame_metadata']['msaa'],4);self.assertTrue(any(e['type']=='fleet_car_private_submission' and e['draw_hresult']==0 and e['restore_hresult']==0 for e in row['events']));self.assertEqual(len([e for e in row['events'] if e['type']=='fleet_ps2_wheel_submission' and e['draw_hresult']==0 and e['restore_hresult']==0]),4)
if __name__=='__main__':unittest.main()
