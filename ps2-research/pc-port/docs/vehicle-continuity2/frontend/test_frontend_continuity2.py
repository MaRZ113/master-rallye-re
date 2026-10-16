import json,pathlib,unittest,importlib.util,hashlib
HERE=pathlib.Path(__file__).resolve().parent;PORT=HERE.parents[2]
class Evidence(unittest.TestCase):
 def test_prior24_preserved(self):
  old=json.loads((PORT/'docs/vehicle-damage-fix1/frontend/frontend-profiles.json').read_text())['profiles'];new=json.loads((HERE/'frontend-profiles.json').read_text())['profiles'];self.assertEqual(new[:24],old);self.assertEqual(len(new),26)
 def test_unknown_tokens_are_not_aliases(self):
  j=json.loads((HERE/'original-material-evidence.json').read_text());names={r['name'] for r in j['registry_constructor_names']};self.assertEqual(len(names),29);self.assertFalse(names&{'crashiny','carbrakelight','carbrakelights'});self.assertIn('carshiny',names)
 def test_exact_new_policies(self):
  j=json.loads((HERE/'frontend-profiles.json').read_text());profiles={r['ps2_family']:r for r in j['profiles']}
  w=profiles['WOOLDAND']['mesh_secondary_kinds'];self.assertEqual((w[7]['mode'],w[7]['mixed_reflection']),(3,False));self.assertEqual((w[16]['mode'],w[16]['mixed_reflection']),(5,False))
  u=profiles['UFO']['mesh_secondary_kinds'];self.assertEqual((u[12]['mode'],u[12]['mixed_reflection']),(21,True))
  for i in(3,5,13):self.assertEqual((u[i]['mode'],u[i]['mixed_reflection']),(3,False))
  for i in(6,7,8,9):self.assertEqual(u[i]['mode'],1)
 def test_original_word_anchors(self):
  j=json.loads((HERE/'original-material-evidence.json').read_text());r={int(x['va'],16):int(x['word'],16) for x in j['instructions']}
  for a,w in((0x3ae178,0xae220028),(0x315350,0xa2040154),(0x315360,0xa20300a4),(0x314cb4,0xa2030154),(0x314cbc,0xa20000a4)):
   self.assertEqual(r[a],w)
 def test_private_asset_hashes_when_present(self):
  j=json.loads((HERE/'frontend-profiles.json').read_text())
  for r in j['profiles'][-2:]:
   p=PORT/'.assets/vehicles'/r['filename']
   if not p.exists():continue
   self.assertEqual(p.stat().st_size,r['bytes']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r['sha256'])
if __name__=='__main__':unittest.main()
